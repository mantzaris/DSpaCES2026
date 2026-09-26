"""Wall-clock budgets that survive restarts; never reset an existing allocation."""
import json
import os
import resource
import signal
import time
from datetime import datetime, timezone
from pathlib import Path


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class Budget:
    def __init__(self, path, start, seconds=7200, cache=None, max_cache=10_000_000_000):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.start = datetime.fromisoformat(start).timestamp()
        self.deadline = self.start + seconds
        self.cache, self.max_cache = cache, max_cache
        if self.path.exists():
            old = json.loads(self.path.read_text())
            if old['start_timestamp'] != self.start or old['cap_seconds'] != seconds:
                raise ValueError('Cannot reset an existing allocation ledger')
            self.state = old
        else:
            self.state = {'start_timestamp': self.start, 'start_utc': start,
                          'cap_seconds': seconds, 'events': []}
        self.check()
        signal.signal(signal.SIGALRM, self._expired)
        signal.alarm(max(1, int(self.deadline - time.time())))

    def _expired(self, *_):
        self.record('hard_deadline', stopped=True)
        raise TimeoutError('Stage allocation cap reached')

    def check(self):
        if time.time() >= self.deadline:
            raise TimeoutError('Stage allocation cap reached; restarting is prohibited')
        if self.cache:
            size = sum(p.stat().st_size for p in Path(self.cache).rglob('*') if p.is_file())
            if size > self.max_cache:
                raise RuntimeError('Cache size cap exceeded')
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        if rss > 20_000_000_000:
            raise MemoryError('Host RSS cap exceeded')

    def record(self, event, **kwargs):
        self.state['events'].append(dict(event=event, utc=utcnow(), **kwargs))
        self.state['allocated_wall_seconds'] = time.time() - self.start
        self.state['peak_process_rss_bytes'] = max(self.state.get('peak_process_rss_bytes', 0),
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, indent=2) + '\n')
        os.replace(tmp, self.path)


def set_gpu_limit(gib=24):
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('Requested GPU is not available')
    props = torch.cuda.get_device_properties(0)
    torch.cuda.set_per_process_memory_fraction(min(gib * 2**30 / props.total_memory, 0.8), 0)
    torch.backends.cuda.matmul.allow_tf32 = False
    return props
