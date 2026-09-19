# GF Wordbench — Repository Structure

**Document ID:** `GF-WB-REPOSITORY-STRUCTURE`
**Status:** Normative repository layout
**Last reviewed:** 2026-08-05

## 1. Design rule

The Wordbench repository contains the permanent language-neutral framework, documentation, tests, reusable optional-profile templates, and optionally generated local evidence. It does not contain the active RGL language source tree as a required repository partition.

## 2. Canonical tree

```text
GF_Wordbench/
├── pyproject.toml
├── src/gf_wordbench/              permanent Python framework
├── tests/                         framework and contract tests
├── docs/                          framework documentation
├── scripts/                       maintenance and validation scripts
├── tools/                         developer tooling
├── templates/validation-profile/ reusable optional-profile template
├── .gf_wordbench_state.json       optional disposable local state
└── _gf_wordbench/                 default generated output root, normally ignored

<external-rgl-or-source-tree>/
└── src/<language>/                user-selected GF sources
```

A repository-local profile may exist at `project/project.toml`, but `project/` is optional and must not be required by repository or startup checks.

## 3. Framework ownership

`src/gf_wordbench/` owns:

- language probing and runtime composition;
- deterministic source selection;
- scanning and validation orchestration;
- GF path resolution and external process execution;
- scenarios, gold comparison, and release gates;
- run paths, reporting, schemas, migrations, CLI, GUI, and state.

Framework code must not contain hard-coded active-language modules, source paths, or linguistic policy.

## 4. External selected sources

The selected language directory is external input. Wordbench reads it through a resolved context and does not move, duplicate, initialize, reset, or archive it during normal operation.

## 5. Optional profile template

```text
templates/validation-profile/
├── project.toml
├── README.md
├── docs/
└── validation/
    ├── scenarios/
    ├── inputs/
    └── gold/
```

The template describes advanced validation policy. Initializing a profile creates a separate profile directory chosen by the user. It does not create or copy the language source tree.

## 6. Generated output

```text
<output-root>/<language-key>/run_<run-id>/
```

Generated directories contain run-owned artifacts only. They must be new, writable, and outside selected source, RGL, and profile roots.

## 7. Application state

`.gf_wordbench_state.json` is machine-local and disposable. It may remember the last selected path and UI preferences but cannot own language identity or validation policy.

## 8. Path ownership

| Path | Owner | Mutability during normal validation |
|---|---|---|
| selected language path | user / RGL checkout | read-only |
| optional profile root | profile owner | read-only |
| output root and run directory | Wordbench run-path owner | writable |
| state path | Wordbench application state | atomically writable |
| template root | framework maintainers | unchanged by profile initialization |

## 9. Prohibited repository assumptions

Tests and scripts must not assert that:

- `project/` exists;
- `project/project.toml` exists;
- GF sources are inside Wordbench;
- one language requires one repository clone;
- generated runs may be written inside RGL sources.
