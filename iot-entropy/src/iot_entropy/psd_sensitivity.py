"""Gaussian missing-data covariance EM, sensitivity only (never main scoring).

Expected outer products retain conditional covariance of missing entries.
No neighbor signal is copied into an observed time series. Assumes a common
Gaussian row distribution and ignorable missingness, which may fail in practice.
"""
from __future__ import annotations

import numpy as np


def covariance_em(values: np.ndarray, iterations: int = 15) -> np.ndarray | None:
    x=np.asarray(values,dtype=np.float64)
    observed=np.isfinite(x)
    if (observed.sum(0)<max(10,x.shape[1])).any():return None
    mean=np.nanmean(x,0);std=np.nanstd(x,0,ddof=1)
    if (std<1e-8).any():return None
    z=(x-mean)/std
    covariance=np.eye(x.shape[1])
    for _ in range(iterations):
        expected=np.zeros_like(covariance)
        for row,mask in zip(z,observed):
            known=np.flatnonzero(mask);missing=np.flatnonzero(~mask)
            if not len(known):expected+=covariance;continue
            vector=np.zeros(x.shape[1]);vector[known]=row[known]
            if len(missing):
                oo=covariance[np.ix_(known,known)]+1e-6*np.eye(len(known))
                coefficient=np.linalg.solve(oo,covariance[np.ix_(known,missing)]).T
                vector[missing]=coefficient@vector[known]
                conditional=covariance[np.ix_(missing,missing)]-coefficient@covariance[np.ix_(known,missing)]
                expected[np.ix_(missing,missing)]+=conditional
            expected+=np.outer(vector,vector)
        covariance=.95*expected/len(x)+.05*np.eye(x.shape[1])
    sd=np.sqrt(np.diag(covariance))
    return covariance/np.outer(sd,sd)
