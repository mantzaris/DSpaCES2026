"""Cross-type alarms with the already frozen type-specific calibrators.

This is a diagnostic transfer population, not a changed primary endpoint or a
newly tuned classifier. It exposes sensor/association ambiguity in joint use.
"""
from pathlib import Path
import json,sys
import numpy as np
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import json_save
from iot_repair.calibration import null_tail_value
from iot_repair.metrics import candidate_score,scores_for,selected_pool,FLOOR
reports={}
for name in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    folder=ROOT/'results/study'/name;params=json.loads((folder/'frozen.json').read_text());cal=json.loads((folder/'calibration_complete.json').read_text())
    cases=[json.loads(p.read_text()) for p in sorted((folder/'test').glob('test_*.json'))]
    rows=[]
    for case in cases:
        if case['track']!='clean' and case['fault']['status']!='injected':continue
        record=dict(case=case['id'],true_track=case['track'],block=case['block'],accepted={},window_alerts={})
        for kind in ['observation','association']:
            scores,support=scores_for(case,'proposed',kind,params);selected=[]
            for row in case['records']:
                if row['kind']!=kind or row['support_count']<2:continue
                refs=cal['candidate_null_references'][kind+'/'+str(row['support_count'])]
                p=float(null_tail_value(refs,row['score'])) if refs else 1.
                if p<=.05:selected.append(dict(index=row['index'],truth=bool(case[kind+'_truth'][row['index']]),tail=p))
            record['accepted'][kind]=selected
            record['window_alerts'][kind]=float(null_tail_value(cal['null_references'][kind+'/proposed'],float(scores.max())))<=.05
        rows.append(record)
    table={}
    for track in ['clean','observation','association']:
        selected=[r for r in rows if r['true_track']==track]
        table[track]=dict(windows=len(selected),source_blocks=len({r['block'] for r in selected}),
            any_observation_candidate_accepted=float(np.mean([bool(r['accepted']['observation']) for r in selected])),
            any_association_candidate_accepted=float(np.mean([bool(r['accepted']['association']) for r in selected])),
            both_candidate_types_accepted=float(np.mean([bool(r['accepted']['observation']) and bool(r['accepted']['association']) for r in selected])),
            observation_window_alert=float(np.mean([r['window_alerts']['observation'] for r in selected])),
            association_window_alert=float(np.mean([r['window_alerts']['association'] for r in selected])))
    joint={}
    for kind in ['observation','association']:
        truth=[];score=[];probs=[]
        mapping=cal['probability'][kind+'/proposed']
        for case in cases:
            if case['track']!='clean' and case['fault']['status']!='injected':continue
            s,support=scores_for(case,'proposed',kind,params);mask=(s>FLOOR)&selected_pool(case,kind,len(s))
            truth.extend(np.array(case[kind+'_truth'])[mask]);score.extend(s[mask]);probs.extend(expit(mapping['coefficient']*(s[mask]-mapping['mean'])/mapping['scale']+mapping['intercept']))
        y=np.array(truth);s=np.array(score);q=np.array(probs);k=int(np.ceil(.1*len(y)))
        joint[kind]=dict(candidates=len(y),prevalence=float(y.mean()),brier=float(np.mean((q-y)**2)),
            top10percent_precision=float(np.mean(y[np.argsort(-s,kind='stable')[:k]])),calibration_prevalence=mapping['prevalence'])
    reports[name]=dict(alarm_table=table,joint_candidate_population=joint,case_decisions=rows)
json_save(ROOT/'results/cross_type_analysis.json',dict(results=reports,
    scope='Descriptive diagnostic using all unmodified, observation-fault and association-fault windows. Type-specific calibrators are unchanged. Candidate acceptance is not a familywise window guarantee. No exclusive type decision or new hyperparameter is fitted.'))
print({name:d['alarm_table']['observation'] for name,d in reports.items()})
