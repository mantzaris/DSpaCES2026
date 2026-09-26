"""Reproduce the full exact contract from frozen training allocations, no test."""
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from evidence_fusion.chronological_splits import sealed_read, split_mask
from evidence_fusion.provider_models import calendar_features, fit_ols
from evidence_fusion.influence_operators import exact_cross_blocks
from evidence_fusion.exact_exchange import encode,decode

threadpool_limits(limits=4)
frame=sealed_read('data/electricity_pretest.csv');x,_=calendar_features(frame.index)
days=frame.index.normalize();train=split_mask(frame.index,'2016-01-01','2016-10-01')
allocations=json.loads(Path('manifests/provider_allocations.json').read_text())
records=[]
for allocation in allocations:
    y=frame[allocation['building']].to_numpy(dtype=float)
    supports=[np.flatnonzero(train&days.isin(pd.to_datetime(pool))) for pool in allocation['selected_days']]
    models=[fit_ols(x,y,s,days.to_numpy()) for s in supports]
    begin=time.perf_counter();wire=encode(models,allocation['building'],int(train.sum()))
    encode_seconds=time.perf_counter()-begin
    begin=time.perf_counter();restored=decode(wire);parse_seconds=time.perf_counter()-begin
    error=max(float(np.max(np.abs(a.operator-b.operator))) for a,b in zip(models,restored))
    if error>1e-9*max(1.,max(np.max(np.abs(m.operator)) for m in models)):
        raise AssertionError('Exact public-calendar recovery differs')
    begin=time.perf_counter();blocks=exact_cross_blocks(restored);blocks_seconds=time.perf_counter()-begin
    records.append(dict(building=allocation['building'],common_days=allocation['common_days'],
        once_bytes=len(wire),amortized_metadata_bytes_256=len(wire)/256,
        encode_seconds=encode_seconds,parse_and_reconstruction_seconds=parse_seconds,
        cross_blocks_seconds=blocks_seconds,max_operator_absolute_error=error))
Path('results/exact_exchange.json').write_text(json.dumps(records,indent=2)+'\n')
print('Verified exact support exchange for',len(records),'allocations; bytes range',
      min(r['once_bytes'] for r in records),max(r['once_bytes'] for r in records))
