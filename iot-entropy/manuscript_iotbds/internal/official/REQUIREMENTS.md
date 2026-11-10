# Official requirements verification

Retrieved **2026-11-10** (UTC; exact timestamps, URLs, redirects and SHA-256 checksums in `retrievals.json`). All required resources and linked template/instructions were accessible. The web reader cannot display ZIP archives; direct HTTPS download of the official archive succeeded. No organizers were contacted.

## Conference requirements

- [Submission Guidelines](https://iotbds.scitevents.org/Guidelines.aspx): choose a **Regular Paper** for completed, validated research. Initial PDF: **10,000–50,000 characters excluding whitespace**, including references, tables, graphs and appendices. Double-blind review; remove identifying author details and acknowledgments. Initial length is a character criterion, not an IEEE page limit. After acceptance, Regular Papers classified Full have **25 proceedings pages**; those classified Short have **20**. Up to four paid extra pages are mentioned but not needed as an intended target here. The page total includes all material in the prescribed layout. The review-period policy bars public posting from initial submission until final decisions; it does not expressly resolve already-public versions. AI-generated-text sections require citations to the AI system, alongside disclosure.
- [Templates](https://iotbds.scitevents.org/Templates.aspx): the linked Springer template is strongly advised for review and mandatory for camera-ready publication. The page does not link an IEEE or legacy SCITEPRESS style.
- [Call for Papers](https://iotbds.scitevents.org/CallForPapers.aspx): independently confirms Regular Papers as completed research, double-blind review, Springer proceedings and CCIS indexing context. The regular-paper deadline shown is **17 November 2026**, with notification 15 January 2027. Abstracts are a separate track and are not the requested deliverable. The paper's sensor-network and fault-detection scope falls within the listed areas.
- [AI Tools](https://iotbds.scitevents.org/AiTools.aspx): name the tool, identify affected parts and explain its use; authors retain accountability. The page initially requires acknowledgment placement but subsequently allows an appropriate section. This conflicts with removal of acknowledgments for double-blind review in Guidelines. A separately headed, nonidentifying AI disclosure preserves transparency without identifying acknowledgments; this is a reasoned resolution, not explicit conference approval. Existing disclosure supplies roles but not a section-by-section map. Do not invent that map or tool/model details.

## Official template provenance

The conference Templates page's link is:

<https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines>

It redirects to [Springer Information for authors and editors](https://link.springer.com/series/558/information-for-authors-and-editors), which expressly covers **CCIS** alongside LNCS and other computer-science series.

Downloaded from the exact links on that page:

- [LaTeX2e Proceedings Template ZIP](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27851904/data/LaTeX2e%20Proceedings%20Template%20ZIP), saved as `latex-proceedings-template.zip`, SHA-256 `42afb32ed4fadc9e209134ec65dab1bd2a7ead42f9a3f8abb184f250c4a197b9`.
- [Instructions for Authors PDF](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27852130/data/Instructions%20for%20Authors%20PDF), saved as `instructions-for-authors.pdf`, SHA-256 `b6a56391a68e64c06d2d9f4173f5260d123a3277eb9cd1a36d0e74b4702ca385`.

The archive is extracted intact into `template/`; per-file hashes are in `template-files.json`. It contains `llncs.cls` **v2.25, 3 September 2026**, `splncs04.bst`, `samplepaper.tex`, `llncsdoc.pdf`, `samplepaper.pdf`, `readme.txt`, `history.txt`, `fig1.eps` and `DescriptionTexts.txt`.

The sample and class documentation prescribe **`splncs04`**; this is the actual supplied bibliography style. The separate publisher instructions use the broader style name MathPhySci; using the archive's explicitly prescribed `splncs04` resolves that terminology difference. The sample uses T1 encoding plus **`newtxtext` and `newtxmath` with `varvw`**; the 2026 sample differs from older LNCS examples. The class supplies proposition/proof environments and standard title/author/institute/keywords commands. No dedicated anonymous option is provided. Anonymous front matter can use the standard commands with anonymous/empty fields, no author-running head and empty PDF author metadata.

The unmodified class fixes a 122 × 193 mm text area. The template warns against layout/font/spacing overrides. Figure captions go below figures and table captions above tables; vector illustrations are preferred. Its sample requests a 150–250-word abstract. New accessibility support offers `\Description{...}` for figures; publication alt text may also be coordinated at proof stage. Publication instructions require an interests disclosure; none should be invented from absent information. Named authors, affiliations, ORCIDs, signatures, copyright lines, volume/page identifiers and camera-ready obligations must not be mistaken for anonymous-review front matter.

## Remaining policy issues for authors

1. **Already-public source:** PDF anonymization cannot remove public discoverability. No action on repository visibility or original files is authorized or performed. Whether the pre-existing public copy is acceptable under review-period policy remains unresolved.
2. **AI disclosure specificity:** preserve the known OpenAI Codex assistance for implementation, experiment orchestration and manuscript draft editing. The source does not identify exact AI-generated-text sections or model/version. Section-specific citation/disclosure compliance requires author knowledge; do not infer facts.
3. **Interests disclosure:** the current Springer publication instructions require a factual declaration. Source author information is insufficient to assert no competing interests. Authors should supply an appropriate statement before final publication (and before review if the submission form requires it).
