#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for dataset in synthetic_32_linear synthetic_32_nonlinear synthetic_64_nonlinear intel skab; do
  .venv/bin/python scripts/train_models.py --dataset "$dataset" --models diffusion gdn mean no_graph --width 768 --steps 3000 --batch 32
done
