# GF Wordbench — Start Here

**Document ID:** `GF-WB-START-HERE`
**Status:** Normative navigation entrypoint
**Last reviewed:** 2026-08-05

## Current product model

GF Wordbench opens and validates GF language sources **where they already exist**.
Normal startup begins from one explicit input:

```text
one readable GF language directory
or
one readable .gf source file
```

For a standard RGL checkout, the selected source normally remains under:

```text
<rgl-root>/src/<language>/
```

Wordbench does not copy that language tree into its own repository. Normal validation is read-only for the selected source tree.

Wordbench resolves the selected path into one immutable `ResolvedLanguageContext`, performs validation, and writes generated evidence under a separate output root:

```text
<output-root>/<language-key>/run_<run-id>/
```

The default output root may be `<framework-root>/_gf_wordbench`, but it must not overlap the selected source tree or the RGL checkout.

## Optional validation profile

A validation profile is optional. It is attached explicitly only when advanced policy is needed, such as:

- source include or exclude rules beyond safe framework defaults;
- required entrypoints and checkpoints;
- scenarios, inputs, and reviewed golds;
- PGF targets and expected artifacts;
- release gates and language-specific validation documentation.

A profile cannot own or replace:

- the selected language path;
- the active language identity;
- the RGL root or source root;
- the effective GF path;
- the GF executable or output root;
- the source enumeration algorithm;
- application state.

`project/project.toml` remains a supported **explicit profile location** for compatibility. It is not required at repository root and is not the startup authority. The reusable template is `templates/validation-profile/`.

## Documentation precedence

Read these documents in this order when rules overlap:

1. accepted ADRs, especially `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`;
2. `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`;
3. persisted, interfile, and external-tool contract locks;
4. architecture and configuration owner documents;
5. operation-specific references.

Historical documents may describe a workspace-coupled `project/` model. Those clauses are not current behavior when they conflict with ADR-0015.

## Main references

```text
docs/PRODUCT_OVERVIEW.md
docs/SCOPE_AND_NON_GOALS.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
```

## Governing summary

```text
external selected GF source tree
        ↓ read-only resolution
ResolvedLanguageContext
        + optional explicit ValidationProfile
        ↓ one resolved run configuration
validation and GF execution
        ↓
language-scoped generated run directory
```
