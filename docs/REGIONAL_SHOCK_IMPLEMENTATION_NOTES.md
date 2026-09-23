# Shock replay bookkeeping and interpretation notes

September 23, 2026. These notes preserve the frozen protocol/configuration and
original numeric outputs. None changes a detector, observation trace, model or
comparative prediction.

- The frozen field `physical_demand_episodes=104` includes the eight unmodified
  backgrounds. The actual nonzero demand-shock count is 96; the report separates
  these from eight background and eight fault controls. Background time blocks
  are not assumed statistically independent merely because a legacy manifest
  calls them `independent_backgrounds`.

- Episode metadata gives the authoritative onset. The generator uses array index
  `24 + randint(6, 11)` while update zero is array index 23. Thus onset update
  indices are **7-11**, not 6-10. The protocol's prose described the offset loosely;
  scoring has always used the correct saved onset.
- Raw alarm column `observed_affected` counts attempted IDs belonging to the
  episode's affected set. It does not exclude missing values or times when a
  feasible overlay is zero. Analysis creates `informative_valid_reads` from
  the immutable access trace, native mask and actual current perturbation. The
  original column is retained and not used to claim a first informative reading.
- Pandas initially inferred a single-alarm ID column as numeric, causing NumPy
  integer-string parsing warnings. Explicit string dtypes remove the ambiguity.
  The original analysis directory/log are preserved; episode detection and
  forecast summary files are byte-identical after the parsing correction.
- Per-method `complete_seconds` includes channel/policy work, GPU inference,
  output transfer and the current provider-summary scan. It excludes common
  window construction, scoring and file serialization. The episode and whole-job
  clocks cover that additional work; do not call the former field total pipeline
  latency. CUDA event spans include dispatch gaps, not just active kernels.
- The raw cost log assigns 128 framing bytes to M4's single fine request;
  its channel trace correctly records one 64-byte header. Analysis derives
  fine-message bytes from the trace for every method, mapping M3_fixed to the
  same M3 trace. `audited_costs.csv.gz` preserves the raw value alongside the
  correction. These are simulated serialized-payload counts, not packet captures.
- `state_bytes` counts separator state and retained household conditional blocks
  while answering queries. It excludes the shared model, temporary query packs
  and host observation cache. Peak process GPU/RSS and those shared objects must
  also be reported. Per-method peak columns are cumulative peaks from the joint
  comparison process, not isolated method memory measurements.
- The boundary diagnostic's `active_group` field reflects the event policy.
  It is not the uncertainty policy's selected group; that policy's actual
  selection is recoverable from its acquired IDs. It has no separately fitted
  alarm/interval calibration and is not part of the primary detection table.
- All methods rebuild 16 mask-dependent leaf messages and one common separator
  at every window advance. This implementation does not establish cross-window
  factor reuse or a new incremental inference algorithm. Within-step retention
  and subsequent eviction change storage, not the same-information posterior.
- Main error/coverage metrics already use observed target support. The original
  illustrative positive/negative-side forecast averages include all nominated
  households, including two missing positive-side records in the preselected
  episode. A saved-trace GPU reconstruction produces `figure_common_support.csv`
  on matching target support and verifies unchanged regional predictions. The
  original figure file and the reconstruction discrepancy are retained.
- The provider constructs group sums by scanning household readings. Limited
  consumer access therefore measures a simulated fine-message/access saving,
  not a reduction in the provider's sensing or source ingestion. The evaluator's
  background files are not hidden free observations for a policy.

The current-record diagnostic is separately predeclared in
[REGIONAL_SHOCK_DIAGNOSTIC_NOTE.md](REGIONAL_SHOCK_DIAGNOSTIC_NOTE.md). Its zero-lead
noise convention does not change any frozen one-hour/six-hour calculation.
