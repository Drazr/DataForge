# Noise-Conditioned A/B development log

Updated 2026-09-08. A/B synthesis has not started. This log records inherited
setup fixes and the baseline issues that currently prevent this test.

| Step | Problem | Countermeasure and reason | Status |
| --- | --- | --- | --- |
| 1 | Upstream Colab uses Python 3.13; this branch retained the 3.11/3.12-only guard. | Ported the session's Python 3.13 dependency overrides into A/B Cell 3. | Code updated; A/B runtime not yet exercised. |
| 2 | Upgrading loaded SciPy caused an upstream import error. | Restart after installation, then rerun Cells 1–2 and continue at Cell 4. Use a restarted session when changing branch modules. | Upstream workaround succeeded; documented here. |
| 3 | Upstream had no MUSAN files, then empty selection paths. | Download once and verify selected recordings by metadata/listening. A/B imports the frozen noise paths and models instead of choosing new ones. | User's baseline completed; preserve Drive downloads. |
| 4 | Baseline has 42 syntheses / 294 scores, but only one recurrent text at each of two conditions. | Preserve the two-text-per-condition gate in Cell 6; do not start billed variants. | Original run ineligible. |
| 5 | Truncated tables concealed formatting errors in time facts. | Reviewed the full ZIP; moved the review/export tool to Noise-Masking Cell 10 and removed `colab_baseline_review.py` here. | Complete records received. |
| 6 | `9.20am` and equivalent formats were false failures. | Share the corrected time-fact scorer byte-for-byte with Noise-Masking; wrong numbers/names remain errors. | Code and tests added. |
| 7 | Updated implementation cannot import an old fingerprint as if unchanged. | Keep immutable producer manifests; treat Cell 10's corrected tables as derived diagnostics, not a delivery handoff. | A corrected/new producer run is required before an eventual A/B import. |
| 8 | No human review evidence accompanies a successful metric run automatically. | Retain development listening review and held-out checks; do not mark them completed from transcripts. | Pending; A/B not run. |

Next: use the measured Cell 10 assessment to decide whether a new development
baseline is justified. Do not lower the challenge threshold or inspect held-out
results to manufacture eligibility. Grid analysis remains the final workflow.

Existing Colab clones retain their old commit until explicitly updated, even
after changes are pushed to GitHub; producer/consumer scoring hashes
must match before handoff.

Measured update: local Cell 10 execution on all 294 saved scores corrected 51
time-format false failures. **Zero recurrent texts remain in every condition**;
A/B cannot proceed under the existing gate. Clean fact recovery is 95.92%, versus
89.80% for competing speech at 0 dB. No A/B requests or held-out scoring were run.
The local A/B suite passed 32 tests, with one Noise-only test skipped. Use a
separately planned development baseline if further A/B work is pursued.

Current decision: Grid/Breakpoint Analysis is deferred in favor of this A/B
workflow if the next `stress_0_to_minus5` baseline qualifies a challenge. If it
does not qualify, A/B is inapplicable and neither downstream workflow should run.
