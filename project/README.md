# GF Wordbench — Active Albanian Project

**Document role:** Active project entry point  
**Decision status:** Project-owned  
**Implementation status:** Project configuration and documentation are present; source-level completeness is not reverified by this update  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Identity

The active project is defined by `project/project.toml`:

```text
project ID: sqi
name: Albanian
language code: sqi
source directory: lib/src/albanian
entrypoints: GrammarSqi.gf, SyntaxSqi.gf
checkpoints: MorphoSqi.gf, NounSqi.gf, VerbSqi.gf, ExtendSqi.gf, StructuralSqi.gf
required scenarios: load, missing, linearize, parse
optional scenarios: generation, morphology
release PGF required: yes
```

One Wordbench workspace contains exactly one active project. Language-specific policy and evidence stay under `project/` and the configured GF source tree.

## Start here

1. Review `project.toml`.
2. Read `docs/00_PROJECT_START_HERE__PROJECT_DOCS.md` and `docs/INTERFILE_CONTRACT_LOCK.md`.
3. Resolve local GF and RGL paths.
4. Run configuration checks.
5. Run a focused `quick` validation.
6. Validate configured checkpoints.
7. Run `release` only after open project decisions and required evidence are complete.

## Ownership

`project/` owns project identity, linguistic contracts, scenarios, reviewed inputs, gold files, issue and decision records, coverage and release policy. It does not own framework orchestration, UI behavior, generic schemas or process execution.

## Current blockers

The supplied configuration requires a PGF but does not identify a unique release entrypoint or expected PGF filename. The supported GF version range is also unset. These remain release-blocking project decisions until explicitly resolved and verified.

## Read-only validation

Normal validation never modifies project sources, scenarios, inputs, golds or documentation. Mutable maintenance operations are separate and explicit.
