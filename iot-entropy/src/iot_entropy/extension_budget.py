"""Cumulative recorded experiment time, including failed attempts.

Frozen experiment configurations retain their original allowance. A separate
explicit user authorization can raise it; analysis or elapsed time cannot.
CPU reporting/rendering is outside the experiment-stage wall-time ledger.
"""
import json
from pathlib import Path


def components(root: Path) -> dict:
    namespace = root/'experiments/extension-v2'
    config = json.loads((root/'configs/extension-v2.json').read_text())
    result = {'original_seconds': config['original_recorded_seconds']}
    for name, filename, key in [
        ('pilot_seconds', 'pilot.json', 'elapsed_seconds'),
        ('integration_tests_seconds', 'integration-tests.json', 'gpu_budget_additional_seconds'),
        ('multiscale_validation_seconds', 'multiscale-validation.json', 'elapsed_seconds')]:
        path = namespace/filename
        result[name] = json.loads(path.read_text())[key] if path.exists() else 0.
    for name, pattern in [
        ('primary_attempt_seconds', '*/attempt-*.json'),
        ('final_audit_seconds', 'audit-attempt-*.json'),
        ('window_attempt_seconds', 'window-attempt-*.json'),
        ('multiscale_attempt_seconds', 'multiscale-attempt-*.json')]:
        result[name] = sum(json.loads(path.read_text())['elapsed_seconds'] for path in sorted(namespace.glob(pattern)))
    return result


def authorized_hours(root: Path) -> float:
    authority = root/'experiments/extension-v2/budget-authorization.json'
    source = authority if authority.exists() else root/'configs/extension-v2.json'
    return float(json.loads(source.read_text())['gpu_hour_budget'])
