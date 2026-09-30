"""Actual-slope gating, distinct from being above/below the model expectation."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import torch

from .calibration import rank_pvalues
from .data import load_data
from .evaluation import alert_intervals,match_events
from .features import Scan
from .localization import participation,set_metrics
from .synthetic import inject,simulate,system
from .utils import Budget,write_json


@torch.no_grad()
def run_direction_ablation(root: Path,config: dict,budget: Budget) -> None:
    rows=[];observation_audit=[];torch.set_num_threads(4)
    for name in config['datasets']:
        data=load_data(root,name);x=data.standardized
        scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cuda')
        first=root/'experiments/full'/f'score-{name}-physical-17'
        events=json.loads((first/'events.json').read_text())
        predictions=np.load(first/'predictions.npz');times=predictions['times']
        calibration=np.load(first/'calibration.npz')['indices']
        cal_change=[]
        for start in calibration:
            budget.check()
            cal_change.append(scan.extract(torch.as_tensor(x[start:start+120],device='cuda')).values[0,:,1].cpu().numpy())
        cal_change=np.asarray(cal_change);change=[]
        for event in events:
            start=event['base_start'];clean=x[start:event['base_stop']]
            corrupted=clean if event['kind']=='untouched' else inject(clean,event['nodes'],event['onset'],event['duration'],event['kind'],event['severity'],event['seed'])
            if name.startswith('synthetic') and event['kind']=='decouple':
                boundaries=data.episode_bounds[data.episode_bounds[:,2]==3]
                episode=next(i for i,b in enumerate(boundaries) if b[0]<=start<b[1])
                coords,_,transition,_=system(len(data.node_ids))
                raw=simulate(coords,transition,int(boundaries[episode,1]-boundaries[episode,0]),100000+len(data.node_ids)*1000+300+episode,'cuda',event)
                offset=start-int(boundaries[episode,0]);corrupted=(raw[offset:offset+len(clean)]-data.center)/data.scale
            if event['is_fault']:
                old=clean[event['onset']:event['onset']+event['duration'],event['nodes']]
                new=corrupted[event['onset']:event['onset']+event['duration'],event['nodes']]
                joint=np.isfinite(old)&np.isfinite(new)
                modified=joint&(np.abs(np.where(joint,new-old,0))>1e-6)
                removed=np.isfinite(old)&~np.isfinite(new)
                if (np.isfinite(new)&~np.isfinite(old)).any():raise ValueError('Injection fabricated observed support')
                audit={'dataset':name,'event':event['id'],'kind':event['kind'],'base':event['base'],
                       'originally_observed_cells':int(np.isfinite(old).sum()),'total_target_cells':old.size,
                       'modified_finite_cells':int(modified.sum()),'removed_observations':int(removed.sum()),
                       'observable_intervention':bool(modified.any() or removed.any()),'difference_tolerance':1e-6}
                if event['kind']=='matched_covariance':
                    details=[]
                    for channel in range(old.shape[-1]):
                        valid=joint[:,:,channel].all(1);a=old[valid,:,channel].astype(float);b=new[valid,:,channel].astype(float)
                        if len(a)<3 or (np.std(a,axis=0)<1e-8).any() or (np.std(b,axis=0)<1e-8).any():continue
                        ra=np.corrcoef(a.T);rb=np.corrcoef(b.T);m=len(event['nodes'])
                        details.append({'channel':channel,'rows':len(a),'original_full_rank':bool(np.linalg.eigvalsh(ra).min()>1e-7),
                                        'mean_correlation_change':float((rb-ra).sum()/(m*(m-1))),
                                        'maximum_marginal_mean_error':float(np.max(np.abs(a.mean(0)-b.mean(0)))),
                                        'maximum_marginal_sd_error':float(np.max(np.abs(a.std(0,ddof=1)-b.std(0,ddof=1))))})
                    audit['matched_covariance_checks']=details
                observation_audit.append(audit)
            event_change=[]
            for end in times:
                budget.check()
                event_change.append(scan.extract(torch.as_tensor(corrupted[end-119:end+1],device='cuda')).values[0,:,1].cpu().numpy())
            change.append(event_change)
        change=np.asarray(change)
        for seed in config['training_seeds']:
            directory=root/'experiments/full'/f'score-{name}-physical-{seed}'
            archive=np.load(directory/'samples/group_scores.npz');predictions=np.load(directory/'predictions.npz')
            for reference in ['diffusion','bootstrap']:
                column=archive['methods'].tolist().index(reference+'/entropy')
                original=archive['scores'][:,:,column,:];cal=archive['calibration'][:,column,:]
                for label,sign in [('bidirectional',0),('actual_increase_only',1),('actual_decrease_only',-1)]:
                    scores=original if sign==0 else np.where(change*sign>0,original,0)
                    scores=np.where(np.isfinite(original),scores,np.nan)
                    cal_scores=cal if sign==0 else np.where(cal_change*sign>0,cal,0)
                    cal_scores=np.where(np.isfinite(cal),cal_scores,np.nan)
                    maxima=np.where(np.isfinite(scores),scores,-np.inf).max(-1)
                    calmax=np.where(np.isfinite(cal_scores),cal_scores,-np.inf).max(-1)
                    pvalues=rank_pvalues(calmax,maxima)
                    if sign==0:
                        primary_column=predictions['methods'].tolist().index(reference+'/entropy')
                        np.testing.assert_allclose(pvalues,predictions['pvalues'][:,:,primary_column],rtol=0,atol=0)
                    for i,event in enumerate(events):
                        flags=pvalues[i]<=.1;alerts=alert_intervals(times,flags,12)
                        truth=[(event['onset'],event['onset']+event['duration']-1)] if event['is_fault'] else []
                        matched=match_events(alerts,truth,0);iou=0.
                        if matched['matches']:
                            alert,_=matched['matches'][0];tick=int(np.where(times==alerts[alert][0])[0][0])
                            node_scores=participation(scores[i,tick],scan.groups,len(data.node_ids))
                            nodes=np.argsort(-node_scores,kind='stable')[:int(predictions['localization_budget'])].tolist()
                            iou=set_metrics(nodes,event['nodes'])['iou']
                        rows.append({'dataset':name,'seed':seed,'reference':reference,'direction_rule':label,
                                     'event':event['id'],'base':event['base'],'kind':event['kind'],'is_fault':event['is_fault'],
                                     'tp':matched['tp'],'fp':matched['fp'],'localization_iou':iou,
                                     'flagged_issuances':int(flags.sum()),'issuances':len(flags)})
    write_json(root/'experiments/sensitivity/directions.json',{'rows':rows,
               'definition':'Gate each fixed group’s bidirectional score to zero when its observed delta H has the opposite sign, retain quality NaNs, and independently recalibrate the scan. This is not the higher/lower-than-expected one-sided score.',
               'validation':'Unrestricted scores exactly reproduce every saved primary entropy p-value.'})
    write_json(root/'experiments/sensitivity/injection-observability.json',{'rows':observation_audit,
               'interpretation':'All preregistered scheduled events remain in primary denominators. This audit flags interventions with no observable effect under retained masks or covariance guards; it does not change labels or thresholds.'})
