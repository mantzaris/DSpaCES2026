#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
.venv/bin/python scripts/graph_flow.py sampling
.venv/bin/python scripts/graph_flow.py freeze
.venv/bin/python scripts/graph_flow.py calibration
.venv/bin/python scripts/graph_flow.py legacy_calibration
.venv/bin/python scripts/graph_flow.py calibrate
.venv/bin/python scripts/graph_flow.py test
.venv/bin/python scripts/graph_flow.py legacy_test
.venv/bin/python scripts/graph_flow.py analyze
.venv/bin/python scripts/graph_flow.py audit
