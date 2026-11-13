"""Generate a meaningful source patch and hashes without modifying originals."""
from pathlib import Path
import difflib
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    files=['regional_twin_study.tex','references.bib','generated/numbers.tex','generated/principal_rows.tex']
    changes=[]
    for relative in files:
        old=ROOT/'baseline/manuscript'/relative
        new=ROOT/relative
        changes.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),
            fromfile='a/manuscript/'+relative,tofile='b/manuscript-revised/'+relative))
    relative='generated/alarm_matched_rows.tex'
    changes.extend(difflib.unified_diff([], (ROOT/relative).read_text().splitlines(True),
        fromfile='/dev/null',tofile='b/manuscript-revised/'+relative))
    (ROOT/'source_changes.patch').write_text(''.join(changes))
    includes=['regional_twin_study.tex','regional_twin_study.pdf','regional_twin_study_diff.tex',
              'regional_twin_study_diff.pdf','figure_changes.tex','figure_changes.pdf',
              'response_to_reviewers.md','change_summary.md','revision_analysis.md',
              'source_changes.patch','README.md','build.sh','references.bib','IEEEtran.cls','IEEEtran.bst',
              'VENUE_REVISION_NOTE.md']
    for optional in ['regional_twin_study_source.zip', 'regional_twin_study_source.zip.sha256']:
        if (ROOT/optional).exists():
            includes.append(optional)
    for directory in ['scripts','analysis','figures','generated']:
        includes += [str(p.relative_to(ROOT)) for p in (ROOT/directory).rglob('*') if p.is_file()]
    manifest={name:sha(ROOT/name) for name in sorted(set(includes))}
    (ROOT/'artifact_manifest.json').write_text(json.dumps({'sha256':manifest,'raw_data_included':False,
       'baseline_commit':'c2ef65803307ea1652d359dc3e530e3c6af40193',
       'gpu_computation':False,'original_principal_results_preserved':True},indent=2)+'\n')
    print('Wrote source comparison and',len(manifest),'artifact hashes.')

if __name__=='__main__':main()
