"""Small descriptive decision summaries; no new inference or outcome selection."""
import json
from pathlib import Path
import pandas as pd


def main():
    root=Path('results/shock');folder=root/'analysis'
    episodes=pd.DataFrame(json.loads((root/'run/episodes.json').read_text()))
    access=pd.read_csv(root/'run/access.csv.gz',keep_default_na=False)
    alarm=pd.read_csv(folder/'audited_alarms.csv.gz')
    forecasts=pd.read_csv(folder/'episode_forecasts.csv')
    events=pd.read_csv(folder/'episode_detection.csv')
    cfg=json.loads(Path('configs/regional_shock.json').read_text())
    trace=access[access.method=='M3']
    controls={b:list(trace[trace.episode=='b%02d_none_0.0'%b].sort_values(['step','kind']).households)
        for b in range(8)}
    rows=[]
    for e in episodes.itertuples():
        acquired=list(trace[trace.episode==e.episode].sort_values(['step','kind']).households)
        a=alarm[(alarm.method=='M3')&(alarm.episode==e.episode)]
        rows.append(dict(episode=e.episode,background=e.background,family=e.family,
            same_acquisition_ID_trace_as_unmodified=acquired==controls[e.background],
            active_steps=int((a.active_group>=0).sum()),
            affected_group_selected_during_local_event=int(((a.active_group==e.group)&a.in_event).sum())
                if e.family in ('localized','cancel_exact','cancel_approx','delayed','ramp') else None))
    policies=pd.DataFrame(rows);policies.to_csv(folder/'policy_response.csv',index=False)
    local=forecasts[(forecasts.family.isin(['localized','cancel_exact','cancel_approx','delayed','ramp']))
        &(forecasts.level=='affected')&(forecasts.phase=='during')]
    paired=local[local.horizon==2].pivot(index=['background','family','magnitude'],columns='method',values='mae')
    delta=(paired.M3-paired.M2).groupby(level=0).mean()
    delta.rename('M3_minus_M2_local_MAE').to_csv(folder/'paired_background_local_error.csv')
    none=alarm[alarm.episode.str.contains('_none_')]
    no_rates=none.groupby('method').alarm.mean().to_dict()
    ongoing_rates=none[none.step>0].groupby('method').alarm.mean().to_dict()
    local_means=local.groupby(['method','horizon']).mae.mean()
    cal=json.loads((root/'calibration.json').read_text())
    result=dict(
        demand_shock_episodes=int(episodes.family.isin(cfg['families']).sum()),
        demand_shock_episodes_with_changed_M3_acquisition_trace=int((~policies.same_acquisition_ID_trace_as_unmodified
            &policies.family.isin(cfg['families'])).sum()),
        measurement_fault_episodes_with_changed_M3_trace=int((~policies.same_acquisition_ID_trace_as_unmodified
            &(policies.family=='sensor_fault')).sum()),
        M3_active_step_fraction=float((alarm[alarm.method=='M3'].active_group>=0).mean()),
        local_event_affected_group_selected_steps=int(policies.affected_group_selected_during_local_event.sum()),
        negative_control_alarm_rates=no_rates,negative_control_alarm_rates_excluding_initial_step=ongoing_rates,
        local_MAE_one_hour={m:float(local_means[m,2]) for m in no_rates},
        local_MAE_six_hours={m:float(local_means[m,12]) for m in no_rates},
        M3_vs_M2_local_one_hour_percent=100*(float(local_means['M3',2]/local_means['M2',2])-1),
        M3_vs_M1_local_one_hour_percent=100*(float(local_means['M3',2]/local_means['M1',2])-1),
        M3_vs_M4_local_one_hour_percent=100*(float(local_means['M3',2]/local_means['M4',2])-1),
        paired_background_local_MAE_difference_min=float(delta.min()),
        paired_background_local_MAE_difference_max=float(delta.max()),
        effective_standardized_fine_alarm_threshold={m:cal['fine'][m]*cal['joint'][m] for m in no_rates if m!='M0'},
        no_new_outcomes_or_inference=True,independent_backgrounds=8,development_weeks=4,
        caveat='Descriptive paired development results. Same ID traces do not imply identical received values under a shock.')
    (folder/'decision_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
