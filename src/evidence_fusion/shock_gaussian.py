"""GPU finite-window Gaussian inference with partially acquired fine evidence.

The likelihood is p(fine|c) p(derived aggregates|fine,c). This permits arbitrary
cell masks without double counting. It extends the fixed Stage 2 model, not its
parameters. Adaptive schedule censoring outside the window is NOT modeled.
"""
import torch
from .refinement_gaussian import HierarchicalGaussian, tensor, propagate_noise


class ShockGaussian(HierarchicalGaussian):
    horizons = (1, 2, 12)

    def __init__(self, model, length=24, device='cuda'):
        super().__init__(model, length, device)
        self.groups = torch.as_tensor(model['groups'], device=device, dtype=torch.long)
        self.ids = [torch.where(self.groups == g)[0] for g in range(int(self.groups.max())+1)]
        self.identity = torch.eye(length, dtype=torch.float64, device=device)
        self.house_cov = self.covariance(torch.arange(len(self.loading), device=device))
        self.house_obs_cov = self.house_cov + torch.diag_embed(
            self.nugget[:, None].expand(-1, length))
        self.future_noise = {h:propagate_noise(self.transition, self.process, h) for h in self.horizons}
        self.future_transition = {h:torch.linalg.matrix_power(self.transition, h) for h in self.horizons}

    def message(self, ids, native, fine, aggregate, supports, baseline, retain=False):
        """Only fine contains values acquired by the consumer; other cells NaN."""
        mask = native.to(torch.float64)
        acquired = torch.isfinite(fine) & native
        f = acquired.to(torch.float64)
        y = torch.where(acquired, fine, 0.)
        v = self.house_obs_cov[ids]
        h = self.loading[ids]
        vf = v*f[:, :, None]*f[:, None, :] + torch.diag_embed(1-f)
        chol = torch.linalg.cholesky(vf)
        sf = torch.cholesky_solve(self.identity.expand(len(ids), -1, -1), chol)
        sf *= f[:, :, None]*f[:, None, :]
        fy = (sf@y[:, :, None]).squeeze(-1)
        information = torch.einsum('nt,ni->ti', fy, h).reshape(-1)
        precision = torch.einsum('ntu,ni,nj->tiuj', sf, h, h).reshape(self.dimension,self.dimension)
        gain = v@sf
        residual_cov = v-gain@v
        # Condition the *same* derived aggregate on all acquired constituent cells.
        va = (residual_cov*mask[:, :, None]*mask[:, None, :]).sum(0)
        present = (native & ~acquired).any(0)
        va = (va+va.T)/2
        va = va*present[:, None]*present[None, :] + torch.diag((~present).to(torch.float64))
        sa = torch.cholesky_solve(self.identity, torch.linalg.cholesky(va))
        sa *= present[:, None]*present[None, :]
        operator = torch.einsum('tu,ti->tui', self.identity, mask.T@h)
        operator -= torch.einsum('nt,ntu,ni->tui', mask, gain, h)
        operator = operator.reshape(self.length, self.dimension)*present[:, None]
        offset = (mask*(gain@y[:, :, None]).squeeze(-1)).sum(0)
        adjusted = torch.where(present, aggregate-offset, 0.)
        precision += operator.T@sa@operator
        information += operator.T@sa@adjusted
        forecasts = []
        for hi, horizon in enumerate(self.horizons):
            cross = self.variance[ids, None]*self.rho[ids, None]**(
                horizon+self.length-1-torch.arange(self.length, device=self.device))[None, :]
            gf = torch.einsum('nt,ntu->nu', cross, sf)
            offset_q = (gf*y).sum(1)
            coefficient = -torch.einsum('nt,ni->nti', gf, h).reshape(len(ids), self.dimension)
            coefficient[:, -self.d:] += h@self.future_transition[horizon]
            private_before = self.variance[ids]+self.nugget[ids]-(gf*cross).sum(1)
            qa = (cross-torch.einsum('nt,ntu->nu', gf, v))*mask
            ga = qa@sa
            offset_q += ga@adjusted
            coefficient -= ga@operator
            private_diag = private_before-(ga*qa).sum(1)
            weights = supports[hi, ids].to(torch.float64)
            sum_qa = weights@qa
            group_private = (weights.square()*private_before).sum()-sum_qa@sa@sum_qa
            forecasts.append(dict(offset=offset_q+baseline[hi,ids], coefficient=coefficient,
                private=private_diag, loading=h, group_coefficient=weights@coefficient,
                group_loading=weights@h, group_private=group_private, weights=weights))
        leaf = dict(gain=gain, covariance=residual_cov) if retain else {}
        return (precision+precision.T)/2, information, forecasts, leaf

    def infer(self, native, fine, aggregates, supports, baseline, retain_groups=()):
        native = torch.as_tensor(native, dtype=torch.bool, device=self.device)
        fine = tensor(fine, self.device)
        aggregates = tensor(aggregates, self.device)
        supports = torch.as_tensor(supports, dtype=torch.bool, device=self.device)
        baseline = tensor(baseline, self.device)
        precision = self.prior.clone()
        information = torch.zeros(self.dimension, dtype=torch.float64, device=self.device)
        packs, leaves = [], []
        for g, ids in enumerate(self.ids):
            j, b, pack, leaf = self.message(ids, native[ids], fine[ids], aggregates[g],
                                          supports, baseline, g in retain_groups)
            precision += j; information += b
            packs.append(pack); leaves.append(leaf)
        chol = torch.linalg.cholesky((precision+precision.T)/2)
        mean = torch.cholesky_solve(information[:, None],chol).squeeze(1)
        outputs = []
        for hi,horizon in enumerate(self.horizons):
            # Batched queries share one separator factor, including streamed fine.
            coeff = torch.cat([p[hi]['coefficient'] for p in packs])
            action = torch.cholesky_solve(coeff.T,chol).T
            house_mean = torch.empty(len(self.loading),dtype=torch.float64,device=self.device)
            house_var = torch.empty_like(house_mean)
            group_mean, group_var, group_b, group_load, group_private = [],[],[],[],[]
            cursor=0
            for ids,pack in zip(self.ids,packs):
                p=pack[hi]; a=action[cursor:cursor+len(ids)]; cursor+=len(ids)
                mu=p['offset']+p['coefficient']@mean
                vv=(p['coefficient']*a).sum(1)+p['private']
                vv+=((p['loading']@self.future_noise[horizon])*p['loading']).sum(1)
                house_mean[ids]=mu; house_var[ids]=vv
                ba=p['weights']@a
                gv=p['group_coefficient']@ba+p['group_private']
                gv+=p['group_loading']@self.future_noise[horizon]@p['group_loading']
                group_mean.append(p['weights']@mu); group_var.append(gv)
                group_b.append(p['group_coefficient']); group_load.append(p['group_loading'])
                group_private.append(p['group_private'])
            total_b=torch.stack(group_b).sum(0); total_h=torch.stack(group_load).sum(0)
            region_var=total_b@torch.cholesky_solve(total_b[:,None],chol).squeeze(1)
            region_var+=torch.stack(group_private).sum()+total_h@self.future_noise[horizon]@total_h
            outputs.append(dict(mean=house_mean,variance=house_var,group_mean=torch.stack(group_mean),
                group_variance=torch.stack(group_var),region_mean=torch.stack(group_mean).sum(),
                region_variance=region_var))
        return outputs, dict(precision=precision,information=information,mean=mean,chol=chol,
                             leaves=leaves, groups_rebuilt=len(self.ids), separator_dimension=self.dimension)
