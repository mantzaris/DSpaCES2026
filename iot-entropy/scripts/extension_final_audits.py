"""Paired reference fidelity, missingness support, and isolated GPU timings.

No training, threshold selection or architecture search. Every stage is
budgeted and saved; synthetic backgrounds are retained for CPU reproduction.
"""
import json
import time
from pathlib import Path

import numpy as np
import torch

from iot_entropy.extension_data import extension_data
from iot_entropy.extension import fidelity
from iot_entropy.extension_scoring import extract, summaries, score
from iot_entropy.features import Scan, prediction_fidelity
from iot_entropy.reference import BlockBootstrap, issue_reference
from iot_entropy.experiment import load_models
from iot_entropy.temporal import trajectory, window, coarse_grain
from iot_entropy.entropy import window_features
from iot_entropy.utils import Budget, synchronize, write_json, digest
from iot_entropy.extension_budget import components, authorized_hours

root=Path(__file__).resolve().parents[1]
namespace=root/'experiments/extension-v2'
out=root/'results/extension-v2';out.mkdir(parents=True,exist_ok=True)
config=json.loads((root/'configs/full.json').read_text());config.update(json.loads((root/'configs/extension-v2.json').read_text()))
ceiling=authorized_hours(root)
prior=sum(components(root).values())
budget=Budget(ceiling,prior)
attempt=namespace/f'audit-attempt-{len(list(namespace.glob("audit-attempt-*.json")))}.json'
torch.set_num_threads(4);started=time.monotonic();fid=[];missing=[];bench=[];lineage=[]
try:
 with torch.no_grad():
  for name in config['datasets']:
    budget.check()
    directory=namespace/f'{name}-17'
    selected=json.loads((directory/'configuration.json').read_text())
    data,bases,manifest=extension_data(root,name,selected,'cuda')
    values=data.standardized
    if name.startswith('synthetic'):
        path=namespace/'cache'/f'{name}-backgrounds.npz'
        np.savez_compressed(path,extension_values=data.values[data.bounds[1]:],
            extension_timestamps=data.timestamps[data.bounds[1]:],bounds=data.bounds,episode_bounds=data.episode_bounds)
        bootstrap=BlockBootstrap(data,48,120,'cuda')
        start=int(data.issuance_indices(2,48,120,168)[0]);draw_seed=700000+17*100000+start
        samples=issue_reference(None,data,values,start,120,selected,'cuda','bootstrap',bootstrap,draw_seed)
        saved=np.load(namespace/'cache'/f'{name}-17'/f'{start}-bootstrap.npy')
        np.testing.assert_array_equal(samples.cpu().numpy(),saved)
        lineage.append({'dataset':name,'sha256':digest(path),'path':str(path.relative_to(root)),
                        'bootstrap_byte_agreement':True,'device':'CUDA generation; retained arrays permit CPU analysis'})
        del bootstrap
    scan=Scan(data.adjacency,data.coordinates,data.channels,selected,'cuda')
    params=np.load(directory/'development-parameters.npz')
    floors={'spatial':torch.tensor(params['spatial'],device='cuda'),
            'temporal':{w:torch.tensor(params[f'temporal_{w}'],device='cuda') for w in selected['windows']}}
    # Two base blocks and two decision times, fixed without selecting outcomes.
    for bi,(base_start,_) in enumerate(bases[:2]):
      for end in [167,263]:
        budget.check();start=base_start+end-119
        raw=torch.tensor(values[start:start+120],device='cuda');actual=extract(raw,scan,selected)
        samples={ref:torch.tensor(np.load(namespace/'cache'/f'{name}-17'/f'{start}-{ref}.npy'),device='cuda')
                 .masked_fill(~torch.isfinite(raw)[None],float('nan')) for ref in ['bootstrap','diffusion']}
        generated={ref:extract(x,scan,selected) for ref,x in samples.items()}
        summaries_by={ref:summaries(x,floors,selected) for ref,x in generated.items()}
        raw_common=torch.isfinite(raw)
        for x in samples.values():raw_common &= torch.isfinite(x).all(0)
        spatial_common=torch.isfinite(actual['spatial'].values[0,:,0])
        for ref in samples:
            count=torch.isfinite(generated[ref]['spatial'].values[...,0]).sum(0)
            spatial_common &= count>=52
        for ref,x in samples.items():
            row={'dataset':name,'seed':17,'base':bi,'decision':end,'reference':ref,
                 'spatial_common_groups':int(spatial_common.sum()),'raw_common_dimensions':int(raw_common.sum()),
                 **prediction_fidelity(raw.masked_fill(~raw_common,float('nan')),x)}
            s=summaries_by[ref]['spatial'];h=actual['spatial'].values[0,:,0]
            row['spatial_entropy_coverage90']=float(((h>=s.low[:,0])&(h<=s.high[:,0]))[spatial_common].float().mean())
            row['spatial_entropy_width90']=float((s.high[:,0]-s.low[:,0])[spatial_common].mean())
            R_errors=[];cov_errors=[]
            for family,obs,gen in zip(scan.families,actual['spatial'].raw,generated[ref]['spatial'].raw):
                a=window_features(obs,scan.shrinkage);b=window_features(gen,scan.shrinkage)
                count=obs.shape[1];mask=spatial_common[family.offset:family.offset+count]
                R_errors.append((a.correlation[0]-torch.nanmean(b.correlation,dim=0))[mask].square().flatten())
                ac=a.correlation[0]*a.variance[0].sqrt()[...,None]*a.variance[0].sqrt()[...,None,:]
                bc=b.correlation*b.variance.sqrt()[...,None]*b.variance.sqrt()[...,None,:]
                cov_errors.append((ac-torch.nanmean(bc,dim=0))[mask].square().flatten())
            row['correlation_rmse']=float(torch.nanmean(torch.cat(R_errors)).sqrt())
            row['covariance_rmse_training_units']=float(torch.nanmean(torch.cat(cov_errors)).sqrt())
            for w in selected['windows']:
                for fi,label in [(0,'permutation'),(1,'sample'),(2,'acf1')]:
                    obs=actual['temporal'][w]['u'][0,...,fi,0]
                    common=torch.isfinite(obs)
                    for reference in samples:common &= summaries_by[reference]['temporal'][w]['enough'][...,fi,0]
                    s=summaries_by[ref]['temporal'][w]
                    lo,hi=s['low'][...,fi,0],s['high'][...,fi,0]
                    row[f'{label}_{w}_support']=int(common.sum())
                    row[f'{label}_{w}_coverage90']=float(((obs>=lo)&(obs<=hi))[common].float().mean())
                    row[f'{label}_{w}_width90']=float((hi-lo)[common].mean())
                    row[f'{label}_{w}_mae']=float((obs-s['center'][...,fi,0]).abs()[common].mean())
                obs=actual['temporal'][w]['current']['patterns'][0]
                common=torch.isfinite(actual['temporal'][w]['current']['values'][0,...,0])
                for reference in samples:common &= summaries_by[reference]['temporal'][w]['enough'][...,0,0]
                g=generated[ref]['temporal'][w]['current']
                patterns=torch.nanmean(g['patterns'].masked_fill(~torch.isfinite(g['values'][...,0,None]),float('nan')),dim=0)
                row[f'ordinal_tv_{w}']=float((.5*(obs-patterns).abs().sum(-1))[common].mean())
            fid.append(row)
        del samples,generated,summaries_by
    # Development support diagnostic; additional missingness is independent of values.
    starts=data.issuance_indices(1,48,120,168)[:4]
    for j,start in enumerate(starts):
      budget.check();raw=torch.tensor(values[start:start+120],device='cuda')
      generator=np.random.default_rng(81200+j)
      uniforms=torch.tensor(generator.uniform(size=raw.shape),device='cuda')
      for rate in [0,.1,.25,.5]:
        masked=raw.masked_fill(uniforms<rate,float('nan'))
        spatial=scan.extract(masked)
        for w in [48,96]:
            measured=trajectory(masked,w,selected)
            row={'dataset':name,'unit':j,'extra_missing_rate':rate,'window':w,
                'spatial_available':float(spatial.eligible[0,torch.tensor([r['window']==w for r in scan.records],device='cuda')].float().mean()),
                'permutation_available':float(torch.isfinite(measured['u'][...,0,:]).all(-1).float().mean()),
                'sample_available':float(torch.isfinite(measured['u'][...,1,:]).all(-1).float().mean()),
                'conventional_available':float(torch.isfinite(measured['u'][...,2:,:]).all(-1).float().mean()),
                'pe_templates':float(measured['current']['pe_templates'].float().mean()),
                'sample_B':float(measured['current']['B'].float().mean()),
                'role':'development-only support diagnostic; no calibrated detection claim'}
            missing.append(row)
    if name in ['synthetic64','intel','pems']:
        budget.check()
        model,unused=load_models(data,selected,17,root/'experiments/full','cuda');del unused
        bootstrap=BlockBootstrap(data,48,120,'cuda');start=int(starts[0])
        raw=torch.tensor(values[start:start+120],device='cuda')
        observed=extract(raw,scan,selected)
        for ref in ['bootstrap','diffusion']:
            # Complete isolated single-episode pipeline, repeated after warmup.
            measurements=[]
            for repeat in range(4):
                budget.check();torch.cuda.reset_peak_memory_stats();synchronize('cuda');t=time.perf_counter()
                samples=issue_reference(model,data,values,start,120,selected,'cuda',ref,bootstrap,82900+repeat)
                synchronize('cuda');generation=time.perf_counter()-t;t=time.perf_counter()
                samples=samples.masked_fill(~torch.isfinite(raw)[None],float('nan'))
                actual=extract(raw,scan,selected);g=extract(samples,scan,selected);s=summaries(g,floors,selected)
                z=score(actual,g,s,scan,floors,selected,selected['top_fraction'])
                from iot_entropy.extension_scoring import summarize_scores
                summarize_scores(z,scan,len(data.node_ids))
                synchronize('cuda');measurement=time.perf_counter()-t
                if repeat:measurements.append((generation,measurement,torch.cuda.max_memory_allocated()))
            bench.append({'dataset':name,'reference':ref,'pipeline_generation_seconds':float(np.median([x[0] for x in measurements])),
                'pipeline_measure_score_seconds':float(np.median([x[1] for x in measurements])),
                'pipeline_total_seconds':float(np.median([x[0]+x[1] for x in measurements])),
                'peak_gpu_bytes':max(x[2] for x in measurements),'warmup_repetitions':1,'timed_repetitions':3,
                'timing_scope':'isolated single observed episode; both windows, all feature families; includes masks/extraction/scoring/localization; excludes model/data loading'})
        # Statistical kernel comparison: identical arrays, B=16, W=96, transfer excluded.
        # Exact binary grid keeps threshold comparisons away from .1/.2/.3
        # rounding boundaries while evaluating identical CPU/GPU input values.
        x=torch.tensor(np.round(np.random.default_rng(8152).normal(size=(16,120,len(data.node_ids),len(data.channels)))*.2*128)/128,dtype=torch.float64)
        cpu=trajectory(x,96,selected)['u'];gpu=trajectory(x.float().cuda(),96,selected)['u'].cpu().double()
        assert torch.allclose(cpu,gpu,atol=3e-5,rtol=2e-4,equal_nan=True)
        times={}
        for label,block in [('cpu_float64',x),('gpu_float32',x.float().cuda())]:
            trajectory(block,96,selected);synchronize(block.device);durations=[]
            for _ in range(3):
                budget.check();synchronize(block.device);t=time.perf_counter();trajectory(block,96,selected);synchronize(block.device)
                durations.append(time.perf_counter()-t)
            times[label]=float(np.median(durations))
        bench.append({'dataset':name,'kernel':'all temporal features plus endpoints','B':16,'window':96,**times,
            'maximum_absolute_error':float(torch.nan_to_num(cpu-gpu).abs().max()),
            'speedup_scope':'statistical kernel only; not an end-to-end pipeline speedup'})
        del model,bootstrap
    write_json(out/'paired-reference-fidelity.json',fid);write_json(out/'missingness-development.json',missing)
    write_json(out/'isolated-benchmark.json',bench);write_json(namespace/'synthetic-backgrounds.json',lineage)
    print(json.dumps({'completed_audit':name,'cumulative_seconds':budget.elapsed}),flush=True)
finally:
    write_json(attempt,{'elapsed_seconds':time.monotonic()-started,'cumulative_seconds':budget.elapsed,'limit_seconds':ceiling*3600})
