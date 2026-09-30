#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python - <<'PY'
import json,time
from pathlib import Path
p=Path('results/jobs/finish_artifacts.json')
while json.loads(p.read_text())['state']=='running':time.sleep(5)
if json.loads(p.read_text())['state']!='complete':raise SystemExit('Artifact job needs repair')
PY
.venv/bin/python scripts/audit_portable_models.py
.venv/bin/python -m pytest -q --junitxml=results/audits/pytest_cuda.xml
