# Grid and breakpoint analysis runbook

Run `colab_grid_analysis.py` only after producer Cell 10 creates
`ready_for_grid.json`. Use a CPU Colab runtime; the notebook performs no TTS,
ASR, DNSMOS inference, audio decoding, model download, or API request.

1. Cell 1 mounts Drive and chooses the completed v2 producer. Set `READY_RUN_ID`
   only if more than one completed run is present.
2. Cell 2 clones `codex/noise-grid-v2` and records its exact revision.
3. Cell 3 installs NumPy, pandas, and Matplotlib.
4. Cell 4 copies the preregistered settings into a new timestamped session before
   displaying results. The chosen 90% critical-fact target is an engineering
   target, not a human-comprehension or safety threshold.
5. Cell 5 validates the 294-row producer contract and displays the score grid.
6. Cell 6 matches the same text, synthesis repeat, and noise recording at each
   adjacent SNR; it writes the tables, figures, provenance, and report.
7. Cell 7 shows supported breakpoints and repeatable deterioration, then prints
   the persistent output path.

Intervals are +15→+10, +10→+5, +5→0, and 0→-5 dB within each recording. A
missing level never creates a wider substitute comparison. Positive
deterioration means WER rose or fact recovery/ESTOI fell at the lower SNR.
Repeats are averaged within text before text-level aggregation and bootstrap
resampling, so two syntheses do not count as two independent texts.

A deterioration flag needs complete pairs, both repeats, deterioration in every
repeat for at least four of seven critical texts, and the configured mean effect.
A supported fact breakpoint additionally requires the higher-SNR mean to be at
least 0.90 and the lower-SNR mean below 0.90, with that crossing recurring under
the same text/repeat rule. Equality with 0.90 is acceptable. WER has no absolute
limit in this run; ESTOI and DNSMOS cannot define acceptance.

The output is stored under
`MyDrive/DataForge/grid_analysis_v2/outputs/<run-id>/<timestamp>/results/`:

| File | Contents |
| --- | --- |
| `selected_observations.csv` | Validated 294-row input, including DNSMOS support. |
| `analysis_grid.csv` | Condition-level WER, facts, ESTOI, DNSMOS, counts, and measured-SNR ranges. |
| `adjacent_pairs.csv` | Every matched endpoint pair and metric delta. |
| `breakpoint_intervals.csv` | Completeness, recurrence, uncertainty, and breakpoint decisions. |
| `missing_observations.csv` | Missing planned rows; it should be empty for the core run. |
| `adjacent_*.png` | WER, fact-recovery, and ESTOI adjacent-delta figures. |
| `development_challenge_cases.csv` | Fact-level diagnostics linked to qualifying intervals. |
| `analysis_record.json` | Frozen settings, hashes, code revision, versions, and warnings. |
| `REPORT.md` | Result interpretation and limitations. |

No supported breakpoint is a valid outcome. Use the report to decide whether one
extra midpoint or the already-selected second window is worth measuring; do not
change thresholds after seeing the grid and call them preregistered.
