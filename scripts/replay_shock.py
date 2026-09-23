"""Budgeted GPU shock replay. Synthetic labels are confined to evaluator code."""
import argparse
import json
from pathlib import Path
import resource
import time
import hashlib
import numpy as np
import pandas as pd
import torch
from evidence_fusion.refinement_gaussian import tensor_bytes
from evidence_fusion.refinement_access import immutable_digest
from evidence_fusion.shock_gaussian import ShockGaussian
from evidence_fusion.shock_access import ObservationChannel,EvidenceWindow,ProbePolicy
from evidence_fusion.shock_overlays import overlay


METHODS=['M0','M1','M2','M3','M3_fixed','M4']


def cpu(outputs):
    return [{k:v.detach().cpu().numpy() for k,v in p.items()} for p in outputs]


def metric_values(y,mean,var,scale):
    ok=np.isfinite(y)
    if not ok.any():return dict(count=0,mae=np.nan,mse=np.nan,coverage=np.nan,width=np.nan,adjusted_coverage=np.nan,adjusted_width=np.nan,score=np.nan)
    error=abs(mean[ok]-y[ok]);sd=np.sqrt(var[ok])
    radius=1.6448536269514722*sd;adjusted=scale*sd
    return dict(count=int(ok.sum()),mae=float(error.mean()),mse=float((error**2).mean()),
        coverage=float((error<=radius).mean()),width=float((2*radius).mean()),
        adjusted_coverage=float((error<=adjusted).mean()),adjusted_width=float((2*adjusted).mean()),
        score=float((2*adjusted+20*np.maximum(error-adjusted,0.)).mean()))


def run_episode(engine,model,background,slot,metadata,readings,targets,shift,signature,
                cfg,calibration,episode_id,methods=METHODS,steps=None,collect_calibration=False,phase1=False):
    length=cfg['window']; n=len(model['meters']); groups=model['groups']; steps=steps or cfg['steps']
    budget=int(n*cfg['fine_budget_fraction']); probes=int(n*cfg['probe_fraction'])
    event_threshold=calibration.get('trigger',float('inf'))
    histories={m:EvidenceWindow(n,length) for m in methods}
    policies={m:ProbePolicy(groups,cfg['probe_seed'],probes,budget,event_threshold) for m in methods}
    traces={m:[] for m in methods}
    channels={m:ObservationChannel(readings,groups,n if m=='M4' else 0 if m=='M0' else budget,traces[m]) for m in methods if m!='M3_fixed'}
    # Warm-up is aggregate-only. No free household initialization/history reads.
    sums=[];masks=[]
    for t in range(length-1):
        values=readings[t];mask=np.isfinite(values)
        sums.append(np.bincount(groups,weights=np.where(mask,values,0.),minlength=16));masks.append(mask)
    prev_mean=model['profile'][slot[length-1]].astype(float)
    prev_var=model['detail_var']+model['measurement_var']
    prev_group_var=np.array([prev_var[groups==g].sum() for g in range(16)])
    rows=[];alarm_rows=[];costs=[];figure_rows=[];score_cal=[];quantile_cal=[];checks=[]
    hold={};sequential=ProbePolicy(groups,cfg['probe_seed'],probes,budget,event_threshold)
    total_start=time.perf_counter()
    for step in range(steps):
        cutoff=length-1+step
        source_time=time.perf_counter()
        # The same provider summary is physically computed once, then delivered
        # to every method. These scans are charged independently of fine access.
        current=readings[cutoff];native=np.isfinite(current)
        total=np.bincount(groups,weights=np.where(native,current,0.),minlength=16)
        summary_seconds=time.perf_counter()-source_time
        sums.append(total);masks.append(native)
        window_native=np.stack(masks[-length:],1)
        seasonal=model['profile'][slot[cutoff-length+1:cutoff+1]].T.astype(float)
        aggregate=np.stack(sums[-length:],1)-np.stack([(seasonal[groups==g]*window_native[groups==g]).sum(0) for g in range(16)])
        future_ids=[cutoff+h for h in engine.horizons]
        future_base=model['profile'][slot[future_ids]].astype(float)
        supports=np.stack([np.ones(n,dtype=bool)]+[np.isfinite(targets[t]) for t in future_ids[1:]])
        # Prior predictions are from the coarse model only; methods share the
        # same predictable detector reference. No unrevealed residual is formed.
        macro_expected=np.bincount(groups,weights=prev_mean*native,minlength=16)
        macro_z=abs(total-macro_expected)/np.sqrt(np.maximum(prev_group_var,1e-12))
        probe_ids=sequential.probe_ids(step)
        probe_values=None;probe_z=None;selected_trace=None
        outputs_this={};payloads={}
        for method in methods:
            start=time.perf_counter();begin=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True);begin.record()
            cache=histories[method];expired=cache.advance(step)
            retained_values=int(np.isfinite(cache.values).sum())
            if method!='M3_fixed':
                channel=channels[method]
                # Channel holds a sliced causal clock; skip warmup without reads.
                if step==0:channel.cutoff=length-2
                channel.advance(cutoff)
            chosen=np.array([],dtype=int);observed=np.array([],dtype=float);active=[]
            if method=='M4':
                chosen=np.arange(n);observed=channel.read(chosen,'fine_all')
            elif method!='M0' and method!='M3_fixed':
                pv=channel.read(probe_ids,'probe')
                pz=abs(pv-prev_mean[probe_ids])/np.sqrt(np.maximum(prev_var[probe_ids],1e-12))
                if probe_values is None:
                    probe_values=pv;probe_z=pz;sequential.update(probe_ids,pz)
                policy=policies[method];policy.score=sequential.score.copy();policy.active=sequential.active;policy.ttl=sequential.ttl
                chosen=probe_ids;observed=pv
                if method in ('M2','M3','M3_delay','M_uncertainty') and not (method=='M3_delay' and step<26):
                    mode='random' if method=='M2' else 'uncertainty' if method=='M_uncertainty' else 'event'
                    if method=='M3_delay' and step==26:policy.active=int(np.argmax(policy.score))
                    extra=policy.refinement_ids(step,probe_ids,mode,prev_group_var/np.bincount(groups,minlength=16))
                    ev=channel.read(extra,'refinement')
                    chosen=np.r_[probe_ids,extra];observed=np.r_[pv,ev]
                    if policy.active>=0:active=[policy.active]
            elif method=='M3_fixed':
                if selected_trace is None:raise RuntimeError('Sequential M3 trace has not arrived')
                chosen,observed=selected_trace
                active=list(range(16))  # Retains all conditional blocks; same evidence.
            if method=='M3':selected_trace=(chosen.copy(),observed.copy())
            if len(chosen):cache.add(chosen,observed-model['profile'][slot[cutoff],chosen],step)
            coarse=(method=='M0')
            outputs,state=engine.infer(window_native,cache.values,aggregate,supports,future_base,
                                       retain_groups=active)
            pred=cpu(outputs);outputs_this[method]=pred
            if any(np.min(p['variance']) < -1e-8 or float(p['region_variance']) < -1e-8 for p in pred):
                raise ArithmeticError('Negative predictive variance')
            end.record();torch.cuda.synchronize();seconds=time.perf_counter()-start
            detail_bytes=tensor_bytes(state['leaves'])
            state_bytes=tensor_bytes(state)
            if method=='M3_fixed':
                error=max(float(np.max(abs(pred[h][k]-outputs_this['M3'][h][k]))) for h in range(3) for k in pred[h])
                checks.append(dict(episode=episode_id,step=step,same_information_max_abs=error))
                if error>cfg['consistency_tolerance']:raise ArithmeticError('Same-information representation mismatch')
            # Test explicit detail eviction leaves the returned fixed-evidence law unchanged.
            state['leaves']=[]
            hold[method]=dict(mean=state['mean'].detach(),chol=state['chol'].detach())
            del outputs,state
            record_z=abs(observed-prev_mean[chosen])/np.sqrt(np.maximum(prev_var[chosen],1e-12)) if len(chosen) else np.array([])
            qmacro=calibration.get('macro',float('inf'))
            qfine=calibration.get('fine',{}).get(method,float('inf'))
            joint=calibration.get('joint',{}).get(method,1.)
            fine_max=float(np.nanmax(record_z)) if np.isfinite(record_z).any() else 0.
            continuous=max(float(macro_z.max())/qmacro,fine_max/qfine)/joint
            alarming_house=chosen[np.isfinite(record_z)&(record_z>qfine*joint)]
            alarming_groups=np.union1d(np.flatnonzero(macro_z>qmacro*joint),groups[alarming_house])
            affected=np.array(metadata['affected_ids'],dtype=int)
            affected_groups=np.array(metadata['affected_groups'],dtype=int)
            currently_affected=np.flatnonzero(shift[cutoff]!=0.)
            currently_affected_groups=np.unique(groups[currently_affected])
            in_event=metadata['onset']<=step<metadata['onset']+metadata['duration']
            alarm_rows.append(dict(episode=episode_id,step=step,method=method,score=continuous,
                macro_score=float(macro_z.max()),fine_score=fine_max,probe_score=float(sequential.score.max()),
                alarm=continuous>1.,in_event=in_event,house_alarms=len(alarming_house),
                alarming_households=' '.join(map(str,alarming_house)),
                alarming_groups=' '.join(map(str,alarming_groups)),
                correct_house_alarms=len(np.intersect1d(alarming_house,currently_affected)) if in_event else 0,
                false_house_alarms=len(np.setdiff1d(alarming_house,currently_affected)) if in_event else len(alarming_house),
                group_alarms=len(alarming_groups),correct_group_alarms=len(np.intersect1d(alarming_groups,currently_affected_groups)) if in_event else 0,
                false_group_alarms=len(np.setdiff1d(alarming_groups,currently_affected_groups)) if in_event else len(alarming_groups),
                current_group_signature=float(np.max(abs(signature[cutoff]))),
                current_regional_signature=float(signature[cutoff].sum()),
                observed_affected=len(np.intersect1d(chosen,affected)),attempts=len(chosen),
                active_group=active[0] if active and method!='M3_fixed' else -1))
            if collect_calibration:
                score_cal.append(dict(step=step,method=method,macro=float(macro_z.max()),fine=fine_max,
                    trigger=float(sequential.score.max())))
            for hi,horizon in enumerate((2,12),start=1):
                y=targets[cutoff+horizon];ok=np.isfinite(y);p=pred[hi]
                gy=np.array([y[(groups==g)&ok].sum() if ((groups==g)&ok).any() else np.nan for g in range(16)])
                definitions=[('regional',np.array([y[ok].sum() if ok.any() else np.nan]),np.array([p['region_mean']]),np.array([p['region_variance']])),
                    ('group',gy,p['group_mean'],p['group_variance']),
                    ('household',y,p['mean'],p['variance']),
                    ('affected',y[affected],p['mean'][affected],p['variance'][affected])]
                for level,actual,mu,var in definitions:
                    factor=calibration.get('interval',{}).get(method+'_'+str(horizon)+'_'+level,1.6448536269514722)
                    metrics=metric_values(actual,mu,var,factor)
                    rows.append(dict(episode=episode_id,step=step,method=method,horizon=horizon,level=level,
                        relative_target_step=step+horizon-metadata['onset'],**metrics))
                    if collect_calibration and level!='affected':
                        valid=np.isfinite(actual)
                        # Keep exact regional samples and a deterministic household
                        # subsample for bounded calibration storage, fixed by ID.
                        z=abs(actual[valid]-mu[valid])/np.sqrt(var[valid])
                        if level=='household':z=z[::16]
                        quantile_cal.append((method+'_'+str(horizon)+'_'+level,z.tolist()))
                if episode_id.startswith('b00_') or episode_id.startswith('smoke'):
                    plus=np.array(metadata['positive_ids'],dtype=int);minus=np.array(metadata['negative_ids'],dtype=int)
                    def finite_mean(a):
                        return float(np.nanmean(a)) if np.isfinite(a).any() else np.nan
                    figure_rows.append(dict(episode=episode_id,step=step,horizon=horizon,method=method,
                        current_region=float(total.sum()),current_signature=float(signature[cutoff].sum()),
                        current_plus=finite_mean(current[plus]),current_minus=finite_mean(current[minus]),
                        target_region=float(y[ok].sum()),forecast_region=float(p['region_mean']),
                        region_sd=float(np.sqrt(p['region_variance'])),
                        target_plus=finite_mean(y[plus]),forecast_plus=finite_mean(p['mean'][plus]),
                        target_minus=finite_mean(y[minus]),forecast_minus=finite_mean(p['mean'][minus]),
                        active_group=active[0] if active and method!='M3_fixed' else -1))
            costs.append(dict(episode=episode_id,step=step,method=method,complete_seconds=seconds+summary_seconds,
                cuda_event_ms=begin.elapsed_time(end),provider_summary_seconds=summary_seconds,
                provider_summary_scan_rows=n,summary_bytes=16*8+len(np.packbits(native))+64,
                fine_attempts=len(chosen),fine_valid=int(np.isfinite(observed).sum()),
                fine_bytes=int(len(chosen)*16+(128 if len(chosen)>probes else 64 if len(chosen) else 0)),
                window_cache_bytes=cache.values.nbytes,retained_old_fine_cells=retained_values,
                expired_fine_cells=expired,source_rereads=0,groups_rebuilt=16,separator_rebuilt=1,
                detail_bytes=detail_bytes,state_bytes=state_bytes,after_eviction_bytes=state_bytes-detail_bytes,
                gpu_peak_bytes=torch.cuda.max_memory_allocated(),host_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                payload_transfer_bytes=int(window_native.nbytes+cache.values.nbytes+aggregate.nbytes+supports.nbytes+future_base.nbytes)))
        # Policy never sees perturbed targets, injection labels or future choices.
        prev_mean=outputs_this['M0'][0]['mean'];prev_var=outputs_this['M0'][0]['variance']
        prev_group_var=outputs_this['M0'][0]['group_variance']
    access=[]
    for m,trace in traces.items():
        access.extend(dict(episode=episode_id,method=m,**r) for r in trace)
    return dict(metrics=rows,alarms=alarm_rows,costs=costs,figure=figure_rows,checks=checks,
        access=access,score_cal=score_cal,quantile_cal=quantile_cal,
        total_seconds=time.perf_counter()-total_start,summary_warmup_rows=(length-1)*n)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['smoke','calibrate','run'])
    args=parser.parse_args()
    cfg=json.loads(Path('configs/regional_shock.json').read_text())
    root=Path('results/shock');root.mkdir(exist_ok=True)
    folder=root/args.mode;folder.mkdir(exist_ok=True)
    model=dict(np.load('data/regional/refinement/model.npz',allow_pickle=False))
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False
    torch.cuda.set_per_process_memory_fraction(.70)
    engine=ShockGaussian(model,cfg['window'])
    start=time.perf_counter()
    if args.mode=='calibrate':
        with np.load('data/regional/shock/calibration.npz') as p:background=p['values'];slot=p['slots']
        readings,targets,shift,signature,meta=overlay(background,model,'none',0.,cfg['smoke_seed'])
        # First pass learns only the cheap monitoring trigger, no synthetic labels.
        first=run_episode(engine,model,background,slot,meta,readings,targets,shift,signature,cfg,{},
            'calibration_trigger',methods=['M0','M1'],steps=cfg['calibration_steps'],collect_calibration=True)
        trigger=np.quantile([r['trigger'] for r in first['score_cal'] if r['method']=='M1' and r['step']>=8],.98)
        cal={'trigger':float(trigger)}
        result=run_episode(engine,model,background,slot,meta,readings,targets,shift,signature,cfg,cal,
            'calibration_final',steps=cfg['calibration_steps'],collect_calibration=True)
        sc=pd.DataFrame(result['score_cal']);sc=sc[sc.step>=8]
        cal['macro']=float(sc[sc.method=='M0'].macro.quantile(.95))
        cal['fine']={m:float(max(sc[sc.method==m].fine.quantile(.95),1e-8)) if m!='M0' else 1e300 for m in METHODS}
        cal['joint']={}
        for m in METHODS:
            a=sc[sc.method==m]
            cal['joint'][m]=float(np.quantile(np.maximum(a.macro/cal['macro'],a.fine/cal['fine'][m]),.98))
        collected={}
        for key,values in result['quantile_cal']:collected.setdefault(key,[]).extend(values)
        cal['interval']={k:float(np.quantile(v,.9)) for k,v in collected.items()}
        for m in METHODS:
            for h in (2,12):cal['interval'][m+'_'+str(h)+'_affected']=cal['interval'][m+'_'+str(h)+'_household']
        cal.update(config_sha256=immutable_digest('configs/regional_shock.json'),
                   segment=cfg['calibration_start'],steps=cfg['calibration_steps'],
                   caveat='Empirical development quantiles, not a time-series coverage or false-alarm theorem')
        (root/'calibration.json').write_text(json.dumps(cal,indent=2)+'\n')
        pd.DataFrame(result['score_cal']).to_csv(folder/'scores.csv',index=False)
        pd.DataFrame(result['metrics']).to_csv(folder/'raw_metrics.csv',index=False)
        pd.DataFrame(result['costs']).to_csv(folder/'costs.csv',index=False)
        print('calibrated',cal['trigger'],flush=True)
    else:
        cal=json.loads((root/'calibration.json').read_text()) if args.mode=='run' else {}
        if args.mode=='run':
            frozen=json.loads((root/'frozen_manifest.json').read_text())
            if immutable_digest('configs/regional_shock.json')!=frozen['config_sha256']:
                raise ValueError('Configuration differs from comparative freeze')
            if immutable_digest(root/'calibration.json')!=frozen['calibration_sha256']:
                raise ValueError('Calibration changed after freeze')
            if immutable_digest('data/regional/refinement/model.npz')!=frozen['model_sha256']:
                raise ValueError('Training model changed after freeze')
        all_rows={k:[] for k in ('metrics','alarms','costs','figure','checks','access')};episodes=[]
        written={k:0 for k in all_rows}
        if args.mode=='run' and (folder/'episodes.json').exists():
            raise RuntimeError('Comparative outputs already exist; preserve them, do not overwrite')
        def save():
            for name,rows in all_rows.items():
                fresh=rows[written[name]:]
                if fresh:
                    path=folder/(name+'.csv.gz')
                    pd.DataFrame(fresh).to_csv(path,index=False,compression='gzip',mode='a',header=not path.exists())
                    written[name]=len(rows)
            (folder/'episodes.json').write_text(json.dumps(episodes,indent=2)+'\n')
        backgrounds=range(len(cfg['background_origin_indices'])) if args.mode=='run' else range(1)
        for bg in backgrounds:
            with np.load('data/regional/shock/background_%02d.npz'%bg) as p:background=p['values'];slot=p['slots']
            settings=[(f,m) for f in cfg['families'] for m in cfg['magnitudes']]+[('none',0.),('sensor_fault',cfg['magnitudes'][-1])]
            if args.mode=='smoke':settings=[('cancel_exact',cfg['magnitudes'][0])]
            for si,(family,mag) in enumerate(settings):
                eid=('b%02d_'%bg)+family+'_'+str(mag)
                family_index=cfg['families'].index(family) if family in cfg['families'] else 6 if family=='none' else 7
                seed=cfg['episode_seed']+1000*bg+10*family_index if args.mode=='run' else cfg['smoke_seed']
                readings,targets,shift,signature,meta=overlay(background,model,family,mag,seed,cfg['window'])
                meta.update(episode=eid,background=bg,source_sha256=immutable_digest('data/regional/shock/background_%02d.npz'%bg))
                print('episode',eid,'start',flush=True)
                result=run_episode(engine,model,background,slot,meta,readings,targets,shift,signature,cfg,cal,eid,
                    steps=cfg['steps'] if args.mode=='run' else 4)
                meta.update(seconds=result['total_seconds'],provider_warmup_rows=result['summary_warmup_rows'])
                episodes.append(meta)
                for k in all_rows:all_rows[k].extend(result[k])
                save();print('episode',eid,'seconds',result['total_seconds'],flush=True)
        # One declared delayed opening crossing the 24-step window boundary;
        # diagnostic only, not pooled into the primary method comparison.
        if args.mode=='run':
            with np.load('data/regional/shock/background_00.npz') as p:background=p['values'];slot=p['slots']
            family='cancel_exact';mag=cfg['magnitudes'][-1]
            si=10*cfg['families'].index(family)
            readings,targets,shift,signature,meta=overlay(background,model,family,mag,cfg['episode_seed']+si,cfg['window'])
            result=run_episode(engine,model,background,slot,meta,readings,targets,shift,signature,cfg,cal,
                'boundary_diagnostic',methods=['M0','M1','M3_delay','M_uncertainty'])
            for k in all_rows:pd.DataFrame(result[k]).to_csv(folder/('boundary_'+k+'.csv.gz'),index=False,compression='gzip')
        (folder/'summary.json').write_text(json.dumps(dict(completed=True,mode=args.mode,
            episodes=len(episodes),backgrounds=len(list(backgrounds)),households=len(model['meters']),
            episode_updates=len(episodes)*(cfg['steps'] if args.mode=='run' else 4),seconds=time.perf_counter()-start,
            device=torch.cuda.get_device_name(),vram_bytes=torch.cuda.get_device_properties(0).total_memory,
            peak_gpu_bytes=torch.cuda.max_memory_allocated(),peak_host_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            config_sha256=immutable_digest('configs/regional_shock.json'),
            model_sha256=immutable_digest('data/regional/refinement/model.npz'),
            london_holdout_sealed=True,bdg2_seals_unchanged=True),indent=2)+'\n')
    print('complete',args.mode,time.perf_counter()-start,flush=True)


if __name__=='__main__':main()
