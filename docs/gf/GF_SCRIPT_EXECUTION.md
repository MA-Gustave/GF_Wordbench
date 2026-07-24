# GF Wordbench — GF Script Execution

**Document role:** GF scenario execution contract  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Scope

This contract governs execution of project-owned `.gfs` scenarios.

## Execution boundary

The scenario service sends a structured request to `GfToolPort`. The GF adapter builds the GF request and delegates process creation to `ProcessExecutorPort`.

```text
ScenarioService
→ GfToolPort.run_scenario
→ LocalProcessExecutor
→ GF
```

## Preconditions

- the project is resolved;
- the scenario ID is registered;
- the `.gfs` path is inside the project boundary;
- required input files exist;
- GF and RGL paths are resolved;
- timeout and output limits are set;
- the run directory is writable.

## Per-scenario isolation

Each scenario starts in a fresh GF process with a controlled working directory and environment. No scenario may depend on hidden state from a previous scenario.

## Captured evidence

- request metadata and redacted argument representation;
- GF version;
- start and finish timestamps;
- exit code, timeout, cancellation and launch error;
- raw stdout and stderr;
- marker-validation result;
- normalized output;
- assertions and gold comparison;
- produced artifacts, if any.

## Status rules

A zero exit code is not sufficient when markers, assertions or required artifacts are missing. A timeout, launch failure, missing marker or unparseable result is `ERROR`; a completed assertion or gold mismatch is `FAIL`.

## Security

No shell is invoked. Paths and inputs are validated before launch. Output is bounded, and cancellation must terminate the process tree where supported.
