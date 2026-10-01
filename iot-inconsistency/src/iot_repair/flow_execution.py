"""Frozen common-population experiment execution and compact evidence records."""
import datetime
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch
from scipy.special import logsumexp

from .flow_data import configuration,build_cases,graph_for,public_case,sha256
from .flow_training import load_flow
from .flow_inference import infer_case,FLOOR
from .flow_gaussian import load_ppca,infer_ppca
from .flow_baselines import pca_model,pca_repair,supervised_features,classifier_probability
from .flow_ganf import load_ganf,infer_ganf
from .experiment import json_save
from .associations import edge_residuals


def development_selection(root,dataset):
    directory=Path(root)/'results/graph_flow_v1/development'
    return {key:json.loads((directory/(dataset+'_'+key+'.json')).read_text()) for key in ('models','members','scoring','ganf','baselines')}


def freeze(root):
    root=Path(root);directory=root/'results/graph_flow_v1';path=directory/'protocol_lock.json'
    if path.exists():return validate_lock(root)
    config=configuration(root)
    choices={dataset:development_selection(root,dataset) for dataset in config['datasets']}
    legacy_files=[]
    for dataset in config['datasets']:
        legacy_files.extend(root/'results/study'/dataset/name for name in ('frozen.json','residual_scales.json'))
        for kind in ('diffusion','gdn','diffad'):
            for seed in (1101,2202,3303):legacy_files.append(root/'results/models'/dataset/(kind+'_'+str(seed)+'.pt'))
    source=[*sorted((root/'src/iot_repair').glob('flow_*.py')),root/'src/iot_repair/graph_flow_model.py']
    record=dict(namespace=config['namespace'],created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
       configuration=config,configuration_sha256=sha256(root/'configs/graph_flow_v1.json'),
       data_manifest_sha256=sha256(directory/'data_manifest.json'),choices=choices,
       source_sha256={str(p.relative_to(root)):sha256(p) for p in source},
       legacy_artifact_sha256={str(p.relative_to(root)):sha256(p) for p in legacy_files},
       primary_result='One uniform density-mixture ensemble of three trained members; synthetic configurations averaged within their family',
       final_test_scoring_started_at_lock=False,real_exposure=config['real_test_independence'],
       case_selection_rule='For each dataset retain initial clean and injected cases, then lowest-ID correct, incorrect, and numerically inadequate final top-one cases; no visual attractiveness selection')
    json_save(path,record);return record


def validate_lock(root):
    root=Path(root);directory=root/'results/graph_flow_v1';record=json.loads((directory/'protocol_lock.json').read_text())
    assert sha256(root/'configs/graph_flow_v1.json')==record['configuration_sha256']
    assert sha256(directory/'data_manifest.json')==record['data_manifest_sha256']
    for path,digest in record['source_sha256'].items():
        if sha256(root/path)!=digest:raise ValueError('Frozen numerical code changed: '+path)
    return record


def load_suite(root,dataset,selection):
    spec=selection['models']['selected']['specification'];baseline=selection['baselines']
    assert sha256(Path(root)/baseline['supervised']['path'])==baseline['supervised']['sha256']
    assert sha256(Path(root)/'results/models'/dataset/(baseline['pca']['name']+'.npz'))==baseline['pca']['sha256']
    suite=dict(flow=[load_flow(root,r) for r in selection['members']['members']],
               own=[load_flow(root,r) for r in selection['members']['own_history']],
               ganf=[load_ganf(root,r) for r in selection['ganf']['members']],
               pca=pca_model(root,dataset,baseline['pca']['name']),
               gaussian={key:load_ppca(root,baseline[key]) for key in ('ppca','mixture_ppca','all_ppca')},
               classifier=dict(np.load(Path(root)/baseline['supervised']['path'],allow_pickle=False)),
               selection=selection,length=spec['context_length'],graph=graph_for(root,dataset))
    return suite


def score_case(suite,case,seed,primary_samples=None,full_evidence=False,own_history=True):
    settings=suite['selection']['scoring'];values=case['values'];reference=case['reference'];truth=case['truth']
    count=primary_samples or settings['sample_count'];scale=settings['scale'];length=suite['length'];graph=suite['graph']
    flow=infer_case(suite['flow'],values,graph,length,count,scale,seed=seed,reference=reference,sensitivity=False,times=case['target_times'])
    eligible=flow['eligible'];query=np.flatnonzero(eligible)
    arrays=dict(truth=truth,eligible=eligible,ess=flow['ess'],numerical_adequate=flow['numerical_adequate'],
                flow_mean=flow.get('repairs',{}).get('mean',np.full((len(values),8),np.nan)),
                flow_lower=flow.get('repairs',{}).get('lower',np.full((len(values),8),np.nan)),
                flow_upper=flow.get('repairs',{}).get('upper',np.full((len(values),8),np.nan)))
    arrays.update({'score_'+key:value for key,value in flow['scores'].items()})
    arrays.update({'flow_'+key:value for key,value in flow.get('repair_metrics',{}).items()})
    for key in ('query','log_normal_members','log_fault_components','log_normal','log_fault','score','posterior_mean'):
        if key in flow['raw']:arrays['audit_'+key]=flow['raw'][key]
    timing=dict(flow=flow['seconds'])
    arrays['association_direct_residual']=edge_residuals(values[None],graph)[0]
    if own_history:
        own=infer_case(suite['own'],values,graph,length,count,scale,seed=seed,context_mode='own_history',times=case['target_times'])
        arrays['score_own_history']=own['scores']['flow_ratio'];timing['own_history']=own['seconds']
    for key,models in suite['gaussian'].items():
        spec=suite['selection']['baselines'][key]['specification']
        result=infer_ppca(models,values,graph,length,scale,mode=spec['mode'],seed=seed,reference=reference,times=case['target_times'])
        arrays['score_'+key]=result['score'];arrays[key+'_nll']=result['nll']
        for name in ('mean','prior_mean','lower','upper','metrics'):arrays[key+'_'+name]=result[name]
        timing[key]=result['seconds']
    start=time.perf_counter();scores=suite['pca'].score(values[None])[0];scores[~eligible]=FLOOR
    arrays['score_pca']=scores;arrays['pca_mean']=pca_repair(suite['pca'],values)
    arrays['pca_full_residual_norm']=suite['pca'].total_reconstruction_score(values[None])[0]
    timing['pca']=time.perf_counter()-start
    start=time.perf_counter();arrays['score_supervised']=classifier_probability(suite['classifier'],supervised_features(values[None],suite['pca']))
    arrays['score_supervised'][~eligible]=FLOOR;timing['supervised']=time.perf_counter()-start
    torch.cuda.synchronize();start=time.perf_counter();arrays['score_ganf']=infer_ganf(suite['ganf'],values)
    torch.cuda.synchronize();timing['ganf']=time.perf_counter()-start
    for key,value in arrays.items():
        if key.startswith('score_'):
            if not np.isfinite(value).all():raise FloatingPointError(key+' nonfinite candidate score')
            assert np.all(value[~eligible]==FLOOR),'Comparators have unequal target eligibility'
    evidence=flow['raw'] if full_evidence else None
    if evidence is not None:evidence.update(reference=reference,truth=truth)
    return arrays,evidence,timing


def run_split(root,split,datasets=None):
    root=Path(root);lock=validate_lock(root);directory=root/'results/graph_flow_v1'
    if split=='test' and not (directory/'calibration_complete.json').exists():raise RuntimeError('Separate calibration must finish before final scoring')
    for dataset in datasets or lock['configuration']['datasets']:
        output=directory/dataset/split;output.mkdir(parents=True,exist_ok=True)
        cases=build_cases(root,dataset,split);selection=lock['choices'][dataset];suite=load_suite(root,dataset,selection)
        manifest=dict(dataset=dataset,split=split,protocol_lock_sha256=sha256(directory/'protocol_lock.json'),cases=[public_case(case) for case in cases])
        if (output/'manifest.json').exists():assert json.loads((output/'manifest.json').read_text())==json.loads(json.dumps(manifest,default=lambda x:x.tolist()))
        else:json_save(output/'manifest.json',manifest)
        for ordinal,case in enumerate(cases):
            path=output/(case['id']+'.npz');record_path=path.with_suffix('.json')
            if record_path.exists():
                record=json.loads(record_path.read_text());assert sha256(path)==record['sha256'];continue
            seed=41000000+lock['configuration']['datasets'].index(dataset)*100000+ordinal*101+(0 if split=='calibration' else 1000000)
            keep=ordinal<3
            arrays,evidence,timing=score_case(suite,case,seed,full_evidence=keep)
            np.savez_compressed(path,**arrays)
            record=dict(id=case['id'],seed=seed,path=str(path.relative_to(root)),sha256=sha256(path),timing_seconds=timing,
                        complete_target_fraction=float(arrays['eligible'].mean()),flow_peak_gpu_bytes=torch.cuda.max_memory_allocated(),
                        protocol_lock_sha256=manifest['protocol_lock_sha256'],input_sha256=hashlib.sha256(case['values'].tobytes()).hexdigest(),
                        corruption_scale=selection['scoring']['scale'],draws_per_member=selection['scoring']['sample_count'],ensemble_members=3)
            if keep:
                full=directory/'evidence'/(dataset+'_'+split+'_'+case['id']+'.npz');full.parent.mkdir(exist_ok=True)
                np.savez_compressed(full,**evidence);record['full_evidence']=dict(path=str(full.relative_to(root)),sha256=sha256(full))
            json_save(record_path,record)
            if ordinal%20==0:print(dataset,split,ordinal,'/',len(cases),'flow seconds',timing['flow'],flush=True)
        json_save(output/'complete.json',dict(dataset=dataset,split=split,cases=len(cases),manifest_sha256=sha256(output/'manifest.json'),
                   torch_version=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),
                   finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        del suite;torch.cuda.empty_cache()
    return True
