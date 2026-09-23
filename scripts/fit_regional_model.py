"""One fixed seasonal/factor model; all statistical choices use 2012 only."""
import hashlib
import json
from pathlib import Path
import resource
import time
import numpy as np
from sklearn.utils.extmath import randomized_svd
from evidence_fusion.regional_data import load_panel,slots


def main():
    cfg=json.loads(Path('configs/regional_pilot.json').read_text())
    start=time.perf_counter()
    y,times,meters,tariffs=load_panel('train')
    read_seconds=time.perf_counter()-start
    counts=np.isfinite(y).sum(0)
    eligible=counts>=cfg['minimum_training_readings']
    inclusion=[dict(meter=str(m),valid_training_readings=int(c),eligible=bool(e),tariff=t)
               for m,c,e,t in zip(meters,counts,eligible,tariffs)]
    Path('manifests/regional_households.json').write_text(json.dumps(inclusion,indent=2)+'\n')
    y=y[:,eligible]; meters=meters[eligible]
    if len(meters)<2000:
        raise RuntimeError('Fewer than 2000 training-eligible households; preserve cohort audit for explicit amendment')
    observed=np.isfinite(y)
    slot=slots(times)
    # Every eligible valid reading contributes to its household's seasonal mean.
    means=np.nanmean(y,axis=0)
    profile=np.empty((336,len(meters)),dtype=np.float64)
    for s in range(336):
        v=y[slot==s]
        c=np.isfinite(v).sum(0)
        profile[s]=np.divide(np.nansum(v,axis=0,dtype=np.float64),c,
                             out=means.astype(float).copy(),where=c>0)
    residual=y-profile[slot]
    scale=np.sqrt(np.nanmean(residual**2,axis=0))
    scale=np.maximum(scale,0.01)
    residual=(residual/scale).astype(np.float32)
    # Mean-imputed standardized residuals initialize a descriptive factor fit.
    # Missing values are zero RESIDUALS, never zero observed demand or scored labels.
    residual[~observed]=0
    u,s,vt=randomized_svd(residual,n_components=cfg['latent_dimension'],n_iter=2,
                          random_state=cfg['seed'])
    state=u*s/np.sqrt(len(meters))
    h=vt.T*np.sqrt(len(meters))
    # Refit each household loading only on its observed training rows (fixed ALS step).
    eye=np.eye(cfg['latent_dimension'])*1e-5
    for i in range(len(meters)):
        x=state[observed[:,i]].astype(float)
        h[i]=np.linalg.solve(x.T@x+eye,x.T@residual[observed[:,i],i])
    good=observed.mean(1)>=0.5
    adjacent=good[:-1]&good[1:]
    x=state[:-1][adjacent].astype(float); target=state[1:][adjacent].astype(float)
    transition=np.linalg.solve(x.T@x+eye,x.T@target).T
    radius=float(np.max(np.abs(np.linalg.eigvals(transition))))
    if radius>0.995:
        transition*=0.995/radius
    errors=target-x@transition.T
    process_var=np.maximum(np.mean(errors**2,axis=0),1e-4)
    prior_var=np.maximum(np.var(state[good],axis=0),1e-3)
    recon=state@h.T
    noise=np.empty(len(meters))
    for i in range(len(meters)):
        error=residual[observed[:,i],i]-recon[observed[:,i],i]
        noise[i]=max(float(np.mean(error**2)),0.05)
    groups=np.asarray([int(hashlib.sha256(str(m).encode()).hexdigest()[:8],16)%cfg['provider_groups'] for m in meters])
    typical=float(np.median(profile.sum(1)))
    peak=float(np.quantile(profile.sum(1),0.9))
    folder=Path('data/regional/model'); folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(folder/'model.npz',meters=meters.astype(str),profile=profile,scale=scale,
                        loadings=h.astype(float),transition=transition,process_var=process_var,
                        prior_var=prior_var,noise=noise,groups=groups,typical=typical,peak=peak)
    summary=dict(training_start=str(times[0]),training_end=str(times[-1]),
        households=len(meters),source_households=len(eligible),valid_training_records=int(observed.sum()),
        available_training_grid=int(observed.size),missing_fraction=float(1-observed.mean()),
        dimensions=cfg['latent_dimension'],factor_fit='mean-imputed standardized residual randomized SVD, then observed-only loading refit',
        transition_radius_before=radius,transition_radius_after=float(max(abs(np.linalg.eigvals(transition)))),
        dynamics_adjacent_pairs=int(adjacent.sum()),typical_halfhour_kwh=typical,peak_threshold_kwh=peak,
        provider_households=np.bincount(groups,minlength=cfg['provider_groups']).tolist(),
        tariff_counts={t:int(sum(x['tariff']==t and x['eligible'] for x in inclusion)) for t in set(tariffs)},
        parse_panel_seconds=read_seconds,total_seconds=time.perf_counter()-start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        model_sha256=hashlib.sha256((folder/'model.npz').read_bytes()).hexdigest(),
        data_policy='2012 only; duplicate keys and both local DST transition days excluded',
        input='u_t=0; deterministic weekly seasonality is the observation baseline; no tariff causal effect')
    Path('results/regional/model.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
