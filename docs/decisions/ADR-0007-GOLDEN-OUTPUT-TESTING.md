# ADR-0007 — Golden Output Testing

**Document role:** Architectural decision record  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Decision

Reviewed `.gold` files are the canonical exact-comparison references for deterministic normalized scenario output.

```text
raw GF output
→ marker validation
→ versioned normalization
→ current normalized output
→ exact comparison with reviewed gold
```

## Rules

- Raw output is always preserved.
- Gold comparison uses normalized output, never raw terminal text.
- A gold file is a project-owned input, not a generated run artifact.
- `validate` never creates, rewrites or accepts a gold file.
- Gold updates require an explicit command or workflow, a visible diff and maintainer review.
- A normalization change invalidates comparisons until reviewed under the new version.
- Missing required gold evidence blocks a release result from becoming `OK`.

## Update workflow

1. Run the relevant scenario and retain the run ID.
2. Inspect raw and normalized evidence.
3. Review the diff against the current gold.
4. Confirm that the change is intended and linguistically justified.
5. Update the gold through the explicit gold-update operation.
6. Re-run validation and record the approving change.

## Non-claims

A passing gold comparison proves stability against a reviewed expectation. It does not prove universal linguistic correctness or complete grammar coverage.
