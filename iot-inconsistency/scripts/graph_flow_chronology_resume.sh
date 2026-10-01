#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
.venv/bin/python - <<'PY'
import pathlib,json,datetime
base=pathlib.Path('results/graph_flow_v1/development');archive=base/'chronology_correction';archive.mkdir(exist_ok=True)
marker=archive/'remote_correction_applied.json'
if not marker.exists():
 for name in ['skab_scoring.json','skab_flow_predictions.npz']:
  path=base/name
  if path.exists() and not (archive/name).exists():path.rename(archive/name)
 marker.write_text(json.dumps(dict(reason='Original SKAB elapsed timestamps replace an index ramp before final scoring',time=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
PY
.venv/bin/python scripts/graph_flow.py neural
.venv/bin/python scripts/graph_flow.py smoke
