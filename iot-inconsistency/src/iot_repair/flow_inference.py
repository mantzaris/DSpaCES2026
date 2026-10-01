"""GPU prior generation enters both detection and conditional repair inference."""
import math
import time

import numpy as np
import torch

from .graph_flow_model import build_context
from .flow_math import GaussianCorruption, score_candidates, summarize_repairs, weighted_crps

FLOOR=-1e12


@torch.no_grad()
def infer_case(models, values, graph, context_length, sample_count=512, scale=1., seed=1,
               context_mode='graph', draw_chunk=128, reference=None, sensitivity=False, candidate_chunk=64,times=None):
    """Exhaustive candidates, with explicit unavailable-target outputs.

    Reference truth is used only after all score and posterior computations.
    Returned raw arrays retain model log densities, component integrals, seeds,
    generated trajectories and latent draws for independent production auditing.
    """
    device=next(models[0].parameters()).device
    observed=torch.as_tensor(values,dtype=torch.float32,device=device)
    eligible=torch.isfinite(observed[:,-8:]).all(-1)
    query=torch.flatnonzero(eligible) if hasattr(torch,'flatnonzero') else torch.nonzero(eligible,as_tuple=True)[0]
    channels=values.shape[0]
    scores={key:np.full(channels,FLOOR) for key in ('flow_ratio','flow_nll','flow_plugin','flow_single','mean_member_ratios')}
    if not len(query):
        for name in GaussianCorruption.names:scores['without_'+name]=np.full(channels,FLOOR)
        if sensitivity:
            for count in (32,128,512,2048):
                if count<=sample_count:scores['M'+str(count)]=np.full(channels,FLOOR)
            for alternative in (1.,2.):scores['scale_'+str(alternative)]=np.full(channels,FLOOR)
        members=len(models)
        raw=dict(query=np.empty(0,int),input=np.asarray(values),latent=np.empty((0,members,sample_count,8)),
            generated=np.empty((0,members,sample_count,8)),log_normal_members=np.empty((0,members)),
            log_corruption=np.empty((0,members,sample_count)),log_fault_components=np.empty((0,4)),
            log_normal=np.empty(0),log_fault=np.empty(0),score=np.empty(0),posterior_weights=np.empty((0,members*sample_count)),
            posterior_mean=np.empty((0,8)),seed=np.array(seed),corruption_scale=np.array(scale),target_times=np.arange(8) if times is None else np.asarray(times))
        return dict(scores=scores,eligible=eligible.cpu().numpy(),ess=np.zeros(channels),numerical_adequate=np.zeros(channels,bool),
                    repairs={key:np.full((channels,8),np.nan) for key in ('mean','median','lower','upper','variance','width')},
                    repair_metrics={key:np.empty(0) for key in ('posterior_crps','prior_crps','interval_coverage','interval_width','energy_score')},
                    raw=raw,seconds=0.,peak_gpu_bytes=0)
    if device.type=='cuda':torch.cuda.synchronize()
    start=time.perf_counter()
    inputs=build_context(observed[None].expand(len(query),-1,-1),query,graph,context_length,mode=context_mode)
    target=observed[query,-8:]
    channel=GaussianCorruption(8,scale=scale,device=device,times=times)
    generations=[];latents=[];normal=[];q_logs=[];component_logs=[]
    for member,model in enumerate(models):
        model.eval();encoded=model.encode(inputs)
        generator=torch.Generator(device=device).manual_seed(seed+100003*member)
        latent=torch.randn((len(query),sample_count,8),generator=generator,device=device)
        generated=torch.cat([model.sample(encoded[first:first+candidate_chunk],sample_count=sample_count,
            latent=latent[first:first+candidate_chunk],chunk=draw_chunk) for first in range(0,len(query),candidate_chunk)])
        log_normal=model.log_prob(target,encoded)
        components=channel.component_log_prob(target,generated)
        log_q=torch.logsumexp(components+channel.weights.log(),-1)
        normal.append(log_normal);q_logs.append(log_q);component_logs.append(components)
        generations.append(generated);latents.append(latent)
    normal=torch.stack(normal,1);log_q=torch.stack(q_logs,1)
    generated=torch.stack(generations,1);components=torch.stack(component_logs,1)
    evidence=score_candidates(normal,log_q)
    flat=generated.flatten(1,2)
    posterior=summarize_repairs(flat,evidence.weights)
    plugin=channel.log_prob(target,flat.mean(1)[:,None])[:,0]-evidence.log_normal
    single=score_candidates(normal[:,:1],log_q[:,:1])
    member_scores=torch.logsumexp(log_q,dim=2)-math.log(sample_count)-normal.double()
    for key,result in [('flow_ratio',evidence.ratio),('flow_nll',-evidence.log_normal),('flow_plugin',plugin),
                       ('flow_single',single.ratio),('mean_member_ratios',member_scores.mean(1))]:
        scores[key][query.cpu().numpy()]=result.cpu().numpy()
    component_integrals=torch.logsumexp(components.flatten(1,2),1)-math.log(len(models)*sample_count)
    for omitted,name in enumerate(channel.names):
        weights=channel.weights.clone();weights[omitted]=0;weights/=weights.sum()
        value=torch.logsumexp(component_integrals+weights.log(),-1)-evidence.log_normal
        scores['without_'+name]=np.full(channels,FLOOR);scores['without_'+name][query.cpu().numpy()]=value.cpu().numpy()
    if sensitivity:
        for count in [32,128,512,2048]:
            if count>sample_count:continue
            value=score_candidates(normal,log_q[:,:,:count])
            scores['M'+str(count)]=np.full(channels,FLOOR)
            scores['M'+str(count)][query.cpu().numpy()]=value.ratio.cpu().numpy()
        for alternative in [1.,2.]:
            q=GaussianCorruption(8,scale=alternative,device=device,times=times)
            logs=q.log_prob(target,flat)
            value=torch.logsumexp(logs,1)-math.log(flat.shape[1])-evidence.log_normal
            scores['scale_'+str(alternative)]=np.full(channels,FLOOR)
            scores['scale_'+str(alternative)][query.cpu().numpy()]=value.cpu().numpy()
    ess=np.zeros(channels);ess[query.cpu().numpy()]=evidence.ess.cpu().numpy()
    repairs={key:np.full((channels,8),np.nan) for key in posterior}
    for key,value in posterior.items():repairs[key][query.cpu().numpy()]=value.cpu().numpy()
    # Test truth first enters here. It cannot affect generation or importance weights.
    metrics={}
    if reference is not None:
        truth=torch.as_tensor(reference,dtype=torch.float64,device=device)[query,-8:]
        prior_weights=torch.full_like(evidence.weights,1/evidence.weights.shape[1])
        metrics['posterior_crps']=weighted_crps(flat,evidence.weights,truth).mean(-1).cpu().numpy()
        metrics['prior_crps']=weighted_crps(flat,prior_weights,truth).mean(-1).cpu().numpy()
        metrics['interval_coverage']=((truth>=posterior['lower'])&(truth<=posterior['upper'])).double().mean(-1).cpu().numpy()
        metrics['interval_width']=posterior['width'].mean(-1).cpu().numpy()
        # An unbiased Monte Carlo estimate of the empirical joint energy score.
        generator=torch.Generator(device=device).manual_seed(seed+910003)
        pair_indices=torch.multinomial(evidence.weights,1024,replacement=True,generator=generator)
        selected=torch.gather(flat.double(),1,pair_indices[...,None].expand(-1,-1,8))
        energy=(selected[:,:512]-truth[:,None]).norm(dim=-1).mean(1)-.5*(selected[:,:512]-selected[:,512:]).norm(dim=-1).mean(1)
        metrics['energy_score']=energy.cpu().numpy()
    if device.type=='cuda':torch.cuda.synchronize()
    elapsed=time.perf_counter()-start
    raw=dict(input=np.asarray(values),query=query.cpu().numpy(),latent=torch.stack(latents,1).cpu().numpy(),
             generated=generated.cpu().numpy(),log_normal_members=normal.cpu().numpy(),log_corruption=log_q.cpu().numpy(),
             log_fault_components=component_integrals.cpu().numpy(),log_normal=evidence.log_normal.cpu().numpy(),
             log_fault=evidence.log_fault.cpu().numpy(),score=evidence.ratio.cpu().numpy(),
             posterior_weights=evidence.weights.cpu().numpy(),posterior_mean=posterior['mean'].cpu().numpy(),
             context_values=inputs.sequence.cpu().numpy(),context_neighbors=inputs.neighbors.cpu().numpy(),
             context_attributes=inputs.attributes.cpu().numpy(),context_support=inputs.support.cpu().numpy(),
             seed=np.array(seed),corruption_scale=np.array(scale),target_times=channel.times)
    return dict(scores=scores,eligible=eligible.cpu().numpy(),ess=ess,numerical_adequate=ess>=16,
                repairs=repairs,repair_metrics=metrics,raw=raw,seconds=elapsed,
                peak_gpu_bytes=torch.cuda.max_memory_allocated() if device.type=='cuda' else 0)
