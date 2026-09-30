from __future__ import annotations
import copy,sys
from pathlib import Path
import numpy as np
import pytest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from iot_repair.diffusion import ConditionalDiffusion,conditional_sample
from iot_repair.witnesses import select_witnesses,masked_context,canonicalize_records,aggregate_group_losses
from iot_repair.scoring import repair_score,normalized_empirical_crps
from iot_repair.associations import graph_context
from iot_repair.costs import observation_edit_cost
from iot_repair.calibration import null_tail_value


@pytest.fixture
def case():
    torch.manual_seed(42);torch.set_num_threads(2)
    x=torch.randn(1,6,64);o=torch.ones_like(x,dtype=torch.bool)
    g=dict(groups=[str(i) for i in range(6)],affinity=(np.ones((6,6))-np.eye(6)).tolist(),
           edges=[dict(source=i,target=(i+1)%6,lag=1,sign=1,magnitude=.8,intercept=.1) for i in range(6)])
    return x,o,g,ConditionalDiffusion(6,width=16,steps=4).eval()


def test_hidden_witness_values_cannot_affect_proposal(case):
    x,o,g,model=case;p=select_witnesses(0,o[0].numpy(),g)
    forbidden=torch.tensor(p['proposal_forbidden'])[None]
    changed=x.clone();changed[forbidden]=987654.
    a,am=masked_context(x,o,forbidden);b,bm=masked_context(changed,o,forbidden)
    assert torch.equal(a,b) and torch.equal(am,bm)
    left=conditional_sample(model,a,am,g,samples=2,seed=99,sampling_steps=4)
    right=conditional_sample(model,b,bm,g,samples=2,seed=99,sampling_steps=4)
    assert torch.equal(left,right)
    assert not (p['edit_mask'] & p['witness_mask']).any()


def test_upstream_duplicate_invariance_and_conflicts(case):
    x,o,g,model=case;values=x[0].numpy();mask=o[0].numpy();ids=[str(i) for i in range(6)]
    v,m,_=canonicalize_records(np.concatenate([values,values[[2]]]),np.concatenate([mask,mask[[2]]]),ids+['2'])
    assert np.array_equal(v,values) and np.array_equal(m,mask)
    duplicate=torch.tensor(v)[None];forbidden=torch.zeros_like(o);forbidden[...,60:]=True
    context,visible=masked_context(x,o,forbidden);other,_=masked_context(duplicate,o,forbidden)
    assert torch.equal(conditional_sample(model,context,visible,g,2,9,4),conditional_sample(model,other,visible,g,2,9,4))
    conflict=np.concatenate([values,values[[2]]+1])
    with pytest.raises(ValueError):canonicalize_records(conflict,np.concatenate([mask,mask[[2]]]),ids+['2'])


def test_edge_mask_keeps_witness_terms_and_attributes_executable(case):
    x,o,g,model=case;p=select_witnesses(0,o[0].numpy(),g,kind='association')
    frozen=copy.deepcopy(p);edited=copy.deepcopy(g);edited['edges']=edited['edges'][1:]
    losses=aggregate_group_losses(torch.ones(3,8,6,64),p)
    assert losses.shape==(3,8,len(p['groups']))
    assert p['witness_hash']==frozen['witness_hash'] and np.array_equal(p['witness_mask'],frozen['witness_mask'])
    original,_=graph_context(x,o,g);removed,_=graph_context(x,o,edited)
    assert not torch.equal(original,removed)
    signed=copy.deepcopy(g);signed['edges'][0]['sign']=-1
    lagged=copy.deepcopy(g);lagged['edges'][0]['lag']=3
    assert not torch.equal(original,graph_context(x,o,signed)[0])
    assert not torch.equal(original,graph_context(x,o,lagged)[0])


def test_invalid_loss_abstains_and_penalties():
    before=torch.ones(2,5,3,8,2,dtype=torch.float64);after=before*.5;w=torch.tensor([.5,.5],dtype=torch.float64)
    a=repair_score(before,after,w,.1);b=repair_score(before,after,w,.3)
    torch.testing.assert_close(a['score']-b['score'],torch.full((2,5),.04,dtype=torch.float64))
    assert (repair_score(before,before+.2,w,0)['score']<0).all()
    assert (repair_score(before,before,w,0)['score']==0).all()
    broken=after.clone();broken[0,0,0,0,0]=float('nan')
    with pytest.raises(ValueError):repair_score(before,broken,w,0)
    with pytest.raises(ValueError):repair_score(before[:,:,:1],after[:,:,:1],w,0)


def test_null_tail_ties_resolution_and_direction():
    a=np.array([0.,.1,.1,.2,.4]);queries=np.array([-.1,.1,.5])
    np.testing.assert_allclose(null_tail_value(a,queries),[1.,5/6,1/6])


def test_missing_edit_is_not_numeric(case):
    x,o,_,_=case;edit=torch.zeros_like(o);edit[0,0,-1]=True;o[0,0,-1]=False
    with pytest.raises(ValueError):observation_edit_cost(x,x[:,None,None].expand(-1,3,8,-1,-1),edit,o)


def test_crps_pairwise_and_unit_change():
    rng=np.random.default_rng(402);s=torch.tensor(rng.normal(size=(7,11)),dtype=torch.float64)
    y=torch.tensor(rng.normal(size=7),dtype=torch.float64)
    expected=(s-y[:,None]).abs().mean(-1)-.5*(s[:,:,None]-s[:,None,:]).abs().mean((-2,-1))
    torch.testing.assert_close(normalized_empirical_crps(s,y),expected)
    torch.testing.assert_close(normalized_empirical_crps(-3*s+7,-3*y+7,3.),expected)
