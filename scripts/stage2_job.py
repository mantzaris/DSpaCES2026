"""Run an explicitly selected CPU audit job against a persistent 30-minute cap.

Reading/writing and source retrieval are not diagnostic jobs. Every executed
diagnostic (including failed attempts) uses this wrapper. Interrupted unfinished
jobs conservatively consume their entire reserved timeout on the next call.
"""
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or not 0 < args.timeout <= 1800:
        parser.error('Provide a command and timeout in (0,1800]')
    root = Path(__file__).resolve().parents[1]
    folder = root / 'results/stage2'
    folder.mkdir(exist_ok=True)
    path = folder / 'diagnostic_ledger.json'
    with (folder / '.diagnostic.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = json.loads(path.read_text()) if path.exists() else dict(
            cap_seconds=1800, accounting='Cumulative wall time including failures; CPU-only; reading/writing excluded', jobs=[])
        for job in ledger['jobs']:
            if job['status'] == 'running':
                job.update(status='interrupted_reserved_charged', wall_seconds=job['timeout_seconds'])
        used = sum(job.get('wall_seconds', 0) for job in ledger['jobs'])
        timeout = min(args.timeout, ledger['cap_seconds'] - used)
        if timeout <= 0:
            raise SystemExit('Stage 2 diagnostic wall-time cap exhausted')
        row = dict(label=args.label, command=command, start_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   timeout_seconds=timeout, status='running', cuda_visible_devices='')
        ledger['jobs'].append(row)
        path.write_text(json.dumps(ledger, indent=2) + '\n')
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='4', OMP_NUM_THREADS='4',
                   MKL_NUM_THREADS='4', PYTHONPATH=str(root / 'src'))
        start = time.monotonic()
        with (folder / (args.label + '.log')).open('w') as output:
            process = subprocess.Popen(command, cwd=root, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
                status = 'passed' if code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                code, status = 124, 'timeout'
        row.update(status=status, exit_code=code, wall_seconds=time.monotonic()-start,
                   end_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        ledger['cumulative_wall_seconds'] = sum(job['wall_seconds'] for job in ledger['jobs'])
        path.write_text(json.dumps(ledger, indent=2) + '\n')
        print(json.dumps(row, indent=2))
        raise SystemExit(code)


if __name__ == '__main__':
    main()
