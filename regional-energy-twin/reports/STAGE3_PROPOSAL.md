# Archival disposition — no Stage 3 proposed

September 23, 2026 UTC. Decision **C: stop/defer**. Neither the current evidence
nor the event-time candidate clears the research gates. There is no ready-to-paste
execution prompt, compute allocation or manuscript task. The original main-study
entry point stays disabled, and 2017 remains sealed. No new experiment is needed
to resolve the focused Stage 2 CSV correction.

## Preserved artifacts

The existing local project disk now contains a verified snapshot at:

```
/home/resort/Documents/repos/DSpaCES2026/data/archives/stage1_pod_20260923/
```

All **90 research files / 855,761,126 bytes** in the inventoried pod project
matched their SHA-256 hashes after copying. The manifest is
[stage2_artifact_preservation.json](../manifests/stage2_artifact_preservation.json).
Particularly important files are `data/benchmark_input.npz` (109,743,948 bytes),
`results/pilot_predictions.csv` (5,311,547 bytes), numerical outputs, configuration,
logs and source. The original BDG2 ZIP is also retained without extracting its
sealed outcomes. Virtual environment files, bytecode and pytest caches are
excluded as reconstructible runtime state. Environment pins/snapshots are saved.

No inventoried irreplaceable **project** artifact remains only on the pod. The
small reports/code/aggregate evidence are pushed to the existing GitHub origin.
Raw readings, the ZIP and per-target evaluator file remain ignored by git; their
durable copy is on the user's existing local disk, not an independently verified
off-site backup. Preserve `data/archives/`; do not treat it as disposable cache.
Any unrelated files outside `/workspace/DSpaCES2026-stage1` were not inventoried
or changed. No new cloud storage was allocated.

To recheck the local snapshot without executing a study:

```bash
python3 scripts/verify_stage2_archive.py
```

The verifier can use the committed preservation manifest; the raw process
inventory is local-only. This checksum operation reads bytes, not dataset
outcomes. During Stage 2 it was run through the capped diagnostic wrapper.

## Concrete user-controlled stop procedure

The pod is still allocated and may continue incurring charges. GPU-idle time
does not imply billing has stopped. Its reported `/workspace` filesystem resolves
to the container overlay rather than a separately mounted durable volume, so
the archive above is the preservation basis. No persistence guarantee is inferred
from the directory name.

1. Keep the verified local archive and the pushed `main` commit. No remaining
   project artifact needs copying from the inventoried snapshot. If unrelated
   work has since been added on the pod, copy that separately before stopping.
2. In the [Runpod Pods console](https://console.runpod.io/pods), locate the existing
   pod using its ID/connection details in the final resource ledger; verify it
   is the instance at `213.173.107.237:38369` before taking an action.
3. Expand that pod, choose **Stop** (square icon), and confirm. Do not choose
   Terminate/Delete, Reset, or edit the running configuration. Verify the console
   reports it stopped and review the remaining storage allocation there.

This is a procedure for the user, **not an action performed or scheduled here**.
Runpod documents that Stop releases the GPU, clears container disk and retains
volume disk, with storage charges continuing; the local snapshot makes this
project independent of uncertain pod storage persistence.
[Runpod's current management instructions](https://docs.runpod.io/pods/manage-pods)
support the procedure and storage distinction. Rates and actual billing were
not queried. No termination or storage deletion is recommended in this stage.

Future reconsideration needs a new, independently motivated research question,
a demonstrated distinction from the audited literature, a feasible sealed-data
protocol, and explicit authorization. More favorable overlap settings, selected
buildings or extra GPU tuning are not an archival follow-up.
