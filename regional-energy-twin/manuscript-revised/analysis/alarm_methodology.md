# Saved-score alarm comparison

This is a retrospective descriptive analysis of the original panel B acquisition
traces. It reads preserved numerical outputs and code, not meter values, model
files, sealed outcomes or GPU state. No new policy, inference replay, fitting,
threshold calibration or acquisition-parameter search occurs.

## Reproduce

From the shared repository root:

```bash
python3 regional-energy-twin/manuscript-revised/scripts/analyze_alarm_sweep.py \
  --project regional-energy-twin \
  --output regional-energy-twin/manuscript-revised
```

The script refuses output paths outside the revision directory. The main-paper
fragment is `generated/alarm_matched_rows.tex`. Exact thresholds and counts are
in `analysis/alarm_matched_rates.csv`; all score breakpoints are retained in
`analysis/alarm_threshold_sweep.csv`. The supplementary vector plot
`figures/alarm_sweep.pdf` / `.svg` distinguishes original published points from
recomputed points at the requested inclusive window. All input SHA-256 values,
versions, focused checks and internal runtime are in `analysis/alarm_checks.json`.

## Verified window correction

The original manuscript and synthesis prose say lags 0 through 6 inclusive.
However, `scripts/analyze_shock.py` computes panel B events using
`onset <= step < onset + cfg['detection_limit_steps']`, and the frozen configuration
sets that value to **6**. Its reported Table II counts therefore use **lags 0-5**
(six observation instants). At half-hour cadence, the final sampled instant is
2.5 hours after onset, inside a half-open three-hour window. Recomputing from
saved alarm rows exactly reproduces all published counts and localization flags.
This is a discrepancy in the earlier description, not a change to saved results.

The later `scripts/analyze_acquisition_comparison.py`, line 45, instead uses
`step <= onset+6`. Thus panel C really uses **lags 0-6 inclusive**. Its published
counts also reproduce. `analysis/alarm_cohort_window_audit.csv` records both
windows for both panels. The principal table should retain the published values
with corrected panel-specific labels, rather than silently redefine their window.

| Method | B published detection, lags 0-5 | B detection, lags 0-6 | Published localization | Control alarms |
|---|---:|---:|---:|---:|
| M0 aggregate | 37/96 | 43/96 | 20/96 | 36/384 |
| M1 probes | 17/96 | 17/96 | 11/96 | 15/384 |
| M2 random | 33/96 | 35/96 | 14/96 | 25/384 |
| M3 gated | 29/96 | 31/96 | 15/96 | 30/384 |
| M4 full fine | 42/96 | 42/96 | 15/96 | 41/384 |

The reviewer-described observation about the **published** table remains correct:
M0 localizes more than M3/M4, while M4 detects more than M0. Adding lag 6 changes
the M0 detection count and must not be presented as the same published point.
The matched-rate analysis requested for this revision uses lags **0-6 inclusive**
for every method. In panel C, original detection counts M0/M2/M3/M3b/M4 are
10/8/6/4/9 of 12; replacing its actual window by lags 0-5 would yield 9/7/6/4/9.

## What is swept

`replay_shock.py:132-146` records

    R = max(max_group_innovation / q_macro, max_acquired_fine_innovation / q_fine[m]) / q_joint[m]

and declares an alarm when `R > 1`. The saved macro/fine maxima and calibration
constants reconstruct the saved score to maximum absolute discrepancy
4.440892098500626e-16. Raw and audited alarm files contain identical scores and
alarm flags; the audit adds informative-reading counts only.

We replace that final decision by `R > lambda`, keeping all calibration constants,
observations and acquisition histories fixed. Equivalently, both effective alarm
channel thresholds are multiplied by lambda. This is separate from the acquisition
trigger, which is read from `calibration['trigger']` at `replay_shock.py:40` and
used while selecting reads at lines 88-105. Alarm decisions are computed after
inference and are only logged/scored; they do not feed the acquisition policy,
its common forecast reference, or the next inference update. Therefore this
particular sweep is valid fixed-trace alarm post-processing. It says nothing about
changing the acquisition gate, decay or offset, which could alter future evidence.

Detection is any alarm at an episode's seven instants from onset through onset+6.
The denominator is 96 synthetic demand episodes: six families, two magnitudes,
eight backgrounds. Sensor-fault and unmodified episodes are excluded from that
denominator. False-alarm rate is alarmed updates divided by all 384 updates in
the eight unmodified control episodes, including startup updates as in the
published table. These are different observational units. The control labels mean
no injected disturbance; real backgrounds can contain unlabeled actual changes.

## Common empirical rate ceilings and ties

For a requested ceiling alpha and n=384 control scores, let k=floor(alpha*n).
The threshold is the sorted control score at zero-based index n-k-1. The strict
`>` rule yields at most k control alarms. This threshold choice uses control scores
only, never event detection labels. Tied threshold scores are all excluded and
could produce fewer than k alarms; no fractional ties or interpolation are used.

The ceilings 2%, 5% and 10% yield exactly 7, 19 and 38 alarms for every method:
**1.8229167%, 4.9479167% and 9.8958333%**. One control update is **0.2604167
percentage points**. Each selected order statistic has one equal score, so no
additional tied-score shortfall occurs at the displayed points. These are exactly
matched empirical counts, not exactly 2%, 5% or 10%, and not population-level rates.

| Method | 7/384 control alarms | 19/384 control alarms | 38/384 control alarms |
|---|---:|---:|---:|
| M0 aggregate | 8/96 | 19/96 | 43/96 |
| M1 probes | 6/96 | 17/96 | 39/96 |
| M2 random | 8/96 | 27/96 | 43/96 |
| M3 gated | 8/96 | 19/96 | 41/96 |
| M4 full fine | 8/96 | 17/96 | 38/96 |

At the near-2% point, M0, M2, M3 and M4 all detect 8/96. At the middle point,
random M2 detects 27/96, versus 19/96 for gated M3 and 17/96 for full fine M4.
The sweep supplies no adaptive-detection advantage. It also demonstrates that
full fine access's forecasting benefit is not a detection ranking guarantee.
These descriptive counts neither prove equivalence nor establish a validated
operating threshold. Event labels are used to draw the full descriptive curve,
but never to select the three tabulated thresholds.

## Dependence and localization limits

`analysis/alarm_background_counts.csv` keeps the eight backgrounds separate;
there are only four development weeks and many shared/synthetic observations.
The event and control counts are not independent binomial trials. No significance
test or independent-update confidence interval is constructed. Because the same
development controls choose and evaluate the displayed thresholds, this is not
new independent calibration or held-out validation. The sealed later period
remains untouched.

The preserved alarm files store macro/fine maxima, identities already alarmed at
the original threshold, and original correct-localization flags. They do not retain
all per-group and per-household continuous alarm values needed to recover which
affected groups would alarm at arbitrary new lambda. Neither a maximum nor the
original alarmed-group list determines that set. We therefore **do not recompute
localization at swept thresholds** and do not carry original flags across them.
The original localization counts are verified only at their original threshold.
A full localization sweep would require additional reconstruction/replay and is
not necessary for the requested bounded detection analysis.

## Checks and cost

Focused executable checks cover strict thresholds and ties, zero-rate ceiling,
order-statistic invariance, explicit lag-6 inclusion/lag-7 exclusion, exact original
panel B and C count reproduction, raw/audited score identity, normalized-score
reconstruction, event/control denominators, monotone threshold counts and rate
ceilings. All pass. These checks validate calculations, not scientific generality.
Each complete local analysis process takes about four seconds here, including
imports and plots; initial checks and figure layout were rerun during implementation.
The checks JSON records the final internal analysis runtime separately from imports.
No GPU, raw meter data, remote connection or historical ledger was used or changed.
