"""Retrospective matched-control budgets; never changes primary calibration.

Thresholds use untouched controls only. Injected labels are used exclusively
for evaluation. The same controls select and describe each operating point,
so this analysis is not prospective false-alert validation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .localization import set_metrics
from .utils import write_json

FIELDS = ['tp', 'iou', 'faults', 'control_flags', 'control_units',
          'control_alarms', 'control_days', 'transition_flags', 'transition_units']


def event_counts(pvalues: np.ndarray, ranks: np.ndarray, events: list[dict],
                 times: np.ndarray, thresholds: np.ndarray, stride: int,
                 interval_seconds: int) -> np.ndarray:
    """Threshold x recording-block x count, for one scheduled event per trial."""
    if not np.all(np.diff(times) == stride):
        raise ValueError('This vectorized onset calculation requires regular issuance times')
    bases = sorted({event['base'] for event in events})
    positions = {base: index for index, base in enumerate(bases)}
    out = np.zeros((len(thresholds), len(bases), len(FIELDS)))
    for index, threshold in enumerate(thresholds):
        flags = pvalues <= threshold
        onsets = flags & ~np.pad(flags[:, :-1], ((0, 0), (1, 0)), constant_values=False)
        for trial, event in enumerate(events):
            row = out[index, positions[event['base']]]
            if event['is_fault']:
                row[2] += 1
                matches = np.flatnonzero(onsets[trial] & (times >= event['onset']) &
                                         (times < event['onset'] + event['duration']))
                if len(matches):
                    row[0] += 1
                    row[1] += set_metrics(ranks[trial, matches[0]].tolist(), event['nodes'])['iou']
            elif event['kind'] == 'untouched':
                row[3] += flags[trial].sum()
                row[4] += len(times)
                row[5] += onsets[trial].sum()
                row[6] += len(times) * stride * interval_seconds / 86400
            elif event['kind'] == 'transition':
                row[7] += flags[trial].sum()
                row[8] += len(times)
    return out


def select_threshold(counts: np.ndarray, budget: float) -> np.ndarray:
    """Last attainable threshold within budget, with leading threshold zero."""
    rates = counts[..., 3] / np.maximum(counts[..., 4], 1)
    allowed = rates <= budget + 1e-12
    if not np.all(allowed[..., 0]):
        raise ValueError('The no-alert operating point must be present')
    return np.max(np.where(allowed, np.arange(counts.shape[-2]), -1), axis=-1)


def estimate(values: np.ndarray) -> dict:
    return {'low': float(np.quantile(values, .025)), 'high': float(np.quantile(values, .975))}


def build(root: Path) -> None:
    config = json.loads((root / 'configs/full.json').read_text())
    datasets = config['datasets']
    primary = pd.read_csv(root / 'results/event_metrics.csv.gz')
    primary = primary[(primary.graph == 'physical') & (primary.alpha == config['primary_alpha'])]
    cubes = {}; grids = {}; curves = []; verification = []
    for dataset in datasets:
        runs = []
        for seed in config['training_seeds']:
            directory = root / 'experiments/full' / f'score-{dataset}-physical-{seed}'
            events = json.loads((directory / 'events.json').read_text())
            with np.load(directory / 'predictions.npz') as archive:
                runs.append((seed, events, {key: archive[key] for key in
                             ['pvalues', 'ranked_nodes', 'methods', 'times', 'localization_budget']}))
        # Use exact stored rank values, so float representation does not skip ties.
        thresholds = np.unique(np.concatenate([np.array([0.])] + [run[2]['pvalues'].ravel() for run in runs]))
        grids[dataset] = thresholds
        interval = json.loads((root / 'data/manifests' / f'{dataset}.json').read_text())['interval_seconds']
        methods = runs[0][2]['methods'].tolist()
        for column, method in enumerate(methods):
            cube = None
            for seed, events, archive in runs:
                values = archive['pvalues'][:, :, column]
                ranks = archive['ranked_nodes'][:, :, column, :int(archive['localization_budget'])]
                counts = event_counts(values, ranks, events, archive['times'], thresholds,
                                      config['alert_stride'], interval)
                cube = counts if cube is None else cube + counts
                check = event_counts(values, ranks, events, archive['times'], np.array([.1]),
                                     config['alert_stride'], interval)[0].sum(0)
                measured = primary[(primary.dataset == dataset) & (primary.seed == seed) &
                                   (primary.method == method)]
                faults = measured[measured.is_fault]
                controls = measured[measured.kind == 'untouched']
                expected = [faults.tp.sum(), faults.localization_iou.sum(), len(faults),
                            controls.flagged_issuances.sum(), controls.issuances.sum(), controls.fp.sum()]
                np.testing.assert_allclose(check[:6], expected, atol=1e-10, rtol=1e-10)
            cubes[dataset, method] = cube
            total = cube.sum(1)
            for index, threshold in enumerate(thresholds):
                row = total[index]
                curves.append({'dataset': dataset, 'method': method, 'rank_threshold': float(threshold),
                               'event_recall': row[0] / row[2], 'localization_iou': row[1] / row[2],
                               'untouched_exceedance': row[3] / row[4],
                               'background_alerts_per_network_day': row[5] / row[6]})
        verification.append({'dataset': dataset, 'all_30_methods_three_seeds_match_primary_counts': True})
    summaries = []; contrasts = []; settings = []
    comparisons = [('diffusion/entropy', 'diffusion/synchronization'),
                   ('diffusion/entropy', 'diffusion/matrix'),
                   ('diffusion/combined', 'diffusion/synchronization'),
                   ('diffusion/entropy', 'bootstrap/entropy')]
    repeats = config['bootstrap_repetitions']
    for primary_name in ['synthetic', 'intel', 'pems']:
        names = [d for d in datasets if ('synthetic' if d.startswith('synthetic') else d) == primary_name]
        rng = np.random.default_rng(42117)
        weights = {}
        for dataset in names:
            blocks = cubes[dataset, methods[0]].shape[1]
            indices = rng.integers(blocks, size=(repeats, blocks))
            weights[dataset] = np.stack([np.bincount(row, minlength=blocks) for row in indices])
        for budget in [.05, .1, .2]:
            boot = {}
            for method in methods:
                counts = np.zeros(len(FIELDS)); resampled = np.zeros((repeats, len(FIELDS)))
                for dataset in names:
                    cube = cubes[dataset, method]
                    total = cube.sum(1)
                    chosen = int(select_threshold(total, budget))
                    counts += total[chosen]
                    settings.append({'dataset': dataset, 'method': method, 'empirical_budget': budget,
                                     'selected_rank_threshold': float(grids[dataset][chosen]),
                                     'untouched_exceedance': total[chosen, 3] / total[chosen, 4]})
                    samples = np.einsum('rb,abk->rak', weights[dataset], cube)
                    selected = select_threshold(samples, budget)
                    resampled += samples[np.arange(repeats), selected]
                recalls = resampled[:, 0] / resampled[:, 2]
                ious = resampled[:, 1] / resampled[:, 2]
                boot[method] = (recalls, ious)
                summaries.append({'dataset': primary_name, 'method': method, 'empirical_budget': budget,
                                  'event_recall': {'mean': counts[0] / counts[2], **estimate(recalls)},
                                  'localization_iou': {'mean': counts[1] / counts[2], **estimate(ious)},
                                  'untouched_exceedance': counts[3] / counts[4],
                                  'background_alerts_per_network_day': counts[5] / counts[6],
                                  'transition_exceedance': counts[7] / counts[8],
                                  'recording_blocks': sum(cubes[d, method].shape[1] for d in names)})
            for left, right in comparisons:
                for index, metric in enumerate(['event_recall', 'localization_iou']):
                    point = lambda method: next(s[metric]['mean'] for s in summaries if
                        s['dataset'] == primary_name and s['method'] == method and s['empirical_budget'] == budget)
                    contrasts.append({'dataset': primary_name, 'empirical_budget': budget,
                                      'left': left, 'right': right, 'metric': metric,
                                      'mean': point(left) - point(right),
                                      **estimate(boot[left][index] - boot[right][index])})
    pd.DataFrame(curves).to_csv(root / 'results/retrospective_operating_curves.csv', index=False)
    write_json(root / 'results/retrospective_budgets.json', {
        'analysis': 'Post-primary descriptive comparison using reused untouched test controls; not prospective calibration',
        'threshold_selection': 'Largest attainable rank threshold within the empirical issuance budget; pooled seeds within configuration; no injected labels used',
        'resampling': 'Paired whole source blocks within each configuration; threshold reselected in every replicate; residual real-stream dependence remains',
        'primary_results_unchanged': True, 'verification': verification,
        'summaries': summaries, 'paired_contrasts': contrasts, 'settings': settings})
    print(json.dumps({'retrospective_operating_points': len(summaries), 'paired_contrasts': len(contrasts)}))
