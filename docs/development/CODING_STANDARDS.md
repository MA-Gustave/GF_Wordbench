# GF Wordbench — Coding Standards

**Document role:** Development policy  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Core standards

- Use typed Python and explicit boundary models.
- Keep domain policies free of filesystem, JSON, TOML, subprocess and UI dependencies.
- Put process creation only in the process adapter.
- Put GF command construction and output interpretation only in the GF boundary.
- Keep CLI and GUI thin; both call the same use cases.
- Keep report writers pure over completed structured results.
- Avoid I/O and environment reads at import time.
- Prefer small public module APIs over imports from `internal` packages.

## Models and status

Use separate fields for validation status, execution state, diagnostic class and error kind. Do not compress several states into ambiguous booleans or infer machine state from report text.

## Paths and processes

Resolve paths before use, validate write roots, avoid shell invocation, pass argument arrays, bound output and time, preserve raw stdout/stderr and make cancellation explicit.

## Error handling

Expected tool failures return structured results. Exceptions are reserved for programming defects or conditions that prevent construction of a result. Entry boundaries convert uncaught failures into traceable terminal states.

## Persistence

Persisted formats have `schema_id` and `schema_version`. Writes are atomic where possible. Unknown future versions are rejected or handled by an explicit compatibility policy.

## Tests

Every behavior change includes the smallest relevant combination of unit, contract, schema, process, integration, real-GF and end-to-end tests. Claims of `Implemented` or `Verified` require named evidence.

## Documentation

One contract has one owning document. Consumers link to it rather than copying its full rules. Absolute developer-machine paths are forbidden in normative documentation.
