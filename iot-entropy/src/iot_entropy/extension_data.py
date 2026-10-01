"""Independent simulations, explicit recording reuse, and frozen fault draws."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from .data import SensorData, load_data
from .experiment import base_episodes, event_manifest
from .synthetic import fault_nodes, inject, simulate, system
from .utils import digest


def extension_data(root: Path, name: str, config: dict, device: str) -> tuple[SensorData, list, dict]:
    original = load_data(root, name)
    lineage = {'source_processed_sha256': digest(root/'data/processed'/f'{name}.npz'),
               'training_scaling_reused': True, 'primary_channels': original.channels,
               'units': original.units, 'interval_seconds': original.interval_seconds}
    if name.startswith('synthetic'):
        n = len(original.node_ids)
        coords, adjacency, transition, _ = system(n, config['synthetic_graph_seed'])
        values = [original.values[:original.bounds[1]]]
        dates = [original.timestamps[:original.bounds[1]]]
        episodes = original.episode_bounds[original.episode_bounds[:,2] == 0].tolist()
        cursor = int(original.bounds[1]); bounds = [0,cursor]; seeds = []
        for partition, (number, length) in enumerate([(4,312),(32,256),(config['base_episodes'],312)],1):
            for episode in range(number):
                seed = config['synthetic_seed_base']+1000*n+100*partition+episode
                block = simulate(coords, transition, length, seed, device)
                values.append(block)
                dates.append(np.datetime64('2020-01-01','ns').astype('int64') +
                    (np.arange(length,dtype=np.int64)+256+seed%288)*300*10**9)
                episodes.append([cursor,cursor+length,partition])
                seeds.append({'split':partition,'episode':episode,'seed':seed,
                              'start':cursor,'stop':cursor+length})
                cursor += length
            bounds.append(cursor)
        data = replace(original, values=np.concatenate(values), timestamps=np.concatenate(dates),
                       bounds=np.asarray(bounds), episode_bounds=np.asarray(episodes))
        bases = base_episodes(data,config)
        lineage.update({'background_status':'independent new synthetic seeds', 'seeds':seeds,
                        'old_test_overlap_rows':0, 'bounds':bounds})
    else:
        data = original
        v1_config = dict(config, base_episodes=12)
        old = base_episodes(original,v1_config)
        candidates = base_episodes(original,dict(config,base_episodes=100000))
        unused = [b for b in candidates if not any(b[0] < z[1] and z[0] < b[1] for z in old)]
        # Original fidelity audit inspected six 120-row targets with 48-row context.
        audit = [(int(original.bounds[3])+168*i,int(original.bounds[3])+168*(i+1)) for i in range(6)]
        unused = [b for b in unused if not any(b[0] < z[1] and z[0] < b[1] for z in audit)]
        bases = unused[:config['base_episodes']]
        for b in candidates:
            if len(bases) >= config['base_episodes']:
                break
            if b not in bases:
                bases.append(b)
        overlap = sum(max(0,min(b[1],z[1])-max(b[0],z[0])) for b in bases for z in old)
        lineage.update({'background_status':'reused inspected real recordings' if overlap else
                         'blocks excluded from original primary and six-unit fidelity audit; whole release previously available',
                        'old_test_overlap_rows':overlap,'original_primary_blocks':old,
                        'original_fidelity_intervals':audit, 'bounds':data.bounds})
        # Expanded audit found a v1 long-window diagnostic spanning these blocks.
        # This changes the reuse disclosure, not the already frozen selection.
        lineage['validation_status'] = 'exploratory reused recording backgrounds'
        lineage['prior_global_diagnostic_overlap'] = True
    lineage['extension_blocks'] = bases
    lineage['split_episodes'] = data.episode_bounds
    return data, bases, lineage


def new_events(data: SensorData, config: dict, bases: list) -> list[dict]:
    events = event_manifest(data,config,bases)
    for i, event in enumerate(events):
        if event['is_fault']:
            event['seed'] = config['fault_seed_base']+i
            event['nodes'] = fault_nodes(data.adjacency, len(event['nodes']),
                                        event['seed'], event['partly_disconnected'])
            # Do not carry the old node set's connected-component count.
            from scipy.sparse.csgraph import connected_components
            sub = data.adjacency[np.ix_(event['nodes'],event['nodes'])] > 0
            event['affected_components'] = int(connected_components(sub,directed=False)[0])
        else:
            event['seed'] = config['control_seed_base']+event['base']
        start,stop = bases[event['base']]
        event.update({'base_start':start,'base_stop':stop,'extension':True})
    return events


def episode_values(data: SensorData, values: np.ndarray, base: tuple, event: dict,
                   config: dict, device: str) -> np.ndarray:
    clean = values[base[0]:base[1]].copy()
    if event['kind'] == 'untouched':
        return clean
    if event['kind'] == 'decouple' and data.name.startswith('synthetic'):
        index = int(np.where(data.episode_bounds[:,0] == base[0])[0][0])
        test_index = index-int(np.where(data.episode_bounds[:,2] == 3)[0][0])
        seed = config['synthetic_seed_base']+1000*len(data.node_ids)+300+test_index
        coords,_,transition,_ = system(len(data.node_ids),config['synthetic_graph_seed'])
        x = simulate(coords,transition,len(clean),seed,device,event)
        x = ((x-data.center)/data.scale).astype('float32')
        np.testing.assert_allclose(x[:event['onset']],clean[:event['onset']],rtol=2e-5,atol=2e-5)
        return x
    return inject(clean,event['nodes'],event['onset'],event['duration'],
                  event['kind'],event['severity'],event['seed'])


def verify_target(data: SensorData, start: int, context: int, horizon: int, split: int) -> None:
    contained = [int(a) <= start-context and start+horizon <= int(b)
                 for a,b,p in data.episode_bounds if p == split]
    if not any(contained):
        raise ValueError('Context/target crosses partition or episode')
