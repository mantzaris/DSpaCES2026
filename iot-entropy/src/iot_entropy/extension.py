"""Frozen v2 experiment. Models, references, features and calibration are distinct."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch

from .calibration import rank_pvalues
from .classic import gdn_residuals, classic_scores
from .data import SensorData
from .experiment import load_models
from .extension_data import extension_data, new_events, episode_values, verify_target
from .extension_scoring import (MAIN, EXTRA, extract, summaries, score, summarize_scores,
                                primary_localization)
from .features import Scan, prediction_fidelity
from .localization import set_metrics, oracle_overlap
from .reference import BlockBootstrap, issue_reference
from .synthetic import inject, fault_nodes
from .temporal import permutation_entropy, sample_entropy, coarse_grain, window, FEATURES
from .utils import Budget, digest, synchronize, write_json


def floor_from_development(x: torch.Tensor) -> torch.Tensor:
    interval = torch.nanquantile(x,.75,dim=0)-torch.nanquantile(x,.25,dim=0)
    return (.05*interval).nan_to_num(nan=1e-4).clamp_min(1e-4)


def select_estimators(values: np.ndarray, indices: np.ndarray, config: dict,
                      device: str) -> tuple[dict,list]:
    selected = dict(config); rows=[]
    x = torch.as_tensor(np.stack([values[i:i+120] for i in indices]),device=device).permute(0,2,3,1)
    for q,tau in config['permutation_candidates']:
        supports=[]
        for w in config['windows']:
            out = permutation_entropy(x[...,-w:],q,tau,config['minimum_templates'],
                                      config['templates_per_pattern'],config['maximum_tied_fraction'])
            supports.append(float(torch.isfinite(out.value).float().mean()))
            rows.append({'kind':'permutation','q':q,'tau':tau,'window':w,
                'support':supports[-1],'valid_templates_mean':float(out.templates.float().mean()),
                'tied_fraction':float(torch.nanmean(out.tied_fraction)),
                'drop_ties_support':float(torch.isfinite(permutation_entropy(x[...,-w:],q,tau,
                    config['minimum_templates'],config['templates_per_pattern'],1.,True).value).float().mean())})
    candidates=[]
    for q,tau in config['permutation_candidates']:
        support=np.mean([r['support'] for r in rows if r['kind']=='permutation' and r['q']==q and r['tau']==tau])
        candidates.append((-support,q,tau))
    _,selected['permutation_q'],selected['permutation_tau']=min(candidates)
    tolerances=[]
    for delta in config['sample_tolerances']:
        supports=[]
        for w in config['windows']:
            out=sample_entropy(x[...,-w:],config['sample_r'],delta,config['sample_theiler'],
                config['minimum_templates'],config['minimum_B'],config['pair_chunk'],config['series_chunk'])
            supports.append(float(torch.isfinite(out.value).float().mean()))
            rows.append({'kind':'sample','delta':delta,'window':w,'support':supports[-1],
                'A_mean':float(out.A.float().mean()),'B_mean':float(out.B.float().mean()),
                'censored_fraction':float(out.censored.float().mean())})
        tolerances.append((-np.mean(supports),0 if delta==.2 else 1,delta))
    selected['sample_delta']=min(tolerances)[-1]
    return selected,rows


def support_row(observed: dict, prefix: dict) -> list:
    rows=[]
    for w, item in observed['temporal'].items():
        for endpoint in ['current','past']:
            a=item[endpoint]
            rows.append({**prefix,'window':w,'endpoint':endpoint,
                'permutation_available':float(torch.isfinite(a['values'][...,0]).float().mean()),
                'sample_available':float(torch.isfinite(a['values'][...,1]).float().mean()),
                'conventional_available':float(torch.isfinite(a['values'][...,2:]).float().mean()),
                'pe_templates':float(a['pe_templates'].float().mean()),
                'se_templates':float(a['se_templates'].float().mean()),
                'A':float(a['A'].float().mean()),'B':float(a['B'].float().mean()),
                'tied_fraction':float(torch.nanmean(a['ties'])),
                'censored_fraction':float(a['censored'].float().mean()),
                'undefined_fraction':float((a['B']==0).float().mean()),
                'flat_fraction':float(a['flat'].float().mean())})
    return rows


def fidelity(observed: dict, generated: dict, summary: dict,
             raw: torch.Tensor, samples: torch.Tensor) -> dict:
    result=prediction_fidelity(raw,samples)
    actual=observed['spatial'].values[0]
    ref=summary['spatial']
    for k,label in [(0,'spatial_entropy'),(1,'spatial_change')]:
        valid=torch.isfinite(actual[:,k])&ref.enough[:,k]
        result[label+'_support']=int(valid.sum())
        result[label+'_coverage90']=float(((actual[:,k]>=ref.low[:,k])&(actual[:,k]<=ref.high[:,k]))[valid].float().mean())
        result[label+'_width90']=float((ref.high[:,k]-ref.low[:,k])[valid].mean())
    errors=[]
    for a,b in zip(observed['spatial'].correlations,ref.matrices):
        errors.append((a[0]-b).square().flatten())
    result['correlation_element_rmse']=float(torch.nanmean(torch.cat(errors)).sqrt())
    for w,item in observed['temporal'].items():
        ref=summary['temporal'][w]; x=item['u'][0]
        for f,label in enumerate(FEATURES):
            valid=torch.isfinite(x[...,f,0])&ref['enough'][...,f,0]
            low,high=ref['low'][...,f,0],ref['high'][...,f,0]
            result[f'{label}_{w}_support']=int(valid.sum())
            result[f'{label}_{w}_coverage90']=float(((x[...,f,0]>=low)&(x[...,f,0]<=high))[valid].float().mean())
            result[f'{label}_{w}_width90']=float((high-low)[valid].mean())
            result[f'{label}_{w}_mae']=float((x[...,f,0]-ref['center'][...,f,0]).abs()[valid].mean())
        p=item['current']['patterns'][0]
        gp=generated['temporal'][w]['current']['patterns'].mean(0)
        valid=(item['current']['pe_templates'][0]>=30)&(generated['temporal'][w]['current']['pe_templates']>=30).all(0)
        result[f'ordinal_tv_{w}']=float((.5*(p-gp).abs().sum(-1))[valid].mean())
        result[f'ordinal_tv_{w}_support']=int(valid.sum())
    return result


@torch.no_grad()
def run(root: Path, name: str, seed: int, original_config: dict, budget: Budget,
        device: str = 'cuda') -> dict:
    torch.set_num_threads(4)
    directory=root/'experiments/extension-v2'/f'{name}-{seed}'
    if (directory/'status.json').exists():
        return json.loads((directory/'status.json').read_text())
    directory.mkdir(parents=True,exist_ok=True)
    started=time.monotonic(); timings=[]; support=[]; fid=[]; multis=[]
    # Record even a failed run; future resumes count rather than erase its runtime.
    attempt=len(list(directory.glob('attempt-*.json')))
    attempt_path=directory/f'attempt-{attempt}.json'
    config=dict(original_config)
    try:
        budget.check()
        data,bases,lineage=extension_data(root,name,config,device)
        write_json(directory/'data-lineage.json',lineage)
        values=data.standardized
        model,gdn=load_models(data,config,seed,root/'experiments/full',device)
        model_path=root/'experiments/full/checkpoints'/f'{name}-diffusion-physical-{seed}.pt'
        write_json(directory/'models.json',{'diffusion_sha256':digest(model_path),
            'gdn_sha256':digest(root/'experiments/full/checkpoints'/f'{name}-gdn-physical-{seed}.pt'),
            'original_training_configuration':digest(root/'configs/full.json')})
        bootstrap=BlockBootstrap(data,48,120,device)
        dev_indices=data.issuance_indices(1,48,120,168)
        dev_indices=dev_indices[np.linspace(0,len(dev_indices)-1,min(config['development_units'],len(dev_indices)),dtype=int)]
        config,selection=select_estimators(values,dev_indices,config,device)
        scan=Scan(data.adjacency,data.coordinates,data.channels,config,device)
        write_json(directory/'groups.json',scan.records)
        write_json(directory/'estimator-selection.json',selection)
        dev=[]; gdn_dev=[]
        for start in dev_indices:
            verify_target(data,int(start),48,120,1)
            raw=torch.as_tensor(values[start:start+120],device=device)
            dev.append(extract(raw,scan,config))
            gdn_dev.append(gdn_residuals(gdn,values[start-48:start+120],48,device).mean(0))
            support.extend(support_row(dev[-1],{'split':'development','target_start':int(start)}))
            for w in [24,48,96]:
                for scale in config['scales']:
                    x=coarse_grain(raw[-w:].permute(1,2,0),scale)
                    a=window(x,config)
                    multis.append({'split':'development','target_start':int(start),'window':w,'scale':scale,
                        'permutation_support':float(torch.isfinite(a['values'][...,0]).float().mean()),
                        'sample_support':float(torch.isfinite(a['values'][...,1]).float().mean()),
                        'conventional_support':float(torch.isfinite(a['values'][...,2:]).float().mean()),
                        'permutation_mean':float(torch.nanmean(a['values'][...,0])),
                        'sample_mean':float(torch.nanmean(a['values'][...,1])),
                        'templates_mean':float(a['pe_templates'].float().mean()),
                        'B_mean':float(a['B'].float().mean())})
        floors={'spatial':floor_from_development(torch.cat([z['spatial'].values for z in dev])),
                'temporal':{w:floor_from_development(torch.cat([z['temporal'][w]['u'] for z in dev])) for w in config['windows']}}
        gd=torch.stack(gdn_dev); gdcenter=torch.nanmedian(gd,dim=0).values
        gdscale=(torch.nanquantile(gd,.75,dim=0)-torch.nanquantile(gd,.25,dim=0)).clamp_min(.01)
        spatial_dev=torch.cat([z['spatial'].values for z in dev])
        spcenter=torch.nanmedian(spatial_dev,dim=0).values
        spscale=(torch.nanquantile(spatial_dev,.75,dim=0)-torch.nanquantile(spatial_dev,.25,dim=0)).clamp_min(.001)
        floor_payload={'spatial':floors['spatial'].cpu().numpy(),'gdn_center':gdcenter.cpu().numpy(),
                       'gdn_scale':gdscale.cpu().numpy()}
        floor_payload.update({f'temporal_{w}':v.cpu().numpy() for w,v in floors['temporal'].items()})
        np.savez_compressed(directory/'development-parameters.npz',**floor_payload)
        refs=['bootstrap','diffusion']
        cache=root/'experiments/extension-v2/cache'/f'{name}-{seed}'
        cache.mkdir(parents=True,exist_ok=True)
        reference_manifest=[]

        def reference(start: int, split: int, ref: str, raw: torch.Tensor) -> tuple:
            budget.check(); verify_target(data,start,48,120,split)
            t=time.monotonic()
            draw_seed=700000+seed*100000+start
            path=cache/f'{start}-{ref}.npy'
            if path.exists():
                samples=torch.as_tensor(np.load(path),device=device)
                reused=True
            else:
                samples=issue_reference(model,data,values,start,120,config,device,ref,bootstrap,draw_seed)
                # Saved joint trajectories permit identical future measurements.
                np.save(path,samples.cpu().numpy())
                reused=False
            synchronize(device); gen_seconds=time.monotonic()-t
            reference_manifest.append({'target_start':start,'issue_index':start-1,
                'decision_index':start+119,'context_start':start-48,'split':split,'reference':ref,
                'seed':draw_seed,'path':str(path.relative_to(root)), 'shape':list(samples.shape),
                'sha256':digest(path),'reused':reused})
            samples=samples.masked_fill(~torch.isfinite(raw)[None],float('nan'))
            t=time.monotonic(); generated=extract(samples,scan,config)
            summary=summaries(generated,floors,config)
            synchronize(device)
            timings.append({'target_start':start,'reference':ref,'split':split,
                            'generation_seconds':gen_seconds,'measure_summary_seconds':time.monotonic()-t})
            return samples,generated,summary

        # Shared development effort: localization only, no test truth or thresholds.
        tuning={(f,k):[] for f in config['top_fractions'] for k in config['localization_budgets']}
        for j,start0 in enumerate(dev_indices):
            start=int(start0); raw=torch.as_tensor(values[start:start+120],device=device)
            nodes=fault_nodes(data.adjacency,config['fault_sizes'][j%2],99300+j,bool(j%2))
            kind=['copy','noise','drift','delay'][j%4]
            changed=inject(raw.cpu().numpy(),nodes,24,96,kind,1.,99400+j)
            altered=extract(torch.as_tensor(changed,device=device),scan,config)
            for ref in refs:
                samples,generated,summary=reference(start,1,ref,raw)
                fid.append({'split':'development','reference':ref,'target_start':start,
                            **fidelity(dev[j],generated,summary,raw,samples)})
                for fraction in config['top_fractions']:
                    scored=score(altered,generated,summary,scan,floors,config,fraction)
                    names,_,_,rank=summarize_scores(scored,scan,len(data.node_ids))
                    for k in config['localization_budgets']:
                        for family in ['T','TB','ST','B','BST']:
                            prediction=rank[names.index(family),primary_localization(family),:k].tolist()
                            tuning[fraction,k].append(set_metrics(prediction,nodes)['iou'])
                del samples,generated,summary
        selected=min([(-float(np.mean(v)),f,k) for (f,k),v in tuning.items()])
        fraction,loc_budget=selected[1:]
        config.update(top_fraction=fraction,localization_budget=loc_budget)
        write_json(directory/'configuration.json',config)
        write_json(directory/'development-selection.json',{'indices':dev_indices,
            'choices':[{'fraction':f,'budget':k,'mean_iou':np.mean(v)} for (f,k),v in tuning.items()],
            'selected_fraction':fraction,'selected_budget':loc_budget,
            'selection':'pooled development localization across T/TB/ST/B/BST and both references'})
        write_json(directory/'multiscale-development.json',multis)

        names=MAIN+EXTRA+['common/'+k for k in MAIN]
        all_methods=[r+'/'+n for r in refs for n in names]+['causal/GDN']
        cal_indices=data.issuance_indices(2,48,120,168)
        calibration=[]; cal_availability=[]
        for start0 in cal_indices:
            start=int(start0); raw=torch.as_tensor(values[start:start+120],device=device)
            actual=extract(raw,scan,config); maxima=[]; availability=[]
            support.extend(support_row(actual,{'split':'calibration','target_start':start}))
            for ref in refs:
                samples,generated,summary=reference(start,2,ref,raw)
                scored=score(actual,generated,summary,scan,floors,config,fraction)
                _,m,a,_=summarize_scores(scored,scan,len(data.node_ids));maxima.extend(m);availability.extend(a)
                del samples,generated,summary
            gd=gdn_residuals(gdn,values[start-48:start+120],48,device)
            gs=classic_scores(raw,scan,spcenter,spscale,gd,gdcenter,gdscale)['gdn']
            vector=gs.cpu().numpy();maxima.append(float(np.max(np.where(np.isfinite(vector),vector,-np.inf))))
            availability.append(np.isfinite(vector).mean())
            calibration.append(maxima);cal_availability.append(availability)
        calibration=np.asarray(calibration)
        np.savez_compressed(directory/'calibration.npz',scores=calibration,availability=cal_availability,
                            target_start=cal_indices,methods=np.asarray(all_methods))
        write_json(directory/'calibration.json',{'n':len(calibration),'minimum_p':1/(len(calibration)+1),
            'alpha':config['primary_alpha'],'all_abstained_units':np.isneginf(calibration).sum(0),
            'methods':all_methods,'thresholds':{m:float(np.sort(calibration[:,j])[min(len(calibration)-1,
                int(np.ceil((1-config['primary_alpha'])*(len(calibration)+1)))-1)]) for j,m in enumerate(all_methods)},
            'rule':'Rank p; no threshold selected using test controls; each family calibrated separately.'})
        events=new_events(data,config,bases)
        for e in events:
            e['oracle_group_iou']=oracle_overlap(scan.groups,e['nodes']) if e['is_fault'] else None
        write_json(directory/'events.json',events)
        times=np.arange(167,312,12)
        shape=(len(events),len(times),len(all_methods))
        scores=np.full(shape,-np.inf,np.float32);available=np.zeros(shape,np.float32)
        ranks=np.zeros((*shape,3,24),np.int16)
        # Per-sensor feature/support arrays are compact and retained for all episodes.
        feature_shape=(len(events),len(times),len(config['windows']),len(data.node_ids),len(data.channels))
        obs_features=np.full((*feature_shape,len(FEATURES),2),np.nan,np.float32)
        support_names=['pe_templates','se_templates','A','B','pairs','ties','censored','flat']
        obs_support=np.full((*feature_shape,2,len(support_names)),np.nan,np.float32)
        spatial_values=np.full((len(events),len(times),len(scan.records),10),np.nan,np.float32)
        spatial_counts=np.zeros((len(events),len(times),len(scan.records)),np.int16)
        quality=np.zeros((len(events),len(times),2),np.float32)
        for base_index,base in enumerate(bases):
            ids=[i for i,e in enumerate(events) if e['base']==base_index]
            clean=values[base[0]:base[1]]
            altered={i:episode_values(data,values,base,events[i],config,device) for i in ids}
            replay={'dataset':name,'seed':seed,'base':base_index,'times':times.tolist(),
                    'channels':data.channels,'node_ids':data.node_ids.tolist(),
                    'coordinates':data.coordinates.tolist(),'adjacency':data.adjacency.tolist(),
                    'model_sha256':digest(model_path),'groups':scan.records,'frames':[]}
            for ti,end0 in enumerate(times):
                budget.check(); t=time.monotonic(); end=int(end0)
                start=base[0]+end-119
                assert start-1 < base[0]+config['onset']
                raw=torch.as_tensor(clean[end-119:end+1],device=device)
                reference_sets={}
                clean_features=extract(raw,scan,config)
                for ref in refs:
                    samples,generated,summary=reference(start,3,ref,raw)
                    reference_sets[ref]=(samples,generated,summary)
                    if ti in [0,8,12]:
                        fid.append({'split':'test','base':base_index,'reference':ref,'target_start':start,
                                    **fidelity(clean_features,generated,summary,raw,samples)})
                for i in ids:
                    actual_raw=torch.as_tensor(altered[i][end-119:end+1],device=device)
                    actual=extract(actual_raw,scan,config)
                    for wi,w in enumerate(config['windows']):
                        a=actual['temporal'][w]
                        obs_features[i,ti,wi]=a['u'][0].cpu().numpy()
                        for ep,endpoint in enumerate(['current','past']):
                            for sj,key in enumerate(support_names):
                                obs_support[i,ti,wi,:,:,ep,sj]=a[endpoint][key][0].cpu().numpy()
                    spatial_values[i,ti]=actual['spatial'].values[0].cpu().numpy()
                    spatial_counts[i,ti]=actual['spatial'].count[0].cpu().numpy()
                    quality[i,ti]=[float((~torch.isfinite(actual_raw)).float().mean()),
                                    float(actual['temporal'][96]['current']['flat'].float().mean())]
                    support.extend(support_row(actual,{'split':'test','event':i,'time':end,'base':base_index}))
                    for ri,ref in enumerate(refs):
                        samples,generated,summary=reference_sets[ref]
                        if events[i]['kind']=='dropout':
                            # Additional fault mask must affect all reference measurements too.
                            masked=samples.masked_fill(~torch.isfinite(actual_raw)[None],float('nan'))
                            generated=extract(masked,scan,config); summary=summaries(generated,floors,config)
                        scored=score(actual,generated,summary,scan,floors,config,fraction)
                        _,m,a,r=summarize_scores(scored,scan,len(data.node_ids))
                        sl=slice(ri*len(names),(ri+1)*len(names))
                        scores[i,ti,sl]=m; available[i,ti,sl]=a; ranks[i,ti,sl]=r
                        if seed==17 and base_index==0 and i==ids[0] and ref=='diffusion':
                            replay['event']=events[i]
                            replay['frames'].append({'decision_index':base[0]+end,'issue_index':start-1,
                                'decision_timestamp_ns':int(data.timestamps[base[0]+end]),
                                'issue_timestamp_ns':int(data.timestamps[start-1]),'event_time':end,
                                'raw':actual_raw[-96:].cpu().numpy(),'raw_low':torch.nanquantile(samples[:,-96:],.05,dim=0).cpu().numpy(),
                                'raw_high':torch.nanquantile(samples[:,-96:],.95,dim=0).cpu().numpy(),
                                'spatial':actual['spatial'].values[0].cpu().numpy(),
                                'spatial_low':summary['spatial'].low.cpu().numpy(),
                                'spatial_high':summary['spatial'].high.cpu().numpy(),
                                'spatial_center':summary['spatial'].center.cpu().numpy(),
                                'spatial_rows':actual['spatial'].count[0].cpu().numpy(),
                                'groups':{k:scored['groups'][k].cpu().numpy() for k in MAIN},
                                'sensor':{k:scored['direct'][k].cpu().numpy() for k in MAIN},
                                'temporal':{str(w):{'values':actual['temporal'][w]['u'][0].cpu().numpy(),
                                    'low':summary['temporal'][w]['low'].cpu().numpy(),
                                    'high':summary['temporal'][w]['high'].cpu().numpy(),
                                    'center':summary['temporal'][w]['center'].cpu().numpy(),
                                    'signed':scored['signed'][w].cpu().numpy(),
                                    'support':{k:actual['temporal'][w]['current'][k][0].cpu().numpy() for k in support_names}}
                                    for w in config['windows']}})
                    gd=gdn_residuals(gdn,altered[i][:end+1],48,device)
                    gs=classic_scores(actual_raw,scan,spcenter,spscale,gd,gdcenter,gdscale)['gdn'].cpu().numpy()
                    scores[i,ti,-1]=float(np.max(np.where(np.isfinite(gs),gs,-np.inf)))
                    available[i,ti,-1]=np.isfinite(gs).mean()
                    from .localization import participation
                    ranking=np.argsort(-participation(gs,scan.groups,len(data.node_ids)),kind='stable')[:24]
                    ranks[i,ti,-1]=np.stack([ranking]*3)
                synchronize(device)
                timings.append({'base':base_index,'time':end,'stage':'complete_test_tick',
                                'seconds':time.monotonic()-t,'events':len(ids)})
                write_json(attempt_path,{'elapsed_seconds':time.monotonic()-started,'complete':False})
            if replay['frames']:
                replay['calibration']={m:calibration[:,all_methods.index('diffusion/'+m)] for m in MAIN}
                replay['localization_budget']=loc_budget
                write_json(directory/'replay.json',replay)
            print(json.dumps({'dataset':name,'seed':seed,'completed_base':base_index,
                              'elapsed_seconds':time.monotonic()-started}),flush=True)
        pvalues=np.stack([rank_pvalues(calibration[:,j],scores[:,:,j]) for j in range(len(all_methods))],-1)
        np.savez_compressed(directory/'predictions.npz',scores=scores,pvalues=pvalues.astype('float32'),
            availability=available,rankings=ranks,times=times,methods=np.asarray(all_methods),quality=quality)
        np.savez_compressed(directory/'measurements.npz',temporal=obs_features,support=obs_support,
            spatial=spatial_values,spatial_counts=spatial_counts,feature_names=np.asarray(FEATURES),
            support_names=np.asarray(support_names),windows=config['windows'])
        write_json(directory/'support.json',support);write_json(directory/'fidelity.json',fid)
        write_json(directory/'timings.json',timings);write_json(directory/'references.json',reference_manifest)
        synchronize(device)
        status={'complete':True,'dataset':name,'seed':seed,'events':len(events),'faults':72,
            'blocks':len(bases),'calibration_units':len(calibration),'methods':all_methods,
            'elapsed_seconds':time.monotonic()-started,'peak_gpu_bytes':torch.cuda.max_memory_allocated(),
            'protocol_sha256':digest(root/'docs/extension-protocol.md'),
            'configuration_sha256':digest(directory/'configuration.json')}
        write_json(directory/'status.json',status)
        return status
    finally:
        write_json(attempt_path,{'elapsed_seconds':time.monotonic()-started,
                               'complete':(directory/'status.json').exists()})
