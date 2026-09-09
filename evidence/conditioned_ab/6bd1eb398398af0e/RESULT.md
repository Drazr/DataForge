# Conditioned delivery A/B result

- Run: `6bd1eb398398af0edcbe31d260e15fa71a6e5aca1c3d9abc117aef7028d71966`
- Frozen challenge: `competing_speech_-5dB`
- Metric screen: Repeat passed; Clauses and Slow failed.
- Delegated review: Qwen2.5-Omni-7B, 4-bit NF4; 56/56 clips completed.
- Review gate: fact preservation failed; quality acceptance failed.
- Decision: **no winner**. Keep the original Noise-Masking baseline.
- Selection and held-out validation: not run because the review gate failed.

`archive_audit.json` records the source ZIP hash and reproducible integrity checks.
`model_review_results.jsonl` retains every final judgment, fact result, and audio
hash without committing the 143 MB source archive or audio files. Human review is
pending; this result is not a calibrated human-comprehension claim.
