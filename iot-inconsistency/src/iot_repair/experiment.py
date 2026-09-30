"""Shared frozen case construction and common comparator evaluation."""
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from .faults import inject_observation,inject_association,content_hash
from .baselines import PCADetector,GDN,gdn_residual
from .diffusion import ConditionalDiffusion,ConditionalMean,conditional_sample
from .diffad import DiffAD,select_observations,sample as diffad_sample
from .associations import edge_residuals

SEEDS=[1101,2202,3303]

def json_save(path,data):
    def clean(value):
        if isinstance(value,np.ndarray):return clean(value.tolist())
        if isinstance(value,np.generic):return clean(value.item())
        if isinstance(value,float) and not np.isfinite(value):return None
        if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)):return [clean(v) for v in value]
        return value
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(clean(data),indent=2,allow_nan=False)+'\n');temporary.replace(path)


def build_cases(data,graph,split,config):
    indices=np.flatnonzero(data['reference'])
    count=min(len(indices),config['base_windows'][split])
    indices=indices[np.linspace(0,len(indices)-1,count,dtype=int)]
    blocks=sorted(set(str(data['block'][i]) for i in indices))
    null_blocks=set(blocks[:max(1,len(blocks)//2)])
    cases=[];offset={'development':300000,'calibration':500000,'test':700000}[split]
    for ordinal,index in enumerate(indices):
        base=data['x'][index];base_id=f'{split}_{index:04d}'
        common=dict(base_id=base_id,source_index=int(index),block=str(data['block'][index]),
            timestamp=int(data['timestamp'][index]),start=int(data['start'][index]),stop=int(data['stop'][index]),
            native_process_label=bool(data['process_label'][index]),split=split,
            calibration_fold='null' if str(data['block'][index]) in null_blocks else 'probability')
        families=config['observation_families_development']+(config['observation_families_heldout'] if split=='test' else [])
        family=families[ordinal%len(families)]
        x,obs,obs_meta=inject_observation(base,offset+index*101,family=family,
            strength=[.5,1.,2.,4.][(ordinal//len(families))%4],duration=[4,8,16][(ordinal//4)%3])
        edge_graph,edges,edge_meta=inject_association(graph,offset+index*101+3,
            family=config['association_families'][ordinal%len(config['association_families'])])
        specs=[('clean',base,graph,np.zeros(base.shape[0],bool),np.zeros(len(graph['edges']),bool),dict(family='unmodified',status='reference')),
               ('observation',x,graph,obs,np.zeros(len(graph['edges']),bool),obs_meta),
               ('association',base,edge_graph,np.zeros(base.shape[0],bool),edges,edge_meta)]
        for kind,values,g,obs_truth,edge_truth,metadata in specs:
            cases.append(dict(common,id=base_id+'_'+kind,track=kind,x=values,graph=g,
                observation_truth=obs_truth,association_truth=edge_truth,fault=metadata,
                data_sha256=hashlib.sha256(values.tobytes()).hexdigest()))
    return cases


def public_case(case):
    return {key:(value.tolist() if isinstance(value,np.ndarray) else value) for key,value in case.items() if key not in ('x','graph')}


def load_models(root,dataset,kinds=('diffusion','mean','gdn','diffad','no_graph'),device='cuda'):
    directory=Path(root)/'results/models'/dataset;result={}
    graph=json.loads((directory/'graph.json').read_text())
    channels=len(graph['groups'])
    for kind in kinds:
        result[kind]=[]
        for seed in SEEDS:
            saved=torch.load(directory/f'{kind}_{seed}.pt',map_location=device,weights_only=False)
            cls={'diffusion':ConditionalDiffusion,'no_graph':ConditionalDiffusion,'mean':ConditionalMean,'gdn':GDN,'diffad':DiffAD}[kind]
            model=cls(channels,width=saved['config']['width']) if kind in ('diffusion','no_graph','mean') else cls(channels)
            model.load_state_dict(saved['model']);model.to(device).eval();model.inference_autocast=True
            result[kind].append(model)
    return result,graph


@torch.no_grad()
def neural_residuals(models,values,graph,device='cuda',batch=16,seed=80926):
    outputs={};timings={}
    for kind in ('gdn','backbone','diffad'):
        if ('diffusion' if kind=='backbone' else kind) not in models:continue
        members=[];start=time.perf_counter()
        for member,model in enumerate(models['diffusion' if kind=='backbone' else kind]):
            chunks=[]
            for first in range(0,len(values),batch):
                raw=values[first:first+batch];x=torch.as_tensor(raw,device=device);observed=torch.isfinite(x);x=torch.nan_to_num(x)
                if kind=='gdn':scores=gdn_residual(model,torch.as_tensor(raw,device=device))
                elif kind=='backbone':
                    visible=observed.clone();visible[...,-8:]=False
                    predictions=conditional_sample(model,torch.where(visible,x,torch.zeros_like(x)),visible,graph,
                        samples=8,seed=seed+member*100003+first,sampling_steps=12).mean(1)
                    squared=(predictions[...,-8:]-x[...,-8:]).square()
                    mask=observed[...,-8:];scores=torch.where(mask,squared,torch.zeros_like(squared)).sum(-1)/mask.sum(-1).clamp_min(1)
                    scores=scores.masked_fill(mask.sum(-1)==0,float('nan'))
                else:
                    selected=torch.as_tensor(select_observations(raw),device=device)
                    predictions=diffad_sample(model,x,observed,selected,samples=8,seed=seed+member*100003+first).mean(1)
                    squared=(predictions[...,-8:]-x[...,-8:]).square();mask=observed[...,-8:]
                    scores=torch.where(mask,squared,torch.zeros_like(squared)).sum(-1)/mask.sum(-1).clamp_min(1)
                    scores=scores.masked_fill(mask.sum(-1)==0,float('nan'))
                chunks.append(scores.cpu().numpy())
            members.append(np.concatenate(chunks))
        if device.startswith('cuda'):torch.cuda.synchronize()
        outputs[kind]=np.stack(members);timings[kind]=(time.perf_counter()-start)/len(values)
    return outputs,timings


def reference_scale(values):
    median=np.nanmedian(values,axis=0);iqr=np.nanpercentile(values,75,axis=0)-np.nanpercentile(values,25,axis=0)
    # Floor follows reference error scale and never sees a test observation.
    floor=np.maximum(np.abs(median)*1e-3,1e-6)
    return dict(median=np.nan_to_num(median).tolist(),scale=np.where(np.isfinite(iqr),np.maximum(iqr,floor),1.).tolist())


def scaled(values,parameters):
    return (values-np.array(parameters['median']))/np.array(parameters['scale'])
