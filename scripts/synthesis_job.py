"""Account local saved-output analysis and document builds; never start GPU work."""
import argparse
import datetime as dt
import fcntl
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--ledger', default='results/synthesis/resource_ledger.json')
    parser.add_argument('--prior-handoff', default='results/acquisition/resource_handoff.json')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    path = Path(args.ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = (path.parent/'.cpu_job.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX)
    prior = json.loads(Path(args.prior_handoff).read_text())
    ledger = json.loads(path.read_text()) if path.exists() else dict(
        prior_handoff=args.prior_handoff,
        prior_cpu_minutes=prior['cumulative_cpu_job_minutes'], jobs=[],
        gpu_allocation_minutes=0,
        accounting='Local saved-output analysis and document preparation only. No experimental GPU allocation window opened. Closed-stage cloud billing idle continues separately; reading/writing time is not CPU job time.')
    remaining = (21600 - ledger['prior_cpu_minutes']*60
                 - sum(j['wall_seconds'] for j in ledger['jobs'])
                 - ledger.get('ancillary_cpu_seconds', 0))
    if remaining < args.timeout:
        raise SystemExit('Requested job exceeds remaining cumulative CPU support allowance')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('A local command is required')
    job = dict(label=args.label, command=command, started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
               wall_seconds=args.timeout, status='running_reservation')
    ledger['jobs'].append(job)
    path.write_text(json.dumps(ledger, indent=2)+'\n')
    start = time.monotonic()
    try:
        code = subprocess.run(command, timeout=args.timeout).returncode
    except subprocess.TimeoutExpired:
        code = 124
    finally:
        job.update(wall_seconds=time.monotonic()-start, status='finished')
    job['exit_code'] = code
    ledger['additional_cpu_job_minutes'] = sum(j['wall_seconds'] for j in ledger['jobs'])/60
    ledger['cumulative_cpu_job_minutes'] = ledger['prior_cpu_minutes']+ledger['additional_cpu_job_minutes']
    ledger['remaining_cpu_job_minutes'] = 360-ledger['cumulative_cpu_job_minutes']
    ledger['charged_additional_cpu_minutes'] = ledger['additional_cpu_job_minutes']+ledger.get('ancillary_cpu_seconds',0)/60
    ledger['charged_cumulative_cpu_minutes'] = ledger['prior_cpu_minutes']+ledger['charged_additional_cpu_minutes']
    ledger['charged_remaining_cpu_minutes'] = 360-ledger['charged_cumulative_cpu_minutes']
    ledger['remaining_gpu_allocation_minutes'] = prior['remaining_original_allocation_minutes']
    path.write_text(json.dumps(ledger, indent=2)+'\n')
    raise SystemExit(code)


if __name__ == '__main__':
    main()
