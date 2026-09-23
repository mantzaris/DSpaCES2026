"""Bounded analytic theorem checks, separate from real meter observations."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import null_space
from scipy.optimize import minimize
from evidence_fusion.conservative_fusion import solve_simplex, quadratic
from evidence_fusion.provenance_sketches import sufficient_epsilon


def run(out='results/controlled.json'):
    rng = np.random.default_rng(826)
    records = []
    # Six independent Gaussian matrices per family, not Gaussian error replicates.
    for p in (2, 4, 8):
        for overlap in (0., .5, .9):
            n, d = 64, 6
            common = round(n*overlap)
            universe = common+p*(n-common)
            design = np.column_stack([np.ones(universe),rng.normal(size=(universe,d-1))])
            phi = rng.normal(size=d)
            a = np.zeros((p, universe))
            for provider in range(p):
                support = np.r_[np.arange(common),common+provider*(n-common)+np.arange(n-common)]
                q,r=np.linalg.qr(design[support],mode='reduced')
                a[provider,support]=phi@np.linalg.solve(r,q.T)
            s=np.linalg.norm(a,axis=1);ktrue=a@a.T
            for setting, residual, future in [('training',0.,.01),('common',0.,10.),('residual',1.,1.)]:
                rr=np.full(p,residual)
                h=ktrue+np.outer(rr,rr)
                exact=solve_simplex(h)
                for k in (512,2048):
                    epsilon=sufficient_epsilon(k,1,p,.01/108)
                    for seed in (401,402):
                        g=np.random.default_rng(np.random.SeedSequence([seed,p,round(overlap*100),k])).normal(size=(universe,k))/np.sqrt(k)
                        z=a@g;kh=z@z.T
                        event=bool(np.all(np.abs(kh-ktrue)<=epsilon*np.outer(s,s)+1e-12))
                        hh=kh+epsilon*np.outer(s,s)+np.outer(rr,rr)
                        approximate=solve_simplex(hh)
                        weights=np.vstack([rng.dirichlet(np.ones(p),32),exact.weights,approximate.weights,np.eye(p)])
                        risk=quadratic(h,weights)+future
                        bound=quadratic(hh,weights)+future
                        sandwich=bool(np.all(risk<=bound+1e-10) and np.all(bound<=risk+2*epsilon*(weights@s)**2+1e-10))
                        excess=float(quadratic(h,approximate.weights)-exact.value)
                        limit=float(2*epsilon*(s@exact.weights)**2+approximate.gap)
                        if event and (not sandwich or excess>limit+1e-10):
                            raise AssertionError('Within-event theorem failure')
                        records.append(dict(p=p,overlap=overlap,setting=setting,k=k,seed=seed,
                            epsilon=epsilon,projection_event=event,sandwich=sandwich,
                            excess_risk=excess,excess_limit=limit,optimization_gap=float(approximate.gap),
                            common_floor=future,exact_risk=float(exact.value+future)))
    # Known analytic example.
    a=np.array([[np.sqrt(3),1,0,0],[np.sqrt(3),0,1,0],[0,0,0,2]])
    sol=solve_simplex(a@a.T)
    example=dict(weights=sol.weights.tolist(),mean=float(sol.weights@[100,102,110]),
                 variance=float(sol.value+1),equal_actual_variance=float(quadratic(a@a.T+1,np.ones(3)/3)))
    # Deliberately adapt a row to G's nullspace, outside finite nonadaptive guarantee.
    g=np.random.default_rng(73).normal(size=(16,32))/4
    adaptive=null_space(g)[:,0]
    violations=dict(correlated_distinct_innovations=dict(reported=.25,actual=.85),
        omitted_future_noise=dict(reported=.25,actual=9.25),
        projection_dependent_row=dict(actual=float(adaptive@adaptive),
            sketched=float(np.sum((g@adaptive)**2)),illustrative_inflation=.25,
            statement='Vector chosen after observing G; outside the theorem'))
    summary=dict(families=54,projection_evaluations=len(records),
        distinct_projection_draws=36,noise_settings_per_draw=3,
        allocation_note='delta=.01/108 for every evaluation is conservative; some projections are shared across noise settings',
        total_synthetic_failure_allocation=.01,projection_event_failures=sum(not r['projection_event'] for r in records),
        within_event_inequality_failures=0,gaussian_error_draws=0,
        precision='FP64 numerical checks, not a floating-point certificate',example=example,
        assumption_violations=violations,records=records)
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
    return summary


if __name__=='__main__':run()
