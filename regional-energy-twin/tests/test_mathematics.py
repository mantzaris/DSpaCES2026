import numpy as np
import pytest
from scipy.optimize import minimize
from evidence_fusion.conservative_fusion import solve_simplex, quadratic, fuse_arrays
from evidence_fusion.provenance_sketches import sufficient_epsilon, gaussian_columns
from evidence_fusion.provider_models import qr_operator


def test_plan_example():
    a = np.array([[np.sqrt(3),1,0,0],[np.sqrt(3),0,1,0],[0,0,0,2]])
    sol = solve_simplex(a @ a.T)
    np.testing.assert_allclose(sol.weights, [4/15,4/15,7/15], atol=1e-12)
    assert sol.weights @ [100,102,110] == pytest.approx(105.2)
    assert sol.value + 1 == pytest.approx(43/15)
    assert quadratic(a@a.T+1, np.ones(3)/3) == pytest.approx(3.)
    assert sol.gap < 1e-12


@pytest.mark.parametrize('kind', ['zero', 'duplicate', 'negative', 'unequal', 'singular', 'random'])
def test_solver_against_independent_scipy(kind):
    rng = np.random.default_rng(417)
    a = rng.normal(size=(4,12))
    if kind == 'zero': a[0] = 0
    if kind == 'duplicate': a[1] = a[0]
    if kind == 'negative': a[1] = -a[0]
    if kind == 'unequal': a *= np.array([1e-3,1,10,100])[:,None]
    if kind == 'singular': a[3] = a[0] + 1e-9*a[1]
    h = a@a.T
    sol = solve_simplex(h)
    scale = max(np.max(np.abs(h)),1.)
    ref = minimize(lambda w: float(w@h@w/scale), np.ones(4)/4,
        jac=lambda w: 2*h@w/scale, method='SLSQP', bounds=[(0,1)]*4,
        constraints=[{'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(4)}],
        options={'ftol':1e-13, 'maxiter':2000})
    assert ref.success
    assert sol.value <= ref.fun*scale + 1e-7*scale
    assert sol.gap <= 1e-8*scale
    assert sol.weights.min() >= 0 and abs(sol.weights.sum()-1) < 1e-12


def test_uniform_risk_sandwich_and_optimization():
    rng = np.random.default_rng(53)
    a = rng.normal(size=(4,30)); a[0] = 0
    s = np.linalg.norm(a,axis=1); r=np.array([.2,.4,.3,.6]); v=2.
    eps = sufficient_epsilon(512, 10, 4, .01)
    z = a @ (rng.normal(size=(30,512))/np.sqrt(512))
    k = a@a.T; kh=z@z.T
    assert np.all(np.abs(kh-k) <= eps*np.outer(s,s)+1e-12)
    h=k+np.outer(r,r); hh=kh+eps*np.outer(s,s)+np.outer(r,r)
    w=rng.dirichlet(np.ones(4),size=100)
    rv=quadratic(h,w)+v; qv=quadratic(hh,w)+v
    assert np.all(rv <= qv+1e-10)
    assert np.all(qv <= rv+2*eps*(w@s)**2+1e-10)
    exact=solve_simplex(h); sketch=solve_simplex(hh)
    assert quadratic(h,sketch.weights) <= exact.value+2*eps*(s@exact.weights)**2+sketch.gap+1e-10


def test_future_noise_floor_and_fallback():
    for p in (2,4,8):
        z=np.eye(p); s=np.ones(p); r=np.zeros(p)
        out=fuse_arrays(np.ones(p),z,s,r,9.,.2)
        assert out['variance'] >= 9.
        assert out['variance'] <= 10.
    out=fuse_arrays([1,2],np.zeros((2,2)),[0,0],[1,2],3.,.2)
    assert out['variance'] == pytest.approx(4.)


def test_compatible_independent_projection_columns():
    whole=gaussian_columns(['a','b','c'],512,93)
    part=gaussian_columns(['c','a'],512,93)
    np.testing.assert_array_equal(part,whole[[2,0]])
    assert not np.array_equal(whole[0],whole[1])


def test_projection_bound_rejects_unavailable_epsilon():
    with pytest.raises(ValueError): sufficient_epsilon(5,10000,4,.01)
    eps=sufficient_epsilon(2048,2000000,4,.01)
    assert eps == pytest.approx(.2326,abs=1e-4)


def test_qr_influence_matches_refit_perturbation():
    rng=np.random.default_rng(6)
    x=rng.normal(size=(60,7)); y=rng.normal(size=60); phi=rng.normal(size=7)
    operator,_=qr_operator(x)
    delta=np.zeros(60);delta[11]=1e-4
    observed=phi@(np.linalg.lstsq(x,y+delta,rcond=None)[0]-np.linalg.lstsq(x,y,rcond=None)[0])
    assert observed == pytest.approx(phi@operator@delta,rel=1e-7,abs=1e-12)


def test_correlated_distinct_innovations_are_outside_theorem():
    a=np.eye(4);w=np.ones(4)/4
    false_independence=quadratic(a@a.T,w)
    actual=quadratic(a@(.8*np.ones((4,4))+.2*np.eye(4))@a.T,w)
    assert actual > 3*false_independence


def test_training_only_rank_rule_and_exact_exchange():
    import pandas as pd
    from evidence_fusion.provider_models import calendar_features, fit_ols
    from evidence_fusion.exact_exchange import encode, decode
    times=pd.date_range('2016-01-01',periods=24*100,freq='h')
    x,_=calendar_features(times)
    # Deliberately omit weekends: dummy columns must be removed before QR.
    support=np.flatnonzero(times.dayofweek<5)
    y=3+x[:,1]+np.random.default_rng(29).normal(size=len(x))
    model=fit_ols(x,y,support,times.normalize().to_numpy())
    assert len(model.active_columns)<x.shape[1]
    recovered=decode(encode([model],'test',len(x)))[0]
    np.testing.assert_array_equal(recovered.support,model.support)
    np.testing.assert_allclose(recovered.operator,model.operator,atol=1e-12)


def test_two_provider_esci_scalar_connection():
    from scipy.optimize import minimize_scalar
    known=np.array([[.5,.2],[.2,1.]])
    r=np.array([.3,.6]);one=np.ones(2)
    exact=solve_simplex(known+np.outer(r,r))
    # ESCI centralized bound: known K plus diag(r_i^2/omega_i).
    def value(omega):
        covariance=known+np.diag(r*r/np.array([omega,1-omega]))
        precision=np.linalg.solve(covariance,one)
        weights=precision/precision.sum()
        assert weights.min()>=0  # this chosen case remains within our scope
        return 1/precision.sum()
    ref=minimize_scalar(value,bounds=(1e-8,1-1e-8),method='bounded',options={'xatol':1e-13})
    assert ref.success
    assert ref.fun==pytest.approx(exact.value,rel=1e-10)
