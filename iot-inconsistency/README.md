# Separate witness evidence for IoT repair hypotheses

This directory implements the DSpaCES 2026 research specification in `DSpaCES_2026_research_plan_and_Codex_prompt.txt`. The detector is executable. Its equations are evaluated on actual GPU-generated predictions, with saved NumPy/CUDA arithmetic checks and production score audits.

Work stays on `main`. The user will push when the project is complete. No paper submission or new paid resource is authorized. Read [PROGRESS.md](PROGRESS.md) for the current state and [DECISIONS.md](DECISIONS.md) for protocol corrections. A manuscript carrying the layout-draft notice is not the final paper.

The primary study uses one synthetic sensor-network family, Intel Berkeley measurements and SKAB. Native SKAB process events never become sensor-fault labels. The implementation includes PCA with current and lagged inputs, GDN, the conditional backbone's residual detector, deterministic repairs, and a documented independent DiffAD adaptation.

## Artifacts

- [paper/main.tex](paper/main.tex) and [paper/main.pdf](paper/main.pdf) contain the IEEE manuscript. Generated text is sourced through [results/paper_claims.json](results/paper_claims.json).
- [results/analysis.json](results/analysis.json) contains the primary results, paired source-block intervals, probability evaluations, operating points and fault-family subsets.
- `results/study/<configuration>/<split>/` contains case manifests, original inputs, all primary predictive draws, unchanged witness identities and separate score components.
- `results/ablations/`, `results/robustness/`, `results/native/` and `results/sensitivity/` retain secondary experiments and their narrower label scopes.
- [equation_audit.md](equation_audit.md), [equation_to_code.json](equation_to_code.json) and [CLAIMS_AUDIT.md](CLAIMS_AUDIT.md) connect the method to code and evidence.
- `results/model_weights/` contains exact inference state arrays and hashes. GPU training checkpoints also include optimizer state and are intentionally excluded from ordinary result pulls.
- [literature/NOVELTY_MATRIX.md](literature/NOVELTY_MATRIX.md) records full-method comparisons and adaptation limits. `literature/sources.json` and data acquisition manifests record primary sources, versions and licenses.

## Local verification and rendering

The arithmetic reference requires NumPy. Full analysis requires the Python packages in `requirements-runpod.txt`. The recorded GPU environment is `results/environment.lock.txt`. Local artifact analysis also works with the older installed Python 3.8 environment; exact hardware/software reproduction should use the recorded environment.

```bash
python3 reference/reference_score.py
python3 scripts/audit_equations.py --device cpu
python3 -m pytest -q
python3 scripts/analyze.py
python3 scripts/analyze_confidence.py
python3 scripts/summarize_design.py
python3 scripts/analyze_equations.py
python3 scripts/export_graph.py
python3 scripts/figures.py
python3 scripts/make_paper.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
```

Final paper generation requires completed experiments and audits. `make_paper.py --draft` permits explicit pending-result markers for layout work only. It never fabricates missing values. The vendored IEEE class and bibliography style retain their original license notices.

## Data and model reproduction

Raw and processed dataset caches are ignored by Git. Acquire the pinned public sources and prepare the three families with the commands below. The acquisition and processed-file manifests provide checksums. SKAB experiment assignment, Intel chronological gaps, training-only scales, source groups, availability masks and simulator latent truth are retained.

```bash
python3 scripts/acquire.py
python3 scripts/prepare_data.py
```

Main inference automatically loads `results/model_weights/<configuration>/*.npz` when optimizer checkpoints are absent. PCA states are in `results/models/<configuration>/`. Rebuilding metrics and figures from saved predictions does not require GPU inference or retraining. The original GPU predictions are the definitive empirical artifacts. Ordinary float32 GPU reductions can change small seeded scores; [results/audits/inference_repeatability.json](results/audits/inference_repeatability.json) measures that effect. Deterministic CUDA mode verifies exact portable/checkpoint agreement and known-copy invariance separately.

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

## Neo4j and the operator view

Neo4j Community is local, bound to loopback and requires Docker. No cloud database is created.

```bash
bash scripts/neo4j.sh start
python3 scripts/persist_graph.py
python3 operator/server.py
```

Open `http://127.0.0.1:8099`. Select a saved window, click a channel or a scored edge, inspect unchanged witness predictions and the score terms, and record a confirm, reject or defer decision. Gray arrows are predictive associations. Double red circles, blue witness outlines and dashed orange disputed edges retain distinct meanings. Empirical prediction intervals, null-tail values and fitted fault probabilities are labeled separately. The graph stores file references and immutable association versions. Review decisions never modify measurements or actuate equipment.

`results/interface/browser_verification.json` and PNG previews document browser testing. Automated decisions explicitly say that they are interface tests, not human diagnoses. Stop the local database with `bash scripts/neo4j.sh stop` when desired.
