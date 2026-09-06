# Rime evidence — pending execution

## Proposed claim

One fixed delivery intervention improves ASR-based critical-fact recovery under
specified noise conditions on a simulated 8 kHz PCMU phone path. The model and
voice are held constant. This is a hypothesis, not a measured result.

## Preregistered pilot acceptance test

Freeze these criteria before development scoring; defaults live in `experiment.json`.

- Demonstrate a baseline failure on at least two development critical texts and
  across both independently requested synthesis replicates in each chosen condition.
- Choose one or two noisy challenge conditions from baseline results only.
- On matched development clips require mean critical-fact recovery gain >=0.05,
  mean WER increase <=0.02, mean duration ratio <=1.5 and mean DNSMOS OVRL decline
  <=0.15. Review per-condition outliers rather than hiding them in overall means.
- Listen to matched development clips and confirm semantic equivalence, preserved
  negation/numbers, and acceptable naturalness. Then freeze exactly one candidate.
- Apply the same numeric criteria once on the held-out set, and manually inspect
  those clips before final acceptance. If it fails, record no validated improvement.
- Real-product acceptance additionally requires complete playback of all selected
  critical facts, no missing final words, and matched baseline/variant recordings
  through the final provider route. Record counts, failures and measured latency;
  choose product-specific latency limits before the phone demo.

## Reproduction

Follow Cells 1–14 in `colab_noise_ab.py` in order. Record the Git revision and retain
the complete fingerprinted run directory under Drive. Optional Cell 15 runs real
HTTP streaming. Locally: `python scripts/stream_probe.py --output outputs/stream-001`.

Configuration: Coda / celeste / en / `https://users.rime.ai/v1/rime-tts`, HTTP WAV
24 kHz -> simulated PCMU 8 kHz. The probe directly requests HTTP `audio/PCMU`, 8 kHz.
No configured real telephony provider/region or phone recording exists yet.

## Results

Status: **not run with Rime credentials or real phone transport**.
Do not populate WER, fact gain, MOS, latency, or success rate until measured.

After execution attach the following from the run directory:

- `manifest.json`, catalog check, Git/package/FFmpeg/model revisions and request ledger.
- `challenge.json`, `selection.json`, `development_comparisons.csv`,
  `heldout_comparison.csv`, `results.csv`, `condition_summary.csv` and plots.
- Saved original/noisy audio pairs, transcripts, per-fact scoring details and human
  listening notes. Mark exact capture point, transport and noise placement.
- Streaming results with cached/uncached distinction and separate real phone results.
- Any exceptions, candidate failure, unsupported language/noise/provider conditions.

## Limits

Thirty original synthetic texts, ten with critical facts, two selected noise files,
two TTS replicates, one voice and one simulated codec do not establish a universal
intelligibility threshold or automatic noise policy. ASR matching is a proxy; it can
miss alternate valid phrasing or accept a correct phrase beside a contradiction.
The held-out set contains only three critical texts. All numeric screening gains
must be interpreted with that limited sample size and verified by listening.
