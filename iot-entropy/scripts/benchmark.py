"""Synchronized model-only, complete detector and comparable-kernel timings."""
from pathlib import Path
import json
import platform
import time

import numpy as np
import torch

from iot_entropy.calibration import rank_pvalues
from iot_entropy.data import load_data
from iot_entropy.entropy import window_features
from iot_entropy.experiment import load_models
from iot_entropy.features import Scan,score_features
from iot_entropy.models import calendar
from iot_entropy.localization import merge_groups,participation
from iot_entropy.utils import Budget,recorded_runtime,synchronize,write_json

root=Path(__file__).resolve().parents[1]
config=json.loads((root/'configs/full.json').read_text())
directory=root/'experiments/full'
torch.set_num_threads(4)
started=time.monotonic();budget=Budget(config['gpu_hour_budget'],recorded_runtime(root))
results={'hardware':{'cpu':platform.processor(),'logical_cpus':__import__('os').cpu_count(),
                     'torch_threads':torch.get_num_threads(),'gpu':torch.cuda.get_device_name(0)},
         'software':{'torch':torch.__version__,'cuda':torch.version.cuda,'python':platform.python_version()},'detector':[]}
cpuinfo=Path('/proc/cpuinfo').read_text()
results['hardware']['cpu_model']=next(line.split(':',1)[1].strip() for line in cpuinfo.splitlines() if line.startswith('model name'))
for key in ['/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/memory.max']:
    if Path(key).exists():results['hardware'][key]=Path(key).read_text().strip()
def summarize(values):
    return {'p50_seconds':float(np.median(values)),'p95_seconds':float(np.quantile(values,.95)),
            'mean_seconds':float(np.mean(values)),'repetitions':len(values)}
for name in ['synthetic64','synthetic128','synthetic256','intel','pems']:
    budget.check();torch.cuda.reset_peak_memory_stats()
    data=load_data(root,name);model,_=load_models(data,config,17,directory,'cuda')
    scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cuda')
    start=int(data.issuance_indices(1,48,120,168)[0]);values=data.standardized
    floor=torch.as_tensor(np.load(directory/f'score-{name}-physical-17/development_parameters.npz')['floor'],device='cuda')
    calibration=np.load(directory/f'score-{name}-physical-17/calibration.npz')
    localization_budget=json.loads((directory/f'score-{name}-physical-17/development_selection.json').read_text())['localization_budget']
    column=calibration['methods'].tolist().index('diffusion/entropy');maxima=calibration['maxima'][:,column]
    context=torch.as_tensor(values[start-48:start],device='cuda')[None]
    dates=torch.as_tensor(calendar(data.timestamps[start:start+120]),device='cuda')[None]
    model.sample(context,dates,8,20,8);synchronize('cuda')
    model_times=[];pipeline_times=[]
    for _ in range(6):
        synchronize('cuda');begin=time.perf_counter()
        samples=model.sample(context,dates,64,20,16);synchronize('cuda');model_times.append(time.perf_counter()-begin)
        synchronize('cuda');begin=time.perf_counter()
        # Include host-to-device transfer, reference generation, feature extraction,
        # scores, host calibration and a real local JSON record write.
        observed=torch.as_tensor(values[start:start+120],device='cuda')
        ctx=torch.as_tensor(values[start-48:start],device='cuda')[None]
        date=torch.as_tensor(calendar(data.timestamps[start:start+120]),device='cuda')[None]
        samples=model.sample(ctx,date,64,20,16)
        predicted=scan.extract(samples.masked_fill(~torch.isfinite(observed)[None],float('nan')))
        scores,_=score_features(scan.extract(observed),predicted,floor)
        maximum=float(scores['entropy'].nan_to_num(nan=-float('inf')).max())
        p=float(rank_pvalues(maxima,maximum))
        vector=scores['entropy'].cpu().numpy()
        adjusted=rank_pvalues(maxima,np.where(np.isfinite(vector),vector,-np.inf))
        nodes=np.argsort(-participation(vector,scan.groups,len(data.node_ids)),kind='stable')[:localization_budget]
        alerts=np.where((adjusted<=.1)&np.isfinite(vector))[0].tolist()
        merged=merge_groups(alerts,scan.groups,.5)
        write_json(root/'.local/benchmark-record.json',{'score':maximum,'p':p,'ranked_nodes':nodes,'merged_alert_groups':merged})
        synchronize('cuda');pipeline_times.append(time.perf_counter()-begin)
    results['detector'].append({'dataset':name,'model_only':summarize(model_times),'complete_detector':summarize(pipeline_times),
                              'peak_gpu_bytes':torch.cuda.max_memory_allocated(),
                              'network_observations_per_second':120/np.mean(pipeline_times),
                              'scalar_measurements_per_second':120*len(data.node_ids)*len(data.channels)/np.mean(pipeline_times)})
torch.manual_seed(99)
reference=torch.randn(128,96,24,dtype=torch.float64)
kernels={}
for label,values in [('cpu_float32',reference.float()),('cpu_float64',reference),('gpu_float32',reference.cuda().float())]:
    window_features(values);synchronize(values.device);times=[]
    for _ in range(20):
        synchronize(values.device);start=time.perf_counter();features=window_features(values);synchronize(values.device);times.append(time.perf_counter()-start)
    kernels[label]=summarize(times)
kernels['float32_gpu_cpu_reference_max_abs_error']=float((window_features(reference).values-window_features(reference.cuda().float()).values.cpu().double()).abs().max())
results['kernels']=kernels
results['pipeline_stages']=['host-to-device context/target transfer','joint generation','feature/reference statistics','robust scores',
                            'calibration ranks','sensor participation and overlap merging','local alert-record serialization']
results['elapsed_seconds']=time.monotonic()-started
write_json(root/'experiments/benchmark.json',results)
