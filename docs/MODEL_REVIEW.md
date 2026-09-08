# Local model review of development audio

The primary workflow is now Colab Cells 9–11: Qwen2.5-Omni-7B in 4-bit mode on
a T4 GPU. It runs inside the Colab runtime, uses no API key and makes no paid
inference call. It saves its model responses and report with the A/B run. The
7B model is attempted in 4-bit NF4 mode because its ordinary BF16 memory use is
too high for a T4. If the model cannot load, the notebook explicitly asks for the
3B fallback; it never switches models silently.

The optional Windows runner below uses the smaller Qwen2.5-Omni-3B GGUF model
with llama.cpp b10773. It is retained for an offline reproduction path. Its
weights and runtime binaries are ignored by Git.

The user requested delegating listening to a model **after seeing development
metrics and before held-out evaluation**. This is a protocol amendment, not a
preregistered human review. The model is an auxiliary reviewer, not a calibrated
human comprehension test. Human review remains explicitly pending.

## Colab execution

Run Cells 1–8 as usual, then select a T4 runtime and run Cells 9–11. Cell 9
installs Qwen's required Transformers preview, `accelerate`, `bitsandbytes` and
the audio helper. Cell 10 reviews all critical development Baseline/Repeat clips
in the clean and frozen challenge conditions. It does not provide expected text,
the old ASR transcript, the variant name, or metrics to the model.

Cell 10 writes `model_review_qwen/protocol.json`, `responses/*.json` and
`summary.json` below the delivery run output. It can resume intact response files
only when the audio hash and model identifier match. Cell 11 accepts only a
complete, conservative model pass and labels it `model_review_qwen` in the
selection. Held-out Cells 12–13 remain unavailable if it fails.

Use a fresh Colab runtime after a model out-of-memory error. Change `MODEL_ID`
from 7B to the displayed 3B fallback only after that error. Do not compare models
and select whichever result is favorable.

## Optional offline reproduction

Use a Python environment with the branch's scientific dependencies already
installed. Do not upgrade the Colab scoring environment to install another ASR.

```powershell
python scripts/setup_local_reviewer.py
python scripts/run_local_review.py C:/path/development_model_review.zip --output evidence/model_review/my_run
```

The runner starts a loopback-only server in a hidden process, waits for it to be
ready, reviews the audio, then stops it. The default Vulkan configuration places
12 language-model layers and the projector on the GPU. Runtime logs and settings
are retained. Use `--limit 2` for a smoke test; partial runs cannot pass. Resume
with the same command without `--limit`; cached responses must match the input
hash and protocol fingerprint. Failed responses remain errors rather than being
retried until a favorable answer appears.

On other platforms, obtain the matching official llama.cpp build and start
`llama-server` with the same GGUF files and settings. Then call
`scripts/review_development_audio.py` with `--setup-receipt` and the local
`--endpoint`. The convenience downloader/runner currently targets Windows.

## What is reviewed

- Exactly 56 files: seven critical development texts, Baseline and Repeat, two
  replicates, and clean plus `competing_speech_-5dB`. Missing or held-out rows fail
  validation. The archive is read without extracting untrusted paths.
- Each clip is judged independently. The model does not receive variant labels,
  expected facts, reference transcripts, existing ASR transcripts, or A/B metrics.
  It is told to focus on the appointment/payment/code message and mark unclear
  words rather than fill them in.
- The model produces its own transcript, clarity label, competing-voice flag,
  artifact label, naturalness judgment and notes. The frozen repository fact
  scorer compares that transcript against the expected facts afterward.
- The complete protocol and prompt are saved before inference. Each audio hash,
  model revision/hash, raw response, timing, and scoring decision is retained.

The conservative model gate requires every reviewed Repeat clip to recover all
scored facts and receive acceptable naturalness with no severe/uncertain
artifacts. Errors, incomplete coverage, and uncertainty never count as approval.
This stricter operational interpretation must not be confused with the original
mean fact-gain metric: an intervention may improve that mean yet fail this review.

## Interpreting the result

`summary.json` contains `model_gate_pass`, coverage, group means and a clearly
labeled `listening_review` object. A failed model gate can reflect model
transcription limitations as well as difficult audio; it is not proof that a
human cannot understand the clip. Do not change model, prompts or thresholds to
obtain a pass after inspecting the result.

The model reviewer does not synthesize new clips or access held-out audio. The
Colab workflow records a completed model review as a selection amendment after
the original metric screen; it does not call that review human evidence. A failure
does not authorize held-out Cells 12–13.

DNSMOS **already is part of the existing A/B metric screen**. It is not a new
dependency introduced by this workflow; earlier chat advice saying otherwise was
incorrect.

Model/runtime sources:

- https://huggingface.co/Qwen/Qwen2.5-Omni-3B
- https://huggingface.co/Qwen/Qwen2.5-Omni-7B
- https://huggingface.co/ggml-org/Qwen2.5-Omni-3B-GGUF/tree/75f1b73b657a50f5092502799457ccb4a4a1f9df
- https://github.com/ggml-org/llama.cpp/releases/tag/b10773
- https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md
