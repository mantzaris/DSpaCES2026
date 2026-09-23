# Stage 4: why acquisition did not respond

September 23,2026. This report preserves the Stage 3 negative findings and separates
reconstructed diagnostics, controlled behavioral tests and one intentional policy
change. All outcomes remain exploratory development results, not held-out evidence.

## What the original experiment actually established

The reported main handoff585bc42, replay031bdd6 and final diagnostic/test5e27acb
are all ancestors of the inspected main branch. The worktree was initially clean.
No applicable AGENTS.md was found. The actual pod had no experiment running and
its closed ledger matched the local143.4399605-minute cumulative regional charge,
leaving 36.5600395 minutes. The32,623MiB RTX PRO4500 Blackwell was unchanged.

The saved-output audit reproduces112 episodes,96 demand disturbances,4194 actual
households, eight backgrounds from four development weeks, local1h MAE0.1695947
for M3 versus0.1710478 random and0.1385861 streamed fine. M3 had30/384=7.8125%
negative-control alarmed updates. Every method, including random M2 and streamed
fine M4, correctly localized **0/16 exact-cancellation events** within the frozen
six-step window. There was no successful comparator localization to conceal.

The complete [family-by-method table](../results/acquisition/analysis/original_family_method.csv)
contains detection, localization, missed-inclusive delay, false localizations,
local/regional errors, requested/finite readings and bytes. The original
[Stage 3 report](REGIONAL_TWIN_STAGE3_SHOCK_REPORT.md), data and numerical outputs
are preserved. This stage does not correct those headline numbers.

A new FP64 GPU reconstruction supplies previously unavailable intermediate
innovations and 16-group scores. It runs only the original aggregate-only one-step
reference per episode, then executes the actual channel and original ProbePolicy.
It **does not claim these intermediates were logged in Stage 3**. All5376 update
checks match original ordered probe/extra meter IDs, finite returned counts and
active groups. Maximum discrepancy from the saved score maximum is1.599e-14.
Hashes include actual physical meter IDs and timestamps, with separate ordered,
canonical-set and finite-assimilated identities. Selection order also agrees.

Across all 112 episodes,1,123,584 records were requested;1,106,434 finite readings
were returned and newly assimilated. Missing attempts used budget but did not
become zero-valued observations. The channel enforces unique current-time IDs;
no missing/future value or stale cache is silently substituted. All 4194 physical
IDs are unique. Native masks and targets match each reversible overlay. Physical
measurements are real; group partitions, availability policy and disturbances are
experimental constructions. The52.11million training readings were reused through
the fixed training model; no new archive ingestion or fitting occurred.

## The observation-to-action failure mechanism

| Transition in96 demand-shock episodes | Episodes reaching it |
|---|---:|
| Valid affected fine reading acquired before event ends |96|
| Valid affected cheap probe acquired |94|
| Probe innovation differs from paired background |96|
| At least one group score differs |93|
| Full group ranking differs during event |86|
| Acquisition trigger differs |0|
| Active-group action differs |0|
| Actual requested meter/time schedule differs |0|

The two cases without a direct probe hit still change the prediction reference
through observed group aggregates. This is a legitimate macro-to-micro path,
not access to hidden residuals. Three cancellation cases have probe innovations
that change without changing group scores: the changed value does not overcome
the group maximum/drift. Rank changes in this table include lower ranks. The best group changed
in17 episodes, toward an affected group in14; these changes still did not
change the original threshold/hold decision. Full vectors and first divergence times are in
[step diagnostics](../results/acquisition/diagnostic/steps.csv.gz) and
[episode diagnostics](../results/acquisition/diagnostic/episodes.csv), with
[field definitions](../docs/REGIONAL_ACQUISITION_FIELDS.md).

The actual original decision order is:

1. `ProbePolicy.probe_ids(t)` selects41 fixed rotating IDs; `ObservationChannel.read`
   returns their current values. No evaluator label reaches the policy.
2. `run_episode` computes z_i=|y_i-mu_i|/sqrt(v_i), using the previous coarse
   one-step forecast (training seasonal mean/private variance at initial startup).
3. `ProbePolicy.update` sets q_g=.8q_g+max(0,max_{observed probes in g}z_i-2).
   Empty groups only decay. There is no signed averaging, upper clipping or
   shock-independent covariance-only score.
4. If max q_g>13.4333767, select argmax and set a four-decision hold; otherwise
   retain a currently held group or become inactive. This is an acquisition gate,
   separate from the final change-detection alarm.
5. `refinement_ids` spends168 additional attempts:42 explore and126 target the
   active group, or all168 rotate when inactive. Channel validation checks the
  209-attempt cap. No audited event had a budget rejection or minimum-size block.
6. Fine values enter `EvidenceWindow.add` and GPU conditional inference. They
   update forecasts but **never update the original acquisition score**. The next
   policy step again uses new probes and the aggregate-only prediction reference.

Probes precede the current action, so their innovations can change the same
update's extra reads. Values obtained in the extra-read stage cannot influence
that already-issued action; the original method does not use them at the next
selection either. The copied shared probe score is intentional, not a stale-input
cache. Reproduced IDs and active-state traces rule out a later scheduler overwrite.

All96 shock schedules stayed unchanged because no changed score crossed a
selection threshold in a way that altered the original active/hold state. Most
local affected scores were dominated by other observed/background innovations or
fell below the threshold; low-amplitude changes sometimes disappeared at the
max/drift step. Every local-family event had zero affected-group active steps.
Some probes missed events, but missing information alone does not explain the
failure: all exact-cancellation cases had valid affected probe exposure.

**Classification:** a demonstrated method/statistical limitation under this
workload, with some observation limitations; no discovered overlay, indexing,
budget, cache or observation-to-action implementation defect. Large controlled
innovations do change the original action with available alternatives.

## Opportunity, calibration and a worked trace

The elementary uniform-without-replacement reference is
P(no affected read)=choose(N-K,m)/choose(N,m), for fixed K affected households and
m uniformly sampled distinct households. Counting sets proves it. Multiplying
across steps requires independent selections and appropriate persistent support;
for deterministic rotation we inspect actual meter/time intersections. The saved
[sampling reference](../results/acquisition/analysis/sampling_reference.csv) is
explicitly a one-set illustration using event-wide K, not a detection guarantee
or a fitted stochastic model of the actual schedule.

For the preselected b00 exact-cancellation magnitude3 episode, affected probes
are acquired on 9 updates and affected fine readings on all 24 event updates.
First informative exposure is update 11, the onset itself. Acquired affected
probe |z| reaches 3.4411; scores differ by 1.5698, but the maximum remains below
13.4334. No acquisition change follows. The annotated
[observed-but-not-acted-on trace](../results/acquisition/analysis/annotated_trace.csv)
and [figure](figures/acquisition/observed_not_acted.pdf) expose this failure.
This example was selected before the new comparison, not chosen for success.

The2% alarm target and7.81% result both concern **per-update any-channel alarms**
over all group and acquired-household channels. They are not per household,
per group or per episode. Empirical98th-percentile calibration on88 retained
January 3-4 updates yields2/88=2.27% because of finite sample quantiles. The later
M3 no-shock rate is30/384=7.81%. Excluding one startup update gives22/376=5.85%;
excluding the same eight updates as calibration gives17/320=5.31%. Startup
mismatch contributes, but a temporal generalization failure remains. We do not
change the headline denominator or fit thresholds to scored shocks. Background
alarms are false alarms relative to injected-event labels, not proof the real
background lacks anomalies. See [all denominators](../results/acquisition/analysis/alarm_denominators.csv).

## One intentional correction, frozen before comparison

The [pre-edit diagnosis and predicted consequence](../docs/REGIONAL_ACQUISITION_CORRECTION.md)
records evidence from the diagnostic smoke and first two background reconstructions.
Subthreshold scores sometimes changed the best group toward an affected group.
The only tested modification, **M3b**, therefore separates spending an existing
acquisition budget from declaring an alarm: after the same probe update, allocate
to the current positive argmax; rotate if all scores are zero. Keep the same
42 exploratory extra reads,209 total attempts, probe stream, model, observations
and shock magnitude conventions. No score redesign or extra-reading feedback
was added. This is an intentional method change, not a patch claiming the old
policy was wrongly implemented.

Calibration uses the same earlier96 unmodified updates and excludes the first8
alarm steps. M3b gets its own fine/joint quantiles because it observes different
records. All legacy thresholds remain unchanged. Its effective standardized
fine alarm threshold is about20.586, compared with19.708 for M3; the correction
was not a lower alarm threshold to manufacture detections. No model parameter
or waveform was tuned. Raw/adjusted interval scales and widths are retained.

The [freeze](../results/acquisition/frozen.json) predates comparative outcomes:
16 fresh-seed episodes, four predetermined development backgrounds, localized,
exact-cancellation, delayed-aggregate and no-shock conditions; nonzero magnitude3
under the existing feasibility reductions. Four original b00 episodes are a
separate explanatory diagnostic. Fresh seeds on reused backgrounds are not an
independent held-out study. The four chosen backgrounds are the first replay
context in each development week; they do not span every time-of-day context.
The frozen seed parity makes these four localized disturbances increases, so
the fresh check does not independently test localized decreases. No episode
was dropped or replaced after scoring. M0,M2,M3,M3b,M3b_fixed,M4 receive comparable numerical
precision and cache opportunities. M3b_fixed receives the exact acquired trace
sequentially, never future decisions. M3/M2/M4 original-episode outputs are reused
only after matching source, seed, model and target conventions.

## Corrective results

| Fresh-seed result (12 disturbances plus4 no-shock controls) | Random M2 | Original M3 | M3b | Streamed fine M4 |
|---|---:|---:|---:|---:|
| Shock changes its paired-background schedule |0/12|0/12|3/12|0/12|
| Alarm within frozen detection limit |8/12|6/12|4/12|9/12|
| Correct group localization within limit |2/12|2/12|2/12|3/12|
| Affected-household1h MAE, kWh/half-hour |0.26668|0.26213|0.26602|0.20528|
| Regional1h MAE on localized/delayed families, kWh/half-hour |43.314|47.064|45.859|43.352|
| No-shock alarmed updates |14/192|15/192|14/192|31/192|
| Attempted fine records per update |209|209|209|4194|

M3b changes two localized schedules and one cancellation schedule; it changes no
delayed-family schedule. Those changes add77 affected record/time accesses in
localized cases and120 in cancellation relative to its own background policy.
That demonstrates legal observation-sensitive action under the same budget.
It does **not** demonstrate better recovery: cancellation and delayed cases each
have0/4 correct localizations for M3b, M3 and random. M3b gets1/4 raw detections
in each of those families versus2/4 for M3. Coincident background alarms must not
be credited as shock information: matched-background detection/localization
excess is retained in the [per-episode table](../results/acquisition/comparison/episodes.csv).
Even an aggregate-only detector can coincidentally name an affected group during
an exactly invisible event; its observations remain unchanged.

M3b local MAE is 0.25% below random but1.49% above original M3. The four paired
background M3b-minus-random differences are[-0.000822,+0.004144,-0.004348,-0.001597]
kWh; versus M3 they are[+0.001232,-0.001550,+0.002227,+0.013681]. These are small,
heterogeneous descriptive differences, not evidence of superiority or equivalence.
No independent-household/hour confidence interval is manufactured. The four
original diagnostic episodes remain separate from fresh seeds; one localized
schedule changes, with no new localization beyond the original result.

The strongest same-information fixed representation agrees with M3b at all 960
comparison updates: maximum absolute mean/variance discrepancy 0.0. Numerical
representation alone adds no predictive benefit. The inherited conditional
Gaussian evidence-replacement machinery is correct for its fixed working model;
selection-aware distributional calibration is not claimed. Legacy reproduction
also compares20 unchanged episode/method combinations, finding maximum saved
metric difference 0.0. The extension of the replay API did not change original
M0/M2/M3/M4 behavior in these matched checks.

Every limited method spends10,032 attempts per48-update episode. In the fresh
comparison M3b spends160,512 attempts, returns158,116 finite readings, and transmits
2,666,496 modeled fine-message bytes. Random returns157,972 and M3 returns158,164;
missingness is charged consistently. Streamed fine spends3,220,992 attempts and
51,585,024 fine-message bytes. These are simulated communication/access amounts,
not measured remote network traffic. The shared provider still scans4194 records
per update to supply16 derived totals/masks; evaluator cache reads are separate
from estimator access. No raw Parquet rescan or new big-data claim is introduced.

Complete per-method update medians are about70-71ms, including access/policy,
inference and the current summary scan; whole-job time also includes evaluation,
serialization and common window setup. All 16 leaf factors and the separator are
rebuilt each advancing window. Thus there is no demonstrated locality, reduced
factor count or speed benefit from this correction. Numerical performance stays
on GPU; no CPU solver campaign was run. Comparison peak allocated GPU memory is
181,463,552 bytes and host RSS1,461,207,040 bytes. Shared covariance storage and
host evidence windows remain counted in the inherited cost records. Evicting
conditional detail still does not beat the streamed fine reference's retained
summary floor. See [cost columns](../results/acquisition/comparison/episodes.csv).

## Tests, limitations and current research claim

Nine focused tests pass: an accessible above-threshold innovation changes actual
available reads; no-change/below-drift controls; hidden cancelled unread changes;
non-cancellation of opposite observed innovations; explicit available/exhausted
budgets; current-probe timing and the absent extra-reading feedback; stale/window
restoration; FP64 GPU same-evidence covariance/forecast consistency and changed
window evidence; and positive subthreshold ranking for M3b. The GPU restoration
check has0.0 discrepancy; moving the evidence changes forecast means by 0.162096,
so the test would detect a stale unchanged cache. These controlled inputs prove
behavior, not realistic event detection. The smoke also exercises the actual
extended replay path and same-trace comparator on the earlier calibration segment.

There was one incomplete initial transfer extraction, followed by successful
extraction after transfer completion, and one diagnostic-summary failure because
a no-shock event has an empty event window. Both are preserved/charged; neither
changed inference or the scientific benchmark. The empty summary now explicitly
uses0 for its event-only maximum. No unexplained numerical failure occurred.
No Stage 3 headline correction was required. Original files and negative results
remain intact.

The theoretical null-space/observability result remains established mathematics:
if the observed operator annihilates a perturbation through the horizon, identical
noise laws imply identical macro observation distributions. Additional acquired
rows can remove blindness but do not guarantee detectable signal. MRF/hierarchical
Gaussian inference, conditional message reuse, residual triggers, active sensing
and exploratory sampling are established prior methods. The
[Stage 3 primary-source comparison](../docs/REGIONAL_SHOCK_STUDY_PROTOCOL.md) includes
Jurek/Katzfuss, Sun/Work event-based estimation, Han stochastic triggering and
controlled-sensing quickest detection. Their assumptions do not turn this simple
finite-window heuristic into an optimal or exactly calibrated detector. No new
literature-equivalence or publication-readiness claim is made here.

Plain answers to the requested research questions:

1. **Why unchanged?** Actual observations and usually scores changed, but the
   threshold/hold selection state did not; no budget block or lost overlay caused it.
2. **Defect, method or information?** Predominantly a method/statistical limitation,
   with some probe opportunity limits. The original path passes a controlled
   action-response test. M3b is a method change, not a retroactive bug fix.
3. **Useful changes under the same budget?** M3b responds in3/12 fresh shocks and
   acquires more affected readings, but does not improve correct localization or
   overall local error relative to original M3. Subthreshold response is insufficient.
4. **Better than simple acquisition; representation benefit?** No convincing
   advantage over random acquisition; same-evidence representations are identical.
5. **Supported claim now?** An auditable failure mechanism: aggregation blindness,
   observation opportunity, innovation ranking, declaration thresholds and posterior
   representation are separate constraints. Correct Gaussian refinement does not
   itself make a policy informative or effective. This is an explained negative
   pilot plus one measured correction, not a demonstrated new refinement method.

The precise next question is **whether acquired innovations distinguish the local
change from ordinary background variability well enough for any fixed-budget
ranking rule to be useful**, before adding more adaptive machinery. The present
high thresholds, unchanged localization and failed small correction motivate that
identifiability/power question; they do not authorize another experiment or a model
search. Preserve the separate BDCC boundary: no traffic graph aggregation,
Matheron reconstruction, selective simulation or information-versus-Monte-Carlo
contribution was imported. The original RJD failure and Stage 2 streamed-memory
comparison remain negative results.

## Reproduction and handoff

The GPU comparative source and final focused-test source are18fe4af. The final
containing commit adds analysis, documentation and closure; it is reported by
`git log -1`. Configuration/model/source/calibration hashes are in the freeze.
The actual commands, failed attempts and wall durations are preserved in the
[resource ledger](../results/acquisition/resource_ledger.json). Principal commands:

```bash
python scripts/acquisition_job.py --label reconstruct_all --timeout 600 -- python scripts/diagnose_acquisition.py
python scripts/acquisition_job.py --label correction_tests --timeout 60 -- python -m pytest -q tests/test_acquisition.py
python scripts/acquisition_job.py --label correction_smoke --timeout 90 -- python scripts/replay_acquisition.py smoke
python scripts/acquisition_job.py --label correction_calibration --timeout 90 -- python scripts/replay_acquisition.py calibrate
python scripts/acquisition_job.py --label freeze --timeout 30 -- python scripts/freeze_acquisition.py
python scripts/acquisition_job.py --label paired_comparison --timeout 600 -- python scripts/replay_acquisition.py run
python scripts/analyze_acquisition.py
python scripts/analyze_acquisition_comparison.py
python scripts/audit_acquisition.py
```

Closed ledgers refuse further execution, and the comparative launcher refuses to
overwrite results. These are reproduction references, not permission to reset
caps. Figures are generated only from saved outputs:
[observation-to-action counts](figures/acquisition/observation_action.pdf),
[annotated observed-but-not-acted trace](figures/acquisition/observed_not_acted.pdf),
and [corrective accuracy/access tradeoff](figures/acquisition/corrective_tradeoff.pdf),
with SVG counterparts in the same directory.

The [closed handoff](../results/acquisition/resource_handoff.json) records
**25.326328 allocation minutes** for this stage, including a conservative90-second
initial-transfer/setup charge and five-minute final-copy reserve. Cumulative
regional charge is 168.766289 minutes, leaving **11.233711 minutes** of the original
180. The30-minute stage cap was respected. Charged supporting CPU time is
17.437051 additional minutes, including a four-minute transfer/admin allowance;
cumulative91.668949 minutes leaves268.331051 of the original six CPU hours.
The original reconstruction job took370.910 seconds and comparative GPU job
377.111 seconds. Setup, retries, calibration, tests, idle/local work and copies
are included in allocation, not just device-active time.

The ledger closed at 23:41:53 UTC with reserved handoff through 23:46:53 UTC.
Closed-stage cloud billing idle remains separately recorded; the pod was still
allocated during that idle. No experiment remains running. Final inventory shows
an idle GPU with no compute process. Completed artifacts are copied locally and
transport/hash-verified in the durable manifest. London April-December 2013 and
BDG2 seals remain intact; the original main study stays disabled. The pod and
storage remain allocated and intact. No next stage is started or authorized.

The [durable inventory](../manifests/regional_acquisition_durable.json) records
matching local/pod transfer hashes for every completed result. Final source and
reports are committed on main with a normal push; no branch or history rewrite.
