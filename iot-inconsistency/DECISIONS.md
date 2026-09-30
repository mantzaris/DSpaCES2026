# Decisions

2026-09-30 user update. Continue working and committing on `main`. The user will push at completion. Do not retry push authentication or create branches. Initial commit is `83cedd9`.

2026-09-30. Use the existing authorized Runpod host and available SSH authentication. Do not create cloud resources. The provisional 48 to 96 GPU hours in the plan is not a spending authorization. Begin with bounded profiling and finite jobs on the existing pod.

2026-09-30. Keep all local work here and remote execution in `/workspace/iot-inconsistency`. Work directly on `main`. Cache reproducible third-party downloads outside Git under this directory and retain their URLs, revisions, licenses and hashes in tracked manifests.

2026-09-30. The adjacent regional energy twin manuscript concerns selective measurement access and Gaussian refinement. This study concerns sensor and association attribution using withheld witnesses. Its results, prose and scientific figures will not be reused as evidence for this study.

2026-09-30. The workshop page confirms an October 15 deadline and a ten-page IEEE two-column full-paper limit. The submission portal was subsequently verified to state October 15 at 23:59 Anywhere on Earth (AoE). No anonymity instruction was stated on the workshop or submission landing page. See literature/venue_verification.json. Source https://sites.google.com/unisalento.it/ieee-dspaces-2026/home.

The second protocol uses alternating signs in synthetic measurement responses so sign faults can be matched to valid sign metadata. Paired edge permutations preserve source and target degree counts and the marginal distributions of lag, sign, magnitude and intercept. The stored parameter mismatch remains explicitly a surrogate. A separate simulation changes a physical measurement response to examine genuinely stale associations.

All comparator residual medians and scales come from unmodified development windows. Complete calibration blocks are divided into null and labeled probability folds. The small calibration sets cannot resolve every requested nominal tail level. Report the actual attainable resolution and measured false alarms rather than claiming exact temporal coverage.

RunPod synchronization excludes `results` to prevent local progress snapshots from overwriting newer remote artifacts. Result transfer is one way from the GPU to the local project. Optimizer checkpoints remain outside routine transfer until final model export.

Before inspecting final performance, the confidence comparison was tightened to use the same screened candidate pool for all supervised probability calibrators and candidate risk curves. Early outputs may have used every baseline channel for that probability fit. `finalize_saved_protocol.py` preserves the initial calibration, refits only from the labeled calibration blocks and asserts that all null references remain unchanged. It also applies previously frozen score weights directly through the CUDA equation kernel to saved loss arrays where an early JSON record retained arithmetic-default weights. Raw predictions, detector settings and development-selected penalties are unchanged. The correction log records hashes and explicitly states that no test labels or performance guided these corrections.

The final equation comparison also retains the prespecified arithmetic starting weights kappa = 1 and lambda = 0.2 as a fixed-positive-penalty variant. This ensures the experiment examines nonzero penalties even when development selection chooses zero. It is a fixed diagnostic comparison, not a test-tuned replacement for the selected procedure.

The observation cost now casts fixed cell counts to the loss dtype before division. An independent 3/37 count-ratio test verifies float64 precision. Saved loss and replacement arrays allow affected scalar cost/score records to be corrected without changing any predictive draw or learned parameter. The correction audit records any resulting calibration-score roundoff.

## Stress-screen consistency and portable inference states

The targeted robustness script initially screened raw GDN deviations, whereas the main pipeline uses frozen development median/IQR scaling. This was found during a code audit before interpreting stress outcomes. The corrected stress version uses the same frozen scaling and stores conventional GDN/PCA target ranks as well. Any earlier stress case is retained under `pre_scaled_screening` and rerun. Primary experiment scores, hyperparameters and results are unchanged. Native SKAB scores now record the already selected penalties in the CUDA call itself.

Inference weights are exported as exact NPZ state arrays without optimizer state or pickle. The loader falls back to these portable weights when training checkpoints are absent. A final audit reproduces saved predictions from the portable weights with the original seeds. Trained PCA states are loaded directly for subsequent native/stress evaluation rather than refitted.

Secondary confidence intervals were added after viewing the primary detection results. They use the previously specified coverage levels, all dataset configurations, the common screened candidate population and whole-block resampling. They are descriptive, without multiplicity correction, and do not change the primary endpoint or frozen model choices.

## CUDA repeatability and exact portable-weight verification

A comparison with the channel-group ablation exposed small score differences even when source grouping is mathematically unchanged. A five-configuration audit traced repeatability limits to ordinary float32 CUDA graph reductions and subsequent bfloat16 denoising. Fixed random seeds alone do not imply bitwise reproducibility. Three replays of a saved input per configuration retained the same top observation; the audit records all prediction, loss and score differences. Original saved draws remain the empirical inputs for every published metric and independent float64 equation audit.

Exact known-copy invariance passed on all five trained configurations when deterministic CUDA algorithms and `CUBLAS_WORKSPACE_CONFIG=:4096:8` were enabled. Portable NPZ and original checkpoint inference are compared in that mode, with exact state and predictive-array equality. We do not replace original scores with more favorable replay outputs or describe approximate seeded replays as bitwise identical. Numerical group-renaming differences on single-channel sources are not evidence that grouping changed the mathematical method.

## Final targeted-stress sampling

The final bounded stress set uses twelve evenly spaced eligible held-out reference windows, spanning the available source blocks, rather than taking the first twelve consecutive windows. This fixes the representativeness of the diagnostic controls without increasing the case budget or selecting on results. Version `scaled-screen-stratified-v3` includes the frozen screening correction. Earlier stress outputs remain in versioned subdirectories and are excluded from final summaries. Primary test cases and hyperparameters remain frozen.

## Final PCA formula-completeness audit

The original common evaluation uses the maximum standardized sensor contribution and reconstructs only the current coordinate when summarizing each lag vector. This is now named explicitly in the paper. A final audit identified that the conventional B2 full squared reconstruction norm and the B3 mean across all embedded coordinates also needed an explicit detector evaluation. `evaluate_pca_total.py` evaluates them with the already trained PCA states, development-only rank selection and the same calibration blocks. It preserves all original primary selections and reports the additional total-error rows separately. Independent double-precision projection checks pass for both statistics. Entirely unavailable windows abstain at the declared floor and are not assigned zero error.

## Joint use of type-specific confidence

`analyze_cross_type.py` keeps frozen calibrators and evaluates observation, association and unmodified windows together as a descriptive transfer diagnostic. It was added after the illustrated case exposed simultaneous reading and association acceptance. No new exclusivity classifier is fitted. The paper and interface state that the probability map is fitted for one injected fault type against unmodified references. Strong evidence for two types exposes ambiguity rather than a unique causal diagnosis.
