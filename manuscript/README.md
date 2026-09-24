# From Detail to Decisions in Regional Energy Twins

[Compiled author-review PDF](regional_twin_study.pdf), ten pages including references,
IEEEtran conference mode on US Letter. One primary empirical case-study draft;
no extra-page appendix is required to understand the argument. Four vector figures
are provided as PDF and editable SVG in `figures/`. The author's name, affiliation
and email were supplied explicitly in this session.

## Clean build without data access or a GPU

From the repository root:

```bash
python3 scripts/synthesis_job.py --ledger results/editorial/resource_ledger.json --prior-handoff results/synthesis/resource_handoff.json --label editorial-clean-build --timeout 180 -- bash manuscript/build.sh --clean
```

This regenerates result tables, four figures, source hashes, the PDF and automatic
document checks. It reads committed saved numerical outputs only. It does not open
raw Parquet, model NPZ files, held-out outcomes, network connections or CUDA. Page
renders go to `/tmp/regional-twin-manuscript-review/`. The wrapper records executed
CPU job wall time against the existing cumulative supporting-work allowance.
Read-only review and writing time are separate; no closed GPU stage is reopened.

Dependencies are Python 3 with NumPy, pandas and Matplotlib, plus `latexmk`,
`pdflatex`, BibTeX, Poppler `pdfinfo`, `pdffonts`, `pdftotext` and `pdftoppm`.
The build uses standard AMS, graphics, booktabs, array, cite, balance and hyperref packages.
The balance package balances the ending without changing IEEE typography.
`environment.json` records the tested local versions. `IEEEtran.cls` and
`IEEEtran.bst` are unmodified upstream files with their notices preserved;
`template_source.json` records the archive and file hashes. No custom typography
or compressed template spacing is used. `SOURCE_DATE_EPOCH` is fixed in `build.sh`.

To check that editorial changes preserve the synthesis outputs and verify the
revised effect size (requires the preceding synthesis commit in git history):

```bash
python3 scripts/check_regional_editorial.py
```

To regenerate only audited numbers and plots:

```bash
PYTHONPATH=src:.deps python3 scripts/build_regional_study_results.py
```

Key outputs under `results/synthesis/`:

- `principal_results.csv` and `family_method_results.csv`: cohort-separated means,
  event counts, misses and controls. LaTeX Table II is generated from these inputs.
- `paired_background_B.csv`, `paired_background_C.csv`,
  `paired_background_events.csv`: all background-level paired summaries, not
  independent-hour confidence intervals.
- `threshold_margins.csv.gz`, `diagnostic_path.csv`: original-policy score/gate
  checks with explicit event versus full-replay scopes.
- `corrective_action_timing.csv`, `corrective_action_summary.csv`: actual requested
  IDs, timing and available alarm scores. Event-ID membership is explicitly not
  equated to a finite nonzero measurement at every time.
- `input_hashes.json`, `manuscript_checks.json`, `resource_ledger.json`: provenance,
  current build checks and historical CPU accounting. Editorial CPU work is recorded
  separately under `results/editorial/`, inheriting the closed synthesis totals.
  Manual page inspection is recorded separately
  in `visual_review.json`.

The [claim map](../reports/REGIONAL_TWIN_CLAIM_EVIDENCE.md) links scientific claims
to configurations, source versions, episode IDs, metric definitions and limits.
The [synthesis report](../reports/REGIONAL_TWIN_SYNTHESIS_REPORT.md) records new
analysis and remaining questions. The [venue/source note](VENUE_AND_SOURCES.md)
records official formatting checks and primary-paper access. The
[editorial report](../reports/REGIONAL_TWIN_EDITORIAL_REVISION.md) records the
revised argument, figure padding, column balance and final validation. The
[author-review checklist](AUTHOR_REVIEW.md) identifies substantive decisions.

## Experimental reproduction is a separate operation

This build reproduces the paper from retained results. It does not authorize
rerunning the research. The exact original GPU preparation/replay commands are in
the regional Stage 1-4 reports and their frozen manifests. The latest GPU source is
`18fe4af`; the paper synthesis starts from `99dc6b8`. Original B replay used
`031bdd6`. Later reconstructed intermediates are explicitly distinguished from
originally logged values. Tracked code preserves all prior negative findings.

Raw meter data and large caches stay outside git. Source attribution is UK Power
Networks, Low Carbon London, London Datastore. The originating archive hash and
recorded CC BY 4.0 terms are in `manifests/regional_source.json`. Current rendered
catalog wording is Creative Commons Attribution. Duplicate keys, invalid values,
clock ambiguities and missing-target support are described in the manuscript and
data protocol; do not substitute a different Kaggle preprocessing variant.

London April-December 2013 and BDG2 seals remain intact. Original main study remains
disabled. Build scripts cannot launch an experiment. The pod remains allocated and
idle, with billing continuing separately. No submission, registration or payment
has been performed.
