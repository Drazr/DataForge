# DataForge — Shared Project Documents

The `main` branch is the repository default and the single home for shared project planning:

- [Hackathon guidelines](HACKATHON_GUIDELINES.md)
- [Implementation roadmap](rime_implementation_roadmap.md)
- [Testing guide](RIME_TELEPHONY_TESTING_GUIDE.md)
- [Branch handoff instructions](docs/BRANCH_HANDOFF.md)

Only the following two experiments are active, in this order. Use a separate Colab notebook and the corresponding branch for each:

1. [Noise-Masking Test](https://github.com/Drazr/DataForge/tree/noise-masking-test) — `colab_noise_masking.py`.
2. [Noise-Conditioned Delivery A/B](https://github.com/Drazr/DataForge/tree/noise-conditioned-ab) — `colab_noise_ab.py`.

Each test branch retains its own code, dependencies, tests and runbook, and links here for shared planning and handoff instructions. This branch contains no experiment implementation.

Complete Noise Masking first and retain its outputs, datasets and evaluator models in Drive. Delivery A/B imports that baseline. See the [branch handoff instructions](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md) for the required copy.

Catalog engineering guidance is unchanged. Actual experiments and manual listening reviews remain pending; software tests are not experimental evidence.

Project-level scope decisions and their reasons are recorded in
[TROUBLESHOOTING.md](TROUBLESHOOTING.md). Each active test branch maintains its
own chronological `TROUBLESHOOTING.md` with problems and countermeasures.
