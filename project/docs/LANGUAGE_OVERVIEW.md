# Albanian (`sqi`) — Project Overview

**Document role:** Project identity and scope overview  
**Decision status:** Project-owned  
**Implementation status:** Project configuration and documentation are present; source-level completeness is not reverified by this update  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Project facts

| Field | Value | Authority |
|---|---|---|
| Project ID | `sqi` | `project/project.toml` |
| Language | Albanian | `project/project.toml` |
| Language code | `sqi` | `project/project.toml` |
| Documented GF suffix | `Sqi` | project module family and project documents |
| Source directory | `lib/src/albanian` | `project/project.toml` |
| Entrypoints | `GrammarSqi.gf`, `SyntaxSqi.gf` | `project/project.toml` |
| Required PGF | yes | `project/project.toml` |

The module suffix is not a separate field in the supplied configuration schema; it must remain consistent with actual module names and project contracts.

## Goal

The project develops and validates an Albanian Grammatical Framework implementation using the real GF toolchain, project-owned scenarios and reviewed regression evidence.

## Validation scope

Required scenarios are `load`, `missing`, `linearize` and `parse`. Optional scenarios are `generation` and `morphology`. Checkpoints are configured for morphology, nouns, verbs, extensions and structural modules.

## Claims and gaps

This overview does not claim complete linguistic coverage. A current source inventory, scenario results, gold comparisons and PGF build are required before release readiness is asserted.

Open project decisions include the primary Albanian variety, canonical orthography/Unicode policy, unique release entrypoint, expected PGF filename, supported GF versions and approved research authorities.
