"""Disjoint probability, window-alarm and repair-policy calibration."""
import json
from pathlib import Path

import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss,log_loss

from .flow_data import build_cases,configuration,sha256
from .flow_math import repair_outcome
from .experiment import json_save

REPAIR_METHODS={'flow_ratio':'flow_mean','flow_nll':'flow_mean','pca':'pca_mean','ppca':'ppca_mean','mixture_ppca':'mixture_ppca_mean'}


def load_predictions(root,dataset,split):
    directory=Path(root)/'results/graph_flow_v1'/dataset/split
    manifest=json.loads((directory/'manifest.json').read_text());cases=manifest['cases']
    arrays=[dict(np.load(directory/(case['id']+'.npz'),allow_pickle=False)) for case in cases]
    methods=sorted(key[6:] for key in arrays[0] if key.startswith('score_'))
    scores={method:np.stack([a['score_'+method] for a in arrays]) for method in methods}
    return cases,arrays,scores,np.stack([a['truth'] for a in arrays])


def features(scores,record):
    available=np.asarray(scores)>-1e11
    z=np.where(available,np.clip((scores-record['center'])/record['scale'],-30,30),0.)
    return np.stack([z,available.astype(float)],axis=-1).reshape(-1,2)


def fit_probability(scores,truth):
    available=scores>-1e11;values=scores[available]
    center=float(np.median(values)) if len(values) else 0.
    scale=max(float(np.quantile(values,.75)-np.quantile(values,.25)),1e-6) if len(values) else 1.
    record=dict(center=center,scale=scale,features=['standardized clipped raw score','scorable indicator'],
                candidates=int(truth.size),positives=int(truth.sum()),prevalence=float(truth.mean()))
    if len(np.unique(truth))<2:
        record.update(coefficient=[0.,0.],intercept=float(np.log((truth.sum()+.5)/(truth.size-truth.sum()+.5))),constant=True)
    else:
        model=LogisticRegression(C=1.,max_iter=500,random_state=20261001).fit(features(scores,record),truth.ravel())
        record.update(coefficient=model.coef_[0].tolist(),intercept=float(model.intercept_[0]),constant=False)
    return record


def predict_probability(scores,record):
    return expit(features(scores,record)@record['coefficient']+record['intercept']).reshape(scores.shape)


def rank_pvalues(maxima,reference):
    reference=np.asarray(reference);return (1+(reference[None,:]>=np.asarray(maxima)[:,None]).sum(1))/(len(reference)+1)


def wilson_upper(failures,count,z=1.6448536269514722):
    if count==0:return None
    p=failures/count
    return (p+z*z/(2*count)+z*np.sqrt(p*(1-p)/count+z*z/(4*count*count)))/(1+z*z/count)


def repair_rows(cases,arrays,scores,probabilities,method,configuration):
    rows=[];key=REPAIR_METHODS[method]
    for index,(case,array) in enumerate(zip(cases,arrays)):
        target=int(np.argmax(scores[index]));adequate=bool(array['eligible'][target])
        if method.startswith('flow'):adequate=adequate and bool(array['numerical_adequate'][target])
        repaired=array[key][target]
        if np.isfinite(repaired).all():
            outcome=repair_outcome(case['values'],case['reference'],repaired,target,case['truth'],configuration['repair_useful_improvement'])
        else:outcome=dict(improvement=None,failed=True,harmful=False,correct_attribution=False)
        rows.append(dict(case_id=case['id'],block=case['block'],target=target,probability=float(probabilities[index,target]),
                         adequate=adequate,**outcome))
    return rows


def risk_point(rows,threshold):
    accepted=[row for row in rows if row['adequate'] and row['probability']>=threshold]
    count=len(accepted);failures=sum(row['failed'] for row in accepted);harmful=sum(row['harmful'] for row in accepted)
    return dict(threshold=threshold,cases=len(rows),accepted=count,coverage=count/len(rows) if rows else 0.,
                failures=failures,risk=failures/count if count else None,harmful=harmful,harmful_rate=harmful/count if count else None,
                wilson_upper=wilson_upper(failures,count),
                mean_improvement=float(np.mean([row['improvement'] for row in accepted])) if count else None)


def calibrate(root):
    root=Path(root);config=configuration(root);directory=root/'results/graph_flow_v1';records={}
    for dataset in config['datasets']:
        public,arrays,scores,truth=load_predictions(root,dataset,'calibration');actual=build_cases(root,dataset,'calibration')
        assert [c['id'] for c in actual]==[c['id'] for c in public]
        role=np.array([case['calibration_role'] for case in public]);clean=np.array([case['track']=='clean' for case in public])
        probability_mask=role=='fault_probability';policy_mask=role=='repair_policy';normal_mask=(role=='normal_window_tail')&clean
        methods={}
        for method,score in scores.items():
            probability=fit_probability(score[probability_mask],truth[probability_mask])
            predicted=predict_probability(score,probability)
            normal=score[normal_mask].max(1)
            record=dict(probability=probability,normal_window_maxima=normal.tolist(),normal_windows=len(normal),
                        minimum_window_p=1/(len(normal)+1),
                        role_blocks={r:sorted(set(c['block'] for c in public if c['calibration_role']==r)) for r in config['calibration_roles']})
            if method in REPAIR_METHODS:
                rows=repair_rows(actual,arrays,score,predicted,method,config)
                policy=[row for i,row in enumerate(rows) if policy_mask[i]]
                grid=[risk_point(policy,threshold) for threshold in config['repair_probability_thresholds']]
                acceptable=[row for row in grid if row['accepted']>=10 and row['wilson_upper']<=config['repair_failure_target']]
                chosen=max(acceptable,key=lambda row:(row['coverage'],row['threshold'])) if acceptable else None
                record.update(repair_policy=dict(threshold=chosen['threshold'] if chosen else None,calibration=chosen,grid=grid,
                              rule=config['repair_policy_rule'],blocks=sorted(set(row['block'] for row in policy)),
                              dependent_cases_caveat='Wilson is a development selection heuristic, not a dependent-data guarantee'))
            methods[method]=record
        path=directory/dataset/'calibration.json';json_save(path,dict(dataset=dataset,methods=methods));records[dataset]=dict(path=str(path.relative_to(root)),sha256=sha256(path))
    json_save(directory/'calibration_complete.json',dict(datasets=records,protocol_lock_sha256=sha256(directory/'protocol_lock.json')))


def probability_metrics(truth,probability):
    truth=truth.ravel();probability=probability.ravel();bins=[]
    for left,right in zip(np.linspace(0,1,11)[:-1],np.linspace(0,1,11)[1:]):
        selected=(probability>=left)&((probability<right) if right<1 else (probability<=right))
        bins.append(dict(left=float(left),right=float(right),count=int(selected.sum()),
                         predicted=float(probability[selected].mean()) if selected.any() else None,
                         observed=float(truth[selected].mean()) if selected.any() else None))
    return dict(brier=float(brier_score_loss(truth,probability)),log_loss=float(log_loss(truth,probability,labels=[False,True])),
                prevalence=float(truth.mean()),candidates=len(truth),bins=bins)
