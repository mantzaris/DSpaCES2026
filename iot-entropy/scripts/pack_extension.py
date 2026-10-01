"""Compact only results needed for frozen analyses; retain full local arrays.

Rank vectors are dictionary encoded losslessly after retaining the declared
development-selected localization budget. No score, p-value or used rank is
discarded. Full 24-node rankings remain in .local and on the experiment host.
"""
import argparse
import gzip
import hashlib
import json
import shutil
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parents[1];namespace=root/'experiments/extension-v2'
parser=argparse.ArgumentParser();parser.add_argument('action',choices=['pack','verify']);args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[];json_records=[]
if args.action=='pack':
 for directory in sorted(namespace.glob('*-*/')):
    path=directory/'predictions.npz'
    if not path.exists():continue
    backup=root/'.local/extension-v2/full-predictions'/directory.name/'predictions.npz'
    config=json.loads((directory/'configuration.json').read_text());k=config['localization_budget']
    with np.load(path) as archive:arrays={key:archive[key] for key in archive.files}
    if 'rankings' in arrays:
        backup.parent.mkdir(parents=True,exist_ok=True)
        if backup.exists():assert sha(backup)==sha(path)
        else:shutil.copy2(path,backup)
        ranks=arrays.pop('rankings')[...,:k]
        unique,index=np.unique(ranks.reshape(-1,k),axis=0,return_inverse=True)
        arrays.update(rankings_unique=unique,ranking_index=index.reshape(ranks.shape[:-1]).astype('uint32'))
        np.testing.assert_array_equal(unique[arrays['ranking_index']],ranks)
        np.savez_compressed(path,**arrays)
    else:ranks=arrays['rankings_unique'][arrays['ranking_index']]
    records.append({'path':str(path.relative_to(root)),'sha256':sha(path),'bytes':path.stat().st_size,
        'full_local_backup':str(backup.relative_to(root)),'full_sha256':sha(backup),
        'retained_rank_budget':k,'original_rank_budget':24,
        'retained_rank_sha256':hashlib.sha256(ranks.tobytes()).hexdigest(),
        'schema':'rankings_unique[ranking_index]; remaining arrays unchanged'})
    for filename in ['groups.json','support.json','fidelity.json','timings.json','references.json']:
        plain=directory/filename;target=Path(str(plain)+'.gz')
        encoded=gzip.compress(plain.read_bytes(),compresslevel=9,mtime=0);target.write_bytes(encoded)
        assert gzip.decompress(encoded)==plain.read_bytes()
        json_records.append({'path':str(target.relative_to(root)),'sha256':sha(target),
                             'original_sha256':sha(plain),'bytes':target.stat().st_size})
 for plain in [root/'results/extension-v2'/name for name in ['event-pr-curves.json','summary.json','paired.json']]:
    target=Path(str(plain)+'.gz');target.write_bytes(gzip.compress(plain.read_bytes(),compresslevel=9,mtime=0))
    json_records.append({'path':str(target.relative_to(root)),'sha256':sha(target),
                         'original_sha256':sha(plain),'bytes':target.stat().st_size})
 manifest={'predictions':records,'lossless_json':json_records,'bulk_policy':'No raw datasets, checkpoints, trajectory caches or full measurement tensors in Git. Full originals retained locally and on the existing experiment host.'}
 (namespace/'packaging.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
else:
 manifest=json.loads((namespace/'packaging.json').read_text())
 for record in manifest['predictions']:
    path=root/record['path'];assert sha(path)==record['sha256']
    with np.load(path) as x:ranks=x['rankings_unique'][x['ranking_index']]
    assert ranks.shape[-1]==record['retained_rank_budget']
    assert hashlib.sha256(ranks.tobytes()).hexdigest()==record['retained_rank_sha256']
 for record in manifest['lossless_json']:
    path=root/record['path'];assert sha(path)==record['sha256']
    assert hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()==record['original_sha256']
print(json.dumps({'action':args.action,'prediction_MiB':sum(r['bytes'] for r in manifest['predictions'])/2**20,
                  'lossless_JSON_MiB':sum(r['bytes'] for r in manifest['lossless_json'])/2**20}))
