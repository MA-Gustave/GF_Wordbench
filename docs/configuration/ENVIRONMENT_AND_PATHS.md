# GF Wordbench — Environment and Paths

**Document ID:** `GF-WB-CONFIG-ENVIRONMENT-PATHS`  
**Status:** Normative configuration and path-resolution specification  
**Applies to:** one GF Wordbench workspace, its one active project, CLI, GUI, automation, GF invocation, run creation, reporting, migration and tests  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Configuration authority:** `docs/configuration/PROJECT_TOML_REFERENCE.md`, `docs/configuration/APPLICATION_STATE_REFERENCE.md`  
**Boundary authorities:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`  
**Specification version:** `1.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines how GF Wordbench represents, discovers, resolves, validates, persists, and reports environment-dependent values and filesystem paths.

It establishes one shared model for:

- the GF Wordbench framework root;
- the active project root;
- the active project configuration;
- the project source root;
- the GF executable;
- the Resource Grammar Library root;
- the ordered GF search path;
- the output root;
- run directories;
- raw and generated artifact paths;
- application-state location;
- temporary paths;
- environment-variable overrides;
- Windows and POSIX path behavior;
- path containment;
- path migration;
- path-related errors;
- path-related tests.

The objective is portability without ambiguity.

A project must remain clonable, while every execution must record the exact local paths that were actually used.

---

## 2. Core rule

> Portable project facts use project-relative paths; generated run facts use run-relative paths; machine-local tools and roots use resolved environment paths.

No path may be interpreted without a documented base.

No consumer may reconstruct an owned path through duplicated filename constants.

No local environment path may become a language-project fact.

---

## Workspace and product boundary

One GF Wordbench workspace resolves exactly one active GF language project. One run uses exactly one `project_root` and one normative language target.

Environment and path configuration may select the workspace or its active project for the current invocation. It must not create:

- a registry of several Wordbench projects;
- a runtime language-profile list;
- cross-workspace path discovery;
- portfolio-wide output roots or aggregation state;
- a dependency on `gf-portfolio` configuration, schemas, storage or runtime.

The independent `gf-portfolio` product may read finalized, public, versioned run artifacts. It does not participate in Wordbench project discovery, path precedence, GF search-path construction, run-directory creation or application-state resolution.

---

## 3. Related authority

The following documents remain authoritative for their domains:

```text
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
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/gf/GF_PATH_RESOLUTION.md
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
```

Priority when rules overlap:

1. accepted ADRs govern architectural decisions;
2. `DOCUMENTATION_ALIGNMENT_LOCK.md` governs cross-document interpretation and the Wordbench/Portfolio boundary;
3. `PERSISTED_SCHEMA_LOCK.md` governs canonical persisted path representation;
4. `EXTERNAL_TOOL_CONTRACT_LOCK.md` governs executable, working-directory and GF command boundaries;
5. `INTERFILE_CONTRACT_LOCK.md` governs ownership and dependency direction;
6. this document governs environment and path resolution;
7. report and operation-specific references govern presentation details.

---

## 4. Scope

This specification governs:

- configuration precedence;
- environment-variable names;
- path input parsing;
- path expansion policy;
- relative-path bases;
- path normalization;
- path existence checks;
- path type checks;
- path containment;
- symlink and junction handling;
- executable discovery;
- RGL root resolution;
- GF search-path construction;
- output-root selection;
- run-directory construction;
- temporary files;
- persisted path representation;
- legacy path migration;
- Windows drive, UNC, separator, and case behavior;
- POSIX behavior;
- environment inheritance;
- path evidence;
- path error reporting;
- path test coverage.

---

## 5. Exclusions

This specification does not define:

- GF module resolution semantics;
- GF compiler option compatibility;
- the internal structure of the RGL;
- project linguistic architecture;
- report prose;
- scenario command syntax;
- operating-system access-control policy;
- network filesystem administration;
- package installation;
- remote execution;
- container orchestration;
- cloud storage;
- arbitrary environment-variable expansion in project files;
- Portfolio workspace discovery or aggregation.

---

## 6. Configuration ownership

Environment and path values are divided by owner.

### 6.1 Projects module

The `projects` module owns:

- locating the active project boundary;
- loading `project/project.toml`;
- validating project identity;
- resolving project-relative source, entrypoint, checkpoint, scenario, input and gold paths;
- producing the resolved project-path model.

It does not resolve machine-local GF or output locations from project metadata.

### 6.2 Active project

The active project owns portable declarations in:

```text
project/project.toml
```

Examples:

- source directory;
- source glob;
- GF path parts owned by the project;
- entrypoint paths;
- checkpoint paths;
- scenario paths;
- input paths;
- gold paths.

Project-owned paths are project-relative, portable and source-controlled.

### 6.3 Application configuration and state adapter

Machine-local values are supplied through explicit invocation values, documented environment variables or disposable application state.

Examples:

- active project root for the current workspace;
- GF executable;
- RGL root;
- output root;
- optional state-file override.

These values may be absolute. They remain non-authoritative for language identity and project policy.

### 6.4 Runs module

The `runs` module owns the run identity, run directory and immutable run-path allocation.

Examples:

- run directory;
- raw evidence directories;
- temporary directory;
- artifact directories;
- per-file and per-scenario evidence roots.

Run-owned paths are derived once per run.

### 6.5 Reporting module

The `reporting` module owns canonical report and manifest paths supplied through the run-path model.

Examples:

- `summary.json`;
- `summary.md`;
- `AI_READY.md`;
- aggregate logs;
- detail reports;
- `manifest.json`.

Consumers receive owned paths from the run context and never reconstruct them through duplicated filename constants.

### 6.6 Adapters

Filesystem, process, state and platform adapters implement path operations through application ports. Domain and application rules do not depend on GUI widgets, CLI parser objects, operating-system process APIs or private `gf-portfolio` state.

---

## 7. Canonical path classes

Every path field belongs to exactly one path class.

```text
framework path
project-owned path
run-owned path
environment path
temporary path
external evidence path
```

A field must not silently change class.

---

## 8. Framework paths

Framework paths point inside the installed or checked-out GF Wordbench framework.

Examples:

```text
docs/
application package/
tests/
templates/project/
```

Framework paths are resolved against `framework_root`.

They must not be stored as language-project paths.

The active project may reference framework templates only during explicit initialization or reset operations.

Normal project validation must not depend on mutable files under `templates/project/`.

---

## 9. Project-owned paths

Project-owned paths identify source-controlled assets belonging to the active language project.

Examples:

```text
project.toml
lib/src/language
lib/src/language/GrammarX.gf
validation/scenarios/parse.gfs
validation/inputs/parse.txt
validation/gold/parse.gold
docs/VALIDATION_SPEC.md
```

Canonical persistence rules:

- relative to `project_root`;
- `/` separators;
- no drive letter;
- no UNC prefix;
- no `..` after normalization;
- no user-home alias;
- no inline environment variable;
- no backslash in canonical output;
- empty path only when the field explicitly permits it.

---

## 10. Run-owned paths

Run-owned paths identify artifacts inside one run directory.

Examples:

```text
summary.json
raw/compile/GrammarX.stdout.txt
raw/scenarios/parse.out
artifacts/pgf/Grammar.pgf
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

## 11. Environment paths

Environment paths identify machine-local locations.

Examples:

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl/src
C:/work/GF_Wordbench/project
C:/work/gf-wordbench-runs
```

Environment paths may be absolute.

Rules:

- resolve before execution;
- record the actual resolved value;
- use `/` separators in canonical persisted text where practical;
- accept native separators as user input;
- do not copy environment paths into `project.toml`;
- do not infer project semantics from their directory names.

---

## 12. Temporary paths

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
- are excluded from the manifest unless a failure-retention policy explicitly catalogs them;
- must remain inside an owned temporary root;
- must not be placed in the active source directory;
- must be cleaned on successful finalization;
- may remain after abnormal termination only with an explicit recovery marker.

---

## 13. External evidence paths

External evidence paths point outside the project and run roots but are recorded for traceability.

Examples:

```text
resolved GF executable
resolved RGL root
external previous-run summary selected explicitly
```

These paths:

- may be absolute;
- must be read-only unless an operation explicitly owns them;
- must not be treated as portable project paths;
- may be redacted in exported reports;
- must not be followed blindly from untrusted diagnostic text.

---

# 14. Root model

The resolved path model includes:

```text
framework_root
project_root
project_config_path
source_root
gf_executable
rgl_root
gf_search_paths
output_root
run_dir
state_path
temporary_root
```

Each value has one owner and one documented derivation.

---

## 15. `framework_root`

`framework_root` is the root of the current GF Wordbench installation or checkout.

Expected contents include:

```text
application package/
docs/
project/
templates/
```

Resolution order:

1. installed package/resource metadata where applicable;
2. repository root derived from the launcher or package location;
3. explicit developer-test fixture.

`framework_root` must not be derived from the process current working directory alone.

Normal users do not need an environment variable for `framework_root`.

A developer-only override requires an explicit test or development contract.

---

## 16. `project_root`

`project_root` is the root of the workspace's one active project.

It contains:

```text
project.toml
```

Canonical workspace location:

```text
<framework_root>/project
```

An explicit invocation may select another valid active-project root for that invocation. This selects one workspace boundary; it does not create a multi-project registry or permit one run to combine projects.

One GF Wordbench run uses exactly one immutable `project_root`.

---

## 17. `project_config_path`

Canonical path:

```text
<project_root>/project.toml
```

The project configuration path is not independently guessed after the project root is resolved.

A custom project configuration filename is not supported in schema version `1.0`.

This keeps project discovery deterministic.

---

## 18. `source_root`

`source_root` is derived from:

```text
project_root
+
[sources].directory
```

Example:

```text
project_root = C:/work/GF_Wordbench/project
sources.directory = lib/src/french
source_root = C:/work/GF_Wordbench/project/lib/src/french
```

Rules:

- source directory is project-relative;
- source root must remain inside project root;
- source root must exist for normal validation;
- source root must be a directory;
- source root is read-only except for explicit migration or project-editing operations.

---

## 19. `gf_executable`

`gf_executable` is the exact native executable used for the run.

Examples:

```text
C:/Program Files/GF/bin/gf.exe
/usr/local/bin/gf
```

Rules:

- it must be resolved to an explicit path before required validation;
- it must identify a regular file where the platform exposes that distinction;
- it must be passed separately from arguments;
- it must not be silently substituted after configuration finalization;
- the actual path must be recorded in run metadata;
- version probing uses this exact path.

---

## 20. `rgl_root`

`rgl_root` identifies the configured Resource Grammar Library source root.

Example:

```text
C:/work/gf-rgl/src
```

Rules:

- it is machine-local;
- it must not be stored in `project.toml`;
- it may be absent only when the active operation does not require an external RGL root and the GF command contract supports that state;
- if required, it must exist and be a directory;
- RGL-relative GF path aliases resolve under this root;
- the resolved root must be recorded when it affects execution.

GF Wordbench must not search the entire filesystem for an RGL installation.

---

## 21. `gf_search_paths`

`gf_search_paths` is the ordered resolved list passed to GF or used to build the GF path option.

It is derived from:

```text
project [gf].path_parts
project_root
rgl_root
```

The list is structured internally.

The joined command-line representation is derived only at the GF command boundary.

---

## 22. `output_root`

`output_root` contains run directories.

Canonical default:

```text
<framework_root>/_gf_wordbench
```

A user may select another local directory.

Rules:

- output root may be outside the project;
- output root must be writable before a run starts;
- output root must not equal a source directory;
- output root must not be inside `templates/project`;
- output root should not be inside the RGL;
- run directories are created below it;
- existing runs are not overwritten.

---

## 23. `run_dir`

Canonical form:

```text
<output_root>/run_<run-id>
```

Example:

```text
C:/work/gf-wordbench-runs/run_20260722_184500
```

Rules:

- created exclusively for one run;
- collision produces a deterministic numeric suffix;
- never reuse a non-empty prior run directory;
- contains only run-owned artifacts and temporary files;
- path is fixed for the lifetime of the run;
- all `RunPaths` values derive from it.

---

## 24. `state_path`

Canonical default:

```text
<framework_root>/.gf_wordbench_state.json
```

An explicit state-path override may place it elsewhere.

Rules:

- machine-local;
- disposable;
- written atomically;
- must not be inside `project/validation/gold`;
- must not be treated as project configuration;
- deleting it must not damage the project;
- canonical writer uses only the current state schema.

---

## 25. `temporary_root`

Canonical run-local temporary root:

```text
<run_dir>/.tmp
```

Use a run-local temporary root when:

- temporary output will later move into the run;
- atomic replacement requires the same filesystem;
- operation evidence needs deterministic containment.

The operating-system temporary directory may be used only for data that:

- does not need same-filesystem atomic replacement;
- contains no persistent project secret;
- is cleaned deterministically;
- is not mistaken for final evidence.

---

# 26. Canonical environment variables

GF Wordbench version `1.0` recognizes the following path-related variables:

```text
GF_WORDBENCH_PROJECT_ROOT
GF_WORDBENCH_GF_EXE
GF_WORDBENCH_RGL_ROOT
GF_WORDBENCH_OUTPUT_ROOT
GF_WORDBENCH_STATE_PATH
```

These names are framework configuration contracts.

Adding, renaming, or removing one requires documentation and compatibility review.

---

## 27. Environment-variable table

| Variable | Meaning | Required | Canonical target |
|---|---|---:|---|
| `GF_WORDBENCH_PROJECT_ROOT` | Active project root | No | Directory containing `project.toml` |
| `GF_WORDBENCH_GF_EXE` | GF executable | No | `gf.exe` or `gf` file |
| `GF_WORDBENCH_RGL_ROOT` | RGL source root | No | RGL `src` directory |
| `GF_WORDBENCH_OUTPUT_ROOT` | Parent of run directories | No | Writable directory |
| `GF_WORDBENCH_STATE_PATH` | Application state file | No | JSON file path |

An unset variable contributes no value.

An empty variable is treated as unset. A different empty-value meaning requires an explicit configuration-contract revision.

---

## 28. No inline interpolation

Canonical configuration does not expand inline path expressions such as:

```text
%USERPROFILE%\gf
${HOME}/gf
$GF_ROOT/src
~/gf
```

Rules:

- `project.toml` must contain literal project-relative paths;
- application state should contain resolved absolute paths;
- environment variables override complete configuration values;
- CLI input may be expanded at the user-input boundary only when documented;
- the resolved path, not the original expression, enters the resolved run request.

This prevents hidden machine-specific behavior inside portable files.

---

## 29. Unknown environment variables

Variables beginning with:

```text
GF_WORDBENCH_
```

but not documented here must not silently alter behavior.

The bootstrap may:

- ignore them;
- warn in strict configuration mode;
- reject them when an explicit environment-validation command is used.

It must not guess their meaning.

---

## 30. Deprecated environment variables

Legacy or temporary variable names may be read only through a documented compatibility adapter.

Canonical writers and examples must use current names.

A deprecated variable must define:

```text
old name
new name
precedence
warning policy
removal target
tests
```

Legacy GF Audit environment-variable aliases are accepted only through an explicit compatibility contract.

---

# 31. Configuration precedence

Configuration precedence is resolved per field.

General order:

```text
explicit invocation value
        ↓
GF Wordbench environment variable
        ↓
valid application-state value
        ↓
canonical default or documented discovery
        ↓
configuration error when required
```

Project-owned fields are resolved separately from `project.toml`.

Explicit invocation values include current CLI arguments or current GUI form values.

---

## 32. Project-root precedence

```text
1. explicit CLI --project-root
2. explicit current GUI project-root field
3. GF_WORDBENCH_PROJECT_ROOT
4. application-state environment.project_root
5. <framework_root>/project
6. failure
```

The first candidate that validates as a project root wins.

A higher-precedence invalid explicit value must produce an error.

It must not silently fall through to a lower value.

---

## 33. GF-executable precedence

```text
1. explicit CLI GF executable
2. explicit current GUI GF executable
3. GF_WORDBENCH_GF_EXE
4. application-state environment.gf_executable
5. optional PATH discovery
6. failure
```

Canonical project schema version `1.0` does not store a machine-local GF executable.

If `PATH` discovery succeeds:

- the discovered token is resolved to an explicit path;
- the explicit path is used for execution;
- the explicit path is recorded.

---

## 34. RGL-root precedence

```text
1. explicit CLI RGL root
2. explicit current GUI RGL root
3. GF_WORDBENCH_RGL_ROOT
4. application-state environment.rgl_root
5. documented installation-specific discovery
6. null when operation permits it
7. failure when required
```

Broad recursive filesystem search is prohibited.

Installation-specific discovery must be:

- deterministic;
- bounded;
- platform-documented;
- testable;
- visible in resolved configuration.

---

## 35. Output-root precedence

```text
1. explicit CLI output root
2. explicit current GUI output root
3. GF_WORDBENCH_OUTPUT_ROOT
4. application-state environment.output_root
5. <framework_root>/_gf_wordbench
6. failure
```

The winning path must pass write and safety validation before run creation.

---

## 36. State-path precedence

```text
1. explicit application startup option
2. GF_WORDBENCH_STATE_PATH
3. <framework_root>/.gf_wordbench_state.json
```

The state file does not select itself through values stored inside itself.

---

## 37. Project-field precedence

Project-owned fields use:

```text
project.toml value
        ↓
documented schema default
        ↓
configuration error when required
```

Environment variables must not override:

- project ID;
- language code;
- source directory;
- entrypoints;
- checkpoints;
- required scenarios;
- release requirements.

An explicit command may select a subset for a non-release run, but it does not rewrite project policy.

---

## 38. Explicit-value failure rule

An explicitly supplied path is an assertion by the caller.

If it is invalid:

- report the invalid value;
- report its source;
- stop resolution for that field;
- do not silently use state, environment, or discovery.

This rule prevents typographical errors from selecting an unintended installation.

---

## 39. Resolved-value provenance

Every significant resolved path should retain provenance:

```text
explicit_cli
explicit_gui
environment
state
default
discovery
project_config
derived
```

Provenance may be represented internally in a resolved-configuration record.

Reports may show provenance in diagnostic or strict modes.

The full provenance model does not need to be persisted in every summary field unless the schema requires it.

---

# 40. Project configuration path rules

Canonical `project.toml` path fields include:

```text
[project].root
[sources].directory
[gf].path_parts
[modules].entrypoints
[modules].checkpoints
scenario and validation asset paths
```

All project-owned path fields resolve against `project_root` unless a field explicitly declares another base.

---

## 41. `[project].root`

Canonical value:

```toml
[project]
root = "."
```

Version `1.0` expects `.` for the normal layout.

A different value requires:

- a documented layout;
- containment within the selected project root;
- explicit test coverage;
- no ambiguous double-root interpretation.

The selected `project_root` remains the directory containing `project.toml`.

---

## 42. `[sources].directory`

Example:

```toml
[sources]
directory = "lib/src/french"
```

Resolution:

```text
source_root = project_root / sources.directory
```

Validation:

- relative;
- normalized;
- contained;
- existing directory;
- not empty;
- no wildcard;
- no environment interpolation.

---

## 43. Source globs

`[sources].glob` is a filename-matching expression, not a path root.

Example:

```toml
glob = "*.gf"
```

Rules:

- evaluated below `source_root`;
- must not escape source root;
- recursive behavior must be explicit;
- path separators in glob syntax follow the file-selector contract;
- glob result ordering is normalized before use.

---

## 44. Entrypoint paths

Entrypoints may be represented as module filenames or documented project-relative source paths.

Resolution must be unambiguous.

Recommended rule:

- bare filename resolves under `source_root`;
- path containing `/` resolves against `project_root`;
- absolute entrypoint is rejected;
- missing entrypoint is a configuration or release error.

Examples:

```text
GrammarFre.gf
lib/src/french/GrammarFre.gf
```

`PROJECT_TOML_REFERENCE.md` defines the canonical entrypoint representation.

---

## 45. Checkpoint paths

Checkpoint paths follow the same resolution rules as entrypoints.

Declared order is semantically significant for reporting and validation order.

The resolver must not sort checkpoints if the project configuration deliberately orders them.

---

## 46. Scenario paths

Default scenario path:

```text
validation/scenarios/<scenario-id>.gfs
```

Scenario registry configuration may declare a different project-relative path.

Rules:

- `.gfs` extension;
- project-contained;
- read-only during normal validation;
- no inline environment expansion;
- stable scenario identity independent of absolute path.

---

## 47. Input paths

Validation inputs normally resolve under:

```text
validation/inputs/
```

A declared project-relative path outside that directory may be accepted only when:

- still inside `project_root`;
- documented by the project validation specification;
- read-only during normal validation.

Absolute input paths are prohibited in portable project configuration.

---

## 48. Gold paths

Default gold path:

```text
validation/gold/<scenario-id>.gold
```

Rules:

- project-contained;
- read-only during normal validation;
- no environment interpolation;
- no output-root reference;
- no run-relative reference;
- update only through the explicit gold-update operation.

---

# 49. GF search-path model

GF search paths are ordered because path order can affect module resolution.

Canonical project field:

```toml
[gf]
path_parts = [
  "lib/src",
  "lib/src/french",
  "abstract",
  "common",
  "prelude",
]
```

The resolver must preserve declared order.

---

## 50. Project-relative GF path parts

A non-reserved path part resolves against `project_root`.

Examples:

```text
lib/src
lib/src/french
shared
```

Resolved examples:

```text
C:/work/GF_Wordbench/project/lib/src
C:/work/GF_Wordbench/project/lib/src/french
C:/work/GF_Wordbench/project/shared
```

These paths must remain inside `project_root`.

---

## 51. RGL aliases

Canonical version `1.0` reserves these unqualified aliases:

```text
abstract
common
prelude
```

They resolve as:

```text
<rgl_root>/abstract
<rgl_root>/common
<rgl_root>/prelude
```

Rules:

- exact alias matching;
- no nested suffix under an alias in version `1.0`;
- aliases require `rgl_root`;
- unknown bare names are treated as project-relative paths;
- adding another reserved alias is a configuration-contract change.

Any alias syntax extension requires a schema-compatible documented contract change.

---

## 52. GF path resolution algorithm

For each declared `path_part` in order:

1. validate non-empty string;
2. reject absolute syntax;
3. normalize separators;
4. reject parent escape;
5. if exact reserved RGL alias:
   - require `rgl_root`;
   - resolve below `rgl_root`;
6. otherwise:
   - resolve below `project_root`;
7. validate directory according to mode;
8. deduplicate by platform-aware normalized identity;
9. preserve first occurrence;
10. append to the structured resolved list.

The resolver returns:

```text
ordered absolute Path values
provenance per path
warnings
```

---

## 53. Duplicate GF paths

Duplicate resolved paths are removed while preserving the first occurrence.

Duplicate comparison:

- case-insensitive on Windows;
- case-sensitive on normal POSIX filesystems;
- separator-normalized;
- based on normalized absolute identity;
- no lowercasing of the display path.

A duplicate warning may be emitted in strict mode.

---

## 54. Missing GF path part

Default behavior:

- required path part missing → configuration error;
- optional compatibility path missing → explicit warning only when the project schema marks it optional;
- release mode → no silent missing required path;
- diagnostic mode → may continue only when the affected operation can still execute meaningfully.

Version `1.0` treats configured `path_parts` as required. Optional path parts require a configuration-schema revision.

---

## 55. Command-line GF path representation

Internally:

```python
tuple[Path, ...]
```

At the GF command boundary, the command builder creates the version-supported path option.

Possible supported forms include:

```text
--path=<joined-path>
--gf-lib-path=<rgl-root>
```

The join separator uses the platform or GF contract:

```text
Windows: ;
POSIX:   :
```

The structured path list remains authoritative.

A persisted summary should prefer the structured list rather than only the joined string.

---

## 56. No ambient GF path

GF Wordbench must not depend silently on a developer’s global:

```text
GF_LIB_PATH
```

Policy:

- detect the variable when it could affect GF;
- override or neutralize it according to the resolved command contract;
- record the applied policy;
- never let tests pass only because a developer has it configured.

Other GF-version-specific path variables require an explicit compatibility rule before use.

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
2. applies documented removal or neutralization of ambient variables that would alter GF path behavior invisibly;
3. applies explicit safe overrides;
4. passes the resulting mapping only to the child;
5. records the policy identifier;
6. records explicit non-secret overrides;
7. does not persist the full environment.

This policy balances platform compatibility with reproducibility.

---

## 59. Required inherited operating-system context

GF Wordbench should not maintain a brittle universal allowlist for all child-process environment values.

The controlled-inherit policy retains ordinary operating-system context needed by executables, such as:

```text
PATH
system runtime variables
temporary-directory variables
locale variables
user-profile variables needed by the platform
```

However:

- retained values are not automatically recorded;
- path-affecting GF variables are handled explicitly;
- secrets are not copied into reports;
- operation-specific overrides remain visible.

---

## 60. `PATH`

`PATH` may be used for the initial optional discovery of `gf`.

After discovery:

- resolve the executable to an explicit path;
- use that path for the run;
- record that path;
- do not rerun discovery for each operation.

Changing `PATH` after request resolution must not change the selected executable.

---

## 61. Temporary-directory variables

Operating-system variables such as:

```text
TEMP
TMP
TMPDIR
```

may be inherited.

GF Wordbench-owned temporary files should still prefer `temporary_root` when same-filesystem containment or atomic replacement matters.

A child tool’s private temporary behavior is external-tool behavior and should be captured only when it affects the contract.

---

## 62. Locale variables

Locale variables may affect tool wording or encoding.

The policy:

- use explicit UTF-8 file and stream handling;
- record relevant explicit locale overrides;
- avoid relying on locale-specific diagnostic text when stable structured evidence exists;
- keep diagnostic fixtures tagged with platform and locale;
- avoid changing locale silently between CLI and GUI.

A forced locale is permitted only when supported by the selected GF and documented.

---

## 63. Environment override safety

Explicit process environment overrides must:

- use string keys and values;
- reject NUL characters;
- be scoped to one child process;
- avoid secrets where possible;
- mark secret keys for redaction when unavoidable;
- not overwrite project configuration;
- not be persisted as a complete environment dump.

---

## 64. Environment evidence

A process-backed result should preserve:

```text
environment policy identifier
explicit override keys
non-sensitive override values
redaction markers
```

It should not preserve:

```text
complete inherited environment
unrelated user variables
secrets
```

Environment provenance must be sufficient to explain material behavior without leaking private data.

---

# 65. Relative input paths

Relative user input is resolved at one explicit boundary.

### `--project-root`

Relative to the invocation current working directory.

### Other machine-local CLI paths

Relative to the invocation current working directory, then converted to absolute resolved values.

Examples:

```text
--gf-exe tools/gf/gf.exe
--rgl-root ../gf-rgl/src
--output-root runs
```

The invocation current working directory must be recorded or available during configuration diagnosis.

After bootstrap, no machine-local path remains relative.

---

## 66. GUI path inputs

GUI path pickers should produce absolute paths.

Typed relative GUI input must either:

- be rejected with a clear message; or
- resolve against a clearly displayed base before submission.

It must not resolve against an invisible GUI process directory.

---

## 67. Application-state paths

Application state stores machine-local paths as resolved absolute strings or `null`.

It must not store:

- unresolved relative machine paths;
- `%VAR%` expressions;
- `$VAR` expressions;
- `~`;
- project-owned source paths as environment configuration.

Legacy relative values may be migrated only with an explicit known base.

---

## 68. Project-relative persistence

Canonical project paths are serialized with:

```python
relative_path.as_posix()
```

or equivalent semantics.

Before serialization:

- verify containment;
- reject unresolved parent escape;
- preserve Unicode;
- preserve case;
- avoid drive-relative forms.

A failure to relativize a supposed project path is a contract error.

---

## 69. Run-relative persistence

Canonical run artifact paths are serialized relative to `run_dir`.

Examples:

```text
summary.md
raw/master.log
artifacts/pgf/Grammar.pgf
```

A report must not store a different base for the same artifact field.

Legacy absolute run paths may be converted during migration when containment is provable.

---

## 70. Environment-path persistence

Environment paths may be persisted as absolute strings for traceability.

Canonical separator:

```text
/
```

Examples:

```text
C:/Program Files/GF/bin/gf.exe
C:/work/gf-rgl/src
```

Readers accept native `\` for legacy Windows files.

A portable export may redact environment path prefixes but must mark the redaction.

---

# 71. Path normalization

Normalization converts path syntax into a consistent internal identity without changing the target intentionally.

Steps:

1. validate input type;
2. trim only unintended surrounding whitespace from user fields;
3. reject NUL;
4. expand an explicitly allowed user-input form;
5. apply the documented base;
6. normalize `.` components;
7. reject prohibited `..` escape;
8. convert to an absolute internal `Path` for environment/runtime paths;
9. preserve original case for display;
10. perform platform-aware identity comparison;
11. validate containment and type.

Normalization is not existence validation.

---

## 72. Whitespace

User-entered machine-local path fields may trim surrounding whitespace.

Project-owned paths must preserve meaningful internal spaces.

Examples:

```text
C:/Program Files/GF/bin/gf.exe
validation/inputs/example sentences.txt
```

Generated filenames should avoid trailing spaces and platform-invalid endings.

Quoted text entered through a GUI field is not automatically shell quoting and should not be retained as literal quote characters unless the quotes are part of the filename.

---

## 73. Dot components

Allowed:

```text
.
```

during resolution.

Canonical persisted project and run paths should not contain redundant `.` segments.

Parent components:

```text
..
```

may appear in initial machine-local CLI input only before resolution.

They are prohibited in canonical project and run-relative persistence.

---

## 74. User-home expansion

Project files do not use `~`.

CLI machine-local input may support `~` expansion when:

- the expansion is explicit and documented;
- expansion occurs before the run request is resolved;
- the resolved absolute path is recorded;
- Windows behavior is tested.

Application state stores the resolved path, not `~`.

---

## 75. Environment-variable expansion

Inline environment-variable expansion is disabled by default.

The recognized `GF_WORDBENCH_*` variables provide complete values instead.

This avoids:

- platform-specific `%NAME%` versus `$NAME`;
- accidental secret interpolation;
- clone-dependent project files;
- unresolved placeholders;
- double expansion.

Inline interpolation can be introduced only by a new configuration contract.

---

## 76. Filesystem resolution

Do not call unrestricted `resolve()` blindly on untrusted paths when it may require inaccessible or non-existent targets.

Use an operation-appropriate strategy:

- existing input: resolve or canonicalize the existing target;
- new output: resolve the existing parent, then append the validated filename;
- broken symlink: reject or report explicitly;
- unavailable network path: preserve the original candidate in the error.

---

# 77. Path containment

Containment protects project and run boundaries.

Required roots:

```text
project_root
run_dir
rgl_root for RGL aliases
framework_root for framework assets
temporary_root for temporary files
```

A path owned by one root must not escape into another root accidentally.

---

## 78. Lexical containment

Lexical validation rejects:

- absolute project-owned paths;
- `..` escape;
- drive changes;
- UNC changes;
- malformed separators;
- empty required components.

Lexical containment is necessary but not sufficient when symlinks or junctions exist.

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

A symlink or Windows junction can cross lexical boundaries.

Default policy:

- read-only project assets may traverse contained links only when resolved target remains inside an allowed root;
- generated run outputs must not follow a link outside `run_dir`;
- release and gold-update operations use strict resolved containment;
- ambiguous or inaccessible links produce an error;
- the manifest records the final artifact path, not an unverified external target.

A project intentionally using external linked sources requires an explicit project and security policy.

It is not the default portable model.

---

## 81. Root equality

Some paths may equal their root:

- project configuration at project root;
- run report at run root;
- RGL root itself.

Containment checks must distinguish:

```text
inside-or-equal
strictly-inside
```

Generated child artifacts normally require strictly-inside, except canonical files directly under `run_dir`.

---

## 82. Cross-root prohibition

The following are prohibited by default:

- source directory inside output root;
- output root inside source directory;
- state file inside gold directory;
- run directory inside RGL;
- temporary root inside project source;
- project initialization writing into active run artifacts;
- report detail copier reading arbitrary external diagnostic-mentioned files.

Bootstrap should detect dangerous overlap.

---

# 83. Path type validation

Paths are validated by expected type.

| Field | Expected type |
|---|---|
| `framework_root` | directory |
| `project_root` | directory |
| `project_config_path` | regular file |
| `source_root` | directory |
| `gf_executable` | regular executable file |
| `rgl_root` | directory when required |
| `output_root` | directory or creatable directory |
| `run_dir` | new directory |
| `state_path` | file path with creatable parent |
| scenario path | regular `.gfs` file |
| gold path | regular `.gold` file when required |
| entrypoint | regular `.gf` file |
| checkpoint | regular `.gf` file |

A directory must not be accepted where a file is required.

---

## 84. Readability and writability

Required checks should be operation-specific.

### Inputs

Check:

- existence;
- expected type;
- readability where practical;
- containment.

### Outputs

Check:

- parent existence or creatability;
- parent writability where practical;
- collision policy;
- containment;
- no source overwrite.

A preflight writability check cannot guarantee a later write.

Write failures remain explicit runtime errors.

---

## 85. Executability

On POSIX, executable permission should be checked where meaningful.

On Windows:

- regular-file status;
- supported executable form;
- launch result.

A file that exists but cannot launch produces a launch failure.

A `.bat` or `.cmd` file is not treated as a native executable by the generic GF execution path.

---

# 86. Windows path policy

Windows is a first-class supported environment.

GF Wordbench must support:

- drive-letter absolute paths;
- spaces;
- Unicode;
- mixed user-input separators;
- case-insensitive identity;
- executable paths outside the project;
- long paths where Python and the operating system support them.

---

## 87. Windows separators

Accepted input:

```text
C:\work\project
C:/work/project
```

Internal representation uses `Path`.

Canonical persistence uses:

```text
C:/work/project
```

Project and run-relative canonical persistence always uses `/`.

---

## 88. Windows drive letters

Absolute environment path:

```text
C:/work/project
```

Drive-relative path:

```text
C:work/project
```

is prohibited because its base depends on hidden per-drive process state.

Drive-letter comparison is case-insensitive.

Canonical display may preserve the resolved drive casing returned by the platform.

---

## 89. UNC paths

UNC environment paths may be accepted:

```text
//server/share/project
```

when:

- the path is reachable;
- the operation supports network filesystem semantics;
- required atomic-write behavior is available or safely degraded;
- timeout and disconnection behavior are tested.

Canonical project-relative fields never contain UNC paths.

Release workflows should warn when filesystem semantics cannot guarantee required atomicity.

---

## 90. Extended-length Windows paths

Internal Windows paths may use extended-length syntax where required by the runtime:

```text
\\?\C:\...
```

Canonical persisted paths should not expose this prefix unless necessary to identify an otherwise unrepresentable environment path.

Path utility functions own any prefix conversion.

Callers must not add the prefix independently.

---

## 91. Windows case behavior

Path identity is case-insensitive for ordinary Windows filesystems.

Rules:

- do not lowercase paths for display;
- use a normalized comparison key;
- preserve actual path text in reports;
- treat case-only duplicates as duplicates;
- do not assume a case-only rename is portable.

Project module-name semantics remain GF semantics and are not redefined by filesystem comparison.

---

## 92. Windows reserved names

Generated path components must avoid reserved device names such as:

```text
CON
PRN
AUX
NUL
COM1
LPT1
```

The shared safe-name utility owns generated-name sanitization.

Source project files with unsupported names must produce a clear configuration error.

---

## 93. Windows trailing dots and spaces

Generated names must not end with:

```text
.
space
```

because Windows may normalize them unexpectedly.

Canonical project paths should reject ambiguous trailing-dot or trailing-space components in strict mode.

---

## 94. Windows junction safety

Junctions are treated like symlinks for containment.

A lexical path below `run_dir` whose junction target escapes the run is unsafe for generated output.

Strict release and gold-update operations must verify resolved containment.

---

## 95. Windows command safety

Paths containing spaces are passed as separate process arguments.

GF Wordbench must not manually quote the executable into one command string.

Correct:

```python
[gf_executable, "--version"]
```

Incorrect:

```text
"C:\Program Files\GF\gf.exe" --version
```

as one opaque execution string.

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

A project that differs only by path case may not be portable to Windows.

Portability checks should detect case-colliding project assets.

---

## 97. Cross-platform portability checks

Recommended strict checks:

- no case-colliding project-relative paths;
- no Windows reserved generated names;
- no backslash-only project semantics;
- no drive-relative path;
- no path depending on shell expansion;
- no source path escaping project root;
- no absolute project-owned path;
- no project file requiring a machine-specific RGL root;
- no duplicate GF paths after platform normalization.

---

# 98. Run-directory creation

Run ID format:

```text
YYYYMMDD_HHMMSS
```

The timestamp represents UTC.

Directory name:

```text
run_<run-id>
```

Collision suffix:

```text
run_20260722_184500_02
```

Creation must be exclusive.

Run-directory creation must be exclusive and handle race conditions.

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

The following filenames must have one owner:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master.log
ALL_SCAN_LOGS.TXT
ALL_LOGS.TXT
```

Consumers receive paths through `RunPaths`.

They must not define local constants with the same ownership role.

---

## 101. Artifact subject keys

Per-subject artifact filenames must use a shared safe key.

The key must be:

- deterministic;
- path-safe;
- collision-resistant;
- stable within one schema/contract version;
- independent of absolute project location.

When two source paths share a filename, the key must incorporate project-relative path identity or a stable suffix.

---

## 102. Artifact collision

Before writing an owned artifact:

- validate target containment;
- ensure no other active owner has reserved the path;
- apply the artifact collision policy;
- never overwrite a prior run;
- never overwrite project source or gold.

Collision is a contract or artifact error.

It is not silently resolved by dropping evidence.

---

## 103. Atomic report paths

Stable reports use sibling temporary files where supported.

Example:

```text
summary.json.tmp
        → validate
        → atomic replace summary.json
```

The temporary path must:

- remain beside the destination;
- use a collision-safe suffix;
- not appear as a final manifest artifact;
- be cleaned after success.

---

## 104. Tool-generated artifact paths

GF may generate:

```text
.gfo
.pgf
```

The command owner declares expected destinations.

Preferred destinations are below:

```text
artifacts/gfo/
artifacts/pgf/
```

If a GF version cannot write directly to the final owned directory:

1. use an owned temporary or build directory;
2. preserve tool output;
3. copy or move through a documented stage;
4. verify size and identity;
5. catalog the final artifact;
6. do not alter the artifact content.

---

## 105. Previous-run paths

Previous-run comparison may use:

- the last compatible run recorded in state;
- a run selected explicitly;
- deterministic discovery below the output root.

The selected summary must:

- exist;
- validate under a supported schema or migrator;
- not equal the current run summary;
- remain read-only;
- have its path provenance recorded.

Discovery must not parse Markdown to identify a run.

---

## 106. Run discovery

When automatic previous-run discovery is enabled:

1. enumerate direct candidate run directories below `output_root`;
2. validate canonical or supported legacy naming;
3. locate `summary.json`;
4. ignore current run;
5. load metadata;
6. filter for compatible project identity;
7. select by finished timestamp, not directory text alone;
8. preserve deterministic tie-breaking.

A malformed candidate must not crash all discovery.

---

# 107. Application state and paths

Canonical state environment fields:

```text
project_root
rgl_root
gf_executable
output_root
```

Each field is:

```text
string or null
```

State is convenience data for one invocation environment. It is not a project registry, language selector or source of project identity.

Project-owned source configuration must not migrate into state after `project.toml` is authoritative.

---

## 108. State loading

State loading must:

- tolerate missing file;
- reject or safely default invalid fields;
- validate schema version;
- preserve the source during migration;
- not make the framework unusable because state is corrupt;
- not launch tools;
- not silently treat project settings as local environment values.

---

## 109. State saving

State saving must:

- write atomically;
- create the parent directory safely;
- store resolved paths;
- omit secrets;
- omit transient process handles;
- omit active run results;
- omit project entrypoints and scenario policy;
- use canonical separators.

The GUI may save user-confirmed machine-local fields after validation. It must not persist a list of selectable language projects.

---

# 110. CLI and GUI equivalence

Equivalent resolved values from CLI and GUI produce equivalent resolved run requests.

Both interfaces use:

```text
same project loader
same environment reader
same path resolver
same validation rules
same precedence semantics
same RunPaths builder
```

Interface-specific path normalization is prohibited after bootstrap.

---

## 111. CLI display

The CLI configuration-inspection surface displays, for each significant path:

```text
resolved value
source or provenance
validation result
```

Exact command spelling and options are owned by `docs/usage/CLI_REFERENCE.md`.

The CLI inspection surface does not replace internal validation and does not expose secrets or a complete inherited environment.

---

## 112. GUI display

The GUI displays resolved:

- project root;
- project configuration;
- source root;
- GF executable;
- GF version after probe;
- RGL root;
- output root;
- next run location;
- configuration warnings;
- provenance when an environment value overrides stored convenience state.

The GUI uses the same projects and configuration application boundaries as the CLI. It does not maintain a separate project registry or path-resolution policy.

---

# 113. Error model

Path and environment failures normally produce:

```text
validation_status = ERROR
error_kind = CONFIG, IO, TOOL, CONTRACT, or ARTIFACT
```

They do not become GF language failures.

---

## 114. Configuration errors

Examples:

- project root missing;
- `project.toml` absent;
- absolute project-owned path;
- invalid path part;
- missing required RGL root;
- duplicate scenario path;
- output root overlaps source root;
- unresolved environment variable expression;
- unsupported state schema.

These should be detected before GF execution.

---

## 115. I/O errors

Examples:

- permission denied;
- directory cannot be created;
- state cannot be written;
- report atomic replacement fails;
- source cannot be read;
- network path disappears.

The error should preserve:

- operation;
- normalized path;
- path role;
- operating-system detail;
- safe remediation context.

---

## 116. Tool-location errors

Examples:

- GF executable missing;
- path points to directory;
- unsupported launcher type;
- executable disappears after resolution;
- executable cannot launch.

A preflight invalid path is configuration error.

A race or launch denial after preflight is launch failure.

---

## 117. Containment errors

Normalized message should identify:

```text
candidate path
expected root
path role
containment stage
```

Sensitive prefixes may be redacted in portable export.

Containment errors are contract or security errors.

They must not be auto-corrected by moving the target silently.

---

## 118. Artifact-path errors

Examples:

- duplicate writer target;
- run artifact escapes run root;
- required output absent;
- output collides with prior artifact;
- unsafe subject-derived filename.

These are artifact or contract errors.

---

# 119. Persistence rules

Persisted project and run paths must follow the schema lock.

Summary:

| Path category | Persistence form |
|---|---|
| Project asset | Project-relative `/` |
| Source result | Project-relative `/` |
| Run artifact | Run-relative `/` |
| GF executable | Absolute environment path |
| RGL root | Absolute environment path |
| Project root | Absolute environment path where run metadata requires it |
| Output root | Absolute environment path where run metadata requires it |
| State-local path | Absolute |
| Temporary path | Normally not persisted |

---

## 120. Legacy Windows paths

Legacy readers accept:

```text
C:\work\project\file.gf
```

Migration should:

1. parse Windows syntax even on a non-Windows host when possible;
2. determine whether the path belongs to known project or run roots;
3. convert to project-relative or run-relative form;
4. preserve as environment path if that is its actual role;
5. report ambiguity or loss;
6. leave the source untouched.

---

## 121. Legacy relative paths

A legacy relative path is migratable only when its historical base is known.

Possible bases:

```text
legacy project root
legacy run directory
legacy process working directory
legacy application directory
```

If the base is ambiguous:

- preserve the original text in migration evidence;
- mark a loss or warning;
- do not guess silently.

---

## 122. Legacy GF path strings

A legacy joined GF path string may be split only using its known source platform separator.

Migration must know or infer safely:

```text
Windows ;
POSIX :
```

Windows drive colons make naive colon splitting unsafe.

Canonical migration output should store the structured ordered path list when the target schema supports it.

---

# 123. Security rules

Paths are untrusted input until validated.

Required protections:

- no shell interpolation;
- no NUL;
- containment;
- generated-name sanitization;
- no source overwrite;
- no normal-run gold write;
- no arbitrary diagnostic-path copying;
- no complete environment dump;
- no secret interpolation;
- explicit executable path;
- output collision control;
- no `gf-portfolio` path or state dependency.

---

## 124. Diagnostic-mentioned paths

GF output may mention paths.

A diagnostic parser may extract them as text.

Before opening such a path:

1. identify expected path class;
2. map against known project, RGL, or run inventories;
3. validate containment;
4. reject arbitrary external paths;
5. preserve the original diagnostic regardless.

A report detail writer must not copy a file merely because GF output named it.

---

## 125. Project import safety

Initializing or replacing `project/` must:

- target the explicit project root;
- avoid following unsafe links;
- not overwrite framework files;
- not copy application state;
- not copy generated run artifacts;
- validate the resulting project configuration;
- preserve a backup under the explicit reset/migration policy.

This document does not define the full project lifecycle.

---

# 126. Testing architecture

Required coverage is organized around:

```text
tests/paths/
├── test_path_classes.py
├── test_path_precedence.py
├── test_project_paths.py
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

Contract tests:

```text
tests/contracts/test_environment_contract.py
tests/contracts/test_filesystem_contract.py
tests/contracts/test_windows_contract.py
tests/contracts/test_path_ownership_contract.py
```

Schema tests:

```text
tests/schemas/test_project_paths.py
tests/schemas/test_state_paths.py
tests/schemas/test_summary_paths.py
tests/schemas/test_manifest_paths.py
```

---

## 127. Precedence tests

Test each path field with:

- explicit value only;
- environment only;
- state only;
- default only;
- every source set;
- invalid higher-precedence explicit value;
- empty environment value;
- corrupt state value;
- discovery success;
- discovery failure;
- provenance reporting.

---

## 128. Project-path tests

Required cases:

- simple relative path;
- nested relative path;
- `.` normalization;
- parent escape;
- absolute Windows path;
- absolute POSIX path;
- backslash canonicalization;
- Unicode;
- spaces;
- missing source directory;
- entrypoint missing;
- scenario outside root;
- gold outside root;
- symlink escape;
- junction escape.

---

## 129. GF-path tests

Required cases:

- project-relative part;
- `abstract` alias;
- `common` alias;
- `prelude` alias;
- missing RGL root;
- missing path directory;
- duplicate paths;
- duplicate case variation on Windows;
- stable declared order;
- Windows `;` rendering;
- POSIX `:` rendering;
- ambient `GF_LIB_PATH`;
- no global-environment dependency.

---

## 130. Executable tests

Required cases:

- explicit existing GF executable;
- path containing spaces;
- Unicode path;
- missing file;
- directory passed as executable;
- non-executable POSIX file;
- `.bat` or `.cmd` rejection for native GF path;
- `PATH` discovery;
- discovery result recorded;
- explicit invalid path does not fall through;
- executable disappears before launch.

---

## 131. Output-root tests

Required cases:

- default root;
- explicit root;
- environment root;
- state root;
- creatable missing directory;
- permission denied;
- overlaps source root;
- equals RGL root;
- run collision;
- concurrent run creation;
- UNC path where supported;
- atomic report write behavior.

---

## 132. Persistence tests

Required cases:

- project path uses `/`;
- run path uses `/`;
- source result is project-relative;
- environment path remains absolute;
- no `..`;
- no environment interpolation;
- legacy backslash accepted;
- legacy absolute source converted;
- ambiguous legacy path warns;
- stable round trip.

---

## 133. Security tests

Required cases:

- path traversal;
- symlink escape;
- junction escape;
- NUL;
- Windows reserved generated name;
- shell metacharacters remain literal path text;
- diagnostic path cannot trigger arbitrary copy;
- source cannot become report destination;
- gold cannot become raw log destination;
- secret environment value is not reported;
- output root cannot overwrite project template.

---

## 134. Cross-platform fixture policy

Tests use temporary roots and avoid a developer’s real environment.

Real-GF integration tests may read explicit test-only environment values.

They must not pass only because:

```text
GF_LIB_PATH
PATH
current working directory
user profile
IDE settings
```

happen to contain usable local values.

---

# 135. Path-resolution application boundary

The application exposes cohesive operations equivalent to:

```python
resolve_environment(...)
resolve_active_project(...)
resolve_project_paths(...)
allocate_run_paths(...)
```

The exact model and operation names are governed by `docs/architecture/DATA_MODEL.md` and `docs/architecture/COMPONENT_MAP.md`.

Required boundaries:

- entrypoints provide explicit values;
- the projects module resolves active-project paths;
- the runs module allocates run-owned paths;
- adapters perform filesystem and platform operations through ports;
- reporting receives canonical artifact paths from the run context;
- no consumer reconstructs an owned path independently.

---

## 136. Shared path operations

Cohesive path operations cover:

```text
normalize user-supplied environment path
resolve environment path
resolve project-relative path
resolve run-relative path
serialize project path
serialize run path
serialize environment path
verify containment
build a safe artifact key
create an exclusive run directory
```

A shared operation does not hide ownership or business policy. It receives explicit values, roots and path classes.

---

## 137. Shared path-operation restrictions

Shared path operations must not:

- read GUI widgets;
- read CLI parser objects;
- load project configuration independently of the projects module;
- launch GF;
- decide release policy;
- own report prose;
- invent active-language paths;
- silently expand arbitrary environment expressions;
- read or write `gf-portfolio` configuration.

---

# 138. Drift indicators

Environment or path drift exists when:

- CLI and GUI resolve different paths from equivalent inputs;
- a framework module hardcodes an active-language path;
- `project.toml` contains absolute GF, RGL, or output paths;
- application state contains entrypoints or required scenarios;
- a report reconstructs an artifact filename;
- GF path order changes;
- compilation and scenarios construct different GF paths;
- tests rely on ambient `GF_LIB_PATH`;
- a relative machine path survives into the resolved run request;
- project paths persist with drive letters;
- run artifact paths persist as absolute without reason;
- an inline `%VAR%`, `$VAR`, or `~` is silently expanded in project config;
- output root overlaps source root;
- a symlink escapes an owned root;
- one path is normalized differently by writer and reader;
- Windows path comparison lowercases displayed paths;
- `PATH` discovery is repeated after configuration resolution;
- environment values change behavior without provenance;
- a run directory is reused;
- a generated filename differs between components;
- state corruption prevents command-line use;
- a migration guesses an ambiguous path base;
- Wordbench reads a Portfolio registry to resolve its active project.

Any drift indicator requires coordinated review.

---

# 139. Change classification

## 139.1 Internal compatible change

Examples:

- faster containment algorithm with unchanged semantics;
- private helper refactor;
- clearer error text with same semantic fields;
- platform-specific internal optimization with unchanged semantics.

Requirements:

- same resolved values;
- same precedence;
- same persistence;
- tests pass.

## 139.2 Compatible extension

Examples:

- optional new environment variable;
- optional provenance field;
- optional new project-relative path field;
- additional strict-mode warning.

Requires:

- safe default;
- documentation;
- tests;
- schema minor version when persisted.

## 139.3 Breaking change

Examples:

- precedence reorder;
- environment-variable rename;
- path base change;
- new implicit expansion;
- canonical separator change;
- artifact filename change;
- ownership transfer;
- RGL alias semantic change;
- output-root default change after users depend on it;
- project path becoming absolute;
- state path relocation without migration.

Requires:

1. impact analysis;
2. schema review;
3. compatibility adapter;
4. migration;
5. tests;
6. documentation update;
7. contract-lock update;
8. changelog entry.

---

# 140. Configuration review checklist

```text
[ ] framework_root is deterministic
[ ] project_root contains project.toml
[ ] project-root provenance is known
[ ] source_root is project-contained
[ ] GF executable is explicit
[ ] GF executable is recorded
[ ] RGL root is explicit when required
[ ] GF path parts preserve declared order
[ ] RGL aliases resolve under RGL root
[ ] ambient GF path variables are controlled
[ ] output root is writable
[ ] output root does not overlap source
[ ] run directory is new and exclusive
[ ] state path is machine-local
[ ] project paths contain no interpolation
[ ] project paths serialize with /
[ ] run paths serialize relative to run_dir
[ ] environment paths are absolute after bootstrap
[ ] CLI and GUI use the same resolver
[ ] path containment is checked
[ ] symlink/junction behavior is safe
[ ] secrets and full environment are not reported
```

---

# 141. Governing invariants

1. Every path has a declared class and base.
2. Portable project paths are project-relative.
3. Run artifact paths are run-relative.
4. Machine-local paths are resolved before execution.
5. `project.toml` contains no absolute GF, RGL, or output path.
6. Application state contains no language-project architecture.
7. Environment variables override complete local values, not path fragments.
8. Inline environment interpolation is disabled.
9. Explicit invalid input does not silently fall through.
10. Path provenance remains inspectable.
11. The GF executable is explicit and stable for the run.
12. `PATH` discovery is optional and occurs only before resolution finalizes.
13. The RGL is not found through unbounded filesystem search.
14. GF path order is preserved.
15. Compilation and scenarios use the same GF path resolver.
16. Ambient `GF_LIB_PATH` cannot silently determine test or run behavior.
17. Working directories are explicit.
18. Output root does not overlap project source or RGL.
19. Every run directory is new and exclusive.
20. `RunPaths` owns generated artifact locations.
21. Consumers do not reconstruct owned paths.
22. Containment accounts for symlinks and Windows junctions.
23. Canonical persisted separators use `/`.
24. Windows paths with spaces and Unicode are supported.
25. Drive-relative Windows paths are prohibited.
26. Source, scenario, input, and gold assets remain read-only during normal validation.
27. Temporary files remain inside owned locations.
28. Full inherited environments and secrets are not persisted.
29. Migration never guesses an ambiguous path base silently.
30. Path-contract changes are coordinated across configuration, execution, persistence, tests, and documentation.
31. One run resolves exactly one active project root and one normative language target.
32. Wordbench path resolution does not read a Portfolio registry or depend on `gf-portfolio`.
33. Portfolio consumption, when used, begins only at finalized public Wordbench artifacts.

---

# 142. Governing rule

GF Wordbench path resolution follows one explicit chain:

```text
portable project declarations
        +
machine-local environment selection
        +
documented precedence
        ↓
validated absolute runtime roots
        ↓
contained project and run paths
        ↓
structured GF search path
        ↓
recorded execution evidence
        ↓
portable persisted references
```

A path is valid only when its owner, base, provenance, containment, runtime target, and persistence form all agree.
