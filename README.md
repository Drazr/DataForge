# Noise-Conditioned Delivery A/B

Branch: `codex/noise-conditioned-ab`.

Project scope: only **Noise-Masking Test → Noise-Conditioned Delivery A/B → Grid and Breakpoint Analysis**, in that order. Shared planning documents are [hackathon guidelines](HACKATHON_GUIDELINES.md), [implementation roadmap](rime_implementation_roadmap.md), and [testing guide](RIME_TELEPHONY_TESTING_GUIDE.md). Catalog engineering methods are unchanged by this test-scope decision.

Copy the eleven cells in [colab_noise_ab.py](colab_noise_ab.py) into Colab, preserving
the three-blank-line cell separators. Cells 1–2 mount Drive and clone this branch.

This workflow starts from a completed Noise-Masking baseline. It copies the needed
outputs into `inputs/noise_masking/<run-id>/`, verifies hashes/configuration, and
imports baseline scores/audio without synthesizing or transcribing them again.
Optional Grid Analysis conclusions are copied into `inputs/grid_analysis/`.
New A/B and held-out results go to `MyDrive/DataForge/delivery_ab/outputs/<run-id>/`.

Follow [the runbook](docs/COLAB_RUNBOOK.md) and [branch handoffs](docs/BRANCH_HANDOFF.md).
Shared audio/scoring helpers match the Noise-Masking branch. The frozen producer
manifest supplies runtime corpus/settings; the example config and fixtures support
shared-library tests. This branch does not perform a fresh development noise sweep.

No measured results are included. Local checks: `python -m unittest discover -s tests -v`
after installing `requirements-colab.txt` and FFmpeg. Human listening and a real
Colab execution remain necessary.
