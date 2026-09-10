# Final product submission checklist

## Prepared on final-product

- Backend/frontend from product-foundation, dependency locks and placeholder-only
  `.env.example`.
- Focused `RIME_EVIDENCE.md`, original pasted grid outputs, source hashes and
  derived summary with the zero-supported-breakpoint outcome.
- CPU reproduction code/settings/tests, engineering plan, architecture/setup
  README, ordered development log and demo script.

## Required before calling the submission ready

- [ ] Supply full grid result exports and producer provenance; include selected
      clean/noisy demo audio with source attribution and hashes.
- [ ] Implement and verify the chosen speech-risk and fact-read-back extensions,
      or explicitly narrow the submitted feature claim to the working foundation.
- [ ] Configure server-side Rime and LiveKit credentials locally.
- [ ] Run preflight for the exact final model, voice, endpoint and transport.
- [ ] Complete a real normal session and a deliberate stress/failure session;
      preserve received audio and redacted session evidence.
- [ ] Record actual acceptance counts; no performance estimate is a measured result.
- [ ] Record the 4-5 minute demo and supply a shareable submission link.
- [ ] Check README reproduction steps, links, secret-free environment example,
      third-party attribution and the final Git commit.
- [ ] Submit the repository/branch and demo link before the deadline.

The unchanged foundation's live suite does not validate competing-speech
detection or per-fact read-back. No successful credentialed product run is
currently included. Software regression passes do not satisfy this missing step.

Suggested package: README, RIME_EVIDENCE, engineering/acceptance/validation/demo
documents, focused grid evidence, dependency locks, code, tests, environment
example and demo link. Exclude credentials, downloaded models, full datasets,
local caches and unrelated experimental outcomes.
