# GF Wordbench — Timeouts and Process Failures

**Document ID:** `GF-WB-DIAG-TIMEOUTS-PROCESS-FAILURES`  
**Status:** Normative diagnostic and execution specification  
**Applies to:** Every external process launched by GF Wordbench  
**Primary target:** Grammatical Framework (`gf` / `gf.exe`) and statically registered diagnostic tools  
**Owner:** GF Wordbench maintainers  
**Primary architectural owner:** external-process port and platform process adapter  
**Primary adapter:** `app/utils/process_utils.py`  
**Primary consumers:** validation, diagnostics, runs, version probing and registered optional-tool adapters  
**Canonical path:** `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related external contract:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Related diagnostic-tool decision:** `docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md`  
**Related process architecture:** `docs/architecture/PROCESS_EXECUTION_MODEL.md`  
**Related error model:** `docs/diagnostics/ERROR_CLASSIFICATION.md`  
**Specification version:** `1.1`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

GF Wordbench depends on external processes for native Grammatical Framework behavior.

An external operation may:

- complete successfully;
- complete with a GF-reported validation failure;
- fail to launch;
- exceed its timeout;
- be cancelled by the user or controlling system;
- terminate unexpectedly;
- leave child processes running;
- block while writing stdout or stderr;
- fail while stdin is being supplied;
- produce incomplete output;
- create incomplete or stale artifacts;
- fail during output capture or decoding;
- resist termination;
- produce a response that violates the declared external-tool contract.

These outcomes are not equivalent.

This document defines:

- the canonical process request;
- the canonical process result;
- execution-state semantics;
- timeout configuration and enforcement;
- cancellation behavior;
- process-tree ownership and termination;
- stdout and stderr capture;
- partial-evidence handling;
- launch, tool, contract, artifact and termination failures;
- mapping from execution facts to validation status and error kind;
- multi-platform behavior;
- release-gate consequences;
- security requirements;
- testing and observability.

The core rule is:

> A process timeout, cancellation or launch failure is an execution error, not a normal GF validation failure.

GF Wordbench must preserve every available piece of evidence while avoiding false claims that GF completed normally.

---

## 2. Scope

This specification governs processes used for:

- GF version probing;
- individual source-file compilation;
- checkpoint compilation;
- entrypoint validation;
- PGF construction;
- `.gfs` scenario execution;
- parsing;
- linearization;
- morphology;
- generation;
- missing-function inspection;
- grammar introspection;
- optional diagnostic tools present in the static registry defined by ADR-0013.

It governs:

- executable selection;
- ordered arguments;
- working directory;
- environment overrides;
- stdin;
- stdout;
- stderr;
- process start;
- deadlines;
- timeout detection;
- cancellation requests;
- soft termination;
- forced termination;
- child-process containment;
- stream draining;
- output limits;
- process result construction;
- raw evidence;
- required artifact trust;
- failure mapping;
- retries;
- cleanup;
- tests.

It does not govern:

- GF source semantics;
- GF diagnostic wording;
- diagnostic pattern parsing;
- project-specific linguistic acceptance criteria;
- detailed report formatting;
- persisted JSON field-by-field schemas;
- operating-system adapter internals beyond the required behavioral contract;
- discovery, orchestration or aggregation of several Wordbench workspaces;
- `gf-portfolio` storage, indexing, readiness computation or process execution.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **PROCESS REQUEST**: complete immutable description of one external invocation.
- **PROCESS RESULT**: structured record of one invocation attempt.
- **EXECUTION STATE**: process-level terminal state.
- **VALIDATION STATUS**: `OK`, `FAIL`, `ERROR` or `SKIPPED`.
- **TIMEOUT**: configured deadline expired before normal process completion.
- **CANCELLATION**: user or controller requested that execution stop.
- **LAUNCH FAILURE**: operating system did not successfully start the requested executable.
- **TOOL FAILURE**: the tool started and completed but reported failure.
- **CONTRACT FAILURE**: the tool returned, but its response violated the declared request/response contract.
- **ARTIFACT FAILURE**: a required current-operation artifact is absent, invalid or untrusted.
- **CAPTURE FAILURE**: GF Wordbench could not safely capture stdout, stderr or required execution evidence.
- **TERMINATION FAILURE**: GF Wordbench could not confirm that the owned process tree stopped.
- **SOFT TERMINATION**: first cooperative or graceful stop attempt.
- **FORCED TERMINATION**: platform-specific hard stop after the grace period.
- **GRACE PERIOD**: finite interval between soft and forced termination.
- **OWNED PROCESS TREE**: root process launched by GF Wordbench and its attributable descendants.
- **PARTIAL EVIDENCE**: captured evidence from an operation that did not complete normally.
- **CURRENT ARTIFACT**: artifact proven to belong to the present invocation.
- **MONOTONIC CLOCK**: clock suitable for measuring elapsed time and deadlines.
- **WALL CLOCK**: civil timestamp used for reporting.
- **DRAINING**: reading remaining stdout/stderr until pipe closure or a bounded post-termination limit.

---

## 4. Authority boundaries

## 4.1 Process runner owns

- process creation;
- executable invocation;
- process-tree containment;
- timeout enforcement;
- cancellation handling;
- stdout and stderr capture;
- stdin delivery;
- elapsed-time measurement;
- terminal execution state;
- termination attempts;
- raw process evidence paths;
- process-level warnings.

## 4.2 Operation owner owns

Examples:

- compiler owns compilation request construction;
- scenario runner owns scenario request construction;
- PGF builder owns release-build request construction;
- version probe owns version-probe request construction.

The operation owner defines:

- operation identity;
- arguments;
- working directory;
- stdin source;
- timeout class;
- expected artifacts;
- operation-specific success criteria.

## 4.3 Diagnostic parser owns

- interpretation of GF text;
- diagnostic records;
- candidate error kind from GF evidence;
- primary diagnostic selection.

It does not determine timeout or launch failure from message text alone.

## 4.4 Result builder owns

- validation status;
- error kind;
- primary message;
- combination of process, diagnostic and artifact evidence.

## 4.5 Classifier owns

```text
ok
direct
downstream
ambiguous
noise
skipped
```

The process runner MUST NOT assign causal file ownership.

## 4.6 Workspace and Portfolio boundary

Every process request belongs to exactly one active Wordbench project and one run.

GF Wordbench MUST NOT:

- discover executable work from a Portfolio workspace registry;
- launch GF or diagnostic tools for several active projects in one request;
- expose its private process runner as a required `gf-portfolio` API;
- require Portfolio code, state, storage, configuration or services;
- write Portfolio aggregation fields into process results.

The independent `gf-portfolio` product may consume completed public Wordbench
artifacts. That read-only relationship does not change process ownership and
creates no reverse runtime dependency.

---

## 5. Required separation of dimensions

The framework must keep these concepts separate:

```text
execution_state
validation_status
error_kind
diagnostic_class
exit_code
termination_succeeded
```

Example: normal GF type failure.

```text
execution_state       = completed
validation_status     = FAIL
error_kind            = TYPE
diagnostic_class      = direct | downstream | ambiguous
exit_code             = non-zero or tool-specific
termination_succeeded = true
```

Example: timeout.

```text
execution_state       = timed_out
validation_status     = ERROR
error_kind            = TIMEOUT
diagnostic_class      = ambiguous unless stronger classifier evidence exists
exit_code             = null or post-termination code
termination_succeeded = true | false
```

Example: user cancellation.

```text
execution_state       = cancelled
validation_status     = ERROR
error_kind            = OTHER unless a more precise non-GF cause applies
diagnostic_class      = ambiguous
exit_code             = null or post-termination code
termination_succeeded = true | false
```

Example: executable missing.

```text
execution_state       = launch_failed
validation_status     = ERROR
error_kind            = TOOL | CONFIG | IO
diagnostic_class      = ambiguous
exit_code             = null
termination_succeeded = true
```

---

## 6. Canonical execution states

Persisted public execution states:

```text
completed
timed_out
cancelled
launch_failed
```

These values describe how the invocation ended.

They are not validation statuses.

## 6.1 `completed`

The operating system started the process and GF Wordbench observed normal process termination before timeout or cancellation control took effect.

`completed` does not mean validation passed.

Possible validation outcomes:

```text
OK
FAIL
ERROR
```

## 6.2 `timed_out`

The configured deadline expired before normal completion.

The runner initiated termination.

A timed-out process MUST NOT be reported as a normal GF failure.

## 6.3 `cancelled`

A user or controlling system requested cancellation before timeout won the terminal-state race.

The runner initiated termination.

Cancellation is not equivalent to timeout.

## 6.4 `launch_failed`

The requested executable did not start.

Examples:

- executable does not exist;
- executable is not executable;
- working directory does not exist;
- permission denied;
- invalid process arguments;
- process creation failed;
- required stream file could not be prepared before launch.

No GF exit code exists.

---

## 7. Additional process facts

The execution state is supplemented by explicit facts:

```text
started
pid
exit_code
started_at
finished_at
duration_ms
deadline_reached
cancellation_requested
soft_termination_attempted
forced_termination_attempted
termination_succeeded
process_tree_contained
stdout_truncated
stderr_truncated
capture_complete
launch_error
termination_error
```

Persisted fields are defined by `docs/PERSISTED_SCHEMA_LOCK.md` and the owning schema references.

The internal model preserves enough detail for reliable reporting, testing, containment and artifact-trust decisions.

---

## 8. Canonical process request

A process request should contain:

```text
operation_id
operation_kind
executable
arguments
working_directory
environment_overrides
stdin_mode
stdin_source
encoding
timeout_seconds
termination_grace_seconds
stdout_path
stderr_path
stdout_limit_bytes
stderr_limit_bytes
combined_output_limit_bytes
create_process_tree_boundary
shell
```

Optional fields may include:

```text
expected_artifacts
capability_requirements
cancellation_token
redacted_argument_indexes
```

---

## 9. Process-request invariants

- The request is fully resolved before launch.
- The executable is explicit.
- Arguments are an ordered list.
- The working directory is explicit.
- `shell` is `false` for normal GF execution.
- Timeout is finite and positive.
- Grace period is finite and non-negative.
- Output limits are finite and positive when enabled.
- Capture paths belong to the owned run directory.
- Environment overrides are explicit.
- Required directories exist before launch.
- Paths are validated before launch.
- The request contains no unresolved active-language placeholders.
- The operation identity is stable enough for logs and results.
- A process request is not mutated after launch begins.

---

## 10. Executable and argument contract

Preferred conceptual invocation:

```python
subprocess invocation:
    executable = resolved explicit path
    arguments  = ordered list
    shell      = false
```

GF Wordbench MUST NOT create a single unquoted command string for normal execution.

The executed command record must preserve:

- executable;
- argument order;
- argument values;
- working directory;
- allowed environment overrides.

A rendered command for humans is derived evidence.

It must not replace the structured request.

---

## 11. Working-directory contract

Every invocation has an explicit working directory.

It MUST NOT depend on:

- terminal current directory;
- GUI process directory;
- IDE defaults;
- launcher shortcut directory;
- previous process execution;
- global shell state.

A missing or inaccessible working directory is a launch/configuration error.

It is not a GF source error.

---

## 12. Environment contract

The child environment is constructed from a documented policy.

The runner may use:

```text
inherited safe baseline
    + explicit operation overrides
```

Rules:

- required overrides are recorded;
- secret values are not written to reports;
- complete environment dumps are prohibited;
- environment behavior is deterministic under equivalent configuration;
- local `GF_LIB_PATH` or equivalent variables must not silently override resolved project configuration unless policy explicitly allows it;
- environment construction failure occurs before launch;
- untrusted project text must not become an environment variable name.

---

## 13. Standard-input contract

Stdin mode is explicit:

```text
none
text
bytes
file
```

For `.gfs` execution, the selected external-tool contract determines whether GF receives:

- the script path;
- script text on stdin;
- another supported batch mechanism.

Rules:

- encoding is explicit;
- stdin is closed when input delivery completes;
- input delivery is bounded;
- an input write failure is recorded;
- broken pipe does not erase output already captured;
- interactive input is prohibited unless a separate accepted contract enables it;
- the runner must not wait indefinitely for an unhandled prompt.

---

## 14. Standard-output and standard-error contract

Stdout and stderr are separate raw streams.

The runner MUST capture both.

Canonical evidence includes:

```text
stdout_path
stderr_path
stdout_truncated
stderr_truncated
```

The runner MUST NOT infer:

```text
stdout = success
stderr = failure
```

GF may emit diagnostics on either stream.

---

## 15. Concurrent stream draining

Stdout and stderr must be drained without creating a pipe deadlock.

The process adapter ensures that:

- one full pipe cannot permanently block the child while the other stream is being read;
- both streams remain attributable;
- line ordering within each stream is preserved;
- output limits do not cause the runner to stop draining silently;
- stream reader failure is reported.

Permitted adapter strategies include:

- dedicated reader threads;
- asynchronous subprocess streams;
- direct file redirection where it preserves required evidence;
- another tested platform-safe strategy.

The behavioral contract matters more than the internal technique.

---

## 16. Capture-file preparation

Capture destinations SHOULD be prepared before process launch.

Preparation includes:

- validating containment inside the run root;
- creating parent directories;
- opening files or confirming writable destinations;
- recording the resolved capture paths.

If capture setup fails before the child starts:

```text
execution_state = launch_failed
validation_status = ERROR
error_kind = IO
```

No GF failure is claimed.

---

## 17. Encoding contract

UTF-8 is the framework default.

The process layer must define:

- input encoding;
- output decoding;
- decoding error policy;
- newline handling;
- whether raw bytes are additionally retained.

Decoding errors MUST NOT silently discard bytes.

A lossy decoding strategy must record:

```text
decoding_lossy = true
```

A decoding failure may cause:

```text
validation_status = ERROR
error_kind = IO | TOOL
```

Raw recoverable evidence should remain available.

---

## 18. Output limits

Every process class SHOULD have bounded output.

Limits may include:

```text
stdout_limit_bytes
stderr_limit_bytes
combined_output_limit_bytes
maximum_line_length
```

Purposes:

- prevent disk exhaustion;
- contain runaway generation;
- avoid unbounded memory;
- keep reports manageable;
- protect automation.

---

## 19. Output-limit behavior

When a stream reaches its retained-output limit:

- the retained artifact is marked truncated;
- the runner continues draining or safely discarding further bytes so the child cannot block;
- truncation is recorded in the process result;
- the retained prefix remains raw partial evidence;
- exact absence claims become unsafe;
- release success MUST NOT depend on truncated required evidence;
- the operation normally ends as `ERROR` when complete evidence is required.

Canonical marker in a derived report may state:

```text
OUTPUT TRUNCATED
```

The marker is not inserted into the raw GF byte stream while still calling that file unmodified raw output.

---

## 20. Time measurement

Timeout enforcement uses a monotonic clock.

Wall-clock timestamps are used for reporting.

The runner records:

```text
started_at
finished_at
duration_ms
```

Rules:

- `duration_ms` is non-negative;
- system clock changes must not extend or shorten the deadline;
- timeout comparison uses the configured deadline;
- timeout enforcement includes process runtime, not unrelated earlier orchestration;
- startup preparation time may be measured separately when useful.

---

## 21. Timeout requirement

Every external process MUST have a finite timeout.

Operation classes include:

```text
version_probe
file_compile
checkpoint_compile
pgf_build
scenario
generation
diagnostic_introspection
registered_optional_tool
```

No normal validation operation uses an infinite timeout.

A registered optional tool uses the timeout, mutability, network, output-limit
and evidence policies declared in its ADR-0013 registry entry. Arbitrary
commands and dynamically loaded executable plugins are prohibited.

A diagnostic mode may use a larger timeout.

It remains finite.

---

## 22. Timeout configuration ownership

Canonical timeout defaults belong to configuration.

Operation components select a timeout class.

They MUST NOT hardcode conflicting independent defaults.

Conceptual model:

```text
RunConfig
    → timeout policy
        → operation timeout
            → ProcessRequest.timeout_seconds
```

CLI and GUI overrides must resolve through the same configuration builder.

---

## 23. Timeout validation

Timeout values must be:

- finite;
- positive;
- represented in one documented unit;
- within safe platform and runtime bounds;
- serializable when persisted;
- validated before process launch.

Invalid examples:

```text
0
negative value
NaN
infinity
unparseable text
```

An invalid timeout is:

```text
validation_status = ERROR
error_kind = CONFIG
```

The process is not launched.

---

## 24. Deadline creation

The runner computes:

```text
deadline = monotonic_start + timeout
```

The deadline is fixed for the invocation.

It MUST NOT be silently extended because:

- output is still arriving;
- the process appears busy;
- one stage is important;
- the GUI remains responsive;
- a report is waiting.

A deliberate extension policy would require a separate versioned contract.

---

## 25. Timeout detection

A timeout occurs when the deadline is reached before confirmed normal process completion.

Required actions:

1. record that the deadline was reached;
2. set terminal cause candidate to timeout;
3. stop supplying additional input;
4. begin process-tree termination;
5. continue bounded output capture;
6. wait for termination completion;
7. close streams;
8. construct a timed-out process result;
9. preserve partial evidence.

---

## 26. Cancellation

Cancellation is an explicit controller request.

Sources may include:

- GUI cancel action;
- CLI interrupt handling;
- audit-level cancellation;
- CI controller cancellation;
- application shutdown.

Cancellation must use a shared cancellation mechanism.

Operation components MUST NOT invent incompatible cancellation flags.

---

## 27. Cancellation polling

The process runner must observe cancellation while the process is active.

The design must not require waiting for the full timeout before cancellation takes effect.

Cancellation response should be prompt within the constraints of safe process and stream handling.

No exact latency guarantee is defined without measured platform support.

---

## 28. Timeout versus cancellation race

Timeout and cancellation may occur close together.

The terminal state must be deterministic.

Canonical rule:

1. if cancellation was recorded before the monotonic deadline, use `cancelled`;
2. otherwise, if the deadline was reached before normal completion, use `timed_out`;
3. if ordering cannot be established safely, prefer the event recorded first by the centralized runner;
4. record both facts when both occurred.

A user cancellation after the timeout deadline does not rewrite the state to `cancelled`.

---

## 29. External unexpected termination

A process may stop because of:

- operating-system signal;
- console closure;
- external task manager;
- machine shutdown;
- crash;
- library abort.

If GF Wordbench did not request cancellation and the timeout did not fire:

```text
execution_state = completed
```

when the operating system reports process termination.

The abnormal exit is interpreted through:

- exit code;
- signal/termination metadata when available;
- diagnostics;
- artifact checks.

It is normally `FAIL` or `ERROR` depending on whether the tool returned interpretable validation evidence.

---

## 30. Process-tree ownership

GF Wordbench must terminate only the owned process tree.

Ownership begins with the process created for the request.

The runner must not terminate processes based only on:

- executable name;
- process image name;
- window title;
- global command search;
- user account.

Name-based global process killing is prohibited.

---

## 31. Process-tree boundary

The runner SHOULD establish a platform-appropriate process-tree boundary at launch.

The boundary must support, as far as the platform permits:

- identifying the root process;
- attributing descendants;
- sending a soft termination request;
- forcing termination;
- confirming that owned descendants stopped.

If complete containment cannot be guaranteed:

```text
process_tree_contained = false
```

must be recorded internally or as a warning.

---

## 32. Termination sequence

Canonical termination sequence:

```text
1. stop stdin delivery
2. mark termination cause
3. request soft termination of owned process tree
4. wait finite grace period
5. force termination of remaining owned processes
6. wait finite forced-termination period
7. drain stdout and stderr within bounds
8. close handles and files
9. confirm terminal state
10. record termination outcome
```

No step may wait indefinitely.

---

## 33. Soft termination

Soft termination is the first attempt.

Its purpose is to allow:

- orderly GF shutdown;
- stream flushing;
- normal handle closure;
- reduced artifact corruption.

The exact platform mechanism belongs to the process adapter.

Soft termination must not rely on an interactive prompt.

---

## 34. Grace period

The grace period is:

- finite;
- configurable centrally;
- distinct from the operation timeout;
- measured with a monotonic clock.

A zero grace period MAY be used only when an operation or platform policy explicitly requires immediate force.

The grace period is not added to the original validation timeout as extra allowed execution.

It exists only for cleanup.

---

## 35. Forced termination

If the owned process tree remains active after the grace period, the runner MUST attempt forced termination.

Forced termination:

- is recorded;
- invalidates normal process success;
- may leave partial artifacts;
- may produce an operating-system exit code;
- does not turn timeout or cancellation into a GF failure.

---

## 36. Termination confirmation

Termination succeeds only when the runner confirms, within policy limits, that the root process and attributable owned descendants have stopped.

Fields:

```text
termination_succeeded
termination_error
soft_termination_attempted
forced_termination_attempted
```

If termination cannot be confirmed:

```text
termination_succeeded = false
validation_status = ERROR
```

The original execution state remains `timed_out` or `cancelled`.

---

## 37. Termination failure

A termination failure is serious because a process may continue:

- consuming CPU;
- writing files;
- holding locks;
- mutating artifacts;
- blocking cleanup;
- interfering with later runs.

Required behavior:

- record the failure prominently;
- do not finalize affected artifacts as trustworthy;
- do not start a conflicting dependent operation;
- preserve current evidence;
- warn that manual process cleanup may be required;
- block release readiness;
- avoid deleting directories possibly still in use.

---

## 38. Post-termination stream draining

After termination is requested, the runner should continue reading stdout and stderr until:

- pipes close;
- the bounded drain deadline expires;
- a capture failure occurs.

This preserves terminal diagnostics.

The drain deadline is finite.

A stuck pipe or inherited child handle must not block the audit indefinitely.

---

## 39. Stream closure

Before constructing a complete process result:

- stdin writer is closed;
- stdout capture is closed;
- stderr capture is closed;
- process handles are released where supported;
- capture errors are recorded.

A result with open stream writers is incomplete.

Run finalization must not hash an artifact still being written.

---

## 40. Partial evidence

Timeouts, cancellations and crashes may produce partial evidence.

Partial evidence may include:

- command record;
- stdout prefix;
- stderr prefix;
- diagnostics emitted before termination;
- incomplete scenario markers;
- partially written `.gfo`;
- partially written `.pgf`;
- temporary files;
- process metadata.

Partial evidence is retained for diagnosis.

It is not automatically valid acceptance evidence.

---

## 41. Partial-evidence labeling

The process result must make incompleteness explicit through fields such as:

```text
execution_state
stdout_truncated
stderr_truncated
capture_complete
termination_succeeded
artifacts_trusted
```

Reports must not describe partial evidence as complete.

---

## 42. Artifact trust after abnormal termination

Artifacts produced during:

```text
timed_out
cancelled
termination failure
capture failure
```

are untrusted by default.

They MUST NOT satisfy required artifact checks.

Examples:

- a `.gfo` existing after timeout does not prove successful compilation;
- a `.pgf` existing after forced termination does not prove release success;
- a normalized scenario output from incomplete markers does not prove scenario success.

An artifact may be retained and catalogued as partial or untrusted evidence.

---

## 43. Current-artifact proof

A required tool artifact counts only when:

- the process launched;
- the operation completed normally;
- timeout and cancellation did not occur;
- fatal diagnostics do not invalidate the operation;
- the artifact exists;
- the artifact is non-empty when required;
- the artifact belongs to the current invocation;
- required integrity checks pass.

A pre-existing stale artifact is not current evidence.

---

## 44. Launch failures

Launch failures include:

```text
executable_not_found
permission_denied
invalid_working_directory
invalid_argument
environment_construction_failure
capture_setup_failure
process_creation_failure
resource_exhaustion
```

The public error kind uses the canonical vocabulary:

```text
TOOL
CONFIG
IO
OTHER
```

The detailed launch reason may be stored separately.

---

## 45. Launch-failure evidence

The runner records:

```text
requested executable
ordered arguments
working directory
safe environment summary
launch error type
launch error message
start attempt time
stdout path if prepared
stderr path if prepared
```

No exit code is invented.

No GF diagnostic is invented.

---

## 46. Tool failure

A tool failure occurs when:

- the process launched;
- it completed;
- it returned non-success evidence;
- the response remains interpretable.

Examples:

- GF syntax error;
- GF type error;
- GF shell command failure;
- PGF build failure with diagnostics.

Typical mapping:

```text
execution_state = completed
validation_status = FAIL
error_kind = TYPE | SYNTAX | SCRIPT | INTERNAL | OTHER
```

---

## 47. Contract failure

A contract failure occurs when the process completed but the external response violated the declared contract.

Examples:

- zero exit but required scenario markers absent;
- zero exit but required artifact absent;
- unsupported response shape;
- process did not produce required version information;
- command accepted with different semantics;
- expected stream evidence cannot be interpreted.

Typical mapping:

```text
execution_state = completed
validation_status = ERROR
error_kind = TOOL | OTHER
```

Some artifact-specific violations may use `FAIL` only when the project validation criterion itself was executed and clearly failed.

The operation specification decides.

---

## 48. Artifact failure

A required artifact failure includes:

- artifact absent;
- artifact empty when non-empty is required;
- artifact outside approved root;
- artifact stale;
- artifact produced before the current invocation;
- artifact modified after capture;
- artifact untrusted due to abnormal termination.

Typical mapping:

```text
validation_status = FAIL | ERROR
error_kind = TOOL | IO | OTHER
```

Use `FAIL` when the tool ran normally and the expected project artifact criterion failed.

Use `ERROR` when GF Wordbench cannot establish artifact integrity or ownership.

---

## 49. Capture failure

Capture failures include:

- stdout writer failure;
- stderr writer failure;
- disk full;
- permission change;
- path invalidation;
- reader thread failure;
- stream decoding infrastructure failure;
- stream deadlock containment failure.

A capture failure is:

```text
validation_status = ERROR
error_kind = IO
```

The runner must terminate the process if required evidence cannot be captured safely.

---

## 50. Stdin failure

Stdin failure includes:

- source file unreadable;
- encoding failure;
- pipe write failure;
- broken pipe before complete input;
- input size limit exceeded.

If GF terminated first with interpretable diagnostics, both facts may be recorded.

The result builder selects the highest-authority cause.

A required script not fully delivered cannot pass.

---

## 51. Internal runner failure

An unexpected framework exception during process management is:

```text
validation_status = ERROR
error_kind = INTERNAL | IO | OTHER
```

Required containment:

- attempt to terminate any started owned process;
- preserve available stdout and stderr;
- record the framework exception separately;
- do not convert it into a GF language error;
- do not hide it behind a generic non-zero exit.

---

## 52. Exit-code semantics

An exit code is evidence, not the complete diagnosis.

Rules:

- zero does not override fatal diagnostic text;
- zero does not override missing markers;
- zero does not override missing required artifacts;
- zero does not override gold mismatch;
- non-zero does not erase raw diagnostics;
- non-zero does not determine direct/downstream ownership;
- forced-termination exit codes are not normal GF exit codes;
- no exit code exists for launch failure.

---

## 53. Signal and platform termination metadata

Where the platform exposes additional termination metadata, the internal result MAY retain:

```text
signal
native_status
termination_source
```

This metadata is optional and platform-specific.

Portable logic must rely on canonical execution state and structured process facts.

---

## 54. Canonical validation statuses

```text
OK
FAIL
ERROR
SKIPPED
```

`CANCELLED` is not a validation status.

Cancellation is represented through:

```text
execution_state = cancelled
validation_status = ERROR
```

This preserves one validation vocabulary across file and scenario results.

---

## 55. Status mapping matrix

| Process condition | Execution state | Validation status | Default error kind |
|---|---|---|---|
| Normal success, all criteria pass | `completed` | `OK` | `OK` |
| GF completes with language/tool diagnostic failure | `completed` | `FAIL` | parsed kind |
| GF completes, gold mismatch | `completed` | `FAIL` | `OTHER` |
| Required current artifact absent after normal execution | `completed` | `FAIL` or `ERROR` | `TOOL` or `IO` |
| Response violates tool contract | `completed` | `ERROR` | `TOOL` |
| Timeout | `timed_out` | `ERROR` | `TIMEOUT` |
| User/controller cancellation | `cancelled` | `ERROR` | `OTHER` |
| Executable missing | `launch_failed` | `ERROR` | `TOOL` or `CONFIG` |
| Working directory invalid | `launch_failed` | `ERROR` | `CONFIG` |
| Capture setup fails | `launch_failed` | `ERROR` | `IO` |
| Capture fails after launch | applicable state | `ERROR` | `IO` |
| Termination cannot be confirmed | `timed_out` or `cancelled` | `ERROR` | original kind plus termination error |
| Stage deliberately not selected | no process | `SKIPPED` | `OK` or no error |

The result model may retain a detailed process-failure code in addition to the canonical error kind.

---

## 56. Primary messages

Recommended concise primary messages:

```text
Process timed out after <duration>.
Execution was cancelled.
Failed to launch GF executable.
Working directory is invalid.
Failed to capture process output.
Owned process tree could not be terminated.
Required artifact was not produced.
Process response violated the external-tool contract.
```

Messages must not include secrets.

Raw operating-system details may appear in bounded detail fields.

---

## 57. Diagnostic parsing after timeout

Partial stdout and stderr may be parsed.

Rules:

- timeout remains the primary execution failure;
- parsed diagnostics remain supporting evidence;
- incomplete multiline records are marked;
- absence of an error in partial output is not proof of absence;
- a parsed type or syntax diagnostic does not rewrite `error_kind=TIMEOUT` for the terminal process result;
- reports may show both timeout and last observed diagnostic.

---

## 58. Diagnostic parsing after cancellation

Partial output may be parsed for context.

Cancellation remains the primary execution state.

A cancellation requested after GF already completed does not retroactively cancel the operation.

---

## 59. Diagnostic parsing after launch failure

No GF diagnostic parsing is required when GF did not start.

Operating-system launch errors are process evidence.

They MUST NOT be sent through GF syntax/type regexes and presented as native GF diagnostics.

---

## 60. Scenario consequences

A scenario timeout means:

- required end markers may be missing;
- normalized exact output is incomplete;
- gold comparison cannot pass;
- partial stdout/stderr are retained;
- the scenario status is `ERROR`;
- `error_kind=TIMEOUT`;
- required release scenarios block release.

A user cancellation similarly produces `ERROR`, not an expected scenario `FAIL`.

---

## 61. Compilation consequences

A compile timeout means:

- produced `.gfo` files are untrusted;
- downstream compilation should not use them as current success artifacts;
- file result is `ERROR`;
- error kind is `TIMEOUT`;
- causal classification may remain ambiguous;
- dependent stages may be skipped or marked downstream according to classifier policy.

---

## 62. PGF-build consequences

A PGF build timeout means:

- any `.pgf` created during the operation is untrusted;
- release readiness fails;
- the artifact may be retained as partial evidence;
- the manifest must not mark it as a valid required release artifact;
- a later successful run must produce a new current artifact.

---

## 63. Version-probe consequences

A version-probe timeout or launch failure occurs before language validation.

The framework should fail fast unless an explicitly documented compatibility mode permits another proven source of version information.

Silent continuation with an unknown executable is prohibited in strict release mode.

---

## 64. Audit-level cancellation

When an audit is cancelled:

1. stop scheduling new external operations;
2. signal cancellation to active runners;
3. terminate active owned process trees;
4. wait for bounded cleanup;
5. close evidence streams;
6. preserve completed and partial results;
7. mark unexecuted work as skipped or cancelled-context according to result policy;
8. finalize a partial run report when safely possible.

The audit must not claim a complete release result.

---

## 65. Dependent-stage behavior

After an execution `ERROR`, orchestration decides whether to:

```text
stop
skip dependent stage
continue independent stages
enter diagnostic collection
```

Rules:

- release-required dependencies cannot be silently skipped;
- independent diagnostic collection may continue;
- the original execution error remains visible;
- downstream classification belongs to the classifier;
- no dependent stage may consume untrusted artifacts as successful inputs.

---

## 66. Continue-on-error policy

Continue-on-error is an orchestration policy.

It does not change the process result.

A timed-out file remains `ERROR` even when the audit continues.

Diagnostic mode may continue more independent work than release mode.

---

## 67. Retry policy

Automatic retries are disabled by default.

Reasons:

- retries can hide nondeterminism;
- retries can create stale artifacts;
- retries can duplicate side effects;
- retries complicate provenance;
- retries may make timeouts appear successful.

A permitted retry must be operation-specific and explicit.

---

## 68. Retry requirements

When retries are enabled:

- maximum attempts are finite;
- each attempt has its own process result;
- each attempt has separate raw evidence paths;
- the reason is documented;
- artifacts from failed attempts are untrusted;
- the final result exposes attempt count;
- no retry occurs silently after timeout;
- release reports show that retries occurred.

Recommended attempt path suffix:

```text
.attempt-01
.attempt-02
```

or another deterministic owned convention.

---

## 69. No implicit timeout retry

A timeout MUST NOT trigger an automatic immediate rerun under the same hidden conditions.

An explicit user retry creates a new operation attempt or run.

This preserves reproducibility.

---

## 70. Cleanup after launch failure

When launch fails:

- close prepared stream files;
- remove only clearly temporary internal files;
- retain useful launch evidence;
- do not delete unrelated run artifacts;
- do not attempt process termination when no process started.

---

## 71. Cleanup after timeout or cancellation

Cleanup includes:

- process-tree termination;
- stream draining;
- handle closure;
- marking partial artifacts;
- removing temporary files only when safe;
- preserving raw evidence;
- preventing stale artifacts from satisfying later operations.

Cleanup must not delete evidence required to diagnose the timeout.

---

## 72. Temporary files

Temporary process files should use explicit names:

```text
<name>.tmp
<name>.partial
```

A temporary file is not a successful required artifact.

After successful completion:

- validate;
- atomically replace or move when appropriate;
- remove temporary residue.

After abnormal termination:

- retain or remove according to recovery policy;
- never relabel partial bytes as finalized without validation.

---

## 73. Process-result model

A canonical internal result should contain:

```text
operation_id
operation_kind
execution_state
started
pid
exit_code
started_at
finished_at
duration_ms
deadline_reached
cancellation_requested
soft_termination_attempted
forced_termination_attempted
termination_succeeded
process_tree_contained
stdout_path
stderr_path
stdout_size_bytes
stderr_size_bytes
stdout_truncated
stderr_truncated
capture_complete
decoding_lossy
launch_error
termination_error
warnings
produced_artifacts
```

Compatibility fields may include:

```text
timed_out
launch_failed
```

These should be derived from `execution_state`, not independently mutable.

---

## 74. Boolean compatibility invariants

If compatibility fields exist:

```text
timed_out = execution_state == "timed_out"
launch_failed = execution_state == "launch_failed"
cancelled = execution_state == "cancelled"
```

Conflicting serialized values are invalid.

Canonical writers should prefer one source of truth.

---

## 75. Process failure code

A detailed internal process failure code MAY use:

```text
none
executable_not_found
permission_denied
invalid_working_directory
process_creation_failure
stdin_failure
stdout_capture_failure
stderr_capture_failure
decoding_failure
timeout
cancelled
soft_termination_failure
forced_termination_failure
process_tree_unconfirmed
output_limit_exceeded
unexpected_exit
contract_failure
artifact_failure
internal_runner_failure
```

This vocabulary is not a replacement for the canonical persisted `error_kind`.

If persisted, it requires schema ownership and versioning.

---

## 76. Process warnings

Warnings may include:

- process-tree containment unavailable;
- soft termination unsupported;
- output truncated;
- decoding lossy;
- unknown native exit metadata;
- cleanup incomplete;
- local environment fallback used.

Warnings remain visible.

They do not silently convert to success.

---

## 77. Artifact manifest behavior

The manifest may catalog partial evidence.

It must distinguish required trusted artifacts from partial/untrusted files.

A timeout-produced `.pgf` must not receive the same semantic role as a verified release PGF.

The manifest does not decide success.

---

## 78. Summary behavior

`summary.json` should preserve:

- execution state;
- validation status;
- error kind;
- duration;
- exit code;
- raw paths;
- timeout/cancellation facts;
- artifact references;
- primary message.

Human reports should render timeout and cancellation explicitly.

They must not label them as GF syntax errors.

---

## 79. AI-ready report behavior

`AI_READY.md` may include:

- command identity;
- execution state;
- timeout duration;
- termination result;
- partial diagnostic excerpt;
- raw evidence paths;
- next safe investigation step.

It must state when evidence is incomplete.

It must not guess a linguistic root cause from a timeout alone.

---

## 80. Logging requirements

The master log should record, in order:

```text
process request accepted
process launch attempted
process started
timeout deadline
cancellation request
soft termination
forced termination
process exit observed
stream capture closed
process result finalized
```

Sensitive arguments are redacted according to policy.

The executed command remains structurally reproducible without exposing secrets.

---

## 81. Live progress reporting

CLI and GUI may display:

- operation;
- elapsed time;
- configured timeout;
- cancellation availability;
- termination progress.

Live display is not the source of truth.

The structured process result is authoritative.

---

## 82. Determinism

For equivalent requests and observed operating-system responses, result construction must be deterministic.

The runner must not depend on:

- locale-dependent exception wording for classification;
- unordered callbacks;
- current GUI state;
- wall-clock adjustments;
- process name searches;
- hidden shell configuration;
- terminal width.

Platform-native messages may be retained as detail.

Canonical failure codes remain stable.

---

## 83. Security

Process execution crosses a trust boundary.

The runner MUST:

- use ordered arguments;
- avoid an implicit shell;
- validate executable and working-directory paths;
- contain the owned process tree;
- bound output;
- bound runtime;
- avoid killing unrelated processes;
- avoid complete environment dumps;
- redact secrets from rendered commands;
- treat `.gfs` scripts as executable input;
- permit only statically registered optional executables and argument templates;
- enforce each registered tool's mutability and network policy;
- prevent unauthorized shell escape;
- preserve evidence of security-related termination.

---

## 84. Resource exhaustion

Launch may fail because of:

- process limit;
- memory pressure;
- file-handle exhaustion;
- disk exhaustion;
- pipe creation failure.

These are framework/environment errors.

They are not GF language failures.

Recommended mapping:

```text
validation_status = ERROR
error_kind = IO | TOOL | OTHER
```

The detailed native exception remains available.

---

## 85. Disk-full handling

Disk-full during capture is especially dangerous.

Required behavior:

1. record capture failure if possible;
2. terminate the owned process tree;
3. avoid pretending streams are complete;
4. preserve any safely closed evidence;
5. avoid further large report generation;
6. mark the run partial;
7. surface cleanup guidance.

A disk-full event cannot produce a trusted release run.

---

## 86. Handle and file-lock handling

The process layer must close owned handles deterministically.

After process completion or termination:

- raw files become immutable;
- artifact verification occurs only after handles close;
- cleanup waits only within bounded policy;
- lingering locks are reported;
- run finalization does not proceed as complete while required files remain open.

---

## 87. Windows behavioral requirements

Windows support must handle:

- explicit `gf.exe` paths;
- paths containing spaces;
- Unicode paths;
- no implicit command shell;
- owned-process-tree termination;
- child processes;
- console-less GUI launch;
- CRLF output;
- file locking;
- cancellation;
- forced termination;
- stream draining.

A dedicated Windows process adapter owns these platform mechanics.

Platform details must not change public result semantics.

---

## 88. POSIX behavioral requirements

POSIX support must handle:

- explicit executable paths;
- process-group or equivalent owned-tree containment;
- signals;
- Unicode paths;
- LF output;
- cancellation;
- forced termination;
- child processes;
- stream draining;
- exit status and optional signal metadata.

Platform details must not change public result semantics.

---

## 89. Unsupported containment behavior

If a platform cannot guarantee complete process-tree containment:

- the limitation is documented;
- `process_tree_contained=false` is recorded internally;
- strict release policy may reject operations capable of spawning descendants;
- termination warnings remain visible;
- no unsafe global process-kill fallback is used.

---

## 90. GUI integration

The GUI:

- constructs requests through shared bootstrap/configuration;
- invokes audit orchestration;
- sends cancellation through the shared token;
- does not launch GF directly;
- displays terminal structured state;
- does not invent a separate timeout policy.

Closing the GUI while a process is active must follow application-shutdown cancellation policy.

---

## 91. CLI integration

The CLI:

- uses the same timeout configuration;
- maps interrupt handling to cancellation;
- waits for bounded process cleanup;
- returns an exit code consistent with terminal validation status;
- prints raw evidence paths for failures when available;
- does not bypass process-tree cleanup.

Repeated interrupts may request immediate forced cleanup, but the behavior must be explicit and tested.

---

## 92. CI integration

CI must:

- use finite internal process timeouts;
- avoid relying only on an outer CI timeout;
- publish partial evidence when safe;
- distinguish GF failure from infrastructure timeout;
- avoid automatic hidden retries;
- block release on timeout, cancellation, launch or termination failure.

An outer CI kill may prevent cleanup.

This limitation should be documented in CI procedures.

---

## 93. Release-gate rules

A release run is not ready when any required operation is:

```text
timed_out
cancelled
launch_failed
termination_succeeded = false
capture_complete = false
```

A required artifact from such an operation is untrusted.

No release exception may silently convert an execution error into `OK`.

---

## 94. Diagnostic-mode rules

Diagnostic mode may:

- use longer finite timeouts;
- retain more partial evidence;
- continue independent operations;
- include process traces.

It must not:

- use infinite timeouts;
- weaken process-tree cleanup;
- treat truncated output as complete;
- modify validation status semantics.

---

## 95. Quick-mode rules

Quick mode may use shorter configured timeouts for fast feedback.

A timeout remains `ERROR`.

Quick mode must not hide it as a skipped validation.

---

## 96. Checkpoint-mode rules

A required checkpoint timeout:

- blocks that checkpoint;
- invalidates dependent checkpoint success;
- retains partial evidence;
- is not a syntax/type `FAIL`;
- may allow independent diagnostic work to continue.

---

## 97. Operation-specific timeout policy

Each operation class should document:

```text
default timeout source
allowed override
grace period source
output limits
artifact trust requirements
retry policy
```

The numeric defaults belong to configuration documentation.

This file defines semantics, not arbitrary project-specific numbers.

---

## 98. Timeout-change compatibility

Changing a default timeout can change observed outcomes.

A timeout change requires review of:

- configuration;
- CLI and GUI;
- process runner;
- tests;
- CI behavior;
- performance expectations;
- release behavior;
- documentation.

A shorter timeout may create new `ERROR` results.

A longer timeout may increase resource exposure.

---

## 99. Failure-precedence model

Multiple failures can occur.

Canonical precedence for terminal execution and result interpretation:

1. launch failure;
2. cancellation or timeout terminal state;
3. termination failure;
4. capture failure;
5. internal runner failure;
6. contract/artifact failure;
7. parsed GF failure;
8. warning only.

This ordering identifies the highest-authority condition preventing reliable completion.

Supporting failures remain recorded.

---

## 100. Example: normal GF failure

Observed:

```text
process started
exit code non-zero
stdout/stderr captured completely
GF type diagnostic recognized
process tree exited normally
```

Result:

```text
execution_state = completed
validation_status = FAIL
error_kind = TYPE
```

---

## 101. Example: timeout with diagnostics

Observed:

```text
process started
partial type diagnostic emitted
deadline reached
soft termination attempted
forced termination required
streams drained
```

Result:

```text
execution_state = timed_out
validation_status = ERROR
error_kind = TIMEOUT
forced_termination_attempted = true
```

The type diagnostic remains supporting evidence.

---

## 102. Example: cancellation

Observed:

```text
process started
user requested cancellation before deadline
soft termination succeeded
partial stdout retained
```

Result:

```text
execution_state = cancelled
validation_status = ERROR
error_kind = OTHER
termination_succeeded = true
```

---

## 103. Example: missing executable

Observed:

```text
gf.exe path does not exist
process not started
```

Result:

```text
execution_state = launch_failed
validation_status = ERROR
error_kind = TOOL
exit_code = null
```

---

## 104. Example: invalid working directory

Observed:

```text
project root does not exist
process not started
```

Result:

```text
execution_state = launch_failed
validation_status = ERROR
error_kind = CONFIG
```

---

## 105. Example: output capture failure

Observed:

```text
process started
stdout capture disk write fails
owned tree terminated
stderr retained partially
```

Result:

```text
validation_status = ERROR
error_kind = IO
capture_complete = false
```

Execution state reflects whether termination was caused by cancellation/timeout or internal containment.

---

## 106. Example: zero exit, missing artifact

Observed:

```text
process completed with zero exit
no fatal diagnostic
required PGF absent
```

Result:

```text
execution_state = completed
validation_status = FAIL or ERROR according to artifact contract
error_kind = TOOL
```

It is never `OK`.

---

## 107. Example: timeout with leftover child

Observed:

```text
deadline reached
root process stops
owned child remains
forced tree termination cannot be confirmed
```

Result:

```text
execution_state = timed_out
validation_status = ERROR
error_kind = TIMEOUT
termination_succeeded = false
```

A prominent termination warning is required.

---

## 108. Unit-test structure

Recommended:

```text
tests/process/
├── test_process_request.py
├── test_process_launch.py
├── test_process_capture.py
├── test_process_timeout.py
├── test_process_cancellation.py
├── test_process_termination.py
├── test_process_tree.py
├── test_process_output_limits.py
├── test_process_encoding.py
├── test_process_artifact_trust.py
├── test_process_result.py
└── test_process_security.py
```

---

## 109. Request tests

Required cases:

- explicit executable;
- ordered arguments;
- explicit working directory;
- `shell=false`;
- positive timeout;
- invalid zero timeout;
- invalid negative timeout;
- output paths outside run root;
- paths containing spaces;
- Unicode paths;
- safe environment overrides;
- secret redaction metadata.

---

## 110. Launch tests

Required cases:

- successful launch;
- executable missing;
- permission denied;
- invalid working directory;
- invalid executable format;
- capture directory missing and created;
- capture directory unwritable;
- resource-exhaustion simulation where feasible;
- no fake exit code on launch failure.

---

## 111. Capture tests

Required cases:

- stdout only;
- stderr only;
- both streams;
- empty streams;
- high-volume stdout;
- high-volume stderr;
- simultaneous high-volume streams;
- reader failure;
- disk write failure;
- stream closure;
- ordering within each stream.

---

## 112. Timeout tests

Required cases:

- process completes before timeout;
- process exceeds timeout;
- timeout boundary race;
- continuous output does not extend deadline;
- no output does not prevent timeout;
- partial output retained;
- timeout field mapping;
- `error_kind=TIMEOUT`;
- no normal GF failure classification;
- required artifact untrusted after timeout.

---

## 113. Cancellation tests

Required cases:

- cancellation before process start;
- cancellation after launch;
- cancellation before deadline;
- cancellation after timeout deadline;
- cancellation during stdin write;
- cancellation during stream drain;
- repeated cancellation request;
- CLI interrupt mapping;
- GUI cancellation-token mapping;
- partial evidence retained.

---

## 114. Termination tests

Required cases:

- soft termination succeeds;
- soft termination fails, force succeeds;
- force termination fails;
- child process exits;
- child process remains;
- tree containment unavailable;
- drain deadline expires;
- handles close;
- termination result deterministic.

---

## 115. Output-limit tests

Required cases:

- stdout limit;
- stderr limit;
- combined limit;
- process continues after retained prefix limit;
- pipes still drain;
- truncation flags;
- exact comparison cannot pass;
- release blocked;
- no disk exhaustion in fixture.

---

## 116. Encoding tests

Required cases:

- UTF-8 output;
- CRLF;
- Unicode language data;
- invalid byte sequence;
- lossy decoding recorded;
- stdin encoding error;
- BOM handling where relevant;
- no silent byte loss.

---

## 117. Artifact-trust tests

Required cases:

- artifact produced by normal success;
- artifact pre-exists before operation;
- artifact produced during timeout;
- artifact produced during cancellation;
- artifact empty;
- artifact outside approved root;
- artifact modified after completion;
- PGF untrusted after forced termination.

---

## 118. Status-mapping tests

Required matrix:

```text
completed + criteria pass → OK
completed + GF failure → FAIL
completed + contract failure → ERROR
timed_out → ERROR/TIMEOUT
cancelled → ERROR
launch_failed → ERROR
not selected → SKIPPED
```

Tests must prove cancellation is not a fifth validation status.

---

## 119. Multi-platform tests

At minimum:

### Windows

- native executable path;
- path with spaces;
- Unicode path;
- process-tree termination;
- CRLF;
- file locks;
- timeout;
- missing executable.

### POSIX

- executable path;
- process group;
- signal termination;
- child process;
- timeout;
- Unicode path;
- LF output.

Platform-specific tests may be conditionally marked.

---

## 120. Fake-process fixtures

Unit tests should use controlled helper executables capable of:

```text
sleep
write stdout
write stderr
write both concurrently
spawn child
ignore soft termination
exit with selected code
write partial artifact
close stdin early
emit invalid bytes
produce unbounded output within test limits
```

Fixtures must be safe, bounded and test-only.

---

## 121. Real-GF integration tests

A small GF fixture SHOULD test:

- version probe;
- successful compile;
- failing compile;
- scenario execution;
- PGF build;
- finite timeout containment where safely reproducible;
- raw stdout and stderr preservation.

Real-GF timeout tests should avoid corrupting developer projects.

---

## 122. Stress tests

Stress tests SHOULD cover:

- many sequential processes;
- bounded concurrent independent processes if concurrency is supported;
- repeated cancellation;
- repeated timeout;
- large output;
- child-process cleanup;
- handle leakage;
- run-directory cleanup after failures.

No stress test should use unbounded execution.

---

## 123. Property tests

Useful properties:

- timeout is always finite;
- result state is one canonical value;
- `timed_out` compatibility boolean agrees with state;
- launch failure has no exit code;
- timeout cannot yield `OK`;
- cancellation cannot yield `OK`;
- abnormal termination artifacts cannot be trusted;
- raw paths remain inside run root;
- output truncation is explicit;
- runner never kills unrelated fixture processes.

---

## 124. Observability checks

Diagnostic mode may record:

```text
process_runner_version
operation_id
pid
deadline
elapsed_ms
termination_attempts
stream_bytes
stream_truncation
capture_duration_ms
termination_duration_ms
```

These are derived execution diagnostics.

They must not expose secrets.

---

## 125. Automated checks

Recommended command:

```text
gf-wordbench process check
```

Strict mode:

```text
gf-wordbench process check --strict
```

The checker should verify:

1. every operation class has a positive timeout;
2. grace periods are finite;
3. output limits are configured;
4. normal GF requests use no shell;
5. capture paths remain under run root;
6. executable and working directory resolve;
7. cancellation uses the shared mechanism;
8. process-tree policy exists for the platform;
9. compatibility booleans agree with execution state;
10. timeout maps to `ERROR/TIMEOUT`;
11. cancellation is not a validation status;
12. required artifacts after abnormal termination are untrusted;
13. stdout and stderr are both captured;
14. cleanup waits are bounded;
15. report writers do not launch processes.

---

## 126. Drift indicators

Process-contract drift exists when:

- an operation has no timeout;
- one component hardcodes a conflicting timeout;
- continuous output extends the deadline;
- cancellation is reported as `FAIL`;
- cancellation becomes a validation enum value;
- timeout is reported as GF syntax failure;
- launch failure receives a fake exit code;
- only stdout is captured;
- only stderr is captured;
- process output is parsed before raw capture;
- a report launches GF;
- GUI launches GF directly;
- shell execution becomes implicit;
- command logging differs from executed arguments;
- the working directory depends on launcher state;
- a timeout leaves a child running without warning;
- process names are killed globally;
- stream draining can deadlock;
- output limits silently discard bytes;
- a timeout-produced PGF counts as release evidence;
- retry occurs silently;
- run finalization hashes open files;
- platform behavior changes public status meaning;
- cleanup deletes partial evidence;
- a termination failure is hidden;
- an executable absent from the ADR-0013 registry is launched;
- project text selects an executable or interpreter;
- a process result contains Portfolio registry or aggregation state.

Every drift indicator requires restoration or a coordinated contract change.

---

## 127. Change workflow

A process-execution change is complete only when all applicable checks pass.

```text
[ ] External contract identified
[ ] Request owner identified
[ ] Process runner reviewed
[ ] Executable behavior reviewed
[ ] Argument order reviewed
[ ] Working directory reviewed
[ ] Environment reviewed
[ ] Stdin reviewed
[ ] Stdout capture reviewed
[ ] Stderr capture reviewed
[ ] Timeout reviewed
[ ] Cancellation reviewed
[ ] Process-tree containment reviewed
[ ] Soft termination reviewed
[ ] Forced termination reviewed
[ ] Stream draining reviewed
[ ] Output limits reviewed
[ ] Artifact trust reviewed
[ ] Status mapping reviewed
[ ] Error-kind mapping reviewed
[ ] Windows behavior reviewed
[ ] POSIX behavior reviewed
[ ] Unit tests updated
[ ] Integration tests updated
[ ] Persisted schema impact reviewed
[ ] Documentation updated
[ ] External-tool lock updated
```

Change record template:

```text
Operation:
Current request:
New request:
Reason:
Timeout:
Grace period:
Cancellation:
Process tree:
Capture:
Output limits:
Artifacts:
Status mapping:
Platforms:
Compatibility:
Compatibility effects:
Tests:
```

---

## 128. Forbidden behavior

GF Wordbench MUST NOT:

```text
launch normal GF commands through an implicit shell
use an infinite timeout
hide timeout as compilation failure
hide cancellation as validation failure
invent an exit code for launch failure
ignore stderr
ignore stdout
stop draining a full pipe without containment
kill processes by executable name globally
trust artifacts from timed-out execution
trust artifacts from cancelled execution
silently retry a timeout
extend a deadline because output continues
discard partial evidence
finalize reports while streams are open
claim process-tree cleanup without confirmation
allow GUI and CLI to use different timeout semantics
use wall-clock time for deadline enforcement
permit unbounded post-termination waiting
launch an executable optional tool absent from the static registry
let project content choose an executable or interpreter
orchestrate several Wordbench workspaces through the private process runner
```

---

## 129. Related documents

### Architecture and contracts

- `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
- `docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/architecture/PROCESS_EXECUTION_MODEL.md`
- `docs/architecture/ERROR_HANDLING_MODEL.md`
- `docs/architecture/ARTIFACT_MODEL.md`

### GF operations

- `docs/gf/GF_TOOLCHAIN_INTEGRATION.md`
- `docs/gf/GF_COMPILATION.md`
- `docs/gf/GF_PGF_BUILD.md`
- `docs/gf/GF_SCRIPT_EXECUTION.md`
- `docs/gf/GF_VERSION_COMPATIBILITY.md`

### Diagnostics and validation

- `docs/diagnostics/DIAGNOSTIC_OVERVIEW.md`
- `docs/diagnostics/ERROR_CLASSIFICATION.md`
- `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md`
- `docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md`
- `docs/validation/VALIDATION_PIPELINE.md`
- `docs/validation/RELEASE_GATES.md`

### Reports and operations

- `docs/reports/RAW_LOGS_REFERENCE.md`
- `docs/reports/SUMMARY_JSON_REFERENCE.md`
- `docs/operations/RUN_DIRECTORY_LIFECYCLE.md`
- `docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md`
- `docs/operations/AUTOMATION_AND_CI.md`
- `docs/reference/STATUS_VALUES.md`
- `docs/reference/DIAGNOSTIC_KINDS.md`
- `docs/DOCUMENTATION_CORRECTION_LEDGER.md`

---

## 130. Core enforcement rule

External-process control is part of the validation result.

A command that did not launch, did not finish, was cancelled, exceeded its deadline or could not be terminated safely did not produce a normal GF validation outcome.

Therefore:

> No timeout, cancellation, termination, capture or process-tree behavior may change through an isolated code or documentation edit.

Every process-control change must update the request model, process runner, operation owners, result mapping, artifact trust, platform adapters, tests, contract locks and documentation as one coordinated change.
