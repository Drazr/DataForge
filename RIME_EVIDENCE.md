# Rime evidence: competing speech and critical-fact delivery

## What the completed study supports

Across 294 development observations (seven critical texts, two syntheses,
four noise sources, five SNRs plus clean), competing-speech masking reduced
ASR-measured critical-fact recovery. Both speech recordings showed repeatable
deterioration between 0 and -5 dB. The analysis reported **zero supported
breakpoint crossings** under its frozen criteria.

| Condition | Fact recovery | WER | DNSMOS overall |
| --- | ---: | ---: | ---: |
| Clean | 94.90% | 0.304835 | 3.050540 |
| Speech 1, 10 dB | 94.90% | 0.320828 | 2.617493 |
| Speech 1, 5 dB | 85.71% | 0.345044 | 2.486661 |
| Speech 1, 0 dB | 83.67% | 0.379338 | 2.410561 |
| Speech 1, -5 dB | 60.20% | 0.491628 | 2.434310 |
| Speech 2, 10 dB | 94.90% | 0.323203 | 2.851438 |
| Speech 2, 5 dB | 88.78% | 0.370828 | 2.829661 |
| Speech 2, 0 dB | 74.49% | 0.463149 | 2.798541 |
| Speech 2, -5 dB | 17.35% | 0.846196 | 2.844873 |

Five dB is an observed aggregate risk region for these two recordings.
It is not a supported breakpoint, universal cutoff or runtime detector setting.
At the 10-to-5 dB interval, repeatable deterioration occurred in only 2/7 texts
for each speech source; repeated threshold crossings occurred in 2/7 and 1/7.
The frozen rule requires at least 4/7. At 0-to--5 dB, repeatable fact
deterioration occurred in 6/7 and 7/7 texts, but the higher-SNR means were already
below 90%, so these were not acceptance crossings.

DNSMOS can remain relatively high while target facts disappear (speech_2,
-5 dB: 2.845 DNSMOS with 17.35% fact recovery). It is supporting quality evidence,
not a confirmation signal. Environmental conditions provide comparison data in
the archived Cell 6 output; this is not a broad claim about all noise types.

## Procedure and provenance

The engineering target was minimum fact recovery 0.90, frozen before scoring.
Matched adjacent SNRs require both repeats and at least four of seven texts
with consistent deterioration/crossing. Bootstrap resamples texts, with 2,000
samples and seed 20260910. These are exploratory small-sample criteria, without
multiplicity correction.

Mixing used bounded non-looping windows and a global peak-headroom audit.
The producer reports a complete development-only grid with held-out untouched.
Cells 6/7 selected 294 observations and reported zero missing rows, zero supported
crossings and 82 development challenge rows. Those 82 rows are diagnostics,
not 82 independent participants or validated intervention cases.

Full producer run ID:
`05eca3e90a16aae62993a4e8c0622498daf075b34cb0dd9342baad1fa1a946ce`.
Analysis session: `20260910T095801572979Z`.

[Archived outputs and derived summary](evidence/noise-grid-v2/README.md) identify
the supplied files and missing exports. [Reproduction](docs/GRID_REPRODUCTION.md)
includes the CPU analysis command and unchanged source provenance.
Confidence bounds are hidden by the pasted dataframe display; their numeric
values cannot be reconstructed from these means and have not been fabricated.

## Product engineering claim

When a caller reports hearing difficulty, the product withholds confirmation and
requires authoritative reference-code and appointment-time read-back before it
accepts “yes.” Wrong or partial read-back fails closed. The product supplies Rime
speech, targeted replay, a fresh-response gate, and this read-back policy.
Automatic competing-speech detection is not installed; no detector accuracy,
speaker identity, human comprehension, or mitigation improvement has been measured.

[Product procedure](docs/PRODUCT_EVIDENCE.md) defines the next validation.
Record normal and stress cases, false confirmations and unresolved cases on the
actual final transport. The fixed offline mixtures motivate the product but do
not directly validate live microphone monitoring.

The product defaults are Rime `coda/astra/eng`,
`https://users.rime.ai/v1/rime-tts`, mono 24 kHz signed 16-bit PCM through
LiveKit WebRTC/Opus. Verify these through live preflight. The original experiment's
exact voice/model/transport must be recovered from its manifest; do not substitute
these product defaults for missing experimental provenance.

## Limitations

ASR fact recovery and WER are proxies, not measured human comprehension.
Clean fact recovery was 94.90%, not perfect. Seven texts and two recordings per
noise family do not establish generalization. Product read-back checks cannot
authenticate speakers by themselves. Full analysis exports and three selected,
hash-verified source-audio clips are included. A credentialed final-product run
has not yet been added.

The submission evidence concerns competing speech and critical facts only.
