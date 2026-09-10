# Final product implementation roadmap

The current plan is [docs/ENGINEERING_PLAN.md](docs/ENGINEERING_PLAN.md).
Build on the existing `product-foundation` implementation retained in this branch.

The completed grid supports studying competing-speech masking and critical-fact
confirmation. It does not supply a validated detector, universal SNR cutoff, or
proven intervention. Preserve the zero-supported-breakpoint result.

Order: finish evidence transfer; implement a bounded speech-risk input contract;
add risk-aware confirmation and authoritative fact read-back; integrate detector
input and UI status; validate normal/stress behavior; record and submit the demo.
The existing product can run before these extensions, but must not advertise them
as implemented.

Use [RIME_EVIDENCE.md](RIME_EVIDENCE.md) for claims and
[docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md) for delivery.
