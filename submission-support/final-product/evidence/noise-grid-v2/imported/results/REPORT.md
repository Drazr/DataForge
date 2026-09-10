# Grid and breakpoint analysis

Only metrics with configured acceptance limits can identify unacceptable performance.

Selected 294 rows; 0 expected rows missing.
Performance grid: baseline_condition_summary.csv. Scope: evidence_scope.json.
Supported metric/interval crossings: 0.
Development challenge rows: 82.

See breakpoint_intervals.csv for matched counts, nominal/measured SNR, recurrence, and uncertainty.
No supported interval means the present grid supplies insufficient crossing evidence; it does not prove all conditions acceptable.
Challenge rows are candidates for the separate A/B workflow; no challenge.json was written.

- Pilot evidence; no universal threshold or classifier
- WER and fact recovery are ASR proxies, not measured human comprehension
- SNR intervals use nominal calibration; inspect measured SNR differences
- Bootstrap resamples texts, not repeats; small-sample intervals are exploratory
- No multiplicity correction; recurrence settings are pilot choices, not statistical guarantees
- DNSMOS is supporting quality evidence and does not define a breakpoint
