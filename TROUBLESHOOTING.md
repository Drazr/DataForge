# Noise-Conditioned A/B development log

Updated 2026-09-08. Development A/B synthesis and metrics have now been reported.
Candidate selection and held-out validation remain pending. Earlier entries below
preserve the status at each stage; the latest development update is at the end.

| Step | Problem | Countermeasure and reason | Status |
| --- | --- | --- | --- |
| 1 | Upstream Colab uses Python 3.13; this branch retained the 3.11/3.12-only guard. | Ported the session's Python 3.13 dependency overrides into A/B Cell 3. | Code updated; A/B runtime not yet exercised. |
| 2 | Upgrading loaded SciPy caused an upstream import error. | Restart after installation, then rerun Cells 1–2 and continue at Cell 4. Use a restarted session when changing branch modules. | Upstream workaround succeeded; documented here. |
| 3 | Upstream had no MUSAN files, then empty selection paths. | Download once and verify selected recordings by metadata/listening. A/B imports the frozen noise paths and models instead of choosing new ones. | User's baseline completed; preserve Drive downloads. |
| 4 | Baseline has 42 syntheses / 294 scores, but only one recurrent text at each of two conditions. | Preserve the two-text-per-condition gate in Cell 6; do not start billed variants. | Original run ineligible. |
| 5 | Truncated tables concealed formatting errors in time facts. | Reviewed the full ZIP; moved the review/export tool to Noise-Masking Cell 10 and removed `colab_baseline_review.py` here. | Complete records received. |
| 6 | `9.20am` and equivalent formats were false failures. | Share the corrected time-fact scorer byte-for-byte with Noise-Masking; wrong numbers/names remain errors. | Code and tests added. |
| 7 | Updated implementation cannot import an old fingerprint as if unchanged. | Keep immutable producer manifests; treat Cell 10's corrected tables as derived diagnostics, not a delivery handoff. | A corrected/new producer run is required before an eventual A/B import. |
| 8 | No human review evidence accompanies a successful metric run automatically. | Retain development listening review and held-out checks; do not mark them completed from transcripts. | Pending; A/B not run. |

Next: use the measured Cell 10 assessment to decide whether a new development
baseline is justified. Do not lower the challenge threshold or inspect held-out
results to manufacture eligibility. This was the status before Grid was retired.

Existing Colab clones retain their old commit until explicitly updated, even
after changes are pushed to GitHub; producer/consumer scoring hashes
must match before handoff.

Measured update: local Cell 10 execution on all 294 saved scores corrected 51
time-format false failures. **Zero recurrent texts remain in every condition**;
A/B cannot proceed under the existing gate. Clean fact recovery is 95.92%, versus
89.80% for competing speech at 0 dB. No A/B requests or held-out scoring were run.
The local A/B suite passed 32 tests, with one Noise-only test skipped. Use a
separately planned development baseline if further A/B work is pursued.

Current decision at that stage: Grid/Breakpoint Analysis was deferred in favor of this A/B
workflow if the next `stress_0_to_minus5` baseline qualifies a challenge. If it
does not qualify, A/B is inapplicable and neither downstream workflow should run.

## Stress baseline accepted for the next A/B run

1. Received the completed `6bd1eb398398af0e` stress baseline: 210 scores,
   CUDA/float16 ASR, two repeats, both noises at 0 and -5 dB.
2. Cell 10 reported **zero corrections**. Competing speech at -5 dB has three
   recurrent texts: `critical_01` (time/date), `critical_03` (code), and
   `critical_05` (time). Clean fact recovery is 95.92%; the challenge is 71.43%.
3. Copied the user's review ZIP into this branch, verifying 70 critical audio
   hashes and all 210 row identities. The complete synthesis cache and remaining
   audio are still in Drive; Cell 4 performs that verified runtime handoff.
4. Prefilled the source run in Cell 4 and challenge in Cell 6. Added a stale
   module check and a GPU availability check so the frozen producer/consumer
   setup is preserved. Cell 3 and the shared scoring implementation are unchanged.
5. The review manifest's implementation hash matches the A/B scorer's Git/LF
   content. No migration is needed because the producer used the corrected scorer.
6. Human baseline listening remains unconfirmed. A/B metrics, candidate selection
   and held-out validation have not run. Grid was deferred at this stage.
7. Validation passed: 33 tests, with one Noise-only check skipped. The new
   evidence regression recomputes all 210 fact scores and confirms the same
   three recurrent texts using the unchanged consumer scorer.
8. Grid/Breakpoint Analysis was retired to prioritize the direct A/B test. Removed
   the unused Grid input from Cells 4–5; this reduces setup without changing the
   frozen baseline, challenge, metrics or held-out rules.

## Development A/B and delegated review

9. Cell 6 confirmed the frozen challenge and recurrent texts `critical_01`,
   `critical_03`, `critical_05`; no new challenge selection was needed.
10. User-reported Cell 7 metrics: Repeat passed the screen (fact gain +0.08163265,
    WER delta -0.010833, duration ratio 1.08410, DNSMOS delta +0.0275485).
    Clauses and Slow failed. Keep these original results; do not tune their gates.
11. Cell 9 raised "No candidate passes the metrics AND listening review" while
    Cell 8's review fields were still false. This was an uncompleted review gate,
    not evidence that every candidate failed the metric screen. Held-out cells
    remain paused until a valid selection exists.
12. The four reviewed clips contained simultaneous voices. This is expected at
    competing speech -5 dB; assess the intended target message. A single four-clip
    review does not cover every critical development text and replicate.
13. User requested delegating the full review to a model. Added a local, free
    Qwen2.5-Omni reviewer with hashes, fixed prompts, raw responses, complete
    coverage checks, and explicit model/human provenance. This is a post-metrics
    protocol amendment. No model output is presented as human listening.
14. Earlier chat incorrectly said DNSMOS was absent. The implemented comparisons
    already include DNSMOS; corrected the documentation instead of duplicating it.
15. Received `development_model_review.zip`: 56 Baseline/Repeat development clips.
    Model download requires network access; used pinned public model/runtime
    downloads and verified model SHA-256 values. No audio is uploaded to a service.
16. The first Colab 7B review loaded successfully, but saving response `0000`
    failed because its nested `responses/` directory had not been created. Updated
    Cell 10's atomic JSON writer to create parent directories and reuse an already
    loaded matching reviewer when the cell is rerun. This avoids another model
    load or download in the same runtime. Hugging Face token, RoPE-key, eager-to-
    SDPA and text-only audio-output warnings observed during loading are nonfatal.
17. All 56 model-review clips then recorded a TypeError before inference because
    `process_mm_info` requires `use_audio_in_video`. Cell 10 now passes `False`
    for the audio-only queue. Reruns retry saved errors, preserving each previous
    failed attempt under `failed_attempts/`, while retaining successful reviews
    and checking cached input/model identity. Rerun Cell 10 in the same runtime;
    keep selection paused until the review completes successfully.
18. Inference returned readable JSON but omitted `clarity` and used boolean
    `artifact` instead of the required string `artifacts`. Keep strict validation:
    do not manufacture missing judgments. Cell 10 now provides field-specific
    feedback and retries malformed output once, saving both raw attempts and
    generation settings. Increased output allowance from 160 to 512 tokens to
    accommodate transcription plus all review fields; this does not guarantee
    schema compliance. Fixed Markdown fence parsing, and stop at the first
    remaining error to avoid spending GPU time on 56 repeated failures.
19. The corrected full-schema retry still omitted `artifacts` on the first clip.
    Cell 10 now performs one focused audio judgment for only the fields missing
    from the second full response, then validates the merged object. It neither
    converts aliases nor supplies default labels. All raw responses and the
    requested field list remain in `generation_attempts`; a malformed focused
    response still stops the run at that clip.
20. The second full response then used `clarity: acceptable`, which belongs to
    the naturalness vocabulary, while its focused response correctly supplied
    `artifacts`. The focused pass now detects invalid values as well as missing
    keys and requests all affected fields together. For this observed response
    it requests `artifacts` and `clarity`; it does not translate `acceptable`
    into `clear` or reuse the earlier boolean `artifact` alias.
21. A new-account resume failed in Cell 5 because `imported_baseline.json`
    contained the SHA-256 of the whole handoff receipt. That receipt includes
    account-specific source paths, so identical verified files could appear to
    be a different baseline. Delivery provenance now hashes the receipt's file
    inventory and run ID. Existing path-sensitive provenance migrates only after
    the current receipt, complete row set, audio hashes and saved baseline rows
    pass their existing checks; actual content changes still fail.
