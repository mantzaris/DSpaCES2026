"""Measure CUDA reduction repeatability and test exact-copy invariance deterministically."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
from pathlib import Path
import copy,json,sys
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save
from iot_repair.pipeline import score_candidates

torch.set_num_threads(4);reports=[]
for name in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    folder=ROOT/'results/study'/name/'test';path=sorted(folder.glob('test_*_observation.json'))[0]
    case=json.loads(path.read_text());saved=np.load(folder/case['raw_artifact']);params=json.loads((folder.parent/'frozen.json').read_text())
    models,graph=load_models(ROOT,name,('diffusion',));x=saved['input'];kwargs=dict(seed=case['inference_seed'],kappa=params['kappa'],edit_weight=params['lambda'])
    outcomes=[];scores=[]
    torch.use_deterministic_algorithms(False)
    for repeat in range(3):
        rows,raw,_=score_candidates(models['diffusion'],x,case['graph'],case['candidates'],**kwargs)
        actual={(r['kind'],r['index']):r for r in rows};expected={(r['kind'],r['index']):r for r in case['records']}
        outcomes.append(dict(repeat=repeat,max_loss_difference=float(max(np.nanmax(np.abs(raw[k]-saved[k])) for k in ['loss_before','loss_after'])),
            max_prediction_difference=float(max(np.nanmax(np.abs(raw[k]-saved[k])) for k in ['witness_samples_before','witness_samples_after'])),
            max_score_difference=float(max(abs(actual[key]['score']-expected[key]['score']) for key in actual)),
            top_observation=next(r['index'] for r in rows if r['kind']=='observation')))
        scores.append([actual[key]['score'] for key in sorted(actual)])
    torch.use_deterministic_algorithms(True)
    rows,raw,_=score_candidates(models['diffusion'],x,case['graph'],case['candidates'],**kwargs)
    duplicate=np.concatenate([x,x[[0]]]);g=copy.deepcopy(case['graph']);g['edges']+=copy.deepcopy(g['edges'][:3])
    other,other_raw,_=score_candidates(models['diffusion'],duplicate,g,case['candidates'],record_ids=[f'channel_{i}' for i in range(len(x))]+['channel_0'],**kwargs)
    for key in raw:np.testing.assert_array_equal(raw[key],other_raw[key])
    reports.append(dict(dataset=name,case=case['id'],seed=kwargs['seed'],ordinary_cuda_repetitions=outcomes,
        maximum_repeat_score_spread=float(np.ptp(np.asarray(scores),axis=0).max()),deterministic_copy_invariance='exact array equality',
        deterministic_algorithms=True,workspace_config=os.environ['CUBLAS_WORKSPACE_CONFIG']))
    print(name,outcomes,flush=True)
json_save(ROOT/'results/audits/inference_repeatability.json',dict(cases=reports,
    scope='Saved predictive draws remain the definitive empirical inputs. Float32 CUDA index_add reductions may vary under fixed random seeds; deterministic mode is tested separately.'))
