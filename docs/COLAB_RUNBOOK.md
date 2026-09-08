# Delivery A/B in Colab

Current input: `MyDrive/DataForge/noise_masking/outputs/6bd1eb398398af0e`.
Cell 4 and Cell 6 are prefilled for this run and `competing_speech_-5dB`.
Use a GPU runtime to match its frozen CUDA/float16 evaluator. Keep Cell 3 as
supplied; restart after installing, then rerun Cells 1–2 and continue at Cell 4.
All existing human-listening flags still require the user's observations.

Use the eleven cells in `colab_noise_ab.py` on `noise-conditioned-ab`.

1. Cells 1–3 mount Drive, clone this branch into `/content/DataForge-delivery`
   and install audio dependencies. Use Python 3.11/3.12/3.13. Restart after
   installation, rerun 1–2, skip Cell 3, and continue at Cell 4.
2. Cell 4 uses the prefilled completed Noise-Masking run. The handoff copies
   tables, manifest, scored JSON rows, clips and cached speech into this
   checkout's `inputs/` and verifies their hashes.
3. Cell 5 reads your `RIME_API_KEY` secret and imports the frozen baseline into
   the separate delivery output folder without new synthesis or transcription.
   Keep original noise datasets and downloaded ASR/DNSMOS models in shared Drive
   at their frozen paths. Configuration/scoring mismatches fail before A/B work.
4. Cell 6 freezes the prefilled `competing_speech_-5dB` condition, supported by
   three texts losing a cleanly recovered fact in every repeat.
5. Cell 7 runs short-clause, targeted repetition and slowdown variants, separately.
   New Rime requests are billed. Identical cached speech is reused.
6. Cell 8: listen to matched development clips and populate `LISTENING_REVIEW`.
   Check all critical texts/conditions, negation, numbers and naturalness.
7. Cell 9 freezes a candidate using the preregistered metric and human checks.
   If none qualifies, stop and report no winner.
8. Cells 10–11 run the frozen baseline/candidate on held-out texts once and export
   comparisons, audio, scores and the listening queue. Review held-out audio.
   Do not tune on held-out results. A failed validation is a valid outcome.

The imported request ledger keeps baseline costs in the cumulative character cap;
resuming must not overwrite subsequent A/B attempts. One writing notebook per cache.
Inputs are immutable copies and outputs are stored under
`MyDrive/DataForge/delivery_ab/outputs/<run-id>/`. Only downloaded datasets/models
remain shared at their original paths. See [branch handoffs](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md).
