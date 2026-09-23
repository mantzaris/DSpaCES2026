"""Empirical chronological interval correction, without coverage guarantees."""
import numpy as np


def fit_correction(mean, variance, outcomes, mask):
    valid = np.asarray(mask) & np.isfinite(outcomes) & np.isfinite(mean) & (variance > 0)
    if valid.sum() < 20:
        raise ValueError('Insufficient independent-date calibration observations')
    standardized = (outcomes[valid] - mean[valid]) / np.sqrt(variance[valid])
    # Linear quantiles, explicitly empirical (no iid/conformal assertion).
    return dict(q90=float(np.quantile(np.abs(standardized), .9)),
                q95=float(np.quantile(np.abs(standardized), .95)),
                q80=float(np.quantile(standardized, .8)), n=int(valid.sum()))
