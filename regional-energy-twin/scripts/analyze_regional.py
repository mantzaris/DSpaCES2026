"""Descriptive analysis of frozen regional outputs; no new model or outcome access."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def main():
    root=Path('results/regional/replay')
    cost=pd.read_csv(root/'costs.csv'); num=pd.read_csv(root/'numerical.csv')
    forecast=pd.read_csv(root/'forecasts.csv'); cert=pd.read_csv(root/'certificates.csv')
    snapshots=json.loads((root/'snapshots.json').read_text()); summary=json.loads((root/'summary.json').read_text())
    methods={}
    for method,frame in cost.groupby('method'):
        complete=frame.complete_seconds.dropna()
        methods[method]=dict(solver_batch_p50_seconds=float(frame.seconds.median()),
            solver_batch_p95_seconds=float(frame.seconds.quantile(.95)),
            queries_per_solver_second=float(frame.queries.sum()/frame.seconds.sum()),
            complete_snapshot_p50_seconds=float(complete.median()) if len(complete) else None,
            complete_snapshot_p95_seconds=float(complete.quantile(.95)) if len(complete) else None,
            complete_queries_per_second=float(frame.loc[complete.index,'queries'].sum()/complete.sum()) if len(complete) else None)
        error=num[num.method==method]
        if len(error):
            methods[method].update(max_relative_residual=float(error.relative_residual.max()),
                max_weighted_relative_error=float(error.weighted_relative_error.max()),
                max_forward_error=float(error.euclidean_forward_error.max()),max_backward_error=float(error.backward_error.max()),
                max_regional_solver_error_kwh=float(error[['output_error_1h_kwh','output_error_6h_kwh']].max().max()),
                peak_alert_agreement=float(error[['peak_agreement_1h','peak_agreement_6h']].values.mean()),failures=int(error.failed.sum()))
    outcomes=[]
    for (profile,method,horizon),frame in forecast[forecast.profile.isin([0,1])].groupby(['profile','method','horizon']):
        outcomes.append(dict(profile=int(profile),method=method,horizon_hours=int(horizon//2),
            household_mae=float(frame.household_mae.mean()),household_rmse=float(np.sqrt(frame.household_mse.mean())),
            regional_observed_support_mae=float(frame.regional_absolute_error.mean()),
            regional_observed_support_rmse=float(np.sqrt(frame.regional_squared_error.mean())),
            min_observed_households=int(frame.observed_households.min()),max_observed_households=int(frame.observed_households.max())))
    bounds={}
    for name,frame in cert.groupby('basis'):
        bounds[name]=dict(queries=len(frame),delta_less_than_one=int((frame.delta<1).sum()),
            output_conclusive=int(frame.conclusive.sum()),delta_median=float(frame.delta.median()),
            global_median=float(frame.global_delta.median()),block_median=float(frame.block_delta.median()),
            row_median=float(frame.row_delta.median()),
            global_query_us=float(frame.global_query_seconds.median()*1e6),
            block_query_us=float(frame.block_query_seconds.median()*1e6),
            global_setup_ms=float(np.median([x['family_stage_seconds'][name]['global_gram_seconds'] for x in snapshots])*1e3),
            block_setup_ms=float(np.median([x['family_stage_seconds'][name]['block_gram_seconds'] for x in snapshots])*1e3),
            transform_ms=float(np.median([x['family_stage_seconds'][name]['transform_seconds'] for x in snapshots])*1e3),
            norm_audits=int(frame.spectral_delta_audit.notna().sum()),
            median_initial_relative_residual=float(frame.initial_relative_residual.median()))
    unique=forecast[forecast.profile==0].drop_duplicates(['origin','horizon'])
    fallback={}
    for x in snapshots:
        for name,v in x['fallback_counts'].items():fallback[name]=fallback.get(name,0)+v
    output=dict(methods=methods,forecast_metrics=outcomes,bounds=bounds,fallback_counts=fallback,
        unique_target_intervals=len(unique),observed_household_targets=int(unique.observed_households.sum()),
        full_cohort_target_intervals=int((unique.observed_households==summary['households']).sum()),
        development_window_observations=sum(x['available_window_cells'] for x in snapshots),
        independent_time_groups='Four selected development weeks; descriptive pilot, no population confidence interval',
        native_mask_recomputations=sum(x['native_matrix_recomputed'] for x in snapshots),
        matrix_cache_misses=sum(x['matrix_new_factors'] for x in snapshots),
        mean_prediction_seconds=float(np.mean([x['prediction_seconds'] for x in snapshots])),
        mean_persistence_seconds=float(np.mean([x['persistence_seconds'] for x in snapshots])))
    (root/'analysis.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
