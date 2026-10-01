# Findings from the spatial–temporal extension

The completed primary study establishes no consistent overall advantage for
entropy features or for the evaluated diffusion reference. It also does not
establish that all entropy methods are inferior. All real-background comparisons
are exploratory and semi-synthetic; an expanded audit identified prior inspection
of the selected PEMS blocks in a long-window diagnostic.

## Established within this artifact

- A common row permutation preserves a complete window's correlation matrix.
  PE, sample entropy and ACF can nevertheless change. This is an elementary
  property, not a new theorem or a rolling-trace invariance result.
- All 15 primary configurations completed: 360 new fault draws,
  20 source blocks, three model seeds, exactly three primary datasets.
- Intel bootstrap T recall is 0.389, versus 0.000 for TB;
  achieved background rates are 0.103 and 0.000.
  This is an operational result at the frozen threshold, not a matched-rate
  statement about intrinsic information.
- Synthetic T minus TB unconditional localization IoU is
  -0.147 [-0.196, -0.097] for bootstrap and
  -0.138 [-0.188, -0.092] for diffusion.
- Adding entropy to B changes synthetic bootstrap recall by
  +0.003 [+0.000, +0.008]; the other five primary
  dataset/reference combinations show no recall increase at this threshold.
  This does not establish equivalence or feature redundancy.
- Intel spatial group eligibility is 0.017 / 0.049
  under bootstrap / diffusion; temporal entropy eligibility is
  0.541 / 0.633.
  Greater eligibility is not sufficient for calibration or accurate localization.
- Shared-support fidelity exposes serious diffusion entropy miscoverage.
  Intel raw energy score nevertheless improves with diffusion, illustrating
  that raw predictive fit and entropy-functional fit are distinct.

## Uncertainty and interpretation

Four recording blocks per real dataset limit uncertainty assessment. Whole-block
intervals retain repeated injections and model seeds; they are exploratory,
unadjusted and not equivalence tests. Original and extension comparisons have
different windows, seeds, support rules and localization, so a change from v1
is not automatically an improvement attributable to temporal entropy.

Nominal alpha .10 produces unequal achieved rates. On PEMS bootstrap, S/SB
recall 0.528/0.005 becomes
0.069/0.264
under a retrospective control-rate cap .10. The cap reuses evaluation controls
and is descriptive, not prospective threshold validation.

Mechanism, severity, duration, direction and observability strata are saved.
Use actual measured changes separately from deviations from expectation.
The first decision after onset is 11 samples late; raw pipeline timing does
not remove that observation/stride latency. Participation is not causal attribution.

## Corrections, secondary comparisons and budget

The original study remains at revision b900da1b and in its original namespaces.
Strict feature-pair endpoints and lagged full-matrix change are explicitly
identified extensions/corrections. The inherited 51-of-64 spatial-reference
rounding differs from the ceiling rule (52); separately calibrated correction
checks changed no event recall in all five seed-17 configurations.

The completed ledger records 15376.37 cumulative seconds
(4.271 hours), including original runs, validation and
failed attempts. The user explicitly authorized **up to eight hours total**
after the original four-hour stop. That stop and its 0.57-second check granularity
remain in the ledger. All primary comparisons, all five window/support and
calibrated scale-2 sensitivities, fidelity/missingness audits and isolated timings
completed. No declared experiment remains incomplete. CPU postprocessing and
the small known-process estimator-stability diagnostic are separate from GPU-stage time.

The separately frozen, post-primary scale-2 comparison is exploratory and reuses
seed-17 episodes, 96 original observations, and the same cached references.
Scale-2 minus scale-1 bootstrap T recall changes are
-0.093 [-0.231, +0.069] (synthetic), -0.069 [-0.458, +0.333] (Intel),
and -0.333 [-0.722, -0.028] (PEMS). Corresponding TB changes are
-0.074 [-0.245, +0.042], +0.264 [+0.000, +0.750], and -0.153 [-0.278, -0.028].
Background rates, availability and separate PE/SE outcomes must be considered;
these are not matched-rate contrasts. Scale-1 ranks exactly reproduce the
independent W96 support audit. Scale 4 in these windows does not meet the primary
template minimum and remains support-only. Native
physical-fault accuracy, stronger generative architectures, longer histories
and dashboard usability remain outside the demonstrated evidence.

## Reproducibility and submission

See README.md for exact CPU regeneration and CUDA rerun commands.
The manuscript is manuscript/paper.pdf; the interactive replay is dashboard/index.html
after running scripts/build_extension_dashboard.py and serving the directory.
results/extension-v2/claim-ledger.json links every abstract/conclusion assertion
to saved results or proofs. The numerical tests passed on the A6000 (20 tests)
and locally (18 passed, two CUDA checks skipped); the browser passed three-case
interaction checks. Final artifact hashes and PDF inspection are recorded
separately after rendering.

The verified workshop limit is 10 pages including references, IEEE two-column
format, with October 15, 2026 deadline. Parent-conference instructions are
single-blind and prohibit an appendix; a separate workshop supplement policy
was not established. AI assistance is disclosed in the manuscript. Authorship
is preserved; affiliations and email were not supplied. Nothing was submitted
or pushed. See docs/venue.md for primary policy sources and access limitations.
