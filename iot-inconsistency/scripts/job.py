"""Durable finite jobs with a local status file and exact resume command."""
from pathlib import Path
import argparse,datetime,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('action',choices=['launch','run','status']);p.add_argument('name');p.add_argument('command',nargs=argparse.REMAINDER)
a=p.parse_args();directory=ROOT/'results/jobs';directory.mkdir(exist_ok=True);status=directory/(a.name+'.json')
if a.action=='status':
    print(status.read_text() if status.exists() else 'No status recorded');raise SystemExit
if a.action=='launch':
    if status.exists():
        previous=json.loads(status.read_text())
        if previous.get('state')=='running':
            try:os.kill(previous['pid'],0);print('Job already running',previous['pid']);raise SystemExit
            except ProcessLookupError:pass
    log=(directory/(a.name+'.log')).open('a')
    child=subprocess.Popen([sys.executable,__file__,'run',a.name]+a.command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    print(json.dumps(dict(launched_pid=child.pid,status=str(status),log=str(directory/(a.name+'.log')))))
else:
    record=dict(pid=os.getpid(),state='running',command=a.command,started=datetime.datetime.now(datetime.timezone.utc).isoformat())
    status.write_text(json.dumps(record,indent=2)+'\n')
    result=subprocess.run(a.command,cwd=ROOT)
    record.update(state='complete' if result.returncode==0 else 'failed',exit_code=result.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    status.write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(result.returncode)
