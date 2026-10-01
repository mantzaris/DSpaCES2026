"""Compact publication evidence without changing any original scientific result.

All JSON records are lossless. Compact score files retain every detector score,
label, eligibility flag, score audit component, repair mean and proper-score
metric. Redundant prior means and interval endpoints are omitted only from the
explicitly renamed compact copies. Full saved GPU generations and operator
artifacts retain every array. Original checkpoints and full case files remain
outside Git and are never deleted by this command.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import lzma
import tarfile
import zipfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'results/graph_flow_v1'
OMIT={'flow_lower','flow_upper','audit_posterior_mean','ppca_prior_mean','ppca_lower','ppca_upper',
      'mixture_ppca_prior_mean','mixture_ppca_lower','mixture_ppca_upper',
      'all_ppca_prior_mean','all_ppca_lower','all_ppca_upper'}


def digest(data):return hashlib.sha256(data).hexdigest()


def file_digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def repack(path,omit=()):
    output=io.BytesIO();names=[];omitted=[]
    with np.load(path,allow_pickle=False) as source:
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(source.files):
                if name in omit:omitted.append(name);continue
                names.append(name);content=io.BytesIO()
                np.lib.format.write_array(content,source[name],allow_pickle=False)
                archive.writestr(zipfile.ZipInfo(name+'.npy',(1980,1,1,0,0,0)),content.getvalue())
        result=output.getvalue()
        with np.load(io.BytesIO(result),allow_pickle=False) as restored:
            for name in names:np.testing.assert_array_equal(source[name],restored[name])
    return result,names,omitted


def pack():
    output=DIRECTORY/'publication';output.mkdir(exist_ok=True)
    datasets=json.loads((DIRECTORY/'protocol_lock.json').read_text())['configuration']['datasets']
    manifest=dict(version=1,scope=__doc__,bundles=[])
    for dataset in datasets:
        source=[]
        for split in ('calibration','test'):
            source.extend(sorted((DIRECTORY/dataset/split).glob('*')))
        # Proper-score and outcome summaries already remain directly in Git.
        source=[p for p in source if p.is_file() and p.suffix in ('.json','.npz')]
        destination=output/(dataset+'.tar.xz');temporary=destination.with_suffix('.xz.tmp');entries=[]
        with lzma.open(temporary,'wb',preset=6) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|') as archive:
                for path in source:
                    original=str(path.relative_to(ROOT));item=dict(original_path=original,original_sha256=file_digest(path),original_bytes=path.stat().st_size)
                    if path.suffix=='.npz':
                        data,kept,omitted=repack(path,OMIT)
                        relative=Path('results/graph_flow_v1/compact')/path.relative_to(DIRECTORY)
                        item.update(kind='array-exact compact score evidence',kept=kept,omitted=omitted)
                    else:data=path.read_bytes();relative=path.relative_to(ROOT);item['kind']='exact bytes'
                    info=tarfile.TarInfo(str(relative));info.size=len(data);info.mode=0o644;info.mtime=0
                    archive.addfile(info,io.BytesIO(data));item.update(path=str(relative),sha256=digest(data),bytes=len(data));entries.append(item)
        temporary.replace(destination)
        manifest['bundles'].append(dict(path=str(destination.relative_to(ROOT)),sha256=file_digest(destination),bytes=destination.stat().st_size,entries=entries))
        print(dataset,destination.stat().st_size,'bytes',len(entries),'records',flush=True)
    # Uncompressed NPZ inside xz shares repeated inputs and preserves every value.
    # It has an explicitly separate path; exact original file hashes are retained.
    source=sorted((DIRECTORY/'evidence').glob('*.npz'))
    destination=output/'generations.tar.xz';temporary=destination.with_suffix('.xz.tmp');entries=[]
    with lzma.open(temporary,'wb',preset=6) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|') as archive:
            for path in source:
                data,kept,omitted=repack(path)
                relative=Path('results/graph_flow_v1/compact/evidence')/path.name
                info=tarfile.TarInfo(str(relative));info.size=len(data);info.mode=0o644;info.mtime=0
                archive.addfile(info,io.BytesIO(data))
                entries.append(dict(path=str(relative),sha256=digest(data),bytes=len(data),original_path=str(path.relative_to(ROOT)),
                    original_sha256=file_digest(path),original_bytes=path.stat().st_size,kind='all arrays exact',kept=kept,omitted=omitted))
    temporary.replace(destination)
    manifest['bundles'].append(dict(path=str(destination.relative_to(ROOT)),sha256=file_digest(destination),bytes=destination.stat().st_size,entries=entries))
    manifest['archive_bytes']=sum(b['bytes'] for b in manifest['bundles'])
    manifest['original_bytes']=sum(e['original_bytes'] for b in manifest['bundles'] for e in b['entries'])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def verify(restore=False):
    manifest=json.loads((DIRECTORY/'publication/manifest.json').read_text());count=0
    for bundle in manifest['bundles']:
        path=ROOT/bundle['path'];assert file_digest(path)==bundle['sha256'],str(path)
        expected={e['path']:e for e in bundle['entries']};seen=set()
        with tarfile.open(path,'r|xz') as archive:
            for item in archive:
                assert item.isfile() and item.name in expected and item.name not in seen
                name=PurePosixPath(item.name);assert not name.is_absolute() and '..' not in name.parts
                data=archive.extractfile(item).read();assert digest(data)==expected[item.name]['sha256']
                if restore:
                    target=ROOT/item.name
                    if target.exists():assert file_digest(target)==expected[item.name]['sha256'],'Refusing to overwrite edited evidence '+str(target)
                    else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                seen.add(item.name);count+=1
        assert seen==set(expected)
    return dict(verified_records=count,archive_bytes=manifest['archive_bytes'],restored=restore)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['pack','verify','restore']);args=parser.parse_args()
    if args.action=='pack':
        result=pack();print(json.dumps({k:result[k] for k in ('archive_bytes','original_bytes')},indent=2))
    else:print(json.dumps(verify(args.action=='restore'),indent=2))
