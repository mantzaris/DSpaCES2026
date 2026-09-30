"""Uncontended warm inference latency versus tested candidate count."""
from pathlib import Path
import json,sys,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save
from iot_repair.pipeline import screen_candidates,score_candidates
from iot_repair.associations import edge_residuals
from iot_repair.baselines import gdn_residual
torch.set_num_threads(4);rows=[]
for name in ['synthetic_32_nonlinear','synthetic_64_nonlinear']:
    models,graph=load_models(ROOT,name,('diffusion','gdn'));x=np.load(ROOT/'data/processed'/name/'test.npz')['x'][0]
    with torch.no_grad():residual=np.mean([gdn_residual(m,torch.as_tensor(x[None],device='cuda')).cpu().numpy()[0] for m in models['gdn']],axis=0)
    edges=edge_residuals(x[None],graph)[0]
    score_candidates(models['diffusion'],x,graph,screen_candidates(residual,edges,graph),seed=8411)
    for cap in [1,2,4,8]:
        candidates=screen_candidates(residual,edges,graph,cap)
        for repeat in range(5):
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
            records,raw,abstentions=score_candidates(models['diffusion'],x,graph,candidates,seed=84000+repeat)
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            rows.append(dict(dataset=name,channels=x.shape[0],candidate_cap_per_type=cap,tested_candidates=len(candidates),eligible_candidates=len(records),
                repeat=repeat,elapsed_seconds=elapsed,peak_allocated_bytes=torch.cuda.max_memory_allocated(),gpu=torch.cuda.get_device_name(),
                proposal_members=3,replicates=8,predictive_samples=8,parameter_count=sum(p.numel() for m in models['diffusion'] for p in m.parameters())))
            print(rows[-1],flush=True)
json_save(ROOT/'results/latency_scaling.json',dict(measurement='warm inference, transfer and scoring included; model loading and database writes excluded',runs=rows))
