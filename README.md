# Noise-Masking Test

Branch: `noise-masking-test`.

Project scope: **Noise-Masking Test → Noise-Conditioned Delivery A/B**. Grid/Breakpoint Analysis was retired after this test produced a qualifying stress condition. Shared planning documents live only on `main`: [hackathon guidelines](https://github.com/Drazr/DataForge/blob/main/HACKATHON_GUIDELINES.md), [implementation roadmap](https://github.com/Drazr/DataForge/blob/main/rime_implementation_roadmap.md), and [testing guide](https://github.com/Drazr/DataForge/blob/main/RIME_TELEPHONY_TESTING_GUIDE.md). Catalog engineering methods remain unchanged.

Copy the ten cells in [colab_noise_masking.py](colab_noise_masking.py) into Colab.
Exactly three blank lines separate cells. The first two mount Drive and clone
this branch. This workflow generates the baseline only: fixed speech, phone codec,
noise sweep, ASR fact/word recovery, ESTOI, DNSMOS and diagnostic exports.

Follow [the runbook](docs/COLAB_RUNBOOK.md). Results are saved under
`MyDrive/DataForge/noise_masking/outputs/<run-id>/`. No real results are bundled.

[Branch handoffs](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md) explains how Delivery A/B copies these outputs. The audio/scoring library and corpus also carry the frozen
intervention definitions needed by the separate A/B consumer; this notebook never
runs or selects those interventions. Keep both test branches at compatible scoring
versions when transferring evidence.

Local checks: `python -m unittest discover -s tests -v` after installing
`requirements-colab.txt` and FFmpeg. These are software checks, not measured
Rime experiments or human comprehension results.

Session problems, countermeasures and current evidence are tracked in
[TROUBLESHOOTING.md](TROUBLESHOOTING.md). Cell 10 adds an optional saved-transcript
review and export; it makes no TTS/ASR calls and preserves the original run.
