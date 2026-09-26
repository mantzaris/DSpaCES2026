# Refinement Without Rebuilding: bounded regional pilot

September 23, 2026. Completed exploratory development replay; no held-out
evaluation or next stage is authorized by this report.

**The prototype supports coherent fixed-window refinement, evidence replacement,
coarsening and restoration on 4,194 real households. It does not yet establish a
new inference method, an adaptive-policy advantage, or a larger inference capacity
than a structured fine reference.** Registered forecast moments survive eviction
to numerical precision. The cost is retaining sufficient summaries and rereading
fine evidence when other detail is requested. Those ingredients are established.

The next defensible question concerns **moving-window boundary information**:
what must remain resident to reuse these summaries when time and missingness
advance? This stage deliberately rebuilds window-dependent summaries, so it does
not answer that question. Keep the regional research direction open around this
specific limitation; do not start a full paper, a new architecture search, or
another benchmark campaign on the strength of these results.

## Completion and historical baseline

| Required work | Completed evidence and limits |
|---|---|
| Literature and mathematical investigation | Eight closest primary works; attributed Gaussian proofs, replacement rule, locality conditions and two counterexamples. [Novelty audit](../docs/REGIONAL_REFINEMENT_NOVELTY_AUDIT.md), [theory](../docs/REGIONAL_REFINEMENT_THEORY.md). No new elimination theorem claimed. |
| Training-fitted regional hierarchy | 52,109,356 observed training readings from 4,194 households contribute to a frozen household residual layer on the inherited seasonal/factor model. This initial model enrichment is explicit. |
| Actual changing representation and access | Coarse messages, same-evidence detail exposure, selected fine reads, atomic aggregate replacement, eviction, two rerefinements per case, persistent restoration and added coverage all executed. |
| GPU regional replay and strong reference | 1,024/2,048/4,194 nested households; structured fine, fixed coarse, conventional incremental messages, fixed/random/uncertainty access. FP64 matrix workloads on the existing GPU. |
| Meaningful validation | 49 tests passed; independent tiny joint-Gaussian references, correlated conditional detail, missing data, stale versions, ordering, window changes and double-counted negative control. No unexplained numerical consistency failure. |
| Measured outputs | 864 policy cases, 192 coarse/fine baseline cases, 1,728 repeated restoration cycles, three PDF/SVG figures, complete read/cost logs and durable snapshots. These reuse 32 origins, not 1,056 independent episodes. |
| Boundaries | London April-December 2013 and BDG2 seals intact; original main study disabled; no RJD rerun, CPU solver campaign, new pod or automatic next stage. |

The starting handoff `e76bdfc` and prior GPU source `bf28962` were verified in
main's history. [Stage 1](REGIONAL_TWIN_STAGE1_REPORT.md) remains unchanged:
167,932,474 source rows ingested, 4,194 eligible households, 52,109,356 training
readings, 512 regional solver queries and 39 tests. Its median complete snapshots
were 0.2171 s banded CPU, 0.2182 s GPU Cholesky and 0.3603 s GPU RJD corrections;
all 512 RJD certificates were inconclusive. Its 37.4258 allocation minutes and
19.5120 charged CPU job-minutes carry forward. This stage changes the research
objective; it does not reverse that failed acceleration finding.

## Model, access and what actually changes

The fixed model is

    y_it = seasonal_it + l_i^T s_t + d_it + epsilon_it,
    s_(t+1) = F s_t + eta_t,
    d_i,t+1 = rho_i d_it + zeta_it.

The 16 common factors, seasonal profiles, loadings, scales and stable dynamics
come from Stage 1 training (spectral radius 0.994245). An additional observed-only
GPU projection estimates household residual second moments and lag-one products
from 2012. There are 52,054,466 valid adjacent pairs. A fixed 20% nugget and 80%
AR variance split, with rho clipped to [-0.95,0.95], defines a proper working
model; this split is not identified physical sensor noise. Median rho is 0.5865.
The initial addition of household degrees of freedom is operation C, **model
enrichment**, frozen before comparison. Subsequent refinement never refits it.

Households have real physical meter IDs. Their training-sorted index modulo 16
defines balanced **synthetic groups**, not boroughs or electrical feeders. Regional
and group demand are linear sums of household variables in one joint law.
Household AR errors are conditionally independent given the common trajectory;
unconditional cross-household covariance and common future-factor noise remain.
Aggregate conditioning also induces cross-household dependence within each group.

Each window has 24 half-hour steps and a 384-coordinate common trajectory. The
formal full trajectory has 24,960 / 49,536 / 101,040 coordinates for the three
cohorts. This does **not** imply a dense 101,040-dimensional solve: household
24-by-24 temporal blocks eliminate onto the small common separator. Physical
archive rows, represented households, latent dimension and working memory are
different scale measures.

The implemented operations are:

1. **A, representation:** expose household conditional trajectory means,
   covariance blocks and gains under the current evidence; later evict them.
   Regional means and covariances must not change.
2. **B, evidence:** read a selected group's household window and replace its
   previously used derived-sum likelihood with the fine likelihood. Local and
   regional forecasts may change. The sum and its constituents are never counted
   independently in a valid run.
3. **C, model enrichment:** the one initial residual-model addition above. No
   enrichment is hidden inside an A or B result.

The consumer receives aggregate or permitted fine evidence through a versioned
provider API. It does not inspect unrevealed household residuals to choose groups.
The evaluator alone joins future values after prediction. Missing targets remain
missing. Target masks define observed-support scoring queries after policy
selection; they are not used to select a group. Files contain local-clock labels;
Stage 1's duplicate handling, DST-transition exclusions and unit conventions
persist. Outputs are **kWh per half-hour at one-hour or six-hour lead**, not energy
integrated across those horizons. Tariff labels remain descriptors, not treatment
assignments or evidence of a causal tariff response.

Every group retains its separator information matrix/vector and conditional
moments for three registered queries at each lead: full group, scoring support,
and the group's first physical household. All same-lead covariances needed for
these macro/micro queries are retained. Cross-lead covariance is not retained;
neither are arbitrary new household-query conditionals after eviction. Such
queries require reconstruction. No lossy compression is used or claimed.

## Mathematical and novelty outcome

Exact Schur elimination and the conditional law together preserve a joint
Gaussian distribution. A coarse marginal alone cannot restore discarded detail:
`c ~ N(0,1), d|c ~ N(c,1)` and `d|c ~ N(-c,2)` have the same coarse marginal
but different fine laws. The implemented relaxation retains registered query
summaries and rereads immutable evidence when restoring unregistered detail.
All retained state, source files and restoration costs are counted.

For a deterministic aggregate `a=T y`, the correct update is
`p(c|a,y)=p(c|y)`. The old aggregate information contribution must be subtracted
before the fine contribution is added. With conditional independence across
groups, a changed leaf needs its own recomputation and a new common-separator
factorization; unchanged leaf messages can be reused. Their marginal predictions
can still change through that separator. Cross-group residual coupling can cause
fill-in and much larger, potentially global, recomputation.

The nearest implemented mathematical comparator is Katzfuss and Hammerling's
[distributed low-rank Gaussian inference](https://doi.org/10.1007/s11222-016-9627-4):
local sufficient statistics combine into exact inference for a fixed model.
[iSAM2](https://www.cs.cmu.edu/~kaess/pub/Kaess12ijrr.html) already formalizes
conditional reuse and affected-clique updates. M-RA, multiresolution filters and
hierarchical Vecchia models supply stronger multiscale/sparse frameworks under
their own assumptions. MinT already addresses summation coherence; gas-flow
adaptivity changes model/discretization, a different operation from A.

The candidate contribution was an empirical characterization of a selective
evidence and query-retention contract. The experiment finds a valid capability
and the expected storage/reread tradeoff, but **no demonstrated algorithmic
advantage over ordinary incremental messages with the same eviction policy**.
The streamed fine baseline also fits comfortably. A full-paper novelty claim
would presently be premature. The audit records publication versions, inspected
sections and the incomplete mathematical extraction of the newest 2026 source.

The adjacent authoritative BDCC plan was available and read. This work has no
graph quotient enclosure, Matheron samples, selective Monte Carlo or allocation
between observations and simulation counts. Its matrices describe conditional
evidence and retention, not the BDCC coarse/fine event certificate.

## Frozen replay and comparators

[Configuration](../configs/regional_refinement.json) SHA-256:
`8897c168f4da24361e3fd3d5516da53191f7833f6dd05245e803aa13f9b85fee`.
[Frozen origins and model](../results/refinement/frozen_manifest.json) reuse
32 origins, eight in each of four development weeks. All are in January-March
2013. Both forecast leads are evaluated. The primary query is one-hour regional
observed-support demand; the six-hour/group/household results are diagnostic.

Each cohort uses 2, 4 or 8 of 16 groups for additional fine evidence. The fixed
schedule rotates groups, random uses the declared seed, and uncertainty ranks
current coarse one-hour group variance per household. Each policy has the same
hard cap `k*ceil(N/16)*24` household-interval opportunities. Actual returned valid
rows and file bytes can differ; balanced groups differ by at most one household.
This is matched access capacity, not a claim of identical realized bytes.

| Comparator | Evidence and retained work |
|---|---|
| Fixed coarse | Group derived sums only; returns conditional household forecasts without opening fine values. |
| Uniform fine stream | Every group's fine evidence; batched household elimination, one separator solve, streamed eviction of household conditionals. No artificial dense global inverse. |
| Conventional incremental | Same selected evidence and Gaussian messages; retain local conditionals and reuse them on repeated queries. This is an exact star-model realization of message reuse, not a full iSAM2 reproduction. |
| Proposed eviction/restoration | Identical inference to the incremental comparator before eviction; retain registered query summaries, drop detail, reconstruct on charged reread. Fixed/random/uncertainty policies change which evidence is acquired, not the elimination algorithm. |

Every new origin rebuilds mask-dependent window messages from a fixed training
prior. The preceding posterior is not fed back as a prior, avoiding double
counting overlapping windows. This is a finite-window twin, not exact all-history
filtering. Temporal AR covariance is retained inside each window. **Incremental
reuse is demonstrated within a window; cross-window reuse remains open.**

## Observational findings

There are 64 unique target intervals across the two leads, with 264,251 valid
household outcomes. Between 4,082 and 4,168 of the 4,194 households are observed
at a target. **No target has a complete-population observed sum.** Every scored
regional total uses the identical available support across methods. Full-region
model predictions are allowed for inference traces, but their complete-population
accuracy cannot be scored here. The 16 first-household query series are a fixed
diagnostic panel, not a claim of evaluating every household forecast.

At 4,194 households, one-hour results are:

| Method / fine groups | Regional MAE | Regional RMSE | Raw 90% coverage | Width | 90% interval score | Household MAE |
|---|---:|---:|---:|---:|---:|---:|
| Fixed coarse / 0 | 39.629 | 51.260 | 71.88% | 117.570 | 265.485 | 0.16193 |
| Random / 2 | 35.159 | 45.068 | 71.88% | 103.305 | 221.067 | 0.15707 |
| Uncertainty / 2 | 37.857 | 45.273 | 68.75% | 103.202 | 204.026 | 0.15955 |
| Random / 4 | 35.645 | 45.591 | 62.50% | 100.481 | 233.982 | 0.15290 |
| Uncertainty / 4 | 37.089 | 43.664 | 65.62% | 100.431 | 185.075 | 0.15712 |
| Fixed / 8 | 38.492 | 46.402 | 59.38% | 98.194 | 237.372 | 0.14242 |
| Random / 8 | 37.599 | 45.293 | 62.50% | 98.160 | 226.788 | 0.13966 |
| Uncertainty / 8 | 39.082 | 46.997 | 59.38% | 98.145 | 241.372 | 0.14646 |
| Uniform fine / 16 | 38.007 | 45.825 | 59.38% | 96.436 | 234.518 | 0.12435 |

Values other than coverage are in kWh per half-hour (interval score has the
same units). Regional seasonal MAE is 232.244; the household seasonal MAE is
0.14841. Group MAE for coarse/random-8/uncertainty-8/fine is respectively
3.7833 / 3.6116 / 3.6746 / 3.6067. Group raw 90% coverage is only 74-78%.

At six-hour lead, coarse/random-8/uncertainty-8/fine regional MAE is respectively
92.505 / 64.544 / 63.564 / 62.920, with coverage 78.12 / 87.50 / 90.62 / 87.50%.
Seasonal MAE is 215.403. These diagnostic improvements do not rescue the primary
adaptive-policy claim. All configurations, including less favorable cohorts and
policies, remain in [outcome_summary.csv](../results/refinement/replay/outcome_summary.csv).

The uncertainty rule chose **the same group sets at every origin** for each
budget in the largest cohort. With fixed Gaussian parameters, covariance does
not depend on observed values; only masks can change this ranking. Calling this
successful dynamic adaptation would be misleading. Its primary MAE is 7.67%,
4.05% and 3.94% worse than random at 2/4/8 groups. Some interval scores improve
at 2/4 groups, but there is no consistent quality dominance. No policy or
threshold was retuned after viewing these results.

At eight groups, uncertainty-minus-random MAE by week is +1.774, +4.420, -4.159,
+3.897 kWh per half-hour. These are descriptive paired differences over four
weeks, not independent-hour confidence intervals or conclusive significance.
The narrower intervals often under-cover severely. Mathematical posterior
consistency does not make the working Gaussian model empirically calibrated.
No exploratory calibration or sealed-period tuning was added to fix this.

Different evidence legitimately changes the answer. Mean absolute one-hour
regional differences from the all-fine posterior are 21.016 kWh for coarse,
5.263 for random-8 and 6.795 for uncertainty-8. These are acquisition differences,
**not numerical errors**. Same-evidence numerical discrepancies are below.

## Consistency, incremental coverage and a worked trace

| Check | Raw maximum discrepancy or result |
|---|---:|
| Same-evidence representation query means/variances | 0 across 864 cases |
| Two eviction/rerefinement cycles per case | 0 registered-query drift across 1,728 cycles |
| Reconstructed information factors | 0 |
| Incremental separator mean vs fresh assembly | 4.136e-15 |
| Incremental separator covariance vs fresh assembly | 4.510e-17 |
| Sum of group means vs regional mean | 6.821e-13 |
| Independent tiny explicit joint posterior mean/covariance | 1.110e-15 / 7.772e-16 |
| Independent tiny joint regional variance | 8.882e-16 |
| Full-cohort durable snapshot restoration | 1.421e-14 |
| Double-counted negative control, full-cohort separator mean | 0.006236 error; variance trace wrongly falls from 0.204321 to 0.203609 |

The frozen tolerance was 1e-7 absolute and 1e-8 relative. These are FP64 numerical
audits, not floating-point certificates. Tiny tests build an independent full
joint Gaussian, so they do not merely compare two calls to the same summary code.
Tests also cover alternate refinement orders, induced correlated detail, missing
observations and targets, cutoff relabeling, stale model/window caches and moving
window resets. [Checks](../results/refinement/replay/checks.csv),
[independent joint calculations](../results/refinement/explicit_joint_checks.json),
[49-test log](../results/refinement/final_missing_support_tests.log).

Added coverage admits a previously inactive, training-eligible group under the
same frozen model. At the largest cohort this adds 262 households using a 2,269-byte
aggregate-summary file derived from 6,263 valid window readings. It reuses all
15 existing leaf messages and recomputes the separator in a measured 3.721 ms;
the largest separator mean change is 0.02058. This does not demonstrate admitting
unseen households with untrained parameters. The smaller cohorts execute the
same test with 64 and 128 added households.

For a concrete macro-to-micro-to-macro trace, use the first frozen origin and the
full 4,194-household **model query**, with group 12 selected and group 14 unopened:

| Operation | Regional mean / SD | Group-12 household mean / SD | Unopened group-14 household mean |
|---|---:|---:|---:|
| Coarse derived evidence | 988.287 / 36.065 | 0.56302 / 0.19248 | 0.50120 |
| A: expose same-evidence detail | 988.287 / 36.065 | 0.56302 / 0.19248 | 0.50120 |
| B: acquire eight selected groups | 984.012 / 30.126 | 0.66659 / 0.16495 | 0.60572 |

All units are kWh per half-hour, one hour ahead. Merely showing detail changes
nothing. Reading selected household evidence changes the regional state, which
also changes an unopened household's prediction through common factors. This is
an inferential effect, not a causal demand response. Eviction then preserves the
registered moments; reopening requires retained conditionals or charged rereads.
[Exact saved trace](../results/refinement/replay/macro_trace.csv).

A small double-counting example explains the failure to a non-specialist:
with prior regional coordinate `x ~ N(0,1)` and two unit-noise readings 1 and 3,
the correct posterior has mean 4/3 and variance 1/3. Their sum 4 is derived from
those same readings. Adding that sum as an independent measurement gives mean
8/5 and variance 1/5: spurious confidence, not new evidence.

## Data, memory and complete costs

The original [source manifest](../manifests/regional_source.json) records one
801,674,949-byte London archive, SHA-256
`68a35598cc8e70898a7651c482216fb096a0a6910c2d180c616632dfc7a9b014`,
UK Power Networks / London Datastore attribution and CC BY 4.0. This stage
downloaded no second representation and did not rescan the archive for scale.
It reused training/development Parquet. Transferring missing training partitions
to the existing pod copied 189,891,870 already-local bytes, not new observations.

Training parsing took 25.508 s; GPU fitting's synchronized CUDA event span was
0.627 s; the fit stage took 26.189 s. Provider preparation parsed Q1 once in
9.334 s and completed in 10.972 s, reading 69,497,803 compressed Parquet bytes.
It retained 3,167,768 valid readings in the frozen windows and created 31,403,172
bytes of model/provider stores before snapshots. Both setup passes are charged;
selective consumer access is not an initial sensor-ingestion saving.

The main replay accessed 303,258,045 compressed provider-file bytes over 9,699
events, including repeats. Fine reads returned 26,058,060 valid entries and
decoded 45,105,480 because each provider NPZ holds the full group even for a
nested subcohort. Re-refinement alone reread 70,407,162 file bytes. These are
**logical whole-file access bytes**, not physical disk counters; page-cache state
was uncontrolled. The present layout has no row pushdown, so bytes do not shrink
with nested population size. This limitation is visible in the scale figure.

At 4,194 households, medians for the uncertainty schedule are:

| Fine groups | Fine valid rows per origin | Fine file bytes | Resident accounted state | After eviction | Complete update | Two rerefinements / cached queries |
|---|---:|---:|---:|---:|---:|---:|
| 2 | 12,420.5 | 81,686 | 31.48 MB | 21.60 MB | 56.34 ms | 9.93 / 2.52 ms |
| 4 | 24,765 | 163,198 | 41.37 MB | 21.60 MB | 63.72 ms | 9.96 / 2.54 ms |
| 8 | 49,596 | 327,091.5 | 61.12 MB | 21.60 MB | 77.13 ms | 9.91 / 2.53 ms |

Decimal MB are used. Fractional row/byte medians result from averaging the two
central observations, not fractional records. Active trajectory dimension at
eight groups is 50,712; total represented dimension is 101,040. Eviction releases
39.52 MB of accounted detail while preserving registered queries. Observed CUDA
resident allocation in that case falls approximately 83.22 to 42.83 MB; allocator
and temporary overhead explain why it exceeds accounted model state.

The **streamed fine reference also retains 21.60 MB** and completes in median
56.76 ms, p95 59.54 ms. Fixed coarse is 45.85 / 47.59 ms median/p95. The eight-group
uncertainty update is 77.13 / 79.77 ms, including its 45.85 ms coarse setup; its
incremental portion is 31.28 ms. This measures a memory/reread choice, not an
advantage over the best structured fine memory strategy. Conventional cached
incremental inference avoids rereads and is faster on repeated local queries.
All methods use comparable FP64 block elimination, query calculation and caching.

At a fixed window with k changed groups, G-k of 16 leaf messages are reused and
the common factor is recomputed. The declared reuse denominator is 17 factors
(16 leaves plus one separator), so at k=8 the reuse fraction is 8/17, or 8/16
if discussing leaves alone. Every new window invalidates all mask-dependent leaf
messages. No hidden claim of fully local posterior updating is made.

Across 1,024 / 2,048 / 4,194 households at eight groups, retained-detail state is
31.25 / 40.90 / 61.12 MB, falling to 21.60 MB after eviction. Median reconstruction
of one evicted group is 4.32 / 4.47 / 4.96 ms. Population scale is measured on
distinct real IDs; no duplicated-meter or extrapolated capacity claim is used.

Runtime hardware was again **RTX PRO 4500 Blackwell, 32,623 MiB**, not the reported
48 GB assumption. PyTorch 2.8.0+cu128, CUDA 12.8, driver 580.159.04 and four CPU
threads were used. All inference/fitting matrices are FP64; inherited panel
storage is FP32, which is a data-precision qualification. Maximum recorded GPU
allocation was 344.24 MB during fitting and 103.93 MB during replay. Maximum host
RSS was 1.944 GB. Host-to-device payload in replay was 319.76 MB. The archive is
substantial, but this fixed low-rank inference problem is comfortably small on
the measured device.

The full replay process took 63.51 s including interpreter startup (61.47 s
inside the replay). Summed matrix CUDA event spans were 18.083 s and include
dispatch gaps, so they are not pure kernel-active time. A separate isolated
1,024-household smoke profile recorded 69.09 ms kernels and 2.01 ms transfer/memset
activity; its instrumentation is excluded from main timings. No CPU/GPU solver
race was rerun. [Latency quantiles](../results/refinement/replay/latency_quantiles.csv),
[access accounting](../results/refinement/replay/access_accounting.csv),
[isolated profile](../results/refinement/profile_smoke/cuda_activity.json).

## Failures, qualifications and decision

The first preparation attempt encountered absent training partitions on the pod.
The inherited loader returned an empty panel instead of failing; the output
reported zero training rows. It was rejected before any comparison. The original
log and invalid manifests are retained under `results/refinement/invalid_empty_training/`.
A fail-closed source check and training-count assertion were added, the existing
local training files copied, and preparation repeated successfully. Later, a
saved-output analysis attempted to reference an unrecorded variance column;
that failed job is retained and charged. The analysis was corrected to summarize
the recorded mean differences. Neither issue required retuning or altered the
completed main predictions. All retries count in the ledger.

The principal scientific limitations are the known Gaussian/star structure,
fixed small separator, crude residual-noise convention, poor one-hour calibration,
only four exploratory weeks, a small household-query panel, no complete-region
observed totals, logical rather than physical disk accounting, no remote network
behavior, and full window rebuilding. Exactness is conditional on this statistical
model and registered queries; it is not a guarantee about physical demand.

**Recommendation: preserve this executable capability, withdraw a current novelty
or adaptive-policy success claim, and formulate one boundary-message experiment
before considering a full paper.** The precise next question is whether an exact
or explicitly bounded retained boundary message can advance the 24-step window
under changed observation masks while preserving registered regional/group
forecast laws with less rereading than conventional structured filtering/smoothing.
The separator growth and retained conditional cost must be counted. The strongest
competitors are ordinary state-space filtering/smoothing, MRF and hierarchical
conditional inference, not rebuilding an artificially dense system.

A future proposal must state its boundary sufficient information and compare
matched evidence against an exact reference; a useful approximation would need
an output-relevant error bound. It is falsified as a new capability if the same
state/error/storage behavior follows directly from those established methods.
This is one theoretical/experimental question, not authorization to run it or
a promise of publishability. No alternative model or policy search was opened.

## Artifacts, reproduction and operational handoff

The measured source for the full GPU replay is
`4f3d09e670b102388e9bd92fc81f4de041eeae09`. The profiler used `2affebf`; final
49-test GPU validation used `fcbc575d86f42e5095af276fc0e5c012a96c84a7`.
Subsequent changes add analysis/reporting and resource closure, not new model
results. The report's containing commit is the final documentation handoff;
`git log -1` identifies it without a self-referential embedded commit hash.

Core modules are [Gaussian hierarchy/messages](../src/evidence_fusion/refinement_gaussian.py),
[provider access](../src/evidence_fusion/refinement_access.py),
[preparation](../scripts/prepare_refinement.py), [replay](../scripts/replay_refinement.py),
[tests](../tests/test_refinement.py) and [saved-output analysis](../scripts/analyze_refinement.py).
Exact executed commands and retries are in the
[resource ledger](../results/refinement/resource_ledger.json). With compatible
dependencies and the existing source data, the commands used were:

```bash
python scripts/refinement_job.py --label prepare --timeout 600 -- python scripts/prepare_refinement.py
python scripts/refinement_job.py --label tests --timeout 180 -- python -m pytest -q
python scripts/refinement_job.py --label smoke --timeout 180 -- python scripts/replay_refinement.py --smoke
python scripts/refinement_job.py --label replay --timeout 1200 -- python scripts/replay_refinement.py
python scripts/refinement_job.py --label profile --timeout 180 -- python scripts/replay_refinement.py --smoke --profile
python scripts/analyze_refinement.py
python scripts/audit_refinement.py
```

Closed ledgers refuse new jobs. These commands document reproduction; do not
reset the ledger or infer further authorization. Analysis of saved numeric outputs
needs no GPU or raw outcomes. Data preparation requires the existing 2012 and
Q1 partitions and fails when they are absent. No archive redownload is necessary.

Three scientific figures, generated from saved measurements and visually checked:

- [Replay and regional/local uncertainty, PDF](figures/refinement/refinement_replay.pdf)
  / [SVG](figures/refinement/refinement_replay.svg).
- [Accuracy, acquired readings and retained state, PDF](figures/refinement/accuracy_resource.pdf)
  / [SVG](figures/refinement/accuracy_resource.svg).
- [Measured refinement/access costs across real cohort sizes, PDF](figures/refinement/refinement_cost_scale.pdf)
  / [SVG](figures/refinement/refinement_cost_scale.svg).

The [durable manifest](../manifests/regional_refinement_durable.json) hashes every
new model/provider/snapshot artifact on existing local storage. New ignored
refinement data occupy 84,696,501 bytes; combined existing/new `data/` occupy
2,314,102,532 bytes. Temporary transfer archives and tracked outputs are reported
separately in the final operational inventory and remain far below 30 GB. No raw
meter data or large caches enter git. No irreplaceable completed artifact remains
only on the pod. The 13,727,715-byte full retained-state checkpoint was restored
successfully before handoff.

The allocation clock includes all elapsed setup, work, idle, retries and copying
from 10:30:50 UTC through closure, in addition to Stage 1's 37.4258 minutes.
Closed-stage cloud billing idle before this run was 305.5845 minutes and is
explicitly recorded separately; the pod was still allocated, but no intervening
research job was found. Whole job wall time counts toward the original six CPU
hours, plus a conservative 180-second charge for unwrapped archive/transfer/admin
helpers. Exact closing totals and remaining allowance are in the ledger and
final handoff file. Billing idle after closure continues until a user-controlled
pod lifecycle action.

The original main study remains disabled. Sealed London/BDG2 outcomes were neither
fitted, selected nor scored. No experiment remains running. The existing pod and
its storage remain allocated and intact; none was terminated, deleted or upgraded.

### Closed resource totals

The [final resource handoff](../results/refinement/resource_handoff.json) records:

| Quantity | Minutes |
|---|---:|
| Measured elapsed stage wall time | 36.807 |
| Conservative stage allocation, including two-minute final-copy reserve | 38.807 |
| Cumulative original regional allocation | 76.233 |
| Remaining original 180-minute allowance | 103.767 |
| Additional charged CPU job time, including three-minute ancillary allowance | 6.132 |
| Cumulative original CPU job time | 25.643 |
| Remaining original six-hour CPU allowance | 334.357 |

The control ledger closed at 2026-09-23T11:07:38.779712+00:00; its conservative final-copy reserve extends through 2026-09-23T11:09:38.779733+00:00. Unused budget is not authorization for another stage. The final pod inventory records 0% GPU utilization, no GPU compute process, and only the existing service/administrative processes. Local and pod artifact copies are retained; the original instance remains allocated.
