# Claims audit

The manuscript is generated from saved experiment outputs. `results/paper_claims.json` records each generated numerical value, its JSON path or explicit aggregation, the source hash and the generated LaTeX hash. `paper/figures/provenance.json` records figure inputs. Draft status is explicit until native events, all ablations and final audits have finished.

| Claim | Saved evidence | Interpretation and limits |
| --- | --- | --- |
| The equations are executable and used for candidate ranking | `results/study/*/test/provenance.json`, case JSON/NPZ pairs, `results/audits/production_equations.json` | 1,092 primary cases and 8,736 candidates. Independent pairwise CRPS, costs and oracle score reconstruction passed. |
| PCA has higher observation window AP in the three synthetic configurations and SKAB | `results/analysis.json`, each observation track's `paired_difference` | Development-selected PCA comparator. Whole trajectory/day/experiment bootstrap. Intel difference is inconclusive. |
| S32N gives higher attribution precision at 10% screened-candidate coverage | `results/confidence_comparisons.json`, `results.synthetic_32_nonlinear.observation.paired_secondary_endpoints.precision_difference_at_0.1` | Difference 0.1875, interval [0.046875, 0.265625]. Secondary descriptive interval, no multiplicity adjustment. Same 640 screened eligible candidates. |
| The S32N review advantage reverses at broader coverage | Same artifact, `precision_difference_at_0.25` and `precision_difference_at_0.5` | The primary detection endpoint still favors PCA. Do not imply a general attribution advantage. |
| S32N fitted probabilities have lower Brier loss than the selected PCA comparator | Same artifact, `brier_main_minus_comparator` | Difference -0.01843, interval [-0.02689, -0.00723]. Calibration is labeled and prevalence dependent. A null tail is not a probability. |
| Association detection does not establish a clear advantage | `results/analysis.json`, association `paired_difference` in all five configurations | Every interval includes zero. Baselines without association output are not assigned zero accuracy. |
| The penalties do not uniformly help | Frozen `selection` and ablation methods in `results/analysis.json` | Cost is selected only for Intel, with no AP change at displayed precision. S32N selects gain alone. SKAB spread penalty reduces both false alarms and recall. |
| Candidate screening misses true faulty sources | Primary methods' `screening_recall`, `top1`, `candidate_ap` | Misses remain in attribution denominators. The review pool is shared for confidence comparisons. |
| Metadata matching is incomplete | `results/audits/association_metadata.json` | Degrees and marginal edge attributes are matched, but a metadata-only classifier still identifies some joint shortcuts. SKAB ROC area is 0.734. |
| Calibration has limited resolution and imperfect empirical transfer | Each method's `null_reference_units`, `null_resolution`, `operating_points`, `probability_evaluation` | No configuration supports the 1% window-tail level. No temporal exchangeability guarantee is claimed. |
| Exact known copies can be removed without changing model evidence | CPU integration tests and `results/audits/inference_repeatability.json` | Trained CUDA equality is tested with deterministic reductions. Unknown source aliases do not satisfy the assumptions. |
| Portable weights preserve trained inference state | `results/model_weights/manifest.json`, `results/audits/portable_models.json` when complete | Exact state and deterministic checkpoint/NPZ predictive agreement. Ordinary CUDA seeded replays are measured separately. |
| Native SKAB results concern process events | `results/native/skab/analysis.json` when complete | No native broken-sensor or false-edge truth is inferred. Process alerts remain independent of attribution abstention. |
| The operator application persists review evidence | `results/graph/persistence_audit.json`, `results/interface/browser_verification.json`, `results/operator_decisions.jsonl` | Automated interface tests only. No human performance, diagnosis, causal identification or actuation claim. |

The worked S = 0.43 example is illustrative arithmetic. Model member seeds are not independent repetitions of the full ensemble. Primary evaluation uses one three-member ensemble. All intervals preserve source blocks rather than treating overlapping windows as independent.

The original saved predictive draws are authoritative for reported metrics. Float32 CUDA graph reductions followed by bfloat16 denoising can vary under a fixed seed. The repeatability audit reports this variation instead of replacing original outcomes with a preferred replay. Exact arithmetic agreement is evaluated on identical saved inputs.

Conditional family, strength, duration and regime analyses are diagnostic. Stress cases before `scaled-screen-stratified-v3` are retained under versioned subdirectories and excluded from the final stress summary. Negative, inconclusive and unsafe-ablation outcomes remain available.
