"""Context-only intact-block bootstrap and issuance-safe reference interfaces."""
from __future__ import annotations

import numpy as np
import torch

from .data import SensorData
from .models import calendar


class BlockBootstrap:
    def __init__(self, data: SensorData, context: int, horizon: int, device: str):
        self.context=context;self.horizon=horizon;self.device=device
        self.x=data.standardized
        self.candidates=data.issuance_indices(0,context,horizon,24)
        self.cal=calendar(data.timestamps)
        self.descriptors=np.asarray([self.describe(self.x[i-context:i]) for i in self.candidates])

    @staticmethod
    def describe(context: np.ndarray) -> np.ndarray:
        # Context means, last available row and coverage; no future measurements.
        with np.errstate(invalid='ignore'):
            mean=np.nanmean(context,axis=0)
        last=context[-1]
        return np.concatenate([np.nan_to_num(mean).ravel(),np.nan_to_num(last).ravel(),
                               np.isfinite(context).mean(0).ravel()])

    def sample(self, context: np.ndarray, known_calendar: np.ndarray,
               number: int, seed: int) -> torch.Tensor:
        descriptor=self.describe(context)
        distances=((self.descriptors-descriptor)**2).mean(1)
        distances+=.25*((self.cal[self.candidates,:2]-known_calendar[0,:2])**2).sum(1)
        nearest=np.argsort(distances,kind='stable')[:min(64,len(distances))]
        rng=np.random.default_rng(seed)
        donors=rng.choice(nearest,number,replace=True)
        return torch.as_tensor(np.stack([self.x[i:i+self.horizon] for i in self.candidates[donors]]),device=self.device)


def issue_reference(model: torch.nn.Module, data: SensorData, values: np.ndarray,
                    target_start: int, horizon: int, config: dict, device: str,
                    reference: str, bootstrap: BlockBootstrap, seed: int) -> torch.Tensor:
    if target_start < config['context'] or target_start+horizon > len(values):
        raise ValueError('Invalid context/target boundary')
    # The caller verifies split/episode containment; this API cannot receive
    # observed target values via conditioning.
    context=values[target_start-config['context']:target_start]
    known_calendar=calendar(data.timestamps[target_start:target_start+horizon])
    if reference=='bootstrap':
        return bootstrap.sample(context,known_calendar,config['generated_samples'],seed)
    torch.manual_seed(seed)
    return model.sample(torch.as_tensor(context,device=device)[None],
                        torch.as_tensor(known_calendar,device=device)[None],
                        config['generated_samples'],config['sampling_steps'],config['sample_chunk'])
