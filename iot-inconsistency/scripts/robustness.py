"""Targeted stress experiments, with frozen main-study parameters and labels."""
from pathlib import Path
import argparse,copy,json,sys
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save,scaled
from iot_repair.pipeline import score_candidates,screen_candidates
from iot_repair.faults import inject_observation,inject_association
from iot_repair.associations import edge_residuals
from iot_repair.baselines import gdn_residual,PCADetector
from iot_repair.metrics import candidate_score
from iot_repair.witnesses import select_witnesses
from iot_repair.data import simulate
from iot_repair.preprocessing import transform_measurements
from iot_repair.calibration import null_tail_value
p=argparse.ArgumentParser();p.add_argument('--dataset',default='synthetic_32_nonlinear');a=p.parse_args();torch.set_num_threads(4)
name=a.dataset;out=ROOT/'results/robustness'/name;out.mkdir(parents=True,exist_ok=True)
models,graph=load_models(ROOT,name,('diffusion','gdn'))
params=json.loads((ROOT/'results/study'/name/'frozen.json').read_text());cal=json.loads((ROOT/'results/study'/name/'calibration_complete.json').read_text())
scales=json.loads((ROOT/'results/study'/name/'residual_scales.json').read_text())
pca_name=params['strongest_baseline'];pca=PCADetector.load(ROOT/'results/models'/name/(pca_name+'.npz'),lag=int(pca_name.split('_')[1][3:]))
d=np.load(ROOT/'data/processed'/name/'test.npz');source_indices=np.flatnonzero(d['reference'])
source_indices=source_indices[np.linspace(0,len(source_indices)-1,min(12,len(source_indices)),dtype=int)]
base=d['x'][source_indices];meta=json.loads((ROOT/'data/processed'/name/'metadata.json').read_text())
contaminated=None
if name=='synthetic_32_nonlinear':contaminated,_=load_models(ROOT,name+'_contaminated',('diffusion',))

def evaluate(identity,x,g,truth,details,member_models=None,candidates=None):
    path=out/(identity+'.json')
    if path.exists():
        previous=json.loads(path.read_text())
        if previous.get('stress_protocol_version')=='scaled-screen-stratified-v3' and (details['family']!='single_source_support' or previous.get('low_support_protocol')=='ordinary screening, diagnostic ranking only'):return previous
        version=previous.get('stress_protocol_version','unscaled-v1')+('_single_candidate' if details['family']=='single_source_support' else '')
        archive=out/'prior_stress_protocols'/version;archive.mkdir(parents=True,exist_ok=True)
        path.replace(archive/path.name);path.with_suffix('.npz').replace(archive/path.with_suffix('.npz').name)
    with torch.no_grad():residual=np.mean([gdn_residual(m,torch.as_tensor(x[None],device='cuda')).cpu().numpy()[0] for m in models['gdn']],axis=0)
    residual=scaled(residual,scales['gdn'])
    pca_scores=scaled(pca.score(x[None])[0],scales[pca_name])
    if candidates is None:
        candidates=screen_candidates(residual,edge_residuals(x[None],g)[0],g)
    records,raw,abstentions=score_candidates(member_models or models['diffusion'],x,g,candidates,seed=448899,
        kappa=params['kappa'],edit_weight=params['lambda'])
    for row in records:
        row['primary_target']=bool(truth[row['index']]) if row['kind']=='observation' else None
    observations=[r for r in records if r['kind']=='observation' and r['support_count']>=2];best=max(observations,key=lambda r:r['score']) if observations else None
    single=[r for r in records if r['kind']=='observation' and r['support_count']==1];single_best=max(single,key=lambda r:r['score']) if single else None
    selected=max([r['score'] for r in observations],default=-1e12)
    report=dict(id=identity,dataset=name,details=details,records=records,abstentions=abstentions,candidates=candidates,
        stress_protocol_version='scaled-screen-stratified-v3',baseline_sensor_scores={'gdn':residual.tolist(),pca_name:pca_scores.tolist()},
        low_support_protocol='ordinary screening, diagnostic ranking only',single_group_diagnostic_top1=bool(single_best and truth[single_best['index']]),
        baseline_primary_target_top1={'gdn':bool(truth[int(np.nanargmax(residual))]),pca_name:bool(truth[int(np.nanargmax(pca_scores))])},
        primary_target_top1=bool(best and truth[best['index']]),primary_target_screened=any(truth[i] for kind,i in candidates if kind=='observation'),
        primary_target_best_score=max([r['score'] for r in observations if truth[r['index']]],default=None),
        observation_window_null_tail=float(null_tail_value(cal['null_references']['observation/proposed'],selected)),graph=g)
    np.savez_compressed(path.with_suffix('.npz'),input=x,primary_target_truth=truth,**raw);json_save(path,report);return report

for index in range(min(12,len(base))):
    x,truth,fault=inject_observation(base[index],44100+index,'offset',strength=[.5,1,2,4][index%4],duration=[4,8,16][index%3]);target=int(np.flatnonzero(truth)[0])
    partition=select_witnesses(target,np.isfinite(x),graph);excluded={graph['groups'][target],*partition['groups']};available=[j for j in range(len(x)) if graph['groups'][j] not in excluded]
    rng=np.random.default_rng(33500+index);ordering=rng.permutation(available)
    for fraction in [0.,.125,.25,.5]:
        changed=x.copy();channels=ordering[:int(round(fraction*len(available)))];changed[channels,-8:]+=2.
        evaluate(f'conditioning_{index}_{fraction}',changed,graph,truth,dict(family='conditioning_source_contamination',fraction=fraction,contaminated_channels=channels.tolist(),primary_fault=fault,block=str(d['block'][source_indices[index]]),source_index=int(source_indices[index])))
    for fraction in [.1,.3]:
        changed=copy.deepcopy(graph)
        for repeat in range(max(1,int(round(fraction*len(graph['edges'])/2)))):changed,_,_=inject_association(changed,70000+index*100+repeat,'wrong_endpoint')
        evaluate(f'graph_errors_{index}_{fraction}',x,changed,truth,dict(family='graph_error',requested_fraction=fraction,primary_fault=fault))
    # Remove all but one available witness source while preserving the suspect.
    low=x.copy();allowed={graph['groups'][target],partition['groups'][0]}
    for ch,group in enumerate(graph['groups']):
        if group not in allowed:low[ch,-8:]=np.nan
    evaluate(f'low_support_{index}',low,graph,truth,dict(family='single_source_support',primary_fault=fault,
        block=str(d['block'][source_indices[index]]),source_index=int(source_indices[index])))
    dropped=x.copy();dropped[target,-8:]=np.nan
    evaluate(f'dropout_{index}',dropped,graph,truth,dict(family='missingness',availability_alert=bool(np.isnan(dropped[target,-8:]).all()),numeric_edit_expected='abstain'),candidates=[('observation',target)])
    copies=copy.deepcopy(graph);edges=[copy.deepcopy(e) for e in graph['edges'] if e['source']==target]
    for j,edge in enumerate(edges*3):
        edge=copy.deepcopy(edge);edge['id']=edge['id']+f'_unknown_alias_{j}';copies['edges'].append(edge)
    evaluate(f'unknown_aliases_{index}',x,copies,truth,dict(family='unknown_provenance_association_copies',copies=3*len(edges),primary_fault=fault))
    if contaminated is not None:evaluate(f'training_contamination_{index}',x,graph,truth,dict(family='training_contamination',fraction=.1,primary_fault=fault,normalizer='original fixed'),member_models=contaminated['diffusion'])

if name.startswith('synthetic_32'):
    # The same saved measurements admit two explicitly different latent stories.
    normal,latent,regime,units,_=simulate(32,192,830001,nonlinear=name.endswith('nonlinear'))
    physical,shifted_latent,_,_,_=simulate(32,192,830001,nonlinear=name.endswith('nonlinear'),event=dict(start=120,stop=192,magnitude=4,latent=0))
    normalized=transform_measurements(physical,meta['normalizer']).T[:,-64:].astype('float32')
    fault_measurements=normal+(physical-normal)
    roundoff=float(np.max(np.abs(fault_measurements-physical)))
    assert np.allclose(fault_measurements,physical,rtol=0,atol=1e-12)
    fault_measurements=physical.copy()
    ambiguous=evaluate('common_mode_identifiability',normalized,graph,np.zeros(32,bool),dict(family='identifiability_counterexample',
        process_story='latent driver changed while all sensors remained correct',fault_story='unchanged process plus coordinated sensor errors exactly equal to the physical response',
        measurement_identical=True,arithmetic_roundoff=roundoff,observation_fault_truth='not identifiable from the shared measurements'))
    np.savez_compressed(out/'identifiability_latents.npz',normal=normal,physical=physical,common_mode_fault=fault_measurements,latent_normal=latent,latent_changed=shifted_latent)
    stale,stale_latent,_,_,_=simulate(32,192,830002,nonlinear=name.endswith('nonlinear'),association_change=dict(start=120,channel=0,new_latent=1))
    np.savez_compressed(out/'physical_stale_latents.npz',measurements=stale,latent=stale_latent,seed=np.array(830002),change_start=np.array(120),changed_channel=np.array(0),new_latent=np.array(1))
    values=transform_measurements(stale,meta['normalizer']).T[:,-64:].astype('float32')
    evaluate('physical_stale_associations',values,graph,np.zeros(32,bool),dict(family='physical_relation_change',changed_channel=0,
        changed_latent=1,association_truth=[i for i,e in enumerate(graph['edges']) if e['source']==0 or e['target']==0],observation_fault_truth='none injected; measurements follow changed physical response'))
json_save(out/'complete.json',dict(dataset=name,main_parameters_frozen=True))
