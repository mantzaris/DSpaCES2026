"""Bounded, hash-addressed normal-reference training on the authorized GPU."""
import copy
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from .graph_flow_model import GraphFlow, GraphInputs, build_context
from .flow_data import configuration, load_data, graph_for, sha256
from .experiment import json_save


def candidate_training_data(root,dataset,split,context_length,mode='graph',fraction=1.,device='cuda'):
    data=load_data(root,dataset,split);windows=np.flatnonzero(data['reference'])
    blocks=sorted(set(data['block'][windows].tolist()))
    retained=blocks[:max(1,int(np.ceil(len(blocks)*fraction)))]
    windows=windows[np.isin(data['block'][windows],retained)]
    raw=data['x'][windows];valid=np.isfinite(raw[...,-8:]).all(-1)
    row,query=np.nonzero(valid)
    graph=graph_for(root,dataset);parts=[];targets=[]
    for first in range(0,len(row),256):
        index=row[first:first+256];q=torch.tensor(query[first:first+256],device=device)
        values=torch.tensor(raw[index],device=device)
        parts.append(build_context(values,q,graph,context_length,mode=mode))
        targets.append(values[torch.arange(len(q),device=device),q,-8:])
    inputs=GraphInputs(*(torch.cat([getattr(part,key) for part in parts]) for key in GraphInputs.__dataclass_fields__))
    return inputs,torch.cat(targets),dict(windows=len(windows),source_blocks=len(retained),block_ids=retained,
                                        candidates=len(row),eligible_fraction=float(valid.mean()))


def fit_flow(root,dataset,capacity,context_length,seed,mode='graph',fraction=1.,steps=None):
    root=Path(root);config=configuration(root);directory=root/'results/graph_flow_v1/models';directory.mkdir(parents=True,exist_ok=True)
    steps=config['training_steps'] if steps is None else steps
    manifest=json.loads((root/'results/graph_flow_v1/data_manifest.json').read_text())['datasets'][dataset]
    specification=dict(dataset=dataset,capacity=capacity,context_length=context_length,seed=seed,mode=mode,
        fraction=fraction,steps=steps,learning_rate=config['learning_rate'],weight_decay=config['weight_decay'],
        batch=config['training_batch'],train_sha256=manifest['splits']['train']['sha256'],
        development_sha256=manifest['splits']['development']['sha256'],graph_sha256=manifest['graph_sha256'],
        model_code_sha256=sha256(root/'src/iot_repair/graph_flow_model.py'))
    identity=hashlib.sha256(json.dumps(specification,sort_keys=True).encode()).hexdigest()[:20]
    path=directory/(identity+'.pt');record_path=directory/(identity+'.json')
    if record_path.exists():
        record=json.loads(record_path.read_text());assert record['specification']==specification
        assert sha256(path)==record['sha256'];return record
    if not torch.cuda.is_available():raise RuntimeError('CUDA is required for the registered model fits')
    torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    train,target,volume=candidate_training_data(root,dataset,'train',context_length,mode,fraction)
    development,dev_target,dev_volume=candidate_training_data(root,dataset,'development',context_length,mode)
    channels=len(graph_for(root,dataset)['groups'])
    model=GraphFlow(channels,dimension=8,**capacity).cuda()
    optimizer=torch.optim.AdamW(model.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
    best=float('inf');state=None;history=[];best_step=0
    torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
    for step in range(steps):
        model.train();indices=torch.randint(len(target),(config['training_batch'],),device='cuda')
        loss=-model.log_prob(target[indices],train.select(indices)).mean()
        if not torch.isfinite(loss):raise FloatingPointError('Nonfinite training density '+identity)
        optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);optimizer.step()
        if (step+1)%config['check_every']==0 or step+1==steps:
            model.eval();values=[]
            with torch.no_grad():
                for first in range(0,len(dev_target),256):
                    sl=slice(first,first+256);values.append(-model.log_prob(dev_target[sl],development.select(sl)))
                nll=float(torch.cat(values).mean())
                # E2 is exercised during training diagnostics, not only at final inference.
                generated=model.sample(development.select(slice(0,8)),sample_count=8,
                    generator=torch.Generator(device='cuda').manual_seed(seed+step))
                assert torch.isfinite(generated).all()
            history.append(dict(step=step+1,training_nll=float(loss),development_nll=nll))
            if nll<best:
                best=nll;best_step=step+1;state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
            print(dataset,mode,capacity,context_length,seed,'step',step+1,'dev NLL',nll,flush=True)
    torch.cuda.synchronize();elapsed=time.perf_counter()-start;memory=torch.cuda.max_memory_allocated()
    torch.save(dict(model=state,configuration=model.configuration,specification=specification),path)
    record=dict(id=identity,path=str(path.relative_to(root)),sha256=sha256(path),specification=specification,
                best_step=best_step,development_nll=best,history=history,training_seconds=elapsed,peak_gpu_bytes=memory,
                parameters=sum(p.numel() for p in model.parameters()),training_volume=volume,development_volume=dev_volume,
                generation_during_training=True)
    json_save(record_path,record)
    del model,optimizer,train,target,development,dev_target;torch.cuda.empty_cache()
    return record


def load_flow(root,record,device='cuda'):
    path=Path(root)/record['path']
    if sha256(path)!=record['sha256']:raise ValueError('Model checksum mismatch')
    saved=torch.load(path,map_location=device,weights_only=False)
    model=GraphFlow(**saved['configuration']);model.load_state_dict(saved['model']);return model.to(device).eval()


def develop_models(root):
    root=Path(root);config=configuration(root);output=root/'results/graph_flow_v1/development';output.mkdir(parents=True,exist_ok=True)
    for dataset in config['datasets']:
        records=[]
        for context in config['context_lengths']:
            for capacity in config['capacities']:
                records.append(fit_flow(root,dataset,capacity,context,config['seeds'][0]))
        selected=min(records,key=lambda row:(row['development_nll'],row['parameters'],row['id']))
        json_save(output/(dataset+'_models.json'),dict(grid=records,selected=selected,
            selection='Minimum normal development candidate NLL; no final evaluation access'))
    return output
