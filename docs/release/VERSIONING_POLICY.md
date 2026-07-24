# GF Wordbench — Versioning Policy

**Document role:** Release versioning authority  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Independent version axes

GF Wordbench versions the following independently:

- application releases;
- persisted schemas;
- public CLI and Python contracts;
- normalization profiles;
- diagnostic rule sets;
- project configuration schema;
- active-project releases, when published separately.

An application version never implies a schema version.

## Semantic versioning

Use `MAJOR.MINOR.PATCH` for published application releases:

- **MAJOR**: incompatible public behavior or contract;
- **MINOR**: backward-compatible capability;
- **PATCH**: compatible correction.

## Schema changes

Every persisted document carries `schema_id` and `schema_version`. Incompatible changes require a new major schema version and an explicit migration or rejection policy. Migrations preserve the source artifact and record their producer version.

## Normalization and diagnostics

A change that can alter normalized output, gold comparison or diagnostic classification increments the relevant rule/profile version and requires regression review.

## Project compatibility

Project configuration, scenarios and golds declare the contract versions they require. A release must record Wordbench, GF, RGL, schema and normalization versions in its evidence.

## Deprecation

Deprecations are documented before removal, include a replacement and migration path, and remain testable during the announced compatibility window.
