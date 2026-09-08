# Implementation validation

Validation of the product foundation, independent of unfinished experiments:

| Check | Result |
|---|---|
| Python controller, runtime, cache, Rime adapter, SDK and local API checks | 45 passed |
| Browser configuration failure, provider setup failure, mobile width and optional tool checks | 4 passed |
| TypeScript check | Passed |
| Frontend production build | Passed |
| Live acceptance scenario discovery | 5 scenarios found |
| Rime public catalog | Coda / Astra / English present when checked |
| Real credentialed voice verification | **Unverified: credentials missing** |

The browser software checks substitute setup API responses intentionally. They
do not simulate a successful call or supply voice-performance evidence. The
optional WebMCP contract was checked through an injected registry; a native
browser WebMCP registry was not independently verified.

The Python suite reports two dependency deprecation warnings from the
Starlette/httpx test client. The build reports a large client bundle warning
from the voice UI dependencies. Neither prevented the corresponding checks.

The live command generated an ignored local `evidence/live-status.json` with
`status: unverified` and the missing credential names. No API key values,
measured voice timings, experiment conclusions or paid-provider success are
included in this validation record. Run the procedure in PRODUCT_EVIDENCE.md
after configuring credentials before recording a final demonstration.
