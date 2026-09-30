"""Frozen source partitions and unchanged witness support (E5)."""
from __future__ import annotations
import hashlib,json
import numpy as np
import torch


def canonicalize_records(values,observed,record_ids):
    """Deduplicate upstream copies, preserving channel/time order; flag conflicts."""
    first={}; indices=[]
    for position,identity in enumerate(record_ids):
        if identity in first:
            previous=first[identity]
            if not np.array_equal(observed[position],observed[previous]) or not np.allclose(
                    values[position],values[previous],equal_nan=True,rtol=1e-12,atol=1e-12):
                raise ValueError('Conflicting duplicate source identity')
        else: first[identity]=position; indices.append(position)
    return values[indices],observed[indices],[record_ids[i] for i in indices]


def select_witnesses(candidate,observed,graph,horizon=8,max_groups=2,kind='observation'):
    """Ordering depends only on frozen training affinity, provenance and availability."""
    groups=graph['groups']; affinity=np.asarray(graph['affinity']); c,t=observed.shape
    if kind=='observation':
        suspect=candidate; excluded={groups[suspect]}; order=np.argsort(-affinity[:,suspect],kind='stable')
    else:
        edge=graph['edges'][candidate]; suspect=edge['source']; target=edge['target']
        excluded={groups[suspect]}
        order=np.concatenate(([target],np.argsort(-affinity[:,target],kind='stable')))
    chosen=[]; group_ids=[]
    for channel in order:
        group=groups[int(channel)]
        if group in excluded or group in group_ids or not observed[channel,-horizon:].any(): continue
        chosen.append(int(channel));group_ids.append(group)
        if len(chosen)==max_groups: break
    target_mask=np.zeros_like(observed,dtype=bool)
    for channel in chosen: target_mask[channel,-horizon:]=observed[channel,-horizon:]
    # Hide every channel from a selected physical source in the target interval.
    forbidden=np.zeros_like(observed,dtype=bool)
    for channel,group in enumerate(groups):
        if group in group_ids: forbidden[channel,-horizon:]=True
    repair=np.zeros_like(observed,dtype=bool)
    if kind=='observation': repair[candidate,-horizon:]=observed[candidate,-horizon:]
    proposal_forbidden=forbidden.copy()
    if kind=='observation':
        for channel,group in enumerate(groups):
            if group==groups[candidate]: proposal_forbidden[channel,-horizon:]=True
    ids=[f'{groups[ch]}:{ch}:{time}' for ch,time in zip(*np.where(target_mask))]
    digest=hashlib.sha256(json.dumps(ids).encode()).hexdigest()
    return dict(channels=chosen,groups=group_ids,support_count=len(group_ids),
        witness_mask=target_mask,forbidden_witness=forbidden,proposal_forbidden=proposal_forbidden,
        edit_mask=repair,witness_ids=ids,witness_hash=digest,horizon=horizon)


def masked_context(values,observed,forbidden):
    mask=observed & ~forbidden
    # Explicit masks accompany context fills; no target can leak through NaN*0.
    return torch.where(mask,values,torch.zeros_like(values)),mask


def aggregate_group_losses(cell_losses,partition):
    """Cell losses [..., channel,time]; membership fixed by the partition."""
    losses=[]
    for channel in partition['channels']:
        valid=torch.as_tensor(partition['witness_mask'][channel],device=cell_losses.device)
        selected=cell_losses[...,channel,valid]
        if selected.shape[-1]==0 or not torch.isfinite(selected).all():
            raise ValueError('Unavailable witness prediction requires abstention')
        losses.append(selected.mean(-1))
    if not losses: raise ValueError('No eligible witness group')
    return torch.stack(losses,-1)
