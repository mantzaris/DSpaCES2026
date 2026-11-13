# Camera-ready revision: supporting analysis and provenance

This note records the focused analysis and bookkeeping supporting the revision
of **From Detail to Decisions in Regional Energy Twins**. All paths below are
relative to `regional-energy-twin/`, unless prefixed by `manuscript-revised/`.
The new analysis uses preserved scores, traces, numerical summaries and source
code. It uses no raw meter values, new model fit, policy replay or GPU computation.
Historical results and resource ledgers remain read-only.

## 1. Comparison baseline and author information

The revision begins at commit `c2ef65803307ea1652d359dc3e530e3c6af40193`.
`manuscript-revised/baseline/manuscript/` preserves the initial manuscript and
assets; `internal/baseline_manifest.json` records their hashes and the original
tracked research files. The original source SHA-256 is
`eae56e2456e0c9c0a858d6724f1699a41951cb50dc677cd399befd3490560d8d`;
the original PDF SHA-256 is
`42cf5f915d2fee4550fbe3d3bf13713540e086b12b544a6c91bcd73052d3fa78`.

The current title, reviewer-described counts, scale, single-author block and
ambiguous payload sentence match the review's content. No authenticated regional
submission receipt or separate uploaded PDF was found. This supports use of the
preserved current draft as the comparison baseline without asserting byte identity
with a submission-system upload. An older editorial abstract is not substituted
for the current author-edited abstract.

The title and abstract are preserved. The abstract body SHA-256 is
`2e545e3e2c7f96765cb39f7c146992555ab44ecaf1a86f4a5836784e5b438a38`;
`generated/numbers.tex` is unchanged, including the abstract's effect-size macro.

At revision start, the available approved record documented only Alexander V.
Mantzaris, School of Data, Mathematical and Statistical Sciences, University of
Central Florida, `alexander.mantzaris@ucf.edu`. The user subsequently confirmed
**James H. Korris** as second author, Creative Technologies Inc., Hollywood, CA,
USA, `james.korris@cretecinc.com`. The revised source and PDF metadata use that
confirmation. The initial saved-artifact audit's statement that no second author
was documented describes its original inputs; it is superseded by this explicit
author approval. No submission-system metadata was inspected or changed, so upload
consistency remains an author check.

The official [DSpaCES workshop page](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home)
was refreshed on November 10, 2026. It retains a ten-page full-paper limit including
references, IEEE formatting and case-study eligibility; the current page gives
November 22 for camera-ready submission. Generic camera-ready instructions could
not be retrieved. This revision does not infer additional presentation, waiver or
supplement conditions.

## 2. Gate parameter and calibration provenance

Sources: `configs/regional_shock.json`, `results/shock/calibration.json`,
`results/shock/calibrate/scores.csv`, `scripts/prepare_shock.py:25-31`,
`scripts/replay_shock.py:226-244`, and
`src/evidence_fusion/shock_access.py:79-89`. Executable calculations and hashes are
in `manuscript-revised/scripts/audit_provenance.py` and
`manuscript-revised/analysis/provenance_checks.json`.

Calibration origins run from January 3, 2013 at 00:00 through January 4 at 23:30:
96 half-hour updates, using source clock labels without assuming UTC alignment.
The preparation adds 23 prior warm-up intervals, beginning January 2 at 12:30,
and future target support through January 5 at 05:30. The acquisition and alarm
quantiles exclude steps 0-7, leaving 88 updates from January 3 at 04:00 onward.

The acquisition threshold is the NumPy default linear 98th percentile of M1's
maximum group score on those 88 updates, giving **13.433376677685528**. The first
calibration pass runs M0/M1 to set that threshold. Its separate score file was not
retained. The saved second-pass M1 scores reproduce it exactly; the fixed probe
stream and shared M0 forecast reference do not depend on subsequent fine requests.

The decay 0.8 and offset 2.0 are fixed heuristics. They appear in the configuration
and are hard-coded in `ProbePolicy.update`; modifying those JSON fields alone
would not change the historical executable. They are not fitted by the calibration
pass. No documented tuning experiment or optimality rationale was found. The
diagnosis is conditional on these settings, and this revision does not run a
sensitivity study or make claims about other acquisition parameters.

Alarm calibration uses the same 88 updates but a different computation: it fits
95th-percentile macro/fine normalizers and then a method-specific 98th-percentile
joint maximum. The target is an alarm on any channel per update, not a per-meter
alarm. Its empirical calibration count is 2/88 (2.2727%), not an exact 2% guarantee.
M3 later alarms on 30/384 unmodified updates (7.8125%). Removing eight startup
updates from every control episode still gives 17/320 (5.3125%). Startup does not
fully explain the difference.

Prediction-interval calibration is separate. `replay_shock.py:172-178,240-244`
uses 90th-percentile absolute standardized forecast errors over **all 96 forecast
origins**, by method, horizon and query level. It does not apply the eight-update
exclusion; household errors retain every sixteenth finite ordered entry for
bounded storage. For the selected largest-cohort, eight-group uncertainty policy
in panel A, one-hour regional coverage is 19/32 = 59.375%. On panel B's unmodified
controls, M3's one-hour regional coverage is 277/384 = 72.1354%, increasing to
323/384 = 84.1146% after interval adjustment. Mean interval width increases from
106.008467 to 149.307152 kWh. These B values describe M3, not every method.
Sources are `results/refinement/replay/outcome_summary.csv` and
`results/shock/analysis/episode_forecasts.csv`.

## 3. Verified event-window correction

The original panel B analysis uses
`onset <= step < onset + config['detection_limit_steps']`
(`scripts/analyze_shock.py:71`). The frozen configuration value is 6. Consequently
the published B detection/localization counts use **lags 0-5**, six instants in
a half-open three-hour interval, with the final sampled instant at 2.5 hours.
The old manuscript's uniform description as lags 0-6 inclusive was inaccurate.

Panel C's `scripts/analyze_acquisition_comparison.py:45` uses
`step <= onset + 6`; its original counts really use **lags 0-6 inclusive**. The
revision preserves all principal-table values and corrects their panel-specific
labels. The new threshold comparison uses the requested lags 0-6 inclusive for
every method. No original result is silently replaced.

| Method | Original B detection, lags 0-5 | B detection at frozen threshold, lags 0-6 | Original B localization | Control alarms |
|---|---:|---:|---:|---:|
| M0 Aggregate | 37/96 | 43/96 | 20/96 | 36/384 |
| M1 Probes | 17/96 | 17/96 | 11/96 | 15/384 |
| M2 Random | 33/96 | 35/96 | 14/96 | 25/384 |
| M3 Gated | 29/96 | 31/96 | 15/96 | 30/384 |
| M4 Full fine | 42/96 | 42/96 | 15/96 | 41/384 |

Thus M0 localizes more events than M3/M4 at the original operating points, while
M4 detects more than M0 in the original window. Extending the window changes that
comparison and must be identified. The correction does not change the late-action
finding: additional affected identities in the corrective trace first appear at
lags eight and nine, beyond either window. Misses in the original delay metrics
remain assigned seven half-hour steps.

`analysis/alarm_cohort_window_audit.csv` records both windows for both panels.
Panel C's original M0/M2/M3/M3b/M4 detection counts are 10/8/6/4/9 of 12;
applying lags 0-5 instead would give 9/7/6/4/9. Original localization counts are
reproduced only at the original thresholds, not extrapolated across thresholds.

## 4. Fixed-evidence alarm-threshold comparison

The new analysis reads `results/shock/run/alarms.csv.gz`,
`results/shock/analysis/audited_alarms.csv.gz`, `results/shock/run/episodes.json`
and `results/shock/calibration.json`, with code and original summaries used to
verify definitions. The raw and audited alarm files have identical continuous
scores and alarm flags; the audit only adds informative-reading counts.

`replay_shock.py:132-146` records the normalized score

```
R = max(max_group_innovation / q_macro,
        max_acquired_fine_innovation / q_fine[method]) / q_joint[method]
```

and alarms when `R > 1`. Reconstructing this score from retained maxima and
calibration constants gives maximum absolute discrepancy 4.44e-16. The sweep
replaces the final alarm decision by `R > lambda`, keeping calibration constants,
requests and observations fixed. It is equivalent to scaling both effective alarm
channel thresholds by lambda.

The acquisition trigger is separate (`replay_shock.py:40,88-105`). Alarm flags
are computed after inference and only logged/scored; they do not feed acquisition,
its shared forecast reference or the next inference update. This makes this
particular alarm sweep valid fixed-trace post-processing. Changing the acquisition
gate, decay, offset or ranking would require sequential replay and is not evaluated.

Detection is any alarm at one of seven instants, onset through onset+6 inclusive,
over 96 synthetic demand episodes (six families x two magnitudes x eight backgrounds).
Measurement-fault and unmodified episodes are excluded from that denominator.
False-alarm rate is alarmed updates divided by all 384 updates in eight unmodified
episodes, including startup as in the principal table. The two axes have different
units of observation: event detection probability versus per-update false-alarm
rate. "Unmodified" means no injected event, not verified absence of real anomalies.

For ceiling alpha and n=384 control scores, the script sets k=floor(alpha*n) and
chooses the sorted score at zero-based index n-k-1. Under the strict `>` rule,
there are at most k alarms. Ties are excluded as a block, without interpolation
or fractional decisions. Threshold choice uses controls alone, not event labels.
One control update is 0.2604167 percentage points; exact nominal 2%, 5% and 10%
are therefore unattainable with this denominator.

| Method | Detection at 7/384 control alarms (1.8229%) | At 19/384 (4.9479%) | At 38/384 (9.8958%) |
|---|---:|---:|---:|
| M0 Aggregate | 8/96 | 19/96 | 43/96 |
| M1 Probes | 6/96 | 17/96 | 39/96 |
| M2 Random | 8/96 | 27/96 | 43/96 |
| M3 Gated | 8/96 | 19/96 | 41/96 |
| M4 Full fine | 8/96 | 17/96 | 38/96 |

All displayed methods attain exactly the same empirical counts at each ceiling;
there is no additional tied-score shortfall at these selected points. This is
exact empirical count matching, not a population false-alarm guarantee. The
results do not establish an adaptive advantage. Near 2%, several methods have
identical detection counts, which is not proof of equivalence.

`analysis/alarm_matched_rates.csv` retains exact thresholds and counts;
`analysis/alarm_threshold_sweep.csv` retains all score breakpoints. The vector
plot `figures/alarm_sweep.pdf` / `.svg` marks original published points and
inclusive-window frozen points separately. The main paper uses the compact table.
`analysis/alarm_background_counts.csv` preserves background-level counts rather
than treating shared updates as independent trials.

This is retrospective description on eight backgrounds from four development
weeks. The same development controls determine and evaluate the displayed rates.
There is no independent calibration, significance test or confidence interval
based on independent household/update assumptions. Event labels describe the full
curve but do not choose its three tabulated operating points.

Localization cannot be faithfully swept from the saved maxima and original
alarmed-group lists: these do not recover every group's continuous score at each
new threshold. The analysis therefore never reuses old localization flags for new
thresholds. Additional reconstruction/replay would be needed for that optional
extension; it was not undertaken. Independent chronological validation is also
deferred. The sealed London April-December 2013 outcomes and all BDG2 seals remain
unchanged, as do the disabled original studies.

## 5. Corrected payload accounting

`results/shock/analysis/cost_summary.csv` reconstructs fine payloads from actual
calls (`scripts/analyze_shock.py:32-35`), correcting the raw cost log's common
header-count heuristic for M4. `ObservationChannel.read`
(`src/evidence_fusion/shock_access.py:28-44`) charges 16 bytes per attempted record
plus 64 bytes per call, including attempts returning missing data. M3 makes two
calls per update, for 41 probes and 168 additional records; M4 makes one call.

`ObservationChannel.summary` charges 16 float64 group sums (128 bytes), a packed
native missingness mask (ceil(4194/8)=525 bytes) and 64 bytes of framing: 717 bytes
per summary. The totals below cover all 112 episodes x 48 updates = 5,376 updates,
including unmodified and sensor-fault controls.

| Quantity | M3 | M4 |
|---|---:|---:|
| Attempted fine records | 1,123,584 | 22,546,944 |
| Finite returns | 1,106,434 | 22,204,000 |
| Fine read calls | 10,752 | 5,376 |
| Fine payload bytes | 18,665,472 | 361,095,168 |
| Summary payload bytes | 3,854,592 | 3,854,592 |
| Total payload bytes | 22,520,064 | 364,949,760 |
| Total decimal MB | 22.520064 | 364.949760 |

The M4/M3 attempted-read ratio is **20.06698565**. Per-call overhead changes the
fine-payload ratio to **19.34562212**; adding common summaries gives the
total-payload ratio **16.20553831**. These are distinct quantities. Simulated
consumer communication is not measured network traffic, Parquet storage,
host-to-device transfers or provider computation. Summaries still require scanning
all households at the provider. No new physical network measurements were made.

## 6. Bookkeeping moved from the main paper

These preserved measurements provide context without claiming inference capacity
from archive size. All MB and GB in this table are decimal; the historical device
capacity reported in MiB uses its explicitly different unit.

| Measurement | Exact saved value and original rounded wording | Source |
|---|---|---|
| Downloaded archive | 801,674,949 bytes; 801.67 MB ZIP | `manifests/regional_source.json`, `bytes` |
| Expanded CSV | 8,542,818,238 bytes; 8.54 GB | Same manifest, `files[0].bytes` |
| Typed partitioned Parquet | 528,822,113 bytes; 528.82 MB | `results/regional/ingestion.json`, `parquet_bytes` |
| Successful ingestion | 356.008520352 seconds for 167,932,474 source rows; about 471,709 rows/s, rounded to 472,000 in the original paper | Same ingestion artifact, `seconds` and `source_rows` |
| Ingestion peak process RSS | 3,361,779,712 bytes; 3.36 GB | Same ingestion artifact, `peak_rss_bytes` |
| Shock separator after eviction | 2,365,440 bytes; 2.365 MB | `results/shock/analysis/cost_summary.csv`, `median_after_eviction_bytes` |
| Fixed-trace retained query state | 41,017,344 bytes; 41.017 MB | Same cost summary, M3_fixed `median_state_bytes` |
| Shared/private temporal covariance storage | 38,651,904 bytes; 38.652 MB | Same cost summary, M3_fixed `median_detail_bytes`; Stage 3 report's resource explanation |
| Host evidence cache per method | 805,248 bytes; 0.805 MB | 4194 x 24 x 8-byte values; `scripts/replay_shock.py` logs `window_cache_bytes=cache.values.nbytes`; Stage 3 report |
| Comparison-process GPU allocation peak | 182,486,528 bytes; 182.49 MB | `results/shock/run/summary.json`, `peak_gpu_bytes` |
| Comparison-process host RSS peak | 1,731,706,880 bytes; 1.73 GB | Same summary, `peak_host_bytes` |
| Input transfers per method | 5,495,422,464 bytes; 5.50 GB | Cost summary, `payload_transfer_bytes` |

Successful ingestion includes decompression, typing, partition writing and
deduplication, excluding download and prior failed attempts. The source manifest's
small cached rehash time is not network-download time; its preserved first
successful transfer plus hash took 36.37398 seconds. No archive was reread or
downloaded for this revision.

The original shock process peak is shared across comparisons, not an isolated
per-method memory-capacity experiment. Retained separator state excludes model
tensors, private temporal covariances, temporary coefficients and host caches.
Each method rebuilds 86,016 group messages and 5,376 separators across the
original replay; moving-window factor reuse is zero. M3's median and p95 complete
updates were 72.335 and 82.090 ms, versus M4's 72.403 and 82.401 ms, from the same
cost summary. These are historical GPU-context measurements, not new timing runs.

The 101,040 formal coordinates count (4194+16) x 24 latent entries; structured
elimination solves the 384-coordinate common separator rather than a dense
101,040-square system. The archive's 167.93 million rows and training's 52.11
million valid readings do not establish a comparably large simultaneous inference
dimension. These distinctions are retained in the main paper.

## 7. Figure change, reproduction and checks

Figure 2 is regenerated from `results/shock/figure_common_support.csv` and
`results/acquisition/diagnostic/steps.csv.gz` using a revision-local copy of its
plotting logic. Only the requested annotation is added. The selected episode is
`b00_cancel_exact_3.0`, paired with `b00_none_0.0`. The later score peak is at step
38, 13.5 hours after onset, following the disturbance's 12-hour end. Both scores
are exactly 24.14108145542005. `analysis/figure_annotation.json` records curve
coordinates' hashes, axis limits, source hashes and the annotation. The original
curves and event window are unchanged; `figure_changes.pdf` provides before/after
views and identifies the supplementary new sweep.

From the shared repository root, the independent analysis commands are:

```bash
python3 regional-energy-twin/manuscript-revised/scripts/audit_provenance.py \
  --project regional-energy-twin \
  --output regional-energy-twin/manuscript-revised/analysis/provenance_checks.json
python3 regional-energy-twin/manuscript-revised/scripts/analyze_alarm_sweep.py \
  --project regional-energy-twin --output regional-energy-twin/manuscript-revised
python3 regional-energy-twin/manuscript-revised/scripts/build_episode_figure.py \
  --project regional-energy-twin --output regional-energy-twin/manuscript-revised
bash regional-energy-twin/manuscript-revised/build.sh
```

The build invokes revision-local writers, compiles the clean paper and latexdiff
comparison, and builds the figure comparison. It does not invoke the historical
hard-coded manuscript/result generators. Input hashes, versions and elapsed
analysis times are in `analysis/provenance_checks.json`, `analysis/alarm_checks.json`
and `analysis/figure_annotation.json`; build logs are under `internal/`.

Focused checks cover original B/C count reproduction, control/event denominators,
score reconstruction, raw/audited score identity, strict ties, zero ceiling,
control-only threshold selection, monotone counts, lag-6 inclusion and lag-7
exclusion. Payload arithmetic and calibration quantiles reproduce independently.
These are calculation and preservation checks, not scientific validation. The
small saved-output jobs take seconds locally, with no GPU allocation, remote
connection or new inference. Historical ledgers and RunPod resources are untouched.
Final PDF/layout and preservation checks are recorded in the revision's validation
outputs and change summary rather than asserted from compilation alone.
