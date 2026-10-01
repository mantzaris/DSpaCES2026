#!/usr/bin/env python3
"""Fetch exactly pinned source files without modifying the acquisition manifest."""
import hashlib
import json
from pathlib import Path
import urllib.request
root=Path(__file__).resolve().parents[1]
for record in json.loads((root/'literature/graph_flow_sources.json').read_text()):
    if record['name']!='GANF code':continue
    path=root/record['path']
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']:continue
    data=urllib.request.urlopen(record['url'],timeout=60).read()
    assert hashlib.sha256(data).hexdigest()==record['sha256'],record['url']
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
print('Pinned GANF source files verified')
