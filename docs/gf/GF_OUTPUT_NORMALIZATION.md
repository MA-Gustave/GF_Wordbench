# GF Wordbench — GF Output Normalization

**Document role:** GF integration specification  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

Normalization produces stable comparison material while preserving the complete native GF evidence.

## Evidence pipeline

```text
stdout/stderr bytes
→ raw artifacts
→ decoded transcript
→ marker extraction
→ versioned normalization
→ normalized artifact
→ assertions and comparisons
```

## Allowed normalization

A profile may normalize only declared non-semantic instability, such as:

- line-ending differences;
- explicitly identified temporary or run paths;
- stable removal of approved prompts or banners;
- trailing spaces where the contract declares them irrelevant;
- platform-specific path separators in designated fields.

## Forbidden normalization

Normalization must not silently change:

- Albanian text, diacritics or Unicode characters;
- abstract trees or constructor names;
- token order, punctuation or meaningful whitespace;
- parse counts or ambiguity;
- error messages needed for diagnosis;
- missing output, missing markers or truncated sections.

## Versioning

Every normalized artifact records the normalization profile and version. Any incompatible rule change requires review of affected gold files and comparisons.

## Failure semantics

Decoding failure, missing markers, unexpected truncation or an unknown normalization version produces an explicit error. None of these conditions may yield an empty successful comparison.
