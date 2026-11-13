# Accepted-paper revision

This directory contains the camera-ready revision of **From Detail to Decisions
in Regional Energy Twins**. The original `../manuscript/` and all historical
results remain read-only. Nothing has been committed, pushed or submitted.

Primary outputs:

- `regional_twin_study_source.zip`: standalone source package, including the clean PDF, required LaTeX assets, editable SVG figures, build instructions and a source hash manifest.

- `regional_twin_study.pdf`: clean IEEE conference manuscript, 10 pages including references.
- `regional_twin_study_diff.pdf`: 12-page review copy, with additions in blue and deletions in red. The page limit applies to the clean manuscript.
- `figure_changes.pdf`: original and annotated Figure 2, on separate pages.
- `response_to_reviewers.md`: point-by-point responses.
- `change_summary.md`: changes and remaining author checks.
- `revision_analysis.md`: analysis definitions, provenance and deferred validation.

## Rebuild

From the repository root:

```bash
bash regional-energy-twin/manuscript-revised/build.sh
```

The script reads historical inputs through explicit project paths and writes only
inside this revision directory. It recomputes the payload/parameter audit and
saved-score alarm comparison, regenerates Figure 2, compiles all three PDFs and
renders every page for inspection. It checks title/abstract and mathematical-block
preservation, unchanged original files, fonts, references and the clean page limit.
It neither reads raw meter data nor runs inference. Do **not** run the original
manuscript build/result scripts to reproduce this revision.

For a clean LaTeX rebuild, delete only these revision-local products first:

```bash
cd regional-energy-twin/manuscript-revised
latexmk -C regional_twin_study.tex regional_twin_study_diff.tex figure_changes.tex
bash build.sh
```

Document-only build, using the included figures, tables, bibliography and template:

```bash
cd regional-energy-twin/manuscript-revised
latexmk -pdf -interaction=nonstopmode -halt-on-error regional_twin_study.tex
python3 scripts/prepare_diff.py
latexmk -pdf -interaction=nonstopmode -halt-on-error regional_twin_study_diff.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error figure_changes.tex
```

These document commands need no historical results or remote resources. Full
analysis/validation additionally uses the surrounding read-only project.

Dependencies used here: Python 3.8.10, NumPy 1.22.1, pandas 1.3.4, Matplotlib 3.1.2;
TeX Live 2019/Debian, IEEEtran (included), latexmk 4.67, latexdiff 1.3.0, and Poppler
`pdfinfo`, `pdffonts`, `pdftotext`, `pdftoppm`. The included template's typography,
fonts, column widths and spacing are unchanged.

## Analyses and checks

```bash
cd regional-energy-twin/manuscript-revised
PYTHONDONTWRITEBYTECODE=1 python3 scripts/audit_provenance.py --project .. --output analysis/provenance_checks.json
MPLCONFIGDIR=internal/mplconfig PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_alarm_sweep.py --project .. --output .
MPLCONFIGDIR=internal/mplconfig PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_episode_figure.py --project .. --output .
python3 scripts/validate_revision.py
python3 scripts/package_revision.py
```

`analysis/alarm_checks.json` records the focused threshold/window checks and source
hashes. `analysis/alarm_matched_rates.csv` supplies the new main-paper table.
`figures/alarm_sweep.pdf` and `.svg` show full descriptive curves, original frozen
points and the inclusive-window frozen points. This is a fixed-acquisition alarm
analysis, not a newly evaluated policy. Localization is not extrapolated across
thresholds.

`baseline/manuscript/` is the immutable starting snapshot. The source/PDF hashes
and 553 original tracked-file hashes are in `internal/baseline_manifest.json`.
The snapshot includes original local manuscript content, not an older experimental
commit. `source_changes.patch` compares corresponding old/new sources. The marked-up
PDF compares tables separately to avoid misleading row alignment when floats move;
added tables are blue. Actual source float moves remain visible in the patch.

The `internal/` directory contains build logs, validation results, page renders and
visual-review records. These are review aids, not supplementary scientific evidence.

## Standalone source ZIP

Regenerate and check the source ZIP without changing the manuscript:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 regional-energy-twin/manuscript-revised/scripts/build_source_zip.py
```

The check extracts the archive into a temporary directory inside `internal/`,
removes the packaged PDF and compiles from the packaged sources. It verifies the
10-page result and identical extracted text, then removes the temporary build.
`internal/source_zip_validation.json` records the check; the ZIP has a `.sha256`
sidecar. Review markup, raw data and experimental caches are excluded.
