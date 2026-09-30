"""Export exact inference state arrays without optimizer or pickle dependencies."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import json_save
out=ROOT/'results/model_weights';out.mkdir(parents=True,exist_ok=True);manifest=[]
for directory in sorted((ROOT/'results/models').iterdir()):
    for checkpoint in sorted(directory.glob('*.pt')):
        saved=torch.load(checkpoint,map_location='cpu',weights_only=False);target=out/directory.name/(checkpoint.stem+'.npz');target.parent.mkdir(exist_ok=True)
        arrays={key:value.detach().cpu().numpy() for key,value in saved['model'].items()}
        if not target.exists():np.savez_compressed(target,**arrays)
        reloaded=np.load(target)
        for key,value in arrays.items():np.testing.assert_array_equal(value,reloaded[key])
        manifest.append(dict(dataset=directory.name,model=checkpoint.stem,path=str(target.relative_to(ROOT)),bytes=target.stat().st_size,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(),source_checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            configuration=saved['config'],training_step=saved['step'],training_data_sha256=saved['training_data_sha256'],graph_version=saved['graph_version'],
            arrays={key:dict(shape=list(value.shape),dtype=str(value.dtype)) for key,value in arrays.items()},export_equality='exact array equality'))
json_save(out/'manifest.json',dict(models=manifest,total_bytes=sum(r['bytes'] for r in manifest)))
print('Exported',len(manifest),'exact inference states, bytes',sum(r['bytes'] for r in manifest))
