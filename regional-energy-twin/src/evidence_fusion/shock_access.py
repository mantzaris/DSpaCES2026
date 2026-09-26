"""Restricted observation channel and deterministic evidence-window cache."""
import numpy as np


class ObservationChannel:
    def __init__(self, readings, groups, budget, trace):
        self.__readings = readings
        self.__groups = np.asarray(groups)
        self.budget = int(budget)
        self.trace = trace
        self.cutoff = -1
        self.used = set()

    def advance(self, cutoff):
        if cutoff != self.cutoff+1:
            raise ValueError('Observation channel advances one causal step at a time')
        self.cutoff = cutoff; self.used=set()

    def summary(self):
        values=self.__readings[self.cutoff]
        mask=np.isfinite(values)
        sums=np.bincount(self.__groups,weights=np.where(mask,values,0.),minlength=16)
        self.trace.append(dict(step=self.cutoff,kind='summary',attempted=len(values),
            returned=int(mask.sum()),payload_bytes=int(sums.nbytes+np.packbits(mask).nbytes+64),
            provider_scan_rows=len(values),households=''))
        return sums,mask

    def read(self, ids, purpose='probe', at=None):
        at=self.cutoff if at is None else at
        if at != self.cutoff:
            raise ValueError('Only current-time requests are allowed; no future or free historical reads')
        ids=np.asarray(ids,dtype=int)
        if len(ids)!=len(set(ids.tolist())) or np.any(ids<0) or np.any(ids>=self.__readings.shape[1]):
            raise ValueError('Invalid or repeated IDs')
        if self.used.intersection(ids.tolist()):
            raise ValueError('Repeated current records must be served by consumer cache')
        if len(self.used)+len(ids)>self.budget:
            raise ValueError('Fine observation budget exceeded')
        self.used.update(ids.tolist())
        values=self.__readings[at,ids].copy()
        self.trace.append(dict(step=at,kind=purpose,attempted=len(ids),returned=int(np.isfinite(values).sum()),
            payload_bytes=int(16*len(ids)+64),provider_scan_rows=0,
            households='ALL' if len(ids)==self.__readings.shape[1] else ' '.join(map(str,ids))))
        return values


class EvidenceWindow:
    def __init__(self, households, length=24):
        self.length=length
        self.values=np.full((households,length),np.nan,dtype=np.float64)
        self.cutoff=None

    def advance(self, cutoff):
        if self.cutoff is not None and cutoff!=self.cutoff+1:
            raise ValueError('Nonconsecutive evidence window')
        evicted=int(np.isfinite(self.values[:,0]).sum())
        self.values[:,:-1]=self.values[:,1:]; self.values[:,-1]=np.nan
        self.cutoff=cutoff
        return evicted

    def add(self, ids, values, cutoff):
        if cutoff!=self.cutoff:
            raise ValueError('Stale fine evidence')
        self.values[np.asarray(ids),-1]=values


class ProbePolicy:
    """Scores use ONLY revealed probes. Exploration is never switched off."""
    def __init__(self, groups, seed=1729, probes=42, budget=209, trigger=float('inf')):
        self.groups=np.asarray(groups); self.n=len(groups)
        self.order=np.random.default_rng(seed).permutation(self.n)
        self.probes=probes; self.budget=budget; self.trigger=trigger
        self.score=np.zeros(16); self.active=-1; self.ttl=0
        self.rng=np.random.default_rng(seed+1)

    def probe_ids(self, step):
        return self.order[(step*self.probes+np.arange(self.probes))%self.n]

    def update(self, ids, innovations):
        self.score*=.8
        for g in range(16):
            z=np.asarray(innovations)[self.groups[ids]==g]
            z=z[np.isfinite(z)]
            if len(z): self.score[g]+=max(0.,float(z.max())-2.)
        best=int(np.argmax(self.score))
        if self.score[best]>self.trigger:
            self.active=best; self.ttl=4
        elif self.ttl>0:
            self.ttl-=1
        else:
            self.active=-1

    def refinement_ids(self, step, probe_ids, mode='event', uncertainty=None):
        remaining=self.budget-len(probe_ids)
        available=np.setdiff1d(np.arange(self.n),probe_ids)
        if mode=='random': return self.rng.choice(available,remaining,replace=False)
        # 25% of extra reads always explore; idle triggers rotate all reads.
        exploration=max(1,remaining//4)
        rotation=np.roll(self.order,-(step*remaining)%self.n)
        rotation=rotation[~np.isin(rotation,probe_ids)]
        group=self.active if mode=='event' else int(np.argmax(uncertainty))
        if group<0: return rotation[:remaining]
        explore=rotation[:exploration]
        candidates=rotation[(self.groups[rotation]==group)&~np.isin(rotation,explore)]
        chosen=np.r_[explore,candidates[:remaining-exploration]]
        if len(chosen)<remaining:
            chosen=np.r_[chosen,rotation[~np.isin(rotation,chosen)][:remaining-len(chosen)]]
        return chosen.astype(int)
