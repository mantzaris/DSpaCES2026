"""Exact portable/checkpoint state and deterministic inference agreement.

The original study allowed ordinary CUDA reductions. Their saved draws remain
canonical empirical inputs. Replays of those draws are measured, not described
as bitwise reproducible merely because a random seed was saved.
"""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
from pathlib import Path
import hashlib,json,sys
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save
from iot_repair.pipeline import score_candidates

torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
manifest=json.loads((ROOT/'results/model_weights/manifest.json').read_text())
for entry in manifest['models']:
    assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
reports=[]
for dataset in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    path=sorted((ROOT/'results/study'/dataset/'test').glob('test_*_observation.json'))[0]
    case=json.loads(path.read_text());saved=np.load(path.parent/case['raw_artifact'])
    assert all((ROOT/'results/models'/dataset/f'diffusion_{seed}.pt').exists() for seed in [1101,2202,3303]), 'Original checkpoints are required for this export audit'
    portable,graph=load_models(ROOT,dataset,('diffusion',),inference_states=True)
    checkpoint,_=load_models(ROOT,dataset,('diffusion',),inference_states=False)
    for left,right in zip(portable['diffusion'],checkpoint['diffusion']):
        for key,value in left.state_dict().items():assert torch.equal(value,right.state_dict()[key])
    params=json.loads((path.parent.parent/'frozen.json').read_text())
    kwargs=dict(seed=case['inference_seed'],kappa=params['kappa'],edit_weight=params['lambda'])
    rows,raw,_=score_candidates(portable['diffusion'],saved['input'],case['graph'],case['candidates'],**kwargs)
    other,reference,_=score_candidates(checkpoint['diffusion'],saved['input'],case['graph'],case['candidates'],**kwargs)
    for key in raw:np.testing.assert_array_equal(raw[key],reference[key])
    expected={(r['kind'],r['index']):r for r in other}
    for row in rows:
        for term in ('mean_gain','model_instability','edit_cost','score','monte_carlo_standard_error'):
            assert row[term]==expected[(row['kind'],row['index'])][term]
    original={(r['kind'],r['index']):r for r in case['records']}
    reports.append(dict(dataset=dataset,case=case['id'],raw_sha256=case['raw_sha256'],seed=kwargs['seed'],candidates=len(rows),
        portable_vs_checkpoint='exact state and predictive array equality under deterministic CUDA reductions',
        max_score_difference_from_original_study=float(max(abs(row['score']-original[(row['kind'],row['index'])]['score']) for row in rows)),
        note='Original study used ordinary CUDA reductions. See inference_repeatability.json. All published scores are independently audited from the saved original draws.'))
json_save(ROOT/'results/audits/portable_models.json',dict(weight_files_verified=len(manifest['models']),cases=reports,
    deterministic_algorithms=True,workspace_config=os.environ['CUBLAS_WORKSPACE_CONFIG']))
print('Portable weights exactly matched checkpoint inference in',len(reports),'saved input cases')
