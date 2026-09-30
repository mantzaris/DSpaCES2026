"""Descriptive participation and group merging, never causal attribution."""
from __future__ import annotations

import numpy as np


def participation(scores: np.ndarray, groups: list[list[int]], node_count: int) -> np.ndarray:
    numerator, denominator = np.zeros(node_count), np.zeros(node_count)
    for score, group in zip(scores, groups):
        if np.isfinite(score):
            numerator[group] += score / len(group)
            denominator[group] += 1 / len(group)
    return np.divide(numerator, denominator, out=np.zeros(node_count), where=denominator > 0)


def top_nodes(scores: np.ndarray, groups: list[list[int]], node_count: int,
              budget: int) -> list[int]:
    values = participation(scores, groups, node_count)
    return np.argsort(-values, kind='stable')[:budget].tolist()


def set_metrics(predicted: list[int], truth: list[int]) -> dict[str, float]:
    p, t = set(predicted), set(truth)
    overlap = len(p & t)
    precision = overlap / len(p) if p else 0.0
    recall = overlap / len(t) if t else 0.0
    return {'precision': precision, 'recall': recall,
            'f1': 2*precision*recall/(precision+recall) if precision+recall else 0.0,
            'iou': overlap/len(p|t) if p|t else 1.0}


def oracle_overlap(groups: list[list[int]], truth: list[int]) -> float:
    return max(set_metrics(group, truth)['iou'] for group in groups)


def merge_groups(indices: list[int], groups: list[list[int]], threshold: float = 0.5) -> list[list[int]]:
    clusters: list[list[int]] = []
    for index in indices:
        matching = [k for k, cluster in enumerate(clusters)
                    if any(set_metrics(groups[index], groups[j])['iou'] >= threshold for j in cluster)]
        if not matching:
            clusters.append([index])
        else:
            merged = [index]
            for k in reversed(matching):
                merged.extend(clusters.pop(k))
            clusters.append(merged)
    return clusters
