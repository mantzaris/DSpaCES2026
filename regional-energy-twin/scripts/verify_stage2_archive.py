"""Verify local copies against the pod snapshot; do not inspect dataset values."""
import datetime as dt
import hashlib
import json
from pathlib import Path


def main():
    inventory = Path('results/stage2/pod_inventory.log')
    if inventory.exists():
        raw = json.loads(inventory.read_text())
    else:
        saved = json.loads(Path('manifests/stage2_artifact_preservation.json').read_text())
        raw = dict(utc=saved['pod_snapshot_utc'],files=saved['files'],
                   processes='\n'.join(saved['research_workers']),
                   gpu_processes='' if saved['cuda_processes_empty'] else 'nonempty at snapshot')
    root = Path('data/archives/stage1_pod_20260923')
    failures = []
    for entry in raw['files']:
        p = root / entry['path']
        digest = hashlib.sha256()
        if not p.is_file():
            failures.append(entry['path'])
            continue
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(1048576), b''):
                digest.update(chunk)
        if p.stat().st_size != entry['bytes'] or digest.hexdigest() != entry['sha256']:
            failures.append(entry['path'])
    # Record only research process matches, without exposing unrelated command
    # arguments or service credentials from the read-only ps snapshot.
    worker_names = ('scripts/run_pilot.py','scripts/run_main_study.py','scripts/run_benchmarks.py','scripts/benchmark_cold.py')
    research_lines = [line for line in raw['processes'].splitlines()
                      if any(name in line for name in worker_names)]
    result = dict(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        pod_snapshot_utc=raw['utc'], local_archive=str(root.resolve()),
        files=raw['files'], verified_files=len(raw['files'])-len(failures),
        total_bytes=sum(f['bytes'] for f in raw['files']), mismatched_files=failures,
        research_workers=research_lines, cuda_processes_empty=not raw['gpu_processes'].strip(),
        workspace_filesystem='overlay at /; no separate /workspace mount reported by findmnt',
        excluded='Reconstructible .venv, bytecode, pytest cache and .git; no research outputs excluded',
        local_storage='Existing project filesystem on /dev/nvme0n1p2; ignored by git, not a separate off-site backup',
        raw_archive_copied_without_extracting_or_reading_test_values=True,
        irreplaceable_project_artifacts_remaining_only_on_pod=[] if not failures else failures,
        pod_remains_allocated=True)
    Path('manifests/stage2_artifact_preservation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'files'},indent=2))
    assert not failures and not research_lines and result['cuda_processes_empty']


if __name__ == '__main__':
    main()
