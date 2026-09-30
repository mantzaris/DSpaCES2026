"""Verify local research lineage and write portable checksums after retrieval."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import platform
import subprocess

import numpy as np

from iot_entropy.utils import digest,recorded_runtime,write_json
from iot_entropy.calibration import rank_pvalues

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--allow-partial',action='store_true');args=parser.parse_args()
config=json.loads((root/'configs/full.json').read_text())
checks=[];models=[];runs=[];data_records=[];event_manifests={}
for path in sorted((root/'data/manifests').glob('*.json')):
    manifest=json.loads(path.read_text())
    if 'processed_sha256' not in manifest:continue
    data_path=root/'data/processed'/f'{path.stem}.npz'
    actual=digest(data_path);expected=manifest['processed_sha256']
    if actual!=expected:raise ValueError('Processed-data hash mismatch: '+str(data_path))
    data_records.append({'dataset':path.stem,'path':str(data_path.relative_to(root)),'sha256':actual,
                         'manifest_sha256':digest(path),'shape':manifest['shape']})
for name,record in json.loads((root/'data/manifests/raw_sources.json').read_text()).items():
    if digest(root/'data/raw'/name)!=record['sha256']:raise ValueError('Raw-source hash mismatch: '+name)
for path in sorted((root/'experiments/full').rglob('*-training.json')):
    record=json.loads(path.read_text())
    checkpoint=path.parent/'checkpoints'/Path(record['checkpoint']).name
    if digest(checkpoint)!=record['checkpoint_sha256']:raise ValueError('Checkpoint mismatch: '+str(checkpoint))
    models.append({'path':str(checkpoint.relative_to(root)),'sha256':record['checkpoint_sha256'],
                   'dataset':record['dataset'],'kind':record['kind'],'graph':record['graph'],
                   'seed':record['seed'],'screened':record['screen'],'parameters':record['parameters'],
                   'training_seconds':record['training_seconds']})
for status_path in sorted((root/'experiments/full').glob('score-*/status.json')):
    directory=status_path.parent;status=json.loads(status_path.read_text())
    with np.load(directory/'predictions.npz') as archive:
        pvalues=archive['pvalues'];maxima=archive['maxima'];methods=archive['methods'].tolist()
    events=json.loads((directory/'events.json').read_text())
    if len(events)!=len(pvalues):raise ValueError('Event/prediction count mismatch')
    if not np.isfinite(pvalues).all():raise ValueError('Nonfinite rank value')
    if not ((pvalues>0)&(pvalues<=1)).all():raise ValueError('Invalid rank value')
    with np.load(directory/'calibration.npz') as archive:
        if archive['methods'].tolist()!=methods:raise ValueError('Calibration method order mismatch')
        calibration=archive['maxima']
    rebuilt=np.stack([rank_pvalues(calibration[:,column],maxima[:,:,column]) for column in range(len(methods))],-1)
    np.testing.assert_array_equal(rebuilt,pvalues)
    name=status['dataset']
    if name in event_manifests and events!=event_manifests[name]:raise ValueError('Fault realizations differ across seeds/graphs: '+name)
    event_manifests[name]=events
    runs.append({'path':str(directory.relative_to(root)),'dataset':status['dataset'],'seed':status['seed'],'graph':status['graph'],
                 'configuration_sha256':digest(directory/'configuration.json'),'prediction_sha256':digest(directory/'predictions.npz'),
                 'calibration_sha256':digest(directory/'calibration.npz'),'events_sha256':digest(directory/'events.json'),
                 'groups_sha256':digest(directory/'groups.json'),'reference_group_scores_sha256':digest(directory/'samples/group_scores.npz'),
                 'rank_values_exactly_recomputed':True,'identical_events_across_seeds_and_graphs':True,
                 'checkpoint_sha256':status['checkpoint_sha256'],'events':len(events),'calibration_units':status['calibration_units'],
                 'recording_blocks':status['independent_recording_blocks'],
                 'independence':'Independent simulations' if status['dataset'].startswith('synthetic') else 'Disjoint recordings; independence not established'})
if not args.allow_partial:
    if len(models)!=45 or len(runs)!=25:raise ValueError(f'Expected 45 models and 25 full scoring runs; got {len(models)}, {len(runs)}')
    if json.loads((root/'experiments/post-primary-status.json').read_text())['status']!='complete':raise ValueError('Sensitivity stages incomplete')
    if json.loads((root/'experiments/sensitivity/directions-status.json').read_text())['status']!='complete':raise ValueError('Direction and injection-observability audits incomplete')
    if json.loads((root/'experiments/sensitivity/ensembles-status.json').read_text())['status']!='complete':raise ValueError('Selected raw ensemble recovery incomplete')
    if recorded_runtime(root)>config['gpu_hour_budget']*3600:raise ValueError('Recorded stage total exceeds configured ceiling')
source_paths=[*root.glob('src/iot_entropy/*.py'),*root.glob('scripts/*'),root/'configs/full.json']
sources={str(path.relative_to(root)):digest(path) for path in source_paths if path.is_file()}
write_json(root/'environment/reporting-environment.json',{'python':platform.python_version(),'platform':platform.platform(),
           'packages':{name:importlib.metadata.version(name) for name in ['numpy','pandas','matplotlib','torch']}})
write_json(root/'experiments/artifact-manifest.json',{'status':'partial' if args.allow_partial else 'verified',
           'git_revision_at_audit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
           'configuration_sha256':digest(root/'configs/full.json'),'sources':sources,'datasets':data_records,'models':models,'scoring_runs':runs,
           'recorded_gpu_stage_seconds':recorded_runtime(root),'configured_ceiling_seconds':config['gpu_hour_budget']*3600,
           'historical_code':{'protocol':'ca953f5','model_training':'88701ce','primary_scoring':'aa81887',
                              'common_support_fidelity':'6f317d6','benchmark':'b912fa23',
                              'core_sensitivities':'73ce2c4','direction_and_observability':'b912fa23'},
           'lineage_note':'Intel coverage preprocessing was amended in c4d839c before Intel training loaded its data. Primary scoring imported aa81887 code before later reporting/interface changes. Git hashes are this project’s code history; shared-repository commits may also contain sibling work.'})
print(json.dumps({'verified_datasets':len(data_records),'verified_checkpoints':len(models),'verified_scoring_runs':len(runs),
                  'recorded_gpu_stage_hours':recorded_runtime(root)/3600}))
