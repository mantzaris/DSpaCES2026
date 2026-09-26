"""Affine SPD moving-horizon systems and established shared-basis solvers.

Bounds are exact-arithmetic results with FP64 numerical audits, not a formal
floating-point certificate. Negative/cancelled Gram forms fail closed.
"""
import numpy as np
import time
from scipy.linalg import eigh, cho_factor, cho_solve, cholesky_banded, cho_solve_banded


def fixed_objective(transition, process_var, prior_var, length, center, prior, lam):
    d=len(prior); n=length*d
    c=np.zeros((n,n)); b=np.zeros(n)
    pinv=1/prior_var; qinv=1/process_var
    c[:d,:d]+=np.diag(pinv); b[:d]+=pinv*prior
    for t in range(1,length):
        a=slice((t-1)*d,t*d); k=slice(t*d,(t+1)*d)
        c[a,a]+=transition.T@(qinv[:,None]*transition)
        c[k,k]+=np.diag(qinv)
        c[k,a]-=qinv[:,None]*transition
        c[a,k]-=transition.T*qinv
    return c,b+lam*center


def components(blocks):
    g,l,d,_=blocks.shape
    result=np.zeros((g,l*d,l*d))
    for t in range(l):
        result[:,t*d:(t+1)*d,t*d:(t+1)*d]=blocks[:,t]
    return result


def assemble(cs, bs, profiles, lam):
    a=np.column_stack([np.ones(len(profiles)),profiles])
    matrices=np.einsum('bg,gij->bij',a,cs,optimize=True)
    matrices[:,np.arange(matrices.shape[1]),np.arange(matrices.shape[1])]+=lam
    # Per-profile access boundary: a provider with zero availability does not
    # release its observation-dependent RHS. This also prevents 0 * NaN leakage.
    released=np.where(a[:,:,None]>0,bs[None,:,:],0.)
    rhs=np.sum(a[:,:,None]*released,axis=1)
    return matrices,rhs,a


def joint_basis(cs, seed, trials=3):
    """He/Kressner RJD Algorithm 1, Gaussian combinations, full orthogonal basis."""
    rng=np.random.default_rng(seed)
    candidates=[]
    for _ in range(trials):
        _,q=eigh(np.einsum('g,gij->ij',rng.normal(size=len(cs)),cs))
        transformed=q.T@cs@q
        diagonal=np.diagonal(transformed,axis1=1,axis2=2)
        score=float(np.sum(diagonal**2))
        candidates.append((score,q))
    return max(candidates,key=lambda x:x[0])[1]


class Family:
    def __init__(self, cs, q, lam, blocks=8):
        start=time.perf_counter()
        self.q=q; self.lam=lam
        transformed=q.T@cs@q
        self.diag=np.diagonal(transformed,axis1=1,axis2=2).copy()
        self.e=transformed.copy()
        n=q.shape[0]; g=len(cs)
        self.e[:,np.arange(n),np.arange(n)]=0
        self.parts=np.array_split(np.arange(n),blocks)
        self.transform_seconds=time.perf_counter()-start
        start=time.perf_counter()
        flat=self.e.reshape(g,-1)
        self.k=flat@flat.T
        self.ka=np.abs(flat)@np.abs(flat).T
        self.global_gram_seconds=time.perf_counter()-start
        start=time.perf_counter()
        self.kblocks=np.empty((blocks,blocks,g,g))
        self.kabs=np.empty_like(self.kblocks)
        for p,ip in enumerate(self.parts):
            for r,ir in enumerate(self.parts):
                block=self.e[:,ip[:,None],ir].reshape(g,-1)
                self.kblocks[p,r]=block@block.T
                self.kabs[p,r]=np.abs(block)@np.abs(block).T
        self.block_gram_seconds=time.perf_counter()-start

    @staticmethod
    def quadratic_upper(k, absolute_products, a, length):
        raw=float(a@k@a)
        if raw<0 or not np.isfinite(raw):
            return np.inf
        # Conservative standard dot/reduction allowance for STORED E entries.
        # Does not cover basis construction or all assembly error; see proof audit.
        u=np.finfo(float).eps/2
        count=length+2*len(a)**2+4
        gamma=count*u/(1-count*u)
        error=gamma*float(np.abs(a)@absolute_products@np.abs(a))
        return np.nextafter(raw+error,np.inf)

    def certificate(self,a):
        d=self.lam+a@self.diag
        if np.min(d)<=0:
            return d,dict(global_delta=np.inf,block_delta=np.inf,row_delta=np.inf,delta=np.inf)
        n=len(d)
        start=time.perf_counter()
        global_delta=np.sqrt(self.quadratic_upper(self.k,self.ka,a,n*n))/np.min(d)
        global_seconds=time.perf_counter()-start
        start=time.perf_counter()
        mins=np.array([min(d[i]) for i in self.parts])
        m=np.empty((len(mins),len(mins)))
        for p,ip in enumerate(self.parts):
            for r,ir in enumerate(self.parts):
                m[p,r]=np.sqrt(self.quadratic_upper(self.kblocks[p,r],self.kabs[p,r],a,len(ip)*len(ir)))/np.sqrt(mins[p]*mins[r])
        block_delta=float(eigh(m,eigvals_only=True)[-1])
        row_delta=float(np.max(m.sum(1)))
        return d,dict(global_delta=float(global_delta),block_delta=block_delta,
                      row_delta=row_delta,delta=min(float(global_delta),block_delta),
                      global_query_seconds=global_seconds,block_query_seconds=time.perf_counter()-start)

    def initialize(self,b,a):
        d=self.lam+a@self.diag
        return self.q@((self.q.T@b)/d)

    def polynomial(self,b,a,degree):
        d=self.lam+a@self.diag
        inv=1/np.sqrt(d)
        h=inv*(self.q.T@b)
        f=np.einsum('g,gij->ij',a,self.e)*inv[:,None]*inv[None,:]
        term=h.copy(); u=h.copy()
        for _ in range(degree):
            term=-f@term; u+=term
        return self.q@(inv*u),h


def batched_pcg(a,b,x=None,preconditioner=None,tol=1e-7,maxiter=400):
    x=np.zeros_like(b) if x is None else x.copy()
    def mv(v): return (a@v[...,None])[...,0]
    def pre(r):
        if preconditioner is None:
            return r/np.diagonal(a,axis1=1,axis2=2)
        q,d=preconditioner
        return ((r@q)/d)@q.T
    r=b-mv(x); z=pre(r); p=z.copy(); rz=np.sum(r*z,axis=1)
    norm=np.linalg.norm(b,axis=1); threshold=tol*np.where(norm>0,norm,1)
    iterations=np.zeros(len(b),int)
    active=np.linalg.norm(r,axis=1)>threshold
    for step in range(maxiter):
        if not np.any(active): break
        ap=mv(p); den=np.sum(p*ap,axis=1)
        alpha=np.divide(rz,den,out=np.zeros_like(rz),where=active&(den>0))
        x+=alpha[:,None]*p; r-=alpha[:,None]*ap
        iterations[active]+=1
        next_active=np.linalg.norm(r,axis=1)>threshold
        z=pre(r); nxt=np.sum(r*z,axis=1)
        beta=np.divide(nxt,rz,out=np.zeros_like(rz),where=next_active&(rz!=0))
        p=z+beta[:,None]*p; p[~next_active]=0
        rz=nxt; active=next_active
    return x,iterations


def banded_factor(a,dimension):
    # Dense neighboring state blocks give scalar lower bandwidth 2*d-1.
    width=2*dimension-1; n=len(a)
    band=np.zeros((width+1,n))
    for k in range(width+1): band[k,:n-k]=np.diag(a,-k)
    return cholesky_banded(band,lower=True,check_finite=False)


def information_smoother(a,b,dimension):
    """Block Gaussian elimination/back substitution = finite-window information smoother."""
    d=dimension; length=len(b)//d
    schur=[]; factors=[]; rhs=[]
    for t in range(length):
        sl=slice(t*d,(t+1)*d)
        block=a[sl,sl].copy(); v=b[sl].copy()
        if t:
            lower=a[sl,slice((t-1)*d,t*d)]
            cross=cho_solve(factors[-1],lower.T,check_finite=False)
            block-=lower@cross
            v-=lower@cho_solve(factors[-1],rhs[-1],check_finite=False)
        schur.append(block); factors.append(cho_factor(block,lower=True,check_finite=False)); rhs.append(v)
    x=np.zeros_like(b)
    for t in reversed(range(length)):
        sl=slice(t*d,(t+1)*d); v=rhs[t].copy()
        if t<length-1: v-=a[sl,slice((t+1)*d,(t+2)*d)]@x[(t+1)*d:(t+2)*d]
        x[sl]=cho_solve(factors[t],v,check_finite=False)
    return x


def accuracy(a,b,x,reference):
    residual=np.linalg.norm(a@x-b); bn=np.linalg.norm(b)
    error=x-reference
    energy=float(error@a@error); refenergy=float(reference@a@reference)
    return dict(relative_residual=float(residual/bn if bn else residual),
                weighted_relative_error=float(np.sqrt(max(energy,0)/refenergy) if refenergy>0 else np.sqrt(max(energy,0))),
                euclidean_forward_error=float(np.linalg.norm(error)),
                relative_forward_error=float(np.linalg.norm(error)/np.linalg.norm(reference)) if np.linalg.norm(reference)>0 else float(np.linalg.norm(error)),
                backward_error=float(residual/(np.linalg.norm(a,'fro')*np.linalg.norm(x)+bn)) if bn+np.linalg.norm(x)>0 else 0.)
