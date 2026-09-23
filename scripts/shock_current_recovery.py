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


if __name__=='__main__':main()
