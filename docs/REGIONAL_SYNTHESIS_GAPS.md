# Synthesis checks frozen before new saved-output analysis

2026-09-24 UTC (local project date September 23). Starting source 99dc6b8.
No model, policy, calibration threshold, target, or original result is changed.

| Gap and relevance | Available evidence and check | Estimated CPU cost | Resolution rule |
|---|---|---|---|
| RQ1: representation versus additional information | Registered-query checks, retention accounting, streamed fine comparator and same-evidence replay traces | <1 minute | Restrict preservation to registered same-horizon queries; do not claim a capacity advantage. |
| RQ3: scores versus action | Reconstructed Stage 3 per-update score vectors and identity hashes | <1 minute | Count score perturbation versus strict gate margin. This is a sufficient diagnostic bound, not a new policy evaluation. |
| RQ3: changed schedules versus useful recovery | Fresh Stage 4 access IDs, alarms and per-episode records | <1 minute | Establish timing of changed reads relative to the inclusive lag-0-through-6 detection window. Missing per-meter scores remain a limitation. Do not infer causality from an association. |
| Paired uncertainty and cohorts | Per-episode forecasts and detection outputs, background IDs | <1 minute | Display all eight/four background averages. No independent-hour error bars or equivalence claim. |
| Alarm denominators | Completed Stage 4 calibration audit | <1 minute | Preserve deployed any-channel/update definition and compare like burn-ins; no retuning. |
| Detection-window wording | Existing analysis uses onset <= step <= onset+6 | Reading only | Clarify seven observed update instants over three hours; misses assigned seven half-hour steps. Original numbers stand. |
| Bibliographic and venue status | Official workshop/portal, primary author/publisher versions | Reading only | Record inaccessible texts; use verified claims only. |

All substantive numerical experiments already exist. No additional GPU verification
is planned. If a decisive unsupported claim needs new experiments, omit or narrow
it and complete the author-review manuscript. Local document builds and saved-output
jobs are recorded by `scripts/synthesis_job.py`; they do not reopen the closed GPU
allocation window. The pod remains billed while idle. Its billing is not silently
represented as free hardware time or subtracted from experimental caps.
