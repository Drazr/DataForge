# Direct inputs for Grid and Breakpoint Analysis

Files are generated under `/content/drive/MyDrive/DataForge/outputs/<run-id>/`.
Run the noise test first; these outputs are not example measured results shipped
in Git. Analysis needs CPU, pandas/NumPy and plotting libraries, without Rime calls.

| Input | Reuse in the six-stage analysis |
| --- | --- |
| `baseline_results.csv` | Primary per-clip development baseline: WER, fact recovery, ESTOI, DNSMOS SIG/BAK/OVRL, text/clip IDs, repeats, SNR, noise metadata, configuration ID and audio paths. Supports comparability checks, matched adjacent-SNR comparisons and new plots. Available after Cell 9. |
| `results.csv` | Alternative full per-clip table after Cell 15, including all variants and held-out results. Filter by `run_id`, `split` and `variant`; use development only to choose challenges. |
| `manifest.json` + `evidence_scope.json` | Configuration, corpus/split, source hashes/offsets, model versions, leveling/SNR definitions and sample counts for comparability and scope checks. |
| `baseline_condition_summary.csv` + `baseline_*.png` | Ready-made grid means/counts and four curves, reducing Stage 4 work. Summaries alone cannot establish paired deterioration. |
| `baseline_fact_failures.csv` | Per-fact errors with references, transcripts and audio links for diagnosis. Includes clean errors; these are not automatically noise-induced losses. |
| `noise_failure_evidence.csv` | Same fact recovered cleanly and lost in every noisy repeat of a text; linked clean/noisy clips. Helps choose development challenge cases. It is not an adjacent-SNR breakpoint table. |
| `challenge_evidence.csv` + `challenge.json` | Evidence and conditions already selected for A/B work, if Cell 10 ran. Keep this selection separate from new breakpoint conclusions. |
| `clips/`, shared synthesis cache | Audio referenced by the tables for listening. Retain the paths or remap them when copying files. |

Load **either** `baseline_results.csv` **or** the matching baseline subset of
`results.csv`; concatenating both duplicates observations. `dev-baseline.csv`
also overlaps the baseline export. Use `(run_id, text_id, variant, replicate,
condition)` as row keys. Match adjacent SNR levels on text, variant, replicate
and noise source within one run; keep clean rows as a separate reference.

`snr_db` is the nominal full-source calibration. `measured_snr_db` reflects the
noise segment actually mixed with that clip and may differ, especially for
nonstationary competing speech. Preserve both when interpreting a breakpoint.
ESTOI is undefined for the clean reference and is left blank. Fact recovery is
blank for general texts with no labeled facts; do not replace either with zero.

Still needed for Stage 5: verify complete pairs, compute adjacent-SNR differences
and their consistency across texts/repeats, choose any absolute WER/fact-recovery
acceptance limits **before** interpreting pass/fail, and report supported intervals.
The A/B gain/quality guardrails in `experiment.json` are not absolute breakpoint
limits. Without such limits report deterioration, not unacceptable performance.
Repeated conditions are correlated observations, not independent listeners.
