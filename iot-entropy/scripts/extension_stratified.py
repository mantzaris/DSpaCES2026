"""Paired descriptive mechanism/direction/support strata; no threshold fitting."""
from pathlib import Path
import numpy as np
import pandas as pd
from iot_entropy.evaluation import bootstrap_mean

root=Path(__file__).resolve().parents[1];out=root/'results/extension-v2'
events=pd.read_csv(out/'event-metrics.csv.gz');events=events[events.is_fault].copy()
support=pd.read_csv(out/'affected-support-direction.csv.gz')
keys=['configuration','seed','event']
columns=keys+[c for c in support if c.endswith('_direction') or c.endswith('_affected_support')]
events=events.merge(support[columns],on=keys,validate='many_to_one')
for feature in ['permutation','sample','acf1','variance']:
    events[feature+'_support_stratum']=pd.cut(events[feature+'_affected_support'],[-.001,0,.5,.999,1.],
        labels=['none','0-50%','50-99%','all'])
strata=['kind','duration','severity','spatial_direction','permutation_direction','sample_direction',
        'permutation_support_stratum','sample_support_stratum','acf1_support_stratum']
contrasts=[]
for ref in ['bootstrap','diffusion']:
    contrasts += [(ref+'/'+a,ref+'/'+b) for a,b in [('S','SB'),('T','TB'),('ST','S'),('ST','T'),('BST','B')]]
contrasts += [('diffusion/'+f,'bootstrap/'+f) for f in ['S','T','B','BST']]
rows=[];absolute=[]
for dataset,frame in events.groupby('dataset'):
    for key in strata:
        for (method,value),g in frame.groupby(['method',key],observed=True):
            absolute.append({'dataset':dataset,'method':method,'stratum':key,'value':str(value),
                'event_seed_pairs':len(g),'blocks':g.block.nunique(),'recall':g.tp.mean(),
                'iou':g.iou.mean(),'availability':g.availability.mean()})
    for a,b in contrasts:
        left=frame[frame.method==a];right=frame[frame.method==b]
        merge=left.merge(right,on=keys+['block'],suffixes=('_a','_b'),validate='one_to_one')
        for key in strata:
            for value,g in merge.groupby(key+'_a',observed=True):
                for metric in ['tp','iou']:
                    differences=(g[metric+'_a']-g[metric+'_b']).groupby(g.block).mean().to_numpy()
                    stats=bootstrap_mean(differences)
                    if len(differences)<2:stats.update(low=None,high=None)
                    rows.append({'dataset':dataset,'a':a,'b':b,'stratum':key,'value':str(value),
                        'metric':metric,'event_seed_pairs':len(g),**stats,
                        'role':'exploratory unadjusted block interval; post-hoc measured direction/support'})
pd.DataFrame(rows).to_csv(out/'stratified-paired.csv.gz',index=False,compression='gzip')
pd.DataFrame(absolute).to_csv(out/'observability-strata.csv.gz',index=False,compression='gzip')
print({'paired_rows':len(rows),'absolute_rows':len(absolute)})
