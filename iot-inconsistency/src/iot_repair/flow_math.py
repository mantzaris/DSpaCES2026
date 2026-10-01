"""Normalized corruption channels and likelihood/repair equations E4--E12.

Tensor axes are batch B, ensemble E, draws M and target coordinates D.
Density arithmetic is float64. Database and presentation code stay separate.
"""
from dataclasses import dataclass
import math
from typing import Dict

import numpy as np
import torch


@dataclass
class LikelihoodEvidence:
    log_normal: torch.Tensor
    log_fault: torch.Tensor
    ratio: torch.Tensor
    weights: torch.Tensor
    ess: torch.Tensor


def score_candidates(log_normal: torch.Tensor, log_corruption: torch.Tensor) -> LikelihoodEvidence:
    """E8/E9/E10/E11. Inputs [B,E] and [B,E,M], equal member weights."""
    normal, corruption = log_normal.double(), log_corruption.double()
    if normal.ndim != 2 or corruption.ndim != 3 or normal.shape != corruption.shape[:2]:
        raise ValueError('Expected [batch, ensemble] and [batch, ensemble, draws]')
    if not normal.numel() or not corruption.numel() or not torch.isfinite(normal).all() or not torch.isfinite(corruption).all():
        raise ValueError('Density arrays must be nonempty and finite')
    flat = corruption.flatten(1)
    log_p_normal = torch.logsumexp(normal, dim=1) - math.log(normal.shape[1])
    log_p_fault = torch.logsumexp(flat, dim=1) - math.log(flat.shape[1])
    weights = torch.softmax(flat, dim=1)
    return LikelihoodEvidence(log_p_normal, log_p_fault, log_p_fault - log_p_normal,
                              weights, 1. / weights.square().sum(dim=1))


class GaussianCorruption:
    """E5. Bias/drift amplitudes are shared across a full D-coordinate block."""
    names = ('bias', 'drift', 'noise', 'stuck')

    def __init__(self, dimension=8, scale=1., noise_floor=.25, weights=None, times=None, device='cpu'):
        if dimension < 1 or scale <= 0 or noise_floor <= 0:
            raise ValueError('Positive dimension, scale and noise floor required')
        self.dimension, self.scale, self.noise_floor = dimension, float(scale), float(noise_floor)
        times = np.arange(dimension, dtype=float) if times is None else np.asarray(times, dtype=float)
        if times.shape != (dimension,) or not np.isfinite(times).all() or (dimension > 1 and np.any(np.diff(times) <= 0)):
            raise ValueError('Require increasing observed target timestamps')
        ramp = np.zeros(1) if dimension == 1 else 2 * (times - times[0]) / (times[-1] - times[0]) - 1
        one, identity = np.ones(dimension), np.eye(dimension)
        covariance = np.stack([scale**2 * np.outer(one, one) + noise_floor**2 * identity,
                               scale**2 * np.outer(ramp, ramp) + noise_floor**2 * identity,
                               scale**2 * identity,
                               scale**2 * np.outer(one, one) + noise_floor**2 * identity])
        self.covariance = torch.as_tensor(covariance, dtype=torch.float64, device=device)
        self.cholesky = torch.linalg.cholesky(self.covariance)
        self.precision = torch.cholesky_inverse(self.cholesky)
        self.logdet = 2 * torch.diagonal(self.cholesky, dim1=-2, dim2=-1).log().sum(-1)
        weights = np.ones(4) / 4 if weights is None else np.asarray(weights, dtype=float)
        if weights.shape != (4,) or np.any(weights < 0) or not np.isfinite(weights).all() or not np.isclose(weights.sum(), 1):
            raise ValueError('Require four normalized nonnegative mixture weights')
        self.weights = torch.as_tensor(weights, dtype=torch.float64, device=device)
        self.maps = np.stack([identity, identity, identity, np.outer(one, identity[0])])
        self.times = times

    def component_log_prob(self, observed: torch.Tensor, generated: torch.Tensor) -> torch.Tensor:
        """Return [B,M,K] normalized component log densities from [B,D], [B,M,D]."""
        if observed.ndim != 2 or generated.ndim != 3 or observed.shape != (generated.shape[0], generated.shape[2]):
            raise ValueError('Expected observed [B,D], generated [B,M,D]')
        if observed.shape[-1] != self.dimension or not torch.isfinite(observed).all() or not torch.isfinite(generated).all():
            raise ValueError('Corruption density requires complete finite target blocks')
        means = generated.double().unsqueeze(2).expand(-1, -1, 4, -1).clone()
        means[:, :, 3] = generated[:, :, :1].double().expand(-1, -1, self.dimension)
        delta = observed.double()[:, None, None] - means
        quadratic = torch.einsum('bmkd,kdf,bmkf->bmk', delta, self.precision, delta)
        return -.5 * (quadratic + self.logdet + self.dimension * math.log(2 * math.pi))

    def log_prob(self, observed: torch.Tensor, generated: torch.Tensor, context=None) -> torch.Tensor:
        return torch.logsumexp(self.component_log_prob(observed, generated) + self.weights.log(), dim=-1)

    def configuration(self) -> Dict:
        return dict(dimension=self.dimension, scale=self.scale, noise_floor=self.noise_floor,
                    weights=self.weights.cpu().tolist(), times=self.times.tolist(), components=list(self.names))


def gaussian_log_prob(value, mean, covariance):
    value, mean, covariance = np.asarray(value, float), np.asarray(mean, float), np.asarray(covariance, float)
    cholesky = np.linalg.cholesky(covariance)
    residual = np.linalg.solve(cholesky, (value - mean).T).T
    return -.5 * (np.sum(residual**2, axis=-1) + 2 * np.log(np.diag(cholesky)).sum() + len(mean) * np.log(2 * np.pi))


def gaussian_fault_posterior(observed, mean, covariance, channel: GaussianCorruption):
    """Exact E6/E10 for a Gaussian prior and the same four affine channels."""
    from scipy.special import logsumexp
    observed, mean, covariance = np.asarray(observed, float), np.asarray(mean, float), np.asarray(covariance, float)
    components, means, covariances = [], [], []
    for mapping, noise in zip(channel.maps, channel.covariance.cpu().numpy()):
        total = mapping @ covariance @ mapping.T + noise
        components.append(float(gaussian_log_prob(observed, mapping @ mean, total)))
        gain = np.linalg.solve(total, mapping @ covariance).T
        means.append(mean + gain @ (observed - mapping @ mean))
        covariances.append(covariance - gain @ mapping @ covariance)
    weighted_logs = np.asarray(components) + np.log(channel.weights.cpu().numpy())
    log_fault = float(logsumexp(weighted_logs))
    probabilities = np.exp(weighted_logs - log_fault)
    posterior_mean = probabilities @ np.asarray(means)
    posterior_covariance = sum(w * (c + np.outer(m - posterior_mean, m - posterior_mean))
                               for w, m, c in zip(probabilities, means, covariances))
    return dict(log_fault=log_fault, log_normal=float(gaussian_log_prob(observed, mean, covariance)),
                ratio=log_fault-float(gaussian_log_prob(observed, mean, covariance)),
                mean=posterior_mean, covariance=posterior_covariance, component_weights=probabilities,
                component_means=np.asarray(means), component_covariances=np.asarray(covariances))


def summarize_repairs(generated: torch.Tensor, weights: torch.Tensor) -> Dict[str, torch.Tensor]:
    """Weighted means, marginal quantiles and widths. Inputs [B,M,D], [B,M]."""
    values, weights = generated.double(), weights.double()
    if values.ndim != 3 or weights.shape != values.shape[:2] or (weights < 0).any():
        raise ValueError('Invalid weighted repair shapes or weights')
    if not torch.isfinite(values).all() or not torch.isfinite(weights).all() or not torch.allclose(weights.sum(1), torch.ones_like(weights[:, 0])):
        raise ValueError('Finite values and normalized weights required')
    mean = (values * weights[..., None]).sum(1)
    ordered, indices = values.sort(dim=1)
    ordered_weights = torch.gather(weights[..., None].expand_as(values), 1, indices)
    cdf = ordered_weights.cumsum(1)
    quantiles = []
    for probability in (.05, .5, .95):
        index = (cdf < probability).sum(1).clamp_max(values.shape[1] - 1)
        quantiles.append(torch.gather(ordered, 1, index[:, None]).squeeze(1))
    return dict(mean=mean, median=quantiles[1], lower=quantiles[0], upper=quantiles[2],
                variance=(weights[..., None] * (values - mean[:, None]).square()).sum(1),
                width=quantiles[2] - quantiles[0])


def weighted_crps(values: torch.Tensor, weights: torch.Tensor, truth: torch.Tensor):
    """Exact weighted empirical marginal CRPS, O(M log M), returned [B,D]."""
    values, weights, truth = values.double(), weights.double(), truth.double()
    ordered, indices = values.sort(dim=1)
    w = torch.gather(weights[..., None].expand_as(values), 1, indices)
    cumulative_w = w.cumsum(1) - w
    cumulative_wx = (w * ordered).cumsum(1) - w * ordered
    half_pairwise = (w * (ordered * cumulative_w - cumulative_wx)).sum(1)
    return (weights[..., None] * (values - truth[:, None]).abs()).sum(1) - half_pairwise


def repair_outcome(observed, reference, repair, target, true_targets, useful_delta=.01):
    """E12 full-window action. Wrong-target damage is included in the loss."""
    before, truth = np.asarray(observed, float), np.asarray(reference, float)
    after = before.copy(); after[target, -len(repair):] = repair
    mask = np.isfinite(before) & np.isfinite(truth)
    delta = (np.sum((before[mask] - truth[mask])**2) - np.sum((after[mask] - truth[mask])**2)) / len(repair)
    correct = bool(np.asarray(true_targets, bool)[target])
    return dict(improvement=float(delta), failed=bool(not correct or delta <= useful_delta),
                harmful=bool(delta < 0), correct_attribution=correct)
