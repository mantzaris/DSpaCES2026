"""Explicit B2/B3 evaluation added during the final comparator audit.

The frozen primary PCA comparator uses standardized current-coordinate maxima.
This supplement uses the conventional total squared reconstruction error and
all-coordinate contributions. It changes no primary selection or model state.
"""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.baselines import PCADetector
from iot_repair.calibration import null_tail_value
from iot_repair.experiment import json_save
from iot_repair.metrics import ap,paired_ap_interval,task_cases,scores_for
from iot_repair.artifacts import load_case_arrays
threadpool_limits(4)
out=ROOT/'results/pca_total';out.mkdir(exist_ok=True);reports={}
for name in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    study=ROOT/'results/study'/name;params=json.loads((study/'frozen.json').read_text());split_cases={};results={};raw={};audits=[]
    models={p.stem:PCADetector.load(p,lag=int(p.stem.split('_')[1][3:])) for p in sorted((ROOT/'results/models'/name).glob('pca_lag*.npz'))}
    for split in ['development','calibration','test']:
        cases=task_cases([json.loads(p.read_text()) for p in sorted((study/split).glob(split+'_*.json'))],'observation');split_cases[split]=cases
        x=np.stack([load_case_arrays(study/split/case['raw_artifact'])['input'] for case in cases]);results[split]={}
        for key,model in models.items():
            start=time.perf_counter();total=model.total_reconstruction_score(x);contributions=model.all_coordinate_contributions(x);seconds=time.perf_counter()-start
            # Independent B1--B3 projection, complete squared norm and mean
            # attribution, including all lag coordinates rather than only last.
            vectors=model.vectors(x).astype('float64');valid=np.isfinite(vectors)
            centered=np.where(valid,vectors,model.fill)-model.portable_mean
            error=(centered-centered@(model.portable_components.astype('float64').T@model.portable_components.astype('float64')))**2
            error[~valid]=np.nan;error=error.reshape(len(x),x.shape[-1]-model.lag+1,x.shape[1],model.lag)[:,-8:]
            q=np.nansum(error,axis=(2,3));q[~np.isfinite(error).any(axis=(2,3))]=np.nan;q=np.nanmean(q,axis=1)
            attribution=np.nanmean(error,axis=(1,3))
            np.testing.assert_allclose(total,q,rtol=2e-5,atol=2e-6,equal_nan=True)
            np.testing.assert_allclose(contributions,attribution,rtol=2e-5,atol=2e-6,equal_nan=True)
            audits.append(dict(split=split,method=key,max_total_error=float(np.nanmax(np.abs(total-q))),rtol=2e-5,atol=2e-6))
            results[split][key]=dict(total=np.nan_to_num(total,nan=-1e12),contributions=contributions,seconds=seconds,unavailable_windows=int(np.isnan(total).sum()))
            raw[split+'_'+key+'_total']=total;raw[split+'_'+key+'_contributions']=contributions
    ydev=np.array([int(c['track']=='observation') for c in split_cases['development']]);selection={}
    for lag in [1,4]:
        eligible=[key for key in models if key.startswith('pca_lag'+str(lag)+'_')]
        selection[str(lag)]=max(eligible,key=lambda key:ap(ydev,results['development'][key]['total']))
    test=split_cases['test'];y=np.array([int(c['track']=='observation') for c in test]);blocks=[c['block'] for c in test]
    proposed=[float(scores_for(c,'proposed','observation',params)[0].max()) for c in test];metrics={}
    for lag,key in selection.items():
        data=results['test'][key];z=data['total'];cs=data['contributions']
        refs=[float(score) for score,case in zip(results['calibration'][key]['total'],split_cases['calibration']) if case['track']=='clean' and case['calibration_fold']=='null']
        tails=null_tail_value(refs,z);positive=np.flatnonzero(y);top1=[bool(np.isfinite(cs[i]).any() and test[i]['observation_truth'][int(np.nanargmax(cs[i]))]) for i in positive]
        metrics[lag]=dict(method=key,development_ap=ap(ydev,results['development'][key]['total']),window_ap=ap(y,z),top1=float(np.mean(top1)),windows=len(y),prevalence=float(y.mean()),
            null_reference=refs,fpr_005=float(np.mean(tails[y==0]<=.05)),recall_005=float(np.mean(tails[y==1]<=.05)),
            paired_proposed_minus_total_pca=paired_ap_interval(y,proposed,z,blocks),seconds_per_window=data['seconds']/len(test),unavailable_windows=data['unavailable_windows'],
            cases=[dict(id=c['id'],block=c['block'],score=float(s),tail=float(p),label=int(label)) for c,s,p,label in zip(test,z,tails,y)])
    path=out/(name+'.npz');np.savez_compressed(path,**raw)
    reports[name]=dict(selection=selection,metrics=metrics,audits=audits,artifact=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        case_order={split:[c['id'] for c in cases] for split,cases in split_cases.items()})
    print(name,{lag:row['window_ap'] for lag,row in metrics.items()},flush=True)
json_save(out/'analysis.json',dict(results=reports,scope='Final comparator-completeness audit. Rank is selected on development data independently for each lag. B2 sums squared residuals across the full embedding, B3 averages all sensor coordinates. Missing coordinates are excluded. This supplement does not replace the frozen common-protocol primary comparator.'))
