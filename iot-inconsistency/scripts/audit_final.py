"""Release audit for the actual research artifacts and completed IEEE manuscript."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import json_save
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
checks=[]
def check(condition,name):
    assert condition,name
    checks.append(name)

names=read('configs/study.json')['datasets']
for name in ['training_v2','main_experiments','secondary_experiments','finish_artifacts','verify_final_gpu','final_stress']:
    check(read('results/jobs/'+name+'.json')['state']=='complete','completed job '+name)
for name in names:
    check((ROOT/'results/ablations'/name/'complete.json').is_file(),'all inference ablations '+name)
    stress=read('results/robustness/'+name+'/analysis.json')
    check(bool(stress['conditions']),'final stress analysis '+name)
for file in ['reference_checks','parity_cpu','parity_cuda','persistence']:
    check(read('results/audits/'+file+'.json')['status']=='passed','passed '+file)
for file in ['pytest_cpu.xml','pytest_cuda.xml']:
    suites=ET.parse(ROOT/'results/audits'/file).getroot().iter('testsuite')
    total=0
    for suite in suites:
        check(int(suite.attrib['failures'])==int(suite.attrib['errors'])==0,'passing suite '+file)
        total+=int(suite.attrib['tests'])
    check(total>=16,'integration coverage '+file)
oracle=read('results/audits/production_equations.json')
check(oracle['max_absolute_error']<=oracle['tolerance'],'independent production arithmetic')
count=0
for item in oracle['checks']:
    case=read(item['case']);path=str(Path(item['case']).parent/case['raw_artifact'])
    check(sha(path)==case['raw_sha256']==item['sha256'],'original predictive samples '+item['case'])
    count+=len(case['records'])
check(count==oracle['candidates'],'audited candidate count')
manifest=read('results/model_weights/manifest.json')
for model in manifest['models']:
    check(sha(model['path'])==model['sha256'],'portable state '+model['path'])
portable=read('results/audits/portable_models.json')
check(portable['weight_files_verified']==len(manifest['models']),'portable checkpoint audit coverage')
check({r['dataset'] for r in portable['cases']}==set(names),'deterministic inference for every configuration')
for row in read('results/audits/inference_repeatability.json')['cases']:
    check(row['deterministic_copy_invariance']=='exact array equality','trained-model known-copy invariance '+row['dataset'])
check(len(read('results/audits/pca_scores.json')['checks'])==40,'all saved PCA projections audited')
for dataset,record in read('results/pca_total/analysis.json')['results'].items():
    check(len(record['audits'])==24,'full-norm and coordinate PCA audit '+dataset)
    check(sha(record['artifact'])==record['sha256'],'full-norm PCA saved predictions '+dataset)
check(len(read('results/audits/trained_models.json')['checks'])==30,'trained graph and state-space operations audited')
latency=read('results/latency_scaling.json')
check(len(latency['runs'])==40,'candidate-scaling timing runs')
for row in latency['runs']:
    reported=[int(line.split(',')[0]) for line in row['reported_gpu_processes'].splitlines() if line.strip()]
    check(reported==[row['process_id']],'only benchmark process reported on GPU')
browser=read('results/interface/browser_verification.json');bundle=read('results/graph/synthetic_32_nonlinear_illustration.json')
check(browser['run_id']==bundle['run']['id'],'browser tested current evidence version')
ledger=read('results/paper_claims.json');check(ledger['draft'] is False,'final manuscript generation')
for source,digest in ledger['sources'].items():check(sha(source)==digest,'claim source '+source)
for file,digest in ledger['generated_outputs'].items():check(sha('paper/generated/'+file)==digest,'generated manuscript fragment '+file)
for value in ledger['displayed_values']:
    if 'source' in value:
        original=read(value['source'])
        for key in value['json_path']:original=original[key]
        check(original==value['value'],'displayed result '+value['output']+' '+str(value['json_path']))
figures=read('paper/figures/provenance.json')
for name in ['architecture','network','confidence','equations','score_terms','penalty_grid']:
    for source in figures[name]['inputs']:
        check(not source.get('pending',False),'complete figure source '+source['path'])
        if 'sha256' in source:check(sha(source['path'])==source['sha256'],'figure input '+source['path'])
        else:
            for file,digest in source['root_json_files'].items():check(sha(str(Path(source['path'])/file))==digest,'figure directory input '+file)
    for suffix,digest in figures[name]['outputs'].items():check(sha('paper/figures/'+name+'.'+suffix)==digest,'figure output '+name+'.'+suffix)
check(sha(figures['generator']['path'])==figures['generator']['sha256'],'figure generator version')
pdf=ROOT/'paper/main.pdf'
info=subprocess.check_output(['pdfinfo',str(pdf)],text=True);pages=int(re.search(r'Pages:\s+(\d+)',info).group(1))
check(pages<=10,'IEEE page limit including references')
text=subprocess.check_output(['pdftotext',str(pdf),'-'],text=True)
check(not re.search(r'Layout draft|still running|pending in this|awaits the running|\[\?\]|\?\?',text),'no draft placeholders or unresolved references')
log=(ROOT/'paper/main.log').read_text()
check(not re.search(r'Overfull \\[hv]box|undefined references|Citation .* undefined',log),'no overflowing boxes or unresolved citations')
check(len(re.findall(r'\\label\{eq:',(ROOT/'paper/main.tex').read_text()))==14,'all fourteen method equations displayed')
check(len(read('equation_to_code.json'))==21,'method and comparator equation mappings')
json_save(ROOT/'results/audits/final.json',dict(status='passed',timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    checks=checks,pages=pages,primary_cases=oracle['cases'],primary_candidates=count,portable_models=len(manifest['models']),
    model_bytes=manifest['total_bytes'],manuscript_sha256=sha('paper/main.pdf'),manuscript_source_sha256=sha('paper/main.tex'),
    claims_sha256=sha('results/paper_claims.json'),figure_provenance_sha256=sha('paper/figures/provenance.json'),
    scope='Local release verification of completed experiments, saved outputs, figures and manuscript. No submission or remote Git push.'))
print('Final audit passed',len(checks),'checks;',pages,'pages;',len(manifest['models']),'portable model states')
