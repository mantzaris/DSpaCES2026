"""Read-only original-output audit and newly reconstructed causal-path figures."""
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    out=Path('results/acquisition/analysis');out.mkdir(parents=True,exist_ok=True)
    root=Path('results/shock/analysis')
    det=pd.read_csv(root/'episode_detection.csv');fore=pd.read_csv(root/'episode_forecasts.csv')
    costs=pd.read_csv(root/'audited_costs.csv.gz');alarm=pd.read_csv(root/'audited_alarms.csv.gz')
    meta=pd.DataFrame(json.loads(Path('results/shock/run/episodes.json').read_text()))
    table=[]
    for (family,method),a in det.groupby(['family','method']):
        ids=a.episode.tolist();f=fore[(fore.episode.isin(ids))&(fore.method==method)&(fore.horizon==2)]
        c=costs[(costs.episode.isin(ids))&(costs.method==method)]
        al=alarm[(alarm.episode.isin(ids))&(alarm.method==method)]
        table.append(dict(family=family,method=method,episodes=len(a),detected=int(a.detected.sum()),
            localized=int(a.correct_group_detected.sum()),miss_inclusive_delay_steps=float(a.delay_steps.mean()),
            correct_house_unique_sum=int(a.correct_house_unique.sum()),false_house_instances=int(a.false_house_instances.sum()),
            false_group_instances=int(a.false_group_instances.sum()),negative_alarms=int(a.negative_alarms.sum()),negative_steps=int(a.negative_steps.sum()),
            negative_alarm_rate=float(a.negative_alarms.sum()/max(1,a.negative_steps.sum())),
            local_mae=float(f[(f.level=='affected')&(f.phase=='during')].mae.mean()),
            regional_mae=float(f[(f.level=='regional')&(f.phase=='during')].mae.mean()),
            requested=int(c.fine_attempts.sum()),read=int(c.fine_valid.sum()),fine_bytes=int(c.fine_bytes.sum())))
    pd.DataFrame(table).to_csv(out/'original_family_method.csv',index=False)
    loc=fore[(fore.family.isin(['localized','cancel_exact','cancel_approx','delayed','ramp']))&(fore.level=='affected')&(fore.phase=='during')&(fore.horizon==2)]
    rates=alarm[alarm.episode.str.contains('_none_')].groupby('method').alarm.mean().to_dict()
    summary=dict(original_episodes=len(meta),demand_episodes=int(meta.family.isin(['regional','localized','cancel_exact','cancel_approx','delayed','ramp']).sum()),
        households=4194,backgrounds=8,local_mae=loc.groupby('method').mae.mean().to_dict(),negative_alarm_rates=rates,
        exact_cancellation_localizations=det[det.family=='cancel_exact'].groupby('method').correct_group_detected.sum().to_dict())
    scores=pd.read_csv('results/shock/calibrate/scores.csv');cal=json.loads(Path('results/shock/calibration.json').read_text())
    calrows=[]
    for m,a in scores.groupby('method'):
        z=np.maximum(a.macro/cal['macro'],a.fine/cal['fine'][m])/cal['joint'][m]
        for burn in [0,1,8]:
            later=alarm[(alarm.method==m)&alarm.episode.str.contains('_none_')&(alarm.step>=burn)]
            calrows.append(dict(method=m,burn_steps=burn,calibration_alarm_steps=int((z[a.step>=burn]>1).sum()),
                calibration_steps=int((a.step>=burn).sum()),later_alarm_steps=int(later.alarm.sum()),later_steps=len(later),
                units='per update any-channel across all groups/acquired households'))
    pd.DataFrame(calrows).to_csv(out/'alarm_denominators.csv',index=False)
    diagnostic=Path('results/acquisition/diagnostic')
    if diagnostic.exists():
        e=pd.read_csv(diagnostic/'episodes.csv');s=pd.read_csv(diagnostic/'steps.csv.gz')
        demand=e[~e.family.isin(['none','sensor_fault'])]
        counts={'Demand shocks':len(demand),'Informative fine exposure':int((demand.fine_hits_steps>0).sum()),
            'Informative probe exposure':int((demand.probe_hits_steps>0).sum()),
            'Probe innovations changed':int(demand.first_innovation_difference.notna().sum()),
            'Group scores changed':int(demand.first_score_difference.notna().sum()),
            'Ranking changed during event':int((demand.ranking_changed_steps>0).sum()),
            'Trigger changed during event':int((demand.trigger_changed_steps>0).sum()),
            'Action changed during event':int((demand.action_changed_steps>0).sum()),
            'Actual IDs changed':int((demand.read_identity_changed_steps>0).sum())}
        summary['path_counts']=counts
        summary['max_score_reproduction_error']=float(e.score_reproduction_max.max())
        summary['identity_comparisons']=len(s)
        summary['all_ordered_id_hashes_match_original']=bool((s.requested_identity_hash==s.original_identity_hash).all())
        summary['requested_read_assimilated']=e[['requested','read','assimilated']].sum().to_dict()
        summary['probe_hit_no_score_change']=int(((demand.probe_hits_steps>0)&demand.first_score_difference.isna()).sum())
        summary['no_informative_fine_exposure']=int((demand.fine_hits_steps==0).sum())
        summary['budget_blocks']=int(e.budget_block_steps.sum())
        top=[]
        for bg,block in s.groupby('background'):
            control=block[block.family=='none'].set_index('step')
            for eid,z in block[~block.family.isin(['none','sensor_fault'])].groupby('episode'):
                z=z.set_index('step');changed=z.best_group!=control.best_group
                top.append(dict(episode=eid,best_group_changed_steps=int(changed.sum()),
                    best_group_changed_during_event=int((changed&z.in_event).sum()),
                    changed_toward_affected_steps=int((changed&z.in_event&z.affected_top_group).sum())))
        pd.DataFrame(top).to_csv(out/'top_rank_differences.csv',index=False)
        summary['best_group_changed_episodes']=sum(r['best_group_changed_during_event']>0 for r in top)
        summary['best_group_changed_toward_affected_episodes']=sum(r['changed_toward_affected_steps']>0 for r in top)
        family=demand.groupby('family').agg(episodes=('episode','size'),fine_exposure=('fine_hits_steps',lambda x:int((x>0).sum())),
            probe_exposure=('probe_hits_steps',lambda x:int((x>0).sum())),score_change=('first_score_difference',lambda x:int(x.notna().sum())),
            rank_change=('ranking_changed_steps',lambda x:int((x>0).sum())),trigger_change=('trigger_changed_steps',lambda x:int((x>0).sum())),
            affected_top=('affected_top_group_steps',lambda x:int((x>0).sum())),affected_active=('affected_active_steps',lambda x:int((x>0).sum())))
        family.to_csv(out/'path_by_family.csv')
        # Uniform-without-replacement reference is one draw set, NOT this deterministic rotating schedule.
        opportunity=[]
        for ep in meta.itertuples():
            K=len(ep.affected_ids);N=4194;m=41
            logmiss=sum(math.log((N-K-i)/(N-i)) for i in range(m)) if N-K>=m else -np.inf
            opportunity.append(dict(episode=ep.episode,ever_affected_households=K,uniform_one_set_miss_probability=math.exp(logmiss),
                caveat='Event-wide K reference only; native/current availability varies. No independent-step multiplication.'))
        pd.DataFrame(opportunity).to_csv(out/'sampling_reference.csv',index=False)
        figdir=Path('reports/figures/acquisition');figdir.mkdir(parents=True,exist_ok=True)
        plt.rcParams.update({'font.size':9,'svg.fonttype':'none','pdf.fonttype':42})
        fig,ax=plt.subplots(figsize=(8,4.2));names=list(counts);values=list(counts.values())
        ax.barh(names[::-1],values[::-1],color='#0072B2');ax.set_xlim(0,105);ax.set_xlabel('Episodes out of 96 demand shocks (eight backgrounds)')
        for i,v in enumerate(values[::-1]):ax.text(v+.6,i,str(v),va='center')
        fig.tight_layout()
        for ext in ['pdf','svg']:fig.savefig(figdir/('observation_action.'+ext))
        plt.close(fig)
        # Preselected original b00 exact-cancellation magnitude3, not a chosen successful anecdote.
        a=s[s.episode=='b00_cancel_exact_3.0'];b=s[s.episode=='b00_none_0.0']
        fig,axes=plt.subplots(3,1,figsize=(8,6),sharex=True)
        axes[0].plot(a.step,a.affected_probe_z,label='Affected acquired-probe |innovation|',color='#D55E00')
        axes[0].plot(a.step,a.affected_fine_z,label='Affected any-acquired |innovation|',color='#009E73',alpha=.8)
        axes[0].set_ylabel('Standard deviations');axes[0].legend(loc='upper left',fontsize=8)
        axes[1].plot(a.step,a.best_score,label='Shock max group score',color='#D55E00')
        axes[1].plot(b.step,b.best_score,label='Background max group score',linestyle='--',color='#0072B2')
        axes[1].axhline(cal['trigger'],color='black',linestyle=':',label='Frozen trigger');axes[1].set_ylabel('Group score');axes[1].legend(fontsize=8)
        axes[2].step(a.step,a.active_group,where='mid',label='Activated group (-1 = rotating)')
        axes[2].scatter(a[a.probe_hits>0].step,np.full(int((a.probe_hits>0).sum()),-1),marker='x',color='#D55E00',label='Affected probe hit')
        axes[2].set_ylabel('Group');axes[2].set_xlabel('Half-hour updates');axes[2].legend(fontsize=8)
        for ax in axes:ax.axvspan(a.onset.iloc[0],a.onset.iloc[0]+a.duration.iloc[0],color='grey',alpha=.1)
        fig.suptitle('Observed local change can remain below the acquisition trigger\nOriginal preselected cancellation episode; same reading IDs, different values',fontsize=10)
        fig.tight_layout(rect=[0,0,1,.93])
        for ext in ['pdf','svg']:fig.savefig(figdir/('observed_not_acted.'+ext))
        plt.close(fig)
        a.to_csv(out/'annotated_trace.csv',index=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
