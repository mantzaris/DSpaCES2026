import itertools
import math

import numpy as np
import pytest
import torch

from iot_entropy.temporal import permutation_entropy, sample_entropy, coarse_grain, conventional
from iot_entropy.entropy import window_features, equicorrelation_entropy, equicorrelation_derivative
from iot_entropy.calibration import rank_pvalues


def sample_oracle(x, r=2, delta=.2, theiler=2):
    templates = [x[i:i+r+1] for i in range(len(x)-r)]
    pairs = A = B = 0
    for a in range(len(templates)):
        for b in range(a+theiler+1, len(templates)):
            if np.isfinite(templates[a]).all() and np.isfinite(templates[b]).all():
                pairs += 1
                distance = np.abs(templates[a]-templates[b])
                B += int(max(distance[:r]) <= delta)
                A += int(max(distance) <= delta)
    return A, B, pairs


def test_sample_common_pairs_missing_and_chunks():
    x = np.random.default_rng(53).normal(size=(3, 64))*.2
    x[0, [4, 15, 40]] = np.nan
    result = sample_entropy(torch.tensor(x), pair_chunk=7, series_chunk=2)
    for i in range(len(x)):
        A, B, pairs = sample_oracle(x[i])
        assert (result.A[i].item(), result.B[i].item(), result.pairs[i].item()) == (A, B, pairs)
        assert A <= B <= pairs
        if A and B:
            assert result.raw[i].item() == pytest.approx(-math.log(A/B))


def test_permutation_known_signals_and_gap_grid():
    ramp = torch.arange(64, dtype=torch.float64)
    assert permutation_entropy(ramp).value.item() == pytest.approx(0)
    periodic = (ramp % 2)
    assert torch.isnan(permutation_entropy(periodic).value)  # every q=3 template tied
    dropped = ramp.clone(); dropped[10] = float('nan')
    assert permutation_entropy(dropped).templates.item() == 59
    assert permutation_entropy(ramp, tau=2).templates.item() == 60
    # Three-element permutations explicitly give the six equally likely patterns.
    counts = []
    for p in itertools.permutations(range(3)):
        counts.append(permutation_entropy(torch.tensor(p, dtype=torch.float64), minimum=1,
                                         per_pattern=0).probabilities)
    probabilities = torch.stack(counts).mean(0)
    assert torch.allclose(probabilities, torch.ones(6, dtype=torch.float64)/6)
    assert permutation_entropy(ramp[:20]).value.isnan()
    assert permutation_entropy(ramp*0).flat


def test_sample_censoring_and_undefined():
    # repeated two-prefix with deliberately distinct successor and tiny delta
    x = torch.tensor([0., 1., 2., 8., 0., 1., 3., 9.])
    se = sample_entropy(x, delta=.01, minimum=0, minimum_B=0)
    assert se.B > 0 and se.A == 0 and se.censored and torch.isinf(se.raw)
    assert torch.isnan(se.value)
    short = sample_entropy(torch.tensor([1.]))
    assert short.B == 0 and torch.isnan(short.raw)
    flat = sample_entropy(torch.zeros(64))
    assert flat.flat and flat.A == flat.B and flat.raw == 0 and torch.isnan(flat.value)


def test_coarse_bins_and_correlation_time_invariance():
    x = torch.arange(16, dtype=torch.float64)
    x[3] = float('nan')
    coarse = coarse_grain(x, 4)
    assert torch.isnan(coarse[0]) and coarse[1] == 5.5
    generator = torch.Generator().manual_seed(83)
    block = torch.randn(96, 6, generator=generator, dtype=torch.float64)
    reordered = block[torch.randperm(96, generator=generator)]
    a, b = window_features(block), window_features(reordered)
    assert torch.allclose(a.correlation, b.correlation, atol=1e-12)
    assert torch.allclose(a.values, b.values, atol=1e-12)
    r = torch.tensor(.4, dtype=torch.float64); eps=1e-6
    numerical = (equicorrelation_entropy(6,r+eps)-equicorrelation_entropy(6,r-eps))/(2*eps)
    assert abs(numerical-equicorrelation_derivative(6,r)) < 1e-8


def test_null_rank_and_temporal_support():
    rng = np.random.default_rng(781)
    rejected = []
    for _ in range(4000):
        scores = rng.normal(size=(20, 7)).max(1)
        rejected.append(rank_pvalues(scores[:-1], scores[-1:])[0] <= .1)
    assert .08 < np.mean(rejected) < .12
    x = torch.arange(64, dtype=torch.float64)
    values, _ = conventional(x)
    assert torch.allclose(values[:3], torch.ones(3, dtype=torch.float64))
    assert values[3] == 0 and values[5] == pytest.approx(1)


def test_multiscale_physical_endpoints_and_missing_bins():
    import json
    from pathlib import Path
    from iot_entropy.temporal import multiscale_trajectory, trajectory, window
    config = json.loads((Path(__file__).parents[1]/'configs/extension-v2.json').read_text())
    x = torch.tensor(np.random.default_rng(194).normal(size=(2, 120, 3, 1)), dtype=torch.float64)
    x[0, 25, 0, 0] = float('nan')
    result = multiscale_trajectory(x, 96, 2, config)
    # Explicit endpoint-by-endpoint bins, independent of the full-target helper.
    current = x[:, -96:].permute(0, 2, 3, 1).reshape(2, 3, 1, 48, 2).mean(-1)
    past = x[:, -120:-24].permute(0, 2, 3, 1).reshape(2, 3, 1, 48, 2).mean(-1)
    assert torch.isnan(current[0, 0, 0, 0]) and torch.isnan(past[0, 0, 0, 12])
    expected = torch.stack((window(current, config)['values'],
                           window(current, config)['values']-window(past, config)['values']), -1)
    assert torch.allclose(result['u'], expected, equal_nan=True)
    assert torch.allclose(multiscale_trajectory(x, 96, 1, config)['u'],
                          trajectory(x, 96, config)['u'], equal_nan=True)
    with pytest.raises(ValueError):
        multiscale_trajectory(x[:, :-1], 96, 2, config)


@pytest.mark.skipif(not torch.cuda.is_available(), reason='CUDA not available')
def test_cpu_gpu_counts_and_values():
    rng = np.random.default_rng(113)
    array = rng.normal(size=(5,96)).astype('float32')*.25
    array[0,8:12] = np.nan
    x = torch.tensor(array)
    pc, pg = permutation_entropy(x.double()), permutation_entropy(x.cuda())
    sc, sg = sample_entropy(x.double()), sample_entropy(x.cuda())
    assert torch.equal(pc.templates, pg.templates.cpu())
    assert torch.equal(sc.A, sg.A.cpu()) and torch.equal(sc.B, sg.B.cpu())
    assert torch.allclose(pc.value, pg.value.cpu().double(), atol=2e-6, equal_nan=True)
    assert torch.allclose(sc.value, sg.value.cpu().double(), atol=2e-6, equal_nan=True)
    cv, _ = conventional(x.double()); gv, _ = conventional(x.cuda())
    assert torch.allclose(cv, gv.cpu().double(), atol=2e-5, equal_nan=True)
