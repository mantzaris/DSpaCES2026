"""Run frozen scans after full model training; resume completed configurations."""
from pathlib import Path
import json
import argparse

from iot_entropy.data import load_data
from iot_entropy.experiment import run
from iot_entropy.utils import Budget,recorded_runtime,write_json

parser=argparse.ArgumentParser()
parser.add_argument('--dataset')
parser.add_argument('--seed',type=int)
parser.add_argument('--graph',default='physical',choices=['physical','removed','shuffled'])
parser.add_argument('--smoke',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
config=json.loads((root/'configs/full.json').read_text())
directory=root/'experiments/full'
previous=recorded_runtime(root)
budget=Budget(config['gpu_hour_budget'],previous)
if args.smoke:
    config.update(base_episodes=1,fault_types=['copy','noise','flatline'],durations=[48],severities=[1.],generated_samples=8)
    # Write smoke scoring separately while retrieving existing trained models.
    import tempfile,os
    smoke_dir=root/'experiments/scoring-smoke'
    smoke_dir.mkdir(parents=True,exist_ok=True)
    if not (smoke_dir/'checkpoints').exists():(smoke_dir/'checkpoints').symlink_to(Path('../full/checkpoints'),target_is_directory=True)
    directory=smoke_dir
try:
    seeds=[args.seed] if args.seed else config['training_seeds'] if args.graph=='physical' else [17]
    for name in ([args.dataset] if args.dataset else config['datasets']):
        for seed in seeds:
            result=run(load_data(root,name),config,seed,directory,budget,graph=args.graph)
            print(result,flush=True)
    marker='scoring_status.json' if not args.dataset and not args.seed and args.graph=='physical' else f'selected-scoring-{args.dataset or "all"}-{args.graph}-{args.seed or "all"}.json'
    if not (directory/marker).exists():
        write_json(directory/marker,{'status':'complete','total_budgeted_seconds':budget.elapsed})
except TimeoutError as exc:
    write_json(directory/'scoring_status.json',{'status':'budget_exhausted','total_budgeted_seconds':budget.elapsed,'reason':str(exc)})
