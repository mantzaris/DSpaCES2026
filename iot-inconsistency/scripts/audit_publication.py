"""Verify the compact Git evidence without neural weights or full draw archives.

E6--E11 are recomputed for every primary test case from compact arrays read
directly from the distribution. E4 is independently recomputed on the complete
draw examples in that distribution. The earlier all-case E4 audit is preserved
separately and is not represented as a new all-case CRPS recomputation here.
"""
from pathlib import Path
import io
import json
import sys
import tarfile

import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reference'))
sys.path.insert(0, str(ROOT / 'src'))
from reference_score import repair_score
from iot_repair.baselines import PCADetector
from package_results import file_digest, inspect_archives


def score_errors(case, raw, crps=False):
    errors = []
    x = raw['input']
    for record in case['records']:
        i = record['raw_index']
        support = record['support_count']
        before = raw['loss_before'][i, :, :, :support]
        after = raw['loss_after'][i, :, :, :support]
        weights = raw['group_weights'][i, :support]
        if crps:
            target = x[np.array(record['witness_channels']), -8:].astype('float64')
            available = np.isfinite(target)
            observed = np.nan_to_num(target)
            for key, expected in [('witness_samples_before', before), ('witness_samples_after', after)]:
                samples = raw[key][i, :, :, :support].astype('float64')
                cell = (np.mean(np.abs(samples - observed[None, None, :, :, None]), axis=-1)
                        - .5 * np.mean(np.abs(samples[..., None, :] - samples[..., :, None]), axis=(-1, -2)))
                grouped = np.array([cell[:, :, g, available[g]].mean(-1) for g in range(support)]).transpose(1, 2, 0)
                errors.append(float(np.max(np.abs(grouped - expected))))
        if record['kind'] == 'observation':
            channel = record['index']
            mask = np.isfinite(x[channel, -8:])
            replacement = raw['replacement_targets'][i].astype('float64')
            cost = (.5 * mask.sum() / np.isfinite(x).sum()
                    + .5 * np.minimum(np.abs(replacement[..., mask] - x[channel, -8:][mask]) / 3, 1).mean())
        else:
            cost = 1 / len(case['graph']['edges'])
        params = case['score_parameters']
        oracle = repair_score(before, after, weights, cost,
                              uncertainty_weight=params['kappa'], edit_weight=params['lambda'])
        errors.extend(abs(value - record[key]) for key, value in oracle.items())
        assert record['witness_hash_before'] == record['witness_hash_after']
    error = max(errors, default=0.)
    assert np.isfinite(error) and error <= 1e-10, (case['id'], error)
    return error


def main():
    threadpool_limits(4)
    directory = ROOT / 'results/evidence'
    verification = inspect_archives(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    hashes = {e['path']: e['sha256'] for a in manifest['archives'] for e in a['entries']}
    oracle = json.loads((ROOT / 'results/audits/production_equations.json').read_text())
    historic = {r['case']: r for r in oracle['checks']}
    score_checks = []
    crps_checks = []
    pca_checks = []
    seen = set()
    for archive_record in manifest['archives']:
        cases = {}
        inputs = {}
        full_examples = {}
        test_manifest = None
        baselines = None
        entries = {e['path']: e for e in archive_record['entries']}
        with tarfile.open(directory / archive_record['path'], 'r|xz') as archive:
            for item in archive:
                parts = Path(item.name).parts
                primary = parts[:2] == ('results', 'study') and len(parts) == 5 and parts[3] == 'test'
                compact = parts[:3] == ('results', 'compact', 'study') and len(parts) == 6 and parts[4] == 'test'
                if not primary and not compact:
                    continue
                data = archive.extractfile(item).read()
                if primary and item.name.endswith('.json'):
                    if parts[-1] == 'case_manifest.json':
                        test_manifest = json.loads(data)
                    elif parts[-1].startswith('test_'):
                        cases[item.name] = json.loads(data)
                elif primary and parts[-1] == 'baselines_raw.npz':
                    with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
                        baselines = {k: arrays[k].copy() for k in arrays.files if k.startswith('pca_')}
                elif primary and item.name.endswith('.npz'):
                    full_examples[item.name] = data
                elif compact:
                    entry = entries[item.name]
                    case_path = str(Path(entry['original_path']).with_suffix('.json'))
                    case = cases[case_path]
                    assert entry['original_sha256'] == case['raw_sha256'] == historic[case_path]['sha256']
                    with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
                        assert set(arrays.files) == set(entry['retained_arrays'])
                        assert not set(arrays.files).intersection(entry['omitted_arrays'])
                        error = score_errors(case, arrays)
                        inputs[case['id']] = arrays['input'].copy()
                    score_checks.append(dict(case=case_path, max_absolute_error=error, candidates=len(case['records'])))
                    seen.add(case_path)
        for path, data in full_examples.items():
            case_path = str(Path(path).with_suffix('.json'))
            case = cases[case_path]
            assert hashes[path] == case['raw_sha256']
            with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
                error = score_errors(case, arrays, crps=True)
            crps_checks.append(dict(case=case_path, max_absolute_error=error, candidates=len(case['records'])))
        if test_manifest is not None:
            # All 40 saved PCA configurations are checked on identical inputs.
            values = np.stack([inputs[c['id']] for c in test_manifest['cases']])
            dataset = archive_record['path'].replace('.tar.xz', '')
            for key, expected in sorted(baselines.items()):
                lag = int(key.split('_')[1][3:])
                model = PCADetector.load(ROOT / 'results/models' / dataset / (key + '.npz'), lag)
                actual = model.score(values)
                np.testing.assert_allclose(actual, expected, atol=2e-6, rtol=2e-5, equal_nan=True)
                pca_checks.append(dict(dataset=dataset, method=key, windows=len(values),
                                       max_absolute_error=float(np.nanmax(np.abs(actual - expected)))))
        print('Audited ' + archive_record['path'], flush=True)
    assert seen == set(historic)
    assert sum(r['candidates'] for r in score_checks) == oracle['candidates']
    assert len(pca_checks) == 40
    # Every claim and figure input must resolve either directly or in a verified
    # archive. This includes the complete raw draw file behind the network view.
    def check_hash(path, expected):
        actual = hashes.get(path)
        if actual is None:
            actual = file_digest(ROOT / path)
        assert actual == expected, path
    ledger = json.loads((ROOT / 'results/paper_claims.json').read_text())
    for path, expected in ledger['sources'].items():
        check_hash(path, expected)
    for name, expected in ledger['generated_outputs'].items():
        check_hash('paper/generated/' + name, expected)
    figures = json.loads((ROOT / 'paper/figures/provenance.json').read_text())
    for name, record in figures.items():
        if name == 'generator':
            check_hash(record['path'], record['sha256'])
            continue
        for source in record['inputs']:
            if 'sha256' in source:
                check_hash(source['path'], source['sha256'])
            else:
                for file, expected in source['root_json_files'].items():
                    check_hash(str(Path(source['path']) / file), expected)
        for suffix, expected in record['outputs'].items():
            check_hash('paper/figures/' + name + '.' + suffix, expected)
    for path in sorted((ROOT / 'results/graph').glob('*.json')):
        bundle = json.loads(path.read_text())
        if 'artifact' in bundle:
            check_hash(bundle['artifact'], bundle['case']['raw_sha256'])
    final = json.loads((ROOT / 'results/audits/final.json').read_text())
    check_hash('paper/main.pdf', final['manuscript_sha256'])
    check_hash('paper/main.tex', final['manuscript_source_sha256'])
    report = dict(status='passed', archive_verification=verification,
                  manifest_sha256=file_digest(directory / 'manifest.json'),
                  primary_cases=len(score_checks), primary_candidates=oracle['candidates'],
                  score_max_absolute_error=max(r['max_absolute_error'] for r in score_checks),
                  crps_example_cases=len(crps_checks), crps_example_checks=crps_checks,
                  pca_checks=pca_checks, score_checks=score_checks,
                  scope='All primary test E6--E11 and all saved PCA configurations verified from '
                        'compact distribution arrays. E4 newly verified only on the included '
                        'full-draw examples. Historical all-case E4 and neural-weight audits '
                        'remain in their original reports and require the full local/RunPod archive to repeat.',
                  claims_and_figure_hashes='passed', manuscript_sha256=final['manuscript_sha256'])
    destination = ROOT / 'results/audits/publication.json'
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print('Publication audit passed: {} primary cases, {} E4 examples, {} PCA settings.'.format(
        len(score_checks), len(crps_checks), len(pca_checks)))


if __name__ == '__main__':
    main()
