# Experiment branches and evidence handoffs

## Current repository layout

`main` is the default branch. It owns `HACKATHON_GUIDELINES.md`,
`rime_implementation_roadmap.md`, `RIME_TELEPHONY_TESTING_GUIDE.md` and this
`docs/BRANCH_HANDOFF.md` guide. Test branches link to these shared documents;
their notebook scripts, dependencies, tests and workflow-specific runbooks remain
on their respective branches. `RIME_EVIDENCE.md` belongs to `noise-conditioned-ab`.

Use the exact branch names below.
For an existing Colab notebook, copy the latest cells from the matching branch.
Before starting a new run, use a fresh runtime so Cell 2 clones the current branch
and commit; existing checkouts are intentionally not updated automatically.
Preserve all Drive results, datasets, models and synthesis caches. Do not switch
code revisions during a frozen run without checking producer/consumer compatibility.

## Execution and evidence transfer

The two original pilots completed development evaluation. Next is
[Noise grid v2](NOISE_GRID_V2_PROTOCOL.md), implemented on
`codex/noise-grid-v2` at `24c5553`. Its producer verifies and reuses 14
critical-text syntheses and the frozen evaluator configuration while writing a
separate 294-score run with versioned noise calibration. Its second notebook
analyzes that run on CPU. The original experiment branches remain available.

Delivery A/B requires the complete Noise-Masking output and synthesis cache. It imports the frozen baseline without rerunning it.

| Workflow | Branch | Colab entry file |
| --- | --- | --- |
| Noise-Masking Test | noise-masking-test | colab_noise_masking.py |
| Noise-Conditioned Delivery A/B | noise-conditioned-ab | colab_noise_ab.py |
| Noise Grid v2 producer | codex/noise-grid-v2 | colab_noise_masking.py |
| Noise Grid v2 analysis | codex/noise-grid-v2 | colab_grid_analysis.py |

Noise Masking produces the baseline. Delivery A/B
copies the frozen baseline, scored rows, audio and synthesis cache into its own
checkout, then evaluates interventions; it does not rerun the development baseline.
The two audio branches include identical shared scoring/audio utilities to preserve
the producer configuration and evaluation hashes.

Every consumer copies inputs under its branch checkout's `inputs/` folder.
`handoff.json` records the originating run, file hashes and audio path mappings.
Copies fail on conflicts rather than overwriting different evidence. Drive retains
producer outputs, consumer outputs, large downloaded datasets and model snapshots.
Download/model assets remain shared in Drive; they are not experimental outputs.

Measured baseline and A/B outputs now exist. The A/B audit and compact evidence
were committed at `4ddef62` on `noise-conditioned-ab`; the full ZIP remains external.
The outcome is no promoted candidate, with no held-out run. Small copied evidence
files are retained after review; raw audio/models remain ignored by Git. V2 must
not pool old noisy measurements with its new calibration.

Persistent Drive folders under `MyDrive/DataForge/`:
- `noise_masking/outputs/<run-id>/`: measured baseline and diagnostic exports.
- `delivery_ab/outputs/<run-id>/`: copied baseline plus A/B and held-out evidence.
- `noise_grid_v2/outputs/<run-id>/`: v2 measurements, separate from pilot results.
- `grid_analysis_v2/outputs/<run-id>/<timestamp>/results/`: CPU breakpoint reports.
