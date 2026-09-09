# Delivery A/B evidence — no winner

## Input

A copied, complete Noise-Masking baseline.
The frozen producer manifest supplies the scoring configuration, corpus, repeats,
noise sources and SNR conditions. This branch imports baseline scores/audio.

## Screening result

Repeat was the sole development metric-screen pass: fact-recovery gain
`+0.08163265`, WER delta `-0.010833`, duration ratio `1.08410`, and DNSMOS OVRL
delta `+0.0275485`. Clauses and Slow failed the frozen metric thresholds.

At the user's request, a Qwen2.5-Omni-7B model review was added as a documented
post-metrics amendment. It covered 56 Baseline/Repeat clips across seven critical
development texts, two replicates, clean audio, and `competing_speech_-5dB`.
All records and their referenced audio hashes passed the archive audit. Repeat
failed both the conservative fact-preservation and quality gates. Model review is
not calibrated human listening, and human review remains pending.

The final outcome is **no winner**. No `selection.json` was created and the held-out
split was not run. The original Noise-Masking baseline therefore remains unchanged.

## Evidence to retain

- The full 142,573,883-byte archive remains external; its SHA-256 is
  `2054a2afdaba34afdf366e69b7103327c836d0ae8320d1bf1ea236298162b281`.
- Compact evidence is committed under `evidence/conditioned_ab/6bd1eb398398af0e/`:
  audit, frozen challenge, development comparisons, review protocol and summary,
  all 56 final judgments, fact details, and referenced-audio SHA-256 values.
- `scripts/audit_conditioned_ab_archive.py` reproduces archive integrity, matrix,
  schema, audio-hash, metric-screen, and model-gate checks.

The small default corpus, selected recordings, ASR proxy and simulated codec
support a pilot only. This branch does not perform real phone-provider validation.
