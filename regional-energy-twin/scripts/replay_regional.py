"""Bounded retrospective household/regional twin and matched-input solver replay."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import resource
import time
import numpy as np
import pandas as pd
from scipy.linalg import cho_factor,cho_solve,cho_solve_banded,eigh
from evidence_fusion.regional_data import load_panel,slots,masked_provider_statistics
from evidence_fusion.regional_solver import (fixed_objective,components,assemble,joint_basis,
    Family,batched_pcg,banded_factor,information_smoother,accuracy)


def torch_pcg(torch,a,b,x=None,q=None,d=None,tol=1e-7,maxiter=400):
    x=torch.zeros_like(b) if x is None else x.clone()
    def mv(v): return (a@v.unsqueeze(-1)).squeeze(-1)
    def pre(r): return r/a.diagonal(dim1=-2,dim2=-1) if q is None else ((r@q)/d)@q.T
    r=b-mv(x); z=pre(r); p=z.clone(); rz=(r*z).sum(1)
    threshold=tol*torch.where(torch.linalg.vector_norm(b,dim=1)>0,torch.linalg.vector_norm(b,dim=1),1.)
    active=torch.linalg.vector_norm(r,dim=1)>threshold
    steps=torch.zeros(len(b),device=b.device,dtype=torch.int64)
    for _ in range(maxiter):
        if not bool(active.any()): break
        ap=mv(p); den=(p*ap).sum(1)
        alpha=torch.where(active&(den>0),rz/torch.where(den>0,den,1.),0.)
        x+=alpha[:,None]*p; r-=alpha[:,None]*ap; steps+=active
        active=torch.linalg.vector_norm(r,dim=1)>threshold
        z=pre(r); nxt=(r*z).sum(1)
        beta=torch.where(active&(rz!=0),nxt/torch.where(rz!=0,rz,1.),0.)
        p=z+beta[:,None]*p; p[~active]=0; rz=nxt
    return x,steps


def profiles(cfg):
    g=cfg['provider_groups']; rng=np.random.default_rng(cfg['seed'])
    w=[np.ones(g),np.zeros(g),np.arange(g)%2,np.ones(g)*.5]
    while len(w)<cfg['provider_profiles']:
        w.append(rng.choice([0.,.25,.5,1.],size=g))
    return np.array(w)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--gpu',action='store_true'); args=parser.parse_args()
    started=time.perf_counter(); cfg=json.loads(Path('configs/regional_pilot.json').read_text())
    out=Path('results/regional/smoke' if args.smoke else 'results/regional/replay'); out.mkdir(parents=True,exist_ok=True)
    snapshots=Path('data/regional/snapshots'); snapshots.mkdir(exist_ok=True)
    model=np.load('data/regional/model/model.npz',allow_pickle=False)
    loadings=model['loadings']; transition=model['transition']; d=loadings.shape[1]
    length=cfg['window_steps']; n=d*length; g=cfg['provider_groups']; lam=cfg['regularization']
    prep_start=time.perf_counter()
    y,times,meters,_=load_panel('development',model['meters'])
    parsed_seconds=time.perf_counter()-prep_start
    origins=[]
    for week in cfg['development_weeks']:
        # Fixed origins 12 hours into evenly spaced days of the declared week.
        start=pd.Timestamp(week)+pd.Timedelta(hours=12)
        origins.extend(start+pd.Timedelta(minutes=30*int(i)) for i in np.linspace(0,6*48,cfg['origins_per_week']))
    w=profiles(cfg)
    if args.smoke: origins=origins[:1]; w=w[:2]
    frozen=dict(config=cfg,origins=[str(x) for x in origins],profiles=w.tolist(),households=len(meters),
                config_sha256=hashlib.sha256(Path('configs/regional_pilot.json').read_bytes()).hexdigest(),
                model_sha256=hashlib.sha256(Path('data/regional/model/model.npz').read_bytes()).hexdigest(),
                timing_started=False)
    (out/'frozen_manifest.json').write_text(json.dumps(frozen,indent=2)+'\n')
    basis_start=time.perf_counter()
    center=np.zeros(n); prior=np.zeros(d)
    c0,b0=fixed_objective(transition,model['process_var'],model['prior_var'],length,center,prior,lam)
    training_blocks=np.zeros((g,length,d,d))
    for group in range(g):
        ix=model['groups']==group; h=loadings[ix]
        training_blocks[group]=h.T@(h/model['noise'][ix,None])
    design_cs=np.concatenate([c0[None],components(training_blocks)])
    basis={}; basis_cost={}
    t=time.perf_counter(); basis['identity']=np.eye(n); basis_cost['identity']=time.perf_counter()-t
    t=time.perf_counter(); basis['reference_eigen']=eigh(design_cs.sum(0))[1]; basis_cost['reference_eigen']=time.perf_counter()-t
    t=time.perf_counter(); basis['rjd']=joint_basis(design_cs,cfg['seed'],cfg['rjd_trials']); basis_cost['rjd']=time.perf_counter()-t
    setup_seconds=time.perf_counter()-basis_start
    torch=None; hardware=dict(cpu=platform.processor(),platform=platform.platform(),threads=cfg['cpu_threads'])
    cuda_init=0.
    if args.gpu:
        t=time.perf_counter(); import torch
        torch.set_num_threads(cfg['cpu_threads']); torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        if not torch.cuda.is_available(): raise RuntimeError('GPU requested but unavailable')
        torch.cuda.set_per_process_memory_fraction(min(24*1024**3/torch.cuda.get_device_properties(0).total_memory,.8))
        torch.zeros(1,device='cuda'); torch.cuda.synchronize(); cuda_init=time.perf_counter()-t
        hardware.update(gpu=torch.cuda.get_device_name(),vram_bytes=torch.cuda.get_device_properties(0).total_memory,
                        torch=torch.__version__,cuda=torch.version.cuda)
    errors=[]; costs=[]; forecasts=[]; certificates=[]; snapshot_manifest=[]
    masks_seen=set(); factors={}; bandfactors={}; gpu_factors={}
    prior_state=np.zeros(d); previous_origin=None
    output_tolerance=float(model['typical'])*cfg['regional_output_fraction_tolerance']
    peak=float(model['peak'])
    for origin_id,origin in enumerate(origins):
        origin_start=time.perf_counter(); pos=int(times.get_loc(origin)); window=slice(pos-length+1,pos+1)
        measurement_start=time.perf_counter()
        baseline=model['profile'][slots(times[window])]
        residual=(y[window]-baseline)/model['scale']; mask=np.isfinite(residual)
        # The provider API receives only each group's available cells. The offline
        # evaluator keeps full outcomes outside solver inputs.
        cb,bb=masked_provider_statistics(residual,mask,loadings,model['noise'],model['groups'],np.ones(g))
        native_hash=hashlib.sha256(mask.tobytes()).hexdigest()
        fresh=native_hash not in masks_seen; masks_seen.add(native_hash)
        if previous_origin is not None:
            gap=int((origin-previous_origin)/pd.Timedelta(minutes=30))
            prior_state=np.linalg.matrix_power(transition,gap-length+1)@prior_state if gap>=length else np.zeros(d)
        prior_trajectory=np.vstack([np.linalg.matrix_power(transition,t)@prior_state for t in range(length)]).reshape(-1)
        c0,b0=fixed_objective(transition,model['process_var'],model['prior_var'],length,prior_trajectory,prior_state,lam)
        cs=np.concatenate([c0[None],components(cb)]); bs=np.vstack([b0,bb.reshape(g,n)])
        # Immutable source-access envelopes: same target/cutoff, native mask digest,
        # physical-ID model hash. Revisions are monotonically increasing snapshots.
        payload=json.dumps(dict(origin=str(origin),cutoff=str(origin),model=frozen['model_sha256'],
                                revision=origin_id,mask_digest=native_hash,groups=list(range(g))))
        json.loads(payload)
        measure_seconds=time.perf_counter()-measurement_start
        t=time.perf_counter(); matrices,rhs,augmented=assemble(cs,bs,w,lam); assembly=time.perf_counter()-t
        t=time.perf_counter(); keys=[hashlib.sha256(a.tobytes()).hexdigest() for a in matrices]
        key_seconds=time.perf_counter()-t
        t=time.perf_counter(); reference=[]; cold=0
        for a,b,key in zip(matrices,rhs,keys):
            if key not in factors:
                factors[key]=cho_factor(a,lower=True,check_finite=False); cold+=1
            reference.append(cho_solve(factors[key],b,check_finite=False))
        reference=np.asarray(reference); chol_seconds=time.perf_counter()-t
        methods={'cpu_cholesky':reference}; method_times={'cpu_cholesky':chol_seconds}
        t=time.perf_counter(); warm=np.array([cho_solve(factors[key],b,check_finite=False) for key,b in zip(keys,rhs)])
        warm_chol=time.perf_counter()-t
        t=time.perf_counter(); sol=[]
        for a,b,key in zip(matrices,rhs,keys):
            if key not in bandfactors: bandfactors[key]=banded_factor(a,d)
            sol.append(cho_solve_banded((bandfactors[key],True),b,check_finite=False))
        methods['cpu_banded']=np.array(sol); method_times['cpu_banded']=time.perf_counter()-t
        t=time.perf_counter(); methods['cpu_information_smoother']=np.array([information_smoother(a,b,d) for a,b in zip(matrices,rhs)])
        method_times['cpu_information_smoother']=time.perf_counter()-t
        t=time.perf_counter(); methods['cpu_pcg'],_=batched_pcg(matrices,rhs); method_times['cpu_pcg']=time.perf_counter()-t
        families={}; ds={}; init={}; family_times={}; init_times={}; audit_times={}; fallback_counts={}
        family_stages={}
        for name,q in basis.items():
            t=time.perf_counter(); fam=Family(cs,q,lam,cfg['certificate_blocks']); families[name]=fam
            certs=[fam.certificate(a) for a in augmented]; ds[name]=np.array([x[0] for x in certs])
            family_times[name]=time.perf_counter()-t
            family_stages[name]=dict(transform_seconds=fam.transform_seconds,global_gram_seconds=fam.global_gram_seconds,
                                    block_gram_seconds=fam.block_gram_seconds,
                                    global_queries_seconds=sum(x[1]['global_query_seconds'] for x in certs),
                                    block_queries_seconds=sum(x[1]['block_query_seconds'] for x in certs))
            t=time.perf_counter(); init[name]=np.array([fam.initialize(b,a) for b,a in zip(rhs,augmented)])
            init_times[name]=time.perf_counter()-t
            t=time.perf_counter()
            z,steps=batched_pcg(matrices,rhs,x=init[name],preconditioner=(q,ds[name]))
            correction_time=time.perf_counter()-t
            t=time.perf_counter()
            fallback=0
            for k in range(len(w)):
                metric=accuracy(matrices[k],rhs[k],z[k],reference[k])
                if metric['relative_residual']>1e-5 or metric['weighted_relative_error']>1e-4:
                    z[k]=cho_solve(factors[keys[k]],rhs[k],check_finite=False); fallback+=1
            methods['cpu_'+name+'_corrected']=z
            fallback_counts['cpu_'+name+'_corrected']=fallback
            audit_times[name]=time.perf_counter()-t
            method_times['cpu_'+name+'_corrected']=correction_time+init_times[name]+audit_times[name]+family_times[name]
            for k,((diagonal,cert),a,b) in enumerate(zip(certs,augmented,rhs)):
                h=(q.T@b)/np.sqrt(diagonal); delta=cert['delta']
                j=np.zeros(n); j[-d:]=(model['scale'][:,None]*loadings).sum(0)@np.linalg.matrix_power(transition,12)
                multiplier=np.linalg.norm((q.T@j)/np.sqrt(diagonal))
                degree=cfg['max_correction_degree']
                bound=delta**(degree+1)/(1-delta)*np.linalg.norm(h)*multiplier if delta<1 else np.inf
                # Execute the polynomial itself when the family test is informative.
                poly_start=time.perf_counter()
                poly,ph=fam.polynomial(b,a,degree) if delta<1 else (init[name][k],h)
                polynomial_seconds=time.perf_counter()-poly_start
                actual=abs(j@(poly-reference[k]))
                exact_delta=None
                if origin_id==0 and k<4:
                    e=np.einsum('g,gij->ij',a,fam.e)
                    f=e/np.sqrt(diagonal[:,None]*diagonal[None,:])
                    exact_delta=float(np.max(abs(eigh(f,eigvals_only=True))))
                    if exact_delta>delta*(1+1e-9)+1e-12:
                        raise AssertionError('Family norm audit failed')
                certificates.append(dict(origin=origin_id,profile=k,basis=name,**cert,
                    spectral_delta_audit=exact_delta,
                    polynomial_seconds=polynomial_seconds,
                    output_bound_kwh=bound,polynomial_output_error_kwh=float(actual),degree=degree,
                    conclusive=bool(delta<1 and bound<=output_tolerance),fallback_count_batch=fallback,
                    initial_relative_residual=accuracy(matrices[k],b,init[name][k],reference[k])['relative_residual']))
        if torch is not None:
            t=time.perf_counter(); ta=torch.as_tensor(matrices,device='cuda'); tb=torch.as_tensor(rhs,device='cuda')
            torch.cuda.synchronize(); transfer=time.perf_counter()-t
            t=time.perf_counter()
            tq=torch.as_tensor(basis['rjd'],device='cuda'); td=torch.as_tensor(ds['rjd'],device='cuda')
            tx=torch.as_tensor(init['rjd'],device='cuda'); torch.cuda.synchronize(); rjd_transfer=time.perf_counter()-t
            t=time.perf_counter()
            # Cache and batch only genuinely new matrices; all repeats get factor reuse.
            unseen=[i for i,key in enumerate(keys) if key not in gpu_factors]
            if unseen:
                factor_batch=torch.linalg.cholesky(ta[unseen]); torch.cuda.synchronize()
                for ix,factor in zip(unseen,factor_batch): gpu_factors[keys[ix]]=factor
            tf=torch.stack([gpu_factors[key] for key in keys])
            gx=torch.cholesky_solve(tb.unsqueeze(-1),tf).squeeze(-1); torch.cuda.synchronize()
            kernel=time.perf_counter()-t; t=time.perf_counter(); methods['gpu_cholesky']=gx.cpu().numpy(); torch.cuda.synchronize(); back=time.perf_counter()-t
            method_times['gpu_cholesky']=transfer+kernel+back
            costs.append(dict(origin=origin_id,method='gpu_cholesky_kernel',seconds=kernel,queries=len(w),complete_seconds=None))
            t=time.perf_counter(); gx=torch.cholesky_solve(tb.unsqueeze(-1),tf).squeeze(-1); torch.cuda.synchronize(); gpu_warm=time.perf_counter()-t
            t=time.perf_counter(); warm_host=gx.cpu().numpy(); torch.cuda.synchronize(); warm_back=time.perf_counter()-t
            for name,initial,qq,dd in [('gpu_pcg',None,None,None),('gpu_rjd_corrected',tx,tq,td)]:
                t=time.perf_counter(); gx,steps=torch_pcg(torch,ta,tb,initial,qq,dd); torch.cuda.synchronize()
                kernel=time.perf_counter()-t; t=time.perf_counter(); arr=gx.cpu().numpy(); torch.cuda.synchronize(); back=time.perf_counter()-t
                audit_start=time.perf_counter()
                fallback=0
                for k in range(len(w)):
                    metric=accuracy(matrices[k],rhs[k],arr[k],reference[k])
                    if metric['relative_residual']>1e-5 or metric['weighted_relative_error']>1e-4:
                        arr[k]=cho_solve(factors[keys[k]],rhs[k],check_finite=False); fallback+=1
                audit=time.perf_counter()-audit_start
                fallback_counts[name]=fallback
                methods[name]=arr; method_times[name]=transfer+kernel+back+audit+(family_times['rjd']+init_times['rjd']+rjd_transfer if 'rjd' in name else 0)
                costs.append(dict(origin=origin_id,method=name+'_kernel',seconds=kernel,queries=len(w),complete_seconds=None))
            costs.append(dict(origin=origin_id,method='gpu_cholesky_cached',seconds=gpu_warm,queries=len(w),
                              complete_seconds=measure_seconds+assembly+key_seconds+transfer+gpu_warm+warm_back))
        prediction_start=time.perf_counter()
        household_predictions=np.empty((len(w),len(cfg['horizons_steps']),len(meters)))
        for hi,horizon in enumerate(cfg['horizons_steps']):
            base=model['profile'][slots(times[[pos+horizon]])[0]]
            household_predictions[:,hi]=base+((reference[:,-d:]@np.linalg.matrix_power(transition,horizon).T)@loadings.T)*model['scale']
        group_predictions=np.stack([household_predictions[:,:,model['groups']==group].sum(2) for group in range(g)],axis=-1)
        prediction_seconds=time.perf_counter()-prediction_start
        # Score only the declared development targets. All sums use precisely the
        # observed target support, reported explicitly; no expansion to missing homes.
        t=time.perf_counter()
        for k in range(len(w)):
            for name,sol in methods.items():
                metric=accuracy(matrices[k],rhs[k],sol[k],reference[k]); fail=metric['relative_residual']>1e-5 or metric['weighted_relative_error']>1e-4
                errors.append(dict(origin=origin_id,profile=k,method=name,**metric,failed=bool(fail)))
            for horizon in cfg['horizons_steps']:
                future=pos+horizon; observed=np.isfinite(y[future]); observed_count=int(observed.sum())
                target=y[future,observed].astype(float); base=model['profile'][slots(times[[future]])[0]]
                propagate=np.linalg.matrix_power(transition,horizon)
                full_j=(model['scale'][:,None]*loadings).sum(0)@propagate
                support_j=(model['scale'][observed,None]*loadings[observed]).sum(0)@propagate
                predicted=base+model['scale']*(loadings@(propagate@reference[k,-d:]))
                seasonal=base; no_new=base+model['scale']*(loadings@(np.linalg.matrix_power(transition,length-1+horizon)@prior_state))
                for name,pred in [('exact_twin',predicted),('seasonal',seasonal),('no_new_observation',no_new)]:
                    err=pred[observed]-target
                    forecasts.append(dict(origin=origin_id,cutoff=str(origin),target=str(times[future]),profile=k,horizon=horizon,
                        method=name,observed_households=observed_count,cohort_households=len(meters),
                        observed_sum_kwh=float(target.sum()),prediction_observed_support_kwh=float(pred[observed].sum()),
                        prediction_full_cohort_kwh=float(pred.sum()),household_mae=float(np.mean(abs(err))),
                        household_mse=float(np.mean(err**2)),regional_absolute_error=float(abs(err.sum())),
                        regional_squared_error=float(err.sum()**2)))
                exact_full=float(base.sum()+full_j@reference[k,-d:])
                for name,sol in methods.items():
                    additional=float(full_j@(sol[k,-d:]-reference[k,-d:]))
                    errors[-len(methods)+list(methods).index(name)][('output_error_%dh_kwh'%(horizon//2))]=abs(additional)
                    errors[-len(methods)+list(methods).index(name)][('peak_agreement_%dh'%(horizon//2))]=bool((exact_full>=peak)==(exact_full+additional>=peak))
        scoring=time.perf_counter()-t
        persist=time.perf_counter()
        np.savez_compressed(snapshots/('snapshot_%03d.npz'%origin_id),states=reference.reshape(len(w),length,d),
                            meter_ids=meters.astype(str),cutoff=str(origin),profiles=w,model=frozen['model_sha256'],version=origin_id,
                            household_predictions=household_predictions,group_predictions=group_predictions,
                            regional_predictions=household_predictions.sum(2),horizons=cfg['horizons_steps'])
        persistence=time.perf_counter()-persist
        if torch is not None:
            for row in costs:
                if row['origin']==origin_id and row['method']=='gpu_cholesky_cached':
                    row['complete_seconds']+=prediction_seconds+persistence
        snapshot_manifest.append(dict(origin=origin_id,cutoff=str(origin),version=origin_id,mask_digest=native_hash,
            native_matrix_recomputed=fresh,available_window_cells=int(mask.sum()),matrix_new_factors=cold,
            provider_payload_bytes=len(payload.encode()),measurement_seconds=measure_seconds,
            assembly_seconds=assembly,matrix_key_seconds=key_seconds,family_seconds=family_times,
            family_stage_seconds=family_stages,fallback_counts=fallback_counts,initialization_seconds=init_times,
            acceptance_audit_seconds=audit_times,scoring_seconds=scoring,
            prediction_seconds=prediction_seconds,persistence_seconds=persistence,elapsed_all_methods_seconds=time.perf_counter()-origin_start))
        for name,seconds in method_times.items():
            costs.append(dict(origin=origin_id,method=name,seconds=seconds,queries=len(w),
                              complete_seconds=measure_seconds+assembly+key_seconds+seconds+persistence+prediction_seconds,
                              amortized_complete_seconds=measure_seconds+assembly+key_seconds+seconds+persistence+prediction_seconds+parsed_seconds/len(origins)+(basis_cost['rjd']/len(origins) if 'rjd' in name else basis_cost['reference_eigen']/len(origins) if 'reference_eigen' in name else 0)+(cuda_init/len(origins) if name.startswith('gpu') else 0)))
        costs.append(dict(origin=origin_id,method='cpu_cholesky_cached',seconds=warm_chol,queries=len(w),complete_seconds=measure_seconds+assembly+key_seconds+warm_chol+persistence+prediction_seconds))
        prior_state=reference[0,-d:].copy(); previous_origin=origin
        # Identical matrices across origins reuse factors. A common 64-matrix
        # FIFO budget is applied to every factor cache (including the GPU).
        for cache in (factors,bandfactors,gpu_factors):
            while len(cache)>64:
                del cache[next(iter(cache))]
        if torch is not None: torch.cuda.empty_cache()
        print('completed origin',origin_id,str(origin),'seconds',round(time.perf_counter()-origin_start,2),flush=True)
    pd.DataFrame(errors).to_csv(out/'numerical.csv',index=False)
    pd.DataFrame(costs).to_csv(out/'costs.csv',index=False)
    pd.DataFrame(forecasts).to_csv(out/'forecasts.csv',index=False)
    pd.DataFrame(certificates).to_csv(out/'certificates.csv',index=False)
    (out/'snapshots.json').write_text(json.dumps(snapshot_manifest,indent=2)+'\n')
    summary=dict(hardware=hardware,households=len(meters),origins=len(origins),profiles=len(w),queries=len(origins)*len(w),
        development_valid_readings=int(np.isfinite(y).sum()),native_mask_families=len(masks_seen),
        parsing_seconds=parsed_seconds,basis_setup_seconds=basis_cost,setup_seconds=setup_seconds,cuda_initialization_seconds=cuda_init,
        total_seconds=time.perf_counter()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None else 0,
        output_tolerance_kwh=output_tolerance,precision='FP64 all matrix solves; source panel FP32 then FP64 algebra',
        snapshot_storage_bytes=sum(p.stat().st_size for p in snapshots.glob('*.npz')),
        maximum_numerical_residual=max(x['relative_residual'] for x in errors),failures=sum(x['failed'] for x in errors),
        limitations=['bounds exact-arithmetic plus numerical audits, not formal floating-point certificates',
                     'observed-support sums; no full cohort outcome when readings missing',
                     'counterfactual provider access only; no physical outage effect',
                     'GPU PCG is vectorized PyTorch, not a tuned Ginkgo fused kernel',
                     'full information smoother is timing reference; banded Cholesky supplies optimized equivalent',
                     'provider statistics prepared separately; zero-availability RHS is removed at the per-query access boundary'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
