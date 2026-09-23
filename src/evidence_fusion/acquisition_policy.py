"""One intentional variant: separate acquisition ranking from alarm declaration."""
import numpy as np
from .shock_access import ProbePolicy

class RankedProbePolicy(ProbePolicy):
    """Same acquired-probe score; current positive rank allocates existing extra reads.

    This is a standard residual-driven allocation, not a new detection theorem.
    The alarm threshold is unchanged by this allocation decision.
    """
    def update(self, ids, innovations):
        super().update(ids, innovations)
        self.active=int(np.argmax(self.score)) if self.score.max()>0. else -1
        self.ttl=0

    def decision_reason(self):
        return 'positive_rank' if self.active>=0 else 'rotate_zero_score'
