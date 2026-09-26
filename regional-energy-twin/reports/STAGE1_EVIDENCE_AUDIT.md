# Stage 1 evidence audit

Audited September 23, 2026 UTC (September 22 EDT), against `6889a6a` on `main`.
The complete supplied plan is [docs/RESEARCH_PLAN.md](../docs/RESEARCH_PLAN.md);
there is no separate `DSpaCES_2026_Research_Plan.md` in this repository. No
applicable AGENTS.md was found. The initial working tree was clean and the
reported commit was HEAD. Original Stage 1 reports, configurations, manifests,
figures and numerical outputs remain unchanged. This document is the dated
correction and qualification record.

**The local stop recommendation survives the audit. This is not evidence that
weighted lineage or GPUs are generally unhelpful.** A secondary CSV analysis bug
was corrected without fitting a model or reopening source measurements. It does
not change the principal comparisons. Neither a population equivalence claim
nor the planned practical-advantage claim is supported.

## Reproducibility and evidence map

The audit commands below operate on saved artifacts. Use `python3`; this host's
`python` resolves to Python 2. The failed initial runner invocation is charged in
the independent [diagnostic ledger](../results/stage2/diagnostic_ledger.json).

```bash
python3 scripts/stage2_job.py --label evidence_audit --timeout 120 -- python3 scripts/audit_stage1_evidence.py
python3 scripts/stage2_job.py --label tests_audit --timeout 120 -- python3 -m pytest -q
python3 scripts/stage2_job.py --label artifact_audit --timeout 120 -- python3 scripts/verify_artifacts.py
python3 scripts/stage2_job.py --label main_guard --timeout 30 -- python3 scripts/run_main_study.py --preflight
```

The exact executed commands, failures, logs and durations are retained in that
ledger. `audit_stage1_evidence.py` writes only `results/stage2/`. It requires the
ignored October evaluator CSV, already preserved locally and in the archive.
Original-generation commands in the table are provenance references, **not
instructions or authorization to rerun the pilot**. Their expired allocation
must not be reset. All rows use the frozen [pilot configuration](../configs/pilot.yaml)
and [data configuration](../configs/data.yaml).

| Planned hypothesis | Observed result and numerical effect | Strongest relevant comparator | Uncertainty / supported conclusion | Output and reproduction reference |
|---|---|---|---|---|
| Retaining dependence remedies naive overconfidence | Raw 90% coverage: naive 73.344%, common-corrected 95.671%, exact 96.098%. Normalized widths: .8094, 1.5891, 1.5986 | Common-future-noise correction | The large change accompanies almost doubled widths and changed fusion weights. It is not an isolated overlap-information effect. Raw corrected IS90 actually worsens from 1.5170 to 1.6750 | [Recomputed summaries](../results/stage2/summary_metrics.csv), [baseline formulae](../src/evidence_fusion/fusion_baselines.py); audit command above; original `scripts/run_pilot.py --config configs/pilot.yaml` |
| Exact weighted lineage adds useful decision quality | Calibrated IS90 1.391485 versus 1.398226: **0.482% lower**; coverage difference **−0.0055 pp**; reservation loss .366823 versus .365746: **0.294% higher**; MAE 1.876% lower | Common-corrected fusion; individual 2 has still lower IS90, 1.380573 | Exact-minus-common IS90 three-week resampling percentiles [−.011850, +.004326] cross zero. These are descriptive sensitivity, not confidence bounds or equivalence. No 5% co-primary advantage established | [Contrasts](../results/stage2/contrasts.json), [new exact/common sensitivity](../results/stage2/exact_common_sensitivity.json), [per-overlap results](../results/stage2/by_overlap.csv); audit command |
| Sketch approximates exact quality at useful compression | k=2048 calibrated IS90 1.371899 versus exact 1.391485 (−1.407%); coverage 82.760% versus 83.467%; loss .369373 versus .366823 | Exact lineage for approximation; common-corrected and individual family for deployment | Close point averages do not establish noninferiority; all these calibrated 90% intervals undercover. The required useful metadata reduction fails | [Stage 1 paired sensitivity](../results/paired_sensitivity.json), [audit contrasts](../results/stage2/contrasts.json); original `scripts/analyze_pilot.py`, audit command |
| Training reuse is a material uncertainty component | Mean individual modeled fraction **4.2759%**, condition means 3.35–5.91%; training residual lag-1 ACF .844 | Shared-future allowance in the same plug-in decomposition | A property of the chosen OOF-scale convention, not an identified physical variance fraction. Correlated and biased residuals invalidate the iid real-data interpretation | [Diagnostics](../results/diagnostics.json), [residual audit](../results/residual_diagnostics.json); original `scripts/audit_residuals.py`; audit command |
| Sketch saves bytes over competent exact exchange | Exact setup 1,039–1,071 bytes, mean 1,059, all four providers; 48 reconstructions with zero measured error. Estimated cached k=2048 setup 1,245,973 bytes | Compressed supports plus public calendar design, under a richer support-disclosure contract | Actual exact codec and uncached sketch wire measured; cached-sketch transfer is an array-size estimate. At 256 queries and shared headers: 3,154.76 versus 8,017.70 estimated bytes/query | [Exact exchange measurements](../results/exact_exchange.json), [cost records](../results/pilot_costs.csv), [consistent horizons](../results/stage2/metadata_accounting.csv); original `scripts/audit_exact_exchange.py`, audit command |
| GPU improves complete pipeline cost | Warm CPU/GPU batch 1: 12.24/22.60 ms; batch 256: 2.7927/2.8098 s. Cold 256: 3.0186/2.9916 s | Four-thread FP64 CPU using the same fixed operators | Five repeats, sequential backend order, one building/middle-overlap cache. No interval on speedup. No useful advantage demonstrated for this Python codec workload; no universal crossover claim | [Warm records](../results/benchmarks.json), [cold records](../results/cold_benchmarks.json), [code](../src/evidence_fusion/replay_benchmarks.py); original `scripts/run_benchmarks.py`, `scripts/benchmark_cold.py`; saved-record audit only |
| Projection risk inequality and contract behave as specified | 108 condition evaluations / 36 distinct projections; zero within-event failures; 34 tests pass again | Analytic covariance, independent SciPy solve and restricted two-provider ESCI check | Numerical validation of a standard corollary under stated assumptions, not estimated 99% probability, a floating-point certificate, or a real-data coverage theorem | [Controlled output](../results/controlled.json), [proof audit](../docs/PROOF_AUDIT.md), [test log](../results/stage2/baseline_checks.log); original `scripts/run_controlled.py`; tests/artifact commands |

## Attribution of the apparent uncertainty improvement

Common-corrected fusion includes future noise once and minimizes only the
diagonal training component. Naive precision weighting instead includes future
noise in each marginal. Thus this comparison changes **both weights and variance**;
it is not a pure same-forecast variance ablation. Coverage alone favors the much
wider corrected intervals, while the proper raw interval score does not.

Exact lineage changes the off-diagonal training covariance and weights, holding
the common future convention fixed. Its raw IS90 improvement over correction
alone is only 0.0985%; raw normalized width rises 0.602%. After method-specific
chronological calibration, its IS90 improvement is 0.482%, normalized width falls
0.906%, and reservation loss gets slightly worse. This is a weak, local tradeoff,
not an equivalence result. No experiment isolated an operational federation effect.

Calibration alone raises naive coverage to 83.377%, while common-corrected reaches
83.472%. It reduces the latter's average normalized width from 1.5891 to .9762.
The large raw coverage separation largely disappears. k=2048 has a narrower
calibrated normalized width (.9609) than exact (.9673), so its lower calibrated
score cannot simply be described as wider final intervals. Inflation also changes
weights and subsequent estimated scale factors. The uninflated k=2048 score is
1.388041 with coverage 83.467%, close to exact. These comparisons do not identify
a causal benefit from the theoretical inflation term on real meter errors.

The strongest implemented equal-access family is metric-dependent. Individual 2
is the best of the four individuals by calibrated IS90, identified **after**
scoring; it is not a validated provider-selection rule. Common-corrected fusion
has the lowest calibrated reservation loss among the deployable primary methods.
CI and shrinkage are competent formula implementations but not the strongest
observed comparators. Shrinkage uses centered covariance of only 32–33 historical
errors, with no bias correction; its poor raw coverage cannot establish failure
of learned covariance combination generally. The pooled predictor is privileged
and uses the same simple calendar model, not a tuned modern forecasting model.

All Stage 1 minimum named numerical baselines exist, including all four
individuals, seasonal naive, equal weighting, naive/duplicate-aware independence,
common correction, scalar CI, exact conservative split-error reference, shrinkage,
uninflated sketches and pooled OLS. The exact scalar reference plus two-provider
test fulfills the allowed SCI/ESCI alternative; a general vector ESCI solver was
not evaluated. Missing planned extensions include regime-dependent shrinkage,
unrestricted regularized GLS, a stronger central model, fixed-union redistribution,
ID-only/shuffled-ID comparisons, multiple allocation seeds, and full scaling.
They must not appear as completed comparisons. Primary outcomes contain no
duplicate packets; protocol fixtures test final active-state invariance, not a
measured duplicate stream through every baseline's full pipeline.

## Temporal, causal and selection audit

| Role | What actually entered Stage 1 | Qualification |
|---|---|---|
| Eligibility / models / noise scales | January 1–September 30, 2016; training-only site round-robin eligibility; five deterministic day-block OOF folds | OOF fits use both earlier and later **training** blocks, appropriate for a fixed later forecast but not an online causal residual experiment. No validation labels fit provider coefficients |
| Historical covariance | Scheduled October 1–10; actual sampled dates October 8–10, 32–33 outcomes/building | Seven-day lag-168 embargo and 256-origin total cap leave only three dates; much weaker than a full October covariance history |
| Interval and reservation correction | October 11–20, 101–107 sampled outcomes | Same role for every method, after historical weights are fixed; serial dependence and linear empirical quantiles preclude an exact coverage guarantee |
| Pilot scoring | October 21–31; 1,856 unique building-target observations | 33,408 retained prediction rows are six methods × three overlap settings × targets, not independent evidence |
| Later calibration / test | November–December 2016 and all 2017 | No parsed values used. Copying/hashing the existing unopened ZIP for preservation did not evaluate or extract these outcomes |

The October subdivision is explicitly authorized by the Stage 1 prompt, an
amendment to the original November/December calibration and annual test protocol.
All of October is now development-exposed; even a new model's October 21–31
score would not be a pristine research holdout. The score window has 511, 1,181
and 164 unique targets in three calendar-week groups, with only one full week.
Sixteen sites contain one selected building each; selection is deterministic,
not a random sample, and sites share calendar/weather dependence. Resampling
all sites together avoids pretending they are independent, but three weeks do
not support narrow population intervals. One thousand resamples add no evidence.

Each provider retains 42 full days. Canonical IDs encode the same building,
timestamp, row, meter kind and revision across shared records. Allocation and
projection seeds are distinct fixed values. Supports have exactly the recorded
0/504/912 pairwise overlaps; unions shrink 4,032→2,520→1,296. Without the missing
fixed-union control, an overlap trend confounds reuse and total unique evidence.
The one repaired rank failure occurred before scoring, under a training-design
rule. Saved configuration hashes agree with both start events; this is an audit
trail, not an independent preregistration.

Provider features are calendar-only, deterministic at target time. They do not
depend on a recent consumption lag. Seasonal naive alone uses lag-168. All
methods are scored on the same valid-target/valid-lag mask; this unnecessarily
restricts the calendar model but preserves paired comparisons. No target is
imputed. Local-time DST exclusions are used; physical UTC accuracy remains
unverified. Shared message cutoff September 30 23:00 is a permitted upper bound,
not each support's actual latest observed event. Issue=start−1 minute and
arrival=start are constructed labels. The active-message API currently requires
identical cutoffs. These fields do not constitute an event-time experiment.

The consumer module has no raw-observation/influence argument. Reference and
evaluation code have broader access in the same process; this is an API boundary,
not an enforced security isolation. Code and artifacts support the seal claim;
unit tests alone do not prove the absence of all conceivable access paths.

## Metadata and timing audit

Exact exchange losslessly encodes support positions with a public regular-time
dictionary, feature recipe, retained columns and FP64-compatible scales. The
consumer reconstructs signed operators without training outcomes. Its compactness
is specific to public low-dimensional calendar regression and contiguous hourly
IDs. The richer support-disclosure contract is materially different from opaque
sketch exchange; the byte result is not proof of equal-disclosure dominance or
privacy. All eligible methods could exploit those supports under the richer
contract. No formal privacy benefit is established for sketches.

The 1,059-byte exact setup includes its serialized header and support framing.
The 68,686.62-byte uncached k=2048 query includes all four FP64 vectors and actual
dynamic headers (mean 3,150.62 bytes). Cached sketch setup is `operators.nbytes`
plus a JSON header estimate; there is no implemented cached-sketch wire codec,
decoder, digest binding or measured cached query pipeline. Exact cached dense
operators/cross-block alternatives in `pilot_costs.csv` are compressed payload
calculations, not complete independently validated codecs.

The corrected accounting charges the same measured dynamic header allowance and
one setup to both methods. At 256 queries the estimates are 3,154.76 exact versus
8,017.70 sketch bytes/query (2.54×); at an arithmetic 8,760-query horizon they are
3,150.74 versus 3,292.85 (only 1.045×). These horizons are not additional runs.
The roughly 1,177× setup ratio must not be presented as a complete amortized
communication ratio. Header reduction, model refresh frequency and feature
disclosure would change both contracts. FP32 sketch sizes were estimates; the
measured comparison and reconstruction used FP64.

Matched CPU/GPU paths use the same FP64 data and active-face solver objective.
Transfers, provider projection/query work, hashing, wire encoding/decoding,
validation, Gram construction, optimization, fallback and output encoding are
timed. Warm runs cache model operators; cold runs add cache reads, canonical-ID
creation, Gaussian-column generation and operator setup. Model fitting, dataset
parsing and process/framework startup are not in those query latency percentiles.
CUDA initialization was separately measured once (about .275 s), not included in
the cold percentiles. The supplemental explicit init call followed device
inspection and is not a full startup measurement. OS caches were not evicted.

Additional scope limit: the benchmark codec uses one repeated synthetic target
label with varying frozen numerical rows and reads original means/norms after
validating messages; it is a matched numerical/protocol replay, not a causally
faithful distributed forecast service. It includes no real network latency or
failure handling. Five repeats and fixed CPU-then-GPU order do not support a
precise population speedup estimate. The local .6% warm batch advantage for CPU
and .9% cold batch advantage for GPU are too small to promote. Python protocol
handling dominates this implementation. Any claim about optimized cached
interfaces requires a separately authorized new benchmark; none was launched.

## Dated corrections, September 23 UTC

1. **CSV boundary bug.** Default pandas float parsing in `analyze_pilot.py`
   moved saved binary64 values across interval boundaries. For
   `Lamb_assembly_Alden` seasonal naive, it lost 30 covered targets out of 117,
   repeated under three sharing settings. The incorrect block-derived site
   coverage is lower by 25.641 pp, and the equal-building aggregate by 1.603 pp.
   The original in-memory `pilot_metrics.csv` / headline coverage **86.000%**
   was correct. `float_precision='round_trip'` reproduces every available saved
   metric to 1.8e−15; no tolerance was added to the scientific coverage rule.
   [Corrected block sums](../results/stage2/corrected_pilot_block_sums.csv) and
   [differences](../results/stage2/corrected_block_differences.csv) supersede the
   affected seasonal rows only. Original blocks remain intact. Exact/common/
   sketch contrasts and their old resampling ranges are unaffected.
2. **Cost labels.** The old cost figure's blanket “measured wire cost” title
   overstates cached-sketch evidence. Its generator now labels measured wire
   bytes and cache estimates separately; the archived Stage 1 figure is retained
   unchanged. Use the explicit [accounting table](../results/stage2/metadata_accounting.csv).
3. **Gate wording.** Stage 1's “rough quality thresholds pass” means only that
   point estimates fell inside numerical thresholds. The joint gate also
   requires useful compression and paired uncertainty. That gate did not pass.
4. **Resource wording.** 49.1 minutes is the recorded Stage 1 research window,
   not total cloud billing. The pod stayed allocated afterward, including Stage
   2. No additional GPU work was executed. Allocation cost outside the research
   window is not measured and is not represented as free.

No substantive experiment rerun is needed to resolve these corrections. A
credible broader empirical claim would need a newly authorized protocol with
adequate chronological blocks and stronger comparisons; its cost is unmeasured.
The old 24-hour plan is neither that protocol nor permission to obtain it.
