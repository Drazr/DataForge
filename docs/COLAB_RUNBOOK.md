# Colab handoff

Use `colab_noise_ab.py`: copy each numbered `# %%` block into its own code cell.
Exactly three blank lines separate the 16 blocks. Cell 1 mounts Google Drive for
persistent results; Cell 2 clones the branch into `/content/DataForge`.

## Before running

- Use the `codex/noise-conditioned-ab` branch. A fresh Colab runtime clones the
  latest branch code; an existing checkout is kept at its printed commit.
- Add your own `RIME_API_KEY` in Colab Secrets and enable notebook access.
  Rime billing is separate from ChatGPT Plus. Never paste the key into source.
- Allow the Drive mount. Dependency pins target Python 3.11/3.12. CPU/int8 is the
  default; configure CUDA/float16 in Cell 4 only with a compatible GPU runtime.
  Restart after dependency installation if asked.
- Allow roughly 13 GiB free temporary space for the MUSAN download, plus space
  in Drive for extracted clips, evaluation models, and results.
- Run only one writing notebook at a time against a shared synthesis cache.

## Run stages

1. **Cells 1–4:** mount Drive, load the branch, install dependencies, validate the live Rime catalog,
   select SNR points and review the synthesis character cap. Keep the defaults
   for a first pilot; `[10, 7.5, 5, 2.5, 0]` is an optional finer grid.
   If installation needs a restart, rerun Cells 1–2 and continue at Cell 4.
2. **Cells 5–7:** enable the automatic MUSAN download or point to an existing
   copy. Listen to and select one competing speaker and one traffic/machinery
   recording. Set their paths, offsets and verification flag. Models download
   automatically and their revisions are recorded. For broader evidence, use a
   larger pre-split `CORPUS_PATH` in Cell 4 and independent recordings in
   `EXTRA_NOISES` before scoring. Listen to each extra recording and retain metadata.
3. **Cells 8–9:** run the live Rime/codec/ASR/DNSMOS preflight and inspect
   `runtime_preflight.json`. Resolve errors before the batch. Listen to the original
   and phone-formatted speech, confirm voice/facts/completion, then run baseline.
   Inspect the SNR plots, per-fact failure CSV and `noise_failure_evidence.csv`.
   Compare nominal and measured SNR: fixed noise gain permits local fluctuations.
   Use the audio paths to listen to clean/noisy pairs.
4. **Cell 10:** enter one or two noisy conditions with repeated failures. Each
   requires two texts losing the same fact in every repeat, with that fact
   recovered in every matched clean clip. If none
   qualify, retain the baseline results and stop. Any finer follow-up sweep must
   stay on development texts, use a new recorded configuration in Cell 4, and happen
   before candidate selection. A new SNR grid creates new scores while reusing
   compatible speech from the shared synthesis cache.
5. **Cells 11–13:** run three separate interventions. Use the listening queue to
   review critical texts, fill the human review dictionary, and freeze a candidate.
   If none qualifies, report no winner; do not repeatedly tune to force a pass.
6. **Cells 14–15:** validate the frozen candidate once on held-out texts and
   export results. Listen to the held-out queue and retain notes on facts,
   contradictions and naturalness. The automatic evidence status leaves this
   human review pending. Share the result CSVs and listening notes for review.
7. **Cell 16 (optional):** run a separately billed HTTP streaming probe. Actual
   phone calls require the provider setup in `REAL_PHONE_TESTS.md`.

Resume after a disconnected runtime by rerunning setup with the same code,
configuration, paths and source selections. Saved clips and scores are reused.
Model preparation accepts both its requested and locked revision. The shared
request ledger path is recorded in `synthesis_cache.json`; the character cap
includes attempts from other evaluation grids using that cache. An SNR change
does not renew the budget. Preserve the shared cache with the run folders.
Do not run the entire script unattended: it intentionally stops for human inputs.
ASR recovery is a screening proxy; the small pilot cannot establish a universal
noise threshold or prove human comprehension. These fixes have offline regression
coverage; the live Colab preflight and full run still need your credentials.
See `GRID_ANALYSIS_INPUTS.md` for analysis inputs that require no new synthesis.
