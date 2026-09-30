"""Joint conditional graph-temporal diffusion and a labeled GDN adaptation.

Conceptual lineage: DiffSTG (Wen et al., 2023), CSDI (Tashiro et al., 2021).
Cosine beta schedule: Nichol & Dhariwal (2021); DDIM: Song et al. (2021).
This compact architecture is an independent implementation, not their code.
"""
from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


def calendar(timestamps: np.ndarray) -> np.ndarray:
    seconds=timestamps.astype(np.float64)/1e9
    daily=2*np.pi*(seconds%86400)/86400
    weekly=2*np.pi*(seconds%(86400*7))/(86400*7)
    return np.stack((np.sin(daily),np.cos(daily),np.sin(weekly),np.cos(weekly)),-1).astype(np.float32)


def cosine_schedule(steps: int) -> torch.Tensor:
    t=torch.arange(steps+1,dtype=torch.float64)/steps
    alpha=torch.cos((t+.008)/1.008*math.pi/2).square()
    alpha=alpha/alpha[0]
    return (1-alpha[1:]/alpha[:-1]).clamp(0,.999).float()


class GraphTemporalBlock(nn.Module):
    def __init__(self, hidden: int, dilation: int):
        super().__init__()
        self.temporal=nn.Conv2d(hidden,2*hidden,(1,3),padding=(0,dilation),dilation=(1,dilation))
        self.graph=nn.Conv2d(hidden,2*hidden,1)
        self.output=nn.Conv2d(hidden,hidden,1)

    def forward(self, value: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        # All nodes in each future sample interact; no univariate factorization.
        aggregate=torch.einsum('nm,bhmt->bhnt',adjacency.to(value.dtype),value)
        left,right=(self.temporal(value)+self.graph(aggregate)).chunk(2,1)
        return (value+self.output(torch.tanh(left)*torch.sigmoid(right)))/math.sqrt(2)


class GraphDiffusion(nn.Module):
    def __init__(self, node_count: int, channels: int, context: int, hidden: int,
                 layers: int, steps: int, adjacency: torch.Tensor, coordinates: torch.Tensor):
        super().__init__()
        self.channels,self.context,self.steps=channels,context,steps
        self.register_buffer('adjacency',adjacency)
        coords=(coordinates-coordinates.mean(0))/(coordinates.std(0)+1e-6)
        self.register_buffer('coordinates',coords)
        self.register_buffer('alpha_bar',torch.cumprod(1-cosine_schedule(steps),0))
        self.context_encoder=nn.Sequential(nn.Linear(context*channels*2,hidden),nn.SiLU(),nn.Linear(hidden,hidden))
        self.coordinate_encoder=nn.Linear(coordinates.shape[1],hidden)
        self.calendar_encoder=nn.Linear(4,hidden)
        self.step_encoder=nn.Sequential(nn.Linear(16,hidden),nn.SiLU(),nn.Linear(hidden,hidden))
        self.input=nn.Conv2d(channels,hidden,1)
        self.blocks=nn.ModuleList([GraphTemporalBlock(hidden,2**i) for i in range(layers)])
        self.output=nn.Sequential(nn.Conv2d(hidden,hidden,1),nn.SiLU(),nn.Conv2d(hidden,channels,1))

    def conditioning(self, context: torch.Tensor, target_calendar: torch.Tensor) -> torch.Tensor:
        b,t,n,c=context.shape
        valid=torch.isfinite(context)
        observed=torch.cat((torch.nan_to_num(context),valid.to(context.dtype)),-1)
        encoded=self.context_encoder(observed.permute(0,2,1,3).reshape(b,n,-1))
        encoded=encoded+self.coordinate_encoder(self.coordinates)[None]
        time=self.calendar_encoder(target_calendar)
        return (encoded[:,:,None,:]+time[:,None,:,:]).permute(0,3,1,2)

    def forward(self, noisy: torch.Tensor, steps: torch.Tensor, condition: torch.Tensor) -> torch.Tensor:
        frequency=torch.exp(torch.arange(8,device=noisy.device)*(-math.log(10000)/7))
        phase=steps[:,None].float()*frequency[None]
        embedding=self.step_encoder(torch.cat((torch.sin(phase),torch.cos(phase)),-1))
        hidden=self.input(noisy.permute(0,3,2,1))+condition+embedding[:,:,None,None]
        for block in self.blocks: hidden=block(hidden,self.adjacency)
        return self.output(F.silu(hidden)).permute(0,3,2,1)

    def loss(self, target: torch.Tensor, context: torch.Tensor, target_calendar: torch.Tensor,
             screen: bool = True) -> torch.Tensor:
        batch=len(target)
        steps=torch.randint(self.steps,(batch,),device=target.device)
        alpha=self.alpha_bar[steps,None,None,None]
        mask=torch.isfinite(target)
        if screen: mask=mask&(target.abs()<=8)
        clean=torch.where(mask,target,torch.zeros_like(target))
        noise=torch.randn_like(clean)
        noisy=alpha.sqrt()*clean+(1-alpha).sqrt()*noise
        prediction=self(noisy,steps,self.conditioning(context,target_calendar))
        return ((prediction.float()-noise).square()*mask).sum()/mask.sum().clamp_min(1)

    @torch.no_grad()
    def sample(self, context: torch.Tensor, target_calendar: torch.Tensor, samples: int,
               sampling_steps: int, chunk: int = 16, clip: float = 8.0) -> torch.Tensor:
        if len(context)!=1: raise ValueError('Sample one historical issuance at a time')
        self.eval()
        device=context.device
        condition=self.conditioning(context,target_calendar)
        horizon=target_calendar.shape[1]
        indices=np.linspace(0,self.steps-1,sampling_steps,dtype=int)[::-1].copy()
        results=[]
        for start in range(0,samples,chunk):
            number=min(chunk,samples-start)
            latent=torch.randn(number,horizon,context.shape[2],self.channels,device=device)
            for k,index in enumerate(indices):
                alpha=self.alpha_bar[index]
                next_alpha=self.alpha_bar[indices[k+1]] if k+1<len(indices) else torch.tensor(1.,device=device)
                with torch.autocast(device_type=device.type,dtype=torch.bfloat16,enabled=device.type=='cuda'):
                    epsilon=self(latent,torch.full((number,),int(index),device=device),condition.expand(number,-1,-1,-1)).float()
                x0=((latent-(1-alpha).sqrt()*epsilon)/alpha.sqrt()).clamp(-clip,clip)
                # DDIM eta=0; distinct initial noises give independent joint draws.
                latent=next_alpha.sqrt()*x0+(1-next_alpha).sqrt()*epsilon
            results.append(latent)
        return torch.cat(results)


class GDN(nn.Module):
    """GDN-style learned top-k embedding graph + graph attention + prediction.

    Differences from Deng & Hooi: multiple measurement channels, shared simple
    two-layer forecast head, no batch normalization. Original robust max score
    and four-step trailing smoothing are implemented in the experiment runner.
    """
    def __init__(self, nodes: int, channels: int, context: int, hidden: int = 32, topk: int = 15):
        super().__init__()
        self.topk=min(topk,nodes)
        self.embedding=nn.Parameter(torch.randn(nodes,hidden)*.1)
        self.input=nn.Linear(context*channels*2,hidden)
        self.left=nn.Linear(2*hidden,1,bias=False)
        self.right=nn.Linear(2*hidden,1,bias=False)
        self.predictor=nn.Sequential(nn.Linear(hidden,hidden),nn.ReLU(),nn.Linear(hidden,channels))

    def forward(self, history: torch.Tensor) -> torch.Tensor:
        b,t,n,c=history.shape
        masked=torch.cat((torch.nan_to_num(history),torch.isfinite(history).to(history.dtype)),-1)
        hidden=self.input(masked.permute(0,2,1,3).reshape(b,n,-1))
        normalized=F.normalize(self.embedding,dim=-1)
        similarities=normalized@normalized.T
        neighbors=similarities.topk(self.topk,dim=-1).indices
        permitted=torch.zeros_like(similarities,dtype=torch.bool).scatter_(1,neighbors,True)
        merged=torch.cat((hidden,self.embedding[None].expand(b,-1,-1)),-1)
        logits=F.leaky_relu(self.left(merged)+self.right(merged).transpose(1,2),.2)
        attention=torch.softmax(logits.masked_fill(~permitted[None],-1e9),dim=-1)
        aggregate=attention@hidden
        return self.predictor(F.relu(aggregate)*self.embedding[None])
