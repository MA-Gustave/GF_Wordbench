# GF Wordbench — Optional `project.toml` Validation-Profile Reference

**Document ID:** `GF-WB-CONFIG-PROJECT-TOML`
**Status:** Normative compatibility and profile reference
**Schema ID:** `gf-wordbench.project`
**Current schema version:** `1.0`
**Last reviewed:** 2026-08-05

## 1. Purpose

`project.toml` is an explicitly selected optional validation profile. It adds advanced validation and release policy to an already published `ResolvedLanguageContext`.

It is not a startup authority. It does not select, copy, relocate, or rename the active GF language.

Supported explicit locations include:

```text
<profile-root>/project.toml
<repository-root>/project/project.toml    # compatibility convention only
```

The reusable template is:

```text
templates/validation-profile/project.toml
```

Wordbench must not silently search ancestors and adopt the first `project.toml` it finds.

## 2. Authority boundary

The profile may own:

- profile identity and display metadata;
- an expected-language-key compatibility assertion;
- additional source include and exclude policy;
- required and release entrypoints;
- ordered checkpoints;
- required and optional scenarios;
- profile-owned inputs and reviewed golds;
- PGF targets and expected artifacts;
- release gates and known limitations.

The profile must not own:

- selected language path or active language identity;
- language directory, RGL source root, or RGL root;
- source inventory or source-enumeration algorithm;
- effective GF path or local GF executable;
- output root, state path, or run directory.

## 3. Schema identity

Canonical header:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"
```

The historical schema ID is retained for compatibility. Its current meaning is an optional validation profile. Renaming it requires a versioned schema migration and coordinated reader, writer, test, and documentation changes.

## 4. Canonical profile shape

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[profile]
id = "english-release"
name = "English release validation"

[compatibility]
expected_language_key = "rgl:english"

[selection]
include = []
exclude = []

[modules]
required_entrypoints = ["GrammarEng.gf"]
release_entrypoints = ["LangEng.gf"]
checkpoints = ["MorphoEng.gf", "SyntaxEng.gf"]

[validation]
required_scenarios = ["load", "parse", "linearize"]
optional_scenarios = ["generation", "morphology"]

[release]
requires_pgf = true
pgf_targets = ["LangEng.pgf"]
required_artifacts = []
required_gates = ["required-scenarios", "required-golds"]
```

All module paths are relative to the resolved language directory. Scenario, input, gold, and other profile-owned asset paths are relative to the explicitly selected profile root.

## 5. Field semantics

### 5.1 `[profile]`

- `id`: stable profile identifier, separate from active-language identity;
- `name`: human-readable profile name.

### 5.2 `[compatibility]`

- `expected_language_key`: optional assertion checked against the already resolved language context. An empty value means no additional key assertion.

This field can reject an incompatible attachment. It cannot select or rename a language.

### 5.3 `[selection]`

- `include`: additional explicit inclusion policy within approved source roots;
- `exclude`: additional exclusion policy within approved source roots.

The canonical selection service remains authoritative for enumeration, containment, deduplication, filtering semantics, and ordering.

### 5.4 `[modules]`

- `required_entrypoints`: modules required by profiled validation;
- `release_entrypoints`: additional modules required by release validation;
- `checkpoints`: ordered development-layer proof targets.

Detected entrypoint candidates remain resolved-context facts. Profile entries state what a particular validation policy requires.

### 5.5 `[validation]`

- `required_scenarios`: scenario IDs whose failure blocks the applicable gate;
- `optional_scenarios`: visible scenarios that are non-blocking unless another explicit policy promotes them.

### 5.6 `[release]`

- `requires_pgf`: whether release validation requires PGF construction;
- `pgf_targets`: required PGF targets;
- `required_artifacts`: additional required artifact identifiers or relative paths;
- `required_gates`: explicit release-gate identifiers.

## 6. Prohibited ownership fields

Canonical profiles do not contain fields such as:

```text
language_path
language_directory
source_root
rgl_source_root
rgl_root
source inventory
gf_executable
gf_path
path_parts
output_root
state_path
run_dir
```

Historical project documents containing `[project]`, `[sources]`, `[gf]`, `sources.directory`, or `gf.path_parts` are legacy compatibility inputs. Readers may accept them only through an explicit migration path that does not redirect the resolved language context. Canonical writers and templates emit the `[profile]` shape above.

## 7. Validation rules

Before use, Wordbench verifies:

- exact schema ID and supported version;
- required tables and field types;
- unique, non-empty declared lists;
- resolved placeholders in non-template profiles;
- compatibility with the resolved language key;
- containment of profile-owned paths;
- deterministic module and scenario order;
- required asset existence for the requested mode;
- complete release requirements in release mode;
- absence of machine-local path ownership fields.

Unknown fields are rejected in strict mode.

## 8. Loading and mutation

A profile is loaded only when explicitly selected by the user, CLI, automation, or another reviewed configuration contract. It is read-only during normal validation.

Gold updates, profile migration, and profile initialization are separate authorized write operations. None of them rewrites the externally selected GF source tree.

## 9. Governing rule

> A validation profile states what must be validated; `ResolvedLanguageContext` states which language and sources are active.
