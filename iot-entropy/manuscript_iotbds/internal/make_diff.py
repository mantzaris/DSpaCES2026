#!/usr/bin/env python3
"""Run latexdiff on equal-layout sources; render front matter in an appendix."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
raw = subprocess.check_output([
    'latexdiff', '--type=UNDERLINE', '--graphics-markup=none',
    'internal/baseline/paper_baseline.tex', 'paper.tex'], cwd=root, text=True)
diffdir = root / 'internal/diff'
diffdir.mkdir(exist_ok=True)
(diffdir / 'latexdiff-raw.tex').write_text(raw)
start, end = raw.index('\\author{'), raw.index('\\hypersetup{')
raw = raw[:start] + r'''% Front-matter changes are shown in the explicit comparison appendix.
\author{Anonymous Author(s)}
\institute{}

''' + raw[end:]
appendix = r'''
\clearpage
\section*{Internal review: front-matter comparison}
This is an internal comparison artifact, not the submission PDF.
Red struck-out text denotes removals; blue underlined text denotes additions.
The comparison baseline preserves the original wording in the same Springer
layout as the anonymous manuscript. Mechanical class, keyword, table-panel,
figure-placement and bibliography-style changes are normalized equally.
The title, equations, numerical results, captions, bibliographic records and
AI-disclosure body are unchanged. Four user-requested language corrections and
one added abstract sentence summarizing the existing overall finding are marked
in place, together with the disclosure heading change.

\subsection*{Author and affiliation text: before}
\noindent\DIFdel{Alexander V. Mantzaris}\par
\noindent\DIFdel{School of Data, Mathematical, and Statistical Sciences}\par
\noindent\DIFdel{University of Central Florida}\par
\noindent\DIFdel{Orlando, FL, USA}\par
\noindent\DIFdel{Alexander.Mantzaris@ucf.edu}\par
\medskip
\noindent\DIFdel{James H. Korris}\par
\noindent\DIFdel{Creative Technologies Inc.}\par
\noindent\DIFdel{Hollywood, CA, USA}\par
\noindent\DIFdel{james.korris@cretecinc.com}\par

\subsection*{Author and affiliation text: after}
\noindent\DIFadd{Anonymous Author(s)}\par
The institute field is empty. No affiliations, emails, ORCIDs or author
running heads appear in the submission PDF.

\subsection*{PDF author metadata}
Before: \DIFdel{Alexander V. Mantzaris and James H. Korris}\par
After: empty.

\subsection*{Required anonymity and editorial changes}
Author identity and PDF author metadata are suppressed for double-blind review.
The heading ``Acknowledgment and AI disclosure'' becomes ``AI disclosure''
to retain the required disclosure outside acknowledgments. The requested
language corrections repair ``clusting'', ``findings set'', ``make recall
nonmonotonically'', and the computation-time sentence. The added abstract
sentence reports limited incremental benefit from entropy and no consistent
overall entropy or diffusion advantage. No length-related editing was needed.
'''
raw = raw.replace('\\end{document}', appendix + '\n\\end{document}\n')
(root / 'paper_diff.tex').write_text(raw)
print('Generated paper_diff.tex; raw latexdiff retained in internal/diff/')
