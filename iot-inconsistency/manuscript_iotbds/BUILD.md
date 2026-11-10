# Build the anonymous IoTBDS manuscript

From the repository root:

```bash
cd iot-inconsistency/manuscript_iotbds
bash build.sh
```

The exact compilation command is:

```bash
latexmk -pdf -jobname=paper -interaction=nonstopmode -halt-on-error \
  -outdir=build/final main.tex
cp build/final/paper.pdf paper.pdf
```

`latexmk` invokes pdfLaTeX, BibTeX and the necessary repeated pdfLaTeX passes.
All manuscript inputs are local: `main.tex`, `references.bib`, `llncs.cls`,
`splncs04.bst` and the six PDFs in `figures/graph_flow/`. No original-paper,
other-project, dataset, experiment or generator dependency is used.

Use a normal TeX Live installation with `latexmk`, pdfLaTeX, BibTeX, T1 font
support, `newtxtext`, `newtxmath`, `booktabs`, `graphicx`, `microtype`, `url`,
`hyperref`, and the standard packages required by LNCS. The official class and
bibliography style are supplied unchanged. Temporary files stay in `build/`.

## Internal review PDF

```bash
bash build_review.sh
```

This builds `review/baseline/main_baseline.tex`, then runs:

```bash
latexdiff --type=UNDERLINE --graphics-markup=none \
  review/baseline/main_baseline.tex main.tex
```

`internal/make_diff.py` retains the raw output, moves unsafe front-matter
comparisons to an explicit appendix, labels the artifact on its first page,
and writes both plain-text source diffs. The generated source is
`review/paper_diff.tex`; the output is **`review/paper_diff.pdf`**.
The diff needs `latexdiff`, `ulem` and `color` in addition to the normal build.
It may contain author identities and must not be submitted.

## Verification and counting

```bash
python3 internal/content-review/verify.py
python3 internal/audit_pdf.py
```

The first command checks original/baseline/final wording, mathematical content,
numerical macros, keyed table cells, bibliography, original-paper hashes and
protected repository files. Its original-source reads are verification-only;
they are not manuscript build dependencies.

The PDF audit uses `pdftotext` and PyMuPDF. The local tool installation is in
`internal/python/`; recreate it if needed:

```bash
python3 -m pip install --target internal/python --no-cache-dir PyMuPDF==1.24.11
```

The rendered character estimate and anonymity evidence are written to
`internal/validation/`. Both PDFs were also rendered and visually inspected;
an automated text audit does not replace that inspection.

## Reproduce the recorded conversion

```bash
python3 internal/convert.py --final
```

This **overwrites** the baseline and `main.tex` using the frozen current-local
source snapshot, the figure-layout plan and explicit editorial-change list.
Do not run it over later manual edits without preserving them first. Ordinary
build commands do not invoke it. No manuscript or experiment generator from
the original project is run.

## Submission-only bundle

```bash
python3 internal/package_submission.py
```

This refreshes `submission/` and `submission_source.zip` from an explicit
anonymous allowlist. They exclude all review files, baselines, restoration
notes, logs, source provenance and local audit tools. Read the report's
remaining policy notes before submitting.
