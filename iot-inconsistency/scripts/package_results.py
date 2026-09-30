"""Lossless result records and compact numeric evidence for a small Git release.

Original JSON bytes are preserved, including unsuccessful experiments. Compact
NPZ files keep inputs, masks, losses, costs and truth, but omit repeated witness
draws. Their paths and checksums differ explicitly from the original artifacts.
Selected complete draw files support CRPS checks and all ten operator examples.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OMITTED = {'witness_samples_before', 'witness_samples_after'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def compact_arrays(source):
    """Deterministic uncompressed NPZ lets outer xz share repeated arrays."""
    output = io.BytesIO()
    with np.load(source, allow_pickle=False) as original:
        names = sorted(set(original.files) - OMITTED)
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name in names:
                array = io.BytesIO()
                np.lib.format.write_array(array, original[name], allow_pickle=False)
                item = zipfile.ZipInfo(name + '.npy', (1980, 1, 1, 0, 0, 0))
                archive.writestr(item, array.getvalue())
        data = output.getvalue()
        with np.load(io.BytesIO(data), allow_pickle=False) as restored:
            for name in names:
                np.testing.assert_array_equal(original[name], restored[name])
        return data, names, sorted(set(original.files) & OMITTED)


def source_files(dataset):
    paths = set()
    for split in ('development', 'calibration', 'test'):
        directory = ROOT / 'results/study' / dataset / split
        paths.update(directory.glob('*.json'))
        paths.update(directory.glob('baselines_raw.npz'))
    paths.update((ROOT / 'results/ablations' / dataset).glob('*/*/*.json'))
    paths.update((ROOT / 'results/robustness' / dataset).glob('*.json'))
    paths.update((ROOT / 'results/robustness' / dataset).glob('*latents.npz'))
    paths.update((ROOT / 'results/sensitivity' / dataset).glob('*.json'))
    if dataset == 'skab':
        paths.update((ROOT / 'results/native/skab').glob('*.json'))
    # Preserve complete raw predictions for every operator bundle.
    for path in (ROOT / 'results/graph').glob('*.json'):
        case = json.loads(path.read_text())
        if case.get('dataset') == dataset and case.get('artifact'):
            paths.add(ROOT / case['artifact'])
    # Also retain a deterministic clean/observation/association CRPS example.
    directory = ROOT / 'results/study' / dataset / 'test'
    for track in ('clean', 'observation', 'association'):
        cases = sorted(directory.glob('test_*_' + track + '.json'))
        if cases:
            case = json.loads(cases[0].read_text())
            paths.add(directory / case['raw_artifact'])
    return sorted(paths)


def pack_one(job):
    name, directory = job
    destination = Path(directory) / (name + '.tar.xz')
    temporary = destination.with_suffix('.xz.tmp')
    entries = []
    if name == 'support':
        sources = sorted(set((ROOT / 'results/models').glob('**/*.npz')) |
                         set((ROOT / 'results/pca_total').glob('*.npz')) |
                         set((ROOT / 'results/audits').glob('*.npz')) |
                         set((ROOT / 'results/interface').glob('*.png')) |
                         set((ROOT / 'paper/figures').glob('*.png')))
    else:
        sources = source_files(name)
    with lzma.open(temporary, 'wb', preset=3) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as archive:
            def add(path, data, extra=None):
                item = tarfile.TarInfo(path)
                item.size = len(data)
                item.mode = 0o644
                item.mtime = 0
                archive.addfile(item, io.BytesIO(data))
                entry = dict(path=path, bytes=len(data), sha256=digest(data))
                if extra:
                    entry.update(extra)
                entries.append(entry)
            for source in sources:
                add(source.relative_to(ROOT).as_posix(), source.read_bytes())
            if name != 'support':
                for source in sorted((ROOT / 'results/study' / name).glob('*/*.npz')):
                    if source.name == 'baselines_raw.npz':
                        continue
                    data, retained, omitted = compact_arrays(source)
                    relative = source.relative_to(ROOT / 'results')
                    target = (Path('results/compact') / relative).as_posix()
                    add(target, data, dict(original_path=source.relative_to(ROOT).as_posix(),
                                         original_sha256=file_digest(source),
                                         retained_arrays=retained, omitted_arrays=omitted))
    temporary.replace(destination)
    result = dict(path=destination.name, bytes=destination.stat().st_size,
                  sha256=file_digest(destination), entries=entries)
    print('{}: {} files, {:.2f} MiB'.format(name, len(entries), result['bytes'] / 2**20), flush=True)
    return result


def pack(directory, workers):
    directory.mkdir(parents=True, exist_ok=True)
    datasets = json.loads((ROOT / 'configs/study.json').read_text())['datasets']
    jobs = [(name, str(directory)) for name in list(datasets) + ['support']]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        archives = list(executor.map(pack_one, jobs))
    manifest = dict(schema=1, format='tar.xz', archives=archives,
                    scope='Exact finalized JSON records, compact primary arrays, all PCA states, '
                          'arithmetic inputs, and selected complete predictive draws. '
                          'Full neural weights and all predictive draws stay in the original archive.',
                    omitted_from_compact=sorted(OMITTED))
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def inspect_archives(directory, target=None):
    """Verify before extracting; refuse paths, links or changed local evidence."""
    manifest = json.loads((directory / 'manifest.json').read_text())
    total = 0
    changed = 0
    seen = set()
    for record in manifest['archives']:
        name = PurePosixPath(record['path'])
        if len(name.parts) != 1 or name.name in ('.', '..'):
            raise ValueError('Invalid archive name')
        path = directory / name.name
        if file_digest(path) != record['sha256'] or path.stat().st_size != record['bytes']:
            raise ValueError('Archive checksum mismatch: ' + str(path))
        expected = {entry['path']: entry for entry in record['entries']}
        if len(expected) != len(record['entries']):
            raise ValueError('Duplicate manifest path')
        with tarfile.open(path, 'r|xz') as archive:
            for item in archive:
                relative = PurePosixPath(item.name)
                if (not item.isfile() or relative.is_absolute() or '..' in relative.parts
                        or not relative.parts or relative.parts[0] not in ('results', 'paper')
                        or item.name not in expected or item.name in seen):
                    raise ValueError('Unexpected or unsafe archive member: ' + item.name)
                data = archive.extractfile(item).read()
                entry = expected.pop(item.name)
                if len(data) != entry['bytes'] or digest(data) != entry['sha256']:
                    raise ValueError('Member checksum mismatch: ' + item.name)
                seen.add(item.name)
                total += 1
                if target is not None:
                    destination = target / item.name
                    if target.resolve() not in destination.resolve().parents:
                        raise ValueError('Extraction escapes target: ' + item.name)
                    if destination.exists():
                        if file_digest(destination) != entry['sha256']:
                            raise ValueError('Refusing to overwrite changed evidence: ' + item.name)
                    else:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(data)
                        changed += 1
                del data
        if expected:
            raise ValueError('Missing archive members: ' + str(sorted(expected)[:5]))
        print('Verified ' + path.name, flush=True)
    print('Verified {} exact artifacts; restored {} files.'.format(total, changed))
    return dict(archives=len(manifest['archives']), artifacts=total, restored=changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('pack', 'restore', 'verify'))
    parser.add_argument('--directory', type=Path, default=ROOT / 'results/evidence')
    parser.add_argument('--target', type=Path, default=ROOT)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    if args.action == 'pack':
        pack(args.directory.resolve(), args.workers)
    else:
        inspect_archives(args.directory.resolve(), args.target.resolve() if args.action == 'restore' else None)


if __name__ == '__main__':
    main()
