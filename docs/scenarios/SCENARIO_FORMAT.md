# GF Wordbench — Scenario Format

**Document role:** Scenario asset contract  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Canonical assets

```text
project/validation/scenarios/<scenario-id>.gfs
project/validation/inputs/
project/validation/gold/<scenario-id>.gold
```

Scenario registration belongs to `project/project.toml` and the project validation specification.

## Identifier

A scenario ID is lowercase, stable and filesystem-safe:

```text
[a-z][a-z0-9_-]*
```

Renaming an ID is a project migration because it changes registration, artifacts, gold references and historical comparisons.

## Script requirements

A `.gfs` file must:

- be UTF-8 text with a final newline;
- load only declared project modules and inputs;
- emit stable section markers;
- bound its output;
- terminate explicitly;
- avoid machine-local absolute paths;
- avoid hidden dependency on previous scenario state.

## Required metadata

Registration records purpose, required/optional status, applicable modes, timeout, normalization profile, input references, expected markers and optional gold reference.

## Validation

Format validation occurs before GF execution. A malformed registration or unsafe path is a configuration error, not a scenario assertion failure.
