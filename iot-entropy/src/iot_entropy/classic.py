"""Independently calibrated finite-memory CUSUM and GDN error scores."""
from __future__ import annotations

import numpy as np
import torch

from .entropy import window_features
from .features import Scan


@torch.no_grad()
def gdn_residuals(model: torch.nn.Module, history_and_target: np.ndarray, context: int,
                 device: str) -> torch.Tensor:
    length=len(history_and_target)
    indices=np.arange(length-4,length)
    history=np.stack([history_and_target[t-context:t] for t in indices])
    predicted=model(torch.as_tensor(history,device=device))
    target=torch.as_tensor(history_and_target[indices],device=device)
    return (predicted-target).abs()


@torch.no_grad()
def classic_scores(block: torch.Tensor, scan: Scan, center: torch.Tensor,
                   scale: torch.Tensor, gdn_errors: torch.Tensor,
                   gdn_center: torch.Tensor, gdn_scale: torch.Tensor) -> dict[str,torch.Tensor]:
    cusum=[];gdn=[]
    node_errors=((gdn_errors-gdn_center)/gdn_scale).mean(0).clamp_min(0)
    for family in scan.families:
        selected=block[:,family.nodes,:].permute(1,3,0,2)
        groups,channels,time,size=selected.shape
        selected=selected.reshape(groups*channels,time,size)
        offset=family.offset;stop=offset+groups*channels
        indices=torch.tensor([2,6],device=block.device)
        middle=center[offset:stop][:,indices];spread=scale[offset:stop][:,indices]
        positive=torch.zeros_like(middle);negative=positive.clone()
        # At most four trailing measurements, restart at the same relative
        # historical point for every calibrated issuance. No lookahead.
        for lag in reversed(range(min(4,(time-family.window)//12+1))):
            end=time-lag*12
            result=window_features(selected[:,end-family.window:end,:],scan.shrinkage)
            values=result.values[:,[1,3]]
            z=(values-middle)/spread
            valid=torch.isfinite(z)
            positive=torch.where(valid,(positive+z-.5).clamp_min(0),positive)
            negative=torch.where(valid,(negative-z-.5).clamp_min(0),negative)
        scores=torch.maximum(positive,negative).max(-1).values
        scores=scores.masked_fill(~result.valid,float('nan'))
        cusum.append(scores)
        group_errors=node_errors[family.nodes].permute(0,2,1).reshape(groups*channels,size)
        errors=group_errors.nan_to_num(nan=-float('inf')).max(-1).values
        errors=errors.masked_fill(~result.valid,float('nan'))
        gdn.append(errors)
    return {'cusum':torch.cat(cusum),'gdn':torch.cat(gdn)}
