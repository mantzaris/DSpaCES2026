# Research progress

Updated 2026-09-30. Work is active on `main` in this directory.

The full 791-line specification has been read. Part C was extracted without changes and its 13 CPU checks passed. These are arithmetic checks only. No detector performance has been established.

Runpod access works with the configured SSH agent/default identity. Hardware is NVIDIA RTX PRO 4500 Blackwell with 32623 MiB, driver 580.178.04, Python 3.12.3, PyTorch 2.8.0+cu128. Local Python is 3.8.10 and local Torch is 1.10.1 CPU. Remote project files stay under `/workspace/iot-inconsistency`.

CPU and CUDA saved-input parity passed. CUDA maximum score-component absolute differences were 1.11e-16 in float64 and 8.56e-8 in float32. Seven initial integration tests passed locally, including withheld-value noninterference, upstream duplicate invariance, conflict rejection and attribute-sensitive graph predictions. These tests use an untrained model and do not establish predictive quality.

Intel and SKAB downloads are pinned. SKAB contains 35 CSV files, including one anomaly-free file. Dataset adapters and split manifests are implemented for three simulator configurations, Intel and SKAB. The initial cached manifests still need the final fault protocol and latent-truth export audit before being called frozen. Core scoring, costs, normalization, witness partitioning, association discovery, PCA, GDN and conditional diffusion modules are implemented. Full-method source review and the novelty matrix are in `literature`.

An isolated Runpod environment now has pinned research dependencies. Current stage is model profiling and the end-to-end inference implementation. Remaining stages are full comparator verification and training, development selection, frozen calibration and testing, ablations, graph persistence and UI, figures and manuscript verification.

Resume from this directory

```bash
python3 reference/reference_score.py
python3 scripts/audit_equations.py --device cpu
bash scripts/runpod.sh sync
bash scripts/runpod.sh exec .venv/bin/python scripts/audit_equations.py --device cuda
bash scripts/runpod.sh pull
```

Do not infer completion from this file's existence. Read result manifests and run statuses. No submission or new paid resource is authorized.
