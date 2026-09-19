# GF Wordbench — Data Model

**Document ID:** `GF-WB-DATA-MODEL`
**Status:** Normative conceptual model
**Last reviewed:** 2026-08-05

**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
## 1. Model graph

```text
ExplicitLanguageSelection
    → LanguageCandidate
    → ResolvedLanguageContext

ResolvedLanguageContext
    + ValidationProfile?
    + EnvironmentConfig
    + ExplicitRunOptions
    → ResolvedRunConfig
    → RunResult
    → RunSummary + ArtifactManifest
```

## 2. `ExplicitLanguageSelection`

Represents one user-supplied readable directory or `.gf` file. It is startup intent, not portable identity.

## 3. `LanguageCandidate`

A provisional non-executable model containing observed path facts, possible roots, module suffixes, entrypoint candidates, and structural diagnostics.

A candidate is not run authority.

## 4. `ResolvedLanguageContext`

The immutable active-language authority. Required conceptual fields include:

- `language_key`;
- `selected_path` and `selected_path_kind`;
- `language_directory`;
- `rgl_source_root` and optional `rgl_root`;
- optional selected file and focused target;
- available entrypoint candidates;
- source inventory or stable inventory reference;
- GF path requirements and provenance;
- capability statuses;
- resolution diagnostics and provenance.

Changing language, source roots, identity, or GF-path facts requires a new context and runtime.

## 5. `ValidationProfile`

An optional immutable policy model loaded explicitly. It may contain:

- profile ID, display name, version, and expected language-key assertion;
- additional source selection policy;
- required entrypoints and checkpoints;
- scenario registry and asset references;
- gold expectations;
- PGF targets and expected artifacts;
- release gates, limitations, and documentation references.

It must not contain authoritative selected paths, source roots, RGL roots, local executable paths, output roots, or application-state values.

## 6. `EnvironmentConfig`

Machine-local, observable configuration including GF executable, optional root overrides, output root, state path, platform, and timeouts.

## 7. `ResolvedRunConfig`

One immutable snapshot combining allowed values from the resolved context, profile, environment, and explicit run request. Every stage consumes this snapshot and must not independently re-resolve configuration.

## 8. `RunPaths`

Owns all generated paths for one run. Its values are derived from one run directory and are never reconstructed by consumers.

## 9. Results and evidence

`RunResult` records stage outcomes and causal diagnostics. `RunSummary` and `ArtifactManifest` persist versioned portable evidence for exactly one context and run.

## 10. Identity distinctions

```text
language identity     owned by ResolvedLanguageContext
profile identity      owned by ValidationProfile
run identity          owned by run lifecycle
workspace path        local environment fact
```

These identities must not be conflated.
