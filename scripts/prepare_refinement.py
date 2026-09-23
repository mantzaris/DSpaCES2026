"""Reuse the archive: GPU fit of one residual model; provider replay stores.

The preparer is a privileged provider/evaluator, NOT the inference consumer.
Only training and Q1 development paths are accepted by load_panel.
"""
import json
import hashlib
from pathlib import Path
import resource
import time
import numpy as np
import pandas as pd
import torch
from evidence_fusion.regional_data import load_panel, slots
from evidence_fusion.refinement_access import checked_window, immutable_digest


def main():
    cfg = json.loads(Path('configs/regional_refinement.json').read_text())
    folder = Path('data/regional/refinement')
    folder.mkdir(exist_ok=True)
    out = Path('results/refinement'); out.mkdir(exist_ok=True)
    source = Path('data/regional/model/model.npz')
    model = dict(np.load(source, allow_pickle=False))
    # Balanced training-frozen physical-ID order, without geographical meaning.
    model['groups'] = np.arange(len(model['meters'])) % cfg['groups']
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.cuda.set_per_process_memory_fraction(.70)
    device = 'cuda'
    start = time.perf_counter()
    y, times, meters, _ = load_panel('train', model['meters'])
    parse = time.perf_counter()-start
    # Reuse seasonal/loadings/dynamics; fit only the added residual AR layer.
    loading = torch.as_tensor(model['loadings'], dtype=torch.float64, device=device)
    scale = torch.as_tensor(model['scale'], dtype=torch.float64, device=device)
    n = len(meters)
    sums = torch.zeros((5, n), device=device, dtype=torch.float64)
    previous = previous_mask = None
    begin = torch.cuda.Event(enable_timing=True); end = torch.cuda.Event(enable_timing=True)
    begin.record()
    for lower in range(0, len(times), 256):
        upper = min(lower+256, len(times))
        raw = torch.as_tensor(y[lower:upper], dtype=torch.float64, device=device)
        seasonal = torch.as_tensor(model['profile'][slots(times[lower:upper])], dtype=torch.float64, device=device)
        mask = torch.isfinite(raw)
        res = torch.where(mask, (raw-seasonal)/scale, 0.)
        weights = mask.to(torch.float64)
        j = torch.einsum('th,hi,hj->tij', weights, loading, loading)
        j += torch.eye(loading.shape[1], device=device, dtype=torch.float64)*1e-5
        rhs = res @ loading
        states = torch.linalg.solve(j, rhs[:, :, None]).squeeze(-1)
        errors = (res-states@loading.T)*scale
        sums[0] += (errors.square()*mask).sum(0)
        sums[1] += mask.sum(0)
        extended = errors if previous is None else torch.cat((previous[None], errors))
        extended_mask = mask if previous_mask is None else torch.cat((previous_mask[None], mask))
        adjacent = extended_mask[1:] & extended_mask[:-1]
        sums[2] += (extended[1:]*extended[:-1]*adjacent).sum(0)
        sums[3] += (extended[:-1].square()*adjacent).sum(0)
        sums[4] += adjacent.sum(0)
        previous, previous_mask = errors[-1], mask[-1]
    fraction = cfg['measurement_variance_fraction']
    variance = (sums[0]/sums[1]).clamp_min(1e-6)
    ar = (sums[2]/sums[3].clamp_min(1e-12)/(1-fraction)).clamp(
        -cfg['maximum_abs_detail_ar'], cfg['maximum_abs_detail_ar'])
    model.update(detail_var=((1-fraction)*variance).cpu().numpy(),
                 measurement_var=(fraction*variance).cpu().numpy(), detail_ar=ar.cpu().numpy())
    end.record(); torch.cuda.synchronize()
    training = dict(rows=int(sums[1].sum().item()), adjacent_pairs=int(sums[4].sum().item()),
                    ar_min=float(ar.min()), ar_median=float(ar.median()), ar_max=float(ar.max()),
                    parse_seconds=parse, gpu_fit_ms=begin.elapsed_time(end),
                    total_seconds=time.perf_counter()-start,
                    device=torch.cuda.get_device_name(), vram_bytes=torch.cuda.get_device_properties(0).total_memory,
                    gpu_peak_bytes=torch.cuda.max_memory_allocated(),
                    parent_model_sha256=immutable_digest(source),
                    model_change='fixed seasonal/factor model plus household AR residual; nugget fraction fixed .2, not identified measurement noise')
    np.savez_compressed(folder/'model.npz', **model)
    del y, raw, seasonal, res, j, rhs, states, errors, weights, mask
    torch.cuda.empty_cache()
    start = time.perf_counter()
    development, times, _, _ = load_panel('development', meters)
    parse_dev = time.perf_counter()-start
    origins = json.loads(Path(cfg['origins_from']).read_text())['origins'][:cfg['origins_count']]
    trace = []
    for oi, origin in enumerate(origins):
        checked_window(origin, cfg['window_steps'])
        pos = int(times.get_loc(origin))
        window = slice(pos-cfg['window_steps']+1, pos+1)
        location = folder/('origin_%03d' % oi); location.mkdir(exist_ok=True)
        residual = (development[window]-model['profile'][slots(times[window])]).T.astype(float)
        future = np.array([pos+h for h in cfg['horizons_steps']])
        targets = development[future]
        np.savez_compressed(location/'evaluation.npz', targets=targets, slots=slots(times[future]),
                            timestamps=times[future].values.astype(str))
        np.savez_compressed(location/'query_support.npz', mask=np.isfinite(targets), slots=slots(times[future]))
        for g in range(cfg['groups']):
            ids = np.flatnonzero(model['groups'] == g)
            values = residual[ids]; mask = np.isfinite(values)
            version = hashlib.sha256(np.where(mask, values, 0.).tobytes()+mask.tobytes()).hexdigest()
            np.savez_compressed(location/('group_%02d_fine.npz' % g), ids=ids, mask=mask, residual=values, evidence_version=version)
            summary = dict(ids=ids, mask=mask, evidence_version=version)
            for count in cfg['cohort_sizes']:
                summary['sum_%d' % count] = np.nansum(values[ids<count], axis=0)
            np.savez_compressed(location/('group_%02d_aggregate.npz' % g), **summary)
            trace.append(dict(origin=oi, cutoff=origin, group=g, valid_rows=int(mask.sum()),
                              households=len(ids), numeric_source_bytes=int(values.nbytes)))
    training['model_sha256'] = immutable_digest(folder/'model.npz')
    training['peak_host_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    preparation = dict(development_parse_seconds=parse_dev, provider_preparation_seconds=time.perf_counter()-start,
        valid_window_rows=sum(r['valid_rows'] for r in trace), origins=len(origins),
        development_source_file_bytes=sum(p.stat().st_size for p in Path('data/regional/parquet/development').glob('*/*.parquet')),
        provider_store_bytes=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()),
        all_source_rows_read_for_initial_summary=True,
        no_online_sensor_ingestion_saving=True,
        caveat='Provider setup reads Q1 once; only frozen windows retained. Scored future values remain in evaluator files, inaccessible to consumer API.')
    (out/'training.json').write_text(json.dumps(training, indent=2)+'\n')
    (out/'preparation.json').write_text(json.dumps(preparation, indent=2)+'\n')
    (out/'provider_preparation_trace.json').write_text(json.dumps(trace, indent=2)+'\n')
    (out/'frozen_manifest.json').write_text(json.dumps(dict(config=cfg, origins=origins,
        config_sha256=immutable_digest('configs/regional_refinement.json'), model_sha256=training['model_sha256'],
        meter_order='sorted physical IDs inherited unchanged; nested prefixes 1024/2048/4194',
        groups='sorted eligible physical-ID index modulo 16; balanced synthetic providers, no geographical meaning',
        stage1_forecast_and_solver_results_preserved=True), indent=2)+'\n')
    print(json.dumps(dict(training=training, preparation=preparation), indent=2))


if __name__ == '__main__':
    main()
