# Competing-speech grid evidence

This folder contains only the completed grid evidence relevant to the product's
speech-masking and critical-fact motivation.

- `cell6_output.txt`: verbatim user-pasted grid, interval display and report.
- `cell7_output.txt`: verbatim user-pasted supported/repeatable displays and output path.
- `provenance.json`: source hashes, run/session and artifact availability.
- `reported_results.json`: derived values transcribed from displayed output;
  not a replacement for the original analysis_record.json.

The supported table is empty (zero crossings); the repeatable table has 21
metric-interval rows. That count includes ESTOI and WER, not just fact recovery.
There are 82 challenge rows; those are not independent trials or subjects.

`imported/results/` contains the supplied machine-readable reports and CSVs;
`imported/audio/` contains three selected WAVs. `stress_case.json` identifies the
clean/5 dB/−5 dB critical_01 comparison, and `provenance.json` records hashes for
every imported file. The original producer manifest and full 294-clip set were
not supplied. No detector metrics, intervention gains, or human results are invented.
