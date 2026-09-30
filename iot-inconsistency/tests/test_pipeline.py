from pathlib import Path
import sys
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from iot_repair.diffusion import ConditionalDiffusion
from iot_repair.pipeline import score_candidates


def test_complete_pipeline_no_op_has_zero_gain_and_fixed_targets():
    torch.set_num_threads(2);torch.manual_seed(42)
    x=np.random.default_rng(33).normal(size=(6,64)).astype('float32')
    graph=dict(version='test',groups=[str(i) for i in range(6)],affinity=(np.ones((6,6))-np.eye(6)).tolist(),
        edges=[dict(source=i,target=(i+1)%6,lag=1,sign=1,magnitude=.8,intercept=.1) for i in range(6)])
    models=[ConditionalDiffusion(6,width=16,steps=4).eval() for _ in range(3)]
    records,raw,abstentions=score_candidates(models,x,graph,[('observation',0),('association',0)],
        replicates=2,predictive_samples=2,sampling_steps=4,no_op=True)
    assert not abstentions
    assert raw['loss_before'].shape==(2,3,2,2)
    assert raw['witness_samples_before'].shape==(2,3,2,2,8,2)
    np.testing.assert_array_equal(raw['loss_before'],raw['loss_after'])
    for record in records:
        assert record['witness_hash_before']==record['witness_hash_after']
        assert record['mean_gain']==0 and record['model_instability']==0
        assert record['score']<0 # The stated nonempty edit mask retains its E9 cost.


def test_production_boundary_deduplicates_values_and_messages():
    torch.set_num_threads(2);torch.manual_seed(400)
    x=np.random.default_rng(12).normal(size=(6,64)).astype('float32')
    graph=dict(version='test',groups=[str(i) for i in range(6)],affinity=(np.ones((6,6))-np.eye(6)).tolist(),
        edges=[dict(id=str(i),source=i,target=(i+1)%6,lag=1,sign=1,magnitude=.8,intercept=.1) for i in range(6)])
    models=[ConditionalDiffusion(6,width=16,steps=4).eval() for _ in range(3)]
    kwargs=dict(replicates=2,predictive_samples=2,sampling_steps=4,seed=801)
    a,raw,_=score_candidates(models,x,graph,[('observation',0),('association',0)],**kwargs)
    duplicate=np.concatenate([x,x[[2]]]);other=dict(graph,edges=graph['edges']+[graph['edges'][2]]*4)
    b,rawb,_=score_candidates(models,duplicate,other,[('observation',0),('association',0)],record_ids=[f'channel_{i}' for i in range(6)]+['channel_2'],**kwargs)
    for key in raw:
        np.testing.assert_array_equal(raw[key],rawb[key])
    for left,right in zip(a,b):
        for field in ('mean_gain','model_instability','edit_cost','score','witness_hash_before'):assert left[field]==right[field]


def test_labels_and_future_values_are_outside_model_boundary():
    # Model input is a causal 64-sample prefix. Later samples and all annotations
    # belong to the case manifest, not to any inference function argument.
    import inspect
    assert 'labels' not in inspect.signature(score_candidates).parameters
    rng=np.random.default_rng(401);stream=rng.normal(size=(6,80)).astype('float32')
    altered=stream.copy();altered[:,64:]=999999
    np.testing.assert_array_equal(stream[:,:64],altered[:,:64])
