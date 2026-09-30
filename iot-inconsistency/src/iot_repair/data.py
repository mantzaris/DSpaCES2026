"""Three datasets, immutable measurements and explicitly disjoint split units."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from .preprocessing import fit_training_normalizer, transform_measurements

SPLITS=('train','development','calibration','test')


def simulate(nodes, length, seed, nonlinear=True, heldout=False,event=None,association_change=None):
    rng=np.random.default_rng(seed)
    z=np.zeros((length+128,4)); regime=np.zeros(len(z),dtype=int)
    regime[len(z)//2:]=2 if heldout else 1
    a=.83*np.eye(4)+.025*np.roll(np.eye(4),1,axis=1)
    spectral_radius=float(np.max(np.abs(np.linalg.eigvals(a))))
    for t in range(1,len(z)):
        u=np.sin(t/np.array([27.,41.,67.,103.])+seed%31)
        u+=.2*regime[t]
        if event is not None and event['start']<=t-128<event['stop']:
            u[event.get('latent',0)]+=event['magnitude']
        z[t]=a@z[t-1]+.08*u+.035*np.tanh(np.roll(z[t-1],1))+rng.normal(0,.025,4)
    z=z[128:]; regime=regime[128:]
    x=np.zeros((length,nodes)); units=[]
    offsets=np.array([20.,100.,2.5,500.]); scales=np.array([5.,20.,.15,100.])
    correlated=rng.normal(0,.012,(length,4))
    for i in range(nodes):
        j=i%4; lag=i%3
        value=z[np.maximum(np.arange(length)-lag,0),j]+.1*z[:,(j+1)%4]
        if nonlinear:
            value+=.6*np.sin(2*z[:,j]+.2*(i//4)%3)+.15*regime*z[:,(j+2)%4]**2
        if association_change is not None and i==association_change['channel']:
            alternate=association_change['new_latent'];start=association_change['start']
            changed=z[np.maximum(np.arange(length)-lag,0),alternate]+.1*z[:,(alternate+1)%4]
            if nonlinear:changed+=.6*np.sin(2*z[:,alternate]+.2*(i//4)%3)+.15*regime*z[:,(alternate+2)%4]**2
            value[start:]=changed[start:]
        response_sign=1 if (i//4)%2==0 else -1
        x[:,i]=offsets[j]+scales[j]*(response_sign*(value+correlated[:,j])+rng.normal(0,.015,length))
        units.append(['degC','kPa','V','lux'][j])
    assert np.isfinite(x).all() and np.max(np.abs(z))<10
    return x,z,regime,units,{'linear_spectral_radius':spectral_radius,
        'nonlinear_lipschitz_upper_bound':.035,'max_abs_latent':float(np.max(np.abs(z))),
        'sample_seconds':1.,'seed':seed,'generator_version':'signed-responses-v2'}


def _windows(x,timestamps,unit,labels=None,h=64,stride=32):
    result=[]
    for stop in range(h,len(x)+1,stride):
        a=x[stop-h:stop].T
        if np.isfinite(a).mean()<.4: continue
        result.append({'x':a,'timestamp':int(timestamps[stop-1]),'block':unit,
                       'start':stop-h,'stop':stop,
                       'process_label':bool(np.any(labels[stop-8:stop])) if labels is not None else False,
                       'reference':not bool(np.any(labels[stop-h:stop])) if labels is not None else True})
    return result


def synthetic_records(root,nodes,nonlinear):
    records={}; all_train=[]; manifest=[]
    for s,split in enumerate(SPLITS):
        rows=[]
        for trajectory in range(12 if split=='train' else 8):
            seed=10000+nodes*100+s*1000+trajectory
            x,z,r,units,meta=simulate(nodes,1024,seed,nonlinear,heldout=(split=='test' and trajectory>=6))
            identity=f'{split}_trajectory_{trajectory}'
            meta.update(split=split,trajectory=identity,heldout_regime=(split=='test' and trajectory>=6))
            rows+=_windows(x,np.arange(len(x)),identity)
            manifest.append(meta)
            truth_directory=root/'data/processed'/f'synthetic_{nodes}_{"nonlinear" if nonlinear else "linear"}'/'latent_truth'
            truth_directory.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(truth_directory/(identity+'.npz'),measurements=x,latent=z,regime=r,
                                timestamps=np.arange(len(x)),observation_fault=np.zeros_like(x,dtype=bool))
            if split=='train': all_train.append(x)
        records[split]=rows
    return records,np.concatenate(all_train),[f'sensor_{i:02d}' for i in range(nodes)],units,manifest


def intel_records(root,mote_count=12):
    raw=root/'data/raw/intel/data.txt.gz'
    names=['date','time','epoch','mote','temperature','humidity','light','voltage']
    df=pd.read_csv(raw,sep=r'\s+',header=None,names=names)
    df['timestamp']=pd.to_datetime(df['date']+' '+df['time'],errors='coerce')
    df=df.loc[df.mote.between(1,54)&df.timestamp.between('2004-02-28','2004-03-28')].copy()
    df['mote']=df.mote.astype(int)
    fields=names[4:]
    duplicates=int(df.duplicated(['mote','timestamp']).sum())
    # Conflicting duplicate source records are unavailable, not averaged.
    df=df.loc[~df.duplicated(['mote','timestamp'],keep=False)]
    df['bin']=df.timestamp.dt.floor('5min')
    # Aggregation uses only already observed records inside a completed bin.
    wide=df.groupby(['bin','mote'])[fields].median().unstack('mote')
    grid=pd.date_range('2004-02-28','2004-03-28',freq='5min',inclusive='left') if int(pd.__version__.split('.')[0])>=2 else pd.date_range('2004-02-28','2004-03-28',freq='5min',closed='left')
    wide=wide.reindex(grid)
    bounds=[0,int(len(grid)*.45),int(len(grid)*.65),int(len(grid)*.82),len(grid)]
    coverage=wide.iloc[:bounds[1]].notna().groupby(level=1,axis=1).mean().mean()
    selected=sorted(coverage.sort_values(ascending=False,kind='mergesort').head(mote_count).index.tolist())
    cols=[(field,mote) for mote in selected for field in fields]
    x=wide.reindex(columns=pd.MultiIndex.from_tuples(cols)).to_numpy(dtype=float)
    groups=[f'mote_{mote:02d}' for field,mote in cols]
    units=[{'temperature':'degC','humidity':'percent_RH','light':'lux','voltage':'V'}[field] for field,mote in cols]
    records={}; manifest=[]
    for s,split in enumerate(SPLITS):
        lo=bounds[s]+(64 if s else 0); hi=bounds[s+1]
        timestamps=grid[lo:hi].astype('int64').to_numpy()//10**9+300
        records[split]=_windows(x[lo:hi],timestamps,'intel_'+split,stride=32)
        # Temporal bootstrap blocks are days, never individual overlapping windows.
        for record in records[split]: record['block']=str(record['timestamp']//86400)
        manifest.append(dict(split=split,start=str(grid[lo]),end=str(grid[hi-1]),
            rows=hi-lo,missing_fraction=float(np.isnan(x[lo:hi]).mean())))
    archive=root/'data/processed/intel_source_records.npz'; archive.parent.mkdir(parents=True,exist_ok=True)
    # Preserve original irregular timestamps and all channels, in addition to raw archive.
    np.savez_compressed(archive,timestamps=df.timestamp.astype('int64').to_numpy(),
        mote=df.mote.to_numpy(),epoch=df.epoch.to_numpy(),values=df[fields].to_numpy())
    manifest.append(dict(selected_motes=selected,channel_names=[f'{m}:{f}' for f,m in cols],
        resample_seconds=300,decision_time='right boundary of completed five-minute bin',interpolation='none',gap_bins=64,duplicate_records_excluded=duplicates,
        selection='highest training availability, all four channels of each chosen mote',
        label_scope='controlled corruption of unadjudicated measured reference',
        source_record_archive=str(archive.relative_to(root))))
    return records,x[:bounds[1]],groups,units,manifest


def skab_records(root):
    directory=root/'data/raw/SKAB/data'
    files=sorted(directory.glob('*/*.csv'))
    normal=[p for p in files if 'anomaly-free' in str(p)]
    experiments=[p for p in files if p not in normal]
    rng=np.random.default_rng(9026)
    order=np.array(experiments,dtype=object)[rng.permutation(len(experiments))]
    # Entire experiments are assigned, including their normal segments.
    assigned={'train':normal+list(order[:6]),'development':list(order[6:14]),
              'calibration':list(order[14:24]),'test':list(order[24:])}
    records={}; train=[]; manifest=[]
    for split in SPLITS:
        rows=[]
        for path in assigned[split]:
            df=pd.read_csv(path,sep=';')
            features=[c for c in df.columns if c not in ('datetime','anomaly','changepoint')]
            values=df[features].to_numpy(dtype=float)
            labels=df['anomaly'].to_numpy() if 'anomaly' in df else np.zeros(len(df))
            timestamps=pd.to_datetime(df.datetime).astype('int64').to_numpy()//10**9
            identity=str(path.relative_to(directory))
            win=_windows(values,timestamps,identity,labels)
            rows+=win
            if split=='train': train.append(values[labels==0])
            manifest.append(dict(split=split,experiment=identity,rows=len(df),
                native_process_anomaly_rows=int(labels.sum()),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        records[split]=rows
    units=['g','g','A','bar','degC','degC','V','L/min']
    manifest.append(dict(actual_csv_count=len(files),labeled_experiment_count=len(experiments),
                         label_scope='native process anomalies, not sensor fault truth',channels=features))
    return records,np.concatenate(train),features,units,manifest


def prepare_dataset(root,name,max_windows=None):
    if name.startswith('synthetic'):
        nodes=int(name.split('_')[1]); nonlinear=name.endswith('nonlinear')
        records,train,groups,units,manifest=synthetic_records(root,nodes,nonlinear)
    elif name=='intel': records,train,groups,units,manifest=intel_records(root)
    elif name=='skab': records,train,groups,units,manifest=skab_records(root)
    else: raise ValueError(name)
    normalizer=fit_training_normalizer(train,units=units)
    if normalizer['excluded']: raise ValueError('Channels without any training observations need exclusion.')
    output=root/'data/processed'/name; output.mkdir(parents=True,exist_ok=True)
    for split,rows in records.items():
        if split=='train': rows=[r for r in rows if r['reference']]
        if max_windows and len(rows)>max_windows.get(split,len(rows)):
            indices=np.linspace(0,len(rows)-1,max_windows[split],dtype=int)
            rows=[rows[i] for i in indices]
        x=np.stack([transform_measurements(r['x'].T,normalizer).T for r in rows]).astype('float32')
        observed=np.isfinite(x)
        age=np.where(observed,0,-1).astype(np.int32)
        for t in range(1,x.shape[-1]): age[...,t]=np.where(observed[...,t],0,np.where(age[...,t-1]>=0,age[...,t-1]+1,-1))
        np.savez_compressed(output/(split+'.npz'),x=x,observed=observed,age=age,
            timestamp=np.array([r['timestamp'] for r in rows]),block=np.array([r['block'] for r in rows]),
            process_label=np.array([r['process_label'] for r in rows]),reference=np.array([r['reference'] for r in rows]),
            start=np.array([r['start'] for r in rows]),stop=np.array([r['stop'] for r in rows]))
    finite=transform_measurements(train,normalizer)
    contamination=float(np.nanmean(np.abs(finite)>8))
    metadata=dict(name=name,groups=groups,units=units,normalizer=normalizer,sources=manifest,
        reference_contamination_proxy={'training_abs_robust_z_over_8':contamination,
            'meaning':'tail frequency proxy, not an authoritative fault label'},
        window=64,stride=32,interpolation='none')
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    files={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*.npz')}
    (root/'data/manifests'/(name+'.json')).write_text(json.dumps(dict(metadata=metadata,files=files),indent=2)+'\n')
    return output
