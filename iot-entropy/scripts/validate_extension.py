"""Record CPU checks, or one CUDA validation stage within the experiment ledger."""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser(); parser.add_argument('--cuda', action='store_true'); args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
path = root/'experiments/extension-v2'/('multiscale-validation.json' if args.cuda else 'cpu-validation.json')
if args.cuda:
    import torch
    assert torch.cuda.is_available()
    assert not path.exists(), 'Preserve the accepted CUDA validation record; use an archival rerun copy.'
command = [sys.executable, '-m', 'pytest', '-q', 'tests', '--disable-warnings']
started = time.monotonic()
result = subprocess.run(command, cwd=root, capture_output=True, text=True)
elapsed = time.monotonic()-started
passed = re.search(r'(\d+) passed', result.stdout)
skipped = re.search(r'(\d+) skipped', result.stdout)
record = {'command': command, 'returncode': result.returncode, 'elapsed_seconds': elapsed,
          'passed': int(passed.group(1)) if passed else 0,
          'skipped': int(skipped.group(1)) if skipped else 0,
          'stdout': result.stdout, 'stderr': result.stderr,
          'device': torch.cuda.get_device_name() if args.cuda else 'CPU',
          'scope': 'Mathematical, numerical, leakage, event, localization, aggregation and multiscale endpoint checks'}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
print(result.stdout)
if result.stderr: print(result.stderr, file=sys.stderr)
raise SystemExit(result.returncode)
