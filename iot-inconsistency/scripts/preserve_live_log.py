"""Recover the still-open job log after an early result-sync inode replacement."""
from pathlib import Path
import argparse,os,time
p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--output',required=True);a=p.parse_args()
# Open once so the original inode remains readable through process completion.
with Path(f'/proc/{a.pid}/fd/1').open('rb') as source,Path(a.output).open('wb',buffering=0) as target:
    while True:
        chunk=source.read(1024*1024)
        if chunk:target.write(chunk);continue
        try:os.kill(a.pid,0)
        except ProcessLookupError:
            chunk=source.read()
            if chunk:target.write(chunk)
            break
        time.sleep(1)
