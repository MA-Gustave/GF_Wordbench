# GF Wordbench — Exit Codes

**Document ID:** `GF-WB-REF-EXIT-CODES`  
**Status:** Normative CLI and automation reference  
**Applies to:** GF Wordbench CLI commands, automation wrappers, Windows launchers, CI jobs, migration commands, contract checks and release checks  
**Owner:** CLI entrypoint and shared application result model  
**Reference version:** `2.0`  
**Last reviewed:** `2026-07-24`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related references:** `docs/reference/STATUS_VALUES.md`, `docs/reference/DIAGNOSTIC_KINDS.md`, `docs/architecture/ERROR_HANDLING_MODEL.md`

---

## 1. Purpose

This document defines the process exit codes returned by GF Wordbench.

It establishes:

- canonical numeric values;
- the meaning of each value;
- mapping from command outcomes to exit codes;
- the distinction between validation failure and framework error;
- controlled cancellation semantics;
- usage and configuration error semantics;
- propagation through launchers and CI;
- reserved values;
- test obligations.

The exit code is a compact automation signal.

Detailed causes remain in terminal output, `summary.json`, logs and run artifacts.

---

## 2. Product boundary

Exit codes summarize one GF Wordbench command concerning one active project and one requested operation.

They do not represent:

- several Wordbench workspaces;
- multilingual portfolio aggregation;
- cross-project readiness;
- `gf-portfolio` execution state.

`gf-portfolio` may invoke GF Wordbench or consume public artifacts, but Wordbench exit-code semantics do not depend on Portfolio.

---

## 3. Core rule

> GF Wordbench returns an application exit code for the complete requested command; it does not forward a child GF process exit code.

Child process codes remain recorded in structured evidence such as:

```text
ProcessResult
CompileResult
ScenarioResult
summary.json
raw process evidence
```

The GF Wordbench code describes the command-level outcome.

---

## 4. Canonical table

| Code | Constant | Meaning |
|---:|---|---|
| `0` | `EXIT_OK` | Command completed and all required criteria passed |
| `1` | `EXIT_VALIDATION_FAILED` | Command completed, but one or more required criteria failed |
| `2` | `EXIT_USAGE_ERROR` | Invocation, arguments or pre-execution configuration were invalid |
| `3` | `EXIT_RUNTIME_ERROR` | GF Wordbench could not execute, complete, interpret or persist the requested operation safely |
| `4` | `EXIT_CANCELLED` | The command was deliberately cancelled before normal completion |

Only these values are allocated by this contract.

Canonical constants:

```python
EXIT_OK = 0
EXIT_VALIDATION_FAILED = 1
EXIT_USAGE_ERROR = 2
EXIT_RUNTIME_ERROR = 3
EXIT_CANCELLED = 4
```

Numeric values `0` through `3` remain compatible with the predecessor GF Audit command contract.

---

## 5. Exit code `0` — success

```text
EXIT_OK = 0
```

Meaning:

- the command executed successfully;
- every required criterion passed;
- no command-level framework error occurred;
- the command was not cancelled.

For a validation run:

```text
overall_status = OK
```

maps to `0`.

### Successful non-validation commands

Examples:

```text
gf-wordbench --help
gf-wordbench --version
gf-wordbench config show
gf-wordbench scenarios list
gf-wordbench contracts check
gf-wordbench migrate state
```

They return `0` when the requested action completes and its criteria pass.

A migration that determines no change is required may return `0`.

### Warnings

Warnings do not automatically change success.

A command may return `0` when:

- warnings are nonblocking;
- optional scenarios were not selected;
- a newer GF version is accepted by policy;
- heuristic scan findings are informational;
- optional artifacts are absent by contract.

### Skipped operations

An individual operation may be:

```text
validation_status = SKIPPED
```

while the command returns `0` only when the skip is allowed by the resolved command contract.

A required skipped operation prevents success.

---

## 6. Exit code `1` — required criteria failed

```text
EXIT_VALIDATION_FAILED = 1
```

Meaning:

- GF Wordbench completed the requested evaluation sufficiently;
- one or more required criteria were not satisfied;
- the outcome is a completed negative result, not an inability to evaluate.

For a validation run:

```text
overall_status = FAIL
```

maps to `1`.

Examples:

- GF compilation completed and reported a project error;
- a required module failed;
- a required scenario assertion failed;
- a required scenario section did not complete;
- normalized output differed from reviewed gold;
- a required release gate failed;
- a required PGF criterion failed after interpretable execution;
- a contract or schema check completed and found violations;
- a project check found missing required work.

Exit code `1` means the tool worked well enough to establish noncompliance.

It is not used for:

- malformed CLI invocation;
- missing required arguments;
- invalid project configuration before command construction;
- executable launch failure;
- timeout;
- unexpected application exception;
- required reporting failure;
- controlled cancellation.

### Release mode

A release command returns `1` when required evidence was evaluated and at least one release criterion failed.

Examples:

```text
required compile result = FAIL
required scenario result = FAIL
required gold comparison = mismatch
release gate = FAIL
required PGF criterion = FAIL
```

When a required gate cannot be evaluated safely, the result is `3`.

### Check commands

Compliance-oriented commands return `1` when evaluation completes and finds violations.

Examples:

```text
contracts check
schema check
paths check
project check
release check
```

Rule:

```text
check completed + criterion false = 1
```

---

## 7. Exit code `2` — usage or pre-execution configuration error

```text
EXIT_USAGE_ERROR = 2
```

Meaning:

- invocation is invalid;
- caller-supplied configuration is missing or malformed;
- a valid command request cannot be constructed.

Examples:

- unknown option;
- missing required option;
- invalid option combination;
- unsupported mode;
- required target omitted;
- invalid numeric argument;
- invalid caller-supplied regex;
- explicitly supplied project root is invalid;
- explicitly supplied GF executable path is invalid before execution;
- project configuration cannot be parsed;
- unsupported project schema;
- duplicate required scenario IDs;
- invalid output path;
- incompatible command selection.

### Explicit invalid values

When the caller explicitly supplies an invalid value, GF Wordbench does not silently fall back to:

- application state;
- environment variables;
- defaults;
- automatic discovery.

It reports the invalid value and returns `2`.

### Parser behavior

```text
help requested    → 0
version requested → 0
parse error       → 2
```

A non-integer parser termination value is normalized to `2`.

### Configuration boundary

Use `2` when configuration is rejected before the requested operation starts.

Use `3` when a valid resolved request starts but execution or required persistence fails.

Example:

```text
configured executable path invalid during bootstrap → 2
executable disappears before process launch         → 3
```

### Schema inputs

A command reading caller-selected configuration returns `2` when:

- schema identity is wrong;
- schema version is unsupported;
- a required field is missing;
- a field type is invalid;
- path semantics are invalid;
- an explicit migration is required but was not requested.

A migration command returns `3` when transformation or persistence begins and then fails.

---

## 8. Exit code `3` — runtime or framework error

```text
EXIT_RUNTIME_ERROR = 3
```

Meaning:

- GF Wordbench could not execute, complete, interpret or persist the requested operation safely;
- the problem is not merely a failed project criterion;
- required evidence may be incomplete.

For a validation run:

```text
overall_status = ERROR
```

maps to `3`.

Examples:

- GF executable launch failure;
- required external process timeout;
- output-limit termination;
- process-tree containment failure;
- raw stream capture failure;
- decoding failure that prevents required interpretation;
- required artifact cannot be verified safely;
- normalization failure;
- required report cannot be written;
- required manifest cannot be created or verified;
- unexpected internal exception;
- run-directory creation failure;
- migration write or verification failure;
- schema serialization failure;
- project data changes during execution and integrity cannot be established;
- unsupported external-tool behavior prevents safe interpretation.

### Failure versus error

Use `1` when the subject was evaluated and failed.

Use `3` when Wordbench could not reliably perform or interpret the evaluation.

| Condition | Code |
|---|---:|
| GF reports a source syntax error and evidence is captured | `1` |
| GF executable cannot start | `3` |
| Scenario gold differs from normalized output | `1` |
| Scenario normalization fails | `3` |
| Required artifact is absent after interpretable execution | `1` or `3` according to the artifact contract |
| Required manifest cannot be persisted | `3` |
| Required scenario exceeds its timeout | `3` |

### Required artifacts

A zero child-process exit does not guarantee Wordbench success.

When a required artifact is missing:

- the stage does not pass;
- the absence is recorded;
- the command returns `1` when an evaluated project criterion failed;
- the command returns `3` when the operation contract cannot be completed or interpreted safely.

The stage-specific artifact contract owns this distinction.

### Timeout

A required process timeout returns:

```text
3
```

It is not:

- a child sentinel forwarded by Wordbench;
- an ordinary source failure;
- controlled cancellation.

### Launch failure

A process that never starts has no child exit code to forward.

Wordbench returns `3` and records, when applicable:

```text
execution_state = launch_failed
exit_code = null
```

### Reporting failure

When a required report or integrity artifact cannot be produced, the command returns `3`.

A missing required `summary.json` or `manifest.json` is a runtime error even when language validation passed.

### Unexpected exceptions

Unhandled application exceptions are converted at the CLI boundary to:

```text
EXIT_RUNTIME_ERROR = 3
```

The CLI writes a concise error, preserves available evidence and avoids exposing secrets.

---

## 9. Exit code `4` — controlled cancellation

```text
EXIT_CANCELLED = 4
```

Meaning:

- the user, controller or application shutdown requested cancellation;
- the operation did not complete normally;
- cancellation is the accepted command-level cause;
- evidence preservation and process containment were attempted.

Canonical reasons include:

```text
user
application_shutdown
controller_policy
```

Output-limit termination is a runtime error, not cancellation.

### Keyboard interruption

The CLI catches `KeyboardInterrupt` and requests controlled cancellation.

When containment and evidence preservation succeed:

```text
4
```

When cancellation handling itself fails critically:

```text
3
```

### Cancellation versus validation failure

A cancelled command does not claim project success or failure.

It returns `4` even when earlier subjects failed, provided cancellation is the command-level outcome and no runtime failure prevents safe closure.

### Cancellation versus timeout

```text
user cancellation → 4
process timeout   → 3
```

A timeout must not be relabeled as cancellation.

### CI

CI treats `4` as unsuccessful, while retaining the distinction for operator reporting or retry policy.

---

## 10. Exit-code selection

The CLI selects one code for the complete command.

Conceptual mapping:

```python
def determine_exit_code(command_result: CommandResult) -> int:
    if command_result.overall_status == "ERROR":
        return EXIT_RUNTIME_ERROR
    if command_result.cancelled:
        return EXIT_CANCELLED
    if command_result.overall_status == "FAIL":
        return EXIT_VALIDATION_FAILED
    return EXIT_OK
```

Usage and configuration errors are handled before a valid `CommandResult` exists.

### Precedence

Before execution:

```text
invalid invocation or configuration → 2
```

After execution begins:

```text
runtime ERROR > controlled cancellation > validation FAIL > OK
```

Mapping:

| Command outcome | Exit code |
|---|---:|
| `OK` | `0` |
| `FAIL` | `1` |
| `ERROR` | `3` |
| Controlled cancellation | `4` |

There is no run-level mapping to `2`; `2` means a valid run was not constructed.

---

## 11. Individual results do not map directly

An individual:

```text
FileResult
ScenarioResult
ProcessResult
ReleaseGateResult
```

does not determine the process exit code by itself.

The application aggregates the complete command outcome.

Examples:

- an optional scenario failure may remain nonblocking;
- a downstream skipped result may follow an earlier required failure;
- a non-zero child exit may be expected by a negative scenario;
- a warning may remain nonblocking.

---

## 12. No child-code forwarding

If GF returns:

```text
1
2
42
-9
```

GF Wordbench records that value and independently returns one of:

```text
0
1
2
3
4
```

This keeps automation stable across GF versions and operating systems.

### Expected negative scenarios

A scenario may intentionally expect a non-zero GF process result.

When the expected condition is proven:

```text
scenario status = OK
command exit code = 0
```

The child code remains recorded as evidence.

---

## 13. Standard streams

CLI convention:

```text
normal result summary → stdout
warnings              → stderr or documented warning channel
usage error           → stderr
runtime error         → stderr
```

Machine-readable evidence remains in generated artifacts.

Scripts must not parse human stderr to infer the exit code.

For non-zero outcomes, the CLI should identify:

- error category;
- failed command;
- run directory when created;
- summary path when available;
- primary remediation;
- cancellation state.

Secrets must not appear.

Quiet or machine-output modes may change terminal formatting, but not exit-code meaning.

---

## 14. Command classes

The same five codes apply to all command classes.

### Informational commands

Examples:

```text
--help
--version
config show
scenarios list
```

Mapping:

- completed → `0`;
- invalid invocation → `2`;
- runtime failure → `3`;
- cancelled where applicable → `4`.

Informational commands do not normally return `1`.

### Action commands

Examples:

```text
project init
gold update
cleanup
export
```

Mapping:

- success → `0`;
- completed negative acceptance result → `1`;
- invalid request → `2`;
- unsafe or incomplete execution → `3`;
- cancelled → `4`.

Destructive actions must not partially succeed silently.

### Validation commands

Examples:

```text
validate
run
quick
checkpoint
diagnostic
release
```

Mapping:

- all required criteria pass → `0`;
- completed required failure → `1`;
- invalid request → `2`;
- framework or execution error → `3`;
- controlled cancellation → `4`.

### Check commands

Examples:

```text
contracts check
schema check
paths check
project check
release check
```

Mapping:

- compliant → `0`;
- noncompliant → `1`;
- invalid request → `2`;
- unable to complete → `3`;
- cancelled → `4`.

### Migration commands

Examples:

```text
migrate project
migrate state
migrate run
```

Mapping:

- success or no-op → `0`;
- completed negative criterion explicitly defined by the command → `1`;
- invalid source or arguments → `2`;
- read, transform, write, verification or rollback failure → `3`;
- cancelled → `4`.

### Release checks

A release check returns:

- `0` when all required gates pass;
- `1` when gates are evaluated and at least one fails;
- `2` when inputs are invalid;
- `3` when a gate cannot be evaluated or evidence cannot be persisted;
- `4` when cancelled.

---

## 15. Shell examples

### POSIX shell

```sh
gf-wordbench validate --mode release
code=$?

case "$code" in
  0) echo "Release validation passed" ;;
  1) echo "Release criteria failed" ;;
  2) echo "Invalid invocation or configuration" ;;
  3) echo "GF Wordbench runtime error" ;;
  4) echo "Validation cancelled" ;;
  *) echo "Unknown GF Wordbench exit code: $code" ;;
esac
```

### PowerShell

```powershell
gf-wordbench validate --mode release
$code = $LASTEXITCODE

switch ($code) {
    0 { Write-Host "Release validation passed" }
    1 { Write-Error "Release criteria failed" }
    2 { Write-Error "Invalid invocation or configuration" }
    3 { Write-Error "GF Wordbench runtime error" }
    4 { Write-Warning "Validation cancelled" }
    default { Write-Error "Unknown GF Wordbench exit code: $code" }
}

exit $code
```

### Windows batch

```bat
@echo off
gf-wordbench validate --mode release
set "GF_WORDBENCH_EXIT=%ERRORLEVEL%"

if "%GF_WORDBENCH_EXIT%"=="0" echo Release validation passed
if "%GF_WORDBENCH_EXIT%"=="1" echo Release criteria failed 1>&2
if "%GF_WORDBENCH_EXIT%"=="2" echo Invalid invocation or configuration 1>&2
if "%GF_WORDBENCH_EXIT%"=="3" echo GF Wordbench runtime error 1>&2
if "%GF_WORDBENCH_EXIT%"=="4" echo Validation cancelled 1>&2

exit /b %GF_WORDBENCH_EXIT%
```

Launchers preserve the exact application code.

---

## 16. Launcher contract

Launchers must:

- invoke the intended entrypoint;
- preserve argument boundaries;
- return the exact GF Wordbench code;
- avoid replacing every non-zero code with `1`;
- avoid returning a child GF code;
- avoid returning `0` after application failure;
- avoid hidden validation behavior.

Python module termination:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

`main()` returns an integer in the canonical range.

Installed console scripts and wrappers propagate it unchanged.

---

## 17. CI policy

Most CI systems treat every non-zero code as failure. That is correct for validation jobs.

Recommended classification:

| Code | CI meaning |
|---:|---|
| `0` | passed |
| `1` | validation or check failed |
| `2` | job invocation or configuration error |
| `3` | infrastructure or framework error |
| `4` | cancelled or interrupted |

### Retry policy

- `1`: do not retry automatically;
- `2`: do not retry without changing inputs;
- `3`: retry only when policy identifies a transient cause;
- `4`: retry only when cancellation policy permits it.

A retry must not overwrite prior run evidence.

### Artifact retention

For codes `1`, `3` and `4`, retain available:

```text
summary.json
summary.md
AI_READY.md
manifest.json
master.log
raw stdout and stderr
gold diffs
```

For code `2`, a run directory may not exist.

### False-success prevention

Do not use:

```text
gf-wordbench validate || true
```

unless the script captures and enforces the original code separately.

---

## 18. GUI process exit

The GUI is not the automation interface.

Typical GUI process behavior:

- normal close → `0`;
- invalid startup arguments → `2`;
- fatal startup or framework error → `3`.

A validation cancelled inside a running GUI is represented in the run result and does not necessarily terminate the GUI process.

Automation uses the CLI.

---

## 19. Relationship to internal result dimensions

Exit codes remain distinct from:

```text
validation_status
execution_state
error_kind
diagnostic_class
change_kind
release-gate status
```

### Validation statuses

```text
OK
FAIL
ERROR
SKIPPED
```

### Execution states

```text
completed
timed_out
cancelled
launch_failed
```

### Diagnostic classes

```text
ok
direct
downstream
ambiguous
noise
skipped
```

No individual status, state, kind or class is itself a process exit code.

Aggregation determines the command result.

---

## 20. Reserved and unknown values

Values:

```text
5 through 63
```

are reserved for GF Wordbench.

They must not be assigned by individual commands without a contract revision.

Values:

```text
64 through 125
```

are unallocated by this reference.

GF Wordbench uses values within:

```text
0 through 255
```

for cross-platform portability.

### Signal-style termination

POSIX shells may expose external termination as:

```text
128 + signal number
```

When the operating system terminates Wordbench before it can return normally, automation may observe a noncanonical value.

### Unknown values

A wrapper receiving a value outside `0` through `4` must:

- preserve it;
- avoid labeling it as a known Wordbench outcome;
- report unknown or external termination;
- retain available evidence.

It must not rewrite an unknown observed value to `3` after the process has ended.

---

## 21. Public constants

One shared source owns the constants.

Canonical definitions:

```python
EXIT_OK = 0
EXIT_VALIDATION_FAILED = 1
EXIT_USAGE_ERROR = 2
EXIT_RUNTIME_ERROR = 3
EXIT_CANCELLED = 4
```

A typed enum may wrap them:

```python
from enum import IntEnum

class ExitCode(IntEnum):
    OK = 0
    VALIDATION_FAILED = 1
    USAGE_ERROR = 2
    RUNTIME_ERROR = 3
    CANCELLED = 4
```

Public numeric values remain unchanged, and `main()` returns an `int`.

Launchers may compare numeric values but must not become an independent owner.

---

## 22. Compatibility

Legacy source aliases may be accepted by isolated compatibility code:

```python
EXIT_AUDIT_FAILURES = EXIT_VALIDATION_FAILED
EXIT_INVALID_ARGS = EXIT_USAGE_ERROR
```

Canonical documentation, public APIs and new code use the Wordbench names.

Aliases do not define different behavior.

Changing an allocated numeric value is a breaking CLI contract and requires:

- application version review;
- CLI reference update;
- contract-lock update;
- launcher and CI update;
- compatibility strategy;
- tests;
- changelog entry.

Adding a reserved code also requires explicit compatibility review because automation may inspect exact values.

Human message wording may evolve without changing exit-code semantics.

---

## 23. Test obligations

### Constant tests

```python
assert EXIT_OK == 0
assert EXIT_VALIDATION_FAILED == 1
assert EXIT_USAGE_ERROR == 2
assert EXIT_RUNTIME_ERROR == 3
assert EXIT_CANCELLED == 4
```

### Result mapping

Test:

- `OK` → `0`;
- `FAIL` → `1`;
- `ERROR` → `3`;
- controlled cancellation → `4`;
- runtime error outranks prior validation failure;
- cancellation-handling error → `3`;
- optional skip with successful command → `0`;
- required skip → non-zero according to cause.

### Parser and CLI boundary

Test:

- help → `0`;
- version → `0`;
- unknown option → `2`;
- missing required option → `2`;
- invalid choice → `2`;
- non-integer parser exit normalization → `2`;
- unexpected exception → `3`;
- successful `KeyboardInterrupt` containment → `4`.

### Validation cases

Test:

- compilation failure → `1`;
- gold mismatch → `1`;
- required scenario assertion failure → `1`;
- release gate failure → `1`;
- launch failure → `3`;
- timeout → `3`;
- normalization failure → `3`;
- required report failure → `3`;
- manifest verification failure → `3`.

### Child-code isolation

Use fake child processes returning:

```text
0
1
2
42
```

Verify that Wordbench determines its own code from the command contract.

### Expected negative scenario

Verify:

- expected child failure is proven;
- scenario status is `OK`;
- command returns `0`;
- child code remains recorded.

### Launcher propagation

Verify launchers propagate `0`, `1`, `2`, `3` and `4` without collapsing or masking them.

---

## 24. Drift indicators

Exit-code drift exists when:

- the CLI returns a child GF code directly;
- `fail_count` alone decides the command result after `ERROR` exists;
- timeout returns `1`;
- cancellation returns `0`;
- invalid arguments return `3`;
- required report failure is hidden behind `1`;
- CLI and launcher return different values;
- a batch launcher omits `exit /b`;
- help returns non-zero;
- strict check violations return `0`;
- an expected negative scenario returns the child code;
- constants are duplicated with different values;
- a numeric value changes without contract review;
- GUI behavior is treated as the automation contract;
- external termination is labeled as controlled cancellation;
- CI suppresses a non-zero result;
- Wordbench exit behavior depends on `gf-portfolio`.

Any drift indicator requires coordinated correction.

---

## 25. Compliance checklist

```text
[ ] canonical values are 0, 1, 2, 3 and 4
[ ] success maps to 0
[ ] completed required failure maps to 1
[ ] invalid invocation or pre-execution configuration maps to 2
[ ] runtime or framework error maps to 3
[ ] controlled cancellation maps to 4
[ ] child codes are recorded but not forwarded
[ ] help and version return 0
[ ] parser errors return 2
[ ] timeout returns 3
[ ] launch failure returns 3
[ ] gold mismatch returns 1
[ ] required report failure returns 3
[ ] cancellation remains distinct from timeout
[ ] launchers propagate the exact code
[ ] complete command outcome drives the result
[ ] reserved values are not assigned ad hoc
[ ] every allocated code has tests
[ ] CI examples preserve the code
[ ] Wordbench remains independent from gf-portfolio
```

---

## 26. Invariants

1. GF Wordbench owns the application exit code.
2. Child GF exit codes are never forwarded automatically.
3. `0` means the requested command passed its required criteria.
4. `1` means completed evaluation found required failures.
5. `2` means invocation or pre-execution configuration was invalid.
6. `3` means Wordbench could not complete or interpret the operation safely.
7. `4` means controlled cancellation.
8. Timeout is `3`.
9. Launch failure is `3`.
10. Gold mismatch is normally `1`.
11. Required report or manifest failure is `3`.
12. Help and version return `0`.
13. Individual results do not map directly without aggregation.
14. `SKIPPED` has no independent process code.
15. Warnings do not automatically change success.
16. Expected negative scenarios may produce command success.
17. Launchers preserve the application code.
18. CI treats non-zero as unsuccessful unless it has an explicit classification policy.
19. Numeric values `0` through `3` remain compatible with predecessor automation.
20. Numeric changes require contract review.
21. Exit-code semantics do not depend on `gf-portfolio`.

---

## 27. Enforcement

GF Wordbench exit codes answer:

> What happened to the complete command requested from GF Wordbench?

Decision chain:

```text
invalid request before execution
    → 2

valid request
    → runtime or framework error
        → 3
    → controlled cancellation
        → 4
    → completed required-criterion failure
        → 1
    → complete success
        → 0
```

Detailed causes remain in structured results and artifacts.

Automation uses the exit code for the command-level outcome and `summary.json` for the complete explanation.
