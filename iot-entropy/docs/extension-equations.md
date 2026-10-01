# Equation-to-function and artifact map

| Measurement or operation | Implementation | Saved evidence |
|---|---|---|
| Complete-case sample Gram correlation, shrinkage, eigenvalue entropy | `entropy.window_features`, `entropy.entropy_from_correlation` | v1/v2 spatial measurements, complete-row counts, mathematical tests |
| Spatial level and lagged change | `entropy.trajectory_features`, `features.Scan.extract` | `measurements.npz:spatial`, replay spatial levels/changes |
| Permutation templates, stable ties, ordinal frequencies and normalized entropy | `temporal.permutation_entropy` | per-sensor values, template/tie counts; explicit permutation tests |
| Common unordered sample-template pair set, Theiler exclusion, A/B and censoring | `temporal.sample_entropy` | `measurements.npz:support`, censored/flat flags, CPU pair oracle |
| Causal coarse-graining with invalid missing bins | `temporal.coarse_grain`, `temporal.multiscale_trajectory` | `multiscale-development.json`, `results/extension-v2/diagnostics.csv.gz`, `multiscale-calibrated.json` |
| ACF, difference/local variance, trend, mean and CUSUM | `temporal.conventional` | ten temporal feature levels/changes and support counts |
| Current and lagged temporal endpoints from one trajectory | `temporal.trajectory` | `measurements.npz:temporal`, selected replay |
| Joint bootstrap conditioned only on history/calendar | `reference.BlockBootstrap` | reference manifest, cached joint `.npy` draws |
| Graph-conditioned DDIM trajectories and masked denoising objective | `models.GraphDiffusion`, `training.fit` | original checkpoints/training logs, cached joint trajectories |
| Robust median/MAD residual, development floors and reference support | `extension.floor_from_development`, `extension_scoring.summaries`, `extension_scoring.score` | development parameters, calibration arrays, predictions |
| Full correlation-matrix level and change discrepancies | `features.score_features`, `extension_scoring.extract`, `extension_scoring.summaries` | SB/B/BST scores, matrix replay overlays |
| Top-k temporal group aggregation and feature union | `extension_scoring.aggregate`, `extension_scoring.score` | family scores and availability |
| Rank calibration of complete scan maxima | `calibration.rank_pvalues` | `calibration.npz`, exact score-to-rank reconstruction in reporting |
| Participation, direct and combined ranks | `extension_scoring.summarize_scores`, `extension_scoring.primary_localization` | three ranking alternatives per event/decision/family |
| One-to-one event onset matching and event-PR envelope | `evaluation.match_events`, `evaluation.event_pr_curve` | event rows, raw PR curves, unconditional/conditional metrics |
| Paired uncertainty with repeated seeds/injections retained | `extension_reporting.paired`, `evaluation.bootstrap_mean` | paired block differences; no window-level independence assumption |
| Historical context/target and partition constraints | `extension_data.verify_target`, `reference.issue_reference` | issuance/decision reference manifests, leakage tests |
| New independent synthetic simulations and background reuse | `extension_data.extension_data`, `extension_data.new_events` | explicit source hashes, split/seed/block lineage, fault manifests |

All new experiment paths are under `experiments/extension-v2`. Heavy joint
trajectories and full per-sensor measurement arrays are preserved on the
experiment host and excluded from Git. Compact predictions, calibration,
support summaries and manifests are the inputs to the publication tables.
The original `experiments/full` and `results` namespaces remain unchanged.

S/SB primary localization is participation, PE/SE/T/TB is direct temporal
ranking, and ST/B/BST averages rank percentiles. Alternative localization
columns separate detection changes from that choice. Direct localization for
a spatial-only alarm explicitly adds temporal evidence; it is not relabeled
as attribution intrinsic to spatial entropy.

CUDA simulation random streams are reproducible in the recorded CUDA
environment, but CPU and CUDA random-number generators need not produce the
same trajectories from the same integer seed. CPU/GPU agreement checks concern
statistical definitions evaluated on identical input arrays. Regenerate full
synthetic backgrounds using the recorded device/software, or retain the
generated experiment arrays.
