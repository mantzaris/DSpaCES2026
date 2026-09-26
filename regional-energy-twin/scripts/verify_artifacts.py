"""Read-only checks on retained empirical and mathematical evidence."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd


def verify():
    audit=json.loads(Path('manifests/data_audit.json').read_text())
    source=json.loads(Path('manifests/source_archive.json').read_text())
    allocations=json.loads(Path('manifests/provider_allocations.json').read_text())
    epochs=json.loads(Path('manifests/sketch_epochs.json').read_text())
    controlled=json.loads(Path('results/controlled.json').read_text())
    benchmarks=json.loads(Path('results/benchmarks.json').read_text())
    cold=json.loads(Path('results/cold_benchmarks.json').read_text())
    metrics=pd.read_csv('results/pilot_metrics.csv')
    costs=pd.read_csv('results/pilot_costs.csv')
    recovered=pd.read_json('results/exact_exchange.json')
    assert source['bytes']==595266464 and source['md5']=='44393dc4cf61e84dec105e955368c890'
    assert not source['test_values_parsed'] and not audit['test_values_opened']
    assert len(audit['selected_buildings'])==16 and len(audit['selected_sites'])>=4
    assert len(allocations)==48 and len(costs)==96
    for item in allocations:
        common=item['common_days']*24
        assert item['provider_records']==[1008]*4
        assert item['union_records']==common+4*(1008-common)
        for i in range(4):
            for j in range(4):assert item['intersection_records'][i][j]==(1008 if i==j else common)
        assert item['target_count']<=256
    assert [e['actual_queries'] for e in epochs]==[12288,12288]
    assert sum(e['delta'] for e in epochs)==.01
    for epoch in epochs:
        assert epoch['actual_queries']<=epoch['query_cap']
        assert costs[costs.k==epoch['k']].max_relative_gram_error.max()<=epoch['epsilon']
    assert controlled['within_event_inequality_failures']==0
    assert controlled['projection_evaluations']==108 and controlled['distinct_projection_draws']==36
    assert benchmarks['max_cpu_gpu_mean_absolute_difference']<1e-9
    assert benchmarks['max_cpu_gpu_variance_absolute_difference']<1e-9
    assert cold['max_cpu_gpu_absolute_difference']<1e-9
    assert len(cold['summary'])==4 and all(r['replicates']==5 for r in cold['summary'])
    assert benchmarks['peak_vram_allocated_bytes']<24*2**30
    assert recovered.max_operator_absolute_error.max()==0
    assert costs.max_relative_solver_gap.max()<1e-8
    keys=['building','common_days','calibrated']
    naive=metrics[metrics.method=='naive_independence'].sort_values(keys).reset_index(drop=True)
    duplicate=metrics[metrics.method=='duplicate_aware_independence'].sort_values(keys).reset_index(drop=True)
    for column in ('mae','coverage90','normalized_is90'):np.testing.assert_array_equal(naive[column],duplicate[column])
    assert Path('reports/figures/pilot_quality.pdf').is_file() and Path('reports/figures/pilot_cost.pdf').is_file()
    result=dict(status='passed',allocations=48,real_queries_per_sketch_epoch=12288,
        theoretical_projection_allocations_sum=.02,within_event_failures=0,
        main_test_opened=False,exact_reconstructions=len(recovered))
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':verify()
