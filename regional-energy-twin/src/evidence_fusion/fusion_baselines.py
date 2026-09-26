"""Established scalar baselines; equal access to duplicate-filtered messages."""
import numpy as np
from sklearn.covariance import LedoitWolf
from .conservative_fusion import solve_simplex, quadratic


def fuse_with_weights(means, weights, variance):
    return dict(mean=np.sum(means * weights, axis=-1), variance=variance, weights=weights)


def independence(means, norms, residual, future, corrected=False):
    marginal = norms**2 + residual**2
    if not corrected:
        marginal = marginal + future
    precision = 1/np.maximum(marginal, np.finfo(float).tiny)
    w = precision / precision.sum(axis=-1, keepdims=True)
    variance = np.sum(w*w*marginal, axis=-1)
    if corrected:
        variance = variance + future
    return fuse_with_weights(means, w, variance)


def scalar_ci(means, norms, residual, future):
    variance = norms**2 + residual**2 + future
    index = np.argmin(variance, axis=-1)  # deterministic tie: provider order
    w = np.eye(means.shape[-1])[index]
    return fuse_with_weights(means, w, np.min(variance, axis=-1))


def exact_lineage(means, gram, residual, future):
    h = gram + residual[..., :, None]*residual[..., None, :]
    solution = solve_simplex(h)
    answer = fuse_with_weights(means, solution.weights, solution.value + future)
    answer['gap'] = solution.gap
    return answer


def learned_covariance(means, outcomes, covariance_mask):
    """Fit October 1-10 only; score/calibration arrays are never accepted here."""
    errors = means[covariance_mask] - outcomes[covariance_mask, None]
    valid = np.isfinite(errors).all(axis=1)
    if valid.sum() < 20:
        raise ValueError('Insufficient historical errors for covariance fit')
    estimator = LedoitWolf(assume_centered=False).fit(errors[valid])
    covariance = estimator.covariance_
    solution = solve_simplex(covariance)
    return fuse_with_weights(means, solution.weights, np.full(len(means), solution.value)), {
        'covariance': covariance.tolist(), 'shrinkage': float(estimator.shrinkage_),
        'fit_targets': int(valid.sum()), 'weights': solution.weights.tolist(), 'gap': float(solution.gap)}
