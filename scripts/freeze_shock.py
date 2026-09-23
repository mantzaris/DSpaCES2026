"""Freeze the paired matrix after calibration/smoke, without reading outcomes."""
import datetime as dt
import json
from pathlib import Path
import time
from evidence_fusion.refinement_access import immutable_digest


def main():
    out=Path('results/shock')
    if (out/'frozen_manifest.json').exists():raise RuntimeError('Already frozen')
    cfg=json.loads(Path('configs/regional_shock.json').read_text())
    smoke=json.loads((out/'smoke/summary.json').read_text())
    cal=json.loads((out/'calibration.json').read_text())
    ledger=json.loads((out/'resource_ledger.json').read_text())
    episodes=len(cfg['background_origin_indices'])*(len(cfg['families'])*len(cfg['magnitudes'])+2)
    projected=smoke['seconds']/smoke['episode_updates']*cfg['steps']*episodes
    remaining=ledger['cap_seconds']-(time.time()-ledger['start_epoch'])
    if projected+cfg['handoff_reserve_seconds']>remaining:
        raise RuntimeError('Measured projection cannot fit with handoff reserve; reduce paired backgrounds before freezing')
    assert cal['config_sha256']==immutable_digest('configs/regional_shock.json')
    snapshot=dict(config=cfg,config_sha256=immutable_digest('configs/regional_shock.json'),
        protocol_sha256=immutable_digest('docs/REGIONAL_SHOCK_STUDY_PROTOCOL.md'),
        calibration_sha256=immutable_digest(out/'calibration.json'),
        model_sha256=immutable_digest('data/regional/refinement/model.npz'),
        source=json.loads((out/'source.json').read_text()),
        frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(),episodes=episodes,
        physical_demand_episodes=episodes-len(cfg['background_origin_indices']),
        independent_backgrounds=len(cfg['background_origin_indices']),development_weeks=4,
        projected_replay_seconds=projected,remaining_allocation_at_freeze_seconds=remaining,
        no_comparative_outcomes_opened=True,smoke_before_shock_onset=True)
    (out/'frozen_manifest.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    print(json.dumps(snapshot,indent=2),flush=True)


if __name__=='__main__':main()
