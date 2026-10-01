"""Production density replay, prior-sampling repeatability and numerical evidence."""
import json
from pathlib import Path
import time

import numpy as np
import torch
from scipy.special import logsumexp
from scipy.stats import spearmanr

from .flow_data import configuration,build_cases,graph_for,sha256
from .flow_training import load_flow
from .flow_inference import infer_case
from .flow_execution import development_selection
from .flow_math import GaussianCorruption
from .graph_flow_model import build_context
from .experiment import json_save


def sampling_development(root):
    root=Path(root);config=configuration(root);directory=root/'results/graph_flow_v1/development'
    for dataset in config['datasets']:
        path=directory/(dataset+'_sampling.json')
        if path.exists():continue
        selection=development_selection(root,dataset);models=[load_flow(root,r) for r in selection['members']['members']]
        graph=graph_for(root,dataset);cases=build_cases(root,dataset,'development')
        selected=[cases[i] for i in np.linspace(0,len(cases)-1,12,dtype=int)]
        scores={m:[] for m in config['sample_counts']};timings=[];eligibility=[]
        for repeat in range(3):
            for ordinal,case in enumerate(selected):
                result=infer_case(models,case['values'],graph,selection['models']['selected']['specification']['context_length'],2048,
                     selection['scoring']['scale'],seed=72000000+repeat*100000+ordinal*101,sensitivity=True)
                for m in scores:scores[m].append(result['scores']['M'+str(m)])
                timings.append(result['seconds']);eligibility.append(result['eligible'])
        eligibility=np.asarray(eligibility).reshape(3,12,-1)[0]
        score_arrays={m:np.asarray(v).reshape(3,12,-1) for m,v in scores.items()};report=[]
        for m,values in score_arrays.items():
            difference=np.abs(values[1:,eligibility]-values[0,eligibility])
            report.append(dict(samples=m,repeat_absolute_difference_p95=float(np.quantile(difference,.95)),
                repeat_absolute_difference_max=float(difference.max()),
                spearman_vs_repeat0=[float(spearmanr(values[0,eligibility],values[r,eligibility]).statistic) for r in (1,2)]))
        # Exclusive-GPU profiles follow model fitting. Each M has its own timed execution.
        profile=[];case=selected[1]
        for m in config['sample_counts']:
            measured=[]
            for repeat in range(3):
                torch.cuda.reset_peak_memory_stats()
                result=infer_case(models,case['values'],graph,selection['models']['selected']['specification']['context_length'],m,
                     selection['scoring']['scale'],seed=73000000+repeat,reference=case['reference'])
                measured.append(dict(seconds=result['seconds'],peak_gpu_bytes=result['peak_gpu_bytes'],
                                     candidates=int(result['eligible'].sum()),mean_ess=float(result['ess'][result['eligible']].mean())))
            profile.append(dict(samples=m,repetitions=measured))
        arrays=path.with_suffix('.npz');np.savez_compressed(arrays,**{'M'+str(k):v for k,v in score_arrays.items()},eligible=eligibility)
        json_save(path,dict(dataset=dataset,case_ids=[c['id'] for c in selected],sampling_seeds=3,model_ensemble_repetitions=1,
                   repeatability=report,profiles=profile,arrays_sha256=sha256(arrays),primary_samples=selection['scoring']['sample_count'],
                   caveat='M=2048 is a finite reference, not the exact integral. Repeatability is not a bound on model error.'))
        del models;torch.cuda.empty_cache()


def audit_production(root):
    root=Path(root);directory=root/'results/graph_flow_v1';lock=json.loads((directory/'protocol_lock.json').read_text());summary=[];total=0;max_error=0.
    for dataset in lock['configuration']['datasets']:
        selection=lock['choices'][dataset];models=[load_flow(root,r) for r in selection['members']['members']];graph=graph_for(root,dataset)
        for split in ('calibration','test'):
            for path in sorted((directory/dataset/split).glob('*.npz')):
                raw=dict(np.load(path,allow_pickle=False));normal=raw['audit_log_normal_members']
                if not len(normal):continue
                fault=logsumexp(raw['audit_log_fault_components']-np.log(4),axis=1)
                expected=fault-(logsumexp(normal,axis=1)-np.log(3))
                error=float(np.max(np.abs(expected-raw['audit_score'])));max_error=max(error,max_error);total+=len(expected)
                assert error<1e-7
            for path in sorted((directory/'evidence').glob(dataset+'_'+split+'_*.npz')):
                raw=dict(np.load(path,allow_pickle=False));values=torch.tensor(raw['input'],device='cuda')
                if not len(raw['query']):
                    summary.append(dict(path=str(path.relative_to(root)),sha256=sha256(path),candidates=0,status='all targets unavailable, no numeric density evaluated'))
                    continue
                query=torch.tensor(raw['query'],device='cuda');target=values[query,-8:]
                inputs=build_context(values[None].expand(len(query),-1,-1),query,graph,selection['models']['selected']['specification']['context_length'])
                generation_error=0.;density_error=0.;inverse_error=0.;jacobian_error=0.
                with torch.no_grad():
                    for member,model in enumerate(models):
                        encoded=model.encode(inputs);latent=torch.tensor(raw['latent'][:,member],device='cuda')
                        generated=model.sample(encoded,sample_count=latent.shape[1],latent=latent,chunk=128)
                        generation_error=max(generation_error,float(np.max(np.abs(generated.cpu().numpy()-raw['generated'][:,member]))))
                        density_error=max(density_error,float(np.max(np.abs(model.log_prob(target,encoded).cpu().numpy()-raw['log_normal_members'][:,member]))))
                        transformed,_=model.transform(target,encoded);restored,_=model.transform(transformed,encoded,inverse=True)
                        inverse_error=max(inverse_error,float((restored-target).abs().max()))
                # E5 independently evaluated with NumPy Cholesky, not the Torch kernel.
                channel=GaussianCorruption(8,scale=float(raw['corruption_scale']));generated=raw['generated'].astype(float)
                components=[]
                for mapping,covariance in zip(channel.maps,channel.covariance.numpy()):
                    difference=raw['input'][raw['query'],-8:][:,None,None]-np.einsum('ij,bemj->bemi',mapping,generated)
                    cholesky=np.linalg.cholesky(covariance)
                    whitened=np.linalg.solve(cholesky,difference.reshape(-1,8).T).T.reshape(difference.shape)
                    components.append(-.5*(np.square(whitened).sum(-1)+2*np.log(np.diag(cholesky)).sum()+8*np.log(2*np.pi)))
                log_q=logsumexp(np.stack(components,-1)-np.log(4),axis=-1)
                q_error=float(np.max(np.abs(log_q-raw['log_corruption'])))
                expected=logsumexp(log_q.reshape(len(query),-1),axis=1)-np.log(log_q.shape[1]*log_q.shape[2])
                expected-=logsumexp(raw['log_normal_members'],axis=1)-np.log(3)
                score_error=float(np.max(np.abs(expected-raw['score'])))
                weights=np.exp(log_q.reshape(len(query),-1)-logsumexp(log_q.reshape(len(query),-1),axis=1,keepdims=True))
                repair=(weights[...,None]*generated.reshape(len(query),-1,8)).sum(1)
                repair_error=float(np.max(np.abs(repair-raw['posterior_mean'])))
                assert generation_error<1e-4 and density_error<1e-4 and q_error<1e-6 and score_error<1e-6 and repair_error<1e-6
                summary.append(dict(path=str(path.relative_to(root)),sha256=sha256(path),generated_max_error=generation_error,
                    normal_density_max_error=density_error,corruption_density_max_error=q_error,ratio_max_error=score_error,
                    repair_mean_max_error=repair_error,inverse_max_error=inverse_error,candidates=len(query)))
        del models;torch.cuda.empty_cache()
    record=dict(compact_candidate_scores_recomputed=total,compact_max_error=max_error,full_generation_and_density_replays=summary,
                distinction='All compact scores recomputed from saved component integrals. Listed full bundles independently recompute q from actual generations and replay generations/densities from exact GPU weights and saved latent draws.')
    json_save(directory/'production_equation_audit.json',record);return record
