# When Forecast Contracts Disagree

## A conditional research plan for compatible probabilistic twin composition

Prepared September 23, 2026. Target: DSpaCES 2026, a workshop of IEEE Big Data 2026. Requested planning hardware: **one NVIDIA RTX PRO4500 Generation GPU with 48 GB VRAM, subject to verification**. The previously inspected RunPod had an RTX PRO 4500 Blackwell with 32,623 MiB, not 48 GB. This plan retains the requested assumption but sizes the pilot below 24 GiB and requires a fresh device check before execution. The request's later reference to an RTX 6000 Ada is treated as an older hardware reference, not a second device.

This is a planning document, not authorization to execute the proposed study. No observational experiment, model fit, GPU benchmark, test-year access, submission, organizer contact or cloud lifecycle action was performed for this plan. Small eight-state CPU linear programs checked the illustrative examples; a script also checked dimensions, page allocation, budget totals and deadline conversion. Their output is [planning_20260923_arithmetic.json](reports/planning_20260923_arithmetic.json). They are not empirical evidence.

The complete 792-line **When Averages Hide Congestion** plan was read first from the available repository copy, `../EAI-BDCC2026/research_plan/EAI_BDCC_2026_Research_Plan.md`. A separately named `EAI_BDCC_2026_Research_Plan(1).md` was not present in the workspace. The exact copy's SHA-256 is recorded with the arithmetic checks. No comparison is represented as a reading of an unavailable, potentially different attachment.

## 1. Recommendation and three contingent contributions

**Recommend a bounded feasibility study of probabilistic compatibility contracts, not a restart of weighted-provenance sketching or an immediate commitment to a full paper.** Ask whether separately fitted forecasts for overlapping groups of buildings can be composed into a defensible decision when the consumer receives their probability tables but not a joint predictive distribution. Check two different failures: the messages may have no common joint distribution at the declared tolerance, or they may admit several distributions that imply materially different decisions.

The operational target is the number of buildings in a portfolio that will have an elevated recorded electricity reading next hour. A consumer reserves a number of review slots before that hour. This gives a bounded, observable decision loss without inventing electricity prices, outage labels, physical intervention benefits or a power-network topology. The release supplies actual meter outcomes. The providers, overlapping service portfolios and review policy are experimental constructions.

The mathematical objects are a finite marginal polytope, an incompatibility witness and a worst-case **expected decision regret** over compatible laws. There is no graph dynamics, hidden traffic reconstruction, rollout enclosure or selective simulation. The theory uses established marginal-problem duality and robust decision theory. Its substantive role is to make the information boundary and the limits of an optimized decision auditable. **The proposition below is a derived contract corollary, not a claimed new general theorem.**

The previous project is already informative. [Stage 2](reports/STAGE2_DECISION.md) found only a 0.482% calibrated interval-score improvement for exact lineage over common-noise correction, 0.294% worse reservation loss, cheaper compressed exact metadata and no useful GPU advantage on its tested pipeline. The few scoring blocks did not establish equivalence. Those observations remain local, but they are sufficient reason not to fund a search for favorable overlap configurations. The same review did not establish an event-time contribution. This new planning request permits examination of the third candidate; it does not erase either finding.

Three intended contribution statements, conditional on the gates in Section 14:

1. **Contract and mathematical analysis.** Specify a forecast exchange whose common conditioning information, variable scopes, probability tolerances and revisions define a joint-law feasibility problem. Derive verifiable infeasibility and decision-regret certificates, including optimization and numerical qualifications, from established finite-dimensional duality. Demonstrate precisely why agreement on shared variables is insufficient on cyclic scopes.
2. **Real-data evidence.** Determine whether independently trained, individually assessed building forecasts exhibit incompatibility or consequential residual dependence ambiguity, and whether explicit contract handling improves the complete policy's observed loss beyond competent coherent reconciliation and a history-trained dependence model. A useful result must survive equal-access calibration and include every fallback decision.
3. **Systems evidence.** Measure the complete cost of auditing many forecast bundles, including typed messages, canonical scope identities, version handling and batched optimization. Identify an actual CPU/GPU crossover, if one exists, using matched tolerances and complete verified results rather than solver iterations or synthetic message counts as the outcome.

Only statements 2 and 3 can supply a new empirical/systems contribution at present. Statement 1 supplies necessary mathematical substance and a precise interface. If the observable phenomenon is absent, if ordinary reconciliation solves it equally well, or if the only surviving result is an LP demonstration, **defer DSpaCES rather than manufacture a paper**. The existing stopped status remains in force until a separately authorized pilot clears those gates.

## 2. Venue verification and scope

Rechecked September 23, 2026:

| Item | Verified position |
|---|---|
| Workshop | Fourth IEEE International Workshop on Dataspaces and Digital Twins for Critical Entities and Smart Urban Communities, co-located with IEEE Big Data 2026 |
| Event | December 14, 2026, fully online; Zoom is specified |
| Submission | October 15, 2026, **23:59 Anywhere on Earth**, explicitly on the workshop-specific submission portal |
| UTC deadline | October 16, 2026, 11:59 UTC; internal completion October 14 |
| Length and style | Workshop full paper up to 10 pages and short/position paper up to 5, references included; IEEE two-column conference format |
| Later dates | Notification November 5; camera-ready November 20; workshop author registration November 26 |

The workshop advances data quality, provenance, interoperable exchange and composition of distributed twins. Synchronization is a necessary contract precondition here. Privacy and infrastructure resilience are not demonstrated by withholding records or reserving review capacity. [Official workshop page](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home).

Use the [DSpaCES CyberChair portal](https://wi-lab.com/cyberchair/2026/bigdata26/scripts/submit.php?subarea=S53&undisplay_detail=1&wh=/cyberchair/2026/bigdata26/scripts/ws_submit.php), not the parent conference's main research track. The portal confirms the deadline timezone and 10-page limit. The [IEEE template page](https://www.ieee.org/conferences/publishing/templates.html) is the official linked source; automated retrieval was blocked, so template compilation is an execution gate, not claimed completed work.

The [author registration page](https://web.cvent.com/event/ea01f8b2-6760-4c81-babc-4c44cc93aeb9/websitePage:8a02ffa9-1a19-43d5-a7f1-9a9e99197482) was readable in this review. It requires a full author registration and gives November 26 for workshop authors. The workshop mentions an expected waiver, but still says details are forthcoming. Treat the waiver as unconfirmed.

The [generic camera-ready instructions](https://wi-lab.com/cyberchair/2026/bigdata26/scripts/BigData_2026_Camera_ready_instruction.php) apply to workshops and require PDF validation, copyright, final PDF submission and a registration receipt. Their generic six-page short-paper rule does not replace the workshop's five-page rule. Their extra-page purchase option does not change this plan's ten-page target. A generic in-person selection field does not establish a DSpaCES travel requirement. A live versus prerecorded presentation requirement, duration and no-show publication condition remain unresolved. Acceptance alone is not treated as a publication guarantee. No organizer was contacted.

## 3. Substantial differences from BDCC

| Dimension | BDCC: When Averages Hide Congestion | Proposed DSpaCES study |
|---|---|---|
| Question | When should a traffic twin retain local observations rather than simulate more? | When can overlapping predictive distributions support a common probability model and a defensible consumer decision? |
| Failure | Compression hides local arrangements relevant to nonlinear future congestion | Separately issued probability claims conflict globally, or leave decision-relevant dependence unidentified |
| Mathematical object | Nonnegative graph recurrence, quotient, structural-defect matrix D and trajectory radii | Marginalization operator A, probability simplex, finite ambiguity set and LP dual witnesses |
| Main result | Fine-trajectory enclosure and sustained-event certificate | Conditional expected-regret bound for decisions selected from forecast messages, with explicit feasibility and numerical conditions |
| Algorithm | Matheron reconstruction, coarse propagation and selective fine Monte Carlo | Message validation, joint-law feasibility, coherent-repair competitors and robust decision optimization |
| Inputs withheld | Local sensor histories after aggregation | Providers' raw training observations and their unavailable joint predictive law |
| Primary data | PEMS-BAY speed; LargeST flow for engineering scale | BDG2 electricity readings and building/site metadata |
| Outcome | Sustained future congestion derived from speeds | Next-hour elevated-reading count in a fixed building portfolio |
| Decision | Warning and observation/computation allocation | Review-slot reservation with a frozen asymmetric count loss |
| Main intervention | Retention fraction, graph resolution and sample count | Forecast scope structure, legitimate local fitting differences and declared probability tolerance |
| Evaluation | Brier score, warning performance, enclosure validity and time-to-error | Compatibility, decision regret within a model, observed policy loss, interval score/coverage and complete audit cost |
| Principal figures | Equal averages/different traffic; information versus scenarios; graph certificate | Locally agreeing/globally conflicting messages; observed portfolio episode; contract diagnostic versus policy loss; verified throughput |

Removing titles and domain names leaves different scientific questions. An overlap graph here records which variables appear together in messages; it is neither a road graph nor a physical propagation model. Enumerating a finite probability space is not coarse/fine simulation. No theorem, empirical result or specific refinement mechanism from BDCC is claimed anew. Generic source manifests, plotting conventions and budget logging may be reused with attribution.

## 4. Three candidates and selection

| Candidate | Potential contribution | Closest obstacle | Decision |
|---|---|---|---|
| A. Partially known evidence dependence | Conservatively combine derived estimates with limited lineage | CI/ESCI, common-information removal and covariance compression are established; the completed pilot found weak incremental value and unfavorable metadata cost | Retire the present sketch proposal; no further tuning in this plan |
| B. Event-time consistency | Compose valid same-target forecasts based on different observation cutoffs | OOS estimation, asynchronous fusion, age-vector inference loss and real-time reconciliation already cover much of the mechanism; previous calendar providers have no recent-input staleness mechanism | Do not pivot here; keep age and target support fixed |
| C. Probabilistic compatibility contracts | Detect when overlapping scope forecasts cannot coexist, and expose remaining decision ambiguity | Compatibility testing and robust decisions from overlapping marginals already exist; empirical value beyond competent reconciliation is unknown | Choose only for a short falsifiable feasibility study |

The reason to choose C is not that it is proven novel. It addresses an untested failure distinct from Stage 1's training-influence variance, admits an exact finite reference, and allows an unusually strong negative control: messages obtained by marginalizing one joint forecast must be compatible. Its weakness is equally clear: a familiar mathematical construction plus an artificial fault injection is insufficient for publication.

The research question is therefore narrow: **Do independently fitted, overlapping forecasts create decision-relevant incompatibility or ambiguity on real outcomes after reasonable calibration, and does exposing that distinction improve a consumer policy at its measured cost?** Units, time support, upstream model ancestry and transport duplication are controlled contract fields. Do not add a privacy method, scheduling algorithm or security claim.

## 5. Twelve-source novelty review

The table separates retrieved results from possible differences. The most important new comparisons are Berrett-Samworth and Doan-Li-Natarajan: they rule out claims to have invented compatibility testing or robust optimization with overlapping marginals. Full-text sections were inspected where stated; this is not a claim to have rederived every proof. The prior [fusion audit](docs/NOVELTY_AUDIT.md) and [event-time audit](docs/STAGE2_NOVELTY_AUDIT.md) remain part of the evidence boundary.

| Primary source and status | Existing assumptions and result inspected | Remaining difference and required evidence |
|---|---|---|
| 1. McLaughlin, Krishnamurthy and Challa, 2003, *Managing Data Incest in a Distributed Sensor Network*. [Proceedings PDF](https://dihana.cps.unizar.es/proceedings/ICASSP/2003/pdfs/05-00269.pdf) | Indexed opening formulation describes repeated information treated as independent in distributed Bayesian estimation. Direct complete retrieval again timed out; no full-proof comparison claimed | We will not call double-counting new. Scope compatibility concerns several variables' predictive laws, not packet retransmission. The original remains an access limitation |
| 2. Cros et al., 2025, *Revisiting Split Covariance Intersection: Correlated Components and Optimality*. [Full author text](https://arxiv.org/html/2501.07915v1), [IEEE TAC DOI](https://doi.org/10.1109/TAC.2025.3530854) | Problem 2 and Theorem 1 treat split errors with known correlated components and optimal conservative two-estimator fusion | Reject a new correlated-fusion claim. A probability-table compatibility problem is different from bounding covariance of unbiased estimates, but that difference alone is not a contribution |
| 3. Funk and Noack, 2024 preprint, *An Event-Based Approach for the Conservative Compression of Covariance Matrices*. [Full text](https://arxiv.org/html/2403.05977v1) | Section III derives conservative elementwise compression with triggers, shared buffer state and diagonal-dominance bounds; assumes reliable error-free transmission. Current arXiv record still identifies submission, not verified acceptance | Compression plus conservative inflation is already established. No sketch/compression theorem is proposed here; real metadata measurements must include reusable state |
| 4. Berrett and Samworth, 2023, *Optimal Nonparametric Testing of Missing Completely At Random and Its Connections to Compatibility*. [Published full text](https://thomasberrett.github.io/AOS2326.pdf), DOI 10.1214/23-AOS2326 | Sections 2-3, the Kellerer characterization and Theorem 2 supply compatibility, an incompatibility index and LP/statistical tests. Consistency on pairwise intersections is insufficient. Their testing theory assumes specified sampling conditions | This directly precedes our feasibility diagnostic. Forecast messages are estimated conditional laws rather than their independent marginal samples. No new compatibility test or finite-sample guarantee is asserted for meter forecasts |
| 5. Doan, Li and Natarajan, 2015, *Robustness to Dependency in Portfolio Optimization Using Overlapping Marginals*. [Accepted full text](https://wrap.warwick.ac.uk/id/eprint/73640/1/WRAP_Doan_1074440-wbs-221015-opre-2013-05-231_final.pdf), DOI 10.1287/opre.2015.1424 | Discrete overlapping marginals, running-intersection/regular-cover structure, efficient LP formulations for worst expected piecewise-linear loss and robust portfolio CVaR. Formulation and Proposition 1 inspected | Robust decisions under overlapping marginal information are not new. We allow incompatible approximate reports and small cyclic scopes, use finite enumeration and assess an explicit fallback policy. That is an interface/application distinction needing real outcome evidence |
| 6. Panagiotelis et al., 2023, *Probabilistic Forecast Reconciliation: Properties, Evaluation and Score Optimisation*. [Author record](https://robjhyndman.com/publications/coherentprob/), [publisher text](https://www.sciencedirect.com/science/article/pii/S0377221722006087) | Defines reconciliation under known linear constraints, distribution/sample constructions and proper-score optimization. Publisher methods descriptions and author metadata were readable; linked complete author PDF retrieval failed | Ordinary coherent projection is a mandatory comparator. Retaining a set of laws and reporting decision ambiguity differs from selecting one reconciled distribution; superiority is unestablished |
| 7. Girolimetto et al., 2024, *Cross-temporal Probabilistic Forecast Reconciliation*. [Full v3](https://arxiv.org/html/2303.17277v3), [publication record](https://robjhyndman.com/publications/ctprob.html) | Definition 3.2/Theorem 3.1 reconcile samples; equation (8) transforms Gaussian means/covariances. Section 4 studies appropriate residual covariance. Published IJF 40(3), 1134-1151 | Our scopes share an identical target hour; no temporal hierarchy is invented. Different supports are rejected, not reconciled by a new timestamp rule |
| 8. Neubauer and Filzmoser, 2024 preprint, *Enhancing Forecasts Using Real-Time Data Flow and Hierarchical Forecast Reconciliation, with Applications to the Energy Sector*. [Full text](https://arxiv.org/html/2411.01528v1), [institutional record](https://repositum.tuwien.at/handle/20.500.12708/208404) | Algorithm 1 uses new partial observations; Theorem 1 assumes covariance-stationary errors and Theorem 2 specializes the model. No later journal publication verified | Energy application plus real-time updating is not an empty novelty space. We hold cutoff semantics fixed and do not claim an update-improvement theorem |
| 9. Wen and Pinson, *Value-oriented Forecast Reconciliation for Renewables in Electricity Markets*, published EJOR 332(2), 492-504, 2026. [Publisher record](https://www.sciencedirect.com/science/article/pii/S0377221725009798), [full author preprint](https://arxiv.org/html/2501.16086v1) | Energy newsvendor decisions, heterogeneous agent objectives, Nash bargaining and empirical primal-dual learning. Sections 2-3 inspected in author version; publisher full retrieval was intermittent. DOI 10.1016/j.ejor.2025.12.011 | Decision-aware reconciliation is established. One consumer's worst-case regret over a contract differs from multi-agent bargaining, but must beat an equally calibrated decision-trained coherent model |
| 10. Shisher et al., 2026, *AoI-Based Scheduling of Correlated Sources for Timely Inference*. [Journal DOI](https://doi.org/10.1109/TON.2025.3643286), [full v2](https://arxiv.org/html/2509.01926v2) | Joint stationarity, signal-agnostic scheduling and correlated sources yield nonseparable age-vector loss; assumption and central result inspected. Published TON 34, 2181-2195 | Correlation plus heterogeneous ages is already studied. This supports rejecting candidate B as a broad claim; it is not a baseline forced into a synchronous contract experiment |
| 11. Biswas et al., 2026 preprint, *Nonlinear Probabilistic Forecast Reconciliation*. [Current record](https://arxiv.org/abs/2604.26668), [full v3](https://arxiv.org/html/2604.26668v3) | September 17, 2026 revision inspected. Sections 3.1-3.2 extend projection and conditioning to nonlinear constraints; UKF approximation uses Gaussian base distributions and a factorization assumption | A new domain or nonlinear constraint is insufficient novelty. Our categorical scope constraints and set-valued decisions are narrower. No peer-reviewed status is inferred from the preprint |
| 12. Gneiting, Balabdaoui and Raftery, 2007, *Probabilistic Forecasts, Calibration and Sharpness*. [Author full text](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf) | Sections 1-3 distinguish calibration notions, show misleading PIT behavior and motivate joint assessment of sharpness and proper scores | Passing individual calibration checks does not imply a correct common conditional law. We must measure the phenomenon, not rename this established limitation |

The original CI, Forsling's robust covariance optimization, provenance semirings and distributed covariance sketches were examined in the earlier audits. They remain background, not omitted discoveries. In particular [Green et al.'s provenance semirings](https://web.cs.ucdavis.edu/~green/papers/pods07.pdf) concern derivation lineage; an identifier or lineage polynomial alone does not specify a probability law. Shared Bayesian priors require common-information accounting, not multiplication of complete posteriors as independent likelihoods.

**Novelty verdict.** Reject the broad propositions “test whether marginals agree,” “optimize conservatively with partial dependence,” “reconcile probabilistic forecasts,” and “use GPU batching” as new science. The only candidate gap is an empirical contract study: whether explicit compatibility/ambiguity status is operationally useful beyond competent reconciliation for separately administered predictive services. A one-day preimplementation comparison must examine existing software and forecast-specific applications of these exact results. If an equivalent experiment/interface already exists, or the proposed empirical question has no credible incremental consequence, stop. The search does not establish an absence theorem.

## 6. Data-space roles, information and updates

For one portfolio of d buildings, let Y_j,t be recorded hourly consumption in kWh. Define X_j,t = 1{Y_j,t > h_j}, with h_j the training-only 90th percentile of valid readings. Strict inequality is frozen. These are elevated readings, not faults or emergencies. Let N_t = sum_j X_j,t. A consumer chooses a_t in {0,...,d} review slots before target interval t, with illustrative loss

    loss(a, x) = 4 max(sum_j x_j - a, 0) + max(a - sum_j x_j, 0).       (1)

Units are study-defined review-capacity cost, not money or measured labor. No claim is made that every elevated reading actually requires intervention. Report raw kWh alongside count episodes, but do not turn count loss into electricity savings. This bounded decision is deliberately simpler than dispatch or outage control.

Each simulated provider owns a scope S_i of two buildings and historical records for that scope. It sends a four-cell conditional probability table b_i,t for X_Si,t in {00,01,10,11}. Primary d=8, with 12 distinct pairs: the sorted cycle (1,2),...,(8,1) plus (1,3),(3,5),(5,7),(7,1). This contains cycles; a seven-edge chain is the prespecified simpler control. These edges mean overlapping service scopes, not electrical connections. Scope size and topology are frozen before outcomes are compared.

All providers target **the same conditional law** given a public context H_t. H_t contains a versioned calendar feature vector and a public past portfolio-count summary, using only times before t: N_(t-2), N_(t-24), N_(t-168), with explicit missing flags. Primary evaluation requires these lags to be observed; no target filling is permitted. The context broker supplies identical serialized values to all providers and the consumer. This is extra declared information with a measured byte cost, not hidden central access. Local training records may differ, but private current covariates are excluded from the primary experiment.

For replay, make a reading available no earlier than one hour after its local label and issue the forecast 30 minutes before the target label. The t-2 lag then has explicit slack before issue time. This is a controlled availability convention, not an observed delivery process. Resolve interval-start versus interval-end labeling before making physical lead-time claims; absent that resolution, the target is the next labeled meter interval and no physical warning lead time is claimed.

This common-conditioning requirement matters. Two correct distributions conditional on different information sets can disagree without either being erroneous. A timestamp or context hash cannot prove that providers used the declared information; providers are trusted to implement their declared target. Tests deliberately violate this assumption in a separately labeled experiment. Never call those different conditional laws a statistical contradiction merely because they differ.

The consumer receives current tables, tolerances and metadata, plus the same authorized historical forecast/outcome feedback as its baseline competitors. It cannot access provider training rows or an evaluator's future outcomes. A feedback broker may release the complete binary outcome vector after its target has elapsed; historical November feedback is therefore sufficient for strong consumer covariance and coherent-distribution baselines. Meter magnitudes and hidden provider fitting records remain outside that interface. The offline evaluator retains full original observations for scoring and a privileged training reference.

### 6.1 Distinct dependencies

| Mechanism | What the contract establishes | What it does not establish |
|---|---|---|
| Duplicate transmission | Immutable ID plus identical content: accept once | A repeated packet is not new evidence |
| Different outputs sharing training records | Canonical record manifests/digests and declared ancestry describe reuse | Overlap does not determine prediction-error covariance |
| Overlapping target variables | Scope IDs identify the same X_j,t in several tables | Agreement on intersections does not guarantee a common joint law |
| Shared prior or upstream model | Version and parent-model hashes identify ancestry | Hash equality does not quantify common uncertainty |
| Different but dependent measurements | Joint probability constraints may describe some dependence | Disjoint record IDs never prove independence |
| Different ages or windows | Target support, issue time, event cutoff, arrival and context must match rules | A forecast for another hour cannot be relabeled as this target |
| Missing coverage | An explicit mask changes which outcome scope is asserted | Missingness is not an observed zero and may be informative |

Training-lineage identities and target-scope identities are separate namespaces. The main consumer needs exact scope identities, not a weighted lineage sketch. A support digest identifies exact equality only. Coarse memberships or approximate overlap sketches cannot substitute for knowing that two messages refer to the same building and hour; evaluate them only as malformed-contract stress if useful, not as a second method.

### 6.2 Minimum message

Include protocol version, provider/service ID, ordered scope IDs, dataset/threshold versions, local target interval and clock convention, context version/hash, issue time, latest actually used event time, training cutoff, arrival time, model/parent hashes, training-support digest, four probabilities, their four tolerances, calibration version, immutable message ID, revision number and superseded ID. Probabilities must be finite, nonnegative and sum to one under an explicit serialization tolerance. Quantization error is added to the declared probability tolerance, never hidden.

Use one active message per provider/scope/model family/target/context. A higher explicit revision replaces the prior one; arrival order alone does not determine freshness. Contradictory contents under one immutable ID are rejected. An exact derived duplicate contributes one constraint set to every eligible baseline. A different forecast on the same scope remains a separate claim, even if it conflicts. No recursive forwarding or evidence shopping is included.

Compile a bundle only after target, threshold, units and conditioning checks. Record its active ID set and bundle hash. Revisions rebuild the active constraint set and invalidate old decisions for that bundle. Each decision is computed at a declared deadline using messages already arrived. Primary messages arrive before the deadline without injected delay; permutations, retransmission and explicit supersession test semantics only.

Providers are trusted, not adversarially verified. Scope identifiers, tables and ancestry may disclose building membership and relationships. This is neither differential privacy nor secure multiparty computation. Public calendar/context information and feedback are documented disclosure, not regulatory compliance.

## 7. Mathematical formulation and auditable proposition

### 7.1 Ambiguity set and incompatibility

Enumerate states Omega={0,1}^d, n=2^d. A column represents one possible observed binary vector. The m-by-n matrix A has A_(i,u),x=1{x_Si=u}, one row per reported local pattern. Stack reported probabilities b and nonnegative tolerances r. Define

    P(b,r) = {p >= 0 : 1^T p = 1, |A p - b| <= r}.                 (2)

This is a finite marginal problem, not a new definition of probability. It permits dependence of any form consistent with the supplied constraints. It may be empty. It is not a posterior distribution over p, and a nonempty set does not prove its elements are calibrated to reality.

As a diagnostic, compute

    rho_star = min rho >= 0 such that P(b, r + rho 1) is nonempty.  (3)

This measures the smallest additional uniform **cell-probability** tolerance, not total variation and not the Berrett-Samworth incompatibility index. Implement their index separately on a small reference panel rather than rename it. Do not silently inflate r by rho_star and announce restored validity. Repair is a comparator, with its change and lost guarantee explicitly reported.

For any real vector y, let c(y)=max_x (A^T y)_x. Every feasible p satisfies

    y^T b - |y|^T r <= y^T A p <= c(y).                          (4)

Therefore y^T b - |y|^T r > c(y) is a certificate of incompatibility. Its positive gap divided by ||y||_1 is a lower bound on rho_star when y is nonzero. This is a finite Farkas/separation argument, inherited from linear programming and marginal-problem duality.

### 7.2 Decision regret rather than automatic worst-case overprovisioning

Let l_a be the vector of losses (1). For nonempty P=P(b,r), define

    R_P(a) = sup_(p in P) [l_a^T p - min_c l_c^T p]
           = max_c sup_(p in P) (l_a-l_c)^T p.                  (5)

The interchange is valid because c ranges over a finite set. The reference a_star minimizes R_P(a). This is established minimax regret, distinct from minimizing sup_p l_a^T p; both are evaluated. The distinction matters because a worst-case loss rule can reserve excessive capacity even when its extra capacity has high regret in plausible lower-load worlds.

For h=l_a-l_c, nonnegative vectors u,v and scalar t satisfying

    t 1 + A^T(u-v) >= h                                      (6)

give the valid dual upper bound

    sup_(p in P) h^T p <= t + b^T(u-v) + r^T(u+v).            (7)

Multiplication of (6) by p and substitution of (2) prove (7). Feasible primal distributions provide lower bounds. In finite dimensions, feasible bounded primal problems attain their optima and standard LP strong duality supplies matching dual values. Retain these certificates, not just a solver success flag.

### 7.3 Proposition: validity after message-dependent decision selection

Assume:

1. At each target, all active messages concern the same X, threshold definitions and common information H. Condition on fixed fitted models/design, so messages are functions of H; solver randomness is independent of future X. The true conditional state law is p0=P(X=.|H). If model estimation is random, future X must retain this law conditional on that estimation information, as in the controlled iid experiment. Otherwise the law must instead be conditioned on the entire consumer information set and assumption 2 checked for that law.
2. With probability at least 1-delta over the stated estimation procedure, **simultaneously for every bundle to be used**, |A p0-b|<=r. This is an explicit assumption/event, not a consequence of identifiers, calibration plots or model agreement.
3. On nonempty P, the implementation supplies upper bounds U_ac for every ordered action pair, each within epsilon_opt of the exact supremum in (5). Feasible primal/dual brackets verify that gap. Let U_a=max_c U_ac. The selected a_hat satisfies U_(a_hat)<=min_a U_a+eta_select.

Then, on the event in assumption 2,

    E[loss(a_hat,X)|H] - min_a E[loss(a,X)|H]
        <= R_P(a_hat) <= U_(a_hat)
        <= min_a R_P(a) + epsilon_opt + eta_select.            (8)

**Proof.** The event puts p0 in P. Consequently the regret at p0 is no larger than the supremum in (5). Weak duality bounds each pairwise loss difference, hence R_P(a)<=U_a. The uniform gap gives U_a<=R_P(a)+epsilon_opt. Apply the selection inequality at an exact minimizer of R_P. Nothing conditions on the realized future X; optimization using b is allowed because all action comparisons hold on the same event. This proves (8).

If a dual candidate has maximum positive residual

    xi = max(0, max_x [h_x-t-(A^T(u-v))_x]),

adding xi to t restores (6) in exact arithmetic. The explicit price of a **certified** residual bound is therefore xi in (7). This makes an approximate batched optimizer auditable. It does not excuse an unmeasured floating-point residual.

**Scope.** Equation (8) bounds conditional expected regret against the best action with the same H and true conditional law. It does not bound each realized loss, compare with a clairvoyant action using X, prove a physical intervention effect, or make a false uncertainty set valid. If P is empty, no bound is returned and the prespecified fallback acts. If P is nonempty but p0 is outside it, the numerical certificate still concerns P only.

The proposition is an explicit specialization of robust regret and weak duality. Do not market the algebra, Farkas witness or data-dependent action selection as an original theorem. A paper must earn its contribution from a distinctive interface finding and real decision evidence. A requirement for a genuinely new general mathematical theorem would leave this project below the present novelty gate.

### 7.4 When can the probability assumption be justified?

In a controlled experiment with a fixed context regime, suppose provider i estimates each local cell probability from n_i iid draws of that regime. Hoeffding plus a union bound permits

    r_(i,u) = sqrt(log(2 m T / delta) / (2 n_i))                (9)

for a fixed family of at most T bundles, using the smallest applicable sample size for each row. Sharing draws between providers does not invalidate this union bound; within-provider iid sampling and fixed selection do matter. Clip probability endpoints to [0,1] without making the interval narrower than the intersection. A packet retry does not increase n_i. Adaptive evidence selection or an indefinite stream needs another analysis and is outside scope.

For real conditional logistic forecasts, equation (9) is **not applicable**: serial dependence, fitted regressions, seasonal drift and conditional model error invalidate that interpretation. Primary real-data r is a declared contract sensitivity, fixed at 0.025 per cell, with r=0 and 0.10 as prespecified alternatives. These are not confidence radii. November calibrates forecasts and December supplies a separate empirical interval correction. Neither step proves simultaneous per-hour conditional containment. Report certificate validity as model-conditional and empirical coverage as observed, separately.

The fixed 0.025 value is a tolerance under study, not a universal acceptable forecast error. If the diagnostic only appears at unrealistically tight tolerances, or decision bounds become useful only after understating model error, reject the method's practical claim. A future statistically justified time-series uncertainty set would be separate research.

### 7.5 Floating point and computational limits

Use FP64 LP references and dot-product verification. For formal numerical certification, compute outward bounds on (6), the objective and probability normalization, including serialization error. A standard forward-error factor gamma_m=m*u/(1-m*u) times absolute summands can bound reductions when its assumptions hold; outward interval arithmetic is simpler for the small verifier. If that verification is not implemented, label results exact-arithmetic theory with numerical agreement, not unconditional floating-point guarantees.

The state space is exponential. d=8 gives 256 states; d=16 gives 65,536. The plan makes no polynomial-time claim for arbitrary cyclic scopes. Tree/decomposable alternatives from established marginal theory are strong cheaper comparators. This limitation must appear in the paper, not only a supplement.

## 8. Two illustrative calculations

### 8.1 Shared-variable agreement does not imply a joint law

Three services forecast (X1,X2), (X2,X3), and (X1,X3). Each sends:

| Local pattern | 00 | 01 | 10 | 11 |
|---|---:|---:|---:|---:|
| Reported probability | 0.05 | 0.45 | 0.45 | 0.05 |

Each variable has probability 0.5 of an elevated reading, so all singleton intersection checks pass. Each pair claims disagreement probability 0.9. But three binary values have either zero or two disagreeing pairs, never three. Thus the sum of the three disagreement probabilities cannot exceed 2, whereas the messages claim 2.7.

With equal cell tolerance r, (4) gives 2.7-6r<=2 as a necessary condition. The minimum repair is exactly **7/60=0.1166667** per cell. It is attained by a joint distribution uniform on the six nonconstant binary states: pair tables then have probabilities (1/6,1/3,1/3,1/6). Packet deduplication removes none of these messages; checking only shared singletons misses the failure.

This is a standard marginal-consistency example, not experimental evidence or a new mathematical discovery. In particular, the messages are not represented as the true conditional marginals of one physical system.

### 8.2 Compatibility still leaves a decision unidentified

Now every pair reports (0.25,0.25,0.25,0.25), with r=0. Two compatible joint laws are:

| Law | States, each with probability 1/4 | Distribution of N |
|---|---|---|
| Even parity | 000, 011, 101, 110 | P(N=0)=1/4, P(N=2)=3/4 |
| Odd parity | 001, 010, 100, 111 | P(N=1)=3/4, P(N=3)=1/4 |

Both have identical pairwise information, including zero pairwise covariance. Yet under (1):

| Reserved slots a | Expected loss, even law | Expected loss, odd law | Worst regret over all compatible laws |
|---:|---:|---:|---:|
| 0 | 6.00 | 6.00 | 5.50 |
| 1 | 3.25 | 2.00 | 2.75 |
| 2 | 0.50 | 1.75 | 0.25 |
| 3 | 1.50 | 1.50 | 1.00 |

Here the full compatible family is the convex line segment between the two parity laws. The optimal action is 2 under the even law and 3 under the odd law. **Minimax regret selects 2 with regret bound 0.25; minimax expected loss selects 3 with worst loss 1.50.** A point independence model cannot identify which law generated the data. This illustrates what the contract can and cannot support; it does not predict a gain on buildings.

The saved CPU check independently solves the eight-state LPs for the repair and every pairwise regret objective. Reproduce with `CUDA_VISIBLE_DEVICES='' OPENBLAS_NUM_THREADS=1 python3 scripts/check_research_plan_arithmetic.py`. Its runtime is negligible relative to a pilot and it reads no meter outcomes.

## 9. Method, pseudocode and complete cost

The proposed policy is a contract wrapper around established optimization. Its output is a compatibility status, decision, model-conditional regret bound, count interval, active-message provenance and cost record. It need not emit a unique joint predictive distribution.

For comparisons requiring a point distribution, construct one common coherent representative by minimizing a fixed KL-to-history criterion over P. Give the historical reference full support through a fixed, reported smoothing rule so that this optimization is well defined even for unseen states. The same representative is supplied to its Bayes-action baseline and the proposed policy. This deliberately prevents a gain caused by giving only the proposed decision rule a better forecast. When P is empty, use the frozen history-trained coherent consumer baseline, record `contract_incompatible`, and return no original-contract certificate. The fallback is part of the scored policy, not a discarded query.

```text
PREPARE
    Read only authorized dates; establish canonical interval and threshold IDs.
    Freeze portfolio membership, pair scopes, common context and provider pools.
    Fit providers on training data; publish versioned probability-table messages.
    Fit allowed consumer baselines and calibration on their assigned dates.
    Enumerate binary states and cache each scope-pattern lookup matrix A.
    Freeze all tolerances, solvers, fallbacks, decision loss and evaluation dates.

COMPOSE(messages, context, deadline)
    Validate scope, target, thresholds, clock labels and identical conditioning.
    Retain arrived active revisions; deduplicate with the same rules for all methods.
    Assemble b, r and active IDs; include quantization error in r.
    Solve feasibility and minimum additional tolerance rho.
    If incompatible:
        save a verified separating witness;
        return frozen coherent fallback decision, unavailable certificate and costs.
    Else:
        for each ordered pair of candidate actions:
            solve maximum expected loss difference;
            verify primal/dual feasibility and objective gap;
        choose the action with smallest worst-regret upper bound;
        construct count interval from worst-case tail probabilities;
        return decision, bound, interval, active IDs and complete costs.

EVALUATE
    Join frozen predictions with eligible future observations outside consumer code.
    Score every target, including incompatibility and solver-timeout fallbacks.
    Retain separate observed-target, allocation, message and benchmark identifiers.
    Aggregate uncertainty over shared calendar blocks and report site sensitivities.
```

A solver timeout is neither compatibility nor incompatibility. Label it unresolved and use the same fallback, including its cost. A successful feasibility solve must yield a primal witness; an infeasibility claim requires a separating witness or a validated reference-solver certificate. The dual residual rule allows useful upper bounds before optimization is exact, but a loose upper bound is reported as loose. It is not a substitute for the objective-gap requirement in (8).

For a conservative central count interval [l,u], bound each tail over P. Choose l and u so sup_p P_p(N<l)<=alpha/2 and sup_p P_p(N>u)<=alpha/2; their union then has probability at most alpha for any p in P. Enumerating both extrema of the d count-CDF thresholds suffices for both 90% and 95% intervals. Such intervals can be wide or all of [0,d]. Report this failure of useful sharpness directly. Empirical December corrections are separate outputs and do not retain the original mathematical interpretation automatically.

For p providers of pair scopes, m=4p and n=2^d. A has p nonzeros per column. Building it costs O(p n), cached once per scope/threshold configuration. Sparse marginal products cost O(p n) per iteration; a dense implementation costs O(m n). One regret decision requires at most d(d+1) nontrivial ordered action comparisons; comparisons with the same action are identically zero. Add at most 2d CDF objectives, feasibility and repair. Exact LP iteration counts are not assumed constant. At d=8,p=12 there are 72 regret objectives and 16 CDF objectives, not one tiny solve.

The per-message probability payload is 4 FP64 values plus four tolerances, 64 bytes before headers. Twelve messages require 768 numeric bytes per target, plus scope/context/threshold metadata, headers, IDs and framing. A scope dictionary of 12 pairs needs 192 bytes for two 64-bit IDs per pair before framing, cached fairly for all methods. Compare actual canonical JSON/CBOR or equivalent encodings, compressed repeated headers and cached model/context versions. Do not advertise these arithmetic payloads as measured wire sizes. Reporting only three probabilities is permitted if the fourth and its error are reconstructed explicitly.

Certificate storage can exceed message storage: all pairwise dual vectors scale as O(d^2 m). Retain certificates for audit targets, failures and a deterministic sample; otherwise retain hashes, gap summaries and enough deterministic input state for regeneration. Count both wire and archival bytes. No claim is made that the contract hides membership or compresses more effectively than exact scope information.

## 10. Verified data choice and causal experimental design

### 10.1 Source and already established facts

Use the [originating BDG2 repository](https://github.com/buds-lab/building-data-genome-project-2) and [Zenodo v1.0](https://zenodo.org/records/3887306). The official deposit describes hourly data for 2016-2017, 3,053 meters, 1,636 nonresidential buildings and 19 sites. Its rectangular positions are not all observed readings. Access is public without an application. The existing verified archive can be reused; another download is unnecessary.

| Property | Verified evidence and study implication |
|---|---|
| Exact source bytes | Prior manifest: 595,266,464 bytes; MD5 `44393dc4cf61e84dec105e955368c890`; SHA-256 `50ef5178c5d4ce18b0d0480140e83349d1b058f10b4b1e59b9e8698a7b8e417b` |
| Electricity member | `data/meters/raw/electricity.csv`, 174,239,039 uncompressed bytes in the archive; actual CSV, not an LFS pointer |
| Schema and units | Timestamp column plus building columns; hourly energy readings in kWh; local clock labels |
| Electricity scope | Prior data audit counted 1,578 electricity columns; January-September 2016 had 9,811,945 finite readings out of 10,376,928 positions |
| Eligibility evidence | Prior training-only audit found 1,324 eligible buildings across 17 sites; this does not yet establish complete eight-building portfolio coverage |
| Synchronization | Site timezone field exists; a regular hourly label grid does not prove clock accuracy or a resolved DST convention |
| Connectivity | Building/site IDs exist; no verified feeder graph or provider organization map |
| Outcomes | Actual future meter readings; elevated flags and portfolio counts are derived labels; no real review demand, response benefit or outage ground truth |
| Missingness | Preserve missing labels; complete-portfolio scoring can introduce selection bias. Record exclusions and their site/season distribution |

The [meter documentation](https://github.com/buds-lab/building-data-genome-project-2/wiki/Meters-data-features) and [metadata documentation](https://github.com/buds-lab/building-data-genome-project-2/wiki/Metadata-features) substantiate units, layout and timezones. The release's raw folder is already harmonized, not untouched instrument output. The cleaned version removes outliers and some zero readings; use it as a sensitivity mask, not a replacement source that silently removes high outcomes. No future weather is used.

**Terms discrepancy.** The downloaded v1.0 archive contains an MIT root license, retained at [BDG2_LICENSE.txt](manifests/BDG2_LICENSE.txt). The [current repository license](https://raw.githubusercontent.com/buds-lab/building-data-genome-project-2/master/LICENSE), rechecked here, is headed Attribution-ShareAlike 4.0 Unported. Its exact text is retained at [BDG2_CURRENT_LICENSE.txt](manifests/BDG2_CURRENT_LICENSE.txt). Preserve both records and attribution; do not assert that the software-style MIT notice resolves all measurement rights or replace it with the article's license. Publish code, retrieval instructions and permitted derived evidence; raw redistribution is unnecessary. The data are accessible now, but this wording discrepancy remains a documented publication/redistribution limitation.

### 10.2 Cohort and partitions

Choose at most 16 disjoint portfolios of eight electricity buildings, up to two per site, from at least eight sites if training completeness permits. This gives at most 128 buildings. Sort eligible site and building IDs and apply a deterministic round-robin grouping rule. Require at least 95% valid nonnegative training hours per building and 90% complete training hours per portfolio, including required context lags. Store every exclusion and actual site count. Do not select by incompatibility frequency, interval score or decision gains.

A bounded pilot uses four portfolios from four sites. If the fixed rule cannot produce at least eight complete portfolios at four sites for a later main study, narrow the scope before testing or defer. Do not replace unfavorable sites. Portfolio construction is simulated service organization within a real site, not discovered electrical connectivity. No physical aggregation across local timezones is needed.

| Dates | Role and permission boundary |
|---|---|
| January-September 2016 | Eligibility, thresholds, provider fitting, preprocessing and blocked out-of-fold diagnostics |
| October 2016 | Development and bounded feasibility only. All October is already development-exposed by Stages 1-2; it is not a new unbiased holdout |
| November 2016 | After models/protocol are frozen: fit probability temperatures and consumer historical-dependence/reconciliation parameters under fixed rules. No exploratory architecture or cohort selection |
| December 2016 | After those weights are frozen: empirical interval corrections; no retrospective model selection |
| January-December 2017 | One final frozen evaluation only after separate main-study authorization; remains sealed in planning and pilot |

Use a seven-day embargo wherever lag-168 context is required to lie wholly inside a split. Thus November fitting begins no earlier than November 8, December calibration no earlier than December 8, and test scoring no earlier than January 8. This sacrifices sample size and must be counted. Calendar week labels and sites are grouping variables, not independent replications. Report partial weeks. Do not count eight calendar weeks of November/December as eight complete usable blocks after embargoes.

Use original local labels with the previously documented ambiguous/nonexistent-clock exclusions and any additional interval discontinuities. Keep corrected records versioned. Within a split, the same canonical measurement has one role regardless of how many providers reuse it. Mask any target missing in the eight-building portfolio; never interpolate it. Scoring is for complete eligible portfolios, with exclusions explicitly reported. A missingness stress experiment hides observed inputs only and retains its separate intervention label.

### 10.3 Provider models and experimental federation

Fit a four-category multinomial logistic forecast per pair using the same small feature specification: calendar harmonics, weekday and the shared causal portfolio-count lags. Use ridge regularization with at most three training/development-selected strengths, shared across providers. Fit by an established optimizer; no new neural architecture is needed. A shrinkage categorical seasonal model is a competence baseline. A label that is nearly constant is not grounds to change its threshold on test.

Primary provider evidence pools use approximately two-thirds of eligible training days, stratified over the full training period by a fixed hash of provider ID and day. The target is about 180 days, not 21 or 42 artificially small days. Impose a study-wide minimum of 160 sufficiently observed days per provider. Report actual records, pair overlaps and the common union. Pool differences represent simulated administrative histories; their relationship to real organizations is unmeasured.

Use one fixed allocation seed in the pilot and three frozen seeds in a main study. Repeated fits/allocations do not create new observed targets. A shared-pool control gives every provider the same training dates. A fully coherent control takes all tables from one joint forecast; it distinguishes optimization defects from ordinary local estimation differences. Primary data contain no injected contradictory probability entries. Injected corruption and different-conditioning messages are stress tests, never the evidence for natural incompatibility.

Fit a common temperature-calibration family per provider using only the assigned historical window. For the October pilot, use October 8-14 for historical fitting, October 15-21 for interval correction and October 22-31 for scoring, at no more than 256 uniformly spaced eligible targets per portfolio across all roles. The short scoring span supports a feasibility diagnosis only. Do not confuse a seven-day label span with seven independent model comparisons.

Theorems apply to a correctly specified common conditional law and valid cell tolerances. The real model is a plug-in approximation. Shared priors, weather, occupancy and cross-building dependence can remain even when evidence pools are disjoint. No attempt is made to infer independence from provenance or to identify a physical covariance decomposition from one series.

## 11. Small, decisive evaluation

### 11.1 Strong baselines and information regimes

All deployable methods receive identical active identifiers, scope dictionaries, probabilities, contexts, historical feedback and calibration dates. All use the same target eligibility and serialization precision. Measure their information and cost rather than calling everything equal-access by assumption.

| Baseline | Information/use | Purpose |
|---|---|---|
| Seasonal count distribution and persistence-informed count model | Common context and permitted historical counts | Establish a useful low-cost decision baseline |
| Independence composition, with exact packet/derived deduplication | Consensus singleton probabilities from the same tables | Simple failure reference; not the main competitor |
| Tree composition / decomposable marginal method | Same tables, deterministic tree selection fixed in development | Efficient established reference where intersection consistency suffices; excluded edges and information loss reported |
| Coherent point reconciliation | Joint law minimizing a fixed weighted probability-table mismatch, with regularization and exact normalization over 256 states | Strong ordinary repair method; computes a valid law rather than multiplying overlapping tables |
| History-trained coherent dependence model | A regularized binary log-linear/Ising model fitted with the same permitted November outcome feedback and contexts | Estimates dependence and uses all available historical labels; cap tuning to the same three settings |
| Direct decision model | Regularized linear 0.8-quantile regression for N using common context and current table entries; fit on identical historical feedback, clip to [0,d] and round upward | Strong decision-oriented competitor that need not estimate an entire joint law |
| Exact marginal LP and minimax expected loss | Identical current ambiguity set and scopes | Known mathematical reference; exact LP is equal-access, not privileged; contrasts regret with worst loss |
| Proposed compatibility status plus minimax-regret policy | Same messages; prescribed fallback on empty/unresolved bundles | Tests the operational value of exposing the constraint set rather than choosing one unqualified joint law |
| Full-information joint predictor | All selected training binary vectors/causal features | Privileged fitting reference, disclosed as richer training access; later feedback access alone does not make it privileged |

Use nearest-coherent least-squares reconciliation and KL-to-history selection as explicit implementations, not a vaguely named ideal baseline. Use the same three regularization choices for the direct decision baseline; its quantile level is fixed by the loss, not tuned to outcomes. For r-nonempty bundles, feed the **same** KL-to-history representative to the point-action and robust-action policies. Differences in decisions then isolate ambiguity treatment. On a small panel implement the published incompatibility index for comparison with rho_star. Scalar CI is not an appropriate substitute for a joint categorical distribution: it addresses an estimator covariance, not this target. The relevant dependence-aware competitors are coherent categorical models, decomposable marginal methods and the exact LP.

Report raw tables, equally temperature-calibrated tables and December-corrected count intervals. If one method gains solely from receiving more feedback or from wider intervals, reject a contract-specific benefit. A fallback must be trained and frozen before test, and its outcomes are included in every headline policy score. Report incompatible, feasible-but-ambiguous, resolved and solver-timeout rates separately.

### 11.2 Controlled theorem experiment

Use finite binary distributions with known exact cell probabilities, so true risk is analytic. Test d in {3,8,12}; tree and fixed cyclic scopes; exact probabilities and iid empirical tables; three dependence regimes (independent, common-factor and parity-based). This is at most 36 structural/noise condition families before a small fixed set of sample sizes. Cap at 20 independent estimation repetitions per retained family; no full product with every tolerance and GPU batch size.

Verify feasibility, witness separation, minimum repair, all regret upper bounds and the solver-gap consequence against an FP64 reference. Count violations of probability-set containment separately from invalid numerical certificates. Include exact duplicates, zero-probability cells, near-boundary probabilities, singular/redundant constraints and inconsistent singleton marginals. Use (9) only for its declared fixed iid family and account for the total failure allocation across all reported runs.

Deliberate assumption failures: serially correlated samples treated as iid, different conditioning information labeled as common, and biased/selected provider histories. Their failures limit assumptions; they are not reasons to tune the theorem. Known compatible tables must produce no unexplained positive incompatibility certificate. A primal/dual or enumeration discrepancy blocks subsequent claims.

### 11.3 Bounded real and systems matrix

| Package | Frozen configurations | Scope |
|---|---|---|
| Feasibility pilot | Four d=8 portfolios, one allocation, primary cyclic scope, r in {0,0.025,0.10}; same minimum baseline family | At most 256 October origins per portfolio; no November/December or 2017 access |
| Main outcome study, if authorized | Up to 16 portfolios, 12 providers, r=0.025, three allocation seeds, frozen methods | All eligible 2017 targets; average allocation replicas within targets |
| Contract sensitivity | r=0 and 0.10, tree control and shared-pool control | Four frozen portfolios, at most 2,000 test targets each; no new tuning |
| Coherent negative control | Tables marginalized from one coherent predictor | Same frozen target panel; no expected compatibility benefit |
| Protocol integrity | Duplicate factors 1,2,10; arrival permutations; one explicit revision | Fixed predictions and deadline, no purported new independent observations |
| Assumption failure | Condition mismatch and controlled probability corruption | Synthetic or bounded development panel only; separate from main real-data evidence |
| Scaling | d in {4,8,12,16}, pair counts tied to fixed sparse/dense scope patterns, batches up to 2,048 LP objectives | Controlled replay capped at five million transmitted messages; larger d is engineering stress |

Do not cross all rows. Freeze a seed manifest before main execution. Changes to tolerances, scopes, models or complete-target criteria after test inspection require a new study, not relabeling the same test as validation.

### 11.4 Metrics, evidence counts and uncertainty

Co-primary outcomes are mean observed loss (1), normalized by d, and the 90% count interval score, also normalized by d. For a central interval [l,u], use

    IS_alpha = (u-l) + (2/alpha)(l-N) 1{N<l}
                      + (2/alpha)(N-u) 1{N>u}.                (10)

Also report 90/95% coverage, interval width in buildings, count MAE/RMSE, provider categorical log/Brier scores, and a ranked probability score for each actual point count distribution. A set of distributions is not itself a point forecast; do not score its midpoint CDF as if it carried the set's guarantee. Report provider-level reliability on fixed bins and conditional bias by season and site.

Compatibility diagnostics include rho_star, minimum witness margin, rate of failures not detected by singleton intersection checks, and changes in decisions or action-regret bounds. Mathematical R_P is a property of the working uncertainty set. It is not an observed estimate of regret against the unknown true optimal action. Real outcomes identify policy loss differences, not that counterfactual optimum.

Average losses within portfolio, then within site, then across sites for the primary estimate. Show a target-weighted alternative explicitly. Preserve paired methods, portfolios and allocation replicates when resampling chronological week blocks. Use 1,000 CPU bootstrap replicates for a final study, resampling the same weeks across all sites to retain shared calendar effects. Add site-deletion sensitivity. Neither disjoint buildings nor geographic sites guarantee independence. The final year has at most 52 usable weekly blocks, fewer after exclusions.

The pilot has too few October blocks for a decisive statistical claim. Its uncertainty output is descriptive and its role is to detect absence, catastrophic failure or infeasible cost. For any high-count episode claim, define episodes from training rules and count distinct site-days/weeks; require at least 50 observed episodes across 20 site-days in a final analysis. Continuous count loss remains primary if that gate fails. Do not tune event thresholds to manufacture episodes.

For that secondary episode analysis, fix K=max(2, ceiling of the training 90th percentile of N) separately for each portfolio, and group consecutive complete hourly readings with N>=K. An unobserved hour ends a group. For Figure 2, use the first complete 24-hour local day on or after February 1, 2017 containing such an episode in the first sorted eligible portfolio. If none exists, use its first complete day after that date and label it an ordinary day. This selection may use the observed count but never a method's advantage. Any extra forecasts needed to show hourly detail under the reduced main cadence are a separately counted, at-most-24-origin illustration, excluded from headline scores.

### 11.5 Falsification criteria

1. Any unexplained invalid feasibility/witness/regret result under checked assumptions blocks the mathematical implementation claim.
2. Continue beyond feasibility only if uncorrupted provider forecasts show a reproducible nontrivial issue at reasonable tolerance: either global incompatibility missed by intersection checks or a remaining ambiguity that actually changes candidate actions. As a practical pilot screen, require at least 5% affected eligible targets across at least three of four portfolios; report counts and stability, not a significance claim.
3. The methods must be competent: coherent/provider forecasts should match or improve the seasonal count baseline on development proper score and decision loss. No deliberately misspecified or tiny-data provider is used to create a problem.
4. A practical main-study claim requires at least a 5% observed loss improvement over the strongest deployable equal-access baseline at comparable complete cost, or at least 2x complete throughput at materially comparable decision quality. Report paired uncertainty and failures; these are practical thresholds, not automatic statistical tests.
5. Coverage gains require useful sharpness: no more than a 5% interval-score degradation and no claim based on returning [0,d] for most targets. Model-conditional bounds must not be sold as distribution-free real coverage.
6. If near-coherent repair or the learned coherent model matches the policy, retire the proposed method. An informative diagnostic paper remains possible only if real incompatibility/ambiguity itself exposes a substantive, reproducible limitation beyond existing compatibility examples.
7. If the issue appears only after corrupting probabilities, shrinking data pools, changing context without declaring it, or using an unrealistically small tolerance, stop the real-data claim.
8. A useful GPU claim requires a measured improvement in complete verified work. If none appears on the bounded workload, report that and remove the GPU-benefit claim. If useful GPU computation is an essential submission requirement, this is a stop gate, not permission to pad the workload.

## 12. GPU work, big-data accounting and bounded budget

### 12.1 What the GPU would do

The meaningful candidate workload is a batch of many marginal feasibility and loss-difference LPs sharing A but having different probability bounds and objectives. There are no traffic rollouts, conditional Gaussian fields, Matheron samples or coarse/fine decisions. Model fitting is small and CPU-first. The GPU can accelerate repeated marginal products and primal-dual updates if enough complete problems are available.

Use an established primal-dual method or verified library implementation, with an exact CPU reference and the explicit dual checks above. GPU LP methods themselves are prior work; [Lu and Yang's cuPDLP.jl, Operations Research, 2025](https://doi.org/10.1287/opre.2024.1069) is an implementation reference, not evidence of speed on these small batched problems. No new convergence rate, solver or GPU architecture is proposed. Do not substitute entropic objective values for the original LP without a derived regularization error bound.

Flatten (target, allocation, action pair) into LP jobs. A batch of 2,048 jobs does **not** mean 2,048 targets each with all action pairs resident. Keep state order and scope matrices cached, chunk objectives, and use separate deterministic queues for feasible, infeasible and unresolved problems without dropping hard cases from throughput.

| Buffer | Example shape / precision | Raw bytes, excluding workspaces |
|---|---|---:|
| Primary primal probabilities | [2,048 LP jobs, 256 states], FP32 | 2,097,152 |
| Primary dual constraints | [2,048, 96], FP32, two signs for 48 cells | 786,432 |
| d=12 primal state | [256, 4,096], FP32 | 4,194,304 |
| d=16 primal state | [128, 65,536], FP32 | 33,554,432 |
| Dense shared d=16 scope matrix | [96,65,536], FP32 for 24 pair scopes | 25,165,824 |
| Primary target context/predictions | Streamed [targets in batch, providers, 4 cells] plus tolerances | Measured separately; never store all solver iterates |

Several primal/dual/work buffers are required; FP64 doubles those examples. Nothing here requires 48 GB merely to fit. The expected value of the GPU is arithmetic throughput over many objectives, not filling VRAM. Cap active allocation at 24 GiB for the initial study even if the requested 48 GB device is confirmed. Cap host working memory at 20 GB and data/cache output at 10 GB. Reuse the verified 0.595 GB archive; initial new downloads, including dependencies and papers, must remain below 2 GB.

CPU responsibilities include source parsing, threshold/context construction, canonical IDs, message validation, reference LPs, calibration, uncertainty summaries and plotting. Include model fitting, scope compilation and verification in total study cost. Parse wire messages into contiguous arrays; measure parsing separately but also include it in the end-to-end pipeline. Do not feed pre-parsed arrays to the GPU benchmark and raw JSON to the CPU baseline.

Compare a competent multicore reference (warm-start/cached CPU LP where available), vectorized CPU primal-dual updates and the GPU implementation. Run matched FP64 comparisons on an audit panel and matched objective/feasibility tolerances for throughput; separately label any FP32-plus-FP64-verification path. Avoid BF16/FP16 in probability or certificate arithmetic. Record CPU identity, thread count/quota, GPU name/VRAM/driver, libraries and environment lock. No published FLOP rating substitutes for measurement.

Measure process/model initialization, compilation if used, scope compilation, parsing/deduplication, transfers, solver, certificate verification, output serialization and peak memory. Synchronize GPU timings. Report cold and warm p50/p95 latency and completed verified targets/second, not only LP iterations/second. Also report completed LP objectives/second, provider messages/second and fallback rates. Randomize CPU/GPU benchmark order across at least five complete repetitions; use matched saved messages. A single target can favor the CPU even if offline replay benefits from the GPU.

### 12.2 Honest scale

At the maximum proposed cohort, a non-leap test year supplies at most:

* 128 x 8,760 = **1,121,280 building-hour positions**, before missingness and embargoes;
* 16 x 8,760 = **140,160 portfolio-target outcomes**;
* 140,160 x 12 = **1,681,920 provider messages per allocation**;
* three allocations: **5,045,760 distinct model/target messages**, but the same 140,160 possible observed portfolio targets;
* 88 regret/CDF objectives per target and allocation: up to **37,002,240 LP objectives**, plus feasibility/repair and point reconciliation.

This last count is a real cost risk. The pilot must project it using complete observed timings, including failed/slow cases. If it exceeds the cap, the single prespecified scope reduction is to evaluate targets at local 00:00, 06:00, 12:00 and 18:00 for every portfolio, chosen before test access. Preserve all three allocation seeds and all baselines; never select hours by performance. If even that is infeasible, defer. Main outputs must disclose whichever cadence is frozen.

The native rate is only 192 messages/hour, about 0.053 messages/second, for 16 portfolios with 12 providers. High replay rates represent catch-up or batch auditing, not a measured high-velocity deployment. The archive itself is moderate. Big-data relevance is the combination of a heterogeneous meter archive, millions of versioned forecast messages and tens of millions of compositional risk queries. Binary states, LP objectives, allocation seeds and duplicated packets are computation, not new real observations.

Scale axes are portfolio dimension, scope count/cycle structure, message volume and refresh frequency. Larger d stresses the actual marginal problem and its exponential cost; it is not evidence of new independent sites. A single-machine provider/consumer replay verifies API restrictions, semantics, numerical results and cost. It establishes no inter-organizational deployment, network availability or resilience to real communication faults.

### 12.3 Provisional caps

| Work package | Maximum new GPU-allocated hours |
|---|---:|
| Environment, CPU/GPU feasibility pilot and precision audit | 2 |
| Provider construction and fixed-model preparation | 3 |
| Strong baseline fitting and limited tuning | 3 |
| Frozen observed-outcome evaluations | 5 |
| Controlled theorem and assumption checks | 3 |
| Complete pipeline scaling | 3 |
| Minimal contract/coverage ablations | 2 |
| Reserve for diagnosed failures | 3 |
| **Total ceiling, including pilot** | **24** |

These are ceilings, not estimates or spending targets. CPU-only work need not hold a GPU job open; distinguish GPU-active duration, allocated research wall time and provider billing. Existing Stage 1's 49.1-minute research window remains historical and is not relabeled as this study. The new 24-hour envelope is hypothetical until authorized, and does not terminate an already allocated pod.

An optional extension to 48 total GPU-hours would allow at most 8 more hours for a frozen seasonal replication, 6 for broader same-domain portfolios, 6 for numerical robustness and 4 for independent reproduction. It cannot fund a new domain, an architecture search, favorable-tolerance hunting or unbounded solver tuning. It requires separate authorization and a surviving scientific claim.

The first implementation prompt below permits, only when separately invoked, a 12 CPU-hour cumulative job cap and at most 2 GPU-allocated hours. Reading/writing time is logged separately. A four-hour CPU novelty/correctness gate precedes observational fitting. Stop cleanly with manifests/checkpoints on budget exhaustion; leave no experiment running.

## 13. Scientific visuals, tables, paper and talk

Generate figures from retained numerical data with Matplotlib or equivalent. Use vector PDF/SVG, embedded fonts, readable colorblind-safe colors and direct units. Keep one color for independence, one for coherent point reconciliation, one for learned dependence, one for the contract policy and gray for privileged references. Explicitly distinguish illustrative geometry, working-model bounds and empirical uncertainty. No empirical-looking chart is generated during planning.

| Main figure | Precise claim and required evidence | Axes, uncertainty and reproducible rule |
|---|---|---|
| 1. Local agreement, global incompatibility | Three pair-service tables refer to three canonical building variables; the first Section 8 example violates one global inequality while passing all singleton checks | Diagram edges are forecast scopes, not causal links. Adjacent bars show disagreement sum 2.7 versus maximum 2 and repair 7/60. Exact illustrative values, no error bars or real provider logos; generated from checked eight-state example |
| 2. One observed portfolio episode | Show whether compatibility/ambiguity changes a capacity decision before actual elevated readings occur | Local time x; actual N and reserved slots y; separate interval and rho/bound panels, plus missingness. Select the first complete elevated-count episode after a frozen date in the first sorted eligible test portfolio, without consulting method gains. Plot all selected times, including an unimpressive result |
| 3. Contract diagnostic versus useful performance | Determine whether the natural issue persists after calibration and whether the policy improves decisions without vacuous intervals | Tolerance r on x; separate panels for incompatibility/ambiguity rate, normalized policy loss and interval score. Shared week-block uncertainty in final study; pilot labeled descriptive. Show uncorrupted primary data separately from stress and coherent controls |
| 4. Complete verified processing cost | Identify where batched auditing benefits from GPU work and where it fails | Portfolio dimension or completed batch size on x; verified targets/second and p95 latency on y; companion measured bytes/target versus policy quality panel. Show CPU/GPU, precision, gap tolerance, cold/warm state and timing ranges. Read saved stage timings, never only device kernel logs |

Three main tables: (1) data and evidence accounting, including actual sites, buildings, eligible hours, missing targets, episodes/weeks and synthetic provider roles; (2) main observed losses, interval scores/coverage/widths, fallback rates and paired uncertainty; (3) information contracts, serialized/amortized bytes, solver/verifier cost and memory. Put exhaustive source comparisons, conditions and diagnostic distributions in the repository supplement, not an unreadable main-paper table.

Working title: **When Forecast Contracts Disagree: Compatible Decisions from Overlapping Twin Predictions**. If results support only a diagnostic, use a title describing that limitation rather than implying improved decisions. Do not advertise a new general fusion theorem.

| Ten-page full-paper allocation | Pages, including figures/tables |
|---|---:|
| Abstract and problem/contribution | 0.8 |
| Closest literature and novelty boundary | 0.9 |
| Exchange contract, target and information sets | 1.2 |
| Compatibility and decision proposition, proof and example | 1.6 |
| Data, interventions and evaluation | 1.2 |
| Results, four figures and three compact tables | 2.6 |
| Limitations and conclusion | 0.5 |
| References | 1.2 |
| **Total** | **10.0** |

Compile the actual IEEE template early. Keep the main proof readable in the paper; a repository supplement does not compensate for missing main reasoning. Do not shrink fonts or margins. A GPU failure can remove a systems panel without invalidating a genuinely useful empirical result, but it would no longer satisfy the user's full GPU-oriented objective. A failure of the empirical/novelty gate invalidates the intended full paper, not merely a figure.

Nine-slide talk:

1. Three plausible local tables that cannot all be true together.
2. Define the real elevated-reading outcome and review-capacity decision.
3. Show provider scopes, common conditioning and the consumer's access boundary.
4. Explain why shared-record IDs, common target identity and joint compatibility differ.
5. Show the finite set of compatible laws and one dual regret bound.
6. Show actual data, simulated service assignments and chronological controls.
7. Compare observed policy loss and interval quality against the strongest baseline.
8. Show actual complete CPU/GPU cost and its crossover or failure.
9. State supported claims, model assumptions and the go/no-go conclusion.

Presentation duration is not verified; adjust slides only after it is known.

## 14. Schedule, gates and modest fallback

The schedule targets October 14 readiness, before the verified October 15 AoE deadline. It is conditional; there is no reason to consume the whole calendar if an early gate fails.

| Date, 2026 | Deliverable | Gate |
|---|---|---|
| September 23 | This plan, BDCC comparison, current source audit and checked example | Preserve completed Stage 2 findings and the sealed dates |
| September 24 | One-page comparison of exact interface/corollary with compatibility, robust-regret and forecast-reconciliation work; implement tiny CPU references only if separately authorized | Reject claims already supplied by prior work. Continue only with a credible empirical question and a plausible distinguishing result |
| September 25-26 | Bounded CPU-first four-portfolio pilot; at most 2 GPU-allocated hours if the CPU gate passes | Natural uncorrupted issue, competent baselines, valid arithmetic and cost projection; otherwise stop |
| September 27 | Pilot report, information-access audit and complete byte/timing accounting | No selected buildings, tiny pools or injected faults used to rescue a failure |
| September 28-29 | Freeze cohort, cadences, models, scopes, r, baseline tuning, calibration rules and main command | Project <=24 new GPU-hours; main still disabled until authorized |
| September 30-October 2 | Authorized controlled study and November/December fitting/calibration under frozen rules | No exploratory selection from those outcomes; numerical violations block certification |
| October 3-4 | Authorized 2017 evaluation and bounded scaling | No retuning from test; preserve all targets/fallbacks |
| October 5-6 | Paired analysis, site sensitivity, claims ledger and figure data | Require practically meaningful effect beyond strongest equal-access method; report denominators |
| October 7-9 | Manuscript in official ten-page template | No new theorem or deployment claim inferred from code correctness |
| October 10-11 | Scientific review and reproducibility check | Remove unsupported performance, calibration or GPU claims |
| October 12-13 | Bibliography, formatting, author requirements and talk outline | Recheck presentation conditions, registration/waiver and current venue instructions |
| October 14 | User-reviewable submission candidate and source archive | No automatic submission |
| October 15 | Correction buffer; user-controlled submission | 23:59 AoE = October 16, 11:59 UTC |

**Decision gates before test.** Require at least eight eligible portfolios at four sites, with a target of sixteen at eight sites; enough training days for full provider pools; nondegenerate elevated-reading labels; and an October pilot that shows more than a synthetic contradiction. Freeze the final cohort based on quality, not estimated gains. Require all controlled certificates to pass, a measured solver-gap policy, manageable fallback frequency, and feasible complete cost. The shorter embargoed calibration windows are disclosed rather than called independent full months.

**Fallback.** If GPU batching fails but a substantial real compatibility/decision finding survives, a CPU-based case study could be scientifically defensible, although it misses the requested GPU requirement. If policy gains fail but a reproducible limitation beyond published marginal examples remains, consider a five-page diagnostic paper with established theory and candid scope. Neither fallback is automatic. If the only evidence is a standard parity example, an incompatible injected table or negative timing, stop/defer. Do not return to the retired sketch or event-time approach within the same ten-page paper.

## 15. Repository structure and preservation rules

Keep this plan at the requested root path. Preserve `docs/RESEARCH_PLAN.md`, the completed Stage 1/2 reports, their configurations and numerical outputs as historical evidence. The original `scripts/run_main_study.py` remains disabled. Use a separate descriptive package for any later contract implementation within the same repository, on `main`, without new branches. Reuse only generic infrastructure where it does not import BDCC science or reopen the stopped sketch.

| Proposed path | Responsibility |
|---|---|
| `DSpaCES_2026_Research_Plan.md` | This complete prospective plan |
| `docs/contract_study/CLAIM_MAP.md` | Exact inherited results, proposed empirical distinction, unresolved novelty |
| `docs/contract_study/PROOF_AUDIT.md` | Feasibility, witness, regret proof and arithmetic/precision scope |
| `configs/contract_study/data.yaml` | Source hash, canonical IDs, cohort rule, split/access limits |
| `configs/contract_study/pilot.yaml` | Frozen small workload and CPU/GPU/storage limits |
| `configs/contract_study/main.yaml` | Proposed matrix, `authorized: false` until explicitly enabled later |
| `src/forecast_contracts/target_definition.py` | Elevated-reading labels, thresholds, count outcome and loss |
| `src/forecast_contracts/provider_models.py` | Local pair fits and probability calibration |
| `src/forecast_contracts/common_context.py` | Shared causal features, cutoff semantics and context hash |
| `src/forecast_contracts/messages.py` | Typed schema, scopes, immutable identities and revisions |
| `src/forecast_contracts/marginal_constraints.py` | Enumerated states, A and probability tolerance construction |
| `src/forecast_contracts/compatibility.py` | Feasibility, additional tolerance and separating witnesses |
| `src/forecast_contracts/decision_bounds.py` | Loss-difference LPs, dual bounds and minimax-regret actions |
| `src/forecast_contracts/numerical_verifier.py` | FP64/outward residual checks and explicit certificate status |
| `src/forecast_contracts/coherent_baselines.py` | Exact LP, point repair, tree and learned coherent competitors |
| `src/forecast_contracts/evaluator.py` | Privileged outcome joins, proper scores and grouped inference |
| `src/forecast_contracts/batched_solver.py` | CPU/GPU numerical kernels with a shared tested objective |
| `scripts/run_contract_pilot.py` | Future bounded implementation entry point |
| `scripts/run_contract_main.py` | Future frozen main entry point, disabled by default |
| `reports/contract_study/` | Feasibility and explicit continue/stop decision |
| `manifests/contract_study/`, `results/contract_study/` | Sources, access logs, seeds, small evidence and ledgers |
| `paper/contract_study/` | Official template, manuscript and vector figure references |

The consumer package must accept typed message bundles and public context, not a dataframe of hidden training rows. Tests should attempt forbidden future/record access and verify that evaluator privileges remain separate. Ignore raw data, large predictions, third-party papers, caches and environments in git. Preserve the existing local pod archive; do not allocate new resources, change remotes, stop/delete the pod or modify unrelated projects under this planning request.

## 16. Ready-to-paste bounded implementation prompt

This text is a **proposal for a future receiving session**. Its presence here does not execute or authorize that session. It intentionally begins with an early stop gate and does not reverse Stage 2 merely because another plan has been written.

```text
Act as my research software collaborator. Read the complete root
DSpaCES_2026_Research_Plan.md, applicable AGENTS.md, reports/STAGE2_DECISION.md,
reports/STAGE1_EVIDENCE_AUDIT.md and both prior novelty audits. Preserve all
existing work. The weighted-provenance sketch and original main study stay stopped.

Implement only the bounded feasibility stage for "When Forecast Contracts
Disagree." The question concerns compatibility and decision ambiguity of
overlapping categorical forecast tables, not a new CI, covariance-sketch,
timestamp, graph-aggregation or selective-Monte-Carlo method.

Authorization when this prompt is explicitly invoked
- Work on main, create no branches, preserve history and unrelated changes.
  Commit and normally push completed code/reports to the existing origin/main.
- Use at most 12 cumulative CPU job-hours and 2 GPU-allocated hours including
  retries, setup, compilation, fitting, verification and warm-up. Reading and
  writing time are separate. Record active GPU time and allocated wall time.
- First spend at most 4 CPU job-hours on novelty/correctness before observational
  fitting. Stop early if the empirical question is not defensible.
- The requested hardware assumption is one RTX PRO4500 Generation with 48 GB;
  verify the actual device. Earlier evidence found a 32 GB RTX PRO 4500 Blackwell.
  Use a 24 GiB active-memory ceiling, 20 GB host RAM and 10 GB data/cache cap.
- Reuse the verified BDG2 archive. At most 2 GB additional downloads. No new
  paid resources, organizer contact, submission, deployment or pod lifecycle action.
- No November/December or 2017 outcomes in this pilot. Do not enable the original
  or proposed main study; the hypothetical 24/48-hour budgets are not authorized.

Early scientific gate
- Compare the exact proposed interface with Berrett-Samworth compatibility,
  Doan-Li-Natarajan overlapping-marginal optimization, probabilistic/decision
  reconciliation and current 2026 work. The displayed proposition is an inherited
  robust-regret corollary. Do not claim a new compatibility or fusion theorem.
- Create docs/contract_study/CLAIM_MAP.md and PROOF_AUDIT.md with precise source
  results, full-text access limitations and what empirical finding would be new.
- If only ordinary LP compatibility under new names remains, end with a stop
  report and preserved arithmetic; do not force a pilot or a paper.

Data and information boundary
- Preserve original splits and canonical records. January-September 2016 is
  training. All October is development-exposed; label new October results as
  feasibility, never a fresh confirmatory holdout.
- Select four eight-building portfolios across four sites deterministically
  from training-only quality. Use the frozen 12-pair scope pattern and one seed.
- Define elevated readings by each building's training 90th percentile with
  strict >. Target next recorded hour; use fixed 4:1 review-capacity loss.
  Do not call flags faults, counts kWh, or cost measured savings.
- Use the same common calendar/causal-count context for every provider and
  consumer. Keep lag windows inside their split with the seven-day embargo.
  Exclude unresolved local-time transitions and missing targets; never fill labels.
- Primary providers get approximately 180 training days, minimum 160, by the
  prespecified stratified allocation. Do not make pools tiny to create contradictions.
- Separate provider raw access, consumer messages/public context and evaluator
  outcomes. All consumer baselines get the same identifiers and historical feedback.

Implementation
- Implement typed four-cell messages, exact scope and threshold IDs, common
  conditioning checks, target/cutoff/arrival semantics, immutable IDs and revisions.
  No recursive forwarding. Deduplicate packets identically for all methods.
- Implement finite state enumeration and A, feasibility P(b,r), minimum additional
  cell tolerance, and a separating witness. Never silently repair an incompatible
  bundle and continue claiming the original contract held.
- Implement exact CPU LPs for pairwise expected-loss differences, minimax regret,
  minimax expected loss and count tail intervals. Record primal/dual gaps.
- Any accelerated solver must match the same objective and yield verified
  bounds. Explain exact-arithmetic versus floating-point guarantees. Do not call
  a successful tolerance test a numerical proof.
- Use primary r=.025 and controls 0,.10 as contract sensitivities, not real
  conditional confidence bands. Hoeffding radii belong only in the iid controlled
  model with explicit finite-family failure allocation.
- Implement competent coherent repair, a history-trained coherent dependence
  model, the direct 0.8-quantile decision competitor, seasonal count prediction,
  deduplicated independence and a tree reference. Share the same representative
  joint forecast between the point-action and robust-action comparison.
- On incompatible or unresolved bundles use a frozen coherent fallback. Score
  every fallback; no selection of only accepted targets.

Meaningful checks
- Reproduce the 7/60 minimum repair example and the parity example's minimax
  regret action 2, bound .25, versus minimax-loss action 3, loss 1.5.
- Validate dual witnesses and regret brackets against exact finite references,
  including duplicates, zeros, redundant constraints and nearly feasible tables.
- Check coherent-derived tables, shared-pool and tree controls. A coherent
  bundle must not produce an unexplained incompatibility certificate.
- Separately label correlated-sample, biased-pool and wrong-conditioning
  assumption failures. Do not infer real conditional validity from calibration.
- Check forbidden raw/future accesses and invariant final active-message state
  after retransmission/permutation/revision replay.

Pilot and cost
- At most 256 October targets per portfolio across all roles. October 8-14 fits
  permitted consumer/calibration parameters, 15-21 supplies interval corrections,
  22-31 scores. Keep all roles and exact sample counts in the manifest.
- No injected probabilities in the primary observed-data pilot. Stress faults
  cannot supply the main contribution. Report all three tolerance settings.
- Measure whether natural incompatibility/ambiguity survives strong calibration
  and changes decisions. Compare full policy loss and interval score/coverage,
  including fallback rates. Treat short-block uncertainty as descriptive.
- Only if the CPU scientific gate survives, compare matched complete CPU/GPU
  costs for the same saved bundles: setup, parsing, transfer, optimization,
  verification, serialization, cold/warm p50/p95, throughput, RAM/VRAM and bytes.
  Count verified targets, not iterations. Avoid unbounded GPU tuning.

Finish with
- reports/contract_study/FEASIBILITY_REPORT.md and PILOT_DECISION.md, giving one
  continue/simplify/stop judgment, actual counts, assumptions and closest baseline.
- Frozen configs, source/access/seed manifests, environment lock, resource
  ledgers, small numerical outputs and two honest reproducible pilot figures.
- A measured projection of the proposed main matrix, at most 24 new GPU-hours
  including this pilot, and a disabled ready-to-run command for later approval.
- A stop recommendation if only synthetic conflicts, vacuous intervals or
  established mathematics survive. No full manuscript, Stage 3 or background run.
- Report commit/push status, sealed-date status and the pod's remaining allocation.
```

## 17. What this plan does and does not establish

The data source is accessible and its schema supports the outcome. The finite example and proposition are auditable, and the proposed experiment is scientifically distinct from BDCC. Current workshop dates and submission timezone were verified. The repository's prior pilot evidence, license discrepancy and hardware mismatch are incorporated rather than erased.

What is **not** established is a new general theorem, naturally occurring decision-relevant incompatibility in these forecasts, practical superiority to coherent reconciliation, useful real conditional coverage or GPU acceleration. This is therefore a complete, bounded design for deciding whether one new contract study merits a ten-page paper. It is not a promise of publication and not a reason to reopen a failed method. If a guaranteed publishable contribution with a genuinely new theorem and useful GPU acceleration is required before a pilot, the present evidence supports deferral.
