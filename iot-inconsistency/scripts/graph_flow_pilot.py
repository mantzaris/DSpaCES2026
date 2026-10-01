"""Finite GPU training and production arithmetic pilot, not benchmark evidence."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from iot_repair.graph_flow_model import GraphFlow, build_context
from iot_repair.flow_math import GaussianCorruption, score_candidates, summarize_repairs
from iot_repair.experiment import json_save


def main():
    if not torch.cuda.is_available():
        raise RuntimeError('This stage requires the authorized CUDA GPU')
    torch.set_num_threads(4)
    torch.manual_seed(20261001)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    output = ROOT / 'results/graph_flow_v1'
    (output / 'models').mkdir(parents=True, exist_ok=True)
    (output / 'evidence').mkdir(exist_ok=True)
    processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True)
    other = [line for line in processes.splitlines() if int(line.split(',')[0]) != os.getpid()]
    if other:
        raise RuntimeError('Pilot requires idle GPU. Existing processes: ' + str(other))
    graph = dict(groups=['target','other','context_a','context_b'], edges=[
        dict(source=s, target=0, lag=1, sign=1, training_abs_correlation=.8, validation_gain=.5) for s in (2,3)])
    rng = np.random.default_rng(20261001)
    values = rng.normal(size=(1536,4,64)).astype('float32')
    context_values = rng.normal(size=(1536,2)).astype('float32')
    values[:,2:] = context_values[:,:,None]
    expected_mean = .7 * context_values[:,0] + .4 * context_values[:,1]
    values[:,0,-8:] = expected_mean[:,None] + rng.normal(0,.5,(1536,8))
    tensor = torch.tensor(values,device='cuda')
    inputs = build_context(tensor,torch.zeros(len(tensor),dtype=torch.long,device='cuda'),graph,context_length=32)
    model = GraphFlow(4,width=32,layers=4).cuda()
    validation = torch.arange(1024,1536,device='cuda')
    with torch.no_grad():initial = float(-model.log_prob(tensor[validation,0,-8:],inputs.select(validation)).mean())
    optimizer = torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
    torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
    losses=[]
    for step in range(600):
        indices=torch.randint(0,1024,(128,),device='cuda')
        loss=-model.log_prob(tensor[indices,0,-8:],inputs.select(indices)).mean()
        if not torch.isfinite(loss):raise FloatingPointError('Nonfinite pilot loss')
        optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);optimizer.step()
        if (step+1)%100==0:
            losses.append(dict(step=step+1,training_nll=float(loss)))
            print('Pilot',step+1,float(loss),flush=True)
    torch.cuda.synchronize();training_seconds=time.perf_counter()-start
    model.eval()
    with torch.no_grad():
        final=float(-model.log_prob(tensor[validation,0,-8:],inputs.select(validation)).mean())
        selected=validation[:16];context=inputs.select(selected);encoded=model.encode(context)
        latent=torch.randn((16,2048,8),device='cuda',generator=torch.Generator(device='cuda').manual_seed(813))
        generated=model.sample(encoded,sample_count=2048,latent=latent)
        observed=tensor[selected,0,-8:]+2.
        normal=model.log_prob(observed,encoded)
        channel=GaussianCorruption(8,device='cuda')
        log_q=channel.log_prob(observed,generated)
        evidence=score_candidates(normal[:,None],log_q[:,None])
        repair=summarize_repairs(generated,evidence.weights)
        z,det=model.transform(observed,encoded);back,invdet=model.transform(z,encoded,inverse=True)
        inverse_error=float((back-observed).abs().max())
        mean_mae=float(np.abs(generated.mean(1).cpu().numpy()-expected_mean[selected.cpu().numpy(),None]).mean())
        variance_error=float(np.abs(generated.var(1).cpu().numpy()-.25).mean())
    assert final < initial, 'Pilot failed to learn the simple conditional law'
    assert inverse_error < 1e-4
    path=output/'models/pilot.pt';torch.save(dict(model=model.cpu().state_dict(),configuration=model.configuration),path)
    arrays=output/'evidence/pilot.npz'
    np.savez_compressed(arrays,context_input=values[selected.cpu().numpy()],observed=observed.cpu().numpy(),
                        latent=latent.cpu().numpy(),generated=generated.cpu().numpy(),log_normal=normal.cpu().numpy(),
                        log_corruption=log_q.cpu().numpy(),score=evidence.ratio.cpu().numpy(),
                        weights=evidence.weights.cpu().numpy(),repair_mean=repair['mean'].cpu().numpy())
    # Independent scalar arithmetic uses exactly the saved GPU-produced inputs.
    sys.path.insert(0,str(ROOT/'reference'))
    from reference_graph_flow import corruption_score
    with np.load(arrays) as saved:
        errors=[abs(corruption_score([saved['log_normal'][i]],saved['log_corruption'][i:i+1])-saved['score'][i]) for i in range(16)]
    assert max(errors)<1e-10
    json_save(output/'pilot.json',dict(status='passed',scope='Simple Gaussian training pilot; no H1/H2 benchmark claim',
        model_parameters=sum(p.numel() for p in model.parameters()),steps=600,train_candidates=1024,validation_candidates=512,
        initial_validation_nll=initial,final_validation_nll=final,training_seconds=training_seconds,
        peak_gpu_bytes=torch.cuda.max_memory_allocated(),inverse_max_absolute_error=inverse_error,
        generated_conditional_mean_mae=mean_mae,generated_variance_absolute_error=variance_error,
        sampled_gpu_score_max_absolute_error=max(errors),mean_ess=float(evidence.ess.mean()),
        model_path=str(path.relative_to(ROOT)),model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        evidence_path=str(arrays.relative_to(ROOT)),evidence_sha256=hashlib.sha256(arrays.read_bytes()).hexdigest(),
        losses=losses,environment=dict(torch=torch.__version__,numpy=np.__version__,python=platform.python_version(),
        cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),other_gpu_processes=other),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/iot_repair/graph_flow_model.py','src/iot_repair/flow_math.py', 'scripts/graph_flow_pilot.py']}))
    print('GPU pilot passed',json.dumps(dict(initial_nll=initial,final_nll=final,seconds=training_seconds,score_error=max(errors))),flush=True)


if __name__=='__main__':main()
