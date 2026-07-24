# GF Wordbench — Direct and Downstream Failures

**Document role:** Diagnostic causality contract  
**Decision status:** Accepted  
**Implementation status:** A prior classifier implementation is referenced by the source documents; alignment with this contract is not reverified here  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

One root failure can cause many dependent GF modules to fail. Wordbench classifies causal relationships so reports emphasize likely roots without discarding downstream evidence.

## Diagnostic classes

```text
DIRECT       evidence points to the reported subject or an execution root failure
DOWNSTREAM   failure is explained by one or more identified upstream failures
AMBIGUOUS    available evidence supports multiple plausible roots
NOISE        non-actionable or explicitly excluded diagnostic material
SKIPPED      subject was not executed, with a reason
OK           no failure classification applies
```

## Rules

- Classification is derived from structured results and dependency evidence.
- Raw GF diagnostics remain attached to the original subjects.
- Downstream classification never turns a failed subject into `OK`.
- Ambiguity remains visible; the classifier does not invent certainty.
- Root-cause collapse is deterministic and cycle-safe.
- Paths and module names are normalized for comparison but preserved in evidence.

## Reporting

Summaries prioritize direct roots, then ambiguous failures, then downstream impact. Detailed reports retain every subject and its `blocked_by` chain.

## Verification

Tests must cover chains, diamonds, multiple roots, cycles, missing references, execution-level failures and stable ordering.
