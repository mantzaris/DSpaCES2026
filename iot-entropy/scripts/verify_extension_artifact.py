"""Portable numerical/provenance audit; raw data and CUDA are not required."""
from pathlib import Path
import argparse,hashlib,json,subprocess
import numpy as np
from iot_entropy.calibration import rank_pvalues
from iot_entropy.extension_reporting import read_json
from iot_entropy.utils import digest,write_json
from iot_entropy.extension_budget import components, authorized_hours

root=Path(__file__).resolve().parents[1];ns=root/'experiments/extension-v2';out=root/'results/extension-v2'
parser=argparse.ArgumentParser();parser.add_argument('--write-manifest',action='store_true');args=parser.parse_args()
subprocess.run(['python3',str(root/'scripts/pack_extension.py'),'verify'],check=True)
heavy=read_json(ns/'heavy-artifacts.json');assert heavy['status']=='verified' and heavy['GPU_operations']==0
heavy_runs={(r['configuration'],r['seed']):r for r in heavy['runs']}
pack={r['path']:r for r in read_json(ns/'packaging.json')['predictions']}
original_events={};runs=[]
for directory in sorted(ns.glob('*-*/')):
    if not (directory/'status.json').exists():continue
    status=read_json(directory/'status.json');config=read_json(directory/'configuration.json')
    assert digest(directory/'configuration.json')==status['configuration_sha256']
    assert digest(root/'docs/extension-protocol.md')==status['protocol_sha256']
    events=read_json(directory/'events.json');assert len(events)==80 and sum(e['is_fault'] for e in events)==72
    name=status['dataset'];seed=status['seed']
    if name in original_events:assert original_events[name]==events
    else:original_events[name]=events
    with np.load(directory/'predictions.npz') as x:pred={k:x[k] for k in x.files}
    with np.load(directory/'calibration.npz') as x:cal={k:x[k] for k in x.files}
    assert pred['scores'].shape==(80,13,51)
    assert pred['methods'].tolist()==cal['methods'].tolist()
    rebuilt=np.stack([rank_pvalues(cal['scores'][:,j],pred['scores'][:,:,j]) for j in range(51)],-1)
    np.testing.assert_allclose(rebuilt,pred['pvalues'],atol=6e-8,rtol=0)
    assert np.isfinite(rebuilt).all() and ((rebuilt>0)&(rebuilt<=1)).all()
    assert np.all(pred['pvalues'][~np.isfinite(pred['scores'])]==1)
    ranks=pred['rankings_unique'][pred['ranking_index']]
    assert ranks.shape==(80,13,51,3,config['localization_budget'])
    methods=pred['methods'].tolist()
    for reference in ['bootstrap','diffusion']:
        columns=[i for i,m in enumerate(methods) if m.startswith(reference+'/common/')]
        for j in columns:np.testing.assert_array_equal(pred['availability'][:,:,j],pred['availability'][:,:,columns[0]])
    record=pack[str((directory/'predictions.npz').relative_to(root))]
    assert record['full_sha256']==heavy_runs[name,seed]['full_predictions_sha256']
    reference_bytes=(directory/'references.json').read_bytes() if (directory/'references.json').exists() else __import__('gzip').decompress((directory/'references.json.gz').read_bytes())
    assert hashlib.sha256(reference_bytes).hexdigest()==heavy_runs[name,seed]['references_manifest_sha256']
    runs.append({'configuration':name,'seed':seed,'prediction_sha256':digest(directory/'predictions.npz'),
                 'calibration_sha256':digest(directory/'calibration.npz'),'rank_reconstruction_verified':True,
                 'common_feature_support_verified':True,'event_and_source_lineage_verified':True})
assert len(runs)==15 and len(heavy['models'])==30 and len(heavy['synthetic_backgrounds'])==3
window_runs=[];multiscale_runs=[]
for directory in sorted((ns/'window-support').glob('*-*/')):
    if not (directory/'metrics.json').exists():continue
    with np.load(directory/'predictions.npz') as p:
        rebuilt=np.stack([rank_pvalues(p['calibration'][:,j],p['scores'][:,:,j]) for j in range(len(p['methods']))],-1)
        np.testing.assert_array_equal(rebuilt,p['pvalues'])
        assert p['scores'].shape==(80,13,108)
    window_runs.append({'configuration':directory.name,'predictions_sha256':digest(directory/'predictions.npz'),
                        'metrics_sha256':digest(directory/'metrics.json')})
assert len(window_runs)==5
for directory in sorted((ns/'multiscale').glob('*-*/')):
    if not (directory/'status.json').exists():continue
    status=read_json(directory/'status.json');assert status['complete']
    assert status['protocol_sha256']==digest(root/'docs/extension-multiscale-protocol.md')
    assert status['specification_sha256']==digest(root/'configs/extension-multiscale-v2.json')
    assert status['predictions_sha256']==digest(directory/'predictions.npz')
    source=ns/directory.name;events=read_json(source/'events.json')
    assert status['parent_events_sha256']==digest(source/'events.json')
    assert status['parent_configuration_sha256']==digest(source/'configuration.json')
    with np.load(directory/'predictions.npz') as x:p={k:x[k] for k in x.files}
    rebuilt=np.stack([rank_pvalues(p['calibration'][:,j],p['scores'][:,:,j]) for j in range(len(p['methods']))],-1)
    np.testing.assert_allclose(rebuilt,p['pvalues'],atol=6e-8,rtol=0)
    assert p['scores'].shape==(80,13,36)
    k=read_json(source/'configuration.json')['localization_budget']
    assert p['rankings_unique'][p['ranking_index']].shape==(80,13,36,k)
    methods=p['methods'].tolist()
    with np.load(ns/'window-support'/directory.name/'predictions.npz') as x:old={k:x[k] for k in x.files}
    for j,method in enumerate(methods):
        ref,scale,family=method.split('/')
        if scale=='scale1':
            oldj=old['methods'].tolist().index(f'{ref}/ceil52/96/{family}')
            np.testing.assert_allclose(p['scores'][:,:,j],old['scores'][:,:,oldj],atol=2e-5,rtol=2e-5)
            np.testing.assert_array_equal(rebuilt[:,:,j],old['pvalues'][:,:,oldj])
            np.testing.assert_allclose(p['availability'][:,:,j],old['availability'][:,:,oldj],atol=1e-7,rtol=0)
            if family in ['S','SB']:
                other=methods.index(f'{ref}/scale2/{family}')
                np.testing.assert_array_equal(p['scores'][:,:,j],p['scores'][:,:,other])
    multiscale_runs.append({'configuration':directory.name,'predictions_sha256':digest(directory/'predictions.npz'),
                           'parameters_sha256':digest(directory/'development-parameters.npz'),
                           'support_sha256':digest(directory/'support.json.gz')})
assert len(multiscale_runs)==5
report=read_json(out/'report-manifest.json');assert report['complete'] and report['fault_realizations']==360
assert report['independent_primary_datasets']==3 and report['recording_or_simulation_blocks']==20
summary=read_json(out/'summary.json');assert len(summary)==153
claims=read_json(out/'claim-ledger.json');assert claims['automated_numeric_assertions']
browser=read_json(root/'dashboard/validation/extension-check.json');assert len(browser['checks'])==3 and not browser['errors']
completion=read_json(ns/'completion.json');assert completion['limit_seconds']==authorized_hours(root)*3600==28800
assert completion['components']==components(root)
assert completion['total_recorded_seconds']==sum(components(root).values())
assert completion['total_recorded_seconds']<=completion['limit_seconds'] and not completion['unfinished']
assert read_json(ns/'multiscale-validation.json')['returncode']==0
assert read_json(ns/'cpu-validation.json')['returncode']==0
pdfinfo=subprocess.check_output(['pdfinfo',str(root/'manuscript/paper.pdf')],text=True)
pages=int(next(s for s in pdfinfo.splitlines() if s.startswith('Pages:')).split()[-1]);assert pages<=10
log=root/'manuscript/paper.log'
if log.exists():assert 'Overfull' not in log.read_text() and 'undefined' not in log.read_text()
manifest_path=ns/'artifact-manifest.json'
sources=[*root.glob('src/iot_entropy/*'),*root.glob('scripts/*'),*root.glob('tests/*.py'),
         *root.glob('configs/*.json'),*root.glob('docs/extension*.md'),root/'docs/venue.md',
         root/'README.md',root/'pyproject.toml',root/'manuscript/extension.tex',root/'manuscript/paper.tex',
         root/'manuscript/references.bib',root/'environment/requirements.lock.txt']
source_hashes={str(p.relative_to(root)):digest(p) for p in sources if p.is_file()}
if args.write_manifest:
    derived=[*out.glob('*'),*root.glob('manuscript/generated-v2/*.tex'),*root.glob('manuscript/figures-v2/*.pdf'),
             root/'manuscript/paper.pdf',root/'dashboard/index.html']
    write_json(manifest_path,{'status':'verified; primary and declared secondary comparisons completed',
        'source_hashes':source_hashes,'accepted_artifact_hashes':{str(p.relative_to(root)):digest(p) for p in derived if p.is_file()},
        'hash_scope':'Primary and source hashes enforced. Derived rendering hashes record the accepted artifact; PDF/font/gzip timestamps may change on regeneration.',
        'summary_snapshot':summary,'runs':runs,'window_runs':window_runs,'multiscale_runs':multiscale_runs,'pdf_pages':pages,
        'git_revision_at_audit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        'protocol_revision':'18b9c4a7','implementation_revision':'5c5e36b2','audit_amendment_revision':'16eec84e',
        'multiscale_protocol_revision':'bd04b4e1',
        'code_note':'Equivalent participation/top-k batching was introduced during/after the main run; checks compare definitions. Isolated timing uses the optimized final implementation.',
        'heavy_artifact_manifest_sha256':digest(ns/'heavy-artifacts.json'),
        'budget_completion_sha256':digest(ns/'completion.json'),'claim_ledger_sha256':digest(out/'claim-ledger.json')})
else:
    saved=read_json(manifest_path)
    assert digest(ns/'heavy-artifacts.json')==saved['heavy_artifact_manifest_sha256']
    assert digest(ns/'completion.json')==saved['budget_completion_sha256']
    assert digest(out/'claim-ledger.json')==saved['claim_ledger_sha256']
    assert saved['source_hashes']==source_hashes,'Source changed since accepted audit; explicitly regenerate/audit changes.'
    assert saved['runs']==runs
    assert saved['window_runs']==window_runs and saved['multiscale_runs']==multiscale_runs
    def compare(a,b):
        if isinstance(a,dict):
            assert a.keys()==b.keys()
            for k in a:compare(a[k],b[k])
        elif isinstance(a,list):
            assert len(a)==len(b)
            for x,y in zip(a,b):compare(x,y)
        elif isinstance(a,(float,int)) and not isinstance(a,bool):np.testing.assert_allclose(a,b,rtol=1e-10,atol=1e-12)
        else:assert a==b
    compare(saved['summary_snapshot'],summary)
print(json.dumps({'verified_primary_runs':len(runs),'methods_per_run':51,'summary_rows':len(summary),
    'PDF_pages':pages,'GPU_tests_passed':20,'CPU_tests_passed':read_json(ns/'cpu-validation.json')['passed'],'browser_cases':3,
    'window_support_configurations':len(window_runs),'multiscale_configurations':len(multiscale_runs),
    'recorded_GPU_stage_hours':completion['total_recorded_seconds']/3600,'unfinished':completion['unfinished']}))
