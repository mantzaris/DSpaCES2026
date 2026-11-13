# Camera-ready revision summary

Starting commit: `c2ef65803307ea1652d359dc3e530e3c6af40193`.
The clean manuscript is **10 pages**, IEEE two-column conference format including
references. The marked-up review copy is 12 pages; the figure comparison is two.

## Preservation

- Title unchanged: **From Detail to Decisions in Regional Energy Twins**.
- Abstract preserved verbatim, including the unchanged numerical macro expansion.
- All three propositions and proofs, method definitions and original principal
  result rows are unchanged.
- The original manuscript, historical outputs/configurations and resource ledgers
  are unchanged. Baseline hashes and final checks cover 553 original tracked files.
- No new inference, policy, tuning, raw-data access or GPU computation. Both outcome
  seals remain intact and the original main study remains disabled.

## Targeted changes

1. Added an explicitly illustrative energy-analytics use case and a compact
   findings/design-guidance table. The diagnostic contribution is distinguished
   from operational validation; repeated general statements were shortened.
2. Explained synthetic modulo-16 groups, prior restarts without boundary messages,
   the modest 384-dimensional separator and limits on generalization. Added short
   definitions at first use instead of another terminology table.
3. Audited gate provenance: the threshold is the 98th percentile of 88 post-startup
   M1 scores; decay 0.8 and offset 2 are fixed heuristics, not tuned parameters.
   Prediction-interval adjustment uses 96 origins and is separate from alarms.
4. Added a saved-score alarm comparison with acquisition held fixed. At 7/384
   control alarms, M0/M2/M3/M4 each detect 8/96 disturbances; M1 detects 6/96.
   At 19/384, random M2 detects 27/96 versus M3's 19/96. These are descriptive
   development results, not independent calibration or an improved policy.
5. Corrected a verified window-description error: original panel B uses lags 0-5;
   panel C uses 0-6. Original counts remain in Table II. New comparisons use 0-6
   inclusive, with both frozen windows retained in the technical analysis.
6. Corrected the payload wording: 22.52 MB and 364.95 MB are **total M3/M4 estimated
   consumer payloads**, including summaries. The request and total-payload ratios
   are 20.07 and 16.21, respectively. Decimal units and overheads are explicit.
7. Marked the later, shared-background score spike directly in Figure 2(d).
   The underlying curves and values are unchanged; Figures 1, 3 and 4 are unchanged.
8. Added the author-confirmed James H. Korris after Alexander V. Mantzaris, with
   Creative Technologies Inc. and the confirmed email, in the author block and
   PDF metadata. No author information remains missing.

## Verification

The revision-local build compiles the clean, marked-up and figure-comparison PDFs.
Automated checks cover preserved sources, abstract/macros, mathematical blocks,
original counts, threshold ties, event windows, control denominators, output paths,
embedded fonts, references, citations and page count. The final rendering and visual
inspection records are in `internal/validation.json`, `internal/clean_visual_review.json`
and `internal/diff_visual_review.json`. Compilation and arithmetic checks do not
establish scientific calibration or operational performance.

`source_changes.patch` is a source-to-source comparison; it does not merely show
this directory as entirely new. `figure_changes.pdf` exposes the graphical edit.
The bibliography and IEEE template are unchanged. Nonessential ingestion/cache
bookkeeping is preserved in `revision_analysis.md`.

## Remaining author checks and deferred work

- Confirm the submission system uses the approved two-author order and affiliations.
  It was not accessed or changed here.
- Review the disclosed B-versus-C window correction and the descriptive threshold
  comparison before upload. Both retain the original negative findings.
- Independent chronological evaluation on sealed April-December 2013, robust
  interval/alarm calibration and spatial grouping remain future work. No new
  localization curve is claimed because continuous group/household scores were
  not preserved sufficiently for that analysis.
- The official workshop page retains the 10-page limit and currently lists
  November 22, 2026 for camera-ready submission. Generic camera-ready instructions
  could not be refreshed; authors must complete their required submission checks.

No commits, pushes, submission, registration or organizer contact were performed.
The pod was not accessed, changed or terminated by this revision.

## Source-package addition, November 11, 2026

Added `regional_twin_study_source.zip`, containing the clean source/PDF, bibliography,
IEEE template, required tables, PDF/SVG figures and standalone build instructions.
An extracted copy rebuilt successfully to ten pages with identical extracted text.
The manuscript and both previously delivered PDFs are unchanged. No commit or push
was performed.
