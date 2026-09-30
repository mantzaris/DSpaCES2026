"""Pre-freeze M, L, E and neural-precision study on development windows only."""
from pathlib import Path
import argparse,json,sys,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save
from iot_repair.pipeline import score_candidates,screen_candidates
from iot_repair.faults import inject_observation
from iot_repair.associations import edge_residuals
from iot_repair.baselines import gdn_residual
p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);a=p.parse_args();torch.set_num_threads(4)
out=ROOT/'results/sensitivity'/a.dataset;out.mkdir(parents=True,exist_ok=True)
if (out/'complete.json').exists():raise SystemExit
models,graph=load_models(ROOT,a.dataset,('diffusion','gdn'))
d=np.load(ROOT/'data/processed'/a.dataset/'development.npz');reference=d['x'][d['reference']]
settings=[(3,2,8,True),(3,4,8,True),(3,8,8,True),(3,16,8,True),(3,8,4,True),(3,8,16,True),(2,8,8,True),(3,8,8,False)]
for index in range(min(3,len(reference))):
    x,truth,fault=inject_observation(reference[index],626000+index,'offset',strength=2.)
    with torch.no_grad():residual=np.mean([gdn_residual(m,torch.as_tensor(x[None],device='cuda')).cpu().numpy()[0] for m in models['gdn']],axis=0)
    candidates=screen_candidates(residual,edge_residuals(x[None],graph)[0],graph,cap=4)
    for e,m,l,amp in settings:
        name=f'case{index}_E{e}_M{m}_L{l}_amp{int(amp)}';path=out/(name+'.json')
        if path.exists():continue
        for model in models['diffusion']:model.inference_autocast=amp
        torch.cuda.reset_peak_memory_stats()
        records,raw,abstentions=score_candidates(models['diffusion'][:e],x,graph,candidates,replicates=m,predictive_samples=l,seed=8822+index)
        np.savez_compressed(out/(name+'.npz'),input=x,truth=truth,**raw)
        json_save(path,dict(E=e,M=m,L=l,neural_autocast=amp,case=index,records=records,abstentions=abstentions,peak_bytes=torch.cuda.max_memory_allocated(),
            seconds=sum(r['elapsed_seconds_per_candidate'] for r in records),fault=fault,scope='development sensitivity; not final performance'))
        if (e,m,l,amp)==(3,8,8,True):
            rows=[dict(kind=r['kind'],index=r['index'],mean_gain=float(raw['model_gains'][r['raw_index'],0]),uncertainty=None,
                score=float(raw['model_gains'][r['raw_index'],0]-.2*r['edit_cost'])) for r in records]
            json_save(out/f'case{index}_E1_uncertainty_free.json',dict(E=1,records=rows,scope='first-member gain with shared ensemble cost, U undefined'))
json_save(out/'complete.json',dict(dataset=a.dataset,development_cases=min(3,len(reference)),settings=settings,chosen_E=3,chosen_M=8,chosen_L=8,
    choice='predeclared bounded setting, no final test outcomes used'))
print(a.dataset,'development sensitivity complete',flush=True)
