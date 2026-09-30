"""Independent NumPy GDN operation audit and trained S4 stability checks."""
from pathlib import Path
import json,sys
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save
from iot_repair.diffad import DenseS4

def numpy_gdn(model,values):
    state={k:v.detach().cpu().numpy().astype('float64') for k,v in model.state_dict().items()}
    emb=state['embedding.weight'];norm=emb/np.linalg.norm(emb,axis=1,keepdims=True);sim=norm@norm.T
    neighbors=np.argsort(-sim,axis=1)[:,:model.topk];hidden=values@state['projection.weight'].T;messages=np.zeros_like(hidden)
    for batch in range(len(values)):
      for target in range(values.shape[1]):
        adjacent=sorted(set(neighbors[target].tolist()+[target]));logits=[]
        for source in adjacent:
            score=hidden[batch,target]@state['attention_i']+hidden[batch,source]@state['attention_j']+emb[target]@state['attention_embedding_i']+emb[source]@state['attention_embedding_j']
            logits.append(max(score,.2*score))
        p=np.exp(np.array(logits)-max(logits));p/=p.sum();messages[batch,target]=np.sum(p[:,None]*hidden[batch,adjacent],axis=0)+state['bias']
    def bn(x,prefix):return (x-state[prefix+'.running_mean'])/np.sqrt(state[prefix+'.running_var']+1e-5)*state[prefix+'.weight']+state[prefix+'.bias']
    output=np.maximum(bn(messages,'bn_graph'),0)*emb
    output=np.maximum(bn(output,'bn_output'),0)
    return (output@state['head.weight'].T+state['head.bias'])[...,0]

reports=[];torch.set_num_threads(4)
for dataset in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    models,_=load_models(ROOT,dataset,('gdn','diffad'),device='cpu');x=np.nan_to_num(np.load(ROOT/'data/processed'/dataset/'development.npz')['x'][:3,:,:56])
    for seed,model in zip([1101,2202,3303],models['gdn']):
        with torch.no_grad():actual=model(torch.tensor(x)).numpy()
        expected=numpy_gdn(model,x.astype('float64'));np.testing.assert_allclose(actual,expected,atol=2e-5,rtol=2e-5)
        reports.append(dict(dataset=dataset,model='GDN',seed=seed,max_absolute_error=float(np.max(np.abs(actual-expected))),reference='independent per-edge attention and batch-normalization calculation'))
    for seed,model in zip([1101,2202,3303],models['diffad']):
        maxima=[]
        for module in model.modules():
            if isinstance(module,DenseS4):
                with torch.no_grad():a,b=module.matrices();maxima.append(float(torch.linalg.eigvals(a).abs().max()))
        assert max(maxima)<1.00001
        reports.append(dict(dataset=dataset,model='DiffAD adaptation',seed=seed,maximum_discrete_pole_radius=max(maxima)))
json_save(ROOT/'results/audits/trained_models.json',dict(checks=reports))
print('Audited',len(reports),'trained comparator members')
