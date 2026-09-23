# When Agreement Reuses Evidence

## A bounded plan for conservative fusion with compact weighted provenance

Prepared September 22, 2026. Target: DSpaCES 2026, a workshop of IEEE Big Data 2026. Hardware assumption: RTX PRO 4500 1x , to be verified on the execution machine.

This is a prospective research plan. No dataset has been downloaded, no model has been trained, and no GPU experiment has been run in this planning session. Small CPU calculations checked the illustrative example, dimensions, deadline conversion, budget totals and the algebraic risk inequalities on 20 small cases. They are not experimental evidence or a statistical verification of the projection probability.

The supplied DSpaCES planning prompt was read before the complete attached BDCC plan. The latter, titled "When Averages Hide Congestion," defines the exclusion boundary below.

## 1. Recommendation

Study **whether compact, weighted provenance can preserve conservative uncertainty when several building-energy forecasting twins reuse observations**. The consumer receives predictions and bounded metadata, rather than every underlying training record and influence coefficient.

The central failure is false corroboration. Several forecasts can agree because their estimators use overlapping evidence. Independence-based fusion can then report uncertainty much smaller than its actual prediction error. Merely removing repeated network packets does not address partially overlapping derived estimates.

Do not advertise a new general method for correlated fusion. Covariance intersection, split covariance intersection, conservative robust optimization, and covariance sketching already exist. Recent work explicitly handles known correlated error components. The narrower proposed contribution is a **finite-horizon communication contract and an explicit compression-to-risk bound for weighted influence sketches**, followed by a real-data test of whether that contract is useful.

Use Building Data Genome 2 (BDG2) electricity observations. Forecast each building's next recorded hourly consumption. Simulate independently administered providers by assigning overlapping historical evidence to separate forecasting processes. The original measurements and held-out outcomes are real. Provider organizations, sharing policies, and delivery patterns are experimental constructions.

**My recommendation is to fund the bounded pilot, not to assume a successful paper.** This direction is distinct from BDCC and mathematically tractable, but has two material risks. First, the theorem may be judged a straightforward synthesis of established sketching and conservative estimation results. Second, common future uncertainty may dominate the effect of training overlap. Both must be tested early. A generic "provenance helps" demonstration is insufficient.

### Three proposed contribution statements

1. **Theory.** We derive a uniform conservative risk bound for simplex-weighted fusion using independently computed, shared-seed sketches of signed influence lineage. The result separates sketch error, unresolved residual dependence, and irreducible common future uncertainty. It bounds excess conservative risk relative to an exact-influence reference and remains valid after the consumer optimizes fusion weights using the sketches, under stated nonadaptivity assumptions.
2. **Method and contract.** We implement a versioned evidence-exchange protocol that makes these assumptions explicit, including canonical record identities, estimator lineage, exact influence norms, a finite sketch validity horizon, and rules for duplicate or superseded messages. We measure metadata and computation against compressed exact lineage and established dependence-aware fusion.
3. **Evidence.** We evaluate coverage, interval score, forecasting error, and an energy-reservation loss against held-out real meter observations, with controlled changes in evidence sharing. Batched GPU replay quantifies the cost of provenance-aware composition as provider count and lineage length grow.

These are intended claims, contingent on the gates in Section 14. The proof below is auditable; its originality and practical value remain provisional. A successful prototype does not establish an operational multi-organization deployment.

## 2. Venue and submission conditions

The official workshop page and its actual submission portal were checked on September 22, 2026. [C1-C3]

| Item | Verified position |
|---|---|
| Venue | Fourth IEEE International Workshop on Dataspaces and Digital Twins for Critical Entities and Smart Urban Communities, co-located with IEEE Big Data 2026 |
| Workshop date and mode | December 14, 2026, fully online; the page specifies Zoom |
| Submission deadline | October 15, 2026, 11:59 pm Anywhere on Earth, explicitly stated by the workshop submission portal |
| UTC conversion | October 16, 2026, 11:59 UTC. Use October 14 as the internal completion deadline |
| Full paper | Up to 10 pages including references |
| Short/position paper | Up to 5 pages including references, according to the workshop-specific page |
| Format | IEEE two-column conference proceedings format using the official linked template |
| Notification | November 5, 2026 |
| Camera-ready | November 20, 2026 |
| Registration | Workshop page gives November 26 as a strict deadline and requires at least one author at a full author registration rate |
| Possible waiver | The page says a registration waiver is expected, with details to come. It is not confirmed and conflicts with treating registration as already free |

Submit through the [DSpaCES-specific CyberChair portal](https://wi-lab.com/cyberchair/2026/bigdata26/scripts/submit.php?subarea=S53&undisplay_detail=1&wh=/cyberchair/2026/bigdata26/scripts/ws_submit.php), not the main research track. The generic camera-ready page covers workshops and calls for IEEE-compatible PDF validation, electronic copyright, final PDF submission, and a registration receipt. It also offers an in-person presentation selection. Its generic extra-page option does not authorize exceeding this plan's 10-page workshop target. [C2-C3]

**Unresolved publication details.** A live versus prerecorded author presentation requirement, duration, no-show exclusion rule, and the application of any waiver were not recoverable from the retrieved instructions. The linked Cvent author-information page returned no readable content. Plan for author participation online, but do not assert that acceptance alone guarantees publication. No organizer was contacted. Recheck these items before user-controlled submission and registration.

**Exact workshop fit.** The primary themes are provenance and lineage, data quality, interoperable data exchange, and composition of distributed or federated twins. The energy application supplies a decision-support setting. Synchronization is a contract precondition, not a second research contribution. Privacy, security, and infrastructure resilience are not demonstrated simply by withholding raw observations.

## 3. Substantial boundary with the BDCC project

| Dimension | Attached BDCC project | Proposed DSpaCES project |
|---|---|---|
| Question | When should a traffic twin retain local measurements rather than simulate more scenarios? | What uncertainty can a consumer safely report when derived forecasts reuse evidence and detailed lineage is expensive to exchange? |
| Failure mechanism | Spatial/temporal aggregation conceals configurations relevant to congestion | Correlated estimation errors are counted as independent corroboration |
| Mathematical object | Graph quotient, structural-defect matrix, rollout error radii and threshold-event enclosure | Signed influence vectors, sketched Gram matrix, covariance ambiguity and conservative fusion risk |
| Proposed result | A graph aggregation enclosure and coarse/fine event certificate | A uniform compression-to-risk inequality under an explicit metadata contract |
| Algorithm | Conditional reconstruction, coarse simulation and selective fine evaluation | Independent local estimation, compact influence exchange and a small convex fusion problem |
| Main data | PEMS-BAY speeds; LargeST flows for scale | BDG2 electricity-meter observations |
| Outcome | Sustained future congestion event | Future recorded hourly electricity consumption and reservation error |
| Intervention | Observation retention, aggregation and simulation budget | Provider evidence overlap, lineage representation and controlled message duplication |
| GPU work | Conditional sampling and graph scenario rollouts | Batched influence construction, Gram matrices, optimization and message replay |
| Evaluation | Brier score, warning performance and computation-to-error | Coverage with sharpness, proper interval score, MAE, decision loss and metadata cost |
| Main figures | Equal aggregates, different traffic; local detail versus scenarios; enclosure efficiency | Shared evidence diagram; real forecast episode; coverage versus overlap; quality versus provenance bytes and complete cost |

Removing the titles and domain labels leaves different questions, equations, algorithms, and experimental interventions. There is no graph enclosure, Matheron reconstruction, selective refinement, or information-versus-simulation allocation in the proposed DSpaCES method. Generic logging, plotting and budget utilities may be reused with attribution.

## 4. Candidate comparison and choice

These are judgments, not measured scores.

| Candidate | Scientific role of the data space | Main opportunity | Main problem | Decision |
|---|---|---|---|---|
| A. Dependence-aware evidence exchange | Providers communicate what permits or limits a consumer's fusion | A precise link between compressed weighted lineage and conservative prediction error | Mature fusion and sketching literature; practical overlap effect may be small | Choose, with early novelty and usefulness gates |
| B. Event-time consistency | Consumers must align target times and temporal support across asynchronous messages | A useful study of decision degradation from inconsistent snapshots | Age-of-information and out-of-sequence estimation are mature; BDG2 lacks actual delivery timestamps | Keep fixed in the main study; no new synchronization theorem |
| C. Operational data contracts | Consumers reject unit, coverage or target mismatches before composition | Clear engineering usefulness and good workshop fit | Validation rules alone offer limited mathematical novelty; injected faults could dominate the evidence | Use as protocol infrastructure, not the main contribution |

A is viable only in the narrowed form. Reject the broad proposal "use provenance plus covariance intersection" because it repackages existing techniques. Do not rescue a failed A by adding all of B and C to the same 10-page paper.

## 5. Closest primary literature and novelty audit

The review searched classic foundations and 2024-2026 sources. It located the following twelve directly relevant papers. Full-text access was strongest for conservative optimization, the 2024/2025 correlated-component papers, the 2026 optimization preprint, provenance semirings, Johnson-Lindenstrauss projection, and approximate matrix multiplication. Where only a primary abstract or bibliographic record was accessible, that limitation is explicit. No absence claim is based on a failed search.

| Source | Existing result or assumption | Proposed difference and required evidence |
|---|---|---|
| L1. Julier and Uhlmann, 1997, *A Non-divergent Estimation Algorithm in the Presence of Unknown Correlations* | CI combines estimates conservatively without known cross-covariances. Bibliography checked on an author page; the original full text was not retrieved. Its formulation is also presented in L6 | CI is a baseline. Any tighter result uses additional declared information. Demonstrate useful coverage/sharpness at its metadata cost |
| L2. McLaughlin, Krishnamurthy and Challa, 2003, *Managing Data Incest in a Distributed Sensor Network* | Repeated information in decentralized Bayesian estimation is an established failure. A primary proceedings source was located, but full retrieval failed | No novelty in identifying double-counting. Distinguish retransmission from partial overlap of signed estimator influences; obtain the full paper in the novelty gate |
| L3. Ajgl and Straka, 2022, *Covariance Intersection Fusion with Element-wise Partial Knowledge of Correlation* | Uses known entries of joint error structure and constructs conservative bounds, explicitly considering configurations up to four estimates. Institutional abstract retrieved; full-text link led to login | The gap is how bounded exchange obtains uncertain covariance information, not conservative use of partial covariance itself. Compare the sketch-induced uncertainty set with this formulation |
| L4. Forsling et al., 2022, *Conservative Linear Unbiased Estimation Under Partially Known Covariances* | General robust optimization for conservative linear estimation, including existing fusion methods as special cases. Full author postprint inspected | Treat the minimax objective as inherited. The proposed deliverable is an explicit, easily evaluated compression penalty and its protocol assumptions, not a new general robust estimator |
| L5. Cros et al., 2024, *Split Covariance Intersection with Correlated Components for Distributed Estimation* | Introduces treatment of known correlated components beyond standard SCI. Author preprint inspected; cite its verified publication status when drafting | Merely separating known and unknown error components is already covered. The compressed and probabilistic metadata constraint is the possible difference |
| L6. Cros et al., 2025, *Revisiting Split Covariance Intersection: Correlated Components and Optimality* | ESCI includes known correlated components and proves optimal conservative bounds for two estimators. Full text inspected; IEEE TAC publication verified | Do not claim superiority to its two-estimator theorem or arbitrary vector fusion. Compare exact and compressed influence information under the same restricted scalar task |
| L7. Hao Li, June 2026 preprint, *Guaranteed Fast Implementation of the Split Covariance Intersection Filter* | Fourth-order convexity supports a nested Newton optimization of SCI weights. Full preprint inspected; peer review not established | Ordinary batching or a faster weight search is not the novelty. Use a competent optimized CPU solver and document convergence |
| L8. Bates and Granger, 1969, *The Combination of Forecasts* | Forecast-error covariance informs forecast combination. Primary publisher abstract retrieved | Neither combining forecasts nor exploiting error correlations is new. A learned covariance combination is an essential practical competitor |
| L9. Ledoit and Wolf, 2004, *A Well-conditioned Estimator for Large-dimensional Covariance Matrices* | Shrinkage stabilizes covariance estimation. Publisher and author abstracts retrieved; PDF retrieval failed | A noisy sample covariance is too weak a comparator. Test shrinkage with the same historical forecast outcomes and calibration allowance |
| L10. Green, Karvounarakis and Tannen, 2007, *Provenance Semirings* | Algebraic lineage records how outputs derive from inputs. Full author paper retrieved | A lineage expression does not itself specify an error distribution. Define the extra signed sensitivity and noise assumptions rather than claiming logging is new |
| L11. Dasgupta and Gupta, 2003, *An Elementary Proof of a Theorem of Johnson and Lindenstrauss* | Low-dimensional random projections preserve a finite set of geometrical relationships. Full author paper retrieved | The concentration inequality is inherited. Derive its explicit consequence for optimized conservative fusion, finite validity, and unresolved common errors |
| L12. Mroueh, Marcheret and Goel, 2017, *Co-occurring Directions Sketching for Approximate Matrix Multiply* | Streaming matrix-product and covariance approximation with error guarantees. Full proceedings paper retrieved | Covariance sketches are established. Independently produced messages must use compatible sketches without centralized access to all provider matrices. Compare compact exact alternatives and explain this access constraint |

### What might be new, and what is definitely not

The proposed mathematics combines a standard projection guarantee with a conservative error decomposition. The specific result includes a finite-message validity scope, optimization after sketch observation, a residual-dependence term, and a risk gap relative to exact weighted lineage. This is a plausible workshop contribution only if the exact interface and its useful operating regime are not already established and the real-data comparison is informative.

The proof is short because it uses known ingredients. Do not describe it as a new Johnson-Lindenstrauss theorem, a new CI family, a general privacy mechanism, or a new principle of forecast combination. The novelty gate must compare the displayed result directly against L3-L6 and communication-constrained covariance estimation, rather than compare only titles.

Reserve at most one working day for this audit, including full retrieval of L1-L3 and L9 where possible. If an equivalent theorem and interface exist, cite them and evaluate whether the observational result independently merits a case-study paper. If neither theory nor empirical result is distinctive, stop the intended full paper.

## 6. What is exchanged and who knows what

### 6.1 Physical target and access boundary

For building b, let Y_(b,t+1) be its next recorded hourly electricity consumption in kWh. The target is a reported meter interval, not an inferred instantaneous physical demand. A provider forecasts the same building, target interval and unit as every other provider participating in that query.

Each simulated provider controls a local evidence set S_i, a linear forecasting model, and its local influence calculation. The consumer can request forecasts and metadata but cannot fetch raw training measurements through the main fusion interface. An offline evaluator can access all original records and future observations for scoring. That evaluator privilege must not leak into consumer code.

Use four providers per building in the primary experiment. They represent separate service roles, such as a facilities analyst and forecasting contractor, but are **not asserted to be actual BDG2 organizations**. Eight providers are a secondary setting. Larger provider counts are explicitly engineering stress.

The data space has a scientific role because the allowable exchange determines which uncertainty calculation the consumer can perform. An ablation changes the exchange contract while holding forecasts and observed outcomes fixed.

### 6.2 Distinct dependency mechanisms

| Mechanism | What can be known | Required treatment |
|---|---|---|
| Retransmission | Same immutable message identifier and content | Accept once; all baselines use the same deduplication rule |
| Exact derived duplicate | Same estimator, target, evidence digest and version | Collapse using the same available fields for every method |
| Partial reuse of observations | Overlapping evidence identities with possibly different signed influence | Account for weighted overlap; a count or Jaccard score is insufficient |
| Shared prior or pretrained model | Model hash and declared prior ancestry | Primary model uses no shared pretrained neural prior; a hash does not quantify uncertainty |
| Distinct but statistically dependent measurements | Residual covariance or a valid error model | Disjoint identifiers do not establish independence; allocate unresolved dependence explicitly |
| Shared future prediction noise | All providers predict one future observation | Include its variance once as a common term; never divide it by provider count |
| Different target windows or ages | Target support, observation cutoff, issue time and arrival time | Reject incompatible target support; primary study keeps age fixed |

### 6.3 Minimum message and update rules

Every message contains a protocol version, provider identifier, building identifier, target interval identifier, kWh unit, evidence cutoff, issue and arrival times, model version, forecast mean, exact influence norm, residual uncertainty allowance, common-noise contract identifier, sketch length, sketch seed/epoch identifier, sketch vector, evidence-set digest, and immutable message identifier. Digest equality helps identify exact repeated supports; it gives no partial-overlap estimate.

Providers use canonical record identities based on dataset version, meter identity, timestamp/row disambiguator, and measurement kind. A corrected value gets a versioned record identity and explicitly supersedes the earlier one. Within a local fit, each canonical record appears once. A shared seed maps the same record to the same random vector at every provider.

For a given provider, model version and target, accept one active message. A higher explicit revision supersedes the previous revision; an old arrival does not become fresh evidence. Exact duplicates are discarded before numerical fusion. In the primary experiment there is no recursive forwarding of fused estimates. Adding such forwarding would require carrying the complete induced influence and residual-dependence structure, not assigning a new independent identifier.

Validate schema, units, target support, common-noise convention and sketch epoch before composition. Messages with incompatible sketch seeds cannot be combined by dot product. If the finite query horizon is exhausted, start a new declared epoch with a new probability allocation or remove the finite-horizon guarantee.

The providers are trusted to report norms, model versions and lineage correctly. Content hashes check identity, not the truth of a variance decomposition. Sketches can reveal similarities and aspects of training membership. There is no differential privacy, secure aggregation, secrecy, or regulatory-compliance claim.

## 7. Mathematical formulation and proposed result

### 7.1 Restricted error model

Suppress b and t for one target. Provider i reports m_i. Its error relative to the observed target Y is

    e_i = m_i - Y = a_i^T xi + u_i - nu.

Here a_i is a signed vector over canonical evidence innovations, xi has mean zero and covariance identity, u is an unresolved zero-mean error vector, and nu is the future innovation shared by every predictor of Y. Assume

    Cov(xi, u) = 0,
    Cov(xi, nu) = 0,
    Cov(u, nu) = 0,
    Var(nu) = v >= 0,
    Cov(u) = U >= 0 with U_ii <= r_i^2.

The notation U >= 0 means positive semidefinite. The influence vectors and variance allowances are fixed conditional on design information independent of these error draws. All providers estimate the same target without bias under this model.

These assumptions are substantive. Record IDs index independent innovations only when a correct noise model makes them so. Correlated original records require an appropriate factorization before a_i can have this interpretation. Unmodeled dependence cannot be made valid merely by renaming the records. Estimated residual allowances and real-world model bias are not covered automatically.

Let A have rows a_i^T. Restrict fusion to the probability simplex

    W = {w: w_i >= 0 and sum_i w_i = 1}.

The fused forecast is m(w) = sum_i w_i m_i. Its worst-case variance over the stated residual ambiguity set is exactly

    R(w) = ||A^T w||_2^2 + (r^T w)^2 + v.                 (1)

To see this, PSD implies |U_ij| <= r_i r_j, so w^T U w <= (r^T w)^2. Equality is attained by U = r r^T, which is admissible. This conservative optimization is established reasoning, not the novelty.

Nonnegative weights simplify the proposed method and interpretation. Unrestricted signed GLS is allowed as a separate reference, but the displayed quadratic bound and excess-risk claim apply to W. Do not silently compare its optimum with the unrestricted BLUE and call them equal.

### 7.2 How a provider can calculate a_i

An auditable example is fixed-design ordinary least squares. For provider records S_i,

    y_(S_i) = X_i beta + sigma xi_(S_i),
    beta_hat_i = (X_i^T X_i)^(-1) X_i^T y_(S_i),
    m_i = phi^T beta_hat_i,
    a_(i,r) = sigma phi^T (X_i^T X_i)^(-1) x_r, r in S_i,
    a_(i,r) = 0 otherwise.

If Y = phi^T beta + nu with independent future noise, then (1) applies with r_i = 0. Inputs must have full column rank, sigma is known in the controlled experiment, and the same underlying xi_r is used when providers share record r. For a known nonidentity noise covariance, derive the corresponding influence on whitened innovations explicitly.

This gives signed influence even though fusion weights are nonnegative. The same record can affect two predictions with different magnitudes or signs. OLS covariance identities are background. Ridge, estimated whitening, fitted residual scales, nonlinear features and nonstationarity change the assumptions and are evaluated empirically rather than inheriting this theorem by assertion.

### 7.3 Compact weighted provenance

Draw a shared Gaussian projection G of shape [k, R], with independent entries Normal(0, 1/k), independent of all influence vectors in its declared epoch. R is the canonical innovation universe, not the number of forecasts. Provider i transmits

    z_i = G a_i,        s_i = ||a_i||_2.

The consumer constructs the Gram estimate Khat_ij = z_i^T z_j. A provider need not materialize the complete universe: generate compatible projection columns from a recorded random stream and add the columns for its own records. The theorem uses ideal independent Gaussian columns; a pseudorandom implementation and finite precision need separate verification.

For a declared upper bound T on query sets in an epoch and at most p providers per query, consider all nonzero normalized rows and their pairwise sums and differences. There are at most

    M = T (2 p^2 + p)

such vectors. This is a deliberately loose count. The standard Gaussian norm bound and a union bound imply that, for 0 < epsilon < 1, it suffices to choose

    k >= log(2 M / delta) / (epsilon^2 / 4 - epsilon^3 / 6).  (2)

With probability at least 1-delta over G, simultaneously for all these queries,

    |Khat_ij - a_i^T a_j| <= epsilon s_i s_j.               (3)

The vectors must be fixed independently of G. A predefined replay, or design decisions independent of sketch values, can satisfy this requirement. Providers may not search for adversarial evidence subsets after inspecting the same sketch seed. Unbounded adaptive streams require different analysis and are outside scope. Uniformity over fusion weights is permitted, as shown next.

### 7.4 Proposition and proof

Define the reported conservative objective

    Q(w) = ||sum_i w_i z_i||_2^2
           + epsilon (s^T w)^2 + (r^T w)^2 + v.             (4)

Let w_star minimize R(w) on W. Let w_hat be a feasible solution with

    Q(w_hat) <= min_(w in W) Q(w) + eta_opt,

where eta_opt is an explicit nonnegative optimization gap. On event (3),

    R(w) <= Q(w) <= R(w) + 2 epsilon (s^T w)^2             (5)

for every w in W. Consequently,

    R(w_hat) <= R(w_star)
                + 2 epsilon (s^T w_star)^2 + eta_opt
             <= R(w_star) + 2 epsilon max_i s_i^2 + eta_opt. (6)

**Proof of the projection step.** For nonzero a_i, normalize u_i = a_i/s_i. Norm preservation of u_i+u_j and u_i-u_j, followed by polarization, bounds the inner-product error by

    epsilon (||u_i+u_j||^2 + ||u_i-u_j||^2) / 4 = epsilon.

Multiplying by s_i s_j gives (3). A zero row has an exactly zero sketch and presents no exception.

**Proof of the risk bound.** Let K = A A^T. For nonnegative w, (3) gives

    |w^T(Khat-K)w| <= sum_(i,j) w_i w_j epsilon s_i s_j
                      = epsilon (s^T w)^2.

Adding the inflation in (4) and the identical residual and future terms yields (5). Optimality up to eta_opt gives

    R(w_hat) <= Q(w_hat) <= Q(w_star)+eta_opt,

and applying the upper side of (5) proves (6). Because (5) holds simultaneously over W, selecting w_hat after seeing the sketches does not invalidate this argument. This does not permit influence vectors to be adapted to the same sketch.

**Interpretation.** There is a quantitative price for compressing dependence information. More sketch dimensions reduce the stated penalty through (2), but cannot repair a wrong error decomposition, biased forecasts, understated residual uncertainty, or missing common future noise.

The quadratic in (4) has PSD matrix

    H = Z Z^T + epsilon s s^T + r r^T,

with Z having rows z_i^T. It is a small convex quadratic program. The consumer also knows the exact individual conservative bounds s_i^2+r_i^2+v. It may choose the best of the sketch-fused candidate and the individual candidates by their valid bounds. This guards against unnecessary inflation in trivial cases. The choice must use design/uncertainty metadata, not the realized forecast error. The corresponding risk bound is no larger than that of the original sketch candidate.

Under joint Gaussian errors and weights independent of their realizations, m(w_hat) +/- 1.96 sqrt(Q(w_hat)) is conservative at the usual two-sided 95% level conditional on the successful sketch event. This is repeated-sample coverage over errors at fixed design and projection, not coverage conditional on every realized training dataset. Across sketch randomness the coverage lower bound is at least 0.95(1-delta). Covariance bounds alone do not imply Gaussian interval coverage. With only second moments, Chebyshev gives a valid but potentially useless radius sqrt(Q/alpha). Neither statement is a distribution-free claim for the real meter data.

### 7.5 Dimensions, numerical validity and nontriviality

For p=4, T=2,000,000 queries and delta=0.01 in one epoch, (2) gives approximately:

| k | Sufficient epsilon | Float32 sketch payload, excluding header |
|---:|---:|---:|
| 512 | 0.5322 | 2,048 bytes |
| 1,024 | 0.3444 | 4,096 bytes |
| 2,048 | 0.2326, rounded upward | 8,192 bytes |
| 4,096 | 0.1600, rounded upward | 16,384 bytes |

This is not a promise of tiny metadata. Large uncertainty inflation or short lineage can make sketches unattractive. Each seed/configuration must declare whether delta is per run or allocated across all runs. A paper-wide success probability requires summing the failure allocations, not repeating a per-run 99% claim.

Use FP64 to verify Gram matrices, norms, solver gaps and illustrative examples. An exact-arithmetic proposition plus numerical tests is not an unconditional floating-point certificate. Formal numerical claims require a derived additive dot-product/reduction error allowance in (4), including projection accumulation and serialization error. Otherwise label the implementation's guarantee as mathematical under exact arithmetic, with measured numerical agreement.

The new result should be judged on the explicit risk consequence and validity conditions, not the existence of a random projection. The finite-horizon union bound may be loose. Tightening it is optional and cannot replace the main real-outcome study.

## 8. Illustrative numerical example

Three twins forecast the same next-hour meter value. They report 100, 102 and 110 kWh. Their influence rows are

    a_1 = (sqrt(3), 1, 0, 0),
    a_2 = (sqrt(3), 0, 1, 0),
    a_3 = (0, 0, 0, 2).

The first two reuse one innovation but are not identical estimators or retransmitted messages. All influence norms are 2 kWh. Take r=0 and a common future innovation variance v=1 kWh^2. The true error covariance is

    C = [[5, 4, 1],
         [4, 5, 1],
         [1, 1, 5]] kWh^2.

| Calculation | Forecast | Reported or actual variance |
|---|---:|---:|
| Fully naive independent fusion | 104 kWh | Reports 5/3 = 1.667 kWh^2 |
| Actual variance of that equal-weight forecast | 104 kWh | 3.000 kWh^2 |
| Independence of training errors, but common future noise corrected | 104 kWh | Reports 4/3+1 = 2.333 kWh^2, still below the actual 3 |
| Exact weighted-lineage optimum | 105.2 kWh | 43/15 = 2.867 kWh^2 |
| Conservative scalar CI | Depends on deterministic tie handling | 5.000 kWh^2 |

The exact optimum has weights (4/15, 4/15, 7/15). It reduces the combined weight on the closely related first two forecasts. Packet deduplication removes none of these distinct messages.

For an idealized sketch whose Gram matrix happens to equal A A^T, epsilon=0.2 adds 0.8 kWh^2 because s^T w=2. The reported sketch bound at the optimum is then 3.667 kWh^2, between exact fusion and CI. This is an explanatory arithmetic case, not a sampled result or a claim that k=2,048 guarantees epsilon=0.2 under the preceding horizon. In real sketches the Gram error can have either sign and (5), not this special equality, governs the bound.

The covariance and optimum were checked with a small CPU calculation in this planning session.

## 9. Real data, forecasting task and evidence audit

### 9.1 Verified release and schema

Use the originating [BDG2 repository](https://github.com/buds-lab/building-data-genome-project-2) and its [Zenodo v1.0 release](https://zenodo.org/records/3887306). The latter lists one 595.3 MB ZIP and a checksum. It is a public download, without an application or approval step. GitHub also uses Git LFS, so a small pointer file must not be mistaken for measurement data. Exact downloaded bytes, ZIP contents and hashes still require execution-time verification. [D1-D2]

The published release covers 3,053 meters from 1,636 buildings at 19 sites, with hourly data for 2016 and 2017. The full rectangular grid has 53,561,832 meter-hour positions. Missing positions are not observed readings. This study uses electricity only and must count the actual electricity columns after download, rather than describe all 53.6 million positions as its sample. [D1, D3]

| Data issue | Verified fact and study action |
|---|---|
| File organization | Separate meter-type files under `data/meters/raw/`; building descriptors under `data/metadata/`; weather in a separate directory |
| Measurement schema | A `timestamp` column and one column per building, with hourly readings. Use the documented schema, then check the downloaded header |
| Units | The release's energy-meter files use kWh. Do not substitute unconverted Kaggle competition readings |
| Timestamp semantics | Documentation identifies local-time timestamps; metadata provides site timezones. It does not establish clock accuracy, network arrival time, or an unambiguous DST policy |
| Connectivity | Site and building identifiers are available. There is no verified electrical feeder graph or operational provider network in the release |
| Outcome | Future observed electricity consumption. No outage, equipment fault, intervention benefit, or real dispatch-cost labels are assumed |
| Missingness | The release contains missing values; the additional cleaned version removes outliers and some zero runs. Measure missingness per meter and period after download |
| Data terms | The repository license is labeled Attribution-ShareAlike 4.0, with unusual "Unported" wording. Preserve its exact text and attribution. Do not confuse this with the Scientific Data article's CC BY license |

The schema and cleaning statements come from the project's meter documentation; timezone and identifier fields come from its metadata documentation. [D4-D6] The license can be read directly in the repository. Publish retrieval instructions, code and derived metrics; redistribution is not needed to conduct the pilot. [D7]

The raw folder is already a harmonized release, not untouched instrument output. Its preparation included unit conversion, exclusions and some outlier handling. This constrains tai
l interpretation. Use the raw release for the main evaluation and the cleaned mask only as a sensitivity, since additional cleaning might remove the very large readings the decision metric should assess. [D3]

**Why this dataset fits.** The required target exists in the documented schema, the time span permits chronological evaluation, and no unverified access approval is needed. The paper's site table identifies the Panther site as UCF, which could provide a recognizable talk example if it passes the same selection criteria as other sites. It supplies no special access or evidence about current UCF operations. [D3]

### 9.2 Scope and chronological partitions

Select at most 128 electricity-meter buildings. Use training-only eligibility and a deterministic selection stratified across at least four sites if available. Require enough valid training observations for all prespecified provider allocations and at least 95% valid training hours for the primary cohort. Store the complete inclusion/exclusion list. Do not choose buildings by which method wins.

Use these local-calendar partitions:

| Partition | Dates | Permitted use |
|---|---|---|
| Training | January 1 - September 30, 2016 | Building eligibility, feature transforms, fixed provider evidence pools, local fits and noise-model development |
| Validation | October 1 - October 31, 2016 | Small model/uncertainty choices, solver tolerances and pilot timing |
| Calibration | November 1 - December 31, 2016 | November for historical forecast-error covariance; December for the frozen interval-scale correction |
| Test | January 1 - December 31, 2017 | One final evaluation of frozen configurations, with seasonal breakdowns |

The one-hour targets and any lagged inputs must lie wholly inside their intended split for the main analysis. Use a seven-day embargo at boundaries if the optional lag-168 model is retained; all compared methods use the same eligible target set. No future weather measurements are forecast covariates.

The primary estimator is fixed after training. This makes the influence set and reuse mechanism auditable. A single prespecified refresh using the same rules on later past data is optional only after the main experiment; it requires a new leakage analysis and sketch horizon. Do not adapt models to test residuals while reporting a frozen test.

Treat each local timestamp as a labeled meter interval until DST semantics are resolved. Exclude ambiguous or discontinuous transitions from one-hour targets if necessary. Do not invent UTC precision. No cross-site synchronous physical aggregation is required by the method.

Keep missing targets missing and exclude them from outcome scoring. For the calendar-only model, no meter imputation is necessary for features. For the optional lagged model, require valid lag values or use a documented causal training-fitted fill with missingness indicators. Never interpolate test labels or use a centered filter spanning future observations.

### 9.3 Provider models and realistic sharing conditions

Start with a small linear calendar model, approximately 16-24 fixed features: intercept, daily Fourier harmonics, weekday indicators, annual harmonics, and a limited set of predeclared interactions. Use OLS with QR-based solves where full rank is adequate. Drop redundant features by a training-only fixed rule. Record conditioning. A ridge alternative and lag-24/lag-168 features may be selected on validation if needed for forecast competence, but then label the theoretical connection as an empirical extension.

Each of four providers receives 42 complete or sufficiently observed training days, approximately 1,008 hourly records, stratified across the training period. The exact same valid-record rule applies across providers. Use common-core plus disjoint-private day allocations at common fractions 0, approximately 0.5, and approximately 0.9. Round day counts explicitly and report actual record intersections. Use three predetermined allocation seeds. These rates are experimental conditions, not estimates of real provider sharing.

Keep per-provider record counts fixed in the main overlap comparison. The union then shrinks with increased sharing; report that change rather than implying equal total information. Add one fixed-union redistribution control on the validation panel to distinguish loss of unique evidence from an artifact of a particular allocation rule. If the required disjoint allocations are impossible after filtering, reduce the shared study-wide day count before inspecting test outcomes, not separately for favorable conditions.

For eight providers, use a prespecified smaller evidence allotment, such as 21 days each, when needed to preserve the zero-overlap control. This is a separate provider-count condition with its changed sample size disclosed. The synthetic study can vary provider count and evidence size independently.

The provider model is intentionally simple to expose lineage. Include seasonal-naive and a competent centralized predictive reference as checks that the observation task is sensible. More complex neural models are not a minimum deliverable.

### 9.4 The theory-to-data boundary

Calendar regressions on buildings do not make energy residuals independent Gaussian innovations. Autocorrelation, weather effects, occupancy changes and model misspecification are expected. Measure residual autocorrelation, conditional bias, seasonal variance, and cross-provider forecast-error correlation. Do not assume that standardizing residuals removes their dependence.

Use training out-of-fold residuals to estimate a working scale. The OLS influence formula with this estimated scale is a plug-in model. Use a common future-noise term estimated under the same declared working model for every method that uses that decomposition. Its exact physical separation from model misspecification is not identifiable from one meter series.

For unresolved residual allowances, permit only a small validation-selected global multiplier grid, for example 0, 0.5 and 1 times each provider's training out-of-fold residual scale. This is an empirical sensitivity parameter, not an upper-confidence guarantee for U. Do not claim that subtracting two empirical variance estimates proves orthogonality or identifies the true unresolved variance.

Report raw model intervals and a second, equally calibrated version of every eligible method. Use November to fit historical forecast-error covariance and December to calculate interval corrections after those weights are frozen. The correction uses quantiles of absolute standardized errors, with no test adjustment. Do not fit a combination's weights and calibrate its intervals on the same residuals. Because observations are serially dependent and nonstationary, call this an empirical calibration procedure, not exact exchangeability-based coverage. If formal coverage is desired later, a separate time-series conformal analysis is needed and is outside the minimum study.

The primary real-data question is whether compressed weighted lineage approximates the exact-influence method efficiently and improves the coverage/sharpness tradeoff relative to strong deployable alternatives. It need not beat a privileged estimator with all observations. If weighted training overlap has negligible effect after common future noise is handled, report that conclusion and stop the broad confidence-improvement claim.

## 10. Algorithm, metadata and complexity

### 10.1 Pseudocode

```text
PREPARE_STUDY
    Validate source data, units, local times, missingness and canonical records.
    Freeze training, validation, calibration and test partitions.
    Select buildings using training-only eligibility.
    Create fixed provider evidence allocations and immutable manifests.
    Fit local models and compute influence operators.
    Declare the projection seed, maximum queries, provider cap and failure budget.
    Compute compatible local influence sketches and exact norms.
    Fit only the allowed calibration and baseline covariance estimates.

PROVIDER_FORECAST(provider, target_interval)
    Compute forecast using records and covariates available before the target.
    Compute signed influence sketch and exact influence norm for that target.
    Attach uncertainty convention, model/evidence versions and support metadata.
    Emit an immutable versioned message.

CONSUMER_FUSE(messages, contract)
    Validate target, units, cutoff, versions and sketch epoch.
    Drop duplicate messages and replace superseded provider revisions.
    Check the epoch's declared query and provider limits.
    Form Z, s, r and the common future variance v.
    Form H = Z Z^T + epsilon s s^T + r r^T.
    Solve the convex simplex quadratic to a recorded objective gap.
    Compare its valid bound with the exact individual conservative bounds.
    Return the chosen forecast, raw variance bound, calibrated interval if used,
           weights, active message IDs, metadata bytes and latency components.

EVALUATE
    Join only frozen predictions to eligible held-out observations.
    Score coverage, interval score, sharpness, error and reservation loss.
    Retain separate identifiers for real target, provider allocation and sketch seed.
    Aggregate uncertainty over observed blocks, not over duplicated messages.
```

### 10.2 Precomputation and exact competitors

For fixed OLS features, define the local operator

    B_i = sigma (X_i^T X_i)^(-1) X_i^T.

The influence at feature vector phi is phi^T B_i. Precompute B_i G^T once per provider model, then form target sketches as phi^T(B_i G^T). Compute norms from B_i B_i^T. Use QR-based algebra to avoid an unnecessary explicit inverse. This is ordinary linear algebra and must be counted as provider work.

A low-dimensional regression also permits compact exact alternatives. With accessible support IDs and public design features, exact cross-Gram blocks may be cheaper than repeated sketches. Include bitmaps or interval-coded supports, cached influence operators, and exact cross-Gram sufficient statistics where the access contract permits their construction. A dense list of repeated 64-bit IDs is not a competent compression baseline.

The main sketch interface does not provide raw records or exact support lists. An identifier-rich comparison does provide the same identifiers to **every** eligible method, including deduplication and exact methods. If those identifiers plus public features recover exact influences, the resulting exact method is deployable under that richer contract and must not be mislabeled as impossible or privileged. A pooled model using hidden raw outcomes is a genuinely privileged reference.

### 10.3 Complexity and bytes

With d features, n_i local records, p providers, sketch dimension k and F target queries, an unfactored projection costs O(n_i k) per influence vector. For a fixed linear model, precomputing its feature-to-sketch operator costs approximately O(d n_i k), plus model fitting; each forecast then costs O(d k). Exploit repeated features and compatible cached operators fairly for exact and approximate methods.

The consumer forms a Gram matrix in O(p^2 k), then uses O(J p^2) work for J projected-gradient iterations, plus simplex projections. A reference convex solver verifies the optimum and stopping gap for small problems. Use a primal/dual or Frank-Wolfe gap, not the mere fact that weights stopped changing. Streaming consumer state is O(p k+p^2) per active target.

A per-query float32 sketch needs 4k bytes, exact norms/scales and a serialized header. For comparison, an uncompressed lineage list with n identifiers and scalar weights needs approximately 12n bytes before framing, but this is only a naive upper reference. Measure actual compressed encodings and the cost of parsing them.

Sending an entire d-by-k sketch operator once per model can amortize repeated messages. It also changes the disclosure contract and moves feature evaluation to the consumer. Report both per-message and amortized bytes, including operator transfer, model refreshes, record dictionaries and seeds. Do not count a cached model as free for the proposed method while repeatedly retransmitting exact lineage for the baseline.

## 11. Small, decisive evaluation

### 11.1 Required baselines

| Baseline | Available information | Purpose |
|---|---|---|
| Individual forecasts, seasonal naive, equal-weight ensemble | Same causal inputs or same provider forecasts as applicable | Establish task competence and a strong simple combination |
| Naive independent Gaussian fusion | Marginal forecast variances | Expose the basic failure; not the only comparator |
| Independent training errors plus common future noise | Same working future-noise contract | Prevent a trivial apparent gain from fixing only the shared target innovation |
| Duplicate-aware independence | All the identifiers and digests available under the chosen contract | Remove retransmission and exact derived duplicates fairly; does not treat partially overlapping outputs as removable records |
| Optimized CI | Marginal conservative variances | Dependence-robust baseline; in the scalar case variance minimization can select a single provider, so do not intentionally weaken it with arbitrary weights |
| SCI/ESCI or equivalent conservative optimization | Same justified split-error information under each comparison | Strong dependence-aware comparator. With full K and residual bounds, equation (1) supplies the exact scalar simplex reference; a two-provider ESCI check validates the connection |
| Shrinkage covariance fusion | Historical aligned provider forecast errors on the same allowed calibration dates | Competent empirical dependence estimation; simplex weights for the primary comparison, unrestricted regularized GLS secondary |
| Exact weighted lineage | Exact coefficients or reconstructible sufficient statistics, with its full byte cost | Accuracy and conservatism reference for compression; a richer exchange contract |
| Proposed sketch with inflation | Sketch, exact norms and declared residual/common terms | Main approximate protocol |
| Uninflated sketch | Identical sketch without the epsilon term | Isolate the safety cost; cannot claim the proposition's bound |
| Pooled raw-data predictor | Union of underlying training observations | Privileged predictive reference; not an equal-information fusion method |

For empirical shrinkage, compare a global covariance with a small prespecified calendar-regime version if the calibration sample supports it. Fit these on the same dates available to the proposed method. Cap tuning equally. Report whether the proposed method's advantage disappears when all methods receive empirical calibration.

Do not implement every named variant as a separate research branch. One verified CI implementation, the exact conservative split-error reference, one competent shrinkage implementation, and the core ablations are sufficient. Inverse CI's common-estimate assumptions need not be forced onto the chosen model; discuss it through L5-L6 and add it only if those assumptions actually match the experiment.

### 11.2 Controlled theorem experiment

Generate fixed-design linear regression problems with shared canonical Gaussian innovations, known noise scales and declared residual covariance. Vary p in {2,4,8,32}, common evidence fraction in {0,0.5,0.9}, k in {512,2048}, and residual/common-noise dominance in three fixed settings. This is 72 core condition families if p and overlap are crossed with the three noise settings and two k values. Use at most 20 independent sketch seeds per family and batched error draws only as a secondary diagnostic.

For each condition, compute the true covariance analytically. Verify (3)-(6), exact solver solutions, the common-noise floor and the finite-horizon accounting. An observed violation is counted against its sketch event; a violation of (5) when (3) holds indicates a mathematical or implementation error. Monte Carlo can illustrate Gaussian coverage, but it is not needed to estimate a variance that is known analytically.

Include adversarial numerical cases with zero influence rows, nearly duplicated estimators, negative individual influence coefficients, nearly singular exact covariance and highly unequal scales. Include three deliberate assumption violations separately: correlated "distinct" innovations, unmodeled common errors, and data-dependent selection of evidence after observing the sketch. The theorem is not expected to protect those cases.

### 11.3 Main real-data matrix

Avoid a full Cartesian product. The following limits define a main study, subject to the pilot's measured cost.

| Experiment | Configurations | Scope and evidence |
|---|---|---|
| Primary outcome study | p=4; overlap 0, 0.5, about 0.9; three evidence allocations; k=2,048 for proposed method; frozen baseline set | Up to 128 buildings, all eligible 2017 targets; paired real-outcome comparisons |
| Sketch size | k=512,1,024,2,048,4,096 on one frozen allocation at middle overlap | A predetermined 16-building panel and at most 2,000 origins per building; compression and risk penalty |
| Larger provider panel | p=8, one overlap level, three allocations, adjusted record allotment | Same 16-building panel; state the changed per-provider data count |
| Metadata ablation | ID-only overlap, weighted lineage, shuffled-ID negative control, exact compressed lineage | Panel only; wrong IDs should destroy dependence interpretation |
| Residual/common-noise ablation | With/without known common term, low/high unresolved allowance | Controlled study plus a bounded validation panel; never justify omitting it in the main claim |
| Stream integrity | Duplicate factors 1,2,10; reordered arrivals; explicit revisions | Fixed predictions; all correct implementations should preserve final active-message results |
| Scaling | p=4,8,16,32,64; lineage length 256,1,024,4,096; one k per comparison | Controlled replay, up to 10 million transmitted messages across this package |

The zero-overlap condition should provide little benefit over a correctly specified independence baseline after shared future uncertainty is retained. Identical-estimator conditions should offer no information gain after exact duplicate handling. A working method must not manufacture shrinking uncertainty in either condition.

### 11.4 Metrics and operational decision

The co-primary uncertainty outputs are coverage at 90% and 95% and the normalized 90% interval score. For a central interval [l,u], the interval score at error rate alpha is

    IS_alpha = (u-l)
               + (2/alpha)(l-y) 1{y<l}
               + (2/alpha)(y-u) 1{y>u}.

Report raw kWh widths and building-normalized scores using a training-only scale, plus MAE, RMSE, bias and calibration by season. Average per-building results before pooling across buildings so a large building does not determine the headline. Also show the consumption-weighted alternative explicitly.

For a concrete decision, a consumer reserves q kWh for the next interval. Define

    L(q,y) = c_under max(y-q,0) + c_over max(q-y,0),

with c_under:c_over = 4:1 as a prespecified illustrative planning cost. The optimal quantile under the predictive distribution is 0.8. Choose q from the forecast's calibrated one-sided predictive quantile, with a deterministic nonnegative constraint if appropriate. Score it against the actual meter observation. Costs are study-defined utility units, not measured market tariffs or demonstrated savings.

If high-consumption episodes are displayed, define the threshold from training, such as the building's training 90th percentile. Group consecutive exceedances and report building-days/sites containing them. These are elevated readings, not physical outages or grid emergencies. Continuous forecast scoring remains primary if extreme-event counts are small.

### 11.5 Independent evidence and uncertainty

The same real target can appear under several provider allocations and sketch seeds. It is still one observed target. Aggregate simulation replicates within each real target or retain a crossed analysis; never treat them as extra independent buildings or hours.

For paired performance intervals, resample chronological week blocks while keeping all buildings and all methods for the sampled calendar periods together. This preserves important shared weather/calendar effects. Show site-stratified results and a site-deletion sensitivity. With only a few sites, do not claim broad population independence from 128 buildings. Report both the number of sites and the 52 or fewer test weeks represented.

Use 1,000 CPU block-bootstrap replicates for the final paired metrics. In the synthetic experiment, uncertainty over independently drawn projection matrices is separate from variability of Gaussian errors at a fixed projection. State the two denominators separately.

### 11.6 Predeclared success and falsification rules

The following are practical study criteria, not universal statistical thresholds:

1. No unexplained failure of the exact-arithmetic inequality on inputs satisfying the checked projection event. Any such failure blocks the mathematical claim.
2. At a useful measured metadata reduction, the sketch method should stay within 2% of the exact-influence reference's normalized interval score on the prespecified primary average, with coverage no more than two percentage points lower. Report paired uncertainty rather than turning these thresholds into a significance test.
3. To claim a practical advantage, demonstrate either at least a 5% interval-score or reservation-loss improvement over the strongest deployable equal-access baseline at comparable cost, or a substantial cost reduction with comparable quality. A smaller informative effect may still be reported, but not promoted as operationally important.
4. A sketch compression claim requires a meaningful saving over **compressed/cached exact lineage**, provisionally at least 2x in bytes or complete cost on an identified regime. Beating only an uncompressed list is insufficient.
5. If all coverage improvement comes from a common-future-noise correction, calibration, or intervals becoming very wide, reject the weighted-provenance benefit claim.
6. If the exact-influence method itself offers little useful difference from shrinkage or CI, stop further sketch optimization. Compression cannot rescue an irrelevant source of information.

## 12. GPU work, big-data accounting and bounded budget

### 12.1 Work that can justify the RTX 6000 Ada

Use the GPU for batched local linear algebra, many independent building/provider allocations, constructing projection operators, Gram matrices, and batched small convex problems. The controlled study can examine many admissible correlation structures analytically and use Gaussian draws for illustrative coverage. It does not simulate coarse/fine physical scenarios or selectively refine event trajectories.

A four-provider fusion query is tiny. Expect a competent CPU to be competitive or faster for single queries. The plausible GPU benefit is many-query throughput and projection construction. This is a falsifiable expectation, not a hardware-speedup claim.

| Tensor or state | Example shape and precision | Approximate raw storage |
|---|---|---:|
| Sketches for a target batch | [4,096, 4, 2,048], FP32 | 134.2 MB |
| Consumer Gram matrices | [4,096, 4, 4], FP64 | 0.524 MB |
| Fixed model-to-sketch operators | [128, 4, 24, 2,048], FP32 | 100.7 MB |
| Shared projection over 6,576 time identities, reused per independent building namespace | [6,576, 2,048], FP32 | 53.9 MB per active namespace if materialized |
| Large-provider batch sketches | [512, 64, 2,048], FP32 | 268.4 MB |
| Dense full-release value grid, before masks | [17,544, 3,053], FP32 | 214.2 MB; this does not mean all entries are observed |

Generate and cache projections in chunks. A reused numerical projection matrix across independent building queries is acceptable for a finite-family union-bound analysis if that family is fixed independently of the seed; do not infer statistical independence between sketch failures across buildings. If future work fuses buildings together, their canonical innovation namespaces must remain distinct unless the noise model explicitly links them.

Do not allocate [all_targets, all_providers, all_records, all_sketch_dimensions]. Keep model operators resident where possible and stream targets. Set a 32 GB active allocation ceiling despite 48 GB nominal VRAM. FP32 is the initial throughput path; use FP64 audits and avoid BF16/FP16 for the proposed safety calculation until numerical error is explicitly assessed.

CPU responsibilities include downloading, parsing, canonical IDs, sorting/version resolution, data splits, compression, reference optimization and block bootstrap. Measure host-to-device and device-to-host traffic, serialization and lineage construction. Actual bottlenecks may be provider-side projection work or metadata handling rather than consumer matrix multiplication.

Compare multicore NumPy/SciPy or equivalent BLAS-backed CPU code, eager GPU, and compiled GPU only if compilation can amortize. Use the same numerical precision where meaningful and report any precision differences. Record CPU identity, thread count, GPU device/driver, framework versions, compilation time and warm-up. Report both cold and warm end-to-end p50/p95 latency, queries/second and messages/second. Synchronize device timing properly. A device-only kernel number cannot substitute for complete pipeline throughput.

### 12.2 Honest scale accounting

The published archive is moderate in size, with millions of meter observations and heterogeneous sites, rather than a petabyte system. Big-data relevance comes from archive processing and the growth of composed forecast/lineage streams. If the final processed subset is small, call it a scalable prototype with measured scaling rather than claim production big-data deployment.

At most 128 buildings times 8,760 test hours gives 1,121,280 building-target pairs before missingness and embargo exclusions. Four providers could generate 4,485,120 distinct forecast messages for one configuration. Nine evidence-allocation/overlap configurations do not multiply the unique observed outcomes by nine.

Track actual counts of valid meter records, unique evidence records, unique target observations, provider identities, provider-model versions, active forecasts, duplicate packets, discarded revisions, bytes, peak state and independent observed blocks. At hourly cadence, four providers for 128 buildings average only about 0.142 messages/second. High throughput replay is catch-up or stress processing, not evidence of that native live velocity.

For k=2,048, unamortized sketch vectors alone would exceed 36 GB for the preceding 4.49 million messages. Stream them or exchange cached operators; do not persist every vector by default. Include this cost prominently. A claim that metadata is always negligible would be false.

Scaling axes tied to the contribution are provider count, evidence-lineage length, overlap structure, sketch length and model-refresh frequency. Repeated messages measure processing load. A single-machine replay tests interface semantics, numerical accuracy and computational cost; it does not establish distributed availability, network resilience or organizational interoperability.

### 12.3 Compute caps

| Work package | Maximum GPU-hours |
|---|---:|
| Environment, correctness and bounded pilot | 2 |
| Local model and influence construction | 3 |
| Strong baseline fitting and limited tuning | 3 |
| Frozen real-outcome evaluations | 4 |
| Controlled theorem and assumption-violation study | 3 |
| CPU/GPU and lineage scaling | 3 |
| Minimum ablations | 2 |
| Figure-data regeneration and numerical audit | 1 |
| Reserve for diagnosed failures | 3 |
| **Total ceiling** | **24** |

These are allocation caps, not runtime predictions or an instruction to consume 24 hours. The pilot projects actual costs and can recommend a smaller study. Count fitting, warm-up, compilation and reruns. Track GPU-active timing and GPU-allocated wall time separately; use the more conservative allocated time for the budget.

An optional extension to 48 total GPU-hours would allocate up to 8 additional hours to a fixed later-model refresh, 6 to a stronger forecasting reference, 6 to wider scale measurements and 4 to robustness replication. It is not authorized in this planning session. Do not spend it on a second domain, additional neural architectures or an unbounded search for a winning overlap condition.

Initial pilot storage caps: 2 GB downloaded, 10 GB processed/cache output, and 20 GB host working RAM unless the actual machine supports and needs more. One published ZIP is approximately 0.6 GB. Read its contents before deciding whether additional raw-file retrieval is necessary. Maintain a run ledger and stop cleanly at the cap.

## 13. Figures, tables, paper and talk

### 13.1 Four main figures

Use reproducible Matplotlib or equivalent scientific plotting, vector PDF/SVG, embedded fonts and a colorblind-readable palette. Keep a consistent color for raw independence, common-noise correction, CI, learned covariance, exact lineage and the proposed approximation. Distinguish theoretical bounds from empirical intervals with explicit labels. Do not generate empirical-looking charts before the measurements exist.

| Figure | Precise claim and required data | Axes and uncertainty | Reproducible construction |
|---|---|---|---|
| 1. Different messages, shared evidence | Explain partial overlap and the difference between identifiers and influence. Use the Section 8 example and a small provenance DAG | Topology panel has source IDs and signed edge weights. Beside it, show numerical variance bars in kWh^2, explicitly illustrative | Generate from one checked example configuration; use no real provider logos or invented organizations |
| 2. A held-out building episode | Show whether several agreeing forecasts are incorrectly narrow and whether the correction helps on observed data | Local clock time on x; kWh on y; actual readings and 90% intervals for at most three methods. A second panel shows lineage overlap and missingness | Select the first eligible high-consumption day after a prespecified test date for the first eligible building by sorted ID, before method comparison. Include all selected times, even if visually unimpressive |
| 3. Coverage with sharpness as overlap changes | Determine whether weighted lineage handles the injected sharing mechanism after the common-noise baseline | Actual overlap on x. Separate y panels for 90% coverage and normalized interval score or width. Horizontal nominal-coverage line; paired week-block intervals | Use all frozen primary test targets, aggregate allocation seeds within target, and display actual unique-record counts beneath the axis |
| 4. Quality and complete processing cost | Locate regimes where compressed lineage is worth its overhead | Panel A: normalized interval score versus measured bytes/query, including amortized exact formats. Panel B: completed targets/second versus provider count. Optional inset: p95 single-query latency | Read saved per-stage timing and byte logs. Show CPU and GPU, cold/warm state, replicate timing ranges, hardware and precision |

Figure 1 is illustrative; Figures 2-4 must be generated from retained observations and measurements. If the main result is negative, keep the same figures and change the claim, not the selection rule. Extra sketch-error distributions and assumption failures belong in the repository supplement.

### 13.2 Three tables

| Table | Required content | Purpose |
|---|---|---|
| 1. Data and evidence accounting | Exact dates, sites, buildings, valid records, unique targets, high-consumption groups, provider counts and sharing interventions | Separate observed evidence from simulated federation workload |
| 2. Main outcomes | MAE, 90/95% coverage, normalized interval score, width and reservation loss, with paired uncertainty and information regime | Judge usefulness rather than coverage alone |
| 3. Cost and contract | Metadata available, exact/compressed/cached bytes, projection cost, fusion cost, complete latency, throughput and peak memory | Make additional information and system cost visible |

The long literature table in this plan should become concise related-work prose and a few explicit distinctions in the paper. Do not spend a page reproducing all planning tables.

### 13.3 Ten-page full-paper allocation

Working title: **When Agreement Reuses Evidence: Conservative Fusion for Federated Building Twins**.

If communication is the successful result, use **Compact Weighted Provenance for Conservative Twin Fusion**. If only the diagnostic survives, use a title that describes the observed limitation rather than implying successful correction.

| Component | Pages, including figure/table footprint |
|---|---:|
| Abstract and introduction | 0.8 |
| Related work and explicit novelty boundary | 0.7 |
| Data-space contract and target/error model | 1.1 |
| Compression-to-risk proposition and proof | 1.6 |
| Dataset, interventions and evaluation protocol | 1.1 |
| Results, four figures and three compact tables | 3.0 |
| Limitations and conclusion | 0.5 |
| References | 1.2 |
| **Total** | **10.0** |

Keep the central proof and common-noise distinction in the main text. A repository supplement may contain exhaustive configurations, expanded proofs and source manifests, but cannot be used to evade a paper requirement or assumed to be reviewed. Compile the actual IEEE template early. Do not shrink fonts or margins to make this allocation fit.

### 13.4 Nine-slide talk storyline

1. Three forecasts agree, but two reuse evidence. Show the illustrative example.
2. Define the observed next-hour energy target and the consumer's information boundary.
3. Explain why retransmission, shared training records and shared future noise differ.
4. Show weighted influence as the connection between an input record and forecast error.
5. Explain the sketch penalty and excess-risk bound in one equation and plain language.
6. Describe the real observations and the simulated provider-sharing intervention.
7. Present coverage and interval score against the strongest baselines, including failures.
8. Present actual bytes and CPU/GPU costs, distinguishing batch throughput from single-query latency.
9. State exactly what is supported, the model assumptions, and the next unresolved question.

Adapt the number of slides to the workshop's eventual presentation duration. No particular slot length has been verified.

## 14. Schedule, gates and fallback

This schedule ends before the verified October 15 AoE deadline. It allows a short feasibility cycle before committing most compute.

| Date | Deliverable | Decision gate |
|---|---|---|
| September 22 | This plan, verified venue links and a source inventory | Preserve the BDCC boundary and provisional status of the claims |
| September 23 | Local environment, source ZIP/schema audit, license record and candidate building manifest | Continue only with real readable observations, understood units and enough complete training support |
| September 24 | Exact comparison with L3-L6 and covariance communication literature; proof audit and example | If the contract/risk result is equivalent to known work, revise attribution before substantial experiments |
| September 25 | Bounded Stage 1 pilot, at most 2 GPU-hours total | Verify valid inference code, leakage controls, measured metadata costs and a plausible theoretical/empirical distinction |
| September 26-27 | Strong baselines, training/validation residual diagnostics, exact-lineage comparison | If exact weighted lineage is unhelpful after common future noise and shrinkage, stop the sketch 
branch |
| September 28-29 | Frozen task, models, uncertainty protocol, formats and main command | Require compressed exact-lineage comparison, feasible independent groups, and projected total <=24 GPU-hours |
| September 30 - October 2 | Controlled mathematical study and main real-outcome runs | Any unexplained within-assumption failure blocks the theorem claim; no test-driven retuning |
| October 3-4 | Bounded scaling and minimum ablations | No extra architectures or dataset switching to seek a favorable result |
| October 5-6 | Final paired analysis, claims ledger and all figure data | Check real observations, message counts and simulation seeds have separate denominators |
| October 7-9 | Complete manuscript in the official 10-page template | Main proof readable, figures legible, all claims linked to saved evidence |
| October 10-11 | Scientific review and reproducibility check | Correct errors; withdraw unsupported superiority, calibration or resilience claims |
| October 12-13 | Final text, bibliography and presentation-outline pass | Preserve explicit limitations and verify author/format instructions |
| October 14 | User-reviewable submission candidate and source archive | Ready before the deadline; no automatic submission |
| October 15 | Buffer for required corrections and user-controlled submission | Deadline is 23:59 AoE, corresponding to October 16 11:59 UTC |

**Data and observed-group gate.** Before opening test outcomes, aim for at least 64 eligible buildings at four sites, at least four usable validation week blocks and eight calibration week blocks. The one-year test offers at most 52 weekly blocks. If the eventual valid test span or site diversity is much smaller, narrow the generalization claim. For any separate tail claim, require at least 50 observed high-consumption episodes spread over at least 20 building-days and disclose site/week clustering. Do not lower the test threshold to manufacture events.

**Novelty gate.** Produce a one-page claim map saying which equations are standard, which interface assumptions differ from prior work, and which exact experimental observation would be new. If the only surviving mathematical content is standard covariance inflation, do not market a new fusion theorem.

**Practical relevance gate.** The pilot must report the fraction of predictive uncertainty attributable to the modeled training-influence component versus shared future and unresolved components. If training influence is negligible, do not select artificially tiny training sets only to magnify it. Report the diagnosis and reduce scope.

**GPU gate.** Continue with GPU batching if it materially increases the number of configurations or reduces complete run cost. If CPU is faster for all relevant workloads, use the CPU and withdraw the GPU-benefit claim. A GPU utilization chart is not scientific evidence of useful acceleration.

**Modest fallback.** If compression fails but the exact weighted-lineage analysis reveals a reproducible, practically meaningful overconfidence regime that strong baselines do not fully handle, develop a carefully scoped empirical case study, using established fusion methods and clearly attributed theory. If the effect is small or the theorem is already equivalent to prior work, consider a 5-page position/negative-result submission only if it provides a substantive contract diagnostic and real evidence. If those conditions are absent, stop or defer. A simulation-only wrapper or a known theorem with renamed variables does not satisfy the requested full-paper goal.

## 15. Repository structure

Use a new research project, separate from the BDCC scientific code. This planning session has not created or modified a remote repository. A local repository name such as `dspaces-evidence-fusion` is only a suggestion.

| Path | Responsibility |
|---|---|
| `README.md` | Research question, evidence boundaries and exact reproduction commands |
| `pyproject.toml`, environment lock | Package definition and verified dependencies |
| `docs/RESEARCH_PLAN.md` | This plan and any explicit subsequent amendments |
| `docs/NOVELTY_AUDIT.md` | Nearest methods, sources, standard equations and candidate distinction |
| `docs/PROOF_AUDIT.md` | Assumptions, proof and precision qualifications |
| `configs/data.yaml` | Source version, dates, schema, quality rules and limits |
| `configs/pilot.yaml` | Small authorized workload and strict resource caps |
| `configs/main_study.yaml` | Frozen main matrix, disabled until authorized |
| `src/evidence_fusion/data_access.py` | Verified retrieval and source manifests |
| `src/evidence_fusion/record_identity.py` | Canonical IDs, versions and support encodings |
| `src/evidence_fusion/chronological_splits.py` | Causal windows, embargoes and group IDs |
| `src/evidence_fusion/provider_models.py` | Local linear models and training-only diagnostics |
| `src/evidence_fusion/influence_operators.py` | Exact signed influences, norms and cached operators |
| `src/evidence_fusion/provenance_sketches.py` | Compatible projection streams and validity accounting |
| `src/evidence_fusion/message_contracts.py` | Schema, target agreement, duplicate and revision rules |
| `src/evidence_fusion/conservative_fusion.py` | Convex objective, solver gaps and individual fallback |
| `src/evidence_fusion/fusion_baselines.py` | CI, split-error reference and shrinkage covariance fusion |
| `src/evidence_fusion/calibration.py` | Frozen empirical interval correction |
| `src/evidence_fusion/evaluation.py` | Coverage, proper scores, operational loss and grouped uncertainty |
| `src/evidence_fusion/replay_benchmarks.py` | CPU/GPU stage costs, bytes and stream counts |
| `src/evidence_fusion/resource_ledger.py` | Budget accounting and clean stop/checkpoint behavior |
| `scripts/run_data_audit.py` | Dataset-only audit entry point |
| `scripts/run_pilot.py` | Bounded implementation/pilot entry point |
| `scripts/run_main_study.py` | Frozen main execution entry point |
| `scripts/build_figures.py` | Plots solely from saved numeric results |
| `tests/` | Mathematical invariants, meaningful protocol and leakage checks |
| `manifests/`, `reports/`, `results/` | Small reproducible evidence and run reports |
| `paper/` | Official IEEE template, manuscript, bibliography and figure references |

Use descriptive names and type-checked message records. Separate provider access from consumer access in the API. Keep raw measurements, environments and large caches out of git. Commit small manifests, configurations, exact commands and figure data according to the receiving repository's workflow. Do not silently turn this plan into authorization to push.

## 16. Ready-to-paste Codex prompt for Stage 1

The prompt below authorizes the receiving implementation session to perform a bounded pilot. It does not authorize this planning session to run that pilot, nor does it authorize the 24-hour main study.

```text
Act as my research software collaborator in the current local repository.
Read the complete DSpaCES_2026_Research_Plan.md first, inspect the repository
and applicable AGENTS.md instructions, and preserve all existing work.

Implement Stage 1 of the project "When Agreement Reuses Evidence."
The scientific question is whether compact weighted provenance can preserve
useful conservative uncertainty when building-energy forecasting providers
reuse observations. This is separate from the BDCC congestion project.
Do not import its graph enclosure, conditional reconstruction, selective
Monte Carlo or information-versus-simulation scientific contribution.

Authorization and limits
- Complete the local implementation, data audit, proof checks, strong minimal
  baselines and a bounded pilot. Do not stop after writing scaffolding.
- Verify the actual GPU. The planning assumption is one NVIDIA RTX 6000 Ada
  Generation with 48 GB VRAM. Report any difference before interpreting timings.
- Stage 1 has a hard cap of 2 total GPU-hours, including warm-up, compilation,
  fitting and reruns. Record GPU-allocated wall time and device timings.
- Download at most 2 GB and create at most 10 GB of data/cache output initially.
  Limit active GPU allocation to 32 GB. Use chunked data and query processing.
- The 24-hour main study and optional 48-hour extension are not authorized.
  Leave no background full-study process running at the end.
- Do not contact organizers, submit papers, deploy services, rent compute,
  create remotes, rewrite history or push without existing authorization.
- Follow the repository's existing branch/commit workflow. Do not infer a
  requirement to use main from the unrelated BDCC repository. Report the branch,
  working diff and any normal commit created under the applicable workflow.

Scientific discipline
- Treat CI, SCI/ESCI, robust covariance optimization, OLS influence identities,
  Gaussian random projections and covariance sketching as established methods.
- Create docs/NOVELTY_AUDIT.md comparing the precise proposed contract and risk
  bound with the plan's closest primary sources, especially Forsling 2022,
  Ajgl and Straka 2022, Cros 2024/2025 and the sketching literature.
- Retrieve unavailable close full texts if possible. If an equivalent result
  exists, cite it and revise the novelty claim. Do not manufacture a new theorem.
- Create docs/PROOF_AUDIT.md with assumptions, the projection event, the uniform
  simplex inequality, the optimization-gap term and exact-arithmetic limits.

Data audit
- Use the originating BDG2 repository and the public Zenodo v1.0 archive linked
  in the plan. The listing is about 595.3 MB. Verify actual bytes and contents.
- Record the source version, hash, exact license text, units, metadata schema,
  electricity-meter count, timestamps, timezone/DST ambiguities and missingness.
- Do not confuse Git LFS pointers with data or the paper's license with the
  dataset license. Publish retrieval instructions rather than raw measurements.
- Use the documented raw electricity release. It is already harmonized data;
  do not describe it as unprocessed instrument output. Keep a separate cleaned
  mask sensitivity and never fill missing target labels.
- Select the pilot buildings using training-only eligibility. Start with 16
  buildings across at least four sites if available. Keep the test year sealed.
- Use the plan's chronological training, validation and calibration partitions.
  Every record reused by several providers must retain the same split identity.

Model and contract
- Implement a small fixed-design calendar OLS model with full-rank QR solves,
  exact signed influence operators, exact norms and cached feature operators.
- Use the same target interval, units and evidence cutoff for all fused messages.
  Include the common future prediction-noise term once. It is not reduced by
  the number of providers. Distinguish this from training evidence overlap.
- Real residual scales and unresolved allowances are empirical plug-ins.
  Do not claim the independent Gaussian theorem is proven for building data.
- Implement a consumer API that accepts messages but cannot access hidden raw
  records, full influence vectors or future outcomes. Keep evaluator privileges
  in a separate module and explicit reference method.
- Implement canonical record IDs, immutable message IDs, exact duplicate
  handling, revisions, target/unit checks and compatible sketch epoch checks.
  All baselines receive the same identifiers available under each contract.
- Exclude recursive forwarding of fused estimates from Stage 1.

Core method
- Generate a common Gaussian projection from recorded independent streams.
  Build weighted sketches from signed influences and transmit exact norms.
- Calculate epsilon from the declared provider/query caps, sketch dimension
  and probability budget. Do not substitute an empirical epsilon into the
  theoretical guarantee. Reject exhausted or incompatible sketch epochs.
- Implement Q(w) = ||sum_i w_i z_i||^2 + epsilon (s^T w)^2
                 + (r^T w)^2 + v on nonnegative weights summing to one.
- Use a convex solver reference and a vectorized CPU/GPU implementation.
  Report a meaningful objective gap, not only parameter-change convergence.
- Compare against valid individual conservative bounds and retain the candidate
  with the smallest valid upper variance bound as described in the plan.
- Preserve the difference between a mathematical covariance bound, a Gaussian
  prediction interval, and an empirically calibrated interval. In the main
  protocol, November fits empirical dependence and December calibrates intervals
  after weights are frozen. For the Stage 1 validation-only pilot, use a fixed
  chronological subdivision of October for these roles; label its short scope.
- Use FP64 audit calculations. Either derive numerical error allowances or
  label the implemented certificate as exact-arithmetic theory plus numerical
  validation. Do not call a tolerance test a floating-point proof.

Minimum baselines
- Seasonal naive, individual forecasts and equal-weight combination.
- Naive independence, independence corrected for common future noise, and
  duplicate-aware independence using the same available IDs/digests.
- Competently optimized scalar CI.
- Exact weighted-lineage conservative fusion under the same simplex constraint.
- Shrinkage covariance fusion with historical validation forecast errors.
- Uninflated sketch as an ablation.
- Measure compressed exact support/lineage and cached sufficient-statistic
  alternatives. Do not compare only with a wasteful uncompressed ID list.

Meaningful validation
- Reproduce the three-provider numeric example and its optimal weights,
  mean 105.2 and variance 43/15 before approximate calculations.
- Check the risk sandwich and excess-risk inequality on controlled problems
  whenever the observed projection event holds. Distinguish rare projection
  failures from implementation failures.
- Include zero rows, exact duplicates, partial overlap, negative influence
  coefficients, nearly singular covariance and unequal provider variances.
- Verify common future uncertainty persists even with disjoint training IDs.
- Verify duplicate packets and reordered arrivals do not change the final
  valid active-message state. Verify revision supersession and epoch mismatch.
- Check that influence values and exact hidden references never leak into
  the deployable consumer, and that test outcomes never enter tuning.
- Include a deliberate correlated-innovation assumption failure and label it
  outside the theorem. Do not adjust the theorem after seeing a failure.

Pilot workload
- Use four providers, overlap 0, about 0.5 and about 0.9, and one allocation seed.
- Use k=512 and 2,048, at most 256 validation origins per selected building,
  and a bounded analytic synthetic panel. Do not run the full Cartesian matrix.
- Keep per-provider evidence count fixed where feasible and report exact union
  and intersection counts. Do not make training sets tiny to force a benefit.
- Measure vectorized CPU and GPU complete costs, including projection setup,
  ID handling, parsing, transfer, optimization, output and cached amortization.
- Report cold/warm p50/p95 latency, throughput, peak host RAM and VRAM, actual
  metadata bytes and the fraction of modeled variance due to training influence.
- Plot two clearly labeled pilot figures from saved measurements only.

Deliverables
- reports/FEASIBILITY_REPORT.md with actual hardware, dataset, timestamps,
  evidence counts, terms and any unresolved source/venue conditions.
- docs/NOVELTY_AUDIT.md and docs/PROOF_AUDIT.md.
- reports/STAGE1_REPORT.md with exact completed work, meaningful test outcomes,
  raw versus calibrated uncertainty, strongest-baseline comparison, actual
  GPU time, bytes, cost bottlenecks and a continue/simplify/stop decision.
- Frozen pilot configs, seed/epoch manifests, environment lock, small numeric
  outputs and reproducible plotting commands.
- A measured projection of the main study within 24 total GPU-hours, with a
  single ready-to-run command that enforces its cap if authorized later.
- A clear diagnosis if exact lineage has no useful advantage or compressed
  exact metadata beats sketches. Do not promise a full paper merely because
  code runs. End with the reviewable Stage 1 package and no active large run.
```

## 17. Source register and verification limits

Sources were checked or located on September 22, 2026. A retrieved paper title or abstract does not establish that every proof was audited. The source-access limitations in Section 5 are part of the plan and must remain visible during Stage 1. Searches did not establish the absence of an equivalent weighted-provenance result.

### Venue

- C1. [DSpaCES 2026 official workshop page](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home). Dates, online format, themes, workshop limits, registration language and provisional waiver.
- C2. [DSpaCES-specific submission portal](https://wi-lab.com/cyberchair/2026/bigdata26/scripts/submit.php?subarea=S53&undisplay_detail=1&wh=/cyberchair/2026/bigdata26/scripts/ws_submit.php). Explicit October 15, 2026, 11:59 pm AoE deadline.
- C3. [IEEE Big Data 2026 camera-ready instructions](https://wi-lab.com/cyberchair/2026/bigdata26/scripts/BigData_2026_Camera_ready_instruction.php). Applies to main conference, workshops and posters; PDF validation, copyright and registration-receipt procedure.
- C4. [Official IEEE conference templates](https://www.ieee.org/conferences/publishing/templates.html), linked by C1-C3. Download and inspect the actual template during execution.

### Twelve-paper comparison

- L1. Julier and Uhlmann (1997). [DOI](https://doi.org/10.1109/ACC.1997.609105), [author publication list](https://uhlmannj.mufaculty.umsystem.edu/home/publications). The DOI full text was not retrieved; the modern formulation was checked in L6.
- L2. McLaughlin, Krishnamurthy and Challa (2003). [Primary proceedings PDF located by search](https://dihana.cps.unizar.es/proceedings/ICASSP/2003/pdfs/05-00269.pdf). Full retrieval failed in this review; obtain it before closing the novelty audit.
- L3. Ajgl and Straka (2022). [DOI](https://doi.org/10.1016/j.automatica.2022.110168), [institutional record](https://dspace.zcu.cz/items/6e4e81e9-0161-41f3-95c9-dbfc6c55b0b6). Abstract and bibliographic details inspected; the download redirected to a login page.
- L4. Forsling et al. (2022). [DOI](https://doi.org/10.1109/TSP.2022.3179841), [author postprint](https://www.diva-portal.org/smash/get/diva2:1690215/FULLTEXT01.pdf). This is the principal robust-optimization comparison.
- L5. Cros et al. (2024). [Author preprint and full text](https://arxiv.org/html/2403.03543v1). Use verified publication metadata when building the bibliography; this plan relies on the preprint.
- L6. Cros et al. (2025). [IEEE TAC DOI](https://doi.org/10.1109/TAC.2025.3530854), [full author version](https://arxiv.org/html/2501.07915v1). Known correlated components and two-estimator optimality.
- L7. Hao Li (2026). [Preprint record](https://arxiv.org/abs/2606.09505), [full PDF](https://arxiv.org/pdf/2606.09505). Submitted June 8, 2026; do not imply verified journal publication.
- L8. Bates and Granger (1969). [Primary publisher record](https://www.tandfonline.com/doi/abs/10.1057/jors.1969.103). Full text was not retrieved.
- L9. Ledoit and Wolf (2004). [Publisher record](https://www.sciencedirect.com/science/article/pii/S0047259X03000964), [author abstract](https://www.ledoit.net/ole1_abstract.htm), [author PDF location](https://www.ledoit.net/Well-conditioned2004.pdf). Abstract inspected; PDF retrieval failed.
- L10. Green, Karvounarakis and Tannen (2007). [Author-hosted PODS paper](https://web.cs.ucdavis.edu/~green/papers/pods07.pdf).
- L11. Dasgupta and Gupta (2003). [Author paper](https://cseweb.ucsd.edu/~dasgupta/papers/jl.pdf), [published DOI](https://doi.org/10.1002/rsa.10073).
- L12. Mroueh, Marcheret and Goel (2017). [Official proceedings record](https://proceedings.mlr.press/v54/mroueh17a.html), [full paper](https://proceedings.mlr.press/v54/mroueh17a/mroueh17a.pdf).

### Dataset

- D1. [Originating BDG2 repository](https://github.com/buds-lab/building-data-genome-project-2). Release organization and published scope.
- D2. [Zenodo v1.0 archive](https://zenodo.org/records/3887306). Public 595.3 MB ZIP, release metadata and checksum listing.
- D3. Miller et al. (2020). [Scientific Data DOI](https://doi.org/10.1038/s41597-020-00712-x), [full author preprint](https://arxiv.org/pdf/2006.02273). The Nature page redirected during this review; the full author version supplied the detailed schema, site and processing account.
- D4. [Meter data features and raw/cleaned distinctions](https://github.com/buds-lab/building-data-genome-project-2/wiki/Meters-data-features).
- D5. [Metadata features](https://github.com/buds-lab/building-data-genome-project-2/wiki/Metadata-features), including identifiers, timezones and meter-presence fields.
- D6. [Project documentation index](https://github.com/buds-lab/building-data-genome-project-2/wiki).
- D7. [Repository license](https://github.com/buds-lab/building-data-genome-project-2/blob/master/LICENSE). Preserve its exact wording; do not replace it with the article license.

### What remains to be learned

Actual source-file integrity, electricity-meter counts, usable cohorts, timestamp/DST behavior, residual dependence, influence relevance, the closest-method novelty judgment, empirical interval quality, compressed-exact versus sketch cost, and GPU crossover remain unmeasured. The paper's final claims must be determined by those results. The mathematical proof and illustrative arithmetic do not substitute for them.
