"""Frozen descriptive summaries, paired short-block sensitivity, and cost gates."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def main():
    metrics=pd.read_csv('results/pilot_metrics.csv')
    costs=pd.read_csv('results/pilot_costs.csv')
    diagnostics=pd.read_json('results/diagnostics.json')
    exact=pd.read_json('results/exact_exchange.json')
    benchmarks=json.loads(Path('results/benchmarks.json').read_text())
    numeric=['mae','rmse','bias','coverage90','coverage95','normalized_is90','width90','normalized_reservation_loss']
    # Equal weight to buildings; allocation replicates are averaged within building.
    building=metrics.groupby(['building','site','method','calibrated'])[numeric].mean().reset_index()
    summary=building.groupby(['method','calibrated'])[numeric].mean().reset_index()
    summary.to_csv('results/summary_metrics.csv',index=False)
    metrics.groupby(['site','method','calibrated'])[numeric].mean().reset_index().to_csv('results/site_metrics.csv',index=False)
    leave=[]
    for omitted in sorted(building.site.unique()):
        table=building[(building.site!=omitted)&building.calibrated].groupby('method')[numeric].mean()
        for ref in ('common_corrected','exact_lineage','ci','shrinkage'):
            leave.append(dict(omitted_site=omitted,reference=ref,
                is90_difference=float(table.loc['sketch_2048','normalized_is90']-table.loc[ref,'normalized_is90']),
                coverage90_difference=float(table.loc['sketch_2048','coverage90']-table.loc[ref,'coverage90'])))
    pd.DataFrame(leave).to_csv('results/site_deletion.csv',index=False)
    # Raw outcomes remain untracked. Commit only aggregates of observed calendar blocks.
    pred=pd.read_csv('results/pilot_predictions.csv')
    audit=json.loads(Path('manifests/data_audit.json').read_text())
    scales={r['building']:r['training_scale'] for r in audit['selection']}
    pred['scale']=pred.building.map(scales)
    sd=np.sqrt(pred.variance.to_numpy());err=pred.outcome.to_numpy()-pred['mean'].to_numpy()
    radius=pred.q90.to_numpy()*sd
    pred['is90']=(2*radius+20*np.maximum(np.abs(err)-radius,0))/pred.scale.to_numpy()
    pred['coverage90']=(np.abs(err)<=radius).astype(float)
    q=np.maximum(pred['mean'].to_numpy()+pred.q80.to_numpy()*sd,0)
    pred['loss']=(4*np.maximum(pred.outcome.to_numpy()-q,0)+np.maximum(q-pred.outcome.to_numpy(),0))/pred.scale.to_numpy()
    per_target=pred.groupby(['building','site','target','method'])[['is90','coverage90','loss']].mean().reset_index()
    per_target['week']=pd.to_datetime(per_target.target).dt.to_period('W-SUN').astype(str)
    blocks=per_target.groupby(['week','building','site','method'])[['is90','coverage90','loss']].agg(['sum','count'])
    blocks.columns=['_'.join(x) for x in blocks.columns]
    blocks.reset_index().to_csv('results/pilot_block_sums.csv',index=False)
    rng=np.random.default_rng(817);weeks=sorted(per_target.week.unique());bootstrap=[]
    block_reset=blocks.reset_index()
    for _ in range(1000):
        sampled=rng.choice(weeks,size=len(weeks),replace=True)
        selected=pd.concat([block_reset[block_reset.week==week] for week in sampled],ignore_index=True)
        summed=selected.groupby(['building','method'])[['is90_sum','is90_count','coverage90_sum','coverage90_count','loss_sum','loss_count']].sum()
        for column in ('is90','coverage90','loss'):summed[column]=summed[column+'_sum']/summed[column+'_count']
        table=summed.groupby('method')[['is90','coverage90','loss']].mean()
        bootstrap.append({ref:{col:float(table.loc['sketch_2048',col]-table.loc[ref,col]) for col in ('is90','coverage90','loss')}
                          for ref in ('common_corrected','exact_lineage','ci','shrinkage')})
    intervals={ref:{col:dict(low=float(np.quantile([r[ref][col] for r in bootstrap],.025)),
                             high=float(np.quantile([r[ref][col] for r in bootstrap],.975)))
                    for col in ('is90','coverage90','loss')} for ref in bootstrap[0]}
    Path('results/paired_sensitivity.json').write_text(json.dumps(dict(replicates=1000,week_labels=weeks,
        warning='Only three calendar week groups, two partial: descriptive resampling sensitivity, not credible population confidence intervals',
        unit='All buildings and methods resampled together; allocation replicates averaged per observed target',
        differences='sketch_2048 minus reference, calibrated',intervals=intervals),indent=2)+'\n')
    calibrated=summary[summary.calibrated].set_index('method')
    primary=costs[costs.k==2048]
    estimates=[]
    cpu=next(r for r in benchmarks['summary'] if r['backend']=='cpu' and r['batch']==256)
    for count in (16,32,64,128):
        targets=count*8760;queries=targets*9
        warm_seconds=queries/cpu['queries_per_second']
        setup_seconds=count*9*float(primary[['fit_seconds','operator_seconds']].sum(axis=1).mean())+count*float(primary.projection_seconds.mean())
        # Conservative sensitivity, not measured full-run time. Includes independent
        # 8-hour allowance for other packages and 25% replay overhead.
        projected_hours=(1.25*(warm_seconds+setup_seconds))/3600+8
        estimates.append(dict(buildings=count,unique_targets_upper_bound=targets,primary_queries_upper_bound=queries,
            warm_replay_hours=warm_seconds/3600,with_25pct_margin_and_8h_other_packages=projected_hours,
            under_total_24h=projected_hours<=24,
            full_wire_bytes=queries*float(primary.sketch_bytes_per_query.mean()),
            caveat='Linear projection of measured FP64 CPU replay, no missing-target savings; margin and other-package allowance are assumptions'))
    result=dict(decision='stop_sketch_branch',main_study_authorized=False,
        theory_numerics_passed=True,novelty_established=False,
        buildings=metrics.building.nunique(),sites=metrics.site.nunique(),
        unique_scored_targets=len(pred[['building','target']].drop_duplicates()),score_week_groups=weeks,
        training_influence_fraction_mean=float(diagnostics.training_influence_fraction_mean.mean()),
        exact_vs_common_corrected_calibrated_is90_relative=float(calibrated.loc['exact_lineage','normalized_is90']/calibrated.loc['common_corrected','normalized_is90']-1),
        sketch_vs_exact_calibrated_is90_relative=float(calibrated.loc['sketch_2048','normalized_is90']/calibrated.loc['exact_lineage','normalized_is90']-1),
        sketch_vs_exact_calibrated_coverage90_difference=float(calibrated.loc['sketch_2048','coverage90']-calibrated.loc['exact_lineage','coverage90']),
        measured_exact_contract_once_bytes_mean=float(exact.once_bytes.mean()),
        measured_exact_contract_reconstruction_seconds_mean=float(exact.parse_and_reconstruction_seconds.mean()),
        sketch_cached_operator_once_bytes_mean=float(primary.cached_sketch_operator_once_bytes.mean()),
        gpu_complete_pipeline_benefit=False,main_cost_projection=estimates,
        reasons=['Exact lineage adds little beyond common-noise correction on this pilot',
                 'Compressed public-calendar exact supports are much smaller than sketches',
                 'No complete-pipeline GPU speedup at measured batches',
                 'Short chronological calibration did not transfer at nominal coverage',
                 'A distinctive new theorem is not established'],
        next_step='Preserve a contract/negative-result diagnostic; no expanded study without a revised scientific rationale and explicit authorization')
    Path('results/decision.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
