"""Recover selected joint raw ensembles and check against frozen feature draws."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from .data import load_data
from .experiment import load_models
from .features import Scan
from .reference import BlockBootstrap, issue_reference
from .utils import Budget, digest, write_json


@torch.no_grad()
def save_ensembles(root: Path, config: dict, budget: Budget) -> None:
    output = root / 'experiments/selected-ensembles'
    (output / 'samples').mkdir(parents=True, exist_ok=True)
    records = []; seed = 17; end = 203; horizon = 120
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    for dataset in ['synthetic64', 'intel', 'pems']:
        data = load_data(root, dataset); values = data.standardized
        directory = root / 'experiments/full' / f'score-{dataset}-physical-{seed}'
        events = json.loads((directory / 'events.json').read_text())
        indices = [0, 18, len(events)-1] if dataset == 'synthetic64' else [len(events)-2]
        model, _ = load_models(data, config, seed, root / 'experiments/full', 'cuda')
        bootstrap = BlockBootstrap(data, config['context'], horizon, 'cuda')
        scan = Scan(data.adjacency, data.coordinates, data.channels, config, 'cuda')
        for index in indices:
            event = events[index]
            start = event['base_start'] + end - horizon + 1
            observed = torch.as_tensor(values[start:start+horizon], device='cuda')
            for reference in ['diffusion', 'bootstrap']:
                budget.check()
                draws = issue_reference(model, data, values, start, horizon, config, 'cuda',
                                        reference, bootstrap, seed+start)
                reconstructed = scan.extract(draws.masked_fill(~torch.isfinite(observed)[None], float('nan'))).values.cpu().numpy()
                saved = directory / 'samples' / f'{reference}-base{event["base"]}-time{end}.npz'
                with np.load(saved) as archive:
                    expected = archive['features']
                np.testing.assert_allclose(reconstructed, expected, rtol=1e-5, atol=1e-5, equal_nan=True)
                difference = np.abs(reconstructed-expected)
                maximum_error = float(np.nanmax(difference)) if np.isfinite(difference).any() else None
                path = output / 'samples' / f'{dataset}-event{index}-time{end}-{reference}.npz'
                np.savez_compressed(path, samples=draws.cpu().numpy(),
                                    clean_target=values[start:start+horizon],
                                    history=values[start-config['context']:start],
                                    timestamps=data.timestamps[start:start+horizon],
                                    center=data.center, scale=data.scale)
                records.append({'dataset': dataset, 'event': event['id'], 'event_index': index,
                                'observation_index': end, 'target_start': start, 'reference': reference,
                                'sampling_seed': seed+start, 'model_seed': seed,
                                'shape': list(draws.shape), 'path': str(path.relative_to(root)),
                                'sha256': digest(path), 'saved_feature_sha256': digest(saved),
                                'maximum_feature_recovery_error': maximum_error})
    write_json(output / 'manifest.json', {
        'purpose': 'Selected raw joint ensembles recovered from frozen checkpoints/seeds; no detector outcomes changed',
        'units': 'Training-standardized; multiply by scale and add center for original channel units',
        'validation': 'Every reconstructed feature draw agrees with its original saved array, including NaN support, at rtol=atol=1e-5',
        'selection': 'Observation index 203 in all five exported dashboard cases, both references',
        'records': records})
