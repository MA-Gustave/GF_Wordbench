# ADR-0003 — Separate Static Scan and GF Compilation

**Document role:** Architectural decision record  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Decision

Static scanning and GF compilation are separate validation stages with separate result types and separate claims.

```text
static scan → heuristic findings
GF compile → authoritative GF validity evidence
```

A scan finding may identify a risky pattern, style defect, migration hazard or likely source of failure. It must not declare a module GF-valid or GF-invalid.

## Required behavior

- Scanners are deterministic and versioned.
- Findings include rule ID, subject, location, severity and evidence.
- Compilation is executed through the GF boundary.
- Raw compiler output is retained before parsing.
- Reports show scan findings and compile results separately.
- A release gate may require a scan policy, but GF validity comes from GF.
- `SKIPPED`, `ERROR`, `FAIL` and `OK` remain distinct.

## Failure handling

A scanner failure does not become a compiler failure. A compiler failure does not erase scan evidence. Continuation is decided by run policy and the selected validation mode.

## Evidence required

Unit tests must prove scanner determinism and non-authoritative wording. Integration tests must prove that compile status is derived from GF execution and required artifacts, not from scan counts.
