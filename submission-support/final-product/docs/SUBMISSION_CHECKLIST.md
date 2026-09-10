# Final product submission checklist

## Prepared on final-product

- Backend/frontend from product-foundation, dependency locks and placeholder-only
  `.env.example`.
- Focused `RIME_EVIDENCE.md`, original pasted grid outputs, source hashes and
  derived summary with the zero-supported-breakpoint outcome.
- CPU reproduction code/settings/tests, engineering plan, architecture/setup
  README, ordered development log and demo script.

## Required before calling the submission ready

- [x] Supply full grid analysis exports and three selected clean/noisy demo clips;
      preserve producer hashes and limitations.
- [x] Implement and verify user-triggered risk-aware confirmation and strict
      reference/time read-back; disclose that no automatic detector is installed.
- [ ] Configure server-side Rime and LiveKit credentials locally.
- [ ] Run preflight for the exact final model, voice, endpoint and transport.
- [ ] Complete a real normal session and a deliberate stress/failure session;
      preserve received audio and redacted session evidence.
- [ ] Record actual acceptance counts; no performance estimate is a measured result.
- [ ] Record the 4-5 minute demo and put its public URL and the repository URL
      in the Google Doc linked from `DEMO_LINK.md`.
- [ ] Set the Google Doc, repository and recording permissions as required by
      the event; verify all three while signed out.
- [ ] Check README reproduction steps, links, secret-free environment example,
      third-party attribution and the final Git commit.
- [ ] Submit the repository/branch and demo link before the deadline.

The focused live suite exercises normal confirmation, successful read-back, and
a disclosed injected-risk session that ends unconfirmed after wrong read-back.
No successful credentialed product run is currently included. Software regression
passes do not satisfy this missing step.

Suggested package: README, RIME_EVIDENCE, engineering/acceptance/validation/demo
documents, focused grid evidence, dependency locks, code, tests, environment
example and `DEMO_LINK.md` containing the Google Doc URL. Exclude credentials,
downloaded models, full datasets, local caches and unrelated experimental
outcomes.
