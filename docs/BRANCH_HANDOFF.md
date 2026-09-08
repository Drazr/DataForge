# Two independent workflow branches

## Current repository layout

`main` is the default branch. It owns `HACKATHON_GUIDELINES.md`,
`rime_implementation_roadmap.md`, `RIME_TELEPHONY_TESTING_GUIDE.md` and this
`docs/BRANCH_HANDOFF.md` guide. Test branches link to these shared documents;
their notebook scripts, dependencies, tests and workflow-specific runbooks remain
on their respective branches. `RIME_EVIDENCE.md` belongs to `noise-conditioned-ab`.

The two test branches have no prefix; use the exact names below.
For an existing Colab notebook, copy the latest cells from the matching branch.
Before starting a new run, use a fresh runtime so Cell 2 clones the current branch
and commit; existing checkouts are intentionally not updated automatically.
Preserve all Drive results, datasets, models and synthesis caches. Do not switch
code revisions during a frozen run without checking producer/consumer compatibility.

## Execution and evidence transfer

Active experiments only, in the chosen order: **Noise-Masking Test → Noise-Conditioned Delivery A/B**. See the shared documents on `main`: the [roadmap](https://github.com/Drazr/DataForge/blob/main/rime_implementation_roadmap.md) and [testing guide](https://github.com/Drazr/DataForge/blob/main/RIME_TELEPHONY_TESTING_GUIDE.md). Catalog engineering methods are unchanged and outside this scope decision.

Delivery A/B requires the complete Noise-Masking output and synthesis cache. It imports the frozen baseline without rerunning it.

| Workflow | Branch | Colab entry file |
| --- | --- | --- |
| Noise-Masking Test | noise-masking-test | colab_noise_masking.py |
| Noise-Conditioned Delivery A/B | noise-conditioned-ab | colab_noise_ab.py |

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

There are no measured outputs to transfer yet. Consumer cells perform the copies
once the producer finishes. Small copied evidence files can be committed to the
consumer branch after review; raw audio/models remain ignored by Git. Nothing is
automatically uploaded or mixed into another branch while an experiment runs.

Persistent Drive folders under `MyDrive/DataForge/`:
- `noise_masking/outputs/<run-id>/`: measured baseline and diagnostic exports.
- `delivery_ab/outputs/<run-id>/`: copied baseline plus A/B and held-out evidence.
