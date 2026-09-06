# Colab handoff

Use `colab_noise_ab.py`: copy each numbered `# %%` block into its own code cell.
Exactly three blank lines separate the 15 blocks. Mounting Drive stores results;
cloning Git retrieves the code. They are separate operations in Cell 1.

## Before running

- Use the `codex/noise-conditioned-ab` branch. If it is unavailable remotely,
  upload a ZIP of the source and extract it to `/content/DataForge` before Cell 1.
- Add your own `RIME_API_KEY` in Colab Secrets and enable notebook access.
  Rime billing is separate from ChatGPT Plus. Never paste the key into source.
- Allow the Drive mount. CPU/int8 is the default; configure CUDA/float16 in Cell 3
  only with a compatible GPU runtime. Restart after dependency installation if asked.
- Allow roughly 13 GiB free temporary space for the MUSAN download, plus space
  in Drive for extracted clips, evaluation models, and results.

## Run stages

1. **Cells 1–3:** load code, install dependencies, validate the live Rime catalog,
   select SNR points and review the synthesis character cap. Keep the defaults
   for a first pilot; `[10, 7.5, 5, 2.5, 0]` is an optional finer grid.
2. **Cells 4–6:** enable the automatic MUSAN download or point to an existing
   copy. Listen to and select one competing speaker and one traffic/machinery
   recording. Set their paths, offsets and verification flag. Models download
   automatically and their revisions are recorded.
3. **Cells 7–8:** listen to the preflight speech, confirm voice/facts/completion,
   then run the baseline. Inspect the saved SNR plots and per-fact failure CSV.
   Use the listed audio paths to listen to clean/noisy pairs.
4. **Cell 9:** enter one or two noisy conditions with repeated failures. If none
   qualify, retain the baseline results and stop. Any finer follow-up sweep must
   stay on development texts, use a new recorded configuration, and happen before
   candidate selection. Changing configuration creates a new run and may incur
   new synthesis charges.
5. **Cells 10–12:** run three separate interventions. Use the listening queue to
   review critical texts, fill the human review dictionary, and freeze a candidate.
   If none qualifies, report no winner; do not repeatedly tune to force a pass.
6. **Cells 13–14:** validate the frozen candidate once on held-out texts and
   export results. Listen to the held-out queue and retain notes on facts,
   contradictions and naturalness. The automatic evidence status leaves this
   human review pending. Share the result CSVs and listening notes for review.
7. **Cell 15 (optional):** run a separately billed HTTP streaming probe. Actual
   phone calls require the provider setup in `REAL_PHONE_TESTS.md`.

Resume after a disconnected runtime by rerunning setup with the same code,
configuration, paths and source selections. Saved clips and scores are reused.
Do not run the entire script unattended: it intentionally stops for human inputs.
ASR recovery is a screening proxy; the small pilot cannot establish a universal
noise threshold or prove human comprehension.
