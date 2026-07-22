# GF Wordbench — Interfile Contract Lock

**Document ID:** `GF-WB-ARCH-INTERFILE-LOCK`
**Status:** Normative
**Applies to:** GF Wordbench framework
**Scope:** Contracts between source files, configuration files, scenarios, reports and generated artifacts
**Does not govern:** Internal implementation details that do not affect another file
**Owner:** GF Wordbench maintainers
**Change policy:** Coordinated contract change only

---

## 1. Purpose

This document prevents architectural drift between files in GF Wordbench.

GF Wordbench is composed of files that call, configure, consume or interpret one another. A change may appear locally correct while silently breaking another file that depends on its public behavior.

This lock defines the contracts that exist at file boundaries:

* which file initiates a request;
* which file provides the response;
* which symbols are public;
* which inputs are accepted;
* which outputs are guaranteed;
* which side effects are permitted;
* which errors may be raised or returned;
* which artifacts are created;
* which invariants must remain true;
* which tests must validate the relationship.

A file may change freely internally when its external contract remains compatible.

A contract must not change implicitly.

---

## 2. Core rule

> A provider file and all of its consumer files form one change unit whenever their shared contract changes.

A contract change is complete only when all of the following have been updated together:

1. the provider;
2. every known consumer;
3. shared models or schemas;
4. affected configuration;
5. unit tests;
6. integration tests;
7. generated artifact expectations;
8. this contract lock;
9. migration notes when compatibility is affected.

Changing only the provider is prohibited when consumers depend on the changed behavior.

Changing only a consumer is prohibited when the provider does not guarantee the requested behavior.

---

## 3. Normative language

The terms below are normative:

* **MUST**: mandatory;
* **MUST NOT**: prohibited;
* **SHOULD**: expected unless a documented reason justifies an exception;
* **SHOULD NOT**: normally prohibited unless explicitly justified;
* **MAY**: optional;
* **LOCKED**: part of the interfile contract;
* **INTERNAL**: implementation detail that may change without coordinated migration;
* **PROVIDER**: file that exposes a symbol, artifact, schema or behavior;
* **CONSUMER**: file that invokes, imports, reads or interprets the provider;
* **OWNER**: file or component responsible for creating or mutating an artifact;
* **OBSERVER**: file allowed to read an artifact without modifying it.

---

## 4. Scope of the lock

This document locks relationships between:

* Python modules;
* CLI and application builders;
* GUI and application builders;
* audit orchestration and audit stages;
* stages and shared data models;
* audit execution and report generators;
* configuration files and configuration loaders;
* GF scenario files and the scenario runner;
* scenario outputs and gold files;
* run results and generated reports;
* state files and state loaders;
* manifests and artifact consumers.

This document does not lock:

* local variable names;
* private helper names beginning with `_`;
* internal algorithm choices;
* formatting that is not parsed by another file;
* comments;
* implementation order inside a provider;
* performance optimizations that preserve observable behavior.

An internal detail becomes part of the contract as soon as another file depends on it.

---

## 5. Contract categories

GF Wordbench uses the following contract categories.

### 5.1 Call contract

A Python file calls a public function or method in another file.

Example:

```text
audit_core.py
    → compiler.py::compile_file(...)
    → CompileSummary
```

### 5.2 Data contract

One file produces a typed object or serialized structure consumed by another.

Example:

```text
result_model.py
    → RunResult
    → report_json.py
```

### 5.3 Configuration contract

A configuration file provides fields interpreted by Python code.

Example:

```text
project/project.toml
    → project_config.py
    → ProjectConfig
```

### 5.4 Artifact contract

One component writes a file that another component reads or exposes.

Example:

```text
report_json.py
    → summary.json
    → diff.py
```

### 5.5 Process contract

A Python component launches GF or another external process and interprets its result.

Example:

```text
scenario_runner.py
    → gf executable
    → stdout, stderr, exit code and generated artifacts
```

### 5.6 Scenario contract

A `.gfs` file communicates with the scenario runner through commands, markers and output expectations.

Example:

```text
load.gfs
    → scenario_runner.py
    → ScenarioResult
```

---

## 6. Contract identity

Every locked relationship MUST have a stable contract identifier.

Format:

```text
IFC-<DOMAIN>-<NUMBER>
```

Examples:

```text
IFC-BOOT-001
IFC-AUDIT-003
IFC-REPORT-002
IFC-SCENARIO-001
```

Contract identifiers MUST NOT be reused for a different relationship.

A retired contract remains recorded with status `retired`.

---

## 7. Required contract fields

Each contract entry MUST define:

| Field                     | Meaning                                                    |
| ------------------------- | ---------------------------------------------------------- |
| Contract ID               | Stable identifier                                          |
| Status                    | `active`, `deprecated`, `retired` or `experimental`        |
| Caller                    | Consumer file                                              |
| Provider                  | Responding file                                            |
| Public symbol or artifact | Function, class, field, file or schema                     |
| Request                   | Inputs supplied by the caller                              |
| Response                  | Value or artifact returned                                 |
| Side effects              | Files, directories, logs or state changes                  |
| Errors                    | Exceptions, error results or failure states                |
| Locked invariants         | Behaviors that must remain true                            |
| Forbidden behavior        | Behavior that would violate separation of responsibilities |
| Compatibility rule        | Conditions for backward compatibility                      |
| Tests                     | Tests proving the contract                                 |
| Owners                    | Responsible components                                     |
| Last reviewed             | Contract review date or release                            |

---

## 8. Global interfile invariants

The following rules apply to all contracts.

### 8.1 Typed boundary rule

Structured information crossing a Python file boundary SHOULD use an explicit type:

* dataclass;
* typed dictionary;
* enum or literal type;
* documented immutable mapping;
* versioned JSON schema.

Passing undocumented dictionaries between major components SHOULD be avoided.

### 8.2 No hidden parsing rule

A consumer MUST NOT infer undocumented meaning from:

* human-readable log formatting;
* exception message wording;
* report prose;
* dictionary insertion order;
* file naming accidents;
* private attributes;
* internal helper behavior.

Information intended for programmatic consumption MUST be represented explicitly.

### 8.3 Single ownership rule

Each generated artifact MUST have one owner.

Only the owner may define:

* its location;
* its filename;
* its schema;
* its write lifecycle;
* its replacement policy.

Observers MUST NOT rewrite owned artifacts.

### 8.4 Stable path rule

Artifact paths MUST be supplied through `RunPaths`, `ProjectConfig` or another explicit path model.

Consumers MUST NOT reconstruct owned paths by duplicating filename constants.

### 8.5 No duplicate execution rule

A report generator MUST NOT rerun compilation, scanning or scenarios to obtain information already produced by the audit.

Reports consume results. They do not create new audit evidence.

### 8.6 Raw evidence preservation rule

Normalized diagnostics MUST retain references to the raw evidence from which they were derived.

At minimum, process-backed results SHOULD preserve:

* command;
* working directory;
* exit code;
* timeout state;
* duration;
* stdout path;
* stderr path.

### 8.7 Compatibility rule

Adding an optional field with a safe default is normally backward compatible.

The following changes are breaking unless migration support is provided:

* removing a public field;
* renaming a public field;
* changing a field type;
* changing a public function signature;
* changing error semantics;
* changing an artifact path or filename;
* changing serialized meaning;
* changing a status value;
* changing which component owns an artifact.

### 8.8 Failure containment rule

A failure in one reporting output SHOULD NOT erase valid raw evidence from the audit.

A report failure MUST be recorded separately from a GF compilation or scenario failure.

### 8.9 Determinism rule

Given equivalent inputs and normalized environment data, consumers SHOULD receive deterministically ordered results.

The following SHOULD be sorted before serialization:

* file results;
* scenario results;
* diagnostic groups;
* artifact lists;
* dependency lists;
* top errors where counts are equal.

---

## 9. Architectural ownership map

| Responsibility                      | Owner                                              |
| ----------------------------------- | -------------------------------------------------- |
| Application defaults                | `app/config.py`                                    |
| Configuration construction          | `app/bootstrap.py`                                 |
| Shared result models                | `app/models.py`                                    |
| File discovery                      | `app/audit/file_selector.py`                       |
| Static GF source checks             | `app/audit/scanner.py`                             |
| GF compilation                      | `app/audit/compiler.py`                            |
| GF scenario execution               | `app/audit/scenario_runner.py`                     |
| Diagnostic normalization            | `app/audit/diagnostics.py`                         |
| Failure relationship classification | `app/audit/classifier.py`                          |
| Source fingerprints                 | `app/audit/fingerprint.py`                         |
| Previous-run comparison             | `app/audit/diff.py`                                |
| Result construction                 | `app/audit/result_model.py`                        |
| Audit orchestration                 | `app/audit/audit_core.py`                          |
| JSON report                         | `app/reports/report_json.py`                       |
| Markdown report                     | `app/reports/report_md.py`                         |
| AI handoff report                   | `app/reports/report_ai_ready.py`                   |
| Raw and aggregate logs              | `app/reports/report_logs.py`                       |
| Per-result detail copies            | `app/reports/report_details.py`                    |
| CLI behavior                        | `app/main_cli.py`                                  |
| GUI behavior                        | `app/main_gui.py`, `app/gui/`                      |
| Process execution                   | `app/utils/process_utils.py`                       |
| Filesystem primitives               | `app/utils/io_utils.py`, `app/utils/path_utils.py` |
| Persistent UI state                 | `app/state.py`                                     |
| Active language contract            | `project/project.toml`                             |
| GF validation scenarios             | `project/validation/scenarios/`                    |
| Expected scenario output            | `project/validation/gold/`                         |

A component MUST NOT silently assume ownership assigned to another component.

---

# 10. Locked framework contracts

## IFC-BOOT-001 — CLI to configuration builder

**Status:** Active

**Caller**

```text
app/main_cli.py
```

**Provider**

```text
app/bootstrap.py
```

**Public symbols**

```python
build_app_config()
build_run_config(...)
```

**Request**

`main_cli.py` supplies normalized command-line values including:

* project root;
* RGL root;
* GF executable;
* output root;
* scan directory;
* scan glob;
* GF path override;
* timeout;
* maximum file count;
* execution mode;
* target file;
* include and exclude patterns;
* execution flags.

**Response**

```python
AppConfig
RunConfig
```

**Locked invariants**

* `build_run_config` MUST validate mode-specific requirements.
* File mode MUST require a target file.
* Paths MUST be normalized before being placed in `RunConfig`.
* Default values MUST come from `AppConfig`.
* An empty explicit GF path MUST trigger the documented automatic path construction.
* CLI code MUST NOT manually reconstruct `RunConfig`.
* `RunConfig` MUST contain all information required for a non-interactive audit.

**Forbidden behavior**

* `bootstrap.py` MUST NOT execute an audit.
* `main_cli.py` MUST NOT duplicate path-building logic.
* `main_cli.py` MUST NOT mutate a returned `RunConfig` to complete missing configuration.

**Errors**

Invalid configuration MAY raise `ValueError`, `FileNotFoundError` or a documented configuration exception.

**Tests**

```text
tests/test_bootstrap.py
tests/test_smoke.py
tests/test_cli.py
```

---

## IFC-BOOT-002 — GUI to configuration builder

**Status:** Active

**Caller**

```text
app/main_gui.py
app/gui/main_window.py
```

**Provider**

```text
app/bootstrap.py
```

**Response**

```python
AppConfig
RunConfig
```

**Locked invariants**

* GUI and CLI MUST use the same `RunConfig` construction path.
* GUI-only state MUST NOT become a required audit dependency.
* The audit MUST remain executable without PySide6.
* GUI values MUST be converted to plain Python values before calling the builder.
* GUI validation MAY provide earlier feedback but MUST NOT replace builder validation.

**Forbidden behavior**

* Audit semantics MUST NOT differ between GUI and CLI for equivalent configuration.
* GUI code MUST NOT call compiler, scanner or reports directly.

---

## IFC-STATE-001 — GUI to persistent state

**Status:** Active

**Caller**

```text
app/main_gui.py
app/gui/main_window.py
```

**Provider**

```text
app/state.py
```

**Artifact**

```text
.gf_wordbench_state.json
```

or the configured equivalent.

**Locked invariants**

* State is convenience data, not project configuration.
* Failure to read state MUST NOT make the framework unusable.
* Invalid state values MUST fall back to safe defaults.
* Project identity and required validation rules MUST come from project configuration, not UI state.
* State MUST NOT contain audit results.
* State MAY contain recently selected paths and UI preferences.

**Security rule**

State files MUST NOT store credentials or secrets.

---

## IFC-AUDIT-001 — CLI and GUI to audit orchestrator

**Status:** Active

**Callers**

```text
app/main_cli.py
app/gui/main_window.py
```

**Provider**

```text
app/audit/audit_core.py
```

**Public symbol**

```python
run_audit(run_config: RunConfig, run_paths: RunPaths | None = None) -> RunResult
```

**Locked invariants**

* `run_audit` is the authoritative application-level audit entry point.
* Equivalent `RunConfig` values MUST produce equivalent pipeline selection.
* `run_audit` MUST return a `RunResult`, including partial-failure cases where evidence was created.
* Reports MUST be generated through the orchestration layer or a documented reporting stage.
* Consumers MUST determine success from the returned result, not by parsing console output.
* `run_audit` MUST not require GUI state.

**Forbidden behavior**

* Callers MUST NOT execute audit stages independently as a substitute for `run_audit`.
* Callers MUST NOT write reports after `run_audit` if report writing is already owned by the orchestrator.

---

## IFC-AUDIT-002 — Audit orchestrator to run-path builder

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/bootstrap.py
```

**Public symbol**

```python
build_run_paths(run_config: RunConfig) -> RunPaths
```

**Response**

`RunPaths` containing all owned run locations.

**Locked invariants**

* A run directory MUST have a unique run identifier.
* Required directories MUST be created before stages use them.
* Paths MUST be represented explicitly in `RunPaths`.
* Stage files MUST use paths from `RunPaths`.
* Report generators MUST NOT independently choose filenames.
* Run structure changes require coordinated updates to reports, manifests, diff loading and tests.

---

## IFC-AUDIT-003 — Audit orchestrator to file selector

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/file_selector.py
```

**Public symbols**

```python
select_files(...)
extract_module_name(...)
```

**Response**

A deterministic selection containing:

* included files;
* excluded files or exclusion counts;
* noise exclusions where applicable.

**Locked invariants**

* Included files MUST satisfy scan directory, glob and inclusion rules.
* Excluded files MUST not be compiled accidentally.
* File ordering MUST be deterministic.
* File mode MUST select exactly the requested target when valid.
* Selection MUST not compile, scan or mutate source files.
* Module-name extraction MUST be independent of report formatting.

**Forbidden behavior**

* `audit_core.py` MUST NOT duplicate selection filters.
* `file_selector.py` MUST NOT create audit output directories.

---

## IFC-AUDIT-004 — Audit orchestrator to scanner

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/scanner.py
```

**Public symbol**

```python
scan_file(
    file_path: Path,
    run_config: RunConfig,
    run_paths: RunPaths,
) -> tuple[ScanCounts, Path]
```

**Request**

* one GF source file;
* run configuration;
* run paths.

**Response**

* structured `ScanCounts`;
* path to the per-file scan log.

**Locked invariants**

* Scanning MUST NOT modify the GF source file.
* Scanning MUST NOT invoke GF.
* Scan findings are heuristic and MUST remain distinct from compile status.
* The scan log path MUST identify an existing or intentionally created file.
* `ScanCounts` fields MUST have stable meanings.
* Comments and string literals MUST be handled according to GF-aware masking rules.
* A compile success MUST NOT erase scan findings.
* A scan finding alone MUST NOT be represented as a GF compilation failure.

**Forbidden behavior**

* The scanner MUST NOT generate reports.
* The scanner MUST NOT classify dependency cascades.
* Consumers MUST NOT parse human-readable scan logs when `ScanCounts` already contains the required data.

---

## IFC-AUDIT-005 — Audit orchestrator to compiler

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/compiler.py
```

**Public symbols**

```python
probe_gf_version(...)
compile_file(...)
build_gf_args(...)
```

**Primary response**

```python
CompileSummary
```

**Required fields**

* `exit_code`;
* `timed_out`;
* `duration_ms`;
* `error_kind`;
* `first_error`;
* `error_detail`;
* `stdout_path`;
* `stderr_path`.

**Locked invariants**

* `stdout_path` and `stderr_path` MUST identify the captured process outputs.
* A timeout MUST set `timed_out = True`.
* A successful compilation MUST have `exit_code == 0`.
* A skipped compilation MUST be distinguishable from a successful GF invocation.
* The exact executed command MUST be reconstructible or recorded.
* Compilation MUST use the configured GF executable and GF path.
* Compiler output parsing MUST be delegated to diagnostic normalization where separated.
* The compiler MUST preserve raw output before normalization.

**Forbidden behavior**

* The compiler MUST NOT classify failures as downstream.
* The compiler MUST NOT generate Markdown or AI reports.
* The caller MUST NOT reparse raw GF output using separate undocumented rules.

---

## IFC-AUDIT-006 — Compiler and scenario runner to process runner

**Status:** Active

**Callers**

```text
app/audit/compiler.py
app/audit/scenario_runner.py
```

**Provider**

```text
app/utils/process_utils.py
```

**Response**

A structured process result containing at least:

* command;
* exit code;
* timeout state;
* duration;
* stdout;
* stderr.

**Locked invariants**

* Timeout handling MUST terminate or contain the process according to platform policy.
* Output capture MUST use explicit encoding behavior.
* Process invocation MUST avoid shell-dependent interpretation unless explicitly required.
* The working directory MUST be explicit.
* Consumers MUST receive output even on non-zero exit.
* Process launch failures MUST be distinguishable from tool-reported failures.

**Forbidden behavior**

* `process_utils.py` MUST NOT interpret GF diagnostics.
* `process_utils.py` MUST NOT know audit statuses such as `direct` or `downstream`.

---

## IFC-AUDIT-007 — Audit orchestrator to fingerprint provider

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/fingerprint.py
```

**Response**

```python
SourceFingerprint
```

**Locked invariants**

* Fingerprints MUST be derived from source content or explicitly documented metadata.
* Equivalent source content MUST produce equivalent content hashes.
* Fingerprint failure MUST not cause loss of compile logs.
* Fingerprints MUST be serialized consistently in `summary.json`.
* Consumers MUST NOT invent alternative hashes for the same field.

---

## IFC-AUDIT-008 — Audit orchestrator to result builder

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/result_model.py
```

**Public symbols**

```python
build_file_result(...)
build_run_result(...)
update_run_counts(...)
bucket_top_errors(...)
```

**Responses**

```python
FileResult
RunResult
```

**Locked invariants**

* Result builders MUST produce internally coherent status fields.
* Totals MUST be derivable from result collections.
* `fail_count` MUST agree with failure results.
* Diagnostic class counts MUST agree with classified results.
* Paths embedded in results MUST point to the corresponding evidence.
* Top-error grouping MUST be deterministic.
* Result builders MUST not rerun audit stages.

---

## IFC-AUDIT-009 — Audit orchestrator to classifier

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/classifier.py
```

**Public symbol**

```python
classify_file_results(file_results: list[FileResult]) -> list[FileResult]
```

**Locked statuses**

```text
ok
direct
downstream
ambiguous
noise
skipped
script_error
```

The exact supported set MUST also be declared in the model or status reference.

**Locked invariants**

* Classification MUST operate on existing results and evidence.
* Classification MUST NOT rerun GF.
* A downstream failure MUST identify at least one blocking relationship when known.
* Direct failures represent likely local/root evidence.
* Ambiguous failures MUST remain ambiguous when evidence is insufficient.
* Classification order MUST be deterministic.
* Original raw diagnostics MUST remain accessible.

**Forbidden behavior**

* The classifier MUST NOT modify source files.
* Reports MUST NOT independently reclassify failures.

---

## IFC-AUDIT-010 — Audit orchestrator to previous-run diff

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/diff.py
```

**Public symbols**

```python
find_previous_run_dir(...)
load_previous_summary(...)
build_diff_entries(...)
```

**Response**

```python
list[DiffEntry]
```

**Locked invariants**

* Diff logic MUST consume structured summaries.
* Human-readable Markdown MUST NOT be the diff source.
* A missing or invalid previous run MUST produce no diff rather than corrupt the current run.
* Current results MUST remain valid if diff generation fails.
* Path comparison MUST use a stable normalized identity.
* Improvements and regressions MUST use documented status rules.
* Legacy summary compatibility MUST be explicit and tested.

---

## IFC-SCENARIO-001 — Audit orchestrator to scenario runner

**Status:** Planned active contract

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/audit/scenario_runner.py
```

**Public symbols**

```python
run_scenario(...)
run_required_scenarios(...)
```

**Response**

```python
ScenarioResult
```

or a deterministic list of `ScenarioResult`.

**Required fields**

* scenario identifier;
* script path;
* required/optional flag;
* status;
* command;
* working directory;
* exit code;
* timeout state;
* duration;
* stdout path;
* stderr path;
* normalized output path;
* gold path when applicable;
* diagnostic kind;
* primary message;
* produced artifacts.

**Locked invariants**

* Scenario files MUST remain external project assets.
* The runner MUST execute GF rather than reimplement GF commands.
* Raw output MUST be preserved before normalization.
* Required and optional scenarios MUST remain distinguishable.
* Missing required scenarios MUST be reported as configuration failures.
* Gold comparison MUST occur after normalization.
* Updating gold files MUST require an explicit operation.
* Normal audit execution MUST NOT silently rewrite gold files.
* Scenario ordering MUST be deterministic.

---

## IFC-SCENARIO-002 — Scenario file to scenario runner

**Status:** Planned active contract

**Caller artifact**

```text
project/validation/scenarios/<scenario>.gfs
```

**Provider**

```text
app/audit/scenario_runner.py
```

**Locked scenario requirements**

A scenario SHOULD contain stable markers:

```text
GF_WORDBENCH_BEGIN <section-id>
GF_WORDBENCH_END <section-id>
```

or the final marker syntax defined by `SCENARIO_FORMAT.md`.

**Locked invariants**

* Marker identifiers MUST be unique within one scenario.
* The runner MUST verify expected marker completion.
* A missing end marker MUST produce a scenario failure.
* Scenario output normalization MUST not remove semantic GF output.
* A scenario MUST terminate GF explicitly where required.
* Unsupported commands MUST not be treated as success merely because GF returns zero.

---

## IFC-SCENARIO-003 — Scenario output to gold comparison

**Status:** Planned active contract

**Providers**

```text
scenario_runner.py
project/validation/gold/<scenario>.gold
```

**Consumer**

```text
scenario comparison logic
```

**Locked invariants**

* Comparison MUST use normalized output.
* Raw output MUST remain available.
* Normalization rules MUST be versioned or documented.
* Platform-specific paths, timestamps and unstable process noise MAY be normalized.
* Linguistically meaningful output MUST NOT be normalized away.
* Gold files MUST be reviewed source artifacts.
* A missing required gold file MUST not be interpreted as an automatic pass.

---

## IFC-REPORT-001 — Run result to JSON report

**Status:** Active

**Caller**

```text
app/audit/audit_core.py
```

**Provider**

```text
app/reports/report_json.py
```

**Public symbol**

```python
write_summary_json(run_result: RunResult) -> Path
```

**Owned artifact**

```text
summary.json
```

**Locked invariants**

* `summary.json` is the primary machine-readable run summary.
* It MUST be valid UTF-8 JSON.
* It MUST contain a schema or format version.
* It MUST preserve enough structured data for diff loading.
* Paths MUST be serialized consistently.
* Datetimes MUST use a documented representation.
* Status values MUST use the shared model vocabulary.
* Report generation MUST not mutate audit evidence.

**Compatibility**

Removing or renaming serialized fields is breaking unless migration support exists.

---

## IFC-REPORT-002 — Run result to Markdown report

**Status:** Active

**Provider**

```text
app/reports/report_md.py
```

**Owned artifact**

```text
summary.md
```

**Locked invariants**

* `summary.md` is human-readable.
* It MUST derive all claims from `RunResult`.
* It MUST NOT become the machine-readable source of truth.
* Failure sections MUST distinguish direct, downstream and ambiguous results.
* Ordering SHOULD match structured report ordering.

---

## IFC-REPORT-003 — Run result to AI handoff report

**Status:** Active

**Provider**

```text
app/reports/report_ai_ready.py
```

**Owned artifact**

```text
AI_READY.md
```

**Locked invariants**

* The report MUST be created without a second compilation.
* It MUST reference existing raw evidence.
* It SHOULD include the most relevant failure evidence with bounded excerpts.
* It MUST identify artifact paths.
* It MUST distinguish compile failures from scan findings.
* It MUST distinguish root-like failures from downstream failures.
* It MUST not invent a diagnosis unsupported by `RunResult`.
* It MUST remain useful when only one failure exists.
* It MUST not duplicate the same failure into contradictory sections.

---

## IFC-REPORT-004 — Run result to raw log aggregation

**Status:** Active

**Provider**

```text
app/reports/report_logs.py
```

**Owned artifacts**

```text
master.log
ALL_SCAN_LOGS.TXT
ALL_LOGS.TXT
top_errors.txt
```

**Locked invariants**

* Raw logs MUST preserve source attribution.
* Aggregation MUST not destroy the original per-stage logs.
* Missing optional logs MUST not crash report generation.
* Aggregate logs are convenience artifacts, not structured sources of truth.
* `top_errors.txt` MUST use deterministic grouping.
* If `ALL_LOGS.TXT` becomes optional, that policy MUST be reflected in configuration and documentation.

---

## IFC-REPORT-005 — Run result to detail artifacts

**Status:** Active

**Provider**

```text
app/reports/report_details.py
```

**Owned location**

```text
details/
```

**Locked invariants**

* Detail filenames MUST avoid collisions.
* Source result identity MUST remain recoverable.
* Detail creation MUST copy or reference existing evidence.
* It MUST NOT alter raw source logs.
* Duplicate stems MUST be disambiguated deterministically.

---

## IFC-MODEL-001 — Shared models to all consumers

**Status:** Active

**Provider**

```text
app/models.py
```

**Consumers**

```text
app/audit/*
app/reports/*
app/bootstrap.py
app/main_cli.py
app/gui/*
tests/*
```

**Locked public models**

At minimum:

```text
AppConfig
RunConfig
RunPaths
ScanCounts
CompileSummary
SourceFingerprint
FileResult
DiffEntry
RunResult
ScenarioResult
```

`ScenarioResult` becomes locked when implemented.

**Locked invariants**

* Public field names have stable meanings.
* Mutable defaults MUST NOT be shared accidentally.
* Path fields MUST use a consistent type internally.
* Serialization MUST be centralized.
* Status fields MUST use documented values.
* New optional fields MUST have safe defaults.
* Model migrations MUST be reflected in JSON loading and tests.

**Forbidden behavior**

Consumers MUST NOT attach undocumented dynamic attributes to shared result models.

---

## IFC-CONFIG-001 — Application defaults to bootstrap

**Status:** Active

**Provider**

```text
app/config.py
```

**Consumer**

```text
app/bootstrap.py
```

**Locked invariants**

* Application name and version MUST come from the package metadata source.
* Defaults MUST not encode an active language once project configuration exists.
* Constants used across files MUST have one owner.
* `bootstrap.py` MAY apply validation but MUST not redefine conflicting defaults.

---

## IFC-PROJECT-001 — Project configuration to project loader

**Status:** Planned active contract

**Provider artifact**

```text
project/project.toml
```

**Consumer**

```text
app/project_config.py
```

or the final designated loader.

**Required configuration domains**

```text
project identity
source location
GF path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release requirements
```

**Locked invariants**

* One project configuration represents one active language.
* Configuration fields MUST be validated before execution.
* Unknown required fields MUST produce a clear configuration error.
* Language-specific data MUST not be hardcoded in framework defaults.
* Relative paths MUST resolve against the documented project root.
* Scenario identifiers MUST be unique.
* Entrypoints and checkpoints MUST be deterministic lists.

---

## IFC-PROJECT-002 — Project configuration to audit configuration

**Status:** Planned active contract

**Providers**

```text
project/project.toml
app/project_config.py
```

**Consumer**

```text
app/bootstrap.py
```

**Locked invariants**

* Project-specific defaults are loaded before constructing the final `RunConfig`.
* Explicit CLI or GUI values MAY override documented project defaults.
* Required release constraints MUST NOT be bypassed silently by UI state.
* Active-language paths MUST come from project configuration.

---

# 11. Artifact ownership lock

| Artifact                       | Owner                         | Allowed observers                                     |
| ------------------------------ | ----------------------------- | ----------------------------------------------------- |
| `summary.json`                 | `report_json.py`              | diff, CLI, GUI, external tooling                      |
| `summary.md`                   | `report_md.py`                | users, GUI, AI packet builder if explicitly permitted |
| `AI_READY.md`                  | `report_ai_ready.py`          | users and AI systems                                  |
| `top_errors.txt`               | `report_logs.py`              | users and aggregate logs                              |
| `master.log`                   | audit orchestration/log owner | report aggregation                                    |
| per-file scan logs             | `scanner.py`                  | details and report components                         |
| per-file compile stdout/stderr | `compiler.py`                 | classifier, reports and details                       |
| scenario stdout/stderr         | `scenario_runner.py`          | scenario reports and details                          |
| normalized scenario output     | `scenario_runner.py`          | gold comparison and reports                           |
| `.gold` files                  | project maintainers           | scenario comparison                                   |
| `manifest.json`                | designated manifest writer    | all artifact consumers                                |
| state file                     | `state.py`                    | GUI                                                   |
| `project.toml`                 | project maintainers           | project loader                                        |

No observer may rewrite an artifact owned by another component.

---

# 12. Status and error semantics

## 12.1 Tool execution state

Process execution and audit interpretation MUST remain separate.

A process result may contain:

```text
exit_code
timed_out
launch_failed
stdout
stderr
```

An audit result may contain:

```text
status
diagnostic_class
error_kind
primary_message
blocked_by
```

A non-zero process exit does not by itself determine `direct` or `downstream`.

## 12.2 Required status distinctions

The framework MUST distinguish at least:

```text
OK
FAIL
SKIPPED
ERROR
```

where:

* `FAIL` means the validation was executed and did not satisfy its criterion;
* `ERROR` means GF Wordbench could not correctly execute or interpret the validation;
* `SKIPPED` means the stage was intentionally not executed;
* `OK` means the stage completed and met its criteria.

## 12.3 Exceptions versus result failures

Expected validation failures SHOULD be represented as structured results.

Exceptions SHOULD be reserved for:

* invalid configuration;
* impossible filesystem operations;
* process launch failures;
* corrupted internal state;
* contract violations;
* programming errors.

---

# 13. Change classification

Every proposed change affecting more than one file MUST be classified.

## 13.1 Internal change

Characteristics:

* no public signature changes;
* no model-field changes;
* no artifact-path changes;
* no status-semantic changes;
* all existing contract tests continue to pass.

Action:

* update normal tests as needed;
* no contract version change required.

## 13.2 Compatible contract extension

Examples:

* new optional model field;
* new optional report section;
* new optional scenario result metadata;
* new configuration field with a safe default.

Action:

* update provider;
* update relevant consumers;
* add tests;
* update this document;
* increment schema minor version where applicable.

## 13.3 Breaking contract change

Examples:

* field removal or rename;
* function signature change;
* artifact filename change;
* ownership transfer;
* status meaning change;
* required configuration change;
* output normalization change that invalidates gold files.

Action:

1. document the reason;
2. identify all consumers;
3. define migration behavior;
4. update all affected files together;
5. update fixtures and gold files deliberately;
6. add backward-compatibility tests where supported;
7. update changelog and migration guide;
8. increment the relevant major contract or schema version.

## 13.4 Emergency repair

An emergency repair MAY temporarily bypass the normal sequence only when:

* data loss is possible;
* execution is unsafe;
* generated evidence is incorrect;
* a security issue exists.

The contract documentation and missing tests MUST be completed before the repair is considered closed.

---

# 14. Contract-change workflow

A contract-changing pull request or change set MUST include:

```text
[ ] Contract ID identified
[ ] Provider updated
[ ] All consumers identified
[ ] Shared model/schema updated
[ ] Artifact ownership reviewed
[ ] Error behavior reviewed
[ ] Unit tests updated
[ ] Integration tests updated
[ ] Compatibility impact documented
[ ] This lock updated
[ ] Migration documentation added when needed
```

The change description SHOULD state:

```text
Contract:
Current behavior:
New behavior:
Reason:
Consumers:
Compatibility:
Migration:
Evidence:
```

---

# 15. Required contract tests

The framework SHOULD maintain explicit contract tests under:

```text
tests/contracts/
```

Recommended structure:

```text
tests/contracts/
├── test_bootstrap_contracts.py
├── test_audit_stage_contracts.py
├── test_model_contracts.py
├── test_report_contracts.py
├── test_scenario_contracts.py
├── test_artifact_ownership.py
└── test_project_config_contracts.py
```

Contract tests SHOULD verify:

* public signatures where stability matters;
* required result fields;
* status semantics;
* artifact creation;
* artifact ownership;
* deterministic ordering;
* serialization round trips;
* legacy summary loading;
* missing optional artifacts;
* process timeout behavior;
* required scenario behavior;
* gold files are not modified during normal runs.

---

# 16. Automated anti-drift validation

GF Wordbench SHOULD eventually include an automated contract checker.

Suggested command:

```text
gf-wordbench contracts check
```

The checker SHOULD verify:

1. every documented provider file exists;
2. every documented caller file exists;
3. public symbols exist;
4. required model fields exist;
5. artifact constants resolve through their owner;
6. project configuration fields match the loader;
7. documented status values match runtime values;
8. report writers return the documented path type;
9. no normal audit modifies gold files;
10. no report module imports the compiler or scenario runner;
11. no GUI module bypasses `run_audit`;
12. no consumer reconstructs owned artifact filenames.

Optional stricter mode:

```text
gf-wordbench contracts check --strict
```

Strict mode MAY also detect:

* duplicate path constants;
* duplicate status literals;
* imports from private symbols;
* undocumented public exports;
* model fields used by consumers but absent from this lock;
* report-time process execution;
* language-specific paths inside framework modules.

---

# 17. Forbidden dependency directions

The following dependency directions are prohibited.

```text
reports → compiler
reports → scanner
reports → scenario_runner
models → reports
models → GUI
process_utils → audit models
scanner → compiler
compiler → reports
classifier → process execution
project configuration → GUI state
```

The following directions are expected:

```text
CLI/GUI → bootstrap
CLI/GUI → audit_core
audit_core → stages
stages → process_utils
stages → models
audit_core → result_model
audit_core → classifier
audit_core → diff
audit_core → reports
reports → models
```

Circular dependencies between these layers are prohibited.

---

# 18. Boundary between framework and active project

The framework lock governs:

```text
app/
tests/
docs/
templates/
```

The active project governs:

```text
project/project.toml
project/docs/
project/validation/
```

Framework code MUST NOT contain active-language identifiers such as:

```text
albanian
Sqi
GrammarSqi
NounSqi
```

except in:

* migration fixtures;
* clearly named historical compatibility tests;
* example documentation explicitly marked as examples.

The active project MAY contain language-specific names.

Project-specific interfile relationships SHOULD be documented separately in:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

That project lock covers:

* GF module imports;
* lincat expectations;
* constructor/provider relationships;
* scenario-to-entrypoint relationships;
* scenario-to-gold relationships;
* release entrypoints;
* project documentation contracts.

---

# 19. Drift indicators

The following observations indicate probable interfile drift:

* a consumer accesses a field not declared by the provider;
* a report parses human-readable output from another report;
* two files define the same filename constant;
* two components classify the same error differently;
* a new status string appears in only one file;
* a model field is optional in one consumer and required in another;
* a scenario runner and its gold comparator normalize output differently;
* GUI and CLI construct different `RunConfig` values from equivalent inputs;
* a test depends on an active-language path inside framework tests;
* a report reruns GF to fill missing evidence;
* a consumer imports a private helper from another module;
* an artifact moves without updating `RunPaths`;
* a configuration value exists in both `app/config.py` and `project.toml`;
* a gold file changes during a normal validation run;
* `summary.json` changes shape without a schema-version change.

Any detected drift MUST be resolved by restoring the documented contract or deliberately changing the contract through the coordinated workflow.

---

# 20. Review policy

This document MUST be reviewed:

* before a major release;
* when a shared model changes;
* when a new validation stage is introduced;
* when a new generated artifact becomes public;
* when configuration ownership changes;
* when report schemas change;
* when project initialization or reset behavior changes;
* after a significant drift incident.

A contract review SHOULD verify both directions:

```text
Does the provider still guarantee the documented response?
Does the consumer still depend only on the documented guarantee?
```

---

# 21. Contract registry summary

| Contract ID      | Relationship                        | Status  |
| ---------------- | ----------------------------------- | ------- |
| IFC-BOOT-001     | CLI → bootstrap                     | Active  |
| IFC-BOOT-002     | GUI → bootstrap                     | Active  |
| IFC-STATE-001    | GUI → state                         | Active  |
| IFC-AUDIT-001    | CLI/GUI → audit core                | Active  |
| IFC-AUDIT-002    | audit core → run paths              | Active  |
| IFC-AUDIT-003    | audit core → file selector          | Active  |
| IFC-AUDIT-004    | audit core → scanner                | Active  |
| IFC-AUDIT-005    | audit core → compiler               | Active  |
| IFC-AUDIT-006    | compiler/scenarios → process runner | Active  |
| IFC-AUDIT-007    | audit core → fingerprint            | Active  |
| IFC-AUDIT-008    | audit core → result builder         | Active  |
| IFC-AUDIT-009    | audit core → classifier             | Active  |
| IFC-AUDIT-010    | audit core → diff                   | Active  |
| IFC-SCENARIO-001 | audit core → scenario runner        | Planned |
| IFC-SCENARIO-002 | `.gfs` → scenario runner            | Planned |
| IFC-SCENARIO-003 | scenario output → gold comparison   | Planned |
| IFC-REPORT-001   | run result → JSON report            | Active  |
| IFC-REPORT-002   | run result → Markdown report        | Active  |
| IFC-REPORT-003   | run result → AI report              | Active  |
| IFC-REPORT-004   | run result → aggregate logs         | Active  |
| IFC-REPORT-005   | run result → details                | Active  |
| IFC-MODEL-001    | shared models → consumers           | Active  |
| IFC-CONFIG-001   | app defaults → bootstrap            | Active  |
| IFC-PROJECT-001  | project TOML → project loader       | Planned |
| IFC-PROJECT-002  | project loader → run configuration  | Planned |

---

# 22. Contract entry template

Use this template for every new relationship.

```markdown
## IFC-<DOMAIN>-<NUMBER> — <relationship name>

**Status:** Active | Experimental | Deprecated | Retired

**Caller**

`path/to/caller.py`

**Provider**

`path/to/provider.py`

**Public symbol or artifact**

`symbol_name`

**Request**

- field or argument;
- field or argument.

**Response**

`ResponseType`

**Side effects**

- created artifact;
- modified state.

**Errors**

- expected exception;
- structured failure state.

**Locked invariants**

- invariant;
- invariant.

**Forbidden behavior**

- prohibition;
- prohibition.

**Compatibility rule**

Describe compatible and breaking changes.

**Tests**

- `tests/...`

**Owners**

- component or maintainer role.

**Last reviewed**

`<release or date>`
```

---

# 23. Final enforcement rule

A file boundary is part of the architecture.

A provider does not own only its code. It owns the promises made to its consumers.

A consumer does not own the provider’s implementation. It may depend only on the provider’s documented promises.

Therefore:

> No interfile contract may be modified through an isolated file edit.

Every contract change must be coordinated, tested, documented and reviewable as one complete change.
