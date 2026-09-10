# Noise-Masking development log

Updated 2026-09-08. Entries are in the order encountered. Runtime observations
come from the user's Colab output and review ZIP, not local audio experiments.

| Step | Problem | Countermeasure and reason | Status |
| --- | --- | --- | --- |
| 1 | Cell 3 rejected Colab Python 3.13; original pins targeted 3.11/3.12. | Added the Python 3.13 dependency overrides used in this session; keep original pins for 3.11/3.12. Capture pip-freeze for reproducibility. | User completed installation and scoring; overrides now in Cell 3. |
| 2 | Cell 4 raised SciPy `is_jax` ImportError after installation. | Restart the session, rerun Cells 1–2, skip installation, then continue at Cell 4. This unloads modules left in memory during upgrades. | Subsequent run succeeded. |
| 3 | Cell 5 found zero noise/speech files. | Enable DOWNLOAD_MUSAN once, then reuse Drive files with it False. Downloads are disabled by default. | User obtained 930 environmental clips and four speech clips. |
| 4 | Cell 6 had empty paths. | Select candidates from downloaded paths using metadata, preview both recordings, and retain manual label verification. A keyword match does not establish the sound type. | Updated Cell 6; user proceeded to scoring. |
| 5 | Cell 7/9 require listening acknowledgements. | Verify labels and preflight audio before setting the corresponding flags. Playback and ASR output alone do not certify quality. | User completed preflight and baseline; no independent listening claim. |
| 6 | Progress said 42 scored, whereas exports had 294 rows. | Interpret 42 as 21 texts × two syntheses; seven conditions give 294 scored clips. | Complete baseline `1f95820a36625efe`. |
| 7 | A/B challenge gate requires two recurrent texts per condition; only one appeared at 0 and 5 dB. | Keep the gate; inspect matched clean/noisy facts before billed variants. Counts across conditions cannot be added. | Original baseline ineligible. |
| 8 | Pasted tables truncated transcripts. | Export complete records and critical audio. The former standalone review script is now Cell 10 here. | ZIP received and inspected; standalone script removed. |
| 9 | Equivalent times such as `9.20am`, `920 a.m.` and `9:20 am` scored differently. | Normalize valid numeric clock formats with explicit AM/PM only for time facts. Keep wrong times, names and codes as failures. Apply the same scorer to Noise and A/B. | Corrected code and regression tests added. |
| 10 | Correcting a frozen run in place would obscure the original measurement. | Cell 10 rescores saved transcripts into `outputs/reviews/<run>/time_format_v2`, preserving original audio, rows, WER, ESTOI and DNSMOS. No synthesis or ASR calls. | Derived review; see the measured assessment below. |

Cell 10 is self-contained for the existing session: paste only that cell into
the completed notebook. Its embedded time normalizer is regression-tested against
the updated library. `BASELINE_REVIEW_SOURCE` can select a different source run.
The default points to this session's completed run.

Review exports are **not A/B handoff runs**. They retain the producer run ID as
provenance and add `fact_scoring_revision`. A future corrected baseline must use
the same revised implementation as A/B; do not bypass manifest/hash checks.

Changes in the local worktrees are not automatically published to GitHub or
installed in an existing Colab checkout. Copy the updated cell explicitly.

## Measured review and verification

Local execution of the complete Cell 10 against the user's ZIP corrected **51
false fact failures** across 294 scores. Clean fact recovery becomes **95.92%**;
competing speech at 0 dB becomes **89.80%**. Each other noisy condition is **95.92%**.
There are **zero recurrent texts in every condition**, so A/B remains ineligible.
Wrong times such as `9.28am` and wrong codes remain errors. These are transcript
metrics; human listening has not been certified.

The original files' hashes were unchanged, and Cell 10 using the old matching
behavior produced the same rescored facts as the updated library. The Noise
suite passed 32 tests; A/B passed 32 with one Noise-only check skipped. An initial
test invocation from the Grid directory imported the wrong package; rerunning
from each branch's own worktree resolved that local test-launch issue.

Machine-readable findings: [BASELINE_REVIEW_RESULT.json](docs/BASELINE_REVIEW_RESULT.json).
Reproduce offline with `python scripts/review_bundle.py PATH_TO_REVIEW_ZIP`.

Next: run only Cell 10 to persist the review in Drive. A further A/B study needs
a separately planned development baseline; keep the original run and held-out
split unchanged, and do not reduce the recurrence gate to force eligibility.

## Next baseline decision (historical; superseded by v2 below)

Grid/Breakpoint Analysis is deferred in favor of retaining Noise-Conditioned A/B
if a stronger baseline validates a challenge. Cell 4 now commits the separate
`stress_0_to_minus5` development profile before model loading: 0 dB and −5 dB,
two noise sources, two repeats, DNSMOS retained, and a required T4 GPU ASR
evaluator. This is 210 scores, while prior raw speech is reused from the
compatible synthesis cache. If no condition has two distinct repeated losses,
A/B and Grid are both inapplicable; if it does, run A/B and defer Grid.

## Completed stress-baseline handoff

The user completed run `6bd1eb398398af0e` and supplied its Cell 10 ZIP. All 210
scores are present and Cell 10 made zero format corrections. The condition
`competing_speech_-5dB` has three recurrent texts: `critical_01` (time/date),
`critical_03` (code), and `critical_05` (time). Fact recovery is 95.92% clean and
71.43% for that challenge. This supersedes the earlier baseline's ineligibility.

The A/B branch now contains the copied review evidence and prefilled handoff
settings. Its Cell 4 copies the complete original run and source synthesis cache
from shared Drive. The review ZIP alone omits that cache and some audio. Human
listening is still pending; no A/B or held-out outcome has been claimed.

## Noise Grid v2 development log

Added 2026-09-10. These entries continue the sequence above and record design
decisions before any v2 score is available.

| Step | Problem | Countermeasure and short reason | Status |
| --- | --- | --- | --- |
| 11 | The two-point 0/-5 dB stress run located a failure condition but could not locate onset or separate recording-specific effects. | Freeze five adjacent SNR levels and four distinct MUSAN recordings. This supplies actual intervals and two sources per noise family. | Implemented; no v2 measurements yet. |
| 12 | A full 42-text grid would consume scarce Colab GPU time while only seven texts carry labeled critical facts. | Use seven critical development texts × two cached syntheses × 21 conditions = 294 scores. This targets the primary factual-fidelity question and leaves held-out untouched. | Implemented as the core run. |
| 13 | New synthesis would add Rime cost and another uncontrolled speech realization. | Bind the source baseline's synthesis cache and verify all 14 WAV/metadata hashes before scoring. Refuse any cache miss. | Implemented in Cell 7. |
| 14 | Full-source RMS plus wrapping can misstate SNR for changing speech/noise and repeat a short segment. | Read a bounded source window, calibrate its actual RMS for each utterance, forbid wrapping, retain gain and nominal/measured SNR, and enforce 0.1 dB agreement. | Implemented and contract-tested. |
| 15 | Choosing favorable noise clips after seeing results would bias the grid; manual listening is slow. | Seed selection before scoring; choose two speech and two environmental files, exclude pilot hashes, and reject short, silent, clipped, or duplicate recordings. Save the audit. | Implemented in `noise_grid_v2.py`. |
| 16 | A long run can lose a Colab GPU session. | Save one JSON row per clip, reuse verified rows on rerun, and estimate runtime from a 12-score preflight. | Implemented in Cells 8–9. |
| 17 | Qwen listening review used a large quantized model, exhausted GPU allocations, and produced unstable JSON without a calibrated human-quality claim. | Remove it from the breakpoint gate. Use objective ASR fact recovery as primary, ESTOI/WER as diagnostics, and existing DNSMOS as supporting quality evidence. | Implemented; Qwen is not downloaded. |
| 18 | Analysis itself could waste a GPU session. | Split generation and analysis notebooks. The second notebook reads saved metrics and runs on CPU only. | Implemented. |
