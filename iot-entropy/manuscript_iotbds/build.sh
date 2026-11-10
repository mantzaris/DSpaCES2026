#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p internal/build/final
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=internal/build/final paper.tex
cp internal/build/final/paper.pdf paper.pdf
