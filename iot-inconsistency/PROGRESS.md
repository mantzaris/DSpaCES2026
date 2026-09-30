# Completed research artifact

Updated 2026-09-30. Work is on `main`. The user will perform the final push. No branch, paper submission or new paid resource was created.

The full specification was read and implemented. Part C was extracted and executed before the PyTorch implementation. Its 13 checks passed. Identical saved inputs passed CPU/CUDA parity. All 16 integration tests passed locally and on the GPU host. Independent production auditing reconstructed 8,736 candidate scores from 1,092 primary test cases, with maximum absolute arithmetic discrepancy 7.11e-15.

All finite stages are complete, including revised training, primary evaluation, inference ablations, native SKAB events, model export, GPU verification and corrected stress analysis. The existing RTX PRO 4500 Blackwell was used. The remote directory remains `/workspace/iot-inconsistency`. All 78 inference states are preserved locally in `results/model_weights`, with exact-array and deterministic checkpoint-replay verification. Optimizer checkpoints remain on the pod. Ordinary CUDA reduction repeatability is measured separately and is not claimed to be bitwise exact.

The paper is complete at `paper/main.pdf`, in standard IEEE conference format with 10 pages including references. It reports a limited S32N precision benefit at 10% screened-candidate coverage, its reversal at broader coverage, stronger PCA detection, association ambiguity, failed robustness conditions and measured costs. Native process labels remain separate from injected sensor and association faults. The conventional total-error PCA supplement is explicitly distinguished from the frozen channel-maximum primary comparison.

Neo4j stores versioned evidence for ten saved review cases. The node-link interface passed browser verification. Confirm, reject and defer records are labeled automated interface tests, not human diagnoses. Repeated evidence import changes no entity counts. The four required scientific figures and two supplemental plots come from saved outputs with source and output hashes.

`results/audits/final.json` records the completed artifact checks and current manuscript hash. `results/paper_claims.json` maps generated values to saved results. `CLAIMS_AUDIT.md`, `equation_audit.md` and `DECISIONS.md` state the claim limits and corrections.

Rebuild the paper from committed evidence, without training or dataset acquisition

```bash
python3 scripts/figures.py
python3 scripts/make_paper.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
python3 scripts/audit_final.py
```

Restore the local review application

```bash
bash scripts/neo4j.sh start
python3 scripts/persist_graph.py
python3 operator/server.py
```

Open `http://127.0.0.1:8099`. The database and viewer bind to loopback. Inspect the existing pod with `bash scripts/runpod.sh status`. Experiment stages are already complete and need not be relaunched. Reproduction and stage commands are in `README.md`. Preserve the published outputs before any new experiment. The user will push the final local commits when ready.
