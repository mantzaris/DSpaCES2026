# Graph-flow revision in progress

Updated 2026-10-01 UTC. Work stays on `main`, with local commits only. The user will push. Unrelated `iot-entropy` work is preserved. No paid resource has been created.

The new namespace is `results/graph_flow_v1/`. The original 306 tracked study files are hashed in `legacy.json`. `paper/legacy/witness_20260930.tar.xz` preserves the previous paper exactly. Original results and evidence bundles remain unchanged. The current main manuscript still describes that preserved study.

The eight reference check groups and 17 focused CPU tests pass. The graph flow trains and generates on the existing RTX PRO 4500 GPU. Its 22,048-parameter Gaussian pilot trained in 9.694 seconds, reduced validation NLL from 10.6692 to 5.7215, and reproduced saved GPU score arithmetic with zero discrepancy. These are pilot diagnostics, not benchmark superiority evidence. See `pilot.json` and `evidence/pilot.npz`.

All 20 flow capacity/context development fits completed. Three-member selected ensembles, own-history ablations, learning curves and official GANF fits have completed. Development-selected PCA, single and mixture PPCA, all-channel PPCA and a portable tree classifier are implemented. PPCA observed-context conditionals agree with the full Gaussian reference. The shared final scorer, separate calibration roles, block bootstrap, repair-risk calculation, legacy rerun, and robustness stages are implemented but not yet final-executed.

Two pre-final implementation corrections are documented. A completely unavailable Intel window now retains the full candidate population with floor scores. Irregular SKAB timestamps require elapsed-time drift ramps. Earlier index-ramp development artifacts are preserved under `development/chronology_correction/`, and affected development selections are being rerun. No new final-test score has yet been examined. The exact protocol lock will be written only after these checks.

Model checkpoints remain outside Git. Compact selections, numerical evidence and code are committed. Primary hypotheses remain untested. Neural flexibility, likelihood-ratio benefit and safe repair coverage are not assumed.

Current validation and resume commands

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python3 -m pytest tests/test_graph_flow.py -q
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status graph_flow_neural_resume
bash scripts/runpod.sh sync
bash scripts/runpod.sh push-flow-baselines
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py launch graph_flow_chronology bash scripts/graph_flow_chronology_resume.sh
bash scripts/runpod.sh pull-flow
```

Once the chronology correction and common-scorer smoke pass, the finite final job is

```bash
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py launch graph_flow_final bash scripts/graph_flow_final.sh
```

That job repeats development sampling diagnostics, freezes model/data/code choices, scores and calibrates disjoint calibration roles, runs the paired final cases, recomputes equations and executes the predeclared stress conditions. Do not start it concurrently with development. Runtime paths and exact hashes are in each run record. Graph persistence, the new operator evidence view, final figures and the revised compiled paper remain to be completed from those results.

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
