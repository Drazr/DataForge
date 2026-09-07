# Rime Telephony & Adverse Audio Implementation Roadmap

## Active scope and execution order

Proceed only with **Noise-Masking Test → Noise-Conditioned Delivery A/B → Grid and Breakpoint Analysis**, using one Colab notebook per branch. This plan supersedes the earlier broader experiment roadmap. It makes no new decision about catalog engineering methods.

See [HACKATHON_GUIDELINES.md](HACKATHON_GUIDELINES.md), [RIME_TELEPHONY_TESTING_GUIDE.md](RIME_TELEPHONY_TESTING_GUIDE.md), and [branch handoffs](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md). Each test branch's README links its executable notebook and detailed runbook; the [main README](README.md) lists those branches.

## Phase 1 — Noise-Masking Test

- Branch: `noise-masking-test`; entry file: `colab_noise_masking.py`.
- Mount Drive, clone the branch, install dependencies, supply the Rime secret, and prepare the pinned evaluator models and reviewed public noise sources.
- Freeze configuration, synthetic corpus, development/held-out split, repeats and noise manifest. Run the existing preflight before the development baseline.
- Measure clean, +10, +5 and 0 dB conditions using the simulated phone codec, fixed noise sources, ASR WER/fact recovery, ESTOI and supporting DNSMOS scores.
- Review repeatable noise-attributable fact losses against matched clean controls. Preserve the configuration, per-clip scores, audio, diagnostic exports and synthesis cache.

Output: `MyDrive/DataForge/noise_masking/outputs/<run-id>/`. Retain the shared datasets and evaluator models at their original Drive paths.

## Phase 2 — Noise-Conditioned Delivery A/B

- Branch: `noise-conditioned-ab`; entry file: `colab_noise_ab.py`.
- Set the completed Noise-Masking run path. The notebook copies and verifies the frozen baseline, scored rows, clips and synthesis cache; it does not repeat the development baseline.
- Leave optional `GRID_RESULTS = None`: Grid Analysis runs later and is not a prerequisite.
- Freeze one or two challenge conditions supported by recurrent development failures. If none qualifies, stop intervention selection and report that result; do not invent a challenge.
- Compare the existing short-clause, targeted-repetition and native-slowdown variants with fixed model/voice and matched controls. These are auditable synthetic variants, not a required upstream LLM integration.
- Complete development listening checks, select/freeze a candidate, then evaluate it on held-out clips. A no-winner result is valid. Do not tune on held-out evidence.
- Export comparisons, listening queues and evidence status; review held-out audio before claiming improvement.

Output: `MyDrive/DataForge/delivery_ab/outputs/<run-id>/`.

## Phase 3 — Grid and Breakpoint Analysis

- Branch: `grid-breakpoint-analysis`; entry file: `colab_grid_analysis.py`.
- Run in a separate CPU Colab notebook after A/B. The default input remains the completed Noise-Masking baseline; A/B completion is the chosen order, not a baseline-analysis dependency.
- For optional analysis of A/B results, point the source at the completed Delivery A/B run, choose `results.csv`, and select one split and variant per analysis session.
- Copy evidence into this branch, verify its hashes and comparability, and reuse matching baseline summaries where available. No new speech generation or metric inference is performed.
- Freeze analysis settings before reviewing the grid. Report paired adjacent-SNR deterioration, recurrence, sample counts and uncertainty. Numeric acceptance limits require a recorded rationale and must not be presented as pre-established if selected after reviewing earlier results.
- Without defensible pre-established limits, report deterioration rather than an unacceptable-performance threshold. DNSMOS is excluded from this implementation's grid/breakpoint decisions.
- Save plots, interval tables and linked development cases. Because A/B is already complete, these cases are reporting evidence, not permission to retrospectively reselect its frozen candidate.

Output: `MyDrive/DataForge/grid_analysis/outputs/<run-id>/<session>/results/`.

## Boundaries and evidence status

Only the three workflows above are active experiments. Standalone telephone-format correctness, DNSMOS quality cross-check, streaming-continuity, DSP comparisons and automatic noise-policy training are not planned here. Embedded codec/preflight validation and quality guardrails remain necessary parts of the selected workflows.

Software checks are not measured experiments. Real Colab runs, credentials, noise-source approval and listening reviews are still required; no measured results are bundled. The simulated codec path does not establish live-phone performance or human comprehension.

## Catalog engineering — unchanged reference

The earlier catalog guidance is retained unchanged below; this scope update makes no selection or implementation decision about it:

Add catalog engineering only if it strengthens the product: interruptible playback, observable fallback, real telephony turn handling or explicitly labeled caching.
