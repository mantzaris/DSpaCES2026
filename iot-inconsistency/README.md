# Separate witness evidence for IoT repair hypotheses

This directory implements the DSpaCES 2026 research specification in `DSpaCES_2026_research_plan_and_Codex_prompt.txt`. The detector is executable. Its equations are evaluated on actual GPU-generated predictions, with saved NumPy/CUDA arithmetic checks and production score audits.

The research and 10-page IEEE paper are complete. Work stays on `main`, and the user will push the local commits. No paper was submitted and no paid resource was created. Read [PROGRESS.md](PROGRESS.md) for completion details and [DECISIONS.md](DECISIONS.md) for protocol corrections.

The measured benefit is limited to high-precision review at 10% screened-candidate coverage in one nonlinear synthetic configuration. It reverses at broader coverage. PCA is stronger for overall observation detection, association differences are inconclusive, and mixed fault types can give competing explanations. These findings and unsuccessful robustness conditions remain in the paper and artifacts.

The primary study uses one synthetic sensor-network family, Intel Berkeley measurements and SKAB. Native SKAB process events never become sensor-fault labels. The implementation includes PCA with current and lagged inputs, GDN, the conditional backbone's residual detector, deterministic repairs, and a documented independent DiffAD adaptation.

## Artifacts

- [paper/main.tex](paper/main.tex) and [paper/main.pdf](paper/main.pdf) contain the IEEE manuscript. Generated text is sourced through [results/paper_claims.json](results/paper_claims.json).
- [results/analysis.json](results/analysis.json) contains the primary results, paired source-block intervals, probability evaluations, operating points and fault-family subsets.
- `results/evidence/` contains six compressed bundles and a checksum manifest. They preserve the exact finalized JSON records for primary and secondary experiments, including negative findings. Run the restore command below to expand them into their original locations.
- Compact primary arrays retain inputs, masks, truth, replacements, witness losses and score components. Repeated predictive draws are omitted from these explicitly named `results/compact/` files. Twenty-one complete draw files cover all ten operator examples and independent CRPS checks. Original array paths and hashes remain distinct from compact paths and hashes.
- `results/ablations/`, `results/robustness/`, `results/native/` and `results/sensitivity/` retain their result summaries directly, with detailed records in the bundles. Native process labels remain separate from injected faults.
- [equation_audit.md](equation_audit.md), [equation_to_code.json](equation_to_code.json) and [CLAIMS_AUDIT.md](CLAIMS_AUDIT.md) connect the method to code and evidence.
- `results/model_weights/manifest.json` records exact neural state hashes. The 78 neural state files, full predictive draws and superseded intermediate runs remain locally and on the existing pod, outside Git. The small PCA states and all source code remain in Git. Optimizer checkpoints are excluded from ordinary result pulls.
- [literature/NOVELTY_MATRIX.md](literature/NOVELTY_MATRIX.md) records full-method comparisons and adaptation limits. `literature/sources.json` and data acquisition manifests record primary sources, versions and licenses.

## Local verification and rendering

The arithmetic reference requires NumPy. Full analysis requires the Python packages in `requirements-runpod.txt`. The recorded GPU environment is `results/environment.lock.txt`. Local artifact analysis also works with the older installed Python 3.8 environment; exact hardware/software reproduction should use the recorded environment.

```bash
python3 scripts/package_results.py restore
python3 scripts/audit_publication.py
python3 reference/reference_score.py
python3 scripts/audit_equations.py --device cpu
python3 -m pytest -q
python3 scripts/analyze.py
python3 scripts/analyze_confidence.py
python3 scripts/analyze_cross_type.py
python3 scripts/analyze_equations.py
python3 scripts/evaluate_pca_total.py
python3 scripts/figures.py
python3 scripts/make_paper.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
```

The restore command checks every file and refuses to overwrite changed local evidence. Expansion needs about 2.4 GiB in a fresh checkout. `package_results.py verify` checks the bundles without expanding them. The publication audit reads primary arrays directly from the bundles and checks all 1,092 test cases, 40 PCA settings, 21 complete CRPS examples, the claim sources and the saved manuscript and figure hashes. Run it before regenerating the published files. `results/audits/production_equations.json` retains the original all-case E4 audit. Repeating that broader draw audit or `scripts/audit_final.py` requires the full local or RunPod archive. Packaging does not change any saved scientific result.

Final paper generation requires completed experiments and audits. `make_paper.py --draft` remains available only for clearly marked intermediate layouts. The vendored IEEE class and bibliography style retain their original license notices. Analysis regenerated under different NumPy or scikit-learn versions can differ in final floating-point digits. The saved outputs and environment lock identify the published values.

## Data and model reproduction

Raw and processed dataset caches are ignored by Git. Acquire the pinned public sources and prepare the three families with the commands below. The acquisition and processed-file manifests provide checksums. SKAB experiment assignment, Intel chronological gaps, training-only scales, source groups, availability masks and simulator latent truth are retained.

```bash
python3 scripts/acquire.py
python3 scripts/prepare_data.py
python3 scripts/summarize_design.py
python3 scripts/export_graph.py
```

Main inference automatically loads local `results/model_weights/<configuration>/*.npz` when optimizer checkpoints are absent. These neural weights are excluded from the Git distribution. PCA states are in `results/models/<configuration>/`. Rebuilding metrics and figures from restored records and compact arrays does not require GPU inference or retraining. The original GPU predictions remain the definitive full empirical archive. Ordinary float32 GPU reductions can change small seeded scores; [results/audits/inference_repeatability.json](results/audits/inference_repeatability.json) measures that effect. Deterministic CUDA mode verifies exact portable/checkpoint agreement and known-copy invariance separately.

## Existing RunPod execution

The helper uses only the already authorized pod. It does not create, resize, purchase or delete resources. Remote files live under `/workspace/iot-inconsistency`.

```bash
bash scripts/runpod.sh sync
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status main_experiments
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status secondary_experiments
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status finish_artifacts
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status verify_final_gpu
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status final_stress
bash scripts/runpod.sh pull
```

`sync` excludes all results, preventing local snapshots from overwriting running experiments. `pull` excludes optimizer checkpoints. The job wrapper writes a finite command, PID, status and log. Completed model and case files are resumed. Do not launch a second job against the same output directory or run other GPU work during latency measurement. The main stage freezes development choices and calibrates before evaluating test cases. The secondary stage runs ablations and native events. The artifact stage benchmarks inference and exports model states. Verification and final stress analysis follow in that order.

For a clean rerun, retain the existing results as immutable evidence and select a new output root through an isolated copy of this project directory. Do not mix partially regenerated runs with the published manifest. The experiment scripts and configuration, rather than test outcomes, specify seeds, masks, budgets and candidate screening.

After dataset preparation in that isolated copy on the existing GPU, run these finite stages sequentially. They expect the recorded `.venv` environment. The first stage discovers associations and trains diffusion, GDN, deterministic and graph-free models. The main stage tunes and trains DiffAD, runs development sensitivity, freezes choices and evaluates calibration and test partitions.

```bash
.venv/bin/python scripts/job.py run training_v2 bash scripts/train_main.sh
.venv/bin/python scripts/job.py run main_experiments bash scripts/continue_main.sh
.venv/bin/python scripts/job.py run secondary_experiments bash scripts/secondary.sh
.venv/bin/python scripts/job.py run finish_artifacts bash scripts/finish_artifacts.sh
.venv/bin/python scripts/job.py run verify_final_gpu bash scripts/verify_final_gpu.sh
.venv/bin/python scripts/job.py run final_stress bash scripts/final_stress.sh
.venv/bin/python scripts/audit_inference_repeatability.py
.venv/bin/python scripts/evaluate_pca_total.py
.venv/bin/python scripts/analyze_cross_type.py
```

The first run executed development sensitivity separately before freezing. `continue_main.sh` now includes that idempotent command so a clean rerun cannot omit it. The portable/checkpoint audit requires the original optimizer checkpoints on the GPU. CPU analysis and rendering use the restored result records and compact arrays. To rebuild the distribution from the full archive, run `python3 scripts/package_results.py pack`, then `python3 scripts/audit_publication.py`.

## Neo4j and the operator view

Neo4j Community is local, bound to loopback and requires Docker. No cloud database is created.

```bash
bash scripts/neo4j.sh start
python3 scripts/persist_graph.py
python3 operator/server.py
```

Open `http://127.0.0.1:8099`. Select a saved window, click a channel or a scored edge, inspect unchanged witness predictions and the score terms, and record a confirm, reject or defer decision. Gray arrows are predictive associations. Double red circles, blue witness outlines and dashed orange disputed edges retain distinct meanings. Empirical prediction intervals, null-tail values and fitted fault probabilities are labeled separately. The graph stores file references and immutable association versions. Review decisions never modify measurements or actuate equipment.

`results/interface/browser_verification.json` and PNG previews document browser testing. Automated decisions explicitly say that they are interface tests, not human diagnoses. Stop the local database with `bash scripts/neo4j.sh stop` when desired.
