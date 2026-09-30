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
