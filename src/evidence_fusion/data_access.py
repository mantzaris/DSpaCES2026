"""Versioned public download, archive integrity, and pre-test-only extraction."""
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

URL = 'https://zenodo.org/records/3887306/files/buds-lab/building-data-genome-project-2-v1.0.zip?download=1'
MD5 = '44393dc4cf61e84dec105e955368c890'


def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def fetch_archive(cache, manifests, cap=2_000_000_000):
    cache, manifests = Path(cache), Path(manifests)
    cache.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    dest = cache / 'bdg2-v1.0.zip'
    if not dest.exists():
        temporary = dest.with_suffix('.partial')
        total = 0
        with urllib.request.urlopen(URL, timeout=60) as response, temporary.open('wb') as f:
            length = response.headers.get('Content-Length')
            if length and int(length) > cap:
                raise RuntimeError('Download cap would be exceeded')
            while True:
                block = response.read(2**20)
                if not block:
                    break
                total += len(block)
                if total > cap:
                    raise RuntimeError('Download cap exceeded')
                f.write(block)
                if total % (50 * 2**20) < 2**20:
                    print('Downloaded bytes:', total, flush=True)
        temporary.replace(dest)
    if digest(dest, 'md5') != MD5:
        raise ValueError('Published MD5 mismatch')
    with zipfile.ZipFile(dest) as archive:
        entries = [dict(name=x.filename, bytes=x.file_size, compressed_bytes=x.compress_size,
                        crc32=x.CRC) for x in archive.infolist()]
        if sum(x['bytes'] for x in entries) > 10_000_000_000:
            raise RuntimeError('Archive expansion exceeds cap')
        # Only read metadata and pre-November 2016 meter values; do not extract test data.
        paths = {}
        for suffix, name in [('data/meters/raw/electricity.csv', 'electricity_pretest.csv'),
                             ('data/meters/cleaned/electricity_cleaned.csv', 'cleaned_pretest.csv'),
                             ('data/metadata/metadata.csv', 'metadata.csv'),
                             ('LICENSE', 'BDG2_LICENSE.txt')]:
            matches = [x['name'] for x in entries if x['name'].endswith('/' + suffix)]
            if len(matches) != 1:
                raise ValueError('Missing/ambiguous archive member: ' + suffix)
            member = matches[0]
            output = (manifests if suffix == 'LICENSE' else cache) / name
            with archive.open(member) as source, output.open('wb') as target:
                header = source.readline()
                if header.startswith(b'version https://git-lfs'):
                    raise ValueError('LFS pointer is not measurement data')
                target.write(header)
                if '/meters/' in suffix:
                    for line in source:
                        # Release is chronological; stop before November, no test parsing.
                        stamp = line.split(b',', 1)[0].strip(b'"')
                        if stamp >= b'2016-11-01':
                            break
                        target.write(line)
                else:
                    for block in iter(lambda: source.read(2**20), b''):
                        target.write(block)
            paths[name] = dict(archive_member=member, path=str(output),
                               bytes=output.stat().st_size, sha256=digest(output))
    manifest = dict(url=URL, version='v1.0', bytes=dest.stat().st_size,
                    md5=MD5, sha256=digest(dest), entries=entries, extracted=paths,
                    test_values_parsed=False, cutoff_exclusive='2016-11-01')
    (manifests / 'source_archive.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest
