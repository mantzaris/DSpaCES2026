# Novelty audit and claim map

September 22, 2026. **Do not claim a new general conservative fusion theorem.**
The displayed risk inequality is a useful, auditable corollary of existing
projection concentration and robust scalar estimation. Its publication value
depends on an informative interface comparison and real evidence. A bounded
search cannot establish absence of an equivalent result.

| Ingredient / closest source | What is inherited | Remaining distinction to test |
|---|---|---|
| [Julier–Uhlmann, ACC 1997](https://doi.org/10.1109/ACC.1997.609105) | Conservative fusion with unknown correlations; scalar CI minimizes reported variance by selecting a smallest-variance input | No novelty claimed; deterministic optimized scalar baseline |
| [McLaughlin–Krishnamurthy–Challa, ICASSP 2003](https://dihana.cps.unizar.es/proceedings/ICASSP/2003/pdfs/05-00269.pdf) | Data incest and communication/storage-aware mitigation | Partial signed influence sharing in a nonrecursive regression interface; identifying reuse is not new |
| [Ajgl–Straka, Automatica 2022](https://doi.org/10.1016/j.automatica.2022.110168) | Conservative bounds using elementwise partial covariance knowledge | Here uncertain entries are obtained through independently computed compatible messages; comparison is incomplete without their restricted full text |
| [Forsling et al., TSP 2022](https://www.diva-portal.org/smash/get/diva2:1690215/FULLTEXT01.pdf) | Definition 2 / equation (7): conservative optimization over an admissible covariance set | The uncertainty set is induced by an exchange budget and a finite Gaussian projection event; optimization itself is inherited |
| [Cros et al., 2024 author preprint](https://arxiv.org/html/2403.03543v1) | Known correlated error components, including common process noise | A common future term is an instance of established split-error reasoning |
| [Cros et al., 2025](https://arxiv.org/html/2501.07915v1) | ESCI, admissible covariance sets, and two-estimator conservative optimality | No improvement over its general vector/two-estimator theorem is asserted; our exact scalar simplex reference has a restricted weight domain |
| [Ledoit–Wolf, 2004](https://www.ledoit.net/ole1_abstract.htm) | Stable shrinkage estimation of historical forecast-error covariance | Essential empirical comparator, fitted before interval calibration |
| [Green et al., PODS 2007](https://web.cs.ucdavis.edu/~green/papers/pods07.pdf) | Algebraic derivation lineage | Sensitivities require a separate noise model; a hash does not establish covariance or privacy |
| [Dasgupta–Gupta, 2003](https://cseweb.ucsd.edu/~dasgupta/papers/jl.pdf) | Finite-set projection concentration and union bound | Translate an inherited event into a uniform simplex risk penalty and state the interface horizon |
| [Mroueh et al., AISTATS 2017](https://proceedings.mlr.press/v54/mroueh17a.html) | Approximate matrix multiplication / covariance sketches | Independent local messages use a common projection; no centralized matrix-product novelty is claimed |

Additional close sources found during Stage 1 materially narrow the claim:

* [Funk and Noack, *An Event-Based Approach for the Conservative Compression of Covariance Matrices* (2024 author preprint)](https://arxiv.org/html/2403.05977v1),
  Section III-B, equations (1)-(4), Theorems 1-2, already couples bounded entrywise
  compression error to conservative inflation and an explicit compression error
  bound. Its transmitter knows a covariance matrix and sends selected entries
  with deterministic error limits; its receiver obtains a matrix upper bound via
  diagonal dominance. The present providers know local signed influence rows,
  and the common projection yields probabilistic entry bounds. Our rank-one
  inflation is conservative on nonnegative weights, not all signed directions.
  **Generic compression-to-conservatism is therefore not a novelty claim.**
* [Huang, Lin, Zhang and Zhang, *Communication-Efficient Distributed Covariance Sketch, with Application to Distributed PCA*, JMLR 22(80), 2021](https://jmlr.org/papers/v22/20-705.html)
  studies communication complexity and algorithms for covariance approximation
  with a matrix distributed across machines. Its row-partitioned matrix/PCA
  objective differs from independently reported scalar prediction-error rows,
  but distributed covariance sketching is plainly established. The paper's
  spectral-error guarantee also implies quadratic-form error bounds, so a risk
  corollary alone is a weak theoretical contribution.
* [Forsling et al., *Decentralized State Estimation In A Dimension-Reduced Linear Regression*, arXiv:2210.06947v2](https://arxiv.org/pdf/2210.06947)
  optimizes dimension reduction for decentralized estimation and supplies an
  encoding scheme. The compressed object there is a vector estimate/covariance;
  here it is a scalar estimator's influence on an evidence universe. Neither
  communication-aware estimation nor metadata compression is new.

## One-page claim map

**Standard:** OLS influence identities; common-noise separation; the residual
worst case `(r^T w)^2`; Gaussian projection concentration; robust covariance
fusion; the convex quadratic; the optimization-gap argument; metadata caching.

**Candidate interface synthesis:** trusted independently administered producers
share canonical innovation IDs only through a common-seed weighted projection,
exact norms, residual bounds and a finite nonadaptive family declaration. On
that event, simplex optimization after sketch observation incurs at most
`2 eps (s^T w_star)^2 + eta`. Message revisions and duplicates are engineering
preconditions. This is a scoped composition of established results.

**Potentially informative empirical observation:** whether realistic hourly
forecast uncertainty contains enough training-estimation variance to matter,
and whether such sketches outperform both historical shrinkage and exact
calendar/support reconstruction at measured total cost. The low-dimensional
model may make exact exchange cheaper. A negative answer is retained.

**Unsupported:** new CI/ESCI family, general signed/vector optimality, privacy,
real Gaussian coverage, resilience, operational multi-organization deployment,
or a paper-worthy result merely because the implementation works.

## Access and search limits

Primary full texts were downloaded and fingerprinted for Forsling 2022, both
Cros papers, Green, Dasgupta–Gupta, Mroueh, Funk–Noack, Huang et al., and the
dimension-reduction paper. Key definitions/results above were inspected; no
claim is made that every proof in every source was rederived. See
[`manifests/literature_access.json`](../manifests/literature_access.json).

The original CI DOI returned an empty publisher page. Ajgl–Straka's institution
served a login page, not a PDF. Direct retrieval of the ICASSP paper failed due
to a hostname/certificate mismatch; the indexed primary PDF exposed its opening
formulation but not a verified complete download. The Ledoit author PDF failed
certificate validation. These are access limitations, not negative search
evidence. Modern CI/ESCI texts were used for verified formulae. No credentials,
paywalls or TLS checks were bypassed, and no author or organizer was contacted.

Searches included the exact nearest-paper titles, covariance/random-projection
fusion, communication-constrained covariance sketches, and conservative
compression. The audit is bounded and provisional; full-paper originality is
not established. Bates–Granger forecast combination and the June 2026 SCI
optimization preprint remain background from the supplied register rather than
newly audited proofs in this Stage 1 package.
