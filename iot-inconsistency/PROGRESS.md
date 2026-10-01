# Graph-flow study completed

Updated 2026-10-01 UTC. Work stays on `main`, with local commits only. The user will push. Unrelated `iot-entropy` work is preserved. No paper was submitted, external site published, branch created or paid resource created.

All six finite stages are complete. The reference arithmetic and GPU pilot passed. Development, three-member model selection, calibration, final paired experiments, shared-case legacy comparisons, registered stress strata, production replay, isolated runtime, Neo4j export and browser checks completed. The new IEEE manuscript compiles to ten pages including references. Final PDF and figure checks are recorded in `results/graph_flow_v1/completion.json`.

The namespace is `results/graph_flow_v1/`. Its protocol locked at 2026-10-01 02:03:02 UTC. All sixteen frozen numerical source hashes still match. The final study has 1,500 cases and 54,080 candidates. Directional H1 is supported against both PCA and same-flow NLL, but the latter improvement misses the 0.02 practical margin. H2 remains inconclusive. H3 is not established. Intel calibration and SKAB repair failures remain prominent in the manuscript. Detailed findings are in `graph_flow_claims_audit.md`.

The eight scalar check groups and all forty tests pass. Independent production auditing reconstructs 107,620 calibration/test scores within 9.10e-13. Thirty generation bundles were replayed from trained models and saved latent draws on the existing RTX PRO 4500. The compact publication audit verifies 6,351 records and reproduces all 100 dataset/method AP values. These numerical checks do not validate the fitted distributions as physical truth.

`execution_jobs.json` preserves the failed initial audit, a reporting-variable failure during the first resume, and successful `graph_flow_finish_resume` completion at 02:45:47 UTC. Both failures were corrected without changing predictions, calibration or model selection. Database schema/data transactions were separated for Neo4j compatibility. `DECISIONS.md` records these corrections.

The original 166 tracked result files remain byte-identical. `legacy.json` hashes the full 306-file starting study. The exact old manuscript is preserved in `paper/legacy/witness_20260930.tar.xz`, including its original PDF and source hashes. Historical completion details below refer to that archive, not the current main paper.

Six new evidence bundles total 86.93 MiB. They preserve exact result JSON, compact candidate evidence and full representative generations. Raw caches, model checkpoints, temporary files and logs are excluded from Git. All required checkpoint paths were verified locally and against the existing pod. Three superseded local sklearn pickle files were never transferred and are unnecessary because the frozen portable arrays are present. The model manifest states this distinction.

No mandatory finite-stage work is blocked. Optional MTGFlow training and dynamic graph adaptation were not included. No human operator study or untouched real-environment validation was performed. A public clone supports saved-evidence replay but requires weights or retraining for model inference.

## Resume and verification commands

The GPU job is complete. Do not relaunch training merely to check its status.

```bash
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status graph_flow_finish_resume
python3 scripts/package_graph_flow.py verify
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 scripts/audit_graph_flow_publication.py
python3 scripts/figures_graph_flow.py
python3 scripts/make_graph_flow_paper.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
```

Saved summary records and graph artifacts suffice for the paper build. For individual candidate inspection, `python3 scripts/package_graph_flow.py restore` expands explicitly named compact arrays and protects edited files. Do not overwrite finalized local presentation files with a broad remote pull. The README gives isolated reproduction stages and prerequisites.

For the local operator application

```bash
bash scripts/neo4j.sh start
python3 scripts/export_graph_flow.py --persist-only
python3 operator/server.py --port 8100
```

Open `http://127.0.0.1:8100/flow`. Twenty-three saved cases cover success, failure, numerical inadequacy, ambiguity and association review. Automated browser accept/reject/defer records are separate from measurements and are not human-study evidence.

## Preserved legacy completion record

Updated 2026-09-30. Work is on `main`. The user will perform the final push. No branch, paper submission or new paid resource was created.

The full specification was read and implemented. Part C was extracted and executed before the PyTorch implementation. Its 13 checks passed. Identical saved inputs passed CPU/CUDA parity. All 16 integration tests passed locally and on the GPU host. Independent production auditing reconstructed 8,736 candidate scores from 1,092 primary test cases, with maximum absolute arithmetic discrepancy 7.11e-15.

All finite stages are complete, including revised training, primary evaluation, inference ablations, native SKAB events, model export, GPU verification and corrected stress analysis. The existing RTX PRO 4500 Blackwell was used. The remote directory remains `/workspace/iot-inconsistency`. All 78 inference states are preserved locally in `results/model_weights`, with exact-array and deterministic checkpoint-replay verification. Optimizer checkpoints remain on the pod. Ordinary CUDA reduction repeatability is measured separately and is not claimed to be bitwise exact.

The preserved paper is complete in `paper/legacy/witness_20260930.tar.xz`, in standard IEEE conference format with 10 pages including references. It reports a limited S32N precision benefit at 10% screened-candidate coverage, its reversal at broader coverage, stronger PCA detection, association ambiguity, failed robustness conditions and measured costs. Native process labels remain separate from injected sensor and association faults. The conventional total-error PCA supplement is explicitly distinguished from the frozen channel-maximum primary comparison.

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
