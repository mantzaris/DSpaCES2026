"""Training-only robust scaling. Masks remain separate from context fill values."""
from __future__ import annotations
import numpy as np


def fit_training_normalizer(x, observed=None, units=None):
    x = np.asarray(x, dtype=np.float64)
    mask = np.isfinite(x) if observed is None else observed & np.isfinite(x)
    valid = np.where(mask,x,np.nan)
    median = np.nanmedian(valid, axis=0)
    q1,q3 = np.nanpercentile(valid,[25,75],axis=0)
    floor = np.maximum(np.abs(median)*1e-6,1e-6)
    iqr = q3-q1
    return dict(median=median.tolist(),scale=np.maximum(iqr,floor).tolist(),
                floor=floor.tolist(),constant=(iqr<=floor).tolist(),
                excluded=np.flatnonzero(~np.isfinite(median)).tolist(),units=units,
                floor_rule='max(abs(training_median)*1e-6, 1e-6)')


def transform_measurements(x, normalizer):
    return (x-np.asarray(normalizer['median']))/np.asarray(normalizer['scale'])
