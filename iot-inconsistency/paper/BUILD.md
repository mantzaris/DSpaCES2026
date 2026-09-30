# Paper build

The workshop accepts full papers up to 10 pages including references, in IEEE two-column format. The official page was checked on 2026-09-30 and lists an October 15 submission deadline and a December 14 online workshop. No submission is authorized. The checked workshop and submission pages did not specify an anonymity rule or deadline timezone. Verify those details before the user submits.

Sources

- https://sites.google.com/unisalento.it/ieee-dspaces-2026/home
- https://wi-lab.com/cyberchair/2026/bigdata26/scripts/submit.php?subarea=S53&undisplay_detail=1&wh=/cyberchair/2026/bigdata26/scripts/ws_submit.php

The author line uses the author's existing adjacent manuscript for identity and affiliation. It does not reuse that project's results or prose.

The results generator must require complete primary, ablation and native result artifacts. It must not substitute illustrative or pilot numbers for final performance. Compile with `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` from this directory after generating all figures and tables. Inspect every rendered page and record the final page count and warnings.
