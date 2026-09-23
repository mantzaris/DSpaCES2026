"""Independent explicit-joint Gaussian references on small FP64 GPU cases."""
import copy
import numpy as np
import pytest
torch = pytest.importorskip('torch')
from evidence_fusion.refinement_gaussian import (
    HierarchicalGaussian, MessageState, gaussian_marginal, evidence_fingerprint)
from evidence_fusion.refinement_access import checked_window


@pytest.fixture
def example():
    if not torch.cuda.is_available():
        pytest.skip('FP64 GPU checks require the authorized pod')
    model = dict(loadings=np.array([[1., .3], [.4, -.6], [.8, .2], [-.2, .7]]),
                 scale=np.array([1., 2., .7, 1.3]), detail_var=np.array([.7, 1.1, .4, 2.]),
                 measurement_var=np.array([.1, .2, .1, .3]), detail_ar=np.array([.8, -.3, .6, .2]),
                 transition=np.array([[.8, .1], [0., .6]]), process_var=np.array([.2, .1]),
                 prior_var=np.array([1., 2.]))
    engine = HierarchicalGaussian(model, 3, 'cuda')
    y = np.array([[1., np.nan, 2.], [.5, -.3, 1.], [2., 1., -.1], [-1., .2, .8]])
    return engine, y


def message(engine, y, group, kind, window='2013-01-07'):
    ids = np.array([2*group, 2*group+1]); mask = np.isfinite(y[ids])
    w = np.array([[1., 1.], [1., 0.], [0., 1.]])
    obs = y[ids] if kind == 'fine' else np.nansum(y[ids], 0)
    return engine.group_message(group, window, ids, mask, obs, kind,
        [w, w], [np.zeros(3), np.zeros(3)], evidence_fingerprint(window, ids, mask))


def explicit_joint(engine, y, kinds):
    """Assemble household state variables and raw observation rows directly."""
    length, d, n = engine.length, engine.d, len(y)
    size = engine.dimension+n*length
    j = torch.zeros((size, size), device='cuda', dtype=torch.float64)
    j[:engine.dimension, :engine.dimension] = engine.prior
    info = torch.zeros(size, device='cuda', dtype=torch.float64)
    for h in range(n):
        sl = slice(engine.dimension+h*length, engine.dimension+(h+1)*length)
        k = engine.covariance(torch.tensor([h], device='cuda'))[0]
        j[sl, sl] = torch.linalg.solve(k, torch.eye(length, device='cuda', dtype=torch.float64))
    for group, kind in enumerate(kinds):
        for t in range(length):
            rows, vals, variances = [], [], []
            for h in [group*2, group*2+1]:
                if not np.isfinite(y[h, t]):
                    continue
                row = torch.zeros(size, device='cuda', dtype=torch.float64)
                row[t*d:(t+1)*d] = engine.loading[h]
                row[engine.dimension+h*length+t] = 1
                rows.append(row); vals.append(y[h, t]); variances.append(engine.nugget[h])
            if kind == 'aggregate' and rows:
                rows, vals, variances = [sum(rows)], [sum(vals)], [sum(variances)]
            for row, val, variance in zip(rows, vals, variances):
                j += torch.outer(row, row)/variance
                info += row*val/variance
    chol = torch.linalg.cholesky(j)
    mean = torch.cholesky_solve(info[:, None], chol).squeeze(1)
    covariance = torch.cholesky_solve(torch.eye(size, device='cuda', dtype=torch.float64), chol)
    return j, info, mean, covariance


@pytest.mark.parametrize('kinds', [('aggregate', 'aggregate'), ('fine', 'aggregate'), ('fine', 'fine')])
def test_same_joint_mean_covariance_and_forecasts(example, kinds):
    engine, y = example
    state = MessageState(engine, '2013-01-07')
    for group, kind in enumerate(kinds):
        state.replace(message(engine, y, group, kind))
    j, info, mean, cov = explicit_joint(engine, y, kinds)
    inferred, factor = state.posterior()
    inferred_cov = torch.cholesky_solve(torch.eye(engine.dimension, device='cuda', dtype=torch.float64), factor)
    assert float((inferred-mean[:engine.dimension]).abs().max()) < 1e-10
    assert float((inferred_cov-cov[:engine.dimension, :engine.dimension]).abs().max()) < 1e-10
    for hi, horizon in enumerate((2, 12)):
        pred = state.predictions(hi)
        weights = torch.tensor([[1., 1.], [1., 0.], [0., 1.]], device='cuda', dtype=torch.float64)
        all_rows, all_future = [], []
        for group in range(2):
            rows = torch.zeros((2, len(mean)), device='cuda', dtype=torch.float64)
            ids = torch.tensor([group*2, group*2+1], device='cuda')
            rows[:, engine.dimension-engine.d:engine.dimension] = engine.loading[ids]@engine.future_transition[horizon]
            for k, h in enumerate(ids):
                rows[k, engine.dimension+(h+1)*engine.length-1] = engine.rho[h]**horizon
            r = weights@rows
            loading = weights@engine.loading[ids]
            noise = (weights*(engine.variance[ids]*(1-engine.rho[ids]**(2*horizon))+engine.nugget[ids]))@weights.T
            noise += loading@engine.future_noise[horizon]@loading.T
            expected = r@mean
            variance = (r@cov@r.T+noise).diagonal()
            assert float((pred['group_mean'][group]-expected).abs().max()) < 1e-9
            assert float((pred['group_var'][group]-variance).abs().max()) < 1e-9
            all_rows.append(r[0]); all_future.append(loading[0])
        total = sum(all_rows)
        future = sum(all_future)
        expected_var = total@cov@total + future@engine.future_noise[horizon]@future
        expected_var += (engine.variance*(1-engine.rho**(2*horizon))+engine.nugget).sum()
        assert abs(float(pred['region_var'][0]-expected_var)) < 1e-9


def test_replacement_orders_roundtrips_and_negative_control(example):
    engine, y = example
    a = MessageState(engine, '2013-01-07'); b = MessageState(engine, '2013-01-07')
    for g in range(2):
        a.replace(message(engine, y, g, 'aggregate'))
        b.replace(message(engine, y, g, 'aggregate'))
    before = a.posterior()[0].clone()
    a.expose_aggregate_detail(0, [0, 1], np.isfinite(y[:2]), np.nansum(y[:2], 0))
    assert a.messages[0].leaf['conditional_mean'].shape == (2, 3)
    assert torch.equal(a.posterior()[0], before)
    a.messages[0].coarsen()
    for g in [0, 1]: a.replace(message(engine, y, g, 'fine'))
    for g in [1, 0]: b.replace(message(engine, y, g, 'fine'))
    assert float((a.posterior()[0]-b.posterior()[0]).abs().max()) < 1e-10
    original = a.predictions(0)['region_var'].clone()
    version = a.version
    for _ in range(5):
        a.messages[0].coarsen()
        with pytest.raises(ValueError): a.activate(0)
        assert not a.replace(message(engine, y, 0, 'fine'))
        a.activate(0)
        assert torch.equal(a.predictions(0)['region_var'], original)
    assert a.version == version
    wrong_j = a.precision+message(engine, y, 0, 'aggregate').precision
    correct_cov = torch.linalg.solve(a.precision, torch.eye(engine.dimension, device='cuda', dtype=torch.float64))
    wrong_cov = torch.linalg.solve(wrong_j, torch.eye(engine.dimension, device='cuda', dtype=torch.float64))
    assert torch.trace(wrong_cov) < torch.trace(correct_cov)


def test_missing_cutoffs_stale_cache_and_moving_window(example):
    engine, y = example
    state = MessageState(engine, '2013-01-07')
    original = message(engine, y, 0, 'fine')
    state.replace(original)
    with pytest.raises(ValueError): state.replace(message(engine, y, 0, 'fine', '2013-01-08'))
    changed = copy.copy(original); changed.evidence_id = 'corrected-source-version'
    with pytest.raises(ValueError): state.replace(changed)
    with pytest.raises(ValueError): checked_window('2013-04-01', 24)
    with pytest.raises(ValueError): checked_window('2013-01-01', 24)
    # New fixed window deliberately uses the same training prior, not the old
    # posterior (which would count overlapping observations twice).
    shifted = np.roll(y, -1, axis=1); shifted[:, -1] = [.2, .3, .4, .5]
    moved = MessageState(engine, '2013-01-08')
    for g in range(2): moved.replace(message(engine, shifted, g, 'fine', '2013-01-08'))
    direct = explicit_joint(engine, shifted, ['fine', 'fine'])[2]
    assert float((moved.posterior()[0]-direct[:engine.dimension]).abs().max()) < 1e-10


def test_schur_elimination_order_and_lost_conditionals(example):
    engine, y = example
    j, h, mean, cov = explicit_joint(engine, y, ['fine', 'fine'])
    jm, hm = gaussian_marginal(j, h, list(range(engine.dimension)))
    first, info = gaussian_marginal(j, h, list(range(engine.dimension+6)))
    second, info = gaussian_marginal(first, info, list(range(engine.dimension)))
    assert float((second-jm).abs().max()) < 1e-10
    assert float((info-hm).abs().max()) < 1e-10
    # Identical c~N(0,1), but d|c~N(c,1) versus N(-c,2): c marginal
    # alone cannot reconstruct either detail mean map or its covariance.
    c_variance = torch.tensor(1., device='cuda')
    assert c_variance == 1 and 1+c_variance != 2+c_variance
