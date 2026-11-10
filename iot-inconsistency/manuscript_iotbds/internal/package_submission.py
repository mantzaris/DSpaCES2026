#!/usr/bin/env python3
"""Build a submission-only ZIP from an explicit anonymous allowlist."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'submission'
out.mkdir(exist_ok=True)
names = ['main.tex', 'paper.pdf', 'references.bib', 'llncs.cls', 'splncs04.bst']
names += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'figures/graph_flow').glob('*.pdf'))]
for name in names:
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, target)
shutil.copy2(ROOT / 'build/final/paper.bbl', out / 'paper.bbl')
(out / 'BUILD.txt').write_text(
    'Anonymous Regular Paper source package\n\n'
    'Run in this directory:\n'
    'latexmk -pdf -jobname=paper -interaction=nonstopmode -halt-on-error main.tex\n\n'
    'Output: paper.pdf. Requires pdfLaTeX, BibTeX, latexmk, newtxtext/newtxmath,\n'
    'T1 fonts, booktabs, graphicx, microtype, url, hyperref and standard LNCS\n'
    'dependencies. Official llncs.cls v2.25 and splncs04.bst are supplied.\n'
    'All manuscript inputs are local; no experiment or generator is needed.\n')
names += ['paper.bbl', 'BUILD.txt']
with zipfile.ZipFile(ROOT / 'submission_source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for name in sorted(names):
        z.write(out / name, name)
manifest = {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in sorted(names)}
(ROOT / 'internal/validation/submission-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('Packaged', len(names), 'anonymous submission files; internal material excluded.')
