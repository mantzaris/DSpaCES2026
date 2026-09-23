import datetime,json,time
from pathlib import Path
from evidence_fusion.refinement_access import immutable_digest
root=Path('results/acquisition')
if (root/'frozen.json').exists():raise RuntimeError('Already frozen')
smoke=json.loads((root/'smoke/summary.json').read_text());ledger=json.loads((root/'resource_ledger.json').read_text())
remaining=ledger['cap_seconds']-(time.time()-ledger['start_epoch'])
projected=smoke['seconds']/8/3*(16*48*6+4*48*3)
# Smoke includes interpreter-independent setup; this is a conservative extrapolation.
if projected+300>remaining:raise RuntimeError('Frozen workload cannot fit measured cap with five-minute reserve')
files=['configs/regional_acquisition.json','configs/regional_shock.json','results/acquisition/calibration.json',
       'data/regional/refinement/model.npz','scripts/replay_shock.py','scripts/replay_acquisition.py',
       'src/evidence_fusion/acquisition_policy.py','src/evidence_fusion/shock_gaussian.py','src/evidence_fusion/shock_access.py',
       'src/evidence_fusion/shock_overlays.py','docs/REGIONAL_ACQUISITION_CORRECTION.md']
result=dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit='18fe4af',
    hashes={p:immutable_digest(p) for p in files},remaining_seconds=remaining,projected_replay_seconds=projected,
    fresh_episodes=16,original_diagnostic_episodes=4,backgrounds=4,no_new_comparative_outcomes_opened=True)
(root/'frozen.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
