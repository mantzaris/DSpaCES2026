# Regional twin synthesis and author-review manuscript

Prepared September 23-24, 2026. **Completed comparative case-study production**:
[manuscript PDF](../manuscript/regional_twin_study.pdf), ten IEEE conference pages
including references. Title: *When Does More Detail Help a Regional Energy Twin?*
Author: Alexander V. Mantzaris, School of Data, Mathematical and Statistical
Sciences, University of Central Florida, alexander.mantzaris@ucf.edu, as supplied.
This is ready for author review, not submission or an established novelty claim.

## Authoritative evidence and scope

The inspected branch was clean `main` at `99dc6b8beda6feec18ca5eb54ad6662dbc914d14`;
`18fe4af` is an ancestor and the latest GPU-tested acquisition source. No applicable
AGENTS.md was found. Stage 1-4 reports, linked protocols, mathematical/source
audits, source manifests, ledgers, per-episode outputs and decisive code were read.
The existing sketch, compatibility, RJD and refinement records remain intact.
The available adjacent BDCC plan was inspected for the scientific boundary.
No traffic result, graph enclosure or selective simulation claim enters this paper.

The manuscript uses the regional platform to separate representation (RQ1), new
observations (RQ2) and acquisition decisions (RQ3). The contribution is an empirical
case study and reproducible diagnostic methodology, supported by attributed
Gaussian and observability calculations. It does not describe the tested policy
as a successful new algorithm. Primary-source comparisons and exact access limits
are in [VENUE_AND_SOURCES](../manuscript/VENUE_AND_SOURCES.md).

The [claim-to-evidence map](REGIONAL_TWIN_CLAIM_EVIDENCE.md) covers 25 claims,
with source/config IDs, metric definitions, exact artifact paths and limitations.
The [pre-analysis gap register](../docs/REGIONAL_SYNTHESIS_GAPS.md) records the
limited checks chosen before new analysis. All new work uses saved outputs;
no new inference, fitting, calibration, threshold sweep or shock replay ran.

## Decisive findings preserved and clarified

| Question | Audited evidence | Supported conclusion |
|---|---|---|
| Regional scale | 167,932,474 archive rows; 4,194 eligible households; 52,109,356 fitting readings; common separator384, formal window101,040 coordinates | Substantial real-data pipeline and sampled regional prototype. Archive volume is not resident inference dimension. |
| RQ1 representation | Registered-query checks pass; retained61.12 to21.60MB; streamed fine21.60MB too; same-information outputs agree | Conditional preservation and an ordinary cache/reread tradeoff. No new capacity or predictive advantage. |
| RQ2 information | Original B:112episodes,96demand,8backgrounds/4weeks. Local1hMAE M3 .169595, random .171048, streamed fine .138586kWh | More fine evidence improves this local forecast average. No policy advantage established. All methods localize0/16exact cancellations. |
| RQ3 original policy | Fine exposure96/96, probe94/96, score93/96, event rank86/96, event top17/96, gate/action/ID schedule0/96 | An observation-sensitive method whose frozen score gate suppresses action changes; no overlay/index/budget defect found. |
| RQ3 correction | C:16fresh episodes/4reused backgrounds; M3b changes3/12demand schedules. M3b/M3/random localize2/12 each. MAE .266024/.262127/.266680 versus fine .205276 | Responsiveness alone does not establish useful localization or a forecast advantage. Same-information representations still agree. |
| Calibration | B M3 control30/384=7.81%; matching8step startup exclusion17/320=5.31% versus calibration2/88 | Real deployed-rate mismatch remains; not a per-household/family-wise denominator mistake. Adjusted intervals also under-cover. |

B and C are separate cohorts, not measurements of model deterioration. The B local
MAE uses80local episodes, while detection uses96demand episodes; C uses12for both.
The reconstructed112 episodes and four repeated diagnostic originals are not new
independent observations. Tests are implementation checks, not sample size.

## New saved-output investigation

1. **Gate margins.** For each of96x48paired updates, compute the infinity norm of
   the changed16-group score vector and the unmodified score maximum's distance
   to the strict acquisition threshold. All4,608satisfy the sufficient unchanged
   gate inequality. Actual ordered meter/time identity checks independently verify
   unchanged actions. This is an explanatory finite-trace diagnostic, not a new
   probabilistic bound or closed-loop threshold evaluation.
2. **Timing of the three corrective schedule changes.** b02 localized first changes
   at lag6 and adds no event-affected meter ID. b04 exact cancellation first changes
   at lag8, adding120affected-ID requests later in the event. b06 localized first
   changes at lag9, adding77later-event affected-ID requests. None adds an affected
   identity inside the scored lag0-6window. These counts use saved ordered IDs and
   evaluator-only affected-ID manifests, not unobserved residuals. They describe
   potential access, not a per-time guarantee of a finite nonzero perturbation.
3. **Remaining detector barrier.** In all12fresh M3b demand cases, the largest
   acquired fine innovation within that window is <=15.8465, below its calibrated
   effective fine threshold20.5864. Its two correct group localizations come via
   macro alarms. This explains a material part of the unchanged localization count.
   It does not show a different threshold or earlier policy would work.
4. **Paired heterogeneity.** Generated per-background error differences, detection,
   localization, miss-inclusive delay and control-alarm differences, together with
   family-by-method outputs. Every background is shown; no independent-hour
   significance test or equivalence claim is manufactured.

The original reports and numerical findings are unchanged. A dated wording
clarification is needed: the implemented detection window includes onset and six
subsequent updates (seven instants over three hours). Miss delay remains seven
half-hour steps. Earlier prose saying six updates including onset was imprecise.
Draft-only rank counting was corrected to event scope86/17rather than full-replay
89/22. These changes do not alter any benchmark or policy.

The mean forecast difference between M3b and M3 is not causally decomposed by this
analysis. Earlier targeted access, a better noise model and alternate alarm rules
remain untested. The paper asks a precise next question but authorizes none of them.

## Manuscript, reproducibility and checks

The full paper fits ten pages without changing IEEE typography, margins or spacing.
It includes four substantive vector PDF/SVG figures, two main tables and three short
explanatory propositions with proofs. The example is the preselected b00 exact
cancellation magnitude3episode, including the missed response. No new empirical
plot is fabricated. Figure labels, tables, captions and text distinguish observations
from synthetic intervention labels and separate the B/C cohorts.

`scripts/build_regional_study_results.py` derives the table and plots from committed
CSV/JSON artifacts, asserts decisive headline reproduction, hashes inputs and writes
new diagnostics under `results/synthesis/`. `scripts/check_regional_manuscript.py`
checks page count, citations/references, overfull boxes, font embedding, author
metadata and renders every page. The final visual inspection is recorded in
`results/synthesis/visual_review.json`. The clean build and exact dependency record
are in [the manuscript README](../manuscript/README.md).

The first LaTeX build exposed a generated-table input issue and was fixed without
scientific changes. A concurrent local ledger write initially lost that subsecond
failed-build record; one second was conservatively restored and the wrapper now
serializes CPU jobs. Both retries are charged. Figure review shortened overflowing
diagram labels, clarified a late shared background trigger and improved float
placement. No original experiment code was changed, so no GPU retest was needed.

## Resources, seals and disposition

No additional GPU experimental allocation was opened: **0new GPU minutes**. The
closed experimental total remains168.7662885minutes of180, leaving
**11.2337115minutes**. Local saved-output analysis, plotting, compilation and page
rendering are charged through `results/synthesis/resource_ledger.json`; final exact
CPU totals and a conservative ancillary allowance are in its closed handoff.
Reading and writing time are not reported as executed CPU-job time. The pod remains
allocated and incurs billing while idle; that closed-stage billing is separate
from experimental-use accounting, not erased or described as free compute.

No new archive was downloaded, no raw meter values were opened for this synthesis,
and no outcomes were unsealed. London April-December2013and all BDG2 seals remain
intact. `configs/main_study.yaml` remains unauthorized and its runner fail-closed.
No manuscript submission, registration, fee, organizer contact, deployment or pod
lifecycle operation occurred. Completed artifacts are local and hash-inventoried;
no new artifact exists only on the pod. Existing durable data manifests remain valid.

The review checklist focuses on contribution strength, development-only evidence,
decision definitions, the uncertainty/information contract and venue/release details.
The recommendation is to review this narrowly framed case study on its evidence;
do not claim a new successful adaptive algorithm or launch another stage automatically.

### Closed local-work accounting

Recorded local analysis/build/render job charges total 63.420 seconds (1.0570 minutes),
including the conservatively restored one-second failed build. Measured retained
job records account for 62.420 seconds. A
conservative 120-second ancillary allowance covers unwrapped helpers, source
retrieval, read-only checks, packaging and normal git handoff. Total additional
charged supporting work is 3.0570 minutes; cumulative CPU charge 94.7260 of 360,
leaving 265.2740 minutes. GPU experimental charge remains zero new minutes and
11.2337115 minutes unused. Existing data plus cache occupied about 2.352 GB
before the small author-review archive; no new meter data were ingested.

The final log has ordinary underfull boxes and a nonfatal multiple-PDF-page-group
warning for the two Matplotlib figures on page 9. Their composed appearance was
inspected; no clipping or color defect was seen. IEEE PDF eXpress validation was
not performed and remains a camera-ready author action.
