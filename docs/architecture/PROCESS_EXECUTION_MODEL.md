# GF Wordbench — Process Execution Model

**Document ID:** `GF-WB-ARCH-PROCESS-EXECUTION`  
**Status:** Normative architectural specification  
**Applies to:** Every external process launched by GF Wordbench  
**Primary implementation owner:** `app/utils/process_utils.py`  
**Primary consumers:** compiler, PGF builder, scenario runner, version probe, and explicitly contracted optional-tool adapters  
**Model version:** `1.0`  
**Target product state:** Final architecture  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines the final process-execution model for GF Wordbench.

It specifies:

- how an external-process request is represented;
- how a process is validated and launched;
- how arguments, working directories, environment values, and standard input are handled;
- how standard output and standard error are captured;
- how timeouts, cancellation, termination, and launch failures are represented;
- how process evidence is preserved;
- how callers evaluate tool-specific success;
- how platform differences are contained;
- how process execution is tested;
- how the current GF Audit process utility migrates to the final model.

This document does not define the semantics of individual GF commands. Those belong to the GF integration and external-tool contracts.

---

## 2. Related authority

The following documents remain authoritative for their own domains:

```text
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/DATA_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
```

Priority when documents overlap:

1. persisted schema lock for serialized fields;
2. external-tool contract lock for the observable tool boundary;
3. interfile contract lock for Python provider-consumer relationships;
4. this document for process-runner architecture and lifecycle;
5. operation-specific documents for GF command semantics.

A change to this model that affects another locked boundary must update all affected documents and tests together.

---

## 3. Scope

This model applies to:

- GF version probing;
- `.gf` module compilation;
- PGF construction;
- `.gfs` scenario execution;
- parsing and linearization scenarios;
- bounded generation;
- morphology and grammar introspection;
- explicitly approved optional tools;
- operating-system utilities used by a documented platform adapter.

It governs:

- executable resolution;
- command arguments;
- process environment;
- working directory;
- standard input;
- standard output;
- standard error;
- process identity;
- timeout;
- cancellation;
- termination;
- output limits;
- raw evidence;
- process-level result fields;
- expected-artifact observations;
- platform containment.

---

## 4. Exclusions

This model does not govern:

- GF syntax or type semantics;
- interpretation of linguistic output;
- module dependency classification;
- direct versus downstream failure classification;
- scenario marker meaning;
- gold acceptance policy;
- report prose;
- project-specific release criteria;
- GUI layout;
- asynchronous job queues;
- remote execution;
- container orchestration;
- distributed workers.

The core process runner executes local child processes only.

---

## 5. Core architectural rule

> GF Wordbench has one process-execution boundary.

Every external process must pass through the designated process runner.

The following components must not invoke `subprocess`, `os.system`, shell commands, or equivalent launch APIs directly:

- CLI;
- GUI widgets;
- report writers;
- classifiers;
- scanners;
- schema loaders;
- project documentation utilities;
- active-project files.

Operation-specific components construct requests. The process runner executes them.

---

## 6. Responsibility split

### 6.1 Request owner

The operation-specific component owns:

- tool selection;
- operation kind;
- command arguments;
- working directory choice;
- standard-input content or source;
- timeout class;
- expected artifacts;
- tool-specific success criteria;
- diagnostic interpretation handoff.

Examples:

```text
app/audit/compiler.py
app/audit/pgf_builder.py
app/audit/scenario_runner.py
```

### 6.2 Process runner

The process runner owns:

- request validation at the generic process boundary;
- process launch;
- shell policy;
- environment construction;
- process-group creation;
- timeout timing;
- cancellation observation;
- termination escalation;
- stream capture;
- capture finalization;
- process-level result construction;
- platform adapter selection.

### 6.3 Diagnostic layer

The diagnostic layer owns:

- text decoding for interpretation;
- GF diagnostic recognition;
- error-kind derivation;
- source-location extraction;
- fatal-diagnostic detection.

It does not launch processes.

### 6.4 Stage owner

The stage owner converts a `ProcessResult` into a stage-specific result such as:

```text
CompileSummary
PgfBuildResult
ScenarioResult
```

The stage owner decides whether the operation met its complete tool contract.

### 6.5 Orchestrator

The orchestrator:

- invokes the stage;
- collects the stage result;
- determines whether later stages may safely continue;
- aggregates final run status.

It does not reconstruct or reinterpret the process request.

---

## 7. Final implementation ownership

The final public process facade is:

```text
app/utils/process_utils.py
```

The final public API should expose:

```text
ProcessRequest
ProcessInput
ProcessCapture
ArtifactExpectation
ArtifactObservation
ProcessResult
CancellationToken
run_process
render_command_for_display
```

Internal platform-specific helpers may be placed in:

```text
app/utils/process_platform.py
```

or an equivalent private module when implementation size justifies separation.

Platform helpers are internal. Callers depend on the public process facade, not on platform modules.

---

## 8. Design principles

The process model follows these principles.

### 8.1 Structured requests

Commands are structured data, not command strings.

### 8.2 No implicit shell

Normal execution uses no intermediate shell.

### 8.3 Explicit context

Every request specifies an executable, arguments, working directory, timeout, and capture paths.

### 8.4 Raw evidence first

Output is captured before diagnostic parsing or normalization.

### 8.5 Orthogonal outcomes

Process execution state is separate from validation status and diagnostic class.

### 8.6 Finite execution

Every process has a finite timeout.

### 8.7 Controlled termination

Timeout and cancellation use a documented escalation policy.

### 8.8 Platform containment

Windows and POSIX differences are hidden behind the process boundary.

### 8.9 Deterministic evidence

Equivalent requests produce consistently named and ordered evidence.

### 8.10 Minimal policy in the runner

The runner handles generic process mechanics. It does not understand GF language semantics.

---

# 9. Conceptual type model

The following definitions are conceptual. Exact Python syntax may differ while preserving the contract.

```python
@dataclass(frozen=True, slots=True)
class ProcessRequest:
    operation_id: str
    operation_kind: str
    executable: Path
    args: tuple[str, ...]
    cwd: Path
    stdout_path: Path
    stderr_path: Path
    timeout_sec: float
    stdin: ProcessInput
    environment_policy: str
    env_overrides: Mapping[str, str]
    sensitive_env_keys: frozenset[str]
    sensitive_arg_indexes: frozenset[int]
    termination_grace_sec: float
    output_limit_bytes: int
    expected_artifacts: tuple[ArtifactExpectation, ...]
    metadata: Mapping[str, str]
```

```python
@dataclass(frozen=True, slots=True)
class ProcessInput:
    kind: str
    text: str | None
    path: Path | None
    encoding: str
```

```python
@dataclass(frozen=True, slots=True)
class ProcessResult:
    operation_id: str
    operation_kind: str
    executable: Path
    args: tuple[str, ...]
    cwd: Path
    execution_state: str
    exit_code: int | None
    pid: int | None
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    timed_out: bool
    cancelled: bool
    cancellation_reason: str | None
    launch_error_kind: str | None
    launch_error_message: str
    termination_attempted: bool
    termination_succeeded: bool
    stdout_path: Path
    stderr_path: Path
    stdout_size_bytes: int
    stderr_size_bytes: int
    output_limit_exceeded: bool
    capture_complete: bool
    environment_policy: str
    recorded_env_overrides: Mapping[str, str]
    artifact_observations: tuple[ArtifactObservation, ...]
```

The public models must use safe immutable defaults.

Mutable dictionaries or lists must not be shared between instances.

---

# 10. Operation identity

Every request has a run-local `operation_id`.

Examples:

```text
gf-version
compile-GrammarSqi
pgf-GrammarSqi
scenario-parse
scenario-linearize
```

Rules:

- non-empty;
- unique within a run;
- stable enough to identify evidence;
- safe for log correlation;
- not used directly as an unrestricted filesystem path;
- sanitized separately before filename use.

The operation ID identifies one execution attempt.

A retry receives a distinct attempt suffix:

```text
compile-GrammarSqi-attempt-02
```

Automatic retries are not part of the default execution model.

---

# 11. Operation kinds

Canonical internal operation kinds:

```text
version_probe
compile
pgf_build
scenario
generation
introspection
optional_tool
```

Operation kind controls:

- timeout defaults;
- output-limit defaults;
- progress labels;
- allowed request policies;
- report grouping.

Operation kind does not define complete command semantics.

---

# 12. Process request requirements

A valid request must contain:

| Field | Requirement |
|---|---|
| `operation_id` | Unique, non-empty identifier |
| `operation_kind` | Known operation kind |
| `executable` | Resolved explicit executable path |
| `args` | Ordered tuple of argument strings |
| `cwd` | Existing explicit directory |
| `stdout_path` | Owned run path |
| `stderr_path` | Owned run path distinct from stdout |
| `timeout_sec` | Finite value greater than zero |
| `stdin` | Explicit input mode |
| `environment_policy` | Registered policy identifier |
| `env_overrides` | Explicit per-process overrides |
| `termination_grace_sec` | Finite non-negative value |
| `output_limit_bytes` | Finite positive limit |
| `expected_artifacts` | Explicit expectations, possibly empty |

The runner must reject incomplete requests before launch.

---

# 13. Request validation

Validation occurs before opening the process.

The runner must validate:

- operation ID format;
- known operation kind;
- executable path;
- executable file status where the platform exposes it;
- working-directory existence and directory status;
- argument types;
- absence of NUL characters;
- timeout positivity and finiteness;
- grace-period validity;
- standard-input mode consistency;
- capture-path containment;
- distinct stdout and stderr paths;
- environment key and value validity;
- output-limit validity;
- expected-artifact containment;
- conflicting active capture paths.

Validation failure is a configuration or contract error.

It is not a GF failure and no process is launched.

---

# 14. Executable resolution

Executable discovery occurs before the final `ProcessRequest` is built.

The resolved request must contain the exact executable used.

Accepted sources may include:

1. explicit CLI or GUI selection;
2. local application state;
3. documented framework discovery;
4. `PATH` lookup as a convenience.

If `PATH` lookup is used:

- the result must be converted to an explicit resolved path;
- the resolved path must be recorded;
- later process execution must use that resolved path;
- reports must not show only the unresolved token.

A request must not depend on a launcher script changing the executable behind the framework.

---

# 15. Executable restrictions

Normal tool requests should target native executables.

On Windows:

```text
.exe
```

is the normal executable form.

Batch files:

```text
.bat
.cmd
```

must not be accepted by the generic runner as if they were ordinary native executables unless an explicit launcher contract defines:

- interpreter;
- quoting;
- shell behavior;
- trusted inputs;
- platform limitation;
- tests.

Untrusted project text must never choose the process interpreter.

---

# 16. Argument model

Arguments are represented as:

```python
tuple[str, ...]
```

Rules:

- order is significant;
- each argument is one logical value;
- paths are converted to strings by the request owner;
- no manual quoting is applied for execution;
- empty arguments are allowed only when meaningful;
- NUL characters are prohibited;
- shell operators have no special meaning under normal execution.

Examples of values that remain individual arguments:

```text
--batch
--make
--path=C:/work/gf-rgl/src
C:/work/project/GrammarSqi.gf
```

The runner must not split one argument on whitespace.

The runner must not concatenate arguments into one execution string.

---

# 17. Command rendering

The executed command is stored structurally as:

```text
executable
ordered arguments
working directory
```

A display string may be generated for logs and reports.

The display string:

- is for humans only;
- may use platform-specific quoting;
- must not be re-executed;
- must preserve argument boundaries visually;
- must redact declared sensitive values.

Recommended display helpers:

```text
Windows: platform-compatible list-to-command rendering
POSIX: shell-style display quoting
```

The structured request remains authoritative.

---

# 18. Shell policy

Default:

```text
shell = false
```

The runner must not:

- call `os.system`;
- prepend `cmd.exe /c`;
- prepend `/bin/sh -c`;
- use shell redirection operators;
- use shell pipelines;
- use command substitution;
- rely on shell variable expansion.

A shell-backed operation requires a separate explicit external-tool contract.

The contract must justify why direct execution is insufficient.

GF scenario input must use direct standard input, not:

```text
gf < scenario.gfs
```

as a shell command string.

---

# 19. Working directory

Every request specifies an existing `cwd`.

The working directory must not depend on:

- the terminal;
- the GUI process directory;
- an IDE;
- the location of a shortcut;
- the current Python working directory;
- the caller’s incidental state.

Typical choices:

| Operation | Working directory |
|---|---|
| version probe | resolved project root |
| source compile | resolved project root or command-contract directory |
| PGF build | resolved project root |
| scenario | scenario-declared directory or resolved project root |
| optional tool | explicit contract directory |

The request owner chooses the directory.

The process runner validates and applies it.

---

# 20. Environment model

The process runner must build a new environment mapping per request.

It must not mutate:

```python
os.environ
```

The default policy is:

```text
controlled-inherit-v1
```

This policy:

1. copies the current process environment;
2. applies documented removals or neutralizations for variables known to create hidden GF behavior;
3. applies explicit request overrides;
4. passes the resulting mapping only to the child process.

Alternative registered policies may include:

```text
clean-v1
explicit-inherit-v1
```

A policy identifier is recorded in the process result.

---

# 21. Environment overrides

Overrides are:

```python
Mapping[str, str]
```

Rules:

- keys and values are converted or validated before launch;
- keys must be non-empty;
- NUL characters are prohibited;
- platform-specific key comparison is respected;
- overrides apply only to the child process;
- the runner records only the explicit overrides, not the full inherited environment;
- secret values are redacted in persisted evidence.

The framework should not rely silently on global `GF_LIB_PATH` or equivalent path-affecting variables.

GF path behavior should be explicit in the command contract.

---

# 22. Sensitive values

GF commands normally require no secrets.

A request containing credentials should be exceptional.

The request may declare:

```text
sensitive argument indexes
sensitive environment keys
```

Rules:

- actual values remain in memory only as required for execution;
- display commands replace them with `<redacted>`;
- persisted environment evidence replaces values with `<redacted>`;
- raw full command strings containing secrets are prohibited;
- reports must not expose them;
- secret values must not be used as operation IDs or filenames.

When a tool can read a secret through standard input instead of an argument, that mechanism should be preferred under an explicit contract.

---

# 23. Standard-input model

Standard input is explicit.

Canonical input kinds:

```text
none
text
file
```

### 23.1 No input

The process receives closed or null standard input.

This prevents accidental interactive waiting.

### 23.2 Text input

The request provides Unicode text and an explicit encoding.

Typical use:

```text
native .gfs scenario content
GF shell commands assembled from trusted scenario assets
```

Text is encoded before launch or before transfer.

### 23.3 File input

The request identifies a validated file.

The runner opens the file directly.

The file path must satisfy the operation’s trust and containment policy.

### 23.4 Mutual exclusion

A request must not contain both text and file input.

### 23.5 Interactive prompts

Unmanaged interactive prompts are prohibited.

An operation requiring interactive dialogue needs a dedicated protocol, tests, and contract. It must not be added through ad hoc sleeps or terminal emulation.

---

# 24. Scenario input

For a `.gfs` scenario, the preferred model is:

```text
scenario runner reads or validates scenario file
        ↓
ProcessRequest.stdin = file or UTF-8 text
        ↓
process runner sends input directly to GF
```

No platform shell redirection is used.

The scenario asset remains unchanged.

The executed scenario hash should be recorded by the scenario layer.

---

# 25. Stream capture model

Standard output and standard error are captured separately.

Canonical ownership:

```text
stdout path → process runner
stderr path → process runner
```

The runner must:

1. create parent directories;
2. open capture files before launch;
3. capture stdout and stderr concurrently or through safe OS redirection;
4. prevent pipe deadlock;
5. flush and close captures after termination;
6. record final byte sizes;
7. mark whether capture completed;
8. leave captured evidence immutable after finalization.

Combining stdout and stderr at launch is prohibited.

Derived aggregate logs may combine them later while preserving stream identity.

---

# 26. Raw byte preservation

Raw evidence means the bytes emitted by the process are preserved without semantic rewriting.

The runner should use binary capture internally.

A canonical capture filename may still use:

```text
.out.txt
.err.txt
.stdout.txt
.stderr.txt
```

The filename extension does not authorize altering bytes.

If the stream is not valid UTF-8:

- original bytes remain preserved;
- decoding failure is recorded;
- diagnostics use the documented decoding policy;
- reports may show a safe decoded excerpt;
- bytes must not be silently discarded.

---

# 27. Text decoding

Text interpretation occurs after or alongside raw capture through a bounded decoder.

Default encoding:

```text
UTF-8
```

Default failure strategy:

```text
preserve raw bytes
record decode issue
produce a non-lossless diagnostic view with explicit replacement
```

The final implementation may use a reversible strategy such as surrogate escaping internally.

Requirements:

- no silent byte deletion;
- no locale-dependent default decoding;
- no different decoding rules between CLI and GUI;
- decoding strategy is testable;
- diagnostic parsing sees both streams.

A tool-specific contract may specify another encoding when required.

---

# 28. Capture paths

Capture paths are supplied through owned run-path models.

They must:

- be inside the active run directory;
- be distinct;
- not point to source files;
- not point to `.gold` files;
- not escape through `..`;
- not overwrite an artifact owned by another operation;
- use deterministic operation-derived names;
- be recorded in the result.

The process runner must not invent report paths.

---

# 29. Capture lifecycle

Capture files may be written incrementally during process execution.

Atomic replacement is not required for streaming raw evidence.

The lifecycle is:

```text
created
  ↓
open and incomplete
  ↓
receiving bytes
  ↓
flushed and closed
  ↓
finalized and immutable
```

`capture_complete` is true only after both streams are closed successfully.

A partial capture caused by application failure should be preserved when possible and must not be presented as complete evidence.

---

# 30. Output limits

Every process request has a finite total output limit.

The limit covers:

```text
stdout bytes + stderr bytes
```

Operation-specific defaults may differ.

Examples:

| Operation | Relative policy |
|---|---|
| version probe | small |
| compile | moderate |
| PGF build | moderate |
| scenario | moderate |
| generation | strict and bounded |
| introspection | bounded by request |
| optional tool | explicit contract |

When the limit is exceeded:

1. the runner records `output_limit_exceeded = true`;
2. the controller requests cancellation;
3. termination escalation begins;
4. already captured bytes remain preserved;
5. the result uses `execution_state = cancelled`;
6. `cancellation_reason = output_limit`;
7. the stage reports an execution or contract error, not a linguistic failure.

Truncation must never be silent.

---

# 31. Process lifecycle

The internal lifecycle is:

```text
created
  ↓
validated
  ↓
capture_opened
  ↓
launching
  ├── launch_failed
  ↓
running
  ├── natural_exit ─────────────→ completed
  ├── deadline_reached ─────────→ timed_out
  ├── cancellation_requested ───→ cancelled
  └── output_limit_reached ─────→ cancelled
```

Intermediate lifecycle states are internal.

Canonical terminal `execution_state` values are:

```text
completed
timed_out
cancelled
launch_failed
```

---

# 32. Terminal-state meanings

## 32.1 `completed`

The child process started and reached an OS terminal state without timeout or controller cancellation.

This does not mean validation success.

A completed process may have:

- exit code zero;
- non-zero exit code;
- fatal diagnostics;
- missing required artifacts;
- failed scenario markers;
- failed gold comparison.

## 32.2 `timed_out`

The configured deadline was reached before natural completion.

The runner initiated termination.

## 32.3 `cancelled`

The controlling system requested termination before natural completion.

Reasons include:

```text
user
application_shutdown
output_limit
controller_policy
```

## 32.4 `launch_failed`

The process did not start successfully.

Examples:

- executable disappeared;
- permission denied;
- invalid executable format;
- OS resource failure;
- platform launch error.

---

# 33. Derived booleans

For compatibility and convenient stage use:

```text
timed_out = execution_state == timed_out
cancelled = execution_state == cancelled
```

These values must not contradict `execution_state`.

`launch_error_message` must be non-empty when:

```text
execution_state == launch_failed
```

---

# 34. Validation status separation

Process execution state is not validation status.

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Typical mapping:

| Process condition | Stage validation status |
|---|---|
| completed, contract passed | `OK` |
| completed, language criterion failed | `FAIL` |
| completed, process contract could not be interpreted | `ERROR` |
| timed out | `ERROR` |
| cancelled | `ERROR` or run-level cancellation handling |
| launch failed | `ERROR` |
| stage intentionally not invoked | `SKIPPED` |

The process runner does not assign direct, downstream, or ambiguous classification.

---

# 35. Exit-code model

`exit_code` is the real OS-observed process return code when available.

Rules:

- zero does not guarantee validation success;
- non-zero is retained exactly;
- signal-derived or platform-specific values are not rewritten;
- no synthetic exit code is presented as if emitted by the tool;
- `exit_code` is `None` when the process never started or no reliable code was obtained;
- timeout and cancellation are represented by execution state, not by invented tool codes.

Legacy adapters may temporarily map older sentinel fields, but canonical process logic must not depend on those sentinels.

Any persisted schema requiring an integer-only exit code must be updated in coordination with the persisted-schema lock to permit absence when no process exit exists.

---

# 36. Timekeeping

Every result records:

```text
started_at
finished_at
duration_ms
```

Rules:

- wall-clock timestamps use UTC;
- duration uses a monotonic clock;
- duration includes launch attempt and termination handling;
- `duration_ms` is a non-negative integer;
- timeout evaluation uses monotonic time;
- system clock changes must not alter timeout behavior.

`started_at` is the time the launch attempt begins.

`finished_at` is the time capture and termination finalization completes.

---

# 37. Timeout model

Every request has a resolved finite timeout.

Timeout defaults are configured by operation class:

```text
version probe
file compilation
PGF build
scenario
generation
introspection
optional tool
```

A caller must not pass:

```text
None
0
negative infinity
positive infinity
```

as a timeout.

The deadline begins immediately before the launch attempt.

A timeout is distinct from:

- non-zero exit;
- fatal GF output;
- launch failure;
- user cancellation;
- missing artifact;
- gold mismatch.

---

# 38. Cancellation model

Cancellation is cooperative at the framework boundary and forceful at the OS boundary when necessary.

A `CancellationToken` may be shared with one active request.

Conceptual interface:

```python
class CancellationToken:
    def is_cancelled(self) -> bool: ...
    def reason(self) -> str | None: ...
```

The runner checks cancellation:

- before launch;
- after launch;
- during wait;
- before expensive finalization;
- during output-limit monitoring.

If cancellation exists before launch:

- no process starts;
- the result is `cancelled`;
- capture files may be empty but valid;
- no launch failure is reported.

---

# 39. Cancellation sources

Canonical reasons:

```text
user
application_shutdown
output_limit
controller_policy
```

The first accepted terminal cause wins.

Race example:

```text
timeout and user cancellation occur nearly together
```

The runner records whichever cause was observed first according to monotonic event order.

It must not alternate terminal state during finalization.

---

# 40. Termination policy

Timeout and cancellation use the same platform-aware escalation mechanism while preserving distinct terminal states.

Generic escalation:

1. stop sending standard input;
2. close or detach owned stdin;
3. request graceful termination for the owned process group;
4. wait for `termination_grace_sec`;
5. force termination of remaining owned processes;
6. wait for process reaping;
7. drain or finalize output capture;
8. record termination outcome.

The runner must avoid leaving owned child processes running after the parent result is finalized.

---

# 41. Termination result fields

The result records:

```text
termination_attempted
termination_succeeded
cancellation_reason
```

`termination_attempted` is true when the runner initiated termination.

`termination_succeeded` is true when the owned process or process group is confirmed no longer running.

If termination cannot be confirmed:

- the result remains timeout or cancelled;
- a containment warning is recorded;
- run cleanup must not claim complete process containment;
- release validation must fail.

---

# 42. Process groups

Each process-backed operation should run in an owned process group or equivalent containment unit.

Purpose:

- terminate child processes created by GF or optional tools;
- avoid killing unrelated processes;
- support reliable cancellation;
- support application shutdown.

The platform adapter owns group creation and termination.

The generic runner must not contain scattered platform conditionals throughout its main logic.

---

# 43. Windows policy

Windows is a first-class platform.

The Windows adapter must address:

- Unicode executable paths;
- spaces in executable and argument paths;
- argument-list execution;
- process-group creation;
- timeout termination;
- child-process containment;
- return-code preservation;
- `.exe` validation;
- inherited handle control;
- no hidden `cmd.exe`;
- long-path behavior where supported.

Preferred containment uses an owned process group or a stronger OS-supported job mechanism.

If an OS utility such as `taskkill.exe` is used as a fallback:

- it must have an explicit external-tool contract;
- arguments must be structured;
- the action must target only the owned process tree;
- fallback use must be recorded;
- failure must be visible.

Batch launchers are not the canonical execution path.

---

# 44. POSIX policy

The POSIX adapter should:

- start the process in a new session or process group;
- send termination to the owned group;
- wait for the grace period;
- escalate to forceful group termination;
- reap the child;
- preserve signal-derived return codes;
- avoid shell invocation.

POSIX behavior must remain an adapter detail.

Callers use the same `ProcessRequest` and `ProcessResult`.

---

# 45. Standard-output and error concurrency

The implementation must avoid deadlocks caused by full OS pipe buffers.

Accepted strategies:

1. redirect both streams directly to separate binary file handles;
2. use dedicated bounded reader threads that write to separate files;
3. use a platform-safe asynchronous pump hidden behind the runner.

The final implementation should choose the simplest strategy that also supports:

- cancellation;
- output-limit monitoring;
- complete byte capture;
- no unbounded in-memory buffering.

For output-limit enforcement, bounded reader pumps are the preferred final strategy.

---

# 46. Memory policy

The runner must not load complete unbounded output into memory.

Raw output is file-backed.

In-memory data may include:

- bounded head excerpt;
- bounded tail excerpt;
- byte counts;
- decoder state;
- small version output;
- structured lifecycle metadata.

Diagnostic parsers should read bounded or operation-appropriate content from owned files.

A report must not force the runner to retain complete output in memory.

---

# 47. Output excerpts

The process result may include bounded excerpts for immediate diagnostics.

If implemented, excerpt fields must define:

```text
source stream
head or tail policy
maximum bytes or characters
encoding policy
truncation flag
```

Excerpts are derived evidence.

They do not replace raw stream files.

---

# 48. Expected artifacts

A request may declare expected artifacts.

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ArtifactExpectation:
    path: Path
    role: str
    required: bool
    kind: str
    minimum_size_bytes: int
```

Canonical `kind` values:

```text
file
directory
```

Expectations come from the stage owner.

The process runner observes them after execution.

---

# 49. Artifact observations

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ArtifactObservation:
    path: Path
    role: str
    required: bool
    exists: bool
    kind_matches: bool
    size_bytes: int | None
```

The process runner may collect these generic facts.

The stage owner decides whether the complete operation succeeded.

Examples:

- compile requires expected `.gfo`;
- PGF build requires a non-empty `.pgf`;
- scenario may require a normalized output generated by a later stage;
- version probe may require no file artifact.

---

# 50. Artifact safety

Expected artifact paths must:

- remain inside an allowed project or run root;
- not point to source files for overwrite;
- not point to `.gold`;
- be deterministic;
- be declared before launch where possible;
- not overlap another active operation’s owned output.

The process runner does not rewrite tool-generated artifacts.

It may observe, copy through an explicitly owned stage, or catalog them.

---

# 51. Success evaluation

The process runner reports process facts.

It does not return a generic “tool succeeded” boolean as the sole truth.

A stage evaluates:

```text
execution state
exit code
stdout
stderr
fatal diagnostics
required markers
expected artifacts
gold result
operation-specific assertions
```

Examples:

### Compilation success

```text
process completed
exit code accepted
no fatal compile diagnostic
required .gfo exists when required
```

### PGF success

```text
process completed
exit code accepted
no fatal build diagnostic
expected .pgf exists
expected .pgf is non-empty
```

### Scenario success

```text
process completed
exit policy accepted
required markers completed
fatal diagnostic checks passed
required artifacts exist
gold comparison passed when required
```

---

# 52. Launch failure handling

Launch failures should be represented as a `ProcessResult` when the runner can create valid capture paths and result metadata.

Required fields:

```text
execution_state = launch_failed
exit_code = null
pid = null
launch_error_kind
launch_error_message
capture_complete
```

Likely launch-error kinds:

```text
not_found
permission_denied
invalid_executable
invalid_working_directory
resource_unavailable
platform_error
unknown
```

The raw exception type may be recorded internally.

Human reports should use normalized wording.

---

# 53. Pre-launch exceptions

The runner may raise a process-request exception before a result exists for:

- invalid request structure;
- unsafe path;
- capture-path collision;
- impossible capture-directory creation;
- unsupported environment policy;
- programming contract violation.

These are not tool outcomes.

The stage or orchestrator converts them into framework `ERROR` evidence.

---

# 54. Post-launch internal failures

If GF Wordbench encounters an internal failure after launch:

1. attempt process containment;
2. preserve available stream evidence;
3. close captures;
4. record the internal failure;
5. do not relabel it as a GF failure;
6. propagate a structured framework error or terminal result according to the public API contract.

A programming error must not be hidden as `exit_code != 0`.

---

# 55. Environment recording

The result records:

```text
environment policy identifier
explicit override names
non-sensitive override values
redaction markers
```

It must not record the full inherited environment.

For reproducibility, operation-specific components should explicitly encode values that materially affect GF behavior in:

- arguments;
- project configuration;
- recorded overrides;
- GF version metadata.

Hidden ambient behavior is architectural drift.

---

# 56. Process event reporting

The runner may emit lifecycle events to an optional event sink.

Recommended events:

```text
request_validated
capture_opened
process_started
termination_requested
process_exited
capture_finalized
```

Event payloads are bounded and structured.

They may include:

- operation ID;
- operation kind;
- PID;
- timestamp;
- terminal cause;
- byte counts.

They must not include:

- complete stdout;
- complete stderr;
- secrets;
- mutable process objects.

CLI and GUI may use these events for progress.

They must not derive validation results from progress events.

---

# 57. Logging

The runner logs:

- operation ID;
- operation kind;
- redacted rendered command;
- explicit working directory;
- environment policy;
- start;
- timeout or cancellation;
- exit code when available;
- duration;
- capture paths;
- termination outcome.

The logged command must correspond to the structured executed request.

A log must not reconstruct a different command after execution.

---

# 58. Concurrency model

The process runner executes one request independently and is not the global scheduler.

Default GF Wordbench scheduling is sequential.

Reasons:

- deterministic evidence;
- simpler diagnosis;
- reduced filesystem collision risk;
- predictable GF artifact behavior;
- simpler cancellation;
- lower resource pressure.

Future bounded concurrency may be added by the orchestrator only when:

- output paths are disjoint;
- GF command contracts permit it;
- result ordering remains deterministic;
- cancellation is tested;
- platform containment is tested;
- configuration exposes a bounded limit;
- release behavior remains reproducible.

The runner must not create an unbounded internal worker pool.

---

# 59. Active-output collision control

Two active requests must not write to the same:

- stdout path;
- stderr path;
- declared exclusive artifact path.

The scheduler or runner must reject collisions before launch.

Read-only overlap is allowed when the tool contract permits it.

---

# 60. Retry policy

Automatic retries are disabled by default.

A non-zero GF result must not be retried merely to obtain a passing outcome.

A documented retry may be considered only for:

- transient OS launch conditions;
- explicitly identified filesystem races;
- optional tools with idempotent operations.

A retry must:

- use a new attempt ID;
- preserve the first attempt evidence;
- record the reason;
- remain bounded;
- not overwrite capture files;
- not hide instability.

Release validation should normally treat retries as visible evidence.

---

# 61. Source-file protection

The process model must not modify source files directly.

A request owner must ensure that:

- output directories are explicit where supported;
- generated artifacts do not overwrite source;
- scenario input is read-only;
- `.gold` files are read-only during normal validation;
- cleanup targets only owned temporary or run files.

The process runner itself does not perform source-tree cleanup.

---

# 62. Temporary resources

Temporary resources may include:

- encoded standard-input buffers;
- temporary capture metadata;
- platform containment handles.

Rules:

- use owned temporary locations;
- avoid user source directories;
- close handles deterministically;
- delete only resources created by the current request;
- preserve diagnostic evidence needed after failure;
- never delete declared tool artifacts unless the stage owns cleanup.

---

# 63. Process-result immutability

A finalized `ProcessResult` is immutable.

Later components may:

- read it;
- derive diagnostics;
- build stage results;
- serialize selected fields;
- reference its evidence.

They must not:

- change exit code;
- change terminal state;
- alter capture paths;
- replace the executable;
- rewrite raw output;
- mark termination successful without new platform evidence.

Derived interpretation belongs in separate models.

---

# 64. Persistence boundary

`ProcessRequest` and `ProcessResult` are internal domain models unless a dedicated persisted schema is introduced.

Stage summaries persist selected process fields.

Typical persisted fields:

```text
command
working directory
exit code
timed out
cancelled or cancellation metadata where supported
duration
stdout path
stderr path
error kind
artifact observations
```

Serialization must be centralized.

Internal Python values such as:

- `Path`;
- enum instances;
- cancellation tokens;
- process handles;
- platform handles;

must not be serialized directly.

---

# 65. Command persistence

Persisted command evidence should use an ordered array:

```json
[
  "C:/tools/gf/gf.exe",
  "--batch",
  "--make",
  "GrammarSqi.gf"
]
```

This array is the redacted executable plus ordered arguments.

A human display string may also be included as derived text, but it is not authoritative.

If arguments are redacted, persistence should record that redaction occurred.

---

# 66. Path persistence

Internal paths use `Path`.

Persisted process paths follow schema-lock rules:

- project-owned paths are project-relative;
- run-owned captures are run-relative;
- environment executable and working-directory paths may be absolute;
- canonical separators use `/`;
- legacy readers may accept `\`.

The runner does not serialize paths itself unless designated by the schema owner.

---

# 67. Process-level error vocabulary

Recommended process error kinds:

```text
OK
LAUNCH
TIMEOUT
CANCELLED
OUTPUT_LIMIT
IO
ENCODING
CONTAINMENT
CONTRACT
OTHER
```

These are process-level terms.

Operation-specific diagnostic kinds such as:

```text
TYPE
SYNTAX
GOLD
ARTIFACT
SCRIPT
TOOL
```

belong to stage or diagnostic models.

The final centralized status reference must define the authoritative enums.

---

# 68. Failure ownership examples

| Condition | Owner of interpretation |
|---|---|
| executable missing before request construction | bootstrap or executable resolver |
| executable disappears at launch | process runner |
| timeout | process runner |
| user cancellation | process runner/controller |
| invalid UTF-8 bytes | process capture/decoder |
| GF syntax diagnostic | diagnostic parser |
| `.gfo` missing | compiler stage |
| `.pgf` missing | PGF stage |
| scenario marker missing | scenario stage |
| gold mismatch | gold comparator |
| downstream dependency cascade | classifier |
| report write fails | report writer |

This separation prevents one layer from swallowing another layer’s responsibility.

---

# 69. Public API

Recommended final API:

```python
def run_process(
    request: ProcessRequest,
    *,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
) -> ProcessResult:
    ...
```

Supporting helpers:

```python
def validate_process_request(request: ProcessRequest) -> None:
    ...
```

```python
def render_command_for_display(
    executable: Path,
    args: Sequence[str],
    *,
    sensitive_arg_indexes: Collection[int] = (),
) -> str:
    ...
```

The main public API should remain small.

Platform-specific functions remain private.

---

# 70. Runner algorithm

Normative high-level algorithm:

```text
validate request
        ↓
reserve capture paths
        ↓
create capture directories
        ↓
open binary captures
        ↓
build controlled child environment
        ↓
prepare platform process-group options
        ↓
check pre-launch cancellation
        ↓
launch executable with shell disabled
        ↓
record PID and start event
        ↓
transfer stdin and capture both streams
        ↓
monitor:
    natural exit
    deadline
    cancellation token
    output limit
        ↓
when required, terminate owned process group
        ↓
wait and reap process
        ↓
flush and close captures
        ↓
observe expected artifacts
        ↓
construct immutable ProcessResult
        ↓
release capture reservation
```

No diagnostic parsing occurs inside this algorithm.

---

# 71. Pseudocode

```python
def run_process(request, *, cancellation_token=None, event_sink=None):
    validate_process_request(request)
    reservation = reserve_outputs(request)

    started_at = utc_now()
    started_clock = monotonic_now()

    try:
        with open_binary_capture(request.stdout_path) as stdout_sink, \
             open_binary_capture(request.stderr_path) as stderr_sink:

            if cancellation_token and cancellation_token.is_cancelled():
                return build_prelaunch_cancelled_result(...)

            environment = build_environment(request)
            platform_context = prepare_platform_context(request)

            try:
                process = launch_without_shell(
                    executable=request.executable,
                    args=request.args,
                    cwd=request.cwd,
                    env=environment,
                    stdin_mode=request.stdin,
                    stdout_sink=stdout_sink,
                    stderr_sink=stderr_sink,
                    platform_context=platform_context,
                )
            except OSError as exc:
                return build_launch_failed_result(...)

            terminal_cause = monitor_process(
                process=process,
                timeout_sec=request.timeout_sec,
                cancellation_token=cancellation_token,
                output_limit_bytes=request.output_limit_bytes,
            )

            if terminal_cause.requires_termination:
                termination = terminate_owned_processes(
                    process,
                    grace_sec=request.termination_grace_sec,
                    platform_context=platform_context,
                )

            exit_code = reap_and_get_exit_code(process)
            finalize_capture(stdout_sink, stderr_sink)
            observations = observe_expected_artifacts(request.expected_artifacts)

            return build_process_result(...)
    finally:
        reservation.release()
```

This pseudocode describes responsibility, not required private function names.

---

# 72. Current GF Audit baseline

The inherited process utility currently provides:

```text
ProcessRunResult
run_process_with_timeout
```

Its current result contains:

```text
exit_code
timed_out
stdout_path
stderr_path
duration_ms
```

Its current execution behavior:

- builds an argument list;
- copies the current environment and applies overrides;
- writes stdout and stderr to separate UTF-8 files;
- uses `Popen`;
- waits with a timeout;
- kills the direct process on timeout;
- uses a synthetic timeout exit code;
- returns a small immutable result.

This is a valid minimal baseline, not the final execution model.

---

# 73. Baseline limitations

The inherited implementation does not yet fully model:

- structured request identity;
- explicit operation kind;
- standard input;
- user cancellation;
- application-shutdown cancellation;
- output limits;
- process-tree containment;
- launch failure as a structured result;
- raw-byte preservation;
- decoding errors;
- platform adapters;
- termination escalation;
- expected-artifact observations;
- environment policy identity;
- command redaction;
- output collisions;
- lifecycle events;
- capture completeness;
- real versus synthetic exit-code separation.

These limitations are migration work, not defects in the historical scope.

---

# 74. Migration plan

## Phase 1 — Introduce models

Add:

```text
ProcessRequest
ProcessInput
ArtifactExpectation
ArtifactObservation
ProcessResult
CancellationToken
```

Keep `run_process_with_timeout` as a compatibility wrapper.

## Phase 2 — Introduce `run_process`

Implement the structured API using existing capture behavior.

Callers migrate one at a time.

## Phase 3 — Remove synthetic timeout semantics

Represent timeout through `execution_state`.

Keep legacy adapter translation only where required.

## Phase 4 — Add direct scenario stdin

Support `.gfs` execution without shell redirection.

## Phase 5 — Add cancellation and process-group containment

Implement platform adapters and termination escalation.

## Phase 6 — Add bounded stream capture

Enforce output limits without unbounded memory.

## Phase 7 — Add expected-artifact observation

Allow compiler and PGF stages to declare artifacts.

## Phase 8 — Retire compatibility wrapper

Remove or deprecate `run_process_with_timeout` after all consumers and tests use `run_process`.

The public owner remains `app/utils/process_utils.py`.

---

# 75. Compatibility wrapper

During migration:

```python
def run_process_with_timeout(
    executable,
    args,
    cwd,
    stdout_path,
    stderr_path,
    timeout_sec,
    env=None,
) -> LegacyProcessRunResult:
    ...
```

may construct a canonical `ProcessRequest` and adapt the `ProcessResult`.

Restrictions:

- one-way adaptation only;
- no second process implementation;
- wrapper behavior tested;
- timeout sentinel documented as legacy;
- new callers prohibited after migration cutoff;
- removal recorded in changelog.

---

# 76. Unit-test architecture

Recommended tests:

```text
tests/process/
├── test_process_request.py
├── test_process_launch.py
├── test_process_capture.py
├── test_process_timeout.py
├── test_process_cancellation.py
├── test_process_output_limit.py
├── test_process_environment.py
├── test_process_artifacts.py
├── test_process_rendering.py
├── test_process_security.py
├── test_process_windows.py
└── test_process_posix.py
```

Contract tests remain under:

```text
tests/contracts/test_process_contract.py
tests/contracts/test_timeout_contract.py
tests/contracts/test_environment_contract.py
tests/contracts/test_windows_contract.py
```

---

# 77. Fake-process fixtures

Tests without GF should use small controlled executables or scripts that can:

- exit zero;
- exit non-zero;
- write stdout only;
- write stderr only;
- write both streams;
- sleep beyond timeout;
- spawn a child process;
- ignore graceful termination;
- emit invalid UTF-8 bytes;
- exceed output limit;
- read standard input;
- create an expected artifact;
- omit an expected artifact;
- print arguments;
- print selected environment variables.

Fixtures must not require network access.

---

# 78. Required unit cases

The final runner must test:

```text
valid request
invalid timeout
missing executable
invalid working directory
capture path outside run root
same stdout and stderr path
arguments containing spaces
Unicode paths
empty argument
NUL rejection
environment override
secret redaction
no implicit shell
stdin none
stdin text
stdin file
natural exit zero
natural exit non-zero
stdout capture
stderr capture
simultaneous streams
timeout
pre-launch cancellation
running cancellation
output-limit cancellation
graceful termination
forced termination
child-process containment
launch failure
invalid UTF-8
capture finalization failure
expected artifact present
expected artifact missing
deterministic display command
```

---

# 79. Integration tests with GF

When GF is available, test:

- version probe;
- successful compile;
- failed compile;
- path containing spaces;
- explicit GF path;
- PGF build;
- `.gfs` scenario over stdin;
- stdout diagnostic;
- stderr diagnostic when produced by the platform/version;
- bounded generation;
- scenario timeout containment;
- required artifact observation.

Real-GF tests should be marked separately from standard unit tests.

---

# 80. Windows tests

Windows-specific tests should verify:

- executable paths containing spaces;
- project paths containing spaces;
- Unicode path handling;
- direct `.exe` execution;
- no hidden `cmd.exe`;
- argument boundary preservation;
- cancellation of owned process group;
- child-process termination;
- return-code recording;
- launch failure normalization;
- launcher scripts are not required.

---

# 81. Determinism tests

Given equivalent requests and controlled environment:

- command arrays are identical;
- display rendering is stable;
- operation IDs are stable;
- capture paths are stable;
- result field meanings are stable;
- expected-artifact observations retain request order;
- event ordering is stable except for timestamps;
- report ordering is independent of OS directory enumeration.

---

# 82. Security tests

Test that:

- shell metacharacters remain literal arguments;
- project input cannot inject a second command;
- environment secrets are redacted;
- sensitive arguments are redacted;
- path escape is rejected;
- source files cannot be selected as capture targets;
- `.gold` cannot be used as a capture target;
- output limits terminate runaway output;
- process termination targets only owned processes;
- full environment dumps are not persisted.

---

# 83. Performance expectations

The runner should add low overhead relative to GF execution.

It must prioritize correctness over micro-optimization.

Performance requirements:

- no unbounded in-memory output;
- no busy-wait loop;
- bounded cancellation polling interval;
- file-backed capture;
- one environment copy per process;
- no repeated hashing of large output inside the execution loop;
- artifact hashing deferred to the manifest stage;
- no duplicate process launch for reporting.

---

# 84. Observability requirements

For every process-backed stage, final evidence should allow a reviewer to determine:

```text
what executable ran
with which ordered arguments
from which working directory
under which environment policy
when it started
how long it ran
whether it timed out or was cancelled
what exit code was observed
where stdout and stderr were captured
whether output was limited
whether termination succeeded
which expected artifacts appeared
```

A reviewer should not need to infer these facts from human prose.

---

# 85. Prohibited behavior

The following are prohibited:

- direct process launch outside the designated boundary;
- `shell=True` for normal GF execution;
- one concatenated unquoted command string;
- implicit working directory;
- infinite timeout;
- stdout-only diagnosis;
- merged raw streams;
- discarded stderr;
- silent output truncation;
- synthetic exit code presented as tool output;
- timeout reported as ordinary GF compile failure;
- user cancellation reported as timeout;
- launch failure reported as GF syntax error;
- report writer rerunning a process;
- GUI widget holding a raw `Popen` object;
- global mutation of `os.environ`;
- full environment persistence;
- normal process execution writing `.gold`;
- output capture outside owned run paths;
- child processes left knowingly running after finalization;
- hidden platform behavior in launch scripts;
- process retry that overwrites first-attempt evidence.

---

# 86. Drift indicators

Process-execution drift exists when:

- callers construct commands differently for the same operation;
- a new direct `subprocess` call appears outside the process utility;
- CLI and GUI resolve different executables;
- logged command differs from executed request;
- working directory is omitted;
- a request can run without timeout;
- stdout and stderr use different decoding rules by interface;
- timeout uses an invented exit code without terminal-state evidence;
- cancellation cannot be distinguished from timeout;
- capture paths are reconstructed by callers;
- a report reads only one stream;
- a process tree survives cancellation;
- environment overrides alter behavior but are not recorded;
- shell redirection is used for `.gfs`;
- output-limit termination is silent;
- a missing artifact is accepted because exit code is zero;
- platform-specific logic leaks into compiler or scenario code.

Any drift indicator requires review of:

```text
process runner
request owner
shared models
tests
external-tool lock
interfile lock
persisted schema when affected
this document
```

---

# 87. Change classification

## 87.1 Internal compatible change

Examples:

- private polling implementation;
- private platform helper refactor;
- faster bounded capture;
- improved internal logging.

Requirements:

- public fields unchanged;
- terminal meanings unchanged;
- evidence unchanged;
- contract tests pass.

## 87.2 Compatible extension

Examples:

- optional metadata field;
- optional event sink;
- new optional artifact observation;
- new registered environment policy.

Requirements:

- safe default;
- callers reviewed;
- tests added;
- schema review if persisted.

## 87.3 Breaking change

Examples:

- terminal-state rename;
- timeout semantic change;
- request-field removal;
- capture-path ownership change;
- environment inheritance change;
- exit-code meaning change;
- shell policy change;
- artifact observation change;
- process owner path change.

Requirements:

1. contract impact analysis;
2. caller migration;
3. model update;
4. test update;
5. schema migration where persisted;
6. changelog entry;
7. lock update;
8. compatibility plan.

---

# 88. Review checklist

A process implementation is compliant when:

```text
[ ] one public runner owns external execution
[ ] request is structured and immutable
[ ] executable is resolved explicitly
[ ] arguments are ordered values
[ ] shell is disabled by default
[ ] working directory is explicit
[ ] child environment is built without mutating os.environ
[ ] timeout is finite
[ ] cancellation is supported
[ ] process-group containment is implemented
[ ] stdout and stderr are captured separately
[ ] raw bytes are preserved
[ ] decoding errors are explicit
[ ] output limit is finite
[ ] output-limit termination is visible
[ ] real exit code is preserved
[ ] no synthetic code is presented as tool output
[ ] launch failure is distinguishable
[ ] capture completeness is recorded
[ ] expected artifacts are observed
[ ] stage-specific success remains outside the runner
[ ] raw evidence is immutable after finalization
[ ] no report launches a process
[ ] Windows paths with spaces are tested
[ ] child-process termination is tested
[ ] secrets are redacted
[ ] path containment is tested
[ ] compatibility wrapper has one implementation underneath
```

---

# 89. Final invariants

1. Every external process passes through one process boundary.
2. The process runner receives a complete structured request.
3. No normal process uses an implicit shell.
4. Every process has an explicit working directory.
5. Every process has a finite timeout.
6. Cancellation and timeout remain distinct.
7. Output-limit cancellation is explicit.
8. Stdout and stderr remain separate.
9. Raw bytes are preserved before interpretation.
10. Exit code is evidence, not complete success.
11. No synthetic code is presented as an OS exit.
12. Launch failure is not a GF validation failure.
13. Process termination targets owned processes only.
14. Environment behavior is controlled and inspectable.
15. Full inherited environments and secrets are not persisted.
16. Capture paths belong to the run.
17. Expected artifacts are declared by the request owner.
18. The runner observes artifacts but does not decide linguistic success.
19. Process results are immutable after finalization.
20. Reports consume process evidence and never recreate it.
21. Platform differences remain behind the process facade.
22. Compatibility logic does not create a second runner.
23. A process-contract change is coordinated across all consumers.
24. Complexity is added only to contain a real execution risk or stable responsibility.

---

# 90. Final rule

The process runner is infrastructure, not a GF interpreter.

Its obligation is to execute one explicit request safely and return complete, trustworthy evidence:

```text
request
  → validated launch
  → bounded execution
  → controlled termination
  → separate raw streams
  → real process facts
  → immutable result
```

All higher-level meaning is added by the component that owns the operation contract.
