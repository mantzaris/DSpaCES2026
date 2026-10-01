"""Leakage-safe graph context and a genuinely invertible conditional neural flow.

E1 evaluates a block density. E2 inversely maps Gaussian draws to trajectories.
Affine neural coupling is used deliberately, without an extra spline dependency.
"""
from dataclasses import dataclass
import math
from typing import Optional

import numpy as np
import torch
from torch import nn


@dataclass
class GraphInputs:
    sequence: torch.Tensor          # [B, 1+K, L, 2], value and availability
    query: torch.Tensor             # [B]
    neighbors: torch.Tensor         # [B,K], channel identity or padding C
    attributes: torch.Tensor        # [B,K,3], lag, sign, training correlation
    support: torch.Tensor           # [B,K], usable context source

    def select(self, indices):
        return GraphInputs(*(getattr(self, key)[indices] for key in self.__dataclass_fields__))

    def to(self, device):
        return GraphInputs(*(getattr(self, key).to(device) for key in self.__dataclass_fields__))


def canonicalize_known_copies(values, identities):
    """Remove identical known measurement copies before masks or messages."""
    if len(identities) != values.shape[1]:
        raise ValueError('One provenance identity is required per channel')
    first, retained = {}, []
    for index, identity in enumerate(identities):
        if identity in first:
            left, right = values[:, first[identity]], values[:, index]
            if not ((left == right) | (torch.isnan(left) & torch.isnan(right))).all():
                raise ValueError('Conflicting known measurement copies')
        else:
            first[identity] = index; retained.append(index)
    return values[:, retained]


def graph_neighbors(graph, maximum=3):
    """One representative incoming edge per supporting physical source."""
    channels = len(graph['groups'])
    neighbors = np.full((channels, maximum), channels, dtype=np.int64)
    attributes = np.zeros((channels, maximum, 3), dtype=np.float32)
    for target in range(channels):
        used = {graph['groups'][target]}
        candidates = sorted((e for e in graph['edges'] if e['target'] == target),
                            key=lambda e: (-e['validation_gain'], e['source']))
        slot = 0
        for edge in candidates:
            source = edge['source']; group = graph['groups'][source]
            if group in used:
                continue
            used.add(group)
            neighbors[target, slot] = source
            attributes[target, slot] = [edge['lag'], edge['sign'], edge['training_abs_correlation']]
            slot += 1
            if slot == maximum:
                break
    return neighbors, attributes


def build_context(values: torch.Tensor, query: torch.Tensor, graph, context_length=56,
                  target_length=8, mode='graph', observation_ids=None) -> GraphInputs:
    """Remove the entire target source block BEFORE computing any feature.

    values [B,C,T] contain NaNs for missing data. Supporting channels are allowed
    observations by the decision time, and are not claimed to be withheld witnesses.
    """
    if observation_ids is not None:
        values = canonicalize_known_copies(values, observation_ids)
    batch, channels, length = values.shape
    if channels != len(graph['groups']) or query.shape != (batch,):
        raise ValueError('Graph/channel/query dimensions differ')
    if context_length + 3 > length or target_length >= context_length:
        raise ValueError('Context must fit lagged observations and contain earlier history')
    groups = {name: i for i, name in enumerate(sorted(set(graph['groups'])))}
    group_id = torch.tensor([groups[name] for name in graph['groups']], device=values.device)
    visible = torch.isfinite(values)
    same_source = group_id[None] == group_id[query, None]
    visible = visible.clone()
    visible[:, :, -target_length:] &= ~same_source[:, :, None]
    masked = torch.where(visible, values, torch.zeros_like(values))
    # No temporal statistic or neural operation has seen the removed values.
    neighbors_np, attributes_np = graph_neighbors(graph)
    neighbors = torch.as_tensor(neighbors_np, device=values.device)[query]
    attributes = torch.as_tensor(attributes_np, device=values.device, dtype=values.dtype)[query]
    if mode == 'own_history':
        neighbors = torch.full_like(neighbors, channels)
        attributes = torch.zeros_like(attributes)
    elif mode != 'graph':
        raise ValueError('Unknown context mode')
    rows = torch.arange(batch, device=values.device)
    sequence = [torch.stack([masked[rows, query, -context_length:],
                              visible[rows, query, -context_length:].to(values.dtype)], -1)]
    support = []
    for slot in range(neighbors.shape[1]):
        source = neighbors[:, slot]
        valid = source < channels
        times = torch.arange(length-context_length, length, device=values.device)[None] - attributes[:, slot, 0].long()[:, None]
        observed = visible[rows[:, None], source.clamp_max(channels-1)[:, None], times] & valid[:, None]
        data = masked[rows[:, None], source.clamp_max(channels-1)[:, None], times]
        sequence.append(torch.stack([torch.where(observed, data, torch.zeros_like(data)), observed.to(values.dtype)], -1))
        support.append(observed.any(-1))
    return GraphInputs(torch.stack(sequence, 1), query, neighbors, attributes, torch.stack(support, 1))


class GraphConditioner(nn.Module):
    def __init__(self, channels, width):
        super().__init__()
        self.temporal = nn.GRU(2, width, batch_first=True)
        self.sensor = nn.Embedding(channels + 1, min(16, width), padding_idx=channels)
        embedding = self.sensor.embedding_dim
        self.message = nn.Sequential(nn.Linear(width + embedding + 3, width), nn.SiLU(), nn.Linear(width, width))
        self.output = nn.Sequential(nn.Linear(2 * width + embedding + 1, width), nn.SiLU(), nn.Linear(width, width))

    def forward(self, context: GraphInputs):
        batch, nodes, length, _ = context.sequence.shape
        _, state = self.temporal(context.sequence.reshape(batch * nodes, length, 2))
        temporal = state[-1].reshape(batch, nodes, -1)
        attributes = context.attributes.clone(); attributes[..., 0] /= 3.
        messages = self.message(torch.cat([temporal[:, 1:], self.sensor(context.neighbors), attributes], -1))
        weights = context.support.to(messages.dtype)
        pooled = (messages * weights[..., None]).sum(1) / weights.sum(1).clamp_min(1)[:, None]
        return self.output(torch.cat([temporal[:, 0], pooled, self.sensor(context.query), weights.mean(1, keepdim=True)], -1))


class AffineCoupling(nn.Module):
    def __init__(self, dimension, context_width, hidden_width, parity):
        super().__init__()
        mask = ((torch.arange(dimension) + parity) % 2).float()
        self.register_buffer('mask', mask)
        self.network = nn.Sequential(nn.Linear(dimension + context_width, hidden_width), nn.SiLU(),
                                     nn.Linear(hidden_width, hidden_width), nn.SiLU(), nn.Linear(hidden_width, 2 * dimension))
        nn.init.zeros_(self.network[-1].weight); nn.init.zeros_(self.network[-1].bias)

    def forward(self, value, context, inverse=False):
        fixed = value * self.mask
        shift, raw_scale = self.network(torch.cat([fixed, context], -1)).chunk(2, -1)
        scale = 1.5 * torch.tanh(raw_scale / 1.5)
        scale, shift = scale * (1-self.mask), shift * (1-self.mask)
        if inverse:
            result = fixed + (1-self.mask) * (value * scale.exp() + shift)
            determinant = scale.sum(-1)
        else:
            result = fixed + (1-self.mask) * ((value-shift) * (-scale).exp())
            determinant = -scale.sum(-1)
        return result, determinant


class GraphFlow(nn.Module):
    def __init__(self, channels, dimension=8, width=32, layers=4):
        super().__init__()
        self.configuration = dict(channels=channels, dimension=dimension, width=width, layers=layers)
        self.dimension = dimension
        self.conditioner = GraphConditioner(channels, width)
        self.location_scale = nn.Linear(width, 2 * dimension)
        nn.init.zeros_(self.location_scale.weight); nn.init.zeros_(self.location_scale.bias)
        self.couplings = nn.ModuleList([AffineCoupling(dimension, width, width, i % 2) for i in range(layers)])

    def encode(self, context: GraphInputs):
        return self.conditioner(context)

    def transform(self, values, encoded, inverse=False):
        mean, raw_scale = self.location_scale(encoded).chunk(2, -1)
        log_scale = 4 * torch.tanh(raw_scale / 4)
        result = values
        determinant = torch.zeros_like(values[..., 0])
        if inverse:
            for coupling in reversed(self.couplings):
                result, change = coupling(result, encoded, inverse=True); determinant += change
            result = result * log_scale.exp() + mean
            determinant += log_scale.sum(-1)
        else:
            result = (result-mean) * (-log_scale).exp()
            determinant -= log_scale.sum(-1)
            for coupling in self.couplings:
                result, change = coupling(result, encoded); determinant += change
        return result, determinant

    def log_prob(self, target_values, context, graph=None, masks=None):
        """E1. Context is GraphInputs or a precomputed context embedding."""
        if not torch.isfinite(target_values).all():
            raise ValueError('Flow targets must be complete and finite; missing context uses masks')
        encoded = self.encode(context) if isinstance(context, GraphInputs) else context
        latent, determinant = self.transform(target_values, encoded)
        return -.5 * (latent.square() + math.log(2 * math.pi)).sum(-1) + determinant

    def sample(self, context, graph=None, masks=None, sample_count=128, generator=None,
               latent: Optional[torch.Tensor] = None, chunk=128):
        """E2. Actual neural inverse generation, [B,M,D], with fixed latent draws.

        Drawing latent values before chunking keeps chunk boundaries from changing
        random-number assignment. Context never incorporates the tested target.
        """
        encoded = self.encode(context) if isinstance(context, GraphInputs) else context
        if latent is None:
            latent = torch.randn((len(encoded), sample_count, self.dimension), device=encoded.device,
                                 dtype=encoded.dtype, generator=generator)
        if latent.shape != (len(encoded), sample_count, self.dimension):
            raise ValueError('Latent draw dimensions differ')
        chunks = []
        for first in range(0, sample_count, chunk):
            epsilon = latent[:, first:first+chunk]
            condition = encoded[:, None].expand(-1, epsilon.shape[1], -1)
            generated, _ = self.transform(epsilon, condition, inverse=True)
            chunks.append(generated)
        return torch.cat(chunks, dim=1)
