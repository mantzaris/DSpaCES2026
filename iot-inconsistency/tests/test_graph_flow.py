"""Independent checks for the new flow, normalized fault densities and repairs."""
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.stats import multivariate_normal
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference'))
from reference_graph_flow import run_checks
from iot_repair.graph_flow_model import GraphFlow, build_context
from iot_repair.flow_math import (GaussianCorruption, gaussian_fault_posterior, gaussian_log_prob,
                                 score_candidates, summarize_repairs, weighted_crps, repair_outcome)


def example_graph():
    return dict(groups=['source_a', 'source_a', 'source_b', 'source_c'], edges=[
        dict(source=source, target=target, lag=1, sign=1, training_abs_correlation=.7, validation_gain=.5)
        for target in range(4) for source in range(4) if source != target])


def test_user_reference():
    assert run_checks()['passed_check_groups'] == 8


def test_flow_inverse_and_independent_autograd_jacobian():
    torch.manual_seed(21)
    model = GraphFlow(4, dimension=4, width=8, layers=4).double()
    for layer in model.couplings:
        torch.nn.init.normal_(layer.network[-1].weight, std=.05)
    context = torch.randn(1, 8, dtype=torch.float64)
    value = torch.randn(1, 4, dtype=torch.float64)
    latent, determinant = model.transform(value, context)
    restored, inverse_determinant = model.transform(latent, context, inverse=True)
    torch.testing.assert_close(restored, value, atol=1e-10, rtol=1e-10)
    torch.testing.assert_close(determinant, -inverse_determinant, atol=1e-10, rtol=1e-10)
    jacobian = torch.autograd.functional.jacobian(lambda y: model.transform(y[None], context)[0][0], value[0])
    torch.testing.assert_close(torch.linalg.slogdet(jacobian)[1], determinant[0], atol=1e-10, rtol=1e-10)


def test_target_and_same_source_masking_and_known_copy_invariance():
    torch.manual_seed(32)
    graph = example_graph(); values = torch.randn(2, 4, 64)
    query = torch.tensor([0, 0]); changed = values.clone(); changed[:, :2, -8:] += 1000
    model = GraphFlow(4, width=8, layers=2).eval()
    a, b = build_context(values, query, graph), build_context(changed, query, graph)
    torch.testing.assert_close(a.sequence, b.sequence, atol=0, rtol=0)
    ca, cb = model.encode(a), model.encode(b)
    torch.testing.assert_close(ca, cb, atol=0, rtol=0)
    latent = torch.randn(2, 16, 8)
    torch.testing.assert_close(model.sample(ca, sample_count=16, latent=latent),
                               model.sample(cb, sample_count=16, latent=latent), atol=0, rtol=0)
    assert not torch.allclose(model.log_prob(values[:, 0, -8:], ca), model.log_prob(changed[:, 0, -8:], cb))
    copied = torch.cat([values, values[:, 2:3]], dim=1)
    cc = build_context(copied, query, graph, observation_ids=['a0','a1','b','c','b'])
    torch.testing.assert_close(a.sequence, cc.sequence, atol=0, rtol=0)
    copied[:, 4, 0] += 1
    with pytest.raises(ValueError, match='Conflicting'):
        build_context(copied, query, graph, observation_ids=['a0','a1','b','c','b'])


def test_missing_targets_rejected_but_context_masks_supported():
    values = torch.randn(1, 4, 64); values[:, 2] = float('nan')
    model = GraphFlow(4, width=8, layers=2)
    context = build_context(values, torch.tensor([0]), example_graph())
    assert torch.isfinite(context.sequence).all()
    assert torch.isfinite(model.log_prob(values[:, 0, -8:], context)).all()
    target = values[:, 0, -8:].clone(); target[0, 0] = float('nan')
    with pytest.raises(ValueError, match='complete'):
        model.log_prob(target, context)


def test_draw_chunking_and_gaussian_reduction():
    torch.manual_seed(90)
    model = GraphFlow(4, dimension=4, width=8, layers=2).double()
    mean = np.array([.2, -.4, .5, .1]); std = np.array([.8, 1.2, .4, 1.5])
    with torch.no_grad():
        model.location_scale.bias[:4] = torch.tensor(mean)
        model.location_scale.bias[4:] = torch.tensor(4*np.arctanh(np.log(std)/4))
    context = torch.zeros(3, 8, dtype=torch.float64); y = torch.randn(3, 4, dtype=torch.float64)
    expected = multivariate_normal.logpdf(y.numpy(), mean, np.diag(std**2))
    np.testing.assert_allclose(model.log_prob(y, context).detach().numpy(), expected, atol=1e-10)
    epsilon = torch.randn(3, 64, 4, dtype=torch.float64)
    first = model.sample(context, sample_count=64, latent=epsilon, chunk=7)
    second = model.sample(context, sample_count=64, latent=epsilon, chunk=64)
    torch.testing.assert_close(first, second, atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(first.detach().numpy(), epsilon.numpy()*std+mean, atol=1e-12)


def test_component_densities_covariance_and_normalization():
    rng = np.random.default_rng(15); channel = GaussianCorruption(4, scale=1.3)
    generated = rng.normal(size=(2, 6, 4)); observed = rng.normal(size=(2, 4))
    actual = channel.component_log_prob(torch.tensor(observed), torch.tensor(generated)).numpy()
    for batch in range(2):
        for draw in range(6):
            for component in range(4):
                mean = channel.maps[component] @ generated[batch, draw]
                expected = multivariate_normal.logpdf(observed[batch], mean, channel.covariance[component].numpy())
                assert abs(actual[batch, draw, component]-expected) < 1e-10
    covariance = channel.covariance.numpy()
    assert covariance[0, 0, 1] > 0 and covariance[1, 0, -1] < 0
    scalar = GaussianCorruption(1); grid = np.linspace(-20,20,20001)
    values = scalar.component_log_prob(torch.tensor(grid[:,None]), torch.full((len(grid),1,1),.3)).numpy()[:,0]
    integrate = np.trapezoid if hasattr(np,'trapezoid') else np.trapz
    np.testing.assert_allclose(integrate(np.exp(values),grid,axis=0),np.ones(4),atol=1e-8)


def test_mixture_log_mean_and_extreme_log_stability():
    evidence = score_candidates(torch.log(torch.tensor([[.1,.4]])),torch.log(torch.tensor([[[.2,.6],[.8,.4]]])))
    assert abs(float(evidence.ratio)-np.log(2)) < 1e-6
    assert not np.isclose(float(evidence.log_fault),float(torch.log(torch.tensor([.2,.6,.8,.4])).mean()))
    a = score_candidates(torch.tensor([[-10002.]]),torch.tensor([[[-10000.,-10001.]]]))
    b = score_candidates(torch.tensor([[-2.]]),torch.tensor([[[0.,-1.]]]))
    assert abs(float(a.ratio-b.ratio)) < 1e-11
    for values in [torch.empty(1,1,0),torch.tensor([[[float('nan')]]])]:
        with pytest.raises(ValueError):score_candidates(torch.zeros(1,1),values)


def test_multivariate_gaussian_integral_and_posterior_monte_carlo():
    torch.manual_seed(53)
    channel = GaussianCorruption(2,scale=2.,weights=[0,0,1,0])
    mean = np.array([.2,-.1]); covariance = np.array([[1.,.3],[.3,.8]]); y=np.array([1.5,-.8])
    exact=gaussian_fault_posterior(y,mean,covariance,channel)
    total=covariance+4*np.eye(2)
    assert abs(exact['log_fault']-multivariate_normal.logpdf(y,mean,total))<1e-10
    proposal=torch.randn(1,131072,2,dtype=torch.float64)@torch.tensor(np.linalg.cholesky(covariance).T)+torch.tensor(mean)
    log_q=channel.log_prob(torch.tensor(y[None]),proposal)
    evidence=score_candidates(torch.tensor([[exact['log_normal']]]),log_q[:,None])
    assert abs(float(evidence.ratio)-exact['ratio'])<.02
    posterior=summarize_repairs(proposal,evidence.weights)
    np.testing.assert_allclose(posterior['mean'].numpy()[0],exact['mean'],atol=.025)
    np.testing.assert_allclose(posterior['variance'].numpy()[0],np.diag(exact['covariance']),atol=.025)


def test_general_unit_jacobians_cancel():
    y=np.array([2.,-.3]);mean=np.array([.5,.2]);cov=np.array([[1.,.2],[.2,.5]])
    noise=np.array([[2.,.4],[.4,1.]])
    change=np.array([[2.,1.],[.2,3.]]);offset=np.array([10.,-4.])
    score=gaussian_log_prob(y,mean,cov+noise)-gaussian_log_prob(y,mean,cov)
    transformed=gaussian_log_prob(change@y+offset,change@mean+offset,change@(cov+noise)@change.T)-gaussian_log_prob(change@y+offset,change@mean+offset,change@cov@change.T)
    assert abs(score-transformed)<1e-10


def test_weighted_crps_and_wrong_target_repair_damage():
    values=torch.tensor([[[0.,1.],[2.,3.],[4.,-1.]]],dtype=torch.float64)
    weights=torch.tensor([[.1,.2,.7]],dtype=torch.float64);truth=torch.tensor([[1.,1.]])
    expected=(weights[...,None]*(values-truth[:,None]).abs()).sum(1)-.5*(weights[:,:,None,None]*weights[:,None,:,None]*(values[:,:,None]-values[:,None,:]).abs()).sum((1,2))
    torch.testing.assert_close(weighted_crps(values,weights,truth),expected)
    reference=np.zeros((2,8));observed=reference.copy();observed[0]=2
    outcome=repair_outcome(observed,reference,np.ones(8),1,[True,False])
    assert outcome['failed'] and outcome['harmful'] and outcome['improvement']==-1
