"""Persistent regional budgets; wrap every executed preparation/diagnostic job."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--kind', choices=['cpu', 'gpu'], default='cpu')
    p.add_argument('--label', required=True)
    p.add_argument('--timeout', type=int, default=3600)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / 'results/regional'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (a.kind + '_ledger.json')
    command = a.command[1:] if a.command[:1] == ['--'] else a.command
    if not command:
        p.error('command required')
    with (folder / (a.kind + '.lock')).open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = json.loads(path.read_text()) if path.exists() else dict(
            kind=a.kind, cap_seconds=21600 if a.kind == 'cpu' else 10800, jobs=[])
        if ledger.get('closed'):
            raise SystemExit('Allocation closed; do not reset it')
        for row in ledger['jobs']:
            if row['status'] == 'running':
                row.update(status='interrupted_reservation_charged', wall_seconds=row['timeout'])
        now = time.time()
        if a.kind == 'gpu':
            ledger.setdefault('allocation_start', now)
            remaining = ledger['cap_seconds'] - (now-ledger['allocation_start'])
            cpu_path=folder/'cpu_ledger.json'
            cpu=json.loads(cpu_path.read_text()) if cpu_path.exists() else {'jobs':[]}
            cpu_used=sum(x.get('wall_seconds',x.get('timeout',0)) for x in cpu['jobs'])
            # Conservatively charge whole GPU jobs to CPU job budget as well.
            remaining=min(remaining,21600-cpu_used-sum(x['wall_seconds'] for x in ledger['jobs']))
        else:
            remaining = ledger['cap_seconds']-sum(x['wall_seconds'] for x in ledger['jobs'])
            gpu_path=folder/'gpu_ledger.json'
            if gpu_path.exists():
                gpu=json.loads(gpu_path.read_text())
                remaining-=sum(x.get('wall_seconds',x.get('timeout',0)) for x in gpu['jobs'])
        timeout = min(a.timeout, remaining)
        if timeout <= 0:
            raise SystemExit('Regional budget exhausted')
        row = dict(label=a.label, command=command, timeout=timeout, status='running',
                   start_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        ledger['jobs'].append(row)
        path.write_text(json.dumps(ledger, indent=2)+'\n')
        env = dict(os.environ, PYTHONPATH=str(root/'src')+':'+str(root/'.deps'),
                   OPENBLAS_NUM_THREADS='4', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4')
        if a.kind == 'cpu':
            env['CUDA_VISIBLE_DEVICES'] = ''
        start = time.monotonic()
        with (folder/(a.label+'.log')).open('w') as out:
            job = subprocess.Popen(command, cwd=root, env=env, stdout=out,
                                   stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = job.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(job.pid, signal.SIGKILL)
                job.wait()
                code = 124
        row.update(status='passed' if code == 0 else 'failed', exit_code=code,
                   wall_seconds=time.monotonic()-start)
        ledger['cumulative_job_wall_seconds'] = sum(x['wall_seconds'] for x in ledger['jobs'])
        if a.kind == 'gpu':
            ledger['allocated_wall_seconds'] = time.time()-ledger['allocation_start']
        path.write_text(json.dumps(ledger, indent=2)+'\n')
        print(json.dumps(row))
        raise SystemExit(code)


if __name__ == '__main__':
    main()
