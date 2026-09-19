# GF Wordbench — Scope and Non-Goals

**Document ID:** `GF-WB-SCOPE-NON-GOALS`
**Status:** Normative boundary specification
**Last reviewed:** 2026-08-05

## In scope

GF Wordbench provides:

- explicit selection of one GF language directory or `.gf` source file;
- bounded RGL-root and language-context resolution;
- deterministic source enumeration and target selection;
- static scanning and source fingerprints;
- GF compilation, grammar loading, scenarios, and PGF builds;
- diagnostic normalization and causal classification;
- gold comparison and previous-run comparison;
- run evidence, summaries, manifests, and AI-ready handoff;
- optional validation profiles for advanced language-specific policy;
- CLI, GUI, and automation interfaces with identical core semantics.

## Selected source boundary

Selected GF sources are external input. Normal validation is read-only. Wordbench must not copy the language tree into a repository-root `project/` directory or require the source to live under Wordbench.

Supported standard selection:

```text
<rgl-root>/src/<language>/
<rgl-root>/src/<language>/<module>.gf
```

## Optional profile scope

Profiles are useful only for policy not already owned elsewhere:

- extra source filters;
- required entrypoints and checkpoints;
- scenarios, inputs, and golds;
- release targets, artifacts, and gates;
- known limitations and language-specific contracts.

Profiles do not own selected source paths, language identity, RGL roots, effective GF paths, executables, output roots, or application state.

## Non-goals

GF Wordbench is not:

- an RGL source mirror;
- a language source repository manager;
- a multi-language runtime dashboard;
- a portfolio manager;
- a replacement for GF parsing, type checking, or module resolution;
- a database or network service;
- a hidden filesystem crawler;
- an automatic gold updater during normal validation;
- a source-rewriting tool during ordinary runs.

## Portfolio boundary

Cross-workspace discovery, aggregation, comparison, trends, and readiness views belong to `gf-portfolio`. Wordbench must function and test without it.

## Capability rule

A source tree may be browse-ready or scan-ready without a validation profile or GF executable. Release readiness requires an explicit compatible profile and complete release evidence.

## Physical workspace rule

One installed Wordbench package may serve many languages sequentially. Separate physical clones or worktrees may be used for development convenience, but they are not required by the product model.
