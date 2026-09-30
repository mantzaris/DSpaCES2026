"""Sequential post-primary GPU stages; never change resources or billing."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

from iot_entropy.utils import write_json

root=Path(__file__).resolve().parents[1]
while not (root/'experiments/full/scoring_status.json').exists():
    time.sleep(15)
primary=json.loads((root/'experiments/full/scoring_status.json').read_text())
if primary['status']!='complete':raise RuntimeError('Primary scoring did not finish: '+str(primary))
commands=[['scripts/benchmark.py'],['scripts/fidelity.py']]
commands += [['scripts/sensitivities.py',stage] for stage in ['quality','global','unscreened','samples','persistence','graphs','directions']]
completed=[]
for command in commands:
    label=Path(command[0]).stem+('-'+command[1] if len(command)>1 else '')
    status=root/'experiments/sensitivity'/f'{command[1]}-status.json' if len(command)>1 else root/'experiments'/('benchmark.json' if label=='benchmark' else 'fidelity-extra.json')
    if status.exists():
        completed.append(label);continue
    print('START',label,flush=True)
    result=subprocess.run([sys.executable,'-u',*command],cwd=root,env=dict(os.environ,PYTHONPATH='src'))
    if result.returncode:
        write_json(root/'experiments/post-primary-status.json',{'status':'failed','stage':label,'returncode':result.returncode,'completed':completed})
        raise SystemExit(result.returncode)
    completed.append(label);print('COMPLETE',label,flush=True)
write_json(root/'experiments/post-primary-status.json',{'status':'complete','completed':completed})
