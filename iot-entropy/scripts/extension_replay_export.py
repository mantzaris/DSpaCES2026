"""Compact dashboard replay from saved joint forecasts; CPU-only export."""
import gzip
import json
from pathlib import Path

import numpy as np
import torch

from iot_entropy.data import load_data
from iot_entropy.features import Scan
from iot_entropy.calibration import rank_pvalues
from iot_entropy.utils import write_json, digest

root=Path(__file__).resolve().parents[1]
torch.set_num_threads(2)
out=root/'results/extension-v2/replays';out.mkdir(parents=True,exist_ok=True)
catalog=[]
for name in ['synthetic64','intel','pems']:
    directory=root/'experiments/extension-v2'/f'{name}-17'
    if not (directory/'status.json').exists():continue
    config=json.loads((directory/'configuration.json').read_text())
    replay=json.loads((directory/'replay.json').read_text())
    data=load_data(root,name)
    replay.update({'version':'spatial-temporal-v2','reference':'diffusion','units':data.units,
                   'config':{k:config[k] for k in ['permutation_q','permutation_tau','sample_delta','sample_r','sample_theiler',
                               'top_fraction','minimum_sensor_coverage','localization_budget']},
                   'example_selection':'First prespecified copy episode on base zero, seed17; not selected by detector success',
                   'interval_seconds':data.interval_seconds,
                   'feature_names':['permutation','sample','acf1','variance'],
                   'feature_indices':[0,1,2,6],'raw_display_stride':2})
    scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cpu')
    for frame in replay['frames']:
        start=frame['issue_index']+1
        path=root/'experiments/extension-v2/cache'/f'{name}-17'/f'{start}-diffusion.npy'
        samples=torch.tensor(np.load(path))
        raw=np.asarray(frame['raw'],dtype=np.float32)
        padded=np.concatenate([np.full_like(raw[:24],np.nan),raw])
        x=torch.tensor(padded)
        samples=samples.masked_fill(~torch.isfinite(x)[None],float('nan'))
        gen=scan.extract(samples);actual=scan.extract(x)
        observed_R={};reference_R={}
        for family,a,b in zip(scan.families,actual.correlations,gen.correlations):
            if family.window!=96:continue
            for j in range(a.shape[1]):
                observed_R[str(family.offset+j)]=a[0,j].numpy()
                reference_R[str(family.offset+j)]=torch.nanmean(b[:,j],dim=0).numpy()
        frame['observed_R']=observed_R;frame['reference_R']=reference_R
        floors=np.load(directory/'development-parameters.npz')['spatial']
        center=torch.nanmedian(gen.values,dim=0).values
        mad=torch.nanmedian((gen.values-center).abs(),dim=0).values
        level_scale=(1.4826*mad+torch.tensor(floors))[:,0].numpy()
        actual_H=np.asarray(frame['spatial'],dtype=float)[:,0]
        middle_H=np.asarray(frame['spatial_center'],dtype=float)[:,0]
        frame['spatial_z_level']=(actual_H-middle_H)/level_scale
        frame['pvalues']={family:rank_pvalues(np.asarray([v if v is not None else -np.inf
            for v in replay['calibration'][family]]),np.asarray([v if v is not None else -np.inf
            for v in scores])) for family,scores in frame['groups'].items()}
        for key in ['raw','raw_low','raw_high']:
            frame[key]=(np.asarray(frame[key],dtype=float)*data.scale+data.center)[1::2]
        frame['joint_reference_sha256']=digest(path)
        # W96 is a single transparent replay view; both windows remain in results.
        frame['temporal']={'96':frame['temporal']['96']}
        for key in ['values','low','high','center','signed']:
            frame['temporal']['96'][key]=np.asarray(frame['temporal']['96'][key],dtype=float)[:,:,[0,1,2,6],:]
    def compact(value):
        if isinstance(value,np.ndarray):return compact(value.tolist())
        if isinstance(value,list):return [compact(v) for v in value]
        if isinstance(value,dict):return {k:compact(v) for k,v in value.items()}
        if isinstance(value,float):return round(value,6) if np.isfinite(value) else None
        return value
    payload=json.dumps(compact(replay),separators=(',',':')).encode()
    filename=name+'.json.gz';(out/filename).write_bytes(gzip.compress(payload,mtime=0))
    catalog.append({'dataset':name,'file':'data/extension/'+name+'.json','source':'results/extension-v2/replays/'+filename,
                    'bytes':(out/filename).stat().st_size,'sha256':digest(out/filename)})
    print(name,len(payload),(out/filename).stat().st_size,flush=True)
write_json(out/'catalog.json',catalog)
