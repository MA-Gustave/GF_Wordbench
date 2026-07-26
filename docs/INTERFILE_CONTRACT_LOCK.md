# GF Wordbench — Interfile Contract Lock

**Document ID:** `GF-WB-ARCH-INTERFILE-LOCK`  
**Status:** Normative  
**Contract version:** `3.0.0`  
**Applies to:** GF Wordbench framework, active-project boundary, project template, persisted state and public artifact boundary  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**File-placement authority:** `docs/architecture/CANONICAL_FILE_ARCHITECTURE.md`  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose and authority

This lock prevents drift between Python files, public symbols, ports, adapters, persisted state and repository-owned artifacts.

It owns:

- the single owner of every cross-file Python contract;
- canonical import and re-export paths;
- provider-consumer relationships;
- allowed dependency direction;
- public facade boundaries;
- package-initializer behavior;
- coordination rules for contract changes.

It does not duplicate behavioral specifications. Status values, schemas, process semantics, project semantics and artifact formats remain governed by their specialized owner documents.

When rules overlap, authority is applied in this order:

1. accepted ADRs;
2. `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`;
3. `docs/PERSISTED_SCHEMA_LOCK.md` for persisted shapes and migrations;
4. `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` for external process and GF boundaries;
5. this file for Python ownership, imports, re-exports and provider-consumer contracts;
6. specialized owner documents for domain behavior;
7. implementation details.

The canonical architecture document MUST exist at:

```text
docs/architecture/CANONICAL_FILE_ARCHITECTURE.md
```

`docs/GF_WORDBENCH_CANONICAL_FILE_ARCHITECTURE.md` is a legacy misplaced path and MUST NOT remain as a competing authority after migration.

---

## 2. Contract vocabulary

- **OWNER**: the only module authorized to define a contract symbol or mutate an owned artifact.
- **PROVIDER**: a module exposing an owned contract to consumers.
- **CONSUMER**: a module importing or receiving that contract.
- **PUBLIC SYMBOL**: a symbol listed in the owner module's `__all__` or explicitly registered here.
- **FACADE**: a module that re-exports owned symbols without redefining them.
- **ADAPTER**: a concrete mechanism implementing a port.
- **DOMAIN MODEL**: an immutable typed value whose meaning is independent of filesystem, process, GUI and serialization libraries.
- **COMPATIBILITY ALIAS**: a temporary, documented migration name. It is never a second owner.

A public symbol has exactly one owner. Re-exporting does not transfer ownership.

---

## 3. Product and architectural invariants

1. One Wordbench workspace contains exactly one active project at `project/`.
2. One run resolves one active project identity and one normative language target.
3. GF Wordbench is one deployable hexagonal modular monolith.
4. `gf-portfolio` may consume finalized public artifacts; GF Wordbench MUST NOT import or require Portfolio code, state, configuration or storage.
5. Static scan and GF execution remain separate stages.
6. Process execution is shell-free and reachable only through the process boundary.
7. Raw evidence is preserved before parsing, normalization or diagnosis.
8. Reports consume finalized typed results and never execute validation or GF.
9. Application state is local, disposable and never authoritative for project identity.
10. Domain policy remains independent of concrete filesystem, TOML, JSON, subprocess, UI and GF implementations.
11. Persisted writers emit explicit schema identity and version and write atomically.
12. Future schema versions fail closed unless an explicit compatibility policy allows otherwise.

---

## 4. Python ownership and import rules

### 4.1 General rules

- Cross-file consumers MUST import a symbol from its owner or an explicitly registered facade.
- A module MUST NOT redefine a symbol owned by another module, even with an identical shape.
- Private names beginning with `_` MUST NOT become cross-file dependencies.
- `TYPE_CHECKING` imports do not bypass ownership rules.
- Import-time filesystem access, environment resolution, logging configuration, process launch and state mutation are forbidden.
- Expected operational failures return structured results when a reliable result can be constructed. Exceptions are reserved for invalid requests, contract violations and failures that prevent reliable result construction.
- Public dataclasses are frozen and slotted unless mutability is intrinsic to the contract and explicitly stated here.
- Collection fields crossing module boundaries use deterministic immutable forms: tuples, frozensets or read-only mappings.

### 4.2 Allowed dependency direction

```text
entrypoints -> application/use cases -> domain models + ports
bootstrap   -> use cases + ports + adapters
adapters    -> ports + infrastructure + external systems
reporting   -> finalized results + artifact readers
```

Foundation-package direction:

```text
kernel
  ^
  ├── config
  ├── infrastructure
  │     └── infrastructure.process
  ├── projects domain/ports
  │     └── projects adapters/use cases
  └── state models/schema/migrations
        └── state repository
```

Additional allowed edges:

- `config.models -> projects.models.ProjectConfig`;
- `projects` adapters -> `infrastructure` mechanisms;
- `state.repository -> infrastructure`, `kernel.errors`, `version`;
- application/bootstrap modules added later -> public module facades and ports.

Forbidden edges include:

- `kernel -> config|infrastructure|projects|state|entrypoints`;
- domain models or policies -> concrete adapters;
- `projects.models|projects.policies|projects.ports -> infrastructure`;
- `state.models|state.schema|state.migrations -> state.repository`;
- `infrastructure -> projects|state|entrypoints`;
- any runtime package -> `gf-portfolio`;
- one adapter importing another adapter's private helper;
- package initializers importing broad implementation graphs.

---

## 5. Package initializer and facade rules

| Module | Locked behavior |
|---|---|
| `gf_wordbench.__init__` | Re-exports only `__version__`. |
| `kernel.__init__` | Empty public API; no eager imports. |
| `config.__init__` | Empty public API; no eager imports. |
| `infrastructure.__init__` | Empty public API; no eager imports. |
| `projects.__init__` | Empty public API; cross-module use cases enter through `projects.public`. |
| `state.__init__` | Empty public API; no eager imports. |
| `infrastructure.process.__init__` | Narrow process facade defined in §9.7. |
| `projects.public` | Narrow project facade defined in §10.13. |

A package initializer MUST NOT perform I/O, resolve configuration, instantiate adapters or hide a dependency cycle.

---

## 6. Canonical foundation file registry

This section locks the responsibility of the first 51 implementation files. Public symbol registries in §§7–11 are authoritative when a row contains only a responsibility summary.

### 6.1 Repository and package root

| Path | Responsibility |
|---|---|
| `pyproject.toml` | Build metadata, Python requirement, dependencies, entry points and tool configuration. |
| `src/gf_wordbench/version.py` | Sole package-version constant owner. |
| `src/gf_wordbench/__init__.py` | Root package facade for `__version__` only. |
| `src/gf_wordbench/py.typed` | PEP 561 marker; empty file. |

### 6.2 Kernel

| Path | Responsibility |
|---|---|
| `kernel/errors.py` | Canonical exception hierarchy and structured `ErrorInfo`. |
| `kernel/events.py` | Delivery-neutral progress and lifecycle event contracts. |
| `kernel/ids.py` | Stable identifier types and lexical validators. |
| `kernel/paths.py` | Pure portable-path normalization, identity and lexical containment. |
| `kernel/serialization.py` | Shared producer metadata and pure canonical-value serialization. |
| `kernel/statuses.py` | Shared cross-module enum vocabularies. |
| `kernel/__init__.py` | Side-effect-free empty package API. |

### 6.3 Configuration

| Path | Responsibility |
|---|---|
| `config/models.py` | Immutable configuration inputs, outputs, diagnostics and resolution models. |
| `config/defaults.py` | Framework defaults and supported schema-major constants only. |
| `config/environment.py` | Documented environment-variable reading and machine-local environment resolution. |
| `config/precedence.py` | Pure field-specific source authority and precedence resolution. |
| `config/resolver.py` | Composition of defaults, explicit input, project facts, state hints and environment into one `RunConfig`. |
| `config/__init__.py` | Side-effect-free empty package API. |

### 6.4 Infrastructure

| Path | Responsibility |
|---|---|
| `infrastructure/atomic_io.py` | Atomic sibling-file replacement primitives. |
| `infrastructure/environment.py` | Controlled child-process environment construction and redaction. |
| `infrastructure/filesystem.py` | Bounded concrete filesystem mechanisms. |
| `infrastructure/json_io.py` | Strict JSON parsing, formatting and atomic writing. |
| `infrastructure/logging.py` | Runtime logging configuration and secret redaction. |
| `infrastructure/time.py` | System clock adapter. |
| `infrastructure/toml_io.py` | Generic strict TOML reading and canonical rendering. |
| `infrastructure/__init__.py` | Side-effect-free empty package API. |

### 6.5 Process infrastructure

| Path | Responsibility |
|---|---|
| `infrastructure/process/models.py` | Immutable process requests, results, events and artifact observations. |
| `infrastructure/process/requests.py` | Request validation and redacted command rendering. |
| `infrastructure/process/streams.py` | Concurrent bounded stdout/stderr capture. |
| `infrastructure/process/launcher.py` | Shell-free process creation only. |
| `infrastructure/process/termination.py` | Cancellation token, containment and owned-process termination. |
| `infrastructure/process/runner.py` | End-to-end process attempt orchestration. |
| `infrastructure/process/__init__.py` | Narrow public process facade. |

### 6.6 Projects

| Path | Responsibility |
|---|---|
| `projects/models.py` | Project configuration, project diagnostics and validation-result models. |
| `projects/paths.py` | Pure project-relative and resolved project-path construction. |
| `projects/policies.py` | Pure project invariants, naming, placeholder and semantic policies. |
| `projects/ports.py` | Project-owned filesystem, TOML, template, archive, clock and lifecycle ports. |
| `projects/schema.py` | Raw project-document shape, version compatibility and document-to-model parsing. |
| `projects/toml_adapter.py` | Project TOML decoding, deterministic rendering and atomic persistence. |
| `projects/filesystem_adapter.py` | Concrete implementation of project filesystem and lifecycle mechanisms. |
| `projects/loader.py` | Load one explicit active project. |
| `projects/validator.py` | Structural and semantic project validation. |
| `projects/initializer.py` | Template-to-active-project initialization. |
| `projects/resetter.py` | Explicit project reset planning and execution. |
| `projects/migrator.py` | Legacy-project migration planning and execution. |
| `projects/public.py` | Stable project use-case facade. |
| `projects/__init__.py` | Side-effect-free empty package API. |

### 6.7 State

| Path | Responsibility |
|---|---|
| `state/models.py` | Immutable local application-state and load-diagnostic models. |
| `state/schema.py` | App-state document shape, defaults, parsing, validation and serialization. |
| `state/migrations.py` | Explicit legacy-state migration only. |
| `state/repository.py` | Bounded state-file loading, recovery and atomic saving. |
| `state/__init__.py` | Side-effect-free empty package API. |

---

## 7. Kernel symbol registry

### 7.1 `kernel.serialization`

Canonical public symbols:

```text
ProducerInfo
CANONICAL_JSON_INDENT
JsonScalar
JsonValue
format_rfc3339_utc
path_to_portable_string
to_json_value
to_json_object
dumps_canonical_json
```

`ProducerInfo` is owned here because it is shared producer metadata, not configuration authority:

```python
@dataclass(frozen=True, slots=True)
class ProducerInfo:
    name: str
    version: str
```

Consumers MUST import it from `gf_wordbench.kernel.serialization`. `config.models` and `state.models` MUST NOT redefine or re-export it as owner symbols.

### 7.2 `kernel.statuses`

Canonical enum owners and exact values:

```text
ValidationStatus: OK, FAIL, ERROR, SKIPPED
OverallStatus: OK, FAIL, ERROR
ExecutionState: completed, timed_out, cancelled, launch_failed
DiagnosticClass: ok, direct, downstream, ambiguous, noise, skipped
ErrorKind: OK, OTHER, TYPE, SYNTAX, INTERNAL, TIMEOUT, SCRIPT, CONFIG, IO, TOOL
ChangeKind: unchanged, improved, regressed, new, removed
ValidationMode: quick, checkpoint, release, diagnostic
TargetKind: file, module, checkpoint, entrypoint, scenario, project, regression
```

Every enum is a separate contract dimension. Values MUST NOT be substituted across dimensions.

`ValidationMode` and `TargetKind` are owned here. They MUST NOT be defined in `config.models`, `validation`, entrypoints or state.

### 7.3 `kernel.errors`

Canonical public exceptions:

```text
GFWordbenchError
ConfigurationError
ProjectConfigurationError
UnsupportedVersionError
SchemaValidationError
ContractViolationError
InfrastructureError
PathSecurityError
EvidenceIOError
ProcessLaunchError
StateWriteError
StageExecutionError
ScanExecutionError
CompileExecutionError
ScenarioExecutionError
NormalizationError
ArtifactError
ReportError
MigrationError
CancellationRequested
ErrorInfo
```

`StateWriteError` is owned here and represents inability to publish a reliable application-state file. It derives from `InfrastructureError`.

Domain- or use-case-specific structured failure models remain with their owning module and are not exceptions merely because their names include `Error` or `Failure`.

### 7.4 Remaining kernel APIs

The following current public registries remain canonical:

- `kernel.events`: `EventScalar`, `EventField`, `EventFields`, `EventLevel`, `ProgressEvent`, `LifecycleEvent`, `EventSink`, `event_fields`;
- `kernel.ids`: identifier aliases and their `validate_*` functions;
- `kernel.paths`: `PathClass`, `ContainmentMode`, portable/environment path functions and lexical containment functions.

Kernel modules MUST remain free of project, state, process, UI and adapter imports.

---

## 8. Configuration contract

### 8.1 Model ownership

`config.models` owns:

```text
EvidenceLevel
IssueSeverity
EnvironmentOverrides
SelectionDefaults
OutputDefaults
SchemaSupport
AppConfig
ValidationTarget
ResolvedEnvironment
ConfigurationIssue
ConfigurationProvenance
ConfigurationResolutionRequest
EnvironmentResolution
ConfigurationResolution
RunConfig
```

Locked relationships:

- `AppConfig.producer` uses `kernel.serialization.ProducerInfo`.
- `ValidationTarget.kind` uses `kernel.statuses.TargetKind`.
- modes use `kernel.statuses.ValidationMode`.
- `RunConfig.project` uses `projects.models.ProjectConfig`.
- `ConfigurationResolution.configuration` is `RunConfig | None`; no competing `ResolvedConfiguration` model is permitted.
- `ConfigurationIssue` records severity, source, field path, provided value, message and remediation.
- `ConfigurationProvenance` records one effective field and its winning source.
- `EnvironmentOverrides` stores raw optional strings and performs no path expansion or discovery.
- `EnvironmentResolution` carries `ResolvedEnvironment | None`, issues and provenance.
- `ConfigurationResolution.require()` returns `RunConfig` or raises `ConfigurationError`.

### 8.2 Precedence ownership

`config.precedence` owns:

```text
ConfigurationSource
ConfigurationDomain
OverrideClass
PrecedencePolicy
PrecedenceValues
PrecedenceResolution
PRECEDENCE_POLICIES
policy_for
resolve_precedence
```

`ConfigurationSource` MUST be imported from `config.precedence`, never from `config.models`.

`resolve_precedence(request)` is pure. It selects explicit and default values, returns provenance and reports equal-tier conflicts. It performs no filesystem access, executable discovery or project loading.

### 8.3 Environment ownership

`config.environment` owns:

```text
ENVIRONMENT_PREFIX
PROJECT_ROOT_ENV
GF_EXECUTABLE_ENV
RGL_ROOT_ENV
OUTPUT_ROOT_ENV
STATE_PATH_ENV
CANONICAL_ENVIRONMENT_VARIABLES
read_environment
find_unknown_environment_variables
resolve_environment
```

```python
read_environment(environ: Mapping[str, str] | None = None) -> EnvironmentOverrides
resolve_environment(request: ConfigurationResolutionRequest) -> EnvironmentResolution
```

Raw environment reading preserves values. Expansion, normalization, existence checks and discovery occur only in `resolve_environment`.

### 8.4 Resolution ownership

`config.resolver` owns exactly:

```python
resolve_configuration(
    request: ConfigurationResolutionRequest,
) -> ConfigurationResolution

require_configuration(
    request: ConfigurationResolutionRequest,
) -> RunConfig
```

The resolver composes existing owners. It MUST NOT duplicate precedence tables, environment variable names, project parsing or project path rules.

### 8.5 Defaults

`config.defaults` owns only documented constants. It imports enum values but defines no enum, model, path resolution or environment behavior.

---

## 9. Process-execution contract

### 9.1 Process model ownership

`infrastructure.process.models` owns:

```text
StringMap
ProcessOperationKind
ProcessInputKind
ArtifactKind
CancellationReason
ProcessErrorKind
ProcessInput
ArtifactExpectation
ArtifactObservation
ProcessRequest
ProcessEvent
ProcessEventSink
ProcessResult
```

The process layer records execution facts only. Validation status, GF semantics, diagnostic classification and report serialization remain outside it.

`ProcessEventSink` is a callable/protocol accepting `ProcessEvent`. It MUST NOT be a GUI callback type.

### 9.2 Environment preparation

`infrastructure.environment` owns:

```text
EnvironmentMapping
PreparedEnvironment
CONTROLLED_INHERIT_V1
REDACTED_VALUE
build_child_environment
```

`PreparedEnvironment` contains the actual child mapping and separately recorded redacted overrides. `runner.py` consumes this object; it MUST NOT import nonexistent alternative helpers such as `build_process_environment` or `recorded_environment_overrides`.

### 9.3 Launch ownership

`infrastructure.process.launcher` owns:

```text
ProcessHandle
StandardInput
launch_without_shell
```

```python
launch_without_shell(...) -> ProcessHandle
```

Only this module calls `subprocess.Popen` or equivalent process-creation APIs. Shell execution is forbidden.

Launch-error classification is assembled by `runner.py` using structured exceptions and `ProcessErrorKind`; no second `normalize_launch_error` owner is introduced.

### 9.4 Stream-capture ownership

`infrastructure.process.streams` owns:

```text
CaptureFailure
StreamCaptureSummary
ProcessCapture
CaptureSession
open_capture_session
```

`ProcessCapture` is the immutable finalized stdout/stderr capture summary. `CaptureSession` is the runner-facing lifecycle contract. Concrete thread, buffer, reservation and sink helpers remain private.

### 9.5 Cancellation and termination ownership

`infrastructure.process.termination` owns:

```text
CancellationToken
ContainmentKind
ProcessContainment
TerminableProcess
TerminationOutcome
DEFAULT_FORCE_WAIT_SEC
DEFAULT_POLL_INTERVAL_SEC
terminate_owned_processes
```

Canonical cancellation interface:

```python
class CancellationToken(Protocol):
    def is_cancelled(self) -> bool: ...
    def reason(self) -> str | None: ...
```

`CancellationToken` MUST NOT be defined in `process.models`. The public process facade re-exports it from `termination`.

`terminate_owned_processes` terminates only the request-owned process or containment unit. A second `terminate_process_tree` contract MUST NOT coexist.

### 9.6 Runner ownership

`infrastructure.process.runner` owns:

```python
run_process(
    request: ProcessRequest,
    *,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
) -> ProcessResult
```

The runner MUST:

1. validate the request through `requests.validate_process_request`;
2. build a controlled environment through `build_child_environment`;
3. launch through `launch_without_shell`;
4. capture through `open_capture_session`;
5. poll timeout and cancellation;
6. terminate through `terminate_owned_processes` when required;
7. finalize capture and artifact observations;
8. return one immutable `ProcessResult` for every attempted request whenever possible.

### 9.7 Public process facade

`infrastructure.process.__init__` re-exports only:

```text
ArtifactExpectation
ArtifactObservation
CancellationToken
ProcessCapture
ProcessInput
ProcessRequest
ProcessResult
render_command_for_display
run_process
validate_process_request
```

Ownership remains:

- models: request/result/artifact/input types;
- streams: `ProcessCapture`;
- termination: `CancellationToken`;
- requests: validation and display rendering;
- runner: execution.

---

## 10. Active-project contract

### 10.1 Project model ownership

`projects.models` owns stable project-domain contracts:

```text
PROJECT_CONFIG_FILENAME
PROJECT_SCHEMA_ID
PROJECT_SCHEMA_VERSION
ProjectIdentity
SourceConfig
GFProjectConfig
ModuleTargets
ValidationPolicy
ProjectConfig
ProjectCheckScope
ProjectDiagnosticSeverity
ProjectDiagnostic
ProjectValidationResult
```

`ProjectValidationResult` is the single project-validation aggregate. `ProjectValidationReport` is not a separate canonical type.

Migration-, initialization- and reset-specific request/result models belong to their use-case modules, not to `projects.models`.

### 10.2 Project path ownership

`projects.paths` owns:

```text
ProjectPaths
PROJECT_ROOT_DECLARATION
PROJECT_CONFIG_FILENAME
PROJECT_README_FILENAME
PROJECT_DOCS_DIRECTORY
PROJECT_VALIDATION_DIRECTORY
PROJECT_SCENARIOS_DIRECTORY
PROJECT_INPUTS_DIRECTORY
PROJECT_GOLD_DIRECTORY
normalize_project_root_declaration
resolve_project_relative_path
resolve_source_root
resolve_source_relative_path
resolve_module_path
resolve_scenario_path
resolve_project_paths
```

`resolve_project_paths(config: ProjectConfig) -> ProjectPaths` is the canonical resolved-path operation.

The following duplicate names are forbidden:

```text
module_path
scenario_path
resolve_project_config
```

Consumers use `resolve_module_path`, `resolve_scenario_path` and `schema.parse_project_document` instead.

Generic filesystem containment comes from `infrastructure.filesystem` in adapters or use cases; project-domain path policy remains pure here.

### 10.3 Project policy ownership

`projects.policies` owns pure reusable policy:

```text
REQUIRED_PROJECT_ASSETS
contains_template_placeholder
find_unresolved_placeholder
validate_project_semantics
enforce_project_invariants
validate_project_id
is_recommended_project_id
validate_project_name
validate_language_code
validate_project_root
validate_source_glob
validate_optional_regex
validate_portable_project_path
normalized_portable_path_key
deduplicate_declared_path_parts
validate_minimum_version
validate_module_targets
validate_scenario_id
is_recommended_scenario_id
validate_scenario_policy
validate_release_requires_pgf
```

Migration-specific planning helpers remain private to `projects.migrator`; they MUST NOT inflate the general project-policy API.

### 10.4 Project ports

`projects.ports` owns mechanism-neutral contracts:

```text
TreeEntryKind
ArchiveFormat
TreeEntry
ArchiveReceipt
LifecycleLockRequest
ProjectConfigReader
ProjectConfigWriter
ProjectFilesystem
ProjectTemplateSource
ProjectArchiveWriter
LifecycleLease
ProjectLifecycleLock
ClockPort
```

Rules:

- `AbstractContextManager` is imported from `contextlib`, not `collections.abc`.
- Protocols use `projects.models.ProjectConfig` under `TYPE_CHECKING` when needed.
- `ProjectWorkspace`, `ProjectFileSystem` and `ProjectMigrationWorkspacePort` are forbidden duplicate aggregate ports.
- Initialization, reset and migration compose the registered granular ports.
- Adapters MUST return the exact `TreeEntry` and `TreeEntryKind` owned here.

### 10.5 Project schema

`projects.schema` owns:

```text
ProjectTable
SourcesTable
GFTable
ModulesTable
ValidationTable
ProjectDocument
ProjectSchemaCompatibility
validate_project_schema
validate_project_template_schema
parse_project_document
```

```python
parse_project_document(
    document: ProjectDocument,
    *,
    source_file: Path,
) -> ProjectConfig
```

It validates schema identity/version and constructs typed project configuration. TOML decoding remains in `toml_adapter`; path calculations remain in `paths`.

### 10.6 TOML adapter

`projects.toml_adapter` owns project-TOML mechanism symbols:

```text
ProjectTomlError
ProjectTomlDecodeError
ProjectTomlEncodeError
TomlScalar
TomlValue
TomlDocument
read_project_toml
parse_project_toml
render_project_toml
write_project_toml
```

The adapter does not own project semantic policy or active-project selection.

### 10.7 Filesystem adapter

`projects.filesystem_adapter` implements project ports using infrastructure filesystem and atomic-I/O primitives.

It MAY own adapter-only symbols such as `LinkPolicy`, `TreeDifference`, `ProjectFilesystemAdapter` and `compare_inventories`.

It MUST import `TreeEntry` and `TreeEntryKind` from `projects.ports`; it MUST NOT redefine them.

### 10.8 Loader

`projects.loader` owns:

```text
ProjectLoader
load_project_config
```

Load flow:

```text
explicit absolute project.toml
-> ProjectConfigReader
-> schema.parse_project_document
-> policies.enforce_project_invariants
-> ProjectValidator.validate_for_load
-> ProjectConfig
```

Loading performs no GF execution, project mutation, state-based identity inference or run-history lookup.

### 10.9 Validator

`projects.validator` owns:

```text
ProjectValidator
validate_project
ensure_project_valid
check_project
```

All return or consume `ProjectValidationResult`; no `ProjectValidationReport` type is introduced.

The validator uses canonical path functions and project policies. It does not parse TOML, write reports or launch GF.

### 10.10 Initializer

`projects.initializer` owns:

```text
ProjectInitializationRequest
ProjectInitializationResult
ProjectInitializer
initialize_project
```

Initialization composes `ProjectTemplateSource`, `ProjectFilesystem`, `ProjectConfigWriter`, `ProjectLifecycleLock` and `ProjectValidator`.

`ProjectTemplateStage` is an implementation detail, if needed, and MUST remain private to `initializer.py`. It is not a shared project model. No aggregate `ProjectWorkspace` port is introduced.

### 10.11 Resetter

`projects.resetter` owns reset-specific enums, models, protocols and services:

```text
ResetScope
PreservationMode
ResetPhase
ResetOutcome
PhaseStatus
LifecycleErrorCategory
ResetRequest
ResetPlan
PhaseRecord
ResetFailure
ResetResult
ProjectResetError
ResetPlanner
ResetOperations
ProjectResetter
plan_project_reset
reset_project
```

`plan_project_reset(request) -> ResetPlan` is pure. `reset_project(...) -> ResetResult` performs the explicit lifecycle operation through ports/adapters.

### 10.12 Migrator

`projects.migrator` owns all migration-specific contracts:

```text
ProjectMigrationStrategy
ProjectMigrationStatus
ProjectMigrationActionKind
ProjectMigrationRequest
ProjectMigrationIssue
ProjectMigrationAction
ProjectMigrationPlan
ProjectMigrationResult
ProjectMigrator
plan_project_migration
migrate_project
```

Migration planning is pure over explicit observations. Execution uses project ports and produces a structured result. Migration-specific models MUST NOT be imported from `projects.models`, and migration-specific policy helpers remain private unless a separately reviewed reusable owner is established.

### 10.13 Public project facade

`projects.public` re-exports only:

```text
ProjectConfig
load_project_config
resolve_project_paths
check_project
initialize_project
plan_project_reset
reset_project
plan_project_migration
migrate_project
```

Each symbol is imported from its owner; `projects.public` defines no behavior.

Consumers requiring use cases import from `projects.public`. Consumers requiring stable domain types MAY import them directly from `projects.models`.

---

## 11. Application-state contract

### 11.1 State models

`state.models` owns:

```text
EnvironmentState
SelectionState
LastRunState
AppState
StateDiagnosticCode
StateDiagnostic
StateLoadResult
```

Locked imports:

- `ProducerInfo` from `kernel.serialization`;
- `ValidationMode` from `kernel.statuses`.

`state.models` MUST NOT import these symbols through `config.models`.

`StateLoadResult` distinguishes loaded, recovered, migrated, defaulted and failed outcomes without making state authoritative for project identity.

### 11.2 State schema

`state.schema` owns:

```text
APP_STATE_SCHEMA_ID
APP_STATE_SCHEMA_VERSION
ProducerDocument
EnvironmentDocument
SelectionDocument
LastRunDocument
AppStateDocument
StateSchemaWarning
StateSchemaResult
default_app_state_document
recover_app_state_document
canonicalize_app_state_document
producer_document
default_app_state
parse_app_state
serialize_app_state
validate_app_state
```

Canonical operations:

```python
default_app_state() -> AppState
parse_app_state(document: Mapping[str, object]) -> AppState
serialize_app_state(state: AppState) -> AppStateDocument
validate_app_state(state: AppState) -> tuple[StateDiagnostic, ...]
```

Document recovery may preserve warnings, but canonical writers emit only the current schema.

### 11.3 State migrations

`state.migrations` owns:

```text
JsonScalar
JsonValue
JsonObject
StateMigrationError
StateMigrationWarning
LegacyStateMigration
migrate_legacy_state
```

Migrations translate supported legacy input to the current document shape. They do not write files or mutate project configuration.

### 11.4 State repository

`state.repository` owns:

```text
CANONICAL_STATE_FILENAME
LEGACY_STATE_FILENAME
StateRepository
load_app_state
save_app_state
```

Repository rules:

1. state paths are explicit normalized absolute paths;
2. state files MUST NOT be placed in run-owned output directories;
3. reads are bounded and strict;
4. supported legacy state may be migrated explicitly;
5. unsupported future major versions fail closed;
6. writes use `atomic_write_bytes`;
7. publication failures raise `kernel.errors.StateWriteError`;
8. diagnostics are structured before optional logging;
9. state never selects a different active project than the workspace/project resolver.

---

## 12. Locked inter-component contracts

| ID | Provider | Consumer | Locked result |
|---|---|---|---|
| `IFC-WB-001` | workspace structure | project loader | exactly one canonical active-project boundary at `project/` |
| `IFC-WB-002` | `project/project.toml` | projects module | schema-validated deterministic project configuration |
| `IFC-WB-003` | CLI/GUI | application use cases | typed requests and equivalent domain meaning |
| `IFC-WB-004` | application run request | validation | explicit ordered stages, target, budget and cancellation |
| `IFC-WB-005` | validation | process/GF ports | structured shell-free request and raw execution evidence |
| `IFC-WB-006` | validation evidence | diagnostics | preserved raw evidence and separate causal classification |
| `IFC-WB-007` | finalized typed results | reporting | deterministic reports without re-execution |
| `IFC-WB-008` | run finalization | artifact bundle | one run directory, terminal state and completeness evidence |
| `IFC-WB-009` | public Wordbench artifacts | optional Portfolio reader | read-only versioned boundary with no reverse dependency |
| `IFC-WB-010` | project template | initializer/resetter | generic staged project with resolved required placeholders |
| `IFC-WB-011` | kernel shared types | config/projects/state/process | one owner per shared enum, identifier, producer and exception |
| `IFC-WB-012` | project ports | project adapters/use cases | adapters implement exact port-owned models and protocols |
| `IFC-WB-013` | app-state schema | state repository | version-aware parse, migration, validation and atomic write |
| `IFC-WB-014` | process submodules | process runner | one launch, capture, cancellation and termination vocabulary |

---

## 13. Artifact ownership

| Artifact | Writer | Readers | Mutation rule |
|---|---|---|---|
| `project/project.toml` | explicit initialization or migration | projects module, documentation | no silent normal-run mutation |
| project GF sources | project maintainers | GF and validation | normal validation is read-only |
| `.gfs` scenarios and inputs | project maintainers | validation and GF | no normal-run mutation |
| gold files | explicit reviewed update workflow | regression comparison | never auto-accepted |
| raw stdout/stderr | process capture | validation, diagnostics, reports, users | immutable after capture |
| normalized output | validation normalizer | comparison and reports | derived; raw evidence retained |
| run summary and manifest | reporting/finalization owners | users, automation, Portfolio | immutable after final publication except versioned repair |
| application state | state repository | entrypoints/application | never project authority |
| project archives | project archive adapter | reset/migration recovery | immutable verified evidence |

---

## 14. Explicit anti-duplication decisions

The following ownership decisions are normative:

| Symbol or concept | Sole owner | Forbidden competing location/name |
|---|---|---|
| `ProducerInfo` | `kernel.serialization` | `config.models`, `state.models` |
| `ValidationMode` | `kernel.statuses` | `config.models`, validation modules |
| `TargetKind` | `kernel.statuses` | string-only duplicate enum elsewhere |
| `CancellationToken` | `process.termination` | `process.models` |
| `ProcessCapture` | `process.streams` | duplicate model in `process.models` |
| process creation | `process.launcher.launch_without_shell` | direct `Popen` elsewhere; `launch_process` duplicate |
| process termination | `process.termination.terminate_owned_processes` | `terminate_process_tree` duplicate |
| child environment | `infrastructure.environment.build_child_environment` | runner-local merge or duplicate helper names |
| `TreeEntry`, `TreeEntryKind` | `projects.ports` | redefinition in `filesystem_adapter` |
| project validation aggregate | `projects.models.ProjectValidationResult` | `ProjectValidationReport` |
| project path functions | `projects.paths.resolve_*` | `module_path`, `scenario_path` aliases |
| project use-case facade | `projects.public` | broad eager exports from `projects.__init__` |
| state producer/mode imports | kernel owners | imports routed through `config.models` |
| state write exception | `kernel.errors.StateWriteError` | repository-local exception hierarchy |
| reset models | `projects.resetter` | duplicate general models in `projects.models` |
| migration models | `projects.migrator` | duplicate general models in `projects.models` |
| canonical architecture document | `docs/architecture/CANONICAL_FILE_ARCHITECTURE.md` | misplaced competing document path |

Compatibility aliases MAY exist only inside a documented migration reader. Canonical runtime writers and imports MUST use the registered names.

---

## 15. Public API and `__all__` enforcement

1. Every owner module MUST declare an explicit `__all__` for its supported cross-file API.
2. Every facade MUST import each re-export from its registered owner.
3. A facade MUST NOT wrap, subclass or redefine an owned symbol merely to change its module path.
4. A public symbol removed or renamed requires compatibility classification, migration/deprecation notes and coordinated consumer updates.
5. Private helpers are unconstrained internally but MUST NOT appear in another module's imports.
6. Protocol implementations are checked structurally and by contract tests; an adapter MAY expose additional private capabilities but consumers MUST depend on the port.

---

## 16. Required conformance checks

The repository architecture verification MUST fail when any of the following is detected:

- a fixed file is absent or placed outside the canonical architecture;
- an internal import names a nonexistent module or symbol;
- two modules define the same registered public contract;
- a facade re-exports a symbol from the wrong owner;
- a package initializer performs work or imports a broad graph;
- a domain/policy/port module imports a concrete adapter;
- process creation occurs outside `launcher.py`;
- atomic persistent publication bypasses `atomic_io.py`;
- project adapters redefine port-owned models;
- state models import shared contracts through configuration;
- a future persisted schema version is accepted silently;
- a runtime module imports `gf-portfolio`;
- generated artifacts or state become project identity authority.

Minimum automated checks:

```text
compile all fixed Python files
import every fixed runtime module
verify every internal imported symbol exists
verify __all__ symbols exist
verify facade owner mappings
verify forbidden imports and dependency cycles
verify exact enum values
verify protocol/adaptor compatibility
verify schema IDs and supported versions
verify atomic writer usage for persistent files
verify package imports perform no I/O
```

---

## 17. Change control

A contract-changing edit MUST:

1. identify the affected `IFC-WB-*` contract;
2. identify the owner, provider and every consumer;
3. classify the change as compatible, breaking or documentation repair;
4. update models, ports, adapters, facades and entrypoints together;
5. update persisted schemas and migrations when applicable;
6. update contract, unit, integration and architecture tests;
7. update the specialized owner documentation;
8. update this lock and the documentation correction ledger;
9. publish deprecation or migration guidance for breaking changes.

A documentation-only edit is compatible only when it does not change normative meaning.

---

## 18. Release checklist

```text
[ ] canonical architecture document is at its declared path
[ ] every fixed foundation file is present
[ ] every runtime module imports successfully
[ ] every internal imported symbol exists
[ ] each public symbol has one registered owner
[ ] package and facade exports match this lock
[ ] shared enums and ProducerInfo use kernel owners
[ ] process runner uses the registered launch/capture/termination APIs
[ ] project adapters implement ports without redefining port models
[ ] project public facade resolves every exported use case
[ ] state schema and repository APIs agree
[ ] state remains non-authoritative for project identity
[ ] dependency direction remains acyclic
[ ] persisted writes are versioned and atomic
[ ] raw process evidence is preserved
[ ] GF Wordbench has no reverse dependency on gf-portfolio
[ ] contract-changing edits updated tests and owner documents
```
