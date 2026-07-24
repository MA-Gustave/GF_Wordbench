# GF Wordbench — `project.toml` Reference

**Document ID:** `GF-WB-CONFIG-PROJECT-TOML`  
**Status:** Normative  
**Applies to:** Active-project identity, source selection, GF path parts, module targets, scenario requirements and release policy  
**Owner:** GF Wordbench maintainers  
**Schema ID:** `gf-wordbench.project`  
**Current schema version:** `1.0`  
**Document version:** `2.0.0`  
**Last reviewed:** `2026-07-24`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related locks:** `docs/PERSISTED_SCHEMA_LOCK.md`, `docs/INTERFILE_CONTRACT_LOCK.md`, `project/docs/INTERFILE_CONTRACT_LOCK.md`

---

## 1. Purpose

This document is the complete reference for:

```text
project/project.toml
```

`project.toml` is the authoritative machine-readable definition of one active GF language project.

It tells GF Wordbench:

- which project is active;
- where its GF source files are located;
- how source files are selected;
- which GF search-path parts the project requires;
- which modules are checkpoints;
- which modules are entrypoints;
- which scenarios are required or optional;
- whether release validation requires a PGF artifact.

The file is intentionally compact.

It MUST describe stable project facts and project policy.

It MUST NOT become a store for:

- local GF executable paths;
- developer-specific RGL paths;
- output directories;
- GUI preferences;
- run history;
- temporary validation state;
- machine-specific timeouts;
- secrets.

The central rule is:

> `project.toml` defines the active language project; environment and application state define the machine that runs it.

### 1.1 Product boundary

One `project.toml` describes exactly one active GF language project and one normative language target.

It MUST NOT contain:

- a registry of several Wordbench workspaces;
- a list of active projects;
- runtime-selectable language profiles;
- cross-project readiness or comparison state;
- `gf-portfolio` configuration, storage identifiers or private schema fields.

Multi-workspace and multilingual aggregation belong to the independent `gf-portfolio` product, which may consume public versioned Wordbench artifacts without becoming a Wordbench dependency.

---

## 2. Canonical location

```text
<repository-root>/project/project.toml
```

The loader MUST resolve the file from the configured or discovered active-project location.

It MUST NOT resolve the file from the process current working directory by accident.

The template source is:

```text
templates/project/project.toml
```

The active file and template share the same schema.

The template may contain documented placeholders.

The active file MUST contain real project values.

---

## 3. Schema identity

Every canonical file begins with:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"
```

### 3.1 `schema_id`

Required exact value:

```text
gf-wordbench.project
```

It identifies the document type.

It is not the project ID.

### 3.2 `schema_version`

Required format:

```text
MAJOR.MINOR
```

Current value:

```text
1.0
```

The project schema version is independent of:

- GF Wordbench package version;
- GF compiler version;
- language-project release version;
- PGF artifact version.

### 3.3 Unsupported versions

An unsupported major version MUST be rejected.

A newer minor version MAY be read only when the loader's compatibility policy permits unknown optional fields.

The loader MUST NOT silently reinterpret a different schema ID.

---

## 4. Canonical complete example

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "sqi"
name = "Albanian"
language_code = "sqi"
root = "."

[sources]
directory = "lib/src/albanian"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"

[gf]
path_parts = [
  "lib/src",
  "lib/src/albanian",
  "abstract",
  "common",
  "prelude",
]
minimum_version = ""

[modules]
entrypoints = [
  "GrammarSqi.gf",
  "SyntaxSqi.gf",
]
checkpoints = [
  "MorphoSqi.gf",
  "NounSqi.gf",
  "VerbSqi.gf",
  "ExtendSqi.gf",
  "StructuralSqi.gf",
]

[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
]
optional_scenarios = [
  "generation",
  "morphology",
]
release_requires_pgf = true
```

This example demonstrates the schema.

Its Albanian values are not framework defaults.

---

## 5. Canonical template

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "<project-id>"
name = "<language-name>"
language_code = "<language-code>"
root = "."

[sources]
directory = "<project-relative-source-directory>"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"

[gf]
path_parts = [
  "<project-relative-path>",
]
minimum_version = ""

[modules]
entrypoints = [
  "<entrypoint>.gf",
]
checkpoints = []

[validation]
required_scenarios = []
optional_scenarios = []
release_requires_pgf = true
```

Template placeholders MUST be replaced before the active project is considered initialized.

---

## 6. Root structure

Canonical root keys:

```text
schema_id
schema_version
project
sources
gf
modules
validation
```

Required tables:

```text
[project]
[sources]
[gf]
[modules]
[validation]
```

Unknown root tables are rejected in strict mode.

Compatible optional fields may be added only through a documented schema revision.

---

# 7. `[project]`

The `[project]` table defines stable project identity.

Canonical fields:

```toml
[project]
id = "sqi"
name = "Albanian"
language_code = "sqi"
root = "."
```

---

## 7.1 `project.id`

### Type

```text
string
```

### Required

Yes.

### Purpose

Stable machine identifier for the active project.

It may be used in:

- run metadata;
- report metadata;
- release evidence;
- project comparisons;
- exported manifests;
- migration checks.

### Recommended format

```text
[a-z0-9][a-z0-9_-]*
```

Examples:

```text
sqi
fre
eng
french-rgl
test-language
```

### Rules

- MUST be non-empty;
- MUST be stable after published runs exist;
- SHOULD be lowercase;
- SHOULD be path-safe;
- MUST NOT contain a filesystem path;
- MUST NOT contain secrets;
- MUST NOT be inferred from an old run directory;
- MUST NOT be inferred from GUI state.

Changing `project.id` after published runs exist is a breaking project migration.

---

## 7.2 `project.name`

### Type

```text
string
```

### Required

Yes.

### Purpose

Human-readable project or language display name.

Examples:

```text
Albanian
French
Experimental French Grammar
```

### Rules

- MUST be non-empty;
- MAY contain Unicode;
- MAY contain spaces;
- MUST NOT be used as a filesystem identity;
- MUST NOT be parsed to derive module names;
- MAY change without changing `project.id` when only display wording changes.

A semantic change to a different active language requires a project reset or migration, not only a renamed display string.

---

## 7.3 `project.language_code`

### Type

```text
string
```

### Required

Yes.

### Purpose

Stable language identifier used in metadata and project documentation.

Recommended value:

```text
ISO 639-3 lowercase code
```

Examples:

```text
sqi
fra
eng
```

A project may use another documented stable code when necessary.

### Rules

- MUST be non-empty;
- SHOULD be lowercase;
- SHOULD be stable;
- MUST NOT be a path;
- MUST agree with active-project documentation;
- MUST NOT be inferred from module suffix alone.

Changing the language code is a project-identity migration.

---

## 7.4 `project.root`

### Type

```text
string
```

### Required

Yes.

### Canonical v1 value

```text
.
```

### Purpose

Defines the logical project root relative to the directory containing `project.toml`.

For schema `1.0`, the supported canonical layout is:

```text
project.toml parent directory = project root
```

Therefore:

```toml
root = "."
```

### Rules

- MUST be project-relative;
- MUST NOT be absolute;
- MUST resolve to a directory;
- MUST NOT escape the `project/` directory;
- SHOULD remain `"."` in schema `1.0`.

A non-dot root requires an explicit layout contract and schema review.

---

# 8. `[sources]`

The `[sources]` table defines source discovery and file-selection policy.

Canonical fields:

```toml
[sources]
directory = "lib/src/albanian"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"
```

The detailed runtime behavior is governed by:

```text
docs/validation/FILE_SELECTION.md
```

---

## 8.1 `sources.directory`

### Type

```text
string
```

### Required

Yes.

### Purpose

Project-relative directory containing active-language GF source files.

Example:

```text
lib/src/albanian
```

### Resolution base

```text
project root
```

### Rules

- MUST be non-empty;
- MUST be relative;
- MUST use `/` in canonical TOML;
- MUST resolve inside the project root;
- MUST exist before normal validation;
- MUST be a directory;
- MUST identify the active language source tree;
- MUST NOT point to a generated run directory;
- MUST NOT contain a drive letter;
- MUST NOT use `..` to escape the project.

### Windows input

The canonical file uses:

```text
/
```

The loader MAY accept legacy backslashes during migration.

Canonical writers emit `/`.

---

## 8.2 `sources.glob`

### Type

```text
string
```

### Required

Yes.

### Canonical default

```text
*.gf
```

### Purpose

Recursive candidate-discovery pattern under `sources.directory`.

### Rules

- MUST be non-empty;
- MUST be a valid pattern for the selector;
- SHOULD select GF source candidates only;
- MUST NOT be treated as a regex;
- MUST NOT contain an absolute path;
- MUST NOT define source semantics.

With recursive enumeration:

```text
*.gf
```

matches GF files in nested source directories.

---

## 8.3 `sources.include_regex`

### Type

```text
string
```

### Required

Yes.

### Purpose

Regex used after glob discovery to accept candidate filenames or project-relative paths.

### Canonical evaluation targets

```text
candidate filename
project-relative POSIX path
```

### Empty value

```toml
include_regex = ""
```

means:

```text
no include-regex restriction
```

### Rules

- MUST compile successfully;
- is case-sensitive unless the pattern requests otherwise;
- uses regex-search semantics;
- SHOULD use anchors when full matching is intended;
- MUST NOT be silently corrected;
- MUST NOT be used to compensate for an invalid source root.

Example:

```toml
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
```

This is a project naming policy, not a GF universal rule.

Projects using Unicode module filenames must choose an appropriate expression.

---

## 8.4 `sources.exclude_regex`

### Type

```text
string
```

### Required

Yes.

### Purpose

Regex used to reject discovered candidates.

### Empty value

```toml
exclude_regex = ""
```

means:

```text
no regex exclusion
```

### Precedence

Exclude matching has priority over include matching.

A file matching both is excluded.

### Rules

- MUST compile successfully;
- is evaluated against filename and project-relative POSIX path;
- SHOULD exclude backups, disabled copies, and temporary files used by the active project;
- MUST NOT contain active-language assumptions in the generic template;
- MUST NOT exclude required entrypoints silently.

Example:

```toml
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"
```

---

# 9. `[gf]`

The `[gf]` table defines project-owned GF toolchain requirements.

Canonical fields:

```toml
[gf]
path_parts = [
  "lib/src",
  "lib/src/albanian",
  "abstract",
  "common",
  "prelude",
]
minimum_version = ""
```

It does not identify the local GF executable or RGL installation.

---

## 9.1 `gf.path_parts`

### Type

```text
array of strings
```

### Required

Yes.

### Purpose

Ordered project-owned components used to construct the effective GF search path.

### Ordering

Order is semantically significant.

The loader and path resolver MUST preserve declared order.

### Allowed value classes

A value may be:

1. a project-relative path;
2. a documented RGL-relative path or alias interpreted by the GF path resolver.

Examples:

```text
lib/src
lib/src/albanian
abstract
common
prelude
```

### Rules

- array MUST exist;
- values MUST be non-empty;
- values MUST use `/` canonically;
- duplicate effective paths SHOULD be removed while preserving first occurrence;
- project-relative values MUST remain inside the project root;
- ordering MUST NOT be alphabetically normalized;
- local RGL absolute paths MUST NOT be stored here;
- environment variables MUST NOT be embedded;
- the effective resolved GF path MUST be recorded in run metadata.

Detailed resolution belongs to:

```text
docs/gf/GF_PATH_RESOLUTION.md
```

---

## 9.2 `gf.minimum_version`

### Type

```text
string
```

### Required

Yes.

### Empty value

```toml
minimum_version = ""
```

means:

```text
no project-specific minimum beyond framework compatibility policy
```

### Purpose

Optional minimum GF version required by the active project.

Examples:

```toml
minimum_version = ""
minimum_version = "3.12"
```

### Rules

- MUST be a string;
- SHOULD use a normalized version form;
- MUST NOT include command output prose;
- MUST NOT identify the executable path;
- MUST be checked against the probed GF version when non-empty;
- MUST NOT override a stricter framework incompatibility rule.

Exact version comparison behavior is defined by:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

---

# 10. `[modules]`

The `[modules]` table defines explicit compilation targets.

Canonical fields:

```toml
[modules]
entrypoints = [
  "GrammarSqi.gf",
  "SyntaxSqi.gf",
]
checkpoints = [
  "MorphoSqi.gf",
  "NounSqi.gf",
]
```

Every item is resolved relative to:

```text
sources.directory
```

---

## 10.1 `modules.entrypoints`

### Type

```text
array of strings
```

### Required

Yes.

### Minimum cardinality

```text
at least one
```

for an initialized project intended for release.

### Purpose

Ordered top-level GF modules used for:

- entrypoint compilation;
- grammar loading;
- scenario execution;
- PGF construction;
- API or release validation.

### Rules

- values MUST be unique after path normalization;
- values MUST be source-root-relative;
- values MUST end in `.gf`;
- values MUST resolve inside the source root;
- values MUST exist before release validation;
- order MUST be preserved;
- basename search fallback MUST NOT be used;
- a required entrypoint MUST NOT be excluded by source filters;
- entrypoints SHOULD be documented in the module dependency map;
- entrypoint changes require scenario and release review.

### Nested example

```toml
entrypoints = [
  "grammar/GrammarX.gf",
  "api/SyntaxX.gf",
]
```

---

## 10.2 `modules.checkpoints`

### Type

```text
array of strings
```

### Required

Yes.

### Empty value

```toml
checkpoints = []
```

is permitted during project bootstrap.

### Purpose

Ordered modules whose successful validation proves development layers or subsystems.

Typical checkpoint order follows dependency order:

```text
morphology/resources
    → category modules
    → syntax/structural/extend
    → entrypoints
```

### Rules

- values MUST be unique after path normalization;
- values MUST be source-root-relative;
- values MUST end in `.gf`;
- values MUST preserve declared order;
- required checkpoint mode MUST NOT truncate the list;
- missing checkpoints cause checkpoint configuration failure;
- a checkpoint MUST NOT be excluded by source filters;
- duplicate overlap with entrypoints is allowed;
- release selection deduplicates overlap while preserving checkpoint-first order.

---

## 10.3 Module suffix

Schema `1.0` does not store a separate mandatory `module_suffix` field.

The active project MUST nevertheless document or resolve the suffix consistently through:

- configured module filenames;
- project language architecture;
- module dependency map;
- project interfile contract lock.

Example:

```text
GrammarSqi.gf
SyntaxSqi.gf
MorphoSqi.gf
```

implies the documented suffix:

```text
Sqi
```

An explicit `module_suffix` field requires a compatible schema revision and coordinated project migration.

---

# 11. `[validation]`

The `[validation]` table defines project scenario policy and the PGF release requirement.

Canonical fields:

```toml
[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
]
optional_scenarios = [
  "generation",
  "morphology",
]
release_requires_pgf = true
```

---

## 11.1 `validation.required_scenarios`

### Type

```text
array of strings
```

### Required

Yes.

### Purpose

Ordered scenario IDs that must pass when required by the current validation mode and release policy.

### Canonical scenario path

For scenario ID:

```text
parse
```

the default script path is:

```text
project/validation/scenarios/parse.gfs
```

The default gold path, when the scenario uses gold comparison, is:

```text
project/validation/gold/parse.gold
```

### Rules

- IDs MUST be non-empty;
- IDs MUST be unique across required and optional arrays;
- order MUST be preserved;
- IDs SHOULD be path-safe;
- IDs SHOULD use lowercase letters, digits, `_`, or `-`;
- every required scenario MUST have a resolvable scenario definition;
- missing required scenario is a validation or release failure;
- required scenarios MUST NOT be silently downgraded by GUI state.

### Bootstrap

An empty list is permitted while initializing a project.

Release readiness with an empty required list depends on the project validation specification and MUST NOT be assumed automatically.

---

## 11.2 `validation.optional_scenarios`

### Type

```text
array of strings
```

### Required

Yes.

### Purpose

Ordered scenario IDs that provide additional evidence without being mandatory for every gate.

### Rules

- IDs MUST be unique;
- IDs MUST not appear in `required_scenarios`;
- order MUST be preserved;
- optional failures remain visible;
- optional does not mean undocumented;
- release policy may later promote a scenario to required through a project configuration change.

Moving a scenario from optional to required is compatible at the schema level but release-significant at the project level.

---

## 11.3 `validation.release_requires_pgf`

### Type

```text
boolean
```

### Required

Yes.

### Purpose

Determines whether release mode requires successful PGF construction and artifact verification.

Canonical values:

```toml
release_requires_pgf = true
release_requires_pgf = false
```

### When `true`

Release requires:

- configured entrypoints;
- successful PGF build;
- expected non-empty `.pgf`;
- manifest registration;
- no fatal build diagnostic.

### When `false`

Release mode may omit PGF construction only when:

- the active project is intentionally not a PGF-producing project;
- the project validation specification explains the decision;
- release criteria agree;
- no scenario or downstream consumer requires the PGF.

It MUST NOT be set to `false` merely to bypass a failing release build.

---

# 12. Validation modes and project fields

## 12.1 Quick

Consumes:

```text
sources.*
explicit runtime target
```

It does not consume checkpoint order as its target set.

## 12.2 Checkpoint

Consumes:

```text
modules.checkpoints
sources.*
gf.path_parts
```

Every configured checkpoint is required.

## 12.3 Release

Consumes:

```text
modules.checkpoints
modules.entrypoints
validation.required_scenarios
validation.release_requires_pgf
gf.path_parts
gf.minimum_version
```

Release module order is:

```text
checkpoints
then entrypoints not already selected
```

## 12.4 Diagnostic

Consumes:

```text
sources.*
gf.path_parts
```

It enumerates broadly under the source root.

Scenario execution follows the selected diagnostic pipeline policy.

---

# 13. Derived paths

The schema stores stable source facts, not every path.

The loader derives:

| Derived asset | Rule |
|---|---|
| project root | parent of `project.toml`, then `project.root` |
| source root | project root + `sources.directory` |
| checkpoint path | source root + checkpoint item |
| entrypoint path | source root + entrypoint item |
| scenario script | `validation/scenarios/<scenario-id>.gfs` |
| gold file | `validation/gold/<scenario-id>.gold` when applicable |
| input directory | `validation/inputs/` |
| project docs | `docs/` |

Generated run paths are not derived from this file.

They belong to `RunPaths` and environment configuration.

---

# 14. What does not belong in `project.toml`

The following fields are prohibited in schema `1.0`.

## 14.1 Machine-specific paths

```text
gf_executable
gf_exe
rgl_root
output_root
temporary_directory
python_executable
```

These belong to environment configuration or application state.

## 14.2 Run preferences

```text
mode
target_file
timeout_sec
max_files
keep_ok_details
diff_previous
skip_version_probe
no_compile
emit_cpu_stats
```

These belong to resolved run configuration or application state.

## 14.3 Runtime state

```text
is_running
last_run_dir
last_summary_path
status_message
current_run_result
```

These belong to application state or in-memory state.

## 14.4 Generated evidence

```text
last_status
compile_result
scenario_result
artifact_hash
run_id
```

These belong to run summaries and manifests.

## 14.5 Portfolio and multi-project state

```text
projects
active_projects
workspace_registry
portfolio_id
portfolio_database
portfolio_readiness
language_profiles
cross_project_comparison
```

These concepts belong outside GF Wordbench project configuration. Public Wordbench artifacts may be consumed by `gf-portfolio`, but `project.toml` MUST NOT contain Portfolio-owned state or establish a reverse dependency.

## 14.6 Secrets

```text
token
password
private_key
credential
```

Secrets MUST NOT be stored in project configuration.

---

# 15. Configuration precedence

`project.toml` is authoritative for project facts.

Recommended complete precedence:

```text
1. immutable schema rules
2. project.toml project facts
3. environment configuration for machine facts
4. explicit CLI or GUI run choices
5. application defaults
```

A runtime override may change a run preference.

It MUST NOT silently change:

```text
project.id
project.language_code
sources.directory
modules.entrypoints
required release scenarios
release_requires_pgf
```

Any override mechanism for project facts must be visible, auditable and prohibited in release mode unless explicitly documented.

---

# 16. Loader contract

Recommended public responsibility:

```python
def load_project_config(
    project_file: Path,
) -> ProjectConfig:
    ...
```

Recommended workflow:

```text
1. locate project.toml
2. read UTF-8 text
3. parse TOML
4. validate schema identity
5. validate schema version
6. validate required tables
7. validate field types
8. normalize canonical strings
9. compile regexes
10. resolve and validate project root
11. resolve and validate source root
12. validate module target syntax
13. validate scenario IDs
14. enforce cross-field invariants
15. return typed ProjectConfig
```

The loader MUST NOT:

- invoke GF;
- compile source files;
- execute scenarios;
- create source directories;
- rewrite the file;
- import GUI state as project truth;
- infer missing required values from old reports.

---

# 17. Recommended typed model

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    id: str
    name: str
    language_code: str
    root: Path


@dataclass(frozen=True, slots=True)
class SourceConfig:
    directory: Path
    glob: str
    include_regex: str
    exclude_regex: str


@dataclass(frozen=True, slots=True)
class GFProjectConfig:
    path_parts: tuple[str, ...]
    minimum_version: str


@dataclass(frozen=True, slots=True)
class ModuleTargets:
    entrypoints: tuple[Path, ...]
    checkpoints: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class ValidationPolicy:
    required_scenarios: tuple[str, ...]
    optional_scenarios: tuple[str, ...]
    release_requires_pgf: bool


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    schema_id: str
    schema_version: str
    identity: ProjectIdentity
    sources: SourceConfig
    gf: GFProjectConfig
    modules: ModuleTargets
    validation: ValidationPolicy
    project_file: Path
    project_root: Path
    source_root: Path
```

Exact internal decomposition may vary.

The observable field semantics are locked.

---

# 18. Cross-field invariants

The loader MUST validate:

```text
project.id is non-empty
project.name is non-empty
project.language_code is non-empty
project.root resolves safely
sources.directory resolves inside project
sources.glob is non-empty
include_regex compiles
exclude_regex compiles
gf.path_parts preserve order
entrypoints are non-empty for initialized release project
entrypoints are unique
checkpoints are unique
module paths are source-root-relative
scenario IDs are unique
required and optional scenario sets do not overlap
release_requires_pgf is boolean
```

Additional project consistency checks SHOULD verify:

```text
configured entrypoints exist
configured checkpoints exist
required scenarios exist
old language identifiers are absent
source filters do not exclude required targets
project docs match configured identity
```

Some existence checks may be deferred to a dedicated project-contract validation stage during bootstrap.

---

# 19. Path rules

Canonical project-owned paths:

- are relative;
- use `/`;
- contain no drive letter;
- contain no unresolved environment variable;
- remain inside the documented root;
- preserve case;
- are normalized before comparison.

Examples:

```text
lib/src/french
grammar/GrammarFre.gf
abstract
common
```

Invalid canonical examples:

```text
C:\work\project\lib\src\french
..\other-project
%USERPROFILE%\gf
${RGL_ROOT}
```

Environment aliases may be supported by the GF path resolver only when explicitly documented.

They are not arbitrary shell variable expansion.

---

# 20. TOML string and regex escaping

TOML basic strings use backslash escaping.

To express the regex:

```text
\.gf$
```

write:

```toml
include_regex = "\\.gf$"
```

Example:

```toml
exclude_regex = "(\\.bak\\.gf$|\\.tmp\\.gf$)"
```

Single-quoted TOML literal strings may reduce escaping, but the canonical template uses double-quoted basic strings consistently.

The loader evaluates the resulting TOML string as a regex.

It MUST NOT apply a second undocumented escaping layer.

---

# 21. Arrays and ordering

These arrays are ordered:

```text
gf.path_parts
modules.entrypoints
modules.checkpoints
validation.required_scenarios
validation.optional_scenarios
```

The loader MUST preserve order.

Canonical writers MUST not sort these arrays automatically.

Duplicate values are invalid or warning-worthy according to the field:

| Field | Duplicate policy |
|---|---|
| `gf.path_parts` | deduplicate effective paths preserving first; warn |
| `entrypoints` | reject duplicate normalized path |
| `checkpoints` | reject duplicate normalized path |
| required scenarios | reject |
| optional scenarios | reject |
| cross required/optional | reject overlap |

---

# 22. Comments and formatting

TOML comments are allowed.

Example:

```toml
# Primary release entrypoints.
[modules]
entrypoints = [
  "GrammarX.gf",
  "SyntaxX.gf",
]
```

Comments do not define machine contracts.

A normal validation run MUST NOT rewrite formatting or comments.

Canonical formatter behavior, if introduced, must be explicit and opt-in.

Semantic equality does not depend on key order.

Human review benefits from the canonical section order used in this document.

---

# 23. Encoding and newlines

Canonical file encoding:

```text
UTF-8 without BOM
```

Canonical newline:

```text
LF
```

Readers may accept CRLF.

Readers may accept a UTF-8 BOM for legacy compatibility.

Canonical writers emit no BOM and LF newlines.

---

# 24. Error handling

Configuration errors use:

```text
validation_status = ERROR
error_kind = CONFIG
```

I/O failures use:

```text
validation_status = ERROR
error_kind = IO
```

Typical errors:

- file missing;
- invalid TOML;
- wrong schema ID;
- unsupported schema version;
- missing table;
- wrong field type;
- invalid regex;
- unsafe path;
- duplicate scenario ID;
- required/optional overlap;
- empty entrypoint list;
- required target excluded by filters.

Errors MUST include:

- field path where known;
- stable error category;
- concise explanation;
- source file path;
- no secret values.

---

# 25. Strict and compatibility modes

## 25.1 Strict mode

Strict mode rejects:

- unknown root tables;
- unknown required fields;
- unsupported versions;
- absolute project paths;
- backslash canonical paths;
- malformed regex;
- duplicate targets;
- placeholder values in active project;
- legacy field names.

## 25.2 Compatibility mode

Compatibility mode may read documented legacy fields and migrate them.

It MUST NOT emit legacy fields.

It MUST NOT make an unsafe project valid silently.

---

# 26. Legacy migration

Earlier GF Audit configuration may store project facts in:

- `app/config.py`;
- CLI defaults;
- GUI state;
- flat `RunConfig`;
- `.gf_audit_state.json`.

Canonical migration mapping:

| Legacy field | Canonical destination |
|---|---|
| `scan_dir` | `sources.directory` |
| `scan_glob` | `sources.glob` |
| `include_regex` | `sources.include_regex` |
| `exclude_regex` | `sources.exclude_regex` |
| project path parts | `gf.path_parts` |
| known top-level targets | `modules.entrypoints` |
| known checkpoint list | `modules.checkpoints` |
| scenario registry | validation scenario arrays |

Fields that do not migrate into `project.toml`:

| Legacy field | Destination |
|---|---|
| `gf_exe` | environment/application state |
| `rgl_root` | environment/application state |
| `out_root` | environment/application state |
| `mode` | run selection/application state |
| `target_file` | run selection/application state |
| `timeout_sec` | run selection/application defaults |
| `max_files` | run selection/application state |
| `no_compile` | run selection/application state |
| `emit_cpu_stats` | run selection/application state |

Migration MUST be explicit and atomic.

The legacy source must remain readable until the canonical destination has been validated and written.

---

# 27. Active file versus template

## 27.1 Template

Allowed placeholders:

```text
<project-id>
<language-name>
<language-code>
<project-relative-source-directory>
<entrypoint>
<project-relative-path>
```

A template is not a valid active-project configuration until every required placeholder has been replaced and the resulting file passes schema validation.

## 27.2 Active project

The active file MUST NOT contain unresolved placeholders.

Forbidden active values include strings matching:

```text
<...>
TODO
REPLACE_ME
LANGUAGE_NAME
PROJECT_ID
```

unless they are legitimate documented project values.

Initialization should validate and report placeholders.

---

# 28. Minimal bootstrap project

A newly initialized project may begin with:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "new-language"
name = "New Language"
language_code = "und"
root = "."

[sources]
directory = "lib/src/new-language"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"

[gf]
path_parts = [
  "lib/src",
  "lib/src/new-language",
  "abstract",
  "common",
  "prelude",
]
minimum_version = ""

[modules]
entrypoints = [
  "GrammarNew.gf",
]
checkpoints = []

[validation]
required_scenarios = []
optional_scenarios = []
release_requires_pgf = true
```

This may be structurally valid but not release-ready.

Release readiness is determined by project validation and release criteria.

---

# 29. Complete release-oriented example

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "fra"
name = "French"
language_code = "fra"
root = "."

[sources]
directory = "lib/src/french"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"

[gf]
path_parts = [
  "lib/src",
  "lib/src/french",
  "abstract",
  "common",
  "prelude",
]
minimum_version = "3.12"

[modules]
entrypoints = [
  "GrammarFre.gf",
  "SyntaxFre.gf",
]
checkpoints = [
  "MorphoFre.gf",
  "ParadigmsFre.gf",
  "NounFre.gf",
  "VerbFre.gf",
  "SentenceFre.gf",
  "QuestionFre.gf",
  "RelativeFre.gf",
  "StructuralFre.gf",
  "ExtendFre.gf",
]

[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
  "morphology",
]
optional_scenarios = [
  "generation",
  "introspection",
]
release_requires_pgf = true
```

The active project must use its declared module set.

---

# 30. Release implications

A release-significant configuration change includes:

- project ID change;
- language-code change;
- source-root change;
- entrypoint addition, removal, rename, or reorder;
- checkpoint addition, removal, rename, or reorder;
- required scenario change;
- GF path-order change;
- minimum GF version change;
- `release_requires_pgf` change.

Such a change requires review of:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/DECISION_LOG.md
scenarios
gold files
release tests
```

---

# 31. Schema evolution

## 31.1 Compatible minor changes

Examples:

- optional field with a documented default;
- optional table;
- additional optional metadata;
- new optional validation behavior.

These require a minor schema increment when emitted canonically.

Example:

```text
1.0 → 1.1
```

## 31.2 Breaking major changes

Examples:

- rename a required table;
- remove a required field;
- change field type;
- change path-resolution base;
- change array ordering semantics;
- make an optional field mandatory;
- redefine scenario-ID meaning.

These require:

```text
major schema increment
migration
tests
lock update
release notes
```

## 31.3 No silent extension

The loader MUST NOT depend on an undocumented field that this reference and schema lock do not define.

---

# 32. Validation command

Recommended command:

```text
gf-wordbench project check
```

Strict form:

```text
gf-wordbench project check --strict
```

Recommended checks:

```text
schema identity
schema version
TOML syntax
required tables
required fields
field types
path containment
regex compilation
target uniqueness
scenario uniqueness
required/optional overlap
entrypoint existence
checkpoint existence
filter compatibility
placeholder detection
project-document consistency
```

The command validates configuration.

It does not need to compile every module unless a validation mode is requested separately.

---

# 33. Required unit tests

```text
test_load_valid_project_toml
test_missing_project_file
test_invalid_toml
test_wrong_schema_id
test_missing_schema_version
test_unsupported_major_version
test_missing_required_table
test_missing_required_field
test_wrong_field_type
test_project_id_empty
test_project_root_defaults_not_inferred
test_project_root_escape_rejected
test_source_directory_absolute_rejected
test_source_directory_escape_rejected
test_source_directory_missing
test_source_directory_not_directory
test_empty_glob_rejected
test_invalid_include_regex
test_invalid_exclude_regex
test_empty_regex_allowed
test_path_parts_order_preserved
test_path_parts_duplicate_warns
test_entrypoints_required
test_entrypoint_duplicate_rejected
test_checkpoint_duplicate_rejected
test_module_path_absolute_rejected
test_module_path_escape_rejected
test_required_scenario_duplicate_rejected
test_optional_scenario_duplicate_rejected
test_required_optional_overlap_rejected
test_release_requires_pgf_type_checked
test_unknown_table_rejected_in_strict_mode
test_comments_preserved_by_read_only_validation
test_loader_does_not_rewrite_file
```

---

# 34. Required integration tests

Temporary project fixtures should cover:

```text
valid complete project
minimal bootstrap project
nested source directory
nested entrypoint paths
Windows-style legacy paths
project path containing spaces
Unicode display name
Unicode source path
missing entrypoint
entrypoint excluded by regex
missing checkpoint
checkpoint excluded by regex
scenario file missing
gold file missing for gold-backed required scenario
RGL path parts
minimum GF version present
template placeholders in active file
```

---

# 35. Contract tests

Recommended tests:

```text
project.toml → ProjectConfig
ProjectConfig → RunConfig
ProjectConfig → file selector
ProjectConfig → GF path resolver
ProjectConfig → checkpoint selection
ProjectConfig → release selection
ProjectConfig → scenario registry
ProjectConfig → release gate
```

These tests prevent field-name and semantic drift between provider and consumers.

---

# 36. Conformance checklist

A canonical `project.toml` conforms to this reference when:

```text
[ ] schema_id is gf-wordbench.project
[ ] schema_version is supported
[ ] every required table and field is valid
[ ] exactly one active project and language target are described
[ ] no Portfolio or multi-project fields are present
[ ] machine-specific paths are excluded
[ ] project identity is authoritative
[ ] source root resolution is safe and deterministic
[ ] regexes are valid
[ ] GF path order is preserved
[ ] entrypoints and checkpoints are explicit, unique and ordered
[ ] required and optional scenario sets are disjoint
[ ] release PGF policy is explicit
[ ] CLI and GUI consume the same ProjectConfig semantics
[ ] normal validation does not rewrite project.toml
[ ] legacy migration is explicit
[ ] template and active project use the same schema
[ ] schema and contract tests pass
[ ] lock files agree
```

---

# 37. Troubleshooting order

When project configuration fails, inspect:

1. `project/project.toml` path;
2. UTF-8 and TOML syntax;
3. `schema_id`;
4. `schema_version`;
5. required tables;
6. `project.root`;
7. `sources.directory`;
8. regex escaping;
9. GF path parts;
10. entrypoint paths;
11. checkpoint paths;
12. scenario IDs;
13. source-filter exclusions;
14. environment paths stored in the wrong file;
15. template placeholders;
16. legacy field migration.

Do not fix a project configuration failure by changing generated run files.

---

# 38. Anti-drift indicators

Configuration drift exists when:

- GUI state becomes the source of project identity;
- framework defaults contain one active language;
- CLI and GUI build different project models;
- source paths resolve from current working directory;
- entrypoint order changes silently;
- checkpoint order is alphabetically sorted;
- scenario IDs differ between configuration and files;
- required and optional scenarios overlap;
- an absolute GF executable appears in `project.toml`;
- output-root paths appear in `project.toml`;
- source filters exclude a required target silently;
- a normal run rewrites project comments or formatting;
- a consumer reads undocumented keys;
- a schema field changes without a version change;
- the template and active project use different schemas;
- old-language identifiers remain after cloning.

Any such change requires coordinated review of:

```text
project loader
ProjectConfig model
bootstrap
CLI
GUI
file selector
GF path resolver
scenario registry
release pipeline
schema tests
project template
PERSISTED_SCHEMA_LOCK.md
INTERFILE_CONTRACT_LOCK.md
project interfile lock
this document
```

---

# 39. Cross-references

| Topic | Document |
|---|---|
| Persisted schema | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Framework configuration boundary | `docs/INTERFILE_CONTRACT_LOCK.md` |
| Active project contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Configuration overview | `docs/configuration/CONFIGURATION_OVERVIEW.md` |
| Application state | `docs/configuration/APPLICATION_STATE_REFERENCE.md` |
| Environment and paths | `docs/configuration/ENVIRONMENT_AND_PATHS.md` |
| File selection | `docs/validation/FILE_SELECTION.md` |
| Validation modes | `docs/validation/VALIDATION_MODES.md` |
| GF path resolution | `docs/gf/GF_PATH_RESOLUTION.md` |
| GF compilation | `docs/gf/GF_COMPILATION.md` |
| PGF build | `docs/gf/GF_PGF_BUILD.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Project lifecycle | `docs/projects/PROJECT_MODEL.md` |
| Module targets | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Project validation | `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md` |
| Release policy | `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` |

---

# 40. Governing rule

> Every stable language-project fact belongs in `project.toml`; every machine-specific or run-specific fact belongs elsewhere.

The file must remain small enough to review, strict enough to validate, and complete enough to reproduce the active project's intended validation targets.
