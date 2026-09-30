from pathlib import Path
import json,sys,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.diffusion import ConditionalDiffusion
from iot_repair.pipeline import score_candidates
from iot_repair.faults import inject_observation
torch.set_num_threads(4)
directory=ROOT/'results/models/synthetic_32_nonlinear'
graph=json.loads((directory/'graph.json').read_text())
models=[]
for seed in [9001,9002,9003]:
    saved=torch.load(directory/f'diffusion_{seed}.pt',map_location='cuda',weights_only=False)
    model=ConditionalDiffusion(32,width=saved['config']['width']).cuda().eval();model.load_state_dict(saved['model']);models.append(model)
x=np.load(ROOT/'data/processed/synthetic_32_nonlinear/development.npz')['x'][0]
x,truth,fault=inject_observation(x,4001,family='offset')
torch.cuda.reset_peak_memory_stats()
records,raw,abstentions=score_candidates(models,x,graph,[('observation',i) for i in range(4)]+[('association',i) for i in range(4)],seed=9001)
out=ROOT/'results/pilot';out.mkdir(exist_ok=True)
np.savez_compressed(out/'inference_raw.npz',input=x,truth=truth,**raw)
report=dict(records=records,abstentions=abstentions,fault=fault,scope='200-step pilot, not final detection evidence',
    gpu=torch.cuda.get_device_name(),parameters=sum(p.numel() for p in models[0].parameters()),
    peak_vram_bytes=torch.cuda.max_memory_allocated(),elapsed_seconds=sum(r['elapsed_seconds_per_candidate'] for r in records))
(out/'inference.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['records','fault']},indent=2))
for model in models:model.inference_autocast=True
torch.cuda.reset_peak_memory_stats()
amp_records,amp_raw,amp_abstentions=score_candidates(models,x,graph,[('observation',i) for i in range(4)]+[('association',i) for i in range(4)],seed=9001)
reference={(r['kind'],r['index']):r for r in records}
comparison=dict(scope='neural inference dtype pilot; arithmetic accumulation is float64 in both',
    elapsed_seconds=sum(r['elapsed_seconds_per_candidate'] for r in amp_records),
    peak_vram_bytes=torch.cuda.max_memory_allocated(),
    max_score_change=max(abs(r['score']-reference[r['kind'],r['index']]['score']) for r in amp_records),
    records=amp_records)
(out/'inference_mixed_precision.json').write_text(json.dumps(comparison,indent=2)+'\n')
np.savez_compressed(out/'inference_mixed_precision_raw.npz',input=x,truth=truth,**amp_raw)
print(json.dumps({k:v for k,v in comparison.items() if k!='records'},indent=2))
