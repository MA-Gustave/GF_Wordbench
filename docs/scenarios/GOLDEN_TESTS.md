# GF Wordbench — Golden Tests

**Document role:** Golden comparison contract  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

Golden tests detect unintended changes in deterministic normalized scenario output.

## Comparison contract

```text
current normalized bytes == reviewed gold bytes
```

Comparison is exact after the declared normalization profile. The comparator does not repair, reorder or reinterpret output.

## Results

- `OK`: current normalized output exactly matches the reviewed gold.
- `FAIL`: both values exist and differ.
- `ERROR`: execution, extraction, normalization, decoding or file access prevents comparison.
- `SKIPPED`: the scenario is not applicable under an explicit policy.

## Evidence

A comparison result links to the raw output, normalized output, gold file, normalization version and diff artifact.

## Release behavior

Every required golden test must be current and `OK`. Missing, stale or incompatible gold evidence prevents release `OK`.

## Limit

A golden test proves regression stability for a reviewed example. It does not establish complete linguistic correctness.
