"""E4 and E6--E11, with arbitrary batch prefixes and explicit support.

Loss axes end in [ensemble, replicate, provenance_group]. Production adds
[batch, candidate]. Missing groups are excluded only by an explicit fixed mask.
Unavailable predictions in eligible groups raise, never become zero losses.
"""
from __future__ import annotations
import torch


def _finite(*values):
    if not all(torch.isfinite(v).all().item() for v in values):
        raise ValueError("Nonfinite prediction/loss requires abstention.")


def normalized_empirical_crps(samples, observed, training_scale=1.):
    if samples.ndim < 1 or samples.shape[-1] < 1 or samples.shape[:-1] != observed.shape:
        raise ValueError("Expected observed.shape + [predictive_sample].")
    scale = torch.as_tensor(training_scale, dtype=samples.dtype, device=samples.device)
    _finite(samples, observed, scale)
    if (scale <= 0).any():
        raise ValueError("Training scale must be positive.")
    n = samples.shape[-1]
    ranks = torch.arange(1, n+1, dtype=samples.dtype, device=samples.device)
    pair_term = (samples.sort(-1).values * (2*ranks-n-1)).sum(-1) / n**2
    value = ((samples-observed.unsqueeze(-1)).abs().mean(-1)-pair_term)/scale
    tolerance = 1e-10 if samples.dtype == torch.float64 else 1e-5
    if (value < -tolerance).any():
        raise ArithmeticError("Materially negative CRPS.")
    return value.clamp_min(0)


def compute_paired_gains(before, after, weights, valid_groups=None):
    if before.ndim < 3 or before.shape != after.shape:
        raise ValueError("Matching [..., E, M, G] arrays required.")
    weights = torch.as_tensor(weights, dtype=before.dtype, device=before.device)
    if weights.shape[-1] != before.shape[-1]:
        raise ValueError("Weights must match groups.")
    if valid_groups is not None:
        valid = torch.as_tensor(valid_groups, device=before.device, dtype=torch.bool)
        if (weights.masked_select(~valid) != 0).any():
            raise ValueError("Ineligible groups cannot have nonzero weight.")
        expanded = valid[..., None, None, :].expand_as(before)
        _finite(before[expanded], after[expanded])
        if (before[expanded] < 0).any() or (after[expanded] < 0).any():
            raise ValueError("Loss must be nonnegative.")
        delta = torch.where(expanded, before-after, torch.zeros_like(before))
    else:
        _finite(before, after)
        if (before < 0).any() or (after < 0).any():
            raise ValueError("Loss must be nonnegative.")
        delta = before-after
    _finite(weights)
    if (weights < 0).any() or not torch.allclose(weights.sum(-1), torch.ones_like(weights.sum(-1))):
        raise ValueError("Weights must be nonnegative and sum to one.")
    return (delta*weights[..., None, None, :]).sum(-1)


def ensemble_instability(model_gains):
    if model_gains.shape[-1] < 2:
        raise ValueError("U is undefined for one member. Use an explicitly labeled ablation.")
    return model_gains.std(-1, unbiased=True)


def sampling_standard_error(paired_gains):
    e, m = paired_gains.shape[-2:]
    if m < 2:
        raise ValueError("At least two independent paired replicates required.")
    return (paired_gains.var(-1, unbiased=True).sum(-1)/(m*e**2)).sqrt()


def repair_score(before, after, weights, edit_cost, uncertainty_weight=1., edit_weight=.2,
                 valid_groups=None):
    paired = compute_paired_gains(before, after, weights, valid_groups)
    gains = paired.mean(-1)
    r = gains.mean(-1)
    u = ensemble_instability(gains)
    cost = torch.as_tensor(edit_cost, dtype=before.dtype, device=before.device)
    penalties = torch.as_tensor([uncertainty_weight, edit_weight], dtype=before.dtype, device=before.device)
    _finite(cost, penalties)
    if (cost < 0).any() or (penalties < 0).any():
        raise ValueError("Nonnegative finite costs and weights required.")
    return dict(score=r-uncertainty_weight*u-edit_weight*cost, mean_gain=r,
                model_instability=u, edit_cost=cost.expand_as(r),
                monte_carlo_standard_error=sampling_standard_error(paired), model_gains=gains)
