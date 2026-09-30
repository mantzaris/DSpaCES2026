"""Finite-sample rank calibration; no exchangeability claim for sensor streams."""
from __future__ import annotations

import numpy as np


def scan_maximum(scores: np.ndarray) -> np.ndarray:
    finite = np.where(np.isfinite(scores), scores, -np.inf)
    return finite.max(axis=-1)


def rank_pvalues(calibration_maxima: np.ndarray, scores: np.ndarray) -> np.ndarray:
    calibration = np.asarray(calibration_maxima)
    # All-abstained units have score -inf and are valid no-alert units.
    if len(calibration) == 0 or np.isnan(calibration).any():
        raise ValueError('Need nonempty calibration without NaN')
    sorted_scores = np.sort(calibration)
    counts = len(calibration) - np.searchsorted(sorted_scores, scores, side='left')
    return (1 + counts) / (len(calibration) + 1)


def two_sided_cusum(values: np.ndarray, center: np.ndarray, scale: np.ndarray,
                    allowance: float = 0.5) -> np.ndarray:
    """Restart each independent episode; missing features pause the accumulator."""
    standardized = (values - center) / scale
    positive = np.zeros(standardized.shape[1:])
    negative = positive.copy()
    result = []
    for row in standardized:
        valid = np.isfinite(row)
        positive = np.where(valid, np.maximum(0, positive + row - allowance), positive)
        negative = np.where(valid, np.maximum(0, negative - row - allowance), negative)
        result.append(np.where(valid, np.maximum(positive, negative), np.nan))
    return np.asarray(result)
