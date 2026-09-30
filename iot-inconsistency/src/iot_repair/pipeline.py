"""Production repair scoring. E4--E11 determine the returned candidate rank."""
from __future__ import annotations
import copy,time
import numpy as np
import torch
from .witnesses import select_witnesses,masked_context,aggregate_group_losses,canonicalize_records,canonicalize_graph
from .diffusion import conditional_sample
from .scoring import normalized_empirical_crps,repair_score
from .costs import observation_edit_cost,association_edit_cost


def screen_candidates(sensor_residuals,edge_residuals,graph,cap=4):
    if cap<1:raise ValueError('Candidate cap must be positive')
    residual=np.nan_to_num(sensor_residuals,nan=-np.inf)
    first=list(np.argsort(-residual,kind='stable')[:max(1,cap//2)])
    outgoing=np.full(len(residual),-np.inf)
    for index,edge in enumerate(graph['edges']):
        if np.isfinite(edge_residuals[index]):outgoing[edge['source']]=max(outgoing[edge['source']],edge_residuals[index])
    order=list(np.argsort(-outgoing,kind='stable'))+list(np.argsort(-residual,kind='stable'))
    for i in order:
        if len(first)>=cap:break
        if i not in first:first.append(int(i))
    edges=np.argsort(-np.nan_to_num(edge_residuals,nan=-np.inf),kind='stable')[:cap]
    return [('observation',int(i)) for i in first]+[('association',int(i)) for i in edges]


@torch.no_grad()
def score_candidates(models,x,graph,candidates,replicates=8,predictive_samples=8,seed=1,
                     kappa=1.,edit_weight=.2,sampling_steps=12,deterministic_models=None,
                     separate_witnesses=True,no_op=False,record_ids=None,deduplicate_graph=True):
    """One immutable decision window, candidates batched within each model.

    Raw tensors keep candidate, ensemble, replicate, group, cell, sample axes.
    Before/after draws are regenerated for each replicate with common noise.
    """
    if x.ndim!=2:raise ValueError('Expected [channel,time] decision window')
    if deduplicate_graph:graph=canonicalize_graph(graph)
    expected=[f'channel_{i}' for i in range(len(graph['groups']))]
    identities=expected if record_ids is None else record_ids
    if len(identities)!=len(x):raise ValueError('Every input record needs a source identity')
    x,_,identities=canonicalize_records(x,np.isfinite(x),identities)
    if set(identities)!=set(expected):raise ValueError('Unexpected source identity requires channel mapping')
    x=x[[identities.index(identity) for identity in expected]]
    device=next(models[0].parameters()).device
    observed=np.isfinite(x);eligible=[];abstentions=[]
    for kind,index in candidates:
        partition=select_witnesses(index,observed,graph,kind=kind)
        if partition['support_count']<1 or (kind=='observation' and not partition['edit_mask'].any()):
            abstentions.append(dict(kind=kind,index=index,status='insufficient_evidence',support_count=partition['support_count']))
        else:eligible.append((kind,index,partition))
    if not eligible:return [],{},abstentions
    if device.type=='cuda':torch.cuda.synchronize()
    start=time.perf_counter();n=len(eligible);e=len(models);m=replicates;l=predictive_samples;c,t=x.shape
    original=torch.as_tensor(np.nan_to_num(x),dtype=torch.float32,device=device)[None].expand(n,-1,-1)
    available=torch.as_tensor(observed,device=device)[None].expand(n,-1,-1)
    forbidden=torch.as_tensor(np.stack([p['forbidden_witness'] for _,_,p in eligible]),device=device)
    proposals=torch.as_tensor(np.stack([p['proposal_forbidden'] for _,_,p in eligible]),device=device)
    edits=torch.as_tensor(np.stack([p['edit_mask'] for _,_,p in eligible]),device=device)
    if not separate_witnesses:proposals=edits
    context,visible=masked_context(original,available,forbidden)
    proposal_context,proposal_visible=masked_context(original,available,proposals)
    all_before=[];all_after=[];all_replacements=[];all_before_draws=[];all_after_draws=[]
    for member,model in enumerate(models):
        model.eval()
        if deterministic_models is None:
            generated=conditional_sample(model,proposal_context,proposal_visible,graph,m,seed+100003*member,sampling_steps)
        else:
            mean=deterministic_models[member](proposal_context,proposal_visible,graph)
            generated=mean[:,None].expand(-1,m,-1,-1)
        if no_op:generated=original[:,None].expand(-1,m,-1,-1)
        edited=torch.where(edits[:,None],generated,original[:,None])
        all_replacements.append(edited)
        before_context=context[:,None].expand(-1,m,-1,-1).reshape(n*m,c,t)
        before_mask=visible[:,None].expand(-1,m,-1,-1).reshape(n*m,c,t)
        after_context=torch.where(visible[:,None],edited,torch.zeros_like(edited)).reshape(n*m,c,t)
        before_encoding=model.encode(context,visible,graph)[:,None].expand(-1,m,-1,-1).reshape(n*m,c,-1)
        after_encodings=[]
        for candidate,(kind,index,p) in enumerate(eligible):
            candidate_graph=graph
            if kind=='association' and not no_op:
                candidate_graph=dict(graph,edges=[edge for j,edge in enumerate(graph['edges']) if j!=index])
            after_encodings.append(model.encode(after_context[candidate*m:(candidate+1)*m],before_mask[candidate*m:(candidate+1)*m],candidate_graph))
        after_encoding=torch.cat(after_encodings,0)
        paired_seed=seed+700001+100003*member
        before_draw=conditional_sample(model,before_context,before_mask,graph,l,paired_seed,sampling_steps,encoding=before_encoding).reshape(n,m,l,c,t)
        after_draw=conditional_sample(model,after_context,before_mask,graph,l,paired_seed,sampling_steps,encoding=after_encoding).reshape(n,m,l,c,t)
        # Losses and differences accumulate in float64, not training precision.
        target=original[:,None].expand(-1,m,-1,-1).double()
        cb=normalized_empirical_crps(before_draw.permute(0,1,3,4,2).double(),target)
        ca=normalized_empirical_crps(after_draw.permute(0,1,3,4,2).double(),target)
        before_groups=[];after_groups=[];before_selected=[];after_selected=[]
        for candidate,(_,_,p) in enumerate(eligible):
            bg=aggregate_group_losses(cb[candidate],p);ag=aggregate_group_losses(ca[candidate],p)
            # Pad absent groups with NaN; explicit weights/masks exclude them later.
            if bg.shape[-1]<2:
                pad=torch.full((m,2-bg.shape[-1]),float('nan'),device=device,dtype=torch.float64)
                bg=torch.cat([bg,pad],-1);ag=torch.cat([ag,pad],-1)
            before_groups.append(bg);after_groups.append(ag)
            def select(draw):
                selected=draw[candidate,:,:,p['channels'],-8:].permute(0,2,3,1)
                if selected.shape[1]<2:
                    selected=torch.cat([selected,torch.full((m,2-selected.shape[1],8,l),float('nan'),device=device)],1)
                return selected
            before_selected.append(select(before_draw));after_selected.append(select(after_draw))
        all_before.append(torch.stack(before_groups));all_after.append(torch.stack(after_groups))
        all_before_draws.append(torch.stack(before_selected));all_after_draws.append(torch.stack(after_selected))
    before=torch.stack(all_before,1);after=torch.stack(all_after,1);replacement=torch.stack(all_replacements,1)
    costs=[];weights=[];valid=[]
    for candidate,(kind,index,p) in enumerate(eligible):
        if kind=='observation':cost=observation_edit_cost(original[candidate].double(),replacement[candidate].double(),edits[candidate],available[candidate])
        else:cost=torch.tensor(association_edit_cost(1,len(graph['edges'])),device=device,dtype=torch.float64)
        costs.append(cost);g=p['support_count'];weights.append([1/g if j<g else 0 for j in range(2)]);valid.append([j<g for j in range(2)])
    terms=repair_score(before,after,torch.tensor(weights,device=device,dtype=torch.float64),torch.stack(costs),kappa,edit_weight,valid_groups=valid)
    if device.type=='cuda':torch.cuda.synchronize()
    elapsed=time.perf_counter()-start
    records=[]
    for candidate,(kind,index,p) in enumerate(eligible):
        record=dict(kind=kind,index=index,raw_index=candidate,status='eligible' if p['support_count']>=2 else 'low_support',
            support_count=p['support_count'],witness_ids=p['witness_ids'],witness_hash_before=p['witness_hash'],
            witness_hash_after=p['witness_hash'],witness_channels=p['channels'],witness_groups=p['groups'],
            model_members=e,replicates=m,predictive_samples=l,graph_version=graph['version'],
            elapsed_seconds_per_candidate=elapsed/n)
        record.update({key:float(value[candidate]) for key,value in terms.items() if key!='model_gains'})
        if kind=='observation':
            record['observed_interval']=x[index,-8:].tolist()
            record['generated_interval_quantiles']=torch.quantile(replacement[candidate,:,:,index,-8:].reshape(e*m,8),torch.tensor([.05,.5,.95],device=device),dim=0).cpu().tolist()
        records.append(record)
    raw=dict(axis_names=np.array(['candidate','ensemble','paired_replicate','provenance_group']),sample_axis_names=np.array(['candidate','ensemble','paired_replicate','provenance_group','cell','predictive_sample']),loss_before=before.cpu().numpy(),loss_after=after.cpu().numpy(),
        witness_samples_before=torch.stack(all_before_draws,1).cpu().numpy(),
        witness_samples_after=torch.stack(all_after_draws,1).cpu().numpy(),
        replacement_targets=np.stack([replacement[j,:,:,i,-8:].cpu().numpy() if k=='observation' else np.full((e,m,8),np.nan) for j,(k,i,p) in enumerate(eligible)]),
        group_weights=np.array(weights),valid_groups=np.array(valid),
        model_gains=terms['model_gains'].cpu().numpy())
    return sorted(records,key=lambda r:r['score'],reverse=True),raw,abstentions
