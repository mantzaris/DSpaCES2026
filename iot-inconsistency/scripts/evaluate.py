"""Resumable shared experiments. Final test requires development freeze and calibration."""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import *
from iot_repair.pipeline import screen_candidates,score_candidates
from iot_repair.faults import content_hash

p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--split',choices=['development','calibration','test'],required=True)
p.add_argument('--device',default='cuda');p.add_argument('--skip-diffad',action='store_true');args=p.parse_args()
torch.set_num_threads(4)
config=json.loads((ROOT/'configs/study.json').read_text());dataset=args.dataset;split=args.split
out=ROOT/'results/study'/dataset;out.mkdir(parents=True,exist_ok=True)
if split!='development' and not (out/'frozen.json').exists():raise RuntimeError('Freeze development selection first')
if split=='test' and not (out/'calibration_complete.json').exists():raise RuntimeError('Calibrate the frozen pipeline before opening test data')
kinds=['diffusion','mean','gdn','no_graph']+([] if args.skip_diffad else ['diffad'])
models,graph=load_models(ROOT,dataset,kinds,args.device)
data=np.load(ROOT/'data/processed'/dataset/(split+'.npz'))
cases=build_cases(data,graph,split,config);splitout=out/split;splitout.mkdir(exist_ok=True)
json_save(splitout/'case_manifest.json',dict(protocol=content_hash(config),cases=[public_case(case) for case in cases]))
values=np.stack([case['x'] for case in cases]);cache=splitout/'baselines_raw.npz'
if cache.exists():
    raw=dict(np.load(cache));timings=json.loads((splitout/'baseline_timing.json').read_text())
else:
    raw,timings=neural_residuals(models,values,graph,args.device,seed={'development':81001,'calibration':82001,'test':83001}[split])
    train=np.load(ROOT/'data/processed'/dataset/'train.npz')['x']
    for lag in config['pca_lags']:
      for rank in config['pca_rank_grid']:
        name=f'pca_lag{lag}_rank{rank}';start=time.perf_counter();model=PCADetector(rank,lag).fit(train)
        fit_elapsed=time.perf_counter()-start;start=time.perf_counter();raw[name]=model.score(values)
        timings[name]=dict(fit_seconds=fit_elapsed,inference_seconds_per_window=(time.perf_counter()-start)/len(values),rank=model.pca.n_components_)
        target=ROOT/'results/models'/dataset/(name+'.npz')
        if not target.exists():np.savez_compressed(target,mean=model.pca.mean_,components=model.pca.components_,fill=model.fill)
    np.savez_compressed(cache,**raw);json_save(splitout/'baseline_timing.json',timings)
# Development reference errors define common per-channel scales for every comparator.
if split=='development':
    scales={name:reference_scale((scores.mean(0) if scores.ndim==3 else scores)[::3]) for name,scores in raw.items()}
    json_save(out/'residual_scales.json',scales)
else:scales=json.loads((out/'residual_scales.json').read_text())
normalized={name:scaled(scores.mean(0) if scores.ndim==3 else scores,scales[name]) for name,scores in raw.items()}
for ordinal,case in enumerate(cases):
    path=splitout/(case['id']+'.json')
    if path.exists():continue
    edge_scores=edge_residuals(case['x'][None],case['graph'])[0]
    candidates=screen_candidates(normalized['gdn'][ordinal],edge_scores,case['graph'],config['candidate_cap_per_type'])
    torch.cuda.reset_peak_memory_stats() if args.device.startswith('cuda') else None
    records,terms,abstentions=score_candidates(models['diffusion'],case['x'],case['graph'],candidates,
        replicates=config['replicates'],predictive_samples=config['predictive_samples'],seed=910000+ordinal*1009+{'development':0,'calibration':2000000,'test':4000000}[split])
    for record in records:
        record['truth']=bool(case[record['kind']+'_truth'][record['index']])
    artifact=case['id']+'.npz';np.savez_compressed(splitout/artifact,input=case['x'],
        observation_truth=case['observation_truth'],association_truth=case['association_truth'],**terms)
    result=dict(public_case(case),graph=case['graph'],records=records,abstentions=abstentions,candidates=candidates,
        edge_residuals=edge_scores.tolist(),baseline_sensor_scores={name:scores[ordinal].tolist() for name,scores in normalized.items()},
        raw_artifact=artifact,raw_sha256=hashlib.sha256((splitout/artifact).read_bytes()).hexdigest(),
        gpu_peak_bytes=torch.cuda.max_memory_allocated() if args.device.startswith('cuda') else 0)
    json_save(path,result)
    if ordinal%25==0:print(dataset,split,ordinal,'/',len(cases),flush=True)
json_save(splitout/'complete.json',dict(cases=len(cases),protocol=content_hash(config),split=split,dataset=dataset))
print(dataset,split,'complete',len(cases),flush=True)
