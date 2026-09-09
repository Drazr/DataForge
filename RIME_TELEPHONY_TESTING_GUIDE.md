# Rime Telephony & Adverse Audio Testing Guide

## Selected tests only

The Noise-Masking and Delivery A/B pilots completed development evaluation with no A/B candidate promoted. The next test is [Noise grid v2](docs/NOISE_GRID_V2_PROTOCOL.md), which defines expanded noise/SNR coverage, window-based SNR calibration, an exploratory 90% fact-recovery target, and bounded refinement. Its implementation is pending. The pilot controls below describe the earlier workflows; the v2 protocol governs the new experiment. Catalog engineering methods remain undecided.

Use the [implementation roadmap](rime_implementation_roadmap.md), each test branch's README/runbook, and [handoff instructions](https://github.com/Drazr/DataForge/blob/main/docs/BRANCH_HANDOFF.md) for setup and file locations. The [main README](README.md) links both test branches.

## Shared controls

- Freeze the Rime model, voice, language, endpoint, synthesis format, single simulated PCMU 8 kHz codec cycle, evaluator versions, corpus split, repeats and noise manifest.
- Use the bundled synthetic corpus: 20 general and 10 critical-information texts, with fixed development/held-out membership.
- Review the actual noise sources and offsets; do not label arbitrary files as traffic or machinery. The completed stress baseline used competing speech and traffic or machinery, clean plus 0 and -5 dB nominal SNR.
- Preserve active-speech leveling and the shared noise-gain policy. Retain nominal and measured SNR; local noise-window levels can differ.
- Retain per-clip run, text, split, variant, condition and replicate identifiers, configuration manifests, model versions, audio paths and file hashes. Keep variants and splits separate.
- Protect secrets; preserve model downloads and datasets at their original shared Drive paths. Existing scoped runtime preflight checks remain required.

## 1. Noise-Masking Test

**Aim:** identify repeatable loss of words and critical facts caused by the tested noise conditions, relative to matched clean speech.

**Method:** run only the development baseline sweep; score ASR WER, lexical critical-fact recovery and aligned ESTOI, with DNSMOS as supporting quality evidence. Attribute a fact loss to noise only when its clean control recovered it and the noisy loss repeats across the configured repeats. Require at least two qualifying texts before using a condition as an A/B challenge.

**Output:** frozen manifest, baseline scores and summaries, fact-loss diagnostics, clips and synthesis cache. These are the inputs copied by Delivery A/B.

**Interpretation:** this compact grid identifies pilot challenge conditions, not an exact or universal noise threshold. ASR fact matching is a proxy, not proof of human comprehension.

## 2. Noise-Conditioned Delivery A/B

**Aim:** determine whether a controlled delivery change improves critical-fact recovery in demonstrated development failures.

**Method:** import the completed Noise-Masking baseline without new baseline synthesis/ASR; freeze supported challenge conditions. Compare short clauses, targeted reference-code repetition and modest native slowdown one change at a time. Keep model/voice fixed. Review facts, naturalness and clean/noisy controls; apply the existing fact-recovery, WER, duration and DNSMOS guardrails before freezing a candidate.

The current synthetic variant definitions do not require an upstream LLM. ESTOI is not a reliable comparison between differently worded or unaligned variants.

**Validation:** evaluate the frozen candidate on held-out clips once, allowing cache-based resume. Do not tune on held-out outcomes. No qualifying challenge or no winning candidate is a legitimate result; do not force later intervention cells to run.

**Output:** development and held-out comparisons, scored rows/audio, listening queues, frozen selection and evidence status. Human review remains necessary before claiming a validated improvement.

## Not separate experiments in this plan

Telephone-format correctness, DNSMOS quality cross-check and streaming gaps/clipping/completion are not standalone planned tests. Necessary codec/preflight checks and DNSMOS audio-quality guardrails remain embedded in the two selected audio workflows. No DSP comparison, classifier training, live-phone validation or automatic listener-SNR policy is claimed by these notebooks.

## Evidence and submission

Retain producer outputs and consumer copies independently. Run the actual Colab experiments and complete manual listening reviews; local software tests do not supply experimental results. Follow [HACKATHON_GUIDELINES.md](HACKATHON_GUIDELINES.md) for submission requirements, state the simulated-channel and lexical-proxy limitations explicitly, and do not claim a breakpoint from the two-point stress baseline.
