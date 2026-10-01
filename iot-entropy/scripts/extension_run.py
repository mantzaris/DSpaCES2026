"""Execute/resume frozen comparisons under the cumulative GPU wall-time limit."""
import argparse
import json
from pathlib import Path

from iot_entropy.extension import run
from iot_entropy.utils import Budget, digest, write_json

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--dataset',default='all')
parser.add_argument('--seed',type=int)
args=parser.parse_args()
config=json.loads((root/'configs/full.json').read_text())
config.update(json.loads((root/'configs/extension-v2.json').read_text()))
directory=root/'experiments/extension-v2';directory.mkdir(exist_ok=True)
pilot=json.loads((directory/'pilot.json').read_text())
assert pilot['validation']['returncode']==0
prior=config['original_recorded_seconds']+pilot['elapsed_seconds']
prior+=sum(json.loads(p.read_text())['elapsed_seconds'] for p in directory.glob('*/attempt-*.json'))
budget=Budget(config['gpu_hour_budget'],prior)
write_json(directory/'run-manifest.json',{'protocol_freeze_revision':'18b9c4a7',
    'protocol_sha256':digest(root/'docs/extension-protocol.md'),
    'config_sha256':digest(root/'configs/extension-v2.json'),
    'previous_recorded_seconds':prior,'budget_hours':config['gpu_hour_budget'],
    'namespace':'extension-v2','original_namespace':'experiments/full',
    'priority':'all configurations at seed17, then29, then43'})
try:
    for seed in ([args.seed] if args.seed else config['training_seeds']):
        for dataset in (config['datasets'] if args.dataset=='all' else [args.dataset]):
            result=run(root,dataset,seed,config,budget)
            print(json.dumps(result),flush=True)
finally:
    write_json(directory/'budget.json',{'cumulative_seconds':budget.elapsed,
        'limit_seconds':config['gpu_hour_budget']*3600,
        'original_seconds':config['original_recorded_seconds'],
        'pilot_seconds':pilot['elapsed_seconds'],
        'completed_runs':[p.parent.name for p in directory.glob('*/status.json')]})
