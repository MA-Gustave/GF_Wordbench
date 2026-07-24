# ADR-0004 — Use Native GF Shell Scenarios

**Document role:** Architectural decision record  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Decision

Executable project scenarios use reviewed native GF shell scripts (`.gfs`). Wordbench does not introduce a second scenario language.

Each scenario is executed in a fresh GF process through the GF boundary and the process executor. Scenario text is provided through standard input; no intermediate command shell is used.

## Scenario contract

A registered scenario has:

```text
stable scenario ID
project-relative .gfs path
purpose
required or optional status
mode applicability
timeout
stable BEGIN and END markers
normalization profile
optional gold reference
```

## Required evidence

For every execution Wordbench preserves:

- resolved scenario registration;
- GF executable and version;
- command/request metadata;
- raw stdout and stderr;
- exit code and termination reason;
- marker validation;
- normalized output and normalization version;
- assertion and gold-comparison results.

## Constraints

- Scenario files belong to the active project.
- One scenario should prove one coherent behavior family.
- Missing markers are an error, not an empty success.
- Normal validation is read-only for scenarios, inputs and gold files.
- A scenario success proves only the behavior explicitly asserted by that scenario.
