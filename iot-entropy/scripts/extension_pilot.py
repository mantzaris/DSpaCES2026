"""Development-only GPU profile; records failures and validation wall time."""
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

from iot_entropy.data import load_data
from iot_entropy.experiment import load_models
from iot_entropy.features import Scan
from iot_entropy.reference import BlockBootstrap, issue_reference
from iot_entropy.temporal import trajectory
from iot_entropy.utils import synchronize, write_json

root = Path(__file__).resolve().parents[1]
directory = root/'experiments/extension-v2'
directory.mkdir(exist_ok=True)
config = json.loads((root/'configs/full.json').read_text())
config.update(json.loads((root/'configs/extension-v2.json').read_text()))
torch.set_num_threads(4)
started = time.monotonic()
result = {'profiles': [], 'device': torch.cuda.get_device_name(), 'torch': torch.__version__}
try:
    checks = subprocess.run(['.venv/bin/python', '-m', 'pytest', 'tests', '-q', '--disable-warnings'],
                            cwd=root, capture_output=True, text=True)
    result['validation'] = {'returncode': checks.returncode, 'output': checks.stdout+checks.stderr}
    if checks.returncode:
        raise RuntimeError('Validation gate failed')
    for name in ['synthetic64', 'intel', 'pems']:
        data = load_data(root, name)
        model, _ = load_models(data, config, 17, root/'experiments/full', 'cuda')
        bootstrap = BlockBootstrap(data, 48, 120, 'cuda')
        scan = Scan(data.adjacency, data.coordinates, data.channels, config, 'cuda')
        start = int(data.issuance_indices(1,48,120,168)[0])
        observed = torch.as_tensor(data.standardized[start:start+120], device='cuda')
        profile = {'dataset': name, 'target_start': start, 'reference': {}}
        with torch.no_grad():
            trajectory(observed, 96, config); synchronize('cuda')
            for ref in ['bootstrap', 'diffusion']:
                torch.cuda.reset_peak_memory_stats(); t = time.perf_counter()
                samples = issue_reference(model, data, data.standardized, start, 120,
                                          config, 'cuda', ref, bootstrap, 89017)
                synchronize('cuda'); generation = time.perf_counter()-t
                samples = samples.masked_fill(~torch.isfinite(observed)[None], float('nan'))
                t = time.perf_counter()
                spatial = scan.extract(samples)
                temporals = [trajectory(samples, w, config) for w in config['windows']]
                synchronize('cuda'); measurements = time.perf_counter()-t
                profile['reference'][ref] = {'generation_seconds': generation,
                    'measurement_seconds': measurements,
                    'peak_gpu_bytes': torch.cuda.max_memory_allocated(),
                    'finite_temporal_fraction': [float(torch.isfinite(z['u']).float().mean()) for z in temporals],
                    'spatial_eligible_fraction': float(spatial.eligible.float().mean())}
                del samples, spatial, temporals
        result['profiles'].append(profile)
        print(json.dumps(profile), flush=True)
        del model, bootstrap, data
except Exception as error:
    result['error'] = repr(error)
    raise
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    write_json(directory/'pilot.json', result)
