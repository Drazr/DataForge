# Actual streaming and phone validation

## What can be automated

The included `scripts/stream_probe.py` performs real Rime HTTP streaming requests
with only a Rime key. It measures client chunk timing and saves raw 8 kHz PCMU.
Credentials placed only in Colab Secrets are accessible to the Colab runtime, not
automatically to this local Codex task. Run Cell 15 there or securely configure the
local environment. Do not paste keys into chat.

Real phone tests can also be scripted once an authorized provider account, number,
agent, and reachable service are configured. Account signup/verification, funding,
and answering/listening to calls are the user's steps. Neither credentials nor a
provider/phone number have been supplied for this repository yet.

## Ordered phone procedure

1. Use the provider intended for the product. One supported option is LiveKit Cloud
   with a LiveKit number; another is LiveKit with a third-party SIP number such as
   Twilio. Provision only the number/account resources you authorize and set a test
   spending limit. A browser WebRTC test alone does not validate PSTN delivery.
2. Configure a running agent with the pinned Rime model/voice, secret environment
   variables, correct codec and sample rate. Use the final endpoint and region.
   Register a dispatch rule; third-party inbound calling also needs the inbound SIP
   trunk and provider route to LiveKit. Deploy/run the agent on a reachable host.
3. Start capture/logging. Record provider call ID, LiveKit room/SIP participant ID,
   actual negotiated codec, agent version, Rime configuration and audio capture point.
   A server recording may exclude the handset's acoustic environment; label it.
4. Call your own test number. First verify the baseline response reaches the phone
   completely, then use short/long replies, final-word fixtures, and interruption
   cases. Confirm the expected SIP participant and agent joined the room.
5. Test the selected delivery variant against baseline with the same fixed texts,
   provider route and devices. Repeat calls and alternate their order. Record actual
   network conditions; they cannot be made perfectly constant across separate calls.
   Do not describe uncontrolled room noise as a calibrated SNR experiment.
6. Measure request start, first received audio, first audible playback (if observable),
   final chunk, playback completion, duration, audible gaps, missing final words,
   interruption stop time and hangup. Obtain packet loss/jitter from RTP/WebRTC stats
   when exposed. Keep HTTP chunk timing separate from audible playback timing.
7. Record only your own or consenting testers' synthetic-data calls. Compare saved
   delivered audio and transcripts against each variant's reference and critical
   facts. For listener-side controlled noise, mix noise into the captured output in
   Colab and label that as post-capture simulation, not a naturally noisy call.
8. Export recordings and metadata to Drive. Use the same pinned ASR/fact-scoring
   functions for analysis, label transport `actual_provider_capture`, and retain
   separate result tables from simulated-codec experiments. Do not add DNSMOS/STOI
   across unrelated captures without an appropriate reference/alignment.
9. Report completion rates and failures, inspect provider and agent logs, and verify
   hangup/disconnection cleanup. Do not make final phone-performance claims until
   the actual final path has passed the acceptance test in `RIME_EVIDENCE.md`.

The current repository includes the HTTP probe and this procedure, not a deployed
LiveKit agent or a configured SIP trunk. Provider-specific code follows selection
of the actual product transport and configuration.

References: [LiveKit testing](https://docs.livekit.io/telephony/testing/),
[SIP setup](https://docs.livekit.io/telephony/start/sip-trunk-setup/),
[Rime LiveKit integration](https://docs.rime.ai/docs/livekit).
