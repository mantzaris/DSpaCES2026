"""Original-source acquisition, causal preprocessing, masks and split lineage."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import requests

from .graphs import proximity_graph
from .utils import digest, write_json

SOURCE_REVISION = '602afd9d767d3aa1c9b3eac51710d6aeee12c227'
SOURCES = {
    'intel_data.txt.gz': 'https://db.csail.mit.edu/labdata/data.txt.gz',
    'intel_mote_locs.txt': 'https://db.csail.mit.edu/labdata/mote_locs.txt',
    'pems-bay.h5': 'https://drive.usercontent.google.com/download?id=1wD-mHlqAb2mtHOe_68fZvDh1LpDegMMq&export=download&confirm=t',
    'graph_sensor_locations_bay.csv': f'https://raw.githubusercontent.com/liyaguang/DCRNN/{SOURCE_REVISION}/data/sensor_graph/graph_sensor_locations_bay.csv',
    'distances_bay_2017.csv': f'https://raw.githubusercontent.com/liyaguang/DCRNN/{SOURCE_REVISION}/data/sensor_graph/distances_bay_2017.csv',
}


@dataclass
class SensorData:
    name: str
    values: np.ndarray  # time, node, channel; NaNs are retained
    timestamps: np.ndarray  # Unix nanoseconds, timezone unspecified for source naive dates
    coordinates: np.ndarray
    adjacency: np.ndarray
    node_ids: np.ndarray
    center: np.ndarray
    scale: np.ndarray
    bounds: np.ndarray  # 5 chronological split boundaries
    episode_bounds: np.ndarray  # each row: start, stop, split index
    channels: list[str]
    units: list[str]
    interval_seconds: int

    @property
    def standardized(self) -> np.ndarray:
        return ((self.values - self.center) / self.scale).astype(np.float32)

    def issuance_indices(self, split: int, context: int, horizon: int,
                         stride: int) -> np.ndarray:
        indices = []
        for start, stop, partition in self.episode_bounds:
            if partition == split:
                indices.extend(range(int(start)+context, int(stop)-horizon+1, stride))
        return np.asarray(indices, dtype=np.int64)  # first target index


def acquire(root: Path) -> dict:
    raw = root / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in SOURCES.items():
        path = raw / name
        if not path.exists():
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            if name.endswith('.h5') and not response.content.startswith(b'\x89HDF'):
                raise RuntimeError('Original Google Drive did not return HDF5; no data substitution')
            path.write_bytes(response.content)
        manifest[name] = {'url': url, 'bytes': path.stat().st_size, 'sha256': digest(path)}
    write_json(root / 'data/manifests/raw_sources.json', manifest)
    return manifest


def scaling(values: np.ndarray, training_end: int) -> tuple[np.ndarray, np.ndarray]:
    training = values[:training_end]
    center = np.nanmedian(training, axis=0)
    lo, hi = np.nanquantile(training, [.25,.75], axis=0)
    scale = (hi-lo)/1.349
    fallback = np.nanstd(training, axis=0)
    scale = np.where(scale > 1e-5, scale, fallback)
    return np.nan_to_num(center).astype(np.float32), np.maximum(np.nan_to_num(scale,nan=1),1e-4).astype(np.float32)


def save_data(root: Path, name: str, values: np.ndarray, timestamps: np.ndarray,
              coordinates: np.ndarray, adjacency: np.ndarray, node_ids: np.ndarray,
              channels: list[str], units: list[str], interval_seconds: int,
              audit: dict, bounds: np.ndarray | None = None,
              episodes: np.ndarray | None = None, observation_times: np.ndarray | None = None) -> SensorData:
    if bounds is None:
        bounds = np.array([0, int(.6*len(values)), int(.75*len(values)), int(.85*len(values)),len(values)])
    if episodes is None:
        episodes = np.array([[bounds[k],bounds[k+1],k] for k in range(4)])
    center, scale = scaling(values, int(bounds[1]))
    directory = root / 'data/processed'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{name}.npz'
    payload = dict(values=values.astype(np.float32),timestamps=timestamps,coordinates=coordinates,
                   adjacency=adjacency.astype(np.float32),node_ids=node_ids,center=center,scale=scale,
                   bounds=bounds,episode_bounds=episodes,channels=channels,units=units,
                   interval_seconds=interval_seconds)
    if observation_times is not None:
        payload['observation_times'] = observation_times
    np.savez_compressed(path, **payload)
    splits=[]
    for k,label in enumerate(['train','development','calibration','test']):
        x=values[bounds[k]:bounds[k+1]]
        splits.append({'name':label,'start':int(bounds[k]),'stop':int(bounds[k+1]),
                       'first_timestamp':str(pd.Timestamp(timestamps[bounds[k]])),
                       'last_timestamp':str(pd.Timestamp(timestamps[bounds[k+1]-1])),
                       'observed_fraction_by_channel':np.isfinite(x).mean((0,1)),
                       'observed_fraction_by_sensor_channel':np.isfinite(x).mean(0)})
    scaled=(values[:bounds[1]]-center)/scale
    audit.update({'name':name,'shape':list(values.shape),'channels':channels,'units':units,
                  'interval_seconds':interval_seconds,'timezone':'unspecified by source',
                  'nodes':node_ids,'splits':splits,'episodes':episodes,
                  'training_extreme_fraction':np.sum(np.abs(scaled)>8)/max(np.isfinite(scaled).sum(),1),
                  'processed_sha256':digest(path)})
    write_json(root/'data/manifests'/f'{name}.json', audit)
    return load_data(root,name)


def load_data(root: Path, name: str, primary_only: bool = True) -> SensorData:
    with np.load(root/'data/processed'/f'{name}.npz', allow_pickle=False) as archive:
        payload = {k:archive[k] for k in SensorData.__dataclass_fields__ if k != 'name'}
    payload['channels'] = payload['channels'].tolist()
    payload['units'] = payload['units'].tolist()
    payload['interval_seconds'] = int(payload['interval_seconds'])
    if name == 'intel' and primary_only:
        for key in ['values','center','scale']:
            payload[key] = payload[key][..., :2]
        payload['channels'],payload['units']=payload['channels'][:2],payload['units'][:2]
    return SensorData(name=name,**payload)


def prepare_intel(root: Path) -> SensorData:
    raw=root/'data/raw'
    names=['date','time','epoch','node','temperature','humidity','light','voltage']
    frame=pd.read_csv(raw/'intel_data.txt.gz',sep=r'\s+',names=names)
    raw_rows=len(frame)
    frame['timestamp']=pd.to_datetime(frame.date+' '+frame.time,errors='coerce')
    frame=frame[frame.node.between(1,54)&frame.timestamp.notna()].copy()
    frame['node']=frame.node.astype(int)
    # Stable chronological order; values are available at the right bin boundary.
    frame=frame.sort_values('timestamp',kind='stable')
    invalid_humidity=(frame.humidity<0)|(frame.humidity>100)
    frame.loc[invalid_humidity,'humidity']=np.nan
    frame['bin']=frame.timestamp.dt.ceil('2min')
    last=frame.groupby(['bin','node'],sort=True).tail(1).set_index(['bin','node'])
    coords=pd.read_csv(raw/'intel_mote_locs.txt',sep=r'\s+',header=None,index_col=0)
    nodes=coords.index.to_numpy()
    grid=pd.date_range(last.index.get_level_values('bin').min(),last.index.get_level_values('bin').max(),freq='2min')
    channels=names[4:]
    values=np.stack([last[c].unstack('node').reindex(index=grid,columns=nodes).to_numpy() for c in channels],-1)
    observed_times=last.timestamp.unstack('node').reindex(index=grid,columns=nodes).to_numpy(dtype='datetime64[ns]').view('int64')
    audit={'source':'https://db.csail.mit.edu/labdata/labdata.html','raw_rows':raw_rows,
           'retained_raw_rows':len(frame),'invalid_humidity_rows':int(invalid_humidity.sum()),
           'raw_first_timestamp':str(frame.timestamp.min()),'raw_last_timestamp':str(frame.timestamp.max()),
           'aggregation':'Last whole observed row per sensor in right-closed 2-minute bin; no filling',
           'graph':'Symmetric 8-nearest Euclidean coordinate proximity, metres',
           'upstream_imputation':'Raw source reports missing/truncated streams; no imputation described',
           'raw_file_sha256':digest(raw/'intel_data.txt.gz')}
    return save_data(root,'intel',values,grid.to_numpy().view('int64'),coords.to_numpy(),
                     proximity_graph(coords.to_numpy()),nodes,channels,['degC','percent RH','lux','V'],120,
                     audit,observation_times=observed_times)


def prepare_pems(root: Path) -> SensorData:
    raw=root/'data/raw'
    with h5py.File(raw/'pems-bay.h5','r') as archive:
        group=archive['speed']
        values=group['block0_values'][:]
        nodes=group['axis0'][:]
        timestamps=group['axis1'][:]
    zero_count=int((values==0).sum())
    raw_nans=int(np.isnan(values).sum())
    differences=np.diff(timestamps)//10**9
    gaps=[{'after':str(pd.Timestamp(timestamps[i])), 'seconds':int(differences[i])}
          for i in np.where(differences!=300)[0]]
    values[values==0]=np.nan
    frame=pd.DataFrame(values,index=pd.to_datetime(timestamps),columns=nodes)
    grid=pd.date_range(frame.index.min(),frame.index.max(),freq='5min')
    values=frame.reindex(grid).to_numpy()[...,None]
    locations=pd.read_csv(raw/'graph_sensor_locations_bay.csv',header=None,names=['id','lat','lon']).set_index('id').loc[nodes]
    # Metric-like planar projection solely for plots/ties; graph uses road distance.
    coordinates=np.column_stack([locations.lon.to_numpy()*np.cos(np.deg2rad(locations.lat.mean())),locations.lat.to_numpy()])
    roads=pd.read_csv(raw/'distances_bay_2017.csv',header=None,names=['from','to','distance'])
    index={int(node):i for i,node in enumerate(nodes)}
    roads=roads[roads['from'].isin(index)&roads['to'].isin(index)]
    scale=float(roads.distance.std(ddof=0))
    adjacency=np.zeros((len(nodes),len(nodes)),np.float32)
    for row in roads.itertuples(index=False,name=None):
        source,target,distance=row
        weight=np.exp(-(distance/scale)**2)
        if weight >= .1 and source!=target:
            adjacency[index[source],index[target]]=weight
    audit={'source':'https://github.com/liyaguang/DCRNN','source_revision':SOURCE_REVISION,
           'original_rows':len(timestamps),'zero_values':zero_count,'raw_nan_values':raw_nans,
           'timestamp_gaps':gaps,'inserted_timestamp_rows':len(grid)-len(timestamps),
           'graph':'Directed release road distances, exp(-(d/std)^2), threshold .1; undirected neighborhoods',
           'road_distance_rows':len(roads),'directed_edges':int((adjacency>0).sum()),
           'latitude':locations.lat.to_numpy(),'longitude':locations.lon.to_numpy(),
           'upstream_imputation':'Preprocessed DCRNN release; provenance of per-value upstream imputation unavailable; zeros follow DCRNN missing-value evaluation convention',
           'raw_file_sha256':digest(raw/'pems-bay.h5')}
    return save_data(root,'pems',values,grid.to_numpy().view('int64'),coordinates,adjacency,nodes,
                     ['speed'],['mph'],300,audit)
