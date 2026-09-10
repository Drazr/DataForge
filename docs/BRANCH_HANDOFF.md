# Final product handoff

Build and submit from `final-product`. It starts at `product-foundation`
commit `826a5df`, retaining the entire backend, frontend, dependency locks,
environment example, and software/live test suites.

The Grid v2 source, fixtures, settings, dependencies and regression tests were
copied from `noise-grid-v2` commit `698fb0e`. The copied Colab entry points now
clone `final-product` into separate directories. Scoring and analysis algorithms
and acceptance settings are unchanged. Do not replace cells in the completed
frozen Colab run or rerun its inference for this documentation task.

## Files to use

- `README.md`: setup, architecture, actual provider settings and current status.
- `RIME_EVIDENCE.md`: focused experimental claim and limitations.
- `evidence/noise-grid-v2/`: original pasted outputs and clearly labeled derived summary.
- `docs/ENGINEERING_PLAN.md`: implementation order and integration points.
- `docs/PRODUCT_EVIDENCE.md`: planned product acceptance procedure.
- `docs/PRODUCT_DEMO.md`: four-to-five minute recording script.
- `docs/SUBMISSION_CHECKLIST.md`: artifacts and remaining release work.
- `docs/DEVELOPMENT_LOG.md`: ordered problems, countermeasures and reasons.
- `docs/GRID_REPRODUCTION.md`: source provenance and exact analysis command.

## Remaining evidence transfer

Only pasted Cells 6 and 7 are locally available. The original results folder is:
`/content/drive/MyDrive/DataForge/grid_analysis_v2/outputs/05eca3e90a16aae6/20260910T095801572979Z/results`.

Obtain the full folder, especially `REPORT.md`, `analysis_record.json`,
`breakpoint_intervals.csv`, `selected_observations.csv` and `analysis_grid.csv`.
Obtain the producer manifest/scope, hashes and selected clean/noisy audio for
reproduction and the demo. Keep producer settings and raw metrics intact.
The pasted table omits confidence-interval columns; no interval endpoints were
invented in the derived summary.

All product building and submission documentation now lives on this branch.
Raw experimental assets remain external until supplied. Earlier experimental
branches remain historical records; their outcomes are not promoted into the
final product evidence.
