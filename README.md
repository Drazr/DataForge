# Grid and Breakpoint Analysis

Branch: `codex/grid-breakpoint-analysis`.

Copy the seven cells in [colab_grid_analysis.py](colab_grid_analysis.py) into a CPU
Colab notebook; exactly three blank lines separate cells. Cells 1–2 mount Drive,
clone this branch and copy a completed Noise-Masking run into this checkout's
`inputs/noise_masking/<run-id>/` folder with hashes and audio path remapping.

This branch contains only the analysis notebook, settings, analysis/handoff code,
lightweight dependencies and their tests. It needs no synthesis, ASR or model
inference. The existing analysis excludes DNSMOS from its breakpoint decisions.

See [the runbook](docs/GRID_ANALYSIS_RUNBOOK.md), [input mapping](docs/GRID_ANALYSIS_INPUTS.md)
and [branch handoffs](docs/BRANCH_HANDOFF.md). New analysis results stay in
`MyDrive/DataForge/grid_analysis/outputs/<run-id>/<session>/results/` and can be
copied into the Delivery A/B branch for human challenge review.

Run `python -m unittest discover -s tests -v` after installing
`requirements-grid.txt`. Tests use synthetic fixtures; there are no measured
experiment outputs in this repository yet.
