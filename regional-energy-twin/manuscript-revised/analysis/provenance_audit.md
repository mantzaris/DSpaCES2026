# Parameter, payload, calibration and author audit

This is a saved-artifact audit for the camera-ready revision. The original project
is read-only. Calculations are reproduced by `scripts/audit_provenance.py`; exact
values, input hashes and elapsed CPU time are in `analysis/provenance_checks.json`.
No GPU, raw meter data, fit or replay was used.

## Calibration provenance and executable behavior

`configs/regional_shock.json` fixes calibration origins at January 3, 2013 00:00
through January 4, 2013 23:30 (96 half-hour updates). These are source clock labels,
not a newly inferred UTC alignment. `scripts/prepare_shock.py:25-31` includes 23
prior warm-up intervals, beginning January 2 at 12:30, and future target support
through January 5 at 05:30 for the six-hour forecast.

`scripts/replay_shock.py:226-230` first runs M0/M1 on the unmodified calibration
background and fixes the acquisition threshold at the NumPy default linear 98th
percentile of M1's maximum group score after excluding steps 0-7. There are exactly
88 retained score values, steps 8-95 (January 3 at 04:00 through January 4 at 23:30).
The resulting threshold is **13.433376677685528**. The first-pass score file was not
separately retained. The stored second-pass M1 scores reproduce this quantile
exactly; their fixed probe stream and common M0 forecast reference do not depend
on fine acquisition, as verified from `replay_shock.py:77-108,201-202`.

The decay **0.8** and offset **2.0** are fixed heuristics recorded in the config.
`src/evidence_fusion/shock_access.py:79-89` hard-codes the same values, followed by
the strict threshold and four-decision hold. They are not estimated by the
calibration pass. No parameter tuning study or recorded optimality rationale was
found. Configuration fields alone are not runtime parameters: changing those two
JSON fields would not change this version's `ProbePolicy.update` implementation.
The diagnosis is therefore conditional on the tested settings. No sensitivity
or alternative policy performance is claimed in this revision.

Alarm-threshold calibration is separate from the acquisition threshold.
`replay_shock.py:233-239` uses the same 88 post-startup updates to fit 95th-percentile
macro/fine component normalizers and then the 98th-percentile joint maximum for
each method. This is a target for any-channel alarms per update, not per meter.
The stored rate is 2/88 = 2.2727% for each method after startup, consistent with
finite empirical quantiles rather than an exact 2% guarantee.

**Prediction intervals have a different sampling detail.** The interval correction
uses the 90th percentile of absolute standardized forecast errors by method,
horizon and query level (`replay_shock.py:172-178,240-244`). It collects all 96
origins, with no eight-update exclusion. Household calculations select every 16th
finite ordered entry for bounded storage. Do not describe the interval corrections
as fitted to only the 88 alarm-calibration updates.

Suggested short main-paper wording:

> The acquisition threshold 13.4334 is the empirical 98th percentile of maximum
> group scores on 88 unmodified January 3-4 calibration updates after excluding
> eight startup steps. Decay 0.8 and offset 2 were fixed heuristics, not tuned;
> the gate diagnosis is conditional on these settings.

## Payload reconciliation

The authoritative `results/shock/analysis/cost_summary.csv` uses fine bytes
reconstructed from actual access calls (`scripts/analyze_shock.py:32-35`). This
corrects the raw cost log's common heuristic header count, which would otherwise
incorrectly charge M4 two headers per update. `ObservationChannel.read`
(`shock_access.py:28-44`) charges **16 bytes per attempted fine record plus 64 bytes
per call**, including attempts returning missing values. M3 makes two calls per
update (41 probes and 168 extra requests); M4 makes one all-household call.

Each shared summary has 16 float64 sums = 128 bytes, a packed missingness mask
of ceil(4,194/8) = 525 bytes, and 64 bytes of framing. Thus each summary is 717
bytes, or 3,854,592 bytes over 5,376 updates. This is a declared simulated exchange
format, not a measurement of physical network packets.

| Quantity, all 112 episodes x 48 updates | M3 | M4 |
|---|---:|---:|
| Attempted fine records | 1,123,584 | 22,546,944 |
| Finite returns | 1,106,434 | 22,204,000 |
| Fine read calls | 10,752 | 5,376 |
| Fine payload bytes | 18,665,472 | 361,095,168 |
| Summary payload bytes | 3,854,592 | 3,854,592 |
| Total consumer payload bytes | 22,520,064 | 364,949,760 |
| Total decimal MB | 22.520064 | 364.949760 |

M4/M3 attempted-read ratio is **20.06698565**. Different per-call overhead makes
the fine-payload ratio **19.34562212**. Adding the same summaries to both gives
the total-payload ratio **16.20553831**. These three ratios measure different things.
They are unrelated to the on-disk Parquet size, measured host-to-device transfers
or the provider scan work, which still constructs summaries from the whole cohort.

Suggested compact corrected main-paper wording:

> Estimated total consumer payload is 22.52 MB for M3 and 364.95 MB for M4, each
> including 3.85 MB of shared summaries. The 20.07-fold fine-request ratio becomes
> a 16.2-fold total-payload ratio because of common summaries and per-call framing.
> Fine accounting charges 16 bytes per attempted record and 64 bytes per call;
> summaries include group sums, a packed missingness mask and framing.

Detailed byte arithmetic can remain in the revision note to save main-paper space.
Keep the distinction from measured network traffic explicit.

## Table II and interval checks

Original panel B values reproduce from `results/synthesis/principal_results.csv`:

| Method | Detection / 96 | Correct group localization / 96 | Control alarms / 384 |
|---|---:|---:|---:|
| M0 | 37 | 20 | 36 |
| M1 | 17 | 11 | 15 |
| M2 | 33 | 14 | 25 |
| M3 | 29 | 15 | 30 |
| M4 | 42 | 15 | 41 |

M0 localizes more than M3 and M4. It detects more than M3 but **less than M4**.
Unequal false-alarm rates preclude treating this as a matched-operating-point rank.

A factual scope mismatch was independently confirmed during this revision:
`scripts/analyze_shock.py:71` uses `step >= onset` and `step < onset + 6`, hence
**lags 0-5**, whereas manuscript prose describes lags 0-6 inclusive. The reviewer
counts match the original six-instant computation. Preserve those original counts
with an explicit corrected label. Report the requested seven-instant, lag-0-6
threshold analysis separately rather than silently merging it with the old table.
The revision's alarm analysis owns the full numeric reconciliation.

Panel A's largest-cohort, eight-group uncertainty policy has regional one-hour
coverage 19/32 = **59.375%**, from `results/refinement/replay/outcome_summary.csv`.
Panel B M3 unmodified controls have raw regional coverage 277/384 = **72.1354%**,
adjusted coverage 323/384 = **84.1146%**, mean raw width **106.008467 kWh** and
adjusted width **149.307152 kWh**, reproduced from `episode_forecasts.csv`.
Interval correction widens uncertainty without reaching nominal 90% coverage.
These are not alarm-calibration quantities or proof of reliable predictive
calibration. The new threshold sweep cannot establish independent validation.

## Reviewed baseline and author discrepancy

The current source and PDF have the unchanged title, single author Alexander V.
Mantzaris, the reviewer-described scale and numerical findings, and the ambiguous
payload sentence quoted in the review. The local working tree was clean at the
revision start. This is strong content correspondence, not proof of byte identity
with a submission-system upload: no separate regional submitted PDF or receipt was
found among this project's artifacts. The preserved current source/PDF is the
best-supported comparison baseline. The historical editorial abstract differs
from the current author-revised abstract; comparison must use the current one.

The documented author block is:

- Alexander V. Mantzaris
- School of Data, Mathematical and Statistical Sciences
- University of Central Florida
- alexander.mantzaris@ucf.edu

`reports/REGIONAL_TWIN_SYNTHESIS_REPORT.md:4-8` records that this was explicitly
supplied, and `manuscript/AUTHOR_REVIEW.md:4-5` confirms it. No author-approved
second-author name, author order, affiliation or email was found for this paper.
Do not borrow a name from other projects or repository contributors. The reviewer
reports two names in submission metadata, so final consistency remains an author
action unless the user supplies the missing approved information.
