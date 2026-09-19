# GF Wordbench — Validation Profile Model

**Document ID:** `GF-WB-PROJECT-MODEL`
**Status:** Normative; filename retained for compatibility
**Last reviewed:** 2026-08-05

## 1. Definition

A GF Wordbench validation profile is an optional, explicit, versioned policy bundle associated with one resolved language context.

It is not the language source tree, not the active-language authority, and not a mandatory repository partition.

## 2. Why profiles exist

The source tree can reveal files and candidate modules, but it does not safely declare all required scenarios, golds, checkpoints, expected artifacts, or release gates. A profile supplies those non-derivable requirements.

## 3. Canonical profile boundary

```text
<profile-root>/
├── project.toml
├── README.md
├── docs/
└── validation/
    ├── scenarios/
    ├── inputs/
    └── gold/
```

The profile root may be anywhere explicitly selected. `project/project.toml` is a compatibility convention, not a required root path. `templates/validation-profile/` is the reusable framework template.

## 4. Ownership

The profile owns:

- profile ID and version;
- expected-language compatibility assertion;
- extra source policy;
- required entrypoints and checkpoints;
- scenario registry, inputs, and golds;
- PGF targets and expected artifacts;
- release gates, known limitations, and documentation contracts.

The profile does not own:

- selected source path;
- language identity;
- RGL roots;
- source inventory mechanics;
- effective GF path;
- local executable or output paths;
- run history or application state.

## 5. Compatibility

A profile may be attached only when its compatibility assertions agree with the immutable `ResolvedLanguageContext`. A mismatch is a configuration error. The profile must not mutate the context to make the mismatch disappear.

## 6. Entrypoints and checkpoints

Detected entrypoints are context facts. Profile entrypoints and checkpoints are requirements.

Checkpoint order follows declared dependency order. Wordbench must not infer checkpoint policy from filenames.

## 7. Scenarios and golds

Scenario IDs are stable and unique. Scenario, input, and gold paths are profile-root-relative and contained. Required scenarios block their containing gate; optional scenarios remain visible but non-blocking unless explicitly promoted.

Golds are reviewed expectations. Normal validation never updates them.

## 8. Release profile

A release-capable profile declares enough policy to evaluate:

- required source and module targets;
- required checkpoints and scenarios;
- gold comparisons;
- PGF targets and expected artifacts;
- blocking issue policy;
- complete release gates.

A source-ready language without such a profile cannot claim Wordbench release readiness.

## 9. Lifecycle

Profile creation, migration, cloning, and reset affect only profile-owned files. They never copy, delete, reset, or rewrite the selected GF source tree unless the user invokes a separate explicitly authorized source operation outside normal Wordbench validation.

## 10. Portability

Portable profile content uses relative paths and contains no machine-local RGL root, GF executable, output root, user directory, drive-specific path, or run directory.

## 11. Enforcement

A profile is valid only when schema, identity, path containment, ordering, referenced assets, and release requirements are coherent with the resolved language context.
