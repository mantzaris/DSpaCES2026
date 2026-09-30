"""Exercise final saved-output reporting in the recorded scientific environment."""
from pathlib import Path
import importlib.metadata
import platform
import time

import pandas as pd

from iot_entropy.manuscript import build as manuscript
from iot_entropy.plotting import build as figures
from iot_entropy.reporting import cross_dataset_summary
from iot_entropy.utils import digest, write_json

root=Path(__file__).resolve().parents[1]
started=time.perf_counter()
frame=pd.read_csv(root/'results/event_metrics.csv.gz')
cross_dataset_summary(frame[(frame.alpha==.1)&(frame.graph=='physical')],root/'results')
figures(root)
manuscript(root)
numeric=[*root.glob('manuscript/generated/*.tex'),
         root/'results/manuscript-claims.json',root/'results/case-selection.json',
         root/'results/dataset-table.json',root/'results/cross_dataset_summary.csv']
families=['architecture','theory','cases','spatial','performance',
          'directional-performance','calibration-cost']
for family in families:
    for extension in ['pdf','svg']:
        path=root/'manuscript/figures'/f'{family}.{extension}'
        if not path.is_file() or path.stat().st_size==0:
            raise RuntimeError('Missing generated figure: '+str(path))
record={'status':'passed','command':'PYTHONPATH=src .venv/bin/python scripts/verify_reporting_environment.py',
        'python':platform.python_version(),'packages':{name:importlib.metadata.version(name)
        for name in ['numpy','pandas','matplotlib','torch']},
        'elapsed_seconds':time.perf_counter()-started,'figure_families':families,
        'numerical_artifact_sha256':{str(path.relative_to(root)):digest(path) for path in numeric},
        'source_sha256':{str(path.relative_to(root)):digest(path) for path in
          [root/'src/iot_entropy/plotting.py',root/'src/iot_entropy/manuscript.py',
           root/'src/iot_entropy/reporting.py',Path(__file__)]},
        'note':'CPU reporting from saved measurements; this is not an additional GPU experiment. PDF graphics may differ across Matplotlib versions.'}
write_json(root/'experiments/validation/reporting-environment.json',record)
print('Reporting environment verified:',record['python'],record['packages'])
