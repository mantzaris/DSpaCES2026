"""Numerical manuscript text; every value is derived from saved run outputs."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .utils import recorded_runtime,write_json


def number(value: float | None,digits: int = 3) -> str:
    return '--' if value is None or not np.isfinite(value) else f'{value:.{digits}f}'


def interval(record: dict) -> str:
    return f"{number(record['mean'])} [{number(record['low'])}, {number(record['high'])}]"


def build(root: Path) -> None:
    coverage=json.loads((root/'results/report-coverage.json').read_text())
    if not coverage['primary_complete']:raise RuntimeError('Cannot write manuscript results from an incomplete primary study')
    if coverage['completed_scoring_configurations']!=25:
        raise RuntimeError('Both graph sensitivities must be included before final manuscript generation')
    for stage in ['quality','global','unscreened','samples','persistence','graphs','directions']:
        status=root/'experiments/sensitivity'/f'{stage}-status.json'
        if not status.exists() or json.loads(status.read_text())['status']!='complete':
            raise RuntimeError('Required sensitivity is incomplete: '+stage)
    destination=root/'manuscript/generated';destination.mkdir(exist_ok=True)
    summaries=json.loads((root/'results/summary.json').read_text())
    pairs=json.loads((root/'results/paired_comparisons.json').read_text())
    datasets=['synthetic','intel','pems'];names={'synthetic':'synthetic','intel':'Intel','pems':'PEMS'}
    def result(dataset,method):return next(s for s in summaries if s['dataset']==dataset and s['method']==method)
    def contrast(dataset,left,right,metric):
        return next(p for p in pairs if p['dataset']==dataset and p['left']==left and p['right']==right and p['metric']==metric)
    entropy=[result(d,'diffusion/entropy') for d in datasets]
    sync=[result(d,'diffusion/synchronization') for d in datasets]
    faults=sum(r['fault_realizations'] for r in entropy);blocks=sum(r['independent_blocks'] for r in entropy)
    recall_h='/'.join(number(r['event_recall']['mean']) for r in entropy)
    recall_s='/'.join(number(r['event_recall']['mean']) for r in sync)
    rates=[r['background_unit_exceedance'] for r in entropy]
    consistent=all(contrast(d,'diffusion/entropy','diffusion/synchronization',m)['low']>0 for d in datasets for m in ['tp','localization_iou'])
    conclusion=('The paired comparisons support an entropy advantage within this protocol.' if consistent else
                'The paired comparisons do not establish a consistent entropy advantage in both detection and localization.')
    abstract=(r'We test whether local correlation-spectrum entropy trajectories improve sensor-group monitoring when compared with a conditional joint normal reference. '
              r'The formulation combines entropy level and change, explicit missing-data abstention, spatial scan calibration and inspectable sensor participation. '
              r'A compact graph-conditioned diffusion model and a context-only block bootstrap supply matched entropy, synchronization and combined comparisons; full correlation matrices, raw residuals, CUSUM and a GDN adaptation are also evaluated. '
              f'One synthetic benchmark and semi-synthetic evaluation on Intel Lab and PEMS-BAY recordings provide {faults} scheduled fault injections in {blocks} recording blocks, with three training seeds. '
              f'At nominal per-issuance $\\alpha=.10$, diffusion entropy recall is {recall_h}, versus {recall_s} for synchronization, in dataset order. '
              +conclusion+' '
              f'Untouched entropy exceedance ranges from {min(rates):.3f} to {max(rates):.3f}, so equal nominal budgets do not establish equal realized false-alert rates. '
              r'Analytical bounds and an exact matched-correlation counterexample delimit the information captured by entropy. Saved predictions, calibrated diagnostics and a replay dashboard make the resulting attention signals auditable without claiming verified field failures or causal explanations.')
    (destination/'abstract.tex').write_text(abstract+'\n')

    lines=[r'\input{generated/main-table.tex}',
           r'\subsection{Detection, localization and the feature hypothesis}',
           f'The full primary study contains {faults} scheduled fault injections within {blocks} recording blocks. '
           r'All three seeds are complete; the three synthetic node counts remain configurations of one benchmark. '
           r'Table~\ref{tab:main} gives the reference-by-feature comparison and required baselines. '
           r'Figure~\ref{fig:performance} includes whole-block uncertainty and the measured direction strata. '+conclusion]
    lines.append('The mean fraction of eligible diffusion-entropy group windows is '+
                 '/'.join(number(r['eligible_fraction']['mean']) for r in entropy)+
                 ' in dataset order. Intel performance is therefore dominated by limited sample support. '
                 'The shared quality rule does not force identical eligibility when bootstrap donors have additional missing values.')
    for d in datasets:
        h=result(d,'diffusion/entropy');s=result(d,'diffusion/synchronization')
        delta=contrast(d,'diffusion/entropy','diffusion/synchronization','tp')
        loc=contrast(d,'diffusion/entropy','diffusion/synchronization','localization_iou')
        lines.append(f"For {names[d]}, the paired entropy-minus-synchronization recall difference is {interval(delta)}, and its IoU difference is {interval(loc)}. "
                     f"Entropy misses {h['missed_event_seed_pairs']} event--seed pairs; conditional detected-event IoU is {number(h['conditional_detected_localization']['iou'])}, "
                     f"versus {number(h['localization_iou']['mean'])} when misses count as zero. The mean oracle candidate-group IoU is {number(h['oracle_mean_iou'])}.")
    lines.extend([r'The comparison is against specific scoring rules. Entropy cannot add information to the full correlation matrix from which it is computed; an empirical difference from the Frobenius baseline does not contradict this fact. Type macros, seed variability, event precision, sensor-level precision/recall/F1, topology/severity/duration strata and every raw PR curve are retained in the artifact.',
                  r'\begin{figure*}[t]\centering\includegraphics[width=.97\textwidth]{performance.pdf}',
                  r'\caption{At nominal $\alpha=.10$, top panels show overall event recall with whole-block 95\% intervals; open up/down markers show observed-increase/decrease strata. B denotes bootstrap, D diffusion, H entropy and S synchronization. Bottom panels are paired differences in unconditional localization IoU, with 95\% intervals; positive favors the left-hand feature set.}\label{fig:performance}\end{figure*}',
                  r'\subsection{Reference fidelity and calibration}'])
    fidelity=pd.DataFrame(json.loads((root/'experiments/fidelity-extra.json').read_text())['rows'])
    fidelity_means=fidelity.groupby(['dataset','reference']).mean(numeric_only=True)
    table=[r'\begin{table}[t]\centering\caption{Defined values from six fixed untouched units and three seeds. Raw/H cov. are 90\% interval coverages on identical support for both references; R error is mean element RMSE. Energy/covariance errors and support counts are retained. Undefined common support is shown as --.}\label{tab:fidelity}\small',
           r'\begin{tabular}{llrrr}\toprule Data & Reference & Raw cov. & H cov. & R error\\\midrule']
    for name,label in [('synthetic64','Syn. 64'),('intel','Intel'),('pems','PEMS')]:
        for ref in ['bootstrap','diffusion']:
            row=fidelity_means.loc[(name,ref)]
            table.append(f"{label} & {'Block' if ref=='bootstrap' else 'Diffusion'} & {number(row.common_raw_coverage90)} & {number(row.common_entropy_coverage90)} & {number(row.common_correlation_element_rmse)}"+r' \\')
    table.extend([r'\bottomrule\end{tabular}\end{table}'])
    (destination/'fidelity-table.tex').write_text('\n'.join(table)+'\n')
    lines.append(r'\input{generated/fidelity-table.tex}')
    lines.append(r'Table~\ref{tab:fidelity} tests distributions, not just forecast means. The raw energy score uses independent ensemble pairs and a Euclidean norm normalized by the square root of the jointly observed dimension count. Comparing references uses their common support; an empty support has no score. Covariance errors use training-scaled units. Entropy/change coverage, interval width, correlation/covariance errors and raw energy scores are saved separately, with their support counts. These compact forecasts are model-based references, not known healthy trajectories.')
    row=fidelity_means.loc[('synthetic64','diffusion')]
    lines.append(f"Raw marginal coverage does not ensure organizational fidelity: synthetic diffusion raw coverage is {row.common_raw_coverage90:.3f}, but H coverage is {row.common_entropy_coverage90:.3f}. "
                 r'This limits the reference model, but model error alone does not invalidate the rank theorem: that result permits any fixed scoring rule under exchangeability. Distribution differences across calibration and test units must be considered separately.')
    minimum={d:json.loads((root/'experiments/full'/f'score-{"synthetic64" if d=="synthetic" else d}-physical-17/status.json').read_text())['calibration_units'] for d in datasets}
    lines.append('Calibration has '+', '.join(f"{minimum[d]} units for {names[d]}" for d in datasets)+
                 r'; Intel therefore cannot attain $\alpha=.05$. For diffusion entropy at $.10$, untouched per-issuance exceedance is '+
                 '/'.join(number(r['background_unit_exceedance']) for r in entropy)+
                 ', while legitimate-transition exceedance is '+ '/'.join(number(r['transition_unit_exceedance']) for r in entropy)+
                 r'. These are empirical background rates. Native recordings lack adjudicated failure labels, and comparable nominal thresholds do not mean matched realized false-alert rates. Thus a recall advantage across reference models alone would not demonstrate superiority at equal false-alarm rates.')
    null=json.loads((root/'results/calibration-null-diagnostic.json').read_text())
    def nullrate(rho,gap):return next(r['exceedance'] for r in null['rows'] if r['rho']==rho and r['gap']==gap and r['alpha']==.1)
    lines.append(f"A separate {null['replicates']:,}-replicate diagnostic fixes the score to the maximum absolute value of four stationary AR(1) sensors. At nominal .10 with 32 calibration units, exceedance is {nullrate(0.,1):.3f} for IID units and {nullrate(.99,1):.3f} at autocorrelation .99. Spacing by 32 steps gives {nullrate(.99,32):.3f} for this specified process; it is not a validity theorem for gapped real data.")
    retrospective=json.loads((root/'results/retrospective_budgets.json').read_text())
    empirical_budget_table(retrospective,destination)
    lines.extend([r'\input{generated/empirical-budget-table.tex}',
                  r'Table~\ref{tab:empirical} is a post-primary diagnostic at common empirical budgets. For each method/configuration, the largest attainable rank threshold with untouched-control exceedance at most .10 is chosen, pooling seeds and using no injected labels. Whole-block paired resampling reselects thresholds. The same controls select and describe these points: this is retrospective comparison, not prospective false-alert validation, and finite rank resolution often leaves unused budget. Primary thresholds remain unchanged.'])
    for d in ['synthetic','pems']:
        delta=next(p for p in retrospective['paired_contrasts'] if p['dataset']==d and p['empirical_budget']==.1 and
                   p['left']=='diffusion/entropy' and p['right']=='diffusion/synchronization' and p['metric']=='event_recall')
        lines.append(f"At this empirical budget, the paired H-minus-S recall difference for {names[d]} is {interval(delta)}.")
    lines.append(r'For Intel, the displayed methods have no nonzero attainable rank threshold within the .10 control budget; their zero recall is a resolution/shift limitation, not evidence of equal feature quality.')
    lines.extend([r'\subsection{Ablations, quality and persistent history}',r'\input{generated/ablation-table.tex}'])
    ablation_table(root,destination)
    observability=json.loads((root/'experiments/sensitivity/injection-observability.json').read_text())['rows']
    absent=[r for r in observability if not r['observable_intervention']]
    lines.append(f"The post-run measurement audit finds {len(absent)}/{len(observability)} scheduled interventions with no modified finite value or newly removed observation in the named fault set, at a $10^{{-6}}$ training-scaled tolerance. These remain in the primary denominators; their labels describe scheduled interventions rather than guaranteed visible changes. Sensor coverage and covariance guards therefore limit interpretation of the real-data benchmark.")
    sample_frame=pd.read_csv(root/'results/sample_count_metrics.csv')
    for name in ['synthetic64','pems']:
        selected=sample_frame[(sample_frame.dataset==name)&(sample_frame.method=='diffusion/entropy')&sample_frame.is_fault]
        recall=selected.groupby('generated_samples').tp.mean()
        lines.append(f"On the identical three-fault limited subset for {name.replace('synthetic64','synthetic 64')}, entropy recall with B=32/64/128 is "+
                     '/'.join(number(recall.loc[b]) for b in [32,64,128])+r'. These small subsets quantify Monte Carlo sensitivity and cost, not a precise ranking of sample budgets.')
    # Further sensitivity paragraphs are emitted from the finished stage files.
    global_result=json.loads((root/'experiments/sensitivity/global-comparison.json').read_text())
    global_rows=pd.DataFrame(global_result['rows']);fault_rows=global_rows[global_rows.is_fault]
    means=fault_rows.groupby('arm')[['tp','localization_iou']].mean()
    lines.append(f"The global/local sensitivity uses the same W={global_result['window']} bootstrap forecasts and calibration budget at 64 nodes. Local/global recall is {means.loc['local','tp']:.3f}/{means.loc['global','tp']:.3f}, and IoU is {means.loc['local','localization_iou']:.3f}/{means.loc['global','localization_iou']:.3f}. "
                 f"The first valid issuance is {global_result['first_observation_relative_to_onset']} samples after onset, so short events may finish first. "
                 r'The global sample-support rule requires longer windows: the other configurations cannot supply enough calibration units to attain .10 under their original split/episode boundaries. This is a feasibility and longer-window comparison, not an isolated comparison with the primary shorter windows.')
    quality=json.loads((root/'experiments/sensitivity/quality.json').read_text())
    quality_frame=pd.DataFrame([r for r in quality if 'missing_rate' in r])
    for d in ['synthetic64','intel','pems']:
        q=quality_frame[quality_frame.dataset==d].groupby('missing_rate').eligible_fraction.mean()
        lines.append(f"For {d.replace('synthetic64','synthetic 64')}, the eligible-group fraction falls from {q.loc[0.]:.3f} to {q.loc[.1]:.3f} after 10\% additional entrywise missingness.")
    em=[r for r in quality if 'em_eligible' in r]
    recovered=sum(r['em_eligible'] and not r['complete_case_eligible'] for r in em)
    lines.append(f"Among {len(em)} inspected group windows, the labeled Gaussian covariance-EM sensitivity supplies a PSD estimate in {recovered} cases that the primary rule cannot use; it assumes a Gaussian missing-at-random model and does not inherit the detector's calibration. Separate retained-span light/voltage features and their coverage are preserved in the Intel auxiliary audit. Quality-hybrid outcomes remain separate from entropy-only results.")
    persistence=pd.DataFrame(json.loads((root/'experiments/sensitivity/persistence.json').read_text())['rows'])
    late=persistence[(persistence.time>=360)&(persistence.time<480)].groupby('reference')[['entropy_max','raw_max']].mean()
    lines.append('In the long-fault sensitivity, mean late-event entropy maxima for contaminated, paired-clean and frozen-earlier histories are '+
                 '/'.join(number(late.loc[r,'entropy_max']) for r in ['contaminated','paired_clean','frozen_earlier'])+
                 r'. These are sensitivity scores, not newly calibrated decisions. The intervention changes the conditioning history; a historical reference need not remain useful after a persistent regime change. The unscreened-training fidelity comparison is also retained, rather than assuming the real training data are healthy.')
    lines.extend([r'\begin{figure*}[t]\centering\includegraphics[width=.97\textwidth]{cases.pdf}',
                  r'\caption{Two fixed saved injections at 64 nodes. The shaded red span is the true 12-sample event; vertical lines mark onset. Filled H markers are issuance levels and open markers their measured lagged levels, since $W/4$ need not equal the alert stride. Reference bands/medians share the same generated blocks. The dashed score line is the strict scan threshold. Groups are selected by signed measured change among candidates overlapping the injected set, solely for illustration; neither displayed group crosses the scan threshold during the event.}\label{fig:cases}\end{figure*}',
                  r'\begin{figure*}[t]\centering\includegraphics[width=.97\textwidth]{spatial.pdf}',
                  r'\caption{Saved-case spatial membership and signed residual traces. Black outlines mark known injected sensors; triangles mark the displayed group. The heatmap shows H minus expected H, which differs from the actual slope used for the up/down node markers. Group locality is predefined, not a discovered cause.}\label{fig:spatial}\end{figure*}',
                  r'\subsection{Computational cost and operational delay}'])
    benchmark=json.loads((root/'experiments/benchmark.json').read_text());costs=benchmark['detector']
    p50=[x['complete_detector']['p50_seconds'] for x in costs];p95=[x['complete_detector']['p95_seconds'] for x in costs]
    memory=max(x['peak_gpu_bytes'] for x in costs)/2**20
    kernel=benchmark['kernels'];ratio=kernel['cpu_float32']['p50_seconds']/kernel['gpu_float32']['p50_seconds']
    lines.append(f"On the RTX A6000, complete-detector p50 latency ranges from {min(p50):.3f} to {max(p50):.3f} s per issuance, with p95 {min(p95):.3f}--{max(p95):.3f} s and peak allocated memory {memory:.1f} MiB. "
                 f"Training, scoring and required GPU-enabled audits record {recorded_runtime(root)/3600:.2f} stage-hours within the four-hour ceiling. "
                 f"For the identical 128-window, 96-row, 24-sensor measurement batch, CPU float32/GPU float32 p50 time is {ratio:.2f}; this is a kernel comparison, not an end-to-end CPU speedup claim. The CPU uses four Torch threads. "
                 r'Model-only and complete-pipeline throughput, p50/p95, hardware/software and sample-count tradeoffs are saved. Serial computation is added to timestamp delays in the artifact; issuance spacing and window availability dominate these sub-second/second execution costs.')
    lines.extend([r'\begin{figure*}[t]\centering\includegraphics[width=.97\textwidth]{calibration-cost.pdf}',
                  r'\caption{Empirical untouched exceedance, synchronized execution timing, detected-event delay and generated-sample cost. Calibration is per issuance; missed events are excluded only from the delay boxplots and are counted in recall/localization. B-cost timing includes the full comparison pipeline on the same limited event subset.}\label{fig:cost}\end{figure*}'])
    (destination/'results.tex').write_text('\n\n'.join(lines)+'\n')
    ending=(conclusion+' '+r'The exact counterexample shows that entropy can distinguish correlation structures sharing simple synchronization summaries, while its invariances prevent sign, sensor-order or causal interpretation. '
            r'In this compact forecasting study, reference fidelity, calibration shift, sample support and the group library constrain practical detection. Equal nominal rank thresholds do not establish equal physical false-alarm rates. '
            r'The useful deliverable is an auditable monitoring formulation and measured comparison, with explicit abstention and honest cause labels. Stronger predictive references and more representative calibration require new prospective validation before deployment claims.')
    (destination/'conclusion.tex').write_text(ending+'\n')
    write_json(root/'results/manuscript-claims.json',{'fault_realizations':faults,'recording_blocks':blocks,
               'consistent_entropy_advantage_supported':consistent,'entropy_recall':[r['event_recall'] for r in entropy],
               'synchronization_recall':[r['event_recall'] for r in sync],'untouched_exceedance':rates,
               'evidence_files':['summary.json','paired_comparisons.json','retrospective_budgets.json','calibration-null-diagnostic.json','case-selection.json',
                                 '../experiments/fidelity-extra.json','../experiments/benchmark.json'],
               'qualification':'Conclusions apply to this compact model, forecast lead, injected taxonomy and finite calibration design; no verified real failures or usability study.'})


def empirical_budget_table(record: dict,destination: Path) -> None:
    lines=[r'\begin{table*}[t]\centering\caption{Retrospective comparison at untouched-control issuance budgets of at most .10. Each cell is event recall / unconditional IoU / achieved background exceedance. Thresholds use reused test controls, so these are descriptive operating points, not deployment guarantees.}\label{tab:empirical}\small',
           r'\begin{tabular}{lccc}\toprule Method & Synthetic & Intel & PEMS\\\midrule']
    methods=[('bootstrap/entropy','Bootstrap H'),('bootstrap/synchronization','Bootstrap S'),('bootstrap/combined','Bootstrap H+S'),
             ('diffusion/entropy','Diffusion H'),('diffusion/synchronization','Diffusion S'),('diffusion/combined','Diffusion H+S'),
             ('diffusion/matrix','Diffusion full R'),('gdn','GDN adaptation')]
    for method,label in methods:
        entries=[]
        for dataset in ['synthetic','intel','pems']:
            row=next(r for r in record['summaries'] if r['method']==method and r['dataset']==dataset and r['empirical_budget']==.1)
            entries.append(' / '.join(number(v) for v in [row['event_recall']['mean'],row['localization_iou']['mean'],row['untouched_exceedance']]))
        lines.append(label+' & '+' & '.join(entries)+r' \\')
    lines.extend([r'\bottomrule\end{tabular}\end{table*}'])
    (destination/'empirical-budget-table.tex').write_text('\n'.join(lines)+'\n')


def ablation_table(root: Path,destination: Path) -> None:
    frame=pd.read_csv(root/'results/event_metrics.csv.gz')
    frame=frame[(frame.alpha==.1)&(frame.seed==17)&frame.is_fault]
    directions=pd.DataFrame(json.loads((root/'experiments/sensitivity/directions.json').read_text())['rows'])
    directions=directions[(directions.seed==17)&(directions.reference=='diffusion')&directions.is_fault]
    subsets=pd.read_csv(root/'results/group_window_ablations.csv')
    subsets=subsets[(subsets.method=='diffusion/entropy')&subsets.is_fault]
    datasets=['synthetic','intel','pems']
    def subset(data,dataset):
        return data[data.dataset.str.startswith('synthetic')] if dataset=='synthetic' else data[data.dataset==dataset]
    rows=[]
    for method,label in [('entropy','H + ΔH'),('level','H level only'),('higher','Higher than expected'),('lower','Lower than expected')]:
        row=[number(subset(frame,d)[(subset(frame,d).graph=='physical')&(subset(frame,d).method=='diffusion/'+method)].tp.mean()) for d in datasets]
        rows.append((label,row))
    for rule,label in [('actual_increase_only','Actual increase only'),('actual_decrease_only','Actual decrease only')]:
        rows.append((label,[number(subset(directions,d)[subset(directions,d).direction_rule==rule].tp.mean()) for d in datasets]))
    for graph,label in [('removed','Graph conditioning removed'),('shuffled','Graph conditioning shuffled')]:
        rows.append((label,[number(subset(frame,d)[(subset(frame,d).graph==graph)&(subset(frame,d).method=='diffusion/entropy')].tp.mean()) for d in datasets]))
    for field,values,label in [('size',[6,12,24],'Group size 6 / 12 / 24'),('window',[24,48,96],'Window 24 / 48 / 96')]:
        rows.append((label,[' / '.join(number(subset(subsets,d)[(subset(subsets,d).feature==field)&(subset(subsets,d).value==v)].tp.mean()) for v in values) for d in datasets]))
    lines=[r'\begin{table*}[t]\centering\caption{Diffusion-entropy ablation recall at nominal $\alpha=.10$, seed 17 throughout. Each restricted family has its own calibration maxima; the localization budget stays fixed. Last two rows list the three labeled settings in order.}\label{tab:ablations}\small',
           r'\begin{tabular}{lccc}\toprule Setting & Synthetic & Intel & PEMS\\\midrule']
    for label,values in rows:
        label=label.replace('ΔH',r'$\Delta H$')
        lines.append(label+' & '+' & '.join(values)+r' \\')
    lines.extend([r'\bottomrule\end{tabular}\end{table*}'])
    (destination/'ablation-table.tex').write_text('\n'.join(lines)+'\n')
