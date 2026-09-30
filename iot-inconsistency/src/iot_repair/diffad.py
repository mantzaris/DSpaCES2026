"""Independent DiffAD paper implementation, with explicit adaptation choices.

Implements density-ratio point selection (paper E1--E4), bicubic conditioning,
weight-incremental sampling (E5--E11), multi-scale structured state-space U-Net,
and reconstruction scoring (E12). Uses a dense DPLR S4 kernel instead of its
Cauchy acceleration. Reference: Xiao et al., KDD 2023, doi:10.1145/3580305.3599391.
No unlicensed author source is copied or distributed.
"""
from __future__ import annotations
import math
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


def select_observations(x,fraction=.12,segment=8):
    """Diagonal Gaussian plug-in density ratios, fixed 1e-3 variance floor.

    The paper leaves the density estimator unspecified. Distances are recomputed
    greedily after each selected point, with a 1e-6 denominator for zero CHG.
    This is a score for ordering, not a calibrated probability.
    """
    x=np.asarray(x);b,c,t=x.shape;all_masks=[]
    for row in x:
        complete=np.isfinite(row);filled=np.where(complete,row,0.)
        changes=np.zeros(t)
        for stop in range(2*segment,t+1,segment):
            old=filled[:,stop-2*segment:stop-segment];new=filled[:,stop-segment:stop]
            mean_old=old.mean(-1);mean_new=new.mean(-1)
            var_old=old.var(-1)+1e-3;var_new=new.var(-1)+1e-3
            log_old=-.5*(np.log(var_old[:,None])+(new-mean_old[:,None])**2/var_old[:,None])
            log_new=-.5*(np.log(var_new[:,None])+(new-mean_new[:,None])**2/var_new[:,None])
            ratio=np.exp(np.clip((log_old-log_new).sum(0),-20,20))
            changes[stop-segment:stop]=max(0.,.5-float(ratio.mean()))
        threshold=np.quantile(changes,.3);allowed=(changes<=threshold)&complete.any(0)
        chosen=[]
        for _ in range(max(2,int(round(t*fraction)))):
            distance=np.min(np.abs(np.arange(t)[:,None]-np.array(chosen)[None]),axis=1) if chosen else np.arange(t)+1
            score=distance*(1-changes+changes.mean())/np.maximum(changes,1e-6)
            score[~allowed]=-np.inf
            if chosen:score[chosen]=-np.inf
            if not np.isfinite(score).any():break
            chosen.append(int(np.argmax(score)))
        mask=np.zeros((c,t),dtype=bool);mask[:,chosen]=complete[:,chosen]
        all_masks.append(mask)
    return np.stack(all_masks)


class DenseS4(nn.Module):
    """Stable normal-plus-rank-one HiPPO state matrix and exact bilinear kernel."""
    def __init__(self,width,state=8):
        super().__init__();self.width=width;self.state=state
        q=torch.sqrt(2*torch.arange(state,dtype=torch.float32)+1)
        hippo=-torch.tril(q[:,None]*q[None,:],diagonal=-1)-torch.diag(torch.arange(1,state+1,dtype=torch.float32))
        self.skew=nn.Parameter(((hippo-hippo.T)/2)[None].repeat(width,1,1))
        self.rank=nn.Parameter((q/math.sqrt(2))[None].repeat(width,1))
        self.damping=nn.Parameter(torch.full((width,),math.log(math.expm1(.5))))
        self.log_dt=nn.Parameter(torch.linspace(math.log(.01),math.log(.1),width))
        self.B=nn.Parameter(q[None].repeat(width,1));self.C=nn.Parameter(torch.randn(width,state)/math.sqrt(state))
        self.D=nn.Parameter(torch.ones(width));self._cache=None
    def matrices(self):
        eye=torch.eye(self.state,device=self.B.device)[None]
        skew=(self.skew-self.skew.transpose(-2,-1))/2
        a=skew-F.softplus(self.damping)[:,None,None]*eye-self.rank[:,:,None]*self.rank[:,None,:]
        dt=self.log_dt.exp()[:,None,None]
        left=eye-dt*a/2
        discrete=torch.linalg.solve(left,eye+dt*a/2)
        b=torch.linalg.solve(left,dt*self.B[:,:,None]).squeeze(-1)
        return discrete,b
    def kernel(self,length):
        if not self.training and self._cache is not None and self._cache.shape[-1]==length:return self._cache
        a,b=self.matrices();states=b[:,:,None];power=a
        while states.shape[-1]<length:
            states=torch.cat([states,power@states],dim=-1);power=power@power
        kernel=(states[...,:length]*self.C[:,:,None]).sum(1)
        if not self.training:self._cache=kernel.detach()
        return kernel
    def train(self,mode=True):
        self._cache=None;return super().train(mode)
    def forward(self,x):
        with torch.autocast(device_type=x.device.type,enabled=False):
            k=self.kernel(x.shape[-1]);size=2*x.shape[-1]
            y=torch.fft.irfft(torch.fft.rfft(x.float(),n=size)*torch.fft.rfft(k,n=size)[None],n=size)[...,:x.shape[-1]]
            return y+self.D[None,:,None]*x.float()


class S4Block(nn.Module):
    def __init__(self,width):
        super().__init__();self.norm=nn.GroupNorm(1,width);self.s4=DenseS4(width)
        self.mix=nn.Conv1d(width,width,1);self.time=nn.Linear(32,width)
    def forward(self,x,time):
        y=self.norm(x)+self.time(time)[:,:,None]
        return x+self.mix(F.gelu(self.s4(y)))


class DiffAD(nn.Module):
    def __init__(self,channels,width=32,steps=100):
        super().__init__();self.channels=channels;self.steps=steps
        self.input=nn.Conv1d(2*channels,width,1)
        self.down=nn.ModuleList([nn.Conv1d(width,width*2,4,stride=2,padding=1),nn.Conv1d(width*2,width*4,4,stride=2,padding=1)])
        self.blocks=nn.ModuleList([S4Block(width),S4Block(width*2),S4Block(width*4),S4Block(width*2),S4Block(width)])
        self.up=nn.ModuleList([nn.Conv1d(width*6,width*2,1),nn.Conv1d(width*3,width,1)])
        self.output=nn.Conv1d(width,channels,1)
        beta=torch.linspace(1e-6,1e-2,steps);alpha=1-beta;ab=torch.cumprod(alpha,0)
        self.register_buffer('beta',beta);self.register_buffer('alpha',alpha);self.register_buffer('alpha_bar',ab)
        self.register_buffer('frequencies',torch.exp(torch.linspace(0,-math.log(10000),16)))
    def forward(self,x,conditioning,step):
        angle=step[:,None].to(x.dtype)*self.frequencies[None]
        time=torch.cat([angle.sin(),angle.cos()],-1)
        h=self.blocks[0](self.input(torch.cat([x,conditioning],1)),time);skip0=h
        h=self.blocks[1](self.down[0](h),time);skip1=h
        h=self.blocks[2](self.down[1](h),time)
        h=self.blocks[3](self.up[0](torch.cat([F.interpolate(h,size=skip1.shape[-1]),skip1],1)),time)
        h=self.blocks[4](self.up[1](torch.cat([F.interpolate(h,size=skip0.shape[-1]),skip0],1)),time)
        return self.output(h)


def bicubic_condition(values,selected):
    result=[]
    for row,mask in zip(values,selected):
        indices=torch.where(mask.any(0))[0]
        if not len(indices):result.append(torch.zeros_like(row));continue
        observed=torch.where(mask,row,torch.zeros_like(row))[:,indices]
        result.append(F.interpolate(observed[None,None],size=row.shape,mode='bicubic',align_corners=False)[0,0])
    return torch.stack(result)


def diffusion_loss(model,values,available,conditioning):
    step=torch.randint(model.steps,(len(values),),device=values.device)
    alpha=model.alpha_bar[step,None,None];noise=torch.randn_like(values)
    noisy=alpha.sqrt()*values+(1-alpha).sqrt()*noise
    predicted=model(noisy,conditioning,step)
    squared=(predicted-noise).float().square()
    return torch.where(available,squared,torch.zeros_like(squared)).sum()/available.sum().clamp_min(1)


@torch.no_grad()
def sample(model,values,available,selected,samples=8,seed=9026):
    """Full 100-step sampler. Exponential weight follows the paper integer reverse-step index."""
    conditioning=bicubic_condition(values,selected)
    b,c,t=values.shape;repeat=lambda a:a[:,None].expand(-1,samples,-1,-1).reshape(b*samples,c,t)
    condition=repeat(conditioning);observations=repeat(values);mask=repeat(selected)
    rng=torch.Generator(device=values.device).manual_seed(seed)
    noise=torch.randn(condition.shape,device=values.device,generator=rng)
    state=torch.where(mask,observations,.9*condition+.1*noise)
    for step in reversed(range(model.steps)):
        with torch.autocast(device_type=state.device.type,dtype=torch.bfloat16,
                            enabled=state.device.type=='cuda' and getattr(model,'inference_autocast',False)):
            predicted=model(state,condition,torch.full((b*samples,),step,device=values.device))
        mean=(state-model.beta[step]/(1-model.alpha_bar[step]).sqrt()*predicted)/model.alpha[step].sqrt()
        if step:
            variance=model.beta[step]*(1-model.alpha_bar[step-1])/(1-model.alpha_bar[step])
            mean=mean+variance.sqrt()*torch.randn(state.shape,device=state.device,generator=rng)
        weight=math.exp(-25*step)
        state=torch.where(mask,(1-weight)*mean+weight*observations,mean)
    return state.reshape(b,samples,c,t)
