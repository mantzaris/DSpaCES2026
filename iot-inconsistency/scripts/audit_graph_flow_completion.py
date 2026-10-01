"""Verify the final study inventory and bind visual review to an exact PDF."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform
import re
import subprocess
import tarfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'results/graph_flow_v1'


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def read(name):
    return json.loads((DIRECTORY / name).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-visual-review', action='store_true',
                        help='Use only after inspecting every rendered page and the corrected figures.')
    arguments = parser.parse_args()
    lock = read('protocol_lock.json')
    assert sha(ROOT / 'configs/graph_flow_v1.json') == lock['configuration_sha256']
    assert sha(DIRECTORY / 'data_manifest.json') == lock['data_manifest_sha256']
    for path, digest in lock['source_sha256'].items():
        assert sha(ROOT / path) == digest, path
    legacy = read('legacy.json')
    original_results = {p: h for p, h in legacy['files'].items() if p.startswith('results/')}
    for path, digest in original_results.items():
        assert sha(ROOT / path) == digest, path
    assert sha(ROOT / legacy['paper_archive']) == legacy['paper_archive_sha256']
    with tarfile.open(ROOT / legacy['paper_archive'], 'r:xz') as archive:
        archived = {}
        for item in archive:
            if item.isfile() and item.name in legacy['files']:
                digest = hashlib.sha256(archive.extractfile(item).read()).hexdigest()
                assert digest == legacy['files'][item.name], item.name
                archived[item.name] = digest
    paper = ROOT / 'paper/main.pdf'
    pdf_info = subprocess.check_output(['pdfinfo', str(paper)], text=True)
    pages = int(re.search(r'^Pages:\s+(\d+)', pdf_info, re.M).group(1))
    assert pages <= 10
    latex_log = (ROOT / 'paper/main.log').read_text()
    warnings = [line for line in latex_log.splitlines() if 'Warning' in line or 'Overfull' in line]
    assert not warnings, warnings
    tests = ET.parse(DIRECTORY / 'numerical_cpu.xml').getroot()
    suites = list(tests.iter('testsuite'))
    test_count = sum(int(s.attrib.get('tests', 0)) for s in suites)
    assert test_count == 40
    assert not sum(int(s.attrib.get('failures', 0)) + int(s.attrib.get('errors', 0)) for s in suites)
    publication = read('publication_audit.json')
    assert publication['status'] == 'passed'
    assert publication['compact_scores_recomputed'] == 107620
    assert len(publication['average_precision_checks']) == 100
    assert all('ess_max_error' in r for r in publication['generation_replays'])
    action_checks = [r for r in publication['generation_replays'] if 'repair_outcome_max_error' in r]
    assert len(action_checks) == 15
    models = read('model_manifest.json')
    for item in models['files']:
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
    remote = read('model_remote_audit.json')
    assert remote['status'] == 'passed'
    for path in models['frozen_model_paths_verified']:
        assert remote['files'][path] == sha(ROOT / path), path
    assert read('execution_jobs.json')['graph_flow_finish_resume']['state'] == 'complete'
    assert read('graph/persistence_audit.json')['idempotent']
    assert read('graph/interface/browser_verification.json')['case_count'] == 23
    # All graph case files and content-addressed evidence referenced by them exist.
    exports = read('graph/export_manifest.json')
    for item in exports:
        assert sha(ROOT / item['path']) == item['sha256']
        case = json.loads((ROOT / item['path']).read_text())
        assert sha(ROOT / case['artifact']['path']) == case['artifact']['sha256']
    for ledger_name in ('paper_claims.json', 'figure_provenance.json'):
        record = read(ledger_name)
        ledgers = [record] if ledger_name == 'paper_claims.json' else record.values()
        for ledger in ledgers:
            for category in ('inputs', 'outputs'):
                for path, digest in ledger[category].items():
                    if path.endswith('.png') and not (ROOT / path).exists():
                        continue
                    assert sha(ROOT / path) == digest, path
    old = read('completion.json') if (DIRECTORY / 'completion.json').exists() else {}
    if not arguments.record_visual_review:
        assert old.get('visual_review_pdf_sha256') == sha(paper), 'Inspect changed PDF before recording completion'
    import numpy, scipy, sklearn, matplotlib, torch
    environment = dict(python=platform.python_version(), numpy=numpy.__version__, scipy=scipy.__version__,
                       sklearn=sklearn.__version__, matplotlib=matplotlib.__version__, torch=torch.__version__)
    important = ['analysis.json', 'protocol_lock.json', 'production_equation_audit.json',
                 'publication_audit.json', 'publication/manifest.json', 'model_manifest.json',
                 'model_remote_audit.json', 'execution_jobs.json', 'paper_claims.json', 'figure_provenance.json',
                 'graph/persistence_audit.json', 'graph/interface/browser_verification.json']
    record = dict(status='complete', created_utc=datetime.now(timezone.utc).isoformat(),
                  mandatory_stages_complete=list(range(1, 7)), blockers=[],
                  optional_unexecuted=['MTGFlow training', 'Dynamic graph adaptation'],
                  not_performed=['Paper submission', 'Human operator study', 'Untouched real-environment validation'],
                  frozen_numerical_sources_verified=len(lock['source_sha256']),
                  original_result_files_preserved=len(original_results), legacy_paper_files_verified=archived,
                  tests_passed=test_count, scalar_check_groups=read('reference_checks.json')['passed_check_groups'],
                  candidate_scores_recomputed=publication['compact_scores_recomputed'],
                  production_generation_bundles=30, independent_repair_action_checks=len(action_checks),
                  paper=dict(path='paper/main.pdf', sha256=sha(paper), pages=pages,
                             source_sha256=sha(ROOT / 'paper/main.tex'), warnings=warnings),
                  venue=dict(url='https://sites.google.com/unisalento.it/ieee-dspaces-2026/home',
                             checked_utc_date='2026-10-01', full_paper_limit_including_references=10),
                  visual_review_pdf_sha256=sha(paper), visually_reviewed_pages=list(range(1, pages + 1)),
                  visual_review_scope='Every rendered page, six scientific figures and both operator screenshots. '
                                      'Architecture clipping was corrected before this final build.',
                  graph_cases=len(exports), model_files_verified=len(models['files']),
                  frozen_model_paths_verified=len(models['frozen_model_paths_verified']),
                  compact_archive_bytes=read('publication/manifest.json')['archive_bytes'],
                  artifact_sha256={str((DIRECTORY / name).relative_to(ROOT)): sha(DIRECTORY / name) for name in important},
                  rendering_environment=environment,
                  reproducibility_limit=models['limitation'], git_policy='main, local commits, user pushes')
    (DIRECTORY / 'completion.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ('status', 'tests_passed', 'candidate_scores_recomputed',
        'independent_repair_action_checks', 'paper', 'original_result_files_preserved', 'blockers')}, indent=2))


if __name__ == '__main__':
    main()
