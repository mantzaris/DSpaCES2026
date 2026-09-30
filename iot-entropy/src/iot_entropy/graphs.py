"""Fixed groups from physical coordinates or supplied road distances."""
from __future__ import annotations

import numpy as np
from scipy.sparse.csgraph import shortest_path
from scipy.spatial.distance import cdist


def proximity_graph(coordinates: np.ndarray, neighbors: int = 8) -> np.ndarray:
    distances = cdist(coordinates, coordinates)
    nearest = np.argsort(distances, axis=1)[:, 1:neighbors+1]
    adjacency = np.zeros_like(distances)
    adjacency[np.arange(len(distances))[:, None], nearest] = 1
    return np.maximum(adjacency, adjacency.T).astype(np.float32)


def graph_groups(adjacency: np.ndarray, coordinates: np.ndarray,
                 sizes: list[int], max_centers: int | None = None) -> dict[int, np.ndarray]:
    distances = shortest_path(adjacency > 0, directed=False, unweighted=True)
    geographic = cdist(coordinates, coordinates)
    geographic /= max(geographic.max(), 1e-12)
    order = np.argsort(distances + 0.01 * geographic, axis=1, kind='stable')
    centers = np.arange(len(adjacency))
    if max_centers is not None and max_centers < len(centers):
        # Deterministic evenly distributed index centers; fixed before scoring.
        centers = np.linspace(0, len(adjacency)-1, max_centers, dtype=int)
    result = {}
    for size in sizes:
        if size <= len(adjacency):
            groups = np.sort(order[centers, :size], axis=1)
            result[size] = np.unique(groups, axis=0)
    return result


def normalized_adjacency(adjacency: np.ndarray) -> np.ndarray:
    matrix = adjacency + np.eye(len(adjacency))
    return (matrix / matrix.sum(axis=1, keepdims=True)).astype(np.float32)
