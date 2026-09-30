"""An independent graph-coupled benchmark and model-independent interventions."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from scipy.spatial.distance import cdist

from .data import SensorData, save_data
from .utils import seed_all


def system(node_count: int, seed: int = 3107) -> tuple[np.ndarray,np.ndarray,np.ndarray,dict]:
    rng=np.random.default_rng(seed+node_count)
    coordinates=rng.uniform(size=(node_count,2))
    radius=np.sqrt(12/(np.pi*node_count))
    distances=cdist(coordinates,coordinates)
    adjacency=((distances<radius)&(distances>0)).astype(np.float32)
    laplacian=np.diag(adjacency.sum(1))-adjacency
    laplacian/=max(adjacency.sum(1).max(),1)
    transition=.82*np.eye(node_count)-.25*laplacian
    radius_actual=float(np.max(np.abs(np.linalg.eigvalsh(transition))))
    if radius_actual>=1:
        raise ValueError('Synthetic transition is unstable')
    return coordinates,adjacency,transition,{'a':.82,'kappa':.25,'sigma':.12,
            'laplacian_normalization':'maximum degree','geometric_radius':radius,
            'spectral_radius':radius_actual,'graph_seed':seed+node_count}


def simulate(coordinates: np.ndarray, transition: np.ndarray, length: int,
             seed: int, device: str = 'cpu', intervention: dict | None = None) -> np.ndarray:
    """Graph process with known daily/weekly and latent OU drivers, burn-in 256."""
    generator=torch.Generator(device=device).manual_seed(seed)
    n=len(coordinates)
    matrix=torch.as_tensor(transition,dtype=torch.float32,device=device)
    changed=matrix.clone()
    if intervention is not None:
        nodes=torch.as_tensor(intervention['nodes'],device=device)
        changed[nodes]=(1-intervention['severity'])*matrix[nodes]
        changed[nodes,nodes]=0
        changed[nodes,nodes]=.82-changed[nodes].sum(-1)
    coords=torch.as_tensor(coordinates,dtype=torch.float32,device=device)
    loadings=torch.stack((torch.ones(n,device=device),torch.sin(2*torch.pi*coords[:,0]),
                         torch.cos(2*torch.pi*coords[:,1])),1)
    noise=torch.randn(length+256,n,generator=generator,device=device)*.12
    factor_noise=torch.randn(length+256,3,generator=generator,device=device)*.025
    state=torch.zeros(n,device=device)
    factors=torch.zeros(3,device=device)
    output=torch.empty(length,n,1,device=device)
    phase=seed%288
    for t in range(length+256):
        factors=.95*factors+factor_noise[t]
        season=.08*np.sin(2*np.pi*(t+phase)/288)+.03*np.cos(2*np.pi*(t+phase)/(288*7))
        active=intervention is not None and intervention['onset']<=t-256<intervention['onset']+intervention['duration']
        state=(changed if active else matrix)@state+loadings@factors+season+noise[t]
        if t>=256: output[t-256,:,0]=state
    return output.cpu().numpy()


def prepare_synthetic(root: Path, node_count: int, device: str = 'cpu') -> SensorData:
    coords,adjacency,transition,audit=system(node_count)
    segments=[]; time_segments=[]; episodes=[]; seeds=[]; bounds=[0]; cursor=0
    for split,(number,length) in enumerate([(48,1024),(12,1024),(32,256),(32,384)]):
        for episode in range(number):
            seed=100000+node_count*1000+split*100+episode
            segments.append(simulate(coords,transition,length,seed,device))
            time_segments.append(np.datetime64('2020-01-01','ns').astype('int64')+(np.arange(length,dtype=np.int64)+256+seed%288)*300*10**9)
            episodes.append([cursor,cursor+length,split]);seeds.append(seed);cursor+=length
        bounds.append(cursor)
    values=np.concatenate(segments)
    timestamps=np.concatenate(time_segments)
    audit.update({'source':'Independently specified graph-coupled stochastic process',
                  'normal_drivers':'daily + weekly sinusoid; 3 OU factors with spatial sinusoidal loadings',
                  'episode_seeds':seeds,'timestamp_note':'Synthetic display index; calendar features use episode phase stored by seed'})
    return save_data(root,f'synthetic{node_count}',values,timestamps,coords,adjacency,np.arange(node_count),
                     ['signal'],['arbitrary units'],300,audit,np.array(bounds),np.array(episodes))


def fault_nodes(adjacency: np.ndarray, size: int, seed: int, disconnected: bool) -> list[int]:
    rng=np.random.default_rng(seed)
    start=int(rng.integers(len(adjacency)))
    chosen=[start]
    while len(chosen)<size:
        boundary=np.flatnonzero((adjacency[chosen]>0).any(0))
        options=np.setdiff1d(boundary,chosen)
        if not len(options): options=np.setdiff1d(np.arange(len(adjacency)),chosen)
        chosen.append(int(rng.choice(options)))
    if disconnected:
        far=np.setdiff1d(np.arange(len(adjacency)),chosen)
        if len(far):
            # Partly disconnected selection relative to original connected patch.
            linkage=adjacency[far][:,chosen].sum(1)
            chosen[-size//2:]=far[np.argsort(linkage,kind='stable')[:size//2]].tolist()
    return sorted(chosen)


def inject(values: np.ndarray, nodes: list[int], onset: int, duration: int,
           kind: str, severity: float, seed: int) -> np.ndarray:
    """Operate on standardized recordings, retain missing values except dropout.

    These sensor-level interventions do not depend on generated references.
    'decouple' is observational decorrelation; synthetic dynamical coupling
    changes are supplied separately as a model-level sensitivity.
    """
    rng=np.random.default_rng(seed)
    out=values.copy()
    stop=min(onset+duration,len(out))
    x=out[onset:stop,nodes].copy()
    mask=np.isfinite(x)
    steps=stop-onset
    train=out[max(0,onset-96):onset,nodes]
    center=np.nanmean(train,axis=0)
    scale=np.maximum(np.nanstd(train,axis=0),.05)
    center=np.nan_to_num(center)
    scale=np.nan_to_num(scale,nan=1)
    noise=rng.normal(size=x.shape)*scale
    donor=np.nan_to_num(x[:,:1],nan=0)
    if kind=='copy':
        changed=(1-severity)*x+severity*(donor+0.01*noise)
    elif kind=='anticorrelated':
        sign=np.where(np.arange(len(nodes))%2, -1,1)[None,:,None]
        changed=(1-severity)*x+severity*(sign*donor+.01*noise)
    elif kind in ('common','transition'):
        common=rng.normal(size=(steps,1,x.shape[-1]))
        if kind=='transition':
            common=np.sin(np.linspace(0,np.pi,steps))[:,None,None]*np.ones((1,1,x.shape[-1]))
        changed=x+(3 if kind=='common' else 1.5)*severity*common*scale
    elif kind=='noise': changed=x+3*severity*noise
    elif kind=='decouple': changed=(1-severity)*x+severity*(center+noise)
    elif kind=='delay':
        changed=x.copy()
        delay=max(1,int(12*severity))
        for j in range(0,len(nodes),2): changed[:,j]=out[onset-delay:stop-delay,nodes[j]]
    elif kind=='drift':
        ramp=np.linspace(0,1,steps)[:,None,None]
        changed=x*(1+severity*ramp)+2*severity*ramp*scale
    elif kind=='flatline': changed=np.broadcast_to(center,x.shape).copy()
    elif kind=='dropout': changed=np.full_like(x,np.nan)
    elif kind=='mixed':
        changed=x.copy();half=len(nodes)//2
        changed[:,:half]=(1-severity)*x[:,:half]+severity*(donor+.01*noise[:,:half])
        changed[:,half:]=x[:,half:]+3*severity*noise[:,half:]
    elif kind=='marginal_preserving':
        changed=x.copy()
        for j in range(len(nodes)):
            for c in range(x.shape[-1]):
                valid=np.flatnonzero(mask[:,j,c]); changed[valid,j,c]=rng.permutation(x[valid,j,c])
    elif kind=='matched_covariance':
        # Match the untouched event's average correlation, marginal mean and
        # variance while changing its spectrum. With sufficient full-rank rows,
        # whitening/recoloring gives an exact finite-sample construction.
        changed=x.copy()
        m=len(nodes)
        for channel in range(x.shape[-1]):
            common=mask[:,:,channel].all(1)
            original=x[common,:,channel]
            if len(original)<3 or (np.std(original,axis=0)<1e-8).any():continue
            mean=original.mean(0);sd=original.std(0,ddof=1)
            z=(original-mean)/sd
            r=z.T@z/(len(z)-1)
            average=float((r.sum()-m)/(m*(m-1)))
            equicorrelation=(1-average)*np.eye(m)+average*np.ones((m,m))
            target=(1-severity)*r+severity*equicorrelation
            eig,vec=np.linalg.eigh(r);teig,tvec=np.linalg.eigh(target)
            if eig.min()>1e-7:
                transformed=z@((vec/np.sqrt(eig))@vec.T)@((tvec*np.sqrt(np.maximum(teig,0)))@tvec.T)
            else:
                # Rank-deficient short events draw from the target population
                # covariance, then restore sample margins. Their realized
                # sample correlation need not equal the population target.
                transformed=rng.multivariate_normal(np.zeros(m),target,size=len(z))
                transformed=(transformed-transformed.mean(0))/np.maximum(transformed.std(0,ddof=1),1e-8)
            changed[common,:,channel]=mean+transformed*sd
    else: raise ValueError(f'Unknown fault {kind}')
    if kind!='dropout': changed=np.where(mask,changed,np.nan)
    out[onset:stop,nodes]=changed
    return out
