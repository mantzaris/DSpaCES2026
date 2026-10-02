# Spatial and Temporal Entropy for IoT Fault Detection

Comparative research for IEEE DSpaCES 2026 by Alexander V. Mantzaris and
James H. Korris. The extension separates feature family, reference model,
estimator support, calibration and localization. Neither entropy nor diffusion
is required to win.

Read [the manuscript](manuscript/paper.pdf), [findings](docs/extension-findings.md),
[the frozen protocol](docs/extension-protocol.md), and
[the audit amendment](docs/extension-audit-amendment.md).
The original study remains in `experiments/full`, the original `results/`
files, and revision `b900da1b`. Its [README](docs/original-study-readme.md)
describes the original pipeline. The complete, editable LaTeX source is
`manuscript/paper.tex`: all sections and tables are inline. Only
`manuscript/references.bib` and the figures remain external content; compilation
does not load any other manuscript `.tex` files.
The original removed/shuffled-topology ablations are retained in v1; the
frozen temporal extension fixes the physical/proximity graph to compare features.

All 15 primary extension runs completed: 360 new fault realizations in 20
source blocks, three training seeds, one synthetic benchmark (64/128/256-node
configurations), Intel Lab and PEMS-BAY. The main comparisons show no consistent
overall entropy or diffusion advantage. Temporal entropy captures some changes
that spatial covariance cannot, but conventional temporal statistics can also
do so. Both real-background extensions are exploratory reuse with semi-synthetic
faults, not validation against verified native failures.

The user explicitly raised the cumulative GPU experiment allowance to eight
hours after the original four-hour stop. The original stop is preserved in the
ledger; completed stages and actual time are recorded in
`experiments/extension-v2/completion.json`. The separately frozen
[scale-2 sensitivity](docs/extension-multiscale-protocol.md) reuses seed-17 episodes
and references and is exploratory. No infrastructure was provisioned, and
nothing was submitted or pushed. Affiliations and corresponding email were not supplied.

## Rebuild results, figures, paper and dashboard without a GPU

Run from this directory. Python dependencies are declared in `pyproject.toml`;
`environment/requirements.lock.txt` records the CUDA experiment environment.
The tested CPU reporting versions are in `environment/reporting-environment.json`.
IEEEtran and its bibliography style are vendored. LaTeX commands need `latexmk`,
`pdflatex` and BibTeX; figure export uses Ghostscript to subset embedded fonts
without rasterizing the plots. Original full-font PDFs remain local.

For manuscript edits, edit `manuscript/paper.tex` and run the `latexmk` command
below. The results regeneration command `scripts/extension_writeup.py` refreshes
only the four blocks marked `% BEGIN GENERATED` / `% END GENERATED` in that
file, preserving the surrounding prose. Edit numerical prose in that script
to retain it across results regeneration. The files in `manuscript/generated-v2/`
are intermediate generation outputs, not dependencies for compiling the paper.

```bash
export PYTHONPATH=src
export OPENBLAS_NUM_THREADS=1
python3 scripts/pack_extension.py verify
python3 scripts/extension_report.py
python3 scripts/extension_stratified.py
python3 scripts/extension_multiscale.py --report-only
python3 scripts/extension_completion.py
python3 scripts/extension_figures.py
python3 scripts/extension_writeup.py
python3 scripts/build_extension_dashboard.py
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error manuscript/paper.tex
python3 scripts/verify_extension_artifact.py
```

These commands use committed predictions, calibration, support summaries,
compact replays and diagnostics. They do not need the raw datasets, neural
checkpoints or full generated trajectories. Numerical results are reproducible;
PDF byte hashes can differ with fonts, TeX version and embedded timestamps.
Large numerical JSON/CSV results are stored losslessly as `.gz`; project readers
load them directly, and regeneration retains readable local exports.
Before rebuilding the preserved v1 pipeline, run
`python3 scripts/manage_git_results.py restore`; it restores original JSON and
CSV bytes and verifies their hashes. Existing local originals are retained.
To rerun the standalone CPU mathematical diagnostics:

```bash
python3 scripts/extension_diagnostics.py
python3 scripts/extension_estimator_stability.py
python3 -m pytest tests -q
```

The 20-test suite passed on the A6000; locally 18 passed and two CUDA checks
were skipped. Core checks cover entropy bounds, derivatives, row-permutation
invariance, explicit sample-pair counting, ties/gaps/flatlines, leakage, rank
calibration, event matching and localization. Optimized aggregation agrees
with the unbatched definition. No point-adjusted event metrics are used.

Serve the dashboard:

```bash
python3 -m http.server 8766 --bind 127.0.0.1 --directory dashboard
```

Open `http://127.0.0.1:8766`. The three prespecified replay cases include stable
physical layouts, distinct correlation overlays, temporal evidence, reference
bands, actual changes, reference departures, quality and support counts,
forecast issuance, model version and rank p-values. Full trace views are
retrospective; the heatmap and coordination summaries stop at the selected time.
The original interface is retained as `dashboard/spatial-v1.html`; its data
exports require the original reconstruction procedure. Browser validation is
recorded in `dashboard/validation/extension-check.json`. There are no external
browser services.

## Artifact schema and storage

`experiments/extension-v2/<configuration>-<seed>/` contains:

- `configuration.json`, `data-lineage.json`, `events.json` and `status.json`;
- development parameters/selection records and `calibration.npz`;
- `predictions.npz`: scores, stored rank p-values, availability and three
  localization alternatives for every episode, decision and detector;
- compressed group, support, timing, reference and fidelity records.

Predictions use `rankings_unique[ranking_index]` to recover rankings. Only the
**development-selected localization budget** is retained in Git; unused ranks
13–24 (or 7–24 for Intel) remain in full local/remote originals. All score,
calibration, availability and used-rank entries are preserved exactly. The
compact primary prediction files total about 8.4 MiB. `packaging.json` records
checksums and the reversible dictionary encoding. Do not overwrite these
accepted compact archives with an indiscriminate remote download.

`results/extension-v2/` holds complete event metrics, paired whole-block intervals,
mechanism/severity/duration/direction/support strata, operating points, fidelity,
window sensitivities, diagnostic arrays and compressed replay cases. In event
rows, `tp/fp/fn` are event counts while `precision/recall/f1/iou` are sensor
localization metrics; summary `recall` means event recall. Missed events receive
zero unconditional localization. Conditional metrics are separately named.
Common feature support is within a reference; the separate paired-fidelity
audit uses support shared across references. Retrospective rate caps reuse test
controls and must not be interpreted as prospectively validated thresholds.
Stratified paired estimates weight represented blocks equally; they need not
equal subtraction of the event-weighted descriptive proportions in each stratum.

`experiments/extension-v2/multiscale/` preserves the separately calibrated
W96 scale-1/2 sensitivity, both references, nine feature families, seed 17.
Its compact ranks store each family's declared primary localization rule;
the main experiment retains all three alternatives. Scale 1 is checked against
the independent W96/ceil52 audit. Scale 2 uses 48 complete two-row bins and the
same physical 24-row change lag. Coarse-grid PE/ACF/Theiler lags double in
physical time; scale 4 remains an insufficient-support diagnostic.

Full raw data, checkpoints, generated draws and per-sensor measurement tensors
are ignored. Existing local files are retained. Remote heavy artifacts remain
under `/workspace/iot-entropy/` on the configured Pod:

- `experiments/full/checkpoints/` and original training manifests;
- `experiments/extension-v2/cache/<configuration>-<seed>/*.npy`;
- `experiments/extension-v2/cache/*-backgrounds.npz` (new CUDA simulations);
- `experiments/extension-v2/<configuration>-<seed>/measurements.npz`.

The reference manifests hash every saved joint draw; the heavy-artifact manifest
hashes measurements, backgrounds and checkpoints. Use the configured
`scripts/ssh-gpu.sh` and selective `rsync` over the direct SSH connection to
retrieve these if needed. No credentials or private key contents are committed.
The ordinary Git artifact is sufficient to regenerate the published analysis.

## Reproduce the CUDA experiments

Use the existing configured CUDA device; these commands do not provision one.
The original pipeline's acquisition, preprocessing and training commands are
in [the preserved README](docs/original-study-readme.md). Dataset manifests
record original URLs, units, hashes and chronological boundaries. Use the
recorded Python 3.12 / torch 2.8.0+cu128 environment for closest reproducibility.

A rerun must use a separate project copy: retain its accepted extension directory
under an archival name before creating fresh outputs. Do not mix new settings
with old completion markers. For example, in that separate copy:

```bash
mv experiments/extension-v2 experiments/extension-v2-accepted
mkdir experiments/extension-v2
cp experiments/extension-v2-accepted/original-study.json experiments/extension-v2/
cp experiments/extension-v2-accepted/budget-authorization.json experiments/extension-v2/
PYTHONPATH=src .venv/bin/python scripts/extension_pilot.py
PYTHONPATH=src .venv/bin/python scripts/extension_run.py
PYTHONPATH=src .venv/bin/python scripts/extension_final_audits.py
PYTHONPATH=src .venv/bin/python scripts/extension_window_support.py
PYTHONPATH=src .venv/bin/python scripts/validate_extension.py --cuda
PYTHONPATH=src .venv/bin/python scripts/extension_multiscale.py
PYTHONPATH=src .venv/bin/python scripts/extension_completion.py
PYTHONPATH=src .venv/bin/python scripts/extension_observability.py
PYTHONPATH=src .venv/bin/python scripts/extension_replay_export.py
```

The runner loads the frozen original checkpoints and training normalizers.
`--dataset NAME --seed INTEGER` selects a main run. New synthetic development,
calibration and test simulations use independent predeclared seeds. CUDA and
CPU RNGs need not generate the same simulation from the same integer seed:
retained CUDA arrays and a cached-bootstrap byte-agreement check resolve this.
CPU/GPU estimator checks use identical arrays. Fixed seeds do not guarantee
bitwise equality across library versions.

The cumulative guard includes recorded original work, pilot, failed/accepted
primary attempts, CUDA validation and auxiliary GPU stages. The frozen primary
configuration retains its original four-hour value; the explicit user
authorization file raises the ceiling to eight hours. All runners use the
same ledger. The original stop and subsequent authorized resume are retained.
This allowance is a ceiling, not a requirement to spend the remaining time.
CPU reporting, rendering and file checks are separate from GPU experiment-stage
time, not a claim about Pod rental uptime.

`docs/extension-equations.md` maps equations to code and saved evidence.
`docs/extension-literature.md`, `docs/venue.md` and the preserved literature
records provide verified primary sources. The venue limit is 10 pages including
references; the verified deadline is October 15, 2026. Author review, missing
contact metadata, final push and submission remain with the user.
