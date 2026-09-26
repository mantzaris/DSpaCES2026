"""Paired descriptive analysis and vector figures from the frozen shock replay."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from evidence_fusion.shock_overlays import overlay

COLORS={'M0':'#777777','M1':'#0072B2','M2':'#E69F00','M3':'#D55E00','M3_fixed':'#CC79A7','M4':'#009E73'}
NAMES={'M0':'Group sums','M1':'Cheap probes','M2':'Random refinement','M3':'Event refinement',
       'M3_fixed':'Same trace, fixed','M4':'Streamed fine'}


def main():
    root=Path('results/shock');run=root/'run';out=root/'analysis';out.mkdir(exist_ok=True)
    cfg=json.loads(Path('configs/regional_shock.json').read_text())
    cal=json.loads((root/'calibration.json').read_text())
    meta=pd.DataFrame(json.loads((run/'episodes.json').read_text()))
    metrics=pd.read_csv(run/'metrics.csv.gz');alarms=pd.read_csv(run/'alarms.csv.gz',
        dtype={'alarming_households':str,'alarming_groups':str})
    costs=pd.read_csv(run/'costs.csv.gz');access=pd.read_csv(run/'access.csv.gz',keep_default_na=False)
    checks=pd.read_csv(run/'checks.csv.gz');figdata=pd.read_csv(run/'figure.csv.gz')
    corrected=root/'figure_common_support.csv'
    if corrected.exists():
        replacement=pd.read_csv(corrected)
        figdata=pd.concat([figdata[~figdata.episode.isin(replacement.episode.unique())],replacement],ignore_index=True)
    model=dict(np.load('data/regional/refinement/model.npz',allow_pickle=False))
    # The channel trace is authoritative for simulated framing. M4 makes one
    # request, so its header is 64 bytes, not the two-request 128-byte estimate.
    payload=access[access.kind!='summary'].groupby(['episode','method','step']).payload_bytes.sum().to_dict()
    costs['raw_fine_bytes']=costs.fine_bytes
    costs['fine_bytes']=[payload.get((r.episode,'M3' if r.method=='M3_fixed' else r.method,
        int(r.step)+cfg['window']-1),0) for r in costs.itertuples()]
    costs.to_csv(out/'audited_costs.csv.gz',index=False,compression='gzip')
    # Bookkeeping audit: old raw observed_affected counts attempted IDs. Derive
    # actually informative *valid current* records from the immutable acquisition
    # trace, native masks and reversible evaluator overlay, without rerunning inference.
    visible={};visibility_checks=[];target_support={}
    for bg,episodes in meta.groupby('background'):
        with np.load('data/regional/shock/background_%02d.npz'%bg) as source:
            background=source['values'];timestamps=source['timestamps']
        target_indices=sorted({cfg['window']-1+t+h for t in range(cfg['steps']) for h in (2,12)})
        for ti in target_indices:
            key=str(timestamps[ti]);valid=np.isfinite(background[ti])
            target_support[key]=target_support.get(key,np.zeros(len(valid),bool))|valid
        for ep in episodes.itertuples():
            readings,targets,shift,signature,recreated=overlay(background,model,ep.family,ep.magnitude,int(ep.seed),cfg['window'])
            assert abs(recreated['max_group_signature']-ep.max_group_signature)<1e-8
            visibility_checks.append(dict(episode=ep.episode,max_group_signature=float(abs(signature).max()),
                first_nonzero_group_signature=next((t-cfg['window']+1 for t in range(cfg['window']-1,len(signature)) if abs(signature[t]).max()>1e-8),None),
                nonnegative_min_reading=float(np.nanmin(readings)),nonnegative_min_target=float(np.nanmin(targets))))
            affected=np.array(ep.affected_ids,dtype=int)
            sd=np.sqrt(model['detail_var']+model['measurement_var'])
            visibility_checks[-1]['median_realized_peak_in_training_sd']=float(np.median(abs(shift[:,affected]).max(0)/sd[affected])) if len(affected) else 0.
            aa=access[access.episode==ep.episode]
            for row in aa.itertuples():
                if row.kind=='summary':continue
                ids=np.arange(len(model['meters'])) if row.households=='ALL' else np.fromstring(str(row.households),sep=' ',dtype=int)
                t=int(row.step);valid=np.isfinite(readings[t,ids])
                informative=int(np.sum(valid&(shift[t,ids]!=0)))
                key=(ep.episode,row.method,t-cfg['window']+1)
                visible[key]=visible.get(key,0)+informative
    alarms['informative_valid_reads']=[visible.get((r.episode,'M3' if r.method=='M3_fixed' else r.method,int(r.step)),0) for r in alarms.itertuples()]
    pd.DataFrame(visibility_checks).to_csv(out/'visibility_checks.csv',index=False)
    alarms.to_csv(out/'audited_alarms.csv.gz',index=False,compression='gzip')
    event_rows=[]
    for ep in meta.itertuples():
        for method,a in alarms[alarms.episode==ep.episode].groupby('method'):
            limit=a[(a.step>=ep.onset)&(a.step<ep.onset+cfg['detection_limit_steps'])]
            hit=limit[limit.alarm];local=limit[limit.correct_group_alarms>0]
            event=a[a.in_event];negative=a[~a.in_event]
            seen=event[event.informative_valid_reads>0]
            macro_hit=event[event.macro_score>cal['macro']*cal['joint'][method]]
            acquired_house=set();false_house=set()
            truth=set(ep.affected_ids)
            for row in event.itertuples():
                ids=set(np.fromstring(str(row.alarming_households),sep=' ',dtype=int)) if pd.notna(row.alarming_households) else set()
                acquired_house.update(ids&truth);false_house.update(ids-truth)
            delay=int(hit.step.min()-ep.onset) if len(hit) else cfg['miss_delay_steps']
            sham=alarms[(alarms.episode=='b%02d_none_0.0'%ep.background)&(alarms.method==method)
                &(alarms.step>=ep.onset)&(alarms.step<ep.onset+cfg['detection_limit_steps'])]
            sham_group=any(len(set(np.fromstring(str(v),sep=' ',dtype=int))&set(ep.affected_groups))>0
                for v in sham.alarming_groups if pd.notna(v))
            event_rows.append(dict(episode=ep.episode,background=ep.background,week=int(ep.background)//2,
                family=ep.family,magnitude=ep.magnitude,method=method,event_duration=ep.duration,
                detected=bool(len(hit)),correct_group_detected=bool(len(local)),delay_steps=delay,
                missed=not bool(len(hit)),negative_steps=len(negative),negative_alarms=int(negative.alarm.sum()),
                matched_background_detected=bool(sham.alarm.any()),
                matched_background_group_detected=sham_group,
                detection_minus_matched_background=int(bool(len(hit)))-int(bool(sham.alarm.any())),
                localization_minus_matched_background=int(bool(len(local)))-int(sham_group),
                peak_score_in_detection_window=float(limit.score.max()),
                median_negative_score=float(negative.score.median()) if len(negative) else np.nan,
                negative_alarm_rate=float(negative.alarm.mean()) if len(negative) else np.nan,
                any_negative_alarm=bool(negative.alarm.any()),event_alarm_steps=int(event.alarm.sum()),
                correct_house_instances=int(event.correct_house_alarms.sum()),false_house_instances=int(event.false_house_alarms.sum()),
                correct_house_unique=len(acquired_house),false_house_unique=len(false_house),
                affected_households=len(truth),house_localization_recall=len(acquired_house)/len(truth) if truth else np.nan,
                false_group_instances=int(event.false_group_alarms.sum()),
                first_informative_read_step=float(seen.step.min()-ep.onset) if len(seen) else np.nan,
                first_macro_alarm_step=float(macro_hit.step.min()-ep.onset) if len(macro_hit) else np.nan,
                local_detection_step=float(local.step.min()-ep.onset) if len(local) else np.nan,
                zero_effect=ep.zero_effect))
    events=pd.DataFrame(event_rows);events.to_csv(out/'episode_detection.csv',index=False)
    agg=events.groupby(['family','magnitude','method']).agg(
        backgrounds=('background','nunique'),detection_rate=('detected','mean'),
        correct_group_rate=('correct_group_detected','mean'),mean_delay_including_misses=('delay_steps','mean'),
        matched_background_detection_rate=('matched_background_detected','mean'),
        detection_excess_over_background=('detection_minus_matched_background','mean'),
        localization_excess_over_background=('localization_minus_matched_background','mean'),
        missed_fraction=('missed','mean'),house_recall=('house_localization_recall','mean'),
        false_house_instances=('false_house_instances','mean'),false_group_instances=('false_group_instances','mean'),
        median_peak_detection_score=('peak_score_in_detection_window','median'),
        negative_alarm_rate=('negative_alarm_rate','mean'),any_negative_alarm=('any_negative_alarm','mean')).reset_index()
    agg.to_csv(out/'detection_summary.csv',index=False)
    keys=['episode','background','family','magnitude','onset','duration']
    m=metrics.merge(meta[keys],on='episode',validate='many_to_one')
    m['phase']=np.where(m.relative_target_step<0,'before',np.where(m.relative_target_step<m.duration,'during','after'))
    m.loc[m.family=='none','phase']='background'
    numeric=['mae','mse','coverage','width','adjusted_coverage','adjusted_width','score']
    per=m.groupby(['episode','background','family','magnitude','method','horizon','level','phase'])[numeric].mean().reset_index()
    per.to_csv(out/'episode_forecasts.csv',index=False)
    forecast=per.groupby(['family','magnitude','method','horizon','level','phase'])[numeric].mean().reset_index()
    forecast['rmse']=np.sqrt(forecast.mse);forecast.to_csv(out/'forecast_summary.csv',index=False)
    c=costs.merge(meta[['episode','background','family','magnitude']],on='episode')
    cost_summary=c.groupby('method').agg(updates=('step','size'),fine_attempts=('fine_attempts','sum'),
        fine_valid=('fine_valid','sum'),fine_bytes=('fine_bytes','sum'),summary_bytes=('summary_bytes','sum'),
        median_update_seconds=('complete_seconds','median'),p95_update_seconds=('complete_seconds',lambda x:x.quantile(.95)),
        mean_fine_per_step=('fine_attempts','mean'),median_state_bytes=('state_bytes','median'),
        median_after_eviction_bytes=('after_eviction_bytes','median'),median_detail_bytes=('detail_bytes','median'),
        peak_gpu_bytes=('gpu_peak_bytes','max'),peak_host_bytes=('host_peak_bytes','max'),
        payload_transfer_bytes=('payload_transfer_bytes','sum'),expired_fine_cells=('expired_fine_cells','sum'),
        groups_rebuilt=('groups_rebuilt','sum')).reset_index()
    cost_summary.to_csv(out/'cost_summary.csv',index=False)
    # Paired time-block differences, with variants nested in each background.
    physical=events[events.family.isin(cfg['families'])]
    paired=physical.pivot(index=['background','family','magnitude'],columns='method',values='delay_steps')
    differences=(paired.M3-paired.M2).groupby(level=0).mean().rename('M3_minus_M2_delay_steps')
    differences.to_csv(out/'paired_background_delay.csv')
    per[(per.level=='affected')&(per.phase=='during')].pivot(
        index=['background','family','magnitude','horizon'],columns='method',values='mae').to_csv(out/'paired_local_forecasts.csv')
    # Exact cancellation must leave M0's macro-only detector identical to background.
    m0=alarms[alarms.method=='M0'].merge(meta[['episode','background','family','magnitude']],on='episode')
    paired_macro=m0[m0.family=='cancel_exact'].merge(
        m0[m0.family=='none'][['background','step','macro_score']],on=['background','step'],suffixes=('_cancel','_background'))
    max_macro=float(abs(paired_macro.macro_score_cancel-paired_macro.macro_score_background).max())
    if max_macro>1e-7:raise ArithmeticError('Exact cancellation changed the macro-only score')
    if checks.same_information_max_abs.max()>cfg['consistency_tolerance']:raise ArithmeticError('Representation mismatch')
    budget=int(cfg['households']*cfg['fine_budget_fraction'])
    if costs[costs.method.isin(['M1','M2','M3','M3_fixed'])].fine_attempts.max()>budget:raise ArithmeticError('Budget violation')
    summary=dict(episodes=len(meta),backgrounds=int(meta.background.nunique()),weeks=4,
        demand_shock_episodes=int(meta.family.isin(cfg['families']).sum()),background_controls=int((meta.family=='none').sum()),
        measurement_fault_controls=int((meta.family=='sensor_fault').sum()),households=cfg['households'],
        episode_updates=len(meta)*cfg['steps'],method_updates=len(costs),
        same_information_max_abs=float(checks.same_information_max_abs.max()),
        cancellation_macro_score_max_difference=max_macro,
        zero_effect_noncontrol_episodes=int(((meta.family!='none')&meta.zero_effect).sum()),
        unique_target_intervals=len(target_support),
        unique_observed_household_targets=int(sum(v.sum() for v in target_support.values())),
        complete_population_observed_target_intervals=int(sum(v.all() for v in target_support.values())),
        scalar_forecast_count=int(metrics['count'].sum()),
        summed_episode_seconds=float(meta.seconds.sum()),
        summed_measured_method_update_seconds=float(costs.complete_seconds.sum()),
        shared_household_temporal_covariance_bytes=int(2*cfg['households']*cfg['window']**2*8),
        observation_cache_bytes_per_method=int(cfg['households']*cfg['window']*8),
        accounting_caveat='Per-method time includes channel/policy/inference/current-summary scan; whole-job time additionally includes common window preparation, evaluation, serialization and startup. GPU peak is the combined comparison process, not isolated per-method peak.',
        inference_scope='Finite-window working Gaussian; no exact adaptive-selection coverage claim',
        bookkeeping_correction='informative_valid_reads reconstructed from access IDs, native masks and current overlay; raw observed_affected counts attempted affected IDs',
        nominal_alarm_budget_per_step=cfg['alarm_probability_per_step_target'],
        no_point_adjustment=True,no_independent_hour_inference=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    boundary_cost=pd.read_csv(run/'boundary_costs.csv.gz')
    boundary_access=pd.read_csv(run/'boundary_access.csv.gz',keep_default_na=False)
    boundary_metrics=pd.read_csv(run/'boundary_metrics.csv.gz')
    diagnostic=[]
    for method,bc in boundary_cost.groupby('method'):
        ba=boundary_access[(boundary_access.method==method)&(boundary_access.kind=='refinement')]
        selected=[]
        for row in ba.itertuples():
            ids=np.fromstring(row.households,sep=' ',dtype=int)
            selected.append(int(np.bincount(model['groups'][ids],minlength=16).argmax()))
        bm=boundary_metrics[(boundary_metrics.method==method)&(boundary_metrics.level=='affected')&(boundary_metrics.horizon==2)]
        diagnostic.append(dict(method=method,fine_attempts=int(bc.fine_attempts.sum()),
            extra_read_first_update=int(ba.step.min()-cfg['window']+1) if len(ba) else None,
            dominant_refinement_groups=sorted(set(selected)),
            expired_cells=int(bc.expired_fine_cells.sum()),rereads=int(bc.source_rereads.sum()),
            groups_rebuilt=int(bc.groups_rebuilt.sum()),mean_affected_one_hour_mae=float(bm.mae.mean()),
            total_inference_seconds=float(bc.complete_seconds.sum()),
            caveat='One declared boundary episode; no separate alarm calibration, not pooled into primary detection rates'))
    (out/'boundary_diagnostic.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
    plot(out,meta,alarms,agg,per,m,cost_summary,events,figdata,cfg,cal)
    print(json.dumps(summary,indent=2),flush=True)


def plot(out,meta,alarms,agg,per,m,cost,events,data,cfg,cal):
    folder=Path('reports/figures/shock');folder.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
    methods=['M0','M1','M2','M3','M4']
    def save(name):
        plt.savefig(folder/(name+'.pdf'),bbox_inches='tight');plt.savefig(folder/(name+'.svg'),bbox_inches='tight')
        p=folder/(name+'.svg');p.write_text('\n'.join(x.rstrip() for x in p.read_text().splitlines())+'\n');plt.close()
    eid='b00_cancel_exact_3.0';ep=meta[meta.episode==eid].iloc[0]
    fig,axes=plt.subplots(4,1,figsize=(11,10),sharex=True)
    p=data[(data.episode==eid)&(data.method=='M3')&(data.horizon==2)].sort_values('step')
    x=p.step.values
    axes[0].plot(x,p.current_region,'k-',label='Current observed-support total')
    axes[0].plot(x,p.current_region-p.current_signature,'--',color=COLORS['M1'],label='Unmodified total (coincident)')
    axes[0].set_ylabel('Regional kWh / half-hour');axes[0].legend(fontsize=8)
    for ax,side in zip(axes[1:3],['plus','minus']):
        ax.plot(x,p['current_'+side],'k-',label='Observed current local mean')
        for method in ['M0','M1','M3','M4']:
            pp=data[(data.episode==eid)&(data.method==method)&(data.horizon==2)].sort_values('step')
            ax.plot(pp.step+2,pp['forecast_'+side],color=COLORS[method],label=NAMES[method])
        ax.set_ylabel(('Positive' if side=='plus' else 'Negative')+' side\nkWh / household / half-hour')
    axes[1].legend(ncol=3,fontsize=8)
    a=alarms[(alarms.episode==eid)&(alarms.method=='M3')].sort_values('step')
    axes[3].plot(a.step,a.informative_valid_reads,color=COLORS['M3'],label='Affected valid fine readings')
    axes[3].scatter(a.step[a.alarm],np.zeros(int(a.alarm.sum())),marker='x',color='k',label='Alarm')
    axes[3].scatter(a.step[a.active_group==ep.group],np.full(int((a.active_group==ep.group).sum()),-1.),s=12,color=COLORS['M1'],label='Affected group selected')
    axes[3].set_ylabel('Acquired readings');axes[3].set_xlabel('Half-hour update index; forecasts plotted at their target time')
    axes[3].legend(ncol=3,fontsize=8)
    for ax in axes:
        ax.axvline(ep.onset,color='black',linestyle=':');ax.axvline(ep.onset+ep.duration,color='black',linestyle=':');ax.grid(alpha=.2)
    fig.suptitle('Preselected within-group cancellation: real background, synthetic disturbance')
    fig.tight_layout(rect=(0,0,1,.96));save('shock_episode')
    fig,axes=plt.subplots(1,3,figsize=(14,6),gridspec_kw={'width_ratios':[1.2,1.2,1]})
    keys=[(f,v) for f in cfg['families'] for v in cfg['magnitudes']]
    for ax,column,title in zip(axes[:2],['detection_rate','correct_group_rate'],['Any alarm within 3 hours','Correct-group alarm within 3 hours']):
        table=agg[agg.family.isin(cfg['families'])].pivot(index=['family','magnitude'],columns='method',values=column).reindex(index=keys,columns=methods)
        ax.imshow(table.values,aspect='auto',vmin=0,vmax=1,cmap='Blues')
        ax.set_yticks(range(len(keys)));ax.set_yticklabels([f+' / '+str(v)+' SD' for f,v in keys])
        ax.set_xticks(range(len(methods)));ax.set_xticklabels(methods);ax.set_title(title)
        for i in range(len(keys)):
            for j in range(len(methods)):
                value=table.values[i,j];ax.text(j,i,format(value,'.2f'),ha='center',va='center',color='white' if value>.65 else 'black',fontsize=8)
    no=events[events.family=='none'].groupby('method').negative_alarm_rate.mean().reindex(methods)
    axes[2].bar(range(len(methods)),no.values,color=[COLORS[m] for m in methods]);axes[2].axhline(.02,color='k',ls='--',label='Calibration target')
    axes[2].set_xticks(range(len(methods)));axes[2].set_xticklabels(methods);axes[2].set_ylabel('Unmodified-background alarm steps / steps');axes[2].legend(fontsize=8)
    axes[2].set_title('Realized negative-control alarms')
    fig.suptitle('Eight paired backgrounds; requested SD magnitudes, descriptive rates, no point adjustment')
    fig.tight_layout(rect=(0,0,1,.95));save('shock_detection')
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    physical=events[events.family.isin(cfg['families'])]
    delays=physical.groupby('method').delay_steps.mean()
    cc=cost.set_index('method')
    for method in COLORS:
        marker='x' if method=='M3_fixed' else 'o'
        axes[0].scatter(cc.loc[method,'mean_fine_per_step'],delays[method]*.5,color=COLORS[method],marker=marker,label=NAMES[method],s=65)
        axes[1].scatter(cc.loc[method,'median_state_bytes']/1e6,cc.loc[method,'median_update_seconds']*1000,color=COLORS[method],marker=marker,s=65)
    axes[0].set_xscale('symlog',linthresh=50);axes[0].set_xlabel('Fine readings attempted per half-hour');axes[0].set_ylabel('Mean delay (hours); misses assigned 3.5 h')
    axes[1].set_xlabel('Separator + retained detail (MB)\nShared model/cache excluded');axes[1].set_ylabel('Acquisition + GPU inference median (ms)')
    axes[1].set_ylim(0,float(cc.p95_update_seconds.max())*1100)
    during=per[(per.level=='affected')&(per.phase=='during')&(per.horizon==2)&per.family.isin(['localized','cancel_exact','cancel_approx','delayed','ramp'])]
    local=during.groupby('method').mae.mean().reindex(list(COLORS))
    axes[2].bar(range(len(local)),local.values,color=[COLORS[k] for k in local.index]);axes[2].set_xticks(range(len(local)));axes[2].set_xticklabels(local.index,rotation=30)
    axes[2].set_ylabel('Affected-household one-hour MAE (kWh / half-hour)')
    axes[0].legend(fontsize=7);fig.suptitle('Acquisition, representation and complete cost are separate comparisons')
    for ax in axes:ax.grid(axis='y',alpha=.2)
    fig.tight_layout(rect=(0,0,1,.92));save('shock_resource_tradeoff')
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,level,families in [(axes[0,0],'affected',['localized','cancel_exact','cancel_approx','delayed','ramp']),
                              (axes[0,1],'regional',['regional','localized','cancel_approx','delayed','ramp'])]:
        panel=m[(m.horizon==2)&(m.level==level)&m.family.isin(families)]
        for method in methods:
            q=panel[panel.method==method].groupby(['background','relative_target_step']).mae.mean().groupby('relative_target_step').mean()
            ax.plot(q.index*.5,q.values,color=COLORS[method],label=method)
        ax.axvline(0,color='k',ls=':');ax.set_xlabel('Target hours relative to shock onset')
        ax.set_ylabel(('Affected-household' if level=='affected' else 'Observed-support regional')+' MAE\nkWh / half-hour');ax.legend(ncol=3,fontsize=8);ax.grid(alpha=.2)
    negative=per[(per.family=='none')&(per.horizon==2)&(per.level=='regional')].groupby('method')[['coverage','adjusted_coverage','width','adjusted_width']].mean().reindex(methods)
    x=np.arange(len(methods))
    for ax,columns,title in [(axes[1,0],['coverage','adjusted_coverage'],'Negative control: regional 90% coverage'),
                             (axes[1,1],['width','adjusted_width'],'Negative control: interval width')]:
        ax.bar(x-.18,negative[columns[0]],.36,label='Raw',color='#999999');ax.bar(x+.18,negative[columns[1]],.36,label='Earlier-segment correction',color='#0072B2')
        ax.set_xticks(x);ax.set_xticklabels(methods);ax.set_title(title);ax.legend(fontsize=8)
    axes[1,0].axhline(.9,color='k',ls='--');axes[1,0].set_ylim(0,1);axes[1,1].set_ylabel('kWh / half-hour')
    fig.suptitle('Forecast error and calibration on later exploratory development backgrounds')
    fig.tight_layout(rect=(0,0,1,.95));save('shock_forecasts_calibration')
    (folder/'PROVENANCE.md').write_text('Generated by `python scripts/analyze_shock.py` from the frozen `results/shock/run` numeric outputs. The first episode is fixed as background 0, exact cancellation, magnitude 3. All inputs are real development readings plus declared synthetic overlays. Forecast lines are aligned to target time; plotted uncertainty/coverage is empirical working-model output, not a superiority confidence interval. Rates average paired backgrounds, not independent hours.\n')


if __name__=='__main__':main()
