"""Auditable development sensitivity and targeted stress summaries."""
from pathlib import Path
import itertools,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import json_save
from iot_repair.calibration import null_tail_value
config=json.loads((ROOT/'configs/study.json').read_text());reports={}
for dataset in config['datasets']:
    study=ROOT/'results/study'/dataset;params=json.loads((study/'frozen.json').read_text());cal=json.loads((study/'calibration_complete.json').read_text())
    sensitivities=[]
    for path in sorted((ROOT/'results/sensitivity'/dataset).glob('case*.json')):
        d=json.loads(path.read_text());rows=d['records'];observations=[r for r in rows if r['kind']=='observation']
        key='score' if d['E']>1 else 'mean_gain';best=max(observations,key=lambda r:r[key]) if observations else None
        if d['E']==1:
            index=int(path.stem.split('_')[0][4:]);parent=json.loads((path.parent/f'case{index}_E3_M8_L8_amp1.json').read_text())
            sensitivities.append(dict(path=str(path.relative_to(ROOT)),E=1,M=8,L=8,case=index,amp=True,
                seconds=None,peak_bytes=None,top1=bool(best and best['index'] in parent['fault']['channels']),
                median_monte_carlo_se=None,median_instability=None,scope=d['scope']))
            continue
        sensitivities.append(dict(path=str(path.relative_to(ROOT)),E=d['E'],M=d['M'],L=d['L'],case=d['case'],amp=d['neural_autocast'],
            seconds=d['seconds'],peak_bytes=d['peak_bytes'],top1=bool(best and best['index'] in d['fault']['channels']),
            median_monte_carlo_se=float(np.median([r['monte_carlo_standard_error'] for r in rows if r.get('monte_carlo_standard_error') is not None])),
            median_instability=float(np.median([r['model_instability'] for r in rows if r.get('model_instability') is not None])) if d['E']>1 else None))
    reversal=None
    for path in sorted((study/'development').glob('development_*.json')):
        if reversal:break
        case=json.loads(path.read_text());rows=[r for r in case['records'] if r['kind']=='observation']
        for a,b in itertools.combinations(rows,2):
            gain=a['mean_gain']-b['mean_gain'];spread=a['model_instability']-b['model_instability'];cost=a['edit_cost']-b['edit_cost']
            if gain*(gain-spread-.2*cost)<0:
                reversal=dict(path=str(path.relative_to(ROOT)),first=a['index'],second=b['index'],gain_difference=gain,
                    instability_difference=spread,cost_difference=cost,penalty_difference=spread+.2*cost,
                    score_difference_at_zero=gain,score_difference_at_kappa1_lambda02=gain-spread-.2*cost,
                    interpretation='The sign changes exactly where the displayed ranking inequality changes. This is a development example, not a performance estimate.')
                break
    folder=ROOT/'results/robustness'/dataset
    if not (folder/'complete.json').exists():raise RuntimeError('Stress experiments incomplete '+dataset)
    cases=[json.loads(p.read_text()) for p in sorted(folder.glob('*.json')) if p.name not in ['complete.json','analysis.json']]
    if any(r.get('stress_protocol_version')!='scaled-screen-stratified-v3' for r in cases):raise RuntimeError('Stress protocol correction still required '+dataset)
    if any(r.get('low_support_protocol')!='ordinary screening, diagnostic ranking only' for r in cases if r['details']['family']=='single_source_support'):raise RuntimeError('Single-group screening audit still required '+dataset)
    buckets={}
    for case in cases:
        details=case['details'];name=details['family'];level=details.get('fraction',details.get('requested_fraction','all'));key=name+'/'+str(level)
        buckets.setdefault(key,[]).append(case)
    summary={}
    for key,rows in buckets.items():
        supports=[r['support_count'] for case in rows for r in case['records']];scores=[r['score'] for case in rows for r in case['records']]
        summary[key]=dict(cases=len(rows),primary_target_top1=float(np.mean([r['primary_target_top1'] for r in rows])),
            primary_target_screened=float(np.mean([r['primary_target_screened'] for r in rows])),
            single_group_diagnostic_top1=float(np.mean([r.get('single_group_diagnostic_top1',False) for r in rows])),
            baseline_primary_target_top1={method:float(np.mean([r['baseline_primary_target_top1'][method] for r in rows])) for method in rows[0]['baseline_primary_target_top1']},
            median_score=float(np.median(scores)) if scores else None,source_blocks=sorted({r['details']['block'] for r in rows if 'block' in r['details']}),
            support_counts={str(count):supports.count(count) for count in sorted(set(supports))},numeric_abstentions=sum(len(r['abstentions']) for r in rows),
            selected_primary_windows_abstained=sum(not any(r['kind']=='observation' and r['support_count']>=2 for r in c['records']) for c in rows),
            availability_alerts=sum(bool(r['details'].get('availability_alert',False)) for r in rows),
            observation_window_alarms_at_005=sum(r['observation_window_null_tail']<=.05 for r in rows),
            source_files=[str((folder/(r['id']+'.json')).relative_to(ROOT)) for r in rows])
    physical={}
    for name in ['common_mode_identifiability','physical_stale_associations']:
        path=folder/(name+'.json')
        if not path.exists():continue
        case=json.loads(path.read_text());accepted=[]
        for row in case['records']:
            reference=cal['candidate_null_references'][row['kind']+'/'+str(row['support_count'])]
            p=float(null_tail_value(reference,row['score'])) if reference else 1.
            if row['support_count']>=2 and p<=.05:accepted.append(dict(kind=row['kind'],index=row['index'],null_tail=p))
        physical[name]=dict(accepted_hypotheses=accepted,details=case['details'],observation_window_tail=case['observation_window_null_tail'],path=str(path.relative_to(ROOT)))
    json_save(folder/'analysis.json',dict(conditions=summary,physical_controls=physical,
        scope='Twelve evenly spaced reference windows, nested contamination sets, no parameter refitting. Primary target attribution differs from classifying every additional contaminated channel. Small diagnostic study, not independent final-method repetitions.'))
    reports[dataset]=dict(development_grid=params['parameter_grid'],sampling_sensitivity=sensitivities,ranking_reversal=reversal,
        stress_analysis=str((folder/'analysis.json').relative_to(ROOT)),
        term_correlations=json.loads((study/'analysis.json').read_text())['score_terms'])
json_save(ROOT/'results/equation_analysis.json',reports)
print('Summarized equation sensitivity and stress conditions for',len(reports),'configurations')
