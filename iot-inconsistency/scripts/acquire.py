"""Acquire public research inputs and record exact byte hashes/revisions.

Never execute downloaded code here. Extract archives only inside this project.
"""
from __future__ import annotations
import concurrent.futures, hashlib, json, tarfile, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data/manifests/acquisition.json'


def fetch(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'DSpaCES-research/1.0'})
        with urllib.request.urlopen(request,timeout=120) as response:
            path.write_bytes(response.read())
    return {'url':url,'path':str(path.relative_to(ROOT)), 'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def repository(repo,name,destination):
    api=urllib.request.Request('https://api.github.com/repos/'+repo+'/commits?per_page=1',headers={'User-Agent':'DSpaCES-research/1.0'})
    with urllib.request.urlopen(api,timeout=60) as response:
        revision=json.load(response)[0]['sha']
    archive=ROOT/'literature/downloads'/(name+'-'+revision+'.tar.gz')
    record=fetch('https://codeload.github.com/'+repo+'/tar.gz/'+revision,archive)
    target=ROOT/destination/name
    if not target.exists():
        target.mkdir(parents=True)
        with tarfile.open(archive) as tf:
            for member in tf.getmembers():
                parts=Path(member.name).parts[1:]
                if not parts or member.issym() or member.islnk(): continue
                relative=Path(*parts)
                if '..' in relative.parts: raise ValueError('Unsafe archive member')
                output=target/relative
                if member.isdir(): output.mkdir(parents=True,exist_ok=True)
                elif member.isfile():
                    output.parent.mkdir(parents=True,exist_ok=True)
                    output.write_bytes(tf.extractfile(member).read())
    record.update(repository=repo,revision=revision,extracted=str(target.relative_to(ROOT)))
    licenses=list(target.glob('*LICENSE*'))+list(target.glob('*COPYING*'))
    record['license_files']=[str(p.relative_to(ROOT)) for p in licenses]
    return record


def main():
    tasks=[('GDN',lambda:repository('d-ailin/GDN','GDN','literature/upstream')),
           ('DiffAD',lambda:repository('ChunjingXiao/DiffAD','DiffAD','literature/upstream')),
           ('CSDI',lambda:repository('ermongroup/CSDI','CSDI','literature/upstream')),
           ('SKAB',lambda:repository('waico/SKAB','SKAB','data/raw')),
           ('intel_data',lambda:fetch('https://db.csail.mit.edu/labdata/data.txt.gz',ROOT/'data/raw/intel/data.txt.gz')),
           ('intel_locations',lambda:fetch('https://db.csail.mit.edu/labdata/mote_locs.txt',ROOT/'data/raw/intel/mote_locs.txt')),
           ('intel_description',lambda:fetch('https://db.csail.mit.edu/labdata/labdata.html',ROOT/'data/raw/intel/description.html'))]
    results=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fn):name for name,fn in tasks if name not in results or 'error' in results[name]}
        for future in concurrent.futures.as_completed(futures):
            name=futures[future]
            try: results[name]=future.result(); print(name,results[name].get('revision',''),results[name]['bytes'],flush=True)
            except Exception as exc: results[name]={'error':str(exc)}; print(name,'FAILED',str(exc),flush=True)
            MANIFEST.write_text(json.dumps(results,indent=2)+'\n')
    if any('error' in value for value in results.values()): raise SystemExit(1)

if __name__=='__main__': main()
