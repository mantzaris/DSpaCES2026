#!/usr/bin/env python3
"""Regenerate the mechanically normalized baseline and anonymous manuscript.

Input is the frozen LOCAL source snapshot, never a remote revision.
All layout-only transformations are identical in baseline and final source.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'internal/provenance/original-paper.tex').read_text()
text = source.replace(r'\documentclass[conference]{IEEEtran}', r'\documentclass{llncs}')
text = text.replace(r'\usepackage{amsmath,amssymb,amsthm,booktabs,graphicx,microtype}',
                    '\\usepackage{newtxtext}\n\\usepackage[varvw]{newtxmath}\n\\usepackage{booktabs,graphicx,microtype}')
text = text.replace('\\usepackage{dblfloatfix}\n', '')
text = text.replace('\\newtheorem{proposition}{Proposition}\n', '')
text = text.replace(r'\\[-2mm]', r'\\')
start = text.index('\\author{')
end = text.index('\\hypersetup{')
text = text[:start] + r'''\author{Alexander V. Mantzaris\inst{1} \and James H. Korris\inst{2}}
\institute{School of Data, Mathematical, and Statistical Sciences\\
University of Central Florida\\
Orlando, FL, USA\\
\email{Alexander.Mantzaris@ucf.edu}
\and Creative Technologies Inc.\\
Hollywood, CA, USA\\
\email{james.korris@cretecinc.com}}

''' + text[end:]
text = re.sub(r'\\end\{abstract\}\s*\\begin\{IEEEkeywords\}\s*(.*?)\s*\\end\{IEEEkeywords\}',
              lambda m: '\\keywords{' + m[1].replace(', ', r' \and ') + '}\n\\end{abstract}', text, flags=re.S)
text = text.replace('figure*', 'figure').replace('table*', 'table')
text = text.replace(r'\begin{table}[t]', r'\begin{table}[!tbp]')
text = text.replace(r'\begin{figure}[!tb]', r'\begin{figure}[!tbp]')
text = text.replace('\\IEEEtriggeratref{7}\n', '').replace(r'\bibliographystyle{IEEEtran}', r'\bibliographystyle{splncs04}')

# Reflow the 14-column results table as three stacked six-column panels.
# Every numerical cell stays with its original dataset/reference/family.
pattern = r'\\begin\{tabular\}\{llrrrrrrrrrrrr\}.*?\\end\{tabular\}'
old = re.search(pattern, text, re.S)[0]
rows = [r.strip().rstrip('\\').strip().split('&') for r in old.splitlines()
        if r.startswith(('Block &', 'Diffusion &'))]
panels = []
for i, dataset in enumerate(['Synthetic (three sizes)', 'Intel Lab', 'PEMS-BAY']):
    panel = [r'\begin{tabular}{llrrrr}\toprule',
             r'\multicolumn{6}{c}{' + dataset + r'}\\',
             r'Reference&Family&P&R&AP&IoU\\\midrule']
    for n, row in enumerate(rows):
        if n == 5:
            panel.append(r'\midrule')
        panel.append(' & '.join(x.strip() for x in row[:2]+row[2+i*4:6+i*4]) + r' \\')
    panel += [r'\bottomrule', r'\end{tabular}']
    panels.append('\n'.join(panel))
text = text.replace(old, '\n\\par\\medskip\n'.join(panels))

# Reflow fidelity columns into two panels, without scaling table fonts.
pattern = r'\\begin\{tabular\}\{llrrrrrrrr\}.*?\\end\{tabular\}'
old = re.search(pattern, text, re.S)[0]
rows = [r.strip().rstrip('\\').strip().split('&') for r in old.splitlines()
        if r.startswith(('Synthetic &', 'Intel Lab &', 'PEMS-BAY &'))]
panels = []
for i, heading in enumerate(['Raw&H&PE&SE', 'ACF1 MAE&Ordinal TV&R RMSE&ES']):
    panel = [r'\begin{tabular}{llrrrr}\toprule',
             'Dataset&Reference&' + heading + r'\\\midrule']
    panel += [' & '.join(x.strip() for x in row[:2]+row[2+i*4:6+i*4]) + r' \\' for row in rows]
    panel += [r'\bottomrule', r'\end{tabular}']
    panels.append('\n'.join(panel))
text = text.replace(old, '\n\\par\\medskip\n'.join(panels))

# Figure panel layout, if present, consists solely of includegraphics commands.
layout = ROOT / 'internal/figure-layout.json'
if layout.exists():
    import json
    for filename, replacement in json.loads(layout.read_text()).items():
        text = text.replace(r'\includegraphics[width=\textwidth]{' + filename + '}', replacement)

baseline = ROOT / 'internal/baseline'
baseline.mkdir(exist_ok=True)
(baseline / 'paper_baseline.tex').write_text(text)

# Review-anonymity changes are applied only after saving the original-wording baseline.
start = text.index('\\author{')
end = text.index('\\hypersetup{')
text = text[:start] + '\\author{Anonymous Author(s)}\n\\institute{}\n\n' + text[end:]
text = text.replace('pdfauthor={Alexander V. Mantzaris and James H. Korris}', 'pdfauthor={}')
text = text.replace(r'\section*{Acknowledgment and AI disclosure}', r'\section*{AI disclosure}')
# Explicit user-requested editorial changes; never fold these into the baseline.
editorial = ROOT / 'internal/editorial-changes.json'
if editorial.exists():
    import json
    for change in json.loads(editorial.read_text()):
        assert text.count(change['before']) == 1, change['location']
        text = text.replace(change['before'], change['after'])
(ROOT / 'paper.tex').write_text(text)
print('Generated paper.tex and internal/baseline/paper_baseline.tex')
