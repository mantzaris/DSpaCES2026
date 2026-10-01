"""Record locally available weights without placing checkpoints in Git."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'results/graph_flow_v1'


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-remote', action='store_true')
    arguments = parser.parse_args()
    files = []
    for path in sorted((DIRECTORY / 'models').iterdir()):
        if path.suffix not in ('.pt', '.npz', '.pkl', '.json'):
            continue
        relative = str(path.relative_to(ROOT))
        files.append(dict(path=relative, sha256=sha256(path), bytes=path.stat().st_size,
                          local_absolute_path=str(path),
                          authorized_pod_path='/workspace/iot-inconsistency/' + relative))
    by_path = {item['path']: item for item in files}
    lock = json.loads((DIRECTORY / 'protocol_lock.json').read_text())
    checked = set()

    def check(value):
        if isinstance(value, dict):
            path = value.get('path')
            if isinstance(path, str) and path.startswith('results/graph_flow_v1/models/'):
                assert path in by_path, path
                assert by_path[path]['sha256'] == value['sha256'], path
                checked.add(path)
            for item in value.values():
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)

    check(lock)
    remote_path = DIRECTORY / 'model_remote_audit.json'
    if arguments.check_remote:
        command = ("from pathlib import Path; import hashlib,json; "
                   "print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() "
                   "for p in Path('results/graph_flow_v1/models').iterdir() "
                   "if p.is_file() and p.suffix in ['.pt','.npz','.pkl','.json']}))")
        response = subprocess.run(['bash', 'scripts/runpod.sh', 'exec', '.venv/bin/python', '-c', command],
                                  cwd=ROOT, check=True, capture_output=True, text=True)
        remote = json.loads(response.stdout)
        missing = [item['path'] for item in files if item['path'] not in remote]
        different = [item['path'] for item in files if item['path'] in remote and remote[item['path']] != item['sha256']]
        required_missing = sorted(checked - set(remote))
        audit = dict(status='passed' if not required_missing and not different else 'failed',
                     checked_utc=datetime.now(timezone.utc).isoformat(), files=remote,
                     local_files=len(files), remote_files=len(remote), missing_on_pod=missing,
                     different=different, required_frozen_models_missing=required_missing,
                     remote_root='/workspace/iot-inconsistency',
                     local_only_explanation='Any missing non-frozen files are local-only development artifacts. '
                                            'Frozen inference uses the verified portable tree arrays.')
        remote_path.write_text(json.dumps(audit, indent=2) + '\n')
        assert audit['status'] == 'passed', audit
    if remote_path.exists():
        remote = json.loads(remote_path.read_text())['files']
        for item in files:
            item['verified_on_pod'] = remote.get(item['path']) == item['sha256']
            if not item['verified_on_pod']:
                item['authorized_pod_path'] = None
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(), files=files,
                  total_bytes=sum(item['bytes'] for item in files),
                  frozen_model_paths_verified=sorted(checked),
                  local_files_verified=True, publicly_distributed=False,
                  limitation='These files are available in this workspace and the existing authorized pod. '
                             'The repository alone does not provide model-weight replay. '
                             'An independent user must retrain or obtain these exact weights. '
                             'Published score and generation audits do not require weights.',
                  legacy_weights_manifest='results/model_weights/manifest.json',
                  environment='results/graph_flow_v1/environment_gpu.json',
                  remote_verification='results/graph_flow_v1/model_remote_audit.json' if remote_path.exists() else None,
                  protocol_lock_sha256=sha256(DIRECTORY / 'protocol_lock.json'))
    (DIRECTORY / 'model_manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(files=len(files), frozen_model_paths_verified=len(checked),
                          total_bytes=report['total_bytes']), indent=2))


if __name__ == '__main__':
    main()
