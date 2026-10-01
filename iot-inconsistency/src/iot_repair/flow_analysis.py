"""Paired source-block endpoints, uncertainty and honest confidence/repair reports."""
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score,precision_recall_curve

from .flow_data import configuration,build_cases,sha256
from .flow_confidence import (load_predictions,predict_probability,rank_pvalues,probability_metrics,
                              repair_rows,risk_point,REPAIR_METHODS)
from .flow_math import repair_outcome
from .experiment import json_save


def weighted_ap_preparation(truth,score):
    y=truth.ravel().astype(float);score=score.ravel();order=np.argsort(-score,kind='stable')
    starts=np.r_[0,1+np.flatnonzero(np.diff(score[order])!=0)]
    def evaluate(case_weight):
        weight=np.repeat(case_weight,truth.shape[1])[order]
        positive=np.add.reduceat(weight*y[order],starts);total=np.add.reduceat(weight,starts)
        total_positive=positive.sum()
        if not total_positive:return np.nan
        precision=np.cumsum(positive)/np.maximum(np.cumsum(total),1e-15)
        return float(precision@positive/total_positive)
    return evaluate


def localization(truth,scores,eligible):
    windows=np.flatnonzero(truth.any(1));top1=[];top3=[];rr=[];unscorable=0
    for window in windows:
        order=np.argsort(-scores[window],kind='stable');targets=np.flatnonzero(truth[window])
        usable=[target for target in targets if eligible[window,target] and scores[window,target]>-1e11]
        if not usable:top1.append(0);top3.append(0);rr.append(0.);unscorable+=1;continue
        rank=min(int(np.flatnonzero(order==target)[0])+1 for target in usable)
        top1.append(rank<=1);top3.append(rank<=3);rr.append(1/rank)
    return dict(fault_windows=len(windows),top1=float(np.mean(top1)),top3=float(np.mean(top3)),
                reciprocal_rank=float(np.mean(rr)),unscorable_fault_windows=unscorable)


def analyze(root):
    root=Path(root);directory=root/'results/graph_flow_v1';config=configuration(root);reports={};bootstrap_inputs={};uncertainty={};uncertainty_samples={}
    for dataset in config['datasets']:
        public,arrays,scores,truth=load_predictions(root,dataset,'test');actual=build_cases(root,dataset,'test')
        calibration=json.loads((directory/dataset/'calibration.json').read_text())['methods'];eligible=np.stack([a['eligible'] for a in arrays])
        blocks=np.array([c['block'] for c in public]);unique=sorted(set(blocks));block_index=np.array([unique.index(b) for b in blocks])
        methods={};window_truth=truth.any(1);curves={};uncertainty[dataset]={};uncertainty_samples[dataset]={}
        for method,score in scores.items():
            probability=predict_probability(score,calibration[method]['probability'])
            clipped=np.clip(probability,1e-15,1-1e-15)
            uncertainty[dataset][method]=dict(brier=((probability-truth)**2).mean(1),
                log_loss=-(truth*np.log(clipped)+(1-truth)*np.log1p(-clipped)).mean(1))
            uncertainty_samples[dataset][method]=dict(brier=[],log_loss=[],repair_risk=[],repair_coverage=[])
            tail=rank_pvalues(score.max(1),calibration[method]['normal_window_maxima'])
            alarms={}
            for alpha in (.01,.05,.1):
                alarm=tail<=alpha
                alarms[str(alpha)]=dict(false_alarms=int(alarm[~window_truth].sum()),normal_windows=int((~window_truth).sum()),
                  false_alarm_rate=float(alarm[~window_truth].mean()),recall=float(alarm[window_truth].mean()),
                  attainable=calibration[method]['minimum_window_p']<=alpha)
            method_report=dict(average_precision=float(average_precision_score(truth.ravel(),score.ravel())),
                window_average_precision=float(average_precision_score(window_truth,score.max(1))),
                localization=localization(truth,score,eligible),confidence=probability_metrics(truth,probability),window_alarms=alarms,
                minimum_window_p=calibration[method]['minimum_window_p'])
            precision,recall,threshold=precision_recall_curve(truth.ravel(),score.ravel())
            curves[method+'_precision']=precision;curves[method+'_recall']=recall
            # Full range candidate-review precision, retaining all planned candidates.
            order=np.argsort(-probability.ravel(),kind='stable');review=[]
            for coverage in [.01,.02,.05,.1,.2,.4,.6,.8,1.]:
                count=max(1,int(np.ceil(truth.size*coverage)));review.append(dict(coverage=count/truth.size,count=count,precision=float(truth.ravel()[order[:count]].mean())))
            method_report['review']=review
            strata={}
            for name,mask in [('known',np.array([c['fault']['family'] in config['faults_development'] or c['track']=='clean' for c in public])),
                              ('heldout',np.array([c['fault']['family'] in config['faults_heldout'] or c['track']=='clean' for c in public])),
                              ('heldout_regime',np.array([c['heldout_regime'] for c in public]))]:
                if mask.any() and truth[mask].any():strata[name]=dict(cases=int(mask.sum()),average_precision=float(average_precision_score(truth[mask].ravel(),score[mask].ravel())))
            method_report['strata']=strata
            if method in REPAIR_METHODS:
                rows=repair_rows(actual,arrays,score,probability,method,config);policy=calibration[method]['repair_policy']
                point=risk_point(rows,policy['threshold']) if policy['threshold'] is not None else risk_point(rows,1.0000001)
                point['threshold']=policy['threshold']
                accepted=np.array([r['adequate'] and policy['threshold'] is not None and r['probability']>=policy['threshold'] for r in rows])
                uncertainty[dataset][method].update(accepted=accepted,failed=np.array([r['failed'] for r in rows]))
                method_report['repair']=dict(policy=point,curve=[risk_point(rows,t) for t in [0.,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,.99,1.]],
                                             numerical_or_availability_abstentions=sum(not r['adequate'] for r in rows))
                oracle=[];end=[]
                for case,array,row in zip(actual,arrays,rows):
                    for target in np.flatnonzero(case['truth']):
                        repair=array[REPAIR_METHODS[method]][target]
                        if np.isfinite(repair).all():oracle.append(repair_outcome(case['values'],case['reference'],repair,int(target),case['truth']))
                    if row['improvement'] is not None:end.append(row['improvement'])
                method_report['repair']['oracle_target']=dict(scored=len(oracle),mean_improvement=float(np.mean([v['improvement'] for v in oracle])) if oracle else None,
                   harmful_fraction=float(np.mean([v['harmful'] for v in oracle])) if oracle else None)
                method_report['repair']['unthresholded_end_to_end_mean_improvement']=float(np.mean(end)) if end else None
                json_save(directory/dataset/(method+'_repair_rows.json'),rows)
            methods[method]=method_report
        distributions={}
        for method in ('flow','ppca','mixture_ppca','all_ppca'):
            values=[]
            for array in arrays:
                query=np.flatnonzero(array['eligible']);positive=array['truth'][query]
                if method=='flow':
                    if not positive.any():continue
                    values.append(np.stack([array['flow_posterior_crps'],array['flow_interval_coverage'],array['flow_interval_width'],array['flow_energy_score']],1)[positive])
                else:values.append(array[method+'_metrics'][array['truth']&array['eligible']])
            combined=np.concatenate(values) if values else np.empty((0,4))
            distributions[method]=dict(eligible_fault_candidates=len(combined),crps=float(np.mean(combined[:,0])) if len(combined) else None,
                   interval_coverage=float(np.mean(combined[:,1])) if len(combined) else None,interval_width=float(np.mean(combined[:,2])) if len(combined) else None,
                   energy_score=float(np.mean(combined[:,3])) if len(combined) else None)
        report=dict(dataset=dataset,cases=len(public),candidates=int(truth.size),fault_candidates=int(truth.sum()),prevalence=float(truth.mean()),
            source_blocks=len(unique),block_ids=unique,complete_candidates=int(eligible.sum()),eligible_fraction=float(eligible.mean()),
            unscorable_fault_candidates=int((truth&~eligible).sum()),unobservable_injection_attempts=sum(c['fault'].get('attempted_unobservable',False) for c in public),
            methods=methods,repair_distributions=distributions,
            production_manifest_sha256=sha256(directory/dataset/'test/manifest.json'))
        reports[dataset]=report
        np.savez_compressed(directory/dataset/'precision_recall.npz',**curves)
        bootstrap_inputs[dataset]=(block_index,unique,{m:weighted_ap_preparation(truth,s) for m,s in scores.items()})
    rng=np.random.default_rng(20261001);replicates={d:{m:[] for m in r['methods']} for d,r in reports.items()}
    for repeat in range(config['bootstrap_replicates']):
        shared32=None
        for dataset in config['datasets']:
            block_index,blocks,evaluators=bootstrap_inputs[dataset];count=len(blocks)
            if dataset.startswith('synthetic_32'):
                if shared32 is None:shared32=rng.multinomial(count,np.ones(count)/count)
                weights=shared32
            else:weights=rng.multinomial(count,np.ones(count)/count)
            case_weight=weights[block_index]
            for method,evaluate in evaluators.items():replicates[dataset][method].append(evaluate(case_weight))
            for method,values in uncertainty[dataset].items():
                for metric in ('brier','log_loss'):
                    uncertainty_samples[dataset][method][metric].append(float(case_weight@values[metric]/case_weight.sum()))
                if 'accepted' in values:
                    accepted_weight=case_weight*values['accepted'];count=accepted_weight.sum()
                    uncertainty_samples[dataset][method]['repair_coverage'].append(float(count/case_weight.sum()))
                    if count:uncertainty_samples[dataset][method]['repair_risk'].append(float(accepted_weight@values['failed']/count))
    comparisons={};families=config['families']
    for comparator in ['pca','flow_nll','ppca','mixture_ppca','ganf','supervised','flow_plugin','own_history']:
        differences=[];estimate=[]
        for family,datasets in families.items():
            differences.append(np.mean([np.asarray(replicates[d]['flow_ratio'])-np.asarray(replicates[d][comparator]) for d in datasets],axis=0))
            estimate.append(np.mean([reports[d]['methods']['flow_ratio']['average_precision']-reports[d]['methods'][comparator]['average_precision'] for d in datasets]))
        values=np.mean(differences,axis=0);level=.975 if comparator in ('pca','flow_nll') else .95;alpha=(1-level)/2
        low,high=np.quantile(values,[alpha,1-alpha]);mean=float(np.mean(estimate))
        comparisons[comparator]=dict(macro_ap_difference=mean,interval=[float(low),float(high)],interval_level=level,
            family_differences=dict(zip(families,map(float,estimate))),practical_margin_reached=mean>=.02,
            interpretation='positive' if low>0 else 'negative' if high<0 else 'inconclusive')
    for dataset,report in reports.items():
        for method,values in replicates[dataset].items():report['methods'][method]['ap_interval_95']=np.quantile(values,[.025,.975]).tolist()
        for method,metrics in uncertainty_samples[dataset].items():
            for metric,values in metrics.items():
                interval=np.quantile(values,[.025,.975]).tolist() if values else None
                if metric in ('brier','log_loss'):report['methods'][method]['confidence'][metric+'_interval_95']=interval
                elif method in REPAIR_METHODS:report['methods'][method]['repair'][metric+'_interval_95']=interval
        report['paired_differences']={method:dict(estimate=report['methods']['flow_ratio']['average_precision']-report['methods'][method]['average_precision'],
            interval_95=np.quantile(np.asarray(replicates[dataset]['flow_ratio'])-np.asarray(replicates[dataset][method]),[.025,.975]).tolist()) for method in ('pca','flow_nll','ppca')}
        json_save(directory/dataset/'analysis.json',report)
    result=dict(datasets=reports,paired_macro_comparisons=comparisons,
                h1_supported=all(comparisons[m]['interpretation']=='positive' for m in ('pca','flow_nll')),
                h2_supported=comparisons['ppca']['interpretation']=='positive',bootstrap_replicates=config['bootstrap_replicates'],
                resampling='Whole trajectories, Intel time blocks, SKAB experiments. Matched 32-sensor linear/nonlinear trajectories share bootstrap draws. Synthetic configurations average within one family.',
                limitations=['Old real test recordings informed redesign. New injections do not create independent environments.',
                             'Only one three-member trained ensemble, not three ensemble repetitions.',
                             'Few independent real recording blocks limit interval stability.'])
    json_save(directory/'analysis.json',result);np.savez_compressed(directory/'bootstrap_ap.npz',**{d+'__'+m:np.asarray(v) for d,methods in replicates.items() for m,v in methods.items()})
    return result
