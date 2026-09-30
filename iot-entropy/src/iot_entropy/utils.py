"""Small, explicit helpers for manifests and reproducibility."""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    def convert(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): convert(v) for k, v in value.items()}
        if isinstance(value, (tuple, list)):
            return [convert(v) for v in value]
        if isinstance(value, np.ndarray):
            return convert(value.tolist())
        if isinstance(value, np.generic):
            return convert(value.item())
        if isinstance(value, float) and not np.isfinite(value):
            return None
        if isinstance(value, Path):
            return str(value)
        return value
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(convert(obj), indent=2, sort_keys=True) + '\n')
    temp.replace(path)


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def revision() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()


def synchronize(device: str | torch.device) -> None:
    if str(device).startswith('cuda'):
        torch.cuda.synchronize()


class Budget:
    """Wall time on a single leased GPU, including idle time in this process."""
    def __init__(self, hours: float, previous_seconds: float = 0.0):
        self.started = time.monotonic()
        self.limit_seconds = hours * 3600
        self.previous_seconds = previous_seconds

    @property
    def elapsed(self) -> float:
        return self.previous_seconds + time.monotonic() - self.started

    def check(self) -> None:
        if self.elapsed >= self.limit_seconds:
            raise TimeoutError('Configured GPU runtime budget reached; outputs preserved')


def recorded_runtime(root: Path) -> float:
    """Completed GPU-stage wall time; exclude nested summaries counted already."""
    full=root/'experiments/full'
    training=full/'training_status.json'
    total=(json.loads(training.read_text())['elapsed_seconds'] if training.exists()
           else sum(json.loads(p.read_text())['training_seconds'] for p in full.rglob('*training.json')))
    total+=sum(json.loads(p.read_text())['elapsed_seconds'] for p in full.glob('score-*/status.json'))
    total+=sum(json.loads(p.read_text())['elapsed_seconds'] for p in (root/'experiments/scoring-smoke').glob('score-*/status.json'))
    # Graph runs live under full/score-*; their stage summary is not additive.
    for path in (root/'experiments/sensitivity').glob('*-status.json'):
        if path.name!='graphs-status.json':total+=json.loads(path.read_text()).get('elapsed_seconds',0)
    for name in ['benchmark.json','fidelity-extra.json']:
        path=root/'experiments'/name
        if path.exists():total+=json.loads(path.read_text()).get('elapsed_seconds',0)
    pilot=root/'experiments/pilot/profile.json'
    if pilot.exists():total+=json.loads(pilot.read_text()).get('total_seconds',0)
    return total
