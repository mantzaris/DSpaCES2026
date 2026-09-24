# DSpaCES research pilots

**Current deliverable: editorially revised regional twin case study for author review.**
Read [From Detail to Decisions in Regional Energy Twins](manuscript/regional_twin_study.pdf),
a ten-page IEEE conference draft with four vector figures, an evidence-generated
results table and the supplied author block. The [editorial report](reports/REGIONAL_TWIN_EDITORIAL_REVISION.md)
explains the stronger attribution and design argument; the [synthesis report](reports/REGIONAL_TWIN_SYNTHESIS_REPORT.md),
[claim map](reports/REGIONAL_TWIN_CLAIM_EVIDENCE.md), [clean build](manuscript/README.md)
and [author-review decisions](manuscript/AUTHOR_REVIEW.md) accompany it.

Saved-output analysis shows that all 4,608 original demand-replay updates satisfy
a sufficient unchanged-acquisition-gate condition. M3b's added affected-meter
requests occur after the detection window; its acquired fine alarm score stays
below threshold in all 12 fresh demand cases. No adaptive advantage is claimed.
No new GPU experiment ran; 11.2337 regional allocation minutes remain. Seals and
the disabled main study persist. The pod remains allocated and idle. This is not
a submitted paper, a novelty certificate or authorization for another stage.

**Completed active stage: shock-responsive acquisition diagnosis.** GPU reconstruction
verified all 112 original episodes. In 96 demand shocks, 93 group scores changed,
but no original acquisition trigger or schedule changed. This was a policy
threshold limitation, not a lost overlay or blocked budget.

One frozen rank-responsive variant changed schedules in 3/12 fresh disturbances
but did not improve localization: variant, original and random each localized
2/12. Local one-hour MAE was 0.2660, 0.2621 and 0.2667 kWh respectively; streamed
fine achieved 0.2053. Same-evidence fixed/adaptive outputs agreed exactly. Nine
focused tests pass; no unexplained numerical failure. These four-background
results do not establish an adaptive-refinement advantage or publication readiness.

Read the [Stage 4 report](reports/REGIONAL_TWIN_STAGE4_ACQUISITION_REPORT.md),
[diagnostic field definitions](docs/REGIONAL_ACQUISITION_FIELDS.md),
[pre-edit correction hypothesis](docs/REGIONAL_ACQUISITION_CORRECTION.md),
[three PDF/SVG figures](reports/figures/acquisition/), and
[closed resource handoff](results/acquisition/resource_handoff.json).
The stage charged 25.3263 allocation minutes, leaving 11.2337 original regional
minutes. Both outcome seals remain intact; the original main study is disabled.
The existing pod/storage remain allocated and idle. No next stage is running.

## Preserved Stage 3 shock study

**Completed prior stage: When Regional Totals Hide Local Change.** The bounded
GPU shock study ran 112 episodes on 4,194 real households, using eight exploratory
development backgrounds and reversible synthetic disturbances. All 16 focused
shock tests pass; previous results remain preserved.

The result does **not** establish a shock-targeted refinement advantage. None of
the 96 demand shocks changed the event policy's acquired-ID trace relative to its
unmodified background. Exact-cancellation events were not correctly localized.
Local one-hour MAE was 0.1696 kWh for event refinement, 0.1710 for random selection
and 0.1386 for streamed fine inference. Same-information fixed/adaptive inference
agreed exactly; negative-control alarms exceeded the calibration target.

Read the [measured shock report](reports/REGIONAL_TWIN_STAGE3_SHOCK_REPORT.md),
[frozen protocol and primary-source comparison](docs/REGIONAL_SHOCK_STUDY_PROTOCOL.md),
[four PDF/SVG figures](reports/figures/shock/), and
[decision summaries](results/shock/analysis/decision_summary.json).
The report separates additional data, acquisition policy, representation, physical
measurements and synthetic interventions. No full paper or next stage is started.

Executable preparation, calibration, GPU replay, trace reconstruction and analysis
commands are in the report. Saved-output analysis uses `scripts/analyze_shock.py`
and `scripts/shock_decision_summary.py`. The
[shock ledger](results/shock/resource_ledger.json) retains the original regional
allowance; a closed ledger refuses further execution. Completed artifacts are
copied and hash-verified on existing local storage in the
[durable inventory](manifests/regional_shock_durable.json).
London April-December 2013 and all earlier BDG2 seals remain intact. The original
main study is disabled. The existing pod remains allocated; no experiment is running.

## Previous regional refinement stage

**Refinement Without Rebuilding was the preceding bounded Greater
London regional twin refinement pilot.** The GPU implementation uses 4,194 real
households, with nested 1,024/2,048-household comparisons. It preserves registered
posterior queries through detail eviction and evidence replacement. All 49 tests
pass. The measured cache/reread tradeoff is real; a new inference contribution,
capacity advantage over streamed fine inference, and adaptive-policy benefit
are not established. One-hour regional intervals under-cover.

Read the [measured refinement report](reports/REGIONAL_TWIN_STAGE2_REFINEMENT_REPORT.md),
[theory and counterexamples](docs/REGIONAL_REFINEMENT_THEORY.md),
[closest-source audit](docs/REGIONAL_REFINEMENT_NOVELTY_AUDIT.md), and
[three measured figures](reports/figures/refinement/). The next proposed question
is incremental boundary information when the time window moves; it is not an
authorized next stage. The previous shared-matrix solver's negative result is
preserved in the [regional Stage 1 report](reports/REGIONAL_TWIN_STAGE1_REPORT.md).

Saved refinement summaries/figures regenerate with
`python scripts/analyze_refinement.py`; executable preparation, replay and
validation commands are in the report. The closed
[resource ledger](results/refinement/resource_ledger.json) adds this stage to
the original allowance and refuses further execution. Raw data/model caches are
ignored by git and hash-listed in the
[durable inventory](manifests/regional_refinement_durable.json).

The compatibility-contract document remains an unchanged candidate at
[DSpaCES_2026_Research_Plan.md](DSpaCES_2026_Research_Plan.md).

Read [active scope and caps](docs/ACTIVE_RESEARCH_SCOPE.md),
[matrix derivations and numerical limits](docs/REGIONAL_MATRIX_PROOFS.md),
[primary-source comparison](docs/REGIONAL_SOURCES.md), and the
[measured regional handoff](reports/REGIONAL_TWIN_STAGE1_REPORT.md).
The original BDG2 study and its main-study launcher remain stopped/disabled.
London April–December 2013 outcomes and the earlier BDG2 seals remain intact.

The regional commands below reproduce the authorized bounded package; closed
allocation ledgers refuse new compute. They do not authorize another allocation.
Use Python with the project scientific dependencies, `requirements.regional.txt`,
and the `7z` executable. The recorded local interpreter was Python 3.8; the
existing pod used Python 3.12 and PyTorch 2.8.0+cu128.

```bash
python3 scripts/regional_job.py --label ingest --timeout 5400 -- python3 scripts/prepare_london.py
python3 scripts/regional_job.py --label fit --timeout 5400 -- python3 scripts/fit_regional_model.py
python3 scripts/regional_job.py --label smoke --timeout 900 -- python3 scripts/replay_regional.py --smoke
python3 scripts/regional_job.py --kind gpu --label replay --timeout 3600 -- python3 scripts/replay_regional.py --gpu
python3 scripts/regional_job.py --label artifact_audit --timeout 180 -- python3 scripts/audit_regional_artifacts.py
python3 scripts/plot_regional.py
```

The immutable configuration has 16 latent variables, a 24-step window, 16
simulated providers, 32 origins across four development weeks and 16 access
profiles. Per-household/cohort/regional predictions and model/state snapshots
are under ignored `data/regional/`; small measurements and manifests are in git.
Figures use retained numeric outputs only. No raw readings are redistributed.

## Earlier weighted-provenance study

**Stage 2 decision C: stop/defer this DSpaCES project.** The original sketch
approach is stopped. The evidence does not yet justify its narrow paper fallback
or an event-time pivot. The main study remains disabled; no Stage 3 is proposed.

A subsequent September 23 planning request produced
[When Forecast Contracts Disagree](DSpaCES_2026_Research_Plan.md), a complete
conditional design for a separate compatibility-contract feasibility study.
It attributes the mathematical ingredients to existing work and proposes early
novelty and usefulness gates. This planning addendum does not reverse Stage 2's
decision, authorize another pilot, or unseal calibration/test outcomes.

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
