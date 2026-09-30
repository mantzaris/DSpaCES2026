#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python - <<'PY'
import json,time
from pathlib import Path
p=Path('results/jobs/secondary_experiments.json')
while json.loads(p.read_text())['state']=='running':time.sleep(5)
if json.loads(p.read_text())['state']!='complete':raise SystemExit('Secondary experiment job needs repair')
PY
.venv/bin/python scripts/benchmark.py
.venv/bin/python scripts/export_models.py
.venv/bin/python scripts/analyze.py
.venv/bin/python scripts/export_graph.py
.venv/bin/python scripts/figures.py
