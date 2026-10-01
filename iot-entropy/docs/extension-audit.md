# Audit and implementation corrections

The v1 study is preserved at the revision in `experiments/extension-v2/original-study.json`.
The audit reproduces the requested recall, unconditional localization, Intel
eligibility and background exceedance checkpoints. Its fidelity checkpoint is
**reference-common support**, giving Intel 0.09167; diffusion-only support gives
0.22191. These are different denominators, not conflicting measurements. The
synthetic fidelity row is specifically 64 nodes, not a three-size macro average.

Event matching checks confirm one-to-one alert-onset matching, no point
adjustment, and no credit for an alert beginning before the injected interval.
All v1 primary scoring contexts end before the injection. GDN instead uses
causal observed target history for one-step prediction; this different forecast
lead is retained and disclosed. Bootstrap donors are joint training blocks.
The diffusion API receives context, masks, graph and known calendar, not targets.
New code additionally asserts split and simulation containment at every issuance.

Two implementation distinctions were found while integrating v2, before any
extension results were analyzed. First, v1's maximum over finite components can
score a feature level even if its lagged change is undefined. V2 requires **both
endpoints** for each level/change feature pair, as specified in the frozen
extension protocol. Second, v1's full-matrix comparator measures current R's
distance from the reference center; it does not separately measure Delta R.
V2 includes both the current-matrix discrepancy and a reference-standardized
Frobenius discrepancy of Delta R, computed from the same joint trajectory.
These are explicit scoring corrections/extensions; v1 outputs remain unchanged.

A first v2 integration run was interrupted after finding these distinctions;
its runtime is counted, its target-independent forecasts can be reused, and it
produced no accepted final result. The complete final comparisons use the
corrected code. Missing template endpoints never become zero-valued evidence.
Common-support localization also restricts contributing temporal windows and
channels, rather than merely restricting the final sensor list.

The original complete-row correlation rule is retained. It removes many Intel
group windows even when individual sensors have sufficient temporal support.
V2 separates operational support, common feature support, reference support,
and explicit data-quality flags. No PSD covariance repair is promoted to a main
method without recalibration; v1's Gaussian covariance-EM sensitivity remains
an identifiable auxiliary experiment.

Floors are fitted on development observations. Reference MADs are model
distribution summaries, not a Gaussian tail claim. Primary thresholds use only
calibration; test background exceedance is evaluation. Any rate-matched view
using test controls is descriptive. Participation ranks are not causal evidence.

The original paper's figures and numerical tables were generated from saved
outputs; its source generator is retained. The revised paper uses its own
extension output namespace and a claim-to-evidence ledger. Neither native Intel
nor native PEMS events are certified physical faults by these experiments.
