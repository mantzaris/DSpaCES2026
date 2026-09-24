# Editorial revision: From Detail to Decisions in Regional Energy Twins

September 24, 2026. The revised [manuscript PDF](../manuscript/regional_twin_study.pdf)
is **10 pages including references**, in unmodified IEEEtran conference format.
It is a polished author-review draft, not a guarantee of acceptance or a submitted
paper. The revision starts from clean `main` at `b2fb7ac`; previous reports,
experiments and negative results remain intact.

## Argument and title

The preferred title replaces the open question with the paper's affirmative
argument: controlled comparisons locate where detail obtains value and where
that value is lost between observations and decisions. The abstract is 228 words.
The introduction states three contributions with their results and practical use:

- **Controlled attribution.** Matched evidence preserves registered queries;
  the 61.12-to-21.60 MB retained-state saving disappears against streamed fine
  inference. Designers should compare storage strategies and restoration costs.
- **Information value across scales.** Additional fine readings improve local
  forecasts, while aggregate visibility and localization remain separate. The
  18.2839428% original-panel MAE reduction is explicitly a full-access comparison
  at a larger observation budget, not matched-budget superiority.
- **Execution-level diagnosis.** The original acquisition gate blocks responsive
  scores. The one correction changes some requests, but adds no affected meter
  identity inside the detection window; fine alarm thresholds remain a barrier.
  The evidence identifies a concrete allocation/timing problem without claiming
  a superior adaptive method.

Results use finding-led RQ headings. The first-origin macro-to-micro example
explains why exposing detail preserves predictions while newly acquired data
change even an unopened group's conditional prediction. This is statistical
information propagation, not causal demand propagation. The discussion gives
five design checks tied to the measurements: streaming comparators, explicit
access interfaces, separate allocation and alarming, information arrival before
the decision deadline, and calibration separate from numerical consistency.
The conclusion now states what the controlled evaluation delivers.

## Presentation and evidence preservation

All four figures and both principal tables remain. Figure 1 was rebuilt with
wrapped labels, internal padding checked against rendered text bounds, and
separate request, probe and conditional-storage arrows. Figure 2's legend no
longer covers the post-event score peak. Method codes have descriptive labels
in tables and plots; captions explain the finding and define the original and
corrective panels. All 32 B and 16 C paired points remain. Figure 4's diagnostic
counts and margin comparisons are unchanged.

The standard `balance` package balances the final columns. IEEE fonts, margins,
column widths and line spacing are unchanged. Redundant positioning and repeated
qualification were condensed to retain ten pages; no essential evidence was
moved into supplementary material. The first layout attempt exceeded the page
limit and was corrected by editing prose, not compressing the template.

The [existing claim map](REGIONAL_TWIN_CLAIM_EVIDENCE.md) was updated in place.
The [editorial validation](../results/editorial/validation.json) verifies ten
scientific summary/diagnostic outputs against the synthesis commit (decompressed
content for gzip). Model code, frozen configurations, bibliography and IEEE class
are unchanged. The saved macro-to-micro trace and all-method zero-of-16 exact
cancellation finding now have explicit build assertions. No new results replace
previous findings. Different B/C MAEs remain separate exploratory panels.

Visible limitations include the streamed-memory equality, no M3b advantage,
zero original exact-cancellation localization even under full access, deficient
interval/alarm calibration, few reused development backgrounds, synthetic
interventions and provider groups, and archive volume distinct from inference
dimension. No GPU speedup, live deployment or new inference theorem is claimed.

## Validation and reproduction

The [official workshop page](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home)
was refreshed on September 24: case studies remain welcome, the full-paper cap
is ten pages including references, and IEEE two-column formatting remains
required. The [venue note](../manuscript/VENUE_AND_SOURCES.md) records the refresh.

Use the [documented clean build](../manuscript/README.md). It regenerates the
figures, table, derived effect-size macro and PDF from saved outputs only.
The successful final clean build passes reference/citation, overfull-box,
font-embedding, author, page-count and figure-padding checks. The evidence check
passes without changing any experimental output. All ten final pages and the
standalone Figure 1 were visually inspected; the exact PDF hash and page-specific
findings are in [visual_review.json](../results/synthesis/visual_review.json).
The remaining TeX messages are ordinary underfull boxes; no missing citation,
overfull box, balance warning, clipped graphic or unreadable label was found.
No new model tests are warranted because inference and policy code are unchanged.

Local analysis/build retries are charged in the separate
[editorial ledger](../results/editorial/resource_ledger.json), inheriting the
closed synthesis CPU total. The first padding assertion and first page-limit
check failed, were fixed, and remain recorded. No GPU experiment, fitting,
threshold search, raw-meter read or sealed-outcome access occurred. The original
main study remains disabled. GPU allowance is unchanged at **11.2337115 minutes**.
No pod command or lifecycle action was performed; its last verified state was
allocated and idle, with billing continuing separately. No experiment was started.

## Remaining author decisions

Review the strength of this comparative case-study contribution for DSpaCES,
the stated exploratory scope, and the operational meaning of the detection
window and information interface. Presentation/no-show requirements and any
fee waiver remain author-controlled venue checks before submission. The author
block is the supplied Alexander V. Mantzaris / UCF metadata. Neither acceptance
nor a novel general algorithm is asserted. No submission or organizer contact
occurred.

## Closed accounting and local artifacts

Measured local build/audit jobs, including retries, took 40.096
seconds. A conservative 180-second allowance covers ancillary helpers, rendering,
packaging and git handoff. Total additional supporting charge is
3.668260 minutes; cumulative CPU charge is
98.394210 of 360 minutes. GPU charge is zero. The
[closed handoff](../results/editorial/resource_handoff.json) records exact totals.

A separate hash-verified local copy is
`data/regional/manuscript/regional_twin_editorial.pdf`; the reproducible artifact
archive is `data/regional/manuscript/regional_twin_editorial.zip`. Its contents
and hashes are recorded in `manifests/regional_editorial_durable.json`. The previous
synthesis archive/PDF copy is preserved. The revision's containing commit identifies
the final source; the last GPU-tested source remains `18fe4af`.
