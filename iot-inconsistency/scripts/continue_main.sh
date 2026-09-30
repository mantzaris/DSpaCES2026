#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# A running upstream job is polled inside this detached finite pipeline.
.venv/bin/python - <<'PY'
import json,time
from pathlib import Path
p=Path('results/jobs/training_v2.json')
while json.loads(p.read_text())['state']=='running':time.sleep(5)
if json.loads(p.read_text())['state']!='complete':raise SystemExit('Upstream training failed')
PY
bash scripts/train_diffad.sh
for dataset in synthetic_32_linear synthetic_32_nonlinear synthetic_64_nonlinear intel skab; do
  .venv/bin/python scripts/evaluate.py --dataset "$dataset" --split development
  .venv/bin/python scripts/freeze.py --dataset "$dataset" --stage development
  .venv/bin/python scripts/evaluate.py --dataset "$dataset" --split calibration
  .venv/bin/python scripts/freeze.py --dataset "$dataset" --stage calibration
  .venv/bin/python scripts/evaluate.py --dataset "$dataset" --split test
done
