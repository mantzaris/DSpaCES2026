# Paper build

The current `main.tex` contains the complete graph-flow manuscript, including
all tables, numerical macros and the bibliography. Compile from this directory

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

This produces `main.pdf`. Keep `IEEEtran.cls` and `figures/` alongside the source.
No separate LaTeX fragments, `.bib` files, BibTeX run or Python generation step
is needed to compile. A clean build with only the main source, class and figure
files is recorded in `../results/graph_flow_v1/single_tex_build.json`.

To regenerate figures and numerical content from saved evidence, run
`python3 scripts/figures_graph_flow.py` and
`python3 scripts/make_graph_flow_paper.py` from the project root, then compile.
The latter refreshes the marked generated sections inside `main.tex` and their
hash ledger. Separate generated fragments and bibliography sources remain as
provenance, not compilation dependencies. Edit reference entries directly in
the embedded `thebibliography` environment when revising the manuscript.
The compiled PDF has ten pages including references. Source/figure hashes and
visual inspection are recorded in `results/graph_flow_v1/completion.json`.
The exact former paper is in `legacy/witness_20260930.tar.xz`. Legacy generators
write the main paths and must only run in an isolated copy of that archive.

The workshop accepts full papers up to 10 pages including references, in IEEE two-column format. The official page was checked on 2026-09-30 and lists an October 15 submission deadline and a December 14 online workshop. No submission is authorized. The checked workshop and submission pages did not specify an anonymity rule or deadline timezone. Verify those details before the user submits.

Sources

- https://sites.google.com/unisalento.it/ieee-dspaces-2026/home
- https://wi-lab.com/cyberchair/2026/bigdata26/scripts/submit.php?subarea=S53&undisplay_detail=1&wh=/cyberchair/2026/bigdata26/scripts/ws_submit.php

The author line uses the author's existing adjacent manuscript for identity and affiliation. It does not reuse that project's results or prose.

The results generator must require complete primary, ablation and native result artifacts. It must not substitute illustrative or pilot numbers for final performance. Inspect changed rendered pages and record the final page count and warnings.
