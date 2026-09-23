# Stage 2 decision

September 23, 2026 UTC. **C — Stop/defer this DSpaCES project.** Retire the
present sketch approach, preserve its evidence, and do not start the event-time
alternative or the original main study. This is a research allocation decision
under the plan's gates, not a universal negative result about provenance.

## Basis

The [evidence audit](STAGE1_EVIDENCE_AUDIT.md) independently reproduced the saved
summaries and rechecked all 34 tests. The Stage 1 description is substantially
accurate: 16 buildings at 16 sites, four providers, fixed calendar OLS, three
synthetic sharing levels, October-only scoring, and a recorded 49.1-minute Stage
1 research window on an RTX PRO 4500 Blackwell. The test year remains sealed.

| Decision-relevant evidence | Interpretation |
|---|---|
| Exact versus common-corrected calibrated IS90: 1.391485 versus 1.398226, **0.482% lower**; reservation loss **0.294% higher** | No practical advantage at the prespecified 5% scale is established. Exact is also worse in IS90 than the best observed individual baseline (1.380573), though selecting that individual afterward is not a deployable selection rule |
| Exact-minus-common IS90 three-week descriptive resampling range, 2.5/97.5 percentiles: **[−.011850, +.004326]** | Direction is sensitive to the few observed time blocks. This neither proves equality nor supplies credible population confidence bounds |
| Raw naive/common-corrected coverage: **73.344% / 95.671%**; normalized widths **.8094 / 1.5891** | Common future uncertainty and much wider intervals explain the large apparent confidence correction; raw proper interval score worsens. Calibrated common/exact coverage is only about 83.47% at nominal 90% |
| Training-influence fraction **4.2759%** under the declared empirical decomposition | The investigated source of dependence is a small component under this model. The fraction is not an identified physical variance decomposition |
| Exact support setup **1,059 bytes**; cached k=2048 setup estimate **1.246 MB** | The tested public-calendar design makes exact exchange economical. With matched headers at 256 targets, estimated exact/sketch cost is **3,154.76 / 8,017.70 bytes per query**. Richer support disclosure and cached-wire estimation limit this comparison |
| Warm CPU/GPU batch-256 time **2.7927 / 2.8098 s**; cold **3.0186 / 2.9916 s** | No useful complete-pipeline advantage demonstrated for this codec and cache. Five repeats at one workload do not establish a general GPU limit |

The CSV parsing correction affects secondary seasonal-naive block coverage for
one building. It leaves the original headline table and all decisive
exact/common/sketch contrasts unchanged. Round-trip parsing restores the original
metrics within 1.8e−15. A cost-label correction distinguishes measured wire bytes
from cached-sketch estimates. Original Stage 1 artifacts are retained. There is
**no unresolved concrete defect requiring a substantive rerun before this
decision**; the evidence limitations themselves prevent stronger claims.

## Why A is rejected

The narrow fallback question would be: *when do compact dependence descriptions
give data-space consumers better reservation decisions than ordinary common-noise
correction and empirical covariance fusion, at their complete information cost?*
This pilot usefully teaches that an exchange contract can cost more than exact
public-design reconstruction, and that modeled training reuse can be minor
relative to the shared target error. Consumers should price the exact sufficient
information and retain common uncertainty before investing in sketches.

Those are useful engineering lessons, but this particular result does not clear
the plan's paper gate. It is a small, chosen calendar model under simulated
sharing, not a demonstrated operational federation. The proof is a synthesis of
existing robust estimation and projection bounds. Known conservative covariance
compression already connects bounded compression error with inflation; see the
[original source-by-source audit](../docs/NOVELTY_AUDIT.md). There is no robust,
practically meaningful residual overconfidence regime that the strong relevant
baseline fails to handle. Three scoring week groups, one allocation seed, weak
historical covariance estimation and no fixed-union control also prevent a
convincing broader empirical claim. Reproducibility and negative timing alone
do not justify a full or short paper. No manuscript is proposed.

## Why B is rejected

The [Stage 2 novelty audit](../docs/STAGE2_NOVELTY_AUDIT.md) compares eight close
works, including original asynchronous track fusion, AoII, probabilistic temporal
reconciliation and energy forecast updating. Current work already treats joint
age-vector losses: Shisher et al.'s correlated-source study is published in
TON 34 (2026), and Zhang et al.'s April 2026 revision extends multimodal scheduling.
The latter remains a submitted journal extension according to its current record.
The audit does not claim that these works solve every possible forecast-only
contract, but it removes the suggested broad novelty of freshness-aware fusion.

The existing providers use no recent meter input, so merely changing cutoff or
delivery labels cannot demonstrate the proposed staleness mechanism for available
same-target forecasts. A new lagged/state-space model and causal delay replay
would constitute a new experiment. No evidence shows a benefit beyond a
competent joint age-aware predictor, and no precise new guarantee fills the
missing-information gap. BDG2 has no observed provider-arrival process. All
October outcomes are already development-exposed; November/December cannot be
borrowed for exploratory model selection. B does not follow just because A fails.

The inaccessible original Bar-Shalom full text and other recorded source gaps
limit a positive originality claim. They do not imply that novelty is absent
everywhere, nor provide grounds to fund a pivot. A future reconsideration would
require an independently motivated, precisely differentiated question and a
separately authorized protocol; this stage supplies neither a fabricated theorem
nor a speculative execution prompt.

## Disposition and accounting

Follow the [archival disposition](STAGE3_PROPOSAL.md). The original main-study
configuration and launcher remain disabled; the 24-hour allocation is not renewed.
No Stage 3 pilot, GPU benchmark, training sweep, November/December analysis or
2017 evaluation ran. No experiment is left running. The user's pod remains
allocated; no stop, terminate, deletion or additional rental was performed.

Stage 2 diagnostics and retries are charged to a separate persistent 1,800-second
cap in [diagnostic_ledger.json](../results/stage2/diagnostic_ledger.json). That ledger
conservatively includes the 97.42-second artifact transfer as well as read-only
pod inventory/hash checks, tests and recomputations. Literature retrieval,
reading and writing are outside diagnostic job time. The final stage accounting
and current allocation observation are in
[resource_ledger.json](../results/stage2/resource_ledger.json).

Changes comprise this decision, the evidence and novelty audits, archival
disposition, README status, audit scripts and their saved numerical outputs,
access/publication/preservation manifests, the focused CSV parsing fix, and the
future cost-figure label correction. No provider model, cohort, sharing condition,
scientific seed or calibration partition changed. All changes use the existing
`main` and a normal push to `origin/main`; `6889a6a` remains in history.
