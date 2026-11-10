# IoTBDS 2027 anonymous Regular Paper conversion

Prepared locally on **10 November 2026**. The completed-research manuscript is **21 pages**, with an estimated **42,172 non-whitespace characters** including references, tables, captions and figure text. Following author review, four requested language corrections and one requested sentence summarizing the existing overall finding were applied. No length-driven shortening was needed. The submission PDF is `paper.pdf`; `paper_diff.pdf` is an identified **internal review artifact**, not a submission file.

## Requirements and official template

All four official conference pages and the linked Springer resources were retrieved successfully on 2026-11-10. Archived responses, exact retrieval times, redirects and SHA-256 hashes are in [internal/official/retrievals.json](internal/official/retrievals.json); detailed findings are in [internal/official/REQUIREMENTS.md](internal/official/REQUIREMENTS.md).

| Official source | Applicable requirement |
|---|---|
| [Guidelines](https://iotbds.scitevents.org/Guidelines.aspx) | Double-blind review. Initial **Regular Paper: 10,000–50,000 characters excluding whitespace**, including references, tables, graphs and appendices. |
| [Call for Papers](https://iotbds.scitevents.org/CallForPapers.aspx) | Regular Papers represent completed, validated research. This conversion is not an abstract or position paper. |
| [Guidelines](https://iotbds.scitevents.org/Guidelines.aspx) | **After acceptance:** Full Papers have 25 proceedings pages; Short Papers have 20. These are distinct from initial character limits. The intended full-paper target is met; no short-paper or generic IEEE ten-page limit was imposed. |
| [Templates](https://iotbds.scitevents.org/Templates.aspx) | Links to Springer's computer-science proceedings templates, applicable to CCIS. |
| [AI Tools](https://iotbds.scitevents.org/AiTools.aspx) | Disclose named tools and affected parts; human authors remain accountable. Disclosure/anonymity ambiguities are recorded below. |

The conference's [Springer link](https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines) redirected to [Information for authors and editors](https://link.springer.com/series/558/information-for-authors-and-editors), which explicitly includes CCIS. Its actual [LaTeX archive](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27851904/data/LaTeX2e%20Proceedings%20Template%20ZIP) and [author instructions](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27852130/data/Instructions%20for%20Authors%20PDF) were downloaded and inspected.

The supplied **`llncs.cls` v2.25 (2026-09-03)** and **`splncs04.bst`** are copied without alteration. The archive SHA-256 is `42afb32ed4fadc9e209134ec65dab1bd2a7ead42f9a3f8abb184f250c4a197b9`. The class documentation and sample explicitly prescribe `splncs04`; the separate instructions call the broader style MathPhySci. The current sample's T1 encoding, `newtxtext` and `newtxmath[varvw]` are used. Default class dimensions, font sizes and line spacing are retained. The revised abstract has 176 whitespace-delimited words, within the sample's 150–250 guidance. No publication identifiers, copyright or acceptance claims were added.

## Authoritative local baseline

- Repository revision: **`c029b38e579ba5e743a51c6a5c5136aff6e2b84f`**, branch `main`.
- Initial working tree: **clean**, including untracked-file checks. No applicable `AGENTS.md` was found in repository or ancestor directories. The destination did not previously exist.
- Input: current local `iot-entropy/manuscript/paper.tex`, not a remote revision or the existing PDF. Relevant root/project README and source vendor instructions were read.
- Entry point: `paper.tex`, all prose and tables inline; no generated `.tex` dependencies. Assets: `references.bib` and `figures-v2/{architecture,theory,performance,traces,availability,dashboard_cost}.pdf`.
- Source TeX SHA-256: `c5a56fc28689dfd484fd97357dbef48ec8d53d0a4cbc6134f1db0705bf221515`. Bibliography: `08dd7d3a6471fa6f1512ce2a1ea227a5b1d736dc9692be36bb2ba57e21de11fc`.

[source-baseline.json](internal/provenance/source-baseline.json) and [source-files.sha256](internal/provenance/source-files.sha256) inventory **every original manuscript file**, including all asset hashes. Frozen source and bibliography snapshots are retained internally. The final preservation check confirms the same paths and hashes: **the original directory is unchanged**. No other paper, experiment code, dataset or reported result was modified; no experiments were run.

## Changes and comparison

Every human-readable editorial change is listed here:

| Location | Before → after | Reason |
|---|---|---|
| Original lines 12–28; final line 12 | Named author/affiliation/email block → `Anonymous Author(s)`, empty institute | Required double-blind anonymity; exact deleted information is in the diff appendix and internal restoration note. |
| Original line 32; final line 17 | Identified PDF author → empty | Metadata anonymity. |
| Original line 857; final line 890 | `Acknowledgment and AI disclosure` → `AI disclosure` | Retain required nonidentifying disclosure outside acknowledgments. The disclosure body is verbatim. |
| Introduction, final line 40 (page 1) | `homogeneous clusting` → `homogeneous clustering` | User-requested spelling correction. |
| Abstract, final line 25 (page 1) | `The findings set complementary measurement capabilities` → `The findings characterize complementary measurement capabilities` | User-requested language correction. |
| Alert evaluation, final line 515 (page 10) | `make recall nonmonotonically` → `make recall nonmonotonic` | User-requested grammatical correction. |
| Alert evaluation, final line 516 (page 10) | `Computation time is measured as a different source` → `Computation time is reported separately` | User-requested clarification; the distinction from detection delay is preserved. |
| Abstract, after the missing-data sentence (page 1) | Added: “Adding entropy to conventional features yields limited incremental benefit, and neither entropy nor the evaluated diffusion reference provides a consistent overall advantage.” | User-requested balanced summary of the existing overall finding; no new result or evidence. |

There are **no length-related edits**. Apart from the five explicitly requested edits above, all wording is unchanged. Title, research questions, conclusions, equations, numerical results, uncertainty intervals, qualifications, limitations and captions are preserved. Necessary self-citations already use third-person wording and remain. All 20 bibliography records are byte-identical; all 19 cited works render, and the pre-existing unused record remains in the `.bib`.

Mechanical changes: IEEE front matter/keywords/bibliography become native Springer constructs; LNCS supplies proposition/proof environments. The original negative equation-row spacing is removed. Wide tables are reflowed into stacked dataset/metric panels with repeated existing headings and row labels; all **168 numerical cells and associations** are verified. Two wide figure grids rotate; trace/dashboard panels are rearranged through vector-preserving viewports. Every original panel, label and legend remains visible; six asset files remain byte-identical. Minimum measured final figure lettering is **6.10 pt**. No class modifications, compressed margins, tiny fonts or hidden essential evidence were used.

`internal/baseline/paper_baseline.tex` preserves original wording and identities with the same mechanical Springer layout. `build_review.sh` runs `latexdiff`, retains its raw output, and produces the **22-page** `paper_diff.pdf`. All five user-requested editorial changes and the disclosure-heading deletion are marked in place; an explicit before/after appendix marks every suppressed identity, email and metadata value. The baseline retains the original wording, including the corrected phrases and the original abstract; no editorial changes are hidden in it. The exact revision instructions are recorded in `internal/editorial-changes.json`, and pre-revision outputs are archived under `internal/revisions/language-and-abstract/before/`. Baseline, diff source and regeneration commands are retained; see [README.txt](README.txt). Original-to-final semantic verification is reproducible with `python3 internal/preservation/verify.py`.

## Length, build and visual validation

The first prose-preserving Springer build measured **19 pages / 42,019 characters**, before enlarging figure layouts; shortening was therefore unnecessary. Final measurement:

| Method | Non-whitespace characters |
|---|---:|
| Poppler full-PDF extraction, NFKC normalized | 42,715 |
| Independent PyMuPDF extraction, NFKC normalized | 42,730 |
| Figure-adjusted rendered estimate | **42,172** |

Run `python3 internal/audit_pdf.py`. It counts extracted Unicode characters, not raw LaTeX or comments. The adjusted estimate is **42,730 − 2,406 extracted figure-font characters + 1,848 original figure characters counted once**. Repeated clipped-PDF inclusions retain some invisible text objects; the correction prevents counting these twice. Distinct figure fonts, geometry checks and visual panel inspection support this correction. Both raw conservative totals also satisfy the limit with over 7,200 characters of headroom.

These are reproducible estimates, **not conference-certified counts**. Mathematical glyph mappings, accents, subscripts, line-break hyphens and ligatures can affect extraction; NFKC expands compatibility ligatures. Figure text was independently extracted and visually checked, not assumed complete. The only raster component is a text-free color gradient. Evidence and limitations are in [audit.json](internal/validation/audit.json).

Final, baseline and diff compile successfully with pdfLaTeX/BibTeX through latexmk. The submission-only ZIP was extracted and rebuilt independently, with no access needed to the original manuscript. All citations/cross-references resolve; no missing graphics, placeholders or overfull boxes remain. The installed TeX stack reports an unused `\vec` redefinition warning and benign underfull-page boxes; visual inspection found no resulting defect. Fonts are embedded, with no Type 3 fonts.

Every final page was rendered and visually inspected during conversion; rotated grids were also inspected upright. After the editorial revision, all 21 final and 22 diff pages were rendered again. Changed final pages 1, 2 and 10 and changed diff pages 1, 2, 10 and 22 were visually re-inspected. Every other page is pixel-identical to its previously reviewed version. The requested additions/deletions are readable; no clipping, overlap, missing panels or floats after references were found. Revision evidence is in `internal/revisions/language-and-abstract/render-comparison.json`; visual notes remain under `internal/`.

## Anonymity and matters requiring author attention

Visible content, PDF author/XMP metadata, bookmarks, annotations, hyperlinks and attachments were checked. Author metadata is blank; no identifying body text, personal repository URLs, ORCIDs, author running heads, embedded attachments, forms, JavaScript or non-link annotations remain. The two bibliography surname matches are necessary third-person citations. [internal/RESTORATION.txt](internal/RESTORATION.txt) preserves camera-ready restoration information and is excluded from the submission bundle.

1. **Pre-existing public copy:** the conference prohibits new public posting during review but does not explicitly resolve already-public versions. The repository's discoverability remains separate from PDF anonymity. Visibility and original files were left untouched; nothing new was published.
2. **AI disclosure specificity:** the original nonidentifying OpenAI Codex disclosure is preserved. The policy asks for affected parts, and Guidelines asks for citations in AI-generated-text sections. The source does not identify those exact sections or model/version. The authors must confirm actual affected sections before submission; no facts or citations were invented. Separate `AI disclosure` placement reconciles the acknowledgment-removal rule with the AI page's allowance for an appropriate section, but is not organizer-confirmed.
3. **Publication requirements:** a factual competing-interests declaration is required by Springer; none was invented. Supply it for camera-ready preparation, or earlier if the submission form requests it. Figure accessibility descriptions can also be completed through the publisher's documented publication process.

## Deliverables

`paper.tex`, `paper.pdf`, local class/style/bibliography/figures, `paper_diff.tex`, `paper_diff.pdf`, this report, `build.sh`, `build_review.sh`, and `README.txt` are in this directory. `submission/` and `submission_source.zip` contain only the anonymous PDF/source, six figure assets, class/style, bibliography/BBL and build instructions. Internal baselines, identified review artifacts, restoration notes, logs and tools are excluded. No submission, contact with organizers, commit, push or branch change occurred.
