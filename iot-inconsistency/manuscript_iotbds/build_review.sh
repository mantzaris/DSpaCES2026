#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/baseline build/diff
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build/baseline review/baseline/main_baseline.tex
cp build/baseline/main_baseline.pdf review/baseline/paper_baseline.pdf
python3 internal/make_diff.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build/diff review/paper_diff.tex
cp build/diff/paper_diff.pdf review/paper_diff.pdf
