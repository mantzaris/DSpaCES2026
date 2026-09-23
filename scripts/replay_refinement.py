"""GPU replay of representation changes and selective evidence acquisition."""
import argparse
import copy
import json
from pathlib import Path
import resource
import time
import numpy as np
import pandas as pd
import torch
from evidence_fusion.refinement_access import ProviderArchive, query_spec, immutable_digest
from evidence_fusion.refinement_gaussian import HierarchicalGaussian, MessageState, tensor_bytes


def cpu_prediction(pred):
    return {k: v.detach().cpu().numpy() for k, v in pred.items()}


def maximum_difference(a, b):
    return max(float(np.max(np.abs(a[k]-b[k]))) for k in a)


def write_scores(rows, predictions, model, count, origin, policy, active, outputs, targets,
                 slots, reference):
    groups = model['groups'][:count]
    for hi, horizon in enumerate((2, 12)):
        p = outputs[hi]
        finite = np.isfinite(targets[hi, :count])
        actual = targets[hi, :count]
        group_actual, seasonal, valid_house, house_y = [], [], [], []
        for group in range(16):
            ids = np.flatnonzero(groups == group)
            use = ids[finite[ids]]
            group_actual.append(float(actual[use].sum()) if len(use) else np.nan)
            seasonal.append(float(model['profile'][slots[hi], use].sum()))
            first = ids[0]
            valid_house.append(bool(finite[first]))
            house_y.append(float(actual[first]))
        definitions = [
            ('regional', np.array([np.nansum(actual)]), p['region_mean'][1:2], p['region_var'][1:2],
             np.array([sum(seasonal)])),
            ('group', np.array(group_actual), p['group_mean'][:, 1], p['group_var'][:, 1], np.array(seasonal)),
            ('household', np.array(house_y), p['group_mean'][:, 2], p['group_var'][:, 2],
             np.array([model['profile'][slots[hi], np.flatnonzero(groups==g)[0]] for g in range(16)]))]
        for level, y, mean, variance, baseline in definitions:
            ok = np.isfinite(y)
            error = mean[ok]-y[ok]
            sd = np.sqrt(variance[ok])
            radius = 1.6448536269514722*sd
            score = 2*radius+20*np.maximum(np.abs(error)-radius, 0)
            rows.append(dict(population=count, origin=origin, policy=policy, active_groups=active,
                horizon_steps=horizon, level=level, queries=int(ok.sum()),
                mae=float(np.mean(np.abs(error))), mse=float(np.mean(error**2)),
                coverage90=float(np.mean(np.abs(error)<=radius)), width90=float(np.mean(2*radius)),
                interval_score90=float(np.mean(score)), seasonal_mae=float(np.mean(np.abs(baseline[ok]-y[ok]))),
                missing_queries=int((~ok).sum()), observed_households=int(finite.sum())))
            # Every regional result and the first deterministic local query are saved.
            idx = 0
            predictions.append(dict(population=count, origin=origin, policy=policy,
                active_groups=active, horizon_steps=horizon, level=level,
                actual=float(y[idx]), mean=float(mean[idx]), variance=float(variance[idx]),
                seasonal=float(baseline[idx]), support='observed support' if level!='household' else 'first physical ID',
                full_evidence_mean=float(reference[hi]['region_mean'][1]) if level=='regional' else float(
                    reference[hi]['group_mean'][0, 1 if level=='group' else 2])))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    cfg = json.loads(Path('configs/regional_refinement.json').read_text())
    frozen = json.loads(Path('results/refinement/frozen_manifest.json').read_text())
    if immutable_digest('configs/regional_refinement.json') != frozen['config_sha256']:
        raise ValueError('configuration changed after preparation')
    folder = Path('data/regional/refinement')
    if immutable_digest(folder/'model.npz') != frozen['model_sha256']:
        raise ValueError('model changed after freeze')
    model = dict(np.load(folder/'model.npz', allow_pickle=False))
    out = Path('results/refinement/smoke' if args.smoke else 'results/refinement/replay')
    out.mkdir(parents=True, exist_ok=True)
    snapshots = folder/'snapshots'; snapshots.mkdir(exist_ok=True)
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.set_per_process_memory_fraction(.70)
    started = time.perf_counter()
    engine = HierarchicalGaussian(model, cfg['window_steps'], 'cuda')
    torch.cuda.synchronize()
    setup = time.perf_counter()-started
    origins = frozen['origins'][:1] if args.smoke else frozen['origins']
    counts = cfg['cohort_sizes'][:1] if args.smoke else cfg['cohort_sizes']
    levels = cfg['active_groups'][:1] if args.smoke else cfg['active_groups']
    metrics, predictions, costs, accesses, checks, macro_trace = [], [], [], [], [], []
    def save():
        for name, rows in [('metrics', metrics), ('predictions', predictions), ('costs', costs),
                           ('access_trace', accesses), ('checks', checks), ('macro_trace', macro_trace)]:
            if rows:
                pd.DataFrame(rows).to_csv(out/(name+'.csv'), index=False)
    for count in counts:
        for oi, origin in enumerate(origins):
            print('origin', count, oi, origin, flush=True)
            trace = []
            archive = ProviderArchive(folder, oi, count, model, origin, trace)
            with np.load(folder/('origin_%03d' % oi)/'query_support.npz') as supports:
                target_support, future_slots = supports['mask'], supports['slots']
            # Values are loaded for scoring only after predictions are formed.
            def make(group, kind):
                ids, mask, y, identity = archive.read(group, kind)
                weights, baseline = query_spec(model, ids, future_slots, target_support)
                begin_matrix = torch.cuda.Event(enable_timing=True)
                end_matrix = torch.cuda.Event(enable_timing=True)
                begin_matrix.record()
                message = engine.group_message(group, origin, ids, mask, y, kind,
                                               weights, baseline, identity)
                end_matrix.record(); torch.cuda.synchronize()
                trace[-1]['matrix_cuda_event_ms'] = begin_matrix.elapsed_time(end_matrix)
                trace[-1]['host_to_device_payload_bytes'] = int(ids.nbytes+mask.nbytes+y.nbytes+
                    sum(x.nbytes for x in weights+baseline))
                return message
            coarse_start = time.perf_counter()
            aggregate = [make(g, 'aggregate') for g in range(16)]
            state = MessageState(engine, origin)
            for msg in aggregate:
                state.replace(copy.copy(msg))
            coarse = [cpu_prediction(state.predictions(h)) for h in range(2)]
            torch.cuda.synchronize()
            coarse_seconds = time.perf_counter()-coarse_start
            coarse_bytes = state.bytes()
            # Strong uniform fine reference uses the SAME structure and streaming
            # elimination. It is not forced to hold a dense household covariance.
            del state
            fine_start = time.perf_counter()
            fine = MessageState(engine, origin)
            for g in range(16):
                msg = make(g, 'fine')
                msg.coarsen()  # registered forecasts need no resident leaf
                fine.replace(msg)
            reference = [cpu_prediction(fine.predictions(h)) for h in range(2)]
            fine_mean, fine_chol = fine.posterior()
            torch.cuda.synchronize()
            fine_seconds = time.perf_counter()-fine_start
            fine_bytes = fine.bytes()
            del fine, fine_mean, fine_chol, msg
            torch.cuda.empty_cache()
            # Selection uses coarse current posterior variance only, never target
            # support, target values, or unrevealed household residuals.
            sizes = np.bincount(model['groups'][:count], minlength=16)
            uncertainty_order = np.argsort(-coarse[0]['group_var'][:, 0]/sizes, kind='stable')
            orders = dict(fixed=np.roll(np.arange(16), -(oi%16)),
                          random=np.random.default_rng(cfg['seed']+oi+count).permutation(16),
                          uncertainty=uncertainty_order)
            saved_outputs = [('fixed_coarse', 0, coarse), ('uniform_fine_stream', 16, reference)]
            costs.append(dict(population=count, origin=oi, policy='uniform_fine_stream', active_groups=0,
                acquired_groups=16, update_seconds=fine_seconds, state_bytes=fine_bytes,
                retained_bytes=fine_bytes, coarse_setup_seconds=0., source_access_rows=sum(
                    x['returned_rows'] for x in trace if x['operation']=='fine'),
                gpu_peak_bytes=torch.cuda.max_memory_allocated(), complete_seconds=fine_seconds,
                recomputed_group_factors=16, reused_group_factors=0, factor_denominator=17,
                separator_factorizations=1))
            costs.append(dict(population=count, origin=oi, policy='fixed_coarse', active_groups=0,
                acquired_groups=0, update_seconds=coarse_seconds, state_bytes=coarse_bytes,
                retained_bytes=coarse_bytes, coarse_setup_seconds=coarse_seconds, source_access_rows=0,
                complete_seconds=coarse_seconds, recomputed_group_factors=16,
                reused_group_factors=0, factor_denominator=17, separator_factorizations=1))
            accesses.extend(dict(x, policy='shared_baseline_setup', active_groups=-1) for x in trace)
            trace.clear()
            for policy, order in orders.items():
                for active in levels:
                    selected = order[:active].tolist()
                    state = MessageState(engine, origin)
                    for msg in aggregate:
                        state.replace(copy.copy(msg))
                    # A: expose household conditional detail without obtaining any
                    # fine readings, then coarsen under exactly the same evidence.
                    rep_start = time.perf_counter()
                    g = selected[0]
                    ids, mask, ysum, _ = archive.read(g)
                    before = cpu_prediction(state.predictions(0))
                    state.expose_aggregate_detail(g, ids, mask, ysum)
                    exposed_bytes = tensor_bytes(state.messages[g].leaf)
                    after = cpu_prediction(state.predictions(0))
                    state.messages[g].coarsen()
                    torch.cuda.synchronize()
                    representation_seconds = time.perf_counter()-rep_start
                    representation_error = maximum_difference(before, after)
                    accesses.extend(dict(x, policy=policy, active_groups=active, phase='representation_A') for x in trace)
                    trace.clear()
                    torch.cuda.reset_peak_memory_stats()
                    begin = torch.cuda.Event(enable_timing=True); end = torch.cuda.Event(enable_timing=True)
                    start = time.perf_counter(); begin.record()
                    for g in selected:
                        state.replace(make(g, 'fine'))
                    for g in selected:
                        state.activate(g)
                    outputs = [cpu_prediction(state.predictions(h)) for h in range(2)]
                    end.record(); torch.cuda.synchronize()
                    update_seconds = time.perf_counter()-start
                    event_ms = begin.elapsed_time(end)
                    resident_bytes = state.bytes()
                    resident_cuda = torch.cuda.memory_allocated()
                    peak = torch.cuda.max_memory_allocated()
                    acquired_rows = sum(x['returned_rows'] for x in trace if x['operation']=='fine')
                    acquired_bytes = sum(x['file_bytes'] for x in trace)
                    accesses.extend(dict(x, policy=policy, active_groups=active, phase='acquisition_B') for x in trace)
                    trace.clear()
                    # Reassemble the separator independently of incremental
                    # subtract/add bookkeeping and compare mean AND covariance.
                    mean, chol = state.posterior()
                    j = engine.prior+sum((m.precision for m in state.messages.values()))
                    b = sum((m.information for m in state.messages.values()))
                    fresh_chol = torch.linalg.cholesky((j+j.T)/2)
                    fresh_mean = torch.cholesky_solve(b[:, None], fresh_chol).squeeze(1)
                    eye = torch.eye(engine.dimension, device='cuda', dtype=torch.float64)
                    covariance = torch.cholesky_solve(eye, chol)
                    fresh_cov = torch.cholesky_solve(eye, fresh_chol)
                    mean_error = float((mean-fresh_mean).abs().max())
                    covariance_error = float((covariance-fresh_cov).abs().max())
                    if oi == 0 and count == counts[-1] and active == levels[-1] and policy == 'uncertainty':
                        for label, p in [('coarse', coarse[0]), ('same_evidence_refined', after), ('fine_acquired', outputs[0])]:
                            macro_trace.append(dict(operation=label, group=selected[0],
                                region_mean=float(p['region_mean'][0]), region_sd=float(np.sqrt(p['region_var'][0])),
                                local_mean=float(p['group_mean'][selected[0], 2]),
                                local_sd=float(np.sqrt(p['group_var'][selected[0], 2])),
                                untouched_group=int(order[-1]),
                                untouched_household_mean=float(p['group_mean'][order[-1], 2])))
                    # Deliberately double-count the derived aggregate: not a method.
                    if oi == 0 and policy == 'fixed' and active == levels[0]:
                        bad_j = state.precision+sum(aggregate[g].precision for g in selected)
                        bad_h = state.information+sum(aggregate[g].information for g in selected)
                        bad_chol = torch.linalg.cholesky((bad_j+bad_j.T)/2)
                        bad_mean = torch.cholesky_solve(bad_h[:, None], bad_chol).squeeze(1)
                        checks.append(dict(population=count, origin=oi, policy='double_count_negative_control',
                            active_groups=active, separator_mean_error=float((bad_mean-mean).abs().max()),
                            separator_variance_trace=float(torch.trace(torch.cholesky_solve(eye, bad_chol))),
                            correct_variance_trace=float(torch.trace(covariance))))
                        del bad_j, bad_h, bad_chol, bad_mean
                    del j, b, fresh_chol, fresh_mean, fresh_cov, covariance, eye, mean, chol
                    # Conventional incremental inference retains the acquired leaf
                    # factors. Its prediction above is the matched-evidence baseline.
                    # Now physically evict those tensors; no hidden host copy.
                    start = time.perf_counter()
                    released = sum(m.coarsen() for m in state.messages.values())
                    torch.cuda.synchronize()
                    coarsen_seconds = time.perf_counter()-start
                    retained_bytes = state.bytes()
                    torch.cuda.empty_cache()
                    evicted_cuda = torch.cuda.memory_allocated()
                    cycle_error = max(maximum_difference(outputs[h], cpu_prediction(state.predictions(h))) for h in range(2))
                    restore_time = 0.
                    factor_error = 0.
                    for cycle in range(2):
                        start = time.perf_counter()
                        restored = make(selected[0], 'fine')
                        old = state.messages[selected[0]]
                        factor_error = max(factor_error, float((old.precision-restored.precision).abs().max()),
                                           float((old.information-restored.information).abs().max()))
                        if state.replace(restored):
                            raise AssertionError('same evidence was added twice')
                        del restored, old
                        state.activate(selected[0])
                        cycle_error = max(cycle_error, maximum_difference(outputs[0], cpu_prediction(state.predictions(0))))
                        state.messages[selected[0]].coarsen()
                        torch.cuda.synchronize()
                        restore_time += time.perf_counter()-start
                    accesses.extend(dict(x, policy=policy, active_groups=active, phase='rerefine_same_evidence') for x in trace)
                    trace.clear()
                    checks.append(dict(population=count, origin=oi, policy=policy, active_groups=active,
                        representation_error=representation_error, cycle_error=cycle_error, factor_error=factor_error,
                        separator_mean_error=mean_error, separator_covariance_error=covariance_error,
                        aggregation_mean_error=float(np.max(np.abs(outputs[0]['region_mean']-outputs[0]['group_mean'].sum(0))))))
                    if max(representation_error, cycle_error, factor_error, mean_error, covariance_error) > cfg['consistency_absolute_tolerance']:
                        raise ArithmeticError('frozen consistency tolerance exceeded')
                    costs.append(dict(population=count, origin=oi, policy=policy, active_groups=active,
                        acquired_groups=active, selected_groups=' '.join(map(str, selected)),
                        update_seconds=update_seconds, gpu_event_span_ms=event_ms,
                        complete_seconds=coarse_seconds+update_seconds,
                        coarse_setup_seconds=coarse_seconds, representation_seconds=representation_seconds,
                        representation_detail_bytes=exposed_bytes, state_bytes=resident_bytes,
                        retained_bytes=retained_bytes, released_detail_bytes=released,
                        cuda_resident_bytes=resident_cuda, cuda_after_eviction_bytes=evicted_cuda,
                        gpu_peak_bytes=peak, gpu_reserved_bytes=torch.cuda.memory_reserved(),
                        coarsen_seconds=coarsen_seconds, two_rerefine_seconds=restore_time,
                        source_access_rows=acquired_rows, source_file_bytes=acquired_bytes,
                        acquired_households=int(sizes[selected].sum()),
                        access_budget_cells=int(active*int(np.ceil(count/16))*cfg['window_steps']),
                        active_state_dimension=int(engine.dimension+sizes[selected].sum()*cfg['window_steps']),
                        total_state_dimension=int(engine.dimension+count*cfg['window_steps']),
                        recomputed_group_factors=active, reused_group_factors=16-active,
                        factor_denominator=17, separator_factorizations=1,
                        host_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
                    saved_outputs.append((policy, active, outputs))
                    if count == counts[-1] and policy == 'uncertainty' and active == levels[-1]:
                        mean, chol = state.posterior()
                        np.savez_compressed(snapshots/('snapshot_%03d.npz' % oi),
                            separator_mean=mean.cpu().numpy(), separator_cholesky=chol.cpu().numpy(),
                            meter_ids=model['meters'][:count], cutoff=origin, version=state.version,
                            model_sha256=frozen['model_sha256'], selected_groups=selected,
                            registered_coefficients=np.stack([p.coefficient.cpu().numpy() for m in state.messages.values() for p in m.forecasts]),
                            registered_intercepts=np.stack([(p.intercept+p.baseline).cpu().numpy() for m in state.messages.values() for p in m.forecasts]),
                            registered_covariances=np.stack([p.residual_covariance.cpu().numpy() for m in state.messages.values() for p in m.forecasts]),
                            regional_mean=outputs[0]['region_mean'], regional_variance=outputs[0]['region_var'])
                        del mean, chol
                    del state
            # Added coverage: admit the final training-eligible group after starting
            # with 15. Other likelihoods are unchanged; common posterior updates.
            if oi == 0:
                partial = MessageState(engine, origin)
                for msg in aggregate[:15]:
                    partial.replace(copy.copy(msg))
                old_mean = partial.posterior()[0].clone()
                start = time.perf_counter()
                partial.replace(make(15, 'aggregate'))
                added_mean = partial.posterior()[0]
                torch.cuda.synchronize()
                checks.append(dict(population=count, origin=oi, policy='added_coverage', active_groups=0,
                    added_households=int(sizes[15]), reused_group_factors=15, updated_separator=True,
                    seconds=time.perf_counter()-start, new_summary_bytes=trace[-1]['file_bytes'],
                    provenance_rows=trace[-1]['returned_rows'],
                    separator_change=float((added_mean-old_mean).abs().max())))
                accesses.extend(dict(x, policy='added_coverage', active_groups=0, phase='admission') for x in trace)
                trace.clear()
                del partial, old_mean, added_mean
            with np.load(folder/('origin_%03d' % oi)/'evaluation.npz') as evaluation:
                targets = evaluation['targets']
            for policy, active, outputs in saved_outputs:
                write_scores(metrics, predictions, model, count, oi, policy, active, outputs,
                             targets, future_slots, reference)
            del aggregate, saved_outputs, outputs, msg
            torch.cuda.empty_cache()
            save()
    summary = dict(completed=True, smoke=args.smoke, populations=counts, origins_per_population=len(origins),
        model_setup_seconds=setup, total_seconds=time.perf_counter()-started,
        device=torch.cuda.get_device_name(), vram_bytes=torch.cuda.get_device_properties(0).total_memory,
        torch=torch.__version__, cuda=torch.version.cuda, precision='float64', cpu_threads=4,
        gpu_peak_bytes=torch.cuda.max_memory_allocated(), host_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        source_file_bytes=sum(a['file_bytes'] for a in accesses), data_access_events=len(accesses),
        same_evidence_failures=0, london_heldout_sealed=True, bdg2_seals_unchanged=True,
        config_sha256=frozen['config_sha256'], model_sha256=frozen['model_sha256'],
        timing_caveat='CUDA event spans include gaps while synchronous provider I/O runs; they are not pure kernel time. Complete update includes reads/transfers/assembly/solve/query conversion; setup is charged separately and added to complete_seconds.')
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
