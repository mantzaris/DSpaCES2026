"""Close only this experiment ledger, never the pod or its storage."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    root=Path('results/regional'); p=root/'gpu_ledger.json'
    x=json.loads(p.read_text())
    if any(j['status']=='running' for j in x['jobs']):
        raise RuntimeError('A regional job is still marked running')
    if not x.get('closed'):
        x.update(closed=True,closed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                 allocated_wall_seconds=time.time()-x['allocation_start'],pod_lifecycle_action='none; remains allocated')
        p.write_text(json.dumps(x,indent=2)+'\n')
    source={}
    for file in ['scripts/replay_regional.py','scripts/regional_job.py','src/evidence_fusion/regional_solver.py',
                 'src/evidence_fusion/regional_data.py','configs/regional_pilot.json']:
        source[file]=hashlib.sha256(Path(file).read_bytes()).hexdigest()
    (root/'executed_source_hashes.json').write_text(json.dumps(source,indent=2)+'\n')
    with (root/'pod_environment.lock.txt').open('w') as f:
        subprocess.run(['/workspace/DSpaCES2026-stage1/.venv/bin/pip','freeze'],stdout=f,check=True)
    info=dict(source_commit='bf2896254ae93d85dc58619b46b3a8642c5f1af2',
              original_replay_source_commit='2dd63f2',source_hashes=source,
              gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],text=True).strip(),
              active_cuda_processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_gpu_memory','--format=csv,noheader'],text=True).strip(),
              cpu_model=next(s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),
              cpu_quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else 'unavailable',
              memory_limit=Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else 'unavailable',
              pod_status='allocated; no experiment running; no stop/delete request executed')
    (root/'pod_close.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(x,indent=2))


if __name__=='__main__':main()
