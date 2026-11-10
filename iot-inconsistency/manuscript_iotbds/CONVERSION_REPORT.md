# IoTBDS 2027 Regular Paper conversion

Prepared locally on **10 November 2026**. The clean anonymous manuscript is
**`paper.pdf`: 22 pages, approximately 38,103 non-whitespace characters**.
It retains the current graph-conditioned normalizing-flow research and title.
**No substantive prose was shortened.** Only clear language errors, anonymity
and supported disclosure details were changed. See [CHANGELOG.md](CHANGELOG.md)
for every edit and [BUILD.md](BUILD.md) for reproducible commands.

## Official requirements and template

The current official pages were retrieved again on 2026-11-10:

- [Guidelines](https://iotbds.scitevents.org/Guidelines.aspx): double-blind
  anonymous review; initial **Regular Papers require 10,000–50,000 characters
  excluding whitespace**, including references, tables, graphs and appendices.
  After acceptance, Full Papers have **25 proceedings pages**, Short Papers
  **20**. These publication allowances are distinct from initial character
  limits. This is completed research prepared as a Regular Paper, not a
  position paper. No ten-page IEEE or automatic twenty-page limit was applied.
- [Templates](https://iotbds.scitevents.org/Templates.aspx): links to Springer
  computer-science proceedings formatting, applicable to CCIS.
- [AI Tools](https://iotbds.scitevents.org/AiTools.aspx): identify the tool and
  assisted parts; preserve author responsibility. Disclosure-placement and
  historical-section uncertainties are discussed below.
- [Call for Papers](https://iotbds.scitevents.org/CallForPapers.aspx) independently
  confirms the Regular Paper and double-blind requirements.

The conference's [Springer link](https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines)
redirects to [Information for authors and editors](https://link.springer.com/series/558/information-for-authors-and-editors),
which explicitly covers CCIS. Its actual [LaTeX archive](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27851904/data/LaTeX2e%20Proceedings%20Template%20ZIP)
and [author instructions](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27852130/data/Instructions%20for%20Authors%20PDF)
were freshly downloaded and inspected. The archive SHA-256 is
`42afb32ed4fadc9e209134ec65dab1bd2a7ead42f9a3f8abb184f250c4a197b9`.

The supplied **`llncs.cls` v2.25, 2026-09-03**, and prescribed
**`splncs04.bst`** are unchanged. Current sample fonts are T1 `newtxtext` and
`newtxmath[varvw]`; native class dimensions remain 122 × 193 mm. The abstract
is unchanged at 175 whitespace-delimited words, within the sample's 150–250
guidance. No invented publication identifiers or branding were added.
Fresh resources match the previously verified entropy template bytes; only
formatting/audit infrastructure was reused, never that paper's research.
Exact URLs, access timestamps and hashes are in
[internal/official/retrievals.json](internal/official/retrievals.json).

## Authoritative source and preservation

Source: **`iot-inconsistency/paper/main.tex`**, titled *Evaluating
Graph-Conditioned Generative AI for IoT Sensor Fault Detection and Repair*.
Repository revision: **`c029b38e579ba5e743a51c6a5c5136aff6e2b84f`**, branch
`main`. Initial Git status contained only the pre-existing untracked
`iot-entropy/manuscript_iotbds/`; the new destination did not exist. No
applicable `AGENTS.md` was found. Relevant README and `paper/BUILD.md` were read.

The current local TeX, including its 23 numerical macros, tables and embedded
19-entry bibliography, was authoritative. Source SHA-256:
`8182cf934a8b138ef00906902071567bd7066612690d6da2e9b8ab5205b07722`.
Its only external content dependencies are the six graph-flow PDFs:
architecture, performance, confidence, repair, equations and network.
No generated fragments, inactive `.bib` files or legacy manuscript were
substituted. No source generator or experiment was run.

[source-baseline.json](internal/provenance/source-baseline.json) and
[source-files.sha256](internal/provenance/source-files.sha256) identify all
**72 original-paper files**. The current source is frozen internally.
Final checks verify the original directory and **2,476 protected repository
and entropy-submission files** unchanged. Independent semantic checks preserve
**23 macros, 232 keyed table values, E1–E12, all three explicit E2/E5/E6
references, and all 19 bibliographic records**. Citation identities and order
in the source remain; Springer sorting changes displayed reference numbers.
Bibliography field mapping and token verification are retained in
`internal/content-review/`.

The original-wording, identified baseline is
`review/baseline/main_baseline.tex` and `review/baseline/paper_baseline.pdf`.
It was built and measured before editorial changes. The title, abstract,
organization, methods, findings and qualifications remain: detection is not
calibration or repair quality; the smaller gain misses the practical margin;
Gaussian-model benefits remain inconclusive; supervised methods are stronger;
repair failures, missing targets and reused recordings remain explicit.
Predictive graph associations are not recast as causality, and likelihood
ratios are not recast as physical-failure probabilities. The source-only audit
found no clear scientific error requiring intervention; this is not a new
experimental validation.

## Length and presentation

| Stage | Pages | Estimated rendered non-whitespace characters |
|---|---:|---:|
| First format-only baseline, before readable panel rearrangement | 18 | 38,126 |
| Original wording in the final upright layout | 22 | 38,158 |
| Final anonymous submission | **22** | **38,103** |

The first baseline already met the character limit, so no length reduction
was attempted. An initial `pdftotext -layout` count was 38,130; the table uses
the standardized PyMuPDF/figure-adjusted audit for comparable before/after
values. Final conservative full-PDF counts are **44,508** (Poppler) and
**44,503** (PyMuPDF); both independently remain below 50,000.

Run `python3 internal/audit_pdf.py`. It extracts rendered text, normalizes
Unicode with NFKC, and counts non-whitespace code points—not LaTeX commands
or comments. References, tables, captions, disclosure/footnote and all figure
labels are included. Cropped PDF reuse retains invisible duplicate text in
extraction, so the rendered estimate is:

**44,503 − 9,123 extracted figure-font characters + 2,723 original figure
characters counted once = 38,103.**

The figure fonts are distinct from manuscript fonts. All source text spans
are covered once by the visible panel plan; plots and legends were also
visually checked. All six assets contain extractable vector text and no
embedded raster images. Mathematical glyph mappings, ligatures, superscripts,
line-break hyphens and extraction order can still affect counts. These are
reproducible estimates, **not conference-certified measurements**. Raw and
adjusted counts, extraction texts and limitations are in
[audit.json](internal/validation/audit.json).

All figures remain upright. Dense panels continue onto additional pages
without dropping evidence; minimum measured figure lettering is **6.16 pt**.
Tables use editable cells and the original supported small-table font.
The class, margins and line spacing were not modified. The sole initial
overfull inline sampling-budget set was fixed with ordinary allowed breaks;
its mathematical content is unchanged.

## Builds, diff and visual inspection

Final, baseline and diff compile successfully with pdfLaTeX/BibTeX/latexmk.
All citations and references resolve. No missing files/glyphs, placeholders,
overfull boxes or material layout warnings remain. The installed TeX stack
reports an unused `\vec` redefinition warning and benign underfull-page boxes;
visual inspection found no defect. All fonts are embedded; no Type 3 fonts
are used. The submission-only ZIP was extracted and rebuilt independently.

Every final page was rendered and visually inspected, including equations,
labels, continued figures, legends, tables and references. No clipping,
overlap, missing panels or floats after the bibliography were found. The
**23-page `review/paper_diff.pdf`** visibly marks all editorial and disclosure
changes, and contains a before/after appendix for identities and metadata.
Its first page is labeled **internal review—do not submit**. All diff pages
were rendered: 15 match final-page pixels; all eight differing/appendix pages
were explicitly inspected. A local word-space stretch in the internal diff's
marked disclosure prevents underline-induced overflow; the submission layout
is unaffected.

Comparison evidence includes `review/latexdiff-raw.tex`,
`review/paper_diff.tex`, `review/baseline-to-final.diff`,
`review/source-original-to-final.diff`, and the preserved baseline.
The baseline normalizes only mechanical template/table/figure/reference-style
differences. Repeated table labels and two `Continued.` caption words are
documented explicitly, so no editorial changes are concealed in conversion.

## Anonymity, disclosure and remaining issues

The visible PDF and its author/XMP metadata, bookmarks, links, annotations,
attachments and figures were checked. Author metadata is blank; no identifying
author details, personal links, author running heads, non-link annotations,
attachments, forms or JavaScript remain. The source's public SKAB dataset
repository is a necessary dataset citation, not a personal project link.
Restoration information is separated in `review/RESTORATION.txt`.

The nonidentifying AI disclosure preserves recorded software-development and
grammar assistance, corrects its grammar, adds the known current conversion,
anonymization and proofreading work, and attributes the official
[OpenAI Codex tool](https://openai.com/codex/) in a footnote. No model version
or new human-verification claim is invented. The tool page was readable through
the web tool; direct archival downloading returned 403, documented separately.

Two matters remain for author judgment before submission:

1. **Existing public version:** the conference bars new public posting during
   review but does not explicitly resolve copies already public. PDF anonymity
   does not remove discoverability. Repository visibility and public originals
   were left unchanged.
2. **Historical AI-generated text:** the source establishes software/grammar
   assistance, but does not identify any prior substantively generated sections.
   Confirm whether additional section-level AI citations are applicable.
   `AI disclosure` placement reconciles the AI page's allowance for an
   appropriate section with removal of acknowledgments; it is not organizer-
   confirmed. The current tool attribution and preparation roles are explicit.

For eventual publication, supply a factual competing-interests declaration
and complete any requested accessibility descriptions; neither was fabricated.
No submission, organizer contact, experiment, commit, push or branch change
occurred. `submission/` and `submission_source.zip` exclude all identified
review artifacts, baselines, logs and restoration notes.
