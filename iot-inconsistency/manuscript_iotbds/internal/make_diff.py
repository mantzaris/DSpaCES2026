#!/usr/bin/env python3
"""Preserve equal-layout original wording; mark edits with latexdiff."""
from pathlib import Path
import difflib
import subprocess

ROOT = Path(__file__).resolve().parents[1]
baseline = ROOT / 'review/baseline/main_baseline.tex'
final = ROOT / 'main.tex'
raw = subprocess.check_output([
    'latexdiff', '--type=UNDERLINE', '--graphics-markup=none',
    'review/baseline/main_baseline.tex', 'main.tex'], cwd=ROOT, text=True)
(ROOT / 'review/latexdiff-raw.tex').write_text(raw)
original_diff = raw
start, end = raw.index('\\author{'), raw.index('\\begin{document}')
# Author/institute commands do not reliably mark email macros. Show every
# deleted word explicitly in the appendix; use a visible internal-only label.
raw = raw[:start] + r'''% Front matter is compared in the explicit appendix.
\author{Anonymous Author(s)}
\institute{Internal review artifact --- do not submit}
''' + raw[end:]
# latexdiff's macro definitions precede \begin{document}; preserve that preamble.
preamble = original_diff
extension_start = preamble.index('%DIF PREAMBLE EXTENSION ADDED BY LATEXDIFF')
extension_end = preamble.index('%DIF END PREAMBLE EXTENSION ADDED BY LATEXDIFF')
extension_end = preamble.index('\n', extension_end)
raw = raw.replace(r'\begin{document}', preamble[extension_start:extension_end] + '\n\\begin{document}', 1)
# Strikeout/underline markup can prevent ordinary paragraph fitting. Permit
# emergency word-space stretch only in the internal disclosure comparison.
disclosure_start = raw.index(r'OpenAI Codex\DIFaddbegin')
disclosure_end = raw.index('\n', disclosure_start)
raw = (raw[:disclosure_start] + '\\begingroup\\emergencystretch=2em\n'
       + raw[disclosure_start:disclosure_end] + '\\par\\endgroup'
       + raw[disclosure_end:])
appendix = r'''
\clearpage
\section*{Internal review: front matter and comparison scope}
This is an internal review artifact. Do not upload it as the conference manuscript.
Red struck-out text marks deletions; blue underlined text marks additions.
The comparison baseline retains the original substantive wording, including
errors, in the same Springer layout as the final manuscript.
The title, equations, numerical macros, results and reference records are
unchanged. All localized proofreading and disclosure edits are marked in place.
No substantive prose was shortened for length.

\subsection*{Author and affiliation text: before}
\noindent\DIFdel{Alexander V. Mantzaris}\par
\noindent\DIFdel{School of Data, Mathematical and Statistical Sciences}\par
\noindent\DIFdel{University of Central Florida}\par
\noindent\DIFdel{Orlando, FL, USA}\par
\noindent\DIFdel{alexander.mantzaris@ucf.edu}\par
\medskip
\noindent\DIFdel{James H. Korris}\par
\noindent\DIFdel{Creative Technologies Inc.}\par
\noindent\DIFdel{Hollywood, CA, USA}\par
\noindent\DIFdel{james.korris@cretecinc.com}\par

\subsection*{Author and affiliation text: after}
\noindent\DIFadd{Anonymous Author(s)}\par
The submission institute field is empty. The internal-review warning on the
first page belongs only to this diff, not to the submission.

\subsection*{PDF author metadata}
Before: \DIFdel{Alexander V. Mantzaris and James H. Korris}\par
After: empty.

\subsection*{Mechanical changes normalized in the comparison}
Both versions use the official Springer class, fonts, keywords and bibliography
style. All 19 embedded bibliographic records were transcribed to BibTeX without
changing their citation identities or information; their author/title/venue/date/
page/DOI/URL mapping is preserved in the review evidence.
The confidence table repeats its existing configuration heading and row labels
in two metric panels. Figure panels and shared legends are rearranged upright;
two continuation captions add only ``Continued.'' to the original captions.
These presentation changes occur equally in both compared sources and do not
remove scientific material. The E-prefixed equation numbering is retained.
'''
raw = raw.replace(r'\end{document}', appendix + '\n\\end{document}\n')
(ROOT / 'review/paper_diff.tex').write_text(raw)
for filename, old, oldname in [
        ('baseline-to-final.diff', baseline.read_text(), 'original-wording-springer-baseline'),
        ('source-original-to-final.diff', (ROOT / 'internal/provenance/original-main.tex').read_text(), 'original-local-flow-manuscript')]:
    value = ''.join(difflib.unified_diff(old.splitlines(True), final.read_text().splitlines(True),
                                       fromfile=oldname, tofile='anonymous-main.tex'))
    (ROOT / 'review' / filename).write_text(value)
print('Generated review/paper_diff.tex and two plain-text comparisons.')
