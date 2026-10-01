"""User-provided scalar reference. Arithmetic only, not a trained detector.

NumPy 1.x compatibility explicitly uses trapz in place of NumPy 2.x trapezoid.
"""
import json
import numpy as np


def log_mean_exp(values, axis=None):
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError('Expected nonempty finite log densities')
    maximum = np.max(values, axis=axis, keepdims=True)
    reduced = maximum + np.log(np.mean(np.exp(values - maximum), axis=axis, keepdims=True))
    return np.squeeze(reduced) if axis is None else np.squeeze(reduced, axis=axis)


def corruption_score(log_normal_densities, log_corruption_densities):
    normal = np.asarray(log_normal_densities, dtype=np.float64)
    corruption = np.asarray(log_corruption_densities, dtype=np.float64)
    if normal.ndim != 1 or corruption.ndim != 2:
        raise ValueError('Unexpected dimensions')
    if corruption.shape[0] != normal.size:
        raise ValueError('Ensemble sizes differ')
    return float(log_mean_exp(corruption) - log_mean_exp(normal))


def gaussian_log_density(value, mean, variance):
    if np.any(np.asarray(variance) <= 0):
        raise ValueError('Variance must be positive')
    return -.5 * (np.log(2 * np.pi * variance) + np.square(np.asarray(value) - mean) / variance)


def analytic_score(observed, prior_variance=1., corruption_variance=4.):
    return (gaussian_log_density(observed, 0., prior_variance + corruption_variance)
            - gaussian_log_density(observed, 0., prior_variance))


def run_checks():
    checks = {}
    assert np.isclose(analytic_score(0.), -.8047189562170501)
    assert np.isclose(analytic_score(3.), 2.7952810437829498)
    checks['analytic_sign_and_values'] = [float(analytic_score(0.)), float(analytic_score(3.))]
    rng = np.random.default_rng(20261001)
    generated = rng.normal(size=262144)
    log_q = gaussian_log_density(3., generated, 4.)
    estimate = corruption_score([gaussian_log_density(3., 0., 1.)], log_q[None, :])
    assert abs(estimate - analytic_score(3.)) < .015
    checks['monte_carlo_score'] = estimate
    weights = np.exp(log_q - np.max(log_q)); weights /= weights.sum()
    mean = float(weights @ generated)
    variance = float(weights @ (generated - mean)**2)
    assert abs(mean - .6) < .015 and abs(variance - .8) < .015
    checks['posterior_mean_and_variance'] = [mean, variance]
    score = corruption_score(np.log([.1, .4]), np.log([[.2, .6], [.8, .4]]))
    assert np.isclose(score, np.log(2.))
    checks['mixture_of_densities'] = score
    scale, offset = 7., 11.
    transformed = (gaussian_log_density(scale * 3. + offset, offset, scale**2 * 5.)
                   - gaussian_log_density(scale * 3. + offset, offset, scale**2))
    assert np.isclose(transformed, analytic_score(3.))
    checks['unit_change_invariance'] = float(transformed)
    grid = np.linspace(-18., 18., 200001)
    integrate = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz
    expectation = integrate(np.exp(analytic_score(grid)) * np.exp(gaussian_log_density(grid, 0., 1.)), grid)
    assert abs(expectation - 1.) < 1e-10
    checks['ideal_null_mean_likelihood_ratio'] = float(expectation)
    original = corruption_score([-10002.], [[-10000., -10001.]])
    shifted = corruption_score([-2.], [[0., -1.]])
    assert np.isclose(original, shifted, atol=1e-11)
    checks['log_space_stability'] = original
    rejected = 0
    for invalid in (np.array([[np.nan]]), np.empty((1, 0))):
        try:
            corruption_score([0.], invalid)
        except ValueError:
            rejected += 1
    assert rejected == 2
    checks['invalid_input_rejection'] = rejected
    return dict(passed_check_groups=len(checks), checks=checks)


if __name__ == '__main__':
    print(json.dumps(run_checks(), indent=2))
