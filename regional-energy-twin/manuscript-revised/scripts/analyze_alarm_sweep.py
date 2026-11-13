"""Descriptive alarm-threshold analysis of preserved acquisition traces.

No replay, model loading, GPU work, new calibration, or acquisition modification.
Only paths below manuscript-revised may be written. Historical sources are read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

METHODS = ['M0', 'M1', 'M2', 'M3', 'M4']
LABELS = dict(M0='Aggregate', M1='Probes', M2='Random', M3='Gated', M4='Full fine')
COLORS = dict(M0='#666666', M1='#CC79A7', M2='#E69F00', M3='#D55E00', M4='#009E73')
FAMILIES = ['regional', 'localized', 'cancel_exact', 'cancel_approx', 'delayed', 'ramp']


def alarm_counts(scores, threshold):
    """Strict > matches the deployed alarm; equal scores are not alarms."""
    return int(np.count_nonzero(np.asarray(scores) > threshold))


def control_threshold(scores, ceiling):
    """Observed control order statistic; no event labels or interpolation.

    For n controls and k=floor(n*ceiling), select sorted_control[n-k-1].
    The strict rule admits at most k alarmed updates; ties may admit fewer.
    """
    x = np.sort(np.asarray(scores, dtype=float))
    if not 0 <= ceiling < 1 or not len(x) or not np.isfinite(x).all():
        raise ValueError('Need finite controls and a ceiling in [0,1)')
    k = int(np.floor(len(x)*ceiling))
    return float(x[len(x)-k-1])


def checks():
    # Ties are excluded, zero ceiling admits none, order has no effect.
    assert alarm_counts([0., 1., 1., 2.], 1.) == 1
    assert control_threshold([0., 1., 1., 2.], .5) == 1.
    assert alarm_counts([0., 1., 1., 2.], control_threshold([0., 1., 1., 2.], .5)) == 1
    assert alarm_counts([0., 1., 1., 2.], control_threshold([0., 1., 1., 2.], 0.)) == 0
    assert control_threshold([2., 1., 0., 1.], .5) == 1.
    # Inclusion at lag 6 is consequential; lag 7 is outside the requested window.
    step = np.arange(8)
    scores = np.array([0.,0.,0.,0.,0.,0.,2.,3.])
    assert alarm_counts(scores[(step >= 0) & (step <= 6)], 1.) == 1
    assert alarm_counts(scores[(step >= 0) & (step < 6)], 1.) == 0
    return ['strict_threshold_ties', 'control_only_order_statistic', 'zero_ceiling',
            'input_order_invariance', 'inclusive_lag6_exclusive_lag7']


def main():
    started = time.perf_counter()
    revision = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=revision.parent)
    parser.add_argument('--output', type=Path, default=revision)
    args = parser.parse_args()
    project = args.project.resolve(); output = args.output.resolve()
    if output != revision and revision not in output.parents:
        raise SystemExit('All outputs must remain inside manuscript-revised')
    analysis = output/'analysis'; generated = output/'generated'; figures = output/'figures'
    for folder in [analysis, generated, figures]: folder.mkdir(parents=True, exist_ok=True)
    inputs = ['results/shock/run/alarms.csv.gz', 'results/shock/analysis/audited_alarms.csv.gz',
              'results/shock/run/episodes.json', 'results/shock/calibration.json',
              'results/shock/calibrate/scores.csv', 'results/shock/analysis/episode_detection.csv',
              'results/synthesis/principal_results.csv', 'configs/regional_shock.json',
              'scripts/replay_shock.py', 'scripts/analyze_shock.py',
              'src/evidence_fusion/shock_access.py', 'scripts/analyze_acquisition_comparison.py',
              'results/acquisition/run/alarms.csv.gz', 'results/acquisition/run/episodes.json']
    hashes = {p: hashlib.sha256((project/p).read_bytes()).hexdigest() for p in inputs}
    alarms = pd.read_csv(project/inputs[0])
    audited = pd.read_csv(project/inputs[1])
    assert np.array_equal(alarms[['episode','step','method']].values, audited[['episode','step','method']].values)
    assert np.array_equal(alarms.score.values, audited.score.values)
    assert np.array_equal(alarms.alarm.values, audited.alarm.values)
    meta = pd.read_json(project/'results/shock/run/episodes.json')
    cal = json.loads((project/'results/shock/calibration.json').read_text())
    cfg = json.loads((project/'configs/regional_shock.json').read_text())
    historical = pd.read_csv(project/'results/shock/analysis/episode_detection.csv')
    principal = pd.read_csv(project/'results/synthesis/principal_results.csv')
    a = alarms.merge(meta[['episode','background','family','onset','duration']], on='episode', validate='many_to_one')
    assert a[['episode','step','method']].duplicated().sum() == 0
    assert np.isfinite(a.score).all()
    assert (a.alarm.values == (a.score.values > 1.)).all()
    reconstructed = np.maximum(a.macro_score.values/cal['macro'],
        a.fine_score.values/a.method.map(cal['fine']).values)/a.method.map(cal['joint']).values
    reconstruction_error = float(np.max(abs(reconstructed-a.score.values)))
    assert reconstruction_error < 1e-12
    assert len(meta)==112 and meta.background.nunique()==8
    assert meta.family.isin(FAMILIES).sum()==96 and (meta.family=='none').sum()==8
    assert cfg['detection_limit_steps']==6
    test_names = checks()
    operating=[]; matched=[]; curves=[]; episode_rows=[]; background_rows=[]
    for method in METHODS:
        am = a[a.method==method]
        controls = am[am.family=='none'].sort_values(['background','step'])
        assert len(controls)==384 and controls.groupby('background').size().eq(48).all()
        demand = am[am.family.isin(FAMILIES)]
        rows6 = demand[(demand.step>=demand.onset)&(demand.step<demand.onset+6)]
        rows7 = demand[(demand.step>=demand.onset)&(demand.step<=demand.onset+6)]
        assert rows6.groupby('episode').size().eq(6).all()
        assert rows7.groupby('episode').size().eq(7).all()
        peak6 = rows6.groupby('episode').score.max()
        peak7 = rows7.groupby('episode').score.max()
        assert len(peak6)==96 and len(peak7)==96
        saved = historical[(historical.method==method)&historical.family.isin(FAMILIES)].set_index('episode')
        assert np.array_equal((peak6.loc[saved.index].values>1.), saved.detected.values)
        localized = rows6.assign(localized=rows6.correct_group_alarms>0).groupby('episode').localized.any()
        assert np.array_equal(localized.loc[saved.index].values, saved.correct_group_detected.values)
        published = principal[(principal.cohort=='B')&(principal.method==method)].iloc[0]
        cscore = controls.score.values
        assert alarm_counts(cscore,1.) == int(published.negative_alarms)
        assert int((peak6>1.).sum()) == int(published.detected)
        assert int(localized.sum()) == int(published.localized)
        operating.append(dict(method=method,threshold=1.,control_alarms=alarm_counts(cscore,1.),
            control_updates=len(controls),false_alarm_rate=alarm_counts(cscore,1.)/len(controls),
            original_detected_lags0_5=alarm_counts(peak6,1.),
            requested_detected_lags0_6=alarm_counts(peak7,1.), demand_episodes=96,
            original_localized_lags0_5=int(localized.sum())))
        # Full descriptive sweep includes all relevant control scores and event maxima.
        # This draws the curve only; operating thresholds below use controls alone.
        thresholds = np.unique(np.r_[0., cscore, peak7.values, 1., np.inf])
        previous_c=385; previous_d=97
        for threshold in thresholds:
            c=alarm_counts(cscore,threshold);d=alarm_counts(peak7.values,threshold)
            assert c<=previous_c and d<=previous_d
            previous_c=c;previous_d=d
            curves.append(dict(method=method,threshold=threshold,control_alarms=c,
                control_updates=384,false_alarm_rate=c/384,detected=d,demand_episodes=96,
                event_detection_probability=d/96,detection_first_lag=0,detection_last_lag=6,
                frozen_alarm_threshold=bool(threshold==1.)))
        per_episode = peak7.rename('peak_score_lags0_6').to_frame().join(peak6.rename('peak_score_lags0_5'))
        per_episode = per_episode.join(meta.set_index('episode')[['background','family','onset']])
        for ep, r in per_episode.iterrows():
            episode_rows.append(dict(episode=ep,method=method,background=int(r.background),family=r.family,
                onset=int(r.onset),peak_score_lags0_5=r.peak_score_lags0_5,
                peak_score_lags0_6=r.peak_score_lags0_6,
                frozen_detected_lags0_5=bool(r.peak_score_lags0_5>1),
                frozen_detected_lags0_6=bool(r.peak_score_lags0_6>1)))
        for ceiling in [.02,.05,.10]:
            threshold=control_threshold(cscore,ceiling)
            count=alarm_counts(cscore,threshold); detected=alarm_counts(peak7,threshold)
            assert count<=np.floor(ceiling*384)
            matched.append(dict(method=method,nominal_control_ceiling=ceiling,threshold=threshold,
                control_alarms=count,control_updates=384,false_alarm_rate=count/384,
                detected=detected,demand_episodes=96,event_detection_probability=detected/96,
                controls_equal_threshold=int(np.count_nonzero(cscore==threshold)),
                interpolated=False,threshold_selected_without_event_labels=True))
            for background in range(8):
                bc=controls[controls.background==background]
                be=per_episode[per_episode.background==background]
                assert len(bc)==48 and len(be)==12
                background_rows.append(dict(method=method,nominal_control_ceiling=ceiling,
                    threshold=threshold,background=background,week=background//2,
                    control_alarms=alarm_counts(bc.score,threshold),control_updates=48,
                    detected=alarm_counts(be.peak_score_lags0_6,threshold),demand_episodes=12))
    op=pd.DataFrame(operating); match=pd.DataFrame(matched); curve=pd.DataFrame(curves)
    pd.DataFrame(episode_rows).to_csv(analysis/'alarm_episode_peaks.csv',index=False)
    pd.DataFrame(background_rows).to_csv(analysis/'alarm_background_counts.csv',index=False)
    op.to_csv(analysis/'alarm_frozen_operating_points.csv',index=False)
    match.to_csv(analysis/'alarm_matched_rates.csv',index=False)
    curve.to_csv(analysis/'alarm_threshold_sweep.csv',index=False)
    # The later corrective analysis really did include lag 6. Preserve its distinct
    # original window rather than retroactively changing either panel's results.
    cmeta = pd.read_json(project/'results/acquisition/run/episodes.json')
    cmeta = cmeta[cmeta.phase=='fresh']
    ca = pd.read_csv(project/'results/acquisition/run/alarms.csv.gz').merge(
        cmeta[['episode','background','family','onset']],on='episode',validate='many_to_one')
    window_checks = [dict(cohort='B', method=r.method, published_last_lag=5,
        detected_lags0_5=int(r.original_detected_lags0_5),
        detected_lags0_6=int(r.requested_detected_lags0_6), episodes=96)
        for r in op.itertuples()]
    for method in ['M0','M2','M3','M3b','M4']:
        cm = ca[(ca.method==method)&~ca.family.isin(['none','sensor_fault'])]
        c6 = cm[(cm.step>=cm.onset)&(cm.step<cm.onset+6)].groupby('episode').alarm.any()
        c7 = cm[(cm.step>=cm.onset)&(cm.step<=cm.onset+6)].groupby('episode').alarm.any()
        assert len(c6)==12 and len(c7)==12
        published = principal[(principal.cohort=='C')&(principal.method==method)].iloc[0]
        assert int(c7.sum())==int(published.detected)
        window_checks.append(dict(cohort='C',method=method,published_last_lag=6,
            detected_lags0_5=int(c6.sum()),detected_lags0_6=int(c7.sum()),episodes=12))
    pd.DataFrame(window_checks).to_csv(analysis/'alarm_cohort_window_audit.csv',index=False)
    # Compact table exposes units/denominators in the caption supplied by the paper.
    table=[r'\begin{tabular}{lrrr}\toprule',
           r'Method & 7/384 & 19/384 & 38/384\\\midrule']
    for method in METHODS:
        o=op[op.method==method].iloc[0];m=match[match.method==method].sort_values('nominal_control_ceiling')
        table.append('%s %s & %d & %d & %d \\\\'%(method,LABELS[method],
            *m.detected.astype(int).tolist()))
    table.append(r'\bottomrule\end{tabular}')
    (generated/'alarm_matched_rows.tex').write_text('\n'.join(table)+'\n')
    # Plot retained as supporting analysis; no new figure is required in the paper.
    plt.rcParams.update({'font.size':9,'axes.titlesize':10,'legend.fontsize':8,
                         'pdf.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'regional-revision-alarm'})
    fig,ax=plt.subplots(figsize=(6.8,3.6))
    for method in METHODS:
        c=curve[curve.method==method].sort_values('threshold',ascending=False)
        ax.step(c.false_alarm_rate.values*100,c.event_detection_probability.values*100,where='post',
                color=COLORS[method],label=method+' '+LABELS[method],lw=1.2)
        o=op[op.method==method].iloc[0]
        ax.scatter([100*o.false_alarm_rate],[100*o.requested_detected_lags0_6/96],s=45,
                   marker='o',color=COLORS[method],edgecolor='black',linewidth=.5,zorder=4)
        ax.scatter([100*o.false_alarm_rate],[100*o.original_detected_lags0_5/96],s=55,
                   marker='v',facecolor='none',edgecolor=COLORS[method],linewidth=1,zorder=5)
    ax.axvline(2,color='gray',ls=':',lw=.8)
    ax.set(xlim=(0,15),ylim=(0,80),xlabel='Per-update false-alarm rate on unmodified controls (%)',
           ylabel='Event detection probability (%)\n(lags 0-6 inclusive)',
           title='Fixed acquisitions; alarm-threshold post-processing')
    handles,labels=ax.get_legend_handles_labels()
    handles.extend([Line2D([],[],marker='o',color='black',ls='',markersize=5),
                    Line2D([],[],marker='v',color='black',markerfacecolor='none',ls='',markersize=5)])
    labels.extend(['Frozen threshold, lags 0-6','Published frozen counts, lags 0-5'])
    ax.legend(handles,labels,loc='upper left',ncol=2)
    ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(figures/'alarm_sweep.pdf',metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(figures/'alarm_sweep.svg');plt.close(fig)
    checks_out=dict(checks_passed=test_names+['raw_audited_scores_identical','normalized_score_reconstruction',
        'published_B_6_instant_and_C_7_instant_detections_reproduced','published_localization_flags_reproduced_only_at_frozen_threshold',
        'original_control_rates_reproduced','96_demand_8_background_384_control_denominators',
        'window_row_counts','monotone_threshold_counts','control_budget_bound'],
        normalized_score_max_abs_error=reconstruction_error,
        original_window_code='onset <= step < onset + config.detection_limit_steps; config value 6',
        requested_window='onset <= step <= onset + 6',
        unmodified_control_updates=384,demand_episodes=96,backgrounds=8,weeks=4,
        new_calibration=False,policy_replay=False,acquisition_parameters_changed=False,
        localization_recomputed_at_new_thresholds=False,raw_meter_data_read=False,gpu_used=False,
        elapsed_cpu_job_seconds=time.perf_counter()-started,python=sys.version.split()[0],
        numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__,input_sha256=hashes)
    (analysis/'alarm_checks.json').write_text(json.dumps(checks_out,indent=2)+'\n')
    print(op.to_string(index=False));print(match.to_string(index=False))
    print('Wrote outputs only to',output,'in',checks_out['elapsed_cpu_job_seconds'],'seconds')


if __name__=='__main__':
    main()
