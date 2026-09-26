# Venue and primary-source verification

Checked September 23, 2026 in the project timezone; final document preparation
continues September 24 UTC. These are internal review notes, not submission actions.

## Editorial refresh, September 24, 2026

The [official workshop page](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home)
was retrieved again. It still explicitly welcomes case studies, limits full papers
to ten pages including references, and requires IEEE two-column proceedings format.
The December 14 online meeting, October 15 submission date and provisional waiver
language are unchanged. No newly established presentation or anonymity rule was
found. The existing template and full-paper format are retained. This refresh
was limited to the workshop instructions, not a new venue/literature search.

## Venue

- [Official DSpaCES workshop page](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home): fourth workshop, co-located with IEEE Big Data 2026; December 14, fully online on Zoom. Original research, positions and case studies are welcomed. Full papers: ten pages including references; short/position: five. IEEE two-column conference formatting.
- [Workshop-specific CyberChair portal](https://wi-lab.com/cyberchair/2026/bigdata26/scripts/submit.php?subarea=S53&undisplay_detail=1&wh=/cyberchair/2026/bigdata26/scripts/ws_submit.php): October 15, 2026, 23:59 AoE, equivalent to October 16, 11:59 UTC. This is S53, not the main research track. Direct retrieval initially failed; following the official workshop link succeeded.
- The workshop lists notification November 5, camera-ready November 20, author registration November 26. Its possible waiver is expected, not confirmed. The linked [Cvent author-information page](https://web.cvent.com/event/ea01f8b2-6760-4c81-babc-4c44cc93aeb9/websitePage:8a02ffa9-1a19-43d5-a7f1-9a9e99197482) was readable this time and requires one full author registration per accepted paper. No payment or registration was made.
- Live/prerecorded presentation requirements, duration, no-show consequences, anonymity and acceptance of external supplements were not established from the retrieved workshop instructions. Do not infer that acceptance alone guarantees publication. The manuscript uses the author block explicitly supplied by the user and has no separate supplementary PDF needed to follow its argument.
- The linked [official IEEE template page](https://www.ieee.org/conferences/publishing/templates.html) was blocked to automated retrieval. An [IEEE-hosted template guidance mirror](https://cai.ieee.org/2025/manuscript-templates-for-conference-proceedings/) explicitly directs authors to IEEEtran conference mode and CTAN instructions. The direct IEEE ZIP response was not a ZIP. The documented class and bibliography style were retrieved unmodified from [CTAN IEEEtran](https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip). Versions: class 1.8b, style 1.14. Hashes are in `template_source.json`; copyright/license notices remain intact. No template font, margin, spacing or column override is used.

The full ten-page case-study format is chosen because the model/interface distinctions,
three short mathematical explanations, separate cohorts and action diagnosis all need
to stand alone. This is one author-review draft, not a submission or a novelty certificate.

## Closest work and checked claims

The earlier complete audits remain in `docs/REGIONAL_REFINEMENT_NOVELTY_AUDIT.md`
and `docs/REGIONAL_SHOCK_STUDY_PROTOCOL.md`. The table records what supports this
manuscript, not a claim that every related paper was reproduced.

| Bibliography key / primary version | Checked material and permitted use | Limit and comparison |
|---|---|---|
| `katzfuss2017`: [author v2](https://arxiv.org/pdf/1507.04789), [JASA record](https://doi.org/10.1080/01621459.2015.1123632) | Earlier full-text audit, Sections 2.2-2.5 and 3.1-3.6: multiresolution basis inference and conditional structure. Published 2017, 112(517), 201-214. | Standard multiresolution uncertainty; not evidence that our eviction implementation is new. |
| `mrf`: [full v2 HTML](https://arxiv.org/html/1810.04200v2), [JCGS DOI](https://doi.org/10.1080/10618600.2021.1886938) | Sections 2-4, especially 4.1: forecast-covariance approximation and identified exact cases. Publication 2021, 30(4), 1095-1110. | Their spatial filtering scalability depends on structure; our exactness concerns a smaller fixed model. |
| `vecchia`: [full v2](https://arxiv.org/html/2006.16901v2), [published DOI](https://doi.org/10.1007/s11222-021-10077-9) | Earlier Propositions 1-4 and current Sections 4-5: sparse factors under hierarchical conditional assumptions. Statistics and Computing 32, article 15, 2022. | Does not imply arbitrary local updates in a coupled Gaussian model. |
| `distributed`: [full author paper](https://arxiv.org/abs/1402.1472), [published DOI](https://doi.org/10.1007/s11222-016-9627-4) | Algorithm 1 and temporal extension inspected in earlier audit; publication 27, 363-375, 2017. Exact inference relative to low-rank/private model. | Closest implemented mathematical comparator, not a full reproduction of its application. |
| `isam`: [author record and full PDF](https://www.cs.cmu.edu/~kaess/pub/Kaess12ijrr.html) | Author bibliography checked; earlier full-text Sections 3, Algorithms 4/6 and 5.2. IJRR 31(2), 216-235, 2012. | Conditional reuse is established. Our star-message implementation is not an iSAM2 reproduction or sparse nonlinear solver. |
| `mint`: [author record](https://robjhyndman.com/publications/mint/), [full paper](https://robjhyndman.com/papers/mint.pdf) | Author publication metadata and earlier Theorem 1/Sections 2-3: coherent forecasts with covariance/unbiasedness assumptions. JASA 114(526), 804-819, 2019. | Forecast reconciliation does not itself supply observation acquisition/retraction. |
| `sun`: [full proceedings PDF](https://lab-work.github.io/download/SunWork2017.pdf), [author publication list](https://lab-work.github.io/publications/) | PDF pp. 2533-2540, Sections II-III: threshold scheduling, nontransmission information, synthetic-measurement approximate estimator. ECC **2016**, despite filename 2017. | Our working window posterior does not model all implicit scheduling information. |
| `han`: [full journal PDF](https://eesling.home.ece.ust.hk/papers/j/j37.pdf) | Title page, introduction and schedule/filter assumptions: particular stochastic rules preserve Gaussian estimation; deterministic events generally do not. TAC 60(10), 2661-2675, 2015, DOI verified in PDF. | No guarantee transfers to the heuristic score used here. |
| `controlled`: [full journal PDF](https://www.ssp.ece.upatras.gr/moustakides/downloads/journals/seq2024_1.pdf) | Sections II-IV: finite actions/parameters, specified densities, Lorden criterion and asymptotic false-alarm regime. JSAIT 5, 1-11, 2024. | Stronger sensing theory, different assumptions. Not an implemented equal-access baseline; no superiority claim to it. |
| `he`: [final publisher PDF](https://www.nature.com/articles/s41598-026-54639-1.pdf) | Full typeset source now accessible, unlike earlier HTML attempts. Title-page authors, Sections 2-4, participant time-slot features and localization rule checked. Scientific Reports 16, 26384, 2026. | Input already includes participant detail; not a limited-access aggregate-only comparator. This updates the earlier accepted-manuscript-only access limitation. |
| `london`: [originating catalog](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d) | Half-hour kWh, approximate population, two duplicate representations and attribution terms checked. Exact local counts come from our saved ingestion manifest, not catalog approximations. | Current rendered page says Creative Commons Attribution; the execution source manifest records CC BY 4.0 and its URL. No raw data redistribution is needed. |
| `hespanha`: [author book record](https://web.ece.ucsb.edu/~hespanha/linearsystems/), second-edition index | Title, author, second edition, Princeton University Press, 2018 and observability coverage verified. | Full book not retrieved. Cited to attribute standard terminology; the finite-horizon coupling proof is written out, not claimed audited from an inaccessible theorem. |

The failed large-PDF web fetch for Särkkä and Svensson's 2023 book is not treated
as a full-text audit. The paper attributes Gaussian elimination to the inspected
distributed/incremental primary literature and supplies self-contained proofs.
Observability is standard linear systems mathematics; the displayed coupling
argument is an explanatory specialization, not an originality claim.

## Distinct scope

The available adjacent BDCC plan, `../EAI-BDCC2026/research_plan/EAI_BDCC_2026_Research_Plan.md`,
concerns traffic graph aggregation, structural-defect enclosures, Matheron
reconstruction and selective simulation. This paper uses none of its data,
results, graph certificates or Monte Carlo allocation claims. Its scope is
Gaussian query preservation, legal observation access and acquisition behaviour
on a London household replay. Generic probability identities do not establish
either project's novelty.
