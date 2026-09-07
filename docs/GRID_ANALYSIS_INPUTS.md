# Inputs copied from Noise Masking

Set `SOURCE_RUN_DIR` in `colab_grid_analysis.py` to the completed Noise-Masking
run. Cell 2 copies it into this branch's `inputs/noise_masking/<run-id>/` folder.
It records file hashes and remaps audio paths; the original results remain intact.

- `baseline_results.csv` and `manifest.json`: required per-clip scores and controls.
- `evidence_scope.json`: optional planned-count cross-check.
- `baseline_condition_summary.csv` and `baseline_*.png`: existing grid and plots.
- `baseline_fact_failures.csv`, `noise_failure_evidence.csv`, `clips/`: linked failures/listening.
- `results.csv`: optional later A/B output; select a single split/variant and do
  not concatenate its overlapping baseline rows with `baseline_results.csv`.

Noise Masking produces these at Cell 9 without any A/B selection. No real data
exists to copy until that notebook runs. DNSMOS columns are retained in the copied
source but excluded from this analysis. Keep the same preselected acceptance and
recurrence settings when reporting held-out data. See [the runbook](GRID_ANALYSIS_RUNBOOK.md).
