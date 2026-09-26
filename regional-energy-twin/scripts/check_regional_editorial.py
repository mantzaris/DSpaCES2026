"""Check editorial claims against retained results; no meter data or inference.

Run after manuscript/build.sh. The reference commit is the preceding synthesis,
not an experimental reset. All comparisons read committed artifacts only.
"""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

REFERENCE = 'b2fb7acbabbe315f7c004079c86086e5d283d8a8'


def prior(path):
    return subprocess.check_output(['git', 'show', REFERENCE+':'+path])


def main():
    unchanged = {}
    names = ['principal_results.csv', 'family_method_results.csv',
             'paired_background_B.csv', 'paired_background_C.csv',
             'paired_background_events.csv', 'diagnostic_path.csv',
             'threshold_margins.csv.gz', 'corrective_action_timing.csv',
             'corrective_action_summary.csv', 'summary.json']
    for name in names:
        path = 'results/synthesis/'+name
        old, new = prior(path), Path(path).read_bytes()
        if name.endswith('.gz'):
            old, new = gzip.decompress(old), gzip.decompress(new)
        assert old == new, 'Scientific output changed: '+path
        unchanged[path] = hashlib.sha256(new).hexdigest()
    rows = list(csv.DictReader(Path('results/synthesis/principal_results.csv').open()))
    b = {r['method']: float(r['local_one_hour_mae']) for r in rows if r['cohort']=='B'}
    gain = 100*(1-b['M4']/b['M3'])
    assert round(gain, 1)==18.3
    paired_counts = {}
    for cohort, methods in [('B', ['M0','M1','M3','M4']), ('C', ['M0','M3','M3b','M4'])]:
        pairs = list(csv.DictReader(Path('results/synthesis/paired_background_'+cohort+'.csv').open()))
        assert all(float(r['M4'])<float(r['M2']) for r in pairs)
        paired_counts[cohort] = len(pairs)*len(methods)
    immutable = ['manuscript/references.bib','manuscript/IEEEtran.cls','manuscript/IEEEtran.bst',
                 'configs/main_study.yaml','configs/regional_refinement.json',
                 'configs/regional_shock.json','configs/regional_acquisition.json',
                 'src/evidence_fusion/shock_access.py','src/evidence_fusion/shock_gaussian.py',
                 'src/evidence_fusion/acquisition_policy.py']
    for path in immutable:
        assert prior(path)==Path(path).read_bytes(), 'Unexpected scientific/template edit: '+path
    tex = Path('manuscript/regional_twin_study.tex').read_text()
    abstract = tex.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
    abstract = abstract.replace(r'\FineGainPercent{}', format(gain, '.1f'))
    word_count = len(abstract.split())
    assert 200<=word_count<=230
    assert not any(ord(c)>127 for c in tex), 'Non-ASCII authored LaTeX'
    assert tex.count(r'\begin{figure*}')==4 and tex.count(r'\begin{table*}')==2
    assert 'From Detail to Decisions in Regional Energy Twins' in tex
    checks = json.loads(Path('results/synthesis/manuscript_checks.json').read_text())
    assert checks['pages']<=10
    assert checks['pdf_sha256']==hashlib.sha256(Path('manuscript/regional_twin_study.pdf').read_bytes()).hexdigest()
    out = dict(reference_commit=REFERENCE, scientific_outputs_unchanged=unchanged,
               template_bibliography_configs_and_inference_unchanged=immutable,
               abstract_words=word_count, pages=checks['pages'], pdf_sha256=checks['pdf_sha256'],
               fine_access_reduction_percent=gain,
               effect_interpretation='B local 1h MAE: M4 full fine access versus M3, with a larger observation budget.',
               plotted_paired_points=paired_counts, figures=4, principal_tables=2,
               new_experiments=0, raw_meter_reads=0,
               figure_padding='Rendered text-bound checks execute in build_regional_study_results.py.',
               visual_review='Separate inspection required for this PDF hash.')
    path = Path('results/editorial/validation.json'); path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['scientific_outputs_unchanged','template_bibliography_configs_and_inference_unchanged']},indent=2))


if __name__=='__main__':
    main()
