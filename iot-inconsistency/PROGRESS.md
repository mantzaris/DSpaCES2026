# Graph-flow revision in progress

Updated 2026-10-01 UTC. The new authorized study is under `results/graph_flow_v1/`. Work remains on `main`, with local commits only. Unrelated `iot-entropy` modifications are present and are not part of this task.

The live repository and GPU workflow were inspected. The authorized RTX PRO 4500 is reachable. The old study is preserved by hashes in `results/graph_flow_v1/legacy.json` and the exact paper archive `paper/legacy/witness_20260930.tar.xz`. Existing result files and evidence bundles remain immutable. The current main paper still describes the legacy study until the new experiments are complete.

The eight scalar reference groups passed. Ten new CPU tests passed for inverse/Jacobian consistency, masking and copies, density normalization, mixture arithmetic, Gaussian integration/posterior moments, unit changes, weighted CRPS and wrong-target damage. Neural graph-conditioned flow and corruption/repair kernels are implemented. GPU model training, development selection, final scoring, production audits, new graph exports and manuscript revision are still pending.

The finite pre-evaluation protocol is in `docs/graph_flow_protocol.md` and `configs/graph_flow_v1.json`. No new final test has been scored. Real environments have prior project exposure. Fresh synthetic final trajectories will be generated; training/development/calibration retain the original observations so the legacy comparator receives the same training data.

Current local verification

```bash
python3 reference/reference_graph_flow.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python3 -m pytest tests/test_graph_flow.py -q
bash scripts/runpod.sh status
```

## Preserved legacy completion record

Updated 2026-09-30. Work is on `main`. The user will perform the final push. No branch, paper submission or new paid resource was created.

The full specification was read and implemented. Part C was extracted and executed before the PyTorch implementation. Its 13 checks passed. Identical saved inputs passed CPU/CUDA parity. All 16 integration tests passed locally and on the GPU host. Independent production auditing reconstructed 8,736 candidate scores from 1,092 primary test cases, with maximum absolute arithmetic discrepancy 7.11e-15.

All finite stages are complete, including revised training, primary evaluation, inference ablations, native SKAB events, model export, GPU verification and corrected stress analysis. The existing RTX PRO 4500 Blackwell was used. The remote directory remains `/workspace/iot-inconsistency`. All 78 inference states are preserved locally in `results/model_weights`, with exact-array and deterministic checkpoint-replay verification. Optimizer checkpoints remain on the pod. Ordinary CUDA reduction repeatability is measured separately and is not claimed to be bitwise exact.

The paper is complete at `paper/main.pdf`, in standard IEEE conference format with 10 pages including references. It reports a limited S32N precision benefit at 10% screened-candidate coverage, its reversal at broader coverage, stronger PCA detection, association ambiguity, failed robustness conditions and measured costs. Native process labels remain separate from injected sensor and association faults. The conventional total-error PCA supplement is explicitly distinguished from the frozen channel-maximum primary comparison.

Neo4j stores versioned evidence for ten saved review cases. The node-link interface passed browser verification. Confirm, reject and defer records are labeled automated interface tests, not human diagnoses. Repeated evidence import changes no entity counts. The four required scientific figures and two supplemental plots come from saved outputs with source and output hashes.

`results/audits/final.json` records the completed artifact checks and current manuscript hash. `results/paper_claims.json` maps generated values to saved results. `CLAIMS_AUDIT.md`, `equation_audit.md` and `DECISIONS.md` state the claim limits and corrections.

The Git distribution now uses six compressed evidence bundles. Exact primary and secondary JSON records are preserved. Compact arrays omit repeated witness draws while retaining all primary inputs and score components. The new publication audit reconstructs all 8,736 test candidate scores, verifies all 40 PCA settings and repeats E4 on 21 complete examples. The earlier full E4 audit remains available. All 22 local tests pass, including exact restoration, protection of edited evidence and array fidelity. Neural weights, full draws and superseded runs remain locally and on the pod, outside Git.

Rebuild the paper from committed evidence, without training or dataset acquisition

```bash
python3 scripts/package_results.py restore
python3 scripts/audit_publication.py
python3 scripts/figures.py
python3 scripts/make_paper.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
```

The publication audit checks the saved paper before regeneration. Repeating `scripts/audit_final.py` or the all-case predictive-draw audit requires the full experiment archive. Restoration refuses to overwrite edited files. `python3 scripts/package_results.py verify` checks bundle contents without expanding them.

Restore the local review application

```bash
bash scripts/neo4j.sh start
python3 scripts/persist_graph.py
python3 operator/server.py
```

Open `http://127.0.0.1:8099`. The database and viewer bind to loopback. Inspect the existing pod with `bash scripts/runpod.sh status`. Experiment stages are already complete and need not be relaunched. Reproduction and stage commands are in `README.md`. Preserve the published outputs before any new experiment. The user will push the final local commits when ready.
