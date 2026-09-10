# Noise Grid v2 and Breakpoint Analysis

Branch: `noise-grid-v2`.

This branch measures where the existing Coda baseline begins to lose critical
facts as noise increases. It replaces the earlier two-point masking pilot with a
precommitted five-point grid: **+15, +10, +5, 0 and -5 dB** across two MUSAN
speech recordings and two MUSAN environmental recordings.

The producer uses the seven critical development texts and two already-cached
Rime syntheses per text. Its complete core is **294 scores**: 14 clean controls
plus 280 noisy clips. It does not synthesize new speech and does not access the
held-out split. Each utterance uses an actual non-looping noise window whose RMS
is calibrated separately; nominal and measured SNR are retained. Before scoring,
one global speech level is chosen from an exact peak audit of every planned
speech/noise/SNR combination, preventing clipping without per-clip limiting.

Run the ten cells in [colab_noise_masking.py](colab_noise_masking.py) in a CPU
Colab notebook. Faster-Whisper uses CPU INT8; no GPU quota is required. The
notebook verifies the completed source baseline and its 14 cache files,
selects a deterministic four-recording noise panel, runs a 12-score timed
preflight, checkpoints every result, and exports `ready_for_grid.json` only after
all 294 rows pass the contract.

Then run the seven cells in [colab_grid_analysis.py](colab_grid_analysis.py) in a
separate CPU notebook. It computes matched adjacent-SNR deterioration, clustered
uncertainty across texts, the preregistered 90% critical-fact threshold, and
supporting WER, ESTOI, and DNSMOS summaries. DNSMOS is a quality diagnostic; it
does not define a breakpoint.

Use [the Colab runbook](docs/COLAB_RUNBOOK.md), [analysis runbook](docs/GRID_ANALYSIS_RUNBOOK.md),
and [input contract](docs/GRID_ANALYSIS_INPUTS.md). Problems and countermeasures
are recorded in [TROUBLESHOOTING.md](TROUBLESHOOTING.md) in encounter order.

Local verification:

```shell
python -m pip install -r requirements-colab.txt
python -m unittest discover -s tests -v
```

Tests use synthetic fixtures. No measured experiment result or MUSAN audio is
committed to Git.
