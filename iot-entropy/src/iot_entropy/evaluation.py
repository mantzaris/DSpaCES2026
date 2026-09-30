"""Event matching without point adjustment; independent-episode resampling."""
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment


def alert_intervals(times: np.ndarray, flags: np.ndarray, stride: int) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    for time in times[flags]:
        if intervals and time <= intervals[-1][1] + stride:
            intervals[-1] = (intervals[-1][0], int(time))
        else:
            intervals.append((int(time), int(time)))
    return intervals


def match_events(alerts: list[tuple[int, int]], events: list[tuple[int, int]],
                 tolerance: int = 0) -> dict:
    # First alarm onset must fall inside true interval; no credit for earlier
    # persistent alarms. tolerance is a documented trailing allowance only.
    allowed = np.array([[start >= onset and start <= end + tolerance
                         for onset, end in events] for start, _ in alerts], dtype=bool)
    matches: list[tuple[int, int]] = []
    if alerts and events:
        a, b = linear_sum_assignment(-allowed.astype(float))
        matches = [(int(i), int(j)) for i, j in zip(a, b) if allowed[i,j]]
    tp = len(matches)
    return {'tp': tp, 'fp': len(alerts)-tp, 'fn': len(events)-tp,
            'matches': matches, 'delays': [alerts[i][0]-events[j][0] for i,j in matches]}


def bootstrap_mean(values: np.ndarray, seed: int = 912, repeats: int = 1000) -> dict:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return {'mean': None, 'low': None, 'high': None, 'n': 0}
    rng = np.random.default_rng(seed)
    means = values[rng.integers(len(values), size=(repeats, len(values)))].mean(-1)
    return {'mean': float(values.mean()), 'low': float(np.quantile(means,.025)),
            'high': float(np.quantile(means,.975)), 'n': len(values)}


def event_pr_curve(episode_predictions: list[dict], alphas: np.ndarray,
                   stride: int, tolerance: int = 0) -> dict:
    points = []
    for alpha in alphas:
        total = np.zeros(3)
        for item in episode_predictions:
            alarms = alert_intervals(np.asarray(item['times']), np.asarray(item['pvalues']) <= alpha, stride)
            matched = match_events(alarms, item['events'], tolerance)
            total += [matched['tp'], matched['fp'], matched['fn']]
        tp, fp, fn = total
        points.append([float(alpha), float(tp/(tp+fp)) if tp+fp else 1.0,
                       float(tp/(tp+fn)) if tp+fn else 0.0])
    # Event merging makes recall nonmonotone; define an explicit upper envelope
    # over reachable recalls and integrate it, retaining the raw curve.
    rows = np.asarray(points)
    order = np.argsort(rows[:,2], kind='stable')
    recall, precision = rows[order,2], rows[order,1]
    unique = np.unique(recall)
    precision_at = np.array([precision[recall >= r].max() for r in unique])
    area = np.sum(np.diff(np.r_[0.0,unique]) * precision_at)
    return {'event_auprc_envelope': float(area), 'points': points,
            'definition': 'upper precision envelope over reachable one-to-one event recalls'}
