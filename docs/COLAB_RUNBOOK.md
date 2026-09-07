# Delivery A/B in Colab

Use the eleven cells in `colab_noise_ab.py` on `codex/noise-conditioned-ab`.

1. Cells 1–3 mount Drive, clone this branch into `/content/DataForge-delivery`
   and install audio dependencies. Use Python 3.11/3.12. If restarted, rerun 1–2.
2. Cell 4: set `SOURCE_NOISE_RUN` to the completed Noise-Masking run. The handoff
   copies tables, manifest, scored JSON rows, clips and cached speech into this
   checkout's `inputs/`. Set optional `GRID_RESULTS` to a matching development
   grid result directory to copy its candidate/interval tables too.
3. Cell 5 reads your `RIME_API_KEY` secret and imports the frozen baseline into
   the separate delivery output folder without new synthesis or transcription.
   Keep original noise datasets and downloaded ASR/DNSMOS models in shared Drive
   at their frozen paths. Configuration/scoring mismatches fail before A/B work.
4. Cell 6: review recurrence counts and any grid suggestions; enter one or two
   conditions with at least two texts losing the same cleanly recovered fact
   in every repeat. This freezes conditions; it does not select a delivery change.
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
remain shared at their original paths. See [branch handoffs](BRANCH_HANDOFF.md).
