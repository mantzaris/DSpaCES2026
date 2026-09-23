"""Reversible synthetic demand/readout perturbations; evaluator privilege only."""
import numpy as np

FAMILIES=('regional','localized','cancel_exact','cancel_approx','delayed','ramp')


def overlay(background, model, family, magnitude, seed, warmup=24):
    rng=np.random.default_rng(seed)
    t,n=background.shape
    shift=np.zeros((t,n),dtype=np.float64)
    onset=warmup+int(rng.integers(6,11))
    duration=24 if family in ('cancel_exact','cancel_approx','delayed','ramp') else int(rng.choice([12,20]))
    group=int(rng.integers(16)); members=np.flatnonzero(model['groups']==group)
    scale=np.sqrt(model['detail_var']+model['measurement_var'])
    # Draw a balanced mixture of training consumption sizes without using outcomes.
    ordered=members[np.argsort(model['profile'][:,members].mean(0))]
    selected=np.concatenate([rng.choice(x,min(16,len(x)),replace=False) for x in np.array_split(ordered,4)])
    rng.shuffle(selected)
    plus,minus=selected[:32],selected[32:64]
    end=min(onset+duration,t)
    if family=='none':
        plus=minus=np.array([],dtype=int); onset=warmup+8; duration=0
    elif family=='regional':
        plus=np.arange(n);minus=np.array([],dtype=int)
        wave=np.ones(end-onset)
        shift[onset:end]=magnitude*.15*scale[None,:]*wave[:,None]
    elif family in ('localized','ramp','sensor_fault'):
        minus=np.array([],dtype=int)
        sign=-1 if family=='localized' and seed%2 else 1
        wave=np.linspace(0.,1.,end-onset) if family=='ramp' else np.ones(end-onset)
        requested=magnitude*scale[plus][None,:]*wave[:,None]
        if sign<0:
            requested=np.minimum(requested,.8*np.nan_to_num(background[onset:end,plus],nan=0.))
        shift[np.ix_(np.arange(onset,end),plus)]=sign*requested
    else:
        for i,j in zip(plus,minus):
            requested=magnitude*min(scale[i],scale[j])
            valid=np.isfinite(background[onset:end,i])&np.isfinite(background[onset:end,j])
            if family=='delayed':
                # One feasible initial amplitude; actual generator is a demand
                # overlay, NOT a shock in the fitted model's state coordinates.
                k=np.arange(end-onset); rho_p=.96;rho_m=.70
                feasible=np.where(valid,.8*background[onset:end,j]/rho_m**k,np.inf)
                amplitude=min(requested,float(feasible.min()))
                pos=amplitude*rho_p**k;neg=amplitude*rho_m**k
            else:
                pos=np.minimum(requested,.8*np.nan_to_num(background[onset:end,j],nan=0.))
                neg=pos*(.8 if family=='cancel_approx' else 1.)
            pos=np.where(valid,pos,0.);neg=np.where(valid,neg,0.)
            shift[onset:end,i]=pos;shift[onset:end,j]=-neg
    shift[~np.isfinite(background)]=0.
    readings=background.astype(np.float64)+shift
    targets=background.astype(np.float64)+(0. if family=='sensor_fault' else shift)
    if np.nanmin(readings)<-1e-12 or np.nanmin(targets)<-1e-12:
        raise ArithmeticError('Overlay violates nonnegative consumption')
    signature=np.stack([shift[:,model['groups']==g].sum(1) for g in range(16)],1)
    if family=='cancel_exact' and np.max(abs(signature))>1e-10:
        raise ArithmeticError('Group cancellation failed')
    affected=np.flatnonzero(np.any(shift!=0.,axis=0))
    metadata=dict(family=family,magnitude=magnitude,seed=seed,onset=onset-warmup+1,
        onset_array=onset,duration=duration,group=group,
        affected_ids=affected.tolist(),positive_ids=plus.tolist(),negative_ids=minus.tolist(),
        affected_groups=np.unique(model['groups'][affected]).tolist(),
        max_group_signature=float(np.max(abs(signature))),
        max_regional_signature=float(np.max(abs(signature.sum(1)))),
        realized_peak_household_shift=float(np.max(abs(shift))),
        zero_effect=not bool(len(affected)),physical_demand=family!='sensor_fault')
    return readings,targets,shift,signature,metadata
