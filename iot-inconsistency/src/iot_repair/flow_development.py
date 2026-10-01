"""Development-only selections and bounded additional neural fits."""
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score
import torch

from .flow_data import configuration, build_cases, graph_for, sha256
from .flow_training import fit_flow, load_flow
from .flow_inference import infer_case
from .flow_ganf import fit_ganf
from .experiment import json_save


def finish_neural_development(root):
    root=Path(root);config=configuration(root);output=root/'results/graph_flow_v1/development'
    for dataset in config['datasets']:
        selection=json.loads((output/(dataset+'_models.json')).read_text())['selected'];spec=selection['specification']
        members=[fit_flow(root,dataset,spec['capacity'],spec['context_length'],seed) for seed in config['seeds']]
        own=[fit_flow(root,dataset,spec['capacity'],spec['context_length'],seed,mode='own_history') for seed in config['seeds']]
        curve=[]
        if dataset in config['learning_curve_datasets']:
            for fraction in config['learning_curve_fractions']:
                curve.append(fit_flow(root,dataset,spec['capacity'],spec['context_length'],config['seeds'][0],fraction=fraction))
        json_save(output/(dataset+'_members.json'),dict(members=members,own_history=own,learning_curve=curve))
        del own;torch.cuda.empty_cache()
        selection_path=output/(dataset+'_scoring.json')
        if not selection_path.exists():
            models=[load_flow(root,r) for r in members];cases=build_cases(root,dataset,'development');graph=graph_for(root,dataset)
            scores={};ess=[];truth=[];eligible=[];timing=[]
            for i,case in enumerate(cases):
                result=infer_case(models,case['values'],graph,spec['context_length'],sample_count=2048,scale=1.,seed=20261001+i,sensitivity=True)
                for key,value in result['scores'].items():scores.setdefault(key,[]).append(value)
                ess.append(result['ess']);truth.append(case['truth']);eligible.append(result['eligible']);timing.append(result['seconds'])
                if i%25==0:print(dataset,'development score',i,'/',len(cases),flush=True)
            scores={k:np.asarray(v) for k,v in scores.items()};truth=np.asarray(truth);eligible=np.asarray(eligible)
            scale_grid={str(scale):float(average_precision_score(truth.ravel(),scores['scale_'+str(scale)].ravel())) for scale in config['corruption_scale_grid']}
            scale=max(config['corruption_scale_grid'],key=lambda v:(scale_grid[str(v)],-v))
            # Sample-count choice uses the selected q, not an unrelated scale.
            if scale!=1.:
                for key in ['M32','M128','M512','M2048']:scores[key]=[]
                for i,case in enumerate(cases):
                    result=infer_case(models,case['values'],graph,spec['context_length'],sample_count=2048,scale=scale,seed=20261001+i,sensitivity=True)
                    for key in ['M32','M128','M512','M2048']:scores[key].append(result['scores'][key])
                for key in ['M32','M128','M512','M2048']:scores[key]=np.asarray(scores[key])
            sensitivity=[];chosen=2048
            for count in config['sample_counts']:
                error=np.abs(scores['M'+str(count)][eligible]-scores['M2048'][eligible])
                correlation=float(spearmanr(scores['M'+str(count)][eligible],scores['M2048'][eligible]).statistic)
                row=dict(samples=count,error_p95=float(np.quantile(error,.95)),spearman=correlation,
                         candidate_ap=float(average_precision_score(truth.ravel(),scores['M'+str(count)].ravel())))
                sensitivity.append(row)
                if chosen==2048 and row['error_p95']<=config['sample_score_error_tolerance'] and correlation>=config['sample_rank_correlation_minimum']:chosen=count
            arrays=output/(dataset+'_flow_predictions.npz')
            np.savez_compressed(arrays,truth=truth,eligible=eligible,ess=np.asarray(ess),**scores)
            json_save(selection_path,dict(scale=scale,sample_count=chosen,scale_development_ap=scale_grid,sample_sensitivity=sensitivity,
                       prediction_sha256=sha256(arrays),timing_seconds=timing,
                       selection='q scale maximizes development candidate AP; smallest M passing fixed tolerance versus M=2048; no test input'))
            del models;torch.cuda.empty_cache()
        ganf_path=output/(dataset+'_ganf.json')
        if not ganf_path.exists():
            grid=[fit_ganf(root,dataset,width,config['seeds'][0]) for width in config['ganf_widths']]
            best=min(grid,key=lambda row:row['development_nll']);width=best['specification']['width']
            members=[fit_ganf(root,dataset,width,seed) for seed in config['seeds']]
            json_save(ganf_path,dict(grid=grid,members=members,selection='Minimum normal development coordinate NLL'))
        print('Completed neural development',dataset,flush=True)
