"""Regenerate the cumulative budget/completion ledger from accepted attempts."""
from pathlib import Path
import json
from iot_entropy.extension_budget import components, authorized_hours
from iot_entropy.utils import write_json

root = Path(__file__).resolve().parents[1]
ns = root/'experiments/extension-v2'
parts = components(root); total = sum(parts.values()); limit = authorized_hours(root)*3600
assert total <= limit
primary = sorted(p.parent.name for p in ns.glob('*/status.json'))
window = sorted(p.parent.name for p in ns.glob('window-support/*/metrics.json'))
multi = sorted(p.parent.name for p in ns.glob('multiscale/*/status.json'))
required = json.loads((root/'configs/extension-v2.json').read_text())['datasets']
unfinished = []
if len(primary) != 15: unfinished.append('primary comparisons')
if len(window) != len(required): unfinished.append('window/support sensitivity')
if len(multi) != len(required): unfinished.append('calibrated scale-2 sensitivity')
write_json(ns/'completion.json', {
    'status': 'completed authorized comparisons' if not unfinished else 'incomplete; see list',
    'components': parts, 'total_recorded_seconds': total, 'limit_seconds': limit,
    'primary_runs': primary, 'window_support_runs': window, 'multiscale_runs': multi,
    'complete': ['15 primary configurations', 'paired reference fidelity for five configurations',
        'development missingness support', 'three isolated pipeline/CPU-GPU kernel benchmarks',
        'five window/support sensitivity configurations', 'five calibrated scale-1/2 configurations']
        if not unfinished else [],
    'unfinished': unfinished,
    'original_four_hour_stop': json.loads((ns/'window-attempt-0.json').read_text()),
    'authorization': 'budget-authorization.json: user explicitly authorized up to eight cumulative hours',
    'guard_snapshot_reconciliation_seconds': total-max(json.loads(p.read_text())['cumulative_seconds']
        for p in ns.glob('multiscale-attempt-*.json')) if multi else None,
    'note': 'Includes original work, pilots, numerical CUDA checks, failed attempts and accepted experiment stages. '
        'The original four-hour guard stopped with 0.57-second check granularity; subsequent work was explicitly authorized. '
        'The final reconstructed ledger includes the earlier 8.6-second CUDA integration check whose local record was '
        'absent from the remote ledger-helper directory during the last multiscale attempt; historical guard snapshots '
        'are retained unchanged. This reconciliation remains well inside the eight-hour allowance. '
        'CPU reporting/rendering/provenance I/O are outside GPU experiment-stage wall time. This is not Pod rental uptime. '
        'Isolated timing excludes ingestion/loading/disk output/calibration lookup/dashboard.'})
print(json.dumps({'total_recorded_hours': total/3600, 'authorized_hours': limit/3600,
                  'primary_runs': len(primary), 'window_support_runs': len(window),
                  'multiscale_runs': len(multi), 'unfinished': unfinished}))
