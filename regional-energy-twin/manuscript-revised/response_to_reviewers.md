# Response to reviewers

We thank the reviewers for their constructive comments and recommendations for
acceptance. We have made a focused revision, retaining the title, abstract,
mathematical results, methods and original numerical findings. The revision adds
one retrospective alarm-threshold comparison from preserved scores. It does not
introduce a policy, rerun inference, open the sealed outcomes or claim operational
validation. Locations below refer to section titles and LaTeX labels, which also
identify the changes in the marked-up manuscript.

## Reviewer 1

**Operational framing and the absence of an adaptive advantage.** We agree that
the evidence supports a diagnostic contribution rather than a validated operational
system. The Introduction, Discussion and Conclusion now state that distinction
directly. The Introduction adds an illustrative consumer: an energy analytics team
receiving group summaries and requesting household readings to prioritize an
investigation. A missed localization leaves the team unable to identify the sampled
group to examine. This is explicitly an illustrative use, without claims about
deployment, physical faults or financial losses.

The Results retain M3's small difference from random acquisition and M3b's lack
of demonstrated advantage. The timing diagnosis remains explicit: new requests
for affected identities arrive after the scoring deadline, and an affected identity
is not automatically an informative finite reading or successful localization.
The new findings/design-guidance table (`tab:guidance`) distinguishes supported
checks from untested remedies such as earlier targeting and better calibration.

## Reviewer 2

**1. Motivation and consumer decision.** The Introduction now gives the concrete
analytics-team use case described above. It identifies the provider's summaries,
the consumer's requests, the investigative decision and the limited consequence
of missed localization. No geographical, feeder or operational capability is
inferred from the simulated interface.

**2. Direct, useful guidance.** The Introduction now states the checks earlier:
hold evidence fixed, use streamed inference as the capacity baseline, inspect
gate margins, obtain information before the deadline, compare detection at
comparable false-alarm rates and assess predictive calibration separately from
numerical consistency. The compact `tab:guidance`, discussed in Section VII, connects each
check to its evidence or limitation and replaces repetitive guidance prose.

**3a. Synthetic groups.** Section III, "One fixed probabilistic model," specifies
sorted meter index modulo 16. These are synthetic groups, not districts or feeders.
The methods and limitations explain that spatially meaningful grouping could
change shared dependence, cancellation within summaries and localization
difficulty. We do not claim an unmeasured direction or magnitude of improvement.

**3b. Window restarts.** Section IV, "Preserving queries as detail changes," now
states that each advancing window restarts from the training prior and rebuilds
all 16 group factors without a boundary message. This discards earlier observation
information and can affect forecasts and uncertainty. That effect was not measured;
the Discussion retains it as a limitation.

**3c. Gate parameter provenance.** Section IV, "Tracing information into
acquisition decisions," and Section V's calibration paragraph now explain the
settings. The threshold 13.4333767 is the empirical 98th percentile of M1 maximum
group scores on 88 unmodified January 3-4, 2013 calibration updates after removing
eight startup updates from 96. Decay 0.8 and offset 2 are fixed heuristics in the
configuration and executable policy, not tuned parameters. The diagnosis is
conditional on those settings. We chose the requested provenance clarification
rather than adding an acquisition-parameter search. `revision_analysis.md`
documents the exact quantile procedure and the implementation's hard-coded values.

**4a. Detection at different false-alarm rates.** The RQ2 Results now discuss the
original table explicitly: M0 detects 37/96 and localizes 20/96, compared with
M3's 29/96 and 15/96. M4 detects more than M0, 42/96, but localizes fewer, 15/96.
Their alarmed control updates are 36, 30 and 41 out of 384; M2 has 25.

We added a control-matched detection table (`tab:alarm_rates`) and a reproducible
saved-score sweep. Acquisition and recorded evidence remain fixed; only the final
alarm threshold changes. At 7/384 control alarms (1.823%, near the nominal 2%),
M0, M2, M3 and M4 each detect 8/96 episodes; M1 detects 6/96. At 19/384 control
alarms, M2 detects 27/96 versus M3's 19/96. These descriptive comparisons do not
establish an adaptive advantage. Thresholds for the displayed rates are chosen
using controls alone, with strict comparisons, no interpolation and 1/384 empirical
resolution. Detection probabilities concern episodes; false-alarm rates concern
updates. Shared backgrounds preclude treating these as independent binomial trials.

This audit also found a description error: the original panel B code uses lags
0-5, whereas its prose said 0-6 inclusive. Panel C actually uses lags 0-6. The
original table counts are preserved and their panel-specific windows corrected in
Section V and the table caption. The new comparison consistently uses the requested
lags 0-6 inclusive. Extending the original frozen thresholds to that window gives
M0/M3/M4 detection counts 43/31/42; those are explicitly distinguished from the
published counts. The technical note and sweep figure retain both sets of points.

We did not sweep localization. Saved maxima and original alarmed-group lists do
not reconstruct all threshold-specific group decisions. Reusing original
localization flags at different thresholds would be invalid. The original
localization findings remain unchanged, including zero of 16 exact-cancellation
events for every method. `analysis/alarm_methodology.md` and its CSVs provide the
full window and threshold audit.

**4b. Payload ambiguity.** Section VI's RQ2 resource paragraph now identifies
22.52 MB and 364.95 MB as total estimated consumer payloads for M3 and M4,
respectively, each including 3,854,592 summary bytes. Fine payloads are
18,665,472 and 361,095,168 bytes. The approximately 20.07-fold request ratio differs
from the 16.21-fold total-payload ratio because of per-call overhead and shared
summaries. The text explains attempted-record accounting and distinguishes
simulated communication from measured network traffic, provider scans and
host-to-device transfers. Exact arithmetic is retained in `revision_analysis.md`.

**4c. Limited corrective panel and chronological validation.** Section V and the
Discussion explicitly retain that panel C has 12 demand episodes and four reused
backgrounds. Fresh seeds are not independent chronological validation. We agree
that April-December 2013 is a natural future evaluation period; it remains sealed.
Independent chronological validation is deferred, not claimed as completed by
this minimal revision.

**4d. Calibration.** The Discussion keeps the shortfall visible: panel A's selected
nominal 90% regional intervals cover 59.4%; M3's one-hour regional intervals on
panel B controls cover 72.14%, or 84.12% after adjustment. Alarm calibration is
separate, uses only 88 post-startup updates and does not achieve its nominal 2%
rate in replay. Prediction-interval adjustment uses all 96 calibration forecast
origins. Neither exact numerical calculations nor the retrospective threshold
sweep establishes reliable calibration.

**5. Generalization and scalability.** The Discussion now collects synthetic
grouping and prior restarts alongside the existing retrospective, simulated-provider
and disturbance limitations. It explicitly identifies the 384-dimensional
separator as modest. The large archive demonstrates ingestion scale, not inference
capacity at a comparable state dimension.

**6a. Terminology and density.** We added short definitions at first use for
registered posterior queries, the common separator, formal coordinates, acquired
fine innovations and informative exposure. The provider scan is described as work
counted separately from consumer access. The existing early method table in
Section III (`tab:methods`) is retained, rather than duplicated. Nonessential
ingestion and cache bookkeeping moves to `revision_analysis.md`; the main paper
keeps the numbers needed to interpret its comparisons.

**6b. Figure 2(d).** A direct annotation, "After event; both runs," marks the
later score peak. It occurs 13.5 hours after onset, after the 12-hour disturbance,
with the same score in the shocked and paired background runs. All original
curves, axes and disturbance support are retained. The before/after comparison is
provided in `figure_changes.pdf`.

**6c. Author list.** The author has now explicitly confirmed the second author
as James H. Korris, following Alexander V. Mantzaris, with Creative Technologies
Inc., Hollywood, CA, USA, and `james.korris@cretecinc.com`. The revised author
block and PDF metadata use this confirmed information. No name was inferred from
repository contributors. The submission system has not been accessed or changed;
the authors should verify its metadata against this confirmed list at upload.

## Reviewer 3

**1. Regional/data-space scope.** The Introduction's illustrative consumer and
Section III's explicit observation interface clarify the data-sharing setting.
The methods and Discussion state that groups are synthetic, the provider is
simulated and no physical grid topology is available. The twin represents the
sampled household population, not all London buildings or a live deployment.

**2. Unequal realized false-alarm rates.** The new `tab:alarm_rates` and saved-score
sweep compare detection at common attained control-alarm counts while retaining
the original operating points. The analysis and verified scoring-window
correction are described under Reviewer 2, item 4a. This is descriptive development
analysis, not independent calibration; no unsupported localization sweep is added.

**3. Model calibration.** We agree that numerical consistency does not establish
predictive calibration. The Discussion emphasizes undercoverage and elevated
alarm rates, distinguishes their calibration procedures and defers independent
chronological validation without opening the sealed outcomes.

**4. Summarizing findings and guidance.** The new `tab:guidance` gives findings,
design implications and their evidence or limits in one compact table. Its
caption distinguishes demonstrated checks from unvalidated remedies. Definitions
and shorter supporting passages improve readability without changing the
negative findings or mathematical claims.
