# Graph-flow claims and evidence

Completed 2026-10-01 UTC. This audit concerns `graph_flow_v1` only. The preserved
witness study keeps its separate `CLAIMS_AUDIT.md`, equation map and result files.

## Primary question

The protocol pools all declared sensor intervals, including clean windows,
uncorrupted candidates and unscorable true faults. It evaluates 1,500 cases and
54,080 candidates. Synthetic linear and nonlinear configurations are averaged
within one family before the three-family macro contrast. Three trained members
form one ensemble, not three independent repetitions.

| Comparison | Macro AP difference | Paired block interval | Interpretation |
| --- | ---: | --- | --- |
| Ratio minus PCA | 0.1311208434 | [0.0926503270, 0.1472380173] | Supports directional comparison |
| Ratio minus identical-flow NLL | 0.0148076824 | [0.0052393659, 0.0273660030] | Supports direction, misses 0.02 point-estimate margin |
| Ratio minus graph PPCA with identical q | 0.0539038025 | [-0.0066119092, 0.0824291819] | H2 inconclusive |
| Ratio minus supervised trees | -0.1404423042 | [-0.1693080177, -0.1144010249] | Trees are stronger |
| Integrated ratio minus mean plug-in | 0.0033318648 | [-0.0074222134, 0.0198757875] | Integration benefit inconclusive |
| Graph context minus own history | 0.0528795997 | [0.0284311716, 0.0770075014] | Supports context contribution in this protocol |

The first two intervals are 97.5% individually for a Bonferroni simultaneous 95%
statement. Others are descriptive 95% intervals. The authoritative unrounded values
are `analysis.json:paired_macro_comparisons`. H1 is supported directionally on this
defined protocol. Neither its macro result nor its interval establishes improvement
on every dataset or broad operational superiority.

PCA is stronger on both 32-channel synthetic configurations, with negative paired
intervals. The ratio improves over PCA on S64N, Intel and SKAB. SKAB drives much of
the family-macro gain. Intel ratio AP remains about 0.075. Only 65.0% of its target
blocks are eligible, and 37 changed targets remain unscorable misses. Supervised
trees beat the ratio in every configuration. The primary table preserves all
methods, including GANF and shared-manifest legacy comparators.

Evidence is in `analysis.json`, per-configuration `analysis.json`,
`bootstrap_ap.npz`, `screening_and_fault_families.json`, the frozen protocol and
the exact case records in `publication/`. `paper_claims.json` hashes numerical
manuscript sources. The production audit and publication audit use independent
arithmetic rather than trusting a displayed table.

## Neural generation and what deserves credit

`GraphFlow.sample` draws latent vectors and applies the trained inverse on the
GPU. `flow_inference.infer_case` evaluates normalized corruption densities at
these samples. `flow_math.score_candidates` uses density mixtures, not averaged
log likelihoods. `summarize_repairs` uses likelihood weights over all members and
draws. Full bundles preserve contexts, masks, draws, generations and log densities.

The exact same checkpoints supply ordinary NLL. Graph PPCA and mixture PPCA use
the identical corruption family, context opportunity and likelihood-ratio rule.
H2 intervals span zero. Lower PPCA CRPS and energy score on every configuration
further limit claims of superior neural repair distributions. The deterministic
prior-mean control is also not clearly worse in AP. Thus the study does not
establish that flexible neural modeling or integration is necessary for the gain.

Single-member and member-average-log-ratio ablations remain reported. The latter
is not substituted for the frozen density-mixture method after observing its
larger macro AP. Leave-one-channel-out, scale, sample-budget, learning-curve and
own-history results are retained. No test result selected a new model or prior.

## Confidence, alarms and repair

Logistic calibration, normal window maxima and repair policies use separate
whole calibration blocks. Probabilities describe injected changes at the designed
candidate prevalence. They are not physical failure probabilities.

Intel ratio Brier score is about 0.068 versus PCA's 0.017. Its minimum attainable
rank p-value is 1/17, so 1% and 5% alarms are unavailable. At 0.10, 79 of 82 unchanged
cases alarm. Some unchanged cases are injection attempts with no changed observed
coordinate. This serious transfer failure rules out claims of a usable Intel alarm
system. Intel accepts no repairs, giving zero coverage and undefined risk.

On SKAB, 123 of 320 cases receive a flow repair recommendation. Twenty-four are
failed recommendations, all harmful. Test risk is 0.1951, with a descriptive block
interval [0, 0.4001]. The point estimate exceeds the 0.10 calibration target. PCA
and PPCA risks are approximately 0.3714 and 0.1834. H3 is not established as a
general controlled-risk coverage advantage. Zero observed synthetic failures do
not prove zero population risk, particularly with dependent source blocks.

Repair evaluations include oracle-target distributions and end-to-end actions.
Wrong-target edits count damage to previously correct measurements. CRPS, joint
energy, width, coverage, accepted failures and harmful edits remain separate.
Sources are per-configuration repair rows, `analysis.json`, calibration records
and the confidence/repair figures. Curves are threshold sweeps, not test-selected
operating policies.

## Failure conditions and independent evidence

Held-out spike, scale, replay and delay faults were absent from development
mechanisms. Ratio AP falls substantially on them. Corrupted support and missing
context change rankings. When several channels are truly faulty, reduced ranking
of the original target does not by itself mean an incorrect fault was chosen.
The stress results therefore retain all-target AP as well as original-target rank.

Graph-only errors can trigger measurement alarms. Separate direct-residual
association hypotheses and cross-type counts prevent interpreting a reading score
as proof of a false edge. Twelve constructed S32N coordinated physical changes
all trigger the 0.10 reading alarm. Each has an identical-observation common-mode
corruption counterpart, demonstrating a limit of identification rather than a
detector-discovered ambiguity guarantee.

The SKAB native task has 224 windows and 78 process-event windows. Ratio, NLL and
PCA window AP are approximately 0.536, 0.546 and 0.499. These events are not sensor
failure labels. The legacy top-four screen is retained visibly, with excluded
faults counted as misses. Its old window results are not mixed into new interval
results.

Fresh synthetic final trajectories are independent draws within the same simulator
family. All real recording partitions had been examined in the earlier study.
Fresh real fault draws test prospective injection behavior, not independent
environment transfer. No test recording was moved into training. Source blocks,
not coordinates or injected copies, form the bootstrap sampling units.

## Numerical checks, costs and reproducibility

Eight scalar check groups, forty tests and the GPU Gaussian pilot pass. Production
replay reconstructs 107,620 scores within 9.10e-13 and thirty complete generation
bundles directly from GPU models and latent draws. Gaussian component densities,
mixture arithmetic, masking, units, posterior moments and full-window action
losses are checked separately. See `equation_audit_graph_flow.md` for measured
float32 inverse tolerances and the precision correction to the independent audit.

The selected three-member ensembles have roughly 97,000 parameters per member.
Operational ratio plus repair takes about 22–23 ms per window outside SKAB and
112.5 ms on SKAB, versus about 9–11 ms for NLL and 0.10–0.15 ms for CPU PCA.
SKAB still has a 0.952 95th-percentile repeated-seed score change at 2048 draws per
member. A finite maximum sample budget does not establish convergence. All seventy
neural fits total 10.8 recorded fitting minutes, excluding data preparation,
Gaussian fitting, inference and analysis. `runtime.json` and development records
provide the exact definitions and hardware. GANF's finite acyclicity residuals
are reported, not described as converged graphs.

The classic operator view and idempotent Neo4j import are implemented and locally
verified. The 23 cases include successes, failures, numerical inadequacy, ambiguity
and association review selected by a predeclared rule. Browser clicks create
separate automated test decisions, not human-study evidence or measurement edits.

No required finite study stage is blocked. Optional MTGFlow execution and dynamic
graph adaptation were not included. No untouched real-environment validation or
human operator study was performed. Git contains compact evidence sufficient for
metric and sampled-equation replay. Weights and raw caches are locally available
and recorded by exact hash and location, but are not distributed in Git. A public
model-inference reproduction still requires those weights or retraining.
