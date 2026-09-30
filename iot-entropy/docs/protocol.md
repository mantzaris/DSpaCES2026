# Preregistered protocol — entropy-reference-v1

Frozen before full training or held-out scoring, 2026-09-30. The configuration
and this document are versioned on `main`. Pilot/development amendments must
be dated in `decisions.md`; no test-guided changes to entropy or hypotheses.

## Questions and primary comparisons

H1: Jointly standardized H and lagged change improve event detection/localization
relative to non-entropic synchronization summaries, at independently calibrated
equal nominal scan budgets. H2: conditional diffusion helps relative to a
context-selected seasonal block bootstrap. H3: the combination improves coverage
of both entropy directions. These are hypotheses; a null or negative result
is publishable. H is a deterministic compression of R and cannot increase its
information. All comparisons include full-correlation distance and raw residuals.

Exactly three primary datasets: graph-coupled synthetic dynamics (64/128/256
node configurations), Intel Lab, and original-release PEMS-BAY. Synthetic
simulation/fault code is independent of learned models. Real-data injection
results are semi-synthetic, never verified native failures.

## Splits, units and quality

Real data use contiguous 60/15/10/15% train/development/calibration/test splits.
No input or target may cross a split. Intel uses causal, right-labelled 2-minute
bins: last observation in the bin, with its original timestamp retained. No
forward filling or interpolation. Keep all coordinate-listed sensors; use
humidity's documented 0--100% range as a validity check. Primary channels are
temperature and humidity; light/voltage are auxiliary coverage analyses.
PEMS keeps 5-minute release values, expands timestamp gaps with masked rows,
and follows the original release evaluation's zero-as-missing convention,
reporting exact zero and NaN counts. Audit upstream preprocessing separately.

Synthetic splits consist of separate simulations, disjoint seeds and entire
episodes: train 48 x 1024, development 12 x 1024, calibration 32 x 256, test
32 x 384. This preserves a 60/15/10/15 split by samples. A single fixed random
geometric graph is used per configuration; its radius and spectrum are recorded.

Training scaling uses per-sensor/channel median and IQR/1.349, with a fallback
to standard deviation and a floor. Extreme training standardized values above
8 in magnitude are excluded only from the model loss; their fraction is logged.
This screening is not a healthy-label claim. A sensitivity model includes them.
Neural inputs replace missing values with zero after scaling and include masks.
No neighbor imputation. Test values are never fitted or clipped for scoring.

Correlations use complete rows within a fixed group and channel. Require
`n_valid >= max(2*m, ceil(0.8*W))`. Near-zero sample variance (1e-8 in scaled
units) gives a distinct quality flag and undefined entropy. The observed mask
is applied to generated samples before feature computation. Missingness and
flatlines are reported separately. All methods share these eligibility rules;
hybrids additionally report quality alerts and never replace missing H with zero.

## Features, graph and model

Spatial groups use supplied graph shortest-path proximity, with coordinates
breaking ties. Sizes 6/12/24, 24 deterministic evenly spaced index centers per
configuration, deduplicated within size. Use W=24/48/96 only when W>=2m;
d=W/4. Freeze all group/channel/window indices before calibration. PEMS uses
published road distances; Intel uses coordinate proximity, not inferred physical
wiring. Synthetic uses its actual coupling graph.

Primary entropy: sample correlation spectrum, shrunk toward I with lambda chosen
from 0/.05/.1 on development reference-fidelity/numerical stability; default .05.
Use a symmetric eigensolver and allow negative roundoff only within
64*m*machine_epsilon. CPU float64 is the numerical reference.

The diffusion reference is an explicitly attributed compact adaptation of
DiffSTG/CSDI: joint graph-temporal denoising with historical measurements/masks,
coordinates, calendar context, cosine DDPM noise schedule and compatible DDIM
sampling. No exact-reproduction claim. Forecast block length is max(W+d)=120;
the 48-row context ends strictly before it. Each smaller window uses a suffix
of this same generated block; its longer forecast lead is explicit. H and DeltaH
come from the same sample. Default 100 training diffusion times, 20 inference
steps, width 24, 3 layers, Adam 1e-3, batch 8, at most 2400 updates. Validate
every 200 updates; stop after four nonimprovements. Three seeds 17/29/43 if the
profiled budget permits. Score 64 samples in chunks of 16. The pilot sets the
explicit runtime ceiling before full runs; a budget stop preserves progress.

Bootstrap references select intact training blocks using calendar phase and
historical context similarity only, preserving multivariate/temporal structure.
No selection uses target measurements. Donor masks are retained.

For each feature, median and 1.4826*MAD over samples give location and scale;
the floor is selected from development variability and numerical precision,
then frozen. Two-sided max absolute residuals are primary. Signed level and
change residuals remain separate diagnostics. Synchronization includes signed
and absolute correlation, within-window squared disagreement, leading spectral
concentration, and their lagged changes. D is algebraically redundant with C
after sample standardization and is not interpreted as independent evidence.

## Required methods and ablations

Cross entropy/synchronization/combined scores with diffusion/bootstrap references.
Additionally calibrate individual C/Cabs/D/P, full-R Frobenius reference distance,
raw predictive residual, entropy-plus-raw and quality hybrids, two-sided CUSUM,
and a labeled GDN reimplementation (learned embedding top-k graph, graph attention,
one-step prediction, robust residual scaling, trailing smoothing). GDN can use
causally observed target history and this forecast-horizon advantage is disclosed.

Ablations: H only; H+DeltaH; positive/negative/two-sided residuals; graph removed
and graph shuffled; local/global entropy; generator choice; feature family;
raw/quality hybrids. Group/window/missingness/B=32/64/128 sensitivity is compact,
using a fixed subset identified before testing. Global entropy needs W>=2N;
use a separate longer window and disclose its additional delay and eligibility,
not a rank-deficient all-node matrix at W=96. Graph and contamination retraining
sensitivities use seed 17; core feature ablations reuse identical saved samples.

## Calibration and events

Calibration is per forecast issuance, not per indefinite stream or day. Maximum
over the entire frozen eligible scan family is the unit score. Calibration
issuances are separated by 168 observations (context plus maximum target),
and synthetic calibration uses one unit per independent simulation. Rank
p=(1+#calibration maxima >= score)/(n+1), including all-abstained no-alert units
as -infinity. Show n and minimum attainable p. Primary alpha=.10; secondary
.05/.20 only where attainable. Dependence diagnostics and empirical exceedances
must accompany any rank statement. The theorem assumes exchangeability and a
fixed scoring rule; real sensor windows are not assumed exchangeable.

Use at most 12 disjoint 312-row base test episodes per configuration (all
available when fewer). For each, score t=167,179,...,311 with stride 12. Event
onset is 192, durations 12/48/96, severities .6/1, affected sizes 6/12, alternately
connected and partially disconnected selections. Balance a fixed 72-event
fault-type x severity x duration grid over base episodes; fix draws independently
of training seeds. Include untouched controls and explicitly labeled legitimate
synchronized operating transitions. Multiple injections into the same underlying
recording are paired, dependent episodes and bootstrap clusters accordingly.

Mechanisms: copy collapse, common interference, reduced coupling, independent
noise, partial delay, offset/gain drift, flatline, dropout, anticorrelated copy,
mixed collapse/noise, matched-mean-correlation covariance changes, and marginal-
preserving temporal rearrangement. Synthetic state-level coupling changes are
identified separately from sensor-level decorrelation injections in real data.
Measure entropy sign against the untouched paired recording; never force it.

An alert is a connected run of consecutive flagged issuance times. Match alert
ONSET one-to-one to event [onset,onset+duration-1], zero trailing tolerance.
An alarm beginning before the event earns no credit. No point adjustment.
Every unmatched alarm is a false alert in this controlled benchmark, including
post-event residual-window alarms. Native unlabelled examples are qualitative.
Report event precision/recall, missed events, and event PR upper-envelope area
from the explicit one-to-one matching rule; retain raw nonmonotone curves because
merging can change recall. Alarm delays include stride/window effects, with
measured computation added; generation can be scheduled at issuance.

Localization uses group-score participation with inverse-size weights and a
fixed top-k budget selected on development injections from {6,12,24}. Evaluate
precision/recall/F1/IoU at first matching alert, report zero for missed events,
and conditional detected-event scores separately. Report candidate oracle IoU.
Merge groups at Jaccard >= .5 for display, retaining originals. Clustering of
trailing signed traces is descriptive and never a second significance test.

Report event/type/dataset macro and pooled results, direction, duration,
severity, size and connected/disconnected strata. False alerts per network-day
and sensor-day use observed control monitoring duration (sample interval times
scored stride coverage); also report per-issuance null exceedance. Real native
controls lack fault labels, so call these background alerts, not confirmed false
fault detections. Legitimate synthetic transitions are known negative controls.
95% paired bootstrap intervals resample entire independent synthetic simulations
or disjoint real recording blocks, retaining all their injections and seeds.

## Reference fidelity, persistence and cost

Evaluate held-out development/test interval coverage/width, multivariate energy
score, covariance error and entropy-distribution fidelity on untouched blocks.
Save raw generated samples for selected replays and compact predictive/feature
arrays for all scores. Evaluate long persistent faults and contaminated history
with recomputed references, plus a frozen clean earlier context sensitivity.
No causal counterfactual claim.

Record checkpoint/config/data hashes, split/group manifests, code revision,
seeds, software and hardware. Time warm CUDA kernels with synchronization and
CPU float64 reference; report kernel and full pipeline costs separately. Count
training/sampling wall time and peak memory. Save results before manuscript
results, derive all figures/tables from saved outputs, inspect final <=10-page
IEEE PDF. Dashboard replay must expose data quality, signs, issue/observation
times, calibration meaning and known mechanisms versus unknown native causes.
