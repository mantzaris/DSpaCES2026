"""Regenerate manuscript results from immutable saved outputs, without meter data/GPU.

Run from repository root with PYTHONPATH=src:.deps python3 ... .
No model, threshold, acquisition, or forecast is rerun by this script.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path('results/synthesis')
FIG = Path('manuscript/figures')
GEN = Path('manuscript/generated')
SOURCES = {}
COLORS = dict(M0='#666666', M1='#CC79A7', M2='#E69F00', M3='#D55E00', M3b='#0072B2', M4='#009E73')


def source(path):
    p = Path(path)
    SOURCES[path] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p


def csv(path, **kw):
    return pd.read_csv(source(path), **kw)


def js(path):
    return json.loads(source(path).read_text())


def save(fig, name):
    for ext in ['pdf', 'svg']:
        fig.savefig(FIG/(name+'.'+ext), bbox_inches='tight')
    svg=FIG/(name+'.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


def summarize(detection, forecasts, cohort):
    demand = detection[~detection.family.isin(['none', 'sensor_fault'])]
    local = forecasts[(forecasts.level == 'affected') & (forecasts.phase == 'during') &
                      ~forecasts.family.isin(['regional', 'none', 'sensor_fault'])]
    rows = []
    for method in sorted(demand.method.unique()):
        d = demand[demand.method == method]
        n = detection[(detection.method == method) & (detection.family == 'none')]
        a = local[(local.method == method) & (local.horizon == 2)]
        b = local[(local.method == method) & (local.horizon == 12)]
        rows.append(dict(cohort=cohort, method=method, demand_episodes=len(d),
            detected=int(d.detected.sum()), localized=int(d.localized.sum()),
            miss_inclusive_delay_hours=float(d.delay_steps.mean()/2),
            local_episodes=len(a), backgrounds=a.background.nunique(),
            local_one_hour_mae=float(a.mae.mean()), local_six_hour_mae=float(b.mae.mean()),
            negative_alarms=int(n.negative_alarms.sum()), negative_steps=int(n.negative_steps.sum())))
    paired = local[local.horizon == 2].pivot_table(index=['background', 'family'], columns='method', values='mae')
    # Magnitudes averaged within background/family; equal family weighting thereafter.
    paired = paired.groupby(level=0).mean()
    paired.to_csv(OUT/('paired_background_'+cohort+'.csv'))
    return pd.DataFrame(rows), paired


def main():
    for p in [OUT, FIG, GEN]:
        p.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size':8.5, 'axes.titlesize':9, 'legend.fontsize':8,
                         'pdf.fonttype':42, 'svg.fonttype':'none', 'axes.spines.top':False,
                         'axes.spines.right':False})
    d3 = csv('results/shock/analysis/episode_detection.csv').rename(columns={'correct_group_detected':'localized'})
    f3 = csv('results/shock/analysis/episode_forecasts.csv')
    d4 = csv('results/acquisition/comparison/episodes.csv')
    f4 = csv('results/acquisition/comparison/forecasts.csv')
    d4 = d4[d4.phase == 'fresh'].copy()
    f4 = f4[f4.phase == 'fresh'].drop(columns='phase').rename(columns={'forecast_phase':'phase'})
    s3, p3 = summarize(d3, f3, 'B')
    s4, p4 = summarize(d4, f4, 'C')
    principal = pd.concat([s3, s4], ignore_index=True)
    principal.to_csv(OUT/'principal_results.csv', index=False)
    background_events=[]
    for cohort,d in [('B',d3),('C',d4)]:
        for (background,method),a in d.groupby(['background','method']):
            demand=a[~a.family.isin(['none','sensor_fault'])]
            none=a[a.family=='none']
            background_events.append(dict(cohort=cohort,background=int(background),method=method,
                demand_episodes=len(demand),detected=int(demand.detected.sum()),
                localized=int(demand.localized.sum()),misses=int(demand.missed.sum()),
                miss_inclusive_delay_hours=float(demand.delay_steps.mean()/2),
                control_alarms=int(none.negative_alarms.sum()),control_updates=int(none.negative_steps.sum())))
    be=pd.DataFrame(background_events)
    for col in ['detected','localized','misses','miss_inclusive_delay_hours','control_alarms']:
        ref=be[be.method=='M2'].set_index(['cohort','background'])[col].to_dict()
        be[col+'_minus_random']=[r[col]-ref[(r['cohort'],r['background'])] for r in be.to_dict('records')]
    be.to_csv(OUT/'paired_background_events.csv',index=False)
    families = []
    for cohort, d, f in [('B',d3,f3),('C',d4,f4)]:
        for (family,method), a in d.groupby(['family','method']):
            ff=f[(f.family==family)&(f.method==method)&(f.horizon==2)&f.phase.isin(['during','background'])]
            row=dict(cohort=cohort,family=family,method=method,episodes=len(a),
                detection=int(a.detected.sum()),localization=int(a.localized.sum()),
                delay_hours=float(a.delay_steps.mean()/2),negative_alarms=int(a.negative_alarms.sum()),
                negative_steps=int(a.negative_steps.sum()))
            for level in ['affected','regional','household']:
                row[level+'_mae']=float(ff[ff.level==level].mae.mean())
            families.append(row)
    pd.DataFrame(families).to_csv(OUT/'family_method_results.csv',index=False)
    assert s3.set_index('method').loc['M3','detected']==29
    assert s3.set_index('method').loc['M3','localized']==15
    assert s4.set_index('method').loc['M3b','localized']==2
    assert abs(s3.set_index('method').loc['M3','local_one_hour_mae']-.1695947270)<1e-9
    assert abs(s4.set_index('method').loc['M3b','local_one_hour_mae']-.2660244222)<1e-9
    assert d3[(d3.family=='cancel_exact') & d3.method.isin(['M2','M3','M4'])].localized.sum()==0

    steps=csv('results/acquisition/diagnostic/steps.csv.gz')
    cal=js('results/shock/calibration.json'); cal4=js('results/acquisition/calibration.json')
    controls={int(b):a.sort_values('step') for b,a in steps[steps.family=='none'].groupby('background')}
    margin_rows=[]; pathrows=[]
    for ep,a in steps[~steps.family.isin(['none','sensor_fault'])].groupby('episode'):
        a=a.sort_values('step');b=controls[int(a.background.iloc[0])]
        q=np.array([json.loads(x) for x in a.scores]);q0=np.array([json.loads(x) for x in b.scores])
        epsilon=np.max(np.abs(q-q0),axis=1);margin=np.abs(q0.max(axis=1)-cal['trigger'])
        gate=q.max(axis=1)>cal['trigger'];gate0=q0.max(axis=1)>cal['trigger']
        certified=epsilon<margin
        assert np.all(gate[certified]==gate0[certified])
        assert not a.read_identity_changed.any()
        assert (a.requested_identity_hash==a.original_identity_hash).all()
        for i,r in enumerate(a.itertuples()):
            margin_rows.append(dict(episode=ep,background=int(r.background),family=r.family,step=r.step,
                epsilon=float(epsilon[i]),baseline_gate_margin=float(margin[i]),
                baseline_max_score=float(q0[i].max()),shock_max_score=float(q[i].max()),
                sufficient_unchanged_gate=bool(certified[i]),gate_changed=bool(gate[i]!=gate0[i]),
                in_event=bool(r.in_event)))
        event=a[a.in_event]
        pathrows.append(dict(episode=ep,background=int(a.background.iloc[0]),family=a.family.iloc[0],
            fine_exposed=bool((event.fine_hits>0).any()),probe_exposed=bool((event.probe_hits>0).any()),
            innovation_changed=bool((a.innovation_difference>1e-10).any()),
            score_changed=bool((a.score_difference>1e-10).any()),ranking_changed=bool(event.ranking_changed.any()),
            top_group_changed=bool(((q.argmax(axis=1)!=q0.argmax(axis=1)) & a.in_event.values).any()),
            gate_changed=bool(a.trigger_changed.any()),schedule_changed=bool(a.read_identity_changed.any()),
            budget_blocked=bool(a.budget_blocked.any())))
    margins=pd.DataFrame(margin_rows);margins.to_csv(OUT/'threshold_margins.csv.gz',index=False)
    paths=pd.DataFrame(pathrows);paths.to_csv(OUT/'diagnostic_path.csv',index=False)
    counts={k:int(paths[k].sum()) for k in paths.columns if k not in ['episode','background','family']}
    assert counts['score_changed']==93 and counts['probe_exposed']==94 and counts['schedule_changed']==0

    # Fresh IDs are compared in requested/assimilation order and as sets. Labels are
    # evaluator-only. Event-wide affected IDs indicate potential access, not a valid
    # nonzero reading at this particular instant; we do not silently equate them.
    access=csv('results/acquisition/run/access.csv.gz',keep_default_na=False)
    alarms=csv('results/acquisition/run/alarms.csv.gz')
    meta=js('results/acquisition/run/episodes.json')
    def selected(ep):
        a=access[(access.episode==ep)&(access.method=='M3b')]
        return {int(t)-23:np.concatenate([np.fromstring(r.households,sep=' ',dtype=int) for r in rows.itertuples()])
                for t,rows in a.groupby('step')}
    controls4={m['background']:selected(m['episode']) for m in meta if m['phase']=='fresh' and m['family']=='none'}
    timing=[]
    for m in meta:
        if m['phase']!='fresh' or m['family']=='none':continue
        chosen=selected(m['episode']);base=controls4[m['background']];affected=set(m['affected_ids'])
        a=alarms[(alarms.episode==m['episode'])&(alarms.method=='M3b')].set_index('step')
        for t,ids in chosen.items():
            changed=not np.array_equal(ids,base[t]);extra=set(ids)-set(base[t])
            timing.append(dict(episode=m['episode'],background=m['background'],family=m['family'],step=t,
                lag=t-m['onset'],in_detection_window=m['onset']<=t<=m['onset']+6,
                in_event=m['onset']<=t<m['onset']+m['duration'],ordered_change=changed,
                set_change=set(ids)!=set(base[t]),extra_ids=len(extra),
                extra_event_affected_ids=len(extra&affected),
                fine_max_z=float(a.loc[t,'fine_score']),
                effective_fine_alarm_threshold=cal4['fine']['M3b']*cal4['joint']['M3b'],
                fine_alarm_possible=bool(a.loc[t,'fine_score']>cal4['fine']['M3b']*cal4['joint']['M3b']),
                correct_group_alarms=int(a.loc[t,'correct_group_alarms'])))
    timing=pd.DataFrame(timing);timing.to_csv(OUT/'corrective_action_timing.csv',index=False)
    timing_summary=timing.groupby(['episode','background','family']).apply(lambda a:pd.Series({
        'changed_steps':int(a.ordered_change.sum()),
        'first_changed_lag':float(a[a.ordered_change].lag.min()),
        'changed_in_detection_window':int(a[a.in_detection_window].ordered_change.sum()),
        'extra_event_ids_in_detection_window':int(a[a.in_detection_window].extra_event_affected_ids.sum()),
        'extra_event_ids_later_in_event':int(a[a.in_event&~a.in_detection_window].extra_event_affected_ids.sum()),
        'max_fine_z_detection_window':float(a[a.in_detection_window].fine_max_z.max()),
        'any_fine_alarm_detection_window':bool(a[a.in_detection_window].fine_alarm_possible.any())})).reset_index()
    timing_summary.to_csv(OUT/'corrective_action_summary.csv',index=False)
    assert int((timing_summary.changed_steps>0).sum())==3

    # Paper tables contain generated values, never copied manual result rows.
    table=[]
    for cohort,methods in [('B',['M0','M1','M2','M3','M4']),('C',['M0','M2','M3','M3b','M4'])]:
        table.append('\\multicolumn{6}{l}{\\textit{Cohort '+cohort+'}} \\\\')
        for method in methods:
            r=principal[(principal.cohort==cohort)&(principal.method==method)].iloc[0]
            table.append('%s & %.4f & %d/%d & %d/%d & %d/%d & %.2f \\\\'%(
                method,r.local_one_hour_mae,r.detected,r.demand_episodes,r.localized,r.demand_episodes,
                r.negative_alarms,r.negative_steps,r.miss_inclusive_delay_hours))
    (GEN/'principal_rows.tex').write_text('\\begin{tabular}{lrrrrr}\\toprule\n'
        'Method & Local MAE & Detected & Localized & Alarmed control updates & Mean delay (h)\\\\\\midrule\n'
        +'\n'.join(table)+'\n\\bottomrule\\end{tabular}\n')
    costs=csv('results/refinement/replay/cost_summary.csv')
    checks=csv('results/refinement/replay/checks.csv')
    js('results/regional/ingestion.json');js('results/regional/model.json')
    js('results/refinement/replay/summary.json');js('results/refinement/training.json')
    csv('results/refinement/replay/outcome_summary.csv')
    csv('results/acquisition/analysis/alarm_denominators.csv')
    js('results/shock/analysis/decision_summary.json')
    js('results/acquisition/comparison/summary.json')
    for path in ['configs/regional_refinement.json','configs/regional_shock.json','configs/regional_acquisition.json',
                 'results/shock/frozen_manifest.json','results/acquisition/frozen.json','manifests/regional_source.json',
                 'src/evidence_fusion/shock_access.py','src/evidence_fusion/shock_gaussian.py',
                 'src/evidence_fusion/acquisition_policy.py','scripts/replay_shock.py',
                 'scripts/analyze_acquisition_comparison.py','scripts/analyze_shock.py']:
        source(path)
    summary=dict(path_counts=counts,gate_margin_steps=len(margins),
        sufficient_unchanged_steps=int(margins.sufficient_unchanged_gate.sum()),
        unexplained_gate_switches=int(margins.gate_changed.sum()),
        original_identity_hashes_matched=bool((steps.requested_identity_hash==steps.original_identity_hash).all()),
        stage3_requested=int(steps.requested.sum()),stage3_read=int(steps.read.sum()),stage3_assimilated=int(steps.assimilated.sum()),
        refinement_max_representation_error=float(checks.representation_error.max()),
        refinement_max_cycle_error=float(checks.cycle_error.max()),
        effective_alarm_threshold_M3=cal['fine']['M3']*cal['joint']['M3'],
        effective_alarm_threshold_M3b=cal4['fine']['M3b']*cal4['joint']['M3b'],
        timing_qualification='Extra event IDs are potential affected access from saved identities, not per-time valid nonzero readings. No meter archive was read.',
        cohorts=dict(B=dict(episodes=112,demand=96,local_mae=80,backgrounds=8,weeks=4),
                     C=dict(episodes=16,demand=12,local_mae=12,backgrounds=4,weeks=4)))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    macros={'MarginChecks':str(len(margins)), 'MarginCertified':str(summary['sufficient_unchanged_steps'])}
    (GEN/'numbers.tex').write_text('\n'.join('\\newcommand{\\%s}{%s}'%(k,v) for k,v in macros.items())+'\n')

    # 1. Model/interface diagram. Coordinates encode no empirical quantities.
    fig,ax=plt.subplots(figsize=(7.0,2.7));ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
    boxes=[(.1,2.35,2.35,1.2,'Household records\n2012 fit; Q1 replay\n4,194 meters','#eeeeee'),
           (3.0,2.35,3.0,1.2,'Provider interface\n16 sums + validity mask\nFine values on request','#d9eaf3'),
           (6.6,2.35,3.2,1.2,'One Gaussian model\nShared state + private detail\nRegional and local queries','#dcebdd'),
           (3.0,.25,3.0,1.2,'Acquisition policy\nProbes, scores, action\n209 requests/update','#f9e5bf'),
           (6.6,.25,3.2,1.2,'Representation/cache\nRetain or evict detail\nSame evidence, same queries','#f1ddec')]
    for x,y,w,h,label,color in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.05',facecolor=color,edgecolor='#555555'))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=8.7,linespacing=1.5)
    for start,end in [((2.5,2.95),(2.95,2.95)),((6.05,2.95),(6.55,2.95)),((4.15,1.5),(4.15,2.3)),((5.25,2.3),(5.25,1.5)),((8.2,1.5),(8.2,2.3))]:
        ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color='#444444',lw=1.2))
    ax.text(.1,.4,'Summary scans charged\nTargets isolated\nby evaluator\nNo physical grid assumed',fontsize=8)
    save(fig,'information_flow')

    # 2. The original preselected episode, not selected by its policy performance.
    example=csv('results/shock/figure_common_support.csv')
    trace=steps[steps.episode=='b00_cancel_exact_3.0'].sort_values('step')
    fig,axs=plt.subplots(2,2,figsize=(7.0,4.3),sharex=True)
    base=example[(example.horizon==2)&(example.method=='M0')].sort_values('step')
    onset=int(trace.onset.iloc[0]);duration=int(trace.duration.iloc[0]);x=(base.step-onset)*.5
    axs[0,0].plot(x,base.current_region,color='black');axs[0,0].set_ylabel('Observed regional sum (kWh)')
    axs[0,0].set_title('(a) All 16 injected group sums are zero')
    axs[0,1].plot(x,base.current_plus,label='Positive-shift meters',color='#0072B2')
    axs[0,1].plot(x,base.current_minus,label='Negative-shift meters',color='#D55E00')
    axs[0,1].set_ylabel('Observed local mean (kWh)');axs[0,1].legend(loc='upper right',fontsize=7)
    axs[0,1].set_title('(b) Real background plus paired shifts')
    for method in ['M0','M3','M4']:
        a=example[(example.horizon==2)&(example.method==method)].sort_values('step')
        axs[1,0].plot((a.step+2-onset)*.5,a.forecast_plus,color=COLORS[method],label=method)
    axs[1,0].plot(x+1,base.target_plus,color='black',label='Observed target',lw=1)
    axs[1,0].set_ylabel('Positive-set mean (kWh)');axs[1,0].set_title('(c) One-hour forecasts, target time')
    axs[1,0].legend(ncol=2,fontsize=7)
    xt=(trace.step-onset)*.5
    axs[1,1].plot(xt,trace.best_score,label='Largest acquisition score',color=COLORS['M3'])
    control=controls[0]
    axs[1,1].plot(xt,control.best_score.values,label='Paired background',color='#666666',ls=':',lw=1)
    axs[1,1].axhline(cal['trigger'],ls='--',color='black',label='Acquisition gate')
    axs[1,1].scatter(xt[trace.probe_hits>0],np.zeros((trace.probe_hits>0).sum()),marker='|',s=70,color='#0072B2',label='Affected probe read')
    axs[1,1].set_ylabel('Score');axs[1,1].set_title('(d) Information observed; schedule unchanged')
    axs[1,1].legend(fontsize=6.8,loc='upper right')
    for ax in axs.flat:
        ax.axvspan(0,duration*.5,color='gray',alpha=.10);ax.axvline(0,color='gray',lw=.7)
    axs[1,0].set_xlabel('Hours relative to onset');axs[1,1].set_xlabel('Hours relative to onset')
    fig.tight_layout();save(fig,'transparent_episode')

    # 3. Paired differences: show all background values, no false independent-hour CI.
    fig,axs=plt.subplots(1,2,figsize=(7.0,2.65),sharey=True)
    for ax,paired,cohort,names in [(axs[0],p3,'B: eight backgrounds',['M0','M1','M3','M4']),
                                  (axs[1],p4,'C: four reused backgrounds',['M0','M3','M3b','M4'])]:
        for i,method in enumerate(names):
            vals=(paired[method]-paired['M2']).values
            ax.scatter(i+np.linspace(-.12,.12,len(vals)),vals,c=COLORS[method],s=20)
            ax.plot([i-.2,i+.2],[vals.mean()]*2,color='black',lw=1.5)
        ax.axhline(0,color='gray',lw=.8);ax.set_xticks(range(len(names)));ax.set_xticklabels(names)
        ax.set_title(cohort);ax.set_xlabel('Compared with random acquisition M2')
    axs[0].set_ylabel('Paired one-hour local MAE difference\n(kWh per household; lower is better)')
    fig.tight_layout();fig.subplots_adjust(wspace=.28);save(fig,'paired_comparison')

    # 4. These are distinct diagnostic conditions, not a strict causal funnel.
    fig,axs=plt.subplots(1,2,figsize=(7.0,2.9))
    keys=['fine_exposed','probe_exposed','score_changed','ranking_changed','top_group_changed','gate_changed','schedule_changed']
    labels=['Fine exposure','Probe exposure','Score changed','Full rank changed','Top group changed','Gate changed','Schedule changed']
    axs[0].barh(np.arange(len(keys)),[counts[k] for k in keys],color='#0072B2')
    axs[0].set_yticks(np.arange(len(keys)));axs[0].set_yticklabels(labels);axs[0].invert_yaxis()
    for i,k in enumerate(keys):axs[0].text(counts[k]+1,i,str(counts[k]),va='center',fontsize=8)
    axs[0].set_xlim(0,110);axs[0].set_xlabel('Demand episodes / 96');axs[0].set_title('(a) Paired original-policy diagnostics')
    a=margins[margins.epsilon>1e-10]
    axs[1].scatter(a.baseline_gate_margin,a.epsilon,s=4,alpha=.25,color='#D55E00',rasterized=False)
    top=max(a.baseline_gate_margin.max(),a.epsilon.max())*1.04
    axs[1].plot([0,top],[0,top],'k--',lw=.7);axs[1].set_xlim(0,top);axs[1].set_ylim(0,top)
    axs[1].set_xlabel('Baseline distance to acquisition gate');axs[1].set_ylabel('Largest group-score perturbation')
    axs[1].set_title('(b) Below line: gate cannot switch')
    fig.tight_layout();save(fig,'acquisition_path')
    (OUT/'input_hashes.json').write_text(json.dumps(SOURCES,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2))
    print(timing_summary.to_string(index=False))


if __name__=='__main__':
    main()
