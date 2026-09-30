"""E9. Denominators are fixed before proposals are drawn."""
from __future__ import annotations
import torch


def observation_edit_cost(original, replacements, edit_mask, eligible_mask, scale=1., rho=.5, c=3.):
    """Original [..., C,T], replacements [..., E,M,C,T]. Returns batch prefix."""
    if not 0 <= rho <= 1 or c <= 0:
        raise ValueError("Invalid edit-cost parameters.")
    if (edit_mask & ~eligible_mask).any():
        raise ValueError("Missingness needs a separate hypothesis, not a numeric edit cost.")
    k, n = edit_mask.sum((-2,-1)), eligible_mask.sum((-2,-1))
    if (k == 0).any() or (n == 0).any():
        raise ValueError("Nonempty edit and fixed eligible window required.")
    scale = torch.as_tensor(scale, dtype=original.dtype, device=original.device)
    if (scale <= 0).any() or not torch.isfinite(scale).all():
        raise ValueError("Positive frozen scales required.")
    delta = (replacements-original[..., None,None,:,:]).abs()/(c*scale)
    expanded = edit_mask[..., None,None,:,:].expand_as(replacements)
    if not torch.isfinite(delta[expanded]).all():
        raise ValueError("An observed edit has nonfinite magnitude.")
    magnitude = torch.where(expanded, delta.clamp(max=1), torch.zeros_like(delta))
    magnitude = (magnitude.sum((-2,-1))/k[...,None,None]).mean((-2,-1))
    return rho*k/n+(1-rho)*magnitude


def association_edit_cost(masked_edges, fixed_graph_edges):
    if masked_edges < 0 or fixed_graph_edges < 0 or masked_edges > fixed_graph_edges:
        raise ValueError("Invalid fixed graph edit count.")
    return masked_edges/max(fixed_graph_edges,1)
