# DataForge: noise-conditioned delivery A/B

Reproducible pilot for testing whether a small delivery change preserves critical
facts in noisy, telephone-format Rime speech. The implementation is an evaluation
harness, not a deployed telephone agent. No measured improvement is claimed yet.

## Start in Colab

1. Open a new Colab notebook. Add `RIME_API_KEY` under the left sidebar's key icon,
   enable notebook access, and keep the key out of notebook source/output.
2. Open [`colab_noise_ab.py`](colab_noise_ab.py). Copy each `# %%` section into its
   own cell. There are **15 cells separated by exactly three blank lines**.
3. Run in order. Cell 1 mounts Drive and clones `codex/noise-conditioned-ab`.
   The branch must be pushed to GitHub for cloning. Alternatively upload this
   workspace as a ZIP, extract it into `/content/DataForge`, and rerun Cell 1.
4. Cell 4 can download the official MUSAN archive (~11 GB network and temporary
   disk). It retains environmental clips, four competing-speech clips and source
   metadata. Existing MUSAN files work too. Audio/models/results stay outside Git.
5. Choose one traffic/machinery noise file and one competing-speaker file, listen,
   and verify their labels in Cells 5–6. One speaker is not a babble mixture.
6. Listen to one Rime preflight clip, then run the development baseline. Select
   repeatable failure conditions, evaluate three variants, listen to matched pairs,
   and freeze a candidate before running the held-out cells.

The notebook deliberately pauses for source labels, the first audio check,
challenge selection, and human listening review. If no condition fails repeatedly
or no candidate qualifies, report that outcome. It is not an instruction to keep
tuning until a positive result appears.

## What is included

- `colab_noise_ab.py`: setup, downloads, inference, A/B scoring, plots, and export.
- `dataforge/experiment.py`: matched mixtures, synthesis cache, HTTP timing,
  ASR scoring, fact matching, DNSMOS P.835 and frozen candidate selection.
- `dataforge/downloads.py`: safe MUSAN extraction and immutable model revisions.
- `fixtures/corpus.json`: 20 general and 10 critical-information **original synthetic
  fixtures**; 14+7 development and 6+3 held-out. These are not Harvard, LibriTTS or
  SP-MCQA examples. Every critical fixture contains a name, day, time, date, amount,
  reference code and negation. Read all variants for semantic equivalence.
- `scripts/stream_probe.py`: actual uncached Rime HTTP PCMU requests and timing logs.
- `docs/REAL_PHONE_TESTS.md`: provider setup, capture and validation procedure.
- `RIME_EVIDENCE.md`: acceptance criteria and pending-result record.

The pilot uses original text to avoid making a large speech-corpus download a
prerequisite. The previously suggested SP-MCQA-Eval repository did not expose usable
data files at inspection time. A licensed benchmark text subset may be substituted
**before** running development; change the corpus source field and retain the split.
The curated short-clause/repetition variants are deterministic, auditable fixtures.
An online LLM delivery formatter is a later product integration, not part of this
pilot's runtime dependencies.

## Pinned defaults and workflow

`experiment.json` selects Coda (`coda`), `celeste`, English (`en`),
`https://users.rime.ai/v1/rime-tts`, HTTP WAV / 24 kHz. The live catalog must confirm
this combination. Region is recorded as the configured endpoint; verify actual
deployment geography before making regional latency claims.

Audio path: Rime WAV -> FFmpeg single 8 kHz G.711 mu-law encode/decode -> speech RMS
leveling to -26 dBFS -> listener-side noise at +10/+5/0 dB SNR -> saved float WAV.
This is a **simulated codec path**, not a recording from a phone provider. A clean
condition retains the same codec path with no added noise. Original Rime WAVs are
also saved. The streaming probe requests direct headerless `audio/PCMU` at 8 kHz.

Interventions are short fact clauses (`clauses`), targeted code repetition
(`repeat`), and `timeScaleFactor=1.1` (`slow`). Every variant changes only one of
these strategies, with the Rime model and voice held constant. General texts remain
unchanged for the first two interventions as negative controls.

Two independently requested syntheses per text/variant help reveal TTS variability.
Identical payloads share cache entries within the same replicate, which means
unchanged controls do not incur extra synthesis calls. Job order uses a fixed seed.
There is no Rime synthesis seed guarantee; saved audio hashes are the reproducible
reference. Re-generating later can differ even with the same model ID.

At defaults: development baseline has 294 evaluated clips; three development
variants add 882; held-out baseline/candidate add 252. CPU ASR can take substantial
time. CPU `int8` is the portable default; a suitable Colab GPU can use CUDA/float16
when its CUDA/cuDNN runtime supports the pinned faster-whisper/CTranslate2 version.
Set the device once before running; a device/configuration change creates a new run.

The cumulative 30,000-character request cap is a guard, not a price quote. Failed
POST attempts count toward it and are not automatically retried. Review the ledger
before increasing the cap. Rime service access/billing is separate from ChatGPT Plus.

## Evaluation and interpretation

- WER uses each variant's own spoken reference; punctuation and case are normalized.
  Numeric formatting is not globally normalized, so WER can overstate digit errors.
- Critical-fact recovery uses explicit whole-phrase aliases and configured conflict
  patterns. It is an ASR lexical proxy, not semantic verification or human comprehension.
  Review false matches, alternate number formatting, contradictions, and all negations.
  Do not edit aliases after inspecting held-out transcripts.
- ESTOI compares each noisy clip to **its own aligned clean phone signal**. Do not
  compute intrusive similarity between two differently rewritten syntheses.
- DNSMOS uses Microsoft's non-personalized P.835 waveform ONNX model and published
  calibration. It reports SIG/BAK/OVRL, not P.808. Short clips repeat to the model's
  9.01-second input; means are a quality guardrail, not a root-cause detector.
- Selection requires paired completeness, >=5 percentage-point mean critical-fact
  gain, <=2-point WER increase, <=1.5x mean duration and <=0.15 DNSMOS OVRL decline,
  plus human approval. These are preregistered pilot choices, not industry thresholds.
- The same criterion screens the held-out candidate. A tiny 3-critical-text held-out
  set supports only a limited pilot claim, not a population-level conclusion. Inspect
  per-condition/per-repeat results; repeated noise/SNR rows are not independent people.
- A response ending normally at HTTP level does not prove all intended speech was
  spoken. Chunk arrival gaps do not measure audible playback gaps or end-user latency.

Run artifacts include configuration/corpus/noise hashes, package versions, model
revisions, request ledger, clips, transcripts, per-fact details, condition summaries,
plots, challenge lock, selection lock and evidence status. Resume from the same
configuration and Drive path to reuse completed work. Held-out re-execution resumes
the same candidate, not another selection experiment. No winner is valid evidence.

## Local validation and streaming

Python 3.11 or 3.12 is recommended. Install requirements into a virtual environment;
install FFmpeg and put it on PATH (or set `FFMPEG_BINARY`).

```shell
python -m pip install -r requirements-colab.txt
python -m unittest discover -s tests -v
python scripts/stream_probe.py --config experiment.json --output outputs/stream-001
```

The probe requires `RIME_API_KEY` in the environment. It sends three repeats of both
short and long text, saving raw PCMU and client timing. It never places a telephone
call. Decode each output and verify the final words:

```shell
ffmpeg -f mulaw -ar 8000 -ac 1 -i outputs/stream-001/stream_0_0.ulaw outputs/stream-001/stream_0_0.wav
```

## Sources and third parties

- [Rime Coda HTTP](https://docs.rime.ai/api-reference/coda/http),
  [speed controls](https://docs.rime.ai/docs/speed),
  [live catalog](https://docs.rime.ai/api-reference/data/voices-v2).
- [MUSAN / OpenSLR 17](https://www.openslr.org/17/): David Snyder, Guoguo Chen,
  Daniel Povey. CC BY 4.0; retain archive metadata and source attribution.
- [Microsoft DNSMOS](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS):
  the model revision/hash and upstream license are downloaded and recorded.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper),
  [pystoi](https://github.com/mpariente/pystoi), FFmpeg, NumPy, SciPy, SoundFile,
  pandas, jiwer, matplotlib, Hugging Face Hub, ONNX Runtime and requests.

Existing submission requirements remain in `HACKATHON_GUIDELINES.md` and the two
planning documents. A working Rime-first phone product and real-path evidence are
still required for the final hackathon submission.
