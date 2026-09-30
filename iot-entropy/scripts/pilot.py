"""Profile before selecting the full-run GPU-hour ceiling; uses development only."""
from pathlib import Path
import json
import platform
import time

import numpy as np
import torch

from iot_entropy.data import load_data
from iot_entropy.entropy import window_features
from iot_entropy.models import calendar
from iot_entropy.synthetic import prepare_synthetic
from iot_entropy.training import fit
from iot_entropy.utils import Budget, synchronize, write_json

root=Path(__file__).resolve().parents[1]
config=json.loads((root/'configs/full.json').read_text())
config.update(training_steps=100,validation_every=50,gdn_steps=50)
directory=root/'experiments/pilot'
directory.mkdir(parents=True,exist_ok=True)
torch.set_num_threads(4)
if not (root/'data/processed/synthetic64.npz').exists():
    prepare_synthetic(root,64,'cuda')
budget=Budget(.5)
results={'software':{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__},'profiles':[]}
for name in ['synthetic64','pems']:
    data=load_data(root,name)
    model,training=fit(data,config,17,directory,budget)
    start=data.issuance_indices(1,48,120,168)[0]
    context=torch.as_tensor(data.standardized[start-48:start],device='cuda')[None]
    dates=torch.as_tensor(calendar(data.timestamps[start:start+120]),device='cuda')[None]
    model.sample(context,dates,4,20,4);synchronize('cuda')
    durations={}
    for number in [32,64,128]:
        torch.cuda.reset_peak_memory_stats();started=time.monotonic()
        samples=model.sample(context,dates,number,20,16);synchronize('cuda')
        durations[str(number)]={'seconds':time.monotonic()-started,'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'finite':bool(torch.isfinite(samples).all())}
    results['profiles'].append({'dataset':name,'training':training,'sampling':durations})
    write_json(directory/'profile.json',results)
torch.manual_seed(991)
reference=torch.randn(128,96,24,dtype=torch.float64)
gpu=reference.cuda().float()
window_features(gpu);synchronize('cuda')
kernel={}
for label,x in [('cpu_float64',reference),('gpu_float32',gpu)]:
    timings=[]
    for _ in range(12):
        synchronize(x.device);start=time.perf_counter();output=window_features(x);synchronize(x.device);timings.append(time.perf_counter()-start)
    kernel[label]={'p50_seconds':float(np.median(timings)),'p95_seconds':float(np.quantile(timings,.95))}
cpu=window_features(reference).values
cuda=window_features(gpu).values.cpu().double()
kernel['maximum_absolute_error']=float((cpu-cuda).abs().max())
results['measurement_kernel']=kernel
results['total_seconds']=budget.elapsed
write_json(directory/'profile.json',results)
print(json.dumps(results,indent=2),flush=True)
