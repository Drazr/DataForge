# Project workflow decision log

Updated 2026-09-10. Test-specific runtime problems and fixes live in each active
test branch's `TROUBLESHOOTING.md`; this file records shared scope decisions.

| Step | Problem or decision | Countermeasure and short reason | Status |
| --- | --- | --- | --- |
| 1 | The initial Noise-Masking baseline contained time-format false failures. | Added explicit AM/PM time normalization and rescored saved transcripts separately, preserving the original run. | Corrected scorer is shared by Noise-Masking and A/B. |
| 2 | The corrected initial baseline had no repeatable masking challenge. | Ran a precommitted stronger baseline at 0 and -5 dB with two repeats. This tested a harder condition without changing held-out data. | Complete run `6bd1eb398398af0e`. |
| 3 | Competing speech at -5 dB produced three qualifying recurrent texts. | Freeze that single condition for Delivery A/B. It satisfies the two-text/two-repeat gate. | A/B input and challenge are prepared. |
| 4 | Limited time required choosing between A/B and Grid/Breakpoint Analysis. | Keep A/B because it directly tests whether a delivery change improves the demonstrated failure; remove Grid from active scope. | Grid branch retired; two-test workflow remains. |
| 5 | Experiment history must remain reviewable after scope changes. | Keep concise chronological logs in both test branches and this shared decision log. | Required for every later problem, fix and result. |
| 6 | Repeat passed development metrics but failed the completed delegated review. | Archive all 56 reviews and preserve no promotion; retain the baseline as a reference rather than declaring it a validated winner. | A/B evidence committed at `4ddef62`; held-out not run. |
| 7 | Prior chat implied no remaining masking weakness and treated model-review completion as decisive quality evidence. | Distinguish observed masking from unsuccessful interventions. Qwen missed competing-voice labels in 27/28 noisy cases; use it only as limited pilot evidence. | V2 uses ASR fact recovery as an explicit proxy, not Qwen judgments. |
| 8 | Two SNR levels and one recording per noise class do not locate a general breakpoint. | Decide a five-level, four-recording grid using 42 cached baseline clips, with bounded midpoint/offset checks. | Core 882 scored conditions; maximum 1,330; implementation pending. |
| 9 | Whole-recording noise RMS and wrapping make nominal SNR harder to interpret. | V2 calibrates actual non-looping noise windows and logs measured SNR; version the change and retain prior measurements separately. | Specified in `docs/NOISE_GRID_V2_PROTOCOL.md`. |
| 10 | Repeated large-model downloads and runtime resets consumed GPU quota. | Reuse shared assets, score with the existing small ASR model, checkpoint per row, and estimate runtime from a timed preflight. | No new TTS or Qwen review planned for v2. |

Retiring Grid does not turn the two-point stress sweep into breakpoint evidence.
Claims remain limited to the tested conditions and the simulated 8 kHz PCMU path.
