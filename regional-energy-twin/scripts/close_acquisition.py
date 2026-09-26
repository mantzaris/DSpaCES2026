"""Close only a completed bounded stage; retain the pod and its storage."""
import json,subprocess,sys
from pathlib import Path
root=Path('results/acquisition')
assert (root/'artifact_audit.json').exists() and (root/'comparison/summary.json').exists()
subprocess.run([sys.executable,'scripts/acquisition_job.py','--label','closure','--close',
                '--ancillary-seconds','240','--handoff-reserve-seconds','300'],check=True)
d=json.loads((root/'resource_ledger.json').read_text())
r=dict(stage='regional_acquisition',closed=True,closed_utc=d['closed_utc'],charged_through_utc=d['charged_through_utc'],
    stage_measured_wall_minutes=d['measured_elapsed_seconds']/60,stage_conservative_allocation_minutes=d['allocated_seconds']/60,
    reserved_handoff_minutes=5,preledger_setup_seconds=d['preledger_setup_seconds'],
    cumulative_regional_allocation_minutes=d['cumulative_regional_allocated_seconds']/60,
    remaining_original_allocation_minutes=d['remaining_regional_seconds']/60,
    unused_stage_cap_minutes=d['remaining_stage_seconds']/60,
    cumulative_cpu_job_minutes=d['charged_cpu_seconds']/60,
    additional_charged_cpu_job_minutes=(d['charged_cpu_seconds']-d['prior_cpu_seconds'])/60,
    ancillary_cpu_allowance_minutes=4,remaining_original_cpu_job_minutes=(21600-d['charged_cpu_seconds'])/60,
    GPU_replay_and_tests_source='18fe4af',original_diagnostic_episodes=112,fresh_comparative_episodes=16,
    paired_original_episodes=4,households=4194,final_focused_tests=9,experiment_running=False,
    pod_allocated=True,london_holdout_sealed=True,bdg2_seals_preserved=True,main_study_disabled=True,
    next_stage_authorized=False,accounting=d['accounting'])
(root/'resource_handoff.json').write_text(json.dumps(r,indent=2)+'\n')
commands=[['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv'],
          ['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv'],['ps','-eo','pid,comm'],['du','-sb','data','results']]
(root/'pod_inventory.json').write_text(json.dumps({str(c):subprocess.check_output(c,text=True) for c in commands},indent=2)+'\n')
print(json.dumps(r,indent=2))
