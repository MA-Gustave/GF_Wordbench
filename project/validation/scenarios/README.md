# Albanian (`Sqi`) — Validation Scenarios

**Document role:** Project scenario authoring guide  
**Decision status:** Project-owned  
**Implementation status:** Scenario IDs are configured; concrete script completeness is not reverified  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Contract

One registered scenario ID maps to one UTF-8 `.gfs` file:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Required IDs are `load`, `missing`, `linearize` and `parse`. Optional IDs are `generation` and `morphology`.

## Authoring rules

- Use project-relative paths and configured modules.
- Start a fresh GF process for each scenario.
- Emit stable `BEGIN` and `END` markers for every asserted section.
- Bound parsing, generation and morphology output.
- Terminate explicitly.
- Do not depend on prior runs, caches or machine-local paths.
- Do not update gold files from the scenario.

## Evidence

Each run records request metadata, GF version, raw stdout/stderr, termination reason, markers, normalized output, assertions and gold comparison.

## Review

A scenario is release-ready only when its purpose, inputs, markers, normalization profile, expected evidence and failure semantics are reviewed and reproducible.
