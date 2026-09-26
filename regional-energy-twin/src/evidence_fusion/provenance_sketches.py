"""Canonical-record Gaussian streams and explicit finite-family accounting."""
from dataclasses import dataclass, field
import hashlib
import math
import numpy as np


def sufficient_epsilon(k, queries, providers, delta):
    if k < 1 or queries < 1 or providers < 1 or not 0 < delta < 1:
        raise ValueError('Invalid projection contract')
    target = math.log(2 * queries * (2*providers**2 + providers) / delta) / k
    if target >= 1/12:
        raise ValueError('No epsilon < 1 satisfies the declared bound')
    low, high = 0., 1.
    for _ in range(80):
        mid = (low + high) / 2
        if mid**2/4 - mid**3/6 >= target:
            high = mid
        else:
            low = mid
    return float(np.nextafter(high, np.inf))


@dataclass
class Epoch:
    name: str
    seed: int
    k: int
    query_cap: int
    provider_cap: int
    delta: float
    seen: set = field(default_factory=set, repr=False)

    @property
    def epsilon(self):
        return sufficient_epsilon(self.k, self.query_cap, self.provider_cap, self.delta)

    def consume(self, query, providers):
        if not 1 <= providers <= self.provider_cap:
            raise ValueError('Provider cap exceeded')
        if query not in self.seen and len(self.seen) >= self.query_cap:
            raise ValueError('Sketch epoch exhausted')
        self.seen.add(query)


def gaussian_columns(record_ids, k, seed):
    """Return [records,k]. Shared IDs reproduce columns without other providers.

    SHA-256-derived PCG64 streams are a reproducible pseudorandom implementation,
    not an information-theoretic proof of independent Gaussian columns.
    """
    out = np.empty((len(record_ids), k), dtype=np.float64)
    for row, record in enumerate(record_ids):
        digest = hashlib.sha256((str(seed) + '\0' + record).encode()).digest()
        words = np.frombuffer(digest, dtype='<u4')
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(words)))
        out[row] = rng.standard_normal(k) / math.sqrt(k)
    return out
