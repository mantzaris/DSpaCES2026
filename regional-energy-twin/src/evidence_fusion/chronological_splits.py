"""Local labeled intervals; no invented UTC timestamp precision."""
import numpy as np
import pandas as pd


def split_mask(times, start, end):
    return (times >= pd.Timestamp(start)) & (times < pd.Timestamp(end))


def causal_target_mask(times, timezone):
    times = pd.DatetimeIndex(times)
    # Neither choose one side of a repeated clock hour nor shift a nonexistent one.
    localized = times.tz_localize(timezone, ambiguous='NaT', nonexistent='NaT')
    valid = ~localized.isna()
    predecessor = times - pd.Timedelta(hours=1)
    previous_localized = predecessor.tz_localize(timezone, ambiguous='NaT', nonexistent='NaT')
    valid &= ~previous_localized.isna()
    valid &= ~times.duplicated(keep=False)
    # Check actual labeled-row adjacency as well as calendar arithmetic.
    ns = times.to_numpy(dtype='datetime64[ns]').view('i8')
    contiguous = np.r_[False, np.diff(ns) == pd.Timedelta(hours=1).value]
    return np.asarray(valid & contiguous)


def pilot_roles(times):
    masks = {name: np.asarray(split_mask(times, start, end)) for name, start, end in [
        ('covariance', '2016-10-01', '2016-10-11'),
        ('calibration', '2016-10-11', '2016-10-21'),
        ('score', '2016-10-21', '2016-11-01')]}
    assert not any(np.any(masks[a] & masks[b]) for a, b in [('covariance','calibration'), ('covariance','score'), ('calibration','score')])
    return masks


def sealed_read(path):
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError('Noncanonical local interval grid')
    if len(frame) and frame.index.max() >= pd.Timestamp('2016-11-01'):
        raise ValueError('Stage 1 reader refuses calibration/main-test outcomes')
    return frame
