"""Download and integrity check; independent of scientific Python dependencies."""
import argparse
import json
from evidence_fusion.data_access import fetch_archive
from evidence_fusion.resource_ledger import Budget

p = argparse.ArgumentParser()
p.add_argument('--start', required=True)
args = p.parse_args()
budget = Budget('results/resource_ledger.json', args.start, cache='data')
budget.record('data_download_start')
try:
    info = fetch_archive('data', 'manifests')
    budget.check()
    budget.record('data_download_complete', bytes=info['bytes'])
    print(json.dumps({k: v for k, v in info.items() if k not in ('entries', 'extracted')}, indent=2))
except BaseException as error:
    budget.record('data_download_failed', error=repr(error))
    raise
