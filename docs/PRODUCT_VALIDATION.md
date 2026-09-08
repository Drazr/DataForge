# Implementation validation

Validation of the product foundation, independent of unfinished experiments:

| Check | Result |
|---|---|
| Python controller, runtime, cache, Rime adapter, SDK, local API and evidence-status checks | 52 passed |
| Browser setup failures, expired sessions, startup cancellation, mobile width and optional tool checks | 7 passed |
| TypeScript check | Passed |
| Frontend production build | Passed |
| Live acceptance scenario discovery | 4 scenarios found |
| Rime public catalog | Coda / Astra / English present when checked |
| Real credentialed voice verification | **Unverified: credentials missing** |

The browser software checks substitute setup API responses intentionally. They
do not simulate a successful call or supply voice-performance evidence. The
optional WebMCP contract was checked through an injected registry; a native
browser WebMCP registry was not independently verified.

The Python suite reports two dependency deprecation warnings from the
Starlette/httpx test client. The build reports a large client bundle warning
from the voice UI dependencies. Neither prevented the corresponding checks.

Review fixes were checked on 8 September 2026. Regression coverage includes
sequential playback, ignored overlapping replies, failed and concurrent worker
cleanup, and interrupted evidence runs. Browser checks verify replacement of expired
sessions and cancellation during both worker creation and audio connection.

The live command generated an ignored local `evidence/live-status.json` with
`status: unverified` and the missing credential names. No API key values,
measured voice timings, experiment conclusions or paid-provider success are
included in this validation record. Run the procedure in PRODUCT_EVIDENCE.md
after configuring credentials before recording a final demonstration.
