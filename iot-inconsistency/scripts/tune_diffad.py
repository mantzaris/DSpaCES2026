"""Equal-size development search for the DiffAD adaptation learning rate."""
from pathlib import Path
import json,sys,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.diffad import DiffAD,select_observations,bicubic_condition,diffusion_loss
from iot_repair.experiment import json_save
torch.set_num_threads(4)
for name in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    out=ROOT/'results/models'/name/'diffad_selection.json'
    if out.exists():continue
    tr=np.load(ROOT/'data/processed'/name/'train.npz')['x'];dev=np.load(ROOT/'data/processed'/name/'development.npz');d=dev['x'][dev['reference']][:48]
    train=torch.as_tensor(tr,device='cuda');validation=torch.as_tensor(d,device='cuda')
    mask=torch.isfinite(train);vmask=torch.isfinite(validation);train=torch.nan_to_num(train);validation=torch.nan_to_num(validation)
    with torch.no_grad():
        condition=bicubic_condition(train,torch.as_tensor(select_observations(tr),device='cuda'))
        vc=bicubic_condition(validation,torch.as_tensor(select_observations(d),device='cuda'))
    rows=[]
    for rate in [3e-6,3e-4,1e-3]:
        torch.manual_seed(8811);model=DiffAD(train.shape[1]).cuda();opt=torch.optim.Adam(model.parameters(),lr=rate);start=time.perf_counter()
        for step in range(500):
            idx=torch.randint(len(train),(32,),device='cuda');opt.zero_grad(set_to_none=True)
            loss=diffusion_loss(model,train[idx],mask[idx],condition[idx]);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step()
        model.eval();torch.manual_seed(224466)
        with torch.no_grad():validation_loss=float(diffusion_loss(model,validation,vmask,vc))
        rows.append(dict(learning_rate=rate,steps=500,validation_masked_noise_mse=validation_loss,elapsed_seconds=time.perf_counter()-start))
        print(name,rows[-1],flush=True)
    json_save(out,dict(selected_learning_rate=min(rows,key=lambda r:r['validation_masked_noise_mse'])['learning_rate'],grid=rows,
        adaptation='paper learning rate included, common fixed window and independent dense S4 implementation'))
