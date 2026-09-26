# Figure provenance

All PDF/SVG figures use saved measurements. No synthetic-looking empirical chart
was generated without data. `scripts/analyze_acquisition.py` reads original
Stage 3 metrics and new FP64 diagnostic traces to produce `observation_action`
and `observed_not_acted`. The latter is the preselected b00 cancellation magnitude3
case, retained despite failure. `scripts/analyze_acquisition_comparison.py` reads
the frozen paired run and produces `corrective_tradeoff`; it keeps four original
diagnostic episodes separate from sixteen fresh-seed episodes. Four backgrounds
are the replication groups. See results/acquisition/frozen.json for source,
configuration, calibration and training-model hashes. SVG preserves text; PDF
embeds TrueType fonts. PDF rendering was visually inspected at handoff.
