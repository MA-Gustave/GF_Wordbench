# Albanian (`Sqi`) — Language Architecture

**Document role:** Project language architecture  
**Decision status:** Project-owned  
**Implementation status:** Project configuration and documentation are present; source-level completeness is not reverified by this update  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Authority

GF source is authoritative for actual imports, categories, lincats and linearizations. This document defines intended ownership and invariants; it must be synchronized with a generated source inventory.

## Intended layers

```text
external GF/RGL foundations
→ resource and morphology modules
→ category implementations and paradigms
→ syntax, structural and extension modules
→ grammar and syntax entrypoints
→ scenarios and release artifacts
```

Lower layers must not import release-facing entrypoints. Cycles and reverse dependencies require an explicit project decision.

## Configured checkpoints and entrypoints

| Role | Module |
|---|---|
| Morphology checkpoint | `MorphoSqi.gf` |
| Noun checkpoint | `NounSqi.gf` |
| Verb checkpoint | `VerbSqi.gf` |
| Extension checkpoint | `ExtendSqi.gf` |
| Structural checkpoint | `StructuralSqi.gf` |
| Entrypoint | `GrammarSqi.gf` |
| Entrypoint | `SyntaxSqi.gf` |

The configuration does not identify which entrypoint owns the release PGF. That role must not be inferred from filenames.

## Invariants

- Morphological distinctions are represented structurally before final strings.
- Category lincats have one authoritative owner.
- Public constructors preserve required agreement and state.
- Structural modules do not become hidden lexicons.
- Extension modules contain genuinely project-specific behavior rather than untracked fallback.
- Entrypoints compose lower layers and do not own low-level morphology.
- Every release-facing claim has a scenario or compile artifact.

## Verification

The definitive dependency map must be generated from current `.gf` sources, compared with this architecture and recorded in `MODULE_DEPENDENCY_MAP.md`.
