"""Deterministic tables from saved scores; no fitted threshold uses test labels."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .calibration import rank_pvalues
from .evaluation import alert_intervals, match_events, bootstrap_mean, event_pr_curve
from .extension_scoring import primary_localization, MAIN
from .localization import set_metrics
from .utils import write_json, digest


def read_json(path: Path):
    if path.exists(): return json.loads(path.read_text())
    with gzip.open(str(path)+'.gz','rt') as stream:return json.load(stream)


def archive_json(path: Path) -> dict:
    payload=path.read_bytes()
    target=Path(str(path)+'.gz')
    target.write_bytes(gzip.compress(payload,compresslevel=9,mtime=0))
    return {'path':str(path),'sha256':digest(path),'compressed_bytes':target.stat().st_size}


def event_rows(directory: Path) -> tuple[list,list,list,list]:
    config=read_json(directory/'configuration.json'); events=read_json(directory/'events.json')
    pred=np.load(directory/'predictions.npz'); cal=np.load(directory/'calibration.npz')
    status=read_json(directory/'status.json')
    dataset=status['dataset']; seed=status['seed']; times=pred['times'];methods=pred['methods'].tolist()
    interval=120 if dataset=='intel' else 300
    rows=[];curves=[];operating=[];diagnostics=[]
    for mi,method in enumerate(methods):
        # Reconstruct exact rational ranks, avoiding float32 p-value boundary rounding.
        pvalues=rank_pvalues(cal['scores'][:,mi],pred['scores'][:,:,mi])
        np.testing.assert_allclose(pvalues,pred['pvalues'][:,:,mi],atol=6e-8,rtol=0)
        localization=primary_localization(method)
        alpha=config['primary_alpha']
        for ei,event in enumerate(events):
            alerts=alert_intervals(times,pvalues[ei]<=alpha,12)
            truth=[(event['onset'],event['onset']+event['duration']-1)] if event['is_fault'] else []
            matched=match_events(alerts,truth)
            loc=[{k:0. for k in ['precision','recall','f1','iou']} for _ in range(3)]
            if matched['tp']:
                first=alerts[matched['matches'][0][0]][0]
                tick=int(np.flatnonzero(times==first)[0])
                loc=[set_metrics(pred['rankings'][ei,tick,mi,j,:config['localization_budget']].tolist(),event['nodes']) for j in range(3)]
            event_ticks=(times>=event['onset'])&(times<event['onset']+event['duration'])
            row={'dataset':'synthetic' if dataset.startswith('synthetic') else dataset,
                'configuration':dataset,'seed':seed,'method':method,'event':ei,'base':event['base'],
                'block':f'{dataset}/{event["base"]}','kind':event['kind'],'is_fault':event['is_fault'],
                'severity':event['severity'],'duration':event['duration'],'size':len(event['nodes']),
                'partly_disconnected':event['partly_disconnected'],'tp':matched['tp'],'fp':matched['fp'],'fn':matched['fn'],
                'delay_seconds':matched['delays'][0]*interval if matched['tp'] else np.nan,
                'scheduled_exceedance':float(np.mean(pvalues[ei]<=alpha)),
                'availability':float(np.mean(pred['availability'][ei,:,mi])),
                'event_has_valid_scan':bool(np.any(pred['availability'][ei,event_ticks,mi]>0)),
                'missing_fraction':float(pred['quality'][ei,event_ticks,0].mean()),
                'flat_fraction':float(pred['quality'][ei,event_ticks,1].mean()),
                'oracle_iou':event['oracle_group_iou'],
                'monitoring_seconds':len(times)*12*interval,
                'localization_budget':config['localization_budget'],
                **loc[localization]}
            for j,name in enumerate(['participation','direct','combined']):
                row[name+'_iou']=loc[j]['iou']
            rows.append(row)
        alphas=np.r_[0,np.arange(1,len(cal['scores'])+2)/(len(cal['scores'])+1)]
        curve=event_pr_curve([{'times':times,'pvalues':pvalues[i],
            'events':[(e['onset'],e['onset']+e['duration']-1)] if e['is_fault'] else []}
            for i,e in enumerate(events)],alphas,12)
        curves.append({'dataset':dataset,'seed':seed,'method':method,**curve})
        controls=np.asarray([i for i,e in enumerate(events) if e['kind']=='untouched'])
        for cap in config['retrospective_rate_caps']:
            achieved=np.asarray([np.mean(pvalues[controls]<=a) for a in alphas])
            permissible=np.flatnonzero(achieved<=cap)
            at=int(permissible[-1]); alpha=float(alphas[at]); tp=fp=fn=0
            for ei,e in enumerate(events):
                alarms=alert_intervals(times,pvalues[ei]<=alpha,12)
                target=[(e['onset'],e['onset']+e['duration']-1)] if e['is_fault'] else []
                match=match_events(alarms,target);tp+=match['tp'];fp+=match['fp'];fn+=match['fn']
            operating.append({'configuration':dataset,'seed':seed,'method':method,'cap':cap,
                'selected_alpha':alpha,'achieved_background':achieved[at],'recall':tp/max(tp+fn,1),
                'precision':tp/max(tp+fp,1),'analysis':'retrospective rate cap using evaluated controls; descriptive only'})
        c=cal['scores'][:,mi];finite=np.isfinite(c)
        valid_pairs=finite[:-1]&finite[1:]
        lag=np.corrcoef(c[:-1][valid_pairs],c[1:][valid_pairs])[0,1] if valid_pairs.sum()>2 else np.nan
        diagnostics.append({'configuration':dataset,'seed':seed,'method':method,'n':len(c),
            'minimum_p':1/(len(c)+1),'all_abstained_units':int((~finite).sum()),
            'calibration_availability':float(cal['availability'][:,mi].mean()),'lag1':lag})
    return rows,curves,operating,diagnostics


def aggregate(frame: pd.DataFrame, curves: list) -> list:
    summaries=[]
    for (dataset,method),group in frame.groupby(['dataset','method']):
        faults=group[group.is_fault]; controls=group[group.kind=='untouched']; transitions=group[group.kind=='transition']
        blocks=faults.groupby('block')[['tp','iou','f1','precision','recall','availability']].mean()
        tp=group.tp.sum();fp=group.fp.sum()
        row={'dataset':dataset,'method':method,'fault_realizations':len(faults[['configuration','event']].drop_duplicates()),
            'event_seed_pairs':len(faults),'blocks':len(blocks),'seeds':sorted(faults.seed.unique().tolist()),
            'event_precision':float(tp/max(tp+fp,1)),'recall':bootstrap_mean(blocks.tp.to_numpy()),
            'iou':bootstrap_mean(blocks.iou.to_numpy()),'f1':bootstrap_mean(blocks.f1.to_numpy()),
            'localization_precision':bootstrap_mean(blocks.precision.to_numpy()),
            'localization_recall':bootstrap_mean(blocks.recall.to_numpy()),
            'detected_iou':float(faults[faults.tp==1].iou.mean()),
            'detected_f1':float(faults[faults.tp==1].f1.mean()),
            'availability':bootstrap_mean(blocks.availability.to_numpy()),
            'missed_event_seed_pairs':int(faults.fn.sum()),
            'background_exceedance':float(controls.scheduled_exceedance.mean()),
            'transition_exceedance':float(transitions.scheduled_exceedance.mean()),
            'background_alerts_per_day':float(controls.fp.sum()/controls.monitoring_seconds.sum()*86400),
            'median_delay_seconds':float(faults.delay_seconds.median()),
            'oracle_iou':float(faults.oracle_iou.mean()),
            'observable_event_fraction':float(faults.event_has_valid_scan.mean()),
            'recall_given_any_valid_scan':float(faults[faults.event_has_valid_scan].tp.mean()),
            'event_auprc':float(np.mean([c['event_auprc_envelope'] for c in curves if c['method']==method and
                ('synthetic' if c['dataset'].startswith('synthetic') else c['dataset'])==dataset]))}
        for loc in ['participation','direct','combined']:
            row[loc+'_iou']=float(faults[loc+'_iou'].mean())
        summaries.append(row)
    return summaries


def paired(frame: pd.DataFrame) -> list:
    faults=frame[frame.is_fault];rows=[]
    comparisons=[]
    for reference in ['bootstrap','diffusion']:
        for a,b in [('S','SB'),('PE','TB'),('SE','TB'),('T','TB'),('ST','S'),('ST','T'),('BST','B')]:
            for support in ['', 'common/']:
                comparisons.append((reference+'/'+support+a,reference+'/'+support+b))
    for family in MAIN:comparisons.append(('diffusion/'+family,'bootstrap/'+family))
    for dataset,group in faults.groupby('dataset'):
        for a,b in comparisons:
            left=group[group.method==a];right=group[group.method==b]
            merge=left.merge(right,on=['configuration','seed','event','block'],suffixes=('_a','_b'),validate='one_to_one')
            if not len(merge):continue
            for metric in ['tp','iou','f1']:
                merge['difference']=merge[metric+'_a']-merge[metric+'_b']
                block=merge.groupby('block').difference.mean().to_numpy()
                rows.append({'dataset':dataset,'a':a,'b':b,'metric':metric,**bootstrap_mean(block),
                    'unit':'whole recording/simulation block; all injections and seeds retained',
                    'multiplicity':'exploratory intervals without multiple-comparison adjustment'})
    return rows


def build(root: Path) -> dict:
    directory=root/'experiments/extension-v2';out=root/'results/extension-v2';out.mkdir(parents=True,exist_ok=True)
    rows=[];curves=[];operating=[];calibration=[];support=[];fidelity=[];multi=[];cost=[];lineage=[]
    completed=sorted(directory.glob('*/status.json'))
    for status_path in completed:
        path=status_path.parent;status=read_json(status_path)
        a,b,c,d=event_rows(path);rows+=a;curves+=b;operating+=c;calibration+=d
        for filename,target in [('support.json',support),('fidelity.json',fidelity),('multiscale-development.json',multi)]:
            target.extend([{**row,'configuration':status['dataset'],'seed':status['seed']} for row in read_json(path/filename)])
        timings=read_json(path/'timings.json')
        ticks=[t for t in timings if t.get('stage')=='complete_test_tick']
        generation=[t['generation_seconds'] for t in timings if 'generation_seconds' in t]
        cost.append({'configuration':status['dataset'],'seed':status['seed'],'total_seconds':status['elapsed_seconds'],
            'peak_gpu_bytes':status['peak_gpu_bytes'],'shared_tick_median_seconds':np.median([t['seconds'] for t in ticks]),
            'amortized_episode_tick_seconds':np.median([t['seconds']/t['events'] for t in ticks]),
            'reference_generation_median_seconds':np.median(generation)})
        lineage.append({'configuration':status['dataset'],'seed':status['seed'],**read_json(path/'data-lineage.json')})
        print(path.name,flush=True)
    if not rows:raise RuntimeError('No accepted completed extension runs')
    frame=pd.DataFrame(rows)
    frame.to_csv(out/'event-metrics.csv.gz',index=False,compression='gzip')
    summary=aggregate(frame,curves); differences=paired(frame)
    write_json(out/'summary.json',summary);write_json(out/'paired.json',differences)
    write_json(out/'event-pr-curves.json',curves)
    for filename,content in [('retrospective-operating-points.csv',operating),('calibration.csv',calibration),
        ('support.csv.gz',support),('reference-fidelity.csv',fidelity),('multiscale.csv',multi),('cost.csv',cost)]:
        pd.DataFrame(content).to_csv(out/filename,index=False,compression='gzip' if filename.endswith('.gz') else None)
    write_json(out/'data-lineage.json',lineage)
    strata=[]
    fault=frame[frame.is_fault].copy()
    fault['missingness_stratum']=pd.cut(fault.missing_fraction,[-.001,.01,.1,.3,1.],labels=['<=1%','1-10%','10-30%','>30%'])
    for key in ['configuration','kind','severity','duration','size','partly_disconnected','missingness_stratum']:
        for (dataset,method,value),group in fault.groupby(['dataset','method',key],observed=True):
            strata.append({'dataset':dataset,'method':method,'stratum':key,'value':str(value),
                'trials':len(group),'recall':group.tp.mean(),'iou':group.iou.mean(),'availability':group.availability.mean(),
                'median_delay_seconds':group.delay_seconds.median()})
    pd.DataFrame(strata).to_csv(out/'strata.csv.gz',index=False,compression='gzip')
    report={'completed_runs':[p.parent.name for p in completed],'expected_runs':15,'complete':len(completed)==15,
            'independent_primary_datasets':3,'recording_or_simulation_blocks':20,
            'fault_realizations':360,'source_namespace':'experiments/extension-v2',
            'original_namespace':'experiments/full','original_revision':read_json(directory/'original-study.json')['original_revision'],
            'inference':'exploratory paired block bootstrap; no equivalence test; reused Intel background',
            'common_support':'Common feature group/window/channel support within each reference; operational reference contrasts retain model-specific support.'}
    write_json(out/'report-manifest.json',report)
    return report
