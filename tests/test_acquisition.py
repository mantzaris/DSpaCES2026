"""Behaviour through the actual channel -> standardized innovations -> policy path."""
import json
from pathlib import Path
import numpy as np
import pytest
from evidence_fusion.shock_access import ProbePolicy,ObservationChannel,EvidenceWindow

TRIGGER=json.loads(Path('results/shock/calibration.json').read_text())['trigger']

def action(values,step=0,budget=51):
    policy=ProbePolicy(np.arange(1024)%16,probes=10,budget=budget,trigger=TRIGGER)
    ids=policy.probe_ids(step)
    channel=ObservationChannel(values[None],policy.groups,budget,[]);channel.advance(0)
    observed=channel.read(ids,'probe')
    policy.update(ids,abs(observed-1.))
    extra=policy.refinement_ids(step,ids)
    acquired=channel.read(extra,'refinement')
    return policy,ids,extra,acquired,channel

def test_accessible_innovation_changes_actual_available_action():
    background=np.ones(1024);a,ids,extra,_,_=action(background)
    changed=background.copy();changed[ids[0]]=TRIGGER+4.
    b,_,selected,_,channel=action(changed)
    assert b.score[b.groups[ids[0]]]>TRIGGER and b.active==b.groups[ids[0]]
    assert not np.array_equal(selected,extra)
    assert len(channel.used)==51 and len(set(selected)&set(ids))==0
    assert np.sum(b.groups[selected]==b.active)>np.sum(a.groups[extra]==b.active)

def test_no_change_and_below_drift_controls():
    p,ids,a,_,_=action(np.ones(1024))
    low=np.ones(1024);low[ids[0]]=2.5
    q,_,b,_,_=action(low)
    assert np.array_equal(a,b) and np.array_equal(p.score,q.score) and q.active==-1

def test_unread_cancelled_shock_cannot_reach_policy():
    y=np.ones(1024);p,ids,extra,_,_=action(y)
    hidden=np.setdiff1d(np.arange(1024),np.r_[ids,extra]);group=p.groups[hidden[0]]
    pair=hidden[p.groups[hidden]==group][:2];y[pair]+=[.5,-.5]
    q,_,selected,_,_=action(y)
    assert np.array_equal(p.score,q.score) and np.array_equal(extra,selected)
    assert y[pair].sum()==2.

def test_opposite_observed_changes_do_not_cancel():
    p=ProbePolicy(np.arange(1024)%16,probes=10,budget=51,trigger=TRIGGER)
    ids=np.array([0,16]); signed=np.array([TRIGGER+3.,-TRIGGER-3.])
    p.update(ids,abs(signed))
    assert p.active==0 and p.score[0]>TRIGGER

def test_budget_rejection_has_explicit_reason():
    p,ids,extra,_,channel=action(np.ones(1024))
    available=np.setdiff1d(np.arange(1024),np.r_[ids,extra])[0]
    with pytest.raises(ValueError,match='budget exceeded'):channel.read([available])
    fresh=ObservationChannel(np.ones((1,1024)),p.groups,52,[]);fresh.advance(0)
    fresh.read(np.r_[ids,extra]);assert fresh.read([available])[0]==1.

def test_current_probe_precedes_action_extra_has_no_feedback_in_original():
    p,ids,extra,values,_=action(np.ones(1024))
    initial=p.score.copy();values[0]=1e6
    assert np.array_equal(p.score,initial)  # No update call for acquired extras in M3.
    p.update(extra,abs(values-1.))
    assert p.active==p.groups[extra[0]]  # Would affect a subsequent selection if connected.

def test_restoration_window_and_stale_evidence():
    c=EvidenceWindow(3,3)
    for t in range(3):c.advance(t);c.add([0],[10+t],t)
    saved=c.values.copy();restored=EvidenceWindow(3,3);restored.values[:]=saved;restored.cutoff=2
    assert restored.advance(3)==c.advance(3)==1
    assert np.allclose(restored.values,c.values,equal_nan=True)
    with pytest.raises(ValueError,match='Stale'):restored.add([0],[90.],2)
    restored.add([1],[20.],3);assert np.isnan(restored.values[1,:-1]).all()

def test_gpu_same_evidence_restore_and_boundary_discrepancy(tmp_path):
    torch=pytest.importorskip('torch')
    if not torch.cuda.is_available():pytest.skip('GPU numerical check')
    from evidence_fusion.shock_gaussian import ShockGaussian
    model=dict(loadings=np.array([[1.,.3],[.4,-.6],[.8,.2],[-.2,.7]]),scale=np.ones(4),
        detail_var=np.array([.7,1.1,.4,2.]),measurement_var=np.full(4,.2),detail_ar=np.array([.8,-.3,.6,.2]),
        transition=np.array([[.8,.1],[0.,.6]]),process_var=np.array([.2,.1]),prior_var=np.array([1.,2.]),groups=np.array([0,0,1,1]))
    engine=ShockGaussian(model,3);y=np.arange(12,dtype=float).reshape(4,3)/10
    y[1,1]=np.nan;fine=np.full_like(y,np.nan);fine[0,2]=y[0,2]
    args=(np.isfinite(y),fine,np.stack([np.nansum(y[:2],0),np.nansum(y[2:],0)]),np.ones((3,4),bool),np.zeros((3,4)))
    a,state=engine.infer(*args,retain_groups=[0]);state['leaves']=[]
    b,_=engine.infer(*args,retain_groups=[0,1])
    discrepancy=max(float(abs(x[k]-z[k]).max()) for x,z in zip(a,b) for k in x)
    assert discrepancy<1e-10
    shifted=np.c_[fine[:,1:],np.full(4,np.nan)]
    newer,_=engine.infer(args[0],shifted,*args[2:])
    difference=max(float(abs(x['mean']-z['mean']).max()) for x,z in zip(a,newer))
    assert difference>1e-6
    out=Path('results/acquisition');out.mkdir(exist_ok=True)
    (out/'correctness.json').write_text(json.dumps(dict(same_evidence_max_abs=discrepancy,moved_evidence_forecast_change=difference),indent=2)+'\n')
