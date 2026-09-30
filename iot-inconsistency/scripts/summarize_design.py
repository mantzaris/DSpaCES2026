"""Describe the executed dataset partitions without changing them."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import json_save
summary={}
for name in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    directory=ROOT/'data/processed'/name;meta=json.loads((directory/'metadata.json').read_text())
    splits={}
    for split in ['train','development','calibration','test']:
        path=directory/(split+'.npz');data=np.load(path)
        manifest=ROOT/'results/study'/name/split/'case_manifest.json'
        if manifest.exists():cases=json.loads(manifest.read_text())['cases'];selected=sorted({c['source_index'] for c in cases})
        else:cases=[];selected=list(range(len(data['x'])))
        x=data['x'][selected]
        splits[split]=dict(windows=len(data['x']),base_windows_selected=len(selected),source_blocks=len(set(map(str,data['block'][selected]))),
            missing_fraction=float(np.mean(~np.isfinite(x))),timestamp_min=int(data['timestamp'][selected].min()),timestamp_max=int(data['timestamp'][selected].max()),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    main=json.loads((ROOT/'results/study'/name/'analysis.json').read_text())
    summary[name]=dict(channels=len(meta['groups']),physical_sources=len(set(meta['groups'])),
        split_unit='trajectory' if name.startswith('synthetic') else 'day with temporal gaps' if name=='intel' else 'whole experiment',splits=splits,
        label_scope='controlled observation and association injection; native process labels separate',
        observation_window_prevalence=main['tracks']['observation']['methods']['proposed']['prevalence'],
        association_window_prevalence=main['tracks']['association']['methods']['proposed']['prevalence'],
        reference_contamination_proxy=meta['reference_contamination_proxy'],units=meta['units'],
        graph_edges=len(json.loads((ROOT/'results/models'/name/'graph.json').read_text())['edges']))
json_save(ROOT/'results/dataset_summary.json',summary)
print({name:{'channels':d['channels'],'test_base_windows':d['splits']['test']['base_windows_selected'],'test_missing_fraction':d['splits']['test']['missing_fraction']} for name,d in summary.items()})
