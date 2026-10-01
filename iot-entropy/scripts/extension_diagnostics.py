"""Aligned mathematical diagnostics; deliberately separate from fault benchmarks."""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from iot_entropy.entropy import window_features, entropy_from_correlation
from iot_entropy.temporal import window, coarse_grain, FEATURES
from iot_entropy.utils import write_json

root=Path(__file__).resolve().parents[1]
config=json.loads((root/'configs/extension-v2.json').read_text())
config['sample_delta']=.2
torch.set_num_threads(2)
rng=np.random.default_rng(config['diagnostic_seed'])
rows=[]; examples={}; errors=[]; started=time.monotonic()
for replicate in range(64):
    noise=rng.normal(size=(352,6))*.15
    state=np.zeros((352,6))
    shared=rng.normal(size=352)*.08
    for t in range(1,len(state)):
        state[t]=.88*state[t-1]+noise[t]+shared[t]
    original=state[-96:]
    cases={'normal':original,
           'joint_time_shuffle':original[rng.permutation(96)],
           'replay_period12':np.tile(original[:12],(8,1)),
           'periodic_interference':original+.6*np.sin(2*np.pi*np.arange(96)/8)[:,None],
           'independent_time_shuffle':np.stack([rng.permutation(original[:,i]) for i in range(6)],1),
           'cross_sensor_copy':np.tile(original[:,:1],(1,6)),
           'legitimate_transition':original+.8*np.sin(np.linspace(0,np.pi,96))[:,None],
           'offset':original+2,
           'gain':original*2,
           'sign_change':original*np.array([1,-1,1,-1,1,-1])[None],
           'quantization':np.round(original/.3)*.3,
           'flatline':np.zeros_like(original),
           'dropout':np.where(rng.uniform(size=original.shape)<.15,np.nan,original)}
    baseline=window_features(torch.tensor(original))
    for kind,array in cases.items():
        spatial=window_features(torch.tensor(array))
        if kind=='joint_time_shuffle':
            error=float((spatial.correlation-baseline.correlation).abs().max())
            errors.append(error)
            assert error<1e-12
        for scale in [1,2,4]:
            temporal=window(coarse_grain(torch.tensor(array.T),scale),config)
            row={'replicate':replicate,'scenario':kind,'scale':scale,
                 'spatial_H':float(spatial.values[0]),'spatial_C':float(spatial.values[1]),
                 'spatial_available':bool(spatial.valid),'spatial_rows':int(spatial.count),
                 'templates':float(temporal['pe_templates'].double().mean()),
                 'ties':float(temporal['ties'].mean()),'sample_A':float(temporal['A'].double().mean()),
                 'sample_B':float(temporal['B'].double().mean()),
                 'censored_fraction':float(temporal['censored'].double().mean())}
            for f,feature in enumerate(FEATURES):
                row[feature]=float(torch.nanmean(temporal['values'][...,f]))
                row[feature+'_availability']=float(torch.isfinite(temporal['values'][...,f]).double().mean())
            rows.append(row)
        if replicate==0:
            examples[kind]=array
frame=pd.DataFrame(rows)
out=root/'results/extension-v2';out.mkdir(exist_ok=True,parents=True)
frame.to_csv(out/'diagnostics.csv.gz',index=False,compression='gzip')
np.savez_compressed(out/'diagnostic-examples.npz',**examples)
eye=torch.eye(4,dtype=torch.float64)
one=.8*eye+.2*torch.ones_like(eye);two=eye.clone()
two[0,1]=two[1,0]=two[2,3]=two[3,2]=.6
write_json(out/'theory-checks.json',{'replicates':64,'joint_permutation_max_R_error':max(errors),
    'matched_summary_matrices':[one.numpy(),two.numpy()],
    'matched_H_unshrunk':[float(entropy_from_correlation(one,0)),float(entropy_from_correlation(two,0))],
    'matched_signed_correlation':.2,'matched_leading_concentration':.4,
    'diagnostic_not_primary':True,'device':'cpu float64','elapsed_seconds':time.monotonic()-started})
print(json.dumps({'rows':len(rows),'maximum_invariance_error':max(errors)}))
