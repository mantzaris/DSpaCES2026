"""Read byte-preserving compressed or expanded research replay records."""
from __future__ import annotations

import gzip
import json
from pathlib import Path


def load_frames(directory: Path, event_index: int) -> list[dict]:
    paths = {}
    for path in directory.glob(f'{event_index}-*.json*'):
        if not (path.name.endswith('.json') or path.name.endswith('.json.gz')):
            continue
        tick = int(path.name.split('.')[0].split('-')[-1])
        # Prefer the expanded record if an interrupted compression left both.
        if tick not in paths or path.suffix == '.json':
            paths[tick] = path
    frames = []
    for tick in sorted(paths):
        path = paths[tick]
        opener = gzip.open if path.suffix == '.gz' else open
        with opener(path, 'rt', encoding='utf-8') as stream:
            frames.append(json.load(stream))
    return frames
