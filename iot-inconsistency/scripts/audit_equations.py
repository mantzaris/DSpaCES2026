"""Save common input arrays once, compare independent reference and Torch kernels."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from iot_repair.scoring import normalized_empirical_crps, repair_score
from iot_repair.costs import observation_edit_cost, association_edit_cost
from iot_repair.calibration import null_tail_value


def main():
    p=argparse.ArgumentParser(); p.add_argument('--device',default='cpu'); args=p.parse_args()
    out=ROOT/'results/audits'; out.mkdir(parents=True,exist_ok=True)
    fixture=out/'arithmetic_inputs.npz'
    if not fixture.exists():
        rng=np.random.default_rng(9026)
        np.savez_compressed(fixture,before=rng.uniform(.5,2,(2,5,3,8,4)),
            after=rng.uniform(.1,1.6,(2,5,3,8,4)),weights=np.array([.1,.2,.3,.4]),
            samples=rng.normal(size=(2,5,7,16)),observed=rng.normal(size=(2,5,7)),
            scales=rng.uniform(.5,2,(2,5,7)),costs=rng.uniform(0,1,(2,5)),null=rng.normal(size=129))
    a=dict(np.load(fixture)); spec=importlib.util.spec_from_file_location('reference',ROOT/'reference/reference_score.py')
    reference=importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    report={'device':args.device,'torch':torch.__version__,'input_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'axes':['batch','candidate','ensemble_member','paired_replicate','provenance_group'], 'checks':[]}
    for dtype,tol in [(torch.float64,1e-11),(torch.float32,2e-6)]:
        tensors={k:torch.as_tensor(v,dtype=dtype,device=args.device) for k,v in a.items()}
        crps=normalized_empirical_crps(tensors['samples'],tensors['observed'],tensors['scales'])
        expected=reference.normalized_empirical_crps(a['samples'],a['observed'],a['scales'])
        np.testing.assert_allclose(crps.cpu().numpy(),expected,rtol=tol,atol=tol)
        result=repair_score(tensors['before'],tensors['after'],tensors['weights'],tensors['costs'])
        max_error=0.
        for b in range(2):
            for c in range(5):
                r=reference.repair_score(a['before'][b,c],a['after'][b,c],a['weights'],a['costs'][b,c])
                for key,val in r.items():
                    actual=result[key][b,c].item(); np.testing.assert_allclose(actual,val,rtol=tol,atol=tol)
                    max_error=max(max_error,abs(actual-val))
        original=torch.tensor([[1.,2.],[3.,4.]],dtype=dtype,device=args.device)
        replacement=original[None,None].repeat(3,8,1,1)+.4
        mask=torch.ones_like(original,dtype=torch.bool)
        cost=observation_edit_cost(original,replacement,mask,mask,2.)
        converted=observation_edit_cost(-3*original+7,-3*replacement+7,mask,mask,6.)
        torch.testing.assert_close(cost,converted,rtol=tol,atol=tol)
        np.testing.assert_allclose(cost.item(),.5+.5*.4/6,rtol=tol,atol=tol)
        assert association_edit_cost(1,4)==.25
        pvalues=null_tail_value(tensors['null'],result['score'])
        expected_p=np.array([[reference.null_tail_value(a['null'],v) for v in row] for row in result['score'].cpu().numpy()])
        np.testing.assert_allclose(pvalues.cpu().numpy(),expected_p,atol=tol,rtol=tol)
        report['checks'].append({'dtype':str(dtype),'tolerance':tol,'max_score_component_error':max_error,
            'crps':True,'score_components':True,'edit_cost_unit_invariance':True,'null_tails':True})
    if args.device.startswith('cuda'):
        report['gpu']=torch.cuda.get_device_name(); report['cuda']=torch.version.cuda
    report['status']='passed'
    (out/('parity_'+args.device.replace(':','_')+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
