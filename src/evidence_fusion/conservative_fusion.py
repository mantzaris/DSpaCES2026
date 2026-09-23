"""Message-only scalar fusion and batched simplex QP with a Frank-Wolfe gap."""
from dataclasses import dataclass
from itertools import combinations
import numpy as np


@dataclass(frozen=True)
class Solution:
    weights: np.ndarray
    value: np.ndarray
    gap: np.ndarray


def quadratic(h, w):
    return np.einsum('...i,...ij,...j->...', w, h, w)


def solve_simplex(h):
    """Enumerate active faces for p <= 8, vectorized over independent queries.

    Bordered KKT least-norm solutions also cover zero/singular PSD faces.
    Vertices guarantee a feasible candidate. Returned gap bounds suboptimality
    for a convex quadratic in exact arithmetic; floating point is audited only.
    """
    h = np.asarray(h, dtype=np.float64)
    if h.ndim < 2 or h.shape[-1] != h.shape[-2] or not np.isfinite(h).all():
        raise ValueError('Expected finite square covariance matrices')
    p = h.shape[-1]
    if not 1 <= p <= 8:
        raise ValueError('Bounded exact-face solver supports 1..8 providers')
    shape = h.shape[:-2]
    flat = h.reshape((-1, p, p))
    if not np.allclose(flat, flat.transpose(0, 2, 1), rtol=1e-10, atol=1e-12):
        raise ValueError('Nonsymmetric objective')
    scale = np.maximum(np.max(np.abs(flat), axis=(1, 2)), np.finfo(float).tiny)
    hh = flat / scale[:, None, None]
    if np.min(np.linalg.eigvalsh(hh)) < -1e-9:
        raise ValueError('Objective must be positive semidefinite')
    best = np.full(len(flat), np.inf)
    weights = np.zeros((len(flat), p))
    for size in range(1, p + 1):
        for face in combinations(range(p), size):
            ids = np.asarray(face)
            sub = hh[:, ids[:, None], ids]
            kkt = np.zeros((len(flat), size + 1, size + 1))
            kkt[:, :size, :size] = 2 * sub
            kkt[:, :size, size] = 1
            kkt[:, size, :size] = 1
            rhs = np.zeros((len(flat), size + 1, 1))
            rhs[:, -1, 0] = 1
            candidate = (np.linalg.pinv(kkt, rcond=1e-13) @ rhs)[:, :size, 0]
            feasible = (candidate.min(axis=1) >= -1e-10) & (np.abs(candidate.sum(axis=1) - 1) < 1e-8)
            candidate = np.maximum(candidate, 0)
            candidate /= np.maximum(candidate.sum(axis=1, keepdims=True), 1e-300)
            value = quadratic(sub, candidate)
            choose = feasible & (value < best)
            if choose.any():
                weights[choose] = 0
                rows = np.flatnonzero(choose)
                weights[rows[:, None], ids] = candidate[choose]
                best[choose] = value[choose]
    grad = 2 * np.einsum('bij,bj->bi', flat, weights)
    gaps = np.maximum(np.sum(weights * grad, axis=1) - grad.min(axis=1), 0)
    return Solution(weights.reshape(shape + (p,)), quadratic(flat, weights).reshape(shape), gaps.reshape(shape))


def solve_simplex_torch(h):
    """The same face enumeration on a torch device, in FP64."""
    import torch
    if h.dtype != torch.float64:
        raise ValueError('Use FP64 for audited solver')
    p = h.shape[-1]
    if not 1 <= p <= 8:
        raise ValueError('Bounded solver supports 1..8 providers')
    shape = h.shape[:-2]
    flat = h.reshape(-1, p, p)
    scale = flat.abs().amax(dim=(1, 2)).clamp_min(torch.finfo(h.dtype).tiny)
    hh = flat / scale[:, None, None]
    best = torch.full((len(flat),), float('inf'), device=h.device, dtype=h.dtype)
    weights = torch.zeros((len(flat), p), device=h.device, dtype=h.dtype)
    for size in range(1, p + 1):
        for face in combinations(range(p), size):
            ids = torch.tensor(face, device=h.device)
            sub = hh[:, ids[:, None], ids]
            kkt = torch.zeros((len(flat), size + 1, size + 1), device=h.device, dtype=h.dtype)
            kkt[:, :size, :size] = 2 * sub
            kkt[:, :size, size] = 1
            kkt[:, size, :size] = 1
            candidate = torch.linalg.pinv(kkt, rtol=1e-13)[:, :size, -1]
            feasible = (candidate.amin(dim=1) >= -1e-10) & ((candidate.sum(dim=1) - 1).abs() < 1e-8)
            candidate = candidate.clamp_min(0)
            candidate /= candidate.sum(dim=1, keepdim=True).clamp_min(1e-300)
            value = torch.einsum('bi,bij,bj->b', candidate, sub, candidate)
            choose = feasible & (value < best)
            full = torch.zeros_like(weights)
            full[:, ids] = candidate
            weights = torch.where(choose[:, None], full, weights)
            best = torch.where(choose, value, best)
    grad = 2 * torch.einsum('bij,bj->bi', flat, weights)
    gap = ((weights * grad).sum(dim=1) - grad.amin(dim=1)).clamp_min(0)
    value = torch.einsum('bi,bij,bj->b', weights, flat, weights)
    return weights.reshape(shape + (p,)), value.reshape(shape), gap.reshape(shape)


def fuse_arrays(means, sketches, norms, residual, future_variance, epsilon, fallback=True):
    """Only deployable metadata enters. No evidence vectors or outcomes accepted."""
    z, s, r = map(lambda x: np.asarray(x, dtype=np.float64), (sketches, norms, residual))
    if epsilon < 0 or not np.isfinite(epsilon) or np.any(s < 0) or np.any(r < 0) or np.any(np.asarray(future_variance) < 0):
        raise ValueError('Invalid uncertainty metadata')
    h = z @ z.swapaxes(-1, -2) + epsilon * s[..., :, None] * s[..., None, :] + r[..., :, None] * r[..., None, :]
    solution = solve_simplex(h)
    w = solution.weights.copy()
    variance = solution.value + future_variance
    if fallback:
        individual = s*s + r*r + np.asarray(future_variance)[..., None]
        idx = np.argmin(individual, axis=-1)
        minimum = np.min(individual, axis=-1)
        chosen = minimum < variance
        eye = np.eye(s.shape[-1])[idx]
        w = np.where(np.asarray(chosen)[..., None], eye, w)
        variance = np.minimum(variance, minimum)
    return dict(mean=np.sum(np.asarray(means) * w, axis=-1), variance=variance,
                weights=w, sketch_gap=solution.gap, sketch_candidate_variance=solution.value + future_variance)


def fuse_messages(messages, epoch):
    from .message_contracts import ActiveMessages
    state = ActiveMessages(epoch)
    for message in messages:
        state.accept(message)
    active = state.finalize()
    return fuse_arrays([x.mean for x in active], [x.sketch for x in active],
                       [x.norm for x in active], [x.residual for x in active],
                       active[0].future_variance, epoch.epsilon)
