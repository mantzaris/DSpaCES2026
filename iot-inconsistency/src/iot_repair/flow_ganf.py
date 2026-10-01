"""Pinned author GANF implementation, with explicit benchmark adapters.

The RNN, GNN and MAF are imported unmodified from EnyanDai/GANF. We replace its
water-specific data loader, forbid same-source adjacency, exclude missing target
losses, select on normal development density only, and aggregate the last eight
per-time losses for the common sensor-interval endpoint. Zero-filled missing
context is an acknowledged limitation of the original architecture.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

from .flow_data import load_data, graph_for, configuration, sha256
from .experiment import json_save


def author_class(root):
    records=json.loads((Path(root)/'literature/graph_flow_sources.json').read_text())
    for record in records:
        if record['name']=='GANF code' and record['path'].endswith(('models/GANF.py','models/NF.py')):
            if sha256(Path(root)/record['path'])!=record['sha256']:raise ValueError('GANF source checksum mismatch')
    source=str(Path(root)/'literature/upstream/GANF')
    if source not in sys.path:sys.path.insert(0,source)
    from models.GANF import GANF
    return GANF


def coordinate_log_prob(model,values,adjacency):
    batch,channels,length=values.shape
    x=torch.nan_to_num(values)[...,None]
    hidden,_=model.rnn(x.reshape(batch*channels,length,1))
    hidden=hidden.reshape(batch,channels,length,-1)
    hidden=model.gcn(hidden,adjacency)
    return model.nf.log_prob(x.reshape(-1,1),hidden.reshape(-1,hidden.shape[-1])).reshape(batch,channels,length)


def fit_ganf(root,dataset,width,seed):
    root=Path(root);config=configuration(root);GANF=author_class(root)
    spec=dict(dataset=dataset,width=width,seed=seed,outer=config['ganf_outer_iterations'],steps_per_outer=config['ganf_steps_per_outer'],
              revision='bce38333b109f325a403dae9aff4987ae5bd6e1f',adapter_sha256=sha256(__file__),
              train_sha256=sha256(root/'data/processed'/dataset/'train.npz'))
    identity=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:20]
    path=root/'results/graph_flow_v1/models'/('ganf_'+identity+'.pt');record_path=path.with_suffix('.json')
    if record_path.exists():
        record=json.loads(record_path.read_text());assert sha256(path)==record['sha256'];return record
    torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    train=load_data(root,dataset,'train');dev=load_data(root,dataset,'development')
    train=torch.tensor(train['x'][train['reference']],device='cuda');dev=torch.tensor(dev['x'][dev['reference']],device='cuda')
    channels=train.shape[1];groups=np.array(graph_for(root,dataset)['groups'])
    allowed=torch.tensor(groups[:,None]!=groups[None,:],device='cuda')
    adjacency=torch.nn.Parameter(torch.nn.init.xavier_uniform_(torch.zeros(channels,channels,device='cuda')).abs()*allowed)
    model=GANF(1,1,width,1,dropout=0.,batch_norm=False).cuda()
    rho=1.;alpha=0.;previous=float('inf');best=float('inf');state=None;history=[]
    torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
    for outer in range(config['ganf_outer_iterations']):
        optimizer=torch.optim.Adam([dict(params=model.parameters(),weight_decay=.0005),dict(params=[adjacency])],lr=.002,weight_decay=0.)
        for step in range(config['ganf_steps_per_outer']):
            model.train();values=train[torch.randint(len(train),(32,),device='cuda')]
            logs=coordinate_log_prob(model,values,adjacency*allowed)
            loss=-logs[torch.isfinite(values)].mean()
            h=torch.trace(torch.matrix_exp(adjacency*adjacency))-channels
            total=loss+.5*rho*h*h+alpha*h
            if not torch.isfinite(total):raise FloatingPointError('GANF training diverged')
            optimizer.zero_grad();total.backward();torch.nn.utils.clip_grad_value_(model.parameters(),1.);optimizer.step()
            with torch.no_grad():adjacency.clamp_(0,1);adjacency.mul_(allowed)
        model.eval()
        with torch.no_grad():
            numerator=0.;denominator=0
            for first in range(0,len(dev),32):
                values=dev[first:first+32];logs=coordinate_log_prob(model,values,adjacency)
                numerator+=float(-logs[torch.isfinite(values)].sum());denominator+=int(torch.isfinite(values).sum())
            nll=numerator/denominator;h_value=float(torch.trace(torch.matrix_exp(adjacency*adjacency))-channels)
        history.append(dict(outer=outer+1,development_nll=nll,acyclicity=h_value,rho=rho,alpha=alpha))
        if nll<best:
            best=nll;state=dict(model={k:v.detach().cpu().clone() for k,v in model.state_dict().items()},adjacency=adjacency.detach().cpu().clone(),selected_outer=outer+1)
        if h_value>.5*previous:rho=min(rho*10,1e16)
        previous=h_value;alpha+=rho*h_value
        print('GANF',dataset,width,seed,outer+1,nll,h_value,flush=True)
    torch.cuda.synchronize();elapsed=time.perf_counter()-start
    torch.save(dict(state,width=width,specification=spec),path)
    record=dict(path=str(path.relative_to(root)),sha256=sha256(path),specification=spec,development_nll=best,
                history=history,training_seconds=elapsed,peak_gpu_bytes=torch.cuda.max_memory_allocated(),
                parameters=sum(p.numel() for p in model.parameters())+adjacency.numel(),selected_outer=state['selected_outer'],
                adapter='Official unchanged model; common data splits; missing losses excluded; same-source diagonal forbidden; last-eight coordinate NLL aggregation; finite augmented-Lagrangian budget')
    json_save(record_path,record);return record


def load_ganf(root,record):
    path=Path(root)/record['path'];assert sha256(path)==record['sha256']
    saved=torch.load(path,map_location='cuda',weights_only=False)
    model=author_class(root)(1,1,saved['width'],1,dropout=0.,batch_norm=False).cuda()
    model.load_state_dict(saved['model']);return model.eval(),saved['adjacency'].cuda()


@torch.no_grad()
def infer_ganf(models,values):
    values=torch.as_tensor(values,dtype=torch.float32,device='cuda')[None]
    logs=torch.stack([coordinate_log_prob(model,values,adjacency)[0,:,-8:].sum(-1) for model,adjacency in models])
    scores=-(torch.logsumexp(logs.double(),0)-np.log(len(models))).cpu().numpy()
    scores[~np.isfinite(values.cpu().numpy()[0,:,-8:]).all(-1)]=-1e12
    return scores
