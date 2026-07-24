# GF Wordbench — Error Handling Model

**Document ID:** `GF-WB-ARCH-ERROR-HANDLING`  
**Status:** Normative architecture reference  
**Applies to:** Framework code, CLI, GUI, GF execution, validation stages, reports, persistence, migrations, and the active project boundary  
**Owner:** GF Wordbench maintainers  
**Last structural review:** 2026-07-24

---

## 1. Purpose

This document defines how GF Wordbench detects, represents, contains, propagates, persists, reports, and presents errors.

Its purpose is to prevent five common failures:

1. a language validation failure being reported as a framework crash;
2. a framework or environment failure being reported as a GF language error;
3. a timeout being hidden as an ordinary non-zero exit;
4. an incomplete or corrupted run being reported as successful;
5. an exception being swallowed without traceable evidence.

The model applies to:

- application startup;
- configuration;
- active-project loading;
- file discovery;
- static scanning;
- fingerprinting;
- GF version probing;
- GF module compilation;
- PGF construction;
- `.gfs` scenarios;
- output normalization;
- gold comparison;
- failure classification;
- previous-run comparison;
- report generation;
- manifest creation;
- state persistence;
- schema migration;
- CLI and GUI presentation.

This document does not define GF diagnostics themselves.

GF remains authoritative for GF syntax, typing, compilation, parsing, linearization, generation, and runtime diagnostics.

GF Wordbench remains authoritative for:

- execution control;
- evidence capture;
- validation criteria;
- error representation;
- failure classification;
- continuation policy;
- aggregation;
- persistence;
- reporting.

---

## 2. Related normative documents

This model must remain consistent with:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/COMPONENT_MAP.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/reference/EXIT_CODES.md
docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Ownership boundaries:

| Subject | Authoritative owner |
|---|---|
| Python provider/consumer error contracts | `INTERFILE_CONTRACT_LOCK.md` |
| External process and GF failure semantics | `EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted fields, enums, and migrations | `PERSISTED_SCHEMA_LOCK.md` |
| Component responsibilities | `COMPONENT_MAP.md` |
| Run budgets and finalization reserve | `ADR-0010-RUN-BUDGET-AND-FINALIZATION.md` |
| Active-language module failures | project contract lock |
| Human explanation and architectural rationale | this document |

This document must not silently introduce a persisted enum or field that contradicts the schema lock.

A required new persisted error field is a coordinated schema change.

---

## 3. Core rule

> Expected validation outcomes are structured results. Exceptions are reserved for failures that prevent a component from honoring its contract.

Examples:

- a GF type error is a structured `FAIL`;
- a gold mismatch is a structured `FAIL`;
- an intentionally omitted stage is `SKIPPED`;
- an unreadable required configuration is an exception at the configuration boundary;
- a missing executable becomes a structured stage `ERROR` after the stage owner catches the launch exception;
- an impossible run-directory creation may abort the run before a valid `RunResult` exists;
- a report failure becomes a finalization error or warning according to artifact criticality.

No component may use exceptions as the normal representation of a failed validation criterion.

No component may convert every exception into an ordinary language `FAIL`.

---

# 4. Orthogonal error dimensions

GF Wordbench separates four dimensions that must not be collapsed.

```text
validation status
execution facts
error kind
diagnostic class
```

They answer different questions.

| Dimension | Question |
|---|---|
| Validation status | Did the validation meet its criterion? |
| Execution facts | What happened while attempting the operation? |
| Error kind | What technical or GF error category was recognized? |
| Diagnostic class | Is the observed language failure direct, downstream, ambiguous, noise, or skipped? |

A fifth dimension, log severity, controls presentation only.

It must not replace structured result fields.

---

## 4.1 Validation status

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

Use `OK` when:

- the required operation was executed;
- the result could be interpreted;
- all required criteria for that operation passed.

A zero process exit code alone is insufficient.

### `FAIL`

Use `FAIL` when:

- the operation executed sufficiently to evaluate its criterion;
- GF Wordbench interpreted the evidence correctly;
- the criterion was not met.

Examples:

- GF type error in the target grammar;
- GF syntax error in the target source;
- missing linearization detected by a completed scenario;
- parse scenario produced no accepted parse;
- required linearization differs from reviewed gold;
- release criterion was evaluated and failed.

### `ERROR`

Use `ERROR` when GF Wordbench could not correctly execute or interpret the validation contract.

Examples:

- executable could not be launched;
- process timed out before a valid result was obtained;
- required source could not be read;
- required raw evidence could not be written;
- required scenario marker contract was malformed;
- output normalization crashed;
- expected artifact was missing after apparent tool success;
- result construction violated a model invariant;
- required report or manifest could not be finalized;
- unsupported required schema;
- corrupted internal state affected the run;
- an unexpected exception crossed a stage boundary.

### `SKIPPED`

Use `SKIPPED` when the operation was intentionally not executed.

Examples:

- compilation disabled by an explicit option;
- optional scenario not selected by the current mode;
- release-only stage omitted in quick mode;
- remaining work not started after explicit cancellation;
- a stage is not applicable to the active project.

A skipped stage must record a reason.

`SKIPPED` must never mean:

- failed silently;
- unsupported but ignored;
- timed out;
- could not launch;
- output was not understood.

---

## 4.2 Execution facts

Execution facts describe control flow.

Canonical execution facts:

```text
launched
completed
timed_out
cancelled
launch_failed
termination_attempted
termination_succeeded
```

These facts may be represented as booleans or a typed execution-state model.

Canonical conceptual states:

```text
completed
timed_out
cancelled
launch_failed
not_started
```

Rules:

- `cancelled` is not a validation status;
- `timed_out` is not a GF diagnostic class;
- `launch_failed` is not a GF syntax error;
- `not_started` normally maps to `SKIPPED`;
- an interrupted required operation normally maps to `ERROR`;
- a process may complete with a non-zero exit and still be a normal validation `FAIL`;
- a process may complete with exit code zero and still yield `FAIL` or `ERROR`.

When execution facts are persisted, their schema is governed by `PERSISTED_SCHEMA_LOCK.md`.

Until a fact is explicitly available in the persisted schema, readers must not infer it from unrelated text fields.

---

## 4.3 Error kind

Canonical persisted error kinds currently include:

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

Meaning:

| Error kind | Meaning |
|---|---|
| `OK` | No recognized error |
| `TYPE` | GF type or unification failure |
| `SYNTAX` | GF source syntax failure |
| `INTERNAL` | Internal GF or runtime failure |
| `TIMEOUT` | Operation exceeded its configured time |
| `SCRIPT` | Scenario, script, marker, or orchestration-script failure |
| `CONFIG` | Invalid, missing, incompatible, or contradictory configuration |
| `IO` | Filesystem or stream operation failed |
| `TOOL` | External executable, artifact contract, version, or tool integration failure |
| `OTHER` | Interpreted failure that does not fit a more specific supported kind |

Rules:

- error kind must describe the recognized technical category;
- it must not encode direct/downstream causality;
- it must not encode severity;
- `OTHER` is allowed but must not become the default for avoidable parser gaps;
- adding or redefining an error kind is a model and schema contract change when serialized.

Canonical internal failure reasons may be more specific:

```text
launch_failure
tool_failure
artifact_failure
contract_failure
normalization_failure
gold_mismatch
configuration_failure
unsupported_version
schema_failure
report_failure
migration_failure
```

These internal reasons must map deterministically to the locked persisted `error_kind`.

Canonical mapping:

| Internal failure reason | Persisted error kind |
|---|---|
| `launch_failure` | `TOOL` |
| `tool_failure` without specific GF kind | `TOOL` or `OTHER` |
| `artifact_failure` | `TOOL` |
| `contract_failure` | `SCRIPT` or `TOOL`, according to owner |
| `normalization_failure` | `SCRIPT` |
| `gold_mismatch` | `OTHER` |
| `configuration_failure` | `CONFIG` |
| `unsupported_version` | `TOOL` or `CONFIG` |
| `schema_failure` | `CONFIG` |
| `report_failure` | `IO` or `SCRIPT` |
| `migration_failure` | `CONFIG` or `IO` |

The internal reason must not be serialized as a new public enum until the schema is updated deliberately.

---

## 4.4 Diagnostic class

Canonical causal classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### `ok`

No causal failure classification is needed.

### `direct`

The available evidence identifies the current project subject as a root cause or primary failing subject.

### `downstream`

The current subject failed because one or more other known project subjects failed first.

`blocked_by` identifies the root blockers.

### `ambiguous`

The validation failed, but available evidence does not reliably distinguish direct from downstream causality.

### `noise`

The subject is excluded or the evidence is intentionally non-actionable under the active validation policy.

### `skipped`

The subject was intentionally not validated.

Rules:

- diagnostic class applies primarily to project validation relationships;
- process utilities must not assign it;
- report writers must not recompute it;
- framework failures must not invent a fake project causal class;
- an `ERROR` may remain `ambiguous` when no valid project causality exists;
- a dedicated framework error is represented through status and error kind, not by silently expanding causal semantics.

---

## 4.5 Log severity

Canonical log severities:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Log severity is presentation metadata.

It does not determine validation status.

Examples:

- a `FAIL` may be logged at `ERROR`;
- an optional version-probe failure may be a `WARNING`;
- a successful run with a deprecated configuration may be `OK` with warnings;
- a fatal run-path creation exception may be `CRITICAL`.

---

# 5. Result envelope

Every stage result carries enough structured context to be understood without parsing a human report.

Canonical shared error envelope:

```python
@dataclass(frozen=True, slots=True)
class ErrorInfo:
    code: str
    error_kind: str
    message: str
    detail: str
    stage: str
    operation: str
    subject: str | None
    retryable: bool
    evidence_paths: tuple[str, ...]
    cause_type: str | None
```

This is an architectural model.

Its persisted form is governed by `app/models.py` and the persisted schema.

Minimum semantic fields:

| Field | Purpose |
|---|---|
| `code` | Stable machine-oriented error code |
| `error_kind` | Locked broad category |
| `message` | Concise primary explanation |
| `detail` | Additional bounded context |
| `stage` | Owner stage |
| `operation` | Attempted operation |
| `subject` | File, scenario, artifact, or configuration subject |
| `retryable` | Whether repeating after environmental correction may succeed |
| `evidence_paths` | Raw or derived evidence |
| `cause_type` | Exception class or upstream failure type when safe |

Rules:

- `message` must be useful without exposing secrets;
- `detail` must not contain complete environment dumps;
- error codes must be stable once external consumers use them;
- raw traceback text belongs in diagnostic logs, not normal summary fields;
- evidence paths must be owned, normalized, and traceable.

---

# 6. Error-code namespace

Stable error codes use:

```text
GF-WB-<DOMAIN>-<NUMBER>
```

Canonical domains:

```text
CONFIG
PROJECT
PATH
IO
PROCESS
GF
SCAN
SCENARIO
GOLD
SCHEMA
REPORT
MANIFEST
STATE
MIGRATION
CONTRACT
INTERNAL
```

Examples:

```text
GF-WB-CONFIG-001   invalid validation mode
GF-WB-PROJECT-002  missing configured entrypoint
GF-WB-PROCESS-001  executable not found
GF-WB-PROCESS-002  process timeout
GF-WB-GF-001       GF type failure
GF-WB-SCENARIO-003 missing required end marker
GF-WB-GOLD-001     normalized output differs from gold
GF-WB-REPORT-002   summary JSON write failed
GF-WB-SCHEMA-001   unsupported schema major version
```

Error-code rules:

- never reuse a retired code for another meaning;
- do not encode dynamic paths in the code;
- codes identify categories, not full messages;
- a code change is a contract change once consumed externally;
- human messages may improve without changing the code if semantics remain stable.

---

# 7. Exception hierarchy

GF Wordbench exposes one small, deliberate exception hierarchy.

Canonical hierarchy:

```python
GFWordbenchError
├── ConfigurationError
│   ├── ProjectConfigurationError
│   ├── UnsupportedVersionError
│   └── SchemaValidationError
├── ContractViolationError
├── InfrastructureError
│   ├── PathSecurityError
│   ├── EvidenceIOError
│   └── ProcessLaunchError
├── StageExecutionError
│   ├── ScanExecutionError
│   ├── CompileExecutionError
│   ├── ScenarioExecutionError
│   └── NormalizationError
├── ArtifactError
├── ReportError
├── MigrationError
└── CancellationRequested
```

The hierarchy must remain small.

Do not create one exception class per error message.

### 7.1 Public exception contract

Public component boundaries may document:

```text
ConfigurationError
FileNotFoundError
PermissionError
ContractViolationError
GFWordbenchError
```

Internal third-party or standard-library exceptions are wrapped with their cause preserved:

```python
raise EvidenceIOError("Could not write compile stderr") from exc
```

### 7.2 Cause preservation

Wrapped exceptions must preserve:

- original exception type;
- traceback in debug evidence;
- concise public message;
- operation and subject;
- path when safe;
- stage owner.

Do not replace a useful cause with a generic `"Something went wrong"`.

### 7.3 Exception sanitization

User-facing messages must remove:

- credentials;
- tokens;
- secret environment values;
- command arguments marked secret;
- full environment dumps;
- unrelated personal data.

Paths are allowed when needed for correction, but portable reports may redact known private prefixes.

---

# 8. Result versus exception decision

Use this decision sequence:

```text
Did the component receive a valid request?
    no  → raise configuration or contract exception

Could the component start its owned operation?
    no  → raise internally, then stage owner converts to ERROR result if a run exists

Did the operation execute enough to evaluate its criterion?
    no  → ERROR

Was the operation intentionally omitted?
    yes → SKIPPED

Could the evidence be interpreted reliably?
    no  → ERROR

Did the criterion pass?
    yes → OK
    no  → FAIL
```

Examples:

| Event | Representation |
|---|---|
| GF reports a type mismatch | `FAIL`, `TYPE` |
| GF reports a syntax error | `FAIL`, `SYNTAX` |
| `gf.exe` missing | stage `ERROR`, `TOOL` |
| process timeout | stage `ERROR`, `TIMEOUT` |
| required `.pgf` missing after zero exit | `ERROR`, `TOOL` |
| required scenario marker missing | `ERROR`, `SCRIPT` |
| gold differs after valid normalization | `FAIL`, `OTHER` |
| normalizer crashes | `ERROR`, `SCRIPT` |
| optional scenario not selected | `SKIPPED`, `OK` or documented neutral kind |
| state JSON malformed | warning, safe defaults |
| required `project.toml` malformed | fatal configuration error |
| previous summary unreadable | warning; current validation continues |
| `summary.json` cannot be written | finalization `ERROR`, `IO` |
| optional detail report cannot be written | warning unless policy makes it required |

---

# 9. Stage boundary rule

Each stage owns conversion from internal exceptions to structured stage outcomes.

```text
infrastructure raises precise exception
        ↓
stage owner catches expected operational exception
        ↓
stage owner preserves evidence
        ↓
stage owner returns ERROR result
        ↓
orchestrator applies continuation and aggregation policy
```

Examples:

- `process_utils.py` may raise `ProcessLaunchError`;
- `compiler.py` catches it and returns a compile result with `ERROR`;
- `audit_core.py` must not relabel it as a GF syntax failure;
- report writers receive the completed result and do not inspect the original exception.

Unexpected programming errors may cross the stage boundary to the orchestrator after best-effort evidence capture.

---

# 10. Error propagation levels

GF Wordbench has five propagation levels.

## 10.1 Level 1 — Local recoverable warning

The operation remains valid.

Examples:

- unknown newer GF version in non-strict mode;
- previous-run summary unavailable;
- optional detail report unavailable;
- malformed disposable UI state;
- optional CPU metrics unavailable.

Action:

- record warning;
- preserve context;
- continue;
- do not alter validation status unless the warning affects a required criterion.

## 10.2 Level 2 — Subject-level structured failure

One file or scenario fails, but the run can continue.

Examples:

- GF type error in one file;
- one source unreadable;
- one scenario gold mismatch;
- one scenario times out;
- one artifact missing for one subject.

Action:

- create `FileResult` or `ScenarioResult`;
- preserve evidence;
- continue according to mode and fail-fast policy;
- aggregate later.

## 10.3 Level 3 — Stage-level error

A required stage cannot execute correctly for some or all subjects.

Examples:

- shared GF executable cannot launch;
- scenario runner configuration is invalid;
- output root becomes unwritable;
- diagnostic parser fails globally;
- project source root disappears.

Action:

- mark affected subjects or stage `ERROR`;
- stop dependent stages;
- continue independent finalization if safe;
- overall status becomes `ERROR` when the stage is required.

## 10.4 Level 4 — Run-finalization error

Validation may have run, but required evidence cannot be finalized.

Examples:

- `summary.json` write fails;
- manifest cannot be generated;
- master evidence cannot be preserved;
- run result violates serialization schema.

Action:

- preserve any already written raw evidence;
- mark final outcome `ERROR`;
- return a non-success CLI exit;
- GUI must state that validation evidence is incomplete;
- do not claim release readiness.

## 10.5 Level 5 — Fatal application error

No valid run can be established or safely represented.

Examples:

- invalid startup arguments;
- active project cannot be loaded;
- run directory cannot be created;
- internal model construction fails before run ownership exists;
- security boundary violation;
- uncaught programming error before run initialization.

Action:

- CLI returns configuration or runtime error exit;
- GUI shows a sanitized error dialog;
- traceback is available only in debug evidence;
- no false `RunResult` is fabricated.

---

# 11. Continuation policy

Continuation depends on:

- whether the operation is required;
- whether downstream work remains meaningful;
- whether evidence can still be trusted;
- selected validation mode;
- explicit fail-fast policy.

## 11.1 Default policy

GF Wordbench collects as much independent evidence as safely possible.

It does not stop after the first ordinary language failure.

It stops or skips dependent work when:

- prerequisites are unavailable;
- process execution is unsafe;
- project identity is invalid;
- shared GF path is invalid;
- required evidence cannot be preserved;
- continuing would create misleading results.

## 11.2 Independent versus dependent stages

Examples:

- one file compile failure does not prevent scanning another independent file;
- failure of a required grammar entrypoint may prevent scenarios that load it;
- version-probe warning may not prevent a quick compile when policy permits;
- missing source root prevents file selection, compilation, and scenarios;
- report detail failure does not prevent writing `summary.json`;
- `summary.json` failure prevents a valid machine-readable finalized run.

## 11.3 Required stage

A required stage error makes overall status `ERROR`.

A required stage validation failure makes overall status `FAIL`.

## 11.4 Optional stage

An optional stage may produce `FAIL` or `ERROR` without changing overall status when the active mode and project configuration explicitly define it as non-gating.

The result must still be visible.

Optional must not mean hidden.

## 11.5 Fail-fast

Fail-fast may be offered for development speed.

It must not change the meaning of completed results.

Unexecuted remaining subjects become `SKIPPED` with an explicit fail-fast reason.

Release validation prefers complete evidence over fail-fast unless execution safety requires stopping.

## 11.6 Run budget and finalization reserve

Every run has:

```text
one global run budget
explicit stage budgets
one protected finalization reserve
```

The orchestrator computes each stage budget from the remaining global budget without allocating the protected finalization reserve to normal stage execution.

When the usable execution budget is exhausted, insufficient, or cancelled:

1. no new validation work starts;
2. active child processes receive controlled termination;
3. partial stdout, stderr, timing, and artifact evidence are preserved;
4. not-started dependent work becomes `SKIPPED` with an explicit reason;
5. interrupted required work becomes `ERROR`;
6. the run enters finalization using the protected reserve.

Finalization is idempotent and writes terminal results atomically or through a recoverable replacement protocol.

A run cannot be `OK` or release-ready when:

- required work is incomplete;
- required evidence is missing;
- child-process termination remains unresolved;
- required summary or manifest publication fails;
- finalization cannot establish a coherent terminal state.

These rules are governed by `docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md`.

---

# 12. Status precedence

For one subject, precedence is:

```text
ERROR
FAIL
SKIPPED
OK
```

This precedence is for aggregation, not automatic field overwriting.

Examples:

- scanner `ERROR` plus compile `OK` gives subject `ERROR`;
- scan warning plus compile `OK` gives subject `OK` with findings;
- compile `FAIL` plus optional documentation warning gives subject `FAIL`;
- compile intentionally skipped plus scan `OK` gives the file result defined by mode policy, usually `SKIPPED` for compile validation rather than false `OK`.

A subject result preserves stage sub-results rather than discarding them into one aggregate status.

---

# 13. Overall run outcome

Canonical overall status:

```text
OK
FAIL
ERROR
```

Rules:

### `OK`

- every required criterion passed;
- no required stage is `ERROR`;
- no required stage is incomplete;
- required run artifacts exist.

### `FAIL`

- required validations completed sufficiently;
- at least one required criterion failed;
- no higher-priority required framework error invalidated interpretation.

### `ERROR`

- at least one required stage could not execute or be interpreted;
- required evidence is incomplete;
- required run artifacts could not be produced;
- the run result cannot support a reliable validation claim.

When both `FAIL` and `ERROR` exist, overall status is `ERROR`.

A run may still contain valuable language failures when overall status is `ERROR`.

Reports must show both.

---

# 14. Cancellation model

Cancellation is a control outcome, not a validation result.

Cancellation behavior:

1. record cancellation request;
2. stop launching new external processes;
3. attempt controlled termination of the owned active process;
4. preserve partial stdout and stderr;
5. mark the interrupted operation `ERROR` and record cancellation explicitly in execution evidence;
6. mark not-started operations `SKIPPED` with reason `cancelled`;
7. finalize partial evidence when safe;
8. return a distinct CLI cancellation exit code;
9. show `Cancelled` in the GUI without calling the project invalid.

Until cancellation has a dedicated persisted schema field, it must be recorded explicitly in available execution evidence and must not be inferred from `FAIL`.

CLI cancellation exit code:

```text
130
```

A persisted cancellation field requires a coordinated schema update.

---

# 15. Process execution errors

## 15.1 Process request validation

Before launch, validate:

- executable path;
- argument sequence;
- working directory;
- timeout;
- output paths;
- environment overrides;
- input encoding;
- path containment where required.

Invalid requests are configuration or contract errors.

## 15.2 Launch failure

Examples:

- executable missing;
- permission denied;
- invalid executable format;
- working directory missing;
- operating-system launch failure.

Representation:

```text
validation status: ERROR
error kind: TOOL
execution fact: launch_failed
```

The message must not claim that GF rejected the grammar.

## 15.3 Timeout

Representation:

```text
validation status: ERROR
error kind: TIMEOUT
timed_out: true
```

Required evidence:

- configured timeout;
- command;
- working directory;
- duration;
- termination attempt;
- partial stdout path;
- partial stderr path.

A synthetic timeout exit code may be retained for legacy compatibility, but `timed_out` is authoritative.

Do not identify timeout solely from an exit-code sentinel.

## 15.4 Non-zero exit

A non-zero exit is evidence.

Interpretation sequence:

1. preserve streams;
2. parse recognized diagnostics;
3. verify whether the tool completed enough to interpret;
4. map known language diagnostics to `FAIL`;
5. map launch, timeout, internal contract, or evidence failures to `ERROR`;
6. retain unknown diagnostics as `OTHER` without discarding text.

## 15.5 Zero exit

Zero exit does not override:

- fatal diagnostic text;
- missing required artifact;
- missing scenario marker;
- incomplete scenario;
- normalization failure;
- gold mismatch;
- contract violation.

---

# 16. GF version-probe policy

Version probing is a validation of the external-tool contract.

Possible outcomes:

| Outcome | Default handling |
|---|---|
| supported tested version | continue |
| supported but untested newer version | warning, continue unless strict |
| below minimum supported version | configuration/tool `ERROR` |
| known incompatible version | `ERROR` |
| probe intentionally disabled | `SKIPPED` with explicit configuration |
| probe command failed | requiredness depends on mode and strictness |
| version output unparseable | `ERROR` when version gating is required |

Release mode requires a valid interpretable version unless the release policy explicitly permits otherwise.

Quick or diagnostic mode may continue after a probe warning only when:

- the executable still launches for the requested operation;
- the uncertainty is recorded;
- strict mode is disabled;
- no version-specific command assumption is unsafe.

---

# 17. File-selection errors

## 17.1 Global selection errors

Examples:

- source root missing;
- invalid include regex;
- invalid exclude regex;
- target outside project root;
- project configuration inconsistent.

These normally abort the validation plan with configuration `ERROR`.

## 17.2 Per-file selection errors

Examples:

- one file disappears after discovery;
- one path cannot be normalized;
- one file is not readable.

Create a subject-level `ERROR` when a stable subject identity exists.

Continue with other independent files when safe.

## 17.3 Exclusion

A configured exclusion is not an error.

It is recorded as noise/excluded evidence, not `FAIL`.

---

# 18. Scanner errors

Scanner findings and scanner execution errors are distinct.

## 18.1 Findings

Static findings are structured counts or diagnostics.

They do not automatically make GF compilation fail.

Project or release policy may define selected findings as gating criteria.

## 18.2 Scanner execution error

Examples:

- file cannot be read;
- decoding policy fails;
- scanner invariant fails;
- scan log cannot be written.

Representation:

```text
status: ERROR
error kind: IO or SCRIPT
```

The orchestrator may still attempt compilation when:

- source bytes are readable by the compiler path;
- the scanner failure does not make execution unsafe;
- mode policy allows partial evidence.

The aggregated subject remains `ERROR` because required scanner evidence is incomplete.

---

# 19. Fingerprint errors

A fingerprint is evidence of source identity.

Failure to create a required fingerprint is not a language validation failure.

Representation:

```text
status: ERROR
error kind: IO or SCRIPT
```

Do not silently substitute:

```text
size_bytes = 0
hash = ""
timestamp = ""
```

as though those values were a valid fingerprint.

A degraded placeholder may exist internally only when it is explicitly marked invalid and the run outcome reflects incomplete evidence.

Release claims must not depend on an invalid fingerprint.

---

# 20. Compilation errors

Compilation handling belongs to `app/audit/compiler.py`.

## 20.1 GF type or syntax failure

Representation:

```text
status: FAIL
error kind: TYPE or SYNTAX
```

Preserve:

- command;
- GF version;
- source path;
- stdout;
- stderr;
- exit code;
- duration;
- primary message;
- detailed diagnostic;
- produced artifacts.

## 20.2 GF internal error

An internal GF failure normally means the requested validation could not be completed reliably.

Canonical representation:

```text
status: ERROR
error kind: INTERNAL
```

The classifier may still identify the triggering subject when evidence is strong, but reports must not present the issue as an ordinary language type failure.

## 20.3 Missing artifact

If successful compilation requires an artifact and it is absent:

```text
status: ERROR
error kind: TOOL
internal reason: artifact_failure
```

## 20.4 Stale artifact

A stale `.gfo` or `.pgf` must not satisfy the current run.

When freshness cannot be established:

```text
status: ERROR
error kind: TOOL
```

## 20.5 No-compile mode

Intentional no-compile:

```text
compile status: SKIPPED
timed_out: false
error kind: OK
reason: explicit no-compile configuration
```

Do not fabricate exit code success as evidence that compilation passed.

---

# 21. PGF-build errors

PGF build is a release-significant stage.

Failure modes:

```text
entrypoint configuration failure
launch failure
timeout
GF compile failure
missing PGF
empty PGF
wrong artifact path
artifact collision
manifest registration failure
```

Mapping:

| Failure | Status |
|---|---|
| GF reports language compile/type failure | `FAIL` |
| launch/timeout | `ERROR` |
| missing or empty PGF after apparent success | `ERROR` |
| artifact collision without explicit policy | `ERROR` |
| manifest cannot register required PGF | run finalization `ERROR` |

Individual `.gfo` success cannot override a failed PGF release build.

---

# 22. Scenario errors

Scenario handling belongs to `app/audit/scenario_runner.py`.

## 22.1 Scenario configuration error

Examples:

- duplicate scenario ID;
- missing required script;
- missing required entrypoint;
- path outside project root;
- invalid timeout;
- unsupported command policy.

Representation:

```text
status: ERROR
error kind: CONFIG or SCRIPT
```

## 22.2 Scenario launch or timeout

Representation:

```text
status: ERROR
error kind: TOOL or TIMEOUT
```

## 22.3 GF validation failure inside scenario

Examples:

- required parse absent;
- expected missing-linearization list non-empty;
- required linearization command reports project error.

When evidence is valid and interpretable:

```text
status: FAIL
specific GF error kind when recognized
```

## 22.4 Marker failure

A missing, duplicated, malformed, or unclosed required marker means GF Wordbench cannot prove that the scenario completed its contract.

Representation:

```text
status: ERROR
error kind: SCRIPT
```

Do not treat it as a normal gold mismatch.

## 22.5 Normalization failure

Representation:

```text
status: ERROR
error kind: SCRIPT
```

Raw evidence remains authoritative and immutable.

## 22.6 Gold mismatch

When:

- scenario execution completed;
- markers are valid;
- normalization succeeded;
- gold exists and is valid;
- normalized content differs;

representation is:

```text
status: FAIL
error kind: OTHER
internal reason: gold_mismatch
```

## 22.7 Missing gold

Required gold missing:

```text
status: ERROR
error kind: CONFIG
```

Optional gold absent with explicit assertion strategy:

```text
gold_match: null
```

Normal validation must not create the file.

---

# 23. Diagnostic parsing errors

The diagnostic normalizer must preserve raw evidence before parsing.

Possible outcomes:

1. recognized diagnostic;
2. no diagnostic and successful operation;
3. unknown diagnostic with non-zero exit;
4. parser failure.

Unknown diagnostic is not automatically parser failure.

Use:

```text
error kind: OTHER
primary message: first stable non-noise diagnostic line
```

Parser failure means the parser itself could not honor its contract.

Use:

```text
status: ERROR
error kind: SCRIPT
```

Do not hide a parser failure behind the original GF exit code.

Do not allow compiler, classifier, reports, and GUI to implement separate fallback parsers.

---

# 24. Classification errors

The classifier consumes structured evidence.

It does not execute GF.

## 24.1 Ambiguity

Lack of sufficient causal evidence is:

```text
diagnostic_class: ambiguous
```

It is not a framework error by itself.

## 24.2 Classifier exception

If classification logic crashes or violates an invariant:

- preserve pre-classification results;
- mark affected classification as unavailable;
- overall required interpretation becomes `ERROR`;
- use `SCRIPT` or a documented internal error representation;
- do not silently leave misleading default classes.

## 24.3 Blocker cycles

A blocker cycle is a classification contract error.

The classifier must:

- detect it;
- preserve the cycle members;
- avoid infinite recursion;
- classify affected results as ambiguous;
- emit an error or warning according to whether classification is release-required.

---

# 25. Previous-run comparison errors

Diff is supplementary evidence unless explicitly made a release gate.

Cases:

| Event | Handling |
|---|---|
| no previous run | empty diff, no error |
| previous summary absent | empty diff or warning |
| previous summary malformed | warning, current run continues |
| unsupported previous major schema | warning or strict comparison error |
| current summary invalid | current run `ERROR` |
| diff algorithm invariant failure | warning or run `ERROR` if diff is required |

A previous-run problem must not relabel current language results.

Diff errors belong to comparison evidence.

---

# 26. Report-generation errors

Reports consume a completed result.

They must not repair missing validation evidence by rerunning stages.

## 26.1 Critical reports

Critical run artifacts:

```text
summary.json
manifest.json
master evidence required by policy
```

Failure to produce a critical artifact makes the overall outcome `ERROR`.

## 26.2 Standard human reports

Expected standard reports:

```text
summary.md
AI_READY.md
top_errors.txt
aggregate logs
details/
```

Their requiredness is defined by the report and release policy.

Default artifact requirements:

- `summary.md`: required for a normal finalized run;
- `AI_READY.md`: required when AI packet generation is enabled;
- `top_errors.txt`: required but may be empty;
- aggregate logs: required when source logs exist;
- per-result details: optional unless configured required.

## 26.3 Report failure handling

For each writer:

1. catch the writer-specific exception;
2. record writer name and artifact path;
3. preserve other reports;
4. update artifact availability;
5. determine criticality;
6. set finalization status appropriately;
7. retry only when the operation is known idempotent and retry policy is explicit.

Do not use:

```python
except Exception:
    pass
```

for required reports.

## 26.4 Manifest ordering

The manifest is written after final artifact bytes are stable.

If a required artifact changes after hashing, finalization is invalid.

---

# 27. Persistence errors

## 27.1 State file

State is disposable convenience data.

Read failure:

- warn;
- use safe defaults;
- optionally quarantine malformed state;
- do not block CLI operation.

Write failure:

- warn in normal use;
- do not claim preferences were saved;
- do not alter audit validity.

## 27.2 Project configuration

Project configuration is authoritative.

Read or validation failure:

- fatal configuration error;
- no language validation starts.

## 27.3 Run summary

`summary.json` is the primary machine record.

Write or schema-validation failure:

- run finalization `ERROR`;
- preserve raw evidence;
- do not claim a complete run.

## 27.4 Atomic writes

On failure:

- retain previous valid destination;
- retain or remove temporary file according to recovery policy;
- report the destination and temporary path safely;
- do not leave truncated canonical files.

## 27.5 Partial run directories

A partial run directory must be identifiable as incomplete.

Canonical mechanisms:

```text
finalization state in manifest or summary
temporary run marker
absence of valid manifest
explicit master-log finalization failure
```

Previous-run discovery must ignore incomplete runs unless diagnostic recovery explicitly requests them.

---

# 28. Schema and migration errors

## 28.1 Unsupported schema

Unknown major version:

```text
ConfigurationError or SchemaValidationError
error kind: CONFIG
```

Do not guess.

## 28.2 Invalid legacy input

Migration may continue only when required meaning is recoverable.

Losses and warnings must be explicit.

## 28.3 Migration failure

Rules:

- source remains untouched;
- destination is not published as valid;
- temporary output is quarantined or removed;
- warning and loss records are preserved;
- operation exits non-successfully.

## 28.4 Reader fallback

Fallbacks must be named aliases with tests.

Example:

```text
ai_brief_path → ai_ready
file → quick
all → diagnostic
```

Do not accept arbitrary unknown fields as equivalent to canonical ones.

---

# 29. Configuration errors

Configuration validation occurs before dependent work begins.

Categories:

```text
missing required value
invalid type
invalid enum
invalid path
path outside approved root
contradictory flags
unsupported version
duplicate identifier
missing required project asset
unsafe external command policy
```

CLI behavior:

- explain the invalid field;
- return invalid-arguments/configuration exit;
- avoid traceback by default.

GUI behavior:

- identify the field;
- retain user input for correction;
- avoid starting a run;
- show technical details only on demand.

Configuration errors must not be converted into per-file language failures.

---

# 30. Security errors

Security boundary violations are errors, not warnings.

Examples:

- path traversal outside approved root;
- untrusted shell escape;
- symlink escaping run root;
- attempt to overwrite source as a gold update side effect;
- executable path replaced unexpectedly;
- secret included in report;
- unsafe archive extraction;
- artifact path collision with protected file.

Default handling:

- stop the unsafe operation;
- preserve non-secret evidence;
- mark run or command `ERROR`;
- use a security-specific stable code;
- do not retry automatically.

---

# 31. CLI error presentation

CLI output has two channels:

```text
stdout → normal result and artifact locations
stderr → warnings, configuration failures, runtime errors
```

Canonical exit codes:

```text
0   completed; required criteria passed
1   completed; required validation failed
2   invalid arguments or configuration
3   runtime, framework, evidence, or finalization error
130 cancelled
```

Rules:

- `FAIL` returns `1`;
- `ERROR` returns `3`;
- invalid pre-run configuration returns `2`;
- warning-only run follows final validation status;
- never return `0` when required `summary.json` or manifest finalization failed;
- print one concise primary message;
- print evidence path or run directory when available;
- expose traceback only under explicit debug option.

---

# 32. GUI error presentation

The GUI must distinguish:

```text
validation failed
run error
configuration invalid
warning
cancelled
```

Presentation rules:

- validation failures appear in result views, not generic crash dialogs;
- configuration errors focus the affected control when possible;
- runtime errors show a concise explanation and evidence location;
- optional technical details may include sanitized traceback;
- cancellation must not be presented as grammar failure;
- failed report generation must state which artifacts are unavailable;
- GUI state errors must not prevent opening the application.

The GUI must not invent different status semantics from the CLI.

---

# 33. Logging and evidence

## 33.1 Raw evidence

Raw process evidence includes:

```text
structured command
working directory
selected executable
environment overrides, redacted
start time
finish time
duration
exit code
execution facts
stdout
stderr
produced artifacts
```

Raw stdout and stderr must remain separate.

## 33.2 Master log

The master log records orchestration events.

Canonical fields:

```text
timestamp
run_id
stage
operation
subject
event
status
error_code
message
evidence_path
```

Use structured logging internally where practical.

A human-readable rendering may be generated.

## 33.3 Tracebacks

Tracebacks are useful for framework debugging.

They are:

- retained for unexpected errors;
- written to a debug/error evidence artifact;
- excluded from normal concise reports;
- sanitized when containing secrets;
- associated with the stage and error code.

## 33.4 Message limits

User-facing error messages must be bounded.

Raw evidence may be large and is protected by output-size limits.

Truncation must record:

```text
truncated = true
original size when known
retained size
reason
```

---

# 34. Retry policy

Automatic retries are prohibited by default.

Retry is allowed only when:

- the operation is idempotent;
- retry cannot mutate source or gold unexpectedly;
- failure is classified as transient;
- retry count is bounded;
- each attempt is recorded;
- complete evidence identifies all attempts;
- timeout budget remains bounded.

Potential retryable operations:

```text
read-only version probe
transient report write after directory creation race
read-only artifact existence check
```

Normally non-retryable without explicit policy:

```text
GF compilation
PGF build
scenario execution
gold update
schema migration
project reset
```

A retry must not hide the original failure.

---

# 35. Warning model

Warnings do not automatically change validation status.

Canonical warning record:

```python
@dataclass(frozen=True, slots=True)
class WarningInfo:
    code: str
    message: str
    stage: str
    subject: str | None
    evidence_paths: tuple[str, ...]
```

Warnings cover:

- deprecated configuration;
- untested newer GF version;
- unavailable previous-run diff;
- malformed disposable state;
- optional report failure;
- optional scenario failure;
- recoverable legacy alias;
- bounded evidence truncation.

Warnings must be visible in:

- machine summary when schema supports them;
- Markdown summary;
- AI-ready packet when relevant;
- GUI warning area;
- CLI stderr or the closing warning count.

Do not store warnings only in transient console text.

---

# 36. Required versus optional evidence

Evidence criticality must be explicit.

## Required for a completed external process

```text
command
working directory
exit code or launch failure
timeout fact
duration
stdout path
stderr path
```

## Required for a compiled subject

```text
source identity
compile request
compile result
primary diagnostic when failed
artifact check result
```

## Required for a scenario

```text
scenario identity
script path or hash
command
raw streams
marker result
normalization result
gold result when applicable
```

## Required for a finalized run

```text
RunResult
summary.json
manifest.json
overall status
artifact availability
finalization result
```

Missing required evidence is `ERROR`.

---

# 37. Error aggregation

## 37.1 Counts

Canonical totals distinguish:

```text
files_ok
files_fail
files_error
files_skipped
scenarios_ok
scenarios_fail
scenarios_error
scenarios_skipped
```

Do not combine `FAIL` and `ERROR` into one count.

## 37.2 Top errors

Top-error aggregation includes actionable failures.

Canonical ordering:

```text
descending count
then error kind
then normalized message
```

Do not aggregate:

- empty messages;
- secrets;
- full tracebacks;
- unique temporary paths as distinct errors when normalization can safely remove them;
- warnings into error counts unless the report says so explicitly.

## 37.3 Direct/downstream counts

Direct/downstream/ambiguous counts apply to causal language failure classification.

They must not be used as substitutes for `files_error`.

---

# 38. Public API behavior

Public service functions document:

- accepted exceptions;
- structured failure returns;
- side effects;
- evidence written before failure;
- cancellation behavior;
- idempotence;
- retry safety.

Examples:

```python
run_audit(run_config) -> RunResult
compile_file(...) -> CompileSummary
run_scenario(...) -> ScenarioResult
load_project_config(...) -> ProjectConfig
```

Expected validation failures must not escape from `compile_file` or `run_scenario` as raw exceptions.

Configuration and contract violations may raise before a stage result can be valid.

---

# 39. Anti-patterns

The following are prohibited.

## 39.1 Broad conversion to language failure

```python
try:
    ...
except Exception as exc:
    return FileResult(status="FAIL", error_kind="SCRIPT")
```

This mislabels framework, I/O, configuration, and programming errors.

## 39.2 Silent swallow

```python
try:
    write_required_report()
except Exception:
    pass
```

## 39.3 Exit-code-only interpretation

```python
status = "OK" if exit_code == 0 else "FAIL"
```

## 39.4 Stdout-only parsing

```python
diagnostic = parse(stdout)
```

while stderr is ignored.

## 39.5 Empty placeholder evidence

```python
fingerprint = SourceFingerprint(size_bytes=0, hash="")
```

without marking invalid evidence.

## 39.6 Report-time execution

```python
if evidence_missing:
    rerun_gf()
```

inside a report writer.

## 39.7 GUI-specific semantics

```python
# GUI treats timeout as warning, CLI treats it as failure
```

## 39.8 Hidden fallback

```python
if configured_gf_missing:
    use_any_gf_from_PATH()
```

without recording the resolved executable.

## 39.9 Gold auto-repair

```python
if gold_missing:
    write_current_output_as_gold()
```

## 39.10 Message parsing as API

A consumer must not determine behavior by matching another component's user-facing exception text.

Use error codes, types, and structured fields.

---

# 40. Legacy compatibility with `gf-audit`

Legacy `gf-audit` summaries and evidence remain readable through the persisted-schema compatibility policy. Canonical Wordbench writers emit only the error semantics defined by this document.

## 40.1 Broad per-file exception catch

A legacy broad catch around scanning, fingerprinting, or compilation may construct a `FAIL` result with `SCRIPT`.

Compatibility readers may ingest that representation, but Wordbench processing must:

- identify the failing stage;
- distinguish framework `ERROR` from language `FAIL`;
- preserve the original cause when available;
- retain completed scan or compile evidence;
- avoid assigning project causality before classification.

## 40.2 Empty fallback fingerprints

A legacy record may contain an empty fallback fingerprint after an exception.

Such a fingerprint is invalid evidence. It must be represented explicitly as unavailable or invalid and cannot satisfy a release criterion.

## 40.3 Timeout sentinels

A legacy process result may use a synthetic timeout exit code.

Compatibility readers may recognize the sentinel, but explicit `timed_out` or execution-state data is authoritative whenever present. Canonical writers persist explicit timeout facts.

## 40.4 Report-writer failures

A legacy run may continue after a report writer exception or suppress a master-log exception.

Wordbench classifies every report as required or optional. Failure to produce a required report makes the run outcome `ERROR`; optional report failure remains visible as a warning or non-gating artifact error.

## 40.5 Version-probe failures

A legacy run may continue after a version-probe exception.

Wordbench applies the configured mode, strictness, minimum version, and command-compatibility rules. Continuing is allowed only when the requested operation remains safe and the uncertainty is recorded.

## 40.6 Exit-code-derived status

A legacy record may derive file status directly from the compile exit code.

Canonical interpretation evaluates all available evidence:

```text
launch
timeout
exit code
fatal diagnostics
artifact contract
interpretation success
```

## 40.7 Write policy

Legacy summaries remain readable according to `docs/PERSISTED_SCHEMA_LOCK.md`. Canonical writers do not emit deprecated aliases or ambiguous legacy representations.

---

# 41. Testing requirements

Test structure:

```text
tests/error_handling/
├── test_status_semantics.py
├── test_exception_mapping.py
├── test_stage_containment.py
├── test_run_aggregation.py
├── test_cancellation.py
├── test_warning_model.py
├── test_cli_exit_codes.py
├── test_gui_error_presentation.py
├── test_report_finalization.py
└── test_error_redaction.py
```

Contract and integration suites also cover error behavior.

## 41.1 Status tests

Test:

- `OK`;
- language `FAIL`;
- framework `ERROR`;
- intentional `SKIPPED`;
- precedence;
- required versus optional stages;
- mixed `FAIL` and `ERROR`;
- overall aggregation.

## 41.2 Process tests

Test:

- executable missing;
- permission denied where practical;
- working directory missing;
- timeout;
- partial stdout;
- partial stderr;
- non-zero exit;
- zero exit with fatal diagnostic;
- zero exit with missing artifact;
- cancellation;
- paths containing spaces;
- UTF-8 diagnostics.

## 41.3 Stage tests

Test each stage with:

- expected language failure;
- expected operational error;
- unexpected exception;
- evidence-write failure;
- independent continuation;
- dependent-stage skipping.

## 41.4 Scenario tests

Test:

- valid completion markers;
- missing end marker;
- duplicate marker;
- malformed UTF-8 policy;
- timeout;
- normalization failure;
- gold mismatch;
- missing required gold;
- normal run does not modify gold.

## 41.5 Persistence tests

Test:

- atomic write failure;
- unsupported schema;
- malformed state fallback;
- malformed project configuration failure;
- incomplete run exclusion from previous-run discovery;
- report failure criticality;
- manifest failure.

## 41.6 Security tests

Test:

- path traversal;
- symlink escape;
- shell escape rejection;
- secret redaction;
- untrusted executable path;
- protected-file overwrite attempt.

---

# 42. Error-handling change workflow

Any change to error semantics must include:

```text
Error code or status:
Current behavior:
New behavior:
Reason:
Affected components:
Affected providers:
Affected consumers:
Validation status impact:
Execution-state impact:
Error-kind impact:
Diagnostic-class impact:
Persistence impact:
CLI exit impact:
GUI presentation impact:
Migration:
Tests:
```

Required checklist:

```text
[ ] Error owner identified
[ ] Expected result versus exception reviewed
[ ] Validation status reviewed
[ ] Execution facts reviewed
[ ] Error kind reviewed
[ ] Diagnostic class reviewed
[ ] Evidence preservation reviewed
[ ] Continuation policy reviewed
[ ] Overall aggregation reviewed
[ ] CLI exit code reviewed
[ ] GUI presentation reviewed
[ ] Persisted schema reviewed
[ ] Contract locks reviewed
[ ] Unit tests updated
[ ] Integration tests updated
[ ] Legacy migration updated
[ ] Documentation updated
```

Changing status meaning or a serialized enum is a breaking contract change unless the schema explicitly defines compatibility.

---

# 43. Review checklist

Reviewers verify:

```text
Is this a validation failure or a framework error?
Did the operation execute enough to evaluate the criterion?
Was raw evidence captured first?
Are stdout and stderr both preserved?
Is timeout distinct from non-zero exit?
Is launch failure distinct from GF rejection?
Is a missing artifact detected?
Is an exception swallowed?
Is an optional failure visible?
Can independent work continue safely?
Are dependent stages skipped explicitly?
Is overall status correct?
Are CLI and GUI semantics identical?
Does persistence represent the outcome without guessing?
Are secrets redacted?
Are tests proving the mapping?
```

---

# 44. Normative invariants

GF Wordbench error handling must always preserve these invariants:

1. `FAIL` means a criterion was evaluated and failed.
2. `ERROR` means the validation contract could not be completed or interpreted reliably.
3. `SKIPPED` means intentional non-execution.
4. timeout is explicit.
5. cancellation is explicit.
6. launch failure is not a GF language error.
7. raw evidence precedes normalization.
8. stdout and stderr remain separate.
9. zero exit does not override missing required evidence.
10. reports never rerun validation.
11. required artifact failure prevents success.
12. exceptions retain their cause.
13. warnings remain visible.
14. optional does not mean hidden.
15. CLI and GUI share the same semantics.
16. state corruption does not block the framework.
17. project configuration corruption blocks language validation.
18. migrations never overwrite their source on failure.
19. error enums do not change silently.
20. a run cannot be release-ready when evidence is incomplete.

---

# 45. Governing rule

> GF Wordbench must report what failed, where it failed, whether the attempted operation actually ran, what evidence exists, and whether the failure belongs to the language project, the external tool, the environment, or the framework.

A successful-looking message, zero exit code, partial artifact, swallowed exception, or guessed diagnosis must never substitute for a valid structured result.
