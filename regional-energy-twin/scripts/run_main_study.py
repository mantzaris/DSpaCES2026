"""Fail-closed entry point for the prospective, currently unauthorized main study.

Stage 1's stop gate means there is intentionally no hidden launch path. A revised
study must supply a frozen executable job list as well as explicit authorization.
This runner provides the wall-clock enforcement for such a later approved list.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import yaml


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/main_study.yaml')
    parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--authorize-main',action='store_true')
    parser.add_argument('--max-gpu-hours',type=float,default=24.)
    args=parser.parse_args()
    if not 0 < args.max_gpu_hours <= 24:
        parser.error('The main ceiling is 24 total allocated GPU-hours; no extension is authorized')
    config=yaml.safe_load(Path(args.config).read_text())
    decision=json.loads(Path('results/decision.json').read_text())
    print(json.dumps(dict(config_authorized=config.get('authorized',False),
        stage1_decision=decision['decision'],projections=decision['main_cost_projection']),indent=2))
    if args.preflight:return 0
    if not args.authorize_main or not config.get('authorized',False):
        parser.error('Main study is not authorized; Stage 1 only')
    if decision['decision']!='continue' or not config.get('scientific_review_passed',False):
        parser.error('Stage 1 scientific gate failed; a revised protocol and reviewed gate are required')
    jobs=config.get('frozen_jobs')
    if not jobs or any(not isinstance(job,list) or not job or not all(isinstance(x,str) for x in job) for job in jobs):
        parser.error('No reviewed frozen main-study job list is installed')
    # The already consumed Stage 1 allocation counts toward the total ceiling.
    prior=json.loads(Path('results/resource_ledger.json').read_text())['allocated_wall_seconds']
    cap=args.max_gpu_hours*3600-prior
    if cap<=0:parser.error('Total study allocation cap already exhausted')
    ledger_path=Path('results/main_resource_ledger.json')
    if ledger_path.exists():
        ledger=json.loads(ledger_path.read_text())
        if ledger['jobs']!=jobs or ledger['total_hours']!=args.max_gpu_hours:
            parser.error('Cannot reset budget or change frozen jobs on restart')
    else:
        ledger=dict(start_timestamp=time.time(),start_utc=datetime.now(timezone.utc).isoformat(),
                    deadline_timestamp=time.time()+cap,total_hours=args.max_gpu_hours,
                    prior_stage_seconds=prior,jobs=jobs,completed_jobs=0)
        ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
    for index,job in enumerate(jobs[ledger['completed_jobs']:],start=ledger['completed_jobs']):
        remaining=ledger['deadline_timestamp']-time.time()
        if remaining<=0:raise TimeoutError('Total allocated wall-time cap reached')
        # Own the process group so a timeout also stops worker descendants.
        process=subprocess.Popen(job,start_new_session=True)
        try:
            code=process.wait(timeout=max(.01,remaining-5))
            if code:raise subprocess.CalledProcessError(code,job)
        except (subprocess.TimeoutExpired,KeyboardInterrupt):
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
            ledger['stopped_at_cap_or_interrupt']=True
            ledger['allocated_wall_seconds']=time.time()-ledger['start_timestamp']+prior
            ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
            raise
        ledger['completed_jobs']=index+1
        ledger['allocated_wall_seconds']=time.time()-ledger['start_timestamp']+prior
        ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
