"""Check camera-ready documents and immutable sources; outputs stay revision-local."""
import hashlib,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
REPO=PROJECT.parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(*args):return subprocess.check_output(args,text=True)
def main():
    old=(ROOT/'baseline/manuscript/regional_twin_study.tex').read_text()
    new=(ROOT/'regional_twin_study.tex').read_text()
    abstract=lambda s:s.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
    title=lambda s:re.search(r'\\title\{([^}]+)\}',s).group(1)
    assert title(old)==title(new)=='From Detail to Decisions in Regional Energy Twins'
    assert abstract(old)==abstract(new), 'Abstract text changed'
    assert 'pdfauthor={Alexander V. Mantzaris and James H. Korris}' in new
    assert r'\IEEEauthorblockN{James H. Korris}' in new
    assert (ROOT/'baseline/manuscript/generated/numbers.tex').read_bytes()==(ROOT/'generated/numbers.tex').read_bytes(), 'Abstract macro values changed'
    for tag in ['proposition','proof']:
        blocks=lambda s:re.findall(r'\\begin\{'+tag+r'\}.*?\\end\{'+tag+r'\}',s,re.S)
        assert blocks(old)==blocks(new), 'Mathematical block changed: '+tag
    manifest=json.loads((ROOT/'internal/baseline_manifest.json').read_text())
    for path,expected in manifest['original_tracked_hashes'].items():
        assert digest(REPO/path)==expected, 'Original artifact changed: '+path
    assert (ROOT/'generated/principal_rows.tex').read_bytes()==(ROOT/'baseline/manuscript/generated/principal_rows.tex').read_bytes()
    docs={}
    for name,renderdir in [('regional_twin_study','render-clean'),('regional_twin_study_diff','render-diff'),('figure_changes','render-figures')]:
        pdf=ROOT/(name+'.pdf');log=(ROOT/(name+'.log')).read_text()
        info=command('pdfinfo',str(pdf));fonts=command('pdffonts',str(pdf))
        pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
        issues=[line for line in log.splitlines() if re.search(r'undefined|Overfull|(?:LaTeX|Package .*|pdfTeX) [Ww]arning',line)]
        assert not re.search(r'(Citation|Reference).*undefined|There were undefined|Undefined control sequence',log,re.I),issues
        assert 'Type 3' not in fonts
        for row in fonts.splitlines()[2:]:
            if row.strip():assert row.split()[-5]=='yes', 'Unembedded font: '+row
        out=ROOT/'internal'/renderdir;out.mkdir(parents=True,exist_ok=True)
        for previous in out.glob('page-*.png'):
            previous.unlink()
        subprocess.run(['pdftoppm','-r','100','-png',str(pdf),str(out/'page')],check=True)
        assert len(list(out.glob('page-*.png')))==pages
        for item in (ROOT/(name+'.fls')).read_text().splitlines():
            if item.startswith('OUTPUT '):
                written=(ROOT/item[7:]).resolve()
                assert ROOT in written.parents, 'Build output escaped revision: '+str(written)
        docs[name]=dict(pages=pages,pdf_sha256=digest(pdf),warnings=issues,font_inventory=fonts)
    checks=dict(title_unchanged=True,abstract_verbatim=True,abstract_macros_unchanged=True,
                propositions_and_proofs_unchanged=True,original_result_table_unchanged=True,
                original_files_verified=len(manifest['original_tracked_hashes']),documents=docs,
                approved_author_block=True,latex_outputs_revision_local=True,
                visual_inspection='Pending review of every rendered page',gpu_used=False)
    (ROOT/'internal/validation.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps({name:{'pages':r['pages'],'warnings':r['warnings']} for name,r in docs.items()},indent=2))
    assert docs['regional_twin_study']['pages']<=10, 'Clean manuscript exceeds ten pages'

if __name__=='__main__':main()
