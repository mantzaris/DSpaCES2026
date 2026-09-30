"""Rank-calibration diagnostic on independently simulated dependent sensor paths.

This is a mathematical diagnostic of the existing synthetic study, not another
primary dataset or a tuned detector. Each replicate has four stationary AR(1)
sensors; the score is max(abs(sensor)), fixed before calibration.
"""
from pathlib import Path
import numpy as np
from iot_entropy.utils import write_json

root=Path(__file__).resolve().parents[1];rows=[];replicates=20000;n=32
for rho in [0.,.9,.99]:
    for gap in [1,8,32]:
        rng=np.random.default_rng(10812);state=rng.normal(size=(replicates,4));scores=[]
        coefficient=rho**gap
        for step in range(n+1):
            state=coefficient*state+np.sqrt(1-coefficient**2)*rng.normal(size=state.shape)
            scores.append(np.max(np.abs(state),axis=1))
        scores=np.stack(scores,axis=1)
        p=(1+(scores[:,:n]>=scores[:,n,None]).sum(1))/(n+1)
        for alpha in [.05,.1,.2]:
            rate=float(np.mean(p<=alpha))
            rows.append({'rho':rho,'gap':gap,'alpha':alpha,'exceedance':rate,
                         'mc_standard_error':float(np.sqrt(rate*(1-rate)/replicates)),
                         'effective_ar_coefficient':coefficient})
write_json(root/'results/calibration-null-diagnostic.json',{'replicates':replicates,'calibration_units':n,
           'score':'max absolute value of four independent stationary AR(1) sensors; independent replicate paths',
           'interpretation':'Stationary dependent units need not be exchangeable. Gaps reduce this specified AR dependence but do not prove validity on the real recordings.',
           'rows':rows})
