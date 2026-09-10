# Noise Grid v2 analysis inputs

The CPU notebook consumes one completed producer directory:
`MyDrive/DataForge/noise_grid_v2/outputs/<run-id>/`. Cell 1 selects a run only
when it contains `ready_for_grid.json`.

| Input | Purpose |
| --- | --- |
| `ready_for_grid.json` | Completion marker: 294 rows, v2 mixing, seven critical development texts, two repeats, four noises, five SNRs, no held-out access. |
| `manifest.json` | Frozen corpus, evaluator configuration, source hashes, offsets, window rule, SNR definition, and run identity. |
| `baseline_results.csv` | Per-clip WER, critical-fact recovery, ESTOI, DNSMOS, nominal/measured SNR, source hashes, window RMS, gain, and audio paths. |
| `evidence_scope.json` | Planned score counts and development-only scope. |
| `baseline_condition_summary.csv` | Producer means reused only when they match selected rows. |
| `baseline_fact_failures.csv` and `noise_failure_evidence.csv` | Fact-level diagnostic links for candidate cases. They do not define a breakpoint alone. |
| `clips/` | Optional listening material. Numerical analysis does not reopen or rescore audio. |

The key is `(run_id, text_id, variant, replicate, condition)`. The analysis
requires exactly one baseline row for every planned key. It verifies that one
speech realization is reused across clean and noisy conditions, each noise
window stays fixed across SNRs, no noise was looped, and measured SNR is within
0.1 dB of its nominal request.

DNSMOS OVRL remains in the performance grid as supporting quality evidence.
Only WER, fact recovery, and ESTOI receive adjacent-SNR deterioration intervals;
the preregistered 90% fact-recovery limit is the only absolute breakpoint limit.
Do not concatenate this CSV with older baseline or A/B exports.
