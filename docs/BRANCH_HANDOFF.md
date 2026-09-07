# Three independent workflow branches

Active experiments only, in the chosen order: **Noise-Masking Test → Noise-Conditioned Delivery A/B → Grid and Breakpoint Analysis**. See the [roadmap](../rime_implementation_roadmap.md) and [testing guide](../RIME_TELEPHONY_TESTING_GUIDE.md). Catalog engineering methods are unchanged and outside this scope decision.

Delivery A/B requires only Noise-Masking outputs; leave its optional Grid input unset. Grid runs last and defaults to the Noise-Masking baseline. To analyze A/B outputs instead, select the completed Delivery A/B source run, `results.csv`, and one split/variant per session. Later Grid findings do not reopen the already frozen A/B candidate or permit tuning on held-out data.

| Workflow | Branch | Colab entry file |
| --- | --- | --- |
| Noise-Masking Test | codex/noise-masking-test | colab_noise_masking.py |
| Noise-Conditioned Delivery A/B | codex/noise-conditioned-ab | colab_noise_ab.py |
| Grid and Breakpoint Analysis | codex/grid-breakpoint-analysis | colab_grid_analysis.py |

Noise Masking produces the baseline. Grid Analysis copies its tables, metadata
and clips into its own checkout and performs CPU-only analysis. Delivery A/B
copies the frozen baseline, scored rows, audio and synthesis cache into its own
checkout, then evaluates interventions; it does not rerun the development baseline.
Grid conclusions may also be copied into Delivery A/B for human challenge review.
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
- `grid_analysis/outputs/<run-id>/<session>/results/`: grid conclusions and links.
- `delivery_ab/outputs/<run-id>/`: copied baseline plus A/B and held-out evidence.
