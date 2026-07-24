# Albanian (`Sqi`) — Module Dependency Map

**Document role:** Project dependency authority  
**Decision status:** Project-owned  
**Implementation status:** Configured modules are recorded; exact source edges remain to be regenerated  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

This file records verified GF module relationships. It must not invent edges from naming conventions.

## Configured inventory

| Module | Configured role | Verification |
|---|---|---|
| `MorphoSqi.gf` | checkpoint | source import scan pending |
| `NounSqi.gf` | checkpoint | source import scan pending |
| `VerbSqi.gf` | checkpoint | source import scan pending |
| `ExtendSqi.gf` | checkpoint | source import scan pending |
| `StructuralSqi.gf` | checkpoint | source import scan pending |
| `GrammarSqi.gf` | entrypoint | source import scan pending |
| `SyntaxSqi.gf` | entrypoint | source import scan pending |

## Edge kinds

```text
imports
opens
extends
implements
instantiates
uses_helper
uses_lincat
loads
reads_input
compares_gold
builds_artifact
```

## Required generated table

A current source scan must populate:

| Provider | Consumer | Edge kind | Source location | Contract | Status |
|---|---|---|---|---|---|
| _pending source inventory_ | | | | | |

## Rules

- Direct and transitive dependencies are distinct.
- External RGL modules are labeled external.
- Cycles are errors unless explicitly justified by GF semantics and accepted project policy.
- Scenario, gold and artifact edges are recorded separately from GF imports.
- Renaming a module updates configuration, consumers, scenarios, golds and documentation together.

## Release gate

Release readiness requires a complete inventory, no unexplained cycles, configured modules present, entrypoint closure verified and dependency evidence tied to the current source fingerprint.
