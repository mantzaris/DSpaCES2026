"""Independent production replay with explicit float64 ensemble density arithmetic.

Supersedes the first audit only. Model weights, predictions, calibrators, scores
and the original protocol lock are unchanged. The frozen scorer already casts
normal log densities to float64 before ensemble reduction. SciPy otherwise keeps
a loaded float32 array in float32, which caused the first audit to compare two
different precision paths. See results/graph_flow_v1/audit_precision_correction.json.
"""
from pathlib import Path
import json
import sys
import numpy as np
import torch
from scipy.special import logsumexp
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from iot_repair.flow_data import graph_for,sha256
from iot_repair.flow_training import load_flow
from iot_repair.flow_math import GaussianCorruption
from iot_repair.graph_flow_model import build_context
from iot_repair.experiment import json_save

def audit_production(root):
    root=Path(root);directory=root/'results/graph_flow_v1';lock=json.loads((directory/'protocol_lock.json').read_text());summary=[];total=0;max_error=0.
    for dataset in lock['configuration']['datasets']:
        selection=lock['choices'][dataset];models=[load_flow(root,r) for r in selection['members']['members']];graph=graph_for(root,dataset)
        for split in ('calibration','test'):
            for path in sorted((directory/dataset/split).glob('*.npz')):
                raw=dict(np.load(path,allow_pickle=False));normal=raw['audit_log_normal_members'].astype(np.float64)
                if not len(normal):continue
                fault=logsumexp(raw['audit_log_fault_components']-np.log(4),axis=1)
                expected=fault-(logsumexp(normal,axis=1)-np.log(3))
                error=float(np.max(np.abs(expected-raw['audit_score'])));max_error=max(error,max_error);total+=len(expected)
                assert error<1e-7
            for path in sorted((directory/'evidence').glob(dataset+'_'+split+'_*.npz')):
                raw=dict(np.load(path,allow_pickle=False));values=torch.tensor(raw['input'],device='cuda')
                if not len(raw['query']):
                    summary.append(dict(path=str(path.relative_to(root)),sha256=sha256(path),candidates=0,status='all targets unavailable, no numeric density evaluated'))
                    continue
                query=torch.tensor(raw['query'],device='cuda');target=values[query,-8:]
                inputs=build_context(values[None].expand(len(query),-1,-1),query,graph,selection['models']['selected']['specification']['context_length'])
                generation_error=0.;density_error=0.;inverse_error=0.;jacobian_error=0.
                with torch.no_grad():
                    for member,model in enumerate(models):
                        encoded=model.encode(inputs);latent=torch.tensor(raw['latent'][:,member],device='cuda')
                        generated=model.sample(encoded,sample_count=latent.shape[1],latent=latent,chunk=128)
                        generation_error=max(generation_error,float(np.max(np.abs(generated.cpu().numpy()-raw['generated'][:,member]))))
                        density_error=max(density_error,float(np.max(np.abs(model.log_prob(target,encoded).cpu().numpy()-raw['log_normal_members'][:,member]))))
                        transformed,_=model.transform(target,encoded);restored,_=model.transform(transformed,encoded,inverse=True)
                        inverse_error=max(inverse_error,float((restored-target).abs().max()))
                # E5 independently evaluated with NumPy Cholesky, not the Torch kernel.
                channel=GaussianCorruption(8,scale=float(raw['corruption_scale']),times=raw['target_times']);generated=raw['generated'].astype(float)
                components=[]
                for mapping,covariance in zip(channel.maps,channel.covariance.numpy()):
                    difference=raw['input'][raw['query'],-8:][:,None,None]-np.einsum('ij,bemj->bemi',mapping,generated)
                    cholesky=np.linalg.cholesky(covariance)
                    whitened=np.linalg.solve(cholesky,difference.reshape(-1,8).T).T.reshape(difference.shape)
                    components.append(-.5*(np.square(whitened).sum(-1)+2*np.log(np.diag(cholesky)).sum()+8*np.log(2*np.pi)))
                log_q=logsumexp(np.stack(components,-1)-np.log(4),axis=-1)
                q_error=float(np.max(np.abs(log_q-raw['log_corruption'])))
                expected=logsumexp(log_q.reshape(len(query),-1),axis=1)-np.log(log_q.shape[1]*log_q.shape[2])
                expected-=logsumexp(raw['log_normal_members'].astype(np.float64),axis=1)-np.log(3)
                score_error=float(np.max(np.abs(expected-raw['score'])))
                weights=np.exp(log_q.reshape(len(query),-1)-logsumexp(log_q.reshape(len(query),-1),axis=1,keepdims=True))
                repair=(weights[...,None]*generated.reshape(len(query),-1,8)).sum(1)
                repair_error=float(np.max(np.abs(repair-raw['posterior_mean'])))
                # Autograd determinant from an actually trained flow on the GPU.
                import copy
                audit_model=copy.deepcopy(models[0]).double()
                with torch.no_grad():encoded=models[0].encode(inputs).detach()[:1].double()
                point=target[0].double().detach().requires_grad_(True)
                jacobian=torch.autograd.functional.jacobian(lambda y:audit_model.transform(y[None],encoded)[0][0],point)
                determinant=audit_model.transform(point[None],encoded)[1][0]
                jacobian_error=float((torch.linalg.slogdet(jacobian)[1]-determinant).abs())
                del audit_model
                assert generation_error<1e-4 and density_error<1e-4 and q_error<1e-6 and score_error<1e-6 and repair_error<1e-6
                assert jacobian_error<1e-8
                summary.append(dict(path=str(path.relative_to(root)),sha256=sha256(path),generated_max_error=generation_error,
                    normal_density_max_error=density_error,corruption_density_max_error=q_error,ratio_max_error=score_error,
                    repair_mean_max_error=repair_error,inverse_max_error=inverse_error,autograd_logdet_error=jacobian_error,candidates=len(query)))
        del models;torch.cuda.empty_cache()
    record=dict(compact_candidate_scores_recomputed=total,compact_max_error=max_error,full_generation_and_density_replays=summary,
                distinction='All compact scores recomputed from saved component integrals. Listed full bundles independently recompute q from actual generations and replay generations/densities from exact GPU weights and saved latent draws.')
    json_save(directory/'production_equation_audit.json',record);return record

if __name__=='__main__':
    torch.set_num_threads(4)
    audit_production(ROOT)
