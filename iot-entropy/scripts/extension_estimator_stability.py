"""Post-hoc CPU estimator diagnostic; independent known-process replicates.

No detector fitting or GPU use. Seed, sample counts and transformations are
fixed here before this diagnostic is run. This does not extend primary trials.
"""
from pathlib import Path
import json,time
import numpy as np
import torch
from iot_entropy.temporal import permutation_entropy,sample_entropy
from iot_entropy.utils import write_json

root=Path(__file__).resolve().parents[1];config=json.loads((root/'configs/extension-v2.json').read_text())
rng=np.random.default_rng(config['diagnostic_seed']+100);torch.set_num_threads(2)
start=time.monotonic();rows=[]
def summary(x):
    a=x.detach().numpy();v=a[np.isfinite(a)]
    return {'mean':float(v.mean()) if len(v) else None,'sd':float(v.std(ddof=1)) if len(v)>1 else None,'finite_fraction':float(np.isfinite(a).mean())}
for rho in [0.,.8]:
    noise=rng.normal(size=(128,608))*np.sqrt(1-rho*rho);state=np.zeros_like(noise)
    for t in range(1,608):state[:,t]=rho*state[:,t-1]+noise[:,t]
    for setting in ['continuous','quantized_0.5','missing_0.15']:
        values=state[:,-96:].copy()
        if setting=='quantized_0.5':values=np.round(values/.5)*.5
        if setting=='missing_0.15':values[rng.uniform(size=values.shape)<.15]=np.nan
        for w in [48,96]:
            x=torch.tensor(values[:,-w:],dtype=torch.float64)
            se=sample_entropy(x,2,.2,2,30,20,512,1024)
            for q,tau in [(3,1),(3,2),(4,1)]:
                pe=permutation_entropy(x,q,tau,30,5,.5)
                dropped=permutation_entropy(x,q,tau,30,5,1.,True)
                common=torch.isfinite(pe.value)&torch.isfinite(dropped.value)
                rows.append({'rho':rho,'setting':setting,'window':w,'q':q,'tau':tau,
                    'PE':summary(pe.value),'SE':summary(se.value),'tied_template_fraction':float(pe.tied_fraction.nanmean()),
                    'valid_PE_templates':float(pe.templates.double().mean()),
                    'valid_SE_templates':float(se.templates.double().mean()),
                    'mean_A':float(se.A.double().mean()),'mean_B':float(se.B.double().mean()),
                    'drop_ties_PE':summary(dropped.value),
                    'tie_policy_common_units':int(common.sum()),
                    'tie_policy_mean_absolute_difference':float((pe.value-dropped.value).abs()[common].mean()) if common.any() else None})
write_json(root/'results/extension-v2/estimator-stability.json',{'rows':rows,'independent_replicates':128,
    'seed':config['diagnostic_seed']+100,'device':'CPU float64','elapsed_seconds':time.monotonic()-start,
    'role':'post-hoc mathematical diagnostic, not primary validation or detector selection',
    'process':'stationary unit-variance Gaussian AR(1), rho 0 or .8, 512-row burn-in',
    'interpretation':'SD is between independent finite estimates; support conditioning can bias the reported mean. No claim that the finite-window mean equals a population entropy rate.'})
print({'rows':len(rows),'seconds':time.monotonic()-start})
