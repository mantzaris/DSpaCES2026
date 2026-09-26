import json
from pathlib import Path
import numpy as np
import pytest
torch=pytest.importorskip('torch')
from evidence_fusion.shock_gaussian import ShockGaussian
from evidence_fusion.shock_access import ObservationChannel,EvidenceWindow,ProbePolicy
from evidence_fusion.shock_overlays import overlay

ERRORS=[]


@pytest.fixture(scope='session',autouse=True)
def save_errors():
    yield
    if ERRORS:
        path=Path('results/shock');path.mkdir(exist_ok=True)
        (path/'correctness.json').write_text(json.dumps(ERRORS,indent=2)+'\n')


@pytest.fixture
def model():
    if not torch.cuda.is_available():pytest.skip('Authorized GPU required')
    return dict(loadings=np.array([[1.,.3],[.4,-.6],[.8,.2],[-.2,.7]]),
        scale=np.array([1.,2.,.7,1.3]),detail_var=np.array([.7,1.1,.4,2.]),
        measurement_var=np.array([.1,.2,.1,.3]),detail_ar=np.array([.8,-.3,.6,.2]),
        transition=np.array([[.8,.1],[0.,.6]]),process_var=np.array([.2,.1]),
        prior_var=np.array([1.,2.]),groups=np.array([0,0,1,1]))


@pytest.mark.parametrize('selection',['none','partial','all'])
def test_partial_evidence_matches_independent_joint(model,selection):
    engine=ShockGaussian(model,3)
    y=np.array([[1.,np.nan,2.],[.5,-.3,1.],[2.,1.,-.1],[-1.,.2,.8]])
    native=np.isfinite(y)
    acquired=np.zeros_like(native)
    if selection=='all':acquired=native.copy()
    if selection=='partial':acquired[[0,1,2,3],[2,0,1,0]]=True
    fine=np.where(acquired,y,np.nan)
    aggregate=np.stack([np.nansum(y[g*2:g*2+2],0) for g in range(2)])
    outputs,state=engine.infer(native,fine,aggregate,np.ones((3,4),bool),np.zeros((3,4)),[0])
    r=engine.dimension;size=r+12
    j=torch.zeros((size,size),device='cuda',dtype=torch.float64);j[:r,:r]=engine.prior
    b=torch.zeros(size,device='cuda',dtype=torch.float64)
    eye=torch.eye(3,device='cuda',dtype=torch.float64)
    for i in range(4):j[r+3*i:r+3*i+3,r+3*i:r+3*i+3]=torch.linalg.solve(engine.house_cov[i],eye)
    for g in range(2):
        for t in range(3):
            available=[i for i in [2*g,2*g+1] if native[i,t]]
            sets=[[i] for i in available if acquired[i,t]]+[[i for i in available if not acquired[i,t]]]
            for ids in sets:
                if not ids:continue
                row=torch.zeros(size,device='cuda',dtype=torch.float64)
                for i in ids:
                    row[t*2:t*2+2]+=engine.loading[i]
                    row[r+i*3+t]=1.
                variance=engine.nugget[ids].sum();value=sum(y[i,t] for i in ids)
                j+=torch.outer(row,row)/variance;b+=row*value/variance
    factor=torch.linalg.cholesky(j)
    expected=torch.cholesky_solve(b[:,None],factor).squeeze(1)
    cov=torch.cholesky_solve(torch.eye(size,device='cuda',dtype=torch.float64),factor)
    actualcov=torch.cholesky_solve(torch.eye(r,device='cuda',dtype=torch.float64),state['chol'])
    meanerr=float(abs(state['mean']-expected[:r]).max());coverr=float(abs(actualcov-cov[:r,:r]).max())
    assert meanerr<1e-10 and coverr<1e-10
    for hi,horizon in enumerate(engine.horizons):
        rows=torch.zeros((4,size),device='cuda',dtype=torch.float64)
        rows[:,r-2:r]=engine.loading@engine.future_transition[horizon]
        for i in range(4):rows[i,r+i*3+2]=engine.rho[i]**horizon
        noise=torch.diag(engine.variance*(1-engine.rho**(2*horizon))+engine.nugget)
        noise+=engine.loading@engine.future_noise[horizon]@engine.loading.T
        targetcov=rows@cov@rows.T+noise
        err=float(abs(outputs[hi]['mean']-rows@expected).max())
        varerr=float(abs(outputs[hi]['variance']-targetcov.diag()).max())
        regionalerr=float(abs(outputs[hi]['region_variance']-targetcov.sum()))
        assert max(err,varerr,regionalerr)<1e-10
        ERRORS.append(dict(selection=selection,horizon=horizon,mean_error=meanerr,covariance_error=coverr,
                           forecast_mean_error=err,forecast_variance_error=varerr,regional_variance_error=regionalerr))
    # Eviction changes stored detail, not posterior sufficient quantities.
    before=state['mean'].clone();state['leaves']=[]
    assert torch.equal(before,state['mean'])


def test_observability_and_probe_failure_gpu(model):
    f=torch.diag(torch.tensor([.9,.9,.7],device='cuda',dtype=torch.float64))
    c=torch.ones((1,3),device='cuda',dtype=torch.float64)
    delta=torch.tensor([1.,-1.,0.],device='cuda',dtype=torch.float64)
    o=torch.cat([c@torch.linalg.matrix_power(f,k) for k in range(7)])
    assert float(abs(o@delta).max())==0.
    miss=torch.tensor([[0.,0.,1.]],device='cuda',dtype=torch.float64)
    hit=torch.tensor([[1.,0.,0.]],device='cuda',dtype=torch.float64)
    assert float(miss@delta)==0. and float(hit@delta)==1.
    f[1,1]=.7
    signatures=torch.stack([(c@torch.linalg.matrix_power(f,k)@delta).squeeze() for k in range(4)])
    assert torch.allclose(signatures,torch.tensor([0.,.2,.32,.386],device='cuda',dtype=torch.float64),atol=1e-12)
    ERRORS.append(dict(theory_delayed_signatures=signatures.cpu().tolist()))


def test_channel_budget_missing_future_and_duplicates():
    data=np.ones((3,16));data[0,0]=np.nan
    channel=ObservationChannel(data,np.arange(16),2,[]);channel.advance(0)
    assert np.isnan(channel.read([0])[0])
    with pytest.raises(ValueError):channel.read([1,2])
    with pytest.raises(ValueError):channel.read([0])
    with pytest.raises(ValueError):channel.read([1],at=1)
    with pytest.raises(ValueError):channel.read([1],at=-1)
    channel.read([1]);channel.advance(1)
    assert channel.read([0])[0]==1.


def test_moving_window_discards_old_evidence_and_rejects_stale():
    cache=EvidenceWindow(2,3)
    for t in range(3):cache.advance(t);cache.add([0],[10+t],t)
    assert cache.advance(3)==1
    assert np.allclose(cache.values[0,:2],[11,12])
    with pytest.raises(ValueError):cache.add([1],[7],2)
    with pytest.raises(ValueError):cache.advance(5)


@pytest.mark.parametrize('family',['regional','localized','cancel_exact','cancel_approx','delayed','ramp','none','sensor_fault'])
def test_overlays_are_feasible_and_target_semantics(family):
    n=1024;data=np.full((84,n),.8);data[35,17]=np.nan
    model=dict(groups=np.arange(n)%16,profile=np.ones((336,n)),
               detail_var=np.full(n,.64),measurement_var=np.full(n,.16))
    readings,target,d,signature,meta=overlay(data,model,family,3.,1293)
    assert np.nanmin(readings)>=0 and np.nanmin(target)>=0
    assert np.array_equal(np.isnan(data),np.isnan(target))
    if family=='sensor_fault':assert np.allclose(target,data,equal_nan=True) and np.nanmax(abs(readings-target))>0
    else:assert np.allclose(readings,target,equal_nan=True)
    if family=='cancel_exact':assert np.max(abs(signature))<1e-12 and np.max(abs(d))>0
    if family=='delayed':assert np.max(abs(signature[meta['onset_array']]))<1e-12 and np.max(abs(signature))>0
    if family=='none':assert np.max(abs(d))==0


def test_policy_does_not_receive_fine_residuals_or_labels():
    a=ProbePolicy(np.arange(1024)%16,probes=10,budget=51,trigger=1.)
    ids=a.probe_ids(0);a.update(ids,np.full(10,3.))
    selected=a.refinement_ids(0,ids)
    assert len(selected)==41 and len(set(selected)&set(ids))==0
    assert len(np.unique(a.groups[selected]))>1  # exploration survives a trigger


def test_current_record_query_has_shared_not_future_measurement_noise(model):
    class Current(ShockGaussian):horizons=(0,)
    engine=Current(model,3)
    y=np.arange(12,dtype=float).reshape(4,3)/10
    aggregate=np.stack([y[:2].sum(0),y[2:].sum(0)])
    output,_=engine.infer(np.ones_like(y,bool),y,aggregate,np.ones((1,4),bool),np.zeros((1,4)))
    error=float(abs(output[0]['mean']-torch.as_tensor(y[:,-1],device='cuda')).max())
    variance=float(abs(output[0]['variance']).max())
    assert max(error,variance)<1e-10
    ERRORS.append(dict(current_record_mean_error=error,current_record_variance_error=variance))
