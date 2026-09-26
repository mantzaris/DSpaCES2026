# Diagnostic artifact definitions

All times/indices are half-hour updates; episode step0 corresponds to source
array index23. Physical identity is `(model.meters[index], source.timestamp)`.
`probe_ids` are indices into the frozen training-eligible4194-meter array.
Requested identity hashes preserve probe-then-extra read order; canonical hashes
sort indices. Original identities are rebuilt directly from saved access rows.
Finite current records form assimilated identities. Missing attempts consume
budget but are not observations. Raw arrays remain unchanged and absent from git.

`results/acquisition/diagnostic/steps.csv.gz` reconstructs112 original episodes:
- `probe_values`, `probe_prediction`, `probe_sd`, `probe_z`: revealed readings,
  causal M0 predictions, predictive standard deviations, absolute normalized
  innovations. No future target values enter these columns.
- `scores`, `increments`: all16 values after decay/update and current nonnegative
  group-max increment. `best_group`, `trigger`, `active_group`, `ttl` expose the
  full score/rank/threshold/hold decision. `trigger` is the acquisition gate,
  distinct from the reported familywise change-detection alarm.
- `probe_hits`, `fine_hits`: currently nonzero synthetic perturbation at a valid
  acquired record. These are evaluator diagnostics and never policy inputs.
- `affected_probe_winners`: affected acquired records supplying a within-group
  maximum; a winner below the drift2 still adds zero.
- `*_difference`: max absolute difference from the same background's no-shock
  control. Innovations can change without a direct probe hit when informative
  aggregates change the causal predictive reference. `ranking_changed` compares
  the full16-group ranking, not just the top group.
- `requested`, `read`, `assimilated`: attempts, finite returned readings, finite
  newly inserted cache records. `budget_blocked` is false in all audited original
  paths: exact209 attempts were feasible. Missing reads count against budget.
- `action_reason`: threshold/hold targeting or default rotation. Probes precede
  this update's selection. Fine reads are then assimilated; they never call the
  original policy's score update. They cannot secretly affect the current action.
- `expired_cells`: finite records discarded as the window advances. Historical
  values are not freely restored. Original per-method factors rebuild every window.
- `score_error`: disagreement with the original stored maximum score, used with
  exact ordered-ID and active-group checks to validate reconstruction.

`diagnostic/episodes.csv` gives first divergence, exposure and action time and
counts. NaN first times mean no occurrence. The no-shock event window has zero
length, so its event max is0 by definition; its48 step records remain present.
All96 demand episodes and eight fault/eight background controls are retained.

`analysis/original_family_method.csv` reproduces original outcomes; detection and
correct group localization are within the frozen six-step window (steps onset
through onset+6), while false-localization counts span the event. Negative alarms
are outside the injected event, not verified absence of real-world anomalies.
`alarm_denominators.csv` uses per-update any-channel alarms in both periods and
shows startup exclusions explicitly. `sampling_reference.csv` is the elementary
single-set hypergeometric miss probability, using event-wide K as an illustrative
reference only. Deterministic rotation and native/time-varying support are assessed
by actual read intersections, not independent-draw approximations.

`comparison/episodes.csv` reports the fresh and original diagnostic phases
separately. Schedule change compares ordered acquired IDs against that policy's
same-background no-shock trace. It is a behavioral milestone, not an improvement.
`additional_affected_vs_control` counts newly selected affected records at event
times; repeated times are separate paid observations. M3b_fixed consumes M3b's
same sequential trace, rather than making extra independent requests.
Per-background paired differences are descriptive: four backgrounds are not
thousands of independent households, timesteps or disturbance seeds.
