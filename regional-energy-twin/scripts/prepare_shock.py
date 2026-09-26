"""Prepare only established development partitions and frozen training model."""
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from evidence_fusion.regional_data import load_panel,slots
from evidence_fusion.refinement_access import immutable_digest


def main():
    cfg=json.loads(Path('configs/regional_shock.json').read_text())
    out=Path('results/shock');out.mkdir(exist_ok=True)
    folder=Path('data/regional/shock');folder.mkdir(exist_ok=True)
    model=dict(np.load('data/regional/refinement/model.npz',allow_pickle=False))
    start=time.perf_counter()
    values,times,meters,_=load_panel('development',model['meters'])
    if len(meters)!=cfg['households']:raise ValueError('Training cohort changed')
    parse=time.perf_counter()-start
    original=json.loads(Path('results/refinement/frozen_manifest.json').read_text())['origins']
    starts=[cfg['calibration_start']]+[original[i] for i in cfg['background_origin_indices']]
    records=[]
    for index,origin in enumerate(starts):
        count=cfg['calibration_steps'] if index==0 else cfg['steps']
        first=int(times.get_loc(origin));lower=first-cfg['window']+1
        upper=first+count+max(cfg['horizons'])
        if lower<0 or times[upper-1]>=pd.Timestamp('2013-04-01'):
            raise ValueError('Sealed or insufficient development support')
        path=folder/('calibration.npz' if index==0 else 'background_%02d.npz'%(index-1))
        np.savez_compressed(path,values=values[lower:upper],slots=slots(times[lower:upper]),
                            timestamps=times[lower:upper].values.astype(str))
        records.append(dict(path=str(path),origin=origin,updates=count,
            rows=int(np.isfinite(values[lower:upper]).sum()),bytes=path.stat().st_size,sha256=immutable_digest(path)))
    metadata=dict(model_sha256=immutable_digest('data/regional/refinement/model.npz'),
        config_sha256=immutable_digest('configs/regional_shock.json'),backgrounds=records,
        development_parse_seconds=parse,total_seconds=time.perf_counter()-start,
        compressed_parquet_bytes=sum(p.stat().st_size for p in Path('data/regional/parquet/development').glob('*/*.parquet')),
        actual_valid_development_readings=int(np.isfinite(values).sum()),
        training_rows_reused=52109356,new_training=False,new_dataset_download_bytes=0,
        london_holdout_opened=False,bdg2_outcomes_opened=False)
    (out/'preparation.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2),flush=True)


if __name__=='__main__':main()
