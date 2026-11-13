"""Regenerate only Figure 2 from saved values, adding the reviewer annotation.

No forecasting, fitting, acquisition or threshold selection is run. Input paths are
explicit; all output paths are restricted to the revision directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REVISION = Path(__file__).resolve().parents[1]
COLORS = dict(M0='#666666', M3='#D55E00', M4='#009E73')
LABELS = dict(M0='Aggregate', M3='Gated', M4='Full fine')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=REVISION.parent)
    parser.add_argument('--output', type=Path, default=REVISION)
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    assert output == REVISION or REVISION in output.parents, 'Outputs must remain inside manuscript-revised'
    start = time.monotonic()
    paths = {
        'example': project/'results/shock/figure_common_support.csv',
        'trace': project/'results/acquisition/diagnostic/steps.csv.gz',
        'calibration': project/'results/shock/calibration.json',
        'original_plot_script': project/'scripts/build_regional_study_results.py',
    }
    example = pd.read_csv(paths['example'])
    steps = pd.read_csv(paths['trace'])
    cal = json.loads(paths['calibration'].read_text())
    trace = steps[steps.episode=='b00_cancel_exact_3.0'].sort_values('step')
    control = steps[(steps.family=='none') & (steps.background==0)].sort_values('step')
    assert len(trace)==len(control)==48
    assert np.array_equal(trace.step.values, control.step.values)
    onset = int(trace.onset.iloc[0])
    duration = int(trace.duration.iloc[0])
    base = example[(example.horizon==2) & (example.method=='M0')].sort_values('step')
    x = (base.step-onset)*.5
    xt = (trace.step-onset)*.5
    after = trace[trace.step>=onset+duration]
    peak = after.loc[after.best_score.idxmax()]
    control_peak = control[control.step==peak.step].iloc[0]
    assert float(peak.best_score)==float(control_peak.best_score)
    assert peak.step>=onset+duration and peak.best_score>cal['trigger']

    plt.rcParams.update({'font.size':8.5, 'axes.titlesize':9, 'legend.fontsize':8,
                         'pdf.fonttype':42, 'svg.fonttype':'none', 'svg.hashsalt':'dspaces-camera-ready-figure2',
                         'axes.spines.top':False, 'axes.spines.right':False})
    fig, axs = plt.subplots(2,2,figsize=(7.0,4.3),sharex=True)
    plotted = []
    def plot(ax, xs, ys, name, **kwargs):
        line, = ax.plot(np.asarray(xs), np.asarray(ys), **kwargs)
        # Protect every pre-existing data curve against unintended coordinate edits.
        assert np.array_equal(line.get_xdata(), np.asarray(xs), equal_nan=True)
        assert np.array_equal(line.get_ydata(), np.asarray(ys), equal_nan=True)
        plotted.append(dict(name=name, points=len(xs),
                            x_sha256=hashlib.sha256(np.asarray(xs,dtype=np.float64).tobytes()).hexdigest(),
                            y_sha256=hashlib.sha256(np.asarray(ys,dtype=np.float64).tobytes()).hexdigest()))
        return line

    plot(axs[0,0], x, base.current_region, 'regional observed sum', color='black')
    axs[0,0].set_ylabel('Observed regional sum (kWh)')
    axs[0,0].set_title('(a) All 16 injected group sums are zero')
    plot(axs[0,1], x, base.current_plus, 'positive household mean', label='Positive-shift meters',color='#0072B2')
    plot(axs[0,1], x, base.current_minus, 'negative household mean', label='Negative-shift meters',color='#D55E00')
    axs[0,1].set_ylabel('Observed local mean (kWh)')
    axs[0,1].legend(loc='upper right',fontsize=7)
    axs[0,1].set_title('(b) Real background plus paired shifts')
    for method in ['M0','M3','M4']:
        a = example[(example.horizon==2)&(example.method==method)].sort_values('step')
        plot(axs[1,0], (a.step+2-onset)*.5, a.forecast_plus, method+' forecast',
             color=COLORS[method],label=method+' '+LABELS[method])
    plot(axs[1,0], x+1, base.target_plus, 'observed forecast target',color='black',label='Observed target',lw=1)
    axs[1,0].set_ylabel('Positive-set mean (kWh)')
    axs[1,0].set_title('(c) One-hour forecasts, target time')
    axs[1,0].legend(ncol=2,fontsize=7)
    plot(axs[1,1], xt, trace.best_score, 'shock maximum acquisition score',label='Largest acquisition score',color=COLORS['M3'])
    plot(axs[1,1], xt, control.best_score.values, 'paired background maximum acquisition score',label='Paired background',color='#666666',ls=':',lw=1)
    axs[1,1].axhline(cal['trigger'],ls='--',color='black',label='Acquisition gate')
    axs[1,1].scatter(np.asarray(xt[trace.probe_hits>0]),np.zeros((trace.probe_hits>0).sum()),
                     marker='|',s=70,color='#0072B2',label='Affected probe read')
    axs[1,1].set_ylabel('Score')
    axs[1,1].set_title('(d) Information observed; schedule unchanged')
    axs[1,1].legend(fontsize=6.8,loc='upper left')
    for ax in axs.flat:
        ax.axvspan(0,duration*.5,color='gray',alpha=.10)
        ax.axvline(0,color='gray',lw=.7)
    axs[1,0].set_xlabel('Hours relative to onset')
    axs[1,1].set_xlabel('Hours relative to onset')
    fig.tight_layout()
    original_limits = [(ax.get_xlim(), ax.get_ylim()) for ax in axs.flat]
    # The peak lies outside the disturbance. The two recorded maxima coincide;
    # "both runs" refers to the shock episode and its paired unmodified background.
    axs[1,1].annotate('After event;\nboth runs',
        xy=((float(peak.step)-onset)*.5, float(peak.best_score)), xytext=(20,23),
        ha='right', va='center', fontsize=7.3,
        arrowprops=dict(arrowstyle='->',lw=.8,color='#333333'),
        bbox=dict(boxstyle='round,pad=.15',fc='white',ec='none',alpha=.95))
    assert original_limits == [(ax.get_xlim(), ax.get_ylim()) for ax in axs.flat]
    figures = output/'figures'; figures.mkdir(exist_ok=True)
    analysis = output/'analysis'; analysis.mkdir(exist_ok=True)
    internal = output/'internal'; internal.mkdir(exist_ok=True)
    for ext in ['pdf','svg']:
        fig.savefig(figures/('transparent_episode.'+ext),bbox_inches='tight')
    fig.savefig(internal/'figure2_preview.png',dpi=180,bbox_inches='tight')
    plt.close(fig)
    report = dict(
        purpose='Figure 2(d) annotation only; all pre-existing curve coordinates, gate, probes and disturbance support preserved.',
        episode='b00_cancel_exact_3.0', background_episode=str(control.episode.iloc[0]),
        onset_step=onset, duration_steps=duration, disturbance_end_hours=duration*.5,
        later_peak_step=int(peak.step),later_peak_hours=(float(peak.step)-onset)*.5,
        peak_shock_score=float(peak.best_score),peak_background_score=float(control_peak.best_score),
        peak_scores_equal=True, acquisition_gate=float(cal['trigger']),
        annotation='After event; both runs', input_sha256={str(p.relative_to(project)):digest(p) for p in paths.values()},
        plotted_curves=plotted, original_axis_limits=original_limits,
        runtime_seconds=time.monotonic()-start, gpu_work=False,
        original_source='scripts/build_regional_study_results.py, Figure 2 block; reproduced without executing its hard-coded writers.')
    (analysis/'figure_annotation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['episode','disturbance_end_hours','later_peak_hours','peak_shock_score','peak_background_score','runtime_seconds']},indent=2))


if __name__=='__main__':
    main()
