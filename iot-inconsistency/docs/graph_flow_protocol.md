# Graph-flow study protocol

Declared 2026-10-01 before new benchmark scoring. This document and `configs/graph_flow_v1.json` define the bounded study. A separate lock will record development choices, source hashes, model hashes and calibration assignments before final scoring. Final outcomes cannot change those choices.

## Preservation and scope

`results/graph_flow_v1/legacy.json` hashes the live 306-file study. `paper/legacy/witness_20260930.tar.xz` preserves the exact previous paper, figures, bibliography and generated text. Old result files, evidence archives and model manifests remain immutable. The old paper's window-level endpoint is retained separately. New sensor-interval results cannot be substituted into it.

The primary H1 asks whether corruption integration improves candidate average precision over both development-selected PCA and ordinary NLL from exactly the same trained flow. H2 compares the flow and Gaussian/PPCA using identical corruption channels. H3 concerns useful repair coverage at a calibration-selected recommendation policy and is secondary. None of these hypotheses is assumed true.

The specified corruption densities, change-of-variable formula and posterior weighting are established probability constructions. The candidate contribution is their evaluated combination with graph-conditioned neural generation, explicit measurement-fault hypotheses, source-aware masking and inspectable repairs.

## Data and exposure

The synthetic family retains 32-channel linear, 32-channel nonlinear and 64-channel nonlinear configurations. Training, development and calibration reuse the existing 12, eight and eight trajectories and their training-only scales. This keeps the training observations identical for the frozen legacy diffusion comparator and the new models. Only final evaluation uses 12 freshly seeded trajectories. The final two test trajectories include the predeclared regime shift. Latent physical states and uncorrupted noisy measurements are distinct saved arrays. Reuse of exploratory development data is explicit.

Intel and SKAB retain their original physical-source groups, units, scaling, chronology, experiment assignment, gaps and availability. All original real partitions have previously informed the project. The new protocol therefore evaluates prospective injection draws on examined environments. It does not claim new untouched real environments. No held-out observation moves into training. Intel's reference observations are unadjudicated. SKAB's native process labels remain process labels. Controlled cases use reference windows without native events.

An initial availability audit of the live eight-step target blocks found complete targets in about 65% of Intel test candidates. This known limitation motivates explicit coverage reporting, not a post-outcome exclusion. The eligibility and sampling inventories will record exact counts.

## Candidates and labels

Every named channel's final eight completed time steps form a candidate. The 64-step window and 32-step stride remain fixed. All channels are scored exhaustively. Full target availability is required for a numeric flow density. Missing targets get an unavailable status and the common score floor for end-to-end ranking. Eligible-only metrics are secondary. Missingness alerts are separate outputs.

Primary cases contain one corrupted channel from one physical source. Other sources remain unchanged by the injection. Four fault copies and one unchanged copy share each sampled reference window. Development and calibration use bias, drift, noise and stuck mechanisms. Each test reference contributes two known-family and two held-out-family faults, rotating across spike, scale, replay and delay. New severities and seeds are fixed independently of scores. Fault truth concerns changed observed target cells relative to the reference, with attempted but unobservable edits counted separately. No candidate set is selected using fault truth.

All injected copies stay together under source-block resampling. Calibration uses whole blocks for three distinct roles, namely normal window maxima, labeled probability calibration and repair policy selection. Tail resolution is reported exactly. No nominal alarm rate below the attainable rank resolution is claimed.

## Context and models

Target values are removed before temporal features or graph messages. All channels from the candidate's physical source are masked within the tested interval. Earlier same-source history remains allowed. Known duplicate measurement identities are canonicalized before graph inputs. Context sources are conditioning information, not independent withheld witnesses. All inputs end by the decision timestamp. The graph is discovered using training and development only and remains frozen for primary scoring.

The initial flow uses a shared temporal encoder, a graph message network, query embeddings and invertible neural affine coupling layers. Affine couplings avoid adding an unverified spline dependency to the installed environment. Widths 32 and 64, four and six coupling layers, and 32/56-step context lengths form the complete capacity grid. Each fit has at most 600 steps and selects its checkpoint by normal development NLL. Learning curves use whole training source blocks. There is one uniform three-member ensemble, not three independent ensemble repetitions.

Gaussian bias and drift use one shared random amplitude across the block and positive noise floors. Noise and stuck channels also have normalized Gaussian densities. Mixture weights are fixed at one quarter. Only the two declared scale multipliers are examined. The same selected corruption model is used for flow and Gaussian comparisons. Injections need not be exact draws from this model, and held-out families are mandatory.

The sample grid is 32, 128, 512 and 2048 independent prior draws per member. Development comparisons use shared latent prefixes. The smallest budget meeting the declared score-error and ranking tolerances is selected, or 2048 if none passes. An ESS below 16 flags inadequate posterior sampling and prevents an automatic repair recommendation. Its detection score is retained. Sample budgets are never selected on final outcomes.

## Comparators and finite budget

PCA retains current/four-lag embeddings with ranks 2, 4, 8 and 16 and excludes full-rank reconstruction. Candidate aggregation is mean current-coordinate squared residual over the eight-step interval. Its existing window maximum and the full residual norm remain separately named diagnostics. Development data select rank and lag on the new candidate endpoint.

The same flow's NLL, graph-conditioned Gaussian/PPCA with identical q, mixture PPCA, official GANF, the legacy witness procedure and a supervised small tree classifier are included. Gaussian conditional densities handle missing context by conditioning on observed coordinates. Graph-restricted and all-channel context variants are labeled. GANF uses pinned author architecture and its graph objective, with documented common-protocol changes. The legacy witness screen remains visible, and excluded candidates count as misses. It is rerun on new cases rather than reusing incompatible old scores.

There are at most 80 bounded neural fits, including the linear-Gaussian pilot, capacity grid, selected seeds, own-history ablations, learning curves and GANF. Existing GPU resources are reused. No new cloud resource is created. The pilot will establish measured time and memory before scaling to the finite matrix. Runtime measurement requires an otherwise idle GPU.

## Endpoints and decisions

Primary AP pools all candidate intervals within each configuration, including clean windows. Synthetic configuration differences are averaged within that family before the three-family macro-average. Both primary contrasts use paired whole-block bootstrap intervals at 97.5% individually, giving a Bonferroni simultaneous 95% statement. The chosen practical threshold is 0.02 absolute AP. It is a usefulness convention, not a universal statistical constant.

Secondary outputs include localization, misses, window AP, attained false alarms, probability loss and reliability, review coverage, repair loss and weighted CRPS, interval width/coverage, energy score, numerical adequacy and actual computational costs. Training seeds are not test sampling units.

Repairs use posterior means for squared loss and weighted medians for absolute loss. A wrong-target action is applied to the full target block across all channels, so harm to previously correct measurements is counted. Useful improvement is greater than 0.01 in summed normalized squared error divided by the eight target steps. Failed recommendations include incorrect attribution or insufficient benefit. Harmful edits are reported separately. Zero recommendations give zero coverage and undefined risk.

The policy selects the largest calibration coverage whose one-sided 95% Wilson failure upper bound is at most 0.1, with at least ten recommendations. Dependence limits this diagnostic bound. Actual test risk and whole-block uncertainty remain mandatory. A fitted injection probability is prevalence dependent and is not a probability of physical sensor failure.

## Required diagnostics and presentation

The registered stress set uses 12 reference windows per dataset, selected evenly across blocks. It examines extra corrupted sources, partial context availability, graph errors, known copies, held-out faults and regimes. Synthetic coordinated physical changes and an observationally identical common-mode corruption pair demonstrate non-identifiability. Association hypotheses have their own direct-residual baseline and separate cross-type analysis.

Equation audits include inverse/Jacobian checks, Gaussian closed forms, correlated corruption normalization, unit changes, mixture arithmetic, posterior moments, masking, duplicate-source invariance, chunking and saved production score recomputation. Selected model/draw replay is distinct from scalar audits.

Case selection uses the first successful attribution, first failed attribution and first numerically inadequate or ambiguous case in deterministic case order, with declared fallbacks. The classic 2D network view keeps context, disputed readings and explicitly tested disputed associations distinct. No generated reading replaces an observation. Browser actions are interface tests, not a human study.

The live workshop page was checked on 2026-10-01. Full papers allow ten IEEE two-column pages including references. The main manuscript will remain self-contained within that limit. No separate supplement is presumed accepted. Source https://sites.google.com/unisalento.it/ieee-dspaces-2026/home.

## Development implementation clarifications before the lock

The timestamp audit found nonuniform SKAB sample intervals. Both injected drift
and the drift-channel covariance therefore use the eight actual timestamps from
the original experiment file. Intel uses completed 300-second bins and synthetic
data use one-second steps. Flow temporal encoders and graph lags use observation
indices and availability, without treating a lagged row as an exact elapsed-second
lag. This limitation is stated for irregular recordings. Earlier SKAB development
scores using an index ramp are preserved in `development/chronology_correction/`
and cannot select the final configuration.

A completely unavailable target population produces a complete vector of floor
scores and availability flags. It produces no numeric density or repair. A failed
Intel development population assertion exposed this path, and the correction
precedes final scoring. Partial and fully missing faults remain in coverage and
miss accounting. No test outcome selected either correction.

PPCA fits joint target and allowed context observations. Training missing context
is mean-filled only while estimating its parameters. At scoring time, missing
context is marginalized and never treated as an observed zero. Single and
two-component PPCA use rank 2, 4 or 8, selected by normal development NLL.
Two-component fits use twelve bounded EM updates. An all-channel PPCA variant
has more context than graph-restricted models and is named separately.

The modest classifier is trained on four declared fault families injected into
training reference windows and tuned on development candidate AP. It sees target
shape, earlier history, PCA residual and availability. Its exported tree traversal
is checked against sklearn predictions before use on the GPU host.

The official GANF architecture is imported without modifications. Adapters exclude
missing target losses, prohibit adjacency between channels from the same physical
source, select on development density, and sum the final eight coordinate log
densities. Its recurrent factorization can use preceding values inside the tested
interval. This differs from the proposed block-masked generation policy and is
reported explicitly. Missing context is filled with zero for this original
architecture, which has no explicit availability-mask input. The finite graph
optimization may leave a nonzero acyclicity residual. We report that residual and
do not claim exact DAG convergence.

Probability calibration uses the raw score, robustly scaled on its labeled
calibration role, and a scorable indicator for every method. It describes the
benchmark candidate prevalence. Repair recommendations take the maximum raw-score
candidate, apply the shared eligibility rule, and apply the calibration-selected
probability threshold. Flow repairs also require ESS at least sixteen. This
sampling rule is distinct from fault confidence. Recorded sensor quantization is
approximated by a continuous density consistently in both hypotheses.

The 32-channel linear and nonlinear synthetic configurations use paired generator
seeds. Their block bootstrap draws are therefore shared. The 64-channel trajectories,
Intel blocks and SKAB experiments are independently resampled. Correlated channels
and injected copies never become independent test subjects.
