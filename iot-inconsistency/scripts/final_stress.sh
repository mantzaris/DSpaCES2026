#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python - <<'PY'
import json,time
from pathlib import Path
p=Path('results/jobs/verify_final_gpu.json')
while json.loads(p.read_text())['state']=='running':time.sleep(5)
if json.loads(p.read_text())['state']!='complete':raise SystemExit('Final verification needs repair')
PY
for dataset in synthetic_32_linear synthetic_32_nonlinear synthetic_64_nonlinear intel skab; do
  .venv/bin/python scripts/robustness.py --dataset "$dataset"
done
.venv/bin/python scripts/analyze_equations.py
.venv/bin/python scripts/analyze_confidence.py
.venv/bin/python scripts/summarize_design.py
.venv/bin/python scripts/figures.py
