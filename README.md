# DataForge — voice appointment confirmation

A local browser voice product with a guided conversation, Rime speech, explicit confirmation, observable fallback behavior, and verified audio reuse. It uses synthetic appointments only: no real booking is created or changed.

This is the `final-product` branch, based on `product-foundation` commit
`826a5df`. It retains the working voice foundation and adds the completed
competing-speech grid evidence, risk-aware confirmation, and critical-fact read-back.

**Current status:** guided speech, repeat requests, caching, explicit confirmation,
and strict code/time read-back after reported hearing difficulty are implemented.
Automatic competing-speech detection is not installed: risk is triggered by the
user or by a visibly disclosed test-mode injection. The study reported zero
supported breakpoint crossings; 5 dB is an observed aggregate risk region in two
speech recordings. No universal threshold, detector accuracy, human-comprehension,
or mitigation-improvement claim is made.

Start with [engineering methods](docs/ENGINEERING_PLAN.md),
[focused evidence](RIME_EVIDENCE.md), [submission checklist](docs/SUBMISSION_CHECKLIST.md),
and [ordered development log](docs/DEVELOPMENT_LOG.md).
The existing backend/frontend and their dependency locks are all in this branch.
The original Colab outputs, full machine-readable analysis results, and three
hash-verified clean/competing-speech clips are archived in this branch.
[Repository and demo links](DEMO_LINK.md) is the stable handoff to the public
Google Doc containing the repository and final recording URLs.

## Run locally

Requirements: Python 3.12, Node 22.13 or later, pnpm, a Rime API key, and a LiveKit Cloud project with inference enabled. On Windows, install the Microsoft Visual C++ 2015–2022 x64 runtime if necessary. The Codex bundled runtime is detected locally; an alternative directory can be supplied through `DATAFORGE_DLL_DIRECTORY`.

Run commands from this product worktree, not from an experiment checkout:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-product.lock.txt
Copy-Item .env.example .env
```

Fill the four credential fields in `.env` locally. Never put credentials in frontend code or Git. `RIME_SPEAKER=astra` is the default; preflight checks the configured Coda/English voice against the current public catalog. Existing shells need the worker restarted after configuration changes.

```powershell
.venv/Scripts/python.exe -m product.cli preflight
.venv/Scripts/python.exe -m uvicorn product.server:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd web
pnpm install --frozen-lockfile
pnpm dev
```

Open http://127.0.0.1:3000 and select **Start voice session**. Allow microphone access and, if shown, select **Enable speaker audio**. Headphones reduce echo. On macOS/Linux use `.venv/bin/python` in place of `.venv/Scripts/python.exe`.

No hosted deployment or SIP setup is required. The Python service owns the voice workers in the same process; run one Uvicorn process because session state is in memory. Sessions expire after 20 minutes. Up to four active sessions are accepted. Stop both terminal processes to end the local application.

The catalog methods used by the working product are LiveKit turn-taking and
transport, disclosed fallback handling, and content-specific phrase/audio caching.
Risk-aware confirmation and authoritative fact read-back are evidence-motivated
countermeasures. Automatic speech-risk detection is not part of runtime behavior.

## Conversation behavior

The assistant reads the appointment time (including date and timezone), location, and reference code, then asks for confirmation. Supported phrases include:

- “Yes”, “I confirm”, “Yes, that works.”
- “No”, “No thank you”, “I cannot attend.”
- “Repeat that”, “Say that again”, “Repeat the last detail.”
- “Repeat the time”, “Say the reference code again”, “What is the location?”
- “Stop”, “End the session”, “Goodbye.”
- “I hear another voice”, “Too noisy”, “Someone else is speaking.”

Polite prefixes and suffixes are accepted. Mixed, conditional, unsupported, or ambiguous requests trigger clarification. Two unclear replies end the session unconfirmed. These are product defaults, not outcomes of the noise experiments.

After hearing difficulty is reported, a plain “yes” cannot confirm. The caller
must first repeat the full reference code and appointment time. Wrong or partial
values are retried once, then the session ends unconfirmed. Exported events store
match outcomes without retaining the caller's raw fact transcript.

Confirmation requires all required details and the confirmation question to finish playing, then a fresh affirmative utterance. Replies received while the assistant is playing audio are discarded. Playback completion is a sender-side event and is not a claim that someone heard or understood the audio.

## Architecture and extension points

```text
Browser microphone -> LiveKit WebRTC -> Silero VAD + Deepgram Nova-3 STT
  -> IntentInterpreter -> Controller -> DeliveryPlanner
  -> verified PCM cache / Rime Coda -> LiveKit playback -> browser speaker
```

`product/core.py` is provider-independent. `IntentInterpreter` receives finalized text plus read-only context and returns one of confirm/reject/repeat/stop/unclear, with an optional detail identifier. The controller alone changes appointment state. Invalid interpreter output becomes clarification. A future LLM implementation can use that same contract; v1 installs only `guided`, has no application LLM calls, and requires no LLM key. LiveKit's transitive SDK dependencies may include model-client libraries.

`DeliveryPlanner` uses fixed templates with stable fact identifiers. A future validated delivery profile can replace that planner without changing confirmation authority. No experiment caches, results, datasets, or thresholds are loaded by this product.

`product/runtime.py` delivers one segment at a time and owns failure recovery and shutdown. `product/worker.py` binds that runtime to a LiveKit AgentSession with overlapping caller audio disabled. `product/server.py` supplies room-scoped tokens and capability-protected local session controls; there is deliberately no text-confirmation API. `web` is the Sites/Vinext frontend with LiveKit React components.

## Provider and audio configuration

| Setting | Value |
|---|---|
| Primary and only TTS provider | Rime direct plugin |
| Model / default speaker / language | `coda` / `astra` / `eng` |
| Endpoint | `https://users.rime.ai/v1/rime-tts` |
| Synthesis output | mono signed 16-bit PCM, 24,000 Hz |
| Delivery | `time_scale_factor=1.0`, fixed templates `plain-v1` |
| Transport | browser LiveKit WebRTC/Opus; no simulated PCMU conversion |
| Recognition | LiveKit Inference `deepgram/nova-3`, English |
| Turn handling | Silero VAD; caller replies are accepted after assistant playback |
| Browser input | echo cancellation on, noise suppression and automatic gain off |

LiveKit region depends on the configured project and network placement. Session evidence records the configured URL/region metadata when available; do not claim a fixed region from browser tests. Revalidate the exact deployment configuration before the final demo.

Rime audio is buffered to completion before playback so only complete output enters the cache. This adds initial latency; v1 makes no streaming-latency claim. The cache key includes exact text and every configured synthesis setting. Corrupt/incomplete entries are misses. Independent experiment repeats are never replaced by product cache reuse.

## Failure behavior and local storage

- **Rime failure:** one synthesis attempt; enter recovery. Use a previously generated Rime status phrase if available, visibly labeled through failure state and exported provenance. No silent provider substitution or hidden paid retry.
- **Recognition failure:** leave unconfirmed; end and start a fresh session to recreate the STT stream.
- **Connection loss:** clear confirmation eligibility and require the full details plus a new confirmation prompt after explicit recovery.
- **Failure after confirmation:** preserve the already recorded acknowledgment and report the later failure; do not invent a second outcome.

Recovery is limited, not full offline operation. The worker keeps state/events in memory. Synthetic PCM cache entries are ignored under `.product-cache`. Evidence is written only by explicit export or verification commands; `.env`, caches, recordings, and local test outputs are ignored by Git.

In the expanded connection panel, export the session JSON. CLI alternative:

```powershell
# Set DATAFORGE_SESSION_CAPABILITY locally, then:
.venv/Scripts/python.exe -m product.cli export --session SESSION_ID --output evidence/session.json
```

The exported artifact contains configuration, catalog hash, state transitions, and audio cache provenance; it contains no API keys or room tokens. Live verification additionally captures received browser audio. Do not share private credentials or substitute real appointment data into evidence fixtures.

## Verification

Offline software verification:

```powershell
.venv/Scripts/python.exe -m product.cli test
cd web
pnpm exec playwright install chromium
pnpm exec playwright test --config playwright.config.ts
pnpm exec tsc --noEmit
pnpm build
```

The browser suite mocks only configuration/setup error responses and labels itself as software verification. It does not prove live voice performance.

For unattended real voice verification, install Chromium first, configure credentials, and stop an already-running backend unless it was started with `DATAFORGE_TEST_MODE=1`. Then run from the product root:

```powershell
.venv/Scripts/python.exe -m product.cli live
```

This generates synthetic Rime caller WAV fixtures, starts/reuses the local services, injects fixture audio into a real browser microphone stream, runs the real VAD/STT/TTS path, and saves reports plus received audio under `evidence/`. It uses billed Rime/LiveKit calls. Missing credentials produce `unverified` and a nonzero exit, never a pass. If reusing services, the backend must have test mode enabled. Failure injection is disabled by default in ordinary use.

See [product evidence and frozen acceptance procedures](docs/PRODUCT_EVIDENCE.md) and [demo script](docs/PRODUCT_DEMO.md). Report final-product measurements separately from offline grid metrics. The saved grid's acceptance criteria remain unchanged.
