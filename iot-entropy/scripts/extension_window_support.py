"""Separately calibrated W48/W96 and 51-vs-52-draw support sensitivities.

Seed17 only, all five dataset configurations; no generation or retuning.
Saved per-sensor measurements are reused. The complete main runs remain intact.
"""
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from iot_entropy.data import load_data
from iot_entropy.extension_data import extension_data, episode_values
from iot_entropy.extension_scoring import extract, summaries, score, MAIN
from iot_entropy.features import Scan
from iot_entropy.calibration import rank_pvalues
from iot_entropy.evaluation import alert_intervals, match_events
from iot_entropy.utils import Budget, synchronize, write_json
from iot_entropy.extension_budget import components, authorized_hours

root=Path(__file__).resolve().parents[1];namespace=root/'experiments/extension-v2'
config=json.loads((root/'configs/full.json').read_text());config.update(json.loads((root/'configs/extension-v2.json').read_text()))
ceiling=authorized_hours(root)
prior=sum(components(root).values())
budget=Budget(ceiling,prior);started=time.monotonic()
attempt=namespace/f'window-attempt-{len(list(namespace.glob("window-attempt-*.json")))}.json'
torch.set_num_threads(4);rows=[]
rounding_path=root/'results/extension-v2/reference-support-rounding.json'
rounding=json.loads(rounding_path.read_text()) if rounding_path.exists() else []
try:
 with torch.no_grad():
  for name in config['datasets']:
    budget.check();directory=namespace/f'{name}-17';selected=json.loads((directory/'configuration.json').read_text())
    destination=namespace/'window-support'/f'{name}-17';destination.mkdir(parents=True,exist_ok=True)
    if (destination/'metrics.json').exists():
        rows+=json.loads((destination/'metrics.json').read_text());continue
    data=load_data(root,name);manifest=json.loads((directory/'data-lineage.json').read_text());bases=manifest['extension_blocks']
    if name.startswith('synthetic'):
        with np.load(namespace/'cache'/f'{name}-backgrounds.npz') as archive:
            data=replace(data,values=np.concatenate([data.values[:data.bounds[1]],archive['extension_values']]),
                timestamps=np.concatenate([data.timestamps[:data.bounds[1]],archive['extension_timestamps']]),
                bounds=archive['bounds'],episode_bounds=archive['episode_bounds'])
    values=data.standardized;scan=Scan(data.adjacency,data.coordinates,data.channels,selected,'cuda')
    with np.load(directory/'development-parameters.npz') as params:
        floors={'spatial':torch.tensor(params['spatial'],device='cuda'),
                'temporal':{w:torch.tensor(params[f'temporal_{w}'],device='cuda') for w in selected['windows']}}
    events=json.loads((directory/'events.json').read_text());times=np.arange(167,312,12)
    with np.load(directory/'measurements.npz') as archive:observations=archive['temporal']
    methods=[f'{ref}/{policy}/{scope}/{family}' for ref in ['bootstrap','diffusion']
             for policy in ['legacy51','ceil52'] for scope in ['all','48','96'] for family in MAIN]
    masks={'all':torch.ones(len(scan.records),dtype=torch.bool,device='cuda')}
    masks.update({str(w):torch.tensor([r['window']==w for r in scan.records],device='cuda') for w in [48,96]})
    def measurements(start,raw,ref):
        cached=torch.tensor(np.load(namespace/'cache'/f'{name}-17'/f'{start}-{ref}.npy'),device='cuda')
        samples=cached.masked_fill(~torch.isfinite(raw)[None],float('nan'))
        generated=extract(samples,scan,selected);summary=summaries(generated,floors,selected)
        return samples,generated,summary
    def maxima(actual,generated,summary):
        answer=[];availability=[]
        original=summary['spatial'].enough.clone()
        counts=torch.isfinite(generated['spatial'].values).sum(0)
        changed=bool((counts==51).any())
        previous=None
        for policy in ['legacy51','ceil52']:
            summary['spatial'].enough=original if policy=='legacy51' else counts>=52
            if policy=='legacy51' or changed:
                previous=score(actual,generated,summary,scan,floors,selected,selected['top_fraction'])['groups']
            for scope in ['all','48','96']:
                for family in MAIN:
                    a=previous[family][masks[scope]];valid=torch.isfinite(a)
                    answer.append(float(a.masked_fill(~valid,-float('inf')).max()))
                    availability.append(float(valid.float().mean()))
        summary['spatial'].enough=original
        return answer,availability,int((counts==51).any(-1).sum())
    cal_indices=data.issuance_indices(2,48,120,168);cal=[]
    for start0 in cal_indices:
        budget.check();start=int(start0);raw=torch.tensor(values[start:start+120],device='cuda')
        actual=extract(raw,scan,selected);combined=[]
        for ref in ['bootstrap','diffusion']:
            samples,generated,summary=measurements(start,raw,ref)
            m,_,boundary=maxima(actual,generated,summary);combined.extend(m)
            rounding.append({'dataset':name,'split':'calibration','start':start,'reference':ref,'groups_at_51':boundary})
        cal.append(combined)
    cal=np.asarray(cal);shape=(len(events),len(times),len(methods))
    scores=np.full(shape,-np.inf,np.float32);available=np.zeros(shape,np.float32)
    for bi,base in enumerate(bases):
        ids=[i for i,e in enumerate(events) if e['base']==bi]
        changed={i:episode_values(data,values,base,events[i],selected,'cuda') for i in ids}
        for ti,end0 in enumerate(times):
            budget.check();end=int(end0);start=base[0]+end-119
            clean=torch.tensor(values[start:start+120],device='cuda')
            references={ref:measurements(start,clean,ref) for ref in ['bootstrap','diffusion']}
            for ei in ids:
                raw=torch.tensor(changed[ei][end-119:end+1],device='cuda')
                actual=extract(raw,scan,selected,include_temporal=False)
                actual['temporal']={w:{'u':torch.tensor(observations[ei,ti,wi][None],device='cuda')}
                                    for wi,w in enumerate(selected['windows'])}
                for ri,ref in enumerate(['bootstrap','diffusion']):
                    samples,generated,summary=references[ref]
                    if events[ei]['kind']=='dropout':
                        generated=extract(samples.masked_fill(~torch.isfinite(raw)[None],float('nan')),scan,selected)
                        summary=summaries(generated,floors,selected)
                    m,a,boundary=maxima(actual,generated,summary)
                    sl=slice(ri*54,(ri+1)*54);scores[ei,ti,sl]=m;available[ei,ti,sl]=a
                    if events[ei]['kind']=='untouched':rounding.append({'dataset':name,'split':'test','start':start,'reference':ref,'groups_at_51':boundary})
        print(json.dumps({'sensitivity':name,'completed_base':bi,'cumulative_seconds':budget.elapsed}),flush=True)
    pvalues=np.stack([rank_pvalues(cal[:,mi],scores[:,:,mi]) for mi in range(len(methods))],-1)
    np.savez_compressed(destination/'predictions.npz',methods=methods,scores=scores,pvalues=pvalues,
                        availability=available,calibration=cal,times=times)
    dataset_rows=[]
    for mi,method in enumerate(methods):
        ref,policy,scope,family=method.split('/')
        tp=fp=fn=0;delays=[]
        for ei,e in enumerate(events):
            alerts=alert_intervals(times,pvalues[ei,:,mi]<=.1,12)
            truth=[(e['onset'],e['onset']+e['duration']-1)] if e['is_fault'] else []
            match=match_events(alerts,truth);tp+=match['tp'];fp+=match['fp'];fn+=match['fn'];delays+=match['delays']
        controls=[i for i,e in enumerate(events) if e['kind']=='untouched']
        dataset_rows.append({'dataset':name,'seed':17,'reference':ref,'support_rule':policy,'window':scope,'family':family,
            'recall':tp/(tp+fn),'precision':tp/max(tp+fp,1),'background_exceedance':float((pvalues[controls,:,mi]<=.1).mean()),
            'availability':float(available[:,:,mi].mean()),'median_delay_samples':float(np.median(delays)) if delays else None,
            'calibration_units':len(cal),'localization':'not re-evaluated in this window sensitivity'})
    write_json(destination/'metrics.json',dataset_rows);rows+=dataset_rows
    write_json(root/'results/extension-v2/window-support.json',rows)
    write_json(root/'results/extension-v2/reference-support-rounding.json',rounding)
    del observations
finally:
    write_json(attempt,{'elapsed_seconds':time.monotonic()-started,'cumulative_seconds':budget.elapsed,'limit_seconds':ceiling*3600})
