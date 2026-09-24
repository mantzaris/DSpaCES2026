#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src:.deps${PYTHONPATH:+:$PYTHONPATH}"
export SOURCE_DATE_EPOCH=1790208000
export FORCE_SOURCE_DATE=1
if [[ "${1:-}" == "--clean" ]]; then
  latexmk -cd -C manuscript/regional_twin_study.tex
fi
python3 scripts/build_regional_study_results.py
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error manuscript/regional_twin_study.tex
python3 scripts/check_regional_manuscript.py
