# Rime Hackathon Guidelines

## Eligibility and product rules

- Rime-generated speech must be the primary, essential spoken output. A product that remains mostly intact without speech is not eligible.
- Use a current Rime model, voice and language combination from the live catalog.
- Keep credentials server-side; never expose them in code, documents, screenshots or recordings.
- Rime must be the default path. Any fallback must be observable and documented.
- The application owns input, ASR, reasoning, state, transport, tools, safety and evaluation; Rime supplies TTS.
- Keep spoken turns concise and use synthetic/de-identified data for sensitive domains.

## What to submit

- **Working repository:** judges may ask for reproduction.
- **README:** setup, architecture, third parties, known limitations, failure behavior, and exact Rime model ID, speaker, language, endpoint, format and transport.
- **[RIME_EVIDENCE.md on noise-conditioned-ab](https://github.com/Drazr/DataForge/blob/noise-conditioned-ab/RIME_EVIDENCE.md):** hard voice claim, acceptance test, exact procedure, results, saved clips/fixtures, limitations and a repeatable command.
- **4–5 minute demo:** user need, normal flow, deliberate stress/failure case, measured result, and active Rime provider.
- **Environment example:** placeholders only; it must pass secret/config preflight.

## Evidence rules

- Define the acceptance test before recording the demo.
- Test the exact endpoint, region, framework, model, audio format and transport used in the final product.
- Measure the user-visible experience, not only a convenient proxy.
- Show a normal interaction and one deliberate stress/failure case.
- For delivery claims, hold model and voice constant, render at least two text variants, save clips and explain the causal change.
- Separate cached and uncached measurements.
- Disclose limitations and unsupported conditions; do not present unverified performance numbers as facts.

## Evaluation focus

| Area | Weight |
|---|---:|
| Problem and necessity of voice | 25% |
| Hard voice engineering | 25% |
| Rime integration and voice experience | 20% |
| Evidence and reproducibility | 20% |
| Demo clarity | 10% |

## Project scope

The selected path is **Telephony and adverse audio conditions**. The active experimental scope is limited to these three workflows, in this execution order:

1. **Noise-Masking Test**.
2. **Noise-Conditioned Delivery A/B**.
3. **Grid and Breakpoint Analysis**.

The [implementation roadmap](rime_implementation_roadmap.md) and [testing guide](RIME_TELEPHONY_TESTING_GUIDE.md) define this plan; this file remains the submission and compliance reference. Standalone telephone-format, DNSMOS cross-check and streaming-continuity experiments are not part of the selected test plan. Necessary codec/preflight checks and DNSMOS quality guardrails remain inside the selected audio workflows.

This test-scope decision does not select, reject or change any catalog engineering method; that topic is unchanged and outside this update.

## Catalog engineering methods

The product foundation selects these low-data-engineering additions:

- disclosed offline/fallback handling;
- lightweight phrase/audio caching.

Integrate only methods used in the working flow, and document their behavior and any effect on evidence measurements.

## Disqualifiers to avoid

- No verifiable Rime integration in code.
- Rime used incidentally rather than as essential output.
- Static or mock-only demo with no working product path.
- Missing demo or reproducibility evidence.
- Exposed secrets.
- A stale or failing model/voice/language configuration at preflight.
