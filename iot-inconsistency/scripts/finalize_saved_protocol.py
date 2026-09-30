"""Apply frozen score weights to saved losses and harmonize candidate calibration.

No test labels or detection metrics are read to choose any setting. This repairs
serialization and comparison-population inconsistencies using the specification.
"""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.scoring import repair_score
from iot_repair.costs import COST_PRECISION_VERSION
from iot_repair.experiment import json_save
config=json.loads((ROOT/'configs/study.json').read_text());changes=[]
for dataset in config['datasets']:
    directory=ROOT/'results/study'/dataset;parameters=json.loads((directory/'frozen.json').read_text());weights={key:parameters[key] for key in ('kappa','lambda')}
    for split in ['calibration','test']:
        for path in sorted((directory/split).glob(split+'_*.json')):
            case=json.loads(path.read_text())
            if case.get('score_parameters')==weights and case.get('cost_precision_version')==COST_PRECISION_VERSION:continue
            before_hash=hashlib.sha256(path.read_bytes()).hexdigest();raw=np.load(path.with_suffix('.npz'))
            if not case['records']:
                case['score_parameters']=weights;json_save(path,case);continue
            costs=np.empty(raw['loss_before'].shape[0])
            x=raw['input'].astype('float64')
            for row in case['records']:
                if row['kind']=='observation':
                    channel=row['index'];valid=np.isfinite(x[channel,-8:]);replacements=raw['replacement_targets'][row['raw_index']].astype('float64')
                    costs[row['raw_index']]=.5*valid.sum()/np.isfinite(x).sum()+.5*np.minimum(np.abs(replacements[...,valid]-x[channel,-8:][valid])/3,1).mean()
                else:costs[row['raw_index']]=1/len(case['graph']['edges'])
            terms=repair_score(torch.as_tensor(raw['loss_before'],device='cuda'),torch.as_tensor(raw['loss_after'],device='cuda'),
                torch.as_tensor(raw['group_weights'],device='cuda'),torch.as_tensor(costs,device='cuda'),
                uncertainty_weight=weights['kappa'],edit_weight=weights['lambda'],valid_groups=raw['valid_groups'])
            previous=case.get('score_parameters',dict(kappa=1.,**{'lambda':.2}))
            for row in case['records']:
                assert abs(row['score']-(row['mean_gain']-previous['kappa']*row['model_instability']-previous['lambda']*row['edit_cost']))<1e-9
                for key,value in terms.items():
                    if key!='model_gains':row[key]=float(value[row['raw_index']])
            case['score_parameters']=weights;case['cost_precision_version']=COST_PRECISION_VERSION;case['score_weights_at_predictive_sampling']=previous;case['score_recomputed_from_saved_losses']=True
            case['records'].sort(key=lambda r:r['score'],reverse=True);json_save(path,case)
            changes.append(dict(case=str(path.relative_to(ROOT)),previous_json_sha256=before_hash,updated_json_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),raw_predictions_unchanged=True))
    calibration=directory/'calibration_complete.json';original=json.loads(calibration.read_text())
    if 'observation/fixed_penalties' not in original['null_references'] or original.get('candidate_probability_population')!='common screened candidate pool v2' or any(r.get('case','').startswith('results/study/'+dataset+'/calibration/') for r in changes):
        archive=ROOT/'results/protocol_corrections'/dataset;archive.mkdir(parents=True,exist_ok=True)
        if not (archive/'initial_calibration.json').exists():shutil.copyfile(calibration,archive/'initial_calibration.json')
        subprocess.run([sys.executable,str(ROOT/'scripts/freeze.py'),'--dataset',dataset,'--stage','calibration'],check=True)
        corrected=json.loads(calibration.read_text())
        max_tail_score_change=0.
        for key,values in original['null_references'].items():
            np.testing.assert_allclose(corrected['null_references'][key],values,rtol=0,atol=1e-8)
            max_tail_score_change=max(max_tail_score_change,float(np.max(np.abs(np.asarray(corrected['null_references'][key])-values))))
        corrected['candidate_probability_population']='common screened candidate pool v2';json_save(calibration,corrected)
        changes.append(dict(dataset=dataset,correction='supervised probability references use the same screened candidate pool for all methods',
            maximum_null_score_roundoff=max_tail_score_change,unchanged=['models','score weights','raw predictions'],fitting_data='calibration blocks only',test_labels_used=False))
report_path=ROOT/'results/audits/protocol_finalization.json'
previous=json.loads(report_path.read_text())['changes'] if report_path.exists() else []
json_save(report_path,dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),changes=previous+changes,
    reason='specification compliance and scalar serialization; no test performance guided these corrections'))
