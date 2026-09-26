"""Render reviewable reports from retained measurements; no experiment execution."""
import json
from pathlib import Path
import pandas as pd


def main():
    audit=json.loads(Path('manifests/data_audit.json').read_text())
    source=json.loads(Path('manifests/source_archive.json').read_text())
    decision=json.loads(Path('results/decision.json').read_text())
    ledger=json.loads(Path('results/resource_ledger.json').read_text())
    bench=json.loads(Path('results/benchmarks.json').read_text())
    cold_bench=json.loads(Path('results/cold_benchmarks.json').read_text())
    device_seconds=bench['total_device_event_seconds']+cold_bench['device_event_seconds']
    runtime=json.loads(Path('results/final_runtime.json').read_text()) if Path('results/final_runtime.json').exists() else {}
    metrics=pd.read_csv('results/summary_metrics.csv')
    costs=pd.read_csv('results/pilot_costs.csv')
    exact=pd.read_json('results/exact_exchange.json')
    residual=pd.read_json('results/residual_diagnostics.json')
    diag=pd.read_json('results/diagnostics.json')
    controlled=json.loads(Path('results/controlled.json').read_text())
    epochs=json.loads(Path('manifests/sketch_epochs.json').read_text())
    tests=Path('results/tests.txt').read_text().strip().splitlines()[-1]
    primary=costs[costs.k==2048]
    method_names={'seasonal_naive':'Seasonal naive', 'individual_2':'Individual 2 (one of four)',
        'equal_weight':'Equal weights','naive_independence':'Naive independence',
        'common_corrected':'Common-noise corrected','ci':'Optimized scalar CI',
        'shrinkage':'Historical shrinkage','exact_lineage':'Exact lineage',
        'sketch_512':'Sketch k=512','sketch_2048':'Sketch k=2048',
        'uninflated_2048':'Uninflated k=2048','pooled_privileged':'Pooled raw-data reference'}
    table=['| Method | Raw 90% coverage | Cal. 90% coverage | Cal. 95% coverage | Cal. normalized IS90 | Cal. normalized reservation loss |',
           '|---|---:|---:|---:|---:|---:|']
    for method,name in method_names.items():
        raw=metrics[(metrics.method==method)&(~metrics.calibrated)].iloc[0]
        cal=metrics[(metrics.method==method)&metrics.calibrated].iloc[0]
        table.append(f'| {name} | {raw.coverage90:.2%} | {cal.coverage90:.2%} | {cal.coverage95:.2%} | {cal.normalized_is90:.4f} | {cal.normalized_reservation_loss:.4f} |')
    timing=['| Backend / batch | Warm p50 | Warm p95 | Queries/s |', '|---|---:|---:|---:|']
    for row in bench['summary']:
        timing.append(f"| {row['backend'].upper()} / {row['batch']} | {1000*row['p50_seconds']:.2f} ms | {1000*row['p95_seconds']:.2f} ms | {row['queries_per_second']:.2f} |")
    cold=['| Backend / batch | Cold p50, 5 repeats | Cold p95, 5 repeats |', '|---|---:|---:|']
    for row in cold_bench['summary']:
        cold.append(f"| {row['backend'].upper()} / {row['batch']} | {row['p50_seconds']:.4f} s | {row['p95_seconds']:.4f} s |")
    projection=['| Buildings | Primary warm replay | With 25% margin + 8 h other work | Fits 24 h? |', '|---|---:|---:|---|']
    for row in decision['main_cost_projection']:
        projection.append(f"| {row['buildings']} | {row['warm_replay_hours']:.2f} h | {row['with_25pct_margin_and_8h_other_packages']:.2f} h | {'yes' if row['under_total_24h'] else 'no'} |")
    complete_event=next(e for e in ledger['events'] if e['event']=='pilot_complete')
    allocated=ledger['allocated_wall_seconds']
    feasibility=f'''# Stage 1 feasibility report

The bounded pilot completed on September 22–23, 2026 UTC. **Data access and the
numerical implementation are feasible; expanding the proposed sketch study is
not supported by its current scientific or cost gates.** See [STAGE1_REPORT.md](STAGE1_REPORT.md).

## Machine and environment

* Actual device: **{bench['hardware']['gpu']}**, 32,623 MiB ({bench['hardware']['gpu_total_bytes']:,} bytes).
  The older RTX 6000 Ada / 48 GB sections of the plan do not describe this machine.
* Driver {bench['hardware']['gpu_driver']}; Python {bench['hardware']['python']};
  PyTorch {bench['hardware']['torch']}, CUDA runtime {bench['hardware']['cuda']}.
* Host CPU: AMD EPYC 7443P, 24 physical / 48 logical cores. Container CPU quota
  `{bench['hardware']['cpu_quota']}` permits about 10.2 CPU cores; measurements used
  four BLAS/PyTorch threads. Container memory quota is {int(bench['hardware']['memory_quota'])/1e9:.1f} GB.
* Device ceiling: 24 GiB; actual benchmark peak {bench['peak_vram_allocated_bytes']/2**20:.1f} MiB.
  Measured benchmark process peak RSS: {bench['peak_process_rss_bytes']/1e9:.3f} GB.
  No compilation, neural model download or GPU training was performed. GPU work
  was fixed-operator projection, Gram construction and batched convex fusion.

[`environment.lock.txt`](../environment.lock.txt) records the full environment;
[`requirements.lock.txt`](../requirements.lock.txt) isolates pinned analysis
dependencies. The host Python 3.8 environment was also used for code tests, but
the reported experiment and final figures use the pod environment.

## Archive and terms

The originating [BDG2 v1.0 archive](https://zenodo.org/records/3887306) downloaded
as **{source['bytes']:,} bytes**. Published MD5 matched `{source['md5']}`.
Observed SHA-256: `{source['sha256']}`. Archive paths, sizes, CRC labels and
extracted-file hashes are in [`source_archive.json`](../manifests/source_archive.json).
The raw electricity member is a real CSV, not a Git LFS pointer. Its cleaned
counterpart is named `electricity_cleaned.csv`.

The v1.0 archive's root [LICENSE](../manifests/BDG2_LICENSE.txt) is MIT, whereas
the [current repository license text](../manifests/BDG2_CURRENT_LICENSE.txt)
starts “Attribution-ShareAlike 4.0 Unported”. Both exact texts and retrieval hashes
are retained. This version discrepancy is unresolved; the report does not replace
either text with the Scientific Data article license or assert a legal resolution.
No raw archive, meter table or per-target observed-reading file is committed.

The source documentation specifies kWh for these energy-meter files and local
clock labels. The raw release is already harmonized. The cleaned mask is an
explicit secondary sensitivity; it does not replace the primary raw labels.
References: [meter schema](https://github.com/buds-lab/building-data-genome-project-2/wiki/Meters-data-features),
[metadata schema](https://github.com/buds-lab/building-data-genome-project-2/wiki/Metadata-features).

## Observed data and cohort

| Item | Measured count / scope |
|---|---|
| Electricity columns | {audit['electricity_meters']:,} |
| Parsed rows | {audit['pretest_rows']:,}, January 1–October 31, 2016 |
| Training hours | {audit['training_hours']:,} |
| Training finite readings across all electricity columns | {audit['training_valid_readings']:,} / {audit['training_meter_hour_positions']:,} positions |
| Eligible buildings / sites | {audit['eligible_buildings']:,} / {audit['eligible_sites']} |
| Frozen selected buildings / sites | 16 / 16 |
| Unique selected origins across October roles | 4,096 |
| Distinct observed scoring targets | {decision['unique_scored_targets']:,} |
| Main calibration/test values parsed | none; November 2016 onward sealed |

Full inclusion/exclusion reasons and per-building training missingness, zero and
negative counts are in [`building_eligibility.csv`](../manifests/building_eligibility.csv).
Selection requires 95% finite nonnegative training values, nondegenerate training
consumption, and 168 fully observed usable days. Sites and building names are
sorted, then selected in site round-robin order. This is a deterministic pilot
panel, not a representative random sample of all building types.

Metadata include site IDs, building IDs and timezones. The parsed local grid has
{audit['duplicate_timestamps']} duplicate timestamps and {audit['nonhourly_steps']}
nonhourly steps. That regular grid does not establish DST disambiguation or clock
accuracy. Timezone-ambiguous/nonexistent hours and their predecessors are excluded.
No artificial UTC precision or physical cross-site aggregation is introduced.

Training is January–September 2016. October 1–10 is reserved for covariance,
October 11–20 for interval correction, and October 21–31 for scoring. A seven-day
embargo keeps seasonal-naive lag-168 inputs in validation; the resulting covariance
sample actually lies October 8–10 and contains
{residual.historical_covariance_observations.min()}–{residual.historical_covariance_observations.max()}
observed sampled origins per building. This short history limits the shrinkage
comparison. Models, records and hyperparameters were not revised after scoring.

## Venue conditions

The [official workshop page](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home)
was rechecked: December 14 online, October 15 submission date, 10-page full /
5-page short limits, November 5 notification, November 20 camera-ready and
November 26 registration. Its waiver remains prospective, alongside full author
registration language. Presentation duration, live/prerecorded obligations and
no-show rules remain unresolved. The portal could not be independently reread
with the web tool in this execution; the supplied plan records October 15 23:59
AoE (October 16 11:59 UTC). No submission, registration or organizer contact occurred.

## Resource accounting

The Stage 1 allocation ledger begins **{ledger['start_utc']}**, with a 7,200-second
hard ceiling. Recorded stage window through its latest close is **{allocated:.1f}
seconds ({allocated/3600:.3f} hours)**, including setup, failed training-rank attempt,
idle development, fitting, benchmark and audits. CUDA-event intervals in the
benchmarks total {device_seconds:.6f} seconds; these device
timings are distinct from allocated wall time and are not provider billing time.

Final process/storage inspection is in [`final_runtime.json`](../results/final_runtime.json).
The archive is 0.595 GB; processed data/cache remain below 10 GB and the observed
process memory remains below 20 GB. Downloaded package sizes are retained in
`environment-install.log`; preinstalled CUDA/PyTorch were reused. The data fetch
enforces a 2 GB archive-download ceiling. Small literature downloads are separately
recorded in the local source manifest. Actual aggregate downloads remain below 2 GB.
The pod remains user-allocated; no background research experiment is left running.
'''
    stage=f'''# Stage 1: completed pilot and stop decision

**Recommendation: stop the present sketch branch.** Preserve the implementation
and negative contract diagnostic; do not launch the 24-hour main study. This
pilot establishes a working bounded interface and numerical corollary, not a
new general fusion theorem, calibrated real-world guarantee, or successful paper.

## Completed work

The pinned BDG2 data audit selected 16 buildings at 16 sites using training data
alone. Four fixed calendar OLS providers per building each use 42 complete days
(1,008 records). Shared cores contain 0, 21 or 38 days. Pairwise intersections
are therefore 0, 504 and 912 records; unions contain 4,032, 2,520 and 1,296 records.
Per-provider sample count stays fixed while total unique evidence shrinks.
One allocation seed and two projection seeds are frozen in the manifests.

There are 48 building/allocation conditions, 192 provider fits, 4,096 distinct
scheduled building-target origins, and {decision['unique_scored_targets']:,}
observed scoring targets. The two sketch representations process 24,576 query
sets / 98,304 provider messages. They are not additional observations. There are
no duplicate packets in the outcome study; controlled protocol tests add them.
Only three calendar week groups appear in scoring, two partial. All 2017 outcomes
remain sealed, so no annual, seasonal-test or general deployment claim is made.

The first attempt stopped during training-only OOF rank checking before scoring.
The fixed rank-reduction rule was then applied and the successful complete pilot
took **{complete_event['wall_seconds']:.2f} seconds**. Existing data and the original
allocation clock were preserved. No model/seed/overlap retuning followed results.

Implemented: canonical identities, immutable binary messages, duplicate and
revision resolution, finite sketch epochs, target/unit checks, QR influence,
FP64 convex fusion with gap checks and individual fallback, optimized scalar CI,
exact conservative lineage, Ledoit–Wolf historical covariance, uninflated
sketches, seasonal naive, all individuals, equal weights, common-noise correction
and a privileged pooled predictor. The deployable consumer has no outcome or
exact-influence argument. An explicitly richer exact interface reconstructs
operators from public calendar features and compressed support identities.

## Mathematics and checks

**{tests}.** The retained controlled panel has 54 condition families, 108
projection evaluations and 36 distinct projection draws (shared across three
noise settings). There were **zero observed projection-event failures and zero
within-event inequality failures**. These counts are numerical diagnostics,
not statistical verification of the advertised probability.

The illustrative optimum is `(4/15,4/15,7/15)`, mean 105.2 and variance 43/15.
Tests cover zero/duplicate/signed influence, unequal scales, near singularity,
an independent SciPy solver and a two-provider ESCI connection. Shared future
noise cannot disappear under disjoint IDs. A deliberate correlated-innovation
example, omitted future noise and projection-adaptive nullspace vector remain
explicit assumption violations.

Pilot epsilons are {epochs[0]['epsilon']:.6f} (k=512) and
{epochs[1]['epsilon']:.6f} (k=2048), based on 12,288 queries and delta=.005 each.
Both epochs used exactly their declared capacity. Maximum observed normalized
Gram errors were {costs[costs.k==512].max_relative_gram_error.max():.6f} and
{costs[costs.k==2048].max_relative_gram_error.max():.6f}, respectively. Maximum
relative QP gap was {costs.max_relative_solver_gap.max():.3g}. Main wire/numerics
are FP64; the maximum measured FP32 Gram discrepancy was
{costs.max_fp32_relative_gram_error.max():.3g} relative to exact norm products.
No formal floating-point certificate is claimed. See [PROOF_AUDIT.md](../docs/PROOF_AUDIT.md).

## Real outcomes: raw versus empirical calibration

The local OOF scales and shared future variance are working empirical quantities.
The common future term is the mean of provider-local training OOF MSEs; it is
not an identified physical decomposition. Under this convention, training
influence accounts for **{decision['training_influence_fraction_mean']:.2%}** of
individual modeled predictive variance on average (condition means range
{diag.training_influence_fraction_mean.min():.2%}–{diag.training_influence_fraction_mean.max():.2%}).
Monthly training bias/RMSE, residual autocorrelation and historical provider-error
correlations are retained in `residual_diagnostics.json` and `diagnostics.json`.
Training residual lag-1 correlation averages 0.844 (lag-24: 0.486), so independent
innovations are not a defensible empirical default for these regressions.

Scores average allocation conditions within each building, then buildings equally.
Intervals are symmetric standardized-error quantile corrections fitted only on
October 11–20. Reservation is the fitted one-sided 0.8 quantile, clipped at zero,
with illustrative 4:1 under/over costs; these are not electricity tariffs.

{chr(10).join(table)}

All four individual results, MAE, RMSE, bias and raw widths are retained in
[`summary_metrics.csv`](../results/summary_metrics.csv). Individual 2 is shown
as a strong member of the prespecified baseline family, not selected as a new
deployable rule after scoring. Duplicate-aware independence equals ordinary
independence here because all primary estimator messages are distinct.

Exact lineage improves calibrated normalized interval score by only **0.48%**
over common-noise-corrected independence and slightly worsens reservation loss.
The k=2048 sketch score is 1.41% lower than exact lineage, with 0.71 percentage
points less 90% coverage, but all these calibrated coverage levels are well below
90%. This is not evidence that sketching is intrinsically superior to exact
information. Its extra inflation changes empirical weights and scale correction.
The sketch's score improvement over individual 2 is under 1%, with lower coverage.
No 5% practical advantage over the strongest deployable family is established.

The large raw difference from naive independence mostly disappears after keeping
the common future term. Raw corrected intervals cover about 96% at nominal 90%,
and their chronological calibration does not transfer reliably. The short
historical covariance window is especially weak for the shrinkage estimate;
these results do not establish a general failure of learned covariance fusion.

[`paired_sensitivity.json`](../results/paired_sensitivity.json) resamples all
sites/buildings/methods together across the three observed week groups 1,000 times,
after averaging allocation replicates within targets. With two partial weeks,
its ranges are descriptive sensitivity only. The sketch-minus-exact interval-score
range includes zero. Site-level and site-deletion results and the cleaned-mask
sensitivity are retained; none was used to select a winning configuration.

![Measured pilot quality](figures/pilot_quality.png)

## Metadata, computation and hardware

For all 48 allocations, a real lossless exact-support message reconstructed the
full signed operator with **zero measured absolute difference**. Its total size
for all four providers is {int(exact.once_bytes.min())}–{int(exact.once_bytes.max())}
bytes once per model set (mean **{exact.once_bytes.mean():.0f} bytes**), including
the public feature recipe, canonical time dictionary, active columns and scales.
Decode/reconstruction takes {1000*exact.parse_and_reconstruction_seconds.mean():.2f}
ms on average. It exposes exact support IDs and assumes public calendar features;
it is deployable only under that richer contract, not a hidden-data oracle.

The four k=2048 cached sketch operators occupy about
**{primary.cached_sketch_operator_once_bytes.mean()/1e6:.3f} MB** once, before the
same dynamic query headers. Per-query FP64 sketch messages cost
**{primary.sketch_bytes_per_query.mean()/1000:.2f} KB** per four-provider query.
The 256-query amortized plot charges identical dynamic-header bytes to both
contracts, so exact exchange is not credited with free headers or model refreshes.
The sketch fails the provisional 2x saving gate against compressed/cached exact
lineage. Per-query FP32 payload arithmetic is reported separately, not as a timed
or formally certified alternative.

{chr(10).join(timing)}

{chr(10).join(cold)}

Cold model-state latency includes reading frozen local operators/features,
canonical ID construction, fresh Gaussian columns, operator transfer/setup,
wire parsing/validation, optimization and output. Five replicates supply each
cold percentile; these measurements supplement rather than replace the original
warm records. Model fitting and archive preparation are separate study setup,
and the OS disk cache is not evicted. Add the
measured {bench['cuda_initialization_seconds']:.3f} s CUDA initialization once to
the first GPU use. The supplementary cold run starts after device inspection;
its explicit `cuda.init` timing excludes context setup and is not a startup
measurement. Per-allocation cold costs and stage decomposition
are in `pilot_costs.csv`. For k=2048 the average serialization/parse/validation
stage takes {primary.protocol_seconds.mean():.3f} s per 256 queries, versus
{primary.solver_seconds.mean():.4f} s for the CPU convex solver. No useful complete
pipeline GPU speedup appears at the measured sizes; single-query GPU latency is
higher. This is not a claim about all batch sizes or other representations.

The matched GPU replay uses actual frozen provider operators and inputs, FP64,
explicit synchronization, transfers, parsing and output encoding. CPU/GPU mean
and variance disagreement is at most {bench['max_cpu_gpu_mean_absolute_difference']:.3g}
and {bench['max_cpu_gpu_variance_absolute_difference']:.3g}, respectively.
Peak CUDA allocation is {bench['peak_vram_allocated_bytes']/2**20:.1f} MiB; peak
benchmark RSS is {bench['peak_process_rss_bytes']/1e9:.3f} GB. CUDA event intervals
sum to {device_seconds:.6f} seconds across both benchmark packages. The conservative
allocated Stage 1 window is **{allocated:.1f} seconds ({allocated/3600:.3f} h)**,
below its two-hour ceiling. Billing allocation outside this window is unknown.

![Measured pilot cost](figures/pilot_cost.png)

## Main-study readiness and gates

{chr(10).join(projection)}

These are linear projections from measured CPU warm FP64 replay, not actual
full-year runs. The 25% margin and eight hours for other work are explicit planning
assumptions, charging wall time while the GPU pod remains allocated. A later
CPU-only execution without an allocated GPU would have different accounting.
The 128-building primary replay alone takes about 30.6 hours and
would transmit roughly 693 GB in this uncached representation. The 32-building
scenario projects below 24 hours but fails the original minimum 64-building
evidence target. Cached exact exchange suggests a cheaper different study; no
unmeasured cached-sketch speedup is substituted into this projection.

`python scripts/run_main_study.py --authorize-main --max-gpu-hours 24` is a
fail-closed launcher: it refuses the false authorization flag in the frozen
config, failed scientific gate, or missing reviewed job list. After a separately
authorized revision it can enforce a persistent total cap, including Stage 1,
on an explicit foreground job list. **Full-study execution remains blocked by
failed scientific gates and the absence of an approved job list.** No full-study
job was launched.

Gate assessment: numerical correctness passes; rough compressed-vs-exact quality
thresholds pass on this short empirical pilot; useful compression fails;
complete-pipeline GPU advantage fails at tested sizes; practical advantage is
not established; mathematical novelty is unproven. The newer conservative
covariance-compression literature further weakens a broad theorem claim.

Preserve this package as an auditable negative/contract diagnostic. A paper would
need a substantive revised question and stronger evidence, not more seeds or
smaller training pools chosen to make overlap matter. Do not fund the main sketch
run from these results alone.

## Reproduction, limits and final state

The [README](../README.md) gives exact pilot, plotting and saved-results checks.
Configuration, source hashes, epoch registries, provider allocations, licenses,
environment snapshot and small numeric outputs are committed. Raw source and
per-target observed readings remain outside git. No submission, external message,
service deployment, new compute rental or new branch occurred. Work follows the
user-authorized `main` workflow.

Stage 1 intentionally does not implement the full 2017 experiment, p=32/64
scaling, a second allocation seed, optional refresh, neural models or claimed
operational federation. No empirical Gaussian, privacy, resilience or tail-event
guarantee is inferred. Final runtime inspection shows no active research worker;
the user's pod remains allocated. See [FEASIBILITY_REPORT.md](FEASIBILITY_REPORT.md)
for the archive/license and venue conditions that remain unresolved.
'''
    Path('reports').mkdir(exist_ok=True)
    Path('reports/FEASIBILITY_REPORT.md').write_text(feasibility)
    Path('reports/STAGE1_REPORT.md').write_text(stage)
    print('Wrote feasibility and Stage 1 reports from saved measurements')


if __name__=='__main__':main()
