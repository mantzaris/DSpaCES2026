"""PPCA and mixture-PPCA conditional densities with exactly the same corruption law.

Training missing context is filled by training means for parameter fitting only.
At inference, unobserved context is marginalized analytically. Target blocks must
be complete. The fitted joint density remains a normalized probabilistic model.
"""
import hashlib
import json
from pathlib import Path
import time
import pickle

import numpy as np
import torch
from scipy.special import logsumexp
from sklearn.utils.extmath import randomized_svd

from .flow_data import load_data, graph_for, sha256, configuration
from .graph_flow_model import build_context
from .flow_math import GaussianCorruption, gaussian_fault_posterior, gaussian_log_prob
from .experiment import json_save


def context_matrix(values, query, graph, length, mode='graph'):
    """Raw allowed observations, not target-aware fitted residuals."""
    if mode=='all_channels':
        x=np.asarray(values,float).copy()
        groups=np.asarray(graph['groups']);x[:,groups==groups[query],-8:]=np.nan
        return x[:,:,-length:].reshape(len(x),-1)
    inputs=build_context(torch.as_tensor(values),torch.full((len(values),),query,dtype=torch.long),graph,length)
    sequence=inputs.sequence.numpy()
    return np.where(sequence[...,1]>0,sequence[...,0],np.nan).reshape(len(values),-1)


def lowrank_log_prob(x,mean,loading,noise):
    centered=x-mean;dimension=len(mean)
    small=np.eye(loading.shape[1])+loading.T@loading/noise
    rhs=centered@loading/noise
    quadratic=(centered**2).sum(-1)/noise-(rhs*np.linalg.solve(small,rhs.T).T).sum(-1)
    logdet=dimension*np.log(noise)+np.linalg.slogdet(small)[1]
    return -.5*(quadratic+logdet+dimension*np.log(2*np.pi))


def fit_component(x,weights,rank,floor,seed):
    weights=weights/max(weights.sum(),1e-15);mean=weights@x
    centered=(x-mean)*np.sqrt(weights[:,None])
    rank=min(rank,x.shape[1]-1,len(x)-1)
    _,singular,vectors=randomized_svd(centered,n_components=rank,random_state=seed,n_iter=4)
    trace=float(np.square(centered).sum())
    noise=max(floor,(trace-float(np.square(singular).sum()))/max(1,x.shape[1]-rank))
    loading=vectors.T*np.sqrt(np.maximum(singular**2-noise,0))
    return dict(mean=mean,loading=loading,noise=noise)


def fit_joint(x,rank,mixtures,floor,seed):
    fill=np.nanmean(x,axis=0);fill=np.nan_to_num(fill)
    x=np.where(np.isfinite(x),x,fill)
    if mixtures==1:return [dict(fit_component(x,np.ones(len(x)),rank,floor,seed),weight=1.)]
    # Deterministic two-cluster initialization, followed by bounded weighted PPCA EM.
    from sklearn.cluster import KMeans
    labels=KMeans(n_clusters=mixtures,n_init=5,random_state=seed).fit_predict(x)
    responsibility=np.eye(mixtures)[labels]*.98+.02/mixtures
    components=[]
    for iteration in range(12):
        components=[dict(fit_component(x,responsibility[:,k],rank,floor,seed+k),
                         weight=float(responsibility[:,k].mean())) for k in range(mixtures)]
        logs=np.stack([lowrank_log_prob(x,c['mean'],c['loading'],c['noise'])+np.log(c['weight']) for c in components],1)
        responsibility=np.exp(logs-logsumexp(logs,axis=1,keepdims=True))
        responsibility=np.maximum(responsibility,1e-8);responsibility/=responsibility.sum(1,keepdims=True)
    return components


def fit_ppca(root,dataset,length,rank,mixtures=1,mode='graph'):
    root=Path(root);config=configuration(root)
    data=load_data(root,dataset,'train');values=data['x'][data['reference']];graph=graph_for(root,dataset)
    spec=dict(dataset=dataset,length=length,rank=rank,mixtures=mixtures,mode=mode,
              variance_floor=config['ppca_variance_floor'],code_sha256=sha256(__file__),
              train_sha256=sha256(root/'data/processed'/dataset/'train.npz'))
    identity=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:20]
    path=root/'results/graph_flow_v1/models'/('ppca_'+identity+'.pkl');record_path=path.with_suffix('.json')
    if record_path.exists():
        record=json.loads(record_path.read_text());assert sha256(path)==record['sha256'];return record
    start=time.perf_counter();models=[]
    for query in range(values.shape[1]):
        eligible=np.isfinite(values[:,query,-8:]).all(-1);raw=values[eligible]
        context=context_matrix(raw,query,graph,length,mode)
        keep=np.isfinite(context).any(0)
        joint=np.concatenate([raw[:,query,-8:],context[:,keep]],1)
        models.append(dict(context_keep=keep,components=fit_joint(joint,rank,mixtures,config['ppca_variance_floor'],20261001+query)))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('wb') as stream:pickle.dump(models,stream,protocol=4)
    record=dict(path=str(path.relative_to(root)),sha256=sha256(path),specification=spec,training_seconds=time.perf_counter()-start,
                training_windows=len(values),source_blocks=len(set(data['block'][data['reference']].tolist())),
                missing_training_context='training-mean fill for parameter fitting, exact observed-context marginal at inference')
    json_save(record_path,record);return record


def load_ppca(root,record):
    path=Path(root)/record['path'];assert sha256(path)==record['sha256']
    with path.open('rb') as stream:return pickle.load(stream)


def conditional_components(model,context,log_weights=False):
    context=context[model['context_keep']];observed=np.isfinite(context)
    components=[];logs=[]
    for component in model['components']:
        mean,loading,noise=component['mean'],component['loading'],component['noise']
        wy=loading[:8];wc=loading[8:][observed];xc=context[observed];mc=mean[8:][observed]
        precision=np.eye(loading.shape[1])+wc.T@wc/noise
        posterior_cov=np.linalg.inv(precision);latent_mean=posterior_cov@wc.T@(xc-mc)/noise
        components.append((mean[:8]+wy@latent_mean,noise*np.eye(8)+wy@posterior_cov@wy.T))
        logs.append(float(lowrank_log_prob(xc,mc,wc,noise))+np.log(component['weight']))
    normalized=np.asarray(logs)-logsumexp(logs)
    weights=normalized if log_weights else np.exp(normalized)
    return weights,components


def infer_ppca(models,values,graph,length,scale=1.,mode='graph',seed=1,reference=None,draws=512,times=None):
    channel=GaussianCorruption(8,scale=scale,times=times);channels=values.shape[0]
    eligible=np.isfinite(values[:,-8:]).all(-1)
    scores=np.full(channels,-1e12);normal=np.full(channels,-1e12);means=np.full((channels,8),np.nan)
    prior_means=means.copy();lower=means.copy();upper=means.copy();metrics=np.full((channels,4),np.nan)
    rng=np.random.default_rng(seed);start=time.perf_counter()
    for query in np.flatnonzero(eligible):
        context=context_matrix(values[None],int(query),graph,length,mode)[0]
        log_weights,components=conditional_components(models[query],context,log_weights=True)
        posteriors=[gaussian_fault_posterior(values[query,-8:],mean,cov,channel) for mean,cov in components]
        log_normal=logsumexp([w+p['log_normal'] for w,p in zip(log_weights,posteriors)])
        log_fault=logsumexp([w+p['log_fault'] for w,p in zip(log_weights,posteriors)])
        posterior_weights=np.exp([w+p['log_fault']-log_fault for w,p in zip(log_weights,posteriors)])
        scores[query]=log_fault-log_normal;normal[query]=-log_normal
        means[query]=sum(w*p['mean'] for w,p in zip(posterior_weights,posteriors))
        prior_means[query]=sum(w*p[0] for w,p in zip(np.exp(log_weights),components))
        component_weights=np.concatenate([w*p['component_weights'] for w,p in zip(posterior_weights,posteriors)])
        component_means=np.concatenate([p['component_means'] for p in posteriors])
        component_covariances=np.concatenate([p['component_covariances'] for p in posteriors])
        choices=rng.choice(len(component_weights),size=draws,p=component_weights)
        samples=np.empty((draws,8))
        for index in np.unique(choices):
            mask=choices==index;samples[mask]=rng.multivariate_normal(component_means[index],component_covariances[index],mask.sum())
        lower[query],upper[query]=np.quantile(samples,[.05,.95],axis=0)
        if reference is not None:
            truth=reference[query,-8:];ordered=np.sort(samples,axis=0)
            halfpair=((2*np.arange(1,draws+1)-draws-1)[:,None]*ordered).sum(0)/draws**2
            crps=np.mean(np.abs(samples-truth).mean(0)-halfpair)
            energy=np.linalg.norm(samples-truth,axis=-1).mean()-.5*np.linalg.norm(samples[:draws//2]-samples[draws//2:],axis=-1).mean()
            metrics[query]=[crps,((truth>=lower[query])&(truth<=upper[query])).mean(),(upper[query]-lower[query]).mean(),energy]
    return dict(score=scores,nll=normal,mean=means,prior_mean=prior_means,lower=lower,upper=upper,metrics=metrics,
                seconds=time.perf_counter()-start)
