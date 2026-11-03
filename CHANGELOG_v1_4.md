# GF Wordbench 1.4.0

- Adds fail-closed `semantik-wordbench-handoff-v1` inspection.
- Verifies all declared SHA-256 hashes and binds candidate surfaces back to the source Phrase Ops report.
- Validates technical/adverstised/disabled case accounting and SA baseline-plus-extension capability declarations.
- Supports safe materialization only after verification.
- A valid handoff is `ACCEPTED_FOR_WORDBENCH_VALIDATION` and is always `release_eligible=false`.
- Existing Wordbench scenario, reviewed-golden, linguistic-review, PGF, and release gates remain authoritative and unchanged.
