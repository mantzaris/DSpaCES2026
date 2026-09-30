from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from iot_repair.faults import inject_association
from iot_repair.experiment import build_cases
from iot_repair.metrics import summarize


def test_edge_attribute_permutations_preserve_metadata_and_degrees():
    graph=dict(version='original',groups=list(range(6)),affinity=np.zeros((6,6)).tolist(),edges=[
        dict(id=str(i),source=i,target=(i+1)%6,sign=(-1)**i,lag=1+i%3,magnitude=1+i*.1,intercept=.1*i) for i in range(6)])
    for family in ['wrong_endpoint','wrong_lag','wrong_sign','unsupported','stale']:
        changed,truth,meta=inject_association(graph,401,family)
        assert meta['status']=='injected' and truth.sum()==2
        assert changed['version']!=graph['version']
        for field in ['source','target','sign','lag','magnitude','intercept']:
            assert sorted(e[field] for e in changed['edges'])==sorted(e[field] for e in graph['edges'])


def test_screening_misses_stay_in_attribution_denominator():
    cases=[]
    for i in range(4):
        cases.append(dict(id=str(i),track='observation',fault={'status':'injected','family':'offset'},block=str(i),observation_truth=[True,False],records=[dict(kind='observation',index=1,support_count=2,mean_gain=1.,model_instability=.1,edit_cost=.1)]))
    result=summarize(cases,'proposed','observation',{'kappa':1,'lambda':.2})
    assert result['top1']==0 and result['screening_recall']==0
