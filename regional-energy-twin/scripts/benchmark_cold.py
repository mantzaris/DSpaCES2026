"""Complete cold model-state latency, including canonical IDs and projection RNG.

Complements the original warm replay without replacing its measurements.
Provider fitting and archive preparation are separate study-level costs.
"""
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
import yaml
from threadpoolctl import threadpool_limits
from evidence_fusion.provenance_sketches import gaussian_columns
from evidence_fusion.record_identity import record_id
from evidence_fusion.replay_benchmarks import codec
from evidence_fusion.conservative_fusion import solve_simplex, solve_simplex_torch
from evidence_fusion.resource_ledger import Budget,set_gpu_limit

cfg=yaml.safe_load(Path('configs/pilot.yaml').read_text())
budget=Budget('results/resource_ledger.json',cfg['allocation_start_utc'],cfg['gpu_allocation_cap_seconds'],cache='data')
budget.record('cold_percentile_completion_start',reason='Complete required cold p50/p95 and include canonical-ID construction and Gaussian generation')
threadpool_limits(limits=4);torch.set_num_threads(4);set_gpu_limit(24)
init=time.perf_counter();torch.cuda.init();torch.cuda.synchronize();initialization=time.perf_counter()-init
building=json.loads(Path('manifests/data_audit.json').read_text())['selected_buildings'][0]
records=[];references={};max_difference=0.;device_seconds=0.
for backend in ('cpu','gpu'):
    for batch in (1,256):
        for repeat in range(5):
            budget.check();begin=time.perf_counter();stages={}
            stage=time.perf_counter()
            with np.load('data/benchmark_input.npz') as arrays:
                phi=arrays['features'][:batch];means=arrays['means'][:batch]
                s=arrays['norms'][:batch];r=arrays['residual'][:batch]
                local=arrays['local_operators'];supports=arrays['supports']
                v=float(arrays['future']);epsilon=float(arrays['epsilon'])
            stages['model_cache_read_seconds']=time.perf_counter()-stage
            stage=time.perf_counter()
            times=pd.date_range('2016-01-01',periods=6576,freq='h')
            ids=[record_id(building,str(t),i) for i,t in enumerate(times)]
            stages['canonical_ids_seconds']=time.perf_counter()-stage
            stage=time.perf_counter();g=gaussian_columns(ids,2048,312048)
            stages['gaussian_columns_seconds']=time.perf_counter()-stage
            event1=torch.cuda.Event(enable_timing=True);event2=torch.cuda.Event(enable_timing=True)
            stage=time.perf_counter()
            if backend=='gpu':
                event1.record()
                gd=torch.as_tensor(g,device='cuda');bd=torch.as_tensor(local,device='cuda');ix=torch.as_tensor(supports,device='cuda')
                op=bd@gd[ix];z=torch.einsum('td,pdk->tpk',torch.as_tensor(phi,device='cuda'),op).cpu().numpy()
                event2.record();torch.cuda.synchronize();device_seconds+=event1.elapsed_time(event2)/1000
            else:
                op=local@g[supports];z=np.einsum('td,pdk->tpk',phi,op,optimize=True)
            stages['operator_transfer_and_provider_seconds']=time.perf_counter()-stage
            stage=time.perf_counter();parsed,nbytes=codec(means,z,s,r,v)
            stages['serialize_parse_validate_seconds']=time.perf_counter()-stage
            stage=time.perf_counter()
            if backend=='gpu':
                event1.record()
                zd=torch.as_tensor(parsed,device='cuda');sd=torch.as_tensor(s,device='cuda');rd=torch.as_tensor(r,device='cuda')
                h=zd@zd.transpose(-1,-2)+epsilon*sd[:,:,None]*sd[:,None,:]+rd[:,:,None]*rd[:,None,:]
                w,var,gap=solve_simplex_torch(h)
                w=w.cpu().numpy();var=var.cpu().numpy()+v
                event2.record();torch.cuda.synchronize();device_seconds+=event1.elapsed_time(event2)/1000
            else:
                h=parsed@parsed.transpose(0,2,1)+epsilon*s[:,:,None]*s[:,None,:]+r[:,:,None]*r[:,None,:]
                solution=solve_simplex(h);w=solution.weights;var=solution.value+v
            individual=s*s+r*r+v;minimum=individual.min(axis=1)
            w=np.where((minimum<var)[:,None],np.eye(4)[individual.argmin(axis=1)],w)
            var=np.minimum(var,minimum);mean=np.sum(means*w,axis=1)
            output=json.dumps(dict(mean=mean.tolist(),variance=var.tolist(),weights=w.tolist())).encode()
            stages['consumer_transfer_gram_solve_output_seconds']=time.perf_counter()-stage
            elapsed=time.perf_counter()-begin
            if backend=='cpu':references[batch]=(mean,var)
            else:
                difference=max(float(np.max(np.abs(mean-references[batch][0]))),float(np.max(np.abs(var-references[batch][1]))))
                max_difference=max(max_difference,difference)
                if difference>1e-9:raise AssertionError('Cold CPU/GPU numerical mismatch')
            records.append(dict(backend=backend,batch=batch,repeat=repeat,complete_seconds=elapsed,
                wire_bytes=nbytes,output_bytes=len(output),**stages))
            if backend=='gpu':
                del gd,bd,ix,op,zd,sd,rd,h
                torch.cuda.empty_cache()
            del g,z,parsed
summary=[]
for backend in ('cpu','gpu'):
    for batch in (1,256):
        values=[r['complete_seconds'] for r in records if r['backend']==backend and r['batch']==batch]
        summary.append(dict(backend=backend,batch=batch,replicates=len(values),
            p50_seconds=float(np.median(values)),p95_seconds=float(np.quantile(values,.95))))
result=dict(summary=summary,records=records,explicit_cuda_init_after_device_inspection_seconds=initialization,
    max_cpu_gpu_absolute_difference=max_difference,device_event_seconds=device_seconds,
    scope='Cold model-state: cache read, canonical IDs, fresh Gaussian columns, projection operators, wire protocol, transfers, solver and output. Model fitting and archive preparation are separately measured study setup; OS disk cache not evicted.')
Path('results/cold_benchmarks.json').write_text(json.dumps(result,indent=2)+'\n')
budget.record('cold_percentiles_complete',device_seconds=device_seconds)
print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
