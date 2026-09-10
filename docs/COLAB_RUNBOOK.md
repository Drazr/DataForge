# Noise Grid v2 in Colab

Use a GPU runtime for `colab_noise_masking.py`; a T4 is sufficient. Keep the
existing MUSAN copy and source baseline under `MyDrive/DataForge`. The producer
requires baseline run `6bd1eb398398af0e` and its shared synthesis cache.

1. Copy the ten `# %%` cells into a fresh Colab notebook.
2. Run Cells 1–3. If dependency installation asks for a restart, restart and run
   Cells 1–2 again, then continue at Cell 4.
3. Cell 4 verifies the source run, freezes the seven critical development texts,
   two repeats, four noise sources, and SNRs +15/+10/+5/0/-5. It expects 294
   scores and never opens held-out data.
4. Cells 5–6 locate MUSAN and select two speech plus two environmental recordings
   by a seeded rule. Pilot source hashes, short recordings, silent windows,
   clipped windows, and duplicate audio are rejected before scores are viewed.
5. Cell 7 downloads evaluator models and proves that all 14 source syntheses and
   metadata files already exist with matching hashes. It stops before any Rime
   request if the cache is incomplete.
6. Cell 8 scores a 12-row timed preflight and prints a full-run estimate. Share
   that estimate if GPU time is tight. Saved rows are reusable by Cell 9.
7. Cell 9 runs the complete grid. Rerunning it resumes from saved JSON rows.
8. Cell 10 verifies all 294 keys, exports summaries and failure evidence, and
   writes `ready_for_grid.json`.

If the runtime disconnects, reconnect Drive and clone the branch again. Install
dependencies only in a new runtime, then rerun Cells 4–9; completed row files are
read from Drive. Cell 10 can run only after Cell 9 reports all 294 rows.

Generation output is stored at
`MyDrive/DataForge/noise_grid_v2/outputs/<run-id>/`. Do not delete `rows/` while a
run is incomplete. The Rime key remains optional because this workflow refuses
to synthesize; it is accepted only for compatibility with the shared experiment
class.

After Cell 10, open a separate CPU notebook and run the seven cells from
`colab_grid_analysis.py`. See [GRID_ANALYSIS_RUNBOOK.md](GRID_ANALYSIS_RUNBOOK.md).
