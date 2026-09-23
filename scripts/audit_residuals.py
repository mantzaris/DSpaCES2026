"""Fixed training and historical-validation diagnostics; no model selection."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from evidence_fusion.chronological_splits import sealed_read, split_mask, causal_target_mask, pilot_roles
from evidence_fusion.provider_models import calendar_features, fit_ols

threadpool_limits(limits=4)
frame=sealed_read('data/electricity_pretest.csv');x,_=calendar_features(frame.index)
days=frame.index.normalize();train=split_mask(frame.index,'2016-01-01','2016-10-01')
audit=json.loads(Path('manifests/data_audit.json').read_text())
allocations=json.loads(Path('manifests/provider_allocations.json').read_text());records=[]
for allocation in allocations:
    building=allocation['building'];y=frame[building].to_numpy(dtype=float)
    supports=[np.flatnonzero(train&days.isin(pd.to_datetime(pool))) for pool in allocation['selected_days']]
    models=[fit_ols(x,y,s,days.to_numpy()) for s in supports]
    means=np.column_stack([m.predict(x) for m in models]);errors=means-y[:,None]
    valid=np.isfinite(y)&(y>=0)
    monthly=[]
    for month in range(1,10):
        mask=train&valid&(frame.index.month==month)
        monthly.append(dict(month=month,n=int(mask.sum()),provider_bias=np.mean(errors[mask],axis=0).tolist(),
            provider_rmse=np.sqrt(np.mean(errors[mask]**2,axis=0)).tolist()))
    timezone=next(r['timezone'] for r in audit['selection'] if r['building']==building)
    eligible=np.flatnonzero(causal_target_mask(frame.index,timezone)&split_mask(frame.index,'2016-10-08','2016-11-01'))
    target=eligible[np.linspace(0,len(eligible)-1,256,dtype=int)]
    history=pilot_roles(frame.index[target])['covariance']&valid[target]&valid[target-168]
    correlation=np.corrcoef(errors[target[history]],rowvar=False)
    records.append(dict(building=building,common_days=allocation['common_days'],training_monthly=monthly,
        historical_error_correlation=correlation.tolist(),historical_covariance_observations=int(history.sum())))
Path('results/residual_diagnostics.json').write_text(json.dumps(records,indent=2)+'\n')
print('Saved frozen training-month and historical error-correlation diagnostics for',len(records),'allocations')
