# Graph-flow equations and assumptions

This is a separate equation namespace from the preserved witness study. Its map is
`equation_to_code_graph_flow.json`. Arithmetic tests and the Gaussian GPU pilot
have passed. Full benchmark production replay will be recorded in
`results/graph_flow_v1/production_equation_audit.json` after execution. A missing
production record means that stage has not passed yet.

## Density and generation

For fixed allowed context c, the affine coupling composition f is invertible.
Every scale is the exponential of a finite bounded neural output. Its Jacobian is
triangular in each coupling, so the log absolute determinant is the sum of the
coordinate log scales. Applying change of variables gives E1. Applying the inverse
to standard normal draws gives E2. Minimizing reference-candidate mean negative
log likelihood gives E3. Reference means the declared training population, not a
certificate of healthy physical instrumentation.

The implementation masks the tested source's entire target block before the
recurrent encoder, graph messages or context statistics. Altering hidden target
values cannot change c or a prior generation with the same latent draw. It changes
the observed-target density. The prior samples used below are therefore independent
of the tested target conditional on c and the trained parameters. Supporting
sensors are conditioning variables, not withheld independent witnesses.

## Normalization and the likelihood ratio

E4 uses this conditional density as the normal hypothesis. E5 uses four Gaussian
conditional densities. Bias and drift have block-correlated covariance from one
shared amplitude. Stuck readings use the affine map H = 1 e_1^T. Positive diagonal
noise makes every covariance positive definite. The drift ramp uses actual target
timestamps, including irregular SKAB intervals. Mixture weights are nonnegative
and sum to one.

T1 follows from Tonelli's theorem. For fixed context, the nonnegative integrand in
E6 permits changing integration order. Integrating q(y|z) over y gives one, then
integrating p(z|c) over z gives one. Thus the fault density is normalized on the
same continuous target space. Quantized observations use a consistent continuous
approximation in both hypotheses. Missing targets are never silently filled and
scored as complete observations.

E7 is a likelihood ratio on that target space. E8 estimates its numerator by the
mean of densities evaluated at actual inverse-flow generations. Its density
estimate is unbiased under independent prior sampling. Jensen's inequality shows
that the logarithm generally has downward bias. The log-sum-exp implementation
never substitutes mean log density or the best generation. Repeat-seed and draw
budget studies estimate numerical sensitivity, not physical correctness.

For E9 the normal ensemble is a uniform mixture of normalized model densities.
The fault ensemble integrates q against that mixture. Equal draws per member
therefore give a mean over all member/draw pairs. Averaging member log ratios has a
different meaning and is a separately named ablation.

For T2 assume the true healthy conditional law equals p_normal and p_fault is
absolutely continuous with respect to it. Then

    E_normal[exp(S) | c] = integral p_fault(y|c) dy = 1.

Markov's inequality gives P_normal(S >= log(1/alpha) | c) <= alpha. These are
established likelihood-ratio facts. They do not validate a learned detector under
density error, contaminated context, dependent window selection or distribution
shift. A maximum over sensor candidates does not inherit the single-candidate
bound. The pipeline instead calibrates actual window maxima on separate reference
blocks, reporting the exact minimum attainable rank p-value. A mixture of valid
ratios with fixed nonnegative weights summing to one retains the ideal expectation
property. Data-selected weights do not acquire that property without justification.

For T3 let u = g(y) be a common differentiable bijection and transform both model
densities and the corruption channel consistently. Both numerator and denominator
multiply by |det Dg^{-1}(u)|. Their ratio is unchanged. This is not invariance to
inconsistent scaling, retraining, or replacing the corruption prior. Numerical
tests use a non-diagonal affine transformation and an offset.

## Gaussian reference and conditional repair

T4 takes z ~ N(mu,Sigma) and y = z + eta, eta ~ N(0,R), independently. Gaussian
convolution gives p_fault(y) = N(y;mu,Sigma+R). Consequently

    S = -1/2 log[det(Sigma+R)/det(Sigma)]
        + 1/2 (y-mu)^T [Sigma^{-1}-(Sigma+R)^{-1}] (y-mu).

Completing the square yields posterior mean
mu + Sigma(Sigma+R)^{-1}(y-mu) and covariance
Sigma - Sigma(Sigma+R)^{-1}Sigma. The implemented affine-channel extension replaces
y's mean by H mu and covariance by H Sigma H^T+R. Mixture posterior component
weights are proportional to prior component weight times observation likelihood.
Both PPCA controls and the independent numerical reference exercise these formulas.

E10 is Bayes' rule for the uncorrupted interval given the recorded interval under
the declared fault hypothesis. Prior sampling leaves weights proportional to
q(y|z_m). The code normalizes these weights over the entire uniform ensemble,
then computes weighted means, variances and marginal quantiles. Hidden reference
truth enters only afterward for offline scoring. No generation is selected using
its reference error. E11 is the usual inverse squared-weight sum. Low ESS means
poor importance-sampling resolution and triggers a numerical abstention for
recommendations. It is not a direct estimate of physical uncertainty.

E12 measures the loss difference after applying the proposed action to the full
window. Incorrect attribution is a failed recommendation even when an edit happens
to reduce an incidental error. A correct-target change with improvement at most
0.01 also fails the useful-edit definition. Negative improvement is separately
harmful. The denominator is all evaluated cases for coverage and accepted cases
for risk. Empty acceptance gives undefined risk. Weighted marginal CRPS is exact
for the empirical weighted distribution. The joint energy score uses independent
weighted resampling pairs and reports its finite-sample nature.

## Identifiability and evidence limits

For T5 consider two sensors measuring the same latent process x_t. A coordinated
physical change from x_t to x_t+a_t produces readings (x_t+a_t,x_t+a_t). An unchanged
process with the same additive corruption a_t in both sensors produces exactly the
same readings and available context. Without another source of information no
function of those observations, including the proposed ratio, can distinguish the
two explanations. The synthetic stress study stores such an identical-observation
pair, with separate latent-process truth. Its ambiguity label is a constructed
counterexample, not a claim that the detector discovers every ambiguous case.

Predictive graph edges do not establish causation. A high reading score is not a
proof that an association is false. Separate relation hypotheses and direct
residuals are assessed in the cross-type study. Calibrated fault probabilities
refer to injected numeric changes at the benchmark prevalence. They do not identify
unknown physical truth, deployment fault prevalence or native SKAB process events.
