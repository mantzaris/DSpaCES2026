# Research progress

Updated 2026-09-30. Active on `main`. The user will push at completion. Do not make branches or retry pushing.

The full 791-line specification was read. Part C was extracted and run first. Its 13 checks passed. Saved-input CPU/CUDA parity passed, with maximum float64 discrepancy 1.11e-16 and float32 discrepancy 8.56e-8. All 16 local integration tests passed. The production audit independently recomputed 8,736 candidate scores from saved samples in 1,092 test cases, with maximum discrepancy 7.11e-15. Trained GDN and S4 comparator audits passed.

The existing RunPod GPU is an RTX PRO 4500 Blackwell. Remote work is `/workspace/iot-inconsistency`. Revised training and all five primary configurations are complete. Three dataset families remain synthetic, Intel Berkeley and SKAB. Native process labels are separate from injected sensor and association faults. Models, split manifests, calibration fits and raw predictive draws are saved. No new paid resource was created.

Primary results do not establish a detection advantage over the development-selected PCA comparator. A narrower attribution-precision benefit at 10% screened-candidate coverage appears in the 32-channel nonlinear simulator and reverses at higher coverage. These findings are retained. Secondary confidence comparisons are descriptive, not a replacement endpoint. Ablations, source/graph contamination, native process evaluation, portable weight export and uncontended latency measurements are continuing as finite resumable jobs.

The local Neo4j store contains actual saved experiment evidence. The node-link operator application loads ten cases and logs confirm/reject/defer actions. Browser tests passed. Automated review records are labeled as interface verification, not human diagnoses. Figure and manuscript generation is implemented. The current manuscript is a layout draft with secondary-result placeholders, not a completed paper.

Resume from this directory

```bash
python3 -m pytest -q
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status secondary_experiments
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status finish_artifacts
bash scripts/runpod.sh exec .venv/bin/python scripts/job.py status verify_final_gpu
bash scripts/runpod.sh pull
python3 scripts/analyze.py
python3 scripts/analyze_confidence.py
python3 scripts/summarize_design.py
python3 scripts/export_graph.py --persist
python3 scripts/figures.py
python3 scripts/make_paper.py --draft
```

`secondary.sh` resumes per-case ablations and stress runs, then native SKAB events. `finish_artifacts.sh` waits for it and produces latency/model exports/figures. `verify_final_gpu.sh` waits for artifacts and reproduces saved cases from portable weights, then runs the GPU tests. Stress cases marked before `scaled-screen-v2` need the documented screening correction and rerun before final stress analysis. Final manuscript generation must omit `--draft` and pass its completeness gates. Preserve all final weights before ending GPU work. No automatic submission is authorized.
