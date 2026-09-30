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
