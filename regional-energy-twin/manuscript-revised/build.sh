#!/usr/bin/env bash
set -euo pipefail
REVISION_ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$REVISION_ROOT/.." && pwd)"
cd "$REVISION_ROOT"
mkdir -p internal/tmp internal/mplconfig internal/render-clean internal/render-diff
export TMPDIR="$REVISION_ROOT/internal/tmp"
export MPLCONFIGDIR="$REVISION_ROOT/internal/mplconfig"
export PYTHONDONTWRITEBYTECODE=1
export SOURCE_DATE_EPOCH=1794355200
export FORCE_SOURCE_DATE=1
python3 scripts/audit_provenance.py --project "$PROJECT_ROOT" --output "$REVISION_ROOT/analysis/provenance_checks.json" > internal/provenance-build.log
python3 scripts/analyze_alarm_sweep.py --project "$PROJECT_ROOT" --output "$REVISION_ROOT" > internal/alarm-build.log
python3 scripts/build_episode_figure.py --project "$PROJECT_ROOT" --output "$REVISION_ROOT" > internal/figure-build.log
latexmk -pdf -interaction=nonstopmode -halt-on-error regional_twin_study.tex > internal/clean-build.log 2>&1
python3 scripts/prepare_diff.py
latexmk -pdf -interaction=nonstopmode -halt-on-error regional_twin_study_diff.tex > internal/diff-build.log 2>&1
latexmk -pdf -interaction=nonstopmode -halt-on-error figure_changes.tex > internal/figure-comparison-build.log 2>&1
python3 scripts/validate_revision.py
python3 scripts/package_revision.py
