# Mathematical statements and implementation links

For a PSD m-by-m correlation matrix, eigenvalues are nonnegative and sum to m.
Normalized eigenvalues therefore form a probability vector. Shannon's entropy
bound gives 0 <= H <= 1. Identity attains 1; a rank-one correlation matrix,
including an outer product of signs, attains 0 at zero shrinkage. With lambda>0,
the minimum is the entropy of `(1-lambda+lambda/m, lambda/m, ..., lambda/m)`:
each shrunken probability is at least lambda/m, and this maximally concentrated
vector majorizes all feasible vectors. Shannon entropy is Schur concave.

If R comes from n centered observations, rank(R)<=min(m,n-1). At zero
shrinkage H<=log(min(m,n-1))/log(m). Autocorrelation does not change this
algebraic bound but reduces effective information; the n>=2m rule is a
conservative eligibility heuristic, not a guarantee of independent samples.

For R(rho)=(1-rho)I+rho*11', the vector 1 has eigenvalue 1+(m-1)rho;
its orthogonal complement has eigenvalue 1-rho. Dividing by m and differentiating
`-sum(p log p)/log(m)` cancels the constant derivative terms because sum(p')=0,
yielding `(m-1)/(m log m)*log((1-rho)/(1+(m-1)rho))`. This is nonpositive
for 0<=rho<1. Under shrinkage evaluate it at (1-lambda)rho and multiply by
(1-lambda). No general monotonic fault or synchronization law follows.

For m=4, equicorrelation .2 has spectrum (1.6,.8,.8,.8). Two block-diagonal
2-by-2 correlation matrices with within-pair .6 have eigenvalues
(1.6,1.6,.4,.4). Both are positive definite with unit diagonal. Off-diagonal
upper-triangle sums are 1.2, hence mean correlation .2, and both leading
eigenvalues give concentration .4. Their zero-shrinkage H values are
.9609640474 and .8609640474. This demonstrates sensitivity to organization
lost by those simple summaries, not an advantage over observing R itself.

Conditional on a fixed trained scoring rule, let calibration maxima M_1,...,M_n
and a null test maximum M_* be exchangeable. Rank the n+1 scores from largest
to smallest with random tie-breaking. The test position is uniform by symmetry.
The p-value using greater-or-equal ties is at least its randomized rank/(n+1),
so P(p<=alpha)<=floor(alpha(n+1))/(n+1)<=alpha. Maxima must use the same
predeclared scan family and eligibility rules. Comparing one group's score to
these maxima is conservative relative to the test maximum. This is per unit,
not indefinite stream control. Dependence, real-data contamination or changes
to the scoring rule invalidate the exchangeability argument; a gap alone
does not prove exchangeability. Empirical calibration diagnostics are essential.

SRS with diagonal signs S and PRP' with permutation P are orthogonal
similarities and preserve H. Per-sensor offsets and positive scaling preserve
Pearson R. A coherent nonzero-variance fault and a normal common driver can
share the same spectrum. A constant channel has undefined Pearson correlation.
The implementation flags it rather than assigning zero entropy.

| Paper statement | Code | Check |
|---|---|---|
| PSD correlation and H | `entropy.window_features`, `entropy_from_correlation` | `test_limits_shrinkage_and_counterexample`, `test_missing_constant_and_disagreement` |
| Equicorrelation derivative | `entropy.equicorrelation_derivative` | centered finite differences |
| Trajectory and signed residuals | `entropy.trajectory_features`, `features.score_features` | shared reference and eligibility checks |
| Rank calibration | `calibration.rank_pvalues` | exchangeable-null simulation, ties and minimum p |
| Context chronology | `data.issuance_indices`, `reference.issue_reference` | split containment and target perturbation invariance |
| Localization and event matching | `localization.set_metrics`, `evaluation.match_events` | exact known sets; no credit for a pre-onset alarm |
| GPU numerical precision | `entropy.window_features` | CPU float64 vs CUDA float32 |
