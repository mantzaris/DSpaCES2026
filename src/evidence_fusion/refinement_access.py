"""Provider access and immutable evidence identities; evaluator kept separate."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from .refinement_gaussian import evidence_fingerprint


class ProviderArchive:
    def __init__(self, root, origin, population, model, window, trace):
        self.root = Path(root)
        self.origin = origin
        self.population = population
        self.model = model
        self.window = window
        self.trace = trace
        checked_window(window, 24)
        manifest = json.loads(Path('results/refinement/frozen_manifest.json').read_text())
        if origin < 0 or origin >= len(manifest['origins']) or manifest['origins'][origin] != window:
            raise ValueError('source origin and information cutoff disagree')

    def read(self, group, kind='aggregate'):
        if kind not in ('aggregate', 'fine'):
            raise ValueError('unsupported source interface')
        path = self.root / ('origin_%03d' % self.origin) / ('group_%02d_%s.npz' % (group, kind))
        start = time.perf_counter()
        with np.load(path, allow_pickle=False) as stored:
            ids = stored['ids']
            selected = ids < self.population
            ids = ids[selected]
            mask = stored['mask'][selected]
            source_version = str(stored['evidence_version'])
            if kind == 'fine':
                y = stored['residual'][selected]
            else:
                # Provider publishes a separately prepared sum for each nested
                # cohort. The consumer never loads hidden constituent values.
                y = stored['sum_%d' % self.population]
        event = dict(origin=self.origin, population=self.population, group=int(group),
                     operation=kind, path=str(path), file_bytes=path.stat().st_size,
                     returned_rows=int(mask.sum()), returned_value_count=int(np.isfinite(y).sum()),
                     returned_numeric_bytes=int(y.nbytes+mask.nbytes+ids.nbytes),
                     seconds=time.perf_counter()-start, cutoff=self.window,
                     evidence_id=evidence_fingerprint(self.window, ids, mask, source_version))
        # For a summary, returned_rows is provenance coverage, not rows accessed
        # by the consumer; file_bytes charges full compressed NPZ member reads.
        self.trace.append(event)
        return ids, mask, y, event['evidence_id']


def checked_window(origin, length):
    import pandas as pd
    end = pd.Timestamp(origin)
    start = end-pd.Timedelta(minutes=30*(length-1))
    if start < pd.Timestamp('2013-01-01') or end >= pd.Timestamp('2013-04-01'):
        raise ValueError('sealed or out-of-split information cutoff')
    return start, end


def query_spec(model, ids, future_slots, target_support):
    """Output supports, supplied after policy freeze; never future values."""
    weights, baseline = [], []
    for k, slot in enumerate(future_slots):
        w = np.zeros((3, len(ids)), dtype=np.float64)
        w[0] = 1
        w[1] = target_support[k, ids]
        if len(ids):
            w[2, 0] = 1
        weights.append(w)
        baseline.append(w @ model['profile'][slot, ids])
    return weights, baseline


def immutable_digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()
