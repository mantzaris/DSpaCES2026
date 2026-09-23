from pathlib import Path
import json
import yaml
from threadpoolctl import threadpool_limits
from evidence_fusion.resource_ledger import Budget
from evidence_fusion.replay_benchmarks import benchmark

cfg=yaml.safe_load(Path('configs/pilot.yaml').read_text())
threadpool_limits(limits=cfg['cpu_threads'])
budget=Budget('results/resource_ledger.json',cfg['allocation_start_utc'],cfg['gpu_allocation_cap_seconds'],cache='data')
budget.record('benchmarks_start')
result=benchmark('data/benchmark_input.npz',budget)
print(json.dumps({k:v for k,v in result.items() if k not in ('records','hardware')},indent=2))
