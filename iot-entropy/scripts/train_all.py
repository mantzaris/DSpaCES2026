"""Train core models and preregistered graph/contamination sensitivities."""
from pathlib import Path
import json
import time

import torch

from iot_entropy.data import load_data
from iot_entropy.synthetic import prepare_synthetic
from iot_entropy.training import fit
from iot_entropy.utils import Budget, digest, recorded_runtime, write_json

root=Path(__file__).resolve().parents[1]
config=json.loads((root/'configs/full.json').read_text())
directory=root/'experiments/full'
directory.mkdir(parents=True,exist_ok=True)
status_path=directory/'training_status.json'
if status_path.exists() and json.loads(status_path.read_text())['status']=='complete':
    print('Training already complete; preserving original runtime and lineage.')
    raise SystemExit(0)
previous=recorded_runtime(root)
budget=Budget(config['gpu_hour_budget'],previous)
torch.set_num_threads(4)
for nodes in [64,128,256]:
    if not (root/f'data/processed/synthetic{nodes}.npz').exists():
        prepare_synthetic(root,nodes,'cuda')
try:
    for name in config['datasets']:
        data=load_data(root,name)
        for seed in config['training_seeds']:
            for kind in ['diffusion','gdn']:
                path=directory/f'{name}-{kind}-physical-{seed}-training.json'
                if path.exists():continue
                fit(data,config,seed,directory,budget,kind=kind)
        for graph in ['removed','shuffled']:
            path=directory/f'{name}-diffusion-{graph}-17-training.json'
            if not path.exists():fit(data,config,17,directory,budget,graph=graph)
        # Unscreened training stored in its own folder with unambiguous identity.
        path=directory/'unscreened'/f'{name}-diffusion-physical-17-training.json'
        if not path.exists():fit(data,config,17,directory/'unscreened',budget,screen=False)
    status='complete'
except TimeoutError:
    status='budget_exhausted'
write_json(directory/'training_status.json',{'status':status,'elapsed_seconds':budget.elapsed,
    'config_sha256':digest(root/'configs/full.json'),'revision':(root/'environment/code-revision.txt').read_text().strip()})
