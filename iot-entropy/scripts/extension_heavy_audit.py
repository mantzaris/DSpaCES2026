"""CPU/file-I/O audit on the experiment host; does not run CUDA operations."""
from pathlib import Path
import json,time
import numpy as np
from iot_entropy.utils import digest,write_json
from iot_entropy.extension_reporting import read_json

root=Path(__file__).resolve().parents[1];ns=root/'experiments/extension-v2'
started=time.monotonic();runs=[];models=[];seen={};data_records={}
for directory in sorted(ns.glob('*-*/')):
    if not (directory/'status.json').exists():continue
    status=read_json(directory/'status.json');name=status['dataset'];seed=status['seed']
    lineage=read_json(directory/'data-lineage.json');events=read_json(directory/'events.json')
    if name in seen:assert seen[name]==events
    else:seen[name]=events
    data_path=root/'data/processed'/f'{name}.npz'
    if name not in data_records:
        actual=digest(data_path);assert actual==lineage['source_processed_sha256']
        data_records[name]={'path':str(data_path.relative_to(root)),'sha256':actual}
    references=read_json(directory/'references.json');reference_bytes=0
    for ref in references:
        path=root/ref['path'];assert digest(path)==ref['sha256']
        assert ref['issue_index']==ref['target_start']-1
        assert ref['decision_index']==ref['target_start']+119
        assert ref['context_start']==ref['target_start']-48
        assert any(int(a)<=ref['context_start'] and ref['decision_index']<int(b)
                   for a,b,p in lineage['split_episodes'] if int(p)==ref['split'])
        reference_bytes+=path.stat().st_size
    path=directory/'measurements.npz'
    with np.load(path) as x:
        shape=x['temporal'].shape;assert shape[:3]==(80,13,2)
        assert x['support'].shape[:5]==shape[:5]
        assert x['feature_names'].tolist()==['permutation','sample','acf1','acf2','acf4','difference_variance','variance','trend','mean','cusum']
    runs.append({'configuration':name,'seed':seed,'full_predictions_sha256':digest(directory/'predictions.npz'),
        'measurements_path':str(path.relative_to(root)),'measurements_sha256':digest(path),
        'measurement_bytes':path.stat().st_size,'temporal_shape':list(shape),
        'verified_reference_files':len(references),'reference_bytes':reference_bytes,
        'references_manifest_sha256':digest(directory/'references.json'),
        'identical_events_across_model_seeds':True,'all_issuance_and_partition_boundaries_valid':True})
    for kind in ['diffusion','gdn']:
        path=root/'experiments/full/checkpoints'/f'{name}-{kind}-physical-{seed}.pt'
        record=read_json(root/'experiments/full'/f'{name}-{kind}-physical-{seed}-training.json')
        actual=digest(path);assert actual==record['checkpoint_sha256']
        models.append({'path':str(path.relative_to(root)),'sha256':actual,'bytes':path.stat().st_size})
    print(directory.name,flush=True)
backgrounds=[]
for path in sorted((ns/'cache').glob('*-backgrounds.npz')):
    backgrounds.append({'path':str(path.relative_to(root)),'sha256':digest(path),'bytes':path.stat().st_size})
write_json(ns/'heavy-artifacts.json',{'status':'verified','host_project_path':'/workspace/iot-entropy',
    'retrieval':'configured direct SSH; selective rsync; no bulk in Git',
    'runs':runs,'models':models,'data':data_records,'synthetic_backgrounds':backgrounds,
    'CPU_file_audit_seconds':time.monotonic()-started,'GPU_operations':0})
