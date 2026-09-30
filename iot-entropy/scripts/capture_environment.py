"""Capture the numerical runtime and its installed transitive dependencies."""
from pathlib import Path
from importlib.metadata import distribution,distributions
import json
import platform

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root=Path(__file__).resolve().parents[1];directory=root/'environment';directory.mkdir(exist_ok=True)
roots=['numpy','scipy','pandas','matplotlib','h5py','requests','torch','pytest','setuptools']
pending=list(roots);resolved={}
while pending:
    name=canonicalize_name(pending.pop())
    if name in resolved:continue
    package=distribution(name);resolved[name]=package.version
    for requirement in package.requires or []:
        item=Requirement(requirement)
        if item.marker is None or item.marker.evaluate({'extra':''}):pending.append(item.name)
header='# Installed scientific environment and transitive closure; Python '+platform.python_version()+'\n'
header+='--extra-index-url https://download.pytorch.org/whl/cu128\n'
(directory/'requirements.lock.txt').write_text(header+'\n'.join(f'{name}=={version}' for name,version in sorted(resolved.items()))+'\n')
packages=sorted([{'name':d.metadata['Name'],'version':d.version} for d in distributions()],key=lambda d:d['name'].lower())
(directory/'packages.json').write_text(json.dumps(packages,indent=2)+'\n')
(directory/'runtime.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform(),
  'lock_roots':roots,'locked_packages':len(resolved),'scope':'Installed required dependency closure; optional extras excluded'},indent=2)+'\n')
print('Locked',len(resolved),'installed scientific and transitive packages.')
