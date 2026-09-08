# Project workflow decision log

Updated 2026-09-08. Test-specific runtime problems and fixes live in each active
test branch's `TROUBLESHOOTING.md`; this file records shared scope decisions.

| Step | Problem or decision | Countermeasure and short reason | Status |
| --- | --- | --- | --- |
| 1 | The initial Noise-Masking baseline contained time-format false failures. | Added explicit AM/PM time normalization and rescored saved transcripts separately, preserving the original run. | Corrected scorer is shared by Noise-Masking and A/B. |
| 2 | The corrected initial baseline had no repeatable masking challenge. | Ran a precommitted stronger baseline at 0 and -5 dB with two repeats. This tested a harder condition without changing held-out data. | Complete run `6bd1eb398398af0e`. |
| 3 | Competing speech at -5 dB produced three qualifying recurrent texts. | Freeze that single condition for Delivery A/B. It satisfies the two-text/two-repeat gate. | A/B input and challenge are prepared. |
| 4 | Limited time required choosing between A/B and Grid/Breakpoint Analysis. | Keep A/B because it directly tests whether a delivery change improves the demonstrated failure; remove Grid from active scope. | Grid branch retired; two-test workflow remains. |
| 5 | Experiment history must remain reviewable after scope changes. | Keep concise chronological logs in both test branches and this shared decision log. | Required for every later problem, fix and result. |

Retiring Grid does not turn the two-point stress sweep into breakpoint evidence.
Claims remain limited to the tested conditions and the simulated 8 kHz PCMU path.
