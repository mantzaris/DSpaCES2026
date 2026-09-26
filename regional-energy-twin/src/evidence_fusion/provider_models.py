"""Fixed public calendar features and provider-local QR OLS."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.linalg import solve_triangular


def calendar_features(times):
    t = pd.DatetimeIndex(times)
    hour = t.hour.to_numpy(dtype=float)
    day = (t.dayofyear.to_numpy(dtype=float) - 1 + hour/24) / 365.25
    weekend = (t.dayofweek >= 5).astype(float)
    columns = [np.ones(len(t))]
    names = ['intercept']
    for j in (1, 2, 3):
        for fun, name in ((np.sin, 'sin'), (np.cos, 'cos')):
            columns.append(fun(2*np.pi*j*hour/24)); names.append(f'daily_{name}{j}')
    for j in range(1, 7):
        columns.append((t.dayofweek == j).astype(float)); names.append(f'weekday{j}')
    for j in (1, 2):
        for fun, name in ((np.sin, 'sin'), (np.cos, 'cos')):
            columns.append(fun(2*np.pi*j*day)); names.append(f'annual_{name}{j}')
    for fun, name in ((np.sin, 'sin'), (np.cos, 'cos')):
        columns.append(weekend * fun(2*np.pi*hour/24)); names.append(f'weekend_daily_{name}')
    return np.column_stack(columns), names


@dataclass
class OLS:
    beta: np.ndarray
    operator: np.ndarray
    sigma: float
    condition: float
    support: np.ndarray
    oof_residuals: np.ndarray
    active_columns: list

    def predict(self, features):
        return features @ self.beta


def qr_operator(x):
    if x.shape[0] <= x.shape[1] or np.linalg.matrix_rank(x) < x.shape[1]:
        raise ValueError('Insufficient full-rank provider design')
    q, r = np.linalg.qr(x, mode='reduced')
    if np.linalg.cond(r) > 1e8:
        raise ValueError('Ill-conditioned fixed design; do not tune using later outcomes')
    return solve_triangular(r, q.T), float(np.linalg.cond(r))


def fit_ols(x, y, support, day_codes):
    """Five fixed day-block folds within the provider's training data only."""
    support = np.asarray(support, dtype=int)
    xx, yy = x[support], y[support]
    if not np.isfinite(yy).all():
        raise ValueError('Missing labels cannot be imputed for fitting')
    unique = np.unique(day_codes[support])
    folds = {day: min(4, i*5 // len(unique)) for i, day in enumerate(unique)}
    group = np.array([folds[d] for d in day_codes[support]])
    # Fixed training-design-only rule: retain columns in recipe order only if
    # every OOF training fold and full fit remain full rank. Absent weekdays
    # must not induce arbitrary least-squares coefficients in a tiny fold.
    designs = [xx] + [xx[group != fold] for fold in range(5)]
    active = []
    for column in range(xx.shape[1]):
        proposed = active + [column]
        if all(np.linalg.matrix_rank(design[:, proposed]) == len(proposed) for design in designs):
            active = proposed
    reduced = xx[:, active]
    reduced_op, condition = qr_operator(reduced)
    op = np.zeros((xx.shape[1], len(yy)))
    op[active] = reduced_op
    residuals = np.empty(len(yy))
    for fold in range(5):
        held = group == fold
        train = ~held
        part, _ = qr_operator(reduced[train])
        residuals[held] = yy[held] - reduced[held] @ (part @ yy[train])
    sigma = float(np.sqrt(np.mean(residuals**2)))
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError('Degenerate training-only residual scale')
    return OLS(op @ yy, sigma*op, sigma, condition, support, residuals, active)


def allocate_days(complete_days, common_days, per_provider=42, providers=4, seed=71021):
    """Month-stratified common core and disjoint private days; counts stay fixed."""
    days = pd.DatetimeIndex(sorted(complete_days))
    rng = np.random.default_rng(seed)
    buckets = [list(rng.permutation(days[days.month == month].values)) for month in range(1, 10)]
    ordered = []
    # Cycle months so every prefix is seasonally spread.
    while any(buckets):
        for bucket in buckets:
            if bucket:
                ordered.append(bucket.pop())
    count = common_days + providers * (per_provider - common_days)
    if len(ordered) < count:
        raise ValueError('Insufficient training days for fixed evidence allocations')
    common = ordered[:common_days]
    private = ordered[common_days:count]
    result = [pd.DatetimeIndex(sorted(common + private[i::providers])) for i in range(providers)]
    if any(len(x) != per_provider for x in result):
        raise AssertionError('Unequal evidence count')
    return result
