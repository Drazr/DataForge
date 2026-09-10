# DataForge — Shared Project Documents

The `main` branch is the repository default and the single home for shared project planning:

- [Hackathon guidelines](HACKATHON_GUIDELINES.md)
- [Implementation roadmap](rime_implementation_roadmap.md)
- [Testing guide](RIME_TELEPHONY_TESTING_GUIDE.md)
- [Branch handoff instructions](docs/BRANCH_HANDOFF.md)
- [Noise grid v2 setup and baseline decisions](docs/NOISE_GRID_V2_PROTOCOL.md)

The first two pilot experiments have completed development evaluation. Their code and evidence remain on their respective branches:

1. [Noise-Masking Test](https://github.com/Drazr/DataForge/tree/noise-masking-test) — `colab_noise_masking.py`.
2. [Noise-Conditioned Delivery A/B](https://github.com/Drazr/DataForge/tree/noise-conditioned-ab) — `colab_noise_ab.py`.
3. [Noise Grid v2](https://github.com/Drazr/DataForge/tree/codex/noise-grid-v2) — `colab_noise_masking.py` for CPU INT8 measurement, then `colab_grid_analysis.py` for CPU analysis.

Each test branch retains its own code, dependencies, tests and runbook, and links here for shared planning and handoff instructions. This branch contains no experiment implementation.

Complete Noise Masking first and retain its outputs, datasets and evaluator models in Drive. Delivery A/B imports that baseline. See the [branch handoff instructions](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md) for the required copy.

Delivery A/B ended with no candidate promoted after 56 model reviews; held-out
evaluation was not run and human review remains pending. Compact evidence is on
`noise-conditioned-ab` at commit `4ddef62`. The next experiment is
[Noise grid v2](docs/NOISE_GRID_V2_PROTOCOL.md): a 294-score critical-text grid
using cached baseline speech, followed by CPU-only breakpoint analysis. The
tested CPU implementation is on `codex/noise-grid-v2` at commit `24c5553`.

Project-level scope decisions and their reasons are recorded in
[TROUBLESHOOTING.md](TROUBLESHOOTING.md). Each active test branch maintains its
own chronological `TROUBLESHOOTING.md` with problems and countermeasures.
