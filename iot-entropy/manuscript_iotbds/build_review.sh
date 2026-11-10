#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p internal/build/baseline internal/build/diff
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=internal/build/baseline internal/baseline/paper_baseline.tex
python3 internal/make_diff.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=internal/build/diff paper_diff.tex
cp internal/build/diff/paper_diff.pdf paper_diff.pdf
