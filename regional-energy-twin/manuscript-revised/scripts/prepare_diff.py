"""Readable latexdiff with tables compared individually, independent of float moves.

Float moves confuse latexdiff's alignment of unrelated table rows. We remove
whole tables before the prose comparison, compare the two existing tables
individually, and insert the added tables in blue. No source content is discarded.
The unified source patch separately exposes the actual source float relocation.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TABLE = re.compile(r'\\begin\{(table\*?)\}.*?\\end\{\1\}', re.S)

def flatten(path):
    def expand(match):
        target = path.parent / match.group(1)
        if not target.suffix:
            target = target.with_suffix('.tex')
        return flatten(target)
    return re.sub(r'\\input\{([^}]+)\}', expand, path.read_text())

def tables(text):
    found = {}
    for match in TABLE.finditer(text):
        block = match.group(0)
        label = re.search(r'\\label\{([^}]+)\}', block).group(1)
        found[label] = block
    return found

def diff(old, new, tag):
    a = ROOT / ('internal/'+tag+'_old.tex')
    b = ROOT / ('internal/'+tag+'_new.tex')
    a.write_text(old); b.write_text(new)
    result = subprocess.run(['latexdiff', '--math-markup=0', '--graphics-markup=none',
                             '--disable-citation-markup', str(a), str(b)],
                            capture_output=True, text=True, cwd=ROOT, check=True)
    with (ROOT/'internal/latexdiff.log').open('a') as log:
        log.write(tag+'\n'+result.stderr)
    return result.stdout

def main():
    old = flatten(ROOT/'baseline/manuscript/regional_twin_study.tex')
    new = flatten(ROOT/'regional_twin_study.tex')
    old_tables, new_tables = tables(old), tables(new)
    (ROOT/'internal/latexdiff.log').write_text('')
    output = diff(TABLE.sub('', old), TABLE.sub('', new), 'prose')
    rendered = {}
    for label, table in new_tables.items():
        if label in old_tables:
            wrap = lambda value: '\\documentclass{article}\n\\begin{document}\n'+value+'\n\\end{document}\n'
            compared = diff(wrap(old_tables[label]), wrap(table), label.replace(':','_'))
            body = compared.split(r'\begin{document}',1)[1].split(r'\end{document}',1)[0]
        else:
            # Color at the table scope, not around alignment commands/rows.
            body = table.replace('\\caption{', '\\color{blue}\n\\caption{',1)
        rendered[label] = body
    assert set(rendered)=={'tab:methods','tab:results','tab:alarm_rates','tab:guidance'}
    # Place unchanged and caption-edited tables near the same stable content.
    anchor = 'Regional targets sum valid household readings'
    assert output.count(anchor)==1
    output = output.replace(anchor, rendered['tab:methods']+'\n'+anchor)
    anchor = r'\subsection{RQ2.'
    assert output.count(anchor)==1
    output = output.replace(anchor, rendered['tab:results']+'\n'+anchor)
    anchor = '\\begin{figure*}[!t]\n\\centering\\includegraphics[width=\\textwidth]{figures/transparent_episode.pdf}'
    assert output.count(anchor)==1
    output = output.replace(anchor,rendered['tab:alarm_rates']+'\n'+rendered['tab:guidance']+'\n'+anchor)
    # Diff pagination differs; use normal IEEE flow instead of clean-paper balancing.
    output = output.replace(r'\balance','')
    # latexdiff normally uses the new preamble without marking author changes.
    output = output.replace(r'\IEEEauthorblockN{James H. Korris}',
                            r'\IEEEauthorblockN{\textcolor{blue}{James H. Korris}}')
    for added_line in ['Creative Technologies Inc.', 'Hollywood, CA, USA', 'james.korris@cretecinc.com']:
        output = output.replace(added_line, r'\textcolor{blue}{'+added_line+'}')
    (ROOT/'regional_twin_study_diff.tex').write_text(output)

if __name__=='__main__':
    main()
