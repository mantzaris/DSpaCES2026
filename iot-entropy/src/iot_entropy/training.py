"""Development-selected training and budgeted checkpoints."""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import torch

from .data import SensorData
from .graphs import normalized_adjacency
from .models import GDN, GraphDiffusion, calendar
from .utils import Budget, digest, seed_all, synchronize, write_json


def build_diffusion(data: SensorData, config: dict, device: str, graph: str = 'physical') -> GraphDiffusion:
    adjacency=normalized_adjacency(data.adjacency)
    if graph=='removed': adjacency=np.eye(len(adjacency),dtype=np.float32)
    if graph=='shuffled':
        permutation=np.random.default_rng(991).permutation(len(adjacency))
        adjacency=adjacency[permutation][:,permutation]
    return GraphDiffusion(len(data.node_ids),len(data.channels),config['context'],config['hidden'],
                          config['layers'],config['diffusion_steps'],
                          torch.as_tensor(adjacency,device=device),
                          torch.as_tensor(data.coordinates,dtype=torch.float32,device=device)).to(device)


def fit(data: SensorData, config: dict, seed: int, directory: Path, budget: Budget,
        device: str = 'cuda', kind: str = 'diffusion', graph: str = 'physical', screen: bool = True) -> tuple[torch.nn.Module,dict]:
    seed_all(seed)
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32=True
    horizon=max(w+w//4 for w in config['windows']) if kind=='diffusion' else 1
    context=config['context']
    model=build_diffusion(data,config,device,graph) if kind=='diffusion' else GDN(len(data.node_ids),len(data.channels),context,config['gdn_hidden'],config['gdn_topk']).to(device)
    x=torch.as_tensor(data.standardized,device=device)
    cal=torch.as_tensor(calendar(data.timestamps),device=device)
    train_indices=data.issuance_indices(0,context,horizon,1)
    dev_indices=data.issuance_indices(1,context,horizon,max(horizon,24))
    rng=np.random.default_rng(seed)
    optimizer=torch.optim.Adam(model.parameters(),lr=config['learning_rate'])
    batch_size=config['batch_size']
    steps=config['training_steps'] if kind=='diffusion' else config['gdn_steps']
    best=float('inf'); unimproved=0; history=[]
    checkpoint=directory/'checkpoints'/f'{data.name}-{kind}-{graph}-{seed}.pt'
    checkpoint.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    if str(device).startswith('cuda'): torch.cuda.reset_peak_memory_stats()
    def batch_loss(indices: np.ndarray) -> torch.Tensor:
        target_ids=torch.as_tensor(indices[:,None]+np.arange(horizon)[None],device=device)
        history_ids=torch.as_tensor(indices[:,None]-context+np.arange(context)[None],device=device)
        if kind=='diffusion':
            return model.loss(x[target_ids],x[history_ids],cal[target_ids],screen)
        target=x[target_ids[:,0]]
        mask=torch.isfinite(target)
        if screen: mask=mask&(target.abs()<=8)
        residual=model(x[history_ids])-torch.nan_to_num(target)
        return (residual.square()*mask).sum()/mask.sum().clamp_min(1)
    for step in range(1,steps+1):
        budget.check();model.train();optimizer.zero_grad(set_to_none=True)
        indices=rng.choice(train_indices,batch_size)
        with torch.autocast(device_type=torch.device(device).type,dtype=torch.bfloat16,enabled=str(device).startswith('cuda')):
            loss=batch_loss(indices)
        if not torch.isfinite(loss): raise FloatingPointError('Nonfinite training loss')
        loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
        if step%config['validation_every']==0 or step==steps:
            model.eval()
            # Fixed random validation noise per checkpoint comparison, restore
            # training RNG afterwards so validation cannot alter future updates.
            with torch.random.fork_rng(devices=[torch.cuda.current_device()] if str(device).startswith('cuda') else []):
                torch.manual_seed(seed+10000)
                with torch.no_grad():
                    losses=[float(batch_loss(dev_indices[k:k+batch_size]).item()) for k in range(0,min(len(dev_indices),64),batch_size)]
            validation=float(np.mean(losses));synchronize(device)
            row={'step':step,'loss':float(loss),'development_loss':validation,'seconds':time.monotonic()-started}
            history.append(row); print(data.name,kind,graph,seed,row,flush=True)
            if validation<best:
                best=validation;unimproved=0
                torch.save({'state_dict':model.state_dict(),'config':config,'seed':seed,'kind':kind,'graph':graph,'step':step,'screen':screen},checkpoint)
            else: unimproved+=1
            if unimproved>=config['early_stopping_patience']:break
    model.load_state_dict(torch.load(checkpoint,map_location=device,weights_only=False)['state_dict'])
    synchronize(device)
    manifest={'dataset':data.name,'kind':kind,'seed':seed,'graph':graph,'screen':screen,
              'training_seconds':time.monotonic()-started,'best_development_loss':best,
              'parameters':sum(p.numel() for p in model.parameters()),'history':history,
              'checkpoint':str(checkpoint),'checkpoint_sha256':digest(checkpoint),
              'peak_gpu_bytes':torch.cuda.max_memory_allocated() if str(device).startswith('cuda') else None}
    write_json(directory/f'{data.name}-{kind}-{graph}-{seed}-training.json',manifest)
    return model,manifest
