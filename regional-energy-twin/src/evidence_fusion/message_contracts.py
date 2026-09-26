"""Strict immutable wire messages; no raw outcomes or hidden influence fields."""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
import numpy as np


@dataclass(frozen=True)
class Message:
    protocol: str
    provider: str
    building: str
    target_start: str
    target_end: str
    unit: str
    cutoff: str
    issued: str
    arrival: str
    model_version: str
    estimator_digest: str
    evidence_digest: str
    revision: int
    supersedes: str
    common_contract: str
    future_variance: float
    epoch: str
    seed: int
    k: int
    mean: float
    norm: float
    residual: float
    sketch: tuple
    message_id: str = ''

    def identity_payload(self):
        values = asdict(self)
        values.pop('message_id')
        values.pop('arrival')  # delivery envelopes do not create new evidence
        return json.dumps(values, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

    def signed(self):
        return replace(self, message_id=hashlib.sha256(self.identity_payload()).hexdigest())

    def validate(self, epoch):
        if self.protocol != 'weighted-provenance/1' or self.unit != 'kWh':
            raise ValueError('Unsupported protocol/unit')
        if (self.epoch, self.seed, self.k) != (epoch.name, epoch.seed, epoch.k):
            raise ValueError('Incompatible projection epoch')
        if self.message_id != hashlib.sha256(self.identity_payload()).hexdigest():
            raise ValueError('Immutable message content changed')
        if self.revision < 0 or (self.revision > 0 and not self.supersedes):
            raise ValueError('Revision requires explicit supersession')
        if len(self.sketch) != self.k or not all(map(math.isfinite, self.sketch)):
            raise ValueError('Invalid sketch')
        if not all(map(math.isfinite, (self.mean, self.norm, self.residual, self.future_variance))):
            raise ValueError('Invalid numeric metadata')
        if min(self.norm, self.residual, self.future_variance) < 0:
            raise ValueError('Negative uncertainty')
        if self.norm == 0 and any(x != 0 for x in self.sketch):
            raise ValueError('Zero influence must have zero sketch')
        from datetime import datetime, timedelta
        start, end, cutoff, issue, arrival = map(datetime.fromisoformat,
            (self.target_start, self.target_end, self.cutoff, self.issued, self.arrival))
        if end - start != timedelta(hours=1) or cutoff > start or issue > start or cutoff > issue or arrival < issue:
            raise ValueError('Incompatible target support/cutoff/issue times')

    def to_wire(self):
        header = asdict(self)
        header.pop('sketch')
        encoded = json.dumps(header, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        # FP64 wire preserves the ID. FP32 is a separate measured numerical ablation.
        return len(encoded).to_bytes(4, 'little') + encoded + np.asarray(self.sketch, dtype='<f8').tobytes()

    @classmethod
    def from_wire(cls, payload):
        if len(payload) < 4:
            raise ValueError('Truncated message')
        size = int.from_bytes(payload[:4], 'little')
        if size > 65536 or size + 4 > len(payload):
            raise ValueError('Invalid header length')
        data = json.loads(payload[4:size+4])
        if len(payload) - size - 4 != 8 * data['k']:
            raise ValueError('Truncated or excessive sketch payload')
        data['sketch'] = tuple(np.frombuffer(payload[size+4:], dtype='<f8').tolist())
        return cls(**data)


class ActiveMessages:
    def __init__(self, epoch):
        self.epoch = epoch
        self.versions = {}
        self.ids = set()
        self.context = None
        self.duplicates = 0

    def accept(self, message):
        message.validate(self.epoch)
        context = (message.building, message.target_start, message.target_end, message.cutoff,
                   message.common_contract, message.future_variance, message.unit)
        if self.context is not None and context != self.context:
            raise ValueError('Messages describe incompatible targets or noise conventions')
        self.context = context
        if message.message_id in self.ids:
            self.duplicates += 1
            return
        key = message.provider
        revisions = self.versions.setdefault(key, {})
        if message.revision in revisions and revisions[message.revision].message_id != message.message_id:
            raise ValueError('Conflicting immutable revision')
        revisions[message.revision] = message
        self.ids.add(message.message_id)

    def finalize(self):
        if not self.versions:
            raise ValueError('Empty fusion query')
        active = []
        for provider, revisions in sorted(self.versions.items()):
            # Require the complete chain in Stage 1; out-of-order delivery is allowed.
            keys = sorted(revisions)
            if keys != list(range(keys[-1] + 1)):
                raise ValueError('Missing revision chain')
            for number in keys[1:]:
                if revisions[number].supersedes != revisions[number-1].message_id:
                    raise ValueError('Invalid supersession chain')
            active.append(revisions[keys[-1]])
        self.epoch.consume((self.context, tuple(x.message_id for x in active)), len(active))
        # Distinct providers declaring the exact same estimator/lineage are one estimate.
        unique = {}
        for item in active:
            key = (item.estimator_digest, item.evidence_digest, item.model_version)
            if key in unique:
                old = unique[key]
                if (item.mean, item.norm, item.residual, item.sketch) != (old.mean, old.norm, old.residual, old.sketch):
                    raise ValueError('Exact-estimator identity conflicts with numerical content')
            else:
                unique[key] = item
        return list(unique.values())
