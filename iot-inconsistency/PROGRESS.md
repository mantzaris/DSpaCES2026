# Research progress

Updated 2026-09-30. Work is active on `main`. The user will push at completion. Do not make branches or retry pushing.

The complete 791-line specification was read. The exact Part C oracle passed 13 checks. Saved-input CPU and CUDA arithmetic parity passed, with maximum score-component differences of 1.11e-16 in CUDA float64 and 8.56e-8 in float32. Integration checks cover witness exclusion, duplicate conflicts, fixed edge targets, masks, costs and missing predictions. These are correctness checks, not detector accuracy claims.

The existing RunPod has an RTX PRO 4500 Blackwell GPU with 32623 MiB. Project files are under `/workspace/iot-inconsistency`. Initial model runs were archived as exploratory after the fault protocol audit. Version 2 uses signed synthetic responses and paired association-attribute permutations that preserve marginal attributes and graph degrees. Native process labels remain separate from injected faults. All three dataset families are retained.

Current work is the revised training, shared baseline evaluation, development freeze and independent calibration pipeline. A 200-step pilot measured 1.24 s for eight candidates in full neural precision and 0.35 s with bfloat16 denoising. The maximum score change was 0.00352. Final score arithmetic remains float64. These are pilot timings only.

DiffAD is an independent adaptation of the paper's selection, S4 denoising, incremental conditioning and residual scoring. Its dense S4 kernel passes an independent state-recurrence test. Learning-rate selection includes the paper's value and uses only development data. PCA, GDN, backbone residual and deterministic repair alternatives are implemented. A free local Neo4j instance is running on loopback ports 17474 and 17687. Graph persistence, operator UI, final analyses and manuscript remain in progress.

Resume and inspect from this directory

```bash
python3 -m pytest -q
bash scripts/runpod.sh sync
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status training_v2
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status main_experiments
bash scripts/runpod.sh pull
```

The finite main pipeline is `scripts/continue_main.sh`. It waits for revised training, tunes/trains DiffAD, evaluates development, freezes choices, calibrates, then opens test data. It resumes completed case files. Pull excludes optimizer checkpoints; preserve those and final model weights separately before ending the project. Do not infer completion from this document. No submission or new paid resource is authorized.
