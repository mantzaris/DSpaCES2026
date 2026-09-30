#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m venv --system-site-packages .venv
.venv/bin/python -m pip install --cache-dir .cache/pip -r requirements-runpod.txt
.venv/bin/python -m pip freeze > results/environment.lock.txt
