# GF Wordbench — Application State Reference

**Document ID:** `GF-WB-CONFIG-APPLICATION-STATE`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\configuration\APPLICATION_STATE_REFERENCE.md`  
**Applies to:** Local application-state loading, validation, migration, use and persistence  
**Owner:** GF Wordbench maintainers  
**Lifecycle owner:** `app/state.py`  
**Schema implementation:** `app/schemas/state_schema.py`  
**Interfile contract:** `IFC-STATE-001`  
**Persisted schema:** `gf-wordbench.app-state/1.0`  
**Canonical artifact:** `.gf_wordbench_state.json`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines the local application-state contract for GF Wordbench.

Application state remembers disposable convenience values between application sessions, including:

- recently used local paths;
- the last selected validation mode;
- non-authoritative execution preferences;
- pointers to the most recent run;
- a short user-facing status message.

Application state is not project configuration.

It does not define:

- the active language;
- source-module ownership;
- source-selection policy;
- GF entrypoints;
- release criteria;
- required scenarios;
- gold expectations;
- run results.

The core rule is:

> Application state may improve continuity of use, but deleting, corrupting or ignoring it must never damage the project or change the project’s authoritative contract.

---

## 2. Scope

This reference governs:

- the canonical state filename;
- the canonical JSON schema;
- field meanings and defaults;
- state loading;
- state validation;
- safe fallback behavior;
- state writing;
- atomic replacement;
- migration from legacy `gf-audit` state;
- interaction with the GUI;
- interaction with bootstrap and project configuration;
- path handling;
- security;
- versioning;
- tests;
- anti-drift requirements.

This reference does not govern:

- `project/project.toml`;
- application-wide compiled defaults;
- CLI argument syntax;
- run-summary schemas;
- GUI widget layout;
- audit result schemas;
- operating-system credential stores;
- cloud synchronization;
- multi-user shared preferences;
- arbitrary extension data.

---

## 3. Related normative documents

```text
docs/PERSISTED_SCHEMA_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/REPOSITORY_STRUCTURE.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/usage/CLI_REFERENCE.md
docs/usage/GUI_REFERENCE.md
docs/validation/VALIDATION_MODES.md
project/project.toml
```

This file explains the application-state schema in operational detail.

`PERSISTED_SCHEMA_LOCK.md` remains authoritative for schema identity, compatibility and migration policy.

---

## 4. Normative terminology

- **STATE FILE**: canonical local JSON artifact `.gf_wordbench_state.json`.
- **STATE MANAGER**: `app/state.py`, which owns loading, migration and writing.
- **STATE SCHEMA**: `gf-wordbench.app-state/1.0`.
- **CANONICAL STATE**: the current versioned JSON form emitted by GF Wordbench.
- **LEGACY STATE**: an older unversioned `gf-audit` state form accepted for migration.
- **DEFAULT STATE**: safe in-memory values used when no valid state is available.
- **LOCAL ENVIRONMENT VALUE**: machine-specific path or tool location.
- **SELECTION PREFERENCE**: non-authoritative UI or execution preference.
- **LAST-RUN POINTER**: convenience path to previously generated evidence.
- **RUNTIME-ONLY STATE**: in-memory process state that must not be persisted.
- **PROJECT-OWNED VALUE**: fact or rule whose authority belongs to `project.toml` or project documentation.
- **QUARANTINE**: preserving an invalid state artifact under another name for inspection while continuing with defaults.

---

## 5. Authority boundaries

### 5.1 `project.toml` is authoritative for

```text
project identity
language identity
source roots owned by the project contract
file-selection rules
GF path parts owned by the project
entrypoints
checkpoints
scenario registry
gold mappings
release requirements
```

Application state MUST NOT override those facts silently.

### 5.2 Application state is authoritative only for

```text
remembered local environment paths
remembered validation-mode selection
remembered non-authoritative execution preferences
last-run convenience pointers
short local status text
```

Even these values must be validated before use.

### 5.3 Application defaults are authoritative for fallback values

Framework defaults belong to:

```text
app/config.py
```

The state file stores user selections, not duplicate definitions of framework defaults.

### 5.4 Runtime configuration is authoritative for one execution

A validated `RunConfig` is built from:

```text
project configuration
+ resolved environment
+ explicit current user values
+ allowed state preferences
+ application defaults
```

The state file itself is never passed to an audit stage as a substitute for `RunConfig`.

---

## 6. Precedence rules

Canonical precedence is:

```text
1. explicit current CLI or GUI value
2. authoritative project configuration
3. valid application-state convenience value
4. application default
```

This ordering is applied per field category.

### 6.1 Project-owned fields

For a project-owned field:

```text
project.toml
```

wins over application state.

A conflicting state value is ignored or removed during migration.

### 6.2 Local environment fields

For local environment paths:

```text
explicit current selection
→ valid state value
→ detected or configured application default
→ unresolved
```

Unresolved required environment values must be requested or reported before execution.

### 6.3 Selection preferences

For non-authoritative preferences:

```text
explicit current selection
→ valid state value
→ application default
```

### 6.4 Release constraints

State MUST NOT weaken required release constraints.

Examples:

- remembered `no_compile = true` does not permit a release without compilation;
- remembered `skip_version_probe = true` does not bypass a required compatibility check;
- remembered `max_files` does not silently truncate a release-required file set;
- remembered mode does not change project release criteria.

The configuration builder must reject or override incompatible convenience values explicitly.

---

## 7. Canonical identity

```text
schema_id: gf-wordbench.app-state
schema_version: 1.0
```

These fields identify the state format.

They are not inferred from the GF Wordbench package version.

---

## 8. Canonical path

Repository-relative canonical path:

```text
.gf_wordbench_state.json
```

Typical Windows path:

```text
C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\.gf_wordbench_state.json
```

### 8.1 Path ownership

The canonical state path belongs to the current GF Wordbench repository copy.

One duplicated GF Wordbench copy therefore has one local state file.

### 8.2 Explicit alternate path

Tests and explicitly documented portable or diagnostic invocations MAY supply an alternate state path to the state manager.

An alternate path:

- does not change the canonical filename;
- must be explicit;
- must not become project configuration;
- must obey the same schema;
- must not be inferred from the run-output root.

### 8.3 Not stored under `runs/`

Application state MUST NOT be written inside:

```text
runs/
run_<run-id>/
```

Run directories are evidence, not application preference stores.

### 8.4 Version-control policy

The canonical state file SHOULD be ignored by version control.

It is local, disposable and machine-specific.

---

## 9. Legacy path

Legacy `gf-audit` path:

```text
.gf_audit_state.json
```

The legacy path is read only for controlled migration.

Canonical writers MUST never emit or update it.

---

## 10. Canonical JSON

```json
{
  "schema_id": "gf-wordbench.app-state",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "0.1.0"
  },
  "environment": {
    "project_root": "C:/work/GF_Wordbench",
    "rgl_root": "C:/work/gf-rgl/src",
    "gf_executable": "C:/tools/gf/gf.exe",
    "output_root": "C:/work/gf-wordbench-runs"
  },
  "selection": {
    "mode": "diagnostic",
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

The example paths are illustrative.

They are not defaults and must not be embedded in framework code.

---

## 11. Required root fields

Canonical v1 requires:

```text
schema_id
schema_version
environment
selection
last_run
```

Recommended:

```text
producer
```

### 11.1 Root type

The JSON root MUST be one object.

Arrays, strings, numbers, booleans and `null` are invalid roots.

### 11.2 Unknown root fields

For supported schema major version `1`:

- readers SHOULD ignore unknown optional fields;
- readers MUST NOT reinterpret them;
- canonical writers MUST NOT copy them into newly written state unless a documented migration requires preservation.

### 11.3 Missing required group

A missing required group is invalid canonical state.

Because state is disposable, the reader may recover using that group’s safe defaults rather than fail application startup.

The recovery must be recorded in diagnostics.

---

## 12. Producer object

Canonical shape:

```json
{
  "name": "gf-wordbench",
  "version": "0.1.0"
}
```

### 12.1 `name`

Type:

```text
string
```

Canonical value:

```text
gf-wordbench
```

### 12.2 `version`

Type:

```text
string
```

Meaning:

```text
application version that wrote the state
```

### 12.3 Producer limitations

The reader MUST NOT use `producer.version` as a replacement for `schema_version`.

A different supported producer version does not make the state invalid by itself.

---

# 13. `environment`

The `environment` object stores machine-local path selections.

Canonical fields:

```text
project_root
rgl_root
gf_executable
output_root
```

These are convenience paths, not proof that the targets exist or are valid.

---

## 14. `environment.project_root`

### 14.1 Type

```text
string or null
```

Default:

```text
null
```

### 14.2 Meaning

Recently selected GF Wordbench or active-project root used by the UI to locate:

```text
project/project.toml
```

or the explicitly supported project configuration entry point.

### 14.3 Validation before use

Before execution, the configuration layer must verify:

- path syntax is valid;
- path exists;
- path is a directory;
- required project configuration exists;
- the resolved path is supported by the project model.

### 14.4 Authority limitation

The path locates a project.

It does not define the project’s identity or language.

---

## 15. `environment.rgl_root`

### 15.1 Type

```text
string or null
```

Default:

```text
null
```

### 15.2 Meaning

Recently selected local RGL source root.

### 15.3 Validation before use

The GF toolchain resolver validates:

- existence;
- directory type;
- expected RGL structure;
- compatibility with the active project and GF version.

### 15.4 No hidden path policy

The state value does not define the complete GF search path.

Project configuration and the central path resolver remain authoritative.

---

## 16. `environment.gf_executable`

### 16.1 Type

```text
string or null
```

Default:

```text
null
```

### 16.2 Meaning

Recently selected `gf` or `gf.exe` executable path.

### 16.3 Validation before use

The external-tool resolver must verify:

- path exists;
- path is a regular executable file according to platform policy;
- executable can be launched or probed;
- version is supported or handled by compatibility policy.

### 16.4 No command arguments

This field stores one executable path only.

It MUST NOT contain:

```text
command-line arguments
shell redirection
environment assignments
quoted command strings
```

---

## 17. `environment.output_root`

### 17.1 Type

```text
string or null
```

Default:

```text
null
```

### 17.2 Meaning

Recently selected local root under which new run directories may be created.

### 17.3 Validation before use

The run-path builder validates:

- path syntax;
- containment policy;
- ability to create or write;
- separation from protected source locations;
- release retention policy when relevant.

### 17.4 Not a run directory

The field points to an output root, not to one existing `run_<id>` directory.

---

## 18. Environment path serialization

Canonical environment paths:

- are absolute when available;
- use `/` separators in JSON;
- contain no environment-variable placeholders;
- contain no user-home aliases;
- are valid Unicode strings;
- do not require the target to exist when state is merely loaded.

Example:

```text
C:/tools/gf/gf.exe
```

Legacy readers accept backslashes.

Canonical writers normalize separators to `/`.

### 18.1 No eager filesystem mutation

Loading an environment path MUST NOT create the referenced directory.

Directory creation belongs to the owning operation after validation.

### 18.2 Stale path

A syntactically valid path that no longer exists may remain visible as a remembered value.

It cannot be used for execution until validated.

The UI should identify it as unavailable rather than crash.

---

# 19. `selection`

The `selection` object stores non-authoritative execution and display preferences.

Canonical fields:

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

Every restored selection value passes through the normal configuration builder before an audit begins.

---

## 20. `selection.mode`

### 20.1 Type

```text
string
```

Default:

```text
diagnostic
```

Allowed canonical values:

```text
quick
checkpoint
diagnostic
release
```

### 20.2 Meaning

Most recently selected validation mode.

### 20.3 Invalid value

An unknown value falls back to:

```text
diagnostic
```

The invalid value is not copied into canonical output.

### 20.4 Legacy aliases

Migration only:

```text
file → quick
all  → diagnostic
```

Canonical writers MUST NOT emit `file` or `all`.

---

## 21. `selection.target_file`

### 21.1 Type

```text
string
```

Default:

```text
""
```

### 21.2 Meaning

Most recently selected target source file for a mode or operation that accepts one file.

### 21.3 Empty value

An empty string means:

```text
no remembered target file
```

It does not mean current directory.

### 21.4 Validation before use

The configuration builder validates:

- whether the selected mode accepts or requires a target;
- path existence;
- regular-file status;
- approved source-root containment;
- file-selection policy;
- `.gf` extension where required.

### 21.5 Serialization

This is a local remembered path and may be absolute.

Canonical separators use `/`.

---

## 22. `selection.timeout_sec`

### 22.1 Type

```text
integer
```

Default:

```text
60
```

### 22.2 Valid range

Canonical value must be:

```text
greater than 0
```

### 22.3 Meaning

Remembered general timeout preference where the UI exposes one shared timeout.

Operation-specific final timeouts may be derived or overridden by configuration policy.

### 22.4 Invalid value

Invalid, boolean, fractional, string or non-positive canonical values fall back to the application default.

Legacy readers may coerce an integer string during migration.

Canonical writers emit an integer.

---

## 23. `selection.max_files`

### 23.1 Type

```text
integer
```

Default:

```text
0
```

Meaning:

```text
0 = no user-imposed file-count limit
positive value = remembered diagnostic limit
```

Negative values are invalid.

### 23.2 Release behavior

A remembered positive `max_files` MUST NOT silently truncate a release-required file set.

Release validation either ignores it or rejects the incompatible selection explicitly.

---

## 24. `selection.keep_ok_details`

Type:

```text
boolean
```

Default:

```text
false
```

Meaning:

```text
retain optional detailed human artifacts for successful file results
```

It does not control canonical required evidence.

---

## 25. `selection.diff_previous`

Type:

```text
boolean
```

Default:

```text
true
```

Meaning:

```text
request comparison with an eligible previous run when available
```

A missing or incompatible previous run is handled by comparison policy.

State does not identify which run is authoritative for comparison.

---

## 26. `selection.skip_version_probe`

Type:

```text
boolean
```

Default:

```text
false
```

Meaning:

```text
remember a user preference to skip an optional GF version probe
```

### 26.1 Constraint

This preference cannot bypass a mode or compatibility policy requiring version verification.

---

## 27. `selection.no_compile`

Type:

```text
boolean
```

Default:

```text
false
```

Meaning:

```text
remember a diagnostic preference to omit GF compilation
```

### 27.1 Constraint

This preference cannot make scan-only evidence satisfy a compile or release gate.

---

## 28. `selection.emit_cpu_stats`

Type:

```text
boolean
```

Default:

```text
false
```

Meaning:

```text
request supported GF CPU-statistics output where the operation permits it
```

The external-tool compatibility layer determines whether the installed GF version supports the required option.

---

## 29. Boolean handling

Canonical JSON uses:

```text
true
false
```

Canonical writers MUST NOT emit:

```text
1
0
"true"
"false"
"yes"
"no"
"on"
"off"
```

Legacy migration MAY recognize common boolean aliases.

Ambiguous values fall back to the field default.

---

# 30. `last_run`

The `last_run` object stores convenience pointers only.

Canonical fields:

```text
run_dir
summary_path
status_message
```

It is not an audit-result cache.

---

## 31. `last_run.run_dir`

### 31.1 Type

```text
string or null
```

Default:

```text
null
```

### 31.2 Meaning

Path to the most recently completed or otherwise intentionally recorded run directory.

### 31.3 Limitations

The pointer:

- may become stale;
- does not prove the run is valid;
- does not prove the run belongs to the current project;
- does not replace `summary.json`;
- does not make the run current configuration.

The GUI must validate the path before opening it.

---

## 32. `last_run.summary_path`

### 32.1 Type

```text
string or null
```

Default:

```text
null
```

### 32.2 Meaning

Path to the last known machine-readable `summary.json`.

### 32.3 Validation before use

A consumer validates:

- file exists;
- file is regular;
- schema is supported;
- run relationship is coherent;
- project/run comparison policy permits use.

Application state does not grant schema trust.

---

## 33. `last_run.status_message`

### 33.1 Type

```text
string
```

Default:

```text
""
```

### 33.2 Meaning

Short user-facing continuity text, for example:

```text
Validation completed.
Last run could not be opened.
```

### 33.3 Restrictions

It MUST NOT contain:

- complete logs;
- serialized exceptions;
- stack traces;
- audit results;
- secrets;
- command-line arguments containing secrets;
- unbounded external output.

It is display convenience, not structured status.

### 33.4 Startup behavior

The GUI MAY display the remembered message.

It MUST NOT infer that a run is active or successful solely from this string.

---

## 34. Values that MUST NOT be persisted

The following are runtime-only:

```text
is_running
current_run_config
current_run_result
active process handles
threads
futures
cancellation tokens
open files
GUI widget objects
model object identities
temporary paths
partial report objects
exception objects
stdout/stderr contents
```

### 34.1 Startup invariant

On every application start:

```text
is_running = false
```

regardless of legacy state.

### 34.2 Crash recovery

A process interrupted while running does not resume from application state.

Recovery uses persisted run evidence and explicit workflows, not stale in-memory flags.

---

## 35. Project-owned values prohibited from state

Canonical v1 state MUST NOT store:

```text
language name
language code
module suffix
scan directory
scan glob
include regex
exclude regex
GF path definition
entrypoints
checkpoints
required scenarios
optional scenarios
gold mappings
expected PGF filename
release criteria
source-module ownership
```

These values belong to `project.toml` or project documentation.

### 35.1 Reason

Duplicating them would create two competing project definitions and cause drift.

### 35.2 UI behavior

The GUI may display these values after loading project configuration.

It must not serialize them into application state.

---

## 36. Audit results prohibited from state

Application state MUST NOT contain:

```text
file_results
scenario_results
top_errors
diff_entries
compile summaries
scan counts
diagnostic classes
run totals
manifest entries
raw log content
AI-ready report content
```

The authoritative result is:

```text
run_<run-id>/summary.json
```

State stores only pointers to evidence.

---

## 37. Default canonical state

When no valid state exists, the in-memory state is equivalent to:

```json
{
  "schema_id": "gf-wordbench.app-state",
  "schema_version": "1.0",
  "environment": {
    "project_root": null,
    "rgl_root": null,
    "gf_executable": null,
    "output_root": null
  },
  "selection": {
    "mode": "diagnostic",
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

The producer object is added when the state is written.

---

## 38. Reader contract

The state reader SHOULD expose one stable operation equivalent to:

```python
load_app_state(
    state_path: Path | None = None,
) -> AppState
```

The concrete in-memory type may be a validated dataclass or another explicit model.

It must not be a raw unvalidated dictionary after loading.

### 38.1 Reader sequence

1. resolve canonical or explicit path;
2. if canonical file exists, read it;
3. otherwise, check migration eligibility;
4. read bytes;
5. decode UTF-8;
6. parse JSON;
7. validate root and schema identity;
8. migrate when explicitly supported;
9. validate each group and field;
10. apply safe defaults where permitted;
11. reset runtime-only state;
12. return validated in-memory state;
13. report warnings without preventing startup.

### 38.2 Missing file

A missing state file is normal.

Return default state.

Do not create a state file merely by reading.

### 38.3 Empty file

An empty file is malformed.

Return defaults and record a warning.

### 38.4 Malformed JSON

Malformed JSON MUST NOT crash the application.

Return defaults.

The implementation MAY quarantine the malformed file.

### 38.5 Wrong root type

Return defaults and record a warning.

### 38.6 Schema ID mismatch

A different `schema_id` is not application state.

Do not reinterpret it.

Return defaults and record a schema warning.

### 38.7 Supported major version

For schema major `1`:

- validate required groups;
- ignore unknown optional fields;
- apply documented defaults to invalid convenience values;
- never invent project-owned values.

### 38.8 Unsupported future major

Do not rewrite or downgrade automatically.

Return defaults and preserve the source file.

The UI may state that the state version is unsupported.

---

## 39. Field-level recovery

Because application state is disposable, readers should recover safely when possible.

Examples:

| Invalid field | Recovery |
|---|---|
| unknown mode | `diagnostic` |
| timeout ≤ 0 | application default |
| negative max-files | `0` or application default |
| non-boolean preference | field default |
| malformed path value | `null` or `""` according to field |
| missing optional producer | continue |
| missing required object | default that object |
| runtime-only legacy field | discard |

### 39.1 No partial trust for project facts

Field-level recovery applies only to state-owned convenience fields.

It MUST NOT recover a project rule from state.

### 39.2 Warning aggregation

The reader SHOULD aggregate validation warnings rather than interrupt startup with one dialog per field.

---

## 40. Writer contract

The state writer SHOULD expose one stable operation equivalent to:

```python
save_app_state(
    state: AppState,
    state_path: Path | None = None,
) -> Path
```

### 40.1 Writer input

The writer accepts a validated application-state model.

It MUST NOT accept an arbitrary object graph and serialize every attribute.

### 40.2 Canonical output only

The writer emits:

```text
gf-wordbench.app-state/1.0
```

It never emits the legacy flat schema.

### 40.3 Whitelist serialization

The writer serializes only canonical fields.

Runtime attributes and unknown keys are excluded by construction.

### 40.4 Validation before write

Before writing, the writer validates:

- schema identity;
- field types;
- mode enum;
- integer ranges;
- path serialization;
- absence of prohibited fields;
- JSON serializability.

### 40.5 Return value

On success, return the written path.

On failure, raise or return a documented state-write error without destroying the previous valid state.

---

## 41. JSON serialization

Canonical writer settings:

```text
UTF-8 without BOM
valid JSON
one root object
Unicode preserved
stable indentation
LF newlines
final newline
```

Recommended logical equivalent:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    indent=2,
)
```

followed by one LF.

### 41.1 Key order

JSON key order is not semantically significant.

Canonical writers SHOULD use the documented group and field order for reviewability.

### 41.2 No non-JSON values

Prohibited:

```text
NaN
Infinity
-Infinity
Python Path objects
dataclass objects
sets
bytes
datetime objects
```

They must be converted to canonical scalar forms before serialization.

---

## 42. Atomic write procedure

State writes MUST use atomic replacement where supported.

Canonical sequence:

1. resolve destination;
2. ensure the destination parent is an approved location;
3. create a sibling temporary file;
4. write complete canonical UTF-8 JSON;
5. flush and close;
6. validate the temporary file;
7. replace the destination atomically;
8. remove the temporary file after a failed attempt where safe.

Example temporary path:

```text
.gf_wordbench_state.json.tmp
```

### 42.1 Failure invariant

A failed write MUST NOT destroy the last valid state file.

### 42.2 Parent creation

An explicit alternate-state parent MAY be created when the caller owns it.

The canonical repository root is expected to exist.

The writer MUST NOT create a missing project root to hide a configuration error.

---

## 43. Save lifecycle

State SHOULD be saved at controlled lifecycle points:

```text
normal GUI shutdown
after an explicit preference-save action
after a completed run updates last-run pointers
after a successful legacy migration
```

It SHOULD NOT be rewritten on every keystroke.

### 43.1 Before application shutdown

The GUI converts widget values into plain validated state values before saving.

GUI objects are never passed into serialization.

### 43.2 Failed application shutdown

A failed state save should be logged or shown as a non-fatal warning.

The application’s project and run evidence remain usable.

### 43.3 CLI use

The CLI does not require application state.

A CLI invocation MAY ignore state completely.

A future explicit `--use-state` convenience option would require documentation and must preserve precedence rules.

---

## 44. Last-run update lifecycle

### 44.1 Run begins

Do not persist an active-running flag.

The in-memory UI may set:

```text
is_running = true
```

but the state writer excludes it.

### 44.2 Run completes

After required run evidence is written, application state may update:

```text
last_run.run_dir
last_run.summary_path
last_run.status_message
```

### 44.3 Run fails before run creation

Leave last valid run pointers unchanged unless the UI intentionally clears them.

Update only the short status message if appropriate.

### 44.4 Partial run

A partial run pointer may be stored only when the run directory contains traceable evidence and the UI labels it accurately.

It must not be presented as a successful run.

---

## 45. Safe read failures

State-loading failure is non-fatal.

The framework remains usable with defaults.

The state manager SHOULD make failure visible through:

```text
application log
one bounded GUI warning
diagnostic status
```

It MUST NOT:

- terminate the application;
- delete the project;
- rewrite the invalid file immediately;
- treat missing state as invalid project configuration;
- infer values from unrelated run directories.

---

## 46. Quarantine policy

When a canonical state file is malformed, GF Wordbench MAY preserve it under a quarantine name before the next successful write.

Recommended pattern:

```text
.gf_wordbench_state.invalid-<UTC-ID>.json
```

Quarantine is optional because state is non-critical.

If used:

- the original bytes are preserved;
- the quarantine path remains beside the state file;
- collision handling is safe;
- secrets are not introduced into logs;
- quarantine failure does not prevent fallback to defaults.

GF Wordbench MUST NOT quarantine a supported state merely because one optional field is invalid.

---

## 47. Legacy migration trigger

Legacy import is considered only when:

```text
canonical `.gf_wordbench_state.json` does not exist
and legacy `.gf_audit_state.json` exists
```

If canonical state exists, it wins.

Legacy state is not merged into canonical state automatically.

---

## 48. Legacy flat keys

Recognized legacy keys may include:

```text
selected_mode
selected_target_file
selected_project_root
selected_rgl_root
selected_gf_exe
selected_out_root
selected_scan_dir
selected_scan_glob
selected_gf_path
selected_timeout_sec
selected_max_files
selected_include_regex
selected_exclude_regex
selected_keep_ok_details
selected_diff_previous
selected_skip_version_probe
selected_no_compile
selected_emit_cpu_stats
is_running
last_run_dir
last_summary_path
status_message
```

Unknown keys are ignored.

---

## 49. Legacy mapping

| Legacy key | Canonical destination | Policy |
|---|---|---|
| `selected_project_root` | `environment.project_root` | normalize local path |
| `selected_rgl_root` | `environment.rgl_root` | normalize local path |
| `selected_gf_exe` | `environment.gf_executable` | normalize local path |
| `selected_out_root` | `environment.output_root` | normalize local path |
| `selected_mode` | `selection.mode` | map legacy mode |
| `selected_target_file` | `selection.target_file` | normalize path text |
| `selected_timeout_sec` | `selection.timeout_sec` | validate positive integer |
| `selected_max_files` | `selection.max_files` | validate non-negative integer |
| `selected_keep_ok_details` | `selection.keep_ok_details` | coerce legacy boolean |
| `selected_diff_previous` | `selection.diff_previous` | coerce legacy boolean |
| `selected_skip_version_probe` | `selection.skip_version_probe` | coerce legacy boolean |
| `selected_no_compile` | `selection.no_compile` | coerce legacy boolean |
| `selected_emit_cpu_stats` | `selection.emit_cpu_stats` | coerce legacy boolean |
| `last_run_dir` | `last_run.run_dir` | normalize local path |
| `last_summary_path` | `last_run.summary_path` | normalize local path |
| `status_message` | `last_run.status_message` | retain bounded text |

---

## 50. Legacy values discarded

The following legacy values are not migrated into canonical state:

```text
selected_scan_dir
selected_scan_glob
selected_gf_path
selected_include_regex
selected_exclude_regex
is_running
current_run_config
current_run_result
language-specific values
audit-result data
```

### 50.1 Reason

Source selection and GF path policy belong to project configuration and the central path resolver.

`is_running` and runtime objects are not restart-safe.

### 50.2 No compatibility shadow

Discarded fields MUST NOT be retained under a `legacy` object in canonical state.

That would preserve duplicate authority.

---

## 51. Legacy mode mapping

```text
file → quick
all  → diagnostic
```

Already canonical values remain unchanged when valid.

Unknown modes fall back to:

```text
diagnostic
```

---

## 52. Legacy migration procedure

1. verify canonical file is absent;
2. locate legacy file;
3. read legacy bytes;
4. parse legacy JSON;
5. validate root object;
6. map allowed fields;
7. discard prohibited fields;
8. apply canonical defaults;
9. construct canonical state;
10. validate canonical state;
11. write canonical file atomically;
12. verify canonical file can be read;
13. retain legacy file unchanged;
14. record migration success.

### 52.1 Legacy preservation

The legacy file remains untouched until canonical state is successfully written and verified.

GF Wordbench does not need to delete it automatically.

### 52.2 Repeated startup

After canonical state exists, future startups load canonical state and do not repeat import.

---

## 53. State reset

A reset operation may:

```text
delete `.gf_wordbench_state.json`
or replace it with canonical defaults
```

Recommended user-visible operation:

```text
gf-wordbench state reset
```

or an equivalent GUI action.

### 53.1 Reset effect

Reset clears only local convenience state.

It MUST NOT delete:

```text
project/
project.toml
GF source
gold files
runs/
templates/
framework configuration
```

### 53.2 Missing state

Resetting an already missing state file succeeds idempotently.

---

## 54. State inspection

A diagnostic command MAY expose validated state:

```text
gf-wordbench state show
```

It SHOULD:

- identify the loaded path;
- show schema ID and version;
- show effective canonical fields;
- mark stale paths;
- redact future sensitive fields if ever introduced;
- avoid dumping internal objects.

This is optional and does not require a state-management subsystem beyond `app/state.py`.

---

## 55. Path safety

The state manager validates the state-file path separately from remembered environment paths.

### 55.1 State artifact path

The writer MUST avoid:

- directory traversal from an untrusted filename;
- replacing a directory;
- writing through an unsafe symlink in strict mode;
- writing into a run artifact by default;
- writing outside the explicit or canonical root unintentionally.

### 55.2 Remembered paths

Remembered paths are text until validated by their owning component.

Loading them MUST NOT:

- execute the file;
- open the GF executable;
- create directories;
- scan project files;
- trust symlink targets;
- infer project identity.

---

## 56. Security and privacy

Application state MUST NOT store:

```text
passwords
access tokens
private keys
authentication cookies
license secrets
complete environment dumps
secret command-line arguments
raw source content
raw GF output
user-entered credentials
```

### 56.1 Local paths

Local absolute paths are not treated as secrets by the schema, but they may reveal usernames or directory layout.

State exports or support bundles SHOULD redact them when portability or privacy requires it.

### 56.2 File permissions

GF Wordbench SHOULD rely on normal user-local filesystem permissions.

It MUST NOT deliberately make the state file globally writable.

### 56.3 Untrusted state

A state file is untrusted input.

The reader must validate all types and never evaluate strings.

---

## 57. Concurrency model

Canonical v1 assumes one primary GUI writer per repository copy.

### 57.1 Atomicity

Atomic replacement prevents readers from seeing a partially written JSON document.

### 57.2 Last-writer behavior

When two application instances write concurrently:

```text
last completed atomic writer wins
```

No merge is attempted.

### 57.3 No state database

GF Wordbench does not require:

```text
file locking service
SQLite database
distributed synchronization
conflict-resolution engine
```

Application state is disposable convenience data.

The GUI SHOULD warn or avoid concurrent writers where practical.

---

## 58. In-memory model

A final implementation SHOULD use one explicit validated model, conceptually:

```python
AppState(
    schema_id="gf-wordbench.app-state",
    schema_version="1.0",
    producer=ProducerInfo(...),
    environment=EnvironmentState(...),
    selection=SelectionState(...),
    last_run=LastRunState(...),
)
```

This may be implemented with dataclasses or another typed model.

### 58.1 Model rule

The in-memory model may include runtime-only attributes such as:

```text
is_running
current_run_config
current_run_result
load_warnings
source_path
```

The canonical serializer must whitelist persisted fields and exclude runtime-only values.

### 58.2 No duplicated legacy model

Legacy flat keys may be handled by a migration function.

They should not remain the main application-state model.

---

## 59. State manager responsibilities

`app/state.py` owns:

```text
canonical path resolution
default-state construction
load lifecycle
legacy discovery
migration orchestration
field validation coordination
runtime reset
canonical serialization
atomic save
reset operation
load/save diagnostics
```

`app/state.py` does not own:

```text
project parsing
GF path construction
GF executable probing
audit execution
run result loading
report generation
GUI widgets
```

---

## 60. Schema implementation responsibilities

`app/schemas/state_schema.py` owns:

```text
schema identity
field definitions
field validation
canonical defaults
canonical dictionary conversion
supported-version checks
```

`app/schemas/migrations.py` or a state-owned migration helper owns:

```text
legacy flat-state conversion
mode alias conversion
discard policy
migration warnings
```

No GUI module should duplicate these rules.

---

## 61. GUI integration

### 61.1 Startup

The GUI:

1. requests validated state from `app/state.py`;
2. initializes local path selectors and preferences;
3. loads authoritative project configuration;
4. reconciles state under precedence rules;
5. shows bounded warnings;
6. remains usable when state loading failed.

### 61.2 Widget values

Before creating `RunConfig`, GUI values are converted to plain Python values.

They pass through the shared configuration builder.

### 61.3 Shutdown

The GUI synchronizes allowed widget values into the in-memory state model and invokes the state writer.

### 61.4 Forbidden behavior

The GUI MUST NOT:

- parse canonical JSON independently;
- write `.gf_wordbench_state.json` directly;
- restore `is_running = true`;
- serialize widget objects;
- store project-owned fields;
- construct `RunConfig` by copying state fields manually;
- treat `status_message` as run truth.

---

## 62. Bootstrap integration

Bootstrap may consume validated state convenience values.

It must:

- preserve precedence;
- load `project.toml` for project facts;
- validate required environment paths;
- validate mode-specific requirements;
- construct complete `RunConfig`;
- reject incompatible combinations.

Bootstrap MUST NOT:

- mutate the state file while merely reading configuration;
- use state as a substitute for project configuration;
- execute an audit;
- restore runtime objects.

---

## 63. CLI integration

The CLI remains fully operable without application state.

Canonical CLI behavior:

```text
explicit CLI arguments
+ project configuration
+ application defaults
```

State is not an implicit hidden input.

This ensures reproducible automation.

A GUI action may reuse state because the GUI exposes the remembered values to the user before execution.

---

## 64. Diagnostics

State diagnostics SHOULD distinguish:

```text
state_missing
state_loaded
state_partially_defaulted
state_malformed
state_schema_mismatch
state_version_unsupported
state_migrated
state_write_failed
state_quarantined
```

These are application diagnostics.

They are not audit validation statuses and do not enter `summary.json` unless a run explicitly records relevant startup configuration evidence.

---

## 65. Logging

State logs SHOULD include:

```text
state path
schema ID
schema version
load or save operation
migration source
warning count
success or failure category
```

They MUST NOT include:

```text
complete file content
secrets
complete environment dump
runtime result objects
```

Local paths may be logged according to normal diagnostic privacy policy.

---

## 66. Versioning

Schema version format:

```text
MAJOR.MINOR
```

Current:

```text
1.0
```

### 66.1 Compatible minor extension

A minor version may add:

- an optional state-owned field;
- a safe default;
- a reader that ignores the field;
- no change to existing field meaning.

Requirements:

- schema update;
- model update;
- reader/writer tests;
- documentation update;
- compatibility tests.

### 66.2 Breaking major change

A major version is required for:

```text
removing a required field
renaming a field
changing a field type
changing null/empty semantics
moving authority into or out of state
changing path representation incompatibly
changing mode meanings
changing required root structure
```

### 66.3 Application release independence

A new GF Wordbench release does not require a state schema change when the persisted contract is unchanged.

---

## 67. Unknown future minor versions

A reader supporting major `1` MAY read a newer `1.x` state when:

- required known fields remain valid;
- unknown optional fields are ignored;
- enum values are not reinterpreted;
- canonical rewrite does not claim to preserve unknown fields.

Before rewriting such state, the implementation SHOULD avoid destructive downgrade.

A conservative implementation may keep the file untouched and use known values in memory.

---

## 68. Unsupported major versions

For unsupported major versions:

- preserve the source file;
- return defaults;
- report incompatibility;
- do not migrate without an explicit migrator;
- do not overwrite automatically on startup.

An explicit user save may require confirmation before replacing unsupported state.

---

## 69. Determinism

Equivalent validated state produces equivalent canonical JSON values.

Determinism includes:

```text
same defaults
same mode mapping
same path normalization
same field whitelist
same boolean representation
same integer representation
same logical key ordering
```

The producer application version may legitimately differ between writes.

State files are not expected to be byte-identical across different producer versions when only producer metadata changes.

---

## 70. Required unit tests

Recommended file:

```text
tests/unit/test_state.py
```

### 70.1 Default state

```text
missing canonical file returns defaults
missing legacy file remains non-fatal
default mode is diagnostic
runtime state begins false
paths default to null
target file defaults to empty string
```

### 70.2 Canonical load

```text
valid canonical state
missing producer
unknown optional field
missing group
invalid root type
wrong schema ID
unsupported major
future minor
UTF-8 BOM compatibility
Unicode paths
CRLF JSON
```

### 70.3 Field validation

```text
all four modes
unknown mode
legacy mode aliases only during migration
timeout zero
timeout negative
timeout string in canonical input
negative max-files
boolean aliases in legacy input
boolean aliases rejected/defaulted in canonical input
null paths
empty paths
path with spaces
Windows backslashes
forward-slash canonical write
stale path
```

### 70.4 Runtime exclusions

```text
is_running is never restored true
current_run_config not serialized
current_run_result not serialized
process handles not serializable
audit results not serialized
```

### 70.5 Write behavior

```text
canonical schema emitted
producer emitted
UTF-8 without BOM
Unicode preserved
stable indentation
final newline
temporary file used
atomic replace
old valid file survives failed write
unknown fields not copied
legacy keys not emitted
```

### 70.6 Legacy migration

```text
canonical file wins over legacy
legacy imported when canonical absent
file mode maps to quick
all mode maps to diagnostic
environment paths mapped
selection fields mapped
last-run fields mapped
scan fields discarded
GF-path field discarded
include/exclude fields discarded
is_running discarded
legacy file retained
canonical write verified
malformed legacy does not crash
```

---

## 71. Contract tests

Recommended file:

```text
tests/contracts/test_application_state_contract.py
```

Contract tests MUST verify:

- artifact owner is `app/state.py`;
- GUI does not write state directly;
- canonical filename is defined once;
- canonical schema ID and version match `PERSISTED_SCHEMA_LOCK.md`;
- state does not contain project-owned fields;
- state does not contain audit results;
- state is optional for CLI execution;
- `project.toml` wins for project facts;
- runtime-only state is excluded;
- writer is atomic;
- malformed state is non-fatal;
- legacy aliases are not emitted;
- canonical state is versioned;
- state reset does not delete project or runs;
- local paths are normalized consistently.

---

## 72. Integration tests

Recommended cases:

```text
GUI starts with no state file
GUI starts with valid state
GUI starts with malformed state
GUI starts with stale paths
GUI starts after interrupted prior run
GUI saves on normal shutdown
GUI continues after save failure
project configuration overrides conflicting legacy state
release mode rejects remembered no-compile preference
last-run link opens valid summary
last-run link reports missing summary safely
legacy state migrates once
second startup uses canonical state
two sequential writers preserve valid JSON
```

GUI tests may use a temporary explicit state path.

They MUST NOT depend on the developer’s real home or repository state.

---

## 73. Property tests

Useful bounded properties:

```text
canonical serialize → load preserves canonical values
all loaded modes are canonical
all integer fields satisfy range constraints
runtime-only fields never appear in output
unknown input fields never appear in canonical output
writer output is valid JSON
writer output contains no Path objects
malformed input never crashes the application
deleting state never changes project files
legacy migration never writes the legacy path
```

---

## 74. Failure cases and required response

| Failure | Required response |
|---|---|
| file absent | use defaults |
| permission denied on read | warn, use defaults |
| invalid UTF-8 | preserve file, use defaults |
| invalid JSON | preserve or quarantine, use defaults |
| wrong schema ID | preserve, use defaults |
| unsupported major | preserve, use defaults |
| invalid field | default field or group |
| permission denied on write | keep old file, report non-fatal error |
| temporary write failure | keep old file |
| atomic replacement failure | keep old file where possible |
| legacy migration failure | keep legacy file, use defaults |
| stale last-run path | show unavailable, continue |
| state/project conflict | project configuration wins |

---

## 75. Anti-drift indicators

Probable state-contract drift exists when:

- `.gf_wordbench_state.json` is written by a GUI module;
- two modules define the state filename;
- application state contains language identity;
- application state contains scan directories or entrypoints;
- state contains `RunResult`;
- `is_running` is restored as true;
- CLI behavior changes because hidden state was loaded;
- a release gate is bypassed by remembered preferences;
- canonical writer emits `file` or `all`;
- legacy state is rewritten;
- malformed state crashes startup;
- a failed write truncates the previous state;
- state paths are created while loading;
- backslashes are emitted by the canonical writer;
- producer version is used as schema version;
- unknown fields are copied blindly;
- state is stored inside a run directory;
- reports read application state for audit facts;
- last-run status text is treated as structured result truth;
- a project reset deletes unrelated state without policy;
- a state reset deletes project or run evidence;
- state schema changes without migration and tests.

Any drift indicator requires contract review.

---

## 76. Change workflow

A state-contract change is complete only when all applicable items are checked:

```text
[ ] field ownership reviewed
[ ] project/state boundary reviewed
[ ] schema ID reviewed
[ ] schema version reviewed
[ ] defaults reviewed
[ ] null/empty semantics reviewed
[ ] path representation reviewed
[ ] mode enum reviewed
[ ] release constraints reviewed
[ ] runtime-only exclusions reviewed
[ ] security reviewed
[ ] reader updated
[ ] writer updated
[ ] migration updated
[ ] GUI integration updated
[ ] bootstrap integration updated
[ ] CLI hidden-input rule reviewed
[ ] reset behavior updated
[ ] unit tests updated
[ ] contract tests updated
[ ] integration tests updated
[ ] PERSISTED_SCHEMA_LOCK.md updated
[ ] INTERFILE_CONTRACT_LOCK.md updated when required
[ ] this document updated
```

---

## 77. Implementation checklist

A conforming v1 implementation satisfies:

```text
[ ] canonical path is `.gf_wordbench_state.json`
[ ] schema ID is `gf-wordbench.app-state`
[ ] schema version is `1.0`
[ ] root contains environment, selection and last_run
[ ] producer metadata is emitted
[ ] state is optional
[ ] missing state returns defaults
[ ] malformed state does not crash
[ ] unsupported major is preserved
[ ] project.toml remains authoritative
[ ] language-specific values are excluded
[ ] audit results are excluded
[ ] runtime objects are excluded
[ ] is_running always starts false
[ ] canonical modes are used
[ ] legacy modes migrate
[ ] canonical integers are validated
[ ] canonical booleans are strict
[ ] paths use `/` in JSON
[ ] remembered paths are revalidated before use
[ ] writer uses a field whitelist
[ ] writer uses UTF-8 without BOM
[ ] writer appends a final newline
[ ] writer uses atomic replacement
[ ] failed write preserves old state
[ ] canonical file wins over legacy
[ ] legacy file is retained after migration
[ ] CLI does not depend on hidden state
[ ] GUI uses the state manager
[ ] reset affects only application state
```

---

## 78. Final enforcement rule

Application state is a convenience layer, not a second configuration system.

Therefore:

> No value may be added to application state merely because the GUI currently displays it. A persisted value is valid only when it is local, disposable, safely defaultable, non-secret, non-authoritative for the language project, explicitly validated before use and owned by the state manager.
