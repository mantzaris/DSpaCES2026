#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
.venv/bin/python scripts/graph_flow.py audit
.venv/bin/python scripts/graph_flow.py robustness
.venv/bin/python scripts/benchmark_graph_flow.py
.venv/bin/python scripts/export_graph_flow.py
