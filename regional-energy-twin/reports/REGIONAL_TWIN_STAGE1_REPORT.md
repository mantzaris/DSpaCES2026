# Regional digital twin feasibility pilot

Completed September 23, 2026. **The regional data and twin implementation gates
pass. The shared-basis acceleration/certificate gate does not pass on this
workload.** Preserve this executable regional prototype, but do not launch a
main study or advertise a new fast matrix method from these results.

## Completion checklist

- [x] One official real archive ingested: **167,932,474 rows**, **167,817,021
  distinct meter/time keys**, **5,566 physical household IDs**. The catalog's
  approximately 167 million / 5,567 figures are not substituted for counts.
- [x] **4,194 training-eligible households** and **52,109,356 valid 2012 readings**
  actually contribute to seasonal profiles, factor fitting/loading refits and
  noise/dynamics statistics. This exceeds both the 50-million-record and
  2,000-household targets without an unrelated small benchmark.
- [x] Persistent household-ID-linked model/state snapshots, household/cohort/
  regional forecasts at one and six hours, cutoffs and versions, and a causal
  regional replay are implemented. **32 origins, four development weeks,
  16 provider profiles = 512 matrix queries**, using 3,167,768 available window
  observations. Native masks are recomputed at all 32 origins.
- [x] Orthogonal RJD, identity and reference eigenbases; global/block norm
  bounds; polynomial corrections; residual-driven corrections; dense/banded
  Cholesky, information smoothing and batched CPU/GPU PCG are implemented.
- [x] CPU/GPU execution completed on the existing **RTX PRO 4500 Blackwell,
  nominal 32 GB**, with **zero final accuracy failures**. The request's 48 GB
  assumption does not describe this measured device.
- [x] Four measured figures, frozen manifests, proofs, source comparison,
  numerical outputs, environment records, resource ledgers, and local durable
  copies of every new pod snapshot are retained. No experiment remains running.
- [ ] Useful RJD family certificate or speed advantage over the strongest
  structured solver: **not demonstrated**. This is a negative finding, not an
  unfinished implementation hidden by the checklist.

## Evidence and reproduction map

| Evidence | Configuration / executable | Saved output |
|---|---|---|
| Official retrieval, typing, deduplication, bytes, throughput | [prepare_london.py](../scripts/prepare_london.py), [configuration](../configs/regional_pilot.json) | [source manifest](../manifests/regional_source.json), [ingestion](../results/regional/ingestion.json) |
| Training eligibility, seasonal/factor model | [fit_regional_model.py](../scripts/fit_regional_model.py) | [household inclusion list](../manifests/regional_households.json), [model audit](../results/regional/model.json) |
| Frozen regional comparison | [replay_regional.py](../scripts/replay_regional.py), [frozen origins and profiles](../results/regional/replay/frozen_manifest.json) | [summary](../results/regional/replay/summary.json), [costs](../results/regional/replay/costs.csv), [numerics](../results/regional/replay/numerical.csv), [forecasts](../results/regional/replay/forecasts.csv), [certificates](../results/regional/replay/certificates.csv) |
| Saved-output analysis and figures | [analyze_regional.py](../scripts/analyze_regional.py), [plot_regional.py](../scripts/plot_regional.py) | [analysis](../results/regional/replay/analysis.json), [four vector figures](figures/regional/) |
| Correctness, causality and seals | [tests](../tests/test_regional.py), [access boundary](../src/evidence_fusion/regional_data.py) | [39 passing local tests](../results/regional/all_tests_before_gpu.log), [39 passing pod tests](../results/regional/regional_pod_tests.log) |
| Source, budget and preservation | [source hashes](../results/regional/executed_source_hashes.json), [durable inventory](../manifests/regional_durable_artifacts.json) | [resource handoff](../results/regional/resource_handoff.json), [GPU ledger](../results/regional/gpu_ledger.json), [CPU ledger](../results/regional/cpu_ledger.json) |

Exact execution commands and failed attempts are retained in the ledgers. The
successful preparation source was committed as `2dd63f2`; the final GPU-tested
replay source is **`bf2896254ae93d85dc58619b46b3a8642c5f1af2`**. Five executed
source/configuration hashes match the final local numerical code. Later changes
add reporting, plotting compatibility, artifact auditing and download-accounting
metadata, not another model or research direction.

On an already provisioned compatible environment, the executable stages are:

```bash
python3 scripts/regional_job.py --label ingest --timeout 5400 -- python3 scripts/prepare_london.py
python3 scripts/regional_job.py --label fit --timeout 5400 -- python3 scripts/fit_regional_model.py
python3 scripts/regional_job.py --label smoke --timeout 900 -- python3 scripts/replay_regional.py --smoke
python3 scripts/regional_job.py --kind gpu --label replay --timeout 3600 -- python3 scripts/replay_regional.py --gpu
python3 scripts/analyze_regional.py
python3 scripts/plot_regional.py
```

The recorded execution allocation is closed. These commands describe reproduction;
they do not authorize resetting the ledger or opening a new compute allocation.

## Data pipeline and causal scope

The [official UK Power Networks release](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d)
links the selected archive and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Attribution is preserved in the manifest. One **801,674,949-byte ZIP** was
downloaded, containing one **8,542,818,238-byte CSV**. Its SHA-256 is
`68a35598cc8e70898a7651c482216fb096a0a6910c2d180c616632dfc7a9b014`.
No duplicate archive was fetched. A Python HTTP 403 was resolved with curl;
Deflate64 required the installed 7z streaming decoder. An incompatible DuckDB
COPY parameter API was replaced by its relation writer. Failures and retries
remain charged and visible rather than removed from the ledger.

PyArrow streams bounded CSV batches; DuckDB performs typed conversion and
per-split/per-meter-bucket deduplication into Zstandard Parquet. Final Parquet
is **528,822,113 bytes**. Successful ingestion took **356.0 seconds**, about
**471,709 source rows/second**, with **3.36 GB peak process RSS**. This includes
decompression, parsing, partition writing and deduplication; download and prior
failed attempts are separate. The first successful transfer plus hash took
36.37 seconds. Reinvocation's small hash-only duration is explicitly identified.

The archive has **115,453 duplicate excess records**. It retains a deterministic
first row and duplicate count for each key, while fitting/replay exclude every
duplicated key. Negative, nonfinite and nonnumeric readings become NULL, never
zero. Training contains 5,548 invalid/null and 5,548 off-grid keys; development
contains four of each. These structural exclusions are recorded, not imputed as
observed energy. The local timestamp convention is unresolved by the catalog.
We retain source-clock labels, exclude whole last-Sunday March/October transition
days in accessible panels, and make no invented UTC precision claim. All replay
origins are away from those transitions.

2012 supplies eligibility and all fitted parameters. A household needs at least
8,760 valid training readings; 4,194 qualify. Their training grid is 29.3% missing,
including enrollment gaps. Each observed value contributes to household weekly
profiles and scales. Standardized missing residuals are initially mean-imputed
for a fixed randomized SVD, then each loading is refit on its observed rows only.
This is a declared descriptive missing-data approximation, not zero-demand
imputation or proof of unbiased latent recovery. Fitting took 38.18 seconds,
including 27.96 seconds of panel parsing, with 2.97 GB peak process RSS. The
16-state transition's spectral radius is **0.994245**; no stability contraction
was needed. No architecture or hyperparameter search was run.

There are 3,362 standard-tariff and 832 ToU households in the cohort. Tariff is
accounted for descriptively, without a causal effect claim. The 16 deterministic
provider groups contain 244–296 real household IDs each, but the organizations
and access/confidence profiles are simulated. No boroughs, feeders, substations,
coordinates or population expansion weights are inferred. This is a twin of the
sampled eligible Greater London households, not of every London household.

January–March 2013 supplies development only. The replay visits four prespecified
weeks and uses a 24-half-hour window at each origin, with 2- and 12-step targets.
The common initial prior is propagated from the earlier all-provider snapshot;
profiles intervene on access within the new window, not on long-running outage
policies. Observation-dependent RHS statistics are removed for zero-availability
providers. Masked data poisoning is tested. A 64-matrix FIFO cache is shared in
capacity across dense CPU, banded CPU and GPU factor methods; there were 487
new matrices among 512 queries. Changing native masks triggers fresh components
and certificate preprocessing, whose cost is included. The final audit checked
12,288 native measurement blocks: withdrawing a provider changes trajectory
rank **368–384 out of 384**, offering no justified small-rank update shortcut.

April–December 2013 and later London demand values were only ingested and
partitioned; they were not fitted, explored or scored. The analysis API refuses
sealed partitions. Only development Parquet and the trained model were copied
to the regional pod directory. A key-only inventory and opaque hashes cover
sealed files without demand summaries. Earlier BDG2 seals and the disabled
original main-study launcher remain unchanged.

## Twin outcomes: descriptive development evidence

There are **64 distinct target intervals and 264,251 observed household-target
values**, not 1,024 independent targets from repeating 16 profiles. The panel
covers only four selected weeks. No hourly independence assumption, population
confidence interval, predictive-equivalence claim or held-out test claim is made.
Every target misses at least one cohort household: observed support ranges from
4,082 to 4,168 of 4,194. Scores compare each prediction to exactly that support.
Persistent files also contain full-cohort forecasts, but partial sums are never
called complete regional ground truth.

| All-provider prediction | 1 h regional MAE / RMSE, kWh | 6 h regional MAE / RMSE, kWh | 1 h household MAE / RMSE, kWh |
|---|---:|---:|---:|
| Exact moving-horizon twin | **39.56 / 46.72** | **63.75 / 79.74** | 0.1372 / 0.2598 |
| No new observation, same propagated prior | 131.24 / 151.94 | 105.23 / 144.36 | 0.1396 / 0.2694 |
| Training-fitted weekly seasonal profile | 232.24 / 261.10 | 215.40 / 244.85 | 0.1401 / 0.2861 |

These are kWh per target half-hour, forecast one or six hours ahead. The seasonal
baseline is the fitted weekly profile, not a tuned modern forecasting competitor.
The large regional improvement and smaller household improvement are consistent
with useful aggregate state assimilation. They do not establish a novel forecasting
method. No physical response to tariff changes, provider failures or power outages
is identified by these access interventions.

## Matrix results and complete cost

The [proof document](../docs/REGIONAL_MATRIX_PROOFS.md) derives C_0, b_0 (including
lambda times the fixed center), C_g and b_g from one objective. It proves the
global and symmetric-block majorant, the Neumann remainder, and the regional
output multiplier. It attributes RJD and preconditioning to established work;
the [source comparison](../docs/REGIONAL_SOURCES.md) makes remaining novelty limits
explicit. This is no new joint-diagonalization, unlearning or privacy theorem.

All solves used the same FP64 matrices/RHS and exact CPU Cholesky reference.
Source/model panels are stored in FP32 before FP64 construction, identically for
every method. The fixed acceptance thresholds were residual <=1e-5 and A-energy
relative error <=1e-4; iterative stopping used 1e-7 residual to leave margin.
The maximum accepted residual was **9.999e-8** and maximum weighted relative
error **1.212e-7**. The largest regional additional solver error was
**3.857e-5 kWh**, versus the frozen **0.833709 kWh** tolerance. All numerical
methods agreed with the exact twin's training-threshold peak alerts at both
horizons. This is numerical alert agreement, not observed outage detection.
No PCG-to-Cholesky accuracy fallback was needed.

| Basis, 512 queries | Median global / block bound | delta < 1 | Degree-12 output bound meets tolerance |
|---|---:|---:|---:|
| Identity | 16.204 / 7.449 | 0 | 0 |
| Reference-matrix eigenbasis | 6.067 / 2.272 | 62 | **31** |
| Three-trial orthogonal RJD | 5.788 / 2.942 | **0** | **0** |

Thus RJD's cheap certificate is inconclusive for **100%** of this family; that
does not prove the Neumann iteration itself diverges. PCG supplies accurate
corrections independently of that certificate. Degree-12 polynomial outputs are
also evaluated wherever delta<1; most loose bounds greatly exceed actual error.
Four actual queries per basis receive explicit spectral-norm audits; all pass.
Controlled tests verify the remainder on a near-commuting PSD family, centered
gradients, zero RHS, unavailable observations and equivalent banded/smoother
solutions. There are **39 passing tests**, not a formal floating-point proof.
Negative computed Gram forms return infinity rather than being clipped. The
remaining transform/orthogonality rounding error is not fully enclosed.

RJD-family preprocessing per changed mask had median transform cost **30.33 ms**,
global Gram cost **14.27 ms**, and block Gram cost **27.40 ms**. Median global
query evaluation was **14.72 microseconds**, versus **669.95 microseconds** for
the block bound. The block bound is tighter here, but its overhead does not buy
a conclusive RJD certificate. Costs include absolute-product rounding allowances.

CPU/GPU comparisons ran together on the same AMD EPYC 7443P pod with four BLAS/
framework threads, PyTorch 2.8.0+cu128, CUDA 12.8 and driver 580.159.04. The GPU
reported 32,623 MiB through nvidia-smi. Peak PyTorch tensor allocation was
**176.4 MB**; peak replay process RSS was **1.84 GB**. Neither the 24 GB device
target nor 8 GB process working target was approached. Process RSS does not
include all OS/container or library-driver memory.

Each window has a 384-coordinate trajectory. Its 17 FP64 component matrices
occupy about 20.1 MB; a 16-query dense batch is about 18.9 MB before factors and
workspace. The full basis is 384 by 384. This is substantial observational data
processing feeding small structured systems, not a claim that each query is a
large GPU problem. Parallelism comes from the fixed provider profiles and origins.

| Method | Solver stage p50 / p95 per 16 queries, ms | Complete snapshot p50 / p95, ms | Complete queries/s |
|---|---:|---:|---:|
| CPU banded Cholesky | **2.68 / 3.57** | **217.07 / 228.80** | **73.31** |
| CPU dense Cholesky | 13.53 / 16.18 | 229.22 / 241.32 | 69.70 |
| GPU dense Cholesky, with transfers | 3.87 / 4.10 | 218.15 / 230.22 | 72.19 |
| CPU finite-window information smoother | 21.04 / 24.65 | 236.36 / 247.96 | 67.38 |
| CPU batched PCG | 1309.11 / 1408.50 | 1528.26 / 1626.79 | 11.12 |
| GPU batched PCG | 172.73 / 194.18 | 387.70 / 412.62 | 40.69 |
| CPU RJD initialization + corrections + family work | 334.50 / 356.30 | 549.75 / 567.40 | 29.85 |
| GPU RJD initialization + corrections + family work | 147.06 / 152.86 | 360.29 / 372.98 | 44.32 |

Complete snapshot numbers are sums of measured provider-statistic preparation,
header handling, assembly, matrix-key hashing, method stages, prediction production
and persistent snapshot output. They exclude offline scoring and other methods'
diagnostic work. Bulk development parsing (10.03 s), RJD setup (0.139 s), reference
basis setup (0.017 s), and CUDA/import initialization (1.32 s) are reported
separately and allocated in the saved amortized costs. They are not falsely
presented as zero. The actual final replay, including all baselines and audits,
took **199.90 seconds**. Model fitting was a separate CPU stage.

Synchronized GPU Cholesky kernel timing alone yields 3,436 queries/s, versus
2,561/s including its transfer stage. Cached GPU solve kernels reach 28,996/s,
but cached complete processing is only 73.56/s (216.36/227.81 ms p50/p95). Cached
CPU dense solves give 72.83 complete queries/s. These small complete-pipeline
differences across 32 origins do not establish superiority or equivalence. There
is **no measured amortization break-even against CPU banded Cholesky**: the GPU
and RJD setup is additional and their observed full-stage costs do not beat it.
GPU batching accelerates these dense/iterative kernels, but the strongest
structured CPU comparator removes the claimed practical acceleration advantage.
The PCG implementation is vectorized PyTorch/NumPy, not a tuned fused Ginkgo
kernel; this limitation does not weaken the measured banded-solve counterexample.

An initial complete run at `2dd63f2` is preserved under
`results/regional/replay_initial/`. It omitted matrix hashing from complete cost
and charged RJD-specific transfers to GPU Cholesky. The final run corrects these
bookkeeping issues and separates certificate stages. **Model, data, profiles,
origins, tolerances and seeds were unchanged.** The repeat and plotting retries
are charged; no outcome-selected retuning or extra GPU optimization was run.

## Visuals, resources and disposition

Four PDF/SVG plots are generated directly from saved numbers:

1. [Regional predictions](figures/regional/regional_predictions.pdf): every
   frozen origin, both horizons, explicitly matched observed support.
2. [Numerical accuracy and bounds](figures/regional/numerical_accuracy_bounds.pdf):
   residuals, sorted family bounds, actual polynomial error versus its bound.
3. [Speed and amortization](figures/regional/speed_amortization.pdf): measured
   complete costs and descriptive 5–95% variation across origins; a separately
   labeled projection from measured setup, not additional experiments.
4. [Pipeline scale](figures/regional/pipeline_scale.pdf): actual parse progression
   and process memory through deduplication, with bytes and the host target.

The regional GPU execution window ran **05:05:58–05:15:13 UTC**, **554.60 seconds
(9.24 minutes)** including idle gaps, dependency setup, tests and both full runs.
GPU job wall time was 413.10 seconds. The combined resource handoff additionally
charges the existing pod conservatively from the very first local regional job
at 04:47:49 UTC through final stage closure; this remains below three hours and
is the cap-comparison figure. All local CPU jobs, failures, analysis/plot retries,
plus whole GPU job time are charged against the six-hour CPU budget. Exact final
totals, dependency setup allowances and remaining capacity are in the handoff
ledger rather than an untracked rounded estimate. No main-study budget is used.

Final conservative totals are **37.43 allocated minutes** against the three-hour
GPU cap and **19.51 charged CPU job-minutes** against six hours (including whole
GPU jobs and a 60-second ancillary-helper allowance). Local wrapped CPU jobs
alone used 697.62 seconds. The remaining caps are unused, not permission to
reopen this closed stage. Source download is 801.67 MB; a conservative additional
210 MB allowance covers both machines' dependency downloads and catalog metadata.

New durable data/model/snapshots occupy about **1.37 GB**, well below 30 GB;
the one source archive plus dependency downloads remain below 4 GB. The official
source, typed partitions, trained model and all 32 final snapshots are under
local `data/regional/`. The pod-output transfer was hash-verified as
`756e287807c29e9dff37549d41eda4af4101ee7879ba296c229c58317845c174`.
The [inventory](../manifests/regional_durable_artifacts.json) records each durable
file's bytes and SHA-256. Earlier BDG2 artifacts remain preserved separately.
No irreplaceable new research artifact remains only on the pod.

The pod **remains allocated**, with no active CUDA/research job at closure; its
billing allocation continues until the user changes it. The remote workspace is
an overlay, not a promised durable volume. A safe user-controlled stop procedure
is: check the local inventory and committed results; verify no research job or
CUDA process is running; then use RunPod's **Stop** control for this existing pod,
after checking which storage that control preserves. Do not choose Terminate or
Delete. No remaining artifact copy is required for this completed pilot, and no
pod lifecycle action was executed here.

The defensible conclusion is a substantial regional observational pipeline and
working retrospective twin, with a negative shared-matrix acceleration result
against strong structured solvers. Its scientific novelty and publishability
remain unresolved. Keep the compatibility-contract candidate and prior BDG2
record intact; do not use either to relabel this negative finding as success.
No Stage 2 regional extension, alternative direction or full study starts
automatically from this handoff.
