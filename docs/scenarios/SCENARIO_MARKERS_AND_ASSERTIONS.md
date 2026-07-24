# GF Wordbench — Scenario Markers and Assertions

**Document role:** Scenario marker and assertion contract  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Markers

Markers delimit stable output sections without interpreting unrelated GF output.

Recommended form:

```text
@@GF-WORDBENCH BEGIN <scenario-id> <section-id>@@
...
@@GF-WORDBENCH END <scenario-id> <section-id>@@
```

IDs must match the registered scenario and declared section. Markers must be unique, correctly ordered and complete.

## Marker failures

Missing, duplicate, nested incorrectly or mismatched markers produce `ERROR`. Wordbench must not treat an absent section as empty successful output.

## Assertion types

Supported assertions should be explicit and structured, for example:

- section exists;
- exact normalized text equals a reviewed value;
- normalized output matches a reviewed gold;
- required substring or pattern is present;
- prohibited substring or pattern is absent;
- parse or result count satisfies a declared bound;
- expected artifact exists and is current.

## Semantics

A completed assertion mismatch is `FAIL`. An assertion that cannot be evaluated because execution or extraction failed is `ERROR`. Assertions never parse human report prose.
