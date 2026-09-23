# Proof audit: a corollary under an explicit information contract

Audited September 22, 2026. The complete prospective specification is preserved in
[RESEARCH_PLAN.md](RESEARCH_PLAN.md). Numerical evidence is in
[`results/controlled.json`](../results/controlled.json); it does not prove a probability bound.

## Assumptions and scope

For one scalar target, write each error as `e_i = a_i^T xi + u_i - nu`.
Conditional on fixed design, `E[xi]=E[u]=E[nu]=0`, `Cov(xi)=I`, and the three
components are mutually uncorrelated. `U=Cov(u)` is PSD with `U_ii <= r_i^2`,
and `Var(nu)=v`. Rows of A, exact norms s, allowances r and v are fixed
independently of both the error draws and the Gaussian sketch. Fusion weights
are nonnegative and sum to one. No recursive reuse of previously fused messages
is allowed. All compared forecasts concern the same interval, building and unit.

Canonical identities represent innovations only under a valid noise model.
Different IDs do not imply independence. If observations have known covariance
`Sigma=L L^T`, an observation coefficient row `b_i^T` must be transformed to
`a_i^T=b_i^T L` on the common innovation universe; merely applying per-record
standard deviations does not whiten correlated readings.

Real OLS scales are estimated from provider-local training residuals. Calendar
models can be biased and autocorrelated, and weights then depend on error draws
through the plug-in scales. Therefore the real-data intervals are empirical;
none inherits the controlled-model Gaussian coverage guarantee.

## Exact residual ambiguity

PSD implies `|U_ij| <= r_i r_j`. For simplex w,
`sup_U w^T U w = (r^T w)^2`, attained by `U=r r^T`. Thus

```
R(w) = w^T A A^T w + (r^T w)^2 + v.
```

The common future innovation is retained once because `sum(w)=1`.
This is standard robust covariance reasoning. It is scalar: the scalar minimax
description is not a claim about general matrix-valued conservative optimality.
Forsling et al. (2022), Definition 2 and Section III-D, explicitly distinguish
matrix conservatism from minimizing only a scalar loss of a matrix.

For the two-provider ESCI connection, its centralized bound is
`K + diag(r_i^2/omega_i)` for positive simplex omega. At fixed nonnegative w,
minimizing `sum_i r_i^2*w_i^2/omega_i` gives `(r^T w)^2` by Cauchy–Schwarz,
with the boundary interpreted by continuity. A separate scalar omega search
checks equality with the exact reference in a two-provider case whose gains
remain nonnegative. This does not equate our simplex optimum with unrestricted
ESCI in cases with negative optimal gains.

## Projection event and horizon

For a fixed vector x and an ideal k-by-R matrix of independent `N(0,1/k)` entries,
the Gaussian moment generating function and Chernoff bound give, for `0<eps<1`,

```
Pr[ | ||Gx||^2 - ||x||^2 | > eps ||x||^2 ]
 <= 2 exp[-k(eps^2/4 - eps^3/6)].
```

This is an inherited concentration argument, not a new JL result. The
[Dasgupta–Gupta paper](https://cseweb.ucsd.edu/~dasgupta/papers/jl.pdf) supplies
the classical concentration/union-bound framework; the above expression follows
directly for independent Gaussian entries and does not require an orthogonalized
projection.

Normalize nonzero rows `u_i=a_i/s_i`. Across T fixed queries with at most p rows,
the rows and pairwise sums/differences comprise at most `M=T(2p^2+p)` vectors.
Norm preservation and polarization yield
`|z_i^T z_j - a_i^T a_j| <= eps s_i s_j` simultaneously. Zero rows have zero
sketches. Choose k from `log(2M/delta)/(eps^2/4-eps^3/6)`; epsilon is obtained
by upward-rounded bisection from this formula, never from observed errors.

The pilot has two epochs, k=512 and 2048, each with T=12,288, p=4 and delta=.005.
Their combined mathematical failure allocation is .01. The synthetic package
allocates a separate .01; a joint statement covering both uses .02, not .01.
Repeated noise settings sharing a projection are not independent sketch draws.
The registry counts different query/model-message sets and rejects exhausted
epochs. Stream revisions consume additional distinct query sets if finalized.
The pilot manifests retain the final count and query-set digest. There is no
claim for an unbounded/adaptive stream or for restarting with an altered family
under the same allocation. Fresh processes must restore/account for their
epoch registry before production reuse; Stage 1 is a single bounded replay.

## Uniform sandwich and optimized risk

On the event, for every simplex w,

```
|w^T (Khat-K) w| <= eps (s^T w)^2,
Q(w) = w^T Khat w + eps(s^T w)^2 + (r^T w)^2 + v,
R(w) <= Q(w) <= R(w) + 2 eps (s^T w)^2.
```

If `Q(w_hat) <= min Q + eta_opt`, then for the exact simplex minimizer w_star,

```
R(w_hat) <= R(w_star) + 2 eps (s^T w_star)^2 + eta_opt
         <= R(w_star) + 2 eps max_i s_i^2 + eta_opt.
```

Uniformity permits selecting weights after observing the sketch, but does not
permit selecting A after observing it. Selecting an individual candidate by its
valid bound also preserves the result: selected risk is bounded by the smaller
reported bound, which is at most `Q(w_hat)`. Selection must not use realized error.

The optimized matrix `Khat+eps ss^T+rr^T` is PSD. Its difference from K need not
be PSD on all signed directions. The proposition guarantees the quadratic
inequality on the nonnegative simplex, not a matrix Loewner upper bound or an
unrestricted signed BLUE result. This distinction matters when comparing with
Funk–Noack's conservative covariance-matrix compression.

## Optimization and numerical qualifications

For p<=8, the implementation enumerates all nonempty active faces. Each face
uses a bordered KKT pseudoinverse and feasibility check; vertices guarantee an
available feasible candidate. The solver reports
`g_FW=2[w^T H w - min_i (Hw)_i]`. Convexity makes this an upper bound on the
objective gap in exact arithmetic. Tests compare an independent SciPy SLSQP
solution, including singular, zero-row and negative-influence cases. GPU and CPU
use the same objective and face enumeration; this is established optimization,
not an algorithmic novelty claim. The restricted p<=8 implementation does not
pretend to implement the prospective 64-provider scaling package.

The main wire format is FP64, an explicit pilot amendment to the prospective
FP32 throughput path. FP32 Gram disagreement is measured separately. No formal
rounding/reduction/serialization allowance has been derived, so the code reports
exact-arithmetic theory plus numerical validation. Pseudorandom PCG64 streams
keyed by SHA-256 canonical IDs provide reproducibility, not proof of ideal
independent Gaussian columns.

## Coverage interpretation

Under the additional joint Gaussian assumption and weights independent of the
error realizations, `mean +/- Phi^-1(.975)*sqrt(Q)` is conservative at 95%
conditional on the successful projection event. Unconditionally over projection
randomness the lower bound is `.95*(1-delta)`. It is repeated-sample coverage at
fixed design, not conditional coverage for every observed training response.
With second moments alone the Chebyshev radius is `sqrt(Q/alpha)`.

October's disjoint historical-error, calibration and scoring dates supply only
an empirical real-data check. Calendar dependence, OOF scale estimation and
nonstationarity prevent an exact conformal or Gaussian certificate.

## Falsification

Within-event violations block the mathematical claim. A failed projection event
must be recorded separately. Controlled examples deliberately break innovation
independence, omit future noise, and choose a vector in the observed projection's
nullspace; these are outside the assumptions, not failures of the proposition.
The short proof is a synthesis/corollary. Originality remains subject to the
[novelty audit](NOVELTY_AUDIT.md).
