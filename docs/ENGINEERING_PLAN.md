# Engineering plan: competing speech and critical facts

## Evidence-led boundary

The grid found repeatable fact deterioration from 0 to -5 dB for both speech
recordings, but zero supported breakpoint crossings. Both 5 dB means were below
the 90% target; crossings were not recurrent enough. Treat this as design
motivation, not a calibrated detector or proof that a mitigation works.

Noise was mixed into the offline listening signal. A browser microphone sees
incoming audio, which can differ from the sound at the listener's ears.
The implementation must state which stream it observes. Never infer the
listener's SNR from server output, caller VAD or aggregate experiment scores.

## Existing implementation to retain

| Area | Current behavior |
| --- | --- |
| Rime + LiveKit | Essential Rime Coda output through a browser WebRTC session; VAD and STT provide incoming text. |
| Authoritative facts | Fixed synthetic appointment object and DeliveryPlanner templates; interpreter cannot rewrite facts. |
| Sequential confirmation | Complete playback and a fresh affirmative utterance are required; early replies are ignored. |
| Targeted replay | Named time, location or reference detail can be repeated after the question. |
| Cache | Complete PCM is keyed by text and synthesis settings, with hash checks and visible provenance. |
| Recovery | Failed sessions stay unconfirmed; cached Rime disclosure is observable when available. |
| Evidence | Session configuration/events and live received audio can be exported. |

These are inherited capabilities, not results of the grid. The generic yes/no
gate does not verify speaker identity or understanding of individual facts.

## Implementation order

1. **Speech-risk contract.** Add a provider-independent observation containing
   stream, timestamps/turn, source, detector version, score and one of
   clear/suspected/unknown. Distinguish user-reported difficulty, injected demo
   events and model detections. Missing/stale information must not be labeled
   clear. A detector is not selected or installed by this documentation change.
2. **Risk-aware confirmation.** Before intent interpretation can authorize an
   outcome, check the observation for that input turn. Suspected/unknown input
   requires clarification or read-back; it cannot directly confirm. Ignore stale
   callbacks and require a fresh response after recovery. Treat unconfirmed
   outcomes as unresolved, not successful comprehension.
3. **Critical-fact read-back.** Ask for one authoritative code or appointment time
   at a time. Match permitted equivalent representations against the fixed
   appointment. Wrong, contradictory or missing values remain unconfirmed;
   never allow an LLM to invent or replace a fact. This checks content, not identity.
4. **Targeted replay and bounded recovery.** Reuse the existing planner/cache for
   the affected detail. Ask the user to move to quieter surroundings if needed.
   After bounded failed attempts, visibly end unconfirmed with the authoritative
   details available on screen. Record unresolved sessions explicitly.
5. **Detector integration and user feedback.** Add an actual incoming-audio
   overlap/competing-speech detector only after verifying its model interface,
   license, runtime cost and labeled performance. VAD and STT confidence are
   auxiliary signals, not proof of multiple voices. Without that integration,
   ship only an explicitly user-triggered difficulty flow and disclose the scope.
6. **Paired product verification.** Freeze normal/stress fixtures and procedure
   before measurements. Check false confirmations, correct fact matches,
   unresolved sessions and detector errors on the final transport. Show a
   measured normal flow and a disclosed stress case in the submission.

## Integration map

- `product/worker.py`: observe incoming audio/transcripts and deliver timestamped
  risk observations; retain final-provider metadata.
- `product/runtime.py`: pass observations, coordinate replay and invalidate old turns.
- `product/core.py`: retain exclusive state authority; extend Context/Controller
  with risk and per-fact verification state; extend GuidedInterpreter only for
  bounded read-back parsing.
- `product/server.py`: export public risk/fact state and redacted evidence.
- `web/lib/product.ts`, `web/app/page.tsx`: expose the corresponding status and
  user difficulty/repeat controls. UI displays observations; it cannot authorize confirmation.
- `tests_product/`: verify controller/runtime cases; `web/tests-live/`: add
  real speech-risk and fact-read-back scenarios without relabeling old tests.

Graft dependency tracing confirmed Controller is consumed by the worker and
controller/runtime/SDK/server tests. The new risk/fact state also crosses the
snapshot/API/frontend boundary. Trace exact touched functions again at implementation.

## Submission priority

Implement the bounded confirmation/read-back state first, then integrate and
validate the detector if time permits. Do not present planned detection as
working or use a hidden injected score. Keep current Rime voice/delivery fixed.
No new conditioned A/B, universal 5 dB trigger, denoising benefit or automatic
speech-rate optimization is claimed by this plan.
