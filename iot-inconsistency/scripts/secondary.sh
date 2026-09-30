#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python - <<'PY'
import json,time
from pathlib import Path
p=Path('results/jobs/main_experiments.json')
while json.loads(p.read_text())['state']=='running':time.sleep(5)
if json.loads(p.read_text())['state']!='complete':raise SystemExit('Main experiments need repair before secondary work')
PY
.venv/bin/python scripts/audit_saved_scores.py
.venv/bin/python scripts/analyze.py
.venv/bin/python scripts/audit_models.py
.venv/bin/python scripts/audit_metadata.py
.venv/bin/python scripts/prepare_contaminated.py
.venv/bin/python scripts/train_models.py --dataset synthetic_32_nonlinear_contaminated --models diffusion --width 768 --steps 3000 --batch 32
for dataset in synthetic_32_linear synthetic_32_nonlinear synthetic_64_nonlinear intel skab; do
  .venv/bin/python scripts/ablate.py --dataset "$dataset"
  .venv/bin/python scripts/robustness.py --dataset "$dataset"
done
.venv/bin/python scripts/native_process.py
