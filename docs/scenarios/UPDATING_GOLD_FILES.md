# GF Wordbench — Updating Gold Files

**Document role:** Gold update procedure  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Safety rule

Gold files change only through an explicit maintainer operation. Normal validation, release validation and report generation are read-only.

## Required workflow

1. Produce a current run for the scenario.
2. Inspect GF version, raw output, normalized output and normalization version.
3. Review the generated diff.
4. Confirm that the behavior change is intended.
5. Record linguistic or technical justification.
6. Update the selected gold explicitly.
7. Re-run the scenario and all affected release checks.
8. Commit the gold with related source, scenario, contract and changelog updates.

## Refusal conditions

Do not update a gold when output is truncated, markers are invalid, GF/RGL compatibility is unknown, normalization changed unexpectedly, the scenario is nondeterministic, or the change merely hides a defect.

## Auditability

The update record should identify scenario ID, prior gold hash, new gold hash, source run ID, normalization version, reviewer and related decision or issue.
