"""Frozen calibration and paired controlled-injection experiment runner."""
from __future__ import annotations

import itertools
import json
import time
import warnings
from pathlib import Path

import numpy as np
import torch
from scipy.sparse.csgraph import connected_components

from .calibration import rank_pvalues
from .classic import classic_scores, gdn_residuals
from .data import SensorData
from .features import Scan, prediction_fidelity, robust_location_scale, score_features, summarize_reference
from .localization import oracle_overlap, participation, set_metrics
from .models import GDN
from .reference import BlockBootstrap, issue_reference
from .synthetic import fault_nodes, inject, simulate, system
from .training import build_diffusion
from .utils import Budget, digest, synchronize, write_json


def load_models(data: SensorData, config: dict, seed: int, directory: Path,
                device: str, graph: str = 'physical') -> tuple[torch.nn.Module,torch.nn.Module]:
    model=build_diffusion(data,config,device,graph)
    model.load_state_dict(torch.load(directory/'checkpoints'/f'{data.name}-diffusion-{graph}-{seed}.pt',map_location=device,weights_only=False)['state_dict'])
    gdn=GDN(len(data.node_ids),len(data.channels),config['context'],config['gdn_hidden'],config['gdn_topk']).to(device)
    gdn.load_state_dict(torch.load(directory/'checkpoints'/f'{data.name}-gdn-physical-{seed}.pt',map_location=device,weights_only=False)['state_dict'])
    model.eval();gdn.eval()
    return model,gdn


def base_episodes(data: SensorData, config: dict, split: int = 3) -> list[tuple[int,int]]:
    candidates=[]
    for start,stop,partition in data.episode_bounds:
        if partition==split:
            candidates.extend([(i,i+config['episode_length']) for i in range(int(start),int(stop)-config['episode_length']+1,config['episode_length'])])
    if len(candidates)>config['base_episodes']:
        take=np.linspace(0,len(candidates)-1,config['base_episodes'],dtype=int)
        candidates=[candidates[i] for i in take]
    return candidates


def event_manifest(data: SensorData, config: dict, bases: list[tuple[int,int]]) -> list[dict]:
    events=[]
    for i,(kind,severity,duration) in enumerate(itertools.product(config['fault_types'],config['severities'],config['durations'])):
        seed=57100+i
        size=config['fault_sizes'][i%len(config['fault_sizes'])]
        nodes=fault_nodes(data.adjacency,size,seed,bool(i%2))
        events.append({'id':f'{kind}-{i:03d}','kind':kind,'severity':severity,'duration':duration,
                       'onset':config['onset'],'nodes':nodes,'partly_disconnected':bool(i%2),
                       'base':i%len(bases),'seed':seed,'is_fault':True})
        events[-1]['affected_components']=int(connected_components(data.adjacency[np.ix_(nodes,nodes)]>0,directed=False)[0])
    for base in range(len(bases)):
        for kind in ['untouched','transition']:
            events.append({'id':f'{kind}-{base:03d}','kind':kind,'severity':1.,'duration':96,
                           'onset':config['onset'],'nodes':list(range(len(data.node_ids))) if kind=='transition' else [],
                           'partly_disconnected':False,'base':base,'seed':68100+base,
                           'is_fault':False})
    return events


def score_summary(scores: dict[str,torch.Tensor], scan: Scan, node_count: int) -> tuple[dict,dict]:
    maxima={};rankings={}
    for name,score in scores.items():
        vector=score.detach().cpu().numpy()
        maxima[name]=float(np.max(np.where(np.isfinite(vector),vector,-np.inf)))
        values=participation(vector,scan.groups,node_count)
        rankings[name]=np.argsort(-values,kind='stable')[:24]
    return maxima,rankings


@torch.no_grad()
def run(data: SensorData, config: dict, seed: int, experiment_dir: Path, budget: Budget,
        device: str = 'cuda', graph: str = 'physical', limit_events: int | None = None,
        stop_after_calibration: bool = False) -> dict:
    torch.set_num_threads(4)
    directory=experiment_dir/f'score-{data.name}-{graph}-{seed}'
    if (directory/'status.json').exists():
        return json.loads((directory/'status.json').read_text())
    directory.mkdir(parents=True,exist_ok=True)
    samples_dir=directory/'samples';samples_dir.mkdir(exist_ok=True)
    model,gdn=load_models(data,config,seed,experiment_dir,device,graph)
    if device=='cuda':torch.cuda.reset_peak_memory_stats()
    scan=Scan(data.adjacency,data.coordinates,data.channels,config,device)
    write_json(directory/'groups.json',scan.records)
    values=data.standardized;horizon=max(w+w//4 for w in config['windows'])
    bootstrap=BlockBootstrap(data,config['context'],horizon,device)
    started=time.monotonic();timings=[];fidelity=[];reference_names=['diffusion','bootstrap']
    write_json(directory/'configuration.json',config)
    # Development only: numerical floors, conventional feature centers/scales,
    # GDN residual scaling and localization rank budget.
    dev_indices=data.issuance_indices(1,config['context'],horizon,168)
    dev_indices=dev_indices[np.linspace(0,len(dev_indices)-1,min(12,len(dev_indices)),dtype=int)]
    observed_development=[];gdn_development=[];development_samples=[]
    for target_start in dev_indices:
        budget.check()
        block=torch.as_tensor(values[target_start:target_start+horizon],device=device)
        observed=scan.extract(block)
        observed_development.append(observed.values[0])
        gdn_development.append(gdn_residuals(gdn,values[target_start-config['context']:target_start+horizon],config['context'],device))
        samples=issue_reference(model,data,values,int(target_start),horizon,config,device,'diffusion',bootstrap,seed+int(target_start))
        development_samples.append(samples.cpu())
        fidelity.append({'split':'development','reference':'diffusion','target_start':int(target_start),**prediction_fidelity(block,samples)})
    development=torch.stack(observed_development)
    variability=torch.nanquantile(development,.75,dim=0)-torch.nanquantile(development,.25,dim=0)
    floor=(variability*.05).nan_to_num(nan=0).clamp_min(1e-4)
    center,spread=robust_location_scale(development,floor)
    center=center.nan_to_num(nan=0);spread=spread.nan_to_num(nan=1)
    errors=torch.cat(gdn_development)
    gdn_center=torch.nanmedian(errors,dim=0).values
    gdn_scale=(torch.nanquantile(errors,.75,dim=0)-torch.nanquantile(errors,.25,dim=0)).clamp_min(.01)
    gdn_center=gdn_center.nan_to_num(nan=0);gdn_scale=gdn_scale.nan_to_num(nan=1)
    localization={k:[] for k in config['localization_budgets']}
    for number,target_start in enumerate(dev_indices[:6]):
        block=values[target_start:target_start+horizon].copy()
        size=config['fault_sizes'][number%len(config['fault_sizes'])]
        nodes=fault_nodes(data.adjacency,size,8800+number,False)
        corrupted=inject(block,nodes,24,96,['copy','noise','drift'][number%3],1.,8900+number)
        samples=development_samples[number].to(device).masked_fill(~torch.isfinite(torch.as_tensor(corrupted,device=device))[None],float('nan'))
        scores,_=score_features(scan.extract(torch.as_tensor(corrupted,device=device)),scan.extract(samples),floor)
        node_scores=participation(scores['entropy'].cpu().numpy(),scan.groups,len(data.node_ids))
        order=np.argsort(-node_scores,kind='stable')
        for k in localization:localization[k].append(set_metrics(order[:k].tolist(),nodes)['iou'])
    chosen_budget=max(localization,key=lambda k:np.mean(localization[k]))
    np.savez_compressed(directory/'development_parameters.npz',floor=floor.cpu().numpy(),center=center.cpu().numpy(),
                        spread=spread.cpu().numpy(),gdn_center=gdn_center.cpu().numpy(),gdn_scale=gdn_scale.cpu().numpy())
    write_json(directory/'development_selection.json',{'localization_budget':chosen_budget,'candidate_mean_iou':{k:np.mean(v) for k,v in localization.items()},
               'shrinkage':config['shrinkage'],'floor_rule':'.05 development IQR, minimum 1e-4','development_indices':dev_indices})
    del development_samples
    # Fixed, disjoint context + target calibration units; real streams remain
    # dependent. Synthetic units are independent simulation episodes.
    calibration_indices=data.issuance_indices(2,config['context'],horizon,config['calibration_stride'])
    calibration=[];calibration_quality=[];calibration_groups=[]
    group_methods=[f'{reference}/{feature}' for reference in reference_names for feature in ['entropy','synchronization','combined']]
    for unit,target_start in enumerate(calibration_indices):
        budget.check();synchronize(device);timer=time.perf_counter()
        block=torch.as_tensor(values[target_start:target_start+horizon],device=device)
        observed=scan.extract(block)
        all_scores={}
        for reference in reference_names:
            samples=issue_reference(model,data,values,int(target_start),horizon,config,device,reference,bootstrap,seed+int(target_start))
            generated=scan.extract(samples.masked_fill(~torch.isfinite(block)[None],float('nan')))
            scores,_=score_features(observed,generated,floor)
            all_scores.update({f'{reference}/{key}':value for key,value in scores.items()})
        residual=gdn_residuals(gdn,values[target_start-config['context']:target_start+horizon],config['context'],device)
        all_scores.update(classic_scores(block,scan,center,spread,residual,gdn_center,gdn_scale))
        maxima,_=score_summary(all_scores,scan,len(data.node_ids));calibration.append(maxima)
        calibration_groups.append(torch.stack([all_scores[m] for m in group_methods]).cpu().numpy())
        calibration_quality.append(float(observed.eligible.float().mean()))
        synchronize(device);timings.append({'stage':'calibration','seconds':time.perf_counter()-timer})
    methods=list(calibration[0])
    calibration_array=np.array([[row[m] for m in methods] for row in calibration])
    write_json(directory/'calibration.json',{'methods':methods,'indices':calibration_indices,
               'maxima':np.where(np.isneginf(calibration_array),-1e30,calibration_array),
               'n_units':len(calibration),'minimum_p':1/(len(calibration)+1),'eligible_fraction':calibration_quality,
               'unit':'One context-plus-target unit; all-abstained maxima encoded as -1e30 in JSON, -inf in NPZ'})
    np.savez_compressed(directory/'calibration.npz',maxima=calibration_array,indices=calibration_indices,methods=methods)
    if stop_after_calibration:
        return {'status':'calibrated','dataset':data.name,'seed':seed,'units':len(calibration)}
    # TEST BEGINS: all preceding settings are frozen and saved.
    bases=base_episodes(data,config);events=event_manifest(data,config,bases)
    if limit_events is not None:events=events[:limit_events]
    times=np.arange(config['context']+horizon-1,config['episode_length'],config['alert_stride'])
    event_maxima=np.full((len(events),len(times),len(methods)),-np.inf,np.float32)
    rankings=np.zeros((len(events),len(times),len(methods),24),np.int16)
    quality=np.zeros((len(events),len(times)),np.float32)
    method_quality=np.zeros_like(event_maxima)
    directions=np.full((len(events),len(times)),np.nan,np.float32)
    observed_changes=directions.copy()
    saved_group_scores=np.full((len(events),len(times),len(group_methods),len(scan.records)),np.nan,np.float32)
    for base,(start,stop) in enumerate(bases):
        selected=[i for i,event in enumerate(events) if event['base']==base]
        if not selected:continue
        clean=values[start:stop]
        episode_values={i:clean if events[i]['kind']=='untouched' else inject(clean,events[i]['nodes'],events[i]['onset'],events[i]['duration'],events[i]['kind'],events[i]['severity'],events[i]['seed']) for i in selected}
        if data.name.startswith('synthetic'):
            test_rows=data.episode_bounds[data.episode_bounds[:,2]==3]
            episode_id=next(i for i,row in enumerate(test_rows) if row[0]<=start<row[1])
            simulation_seed=100000+len(data.node_ids)*1000+300+episode_id
            coords,_,transition,_=system(len(data.node_ids))
            for i in selected:
                if events[i]['kind']=='decouple':
                    fault=simulate(coords,transition,int(test_rows[episode_id,1]-test_rows[episode_id,0]),simulation_seed,device,events[i])
                    begin=start-int(test_rows[episode_id,0])
                    episode_values[i]=((fault[begin:begin+len(clean)]-data.center)/data.scale).astype(np.float32)
                    np.testing.assert_allclose(episode_values[i][:config['onset']],clean[:config['onset']],rtol=1e-5,atol=1e-5)
                    events[i]['mechanism']='Reduced incident coupling in affected dynamical rows; propagated effects may reach other nodes'
        for tick,end in enumerate(times):
            budget.check();synchronize(device);timer=time.perf_counter()
            target_start=start+int(end)-horizon+1
            # With end<=311 and onset192, every conditioning context remains
            # pre-event. History contamination is tested in a separate study.
            if target_start-start>config['onset']:raise ValueError('Core reuse requires fault-free conditioning history')
            clean_block=torch.as_tensor(clean[end-horizon+1:end+1],device=device)
            clean_features=scan.extract(clean_block)
            references={};generated_features={};summaries={}
            for reference in reference_names:
                samples=issue_reference(model,data,values,target_start,horizon,config,device,reference,bootstrap,seed+target_start)
                references[reference]=samples
                generated_features[reference]=scan.extract(samples.masked_fill(~torch.isfinite(clean_block)[None],float('nan')))
                summaries[reference]=summarize_reference(generated_features[reference],floor)
                if tick==len(times)-1:
                    fidelity.append({'split':'test_untouched','reference':reference,'base':base,**prediction_fidelity(clean_block,samples)})
                # Compact feature samples support re-analysis without diffusion.
                np.savez_compressed(samples_dir/f'{reference}-base{base}-time{end}.npz',features=generated_features[reference].values.cpu().numpy(),target_start=target_start,
                                    issue_timestamp=data.timestamps[target_start-1],observation_timestamp=data.timestamps[target_start+horizon-1])
            for event_index in selected:
                event=events[event_index];episode=episode_values[event_index]
                block=torch.as_tensor(episode[end-horizon+1:end+1],device=device)
                observed=scan.extract(block);all_scores={};diagnostics={}
                for reference in reference_names:
                    generated=generated_features[reference]
                    if event['kind']=='dropout':
                        generated=scan.extract(references[reference].masked_fill(~torch.isfinite(block)[None],float('nan')))
                    scores,diagnostic=score_features(observed,generated,floor,summary=None if event['kind']=='dropout' else summaries[reference])
                    all_scores.update({f'{reference}/{key}':value for key,value in scores.items()})
                    diagnostics[reference]=diagnostic
                residual=gdn_residuals(gdn,episode[:end+1],config['context'],device)
                all_scores.update(classic_scores(block,scan,center,spread,residual,gdn_center,gdn_scale))
                maxima,orders=score_summary(all_scores,scan,len(data.node_ids))
                saved_group_scores[event_index,tick]=torch.stack([all_scores[m] for m in group_methods]).cpu().numpy()
                event_maxima[event_index,tick]=[maxima[m] for m in methods]
                method_quality[event_index,tick]=[float(torch.isfinite(all_scores[m]).float().mean()) for m in methods]
                rankings[event_index,tick]=np.stack([orders[m] for m in methods])
                quality[event_index,tick]=float(observed.eligible.float().mean())
                if event['nodes']:
                    overlaps=np.array([set_metrics(g,event['nodes'])['iou'] for g in scan.groups])
                    best=int(np.argmax(overlaps))
                    directions[event_index,tick]=float(observed.values[0,best,0]-clean_features.values[0,best,0])
                    observed_changes[event_index,tick]=float(observed.values[0,best,1])
                # Auditable replay records for the first copy/noise event and controls.
                if seed==17 and event_index in [0,18,len(events)-2,len(events)-1]:
                    replay_dir=directory/'replay';replay_dir.mkdir(exist_ok=True)
                    diagnostic=diagnostics['diffusion']
                    matrix_current=[r[0].cpu().numpy() for r in observed.correlations]
                    matrix_expected=[r.cpu().numpy() for r in diagnostic['matrix_center']]
                    write_json(replay_dir/f'{event_index}-{tick}.json',{'event':event,'end':int(end),'target_start':target_start,
                               'issuance_timestamp_ns':int(data.timestamps[target_start-1]),'observation_timestamp_ns':int(data.timestamps[target_start+horizon-1]),
                               'observed':diagnostic['observed'].cpu().numpy(),'reference_center':diagnostic['reference_center'].cpu().numpy(),
                               'reference_low':diagnostic['reference_low'].cpu().numpy(),'reference_high':diagnostic['reference_high'].cpu().numpy(),
                               'eligible':diagnostic['eligible'].cpu().numpy(),'flatline':diagnostic['flatline'].cpu().numpy(),
                               'common_rows':diagnostic['common_rows'].cpu().numpy(),'scores':{k:v.cpu().numpy() for k,v in all_scores.items()},
                               'correlations':matrix_current,'expected_correlations':matrix_expected,
                               'raw':episode[end-horizon+1:end+1],
                               'raw_low':torch.nanquantile(references['diffusion'],.05,dim=0).cpu().numpy(),
                               'raw_high':torch.nanquantile(references['diffusion'],.95,dim=0).cpu().numpy()})
            synchronize(device);timings.append({'stage':'test_shared_reference_and_all_injections','seconds':time.perf_counter()-timer,'events':len(selected)})
        print(data.name,graph,seed,'scored base',base+1,'/',len(bases),flush=True)
    pvalues=np.stack([rank_pvalues(calibration_array[:,k],event_maxima[:,:,k]) for k in range(len(methods))],-1)
    for event in events:
        event['oracle_group_iou']=oracle_overlap(scan.groups,event['nodes']) if event['is_fault'] else None
        start,stop=bases[event['base']];event['base_start']=start;event['base_stop']=stop
    np.savez_compressed(directory/'predictions.npz',maxima=event_maxima,pvalues=pvalues,ranked_nodes=rankings,
                        eligible_fraction=quality,method_eligible_fraction=method_quality,entropy_direction=directions,observed_delta_h=observed_changes,
                        times=times,methods=methods,localization_budget=chosen_budget)
    np.savez_compressed(samples_dir/'group_scores.npz',calibration=np.stack(calibration_groups),
                        scores=saved_group_scores,methods=group_methods)
    write_json(directory/'events.json',events)
    write_json(directory/'fidelity.json',fidelity)
    write_json(directory/'runtime.json',{'timings':timings,'total_seconds':time.monotonic()-started,
               'peak_gpu_bytes':torch.cuda.max_memory_allocated() if device=='cuda' else None})
    status={'status':'complete','dataset':data.name,'seed':seed,'graph':graph,'events':len(events),
            'fault_events':sum(e['is_fault'] for e in events),'independent_recording_blocks':len(bases),
            'calibration_units':len(calibration),'methods':methods,'elapsed_seconds':time.monotonic()-started,
            'checkpoint_sha256':digest(experiment_dir/'checkpoints'/f'{data.name}-diffusion-{graph}-{seed}.pt')}
    write_json(directory/'status.json',status)
    return status
