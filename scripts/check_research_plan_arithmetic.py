"""Small illustrative arithmetic checks; no meter data, fitting, or GPU access."""
import datetime as dt
import hashlib
import itertools
import json
from pathlib import Path
import time

import numpy as np
from scipy.optimize import linprog


def main():
    started = time.monotonic()
    states = np.array(list(itertools.product((0, 1), repeat=3)))
    pairs = list(itertools.combinations(range(3), 2))
    matrix = np.array([
        np.all(states[:, pair] == pattern, axis=1).astype(float)
        for pair in pairs for pattern in itertools.product((0, 1), repeat=2)
    ])
    messages = np.tile([.05, .45, .45, .05], 3)
    repair = linprog(
        np.r_[np.zeros(8), 1.],
        A_ub=np.vstack([np.c_[matrix, -np.ones(12)],
                        np.c_[-matrix, -np.ones(12)]]),
        b_ub=np.r_[messages, -messages],
        A_eq=np.array([np.r_[np.ones(8), 0.]]), b_eq=[1.],
        bounds=(0, None), method='highs',
    )
    assert repair.success and abs(repair.fun - 7 / 60) < 1e-12
    counts = states.sum(axis=1)
    losses = np.array([4 * np.maximum(counts-a, 0) + np.maximum(a-counts, 0)
                       for a in range(4)])
    ae = np.vstack([np.ones(8), matrix])
    be = np.r_[1., np.full(12, .25)]

    def upper(values):
        result = linprog(-values, A_eq=ae, b_eq=be, bounds=(0, None), method='highs')
        assert result.success
        return float(-result.fun)

    regrets = [max(upper(losses[a] - losses[b]) for b in range(4)) for a in range(4)]
    worst_losses = [upper(row) for row in losses]
    even = (counts % 2 == 0).astype(float) / 4
    odd = (counts % 2 == 1).astype(float) / 4
    assert np.allclose(matrix @ even, .25) and np.allclose(matrix @ odd, .25)
    assert np.argmin(regrets) == 2 and abs(regrets[2] - .25) < 1e-12
    assert np.argmin(worst_losses) == 3 and abs(worst_losses[3] - 1.5) < 1e-12
    deadline = dt.datetime(2026, 10, 15, 23, 59, tzinfo=dt.timezone(dt.timedelta(hours=-12)))
    budget = [2, 3, 3, 5, 3, 3, 2, 3]
    pages = [.8, .9, 1.2, 1.6, 1.2, 2.6, .5, 1.2]
    assert sum(budget) == 24 and abs(sum(pages) - 10) < 1e-12
    bdcc = Path('/home/resort/Documents/repos/EAI-BDCC2026/research_plan/EAI_BDCC_2026_Research_Plan.md')
    output = {
        'scope': 'Illustrative eight-state LPs, dimensions, dates and budget arithmetic only',
        'bdcc_source': str(bdcc), 'bdcc_sha256': hashlib.sha256(bdcc.read_bytes()).hexdigest(),
        'states': states.tolist(), 'minimum_cell_repair': float(repair.fun),
        'even_parity_action_losses': (losses @ even).tolist(),
        'odd_parity_action_losses': (losses @ odd).tolist(),
        'worst_case_regret_by_action': regrets, 'worst_case_loss_by_action': worst_losses,
        'deadline_utc': deadline.astimezone(dt.timezone.utc).isoformat(),
        'gpu_budget_hours': budget, 'paper_pages': pages,
        'primary_max_targets': 16 * 8760,
        'primary_max_provider_messages': 16 * 8760 * 12,
        'primary_max_meter_positions': 128 * 8760,
        'fp32_state_buffer_bytes': {
            '2048_by_256': 2048 * 256 * 4,
            '256_by_4096': 256 * 4096 * 4,
            '128_by_65536': 128 * 65536 * 4,
        },
        'no_observational_data_read': True, 'gpu_used': False,
        'cpu_wall_seconds': time.monotonic() - started,
    }
    path = Path('reports/planning_20260923_arithmetic.json')
    path.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
