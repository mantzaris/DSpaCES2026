"""Development-only selection, followed by disjoint null/probability calibration."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.metrics import *
from iot_repair.experiment import json_save
from iot_repair.faults import content_hash
p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--stage',choices=['development','calibration'],required=True);a=p.parse_args()
out=ROOT/'results/study'/a.dataset;config=json.loads((ROOT/'configs/study.json').read_text())
def load(split):
    directory=out/split
    if not (directory/'complete.json').exists():raise RuntimeError('Incomplete '+split)
    return [json.loads(p.read_text()) for p in sorted(directory.glob(split+'_*.json'))]
if a.stage=='development':
    cases=load('development');grid=[]
    for kappa in config['kappa_grid']:
      for penalty in config['lambda_grid']:
        params=dict(kappa=kappa,**{'lambda':penalty})
        metric=summarize(cases,'proposed','observation',params)
        grid.append(dict(params,window_ap=metric['window_ap']))
    # Stable, declared grid order breaks ties toward less penalization.
    best=max(grid,key=lambda row:row['window_ap']);parameters=dict(kappa=best['kappa'],**{'lambda':best['lambda']})
    pca={}
    for lag in config['pca_lags']:
        choices=[f'pca_lag{lag}_rank{rank}' for rank in config['pca_rank_grid']]
        pca[str(lag)]=max(choices,key=lambda name:summarize(cases,name,'observation',parameters)['window_ap'])
    baselines=['gdn','backbone','diffad']+list(pca.values())
    available=set(cases[0]['baseline_sensor_scores']);baselines=[x for x in baselines if x in available]
    baseline_scores={name:summarize(cases,name,'observation',parameters)['window_ap'] for name in baselines}
    parameters.update(pca=pca,strongest_baseline=max(baseline_scores,key=baseline_scores.get),baseline_development_ap=baseline_scores,
                      parameter_grid=grid,supervised_terms={},protocol=content_hash(config))
    for kind in ('observation','association'):
        rows=[r for case in cases for r in case['records'] if r['kind']==kind and r['support_count']>=2]
        features=np.array([[r['mean_gain'],r['model_instability'],r['edit_cost']] for r in rows]);y=np.array([r['truth'] for r in rows],int)
        scaler=StandardScaler().fit(features);model=LogisticRegression(C=1.,max_iter=2000,random_state=9026).fit(scaler.transform(features),y)
        parameters['supervised_terms'][kind]=dict(mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),coefficient=model.coef_[0].tolist(),intercept=float(model.intercept_[0]),training_prevalence=float(y.mean()))
    json_save(out/'frozen.json',parameters);print(a.dataset,'frozen',best,parameters['strongest_baseline'],flush=True)
else:
    parameters=json.loads((out/'frozen.json').read_text());cases=load('calibration');nulls={};probability={};candidate_refs={}
    methods=['proposed','R_only','no_uncertainty','no_cost','supervised_terms','gdn','backbone','diffad']+list(parameters['pca'].values())
    for kind in ('observation','association'):
      for method in (methods if kind=='observation' else ['proposed','R_only','no_uncertainty','no_cost','supervised_terms','edge_residual']):
        if method=='diffad' and method not in cases[0]['baseline_sensor_scores']:continue
        key=kind+'/'+method
        clean=[case for case in cases if case['track']=='clean' and case['calibration_fold']=='null']
        reference=[float(scores_for(case,method,kind,parameters)[0].max(initial=FLOOR)) for case in clean]
        nulls[key]=reference
        if method=='proposed':
            for support in (1,2):
                selected=[candidate_score(r,method,parameters['kappa'],parameters['lambda']) for case in clean for r in case['records'] if r['kind']==kind and r['support_count']==support]
                candidate_refs[kind+'/'+str(support)]=selected
        labeled=[case for case in task_cases(cases,kind) if case['calibration_fold']=='probability']
        features=[];labels=[]
        for case in labeled:
            scores,support=scores_for(case,method,kind,parameters);eligible=scores>FLOOR
            features.extend(scores[eligible].tolist());labels.extend(np.array(case[kind+'_truth'])[eligible].tolist())
        if len(set(labels))==2:
            values=np.array(features)[:,None];scaler=StandardScaler().fit(values)
            model=LogisticRegression(C=1.,max_iter=2000,random_state=9026).fit(scaler.transform(values),labels)
            probability[key]=dict(mean=float(scaler.mean_[0]),scale=float(scaler.scale_[0]),coefficient=float(model.coef_[0,0]),intercept=float(model.intercept_[0]),
                units=len(labels),prevalence=float(np.mean(labels)),scope='selected eligible candidates on disjoint labeled calibration blocks')
    json_save(out/'calibration_complete.json',dict(null_references=nulls,candidate_null_references=candidate_refs,probability=probability,
        frozen_sha256=hashlib.sha256((out/'frozen.json').read_bytes()).hexdigest(),
        null_blocks=sorted({case['block'] for case in cases if case['calibration_fold']=='null'}),probability_blocks=sorted({case['block'] for case in cases if case['calibration_fold']=='probability'})))
    print(a.dataset,'calibrated',len(nulls),'pipelines',flush=True)
