"""Bounded, resumable GPU training. Test files are never opened by this script."""
from __future__ import annotations
import argparse,hashlib,json,os,sys,time
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.associations import discover_associations
from iot_repair.diffusion import ConditionalDiffusion,ConditionalMean,masked_denoising_loss,training_target_mask
from iot_repair.baselines import GDN
from iot_repair.diffad import DiffAD,select_observations,bicubic_condition,diffusion_loss


def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--steps',type=int,default=1500)
    p.add_argument('--width',type=int,default=128);p.add_argument('--batch',type=int,default=32)
    p.add_argument('--seeds',type=int,nargs='+',default=[1101,2202,3303]);p.add_argument('--models',nargs='+',default=['diffusion','gdn'])
    p.add_argument('--device',default='cuda');args=p.parse_args()
    torch.set_num_threads(4)
    data=ROOT/'data/processed'/args.dataset;out=ROOT/'results/models'/args.dataset;out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((data/'metadata.json').read_text());tr=np.load(data/'train.npz')['x'];d=np.load(data/'development.npz')
    dev=d['x'][d['reference']]
    graph_path=out/'graph.json'
    if not graph_path.exists(): graph_path.write_text(json.dumps(discover_associations(tr,dev,meta['groups']),indent=2)+'\n')
    graph=json.loads(graph_path.read_text());print('graph',len(graph['edges']),'edges',flush=True)
    data_hash=hashlib.sha256(tr.tobytes()).hexdigest()
    train=torch.as_tensor(tr,device=args.device);observed=torch.isfinite(train);values=torch.nan_to_num(train)
    validation=torch.as_tensor(dev[:64],device=args.device)
    run=json.loads((out/'training.json').read_text()) if (out/'training.json').exists() else []
    for kind in args.models:
      for seed in args.seeds:
        torch.manual_seed(seed);np.random.seed(seed)
        if kind in ('diffusion','no_graph'):model=ConditionalDiffusion(tr.shape[1],width=args.width)
        elif kind=='mean':model=ConditionalMean(tr.shape[1],width=args.width)
        elif kind=='gdn':model=GDN(tr.shape[1])
        elif kind=='diffad':model=DiffAD(tr.shape[1])
        else:raise ValueError(kind)
        model=model.to(args.device)
        lr=8e-4 if kind in ('diffusion','no_graph') else json.loads((out/'diffad_selection.json').read_text())['selected_learning_rate'] if kind=='diffad' else 1e-3
        optimizer=torch.optim.Adam(model.parameters(),lr=lr)
        if kind=='diffad':
            selected=torch.as_tensor(select_observations(tr),device=args.device)
            with torch.no_grad():conditions=bicubic_condition(values,selected)
        checkpoint=out/f'{kind}_{seed}.pt';start=0;history=[];elapsed_prior=0.
        if checkpoint.exists():
            saved=torch.load(checkpoint,map_location=args.device,weights_only=False)
            if saved['config']['width']!=args.width: raise ValueError('Checkpoint architecture differs')
            if saved.get('training_data_sha256')!=data_hash: raise ValueError('Checkpoint training data differs or lacks an audited fingerprint')
            model.load_state_dict(saved['model']);optimizer.load_state_dict(saved['optimizer'])
            start=saved['step'];history=saved['history'];elapsed_prior=saved.get('elapsed_seconds',0.)
            torch.set_rng_state(saved['rng_cpu'].cpu())
            if 'rng_cuda' in saved and args.device.startswith('cuda'): torch.cuda.set_rng_state(saved['rng_cuda'].cpu())
        if start>=args.steps: print('already trained',kind,seed,start,flush=True);continue
        torch.cuda.reset_peak_memory_stats() if args.device.startswith('cuda') else None
        model.train();started=time.perf_counter()
        for step in range(start,args.steps):
            idx=torch.randint(len(train),(args.batch,),device=args.device);x=values[idx];o=observed[idx]
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda',dtype=torch.bfloat16,enabled=args.device.startswith('cuda')):
                if kind in ('diffusion','no_graph'): loss=masked_denoising_loss(model,x,o,training_target_mask(o),graph if kind=='diffusion' else dict(graph,edges=[]))
                elif kind=='mean':
                    target=training_target_mask(o);context_mask=o&~target
                    prediction=model(torch.where(context_mask,x,torch.zeros_like(x)),context_mask,graph)
                    loss=torch.where(target,(prediction-x).float().square(),torch.zeros_like(x)).sum()/target.sum().clamp_min(1)
                elif kind=='diffad':loss=diffusion_loss(model,x,o,conditions[idx])
                else:
                    prediction=model(x[...,:56]);mask=o[...,56]
                    loss=torch.where(mask,(prediction-x[...,56]).float().square(),torch.zeros_like(prediction,dtype=torch.float32)).sum()/mask.sum().clamp_min(1)
            if not torch.isfinite(loss): raise ArithmeticError('Nonfinite training loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
            if (step+1)%100==0 or step==0 or step+1==args.steps:
                if args.device.startswith('cuda'):torch.cuda.synchronize()
                elapsed=elapsed_prior+time.perf_counter()-started
                row=dict(step=step+1,loss=float(loss.detach()),elapsed_seconds=elapsed)
                history.append(row);print(args.dataset,kind,seed,row,flush=True)
                state=dict(model=model.state_dict(),optimizer=optimizer.state_dict(),step=step+1,seed=seed,
                    history=history,config=vars(args),elapsed_seconds=elapsed,graph_version=graph['version'],
                    rng_cpu=torch.get_rng_state(),rng_cuda=torch.cuda.get_rng_state() if args.device.startswith('cuda') else None,
                    training_data_sha256=data_hash)
                tmp=checkpoint.with_suffix('.tmp');torch.save(state,tmp);os.replace(tmp,checkpoint)
        run=[r for r in run if not(r['model']==kind and r['seed']==seed)]
        run.append(dict(model=kind,seed=seed,steps=args.steps,parameters=sum(p.numel() for p in model.parameters()),
            elapsed_seconds=elapsed,gpu_hours=elapsed/3600,peak_vram_bytes=torch.cuda.max_memory_allocated() if args.device.startswith('cuda') else 0,
            device=torch.cuda.get_device_name() if args.device.startswith('cuda') else 'cpu',dtype='bfloat16 autocast, float32 loss',learning_rate=lr,
            checkpoint=checkpoint.name,sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest()))
        (out/'training.json').write_text(json.dumps(run,indent=2)+'\n')

if __name__=='__main__':main()
