"""Native SKAB process events, evaluated independently of injected-fault truth."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.data import skab_records
from iot_repair.preprocessing import transform_measurements
from iot_repair.experiment import load_models,neural_residuals,scaled,json_save
from iot_repair.baselines import PCADetector
from iot_repair.associations import edge_residuals
from iot_repair.pipeline import score_candidates,screen_candidates
from iot_repair.metrics import candidate_score,FLOOR
from iot_repair.calibration import null_tail_value,decide_or_abstain
torch.set_num_threads(4);dataset='skab';out=ROOT/'results/native/skab';out.mkdir(parents=True,exist_ok=True)
study=ROOT/'results/study/skab';params=json.loads((study/'frozen.json').read_text());cal=json.loads((study/'calibration_complete.json').read_text())
scales=json.loads((study/'residual_scales.json').read_text());meta=json.loads((ROOT/'data/processed/skab/metadata.json').read_text())
records,_,_,_,_=skab_records(ROOT);records=records['test']
values=np.stack([transform_measurements(row['x'].T,meta['normalizer']).T for row in records]).astype('float32')
models,graph=load_models(ROOT,dataset,('diffusion','gdn','diffad'))
cache=out/'baselines.npz'
if cache.exists():raw=dict(np.load(cache))
else:
    raw,times=neural_residuals(models,values,graph)
    train=np.load(ROOT/'data/processed/skab/train.npz')['x']
    for name in params['pca'].values():
        lag=int(name.split('_')[1][3:]);rank=int(name.split('_')[2][4:]);raw[name]=PCADetector(rank,lag).fit(train).score(values)
    np.savez_compressed(cache,**raw);json_save(out/'timing.json',times)
scores={name:scaled(a.mean(0) if a.ndim==3 else a,scales[name]) for name,a in raw.items()}
rows=[]
for i,(record,x) in enumerate(zip(records,values)):
    path=out/f'window_{i:04d}.json'
    if path.exists():rows.append(json.loads(path.read_text()));continue
    residual=edge_residuals(x[None],graph)[0];candidates=screen_candidates(scores['gdn'][i],residual,graph)
    findings,terms,abstentions=score_candidates(models['diffusion'],x,graph,candidates,seed=12000000+i*1009)
    process_p={name:float(null_tail_value(cal['null_references']['observation/'+name],np.nanmax(a[i]))) for name,a in scores.items()}
    accepted=[]
    for finding in findings:
        value=candidate_score(finding,'proposed',params['kappa'],params['lambda']);reference=cal['candidate_null_references'][finding['kind']+'/'+str(finding['support_count'])]
        p=float(null_tail_value(reference,value)) if reference else 1.
        decision=decide_or_abstain(process_p['gdn'],p,finding['support_count'])
        finding.update(selected_score=value,candidate_null_tail=p,attribution_accepted=bool(decision['attribution_accepted']))
        accepted.append(bool(decision['attribution_accepted']))
    metadata={k:v for k,v in record.items() if k!='x'}
    result=dict(metadata,baseline_scores={name:float(np.nanmax(a[i])) for name,a in scores.items()},process_p=process_p,
        findings=findings,attribution_accepted=any(accepted),attribution_abstained=not any(accepted),
        observation_fault_truth=None,association_fault_truth=None,label_scope='native process anomaly only')
    np.savez_compressed(path.with_suffix('.npz'),input=x,**terms);json_save(path,result);rows.append(result)
    if i%50==0:print('native SKAB',i,'/',len(records),flush=True)
y=np.array([r['process_label'] for r in rows]);report={}
for method in scores:
    z=np.array([r['baseline_scores'][method] for r in rows]);tails=np.array([r['process_p'][method] for r in rows]);alarms=tails<=.05
    events=[];alarm_events=0;matched_alarm_events=0;false_alarm_events=0;hours=0
    for block in sorted({r['block'] for r in rows}):
        indices=np.array([i for i,r in enumerate(rows) if r['block']==block]);source=pd.read_csv(ROOT/'data/raw/SKAB/data'/block,sep=';')
        timestamps=pd.to_datetime(source.datetime).astype('int64').to_numpy()//10**9;native=source.anomaly.to_numpy().astype(bool)
        onset=int(timestamps[np.flatnonzero(native)[0]]);end=int(timestamps[np.flatnonzero(native)[-1]])
        hits=[rows[i]['timestamp'] for i in indices if alarms[i] and y[i]]
        events.append(dict(experiment=block,onset=onset,end=end,detected=bool(hits),delay_seconds=int(min(hits)-onset) if hits else None))
        hours+=(rows[int(indices[-1])]['timestamp']-rows[int(indices[0])]['timestamp']+32)/3600
        active=alarms[indices];starts=np.flatnonzero(active&~np.r_[False,active[:-1]])
        for start in starts:
            stop=start+1
            while stop<len(indices) and active[stop]:stop+=1
            overlap=bool(y[indices[start:stop]].any());alarm_events+=1;matched_alarm_events+=overlap;false_alarm_events+=not overlap
    delays=[e['delay_seconds'] for e in events if e['detected']]
    report[method]=dict(window_ap=float(average_precision_score(y,z)),prevalence=float(y.mean()),windows=len(y),experiments=len(events),
        nominal_fpr=.05,achieved_fpr=float(alarms[~y].mean()),recall=float(alarms[y].mean()),
        event_recall=float(np.mean([e['detected'] for e in events])),event_precision=matched_alarm_events/alarm_events if alarm_events else None,
        median_detected_event_delay_seconds=float(np.median(delays)) if delays else None,censored_events=sum(not e['detected'] for e in events),
        false_alarm_events_per_hour=false_alarm_events/hours,monitored_hours=hours,events=events,
        process_alerts_retained_during_attribution_abstention=sum(bool(alarms[i]) and r['attribution_abstained'] for i,r in enumerate(rows)))
json_save(out/'analysis.json',dict(label_scope='native process labels only; no sensor or association attribution ground truth',methods=report,
    attribution_abstention_fraction=float(np.mean([r['attribution_abstained'] for r in rows])),decision_stride_samples=32))
json_save(out/'complete.json',dict(windows=len(rows)))
