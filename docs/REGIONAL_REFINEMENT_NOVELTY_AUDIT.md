# Refinement literature and candidate contribution

Checked September 23, 2026. Full author PDFs were retrieved for the seven core
works below, rather than inferring capabilities from titles. The HTML arXiv
endpoints for the three Katzfuss papers failed; their PDFs succeeded. The recent
decentralized paper was read in publisher HTML, whose extracted mathematical
notation is incomplete. Its supplement was not audited, so no detailed theorem
equivalence claim rests on that source.

“Not evaluated” below means the cited sections do not demonstrate that property;
it is not a proof that the method cannot provide it. GPU suitability is **our
implementation inference**, not a hardware result claimed by these papers.

| Closest primary source; version/sections inspected | Refinement/coarsening and uncertainty | Incremental evidence and data access | Locality and GPU assessment; remaining distinction |
|---|---|---|---|
| Katzfuss, [M-RA author PDF](https://arxiv.org/pdf/1507.04789), v2 Dec 7 2015; published JASA 112(517), 201-214, 2017, [DOI](https://doi.org/10.1080/01621459.2015.1123632). Sections 2.2-2.5, 3.1-3.6. | Multiresolution basis model and coherent posterior within that approximation; partitions/knots fixed in the described inference. Online eviction/reopening policy not evaluated there. | Upward sufficient quantities and downward conditional prediction; distributed computation. | Limited-support bases and hierarchical conditional structure permit recursion. Block algebra is GPU-suitable in principle. Our selective evidence replacement/cache experiment is a systems question, not new multiresolution Gaussian inference. |
| Jurek & Katzfuss, [MRF author PDF](https://arxiv.org/pdf/1810.04200), v2 Nov 13 2019; [JCGS 30(4), 1095-1110, 2021](https://doi.org/10.1080/10618600.2021.1886938). Algorithms 1-2, Sections 4.1-4.3, 5.2. | Multiscale probabilistic filtering; resolution controls approximation. Exact only in identified special cases; ordinarily reapproximates forecast covariance. | Sequential assimilation with changing measurements; not an arbitrary same-evidence detail-cache service in the inspected sections. | Linear/quasilinear cost requires restricted local evolution and bounded multiresolution rank. GPU block algebra is plausible, not a result verified here. Our exactness is for a smaller fixed model; it does not supersede MRF. |
| Jurek & Katzfuss, [hierarchical sparse Cholesky PDF](https://arxiv.org/pdf/2006.16901), v2 Sep 23 2021; [Statistics and Computing 32,15, 2022](https://doi.org/10.1007/s11222-021-10077-9). Propositions 1-4, Sections 3 and 5, proof discussion. | Hierarchical Vecchia assumptions make covariance and precision Cholesky factors sparse; posterior pattern preservation requires the stated observation structure. | Sparse filtering and extensions through Laplace approximations. Dynamic arbitrary resolution changes not demonstrated in the inspected results. | Sparsity is conditional-model structure, not a generic property of Gaussian updates. GPU sparse/batched solves are plausible. Our dense common separator is simpler and potentially limiting; no new sparse-factor theorem. |
| Domschke et al., [author PDF](https://arxiv.org/pdf/1701.09031), v1 Jan 31 2017; [ETNA 48,97-113, 2018](https://emis.de/ft/18670), DOI 10.1553/etna_vol48s97. Sections 2-3 and adaptive flowchart. | Actual model/mesh/time refinement and coarsening driven by functional error estimates, with re-simulation. | Physical gas-flow model hierarchy; Bayesian acquisition/retraction is a different operation. | Local error estimates guide model/discretization choices, but network simulation remains coupled. GPU performance not demonstrated in these sections. Our fixed-model posterior refinement must not be presented as their model-adaptivity result. |
| Kaess et al., [iSAM2 author PDF](https://www.cs.cmu.edu/~kaess/pub/Kaess12ijrr.pdf), [IJRR 31(2),216-235, 2012 record](https://www.cs.cmu.edu/~kaess/pub/Kaess12ijrr.html). Sections 3.1-3.3, Algorithms 4/6, Section 5.2. | Bayes-tree conditional densities and sparse factorization; exact linear elimination, with separate nonlinear relinearization policy. | Incremental factors edit affected cliques and ancestors while preserving orphan subtrees and cached messages. | Separator size, ordering and fill-in determine locality; loop closure can touch a large region. Irregular trees need specialized GPU scheduling. This is the strongest conceptual competitor: retaining/reusing conditionals is already established. Our star-message baseline grants that reuse. |
| Wickramasuriya, Athanasopoulos & Hyndman, [MinT full author PDF](https://robjhyndman.com/papers/mint.pdf), Jan 23 2018; [JASA 114(526),804-819, 2019](https://robjhyndman.com/publications/mint/). Theorem 1, Sections 2-3, Appendix A. | Reconciles forecasts under exact summation constraints, minimizing trace under unbiasedness/covariance assumptions. | Does not itself specify acquisition or replacement of observation likelihoods. | Matrix projection is GPU-suitable; covariance estimation and dense coupling matter. Algebraic aggregation coherence is already standard. We derive queries from one joint model rather than claiming a new reconciliation theorem. |
| Katzfuss & Hammerling, [full author PDF](https://arxiv.org/pdf/1402.1472), [Statistics and Computing 27,363-375,2017](https://doi.org/10.1007/s11222-016-9627-4), online Feb 9 2016. Algorithm 1, Sections 3,5,6 and Algorithm 3. | Exact distributed inference relative to a low-rank model with fine-scale variation; full joint prediction requires appropriate conditional terms. | Local R_j/gamma_j summaries yield the same posterior as centralized computation; communication independent of data count at fixed rank. Temporal extension includes filtering/smoothing. | Conditional private structure and fixed rank provide locality. This is the **implemented nearest mathematical baseline**, extended with temporal household residuals. Ordinary sufficient-statistic exchange is therefore not our contribution. |
| [Fully decentralized inference for spatial data using low-rank models](https://doi.org/10.1093/jrsssb/qkag113), JRSS B, published July 10 2026, accepted June 24. Publisher Sections 3-4 and Theorem 4 discussion. | Low-rank inference with decentralized parameter estimation and consensus; regularity assumptions matter. | Removes a central optimizer and studies estimator convergence; not an observed London federation. | Approximate linear convergence and asymptotic equivalence require the stated communication/regularity assumptions. Extracted equations were incomplete; supplement not audited. Our single-GPU replay demonstrates neither decentralization nor availability/resilience. |

## Narrow question retained for this bounded test

Can a consumer retain exact laws for a small registered regional/group forecast
set while evicting household conditionals, then reacquire selected local evidence
under versioned replacement without losing information or double counting?
Measure resident state, source access, reconstruction and forecast quality against
ordinary cached incremental messages and a streamed all-fine reference.

The possible contribution is an **empirical characterization of that contract
and its storage/reread tradeoff** under an explicit regional household model.
The registered-query proposition in the theory file is a standard Gaussian
sufficient-information corollary. Source count, public data volume, one GPU and
passing identities do not establish publishability. A conventional method can
implement exactly the same eviction policy; any claim of a new inference
algorithm would fail this audit.

Falsifying tests: if streamed fine inference has comparable working memory, do
not claim greater representable population. If query-preserving eviction merely
trades the expected cache bytes for extra reads, report that inherited tradeoff.
If uncertainty-guided access does not improve observed query quality over a
random policy under the same access cap, withdraw an adaptive-policy benefit.
If coarse summaries already predict the regional outcome as well, investigate
only a justified local-query capability; do not select favorable buildings or
increase latent complexity to manufacture a gain in this stage.

## Separation from BDCC

The authoritative adjacent file
`../EAI-BDCC2026/research_plan/EAI_BDCC_2026_Research_Plan.md` was available and
read. Its title is *When Averages Hide Congestion*. It uses PEMS-BAY/LargeST,
Matheron conditional simulation, graph dynamics, a structural-defect enclosure,
coarse/fine threshold certificates and observation-versus-simulation allocation.

| Dimension | BDCC | This fixed-model refinement pilot |
|---|---|---|
| Question | Local traffic information versus number/resolution of rollouts | What must be retained or reread to change represented household detail consistently? |
| Failure | Averages conceal graph configurations relevant to a future event | Eviction loses conditionals; derived aggregates and revealed constituents can be counted twice |
| Object | Quotient graph, defect matrix, trajectory radii | Gaussian separator messages, conditional query laws, evidence versions |
| Computation | Conditional samples, coarse enclosure, selective fine simulation | Deterministic elimination, atomic likelihood replacement, cache eviction/restoration |
| Outcome | Sustained congestion risk | Household/group/regional half-hour energy at fixed forecast leads |
| Main evidence | Held-out traffic forecasts and certified event agreement | Q1 London exploratory replay, posterior round trips, measured storage/read costs |

Both use general conditional probability, but this pilot has no graph enclosure,
scenario generation or simulation-count allocation. Do not import those claims
or disguise information-versus-Monte-Carlo experiments as refinement evidence.
