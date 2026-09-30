"""E2. Conditional DDPM objective and batched DDIM predictive draws.

Context encoding is cached only when all conditioning values/masks/graph agree.
Replicate noise remains independent. The generator API accepts no truth labels.
"""
from __future__ import annotations
import math
import torch
from torch import nn
from .associations import graph_context


def schedule(steps):
    grid=torch.arange(steps+1,dtype=torch.float64)/steps
    cumulative=torch.cos((grid+.008)/1.008*math.pi/2)**2
    cumulative=cumulative/cumulative[0]
    beta=(1-cumulative[1:]/cumulative[:-1]).clamp(max=.999)
    return torch.cumprod(1-beta,0).float()


class ConditionalDiffusion(nn.Module):
    def __init__(self,channels,window=64,width=128,steps=32):
        super().__init__();self.window=window;self.width=width;self.steps=steps
        self.embedding=nn.Embedding(channels,16)
        self.encoder=nn.Sequential(nn.Linear(4*window+16,width),nn.SiLU(),nn.Linear(width,width),nn.SiLU())
        self.denoiser=nn.Sequential(nn.Linear(window+width+32,width*2),nn.SiLU(),
            nn.Linear(width*2,width*2),nn.SiLU(),nn.Linear(width*2,width*2),nn.SiLU(),nn.Linear(width*2,window))
        self.register_buffer('alpha_bar',schedule(steps))
        self.register_buffer('frequencies',torch.exp(torch.linspace(0,-math.log(10000),16)))
    def encode(self,context,observed,graph,dropout=0.):
        if not torch.isfinite(context).all(): raise ValueError('Context must be finite with an explicit mask')
        context=torch.where(observed,context,torch.zeros_like(context))
        predicted,valid=graph_context(context,observed,graph,dropout)
        emb=self.embedding.weight[None].expand(len(context),-1,-1)
        return self.encoder(torch.cat([context,observed.to(context.dtype),predicted,valid.to(context.dtype),emb],-1))
    def predict_noise(self,noisy_target,step,encoding):
        angle=step[:,None].to(noisy_target.dtype)*self.frequencies[None]
        time=torch.cat([angle.sin(),angle.cos()],-1)[:,None].expand(-1,noisy_target.shape[1],-1)
        return self.denoiser(torch.cat([noisy_target,encoding,time],-1))


def masked_denoising_loss(model,values,observed,target_mask,graph,edge_dropout=.15):
    target=target_mask & observed
    context_mask=observed & ~target
    context=torch.where(context_mask,values,torch.zeros_like(values))
    encoding=model.encode(context,context_mask,graph,edge_dropout)
    steps=torch.randint(model.steps,(len(values),),device=values.device)
    alpha=model.alpha_bar[steps,None,None]
    noise=torch.randn_like(values)
    clean=torch.where(target,values,torch.zeros_like(values))
    noisy=(alpha.sqrt()*clean+(1-alpha).sqrt()*noise)*target
    predicted=model.predict_noise(noisy,steps,encoding)
    # Squaring follows masking, and each batch unit has its own observed count.
    squared=torch.where(target,(noise-predicted).float().square(),torch.zeros_like(predicted,dtype=torch.float32))
    return (squared.sum((-2,-1))/target.sum((-2,-1)).clamp_min(1)).mean()


@torch.no_grad()
def conditional_sample(model,context,context_mask,graph,samples=8,seed=0,sampling_steps=12,
                       encoding=None,initial_noise=None):
    """Output [batch,sample,channel,time], with known context exactly preserved."""
    if encoding is None: encoding=model.encode(context,context_mask,graph)
    b,c,t=context.shape
    cached=encoding[:,None].expand(-1,samples,-1,-1).reshape(b*samples,c,-1)
    visible=context_mask[:,None].expand(-1,samples,-1,-1).reshape(b*samples,c,t)
    fixed=context[:,None].expand(-1,samples,-1,-1).reshape(b*samples,c,t)
    rng=torch.Generator(device=context.device).manual_seed(seed)
    state=torch.randn((b*samples,c,t),device=context.device,generator=rng) if initial_noise is None else initial_noise.reshape(b*samples,c,t).clone()
    state=state.masked_fill(visible,0)
    grid=torch.linspace(model.steps-1,0,min(sampling_steps,model.steps),device=context.device).long().unique(sorted=True).flip(0)
    for index,step in enumerate(grid):
        level=step.expand(b*samples)
        with torch.autocast(device_type=state.device.type,dtype=torch.bfloat16,
                            enabled=state.device.type=='cuda' and getattr(model,'inference_autocast',False)):
            noise=model.predict_noise(state,level,cached)
        alpha=model.alpha_bar[step]
        clean=(state-(1-alpha).sqrt()*noise)/alpha.sqrt()
        clean=clean.clamp(-12,12)
        if index+1<len(grid):
            previous=model.alpha_bar[grid[index+1]]
            state=previous.sqrt()*clean+(1-previous).sqrt()*noise
        else: state=clean
        state=state.masked_fill(visible,0)
    return torch.where(visible,fixed,state).reshape(b,samples,c,t)


def training_target_mask(observed):
    b,c,t=observed.shape
    channel=torch.rand((b,c,1),device=observed.device)<.2
    tail=torch.arange(t,device=observed.device)[None,None,:]>=t-torch.randint(4,25,(b,1,1),device=observed.device)
    cells=torch.rand((b,c,t),device=observed.device)<.04
    return ((channel & tail)|cells)&observed


class ConditionalMean(ConditionalDiffusion):
    def __init__(self,channels,window=64,width=128,steps=32):
        super().__init__(channels,window,width,steps)
        # Retain only the conditional encoder and mean head, not unused denoiser weights.
        del self.denoiser
        self.mean_head=nn.Sequential(nn.Linear(width,width*2),nn.SiLU(),nn.Linear(width*2,window))
    def forward(self,context,observed,graph):
        return self.mean_head(self.encode(context,observed,graph))
