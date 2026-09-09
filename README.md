# Noise-Conditioned Delivery A/B

Branch: `noise-conditioned-ab`.

Project scope: **Noise-Masking Test → Noise-Conditioned Delivery A/B**. Grid/Breakpoint Analysis was retired to prioritize this direct intervention test. Shared planning documents live only on `main`: [hackathon guidelines](https://github.com/Drazr/DataForge/blob/main/HACKATHON_GUIDELINES.md), [implementation roadmap](https://github.com/Drazr/DataForge/blob/main/rime_implementation_roadmap.md), and [testing guide](https://github.com/Drazr/DataForge/blob/main/RIME_TELEPHONY_TESTING_GUIDE.md). Catalog engineering methods remain unchanged.

Copy the thirteen cells in [colab_noise_ab.py](colab_noise_ab.py) into Colab, preserving
the three-blank-line cell separators. Cells 1–2 mount Drive and clone this branch.

This workflow starts from a completed Noise-Masking baseline. It copies the needed
outputs into `inputs/noise_masking/<run-id>/`, verifies hashes/configuration, and
imports baseline scores/audio without synthesizing or transcribing them again.
New A/B and held-out results go to `MyDrive/DataForge/delivery_ab/outputs/<run-id>/`.

Follow [the runbook](docs/COLAB_RUNBOOK.md) and [branch handoffs](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md).
Shared audio/scoring helpers match the Noise-Masking branch. The frozen producer
manifest supplies runtime corpus/settings; the example config and fixtures support
shared-library tests. This branch does not perform a fresh development noise sweep.

The verified stress-baseline review is included under
`inputs/noise_masking_review/6bd1eb398398af0e/`. It supports the prefilled
`competing_speech_-5dB` challenge. Cell 4 copies the complete original run and
synthesis cache from Drive; the review is not a replacement for that handoff.
Development A/B metrics have been reported from Colab: Repeat passed the metric
screen; Clauses and Slow failed. The requested delegated
[local model review](docs/MODEL_REVIEW.md) covered all 56 Baseline/Repeat clips and
failed Repeat on fact preservation and quality. No candidate was selected and the
held-out split was intentionally not run. Human review remains explicitly pending;
the model result is not presented as a human-comprehension claim. The compact,
audited result is under `evidence/conditioned_ab/6bd1eb398398af0e/`. Local checks:
`python -m unittest discover -s tests -v` after installing dependencies and FFmpeg.

Session problems, fixes and the current baseline eligibility decision are tracked
in [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Saved-baseline review belongs to
Noise-Masking Cell 10; there is no separate Colab review script in this branch.

Development audio can be audited with `scripts/run_local_review.py`; this is
separate from the upstream saved-baseline rescoring workflow. Model-review
evidence retains the raw responses and audio hashes without committing model weights.
