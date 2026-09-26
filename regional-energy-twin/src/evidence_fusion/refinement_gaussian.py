"""Exact Gaussian messages for a fixed finite-window household hierarchy.

All matrix work uses the caller's torch device and FP64. The global trajectory
is the separator. Household AR residuals are independent *conditional* on that
trajectory, not unconditionally. No outcome data are fetched by this module.
"""
from dataclasses import dataclass
import hashlib
import numpy as np
import torch


def tensor(x, device):
    return torch.as_tensor(x, dtype=torch.float64, device=device)


def tensor_bytes(value):
    if isinstance(value, torch.Tensor):
        return value.nelement() * value.element_size()
    if isinstance(value, (list, tuple)):
        return sum(tensor_bytes(x) for x in value)
    if isinstance(value, dict):
        return sum(tensor_bytes(x) for x in value.values())
    return 0


def gaussian_marginal(precision, information, keep):
    """Schur elimination; ordering of kept coordinates is explicit."""
    keep = torch.as_tensor(keep, device=precision.device, dtype=torch.long)
    drop = torch.tensor([i for i in range(len(information)) if i not in keep.tolist()],
                        device=precision.device, dtype=torch.long)
    a = precision[keep][:, keep]
    b = information[keep]
    if len(drop) == 0:
        return a, b
    cross = precision[keep][:, drop]
    leaf = precision[drop][:, drop]
    solved = torch.linalg.solve(leaf, torch.cat((cross.T, information[drop, None]), 1))
    return a - cross @ solved[:, :-1], b - cross @ solved[:, -1]


def trajectory_prior(transition, process_var, prior_var, length):
    """Proper prior: s0~N(0,P), s[t+1]=F s[t]+epsilon. No extra ridge."""
    d = len(prior_var)
    j = torch.zeros((length*d, length*d), device=transition.device, dtype=transition.dtype)
    j[:d, :d] += torch.diag(1/prior_var)
    r = torch.diag(1/process_var)
    for t in range(1, length):
        prev, cur = slice((t-1)*d, t*d), slice(t*d, (t+1)*d)
        j[prev, prev] += transition.T @ r @ transition
        j[cur, cur] += r
        j[prev, cur] -= transition.T @ r
        j[cur, prev] -= r @ transition
    return j


def propagate_noise(transition, process_var, horizon):
    q = torch.zeros_like(transition)
    for _ in range(horizon):
        q = transition @ q @ transition.T + torch.diag(process_var)
    return q


@dataclass
class ForecastConditional:
    intercept: torch.Tensor
    coefficient: torch.Tensor
    residual_covariance: torch.Tensor
    future_loading: torch.Tensor
    baseline: torch.Tensor

    def bytes(self):
        return sum(tensor_bytes(v) for v in vars(self).values())


@dataclass
class GroupMessage:
    group: int
    window: str
    evidence_id: str
    kind: str
    precision: torch.Tensor
    information: torch.Tensor
    forecasts: list
    leaf: dict
    households: int

    def bytes(self):
        return (tensor_bytes(self.precision) + tensor_bytes(self.information)
                + sum(x.bytes() for x in self.forecasts) + tensor_bytes(self.leaf))

    def coarsen(self):
        """Representation only: retain likelihood and registered-query laws."""
        released = tensor_bytes(self.leaf)
        self.leaf = {}
        return released


class HierarchicalGaussian:
    def __init__(self, model, length=24, device='cuda'):
        self.device = device
        self.length = length
        self.loading = tensor(model['loadings']*model['scale'][:, None], device)
        self.variance = tensor(model['detail_var'], device)
        self.nugget = tensor(model['measurement_var'], device)
        self.rho = tensor(model['detail_ar'], device)
        self.transition = tensor(model['transition'], device)
        self.process = tensor(model['process_var'], device)
        self.prior = trajectory_prior(self.transition, self.process,
                                      tensor(model['prior_var'], device), length)
        self.dimension = self.prior.shape[0]
        self.d = self.transition.shape[0]
        self.future_noise = {h: propagate_noise(self.transition, self.process, h) for h in (2, 12)}
        self.future_transition = {h: torch.linalg.matrix_power(self.transition, h) for h in (2, 12)}

    def covariance(self, ids):
        t = torch.arange(self.length, device=self.device)
        distance = (t[:, None]-t[None, :]).abs()
        return self.variance[ids, None, None] * self.rho[ids, None, None]**distance

    def group_message(self, group, window, ids, mask, observations, kind,
                      query_weights, baselines, evidence_id):
        """Observations are either a derived SUM (L,) or fine residuals (N,L).

        query_weights[h] has rows: full group, evaluator's observed support,
        first physical household. Supports affect output queries only, never
        conditioning or policy selection. Missing dummy coordinates contribute
        exactly zero information; no missing demand is imputed.
        """
        ids = torch.as_tensor(ids, device=self.device, dtype=torch.long)
        mask = torch.as_tensor(mask, device=self.device, dtype=torch.bool)
        y = tensor(observations, self.device)
        if kind not in ('aggregate', 'fine'):
            raise ValueError('unknown evidence kind')
        h = self.loading[ids]
        k = self.covariance(ids)
        n, length = mask.shape
        eye = torch.eye(length, device=self.device, dtype=torch.float64)
        m = mask.to(torch.float64)
        v = k*m[:, :, None]*m[:, None, :] + torch.diag_embed(self.nugget[ids, None]*m + (1-m))
        if kind == 'fine':
            safe_y = torch.where(mask, y, torch.zeros_like(y))
            if not bool(torch.isfinite(safe_y).all()):
                raise ValueError('nonfinite observed values')
            chol = torch.linalg.cholesky(v)
            # Solves against I provide reusable inverse ACTION coefficients.
            # The full global inverse is never formed.
            solve = torch.cholesky_solve(eye.expand(n, -1, -1), chol)*m[:, :, None]*m[:, None, :]
            solved_y = (solve @ safe_y[:, :, None]).squeeze(-1)
            j = torch.einsum('htu,hi,hj->tiuj', solve, h, h).reshape(self.dimension, self.dimension)
            rhs = torch.einsum('ht,hi->ti', solved_y, h).reshape(-1)
            leaf = dict(solve=solve, residual=safe_y, mask=mask, covariance=k, ids=ids)
        else:
            # Sum covariance must not include the per-household dummy coordinates.
            v_sum = (k*m[:, :, None]*m[:, None, :]).sum(0) + torch.diag((self.nugget[ids, None]*m).sum(0))
            observed_time = mask.any(0)
            v_sum += torch.diag((~observed_time).to(torch.float64))
            safe_y = torch.where(observed_time, y, torch.zeros_like(y))
            chol = torch.linalg.cholesky(v_sum)
            solve = torch.cholesky_solve(eye, chol)*observed_time[:, None]*observed_time[None, :]
            oh = m.T @ h
            operator = torch.einsum('tu,ti->tui', eye, oh).reshape(length, self.dimension)
            j = operator.T @ solve @ operator
            rhs = operator.T @ solve @ safe_y
            leaf = {}  # Aggregate-only model never opens household conditionals.
        forecasts = []
        for index, horizon in enumerate((2, 12)):
            weights = tensor(query_weights[index], self.device)
            cross = self.variance[ids, None] * self.rho[ids, None]**(
                horizon+length-1-torch.arange(length, device=self.device))[None, :]
            cross *= m
            load = weights @ h
            coefficient = torch.zeros((len(weights), self.dimension), device=self.device, dtype=torch.float64)
            coefficient[:, -self.d:] = load @ self.future_transition[horizon]
            residual_cov = (weights*(self.variance[ids]+self.nugget[ids])) @ weights.T
            if kind == 'fine':
                gain = torch.einsum('ht,htu->hu', cross, solve)
                intercept = weights @ (gain*safe_y).sum(1)
                coefficient -= torch.einsum('qh,ht,hi->qti', weights, gain, h).reshape(len(weights), -1)
                residual_cov -= (weights*(gain*cross).sum(1)) @ weights.T
            else:
                gain = (weights @ cross) @ solve
                intercept = gain @ safe_y
                coefficient -= gain @ operator
                residual_cov -= gain @ (weights @ cross).T
            forecasts.append(ForecastConditional(intercept, coefficient, residual_cov, load,
                                                 tensor(baselines[index], self.device)))
        return GroupMessage(group, window, evidence_id, kind, (j+j.T)/2, rhs,
                            forecasts, leaf, n)


class MessageState:
    """One active likelihood per physical group/window. Atomic replacement."""
    def __init__(self, model, window):
        self.model = model
        self.window = window
        self.messages = {}
        self.precision = model.prior.clone()
        self.information = torch.zeros(model.dimension, device=model.device, dtype=torch.float64)
        self.version = 0
        self.factorizations = 0
        self._posterior = None

    def replace(self, message):
        if message.window != self.window:
            raise ValueError('stale window; factors must be recomputed')
        old = self.messages.get(message.group)
        if old is not None:
            if old.evidence_id == message.evidence_id and old.kind == message.kind:
                # Representation restoration may attach leaf conditionals, but
                # cannot add its already-counted likelihood a second time.
                old.leaf = message.leaf
                return False
            if old.evidence_id != message.evidence_id:
                raise ValueError('support/version mismatch; explicit new window required')
            self.precision -= old.precision
            self.information -= old.information
        self.messages[message.group] = message
        self.precision += message.precision
        self.information += message.information
        self.version += 1
        self._posterior = None
        return True

    def posterior(self):
        if self._posterior is None:
            j = (self.precision+self.precision.T)/2
            chol = torch.linalg.cholesky(j)
            mean = torch.cholesky_solve(self.information[:, None], chol).squeeze(1)
            self._posterior = (mean, chol)
            self.factorizations += 1
        return self._posterior

    def predictions(self, horizon_index):
        mean, chol = self.posterior()
        messages = [self.messages[g] for g in sorted(self.messages)]
        packs = [msg.forecasts[horizon_index] for msg in messages]
        horizon = (2, 12)[horizon_index]
        b = torch.stack([p.coefficient for p in packs])
        offset = torch.stack([p.intercept+p.baseline for p in packs])
        loading = torch.stack([p.future_loading for p in packs])
        private = torch.stack([p.residual_covariance for p in packs])
        flat = b.reshape(-1, self.model.dimension)
        action = torch.cholesky_solve(flat.T, chol).T.reshape_as(b)
        group_mean = offset + b @ mean
        group_var = (b*action).sum(-1) + private.diagonal(dim1=-2, dim2=-1)
        group_var += torch.einsum('gqi,ij,gqj->gq', loading, self.model.future_noise[horizon], loading)
        # Sum coefficient BEFORE covariance. Cross-group errors are correlated.
        total_b = b.sum(0)
        total_loading = loading.sum(0)
        region_mean = group_mean.sum(0)
        region_var = (total_b*action.sum(0)).sum(-1) + private.diagonal(dim1=-2, dim2=-1).sum(0)
        region_var += torch.einsum('qi,ij,qj->q', total_loading, self.model.future_noise[horizon], total_loading)
        if bool((group_var < -1e-8).any()) or bool((region_var < -1e-8).any()):
            raise ArithmeticError('negative predictive variance')
        return dict(group_mean=group_mean, group_var=group_var,
                    region_mean=region_mean, region_var=region_var)

    def bytes(self):
        base = tensor_bytes(self.precision)+tensor_bytes(self.information)
        if self._posterior is not None:
            base += tensor_bytes(self._posterior)
        return base+sum(m.bytes() for m in self.messages.values())

    def checkpoint(self, path, model_hash, meter_ids):
        """Persist exactly the retained state, without hidden leaf caches."""
        messages = [self.messages[g] for g in sorted(self.messages)]
        payload = dict(model_hash=model_hash, meter_ids=meter_ids, window=self.window,
                       groups=np.array([m.group for m in messages]),
                       households=np.array([m.households for m in messages]),
                       evidence_ids=np.array([m.evidence_id for m in messages]),
                       kinds=np.array([m.kind for m in messages]), version=self.version,
                       precision=np.stack([m.precision.cpu().numpy() for m in messages]),
                       information=np.stack([m.information.cpu().numpy() for m in messages]))
        for field in ('intercept', 'coefficient', 'residual_covariance', 'future_loading', 'baseline'):
            payload[field] = np.stack([[getattr(p, field).cpu().numpy() for p in m.forecasts] for m in messages])
        np.savez_compressed(path, **payload)

    @classmethod
    def restore(cls, model, path, model_hash):
        with np.load(path, allow_pickle=False) as stored:
            if str(stored['model_hash']) != model_hash:
                raise ValueError('checkpoint model version mismatch')
            state = cls(model, str(stored['window']))
            for i, group in enumerate(stored['groups']):
                forecasts = [ForecastConditional(*[tensor(stored[field][i, h], model.device)
                    for field in ('intercept', 'coefficient', 'residual_covariance', 'future_loading', 'baseline')])
                    for h in range(2)]
                msg = GroupMessage(int(group), state.window, str(stored['evidence_ids'][i]),
                    str(stored['kinds'][i]), tensor(stored['precision'][i], model.device),
                    tensor(stored['information'][i], model.device), forecasts, {}, int(stored['households'][i]))
                state.replace(msg)
            state.version = int(stored['version'])
            return state

    def activate(self, group):
        """Expose an actual trajectory and its covariance, not just a display."""
        msg = self.messages[group]
        if not msg.leaf:
            raise ValueError('conditional evicted: reread evidence before refinement')
        if msg.kind == 'fine' and msg.leaf.get('posterior_version') != self.version:
            mean, _ = self.posterior()
            leaf = msg.leaf
            expected = self.model.loading[leaf['ids']] @ mean.reshape(self.model.length, self.model.d).T
            gain = leaf['covariance'] @ leaf['solve']
            leaf['conditional_mean'] = (gain @ (leaf['residual']-expected)[:, :, None]).squeeze(-1)
            leaf['conditional_covariance'] = leaf['covariance']-gain @ leaf['covariance']
            leaf['conditional_gain'] = gain
            leaf['posterior_version'] = self.version
        return msg.leaf

    def expose_aggregate_detail(self, group, ids, mask, aggregate):
        """Operation A: conditional detail using exactly the SAME aggregate.

        Cross-household covariance is retained implicitly through the aggregate
        gain and separator posterior. Diagonal covariance blocks are not an
        assertion of household independence.
        """
        msg = self.messages[group]
        if msg.kind != 'aggregate':
            raise ValueError('restore fine conditionals for fine evidence')
        ids = torch.as_tensor(ids, device=self.model.device, dtype=torch.long)
        m = tensor(mask, self.model.device)
        y = tensor(aggregate, self.model.device)
        k = self.model.covariance(ids)
        v = (k*m[:, :, None]*m[:, None, :]).sum(0)
        v += torch.diag((self.model.nugget[ids, None]*m).sum(0))
        present = m.sum(0) > 0
        v += torch.diag((~present).to(torch.float64))
        cross = k*m[:, None, :]
        gain = torch.linalg.solve(v, cross.transpose(-2, -1)).transpose(-2, -1)
        mean, _ = self.posterior()
        expected = (m.T @ self.model.loading[ids] * mean.reshape(self.model.length, self.model.d)).sum(1)
        detail_mean = gain @ (y-expected)
        conditional_cov = k-gain@cross.transpose(-2, -1)
        msg.leaf = dict(conditional_mean=detail_mean, conditional_covariance=conditional_cov,
                        aggregate_gain=gain, ids=ids)
        return msg.leaf


def evidence_fingerprint(window, ids, mask, source_version='fixed'):
    digest = hashlib.sha256(window.encode())
    digest.update(source_version.encode())
    digest.update(np.asarray(ids, dtype=np.int64).tobytes())
    digest.update(np.asarray(mask, dtype=np.bool_).tobytes())
    return digest.hexdigest()
