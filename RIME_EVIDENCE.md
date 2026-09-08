# Delivery A/B evidence — pending execution

## Input

A copied, complete Noise-Masking baseline.
The frozen producer manifest supplies the scoring configuration, corpus, repeats,
noise sources and SNR conditions. This branch imports baseline scores/audio.

## Proposed claim and screening

One delivery intervention improves ASR-based critical-fact recovery under the
selected noisy simulated phone conditions. No measured gain is claimed yet.

Choose one or two development conditions where the same cleanly recovered fact
fails in every noisy repeat on at least two texts. Compare each delivery change
separately. The frozen defaults require at least 0.05 mean fact-recovery gain,
at most 0.02 WER increase, at most 1.5x duration and at most 0.15 DNSMOS OVRL decline.
Human review must approve facts, negation and naturalness before candidate selection.

Run Cells 1–11 of `colab_noise_ab.py`. Freeze the candidate before running held-out
texts and review their audio. No winner or failed validation is a valid result.

## Evidence to retain

- Copied `inputs/noise_masking/<run-id>/` and its `handoff.json`.
- `manifest.json`, `imported_baseline.json`, `evidence_scope.json` and cache ledger.
- Challenge and selection locks; development/held-out comparison CSVs.
- `results.csv`, audio, transcripts, per-fact details and human listening notes.

New output goes to `MyDrive/DataForge/delivery_ab/outputs/<run-id>/`.
The small default corpus, selected recordings, ASR proxy and simulated codec
support a pilot only. This branch does not perform real phone-provider validation.
