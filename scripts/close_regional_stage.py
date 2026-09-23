"""Conservative final budget accounting; does not stop any cloud resource."""
import datetime as dt
import json
from pathlib import Path
import time


def main():
    root=Path('results/regional'); cpu_path=root/'cpu_ledger.json'
    handoff=root/'resource_handoff.json'
    if handoff.exists() and json.loads(handoff.read_text()).get('closed'):
        print(handoff.read_text())
        return
    cpu=json.loads(cpu_path.read_text()); gpu=json.loads((root/'gpu_ledger.json').read_text())
    if any(j['status']=='running' for j in cpu['jobs']+gpu['jobs']):
        raise RuntimeError('Do not close while jobs are running')
    if not gpu.get('closed'):
        raise RuntimeError('GPU execution ledger must already be closed')
    now=time.time(); start=dt.datetime.fromisoformat(cpu['jobs'][0]['start_utc']).timestamp()
    # Existing pod stayed allocated while local preparation/analysis took place.
    # Charge all elapsed time from the earliest regional execution conservatively.
    conservative_gpu=now-start
    measured_cpu=sum(x['wall_seconds'] for x in cpu['jobs'])+sum(x['wall_seconds'] for x in gpu['jobs'])
    ancillary_allowance=60.0  # Covers short dependency/metadata/rendering helpers outside wrappers.
    assert conservative_gpu<10800 and measured_cpu+ancillary_allowance<21600
    inventory=json.loads(Path('manifests/regional_durable_artifacts.json').read_text())
    result=dict(stage='regional_stage1',closed=True,closed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        original_planning_commit='09ae274',gpu_tested_source_commit='bf2896254ae93d85dc58619b46b3a8642c5f1af2',
        conservative_gpu_allocation_start_utc=cpu['jobs'][0]['start_utc'],
        conservative_gpu_allocated_seconds=conservative_gpu,gpu_cap_seconds=10800,
        unused_gpu_cap_seconds=10800-conservative_gpu,
        actual_regional_gpu_execution_window_seconds=gpu['allocated_wall_seconds'],
        gpu_job_wall_seconds=gpu['cumulative_job_wall_seconds'],
        local_cpu_job_wall_seconds=cpu['cumulative_job_wall_seconds'],
        cpu_job_wall_including_whole_gpu_jobs=measured_cpu,
        ancillary_cpu_allowance_seconds=ancillary_allowance,
        charged_cpu_seconds=measured_cpu+ancillary_allowance,cpu_cap_seconds=21600,
        unused_cpu_cap_seconds=21600-measured_cpu-ancillary_allowance,
        downloaded_source_bytes=801674949,
        dependency_and_metadata_download_upper_allowance_bytes=210000000,
        download_cap_bytes=4000000000,
        durable_regional_file_bytes=inventory['total_bytes'],cache_cap_bytes=30000000000,
        source_and_outputs_local=True,irreplaceable_pod_only_artifacts=[],
        transfer_sha256='756e287807c29e9dff37549d41eda4af4101ee7879ba296c229c58317845c174',
        london_heldout_sealed=True,bdg2_seals_unchanged=True,original_main_disabled=True,
        pod_status='allocated, idle, no lifecycle action; billing allocation continues',
        research_jobs_running=False,next_stage_authorized=False,
        accounting_note='GPU cap compared against ALL elapsed time from first local regional job through closure, including local preparation/analysis and idle time. CPU cap charges all job wall time, including failed attempts and whole GPU jobs, plus 60 s allowance for short ancillary helpers. Reading/writing time is not CPU job time. No claim of CUDA-active profiler seconds.')
    (root/'resource_handoff.json').write_text(json.dumps(result,indent=2)+'\n')
    cpu.update(closed=True,closed_utc=result['closed_utc'])
    cpu_path.write_text(json.dumps(cpu,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
