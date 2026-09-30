"""Controlled corruption. Native process labels are never repurposed as fault truth."""
from __future__ import annotations
import copy,hashlib,json
import numpy as np

OBSERVATION_FAMILIES=['offset','drift','stuck','spike','noise','dropout','replay','scale','coordinated','delay']
EDGE_FAMILIES=['wrong_endpoint','wrong_lag','wrong_sign','unsupported','stale']


def inject_observation(x,seed,family=None,strength=None,duration=None):
    rng=np.random.default_rng(seed);out=x.copy();c,t=x.shape
    family=family or OBSERVATION_FAMILIES[seed%len(OBSERVATION_FAMILIES)]
    duration=int(duration or rng.choice([4,8,16]));strength=float(strength or rng.choice([.5,1.,2.,4.]))
    eligible=np.flatnonzero(np.isfinite(x[:,-duration:]).mean(-1)>.75)
    labels=np.zeros(c,dtype=bool)
    if not len(eligible):return out,labels,dict(family=family,seed=seed,status='no_eligible_sensor')
    channel=int(rng.choice(eligible));channels=[channel]
    if family in ('coordinated','common_mode'):
        count=min(len(eligible),max(2,c//8) if family=='coordinated' else len(eligible))
        channels=rng.choice(eligible,count,replace=False).tolist()
    sign=int(rng.choice([-1,1]));tail=slice(t-duration,t)
    for i in channels:
        if family in ('offset','coordinated','common_mode'):out[i,tail]+=sign*strength
        elif family=='drift':out[i,tail]+=sign*strength*np.linspace(0,1,duration)
        elif family=='stuck':out[i,tail]=x[i,t-duration-1]
        elif family=='spike':out[i,np.arange(t-duration,t,2)]+=sign*strength*2
        elif family=='noise':out[i,tail]+=rng.normal(0,strength,duration)
        elif family=='dropout':out[i,tail]=np.nan
        elif family=='replay':out[i,tail]=x[i,t-duration-8:t-8]
        elif family=='delay':
            lag=int(rng.integers(1,5));out[i,tail]=x[i,t-duration-lag:t-lag]
        elif family=='scale':out[i,tail]=(x[i,tail]+1)*(1+strength)-1
        else:raise ValueError(family)
        labels[i]=True
    return out,labels,dict(family=family,seed=seed,channels=channels,start=t-duration,stop=t,
        duration=duration,strength=strength,sign=sign,label_provenance='injected observation fault',status='injected')


def inject_association(graph,seed,family=None):
    """Paired attribute permutations preserve metadata marginals and degrees.

    The stale family is a parameter-version mismatch surrogate. It is reported
    separately from a genuine change in the physical generating process.
    """
    rng=np.random.default_rng(seed);out=copy.deepcopy(graph)
    labels=np.zeros(len(graph['edges']),dtype=bool)
    family=family or EDGE_FAMILIES[seed%len(EDGE_FAMILIES)]
    pairs=[];existing={(e['source'],e['target']) for e in graph['edges']}
    for i,a in enumerate(graph['edges']):
      for j in range(i+1,len(graph['edges'])):
        b=graph['edges'][j]
        if family in ('wrong_endpoint','unsupported'):
            valid=(a['source']!=b['source'] and a['target']!=b['target']
                and graph['groups'][a['source']]!=graph['groups'][b['target']]
                and graph['groups'][b['source']]!=graph['groups'][a['target']]
                and (a['source'],b['target']) not in existing
                and (b['source'],a['target']) not in existing)
            if family=='unsupported':
                affinity=np.asarray(graph['affinity'])
                valid=valid and affinity[b['target'],a['source']]<.5 and affinity[a['target'],b['source']]<.5
        elif family=='wrong_lag':valid=a['lag']!=b['lag']
        elif family=='wrong_sign':valid=a['sign']!=b['sign']
        elif family=='stale':valid=abs(a['magnitude']-b['magnitude'])>.02
        else:raise ValueError(family)
        if valid:pairs.append((i,j))
    if not pairs:return out,labels,dict(family=family,seed=seed,status='no_matched_pair')
    i,j=pairs[int(rng.integers(len(pairs)))];a=out['edges'][i];b=out['edges'][j]
    fields={'wrong_endpoint':['source'],'unsupported':['source'],'wrong_lag':['lag'],
            'wrong_sign':['sign'],'stale':['magnitude','intercept']}[family]
    originals=[copy.deepcopy(a),copy.deepcopy(b)]
    for field in fields:a[field],b[field]=b[field],a[field]
    labels[[i,j]]=True
    out['base_version']=graph['version'];out['version']=content_hash(out['edges'])[:16]
    return out,labels,dict(family=family,seed=seed,indices=[i,j],original=originals,
        modified=[copy.deepcopy(a),copy.deepcopy(b)],matched_fields=fields,
        label_provenance='injected association attribute fault',status='injected',
        interpretation='parameter-version mismatch surrogate' if family=='stale' else 'paired attribute permutation')


def content_hash(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
