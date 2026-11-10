# Official requirements rechecked for the graph-flow submission

Access date: **10 November 2026**. Fresh official-page and template downloads are archived here; URLs, redirects, UTC times, HTTP status and SHA-256 checksums are in `retrievals.json`. No organizer was contacted.

## Initial submission and later publication

- [IoTBDS Guidelines](https://iotbds.scitevents.org/Guidelines.aspx): initial **Regular Papers** are completed and validated research, submitted anonymously for double-blind review. The limit is **10,000–50,000 characters excluding whitespace**, including references, tables, graphs and appendices. It is not an initial 10-page or 20-page rule. After acceptance, Full/Short classifications receive **25/20 proceedings pages**; up to four paid extra pages are mentioned, but need not be assumed here. Names, affiliations and identifying acknowledgments must be removed. New public posting is prohibited while under review, from submission to final selection; the page does not expressly settle pre-existing public copies.
- [Call for Papers](https://iotbds.scitevents.org/CallForPapers.aspx): confirms completed-research Regular Papers, double-blind evaluation and Springer publication. The current regular deadline shown is 17 November 2026. Position papers and abstracts are separate categories, not the requested target.
- [Templates](https://iotbds.scitevents.org/Templates.aspx): use of the linked template is strongly advised for review and mandatory for camera-ready publication. The conference links Springer computer-science proceedings formatting.

## Exact template route and files

The conference link is <https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines>, redirecting to [Springer Information for authors and editors](https://link.springer.com/series/558/information-for-authors-and-editors), which explicitly includes CCIS.

Fresh downloads from that page:

- [LaTeX2e Proceedings Template ZIP](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27851904/data/LaTeX2e%20Proceedings%20Template%20ZIP), SHA-256 `42afb32ed4fadc9e209134ec65dab1bd2a7ead42f9a3f8abb184f250c4a197b9`.
- [Instructions for Authors PDF](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27852130/data/Instructions%20for%20Authors%20PDF), SHA-256 `b6a56391a68e64c06d2d9f4173f5260d123a3277eb9cd1a36d0e74b4702ca385`.

The ZIP is extracted intact into `template/`. Its class is **`llncs.cls` v2.25, 2026-09-03**, SHA-256 `04ec99046ad9867f6cd54ffd1ef8c47c767b327d1baec77536db0528cd492fa2`. The prescribed bibliography style is **`splncs04.bst`**, SHA-256 `f36c3a17e5304a692706359aafa9de709395a085e579eb47c027095aeaa35174`. The readme, sample and class documentation explicitly prescribe this style; the separate PDF calls the broad style MathPhySci. Per-file hashes are in `template-files.json`.

Every fresh resource matches the earlier verified infrastructure in `iot-entropy/manuscript_iotbds/internal/official/` byte-for-byte. That directory was read only; no scientific text or results from the entropy paper were copied.

The current sample uses T1 encoding, `newtxtext` and `newtxmath[varvw]`; class documentation says not to load `amsmath` separately with `newtxmath`. The class fixes the 122 × 193 mm text area and supplies native front matter and theorem/proof structures. There is no dedicated anonymous class option. The sample requests a 150–250-word abstract. Publisher instructions specify at least 6 pt figure lettering, editable equations/tables, captions below figures and above tables. They permit publication-stage alt-text preparation by the chairs/typesetters, and require a factual competing-interests declaration for publication. Neither an interests statement nor publication identifiers should be invented.

## AI disclosure and anonymity

[AI Tools](https://iotbds.scitevents.org/AiTools.aspx) asks authors to name the tool, identify assisted parts and explain use. It initially names acknowledgments, then permits an appropriate section. Guidelines separately requires citation to the system in sections using AI-generated text and removal of identifying acknowledgments. A nonidentifying `AI disclosure` section is a reasoned reconciliation, not explicit organizer approval.

The graph-flow source records OpenAI Codex assistance with software development and grammar checking; it does not identify which earlier sections contained generated text. Preserve those supported roles, add only the current conversion/proofreading work actually performed, and do not invent a model version, assistance history or completed human verification. An official tool footnote is supported by [OpenAI's Codex page](https://openai.com/codex/), successfully read via the web tool on 2026-11-10. Direct archival download returned HTTP 403; that limitation and the successful web retrieval are in `tool-attribution-retrieval.json`.

Authors must resolve any unknown earlier AI-generated-text section mapping before claiming complete section-specific compliance. Pre-existing public-copy eligibility remains separate from anonymizing this PDF. No visibility changes, public posting or organizer contact occurred.
