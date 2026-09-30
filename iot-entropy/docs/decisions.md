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
