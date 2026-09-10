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
- **[RIME_EVIDENCE.md](RIME_EVIDENCE.md):** hard voice claim, acceptance test, exact procedure, results, saved clips/fixtures, limitations and a repeatable command.
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

The final product is a browser voice appointment-confirmation flow built on the
existing product foundation. The engineering direction is suspected competing
speech and critical-fact confirmation, with implementation status tracked in
[the plan](docs/ENGINEERING_PLAN.md).

The submission's experimental evidence is the completed 294-score Noise Grid v2.
It supports repeatable deterioration in competing speech but reports zero
supported breakpoint crossings. Five dB is descriptive of these recordings,
not a validated detector threshold. No automatic detector or read-back benefit
has been measured yet.

Use [the submission checklist](docs/SUBMISSION_CHECKLIST.md). The grid's offline
audio setup is not proof of performance on the final WebRTC transport.

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
