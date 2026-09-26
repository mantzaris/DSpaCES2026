"""Verify the refinement handoff without inspecting held-out outcomes."""
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def tree_bytes(path):
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())


def main():
    manifest = json.loads(Path('manifests/regional_refinement_durable.json').read_text())
    for item in manifest['files']:
        path = Path(item['path'])
        assert path.stat().st_size == item['bytes'], str(path)
        assert digest(path) == item['sha256'], str(path)
    replay = json.loads(Path('results/refinement/replay/summary.json').read_text())
    assert replay['config_sha256'] == digest(Path('configs/regional_refinement.json'))
    assert replay['model_sha256'] == manifest['training_model_sha256']
    assert replay['same_evidence_failures'] == 0 and replay['completed']
    assert replay['london_heldout_sealed'] and replay['bdg2_seals_unchanged']
    assert '49 passed' in Path('results/refinement/final_missing_support_tests.log').read_text()
    source = Path('results/refinement/pod_final_idle_inventory.log').read_text()
    for filename in ['src/evidence_fusion/refinement_gaussian.py',
                     'src/evidence_fusion/refinement_access.py',
                     'scripts/prepare_refinement.py', 'scripts/replay_refinement.py',
                     'tests/test_refinement.py']:
        assert digest(Path(filename)) in source, filename
    report = Path('reports/REGIONAL_TWIN_STAGE2_REFINEMENT_REPORT.md')
    checked_links = 0
    for link in re.findall(r'\]\(([^)]+)\)', report.read_text()):
        if '://' not in link:
            assert (report.parent/link).exists(), link
            checked_links += 1
    folders = ['data', '.deps', '.pytest_cache', 'results/refinement',
               'reports/figures/refinement']
    storage = {p:tree_bytes(Path(p)) for p in folders}
    temporary = set(Path('/tmp').glob('refinement*'))
    temporary.add(Path('/tmp/regional-refinement-source.tar'))
    temporary_bytes = sum(p.stat().st_size for p in temporary if p.is_file())
    assert sum(storage.values())+temporary_bytes < 30_000_000_000
    result = dict(verified_files=len(manifest['files']), checked_report_links=checked_links,
        config_sha256=replay['config_sha256'], model_sha256=replay['model_sha256'],
        local_storage_bytes=storage, local_task_temporary_file_bytes=temporary_bytes,
        pod_data_bytes=387164385+848184301,
        pod_data_source='pod_final_idle_inventory.log; includes prior BDG2 data',
        storage_caveat='Local and pod copies are separate physical storage; temporary transfer copies counted locally. Dependency environments are software, not data; system libraries are not claimed as research cache.',
        no_completed_artifact_pod_only=True, no_gpu_compute_process_at_final_preflight=True,
        seals_preserved=True, GPU_main_source='4f3d09e670b102388e9bd92fc81f4de041eeae09',
        GPU_final_test_source='fcbc575d86f42e5095af276fc0e5c012a96c84a7')
    Path('results/refinement/artifact_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
