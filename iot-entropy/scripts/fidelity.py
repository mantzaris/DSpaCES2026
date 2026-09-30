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
                draws={};distributions={};records={};matrix_errors={}
                for reference in ['diffusion','bootstrap']:
                    budget.check()
                    samples=issue_reference(model,data,x,int(start),120,config,'cuda',reference,bootstrap,seed+int(start))
                    generated=scan.extract(samples.masked_fill(~torch.isfinite(observed)[None],float('nan')))
                    draws[reference]=samples
                    distributions[reference]=(generated.values,generated.eligible)
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
                    r_errors=[];cov_errors=[];all_r=[];all_cov=[];offset=0
                    for observed_r,predicted_r,observed_raw,predicted_raw in zip(obs.correlations,generated.correlations,obs.raw,generated.raw):
                        count=observed_r.shape[1];valid=eligible[offset:offset+count];offset+=count
                        difference=(observed_r[0]-torch.nanmean(predicted_r,dim=0)).square().mean((-1,-2)).sqrt()
                        all_r.append(difference)
                        r_errors.append(difference[valid])
                        observed_cov=covariance(observed_raw,observed_r)[0]
                        predicted_cov=torch.nanmean(covariance(predicted_raw,predicted_r),dim=0)
                        cov_difference=(observed_cov-predicted_cov).square().mean((-1,-2)).sqrt()
                        all_cov.append(cov_difference);cov_errors.append(cov_difference[valid])
                    record['correlation_element_rmse']=float(torch.cat(r_errors).mean())
                    record['covariance_element_rmse_training_scaled']=float(torch.cat(cov_errors).mean())
                    records[reference]=record
                    matrix_errors[reference]=(torch.cat(all_r),torch.cat(all_cov))
                    rows.append(record)
                common=torch.isfinite(observed)
                common_groups=obs.eligible[0].clone()
                for reference in draws:
                    common &= torch.isfinite(draws[reference]).all(0)
                    common_groups &= distributions[reference][1].float().mean(0)>=.8
                for reference,record in records.items():
                    matched=prediction_fidelity(observed.masked_fill(~common,float('nan')),draws[reference])
                    record['common_energy_score']=matched['energy_score']
                    record['common_energy_dimensions']=matched['energy_dimensions']
                    record['common_raw_coverage90']=matched['coverage90']
                    record['common_raw_width90']=matched['width90']
                    record['common_correlation_element_rmse']=float(torch.nanmean(matrix_errors[reference][0][common_groups]))
                    record['common_covariance_element_rmse_training_scaled']=float(torch.nanmean(matrix_errors[reference][1][common_groups]))
                    values=distributions[reference][0][:,:,0]
                    low,high=torch.nanquantile(values,torch.tensor([.05,.95],device='cuda'),dim=0)
                    actual=obs.values[0,:,0]
                    record['common_reference_groups']=int(common_groups.sum())
                    record['common_entropy_coverage90']=float(((actual[common_groups]>=low[common_groups])&(actual[common_groups]<=high[common_groups])).float().mean())
                    record['common_entropy_median_absolute_error']=float((actual-torch.nanmedian(values,dim=0).values)[common_groups].abs().mean())
write_json(root/'experiments/fidelity-extra.json',{'rows':rows,'elapsed_seconds':time.monotonic()-started,
           'selection':'First six disjoint untouched test units, three model seeds, fixed in source before inspecting results',
           'units':'Raw coverage in training-scaled coordinates; covariance errors retain squared training-scaled units; spectrum/correlation are dimensionless.'})
