"""Refresh inline numerical content in paper.tex and its frozen-results ledger."""
from pathlib import Path
import json
import math
import re
import numpy as np
import pandas as pd
from iot_entropy.extension_reporting import read_json
from iot_entropy.utils import write_json

root=Path(__file__).resolve().parents[1];out=root/'results/extension-v2'
dest=root/'manuscript/generated-v2';dest.mkdir(exist_ok=True,parents=True)
manifest=read_json(out/'report-manifest.json');assert manifest['complete']
lookup={(r['dataset'],r['method']):r for r in read_json(out/'summary.json')}
pairs=read_json(out/'paired.json')
def value(d,m,k='recall'):
    x=lookup[d,m][k];return x['mean'] if isinstance(x,dict) else x
def n(x):return f'{x:.3f}'
def sci_upper(x):
    exponent=math.floor(math.log10(x));mantissa=math.ceil(x/10**exponent*10)/10
    return rf'{mantissa:.1f}\times10^{{{exponent}}}'
def v(d,m,k='recall'):return n(value(d,m,k))
def contrast(d,a,b,metric='tp'):
    return next(r for r in pairs if (r['dataset'],r['a'],r['b'],r['metric'])==(d,a,b,metric))
def ci(d,a,b,metric='tp'):
    r=contrast(d,a,b,metric);return f"{r['mean']:+.3f} [{r['low']:+.3f}, {r['high']:+.3f}]"
def figure(name,caption,label,wide=True):
    env='figure*' if wide else 'figure';width=r'\textwidth' if wide else r'\columnwidth'
    return '\n'+rf'\begin{{{env}}}[!tb]\centering\includegraphics[width={width}]{{{name}.pdf}}'+'\n'+rf'\caption{{{caption}}}\label{{fig:{label}}}\end{{{env}}}'+'\n'
diag=pd.read_csv(out/'diagnostics.csv.gz');diag=diag[diag.scale==1].groupby('scenario').mean(numeric_only=True)
theory=read_json(out/'theory-checks.json')
fidelity=pd.DataFrame(read_json(out/'paired-reference-fidelity.json'))
fid=fidelity.groupby(['dataset','reference']).mean(numeric_only=True)
rate=pd.read_csv(out/'retrospective-operating-points.csv.gz');rate['dataset']=rate.configuration.map(lambda x:'synthetic' if x.startswith('synthetic') else x)
rate=rate[rate.cap==.1].groupby(['dataset','method']).mean(numeric_only=True)
mechanism=pd.read_csv(out/'observability-strata.csv.gz')
def mechanism_value(d,m,kind,k='recall'):
    return float(mechanism[(mechanism.dataset==d)&(mechanism.method==m)&(mechanism.stratum=='kind')&(mechanism.value==kind)].iloc[0][k])

abstract=rf'''Spatial covariance and within-sensor temporal order describe different aspects
of IoT behavior. We compare local correlation-spectrum, permutation and sample
entropy with conventional spatial and temporal statistics under joint block-bootstrap
and graph-conditioned diffusion references. A frozen extension evaluates
{manifest['fault_realizations']} fault realizations on {manifest['recording_or_simulation_blocks']} simulation/recording blocks with three model seeds,
using one synthetic benchmark and two semi-synthetic real-data benchmarks.
Aligned diagnostics verify that time reordering can preserve covariance while
changing temporal entropy; autocorrelation also detects this distinction.
Results depend on support, reference and calibration. On Intel, bootstrap temporal
entropy achieves recall {v('intel','bootstrap/T')} versus {v('intel','bootstrap/TB')} for the conventional temporal
scan, with respective background exceedance {v('intel','bootstrap/T','background_exceedance')} and {v('intel','bootstrap/TB','background_exceedance')}.
Adding entropy to the conventional combined scan increases synthetic bootstrap
recall by {n(contrast('synthetic','bootstrap/BST','bootstrap/B')['mean'])}; other dataset/reference combinations show no recall increase.
Shared-support fidelity exposes substantial diffusion entropy miscoverage.
No consistent overall advantage is established for either entropy or the
generative reference. These exploratory results distinguish feature information
from estimator availability and decision performance, without claiming equivalence.
'''
results=rf'''\subsection{{Primary comparisons and incremental benefit}}
Table~\ref{{tab:main}} reports all scheduled events; Fig.~\ref{{fig:performance}}
adds paired block intervals. RQ1 has a mixed answer. Synthetic diffusion S
has lower recall than SB by {ci('synthetic','diffusion/S','diffusion/SB')}; its
IoU difference is {ci('synthetic','diffusion/S','diffusion/SB','iou')}.
Intel diffusion S/SB recall is {v('intel','diffusion/S')}/{v('intel','diffusion/SB')}, but their background
exceedances are {v('intel','diffusion/S','background_exceedance')}/{v('intel','diffusion/SB','background_exceedance')}.
PEMS bootstrap S appears stronger than SB at nominal alpha
({v('pems','bootstrap/S')} versus {v('pems','bootstrap/SB')} recall), with background rates
{v('pems','bootstrap/S','background_exceedance')} versus {v('pems','bootstrap/SB','background_exceedance')}.
Under the descriptive test-control cap .10, corresponding recalls become
{n(rate.loc[('pems','bootstrap/S'),'recall'])} and {n(rate.loc[('pems','bootstrap/SB'),'recall'])}, at attainable rates
{n(rate.loc[('pems','bootstrap/S'),'achieved_background'])} and {n(rate.loc[('pems','bootstrap/SB'),'achieved_background'])}.
Thus a nominal-threshold ranking is not an isolated test of feature information.
The retrospective analysis does not validate a deployable threshold.

For RQ3, synthetic bootstrap T/TB recall is {v('synthetic','bootstrap/T')}/{v('synthetic','bootstrap/TB')},
with paired difference {ci('synthetic','bootstrap/T','bootstrap/TB')}; unconditional IoU is
{v('synthetic','bootstrap/T','iou')}/{v('synthetic','bootstrap/TB','iou')}.
Intel bootstrap T instead exceeds TB by {ci('intel','bootstrap/T','bootstrap/TB')}
recall, but their achieved background rates differ. PE and SE are not interchangeable:
Intel bootstrap PE/SE recall is {v('intel','bootstrap/PE')}/{v('intel','bootstrap/SE')},
with IoU {v('intel','bootstrap/PE','iou')}/{v('intel','bootstrap/SE','iou')}.
Switching Intel T to diffusion yields recall {v('intel','diffusion/T')} and background
exceedance {v('intel','diffusion/T','background_exceedance')}. PEMS temporal contrasts have wide
block intervals. These results do not establish a universal entropy ordering.

For RQ4, synthetic bootstrap ST improves on S by
{ci('synthetic','bootstrap/ST','bootstrap/S')} recall, but ST minus T is
{ci('synthetic','bootstrap/ST','bootstrap/T')}. Their primary localization rules differ;
fixed-rule alternatives are retained to distinguish feature and ranking effects.
The direct incremental comparison BST minus B is
{ci('synthetic','bootstrap/BST','bootstrap/B')} recall for synthetic bootstrap.
The other five dataset/reference combinations have zero mean recall change at
this operating point. This is not equivalence: different feature information
can be suppressed by a maximum and its recalibrated threshold.
Synthetic bootstrap BST minus B IoU is {ci('synthetic','bootstrap/BST','bootstrap/B','iou')}.
Both use the same combined localization rule. A saved maximum-dominance audit
shows that conventional components usually determine the final scan maximum.
The retained causal GDN adaptation has synthetic/Intel/PEMS recall
{v('synthetic','causal/GDN')}/{v('intel','causal/GDN')}/{v('pems','causal/GDN')}, with background rates
{v('synthetic','causal/GDN','background_exceedance')}/{v('intel','causal/GDN','background_exceedance')}/{v('pems','causal/GDN','background_exceedance')}.
PEMS bootstrap raw residuals reach {v('pems','bootstrap/raw')} recall at
{v('pems','bootstrap/raw','background_exceedance')} background exceedance. These additional
detectors retain their disclosed support and information-access differences.
For bootstrap T, conditional versus unconditional IoU is
{v('synthetic','bootstrap/T','detected_iou')}/{v('synthetic','bootstrap/T','iou')} on synthetic,
{v('intel','bootstrap/T','detected_iou')}/{v('intel','bootstrap/T','iou')} on Intel and
{v('pems','bootstrap/T','detected_iou')}/{v('pems','bootstrap/T','iou')} on PEMS.
Mean best-overlap candidate-group IoU is
{v('synthetic','bootstrap/T','oracle_iou')}/{v('intel','bootstrap/T','oracle_iou')}/{v('pems','bootstrap/T','oracle_iou')},
an oracle library diagnostic rather than an upper bound on every sensor ranking.
{(dest/'main-table.tex').read_text().rstrip()}
'''
results+=figure('performance','Operational performance and unadjusted paired 95\% whole-block intervals. IoU assigns zero to missed events. Equal nominal alpha does not imply equal achieved background rates; four real recording blocks give limited precision.','performance')
results+=rf'''
\subsection{{Information captured and mechanism dependence}}
RQ2 is affirmative as an information distinction, not a superiority claim.
In {theory['replicates']} aligned simulations, joint row permutation changes the evaluated
correlation matrix by at most ${sci_upper(theory['joint_permutation_max_R_error'])}$ (rounded upward).
Mean PE changes from {n(diag.loc['normal','permutation'])} to {n(diag.loc['joint_time_shuffle','permutation'])},
SE from {n(diag.loc['normal','sample'])} to {n(diag.loc['joint_time_shuffle','sample'])},
and ACF1 from {n(diag.loc['normal','acf1'])} to {n(diag.loc['joint_time_shuffle','acf1'])}; spatial entropy is unchanged.
Conversely, copying lowers mean spatial entropy from {n(diag.loc['normal','spatial_H'])}
to {n(diag.loc['cross_sensor_copy','spatial_H'])}, while mean PE changes only from
{n(diag.loc['normal','permutation'])} to {n(diag.loc['cross_sensor_copy','permutation'])}.
Offsets, gains, sign changes, quantization, replay, periodic interference,
irregularity, legitimate transitions and dropout remain separate diagnostic cases.
\emph{{These deliberately constructed experiments are not the primary benchmark.}}

In the heterogeneous synthetic benchmark, bootstrap T/TB recall on flatlining
is {n(mechanism_value('synthetic','bootstrap/T','flatline'))}/{n(mechanism_value('synthetic','bootstrap/TB','flatline'))};
for independent noise it is {n(mechanism_value('synthetic','bootstrap/T','noise'))}/{n(mechanism_value('synthetic','bootstrap/TB','noise'))}.
These are mechanism-specific operational results, not calibrated guarantees at
identical false-alert rates. A rolling window crossing a flatline onset can
remain measurable; a wholly constant window correctly abstains.
The artifact reports paired mechanism, severity, duration, measured-direction
and affected-support strata. Direction is the measured lagged change, not a
fault-name label or deviation from reference expectation. The first scheduled
in-event decision is already 11 samples late. Short events can therefore be
missed before adequate window evidence becomes available.
'''
results+=figure('traces','First prespecified synthetic copy episode: common forecast draws supply all bands. The first affected sensor and the best-overlap candidate group are chosen for illustration only, using injection labels; they are not a detection/localization rule. Shading marks the 12-row injection.','traces')
results+=rf'''
\subsection{{Reference fidelity, support and calibration}}
For RQ5, the shared-support audit in Table~\ref{{tab:fidelity}} distinguishes
reference defects from feature limits. Synthetic64 diffusion spatial-entropy
coverage is {n(fid.loc[('synthetic64','diffusion'),'spatial_entropy_coverage90'])}
versus {n(fid.loc[('synthetic64','bootstrap'),'spatial_entropy_coverage90'])} for bootstrap;
Intel values are {n(fid.loc[('intel','diffusion'),'spatial_entropy_coverage90'])} and
{n(fid.loc[('intel','bootstrap'),'spatial_entropy_coverage90'])}, on only
{n(fid.loc[('intel','bootstrap'),'spatial_common_groups'])} common spatial units per audit issuance on average.
Intel diffusion has better raw energy score
({n(fid.loc[('intel','diffusion'),'energy_score'])} versus {n(fid.loc[('intel','bootstrap'),'energy_score'])}),
yet its sample-entropy coverage is {n(fid.loc[('intel','diffusion'),'sample_96_coverage90'])}
versus {n(fid.loc[('intel','bootstrap'),'sample_96_coverage90'])} for bootstrap.
Good raw marginal behavior does not ensure a faithful temporal functional.
No consistent generative-reference improvement is established, and this compact
long-lead model does not represent all generative approaches.
{(dest/'fidelity-table.tex').read_text().rstrip()}

RQ6 exposes distinct operational and statistical limitations (Fig.~\ref{{fig:availability}}).
Intel S group/window eligibility is {v('intel','bootstrap/S','availability')} under bootstrap
and {v('intel','diffusion/S','availability')} under diffusion; T eligibility is
{v('intel','bootstrap/T','availability')} and {v('intel','diffusion/T','availability')}.
Per-sensor support avoids simultaneous complete rows across a group, but
availability alone does not guarantee calibrated detection. Recalibrating
on common feature support can also change achieved rates: Intel bootstrap
common-support B background exceedance is {v('intel','bootstrap/common/B','background_exceedance')},
compared with {v('intel','bootstrap/B','background_exceedance')} operationally. Varying support and nonexchangeable
calibration/test distributions remain unresolved by nominal rank calibration.

Development selects $q=3$ throughout, delay 1 for synthetic and 2 for both real
datasets; $q=4$ loses support at these short windows. Sample tolerance and group
fraction are saved per configuration. At W96, scale 2 can retain sufficient
templates, whereas scale 4 cannot meet the declared 30-template minimum;
W24 is unsupported for the primary temporal entropies. We report these as
limited multiscale support diagnostics; a separately frozen scale-2 detector
sensitivity is reported below.
'''
results+=figure('availability','Top: operational eligible-group fraction. Middle: untouched-background exceedance at nominal alpha .10. Bottom: development-only support after independent added missingness, W96; spatial is group support, PE/SE per-sensor support. These different denominators are intentional and explicit.','availability')
window_path=out/'window-support.json'
if window_path.exists():
    w=pd.DataFrame(read_json(window_path));done=sorted(w.dataset.unique())
    a=w[w.support_rule=='legacy51'];b=w[w.support_rule=='ceil52']
    join=a.merge(b,on=['dataset','reference','window','family'],suffixes=('_a','_b'))
    maximum=float((join.recall_a-join.recall_b).abs().max())
    results+=rf'''
The seed-17, separately calibrated W48/W96 and 51-versus-52-reference-draw
support sensitivity completed {len(done)} of five configurations.
Across completed configurations, the largest absolute recall change caused
by the support-rounding correction is {n(maximum)}. Window-specific thresholds
and results are retained separately; the 120-step forecast lead is held fixed.
'''
    if len(done)<5:results+='The remaining configuration is explicitly incomplete under the cumulative compute ceiling.\n'
multiscale=read_json(out/'multiscale-calibrated.json')
assert len(multiscale['complete_configurations'])==5
ms=pd.DataFrame(multiscale['summary'])
def scale_contrast(dataset,family):
    row=next(r for r in multiscale['paired'] if (r['dataset'],r['reference'],r['family'],r['metric'])==
             (dataset,'bootstrap',family,'tp'))
    return f"{row['mean']:+.3f} [{row['low']:+.3f}, {row['high']:+.3f}]"
results+=rf'''
The separately frozen, exploratory seed-17 scale-2 comparison keeps W96's
physical history, d=24 and both references. All temporal measurements use the
same two-row averages; spatial measurements remain on the original grid.
Bootstrap T recall changes (scale 2 minus 1, paired block intervals) are
{scale_contrast('synthetic','T')}, {scale_contrast('intel','T')} and
{scale_contrast('pems','T')} for synthetic, Intel and PEMS. Corresponding TB
changes are {scale_contrast('synthetic','TB')}, {scale_contrast('intel','TB')} and
{scale_contrast('pems','TB')}. Full PE/SE, localization, support and achieved
background rates accompany these separately calibrated comparisons in the
artifact. Scale-1 calibration ranks reproduce the independent W96 audit;
S/SB scores are unchanged across scales. This reused-data sensitivity does
not select a new primary scale.
'''
stability=read_json(out/'estimator-stability.json')
def stable(rho,setting,w):
    return next(r for r in stability['rows'] if (r['rho'],r['setting'],r['window'],r['q'],r['tau'])==(rho,setting,w,3,1))
i48=stable(0,'continuous',48);i96=stable(0,'continuous',96);quantized=stable(.8,'quantized_0.5',96)
results+=rf'''
A post-hoc CPU estimator check uses {stability['independent_replicates']} independent unit-variance
Gaussian AR(1) realizations. For independent continuous observations, PE's
between-realization SD is {n(i48['PE']['sd'])} at W48 and {n(i96['PE']['sd'])} at W96.
With fixed sample-entropy tolerance .2, finite supported fractions are
{n(i48['SE']['finite_fraction'])} and {n(i96['SE']['finite_fraction'])}; conditional means therefore require caution.
At $\rho=.8$, quantization to .5-unit steps yields tied-template fraction
{n(quantized['tied_template_fraction'])}. Stable-tie PE eligibility is
{n(quantized['PE']['finite_fraction'])}, versus {n(quantized['drop_ties_PE']['finite_fraction'])} after discarding ties.
This demonstrates sensitivity of the quality/support decision, not a reason
to reinterpret arbitrary tied ordering as confident dynamics.
'''
conclusion=rf'''The comparison establishes different measurement information, but no consistent
overall entropy advantage. Temporal entropy can respond when aligned covariance
is invariant; conventional temporal statistics can respond too. Missing-data
support and reference mismatch materially affect operational results. The
Intel bootstrap temporal-entropy advantage occurs under one frozen calibration
setting with different achieved background rates, while synthetic conventional
temporal localization is stronger. Augmenting conventional features changes
synthetic bootstrap recall by {n(contrast('synthetic','bootstrap/BST','bootstrap/B')['mean'])} and leaves recall unchanged in the
other primary dataset/reference combinations. This limited incremental effect
under a maximum rule does not establish statistical or practical equivalence.
The evaluated diffusion reference shows no consistent improvement over joint
bootstrap; its feature-distribution failures cannot establish that entropy
itself is intrinsically inadequate.
'''
for name,text in [('abstract',abstract),('results',results),('conclusion',conclusion)]:
    (dest/(name+'.tex')).write_text(text)
timing=pd.DataFrame(read_json(out/'isolated-benchmark.json'))
pipeline=timing[timing.reference.notna()].set_index(['dataset','reference'])
kernel=timing[timing.kernel.notna()].set_index('dataset')
completion=read_json(root/'experiments/extension-v2/completion.json')
compute=rf'''Isolated generation-to-score medians for synthetic64, Intel and PEMS are
{n(pipeline.loc[('synthetic64','bootstrap'),'pipeline_total_seconds'])},
{n(pipeline.loc[('intel','bootstrap'),'pipeline_total_seconds'])} and
{n(pipeline.loc[('pems','bootstrap'),'pipeline_total_seconds'])} seconds for bootstrap, versus
{n(pipeline.loc[('synthetic64','diffusion'),'pipeline_total_seconds'])},
{n(pipeline.loc[('intel','diffusion'),'pipeline_total_seconds'])} and
{n(pipeline.loc[('pems','diffusion'),'pipeline_total_seconds'])} for diffusion on the RTX A6000.
They include generation, masks, both windows, feature extraction, scoring and
localization; they exclude GDN, acquisition, loading, disk output, rank lookup and
dashboard rendering. They are not a production end-to-end speedup claim.
Peak allocated memory in these isolated runs is at most
{pipeline.peak_gpu_bytes.max()/2**30:.2f} GiB. The PEMS temporal kernel takes
{n(kernel.loc['pems','cpu_float64'])} seconds on CPU float64 versus
{n(kernel.loc['pems','gpu_float32'])} on GPU float32, transfer excluded;
precision and hardware both differ. Maximum CPU/GPU absolute disagreement
across the benchmark is below ${sci_upper(timing.maximum_absolute_error.max())}$.
The cumulative GPU-stage ledger, including the original study, validation and
failed attempts, records {completion['total_recorded_seconds']/3600:.3f} hours within the explicitly
authorized eight-hour ceiling. All primary, window/support, scale-2 and
fidelity/timing comparisons completed. The earlier four-hour stop is preserved;
CPU reporting and rendering are outside this experiment-stage ledger.
'''
compute+=figure('dashboard_cost','Intel replay localization display (orange outlines: injected sensors, for evaluation only) and isolated generation-to-score timing. The example is the first prespecified copy trial, not a selected success. Timing excludes loading, acquisition and presentation.','dashboard-cost')
(dest/'compute.tex').write_text(compute)
claims=[
 {'claim':'360 fault realizations, 20 blocks, three model seeds; exactly three primary datasets','evidence':['report-manifest.json','data-lineage.json'],'status':'counted; sizes are configurations'},
 {'claim':'Time-row permutation preserves the aligned correlation matrix; temporal entropy and ACF can change','evidence':['theory-checks.json','diagnostics.csv.gz','manuscript/paper.tex: order-invariance proof'],'status':'proved and numerically checked; no rolling-trace invariance claim'},
 {'claim':'Intel bootstrap T recall exceeds TB at the frozen nominal operating point','evidence':['summary.json','paired.json','retrospective-operating-points.csv.gz'],'status':'observed with unequal background rates; exploratory'},
 {'claim':'Only synthetic bootstrap BST increases mean recall over B in primary operational comparisons','evidence':['paired.json','maximum-dominance.json'],'status':'all six dataset/reference pairs checked; no equivalence inference'},
 {'claim':'No consistent overall entropy advantage','evidence':['paired.json','stratified-paired.csv.gz','observability-strata.csv.gz','retrospective-operating-points.csv.gz'],'status':'mixed effects, limited recording blocks, feature/support/calibration distinctions retained'},
 {'claim':'Diffusion has substantial entropy miscoverage without consistent overall improvement','evidence':['paired-reference-fidelity.json','reference-fidelity.csv.gz','paired.json'],'status':'specific compact long-lead reference; common-support audit seed17'},
 {'claim':'Conventional synthetic temporal localization is stronger in the evaluated setting','evidence':['paired.json'],'status':'T minus TB IoU intervals below zero for both references'},
 {'claim':'Both real-data extensions reuse inspected backgrounds and are semi-synthetic','evidence':['data-lineage.json','docs/extension-audit-amendment.md'],'status':'expanded audit corrected the PEMS novelty qualification'},
]
for d in ['synthetic','intel','pems']:
    for ref in ['bootstrap','diffusion']:
        diff=contrast(d,ref+'/BST',ref+'/B')['mean']
        if (d,ref)!=('synthetic','bootstrap'):assert diff==0
assert contrast('synthetic','bootstrap/T','bootstrap/TB','iou')['high']<0
assert contrast('synthetic','diffusion/T','diffusion/TB','iou')['high']<0
write_json(out/'claim-ledger.json',{'abstract_and_conclusion_claims':claims,'automated_numeric_assertions':True,
    'scope':'Every empirical abstract/conclusion assertion is limited to completed saved results; no claim of equivalence, universal inferiority, verified native faults or novel entropy theorem.'})
findings=f'''# Findings from the spatial–temporal extension

The completed primary study establishes no consistent overall advantage for
entropy features or for the evaluated diffusion reference. It also does not
establish that all entropy methods are inferior. All real-background comparisons
are exploratory and semi-synthetic; an expanded audit identified prior inspection
of the selected PEMS blocks in a long-window diagnostic.

## Established within this artifact

- A common row permutation preserves a complete window's correlation matrix.
  PE, sample entropy and ACF can nevertheless change. This is an elementary
  property, not a new theorem or a rolling-trace invariance result.
- All 15 primary configurations completed: {manifest['fault_realizations']} new fault draws,
  {manifest['recording_or_simulation_blocks']} source blocks, three model seeds, exactly three primary datasets.
- Intel bootstrap T recall is {v('intel','bootstrap/T')}, versus {v('intel','bootstrap/TB')} for TB;
  achieved background rates are {v('intel','bootstrap/T','background_exceedance')} and {v('intel','bootstrap/TB','background_exceedance')}.
  This is an operational result at the frozen threshold, not a matched-rate
  statement about intrinsic information.
- Synthetic T minus TB unconditional localization IoU is
  {ci('synthetic','bootstrap/T','bootstrap/TB','iou')} for bootstrap and
  {ci('synthetic','diffusion/T','diffusion/TB','iou')} for diffusion.
- Adding entropy to B changes synthetic bootstrap recall by
  {ci('synthetic','bootstrap/BST','bootstrap/B')}; the other five primary
  dataset/reference combinations show no recall increase at this threshold.
  This does not establish equivalence or feature redundancy.
- Intel spatial group eligibility is {v('intel','bootstrap/S','availability')} / {v('intel','diffusion/S','availability')}
  under bootstrap / diffusion; temporal entropy eligibility is
  {v('intel','bootstrap/T','availability')} / {v('intel','diffusion/T','availability')}.
  Greater eligibility is not sufficient for calibration or accurate localization.
- Shared-support fidelity exposes serious diffusion entropy miscoverage.
  Intel raw energy score nevertheless improves with diffusion, illustrating
  that raw predictive fit and entropy-functional fit are distinct.

## Uncertainty and interpretation

Four recording blocks per real dataset limit uncertainty assessment. Whole-block
intervals retain repeated injections and model seeds; they are exploratory,
unadjusted and not equivalence tests. Original and extension comparisons have
different windows, seeds, support rules and localization, so a change from v1
is not automatically an improvement attributable to temporal entropy.

Nominal alpha .10 produces unequal achieved rates. On PEMS bootstrap, S/SB
recall {v('pems','bootstrap/S')}/{v('pems','bootstrap/SB')} becomes
{n(rate.loc[('pems','bootstrap/S'),'recall'])}/{n(rate.loc[('pems','bootstrap/SB'),'recall'])}
under a retrospective control-rate cap .10. The cap reuses evaluation controls
and is descriptive, not prospective threshold validation.

Mechanism, severity, duration, direction and observability strata are saved.
Use actual measured changes separately from deviations from expectation.
The first decision after onset is 11 samples late; raw pipeline timing does
not remove that observation/stride latency. Participation is not causal attribution.

## Corrections, secondary comparisons and budget

The original study remains at revision b900da1b and in its original namespaces.
Strict feature-pair endpoints and lagged full-matrix change are explicitly
identified extensions/corrections. The inherited 51-of-64 spatial-reference
rounding differs from the ceiling rule (52); separately calibrated correction
checks changed no event recall in all five seed-17 configurations.

The completed ledger records {completion['total_recorded_seconds']:.2f} cumulative seconds
({completion['total_recorded_seconds']/3600:.3f} hours), including original runs, validation and
failed attempts. The user explicitly authorized **up to eight hours total**
after the original four-hour stop. That stop and its 0.57-second check granularity
remain in the ledger. All primary comparisons, all five window/support and
calibrated scale-2 sensitivities, fidelity/missingness audits and isolated timings
completed. No declared experiment remains incomplete. CPU postprocessing and
the small known-process estimator-stability diagnostic are separate from GPU-stage time.

The separately frozen, post-primary scale-2 comparison is exploratory and reuses
seed-17 episodes, 96 original observations, and the same cached references.
Scale-2 minus scale-1 bootstrap T recall changes are
{scale_contrast('synthetic','T')} (synthetic), {scale_contrast('intel','T')} (Intel),
and {scale_contrast('pems','T')} (PEMS). Corresponding TB changes are
{scale_contrast('synthetic','TB')}, {scale_contrast('intel','TB')}, and {scale_contrast('pems','TB')}.
Background rates, availability and separate PE/SE outcomes must be considered;
these are not matched-rate contrasts. Scale-1 ranks exactly reproduce the
independent W96 support audit. Scale 4 in these windows does not meet the primary
template minimum and remains support-only. Native
physical-fault accuracy, stronger generative architectures, longer histories
and dashboard usability remain outside the demonstrated evidence.

## Reproducibility and submission

See README.md for exact CPU regeneration and CUDA rerun commands.
The manuscript is manuscript/paper.pdf; the interactive replay is dashboard/index.html
after running scripts/build_extension_dashboard.py and serving the directory.
results/extension-v2/claim-ledger.json links every abstract/conclusion assertion
to saved results or proofs. The numerical tests passed on the A6000 (20 tests)
and locally (18 passed, two CUDA checks skipped); the browser passed three-case
interaction checks. Final artifact hashes and PDF inspection are recorded
separately after rendering.

The verified workshop limit is 10 pages including references, IEEE two-column
format, with October 15, 2026 deadline. Parent-conference instructions are
single-blind and prohibit an appendix; a separate workshop supplement policy
was not established. AI assistance is disclosed in the manuscript. Authorship
is preserved; affiliations and email were not supplied. Nothing was submitted
or pushed. See docs/venue.md for primary policy sources and access limitations.
'''
(root/'docs/extension-findings.md').write_text(findings)

# paper.tex is the editable manuscript, with numerical blocks refreshed in place.
# Comments mark generated content; LaTeX needs no other manuscript .tex files.
paper=root/'manuscript/paper.tex'
source=paper.read_text()
for name,content in [('abstract',abstract),('results',results),('compute',compute),('conclusion',conclusion)]:
    begin=f'% BEGIN GENERATED: {name}'
    end=f'% END GENERATED: {name}'
    pattern=rf'^{re.escape(begin)}\n.*?^{re.escape(end)}$'
    source,count=re.subn(pattern,lambda _:begin+'\n'+content.rstrip()+'\n'+end,
                         source,flags=re.MULTILINE|re.DOTALL)
    if count!=1:
        raise ValueError(f'Expected exactly one generated {name} block in paper.tex; found {count}')
if re.search(r'\\(?:input|include|subfile)\b',source):
    raise ValueError('paper.tex must contain all manuscript LaTeX inline')
paper.write_text(source)
print({'generated':['paper.tex','abstract.tex','results.tex','compute.tex','conclusion.tex'],'claims':len(claims)})
