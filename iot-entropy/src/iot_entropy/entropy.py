"""PSD common-case correlations and spectrum entropy (paper equations 1--3)."""
from __future__ import annotations

import math
from dataclasses import dataclass

import torch


@dataclass
class WindowFeatures:
    values: torch.Tensor  # H, C, Cabs, D, P
    correlation: torch.Tensor
    valid: torch.Tensor
    flatline: torch.Tensor
    count: torch.Tensor
    variance: torch.Tensor


def entropy_from_correlation(correlation: torch.Tensor, shrinkage: float = 0.05) -> torch.Tensor:
    """Normalized eigenvalue Shannon entropy; reject materially non-PSD input."""
    m = correlation.shape[-1]
    if m < 2 or not 0 <= shrinkage <= 1:
        raise ValueError('Require m >= 2 and shrinkage in [0, 1]')
    matrix = (correlation + correlation.transpose(-1, -2)) / 2
    eigenvalues = torch.linalg.eigvalsh(matrix)
    tolerance = 64 * torch.finfo(matrix.dtype).eps * m
    if bool((eigenvalues < -tolerance).any()):
        raise ValueError('Materially non-PSD correlation matrix')
    eigenvalues = eigenvalues.clamp_min(0)
    eigenvalues = (1 - shrinkage) * eigenvalues + shrinkage
    trace = eigenvalues.sum(-1, keepdim=True)
    if bool((trace <= 0).any()):
        raise ValueError('Nonpositive trace')
    p = eigenvalues / trace
    return -(torch.special.xlogy(p, p)).sum(-1) / math.log(m)


def window_features(x: torch.Tensor, shrinkage: float = 0.05,
                    minimum_coverage: float = 0.8, variance_floor: float = 1e-8) -> WindowFeatures:
    """x has shape (..., time, sensors), with NaN for unavailable observations.

    D averages squared differences of within-window sample-standardized signals
    over observed time rows and unordered pairs: D=2(n-1)/n*(1-C).
    Undefined features are NaN; a safe identity is used ONLY inside the solver.
    """
    n_time, m = x.shape[-2:]
    common = torch.isfinite(x).all(-1)
    count = common.sum(-1)
    safe = torch.where(common.unsqueeze(-1), x, torch.zeros_like(x))
    mean = safe.sum(-2) / count.clamp_min(1).unsqueeze(-1)
    centered = torch.where(common.unsqueeze(-1), x - mean.unsqueeze(-2), torch.zeros_like(x))
    denominator = (count - 1).clamp_min(1)
    variance = centered.square().sum(-2) / denominator.unsqueeze(-1)
    flatline = (variance <= variance_floor).any(-1) & (count >= 2)
    valid = (count >= max(2 * m, math.ceil(minimum_coverage * n_time))) & ~flatline
    standardized = centered / variance.clamp_min(variance_floor).sqrt().unsqueeze(-2)
    # Neural-network TF32 settings must not silently reduce Gram precision.
    previous_tf32 = torch.backends.cuda.matmul.allow_tf32
    try:
        torch.backends.cuda.matmul.allow_tf32 = False
        correlation = standardized.transpose(-1, -2) @ standardized
    finally:
        torch.backends.cuda.matmul.allow_tf32 = previous_tf32
    correlation = correlation / denominator.unsqueeze(-1).unsqueeze(-1)
    eye = torch.eye(m, dtype=x.dtype, device=x.device)
    correlation = torch.where(valid[..., None, None], correlation, eye)
    correlation = (correlation + correlation.transpose(-1, -2)) / 2
    entropy = entropy_from_correlation(correlation, shrinkage)
    signed = (correlation.sum((-1, -2)) - m) / (m * (m - 1))
    absolute = (correlation.abs().sum((-1, -2)) - m) / (m * (m - 1))
    disagreement = 2 * (count - 1) / count.clamp_min(1) * (1 - signed)
    concentration = torch.linalg.eigvalsh(correlation)[..., -1] / m
    values = torch.stack((entropy, signed, absolute, disagreement, concentration), -1)
    values = values.masked_fill(~valid[..., None], float('nan'))
    correlation = correlation.masked_fill(~valid[..., None, None], float('nan'))
    return WindowFeatures(values, correlation, valid, flatline, count, variance)


def trajectory_features(block: torch.Tensor, window: int, lag: int,
                        shrinkage: float = 0.05) -> tuple[torch.Tensor, WindowFeatures, WindowFeatures]:
    if block.shape[-2] < window + lag or lag < 1:
        raise ValueError('Target block must contain both lagged windows')
    past = window_features(block[..., -window-lag:-lag, :], shrinkage)
    current = window_features(block[..., -window:, :], shrinkage)
    levels, changes = current.values, current.values - past.values
    return torch.stack((levels, changes), -1).flatten(-2), current, past


def equicorrelation_entropy(m: int, rho: torch.Tensor, shrinkage: float = 0.0) -> torch.Tensor:
    r = (1 - shrinkage) * rho
    large = (1 + (m - 1) * r) / m
    small = (1 - r) / m
    return -(torch.special.xlogy(large, large) + (m - 1) * torch.special.xlogy(small, small)) / math.log(m)


def equicorrelation_derivative(m: int, rho: torch.Tensor, shrinkage: float = 0.0) -> torch.Tensor:
    r = (1 - shrinkage) * rho
    return (1 - shrinkage) * (m - 1) / (m * math.log(m)) * torch.log((1 - r) / (1 + (m - 1) * r))
