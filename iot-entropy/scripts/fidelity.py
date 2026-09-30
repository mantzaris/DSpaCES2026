"""Fixed untouched test subset: raw, spectral, correlation and covariance fidelity."""
from pathlib import Path
import json
import time

import numpy as np
import torch

from iot_entropy.data import load_data
from iot_entropy.experiment import load_models
from iot_entropy.features import Scan,prediction_fidelity
from iot_entropy.reference import BlockBootstrap,issue_reference
from iot_entropy.utils import Budget,recorded_runtime,write_json

root=Path(__file__).resolve().parents[1]
config=json.loads((root/'configs/full.json').read_text());base=root/'experiments/full'
torch.set_num_threads(4);started=time.monotonic()
budget=Budget(config['gpu_hour_budget'],recorded_runtime(root));rows=[]

def covariance(raw,correlation):
    common=torch.isfinite(raw).all(-1)
    count=common.sum(-1)
    mean=raw.masked_fill(~common[...,None],0).sum(-2)/count.clamp_min(1)[...,None]
    centered=(raw-mean[...,None,:]).masked_fill(~common[...,None],0)
    std=(centered.square().sum(-2)/(count-1).clamp_min(1)[...,None]).sqrt()
    return correlation*std[...,None,:]*std[...,:,None]

with torch.no_grad():
    for name in ['synthetic64','intel','pems']:
        data=load_data(root,name);x=data.standardized
        scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cuda')
        bootstrap=BlockBootstrap(data,48,120,'cuda')
        starts=data.issuance_indices(3,48,120,168)[:6]
        for seed in config['training_seeds']:
            model,_=load_models(data,config,seed,base,'cuda')
            for start in starts:
                observed=torch.as_tensor(x[start:start+120],device='cuda');obs=scan.extract(observed)
                for reference in ['diffusion','bootstrap']:
                    budget.check()
                    samples=issue_reference(model,data,x,int(start),120,config,'cuda',reference,bootstrap,seed+int(start))
                    generated=scan.extract(samples.masked_fill(~torch.isfinite(observed)[None],float('nan')))
                    center=torch.nanmedian(generated.values,dim=0).values
                    low=torch.nanquantile(generated.values,.05,dim=0)
                    high=torch.nanquantile(generated.values,.95,dim=0)
                    eligible=obs.eligible[0]&(generated.eligible.float().mean(0)>=.8)
                    record={'dataset':name,'seed':seed,'target_start':int(start),'reference':reference,
                            'eligible_groups':int(eligible.sum()),'total_groups':len(eligible),
                            **prediction_fidelity(observed,samples)}
                    for field,column in [('entropy',0),('entropy_change',1),('signed_correlation',2)]:
                        values=obs.values[0,:,column]
                        record[field+'_coverage90']=float(((values[eligible]>=low[eligible,column])&(values[eligible]<=high[eligible,column])).float().mean())
                        record[field+'_width90']=float((high-low)[eligible,column].mean())
                        record[field+'_median_absolute_error']=float((values-center[:,column])[eligible].abs().mean())
                    r_errors=[];cov_errors=[];offset=0
                    for observed_r,predicted_r,observed_raw,predicted_raw in zip(obs.correlations,generated.correlations,obs.raw,generated.raw):
                        count=observed_r.shape[1];valid=eligible[offset:offset+count];offset+=count
                        difference=(observed_r[0]-torch.nanmean(predicted_r,dim=0)).square().mean((-1,-2)).sqrt()
                        r_errors.append(difference[valid])
                        observed_cov=covariance(observed_raw,observed_r)[0]
                        predicted_cov=torch.nanmean(covariance(predicted_raw,predicted_r),dim=0)
                        cov_errors.append((observed_cov-predicted_cov).square().mean((-1,-2)).sqrt()[valid])
                    record['correlation_element_rmse']=float(torch.cat(r_errors).mean())
                    record['covariance_element_rmse_training_scaled']=float(torch.cat(cov_errors).mean())
                    rows.append(record)
write_json(root/'experiments/fidelity-extra.json',{'rows':rows,'elapsed_seconds':time.monotonic()-started,
           'selection':'First six disjoint untouched test units, three model seeds, fixed in source before inspecting results',
           'units':'Raw coverage in training-scaled coordinates; covariance errors retain squared training-scaled units; spectrum/correlation are dimensionless.'})
