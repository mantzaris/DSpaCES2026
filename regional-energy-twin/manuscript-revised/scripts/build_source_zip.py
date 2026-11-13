"""Package the clean manuscript and verify a standalone build from the ZIP."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'regional_twin_study_source'
ARCHIVE = ROOT / (NAME + '.zip')
FIGURES = ['information_flow', 'transparent_episode', 'paired_comparison', 'acquisition_path']
SOURCES = ['regional_twin_study.tex', 'regional_twin_study.pdf', 'regional_twin_study.bbl',
           'references.bib', 'IEEEtran.cls', 'IEEEtran.bst',
           'generated/numbers.tex', 'generated/principal_rows.tex', 'generated/alarm_matched_rows.tex']
SOURCES += ['figures/' + name + ext for name in FIGURES for ext in ['.pdf', '.svg']]
BUILD = '''#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export SOURCE_DATE_EPOCH=1794355200
export FORCE_SOURCE_DATE=1
latexmk -pdf -interaction=nonstopmode -halt-on-error regional_twin_study.tex
'''
README = '''# From Detail to Decisions in Regional Energy Twins

Authors: Alexander V. Mantzaris and James H. Korris.
This source package contains the clean revised manuscript (10 pages), its compiled
PDF, bibliography, IEEEtran template, generated tables, and PDF/SVG figure assets.
It is independent of the research repository. No raw data, experimental caches,
review markup, or external analysis inputs are needed to compile it.

Build from this directory:

```bash
bash build.sh
```

Requirements: a LaTeX distribution with latexmk, BibTeX, and the standard packages
amsmath, amssymb, amsthm, graphicx, booktabs, array, cite, balance, and hyperref.
The IEEEtran class and bibliography style are included. Sources were verified with
TeX Live 2019/Debian, pdfTeX 1.40.20 and latexmk 4.67. The build uses the supplied
numerical tables and figures; it does not rerun analysis or access the network.

`source_manifest.json` provides SHA-256 hashes of every packaged file other than
itself. The supplied PDF is byte-identical to the clean author-review PDF. PDF
metadata may differ when rebuilt with a different TeX installation.
'''

def digest(data):
    return hashlib.sha256(data).hexdigest()

def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs)

def main():
    payload = {name: (ROOT / name).read_bytes() for name in SOURCES}
    payload.update({'build.sh': BUILD.encode(), 'README.md': README.encode()})
    manifest = {name: digest(data) for name, data in sorted(payload.items())}
    payload['source_manifest.json'] = (json.dumps({'sha256': manifest}, indent=2) + '\n').encode()
    with zipfile.ZipFile(ARCHIVE, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo(NAME + '/' + name, date_time=(2026, 11, 11, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = ((0o100755 if name == 'build.sh' else 0o100644) << 16)
            entry.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(entry, data, compresslevel=9)
    with tempfile.TemporaryDirectory(prefix='source_zip_check_', dir=ROOT/'internal') as tmp:
        with zipfile.ZipFile(ARCHIVE) as archive:
            assert archive.testzip() is None
            assert all(not Path(x).is_absolute() and '..' not in Path(x).parts for x in archive.namelist())
            archive.extractall(tmp)
        package = Path(tmp) / NAME
        for name, expected in manifest.items():
            assert digest((package/name).read_bytes()) == expected, name
        (package/'regional_twin_study.pdf').unlink()  # Force actual standalone compilation.
        with (ROOT/'internal/source_zip_build.log').open('w') as log:
            subprocess.run(['bash', 'build.sh'], cwd=package, stdout=log, stderr=subprocess.STDOUT, check=True)
        pdf = package/'regional_twin_study.pdf'
        info = run('pdfinfo', str(pdf))
        pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
        assert pages == 10
        clean_text = run('pdftotext', str(ROOT/'regional_twin_study.pdf'), '-')
        rebuilt_text = run('pdftotext', str(pdf), '-')
        assert rebuilt_text == clean_text, 'Rebuilt paper text differs'
        log = (package/'regional_twin_study.log').read_text()
        assert not re.search(r'(Citation|Reference).*undefined|There were undefined|Overfull|Undefined control sequence', log)
        outputs = [x[7:] for x in (package/'regional_twin_study.fls').read_text().splitlines() if x.startswith('OUTPUT ')]
        assert all(package in (package/x).resolve().parents for x in outputs)
    sha = digest(ARCHIVE.read_bytes())
    (ROOT/(NAME+'.zip.sha256')).write_text(sha+'  '+ARCHIVE.name+'\n')
    report = {'archive': ARCHIVE.name, 'bytes': ARCHIVE.stat().st_size, 'sha256': sha,
              'files': sorted(payload), 'file_count': len(payload), 'zip_integrity': 'pass',
              'embedded_source_hashes': 'pass', 'standalone_build': 'pass', 'pages': pages,
              'rebuilt_text_matches_clean_pdf': True, 'original_manuscript_changed': False,
              'gpu_used': False, 'raw_data_included': False}
    (ROOT/'internal/source_zip_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
