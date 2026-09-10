# Audio evidence and product validation guide

The active submission focuses on competing speech and critical facts.
The product currently uses browser LiveKit WebRTC/Opus. There is no implemented
SIP/PSTN calling flow and no demonstrated real telephone performance.

Use [docs/GRID_REPRODUCTION.md](docs/GRID_REPRODUCTION.md) to inspect/reproduce the
completed offline grid and [docs/PRODUCT_EVIDENCE.md](docs/PRODUCT_EVIDENCE.md)
for product acceptance. Keep the offline study's codec/noise placement and
evaluator configuration separate from final-product measurements.

For the current grid, all 294 development observations were selected with no
missing rows; zero breakpoint crossings were supported. Do not change the
90% fact target, repeats or recurrence settings after seeing the result.
The 0 to -5 dB competing-speech intervals show repeatable deterioration.
Five dB is descriptive of the observed aggregate risk region only.

Run no additional inference merely to prepare the submission documents.
Prefer the saved source observations, manifest, source hashes, analysis settings
and paired audio. A user-side noise detector or fact-checking intervention needs
its own labeled product checks before any benefit is asserted.
