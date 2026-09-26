# One corrective hypothesis, recorded before policy edits

2026-09-23, 23:26 UTC. Diagnosis uses the passed two-episode diagnostic smoke and
first two completed background reconstructions. The all-episode audit is still
running. Original policy and original results are unchanged.

The original executable path is observation-sensitive and its large-innovation
behavioral test changes actual available reads. In b00 cancellation magnitude3,
nine updates encounter affected probes; observed z reaches3.4411 and group scores
differ by1.5698, but the maximum score remains below13.4334. In b00 localized3,
the best group changes on five updates, four toward the affected group, but no
trigger changes. In b01 approximate-cancellation3, it changes on five updates
all toward the affected group, again without a trigger change. Thus a detector
threshold is suppressing potentially useful *allocation rankings*. This is a
policy choice/statistical limitation, not an overlay or scheduler implementation
bug. Full diagnostic results may qualify its prevalence.

**One intentional change, M3b:** separate alarm declaration from allocation of
an already-spent reading budget. After the SAME41 acquired probes update the
SAME non-cancelling score, choose argmax whenever its score is positive; otherwise
rotate. Preserve42 exploratory plus126 directed extra attempts (209 total),
fixed probe stream, model, causal reference and original shock amplitudes. No
extra-reading feedback, score redesign, changed alarm target, architecture or
multiple-variant search. Unlike M3's threshold/hold allocation, M3b selects the
current best positive score each update. Alarms remain independently calibrated
at the same per-update any-channel target on the original earlier Jan3-4 segment.

Prediction: some subthreshold changes to the best group will change meter IDs;
others will not. This cannot overcome missing informative probes or background
innovations that dominate the ranking. Forecast/localization benefit is uncertain;
wrongly directed reads may lose to random exploration. Keeping identical evidence
should still make fixed and adaptive representations agree.

Freeze before comparisons: 4 backgrounds [0,2,4,6], families localized,
cancel_exact, delayed, none, magnitude3 for nonzero families, seed1040000+1000*b+
10*f (family order above),48 updates. These16 episodes use fresh seeds but reused
development backgrounds. Diagnostic paired originals: b00 localized3,
cancel_exact3, delayed3, none0. Original settings/results can be reused only for
exact matched source, model, calibration, seed and target. Compare M0,M2,M3,M3b,
M3b_fixed,M4 on fresh episodes, and M0,M3b,M3b_fixed on originals with original
comparators reused. No outcome-driven episode dropping. Detection limit6 updates,
miss delay7, familywise per-update alarms, affected-household1h MAE and relevant
regional1h MAE;6h secondary. 5% budget unchanged. Calibration only M3b, retaining
all original methods' frozen thresholds for an explicit legacy comparison.

A small calibration-segment smoke and behavioral tests precede comparison.
Source/config/calibration hashes are frozen. Complete execution must reserve
at least5 minutes within the30-minute cap for validation/copies/handoff.
