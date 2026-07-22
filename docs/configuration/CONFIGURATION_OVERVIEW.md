# GF Wordbench — Configuration Overview

**Document ID:** `GF-WB-CONFIGURATION-OVERVIEW`  
**Status:** Normative overview  
**Applies to:** Framework defaults, active-project configuration, application state, environment resolution, CLI, GUI, bootstrap, validation runs, reports, and migrations  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\configuration\CONFIGURATION_OVERVIEW.md`  
**Configuration contract:** `1.0.0`  
**Last reviewed:** `2026-07-21`

---

## 1. Purpose

This document defines the configuration architecture of GF Wordbench.

It explains:

- which configuration sources exist;
- what each source is allowed to own;
- how values are resolved;
- which values may be overridden;
- which values must not be overridden;
- how project-relative and environment-specific paths are separated;
- how one immutable run configuration is produced;
- how configuration errors are reported;
- how configuration is persisted and migrated;
- how CLI and GUI remain semantically equivalent;
- how the system avoids duplicated or hidden configuration.

This is an overview document.

Detailed field definitions belong to:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 2. Core rule

> Every configuration value must have one authoritative owner, one documented resolution path, and one final resolved value for a run.

Configuration must not be assembled through unrelated modules reading different files independently.

All execution stages must consume the same resolved run configuration.

The compiler, scanner, scenario runner, PGF builder, reports, CLI, and GUI must not each decide independently:

- which project is active;
- which GF executable to use;
- where the RGL is located;
- which source files belong to the project;
- which entrypoints are required;
- which scenarios are required;
- where run artifacts are written;
- which validation mode is active;
- which timeout applies.

---

## 3. Configuration objectives

The configuration system must be:

### 3.1 Explicit

Correctness-critical values must be represented explicitly after resolution.

### 3.2 Layered

Project policy, local environment, interface selection, and framework defaults must remain separate.

### 3.3 Deterministic

Equivalent inputs must produce equivalent resolved configuration.

### 3.4 Portable

Project-owned configuration must be cloneable without embedding one developer’s machine paths.

### 3.5 Safe

Local preferences must not weaken project release requirements.

### 3.6 Validated

Invalid configuration must fail before dependent execution begins.

### 3.7 Observable

The effective configuration used by a run must be recorded in run evidence.

### 3.8 Migratable

Persisted configuration and state must have explicit schema versions and tested migrations.

---

## 4. Configuration source model

GF Wordbench uses the following configuration sources:

```text
package metadata
framework defaults
active project configuration
application state
environment and discovery
explicit CLI or GUI input
runtime-derived values
```

These sources do not have equal authority over every domain.

A source may override a value only when it is authorized to own or select that value.

---

## 5. Configuration sources at a glance

| Source | Typical owner | Purpose | Portable | Persisted | May define project policy |
|---|---|---|---:|---:|---:|
| Package metadata | Package/build system | App name and version | Yes | Yes | No |
| Framework defaults | `app/config.py` or designated owner | Language-neutral defaults | Yes | Yes | No |
| `project/project.toml` | Active project | Project identity and validation policy | Yes | Yes | Yes |
| Application state | State service | Local preferences and last selections | No | Yes | No |
| Environment/discovery | Bootstrap/environment resolver | Local tool and path resolution | No | Usually no | No |
| CLI input | CLI user/automation | Explicit run selection and local overrides | No | In run summary | No |
| GUI input | GUI user | Same run selection and local overrides | No | State and run summary | No |
| Runtime-derived values | Bootstrap/orchestrator | Run ID, resolved paths, effective stages | Run-specific | Run summary | No |

---

# 6. Package metadata

## 6.1 Purpose

Package metadata owns:

```text
application name
application version
package version
supported Python requirement
distribution identity
```

## 6.2 Single source of truth

Application version must come from one package metadata source.

It must not be duplicated independently in:

- CLI;
- GUI;
- reports;
- state;
- project configuration;
- documentation constants;
- schema versions.

## 6.3 Package version versus schema version

These are distinct:

```text
GF Wordbench package version
project schema version
application-state schema version
run-summary schema version
manifest schema version
scenario-output version
```

A reader must not infer a persisted schema version from the package version.

---

# 7. Framework defaults

## 7.1 Purpose

Framework defaults provide safe language-neutral starting values.

Examples:

```text
default validation mode
default timeout classes
default report behavior
default output limits
default state filename
default encoding policy
default path-discovery policy
default log retention behavior
```

## 7.2 Ownership

Framework defaults should have one owner, such as:

```text
app/config.py
```

or a final equivalent configuration module.

Bootstrap may consume defaults.

It must not redefine conflicting copies.

## 7.3 Language neutrality

Framework defaults must not contain active-language assumptions.

Prohibited examples:

```text
Albanian
Sqi
GrammarSqi.gf
lib/src/albanian
language-specific scenario IDs
language-specific accepted warnings
```

Language-specific examples may appear only in clearly labeled fixtures, migration tests, or documentation examples.

## 7.4 Safe fallback rule

A default may fill an optional value.

A default must not hide a missing required project value.

Examples:

```text
default report detail level       allowed
default finite timeout            allowed
default output-size limit         allowed
invented release entrypoint       prohibited
invented source directory         prohibited
invented language code            prohibited
invented required scenario        prohibited
```

---

# 8. Active-project configuration

## 8.1 Canonical file

```text
project/project.toml
```

## 8.2 Schema identity

```text
schema_id = "gf-wordbench.project"
schema_version = "1.0"
```

The persisted schema lock owns the canonical schema.

## 8.3 Purpose

`project.toml` defines one active language project.

It owns project facts and project validation policy.

It must remain portable across machines.

## 8.4 Typical configuration domains

The canonical project schema includes or resolves domains such as:

```text
project identity
source selection
GF path components
entrypoints
checkpoints
required scenarios
optional scenarios
release requirements
expected artifacts
project validation policy
```

Exact field names belong to `PROJECT_TOML_REFERENCE.md` and `PERSISTED_SCHEMA_LOCK.md`.

## 8.5 Project-owned values

The project configuration is authoritative for:

- project ID;
- display name;
- language code;
- project root semantics;
- source directory;
- source glob;
- include and exclude rules;
- ordered GF path parts owned by the project;
- ordered entrypoints;
- ordered checkpoints;
- required scenario IDs;
- optional scenario IDs;
- whether PGF is required for release;
- project-defined release scope.

## 8.6 Values prohibited from project configuration

Portable project configuration must not store machine-specific values such as:

```text
C:/tools/gf/gf.exe
C:/Users/name/gf-rgl/src
D:/temporary-runs
a developer home directory
GUI window geometry
last opened report
current running state
```

The active project must not be tied to one machine.

## 8.7 Project identity stability

After published runs or releases exist, changing `project.id` is a breaking migration.

Changing the language identifier, module suffix, or entrypoint identity may also require coordinated project migration.

## 8.8 Read-only normal operation

Normal validation reads `project.toml`.

It must not rewrite it.

Only explicit operations may create or modify it, such as:

```text
project initialization
project migration
explicit configuration edit
template materialization
```

---

# 9. Application state

## 9.1 Canonical file

```text
.gf_wordbench_state.json
```

## 9.2 Schema identity

```text
schema_id = "gf-wordbench.app-state"
schema_version = "1.0"
```

## 9.3 Purpose

Application state stores disposable local preferences.

Deleting the state file must not damage the project.

## 9.4 Appropriate state values

Application state may store:

```text
last selected project root
last selected RGL root
last selected GF executable
last selected output root
last selected mode
last selected target
timeout preferences
detail-retention preference
previous-run diff preference
last run directory
last summary path
GUI presentation preferences
```

## 9.5 Prohibited state values

Application state must not be authoritative for:

```text
project ID
language code
source directory
source glob
entrypoints
checkpoints
required scenarios
release gates
expected PGF
project known issues
current RunResult
is_running across application restarts
```

## 9.6 Safe corruption behavior

A missing or malformed state file must not prevent project use.

The application should:

1. report or log the state problem;
2. use safe defaults;
3. avoid overwriting the malformed source until policy permits;
4. continue when all required project and environment configuration can be resolved.

## 9.7 Atomic writes

State writes must use atomic replacement where supported.

A failed state write must not destroy the last valid state.

---

# 10. Environment configuration

## 10.1 Purpose

Environment configuration supplies machine-specific values needed to execute the project.

Typical values:

```text
GF executable
RGL root
output root
temporary root
optional tool locations
locale policy
process environment overrides
```

## 10.2 Environment sources

Machine-specific values may come from:

- explicit CLI input;
- explicit GUI input;
- application state;
- documented environment variables;
- optional executable discovery;
- platform-specific defaults;
- controlled `PATH` lookup.

## 10.3 Environment is not project policy

Environment resolution must not define:

- project identity;
- source inventory;
- entrypoints;
- checkpoints;
- scenario requirement;
- release gate;
- expected linguistic behavior.

## 10.4 Explicit configuration before inherited environment

Correctness-critical explicit values take precedence over inherited process environment.

Recommended GF search-path resolution:

```text
explicit resolved run configuration
→ project-configured path parts
→ configured RGL root and approved standard subdirectories
→ documented environment fallback
→ configuration failure
```

GF Wordbench must not silently depend on a developer’s global `GF_LIB_PATH`.

## 10.5 Secrets

GF Wordbench must not persist or report:

- access tokens;
- private keys;
- passwords;
- complete environment dumps;
- unrelated private variables.

Only approved, relevant environment overrides may be recorded.

---

# 11. Explicit CLI and GUI input

## 11.1 Purpose

CLI and GUI collect one run’s explicit selections.

Typical selections:

```text
mode
target
project root
GF executable
RGL root
output root
timeout override
detail level
previous-run comparison
diagnostic subprofile
```

## 11.2 Shared semantics

CLI and GUI must construct equivalent resolved configuration from equivalent inputs.

They may differ in presentation.

They must not differ in:

- project loading;
- mode meaning;
- GF executable resolution;
- path construction;
- timeout semantics;
- release-gate enforcement;
- scenario requirement;
- persisted result fields.

## 11.3 Interface input is not authority

An interface may choose among allowed policies.

It must not redefine those policies.

Examples:

```text
select mode=checkpoint                  allowed
select configured checkpoint           allowed
increase timeout                        allowed
add optional diagnostic scenario        allowed
remove required release scenario        prohibited
replace project entrypoint silently      prohibited
disable release manifest verification   prohibited
```

## 11.4 Validation before execution

Invalid combinations must be rejected before creating or starting the run when possible.

Examples:

```text
release + no_compile
release + skip_version_probe
checkpoint + unknown checkpoint
quick + no target and no quick default
scenario target + unknown scenario ID
```

---

# 12. Runtime-derived configuration

Some values exist only after bootstrap and orchestration resolve a run.

Examples:

```text
run ID
run directory
resolved native paths
effective GF search path
resolved executable
normalized mode
resolved target set
ordered selected files
ordered selected checkpoints
ordered selected scenarios
effective timeout per stage
effective evidence level
previous compatible run
artifact paths
```

These values are not new configuration authorities.

They are derived from authoritative inputs.

They must be recorded in the run summary where relevant.

---

# 13. Configuration domains and owners

| Domain | Authoritative owner |
|---|---|
| App name and package version | Package metadata |
| Language-neutral defaults | Framework configuration |
| Project identity | `project.toml` |
| Source-selection policy | `project.toml` |
| Entrypoints and checkpoints | `project.toml` |
| Scenario requirement | `project.toml` and validation specification |
| Release requirements | `project.toml` and release specification |
| GF executable location | Explicit environment resolution |
| RGL location | Explicit environment resolution |
| Output root | Explicit environment resolution |
| Last selected local paths | Application state |
| Mode selection | Explicit run input or documented default |
| Mode semantics | Framework validation contract |
| Target selection | Explicit run input |
| Run paths | Run-path builder |
| Artifact filenames | Artifact model/schema owner |
| Stage timeouts | Framework defaults plus permitted run override |
| Effective run configuration | Bootstrap |
| Final run truth | Structured run result and summary |

A value must not have two competing owners.

---

# 14. Domain-specific precedence

There is no single universal precedence order.

Resolution depends on the configuration domain.

---

## 14.1 Project identity precedence

```text
explicit project root
→ project/project.toml
→ failure
```

Project identity must not come from:

- application state alone;
- previous run output;
- source filename guessing;
- GUI labels;
- framework defaults.

Application state may remember a project root, but the selected project’s identity still comes from its `project.toml`.

---

## 14.2 GF executable precedence

Recommended order:

```text
explicit CLI or GUI value
→ explicit environment configuration
→ valid application-state preference
→ documented environment variable
→ optional PATH discovery
→ failure
```

The resolved executable must be recorded.

After resolution, no stage may silently substitute a different executable.

---

## 14.3 RGL root precedence

Recommended order:

```text
explicit CLI or GUI value
→ explicit environment configuration
→ valid application-state preference
→ documented environment variable
→ documented discovery
→ failure when required
```

Project configuration may define path parts relative to an RGL root.

It must not define the local absolute RGL root itself.

---

## 14.4 Output-root precedence

Recommended order:

```text
explicit CLI or GUI value
→ automation value
→ valid application-state preference
→ framework local default
```

The output root must be writable.

It must remain distinct from source roots unless an explicit supported policy states otherwise.

---

## 14.5 Mode precedence

```text
explicit CLI or GUI selection
→ explicit automation selection
→ project default when defined
→ framework default
```

A default must never silently choose `release`.

Legacy mode aliases are normalized during input migration:

```text
file → quick
all  → diagnostic
```

Canonical output uses only:

```text
quick
checkpoint
release
diagnostic
```

---

## 14.6 Target precedence

```text
explicit run target
→ project-defined mode target
→ mode-specific resolution
→ failure when the mode requires a target
```

Release scope is project-defined.

A target override must not reduce release scope.

---

## 14.7 Timeout precedence

```text
explicit permitted run override
→ project operation-specific override when supported
→ framework operation-class default
```

All timeouts must remain finite.

A release override may increase a timeout.

It must not disable timeout enforcement.

---

## 14.8 Release-policy precedence

```text
project release policy
→ framework mandatory safety invariants
```

CLI, GUI, state, and environment cannot weaken release policy.

A framework safety invariant may reject a project configuration that requests unsafe or unsupported behavior.

---

# 15. Override classes

Every override is one of three classes.

## 15.1 Strengthening override

Adds validation or evidence.

Examples:

```text
add scenarios
add entrypoints
enable strict scan
retain more detail
verify additional artifacts
compare an additional baseline
```

Generally allowed.

## 15.2 Neutral override

Changes local execution without weakening truth.

Examples:

```text
change output root
select equivalent GF executable
increase timeout
change GUI presentation
enable CPU statistics
```

Allowed when valid and recorded.

## 15.3 Weakening override

Removes required validation.

Examples:

```text
skip required compile
skip required scenario
skip required gold
skip required PGF
ignore required artifact
disable release gate
```

Allowed only in explicitly defined non-release exploratory workflows.

Never allowed to preserve release eligibility.

---

# 16. Bootstrap responsibility

Bootstrap is the configuration composition boundary.

It should:

1. load package metadata;
2. load framework defaults;
3. identify the selected project root;
4. load and validate `project.toml`;
5. load application state safely;
6. collect explicit CLI or GUI inputs;
7. resolve environment paths;
8. apply authorized precedence rules;
9. normalize legacy aliases;
10. validate mode and target combinations;
11. construct the resolved run configuration;
12. return errors before audit execution.

Bootstrap must not:

- compile GF files;
- run scenarios;
- write reports;
- display GUI-specific dialogs;
- parse report prose;
- infer project identity from run history;
- silently rewrite project configuration;
- hide missing required values.

---

# 17. Resolved configuration

## 17.1 Purpose

The resolved configuration is the single configuration object consumed by orchestration.

It represents the effective values for one run.

## 17.2 Characteristics

The resolved configuration should be:

- immutable after run start, or controlled as effectively immutable;
- fully validated;
- independent of GUI widget objects;
- independent of raw CLI parser objects;
- explicit about paths;
- explicit about mode;
- explicit about targets;
- explicit about selected stages;
- serializable into run metadata;
- safe to pass to worker functions.

## 17.3 Conceptual domains

A final run configuration may contain structured domains such as:

```text
project
environment
selection
validation
timeouts
evidence
output
compatibility
```

Exact Python model names belong to `DATA_MODEL.md` and the interfile contract lock.

## 17.4 No late configuration reads

After resolution, validation stages should not independently reread:

- application state;
- CLI arguments;
- GUI widgets;
- environment variables;
- `project.toml`;
- framework defaults.

A stage receives the values it needs from the resolved configuration or a bounded request model.

---

# 18. Example resolution flow

```text
CLI selects:
  project_root = C:/work/GF_Wordbench
  mode = checkpoint
  target = morphology
  gf_executable = C:/tools/gf/gf.exe

project.toml defines:
  project ID
  language code
  source directory
  checkpoint morphology
  entrypoints
  required scenarios

application state provides:
  last RGL root
  last output root
  detail preference

framework defaults provide:
  finite timeout classes
  report defaults
  output limits

bootstrap validates and resolves:
  one project
  one executable
  one RGL root
  one output root
  checkpoint closure
  applicable scenarios
  effective GF path
  run configuration
```

Every downstream stage consumes this resolved result.

---

# 19. Conceptual project configuration example

The persisted schema lock owns the exact canonical shape.

A simplified example:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "example"
name = "Example Language"
language_code = "xxx"
root = "."

[sources]
directory = "lib/src/example"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "(\\.bak\\.gf$|\\.tmp\\.gf$)"

[gf]
path_parts = [
  "lib/src",
  "lib/src/example",
]
minimum_version = ""

[modules]
entrypoints = [
  "GrammarXxx.gf",
  "SyntaxXxx.gf",
]
checkpoints = [
  "MorphoXxx.gf",
  "NounXxx.gf",
  "VerbXxx.gf",
]

[validation]
required_scenarios = [
  "load-main",
  "linearize-basic",
]
optional_scenarios = [
  "generation-bounded",
]
release_requires_pgf = true
```

This example illustrates responsibility.

`PROJECT_TOML_REFERENCE.md` remains authoritative for final field definitions.

---

# 20. Conceptual application-state example

```json
{
  "schema_id": "gf-wordbench.app-state",
  "schema_version": "1.0",
  "environment": {
    "project_root": "C:/work/GF_Wordbench",
    "rgl_root": "C:/work/gf-rgl/src",
    "gf_executable": "C:/tools/gf/gf.exe",
    "output_root": "C:/work/gf-wordbench-runs"
  },
  "selection": {
    "mode": "checkpoint",
    "target_file": "",
    "timeout_sec": 60,
    "max_files": 0,
    "keep_ok_details": false,
    "diff_previous": true,
    "skip_version_probe": false,
    "no_compile": false,
    "emit_cpu_stats": false
  },
  "last_run": {
    "run_dir": null,
    "summary_path": null,
    "status_message": ""
  }
}
```

This file stores convenience values.

It does not define project truth.

---

# 21. Path classes

Configuration paths belong to explicit classes.

## 21.1 Project root

The selected GF Wordbench active-project root.

It contains or resolves:

```text
project/project.toml
project/docs/
project/validation/
active GF source roots
```

## 21.2 Project-relative path

Stored relative to project root.

Examples:

```text
lib/src/example
lib/src/example/GrammarXxx.gf
project/validation/scenarios/load-main.gfs
```

Canonical persisted form uses `/`.

## 21.3 Environment path

Machine-specific absolute path.

Examples:

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl/src
C:/work/gf-wordbench-runs
```

## 21.4 Run-relative path

Stored relative to one run directory.

Examples:

```text
summary.json
raw/compile/GrammarXxx.stdout.txt
artifacts/pgf/Grammar.pgf
```

## 21.5 Source and output separation

Source directories must not be created automatically to hide configuration errors.

Run-owned output directories may be created automatically.

Source and output roots should remain distinct.

---

# 22. GF path configuration

## 22.1 One owner

Effective GF search-path construction must have one owner.

The compiler, scenario runner, and PGF builder must consume equivalent GF path semantics.

## 22.2 Inputs

GF path resolution may combine:

```text
project-owned path parts
active language source root
framework-approved source roots
configured RGL root
operation-specific documented additions
```

## 22.3 Ordering

Path order is semantically significant.

The resolved order must be deterministic and recorded.

## 22.4 Duplicate removal

Equivalent normalized paths should appear once.

Deduplication must preserve first-occurrence order unless the compatibility contract states otherwise.

## 22.5 Missing paths

A missing required path is a configuration error before dependent GF execution.

## 22.6 Inherited environment

Inherited `GF_LIB_PATH` may be used only as a documented fallback.

Its effective contribution must be visible in diagnostics.

---

# 23. GF executable configuration

## 23.1 Resolution

The executable may be supplied as:

- explicit absolute path;
- documented resolvable executable name;
- approved environment-discovery result.

## 23.2 Validation

Before required GF validation begins, the resolved executable must:

- exist or resolve;
- represent a file where the platform can verify it;
- be launchable;
- remain unchanged for the run.

## 23.3 Version probe

The configured executable is used for:

```text
<gf-executable> --version
```

Version probing must not silently use another executable.

## 23.4 Paths with spaces

Paths with spaces must be supported.

The executable and arguments are passed as structured process fields, not one quoted shell string.

---

# 24. Validation-mode configuration

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Mode semantics belong to `VALIDATION_MODES.md`.

Configuration selects a mode and supplies its project-owned content.

It must not redefine canonical meaning.

Examples:

```text
project defines which checkpoints exist
framework defines what checkpoint mode means
project defines required release scenarios
framework defines that release cannot skip them
```

---

# 25. Target configuration

A target should have a typed identity.

Canonical target kinds include:

```text
file
module
checkpoint
entrypoint
scenario
project
regression
```

Examples:

```text
file:lib/src/example/NounXxx.gf
checkpoint:morphology
entrypoint:GrammarXxx
scenario:parse-basic
project:example
```

A target must be resolved and validated before execution.

An arbitrary path must not be accepted as a configured checkpoint.

---

# 26. Scenario configuration

The active project owns the scenario registry.

A scenario configuration should resolve:

```text
scenario ID
script path
required or optional state
applicable modes
checkpoint association
entrypoint
input assets
gold path
timeout class
assertion profile
```

The `.gfs` script does not own this metadata.

Required scenario IDs must be unique and must resolve to existing scripts.

Normal validation must not create missing gold files.

---

# 27. Timeout configuration

## 27.1 Operation classes

Timeouts should be configured by operation class:

```text
version probe
file compilation
checkpoint compilation
entrypoint compilation
PGF build
scenario
generation
diagnostic introspection
```

## 27.2 Finite values

Every external execution must have a finite timeout.

Zero or negative timeout values are invalid unless one documented value explicitly means “use default.”

No value may mean infinite execution in normal validation.

## 27.3 Override policy

A user may generally increase a timeout.

A user may reduce a timeout for exploratory use.

Release configuration must still provide enough finite time to execute the declared contract.

## 27.4 Recording

The effective timeout for each operation must be recoverable from run evidence.

---

# 28. Output configuration

Output configuration may control:

```text
output root
run directory policy
evidence detail
successful-result detail retention
raw output-size limits
aggregate log generation
AI-ready report generation
manifest generation
retention behavior
```

Artifact names and run-directory layouts are not arbitrary interface preferences.

They are owned by the artifact and persisted-schema contracts.

A UI must not rename canonical reports independently.

---

# 29. Logging and evidence configuration

Configuration may select evidence level:

```text
bounded
standard
complete
expanded
```

Evidence level may affect:

- amount of successful-detail retention;
- diagnostic excerpts;
- optional timing;
- optional intermediate files;
- report verbosity.

It must not affect validation truth.

Raw evidence required by a mode must not be disabled by a presentation preference.

---

# 30. Previous-run configuration

Previous-run comparison may be configured through:

```text
automatic compatible previous run
explicit previous run
no comparison where the mode permits
```

The resolver must validate compatibility.

It must not select a previous run solely by newest directory name when project identity or schema is incompatible.

Release-mode comparison requirements belong to `VALIDATION_MODES.md`.

---

# 31. Configuration validation phases

Configuration validation should occur in phases.

## 31.1 Syntax validation

Validate:

- TOML parsing;
- JSON parsing;
- schema identity;
- schema version;
- primitive field types;
- enum values;
- regular expressions;
- numeric ranges.

## 31.2 Structural validation

Validate:

- required sections;
- required fields;
- unique IDs;
- ordered arrays;
- mutually exclusive options;
- authorized overrides.

## 31.3 Path validation

Validate:

- project root;
- source root;
- executable;
- RGL root;
- output root;
- scenario paths;
- gold paths;
- path containment;
- writable output.

## 31.4 Referential validation

Validate:

- entrypoint files exist;
- checkpoint IDs resolve;
- scenario IDs resolve;
- input files exist;
- required gold files exist;
- release targets resolve;
- no duplicate scenario registration exists.

## 31.5 Capability validation

Validate:

- GF can launch;
- supported or permitted GF version;
- required command capabilities;
- platform restrictions;
- optional tool availability when selected.

## 31.6 Mode validation

Validate:

- required target;
- selected checkpoint;
- release scope;
- forbidden weakening flags;
- applicable scenarios;
- required PGF policy.

---

# 32. Configuration error model

Configuration errors must be structured.

Recommended fields:

```text
error_kind
configuration_source
field_path
provided_value
message
remediation
```

Example conceptual error:

```text
error_kind: CONFIG
configuration_source: project/project.toml
field_path: modules.entrypoints[0]
provided_value: GrammarXxx.gf
message: configured entrypoint does not exist
remediation: create the file or correct the entrypoint
```

Secrets or sensitive values must be redacted.

---

# 33. Error severity

Configuration findings may be:

```text
error
warning
info
```

## 33.1 Error

Prevents the selected run from being evaluated correctly.

Examples:

- missing required project field;
- invalid regex;
- missing GF executable;
- unknown release checkpoint;
- missing required scenario;
- invalid schema major version.

## 33.2 Warning

Execution may proceed under documented policy.

Examples:

- GF version newer than tested range;
- optional scenario missing;
- state file unreadable;
- deprecated legacy input;
- output root near a path-length risk.

## 33.3 Info

Useful resolution evidence.

Examples:

- executable discovered from `PATH`;
- state preference ignored because explicit value won;
- legacy mode alias normalized;
- optional environment variable not present.

Release policy may promote specified warnings to errors.

---

# 34. No silent fallback

A fallback is acceptable only when:

- the fallback order is documented;
- the selected source is recorded;
- the fallback preserves semantics;
- the fallback is allowed for the selected mode.

Prohibited silent fallbacks include:

```text
missing project entrypoint → guessed filename
missing RGL root → arbitrary developer directory
invalid release scenario → skip it
missing gold → use current output
missing GF executable → use another installation without notice
invalid output root → write into source tree
unknown mode → use quick
```

---

# 35. Configuration provenance

Every resolved value should retain provenance where diagnostically useful.

Possible provenance values:

```text
package_metadata
framework_default
project_toml
application_state
environment_variable
path_discovery
cli
gui
automation
runtime_derived
legacy_migration
```

Example:

```text
gf_executable:
  value = C:/tools/gf/gf.exe
  source = cli
```

Provenance makes precedence visible and debuggable.

The final persisted schema may store provenance selectively rather than for every field.

---

# 36. Run configuration snapshot

Each run must record enough effective configuration to reproduce or explain it.

Recommended run metadata includes:

```text
project ID
project root
source directory
GF executable
GF version
RGL root
effective GF path
output root
mode
target
selected files
selected checkpoints
selected entrypoints
selected scenarios
timeout values
important overrides
evidence level
compatibility warnings
```

Sensitive or irrelevant environment values must not be recorded.

---

# 37. CLI/GUI parity tests

Equivalent interface inputs must produce equal normalized run configuration.

Required parity cases should include:

```text
same project
same GF executable
same RGL root
same output root
same mode
same target
same timeout
same detail options
same diff option
```

The comparison should ignore presentation-only GUI values.

---

# 38. Application-state migration

Legacy state:

```text
.gf_audit_state.json
```

Canonical state:

```text
.gf_wordbench_state.json
```

Migration rules include:

- local paths move into the environment section;
- execution preferences move into selection;
- last-run pointers move into last-run state;
- project-owned source settings are discarded after `project.toml` is authoritative;
- `is_running` is discarded;
- legacy `file` mode becomes `quick`;
- legacy `all` mode becomes `diagnostic`;
- source remains untouched until canonical output is successfully written.

Canonical writers must not emit the legacy flat format.

---

# 39. Project-configuration migration

A project migration may be required when:

- introducing `project.toml`;
- changing schema major version;
- changing project ID;
- changing language identifier;
- moving source roots;
- changing entrypoint identity;
- changing path-resolution semantics;
- changing scenario identifiers.

A migration must:

1. read the original without modifying it;
2. validate recoverable meaning;
3. produce canonical configuration;
4. report warnings and losses;
5. validate the result;
6. write atomically;
7. preserve the source until success;
8. update project documentation and contracts.

Opening a project must not silently rewrite its configuration.

---

# 40. Configuration files and version control

## 40.1 Commit to version control

Normally commit:

```text
project/project.toml
templates/project/project.toml
project validation metadata
framework defaults
schema definitions
migration code
```

## 40.2 Usually do not commit

Normally exclude:

```text
.gf_wordbench_state.json
local run directories
machine-specific environment files
temporary discovery caches
local GUI geometry
```

A repository may deliberately commit a neutral sample environment file, but not secrets or developer-specific paths.

---

# 41. Security requirements

Configuration handling must:

- validate path containment;
- avoid shell command strings;
- reject unauthorized path traversal;
- avoid reading arbitrary files through project values;
- redact secrets;
- restrict environment propagation;
- use atomic writes;
- treat scenarios as executable project inputs;
- distinguish trusted project configuration from untrusted external input.

A valid schema does not automatically mean a configuration is safe.

Semantic security validation remains required.

---

# 42. Platform behavior

## 42.1 Windows

Must support:

- drive-letter paths;
- paths with spaces;
- `gf.exe`;
- mixed input slash forms;
- native process behavior;
- GUI startup without visible console;
- controlled child-process termination.

## 42.2 Canonical serialization

Portable project paths use `/`.

Local Windows paths may be accepted with `\` and normalized internally.

## 42.3 Platform-neutral orchestration

Windows-specific behavior must remain in environment, launcher, or process adapters.

Project configuration and validation policy remain platform-neutral where possible.

---

# 43. Configuration anti-patterns

## 43.1 Duplicate defaults

Bad:

```text
CLI defines timeout=30
GUI defines timeout=60
compiler defines timeout=120
```

Correct:

```text
one operation-class default
interfaces supply permitted override
resolved value passed to compiler
```

## 43.2 Project policy in state

Bad:

```json
{
  "required_scenarios": ["load-main"]
}
```

in application state.

Correct:

```text
required scenarios in project.toml
```

## 43.3 Local paths in project configuration

Bad:

```toml
gf_executable = "C:/Users/name/tools/gf.exe"
```

Correct:

```text
GF executable resolved from local environment configuration
```

## 43.4 Stage-specific environment reads

Bad:

```text
compiler reads GF_LIB_PATH
scenario runner uses project path parts
PGF builder uses PATH discovery
```

Correct:

```text
bootstrap resolves one effective GF path
all stages consume it
```

## 43.5 Hidden launcher policy

Bad:

```text
launch_release.bat silently adds --skip-scenarios
```

Correct:

```text
launcher forwards explicit arguments to the same CLI semantics
```

## 43.6 Report-derived configuration

Bad:

```text
next run parses summary.md to recover project root
```

Correct:

```text
state or structured summary provides the value
```

---

# 44. Automated checks

Recommended command:

```text
gf-wordbench config check
```

It should validate:

1. package metadata is readable;
2. framework defaults are internally valid;
3. project schema identity and version;
4. required project fields;
5. regular expressions;
6. project-relative path safety;
7. entrypoint existence;
8. checkpoint uniqueness;
9. scenario uniqueness;
10. required scenario existence;
11. required gold existence;
12. environment path resolution;
13. GF executable validation;
14. GF version policy;
15. output-root writability;
16. mode and target combination;
17. prohibited release overrides;
18. state-schema compatibility;
19. legacy migration availability;
20. effective GF path.

Strict mode:

```text
gf-wordbench config check --strict
```

Strict mode may also detect:

- unused project fields;
- deprecated keys;
- duplicate normalized paths;
- state values that duplicate project policy;
- absolute project-owned paths;
- undocumented environment-variable use;
- framework defaults containing active-language identifiers;
- configuration reads outside approved owners.

---

# 45. Required tests

Recommended test structure:

```text
tests/configuration/
├── test_framework_defaults.py
├── test_project_config.py
├── test_project_schema.py
├── test_application_state.py
├── test_environment_resolution.py
├── test_configuration_precedence.py
├── test_path_resolution.py
├── test_run_config.py
├── test_configuration_errors.py
├── test_cli_gui_parity.py
└── test_configuration_migrations.py
```

## 45.1 Framework-default tests

- all defaults are language-neutral;
- all timeouts are finite;
- duplicate constants are absent;
- package version has one owner.

## 45.2 Project tests

- valid project;
- missing required field;
- unknown schema major;
- invalid regex;
- duplicate scenario;
- missing entrypoint;
- absolute machine path rejected;
- deterministic ordering preserved.

## 45.3 State tests

- missing state;
- valid state;
- malformed JSON;
- unknown optional field;
- invalid major version;
- atomic write;
- no project policy restored from state;
- `is_running` discarded.

## 45.4 Precedence tests

- explicit CLI executable wins;
- GUI and CLI resolve equivalently;
- explicit project root wins over remembered root;
- project identity wins over state;
- release gates cannot be weakened;
- explicit timeout wins where permitted;
- environment fallback is visible.

## 45.5 Path tests

- Windows drive path;
- path containing spaces;
- project-relative path;
- mixed slash input;
- parent traversal rejection;
- missing source root;
- writable output creation;
- source root is not auto-created.

## 45.6 Migration tests

- legacy flat state;
- `file → quick`;
- `all → diagnostic`;
- project-owned legacy state fields discarded;
- source preserved until successful migration;
- canonical writer emits only current schema.

---

# 46. Configuration change policy

A configuration change is complete only when:

```text
[ ] Authoritative owner identified
[ ] Field purpose documented
[ ] Type and default defined
[ ] Required or optional status defined
[ ] Override policy defined
[ ] Precedence defined
[ ] Security impact reviewed
[ ] Path semantics reviewed
[ ] Persistence impact reviewed
[ ] Schema version impact classified
[ ] Migration implemented where needed
[ ] CLI impact reviewed
[ ] GUI impact reviewed
[ ] Report impact reviewed
[ ] Tests updated
[ ] Reference documentation updated
[ ] Contract locks updated
```

Changing a field’s owner is usually a breaking architectural change.

---

# 47. Configuration drift indicators

Probable drift exists when:

- the same value exists in framework defaults and `project.toml`;
- CLI and GUI resolve different values from equivalent input;
- a compiler reads environment variables directly;
- a scenario runner builds a different GF path;
- state contains required project scenarios;
- a report determines validation mode;
- project identity is inferred from an output directory;
- a local path appears in portable project configuration;
- a release flag can skip a mandatory gate;
- two modules define the same artifact filename;
- an unknown project field is silently interpreted;
- a legacy alias is emitted by a canonical writer;
- an environment fallback is used but not reported;
- a missing source directory is created automatically;
- `project.toml` is rewritten during normal validation;
- configuration changes after the run starts;
- a stage rereads GUI state;
- one interface supports an undocumented override;
- schema changes without version or migration updates.

Every drift indicator requires correction or an explicit architecture decision.

---

# 48. Documentation ownership map

| Configuration topic | Document |
|---|---|
| Overall architecture | `CONFIGURATION_OVERVIEW.md` |
| Exact project fields | `PROJECT_TOML_REFERENCE.md` |
| Exact state fields | `APPLICATION_STATE_REFERENCE.md` |
| Environment variables and path resolution | `ENVIRONMENT_AND_PATHS.md` |
| Persisted schema and migration | `PERSISTED_SCHEMA_LOCK.md` |
| Validation mode behavior | `validation/VALIDATION_MODES.md` |
| CLI options | `usage/CLI_REFERENCE.md` |
| GUI controls | `usage/GUI_REFERENCE.md` |
| Python provider-consumer contracts | `INTERFILE_CONTRACT_LOCK.md` |
| External GF and process contracts | `EXTERNAL_TOOL_CONTRACT_LOCK.md` |

Rules must not be duplicated inconsistently.

Detailed reference documents may repeat concise context, but one document must remain authoritative for each exact contract.

---

# 49. Final configuration contract

GF Wordbench configuration is divided into distinct responsibilities:

```text
package metadata
    owns application identity and version

framework defaults
    own safe language-neutral defaults

project.toml
    owns active-project identity and validation policy

application state
    owns disposable local preferences

environment resolution
    owns machine-specific tool and path selection

CLI and GUI
    own explicit run selection

bootstrap
    owns final resolution and validation

resolved run configuration
    owns effective values for one run

run summary
    records the effective configuration used
```

The final invariants are:

```text
one active project
one authoritative owner per value
one resolved configuration per run
no hidden late reads
no project policy in application state
no machine paths in portable project configuration
no silent release weakening
no differing CLI and GUI semantics
no unrecorded environment fallback
no unversioned persisted configuration
```

Configuration is correct only when the project remains portable, the local execution environment remains explicit, and every stage receives the same validated interpretation of the run.
