IoTBDS 2027 anonymous Regular Paper preparation

Submission PDF: paper.pdf
Main editable source: paper.tex
Internal comparison (DO NOT SUBMIT): paper_diff.pdf / paper_diff.tex
Requirements, provenance, counts and remaining issues: CONVERSION_REPORT.md

BUILD THE SUBMISSION PDF
  cd iot-entropy/manuscript_iotbds
  bash build.sh

Requires a normal TeX Live installation with pdflatex, BibTeX, latexmk,
newtxtext/newtxmath, T1 font support, booktabs, graphicx, microtype and hyperref.
The unmodified official llncs.cls and splncs04.bst are supplied locally.
Auxiliary build files stay in internal/build/final; paper.pdf is copied here.
The source manuscript directory is never a build output or input dependency.

REBUILD THE INTERNAL COMPARISON
  bash build_review.sh

Requires latexdiff and its ulem/color support in addition to the above.
The frozen equal-layout baseline is internal/baseline/paper_baseline.tex.
internal/make_diff.py runs:
  latexdiff --type=UNDERLINE --graphics-markup=none \
    internal/baseline/paper_baseline.tex paper.tex
It retains the raw result and moves the front-matter comparison into an
explicit appendix, where all removed identities and metadata are marked.
Do not submit the diff, baseline, original-source snapshot, or restoration note.

CHECK PRESERVATION AND RECOUNT
  python3 internal/preservation/verify.py
  python3 internal/audit_pdf.py

The audit uses pdftotext and PyMuPDF, locally installed in internal/python.
For a fresh environment, install without touching the system Python:
  python3 -m pip install --target internal/python --no-cache-dir PyMuPDF==1.24.11
The preservation check also reads the original sibling manuscript to verify
it remains unchanged; this check is not a dependency of the paper build.
Audit evidence and reproducible counting details are in internal/validation/.

RECREATE THE CONVERSION AND RECORDED EDITORIAL REVISION
  python3 internal/convert.py

This OVERWRITES paper.tex and the equal-layout baseline, using only the frozen
snapshot in internal/provenance/, internal/figure-layout.json and the explicit
user-requested edits in internal/editorial-changes.json. The comparison baseline
retains the original wording; editorial changes apply only to paper.tex. Use this
only to reproduce this conversion, not after making new manuscript edits.
Neither ordinary build script invokes it.

RECREATE THE SUBMISSION-ONLY BUNDLE
  python3 internal/package_submission.py

The directory submission/ and submission_source.zip contain only anonymous
submission files and build instructions. No internal review material or logs
are included. See the report's unresolved policy points before submission.

All work is local. Nothing has been submitted, published, committed or pushed.
