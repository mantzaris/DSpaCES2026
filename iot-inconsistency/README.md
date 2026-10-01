# Graph conditional generation for sensor fault testing

This project implements and executes a corruption-aware neural normalizing flow for the DSpaCES 2026 study. Actual GPU-generated sensor intervals enter a normalized fault likelihood and a weighted repair distribution. The frozen comparison covers the synthetic network family, Intel Berkeley and SKAB. Native process events remain separate from injected sensor and association faults.

Work stays on `main`. Commit locally and let the user push. Do not submit the paper, publish externally or create paid resources. The existing RunPod is the only authorized GPU infrastructure. Preserve unrelated repository work.

Family-macro AP is 0.438 for the ratio, 0.307 for PCA and 0.423 for likelihood from the identical flow. Both paired primary intervals are positive, supporting directional H1 for this protocol. The 0.015 gain over same-flow likelihood misses the chosen 0.02 practical margin. H2, neural benefit over matched Gaussian models, remains inconclusive. H3, a general repair coverage advantage at controlled risk, is not established. Supervised trees are stronger in every configuration. Intel confidence transfers poorly and SKAB repair risk exceeds the calibration target in point estimate.

[graph_flow_claims_audit.md](graph_flow_claims_audit.md) gives exact contrasts and limits. Real recording partitions had already informed the earlier study. Fresh injections on those recordings are not untouched field validation.

## Paper and evidence

- [paper/main.pdf](paper/main.pdf) and [paper/main.tex](paper/main.tex) are the new IEEE manuscript. Numerical prose and tables are generated through [paper_claims.json](results/graph_flow_v1/paper_claims.json). [figure_provenance.json](results/graph_flow_v1/figure_provenance.json) hashes figure sources and outputs.
- [docs/graph_flow_protocol.md](docs/graph_flow_protocol.md), [configs/graph_flow_v1.json](configs/graph_flow_v1.json) and [protocol_lock.json](results/graph_flow_v1/protocol_lock.json) record the finite experiment and pre-test choices. The lock was created at 2026-10-01 02:03:02 UTC.
- [analysis.json](results/graph_flow_v1/analysis.json) retains every primary comparison, paired block interval, calibration and repair result. [robustness.json](results/graph_flow_v1/robustness.json) and [runtime.json](results/graph_flow_v1/runtime.json) record adverse conditions and isolated costs.
- [equation_audit_graph_flow.md](equation_audit_graph_flow.md) and [equation_to_code_graph_flow.json](equation_to_code_graph_flow.json) connect E1–E12 to code, tests and production evidence. The production audit reconstructs 107,620 scores and replays 30 full generation bundles on the GPU.
- [publication/manifest.json](results/graph_flow_v1/publication/manifest.json) describes six compressed bundles totaling 86.93 MiB. They retain exact JSON, compact candidate arrays and complete representative generation arrays. Explicit omission lists distinguish compact files from original full files. Every retained array is exact.
- [model_manifest.json](results/graph_flow_v1/model_manifest.json) records hashes and local/pod locations for 261 model and metadata files, including 70 neural checkpoints. All 119 model paths referenced by the lock were verified locally. Weights, raw caches, logs and temporary files are outside Git.
- [literature/graph_flow_novelty_matrix.md](literature/graph_flow_novelty_matrix.md) records primary-source comparisons. Flows, likelihood ratios and Bayesian repairs are established constructions, not newly invented equations.

Published evidence supports metric and equation replay without weights. A fresh clone alone does **not** support model inference replay. An independent user must retrain or obtain the exact weights. Raw data can be reacquired from pinned public sources. Hashes identify artifacts but do not guarantee their continued availability on a temporary pod.

## Compile the paper

All manuscript text, tables and references are in `paper/main.tex`. From this
project directory, compile the committed source directly

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
```

The output is `paper/main.pdf`, with ten pages including references. Keep the
figure files and `paper/IEEEtran.cls` in place. Separate generated LaTeX fragments
and bibliography databases are not required for compilation. See
[paper/BUILD.md](paper/BUILD.md) for regeneration details.

## Rebuild without training

Run from this directory. Summary JSON, graph cases and precision-recall arrays suffice to regenerate the paper. Verification and publication auditing stream compressed evidence without expanding it.

```bash
python3 scripts/package_graph_flow.py verify
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 scripts/audit_graph_flow_publication.py
python3 reference/reference_graph_flow.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 -m pytest -q
python3 scripts/figures_graph_flow.py
python3 scripts/make_graph_flow_paper.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
```

The reference has eight check groups. Forty tests include eighteen new flow tests. The actual GPU environment is [environment_gpu.json](results/graph_flow_v1/environment_gpu.json), with pinned dependencies in `requirements-runpod.txt`. Older local Python 3.8 works for evidence replay and plotting. Use the recorded environment for exact hardware/software replication.

`python3 scripts/package_graph_flow.py restore` expands exact JSON and arrays under explicitly separate `results/graph_flow_v1/compact/` paths. It refuses to overwrite edited files. Compact NPZ files have their own hashes, distinct from the full originals. Full cases and original draws remain locally and on the pod, outside Git. `scripts/diagnose_graph_flow.py` can read full or compact predictions.

## Where neural generation occurs

`src/iot_repair/graph_flow_model.py` supplies `GraphFlow.log_prob` and `GraphFlow.sample`. A temporal/graph encoder conditions invertible neural affine couplings. `sample` draws normal latent vectors and executes the inverse on the GPU. `flow_inference.py` passes these generated intervals to `GaussianCorruption.log_prob` in `flow_math.py`, integrates densities in log space, forms the ensemble ratio and weights the generations for repairs.

The conditioner removes the tested source interval before features. Complete targets are required. Unavailable targets receive flags and a ranking floor, retaining true faults as misses. Supporting sensors are conditioning information, never independent witnesses. Full evidence saves inputs, masks, latent draws, generations and component log densities.

Comparisons include current/lagged PCA, identical-flow NLL, graph PPCA, mixture PPCA, all-channel PPCA, pinned author GANF classes, fault-aware trees and rerun legacy diffusion/GDN methods. GANF's adapters and finite graph-optimization limits are documented. MTGFlow was inspected but was outside the optional execution budget.

## Existing GPU workflow

The finite experiment is complete. Inspect its status without relaunching training.

```bash
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status graph_flow_finish_resume
```

[execution_jobs.json](results/graph_flow_v1/execution_jobs.json) preserves two failed audit/reporting attempts and the successful resume. Predictions and the protocol lock did not change during those corrections. [DECISIONS.md](DECISIONS.md) explains them.

For reproduction, use an isolated directory copy and distinct output namespace, preserving published results. Numerical modules reject changed source/configuration hashes. The legacy dataset preprocessing, legacy model states and pinned GANF source are prerequisites. After they are available, the finite stages are

```bash
.venv/bin/python scripts/graph_flow_pilot.py
bash scripts/graph_flow_develop.sh
.venv/bin/python scripts/graph_flow.py baselines
bash scripts/graph_flow_neural.sh
bash scripts/graph_flow_final.sh
bash scripts/graph_flow_finish.sh
```

`runpod.sh sync` excludes results. `pull-flow` excludes models, caches and raw bundles. Do not broadly pull over finalized local presentation or publication artifacts. Use targeted transfers. Do not run concurrent jobs against one output path or during timing. Helpers do not create, resize or purchase resources.

## Neo4j and operator view

The graph has 23 rule-selected cases covering success, failure, numerical inadequacy, ambiguity and association review. Repeated import preserves entity counts. Observations remain immutable and review decisions are separate records.

```bash
bash scripts/neo4j.sh start
python3 scripts/export_graph_flow.py --persist-only
python3 operator/server.py --port 8100
```

Open `http://127.0.0.1:8100/flow`. The classic network uses named nodes, directed lag/correlation annotations, red disputed intervals, blue supporting sources and amber dashed edges only for assessed association disputes. Details show actual generations, weighted intervals, score meaning, ESS, benchmark probability and accept/reject/defer actions. Actions do not replace measurements.

[graph/interface/browser_verification.json](results/graph_flow_v1/graph/interface/browser_verification.json) and screenshots document browser checks. Automated review records are interface tests, not a human operator study. Neo4j uses the existing local container and binds to loopback.

## Preserved witness study

Original results and legacy evidence bundles are unchanged. [legacy.json](results/graph_flow_v1/legacy.json) hashes the 306-file starting study. `paper/legacy/witness_20260930.tar.xz` preserves its exact paper, PDF, figures and bibliography. The original equation map and claims audit remain separate.

[docs/witness_legacy_readme.md](docs/witness_legacy_readme.md) preserves older reproduction instructions. Run legacy manuscript generators only in an isolated copy of the archived study because they write the main paper paths. New and old endpoints, manifests and checkpoints remain separate.
