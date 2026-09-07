# Baseline review: 1f95820a36625efe

Reviewed the full user-supplied ZIP locally. The original Drive run is unchanged.

- Complete: 21 development texts x two syntheses x seven conditions = 294 scores.
- Original scoring showed one recurrent text at competing speech 0 and 5 dB.
- Numeric time formatting caused false failures, including that recurrent text.
- Corrected 51 false fact failures by treating equivalent explicit AM/PM clock
  formats consistently; incorrect times, names and codes still fail.
- Rescored fact recovery: clean 95.92%; competing speech at 0 dB 89.80%; all other
  noisy conditions 95.92%. WER/ESTOI/DNSMOS are unchanged.
- Zero recurrent texts remain in every condition. No A/B condition qualifies.

The review/export code now lives in **Noise-Masking Cell 10**. Paste that cell
into the existing completed notebook to persist derived review reports in Drive;
no synthesis or ASR is needed. No new ZIP is required for the already completed
local assessment unless your output differs or a new error occurs.

This derived review is not a migrated A/B run. Preserve the two-text recurrence
gate and the held-out split. Further A/B work needs a separately planned
development baseline. See [the chronological log](../TROUBLESHOOTING.md).
