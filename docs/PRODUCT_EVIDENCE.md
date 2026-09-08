# Product evidence — separate from experimental results

## Status

The product foundation implements guided voice control and its offline checks.
The credentialed end-to-end voice suite has **not been run successfully** in this
checkout: RIME_API_KEY, LIVEKIT_URL, LIVEKIT_API_KEY and LIVEKIT_API_SECRET were
not configured during implementation. No live latency, intelligibility,
comprehension, telephone performance, or robustness improvement is claimed.

The public Rime catalog was checked during implementation and contained the
configured `coda` / `astra` / `eng` combination. Each new live session repeats
catalog validation; this is not equivalent to successfully synthesizing speech.

## Engineering claim to verify

DataForge preserves unfinished appointment details across interruptions and
failures, and confirms only after complete delivery of the required details and
question followed by a fresh explicit affirmative utterance. Its interpretation
contract can later accept an LLM without transferring state-changing authority.

The claim concerns software state and observed audio behavior. A recognized
"yes" can still be wrong because of ASR, another speaker, or misunderstanding.
The product does not prove listener comprehension or speaker identity.

## Frozen acceptance procedure v1

1. Run the offline tests and browser error-path checks; all must pass.
2. Run preflight using the exact final model, speaker, endpoint and transport.
3. Run the normal scenario with cache bypass, then with cache reuse. Required
   details and question must complete; no confirmation occurs before the fresh
   synthetic affirmative reply. Exactly one confirmation event follows. Received
   audio must have non-silent samples. Cache provenance must match each mode.
4. Inject the spoken "repeat the time" fixture during audible output. Require
   100 ms of received quiet within **1500 ms of fixture onset**. This is a
   provisional product engineering bound chosen before measurements, unrelated
   to the unfinished noise experiments. Report the observed value and fixture
   onset definition; do not call it human interruption response time.
5. The interrupted flow must recognize a time-repeat intent and reach a new
   confirmation question while still unconfirmed. Offline tests additionally
   prove old callbacks cannot advance the cancelled turn.
6. Inject a provider failure on the next synthesis, including cache-hit paths.
   Require a recovery state, no confirmation, and the cached Rime disclosure.
   Explicit recovery must play a fresh confirmation question.
7. Interrupt connectivity, explicitly record connection loss through the same
   browser control API, and require recovery with confirmation eligibility
   cleared. This is a combined transport/fault-injection scenario, not a proof
   of a particular network outage-detection time.

Scenarios live in `web/tests-live`. Run from the product root:

```powershell
.venv/Scripts/python.exe -m product.cli live
```

The suite records event JSON and received WebM audio under `evidence/live`,
caller fixtures under `evidence/caller-fixtures`, Playwright JSON results, and
an overall `evidence/live-status.json`. It uses real billed providers once
credentials are configured. Browser-generated microphone input and synthetic
caller speech do not substitute for human listening review.

## Evidence integrity and limitations

- Preserve procedure v1 when recording the first measurements. Changes to the
  bound or scenarios require a new version and explanation, never retroactive
  relabeling of a failed run.
- Include Git commit, dependency locks, provider configuration, catalog hash,
  configured LiveKit project endpoint and actual region when available in the
  final evidence package. Transport is browser WebRTC/Opus, not PCMU telephony.
- Preserve raw received audio alongside events. Sender-side completion is a
  useful control signal, but not proof of audible output at the listener.
- Rime synthesis buffers the complete segment. Cached versus uncached latency
  is separate; no independent repeat is silently replaced in the experiments.
- LiveKit or browser acoustic processing may affect input. Record the browser
  and settings when reproducing; do not compare these observations directly
  against frozen simulated-noise metrics.
- No research result is imported automatically, and no listening-SNR threshold
  or adaptive intervention is inferred. Later validated delivery profiles need
  their own linked evidence and final-product checks.

The Delivery A/B branch owns the experimental `RIME_EVIDENCE.md`. This document
adds product evidence without changing that experiment's claims or gates.
