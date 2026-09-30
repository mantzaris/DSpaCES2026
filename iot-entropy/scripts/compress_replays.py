"""Losslessly compress completed-run replay JSON and verify original bytes.

Originals are removed only after a complete gzip round trip matches SHA-256.
Incomplete experiment directories are skipped. Predictions/checkpoints and
statistical values are never changed.
"""
from pathlib import Path
import gzip
import hashlib
import json
import shutil

from iot_entropy.utils import digest, write_json

root = Path(__file__).resolve().parents[1]
records = []
for directory in sorted((root / 'experiments').rglob('replay')):
    status = directory.parent / 'status.json'
    if not status.exists() or json.loads(status.read_text())['status'] != 'complete':
        continue
    for source in sorted(directory.glob('*.json')):
        destination = source.with_suffix('.json.gz')
        temporary = destination.with_suffix('.gz.tmp')
        expected = digest(source)
        with source.open('rb') as raw, temporary.open('wb') as output:
            with gzip.GzipFile(filename='', mode='wb', fileobj=output, compresslevel=6, mtime=0) as compressed:
                shutil.copyfileobj(raw, compressed, length=2**20)
        restored = hashlib.sha256()
        with gzip.open(temporary, 'rb') as stream:
            for block in iter(lambda: stream.read(2**20), b''):
                restored.update(block)
        if restored.hexdigest() != expected:
            raise ValueError('Lossless replay round-trip failed: ' + str(source))
        temporary.replace(destination)
        source.unlink()
    for path in sorted(directory.glob('*.json.gz')):
        restored = hashlib.sha256(); size = 0
        with gzip.open(path, 'rb') as stream:
            for block in iter(lambda: stream.read(2**20), b''):
                restored.update(block); size += len(block)
        records.append({'path': str(path.relative_to(root)), 'gzip_sha256': digest(path),
                        'original_sha256': restored.hexdigest(), 'original_bytes': size,
                        'compressed_bytes': path.stat().st_size})
write_json(root / 'experiments/replay-compression.json', {
    'format': 'gzip, lossless JSON bytes; load directly with replay.load_frames or gzip -dc',
    'records': records, 'original_bytes': sum(r['original_bytes'] for r in records),
    'compressed_bytes': sum(r['compressed_bytes'] for r in records)})
print(json.dumps({'compressed_replay_files': len(records),
                  'original_gib': sum(r['original_bytes'] for r in records) / 2**30,
                  'compressed_gib': sum(r['compressed_bytes'] for r in records) / 2**30}))
