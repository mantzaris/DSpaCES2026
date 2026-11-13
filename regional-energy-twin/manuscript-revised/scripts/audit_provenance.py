"""Reproduce calibration provenance, accounting and reviewed headline checks.

Reads saved artifacts only. All outputs are explicit and confined to this revision.
No raw meter archive, model fitting, replay or GPU is used.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import pandas as pd


def main():
    started = time.perf_counter()
    revision = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, default=revision.parent)
    parser.add_argument('--output', type=Path, default=revision/'analysis'/'provenance_checks.json')
    args = parser.parse_args()
    project = args.project.resolve(); output = args.output.resolve()
    if revision not in output.parents:
        raise SystemExit('Output must stay inside manuscript-revised')
    inputs = {}
    def read(name):
        path = project/name
        inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path
    cfg=json.loads(read('configs/regional_shock.json').read_text())
    cal=json.loads(read('results/shock/calibration.json').read_text())
    prep=json.loads(read('results/shock/preparation.json').read_text())
    scores=pd.read_csv(read('results/shock/calibrate/scores.csv'))
    q=scores[(scores.method=='M1') & (scores.step>=8)].sort_values('step')
    assert q.step.tolist()==list(range(8,96))
    trigger=float(np.quantile(q.trigger,.98))
    assert trigger==cal['trigger']
    assert cfg['group_score_decay']==.8 and cfg['group_score_drift']==2.
    access_code=read('src/evidence_fusion/shock_access.py').read_text()
    assert 'self.score*=.8' in access_code and 'float(z.max())-2.' in access_code
    replay_code=read('scripts/replay_shock.py').read_text()
    read('scripts/prepare_shock.py')
    analysis_code=read('scripts/analyze_shock.py').read_text()
    assert "a.step<ep.onset+cfg['detection_limit_steps']" in analysis_code
    assert cfg['detection_limit_steps']==6
    assert "r['step']>=8],.98)" in replay_code
    assert "for key,values in result['quantile_cal']" in replay_code
    costs=pd.read_csv(read('results/shock/analysis/cost_summary.csv')).set_index('method')
    access=pd.read_csv(read('results/shock/run/access.csv.gz'),keep_default_na=False)
    payload={}
    for method,attempts,calls in [('M3',209,2),('M4',4194,1)]:
        r=costs.loc[method]
        assert int(r.updates)==112*48==5376
        update_fine=16*attempts+64*calls
        update_summary=16*8+(4194+7)//8+64
        assert update_summary==717
        expected_attempts=5376*attempts
        expected_fine=5376*update_fine
        expected_summary=5376*update_summary
        rows=access[(access.method==method)&(access.kind!='summary')]
        assert len(rows)==5376*calls
        assert int(rows.attempted.sum())==expected_attempts==int(r.fine_attempts)
        assert int(rows.payload_bytes.sum())==expected_fine==int(r.fine_bytes)
        assert expected_summary==int(r.summary_bytes)
        assert int(rows.returned.sum())==int(r.fine_valid)
        payload[method]={'updates':5376,'attempts_per_update':attempts,'read_calls_per_update':calls,
                         'fine_attempts':expected_attempts,'finite_returns':int(r.fine_valid),
                         'fine_bytes':expected_fine,'summary_bytes':expected_summary,
                         'total_bytes':expected_fine+expected_summary,
                         'total_decimal_MB':(expected_fine+expected_summary)/1e6}
    principal=pd.read_csv(read('results/synthesis/principal_results.csv'))
    observed={}
    expected={'M0':(37,20,36),'M1':(17,11,15),'M2':(33,14,25),'M3':(29,15,30),'M4':(42,15,41)}
    for method,(d,l,a) in expected.items():
        r=principal[(principal.cohort=='B')&(principal.method==method)].iloc[0]
        assert (int(r.detected),int(r.localized),int(r.negative_alarms))==(d,l,a)
        assert int(r.demand_episodes)==96 and int(r.negative_steps)==384
        observed[method]={'detected':d,'localized':l,'demand_episodes':96,'alarmed_control_updates':a,
                          'control_updates':384,'false_alarm_rate':a/384}
    forecasts=pd.read_csv(read('results/shock/analysis/episode_forecasts.csv'))
    r=forecasts[(forecasts.family=='none')&(forecasts.method=='M3')&(forecasts.horizon==2)&(forecasts.level=='regional')]
    assert len(r)==8 and set(r.phase)=={'background'}
    cover=r[['coverage','width','adjusted_coverage','adjusted_width']].mean().to_dict()
    assert abs(cover['coverage']-277/384)<1e-12
    assert abs(cover['adjusted_coverage']-323/384)<1e-12
    ref=pd.read_csv(read('results/refinement/replay/outcome_summary.csv'))
    a=ref[(ref.population==4194)&(ref.policy=='uncertainty')&(ref.active_groups==8)&(ref.horizon_steps==2)&(ref.level=='regional')].iloc[0]
    assert a.coverage90==19/32
    original_tex=read('manuscript/regional_twin_study.tex').read_text()
    pdf=read('manuscript/regional_twin_study.pdf')
    pdftext=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True)
    assert 'Alexander V. Mantzaris' in original_tex and 'Alexander V. Mantzaris' in pdftext
    assert '22.52' in original_tex and '364.95' in original_tex
    start=pd.Timestamp(cfg['calibration_start'])
    result={'timestamp_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'calibration':{'update_origins_start':str(start),'update_origins_end':str(start+pd.Timedelta(minutes=30*95)),
                'calibration_updates':96,'excluded_alarm_startup_updates':8,'post_startup_alarm_updates':88,
                'retained_alarm_origins_start':str(start+pd.Timedelta(hours=4)),
                'warmup_start':str(start-pd.Timedelta(minutes=30*23)),
                'last_six_hour_target':str(start+pd.Timedelta(minutes=30*(95+12))),
                'quantile':.98,'quantile_interpolation':'NumPy default linear',
                'trigger_from_saved_M1_scores':trigger,'saved_trigger':cal['trigger'],
                'saved_scores_are':'Second calibration pass. Same probe/reference path reproduces first-pass trigger quantile.',
                'decay':.8,'offset':2.,'parameter_status':'Fixed heuristics in config and hard-coded executable behavior; no tuning study found.',
                'interval_calibration':'90th percentile of absolute standardized forecast errors, separately by method/lead/query level, from all96 origins; household every16th finite entry. No eight-update interval exclusion.'},
            'payload':payload,'fine_attempt_ratio_M4_over_M3':payload['M4']['fine_attempts']/payload['M3']['fine_attempts'],
            'fine_payload_ratio_M4_over_M3':payload['M4']['fine_bytes']/payload['M3']['fine_bytes'],
            'total_payload_ratio_M4_over_M3':payload['M4']['total_bytes']/payload['M3']['total_bytes'],
            'original_B_detection_window':{'inclusive_lags':[0,1,2,3,4,5], 'code':'scripts/analyze_shock.py:71 uses step < onset + 6', 'manuscript_mismatch':'Original prose says lags0..6 inclusive. Preserve original count table with corrected scope and keep the requested seven-instant sweep distinct.'},
            'frozen_B':observed,'coverage_A':{'covered':19,'origins':32,'coverage':float(a.coverage90)},
            'coverage_B_M3':cover,
            'author_record':{'documented':'Alexander V. Mantzaris; School of Data, Mathematical and Statistical Sciences; University of Central Florida; alexander.mantzaris@ucf.edu',
                             'second_author_documented':False,'submission_receipt_found':False},
            'baseline_assessment':'Current source/PDF title, reported data scale, numeric findings and ambiguous payload sentence match the reviewer-described paper. Reviewer counts37/29/42 match original B analysis lags0..5, not source-prose lags0..6. No separate submitted regional PDF/receipt is available to certify upload identity.',
            'inputs_sha256':inputs,'seconds':time.perf_counter()-started,'gpu_used':False,'raw_meter_values_read':False}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['inputs_sha256']},indent=2))


if __name__=='__main__':main()
