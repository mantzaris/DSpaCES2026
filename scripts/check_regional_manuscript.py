"""Build-output checks and page renders; visual review is performed separately."""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    root=Path('manuscript'); pdf=root/'regional_twin_study.pdf'
    info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True)
    text=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True)
    pages=text.split('\f')
    if not pages[-1].strip():pages.pop()
    log=(root/'regional_twin_study.log').read_text()
    assert 8<=len(pages)<=10, 'Outside chosen 8-10 page full-paper format'
    assert not re.search(r'undefined|Overfull|Citation .*undefined|Reference .*undefined',log,re.I)
    assert '??' not in text
    assert 'Alexander V. Mantzaris' in text and 'alexander.mantzaris@ucf.edu' in text
    font_rows=[line.split() for line in fonts.splitlines()[2:] if line.strip()]
    assert all('yes' in row for row in font_rows), 'Inspect font embedding'
    assert 'Type 3' not in fonts, 'Bitmap font found'
    output=Path('results/synthesis');output.mkdir(exist_ok=True)
    result=dict(pages=len(pages),page_word_counts=[len(p.split()) for p in pages],
        pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
        embedded_font_inventory=fonts,document_info=info,
        missing_references=False,overfull_boxes=False,
        visual_review='Pending separate human-equivalent page inspection by the agent; not certified by this script')
    review_path=output/'visual_review.json'
    if review_path.exists():
        review=json.loads(review_path.read_text())
        if review.get('pdf_sha256')==result['pdf_sha256']:
            result['visual_review']='All pages inspected; see visual_review.json for this exact PDF hash'
    (output/'manuscript_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    render=Path('/tmp/regional-twin-manuscript-review');render.mkdir(exist_ok=True)
    subprocess.run(['pdftoppm','-r','110','-png',str(pdf),str(render/'page')],check=True)
    print(json.dumps({k:v for k,v in result.items() if k not in ['embedded_font_inventory','document_info']},indent=2))


if __name__=='__main__':main()
