# Ordered problems and countermeasures

Scope: the competing-speech grid and the final product built on the foundation.
Other experiments retain their histories on their own branches.

| Order | Problem | Countermeasure and short reason |
| --- | --- | --- |
| 1 | Colab Python 3.13 differed from original 3.11/3.12 pins; replacing numerical packages left stale imports. | Compatible install path plus runtime restart; avoids mixing NumPy/SciPy versions in memory. |
| 2 | Dataset paths were empty after runtime/account changes. | Reuse the persistent Drive MUSAN folder and verify paths; runtime disks are temporary. |
| 3 | GPU quota and large reviewers consumed the available runtime. | CPU INT8 evaluator, cached synthesis, 12-score timing and per-row checkpoints; use one fixed evaluator within the new grid. |
| 4 | Two SNR points could not describe a degradation region. | Freeze four sources and five adjacent SNRs for seven critical texts with two repeats: 294 scores, development only. |
| 5 | Wrapping noise/full-file RMS could distort the delivered SNR. | Bounded non-looping windows, per-window RMS and measured-SNR checks; preserve comparable mixtures. |
| 6 | The -5 dB mixture exceeded the peak limit in preflight. | Audit all frozen mixtures before run creation and apply one global headroom level; avoid per-clip limiting and preserve failed-run provenance. |
| 7 | New Cell 7 imported safe_speech_level_dbfs from an old checkout/module. | Pull the correct branch and restart/reload before resuming; copying a cell alone does not update imported code. |
| 8 | Large mean losses were initially described too strongly as a breakpoint. | Reread Cells 6/7: zero supported crossings, but repeatable fact deterioration at 0 to -5 dB. Retain the 90% target and four-of-seven rule. |
| 9 | DNSMOS appeared comparatively high despite poor target-fact recovery. | Keep DNSMOS supporting only; use per-fact outcomes for the design motivation. |
| 10 | Pasted dataframes omit full confidence bounds and source metadata. | Archive original pastes and hashes; label summaries as derived and request original exports instead of manufacturing missing evidence. |
| 11 | Foundation has a generic yes/no gate but no competing-speaker detector or fact read-back. | Retain tested code and mark the new contract/controller/read-back work as planned; prevent planned functionality being presented as measured. |
| 12 | Offline listening mixtures do not match what a local microphone observes. | Document stream/noise placement and require separate labeled detector and live product checks. |
| 13 | Build/submission material was spread across branches. | Create final-product from 826a5df and include the focused grid source/evidence and submission documents together. |
| 14 | The final product had no defensible automatic competing-speaker detector. | Use an explicit user report or disclosed test injection; missing detection is never labeled clear. This keeps the claim aligned with available evidence. |
| 15 | A generic “yes” could not show that masked critical facts were retained. | Require full reference-code and appointment-time read-back after reported difficulty; strict equivalent parsing rejects partial, qualified or wrong replies. |
| 16 | Experimental exports and selected audio arrived after the initial handoff. | Import them unchanged, verify 294 row identities and all three WAV hashes, and preserve a narrow stress-case manifest. |
| 17 | A short demo cannot contain complete machine-readable evidence. | Keep the demo at 4–5 minutes and save received WebM audio plus redacted JSON separately for reproducibility. |
| 18 | Submission branch needed only product source and three required documents. | Move supporting docs, evidence and experiment source to main/submission-support/final-product; link the archive from README and RIME_EVIDENCE without changing product imports. |

Validation is recorded in PRODUCT_VALIDATION.md. Future changes should append
the issue, countermeasure, reason and actual validation result in order.
