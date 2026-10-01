"""Post-hoc support/direction strata from saved measurements, without fitting.

Truth is used only to describe affected-sensor support and a best-overlap group.
These summaries do not change any prediction, threshold or localization rule.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from iot_entropy.extension_reporting import read_json
from iot_entropy.utils import write_json

root=Path(__file__).resolve().parents[1];out=root/'results/extension-v2'
rows=[];dominance=[];selection=[]
def mean(x):
    v=np.asarray(x);v=v[np.isfinite(v)]
    return float(v.mean()) if len(v) else None
def direction(x):
    return 'unsupported' if x is None else 'increase' if x>1e-7 else 'decrease' if x< -1e-7 else 'unchanged'
for directory in sorted((root/'experiments/extension-v2').glob('*-*/')):
    if not (directory/'status.json').exists():continue
    status=read_json(directory/'status.json');name=status['dataset'];seed=status['seed']
    events=read_json(directory/'events.json');groups=read_json(directory/'groups.json')
    config=read_json(directory/'configuration.json')
    selection.append({'configuration':name,'seed':seed,**{k:config[k] for k in ['permutation_q','permutation_tau','sample_delta','top_fraction','localization_budget']}})
    with np.load(directory/'measurements.npz') as archive:
        temporal=archive['temporal'];support=archive['support'];spatial=archive['spatial']
        windows=archive['windows'].tolist()
    wi=windows.index(96);ti=3 # sample 203, first scheduled decision after onset 192
    for ei,event in enumerate(events):
        if not event['is_fault']:continue
        nodes=event['nodes'];truth=set(nodes)
        clean=next(i for i,e in enumerate(events) if e['base']==event['base'] and e['kind']=='untouched')
        candidates=[g for g in groups if g['window']==96]
        group=max(candidates,key=lambda g:len(truth&set(g['nodes']))/len(truth|set(g['nodes'])))
        gi=group['index'];actual=temporal[ei,ti,wi,nodes];normal=temporal[clean,ti,wi,nodes]
        row={'configuration':name,'dataset':'synthetic' if name.startswith('synthetic') else name,
             'seed':seed,'event':ei,'base':event['base'],'kind':event['kind'],
             'window':96,'decision':203,'illustrative_best_overlap_group':gi,
             'spatial_actual_change':float(spatial[ei,ti,gi,1]),
             'spatial_paired_level_difference':float(spatial[ei,ti,gi,0]-spatial[clean,ti,gi,0]),
             'spatial_observed_pair_available':bool(np.isfinite(spatial[ei,ti,gi,:2]).all())}
        for fi,label in [(0,'permutation'),(1,'sample'),(2,'acf1'),(6,'variance')]:
            valid=np.isfinite(actual[...,fi,:]).all(-1)
            row[label+'_affected_support']=float(valid.mean())
            row[label+'_actual_change']=mean(actual[...,fi,1])
            row[label+'_direction']=direction(row[label+'_actual_change'])
            paired=np.isfinite(actual[...,fi,0])&np.isfinite(normal[...,fi,0])
            row[label+'_paired_level_difference']=mean((actual[...,fi,0]-normal[...,fi,0])[paired])
        row['spatial_direction']=direction(mean([row['spatial_actual_change']]))
        s=support[ei,ti,wi,nodes,:,0]
        row.update({'affected_PE_templates':mean(s[...,0]),'affected_SE_templates':mean(s[...,1]),
                    'affected_A':mean(s[...,2]),'affected_B':mean(s[...,3]),
                    'affected_tied_fraction':mean(s[...,5]),'affected_censored_fraction':mean(s[...,6]),
                    'affected_flat_fraction':mean(s[...,7])})
        rows.append(row)
    with np.load(directory/'predictions.npz') as archive:
        scores=archive['scores'];methods=archive['methods'].tolist()
    for ref in ['bootstrap','diffusion']:
        a=scores[:,:,methods.index(ref+'/B')];b=scores[:,:,methods.index(ref+'/BST')]
        valid=np.isfinite(a)&np.isfinite(b)
        dominance.append({'configuration':name,'seed':seed,'reference':ref,
            'jointly_valid_scheduled_units':int(valid.sum()),
            'equal_maximum_fraction':float(np.isclose(a[valid],b[valid],rtol=1e-6,atol=1e-6).mean()),
            'BST_larger_fraction':float((b[valid]>a[valid]+1e-6).mean()),
            'interpretation':'same raw scan maximum need not imply equal information or practical equivalence'})
    print(directory.name,flush=True)
pd.DataFrame(rows).to_csv(out/'affected-support-direction.csv.gz',index=False,compression='gzip')
write_json(out/'maximum-dominance.json',dominance);write_json(out/'selected-parameters.json',selection)
write_json(out/'observability-definition.json',{'role':'post-hoc descriptive strata; no tuning',
    'support':'fraction of affected sensor-channel pairs with both measured endpoints at W96 decision 203, before reference support',
    'direction':'mean finite measured lagged change on affected sensors, not deviation from a reference; spatial uses best-overlap candidate only for evaluation',
    'paired_level_difference':'fault-injected level minus unchanged same-background level on common measured support',
    'missing_labels':'unsupported events remain in operational denominators'})
