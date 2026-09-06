# Rime Telephony & Adverse Audio Testing Guide

This guide defines the evidence needed to find and improve Rime output failures in the chosen **Telephony and adverse audio conditions** path. It assumes Rime is already integrated in the product and uses only existing public datasets and generated fixtures—no model training or data collection.

## Test configuration

Record the following value in every result row; change only one in a deliberate A/B test.

| Field | Record |
|---|---|
| Rime configuration | Model ID, speaker, language, API region and endpoint |
| Synthesis path | HTTP/WebSocket/framework integration, format and sample rate |
| Telephony path | Provider, codec, resamplers, normalizers and transport |
| ASR evaluator | Model/version, language and decoding options |
| Evaluation environment | Noise source/file/offset, SNR, gain policy and placement of noise |

For a PCMU phone path, request headerless mu-law at 8 kHz where supported instead of silently double-transcoding. Verify the final provider’s exact payload requirements; for example, Twilio bidirectional Media Streams expect headerless `audio/x-mulaw` at 8 kHz.

## Corpus and controls

- **20 general sentences:** Harvard sentences or a small LibriTTS text subset.
- **10 critical-information utterances:** a small SP-MCQA-Eval subset or documented synthetic fixtures containing names, dates, times, amounts, IDs and negation.
- **Noise:** MUSAN competing speech/babble plus traffic or machinery; save the exact source filenames and start offsets.
- **Split:** reserve 70% of text for development and 30% for held-out validation.

Start with one pinned Rime voice and this compact grid:

| Dimension | Conditions |
|---|---|
| Delivery path | Clean Rime reference; final phone format/path |
| Noise | Babble/competing speech; traffic or machinery |
| SNR | Clean, +10 dB, +5 dB, 0 dB |
| Variant | Baseline plus one changed delivery variant |

Keep speech level, noise segment, clip duration, gain policy and ASR configuration constant within each comparison. Mix noise after the phone-channel simulation if the claim is about listener-side environmental noise, and report that placement.

## Tests

### 1. Telephone-format correctness

**Question:** Does the final codec or transport damage Rime output?

Send fixed clips through the exact telephony path and capture delivery. Check sample rate, mu-law payload format, header removal, duration, clipping, missing tails and transcription.

**Evidence:** WER, duration delta, waveform/level checks and optional PESQ/POLQA.

**Potential fixes:** direct PCMU/8 kHz output, removal of redundant conversion, correct payload framing or codec negotiation.

### 2. Noise-masking sweep

**Question:** Which phone-output conditions lose important speech?

Run the grid on delivered telephone-format output. Calculate WER and separately label each wrong or missing critical fact: name, digit, date, time, amount or negation.

**Evidence:** WER, critical-fact recovery, STOI/ESTOI and saved audio for each failure.

### 3. DNSMOS P.835 quality cross-check

**Question:** Does an output variant improve recognition while harming perceptual quality?

Run DNSMOS P.835 across the same clips and aggregate results by condition and variant.

**Evidence:** SIG, BAK and OVRL. DNSMOS is a quality guardrail, not a root-cause detector or automatic decision rule.

### 4. Grid and breakpoint analysis

**Question:** When does performance become unacceptable?

Plot WER, critical-fact recovery, STOI/ESTOI and DNSMOS by SNR and noise type. Treat only repeatable changes across adjacent conditions as practical breakpoints; use them to select challenge cases for interventions.

Do not train a classifier or claim a general threshold from this compact grid.

### 5. Noise-conditioned delivery A/B

**Question:** Can an AI-controlled delivery change preserve facts in demonstrated failures?

On development failures, compare one change at a time with baseline:

- shorter spoken clauses and punctuation;
- a fact-preserving rewrite that clearly surfaces critical information;
- targeted repetition of one high-value fact;
- a modest native Rime slowdown valid for the pinned model.

Use the upstream LLM to prepare spoken-ready text. Rime prompting guidance applies to the text supplied to TTS; preserve every fact and validate names, numbers and negation before synthesis.

**Evidence:** critical-fact recovery, WER, duration, DNSMOS guardrail, and STOI/ESTOI only when clips remain suitably aligned. Select a candidate on development clips, then validate it once on held-out clips.

### 6. Streaming gaps, clipping and completion

**Question:** Does streaming omit words, introduce gaps or end early?

Exercise short and long replies through the final path. Log synthesis start, first audio, last chunk, playback completion, output duration and ASR transcript. For RTP/WebRTC, record packet loss and jitter when available.

**Evidence:** time to first audio, complete-output rate, missing-tail rate, gap count/duration and WER.

**Potential fixes:** completion-event handling, ordered chunk playback, buffer/chunk tuning or codec configuration.

## Metrics

| Metric | Use it for | Do not use it to claim |
|---|---|---|
| ASR WER | Scalable word-loss screening | Human comprehension alone |
| Critical-fact recovery | Survival of product-important facts | Naturalness or broad quality |
| STOI / ESTOI | Aligned noisy-speech intelligibility comparison | Meaning/pronunciation accuracy or differently rewritten speech |
| PESQ | Legacy intrusive telecom quality comparison | Complete modern TTS or human-comprehension evaluation |
| DNSMOS P.835 | Predicted speech/noise/overall quality | Causal diagnosis or intervention selection |
| Duration / TTFB / gap count | Delivery continuity and speed | Intelligibility alone |

PESQ has been superseded by ITU-T P.863/POLQA in current standards practice. If used, label it as a legacy metric. Report values, deltas and sample counts; aggregate DNSMOS by condition rather than treating one clip as definitive.

## Evidence record

Store one row per clip, condition and variant with:

`clip_id`, `split`, `text_id`, `critical_facts`, `model_id`, `speaker`, `format`, `sample_rate`, `transport`, `noise_file`, `noise_offset_s`, `snr_db`, `variant`, `wer`, `fact_recovery`, `stoi_or_estoi`, `pesq_if_used`, `dnsmos_sig`, `dnsmos_bak`, `dnsmos_ovrl`, `duration_s`, `audio_path`.

Use a result to select a fix only when it repeats on held-out clips and improves critical-fact recovery or WER without an unacceptable duration or quality regression.

## Sources

- [Rime models](https://docs.rime.ai/docs/models)
- [Rime prompting guide](https://docs.rime.ai/docs/prompting)
- [Rime speed controls](https://docs.rime.ai/docs/speed)
- [Rime Coda HTTP API](https://docs.rime.ai/api-reference/coda/http)
- [Rime Coda WebSocket JSON API](https://docs.rime.ai/api-reference/coda/websockets-json)
- [MUSAN](https://arxiv.org/abs/1510.08484)
- [DNSMOS P.835](https://arxiv.org/abs/2110.01763)
- [STOI / ESTOI implementation](https://github.com/mpariente/pystoi)
- [SP-MCQA-Eval](https://huggingface.co/datasets/amphion/SP-MCQA-Eval)
- [LiveKit SIP troubleshooting](https://docs.livekit.io/reference/telephony/troubleshooting/)
