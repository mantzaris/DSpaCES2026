# Active scope - 2026-09-23

The user's regional-pilot instruction selects a retrospective digital twin of
the sampled Greater London households and a shared orthogonal matrix solver.
The planning handoff is `09ae274`, verified in the history of `main` before edits.
`DSpaCES_2026_Research_Plan.md` remains unchanged as the **When Forecast Contracts
Disagree candidate**, with its attribution and proofs. It is not this experiment.
The earlier BDG2 sketch study remains stopped and its main launcher disabled.

Authorized: one London archive, typed partitioned Parquet, training-only seasonal
factor model, bounded January-March 2013 replay, CPU/GPU solver comparison,
proofs, tests, measured report, and normal commit/push on main. No branches.

Limits: 4 GB downloaded, 30 GB new data/cache, 6 cumulative CPU job-hours,
3 cumulative GPU-allocated hours including tests/retries/setup. The per-GPU-job
ledger measures first pod execution to close. The final resource handoff also
conservatively charges the existing pod's allocation from the very first local
regional job through stage closure, including preparation, analysis and idle time;
this larger total is compared with the three-hour cap. CPU jobs have persistent
cumulative accounting, including whole GPU job durations and failed attempts.
Host target 8 GB, GPU target 24 GB. No earlier regional jobs were found locally
or on the existing pod at preflight. The earlier BDG2 allocation is separate.

2012 is training; January-March 2013 development; April-December 2013 and later
London outcomes remain sealed for analysis. Ingestion may type and partition
their bytes but must not summarize their demand values. BDG2 seals remain intact.
Provider partitions/access profiles are simulated; this is not a live regional
deployment or a causal tariff/outage study. No new hardware, pod lifecycle action,
compatibility-contract experiment, main study, or manuscript is authorized.

Hardware assumption in the request: RTX PRO 4500 with 48 GB. Runtime preflight:
RTX PRO 4500 Blackwell, 32,623 MiB total. Configure to measured hardware.

Completion: the regional pipeline and twin were executed, with 4,194 households
and 52.1 million training readings. The shared-basis speed/certificate gate failed
against banded CPU Cholesky. See the measured Stage 1 report. Execution ledgers
are closed, the pod remains allocated and idle, and no next study is authorized.
