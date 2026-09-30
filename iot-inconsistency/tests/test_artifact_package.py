"""Protect exact evidence restoration, local edits and numerical array identity."""
import io
import json
from pathlib import Path
import sys
import tarfile

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from package_results import compact_arrays, digest, file_digest, inspect_archives
from iot_repair.artifacts import load_case_arrays


def bundle(directory, name, data):
    directory.mkdir()
    path = directory / 'test.tar.xz'
    with tarfile.open(path, 'w:xz') as archive:
        item = tarfile.TarInfo(name)
        item.size = len(data)
        archive.addfile(item, io.BytesIO(data))
    record = dict(path=path.name, bytes=path.stat().st_size, sha256=file_digest(path),
                  entries=[dict(path=name, bytes=len(data), sha256=digest(data))])
    (directory / 'manifest.json').write_text(json.dumps(dict(archives=[record])))
    return path


def test_restore_exact_bytes_and_preserve_modified_evidence(tmp_path):
    directory = tmp_path / 'bundle'
    data = b'{"raw": [1.2300, null], "note": "unchanged bytes"}\n'
    bundle(directory, 'results/case.json', data)
    target = tmp_path / 'checkout'
    assert inspect_archives(directory, target)['restored'] == 1
    case = target / 'results/case.json'
    assert case.read_bytes() == data
    assert inspect_archives(directory, target)['restored'] == 0
    case.write_bytes(b'locally edited')
    with pytest.raises(ValueError, match='Refusing to overwrite'):
        inspect_archives(directory, target)
    assert case.read_bytes() == b'locally edited'


def test_restore_rejects_bad_checksum_before_writing(tmp_path):
    directory = tmp_path / 'bundle'
    path = bundle(directory, 'results/case.json', b'{}')
    path.write_bytes(path.read_bytes() + b'changed')
    target = tmp_path / 'checkout'
    with pytest.raises(ValueError, match='checksum mismatch'):
        inspect_archives(directory, target)
    assert not target.exists()


@pytest.mark.parametrize('name', ['../outside.json', '/absolute.json', 'results/../../outside.json'])
def test_restore_rejects_escaping_paths(tmp_path, name):
    directory = tmp_path / 'bundle'
    bundle(directory, name, b'{}')
    with pytest.raises(ValueError, match='unsafe'):
        inspect_archives(directory, tmp_path / 'checkout')
    assert not (tmp_path / 'outside.json').exists()


def test_compact_arrays_preserve_masks_precision_and_distinct_paths(tmp_path):
    source = tmp_path / 'full.npz'
    values = np.array([[np.nan, np.inf, -0., np.pi]], dtype=np.float64)
    np.savez_compressed(source, input=values, mask=np.isfinite(values),
                        witness_samples_before=np.ones((4, 8)),
                        witness_samples_after=np.zeros((4, 8)))
    data, names, omitted = compact_arrays(source)
    assert set(names) == {'input', 'mask'}
    assert set(omitted) == {'witness_samples_before', 'witness_samples_after'}
    assert data == compact_arrays(source)[0]
    original = tmp_path / 'results/study/example/test/case.npz'
    compact = tmp_path / 'results/compact/study/example/test/case.npz'
    compact.parent.mkdir(parents=True)
    compact.write_bytes(data)
    with load_case_arrays(original) as arrays:
        assert arrays['input'].tobytes() == values.tobytes()
        np.testing.assert_array_equal(arrays['mask'], np.isfinite(values))
    assert not original.exists()
    original.parent.mkdir(parents=True)
    original.write_bytes(source.read_bytes())
    with load_case_arrays(original) as arrays:
        assert 'witness_samples_before' in arrays.files
