"""Frozen scale-1/2 sensitivity from saved joint references; no model fitting.

Run on the experiment host. Use --report-only to regenerate compact numerical
results on a CPU from the accepted prediction and calibration archives.
"""
import argparse
import gzip
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from iot_entropy.calibration import rank_pvalues
from iot_entropy.data import load_data
from iot_entropy.evaluation import alert_intervals, match_events, bootstrap_mean, event_pr_curve
from iot_entropy.extension import floor_from_development, support_row
from iot_entropy.extension_data import episode_values, verify_target
from iot_entropy.extension_reporting import read_json, finite_median
from iot_entropy.extension_scoring import extract, summaries, score, summarize_scores, primary_localization
from iot_entropy.features import Scan
from iot_entropy.localization import set_metrics
from iot_entropy.temporal import multiscale_trajectory
from iot_entropy.utils import Budget, digest, write_json
from iot_entropy.extension_budget import components, authorized_hours

ROOT = Path(__file__).resolve().parents[1]
NS = ROOT/'experiments/extension-v2'
OUT = ROOT/'results/extension-v2'
SPEC = read_json(ROOT/'configs/extension-multiscale-v2.json')


def frozen_methods():
    return [f'{ref}/scale{scale}/{family}' for ref in SPEC['references']
            for scale in SPEC['scales'] for family in SPEC['families']]


def run_configuration(name, budget, check_stage):
    source = NS/f'{name}-{SPEC["seed"]}'
    destination = NS/'multiscale'/source.name
    destination.mkdir(parents=True, exist_ok=True)
    if (destination/'status.json').exists():
        return
    started = time.monotonic()
    config = read_json(source/'configuration.json')
    selected = dict(config, windows=[SPEC['physical_window']])
    data = load_data(ROOT, name)
    lineage = read_json(source/'data-lineage.json')
    if name.startswith('synthetic'):
        with np.load(NS/'cache'/f'{name}-backgrounds.npz') as archive:
            data = replace(data, values=np.concatenate([data.values[:data.bounds[1]], archive['extension_values']]),
                           timestamps=np.concatenate([data.timestamps[:data.bounds[1]], archive['extension_timestamps']]),
                           bounds=archive['bounds'], episode_bounds=archive['episode_bounds'])
    values = data.standardized
    scan = Scan(data.adjacency, data.coordinates, data.channels, selected, 'cuda')
    old_scan = Scan(data.adjacency, data.coordinates, data.channels, config, 'cuda')
    indices = [j for j, r in enumerate(old_scan.records) if r['window'] == 96]
    assert [dict(r, index=j) for j, r in enumerate(old_scan.records[k] for k in indices)] == scan.records
    with np.load(source/'development-parameters.npz') as p:
        spatial_floor = torch.tensor(p['spatial'][indices], device='cuda')
        first_floor = torch.tensor(p['temporal_96'], device='cuda')
    dev_indices = read_json(source/'development-selection.json')['indices']
    development = []
    support = []
    for start in dev_indices:
        budget.check(); check_stage(); verify_target(data, start, 48, 120, 1)
        raw = torch.tensor(values[start:start+120], device='cuda')
        item = multiscale_trajectory(raw, 96, 2, selected)
        development.append(item['u'])
        support += support_row({'temporal': {96: item}},
                               {'split': 'development', 'scale': 2, 'target_start': start})
    floors = {1: {'spatial': spatial_floor, 'temporal': {96: first_floor}},
              2: {'spatial': spatial_floor, 'temporal': {96: floor_from_development(torch.cat(development))}}}
    np.savez_compressed(destination/'development-parameters.npz', spatial=spatial_floor.cpu().numpy(),
                        temporal_scale1=first_floor.cpu().numpy(),
                        temporal_scale2=floors[2]['temporal'][96].cpu().numpy(), indices=dev_indices)
    methods = frozen_methods(); times = np.arange(167, 312, 12)
    events = read_json(source/'events.json')
    top = config['localization_budget']; nf = len(SPEC['families'])
    references = {}

    def features(raw):
        spatial = extract(raw, scan, selected, include_temporal=False)
        return {s: {**spatial, 'temporal': {96: multiscale_trajectory(raw, 96, s, selected)}}
                for s in SPEC['scales']}

    def reference(raw, start, ref):
        cached = torch.tensor(np.load(NS/'cache'/source.name/f'{start}-{ref}.npy'), device='cuda')
        assert len(cached) == SPEC['generated_samples']
        return cached.masked_fill(~torch.isfinite(raw)[None], float('nan'))

    def summarize(generated):
        answer = {}
        for s in SPEC['scales']:
            ref = summaries(generated[s], floors[s], selected)
            ref['spatial'].enough = torch.isfinite(generated[s]['spatial'].values).sum(0) >= SPEC['minimum_reference_samples']
            answer[s] = ref
        return answer

    def measure(actual, generated, summary):
        maxima = []; available = []; ranks = []
        for s in SPEC['scales']:
            scored = score(actual[s], generated[s], summary[s], scan, floors[s], selected, config['top_fraction'])
            names, m, a, r = summarize_scores(scored, scan, values.shape[1], top)
            columns = [names.index(f) for f in SPEC['families']]
            maxima.extend(m[columns]); available.extend(a[columns])
            ranks.extend([r[j, primary_localization(names[j])] for j in columns])
        return np.asarray(maxima), np.asarray(available), np.asarray(ranks)

    cal_indices = data.issuance_indices(2, 48, 120, 168)
    calibration = []; cal_available = []
    for start0 in cal_indices:
        budget.check(); check_stage(); start = int(start0); verify_target(data, start, 48, 120, 2)
        raw = torch.tensor(values[start:start+120], device='cuda'); actual = features(raw)
        m = []; a = []
        for ref in SPEC['references']:
            generated = features(reference(raw, start, ref)); summary = summarize(generated)
            scores0, availability0, _ = measure(actual, generated, summary)
            m.extend(scores0); a.extend(availability0)
        calibration.append(m); cal_available.append(a)
    calibration = np.asarray(calibration, dtype=np.float64)
    shape = (len(events), len(times), len(methods))
    scores = np.full(shape, -np.inf, dtype=np.float32)
    available = np.zeros(shape, dtype=np.float32)
    ranks = np.zeros((*shape, top), dtype=np.int16)
    for bi, base in enumerate(lineage['extension_blocks']):
        ids = [i for i, e in enumerate(events) if e['base'] == bi]
        changed = {i: episode_values(data, values, base, events[i], config, 'cuda') for i in ids}
        for ti, end0 in enumerate(times):
            budget.check(); check_stage(); end = int(end0); start = base[0]+end-119
            verify_target(data, start, 48, 120, 3)
            clean = torch.tensor(values[start:start+120], device='cuda')
            references = {}
            for ref in SPEC['references']:
                samples = reference(clean, start, ref); generated = features(samples)
                references[ref] = (samples, generated, summarize(generated))
            for ei in ids:
                raw = torch.tensor(changed[ei][end-119:end+1], device='cuda'); actual = features(raw)
                for s in SPEC['scales']:
                    support += support_row(actual[s], {'split': 'test', 'event': ei, 'end': end, 'scale': s})
                for ri, ref in enumerate(SPEC['references']):
                    samples, generated, summary = references[ref]
                    if events[ei]['kind'] == 'dropout':
                        generated = features(samples.masked_fill(~torch.isfinite(raw)[None], float('nan')))
                        summary = summarize(generated)
                    m, a, r = measure(actual, generated, summary)
                    sl = slice(ri*2*nf, (ri+1)*2*nf)
                    scores[ei, ti, sl] = m; available[ei, ti, sl] = a; ranks[ei, ti, sl] = r
        print(json.dumps({'multiscale': name, 'completed_base': bi, 'cumulative_seconds': budget.elapsed}), flush=True)
    pvalues = np.stack([rank_pvalues(calibration[:, j], scores[:, :, j]) for j in range(len(methods))], -1)
    with np.load(NS/'window-support'/source.name/'predictions.npz') as archive:
        baseline = {k: archive[k] for k in archive.files}
    max_score_error = 0.; max_cal_error = 0.
    for ri, ref in enumerate(SPEC['references']):
        for fi, family in enumerate(SPEC['families']):
            column = ri*2*nf+fi
            previous = baseline['methods'].tolist().index(f'{ref}/ceil52/96/{family}')
            np.testing.assert_allclose(scores[:, :, column], baseline['scores'][:, :, previous], rtol=2e-5, atol=2e-5)
            np.testing.assert_allclose(calibration[:, column], baseline['calibration'][:, previous], rtol=2e-5, atol=2e-5)
            np.testing.assert_array_equal(pvalues[:, :, column], baseline['pvalues'][:, :, previous])
            # The independent audit takes a CUDA float32 mean; the compact
            # summarizer takes a CPU float64 mean then stores float32. Compare
            # the underlying integer valid-group counts exactly, not their
            # differently rounded quotients (observed maximum: one float32 ulp).
            np.testing.assert_array_equal(np.rint(available[:, :, column]*len(scan.records)),
                                          np.rint(baseline['availability'][:, :, previous]*len(scan.records)))
            np.testing.assert_allclose(available[:, :, column], baseline['availability'][:, :, previous], atol=1e-7, rtol=0)
            finite = np.isfinite(scores[:, :, column])
            if finite.any(): max_score_error = max(max_score_error, float(np.max(np.abs(scores[:, :, column][finite]-baseline['scores'][:, :, previous][finite]))))
            finite = np.isfinite(calibration[:, column])
            if finite.any(): max_cal_error = max(max_cal_error, float(np.max(np.abs(calibration[:, column][finite]-baseline['calibration'][:, previous][finite]))))
            if family in ['S', 'SB']:
                np.testing.assert_array_equal(scores[:, :, column], scores[:, :, column+nf])
                np.testing.assert_array_equal(pvalues[:, :, column], pvalues[:, :, column+nf])
    unique, index = np.unique(ranks.reshape(-1, top), axis=0, return_inverse=True)
    np.testing.assert_array_equal(unique[index].reshape(ranks.shape), ranks)
    np.savez_compressed(destination/'predictions.npz', methods=methods, times=times,
        scores=scores, pvalues=pvalues.astype('float32'), availability=available,
        calibration=calibration, calibration_availability=cal_available,
        rankings_unique=unique, ranking_index=index.reshape(shape).astype('uint32'))
    support = [{k: (None if isinstance(v, float) and not np.isfinite(v) else v)
                for k, v in row.items()} for row in support]
    support_bytes = json.dumps(support, separators=(',', ':'), allow_nan=False).encode()
    (destination/'support.json.gz').write_bytes(gzip.compress(support_bytes, compresslevel=9, mtime=0))
    write_json(destination/'status.json', {'complete': True, 'dataset': name, 'seed': SPEC['seed'],
        'protocol_revision': 'bd04b4e1', 'protocol_sha256': digest(ROOT/'docs/extension-multiscale-protocol.md'),
        'specification_sha256': digest(ROOT/'configs/extension-multiscale-v2.json'),
        'parent_configuration_sha256': digest(source/'configuration.json'),
        'parent_events_sha256': digest(source/'events.json'),
        'predictions_sha256': digest(destination/'predictions.npz'),
        'scale1_max_score_error': max_score_error, 'scale1_max_calibration_error': max_cal_error,
        'scale1_exact_pvalues_and_valid_counts': True, 'unchanged_spatial_families': True,
        'availability_note': 'Exact valid-group counts; CPU/GPU means may differ by a float32 ulp.',
        'elapsed_seconds': time.monotonic()-started})


def report():
    event_rows = []; summaries_out = []; curves = []
    for name in SPEC['datasets']:
        source = NS/f'{name}-{SPEC["seed"]}'; directory = NS/'multiscale'/source.name
        if not (directory/'status.json').exists(): continue
        events = read_json(source/'events.json'); config = read_json(source/'configuration.json')
        with np.load(directory/'predictions.npz') as x: pred = {k: x[k] for k in x.files}
        ranks = pred['rankings_unique'][pred['ranking_index']]
        for mi, method in enumerate(pred['methods'].tolist()):
            reference, scale, family = method.split('/'); scale = int(scale[-1])
            pvalues = rank_pvalues(pred['calibration'][:, mi], pred['scores'][:, :, mi])
            np.testing.assert_allclose(pvalues, pred['pvalues'][:, :, mi], rtol=0, atol=6e-8)
            rows = []
            for ei, event in enumerate(events):
                alerts = alert_intervals(pred['times'], pvalues[ei] <= SPEC['alpha'], 12)
                truth = [(event['onset'], event['onset']+event['duration']-1)] if event['is_fault'] else []
                matched = match_events(alerts, truth)
                localization = dict(precision=0., recall=0., f1=0., iou=0.)
                if matched['tp']:
                    tick = int(np.flatnonzero(pred['times'] == alerts[matched['matches'][0][0]][0])[0])
                    localization = set_metrics(ranks[ei, tick, mi].tolist(), event['nodes'])
                row = {'configuration': name, 'dataset': 'synthetic' if name.startswith('synthetic') else name,
                    'seed': SPEC['seed'], 'reference': reference, 'scale': scale, 'family': family,
                    'event': ei, 'base': event['base'], 'block': f'{name}/{event["base"]}',
                    'kind': event['kind'], 'is_fault': event['is_fault'], 'duration': event['duration'],
                    'severity': event['severity'], 'tp': matched['tp'], 'fp': matched['fp'], 'fn': matched['fn'],
                    'delay_samples': matched['delays'][0] if matched['tp'] else np.nan,
                    'background_exceedance': float((pvalues[ei] <= SPEC['alpha']).mean()),
                    'availability': float(pred['availability'][ei, :, mi].mean()),
                    **{'localization_'+k: v for k, v in localization.items()}}
                rows.append(row)
            event_rows.extend(rows); frame = pd.DataFrame(rows); faults = frame[frame.is_fault]
            controls = frame[frame.kind == 'untouched']; tp, fp, fn = frame[['tp', 'fp', 'fn']].sum()
            curve = event_pr_curve([{'times': pred['times'], 'pvalues': pvalues[i],
                'events': [(e['onset'], e['onset']+e['duration']-1)] if e['is_fault'] else []}
                for i, e in enumerate(events)], np.r_[0, np.arange(1, len(pred['calibration'])+2)/(len(pred['calibration'])+1)], 12)
            curves.append({'configuration': name, 'method': method, **curve})
            summaries_out.append({'configuration': name, 'reference': reference, 'scale': scale, 'family': family,
                'recall': tp/(tp+fn), 'precision': tp/max(tp+fp, 1),
                'event_auprc_envelope': curve['event_auprc_envelope'],
                'unconditional_iou': faults.localization_iou.mean(),
                'detected_iou': faults.loc[faults.tp > 0, 'localization_iou'].mean(),
                'background_exceedance': controls.background_exceedance.mean(),
                'availability': frame.availability.mean(), 'median_delay_samples': finite_median(faults.delay_samples.values),
                'calibration_units': len(pred['calibration'])})
    frame = pd.DataFrame(event_rows)
    frame.to_csv(OUT/'multiscale-events.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    comparisons = []
    fault = frame[frame.is_fault]
    for (dataset, reference, family), group in fault.groupby(['dataset', 'reference', 'family']):
        for metric in ['tp', 'localization_iou']:
            pivot = group.pivot(index=['block', 'event'], columns='scale', values=metric)
            blocks = (pivot[2]-pivot[1]).groupby(level='block').mean()
            comparisons.append({'dataset': dataset, 'reference': reference, 'family': family, 'metric': metric,
                'contrast': 'scale2 minus scale1, equal block weights; exploratory',
                **bootstrap_mean(blocks.values, SPEC['bootstrap_seed'], SPEC['bootstrap_repetitions'])})
    write_json(OUT/'multiscale-calibrated.json', {'summary': summaries_out, 'paired': comparisons,
        'complete_configurations': sorted(frame.configuration.unique()), 'specification': SPEC,
        'provenance': 'Post-primary exploratory sensitivity; same events and backgrounds, seed17 only.'})
    (OUT/'multiscale-event-pr-curves.json.gz').write_bytes(gzip.compress(json.dumps(curves, separators=(',', ':')).encode(), 9, mtime=0))
    print(json.dumps({'multiscale_report_configurations': len(frame.configuration.unique()),
                      'methods_per_configuration': len(frozen_methods()), 'event_rows': len(frame)}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--report-only', action='store_true'); args = parser.parse_args()
    if args.report_only:
        report(); return
    validation = read_json(NS/'multiscale-validation.json')
    assert validation['returncode'] == 0
    prior = sum(components(ROOT).values())
    stage_prior = sum(read_json(p)['elapsed_seconds'] for p in NS.glob('multiscale-attempt-*.json'))
    authorized = authorized_hours(ROOT)
    budget = Budget(min(SPEC['cumulative_gpu_hour_limit'], authorized), prior)
    started = time.monotonic(); torch.set_num_threads(4)
    def check_stage():
        if time.monotonic()-started+stage_prior >= SPEC['stage_hour_limit']*3600:
            raise TimeoutError('Frozen multiscale stage budget exhausted')
    attempt = NS/f'multiscale-attempt-{len(list(NS.glob("multiscale-attempt-*.json")))}.json'
    try:
        with torch.no_grad():
            for name in SPEC['datasets']:
                budget.check(); check_stage(); run_configuration(name, budget, check_stage)
    finally:
        write_json(attempt, {'elapsed_seconds': time.monotonic()-started, 'cumulative_seconds': budget.elapsed,
                            'limit_seconds': authorized*3600, 'stage_limit_seconds': SPEC['stage_hour_limit']*3600})
    report()


if __name__ == '__main__':
    main()
