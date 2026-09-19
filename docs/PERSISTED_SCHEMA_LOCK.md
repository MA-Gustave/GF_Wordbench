# GF Wordbench — Persisted Schema Lock

**Document ID:** `GF-WB-PERSISTED-SCHEMA-LOCK`
**Status:** Normative
**Last reviewed:** 2026-08-05

## 1. Scope

This lock governs versioned machine-readable state, optional validation profiles, run summaries, manifests, migrations, and path representation.

## 2. Identity invariants

- one run summary and manifest identify exactly one resolved language context;
- profile identity is separate from language identity;
- workspace paths and local absolute paths are not portable identity;
- schemas contain no `gf-portfolio` private registry or aggregation state.

## 3. Canonical schemas

| Artifact | Schema | Role |
|---|---|---|
| `.gf_wordbench_state.json` | `gf-wordbench.app-state/1.0` | disposable local state |
| explicit `project.toml` profile | `gf-wordbench.project/1.0` | optional validation policy; historical ID retained |
| `summary.json` | `gf-wordbench.run-summary/1.0` | one-run machine summary |
| `manifest.json` | versioned manifest schema | run-owned artifact index |

## 4. Optional profile schema

The `gf-wordbench.project/1.0` schema is interpreted as an optional validation profile. It must not be required for startup or used to own selected source paths, active language identity, RGL roots, effective GF paths, or output roots.

Legacy source-directory and GF-path fields are compatibility inputs only. Canonical writers omit them; migrations validate them against the explicit resolved context and report disagreement.

## 5. Path representation

- portable persisted paths are relative to their owning root;
- canonical separator is `/`;
- run artifact paths are run-relative;
- profile asset paths are profile-relative;
- local absolute paths appear only in explicitly classified local evidence or state;
- traversal, drive-relative paths, unsafe symlinks, and root escape are rejected.

## 6. Versioning

Breaking changes require a new major schema version, coordinated readers and writers, migrations or explicit non-migratable decisions, fixtures, release notes, and contract updates.

No new unversioned machine schema may be introduced.

## 7. Migration rules

Migrations:

- preserve source input;
- write canonical output separately or atomically;
- never guess ambiguous identity or path bases;
- report losses and warnings;
- never relabel weak or unknown evidence as stronger evidence;
- do not copy or rewrite selected GF sources.

## 8. Conformance

Schema tests must cover malformed input, unknown versions, deterministic serialization, path safety, migrations, stale artifacts, and operation without `gf-portfolio` or a root `project/` directory.
