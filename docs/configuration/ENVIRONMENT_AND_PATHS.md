# GF Wordbench — Environment and Paths

**Document ID:** `GF-WB-CONFIG-ENVIRONMENT-PATHS`  
**Status:** Normative configuration and path-resolution specification  
**Applies to:** path-resolved language startup, one resolved language context per session, CLI, GUI, automation, GF invocation, optional validation profiles, run creation, reporting, migration and tests  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Architectural authority:** `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`  
**Configuration authorities:** `docs/configuration/APPLICATION_STATE_REFERENCE.md`, `docs/configuration/PROJECT_TOML_REFERENCE.md` for optional validation profiles  
**Boundary authorities:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`  
**Specification version:** `2.0`  
**Last reviewed:** `2026-07-30`

---

## 1. Purpose

This document defines how GF Wordbench represents, discovers, resolves,
validates, persists and reports environment-dependent values and filesystem
paths under the path-resolved startup model established by ADR-0015.

It establishes one shared model for:

- the GF Wordbench framework root;
- the explicit language path selected by the user;
- the resolved language directory;
- the RGL source root and checkout root;
- an optional validation-profile root and configuration file;
- the GF executable;
- the ordered effective GF search path;
- the output root;
- language-scoped run directories;
- raw and generated artifact paths;
- application-state location;
- temporary paths;
- environment-variable overrides;
- Windows and POSIX path behavior;
- path containment;
- path migration;
- path-related errors;
- path-related tests.

The objective is portability without requiring a global language catalog or a
mandatory project bundle.

A user supplies one language directory or `.gf` file. Wordbench derives only
bounded candidate facts from that explicit path and validates them through its
existing selection, path, preflight, GF and diagnostic boundaries.

---

## 2. Core rule

> The user selects one source location; Wordbench resolves one contained,
> immutable language context; every executable operation consumes that same
> context and the same effective GF path.

Path representation follows these rules:

```text
portable language identity
    → relative to the resolved RGL source root

optional validation-profile assets
    → relative to validation_profile_root

run artifacts
    → relative to run_dir

machine-local tools and roots
    → resolved absolute environment paths
```

No path may be interpreted without a documented base.

No consumer may reconstruct an owned path through duplicated filename constants.

No machine-local absolute path may become the portable identity of a language.

Discovery may propose a candidate path. It does not create executable authority
until `ResolvedLanguageContext` is published successfully.

---

## Workspace and product boundary

One running GF Wordbench session has zero or one resolved language context. One
ordinary run records exactly one portable language identity and one resolved
source context.

The same installed Wordbench application may open several languages
sequentially. Switching language destroys the current runtime and resolves a new
context. It does not merge languages in one run or maintain several active
language contexts simultaneously.

Environment and path configuration must not create:

- a simultaneously active multi-language registry;
- cross-language result aggregation inside one ordinary run;
- a filesystem-wide RGL search;
- a hidden language selection based on branch name, output directory or prior
  run filenames;
- a dependency on `gf-portfolio` configuration, schemas, storage or runtime.

The independent `gf-portfolio` product may read finalized, public, versioned run
artifacts. It does not participate in language probing, path precedence, GF
search-path construction, run-directory creation or application-state
resolution.

---

## 3. Related authority

The following documents remain authoritative for their domains:

```text
docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/DATA_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/gf/GF_PATH_RESOLUTION.md
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
```

Priority when rules overlap:

1. accepted ADRs govern architectural decisions;
2. `DOCUMENTATION_ALIGNMENT_LOCK.md` governs cross-document interpretation and
   the Wordbench/Portfolio boundary;
3. `PERSISTED_SCHEMA_LOCK.md` governs canonical persisted path representation;
4. `EXTERNAL_TOOL_CONTRACT_LOCK.md` governs executable, working-directory and GF
   command boundaries;
5. `INTERFILE_CONTRACT_LOCK.md` governs ownership and dependency direction;
6. this document governs environment and path resolution;
7. report and operation-specific references govern presentation details.

`PROJECT_TOML_REFERENCE.md` governs only an explicitly loaded validation profile.
It is not the normal language-startup authority.

---

## 4. Scope

This specification governs:

- selected-language-path precedence;
- optional validation-profile precedence;
- environment-variable names;
- path input parsing;
- path expansion policy;
- relative-path bases;
- path normalization;
- path existence and type checks;
- path containment;
- symlink and junction handling;
- executable discovery;
- bounded RGL root resolution;
- language-directory resolution;
- GF search-path construction;
- output-root selection;
- language-scoped run-directory construction;
- temporary files;
- persisted path representation;
- legacy path migration;
- Windows drive, UNC, separator and case behavior;
- POSIX behavior;
- environment inheritance;
- path evidence;
- path error reporting;
- path test coverage.

---

## 5. Exclusions

This specification does not define:

- GF module-resolution semantics;
- GF compiler-option compatibility;
- a full parser for GF source syntax;
- a global manifest of RGL languages;
- language-specific linguistic architecture;
- report prose;
- scenario command syntax;
- operating-system access-control administration;
- network filesystem administration;
- package installation;
- remote execution;
- container orchestration;
- cloud storage;
- arbitrary environment-variable expansion in source or profile files;
- Portfolio workspace discovery or aggregation.

GF remains authoritative for parsing, type checking, compilation and module
resolution.

---

## 6. Configuration ownership

Environment and path values are divided by owner.

### 6.1 Projects module

The `projects` module owns the path-resolved language application use case.

It owns:

- accepting one explicit selected language path from an entrypoint;
- coordinating `LanguageProbeService`;
- deriving the candidate language directory;
- locating a bounded RGL source-root ancestor;
- coordinating source enumeration through the existing selection service;
- classifying standard module-role candidates;
- loading an optional explicit validation profile;
- validating profile compatibility with the selected source context;
- producing one immutable `ResolvedLanguageContext`.

It does not:

- implement a second recursive file selector;
- implement a second GF path resolver;
- launch GF directly;
- parse GF diagnostics independently;
- own run directories or report paths;
- discover arbitrary projects across the filesystem.

### 6.2 Resolved language context

The resolved language context owns runtime source identity and boundaries.

Required path facts include:

```text
selected_language_path
selected_path_kind
language_directory
rgl_source_root
rgl_root, when resolved
selected_file, when applicable
portable_language_key
candidate or selected entrypoints
effective GF path requirements and provenance
```

These facts are immutable after runtime composition.

A change to the selected language path, source root, GF path requirements or
validation profile requires a new resolution and a new runtime.

### 6.3 Optional validation profile

An explicitly loaded validation profile may own portable declarations such as:

```text
source include and exclude rules
required entrypoints
required checkpoints
scenario registrations
input paths
gold paths
release targets
release gates
project-specific documentation references
```

The canonical compatibility filename may remain:

```text
project.toml
```

Profile-owned paths are relative to `validation_profile_root`. The profile is not
required for browsing, static scanning or targeted compilation of a standard RGL
language directory.

### 6.4 Application configuration and state adapter

Machine-local values are supplied through explicit invocation values, documented
environment variables or disposable application state.

Examples:

- last successfully selected language path;
- last explicitly selected validation profile;
- GF executable;
- optional RGL root override for a nonstandard layout;
- output root;
- optional state-file override.

These values may be absolute. They remain non-authoritative until revalidated.

### 6.5 Runs module

The `runs` module owns run identity, the run directory and immutable run-path
allocation.

Examples:

- language scope directory;
- run directory;
- raw evidence directories;
- temporary directory;
- artifact directories;
- per-file and per-scenario evidence roots.

Run-owned paths are derived once per run.

### 6.6 Reporting module

The `reporting` module owns canonical report and manifest paths supplied through
the run-path model.

Examples:

- `summary.json`;
- `summary.md`;
- `AI_READY.md`;
- aggregate logs;
- detail reports;
- `manifest.json`.

Consumers receive owned paths from the run context and never reconstruct them
through duplicated filename constants.

### 6.7 Adapters

Filesystem, process, state and platform adapters implement path operations
through application ports. Domain and application rules do not depend on GUI
widgets, CLI parser objects, operating-system process APIs or private
`gf-portfolio` state.

---

## 7. Canonical path classes

Every path field belongs to exactly one path class.

```text
framework path
language-source path
validation-profile-owned path
run-owned path
environment path
temporary path
external evidence path
```

A field must not silently change class.

---

## 8. Framework paths

Framework paths point inside the installed or checked-out GF Wordbench
framework.

Examples:

```text
docs/
application package/
tests/
templates/project/
```

Framework paths are resolved against `framework_root`.

They must not be stored as language-source paths.

Optional project templates may be used only during explicit initialization or
profile-authoring operations. Normal path-resolved startup does not depend on
them.

---

## 9. Language-source paths

Language-source paths identify files in the selected GF language source tree.

Examples:

```text
english
english/LangEng.gf
english/AdjectiveEng.gf
```

Portable representation is relative to `rgl_source_root`, with `/` separators.

Canonical rules:

- no drive letter;
- no UNC prefix;
- no unresolved `..`;
- no user-home alias;
- no inline environment variable;
- no backslash in canonical persisted output;
- preserve Unicode and case;
- containment beneath the resolved `rgl_source_root`;
- one run records one language directory.

When a selected source does not belong to a standard RGL checkout, an explicit
profile may define another approved source base. That base is recorded with
provenance and does not become a global RGL root.

---

## 10. Validation-profile-owned paths

Profile-owned paths identify portable, source-controlled validation policy and
assets.

Examples:

```text
project.toml
validation/scenarios/parse.gfs
validation/inputs/parse.txt
validation/gold/parse.gold
docs/VALIDATION_SPEC.md
```

Canonical persistence rules:

- relative to `validation_profile_root`;
- `/` separators;
- no drive letter;
- no UNC prefix;
- no `..` after normalization;
- no user-home alias;
- no inline environment variable;
- empty path only when the field explicitly permits it.

A profile path must not silently redirect the selected language to another
source tree.

---

## 11. Run-owned paths

Run-owned paths identify artifacts inside one run directory.

Examples:

```text
summary.json
raw/compile/LangEng.stdout.txt
raw/scenarios/parse.out
artifacts/pgf/Lang.pgf
```

Canonical persistence rules:

- relative to `run_dir`;
- `/` separators;
- no drive letter;
- no parent escape;
- deterministic filename;
- one owning writer;
- no collision with another artifact owner.

---

## 12. Environment paths

Environment paths identify machine-local locations.

Examples:

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl
C:/work/gf-rgl/src
C:/work/gf-rgl/src/english
C:/work/gf-wordbench-runs
```

Environment paths may be absolute.

Rules:

- resolve before execution;
- record the actual resolved value when it materially affects evidence;
- use `/` separators in canonical persisted text where practical;
- accept native separators as user input;
- do not copy them into portable profile fields;
- do not infer semantic language identity only from their absolute text;
- revalidate remembered state values on every load.

---

## 13. Temporary and external evidence paths

Temporary paths exist only during one operation or run.

Examples:

```text
run_<id>/.tmp/
summary.json.tmp
manifest.json.tmp
scenario-input.tmp
```

Temporary paths:

- are not canonical final artifacts;
- are excluded from the manifest unless a failure-retention policy catalogs
  them explicitly;
- remain inside an owned temporary root;
- are never placed in the selected language source directory;
- are cleaned on successful finalization;
- may remain after abnormal termination only with an explicit recovery marker.

External evidence paths point outside owned source, profile and run roots but are
recorded for traceability.

Examples:

```text
resolved GF executable
explicit external validation profile
explicit previous-run summary
```

They are read-only unless an operation explicitly owns them, may be redacted in
portable exports and must never be followed blindly from diagnostic text.

---

# 14. Root model

The resolved path model includes:

```text
framework_root
selected_language_path
language_directory
rgl_source_root
rgl_root
selected_file
validation_profile_root
validation_profile_path
gf_executable
gf_search_paths
output_root
language_output_root
run_dir
state_path
temporary_root
```

Optional values are `null` when not applicable.

Each value has one owner and one documented derivation.

---

## 15. `framework_root`

`framework_root` is the root of the current GF Wordbench installation or
checkout.

Expected contents may include:

```text
application package/
docs/
tests/
templates/
```

Resolution order:

1. installed package or resource metadata where applicable;
2. repository root derived from launcher or package location;
3. explicit developer-test fixture.

`framework_root` must not be derived from the process current working directory
alone.

---

## 16. `selected_language_path`

`selected_language_path` is the exact file or directory asserted by the current
caller.

Accepted forms:

```text
<rgl-root>/src/<language-directory>
<rgl-root>/src/<language-directory>/<module>.gf
```

Examples:

```text
C:/work/gf-rgl/src/english
C:/work/gf-rgl/src/english/LangEng.gf
C:/work/gf-rgl/src/english/AdjectiveEng.gf
```

Rules:

- explicit invalid input fails closed;
- a file selection must identify a readable regular `.gf` file;
- a directory selection must identify a readable directory;
- the exact selected file remains the focused target when applicable;
- state may remember the path but does not make it authoritative;
- no fallback to another language occurs when validation fails.

---

## 17. `language_directory`

Derivation:

```text
selected directory → selected directory
selected .gf file  → selected file parent
```

The directory is then validated and enumerated through the existing source
selection service.

Rules:

- contains at least one eligible `.gf` source for `source-ready` status;
- must remain within the approved source root after root resolution;
- is read-only during normal startup and validation;
- is not replaced silently by a detected sibling directory;
- is immutable for the lifetime of the resolved context.

---

## 18. `rgl_source_root`

`rgl_source_root` is the nearest validated ancestor representing the RGL source
root.

Standard form:

```text
<rgl-root>/src
```

Example:

```text
C:/work/gf-rgl/src
```

Resolution is bounded to ancestors of the selected path. Wordbench does not
search unrelated drives, user profiles or arbitrary directory trees.

Acceptance requires:

- the selected language directory is contained beneath the candidate root;
- the candidate satisfies the supported standard RGL source-layout contract;
- no nearer ancestor satisfies that contract more precisely;
- symlink or junction resolution preserves approved containment.

A nonstandard source tree requires an explicit override or validation profile.

---

## 19. `rgl_root`

`rgl_root` is the checkout root that contains `rgl_source_root`.

Standard derivation:

```text
rgl_root = rgl_source_root.parent
```

Example:

```text
C:/work/gf-rgl
```

Rules:

- machine-local;
- normally derived from the selected language path;
- may be asserted explicitly for a nonstandard layout;
- an explicit root must contain the selected source context;
- recorded when it affects execution or evidence;
- never discovered through an unbounded filesystem search.

---

## 20. `validation_profile_root` and `validation_profile_path`

These values are optional.

Canonical explicit profile example:

```text
validation_profile_root = C:/work/my-english-validation
validation_profile_path = C:/work/my-english-validation/project.toml
```

Rules:

- loaded only when explicitly selected, supplied or accepted through documented
  compatibility behavior;
- no arbitrary ancestor search for `project.toml`;
- profile-owned paths resolve relative to `validation_profile_root`;
- profile source declarations must agree with the selected language context;
- conflicts are configuration errors;
- absence of a profile does not block source browsing, static scan or targeted
  compilation.

---

## 21. `gf_executable`

`gf_executable` is the exact native executable used for GF-backed operations.

Examples:

```text
C:/Program Files/GF/bin/gf.exe
/usr/local/bin/gf
```

Rules:

- resolve to an explicit path before a GF-backed operation;
- regular-file and launch validation are platform-aware;
- pass executable separately from arguments;
- do not silently substitute after configuration finalization;
- record the actual path in run metadata;
- version probing uses this exact path;
- absence does not block `source-ready` or `scan-ready` capability.

---

## 22. `gf_search_paths`

`gf_search_paths` is the ordered structured list passed to GF or used to build
the GF path option.

It is derived from:

```text
language_directory
standard shared RGL requirements supported by the existing resolver
explicit source directives exposed through approved contracts
optional validation-profile path requirements
bounded exact missing-module remediation accepted by policy
```

The list is structured internally. The joined command-line representation is
derived only at the GF command boundary.

Wordbench must not add every directory beneath `rgl_source_root`.

---

## 23. `output_root` and `language_output_root`

`output_root` contains language-scoped run directories.

Canonical default:

```text
<framework_root>/_gf_wordbench
```

A user may select another local directory.

`language_output_root` is derived from a safe, deterministic representation of
the portable language key.

Example:

```text
<output_root>/rgl_english
```

Rules:

- output root must be writable before a run starts;
- output root must not equal or be inside selected source directories;
- output root should not be inside the RGL checkout;
- one language scope never reuses another language's run directory;
- existing runs are not overwritten.

---

## 24. `run_dir`

Canonical form:

```text
<language_output_root>/run_<run-id>
```

Example:

```text
C:/work/gf-wordbench-runs/rgl_english/run_20260730_204500
```

Rules:

- created exclusively for one run;
- collision produces a deterministic numeric suffix;
- never reuse a non-empty prior run directory;
- contains only run-owned artifacts and temporary files;
- fixed for the lifetime of the run;
- all `RunPaths` values derive from it.

---

## 25. `state_path` and `temporary_root`

Canonical state default:

```text
<framework_root>/.gf_wordbench_state.json
```

Rules:

- machine-local;
- disposable;
- written atomically;
- never treated as language or profile authority;
- deleting it must not damage source, profiles or runs;
- canonical writer uses only the current state schema.

Canonical run-local temporary root:

```text
<run_dir>/.tmp
```

The operating-system temporary directory may be used only when same-filesystem
atomicity, owned containment and persistent evidence are not required.

---

# 26. Canonical environment variables

GF Wordbench recognizes the following path-related variables under this
specification:

```text
GF_WORDBENCH_LANGUAGE_PATH
GF_WORDBENCH_VALIDATION_PROFILE
GF_WORDBENCH_GF_EXE
GF_WORDBENCH_RGL_ROOT
GF_WORDBENCH_OUTPUT_ROOT
GF_WORDBENCH_STATE_PATH
```

These names are framework configuration contracts.

Adding, renaming or removing one requires documentation and compatibility
review.

---

## 27. Environment-variable table

| Variable | Meaning | Required | Canonical target |
|---|---|---:|---|
| `GF_WORDBENCH_LANGUAGE_PATH` | Selected language directory or `.gf` file | No | Existing readable path |
| `GF_WORDBENCH_VALIDATION_PROFILE` | Optional profile file or root | No | Explicit profile path |
| `GF_WORDBENCH_GF_EXE` | GF executable | No | `gf.exe` or `gf` file |
| `GF_WORDBENCH_RGL_ROOT` | Explicit RGL checkout or source-root override | No | Root containing selected language context |
| `GF_WORDBENCH_OUTPUT_ROOT` | Parent of language-scoped run directories | No | Writable directory |
| `GF_WORDBENCH_STATE_PATH` | Application state file | No | JSON file path |

An unset variable contributes no value.

An empty variable is treated as unset. A different empty-value meaning requires
an explicit configuration-contract revision.

---

## 28. No inline interpolation

Canonical source and profile configuration does not expand inline path
expressions such as:

```text
%USERPROFILE%\gf
${HOME}/gf
$GF_ROOT/src
~/gf
```

Rules:

- portable profile files contain literal relative paths;
- application state contains resolved absolute machine paths;
- environment variables override complete configuration values;
- CLI input may be expanded only at the documented user-input boundary;
- the resolved path, not the original expression, enters the resolved context.

---

## 29. Unknown environment variables

Variables beginning with `GF_WORDBENCH_` but not documented here must not
silently alter behavior.

Bootstrap may ignore them, warn in strict configuration mode or reject them in
an explicit environment-validation command. It must not guess their meaning.

---

## 30. Deprecated environment variables

The catalog-era or project-root variable:

```text
GF_WORDBENCH_PROJECT_ROOT
```

is deprecated as a startup selector.

A compatibility adapter may interpret it only as an explicit validation-profile
root during a documented migration period.

Deprecated variables must define:

```text
old name
new behavior or replacement
precedence
warning policy
removal target
tests
```

Canonical writers and examples use current names.

---

# 31. Configuration precedence

Configuration precedence is resolved per field.

General order:

```text
explicit invocation value
        ↓
GF Wordbench environment variable
        ↓
valid application-state convenience value
        ↓
bounded derivation from the explicit selected path
        ↓
canonical default when documented
        ↓
configuration error when required
```

A higher-precedence invalid explicit value produces an error. It does not
silently fall through.

Optional validation-profile fields are resolved separately from base language
startup.

---

## 32. Selected-language-path precedence

```text
1. explicit CLI language path
2. explicit current GUI language path
3. GF_WORDBENCH_LANGUAGE_PATH
4. application-state last_selected_language_path after user chooses “Open last language”
5. failure or interactive selection
```

There is no implicit framework-local active language default.

The normal GUI always presents the introduction surface before composing the
main runtime.

---

## 33. Validation-profile precedence

```text
1. explicit CLI profile path
2. explicit current GUI profile path
3. GF_WORDBENCH_VALIDATION_PROFILE
4. application-state last_selected_validation_profile when explicitly reused
5. no profile
```

An invalid explicit profile is an error. Its failure does not silently select a
different profile.

No profile is a valid state for source browsing, static scan and targeted
compilation.

---

## 34. GF-executable precedence

```text
1. explicit CLI GF executable
2. explicit current GUI GF executable
3. GF_WORDBENCH_GF_EXE
4. application-state environment.gf_executable
5. optional PATH discovery
6. unavailable capability
```

If `PATH` discovery succeeds, the discovered token is resolved to an explicit
path and recorded.

A missing executable marks GF-backed capabilities unavailable; it does not make
the selected source context invalid.

---

## 35. RGL-root precedence

```text
1. explicit CLI or GUI RGL root assertion
2. GF_WORDBENCH_RGL_ROOT
3. bounded derivation from selected_language_path ancestors
4. application-state last_rgl_root as a validated hint
5. explicit nonstandard-layout remediation
6. failure when a standard RGL root is required
```

Every candidate must contain the selected language context.

Broad recursive filesystem search is prohibited.

---

## 36. Output-root and state-path precedence

Output root:

```text
1. explicit CLI output root
2. explicit current GUI output root
3. GF_WORDBENCH_OUTPUT_ROOT
4. application-state environment.output_root
5. <framework_root>/_gf_wordbench
6. failure
```

State path:

```text
1. explicit application startup option
2. GF_WORDBENCH_STATE_PATH
3. <framework_root>/.gf_wordbench_state.json
```

The state file does not select itself through values stored inside itself.

---

## 37. Profile-field precedence

Profile-owned fields use:

```text
explicit validation-profile value
        ↓
documented profile-schema default
        ↓
configuration error when required by the requested capability
```

Environment variables must not override portable profile facts such as:

- required entrypoints;
- required checkpoints;
- required scenarios;
- gold references;
- release requirements.

A command may select a subset for a non-release run without rewriting profile
policy.

---

## 38. Explicit-value failure rule

An explicitly supplied path is an assertion by the caller.

If invalid:

- report the invalid value;
- report its source;
- stop resolution for that field;
- do not silently use state, environment, catalog data or another sibling path.

---

## 39. Resolved-value provenance

Every significant resolved path retains provenance.

Canonical values include:

```text
explicit_cli
explicit_gui
environment
state
derived_from_selected_path
validation_profile
default
bounded_remediation
```

Reports may show provenance in diagnostic or strict modes.

---

# 40. Optional validation-profile path rules

A validation profile adds policy to an already selected source context.

It must not become a second hidden language selector.

Canonical path fields may include:

```text
[profile].root
[sources].directory or source identity assertion
[sources].glob
[gf].path_parts
[modules].entrypoints
[modules].checkpoints
scenario, input and gold asset paths
```

Every profile path has an explicit base.

---

## 41. `[profile].root`

Canonical value for a profile stored at its root:

```toml
[profile]
root = "."
```

A different value requires documented containment and no ambiguous double-root
interpretation.

The selected `validation_profile_root` remains the directory that owns the
profile contract.

---

## 42. Source assertion

A profile may assert a language source path or portable language key.

The assertion must agree with the path-resolved context.

Allowed behavior:

```text
profile source matches selected language
→ profile may load

profile source differs from selected language
→ configuration error
```

The profile cannot redirect startup to a different language silently.

---

## 43. Source globs

A source glob is a filename-matching expression, not a path root.

Rules:

- evaluated below the resolved `language_directory` or an explicitly approved
  profile source base;
- must not escape its base;
- recursive behavior is explicit;
- path separators follow the file-selector contract;
- result ordering is normalized by the existing selection service.

---

## 44. Entrypoint paths

Without a validation profile, standard module filenames may be presented as
candidate roles. They are not mandatory policy.

With a profile, entrypoints are explicit portable paths or filenames.

Resolution rules:

- bare filename resolves under `language_directory`;
- a profile-relative path resolves against `validation_profile_root` only when
  the schema explicitly defines that base;
- absolute entrypoint is rejected in portable profile configuration;
- missing required profile entrypoint is a capability or release error;
- a user-selected `.gf` file remains the focused target even when another
  entrypoint candidate exists.

---

## 45. Checkpoint paths

Checkpoints are optional unless an explicit validation profile requires them.

Declared order is semantically significant for reporting and validation order.
The resolver must not sort explicitly ordered checkpoints.

Without a profile, Wordbench may browse and scan all selected sources without
inventing a mandatory checkpoint list.

---

## 46. Scenario paths

Default profile-owned scenario form:

```text
validation/scenarios/<scenario-id>.gfs
```

Rules:

- `.gfs` extension;
- profile-contained;
- read-only during normal validation;
- no inline environment expansion;
- stable scenario identity independent of absolute path;
- scenario absence does not block source-ready or compile-ready capability.

---

## 47. Input paths

Validation inputs normally resolve under:

```text
validation/inputs/
```

A declared path outside that directory may be accepted only when still contained
inside `validation_profile_root`, documented by the profile and read-only during
normal validation.

Absolute input paths are prohibited in portable profile configuration.

---

## 48. Gold paths

Default profile-owned gold form:

```text
validation/gold/<scenario-id>.gold
```

Rules:

- profile-contained;
- read-only during normal validation;
- no environment interpolation;
- no output-root or run-relative reference;
- updated only through the explicit gold-update operation;
- absence blocks only a capability or release gate that requires that gold.

---

# 49. GF search-path model

GF search paths are ordered because order can affect module resolution.

The effective list is built once and reused by compilation, scenarios and PGF
construction within one run.

Potential inputs are:

```text
language_directory
standard shared RGL aliases supported by the existing resolver
approved source-local directives
optional profile path_parts
accepted bounded missing-module remediation
```

No catalog is consulted during normal resolution.

---

## 50. Language and shared path parts

The language directory is the first source-local candidate unless an approved GF
contract requires another ordering.

Standard shared aliases may include resolver-owned names such as:

```text
abstract
api
common
prelude
```

Family directories such as `romance`, `scandinavian`, `bantu` or `hindustani`
are not appended globally. They enter the path only through explicit profile
requirements, approved source directives or bounded exact missing-module
remediation.

---

## 51. RGL aliases

Reserved RGL aliases resolve beneath `rgl_source_root`.

Examples:

```text
abstract → <rgl_source_root>/abstract
api      → <rgl_source_root>/api
common   → <rgl_source_root>/common
prelude  → <rgl_source_root>/prelude
```

Rules:

- exact alias matching;
- aliases require a resolved RGL source root;
- adding or changing a reserved alias is a contract change;
- unknown bare profile values are not guessed as aliases;
- every resolved alias retains provenance.

---

## 52. GF path resolution algorithm

For every candidate requirement in order:

1. validate a non-empty structured requirement;
2. identify its declared base and provenance;
3. reject prohibited absolute portable syntax;
4. normalize separators;
5. reject parent escape;
6. resolve standard aliases beneath `rgl_source_root`;
7. resolve language-local requirements beneath `language_directory`;
8. resolve profile-owned requirements according to the profile schema;
9. validate directory existence according to required or optional policy;
10. deduplicate by platform-aware normalized identity;
11. preserve the first accepted occurrence;
12. return one immutable structured resolution.

The resolver returns:

```text
ordered absolute Path values
provenance per path
required or optional classification
warnings and errors
native command representation metadata
```

---

## 53. Duplicate GF paths

Duplicate resolved paths are removed while preserving the first occurrence.

Comparison is:

- case-insensitive on Windows;
- case-sensitive on normal POSIX filesystems;
- separator-normalized;
- based on normalized absolute identity;
- display-case preserving.

---

## 54. Missing GF path or module

Required path part missing:

```text
configuration or capability error
```

Optional path part missing:

```text
explicit warning and omission when policy permits
```

When canonical GF diagnostics identify one missing module, Wordbench may perform
a bounded exact-name search beneath `rgl_source_root` through approved selection
services.

```text
zero exact matches     → module absent
one exact match        → remediation candidate
multiple exact matches → ambiguity requiring user choice
```

No directory is added twice. Resolution stops on ambiguity, no progress or the
configured maximum number of additions.

---

## 55. Command-line GF path representation

Internally:

```python
tuple[Path, ...]
```

At the GF command boundary, the command builder creates the supported path
option.

The join separator follows the platform and GF contract:

```text
Windows: ;
POSIX:   :
```

The structured ordered path list remains authoritative and is preferred in
persisted evidence.

---

## 56. No ambient GF path

GF Wordbench must not depend silently on a developer's global `GF_LIB_PATH`.

Policy:

- detect it when it could affect GF;
- override or neutralize it according to the resolved command contract;
- record the applied policy;
- never let tests pass only because a developer has configured it;
- never use it to select a language implicitly.

---

# 57. Environment preparation

The process environment is constructed per request.

The process runner must not mutate:

```python
os.environ
```

Canonical policy identifier:

```text
controlled-inherit-v1
```

---

## 58. `controlled-inherit-v1`

The policy:

1. copies the current parent environment;
2. removes or neutralizes ambient values that would alter GF path behavior
   invisibly;
3. applies documented safe overrides;
4. passes the resulting mapping only to the child;
5. records the policy identifier;
6. records explicit non-secret overrides;
7. does not persist the full environment.

---

## 59. Required inherited operating-system context

GF Wordbench retains ordinary operating-system context required by executables,
such as:

```text
PATH
system runtime variables
temporary-directory variables
locale variables
user-profile variables required by the platform
```

Retained values are not automatically recorded. Path-affecting GF variables are
handled explicitly and secrets are not copied into reports.

---

## 60. `PATH`

`PATH` may be used for initial optional discovery of `gf`.

After discovery:

- resolve the executable to an explicit path;
- use that path for the operation;
- record that path;
- do not rerun discovery after context finalization.

---

## 61. Temporary-directory variables

Operating-system variables such as `TEMP`, `TMP` and `TMPDIR` may be inherited.

Wordbench-owned temporary files still prefer `temporary_root` when
same-filesystem containment or atomic replacement matters.

---

## 62. Locale variables

Locale variables may affect tool wording or encoding.

Policy:

- use explicit UTF-8 file and stream handling;
- record relevant explicit locale overrides;
- avoid relying on locale-specific diagnostic text when stable evidence exists;
- keep fixtures tagged with platform and locale;
- avoid changing locale silently between CLI and GUI.

---

## 63. Environment override safety

Explicit process environment overrides must:

- use string keys and values;
- reject NUL characters;
- be scoped to one child process;
- avoid secrets where possible;
- mark secret keys for redaction when unavoidable;
- not overwrite portable profile configuration;
- not be persisted as a complete environment dump.

---

## 64. Environment evidence

A process-backed result preserves:

```text
environment policy identifier
explicit override keys
non-sensitive override values
redaction markers
```

It does not preserve the complete inherited environment, unrelated user
variables or secrets.

---

# 65. Relative input paths

Relative user input is resolved at one explicit entrypoint boundary.

### `--language-path`

Relative to the invocation current working directory, then converted to an
absolute resolved value.

### `--validation-profile`

Relative to the invocation current working directory, then converted to an
absolute resolved value.

### Other machine-local CLI paths

The same rule applies to GF executable, RGL-root override, output root and state
path.

Examples:

```text
--language-path ../gf-rgl/src/english
--gf-exe tools/gf/gf.exe
--rgl-root ../gf-rgl
--output-root runs
```

After bootstrap, no machine-local path remains relative.

---

## 66. GUI path inputs

GUI path pickers produce absolute paths.

Typed relative GUI input must either be rejected clearly or resolve against a
clearly displayed base before submission. It must not resolve against an
invisible GUI process directory.

The GUI exposes both directory and `.gf` file selection.

---

## 67. Application-state paths

Application state stores machine-local paths as resolved absolute strings or
`null`.

It may store:

```text
last_selected_language_path
last_selected_validation_profile
last_rgl_root
environment.gf_executable
environment.output_root
```

It must not store unresolved relative paths, interpolation expressions, inferred
entrypoints, required checkpoints, scenario policy or a serialized executable
resolved context.

---

## 68. Portable source and profile persistence

Language-source paths are serialized relative to `rgl_source_root`.

Profile-owned paths are serialized relative to `validation_profile_root`.

Before serialization:

- verify containment;
- reject unresolved parent escape;
- preserve Unicode and case;
- use `/` separators;
- avoid drive-relative forms.

Failure to relativize a supposedly portable path is a contract error.

---

## 69. Run-relative persistence

Canonical run artifact paths are serialized relative to `run_dir`.

Examples:

```text
summary.md
raw/master.log
artifacts/pgf/Lang.pgf
```

A report must not store a different base for the same artifact field.

---

## 70. Environment-path persistence

Environment paths may be persisted as absolute strings for local traceability.

Canonical separator is `/` where practical.

Examples:

```text
C:/Program Files/GF/bin/gf.exe
C:/work/gf-rgl/src/english
```

Portable exports may redact environment path prefixes but must mark the
redaction.

---

# 71. Path normalization

Normalization converts path syntax into a consistent internal identity without
changing the target intentionally.

Steps:

1. validate input type;
2. trim unintended surrounding whitespace from user fields;
3. reject NUL;
4. expand an explicitly allowed user-input form;
5. apply the documented base;
6. normalize `.` components;
7. reject prohibited `..` escape;
8. convert environment and runtime paths to absolute internal `Path` values;
9. preserve original case for display;
10. perform platform-aware identity comparison;
11. validate containment and type.

Normalization is not existence validation.

---

## 72. Whitespace

User-entered machine-local path fields may trim surrounding whitespace.

Portable relative paths preserve meaningful internal spaces.

Generated filenames avoid trailing spaces and platform-invalid endings.

---

## 73. Dot components

Redundant `.` components are removed from canonical persisted paths.

Parent components may appear in initial machine-local CLI input only before
resolution. They are prohibited in canonical source, profile and run-relative
persistence.

---

## 74. User-home expansion

Portable files do not use `~`.

CLI machine-local input may support `~` expansion when documented, performed
before context resolution and tested on supported platforms.

Application state stores the resolved path, not `~`.

---

## 75. Environment-variable expansion

Inline environment-variable expansion is disabled by default.

Recognized `GF_WORDBENCH_*` variables provide complete values instead.

---

## 76. Filesystem resolution

Do not call unrestricted `resolve()` blindly on untrusted paths when it may
require inaccessible or nonexistent targets.

Use an operation-appropriate strategy:

- existing input: resolve or canonicalize the existing target;
- new output: resolve the existing parent, then append the validated filename;
- broken symlink: reject or report explicitly;
- unavailable network path: preserve the original candidate in the error.

---

# 77. Path containment

Containment protects language-source, validation-profile, run, RGL, framework
and temporary boundaries.

Required roots include:

```text
rgl_source_root
language_directory
validation_profile_root, when present
run_dir
framework_root
temporary_root
```

A path owned by one root must not escape into another root accidentally.

---

## 78. Lexical containment

Lexical validation rejects:

- absolute portable profile paths;
- unresolved `..` escape;
- drive changes;
- UNC changes;
- malformed separators;
- empty required components.

Lexical containment is necessary but not sufficient when symlinks or junctions
exist.

---

## 79. Resolved containment

For an existing path:

1. resolve root;
2. resolve target;
3. verify target is below or equal to root;
4. apply platform-aware comparison.

For a new output path:

1. resolve root;
2. resolve nearest existing parent;
3. verify parent containment;
4. append validated remaining components;
5. recheck after creation when strict safety is required.

---

## 80. Symlinks and junctions

Default policy:

- read-only source and profile assets may traverse links only when the resolved
  target remains inside an approved root;
- generated outputs must not follow a link outside `run_dir`;
- release and gold-update operations use strict resolved containment;
- ambiguous or inaccessible links produce an error;
- the manifest records the final artifact path, not an unverified external
  target.

An intentionally external linked source requires explicit profile and security
policy.

---

## 81. Root equality

Some paths may equal their root, such as an RGL root itself or a report directly
under `run_dir`.

Containment checks distinguish:

```text
inside-or-equal
strictly-inside
```

Generated child artifacts normally require strictly-inside except canonical
files directly under `run_dir`.

---

## 82. Cross-root prohibition

Prohibited by default:

- output root inside selected language source;
- selected language source inside output root;
- state file inside a gold directory;
- run directory inside the RGL checkout;
- temporary root inside source;
- validation profile writing into source during normal validation;
- report detail copier reading arbitrary diagnostic-mentioned files;
- one resolved language context using another language's output scope.

Bootstrap detects dangerous overlap.

---

# 83. Path type validation

| Field | Expected type |
|---|---|
| `framework_root` | directory |
| `selected_language_path` | readable directory or regular `.gf` file |
| `language_directory` | directory |
| `rgl_source_root` | directory for a standard RGL context |
| `rgl_root` | directory when resolved |
| `validation_profile_root` | directory when present |
| `validation_profile_path` | regular profile file when present |
| `gf_executable` | regular executable file when GF capability is requested |
| `output_root` | directory or creatable directory |
| `language_output_root` | directory or creatable directory |
| `run_dir` | new directory |
| `state_path` | file path with creatable parent |
| scenario path | regular `.gfs` file |
| gold path | regular `.gold` file when required |
| entrypoint or checkpoint | regular `.gf` file |

A directory must not be accepted where a file is required.

---

## 84. Readability and writability

Inputs are checked for existence, expected type, practical readability and
containment.

Outputs are checked for parent existence or creatability, practical writability,
collision policy, containment and no source overwrite.

A preflight writability check cannot guarantee a later write. Runtime write
failures remain explicit.

---

## 85. Executability

On POSIX, executable permission is checked where meaningful.

On Windows, validate regular-file status, supported executable form and launch
result.

A file that exists but cannot launch produces a launch failure.

A `.bat` or `.cmd` file is not treated as the native GF executable by the generic
GF execution path.

---

# 86. Windows path policy

Windows is a first-class supported environment.

GF Wordbench supports:

- drive-letter absolute paths;
- spaces;
- Unicode;
- mixed user-input separators;
- case-insensitive filesystem identity;
- executable paths outside source;
- long paths where Python and the operating system support them.

---

## 87. Windows separators

Accepted input:

```text
C:\work\gf-rgl\src\english
C:/work/gf-rgl/src/english
```

Internal representation uses `Path`.

Canonical persistence uses `/` separators.

---

## 88. Windows drive letters

Drive-relative paths such as `C:work/english` are prohibited because their base
depends on hidden per-drive process state.

Drive-letter comparison is case-insensitive. Display preserves resolved casing.

---

## 89. UNC paths

UNC environment paths may be accepted when reachable and when the operation
supports network-filesystem semantics.

Portable source, profile and run-relative fields never contain UNC paths.

Release workflows warn when required atomicity cannot be guaranteed.

---

## 90. Extended-length Windows paths

Internal paths may use extended-length syntax when required by the runtime.
Canonical persisted paths avoid exposing that prefix unless necessary.

Shared path utilities own prefix conversion.

---

## 91. Windows case behavior

Rules:

- do not lowercase paths for display;
- use a normalized comparison key;
- preserve actual path text in reports;
- treat case-only duplicates as duplicates;
- do not assume a case-only rename is portable.

GF module-name semantics remain GF semantics.

---

## 92. Windows reserved names

Generated components avoid reserved device names such as `CON`, `PRN`, `AUX`,
`NUL`, `COM1` and `LPT1`.

The shared safe-name utility owns generated-name sanitization.

---

## 93. Windows trailing dots and spaces

Generated names do not end with a dot or space.

Portable relative paths reject ambiguous trailing-dot or trailing-space
components in strict mode.

---

## 94. Windows junction safety

Junctions are treated like symlinks for containment.

A lexical path below `run_dir` whose junction target escapes the run is unsafe
for generated output.

---

## 95. Windows command safety

Paths containing spaces are passed as separate process arguments.

Correct:

```python
[gf_executable, "--version"]
```

Human display rendering is separate from execution.

---

# 96. POSIX path policy

POSIX support uses:

- `/` root;
- case-sensitive identity by default;
- executable permission;
- symlink-aware containment;
- `:` for joined search paths;
- UTF-8 policy independent of locale defaults.

A source tree that differs only by path case may not be portable to Windows.

---

## 97. Cross-platform portability checks

Recommended strict checks:

- no case-colliding source or profile paths;
- no Windows-reserved generated names;
- no backslash-only portable semantics;
- no drive-relative path;
- no path depending on shell expansion;
- no source or profile path escaping its root;
- no absolute portable profile path;
- no profile requiring a machine-specific RGL root;
- no duplicate GF paths after platform normalization;
- no portable language identity derived from an absolute path.

---

# 98. Run-directory creation

Run ID format:

```text
YYYYMMDD_HHMMSS
```

The timestamp represents UTC.

Directory form:

```text
<language_output_root>/run_<run-id>
```

Collision suffix:

```text
run_20260730_204500_02
```

Creation is exclusive and race-safe.

---

## 99. Run path derivation

`RunPaths` is constructed once after `run_dir` exists.

It owns paths including:

```text
summary_json_path
summary_md_path
ai_ready_path
top_errors_path
manifest_path
master_log_path
all_scan_logs_path
all_logs_path
details_dir
raw_compile_dir
raw_scan_dir
raw_scenarios_dir
gfo_dir
out_dir
pgf_dir
temporary_root
```

Exact public field names are locked by the data-model and interfile contracts.

---

## 100. No duplicated artifact filenames

Canonical report and log filenames have one owner. Consumers receive them
through `RunPaths` and do not define local constants with the same ownership
role.

---

## 101. Artifact subject keys

Per-subject artifact filenames use a shared deterministic, path-safe,
collision-resistant key independent of absolute source location.

When two source paths share a filename, the key incorporates portable relative
path identity or a stable suffix.

---

## 102. Artifact collision

Before writing an owned artifact:

- validate target containment;
- ensure no other active owner has reserved the path;
- apply the artifact collision policy;
- never overwrite a prior run;
- never overwrite source, profile or gold assets.

Collision is an artifact or contract error.

---

## 103. Atomic report paths

Stable reports use sibling temporary files where supported and atomically replace
the final target after validation.

Temporary report paths do not appear as final manifest artifacts and are cleaned
after success.

---

## 104. Tool-generated artifact paths

GF-generated `.gfo` and `.pgf` artifacts use owned destinations below the run
artifacts tree.

When GF cannot write directly to the final directory, use an owned temporary
build directory, preserve output, move or copy through a documented stage,
verify identity and catalog the final artifact without modifying its content.

---

## 105. Previous-run paths

Previous-run comparison may use:

- the last compatible run recorded in state;
- a run selected explicitly;
- deterministic discovery below the current language scope.

The selected summary must exist, validate under a supported schema, remain
read-only and record provenance.

Compatibility requires at least:

```text
portable language key
relevant source-context identity
validation-profile identity when policy requires it
schema compatibility
```

---

## 106. Run discovery

When automatic previous-run discovery is enabled:

1. enumerate candidate run directories below `language_output_root`;
2. validate canonical or supported legacy naming;
3. locate `summary.json`;
4. ignore the current run;
5. load metadata;
6. filter for compatible language and profile identity;
7. select by finished timestamp;
8. preserve deterministic tie-breaking.

A malformed candidate does not crash all discovery.

---

# 107. Application state and paths

Canonical state path fields may include:

```text
last_selected_language_path
last_selected_validation_profile
last_rgl_root
environment.gf_executable
environment.output_root
last_compatible_run_by_language
```

Each field is a string, mapping or `null` according to the state schema.

State is convenience data. It is not a language registry, a source of profile
policy or a serialized runtime authority.

---

## 108. State loading

State loading must:

- tolerate a missing file;
- reject or safely default invalid fields;
- validate schema version;
- preserve the source during migration;
- not make CLI or GUI unusable because state is corrupt;
- not launch tools;
- revalidate remembered paths before use;
- not infer a path from an obsolete catalog ID.

---

## 109. State saving

State saving must:

- write atomically;
- create the parent safely;
- store resolved machine-local paths;
- omit secrets and process handles;
- omit active run result objects;
- omit inferred entrypoints and scenario policy;
- use canonical separators;
- update the last selected path only after successful context resolution.

---

# 110. CLI and GUI equivalence

Equivalent CLI and GUI inputs produce equivalent `LanguageProbeRequest`,
`ResolvedLanguageContext` and run requests.

Both interfaces use:

```text
same language probe service
same source selection service
same environment reader
same path resolver
same preflight rules
same GF adapter
same RunPaths builder
```

Interface-specific path inference after bootstrap is prohibited.

---

## 111. CLI display

The CLI configuration-inspection or probe surface displays:

```text
selected path
resolved language directory
portable language key
resolved RGL roots
validation profile when present
effective GF path and provenance
capability statuses
validation result and remediation
```

Exact command spelling is owned by `CLI_REFERENCE.md` and the command registry.

---

## 112. GUI display

The GUI introduction and configuration surfaces display:

- selected language path;
- resolved language directory;
- portable language key;
- module suffix when unambiguous;
- detected candidate entrypoints;
- optional validation profile;
- GF executable and version after probe;
- resolved RGL root;
- effective GF path diagnostics;
- output root and next run scope;
- capability statuses;
- provenance when an explicit value overrides stored convenience state.

The GUI does not maintain a separate discovery or path policy.

---

# 113. Error model

Path and environment failures normally produce structured errors such as:

```text
validation_status = ERROR
error_kind = CONFIG, IO, TOOL, CONTRACT or ARTIFACT
```

They do not become GF linguistic failures.

A missing optional capability may instead produce a structured unavailable or
skipped status.

---

## 114. Configuration errors

Examples:

- selected language path missing;
- selected file is not `.gf`;
- selected directory contains no eligible source;
- RGL source root cannot be resolved;
- explicit RGL root does not contain selected language;
- module suffix or missing-module remediation is ambiguous;
- validation profile conflicts with selected source context;
- absolute profile-owned path;
- invalid GF path requirement;
- output root overlaps source or RGL;
- unsupported state schema.

These are detected before affected GF execution.

---

## 115. I/O errors

Examples:

- permission denied;
- directory cannot be created;
- state cannot be written;
- report atomic replacement fails;
- source cannot be read;
- network path disappears.

Errors preserve operation, normalized path, path role, operating-system detail
and safe remediation context.

---

## 116. Tool-location errors

Examples:

- GF executable missing;
- path points to a directory;
- unsupported launcher type;
- executable disappears after resolution;
- executable cannot launch.

Missing GF may leave source and scan capabilities available.

---

## 117. Containment errors

Normalized messages identify candidate path, expected root, path role and
containment stage.

Containment errors are contract or security errors and are not auto-corrected by
moving the target silently.

---

## 118. Artifact-path errors

Examples:

- duplicate writer target;
- run artifact escapes run root;
- required output absent;
- output collides with prior artifact;
- unsafe subject-derived filename;
- run written under the wrong language scope.

---

# 119. Persistence rules

| Path category | Persistence form |
|---|---|
| Portable language identity | Relative to `rgl_source_root`, `/` |
| Source result | Relative to `rgl_source_root`, `/` |
| Validation-profile asset | Relative to `validation_profile_root`, `/` |
| Run artifact | Relative to `run_dir`, `/` |
| GF executable | Absolute environment path |
| RGL root and source root | Absolute local evidence when required |
| Selected language path | Absolute local state/evidence, redacted when exported |
| Output root | Absolute local evidence when required |
| State-local path | Absolute |
| Temporary path | Normally not persisted |

---

## 120. Legacy Windows paths

Legacy readers accept backslash Windows paths.

Migration determines whether the path belongs to a known RGL source root,
validation profile, run root or environment role, converts it to the correct
portable representation when provable, preserves it as an environment path when
appropriate and reports ambiguity without guessing.

---

## 121. Legacy relative paths

A legacy relative path is migratable only when its historical base is known.

Possible bases include:

```text
legacy project root
legacy RGL source root
legacy run directory
legacy process working directory
legacy application directory
```

Ambiguity is preserved as migration evidence and never resolved silently.

---

## 122. Legacy GF path strings

A joined legacy GF path may be split only using its known source-platform
separator.

Windows drive colons make naive colon splitting unsafe.

Canonical migration output stores the structured ordered path list when the
target schema supports it.

---

# 123. Security rules

Paths are untrusted until validated.

Required protections:

- no shell interpolation;
- no NUL;
- bounded discovery;
- containment;
- generated-name sanitization;
- no source overwrite;
- no normal-run gold write;
- no arbitrary diagnostic-path copying;
- no complete environment dump;
- no secret interpolation;
- explicit executable path;
- output collision control;
- no implicit catalog or sibling-language selection;
- no `gf-portfolio` path or state dependency.

---

## 124. Diagnostic-mentioned paths

GF output may mention paths. A diagnostic parser may extract them as text.

Before opening one:

1. identify expected path class;
2. map it against known language, RGL, profile or run inventories;
3. validate containment;
4. reject arbitrary external paths;
5. preserve the original diagnostic.

A report writer does not copy a file merely because GF named it.

---

## 125. Profile import safety

Initializing or importing an optional validation profile must:

- target an explicit profile root;
- avoid unsafe links;
- not overwrite framework or language source files;
- not copy application state;
- not copy generated run artifacts;
- validate compatibility with the selected language context;
- preserve backups under explicit reset or migration policy.

Normal language startup never creates or rewrites a profile.

---

# 126. Testing architecture

Required coverage is organized around:

```text
tests/paths/
├── test_path_classes.py
├── test_path_precedence.py
├── test_language_probe_paths.py
├── test_validation_profile_paths.py
├── test_run_paths.py
├── test_gf_path_resolution.py
├── test_environment_variables.py
├── test_path_containment.py
├── test_path_persistence.py
├── test_path_migration.py
├── test_windows_paths.py
├── test_posix_paths.py
└── test_path_security.py
```

Contract tests verify the language probe uses public selection, path, preflight
and GF contracts without duplicating them.

Schema tests cover state, summary, manifest and optional profile paths.

---

## 127. Precedence tests

Test each field with explicit value, environment only, state only, default or
derivation only, all sources present, invalid higher-precedence value, empty
environment value, corrupt state, bounded discovery success and failure, and
provenance reporting.

---

## 128. Language and profile path tests

Required cases:

- directory selection;
- focused `.gf` file selection;
- non-`.gf` file rejection;
- nearest RGL source-root derivation;
- nonstandard explicit root;
- parent escape;
- absolute Windows and POSIX paths;
- Unicode and spaces;
- source directory with no eligible GF files;
- ambiguous suffix candidates;
- explicit profile agreement and conflict;
- scenario or gold outside profile root;
- symlink and junction escape.

---

## 129. GF-path tests

Required cases:

- language directory first;
- `abstract`, `api`, `common` and `prelude` aliases;
- missing RGL source root;
- missing required path directory;
- duplicate paths;
- case-variant duplicate on Windows;
- stable declared order;
- Windows `;` rendering;
- POSIX `:` rendering;
- ambient `GF_LIB_PATH` neutralization;
- zero, one and multiple exact missing-module matches;
- bounded remediation termination;
- no all-language path construction.

---

## 130. Executable tests

Required cases include explicit executable, path with spaces, Unicode, missing
file, directory passed as executable, non-executable POSIX file, unsupported
launcher, `PATH` discovery, recorded result, invalid explicit path with no
fallback and executable disappearance before launch.

---

## 131. Output-root tests

Required cases include default, explicit, environment and state roots;
creatable directory; permission denial; overlap with selected source or RGL;
language-scope isolation; run collision; concurrent creation; supported UNC
behavior and atomic report writing.

---

## 132. Persistence tests

Required cases:

- language-source path uses `/` relative to RGL source root;
- profile path uses `/` relative to profile root;
- run path uses `/` relative to run directory;
- environment path remains absolute;
- no unresolved `..` or interpolation;
- legacy backslash accepted;
- legacy absolute source converted when containment is provable;
- ambiguous legacy path warns;
- stable round trip;
- redaction preserves path role.

---

## 133. Security tests

Required cases:

- path traversal;
- unbounded discovery prohibition;
- symlink and junction escape;
- NUL;
- Windows-reserved generated name;
- shell metacharacters remain literal path text;
- diagnostic path cannot trigger arbitrary copy;
- source cannot become report destination;
- gold cannot become raw-log destination;
- secret environment value is not reported;
- output root cannot overwrite source or templates;
- obsolete catalog ID cannot trigger filesystem search.

---

## 134. Cross-platform fixture policy

Tests use temporary roots and avoid a developer's real environment.

Real-GF integration tests may read explicit test-only values but must not pass
only because ambient `GF_LIB_PATH`, `PATH`, current working directory, user
profile or IDE settings happen to contain usable values.

---

# 135. Path-resolution application boundary

The application exposes cohesive operations equivalent to:

```python
probe_language_path(...)
resolve_environment(...)
resolve_gf_path(...)
resolve_validation_profile(...)
allocate_run_paths(...)
```

Required boundaries:

- entrypoints provide explicit values;
- the projects module coordinates language resolution;
- the validation selection service enumerates sources;
- the GF adapter resolves and serializes effective GF paths;
- the runs module allocates run-owned paths;
- adapters perform filesystem and platform operations through ports;
- reporting receives canonical artifact paths from the run context;
- no consumer reconstructs an owned path independently.

---

## 136. Shared path operations

Cohesive path operations cover:

```text
normalize user-supplied environment path
resolve selected language path
resolve bounded RGL ancestors
resolve source-relative path
resolve profile-relative path
resolve run-relative path
serialize portable source path
serialize profile path
serialize run path
serialize environment path
verify containment
build a safe language and artifact key
create an exclusive run directory
```

Shared operations receive explicit roots, classes and provenance.

---

## 137. Shared path-operation restrictions

Shared path operations must not:

- read GUI widgets;
- read CLI parser objects;
- load profiles independently of the projects module;
- launch GF;
- decide release policy;
- own report prose;
- invent a language path;
- silently expand arbitrary environment expressions;
- read or write `gf-portfolio` configuration;
- read a runtime language catalog.

---

# 138. Drift indicators

Environment or path drift exists when:

- CLI and GUI resolve different contexts from equivalent inputs;
- a framework module hardcodes an active-language path;
- a runtime catalog is required for normal startup;
- a profile contains absolute GF, RGL or output paths;
- application state contains inferred entrypoints or required scenarios;
- a report reconstructs an artifact filename;
- GF path order changes between consumers;
- compilation and scenarios construct different GF paths;
- tests rely on ambient `GF_LIB_PATH`;
- a relative machine path survives into the resolved context;
- portable source or profile paths persist with drive letters;
- output root overlaps source or RGL;
- a symlink escapes an owned root;
- path normalization differs by writer and reader;
- `PATH` discovery repeats after resolution;
- a run directory is reused;
- state corruption prevents CLI use;
- migration guesses an ambiguous base;
- Wordbench reads a Portfolio registry;
- one language runtime retains paths from another.

Any drift indicator requires coordinated review.

---

# 139. Change classification

## 139.1 Internal compatible change

Examples include faster containment with unchanged semantics, private helper
refactoring, clearer error text with the same semantic fields and platform
optimization with identical results.

Requirements: same resolved values, precedence and persistence, with tests
passing.

## 139.2 Compatible extension

Examples include an optional provenance field, optional resolver alias, optional
profile field or additional strict-mode warning.

Requires safe default, documentation, tests and schema minor version when
persisted.

## 139.3 Breaking change

Examples:

- precedence reorder;
- environment-variable rename;
- path base change;
- new implicit expansion;
- portable language-key change;
- artifact filename change;
- ownership transfer;
- RGL alias semantic change;
- output-root or language-scope layout change;
- state path relocation without migration;
- reintroducing a mandatory catalog or bundle.

Requires impact analysis, schema review, compatibility adapter, migration, tests,
documentation, contract-lock update and changelog entry.

---

# 140. Configuration review checklist

```text
[ ] framework_root is deterministic
[ ] selected_language_path is explicit and valid
[ ] language_directory is derived once
[ ] rgl_source_root discovery is bounded
[ ] rgl_root contains the selected language context
[ ] portable language key is path-independent
[ ] optional validation profile agrees with the selected language
[ ] GF executable is explicit when GF capability is requested
[ ] effective GF path preserves order and provenance
[ ] ambient GF path variables are controlled
[ ] output root does not overlap source or RGL
[ ] language output scope is deterministic
[ ] run directory is new and exclusive
[ ] state is machine-local convenience only
[ ] source and profile paths contain no interpolation
[ ] portable paths serialize with /
[ ] run paths serialize relative to run_dir
[ ] environment paths are absolute after bootstrap
[ ] CLI and GUI use the same language probe and resolver
[ ] symlink and junction containment is safe
[ ] secrets and full environments are not reported
[ ] no runtime language catalog is required
```

---

# 141. Governing invariants

1. Every path has a declared class, base and owner.
2. The user supplies exactly one primary language path for startup.
3. A running session has zero or one immutable resolved language context.
4. A selected `.gf` file remains the focused target unless the user changes it.
5. The language directory is derived once from the selected path.
6. RGL root discovery is bounded to explicit input and its approved ancestors.
7. Wordbench never searches the entire filesystem for an RGL installation.
8. Portable language identity is relative to an approved source root, not an
   absolute path.
9. Optional profile paths are relative to their profile root.
10. Run artifact paths are relative to `run_dir`.
11. Machine-local paths are resolved before execution.
12. Application state is convenience only and is revalidated.
13. An explicit invalid input never silently falls through.
14. Path provenance remains inspectable.
15. The GF executable is explicit and stable for each GF-backed operation.
16. Missing GF does not invalidate source-ready or scan-ready context.
17. GF path order is preserved.
18. Compilation, scenarios and PGF construction use one GF path resolution.
19. Ambient `GF_LIB_PATH` cannot determine behavior silently.
20. GF remains authoritative for module semantics.
21. Missing-module assistance is exact, bounded and ambiguity-safe.
22. No all-language GF path is constructed.
23. Output root does not overlap selected source or RGL.
24. Every run directory is new, exclusive and language-scoped.
25. `RunPaths` owns generated artifact locations.
26. Consumers do not reconstruct owned paths.
27. Containment accounts for symlinks and Windows junctions.
28. Canonical persisted separators use `/`.
29. Windows paths with spaces and Unicode are supported.
30. Drive-relative Windows paths are prohibited.
31. Source, scenario, input and gold assets remain read-only during normal
    validation.
32. Full inherited environments and secrets are not persisted.
33. Migration never guesses an ambiguous path base.
34. A validation profile may add policy but cannot redirect language identity.
35. `project.toml` is optional for normal language startup.
36. A runtime catalog or mandatory language bundle is not required.
37. Language switching recreates the runtime and is prohibited during an active
    run.
38. Previous-run comparison requires compatible language context.
39. One ordinary run never mixes unrelated languages.
40. Wordbench path resolution does not depend on `gf-portfolio`.

---

# 142. Governing rule

GF Wordbench path resolution follows one explicit chain:

```text
one user-selected language directory or .gf file
        ↓
bounded candidate resolution
        ↓
existing source selection and path services
        ↓
one immutable ResolvedLanguageContext
        ↓
one ordered effective GF path
        ↓
capability-specific preflight and execution
        ↓
language-scoped run evidence
        ↓
portable relative references plus controlled local-path evidence
```

A path is valid only when its owner, base, provenance, containment, runtime
target and persistence form all agree.
