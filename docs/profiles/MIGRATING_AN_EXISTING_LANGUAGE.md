# GF Wordbench — Migrating an Existing Validation Profile

**Document ID:** `GF-WB-PROFILES-MIGRATING`
**Status:** Normative migration procedure
**Last reviewed:** 2026-08-05

## 1. Scope

This document migrates legacy Wordbench project configurations into optional validation profiles while leaving GF language sources in their existing location.

## 2. Legacy assumptions to remove

- mandatory root `project/`;
- project configuration as active-language authority;
- `sources.directory` selecting the language;
- `gf.path_parts` constructing the runtime GF path;
- one physical Wordbench clone per language;
- source copying during project initialization or reset.

## 3. Migration mapping

| Legacy fact | Current owner or treatment |
|---|---|
| source directory | explicit selected path and `ResolvedLanguageContext` |
| RGL root / GF path parts | environment and canonical GF path resolver |
| project ID | profile ID only |
| language code | compatibility assertion only |
| entrypoints/checkpoints | profile-required policy |
| scenarios/inputs/golds | profile-owned assets |
| release requirements | profile-owned policy |
| output paths | environment and `RunPaths` |
| last selected path | application state |

## 4. Procedure

1. Preserve the original configuration and source tree.
2. Resolve the actual language path explicitly.
3. Create or select a profile root.
4. Copy only profile-owned docs, scenarios, inputs, golds, and policy.
5. Remove or deprecate `sources.directory` and `gf.path_parts` from canonical output.
6. Convert project identity into profile identity and language compatibility assertions.
7. Validate every referenced module and asset against the resolved context.
8. Emit canonical profile output separately.
9. Report ambiguous, lossy, or unsupported conversions.
10. Verify that no source files were copied, moved, or rewritten.

## 5. Safety rules

Migration must be dry-run capable, path-contained, explicit, and recoverable. It must not guess an RGL root, choose an ambiguous language candidate, or rewrite a profile during normal validation.

## 6. Successful result

A successful migration produces:

- unchanged external GF sources;
- one valid explicit optional profile;
- no machine-local paths in portable policy;
- a compatible resolved language context;
- reproducible profile validation and run evidence.
