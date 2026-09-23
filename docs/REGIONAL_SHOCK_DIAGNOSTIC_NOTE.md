# Predeclared current-recovery diagnostic

Added September 23 while the frozen replay was running, before its comparative
outcomes were analyzed. This completes the requested local-state recovery check;
it does not alter any method, detector, calibration or primary replay result.

Use the already preselected background 0, exact within-group cancellation,
magnitude 3 episode. At fixed update steps 12, 26 and 38, reconstruct the current
recorded demand using M0/M1/M2/M3/M4's saved acquisition history in the same
24-step window. No new observations are granted. Report all affected-record MAE,
the unread subset's MAE with its differing support disclosed, and numerical
identity for records already revealed. A current record shares measurement noise
with the current observation; a future-record noise convention would be wrong.

This diagnostic is not recovery of a noise-free physical state. The full-information
reference trivially knows the current record. Predictive usefulness is judged by
the separately frozen one-hour and six-hour forecasts. All matrix calculations
use the existing GPU and count toward the same allocation; no new study starts.
