#!/usr/bin/env python3
"""Mechanical Springer conversion from the frozen current LOCAL flow paper.

Baseline wording stays original. --final additionally applies the separately
recorded editorial and review-anonymity changes only to main.tex.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'internal/provenance/original-main.tex').read_text()
text = source.replace(r'\documentclass[conference]{IEEEtran}', r'\documentclass{llncs}')
text = text.replace(r'\usepackage{amsmath,amssymb,booktabs,graphicx,microtype,url,xcolor}',
                    '\\usepackage[T1]{fontenc}\n\\usepackage[utf8]{inputenc}\n'
                    '\\usepackage{newtxtext}\n\\usepackage[varvw]{newtxmath}\n'
                    '\\usepackage{booktabs,graphicx,microtype,url}')
start, end = text.index('\\author{'), text.index('\\begin{document}')
text = text[:start] + r'''\author{Alexander V. Mantzaris\inst{1} \and James H. Korris\inst{2}}
\institute{School of Data, Mathematical and Statistical Sciences\\
University of Central Florida\\
Orlando, FL, USA\\
\email{alexander.mantzaris@ucf.edu}
\and Creative Technologies Inc.\\
Hollywood, CA, USA\\
\email{james.korris@cretecinc.com}}

''' + text[end:]
text = re.sub(r'\\end\{abstract\}\s*\\begin\{IEEEkeywords\}\s*(.*?)\s*\\end\{IEEEkeywords\}',
              lambda m: '\\keywords{' + m[1].replace(', ', r' \and ') + '}\n\\end{abstract}', text, flags=re.S)
text = text.replace('figure*', 'figure').replace('table*', 'table')
text = re.sub(r'(\\begin\{(?:table|figure)\})\[[^]]*\]', r'\1[!tbp]', text)
text = text.replace(r'M\in\{32,128,512,2048\}',
                    r'M\in\{32,\allowbreak128,\allowbreak512,\allowbreak2048\}')

# Native editable table cells; wrap the long method column instead of scaling.
ap_start = text.index(r'\label{tab:ap}')
ap_end = text.index(r'\end{table}', ap_start)
ap = text[ap_start:ap_end].replace(r'\begin{tabular}{lrrrrrr}', r'\begin{tabular}{@{}p{43mm}rrrrrr@{}}')
text = text[:ap_start] + ap + text[ap_end:]

# Split the nine-column confidence table into two panels, retaining all cells.
start = text.index(r'\label{tab:confidence}')
end = text.index(r'\end{table}', start)
block = text[start:end]
old = re.search(r'\\begin\{tabular\}.*?\\end\{tabular\}', block, re.S)[0]
rows = [r.strip().rstrip('\\').strip().split('&') for r in old.splitlines()
        if re.match(r'(?:S32L|S32N|S64N|Intel|SKAB) &', r)]
panels = []
for offset, heading in [(1, r'Brier & Log loss & Min. $p$ & False alarms'),
                        (5, 'Recall & Repairs & Failed & Harmful')]:
    panel = [r'\begin{tabular}{lrrrr}\toprule', 'Config. & ' + heading + r' \\\midrule']
    panel += [' & '.join(x.strip() for x in row[:1]+row[offset:offset+4]) + r' \\' for row in rows]
    panel += [r'\bottomrule', r'\end{tabular}']
    panels.append('\n'.join(panel))
text = text.replace(old, '\n\\par\\medskip\n'.join(panels))

# E1--E12 and their existing literal E2/E5/E6 references remain unchanged.
# Convert only the embedded, authoritative reference records to official style.
text = re.sub(r'% Bibliography embedded.*?\\end\{thebibliography\}',
              lambda _: '\\bibliographystyle{splncs04}\n\\bibliography{references}', text, flags=re.S)

layout = ROOT / 'internal/figure-layout.json'
if layout.exists():
    for filename, pages in json.loads(layout.read_text()).items():
        floats = list(re.finditer(r'\\begin\{figure\}.*?\\end\{figure\}', text, re.S))
        matching = [m for m in floats if '{' + filename + '}' in m[0]]
        assert len(matching) == 1, filename
        old = matching[0][0]
        caption_and_label = old[old.index(r'\caption'):old.index(r'\end{figure}')]
        new = r'\begin{figure}[p]' + '\n\\centering\n' + pages[0] + '\n' + caption_and_label + r'\end{figure}'
        for page in pages[1:]:
            new += '\n' + r'''\begin{figure}[p]
\centering
''' + page + '\n' + r'''\addtocounter{figure}{-1}
\renewcommand{\theHfigure}{\arabic{figure}continued}
\caption{Continued.}
\end{figure}'''
        text = text.replace(old, new)

baseline = ROOT / 'review/baseline'
baseline.mkdir(parents=True, exist_ok=True)
(baseline / 'main_baseline.tex').write_text(text)
print('Saved original-wording Springer baseline.')

if '--final' in sys.argv:
    start, end = text.index('\\author{'), text.index('\\begin{document}')
    text = text[:start] + '\\author{Anonymous Author(s)}\n\\institute{}\n\n' + text[end:]
    text = text.replace('pdfauthor={Alexander V. Mantzaris and James H. Korris}', 'pdfauthor={}')
    for change in json.loads((ROOT / 'internal/editorial-changes.json').read_text()):
        assert text.count(change['before']) == 1, change['location']
        text = text.replace(change['before'], change['after'])
    (ROOT / 'main.tex').write_text(text)
    print('Saved anonymous main.tex with explicit recorded changes.')
