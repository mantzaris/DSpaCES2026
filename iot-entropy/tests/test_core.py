import math

import numpy as np
import pytest
import torch

from iot_entropy.calibration import rank_pvalues
from iot_entropy.entropy import (entropy_from_correlation, equicorrelation_derivative,
                                 equicorrelation_entropy, trajectory_features, window_features)
from iot_entropy.evaluation import alert_intervals, match_events
from iot_entropy.localization import set_metrics
from iot_entropy.models import GraphDiffusion, cosine_schedule
from iot_entropy.synthetic import system


def test_limits_shrinkage_and_counterexample():
    identity=torch.eye(4,dtype=torch.float64)
    assert entropy_from_correlation(identity,0).item()==pytest.approx(1)
    assert entropy_from_correlation(torch.ones_like(identity),0).item()==pytest.approx(0,abs=1e-14)
    assert entropy_from_correlation(torch.ones_like(identity),.1).item()==pytest.approx(equicorrelation_entropy(4,torch.tensor(1.,dtype=torch.float64),.1).item())
    one=.8*identity+.2*torch.ones_like(identity)
    two=identity.clone();two[0,1]=two[1,0]=two[2,3]=two[3,2]=.6
    assert entropy_from_correlation(one,0).item()==pytest.approx(.96096404744)
    assert entropy_from_correlation(two,0).item()==pytest.approx(.86096404744)
    for r in [one,two]:
        assert (r.sum()-4).item()/12==pytest.approx(.2)
        assert torch.linalg.eigvalsh(r)[-1].item()/4==pytest.approx(.4)


def test_derivative_invariances_and_psd():
    rho=torch.linspace(.01,.95,30,dtype=torch.float64)
    for m in [4,6,24]:
        for shrinkage in [0,.05]:
            numeric=(equicorrelation_entropy(m,rho+1e-6,shrinkage)-equicorrelation_entropy(m,rho-1e-6,shrinkage))/2e-6
            torch.testing.assert_close(numeric,equicorrelation_derivative(m,rho,shrinkage),rtol=1e-7,atol=1e-9)
    torch.manual_seed(1);x=torch.randn(100,6,dtype=torch.float64)
    a=window_features(x).values[0]
    b=window_features((x*torch.tensor([1,-1,1,-1,1,-1]))[:,[3,0,5,1,4,2]]).values[0]
    torch.testing.assert_close(a,b)
    torch.testing.assert_close(a,window_features(x*3+4).values[0])
    bad=torch.tensor([[1.,2.],[2.,1.]],dtype=torch.float64)
    with pytest.raises(ValueError,match='non-PSD'):entropy_from_correlation(bad,.9)


def test_missing_constant_and_disagreement():
    torch.manual_seed(3);x=torch.randn(48,6,dtype=torch.float64)
    good=window_features(x)
    z=(x-x.mean(0))/x.std(0)
    explicit=torch.stack([(z[:,i]-z[:,j]).square().mean() for i in range(6) for j in range(i+1,6)]).mean()
    torch.testing.assert_close(good.values[3],explicit)
    x[:5,0]=float('nan');assert window_features(x).valid
    x[:20,1]=float('nan');assert not window_features(x).valid
    x=torch.randn(48,6,dtype=torch.float64);x[:,2]=1
    output=window_features(x);assert output.flatline and torch.isnan(output.values).all()
    assert not window_features(torch.randn(24,24)).valid


def test_exchangeable_rank_and_ties():
    rng=np.random.default_rng(12)
    exceedances=[]
    for _ in range(4000):
        null=rng.normal(size=100)
        exceedances.append(rank_pvalues(null[:99],null[99])<=.05)
    assert .035<np.mean(exceedances)<.065
    assert np.all(rank_pvalues(np.ones(20),np.ones(3))==1)
    assert rank_pvalues(np.arange(9),100)==.1


def test_event_matching_and_localization():
    times=np.arange(0,10)
    alerts=alert_intervals(times,np.array([1,1,0,1,0,0,1,1,0,0],bool),1)
    assert alerts==[(0,1),(3,3),(6,7)]
    outcome=match_events(alerts,[(2,4),(6,8)])
    assert (outcome['tp'],outcome['fp'],outcome['fn'])==(2,1,0)
    assert match_events([(0,8)],[(3,4)])['tp']==0
    assert set_metrics([1,2],[2,3])['iou']==pytest.approx(1/3)


def test_joint_model_no_target_conditioning_and_stability():
    for n in [64,128,256]: assert system(n)[3]['spectral_radius']<1
    beta=cosine_schedule(100)
    assert (beta>0).all() and (beta<1).all()
    torch.manual_seed(3)
    model=GraphDiffusion(6,1,8,8,2,100,torch.ones(6,6)/6,torch.randn(6,2))
    context=torch.randn(1,8,6,1);target_calendar=torch.zeros(1,12,4)
    model.eval();condition=model.conditioning(context,target_calendar)
    assert condition.shape==(1,8,6,12)
    samples=model.sample(context,target_calendar,4,5,2)
    assert samples.shape==(4,12,6,1) and torch.isfinite(samples).all()
    assert not torch.equal(samples[0],samples[1])


@pytest.mark.skipif(not torch.cuda.is_available(),reason='CUDA absent locally')
def test_gpu_cpu_agreement():
    torch.manual_seed(77);x=torch.randn(9,96,24,dtype=torch.float64)
    cpu=window_features(x)
    gpu=window_features(x.cuda().float())
    torch.testing.assert_close(cpu.values.float(),gpu.values.cpu(),rtol=2e-5,atol=2e-6)
    for noise in [.1,.001]:
        shared=torch.randn(9,96,1,dtype=torch.float64)
        x=shared*torch.where(torch.arange(24)%2==0,1.,-1.)+noise*x
        x[:,0,0]=float('nan')
        torch.backends.cuda.matmul.allow_tf32=True
        cpu=window_features(x);gpu=window_features(x.cuda().float())
        torch.testing.assert_close(cpu.values.float(),gpu.values.cpu(),rtol=2e-5,atol=2e-6)
