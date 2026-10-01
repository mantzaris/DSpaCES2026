"""Pack/restore lossless result files and check the size of the Git index.

The manifest lists selected result files; original files stay on disk. This
script never trains models, changes branches, stages files or pushes to Git.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    path=(root/relative).resolve()
    if root not in path.parents:
        raise ValueError('Artifact path leaves the project: '+relative)
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['pack','restore','check'])
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--max-total-mib',type=float,default=50)
    parser.add_argument('--max-file-mib',type=float,default=5)
    args=parser.parse_args();root=args.project.resolve()
    manifest_path=root/'git-storage.json'
    manifest=json.loads(manifest_path.read_text())
    if args.action=='check':
        repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=root,text=True).strip())
        prefix=str(root.relative_to(repo))+'/'
        entries=subprocess.check_output(['git','ls-files','-s','-z','--',prefix],cwd=repo).split(b'\0')
        blobs={}
        for entry in entries:
            if not entry:continue
            header,path=entry.split(b'\t',1);mode,oid,stage=header.decode().split()
            if stage!='0':raise ValueError('Unmerged path: '+path.decode())
            blobs[path.decode()]=oid
        info=subprocess.check_output(['git','cat-file','--batch-check=%(objectname) %(objectsize)'],
                                     input='\n'.join(sorted(set(blobs.values())))+'\n',cwd=repo,text=True)
        sizes={oid:int(size) for oid,size in (line.split() for line in info.splitlines())}
        total=sum(sizes[oid] for oid in blobs.values())
        largest=max((sizes[oid] for oid in blobs.values()),default=0)
        ignored=subprocess.check_output(['git','ls-files','-ci','--exclude-standard','-z','--',prefix],cwd=repo)
        if ignored:raise ValueError('Ignored bulk files are still staged or tracked; remove them from the index only.')
        if total>args.max_total_mib*1024**2 or largest>args.max_file_mib*1024**2:
            raise ValueError(f'Git size limit exceeded: total={total/1024**2:.2f} MiB; largest={largest/1024**2:.2f} MiB')
        print(json.dumps({'project':root.name,'tracked_files':len(blobs),'total_mib':total/1024**2,'largest_mib':largest/1024**2}))
        return
    for record in manifest['compressed_results']:
        path=safe_path(root,record['original']);archive=safe_path(root,record['archive'])
        if args.action=='pack':
            original=path.read_bytes();encoded=gzip.compress(original,mtime=0)
            if gzip.decompress(encoded)!=original:raise ValueError('Compression round trip failed')
            temp=archive.with_suffix(archive.suffix+'.tmp');temp.write_bytes(encoded);temp.replace(archive)
            record.update(original_sha256=sha(original),archive_sha256=sha(encoded),
                          original_bytes=len(original),archive_bytes=len(encoded))
        else:
            encoded=archive.read_bytes()
            if sha(encoded)!=record['archive_sha256']:raise ValueError('Archive checksum mismatch: '+str(archive))
            original=gzip.decompress(encoded)
            if sha(original)!=record['original_sha256']:raise ValueError('Result checksum mismatch: '+str(archive))
            if path.exists():
                if path.read_bytes()!=original:raise ValueError('Existing local result differs; archive it before restoring: '+str(path))
                continue
            path.parent.mkdir(parents=True,exist_ok=True)
            temp=path.with_suffix(path.suffix+'.restore-tmp');temp.write_bytes(original);temp.replace(path)
    if args.action=='pack':
        manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(f"{args.action}: {len(manifest['compressed_results'])} exact-byte results in {root.name}")


if __name__=='__main__':main()
