# Exploratory calibrated scale-2 comparison

This amendment is frozen before the calibrated scale-2 experiment. The primary
v2 results and the earlier development support diagnostics have already been
inspected. This is an exploratory sensitivity analysis on the same episodes,
not an independent confirmation or a replacement of the primary study.

The user authorized up to eight cumulative experiment hours on the existing
Pod. The original four-hour stop and unsuccessful attempt remain in the ledger.
No infrastructure or billing changes are authorized. Allow at most 30 minutes
for this additional stage within the eight-hour total, including failed runs.

Use all five existing dataset configurations, training seed 17, the same four
test blocks, 72 fault episodes, eight controls, 13 decision times, and saved
64-draw bootstrap/diffusion trajectories. Use W=96 original observations and
d=24 at both scales. Context and forecast target remain 48 and 120 original
observations, respectively. No new model training or architecture selection.

Compare temporal scales 1 and 2, retaining the same spatial measurements on the
original W=96 grid. At scale 2, coarse-grain each 120-row target into 60
left-aligned, nonoverlapping two-row bins. Any missing member invalidates the
bin. Current and previous 48-bin windows have a 12-bin change lag: their physical
endpoints and information horizon equal the scale-1 comparison. All bins end
by the decision time. Applying the missingness mask precedes coarse-graining.
These alignments equal separate coarsening of each evaluated endpoint window.

Retain each configuration's development-selected q, tau, sample-entropy
tolerance, temporal top fraction, and localization budget. Tau, ACF lags, and
the sample-entropy Theiler exclusion are measured on the coarse grid; at scale
2 their physical delays double. Sample tolerance remains in training-derived
standardized units, with no within-window rescaling. Minimum template, tie,
flatline, match-count, and sensor-coverage rules are unchanged. Consequently,
some scale-2 estimates will abstain. Scale 4 remains support-only because a
96-row window leaves fewer than the declared 30 valid templates.

Fit scale-2 temporal score floors on exactly the four original development
issuances using max(1e-4, .05 IQR), before calibration or test. Retain the primary
scale-1 floors and matching W=96 spatial floors. Require ceil(.8*64)=52 valid
reference samples for spatial and temporal feature components at both scales.
This is the explicitly corrected support rule already evaluated separately;
do not silently alter the original 51-draw spatial primary results.

Report S, PE, SE, T, ST, SB, TB, B and BST for both references and scales.
Conventional temporal measurements undergo exactly the same coarsening,
history, aggregation and calibration as temporal entropy. Spatial S and SB
are deliberate unchanged-feature checks. Calibrate each scale/reference/family
on the original calibration units, including all-abstained units, at alpha .10.
Do not select among scales using test outcomes. Do not add an uncalibrated
maximum across scales. The main v2 common-support study remains separately
available; this small sensitivity reports operational metrics and support.

Use the existing one-to-one event matching and development-fixed family
localization rules. Save scores, calibration, availability, compact rankings,
event outcomes, support summaries and timing. Report recall, precision,
unconditional and detected-event localization, background exceedance, and
delay. Pair scale-2 minus scale-1 outcomes within the same episodes; resample
whole base blocks, retaining all injections, for descriptive 95% intervals.
No equivalence claim or new broad superiority claim follows from this audit.

Before accepting results, verify scale-1 scores, calibration ranks and
availability against the separately computed W=96/ceil52 sensitivity, allowing
only floating-point tolerance. Verify S/SB are unchanged across scales, and
test coarsened endpoint alignment and missing-bin behavior. Record any failure
as a correction or incomplete run, never as a completed comparison.
