# GF Wordbench — Exit Codes

**Document ID:** `GF-WB-REF-EXIT-CODES`  
**Status:** Normative CLI and automation reference  
**Applies to:** GF Wordbench CLI commands, automation wrappers, Windows launchers, CI jobs, migration commands, contract checks, and release checks  
**Primary implementation owner:** `app/main_cli.py`  
**Shared semantic owner:** application result and error model  
**Reference version:** `1.0`  
**Target product state:** Final architecture  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines the process exit codes returned by GF Wordbench.

It establishes:

- the canonical numeric values;
- the meaning of each value;
- how CLI outcomes map to exit codes;
- how validation failure differs from framework error;
- how cancellation is represented;
- how argument and configuration errors are represented;
- how command-specific checks use the same codes;
- how launchers and CI must propagate the result;
- how legacy GF Audit constants migrate;
- which values are reserved;
- which tests lock the contract.

The exit code is a compact automation signal.

Detailed evidence remains in terminal output and generated run artifacts.

---

## 2. Core rule

> GF Wordbench returns its own application exit code; it does not forward a child GF process exit code as the CLI result.

GF process return codes remain recorded in:

```text
ProcessResult
CompileSummary
ScenarioResult
summary.json
raw process evidence
```

The GF Wordbench exit code describes the outcome of the complete requested command.

---

## 3. Canonical table

| Code | Canonical constant | Meaning |
|---:|---|---|
| `0` | `EXIT_OK` | Command completed and its required criteria passed |
| `1` | `EXIT_VALIDATION_FAILED` | Command completed, but one or more required criteria failed |
| `2` | `EXIT_USAGE_ERROR` | Invocation, arguments, or pre-execution configuration were invalid |
| `3` | `EXIT_RUNTIME_ERROR` | GF Wordbench could not execute, complete, interpret, or persist the requested operation safely |
| `4` | `EXIT_CANCELLED` | The command was cancelled deliberately before normal completion |

Only these values are allocated in exit-code contract version `1.0`.

---

## 4. Compatibility aliases

The inherited GF Audit CLI uses:

```python
EXIT_OK = 0
EXIT_AUDIT_FAILURES = 1
EXIT_INVALID_ARGS = 2
EXIT_RUNTIME_ERROR = 3
```

GF Wordbench retains numeric compatibility.

Canonical GF Wordbench names are:

```python
EXIT_OK = 0
EXIT_VALIDATION_FAILED = 1
EXIT_USAGE_ERROR = 2
EXIT_RUNTIME_ERROR = 3
EXIT_CANCELLED = 4
```

Temporary source-level aliases may be retained during migration:

```python
EXIT_AUDIT_FAILURES = EXIT_VALIDATION_FAILED
EXIT_INVALID_ARGS = EXIT_USAGE_ERROR
```

Canonical documentation and new code must use the GF Wordbench names.

Aliases must not create different numeric behavior.

---

## 5. Exit code `0` — success

```text
EXIT_OK = 0
```

Meaning:

- the command executed successfully;
- every criterion required by that command passed;
- no terminal framework error occurred;
- the command was not cancelled.

For a validation run:

```text
overall_status = OK
```

normally maps to `0`.

---

## 6. Successful non-validation commands

Exit code `0` also applies when a non-validation command succeeds.

Examples:

```text
gf-wordbench --help
gf-wordbench --version
gf-wordbench config show
gf-wordbench scenarios list
gf-wordbench contracts check
gf-wordbench migrate state
```

provided the requested action completes and its required criteria pass.

A migration that determines that no change is required may return `0`.

---

## 7. Warnings with success

Warnings do not automatically change exit code `0`.

A command may return `0` when:

- validation passed;
- warnings are explicitly nonblocking;
- optional scenarios were not selected;
- an unknown newer GF version is allowed by non-strict policy;
- heuristic scan findings are informational under the selected mode.

A warning becomes exit code `1`, `2`, or `3` only when the applicable policy makes it a failed criterion, invalid request, or execution error.

---

## 8. `SKIPPED` with success

An individual operation may have:

```text
validation_status = SKIPPED
```

while the command returns `0` only when the skipped operation was optional under the resolved command contract.

A required skipped operation prevents success.

Its final command outcome is classified by cause:

- required criterion not met → `1`;
- criterion could not be evaluated safely → `3`;
- user cancelled the command → `4`.

---

## 9. Exit code `1` — required criteria failed

```text
EXIT_VALIDATION_FAILED = 1
```

Meaning:

- GF Wordbench executed the requested evaluation sufficiently;
- one or more required criteria were not satisfied;
- the result is a completed negative outcome, not a framework inability.

For a validation run:

```text
overall_status = FAIL
```

maps to `1`.

---

## 10. Examples of exit code `1`

Examples include:

- GF source compilation completed and reported a project error;
- a required module failed validation;
- a required scenario assertion failed;
- a required scenario section did not complete after an otherwise interpretable run;
- normalized output differed from reviewed gold;
- a required release gate failed;
- a required PGF criterion failed after execution completed;
- a contract-check command completed and found contract violations;
- a strict policy check completed and found noncompliance;
- a project-completion check found missing required project work.

The command still produces evidence when the reporting contract can be completed.

---

## 11. Validation failure is not application crash

Exit code `1` means the tool worked well enough to report that the subject did not pass.

It must not be used for:

- malformed CLI invocation;
- missing required command argument;
- unreadable project configuration before a run can be constructed;
- GF executable launch failure;
- process timeout;
- application exception;
- report persistence failure that prevents required evidence;
- user cancellation.

Those conditions map to another code.

---

## 12. Release mode and exit code `1`

A release-mode run returns `1` when release evidence was evaluated and at least one release criterion failed.

Examples:

```text
required compile result = FAIL
required scenario result = FAIL
required gold comparison = mismatch
release gate = FAIL
required PGF semantic criterion = FAIL
```

A release-mode run returns `3` instead when GF Wordbench could not evaluate a required gate safely.

---

## 13. Check commands and exit code `1`

Commands whose purpose is to evaluate compliance use `1` when the evaluation completes and finds violations.

Examples:

```text
contracts check
paths check
project check
release check
schema validate
```

Generic semantic rule:

```text
check completed + criterion false = 1
```

This makes these commands useful in CI.

---

## 14. Exit code `2` — usage or pre-execution configuration error

```text
EXIT_USAGE_ERROR = 2
```

Meaning:

- the invocation is invalid;
- required caller-supplied configuration is absent or malformed;
- GF Wordbench cannot construct a valid request from the supplied inputs.

This code is compatible with the conventional `argparse` parse-error code.

---

## 15. Examples of exit code `2`

Examples:

- unknown CLI option;
- missing required option;
- invalid option combination;
- unsupported mode name;
- target file required by `quick` mode but not supplied;
- invalid numeric argument;
- invalid regular expression supplied by the user;
- explicitly supplied project root is not a project;
- explicitly supplied GF executable path is invalid before execution;
- project configuration cannot be parsed or validated before run creation;
- unsupported project schema major;
- duplicate required scenario ID in project configuration;
- invalid migration-command syntax;
- invalid output path supplied explicitly;
- incompatible explicit command selection.

---

## 16. Explicit invalid value rule

When the user explicitly supplies an invalid value, GF Wordbench must not silently fall back to:

- application state;
- environment variables;
- defaults;
- automatic discovery.

The command reports the invalid value and returns `2`.

---

## 17. Parser behavior

The argument parser may raise `SystemExit`.

Canonical behavior:

```text
help requested       → 0
version requested    → 0
parse error          → 2
```

GF Wordbench must preserve valid `argparse` integer codes where they match this contract.

A non-integer parser exit value is normalized to `2`.

---

## 18. Configuration error boundary

Use `2` when configuration is rejected before the requested operation starts.

Use `3` when a valid resolved request begins but execution or required persistence fails.

Example:

```text
configured GF path does not exist during bootstrap → 2
GF executable disappears between validation and launch → 3
```

---

## 19. Schema errors and exit code `2`

A command reading a user-selected configuration input returns `2` when:

- schema identity is wrong;
- schema version is unsupported;
- required field is missing;
- field type is invalid;
- path semantics are invalid;
- migration is required but not requested.

A migration command may return `3` when migration begins but fails to write or verify its target safely.

---

## 20. Exit code `3` — runtime or framework error

```text
EXIT_RUNTIME_ERROR = 3
```

Meaning:

- GF Wordbench could not execute, complete, interpret, or persist the requested operation safely;
- the problem is not merely a failed language criterion;
- required evidence may be incomplete.

For a finalized validation run:

```text
overall_status = ERROR
```

maps to `3`.

---

## 21. Examples of exit code `3`

Examples:

- GF executable launch failure;
- required external process timeout;
- output-limit termination;
- process-tree containment failure;
- raw stream capture failure;
- output decoding failure that prevents required interpretation;
- required artifact could not be observed safely;
- normalization failed;
- required report could not be written;
- required manifest could not be created or verified;
- unexpected internal exception;
- filesystem permission failure during run creation;
- migration target write failed;
- canonical schema serialization failed;
- required project data changed during execution and integrity cannot be established;
- unsupported external-tool behavior prevents safe interpretation.

---

## 22. Runtime error versus validation failure

Use `1` when the subject was evaluated and failed.

Use `3` when GF Wordbench could not reliably perform or interpret the evaluation.

Examples:

| Condition | Code |
|---|---:|
| GF reports a source syntax error and evidence is captured | `1` |
| GF executable cannot start | `3` |
| Scenario gold differs from actual normalized output | `1` |
| Scenario normalization crashes | `3` |
| Required PGF is absent after completed interpretable build | `1` or `3` according to the stage’s artifact contract |
| Manifest writer cannot persist required integrity evidence | `3` |
| Required scenario exceeds its timeout | `3` |

The stage and error-handling model define ambiguous artifact cases consistently.

---

## 23. Required artifact rule

A zero child-process exit code does not guarantee GF Wordbench success.

If a required artifact is missing:

- the stage does not pass;
- the missing artifact is recorded;
- the command returns `1` when this is an evaluated project criterion;
- the command returns `3` when the absence means the operation contract could not be completed or interpreted safely.

The operation-specific contract defines the distinction.

---

## 24. Timeout rule

A required process timeout is a runtime error.

Canonical command result:

```text
3
```

A timeout must not be represented as:

- a forwarded child-process sentinel;
- ordinary GF syntax failure;
- exit code `1` solely because the validation did not pass;
- exit code `4` unless a separate cancellation request was the first terminal cause.

---

## 25. Launch failure rule

A process that never starts has no tool exit code to forward.

GF Wordbench returns:

```text
3
```

and records:

```text
execution_state = launch_failed
exit_code = null
```

in structured evidence where applicable.

---

## 26. Reporting failure rule

A report failure is separate from a GF validation result.

If a required report or integrity artifact cannot be produced:

```text
3
```

even when language validation itself passed.

If validation already failed and an optional report also failed, the overall error-handling model determines whether the final command remains `1` or escalates to `3`.

A missing required machine summary or manifest normally escalates to `3`.

---

## 27. Unexpected exception

An uncaught application exception is converted at the CLI boundary to:

```text
EXIT_RUNTIME_ERROR = 3
```

The CLI should:

- write a concise error to stderr;
- preserve available run evidence;
- avoid printing secrets;
- return `3`.

Debug tracebacks may be enabled through explicit diagnostic policy.

---

## 28. Exit code `4` — controlled cancellation

```text
EXIT_CANCELLED = 4
```

Meaning:

- the user, controller, or application shutdown requested cancellation;
- the operation did not complete normally;
- cancellation was the accepted terminal cause;
- process containment and evidence finalization were attempted.

---

## 29. Cancellation sources

Canonical cancellation reasons include:

```text
user
application_shutdown
controller_policy
```

Output-limit termination is not user cancellation and normally returns `3`.

---

## 30. Keyboard interruption

The CLI should catch:

```text
KeyboardInterrupt
```

and request controlled cancellation.

When containment and finalization succeed, return:

```text
4
```

If cancellation handling itself fails critically, return:

```text
3
```

---

## 31. Cancellation versus validation failure

A cancelled command does not claim that the project passed or failed.

It returns `4` even if some earlier subjects had already failed, provided cancellation is the final run-level outcome and no more severe framework failure prevents safe finalization.

Partial results remain available.

---

## 32. Cancellation versus timeout

```text
user cancellation → 4
process deadline   → 3
```

The first accepted terminal cause wins.

A timeout must not be relabeled as user cancellation.

---

## 33. Cancellation and CI

CI should normally treat `4` as an unsuccessful job.

It may distinguish cancellation from product failure for retry or operator reporting.

An automation system must not treat `4` as a successful validation.

---

# 34. Exit-code selection

The CLI selects one final code for the complete command.

Recommended conceptual function:

```python
def determine_exit_code(command_result: CommandResult) -> int:
    if command_result.cancelled:
        return EXIT_CANCELLED
    if command_result.overall_status == "ERROR":
        return EXIT_RUNTIME_ERROR
    if command_result.overall_status == "FAIL":
        return EXIT_VALIDATION_FAILED
    return EXIT_OK
```

Usage/configuration errors are handled before a valid `CommandResult` exists.

---

## 35. Precedence

When several conditions exist, apply this precedence:

```text
1. invalid invocation before execution              → 2
2. cancellation-handling failure or runtime error   → 3
3. controlled cancellation                          → 4
4. completed required-criterion failure             → 1
5. complete success                                 → 0
```

This list is evaluated by lifecycle phase.

An invalid invocation does not coexist with a started run.

Within a started run:

```text
runtime ERROR > controlled cancellation > validation FAIL > OK
```

---

## 36. Finalized run mapping

| Run-level outcome | Exit code |
|---|---:|
| `OK` | `0` |
| `FAIL` | `1` |
| `ERROR` | `3` |
| Controlled cancelled run | `4` |

There is no run-level mapping to `2`.

Code `2` means that a valid run could not be constructed from the request.

---

## 37. Individual status does not map directly

An individual:

```text
FileResult
ScenarioResult
ProcessResult
ReleaseGateResult
```

does not independently determine the process exit code.

The orchestrator aggregates the complete command result.

Examples:

- optional scenario `FAIL` may or may not fail the run according to policy;
- a downstream `SKIPPED` result may be caused by a prior required failure;
- one process non-zero code may be expected in a negative scenario;
- a warning may remain nonblocking.

---

## 38. No child-code forwarding

Suppose GF returns:

```text
1
2
42
-9
```

GF Wordbench does not return that number automatically.

It records the child code and determines one application code:

```text
0
1
2
3
4
```

This provides stable automation behavior across GF versions and platforms.

---

## 39. Negative test scenarios

A scenario may intentionally expect a GF error.

If the expected condition is proven, the scenario may be `OK` and the CLI may return `0`.

The child GF process may have returned non-zero.

This is another reason child codes cannot be forwarded.

---

# 40. Standard streams

General CLI convention:

```text
normal result summary → stdout
warnings              → stderr or documented warning channel
usage error           → stderr
runtime error         → stderr
```

Machine-readable run evidence remains in generated artifacts.

A script must not parse human stderr to determine the exit code.

---

## 41. Error message requirement

For nonzero exit, the CLI should provide a concise message or result summary.

It should identify, when applicable:

- error category;
- failed command;
- run directory;
- summary path;
- primary remediation;
- cancellation state.

It must not expose secrets.

---

## 42. Quiet mode

A quiet mode may suppress ordinary terminal output.

It must not change the exit code.

Errors may still be written to stderr unless an explicit machine-only output policy applies.

---

## 43. JSON terminal output

A future `--output json` or equivalent mode may change terminal formatting.

It must not change exit-code meaning.

The persisted `summary.json` remains governed by its own schema.

---

# 44. Command classes

The same five codes apply to all CLI command classes.

```text
informational
action
validation
check
migration
release
```

---

## 45. Informational commands

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

---

## 46. Action commands

Examples:

```text
project init
gold update
cleanup
export
```

Mapping:

- completed successfully → `0`;
- requested action completed but explicit acceptance criterion failed → `1`;
- invalid request → `2`;
- action could not be performed safely → `3`;
- cancelled → `4`.

Destructive actions must not partially succeed silently.

---

## 47. Validation commands

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
- completed validation failure → `1`;
- invalid request/configuration → `2`;
- framework/execution error → `3`;
- controlled cancellation → `4`.

---

## 48. Check commands

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
- check unable to complete → `3`;
- cancelled → `4`.

---

## 49. Migration commands

Examples:

```text
migrate project
migrate state
migrate run
```

Mapping:

- migration successful or no-op → `0`;
- source is valid but does not satisfy an explicit migration acceptance criterion → `1` only when the command defines such a completed negative result;
- source/arguments invalid before migration → `2`;
- read, transform, write, verification, or rollback failure → `3`;
- cancelled → `4`.

Migration-specific documentation must identify any use of `1`.

The default migration failure code is `3`.

---

## 50. Release checks

A release-check command returns:

- `0` when every required gate passes;
- `1` when gates are evaluated and one or more fail;
- `2` when release inputs are invalid;
- `3` when a required gate cannot be evaluated or evidence cannot be persisted;
- `4` when cancelled.

---

# 51. Shell usage

## POSIX shell

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

---

## 52. PowerShell

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

---

## 53. Windows batch

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

Launchers must preserve the application code.

---

# 54. Launcher contract

Canonical launchers must:

- invoke the intended Python entrypoint;
- preserve argument boundaries;
- return the exact GF Wordbench exit code;
- avoid replacing every nonzero code with `1`;
- avoid returning the child GF code;
- avoid returning `0` after an application failure;
- avoid adding hidden validation behavior.

---

## 55. Python entrypoint

Canonical module termination:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

`main()` returns the canonical integer code.

It should not call `os._exit()` during normal operation.

---

## 56. Console script

The installed console script must propagate the integer returned by the CLI entrypoint.

Package wrappers must not swallow it.

---

# 57. CI policy

Most CI systems treat any nonzero value as failure.

That default is correct for validation jobs.

CI may use the exact code to classify failure.

Recommended labels:

| Code | CI classification |
|---:|---|
| `0` | passed |
| `1` | validation/check failed |
| `2` | job configuration error |
| `3` | infrastructure/framework error |
| `4` | cancelled/interrupted |

---

## 58. Retry policy

Automatic retry should not be based only on a nonzero code.

Recommended:

- `1`: do not retry automatically;
- `2`: do not retry without changing invocation/configuration;
- `3`: retry only when policy identifies a transient cause;
- `4`: retry only when the cancellation reason permits it.

A repeated retry must not overwrite prior run evidence.

---

## 59. CI artifact retention

For exit codes `1`, `3`, and `4`, retain available:

```text
summary.json
summary.md
AI_READY.md
manifest.json
master.log
raw stdout/stderr
gold diff
```

For code `2`, a run directory may not exist.

Retain configuration diagnostics or parser output where available.

---

## 60. CI gate example

A CI job that expects validation success should use normal shell behavior.

It should not write:

```text
gf-wordbench validate || true
```

unless it later inspects and enforces the exact captured code.

Suppressing the code without enforcement creates false success.

---

# 61. GUI process exit

The GUI application process is not the normal automation interface.

Recommended GUI process behavior:

- normal user close → `0`;
- fatal startup/framework error → `3`;
- invalid startup arguments → `2`.

A validation run cancelled inside a still-running GUI does not immediately determine the GUI process exit code.

The GUI displays the run result separately.

Automation should use the CLI.

---

# 62. Internal statuses

Exit codes must remain distinct from:

```text
validation_status
execution_state
error_kind
diagnostic_class
change_kind
release-gate status
```

Exit code is the final process-level summary of one command.

---

## 63. Validation statuses

Canonical:

```text
OK
FAIL
ERROR
SKIPPED
```

Mapping occurs only after aggregation.

---

## 64. Execution states

Canonical:

```text
completed
timed_out
cancelled
launch_failed
```

Typical final mapping:

- timed out → `3`;
- launch failed → `3`;
- controlled run cancellation → `4`;
- completed → evaluate validation status.

---

## 65. Error kinds

Examples:

```text
TYPE
SYNTAX
INTERNAL
TIMEOUT
CONFIG
IO
TOOL
ARTIFACT
NORMALIZATION
GOLD
```

No individual error kind is itself an exit code.

The complete result determines the code.

---

## 66. Diagnostic classes

Canonical:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

These express causality.

They do not map numerically to process exit codes.

---

# 67. Reserved values

Values:

```text
5 through 63
```

are reserved for future GF Wordbench use.

They must not be assigned ad hoc by individual commands.

Values:

```text
64 through 125
```

are unallocated by GF Wordbench version `1.0`.

They should not be used without a contract revision.

---

## 68. Signal-style values

POSIX shells may expose signal termination through values such as:

```text
128 + signal number
```

GF Wordbench attempts to convert a handled keyboard interruption into `4`.

An externally forced process termination may prevent the application from returning any canonical code.

Automation must recognize that such a value may come from the operating system or shell, not GF Wordbench.

---

## 69. Windows range

Windows supports wider process exit values than POSIX shells.

GF Wordbench intentionally stays within:

```text
0 through 255
```

for cross-platform portability.

---

## 70. Unknown code handling

A wrapper receiving a value outside `0`–`4` must:

- preserve the actual value;
- avoid mislabeling it as a known GF Wordbench outcome;
- report it as unknown or externally terminated;
- retain available evidence.

It must not normalize every unknown value to `3` after the process has already ended.

---

# 71. Public constants

Recommended final owner:

```text
app/main_cli.py
```

or a small shared CLI-status module when both entrypoints require it.

Canonical constants:

```python
EXIT_OK = 0
EXIT_VALIDATION_FAILED = 1
EXIT_USAGE_ERROR = 2
EXIT_RUNTIME_ERROR = 3
EXIT_CANCELLED = 4
```

Constants must not be duplicated across launchers, CLI modules, and tests without one authoritative source.

Shell launchers may use numeric comparisons but must link to this documented contract.

---

## 72. Enum option

A typed internal enum may be used:

```python
from enum import IntEnum

class ExitCode(IntEnum):
    OK = 0
    VALIDATION_FAILED = 1
    USAGE_ERROR = 2
    RUNTIME_ERROR = 3
    CANCELLED = 4
```

If introduced:

- public numeric values remain unchanged;
- `main()` still returns `int`;
- tests verify integer conversion;
- compatibility aliases remain temporary.

---

# 73. `determine_exit_code`

The final function must use the complete command result.

Recommended contract:

```python
def determine_exit_code(command_result: CommandResult) -> int:
    ...
```

For a validation-specific API:

```python
def determine_run_exit_code(run_result: RunResult) -> int:
    ...
```

It must not rely only on:

```text
fail_count
```

because the final architecture also has:

- framework `ERROR`;
- cancellation;
- scenario results;
- report failures;
- release gates.

---

## 74. Baseline migration

The inherited implementation uses:

```python
return EXIT_AUDIT_FAILURES if run_result.fail_count > 0 else EXIT_OK
```

The final implementation must additionally evaluate:

```text
run-level ERROR
controlled cancellation
required scenario outcomes
required release gates
required report/integrity failures
```

Migration preserves codes `0`–`3` and adds `4`.

---

## 75. Migration algorithm

Recommended transition:

```python
def determine_run_exit_code(run_result: RunResult) -> int:
    if run_result.cancelled:
        return EXIT_CANCELLED
    if run_result.overall_status == "ERROR":
        return EXIT_RUNTIME_ERROR
    if run_result.overall_status == "FAIL":
        return EXIT_VALIDATION_FAILED
    return EXIT_OK
```

Configuration exceptions raised before `RunResult` map to `2`.

Unexpected exceptions map to `3`.

---

## 76. Legacy name deprecation

Deprecated names:

```text
EXIT_AUDIT_FAILURES
EXIT_INVALID_ARGS
```

Replacements:

```text
EXIT_VALIDATION_FAILED
EXIT_USAGE_ERROR
```

Deprecation behavior:

- numeric compatibility retained;
- source alias may remain through the migration window;
- new tests use canonical names;
- canonical docs use canonical names;
- eventual alias removal follows versioning and deprecation policy.

---

# 77. Tests

Recommended test module:

```text
tests/reference/test_exit_codes.py
```

CLI tests:

```text
tests/integration/cli/test_cli_exit_codes.py
tests/contracts/test_cli_contracts.py
```

Launcher tests:

```text
tests/contracts/test_windows_launchers.py
```

---

## 78. Required constant tests

Verify:

```python
assert EXIT_OK == 0
assert EXIT_VALIDATION_FAILED == 1
assert EXIT_USAGE_ERROR == 2
assert EXIT_RUNTIME_ERROR == 3
assert EXIT_CANCELLED == 4
```

Verify temporary aliases equal their replacements while aliases are supported.

---

## 79. Required result-mapping tests

Test:

- overall `OK` → `0`;
- overall `FAIL` → `1`;
- overall `ERROR` → `3`;
- controlled cancellation → `4`;
- runtime error outranks prior validation failure;
- cancellation-handling error → `3`;
- optional skipped operation with successful run → `0`;
- required skipped criterion → nonzero according to cause.

---

## 80. Required parser tests

Test:

- help → `0`;
- version → `0`;
- unknown option → `2`;
- missing required option → `2`;
- invalid choice → `2`;
- non-integer `SystemExit` normalization → `2`;
- unexpected exception → `3`;
- `KeyboardInterrupt` with successful containment → `4`.

---

## 81. Required validation tests

Test:

- compilation failure → `1`;
- gold mismatch → `1`;
- required scenario assertion failure → `1`;
- release gate failure → `1`;
- launch failure → `3`;
- timeout → `3`;
- normalization failure → `3`;
- required report write failure → `3`;
- manifest verification failure → `3`.

---

## 82. Required child-code tests

Use fake processes returning:

```text
0
1
2
42
```

Verify that GF Wordbench determines its own code from the complete operation contract.

Do not assert direct forwarding.

---

## 83. Required negative-scenario test

Use a scenario expecting a nonzero GF process result.

Verify:

- scenario criterion passes;
- run status is `OK`;
- CLI returns `0`;
- child exit code remains recorded.

---

## 84. Required launcher tests

Verify Windows batch and other wrappers:

- propagate `0`;
- propagate `1`;
- propagate `2`;
- propagate `3`;
- propagate `4`;
- do not convert all failures to `1`;
- do not return `0` after failure.

---

## 85. Required CI example tests

Where documentation examples are executable, verify:

- shell examples preserve code;
- PowerShell example exits with captured value;
- batch example uses `%ERRORLEVEL%` correctly;
- unknown codes remain visible.

---

# 86. Versioning impact

Changing a numeric exit code is a breaking CLI contract.

After application `1.0.0`, it normally requires:

- application major version;
- CLI reference update;
- contract-lock update;
- launcher update;
- CI migration;
- tests;
- changelog entry;
- deprecation path where possible.

---

## 87. Compatible additions

Adding a new code from the reserved range may be compatible only when:

- existing codes retain meaning;
- old automation treats unknown nonzero as failure safely;
- the new distinction provides stable value;
- documentation and tests are updated.

Because automation may inspect exact values, every addition still requires explicit compatibility review.

---

## 88. Message changes

Changing human stderr wording without changing code semantics is normally compatible.

Scripts must use the numeric code or machine-readable artifacts, not exact human text.

Stable machine output modes may have separate schemas.

---

# 89. Drift indicators

Exit-code drift exists when:

- the CLI returns a child GF exit code directly;
- `fail_count` is the only final decision after `ERROR` exists;
- a timeout returns `1`;
- user cancellation returns `0`;
- invalid arguments return `3`;
- report failure is hidden behind `1`;
- CLI and launcher return different codes;
- Windows batch launcher omits `exit /b`;
- help returns nonzero;
- strict check violations return `0`;
- negative expected scenario returns the child nonzero code;
- canonical constants are duplicated with different values;
- a code changes without version review;
- GUI is used as the automation exit-code interface;
- unknown externally forced termination is labeled as canonical cancellation;
- CI suppresses nonzero results without enforcing them.

Any drift indicator requires contract review.

---

# 90. Compliance checklist

```text
[ ] canonical values are 0, 1, 2, 3, and 4
[ ] success maps to 0
[ ] completed criteria failure maps to 1
[ ] invalid invocation/configuration maps to 2
[ ] runtime/framework error maps to 3
[ ] controlled cancellation maps to 4
[ ] GF child codes remain recorded but are not forwarded
[ ] help and version return 0
[ ] parser errors return 2
[ ] timeout returns 3
[ ] launch failure returns 3
[ ] gold mismatch returns 1
[ ] required report failure returns 3
[ ] cancellation remains distinct from timeout
[ ] launcher propagates the exact code
[ ] CLI uses full run outcome, not only fail_count
[ ] legacy values 0–3 remain compatible
[ ] reserved values are not used ad hoc
[ ] tests cover every allocated code
```

---

# 91. Final invariants

1. GF Wordbench owns the application exit code.
2. Child GF exit codes are never forwarded automatically.
3. `0` means the requested command passed its required criteria.
4. `1` means completed evaluation found required failures.
5. `2` means the invocation or pre-execution configuration was invalid.
6. `3` means GF Wordbench could not complete or interpret the operation safely.
7. `4` means controlled cancellation.
8. Timeout is `3`, not `1` or `4`.
9. Launch failure is `3`.
10. Gold mismatch is normally `1`.
11. Required report or manifest failure is `3`.
12. Help and version return `0`.
13. Individual result statuses do not map directly without aggregation.
14. `SKIPPED` has no independent process code.
15. Warnings do not automatically change success.
16. Expected negative scenarios may still produce command success.
17. Launchers preserve the exact application code.
18. CI treats every nonzero value as unsuccessful unless it has an explicit classification policy.
19. Existing GF Audit numeric values `0`–`3` remain compatible.
20. Numeric changes require CLI contract and version review.

---

# 92. Final rule

GF Wordbench exit codes answer one question:

> What happened to the complete command requested from GF Wordbench?

The stable decision chain is:

```text
invalid request before execution
    → 2

valid request
    → controlled cancellation
        → 4
    → framework/runtime inability
        → 3
    → completed required-criterion failure
        → 1
    → complete success
        → 0
```

Detailed causes remain in structured results and artifacts.

Automation must use the exit code for the top-level outcome and `summary.json` for the complete explanation.
