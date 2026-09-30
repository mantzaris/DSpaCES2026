from pathlib import Path
import sys
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from iot_repair.diffad import DenseS4,select_observations,DiffAD,bicubic_condition,sample


def test_s4_convolution_matches_state_recurrence():
    torch.manual_seed(402);model=DenseS4(3,state=4);x=torch.randn(2,3,16)
    a,b=model.matrices();hidden=torch.zeros(2,3,4);values=[]
    for i in range(x.shape[-1]):
        hidden=torch.einsum('hij,bhj->bhi',a,hidden)+b[None]*x[:,:,i,None]
        values.append((hidden*model.C[None]).sum(-1)+model.D[None]*x[:,:,i])
    expected=torch.stack(values,-1)
    torch.testing.assert_close(model(x),expected,rtol=1e-4,atol=1e-5)
    eigenvalues=torch.linalg.eigvals(a)
    assert (eigenvalues.abs()<1).all()


def test_diffad_conditioning_is_fixed_at_final_step():
    torch.set_num_threads(2);torch.manual_seed(321)
    x=torch.randn(2,4,64);o=torch.ones_like(x,dtype=torch.bool)
    mask=torch.tensor(select_observations(x.numpy()))
    model=DiffAD(4,width=4,steps=3).eval()
    generated=sample(model,x,o,mask,samples=2)
    fixed=mask[:,None].expand_as(generated)
    torch.testing.assert_close(generated[fixed],x[:,None].expand_as(generated)[fixed])
