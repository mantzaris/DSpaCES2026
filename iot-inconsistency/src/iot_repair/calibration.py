"""E12--E14. Null-tail values and fault probabilities are separate objects."""
from __future__ import annotations
import numpy as np
import torch


def fit_null_reference(scores):
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("Nonempty finite calibration units required.")
    return np.sort(scores)


def null_tail_value(reference, score):
    if isinstance(reference, torch.Tensor):
        if reference.ndim != 1 or reference.numel() == 0 or not torch.isfinite(reference).all():
            raise ValueError("Invalid calibration reference.")
        query = torch.as_tensor(score, device=reference.device, dtype=reference.dtype)
        if not torch.isfinite(query).all():
            raise ValueError("Invalid candidate score.")
        sorted_ref = reference.sort().values
        counts = 1+len(reference)-torch.searchsorted(sorted_ref, query.contiguous(), right=False)
        return counts.to(reference.dtype)/(len(reference)+1)
    ref = fit_null_reference(reference)
    if not np.isfinite(score).all():
        raise ValueError("Invalid candidate score.")
    return (1+len(ref)-np.searchsorted(ref,score,side='left'))/(len(ref)+1)


def fit_probability_calibrator(features, labels):
    from sklearn.linear_model import LogisticRegression
    y = np.asarray(labels)
    if np.unique(y).size != 2:
        raise ValueError("Probability calibration requires both labeled classes.")
    model = LogisticRegression(C=1., max_iter=2000, random_state=0)
    return model.fit(np.asarray(features).reshape(len(y),-1), y)


def decide_or_abstain(process_p, candidate_p, support_count, alpha=.05, min_support=2):
    eligible = np.asarray(support_count) >= min_support
    return dict(process_alert=np.asarray(process_p)<=alpha,
                attribution_accepted=eligible & (np.asarray(candidate_p)<=alpha),
                attribution_abstained=~eligible | (np.asarray(candidate_p)>alpha))
