"""Versioned data access, exhaustive candidates and fixed fault manifests."""
import hashlib
import json
from pathlib import Path

import numpy as np

from .data import simulate, _windows
from .preprocessing import transform_measurements
from .experiment import json_save


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def configuration(root):
    return json.loads((Path(root)/'configs/graph_flow_v1.json').read_text())


def source_path(root, dataset, split):
    root=Path(root)
    if dataset.startswith('synthetic') and split=='test':
        return root/'data/processed/graph_flow_v1'/dataset/'test.npz'
    return root/'data/processed'/dataset/(split+'.npz')


def load_data(root, dataset, split):
    with np.load(source_path(root,dataset,split),allow_pickle=False) as archive:
        return {key:archive[key].copy() for key in archive.files}


def metadata(root,dataset):
    return json.loads((Path(root)/'data/processed'/dataset/'metadata.json').read_text())


def graph_for(root,dataset):
    return json.loads((Path(root)/'results/models'/dataset/'graph.json').read_text())


def prepare(root):
    root=Path(root);config=configuration(root);output=root/'results/graph_flow_v1'
    manifest={}
    for dataset in config['datasets']:
        meta=metadata(root,dataset)
        if dataset.startswith('synthetic'):
            path=source_path(root,dataset,'test');path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():
                nodes=int(dataset.split('_')[1]);rows=[];truth=[]
                for trajectory in range(config['synthetic_trajectories']['test']):
                    seed=config['synthetic_seed_origin']+nodes*1000+trajectory
                    shift=trajectory>=config['synthetic_trajectories']['test']-2
                    measurements,latent,regime,units,info=simulate(nodes,1024,seed,dataset.endswith('nonlinear'),heldout=shift)
                    identity='flow_test_trajectory_'+str(trajectory)
                    rows+=_windows(measurements,np.arange(1024),identity)
                    truth_path=path.parent/(identity+'.npz')
                    np.savez_compressed(truth_path,uncorrupted_noisy_measurement=measurements,latent_process=latent,
                                        regime=regime,timestamps=np.arange(1024))
                    truth.append(dict(block=identity,path=str(truth_path.relative_to(root)),sha256=sha256(truth_path),seed=seed,heldout_regime=shift))
                x=np.stack([transform_measurements(r['x'].T,meta['normalizer']).T for r in rows]).astype('float32')
                np.savez_compressed(path,x=x,observed=np.isfinite(x),timestamp=np.array([r['timestamp'] for r in rows]),
                    block=np.array([r['block'] for r in rows]),start=np.array([r['start'] for r in rows]),stop=np.array([r['stop'] for r in rows]),
                    reference=np.ones(len(rows),bool),process_label=np.zeros(len(rows),bool))
                json_save(path.parent/'truth_manifest.json',truth)
        summary={}
        for split in ('train','development','calibration','test'):
            path=source_path(root,dataset,split);data=load_data(root,dataset,split)
            eligible=np.isfinite(data['x'][...,-config['target_length']:]).all(-1)
            summary[split]=dict(path=str(path.relative_to(root)),sha256=sha256(path),windows=len(data['x']),
                channels=data['x'].shape[1],blocks=sorted(set(data['block'].tolist())),reference_windows=int(data['reference'].sum()),
                candidate_count=int(eligible.size),complete_target_candidates=int(eligible.sum()),
                complete_target_fraction=float(eligible.mean()),prior_exposure=not(dataset.startswith('synthetic') and split=='test'))
        manifest[dataset]=dict(splits=summary,metadata_path='data/processed/'+dataset+'/metadata.json',
            metadata_sha256=sha256(root/'data/processed'/dataset/'metadata.json'),
            graph_path='results/models/'+dataset+'/graph.json',graph_sha256=sha256(root/'results/models'/dataset/'graph.json'),
            units=meta['units'],groups=meta['groups'],normalizer=meta['normalizer'])
    destination=output/'data_manifest.json'
    record=dict(configuration_sha256=sha256(root/'configs/graph_flow_v1.json'),datasets=manifest,
                synthetic_final_independence='Fresh trajectories, seeds and injected faults, same generator family',
                real_final_independence='New injections on previously examined held-out recordings, not new environments')
    if destination.exists():
        assert json.loads(destination.read_text())==record,'Prepared data changed; create a new version instead of mixing runs'
    else:json_save(destination,record)
    return record


def sample_reference_indices(data,count):
    """Round-robin source blocks, with evenly spaced windows within each block."""
    indices=np.flatnonzero(data['reference']);count=min(count,len(indices))
    blocks=sorted(set(data['block'][indices].tolist()))
    by_block={block:indices[data['block'][indices]==block] for block in blocks}
    allocation={block:0 for block in blocks}
    while sum(allocation.values())<count:
        for block in blocks:
            if sum(allocation.values())>=count:break
            if allocation[block]<len(by_block[block]):allocation[block]+=1
    chosen=[]
    for block in blocks:
        if allocation[block]:chosen.extend(by_block[block][np.linspace(0,len(by_block[block])-1,allocation[block],dtype=int)].tolist())
    return sorted(chosen)


def calibration_roles(blocks):
    blocks=sorted(set(blocks))
    if len(blocks)<3:raise ValueError('Three disjoint calibration block roles are required')
    normal=max(1,len(blocks)//2);probability=max(1,(len(blocks)-normal)//2)
    return {block:('normal_window_tail' if i<normal else 'fault_probability' if i<normal+probability else 'repair_policy') for i,block in enumerate(blocks)}


def inject(reference,channel,family,severity,seed,horizon=8):
    """One numeric channel fault. No supporting physical source is edited."""
    rng=np.random.default_rng(seed);values=reference.copy();target=values[channel,-horizon:]
    mask=np.isfinite(target);original=target.copy();sign=float(rng.choice([-1,1]));ramp=np.linspace(-1,1,horizon)
    if family=='bias':replacement=target+sign*severity
    elif family=='drift':replacement=target+sign*severity*ramp
    elif family=='noise':replacement=target+rng.normal(0,severity,horizon)
    elif family=='stuck':
        previous=values[channel,:-horizon];previous=previous[np.isfinite(previous)]
        level=float(previous[-1]) if len(previous) else float(np.nanmean(target)) if mask.any() else 0.
        replacement=np.full(horizon,level+sign*.25*severity)+rng.normal(0,.03,horizon)
    elif family=='spike':
        replacement=target.copy();replacement[int(rng.integers(0,horizon))]+=sign*severity*3
    elif family=='scale':replacement=target*(1+sign*min(.8,severity/5))
    elif family=='replay':replacement=values[channel,-2*horizon:-horizon].copy()
    elif family=='delay':replacement=values[channel,-horizon-3:-3].copy()
    else:raise ValueError(family)
    # A numeric mechanism cannot manufacture a missing observation or a missing
    # replay source. This preserves the original availability mask exactly.
    replacement=np.where(np.isfinite(replacement),replacement,target)
    target[mask]=replacement[mask]
    changed=mask & (target!=original)
    return values,dict(family=family,severity=float(severity),seed=int(seed),target=int(channel),
        edited_observed_cells=int(changed.sum()),attempted_unobservable=bool(not changed.any()),
        label_scope='controlled numeric change relative to unadjudicated recorded reference')


def build_cases(root,dataset,split):
    config=configuration(root);data=load_data(root,dataset,split)
    count=config['base_windows'].get(split,32)
    indices=sample_reference_indices(data,count)
    roles=calibration_roles(data['block'][indices]) if split=='calibration' else {}
    dataset_code=config['datasets'].index(dataset)*100000
    offset=dict(train=1000000,development=2000000,calibration=3000000,test=4000000)[split]+20261001+dataset_code
    result=[]
    for ordinal,index in enumerate(indices):
        reference=data['x'][index];channels=reference.shape[0]
        common=dict(base_id=f'{split}_{index:04d}',source_index=int(index),block=str(data['block'][index]),
            timestamp=int(data['timestamp'][index]),start=int(data['start'][index]),stop=int(data['stop'][index]),
            native_process_label=bool(data['process_label'][index]),split=split,
            calibration_role=roles.get(str(data['block'][index]),'not_calibration'),
            heldout_regime=bool(dataset.startswith('synthetic') and split=='test' and int(str(data['block'][index]).split('_')[-1])>=10),
            reference_sha256=hashlib.sha256(reference.tobytes()).hexdigest())
        result.append(dict(common,id=common['base_id']+'_clean',track='clean',fault=dict(family='unmodified',target=None,edited_observed_cells=0),
                           values=reference.copy(),reference=reference,truth=np.zeros(channels,bool)))
        for copy in range(4):
            rng=np.random.default_rng(offset+index*101+copy*17)
            if split=='test':
                family=(config['faults_development'] if copy<2 else config['faults_heldout'])[(ordinal+2*(copy%2))%4]
                severity=float(rng.uniform(*config['test_severity_range']))
            else:
                family=config['faults_development'][copy];severity=config['development_severities'][(ordinal+copy)%3]
            channel=int(rng.integers(channels))
            values,fault=inject(reference,channel,family,severity,offset+index*101+copy*17)
            truth=np.zeros(channels,bool);truth[channel]=fault['edited_observed_cells']>0
            result.append(dict(common,id=common['base_id']+'_'+family,track='measurement',fault=fault,
                               values=values,reference=reference,truth=truth))
    return result


def public_case(case):
    return {key:value for key,value in case.items() if key not in ('values','reference')}
