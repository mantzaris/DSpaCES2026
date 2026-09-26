# When Regional Totals Hide Local Change

September 23, 2026. Bounded exploratory Greater London replay with synthetic
disturbances. This report is completed from the frozen GPU outputs below. It
does not authorize a full study, another stage or a manuscript submission.

**The bounded study is complete, but it does not establish a useful shock-targeted
refinement policy or a new inference contribution.** Aggregation blindness is
verified, and additional household observations improve local forecasts. However,
none of the 96 demand disturbances changed M3's acquisition-ID trace relative to
the paired unmodified background. Its small forecast difference from random
selection is not evidence of successful shock targeting. Same-information fixed
and adaptive representations give identical answers. Preserve this negative result;
do not launch the full study or claim a publishable adaptive-refinement method.

## What was tested

The starting `0a4a0a5` handoff was verified on main. The preceding reports and
numeric artifacts retain 167,932,474 ingested source rows, 4,194 eligible real
households and 52,109,356 training readings. Stage 2's 864 policy cases, 1,728
restoration cycles, static uncertainty policy, 3.94% worse one-hour MAE than
random at eight groups, and 59.38% raw regional coverage remain unchanged.
Its 61.12-to-21.60 MB eviction saving was not a capacity advantage over streamed
fine inference, which also retained 21.60 MB. RJD's failed acceleration result
was neither rerun nor reversed.

The new experiment distinguishes three questions: whether more observations
help; whether event-sensitive selection allocates the same observation budget
better; and whether changing representation improves inference or resource use
with identical observations. These are not interchangeable claims.

The fixed 2012-fitted model retains seasonal household profiles, 16 common
dynamic factors and household AR residuals. The 16 balanced groups are inherited
synthetic partitions of real meter IDs, not boroughs or electrical feeders.
No new training, architecture selection, population weights or propagation
network is introduced. Units are kWh **per half-hour at** one-hour/six-hour lead,
not energy integrated over the forecast horizon.

| Method | Available measurements | Representation |
|---|---|---|
| M0 | Sixteen observed-support group totals and masks | Fixed conditional Gaussian; macro detector and all query levels |
| M1 | M0 plus 41 rotating probes per step | Fixed representation, no directed extra reads |
| M2 | Shared probes plus 168 randomly selected reads | Same model, 209 attempted readings per step |
| M3 | Shared probes plus 168 event-directed/exploration reads | Selected conditional detail retained while querying, then evicted |
| M3_fixed | M3's exact trace, revealed sequentially | Conventional fixed structured inference, all conditional blocks retained during query |
| M4 | Every currently available household reading | Structured fine reference, streamed eviction after queries |

A low-rank model can ingest household readings. Only M0's observation interface
makes it aggregate-only. All methods share the common-factor model and future
noise law. Household query computation is charged for every method. M3_fixed
is a matched-model message-inference comparator, not a full reproduction of
iSAM2 or a multiresolution filter.

Providers compute the common group totals by scanning current household values.
That work is measured. Limited access is therefore a consumer fine-message
contract, not a saving in initial metering or provider ingestion. The evaluator
loads actual backgrounds to construct overlays and score targets; those hidden
values and injection labels are not policy inputs. Acquired probes alone update
the selection score. No full fine residual vector selects the next group.

## Frozen chronology, disturbances and scoring

The unchanged Q1 2013 development partitions supply an earlier unmodified
January 3-4 calibration segment and eight later backgrounds across four existing
development weeks. These dates were already exploratory in earlier stages.
They are not untouched confirmation data. Each main episode has 23 aggregate-only
warm-up steps, 48 sequential updates and enough future support for both leads.
London April-December 2013 and all earlier BDG2 seals stay intact.

Six demand families cross two requested magnitudes (1 and 3 training residual
SD): broad increase, localized signed change, exact within-group cancellation,
approximate cancellation, initially cancelling unequal persistence, and gradual
ramp. Each background also has an unmodified control and a separate reading-fault
control. Locations/onsets are paired across magnitudes and all methods; fresh
comparison seeds are distinct from smoke seeds. No injected waveform fits the
detector. Actual onsets are update indices 7-11, as recorded in episode metadata.

Demand overlays modify both available readings and future targets. The fault
overlay modifies readings only. Negative sides are feasibly scaled, never
independently clipped to manufacture cancellation; missing pairs receive zero
paired changes. Requested SD and realized feasible amplitude are distinct.
The paired within-group changes cancel at the actual 16-row macro interface,
including native support. These are controlled disturbances on real measured
backgrounds, not observed interventions or recovered noise-free demand.

M2/M3 have identical per-step and cumulative attempted-record budgets. Missing
attempts count; no bursts or free historical reads are allowed. M3 reserves 42
of its extra reads for exploration, and uses a four-step exit rule. Its fixed
threshold comes from unmodified earlier development innovations. Component and
joint alarm quantiles target a 2% probability of any alarm per update, empirically;
dependent, limited calibration data do not guarantee that rate.

All detectors use the previous coarse model as their common predictable residual
reference. This isolates the observation interface but is not an optimized detector
for each representation. The first update starts the monitor from seasonal means;
subsequent updates use the coarse posterior forecast. Alarm calibration excludes
its first eight updates, whereas primary negative-control rates include startup.
These implementation choices and realized false alarms limit operational claims.

Detection means an alarm within six updates including onset. Misses receive
seven steps (3.5 hours) in the delay average, rather than disappearing. Any alarm
and correct-group alarm are separate. No point adjustment is applied. Household
localization counts use only actually perturbed records; false localization and
negative-control alarms remain visible. The analysis also compares each shock's
detection window with the identical window in its unmodified background.

Forecast errors use common observed target support, with missing labels excluded.
An observed-support regional sum is not complete-population ground truth. Exact
cancellation does not change the regional target, so regional MAE is not credited
as an injected-event benefit there. Calibration reports both raw and earlier-segment
adjusted 90% intervals and widths. Variants are nested within eight backgrounds
and four weeks; there are no independent-hour significance or equivalence claims.

The GPU completed **112 episodes: 96 demand-shock cases, eight unmodified controls
and eight reading-fault controls**. These contain 5,376 episode updates and 32,256
method updates, plus a separately labeled boundary diagnostic. They reuse eight
backgrounds in four development weeks. There are 464 unique target intervals and
1,916,438 observed household-target pairs; **none has a complete-population observed
total**. The 308,016,768 scalar forecast evaluations across methods, query levels
and overlays are repeated calculations, not independent observations.

The correct-group detection counts within three hours are below. Every cell has
denominator eight backgrounds; M3_fixed equals M3. Any-event alarms are reported
separately in the saved table and figure because unrelated background alarms can
otherwise look like successful shock detection.

| Family / requested magnitude | M0 | M1 | M2 | M3 | M4 |
|---|---:|---:|---:|---:|---:|
| Broad / 1 SD | 4 | 1 | 4 | 4 | 4 |
| Broad / 3 SD | 8 | 8 | 8 | 8 | 8 |
| Localized / 1 SD | 0 | 0 | 0 | 0 | 0 |
| Localized / 3 SD | 4 | 2 | 2 | 3 | 3 |
| Exact cancellation / 1 SD | 0 | 0 | 0 | 0 | 0 |
| Exact cancellation / 3 SD | 0 | 0 | 0 | 0 | 0 |
| Approximate cancellation / 1 SD | 0 | 0 | 0 | 0 | 0 |
| Approximate cancellation / 3 SD | 0 | 0 | 0 | 0 | 0 |
| Delayed / 1 SD | 1 | 0 | 0 | 0 | 0 |
| Delayed / 3 SD | 1 | 0 | 0 | 0 | 0 |
| Ramp / 1 SD | 1 | 0 | 0 | 0 | 0 |
| Ramp / 3 SD | 1 | 0 | 0 | 0 | 0 |

The broad 3-SD control is detected immediately by every method. At the local
macro-blind interface, neither probes nor full fine access produce successful
localization under the frozen detector. All exact-cancellation M0 alarms also
occur in the matching unmodified windows: its apparent 25% any-alarm rate is
not shock detection. The delayed family's M0 correct-group alarms likewise have
zero excess over their matched backgrounds. There is no demonstrated local-warning
lead time over informative macro observations.

| Method | Any demand-event detection / 96 | Correct group / 96 | Mean delay, misses included (hours) | Negative-control alarm steps / 384 |
|---|---:|---:|---:|---:|
| M0 | 37 | 20 | 2.438 | 36 (9.38%) |
| M1 | 17 | 11 | 3.031 | 15 (3.91%) |
| M2 | 33 | 14 | 2.641 | 25 (6.51%) |
| M3 | 29 | 15 | 2.661 | 30 (7.81%) |
| M4 | 42 | 15 | 2.240 | 41 (10.68%) |

These realized alarm rates exceed the 2% calibration target. Excluding only the
initial monitor update, they remain 7.45%, 2.39%, 4.52%, 5.85% and 8.78%, respectively.
They are alarms relative to the injection protocol; real backgrounds may contain
unlabeled anomalies. M3-minus-random delay differences by background are +2.25,
0, 0, 0, -1.25, 0, -0.667 and 0 half-hour steps. This small paired panel does not
support a significance or equivalence conclusion. Continuous peak scores,
misses, household recall, false household/group instances and matched-background
excess are retained in [episode_detection.csv](../results/shock/analysis/episode_detection.csv)
and [detection_summary.csv](../results/shock/analysis/detection_summary.csv).
Across the 16 exact-cancellation events, M3 records ten false household-alarm
instances and 32 false group-alarm instances, with no correct localization.
Those counts concern the 24-step event windows; they are not independent alarms
or unique households. Both unique and repeated counts remain in the episode table.

For the five local families during their disturbances, affected-household MAE is:

| Method | One-hour MAE | Six-hour MAE |
|---|---:|---:|
| M0 | 0.177702 | 0.192521 |
| M1 | 0.176206 | 0.188268 |
| M2 | 0.171048 | 0.186346 |
| M3 / M3_fixed | 0.169595 | 0.185838 |
| M4 | 0.138586 | 0.182569 |

Units are kWh per household per half-hour. M3 is 3.75% below probe-only M1 and
0.85% below random M2 at one hour, but 22.37% above M4. Its paired background
MAE difference from random ranges from -0.008072 to +0.001071. It is slightly
worse than random for exact and approximate cancellation specifically
(0.148992 vs 0.148366; 0.144047 vs 0.143004). Added observations help; a targeted
response to the injected shock is not responsible for the small pooled advantage.

M3's acquisition IDs are unchanged from background in all 96 demand-shock and
eight fault cases. Detail is active in 4.95% of updates, but the affected group is
never the activated group during any local event. Most extra reads therefore
follow the fixed exploration/rotation schedule. This is measured in
[policy_response.csv](../results/shock/analysis/policy_response.csv), not inferred
from a passing test. The same ID trace receives different values under a shock.

For events with aggregate consequences (excluding exact cancellation), regional
one-hour MAE is 51.333 / 44.856 / 44.383 / 44.817 / 44.860 for M0/M1/M2/M3/M4;
six-hour MAE is 158.209 / 115.014 / 109.335 / 107.047 / 97.971. M3 does not dominate
random at both leads. All before/during/after and query-level results remain in
[forecast_summary.csv](../results/shock/analysis/forecast_summary.csv).

The reading-fault control is separate: M3 alarms on six of eight cases, but the
targets have not changed. Its affected-household one-hour MAE is 0.13830, versus
0.13273 for M0 and 0.19453 for M4. More corrupted readings can worsen the demand
forecast. The detector does not identify whether a change is physical or a fault.

On unmodified backgrounds, regional one-hour MAE is 46.070 / 41.712 / 39.392 /
39.146 / 34.187. Raw and adjusted 90% intervals are:

| Method | Raw coverage | Adjusted coverage | Raw width | Adjusted width |
|---|---:|---:|---:|---:|
| M0 | 75.52% | 85.68% | 117.58 | 158.81 |
| M1 | 71.88% | 86.72% | 112.03 | 163.98 |
| M2 | 73.44% | 83.33% | 105.98 | 139.89 |
| M3 | 72.14% | 84.11% | 106.01 | 149.31 |
| M4 | 75.52% | 89.06% | 96.46 | 136.46 |

Widths are regional kWh per half-hour. For M3 at six hours, coverage changes from
83.33% to 86.20%, with width 262.30 to 272.73. Local shock intervals remain poorly
calibrated; the earlier household correction actually shrinks intervals and
reduces M3's affected-household one-hour coverage from 79.00% to 77.34%. Calibration
is neither a guarantee nor a selection improvement.

### Three concrete episodes

- **Macro visible:** background 0, broad 3-SD event, onset update 8, duration
  20. The maximum observed-support regional increase is 292.675 kWh per half-hour.
  Every method alarms at onset. A macro detector already handles this control.
- **Hidden local change:** the preselected background-0 exact-cancellation 3-SD
  event starts at update 11 and lasts 24 steps in group 4. Sixty households have
  nonzero feasible changes; the largest household perturbation is 0.7168 kWh.
  The group signature is at most 1.11e-16. M3 reads affected records at onset but
  its largest three-hour detection score is 0.9732, below the frozen threshold 1.
  M0's later alarm is also present without the disturbance. The figure preserves
  this failure, including forecasts that under-recover the opposing changes.
- **Miss despite an informative probe:** background-0 approximate cancellation,
  1 SD, has a maximum group signature 0.60376 kWh. M3 acquires a perturbed reading
  at onset but peaks at score 0.8465 and misses the detection window. M4's alarm
  is in the wrong group. Having read an affected meter is not the same as detecting
  or localizing the event.

## Mathematical result, consistency and uncertainty diagnosis

The established observability argument is explicit in the
[frozen protocol](../docs/REGIONAL_SHOCK_STUDY_PROTOCOL.md). For a compatible
linear state model, `C=SH` and `O_L=stack(C,CF,...,CF^L)`. If `O_L delta=0` and
the initial/background and noise laws differ only by that state translation,
coupling identical noises makes every macro observation identical through the
horizon. Any detector has equal power and false-alarm probability for that
comparison. Gaussianity is unnecessary. A new probe changes the observation
rows, but can miss the changed coordinates. Equal-and-opposite coordinates with
persistences 0.9 and 0.7 have checked signatures 0, 0.2, 0.32 and 0.386.

The replay's overlays do not follow the fitted state generator. Their visibility
is measured directly as `S_t d_t`, including missing support. The latent theorem
is not silently applied to an incompatible demand generator. Nonzero visibility
also does not ensure useful detection at a fixed noise level or alarm rate.

Arbitrary partially revealed household/time cells use the ordinary Gaussian
factorization `p(fine | common) p(derived aggregate | fine, common)`. The conditional
aggregate covariance retains temporal and cross-household effects induced by
conditioning. Fully revealed aggregate coordinates are redundant and removed.
An independent tiny full joint-state posterior observes the fine cells plus the
disjoint remaining aggregate at each time, checking both means and covariances.
It does not merely compare two calls to the same summary implementation.

This extends the existing evidence-replacement implementation to partial fine
observations, using established conditioning identities. Under identical model
and evidence, fixed and adaptive representations must agree. Activating detail
creates no new statistical information. Every moving window currently rebuilds
all 16 mask-dependent messages and the common separator; the experiment does
not establish cross-window factor reuse. The acquired-value cache is retained
and counted, and expired observations are not silently available on reopening.
Household conditional query work is still performed across the whole population.
Selected retention does not demonstrate that computation scales only with active
detail or that the model supports a larger population than streamed fine inference.

Inspection of Stage 2 found future common process noise, household residual and
measurement noise, and aggregation cross-covariance already included. No omitted
noise-term bug was established. Independent tests audit those terms here. Poor
raw coverage remains a working-model adequacy problem. Empirical scaling can
change interval widths and coverage but cannot establish better selection or
exact coverage. Adaptive histories outside the retained window are not conditioned
on, and deterministic selection does not automatically preserve Gaussianity.

| Check | Measured result |
|---|---:|
| Focused tests on the GPU execution machine | 16 passed; previous 49-test record preserved |
| Same-information M3 vs M3_fixed, 5,376 updates | Maximum mean/variance difference 0 |
| Exact cancellation vs paired background M0 scores | Maximum difference 1.9984e-14 |
| Independent joint posterior mean / covariance | 1.1102e-15 / 9.4369e-16 |
| Independent joint forecast / regional variance | At most 8.8818e-16 |
| Current-record tiny reference, mean / variance | 2.2204e-16 / 4.4409e-16 |
| Corrected illustration vs saved regional forecast | Maximum difference 1.0232e-12 |
| Fine budget violations, zero-effect shock episodes, unexplained numerical failures | 0 / 0 / 0 |

Tests cover missing cells, nonnegative overlays, fault-versus-demand targets,
causal cutoffs, duplicate requests, budget enforcement, expired/stale caches,
partial aggregate replacement, eviction, exact visibility and probe misses.
These are numerical checks, not formal floating-point certificates. Current-record
conditioning produces roundoff-level negative variances as small as -2.78e-16;
they are reported directly, not clipped into a claimed certificate.

The declared delayed-opening diagnostic first acquires extra readings at update
26, after the 24-step boundary. It uses 5,664 attempted reads versus 1,968 for
probe-only, with 978 expired fine cells and no history rereads. It rebuilds all
768 group messages over 48 steps. Affected-household one-hour MAE is 0.14384
versus 0.14556 for probe-only in this single diagnostic, not a separate success
study. It cannot reconstruct expired fine evidence it never retained. The
uncertainty-only diagnostic chooses group 12 throughout; covariance ranking still
does not depend on observed values. [Boundary accounting](../results/shock/analysis/boundary_diagnostic.json).

The predeclared current-record check reuses the exact saved trace and reads no
additional observations. At update 12 of the hidden episode, M3 has three of
60 affected current records and reconstruction MAE 0.26485, versus 0.28116 coarse;
on its unread subset the MAE is 0.27879. At update 26, M3 is slightly worse than
coarse (0.12887 vs 0.12421). M4 reconstructs revealed records to about 7.0e-16,
which is expected because it already observes them. This is recorded-demand
reconstruction, not recovery of an unobserved physical state or a forecasting win.
[All 15 checks](../results/shock/current_recovery.csv).

## Closest work and contribution assessment

The [protocol's seven-work primary-source comparison](../docs/REGIONAL_SHOCK_STUDY_PROTOCOL.md#focused-primary-source-comparison)
records inspected sections, publication versions and access limits. Multiresolution
filters and hierarchical sparse Cholesky already support structured inference;
their low-dimensional representations need not have aggregate-only observations.
Sun and Work's event-triggered filter uses information in nontransmissions, and
Han et al. establish Gaussian-preserving stochastic scheduling under particular
triggers. This heuristic claims neither result. Controlled-sensing work by
Veeravalli, Fellouris and Moustakides, and the 2026 UCB preprint, already couples
exploration with selective sensing under specified likelihood assumptions.
We have no known post-change likelihood or optimal delay theorem.

The 2026 electricity anomaly study by He et al. consumes participant time-slot
features before its global screen; it is not an aggregate-only equal-access
baseline. Its accessible full accepted manuscript was inspected, with final-version
differences left unresolved. IEEE's landing page required JavaScript, but the
Sun/Work author manuscript was accessible. No failed search establishes novelty.

The candidate scientific contribution is a measured relationship between
aggregation blindness, limited local access and refinement cost under an explicit
contract. It is not a new observability theorem, Gaussian-conditioning identity,
active-sensing principle or scalable inference algorithm. Synthetic anomalies
alone do not establish publishability. The separate authoritative BDCC plan
remains scientifically distinct: no graph structural-defect enclosure, Matheron
reconstruction, selective Monte Carlo or observation-versus-simulation allocation
is reused here.

**Decision: close this bounded study without a refinement-success or full-paper
claim.** A useful selective-access prototype and a reproducible diagnostic remain,
but the evidence does not establish an advantage beyond established conditioning
and acquiring more data. M3's event policy did not respond to the injected changes;
its small average difference from random is not an identified new capability.
M3_fixed is identical and streamed fine inference also fits comfortably.

The concrete failure has two visible components. First, earlier-background tails
and familywise calibration yield effective fine-innovation thresholds of 15.17,
26.02, 19.71 and 34.36 standardized units for M1/M2/M3/M4, much larger than the
requested local 1-3 SD shifts. M3's sequential trigger is 13.433. Second, feasible
nonnegative reductions attenuate opposing disturbances: across backgrounds, the
median realized peak is 2.057 SD for requested 3-SD exact cancellation, and only
0.611 SD for the delayed family. All such cases remain included. These observations
explain why visibility alone did not produce reliable alarms; they do not justify
retuning on this comparison or claim a new detector. The short-memory fitted
household model is also not the generator of the sustained overlays.

An unresolved scientific requirement is evidence of shock-sensitive acquisition
that helps at a controlled realized alarm rate beyond a competent active-sensing
baseline, with a contribution beyond standard inference. This stage does not
supply it, and no next experiment is launched. The original BDCC distinction,
earlier negative results, held-out seals and disabled main study all remain.

## Cost, reproducibility and operational handoff

The measured device is the existing **RTX PRO 4500 Blackwell, 32,623 MiB**, not
the earlier reported 48 GB assumption. Matrix work uses GPU FP64, TF32 disabled,
PyTorch 2.8.0+cu128 and four CPU threads. CPU handles I/O, orchestration, saved-output
analysis and plotting. No CPU solver competition, hardware allocation, upgrade,
new training sweep or original main-study execution was started.

No dataset was downloaded or training model refitted. Preparation reread the
existing Q1 Parquet once: 69,497,803 compressed bytes, 17,612,617 valid eligible
readings, 9.903 s parsing and 10.678 s total preparation. That is approximately
7.02 MB/s compressed input or 1.78 million parsed valid readings/s on this pass.
The nine prepared calibration/background stores contain 3,288,355 valid entries
and occupy 6,201,715 bytes. Their reuse does not multiply unique physical evidence.
Initial 52.11-million-reading training contributions remain in the unchanged model.

| Method | Fine attempts per update | Total fine attempts | Simulated fine payload | Median / p95 acquisition + inference | Separator/detail state during query |
|---|---:|---:|---:|---:|---:|
| M0 | 0 | 0 | 0 MB | 72.00 / 81.90 ms | 2.365 MB |
| M1 | 41 | 220,416 | 3.871 MB | 72.13 / 82.16 ms | 2.365 MB |
| M2 | 209 | 1,123,584 | 18.665 MB | 72.28 / 82.19 ms | 2.365 MB |
| M3 | 209 | 1,123,584 | 18.665 MB | 72.34 / 82.09 ms | 2.365 MB median |
| M3_fixed | 209 | 1,123,584 | 18.665 MB | 72.02 / 81.86 ms | 41.017 MB |
| M4 | 4,194 | 22,546,944 | 361.095 MB | 72.40 / 82.40 ms | 2.365 MB |

Decimal MB are used. M3 returns 1,106,434 valid fine readings, M4 22,204,000;
attempted missing records still consume budget. Every alternative also receives
3.855 MB of group sums, native masks and framing. Fine-message payloads are
calculated from the actual request trace and declared wire format, not network
packet measurements. Including common summaries, M3 exchanges about 22.520 MB
versus M4's 364.950 MB, a 16.2-fold simulated communication difference, accompanied
by 22.37% worse local one-hour MAE. The provider still scans all households.
Primary provider-summary construction scans 33,350,688 household-row opportunities
including warm-up, repeatedly over the eight backgrounds. Those are workload,
not additional physical observations.

The table's state measure excludes 38.652 MB of shared household temporal
covariances, other common model tensors, temporary forecast coefficients and
0.805 MB of host observation cache per method. All methods retain 2.365 MB of
separator state after detail eviction; M4 already has this floor. The combined
comparison process peaks at **182.487 MB PyTorch GPU allocation and 1.732 GB host
RSS**. These are process peaks, not separately isolated per-method capacities.
No larger-population capacity advantage is demonstrated.

Every method rebuilds 86,016 group messages and 5,376 separators. The moving-window
factor reuse fraction is zero. The retained acquired-value cache prevents rereads,
but does not avoid window-factor construction. Recorded host/device input payload
is 5.495 GB **per method**, including dense masked caches; limited fine communication
does not currently reduce those transfers. The formal fine trajectory has 101,040
coordinates but structured elimination solves a 384-coordinate common separator,
not a dense 101,040-square system.

The comparative job takes **2,460.192 s (41.003 min)** including startup and the
boundary diagnostic. Primary episode timers sum to 2,431.704 s; per-method measured
updates sum to 2,381.043 s, including repeated charging of the shared current-summary
scan as an alternative-method cost. Whole-job time additionally contains common
window construction, scoring and serialization. It is the six-method comparison
pipeline, not an isolated single-method deployment latency. CUDA event spans
sum to 2,378.863 s and include dispatch; no pure-kernel speedup or CPU comparison
is claimed. Preparation memory was not separately profiled; the quoted RSS peak
belongs to the comparative process.

The same-trace current/figure-support diagnostic takes 27.520 s and grants no
new observations. The first saved-output analysis emitted numeric-ID parsing
deprecation warnings. Forcing alarm ID columns to strings removed the warning;
the initial analysis is preserved and its detection/forecast summary files are
byte-identical to the corrected analysis. Figure support was corrected separately
using frozen traces, and the cost plot uses a zero time origin to avoid exaggerating
sub-millisecond timing differences. All reruns and copies count in the same ledger.

The frozen comparative GPU source is `031bdd6f0535413ecfc9ac025083fcc3300b19bc`.
Its [manifest](../results/shock/frozen_manifest.json) records configuration,
protocol, calibration, model and source hashes. The configuration SHA-256 is
`60d9a17abac78639de7a76ce1ec47a89a2b4b2c313dd3c9d8072526192c0c902`.
The current-record diagnostic adds only a zero-lead noise convention and uses
the already saved trace; it cannot change the frozen future predictions.
Its GPU-tested source and the 16-test source are
`5e27acbcd9be30f1dcfc0b8f1718307f2a3817c8`.
Later commits add analysis, documentation and operational closure. The containing
git commit identifies the final handoff without a self-referential SHA.

Commands are preserved verbatim, including retries, in the
[resource ledger](../results/shock/resource_ledger.json). With the existing data
and scientific environment, the principal executed entry points are:

```bash
python scripts/shock_job.py --label prepare --timeout 300 -- python scripts/prepare_shock.py
python scripts/shock_job.py --label smoke --timeout 120 -- python scripts/replay_shock.py smoke
python scripts/shock_job.py --label calibration --timeout 180 -- python scripts/replay_shock.py calibrate
python scripts/shock_job.py --label freeze --timeout 30 -- python scripts/freeze_shock.py
python scripts/shock_job.py --label comparative_replay --timeout 3600 -- python scripts/replay_shock.py run
python scripts/shock_job.py --label final_tests --timeout 180 -- python -m pytest -q tests/test_shock.py
python scripts/shock_job.py --label current_recovery --timeout 120 -- python scripts/shock_current_recovery.py
python scripts/shock_job.py --label analysis --timeout 300 -- python scripts/analyze_shock.py
python scripts/shock_decision_summary.py
python scripts/audit_shock_artifacts.py
```

Closed ledgers refuse new jobs; do not reset the cap. The comparative launcher
also refuses to overwrite completed outputs. Analysis reuses saved numbers and
reversible development overlays, not sealed outcomes. These commands document
the completed allocation, not permission for a new run.

Four figures are generated from saved outputs by `scripts/analyze_shock.py`:

- [Preselected cancellation episode, PDF](figures/shock/shock_episode.pdf) / [SVG](figures/shock/shock_episode.svg).
- [Detection/localization and false alarms, PDF](figures/shock/shock_detection.pdf) / [SVG](figures/shock/shock_detection.svg).
- [Data access, inference cost and accuracy, PDF](figures/shock/shock_resource_tradeoff.pdf) / [SVG](figures/shock/shock_resource_tradeoff.svg).
- [Errors around onset and calibration, PDF](figures/shock/shock_forecasts_calibration.pdf) / [SVG](figures/shock/shock_forecasts_calibration.svg).

Original numeric files remain intact. Dated
[implementation notes](../docs/REGIONAL_SHOCK_IMPLEMENTATION_NOTES.md) explain
the onset-index prose correction, reconstructed informative-read count, timing
and memory scopes, and the boundary diagnostic's group-label limitation.
No substantive comparison was retuned to obtain a favorable result.
A local artifact-audit attempt exposed an older NumPy string-reduction limitation;
using Python's lexical minimum/maximum for ISO timestamps fixed that bookkeeping
check. It changed no data, inference or scientific result.

All completed scientific artifacts are copied to the existing local project disk,
with matching transport SHA-256 and independent NPZ/model/configuration hashes.
The [durable manifest](../manifests/regional_shock_durable.json) inventories them;
no completed irreplaceable artifact remains only on the pod. Existing local
`data/` occupies 2,320,304,247 bytes, including prior archives and the new 6.202 MB
background cache. New results/figures and temporary transfer archives are separately
inventoried and remain far below the combined 30 GB cap. No raw data or model cache
is committed to git.

The [closed resource handoff](../results/shock/resource_handoff.json) records:

| Resource | Minutes |
|---|---:|
| This stage measured elapsed wall time | 64.207 |
| This stage conservative allocation, including final-copy reserve | 67.207 |
| Final-copy/handoff reserve | 3.000 |
| Cumulative original regional allocation | 143.440 |
| Remaining original 180-minute allowance | 36.560 |
| Additional charged CPU job time | 48.588 |
| Cumulative original CPU job time | 74.232 |
| Remaining original six-hour CPU allowance | 285.768 |

The clock starts at 2026-09-23T15:24:36.236833+00:00 and closes at 2026-09-23T16:28:48.638038+00:00; the conservative
handoff reserve extends through 2026-09-23T16:31:48.638050+00:00. It includes setup, idle,
tests, warm-up, all retries, analysis, documentation and artifact copying. A
5-minute conservative CPU allowance covers
unwrapped transfer/archive administration, local saved-output checks and plot
inspection. Inter-stage allocated billing idle was 254.958
minutes under the previously established closed-stage convention; it is recorded
separately rather than hidden or used to reset the research allowance.

The existing pod remains allocated and its storage intact. Final inventory found
0% GPU utilization, no GPU compute process and no active research ledger job.
The original main-study entry point remains disabled; London and BDG2 seals are
unchanged. No experiment remains running and no next stage starts automatically.
For a later user-controlled stop, first retain the local durable inventory and
source/data copies, verify the idle state, and use RunPod's Stop action without
terminating/deleting the pod or storage. No lifecycle action was taken here.
