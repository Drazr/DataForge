# Grid and breakpoint analysis in Colab

Use `colab_grid_analysis.py`: seven `# %%` cells, separated by exactly three blank
lines, ready to copy into a Colab notebook. Use a Python 3.11/3.12 CPU runtime.
This is analysis of previously measured evidence. It needs no raw datasets,
API keys, synthesis, ASR, DNSMOS, model downloads, or telephony integration.

## Files and manual inputs

1. Use the original run folder from **either Noise Masking or Noise-Conditioned
   Delivery A/B**. In `colab_noise_ab.py`, finish **Cell 9** (baseline and exports);
   analysis can start immediately, even if no challenge or A/B winner exists.
   Required: `baseline_results.csv` and `manifest.json`.
   When present, `evidence_scope.json` is cross-checked. Otherwise planned counts
   are derived from the manifest and that source is recorded in the analysis.
   Retain `baseline_condition_summary.csv` and `baseline_wer.png`,
   `baseline_fact_recovery.png`, `baseline_estoi.png` for existing grid previews.
   Challenge linking also requires `baseline_fact_failures.csv` and
   `noise_failure_evidence.csv`. Missing challenge exports do not stop numerical
   analysis. Keep `clips/` with the referenced clean/noisy audio for optional listening.
   No new dataset, separate baseline run, or intervention output is needed.
2. Open a separate analysis notebook, set `RUN_DIR` in Cell 1 to that same folder,
   and authorize the Drive mount. You do not need to copy the evidence into Git.
3. Clone `codex/grid-breakpoint-analysis` in Cell 2. Local changes must first be
   committed and pushed to make them available on GitHub. Alternatively upload
   an archive of these source files into `/content/DataForge-grid` before Cell 2.
   Private repository authentication, if needed, is handled by the user; do not
   put access tokens into notebook source or remote URLs.
4. Decide absolute WER/fact-recovery limits and their rationale before Cell 5.
   Leave both `None` to report deterioration without declaring unacceptability.
   One limit may be set independently; the unset metric remains descriptive.
   WER is a fraction and can exceed 1; fact recovery is in [0, 1].
   `experiment.json` A/B gain thresholds are not absolute acceptance limits.
5. If audio moved, configure `audio_path_remap` with old and new directory
   prefixes. Original paths remain in outputs alongside resolved paths.

The branch includes `requirements-grid.txt`, `grid_analysis.json`, and the
analysis-only `dataforge/grid_analysis.py`. `dataforge.experiment` is not imported.
The upstream noise/A/B scripts and their DNSMOS behavior are unchanged; DNSMOS
columns and plots are excluded from this new analysis workflow.

## Stages and interpretation

- Cells 1-3: access evidence, load code, install numerical/plotting dependencies.
- Cell 4: snapshot selection, absolute limits, recurrence settings, and audio
  remapping in a timestamped session before reviewing the grid.
- Cell 5: validate IDs, configuration, source hashes/offsets, speech source,
  sample counts, repeats, and planned grid completeness. Reuse the baseline
  summary after matching its conditions, counts, and metrics to selected rows;
  show existing WER/fact-recovery/ESTOI plots only with a matching baseline summary.
- Cell 6: calculate matched adjacent-SNR changes, text-level uncertainty, and
  limit crossings. Reuse verified baseline means/counts in `analysis_grid.csv`,
  adding measured-SNR ranges. A missing/stale summary or a different split/variant
  gets a grid derived from its selected rows. No metric inference is repeated.
- Cell 7: link development challenge candidates to existing fact-loss evidence
  and optionally listen. This does not freeze challenges or run/select a fix.

The manifest defines adjacency, e.g. +10 to +5 and +5 to 0 dB. A missing +5 dB
level never becomes a +10 to 0 comparison. Pair the same text, synthesis repeat,
variant and noise source in one run. Clean phone output is a separate reference.
`snr_db` is nominal calibration; actual `measured_snr_db` is retained in pairs
and summarized in the grid. ESTOI's clean values and general-text fact recovery
remain blank, never zero. Noise sources stay separate even if their kinds match.

For each metric, positive deterioration means lower performance:

- WER: lower-SNR WER minus higher-SNR WER.
- Fact recovery and ESTOI: higher-SNR score minus lower-SNR score.

First average paired deltas across repeats within each text, then average across
texts. Fact recovery is the mean of eligible text recovery fractions, not a pooled
fact count. WER is the mean clip WER with equal text weighting, not corpus WER.
Sample counts distinguish matched observations, eligible texts, and complete texts.
Bootstrap intervals resample text means, retaining repeats together; they are
exploratory 95% intervals conditional on the chosen recordings and small corpus.
They do not establish human comprehension, significance across all comparisons,
or generalization to unseen noises. CIs do not gate the recurrence flags.

Default recurrence rules are explicit pilot choices, not universal thresholds:

- A text consistently deteriorates only if the delta exceeds the configured
  metric minimum in **every** expected repeat (default minimum delta is zero).
- A metric interval is flagged `repeatable_deterioration` only with a complete
  planned pair grid, at least two synthesis repeats, at least two such texts,
  at least 50% of eligible texts, and a mean delta above that same minimum.
- Set minimum deltas before inspection if you need a practical effect-size
  requirement. Zero tests direction only and can flag very small changes.
- `supported_breakpoint` requires an absolute limit, a complete interval, and
  a higher-SNR acceptable / lower-SNR unacceptable mean. That crossing must also
  occur in every repeat for at least two texts and 50% of eligible texts.
  Equality at a limit is acceptable. ESTOI never defines acceptance.
- If the higher SNR is already unacceptable, the table says so; the onset was
  not located within that interval. Nonmonotonic improvement is labeled separately.
- Missing rows are exported and suppress support for the affected intervals.
  Means based on remaining complete texts stay descriptive. No qualifying
  interval or no linked challenge cases is a valid result.

Challenge candidates must also appear in the producer's evidence of the **same
fact** recovered cleanly and lost in every noisy repeat. The worse endpoint of
a primary-metric deterioration or supported crossing supplies candidate conditions.
ESTOI-only changes cannot select challenges. Candidate rows include fact IDs,
transcripts, conflicts, original/resolved audio paths, and supporting intervals.
They require review in the A/B workflow, which retains its own challenge rules.

## Outputs and subsequent runs

Each session is saved to `<run>/grid_analysis/<timestamp>/`. Settings and the
source revision are saved before review; the `results/` subfolder contains:

| File | Contents |
| --- | --- |
| `selected_observations.csv` | Selected input rows with DNSMOS columns removed |
| `analysis_grid.csv` | Reused matching producer means/counts (or selected-row fallback), plus measured SNR ranges |
| `missing_observations.csv` | Expected text/repeat/condition observations absent from input |
| `adjacent_pairs.csv` | Matched endpoint rows, audio paths, controls, and metric deltas |
| `breakpoint_intervals.csv` | Counts, recurrence, text-bootstrap intervals, acceptance status |
| `adjacent_wer.png`, `adjacent_fact_recovery.png`, `adjacent_estoi.png` | New paired-delta plots |
| `development_challenge_cases.csv` | Linked candidates, or a readable empty table |
| `analysis_record.json` | Frozen settings, input/code hashes, scope and grid sources, versions, warnings |
| `REPORT.md` | Evidence status, missing counts, and interpretation limits |

Never concatenate `baseline_results.csv`, `dev_baseline.csv`, and `results.csv`:
their baseline rows overlap. `results.csv` is optional and becomes available after
`colab_noise_ab.py` Cell 15; baseline analysis never waits for it.
To inspect the later intervention/held-out exports, choose `results.csv`
in Cell 4 and explicitly select one `split` and `variant`. The manifest must match
that run. Held-out and nonbaseline analyses export no challenge-selection rows.
Keep original limits and recurrence settings when reporting held-out evidence;
do not retune them to obtain a favorable result. This script does not perform A/B
comparisons or select interventions.

Every execution needs a fresh output folder. Original evidence and existing
analysis folders are never overwritten. Restart from Cell 4 for a new analysis
session; identify any post-review settings changes as exploratory in the rationale.
Post-review limits cannot be described as established-before-review: leave them
unset in this workflow until independently chosen for a new evaluation.

The same analysis can run locally:

```shell
python -m pip install -r requirements-grid.txt
python -m dataforge.grid_analysis --input outputs/RUN_ID --config grid_analysis.json --output outputs/RUN_ID/grid-analysis-001
python -m unittest discover -s tests -p test_grid_analysis.py -v
```

No live results are bundled. Tests construct explicitly synthetic data to check
pairing, missing data, thresholds, repeat clustering, and schema compatibility.
