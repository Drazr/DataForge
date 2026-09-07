# Noise-Masking Test in Colab

Use the nine cells in `colab_noise_masking.py` on `noise-masking-test`.

1. Cells 1–2 mount Drive and clone the branch into `/content/DataForge-noise`.
2. Cell 3 installs dependencies and FFmpeg on Python 3.11/3.12. If a restart is
   requested, rerun Cells 1–2 and continue at Cell 4.
3. Cell 4 reads `RIME_API_KEY` from Colab Secrets, checks the voice catalog and
   freezes corpus, SNR and evaluator settings. CPU/int8 is the default.
4. Cells 5–7 download/select MUSAN noise, obtain listening approval, download
   evaluator models and record the run. The optional archive is about 11 GB and
   needs roughly 13 GiB temporary space, plus Drive storage for retained files.
5. Cell 8 exercises one real Rime request, the codec, ASR and DNSMOS. Listen to
   the original and phone-formatted clip before proceeding.
6. Cell 9 runs development baseline only and exports its scores, summaries,
   per-fact failures, clean/noisy recurring-loss evidence and plots.

Rime usage is billed separately. Synthesis is cached across SNR grids; the ledger
and character cap remain cumulative. Use one writing notebook per cache. Active
speech uses a fixed 20 ms frame gate within 40 dB of peak frame power, not ITU P.56.
Noise gain is fixed across durations; retain nominal and measured SNR when comparing.
Repeated losses require the same fact to recover cleanly and fail in every noisy
repeat. The small default corpus/two recordings support pilot conclusions only.

Keep the complete `noise_masking/outputs/<run-id>/` folder and its referenced
synthesis cache. Keep downloaded datasets and evaluator models in shared Drive.
Consumer handoff cells copy tables, metadata and audio into their branch checkouts;
A/B additionally copies baseline JSON rows and cached speech. No new baseline run
is required. See [branch handoffs](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md).
