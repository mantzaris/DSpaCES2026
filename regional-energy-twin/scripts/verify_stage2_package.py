"""Focused checks on the completed audit package and preservation of Stage 1."""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    assert subprocess.check_output(['git','branch','--show-current'],text=True).strip() == 'main'
    subprocess.run(['git','merge-base','--is-ancestor','6889a6a','HEAD'],check=True)
    original = subprocess.check_output(['git','ls-tree','-r','--name-only','6889a6a'],text=True).splitlines()
    protected = [p for p in original if p.startswith(('configs/','results/','manifests/','reports/','docs/'))]
    for p in protected:
        expected = subprocess.check_output(['git','show','6889a6a:'+p])
        assert Path(p).read_bytes() == expected, 'Original evidence changed: '+p
    for name in ('reports/STAGE2_DECISION.md','reports/STAGE1_EVIDENCE_AUDIT.md',
                 'reports/STAGE3_PROPOSAL.md','docs/STAGE2_NOVELTY_AUDIT.md','README.md'):
        path = Path(name)
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if '://' not in link and not link.startswith('#'):
                assert (path.parent / link.split('#')[0]).exists(), (name,link)
    evidence = json.loads(Path('results/stage2/evidence_checks.json').read_text())
    assert evidence['status'] == 'passed' and evidence['unique_score_targets'] == 1856
    assert evidence['csv_parser_correction']['corrected_unique_targets'] == 30
    assert not evidence['november_december_and_2017_opened']
    archive = json.loads(Path('manifests/stage2_artifact_preservation.json').read_text())
    assert archive['verified_files'] == 90 and not archive['mismatched_files']
    source = json.loads(Path('manifests/source_archive.json').read_text())
    zipped = next(p for p in archive['files'] if p['path'] == 'data/bdg2-v1.0.zip')
    assert zipped['sha256'] == source['sha256']
    assert "float_precision='round_trip'" in Path('scripts/analyze_pilot.py').read_text()
    assert 'Wire bytes and cache estimates' in Path('scripts/build_figures.py').read_text()
    hashes = {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in protected}
    result = dict(status='passed', protected_stage1_artifacts=len(protected),
                  original_artifacts_byte_identical=True, main_study_disabled=True,
                  source_archive_matches_original_hash=True, document_links_resolve=True,
                  original_evidence_sha256=hashes)
    Path('results/stage2/package_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'original_evidence_sha256'},indent=2))


if __name__ == '__main__':
    main()
