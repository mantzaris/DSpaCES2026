#!/usr/bin/env python3
"""Independent semantic checks against the captured local manuscript.

Runs without third-party Python packages. Output is internal review evidence;
it is not a test of the experiment code or an assertion about research validity.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import difflib

HERE = Path(__file__).resolve().parent
DEST = HERE.parents[1]
SOURCE = DEST.parent / 'manuscript'
original = (DEST / 'internal/provenance/original-paper.tex').read_text()
converted = (DEST / 'paper.tex').read_text()
baseline = (DEST / 'internal/baseline/paper_baseline.tex').read_text()

# This explicit allowlist is independent of the conversion script. It encodes
# the user's follow-up request, not a general normalization of editorial text.
BODY_REPLACEMENTS = [
    ('homogeneous clusting', 'homogeneous clustering'),
    ('make recall nonmonotonically', 'make recall nonmonotonic'),
    ('Computation time is measured as a different source',
     'Computation time is reported separately'),
]
ABSTRACT_REPLACEMENT = (
    'The findings set complementary measurement capabilities',
    'The findings characterize complementary measurement capabilities',
)
ABSTRACT_ADDITION = (
    'Adding entropy to conventional features yields limited incremental benefit, '
    'and neither entropy nor the evaluated diffusion reference provides a '
    'consistent overall advantage.'
)


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()


def command_arg(text, command):
    match = re.search(r'\\' + re.escape(command) + r'\{', text)
    start = match.end()
    depth = 1
    for i in range(start, len(text)):
        if text[i] == '{' and text[i-1] != '\\':
            depth += 1
        elif text[i] == '}' and text[i-1] != '\\':
            depth -= 1
            if depth == 0:
                return text[start:i]
    raise ValueError('Unbalanced command ' + command)


def table(text, label):
    for match in re.finditer(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', text, re.S):
        if '\\label{' + label + '}' in match[0]:
            return match[0]
    raise ValueError('Missing table: ' + label)


def row_cells(text):
    result = []
    for row in text.splitlines():
        if re.match(r'\s*(?:Block|Diffusion|Synthetic|Intel Lab|PEMS-BAY)\s*&', row):
            result.append([cell.strip() for cell in row.strip().rstrip('\\').split('&')])
    return result


def main_table(text):
    result = {}
    chunks = re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}', table(text, 'tab:main'), re.S)
    datasets = ['Synthetic (three sizes)', 'Intel Lab', 'PEMS-BAY']
    metrics = ['P', 'R', 'AP', 'IoU']
    if len(chunks) == 1:
        for row in row_cells(chunks[0]):
            assert len(row) == 14
            for i, dataset in enumerate(datasets):
                for j, metric in enumerate(metrics):
                    result[(dataset, row[0], row[1], metric)] = row[2+4*i+j]
    else:
        assert len(chunks) == 3
        for chunk in chunks:
            dataset = next(x for x in datasets if '{' + x + '}' in chunk)
            for row in row_cells(chunk):
                assert len(row) == 6
                for j, metric in enumerate(metrics):
                    result[(dataset, row[0], row[1], metric)] = row[2+j]
    assert len(result) == 120
    return result


def fidelity_table(text):
    result = {}
    chunks = re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}', table(text, 'tab:fidelity'), re.S)
    for chunk in chunks:
        header = re.search(r'Dataset&Reference&(.*?)\\\\', chunk)[1].split('&')
        for row in row_cells(chunk):
            assert len(row) == len(header) + 2
            for metric, value in zip(header, row[2:]):
                result[(row[0], row[1], metric)] = value
    assert len(result) == 48
    return result


def scientific_body(text):
    text = text[text.index(r'\section{Introduction}'):text.index(r'\section*{')]
    # Each table's data are compared by semantic coordinates separately.
    text = re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}', '', text, flags=re.S)
    # Figure content is checked through its unchanged asset hash. Caption text
    # remains in this comparison. Layout may rotate or crop existing panels.
    text = re.sub(r'\\begin\{figure\*?\}(?:\[[^]]*\])?.*?(?=\\caption\{)', '', text, flags=re.S)
    text = re.sub(r'\\(?:begin|end)\{(?:figure|table)\*?\}(?:\[[^]]*\])?', '', text)
    text = re.sub(r'\\(?:centering|small|par|medskip)\b', '', text)
    text = text.replace(r'\\[-2mm]', r'\\')
    return normalize(text)


def abstract(text):
    value = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.S)[1]
    value = re.sub(r'\\keywords\{.*?\}', '', value, flags=re.S)
    return normalize(value)


def keywords(text):
    if r'\begin{IEEEkeywords}' in text:
        return [x.strip() for x in re.search(r'\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}', text, re.S)[1].split(',')]
    return [x.strip() for x in command_arg(text, 'keywords').split(r'\and')]


def disclosure(text):
    value = text[text.index(r'\section*{'):]
    value = value[value.index('}')+1:]
    value = re.split(r'\\(?:IEEEtriggeratref|bibliographystyle)', value)[0]
    return normalize(value)


def citations(text):
    return [key.strip() for keys in re.findall(r'\\cite\{([^}]+)\}', text) for key in keys.split(',')]


source_body = scientific_body(original)
final_body = scientific_body(converted)
expected_body = source_body
change_occurrences = []
for before, after in BODY_REPLACEMENTS:
    # Word boundaries avoid treating 'nonmonotonic' as an occurrence within
    # the original incorrect word 'nonmonotonically'.
    before_pattern = r'(?<!\w)' + re.escape(before) + r'(?!\w)'
    after_pattern = r'(?<!\w)' + re.escape(after) + r'(?!\w)'
    change_occurrences.append({
        'location': 'scientific body', 'before': before, 'after': after,
        'source_before_occurrences': len(re.findall(before_pattern, source_body)),
        'final_before_occurrences': len(re.findall(before_pattern, final_body)),
        'final_after_occurrences': len(re.findall(after_pattern, final_body)),
    })
    expected_body = re.sub(before_pattern, lambda match: after, expected_body)

source_abstract = abstract(original)
final_abstract = abstract(converted)
expected_abstract_without_addition = source_abstract.replace(*ABSTRACT_REPLACEMENT)
final_abstract_without_addition = normalize(final_abstract.replace(ABSTRACT_ADDITION, '', 1))
change_occurrences.append({
    'location': 'abstract', 'before': ABSTRACT_REPLACEMENT[0],
    'after': ABSTRACT_REPLACEMENT[1],
    'source_before_occurrences': source_abstract.count(ABSTRACT_REPLACEMENT[0]),
    'final_before_occurrences': final_abstract.count(ABSTRACT_REPLACEMENT[0]),
    'final_after_occurrences': final_abstract.count(ABSTRACT_REPLACEMENT[1]),
})

checks = {
    'title_exact': command_arg(original, 'title') == command_arg(converted, 'title'),
    'four_requested_replacements_each_occur_exactly_once': all(
        row['source_before_occurrences'] == 1 and row['final_before_occurrences'] == 0
        and row['final_after_occurrences'] == 1 for row in change_occurrences),
    'requested_abstract_sentence_added_exactly_once': (
        source_abstract.count(ABSTRACT_ADDITION) == 0
        and final_abstract.count(ABSTRACT_ADDITION) == 1),
    'remaining_abstract_words_exact': (
        expected_abstract_without_addition == final_abstract_without_addition),
    'keyword_terms_exact': keywords(original) == keywords(converted),
    'scientific_body_and_math_exact_except_three_requested_corrections': expected_body == final_body,
    'comparison_baseline_abstract_preserves_original_wording': source_abstract == abstract(baseline),
    'comparison_baseline_body_preserves_original_wording': source_body == scientific_body(baseline),
    'main_table_120_values_same_semantic_coordinates': main_table(original) == main_table(converted),
    'fidelity_table_48_values_same_semantic_coordinates': fidelity_table(original) == fidelity_table(converted),
    'ai_disclosure_body_exact': disclosure(original) == disclosure(converted),
    'citations_order_and_keys_exact': citations(original) == citations(converted),
    'bibliography_bytes_exact': (SOURCE / 'references.bib').read_bytes() == (DEST / 'references.bib').read_bytes(),
    'local_source_tex_matches_frozen_snapshot': (SOURCE / 'paper.tex').read_bytes() == (DEST / 'internal/provenance/original-paper.tex').read_bytes(),
}
manifest = json.loads((DEST / 'internal/provenance/source-baseline.json').read_text())
actual_source = {str(p.relative_to(SOURCE)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(SOURCE.rglob('*')) if p.is_file()}
checks['all_source_files_and_paths_unchanged'] = manifest['source_files_sha256'] == actual_source
checks['all_six_figure_assets_byte_identical'] = all(
    (SOURCE / 'figures-v2' / p.name).read_bytes() == p.read_bytes()
    for p in (DEST / 'figures-v2').glob('*.pdf'))

result = {
    'checks': checks,
    'all_passed': all(checks.values()),
    'scope': 'Frozen current local source versus anonymous Springer source; no experiment rerun.',
    'expected_wording_changes': [
        'Author names/affiliations/emails replaced by Anonymous Author(s); institute empty.',
        'PDF author metadata cleared.',
        'Acknowledgment and AI disclosure heading changed to AI disclosure.',
        'User-requested four language corrections and one balanced-overall-finding sentence in the abstract.',
    ],
    'authorized_language_replacements': change_occurrences,
    'authorized_abstract_addition': ABSTRACT_ADDITION,
    'layout_only_normalizations': [
        'Springer class/packages, native proposition/proof, keywords, bibliography style.',
        'Float types/placement and figure includegraphics layout.',
        'Main table split by dataset; repeated headers, reference labels and family labels.',
        'Fidelity table split by metric; repeated headers and row labels.',
        'Existing negative equation row spacing removed.',
    ],
    'limitations': 'This verifies TeX wording and values; rendered glyphs, clipping, PDF anonymity, and diff visibility require separate PDF inspection.',
    'source_sha256': hashlib.sha256(original.encode()).hexdigest(),
    'converted_sha256': hashlib.sha256(converted.encode()).hexdigest(),
}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
if not checks['scientific_body_and_math_exact_except_three_requested_corrections']:
    (HERE / 'unexpected-body.diff').write_text('\n'.join(difflib.unified_diff(
        expected_body.split(), final_body.split(), fromfile='expected-authorized-body', tofile='converted')))
if not checks['remaining_abstract_words_exact']:
    (HERE / 'unexpected-abstract.diff').write_text('\n'.join(difflib.unified_diff(
        expected_abstract_without_addition.split(), final_abstract_without_addition.split(),
        fromfile='expected-authorized-abstract', tofile='converted-with-requested-sentence-removed')))
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
