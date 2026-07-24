# GF Wordbench — Data Model

**Document ID:** `GF-WB-ARCH-DATA-MODEL`  
**Status:** Normative architecture  
**Applies to:** GF Wordbench shared runtime models, project configuration, application state, validation results, run aggregation, report serialization and schema migration  
**Primary owner:** canonical shared-model package  
**Serialization owners:** schema and report modules  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related schema authority:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Related status authority:** `docs/reference/STATUS_VALUES.md`  
**Related artifact authority:** `docs/architecture/ARTIFACT_MODEL.md`  
**Related interfile authority:** `docs/INTERFILE_CONTRACT_LOCK.md`  
**Last structural review:** 2026-07-24

---

## 1. Purpose

This document defines the canonical data model used at GF Wordbench component boundaries.

It answers:

- which shared models exist;
- which component owns each model;
- which fields have stable meanings;
- which status dimensions remain separate;
- how runtime paths differ from persisted paths;
- how process evidence becomes file and scenario results;
- how file and scenario results remain intentionally different;
- how run totals and overall status are derived;
- how runtime models project into persisted schemas;
- which fields may be optional;
- which defaults are safe;
- which invariants writers, readers, stages and reports must enforce;
- how models evolve without silent contract drift.

The governing rule is:

> A shared model represents one coherent responsibility, uses explicit typed fields, and must not require consumers to parse prose, infer paths, invent defaults or reconstruct missing evidence.

---

## 2. Authority and precedence

When documents overlap, use this authority order:

1. `docs/PERSISTED_SCHEMA_LOCK.md` for persisted field identity and compatibility;
2. `docs/reference/STATUS_VALUES.md` for canonical status vocabularies;
3. this document for runtime model boundaries and field semantics;
4. `docs/INTERFILE_CONTRACT_LOCK.md` for provider and consumer contracts;
5. `docs/architecture/ERROR_HANDLING_MODEL.md` for error propagation;
6. `docs/architecture/ARTIFACT_MODEL.md` for artifact ownership and lifecycle;
7. domain specifications for compilation, scanning, scenarios, reports and configuration.

When a contradiction is found:

1. do not add a local workaround;
2. identify the authoritative owner;
3. correct all affected documents and serializers together;
4. add or update contract tests;
5. provide a migration when persisted data changes.

---

## 3. Scope

This document governs the runtime equivalents of:

```text
AppConfig
ProjectConfig
RunConfig
RunPaths
AppState
ProducerInfo
ProcessResult
ErrorInfo
ScanCounts
SourceFingerprint
CompileSummary
ScenarioSectionResult
ScenarioAssertionResult
ArtifactRecord
FileResult
ScenarioResult
DiffEntry
TopError
RunTotals
RunResult
```

It also governs the canonical enums and value objects used by those models.

This document does not define:

- GUI widget classes;
- CLI parser namespaces;
- TOML parser internals;
- JSON parser internals;
- external GF data structures;
- `.gfo` or `.pgf` binary formats;
- language-specific GF categories, lincats or constructors;
- report layout beyond the structured fields reports consume;
- database entities, because GF Wordbench does not require a database for the core model.

### 3.1 Product boundary

The shared data model represents one active GF language project, one resolved run configuration and one normative language target per run.

Wordbench runtime and persisted models MUST NOT contain:

- a registry of several active Wordbench workspaces;
- a selectable collection of active language projects;
- portfolio-wide inventory, comparison, trend or readiness state;
- `gf-portfolio` private identifiers, configuration, migrations or storage;
- a mandatory connection to an external product.

`gf-portfolio` may consume finalized public Wordbench artifacts through their versioned persisted schemas. Consumer-specific ingestion, indexing and aggregation models belong to `gf-portfolio`, not to the Wordbench shared model.

Application state may retain non-authoritative environment convenience values, but it MUST NOT override the active project identity declared by `project/project.toml`.

---

## 4. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless an explicit exception is documented.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **RUNTIME MODEL**: validated in-memory representation used by framework components.
- **PERSISTED MODEL**: serialized representation governed by a schema.
- **SOURCE OF TRUTH**: the one authoritative field or model for a fact.
- **DERIVED FIELD**: value computed from authoritative fields.
- **EVIDENCE FIELD**: value referencing or summarizing captured execution evidence.
- **COMPATIBILITY FIELD**: temporary field retained for legacy readers.
- **PROJECT-RELATIVE PATH**: path relative to the active project root.
- **RUN-RELATIVE PATH**: path relative to one run directory.
- **ENVIRONMENT PATH**: machine-local path that may be absolute.
- **SUBJECT**: file, scenario, run, artifact or release gate being evaluated.
- **REQUIRED SUBJECT**: subject whose failure or error affects the containing run.
- **OPTIONAL SUBJECT**: subject whose effect is explicitly controlled by project policy.

---

## 5. Core model rules

All shared models MUST follow these rules.

### 5.1 Typed fields

Public fields use explicit types.

Do not expose:

```text
dict[str, object]
Any
untyped tuple
dynamic attributes
parser namespace objects
GUI widget objects
```

as normal component boundaries when a stable model exists.

### 5.2 One owner per fact

A fact has one authoritative owner.

Examples:

```text
file technical error kind
    → FileResult.compile_summary.error_kind

file primary diagnostic
    → FileResult.compile_summary.first_error

scenario technical error kind
    → ScenarioResult.error_kind

scenario primary diagnostic
    → ScenarioResult.primary_message

overall run status
    → RunResult.overall_status

artifact path inventory
    → manifest / ArtifactRecord collection
```

Convenience properties MAY expose a fact.

They MUST NOT create a second writable source of truth.

### 5.3 No shared mutable defaults

Use:

```python
field(default_factory=list)
field(default_factory=dict)
```

or immutable tuples.

Do not use a shared mutable object as a dataclass default.

### 5.4 Runtime immutability

Configuration, path and immutable evidence records SHOULD be frozen after validation.

Result aggregates MAY remain mutable during assembly.

A finalized `RunResult` SHOULD be treated as immutable by report writers.

### 5.5 Central serialization

Models do not serialize themselves through arbitrary `__dict__` traversal.

Canonical serialization is owned by schema or report modules.

Serializers MUST:

- whitelist fields;
- convert paths according to path class;
- convert datetimes to UTC RFC 3339 strings;
- convert enums to canonical strings;
- preserve deterministic ordering;
- exclude runtime-only attributes;
- enforce schema-required nullability.

### 5.6 No orchestration inside models

Shared models MUST NOT:

- launch GF;
- scan files;
- compile modules;
- execute scenarios;
- read GUI state;
- write reports;
- create run directories;
- classify failures from raw prose;
- discover active-language defaults.

### 5.7 No report-side reconstruction

Reports receive structured models.

Reports MUST NOT:

- parse raw GF output to invent fields;
- rerun a stage;
- reconstruct artifact paths by filename convention;
- reclassify direct and downstream failures;
- infer success from a missing result.

### 5.8 No portfolio state in Wordbench models

Shared Wordbench models MUST NOT encode cross-workspace aggregation, external-product lifecycle, Portfolio registry membership or consumer-specific indexing state.

Public Wordbench artifacts expose only Wordbench-owned facts. External products derive their own models from those artifacts without extending or mutating the Wordbench runtime model.

---

## 6. Canonical enum dimensions

The following dimensions remain separate:

```text
validation status
overall run status
execution state
diagnostic class
error kind
validation mode
target kind
regression change kind
scenario assertion status
artifact role
```

A value from one dimension MUST NOT be reused as a shortcut for another.

---

## 7. Validation status

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

Conceptual enum:

```python
class Status(str, Enum):
    OK = "OK"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
```

Meanings:

| Value | Meaning |
|---|---|
| `OK` | Requested validation executed sufficiently and applicable required criteria passed |
| `FAIL` | Validation executed sufficiently and produced reliable evidence of a failed criterion |
| `ERROR` | Execution, interpretation or evidence preservation was not reliable enough for an ordinary validation conclusion |
| `SKIPPED` | Operation was intentionally omitted under the resolved plan |

Precedence for one required subject:

```text
ERROR
FAIL
SKIPPED
OK
```

This precedence is for aggregation. It does not erase stage-specific evidence.

---

## 8. Overall run status

Canonical values:

```text
OK
FAIL
ERROR
```

A finalized run does not use `SKIPPED` as its overall status.

Aggregation rule:

```python
if any(required.status == Status.ERROR):
    overall_status = Status.ERROR
elif any(required.status == Status.FAIL):
    overall_status = Status.FAIL
else:
    overall_status = Status.OK
```

An unexpectedly skipped required subject MUST be converted to or represented by a containing `ERROR` before final aggregation.

---

## 9. Execution state

Canonical non-null values:

```text
completed
timed_out
cancelled
launch_failed
```

Use `None` when no external process request was made.

Conceptual enum:

```python
class ExecutionState(str, Enum):
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    LAUNCH_FAILED = "launch_failed"
```

Required combinations:

```text
timed_out
    → status = ERROR
    → error_kind = TIMEOUT

launch_failed
    → status = ERROR
    → error_kind = TOOL

cancelled
    → status = ERROR

None + SKIPPED
    → intentionally omitted

None + ERROR
    → pre-execution failure
```

Invalid combinations include:

```text
OK + timed_out
OK + cancelled
FAIL + launch_failed
SKIPPED + completed
timed_out + error_kind OK
```

---

## 10. Diagnostic class

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Conceptual enum:

```python
class DiagnosticClass(str, Enum):
    OK = "ok"
    DIRECT = "direct"
    DOWNSTREAM = "downstream"
    AMBIGUOUS = "ambiguous"
    NOISE = "noise"
    SKIPPED = "skipped"
```

Invariants:

```text
status = OK
    → diagnostic_class = ok

diagnostic_class = direct
    → is_direct = true where compatibility field exists

diagnostic_class = downstream
    → blocked_by is non-empty when the blocker is known

diagnostic_class = skipped
    → status = SKIPPED

diagnostic_class = noise
    → subject is excluded or intentionally non-actionable
```

Technical categories such as `TIMEOUT`, `CONFIG` or `SCRIPT` do not belong in `diagnostic_class`.

---

## 11. Error kind

Canonical values:

```text
OK
OTHER
TYPE
SYNTAX
INTERNAL
TIMEOUT
SCRIPT
CONFIG
IO
TOOL
```

Conceptual enum:

```python
class ErrorKind(str, Enum):
    OK = "OK"
    OTHER = "OTHER"
    TYPE = "TYPE"
    SYNTAX = "SYNTAX"
    INTERNAL = "INTERNAL"
    TIMEOUT = "TIMEOUT"
    SCRIPT = "SCRIPT"
    CONFIG = "CONFIG"
    IO = "IO"
    TOOL = "TOOL"
```

Rules:

- `OK` applies only when no technical error applies.
- A failed semantic assertion or gold mismatch normally uses `OTHER`.
- `TIMEOUT` requires `execution_state = timed_out`.
- `TOOL` covers launch and external-tool availability failures.
- `CONFIG` covers invalid resolved configuration.
- `IO` covers required filesystem or decoding failures.
- `SCRIPT` covers invalid or unsupported scenario-script behavior.
- `INTERNAL` covers framework or GF internal failures when no more specific kind applies.

---

## 12. Validation mode

Canonical values:

```text
quick
checkpoint
release
diagnostic
```

Conceptual enum:

```python
class ValidationMode(str, Enum):
    QUICK = "quick"
    CHECKPOINT = "checkpoint"
    RELEASE = "release"
    DIAGNOSTIC = "diagnostic"
```

Legacy aliases may be read only through migration:

```text
file → quick
all  → diagnostic
```

Canonical writers MUST NOT emit the legacy aliases.

---

## 13. Target kind

Canonical values:

```text
file
module
checkpoint
entrypoint
scenario
project
regression
```

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ValidationTarget:
    kind: str
    value: str | None
```

Examples:

```text
file:lib/src/example/NounEx.gf
checkpoint:morphology
entrypoint:GrammarEx
scenario:parse
project:example
```

The target MUST be resolved and validated before execution.

An arbitrary path MUST NOT be accepted as a configured checkpoint or scenario identity.

---

## 14. Regression change kind

Canonical values:

```text
unchanged
improved
regressed
new
removed
```

Conceptual enum:

```python
class ChangeKind(str, Enum):
    UNCHANGED = "unchanged"
    IMPROVED = "improved"
    REGRESSED = "regressed"
    NEW = "new"
    REMOVED = "removed"
```

Deterministic display order:

```text
regressed
new
improved
removed
unchanged
```

---

## 15. Scenario assertion status

Canonical values:

```text
passed
failed
error
skipped
```

These values belong only to scenario assertions.

They are not aliases for the shared validation status enum.

Aggregation:

```text
any assertion error
    → scenario ERROR

else any required assertion failed
    → scenario FAIL

else all required assertions passed
    → scenario OK
```

---

## 16. ProducerInfo

`ProducerInfo` identifies the application that emitted a persisted artifact.

```python
@dataclass(frozen=True, slots=True)
class ProducerInfo:
    name: str
    version: str
```

Canonical values normally include:

```text
name = gf-wordbench
version = package version
```

Rules:

- package version is not a schema version;
- readers MUST NOT infer schema compatibility from the producer version;
- producer metadata contains no machine-local path;
- producer metadata contains no credentials or environment dump.

---

## 17. Application defaults model

`AppConfig` contains language-neutral framework defaults and schema support policy.

It is not active-project configuration and not application state.

Canonical decomposition:

```python
@dataclass(frozen=True, slots=True)
class SelectionDefaults:
    mode: ValidationMode
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool


@dataclass(frozen=True, slots=True)
class OutputDefaults:
    evidence_level: str
    generate_manifest: bool
    generate_ai_ready: bool
    aggregate_logs: bool


@dataclass(frozen=True, slots=True)
class SchemaSupport:
    project_major: int
    app_state_major: int
    run_summary_major: int
    artifact_manifest_major: int


@dataclass(frozen=True, slots=True)
class AppConfig:
    producer: ProducerInfo
    selection_defaults: SelectionDefaults
    output_defaults: OutputDefaults
    schema_support: SchemaSupport
    state_filename: str
```

Exact constant organization MAY differ.

The following semantics are locked:

- defaults are language-neutral;
- timeouts are finite;
- defaults may fill optional values;
- defaults MUST NOT hide missing required project values;
- state filename is local application policy;
- schema support is explicit;
- active-language names, modules and scenario IDs MUST NOT appear as framework defaults.

---

## 18. Project configuration models

The active project configuration is loaded from:

```text
project/project.toml
```

Canonical schema identity:

```text
schema_id = gf-wordbench.project
schema_version = 1.0
```

### 18.1 ProjectIdentity

```python
@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    id: str
    name: str
    language_code: str
    root: Path
```

Rules:

- `id`, `name` and `language_code` are non-empty;
- `root` resolves safely;
- persisted `root` is project-file-relative;
- active project identity does not come from GUI state or old reports.

### 18.2 SourceConfig

```python
@dataclass(frozen=True, slots=True)
class SourceConfig:
    directory: Path
    glob: str
    include_regex: str
    exclude_regex: str
```

Rules:

- `directory` is project-relative in the TOML schema;
- `glob` is a filename-selection pattern;
- include and exclude expressions are validated before use;
- exclusion has documented precedence;
- source selection does not mutate source files.

### 18.3 GFProjectConfig

```python
@dataclass(frozen=True, slots=True)
class GFProjectConfig:
    path_parts: tuple[str, ...]
    minimum_version: str
```

Rules:

- `path_parts` preserve order;
- duplicate semantic entries are removed deterministically during resolution;
- project-relative entries remain portable;
- `minimum_version = ""` means no project-declared minimum;
- the actual executable remains environment configuration, not project configuration.

### 18.4 ModuleTargets

```python
@dataclass(frozen=True, slots=True)
class ModuleTargets:
    entrypoints: tuple[Path, ...]
    checkpoints: tuple[Path, ...]
```

Rules:

- entrypoints are non-empty for an initialized project;
- paths are project/source-relative according to loader policy;
- entries are unique;
- checkpoint ordering is project-owned;
- module existence is validated before execution.

### 18.5 ValidationPolicy

```python
@dataclass(frozen=True, slots=True)
class ValidationPolicy:
    required_scenarios: tuple[str, ...]
    optional_scenarios: tuple[str, ...]
    release_requires_pgf: bool
```

Rules:

- scenario IDs are unique across required and optional lists;
- required and optional membership is explicit;
- a required scenario cannot be silently downgraded by UI state;
- normal validation does not create a missing gold file;
- release policy is project-owned but cannot weaken framework release invariants.

### 18.6 ProjectConfig

```python
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

Derived fields:

```text
project_root
source_root
resolved module paths
resolved scenario registry
resolved GF path contributions
```

The loader MUST NOT:

- invoke GF;
- compile source;
- execute scenarios;
- create project source directories;
- rewrite `project.toml` during normal load;
- infer required values from old run reports.

---

## 19. Application state models

Canonical persisted identity:

```text
schema_id = gf-wordbench.app-state
schema_version = 1.0
path = .gf_wordbench_state.json
```

Application state is disposable machine-local convenience data.

It is not project truth.

### 19.1 EnvironmentState

```python
@dataclass(frozen=True, slots=True)
class EnvironmentState:
    project_root: str
    rgl_root: str
    gf_executable: str
    output_root: str
```

Persisted state uses strings because values may be stale or invalid at the next startup.

They are converted to validated paths only during environment resolution.

### 19.2 SelectionState

```python
@dataclass(frozen=True, slots=True)
class SelectionState:
    mode: ValidationMode
    target_file: str
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool
```

Rules:

- `target_file = ""` is the canonical state-file absence form where retained for schema compatibility;
- final `RunConfig` uses `None` for no target;
- `timeout_sec` is positive;
- `max_files = 0` means unlimited only where configuration explicitly defines it;
- booleans remain booleans;
- release-required behavior cannot be disabled by stale state.

### 19.3 LastRunState

```python
@dataclass(frozen=True, slots=True)
class LastRunState:
    run_dir: str | None
    summary_path: str | None
    status_message: str
```

Rules:

- values are pointers or presentation convenience only;
- the state file does not embed `RunResult`;
- last-run pointers are validated before use;
- stale or missing paths do not make application startup fail;
- `status_message` is not a machine status source.

### 19.4 AppState

```python
@dataclass(frozen=True, slots=True)
class AppState:
    schema_id: str
    schema_version: str
    producer: ProducerInfo | None
    environment: EnvironmentState
    selection: SelectionState
    last_run: LastRunState
```

Runtime-only state MAY include:

```text
is_running
current_run_config
current_run_result
load_warnings
source_path
```

Runtime-only fields MUST NOT be serialized into the canonical state file.

---

## 20. Resolved environment model

Environment resolution converts untrusted or optional path expressions into validated runtime values.

Canonical model:

```python
@dataclass(frozen=True, slots=True)
class ResolvedEnvironment:
    project_root: Path
    rgl_root: Path
    gf_executable: Path
    output_root: Path
    gf_path: tuple[Path, ...]
```

Rules:

- runtime paths are absolute and normalized;
- required paths are validated for the operation that uses them;
- `gf_executable` contains the executable path only, not command arguments;
- `gf_path` preserves effective search order;
- duplicate semantic paths are removed deterministically;
- no path is taken from application state without validation;
- no stage rereads environment variables after `RunConfig` finalization.

---

## 21. RunConfig

`RunConfig` is the fully resolved, validated and effectively immutable configuration for one run.

It is the only configuration object consumed by orchestration.

Canonical model:

```python
@dataclass(frozen=True, slots=True)
class RunConfig:
    project: ProjectConfig
    environment: ResolvedEnvironment

    mode: ValidationMode
    target: ValidationTarget | None

    timeout_sec: int
    max_files: int

    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool

    selected_checkpoints: tuple[Path, ...]
    selected_entrypoints: tuple[Path, ...]
    selected_scenarios: tuple[str, ...]

    release_requires_pgf: bool
    evidence_level: str

    compatibility_warnings: tuple[str, ...] = ()
```

### 21.1 Required semantics

`RunConfig` MUST contain enough information for a non-interactive run.

It MUST NOT require stages to reread:

```text
CLI parser objects
GUI widgets
application state
environment variables
project.toml
framework defaults
```

### 21.2 Path semantics

Runtime fields use normalized `Path` values.

Persisted run metadata projects them as:

```text
project-owned paths
    → project-relative strings

environment paths
    → normalized absolute strings

GF search path
    → ordered normalized strings
```

### 21.3 Mode invariants

- `quick` resolves a focused file or equivalent bounded target.
- `checkpoint` resolves configured checkpoint modules.
- `release` includes required entrypoints, required scenarios and required release gates.
- `diagnostic` may broaden evidence but does not weaken validation truth.
- `no_compile` cannot produce a successful release when compilation is required.
- `skip_version_probe` cannot hide a required release compatibility check.
- required project scenarios cannot be removed by state or presentation preferences.

### 21.4 Metadata projection

The run-summary metadata projection includes at least:

```text
mode
target_file
project_id
project_name
project_root
rgl_root
gf_executable
output_root
source_directory
source_glob
gf_path
timeout_sec
max_files
skip_version_probe
no_compile
emit_cpu_stats
keep_ok_details
diff_previous
```

Additional effective configuration MAY be recorded compatibly when it does not expose secrets.

---

## 22. RunPaths

`RunPaths` is the authoritative in-memory path registry for one run.

```python
@dataclass(frozen=True, slots=True)
class RunPaths:
    run_id: str
    run_dir: Path

    summary_json: Path
    summary_md: Path
    ai_ready_md: Path
    top_errors_txt: Path
    manifest_json: Path

    details_dir: Path

    raw_dir: Path
    master_log: Path
    all_scan_logs: Path
    all_logs: Path
    raw_compile_dir: Path
    raw_scan_dir: Path
    raw_scenarios_dir: Path

    artifacts_dir: Path
    gfo_dir: Path
    out_dir: Path
    pgf_dir: Path
```

### 22.1 Invariants

- `run_id` is stable for one run.
- `run_dir` is not the project source directory.
- every owned path resolves below `run_dir`;
- paths are constructed by one owner;
- stages consume supplied paths;
- consumers MUST NOT derive sibling filenames by string replacement;
- finalized run paths are not redirected;
- existing finalized runs are not overwritten.

### 22.2 Persistence

In memory:

```text
absolute Path values are permitted
```

In persisted run schemas:

```text
run-owned artifact paths are run-relative
```

Example:

```text
summary.json
raw/compile/GrammarEx.stdout.txt
artifacts/pgf/Example.pgf
```

---

## 23. ProcessResult

`ProcessResult` represents external process execution facts.

It does not decide validation status or diagnostic class.

```python
@dataclass(frozen=True, slots=True)
class ProcessResult:
    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    execution_state: ExecutionState
    duration_ms: int
    stdout_path: Path | None
    stderr_path: Path | None
    launch_error: str
```

### 23.1 Invariants

- command order is preserved;
- no implicit shell string replaces the argument vector;
- `duration_ms` is non-negative;
- stdout and stderr remain separate;
- `exit_code` may be `None` for timeout, cancellation or launch failure;
- `launch_error` is bounded and sanitized;
- raw evidence paths belong to the current run;
- process result does not contain a validation status;
- process result does not infer direct or downstream causality.

---

## 24. ErrorInfo

`ErrorInfo` is the shared structured error envelope for stage and run errors.

```python
@dataclass(frozen=True, slots=True)
class ErrorInfo:
    code: str
    error_kind: ErrorKind
    message: str
    detail: str
    stage: str
    operation: str
    subject: str | None
    retryable: bool
    evidence_paths: tuple[str, ...]
    cause_type: str | None
```

Rules:

- `code` is stable and machine-oriented;
- `message` is concise and safe for normal reports;
- `detail` is bounded;
- complete tracebacks belong in diagnostic evidence;
- `stage` identifies the owner;
- `operation` identifies the attempted action;
- `subject` is a stable file, scenario, artifact or configuration identity;
- evidence paths use the appropriate path class;
- secrets and complete environment dumps are prohibited.

---

## 25. ScanCounts

`ScanCounts` is the stable public result of static scanning.

```python
@dataclass(frozen=True, slots=True)
class ScanCounts:
    single_slash_eq: int = 0
    double_slash_dash: int = 0
    runtime_str_match: int = 0
    untyped_case_str_pat: int = 0
    untyped_table_str_pat: int = 0
    trailing_spaces: int = 0
```

Rules:

- every count is a non-negative integer;
- each field has one stable rule meaning;
- counts remain independent of compilation status;
- zero counts mean the scanner completed and found no matching units;
- zero counts do not prove GF validity;
- adding a persisted counter requires schema review;
- scanner I/O failure MUST NOT be represented by a fake all-zero result.

---

## 26. SourceFingerprint

`SourceFingerprint` identifies the exact source bytes observed for one file result.

```python
@dataclass(frozen=True, slots=True)
class SourceFingerprint:
    size_bytes: int
    hash_algorithm: str
    hash: str
    last_modified_utc: datetime
```

Canonical v1:

```text
hash_algorithm = sha256
hash = full lowercase hexadecimal SHA-256
```

Rules:

- `size_bytes` is non-negative;
- hash is calculated from source content;
- equivalent source bytes produce equivalent hashes;
- timestamp is timezone-aware and serialized in UTC;
- hash failure MUST NOT be represented by an empty valid-looking fingerprint;
- legacy `sha1_short` may be imported but MUST NOT be emitted by canonical writers;
- fingerprint failure does not delete or suppress compile evidence.

---

## 27. CompileSummary

`CompileSummary` contains interpreted compile-process evidence for one GF source subject.

```python
@dataclass(frozen=True, slots=True)
class CompileSummary:
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    error_kind: ErrorKind
    first_error: str
    error_detail: str
    stdout_path: Path | None
    stderr_path: Path | None
```

### 27.1 Field semantics

- `exit_code` is the actual exit code when available.
- `timed_out` is a compatibility convenience and agrees with process execution state.
- `duration_ms` is non-negative.
- `error_kind` uses the canonical enum.
- `first_error` is the first useful normalized diagnostic selected by documented rules.
- `error_detail` is bounded supplementary context.
- raw multiline diagnostics remain in stdout or stderr evidence.
- output paths are current-run owned.

### 27.2 Invariants

```text
timed_out = true
    → error_kind = TIMEOUT

successful required compilation
    → exit_code = 0
    → error_kind = OK

non-zero exit
    → error_kind != OK
```

A zero exit does not by itself prove artifact success when an expected `.gfo` or other artifact is required.

---

## 28. ScenarioSectionResult

A scenario section records whether one stable marked section completed.

```python
@dataclass(frozen=True, slots=True)
class ScenarioSectionResult:
    id: str
    completed: bool
```

Compatible optional fields are:

```text
message
begin_line
end_line
```

When present, they follow the same section identity, ordering and evidence rules.

Rules:

- section IDs are unique within one scenario;
- order follows the scenario definition;
- missing required end markers cause scenario failure or error according to evidence reliability;
- marker text is not inferred from localized UI wording.

---

## 29. ScenarioAssertionResult

```python
@dataclass(frozen=True, slots=True)
class ScenarioAssertionResult:
    assertion_id: str
    assertion_kind: str
    status: str
    message: str
    evidence_path: Path | None
    section_id: str | None
```

Rules:

- `assertion_id` is unique within the scenario;
- assertion order follows the scenario specification;
- status uses `passed`, `failed`, `error` or `skipped`;
- `evidence_path` belongs to the run when present;
- `section_id` references a known section when present;
- optional assertion behavior is explicit;
- assertions MUST NOT disappear silently from aggregation.

---

## 30. ArtifactRecord

`ArtifactRecord` represents one finalized or catalogued run artifact.

```python
@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    path: Path
    role: str
    media_type: str
    required: bool
    size_bytes: int
    sha256: str
    created_by: str
```

Canonical roles include:

```text
machine_summary
human_summary
ai_handoff
top_errors
master_log
aggregate_log
scan_log
compile_stdout
compile_stderr
scenario_stdout
scenario_stderr
scenario_output
gold_diff
detail
gfo
pgf
tool_output
migration_record
other
```

### 30.1 Invariants

- persisted path is run-relative;
- paths are unique;
- directories are not artifact entries;
- `size_bytes` is non-negative;
- `sha256` is the full lowercase hash of finalized bytes;
- `required` is explicit;
- `created_by` identifies the framework component or external producer boundary;
- the canonical manifest excludes itself;
- a required missing artifact invalidates verification;
- artifact records do not grant a consumer permission to rewrite the artifact.

Optional compatible fields may include:

```text
stage
contract_id
source_artifact
producer
```

They require coordinated schema review before persistence.

---

## 31. FileResult

`FileResult` represents validation of one selected GF source file.

```python
@dataclass(slots=True)
class FileResult:
    file_path: Path
    module_name: str

    status: Status
    diagnostic_class: DiagnosticClass
    is_direct: bool
    blocked_by: list[str]

    scan_counts: ScanCounts
    fingerprint: SourceFingerprint
    compile_summary: CompileSummary
    scan_log_path: Path | None

    artifacts: list[ArtifactRecord] = field(default_factory=list)

    @property
    def error_kind(self) -> ErrorKind:
        return self.compile_summary.error_kind

    @property
    def primary_message(self) -> str:
        return self.compile_summary.first_error
```

### 31.1 Identity

Runtime identity:

```text
resolved source Path
```

Persisted identity:

```text
normalized project-relative path using /
```

Example:

```text
lib/src/example/GrammarEx.gf
```

### 31.2 Invariants

- `module_name` matches intended GF module identity;
- `status` uses the shared validation enum;
- `diagnostic_class` uses the shared causal enum;
- `is_direct == (diagnostic_class == direct)`;
- downstream results identify blockers when known;
- blocker paths are normalized and unique;
- scan counts remain separate from compile truth;
- fingerprint corresponds to the compiled or observed source bytes;
- raw stdout and stderr remain separate;
- `status = OK` requires successful required compile evidence unless compilation was intentionally omitted by mode;
- a timeout yields `status = ERROR`;
- no report mutates classification fields.

### 31.3 Compatibility

`is_direct` is a compatibility field.

It is derived, not independent.

Removing it requires a major schema version after all supported readers use `diagnostic_class`.

---

## 32. ScenarioResult

`ScenarioResult` represents one registered native `.gfs` scenario.

```python
@dataclass(slots=True)
class ScenarioResult:
    scenario_id: str
    script_path: Path
    required: bool

    status: Status
    diagnostic_class: DiagnosticClass
    error_kind: ErrorKind
    primary_message: str
    blocked_by: list[str]

    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    execution_state: ExecutionState
    timed_out: bool
    duration_ms: int

    stdout_path: Path | None
    stderr_path: Path | None
    normalized_output_path: Path | None

    gold_path: Path | None
    gold_match: bool | None
    gold_diff_path: Path | None

    sections: list[ScenarioSectionResult]
    assertions: list[ScenarioAssertionResult]
    artifacts: list[ArtifactRecord]
```

### 32.1 Identity

Canonical identity:

```text
scenario_id
```

The script path supports evidence and configuration validation.

It does not replace the stable scenario ID.

### 32.2 Path classes

Persisted project-relative:

```text
script_path
gold_path
```

Persisted run-relative:

```text
stdout_path
stderr_path
normalized_output_path
gold_diff_path
artifact paths
```

Environment path:

```text
working_directory
```

### 32.3 Invariants

- `scenario_id` matches resolved project configuration;
- `required` matches project policy;
- command order is preserved;
- `duration_ms` is non-negative;
- `timed_out` agrees with execution state;
- stdout and stderr reference captured evidence;
- normalized output exists when normalization succeeded;
- `gold_match = None` when no comparison applies;
- normal validation MUST NOT rewrite a gold file;
- section IDs are unique;
- assertion IDs are unique;
- a missing required marker prevents `OK`;
- a required gold mismatch is `FAIL`, normally with `error_kind = OTHER`;
- a missing required gold is a configuration or release-blocking error;
- scenario artifacts remain contained under owned paths;
- downstream scenario results identify stable prerequisite identities.

### 32.4 Why ScenarioResult differs from FileResult

A file result combines:

```text
scan
fingerprint
compile
classification
```

A scenario result combines:

```text
process
markers
assertions
normalization
gold comparison
artifacts
classification
```

Forced identical storage would hide domain-specific evidence.

The models share status semantics, not an artificial identical field layout.

---

## 33. DiffEntry

```python
@dataclass(frozen=True, slots=True)
class DiffEntry:
    subject_kind: str
    subject_id: str
    previous_status: str
    current_status: str
    change_kind: ChangeKind
    message: str
```

Canonical subject kinds:

```text
file
scenario
run
```

Identity rules:

```text
file
    → normalized project-relative path

scenario
    → scenario ID

run
    → stable run-level criterion identity
```

Invariants:

- identity is `subject_kind + subject_id`;
- status values are canonical for the subject;
- message is bounded;
- ordering is deterministic;
- a missing compatible baseline produces an empty diff, not invented changes;
- legacy `file_path` migrates to `subject_kind=file`.

---

## 34. TopError

```python
@dataclass(frozen=True, slots=True)
class TopError:
    error_kind: ErrorKind
    message: str
    count: int
    subject_kinds: tuple[str, ...] = ()
```

Persisted schema `1.0` requires at least:

```text
error_kind
message
count
```

Rules:

- empty messages are excluded;
- count is a positive integer;
- aggregation key includes error kind and normalized message;
- unrelated technical classes are not merged;
- ordering is descending count, then error kind, then case-insensitive message;
- legacy message-to-count objects may be read through migration;
- canonical writers emit an array of records.

---

## 35. RunTotals

Canonical persisted totals:

```python
@dataclass(frozen=True, slots=True)
class RunTotals:
    files_seen: int
    files_included: int
    files_excluded: int

    files_ok: int
    files_fail: int
    files_error: int
    files_skipped: int

    direct_fail: int
    downstream_fail: int
    ambiguous_fail: int
    excluded_noise: int

    scenarios_seen: int
    scenarios_ok: int
    scenarios_fail: int
    scenarios_error: int
    scenarios_skipped: int
    required_scenario_fail: int

    overall_status: Status
```

### 35.1 Count invariants

All values are non-negative integers.

```text
files_included =
    files_ok
  + files_fail
  + files_error
  + files_skipped
```

```text
scenarios_seen =
    scenarios_ok
  + scenarios_fail
  + scenarios_error
  + scenarios_skipped
```

Causal counts apply to failed or errored subjects according to documented aggregation policy.

`excluded_noise` does not count as an included successful file.

### 35.2 Authority

Totals are derived from result collections and selection evidence.

They MUST NOT become an independent manually edited source of truth.

Before finalization, the serializer or result builder MUST verify equations.

A count inconsistency makes the run unreliable and therefore `ERROR`.

---

## 36. RunResult

`RunResult` is the aggregate structured result for one run.

```python
@dataclass(slots=True)
class RunResult:
    run_config: RunConfig
    run_paths: RunPaths

    started_at: datetime
    finished_at: datetime
    duration_ms: int

    gf_version: str
    overall_status: Status

    file_results: list[FileResult]
    scenario_results: list[ScenarioResult]
    diff_entries: list[DiffEntry]
    top_errors: list[TopError]

    totals: RunTotals
```

Optional runtime additions may include:

```text
errors: list[ErrorInfo]
artifacts: list[ArtifactRecord]
release_gate_results
compatibility_warnings
```

Such fields require a defined owner and serializer policy before becoming persisted.

### 36.1 Invariants

- timestamps are timezone-aware;
- canonical persistence uses UTC;
- `finished_at >= started_at`;
- `duration_ms` is non-negative;
- `gf_version` comes from interpreted evidence, not the executable filename;
- file and scenario collections remain separate;
- file results are ordered by normalized project-relative path;
- scenario results follow resolved project scenario order;
- diff entries follow deterministic change severity order;
- top errors follow deterministic count ordering;
- totals agree with collections;
- `overall_status == totals.overall_status`;
- required result precedence is `ERROR > FAIL > OK`;
- report writers consume this result without rerunning stages.

### 36.2 Finalization

A run may be assembled progressively.

Before it is finalized:

1. all executed stages have terminal results;
2. required raw evidence is closed;
3. cross-file classification is complete;
4. totals are recomputed;
5. overall status is derived;
6. reports are written from structured data;
7. required artifacts are verified;
8. the manifest is generated from finalized bytes;
9. final paths and status are no longer mutated.

---

## 37. Persisted run-summary projection

`RunResult` projects into:

```text
run_<run-id>/summary.json
schema_id = gf-wordbench.run-summary
schema_version = 1.0
```

Canonical root structure:

```json
{
  "schema_id": "gf-wordbench.run-summary",
  "schema_version": "1.0",
  "producer": {},
  "metadata": {},
  "totals": {},
  "artifacts": {},
  "file_results": [],
  "scenario_results": [],
  "diff_entries": [],
  "top_errors": []
}
```

Required arrays use `[]` when empty.

Required objects MUST NOT be replaced by `null`.

### 37.1 Projection map

| Runtime source | Persisted destination |
|---|---|
| `ProducerInfo` | `producer` |
| `RunPaths.run_id` and run timing | `metadata` |
| `RunConfig` effective values | `metadata` |
| `RunTotals` | `totals` |
| `RunPaths` stable artifact locations | `artifacts` |
| `FileResult[]` | `file_results` |
| `ScenarioResult[]` | `scenario_results` |
| `DiffEntry[]` | `diff_entries` |
| `TopError[]` | `top_errors` |

### 37.2 Metadata fields

Canonical metadata includes:

```text
run_id
run_dir
started_at
finished_at
duration_ms
gf_version
mode
target_file
project_id
project_name
project_root
rgl_root
gf_executable
output_root
source_directory
source_glob
gf_path
timeout_sec
max_files
skip_version_probe
no_compile
emit_cpu_stats
keep_ok_details
diff_previous
```

Path bases remain explicit.

### 37.3 Artifact-path projection

Run-owned paths are run-relative:

```json
{
  "summary_json": "summary.json",
  "summary_markdown": "summary.md",
  "ai_ready": "AI_READY.md",
  "top_errors": "top_errors.txt",
  "manifest": "manifest.json",
  "master_log": "raw/master.log",
  "all_scan_logs": "raw/ALL_SCAN_LOGS.TXT",
  "all_logs": "raw/ALL_LOGS.TXT",
  "details_dir": "details",
  "raw_dir": "raw",
  "compile_logs_dir": "raw/compile",
  "scan_logs_dir": "raw/scan",
  "scenario_logs_dir": "raw/scenarios",
  "artifacts_dir": "artifacts",
  "gfo_dir": "artifacts/gfo",
  "out_dir": "artifacts/out",
  "pgf_dir": "artifacts/pgf"
}
```

Readers MUST NOT reconstruct a path when the schema supplies it.

---

## 38. Persisted artifact-manifest projection

Artifact records project into:

```text
run_<run-id>/manifest.json
schema_id = gf-wordbench.artifact-manifest
schema_version = 1.0
```

Canonical root structure:

```json
{
  "schema_id": "gf-wordbench.artifact-manifest",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "1.0.0"
  },
  "run_id": "20260723_120000",
  "generated_at": "2026-07-23T16:00:00Z",
  "hash_algorithm": "sha256",
  "artifacts": []
}
```

Manifest rules:

- paths are unique and run-relative;
- directories are not entries;
- artifacts are sorted deterministically;
- hashes use finalized bytes;
- the manifest excludes itself;
- required summary artifacts appear;
- missing required artifacts fail verification;
- symlinks should be rejected in strict mode;
- paths escaping the run root are prohibited.

---

## 39. Path model

Every path field belongs to one explicit class.

### 39.1 Project-relative paths

Examples:

```text
ProjectConfig.sources.directory
FileResult.file_path
ScenarioResult.script_path
ScenarioResult.gold_path
DiffEntry file subject_id
```

Persisted rules:

- `/` separators;
- no drive letter;
- no unresolved `..`;
- no environment interpolation;
- normalized against the project root;
- stable across machines when the project layout is unchanged.

### 39.2 Run-relative paths

Examples:

```text
compile stdout
compile stderr
scan log
scenario stdout
scenario stderr
normalized scenario output
gold diff
manifest artifact path
detail files
```

Persisted rules:

- relative to `run_dir`;
- `/` separators;
- remain contained in the run;
- no absolute fallback;
- no reconstruction by consumer convention.

### 39.3 Environment paths

Examples:

```text
project_root
rgl_root
gf_executable
output_root
run_dir
scenario working_directory
effective gf_path entries
```

Rules:

- may be absolute;
- normalized before entering `RunConfig`;
- canonical serialization uses `/`;
- state values are revalidated before use;
- secrets and unrelated environment values are not recorded.

### 39.4 Internal Path type

Runtime path fields SHOULD use `pathlib.Path`.

Persisted path fields use strings.

A serializer MUST NOT emit Python `Path` repr.

---

## 40. Null, empty and default rules

### 40.1 Required collections

Required collections use empty collections, not `None`:

```text
file_results = []
scenario_results = []
diff_entries = []
top_errors = []
blocked_by = []
sections = []
assertions = []
artifacts = []
```

### 40.2 Optional scalar values

Use `None` when absence is semantically different from an empty value.

Examples:

```text
exit_code
target
gold_path
gold_match
normalized_output_path
gold_diff_path
cause_type
```

### 40.3 Empty strings

Empty strings are permitted only when the schema explicitly defines them.

Examples:

```text
application state target_file
application state status_message
project minimum_version
bounded optional diagnostic detail
```

Canonical run summary normally uses `null`, not `""`, for an absent target or optional path.

### 40.4 Safe defaults

A safe default may apply only when:

- the field is genuinely optional;
- the default does not hide missing required project policy;
- the default does not weaken release validation;
- the default is documented;
- serialization remains deterministic.

No fake evidence object is a safe default.

Prohibited examples:

```python
SourceFingerprint(size_bytes=0, hash_algorithm="sha256", hash="")
CompileSummary(exit_code=0, error_kind=ErrorKind.OK, ...)
```

when the operation did not occur.

---

## 41. Ordering rules

Canonical ordering is part of deterministic behavior.

```text
ProjectConfig path_parts
    → declared effective order

ProjectConfig entrypoints/checkpoints
    → project-declared order

RunConfig selected scenarios
    → resolved scenario-registry order

FileResult[]
    → normalized project-relative file path

ScenarioResult[]
    → resolved execution order

blocked_by
    → stable normalized identity order

DiffEntry[]
    → regressed, new, improved, removed, unchanged
    → then subject identity

TopError[]
    → descending count
    → error kind
    → case-insensitive message

ArtifactRecord[]
    → normalized run-relative path
```

A set may be used internally only when converted back to deterministic order before crossing a boundary.

---

## 42. Status aggregation invariants

### 42.1 File aggregation

File status reflects required file-validation evidence.

Static findings do not automatically force compile failure.

Typical mapping:

```text
compile and required artifact checks pass
    → OK

GF completes and reports a grammar criterion failure
    → FAIL

launch, timeout, required I/O or interpretation failure
    → ERROR

compile intentionally omitted by valid plan
    → SKIPPED for the compile criterion
```

### 42.2 Scenario aggregation

```text
process or framework reliability failure
    → ERROR

marker, required assertion or gold mismatch after reliable execution
    → FAIL

all required gates pass
    → OK

optional scenario not selected
    → SKIPPED
```

### 42.3 Run aggregation

Only required subjects determine ordinary `FAIL`.

Any required `ERROR` makes the overall run `ERROR`.

Optional errors affect overall status only when they also invalidate shared run reliability or project policy declares them blocking.

### 42.4 Required artifact effect

A process exit code of zero is insufficient when an expected artifact is required.

Missing required artifact result:

- `FAIL` when execution and interpretation are reliable and the artifact criterion clearly failed;
- `ERROR` when evidence reliability or artifact verification cannot be established.

---

## 43. Error propagation

Models preserve both:

```text
validation conclusion
execution facts
```

A stage converts expected subject-level failures into structured results.

Unexpected exceptions cross stage boundaries as structured `ErrorInfo` or controlled exceptions with preserved cause.

Rules:

- exceptions are not converted to `OK`;
- exceptions are not silently swallowed;
- raw evidence already written is preserved;
- one file failure does not automatically stop independent file validation;
- required stage errors remain visible at run level;
- cancellation stops new work and preserves partial evidence;
- report generation does not repair missing evidence.

---

## 44. Runtime versus persisted fields

Runtime models may include operational fields that are not persisted.

Examples:

```text
resolved Path objects
open handles
cancellation token
in-memory cache
load warnings
source parser object
temporary staging path
```

Persisted schemas may flatten or normalize runtime composition.

Examples:

- `ScenarioResult` runtime process fields may serialize directly inside one scenario object.
- `RunConfig` fields serialize into `metadata`.
- `RunPaths` serialize into the `artifacts` path map.
- `ArtifactRecord.path` serializes as run-relative text.
- enums serialize as canonical strings.

Runtime and persisted shapes do not need to be identical.

Their meanings MUST remain compatible.

---

## 45. Compatibility and migration

### 45.1 Compatible changes

Normally compatible:

- adding an optional field with a safe documented default;
- adding an optional artifact role;
- adding an optional report field ignored by older readers;
- adding a new model used only internally;
- adding an enum value only when readers are explicitly forward-compatible and the schema policy permits it.

### 45.2 Breaking changes

Breaking changes include:

- renaming or removing a persisted required field;
- changing a field type;
- changing path base semantics;
- changing status meaning;
- merging separate status dimensions;
- changing list identity or ordering rules;
- changing nullability of required fields;
- replacing an array with an object;
- changing the meaning of an existing scan counter;
- changing fingerprint algorithm without schema versioning.

### 45.3 Legacy aliases

Legacy aliases are handled at readers or migrators.

They do not remain canonical runtime fields after normalization.

Examples:

```text
mode=file
    → quick

mode=all
    → diagnostic

DiffEntry.file_path
    → subject_kind=file
    → subject_id=file_path

fingerprint.sha1_short
    → imported legacy fingerprint metadata

ai_brief_path
    → artifacts.ai_ready
```

### 45.4 Migration requirements

A migration MUST be:

```text
explicit
version-aware
idempotent
non-destructive
tested
traceable
```

It MUST report loss or uncertainty.

Read-only loading MUST NOT overwrite the legacy source automatically.

---

## 46. Serialization requirements

Canonical JSON writers use:

```text
UTF-8 without BOM
valid JSON
one object at root
Unicode-preserving output
stable indentation
LF newlines
final newline
```

Prohibited JSON values:

```text
comments
JSON5
NaN
Infinity
Python repr
Path objects
datetime objects
enum objects
```

Conversions:

| Runtime value | Persisted value |
|---|---|
| `Path` | normalized string |
| aware `datetime` | UTC RFC 3339 string |
| enum | canonical string |
| tuple | ordered array |
| absent optional | `null` |
| boolean | JSON boolean |
| integer | JSON integer |

Canonical TOML writers and readers follow the project schema authority.

---

## 47. Security rules

Models and serializers MUST NOT contain:

```text
credentials
tokens
complete environment dumps
secret file contents
unbounded tracebacks in standard reports
arbitrary executable shell strings
unvalidated path traversal
```

Path-bearing models MUST enforce:

```text
root containment
no unresolved ..
no NUL
safe generated names
symlink or junction policy
source/output separation
```

A persisted manifest hash proves integrity against accidental change.

It is not a digital signature.

---

## 48. Ownership map

| Model | Primary owner | Main consumers |
|---|---|---|
| `AppConfig` | `app/config.py` | bootstrap |
| `ProjectConfig` | `app/project_config.py` | bootstrap, validation planning |
| `AppState` | `app/state.py` and state schema | GUI, bootstrap |
| `ResolvedEnvironment` | bootstrap/path resolution | configuration builder |
| `RunConfig` | bootstrap/configuration builder | audit core and stages |
| `RunPaths` | bootstrap/run-path builder | all writers and orchestrator |
| `ProcessResult` | process utility | compiler, scenario runner |
| `ScanCounts` | scanner | result builder, reports |
| `SourceFingerprint` | fingerprint provider | result builder, reports |
| `CompileSummary` | compiler | file result builder |
| `FileResult` | result builder/orchestrator | classifier, diff, reports |
| `ScenarioResult` | scenario runner/result builder | release gates, reports |
| `DiffEntry` | previous-run diff | reports |
| `TopError` | aggregation | reports |
| `ArtifactRecord` | artifact producer/cataloguer | manifest writer, verifier |
| `RunTotals` | result aggregation | reports, release decision |
| `RunResult` | audit core/result builder | all report writers |

A consumer may read a model.

It MUST NOT redefine the model’s field meanings locally.

---

## 49. Prohibited model patterns

### 49.1 Universal result dictionary

Prohibited:

```python
result: dict[str, object]
```

with keys varying by stage.

Use typed subject models.

### 49.2 Universal result dataclass with mostly optional fields

Prohibited:

```python
class Result:
    file_path: Path | None
    scenario_id: str | None
    scan_counts: ScanCounts | None
    gold_match: bool | None
    ...
```

when the object cannot enforce domain invariants.

Use `FileResult` and `ScenarioResult`.

### 49.3 Duplicate writable error fields

Prohibited:

```text
FileResult.error_kind
FileResult.compile_summary.error_kind
```

as independent writable facts.

Use a derived property when needed.

### 49.4 Report parsing

Prohibited:

```text
summary.md → parsed to reconstruct RunResult
AI_READY.md → parsed to reconstruct errors
```

Structured JSON and runtime models are authoritative.

### 49.5 Path reconstruction

Prohibited:

```python
summary_path.with_name("manifest.json")
```

when `RunPaths.manifest_json` or persisted `artifacts.manifest` exists.

### 49.6 Fake successful evidence

Prohibited:

- zero exit code when no process completed;
- empty hash represented as a valid fingerprint;
- missing log represented by an empty path that reports interpret as success;
- missing required scenario represented as `SKIPPED`;
- missing gold automatically created during normal validation.

### 49.7 Status collapse

Prohibited:

```text
execution_state stored in status
error_kind stored in diagnostic_class
diagnostic_class stored in error_kind
```

---

## 50. Required unit tests

### 50.1 Enum tests

```text
canonical values
case sensitivity
legacy alias rejection by canonical writers
invalid cross-dimension value
```

### 50.2 Configuration-model tests

```text
project required fields
project-relative path resolution
duplicate scenario ID
entrypoint uniqueness
finite timeout
release constraint protection
CLI and GUI parity
no late environment reads
```

### 50.3 Path-model tests

```text
all RunPaths below run_dir
project-relative serialization
run-relative serialization
Windows separator normalization
drive-letter rejection for portable paths
path traversal rejection
symlink/junction containment policy
```

### 50.4 Process-model tests

```text
completed with exit code
timeout with no exit code
launch failure
cancellation
stdout/stderr separation
non-negative duration
```

### 50.5 File-result tests

```text
OK compile
TYPE failure
SYNTAX failure
timeout ERROR
downstream blocker
ambiguous result
scan findings with compile OK
fingerprint SHA-256
invalid is_direct mismatch
```

### 50.6 Scenario-result tests

```text
required scenario OK
marker failure
assertion failure
gold match
gold mismatch
missing required gold
timeout
optional skipped
downstream entrypoint blocker
unique sections and assertions
```

### 50.7 Run-result tests

```text
empty valid collections
file count equations
scenario count equations
overall ERROR precedence
overall FAIL precedence
deterministic ordering
timestamp validation
report writers do not mutate result
```

### 50.8 Serialization tests

```text
summary round trip
manifest round trip
Unicode
UTC timestamps
null versus empty
unknown optional field
unsupported major version
deterministic key and list order
legacy migration
no Path or enum repr leakage
```

---

## 51. Required contract tests

Contract tests MUST verify:

- CLI and GUI produce equivalent `RunConfig` for equivalent inputs;
- audit core accepts canonical `RunConfig`;
- run-path builder returns contained `RunPaths`;
- scanner returns `ScanCounts` and a valid owned log path;
- compiler returns a canonical `CompileSummary`;
- process runner does not assign validation status;
- file and scenario collections remain separate;
- report writers consume `RunResult`;
- report writers do not execute GF;
- `summary.json` matches the persisted schema;
- manifest entries match finalized bytes;
- required artifact paths agree between summary and manifest;
- canonical writers emit only canonical enums;
- active-language values do not appear in framework defaults;
- migrations normalize legacy shapes without rewriting sources during read-only load.

The exact command surface for contract and schema verification is owned by `docs/usage/CLI_REFERENCE.md`. This data-model contract does not define competing command names.

---

## 52. Change workflow

Before changing a shared model:

1. identify the model owner;
2. identify all consumers;
3. classify the change as internal, compatible or breaking;
4. review status and path semantics;
5. update this document;
6. update the interfile contract lock;
7. update the persisted schema lock when serialization changes;
8. update all serializers and readers;
9. update migrations;
10. update fixtures and tests;
11. regenerate representative reports;
12. verify deterministic round trips;
13. record an ADR for a significant architectural change.

A model change is incomplete when one consumer still depends on the old field meaning.

---

## 53. Review checklist

```text
[ ] Model has one coherent responsibility
[ ] Owner is identified
[ ] Consumers are identified
[ ] Field types are explicit
[ ] Mutable defaults are safe
[ ] Runtime and persisted fields are distinguished
[ ] Path bases are explicit
[ ] Status dimensions remain separate
[ ] Nullability is documented
[ ] Ordering is deterministic
[ ] Derived fields have one source of truth
[ ] Error evidence is preserved
[ ] No secret-bearing fields are added
[ ] Serialization is centralized
[ ] Persisted schema impact is reviewed
[ ] Migration impact is reviewed
[ ] Contract tests are updated
[ ] Reports do not reconstruct or rerun work
```

---

## 54. Related documents

### Normative schema and contract locks

```text
docs/PERSISTED_SCHEMA_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

### Architecture

```text
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
```

### Configuration

```text
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
```

### Validation and GF

```text
docs/validation/STATIC_SCANNING.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/VALIDATION_PIPELINE.md
docs/gf/GF_COMPILATION.md
```

### Reports and artifacts

```text
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/reports/REPORTING_OVERVIEW.md
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
```

### References

```text
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/reference/SCHEMA_INDEX.md
docs/reference/TERMINOLOGY_REFERENCE.md
```

### Decisions

```text
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0003-SEPARATE-SCAN-AND-COMPILE.md
docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
```

---

## 55. Contract enforcement rule

GF Wordbench may change internal implementation details without changing this contract.

It may not silently change:

```text
shared model identity
public field meaning
status vocabulary
path base
required evidence
result ownership
serialization shape
ordering identity
aggregation precedence
migration behavior
```

The governing rule is:

> Configuration is resolved once, evidence is captured once, structured results are assembled once, and every report derives from those same typed facts.
