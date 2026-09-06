# Rime Telephony & Adverse Audio Implementation Roadmap

## Goal

Ship a phone-style product where Rime is the essential spoken output, identify an output failure in the final telephony path, and integrate one evidence-backed delivery improvement.

Detailed test protocol, metrics and datasets: [RIME_TELEPHONY_TESTING_GUIDE.md](RIME_TELEPHONY_TESTING_GUIDE.md). Delivery requirements and submission rules: [HACKATHON_GUIDELINES.md](HACKATHON_GUIDELINES.md).

## Phase 1 — Establish the baseline

1. Pin the final Rime model, voice, language, endpoint, transport, audio format and sample rate.
2. Confirm one real phone-path response, then save its configuration and clip.
3. Assemble the fixed corpus, public noise manifest and development/held-out split.
4. Run telephone-format correctness, compact noise grid and streaming-continuity tests.

**Output:** reproducible baseline results and one user-visible failure fixture.

## Phase 2 — Diagnose the failure

1. Review WER, critical-fact recovery, STOI/ESTOI, DNSMOS and continuity results together.
2. Use the compact SNR/noise grid to identify a practical breakpoint and select one or two challenge conditions.
3. Choose one failure that has a direct output-side remedy: codec damage, fact loss in noise, truncation/gaps or excessive pace.

**Output:** a narrow problem statement and a matched baseline test case.

## Phase 3 — Test AI-engineering solutions

1. Build an upstream LLM delivery formatter that preserves facts while producing spoken-ready text.
2. Test one intervention at a time: clause/punctuation changes, clear fact phrasing, targeted critical-detail repetition or conservative native Rime slowdown.
3. Select the candidate on development clips, then validate it once on held-out clips under matched conditions.
4. Keep a solution only when it improves WER or critical-fact recovery without a material quality or duration regression.

**Optional:** compare an existing SSDRC implementation. It is DSP-focused and is not the project’s primary solution. Do not train a noise classifier or build a fully automatic listener-SNR policy in this build.

## Phase 4 — Integrate and prove

1. Integrate the selected delivery policy into the normal Rime-first phone flow.
2. Add catalog engineering only if it strengthens the product: interruptible playback, observable fallback, real telephony turn handling or explicitly labeled caching.
3. Generate evidence artifacts and record the demo.

**Output:** working product, repeatable proof and final demo.

## 24-hour execution order

1. Pin configuration and prove one phone-path clip.
2. Prepare fixtures and scoring harness.
3. Run format correctness, compact noise grid and continuity checks.
4. Identify one failure; run delivery A/B tests.
5. Validate the winner on held-out clips.
6. Integrate it and prepare submission evidence.
