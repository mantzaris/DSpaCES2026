"""Coherent command-line stages; all artifacts are relative to the project root."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser=argparse.ArgumentParser(description='IoT correlation-spectrum research stages')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    stages=parser.add_subparsers(dest='stage',required=True)
    stages.add_parser('acquire')
    prepare=stages.add_parser('prepare');prepare.add_argument('--dataset',choices=['intel','pems','all'],default='all')
    synth=stages.add_parser('synthetic');synth.add_argument('--nodes',type=int,nargs='+',default=[64,128,256]);synth.add_argument('--device',default='cuda')
    feature=stages.add_parser('features');feature.add_argument('--dataset',default='synthetic64');feature.add_argument('--device',default='cpu')
    stages.add_parser('train')
    calibration=stages.add_parser('calibrate');calibration.add_argument('--dataset',default='synthetic64');calibration.add_argument('--seed',type=int,default=17)
    score=stages.add_parser('score');score.add_argument('--dataset');score.add_argument('--seed',type=int)
    stages.add_parser('evaluate');stages.add_parser('figures');stages.add_parser('dashboard');stages.add_parser('paper')
    args=parser.parse_args();root=args.root.resolve()
    if args.stage=='acquire':
        from .data import acquire
        acquire(root)
    elif args.stage=='prepare':
        from .data import prepare_intel,prepare_pems
        for name,fn in [('intel',prepare_intel),('pems',prepare_pems)]:
            if args.dataset in ['all',name]:fn(root)
    elif args.stage=='synthetic':
        from .synthetic import prepare_synthetic
        for nodes in args.nodes:prepare_synthetic(root,nodes,args.device)
    elif args.stage=='features':
        from .data import load_data
        from .features import Scan
        import torch,numpy as np
        config=json.loads((root/'configs/full.json').read_text());data=load_data(root,args.dataset)
        scan=Scan(data.adjacency,data.coordinates,data.channels,config,args.device)
        indices=data.issuance_indices(1,48,120,168)[:8]
        values=torch.as_tensor(np.stack([data.standardized[i:i+120] for i in indices]),device=args.device)
        extracted=scan.extract(values)
        out=root/'experiments/features';out.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(out/f'{args.dataset}.npz',features=extracted.values.cpu().numpy(),indices=indices)
    elif args.stage=='calibrate':
        from .data import load_data
        from .experiment import run
        from .utils import Budget,recorded_runtime
        config=json.loads((root/'configs/full.json').read_text())
        print(run(load_data(root,args.dataset),config,args.seed,root/'experiments/full',Budget(config['gpu_hour_budget'],recorded_runtime(root)),stop_after_calibration=True))
    elif args.stage in ['train','score']:
        command=[sys.executable,str(root/'scripts'/('train_all.py' if args.stage=='train' else 'score_all.py'))]
        if args.stage=='score':
            if args.dataset:command+=['--dataset',args.dataset]
            if args.seed:command+=['--seed',str(args.seed)]
        subprocess.run(command,cwd=root,check=True)
    elif args.stage=='evaluate':
        from .reporting import aggregate
        print(aggregate(root))
    elif args.stage=='figures':
        from .plotting import build
        build(root)
    elif args.stage=='dashboard':
        from .dashboard import build
        build(root)
    elif args.stage=='paper':
        subprocess.run(['latexmk','-cd','-pdf','-interaction=nonstopmode','-halt-on-error','manuscript/paper.tex'],cwd=root,check=True)


if __name__=='__main__':main()
