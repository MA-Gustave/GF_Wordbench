# GF Wordbench — Application State Reference

**Document ID:** `GF-WB-CONFIG-APPLICATION-STATE`
**Status:** Normative
**Persisted schema:** `gf-wordbench.app-state/1.0`
**Canonical artifact:** `.gf_wordbench_state.json`
**Last reviewed:** 2026-08-05

## 1. Purpose

Application state stores disposable machine-local convenience values between sessions.

Appropriate values include:

- last successfully selected language path;
- recent local paths;
- UI preferences;
- last selected mode;
- non-authoritative tool or output preferences;
- pointer to a recent run.

## 2. Non-authority rule

State does not define:

- active language identity;
- source roots or source-selection policy;
- entrypoints, checkpoints, scenarios, or golds;
- release criteria;
- effective GF path;
- a project or portfolio registry.

A remembered selected path must be fully revalidated before a new `ResolvedLanguageContext` is published.

## 3. Lifecycle

State is:

- machine-local;
- optional;
- disposable;
- loaded defensively;
- written atomically;
- versioned;
- safe to delete without damaging sources, profiles, or runs.

Corrupt or unsupported state must produce a bounded warning and safe defaults, not a startup crash or hidden fallback.

## 4. Path rules

State may contain absolute local paths because it is non-portable local configuration. Those paths must never be promoted to portable language identity or copied into validation profiles or public artifacts without explicit evidence classification.

## 5. Language switching

State may remember the most recent successful selected path. Switching language disposes the current runtime, resolves the new path, and writes state only after successful resolution according to the state contract.

## 6. Portfolio boundary

State must not contain multi-workspace inventory, cross-language aggregation, or `gf-portfolio` private fields.
