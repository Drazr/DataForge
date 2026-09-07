# Noise-Masking Test

Branch: `codex/noise-masking-test`.

Project scope: only **Noise-Masking Test → Noise-Conditioned Delivery A/B → Grid and Breakpoint Analysis**, in that order. Shared planning documents live only on `main`: [hackathon guidelines](https://github.com/Drazr/DataForge/blob/main/HACKATHON_GUIDELINES.md), [implementation roadmap](https://github.com/Drazr/DataForge/blob/main/rime_implementation_roadmap.md), and [testing guide](https://github.com/Drazr/DataForge/blob/main/RIME_TELEPHONY_TESTING_GUIDE.md). Catalog engineering methods are unchanged by this test-scope decision.

Copy the nine cells in [colab_noise_masking.py](colab_noise_masking.py) into Colab.
Exactly three blank lines separate cells. The first two mount Drive and clone
this branch. This workflow generates the baseline only: fixed speech, phone codec,
noise sweep, ASR fact/word recovery, ESTOI, DNSMOS and diagnostic exports.

Follow [the runbook](docs/COLAB_RUNBOOK.md). Results are saved under
`MyDrive/DataForge/noise_masking/outputs/<run-id>/`. No real results are bundled.

[Branch handoffs](docs/BRANCH_HANDOFF.md) explains how Grid Analysis and Delivery
A/B copy these outputs. The audio/scoring library and corpus also carry the frozen
intervention definitions needed by the separate A/B consumer; this notebook never
runs or selects those interventions. Keep all three branches at compatible scoring
versions when transferring evidence.

Local checks: `python -m unittest discover -s tests -v` after installing
`requirements-colab.txt` and FFmpeg. These are software checks, not measured
Rime experiments or human comprehension results.
