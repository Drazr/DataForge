# Rime Telephony & Adverse Audio Testing Guide

## Selected tests only

The active order is **Noise-Masking Test → Noise-Conditioned Delivery A/B → Grid and Breakpoint Analysis**, in three separate Colab notebooks. This guide supersedes the earlier six-test plan. Catalog engineering methods are outside this scope update and remain unchanged.

Use the [implementation roadmap](rime_implementation_roadmap.md), each test branch's README/runbook, and [handoff instructions](https://github.com/Drazr/DataForge/blob/noise-masking-test/docs/BRANCH_HANDOFF.md) for setup and file locations. The [main README](README.md) links all three test branches.

## Shared controls

- Freeze the Rime model, voice, language, endpoint, synthesis format, single simulated PCMU 8 kHz codec cycle, evaluator versions, corpus split, repeats and noise manifest.
- Use the bundled synthetic corpus: 20 general and 10 critical-information texts, with fixed development/held-out membership.
- Review the actual noise sources and offsets; do not label arbitrary files as traffic or machinery. Start with competing speech and traffic or machinery, clean plus +10, +5 and 0 dB nominal SNR.
- Preserve active-speech leveling and the shared noise-gain policy. Retain nominal and measured SNR; local noise-window levels can differ.
- Retain per-clip run, text, split, variant, condition and replicate identifiers, configuration manifests, model versions, audio paths and file hashes. Keep variants and splits separate.
- Protect secrets; preserve model downloads and datasets at their original shared Drive paths. Existing scoped runtime preflight checks remain required.

## 1. Noise-Masking Test

**Aim:** identify repeatable loss of words and critical facts caused by the tested noise conditions, relative to matched clean speech.

**Method:** run only the development baseline sweep; score ASR WER, lexical critical-fact recovery and aligned ESTOI, with DNSMOS as supporting quality evidence. Attribute a fact loss to noise only when its clean control recovered it and the noisy loss repeats across the configured repeats. Require at least two qualifying texts before using a condition as an A/B challenge.

**Output:** frozen manifest, baseline scores and summaries, fact-loss diagnostics, clips and synthesis cache. These are the inputs copied by Delivery A/B and Grid Analysis.

**Interpretation:** this compact grid identifies pilot challenge conditions, not an exact or universal noise threshold. ASR fact matching is a proxy, not proof of human comprehension.

## 2. Noise-Conditioned Delivery A/B

**Aim:** determine whether a controlled delivery change improves critical-fact recovery in demonstrated development failures.

**Method:** import the completed Noise-Masking baseline without new baseline synthesis/ASR; freeze supported challenge conditions. Compare short clauses, targeted reference-code repetition and modest native slowdown one change at a time. Keep model/voice fixed. Review facts, naturalness and clean/noisy controls; apply the existing fact-recovery, WER, duration and DNSMOS guardrails before freezing a candidate.

The current synthetic variant definitions do not require an upstream LLM. ESTOI is not a reliable comparison between differently worded or unaligned variants. Leave optional Grid inputs unset for the selected order.

**Validation:** evaluate the frozen candidate on held-out clips once, allowing cache-based resume. Do not tune on held-out outcomes. No qualifying challenge or no winning candidate is a legitimate result; do not force later intervention cells to run.

**Output:** development and held-out comparisons, scored rows/audio, listening queues, frozen selection and evidence status. Human review remains necessary before claiming a validated improvement.

## 3. Grid and Breakpoint Analysis

**Aim:** describe how performance deteriorates across tested SNR intervals and whether justified acceptance limits are crossed.

**Method:** after A/B, copy the Noise-Masking baseline for the default analysis. Alternatively copy a completed A/B run and select `results.csv` with exactly one split/variant per session. Check manifests, duplicates, missing observations and matched conditions. Reuse a matching existing baseline grid; compute paired adjacent-SNR deltas with text-clustered uncertainty and recurrence checks. Do not bridge a missing middle SNR.

Use WER, critical-fact recovery and ESTOI; the current analysis excludes DNSMOS. Clean speech is a separate reference. Freeze and record settings before reviewing the grid; disclose if any acceptance limits were informed by earlier Noise-Masking/A/B results. Defaults leave acceptance limits unset and report deterioration only.

**Output:** performance grid, paired comparisons, interval table, plots, analysis record and linked development cases. Report an interval such as “between +5 and 0 dB,” not an exact or general threshold.

Held-out analysis is reporting only. Because A/B precedes this analysis, later challenge listings must not retrospectively change its frozen selection or tune it on held-out results.

## Not separate experiments in this plan

Telephone-format correctness, DNSMOS quality cross-check and streaming gaps/clipping/completion are not standalone planned tests. Necessary codec/preflight checks and DNSMOS audio-quality guardrails remain embedded in the two selected audio workflows. No DSP comparison, classifier training, live-phone validation or automatic listener-SNR policy is claimed by these notebooks.

## Evidence and submission

Retain producer outputs and consumer copies independently. Run the actual Colab experiments and complete manual listening reviews; local software tests do not supply experimental results. Follow [HACKATHON_GUIDELINES.md](HACKATHON_GUIDELINES.md) for submission requirements, and state the simulated-channel and lexical-proxy limitations explicitly.
