# GF Wordbench — GF Path Resolution

**Document ID:** `GF-WB-GF-PATH-RESOLUTION`  
**Status:** Normative technical specification  
**Applies to:** GF compilation, native `.gfs` scenarios, grammar loading, introspection, and PGF construction for one active Wordbench project  
**Owner:** GF Wordbench maintainers  
**Normative counterparts:**  
- `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/configuration/PROJECT_TOML_REFERENCE.md`
- `docs/configuration/ENVIRONMENT_AND_PATHS.md`
- `docs/decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md`

**Document version:** `1.1.0`  
**Last reviewed:** 2026-08-05

---


## ADR-0015 alignment — selected source and optional validation profile

The current startup model is path-resolved:

- the user selects a GF source file or an RGL language directory directly;
- Wordbench reads that source tree in place and does not copy it into this repository;
- `ResolvedLanguageContext` owns the selected path, resolved language identity, source root, RGL root, discovered entrypoints and effective GF-path facts;
- an explicit `ValidationProfile` is optional and may add only non-derivable policy such as additional selection filters, required or release entrypoints, checkpoints, scenarios, inputs, golds, PGF targets, required artifacts and release gates;
- a legacy `project/project.toml` may be read only when explicitly supplied as a validation profile; it is not a mandatory root file or startup authority;
- run state, logs and artifacts are written under the configured output root, normally `<output-root>/<language-key>/run_<run-id>` (with `_gf_wordbench` as the framework default), never into the selected source tree.

Unless a section is explicitly describing legacy migration input, references to an “active project” or a root `project/` directory are superseded by this model.

---
## 1. Purpose

This document defines how GF Wordbench constructs, validates, records, and supplies the GF module search path.

The GF search path determines where GF resolves imported modules, compiled modules, RGL resources, project helpers, and other dependencies. A path that differs between compilation, scenarios, and release builds can produce false failures, false successes, or machine-specific behavior.

GF Wordbench therefore uses one centralized path-resolution process inside the GF anti-corruption boundary.

The resolver operates for exactly one selected language context in one run. Validation use cases request GF operations through `GfToolPort`; the GF adapter resolves and supplies the effective path together with its provenance.

> Every GF operation in one run MUST consume the same resolved GF path unless the operation declares and records an explicit contract-specific extension.

This document does not define GF module-resolution semantics. GF remains authoritative for resolving modules from the path it receives.

---

## 2. Scope

This specification governs:

- project path entries declared in `<validation-profile-root>/project.toml`;
- explicit run-level GF path overrides;
- source-relative source paths;
- RGL-root resolution;
- documented RGL aliases;
- optional inherited-environment fallback;
- path normalization;
- path deduplication;
- path existence checks;
- Windows path handling;
- command-line serialization;
- recorded path evidence;
- path compatibility across compilation, scenarios, and PGF builds;
- migration from the former `gf-audit` path builder;
- isolation of path resolution from `gf-portfolio` and other external consumers.

This specification does not govern:

- discovery of the `gf` or `gf.exe` executable;
- source-file selection;
- generated artifact directories;
- report retention;
- GF's internal precedence rules;
- module-to-module contracts inside the active language project;
- the contents of RGL modules;
- discovery, indexing, or orchestration of several Wordbench workspaces by `gf-portfolio`.

---

## 3. Terminology

- **PROJECT ROOT**: resolved root of the active GF Wordbench project.
- **SOURCE ROOT**: primary source-relative directory containing active-language GF sources.
- **RGL ROOT**: local filesystem directory containing the installed or checked-out GF Resource Grammar Library.
- **PATH PART**: one directory supplied to GF as part of its module search path.
- **PROJECT PATH PART**: source-relative path declared by the selected language context.
- **RGL ALIAS**: documented short name that resolves beneath the configured RGL root.
- **EXPLICIT PATH**: complete GF path supplied directly for one run.
- **DERIVED PATH**: path constructed from project configuration and the environment.
- **EFFECTIVE PATH**: ordered, normalized, validated, deduplicated path used by GF.
- **PATH SOURCE**: origin of a path part, such as explicit override, project configuration, RGL alias, or environment fallback.
- **PORTABLE PATH**: path stored relative to the resolved source root and using `/`.
- **ENVIRONMENT PATH**: machine-local absolute path such as the RGL root.
- **STRICT MODE**: mode that treats unsupported, missing, or ambiguous path configuration as an error.

---

## 4. Authority and ownership

### 4.1 Resolved language-context authority

The selected language context owns its portable GF path declaration:

```text
<validation-profile-root>/project.toml
```

The authoritative field is:

```toml
[gf]
path_parts = []
```

This ordered list defines project requirements, not machine-local installation paths.

### 4.2 Environment authority

Machine-local values are supplied through resolved application configuration:

- resolved source root;
- RGL root;
- GF executable;
- output root;
- optional explicit GF path.

These values may be stored in local application state or supplied through CLI or GUI inputs.

They MUST NOT be written as canonical absolute paths into the reusable project template.

### 4.3 Framework authority

The framework owns:

- interpreting path declarations;
- resolving aliases;
- canonicalizing directories;
- validating allowed roots;
- deduplicating entries;
- producing the effective path;
- passing it to GF;
- recording it in run metadata.

### 4.4 Single owner

Exactly one GF anti-corruption adapter MUST own effective GF path construction.

Canonical adapter role:

```text
app/adapters/gf/path_resolver.py
```

Canonical operation:

```python
resolve_gf_path(request: GFPathRequest) -> GFPathResolution
```

`GfToolPort` accepts typed GF operations. The GF adapter consumes `GFPathResolution` when translating those operations into executable requests.

Compilation, scenario execution, introspection, version-specific command construction, and PGF construction MUST NOT implement independent path-building logic.

### 4.5 Portfolio boundary

`gf-portfolio` MAY consume completed public Wordbench run artifacts that describe the effective GF path.

It MUST NOT:

- supply or override Wordbench path configuration;
- register several workspaces inside the Wordbench resolver;
- introduce Portfolio roots, project IDs, or storage paths into `project.toml`;
- become a dependency of `GfToolPort`, the resolver, or any Wordbench run.

---

## 5. Configuration model

### 5.1 Resolved language context and optional profile

Canonical example:

```toml
[project]
root = "."

[sources]
directory = "lib/src/french"

[gf]
path_parts = [
  "lib/src",
  "lib/src/french",
  "abstract",
  "common",
  "prelude",
]
```

### 5.2 Meaning of `path_parts`

Each item is one of:

1. a source-relative path;
2. a documented RGL alias;
3. an explicitly prefixed RGL-relative path.

Canonical accepted forms:

```text
lib/src
lib/src/french
project:lib/src
rgl:abstract
rgl:common
rgl:prelude
abstract
common
prelude
```

Bare aliases such as `abstract` are accepted only when they appear in the documented RGL alias registry.

### 5.3 Environment configuration

Resolved environment input may include:

```text
project_root
rgl_root
explicit_gf_path
allow_environment_fallback
strict_paths
```

### 5.4 Explicit path input

An explicit path MAY be supplied by:

- CLI;
- GUI;
- automation API;
- legacy migration adapter.

An explicit path is a complete override, not an extra suffix.

When present, it becomes the primary source of path parts.

The selected language context configuration remains loaded for validation and evidence, but its `path_parts` are not appended automatically.

### 5.5 Prohibited configuration

The canonical `project.toml` MUST NOT contain:

```text
C:\...
D:\...
/home/<user>/...
%USERPROFILE%
$HOME
${RGL_ROOT}
```

It also MUST NOT contain:

- output directories;
- run directories;
- GF executable paths;
- temporary-directory paths;
- paths outside the project or RGL roots;
- shell fragments;
- quoted command-line expressions.

---

## 6. RGL alias registry

GF Wordbench maintains a framework-level registry of recognized RGL aliases.

Initial canonical aliases:

```text
abstract
api
alltenses
common
compat
prelude
present
```

The registry MAY be extended when supported GF/RGL layouts require additional stable aliases.

An alias resolves as:

```text
<RGL_ROOT>/<alias>
```

Example:

```text
alias: abstract
RGL root: C:/work/gf-rgl/src
resolved: C:/work/gf-rgl/src/abstract
```

### 6.1 Alias rules

- alias matching is case-sensitive;
- aliases MUST be path-segment names, not arbitrary paths;
- aliases MUST NOT contain `/`, `\`, `:`, `..`, or environment syntax;
- an alias MUST resolve beneath the RGL root;
- a missing required alias is a configuration failure in strict mode;
- a missing optional alias may be omitted only when omission is recorded.

### 6.2 Explicit RGL prefix

The canonical explicit form is:

```text
rgl:<relative-path>
```

Examples:

```text
rgl:abstract
rgl:api
rgl:custom/resources
```

The relative portion:

- MUST remain under the RGL root;
- MUST NOT contain traversal after normalization;
- MUST use `/` in persisted project configuration.

### 6.3 Explicit project prefix

The canonical explicit project form is:

```text
project:<relative-path>
```

Examples:

```text
project:lib/src
project:lib/src/french
project:project/generated/interfaces
```

The relative portion resolves beneath the resolved source root.

---

## 7. Resolution precedence

The effective GF path MUST be resolved using this precedence.

### 7.1 Complete precedence

1. explicit run-level GF path;
2. project-configured `gf.path_parts`;
3. source-directory safety inclusion;
4. optional RGL-root baseline inclusion;
5. optional inherited environment fallback;
6. failure when required resolution remains incomplete.

### 7.2 Explicit override behavior

When `explicit_gf_path` is non-empty:

- parse the explicit path;
- normalize every entry;
- validate every entry;
- deduplicate entries;
- record source as `explicit`;
- do not append project `path_parts`;
- do not append inherited environment entries;
- MAY ensure the selected source root is present only when an explicit policy requests it;
- warn when the active source directory is absent;
- fail in strict mode when a required project path is absent.

### 7.3 Context-derived behavior

When no explicit path exists:

1. read `gf.path_parts` in declared order;
2. resolve each part;
3. ensure the configured source directory is represented;
4. apply configured baseline RGL behavior;
5. optionally apply environment fallback;
6. validate and deduplicate.

### 7.4 Environment fallback

Environment fallback is disabled by default.

When enabled, GF Wordbench MAY read:

```text
GF_LIB_PATH
```

Environment entries are appended after explicit project-derived entries.

Inherited environment MUST NOT silently override project configuration.

Use of environment fallback MUST be recorded in:

- run metadata;
- diagnostic summary;
- effective path entry provenance.

---

## 8. Canonical resolution algorithm

The following algorithm is normative.

```text
INPUT:
  project_root
  source_directory
  project_path_parts
  rgl_root
  explicit_gf_path
  allow_environment_fallback
  strict_paths
  platform
  gf_version_or_capabilities

1. Canonicalize project_root.
2. Validate project_root exists and is a directory.
3. Canonicalize rgl_root when supplied.
4. Validate rgl_root according to required project capabilities.
5. Determine source mode:
     explicit override
     or project-derived
6. Parse ordered input path parts.
7. Resolve every part by type:
     project-prefixed
     RGL-prefixed
     documented bare RGL alias
     source-relative path
     absolute explicit path
8. Reject traversal or forbidden roots.
9. Normalize each resolved directory.
10. Validate existence and directory type.
11. Apply missing-path policy.
12. Ensure source-directory coverage.
13. Append permitted environment fallback entries.
14. Deduplicate while preserving first occurrence.
15. Validate at least one usable path part exists.
16. Serialize the effective path for the selected GF version/platform.
17. Return structured resolution evidence.
```

---

## 9. Path-part classification

Each input string is classified in this order.

### 9.1 Empty input

After trimming whitespace, an empty item is invalid.

Canonical project configuration MUST reject it.

A legacy explicit path parser MAY discard empty entries produced by repeated separators, but MUST emit a migration warning.

### 9.2 `project:` compatibility prefix

```text
project:<path>
```

Resolves beneath the resolved source root.

### 9.3 `rgl:` prefix

```text
rgl:<path>
```

Resolves beneath the RGL root.

### 9.4 Registered bare alias

A bare item matching the alias registry resolves beneath the RGL root.

### 9.5 Absolute path

Absolute paths are accepted only from:

- explicit run-level path;
- environment fallback;
- migration input.

They are prohibited in canonical `project.toml`.

### 9.6 Unprefixed relative path

Any remaining relative item resolves beneath the resolved source root.

Example:

```text
lib/src
```

becomes:

```text
<PROJECT_ROOT>/lib/src
```

---

## 10. Source-directory inclusion

The configured source directory is authoritative under:

```toml
[sources]
directory = "..."
```

### 10.1 Required behavior

The resolver MUST verify that the source directory is represented by an effective path entry or covered by one of its ancestors.

Examples:

```text
source directory: lib/src/french
effective entry:  lib/src/french
result: covered
```

```text
source directory: lib/src/french
effective entry:  lib/src
result: covered
```

### 10.2 Automatic inclusion

In project-derived mode, when no declared path covers the source directory, the resolver SHOULD append the source directory after existing profile-owned path entries and before RGL/environment fallback entries.

This automatic inclusion MUST be recorded as:

```text
source = automatic_source_directory
```

Strict project validation MAY instead require the source directory to appear explicitly in `gf.path_parts`.

### 10.3 Explicit override warning

In explicit override mode, a missing source-directory covering path produces:

- warning in non-strict mode;
- configuration failure in strict mode.

---

## 11. RGL-root baseline behavior

The RGL root itself and its subdirectories serve different purposes.

### 11.1 `--gf-lib-path`

When supported by the selected GF version, the RGL root MAY be supplied separately through:

```text
--gf-lib-path=<RGL_ROOT>
```

### 11.2 `--path`

Resolved RGL aliases and project directories are supplied through:

```text
--path=<EFFECTIVE_GF_PATH>
```

### 11.3 No accidental duplication

Supplying `--gf-lib-path` does not remove the need to record the resolved path.

The resolver MUST avoid adding identical resolved directories repeatedly merely because both RGL-root and alias mechanisms are active.

### 11.4 RGL layout discovery

Automatic discovery MAY inspect only a documented alias registry.

It MUST NOT recursively add every RGL subdirectory.

Recursive discovery is prohibited because it:

- creates unstable ordering;
- masks missing project declarations;
- makes results depend on local RGL contents;
- may resolve unintended modules.

### 11.5 Required versus optional aliases

Every entry declared in `gf.path_parts` is required.

The resolver MAY add an optional compatibility alias only when a framework compatibility policy names it explicitly. An omitted optional alias MUST remain visible in resolution evidence and MUST NOT satisfy a project-declared requirement.

Introducing separate required and optional project fields is a versioned schema change governed by `PROJECT_TOML_REFERENCE.md` and `PERSISTED_SCHEMA_LOCK.md`.

---

## 12. Path normalization

### 12.1 Internal representation

Resolved paths MUST use native absolute `Path` objects internally.

They SHOULD be canonicalized with behavior equivalent to:

```python
path.expanduser().resolve(strict=False)
```

Environment-variable expansion is not permitted for profile-owned paths.

### 12.2 Persisted representation

Project-owned paths persisted in configuration use:

```text
relative/path/with/forward/slashes
```

Machine-local paths persisted in run metadata SHOULD use forward slashes:

```text
C:/work/gf-rgl/src/abstract
```

### 12.3 Case behavior

GF Wordbench MUST NOT lowercase paths globally.

On case-insensitive platforms, deduplication MAY use a normalized comparison key while preserving the first path's original display form.

### 12.4 Trailing separators

Trailing separators are removed except for filesystem roots.

### 12.5 Dot segments

`.` segments are normalized.

`..` is allowed only during initial parsing when the resolved result remains under the permitted root.

Canonical project configuration SHOULD reject `..` before resolution.

### 12.6 Symlinks

Symlink policy is platform- and deployment-sensitive.

Default behavior:

- resolve symlinks when the platform supports reliable resolution;
- validate the resolved target remains within its permitted root for project- and RGL-relative entries;
- record the canonical resolved path;
- preserve the configured lexical path separately when useful for diagnostics.

Strict mode SHOULD reject a symlink that escapes the allowed root.

---

## 13. Deduplication

Deduplication MUST preserve first occurrence.

Example input:

```text
project:lib/src
lib/src
rgl:abstract
abstract
```

Possible resolved entries:

```text
C:/work/project/lib/src
C:/work/project/lib/src
C:/work/gf-rgl/src/abstract
C:/work/gf-rgl/src/abstract
```

Effective result:

```text
C:/work/project/lib/src
C:/work/gf-rgl/src/abstract
```

### 13.1 Comparison key

The comparison key SHOULD account for:

- absolute normalization;
- platform case behavior;
- separator normalization;
- resolved symlink target where available.

### 13.2 Provenance retention

When duplicates are removed, the resolution result SHOULD retain all contributing declarations for diagnostics.

Example:

```json
{
  "resolved_path": "C:/work/project/lib/src",
  "sources": [
    "project:lib/src",
    "lib/src"
  ],
  "effective_index": 0
}
```

---

## 14. Missing-path policy

Each path entry resolves to one of:

```text
usable
missing
not_directory
outside_allowed_root
invalid_syntax
duplicate
unsupported
```

### 14.1 Required entry

A required entry that is:

- missing;
- not a directory;
- outside its permitted root;
- syntactically invalid;

causes configuration failure.

### 14.2 Optional entry

An optional missing entry MAY be omitted.

The omission MUST be recorded.

### 14.3 Source path

The source directory is always required for validations that operate on source files.

### 14.4 RGL root

The RGL root is required when configured project path parts or requested validation operations depend on it.

A run that performs only source scanning MAY proceed without GF/RGL validation when its mode explicitly permits no GF execution.

### 14.5 No automatic source creation

GF Wordbench MUST NOT create missing source or RGL directories.

It MAY create run-owned output and artifact directories.

---

## 15. Effective path data model

Canonical immutable models:

```python
@dataclass(frozen=True, slots=True)
class GFPathRequest:
    project_root: Path
    source_directory: str
    project_path_parts: tuple[str, ...]
    rgl_root: Path | None
    explicit_gf_path: str | None
    environment_gf_lib_path: str | None
    allow_environment_fallback: bool
    strict_paths: bool
    platform: str
    path_separator: str | None = None
```

```python
@dataclass(frozen=True, slots=True)
class GFPathEntry:
    configured_value: str
    resolved_path: Path | None
    source: str
    status: str
    required: bool
    effective_index: int | None
    message: str = ""
```

```python
@dataclass(frozen=True, slots=True)
class GFPathResolution:
    entries: tuple[GFPathEntry, ...]
    effective_paths: tuple[Path, ...]
    serialized_path: str
    separator: str
    used_explicit_override: bool
    used_environment_fallback: bool
    warnings: tuple[str, ...]
```

### 15.1 Structured boundary

Consumers MUST receive `GFPathResolution` or an equivalent typed object.

They MUST NOT receive only an undocumented concatenated string when they also need provenance or validation results.

### 15.2 Immutability

After run configuration is resolved and frozen, the effective resolution MUST remain immutable for the run.

---

## 16. Serialization for GF

### 16.1 Argument-list rule

GF command invocation MUST use a list of arguments.

Example:

```python
[
    "gf",
    "-batch",
    "-s",
    f"--gf-lib-path={rgl_root}",
    f"--path={resolution.serialized_path}",
    str(source_file),
]
```

Manual command-string quoting is prohibited.

### 16.2 Path separator

The separator used inside the GF path MUST be selected by a tested compatibility policy.

The resolver MUST NOT assume that the host operating-system path separator is always the correct GF path-list separator.

The selected separator MUST be:

- centralized;
- version-aware when necessary;
- tested on supported platforms;
- recorded in resolution evidence.

### 16.3 Canonical displayed form

Diagnostic displays SHOULD show path entries one per line, not only as one joined string.

Example:

```text
Effective GF path:
  [0] C:/work/project/lib/src
  [1] C:/work/project/lib/src/french
  [2] C:/work/gf-rgl/src/abstract
  [3] C:/work/gf-rgl/src/common
```

### 16.4 Command logging

The exact serialized argument passed to GF MUST be recorded.

The logged command and executed command MUST derive from the same argument list.

---

## 17. Shared use across GF operations

All GF-backed validation capabilities consume the same resolution through `GfToolPort` and the GF anti-corruption adapter.

### 17.1 Source compilation

`validation.application` submits a typed compilation operation. The GF adapter supplies the effective path to GF and returns preserved process evidence plus interpreted compilation results.

### 17.2 Scenario execution

`validation.application` submits the registered native `.gfs` scenario operation. Grammar loading and script execution use the same effective path as compilation.

### 17.3 PGF construction

`validation.application` submits the project-defined PGF operation. Release-entrypoint construction uses the same effective path and verifies the expected artifact.

### 17.4 GF introspection

Morphology, generation, missing-linearization, and grammar-inspection operations use the same effective path through the same port and adapter.

### 17.5 Allowed extension

A GF operation MAY request additional temporary path parts only when:

- its contract documents the reason;
- the added paths are validated;
- the base effective path remains intact;
- the extension is recorded;
- the operation result records its extended path.

Silent operation-specific path changes are prohibited.

---

## 18. Working-directory relationship

The GF path and working directory are independent inputs.

Canonical working directory:

```text
resolved resolved source root
```

Rules:

- relative selected source arguments resolve consistently from the resolved source root;
- source-relative GF path parts are converted to absolute resolved paths before command execution;
- changing the working directory MUST NOT change the effective path meaning;
- scenario and compile stages SHOULD use the same working directory;
- a stage using another working directory MUST record it explicitly.

---

## 19. Recording and reporting

Every GF-backed run MUST record:

```text
project_root
rgl_root
configured project path_parts
explicit_gf_path, when supplied
environment fallback enabled/disabled
environment fallback used/not used
effective ordered path entries
serialized GF path
selected path-list separator
missing optional entries
warnings
GF version or capability context
```

### 19.1 `summary.json`

Canonical metadata shape:

```json
{
  "gf_path_resolution": {
    "mode": "project-derived",
    "separator": ":",
    "used_environment_fallback": false,
    "effective_paths": [
      "C:/work/project/lib/src",
      "C:/work/project/lib/src/french",
      "C:/work/gf-rgl/src/abstract"
    ],
    "warnings": []
  }
}
```

The persisted schema MUST be coordinated with `PERSISTED_SCHEMA_LOCK.md`.

### 19.2 Human report

Human-facing reports SHOULD include:

- resolution mode;
- count of effective entries;
- warnings;
- path evidence location.

They SHOULD NOT repeat a very long full path list when `summary.json` and raw configuration evidence already contain it.

### 19.3 AI-ready report

`AI_READY.md` SHOULD include the effective path when module-resolution failure is relevant.

It MUST NOT include unrelated environment values.

---

## 20. Security rules

### 20.1 Allowed roots

Project-relative entries MUST remain beneath the resolved source root.

RGL-relative entries MUST remain beneath the RGL root.

Run-owned paths MUST remain beneath the run root.

### 20.2 Path traversal

The following are rejected when they escape the allowed root:

```text
../
..\ 
project:../../outside
rgl:../outside
```

### 20.3 Shell safety

Path entries are data.

They MUST NOT be interpolated into a shell command string.

### 20.4 Environment safety

GF Wordbench MUST NOT persist complete environment dumps.

Only correctness-relevant environment names and sanitized values may be recorded.

### 20.5 Untrusted projects

A cloned or downloaded project may declare hostile paths.

Project path validation MUST occur before launching GF.

### 20.6 Network and special paths

UNC paths and mounted network paths MAY be supported when tested.

Device paths, named pipes, and non-directory special files SHOULD be rejected.

---

## 21. Windows behavior

GF Wordbench must support Windows paths containing:

- drive letters;
- spaces;
- Unicode;
- mixed input separators.

Example:

```text
C:\mycode\Grammatical Framework\gf-rgl\src
```

Internally:

```text
Path("C:/mycode/Grammatical Framework/gf-rgl/src")
```

### 21.1 Quoting

Do not add literal quote characters around path arguments passed through `subprocess` argument lists.

### 21.2 Drive-relative paths

Forms such as:

```text
C:folder
```

are ambiguous and MUST be rejected.

### 21.3 Case-insensitive deduplication

Windows deduplication SHOULD use a case-normalized comparison key while preserving original display casing.

### 21.4 Long paths

The resolver SHOULD detect paths likely to exceed supported limits before GF execution.

A warning or configuration error depends on platform capability and strict mode.

### 21.5 Separator uncertainty

The GF path-list separator on Windows MUST be validated against supported GF versions.

It MUST be represented by a compatibility function, not duplicated string literals.

---

## 22. POSIX behavior

POSIX platforms must support:

- absolute `/...` paths;
- spaces;
- Unicode;
- symlinks;
- case-sensitive path identity.

User-home expansion MAY be accepted for explicit environment input.

It MUST NOT be accepted in canonical project paths.

---

## 23. Migration from `gf-audit`

The legacy GF Audit baseline contains two path-building locations:

- bootstrap default-path construction;
- compiler fallback resolution.

That duplication must be removed.

### 23.1 Legacy behavior to preserve temporarily

The existing tool derives a path from:

```text
lib/src
configured scan directory
detected RGL subdirectories:
  present
  alltenses
  common
  abstract
  prelude
  compat
  api
```

It joins those entries into one GF path string.

### 23.2 Canonical replacement

GF Wordbench moves this behavior to one resolver and replaces language-specific defaults with:

```text
<validation-profile-root>/project.toml
```

### 23.3 Required migration changes

1. create the centralized resolver;
2. introduce typed request and resolution models;
3. load `gf.path_parts` from the selected language context;
4. remove `lib/src/albanian` from framework defaults;
5. remove compiler-local path fallback;
6. remove GUI-specific blank-path assumptions;
7. make CLI and GUI use the same resolver;
8. make scenarios and PGF builds use the same result;
9. record effective path provenance;
10. add contract and integration tests.

### 23.4 Legacy explicit string

A legacy explicit path string MAY be accepted during migration.

It MUST be:

- parsed through the compatibility adapter;
- normalized into structured entries;
- marked as legacy input;
- written only in canonical v1 form when persisted.

### 23.5 No silent semantic change

During migration, old and new resolvers SHOULD be compared against representative projects.

Any difference in effective directories or order must be reviewed.

---

## 24. Error model

Canonical path-resolution error codes:

```text
GF_PATH_PROJECT_ROOT_MISSING
GF_PATH_RGL_ROOT_MISSING
GF_PATH_PART_EMPTY
GF_PATH_PART_INVALID
GF_PATH_PART_MISSING
GF_PATH_PART_NOT_DIRECTORY
GF_PATH_PART_OUTSIDE_ROOT
GF_PATH_SOURCE_NOT_COVERED
GF_PATH_EXPLICIT_INVALID
GF_PATH_ENVIRONMENT_INVALID
GF_PATH_SEPARATOR_UNSUPPORTED
GF_PATH_NO_USABLE_ENTRIES
GF_PATH_VERSION_UNSUPPORTED
```

### 24.1 Error classification

Path-resolution failures are configuration or contract failures.

They are not GF syntax errors.

### 24.2 Validation status

A required GF operation blocked by path resolution normally produces:

```text
validation_status = ERROR
error_kind = CONFIG
execution_state = not_started
```

No GF process should be launched after a fatal path-resolution error.

---

## 25. Diagnostics

A useful path diagnostic includes:

```text
code
configured value
interpreted type
resolved path
source
required/optional
status
reason
suggested correction
```

Example:

```text
Code: GF_PATH_PART_MISSING
Configured value: rgl:abstract
Resolved path: C:/work/gf-rgl/src/abstract
Source: project.toml [gf].path_parts[2]
Required: true
Reason: directory does not exist
Correction: verify rgl_root or update the project path declaration
```

Diagnostics MUST NOT suggest creating missing source or RGL directories automatically.

---

## 26. Contract invariants

The following invariants are normative.

1. One resolver owns effective GF path construction for one selected language context in one run.
2. CLI and GUI produce equivalent path requests from equivalent inputs.
3. Compilation, scenarios, introspection, and PGF build share one base resolution.
4. Project-owned paths are portable and source-relative.
5. Machine-local roots remain environment configuration.
6. Explicit configuration takes precedence over inherited environment.
7. Environment fallback is never silent.
8. Entry order is deterministic.
9. Deduplication preserves first occurrence.
10. Missing required entries fail before GF execution.
11. Source directories are never created automatically.
12. Path traversal outside permitted roots is rejected.
13. Command arguments are passed as an argument list.
14. The effective path is recorded.
15. The executed and logged path are identical.
16. Framework code contains no active-language path literals.
17. GF remains authoritative for module resolution.
18. Normal reports do not reconstruct the GF path independently.
19. Path-resolution changes are contract changes.
20. Path-list separator behavior is centralized and tested.
21. `gf-portfolio` cannot supply, override, or persist Wordbench path resolution.

---

## 27. Prohibited behavior

The following are prohibited:

- building the GF path independently in `compiler.py`;
- building a different path in `scenario_runner.py`;
- adding RGL directories recursively;
- relying silently on global `GF_LIB_PATH`;
- storing absolute RGL paths in the project template;
- storing active-language source defaults in framework code;
- concatenating a shell command with user-provided paths;
- adding manual quote characters to argument-list entries;
- ignoring a missing configured path;
- treating a file as a directory path entry;
- changing path order through set conversion;
- normalizing every path to lowercase;
- dropping provenance after deduplication;
- using report prose as the source of path configuration;
- allowing GUI and CLI resolution precedence to differ;
- changing the effective path after run configuration is frozen;
- using a successful exit from one path configuration as proof another configuration is valid;
- accepting Portfolio workspace roots or registry state as Wordbench path input.

---

## 28. Required tests

Canonical test files:

```text
tests/gf/test_path_resolver.py
tests/contracts/test_gf_path_contract.py
tests/integration/test_gf_path_with_real_gf.py
tests/migrations/test_legacy_gf_path.py
```

### 28.1 Unit tests

Required cases:

- source-relative path;
- `project:` prefix;
- `rgl:` prefix;
- documented bare alias;
- explicit absolute override;
- empty path part;
- missing directory;
- file instead of directory;
- traversal outside resolved source root;
- traversal outside RGL root;
- duplicate lexical entries;
- duplicate resolved entries;
- platform case behavior;
- source directory already covered;
- automatic source-directory inclusion;
- strict missing-source behavior;
- environment fallback disabled;
- environment fallback enabled;
- invalid environment entry;
- paths containing spaces;
- Unicode paths;
- Windows drive paths;
- drive-relative Windows path rejection;
- separator selection;
- deterministic ordering;
- provenance retention;
- no usable entries.

### 28.2 Contract tests

Verify:

- compiler consumes `GFPathResolution`;
- scenario runner consumes the same resolution;
- PGF builder consumes the same resolution;
- no second path builder exists;
- CLI and GUI share precedence;
- reports read recorded resolution;
- project paths serialize canonically;
- no active-language path literal exists in framework defaults.

### 28.3 Integration tests with GF

Using a minimal fixture grammar:

- compile with project paths;
- compile with RGL aliases;
- load the grammar in a `.gfs` scenario;
- build a PGF using the same resolution;
- verify a missing path fails before execution;
- verify a path containing spaces;
- compare logged and executed arguments.

Real-GF tests SHOULD be marked separately when GF is not available in every development environment.

---

## 29. CLI path diagnostics

The CLI reference owns the exact command syntax. The path-resolution command surface includes:

Resolve without executing GF:

```text
gf-wordbench paths resolve
```

Strict resolution:

```text
gf-wordbench paths resolve --strict
```

Show provenance:

```text
gf-wordbench paths resolve --explain
```

Validate project and RGL paths:

```text
gf-wordbench paths check
```

Canonical output:

```text
GF path resolution: OK
Mode: project-derived
Project root: C:/work/GF_Wordbench
RGL root: C:/work/gf-rgl/src
Environment fallback: disabled

Effective path:
  0 project  C:/work/GF_Wordbench/lib/src
  1 project  C:/work/GF_Wordbench/lib/src/french
  2 rgl      C:/work/gf-rgl/src/abstract
  3 rgl      C:/work/gf-rgl/src/common
  4 rgl      C:/work/gf-rgl/src/prelude
```

These commands MUST remain synchronized with `docs/usage/CLI_REFERENCE.md` and `docs/reference/COMMAND_REFERENCE.md`.

---

## 30. Example resolutions

### 30.1 Standard context-derived path

Configuration:

```toml
[sources]
directory = "lib/src/french"

[gf]
path_parts = [
  "lib/src",
  "lib/src/french",
  "abstract",
  "common",
  "prelude",
]
```

Environment:

```text
project_root = C:/work/GF_Wordbench
rgl_root = C:/work/gf-rgl/src
```

Result:

```text
C:/work/GF_Wordbench/lib/src
C:/work/GF_Wordbench/lib/src/french
C:/work/gf-rgl/src/abstract
C:/work/gf-rgl/src/common
C:/work/gf-rgl/src/prelude
```

### 30.2 Explicit override

Input:

```text
C:/custom/project/src:C:/custom/rgl/abstract
```

Result:

- project `path_parts` are not appended;
- both entries are validated;
- override use is recorded;
- missing active source coverage warns or fails under strict policy.

### 30.3 Duplicate aliases

Configuration:

```toml
path_parts = [
  "abstract",
  "rgl:abstract",
]
```

Result:

```text
one effective RGL abstract directory
```

Both declarations remain visible in provenance.

### 30.4 Missing optional alias

Configuration requests an alias classified optional by compatibility policy.

Result:

- entry status: `missing`;
- omitted from effective path;
- warning recorded;
- run may proceed.

### 30.5 Missing required alias

Configuration:

```text
rgl:abstract
```

Resolved directory does not exist.

Result:

```text
validation_status = ERROR
error_kind = CONFIG
GF process = not started
```

---

## 31. Change policy

A change to any of the following is a contract change:

- resolution precedence;
- path-part classification;
- alias registry semantics;
- automatic source inclusion;
- environment fallback behavior;
- path deduplication;
- allowed roots;
- missing-path policy;
- path separator selection;
- serialized run metadata;
- shared-consumer requirements.

A coordinated change MUST update:

1. resolver;
2. request and result models;
3. project loader;
4. bootstrap;
5. compiler;
6. scenario runner;
7. PGF builder;
8. CLI and GUI;
9. reports and schemas;
10. contract tests;
11. migration tests;
12. this document;
13. relevant lock files;
14. `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` when the product boundary changes.

---

## 32. Core rule

> GF Wordbench resolves the GF path once, validates it once, records it once, and reuses that same resolution everywhere GF is invoked.

No component may silently alter the module-search environment after the run begins.
