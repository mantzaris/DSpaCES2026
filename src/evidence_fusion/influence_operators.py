"""Provider work and explicit privileged exact-reference operations."""
import numpy as np


def cached_operator(model, projection_rows):
    return model.operator @ projection_rows[model.support]


def exact_norms(model, target_features):
    metric = model.operator @ model.operator.T
    return np.sqrt(np.maximum(np.einsum('td,de,te->t', target_features, metric, target_features), 0))


def exact_cross_blocks(models):
    """Richer-contract evaluator only: aligns local signed coefficients on IDs."""
    p, d = len(models), models[0].operator.shape[0]
    blocks = np.zeros((p, p, d, d))
    for i in range(p):
        for j in range(i, p):
            _, ii, jj = np.intersect1d(models[i].support, models[j].support, return_indices=True)
            block = models[i].operator[:, ii] @ models[j].operator[:, jj].T
            blocks[i, j] = block
            blocks[j, i] = block.T
    return blocks


def exact_query_grams(blocks, target_features):
    return np.einsum('td,ijde,te->tij', target_features, blocks, target_features, optimize=True)
