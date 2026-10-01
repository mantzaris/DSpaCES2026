# IoT entropy reference study

Research for IEEE DSpaCES 2026 by Alexander V. Mantzaris and James H. Korris.
The study tests local correlation-spectrum entropy against non-entropic
synchronization features using the **same** conditional joint references,
spatial groups, calibration units and controlled injections. The hypothesis of
an entropy advantage is not assumed. All project files belong in this directory.

The submission artifact is [manuscript/paper.pdf](manuscript/paper.pdf).
Its source is [manuscript/paper.tex](manuscript/paper.tex), with numerical tables
and figures generated from saved results. Author affiliations and corresponding
email were not supplied and are not invented. The user owns the final repository
push and workshop submission; this workflow does neither.

## Inspect the results and replay

After a fresh clone, restore the losslessly compressed numerical JSON files:

```bash
python3 scripts/manage_git_results.py restore
```

This uses only the Python standard library and verifies every restored byte
against `git-storage.json`. Existing local results are left in place.

The completed primary experiment does **not establish a consistent entropy
advantage** in detection and localization. At nominal per-issuance alpha 0.10:

| Dataset | Diffusion H recall | Diffusion S recall | H localization IoU | H untouched exceedance |
|---|---:|---:|---:|---:|
| Synthetic | 0.326 | 0.315 | 0.017 | 0.240 |
| Intel Lab | 0.106 | 0.250 | 0.009 | 0.308 |
| PEMS-BAY | 0.139 | 0.181 | 0.006 | 0.032 |

These are 360 scheduled injections nested in 56 source blocks, evaluated with
three training seeds. Localization gives misses zero credit. Intel's sparse
common-row support and limited calibration resolution are material limitations.
Equal nominal thresholds did not achieve equal background rates. The separate
`results/retrospective_budgets.json` compares empirical budgets using reused
untouched test controls; it is explicitly retrospective, not a deployment
calibration guarantee. Native alerts are not adjudicated physical failures.


`results/summary.json` contains all 30 detector/reference combinations, whole
recording-block intervals, seed variability, conditional/unconditional
localization, missed counts, empirical background rates and event prevalence.
`event_metrics.csv.gz` preserves every event, seed and nominal alpha.
`cross_dataset_summary.csv` contrasts equal weighting of the three primary
datasets with event-pooled scores; `cross_dataset_weighting.json` defines those
weights. Synthetic node counts remain configurations of one dataset.
`paired_comparisons.json` resamples the same recording blocks in each contrast.
`direction-paired-comparisons.json` and the standalone `directional-performance`
figure provide paired intervals within measured entropy-increase/decrease
strata, including source-block counts.
`experiments/full/score-*/predictions.npz` retains scores, rank values, node
rankings and eligibility; the event and group definitions are adjacent JSON.

The saved browser replay remains available in this local working directory.
Its generated `dashboard/data/` exports are excluded from Git. On a fresh clone,
retrieve the heavy artifacts as described below, then run `iot-entropy dashboard`
to regenerate those exports. Serve the replay from this directory:

```bash
python3 -m http.server 8766 --bind 127.0.0.1 --directory dashboard
```

Open `http://127.0.0.1:8766`. Select a recording, observation, group or heatmap
cell. The linked graph, traces and evidence show the same saved sample ensemble.
The browser has no external service dependency. A local HTTP server is needed
because replay cases are loaded as JSON. `dashboard/schema.json` describes the
sensor/group/event/frame records. `dashboard/validation/` records the browser
interaction check; the rendered screenshot remains local. Calibration ranks are not physical
fault probabilities; native real recordings have unknown causes.

## Reproduce on CUDA

The recorded execution uses Python 3.12, PyTorch 2.8.0 with CUDA 12.8, and an
NVIDIA RTX A6000. `environment/gpu-inspection.json`, `experiments/benchmark.json`
and the environment lock record hardware, driver and software. Use Python 3.11+
for the source package; use Python 3.12 for the recorded dependency lock.
Commands below run from `iot-entropy`.

```bash
python3.12 -m venv --system-site-packages .venv
source .venv/bin/activate
.venv/bin/python -m pip install -r environment/requirements.lock.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .

iot-entropy acquire
iot-entropy prepare
iot-entropy synthetic --device cuda
PYTHONPATH=src .venv/bin/python -m pytest -q

PYTHONPATH=src .venv/bin/python scripts/pilot.py
iot-entropy train
iot-entropy score
PYTHONPATH=src .venv/bin/python scripts/finish_gpu.py
PYTHONPATH=src .venv/bin/python scripts/compress_replays.py

iot-entropy evaluate
PYTHONPATH=src .venv/bin/python scripts/operating_points.py
PYTHONPATH=src .venv/bin/python scripts/calibration_diagnostic.py
iot-entropy figures
iot-entropy dashboard
iot-entropy paper
PYTHONPATH=src .venv/bin/python scripts/audit_artifacts.py
```

Activate `.venv` or invoke `.venv/bin/iot-entropy` in place of `iot-entropy`.
`latexmk`, `pdflatex` and BibTeX are needed for the final command. The official
IEEEtran class and bibliography style are vendored with their license/source.
The smoke configuration is in `configs/smoke.json`; a quick scoring integration
check with existing full checkpoints is
`PYTHONPATH=src .venv/bin/python scripts/score_all.py --smoke --dataset synthetic64 --seed 17`.
The training smoke/pilot writes separately under `experiments/pilot`.
The final audit verifies raw and processed data, checkpoint and replay hashes,
identical fault manifests, every saved calibration rank, and the recorded
runtime ceiling. It writes `experiments/artifact-manifest.json` with source and
publication-artifact checksums. The publication was rendered locally; its
separate reporting environment is recorded in
`environment/reporting-environment.json`.
`experiments/validation/` also records all 11 passing CUDA checks and report
regeneration under the locked Python 3.12 environment. The latter can be rerun
with `PYTHONPATH=src .venv/bin/python scripts/verify_reporting_environment.py`;
it regenerates the same numerical tables with environment-specific graphics.
`iot-entropy features`, `calibrate`, and `score --dataset NAME --seed SEED`
expose individual stages. Full scoring includes development selection and
calibration before test work; a separate `calibrate` invocation is optional.

`configs/full.json` freezes the full experiment. The configured four-hour
ceiling sums completed GPU-stage wall times, including sampling, feature
calculation and serialization, the pilot and the scoring smoke check. Initial
data acquisition/preparation and validation were not separately timed and are
outside this recorded stage total. It is not pod rental uptime or an estimate of
utilization-weighted GPU kernel hours. No infrastructure is provisioned.
Completed run directories are resumable. To intentionally rerun a completed
experiment, archive its outputs and use a fresh project working copy; do not
mix new configurations with old completion markers. Fixed random seeds do not
promise bitwise equality across different CUDA/library versions.

## Data and provenance

Exactly three primary datasets are used: one independently simulated spatial
benchmark with 64/128/256-node configurations, Intel Berkeley Lab, and the
original DCRNN PEMS-BAY release. `data/manifests/` contains original URLs,
checksums, timestamps, raw-to-processed transformations, coverage, split bounds
and simulation seeds. `data.py` downloads original Intel files and the DCRNN
authors' linked HDF5 file and graph metadata; it never substitutes datasets.

Intel uses last-observed whole rows in right-labeled two-minute bins, with no
interpolation. The pre-test availability audit excludes its terminal sustained
humidity collapse after March 23, 2004; `intel_full.npz` preserves the complete
original span as an auxiliary view of the same dataset. All 54 motes remain.
Primary channels are temperature/humidity. PEMS retains all 325 sensors and
the supplied road-distance graph. Its release actually spans January–June
2017; the timestamp gap is masked. Original upstream per-value imputation
lineage is unavailable. Real data are nominal, not certified fault-free.

All quantitative real-data faults are **controlled injections into held-out
recordings**. They are not confirmed field failures. Correlations use common
observed rows separately by channel. Missing and constant windows abstain;
flatline alerts are reported as a separate quality hybrid. Per-issuance
calibration has a finite-sample guarantee under exchangeability, which is not
asserted for the real streams. Disjoint real blocks are resampling units, not
proof of independence. Their untouched alerts are empirical background
exceedances, not adjudicated false physical-fault alarms.

## Artifact locations and recovery

- `docs/`: frozen protocol, coverage amendments, original-source literature
  verification, venue rules, proofs and equation-to-code checks.
- `src/iot_entropy/`: acquisition, stochastic benchmark, joint graph diffusion,
  measurements, calibration, baselines, evaluation, plotting and replay export.
- `experiments/full/`: training logs, checkpoint hashes, calibration, predictions,
  replay sources and reference feature draws; `unscreened/` isolates its models.
- `experiments/sensitivity/`: graph, sample count, coverage/PSD estimator,
  persistent-history and longer-window global/local sensitivities.
- `experiments/selected-ensembles/`: raw joint diffusion/bootstrap draws for
  selected replay observations, validated against their original feature arrays.
- `results/`: reproducible statistical summaries and complete event metrics.
- `manuscript/`: IEEE LaTeX, verified BibTeX, generated PDF/SVG figures and PDF.

Raw/processed data, checkpoints, generated samples, full replay sources and
dashboard data exports are mirrored locally but ignored by Git. PNG previews
and the downloaded IEEEtran ZIP also remain local. Git retains code, manifests,
compact saved predictions/calibration, numerical results, PDF/SVG publication
figures, the compiled paper, and the IEEE class/style with their notices.
Larger JSON results are committed as lossless `.json.gz` archives listed in
`git-storage.json`. On the supplied pod,
the matching files are at `/workspace/iot-entropy/` with identical relative
paths. In particular, checkpoints are
`experiments/full/checkpoints/{dataset}-{kind}-{graph}-{seed}.pt` and
`experiments/full/unscreened/checkpoints/…`. Checksums in the run manifests
identify them. Their continued remote availability depends on the user's pod;
the local mirror is the durable handoff. They can also be regenerated by the
commands above.

After regenerating results, refresh the compressed copies and check the staged
project size before committing:

```bash
python3 scripts/manage_git_results.py pack
git add -- .
python3 scripts/manage_git_results.py check
```

The check rejects tracked ignored files, any file above 5 MiB, or a project
total above 50 MiB. It does not stage, commit or push. Existing historical
experiment commit IDs remain recorded; `environment/git-history-map.json`
maps them to the history with generated bulk removed.

Expanded replay JSON is stored as lossless `.json.gz` to fit the local disk.
`experiments/replay-compression.json` records compressed and original SHA-256
hashes; compression verifies a full byte round trip before removing an expanded
copy. Plotting and dashboard export read either form directly. No measurement
precision is lost. `gzip -dc RECORD.json.gz` recovers the original JSON bytes.

`scripts/pod.sh upload` synchronizes source to that directory;
`scripts/pod.sh download` verifies/compresses completed replays, then retrieves
data, experiments and environment records.
`scripts/ssh-gpu.sh` reconnects to the user-provided endpoint using the explicitly
authorized existing RSA key. The host-key file lives in ignored `.local/ssh/`;
private keys are never copied into this project. These helpers do not change
pod lifecycle or billing.

Use `main` for this project's commits. Do not push: the user will perform the
final push. Preserve sibling research projects in the repository.
