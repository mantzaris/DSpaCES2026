"""Continuation ledger; never modifies or resets the closed Stage 1 ledger."""
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
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--ancillary-seconds', type=int, default=0,
                        help='Conservative unwrapped transfer/admin CPU charge at closure only')
    parser.add_argument('--handoff-reserve-seconds', type=int, default=0,
                        help='Conservative allocation tail for final closed-ledger copy and handoff')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.ancillary_seconds < 0 or (args.ancillary_seconds and not args.close):
        parser.error('Ancillary charge must be nonnegative and supplied only at closure')
    if args.handoff_reserve_seconds < 0 or (args.handoff_reserve_seconds and not args.close):
        parser.error('Handoff reserve must be nonnegative and supplied only at closure')
    root = Path(__file__).resolve().parents[1]
    folder = root/'results/shock'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder/'resource_ledger.json'
    prior = json.loads((root/'results/refinement/resource_handoff.json').read_text())
    with (folder/'.ledger.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        now = time.time()
        if path.exists():
            ledger = json.loads(path.read_text())
        else:
            ledger = dict(stage='regional_shock', start_epoch=now,
                start_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                prior_gpu_seconds=60*prior['cumulative_regional_allocation_minutes'],
                prior_cpu_seconds=60*prior['cumulative_cpu_job_minutes'],
                cap_seconds=min(5400, 60*prior['remaining_original_allocation_minutes']), jobs=[], closed=False,
                accounting='All elapsed from first new job to closure, including setup, idle, local jobs and artifact copies. Closed-stage billing idle recorded separately, not reset or charged as experimental use.',
                previous_stage_closed_utc=prior['charged_through_utc'],
                inter_stage_billing_idle_seconds=now-dt.datetime.fromisoformat(prior['charged_through_utc']).timestamp())
        if ledger['closed']:
            raise SystemExit('Stage is closed; no further jobs authorized here')
        for job in ledger['jobs']:
            if job['status'] == 'running':
                job.update(status='interrupted_reservation_charged', wall_seconds=job['timeout'])
        elapsed = now-ledger['start_epoch']
        remaining = min(ledger['cap_seconds']-elapsed,
                        21600-ledger['prior_cpu_seconds']-sum(j['wall_seconds'] for j in ledger['jobs']))
        if args.close:
            if args.ancillary_seconds+args.handoff_reserve_seconds > remaining:
                raise SystemExit('Ancillary charge/reserve would exceed remaining resource cap')
            ledger.update(closed=True, closed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                          ancillary_cpu_seconds=args.ancillary_seconds,
                          handoff_allocation_reserve_seconds=args.handoff_reserve_seconds,
                          ancillary_charge_note='Conservative allowance for unwrapped SCP, archive extraction, git archive and read-only administration; elapsed allocation already includes these.')
        else:
            command = args.command[1:] if args.command[:1] == ['--'] else args.command
            if not command or remaining <= 0:
                raise SystemExit('Missing command or exhausted allocation')
            timeout = min(args.timeout, remaining)
            row = dict(label=args.label, command=command, timeout=timeout, status='running',
                       start_utc=dt.datetime.now(dt.timezone.utc).isoformat())
            ledger['jobs'].append(row)
            path.write_text(json.dumps(ledger, indent=2)+'\n')
            env = dict(os.environ, PYTHONPATH=str(root/'src')+':'+str(root/'.deps'),
                       OPENBLAS_NUM_THREADS='4', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4')
            start = time.monotonic()
            with (folder/(args.label+'.log')).open('w') as output:
                proc = subprocess.Popen(command, cwd=root, env=env, stdout=output,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    code = proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                    code = 124
            row.update(status='passed' if code == 0 else 'failed', exit_code=code,
                       wall_seconds=time.monotonic()-start)
        ledger['measured_elapsed_seconds'] = time.time()-ledger['start_epoch']
        ledger['allocated_seconds'] = ledger['measured_elapsed_seconds']+ledger.get('handoff_allocation_reserve_seconds', 0)
        if args.close:
            ledger['charged_through_utc'] = dt.datetime.fromtimestamp(
                ledger['start_epoch']+ledger['allocated_seconds'], dt.timezone.utc).isoformat()
        ledger['cumulative_regional_allocated_seconds'] = ledger['prior_gpu_seconds']+ledger['allocated_seconds']
        ledger['charged_cpu_seconds'] = ledger['prior_cpu_seconds']+sum(j['wall_seconds'] for j in ledger['jobs'])+ledger.get('ancillary_cpu_seconds', 0)
        ledger['remaining_regional_seconds'] = 10800-ledger['cumulative_regional_allocated_seconds']
        ledger['remaining_stage_seconds'] = ledger['cap_seconds']-ledger['allocated_seconds']
        path.write_text(json.dumps(ledger, indent=2)+'\n')
        print(json.dumps(ledger if args.close else row))
        raise SystemExit(0 if args.close else code)


if __name__ == '__main__':
    main()
