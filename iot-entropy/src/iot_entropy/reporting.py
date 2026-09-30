"""Regenerate every reported metric from saved predictions, without sampling."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .evaluation import alert_intervals, bootstrap_mean, event_pr_curve, match_events
from .localization import set_metrics
from .utils import write_json


def measured_direction(values: np.ndarray) -> str:
    finite=values[np.isfinite(values)]
    if not len(finite):return 'undefined'
    value=float(np.median(finite))
    return 'increase' if value>1e-4 else 'decrease' if value< -1e-4 else 'stable'


def evaluate_directory(directory: Path, interval_seconds: int, alphas: list[float]) -> tuple[list[dict],list[dict],list[dict]]:
    status=json.loads((directory/'status.json').read_text())
    config=json.loads((directory/'configuration.json').read_text())
    events=json.loads((directory/'events.json').read_text())
    # NpzFile re-inflates an entire compressed array on every lookup. Materialize
    # once before the event/method loop; values and metrics are unchanged.
    with np.load(directory/'predictions.npz') as source:
        archive={key:source[key] for key in source.files}
    methods=archive['methods'].tolist();times=archive['times'];budget=int(archive['localization_budget'])
    timings=json.loads((directory/'runtime.json').read_text())['timings']
    shared_latency=float(np.mean([r['seconds'] for r in timings if r['stage']=='calibration']))
    rows=[];curves=[];calibration_rows=[]
    for k,method in enumerate(methods):
        predictions=[]
        for i,event in enumerate(events):
            truth=[(event['onset'],event['onset']+event['duration']-1)] if event['is_fault'] else []
            predictions.append({'times':times,'pvalues':archive['pvalues'][i,:,k],'events':truth})
            during=(times>=event['onset'])&(times<event['onset']+event['duration'])
            direction=measured_direction(archive['observed_delta_h'][i,during])
            paired_direction=measured_direction(archive['entropy_direction'][i,during])
            for alpha in alphas:
                flags=archive['pvalues'][i,:,k]<=alpha
                alerts=alert_intervals(times,flags,config['alert_stride'])
                matched=match_events(alerts,truth,config['event_tolerance'])
                if matched['matches']:
                    alert_index,_=matched['matches'][0]
                    first=alerts[alert_index][0]
                    tick=int(np.where(times==first)[0][0])
                    predicted=archive['ranked_nodes'][i,tick,k,:budget].tolist()
                    localization=set_metrics(predicted,event['nodes'])
                    delay=(first-event['onset'])*interval_seconds
                else:
                    localization={key:0. for key in ['precision','recall','f1','iou']};delay=np.nan
                row={'dataset':status['dataset'],'primary_dataset':'synthetic' if status['dataset'].startswith('synthetic') else status['dataset'],
                     'seed':status['seed'],'graph':status['graph'],'method':method,'alpha':alpha,
                     'event':event['id'],'base':event['base'],'kind':event['kind'],'is_fault':event['is_fault'],
                     'duration':event['duration'],'severity':event['severity'],'fault_size':len(event['nodes']),
                     'affected_components':event.get('affected_components',0),'actual_entropy_direction':direction,
                     'paired_entropy_direction':paired_direction,'tp':matched['tp'],'fp':matched['fp'],'fn':matched['fn'],
                     'delay_seconds':delay,'eligible_fraction':float(archive['method_eligible_fraction'][i,:,k].mean()),
                     'shared_pipeline_seconds':shared_latency,'delay_with_shared_pipeline_seconds':delay+shared_latency,
                     'observed_eligible_fraction':float(archive['eligible_fraction'][i].mean()),
                     'flagged_issuances':int(flags.sum()),'issuances':len(flags),
                     'monitoring_days':len(times)*config['alert_stride']*interval_seconds/86400,
                     'localization_budget':budget,'oracle_iou':event['oracle_group_iou'],
                     **{f'localization_{key}':value for key,value in localization.items()}}
                rows.append(row)
        curve=event_pr_curve(predictions,np.unique(np.r_[0,np.linspace(.01,1,100)]),config['alert_stride'],config['event_tolerance'])
        curves.append({'dataset':status['dataset'],'seed':status['seed'],'graph':status['graph'],'method':method,**curve})
        cal=np.load(directory/'calibration.npz')['maxima'][:,k]
        finite=cal[np.isfinite(cal)]
        correlation=float(np.corrcoef(finite[:-1],finite[1:])[0,1]) if len(finite)>3 and np.std(finite)>0 else None
        calibration_rows.append({'dataset':status['dataset'],'seed':status['seed'],'method':method,'n':len(cal),
                                 'minimum_p':1/(len(cal)+1),'lag1_maximum_correlation':correlation,
                                 'all_abstained_units':int(np.isneginf(cal).sum())})
    return rows,curves,calibration_rows


def aggregate(root: Path, allow_partial: bool = False) -> dict:
    config=json.loads((root/'configs/full.json').read_text())
    missing=[f'{dataset}/{seed}' for dataset in config['datasets'] for seed in config['training_seeds']
             if not (root/'experiments/full'/f'score-{dataset}-physical-{seed}/status.json').exists()]
    if missing and not allow_partial:
        raise RuntimeError('Primary scoring incomplete: '+', '.join(missing))
    rows=[];curves=[];calibration=[];runtimes=[];fidelity=[]
    for status_file in sorted((root/'experiments/full').glob('score-*/status.json')):
        directory=status_file.parent
        status=json.loads(status_file.read_text())
        metadata=json.loads((root/'data/manifests'/f"{status['dataset']}.json").read_text())
        current,pr,cal=evaluate_directory(directory,metadata['interval_seconds'],[.05,.1,.2])
        rows.extend(current);curves.extend(pr);calibration.extend(cal)
        runtime=json.loads((directory/'runtime.json').read_text())
        for timing in runtime['timings']:
            runtimes.append({'dataset':status['dataset'],'seed':status['seed'],'graph':status['graph'],**timing,'peak_gpu_bytes':runtime['peak_gpu_bytes']})
        for record in json.loads((directory/'fidelity.json').read_text()):
            # The primary scorer recorded support explicitly. Zero dimensions
            # cannot define a multivariate score; never interpret its stored
            # numerical zero as perfect fidelity.
            if record.get('energy_dimensions',0)==0:record['energy_score']=None
            fidelity.append({'dataset':status['dataset'],'seed':status['seed'],'graph':status['graph'],**record})
    if not rows:raise RuntimeError('No completed score outputs')
    output=root/'results';output.mkdir(exist_ok=True)
    write_json(output/'report-coverage.json',{'primary_complete':not missing,'missing_primary_runs':missing,
               'completed_scoring_configurations':len(list((root/'experiments/full').glob('score-*/status.json')))})
    frame=pd.DataFrame(rows);frame.to_csv(output/'event_metrics.csv.gz',index=False)
    write_json(output/'event_pr_curves.json',curves)
    pd.DataFrame(calibration).to_csv(output/'calibration_diagnostics.csv',index=False)
    pd.DataFrame(runtimes).to_csv(output/'runtime.csv',index=False)
    pd.DataFrame(fidelity).to_csv(output/'fidelity.csv',index=False)
    summaries=[]
    primary=frame[(frame.alpha==config['primary_alpha'])&(frame.graph=='physical')]
    for (dataset,method),group in primary.groupby(['primary_dataset','method']):
        faults=group[group.is_fault]
        controls=group[group.kind=='untouched']
        transitions=group[group.kind=='transition']
        # Average training seeds within each source block; then resample entire
        # blocks, keeping all correlated injections together.
        block_metrics=faults.groupby(['dataset','base'])[['tp','localization_iou','localization_f1','localization_precision','localization_recall','eligible_fraction','observed_eligible_fraction']].mean()
        summary={'dataset':dataset,'method':method,'alpha':config['primary_alpha'],
                 'fault_realizations':len(faults[['dataset','event']].drop_duplicates()),
                 'training_seeds':sorted(faults.seed.unique().tolist()),'independent_blocks':len(block_metrics),
                 'event_precision':float(group.tp.sum()/max(group.tp.sum()+group.fp.sum(),1)),
                 'pooled_event_recall':float(faults.tp.mean()),
                 'macro_type_recall':float(faults.groupby('kind').tp.mean().mean()),
                 'median_delay_seconds':float(faults.delay_seconds.median()),
                 'median_delay_with_shared_pipeline_seconds':float(faults.delay_with_shared_pipeline_seconds.median()),
                 'background_alerts_per_network_day':float(controls.fp.sum()/max(controls.monitoring_days.sum(),1e-8)),
                 'background_unit_exceedance':float(controls.flagged_issuances.sum()/max(controls.issuances.sum(),1)),
                 'transition_unit_exceedance':float(transitions.flagged_issuances.sum()/max(transitions.issuances.sum(),1)),
                 'missed_event_seed_pairs':int(faults.fn.sum()),'oracle_mean_iou':float(faults.oracle_iou.mean()),
                 'event_trial_prevalence':float(group.is_fault.mean())}
        detected=faults[faults.tp>0]
        summary['detected_event_seed_pairs']=len(detected)
        summary['conditional_detected_localization']={metric:float(detected['localization_'+metric].mean())
                                                     for metric in ['precision','recall','f1','iou']}
        seed_scores=faults.groupby('seed')[['tp','localization_iou']].mean()
        summary['seed_variability']={str(seed):{'event_recall':float(row.tp),'localization_iou':float(row.localization_iou)}
                                    for seed,row in seed_scores.iterrows()}
        for metric in block_metrics:
            name='event_recall' if metric=='tp' else metric
            summary[name]=bootstrap_mean(block_metrics[metric].to_numpy(),repeats=config['bootstrap_repetitions'])
        node_counts={'synthetic64':64,'synthetic128':128,'synthetic256':256,'intel':54,'pems':325}
        denominator=sum(row.monitoring_days*node_counts[row.dataset] for row in controls.itertuples())
        summary['background_alerts_per_sensor_day']=float(controls.fp.sum()/max(denominator,1e-8))
        relevant=[x['event_auprc_envelope'] for x in curves if x['method']==method and x['graph']=='physical' and ('synthetic' if x['dataset'].startswith('synthetic') else x['dataset'])==dataset]
        summary['mean_event_auprc_envelope']=float(np.mean(relevant))
        summaries.append(summary)
    write_json(output/'summary.json',summaries)
    pd.json_normalize(summaries).to_csv(output/'method_comparison.csv',index=False)
    paired=[]
    comparisons=[('diffusion/entropy','diffusion/synchronization'),('diffusion/entropy','diffusion/matrix'),
                 ('diffusion/combined','diffusion/synchronization'),('diffusion/entropy','bootstrap/entropy'),
                 ('diffusion/combined','bootstrap/combined')]
    faults=primary[primary.is_fault]
    for dataset,group in faults.groupby('primary_dataset'):
        for left,right in comparisons:
            for metric in ['tp','localization_iou']:
                pivot=group.groupby(['dataset','base','method'])[metric].mean().unstack('method')
                difference=(pivot[left]-pivot[right]).dropna()
                paired.append({'dataset':dataset,'left':left,'right':right,'metric':metric,
                               **bootstrap_mean(difference.to_numpy(),repeats=config['bootstrap_repetitions'])})
    write_json(output/'paired_comparisons.json',paired)
    directional_pairs=[]
    for (dataset,direction),group in faults.groupby(['primary_dataset','actual_entropy_direction']):
        for left,right in comparisons[:3]:
            for metric in ['tp','localization_iou']:
                pivot=group.groupby(['dataset','base','method'])[metric].mean().unstack('method')
                difference=(pivot[left]-pivot[right]).dropna()
                directional_pairs.append({'dataset':dataset,'actual_entropy_direction':direction,'left':left,'right':right,'metric':metric,
                                           **bootstrap_mean(difference.to_numpy(),repeats=config['bootstrap_repetitions'])})
    write_json(output/'direction-paired-comparisons.json',directional_pairs)
    stratifier=primary[primary.is_fault].groupby(['primary_dataset','method','kind','duration','severity','fault_size','actual_entropy_direction'],dropna=False)
    strata=stratifier[['tp','localization_iou','delay_seconds','eligible_fraction']].mean()
    strata['event_seed_pairs']=stratifier.size()
    strata=strata.reset_index()
    strata.to_csv(output/'stratified_metrics.csv',index=False)
    # Keep individual graph variants visible, never pool them into primary rows.
    ablations=frame[frame.alpha==config['primary_alpha']].groupby(['dataset','graph','method','is_fault'])[['tp','fp','localization_iou','eligible_fraction']].mean().reset_index()
    ablations.to_csv(output/'ablations.csv',index=False)
    directions=primary[primary.is_fault].groupby(['primary_dataset','method','actual_entropy_direction'])[['tp','localization_iou']].agg(['mean','count'])
    directions.to_csv(output/'direction_metrics.csv')
    topology=primary[primary.is_fault].groupby(['primary_dataset','method','affected_components'])[['tp','localization_iou']].agg(['mean','count'])
    topology.to_csv(output/'topology_metrics.csv')
    for filename in ['benchmark.json','fidelity-extra.json']:
        path=root/'experiments'/filename
        if path.exists():write_json(output/filename,json.loads(path.read_text()))
    benchmark=root/'experiments/benchmark.json'
    if benchmark.exists():
        costs={x['dataset']:x['complete_detector']['mean_seconds'] for x in json.loads(benchmark.read_text())['detector']}
        latency=primary[(primary.method=='diffusion/entropy')&primary.is_fault].copy()
        latency['mean_compute_seconds']=latency.dataset.map(costs)
        latency['delay_with_serial_computation_seconds']=latency.delay_seconds+latency.mean_compute_seconds
        latency.to_csv(output/'delay_with_computation.csv',index=False)
    feature_subset_ablations(root)
    sample_rows=[];sample_checks=[]
    for name in ['synthetic64','pems']:
        archives=[];event_lists=[]
        for count in [32,64,128]:
            directory=root/f'experiments/sensitivity/B{count}/score-{name}-physical-17'
            if not (directory/'status.json').exists():continue
            metadata=json.loads((root/'data/manifests'/f'{name}.json').read_text())
            evaluated,_,_=evaluate_directory(directory,metadata['interval_seconds'],[.1])
            sample_rows.extend([dict(row,generated_samples=count) for row in evaluated])
            with np.load(directory/'predictions.npz') as source:
                column=source['methods'].tolist().index('gdn');archives.append(source['pvalues'][:,:,column])
            event_lists.append(json.loads((directory/'events.json').read_text()))
        if len(archives)==3:
            for archive,events in zip(archives[1:],event_lists[1:]):
                np.testing.assert_array_equal(archives[0],archive)
                if events!=event_lists[0]:raise ValueError('Sample-count sensitivity changed the injection realizations')
            sample_checks.append({'dataset':name,'identical_fault_realizations':True,'identical_gdn_control_pvalues':True})
    if sample_rows:
        pd.DataFrame(sample_rows).to_csv(output/'sample_count_metrics.csv',index=False)
        write_json(output/'sample_count_consistency.json',sample_checks)
    return {'completed_scoring_configurations':len(list((root/'experiments/full').glob('score-*/status.json'))),'event_metric_rows':len(frame),'summary_rows':len(summaries)}


def feature_subset_ablations(root: Path) -> None:
    """Recalibrate each restricted family from saved samples, with no retraining."""
    from .calibration import rank_pvalues
    from .localization import participation
    rows=[]
    for status_file in sorted((root/'experiments/full').glob('score-*-physical-17/status.json')):
        directory=status_file.parent;status=json.loads(status_file.read_text())
        config=json.loads((directory/'configuration.json').read_text())
        groups=json.loads((directory/'groups.json').read_text())
        events=json.loads((directory/'events.json').read_text())
        with np.load(directory/'predictions.npz') as source:
            predictions={key:source[key] for key in source.files}
        times=predictions['times']
        with np.load(directory/'samples/group_scores.npz') as source:
            archive={key:source[key] for key in source.files}
        for feature in ['window','size']:
            for value in sorted({g[feature] for g in groups}):
                selected=np.array([g[feature]==value for g in groups]);subgroups=[g['nodes'] for g in groups if g[feature]==value]
                for method in ['diffusion/entropy','diffusion/synchronization','diffusion/combined']:
                    column=archive['methods'].tolist().index(method)
                    cal=archive['calibration'][:,column,:][:,selected]
                    test=archive['scores'][:,:,column,:][:,:,selected]
                    calmax=np.where(np.isfinite(cal),cal,-np.inf).max(-1)
                    maximum=np.where(np.isfinite(test),test,-np.inf).max(-1)
                    pvalues=rank_pvalues(calmax,maximum)
                    n={'synthetic64':64,'synthetic128':128,'synthetic256':256,'intel':54,'pems':325}[status['dataset']]
                    for i,event in enumerate(events):
                        truth=[(event['onset'],event['onset']+event['duration']-1)] if event['is_fault'] else []
                        alerts=alert_intervals(times,pvalues[i]<=.1,config['alert_stride'])
                        matched=match_events(alerts,truth,0);iou=0.
                        if matched['matches']:
                            alert,_=matched['matches'][0];tick=int(np.where(times==alerts[alert][0])[0][0])
                            scores=participation(test[i,tick],subgroups,n)
                            nodes=np.argsort(-scores,kind='stable')[:int(predictions['localization_budget'])].tolist()
                            iou=set_metrics(nodes,event['nodes'])['iou']
                        rows.append({'dataset':status['dataset'],'method':method,'feature':feature,'value':value,
                                     'event':event['id'],'base':event['base'],'is_fault':event['is_fault'],'kind':event['kind'],
                                     'tp':matched['tp'],'fp':matched['fp'],'iou':iou,
                                     'eligible_fraction':float(np.isfinite(test[i]).mean())})
    pd.DataFrame(rows).to_csv(root/'results/group_window_ablations.csv',index=False)
