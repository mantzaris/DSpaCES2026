"""Paired exploratory comparison. Original episodes are diagnostic, never pooled with fresh seeds."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from evidence_fusion.shock_overlays import overlay

def main():
    root=Path('results/acquisition');out=root/'comparison';out.mkdir(exist_ok=True)
    meta=pd.DataFrame(json.loads((root/'run/episodes.json').read_text()))
    frames={k:pd.read_csv(root/'run'/(k+'.csv.gz'),keep_default_na=False if k=='access' else True,
        dtype={'alarming_households':str,'alarming_groups':str} if k=='alarms' else None) for k in ['metrics','alarms','costs','access','checks']}
    oldmeta={m['episode']:m for m in json.loads(Path('results/shock/run/episodes.json').read_text())}
    for k in ['metrics','alarms','costs','access']:
        old=pd.read_csv('results/shock/run/'+k+'.csv.gz',keep_default_na=False if k=='access' else True,
            dtype={'alarming_households':str,'alarming_groups':str} if k=='alarms' else None)
        reused=[]
        for ep in meta[meta.phase=='original'].itertuples():
            key='b00_%s_%s'%(ep.family,ep.magnitude)
            assert oldmeta[key]['seed']==ep.seed and oldmeta[key]['source_sha256']==ep.source_sha256
            a=old[(old.episode==key)&old.method.isin(['M2','M3','M4'])].copy();a['episode']=ep.episode;reused.append(a)
        frames[k]=pd.concat([frames[k]]+reused,ignore_index=True)
    metrics,alarms,cost,access= [frames[k] for k in ['metrics','alarms','costs','access']]
    payload=access.groupby(['episode','method','step']).payload_bytes.sum().to_dict()
    cost['fine_bytes']=[payload.get((r.episode,'M3b' if r.method=='M3b_fixed' else r.method,r.step+23),0) for r in cost.itertuples()]
    model=dict(np.load('data/regional/refinement/model.npz'));groups=model['groups'];n=len(groups)
    access_groups={(e,m):a for (e,m),a in access.groupby(['episode','method'])}
    alarm_groups={(e,m):a for (e,m),a in alarms.groupby(['episode','method'])}
    paths=[];eventrows=[]
    def idsets(ep,method):
        a=access_groups.get((ep,method))
        if a is None:return {}
        return {int(t)-23:np.concatenate([np.arange(n) if r.households=='ALL' else np.fromstring(r.households,sep=' ',dtype=int) for r in z.itertuples()]) for t,z in a.groupby('step')}
    controls={}
    for ep in meta[meta.family=='none'].itertuples():
        for method in ['M2','M3','M3b','M4']:controls[ep.phase,ep.background,method]=idsets(ep.episode,method)
    for ep in meta.itertuples():
        with np.load('data/regional/shock/background_%02d.npz'%ep.background) as p:background=p['values']
        readings,target,shift,sig,check=overlay(background,model,ep.family,ep.magnitude,ep.seed)
        for method in sorted(alarms[alarms.episode==ep.episode].method.unique()):
            a=alarm_groups[ep.episode,method];event=a[(a.step>=ep.onset)&(a.step<ep.onset+ep.duration)]
            window=event[event.step<=ep.onset+6];det=window[window.alarm];local=window[window.correct_group_alarms>0]
            trace_method='M3b' if method=='M3b_fixed' else method;ids=idsets(ep.episode,trace_method)
            control=controls.get((ep.phase,ep.background,trace_method),{})
            probehit=[];finehit=[];affectedreads=0;changed=[];targetedchanges=0
            for t,selected in ids.items():
                actual=shift[23+t,selected]!=0;valid=np.isfinite(readings[23+t,selected]);hits=actual&valid
                if hits.any():finehit.append(t)
                if hits[:41].any() and method!='M4':probehit.append(t)
                if ep.onset<=t<ep.onset+ep.duration:affectedreads+=int(hits.sum())
                if t in control and not np.array_equal(selected,control[t]):
                    changed.append(t)
                    if ep.onset<=t<ep.onset+ep.duration:
                        newids=np.setdiff1d(selected,control[t]);targetedchanges+=int(np.sum(shift[23+t,newids]!=0))
            c=cost[(cost.episode==ep.episode)&(cost.method==method)]
            none_ep=meta[(meta.phase==ep.phase)&(meta.background==ep.background)&(meta.family=='none')].episode.iloc[0]
            base=alarm_groups[none_ep,method]
            bw=base[(base.step>=ep.onset)&(base.step<ep.onset+ep.duration)&(base.step<=ep.onset+6)]
            base_local=False
            for br in bw.itertuples():
                marked=np.fromstring(str(br.alarming_groups),sep=' ',dtype=int) if pd.notna(br.alarming_groups) else np.array([],dtype=int)
                current_groups=np.unique(groups[np.flatnonzero(shift[23+br.step]!=0)])
                base_local=base_local or bool(len(np.intersect1d(marked,current_groups)))
            row=dict(matched_background_detected=bool(bw.alarm.any()),matched_background_localized=base_local,
                detection_excess=int(bool(len(det)))-int(bool(bw.alarm.any())),
                localization_excess=int(bool(len(local)))-int(base_local),
                episode=ep.episode,phase=ep.phase,background=ep.background,family=ep.family,method=method,
                detected=bool(len(det)),localized=bool(len(local)),delay_steps=int(det.step.min()-ep.onset) if len(det) else 7,
                missed=not bool(len(det)),negative_alarms=int(a[~a.in_event].alarm.sum()),negative_steps=int((~a.in_event).sum()),
                negative_alarm_rate=float(a[~a.in_event].alarm.mean()),event_peak_score=float(window.score.max()) if len(window) else np.nan,
                false_house_alarms=int(event.false_house_alarms.sum()),false_group_alarms=int(event.false_group_alarms.sum()),
                correct_house_instances=int(event.correct_house_alarms.sum()),fine_exposed=bool(finehit),probe_exposed=bool(probehit),
                first_fine_exposure=min(finehit) if finehit else np.nan,first_probe_exposure=min(probehit) if probehit else np.nan,
                changed_schedule_steps=len(changed),changed_schedule=bool(changed),affected_reads=affectedreads,
                additional_affected_vs_control=targetedchanges,requested=int(c.fine_attempts.sum()),read=int(c.fine_valid.sum()),
                fine_bytes=int(c.fine_bytes.sum()),median_seconds=float(c.complete_seconds.median()),p95_seconds=float(c.complete_seconds.quantile(.95)),
                peak_gpu_bytes=int(c.gpu_peak_bytes.max()),peak_host_bytes=int(c.host_peak_bytes.max()),
                retained_bytes=float(c.after_eviction_bytes.median()),state_bytes=float(c.state_bytes.median()),recomputed_groups=int(c.groups_rebuilt.sum()))
            eventrows.append(row)
    events=pd.DataFrame(eventrows);events.to_csv(out/'episodes.csv',index=False)
    joined=metrics.merge(meta[['episode','phase','background','family','duration']],on='episode')
    joined['forecast_phase']=np.where(joined.relative_target_step<0,'before',np.where(joined.relative_target_step<joined.duration,'during','after'))
    joined.loc[joined.family=='none','forecast_phase']='background'
    forecasts=joined.groupby(['episode','phase','background','family','method','horizon','level','forecast_phase'])[['mae','mse','coverage','width','adjusted_coverage','adjusted_width']].mean().reset_index()
    forecasts.to_csv(out/'forecasts.csv',index=False)
    es=events.groupby(['phase','family','method']).agg(episodes=('episode','size'),detected=('detected','sum'),localized=('localized','sum'),localization_excess=('localization_excess','sum'),detection_excess=('detection_excess','sum'),
        delay_including_misses=('delay_steps','mean'),changed_schedules=('changed_schedule','sum'),fine_exposed=('fine_exposed','sum'),
        probe_exposed=('probe_exposed','sum'),negative_alarms=('negative_alarms','sum'),negative_steps=('negative_steps','sum'),
        affected_reads=('affected_reads','sum'),additional_affected_vs_control=('additional_affected_vs_control','sum'),
        requested=('requested','sum'),read=('read','sum'),fine_bytes=('fine_bytes','sum'),median_seconds=('median_seconds','mean'),
        false_house=('false_house_alarms','sum'),false_group=('false_group_alarms','sum')).reset_index()
    es.to_csv(out/'family_method.csv',index=False)
    local=forecasts[(forecasts.phase=='fresh')&(forecasts.level=='affected')&(forecasts.forecast_phase=='during')&(forecasts.horizon==2)]
    paired=local.pivot(index=['background','family'],columns='method',values='mae')
    paired.to_csv(out/'paired_local_mae.csv')
    regional=forecasts[(forecasts.phase=='fresh')&forecasts.family.isin(['localized','delayed'])&(forecasts.level=='regional')&(forecasts.forecast_phase=='during')&(forecasts.horizon==2)]
    fresh=events[events.phase=='fresh'];physical=fresh[fresh.family!='none'];negative=fresh[fresh.family=='none']
    summary=dict(fresh_episodes=16,diagnostic_original_episodes=4,households=n,backgrounds=4,
        local_mae=local.groupby('method').mae.mean().to_dict(),regional_mae=regional.groupby('method').mae.mean().to_dict(),
        detected=physical.groupby('method').detected.sum().to_dict(),localized=physical.groupby('method').localized.sum().to_dict(),
        changed_schedules=physical.groupby('method').changed_schedule.sum().to_dict(),
        negative_alarm_rates=negative.groupby('method').negative_alarm_rate.mean().to_dict(),
        same_information_max_abs=float(frames['checks'].same_information_max_abs.max()),
        peak_gpu_bytes=int(cost.gpu_peak_bytes.max()),peak_host_bytes=int(cost.host_peak_bytes.max()),
        paired_background_M3b_minus_random=(paired.M3b-paired.M2).groupby(level=0).mean().to_dict(),
        paired_background_M3b_minus_original=(paired.M3b-paired.M3).groupby(level=0).mean().to_dict())
    assert summary['same_information_max_abs']<=1e-7
    assert cost[cost.method.isin(['M2','M3','M3b','M3b_fixed'])].fine_attempts.eq(209).all()
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    figdir=Path('reports/figures/acquisition');figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,3,figsize=(11,3.3));colors={'M2':'#E69F00','M3':'#D55E00','M3b':'#0072B2','M3b_fixed':'#CC79A7','M4':'#009E73'}
    for m,color in colors.items():
        ec=physical[physical.method==m];axes[0].scatter(ec.read.mean()/48,summary['local_mae'][m],label=m,color=color)
    axes[0].set_xlabel('Valid fine readings/update');axes[0].set_ylabel('Affected-household 1 h MAE (kWh)');axes[0].legend(fontsize=8)
    names=['M2','M3','M3b','M4'];x=np.arange(4)
    axes[1].bar(x-.18,[summary['localized'][m] for m in names],width=.36,label='Correct localization /12')
    axes[1].bar(x+.18,[summary['changed_schedules'][m] for m in names],width=.36,label='Schedule changed /12')
    axes[1].set_xticks(x);axes[1].set_xticklabels(names);axes[1].set_ylim(0,13);axes[1].legend(fontsize=7)
    axes[2].bar(names,[100*summary['negative_alarm_rates'][m] for m in names],color=[colors[m] for m in names])
    axes[2].axhline(2,color='black',linestyle=':');axes[2].set_ylabel('No-shock alarmed updates (%)');axes[2].set_xlabel('192 updates; four backgrounds')
    fig.suptitle('One frozen correction: exploratory fresh seeds on reused development backgrounds')
    fig.tight_layout()
    for ext in ['pdf','svg']:fig.savefig(figdir/('corrective_tradeoff.'+ext))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
