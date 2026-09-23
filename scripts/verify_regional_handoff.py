"""Focused final correctness/provenance audit; only frozen development inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
from evidence_fusion.regional_data import load_panel,slots


def main():
    result={}
    source=json.loads(Path('results/regional/executed_source_hashes.json').read_text())
    for file,sha in source.items():
        assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==sha,file
    result['executed_source_hashes_verified']=len(source)
    old=subprocess.check_output(['git','show','09ae274:DSpaCES_2026_Research_Plan.md'])
    assert old==Path('DSpaCES_2026_Research_Plan.md').read_bytes()
    result['compatibility_candidate_unchanged']=True
    assert 'authorized: false' in Path('configs/main_study.yaml').read_text()
    result['original_main_disabled']=True
    current=pd.read_csv('results/regional/replay/forecasts.csv',float_precision='round_trip')
    initial=pd.read_csv('results/regional/replay_initial/forecasts.csv',float_precision='round_trip')
    assert current.shape==initial.shape
    numeric=current.select_dtypes(include=[np.number]).columns
    maxdiff=float(np.max(np.abs(current[numeric].values-initial[numeric].values)))
    assert maxdiff<1e-9
    result['timing_repeat_max_forecast_difference']=maxdiff
    c=pd.read_csv('results/regional/replay/certificates.csv')
    audited=c[c.spectral_delta_audit.notna()]
    assert np.all(audited.spectral_delta_audit<=audited.delta*(1+1e-9)+1e-12)
    finite=c[np.isfinite(c.output_bound_kwh)]
    assert np.all(finite.polynomial_output_error_kwh<=finite.output_bound_kwh+1e-10)
    result['real_spectral_bound_audits']=len(audited)
    result['finite_polynomial_bound_audits']=len(finite)
    config=json.loads(Path('configs/regional_pilot.json').read_text())
    model=np.load('data/regional/model/model.npz',allow_pickle=False)
    values,times,meters,_=load_panel('development',model['meters'])
    frozen=json.loads(Path('results/regional/replay/frozen_manifest.json').read_text())
    ranks=[]; blocks=0
    for origin in frozen['origins']:
        pos=times.get_loc(pd.Timestamp(origin)); mask=np.isfinite(values[pos-23:pos+1])
        for g in range(config['provider_groups']):
            ix=np.flatnonzero(model['groups']==g); h=model['loadings'][ix]
            provider_rank=0
            for row in mask[:,ix]:
                provider_rank+=int(np.linalg.matrix_rank(h[row])) if np.any(row) else 0
                blocks+=1
            ranks.append(provider_rank)
    result['native_measurement_blocks_rank_checked']=blocks
    result['provider_trajectory_rank_min']=min(ranks)
    result['provider_trajectory_rank_max']=max(ranks)
    result['trajectory_dimension']=config['latent_dimension']*config['window_steps']
    snapshots=json.loads(Path('results/regional/replay/snapshots.json').read_text())
    for row in snapshots:
        data=np.load('data/regional/snapshots/snapshot_%03d.npz'%row['origin'],allow_pickle=False)
        assert data['cutoff'].item()==row['cutoff']
        np.testing.assert_array_equal(data['meter_ids'],meters)
        np.testing.assert_allclose(data['household_predictions'].sum(2),data['regional_predictions'],atol=1e-10)
        np.testing.assert_allclose(data['group_predictions'].sum(2),data['regional_predictions'],atol=1e-9)
    result['persistent_snapshots_checked']=len(snapshots)
    result['heldout_policy']='No sealed demand values loaded; analysis accessor restricted to train/development'
    Path('results/regional/final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
