"""Uncontended warm inference latency versus tested candidate count."""
from pathlib import Path
import json,os,subprocess,sys,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save,scaled
from iot_repair.pipeline import screen_candidates,score_candidates
from iot_repair.associations import edge_residuals
from iot_repair.baselines import gdn_residual
from iot_repair.calibration import null_tail_value
torch.set_num_threads(4);rows=[]
for name in ['synthetic_32_nonlinear','synthetic_64_nonlinear']:
    models,graph=load_models(ROOT,name,('diffusion','gdn'));x=np.load(ROOT/'data/processed'/name/'test.npz')['x'][0]
    folder=ROOT/'results/study'/name
    params=json.loads((folder/'frozen.json').read_text());cal=json.loads((folder/'calibration_complete.json').read_text())
    scales=json.loads((folder/'residual_scales.json').read_text())
    def execute(cap,seed):
        with torch.no_grad():residual=np.mean([gdn_residual(m,torch.as_tensor(x[None],device='cuda')).cpu().numpy()[0] for m in models['gdn']],axis=0)
        candidates=screen_candidates(scaled(residual,scales['gdn']),edge_residuals(x[None],graph)[0],graph,cap)
        records,raw,abstentions=score_candidates(models['diffusion'],x,graph,candidates,seed=seed,kappa=params['kappa'],edit_weight=params['lambda'])
        tails={kind:float(null_tail_value(cal['null_references'][kind+'/proposed'],max([r['score'] for r in records if r['kind']==kind and r['support_count']>=2],default=-1e12))) for kind in ['observation','association']}
        return candidates,records,raw,abstentions,tails
    execute(4,8411)
    for cap in [1,2,4,8]:
        for repeat in range(5):
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
            candidates,records,raw,abstentions,tails=execute(cap,84000+repeat)
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            rows.append(dict(dataset=name,channels=x.shape[0],candidate_cap_per_type=cap,tested_candidates=len(candidates),eligible_candidates=len(records),
                repeat=repeat,elapsed_seconds=elapsed,peak_allocated_bytes=torch.cuda.max_memory_allocated(),gpu=torch.cuda.get_device_name(),
                process_id=os.getpid(),reported_gpu_processes=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.strip(),
                frozen_parameters={'kappa':params['kappa'],'lambda':params['lambda']},window_tails= tails,
                tail_scope='Runtime only. Main reference tails are calibrated for four candidates per type, not the other scaling caps.',
                proposal_members=3,replicates=8,predictive_samples=8,parameter_count=sum(p.numel() for m in models['diffusion'] for p in m.parameters())))
            print(rows[-1],flush=True)
json_save(ROOT/'results/latency_scaling.json',dict(measurement='warm screening, inference, transfer, scoring and window-tail calculation included; model loading and database writes excluded',runs=rows))
