# When Agreement Reuses Evidence

**Stage 2 decision C: stop/defer this DSpaCES project.** The original sketch
approach is stopped. The evidence does not yet justify its narrow paper fallback
or an event-time pivot. The main study remains disabled; no Stage 3 is proposed.

Read the [Stage 2 decision](reports/STAGE2_DECISION.md),
[evidence audit and dated corrections](reports/STAGE1_EVIDENCE_AUDIT.md),
[current literature comparison](docs/STAGE2_NOVELTY_AUDIT.md), and
[archival disposition / safe pod stop procedure](reports/STAGE3_PROPOSAL.md).
Stage 1's exact-lineage score improvement over common-noise correction is only
0.48% on this short pilot, with uncertainty too weak for an equivalence claim.
Compressed exact metadata is smaller under a richer public-design contract;
cached-sketch wire costs are estimates. These are local findings.

Start with the [Stage 1 report](reports/STAGE1_REPORT.md),
[feasibility audit](reports/FEASIBILITY_REPORT.md),
[proof audit](docs/PROOF_AUDIT.md), and [novelty audit](docs/NOVELTY_AUDIT.md).
The [complete supplied plan](docs/RESEARCH_PLAN.md) remains prospective; explicit
[execution amendments](docs/AMENDMENTS.md) distinguish it from completed evidence.

The pilot uses 16 buildings at 16 BDG2 sites, four providers, 42 training days
per provider, three fixed sharing levels, and k=512/2048. October 2016 supplies
disjoint covariance, calibration and scoring windows. The 2017 test year is
sealed. Provider institutions and sharing rules are simulated. Real intervals
are empirical plug-ins, not certified Gaussian or distribution-free intervals.

Stage 2 preserves the original Stage 1 reports and outputs. Its only numerical
analysis correction is round-trip CSV parsing for interval-boundary coverage:
30 seasonal-naive targets in one building affected secondary block aggregates;
the original headline table and exact/common/sketch comparisons were correct.
Corrected blocks are in `results/stage2/`, alongside independently recomputed
summaries and a CPU-only diagnostic ledger capped at 30 cumulative minutes.
The pod snapshot (90 files, about 856 MB) is hash-verified under ignored
`data/archives/stage1_pod_20260923/` on the existing local disk. The pod remains
allocated; no research process is running. Neither its termination nor further
compute is authorized by these reproduction examples.

## Reproduce Stage 2 saved-evidence checks

```bash
python3 scripts/stage2_job.py --label evidence_recheck --timeout 120 -- python3 scripts/audit_stage1_evidence.py
python3 scripts/stage2_job.py --label tests_recheck --timeout 120 -- python3 -m pytest -q
python3 scripts/stage2_job.py --label archive_recheck --timeout 120 -- python3 scripts/verify_stage2_archive.py
```

The evidence recomputation uses the existing ignored October evaluator CSV;
the archive verifier hashes opaque files without inspecting sealed outcomes.
The wrapper preserves its cumulative cap across retries. It excludes GPUs and
records every child job's wall time separately from reading/writing. Original
Stage 1 commands below document history and do not authorize new experiments.

## Reproduce saved-results analysis without GPU or source data

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/build_figures.py
python scripts/verify_artifacts.py
python scripts/run_main_study.py --preflight
```

The two [pilot figures](reports/figures/) use retained aggregate numerical
results. Raw meter files and the local per-target evaluator output are ignored
by git. Saved block aggregates and sensitivity intervals remain available.
The original cost figure is retained as evidence; its cached-sketch points are
estimates despite its old blanket title. The generator's title has been corrected
for future reproductions. See the Stage 2 audit before interpreting these figures.

## Reproduce the bounded pilot

The verified execution used Python 3.12.3 and preinstalled PyTorch
2.8.0+cu128 on an RTX PRO 4500 Blackwell. `environment.lock.txt` is the full
observed environment snapshot, including inherited system/Jupyter packages;
`requirements.lock.txt` records the analysis dependency pins. It is not a
portable OS or CUDA image. On a compatible provisioned machine:

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.lock.txt
export PYTHONPATH=src OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
.venv/bin/python scripts/bootstrap_data.py --start 2026-09-22T23:25:34+00:00
.venv/bin/python scripts/run_data_audit.py
.venv/bin/python scripts/run_pilot.py --config configs/pilot.yaml
.venv/bin/python scripts/run_benchmarks.py
.venv/bin/python scripts/benchmark_cold.py
.venv/bin/python scripts/audit_exact_exchange.py
.venv/bin/python scripts/audit_residuals.py
.venv/bin/python scripts/run_controlled.py
.venv/bin/python scripts/analyze_pilot.py
.venv/bin/python scripts/build_figures.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_artifacts.py
.venv/bin/python scripts/close_stage.py
.venv/bin/python scripts/write_reports.py
```

These are the recorded commands for the original allocation. Its immutable
deadline is September 23, 2026, 01:25:34 UTC; rerunning after that deadline
correctly refuses. A separately authorized reproduction needs a new output
directory and an explicit new allocation start/configuration, preserving the
original ledger and scientific parameters. Do not reset the existing budget.
The public archive is downloaded once and checked against the published MD5
and recorded SHA-256. Only January–October 2016 values are parsed/extracted.

## Later full-study execution is gated

```bash
python scripts/run_main_study.py --authorize-main --max-gpu-hours 24
```

This is a **guarded launcher, not an approved or complete main-study job list**.
It currently refuses: authorization is false and the scientific gate failed.
A later approved revision must provide a frozen executable job list and a
reviewed continue decision. The launcher then charges Stage 1 time against the
24-hour total, persists its deadline across restarts, and terminates worker
process groups at the cap. There is no background full-study task.

The measured uncached 128-building protocol projects above the 24-hour cap;
claiming that configuration is ready would be misleading. A smaller 32-building
cost scenario fits the illustrative budget but falls below the original
64-building evidence gate. Neither scenario is authorized.

## Information boundary and attribution

`message_contracts.py` and `conservative_fusion.py` accept forecasts and metadata,
without raw outcomes or influence vectors. Provider fits, hidden exact reference
calculations and outcome scoring are separate modules. `exact_exchange.py`
implements an explicitly richer contract using public calendar features and
lossless support identities. It reconstructs influence without training labels.

Data: Miller et al., Building Data Genome 2,
[Zenodo v1.0](https://zenodo.org/records/3887306),
[originating project](https://github.com/buds-lab/building-data-genome-project-2).
Preserved license texts are in `manifests/`: the pinned archive's root license
differs from the current repository's text. No raw dataset is redistributed.
CI/ESCI, robust fusion, OLS influence, JL projections and covariance sketching
are established work; see the source-by-source novelty audit.

All changes follow the user-authorized `main` workflow; no new branch is used.
