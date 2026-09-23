"""Frozen validation-only real-data pilot. Never loads November or test values."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import time
import zlib
import numpy as np
import pandas as pd
import yaml
from threadpoolctl import threadpool_limits
from evidence_fusion.chronological_splits import sealed_read, split_mask, causal_target_mask, pilot_roles
from evidence_fusion.provider_models import calendar_features, fit_ols, allocate_days
from evidence_fusion.record_identity import record_id, evidence_digest, support_encodings
from evidence_fusion.influence_operators import cached_operator, exact_norms, exact_cross_blocks, exact_query_grams
from evidence_fusion.provenance_sketches import Epoch, gaussian_columns
from evidence_fusion.message_contracts import Message, ActiveMessages
from evidence_fusion.conservative_fusion import fuse_arrays, quadratic
from evidence_fusion.fusion_baselines import independence, scalar_ci, exact_lineage, learned_covariance, fuse_with_weights
from evidence_fusion.calibration import fit_correction
from evidence_fusion.evaluation import score, autocorrelation
from evidence_fusion.resource_ledger import Budget


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare_messages(means, z, norms, residual, future, times, building, models, ids, epoch):
    """Actual binary encode/parse/validate path; materialize only one target group."""
    accepted_z, accepted_s, accepted_r, accepted_m = [], [], [], []
    byte_count=0
    digests=[evidence_digest([ids[i] for i in model.support]) for model in models]
    model_digests=[sha(model.beta.tobytes()+model.operator.tobytes()+digests[i].encode()) for i,model in enumerate(models)]
    for target in range(len(times)):
        state=ActiveMessages(epoch)
        for provider in range(len(models)):
            start=times[target]
            item=Message(protocol='weighted-provenance/1',provider=f'p{provider}',building=building,
                target_start=start.isoformat(),target_end=(start+pd.Timedelta(hours=1)).isoformat(),
                unit='kWh',cutoff='2016-09-30T23:00:00',
                issued=(start-pd.Timedelta(minutes=1)).isoformat(),arrival=start.isoformat(),
                model_version='calendar-19-qr-v1',estimator_digest=model_digests[provider],
                evidence_digest=digests[provider],revision=0,supersedes='',
                common_contract='consensus-local-oof-variance-v1',future_variance=float(future),
                epoch=epoch.name,seed=epoch.seed,k=epoch.k,mean=float(means[target,provider]),
                norm=float(norms[target,provider]),residual=float(residual[target,provider]),
                sketch=tuple(map(float,z[target,provider]))).signed()
            wire=item.to_wire();byte_count+=len(wire)
            state.accept(Message.from_wire(wire))
        active=state.finalize()
        accepted_z.append([x.sketch for x in active]);accepted_s.append([x.norm for x in active])
        accepted_r.append([x.residual for x in active]);accepted_m.append([x.mean for x in active])
    return tuple(np.asarray(x) for x in (accepted_m,accepted_z,accepted_s,accepted_r)),byte_count


def main(config_path):
    cfg=yaml.safe_load(Path(config_path).read_text())
    if cfg['stage']!=1 or cfg['main_study_authorized']:
        raise ValueError('This entry point executes only the frozen Stage 1 workload')
    budget=Budget('results/resource_ledger.json',cfg['allocation_start_utc'],cfg['gpu_allocation_cap_seconds'],cache='data')
    budget.record('pilot_start',config_sha256=sha(Path(config_path).read_bytes()))
    threadpool_limits(limits=cfg['cpu_threads'])
    Path('results').mkdir(exist_ok=True)
    audit=json.loads(Path('manifests/data_audit.json').read_text())
    frame=sealed_read('data/electricity_pretest.csv')
    clean=sealed_read('data/cleaned_pretest.csv')
    train=np.asarray(split_mask(frame.index,'2016-01-01','2016-10-01'))
    x,feature_names=calendar_features(frame.index)
    days=frame.index.normalize()
    epochs=[Epoch(f'pilot-k{k}-v1',seed,k,cfg['epoch_query_cap'],cfg['providers'],cfg['delta_per_epoch'])
            for k,seed in zip(cfg['sketch_dimensions'],cfg['projection_seeds'])]
    rows=[];costs=[];diagnostics=[];allocations=[];calibrations=[];predictions=[]
    max_relative_projection_error=0.;max_fp32_relative_gram_error=0.
    stage_start=time.perf_counter()
    for building in audit['selected_buildings']:
        budget.check()
        info=next(r for r in audit['selection'] if r['building']==building)
        y=frame[building].to_numpy(dtype=float)
        causal=causal_target_mask(frame.index,info['timezone'])
        valid=np.isfinite(y)&(y>=0)
        complete=pd.Series(valid&causal&train,index=days).groupby(level=0).sum()
        complete_days=complete[complete==24].index
        # Seven-day embargo makes seasonal-naive lag inputs wholly validation-local.
        eligible=np.flatnonzero(causal & split_mask(frame.index,'2016-10-08','2016-11-01'))
        targets=eligible[np.linspace(0,len(eligible)-1,min(cfg['max_origins_per_building'],len(eligible)),dtype=int)]
        target_times=frame.index[targets];phi=x[targets]
        roles=pilot_roles(target_times)
        outcome=y[targets].copy();outcome[~valid[targets]]=np.nan
        # All comparisons share the valid seasonal-naive lag set; labels stay missing.
        lag=targets-168
        outcome[~valid[lag]]=np.nan
        ids=[record_id(building,str(frame.index[i]),i) for i in range(int(train.sum()))]
        projection={}
        projection_seconds={}
        for epoch in epochs:
            begin=time.perf_counter();projection[epoch.k]=gaussian_columns(ids,epoch.k,epoch.seed)
            projection_seconds[epoch.k]=time.perf_counter()-begin
        naive_train=np.flatnonzero(train & valid)
        naive_train=naive_train[naive_train>=168]
        naive_train=naive_train[valid[naive_train-168]]
        naive_variance=float(np.mean((y[naive_train]-y[naive_train-168])**2))
        building_seed=cfg['allocation_seed']+int(sha(building.encode())[:8],16)
        for common_days in cfg['common_days']:
            budget.check();begin=time.perf_counter()
            pools=allocate_days(complete_days,common_days,cfg['provider_days'],cfg['providers'],building_seed)
            supports=[np.flatnonzero(train & days.isin(pool)) for pool in pools]
            models=[fit_ols(x,y,support,days.to_numpy()) for support in supports]
            fit_seconds=time.perf_counter()-begin
            means=np.column_stack([model.predict(phi) for model in models])
            norms=np.column_stack([exact_norms(model,phi) for model in models])
            # Explicit empirical convention: consensus of provider-local OOF MSEs.
            # This is not an identified physical future-innovation variance.
            future=float(np.mean([model.sigma**2 for model in models]))
            residual=np.zeros_like(norms)
            union=np.unique(np.concatenate(supports))
            intersections=[[len(np.intersect1d(a,b)) for b in supports] for a in supports]
            allocations.append(dict(building=building,site=info['site'],common_days=common_days,
                allocation_seed=building_seed,provider_records=list(map(len,supports)),
                union_records=len(union),intersection_records=intersections,
                selected_days=[[str(day.date()) for day in pool] for pool in pools],
                record_digest=[evidence_digest([ids[i] for i in support]) for support in supports],
                target_count=len(targets),unique_observed_score_targets=int(np.sum(roles['score']&np.isfinite(outcome)))))
            start=time.perf_counter();blocks=exact_cross_blocks(models);gram=exact_query_grams(blocks,phi)
            exact_setup=time.perf_counter()-start
            base={}
            for i in range(4):base[f'individual_{i}']=dict(mean=means[:,i],variance=norms[:,i]**2+future)
            base['seasonal_naive']=dict(mean=y[lag],variance=np.full(len(phi),naive_variance))
            base['equal_weight']=dict(mean=means.mean(axis=1),variance=norms.mean(axis=1)**2+future)
            base['naive_independence']=independence(means,norms,residual,future)
            base['duplicate_aware_independence']=independence(means,norms,residual,future)
            base['common_corrected']=independence(means,norms,residual,future,corrected=True)
            base['ci']=scalar_ci(means,norms,residual,future)
            start=time.perf_counter();base['exact_lineage']=exact_lineage(means,gram,residual,future)
            exact_query_time=time.perf_counter()-start
            base['shrinkage'],covinfo=learned_covariance(means,outcome,roles['covariance'])
            pooled=fit_ols(x,y,union,days.to_numpy())
            base['pooled_privileged']=dict(mean=pooled.predict(phi),variance=exact_norms(pooled,phi)**2+future)
            encodings=[support_encodings(support,int(train.sum())) for support in supports]
            compressed_support=sum(min(len(value) for value in entry.values()) for entry in encodings)
            # Exact design is public. Support bitmap + sigma + public feature recipe recovers B.
            exact_header=json.dumps(dict(dataset='BDG2-v1.0',building=building,features=feature_names,
                local_start='2016-01-01',hours=int(train.sum()),precision='FP64',sigma=[m.sigma for m in models],
                active_columns=[m.active_columns for m in models]),sort_keys=True).encode()
            exact_support_bytes=compressed_support+len(exact_header)
            exact_operator_bytes=sum(len(zlib.compress(model.operator.astype('<f8').tobytes(),9)) for model in models)+exact_support_bytes
            exact_blocks_bytes=len(zlib.compress(blocks.astype('<f8').tobytes(),9))+len(exact_header)
            fractions=norms**2/(norms**2+future)
            full_residual=y-np.mean([m.predict(x) for m in models],axis=0)
            full_residual[~(train&valid)]=np.nan
            diag=dict(building=building,common_days=common_days,future_variance=future,
                local_oof_scales=[m.sigma for m in models],conditions=[m.condition for m in models],
                active_feature_columns=[m.active_columns for m in models],
                training_influence_fraction_mean=float(fractions.mean()),training_influence_fraction_max=float(fractions.max()),
                train_residual_acf1=autocorrelation(full_residual,1),train_residual_acf24=autocorrelation(full_residual,24),
                train_residual_bias=float(np.nanmean(full_residual)),
                covariance_fit=covinfo,raw_equal_training_variance=float(np.mean(quadratic(gram,np.ones(4)/4))))
            diagnostics.append(diag)
            for epoch in epochs:
                start=time.perf_counter()
                operators=np.stack([cached_operator(model,projection[epoch.k]) for model in models])
                operator_seconds=time.perf_counter()-start
                start=time.perf_counter();z=np.einsum('td,pdk->tpk',phi,operators,optimize=True)
                sketches_seconds=time.perf_counter()-start
                start=time.perf_counter()
                parsed,wire_bytes=prepare_messages(means,z,norms,residual,future,target_times,building,models,ids,epoch)
                protocol_seconds=time.perf_counter()-start
                start=time.perf_counter()
                base[f'sketch_{epoch.k}']=fuse_arrays(*parsed,future,epoch.epsilon)
                solve_seconds=time.perf_counter()-start
                base[f'uninflated_{epoch.k}']=fuse_arrays(*parsed,future,0.,fallback=False)
                kh=z@z.swapaxes(-1,-2)
                denominator=norms[:,:,None]*norms[:,None,:]
                error=float(np.max(np.abs(kh-gram)/np.maximum(denominator,1e-300)))
                max_relative_projection_error=max(max_relative_projection_error,error)
                if error>epoch.epsilon:
                    diag.setdefault('projection_event_failures',[]).append(epoch.k)
                fp32=z.astype(np.float32)
                fp32_error=float(np.max(np.abs((fp32@fp32.swapaxes(-1,-2)).astype(float)-kh)/np.maximum(denominator,1e-300)))
                max_fp32_relative_gram_error=max(max_fp32_relative_gram_error,fp32_error)
                per_message_header=(wire_bytes-z.size*8)/z.shape[0]
                cached_sketch=operators.astype('<f8').nbytes+len(exact_header)
                costs.append(dict(building=building,common_days=common_days,k=epoch.k,queries=len(phi),
                    fit_seconds=fit_seconds,projection_seconds=projection_seconds[epoch.k],
                    projection_reuse_allocations=3,operator_seconds=operator_seconds,sketch_query_seconds=sketches_seconds,
                    protocol_seconds=protocol_seconds,solver_seconds=solve_seconds,
                    complete_cold_seconds=fit_seconds+projection_seconds[epoch.k]+operator_seconds+sketches_seconds+protocol_seconds+solve_seconds,
                    exact_setup_seconds=exact_setup,exact_query_seconds=exact_query_time,
                    sketch_bytes_per_query=wire_bytes/len(phi),sketch_fp32_bytes_per_query=per_message_header+4*epoch.k*4,
                    exact_support_once_bytes=exact_support_bytes,exact_cached_operator_once_bytes=exact_operator_bytes,
                    exact_cross_blocks_once_bytes=exact_blocks_bytes,cached_sketch_operator_once_bytes=cached_sketch,
                    common_header_bytes_per_query=per_message_header,
                    exact_amortized_bytes_per_query=per_message_header+exact_support_bytes/len(phi),
                    sketch_amortized_bytes_per_query=per_message_header+cached_sketch/len(phi),
                    max_relative_gram_error=error,max_fp32_relative_gram_error=fp32_error,
                    max_relative_solver_gap=float(np.max(base[f'sketch_{epoch.k}']['sketch_gap']/np.maximum(base[f'sketch_{epoch.k}']['sketch_candidate_variance'],1e-300)))))
                # One fixed real workload saved for matched CPU/GPU timing; not all sketches.
                if building==audit['selected_buildings'][0] and common_days==21 and epoch.k==2048:
                    np.savez('data/benchmark_input.npz',features=phi,operators=operators,norms=norms,
                        means=means,residual=residual,future=future,epsilon=epoch.epsilon,
                        projection=projection[epoch.k],local_operators=np.stack([m.operator for m in models]),
                        supports=np.stack(supports),blocks=blocks)
            # Prespecified residual sensitivities on a four-building middle-overlap panel.
            if building in audit['selected_buildings'][:4] and common_days==21:
                for multiplier in cfg['residual_sensitivity']:
                    rr=np.broadcast_to(np.array([m.sigma*multiplier for m in models]),norms.shape)
                    base[f'exact_r{multiplier}']=exact_lineage(means,gram,rr,future)
                    base[f'sketch_2048_r{multiplier}']=fuse_arrays(means,z,norms,rr,future,epochs[-1].epsilon)
            for name,pred in base.items():
                # All methods frozen before October 11, then identically calibrated.
                correction=fit_correction(pred['mean'],np.asarray(pred['variance']),outcome,roles['calibration'])
                calibrations.append(dict(building=building,common_days=common_days,method=name,**correction))
                for calibrated in (False,True):
                    metrics=score(pred['mean'],np.asarray(pred['variance']),outcome,roles['score'],info['training_scale'],correction if calibrated else None)
                    rows.append(dict(building=building,site=info['site'],common_days=common_days,
                        overlap=common_days/42,method=name,calibrated=calibrated,**metrics))
                # Sensitivity only: preserve main raw targets, apply released cleaned mask separately.
                cleaned_mask=roles['score']&np.isfinite(clean[building].to_numpy(dtype=float)[targets])
                if name in ('exact_lineage','sketch_2048','ci','shrinkage') and cleaned_mask.any():
                    metrics=score(pred['mean'],np.asarray(pred['variance']),outcome,cleaned_mask,info['training_scale'],correction)
                    rows.append(dict(building=building,site=info['site'],common_days=common_days,
                        overlap=common_days/42,method=name+'_cleaned_mask',calibrated=True,**metrics))
                if name in ('common_corrected','exact_lineage','sketch_2048','ci','shrinkage','seasonal_naive'):
                    for i in np.flatnonzero(roles['score']&np.isfinite(outcome)):
                        predictions.append(dict(building=building,site=info['site'],target=str(target_times[i]),
                            common_days=common_days,method=name,mean=float(pred['mean'][i]),
                            outcome=float(outcome[i]),variance=float(pred['variance'][i]),
                            q90=correction['q90'],q95=correction['q95'],q80=correction['q80']))
            pd.DataFrame(rows).to_csv('results/pilot_metrics.csv',index=False)
            pd.DataFrame(costs).to_csv('results/pilot_costs.csv',index=False)
            budget.record('allocation_complete',building=building,common_days=common_days)
            print(f'{building}: common days {common_days}/42 completed',flush=True)
        del projection
    pd.DataFrame(predictions).to_csv('results/pilot_predictions.csv',index=False)
    Path('results/diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
    Path('manifests/provider_allocations.json').write_text(json.dumps(allocations,indent=2)+'\n')
    Path('manifests/pilot_calibration.json').write_text(json.dumps(calibrations,indent=2)+'\n')
    Path('manifests/sketch_epochs.json').write_text(json.dumps([dict(name=e.name,seed=e.seed,k=e.k,
        query_cap=e.query_cap,actual_queries=len(e.seen),provider_cap=e.provider_cap,delta=e.delta,
        epsilon=e.epsilon,query_set_digest=sha(repr(sorted(e.seen)).encode())) for e in epochs],indent=2)+'\n')
    budget.record('pilot_complete',wall_seconds=time.perf_counter()-stage_start,
        max_relative_projection_error=max_relative_projection_error,
        max_fp32_relative_gram_error=max_fp32_relative_gram_error,test_values_opened=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',default='configs/pilot.yaml')
    main(parser.parse_args().config)
