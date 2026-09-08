# Four-to-five minute demo script

Prerequisites: configured local worker and frontend, successful preflight,
reviewed live evidence, and `DATAFORGE_TEST_MODE=1` for the deliberate failure.
Do not record the final demo with missing credentials or a mock provider.

| Time | Show and explain |
|---|---|
| 0:00–0:35 | Introduce the need: receiving and confirming appointment details by voice, with the ability to ask for a detail again. Identify all appointments as synthetic. |
| 0:35–1:35 | Start the real microphone session. Let Rime read the details and question. Give a fresh explicit confirmation and show the outcome. No real booking is changed. |
| 1:35–2:35 | Start a new session. After the question, say "repeat the time." Show the exact requested detail being replayed before a fresh confirmation question. |
| 2:35–3:20 | Use "Demonstrate speech failure" in the diagnostics panel. Show the visible recovery state and cached Rime disclosure. Retry and show the new confirmation question. |
| 3:20–4:10 | Export evidence. Show the separate cached and uncached observations from the successful acceptance run. If no measured run exists, this segment is not ready. |
| 4:10–4:40 | Show active Rime model/voice/endpoint, explain the guided interpreter boundary and later delivery-profile extension. State browser-only and comprehension limitations. |

Keep keys, tokens, `.env`, and unrelated terminal output out of the recording.
Never present automated caller success as a result of the unfinished noise,
delivery A/B, or breakpoint experiments. Those findings will be paired with the
foundation only after their own validation is complete.
