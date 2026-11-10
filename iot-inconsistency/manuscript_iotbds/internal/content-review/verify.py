#!/usr/bin/env python3
"""Independent preservation checks for the local IoT graph-flow conversion.

Run from any directory. Checks actual source fields, equations and table
coordinates, rather than re-running the converter. Never invokes generators.
"""
from pathlib import Path
from collections import Counter
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = ROOT.parents[1]
SOURCE = ROOT.parent / 'paper'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    text = text.replace(r'\allowbreak', '')
    return re.sub(r'\s+', ' ', text).strip()


def group(text, start):
    """Balanced brace contents and offset after closing brace."""
    assert text[start] == '{'
    depth = 1
    i = start + 1
    while i < len(text):
        if text[i] == '{' and text[i-1] != '\\':
            depth += 1
        elif text[i] == '}' and text[i-1] != '\\':
            depth -= 1
            if not depth:
                return text[start+1:i], i+1
        i += 1
    raise ValueError('Unbalanced brace')


def command_args(text, command):
    out = []
    for match in re.finditer(r'\\' + re.escape(command) + r'(?:\[[^]]*\])?\s*\{', text):
        out.append(group(text, match.end()-1)[0])
    return out


def document_body(text):
    text = text.split(r'\begin{document}', 1)[1]
    text = re.split(r'\\(?:bibliographystyle|begin\{thebibliography\})', text, 1)[0]
    text = re.sub(r'(?m)^\s*%.*$', '', text)
    # All float text is compared separately, including every table cell and
    # the complete original captions. Float commands and panels may move.
    text = re.sub(r'\\begin\{(?:figure|table)\*?\}.*?\\end\{(?:figure|table)\*?\}', '', text, flags=re.S)
    # Keywords change their wrapper only; terms are checked separately.
    text = re.sub(r'\\begin\{IEEEkeywords\}.*?\\end\{IEEEkeywords\}', '', text, flags=re.S)
    for value in command_args(text, 'keywords'):
        text = text.replace(r'\keywords{' + value + '}', '')
    # End marker is absent from the split in normal source but normalize it.
    text = text.replace(r'\end{document}', '')
    return norm(text)


def title(text):
    return command_args(text, 'title')[0]


def keywords(text):
    ieee = re.search(r'\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}', text, re.S)
    if ieee:
        return [norm(x) for x in ieee[1].split(',')]
    return [norm(x) for x in command_args(text, 'keywords')[0].split(r'\and')]


def numerical_macros(text):
    out = {}
    block = re.search(r'% BEGIN GENERATED graph_flow/numbers.tex(.*?)% END GENERATED graph_flow/numbers.tex', text, re.S)[1]
    for match in re.finditer(r'\\newcommand\{(\\\w+)\}\s*\{', block):
        out[match[1]] = group(block, match.end()-1)[0]
    return out


def table_map(text):
    result = {}
    for match in re.finditer(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', text, re.S):
        block = match[0]
        label = command_args(block, 'label')[0]
        count_ids = 2 if label == 'tab:repair' else 1
        for tab in re.finditer(r'\\begin\{tabular\}\{', block):
            _, start = group(block, tab.end()-1)
            end = block.index(r'\end{tabular}', start)
            tabtext = block[start:end]
            tabtext = re.sub(r'\\(?:toprule|midrule|bottomrule)\b', '', tabtext)
            rows = [[norm(c) for c in row.split('&')] for row in re.split(r'\\\\', tabtext) if '&' in row]
            header = rows[0]
            for row in rows[1:]:
                assert len(row) == len(header), (label, row, header)
                identity = tuple(row[:count_ids])
                for key, value in zip(header[count_ids:], row[count_ids:]):
                    coordinate = (label,) + identity + (key,)
                    assert coordinate not in result, coordinate
                    result[coordinate] = value
    return result


def captions(text):
    return Counter(norm(x) for x in command_args(text, 'caption'))


def equation_map(text):
    out = []
    for match in re.finditer(r'\\begin\{(equation|align)\}(.*?)\\end\{\1\}', text, re.S):
        rows = re.split(r'\\\\', match[2]) if match[1] == 'align' else [match[2]]
        out.extend(norm(row) for row in rows)
    return {'E'+str(i+1): row for i, row in enumerate(out)}


def citations(text):
    text = text.split(r'\begin{document}', 1)[1]
    return [key.strip() for keys in re.findall(r'\\cite\{([^}]+)\}', text) for key in keys.split(',')]


def bib_fields(text):
    out = {}
    for match in re.finditer(r'@([A-Za-z]+)\s*\{\s*([^,]+),', text):
        body, _ = group(text, text.index('{', match.start()))
        body = body.split(',', 1)[1]
        fields = {}
        for field in re.finditer(r'(\w+)\s*=\s*\{', body):
            value, _ = group(body, field.end()-1)
            fields[field[1]] = value
        out[match[2].strip()] = (match[1].lower(), fields)
    return out


def write_diff(name, expected, actual):
    (HERE / name).write_text('\n'.join(difflib.unified_diff(
        expected.split(), actual.split(), fromfile='expected', tofile='actual')) + '\n')


def main():
    original = (ROOT / 'internal/provenance/original-main.tex').read_text()
    baseline = (ROOT / 'review/baseline/main_baseline.tex').read_text()
    final = (ROOT / 'main.tex').read_text()
    edits = json.loads((ROOT / 'internal/editorial-changes.json').read_text())
    expected = original
    edit_occurrences = []
    for edit in edits:
        before_count = expected.count(edit['before'])
        edit_occurrences.append({'location':edit['location'], 'before_occurrences':before_count,
                                 'reason':edit.get('reason', '')})
        if before_count != 1:
            raise AssertionError(('Edit must match once', edit['location'], before_count))
        expected = expected.replace(edit['before'], edit['after'])
    mappings = json.loads((HERE / 'bibliography-mapping.json').read_text())
    bib = bib_fields((ROOT / 'references.bib').read_text())
    frozen_bib = bib_fields((HERE / 'baseline-references.bib').read_text())
    map_ok = all(bib[e['key']] == frozen_bib[e['key']] == (e['bibtex_type'], e['fields'])
                 for e in mappings['entries'])
    base_caption = captions(baseline)
    source_caption = captions(original)
    final_caption = captions(final)
    expected_caption = captions(expected)
    # Original captions must survive exactly. Additional repeated or continued
    # captions are explicit layout aids, listed for human verification below.
    baseline_captions_ok = all(base_caption[c] >= n for c,n in source_caption.items())
    final_captions_ok = all(final_caption[c] >= n for c,n in expected_caption.items())
    baseline_caption_extras = base_caption - source_caption
    final_caption_extras = final_caption - expected_caption
    source_tables, base_tables, final_tables = table_map(original), table_map(baseline), table_map(final)
    expected_tables = table_map(expected)
    eq = equation_map(original)
    checks = {
        'title_unchanged': title(original) == title(baseline) == title(final),
        'keyword_terms_unchanged': keywords(original) == keywords(baseline) == keywords(final),
        'numerical_macros_exact': numerical_macros(original) == numerical_macros(baseline) == numerical_macros(final),
        'baseline_all_nonfloat_wording_and_math_original': document_body(original) == document_body(baseline),
        'final_all_nonfloat_wording_and_math_only_recorded_edits': document_body(expected) == document_body(final),
        'baseline_all_original_captions_retained': baseline_captions_ok,
        'final_all_captions_only_recorded_edits': final_captions_ok,
        'additional_captions_only_shared_continuation_labels': (
            set(baseline_caption_extras).issubset({'Continued.'})
            and final_caption_extras == baseline_caption_extras),
        'baseline_table_cells_and_semantic_coordinates_exact': source_tables == base_tables,
        'final_table_cells_and_semantic_coordinates_exact': source_tables == expected_tables == final_tables,
        'equations_E1_through_E12_exact': len(eq) == 12 and eq == equation_map(baseline) == equation_map(final),
        'E_prefix_and_explicit_E2_E5_E6_references_preserved': all(
            r'\renewcommand{\theequation}{E\arabic{equation}}' in t
            and re.findall(r'\(E\d+\)', t) == ['(E2)', '(E6)', '(E5)'] for t in [original,baseline,final]),
        'all_original_citation_keys_and_order_retained_in_baseline': citations(original) == citations(baseline),
        'final_citations_only_original_and_explicit_recorded_additions': citations(expected) == citations(final),
        'all_19_original_bibliographic_records_exact': map_ok and len(mappings['entries']) == 19,
        'original_local_source_matches_frozen_copy': (SOURCE/'main.tex').read_bytes() == original.encode(),
    }
    source_manifest = json.loads((ROOT/'internal/provenance/source-baseline.json').read_text())
    actual_source = {str(p.relative_to(SOURCE)):sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
    checks['entire_original_paper_directory_unchanged'] = actual_source == source_manifest['source_files_sha256']
    assets = re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', original)
    checks['all_six_original_figure_PDFs_byte_identical'] = len(assets) == 6 and all(
        (SOURCE/p).read_bytes() == (ROOT/p).read_bytes() for p in assets)
    protected = json.loads((ROOT/'internal/provenance/protected-files.json').read_text())
    altered = [name for name,digest in protected.items() if not (REPO/name).is_file() or sha(REPO/name) != digest]
    checks['all_protected_repo_and_entropy_files_unchanged'] = not altered
    if not checks['baseline_all_nonfloat_wording_and_math_original']:
        write_diff('unexpected-baseline.diff', document_body(original), document_body(baseline))
    if not checks['final_all_nonfloat_wording_and_math_only_recorded_edits']:
        write_diff('unexpected-final.diff', document_body(expected), document_body(final))
    result = {
        'all_passed':all(checks.values()), 'checks':checks,
        'numerical_macro_count':len(numerical_macros(original)),
        'table_value_count':len(source_tables), 'equation_count':len(eq),
        'original_caption_count':sum(source_caption.values()),
        'baseline_additional_caption_texts':dict(base_caption-source_caption),
        'final_additional_caption_texts':dict(final_caption-expected_caption),
        'edit_match_evidence':edit_occurrences,
        'bibliography_additional_keys':sorted(set(bib)-set(frozen_bib)),
        'protected_files_count':len(protected), 'altered_protected_files':altered,
        'source_sha256':sha(ROOT/'internal/provenance/original-main.tex'),
        'baseline_sha256':sha(ROOT/'review/baseline/main_baseline.tex'),
        'final_sha256':sha(ROOT/'main.tex'),
        'limitations':'Semantic/source checks supplement PDF rendering and visual review; this does not rerun experiments or validate scientific outcomes.'
    }
    (HERE/'preservation-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['all_passed'] else 1)


if __name__ == '__main__':
    main()
