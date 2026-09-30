"""Train-screened lagged predictors with separate development validation (E3)."""
from __future__ import annotations
import hashlib,json
import numpy as np
import torch


def evaluate_association_gain(source,target,slope,intercept,null_mean,mask):
    if mask.sum()<16: return None
    without=(target[mask]-null_mean)**2
    with_edge=(target[mask]-(slope*source[mask]+intercept))**2
    gains=without-with_edge
    folds=np.array_split(gains,4)
    return dict(gain=float(gains.mean()),block_gains=[float(f.mean()) for f in folds],count=int(mask.sum()))


def discover_associations(train,development,groups,cap=3,max_lag=3):
    # Arrays are [window,channel,time]; no shifted cell crosses a source window.
    c=train.shape[1]; edges=[]; affinity=np.zeros((c,c))
    for target in range(c):
        candidates=[]
        for source in range(c):
            if source==target or groups[source]==groups[target]: continue
            best=None
            for lag in range(1,max_lag+1):
                sx=train[:,source,:-lag].ravel(); ty=train[:,target,lag:].ravel()
                mask=np.isfinite(sx)&np.isfinite(ty)
                if mask.sum()<64 or np.std(sx[mask])<1e-6: continue
                corr=float(np.corrcoef(sx[mask],ty[mask])[0,1])
                if best is None or abs(corr)>abs(best[0]): best=(corr,lag,sx,ty,mask)
            if best is None: continue
            corr,lag,sx,ty,mask=best; affinity[target,source]=abs(corr)
            centered=sx[mask]-sx[mask].mean()
            slope=float(np.dot(centered,ty[mask]-ty[mask].mean())/(np.dot(centered,centered)+1.))
            intercept=float(ty[mask].mean()-slope*sx[mask].mean())
            candidates.append((abs(corr),source,lag,slope,intercept,float(ty[mask].mean())))
        for correlation,source,lag,slope,intercept,mean in sorted(candidates,reverse=True)[:cap*2]:
            sx=development[:,source,:-lag].ravel(); ty=development[:,target,lag:].ravel()
            mask=np.isfinite(sx)&np.isfinite(ty)
            result=evaluate_association_gain(sx,ty,slope,intercept,mean,mask)
            if result is not None and result['gain']>0 and sum(v>0 for v in result['block_gains'])>=3:
                edges.append(dict(id=f'a{target:03d}_{source:03d}',source=int(source),target=target,lag=lag,
                    sign=1 if slope>=0 else -1,magnitude=abs(slope),intercept=intercept,
                    validation_gain=result['gain'],validation_blocks=result['block_gains'],
                    training_abs_correlation=correlation,regime='reference',valid_from='training',valid_to=None))
                if sum(e['target']==target for e in edges)>=cap: break
    payload=json.dumps(edges,sort_keys=True).encode()
    return dict(version=hashlib.sha256(payload).hexdigest()[:16],edges=edges,
        affinity=affinity.tolist(),groups=groups,predictor='univariate ridge, alpha 1, normalized units',
        acceptance='positive mean gain and positive gain in at least 3 of 4 development folds')


def graph_context(values,observed,graph,dropout=0.,generator=None):
    """Attribute-sensitive graph predictions; source values enter only when visible."""
    prediction=torch.zeros_like(values); count=torch.zeros_like(values)
    for lag in sorted(set(e['lag'] for e in graph['edges'])):
        if lag>=values.shape[-1]: continue
        edges=[e for e in graph['edges'] if e['lag']==lag]
        sources=torch.tensor([e['source'] for e in edges],device=values.device)
        targets=torch.tensor([e['target'] for e in edges],device=values.device)
        slopes=torch.tensor([e['sign']*e['magnitude'] for e in edges],device=values.device,dtype=values.dtype)
        intercepts=torch.tensor([e['intercept'] for e in edges],device=values.device,dtype=values.dtype)
        valid=observed[:,sources,:-lag]
        if dropout:
            retained=torch.rand(len(edges),device=values.device,generator=generator)>=dropout
            valid=valid & retained[None,:,None]
        p=slopes[None,:,None]*values[:,sources,:-lag]+intercepts[None,:,None]
        prediction[:,:,lag:].index_add_(1,targets,torch.where(valid,p,torch.zeros_like(p)))
        count[:,:,lag:].index_add_(1,targets,valid.to(values.dtype))
    return prediction/count.clamp_min(1),count>0


def edge_residuals(x,graph,horizon=8):
    scores=[]
    for edge in graph['edges']:
        s,t,lag=edge['source'],edge['target'],edge['lag']
        predicted=edge['sign']*edge['magnitude']*x[:,s,-horizon-lag:-lag]+edge['intercept']
        target=x[:,t,-horizon:]
        with np.errstate(invalid='ignore'):
            scores.append(np.nanmean(np.abs(target-predicted),axis=-1))
    return np.stack(scores,axis=-1) if scores else np.zeros((len(x),0))
