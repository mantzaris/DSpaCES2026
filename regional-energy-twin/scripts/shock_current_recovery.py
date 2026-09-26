"""Predeclared current-record reconstruction on one cancellation episode.

This replays the saved acquisition trace; it requests no additional observations.
The primary predictive comparison remains the frozen one-hour/six-hour replay.
"""
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
from evidence_fusion.shock_gaussian import ShockGaussian
from evidence_fusion.shock_overlays import overlay


class CurrentRecordGaussian(ShockGaussian):
    horizons=(0,)


def main():
    root=Path('results/shock');cfg=json.loads(Path('configs/regional_shock.json').read_text())
    model=dict(np.load('data/regional/refinement/model.npz',allow_pickle=False))
    with np.load('data/regional/shock/background_00.npz') as p:background=p['values'];slots=p['slots']
    ep=next(e for e in json.loads((root/'run/episodes.json').read_text()) if e['episode']=='b00_cancel_exact_3.0')
    readings,targets,shift,signature,_=overlay(background,model,ep['family'],ep['magnitude'],ep['seed'],cfg['window'])
    trace=pd.read_csv(root/'run/access.csv.gz',keep_default_na=False)
    trace=trace[trace.episode==ep['episode']]
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False
    engine=CurrentRecordGaussian(model,cfg['window'])
    groups=model['groups'];rows=[]
    for step in (12,26,38):
        cutoff=cfg['window']-1+step;lower=cutoff-cfg['window']+1
        window=readings[lower:cutoff+1].T
        baseline=model['profile'][slots[lower:cutoff+1]].T.astype(float)
        native=np.isfinite(window)
        aggregate=np.stack([np.nansum(window[groups==g]-baseline[groups==g],axis=0) for g in range(16)])
        for method in ('M0','M1','M2','M3','M4'):
            known=np.full_like(window,np.nan)
            for r in trace[(trace.method==method)&(trace.step>=lower)&(trace.step<=cutoff)].itertuples():
                ids=np.arange(len(groups)) if r.households=='ALL' else np.fromstring(r.households,sep=' ',dtype=int)
                known[ids,int(r.step)-lower]=readings[int(r.step),ids]-baseline[ids,int(r.step)-lower]
            start=time.perf_counter()
            pred,_=engine.infer(native,known,aggregate,np.isfinite(targets[cutoff])[None,:],
                model['profile'][slots[cutoff]][None,:])
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            mu=pred[0]['mean'].cpu().numpy();var=pred[0]['variance'].cpu().numpy()
            ids=np.asarray(ep['affected_ids']);ids=ids[np.isfinite(targets[cutoff,ids])]
            seen=np.isfinite(known[ids,-1]);unread=ids[~seen]
            rows.append(dict(episode=ep['episode'],step=step,method=method,affected_valid=len(ids),
                currently_observed_affected=int(seen.sum()),affected_mae=float(abs(mu[ids]-targets[cutoff,ids]).mean()),
                unread_affected_mae=float(abs(mu[unread]-targets[cutoff,unread]).mean()) if len(unread) else np.nan,
                min_current_variance=float(var.min()),seconds=elapsed,new_observations=0,
                revealed_record_reconstruction_error=float(abs(mu[ids[seen]]-targets[cutoff,ids[seen]]).max()) if seen.any() else 0.))
    pd.DataFrame(rows).to_csv(root/'current_recovery.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False),flush=True)
    # Repair only the illustrative series' support: original metric evaluation
    # already excludes missing targets. Replay immutable traces, never policies.
    engine=ShockGaussian(model,cfg['window'])
    original=pd.read_csv(root/'run/figure.csv.gz')
    original=original[original.episode==ep['episode']]
    figure=[];max_match=0.
    for step in range(cfg['steps']):
        cutoff=cfg['window']-1+step;lower=cutoff-cfg['window']+1
        window=readings[lower:cutoff+1].T
        baseline=model['profile'][slots[lower:cutoff+1]].T.astype(float)
        native=np.isfinite(window)
        aggregate=np.stack([np.nansum(window[groups==g]-baseline[groups==g],axis=0) for g in range(16)])
        for method in ('M0','M1','M2','M3','M3_fixed','M4'):
            known=np.full_like(window,np.nan)
            tm='M3' if method=='M3_fixed' else method
            for r in trace[(trace.method==tm)&(trace.step>=lower)&(trace.step<=cutoff)].itertuples():
                ids=np.arange(len(groups)) if r.households=='ALL' else np.fromstring(r.households,sep=' ',dtype=int)
                known[ids,int(r.step)-lower]=readings[int(r.step),ids]-baseline[ids,int(r.step)-lower]
            indices=[cutoff+h for h in engine.horizons]
            support=np.stack([np.ones(len(groups),bool)]+[np.isfinite(targets[t]) for t in indices[1:]])
            pred,_=engine.infer(native,known,aggregate,support,model['profile'][slots[indices]])
            for hi,horizon in enumerate((2,12),start=1):
                row=original[(original.step==step)&(original.method==method)&(original.horizon==horizon)].iloc[0].to_dict()
                mu=pred[hi]['mean'].cpu().numpy()
                max_match=max(max_match,abs(float(pred[hi]['region_mean'])-row['forecast_region']))
                for side,label in [('plus','positive_ids'),('minus','negative_ids')]:
                    ids=np.array(ep[label]);ids=ids[np.isfinite(targets[cutoff+horizon,ids])]
                    row['forecast_'+side]=float(mu[ids].mean()) if len(ids) else np.nan
                    row[side+'_target_support']=len(ids)
                figure.append(row)
    if max_match>1e-7:raise ArithmeticError('Saved-trace reconstruction differs from frozen forecast')
    pd.DataFrame(figure).to_csv(root/'figure_common_support.csv',index=False)
    (root/'figure_support_check.json').write_text(json.dumps(dict(episode=ep['episode'],
        saved_region_mean_max_discrepancy=max_match,new_observations=0,
        corrected_field='Illustrative local forecast means now use the same available target IDs as observed local means; main metrics were already correct'),indent=2)+'\n')
    print('Figure support reconstruction maximum regional difference',max_match,flush=True)


if __name__=='__main__':main()
