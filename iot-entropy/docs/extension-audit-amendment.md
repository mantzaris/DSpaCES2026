# Auxiliary audit frozen after primary scoring

This amendment is dated 2026-10-01 UTC, before running the auxiliary audits.
It does not change the accepted primary scores or select new test thresholds.
The extension remains exploratory, motivated by inspected v1 results.

## Support rounding correction

The inherited spatial reference code accepts `int(0.8 * 64) = 51` finite
draws. New temporal reference code requires `ceil(0.8 * 64) = 52`.
Primary v2 results preserve that inherited spatial convention. Recompute
seed-17 results with both conventions, separately recalibrating every family.
Compare the existing joint W48/W96 family with separately calibrated W48 and
W96 restrictions. Use all five dataset configurations and all existing
episodes; reuse saved joint draws and per-sensor measurements. Do not retune
features, aggregation or localization. Localization is not reevaluated in
this detection/support sensitivity. Record any incomplete configurations.

## Additional audits

For each configuration, use seed 17, the first two test blocks, and decisions
167 and 263 for paired reference fidelity. Use identical observed coordinates
and feature units supported by both references, with the ceiling convention.
Report raw coverage and energy score, spatial correlation/covariance error,
ordinal distributions, ACF and entropy coverage, widths and support counts.

For the first four development issuances, apply independent missingness at
rates 0, 0.10, 0.25 and 0.50 with seed 81200 plus issuance index. Report
estimator support at both windows; this is not a calibrated detection test.
Time three isolated single-episode pipeline repetitions after one warmup on
synthetic64, Intel and PEMS. Separately compare temporal kernels on identical
CPU/GPU arrays. Include failed attempts in the existing four-hour cumulative
experiment ceiling; a higher ceiling requires explicit user authorization.

## Expanded recording reuse audit

The selected PEMS blocks avoid original primary fault trials and the six-unit
fidelity audit, but all overlap the original global-window diagnostic
(`experiments/sensitivity/global.json`, W816, horizon 1020). Therefore they
are **not untouched real-data validation**. Intel backgrounds were already
identified as reused. No remaining contiguous 312-row PEMS candidate avoiding
all those inspections was identified. Retain the frozen blocks and disclose
this qualification instead of selecting another background after evaluation.
Independent new synthetic simulations provide the new-background comparison.
