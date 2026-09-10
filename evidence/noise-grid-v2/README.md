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

Full REPORT.md, analysis_record.json, breakpoint_intervals.csv and raw audio have
not been supplied here. In particular, the displayed ellipses hide the confidence
bounds. No confidence bounds, detector metrics or intervention gains are invented.
The original pastes retain Colab's formatting code as source text only.

Use the original result directory recorded in provenance.json for the transfer.
Preserve these files when importing complete exports into a separately named
subdirectory with their own hashes.
