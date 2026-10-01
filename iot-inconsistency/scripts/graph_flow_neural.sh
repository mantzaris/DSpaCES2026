#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
.venv/bin/python scripts/fetch_graph_flow_sources.py
.venv/bin/python scripts/graph_flow.py neural
