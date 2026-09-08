# Noise-Masking Test in Colab

Use the ten cells in `colab_noise_masking.py` on `noise-masking-test`.

1. Cells 1–2 mount Drive and clone the branch into `/content/DataForge-noise`.
2. Cell 3 installs dependencies and FFmpeg on Python 3.11/3.12/3.13. Restart
   after installation, rerun Cells 1–2, skip Cell 3, and continue at Cell 4.
3. Cell 4 reads `RIME_API_KEY` from Colab Secrets, checks the voice catalog and
   freezes corpus, SNR and evaluator settings. It currently selects the
   `stress_0_to_minus5` profile and requires a Colab T4 GPU for CUDA/float16 ASR.
   This evaluates 21 development texts × two repeats × five conditions = 210
   scored clips; prior baseline syntheses are reused from the shared cache.
   `standard_10_to_0` remains available as an explicit reproducibility profile.
4. Cells 5–7 download/select MUSAN noise, obtain listening approval, download
   evaluator models and record the run. The optional archive is about 11 GB and
   needs roughly 13 GiB temporary space, plus Drive storage for retained files.
5. Cell 8 exercises one real Rime request, the codec, ASR and DNSMOS. Listen to
   the original and phone-formatted clip before proceeding.
6. Cell 9 runs development baseline only and exports its scores, summaries,
   per-fact failures, clean/noisy recurring-loss evidence and plots.
7. Cell 10 reviews an existing baseline, corrects equivalent numeric time
   formatting in saved fact scores, and downloads a review ZIP. It preserves the
   source and writes derived reports under `outputs/reviews/<run>/time_format_v2`.
   Set `BASELINE_REVIEW_SOURCE` to another completed run when needed. These
   diagnostics are not an A/B handoff; do not import them as a frozen experiment.

For the already completed `1f95820a36625efe` session, paste only the updated
Cell 10 into the existing notebook. No reinstall, synthesis or transcription is
needed. Do not rerun Cells 7–9 merely to apply this review. See
[`TROUBLESHOOTING.md`](../TROUBLESHOOTING.md) for chronological fixes and findings.

Rime usage is billed separately. Synthesis is cached across SNR grids; the ledger
and character cap remain cumulative. Use one writing notebook per cache. Active
speech uses a fixed 20 ms frame gate within 40 dB of peak frame power, not ITU P.56.
Noise gain is fixed across durations; retain nominal and measured SNR when comparing.
Repeated losses require the same fact to recover cleanly and fail in every noisy
repeat. The small default corpus/two recordings support pilot conclusions only.

For the stronger baseline, choose **Runtime → Change runtime type → T4 GPU**
before starting. Then run Cells 1–10 in order. Cell 4 creates a new frozen run;
the shared cache avoids new baseline TTS requests only when the model, voice,
language and sample-rate remain unchanged. Verify Cell 8 playback before Cell 9.
Cell 10 automatically reviews the just-created run. If no condition has two
distinct repeated fact losses, A/B is inapplicable. The completed stress run
qualified `competing_speech_-5dB`, so proceed to A/B. Grid/Breakpoint Analysis
has been retired from the active workflow.

Keep the complete `noise_masking/outputs/<run-id>/` folder and its referenced
synthesis cache. Keep downloaded datasets and evaluator models in shared Drive.
Consumer handoff cells copy tables, metadata and audio into their branch checkouts;
A/B additionally copies baseline JSON rows and cached speech. No new baseline run
is required. See [branch handoffs](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md).
