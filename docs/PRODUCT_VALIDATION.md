# Final product validation

## Checks completed for this branch

| Check | Result |
| --- | --- |
| Inherited product controller, runtime, cache, Rime adapter, SDK and API tests | 55 passed |
| Copied Grid v2 producer/analysis regression suite | 64 passed; 12 subtests passed |
| Focused evidence JSON parsing and row/result invariants | Passed |
| Colab cell boundary/compile checks | Included in the passing Grid v2 suite |
| TypeScript/frontend build | Inherited from product-foundation; not rerun after documentation-only frontend changes (there were none) |
| Real credentialed final-product voice verification | Unverified |
| Competing-speech detector and critical-fact read-back | Planned; not implemented or measured |

The product tests were run from `final-product` using the foundation environment.
The grid tests were run from the same branch with the installed evaluator
packages. That local evaluator environment emitted a SciPy warning because its
NumPy version was newer than SciPy's declared range; all 64 tests completed.
For reproduction, use the pinned `requirements-grid.txt` in a separate
environment as documented.

The copied experiment and analysis source matches the Grid v2 branch except for
the Colab checkout branch/directory and the corresponding regression expectation.
No metric algorithm, frozen acceptance setting or reported result was changed.

## Existing product verification inherited from product-foundation

At `product-foundation@826a5df`, seven browser software checks, TypeScript
checking, a production frontend build and discovery of five live scenarios were
reported as passing. Those checks used mocked setup/error responses where
documented and do not establish successful voice behavior. The public Rime
catalog contained Coda/Astra/English when checked; each final live session must
repeat preflight.

The credentialed end-to-end suite has not been supplied as passing. No live
latency, detector accuracy, human comprehension, speaker identity or mitigation
improvement is claimed. The proposed detector/read-back extension requires the
new procedure in PRODUCT_EVIDENCE.md.

## Evidence validation

The Cell 6 and Cell 7 pastes hash to the values in
`evidence/noise-grid-v2/provenance.json`. Derived JSON records 294 observations,
zero missing rows and zero supported crossings. Full result exports and referenced
audio are still missing. The displayed dataframe hides confidence fields, so this
branch records no numeric confidence bounds.

Before submission, run the exact final product with configured Rime/LiveKit
credentials, preserve received audio and redacted events, and record measured
normal/stress results. A software regression pass and an offline ASR-proxy grid
do not replace this product verification.
