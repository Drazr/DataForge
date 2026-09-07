# DataForge — Shared Project Documents

The `main` branch is the single home for shared project planning:

- [Hackathon guidelines](HACKATHON_GUIDELINES.md)
- [Implementation roadmap](rime_implementation_roadmap.md)
- [Testing guide](RIME_TELEPHONY_TESTING_GUIDE.md)

Only the following three experiments are planned, in this order. Use a separate Colab notebook and the corresponding branch for each:

1. [Noise-Masking Test](https://github.com/Drazr/DataForge/tree/codex/noise-masking-test) — `colab_noise_masking.py`.
2. [Noise-Conditioned Delivery A/B](https://github.com/Drazr/DataForge/tree/codex/noise-conditioned-ab) — `colab_noise_ab.py`.
3. [Grid and Breakpoint Analysis](https://github.com/Drazr/DataForge/tree/codex/grid-breakpoint-analysis) — `colab_grid_analysis.py`.

Each test branch retains its own code, dependencies, tests, runbook and handoff instructions, and links here for shared planning. This branch contains no experiment implementation.

Complete Noise Masking first and retain its outputs, datasets and evaluator models in Drive. Delivery A/B imports that baseline; Grid Analysis runs last and defaults to the same baseline. See the [branch handoff instructions](https://github.com/Drazr/DataForge/blob/codex/noise-masking-test/docs/BRANCH_HANDOFF.md) for required copies and optional A/B-result analysis.

Catalog engineering guidance is unchanged. Actual experiments and manual listening reviews remain pending; software tests are not experimental evidence.
