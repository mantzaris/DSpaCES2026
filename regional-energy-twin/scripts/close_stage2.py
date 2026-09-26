"""Write audit accounting from completed job records; launch no work."""
import datetime as dt
import json
from pathlib import Path


root = Path('results/stage2')
ledger = json.loads((root/'diagnostic_ledger.json').read_text())
assert all(j['status'] != 'running' for j in ledger['jobs'])
assert ledger['cumulative_wall_seconds'] < ledger['cap_seconds'] == 1800
pod = json.loads((root/'final_pod_status.log').read_text())
assert not pod['research_workers'] and not pod['cuda_processes']
stage1 = json.loads(Path('results/resource_ledger.json').read_text())
result = dict(stage=2, decision='C_stop_defer', closed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    diagnostic_cap_seconds=1800, diagnostic_wall_seconds=ledger['cumulative_wall_seconds'],
    diagnostic_jobs=len(ledger['jobs']), diagnostic_ledger='results/stage2/diagnostic_ledger.json',
    accounting='Cumulative local CPU child-job wall time, including failures and conservatively including remote inventory/hash checks and artifact copying',
    reading_writing_and_literature_retrieval='Excluded from diagnostic jobs; wall time not separately instrumented',
    additional_gpu_compute_seconds=0, no_training_sweep=True, no_main_study=True, no_stage3=True,
    november_december_and_2017_outcomes_sealed=True,
    original_stage1_research_window_seconds=stage1['allocated_wall_seconds'],
    original_stage1_ledger_unchanged=True,
    pod_status=pod,
    pod_id_note='RUNPOD_POD_ID was unset; use console connection details to identify the existing pod. Supplied SSH gateway prefix was exfhunmqghc3yx',
    existing_connection='root@213.173.107.237:38369',
    pod_remains_allocated=True, pod_lifecycle_actions_performed=[],
    billing='Instance remained allocated beyond Stage 1 and throughout this audit; actual billed amount/rate not queried',
    archived_project_files=90, archived_project_bytes=855761126,
    local_archive='data/archives/stage1_pod_20260923',
    project_artifacts_remaining_only_on_pod=[],
    future_budget_authorized=False)
(root/'resource_ledger.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k in ('decision','diagnostic_wall_seconds','diagnostic_jobs','additional_gpu_compute_seconds','pod_remains_allocated')},indent=2))
