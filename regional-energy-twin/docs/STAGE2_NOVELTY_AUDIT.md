# Stage 2 novelty audit: event-time candidate rejected for now

Checked September 23, 2026 UTC. **No defensible pivot has been established.**
This is a bounded comparison of the event-time direction in the supplied plan,
not a search for an unrelated replacement topic. The original sketch corollary
remains attributed as in [NOVELTY_AUDIT.md](NOVELTY_AUDIT.md): standard robust
fusion and projection arguments, with a provisional interface synthesis.

The [Stage 1 evidence audit](../reports/STAGE1_EVIDENCE_AUDIT.md) does not reveal
the practically meaningful overconfidence regime needed for the narrow fallback.
The literature below therefore examines the one allowed alternative. A difference
in domain, message fields or implementation is not sufficient novelty.

## Eight closest comparisons

Publication metadata and full-text access are separate. The publisher-deposited
records are retained in [stage2_publication_records.json](../manifests/stage2_publication_records.json).
Downloaded primary PDFs, failed retrieval statuses, hashes and URLs are in
[stage2_literature_access.json](../manifests/stage2_literature_access.json).

| Work and checked publication status | Information assumptions and result inspected | Remaining difference from same-target forecast composition |
|---|---|---|
| **Bar-Shalom, 2002**, *Update with out-of-sequence measurements in tracking: exact solution*. [TAES DOI](https://doi.org/10.1109/TAES.2002.1039398), 38(3), 769–777 according to publisher-deposited metadata | Original full text remains inaccessible (empty IEEE response / blocked stamp request). The primary follow-on [Yoon, Sternberg & Cahoy, 2016](https://dspace.mit.edu/server/api/core/bitstreams/e9b0443a-2053-4b78-973b-5a11b4ef9e15/content), introduction and state/noise equations, describes the earlier exact update within the last sampling interval and develops a fixed-lag extension. No original-proof audit is claimed | OOS measurement updates assume a state model and measurement/covariance information. Black-box forecast messages may lack these. Missing information is an access limitation, not a new exact estimator; the inaccessible original prevents closing this comparison completely |
| **Tian & Bar-Shalom, 2010**, *Algorithms for Asynchronous Track-to-Track Fusion*, JAIF 5(2), 128–138. [Journal full text](https://isif.org/files/isif/2024-01/308_0_art_11_27647.pdf) | Sections 2–3, equations (1)–(7), and conclusions inspected. Two asynchronous trackers, common dynamics/process noise, delayed tracks, specified partial feedback. Exact cross-covariances need local gains and observation matrices at sampling times. The memoryless linear-Gaussian reference is consistent; generalized information-matrix approximations reduce communication with scenario-dependent performance | Already handles derived estimates, asynchronous times, common noise and communication limits. A forecast-only interface would withhold the sufficient information used here. New metadata must demonstrably replace needed information or support a useful empirical tradeoff; timestamps alone do not |
| **Maatouk et al., 2020**, *The Age of Incorrect Information: A New Performance Metric for Status Updates*. [DOI](https://doi.org/10.1109/TNET.2020.3005549), TON 28(5), 2215–2228; [author version](https://arxiv.org/pdf/1907.06604) | Sections II–IV and constrained-policy results inspected. Combines elapsed incorrectness and error, rather than elapsed time alone. An N-state Markov source, unreliable iid channel, instantaneous ACK/NACK and transmission-budget assumptions support its policy analysis | AoII already separates freshness from useful correctness. BDG2 supplies delayed evaluation labels, not online knowledge of true future demand or an observed packet process. A reservation loss is more direct than relabeling consumption errors as AoII; its policy guarantee does not transfer |
| **Shisher, Sun & Hou, 2024**, *Timely Communications for Remote Inference*. [Publisher record](https://ieeexplore.ieee.org/document/10559951), TON 32(5), 3824–3839; [v2 full text](https://arxiv.org/html/2404.16281v2) | Section III, Lemma 2 and Theorems 1–2 characterize age-dependent loss via generalized conditional entropy. Near-Markov assumptions explain near-monotonicity; non-Markov data can violate it. Selection-from-buffer and scheduling sections treat general age penalties under their channel/source assumptions | “Newest is not always best” and task-dependent age penalties are established. Energy forecasts with differing cutoffs could be an application, but require an advantage over a competent learned age-loss rule. Neither a new general age-inflation theorem nor such an advantage is currently available |
| **Girolimetto et al., 2024**, *Cross-temporal probabilistic forecast reconciliation: Methodological and practical issues*. [Published record](https://robjhyndman.com/publications/ctprob.html), IJF 40(3), 1134–1151; [v3 full text](https://arxiv.org/html/2303.17277v3) | Section 3 / Theorem 3.1 reconciles samples into a linearly constrained distribution. Equation (8) transforms Gaussian means/covariances; Section 4 examines structured covariance, multi-step and overlapping residuals. Forecasts at several temporal and cross-sectional aggregation levels must satisfy known linear constraints | Different **target supports** in a temporal hierarchy differ from several cutoffs for one identical hourly target. A cutoff contract supplies no new aggregation identity. Standard reconciliation would need an actual hierarchy and estimated joint errors; inventing one solely to create a novelty gap is unjustified |
| **Neubauer & Filzmoser, 2024 preprint**, *Enhancing Forecasts Using Real-Time Data Flow and Hierarchical Forecast Reconciliation, with Applications to the Energy Sector*. [arXiv v1](https://arxiv.org/html/2411.01528v1), [institutional record](https://repositum.tuwien.at/handle/20.500.12708/208404) | Algorithm 1 updates forecasts, prunes observed parts of a temporal hierarchy, reconciles remaining forecasts and restores observations. Section 3.2 Theorem 1 assumes jointly covariance-stationary base errors; Theorem 2 specializes to an aggregated AR(1)/ARIMA setting. Energy examples inspect updating/reconciliation gains | Real-time partial observations and energy applications already appear here. Its consumer has observations, model updates and a hierarchy. Restricting access to provider forecasts is a different contract, but no theorem or demonstrated benefit follows merely from restricting it. No journal publication was verified; the retrieved records still identify a preprint |
| **Zhang, Sun & Ji, 2025 / April 2026 revision**, *Multimodal Remote Inference*. [Current v3 record](https://arxiv.org/abs/2508.07555), [full v3](https://arxiv.org/pdf/2508.07555v3) | v1 and the newer v3 were retrieved. v3 Sections III–V: stationary signal process, signal-agnostic scheduling, known bounded loss on a finite truncated age-vector space, reliable fixed modality-specific transmission times. Assumption 2 requires an optimal stationary policy visiting every modality indefinitely. Theorems/policy construction extend two-modality threshold scheduling to multiple modalities | Joint, non-additive loss from a vector of ages is already explicitly studied. The initial MASS 2025 version is published; the current record says the extension is submitted to TON, not accepted. This is stronger prior art than comparing only a scalar newest-age heuristic; our task would concern forecast composition rather than scheduling |
| **Shisher et al., 2026**, *AoI-Based Scheduling of Correlated Sources for Timely Inference*. [Journal DOI](https://doi.org/10.1109/TON.2025.3643286), TON 34, 2181–2195; [author v2](https://arxiv.org/abs/2509.01926) | Sections II–V, Assumption 1 and Theorem 1 inspected in the downloaded full text. Multiple correlated signals, jointly stationary target/source laws, signal-agnostic scheduling, and reliable one-slot delivery. Age-vector loss is nonseparable; approximation bounds and known/unknown-penalty scheduling methods are developed | Correlation plus heterogeneous ages is not an unoccupied combination. Forecast-only metadata differs from source observations, but the required claim would be a demonstrable prediction/decision benefit under that boundary. This audit found no justified new guarantee that bypasses missing joint information |

These are statements of each work's scope, not endorsements of every proof or
empirical claim. In particular, covariance stationarity, known age-loss functions
and state-space assumptions do not automatically hold for building meters.

## Additional current-record checks and access limits

The bounded search also located [Xue et al., *Communication-Efficient Asynchronous
Fusion for Multi-Radar Systems via State and Covariance Projection*, Electronics
15(2), 458, January 2026](https://www.mdpi.com/2079-9292/15/2/458).
The indexed publisher text describes compact state/covariance/timestamp messages,
projection to a common reference time, and inverse-covariance fusion with an
approximate independence assumption. Its [version record](https://www.mdpi.com/2079-9292/15/2/458/notes)
was accessible, but direct HTML/XML/PDF retrieval failed (PDF 403). This is a
relevant lead, **not a fully audited proof**. Its stated comparison with single
radars would not establish our proposed advantage over strong equal-access
age-aware fusion. The eight-work table already suffices to reject a broad
“timestamps plus alignment” novelty claim without relying on this source.

The original Bar-Shalom PDF remains blocked. The accessible Yoon et al. paper
supports the OOSM context but does not substitute for auditing the original exact
solution. Original sketch-audit access gaps (Ajgl–Straka, original CI, parts of
the early data-incest literature) also remain. They limit positive novelty claims;
they are not evidence that a gap exists.

Searches used the supplied exact titles, asynchronous track fusion, age-dependent
inference loss, correlated-source scheduling and current publication records.
No author was contacted, no access control bypassed, and no exhaustive absence
claim is made. Dates embedded in regenerated HTML are not treated as publication
updates: arXiv version histories, primary institutional records and publisher
metadata determine the status above. Downloaded texts are in ignored
`.cache/stage2_literature`; the access manifest records exact retrieval URLs and
hashes. `pdftotext -layout INPUT.pdf OUTPUT.txt` generated the inspected text.

## The precise alternative that was assessed

At decision time D before a meter interval [τ,τ+1 hour), a consumer would choose
a reservation q≥0 for that **same** physical target. The existing prespecified
loss is `4 max(Yτ−q,0) + max(q−Yτ,0)`; the optimal predictive quantile is .8.
Coverage, interval score and normalized reservation loss would remain distinct
outcomes. This is a study-defined utility, not an observed market tariff.

A minimally interpretable message would distinguish:

| Field | Meaning |
|---|---|
| Target support [τ,τ+1h), meter, unit and clock convention | The predicted observed interval; immutable across forecasts being composed |
| Training cutoff and model version | Data used to estimate parameters; distinct from recent inference inputs |
| Latest observed event time E and input-support description | Most recent **used** observation, plus gaps/lags; a maximum timestamp alone does not describe the information set |
| Issue time I | When this forecast was produced from its declared information |
| Arrival time A | When the consumer could use the message; only A≤D is available |
| Revision and superseded message ID | Replace an earlier forecast for the same provider/target; arrival order is not a freshness order |
| Predictive distribution / error information | A calibrated or modeled conditional forecast, not a claim of validity conferred by a timestamp |

Causality requires used observations to have become available before I and I≤A≤D.
For a lagged same-target predictor, changing E changes its effective horizon;
the provider must recompute a valid forecast for τ from that information set.
An old forecast for τ−h cannot be relabeled τ. Local DST ambiguities would need
the existing exclusions; no precise UTC mapping or arrival measurement is in BDG2.

The current calendar provider computes `m_i(τ)=φ(τ)^T β_i` after a fixed fit.
For an available same-target message, altering I, E or A without changing that
fit or the deterministic target features cannot change its numerical forecast.
This is a direct code invariant, not a new theorem. Synthetic delayed deliveries
could remove messages before a deadline, but that would test availability or
message selection, not the asserted effect of stale recent observations.

Newest-event-time selection can fail generically when models differ, older
features carry seasonal information, or evidence is nonnested. The age-inference
literature already studies such failures. **No BDG2 evidence currently shows
that a well-tuned newest rule or a competent joint age-aware predictor is
insufficient for this task.** A scalar age penalty is too weak a sole comparator.
A credible equal-access comparison would need the same arrived, same-target
forecasts and timestamps for newest selection, a history-trained age-vector
combiner with shrinkage/quantile calibration, and appropriate propagated
state-space/OOS or reconciliation references when their extra information is
actually supplied. Giving raw lagged measurements to only one method would
change the experiment.

The possible empirical claim is falsifiable: a specified compact support/cutoff
description could lower reservation loss beyond a learned joint age-aware rule
without merely discarding knowingly wrong-target messages, increasing intervals,
or receiving more observations. It would need a zero-delay control and fixed
delay interventions independent of outcomes. But the proposed mechanism,
sufficient metadata and equal-access advantage have not been established.
Two joint error laws can share the same marginal forecasts and timestamps while
requiring different fusion weights or quantiles; timestamps do not identify the
missing dependence. This standard identifiability issue supplies no new paper
theorem. We propose **no theoretical contribution** at this point.

BDG2 could support a causal replay of a newly specified recent-observation model
using 2016 data only. Its delays and provider roles would be injected experimental
conditions, not measured network behavior. Such a model is absent from Stage 1,
and all October dates have already informed this decision. Implementing it now
would be a new study rather than an audit diagnostic. November/December remain
reserved and are not borrowed for exploratory selection. The novelty and
feasibility prerequisites for recommending that study are not met. Accordingly
no CPU pilot is recommended, no delay scenario was selected by outcomes, and
no Stage 3 execution protocol is manufactured. The archival disposition in
[STAGE3_PROPOSAL.md](../reports/STAGE3_PROPOSAL.md) records the resulting decision.

This analysis remains separate from BDCC. It introduces no graph aggregation,
structural-defect certificate, Matheron reconstruction or selective Monte Carlo.
