"""PCA B1--B3 and a dense equivalent of the published one-head GDN architecture.

GDN source revision is pinned in the acquisition manifest. The dense attention
form retains top-k cosine graph, embedding attention, multiplicative embeddings,
both batch normalizations, dropout and shared output head. Evaluation is separate.
"""
from __future__ import annotations
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


class PCADetector:
    def __init__(self,rank=4,lag=1): self.rank=rank;self.lag=lag
    def vectors(self,x):
        b,c,t=x.shape
        return np.stack([x[...,k:t-self.lag+k+1] for k in range(self.lag)],-1).transpose(0,2,1,3).reshape(-1,c*self.lag)
    def fit(self,x):
        from sklearn.decomposition import PCA
        a=self.vectors(x)
        self.fill=np.nanmedian(a,axis=0); a=np.where(np.isfinite(a),a,self.fill)
        rank=min(self.rank,a.shape[-1]-1,len(a)-1)
        self.pca=PCA(n_components=rank,svd_solver='randomized',random_state=9026).fit(a)
        return self
    @classmethod
    def load(cls,path,lag=1):
        with np.load(path,allow_pickle=False) as saved:
            model=cls(saved['components'].shape[0],lag)
            model.fill=saved['fill'].copy()
            model.portable_components=saved['components'].copy();model.portable_mean=saved['mean'].copy()
        return model
    def reconstruction_errors(self,x):
        a=self.vectors(x); mask=np.isfinite(a); a=np.where(mask,a,self.fill)
        # sklearn's transform and inverse_transform use the separately fitted PCA mean.
        if hasattr(self,'portable_components'):
            components=self.portable_components
            reconstructed=(a@components.T-self.portable_mean@components.T)@components+self.portable_mean
        else:reconstructed=self.pca.inverse_transform(self.pca.transform(a))
        squared=(a-reconstructed)**2
        squared=np.where(mask,squared,np.nan).reshape(len(x),x.shape[-1]-self.lag+1,x.shape[1],self.lag)
        return squared
    def score(self,x,horizon=8):
        # Frozen common-protocol score uses only each embedded vector's current
        # target coordinate, matching the causal forecasting target interval.
        return np.nanmean(self.reconstruction_errors(x)[:,-horizon:,:,-1],axis=1)
    def total_reconstruction_score(self,x,horizon=8):
        """B2 squared residual norm, averaged over target decision steps.

        Missing coordinates have no observed residual. A wholly unavailable
        vector remains unavailable rather than receiving a zero error.
        """
        error=self.reconstruction_errors(x)[:,-horizon:]
        total=np.nansum(error,axis=(2,3));total[~np.isfinite(error).any(axis=(2,3))]=np.nan
        return np.nanmean(total,axis=1)
    def all_coordinate_contributions(self,x,horizon=8):
        """B3 mean residual over all observed lag coordinates of each sensor."""
        return np.nanmean(self.reconstruction_errors(x)[:,-horizon:],axis=(1,3))


class GDN(nn.Module):
    def __init__(self,channels,history=56,dim=64,topk=5):
        super().__init__();self.channels=channels;self.topk=min(topk,channels)
        self.embedding=nn.Embedding(channels,dim);self.projection=nn.Linear(history,dim,bias=False)
        self.attention_i=nn.Parameter(torch.empty(dim));self.attention_j=nn.Parameter(torch.empty(dim))
        self.attention_embedding_i=nn.Parameter(torch.zeros(dim));self.attention_embedding_j=nn.Parameter(torch.zeros(dim))
        self.bias=nn.Parameter(torch.zeros(dim));self.bn_graph=nn.BatchNorm1d(dim)
        self.bn_output=nn.BatchNorm1d(dim);self.dropout=nn.Dropout(.2);self.head=nn.Linear(dim,1)
        nn.init.kaiming_uniform_(self.embedding.weight,a=np.sqrt(5))
        nn.init.xavier_uniform_(self.projection.weight)
        nn.init.uniform_(self.attention_i,-np.sqrt(3/dim),np.sqrt(3/dim))
        nn.init.uniform_(self.attention_j,-np.sqrt(3/dim),np.sqrt(3/dim))
    def forward(self,x):
        emb=self.embedding.weight
        similarity=F.normalize(emb.detach(),dim=-1)@F.normalize(emb.detach(),dim=-1).T
        neighbors=similarity.topk(self.topk,dim=-1).indices
        adjacency=torch.zeros_like(similarity,dtype=torch.bool).scatter_(1,neighbors,True)
        adjacency.fill_diagonal_(True)
        hidden=self.projection(x)
        target=(hidden*self.attention_i).sum(-1)+(emb*self.attention_embedding_i).sum(-1)
        source=(hidden*self.attention_j).sum(-1)+(emb*self.attention_embedding_j).sum(-1)
        logits=F.leaky_relu(target[:,:,None]+source[:,None,:],negative_slope=.2)
        attention=logits.masked_fill(~adjacency[None],-torch.inf).softmax(-1)
        messages=attention@hidden+self.bias
        messages=F.relu(self.bn_graph(messages.reshape(-1,messages.shape[-1]))).reshape_as(messages)
        output=messages*emb
        output=F.relu(self.bn_output(output.transpose(1,2))).transpose(1,2)
        return self.head(self.dropout(output)).squeeze(-1)


def gdn_residual(model,x,horizon=8):
    history=x.shape[-1]-horizon
    contexts=torch.stack([x[...,step:step+history] for step in range(horizon)],1)
    pred=model(torch.nan_to_num(contexts.reshape(-1,x.shape[1],history))).reshape(len(x),horizon,x.shape[1]).transpose(1,2)
    target=x[...,-horizon:]; mask=torch.isfinite(target)
    errors=torch.where(mask,(target-pred).abs(),torch.zeros_like(target))
    result=errors.sum(-1)/mask.sum(-1).clamp_min(1)
    return result.masked_fill(mask.sum(-1)==0,float('nan'))
