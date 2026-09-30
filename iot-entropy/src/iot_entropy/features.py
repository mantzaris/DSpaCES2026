"""Batched feature scans and shared-sample reference scoring."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .entropy import trajectory_features
from .graphs import graph_groups


@dataclass
class Family:
    window: int
    nodes: torch.Tensor
    channels: int
    offset: int


@dataclass
class Extracted:
    values: torch.Tensor
    correlations: list[torch.Tensor]
    eligible: torch.Tensor
    flatline: torch.Tensor
    count: torch.Tensor
    raw: list[torch.Tensor]


class Scan:
    def __init__(self, adjacency: np.ndarray, coordinates: np.ndarray, channels: list[str],
                 config: dict, device: str):
        self.device=device;self.shrinkage=config['shrinkage'];self.channels=channels
        groups=graph_groups(adjacency,coordinates,config['group_sizes'],config['maximum_group_centers'])
        self.records=[];self.families=[];offset=0
        for window in config['windows']:
            for size,nodes in groups.items():
                if window<2*size: continue
                self.families.append(Family(window,torch.as_tensor(nodes,device=device),len(channels),offset))
                for group in nodes:
                    for channel,name in enumerate(channels):
                        self.records.append({'index':offset,'nodes':group.tolist(),'size':size,
                                             'window':window,'lag':window//4,'channel':channel,'channel_name':name})
                        offset+=1
        self.groups=[record['nodes'] for record in self.records]

    def extract(self, samples: torch.Tensor) -> Extracted:
        # samples: B x T x N x C; preserve channel units by separate scans.
        if samples.ndim==3:samples=samples[None]
        values=[];matrices=[];valid=[];flatline=[];count=[];raw=[]
        for family in self.families:
            selected=samples[:,:,family.nodes,:].permute(0,2,4,1,3)
            batch,groups,channels,time,size=selected.shape
            selected=selected.reshape(batch,groups*channels,time,size)
            features,current,_=trajectory_features(selected,family.window,family.window//4,self.shrinkage)
            values.append(features);matrices.append(current.correlation)
            valid.append(torch.isfinite(features).all(-1));flatline.append(current.flatline)
            count.append(current.count);raw.append(selected[:,:,-family.window:,:])
        return Extracted(torch.cat(values,1),matrices,torch.cat(valid,1),
                         torch.cat(flatline,1),torch.cat(count,1),raw)


def robust_location_scale(samples: torch.Tensor, floor: torch.Tensor | float) -> tuple[torch.Tensor,torch.Tensor]:
    center=torch.nanmedian(samples,dim=0).values
    mad=torch.nanmedian((samples-center).abs(),dim=0).values
    return center,1.4826*mad+floor


def score_features(observed: Extracted, generated: Extracted, floor: torch.Tensor) -> tuple[dict[str,torch.Tensor],dict]:
    center,scale=robust_location_scale(generated.values,floor)
    standardized=(observed.values[0]-center)/scale
    enough=torch.isfinite(generated.values).sum(0)>=max(4,int(.8*len(generated.values)))
    standardized=standardized.masked_fill(~enough,float('nan'))
    def maximum(x: torch.Tensor) -> torch.Tensor:
        valid=torch.isfinite(x)
        answer=x.nan_to_num(nan=-float('inf')).max(-1).values
        return answer.masked_fill(~valid.any(-1),float('nan'))
    entropy=maximum(standardized[:,:2].abs())
    synchronization=maximum(standardized[:,2:].abs())
    scores={'entropy':entropy,'synchronization':synchronization,
            'combined':maximum(standardized.abs()),'level':standardized[:,0].abs(),
            'higher':maximum(standardized[:,:2].clamp_min(0)),
            'lower':maximum((-standardized[:,:2]).clamp_min(0))}
    for name,start in [('signed_correlation',2),('absolute_correlation',4),('disagreement',6),('concentration',8)]:
        scores[name]=maximum(standardized[:,start:start+2].abs())
    matrix_scores=[];raw_scores=[];matrix_centers=[]
    for observed_r,reference_r,observed_raw,reference_raw in zip(observed.correlations,generated.correlations,observed.raw,generated.raw):
        matrix_center=torch.nanmean(reference_r,dim=0)
        sample_dist=torch.linalg.vector_norm(reference_r-matrix_center,dim=(-2,-1))
        actual_dist=torch.linalg.vector_norm(observed_r[0]-matrix_center,dim=(-2,-1))
        location,spread=robust_location_scale(sample_dist,.01)
        matrix_scores.append((actual_dist-location).abs()/spread)
        matrix_centers.append(matrix_center)
        prediction_center,prediction_scale=robust_location_scale(reference_raw,.05)
        residual=(observed_raw[0]-prediction_center).abs()/prediction_scale
        raw_scores.append(torch.nanmean(residual,dim=(-2,-1)))
    scores['matrix']=torch.cat(matrix_scores)
    scores['raw']=torch.cat(raw_scores).masked_fill(~observed.eligible[0],float('nan'))
    scores['entropy_raw']=maximum(torch.stack((scores['entropy'],scores['raw']),-1))
    quality=torch.where(observed.flatline[0],torch.full_like(entropy,1e6),torch.zeros_like(entropy))
    # Hybrid quality includes flatline; missingness is a separate data-quality
    # stream rather than assigning missing entropy a numerical score.
    scores['quality_hybrid']=maximum(torch.stack((scores['entropy_raw'],quality),-1))
    diagnostic={'observed':observed.values[0],'reference_center':center,'reference_scale':scale,
                'reference_low':torch.nanquantile(generated.values,.05,dim=0),
                'reference_high':torch.nanquantile(generated.values,.95,dim=0),
                'eligible':observed.eligible[0],'flatline':observed.flatline[0],
                'common_rows':observed.count[0],'matrix_center':matrix_centers,
                'reference_valid_fraction':enough.float().mean()}
    return scores,diagnostic


def prediction_fidelity(observed: torch.Tensor, samples: torch.Tensor) -> dict:
    mask=torch.isfinite(observed)
    samples=samples.masked_fill(~mask[None],float('nan'))
    low,high=torch.nanquantile(samples,torch.tensor([.05,.95],device=samples.device),dim=0)
    valid=mask&torch.isfinite(low)&torch.isfinite(high)
    coverage=((observed>=low)&(observed<=high))[valid].float().mean()
    width=(high-low)[valid].mean()
    # Energy score with independent pairs from the same empirical ensemble;
    # normalize Euclidean norm by sqrt(number of observed dimensions).
    dimensions=mask.sum().clamp_min(1).sqrt()
    clean=torch.nan_to_num(samples)
    observation=torch.nan_to_num(observed)
    first=torch.linalg.vector_norm((clean-observation).flatten(1),dim=-1).mean()/dimensions
    second=torch.linalg.vector_norm((clean[:len(clean)//2]-clean[len(clean)//2:2*(len(clean)//2)]).flatten(1),dim=-1).mean()/dimensions
    return {'coverage90':float(coverage),'width90':float(width),'energy_score':float(first-.5*second),
            'observed_fraction':float(mask.float().mean())}
