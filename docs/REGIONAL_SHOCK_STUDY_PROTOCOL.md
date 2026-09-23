# When Regional Totals Hide Local Change

September 23, 2026. Bounded exploratory shock study; this file and the JSON
configuration are frozen by hash after a correctness/timing smoke and before
comparative outcomes. The execution manifest records any timing-based uniform
workload reduction. No full study or held-out evaluation is authorized.

## Question and inherited evidence

Can limited local monitoring identify changes that are invisible or weak in
group aggregates, and direct a fixed reading budget more usefully than random
acquisition? Separate benefits of observations, their selection and their
representation. The same-evidence representation comparison must agree under
the same Gaussian model. Agreement is an expected result, not a failed test.

The previous handoff `0a4a0a5`, clean main branch, 49-test log and numeric policy
summaries were inspected. Preserve its 59.4% regional coverage, static variance
policy, 3.94% worse primary MAE than random, and lack of a memory advantage over
streamed fine inference. RJD is neither rerun nor reinterpreted.

The prior interval implementation includes household residual and observation
noise, horizon-dependent common process noise, separator covariance and
cross-group aggregation covariance. No missing-noise bug was found by inspection.
New independent joint-Gaussian tests audit those terms. Raw undercoverage remains
evidence of an inadequate working distribution, not automatically an algebra bug.

## Observation interfaces and fixed statistical model

The sampled population is the same 4,194 training-eligible London meters.
Groups are the inherited 16 balanced synthetic partitions. No topology,
geographical location, provider organization or population weight is invented.
Use the unchanged 2012-fitted seasonal/factor plus household AR model and its
recorded SHA. No new parameter fit or architecture search is performed.

The actual macro operator S_t exposes **16 group sums over native observed
support**, plus that support mask. It is not merely a regional total. Its
provider scans every available household reading to construct these sums; this
work is charged. All methods receive the same summaries. Consumer fine access
is a separate channel. The evaluator may load a full background to produce
overlays, but cannot pass hidden values or labels to a policy.

| Method | Observation interface | Representation and queries |
|---|---|---|
| M0 | Derived group sums only | Fixed finite-window Gaussian; regional, group and conditional household forecasts; macro innovation detector. |
| M1 | Sums plus the same rotating cheap probes as M3 | Fixed representation and incremental evidence cache, no directed expansion. |
| M2 | Sums, shared probes, random remaining reads | Same model and total fine-record cap as M3. |
| M3 | Sums, shared probes, triggered fine reads plus exploration | Activates selected conditional blocks, then evicts them after queries; preserves acquired evidence in a counted 24-step cache. |
| M3_fixed | M3's exact acquisition trace revealed one update at a time | Same structured Gaussian solver, retains all conditional blocks while processing the query; no future policy decisions supplied. |
| M4 | All currently available household readings and derived sums | Structured streamed fine inference, not a dense household inverse. Sums add no duplicate information. |

A 16-dimensional factor model can assimilate individual observations. Only M0's
**interface**, not its latent rank, makes it aggregate-only. All representations
have the same model; exposing conditional coordinates does not create evidence.
All household queries are calculated for scoring, so any common query-workspace
cost is charged even when few details stay resident. No capacity advantage is
presupposed.

## Established observability result and limits

Let x_(t+1)=F x_t+eta_t, y_t=H x_t+epsilon_t and macro observations
z_t=S y_t, with fixed F,H,S. Compare two experiments with initial states differing
by a fixed delta, identical exogenous-input/noise laws and identical background
state law translated by delta. The difference at step k is C F^k delta, C=S H.
Define O_L=stack(C,C F,...,C F^L).

**Proposition (indistinguishability, established).** If O_L delta=0, the joint
macro observation laws through L are identical. Every measurable detector,
including a randomized detector with an independent common randomization law,
has power equal to its false-alarm probability for this simple comparison.

Proof: couple the background initial state and all process/observation noises
identically. The stacked observation difference is O_L delta, hence zero almost
surely. The observation laws coincide, so integrating the same decision function
against either law gives the same probability. Gaussianity is unnecessary for
this conclusion. Different noise laws, unknown input changes, adaptive observation
rows that expose extra information, or nonzero O_L delta invalidate the premise.

With time-varying support S_k, use stack(S_k H F^k); cancellation in the complete
total alone is insufficient. For direct trajectory overlays d_k, measure S_k d_k
directly. The real-data overlays below do **not** obey the fitted state generator;
the F-based theorem is illustrated separately, never asserted for those overlays.

For two coordinates with equal persistence .9 and shock (1,-1), observing only
their sum hides the shock at every lead. A probe [1,0] reveals it; a probe of an
unaffected third coordinate does not. With persistences .9 and .7, the total
signature at k=0,1,2,3 is 0, .2, .32, .386. Thus an initially hidden change may
later become visible. Nonzero but small signatures can be diluted by noise;
nonzero observability does not guarantee useful finite-sample detection power.

For uniform independent sampling of b of N households at each step, m affected
households with fully observed persistent signals, the probability of no affected
probe through T steps is [choose(N-m,b)/choose(N,b)]^T. This is only a sampling
coverage identity: noisy detection can still fail after a hit. Rotating probes,
adaptive schedules, changing support and finite events do not inherit that formula
without new assumptions. No detection-delay theorem is claimed for this replay.

## Partial evidence without aggregate double counting

Within one 24-step window, let c be the 384-coordinate common trajectory. For
household i, y_i=O_i c+e_i, e_i~N(0,V_i), with
V_i[t,u]=v_i rho_i^|t-u|+n_i 1{t=u}. Native support M_i and acquired-cell selector
P_i can differ. Let f_i=P_i y_i. Ordinary Gaussian conditioning gives

    G_i = V_i P_i^T solve(P_i V_i P_i^T, I),
    E[y_i | c,f_i] = G_i f_i + (I-G_i P_i) O_i c,
    W_i = V_i - G_i P_i V_i.

The derived aggregate is a=sum_i M_i y_i. After conditioning on f,

    a | c,f ~ N(alpha_A + O_A c, V_A),
    alpha_A=sum_i M_i G_i f_i,
    O_A=sum_i M_i(I-G_i P_i)O_i,
    V_A=sum_i M_i W_i M_i^T.

Multiply p(f|c) by p(a|c,f), not p(f|c)p(a|c). Completely revealed aggregate
coordinates are redundant and removed algebraically. A positive measurement
nugget makes the remaining conditional observation block proper. The implementation
uses solves, handles masks explicitly and never makes a numerical variance
clipping operation a certificate. Independent tiny joint-state tests instead
observe fine cells and the disjoint remaining aggregate at each time, auditing
means and covariance against a separately assembled posterior.

Forecast moments retain shared factors, future process noise, private temporal
covariance and the negative covariance induced by aggregate conditioning. Summing
household marginal variances alone is incorrect. Evicting conditional blocks
preserves the registered query law; the acquired-value cache is retained and
charged, not hidden as free storage. At a moving boundary, old fine cells expire,
all mask-dependent group messages are rebuilt, and the fixed training window
prior is reused. This is not exact all-history filtering.

The policy is centralized and always receives its scheduled probe values, so it
does not infer “small residual” from a nontransmission. Nevertheless, its selection
history can depend on observations older than the retained window. We do not
condition the model on that full selection history: interval laws are finite-window
working Gaussian laws, not exact post-selection Bayesian or frequentist coverage.

## Reversible disturbances and chronology

Only existing Q1 development Parquet is read. January 3-4 unmodified development
data calibrate thresholds and simple interval scales; all comparison backgrounds
begin January 7 or later, across the same four development weeks. These dates
were already exploratory in Stage 2 and are not untouched confirmation data.
April-December London and the earlier BDG2 seals remain inaccessible.

The default eight backgrounds use origin indices 0,4,8,12,16,20,24,28 from the
previous frozen list. Each has a 23-step aggregate-only warm-up, 48 sequential
half-hour updates and 12 future target steps. There is no free fine warm start.
Locations are sampled among the frozen household IDs, balanced across training
consumption-size quartiles within a seeded group. All methods use identical
episodes. Seeds 930000+1000*background+scenario are reserved for comparison;
700001 is smoke-only. No injected waveform is used to fit a detector or model.

| Family | Frozen mechanism and what should be visible |
|---|---|
| A, regional | Every observed household increases by 0.15*magnitude*training residual SD for 12 or 20 steps. Macro positive control. |
| B, localized | 32 households in one group change by magnitude*training residual SD; sign fixed by seed parity. Reductions are feasibly scaled. Group signature may be diluted, not assumed hidden. |
| C, exact | 32 opposing pairs within one observed group. Each pair receives equal feasible opposite changes. Both are set to zero if either is natively missing. Every exposed group sum stays unchanged. |
| C, approximate | Same pairing, negative side has 80% of the positive amplitude. A weak macro signature remains. |
| D, delayed | Initially opposing pairs decay at .96 and .70. An initial feasible amplitude respects all affected negative backgrounds. These are synthetic demand dynamics, not fitted-model transitions. |
| E, ramp | 32 households rise linearly over 24 steps. |
| F, background | No perturbation. Alarms are relative to the injected-event protocol; unlabeled real anomalies can exist. |
| Reading fault | Localized positive reading overlay; target remains original demand. Report separately from demand changes. |

Two magnitudes, 1 and 3 residual SD, are moderate/large controlled stress settings,
not estimates of real event frequencies. Onset is 6-10 steps after the stored
warm-up index; durations and exact indexing are saved per episode. For negative
changes, use at most 80% of available baseline consumption. Pairwise scaling,+rather than independent clipping, preserves cancellation; record realized sizes,
zero-effect cases, missing support and actual S_t d_t. Keep unmodified inputs intact.

## Monitoring, budgets and calibration

With N=4,194, floor(.05N)=209 attempted fine readings per step and floor(.01N)=41
shared rotating probes. Missing attempts consume budget. No borrowing from later
steps or free history requests. M2/M3 use the remaining 168 reads; M1 uses only
the 41 probes. M3 reserves 42 extra reads for rotation/exploration. Triggered
exploitation focuses the remaining reads on the highest-scoring group, excluding
already read records; unused capacity rotates elsewhere. If no trigger is active,
all extra reads rotate. Four below-threshold steps end active detail.

Probe errors use the previous coarse model's one-step household predictive means
and SDs, indexed only at acquired IDs. The group monitor is
score_g <- .8 score_g + max(0,max_probe_z_g-2). It never computes a full fine
innovation vector before choosing reads. The macro detector uses normalized group
innovations; its variance uses full-group prediction even when current support
changes, a heuristic handled empirically rather than a formal null distribution.

An initial unmodified calibration pass fixes the trigger at the 98th percentile
of the maximum monitoring score. A second pass with that fixed policy determines
method-specific familywise alarm thresholds and interval corrections. The target
alarm budget is 2% of update steps (any channel alarm), not 2% per household.
Component 95th-percentile macro/fine normalizers followed by a joint 98th-percentile
threshold set the rule. Realized step and episode alarm rates must be reported.
Finite, dependent calibration samples do not guarantee the target rate.

Absolute standardized forecast errors set one empirical 90% interval multiplier
per method, lead and query level. Household calibration uses every 16th valid
ordered ID as a bounded deterministic sample; affected-household evaluation uses
that household multiplier. No shock-specific calibration or test-year adjustment.
Raw and adjusted widths/coverage are both retained. Correction cannot demonstrate
a selection benefit or repair a poor point forecast.

The M3 trace is passed sequentially to M3_fixed, including probe and extra reads,
without future choices. One separately labeled boundary diagnostic delays extra
reads until step 26, then opens the group with the largest revealed-probe score;
old observations outside the window remain expired. An uncertainty-only policy
is included there as a small diagnostic, not a renewed primary claim.

## Metrics, accounting and stop rules

Primary detection window: six update steps including the onset step. A miss gets
delay seven, rather than disappearing from the delay average. Report any-event
detection separately from correct-group detection, per-step alarms, affected
household/group localization and false localizations. No point adjustment. Store
continuous scores. Initial cancellation is assessed at the actual macro resolution.
For exact cancellation, local recovery and detection are relevant; regional MAE
is not credited as an injected-event benefit. Report the first revealed affected
record and first macro alarm separately for delayed events.

Forecasts target observed demand at one-hour/six-hour leads. Compare affected
households during and after the event, the whole household cohort, group totals
and common-observed-support regional totals. Missing readings are not zero, and
partial totals are not complete-population ground truth. Count eight backgrounds
and four development weeks, with seeds nested within backgrounds. Use descriptive
block differences; do not treat the thousands of updates or meters as independent
regional events.

Charge provider full scans, fine attempts/valid records, 16-byte simulated fine
records plus framing, support masks, transfers, reconstruction, inference and
query workspace. Separate simulated access from actual compressed Parquet I/O.
Cache reuse avoids source rereads of already retained cells, but all moving-window
factor rebuilding is counted. Shared aggregate preparation is amortized across
methods only when explicitly stated. GPU timing is synchronized; event spans
include dispatch and are not labeled pure active kernel time.

Hard limit: min(90 new allocated minutes, verified remaining 103.7667 minutes)
from the first executed new job. Preserve the earlier 76.2333-minute charge and
25.6435 CPU job-minutes. Inter-session billing idle is separate under the existing
closed-stage convention. Reserve 15 minutes for failures, analysis and handoff.
Original six CPU job-hours, 30 GB data/cache, 8 GB host and 24 GB GPU targets remain.
Hardware preflight measured the same 32,623 MiB RTX PRO 4500 Blackwell, idle.

Stop on any unexplained same-evidence mismatch, negative predictive variance,
budget/cutoff violation or cancellation failure. Correct demonstrable bugs with
logged retries; never retune locations/magnitudes to seek a win. Smoke timing may
reduce paired backgrounds uniformly before freezing, retaining all families.

## Focused primary-source comparison

| Source and checked full text | Relevant result and assumption | Difference or limitation for this study |
|---|---|---|
| Jurek & Katzfuss, [MRF](https://arxiv.org/pdf/1810.04200), v2; JCGS 2021. Rechecked Sections 3.2-3.4. | Multiresolution covariance representation and exact update relative to its approximate prior; arbitrary observation operator is not synonymous with aggregate-only sensing. | We keep a simpler fixed model and vary access. No new multiresolution filter. |
| Jurek & Katzfuss, [hierarchical sparse Cholesky](https://arxiv.org/pdf/2006.16901), v2; Statistics and Computing 2022. Rechecked sparse-update/Laplace sections. | Conditional sparsity supports scalable filtering under specified dependence and likelihood structure. | Shared-separator locality is a model assumption; it does not establish physical locality or a new sparse theorem. |
| Sun & Work, [full author paper](https://lab-work.github.io/download/SunWork2017.pdf), ECC 2016, [DOI](https://doi.org/10.1109/ECC.2016.7810671). Sections II-III and stated stability result. | Threshold-based transmissions, implicit information in silence, synthetic-measurement approximate MMSE and input-to-state stability with bounded synthetic error. | IEEE access required JavaScript; the linked author PDF was accessible. We always receive scheduled probes and do not claim exact filtering from unmodeled silence. |
| Han et al., [stochastic event-triggered scheduling](https://arxiv.org/pdf/1402.0599), Theorem 1 and scheduling definitions. | Exponential stochastic triggers preserve conditional Gaussianity and give an explicit silence update; ordinary deterministic triggers do not generally do so. | Our truncation of history and empirical detector do not inherit that guarantee. |
| Veeravalli, Fellouris & Moustakides, [controlled sensing full paper](https://www.ssp.ece.upatras.gr/moustakides/downloads/journals/seq2024_1.pdf), IEEE JSAIT 5, 1-11, 2024, DOI 10.1109/JSAIT.2024.3362324. Assumptions 2-4, Theorem 1, Section IV. | Windowed Chernoff-CuSum combines information-seeking controls with exploration and asymptotic delay optimality under finite action/parameter sets and identifiable distributional models. | Exploration and active anomaly sensing are established. We use no known post-change likelihood and claim no optimality. |
| Huang et al., [UCB controlled sensing](https://arxiv.org/html/2603.28563v1), March 30 2026 preprint. Assumptions, Algorithm 1, asymptotic theorem. | Stream selection with known distributions/KL separation and regularity; periodic restarts prevent overcommitting to old information. | Directly relevant recent active sensing, not evidence that simple event refinement is novel. Publication beyond preprint not established here. |
| He et al., [participant-level electricity anomalies](https://www.nature.com/articles/s41598-026-54639-1_reference.pdf), Scientific Reports 16, 26384 (2026). Accepted-manuscript Sections 2-4 inspected; catalog lists version of record Aug 24. | Participant time-slot inputs, pooled LSTM date screening, subsequent participant error-rule localization; large private provincial participant data. | Its global screen already consumes participant-level features. It is not an equal-access aggregate-only comparator. Publisher HTML failed; the accessible full accepted manuscript may differ from the final typeset version. |

The candidate contribution is a measured relationship between the actual
aggregation nullspace, restricted monitoring and evidence/refinement cost.
Observability, Gaussian conditioning, active sensing, synthetic anomalies and
GPU batching are established ingredients. The empirical distinction must survive
M1/M2 and same-information M3_fixed. A result explained by simple probes is reported
as such. The BDCC graph enclosure/reconstruction/selective-simulation contribution
remains excluded; its authoritative adjacent plan was available in the earlier
audit and is unchanged. This study uses no traffic dynamics or scenario simulation.
