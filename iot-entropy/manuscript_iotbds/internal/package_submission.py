#!/usr/bin/env python3
"""Package an explicit anonymous allowlist; no internal files can enter the ZIP."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / 'submission'
out.mkdir(exist_ok=True)
names = ['paper.tex', 'paper.pdf', 'references.bib', 'llncs.cls', 'splncs04.bst']
names += [str(p.relative_to(root)) for p in sorted((root / 'figures-v2').glob('*.pdf'))]
for name in names:
    target = out / name
    target.parent.mkdir(exist_ok=True)
    shutil.copy2(root / name, target)
shutil.copy2(root / 'internal/build/final/paper.bbl', out / 'paper.bbl')
names += ['paper.bbl', 'BUILD.txt']
(out / 'BUILD.txt').write_text(
    'Anonymous Regular Paper source package\n\n'
    'Run in this directory:\n'
    '  latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex\n\n'
    'Needs pdflatex, BibTeX, latexmk and the standard TeX Live packages\n'
    'newtxtext/newtxmath, booktabs, graphicx, microtype, hyperref and T1 fonts.\n'
    'Official unmodified llncs.cls v2.25 and splncs04.bst are supplied.\n'
    'Output: paper.pdf. No files outside this directory are needed.\n')
with zipfile.ZipFile(root / 'submission_source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for name in sorted(names):
        z.write(out / name, name)
manifest = {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in sorted(names)}
(root / 'internal/submission-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Packaged', len(names), 'explicitly allowed files; no internal files.')
