# Research decisions

- 2026-09-30: Work only inside `iot-entropy`; commit only its paths on the
  existing `main` branch. The user will push. Preserve sibling projects.
- Use the existing RunPod at the approved direct SSH endpoint, RSA identity,
  and a distinct `/workspace/iot-entropy` working copy. Keep data, outputs and
  checkpoints mirrored locally. No new paid infrastructure.
- Primary datasets are exactly the specified synthetic benchmark (three node
  counts), Intel Lab, and DCRNN PEMS-BAY. Do not replace inaccessible data.
- Only observed common rows enter each correlation. Missing input values use
  masked zero after training-only scaling for the neural network, never a
  neighbor's measurement; generated feature calculations inherit observation
  masks to compare the same support.
- Author identity and any venue requirement absent from current instructions
  remain explicit unresolved submission metadata, not invented statements.
- Preregister before full runs. Select an explicit total runtime budget after
  profiling. Preserve negative results and measure generator fidelity.
- Pilot, before full runs: all seven GPU validation gates passed. B=64 joint
  sampling took 0.20 s at 64 nodes and 0.91 s at 325 nodes; peak allocated GPU
  memory was below 0.4 GB. The 128-matrix measurement batch took 1.48 ms on GPU
  float32 and 8.41 ms on CPU float64 (different precisions, kernel only).
  Retain the compact width-24 model, 20 DDIM steps, B=64 and lambda=.05;
  numerical stability is adequate. Set a **4 GPU-hour wall-runtime ceiling**
  for this study's training, sampling and sensitivities. This is a stop limit,
  not an entitlement to spend that time. The configured pilot cost is separate
  and reported. No full/test results informed this decision.
- Current main-conference CFP explicitly states single-blind review and no
  appendix. Use the supplied author names and a self-contained <=10-page paper
  without an appendix. Workshop pages do not provide a separate supplementary
  policy; preserve reproducibility artifacts locally without assuming they
  can be submitted as reviewed supplementary material.
- Coverage amendment before Intel model training or held-out scoring: the full
  raw-span split has valid humidity coverage 4.33% in calibration and 0.257% in
  test. Apply a data-only rule: exclude the terminal suffix of at least three
  days with primary-channel marginal coverage below 50%. This selects an
  exclusive cutoff of March 24, 2004. Retain earlier short outages, all 54
  coordinate-listed motes and the original 60/15/10/15 fractions. Preserve the
  entire raw-span processed recording as `intel_full.npz`, an auxiliary quality
  view of the same dataset, not a fourth dataset. No detector scores informed
  this correction. Test-group abstention remains an outcome, not an exclusion.
- Implementation audit before full test scoring: matched-covariance faults now
  whiten/recolor the untouched event toward equicorrelation with the same mean
  correlation, preserving means/variances exactly when full rank. Rank-deficient
  short events preserve the correlation target in expectation; they are not
  claimed to satisfy exact finite-sample matching. A mathematical test verifies
  the full-rank case. Synthetic coupling-loss events modify the affected rows
  of the stable state transition, with identical process noise and a checked
  identical pre-event prefix; real-data decorrelation remains a sensor-level
  intervention. The GDN comparator and restarted four-step CUSUM deviations
  are disclosed in the implementation and manuscript.
- Sensitivity implementation frozen while primary scoring is in progress,
  before inspecting aggregate results: the global trace needs at least twice
  as many common observations as sensors. Set its window to the next multiple
  of four at or above 2.5N (minimum 96), allowing some missing rows. Report
  calibration feasibility for every configuration. At N=64, compare global
  and local scans at the identical W=160, d=40 using the same B=32 intact-block
  bootstrap samples, separate calibration maxima and the original injections.
  The trained neural horizon is only 120, so this is explicitly a longer-window
  bootstrap sensitivity. Do not credit detections after short events end.
- Include B=64 alongside B=32/128 on the identical limited subset so the sample
  count comparison is paired. For reference fidelity, fix the first six disjoint
  untouched test units in synthetic64, Intel and PEMS for three model seeds;
  calculate raw, entropy/change, correlation and covariance fidelity. These
  post-training audits do not choose or change a detector.
- Runtime accounting sums GPU-enabled stage wall times, not pod rental uptime
  or utilization-weighted kernel time. Graph-run summaries are not counted a
  second time when individual scoring statuses already contain their duration.
