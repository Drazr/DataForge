# Noise grid v2: baseline and breakpoint decisions

Decision date: 2026-09-10. Status: **core implementation complete and locally
validated; Colab execution pending**. The implementation is on
`codex/noise-grid-v2` at commit `24c5553`; the old retired grid notebook is
not the v2 workflow.

## Objective and prior evidence

Measure where the existing baseline's ASR-based critical-fact recovery deteriorates
as background noise increases, and whether the pattern repeats across recordings.
Use this to choose a subsequent engineering intervention.

The stress baseline `6bd1eb398398af0e` demonstrated recurrent masking. Delivery A/B
finished its development screen and 56 model reviews, with no candidate promoted:
Repeat passed the metric screen but failed the conservative model review.
Evidence is archived on `noise-conditioned-ab` at commit `4ddef62`.
This does not establish that the baseline is a winner or that useful failures are
absent. The baseline remains the reference; no human-comprehension improvement was
validated. No original held-out evaluation is authorized by this protocol.

The archived Qwen judgments marked competing_voice false in 27 of 28 known
competing-speech mixtures. Several repaired clarity labels contradict their notes
or transcripts. Earlier successful records also retain earlier generation settings.
Schema completion and audio-hash integrity do not validate these judgments. Retain
the no-promotion decision and raw evidence, but do not use Qwen as the primary
measurement or gate in v2. Do not relax its old gate retrospectively.

## Frozen reference speech and measurement controls

- Reuse the 14 existing critical-text baseline speech realizations: seven
  development texts with two synthesis replicates per text. The primary endpoint
  has labeled facts only on these texts, so excluding general texts reduces GPU
  scoring without removing an eligible fact observation.
- Preserve Rime Coda / Celeste / English, the producer's sampling settings,
  8 kHz PCMU roundtrip and -26 dBFS active-speech leveling. No new TTS calls are
  planned. Do not send already decoded phone audio through PCMU a second time.
- Verify the producer manifest, synthesis ledger and SHA-256 of every reused
  clean audio file. Missing/corrupt speech is a preflight failure; no silent
  fallback to newly synthesized speech.
- Use baseline delivery only. Clauses, Repeat and Slow belong to the completed A/B
  evidence and are not inputs to this measurement grid.
- Keep the original 9 held-out texts out of synthesis, ASR, model review and charts.
  Reused development texts make this an exploratory extension, not a fresh blind test.
- Keep the producer's pinned `Systran/faster-whisper-small.en` revision
  `d1d751a5f8271d482d14ca55d9e2deeebbae577f`, beam size 5, CPU INT8, and corrected
  fact/time scorer. Rescore all v2 clean and noisy rows on that backend; do not
  mix its scores with the earlier CUDA float16 run. Assert source hashes before
  accepting caches.
- Keep DNSMOS enabled with the producer's pinned ONNX model/revision. Preserve
  its input resampling and score computation. No Qwen or second large model is
  required during the main run.

## Noise panel and reproducible selection

Use the existing MUSAN download. Select four distinct recordings: two speech and
two non-speech environmental noise recordings. Exclude the two recordings used by
the original stress run by hash. Keep each recording separate in outputs; do not
claim specific traffic/machinery labels unless its metadata supports that label.
MUSAN source and attribution: https://www.openslr.org/17/ (CC BY 4.0).

Select before ASR results using seed `20260910`. Enumerate candidates in a stable
relative-path order; exclude corrupt, silent, clipped or duplicate files. Require
enough audio for two non-overlapping windows, each at least as long as the longest
baseline utterance. Record all eligibility checks and rejection reasons. Never
select recordings because they produce a desirable fact-recovery score.

For each recording, deterministically choose two non-overlapping eligible start
offsets and freeze both. Offset A is used for the coarse grid; offset B is reserved
for the bounded stability check. Do not loop short recordings. If the eligible
pool cannot supply the panel, stop before scoring and amend the protocol visibly.
Human listening is optional for diagnosis; automatic/metadata labels must never
set `verified_by_listening=true`.

## SNR and mixing policy v2

Core grid: **+15, +10, +5, 0 and -5 dB**, plus the shared clean reference.
Higher SNR means less noise. Mix noise after the baseline phone roundtrip, as in
the pilot; this models additive noise at the listener, not a live uplink denoiser.

The pilot uses full-recording noise RMS and allows deterministic wrapping.
For v2, use the **actual extracted noise window RMS**, without wrapping. For each
text/replicate/recording/offset, extract a segment matching the baseline duration;
hold its samples and start offset fixed across all SNRs. Scale to the ratio of
active speech RMS to full-window noise RMS. Save the noise gain, both RMS values,
requested SNR, measured SNR, source hash, offset and window length.

Verify measured SNR within 0.1 dB of the requested value. Reject clipping or invalid
RMS; never silently clip, renormalize or change the requested SNR. Save float WAVs.
This calibration is a versioned protocol change: do not pool v2 scores with pilot
scores or reuse pilot noisy caches even where nominal SNR labels match.
If later testing a longer intervention, preserve the baseline-calibrated noise gain
and matching noise prefix for that paired comparison rather than recalibrating it
to the intervention's duration; define that in the later A/B protocol.

## Metrics and breakpoint interpretation

Primary: critical-fact recovery, reporting the seven fact types separately
(name, day, time, date, amount, reference code and negation). Report absolute
recovery and clean-to-noisy change. Attribute noise-induced loss only to a fact
recovered in its matched clean control; flag clean failures separately and retain
them in absolute-recovery reports. General-text fact scores remain missing.

Secondary: WER, aligned ESTOI, and DNSMOS OVRL. DNSMOS is supporting audio-quality
evidence, not a substitute for recovery of names/numbers/negation or a breakpoint
gate. Its documented role is prediction of speech/background/overall quality:
https://www.microsoft.com/en-us/research/academic-program/deep-noise-suppression-challenge-icassp-2023/

Freeze a **90% mean critical-fact-recovery target** for this exploratory engineering
grid before viewing v2 scores. This is a chosen operating target, not a validated
human-understanding or safety threshold. WER and ESTOI stay descriptive; avoid
adding competing absolute WER or DNSMOS pass/fail limits.

For each recording and offset, report adjacent SNR intervals. An observed target
crossing has higher-SNR mean recovery >=0.90 and lower-SNR recovery <0.90. Call it
supported within that recording only when the planned grid is complete and at
least four of seven critical texts cross in both synthesis replicates. Otherwise
report an unsupported/heterogeneous crossing. Separately flag repeatable practical
deterioration: a recovery drop >=0.05 in both repeats of at least four critical
texts, with a mean drop >=0.05. These criteria are explicit pilot choices.

Bootstrap 2,000 times at the text level, keeping synthesis repeats together, for
exploratory 95% intervals on means and paired changes. Do not treat noise offsets
or repeated syntheses as independent texts. Keep recordings separate; a family
summary weights recordings equally and does not imply population generalization
from two recordings. Label nonmonotonic results and incomplete intervals.

Report a bracket such as [0, +5] dB, not an exact breakpoint. If clean or +15 dB
already misses the target, or -5 dB still meets it, report that the onset is not
located in the tested range. A qualifying interval is not guaranteed.

## Bounded refinement and offset check

1. Finish and archive the coarse grid before adding measurements.
2. At most two distinct adjacent intervals receive their 2.5 dB midpoints.
   Rank intervals first by the number of recordings with a supported target
   crossing, then the number with repeatable practical deterioration, then the
   larger mean positive fact-recovery drop, then the higher-SNR endpoint.
   Only intervals meeting either criterion qualify; if none qualify, skip refinement.
   Score a chosen midpoint across all four recordings and all 14 critical-text
   speech realizations.
3. For each recording with a qualifying coarse interval, use its highest-ranked
   interval's two original endpoints at preselected offset B. Score only the
   seven critical texts and their two replicates. This checks offset stability;
   it is not independent held-out confirmation. Preserve disagreements.
4. Do not add more levels or rerun model prompts to obtain a positive result.
   No qualifying breakpoint is a valid completed outcome.

## Compute, persistence and stopping

| Stage | Maximum scored conditions |
| --- | ---: |
| Clean reference: 7 texts x 2 replicates | 14 |
| Coarse noisy grid: 14 x 4 recordings x 5 SNRs | 280 |
| Optional midpoint refinement: 14 x 4 x 2 | 112 |
| Optional offset B check: 14 x 4 x 2 endpoints | 112 |
| Total maximum, including cached clean scores | **518** |

Core total: **294**. Rescore the 14 cached clean audio files with the same
evaluator used for v2 so every core row shares one scorer and configuration.
No billed synthesis, new dataset download or 7B model review is required.

Use one Colab CPU runtime with Faster-Whisper INT8 for mixing/scoring and a
separate CPU notebook for analysis and plotting.
`colab_noise_masking.py` contains the producer setup, freeze, preflight,
core-score and export cells. `colab_grid_analysis.py` consumes its completion
marker and creates a new timestamped analysis. Both use Drive persistence.

Store new runs under `MyDrive/DataForge/noise_grid_v2/outputs/<run-id>/`. Assets stay
in the existing shared `data/` and `models/` folders. Put temporary working audio
on local Colab disk and checkpoint each completed scored row plus hashes to Drive.
Cache identity must include clean-audio hash, noise hash/offset/window, mixing
version, SNR, evaluator revision/settings and scorer version. No recomputation
of verified completed rows after reconnecting. Preflight checks disk and Drive
writes, real ASR/DNSMOS/codec availability and a clean/easy/hard sample set.

Time 12 representative scored conditions, including long critical clips, to
estimate remaining runtime and export that estimate. Do not promise 30 minutes
before measuring. A runtime disconnect pauses the run; it does not change precision,
switch evaluators or authorize extra TTS. Skip optional stages if time is tight
and report their absence. The core result remains useful on its own.

## Implementation and handoff

Implemented on `codex/noise-grid-v2` at `24c5553`, based on the current
Noise-Masking code and corrected scorer. The old analysis was adapted for Python
3.13, the new source/window/calibration schema, DNSMOS support, complete-grid
checks and text-clustered analysis. Local validation passed 62 tests. No old
experiment files are overwritten.

Before scoring, save this protocol, source selection manifest, resolved dependency
and model versions, commit/scorer hashes, full condition count and budget. Export
per-clip/per-fact results, clean failures, measured-SNR grid, interval tables,
offset-stability results, charts and a concise report. Include a chronological
TROUBLESHOOTING.md in the new test branch and retain all amendments.

Only after reviewing these measurements choose a new delivery intervention and
freeze a separate paired A/B protocol. Known mixture SNR does not implement a
live noise detector or routing policy. No new decision about interruption,
reconnection or latency testing is made here.
