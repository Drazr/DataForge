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

## Evidence transfer status

The full supplied analysis folder and three selected clean/noisy WAVs are under
`evidence/noise-grid-v2/imported/`, with hashes recorded in `provenance.json`.
The original producer manifest and complete 294-clip audio set remain external;
the saved analysis record preserves their hashes and source paths.

All product building and submission documentation now lives on this branch.
Earlier experimental branches remain historical records; unrelated outcomes are
not promoted into the final product evidence.
