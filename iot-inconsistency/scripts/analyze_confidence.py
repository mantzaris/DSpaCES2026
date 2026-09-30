"""Paired secondary endpoint intervals on saved, common candidate populations."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.metrics import task_cases,scores_for,selected_pool,FLOOR,paired_ap_interval
from iot_repair.experiment import json_save

config=json.loads((ROOT/'configs/study.json').read_text());reports={}
main=json.loads((ROOT/'results/analysis.json').read_text())
for dataset in config['datasets']:
    directory=ROOT/'results/study'/dataset
    params=json.loads((directory/'frozen.json').read_text());cal=json.loads((directory/'calibration_complete.json').read_text())
    cases=[json.loads(p.read_text()) for p in sorted((directory/'test').glob('test_*.json'))]
    reports[dataset]={}
    for kind in ('observation','association'):
        track=main[dataset]['tracks'][kind];paired={}
        primary=track['methods']['proposed']['decisions']
        for method,summary in track['methods'].items():
            if method=='proposed':continue
            paired[method]=paired_ap_interval([r['y'] for r in primary],[r['score'] for r in primary],
                [r['score'] for r in summary['decisions']],[r['block'] for r in primary],config['bootstrap_replicates'])
        baseline=track['primary_comparator'];blocks=[];truth=[];left=[];right=[];ql=[];qr=[]
        for case in task_cases(cases,kind):
            a,_=scores_for(case,'proposed',kind,params);b,_=scores_for(case,baseline,kind,params)
            mask=selected_pool(case,kind,len(a))&(a>FLOOR)&(b>FLOOR)
            truth.extend(np.asarray(case[kind+'_truth'])[mask]);left.extend(a[mask]);right.extend(b[mask])
            blocks.extend([case['block']]*int(mask.sum()))
            for method,scores,container in [('proposed',a,ql),(baseline,b,qr)]:
                p=cal['probability'][kind+'/'+method]
                container.extend(expit(p['coefficient']*(scores[mask]-p['mean'])/p['scale']+p['intercept']))
        y=np.asarray(truth);a=np.asarray(left);b=np.asarray(right);ql=np.asarray(ql);qr=np.asarray(qr);blocks=np.asarray(blocks)
        null_probability=cal['probability'][kind+'/proposed']['prevalence']
        def statistics(indices):
            yt=y[indices];aa=a[indices];bb=b[indices]
            result={'brier_main_minus_comparator':float(np.mean((ql[indices]-yt)**2-(qr[indices]-yt)**2)),
                    'brier_main_minus_constant':float(np.mean((ql[indices]-yt)**2-(null_probability-yt)**2))}
            for coverage in config['coverage_targets']:
                k=max(1,int(np.ceil(len(indices)*coverage)))
                pl=float(np.mean(yt[np.argsort(-aa,kind='stable')[:k]]));pr=float(np.mean(yt[np.argsort(-bb,kind='stable')[:k]]))
                result['precision_difference_at_'+str(coverage)]=pl-pr
            return result
        actual=statistics(np.arange(len(y)));samples={k:[] for k in actual};rng=np.random.default_rng(9026);units=np.unique(blocks)
        for repeat in range(config['bootstrap_replicates']):
            index=np.concatenate([np.flatnonzero(blocks==unit) for unit in rng.choice(units,len(units),replace=True)])
            for key,value in statistics(index).items():samples[key].append(value)
        intervals={key:dict(difference=value,interval=np.quantile(samples[key],[.025,.975]).tolist()) for key,value in actual.items()}
        reports[dataset][kind]=dict(comparator=baseline,common_eligible_candidates=len(y),source_blocks=len(units),
            prevalence=float(y.mean()),constant_probability=null_probability,paired_secondary_endpoints=intervals,
            paired_window_ap_by_comparator=paired)
json_save(ROOT/'results/confidence_comparisons.json',dict(results=reports,bootstrap_replicates=config['bootstrap_replicates'],
    scope='Secondary descriptive comparisons. Common screened eligible candidates. Whole-block paired bootstrap. Intervals are not adjusted for multiple comparisons.'))
print({name:d['observation']['paired_secondary_endpoints'] for name,d in reports.items()})
