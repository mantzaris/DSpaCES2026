# Equation audit

The authoritative specification is `DSpaCES_2026_research_plan_and_Codex_prompt.txt`. The complete Part C reference was extracted unchanged into `reference/reference_score.py`. Its thirteen preparation checks pass. The production scorer uses the PyTorch implementation in `src/iot_repair/scoring.py`. `equation_to_code.json` maps the specification identifiers to manuscript labels and executable functions.

The saved parity inputs are in `results/audits/arithmetic_inputs.npz`. CPU and GPU runs use this same file. Float64 tolerance is 1e-11 and float32 tolerance is 2e-6. The CUDA maximum component errors were 1.11e-16 and 8.56e-8. These statements are arithmetic verification, not detection claims.

All sixteen required checks have executable coverage

| Check | Executable evidence |
| --- | --- |
| Pairwise CRPS equivalence | `test_crps_pairwise_and_unit_change`, `audit_saved_scores.py` |
| Deterministic absolute error | extracted oracle `run_numerical_checks` |
| Affine unit invariance and edit costs | oracle and `audit_equations.py` |
| No-op edits and retained cost | `test_complete_pipeline_no_op_has_zero_gain_and_fixed_targets` |
| Harmful edits | oracle and `test_invalid_loss_abstains_and_penalties` |
| Edit-penalty slope | oracle and penalty integration test |
| Model-disagreement penalty | oracle and batched CUDA parity |
| Known copies at the model boundary | `test_production_boundary_deduplicates_values_and_messages` |
| Conflicting copies | upstream canonicalization and conflict integration test |
| Scalar CPU/CUDA parity | `audit_equations.py`, identical saved tensors |
| Fixed witness cells and hashes | pipeline test and production sample audit |
| Hidden witness sentinel | `test_hidden_witness_values_cannot_affect_proposal` |
| Labels, future and repaired targets excluded | model API boundary, causal prefix test, sentinel masks |
| Missing predictions cannot lower loss | finite checks and missing-edit test |
| Tail ordering, ties and resolution | oracle and tail integration test |
| Edge deletion preserves targets | attribute-sensitive graph test and pipeline fixed-target audit |

`audit_saved_scores.py` passed on all 1,092 primary test cases and 8,736 candidates. Its maximum absolute discrepancy was 7.11e-15 at tolerance 1e-10. The report is `results/audits/production_equations.json`. It independently recomputes pairwise CRPS from every saved primary test prediction, group losses, edit cost, gain, sample standard deviation and Monte Carlo diagnostic. It also calls the exact NumPy oracle on production loss arrays and verifies artifact hashes. No illustrative score may be substituted for this audit.

The example R = 0.50, U = 0.05, Omega = 0.10, kappa = 1 and lambda = 0.2 gives S = 0.43. It is illustrative arithmetic only.

The neural precision experiment is distinct from arithmetic parity. bfloat16 neural predictions can differ from float32 predictions. State updates remain float32 and loss accumulation remains float64. Saved development sensitivity outputs quantify this change.

## Limited properties

Known-copy invariance assumes canonicalization before prediction and group aggregation, identical unique input values, fixed learned parameters and fixed sampling randomness. Unique input matrices and relation messages are unchanged, so proposal and witness predictions coincide. Unique target cells, weights and edit denominators also coincide. Therefore R, U, Omega and S coincide. Unknown aliases do not meet this assumption.

The penalty derivatives are -U and -Omega. A pairwise ranking changes only when the gain difference crosses the corresponding weighted penalty difference. With one-edge masks and a fixed edge count, the edge cost is constant across hypotheses. Its penalty cannot improve within-type association ranking or a common rank-tail calibration. This structural limitation must be stated when interpreting that ablation.

The rank-tail result requires exchangeability of the full score units, including selection and inference randomness. It is established conformal theory. No such exact validity is asserted for these temporally dependent or shifted sensor windows. A common-mode measurement vector has both a changed-process explanation and an unchanged-process explanation with coordinated sensor errors. The available measurements alone cannot identify which explanation is true.

Witness identity hashes are scoped to one immutable decision window. A complete evidence identity combines the window artifact and its SHA-256 hash with the saved source/channel/time cell identities. The graph evidence-group ID also includes that window identity. A repeated local cell index in another window is not treated as the same observation.

Trained-model CUDA copy invariance also passed with exact predictive-array equality in all five configurations under deterministic reductions. Ordinary CUDA reduction repeatability is measured in `results/audits/inference_repeatability.json`; fixed sampling seeds alone are not a bitwise-reproduction guarantee. The primary score audit uses the original saved draws and is unaffected by resampling variation.

The conventional PCA total squared reconstruction error B2 and all-coordinate attribution B3 are explicitly evaluated in `results/pca_total/analysis.json`. Independent double-precision projections verify both statistics for all eight rank/lag settings in development, calibration and test for every configuration. The frozen primary comparator uses the maximum standardized current-coordinate contribution. The paper distinguishes that harmonized evaluation from the additional conventional total-error results.

E14 was executed on 319 native SKAB windows from 10 held-out experiments. GDN retained 16 process alerts during attribution abstention. No native sensor-fault labels were inferred. Development ranking reversals, M/L/E sensitivity, correlations, missingness and source/graph/training stress are saved in `results/equation_analysis.json` and its linked case files.
