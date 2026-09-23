"""Canonical identities and measured lossless exact-support representations."""
import hashlib
import json
import struct
import zlib
import numpy as np


def record_id(building, timestamp, row, revision=0):
    return f'BDG2-v1.0|electricity|{building}|{timestamp}|row={row}|revision={revision}'


def evidence_digest(ids):
    if len(set(ids)) != len(ids):
        raise ValueError('A record appears more than once within a local fit')
    return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()


def support_encodings(indices, universe_size):
    indices = np.asarray(sorted(set(indices)), dtype=np.int64)
    if len(indices) == 0 or indices[0] < 0 or indices[-1] >= universe_size:
        raise ValueError('Invalid support')
    bitmap = np.zeros(universe_size, dtype=np.uint8)
    bitmap[indices] = 1
    packed = np.packbits(bitmap).tobytes()
    ranges = []
    start = previous = int(indices[0])
    for i in map(int, indices[1:]):
        if i != previous + 1:
            ranges.append((start, previous - start + 1))
            start = i
        previous = i
    ranges.append((start, previous - start + 1))
    intervals = b''.join(struct.pack('<II', a, b) for a, b in ranges)
    return {'bitmap': packed, 'zlib_bitmap': zlib.compress(packed, 9),
            'intervals': intervals, 'zlib_intervals': zlib.compress(intervals, 9),
            'uint32': indices.astype('<u4').tobytes()}
