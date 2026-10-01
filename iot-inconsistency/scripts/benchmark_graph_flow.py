"""Exclusive-GPU runtime accounting separate from offline truth-scoring costs."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.flow_data import build_cases,graph_for,sha256
from iot_repair.flow_training import load_flow
from iot_repair.flow_inference import infer_case
from iot_repair.graph_flow_model import build_context
from iot_repair.flow_gaussian import load_ppca,infer_ppca
from iot_repair.flow_baselines import pca_model
from iot_repair.flow_ganf import load_ganf,infer_ganf
from iot_repair.experiment import json_save

@torch.no_grad()
def nll(models,values,graph,length):
    observed=torch.tensor(values,device='cuda');query=torch.nonzero(torch.isfinite(observed[:,-8:]).all(-1),as_tuple=True)[0]
    inputs=build_context(observed[None].expand(len(query),-1,-1),query,graph,length)
    logs=torch.stack([model.log_prob(observed[query,-8:],inputs) for model in models],1)
    return -(torch.logsumexp(logs.double(),1)-np.log(len(models))).cpu().numpy()


def main():
    torch.set_num_threads(4);directory=ROOT/'results/graph_flow_v1';lock=json.loads((directory/'protocol_lock.json').read_text());records={}
    for dataset,selection in lock['choices'].items():
        models=[load_flow(ROOT,r) for r in selection['members']['members']];graph=graph_for(ROOT,dataset)
        case=next(c for c in build_cases(ROOT,dataset,'test') if c['track']=='clean' and np.isfinite(c['values'][:,-8:]).all(-1).any())
        settings=selection['scoring'];length=selection['models']['selected']['specification']['context_length'];values=case['values']
        pca=pca_model(ROOT,dataset,selection['baselines']['pca']['name']);ppca=load_ppca(ROOT,selection['baselines']['ppca']);ganf=[load_ganf(ROOT,r) for r in selection['ganf']['members']]
        processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader'],text=True).strip().splitlines()
        if any(line.split(',')[0].strip()!=str(os.getpid()) for line in processes):raise RuntimeError('Another GPU job is active')
        methods={}
        actions=dict(flow_ratio_and_repair=lambda:infer_case(models,values,graph,length,settings['sample_count'],settings['scale'],seed=94000000,times=case['target_times']),
                     same_flow_nll=lambda:nll(models,values,graph,length),single_flow_nll=lambda:nll(models[:1],values,graph,length),
                     pca=lambda:pca.score(values[None]),ppca_ratio_and_repair=lambda:infer_ppca(ppca,values,graph,length,settings['scale'],seed=94000000,times=case['target_times']),
                     ganf=lambda:infer_ganf(ganf,values))
        for method,action in actions.items():
            action();measurements=[]
            for repeat in range(7):
                torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter();action();torch.cuda.synchronize()
                measurements.append(dict(seconds=time.perf_counter()-start,peak_gpu_bytes=torch.cuda.max_memory_allocated()))
            methods[method]=dict(repetitions=measurements,median_seconds=float(np.median([r['seconds'] for r in measurements])))
        records[dataset]=dict(case_id=case['id'],eligible_candidates=int(np.isfinite(values[:,-8:]).all(-1).sum()),draws=settings['sample_count'],ensemble_members=3,
           methods=methods,gpu_processes=processes,torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),
           cuda_matmul_tf32=torch.backends.cuda.matmul.allow_tf32,cudnn_tf32=torch.backends.cudnn.allow_tf32,
           scope='Seven warm batch-one-window wall times. Model loading and database excluded. Conditional repair summaries included, hidden-reference metrics excluded. Returned raw evidence transfer included. PPCA and PCA run on the CPU. Peak allocation includes resident models.')
        del models,ganf;torch.cuda.empty_cache()
    json_save(directory/'runtime.json',records)
if __name__=='__main__':main()
