import numpy as np
import pytest
from scipy.linalg import cho_solve
from evidence_fusion.regional_solver import (fixed_objective,components,assemble,Family,
    joint_basis,batched_pcg,banded_factor,information_smoother,accuracy)
from evidence_fusion.regional_data import load_panel,masked_provider_statistics


def test_gradient_centered_regularization_and_masked_access():
    rng=np.random.default_rng(8); d=3; length=4; lam=.4
    f=np.eye(d)*.7; q=np.arange(1,d+1); p=np.ones(d)
    center=rng.normal(size=length*d); prior=rng.normal(size=d)
    h=rng.normal(size=(8,d)); y=rng.normal(size=(length,8)); mask=rng.random(y.shape)>.2
    groups=np.arange(8)%2; weights=np.array([1.,0.])
    c,b=masked_provider_statistics(y,mask,h,np.ones(8),groups,weights)
    hidden=y.copy(); hidden[:,groups==1]=np.nan; hidden[~mask]=np.nan
    c2,b2=masked_provider_statistics(hidden,mask,h,np.ones(8),groups,weights)
    np.testing.assert_array_equal(c,c2); np.testing.assert_array_equal(b,b2)
    c0,b0=fixed_objective(f,q,p,length,center,prior,lam)
    a,rhs,_=assemble(np.concatenate([c0[None],components(c)]),np.vstack([b0,b.reshape(2,-1)]),weights[None],lam)
    def objective(z):
        zz=z.reshape(length,d)
        val=lam*np.sum((z-center)**2)+np.sum((zz[0]-prior)**2/p)
        val+=np.sum((zz[1:]-zz[:-1]@f.T)**2/q)
        for t in range(length):
            for g in range(2):
                valid=mask[t]&(groups==g)
                val+=weights[g]*np.sum((y[t,valid]-h[valid]@zz[t])**2)
        return val/2
    z=rng.normal(size=length*d); eps=1e-5
    numeric=np.array([(objective(z+eps*np.eye(len(z))[i])-objective(z-eps*np.eye(len(z))[i]))/(2*eps) for i in range(len(z))])
    np.testing.assert_allclose(numeric,a[0]@z-rhs[0],rtol=1e-7,atol=1e-7)


def test_family_bounds_and_polynomial_output():
    rng=np.random.default_rng(3)
    q,_=np.linalg.qr(rng.normal(size=(12,12)))
    cs=[]
    for _ in range(4):
        r=rng.normal(size=(12,12))*.005
        cs.append(q@(np.diag(rng.uniform(1,2,12))+r@r.T)@q.T)
    cs=np.array(cs); family=Family(cs,q,.1,blocks=4)
    a=np.array([1,.4,0,.8]); d,cert=family.certificate(a)
    f=np.einsum('g,gij->ij',a,family.e)/np.sqrt(d[:,None]*d[None,:])
    assert np.linalg.norm(f,2)<=cert['delta']*(1+1e-9)
    assert cert['block_delta']<=cert['row_delta']*(1+1e-10)
    b=rng.normal(size=12); j=rng.normal(size=12)
    matrix=np.einsum('g,gij->ij',a,cs)+np.eye(12)*.1
    exact=np.linalg.solve(matrix,b)
    z,h=family.polynomial(b,a,2)
    bound=cert['delta']**3/(1-cert['delta'])*np.linalg.norm(h)
    multiplier=np.linalg.norm((q.T@j)/np.sqrt(d))
    assert abs(j@(z-exact))<=bound*multiplier+1e-12
    assert Family.quadratic_upper(-np.eye(2),np.eye(2),np.ones(2),2)==np.inf


def test_banded_smoothing_cg_and_zero_rhs():
    d=3; length=5
    c,b=fixed_objective(np.eye(d)*.8,np.ones(d),np.ones(d),length,np.zeros(d*length),np.ones(d),.2)
    a=c+np.eye(len(b))*.2; exact=np.linalg.solve(a,b)
    from scipy.linalg import cho_solve_banded
    np.testing.assert_allclose(cho_solve_banded((banded_factor(a,d),True),b),exact,atol=1e-12)
    np.testing.assert_allclose(information_smoother(a,b,d),exact,atol=1e-12)
    x,steps=batched_pcg(np.stack([a,a]),np.stack([b,b*0]))
    np.testing.assert_allclose(x[0],exact,atol=1e-8)
    assert np.all(x[1]==0) and steps[1]==0
    assert accuracy(a,b*0,x[1],b*0)['relative_residual']==0


def test_seal_and_rjd_orthogonality():
    with pytest.raises(ValueError): load_panel('sealed')
    q=joint_basis(np.array([np.diag([1.,2,3]),np.diag([3.,2,7])]),12,2)
    np.testing.assert_allclose(q.T@q,np.eye(3),atol=1e-12)


def test_unavailable_rhs_cannot_contaminate_query():
    cs=np.array([np.eye(2),np.eye(2),np.eye(2)])
    bs=np.array([[1.,1.],[2.,3.],[np.nan,np.nan]])
    a,b,_=assemble(cs,bs,np.array([[1.,0.]]),.1)
    np.testing.assert_array_equal(b,[[3.,4.]])
