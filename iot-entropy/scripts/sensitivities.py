"""Compact predeclared sensitivities using fixed subsets and saved predictions."""
from pathlib import Path
import argparse
import json
import time

import numpy as np
import torch

from iot_entropy.calibration import rank_pvalues
from iot_entropy.data import load_data
from iot_entropy.entropy import entropy_from_correlation,window_features
from iot_entropy.experiment import load_models,run
from iot_entropy.features import Scan,score_features,summarize_reference
from iot_entropy.models import calendar
from iot_entropy.psd_sensitivity import covariance_em
from iot_entropy.reference import BlockBootstrap
from iot_entropy.synthetic import inject,simulate,system
from iot_entropy.utils import Budget,recorded_runtime,write_json

root=Path(__file__).resolve().parents[1]
config=json.loads((root/'configs/full.json').read_text())
base=root/'experiments/full'
out=root/'experiments/sensitivity';out.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['graphs','samples','quality','persistence','global','unscreened','directions'])
args=parser.parse_args()
spent=recorded_runtime(root)
budget=Budget(config['gpu_hour_budget'],spent);torch.set_num_threads(4)
started=time.monotonic()

if args.stage=='directions':
    from iot_entropy.direction_ablation import run_direction_ablation
    run_direction_ablation(root,config,budget)

elif args.stage=='graphs':
    for graph in ['removed','shuffled']:
        for name in config['datasets']:
            budget.check();run(load_data(root,name),config,17,base,budget,graph=graph)

elif args.stage=='samples':
    for number in [32,64,128]:
        directory=out/f'B{number}';directory.mkdir(exist_ok=True)
        if not (directory/'checkpoints').exists():(directory/'checkpoints').symlink_to(Path('../../full/checkpoints'),target_is_directory=True)
        local=dict(config,base_episodes=2,fault_types=['copy','noise','drift'],severities=[1.],durations=[48],generated_samples=number)
        for name in ['synthetic64','pems']:run(load_data(root,name),local,17,directory,budget)

elif args.stage=='quality':
    results=[]
    for name in ['synthetic64','intel','pems']:
        data=load_data(root,name);x=data.standardized
        scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cuda')
        indices=data.issuance_indices(3,48,120,168)[:6]
        for start in indices:
            original=x[start:start+120].copy()
            for rate in [0.,.01,.05,.1,.2]:
                budget.check();rng=np.random.default_rng(891+int(start))
                corrupted=original.copy();corrupted[rng.uniform(size=corrupted.shape)<rate]=np.nan
                result=scan.extract(torch.as_tensor(corrupted,device='cuda'))
                results.append({'dataset':name,'target_start':int(start),'missing_rate':rate,
                                'eligible_fraction':float(result.eligible.float().mean())})
            # Same-data PSD sensitivity on three predeclared size-six groups.
            for record in scan.records[:3]:
                window=record['window'];nodes=record['nodes'];channel=record['channel']
                sample=original[-window:,nodes,channel]
                em=covariance_em(sample)
                main=window_features(torch.as_tensor(sample,dtype=torch.float64),config['shrinkage'])
                results.append({'dataset':name,'target_start':int(start),'estimator':'Gaussian covariance EM sensitivity',
                                'group':record['index'],'complete_case_eligible':bool(main.valid),
                                'em_eligible':em is not None,
                                'complete_case_entropy':float(main.values[0]),
                                'em_entropy':float(entropy_from_correlation(torch.as_tensor(em),config['shrinkage'])) if em is not None else None})
        if name=='intel':
            full=load_data(root,'intel_full',primary_only=False)
            results.append({'dataset':'intel','view':'full-original-span auxiliary channels',
                            'channels':full.channels,'observed_fraction':np.isfinite(full.values).mean((0,1)),
                            'quantitative_channels':data.channels})
            auxiliary=load_data(root,'intel',primary_only=False)
            aux_scan=Scan(auxiliary.adjacency,auxiliary.coordinates,auxiliary.channels,config,'cuda')
            bootstrap=BlockBootstrap(auxiliary,48,120,'cuda')
            aux_values=auxiliary.standardized
            for start in indices:
                budget.check()
                block=torch.as_tensor(aux_values[start:start+120],device='cuda')
                observed=aux_scan.extract(block)
                samples=bootstrap.sample(aux_values[start-48:start],calendar(auxiliary.timestamps[start:start+120]),32,982+int(start))
                generated=aux_scan.extract(samples.masked_fill(~torch.isfinite(block)[None],float('nan')))
                low=torch.nanquantile(generated.values[:,:,0],.05,dim=0)
                high=torch.nanquantile(generated.values[:,:,0],.95,dim=0)
                for channel,label in enumerate(auxiliary.channels):
                    selected=torch.tensor([g['channel']==channel for g in aux_scan.records],device='cuda')
                    eligible=selected&observed.eligible[0]&(generated.eligible.float().mean(0)>=.8)
                    entropy=observed.values[0,:,0]
                    results.append({'dataset':'intel','view':'retained-span four-channel feature sensitivity',
                                    'target_start':int(start),'channel':label,'unit':auxiliary.units[channel],
                                    'observed_fraction':float(torch.isfinite(block[:,:,channel]).float().mean()),
                                    'observed_group_eligible_fraction':float(observed.eligible[0,selected].float().mean()),
                                    'joint_reference_eligible_groups':int(eligible.sum()),
                                    'mean_h':float(torch.nanmean(entropy[selected])),
                                    'bootstrap_h_coverage90':float(((entropy[eligible]>=low[eligible])&(entropy[eligible]<=high[eligible])).float().mean())})
    write_json(out/'quality.json',results)

elif args.stage=='persistence':
    name='synthetic64';data=load_data(root,name)
    model,_=load_models(data,config,17,base,'cuda')
    scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cuda')
    floor=torch.as_tensor(np.load(base/f'score-{name}-physical-17/development_parameters.npz')['floor'],device='cuda')
    coords,adjacency,transition,_=system(64)
    rows=[]
    for episode in range(3):
        raw=simulate(coords,transition,624,901000+episode,'cuda')
        clean=(raw-data.center)/data.scale
        dates=np.datetime64('2020-01-01','ns').astype('int64')+(np.arange(624)+256+(901000+episode)%288)*300*10**9
        nodes=np.argsort(np.linalg.norm(coords-coords[episode],axis=1))[:12].tolist()
        for kind in ['copy','noise','drift']:
            corrupted=inject(clean,nodes,192,288,kind,1.,901100+episode)
            for end in range(179,624,24):
                budget.check();target_start=end-119
                if target_start<48:continue
                observed=scan.extract(torch.as_tensor(corrupted[target_start:end+1],device='cuda'))
                known=torch.as_tensor(calendar(dates[target_start:end+1]),device='cuda')[None]
                contexts={'contaminated':corrupted[target_start-48:target_start],
                          'paired_clean':clean[target_start-48:target_start],
                          'frozen_earlier':corrupted[144:192] if target_start>=192 else corrupted[target_start-48:target_start]}
                for reference,context in contexts.items():
                    torch.manual_seed(99+end)
                    samples=model.sample(torch.as_tensor(context,device='cuda')[None],known,32,config['sampling_steps'],16)
                    scores,diag=score_features(observed,scan.extract(samples),floor)
                    rows.append({'episode':episode,'kind':kind,'time':end,'reference':reference,
                                 'context_after_onset':max(0,target_start-192),'entropy_max':float(scores['entropy'].nan_to_num(nan=-float('inf')).max()),
                                 'raw_max':float(scores['raw'].nan_to_num(nan=-float('inf')).max()),
                                 'mean_expected_h':float(torch.nanmean(diag['reference_center'][:,0]))})
    write_json(out/'persistence.json',{'rows':rows,'interpretation':'Score sensitivity only; frozen/paired-clean conditions are not assigned new calibrated guarantees'})

elif args.stage=='global':
    from iot_entropy.global_ablation import compare_global
    rows=[]
    for name in config['datasets']:
        data=load_data(root,name);x=data.standardized;n=len(data.node_ids)
        window=max(96,4*int(np.ceil(2.5*n/4)));lag=window//4;horizon=window+lag
        calibration=data.issuance_indices(2,48,horizon,48+horizon)
        tests=data.issuance_indices(3,48,horizon,48+horizon)[:8]
        # Large global windows cannot cross synthetic episode boundaries.
        # Their inability to support calibration is itself recorded, not hidden.
        row={'dataset':name,'nodes':n,'window':window,'calibration_units':len(calibration),
             'minimum_p':1/(len(calibration)+1),'attainable_alpha_0_1':len(calibration)>=9,'test_units':len(tests),'units':[]}
        if len(tests):
            bootstrap=BlockBootstrap(data,48,horizon,'cuda')
            for start in tests:
                budget.check();block=torch.as_tensor(x[start:start+horizon],device='cuda')
                generated=bootstrap.sample(x[start-48:start],calendar(data.timestamps[start:start+horizon]),32,381+int(start))
                for channel in range(len(data.channels)):
                    samples=generated[...,channel].masked_fill(~torch.isfinite(block[...,channel])[None],float('nan'))
                    observed=window_features(block[-window:,:,channel],config['shrinkage'])
                    reference=window_features(samples[:,-window:,:],config['shrinkage'])
                    row['units'].append({'target_start':int(start),'channel':channel,'eligible':bool(observed.valid),
                                         'entropy':float(observed.values[0]),'reference_h_median':float(torch.nanmedian(reference.values[:,0]))})
        rows.append(row)
    write_json(out/'global.json',rows)
    compare_global(root,config,budget)

elif args.stage=='unscreened':
    rows=[]
    for name in ['synthetic64','intel','pems']:
        data=load_data(root,name)
        from iot_entropy.training import build_diffusion
        from iot_entropy.features import prediction_fidelity
        for screened in [True,False]:
            model=build_diffusion(data,config,'cuda')
            path=(base if screened else base/'unscreened')/'checkpoints'/f'{name}-diffusion-physical-17.pt'
            model.load_state_dict(torch.load(path,map_location='cuda',weights_only=False)['state_dict'])
            indices=data.issuance_indices(3,48,120,168)[:6]
            for start in indices:
                budget.check();torch.manual_seed(331+int(start))
                context=torch.as_tensor(data.standardized[start-48:start],device='cuda')[None]
                known=torch.as_tensor(calendar(data.timestamps[start:start+120]),device='cuda')[None]
                samples=model.sample(context,known,32,20,16)
                observed=torch.as_tensor(data.standardized[start:start+120],device='cuda')
                rows.append({'dataset':name,'screened':screened,'target_start':int(start),**prediction_fidelity(observed,samples)})
    write_json(out/'unscreened.json',rows)

write_json(out/f'{args.stage}-status.json',{'status':'complete','elapsed_seconds':time.monotonic()-started,'total_budgeted_seconds':budget.elapsed})
