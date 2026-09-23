"""Stage 2: recompute summaries from frozen outputs, without fitting or data access.

Uses saved aggregate blocks and the October-only, ignored evaluator CSV. Never
loads raw meter files, November/December outcomes, CUDA, or a training routine.
Writes only results/stage2. Run through scripts/stage2_job.py.
"""
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd


OUT = Path('results/stage2')


def read_json(path):
    return json.loads(Path(path).read_text())


def main():
    metrics = pd.read_csv('results/pilot_metrics.csv')
    audit = read_json('manifests/data_audit.json')
    scales = {row['building']: row['training_scale'] for row in audit['selection']}
    metrics['normalized_width90'] = metrics.width90 / metrics.building.map(scales)
    cols = ['mae', 'rmse', 'bias', 'coverage90', 'coverage95', 'normalized_is90',
            'width90', 'normalized_width90', 'normalized_reservation_loss']
    building = metrics.groupby(['building', 'site', 'method', 'calibrated'])[cols].mean().reset_index()
    summary = building.groupby(['method', 'calibrated'])[cols].mean().reset_index()
    old = pd.read_csv('results/summary_metrics.csv')
    keys = ['method', 'calibrated']
    common = [c for c in cols if c in old]
    np.testing.assert_allclose(summary.sort_values(keys)[common], old.sort_values(keys)[common], rtol=1e-12, atol=1e-12)
    summary.to_csv(OUT / 'summary_metrics.csv', index=False)
    overlap = metrics.groupby(['common_days', 'method', 'calibrated'])[cols].mean().reset_index()
    overlap.to_csv(OUT / 'by_overlap.csv', index=False)

    contrasts = [('exact_lineage', 'common_corrected'), ('sketch_2048', 'exact_lineage'),
                 ('exact_lineage', 'individual_2'), ('sketch_2048', 'individual_2')]
    rows = []
    for calibrated in (False, True):
        table = summary[summary.calibrated == calibrated].set_index('method')
        for method, reference in contrasts:
            entry = dict(method=method, reference=reference, calibrated=calibrated)
            for metric in cols:
                a, b = table.loc[method, metric], table.loc[reference, metric]
                entry[metric + '_difference'] = float(a-b)
                if b != 0:
                    entry[metric + '_relative'] = float(a/b-1)
            rows.append(entry)
    (OUT / 'contrasts.json').write_text(json.dumps(rows, indent=2)+'\n')

    # The paired exact-vs-common contrast was absent from Stage 1's sensitivity
    # output. Enumerate all 3^3 ordered resamples, avoiding Monte Carlo variation.
    blocks = pd.read_csv('results/pilot_block_sums.csv')
    weeks = sorted(blocks.week.unique())
    assert len(weeks) == 3
    values = []
    for sampled in itertools.product(weeks, repeat=3):
        selected = pd.concat([blocks[blocks.week == w] for w in sampled])
        total = selected.groupby(['building', 'method']).sum(numeric_only=True)
        for metric in ('is90', 'coverage90', 'loss'):
            total[metric] = total[metric+'_sum']/total[metric+'_count']
        table = total.groupby('method')[['is90', 'coverage90', 'loss']].mean()
        values.append({metric: float(table.loc['exact_lineage', metric]-table.loc['common_corrected', metric])
                       for metric in ('is90', 'coverage90', 'loss')})
    sensitivity = dict(ordered_resamples=27, week_labels=weeks,
        warning='Descriptive three-week sensitivity, two partial weeks; not a population confidence interval or equivalence test',
        comparison='exact_lineage minus common_corrected, calibrated',
        ranges={metric: dict(minimum=min(v[metric] for v in values), maximum=max(v[metric] for v in values),
            lower_2_5_percentile=float(np.quantile([v[metric] for v in values], .025)),
            upper_97_5_percentile=float(np.quantile([v[metric] for v in values], .975)))
            for metric in ('is90', 'coverage90', 'loss')})
    leave = []
    for site in sorted(building.site.unique()):
        table = building[(building.site != site) & building.calibrated].groupby('method')[cols].mean()
        leave.append(dict(omitted_site=site, is90_difference=float(table.loc['exact_lineage','normalized_is90']-table.loc['common_corrected','normalized_is90']),
                          relative_is90=float(table.loc['exact_lineage','normalized_is90']/table.loc['common_corrected','normalized_is90']-1)))
    sensitivity['leave_site_out'] = leave
    (OUT / 'exact_common_sensitivity.json').write_text(json.dumps(sensitivity, indent=2)+'\n')

    # Recompute every available saved per-target metric independently.
    pred = pd.read_csv('results/pilot_predictions.csv', float_precision='round_trip')
    times = pd.to_datetime(pred.target)
    assert times.min() >= pd.Timestamp('2016-10-21') and times.max() < pd.Timestamp('2016-11-01')
    assert not pred.duplicated(['building','target','common_days','method']).any()
    target_count = pred.groupby(['building','target']).outcome.nunique()
    assert (target_count == 1).all(), 'Methods must score the identical outcome'
    e = pred.outcome - pred['mean']
    scale = pred.building.map(scales)
    rad = pred.q90*np.sqrt(pred.variance)
    pred['normalized_is90'] = (2*rad+20*np.maximum(np.abs(e)-rad,0))/scale
    pred['coverage90'] = (np.abs(e) <= rad).astype(float)
    reserve = np.maximum(pred['mean']+pred.q80*np.sqrt(pred.variance),0)
    pred['normalized_reservation_loss'] = (4*np.maximum(pred.outcome-reserve,0)+np.maximum(reserve-pred.outcome,0))/scale
    saved_cols = ['normalized_is90','coverage90','normalized_reservation_loss']
    checked = pred.groupby(['building','common_days','method'])[saved_cols].mean()
    recorded = metrics[metrics.calibrated].set_index(['building','common_days','method']).loc[checked.index, saved_cols]
    error = float(np.max(np.abs(checked.to_numpy()-recorded.to_numpy())))
    differences = checked-recorded
    bad = differences[np.abs(differences).max(axis=1) > 1e-12]
    if len(bad):
        bad.reset_index().to_csv(OUT / 'metric_discrepancies.csv', index=False)
        print(bad.to_string(), flush=True)
    np.testing.assert_allclose(checked, recorded, atol=1e-12, rtol=1e-12)
    # Preserve Stage 1 aggregates and write corrected blocks alongside the audit.
    target = pred.groupby(['building','site','target','method'])[saved_cols].mean().reset_index()
    target = target.rename(columns={'normalized_is90':'is90','normalized_reservation_loss':'loss'})
    target['week'] = pd.to_datetime(target.target).dt.to_period('W-SUN').astype(str)
    corrected_blocks = target.groupby(['week','building','site','method'])[['is90','coverage90','loss']].agg(['sum','count'])
    corrected_blocks.columns = ['_'.join(c) for c in corrected_blocks.columns]
    corrected_blocks.reset_index().to_csv(OUT/'corrected_pilot_block_sums.csv',index=False)
    prior = blocks.set_index(['week','building','site','method'])
    change = corrected_blocks-prior.loc[corrected_blocks.index,corrected_blocks.columns]
    changed = change[np.abs(change.coverage90_sum) > 1e-10].reset_index()
    changed.to_csv(OUT/'corrected_block_differences.csv',index=False)
    assert set(changed.method) == {'seasonal_naive'}
    assert set(changed.building) == {'Lamb_assembly_Alden'}
    assert abs(changed.coverage90_sum.sum()-30) < 1e-10

    costs = pd.read_csv('results/pilot_costs.csv')
    exact = pd.read_json('results/exact_exchange.json')
    byte_rows = []
    for k in (512, 2048):
        c = costs[costs.k == k]
        header = float(c.common_header_bytes_per_query.mean())
        exact_bytes = float(exact.once_bytes.mean())
        sketch_bytes = float(c.cached_sketch_operator_once_bytes.mean())
        for horizon in (1, 256, 8760):
            byte_rows.append(dict(k=k, horizon=horizon, measured_dynamic_header_bytes=header,
                measured_exact_setup_bytes=exact_bytes, estimated_sketch_setup_bytes=sketch_bytes,
                estimated_exact_bytes_per_query=header+exact_bytes/horizon,
                estimated_cached_sketch_bytes_per_query=header+sketch_bytes/horizon,
                measured_uncached_sketch_bytes_per_query=float(c.sketch_bytes_per_query.mean()),
                caveat='Common dynamic header charged to both; one model refresh; cached sketch setup not an implemented wire codec; horizon 8760 is arithmetic only'))
    pd.DataFrame(byte_rows).to_csv(OUT / 'metadata_accounting.csv', index=False)

    allocations = read_json('manifests/provider_allocations.json')
    for item in allocations:
        sets = [set(days) for days in item['selected_days']]
        assert all(len(s) == 42 and min(s) >= '2016-01-01' and max(s) < '2016-10-01' for s in sets)
        assert len(set.union(*sets))*24 == item['union_records']
        for i,j in itertools.product(range(4),repeat=2):
            assert len(sets[i]&sets[j])*24 == item['intersection_records'][i][j]
    diagnostics = read_json('results/diagnostics.json')
    calibration = read_json('manifests/pilot_calibration.json')
    benchmark = read_json('results/benchmarks.json')
    cold = read_json('results/cold_benchmarks.json')
    main_config_text = Path('configs/main_study.yaml').read_text()
    assert main_config_text.startswith('authorized: false')
    # Every original tracked evidence artifact stays byte-identical.
    inputs = ['results/pilot_metrics.csv','results/pilot_predictions.csv','results/pilot_block_sums.csv',
              'results/pilot_costs.csv','results/summary_metrics.csv','results/exact_exchange.json',
              'results/diagnostics.json','results/benchmarks.json','results/cold_benchmarks.json',
              'manifests/provider_allocations.json','manifests/pilot_calibration.json',
              'configs/pilot.yaml','configs/main_study.yaml']
    result = dict(status='passed', buildings=metrics.building.nunique(), sites=metrics.site.nunique(),
        unique_score_targets=len(target_count), saved_prediction_rows=len(pred),
        score_start=str(times.min()), score_end=str(times.max()), scored_dates=sorted(times.dt.strftime('%Y-%m-%d').unique()),
        unique_score_target_counts_by_week=pred[['building','target']].drop_duplicates().assign(
            week=lambda x: pd.to_datetime(x.target).dt.to_period('W-SUN').astype(str)).groupby('week').size().to_dict(),
        max_saved_metric_absolute_discrepancy=error,
        csv_parser_correction=dict(method='seasonal_naive',building='Lamb_assembly_Alden',
            corrected_unique_targets=30, original_main_metrics_valid=True,
            effect_on_exact_common_or_sketch_contrasts='none', corrected_blocks='corrected_pilot_block_sums.csv'),
        covariance_observations_range=[min(d['covariance_fit']['fit_targets'] for d in diagnostics),max(d['covariance_fit']['fit_targets'] for d in diagnostics)],
        calibration_observations_range=[min(c['n'] for c in calibration),max(c['n'] for c in calibration)],
        mean_training_influence_fraction=float(np.mean([d['training_influence_fraction_mean'] for d in diagnostics])),
        paired_methods=list(sorted(pred.method.unique())),
        no_raw_meter_read=True, no_new_fit=True, no_gpu_execution=True, november_december_and_2017_opened=False,
        cold_initialization_not_in_percentiles=True, timing_replicates=5,
        benchmark_warm_summary=benchmark['summary'], cold_summary=cold['summary'],
        inputs_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in inputs})
    (OUT / 'evidence_checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs_sha256','benchmark_warm_summary','cold_summary')}, indent=2))


if __name__ == '__main__':
    main()
