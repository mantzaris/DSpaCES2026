"""A fair local/global scan at an identical, sufficiently supported long window.

The short trained neural horizon cannot support a full-network covariance.
Use the same intact-block bootstrap for both arms, with independently calibrated
scan maxima. This sensitivity changes the window, not the primary experiment.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from .calibration import rank_pvalues
from .data import load_data
from .entropy import trajectory_features
from .evaluation import alert_intervals, match_events
from .experiment import base_episodes, event_manifest
from .features import Scan
from .localization import participation, set_metrics
from .models import calendar
from .reference import BlockBootstrap
from .synthetic import inject, simulate, system
from .utils import Budget, write_json


@torch.no_grad()
def compare_global(root: Path, config: dict, budget: Budget) -> None:
    data=load_data(root,'synthetic64');x=data.standardized
    window=160;lag=40;horizon=200
    local=Scan(data.adjacency,data.coordinates,data.channels,dict(config,windows=[window]),'cuda')
    bootstrap=BlockBootstrap(data,48,horizon,'cuda')
    arms=['local','global']

    def extract(block: torch.Tensor) -> dict[str,torch.Tensor]:
        if block.ndim==3:block=block[None]
        global_values=trajectory_features(block.permute(0,3,1,2),window,lag,config['shrinkage'])[0][...,:2]
        return {'local':local.extract(block).values[...,:2],'global':global_values}

    development={arm:[] for arm in arms}
    dev=data.issuance_indices(1,48,horizon,248)[:12]
    for start in dev:
        for arm,values in extract(torch.as_tensor(x[start:start+horizon],device='cuda')).items():
            development[arm].append(values[0])
    floors={}
    for arm in arms:
        values=torch.stack(development[arm])
        floors[arm]=(.05*(torch.nanquantile(values,.75,dim=0)-torch.nanquantile(values,.25,dim=0))).nan_to_num(nan=0).clamp_min(1e-4)

    def compare(block: np.ndarray, references: dict[str,torch.Tensor]) -> dict[str,np.ndarray]:
        observed=extract(torch.as_tensor(block,device='cuda'));scores={}
        for arm in arms:
            reference=references[arm]
            center=torch.nanmedian(reference,dim=0).values
            scale=1.4826*torch.nanmedian((reference-center).abs(),dim=0).values+floors[arm]
            eligible=torch.isfinite(reference).all(-1).float().mean(0)>=.8
            score=((observed[arm][0]-center).abs()/scale).max(-1).values
            scores[arm]=score.masked_fill(~eligible,float('nan')).cpu().numpy()
        return scores

    def draw(start: int, mask: np.ndarray | None = None) -> tuple[torch.Tensor,dict[str,torch.Tensor]]:
        budget.check()
        samples=bootstrap.sample(x[start-48:start],calendar(data.timestamps[start:start+horizon]),32,50001+start)
        if mask is None:mask=np.isfinite(x[start:start+horizon])
        samples=samples.masked_fill(~torch.as_tensor(mask,device='cuda')[None],float('nan'))
        return samples,extract(samples)

    cal_indices=data.issuance_indices(2,48,horizon,248)
    cal={arm:[] for arm in arms}
    for start in cal_indices:
        _,refs=draw(int(start));scores=compare(x[start:start+horizon],refs)
        for arm in arms:cal[arm].append(float(np.max(np.where(np.isfinite(scores[arm]),scores[arm],-np.inf))))

    bases=base_episodes(data,config);events=event_manifest(data,config,bases)
    times=np.arange(48+horizon-1,config['episode_length'],config['alert_stride'])
    maxima=np.full((len(events),len(times),2),-np.inf)
    node_orders=np.zeros((len(events),len(times),24),dtype=int)
    test_bounds=data.episode_bounds[data.episode_bounds[:,2]==3]
    for base,(start,stop) in enumerate(bases):
        indices=[i for i,e in enumerate(events) if e['base']==base]
        clean=x[start:stop];episodes={}
        for i in indices:
            e=events[i]
            episodes[i]=clean if e['kind']=='untouched' else inject(clean,e['nodes'],e['onset'],e['duration'],e['kind'],e['severity'],e['seed'])
            if e['kind']=='decouple':
                number=next(i for i,b in enumerate(test_bounds) if b[0]<=start<b[1])
                coords,_,transition,_=system(64)
                raw=simulate(coords,transition,int(test_bounds[number,1]-test_bounds[number,0]),164300+number,'cuda',e)
                begin=start-int(test_bounds[number,0])
                episodes[i]=(raw[begin:begin+len(clean)]-data.center)/data.scale
        for tick,end in enumerate(times):
            target_start=start+int(end)-horizon+1
            samples,refs=draw(target_start)
            for i in indices:
                block=episodes[i][end-horizon+1:end+1]
                masked_refs=(extract(samples.masked_fill(~torch.as_tensor(np.isfinite(block),device='cuda')[None],float('nan')))
                             if events[i]['kind']=='dropout' else refs)
                scores=compare(block,masked_refs)
                for j,arm in enumerate(arms):
                    maxima[i,tick,j]=np.max(np.where(np.isfinite(scores[arm]),scores[arm],-np.inf))
                node_orders[i,tick]=np.argsort(-participation(scores['local'],local.groups,64),kind='stable')[:24]
    pvalues=np.stack([rank_pvalues(np.asarray(cal[arm]),maxima[:,:,j]) for j,arm in enumerate(arms)],-1)
    selected=json.loads((root/'experiments/full/score-synthetic64-physical-17/development_selection.json').read_text())['localization_budget']
    rows=[]
    for j,arm in enumerate(arms):
        for i,event in enumerate(events):
            truth=[(event['onset'],event['onset']+event['duration']-1)] if event['is_fault'] else []
            alerts=alert_intervals(times,pvalues[i,:,j]<=.1,12)
            matched=match_events(alerts,truth,0);iou=0.
            if matched['matches']:
                index,_=matched['matches'][0];tick=int(np.where(times==alerts[index][0])[0][0])
                # A global trace supplies only the entire network as its location.
                predicted=node_orders[i,tick,:selected].tolist() if arm=='local' else list(range(64))
                iou=set_metrics(predicted,event['nodes'])['iou']
            rows.append({'arm':arm,'event':event['id'],'base':event['base'],'kind':event['kind'],
                         'is_fault':event['is_fault'],'duration':event['duration'],'tp':matched['tp'],
                         'fp':matched['fp'],'localization_iou':iou,
                         'eligible_fraction':float(np.isfinite(maxima[i,:,j]).mean()),
                         'flagged_issuances':int((pvalues[i,:,j]<=.1).sum()),'issuances':len(times)})
    out=root/'experiments/sensitivity'
    np.savez_compressed(out/'global-predictions.npz',maxima=maxima,pvalues=pvalues,times=times,
                        calibration=np.array([cal[arm] for arm in arms]))
    write_json(out/'global-comparison.json',{'dataset':data.name,'reference':'bootstrap','samples':32,
               'window':window,'lag':lag,'calibration_units':len(cal_indices),'rows':rows,
               'first_observation_relative_to_onset':int(times[0]-config['onset']),
               'interpretation':'Both arms use W=160 and the same samples. Short events may finish before the first eligible issuance; this is not the primary W=24/48/96 comparison.'})
