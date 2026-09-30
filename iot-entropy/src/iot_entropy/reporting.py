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
    archive=np.load(directory/'predictions.npz')
    methods=archive['methods'].tolist();times=archive['times'];budget=int(archive['localization_budget'])
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


def aggregate(root: Path) -> dict:
    config=json.loads((root/'configs/full.json').read_text())
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
            fidelity.append({'dataset':status['dataset'],'seed':status['seed'],'graph':status['graph'],**record})
    if not rows:raise RuntimeError('No completed score outputs')
    output=root/'results';output.mkdir(exist_ok=True)
    frame=pd.DataFrame(rows);frame.to_csv(output/'event_metrics.csv',index=False)
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
        block_metrics=faults.groupby(['dataset','base'])[['tp','localization_iou','localization_f1','localization_precision','localization_recall','eligible_fraction']].mean()
        summary={'dataset':dataset,'method':method,'alpha':config['primary_alpha'],
                 'fault_realizations':len(faults[['dataset','event']].drop_duplicates()),
                 'training_seeds':sorted(faults.seed.unique().tolist()),'independent_blocks':len(block_metrics),
                 'event_precision':float(group.tp.sum()/max(group.tp.sum()+group.fp.sum(),1)),
                 'pooled_event_recall':float(faults.tp.mean()),
                 'macro_type_recall':float(faults.groupby('kind').tp.mean().mean()),
                 'median_delay_seconds':float(faults.delay_seconds.median()),
                 'background_alerts_per_network_day':float(controls.fp.sum()/max(controls.monitoring_days.sum(),1e-8)),
                 'background_unit_exceedance':float(controls.flagged_issuances.sum()/max(controls.issuances.sum(),1)),
                 'transition_unit_exceedance':float(transitions.flagged_issuances.sum()/max(transitions.issuances.sum(),1)),
                 'missed_event_seed_pairs':int(faults.fn.sum()),'oracle_mean_iou':float(faults.oracle_iou.mean()),
                 'event_trial_prevalence':float(group.is_fault.mean())}
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
    strata=primary[primary.is_fault].groupby(['primary_dataset','method','kind','duration','severity','fault_size','actual_entropy_direction'],dropna=False)[['tp','localization_iou','delay_seconds','eligible_fraction']].mean().reset_index()
    strata.to_csv(output/'stratified_metrics.csv',index=False)
    # Keep individual graph variants visible, never pool them into primary rows.
    ablations=frame[frame.alpha==config['primary_alpha']].groupby(['dataset','graph','method','is_fault'])[['tp','fp','localization_iou','eligible_fraction']].mean().reset_index()
    ablations.to_csv(output/'ablations.csv',index=False)
    return {'completed_scoring_configurations':len(list((root/'experiments/full').glob('score-*/status.json'))),'event_metric_rows':len(frame),'summary_rows':len(summaries)}
