"""Export a local replay dashboard grounded entirely in saved experiment fields."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .calibration import rank_pvalues
from .data import load_data
from .localization import merge_groups
from .utils import write_json


def rounded(value):
    if isinstance(value,list):return [rounded(v) for v in value]
    if isinstance(value,dict):return {k:rounded(v) for k,v in value.items()}
    if isinstance(value,float):return round(value,5)
    return value


def build(root: Path, datasets: list[str] | None = None) -> None:
    destination=root/'dashboard';(destination/'data').mkdir(parents=True,exist_ok=True)
    catalog=[]
    for name in (datasets or ['synthetic64','intel','pems']):
        directory=root/'experiments/full'/f'score-{name}-physical-17'
        data=load_data(root,name)
        groups=json.loads((directory/'groups.json').read_text())
        events=json.loads((directory/'events.json').read_text())
        calibration=np.load(directory/'calibration.npz')
        index=calibration['methods'].tolist().index('diffusion/entropy')
        maxima=calibration['maxima'][:,index]
        cases=[0,18] if name=='synthetic64' else [len(events)-2]
        for event_index in cases:
            frames=[]
            paths=sorted((directory/'replay').glob(f'{event_index}-*.json'),key=lambda p:int(p.stem.split('-')[-1]))
            for path in paths:
                frame=json.loads(path.read_text())
                scores=np.array([np.nan if v is None else v for v in frame['scores']['diffusion/entropy']])
                frame['p_adjusted']=rank_pvalues(maxima,np.where(np.isfinite(scores),scores,-np.inf)).tolist()
                frame['family_p']=float(rank_pvalues(maxima,np.max(np.where(np.isfinite(scores),scores,-np.inf))))
                alerts=np.where((np.asarray(frame['p_adjusted'])<=.1)&np.isfinite(scores))[0]
                alerts=alerts[np.argsort(-scores[alerts],kind='stable')].tolist()
                frame['merged_alert_groups']=merge_groups(alerts,[g['nodes'] for g in groups],.5)
                frame['correlations']=[matrix for family in frame['correlations'] for matrix in family]
                frame['expected_correlations']=[matrix for family in frame['expected_correlations'] for matrix in family]
                frame['scores']=frame['scores']['diffusion/entropy']
                frames.append(frame)
            if not frames:continue
            payload={'dataset':name,'event':events[event_index],'groups':groups,'frames':frames,
                     'coordinates':data.coordinates,'edges':np.argwhere(np.triu(np.maximum(data.adjacency,data.adjacency.T)>0,1)),
                     'node_ids':data.node_ids,'channels':data.channels,'units':data.units,'center':data.center,'scale':data.scale,
                     'calibration_units':len(maxima),'alpha':.1,'checkpoint':json.loads((directory/'status.json').read_text())['checkpoint_sha256'],
                     'strict_score_threshold':float(np.sort(maxima)[len(maxima)-int(np.floor(.1*(len(maxima)+1)))]) if .1*(len(maxima)+1)>=1 else None,
                     'graph_kind':'synthetic coupling' if name.startswith('synthetic') else 'coordinate proximity' if name=='intel' else 'release road-distance graph'}
            filename=f'{name}-{event_index}.json'
            write_json(destination/'data'/filename,payload)
            # Compact array JSON for fast local replay; retain full-precision
            # source experiment files separately.
            path=destination/'data'/filename
            path.write_text(json.dumps(rounded(json.loads(path.read_text())),separators=(',',':')))
            label=f'{name}: '+({'copy':'copy collapse','noise':'independent noise'}.get(events[event_index]['kind'],'native unlabelled recording'))
            catalog.append({'file':'data/'+filename,'label':label})
    template=(root/'src/iot_entropy/dashboard_template.html').read_text()
    (destination/'index.html').write_text(template.replace('__CATALOG__',json.dumps(catalog)))
    write_json(destination/'schema.json',{'version':1,'sensor':'node_ids index, coordinates, measurement channels/units; supplied graph edges',
               'group':'nodes, window, lag, channel; frozen scan index',
               'event':'controlled injection metadata or untouched recording with unknown cause',
               'frame':'historical issuance/observation times, observed/ref feature distributions, correlations, masks, scores and scan-adjusted rank values',
               'reference':'All displayed reference traces are from the same saved diffusion sample ensemble',
               'feature_order':['H','delta H','C','delta C','Cabs','delta Cabs','D','delta D','P','delta P']})
