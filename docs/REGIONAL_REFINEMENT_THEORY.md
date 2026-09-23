# Fixed-model refinement and evidence replacement

September 23, 2026. These are attributed Gaussian identities and a proposed
implementation contract, not a new general multiresolution inference theorem.
See the [source comparison](REGIONAL_REFINEMENT_NOVELTY_AUDIT.md).

## Model, units and operations

For a fixed 24-half-hour window, let c=(s_0,...,s_23) have dimension r=384,
where s_t has 16 inherited seasonal-factor coordinates. The prior is proper:
s_0~N(0,P), s_{t+1}=F s_t+eta_t, eta_t~N(0,Q). P,Q and F are frozen from
2012 Stage 1 fitting. At household i, measured energy is

    y_it = seasonal_it + l_i^T s_t + d_it + epsilon_it.
    d_i,t+1 = rho_i d_it + zeta_it,
    Var(d_it)=v_i, Var(zeta_it)=v_i(1-rho_i^2),
    Var(epsilon_it)=n_i > 0.

The household residual processes and nuggets are mutually independent conditional
on the common trajectory. Errors are **not** unconditionally independent:
Cov(y_i,y_j) includes the shared-factor covariance. The AR residual assumption is
a working approximation, not a finding that real household residuals are
conditionally independent. Negative consumption is possible under the Gaussian
model; forecasts are not clipped. Uncertainty is model-conditional and uncalibrated.

All output quantities are kWh per half-hour at 1 h / 6 h lead, not integrated
one-hour/six-hour energy. l_i includes the inherited household scale. An additional
GPU training pass estimates household residual second moments and lag-one products
after an observed-only projection onto the fixed loadings. Set n_i=.2 total
residual variance and v_i=.8 total variance; adjust AR moment by .8, then clip rho
to [-.95,.95]. The nugget split is a fixed convention, not identified sensor noise.
This is the one explicit initial **model enrichment C**, before all comparisons.

The hierarchy is region -> 16 groups -> physical household IDs. Group number is
sorted eligible training-ID index modulo 16, a balanced synthetic partition.
Regional/group demand is the linear sum of household variables. It is not a
separately fitted state with conflicting constraints. Thus a summing matrix S
gives macro distribution N(S mu,S Sigma S^T). No London topology is invented.

**Coherent** means all reported distributions are marginals/linear images of one
fixed joint Gaussian posterior for the stated evidence version and window.
**Active detail** means resident household conditional trajectory operators, data
and covariance blocks, not extra physical households or newly trained parameters.
**Affected** means factors whose argument/evidence scope or separator marginal
changes. A global factor can affect every household query through c even when
only one leaf likelihood must be rebuilt.

Operation A exposes or evicts conditionals with fixed model/evidence. Operation B
acquires household readings and replaces an aggregate likelihood. It can change
regional predictions. Operation C changes model parameters/coordinates and is
not an invariance operation. These labels are explicit in the access traces.

## Exact elimination and restoration (established)

For proper p(c,d) proportional to exp(-.5 [c;d]^T J[c;d]+h^T[c;d]), J_dd>0,

    Jc = J_cc - J_cd solve(J_dd,J_dc)
    hc = h_c  - J_cd solve(J_dd,h_d)
    d|c ~ N(solve(J_dd,h_d-J_dc c), solve(J_dd,I)).

Completing the square proves both expressions. Consequently, writing d=a+T c+e,
where e has covariance V and is independent of c, gives

    E[d]=a+T E[c], Cov(d)=V+T Cov(c) T^T,
    Cov(c,d)=Cov(c)T^T.

**Proposition 1 (representation consistency).** Retaining the coarse marginal
and every required conditional makes coarsening/refinement preserve all means,
covariances and linear aggregate laws. Exact elimination of disjoint blocks in
either order yields the same final marginal, provided all induced fill-in is
retained. Proof: both orders integrate the same integrable positive Gaussian
density; completing squares supplies the unique resulting mean/covariance.
Order independence does not hold if an induced edge is dropped or if evidence
changes in one order. Numerical solves have floating-point discrepancies.

**Impossibility of free restoration.** c~N(0,1), d|c~N(c,1) and d|c~N(-c,2)
have the same c marginal but different joint laws. No algorithm receiving only
that marginal can restore both. Exact future refinement must retain a sufficient
conditional, reread versioned evidence/model information, or accept approximation.
This prototype chooses retained query summaries plus charged rereads. It does not
move hidden full fine state to unreported host memory.

## Group likelihoods and derived-evidence replacement

After eliminating a household AR trajectory, its observed residual vector has
law y_i|c~N(O_i c,V_i), where V_i is the observed submatrix of
K_i+n_i I, K_i[t,u]=v_i rho_i^|t-u|. Masks select rows; missing readings are not
zero demand. Dummy identity coordinates in the implementation have exactly zero
operator/RHS and are removed from every information product.

Fine group g contributes

    R_g = sum_i O_i^T solve(V_i,O_i),
    gamma_g = sum_i O_i^T solve(V_i,y_i).

The shared posterior precision/information is J0+sum_g R_g, sum_g gamma_g.
This is the distributed Gaussian sufficient-statistic method of Katzfuss and
Hammerling, also interpretable as leaf elimination onto a common separator.

For derived group sum a_g,t=sum_{i observed at t} y_i,t, the aggregate operator
is O_A[t,:]=sum_i mask_it O_i[t,:]. Its covariance is

    V_A[t,u] = sum_i mask_it mask_iu K_i[t,u]
               + 1{t=u} sum_i mask_it n_i.

The sum is a sum of the **same** constituent observations, not an independent
meter. Native missingness changes both operator and temporal covariance.

**Proposition 2 (replacement).** If a=T y is deterministic and y is later
observed, p(c|a,y)=p(c|y), with compatible a. Replace (R_A,gamma_A) by
(R_fine,gamma_fine); never add both. Proof: a is measurable in y, so it contains
no extra information conditional on y. Equivalently p(a,y|c)=p(y|c) delta(a-Ty).
The implementation atomically subtracts the old group likelihood and adds the
new one under the same source/version identity. An alternative valid partial
reveal must use p(y_revealed|a,c), including covariance; that is outside this
whole-group pilot. Separately measured aggregates require a different joint
noise model. The deliberate negative control adds both and is explicitly invalid.

Example: x~N(0,1), y1=x+e1, y2=x+e2 with iid unit noise, and y=(1,3).
The aggregate sum 4 has conditional variance 2 and operator 2: posterior mean
4/3, variance 1/3. Revealing both readings leaves those x moments unchanged
in this homogeneous example. Counting their sum again gives mean 8/5, variance
1/5. For heterogeneous loadings/noise, the fine observations can add valid
information; unchanged moments are not a universal expectation.

## Forecast summaries and cross-scale inference

For a registered linear household-output query q at lead H, conditioned on c
and group evidence, let

    q_g = baseline_g + alpha_g + B_g c + residual_g + L_g future_eta.

Given a group observation covariance V and target-observation covariance C_qy,

    alpha_g = C_qy solve(V,y),
    B_g = L_g F^H select_last - C_qy solve(V,O),
    Vq_g = Vq_prior - C_qy solve(V,C_yq).

For fine evidence these products sum over households. For aggregate evidence,
conditioning induces cross-household covariance: its negative update cannot be
discarded when forming a sum. The code computes query covariances directly.
Common future-factor covariance Q_H=sum_{j=0}^{H-1}F^j Q(F^j)^T is included once
after summing loadings. Hence

    Var(sum_g q_g) = (sum B_g) Sigma_c (sum B_g)^T
                    + sum Vq_g + (sum L_g) Q_H (sum L_g)^T.

**Proposition 3 (registered-query retention).** Store each group's exact
(R_g,gamma_g,alpha_g,B_g,Vq_g,L_g) for a fixed query set. Evicting its household
conditional factors preserves that query set's joint law after ANY updates to
other groups that leave this group's model, evidence, query support and window
unchanged. Proof: group-private residuals are conditionally independent across
groups given c; the displayed affine conditional law composes with the updated
c posterior by total expectation/covariance. This is a Gaussian sufficient-
information corollary, not a new filtering theorem. New local queries, revised
observations, parameters, coverage or windows may need reconstruction.

The implementation registers three output queries **separately at each lead**:
the full group, its evaluator-defined observed support, and its first physical
household. It retains their 3 by 3 within-lead residual covariance. It does not
retain the cross-lead covariance between the one-hour and six-hour query sets.
A joint decision using both leads would require additional conditional summaries
or restoration. Coherence here covers the reported same-lead macro/micro laws;
there is no claim that arbitrary future joint queries are free after eviction.

Macro-to-micro: changing c's posterior changes an unopened household's conditional
prediction through B_g. Micro-to-macro: local fine evidence replaces a group message
and changes c and aggregate moments. These are predictive updates, not interventions.

No lossy summary compression is used. For a future extension, if conditional
summary errors satisfy |Delta alpha|<=a and ||Delta B Sigma_c^(1/2)||<=b, then
the mean discrepancy is bounded by a+b||Sigma_c^(-1/2)mu_c||, when Sigma_c>0.
That ordinary Cauchy-Schwarz diagnostic is not implemented or claimed certified.

## Locality, costs and window boundaries

For G=16, household window L=24, global dimension r=16L, a fine group with n_g
households needs batched O(n_g L^3) local solves plus information products up to
O(n_g L^2*16^2). Its conditional cache is O(n_g L^2) with structured loadings;
do not materialize n_g L by r dense factors when their Kronecker structure is
available. Each group message uses O(r^2) memory; q registered queries use
O(qr+q^2) plus loadings. The shared separator factorization costs O(r^3).

At one fixed window, replacing one leaf needs only that leaf's matrix work and
the shared separator factorization. Reuse denominator is G leaf messages plus
one separator factor. Updating k groups reuses G-k leaf messages, but can change
every posterior query. A covariance graph with cross-group residual edges lacks
this star structure: elimination creates fill-in, larger separators, and in the
worst case O((NL)^3) dense work. iSAM2 already formalizes affected-clique/ancestor
updates; this code is a simpler exact Gaussian star, not a reproduction of iSAM2.

**Counterexample to purely local posterior effects:** two household variables
x1=c+d1, x2=c+d2 with Var(c)>0. Reading x1 changes E[x2] and Var(x2), despite
separate private residuals. “Unaffected” refers to unchanged conditional factors,
not unchanged marginal means. Arbitrary spatial coupling can also invalidate
factor reuse. Low separator rank is a modeling assumption, not free scale.

Eliminating AR detail induces dense temporal covariance V_i inside the window.
Replacing it by a memoryless variance is generally wrong: rho!=0 gives nonzero
off-diagonal entries. This pilot retains all L by L temporal covariances. At each
new origin it intentionally uses a fixed training prior and the new 24-step
evidence window, rebuilding every mask-dependent group message. This is a valid
finite-window model, **not exact all-history filtering**. It avoids double-counting
overlapping windows by never feeding the previous posterior back as a prior.
Cross-window locality remains unproved/unimplemented. Persistent snapshots record
physical IDs, cutoff, model hash, evidence state and the separator factor.

## Precision and verification limits

All fitting/inference matrix work is FP64 on the GPU. Cholesky solves are used;
small solves against identity produce reusable inverse-action coefficients for
24-step household blocks. There is no dense global household inverse. The
coarse reference solves the 384-dimensional separator. Full explicit fine joint
Gaussians are constructed only for tiny independent GPU correctness cases.

Frozen discrepancy tolerance is 1e-7 absolute and 1e-8 relative for audits; raw
mean/covariance differences are saved. This is numerical validation, not outward
rounding or a floating-point proof. No arbitrary negative quadratic-form clipping
is called certification. Gaussian forecast error, algebraic numerical discrepancy
and missing-data support are reported separately. Real development coverage does
not establish conditional calibration or independence of replay origins.
