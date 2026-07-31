# GF Wordbench — Interfile Contract Lock

**Document ID:** `GF-WB-ARCH-INTERFILE-LOCK`  
**Status:** Normative  
**Contract version:** `4.1.2`  
**Applies to:** GF Wordbench framework, path-resolved language startup, resolved-language boundary, optional validation profiles, persisted state and public artifact boundary  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**File-placement authority:** `docs/architecture/CANONICAL_FILE_ARCHITECTURE.md`  
**Owner:** GF Wordbench maintainers  
**Governing decision:** `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`  
**Last reviewed:** `2026-07-31`

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
- **SELECTED LANGUAGE PATH**: one explicit machine-local directory or `.gf` file chosen by the user, CLI or automation as the starting point for language resolution.
- **LANGUAGE CANDIDATE**: a provisional non-executable result derived from the selected path and bounded observations.
- **RESOLVED LANGUAGE CONTEXT**: the immutable, validated runtime authority for one loaded language.
- **VALIDATION PROFILE**: optional explicit project policy adding filters, targets, scenarios, golds and release gates to a resolved language context.
- **CAPABILITY STATUS**: a typed statement such as `source-ready`, `scan-ready`, `compile-ready`, `scenario-ready` or `release-ready`.

A public symbol has exactly one owner. Re-exporting does not transfer ownership.

Candidate discovery is not runtime authority. Only a `ResolvedLanguageContext` may authorize main-runtime composition or ordinary run construction.

## 3. Product and architectural invariants

1. A running Wordbench session has zero or one resolved language context.
2. One ordinary run resolves exactly one portable language identity and one immutable source context.
3. Normal startup begins from one explicit selected language path; it does not require a global language catalog or mandatory language bundle.
4. Candidate discovery is bounded to the selected path, its supported ancestors, the selected language directory and approved exact-name remediation beneath the resolved source root.
5. Source enumeration, filtering, containment, deduplication and deterministic ordering remain owned by the existing file-selection service.
6. GF path resolution remains centralized and one effective resolution is reused by all GF consumers in a run.
7. GF remains the semantic authority for parsing, type checking, module resolution, compilation and PGF construction.
8. Static scan and GF execution remain separate stages with separate claims.
9. Process execution is shell-free and reachable only through the process boundary.
10. Raw evidence is preserved before parsing, normalization or diagnosis.
11. Reports consume finalized typed results and never execute validation or GF.
12. Application state is local, disposable and never authoritative for language identity, source roots or effective GF paths.
13. A validation profile is optional for browsing, source selection, static scan and targeted compilation; it is required only for policy that it explicitly owns.
14. A validation profile MUST NOT override or escape the resolved language context.
15. Switching language disposes the old runtime and constructs a new resolved context; active-run mutation is forbidden.
16. GF Wordbench is one deployable hexagonal modular monolith.
17. `gf-portfolio` may consume finalized public artifacts; GF Wordbench MUST NOT import or require Portfolio code, state, configuration or storage.
18. Domain policy remains independent of concrete filesystem, TOML, JSON, subprocess, UI and GF implementations.
19. Persisted writers emit explicit schema identity and version and write atomically.
20. Future schema versions fail closed unless an explicit compatibility policy allows otherwise.

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
  ├── projects domain + language-probe ports
  │     └── projects adapters/use cases
  └── state models/schema/migrations
        └── state repository
```

Application composition direction:

```text
GUI / CLI
    → projects.public language-probe use case
        → public source-selection contract
        → public GF-path-resolution contract
        → public structural-preflight contract
        → public diagnostic models

bootstrap
    → composes concrete services and adapters
```

Additional allowed edges:

- `config.models -> projects.models.ProjectConfig` for optional validation profiles;
- `config.models -> projects.languages.models.ResolvedLanguageContext`;
- `projects.languages.probe -> projects.languages.models|projects.languages.ports`;
- probe dependencies supplied through public protocols MAY be implemented by existing validation, GF-path, preflight and diagnostic services;
- `projects` adapters -> `infrastructure` mechanisms;
- `state.repository -> infrastructure`, `kernel.errors`, `version`;
- application/bootstrap modules -> public module facades and ports.

Forbidden edges include:

- `kernel -> config|infrastructure|projects|state|entrypoints`;
- domain models or policies -> concrete adapters;
- `projects.models|projects.policies|projects.ports|projects.languages.models|projects.languages.ports -> infrastructure`;
- `projects.languages.probe -> GUI widgets|process adapters|report writers`;
- `projects.languages.probe` performing direct recursive source enumeration when the source-selection port owns that behavior;
- `projects.languages.probe` launching GF or subprocesses directly;
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
| `projects.languages.__init__` | Empty public API; no eager imports or filesystem discovery. |
| `state.__init__` | Empty public API; no eager imports. |
| `infrastructure.process.__init__` | Narrow process facade defined in §9.7. |
| `projects.public` | Narrow project facade defined in §10.13. |

A package initializer MUST NOT perform I/O, resolve configuration, instantiate adapters or hide a dependency cycle.

---

## 6. Canonical foundation file registry

This section locks the responsibility of the canonical foundation implementation files. Public symbol registries in §§7–11 are authoritative when a row contains only a responsibility summary.

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
| `projects/languages/models.py` | Immutable selected-path, language-candidate, capability, diagnostic, probe-result and resolved-language-context contracts. |
| `projects/languages/ports.py` | Mechanism-neutral probe dependencies for source selection, GF path resolution, structural preflight and optional GF verification. |
| `projects/languages/probe.py` | Bounded orchestration from one explicit selected path to one candidate or resolved language context. |
| `projects/languages/__init__.py` | Side-effect-free empty package API. |
| `projects/models.py` | Optional validation-profile configuration, project diagnostics and validation-result models. |
| `projects/paths.py` | Pure profile-relative and resolved validation-asset path construction. |
| `projects/policies.py` | Pure validation-profile invariants, naming, placeholder and semantic policies. |
| `projects/ports.py` | Profile-owned filesystem, TOML, template, archive, clock and lifecycle ports. |
| `projects/schema.py` | Raw validation-profile document shape, version compatibility and document-to-model parsing. |
| `projects/toml_adapter.py` | Validation-profile TOML decoding, deterministic rendering and atomic persistence. |
| `projects/filesystem_adapter.py` | Concrete implementation of profile filesystem and lifecycle mechanisms. |
| `projects/loader.py` | Load one explicit optional validation profile. |
| `projects/validator.py` | Structural and semantic validation-profile validation. |
| `projects/initializer.py` | Template-to-profile initialization. |
| `projects/resetter.py` | Explicit profile reset planning and execution. |
| `projects/migrator.py` | Legacy-project/profile migration planning and execution. |
| `projects/public.py` | Stable language-probe and validation-profile use-case facade. |
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
- `RunConfig.language_context` uses `projects.languages.models.ResolvedLanguageContext`.
- `RunConfig.validation_profile` is `projects.models.ProjectConfig | None`.
- a validation profile augments policy but MUST NOT redefine the selected language directory, portable language identity or approved source-root containment.
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

`resolve_precedence(request)` is pure. It selects explicit and default values, returns provenance and reports equal-tier conflicts. It performs no filesystem access, executable discovery, language probing or profile loading.

Language identity and source-root facts do not participate in ordinary value precedence after a `ResolvedLanguageContext` exists. Consumers receive those facts from the resolved context.

### 8.3 Environment ownership

`config.environment` owns:

```text
ENVIRONMENT_PREFIX
LANGUAGE_PATH_ENV
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

Canonical environment names include:

```text
GF_WORDBENCH_LANGUAGE_PATH
GF_WORDBENCH_PROJECT_ROOT
GF_WORDBENCH_GF_EXECUTABLE
GF_WORDBENCH_RGL_ROOT
GF_WORDBENCH_OUTPUT_ROOT
GF_WORDBENCH_STATE_PATH
```

`GF_WORDBENCH_LANGUAGE_PATH` is an explicit noninteractive selected-path input. It is not trusted without the normal language probe.

`GF_WORDBENCH_PROJECT_ROOT` remains a compatibility or explicit validation-profile input; it is not the normal language-startup authority.

```python
read_environment(environ: Mapping[str, str] | None = None) -> EnvironmentOverrides
resolve_environment(request: ConfigurationResolutionRequest) -> EnvironmentResolution
```

Raw environment reading preserves values. Expansion, normalization, existence checks and executable discovery occur only in `resolve_environment`. Language-directory and RGL-source-root discovery remain owned by the language probe.

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

The resolver composes an already published `ResolvedLanguageContext`, optional validation profile, defaults, explicit settings, state hints and environment facts.

It MUST NOT duplicate:

- selected-path probing;
- source enumeration;
- language identity construction;
- GF path resolution;
- precedence tables;
- environment variable names;
- profile parsing;
- profile path rules.

### 8.5 Defaults

`config.defaults` owns only documented constants. It imports enum values but defines no enum, model, language identity, path resolution or environment behavior.

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

## 10. Resolved-language and optional validation-profile contracts

### 10.1 Language model ownership

`projects.languages.models` owns:

```text
SelectedPathKind
LanguageCapability
LanguageProbeStatus
LanguageProbeSeverity
LanguageProbeRequest
LanguageProbeDiagnostic
LanguageModuleCandidate
LanguageCandidate
ResolvedLanguageContext
LanguageProbeResult
```

Required model rules:

- public dataclasses are frozen and slotted;
- path collections are deterministic tuples;
- `LanguageCandidate` is provisional and cannot authorize run construction;
- `ResolvedLanguageContext` is immutable and is the sole runtime language/source authority;
- the portable language key is distinct from display name, local absolute path and optional module suffix;
- capability statuses distinguish source, scan, compile, scenario and release readiness;
- absolute selected paths are machine-local evidence, not portable identity.

No competing `ActiveProjectContext`, `LanguageRuntimeConfig`, `CatalogLanguageContext` or mutable GUI-owned context may coexist.

### 10.2 Language-probe ports

`projects.languages.ports` owns mechanism-neutral contracts:

```text
LanguageSourceSelectionPort
LanguageGFPathResolutionPort
LanguageStructuralPreflightPort
LanguageVerificationPort
LanguageProbeClockPort
```

These protocols expose only the observations needed by the probe. They do not redefine models owned by source selection, GF path resolution, preflight, compilation or diagnostics.

Concrete objects from existing modules MAY satisfy these protocols structurally. An adapter is introduced only when a signature translation is required; it MUST delegate rather than reimplement the underlying behavior.

### 10.3 Language probe

`projects.languages.probe` owns:

```text
LanguageProbeService
probe_language_path
```

Canonical operation:

```python
probe_language_path(
    request: LanguageProbeRequest,
    *,
    source_selector: LanguageSourceSelectionPort,
    gf_path_resolver: LanguageGFPathResolutionPort,
    structural_preflight: LanguageStructuralPreflightPort,
    verifier: LanguageVerificationPort | None = None,
) -> LanguageProbeResult
```

The probe owns only:

- interpreting one explicit selected file or directory;
- deriving the candidate language directory;
- bounded ancestor inspection for the supported source-root layout;
- coordinating existing public services;
- classifying standard RGL module-role candidates from selected filenames;
- collecting structured diagnostics and ambiguity choices;
- publishing one resolved context after required structural validation.

The probe MUST NOT:

- recursively enumerate source files itself;
- parse full GF import semantics;
- construct native GF commands;
- call `subprocess`;
- write reports or state;
- read a global runtime language catalog;
- require a language bundle for source-ready startup;
- mutate source or profile files.

### 10.4 Standard module classification

The probe may classify standard candidate roles such as:

```text
Lang<Suffix>.gf
Grammar<Suffix>.gf
All<Suffix>.gf
Syntax<Suffix>.gf
Lexicon<Suffix>.gf
Paradigms<Suffix>.gf
Morpho<Suffix>.gf
Cat<Suffix>.gf
Noun<Suffix>.gf
Verb<Suffix>.gf
Structural<Suffix>.gf
```

Classification is advisory. It does not replace GF module resolution and does not require every language to contain every role.

When a specific `.gf` file is selected, that file remains the focused target. Detected entrypoints may be offered without silently replacing the selected file.

### 10.5 Missing-module assistance

A typed canonical GF diagnostic may trigger a bounded exact-name search under the approved RGL source root.

The source-selection owner performs enumeration and containment. The probe coordinates the result:

```text
zero exact matches      → module absent diagnostic
one exact match         → remediation candidate
multiple exact matches  → explicit ambiguity requiring user choice
```

No directory is added more than once. Search and remediation counts are bounded. The effective GF path is always revalidated by the centralized GF path resolver.

### 10.6 Optional validation-profile model ownership

`projects.models` continues to own stable validation-profile contracts:

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

`ProjectConfig` is an optional validation profile. It may add filters, targets, scenarios, golds and release policy. It is not the normal startup language authority.

`ProjectValidationResult` is the single profile-validation aggregate. `ProjectValidationReport` is not a separate canonical type.

Migration-, initialization- and reset-specific request/result models belong to their use-case modules, not to `projects.models`.

### 10.7 Validation-profile path ownership

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

`resolve_project_paths(config: ProjectConfig) -> ProjectPaths` is the canonical profile-path operation.

The following duplicate names are forbidden:

```text
module_path
scenario_path
resolve_project_config
```

Generic filesystem containment comes from `infrastructure.filesystem` in adapters or use cases; profile-domain path policy remains pure here.

Resolved profile paths MUST be checked against the active `ResolvedLanguageContext` before they participate in a run. A profile cannot redirect the run into another language source tree.

### 10.8 Validation-profile policy ownership

`projects.policies` owns pure reusable profile policy:

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

Policies MUST distinguish startup-optional assets from capability-required assets. Missing scenarios, golds or release targets do not invalidate source-ready startup.

Migration-specific planning helpers remain private to `projects.migrator`.

### 10.9 Validation-profile ports

`projects.ports` owns mechanism-neutral profile and lifecycle contracts:

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
- protocols use `projects.models.ProjectConfig` under `TYPE_CHECKING` when needed;
- `ProjectWorkspace`, `ProjectFileSystem` and `ProjectMigrationWorkspacePort` are forbidden duplicate aggregate ports;
- initialization, reset and migration compose the registered granular ports;
- adapters return the exact `TreeEntry` and `TreeEntryKind` owned here.

### 10.10 Validation-profile schema and TOML adapter

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

`projects.toml_adapter` owns:

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

The adapter does not own profile semantic policy or active-language selection.

### 10.11 Validation-profile loader and validator

`projects.loader` owns:

```text
ProjectLoader
load_project_config
```

Load flow:

```text
explicit absolute project.toml
→ ProjectConfigReader
→ schema.parse_project_document
→ policies.enforce_project_invariants
→ ProjectValidator.validate_for_load
→ ProjectConfig
```

Profile loading performs no GF execution, source-path inference, state-based identity selection or run-history lookup.

`projects.validator` owns:

```text
ProjectValidator
validate_project
ensure_project_valid
check_project
```

All return or consume `ProjectValidationResult`; no `ProjectValidationReport` type is introduced.

The validator checks profile compatibility with the active resolved language context through an explicit application-level operation. It does not parse TOML, write reports or launch GF.

### 10.12 Validation-profile filesystem adapter

`projects.filesystem_adapter` implements profile ports using infrastructure filesystem and atomic-I/O primitives.

It MAY own adapter-only symbols such as:

```text
LinkPolicy
TreeDifference
ProjectFilesystemAdapter
compare_inventories
```

It MUST import `TreeEntry` and `TreeEntryKind` from `projects.ports`; it MUST NOT redefine them.

### 10.13 Initializer

`projects.initializer` owns:

```text
ProjectInitializationRequest
ProjectInitializationResult
ProjectInitializer
initialize_project
```

Initialization composes `ProjectTemplateSource`, `ProjectFilesystem`, `ProjectConfigWriter`, `ProjectLifecycleLock` and `ProjectValidator`.

`ProjectTemplateStage` is an implementation detail, if needed, and MUST remain private to `initializer.py`. No aggregate `ProjectWorkspace` port is introduced.

Initialization creates an optional validation profile. It does not select a language path, publish a resolved context or become a normal startup prerequisite.

### 10.14 Resetter

`projects.resetter` owns:

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

`plan_project_reset(request) -> ResetPlan` is pure. `reset_project(...) -> ResetResult` performs the explicit lifecycle operation through ports and adapters.

Reset affects validation-profile assets only. It MUST NOT alter the selected language path, active resolved context or language source tree.

### 10.15 Migrator

`projects.migrator` owns:

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

Migration may convert a legacy active-project contract into an optional validation profile. It does not infer or select a new language path.

### 10.16 Public project facade

`projects.public` re-exports only reviewed stable symbols, including:

```text
SelectedPathKind
LanguageCapability
LanguageProbeRequest
LanguageProbeDiagnostic
LanguageCandidate
ResolvedLanguageContext
LanguageProbeResult
LanguageProbeService
probe_language_path
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

Consumers requiring startup or validation-profile use cases import from `projects.public`. Consumers requiring stable domain types MAY import them directly from their owner modules.

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

`SelectionState` may remember machine-local convenience values such as:

```text
last_selected_language_path
last_selected_validation_profile_path
last_rgl_root
```

`LastRunState` may retain one run reference and its portable language identity for presentation and compatibility checks.

`StateLoadResult` distinguishes loaded, recovered, migrated, defaulted and failed outcomes without making state authoritative for language identity, source roots, GF paths or profile policy.

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

Canonical writers emit only the current schema. Absolute selected paths are permitted only in local application state according to privacy and redaction policy.

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

Migrations translate supported legacy input to the current document shape. They do not write files, scan the filesystem, select a language, mutate validation-profile configuration or reconstruct an old executable context.

A legacy catalog language ID without a remembered path does not trigger global discovery; the user is asked to select a path.

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
9. state never bypasses `LanguageProbeService` or publishes `ResolvedLanguageContext`;
10. “Open last language” reruns full probe and containment validation;
11. failed state persistence after successful runtime composition is non-fatal and reported as a warning.

## 12. Locked inter-component contracts

| ID | Provider | Consumer | Locked result |
|---|---|---|---|
| `IFC-WB-001` | GUI/CLI explicit selected language path | language probe | one normalized bounded `LanguageProbeRequest` |
| `IFC-WB-002` | language probe | bootstrap and run construction | zero or one immutable `ResolvedLanguageContext`; ambiguity remains explicit |
| `IFC-WB-003` | CLI/GUI | application use cases | typed requests and equivalent domain meaning |
| `IFC-WB-004` | resolved context + optional validation profile | configuration/run construction | one immutable effective `RunConfig` |
| `IFC-WB-005` | application run request | validation | explicit ordered stages, target, capability, budget and cancellation |
| `IFC-WB-006` | language probe | source-selection service | delegated bounded enumeration, filtering, containment, deduplication and ordering |
| `IFC-WB-007` | language probe / validation | GF path resolver | one ordered effective path with provenance reused by every GF consumer |
| `IFC-WB-008` | validation | process/GF ports | structured shell-free request and raw execution evidence |
| `IFC-WB-009` | validation evidence | diagnostics | preserved raw evidence and separate causal classification |
| `IFC-WB-010` | finalized typed results | reporting | deterministic reports without re-execution |
| `IFC-WB-011` | run finalization | artifact bundle | one run directory, terminal state and completeness evidence |
| `IFC-WB-012` | public Wordbench artifacts | optional Portfolio reader | read-only versioned boundary with no reverse dependency |
| `IFC-WB-013` | language-neutral validation-profile template | initializer/resetter | generic staged external validation profile with resolved required placeholders |
| `IFC-WB-014` | kernel shared types | config/projects/state/process | one owner per shared enum, identifier, producer and exception |
| `IFC-WB-015` | project ports | project adapters/use cases | adapters implement exact port-owned models and protocols |
| `IFC-WB-016` | app-state schema | state repository | version-aware parse, migration, validation and atomic write |
| `IFC-WB-017` | process submodules | process runner | one launch, capture, cancellation and termination vocabulary |
| `IFC-WB-018` | explicit optional `project.toml` | profile loader and compatibility validator | policy augmentation only; no language/source-root override |
| `IFC-WB-019` | remembered selected path | introduction flow | convenience action followed by complete re-probe |
| `IFC-WB-020` | language switch request | bootstrap/runtime lifecycle | old runtime disposed before another context is published |

## 13. Artifact ownership

| Artifact | Writer | Readers | Mutation rule |
|---|---|---|---|
| selected language path | user, CLI, automation or local state | language probe | not a repository artifact; always revalidated |
| `ResolvedLanguageContext` | language probe | bootstrap, configuration, runs, GUI | immutable in memory; never reconstructed independently by consumers |
| explicit validation profile such as `<validation-profile-root>/project.toml` | explicit initialization or migration | profile loader, validation, documentation | external to the Wordbench repository by default; no silent normal-run mutation; not startup language authority |
| language GF sources | language/project maintainers | selector, scanner, GF and validation | normal probing and validation are read-only |
| `.gfs` scenarios and inputs | project/profile maintainers | validation and GF | no normal-run mutation |
| gold files | explicit reviewed update workflow | regression comparison | never auto-accepted |
| raw stdout/stderr | process capture | validation, diagnostics, reports, users | immutable after capture |
| normalized output | validation normalizer | comparison and reports | derived; raw evidence retained |
| run summary and manifest | reporting/finalization owners | users, automation, Portfolio | immutable after final publication except versioned repair |
| application state | state repository | entrypoints/application | convenience only; never language, source-root or GF-path authority |
| project/profile archives | project archive adapter | reset/migration recovery | immutable verified evidence |
| optional RGL inventory/catalog | explicit maintenance tooling | diagnostics, documentation, tests | regenerable and non-authoritative; never read by normal startup |

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
| source enumeration, filtering and deterministic order | existing source-selection owner | recursive probe scanner or catalog scanner in normal startup |
| effective GF path | centralized GF path resolver | probe-local concatenation, compiler-local reconstruction or GUI-owned path list |
| language candidate and resolved context models | `projects.languages.models` | `ActiveProjectContext`, `CatalogLanguageContext`, GUI-owned mutable duplicate |
| language-probe orchestration | `projects.languages.probe` | entrypoint-specific discovery or second RGL resolver |
| GF execution | GF anti-corruption/process boundary | probe-local subprocess or trial compiler |
| `TreeEntry`, `TreeEntryKind` | `projects.ports` | redefinition in `filesystem_adapter` |
| validation-profile aggregate | `projects.models.ProjectValidationResult` | `ProjectValidationReport` |
| profile path functions | `projects.paths.resolve_*` | `module_path`, `scenario_path` aliases |
| project/language use-case facade | `projects.public` | broad eager exports from `projects.__init__` |
| state producer/mode imports | kernel owners | imports routed through `config.models` |
| state write exception | `kernel.errors.StateWriteError` | repository-local exception hierarchy |
| reset models | `projects.resetter` | duplicate general models in `projects.models` |
| migration models | `projects.migrator` | duplicate general models in `projects.models` |
| normal startup language authority | explicit selected path + `LanguageProbeService` | runtime catalog, mandatory language bundle, implicit project-root scan |
| canonical architecture document | `docs/architecture/CANONICAL_FILE_ARCHITECTURE.md` | misplaced competing document path |

Compatibility aliases MAY exist only inside a documented migration reader. Canonical runtime writers and imports MUST use the registered names.

## 15. Public API and `__all__` enforcement

1. Every owner module MUST declare an explicit `__all__` for its supported cross-file API.
2. Every facade MUST import each re-export from its registered owner.
3. A facade MUST NOT wrap, subclass or redefine an owned symbol merely to change its module path.
4. A public symbol removed or renamed requires compatibility classification, migration/deprecation notes and coordinated consumer updates.
5. Private helpers are unconstrained internally but MUST NOT appear in another module's imports.
6. Protocol implementations are checked structurally and by contract tests; an adapter MAY expose additional private capabilities but consumers MUST depend on the port.
7. `projects.public` is the only broad cross-module facade for language probing and optional validation-profile use cases.
8. GUI and CLI entrypoints MUST NOT re-export probe implementation helpers or filesystem mechanisms.

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
- application state, a prior run, a global catalog or a mandatory bundle becomes normal startup language authority;
- main-runtime composition occurs without one `ResolvedLanguageContext`;
- the language probe enumerates source files independently of the source-selection owner;
- the language probe constructs native GF command lines or invokes subprocesses;
- a compiler, scenario runner or PGF builder reconstructs a different GF path;
- a validation profile redirects outside or contradicts the resolved language context;
- language switching mutates an existing runtime instead of replacing it;
- generated artifacts or state become portable language-identity authority.

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
verify probe delegates source selection
verify one GF path resolution is reused
verify GUI and CLI produce equivalent probe requests
verify runtime catalog code is absent from normal startup
verify two-language replacement leaves no prior-context paths or targets
```

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

### 17.1 Active parallel remediation lock — snapshot 18

This subsection is the integration authority for the parallel repair campaign based on:

```text
Code_snapshot_GF_Wordbench(18).zip
generated_at: 2026-07-31T10:30:06
```

It remains active until the branch acceptance conditions below are satisfied and the integrated repository passes collection, import, contract and targeted runtime checks. A branch MUST NOT reinterpret this subsection locally. A required change to a locked owner, symbol, field or write set stops the affected branch and requires a coordinated revision of this lock before implementation continues.

#### 17.1.1 Frozen product model

All parallel branches preserve these rules:

1. GF Wordbench is language-agnostic and may open successive GF languages from one explicit directory or `.gf` file.
2. A running runtime has zero or one immutable `ResolvedLanguageContext`; one ordinary run has exactly one language identity.
3. `selected_language_path` is the canonical normal-startup input.
4. `validation_profile_path` is optional explicit advanced policy. It does not select the language and does not override the resolved source context.
5. A repository-local `project/` directory, a static language catalog and a mandatory language bundle are not normal-startup authorities.
6. `project_root` may remain only inside explicitly documented validation-profile compatibility and lifecycle code. It MUST NOT reappear as the canonical GUI, diagnostics or ordinary-run language selector.
7. Language-specific names, modules, scenarios, golds and release rules do not enter framework defaults, tests or documentation except isolated fixtures explicitly labelled as such.
8. `/runs/` is a repository-root output directory; `src/gf_wordbench/runs/` is tracked application code.

#### 17.1.2 Frozen public owners and import paths

The following ownership assignments are mandatory for every branch in this campaign:

| Contract | Sole owner | Locked consumers and rule |
|---|---|---|
| diagnostics launcher configuration fields | `tools/diagnostics/diag_core.py::DiagConfig` | launch UI reads `repo_root`, `language_path` and `validation_profile`; it does not read `project_root` |
| language package initializer | `src/gf_wordbench/projects/languages/__init__.py` | side-effect-free empty package API; no migrations, repository code or eager exports |
| `collapse_blocker_graph` | `diagnostics/classification/relationships.py` | `classification/service.py` imports it from this owner only |
| `CausalityFacts`, `CausalityDecision`, `classify_causality` | `diagnostics/classification/causality.py` | `classification/service.py` adapts resolved relationship facts to this API; `CausalityEvidence` is not a registered contract and MUST NOT be introduced as a compatibility stub |
| diagnostic pattern helper ordering | `diagnostics/patterns/common.py` | every private validator and freezer used by a module-level `DiagnosticPattern` instance is defined before that instance is constructed |
| `DiagnosticMatchResult`, `EvidenceRef`, `Finding`, `TopError` | `diagnostics/models.py` | parsers, findings, top-error aggregation, runs and reporting import these models; consumers do not redefine them |
| `GuiRunRequest`, `LanguageView`, `language_view_from_context` | `entrypoints/gui/view_model.py` | canonical request fields include `selected_language_path` and `validation_profile_path`; CLI/GUI parity tests compare those meanings |
| `LanguageCommandServices` | `entrypoints/cli/language_commands.py` | contains the validated language-probe application dependency; no bootstrap-global service locator |
| `validate_summary_document` | `reporting/schemas/summary_v1.py` | strict public validator used by summary writers; `validate_summary_v1` remains the issue-producing validator |
| `ManifestVerificationPolicy` | `reporting/manifest/models.py` | `reporting/manifest/verifier.py` consumes the policy and MUST NOT define a duplicate policy model |
| `DiffEntry` | `validation/regression/models.py` | `runs/result_builder.py` imports it from the regression owner |
| `ScenarioResult` | `validation/scenarios/models.py` | run construction and diagnostics import it from the scenario owner |
| `TopError` aggregation | model in `diagnostics/models.py`; algorithm in `diagnostics/classification/top_errors.py` | `runs/result_builder.py` builds `TopErrorCandidate` values and calls the canonical aggregation function |
| `CompilePlan`, `CompileSummary` | `validation/compilation/models.py` | compilation service, run models, reporting and tests consume these types; no placeholder duplicates |
| normalization helper ordering | `validation/scenarios/normalization.py` | validators used by module-level profile instances are defined before those instances are constructed |
| canonical language-relative target | `validation/selection/targets.py::canonical_language_relative_target` | `canonical_project_relative_target` and `canonical_source_relative_target` may exist only as temporary compatibility aliases in the same owner |
| validation-profile template location | `templates/validation-profile/` | initialization reads this language-neutral template and writes to an explicit external destination |
| `SelectedPathKind` and `LanguageCapability` facade route | owner: `projects/languages/models.py`; narrow facade: `projects/languages/public.py`; broad facade: `projects/public.py` | both facades re-export the exact owner objects without wrapping, redefining or changing enum values; integration and entrypoint consumers may import the reviewed stable surface from `projects.public` |

Public dataclass field shapes are fixed by the owner module and its existing unit and contract tests. A consumer branch MUST adapt to the owner; it MUST NOT add a second model merely to preserve an obsolete import.

#### 17.1.3 Exclusive branch write sets

Each branch has an exclusive maximum authorized write set. Tests listed in the same row belong to that branch. Every other path is read-only unless the integration owner revises this lock.

A write-set row defines permission, not a mandatory modification list. A branch changes only the assigned files required to satisfy its locked contracts and acceptance evidence. Assigned files that do not require a change remain untouched and are reported under `files intentionally not changed`. Tests in a row are modified only when their imports, fixtures, assertions or coverage must be adapted; otherwise they are executed unchanged.

| Branch ID | Maximum authorized write set | Required evidence |
|---|---|---|
| `S18-B01-diagnostics-launch` | `tools/diagnostics/00-control_panel.pyw`; `tools/diagnostics/launch_diagnostics.bat`; `tests/unit/diagnostics/test_control_panel.py` | compile control panel; launcher fallback test; GUI construction smoke |
| `S18-B02-language-package` | `src/gf_wordbench/projects/languages/__init__.py`; package-initializer contract tests only | import performs no I/O and exposes no eager API |
| `S18-B03-diagnostics-contracts` | `src/gf_wordbench/diagnostics/models.py`; `src/gf_wordbench/diagnostics/classification/service.py`; directly owned diagnostics unit/contract tests | all registered models import; `collapse_blocker_graph` owner is respected; findings and top-error tests pass |
| `S18-B04-gui-view-model` | `src/gf_wordbench/entrypoints/gui/view_model.py`; `tests/unit/entrypoints/test_gui_view_model.py`; GUI side of `tests/components/test_cli_gui_parity.py` | canonical request fields and `LanguageView` tests pass |
| `S18-B05-cli-entrypoints` | `src/gf_wordbench/entrypoints/cli/language_commands.py`; `src/gf_wordbench/entrypoints/cli/project_commands.py`; `tests/unit/entrypoints/test_cli_commands.py`; CLI side of parity tests | language probe and explicit-profile command tests pass; no implicit repository project |
| `S18-B06-summary-schema` | `src/gf_wordbench/reporting/schemas/summary_v1.py`; summary schema/writer tests | both validator entrypoints import; invalid documents fail strictly; writers use the canonical validator |
| `S18-B07-manifest-policy` | `src/gf_wordbench/reporting/manifest/models.py`; manifest verification model tests | `ManifestVerificationPolicy` imports from models and verifier tests pass |
| `S18-B08-runs-results` | `src/gf_wordbench/runs/result_builder.py`; `tests/unit/runs/test_result_builder.py` | owner imports are canonical; scenario result and top-error aggregation tests pass |
| `S18-B09-runs-preflight` | `src/gf_wordbench/runs/preflight.py`; `tests/unit/runs/test_preflight.py`; preflight-specific planner tests when required | no-profile source-only preflight passes; scenario/release policy requires an explicit compatible profile |
| `S18-B10-compilation-models` | `src/gf_wordbench/validation/compilation/models.py`; compilation model/service tests | `CompilePlan` and `CompileSummary` are complete immutable contracts and compilation tests pass |
| `S18-B11-scenario-normalization` | `src/gf_wordbench/validation/scenarios/normalization.py`; normalization tests | module imports successfully; default registry construction and normalization tests pass |
| `S18-B12-selection-targets` | `src/gf_wordbench/validation/selection/targets.py`; `tests/unit/validation/selection/test_targets.py` | canonical language-relative function exists; compatibility aliases, when retained, delegate without changing semantics |
| `S18-B13-profile-initialization` | `scripts/init_project.py`; `src/gf_wordbench/projects/initializer.py`; initializer/lifecycle tests | template source is `templates/validation-profile/`; destination is explicit and external; no repository `project/` recreation |
| `S18-B14-pytest-collection` | `pyproject.toml` only | full collection has no duplicate-module-name collision; no test-discovery weakening |
| `S18-B15-repository-docs` | `DOCUMENT_MANIFEST.json`; `README.md`; `CONTRIBUTING.md` | merge last; paths and product language agree with integrated code and ADR-0015 |
| `S18-B16-diagnostics-pattern-order` | `src/gf_wordbench/diagnostics/patterns/common.py`; directly owned diagnostic-pattern unit/contract tests only | module imports without `NameError`; module-level patterns are constructed only after required private helpers exist; pattern registry and parser collection tests pass |
| `S18-B17-project-facades` | `src/gf_wordbench/projects/languages/public.py`; `src/gf_wordbench/projects/public.py`; project-facade contract tests and the facade-import portion of path-resolved startup integration tests | `SelectedPathKind` and `LanguageCapability` resolve through both reviewed facades with owner identity preserved; no broad package initializer export is introduced |

When a row names a shared integration test, only the portions corresponding to that branch's public surface may change. The integration owner resolves overlapping test hunks after both source branches are accepted; source branches MUST NOT silently overwrite each other.

#### 17.1.4 Campaign-wide read-only files

The following files are read-only for all repair branches unless a defect proves that their public contract is itself wrong and this lock is revised first:

```text
src/gf_wordbench/bootstrap.py
src/gf_wordbench/config/models.py
src/gf_wordbench/kernel/statuses.py
src/gf_wordbench/projects/models.py
src/gf_wordbench/projects/languages/models.py
src/gf_wordbench/runs/models/results.py
src/gf_wordbench/validation/regression/models.py
src/gf_wordbench/validation/scenarios/models.py
src/gf_wordbench/diagnostics/classification/relationships.py
src/gf_wordbench/diagnostics/classification/top_errors.py
tools/diagnostics/diag_core.py
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

A branch MUST NOT:

- create stubs or empty models to satisfy imports;
- move an owned symbol into a consumer;
- weaken or delete assertions solely to obtain a green test run;
- introduce a new package-wide eager facade;
- restore Albanian or other language-specific values to framework code;
- make a profile, catalog or remembered state mandatory for basic language loading;
- edit another branch's source write set;
- regenerate repository-wide manifests or documentation before integration.

#### 17.1.5 Integration order

Branches may be implemented concurrently, but integration follows this dependency order:

```text
0. this lock
1. S18-B14 pytest collection
2. owner/model and import-order branches: B02, B06, B07, B10, B11, B12, B16
3. diagnostics contract consumer: B03
4. reviewed project facades: B17
5. consumer/runtime branches: B04, B05, B08, B09, B13
6. diagnostics launcher: B01
7. repository documentation and manifest: B15
8. full collection, import, contract, component and diagnostics smoke verification
```

`B03` is integrated after `B16` so its diagnostics imports and directly owned tests can execute against an importable pattern registry. `B17` is integrated after `B02` and before `B04` and `B05`. `B08` is integrated after `B03`; profile command behavior in `B05` and lifecycle behavior in `B13` are reviewed together before either is declared final.

#### 17.1.6 Branch acceptance record

Every branch handoff MUST include:

```text
branch ID:
snapshot baseline:
files changed or created:
IFC-WB contracts applied:
public symbols added, restored or removed:
compatibility aliases retained:
tests executed and exact result:
collection/import result:
files intentionally not changed:
remaining conflicts or integration dependencies:
```

A branch is rejected when its diff includes an unassigned source file, changes a frozen contract without a lock revision, or reports success by skipping the owner tests that define its public surface.

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
[ ] language probe accepts one explicit file or directory path
[ ] language probe delegates enumeration and filtering to source selection
[ ] language probe does not launch GF or subprocesses directly
[ ] one immutable ResolvedLanguageContext gates runtime creation
[ ] one effective GF path is reused across GF consumers
[ ] optional validation profiles cannot override the resolved language context
[ ] source-ready and scan-ready behavior do not require GF or a profile
[ ] state remembers convenience paths only and re-probes them on load
[ ] stale remembered paths fail safely
[ ] language switching replaces rather than mutates the runtime
[ ] two-language replacement tests show no path, target or baseline contamination
[ ] normal startup does not require rgl-language-catalog.json or language.toml
[ ] state schema and repository APIs agree
[ ] dependency direction remains acyclic
[ ] persisted writes are versioned and atomic
[ ] raw process evidence is preserved
[ ] GF Wordbench has no reverse dependency on gf-portfolio
[ ] contract-changing edits updated tests and owner documents
```
