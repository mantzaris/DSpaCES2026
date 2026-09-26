# Stage 1 feasibility report

The bounded pilot completed on September 22–23, 2026 UTC. **Data access and the
numerical implementation are feasible; expanding the proposed sketch study is
not supported by its current scientific or cost gates.** See [STAGE1_REPORT.md](STAGE1_REPORT.md).

## Machine and environment

* Actual device: **NVIDIA RTX PRO 4500 Blackwell**, 32,623 MiB (33,685,569,536 bytes).
  The older RTX 6000 Ada / 48 GB sections of the plan do not describe this machine.
* Driver 580.159.04; Python 3.12.3;
  PyTorch 2.8.0+cu128, CUDA runtime 12.8.
* Host CPU: AMD EPYC 7443P, 24 physical / 48 logical cores. Container CPU quota
  `1020000 100000` permits about 10.2 CPU cores; measurements used
  four BLAS/PyTorch threads. Container memory quota is 62.0 GB.
* Device ceiling: 24 GiB; actual benchmark peak 176.7 MiB.
  Measured benchmark process peak RSS: 1.427 GB.
  No compilation, neural model download or GPU training was performed. GPU work
  was fixed-operator projection, Gram construction and batched convex fusion.

[`environment.lock.txt`](../environment.lock.txt) records the full environment;
[`requirements.lock.txt`](../requirements.lock.txt) isolates pinned analysis
dependencies. The host Python 3.8 environment was also used for code tests, but
the reported experiment and final figures use the pod environment.

## Archive and terms

The originating [BDG2 v1.0 archive](https://zenodo.org/records/3887306) downloaded
as **595,266,464 bytes**. Published MD5 matched `44393dc4cf61e84dec105e955368c890`.
Observed SHA-256: `50ef5178c5d4ce18b0d0480140e83349d1b058f10b4b1e59b9e8698a7b8e417b`. Archive paths, sizes, CRC labels and
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
| Electricity columns | 1,578 |
| Parsed rows | 7,320, January 1–October 31, 2016 |
| Training hours | 6,576 |
| Training finite readings across all electricity columns | 9,811,945 / 10,376,928 positions |
| Eligible buildings / sites | 1,324 / 17 |
| Frozen selected buildings / sites | 16 / 16 |
| Unique selected origins across October roles | 4,096 |
| Distinct observed scoring targets | 1,856 |
| Main calibration/test values parsed | none; November 2016 onward sealed |

Full inclusion/exclusion reasons and per-building training missingness, zero and
negative counts are in [`building_eligibility.csv`](../manifests/building_eligibility.csv).
Selection requires 95% finite nonnegative training values, nondegenerate training
consumption, and 168 fully observed usable days. Sites and building names are
sorted, then selected in site round-robin order. This is a deterministic pilot
panel, not a representative random sample of all building types.

Metadata include site IDs, building IDs and timezones. The parsed local grid has
0 duplicate timestamps and 0
nonhourly steps. That regular grid does not establish DST disambiguation or clock
accuracy. Timezone-ambiguous/nonexistent hours and their predecessors are excluded.
No artificial UTC precision or physical cross-site aggregation is introduced.

Training is January–September 2016. October 1–10 is reserved for covariance,
October 11–20 for interval correction, and October 21–31 for scoring. A seven-day
embargo keeps seasonal-naive lag-168 inputs in validation; the resulting covariance
sample actually lies October 8–10 and contains
32–33
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

The Stage 1 allocation ledger begins **2026-09-22T23:25:34+00:00**, with a 7,200-second
hard ceiling. Recorded stage window through its latest close is **2947.0
seconds (0.819 hours)**, including setup, failed training-rank attempt,
idle development, fitting, benchmark and audits. CUDA-event intervals in the
benchmarks total 1.141481 seconds; these device
timings are distinct from allocated wall time and are not provider billing time.

Final process/storage inspection is in [`final_runtime.json`](../results/final_runtime.json).
The archive is 0.595 GB; processed data/cache remain below 10 GB and the observed
process memory remains below 20 GB. Downloaded package sizes are retained in
`environment-install.log`; preinstalled CUDA/PyTorch were reused. The data fetch
enforces a 2 GB archive-download ceiling. Small literature downloads are separately
recorded in the local source manifest. Actual aggregate downloads remain below 2 GB.
The pod remains user-allocated; no background research experiment is left running.
