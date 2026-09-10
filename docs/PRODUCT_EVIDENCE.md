# Product evidence: competing speech and critical facts

The submission evidence entry point is [RIME_EVIDENCE.md](../RIME_EVIDENCE.md).
The only imported experimental results in this branch concern the completed
Noise Grid v2 and its paired analysis.

## Current status

The inherited foundation provides guided Rime speech, sequential playback,
requested-detail replay, explicit confirmation, verified audio caching, and
visible recovery. Its offline tests are software verification. A successful
credentialed voice run has not been supplied for this final product.

Competing-speech detection, risk-aware confirmation and fact read-back are
planned extensions in [ENGINEERING_PLAN.md](ENGINEERING_PLAN.md). They have no
measured accuracy or mitigation benefit yet. Existing VAD detects speech activity;
it is not a multi-speaker detector. The existing generic affirmative gate does
not verify that a particular person heard each fact correctly.

## Evidence boundary

The grid used seven development texts, two syntheses, four noise recordings and
five SNR levels plus clean: 294 scored observations. The analysis reported zero
supported breakpoint crossings. Repeatable deterioration occurred for both
competing-speech recordings between 0 and -5 dB.

A product may use these failures to motivate a design. It may not claim that
5 dB is a validated runtime trigger, that a local microphone measures the
listener's SNR, or that confirmation has already solved the masking problem.
The live product uses WebRTC/Opus; the study's frozen audio/evaluator pipeline
must be described separately. No held-out or human-comprehension claim is made.

## Planned acceptance procedure: speech-and-facts-v1

Freeze the implementation, detector/version/settings, fixture identities and
acceptance criteria before collecting product results. Never overwrite the
original grid or lower its recurrence criteria.

1. Run the inherited offline suite and preflight using the exact final provider
   configuration. Record commit, catalog hash, browser, transport and settings.
2. Verify the normal live flow: Rime speaks the authoritative synthetic facts;
   playback completes; a fresh intended reply confirms exactly once.
3. Once implemented, verify the fact read-back extension: a wrong, partial or
   contradictory code/time leaves the session unconfirmed. Replay the named
   authoritative detail and require a new response. No guessed slot is accepted.
4. Once implemented, use labeled clean, environmental-noise, single-speaker and
   competing-speaker incoming clips to evaluate the actual detector. Report
   false alarms, missed cases and unknown outputs. VAD or a generic ASR
   confidence value alone is not ground truth for competing speech.
5. Verify that suspected/unknown speech input cannot authorize confirmation
   until the designed recovery/read-back path is completed. Manually injected
   risk events verify controller behavior only; label them as injections.
6. Run paired baseline and mitigation sessions on the same frozen stress
   fixtures, with target facts and intended speaker annotated. Report incorrect
   confirmations, successful fact checks and unresolved sessions with counts.
   Withhold any improvement claim until measured. Retrying or failing to confirm
   must not be counted as comprehension success.

Keep cached and uncached observations separate. Export received audio alongside
events; sender completion alone is insufficient. Existing failure scenarios in
the inherited live suite remain available as regression checks, but do not
test the new detector or fact read-back.

Run the existing foundation suite with `python -m product.cli live` only after
credentials and services are configured. It uses billed providers and does not
implement the six-step extension procedure above.
