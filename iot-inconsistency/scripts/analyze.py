"""Saved-result analysis. This script performs no model fitting on test data."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.special import expit
from scipy.stats import spearmanr
from sklearn.metrics import brier_score_loss,log_loss,precision_recall_curve
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.metrics import *
from iot_repair.experiment import json_save
from iot_repair.calibration import null_tail_value
config=json.loads((ROOT/'configs/study.json').read_text());reports={}
for dataset in config['datasets']:
    directory=ROOT/'results/study'/dataset
    if not (directory/'test/complete.json').exists():continue
    params=json.loads((directory/'frozen.json').read_text());cal=json.loads((directory/'calibration_complete.json').read_text())
    cases=[json.loads(p.read_text()) for p in sorted((directory/'test').glob('test_*.json'))]
    report=dict(dataset=dataset,selection=params,tracks={},calibration_blocks=dict(null=cal['null_blocks'],probability=cal['probability_blocks']))
    for kind in ('observation','association'):
        methods=['proposed','fixed_penalties','R_only','no_uncertainty','no_cost','supervised_terms']+(['gdn','backbone','diffad']+list(params['pca'].values()) if kind=='observation' else ['edge_residual'])
        result={}
        for method in methods:
            key=kind+'/'+method
            if key not in cal['null_references']:continue
            result[method]=summarize(cases,method,kind,params,reference=cal['null_references'][key])
            decisions=result[method]['decisions'];y=[r['y'] for r in decisions];z=[r['score'] for r in decisions]
            precision,recall,thresholds=precision_recall_curve(y,z)
            result[method]['pr_curve']=dict(precision=precision.tolist(),recall=recall.tolist(),thresholds=thresholds.tolist())
            if key in cal['probability']:
                calibration=cal['probability'][key];truth=[];probs=[];unknown=[]
                for case in task_cases(cases,kind):
                    scores,support=scores_for(case,method,kind,params);eligible=(scores>FLOOR)&selected_pool(case,kind,len(scores))
                    q=expit(calibration['coefficient']*(scores[eligible]-calibration['mean'])/calibration['scale']+calibration['intercept'])
                    truth.extend(np.array(case[kind+'_truth'])[eligible].astype(int));probs.extend(q)
                    unknown.extend([case['fault']['family'] in config['observation_families_heldout']]*int(eligible.sum()))
                truth=np.array(truth);probs=np.array(probs);bins=np.linspace(0,1,6);reliability=[]
                for first,last in zip(bins[:-1],bins[1:]):
                    mask=(probs>=first)&(probs<last if last<1 else probs<=last)
                    reliability.append(dict(lower=float(first),upper=float(last),count=int(mask.sum()),mean_probability=float(probs[mask].mean()) if mask.any() else None,fault_frequency=float(truth[mask].mean()) if mask.any() else None))
                score=dict(units=len(truth),prevalence=float(truth.mean()),brier=float(brier_score_loss(truth,probs)),log_loss=float(log_loss(truth,np.clip(probs,1e-9,1-1e-9),labels=[0,1])),reliability=reliability,
                    calibration_prevalence=calibration['prevalence'])
                unknown=np.array(unknown)
                if unknown.any():score['unknown_fault_brier']=float(brier_score_loss(truth[unknown],probs[unknown]));score['unknown_fault_units']=int(unknown.sum())
                result[method]['probability_evaluation']=score
        strongest=params['strongest_baseline'] if kind=='observation' else 'edge_residual'
        left=result['proposed']['decisions'];right=result[strongest]['decisions']
        report['tracks'][kind]=dict(methods=result,primary_comparator=strongest,
            paired_difference=paired_ap_interval([r['y'] for r in left],[r['score'] for r in left],[r['score'] for r in right],[r['block'] for r in left],config['bootstrap_replicates']))
        # Conditional fault-family comparisons retain paired unmodified windows.
        families=sorted({case['fault']['family'] for case in cases if case['track']==kind})
        by_family={}
        for family in families:
            positives=[case for case in cases if case['track']==kind and case['fault']['family']==family and case['fault']['status']=='injected']
            base_ids={case['base_id'] for case in positives};subset=positives+[case for case in cases if case['track']=='clean' and case['base_id'] in base_ids]
            if subset:by_family[family]={method:{k:v for k,v in summarize(subset,method,kind,params).items() if k in ('window_ap','top1','screening_recall','windows','source_blocks')} for method in result}
        report['tracks'][kind]['by_family']=by_family
        strata={}
        for stratum in ['known_families','heldout_families','short_interval','long_interval','heldout_regime']:
            positive=[]
            for case in cases:
                if case['track']!=kind or case['fault']['status']!='injected':continue
                unknown=case['fault']['family'] in config['observation_families_heldout']
                heldout_regime=dataset.startswith('synthetic') and int(case['block'].split('_')[-1])>=6 and case['start']>=448
                include=(stratum=='known_families' and not unknown) or (stratum=='heldout_families' and unknown) or (stratum=='short_interval' and case['fault'].get('duration')==4) or (stratum=='long_interval' and case['fault'].get('duration')==16) or (stratum=='heldout_regime' and heldout_regime)
                if include:positive.append(case)
            ids={c['base_id'] for c in positive};subset=positive+[c for c in cases if c['track']=='clean' and c['base_id'] in ids]
            if not positive:continue
            primary=summarize(subset,'proposed',kind,params);comparison=summarize(subset,strongest,kind,params)
            left=primary['decisions'];right=comparison['decisions']
            strata[stratum]=dict(proposed=primary,comparator=comparison,paired_difference=paired_ap_interval([r['y'] for r in left],[r['score'] for r in left],[r['score'] for r in right],[r['block'] for r in left],config['bootstrap_replicates']))
        report['tracks'][kind]['predefined_strata']=strata
        for method in ['fixed_penalties','R_only','no_uncertainty','no_cost','supervised_terms']:
            left=result['proposed']['decisions'];right=result[method]['decisions']
            result[method]['paired_main_minus_variant']=paired_ap_interval([r['y'] for r in left],[r['score'] for r in left],[r['score'] for r in right],[r['block'] for r in left],config['bootstrap_replicates'])

    allrows=[r for case in cases for r in case['records']];terms={}
    for kind in ('observation','association'):
        rows=[r for r in allrows if r['kind']==kind]
        terms[kind]={str(label):{key:dict(median=float(np.median([r[key] for r in rows if r['truth']==label])),quantiles=np.quantile([r[key] for r in rows if r['truth']==label],[.1,.9]).tolist()) for key in ('mean_gain','model_instability','edit_cost','monte_carlo_standard_error')} for label in [False,True] if any(r['truth']==label for r in rows)}
        degree=[];initial=[];gain=[];durations=[]
        for case in cases:
            raw=np.load(directory/'test'/case['raw_artifact'])
            for row in case['records']:
                if row['kind']!=kind:continue
                channel=row['index'] if kind=='observation' else case['graph']['edges'][row['index']]['source']
                degree.append(sum(e['source']==channel or e['target']==channel for e in case['graph']['edges']))
                initial.append(float(np.nanmean(raw['loss_before'][row['raw_index']])));gain.append(row['mean_gain'])
        terms[kind]['gain_initial_loss_spearman']=float(spearmanr(gain,initial).correlation)
        terms[kind]['gain_degree_spearman']=float(spearmanr(gain,degree).correlation)
    report['score_terms']=terms
    report['costs']=dict(inference_seconds_per_window=[sum(r['elapsed_seconds_per_candidate'] for r in case['records']) for case in cases],
        gpu_peak_bytes=max(case['gpu_peak_bytes'] for case in cases),baseline_timing=json.loads((directory/'test/baseline_timing.json').read_text()),
        training=json.loads((ROOT/'results/models'/dataset/'training.json').read_text()))
    report['scope']='Controlled injected faults. Native SKAB process labels are evaluated separately. One three-member ensemble.'
    json_save(directory/'analysis.json',report);reports[dataset]=report
json_save(ROOT/'results/analysis.json',reports)
print({name:{kind:(track['methods']['proposed']['window_ap'],track['primary_comparator'],track['methods'][track['primary_comparator']]['window_ap']) for kind,track in report['tracks'].items()} for name,report in reports.items()})
