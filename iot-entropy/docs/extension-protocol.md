# Frozen spatial–temporal extension, v2

Frozen before full extension evaluation, 2026-10-01 UTC (September 30 local).
The executable configuration is `configs/extension-v2.json`, overlaid on
`configs/full.json`. The freeze commit is recorded in the run manifest. Changes
after the freeze require a dated amendment, reason, and affected runs. This is
an extension motivated by previously inspected outcomes, not preregistration
of the original study. Comparisons reusing recordings or fitted models are
exploratory. No test-result-dependent model or threshold search is permitted.

## Questions and hypotheses

RQ1 compares correlation-spectrum entropy S with conventional spatial summaries
and the full correlation matrix. RQ2 tests the information lost by ignoring time
order. RQ3 compares temporal entropy T with conventional temporal statistics.
RQ4 compares S, T and ST, including localization. RQ5 crosses every main feature
family with bootstrap and diffusion references. RQ6 examines mechanisms,
duration, severity, missingness, support, window and calibration. Directional
advantages are hypotheses, not required outcomes. B versus BST is mandatory.
No equivalence margin is declared: failure to reject cannot establish equivalence.

## Preservation, data and information boundaries

Original revision: `b900da1bf4b3b4f1b8ab2310257af842de587562`. Its manuscript,
code, configuration, predictions and results remain recoverable with `git show`.
Original `experiments/full` and `results` outputs are not overwritten. New runs
live under `experiments/extension-v2`, derived outputs under `results/extension-v2`.
An audit manifest records original file hashes and historical checkpoint values.

Exactly three primary datasets: the existing synthetic process (64/128/256
nodes are configurations), Intel Lab, and PEMS-BAY. Keep existing physical
graphs, units, primary channels, causal preprocessing and train scaling. Intel
temperature and humidity remain separate. PEMS is release speed in mph; its
upstream imputation cannot be reconstructed. Native events lack verified labels.

Retain the trained normal models for seeds 17/29/43; no architecture search.
Synthetic extension uses the original training data and graph but independent
development (4 x 312), calibration (32 x 256), and test (4 x 312) simulations,
seed = 9000000 + 1000*N + 100*partition + episode. Calendar phase follows the
simulation seed. These are separate simulations, not a continuous time series.
For real data retain chronological original partitions; choose four disjoint
312-row test blocks not used in v1 where available, otherwise explicitly
reuse inspected blocks. Record overlap. Reusing Intel backgrounds with new
injections is not new real-data validation. Four base blocks limit precision.

All windows/context remain inside a partition and simulation/recording block.
The 48-row context ends before the 120-row target. W=48/96, d=W/4 use suffixes
of the same joint generated trajectory. Issuance is target_start-1; decision
is target_start+119. The original W=24 scan remains in v1 and is a support
diagnostic, not the main temporal scan. No new target data enters a reference.
Apply observed missingness after generation. Bootstrap also retains donor masks.

## Measurement definitions and support

S is unchanged local correlation-spectrum entropy with shrinkage .05, complete
rows >= max(2m,ceil(.8W)), sample variances >1e-8, symmetrization and PSD tolerance
64*m*machine_epsilon. Reject materially negative eigenvalues. Spatial meaning
comes from grouping, not from an additional entropy of coordinates. Channels
are never pooled. Retain C, absolute C, standardized pairwise disagreement,
leading eigenvalue concentration, and full-R Frobenius discrepancy.

Permutation entropy: q=3,tau=1 initially, natural log normalized by log(q!).
Every embedding preserves grid positions; any required missing point invalidates
that template. Stable time-index tie breaking; store tied-template fraction.
Need >= max(30,5*q!) valid templates at both endpoints. Constant series or tied
fraction >.5 are quality abstentions, not evidence of low complexity. Sensitivity
on development only: (q,tau)=(3,1),(3,2),(4,1), and dropping tied templates.
Choose greatest finite support, breaking ties toward smaller q then tau.

Sample entropy: r=2, unordered start pairs a<b with b-a>2 (Theiler exclusion),
same pair set for length-r and length-(r+1) comparisons. Both templates must
contain all r+1 observations. Tolerance is .1/.2/.3 times the original training
sensor scale, hence fixed standardized units. Choose greatest development
finite-estimate support, ties prefer .2 then smaller tolerance. Require >=30
templates and B>=20 for operational scoring, while retaining raw A/B and
uncensored estimates for audit. B=0 is undefined; A=0,B>0 is +infinity/censored;
neither enters finite-score calibration. Flatlines are quality abstentions.
No pseudocounts, gap concatenation, neighbor imputation, or arbitrary large score.

For both entropies retain level and lagged change. A change requires valid
endpoints; an infinite endpoint cannot create a finite change. Limited
multiscale diagnostics use scales 1/2/4, bins aligned to each window's left
edge; a bin requires every observation and incomplete end bins are discarded.
Report support after coarsening, separately for permutation and sample entropy.
Do not extend the forecast horizon to rescue an unsupported scale. All
conventional diagnostics use the same window/history as their entropy partner.

Temporal conventional features: ACF at lags 1/2/4, variance of first differences,
local sample variance, least-squares trend, mean (predictive-level residual after
reference scoring), and two-sided within-window CUSUM with allowance .5 in
training standardized units, reset at window start and paused at missing rows.
ACF uses actual lag pairs; no gap compression. Need >=max(12,ceil(.5W)) observed
points/pairs for the applicable feature. Keep distinct feature support and
common-support analyses rather than forcing every feature to abstain because
sample entropy is undefined. Conventional level/change and ACF-vector changes
use the same joint references and scoring. Retain original GDN adaptation and
raw residual baseline; label GDN's access to causal observed target history.

## Scoring, tuning and calibration

For each feature pair (level,change), use generated median and 1.4826*MAD plus
floor max(1e-4,.05*development IQR). Need >=80% finite reference draws per
component. Score max absolute component residual, keeping actual signed change
separate. MAD does not imply Gaussian tails. Temporal measurements stay per
sensor/channel. Aggregate top ceil(fraction*m) valid sensor scores within group,
requiring >=ceil(.5m) valid sensors. Candidate fractions .25/.5 and localization
budgets 6/12/24 are selected on four development copy/noise/drift/delay episodes
using average localization IoU over entropy/conventional/reference combinations;
ties favor smaller fraction/budget. Identical choices apply across families.

Families S; PE; SE; T=max(PE,SE); ST=max(S,T); spatial conventional SB;
temporal conventional TB; B=max(SB,TB); BST=max(B,ST). Include individual temporal
feature scores and raw/GDN comparators. A max ignores unavailable components
but abstains if all are unavailable. No score is imputed from zero. Calibrate
every reported family separately; calibrate common-support families anew.
Operational results include all scheduled times and all fault events. Common
support restricts candidate group/window/channel units to valid S,PE,SE,SB,TB;
its event denominator still includes missed/unobservable events. Also report
the observable subset explicitly and without relabeling it overall recall.

Calibration uses original real calibration partitions, independent new
synthetic calibration simulations, context+target gap 168. n and minimum
p=1/(n+1) are reported. Per-issuance scan maxima give p=(1+#cal>=test)/(n+1),
all-abstained maxima=-infinity. alpha=.10 is primary. No test controls select a
prospective threshold. Independence is not implied by gaps, and exchangeability
is an assumption rather than a property of the real recordings. Measure
achieved background rates on separate test controls. If rates differ, any
test-rate-capped comparison is separately labeled retrospective/descriptive.

Localization alternatives: inverse-size group participation, direct maximum
sensor temporal score, and combined ranking based on the mean of normalized
rank percentiles from these two sources. Use the same development-fixed budget.
Primary localization for S/SB uses participation; PE/SE/T/TB direct temporal;
ST/B/BST combined. Save all three alternatives, conditional and unconditional
metrics (misses contribute zero), and candidate-group oracle overlap. Signed
agreement and onset alignment are descriptive, never extra uncalibrated tests.

## Episodes, diagnostics and inference

Retain all 12 original fault mechanisms x severities .6/1 x durations12/48/96
(72 per configuration), sizes6/12 and connected/partly disconnected selections.
New fault seeds97100+i, controls98100+base; onset192, decisions167:12:311.
Synthetic decoupling changes the state transition using the same new clean seed;
real decoupling remains a sensor-level intervention. Untouched and legitimate
transition controls accompany each base. Masking/dropout retain quality status.

Separate controlled diagnostics (seed830197): joint aligned time-row shuffle,
periodic replay/interference, disrupted dependence, copying, legitimate
transition, offset, gain, sign, quantization, flatline and dropout. Joint row
permutation invariance is checked on an identical complete evaluated block;
it is not claimed for every overlapping window or entire entropy trace.
Compare temporal conventional measurements on exactly the same diagnostics.
These mathematical constructions do not establish general detection superiority.

Event matching remains Hungarian one-to-one on alert onset inside the true
event interval, no early-alarm credit, no point adjustment. Report precision,
recall, event-PR envelope area, delays, localization P/R/F1/IoU, background burden,
availability, templates/pairs/ties/censoring and computation. Paired intervals
resample whole base simulations/recording blocks retaining all injections and
model seeds. Repeated windows, injections and seeds are not independent trials.
Report dataset/configuration/mechanism/direction/severity/duration/missingness.

Reference fidelity: marginal coverage/width, energy score, spatial correlation
error, ACF error, ordinal-pattern distribution total variation, sample-entropy
level distribution/coverage, entropy interval coverage/width and finite support.
Poor generator fidelity is not evidence against an entire feature family.

## Budget, validation and delivery

Use existing A6000, cumulative four-hour recorded experiment ceiling, original
recorded10088.092477s; remaining4311.907523s before this extension's profiling.
Profile development first; save a budget ledger including validation/pilot and
failed runs. Request a budget change only if measured cost makes required runs
infeasible. No paid provisioning, billing change, submission, push, or branches.
Prioritize all five configurations and both references at seed17, then29/43;
record incomplete runs rather than substituting fabricated results. Count
warm synchronized CUDA kernels separately from complete pipeline time.

Validation gates: mathematical bounds/shrinkage/finite-difference derivative;
aligned permutation invariance; explicit CPU ordinal and pair-count oracles;
missing/tied/flat/short cases; CPU/GPU agreement; common pair sets; no future
conditioning and split crossing; one-to-one event/localization; calibrated
controlled-null simulation. Chunk quadratic pair calculations. Neural mixed
precision is separate from float32/float64 statistical computations.

Deliver code, compact predictions/support/calibration, selected replay, manifests,
equation mapping, generated figures/tables, dashboard, IEEE source/bibliography
and rendered inspected PDF, and a claim-to-evidence findings report. Heavy
raw trajectories/caches/checkpoints remain local/remote and ignored by Git.
