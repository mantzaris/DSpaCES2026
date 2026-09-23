# Regional matrix method: derivation and limits

This pilot is separate from graph aggregation, conditional traffic reconstruction,
selective Monte Carlo, weighted provenance sketches, and forecast-contract LPs.
All statements below are deterministic linear algebra. The forecasting model is
a fitted working model, not a guaranteed physical law. Error in solving its
normal equations is distinct from its error against observed consumption.

## Moving-horizon objective

Let h index a physical household meter, g(h) a simulated provider partition, and
t a source-clock half-hour label. The measured variable is interval energy in
kWh, not power in kW. Let beta_h(t) be its training weekly seasonal profile and
sigma_h its training residual scale. The standardized observation mapping is
r_ht = (y_ht-beta_h(t))/sigma_h = H_h s_t + measurement error. Training determines
the 16-dimensional latent loadings H, transition F_state, diagonal process
variance V, diagonal measurement variances R_h, and diagonal initial covariance P.
There is no exogenous input in this pilot: B_input u_t = 0. The deterministic
seasonal term belongs to the observation equation. Dynamics are contracted to
spectral radius at most 0.995 using training only.

Stack L=24 states as z=(s_0,...,s_(L-1)). At a query's information cutoff, let O_g
select the AVAILABLE observations of provider g, W_g the diagonal inverse
measurement variances, v_g their standardized residuals, T the block dynamics
operator with rows s_t-F_state s_(t-1), J_0 select the first state, mu its prior,
and c the trajectory propagated from that prior. The objective is

    Phi_w(z) = 1/2 ||J_0 z-mu||_(P^-1)^2
             + 1/2 ||T z||_(I tensor V^-1)^2
             + lambda/2 ||z-c||_2^2
             + 1/2 sum_g w_g ||O_g z-v_g||_(W_g)^2.

The prior comes only from earlier replay snapshots, propagated over the actual
gap to the window start. The center is fixed for every access profile at that
origin. No current hidden measurement determines it. Thus

    C_0 = J_0^T P^-1 J_0 + T^T (I tensor V^-1) T,
    b_0 = J_0^T P^-1 mu + lambda c,
    C_g = O_g^T W_g O_g, b_g = O_g^T W_g v_g,
    A(w) = lambda I + C_0 + sum_g w_g C_g,
    b(w) = b_0 + sum_g w_g b_g.

Differentiating gives grad Phi_w = A(w)z-b(w). Every C is PSD and lambda>0,
so A is SPD and the minimizer is unique for weights in [0,1]. The centered
regularizer's contribution to b is essential. Tests differentiate the original
residual objective numerically; they also poison inaccessible observations.
Native missingness changes O_g and invalidates its matrix statistics. The replay
recomputes them and the certificate, retaining Q but not assuming unchanged C_g.

## Shared orthogonal basis and family bounds

Use augmented a=(1,w_1,...,w_G), including C_0. For an orthogonal full Q write
Q^T C_g Q=D_g+E_g, with D_g diagonal and E_g zero on the diagonal. Then
D=lambda I+sum a_g D_g is positive diagonal, E=sum a_g E_g, and
Q^T A Q=D+E. Orthogonality preserves lambda I. The pilot implements the Gaussian
linear-combination RJD algorithm of He and Kressner, with three fixed trials
selected by summed squared diagonal entries, and compares identity and an
eigenbasis of the all-provider reference matrix. RJD's existing theorem is not
our contribution; this family need not be near commuting.

**Proposition 1 (global bound).** K_gh=<E_g,E_h>_F gives

    ||D^-1/2 E D^-1/2||_2 <= ||E||_F/min D_ii
                          = sqrt(a^T K a)/min D_ii.

Proof: the spectral norm is submultiplicative, ||D^-1/2||_2^2=1/min D_ii,
and ||E||_2<=||E||_F. Expanding the squared Frobenius norm gives the Gram form.

**Proposition 2 (block bound).** Partition the coordinates into fixed disjoint
nonempty blocks I_p. Set d_p=min_(i in I_p)D_ii and

    K_pq[g,h]=<E_g[I_p,I_q],E_h[I_p,I_q]>_F,
    M_pq=sqrt(a^T K_pq a)/sqrt(d_p d_q).

Then for F=D^-1/2 E D^-1/2,

    ||F||_2 <= ||M||_2 <= max_p sum_q M_pq.

Proof: each block satisfies ||F_pq||_2<=M_pq. For a vector x set v_q=||x_q||_2.
The triangle inequality gives ||(Fx)_p||_2<=sum_q M_pq v_q. Squaring and summing
gives ||Fx||_2<=||M||_2||v||_2=||M||_2||x||_2. Since E_g are symmetric, M is
symmetric and entrywise nonnegative, so its spectral norm equals its largest
eigenvalue and is bounded by its maximum row sum. Symmetry is needed for this
last shortcut; a general nonsymmetric block majorant would instead use
sqrt(||M||_1 ||M||_infinity). Neither global nor block bound dominates the other
in general. Use the smaller valid bound and report both setup and query cost.

**Proposition 3 (polynomial correction).** If delta bounds ||F||_2 and delta<1,
define h=D^-1/2 Q^T b, u_m=sum_(j=0)^m (-F)^j h and z_m=Q D^-1/2 u_m.
The Neumann series converges because ||F||<1. Its tail has norm at most

    ||u_exact-u_m||_2 <= delta^(m+1)/(1-delta) ||h||_2.

This follows by summing a geometric upper bound on each omitted term. This is
an established inverse-series result, not a new convergence theorem. When the
family bound is inconclusive, the pilot uses residual-driven PCG with the same
diagonal shared-basis preconditioner and falls back to accurate Cholesky if the
frozen accuracy checks fail. No delta>=1 is interpreted as proof of divergence.

**Proposition 4 (output error).** For q=beta+jz, Cauchy-Schwarz gives

    |q_exact-q_m| <= ||D^-1/2 Q^T j^T||_2
                    delta^(m+1)/(1-delta)||h||_2.

At horizon r, let J_L select the last state. For the regional total,
j = [sum_h sigma_h H_h] F_state^r J_L. For an observed-support evaluation replace
the sum with that exact set of observed target households. This sums loadings
BEFORE taking the norm and makes no independent-household-error assumption.
The fixed tolerance is 0.001 times the median training seasonal regional demand.
The predictor also reports a full cohort forecast, but scores only observed
support when any household target is missing. A partial sum is never labeled
the true complete regional demand.

## Complexity and numerical qualifications

With n=Ld, G providers, P coordinate blocks and B profiles, RJD costs three
dense eigensolves O(n^3) plus component transforms O(G n^3). Stored components
cost O(G n^2). Global Gram construction costs O(G^2 n^2), each query O(G^2+Gn).
All block Gram tables together cost the same asymptotic setup and O(P^2 G^2)
query contractions, plus O(P^3) for the block norm or O(P^2) for its row bound.
A dense polynomial correction costs O(m n^2) per query, including basis
applications. Direct banded Cholesky exploits state bandwidth O(d) and costs
O(L d^3), much less than dense O((Ld)^3). This is a serious comparator.
Information smoothing is equivalent block Gaussian elimination for this
unconstrained finite-window Gaussian objective, including regularization as
independent pseudo-observations. Provider withdrawal generally changes full
trajectory rank, not a small rank-one update, so low-rank savings cannot be
assumed. Repeated matrices reuse factors with the same 64-matrix FIFO capacity
for dense CPU, banded CPU and GPU factorizations, including across origins.

FP64 calculations add a standard dot-product error allowance to Gram quadratic
forms for the stored E entries, using absolute-product sums and gamma_N=Nu/(1-Nu).
Negative computed forms return infinity; they are never clipped into a purported
upper bound. This does not bound all errors in forming C, computing Q, loss of
orthogonality, basis transformations or reductions. Therefore the implemented
widths are exact-arithmetic theory with numerical audits, **not a formal
floating-point certificate**. All accepted outputs are checked against FP64
references, with explicit zero-vector conventions. Weighted relative error uses
the A-energy norm, alongside Euclidean forward error and Frobenius-norm backward
error. A future rigorous implementation needs interval/rounding bounds for the
whole construction. Physical forecast uncertainty is not certified by any of
these deterministic solver statements.
