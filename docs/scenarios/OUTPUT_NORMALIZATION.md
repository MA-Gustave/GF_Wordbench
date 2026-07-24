# GF Wordbench — Scenario Output Normalization

**Document role:** Scenario normalization contract  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Scope

Scenario normalization operates only on extracted marked sections. Raw stdout and stderr remain unchanged.

## Profile

Each scenario names a normalization profile and version. The profile declares every transformation in order.

## Safe transformations

- normalize line endings;
- remove a final trailing blank line when declared;
- replace approved run-local paths with stable tokens;
- normalize path separators in designated path fields;
- remove explicitly recognized non-semantic GF banners or prompts.

## Unsafe transformations

- changing Albanian orthography or Unicode;
- sorting output whose order is meaningful;
- deleting duplicate results;
- collapsing ambiguity;
- rewriting constructor names or trees;
- suppressing errors or missing content;
- accepting malformed markers.

## Reproducibility

The normalized artifact records source evidence, profile ID, profile version and hash. The same raw input and profile version must produce identical normalized output.

## Change control

A normalization change requires tests, changelog entry when public behavior changes, and explicit review of every affected gold.
