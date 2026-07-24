# Albanian (`Sqi`) — Validation Assets

**Document role:** Project validation ownership guide  
**Decision status:** Project-owned  
**Implementation status:** Validation structure and scenario registry are configured  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Structure

```text
project/validation/
├── scenarios/
├── inputs/
└── gold/
```

These are version-controlled project inputs. Run outputs belong under the configured output root, not inside this directory.

## Registered scenarios

Required:

```text
load
missing
linearize
parse
```

Optional:

```text
generation
morphology
```

Every ID must have consistent registration, `.gfs` file, inputs, markers, normalization profile and optional gold.

## Modes

- `quick`: focused scan and compile evidence;
- `checkpoint`: configured checkpoint closure;
- `diagnostic`: extended evidence with controlled continuation;
- `release`: all required scenarios, golds, PGF and release gates.

## Rules

- Validation is read-only for project assets.
- Raw outputs are preserved before normalization.
- A checkpoint success does not prove entrypoint or PGF success.
- Missing required evidence prevents release `OK`.
- Historical artifacts are never treated as current without fingerprint and manifest verification.
