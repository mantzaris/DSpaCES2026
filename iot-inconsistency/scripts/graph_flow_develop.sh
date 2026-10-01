#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
.venv/bin/python scripts/graph_flow.py prepare
.venv/bin/python scripts/graph_flow.py develop_models
