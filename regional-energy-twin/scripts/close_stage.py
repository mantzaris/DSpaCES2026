"""Record a clean end to the bounded research window without stopping the user's pod."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import yaml
from evidence_fusion.resource_ledger import Budget, utcnow

cfg=yaml.safe_load(Path('configs/pilot.yaml').read_text())
budget=Budget('results/resource_ledger.json',cfg['allocation_start_utc'],cfg['gpu_allocation_cap_seconds'],cache='data')
names={'run_pilot.py','run_benchmarks.py','run_controlled.py','run_main_study.py','audit_residuals.py'}
workers=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
        cmd=(proc/'cmdline').read_bytes().split(b'\0')
        # Match complete argv script basenames, not shell command text.
        matched=[Path(x.decode(errors='replace')).name for x in cmd if x and b'\n' not in x]
        running=names.intersection(matched)
        if running:workers.append(dict(pid=int(proc.name),scripts=sorted(running)))
    except (OSError,ValueError):pass
if workers:raise RuntimeError('Research worker still active: '+repr(workers))
cache_bytes=sum(p.stat().st_size for p in Path('data').rglob('*') if p.is_file())
project_bytes=sum(p.stat().st_size for p in Path('.').rglob('*') if p.is_file() and not p.is_symlink())
cuda=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
state=dict(observed_utc=utcnow(),active_research_workers=workers,
    cuda_compute_processes=cuda.strip().splitlines(),cache_bytes=cache_bytes,
    project_file_bytes=project_bytes,main_study_started=False,pod_stopped=False,
    pod_billing_status='User pod remains allocated; provider billing time and rates are not available')
Path('results/final_runtime.json').write_text(json.dumps(state,indent=2)+'\n')
budget.check();budget.record('stage_completed',no_active_research_worker=True,
    cache_bytes=cache_bytes,project_file_bytes=project_bytes,pod_remains_allocated=True)
print(json.dumps(state,indent=2))
