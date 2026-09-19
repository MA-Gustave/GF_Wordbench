# GF Wordbench — Product Boundaries

**Document ID:** `GF-WB-PRODUCT-BOUNDARIES`
**Status:** Normative
**Last reviewed:** 2026-08-05

**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
## GF Wordbench owns

- explicit path-resolved language startup;
- one active resolved language context;
- source selection, scanning, compilation, and scenarios;
- diagnostic classification and run comparison;
- optional-profile loading and compatibility validation;
- run lifecycle, evidence, schemas, reports, and manifests;
- CLI, GUI, and local application state.

## Selected source owner owns

- GF source files and their source-control history;
- linguistic implementation and module content;
- decisions about editing, committing, branching, and releasing those sources.

Wordbench reads those sources in place. It does not copy them into its repository or claim ownership.

## Validation-profile owner owns

- required validation targets not derivable from source structure;
- checkpoint and scenario policy;
- reviewed inputs and golds;
- PGF expectations and release gates;
- profile-specific documentation and known limitations.

The profile cannot own runtime language facts or machine-local paths.

## Environment owner owns

- installed GF executable;
- local RGL and output overrides;
- state and cache locations;
- platform-specific execution values.

## `gf-portfolio` owns

- registration of several workspaces or published runs;
- cross-language aggregation and comparison;
- portfolio readiness and navigation;
- consumer-specific storage and adapters.

Allowed dependency direction:

```text
gf-portfolio → public versioned Wordbench artifacts
```

Forbidden dependency direction:

```text
GF Wordbench -X→ private gf-portfolio runtime, storage, or configuration
```

## Boundary tests

Tests must prove that Wordbench can start, validate, report, and run its suite without a root `project/` directory and without `gf-portfolio`.
