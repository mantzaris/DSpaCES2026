"""Reference-independent feature families and development-fixed localization."""
from __future__ import annotations

import math

import numpy as np
import torch

from .features import Scan, robust_location_scale, score_features, summarize_reference
from .entropy import window_features
from .localization import participation
from .temporal import FEATURES, trajectory


MAIN = ['S','PE','SE','T','ST','SB','TB','B','BST']
EXTRA = ['ACF','difference_variance','variance','trend','predictive_mean','CUSUM','raw']


def maximum(x: torch.Tensor, dim: int = -1) -> torch.Tensor:
    finite = torch.isfinite(x)
    answer = x.masked_fill(~finite, -float('inf')).amax(dim)
    return answer.masked_fill(~finite.any(dim), float('nan'))


def combine(*xs: torch.Tensor) -> torch.Tensor:
    return maximum(torch.stack(xs,-1))


def extract(samples: torch.Tensor, scan: Scan, config: dict, include_temporal: bool = True) -> dict:
    if samples.ndim==3: samples=samples[None]
    spatial=scan.extract(samples)
    changes=[]
    for f,current in zip(scan.families,spatial.correlations):
        chosen=samples[:,:,f.nodes,:].permute(0,2,4,1,3)
        b,g,c,t,m=chosen.shape; chosen=chosen.reshape(b,g*c,t,m)
        d=f.window//4
        previous=window_features(chosen[:,:,-f.window-d:-d],scan.shrinkage).correlation
        changes.append(current-previous)
    result={'spatial':spatial,'matrix_changes':changes}
    if include_temporal:
        result['temporal']={w:trajectory(samples,w,config) for w in config['windows']}
    return result


def summaries(generated: dict, floors: dict, config: dict) -> dict:
    temporal = {}
    for w, item in generated['temporal'].items():
        x = item['u']
        center,scale = robust_location_scale(x,floors['temporal'][w])
        enough = torch.isfinite(x).sum(0) >= math.ceil(config['reference_valid_fraction']*len(x))
        temporal[w] = {'center':center,'scale':scale,'enough':enough,
                       'low':torch.nanquantile(x,.05,dim=0),'high':torch.nanquantile(x,.95,dim=0)}
    matrices=[]
    for changes in generated['matrix_changes']:
        middle=torch.nanmean(changes,dim=0)
        distances=torch.linalg.vector_norm(changes-middle,dim=(-2,-1))
        center,scale=robust_location_scale(distances,.01)
        enough=torch.isfinite(distances).sum(0)>=math.ceil(config['reference_valid_fraction']*len(changes))
        matrices.append((middle,center,scale,enough))
    return {'spatial':summarize_reference(generated['spatial'],floors['spatial']),
            'temporal':temporal,'matrix_changes':matrices}


def aggregate(sensor_scores: torch.Tensor, nodes: torch.Tensor, fraction: float,
              minimum_coverage: float) -> torch.Tensor:
    # N,C -> G,C; take fixed ceil(fraction*m) top sensors where enough exist.
    x = sensor_scores[nodes].transpose(1,2)
    valid = torch.isfinite(x)
    m = nodes.shape[1]; k = math.ceil(fraction*m)
    selected = x.masked_fill(~valid,-float('inf')).topk(k,dim=-1).values
    answer = selected.mean(-1)
    enough = valid.sum(-1) >= max(k,math.ceil(minimum_coverage*m))
    return answer.masked_fill(~enough,float('nan')).flatten()


def score(observed: dict, generated: dict, summary: dict, scan: Scan,
          floors: dict, config: dict, fraction: float) -> dict:
    spatial, spatial_evidence = score_features(observed['spatial'],generated['spatial'],
                                               floors['spatial'],summary['spatial'])
    sensors = {}; signed = {}
    for w, item in observed['temporal'].items():
        ref = summary['temporal'][w]
        z = ((item['u'][0]-ref['center'])/ref['scale']).masked_fill(~ref['enough'],float('nan'))
        a = maximum(z.abs()).masked_fill(~torch.isfinite(z).all(-1),float('nan'))
        sensors[w] = {'PE':a[...,0], 'SE':a[...,1],
            'T':maximum(a[...,:2]), 'TB':maximum(a[...,2:]),
            'ACF':maximum(a[...,2:5]), 'difference_variance':a[...,5],
            'variance':a[...,6], 'trend':a[...,7], 'predictive_mean':a[...,8], 'CUSUM':a[...,9]}
        signed[w] = z
    temporal_names=list(sensors[config['windows'][0]])
    matrices={w:torch.stack([sensors[w][name] for name in temporal_names],-1) for w in config['windows']}
    batches=[]
    for f in scan.families:
        # G,m,C,feature -> G,C,feature,m, sharing the sorting/support kernel.
        x=matrices[f.window][f.nodes].permute(0,2,3,1)
        valid=torch.isfinite(x);m=f.nodes.shape[1];k=math.ceil(fraction*m)
        selected=x.masked_fill(~valid,-float('inf')).topk(k,dim=-1).values.mean(-1)
        enough=valid.sum(-1)>=max(k,math.ceil(config['minimum_sensor_coverage']*m))
        batches.append(selected.masked_fill(~enough,float('nan')).flatten(0,1))
    all_groups=torch.cat(batches,0)
    group_temporal={name:all_groups[:,j] for j,name in enumerate(temporal_names)}
    spatial_z=((observed['spatial'].values[0]-summary['spatial'].center)/summary['spatial'].scale)
    spatial_z=spatial_z.masked_fill(~summary['spatial'].enough,float('nan')).reshape(-1,5,2)
    pair_scores=maximum(spatial_z.abs()).masked_fill(~torch.isfinite(spatial_z).all(-1),float('nan'))
    matrix_scores=[]
    for actual,(middle,center,scale,enough) in zip(observed['matrix_changes'],summary['matrix_changes']):
        distance=torch.linalg.vector_norm(actual[0]-middle,dim=(-2,-1))
        matrix_scores.append(((distance-center).abs()/scale).masked_fill(~enough,float('nan')))
    matrix_change=torch.cat(matrix_scores)
    result = {'S':pair_scores[:,0], 'SB':combine(maximum(pair_scores[:,1:]),spatial['matrix'],matrix_change),
              'raw':spatial['raw'], **group_temporal}
    result['ST'] = combine(result['S'],result['T'])
    result['B'] = combine(result['SB'],result['TB'])
    result['BST'] = combine(result['B'],result['ST'])
    common = torch.stack([torch.isfinite(result[k]) for k in ['S','PE','SE','SB','TB']]).all(0)
    for name in MAIN:
        result['common/'+name] = result[name].masked_fill(~common,float('nan'))
    direct = {}
    for name in ['PE','SE','T','TB']+EXTRA[:-1]:
        direct[name] = maximum(torch.stack([maximum(sensors[w][name],-1)
                                          for w in config['windows']],-1))
    direct.update({'ST':direct['T'],'B':direct['TB'],'BST':combine(direct['T'],direct['TB'])})
    direct['S'] = direct['T']; direct['SB'] = direct['TB']; direct['raw'] = direct['TB']
    # Restrict sensor rankings to the same common group/window/channel units.
    common_sensor={w:torch.zeros_like(sensors[w]['T'],dtype=torch.int32) for w in config['windows']}
    for f in scan.families:
        g,m=f.nodes.shape; c=f.channels
        permitted=common[f.offset:f.offset+g*c].reshape(g,c)
        contribution=permitted[:,None,:].expand(g,m,c).reshape(g*m,c).int()
        common_sensor[f.window].index_add_(0,f.nodes.flatten(),contribution)
    for name in ['PE','SE','T','TB']:
        direct['common/'+name]=maximum(torch.stack([maximum(sensors[w][name].masked_fill(
            common_sensor[w]==0,float('nan')),-1) for w in config['windows']],-1))
    direct.update({'common/ST':direct['common/T'],'common/B':direct['common/TB'],
                   'common/BST':combine(direct['common/T'],direct['common/TB']),
                   'common/S':direct['common/T'],'common/SB':direct['common/TB']})
    return {'groups':result,'direct':direct,'signed':signed,'spatial_evidence':spatial_evidence,
            'common':common}


def normalized_ranks(values: np.ndarray) -> np.ndarray:
    valid = np.isfinite(values)
    if not valid.any():
        return np.zeros_like(values)
    # Equal measurements receive equal percentiles; unavailable values score 0.
    from scipy.stats import rankdata
    result = np.zeros_like(values)
    result[valid] = rankdata(values[valid],method='average')/valid.sum()
    return result


def summarize_scores(scored: dict, scan: Scan, nodes: int, top: int = 24) -> tuple:
    names = MAIN+EXTRA+['common/'+k for k in MAIN]
    # One transfer and a batched linear participation calculation replace
    # thousands of Python group loops. The weighting definition is unchanged.
    group_array=torch.stack([scored['groups'][k] for k in names]).detach().cpu().numpy()
    if not hasattr(scan,'_participation_weights'):
        weights=np.zeros((len(scan.groups),nodes),dtype=np.float64)
        for j,group in enumerate(scan.groups): weights[j,group]=1/len(group)
        scan._participation_weights=weights
    weights=scan._participation_weights
    valid=np.isfinite(group_array)
    denominator=valid.astype(np.float64)@weights
    numerator=np.where(valid,group_array,0).astype(np.float64)@weights
    all_part=np.divide(numerator,denominator,out=np.full_like(numerator,np.nan),where=denominator>0)
    maxima=[]; availability=[]; rankings=[]
    for index,key in enumerate(names):
        scores = group_array[index]
        base = key.split('/')[-1]
        direct = scored['direct'].get(key,scored['direct'][base]).detach().cpu().numpy().copy()
        part=all_part[index]
        combined = (normalized_ranks(part)+normalized_ranks(direct))/2
        arrays=[part,direct,combined]
        ranks = [np.argsort(-np.nan_to_num(a,nan=-np.inf),kind='stable')[:top] for a in arrays]
        maxima.append(float(np.max(np.where(np.isfinite(scores),scores,-np.inf))))
        availability.append(np.isfinite(scores).mean())
        rankings.append(ranks)
    return names,np.asarray(maxima),np.asarray(availability),np.asarray(rankings,dtype=np.int16)


def primary_localization(name: str) -> int:
    name = name.split('/')[-1]
    if name in ['S','SB','raw','GDN']:
        return 0
    if name in ['ST','B','BST']:
        return 2
    return 1
