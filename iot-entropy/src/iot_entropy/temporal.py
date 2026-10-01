"""Grid-preserving temporal measurements, with explicit estimator support.

All kernels accept (..., time) and keep the leading dimensions. Statistical
operations use the input float32/float64, never neural autocast. No gap filling.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import torch


@dataclass
class Permutation:
    value: torch.Tensor
    raw: torch.Tensor
    templates: torch.Tensor
    tied_fraction: torch.Tensor
    probabilities: torch.Tensor
    flat: torch.Tensor


@dataclass
class Sample:
    value: torch.Tensor
    raw: torch.Tensor
    templates: torch.Tensor
    pairs: torch.Tensor
    A: torch.Tensor
    B: torch.Tensor
    censored: torch.Tensor
    flat: torch.Tensor


def moments(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    valid = torch.isfinite(x)
    n = valid.sum(-1)
    mean = x.masked_fill(~valid, 0).sum(-1) / n.clamp_min(1)
    centered = (x - mean[..., None]).masked_fill(~valid, 0)
    variance = centered.square().sum(-1) / (n - 1).clamp_min(1)
    return n, mean, variance


def permutation_entropy(x: torch.Tensor, q: int = 3, tau: int = 1,
                        minimum: int = 30, per_pattern: int = 5,
                        max_ties: float = .5, drop_ties: bool = False) -> Permutation:
    if q < 2 or tau < 1:
        raise ValueError('q>=2 and tau>=1 required')
    shape = x.shape[:-1]
    span = (q - 1) * tau + 1
    if x.shape[-1] < span:
        zero = torch.zeros(shape, device=x.device, dtype=x.dtype)
        return Permutation(zero + float('nan'), zero + float('nan'), zero.long(),
                           zero + float('nan'), torch.zeros(*shape, math.factorial(q),
                           device=x.device, dtype=x.dtype), zero.bool())
    templates = x.unfold(-1, span, 1)[..., ::tau]
    finite = torch.isfinite(templates).all(-1)
    ordered, order = torch.sort(templates, dim=-1, stable=True)
    tied = (ordered[..., 1:] == ordered[..., :-1]).any(-1) & finite
    original_count = finite.sum(-1)
    tied_fraction = tied.sum(-1) / original_count.clamp_min(1)
    if drop_ties:
        finite = finite & ~tied
    code = torch.zeros_like(order[..., 0])
    for j in range(q - 1):
        code += (order[..., j + 1:] < order[..., j, None]).sum(-1) * math.factorial(q-j-1)
    counts = torch.zeros(*shape, math.factorial(q), device=x.device, dtype=x.dtype)
    counts.scatter_add_(-1, code, finite.to(x.dtype))
    n = finite.sum(-1)
    probabilities = counts / n.clamp_min(1)[..., None]
    raw = -torch.special.xlogy(probabilities, probabilities).sum(-1) / math.log(math.factorial(q))
    raw = raw.masked_fill(n == 0, float('nan'))
    observed, _, variance = moments(x)
    flat = (observed >= 2) & (variance <= 1e-8)
    eligible = (n >= max(minimum, per_pattern * math.factorial(q))) & ~flat
    if not drop_ties:
        eligible &= tied_fraction <= max_ties
    return Permutation(raw.masked_fill(~eligible, float('nan')), raw, n,
                       tied_fraction.masked_fill(original_count == 0, float('nan')),
                       probabilities, flat)


def sample_entropy(x: torch.Tensor, r: int = 2, delta: float = .2,
                   theiler: int = 2, minimum: int = 30, minimum_B: int = 20,
                   pair_chunk: int = 512, series_chunk: int = 1024) -> Sample:
    """Unordered common admissible pairs, |a-b|>theiler; retain censoring.

    Both A and B use exactly the valid (r+1)-template start pairs. Theiler is
    measured on the uncompressed sampling grid (coarse grid at multiple scales).
    """
    if r < 1 or delta <= 0 or theiler < 0:
        raise ValueError('Require r>=1, delta>0, and nonnegative Theiler interval')
    shape = x.shape[:-1]
    flat_x = x.reshape(-1, x.shape[-1])
    nseries = len(flat_x)
    A = torch.zeros(nseries, dtype=torch.int64, device=x.device)
    B = A.clone(); pairs = A.clone(); counts = A.clone()
    if x.shape[-1] >= r + 1:
        templates = flat_x.unfold(-1, r+1, 1)
        valid = torch.isfinite(templates).all(-1)
        counts = valid.sum(-1)
        left, right = torch.triu_indices(templates.shape[1], templates.shape[1],
                                        offset=theiler+1, device=x.device)
        for start in range(0, nseries, series_chunk):
            stop = min(start + series_chunk, nseries)
            for p in range(0, len(left), pair_chunk):
                a, b = left[p:p+pair_chunk], right[p:p+pair_chunk]
                admissible = valid[start:stop, a] & valid[start:stop, b]
                distances = (templates[start:stop, a] - templates[start:stop, b]).abs()
                match_r = (distances[..., :r].amax(-1) <= delta) & admissible
                match_next = match_r & (distances[..., r] <= delta)
                B[start:stop] += match_r.sum(-1)
                A[start:stop] += match_next.sum(-1)
                pairs[start:stop] += admissible.sum(-1)
    A, B, pairs, counts = [v.reshape(shape) for v in (A, B, pairs, counts)]
    ratio = A.to(x.dtype) / B.clamp_min(1)
    raw = -torch.log(ratio)
    raw = raw.masked_fill(B == 0, float('nan'))
    censored = (A == 0) & (B > 0)
    observed, _, variance = moments(x)
    flat = (observed >= 2) & (variance <= 1e-8)
    eligible = (counts >= minimum) & (B >= minimum_B) & (A > 0) & ~flat
    value = raw.masked_fill(~eligible, float('nan'))
    return Sample(value, raw, counts, pairs, A, B, censored, flat)


CONVENTIONAL = ['acf1', 'acf2', 'acf4', 'difference_variance', 'variance',
                'trend', 'mean', 'cusum']
FEATURES = ['permutation', 'sample'] + CONVENTIONAL


def conventional(x: torch.Tensor, lags: tuple = (1, 2, 4)) -> tuple[torch.Tensor, torch.Tensor]:
    n, mean, variance = moments(x)
    required = max(12, math.ceil(.5*x.shape[-1]))
    values = []; support = []
    for lag in lags:
        a, b = x[..., lag:], x[..., :-lag]
        valid = torch.isfinite(a) & torch.isfinite(b)
        count = valid.sum(-1)
        ma = a.masked_fill(~valid, 0).sum(-1)/count.clamp_min(1)
        mb = b.masked_fill(~valid, 0).sum(-1)/count.clamp_min(1)
        da = (a-ma[..., None]).masked_fill(~valid, 0)
        db = (b-mb[..., None]).masked_fill(~valid, 0)
        denominator = (da.square().sum(-1)*db.square().sum(-1)).sqrt()
        acf = (da*db).sum(-1)/denominator.clamp_min(1e-12)
        values.append(acf.masked_fill((count < required) | (denominator <= 1e-8), float('nan')))
        support.append(count)
    differences = x[..., 1:]-x[..., :-1]
    nd, _, vd = moments(differences)
    values.extend([vd.masked_fill(nd < required, float('nan')),
                   variance.masked_fill(n < required, float('nan'))])
    support.extend([nd, n])
    valid = torch.isfinite(x)
    t = torch.arange(x.shape[-1], device=x.device, dtype=x.dtype)
    mt = (valid*t).sum(-1)/n.clamp_min(1)
    dt = (t-mt[..., None]).masked_fill(~valid, 0)
    dx = (x-mean[..., None]).masked_fill(~valid, 0)
    trend = (dt*dx).sum(-1)/dt.square().sum(-1).clamp_min(1)
    values.extend([trend.masked_fill(n < required, float('nan')),
                   mean.masked_fill(n < required, float('nan'))])
    support.extend([n, n])
    # Last CUSUM state, reset at each window. Missing timestamps add zero.
    positive = (x-.5).masked_fill(~valid, 0).cumsum(-1)
    negative = (-x-.5).masked_fill(~valid, 0).cumsum(-1)
    cp = positive[..., -1] - positive.amin(-1).clamp_max(0)
    cn = negative[..., -1] - negative.amin(-1).clamp_max(0)
    values.append(torch.maximum(cp, cn).masked_fill(n < required, float('nan')))
    support.append(n)
    return torch.stack(values, -1), torch.stack(support, -1)


def coarse_grain(x: torch.Tensor, scale: int) -> torch.Tensor:
    if scale < 1:
        raise ValueError('Scale must be positive')
    length = (x.shape[-1]//scale)*scale
    # Ordinary mean deliberately invalidates a bin containing even one NaN.
    return x[..., :length].reshape(*x.shape[:-1], length//scale, scale).mean(-1)


def window(x: torch.Tensor, config: dict) -> dict[str, torch.Tensor]:
    pe = permutation_entropy(x, config['permutation_q'], config['permutation_tau'],
        config['minimum_templates'], config['templates_per_pattern'], config['maximum_tied_fraction'])
    se = sample_entropy(x, config['sample_r'], config.get('sample_delta', .2),
        config['sample_theiler'], config['minimum_templates'], config['minimum_B'],
        config['pair_chunk'], config['series_chunk'])
    cv, counts = conventional(x, tuple(config['acf_lags']))
    values = torch.cat((pe.value[..., None], se.value[..., None], cv), -1)
    return {'values': values, 'permutation_raw': pe.raw, 'sample_raw': se.raw,
            'pe_templates': pe.templates, 'se_templates': se.templates,
            'ties': pe.tied_fraction, 'A': se.A, 'B': se.B, 'pairs': se.pairs,
            'censored': se.censored, 'flat': se.flat,
            'patterns': pe.probabilities, 'conventional_support': counts}


def trajectory(samples: torch.Tensor, window_size: int, config: dict) -> dict:
    """B,T,N,C -> values B,N,C,feature,endpoint (level, change)."""
    if samples.ndim == 3:
        samples = samples[None]
    lag = window_size//4
    if samples.shape[1] < window_size+lag:
        raise ValueError('Insufficient joint target for both endpoints')
    x = samples.permute(0, 2, 3, 1)
    current = window(x[..., -window_size:], config)
    past = window(x[..., -window_size-lag:-lag], config)
    u = torch.stack((current['values'], current['values']-past['values']), -1)
    return {'u': u, 'current': current, 'past': past}


def multiscale_trajectory(samples: torch.Tensor, window_size: int, scale: int,
                          config: dict) -> dict:
    """Same physical endpoints after left-aligned, complete-bin averaging.

    Lags and Theiler exclusion in config are in coarse-grid units. Requiring
    divisibility prevents a silently shifted decision time or change endpoint.
    """
    if samples.ndim == 3:
        samples = samples[None]
    if scale < 1 or any(v % scale for v in (samples.shape[1], window_size, window_size//4)):
        raise ValueError('Target, window and change lag must align to complete bins')
    coarse = coarse_grain(samples.permute(0, 2, 3, 1), scale).permute(0, 3, 1, 2)
    return trajectory(coarse, window_size//scale, config)
