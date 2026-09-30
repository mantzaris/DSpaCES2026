"""Read original case arrays or the explicitly identified compact evidence."""
from pathlib import Path

import numpy as np


def load_case_arrays(path):
    """Keep original predictions preferred; never rename reduced data as raw."""
    path = Path(path)
    if path.exists():
        return np.load(path, allow_pickle=False)
    for parent in path.parents:
        if parent.name == 'results':
            compact = parent / 'compact' / path.relative_to(parent)
            if compact.exists():
                return np.load(compact, allow_pickle=False)
            break
    raise FileNotFoundError(
        '{} is absent. Run python3 scripts/package_results.py restore. '
        'Full predictive draws and trained neural weights remain in the '
        'local and RunPod experiment archive.'.format(path))
