import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from evidence_fusion.chronological_splits import sealed_read, split_mask, causal_target_mask
from evidence_fusion.provider_models import calendar_features, qr_operator


def audit(cache='data', out='manifests'):
    root = Path(cache)
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    frame = sealed_read(root / 'electricity_pretest.csv')
    metadata = pd.read_csv(root / 'metadata.csv').set_index('building_id')
    cleaned = sealed_read(root / 'cleaned_pretest.csv')
    train = np.asarray(split_mask(frame.index, '2016-01-01', '2016-10-01'))
    features, names = calendar_features(frame.index)
    all_rows, candidates = [], {}
    for name in sorted(frame.columns):
        y = frame[name].to_numpy(dtype=float)
        site = str(metadata.loc[name, 'site_id'])
        timezone = str(metadata.loc[name, 'timezone'])
        causal = causal_target_mask(frame.index, timezone)
        # All day observations must be present and physically interpretable.
        valid = np.isfinite(y) & (y >= 0)
        daily = pd.Series(valid & causal & train, index=frame.index).groupby(frame.index.normalize()).sum()
        days = list(daily[daily == 24].index)
        fraction = float(valid[train].mean())
        mean = float(np.mean(y[train & valid])) if np.any(train & valid) else 0.
        variation = float(np.std(y[train & valid])) if np.any(train & valid) else 0.
        reason = 'eligible'
        if fraction < .95: reason = 'training_valid_fraction_below_0.95'
        elif len(days) < 168: reason = 'fewer_than_168_complete_training_days'
        elif mean <= 0 or variation <= 1e-8: reason = 'degenerate_training_meter'
        record = dict(building=name, site=site, timezone=timezone, training_valid_fraction=fraction,
                      complete_training_days=len(days), training_scale=mean, reason=reason,
                      training_missing=int(np.sum(~np.isfinite(y[train]))),
                      training_negative=int(np.sum(y[train] < 0)),
                      training_zero=int(np.sum(y[train] == 0)))
        all_rows.append(record)
        if reason == 'eligible':
            candidates.setdefault(site, []).append(name)
    selected = []
    for level in range(16):
        for site in sorted(candidates):
            if level < len(candidates[site]) and len(selected) < 16:
                selected.append(candidates[site][level])
    if len(selected) < 16 or len({metadata.loc[x, 'site_id'] for x in selected}) < 4:
        raise RuntimeError('Pilot cohort gate failed')
    for record in all_rows:
        record['selected'] = record['building'] in selected
    pd.DataFrame(all_rows).to_csv(output / 'building_eligibility.csv', index=False)
    selection = []
    for name in selected:
        row = next(r.copy() for r in all_rows if r['building'] == name)
        y = frame[name].to_numpy(dtype=float)
        causal = causal_target_mask(frame.index, row['timezone'])
        valid = np.isfinite(y) & (y >= 0)
        mask = train & causal & valid
        _, condition = qr_operator(features[mask])
        row['design_condition'] = condition
        row['training_cleaned_mask_removed'] = int(np.sum(mask & cleaned[name].isna().to_numpy()))
        row['validation_observed'] = int(np.sum(~train & causal & valid))
        row['excluded_clock_intervals_pretest'] = int((~causal).sum())
        selection.append(row)
    summary = dict(electricity_meters=len(frame.columns), pretest_rows=len(frame),
        training_hours=int(train.sum()), validation_hours=int((~train).sum()),
        first_interval=str(frame.index.min()), last_interval=str(frame.index.max()),
        duplicate_timestamps=int(frame.index.duplicated().sum()),
        nonhourly_steps=int(np.sum(np.diff(frame.index.to_numpy(dtype='datetime64[ns]').view('i8')) != pd.Timedelta(hours=1).value)),
        training_valid_readings=int(np.sum(np.isfinite(frame.to_numpy()[train]))),
        training_meter_hour_positions=int(train.sum()*len(frame.columns)),
        eligible_buildings=sum(r['reason']=='eligible' for r in all_rows),
        eligible_sites=len(candidates), selected_buildings=selected,
        selected_sites=sorted({metadata.loc[x,'site_id'] for x in selected}),
        selection=selection, metadata_columns=list(metadata.columns), features=names,
        test_values_opened=False, scope='January-October 2016 only; archive bytes include sealed 2017',
        time_policy='Local labeled intervals; ambiguous/nonexistent hours and predecessors excluded',
        source_units='kWh, documented raw harmonized release')
    (output / 'data_audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['selection','metadata_columns','features']}, indent=2))
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--cache', default='data'); p.add_argument('--out', default='manifests')
    args = p.parse_args()
    audit(args.cache, args.out)
