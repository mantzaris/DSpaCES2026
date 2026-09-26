"""Matched FP64 CPU/GPU pipeline with serialization and transfers included."""
import hashlib
import json
import platform
import resource
import subprocess
import time
from pathlib import Path
import numpy as np
from .conservative_fusion import solve_simplex, solve_simplex_torch
from .message_contracts import Message, ActiveMessages
from .provenance_sketches import Epoch


def codec(means, z, s, residual, future):
    """Real immutable binary messages; benchmark envelopes, fixed numerical inputs."""
    epoch=Epoch('benchmark',312048,z.shape[-1],4096,4,.005)
    received=[];bytes_total=0
    for i in range(len(z)):
        state=ActiveMessages(epoch)
        for p in range(4):
            m=Message('weighted-provenance/1',f'p{p}','benchmark-Bear',
                '2016-10-22T01:00:00','2016-10-22T02:00:00','kWh','2016-09-30T23:00:00',
                '2016-10-22T00:59:00','2016-10-22T01:00:00','replay-v1',f'fit{p}',f'evidence{p}',
                0,'','oof-v1',float(future),'benchmark',312048,z.shape[-1],
                float(means[i,p]),float(s[i,p]),float(residual[i,p]),tuple(map(float,z[i,p]))).signed()
            wire=m.to_wire();bytes_total+=len(wire)
            state.accept(Message.from_wire(wire))
        received.append([m.sketch for m in state.finalize()])
    return np.asarray(received),bytes_total


def benchmark(path, budget, repeats=5):
    import torch
    from .resource_ledger import set_gpu_limit
    init=time.perf_counter();props=set_gpu_limit(24)
    torch.set_num_threads(4)
    torch.cuda.init();torch.cuda.synchronize()
    init_seconds=time.perf_counter()-init
    arrays=np.load(path)
    phi=arrays['features'];means=arrays['means'];s=arrays['norms'];r=arrays['residual']
    v=float(arrays['future']);eps=float(arrays['epsilon'])
    local=arrays['local_operators'];supports=arrays['supports'];projection=arrays['projection']
    records=[];reference={};max_mean_error=0.;max_variance_error=0.
    for backend in ('cpu','gpu'):
        budget.check()
        start=time.perf_counter()
        if backend=='gpu':
            begin_event=torch.cuda.Event(enable_timing=True);end_event=torch.cuda.Event(enable_timing=True)
            begin_event.record()
            op=torch.as_tensor(local,device='cuda')
            g=torch.as_tensor(projection,device='cuda')
            ix=torch.as_tensor(supports,device='cuda')
            cached=op@g[ix]
            end_event.record();torch.cuda.synchronize()
            setup_device_ms=begin_event.elapsed_time(end_event)
        else:
            cached=local@projection[supports]
            setup_device_ms=0.
        setup_seconds=time.perf_counter()-start
        for batch in (1, min(256,len(phi))):
            for repeat in range(repeats+1):
                budget.check();timings={};device_ms=0.;begin=time.perf_counter()
                stage=time.perf_counter()
                if backend=='gpu':
                    begin_event.record()
                    features=torch.as_tensor(phi[:batch],device='cuda')
                    zz=torch.einsum('td,pdk->tpk',features,cached)
                    z=zz.cpu().numpy()
                    end_event.record();torch.cuda.synchronize()
                    device_ms+=begin_event.elapsed_time(end_event)
                else:
                    z=np.einsum('td,pdk->tpk',phi[:batch],cached,optimize=True)
                timings['provider_query_seconds']=time.perf_counter()-stage
                stage=time.perf_counter();parsed,nbytes=codec(means[:batch],z,s[:batch],r[:batch],v)
                timings['serialize_parse_validate_seconds']=time.perf_counter()-stage
                stage=time.perf_counter()
                if backend=='gpu':
                    begin_event.record()
                    zdevice=torch.as_tensor(parsed,device='cuda');ss=torch.as_tensor(s[:batch],device='cuda');rr=torch.as_tensor(r[:batch],device='cuda')
                    end_event.record();torch.cuda.synchronize();device_ms+=begin_event.elapsed_time(end_event)
                timings['host_to_device_seconds']=time.perf_counter()-stage
                stage=time.perf_counter()
                if backend=='gpu':
                    begin_event.record()
                    h=zdevice@zdevice.transpose(-1,-2)+eps*ss[:,:,None]*ss[:,None,:]+rr[:,:,None]*rr[:,None,:]
                    end_event.record();torch.cuda.synchronize();device_ms+=begin_event.elapsed_time(end_event)
                else:
                    h=parsed@parsed.transpose(0,2,1)+eps*s[:batch,:,None]*s[:batch,None,:]+r[:batch,:,None]*r[:batch,None,:]
                timings['gram_seconds']=time.perf_counter()-stage
                stage=time.perf_counter()
                if backend=='gpu':
                    begin_event.record();ww,vv,gg=solve_simplex_torch(h)
                    end_event.record();torch.cuda.synchronize();device_ms+=begin_event.elapsed_time(end_event)
                else:
                    solution=solve_simplex(h);ww,vv,gg=solution.weights,solution.value,solution.gap
                timings['solver_seconds']=time.perf_counter()-stage
                stage=time.perf_counter()
                if backend=='gpu':
                    weights=ww.cpu().numpy();variance=vv.cpu().numpy()+v;gap=gg.cpu().numpy()
                    torch.cuda.synchronize()
                else:weights=ww;variance=vv+v;gap=gg
                timings['device_to_host_seconds']=time.perf_counter()-stage
                stage=time.perf_counter()
                individual=s[:batch]**2+r[:batch]**2+v
                index=individual.argmin(axis=1);best=individual.min(axis=1)
                choose=best<variance
                weights=np.where(choose[:,None],np.eye(4)[index],weights);variance=np.minimum(variance,best)
                output_mean=np.sum(means[:batch]*weights,axis=1)
                output=json.dumps(dict(mean=output_mean.tolist(),variance=variance.tolist(),weights=weights.tolist())).encode()
                timings['output_seconds']=time.perf_counter()-stage
                elapsed=time.perf_counter()-begin
                if backend=='cpu':reference[batch]=(output_mean,variance)
                else:
                    max_mean_error=max(max_mean_error,float(np.max(np.abs(output_mean-reference[batch][0]))))
                    max_variance_error=max(max_variance_error,float(np.max(np.abs(variance-reference[batch][1]))))
                records.append(dict(backend=backend,batch=batch,repeat=repeat,cold=repeat==0,
                    complete_seconds=elapsed,complete_with_operator_setup_seconds=elapsed+(setup_seconds if repeat==0 else 0),
                    device_event_ms=device_ms,setup_seconds=setup_seconds,setup_device_ms=setup_device_ms,
                    cuda_initialization_seconds=init_seconds if backend=='gpu' else 0.,wire_bytes=nbytes,
                    output_bytes=len(output),max_relative_solver_gap=float(np.max(gap/np.maximum(variance,1e-300))),**timings))
        if backend=='gpu':
            del op,g,ix,cached
            torch.cuda.empty_cache()
    summary=[]
    for backend in ('cpu','gpu'):
        for batch in (1,min(256,len(phi))):
            warm=[r['complete_seconds'] for r in records if r['backend']==backend and r['batch']==batch and not r['cold']]
            summary.append(dict(backend=backend,batch=batch,warm_replicates=len(warm),
                p50_seconds=float(np.median(warm)),p95_seconds=float(np.quantile(warm,.95)),
                queries_per_second=float(batch/np.median(warm)),messages_per_second=float(4*batch/np.median(warm))))
    result=dict(hardware=dict(gpu=props.name,gpu_total_bytes=props.total_memory,
        gpu_limit_gib=24,torch=torch.__version__,cuda=torch.version.cuda,python=platform.python_version(),
        cpu=subprocess.check_output(['lscpu'],text=True),
        gpu_driver=subprocess.check_output(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True).strip(),
        cpu_quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else 'unavailable',
        memory_quota=Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else 'unavailable',
        torch_threads=torch.get_num_threads(),blas_threads=4),
        precision='FP64 throughout; TF32 disabled; no compilation',records=records,summary=summary,
        cuda_initialization_seconds=init_seconds,max_cpu_gpu_mean_absolute_difference=max_mean_error,
        max_cpu_gpu_variance_absolute_difference=max_variance_error,
        peak_vram_allocated_bytes=torch.cuda.max_memory_allocated(),peak_vram_reserved_bytes=torch.cuda.max_memory_reserved(),
        peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        total_device_event_seconds=sum(r['device_event_ms'] for r in records)/1000+setup_device_ms/1000,
        limitations='Single host replay, no network latency; cold means uncached operators, OS cache not evicted. Source parsing, canonical IDs and projection generation measured separately in pilot/data audit; add once for full cold study cost.')
    Path('results/benchmarks.json').write_text(json.dumps(result,indent=2)+'\n')
    budget.record('benchmarks_complete',device_seconds=result['total_device_event_seconds'],
                  peak_vram=result['peak_vram_allocated_bytes'])
    return result
