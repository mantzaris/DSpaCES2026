"""Training/development-only access. Held-out paths are never accepted here."""
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb


def load_panel(split, meters=None):
    if split not in ('train', 'development'):
        raise ValueError('Held-out London outcomes are sealed')
    parts = sorted((Path('data/regional/parquet')/split).glob('*/*.parquet'))
    if not parts:
        raise FileNotFoundError('No accessible Parquet partitions for '+split)
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'; SET threads=4")
    files = str(Path('data/regional/parquet')/split/'*/*.parquet')
    # Whole local transition days excluded because the source does not resolve DST.
    query = """SELECT meter, tariff, timestamp, kwh FROM read_parquet(?)
        WHERE duplicate_count=1 AND kwh IS NOT NULL AND timestamp IS NOT NULL
        AND second(timestamp)=0 AND minute(timestamp) IN (0,30)
        AND NOT (month(timestamp) IN (3,10) AND dayofweek(timestamp)=0
                 AND day(timestamp)>=25)"""
    if meters is None:
        meters = [r[0] for r in con.execute('SELECT DISTINCT meter FROM read_parquet(?) ORDER BY meter',[files]).fetchall()]
    start,end = ('2012-01-01','2013-01-01') if split=='train' else ('2013-01-01','2013-04-01')
    times = pd.date_range(start,end,freq='30min')[:-1]
    values = np.full((len(times),len(meters)),np.nan,dtype=np.float32)
    tariffs = {}
    for part in parts:
        frame = con.execute(query,[str(part)]).fetchdf()
        index = pd.Index(meters).get_indexer(frame.meter)
        tindex = times.get_indexer(frame.timestamp)
        ok = (index>=0)&(tindex>=0)
        values[tindex[ok],index[ok]] = frame.kwh.values[ok]
        tariffs.update(frame.drop_duplicates('meter').set_index('meter').tariff.to_dict())
        del frame
    con.close()
    tariff = [tariffs.get(m,'unknown') for m in meters]
    return values, times, np.asarray(meters), tariff


def slots(times):
    return np.asarray(times.dayofweek*48+times.hour*2+times.minute//30)


def masked_provider_statistics(y, mask, loadings, variance, groups, weights):
    """Only available observations are indexed. Hidden values cannot enter b."""
    length,n = y.shape
    dimension = loadings.shape[1]
    cs = np.zeros((len(weights),length,dimension,dimension))
    bs = np.zeros((len(weights),length,dimension))
    for g in range(len(weights)):
        # A zero-confidence provider supplies neither values nor matrices.
        if weights[g] == 0:
            continue
        selected = np.flatnonzero(groups == g)
        h = loadings[selected]
        for t in range(length):
            valid = mask[t,selected]
            hv = h[valid]
            inv = 1/variance[selected[valid]]
            cs[g,t] = (hv.T*inv)@hv
            bs[g,t] = hv.T@(y[t,selected[valid]]*inv)
    return cs,bs
