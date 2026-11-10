#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/final
latexmk -pdf -jobname=paper -interaction=nonstopmode -halt-on-error -outdir=build/final main.tex
cp build/final/paper.pdf paper.pdf
