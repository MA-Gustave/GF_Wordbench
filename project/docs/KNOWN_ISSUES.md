# Albanian (`Sqi`) — Known Issues

**Document role:** Active project issue registry  
**Decision status:** Project-owned  
**Implementation status:** Issue registry corrected and deduplicated  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Status and evidence

Historical examples are not current defects until reproduced against the active source fingerprint and toolchain.

| ID | Issue | Status | Evidence | Release impact |
|---|---|---|---|---|
| `KI-SQI-001` | Establish a current release baseline | Open | `E0` | Blocks a release-readiness claim |
| `KI-SQI-002` | Reproduce historical `GrammarSqi` unification failure | Investigating | `E1` | Unknown until reproduced |
| `KI-SQI-003` | Reproduce historical `GeneratePMCFG` / inflection failure | Investigating | `E1` | Unknown until reproduced |
| `KI-SQI-004` | Verify historical missing `DAP` linearization type | Investigating | `E1` | Unknown until reproduced |
| `KI-SQI-005` | Keep downstream failures distinct from root issues | Open | `E1` | Diagnostic quality |
| `KI-SQI-006` | Ensure zero unresolved placeholders in active contracts | Open | `E2` when scanned | Blocks release if normative placeholders remain |
| `KI-SQI-007` | Align entrypoints, scenarios, golds and PGF registry | Open | `E0` | Blocks release if inconsistent |
| `KI-SQI-008` | Remove legacy tool assumptions from project policy | Open | `E1` | Blocks affected contracts |
| `KI-SQI-009` | Regenerate exact active module inventory | Open | `E0` | Blocks release if incomplete |
| `KI-SQI-010` | Record linguistic coverage gaps explicitly | Open | `E0` | Requires explicit acceptance |

## Immediate priorities

1. Resolve unique release entrypoint and expected PGF identity.
2. Declare supported GF/RGL versions.
3. Run a current release validation and retain its manifest.
4. Regenerate module and constructor inventories.
5. Reproduce or close historical diagnostics.
6. Complete approved linguistic-source registry.

## Closure rule

An issue closes only with reproducible evidence, updated contracts and verification of all affected checkpoints, scenarios, golds and release gates.
