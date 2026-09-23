"""Descriptive pilot summaries and figures from saved numerical outputs only."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    folder = Path('results/refinement/replay')
    metrics = pd.read_csv(folder/'metrics.csv')
    predictions = pd.read_csv(folder/'predictions.csv')
    costs = pd.read_csv(folder/'costs.csv')
    checks = pd.read_csv(folder/'checks.csv')
    access = pd.read_csv(folder/'access_trace.csv')
    keys = ['population', 'policy', 'active_groups', 'horizon_steps', 'level']
    summary = metrics.groupby(keys).agg(dict(mae='mean', mse='mean', coverage90='mean',
        width90='mean', interval_score90='mean', seasonal_mae='mean', queries='sum', missing_queries='sum')).reset_index()
    summary['rmse'] = np.sqrt(summary.mse)
    summary.to_csv(folder/'outcome_summary.csv', index=False)
    ckeys = ['population', 'policy', 'active_groups']
    numeric = costs.select_dtypes(include=np.number).columns.difference(['population', 'origin', 'active_groups'])
    cost_summary = costs.groupby(ckeys)[numeric].median().reset_index()
    cost_summary.to_csv(folder/'cost_summary.csv', index=False)
    check_cols = ['representation_error', 'cycle_error', 'factor_error', 'separator_mean_error',
                  'separator_covariance_error', 'aggregation_mean_error']
    correct = checks[checks.policy.isin(['fixed', 'random', 'uncertainty'])]
    actual = {c:float(correct[c].max()) for c in check_cols}
    actual['representation_cases'] = int(len(correct))
    actual['roundtrip_cycles'] = int(2*len(correct))
    actual['observed_regional_origins'] = int(metrics.origin.nunique())
    actual['development_weeks'] = 4
    actual['gpu_matrix_event_seconds'] = float(access.matrix_cuda_event_ms.sum()/1000)
    actual['host_to_device_payload_bytes'] = int(access.host_to_device_payload_bytes.sum())
    actual['gpu_peak_bytes'] = int(costs.gpu_peak_bytes.max())
    actual['host_peak_rss_bytes'] = int(costs.host_peak_rss_bytes.max())
    actual['rerefinement_source_file_bytes'] = int(access.loc[access.phase=='rerefine_same_evidence', 'file_bytes'].sum())
    actual['caveat'] = 'Descriptive four-week development replay. No independent-hours inference or held-out confirmation.'
    (folder/'analysis.json').write_text(json.dumps(actual, indent=2)+'\n')
    # Paired four-week descriptive ranges, not confidence intervals.
    panel = metrics[(metrics.population==4194)&(metrics.horizon_steps==2)&(metrics.level=='regional')].copy()
    panel['week'] = panel.origin//8
    week = panel.groupby(['policy', 'active_groups', 'week']).mae.mean().reset_index()
    week.to_csv(folder/'week_descriptive.csv', index=False)
    figures = Path('reports/figures/refinement'); figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size':10, 'pdf.fonttype':42, 'ps.fonttype':42, 'svg.fonttype':'none'})
    colors = {'fixed':'#0072B2', 'random':'#999999', 'uncertainty':'#D55E00',
              'uniform_fine_stream':'#009E73', 'fixed_coarse':'#CC79A7'}
    def save(name):
        plt.savefig(figures/(name+'.pdf'), bbox_inches='tight')
        plt.savefig(figures/(name+'.svg'), bbox_inches='tight')
        svg = figures/(name+'.svg')
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        plt.close()
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for ax, level in zip(axes, ['regional', 'household']):
        p = predictions[(predictions.population==4194)&(predictions.policy=='uncertainty')&
                        (predictions.active_groups==8)&(predictions.horizon_steps==2)&(predictions.level==level)].sort_values('origin')
        x, mean, sd = p.origin.values, p['mean'].values, np.sqrt(p.variance.values)
        ax.fill_between(x, mean-1.644853627*sd, mean+1.644853627*sd, color=colors['uncertainty'], alpha=.2,
                        label='Raw model 90% interval')
        ax.plot(x, mean, color=colors['uncertainty'], label='Selective fine evidence (8 groups)')
        ax.plot(x, p.actual, 'k.-', label='Observed demand')
        ax.plot(x, p.full_evidence_mean, color=colors['uniform_fine_stream'], linestyle='--', label='All-fine reference')
        for edge in [7.5, 15.5, 23.5]: ax.axvline(edge, color='.8', linewidth=.8)
        ax.set_ylabel(('Regional observed support' if level=='regional' else 'First household in group 0')+'\nkWh / half-hour')
        ax.grid(alpha=.2)
    axes[0].legend(ncol=2, fontsize=8)
    axes[1].set_xlabel('Frozen origin index: 8 origins in each of four development weeks')
    fig.suptitle('Exploratory replay: one-hour forecasts and uncalibrated uncertainty')
    fig.tight_layout(); save('refinement_replay')
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for policy in colors:
        for ax, level in zip(axes[:2], ['regional', 'household']):
            p = summary[(summary.population==4194)&(summary.horizon_steps==2)&(summary.level==level)&(summary.policy==policy)]
            c = cost_summary[(cost_summary.population==4194)&(cost_summary.policy==policy)]
            merged = p.merge(c, on=['population', 'policy', 'active_groups'])
            ax.plot(merged.source_access_rows, merged.mae, 'o-', color=colors[policy], label=policy.replace('_', ' '))
            ax.set_xlabel('Additional household readings per origin')
            ax.set_ylabel(level.capitalize()+' MAE (kWh / half-hour)')
            ax.grid(alpha=.2)
    p = cost_summary[(cost_summary.population==4194)&(cost_summary.policy=='uncertainty')]
    axes[2].plot(p.active_groups, p.state_bytes/1e6, 'o-', color='#0072B2', label='Incremental retained detail')
    axes[2].plot(p.active_groups, p.retained_bytes/1e6, 's-', color='#D55E00', label='Same queries after eviction')
    uniform = cost_summary[(cost_summary.population==4194)&(cost_summary.policy=='uniform_fine_stream')].state_bytes.iloc[0]
    axes[2].axhline(uniform/1e6, color='#009E73', linestyle='--', label='Streamed all-fine summaries')
    axes[2].set_xlabel('Acquired groups (of 16)'); axes[2].set_ylabel('Accounted posterior state (MB)')
    axes[2].legend(fontsize=7); axes[2].grid(alpha=.2)
    axes[0].legend(fontsize=7)
    fig.suptitle('Accuracy, acquisition and representation are separate tradeoffs')
    fig.tight_layout(); save('accuracy_resource')
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for active, marker in [(2,'o'),(4,'s'),(8,'^')]:
        p = cost_summary[(cost_summary.policy=='uncertainty')&(cost_summary.active_groups==active)].sort_values('population')
        axes[0].plot(p.population, p.source_file_bytes/1e6, marker+'-', label=str(active)+' groups')
        axes[1].plot(p.population, 1000*p.two_rerefine_seconds/2, marker+'-', label=str(active)+' groups')
        axes[2].plot(p.population, p.state_bytes/1e6, marker+'-', label=str(active)+' groups active')
        axes[2].plot(p.population, p.retained_bytes/1e6, marker+'--', alpha=.65)
    axes[0].set_ylabel('Fine provider files read per update (MB)')
    axes[1].set_ylabel('Re-refine one evicted group (ms)')
    axes[2].set_ylabel('State MB: solid active, dashed evicted')
    for ax in axes:
        ax.set_xlabel('Distinct real households'); ax.set_xticks([1024, 2048, 4194]); ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Measured GPU replay costs across nested real-household cohorts (medians)')
    fig.tight_layout(); save('refinement_cost_scale')
    (figures/'PROVENANCE.md').write_text(
        '# Figure provenance\n\nGenerated by `python3 scripts/analyze_refinement.py` from '
        '`results/refinement/replay/{predictions,metrics,costs,access_trace,checks}.csv`. '
        'All plots are exploratory development measurements, not held-out evidence. '
        'Interval shading is the raw fitted Gaussian forecast law, not a confidence band for method superiority. '
        'Repeated policies/cohorts reuse the same observed targets. No image generation is used.\n')
    print(json.dumps(actual, indent=2))


if __name__ == '__main__':
    main()
