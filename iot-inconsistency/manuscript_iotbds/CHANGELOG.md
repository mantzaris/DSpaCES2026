# Conversion changes — 10 November 2026

The authoritative source is the current local graph-flow `paper/main.tex`.
No substantive prose was shortened. Title, abstract, section organization,
scientific meaning, equations, results, comparisons and limitations are retained.
The frozen baseline includes the original wording and errors. Every editorial
change appears in `review/paper_diff.pdf` and `review/baseline-to-final.diff`.

## Editorial corrections

| Location | Original → corrected | Reason |
|---|---|---|
| §4.2, measurement units | `a non-diagonal affine transformations` → `non-diagonal affine transformations` | Article/plural agreement. |
| §5.1, dataset configurations | `and a 64 channel nonlinear configurations` → `and 64 channel nonlinear configurations` | Article/plural agreement. |
| §6.2, SKAB repairs | `123 accepted repairs has` → `123 accepted repairs have` | Subject/verb agreement; counts and failures unchanged. |
| §6.3, ensemble ablation | `member log ratios is averaged` → `member log ratios are averaged` | Subject/verb agreement. |
| §6.3, association alarms | `Cross type counts are saved reading alarms` → `Cross type counts are saved; reading alarms` | Missing clause separator; caution preserved. |
| Table 6 caption | `primary-target top k-one rates` → `primary-target top-one rates` | Repair malformed terminology consistently with the existing endpoint. |
| AI disclosure | `software, and grammar checking` → `software and grammar checking` | Remove stray comma. |
| AI disclosure | `The authors takes responsibility` → `The authors take responsibility` | Subject/verb agreement; original responsibility statement retained. |

No new scientific claims, citations, experiments or results were introduced.
Awkward but ambiguous phrases such as “proposing service” and “support human
views” remain; their intended meanings were not inferred.

## Formatting

- IEEE class/front matter/keyword environment become official Springer LNCS
  equivalents. Current template fonts and prescribed `splncs04` style are used.
  Class files, margins, body fonts and line spacing are not modified.
- All **19 embedded bibliography records** were transcribed to BibTeX from
  `main.tex`, preserving citation keys and bibliographic information. The
  separate original `.bib` files and generated fragments were not used as
  content authorities. Record mappings and token checks remain in
  `internal/content-review/`.
- Preserve **E1–E12**, including existing `(E2)`, `(E5)` and `(E6)` references.
  Allow ordinary line breaks after commas in the inline sampling-budget set;
  its values and mathematical meaning are unchanged.
- Replace two-column floats with ordinary Springer floats. Wrap the long
  method-name table column; split the confidence table into two metric panels
  with repeated existing configuration labels. All **232 keyed data values**
  remain unchanged.
- Retain six original figure PDFs byte-for-byte. Rearrange cropped vector
  panels and shared legends upright. Confidence and equation/cost figures each
  continue onto a second page with the same figure number; each continuation
  adds only the mechanical caption word `Continued.`. No panel, curve, value,
  axis label or legend is removed. These changes are applied equally to the
  baseline and final layout and are described explicitly in the diff appendix.

## Anonymity

- Replace both named author/affiliation/email blocks with `Anonymous Author(s)`
  and an empty institute; clear PDF author metadata and omit author running heads.
- Related Work: `Our earlier procedure tested repairs` →
  `The earlier procedure tested repairs`, retaining the predecessor comparison
  without declaring authorship. No legitimate reference was deleted.
- Rename `Acknowledgment` to `AI disclosure`. There was no named funding or
  identifying acknowledgment prose beyond the front matter.
- Exact identity restoration details are in `review/RESTORATION.txt`, excluded
  from the submission-only bundle. Original public files and visibility are unchanged.

## Disclosure

Preserve the recorded Codex software-development/grammar assistance and the
authors' existing responsibility statement, with the two grammar fixes above.
Add a footnote attribution to **OpenAI, Codex**,
`https://openai.com/codex/` (accessed November 10, 2026), and this sentence:

> It also assisted with the present manuscript's LaTeX conversion, anonymization and proofreading.

This records work performed during this conversion. No model version, prior
AI-generated section or new human-verification claim is invented. The heading,
footnote and added sentence are visible in the diff. See the conversion report
for disclosure-placement and historical-section uncertainties.
