# GF Wordbench — Debugging the Framework

**Document ID:** `GF-WB-DEVELOPMENT-DEBUGGING`  
**Status:** Normative development and incident-diagnosis guide  
**Applies to:** GF Wordbench framework code, tests, CLI, GUI, GF and registered diagnostic-tool integration, schemas, reports, migrations, and one active language project  
**Owner:** GF Wordbench maintainers  
**Canonical path:** `docs/development/DEBUGGING_THE_FRAMEWORK.md`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Document version:** `1.1.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines how to diagnose and correct defects in GF Wordbench itself.

It covers failures involving:

- startup and configuration;
- active-project loading;
- path resolution;
- file selection;
- source fingerprinting;
- static scanning;
- GF executable discovery;
- GF version probing;
- process creation and termination;
- compilation;
- diagnostic parsing;
- direct/downstream classification;
- scenario execution;
- output normalization;
- gold comparison;
- PGF construction;
- previous-run comparison;
- result aggregation;
- report generation;
- raw logs;
- manifest verification;
- application-state persistence;
- CLI behavior;
- GUI threading and state;
- schema migration;
- Windows-specific execution;
- test isolation;
- performance and nondeterminism;
- interfile and external-contract drift.

This is a framework-debugging guide.

It is not a guide for correcting the active language grammar itself.

Language-project debugging begins with the evidence produced by GF Wordbench, but language-specific source changes remain governed by:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
```

Every investigation concerns exactly one active Wordbench project and one run.
Cross-workspace discovery, multilingual readiness aggregation, and portfolio-wide
orchestration belong to the independent `gf-portfolio` product.

`gf-portfolio` may consume completed public Wordbench artifacts. It does not call
Wordbench's private debugging, process, validation, or migration APIs, and
Wordbench does not require Portfolio code, state, storage, configuration, or
services.

This guide does not track coding progress in document metadata or project records.

---

## 2. Related normative documents

Read this guide with:

```text
docs/00_START_HERE.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/DEPENDENCY_RULES.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/validation/VALIDATION_PIPELINE.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/reports/RAW_LOGS_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/development/CODEBASE_GUIDE.md
docs/development/TESTING_GF_WORDBENCH.md
docs/reference/EXIT_CODES.md
docs/reference/STATUS_VALUES.md
```

When this guide conflicts with an accepted ADR or lock, the ADR or lock governs. Contradictions are corrected at the owning contract and every affected consumer.

---

## 3. Core debugging rule

> Preserve the failing evidence, identify the contract owner, reproduce the defect through the narrowest public boundary, and fix the owner rather than patching every consumer.

Do not begin by editing the visible symptom.

Examples of incorrect first fixes:

- changing a report because a status is wrong;
- changing the GUI because `RunConfig` is wrong;
- changing a classifier because the compiler discarded stderr;
- updating gold because normalization changed unexpectedly;
- adding a path workaround in one caller;
- swallowing a migration exception;
- retrying a failed external process without recording the first attempt;
- converting a timeout into a generic `FAIL`;
- rebuilding a missing artifact in a report writer.

The first task is to determine where the incorrect fact entered the system.

---

## 4. Debugging objectives

A framework investigation must answer:

1. What exact request was made?
2. Which configuration sources contributed to it?
3. Which component owned the first incorrect value or behavior?
4. What evidence existed before interpretation?
5. Was the failure deterministic?
6. Was the external tool invoked correctly?
7. Did the framework preserve stdout, stderr, exit state, and artifacts?
8. Did interpretation change the meaning of the evidence?
9. Did a consumer rely on an undocumented field or path?
10. Did persisted data use the expected schema version?
11. Did GUI and CLI produce equivalent requests?
12. Did a prior compatibility path influence the result?
13. Can the defect be reproduced without the active language project?
14. Which regression test will fail before the fix and pass after it?

A correction is incomplete until the last question is answered.

---

## 5. Framework failure versus project failure

Before changing framework code, classify the observed problem.

### 5.1 Project validation failure

Examples:

- GF reports a syntax error in a project `.gf` file;
- GF reports a type mismatch in a project module;
- a scenario’s expected parse fails;
- a normalized scenario output differs from reviewed gold;
- a required linearization is missing;
- a project entrypoint cannot compile because a provider module is defective.

Typical result:

```text
validation_status = FAIL
```

This is not automatically a GF Wordbench bug.

### 5.2 Framework error

Examples:

- GF cannot be launched although the configured executable is valid;
- timeout state is lost;
- stderr is discarded;
- the wrong working directory is used;
- two callers build different GF paths;
- a file outside the project is selected unexpectedly;
- a required log is overwritten;
- `summary.json` contains inconsistent totals;
- a report reruns GF;
- a manifest hashes stale bytes;
- the GUI displays `FAIL` as successful;
- a schema migration silently changes meaning.

Typical result:

```text
validation_status = ERROR
```

or an unhandled exception.

### 5.3 Environment failure

Examples:

- configured GF executable is missing;
- RGL root is absent;
- output root is unwritable;
- required runtime dependency is not installed;
- Windows execution policy blocks a launcher;
- antivirus or endpoint policy prevents child-process creation.

Environment failures may be correctly detected by the framework.

Do not change framework behavior merely to hide an invalid environment.

### 5.4 Contract failure

Examples:

- GF exits zero but required PGF is missing;
- a scenario exits but required end marker is absent;
- a report writer returns a path different from its owned path;
- a persisted enum contains an unknown value;
- a consumer reconstructs an artifact filename incorrectly;
- a writer emits an unversioned canonical file.

A contract failure means execution occurred, but an expected boundary was violated.

---

## 6. The four axes to inspect

When debugging any result, inspect all four axes.

```text
validation_status
execution_state
error_kind
diagnostic_class
```

### 6.1 Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

Question:

```text
Did the requested validation criterion pass?
```

### 6.2 Execution state

```text
completed
timed_out
cancelled
launch_failed
```

Question:

```text
What happened to execution?
```

### 6.3 Error kind

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

Question:

```text
What broad kind of problem occurred?
```

### 6.4 Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Question:

```text
Where is this result in the causal graph?
```

If one field appears to encode two questions, inspect the model and aggregation code for drift.

---

## 7. Evidence hierarchy

Use this investigation order:

1. exact source revision;
2. resolved `RunConfig`;
3. structured process request;
4. process metadata;
5. individual raw stdout and stderr;
6. generated artifacts;
7. parsed diagnostic fields;
8. classified result;
9. `summary.json`;
10. human reports;
11. GUI presentation.

Do not debug a low-level process defect only from GUI text.

Do not debug diagnostic parsing only from `summary.md`.

Do not debug report generation only from `ALL_LOGS.TXT`.

The individual raw files and structured values are closer to the originating event.

---

## 8. Preserve the failing run

Before rerunning or editing:

```text
copy or archive the run directory
record the source revision
record the project revision
record the GF version
record the RGL revision or installation identity
record the command or GUI selections
record the operating system
record whether the failure reproduced
```

Minimum artifacts to preserve:

```text
summary.json
manifest.json, when available
raw/master.log
relevant individual stdout/stderr
relevant scan log
scenario normalized output
gold diff
project.toml
```

Do not modify the preserved copy.

A later fixed run should use a new run directory.

---

## 9. Do not destroy the original failure

Prohibited investigation shortcuts:

- deleting the failing run before comparison;
- updating gold before understanding the mismatch;
- editing raw logs;
- replacing stderr with a summarized message;
- rerunning into the same run directory;
- disabling the failing stage without recording it;
- catching every exception and returning `OK`;
- converting all errors to `OTHER`;
- deleting malformed state before copying it;
- rewriting a legacy summary during read-only migration;
- changing source and framework code simultaneously without a baseline.

A successful debug session requires the original evidence to remain inspectable.

---

# 10. First-response checklist

Use this sequence for an unknown failure.

```text
[ ] Reproduce once without changing code
[ ] Record exact invocation
[ ] Preserve the failing run
[ ] Read summary.json
[ ] Read raw/master.log
[ ] Read the relevant individual stdout and stderr
[ ] Check execution_state
[ ] Check validation_status
[ ] Check error_kind
[ ] Check diagnostic_class
[ ] Verify the executed command and working directory
[ ] Verify the expected artifact exists
[ ] Reproduce through CLI when the failure came from GUI
[ ] Reproduce with a fixture project when possible
[ ] Identify the first component that produced an incorrect fact
[ ] Write a failing regression test
[ ] Apply the narrowest owner-level fix
[ ] Run focused tests
[ ] Run complete tests
[ ] Compare pre-fix and post-fix artifacts
[ ] Review affected locks and schemas
```

---

# 11. Establish a clean development baseline

Before debugging a specific issue, establish whether the checkout is healthy.

From the repository root:

```powershell
python -m compileall app tests
python -m pytest
```

For focused output:

```powershell
python -m pytest -x -vv
```

For one test file:

```powershell
python -m pytest tests\test_classifier.py -vv
```

For one test:

```powershell
python -m pytest tests\test_classifier.py::test_name -vv
```

For matching tests:

```powershell
python -m pytest -k "timeout or process" -vv
```

To expose captured output:

```powershell
python -m pytest -s -vv
```

To stop after a small number of failures:

```powershell
python -m pytest --maxfail=1 -vv
```

To enter the debugger on failure:

```powershell
python -m pytest --pdb -x
```

Use the repository’s documented virtual environment.

Do not interpret import failures until the expected interpreter is confirmed.

---

## 12. Record interpreter and package context

Useful commands:

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -c "import sys; print(*sys.path, sep='\n')"
python -c "import app; print(app.__file__)"
python -c "import PySide6; print(PySide6.__version__)"
```

For the active working directory:

```powershell
python -c "from pathlib import Path; print(Path.cwd())"
```

For environment variables relevant to diagnosis:

```powershell
Get-ChildItem Env: | Where-Object {
    $_.Name -match '^(PYTHON|GF|PATH|TEMP|TMP)'
}
```

Do not paste complete environment dumps into public bug reports.

Redact secrets and unrelated paths.

---

# 13. Reproduction levels

Reduce a defect through these levels.

### Level 1 — Full GUI reproduction

Use only to confirm the user-visible defect.

### Level 2 — CLI reproduction

Use equivalent explicit settings.

This removes Qt, widget state, and worker-thread presentation.

### Level 3 — Shared orchestration call

Call:

```python
run_audit(run_config)
```

from a focused test or script.

This removes CLI parsing.

### Level 4 — Stage public function

Examples:

```text
select_files
scan_file
compile_file
classify_file_results
load_previous_summary
write_summary_json
```

Use only when the stage boundary is the suspected owner.

### Level 5 — Utility boundary

Examples:

```text
run_process_with_timeout
parse_compile_summary
write_json
normalize_path
```

### Level 6 — Pure-function fixture

Use synthetic inputs with no filesystem or external process where possible.

Stop reducing when the defect no longer reproduces.

The first level where it appears often identifies the ownership boundary.

---

# 14. Minimal reproduction requirements

A good minimal reproduction contains:

```text
framework revision
Python version
platform
GF version, when relevant
RGL identity, when relevant
minimal project.toml
minimal source files
exact request
expected result
actual result
raw evidence
failing assertion
```

Avoid using the complete active language project unless the defect depends on its scale or structure.

Framework tests should use a tiny synthetic grammar.

---

# 15. Debugging map by owner

| Symptom | First owner to inspect |
|---|---|
| wrong project identity or project-owned defaults | `projects` module |
| wrong merged run configuration | application use case and `bootstrap` composition |
| invalid run lifecycle, paths, totals, or terminal status | `runs` module |
| unexpected files selected | `validation` file-selection owner |
| incorrect static finding | `validation` static-scan owner |
| incorrect GF command or search path | GF anti-corruption adapter and validation request builder |
| process timeout, cancellation, capture, or containment defect | external-process port and platform process adapter |
| GF text interpreted incorrectly | `diagnostics` parser |
| direct/downstream/ambiguous classification wrong | `diagnostics` classifier |
| source fingerprint unstable | validation fingerprint owner |
| scenario markers, assertions, normalization, or gold comparison wrong | `validation` scenario owners |
| previous-run comparison wrong | run comparison owner |
| JSON, Markdown, AI-ready, detail, or aggregate report wrong | `reporting` module |
| manifest or artifact integrity wrong | reporting artifact/manifest owner |
| GUI or CLI request differs | corresponding entrypoint and shared application use case |
| state load/save wrong | application-state adapter |
| schema compatibility or migration wrong | persisted-schema owner and migration adapter |
| registered diagnostic tool runs incorrectly | diagnostics tool registry, adapter, and external-process boundary |
| startup or dependency composition fails | `bootstrap` |

Concrete filenames may be inspected after the owner is identified, but filenames
do not redefine architectural ownership.

Do not change a consumer before confirming the producer's contract.

---

# 16. Debugging application orchestration

The application use case coordinates modules but does not duplicate their
domain rules, process mechanics, diagnostic parsing, or report rendering.

Inspect application orchestration when:

- stages execute in the wrong order;
- one stage receives the wrong result;
- independent work stops too early;
- dependent work runs after a fatal prerequisite;
- run finalization is not attempted after an error;
- reports are written from incomplete or stale results;
- previous-run comparison mutates current results;
- GUI and CLI runs differ despite equivalent resolved configuration;
- exceptions disappear;
- counts are calculated before classification completes.

### 16.1 Canonical orchestration shape

```text
resolve one active project
→ build and validate run configuration
→ create run paths
→ resolve and probe GF
→ select files and checkpoints
→ run static scan
→ fingerprint sources
→ compile required targets
→ classify diagnostics
→ run native .gfs scenarios
→ normalize and compare reviewed golds
→ build required PGF
→ evaluate release gates
→ assemble RunResult
→ write reports and public artifacts
→ build and verify manifest
→ finalize the run atomically
```

A mode may omit optional stages, but it cannot reorder or silently bypass
required dependencies.

### 16.2 Orchestration debugging questions

```text
Was one active project resolved before execution?
Was RunConfig immutable before stage execution?
Was the run directory created exactly once?
Was each selected subject represented?
Were exceptions converted at the correct boundary?
Was classification delayed until required evidence existed?
Were counts recalculated after classification?
Was the previous summary loaded read-only?
Did reporting consume the terminal RunResult?
Was best-effort reporting permitted for this mode?
Did finalization modify overall status?
Was the summary regenerated after a late manifest failure?
```

### 16.3 Instrumentation

Temporarily log:

```text
stage ID
input count
output count
required flag
status
exception type
artifact paths
```

Do not log complete source text or secrets.

### 16.4 Common orchestration defect

Symptom:

```text
the use case raises, but partial reports show success
```

Likely causes:

- overall status built before the fatal error;
- report writer uses a stale `RunResult`;
- exception path does not update counts;
- GUI interprets worker completion as success;
- best-effort reporting hides report failure without recording it.

Fix the run lifecycle or application-orchestration owner.

Do not patch summary wording only.

---

# 17. Debugging configuration and bootstrap

Inspect bootstrap when:

- GUI and CLI differ;
- a valid path becomes empty;
- project values are overridden by stale state;
- a mode constraint is not enforced;
- environment discovery selects an unexpected GF;
- language-specific paths remain after cloning;
- legacy modes are emitted instead of migrated;
- application state overrides `project.toml`.

### 17.1 Configuration precedence

Verify the effective precedence:

```text
framework defaults
→ project.toml
→ local environment
→ disposable app state
→ explicit invocation
→ mode constraints
```

Project-owned fields must not be taken from stale GUI state.

### 17.2 Dump resolved configuration safely

Use a controlled diagnostic representation:

```python
from dataclasses import asdict
from pprint import pprint

payload = asdict(run_config)
for secret_key in {"token", "password", "secret"}:
    payload.pop(secret_key, None)
pprint(payload)
```

Use the model’s official serialization method when available.

### 17.3 Compare GUI and CLI

Build both configurations without running:

```python
assert gui_run_config.to_dict() == cli_run_config.to_dict()
```

Normalize paths and default values before comparison.

### 17.4 Common bootstrap defects

#### Empty `Path("")`

In Python:

```python
Path("")
```

represents the current directory.

A blank required field must be rejected before conversion or represented as `None`.

#### Boolean coercion

Avoid:

```python
bool("false")
```

because it is `True`.

Use explicit boolean parsing.

#### Stale project-owned state

Legacy fields such as:

```text
selected_scan_dir
selected_scan_glob
selected_include_regex
selected_exclude_regex
```

must be discarded after `project.toml` becomes authoritative.

#### Legacy mode leakage

Readers may accept:

```text
file
all
```

Canonical writers must emit:

```text
quick
diagnostic
```

---

# 18. Debugging application state

Canonical state:

```text
.gf_wordbench_state.json
```

Legacy state:

```text
.gf_audit_state.json
```

Inspect state handling when:

- the GUI crashes on startup;
- paths revert unexpectedly;
- `is_running` remains true after restart;
- the wrong project opens;
- a legacy field overrides a project field;
- state is truncated;
- an invalid enum is silently accepted;
- saving state destroys the previous valid file.

### 18.1 Safe investigation

1. Copy the malformed state.
2. Validate JSON syntax.
3. Record schema ID and version.
4. Load through the official reader.
5. Inspect migration warnings.
6. Compare canonical output.
7. Confirm the legacy source remains unchanged.
8. Confirm runtime-only fields are reset.

### 18.2 Never debug by silent deletion only

Deleting state may restore startup, but it does not identify the bug.

Preserve the malformed file and add it as a migration fixture when appropriate.

### 18.3 Atomic-write verification

Simulate failure between:

```text
temporary write
flush
validation
replace
```

The last valid state must survive.

### 18.4 Runtime-only values

Verify these are not persisted:

```text
is_running = true
current_run_config
current_run_result
worker objects
thread objects
cancellation tokens
```

---

# 19. Debugging paths and run directories

Inspect path ownership when:

- logs appear outside the run directory;
- two files overwrite each other;
- Windows paths with spaces fail;
- relative paths resolve from the launcher location;
- a selected source escapes the project;
- a manifest path contains `..`;
- GUI opens the wrong artifact;
- a run overwrites another run.

### 19.1 Required path facts

For every failing path, record:

```text
raw input
expanded path
absolute path
resolved path
project-relative path
run-relative path
existence
file/directory type
containment result
```

### 19.2 Avoid string-prefix containment

Incorrect:

```python
str(child).startswith(str(root))
```

Correct approach:

```python
child.resolve().relative_to(root.resolve())
```

with deliberate handling for missing paths, symlinks, junctions, and platform behavior.

### 19.3 Paths containing spaces

Test at least:

```text
C:\Temp\GF Wordbench Test\
C:\Program Files\GF\bin\gf.exe
```

Arguments must remain separate list items.

Do not add manual quotes when using `shell=False`.

### 19.4 Run ID collision

Create two runs with the same mocked timestamp.

Expected:

```text
run_20260721_163210
run_20260721_163210_02
```

Neither run may be overwritten.

### 19.5 Safe filename collision

Two project paths may produce the same stem.

Verify the safe-key builder resolves collisions deterministically.

---

# 20. Debugging file selection

Inspect `file_selector` when:

- expected files are missing;
- backup files are included;
- order changes between runs;
- target mode selects more than one file;
- a file outside the project is included;
- include/exclude regex behaves differently in GUI and CLI;
- maximum-file limits produce unstable subsets.

### 20.1 Record selection pipeline

For each candidate:

```text
candidate path
source glob match
include-rule result
exclude-rule result
containment result
final decision
reason
```

### 20.2 Deterministic order

Canonical file order:

```text
normalized project-relative path
```

Do not depend on filesystem enumeration order.

### 20.3 Filter precedence

Document and test:

```text
source candidate
→ containment
→ include
→ exclude
→ mode target/checkpoint
→ limit
→ canonical sort
```

If another order is intended, use one shared implementation.

### 20.4 Empty selection

An empty required selection is not success.

Debug whether the problem belongs to:

- invalid configuration;
- filter mismatch;
- missing files;
- stale checkpoint;
- incorrect project root;
- containment failure.

---

# 21. Debugging source fingerprints

Inspect fingerprinting when:

- previous-run comparison reports every file changed;
- unchanged files get different hashes;
- source mutation is not detected;
- Unicode files hash inconsistently;
- legacy SHA-1 values leak into canonical summaries.

### 21.1 Canonical fingerprint

Use raw file bytes and SHA-256.

Record:

```text
size_bytes
sha256
last_modified_utc
```

Timestamp is metadata.

Hash is content identity.

### 21.2 Debug steps

```python
from hashlib import sha256
from pathlib import Path

path = Path("project/path/to/file.gf")
data = path.read_bytes()
print(len(data))
print(sha256(data).hexdigest())
```

Compare with the persisted result.

### 21.3 Common defects

- hashing decoded text instead of bytes;
- newline conversion before hashing;
- hashing an absolute path with content;
- reading the file twice across a modification;
- using locale-dependent encoding;
- truncating before hashing;
- importing legacy short hashes as canonical SHA-256.

---

# 22. Debugging the scanner

Inspect:

```text
app/audit/scanner.py
app/utils/gf_utils.py
```

when:

- a rule triggers inside comments;
- a rule misses multiline structures;
- quoted strings are parsed incorrectly;
- line numbers are wrong;
- one rule changes another rule’s input;
- a scanner exception aborts every file;
- a scan warning becomes a compile failure.

### 22.1 Scanner truth boundary

The scanner is heuristic.

Do not “fix” a scanner mismatch by changing GF compiler interpretation.

### 22.2 Minimal scanner fixture

Use a source string containing:

```text
real target pattern
same pattern inside line comment
same pattern inside block comment
same pattern inside string
multiline block
Unicode text
trailing whitespace
```

Assert exact line numbers and counts.

### 22.3 Debug intermediate representations

Temporarily inspect:

```text
original line
comment-masked line
string-masked line
brace depth
active block
rule decision
```

Do not persist temporary internal masks as canonical scan logs.

### 22.4 Common scanner defects

- regex applied before masking comments;
- escaped quote mishandled;
- brace balance counted inside strings;
- CRLF line counting mismatch;
- zero-based and one-based line confusion;
- broad regex matching language data;
- scanner rule IDs changing without report updates.

---

# 23. Debugging GF executable discovery

Inspect configuration/bootstrap/GF adapter when:

- GUI selects one executable and CLI uses another;
- `PATH` discovery wins over an explicit path;
- a directory is accepted as `gf.exe`;
- a missing executable is reported as a source failure;
- a valid path with spaces fails;
- the executable changes after version probing.

### 23.1 Record resolution chain

```text
explicit invocation
GUI value
application state
environment setting
PATH candidate
resolved final path
```

The final path must be immutable for one run.

### 23.2 Direct launch test

PowerShell:

```powershell
& "C:\Path With Spaces\gf.exe" --version
```

Python:

```powershell
python -c "import subprocess; print(subprocess.run([r'C:\Path With Spaces\gf.exe', '--version'], text=True, capture_output=True).returncode)"
```

### 23.3 Distinguish failures

```text
path missing
path is directory
permission failure
invalid executable format
dependent runtime missing
launch blocked by security software
tool launched and exited non-zero
```

These require different messages.

---

# 24. Debugging process execution

Inspect:

```text
app/utils/process_utils.py
```

when:

- a timeout hangs;
- stdout or stderr is missing;
- exit code is wrong;
- child processes remain alive;
- encoding errors crash the run;
- working directory is ignored;
- environment variables leak;
- cancellation is treated as timeout;
- a shell window flashes unexpectedly on Windows.

### 24.1 Required request facts

Record:

```text
executable
ordered arguments
working directory
environment overrides
stdin mode
timeout
expected artifacts
operation ID
```

### 24.2 Required result facts

Record:

```text
started_at
finished_at
duration_ms
execution_state
exit_code
timed_out
cancelled
launch_error
stdout path
stderr path
```

### 24.3 Use a fake executable

A small Python test program can simulate:

```text
stdout
stderr
non-zero exit
sleep/timeout
partial output
invalid bytes
child process
large output
missing artifact
```

Conceptual fixture:

```python
import os
import subprocess
import sys
import time

mode = sys.argv[1]

if mode == "stdout":
    print("hello")
elif mode == "stderr":
    print("problem", file=sys.stderr)
elif mode == "exit":
    raise SystemExit(7)
elif mode == "sleep":
    print("started", flush=True)
    time.sleep(60)
elif mode == "child":
    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    time.sleep(60)
```

Keep the actual fixture under `tests/fixtures/`.

### 24.4 Timeout investigation

Verify:

1. timeout value is positive;
2. elapsed time is measured monotonically;
3. process termination is requested;
4. child-process termination policy runs;
5. remaining output is collected;
6. `timed_out=true`;
7. `execution_state=timed_out`;
8. status becomes `ERROR`;
9. timeout is not parsed as GF syntax/type failure.

### 24.5 Deadlock symptoms

Possible causes:

- reading stdout and stderr sequentially from full pipes;
- waiting before draining streams;
- blocking GUI thread;
- child inherits unexpected handles;
- process tree remains alive;
- worker waits for a signal emitted on the same blocked thread.

Use `communicate()` or a designed streaming capture mechanism.

Do not mix ad hoc stream readers across callers.

---

# 25. Debugging GF version probing

Inspect when:

- version is `UNKNOWN` despite visible output;
- stderr contains the version but stdout is empty;
- probe compiles project files;
- probe timeout uses compile timeout accidentally;
- a newer version is rejected unexpectedly;
- compatibility uses report prose.

### 25.1 Expected selection

Version text:

1. first non-empty stdout line;
2. otherwise first non-empty stderr line;
3. otherwise `UNKNOWN`.

### 25.2 Evidence

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

### 25.3 Debug data

Record:

```text
raw stdout bytes
raw stderr bytes
decoded stdout
decoded stderr
selected display string
normalized version
recognized flag
compatibility category
```

### 25.4 Common defects

- stripping all lines before selection;
- looking only at stdout;
- locale-specific text parser too strict;
- comparing version strings lexically;
- hidden `PATH` executable differs from recorded executable;
- treating unknown output as recognized success.

---

# 26. Debugging GF command construction

Inspect:

```text
app/audit/compiler.py
GF toolchain adapter
GF path resolver
```

when:

- option order changes;
- source file is not the terminal argument;
- GF path differs between operations;
- output directories are missing;
- CPU flag is always enabled;
- release and file compile commands are conflated;
- Windows quoting fails.

### 26.1 Compare structured arguments

Expected conceptual compile command:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

Expected conceptual PGF command:

```text
<gf> -make -optimize-pgf <path-options> <entrypoints...>
```

Inspect the list representation, not a rendered string.

### 26.2 Argument-debug assertion

```python
assert args[-1] == str(source_file)
assert "--cpu" not in args or run_config.emit_cpu_stats
```

Use the exact supported option spelling selected by the GF-version adapter.

### 26.3 GF path drift

Compare path components from:

```text
compile
PGF build
scenario execution
introspection
```

All should use one path-resolution owner.

### 26.4 Working directory drift

Record `cwd` for every operation.

Do not assume repository root, GUI launch directory, or executable directory.

---

# 27. Debugging compilation

Inspect:

```text
app/audit/compiler.py
app/utils/process_utils.py
diagnostic parser
```

when:

- compile succeeds manually but fails in GF Wordbench;
- `stdout` and `stderr` paths are missing;
- exit code zero becomes failure;
- exit code non-zero becomes success;
- no-compile appears as `OK`;
- timeout appears as direct source failure;
- `.gfo` artifacts are missing;
- diagnostics point to the wrong file.

### 27.1 Manual parity test

Use the exact recorded:

```text
executable
arguments
working directory
environment overrides
```

Do not manually simplify the command.

If the recorded command fails manually, investigate GF/project/environment.

If it succeeds manually, investigate process invocation or evidence interpretation.

### 27.2 Compile layers

Debug separately:

```text
request construction
process execution
stream persistence
artifact detection
diagnostic parsing
CompileSummary construction
FileResult construction
causal classification
```

### 27.3 No-compile behavior

Expected:

```text
validation_status = SKIPPED
diagnostic_class = skipped
```

or downstream where a known prerequisite block exists.

It must not imitate an executed success with exit code zero.

### 27.4 Artifact check

Verify:

```text
expected artifact path
actual filesystem path
file existence
file size
producer operation
path containment
manifest registration
```

---

# 28. Debugging diagnostic parsing

Inspect:

```text
app/utils/gf_utils.py
dedicated diagnostic parser
```

when:

- `first_error` is empty;
- type failure becomes syntax failure;
- Windows paths are truncated at `:`;
- multiline error details disappear;
- stderr-only diagnostics are ignored;
- one GF version breaks patterns;
- normal output is mistaken for fatal diagnostics.

### 28.1 Parser input

Use both streams while preserving them separately.

Recommended combined interpretation input:

```text
stdout text
stderr text
exit code
timeout state
launch error
GF version
operation kind
```

### 28.2 Parser fixtures

Store realistic excerpts for:

```text
syntax error
type error
unification error
unknown identifier
missing module
internal GF error
warning only
stdout diagnostic
stderr diagnostic
Windows path
POSIX path
Unicode path
multiline detail
unknown diagnostic from another GF version
```

Do not use only invented one-line messages.

### 28.3 Pattern precedence

A broad fallback pattern must run after specific patterns.

Example:

```text
TIMEOUT state
→ launch/tool state
→ explicit GF internal
→ syntax
→ type/unification
→ other non-zero
```

### 28.4 Unknown diagnostic

Expected:

```text
validation_status remains non-successful
error_kind = OTHER or TOOL as justified
diagnostic_class = ambiguous when causality is unclear
raw evidence retained
```

Do not guess a precise category.

---

# 29. Debugging classification

Inspect:

```text
app/audit/classifier.py
```

when:

- every failure is direct;
- downstream failures have no blockers;
- a timeout is classified as a source root;
- a diagnostic naming another file is still direct;
- circular blockers appear;
- blocker ordering changes;
- a successful file remains downstream;
- a skipped file becomes failure.

### 29.1 Classifier inputs

Confirm:

```text
file identity
module identity
status
error kind
first error
diagnostic locations
all results
dependency information
compile-skipped state
```

### 29.2 Classifier must not

- execute GF;
- read a human report;
- modify raw diagnostics;
- infer a blocker solely from filename similarity;
- classify process infrastructure as source causality automatically.

### 29.3 Direct classification test

Strong evidence:

```text
diagnostic location matches current file
```

### 29.4 Downstream test

Strong evidence:

```text
diagnostic references a known failed provider
dependency map confirms relation
```

Expected:

```text
diagnostic_class = downstream
blocked_by = [provider identity]
```

### 29.5 Ambiguous test

When evidence is insufficient:

```text
diagnostic_class = ambiguous
```

Do not improve apparent certainty by weakening tests.

### 29.6 Cycle debugging

If A blocks B and B blocks A:

- inspect dependency extraction;
- distinguish direct roots before closure;
- prevent self-reference;
- collapse blockers only after root set is stable;
- test deterministic cycle handling.

---

# 30. Debugging scenario execution

Inspect:

```text
scenario runner
process runner
marker verifier
normalizer
```

when:

- a `.gfs` file works manually but not in GF Wordbench;
- scenario exits zero without passing;
- markers are missing;
- script input is truncated;
- wrong grammar is loaded;
- stdout and stderr are merged;
- scenario times out;
- a prohibited shell escape runs;
- scenario order changes.

### 30.1 Reproduce with exact stdin

Use the exact scenario bytes and recorded command.

Verify:

```text
UTF-8 encoding
final newline
working directory
GF path
loaded grammar
timeout
```

### 30.2 Marker debugging

Record:

```text
required markers
found markers
position of each marker
duplicate marker IDs
forbidden markers
final marker state
```

A zero exit code does not override missing required markers.

### 30.3 Scenario prerequisite debugging

If a scenario is skipped:

```text
was it optional?
was it filtered?
was it blocked?
which entrypoint failed?
was PGF expected first?
```

Use `blocked_by`.

Do not call every omitted scenario `skipped` without cause.

---

# 31. Debugging normalization

Inspect the versioned normalizer when:

- gold changes on every machine;
- meaningful Unicode disappears;
- paths remain unstable;
- line ordering changes;
- diagnostic wording is paraphrased;
- markers are removed;
- normalization hides a real GF-version change.

### 31.1 Compare three files

```text
raw stdout
normalized actual output
gold
```

Do not compare only actual versus gold.

### 31.2 Allowed normalization examples

```text
CRLF → LF
ANSI removal
approved absolute path tokens
trailing-space removal
approved unstable duration token
```

### 31.3 Forbidden normalization examples

```text
removing abstract trees
changing linearized strings
sorting order-dependent output
deleting errors
changing punctuation
folding Unicode distinctions
inventing missing markers
```

### 31.4 Version mismatch

Check:

```text
scenario normalization version
gold normalization version
current normalizer version
```

A changed version requires deliberate gold review.

---

# 32. Debugging gold comparison

Inspect gold comparator when:

- identical files mismatch;
- different files match;
- missing gold is created automatically;
- line endings cause unexpected failure;
- comparison modifies expected files;
- wrong scenario gold is loaded;
- diff output is misleading.

### 32.1 Verify identities

```text
scenario ID
scenario filename
gold filename
header scenario ID
normalization version
```

### 32.2 Byte and text comparison

Check:

```python
actual_bytes = actual_path.read_bytes()
gold_bytes = gold_path.read_bytes()
print(actual_bytes == gold_bytes)
```

Then compare canonical text after allowed newline normalization.

### 32.3 Read-only guarantee

Capture the gold fingerprint before and after a normal validation run.

They must match.

### 32.4 Atomic update workflow

Only the explicit gold-update command may write gold.

Debug update separately from comparison.

---

# 33. Debugging PGF build

Inspect PGF builder/GF adapter when:

- file compiles but release fails;
- `.pgf` is missing;
- `.pgf` is zero bytes;
- wrong entrypoints are passed;
- output is outside the run directory;
- a prior release PGF is overwritten;
- manifest lacks the PGF.

### 33.1 Separate stage

Do not debug PGF build as a file-compilation detail.

Record:

```text
entrypoint order
GF command
working directory
GF path
timeout
expected PGF name
actual generated paths
file size
manifest entry
```

### 33.2 Multiple candidates

If GF generates more than one PGF candidate:

- use declared identity;
- reject ambiguity;
- do not pick the newest file heuristically.

### 33.3 Stale artifact

Delete only the temporary test run’s PGF before reproduction.

Do not let a previous file satisfy a current artifact check.

Use a fresh run directory in tests.

---

# 34. Debugging previous-run comparison

Inspect:

```text
app/audit/diff.py
summary migration reader
```

when:

- the current run compares with itself;
- a run from another project is selected;
- every item appears new;
- removed items disappear;
- legacy summaries crash comparison;
- comparison changes current status;
- the newest directory is incomplete.

### 34.1 Baseline eligibility

Verify:

```text
different run ID
same project identity
supported summary schema
compatible comparison policy
complete summary
normalization compatibility
```

### 34.2 Selection evidence

Log candidate rejection reasons:

```text
current run
wrong project
unsupported schema
missing summary
corrupt summary
incompatible mode
incomplete run
```

### 34.3 Stable identity

Compare files by project-relative path.

Compare scenarios by scenario ID.

Do not compare absolute paths across machines.

### 34.4 Current-result isolation

A diff failure must not mutate current file/scenario results.

It may add a warning or strict finalization error.

---

# 35. Debugging `RunResult` and counts

Inspect:

```text
app/audit/result_model.py
models
```

when:

- counts disagree with lists;
- overall status is wrong;
- top errors are unstable;
- `FAIL` and `ERROR` are mixed;
- skipped required work still returns `OK`;
- new fields disappear during serialization.

### 35.1 Recalculate from collections

Use independent assertions:

```python
assert files_included == (
    files_ok + files_fail + files_error + files_skipped
)
assert scenarios_seen == (
    scenarios_ok + scenarios_fail + scenarios_error + scenarios_skipped
)
```

### 35.2 Aggregation priority

Expected:

```text
ERROR > FAIL > OK
```

A required `SKIPPED` prevents `OK`.

### 35.3 Top errors

Verify deterministic order:

1. descending count;
2. case-insensitive message;
3. stable kind.

Do not count downstream copies as independent roots when presenting a root-cause view.

### 35.4 Serialization round trip

```python
payload = run_result.to_dict()
restored = RunResult.from_dict(payload)
assert restored.to_dict() == payload
```

Use official schema readers and writers.

---

# 36. Debugging report generation

Inspect reports when:

- files are missing;
- a report contains stale status;
- report generation changes the run;
- one report imports the compiler;
- paths are reconstructed incorrectly;
- a report exception hides the original failure;
- `summary.md` disagrees with `summary.json`.

### 36.1 Report source

All reports derive from one terminal `RunResult`.

Verify that report writers do not:

```text
run GF
scan files
classify failures
load project configuration independently
recalculate file selection
update gold
```

### 36.2 Writer isolation

Test each writer with a synthetic `RunResult`.

Examples:

```text
all OK
direct failure
downstream failure
ambiguous failure
framework ERROR
scenario mismatch
missing optional artifact
Unicode paths
empty collections
```

### 36.3 Best-effort behavior

Best-effort report generation after a fatal error is permitted only by the resolved run policy.

Debug two questions separately:

1. Did the original validation fail correctly?
2. Did secondary report generation also fail?

The secondary failure must not replace the primary cause.

### 36.4 Report-order defect

If an aggregate copies a report before that report is finalized, the aggregate becomes stale.

Generate aggregates after their source artifacts are closed and immutable.

### 36.5 `ALL_LOGS.TXT`

The aggregate contains operational evidence, not recursive copies of every report.

If debugging old runs, recognize legacy aggregate composition.

---

# 37. Debugging `summary.json`

Inspect JSON writer/schema when:

- GUI cannot load a run;
- diff loader fails;
- enums are unknown;
- paths are absolute unexpectedly;
- null and missing fields behave differently;
- old fields reappear;
- arrays are unstable;
- schema version does not change after shape changes.

### 37.1 Validate identity

```text
schema_id = gf-wordbench.run-summary
schema_version = 1.0
```

### 37.2 Required debugging checks

```text
required fields present
correct primitive types
canonical enum values
run-relative artifact paths
project-relative source paths
deterministic arrays
no secrets
no legacy aliases emitted
```

### 37.3 Missing versus null

Do not treat them automatically as equivalent.

Use schema-defined defaults only.

### 37.4 Writer-reader compatibility

Test:

```text
current writer → current reader
legacy nested reader → canonical model
legacy flat reader → canonical model
current writer → diff loader
current writer → GUI loader
```

### 37.5 Atomic write failure

Inject a failure before replacement.

The prior valid summary must survive.

---

# 38. Debugging the manifest

Inspect manifest writer/verifier when:

- hashes do not match immediately;
- summary is missing from manifest;
- manifest hashes itself;
- paths escape the run directory;
- duplicate paths exist;
- a required log is omitted;
- report bytes change after hashing;
- an empty stream is treated as missing.

### 38.1 Immutable-byte rule

Hashes are computed after all writes close.

No artifact may be modified after its manifest hash is recorded.

### 38.2 Self-reference

`manifest.json` must not hash itself.

### 38.3 Empty files

A zero-byte required stdout or stderr file is valid and has the SHA-256 hash of empty bytes.

### 38.4 Verification script

Conceptual:

```python
from hashlib import sha256
from pathlib import Path

path = Path(run_dir, entry["path"])
assert path.is_file()
assert path.stat().st_size == entry["size_bytes"]
assert sha256(path.read_bytes()).hexdigest() == entry["sha256"]
```

Also verify containment and uniqueness.

### 38.5 Late failure loop

If manifest verification changes overall status:

1. update `RunResult`;
2. regenerate summary and dependent reports;
3. regenerate manifest;
4. verify again;
5. publish.

Avoid infinite regeneration loops by defining a bounded finalization state machine.

---

# 39. Debugging raw logs

Inspect raw-log writers when:

- stdout and stderr are merged;
- empty files are absent;
- aggregate ordering changes;
- timestamps are misleading;
- a timeout message appears as though GF emitted it;
- invalid bytes vanish;
- `ALL_LOGS.TXT` is the only evidence copy.

### 39.1 Individual files first

Inspect:

```text
raw/gf_version.*
raw/compile/*
raw/scan/*
raw/scenarios/*
```

before aggregate files.

### 39.2 Empty versus missing

```text
empty = captured stream contained zero characters
missing = capture or artifact contract failure, or operation not launched
```

### 39.3 Master log

Use `raw/master.log` to understand stage order.

Do not use it as a substitute for process streams.

### 39.4 Aggregate reproduction

Delete only a copy of an aggregate, rebuild it, and compare.

The individual sources should be sufficient.

---

# 40. Debugging CLI behavior

Inspect:

```text
app/main_cli.py
bootstrap
exit-code mapper
```

when:

- CLI returns zero despite failures;
- runtime exception returns validation-failure code;
- parser defaults differ from GUI;
- printed paths differ from `RunResult`;
- legacy modes remain visible;
- stderr and stdout are used incorrectly.

### 40.1 Exit-code categories

Expected conceptual categories:

```text
0 = OK
1 = validation FAIL
2 = invocation/configuration error
3 = framework/runtime ERROR
```

The exact mapping is owned by `EXIT_CODES.md`.

### 40.2 Stream use

- normal concise result: stdout;
- invocation error: stderr;
- framework exception: stderr;
- artifact paths may be stdout when command succeeds.

### 40.3 CLI tests

Mock:

```text
parse_args
build_run_config
run_audit
print_run_summary
```

Test `RunResult` statuses independently from exceptions.

### 40.4 Direct invocation

Prefer:

```powershell
python -m app.main_cli
```

over executing a module file from an arbitrary working directory.

This tests package imports correctly.

---

# 41. Debugging GUI behavior

Inspect:

```text
app/main_gui.py
app/gui/main_window.py
app/gui/validators.py
worker/controller
state manager
```

when:

- window freezes;
- returned `FAIL` appears successful;
- controls stay disabled;
- worker leaks;
- closing during a run hangs;
- state is not saved;
- last-run pointers disappear;
- GUI differs from CLI;
- exceptions are hidden.

### 41.1 GUI-thread rule

Only the GUI thread updates widgets.

External GF execution and broad filesystem work run in a worker.

### 41.2 Worker contract

The GUI uses a worker object moved to `QThread`, with signals for:

```text
started
finished
failed
```

The interface exposes structured progress and cancellation.

### 41.3 Returned failure versus exception

A normal validation `FAIL` should arrive through `finished(RunResult)`.

An unhandled framework defect may arrive through `failed`.

Do not display every `finished` result as success.

### 41.4 Running-state cleanup

Use a `finally`-equivalent controller path to:

```text
reenable widgets
clear worker reference
clear thread reference
set is_running false
preserve partial/last result
```

### 41.5 Last completed run

Starting a new run must not clear the last completed run pointers before the new run finalizes.

### 41.6 GUI/CLI equivalence

Build equivalent requests in tests and compare normalized `RunConfig`.

---

# 42. Debugging GUI startup crashes

Use a terminal:

```powershell
python -m app.main_gui
```

Enable Python fault reporting:

```powershell
$env:PYTHONFAULTHANDLER = "1"
python -m app.main_gui
```

Check:

```text
PySide6 import
plugin loading
current interpreter
application state JSON
project.toml
window construction
signal connection
resource files
top-level exception hook
```

A malformed state file should not prevent startup.

Preserve it as a fixture.

---

# 43. Debugging GUI freezes

Possible causes:

- GF execution on GUI thread;
- broad file selection on GUI thread;
- synchronous manifest verification;
- blocking `wait()` without processing events;
- worker signal connected to heavy slot;
- unbounded activity-log rendering;
- process output collected through blocking GUI callbacks.

### 43.1 Identify thread

Temporarily log:

```python
from PySide6.QtCore import QThread
print(QThread.currentThread())
```

Do not leave noisy thread prints in production.

### 43.2 Reduce rendering

Test with activity updates disabled.

If freeze disappears, inspect:

- update frequency;
- widget line count;
- string size;
- queued signal backlog.

Batch progress updates.

---

# 44. Debugging cancellation

Inspect cancellation when:

- Cancel does nothing;
- active GF process survives;
- cancellation becomes timeout;
- result becomes `OK`;
- worker thread never exits;
- partial evidence disappears.

### 44.1 Cancellation chain

```text
GUI/CLI signal
→ cancellation token
→ orchestration stops scheduling
→ active process termination
→ stream capture completes
→ result records cancelled
→ finalization preserves evidence
→ UI returns idle
```

### 44.2 Test with fake process

Use a fake process that:

- writes one line;
- spawns a child;
- sleeps;
- responds or does not respond to termination.

Verify both parent and owned child behavior.

### 44.3 Distinct state

Expected:

```text
execution_state = cancelled
overall_status != OK
```

Do not map cancellation to a successful `SKIPPED` run.

---

# 45. Debugging Windows-specific failures

Windows-specific symptoms include:

- paths with spaces fail;
- executable launches manually but not from Python;
- child process remains after timeout;
- batch launcher changes working directory;
- long paths fail;
- reserved filenames collide;
- antivirus quarantines temporary executables;
- CRLF affects comparisons;
- console encoding differs.

### 45.1 Always record

```text
Windows version
Python architecture
Python executable
GF executable path
working directory
command list
environment overrides
path lengths
```

### 45.2 Batch launcher parity

A `.bat` launcher must not add hidden semantics.

Compare:

```powershell
launch_gui.bat
python -m app.main_gui
```

and:

```powershell
launch_cli.bat
python -m app.main_cli
```

Resolved configuration should be equivalent.

### 45.3 Process tree

Windows termination may require a process group or job-object strategy.

Do not assume terminating the parent removes children.

### 45.4 Reserved names

Safe-key tests should include:

```text
CON
PRN
AUX
NUL
COM1
LPT1
```

and trailing spaces/dots.

---

# 46. Debugging encoding and Unicode

Inspect encoding when:

- accented language output is corrupted;
- diagnostics contain replacement characters;
- files fail only on Windows;
- byte hashes differ unexpectedly;
- gold mismatches show invisible changes.

### 46.1 Required encoding

Canonical text:

```text
UTF-8 without BOM
```

Canonical newlines:

```text
LF
```

### 46.2 Inspect bytes

```python
data = path.read_bytes()
print(data[:80])
print(data.decode("utf-8"))
```

### 46.3 Detect invisible differences

```python
for index, (left, right) in enumerate(zip(actual, expected)):
    if left != right:
        print(index, repr(left), repr(right), hex(ord(left)), hex(ord(right)))
        break
```

### 46.4 Unicode normalization

Do not apply NFC/NFD normalization globally unless a documented linguistic policy requires it.

Different code-point sequences may be meaningful evidence.

---

# 47. Debugging schema migration

Inspect migration code when:

- old runs cannot load;
- migration changes original files;
- unknown enum values become known values silently;
- old absolute paths resolve incorrectly;
- legacy top errors disappear;
- language fields remain in app state;
- canonical writers emit aliases.

### 47.1 Migration rule

```text
read legacy
→ construct canonical in memory
→ validate canonical
→ write only through explicit migration command
```

Normal read-only loading must not overwrite legacy input.

### 47.2 Required legacy mappings

Examples:

```text
mode=file → quick
mode=all → diagnostic
ok → files_ok
fail → files_fail
ai_brief_path → ai_ready
legacy SHA-1 → import-only compatibility field
```

### 47.3 Unknown fields

For supported major schemas:

- ignore unknown optional fields when permitted;
- validate required fields;
- never reinterpret unknown enum values;
- do not copy unknown data into new canonical output without policy.

### 47.4 Migration fixture strategy

Keep representative fixtures for:

```text
legacy flat state
legacy flat summary
legacy nested summary
missing optional fields
unknown optional fields
invalid mandatory type
absolute Windows paths
absolute POSIX paths
```

---

# 48. Debugging contract drift

Run:

```text
gf-wordbench contracts check
gf-wordbench contracts check --strict
```

When the checker cannot complete, preserve its evidence and inspect the same contracts manually.

### 48.1 Interfile drift indicators

- consumer reads an undeclared field;
- two modules own the same filename;
- report parses another report;
- GUI bypasses `run_audit`;
- compiler writes reports;
- classifier runs processes;
- `RunPaths` changes without consumer updates;
- status literal appears in one file only;
- GUI and CLI defaults differ;
- active-language identifier appears in framework code.

### 48.2 External-contract drift indicators

- logged command differs from executed command;
- GF path differs between compile and scenarios;
- stdout parsed while stderr ignored;
- no finite timeout;
- expected artifact no longer checked;
- normal run rewrites gold;
- process error reported as source syntax error;
- scenario passes without markers;
- an executable tool runs without an ADR-0013 registry entry;
- project text chooses an executable or interpreter;
- a process result contains `gf-portfolio` registry or aggregation state.

### 48.3 Persisted-schema drift indicators

- shape changes without schema version;
- canonical writer emits legacy alias;
- path becomes absolute unexpectedly;
- array ordering becomes nondeterministic;
- state stores project facts;
- summary is partially written;
- manifest hashes pre-final bytes.

### 48.4 Fix strategy

Update the coordinated change unit:

```text
provider
consumers
models
tests
fixtures
locks
migration
documentation
```

---

# 49. Debugging dependency cycles

Use import analysis when:

- startup fails with partially initialized modules;
- monkeypatch targets disappear;
- models import reports;
- reports import compiler;
- GUI state imports project configuration;
- utility modules import audit models.

### 49.1 Expected directions

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

### 49.2 Prohibited examples

```text
reports → compiler
models → GUI
process_utils → audit models
scanner → compiler
compiler → reports
classifier → process execution
project configuration → GUI state
```

### 49.3 Debugging import cycle

Run:

```powershell
python -X importtime -c "import app.main_cli"
```

and:

```powershell
python -X importtime -c "import app.main_gui"
```

Use output for diagnosis, not as a permanent performance budget.

Move shared immutable types toward lower-level modules.

Do not solve cycles with broad runtime imports unless the dependency direction remains correct.

---

# 50. Debugging tests that pass alone but fail together

Likely causes:

- global mutable state;
- environment variable leakage;
- current-directory changes;
- module-level caches;
- shared temporary paths;
- monkeypatch not restored;
- order-dependent file enumeration;
- time-based run-ID collision;
- lingering child processes;
- Qt application singleton leakage.

### 50.1 Reproduce order

```powershell
python -m pytest tests\test_a.py tests\test_b.py -vv
python -m pytest tests\test_b.py tests\test_a.py -vv
```

### 50.2 Isolation checks

At test end, verify:

```text
cwd restored
environment restored
temporary directory removed
child processes terminated
module globals reset
Qt worker/thread stopped
no output written outside tmp_path
```

### 50.3 Randomized order

If a test-order plugin is adopted, use it as additional evidence.

Do not make it a hidden required tool without documenting it.

---

# 51. Debugging flaky time-based tests

Avoid real sleeps where possible.

Inject:

```text
clock
run-ID generator
timeout controller
timestamp provider
```

### 51.1 Use monotonic time

Durations use a monotonic clock.

Wall-clock timestamps use UTC.

### 51.2 Freeze through dependency injection

Do not monkeypatch every call site independently.

Patch the owner’s clock interface.

### 51.3 Timeout tolerance

Integration tests involving real process timing need bounded tolerance.

They should assert state and containment, not exact milliseconds.

---

# 52. Debugging nondeterministic ordering

Symptoms:

- report diffs change without source change;
- top errors reorder;
- manifest changes;
- file selection changes;
- scenario output comparison flakes.

### 52.1 Canonical orders

```text
file_results: normalized file path
scenario_results: configured scenario order
diff_entries: severity rank then path
top_errors: count descending then message
manifest: artifact path
entrypoints/checkpoints: declared order
unordered inventories: lexical path order
```

### 52.2 Common sources

- sets;
- dictionary construction from filesystem iteration;
- concurrent completion order;
- platform path case behavior;
- locale-aware sort;
- unordered glob results.

Sort at the owner boundary.

Do not sort report-only while leaving `summary.json` unstable.

---

# 53. Debugging performance

First determine whether the issue is:

```text
CPU
disk IO
process startup
GF execution
hashing
report serialization
GUI rendering
historical indexing
```

### 53.1 Measure stage duration

Use pipeline stage timings.

Do not optimize from total duration alone.

### 53.2 Python profiling

For a reproducible CLI operation:

```powershell
python -m cProfile -o profile.pstats -m app.main_cli <arguments>
```

Inspect with a local profiler tool.

Do not commit large profile files.

### 53.3 GF timing

Enable GF CPU statistics only through explicit configuration.

Do not make verbose performance output the default.

### 53.4 Common performance defects

- rereading large logs in every report writer;
- hashing the same file repeatedly;
- scanning excluded files;
- compiling the same module through multiple stages;
- rebuilding aggregates repeatedly;
- loading all historical raw logs;
- sending one GUI signal per output line;
- using unbounded generation scenarios.

### 53.5 Correct optimization boundary

Cache immutable derived values only when:

- cache key is complete;
- invalidation is explicit;
- cache does not replace evidence;
- deterministic tests exist.

---

# 54. Debugging memory growth

Inspect:

- large stream capture in memory;
- aggregate construction through repeated string concatenation;
- GUI activity widgets;
- retained `RunResult` history;
- unbounded detail excerpts;
- Qt signal payloads;
- duplicate raw/report content.

### 54.1 Streaming rule

Large stdout and stderr should be streamed or bounded.

### 54.2 Aggregate writer

Write sections incrementally to a temporary file.

Do not load every log into one in-memory string.

### 54.3 GUI

Cap visible activity lines.

Opening a large log should use a bounded viewer or external editor.

---

# 55. Debugging filesystem permission failures

Test separately:

```text
read project
write output root
create run directory
write temporary file
atomic replace
delete temporary file
open artifact
```

A directory may be writable but atomic replacement may still fail because of:

- antivirus scanning;
- file locks;
- cross-volume temporary path;
- permission inheritance;
- read-only attribute;
- another application holding the file.

Temporary files for atomic replacement should be siblings of the destination.

---

# 56. Debugging report-write failures

The framework should preserve the primary validation result even when a secondary report fails.

Investigate:

```text
which report failed
whether summary.json succeeded
whether master.log recorded the warning
whether terminal overall-status policy changed
whether manifest includes only completed artifacts
whether aggregate generation used partial reports
```

### 56.1 Strict/release behavior

Required report failure is a finalization `ERROR`.

### 56.2 Development behavior

Best-effort may preserve other artifacts with an explicit warning.

### 56.3 Never swallow silently

A broad `except Exception: pass` may be used only as the last effort while another durable error record already exists.

It must not create apparent success.

---

# 57. Debugging unhandled exceptions

Enable full traceback.

CLI:

```powershell
$env:PYTHONFAULTHANDLER = "1"
python -m app.main_cli <arguments>
```

Tests:

```powershell
python -m pytest -x -vv --tb=long
```

### 57.1 Capture context

Record:

```text
exception type
message
traceback
run ID
stage
subject
RunConfig summary
current artifact paths
last lifecycle events
```

### 57.2 Exception translation boundary

Translate exceptions where domain meaning becomes known.

Examples:

- `FileNotFoundError` in executable launch → launch/tool error;
- `TimeoutExpired` in process runner → timeout state;
- `JSONDecodeError` in state loader → state schema/load warning;
- unknown exception in report writer → report/finalization error.

Do not erase the original exception as the cause.

Use exception chaining where appropriate.

---

# 58. Using `pdb`

Insert temporarily:

```python
breakpoint()
```

or run:

```powershell
python -m pytest --pdb -x
```

Useful commands:

```text
p expression
pp object
where
up
down
list
next
step
continue
quit
```

Do not commit unconditional breakpoints.

A deliberate debug flag may enable breakpoints only in local development, but should not be part of normal execution.

---

# 59. Temporary instrumentation

Good temporary instrumentation:

```text
stage boundary
resolved path
operation ID
status transition
collection size
blocker identity
artifact existence
schema version
```

Bad temporary instrumentation:

```text
complete environment
entire source tree
secret arguments
every character processed
large binary payload
unbounded stdout duplication
```

### 59.1 Remove or formalize

Before merging:

- remove temporary prints;
- convert useful diagnostics into structured logging;
- add tests;
- update log reference if new persistent events are introduced.

---

# 60. Assertions and invariant checks

Use assertions in tests and internal impossible-state checks.

Do not use `assert` for user-input validation that must work under optimized Python execution.

Good internal invariants:

```python
assert len(unique_paths) == len(paths)
assert all(path.is_absolute() for path in resolved_paths)
assert result.status in ALLOWED_STATUSES
```

Production input checks should raise typed exceptions with actionable messages.

---

# 61. Typed exceptions

Recommended exception families:

```text
ConfigurationError
ProjectSchemaError
StateLoadError
ToolResolutionError
ProcessLaunchError
ProcessTimeoutError
CancellationError
EvidenceCaptureError
DiagnosticParseError
ArtifactValidationError
ReportWriteError
ManifestValidationError
MigrationError
ContractViolationError
```

The exact hierarchy requires an architectural decision.

Do not introduce many exception classes without distinct handling behavior.

### 61.1 Boundary mapping

Each boundary should define:

```text
exceptions accepted
exceptions translated
exceptions propagated
status produced
evidence preserved
```

---

# 62. Logging during development

Use structured or semi-structured lifecycle logging.

Recommended fields:

```text
timestamp
level
event
stage
subject
operation_id
status
error_kind
artifact_path
```

Do not use message wording as the only machine discriminator.

### 62.1 Logging levels

```text
DEBUG: developer detail
INFO: lifecycle
WARN: recoverable unexpected condition
ERROR: operation/stage error
FATAL: run cannot continue safely
```

### 62.2 Avoid duplicate error logs

An exception should not be logged with full traceback at every layer.

Recommended:

- lower layer adds context and raises;
- boundary owner logs or persists once;
- UI/report renders a bounded view.

---

# 63. Debugging source mutation

Strict runs should detect source changes during validation.

Symptoms:

- fingerprint differs after compile;
- scenario uses newer source than compile;
- reports combine two revisions;
- editor autosave changes a file mid-run.

### 63.1 Investigation

Compare initial and final fingerprints.

Record:

```text
path
initial size/hash
final size/hash
stage when change detected
```

### 63.2 Policy

Checkpoint/release:

```text
overall_status = ERROR
```

Quick mode may warn and recommend rerun, but must not claim a coherent release snapshot.

---

# 64. Debugging security failures

Inspect when:

- project paths escape approved roots;
- shell metacharacters affect execution;
- `.gfs` uses prohibited system commands;
- reports render unescaped content;
- secrets appear in state or logs;
- symlinks escape run/project roots.

### 64.1 Command injection

Verify process API receives:

```text
executable field
argument list
shell=False
```

### 64.2 Scenario trust

Scan scenarios for prohibited shell-escape features according to policy.

Do not execute an untrusted scenario merely to determine whether it is safe.

### 64.3 Diagnostic-tool registry

For every optional executable tool, verify:

```text
static registry entry exists
tool ID is stable
executable resolution follows the entry
arguments match allowed templates
working directory is contained
timeout and output limits are finite
mutability and network policy are enforced
evidence role is declared
AI output remains optional and non-normative
```

Arbitrary user-supplied commands and dynamically loaded executable plugins are
prohibited.

### 64.4 Redaction test

Insert a fake secret into a controlled test environment.

Assert it does not appear in:

```text
state
summary
manifest
master.log
aggregate logs
GUI error
```

---

# 65. Debugging cleanup and retention

Cleanup code must not participate in normal run semantics.

Inspect when:

- active run is deleted;
- latest completed run disappears;
- previous-run baseline is removed unexpectedly;
- cleanup follows symlinks;
- manifest and retained files disagree.

Test:

```text
dry run
age filters
status filters
protected latest release
incomplete runs
symlink rejection
locked files
partial deletion recovery
```

Never debug cleanup against the only copy of release evidence.

---

# 66. Debugging packaging and launchers

Inspect when:

- module imports work from source but not packaged form;
- launcher uses wrong Python;
- GUI starts with another working directory;
- resources are missing;
- version metadata differs.

Record:

```text
sys.executable
sys.path
package __file__
cwd
launcher content
environment activation
installed package version
```

Launchers must delegate.

They must not contain hidden GF paths or validation options.

---

# 67. Test pyramid

Use four levels.

### 67.1 Pure unit tests

No filesystem or process unless through tiny temporary fixtures.

### 67.2 Filesystem/process contract tests

Use `tmp_path` and fake executables.

### 67.3 Real-GF integration tests

Use a tiny fixture grammar.

Mark separately.

### 67.4 End-to-end tests

Exercise CLI and selected GUI flows.

Do not rely on the active language project for framework correctness.

---

# 68. Writing a regression test

A regression test should:

1. fail on the pre-fix implementation;
2. reproduce the actual contract break;
3. use the narrowest public boundary;
4. assert structured behavior;
5. inspect evidence when relevant;
6. avoid implementation-private assumptions;
7. pass consistently across supported platforms or be marked platform-specific;
8. name the user-visible or contract symptom.

Bad regression test:

```text
assert private helper returns the new hard-coded string
```

Good regression test:

```text
a timed-out fake GF process returns execution_state=timed_out,
validation_status=ERROR, preserves partial stdout, and terminates its child
```

---

# 69. Tests by framework zone

## 69.1 Configuration

```text
valid project
missing project
legacy state
blank paths
mode migration
GUI/CLI equivalence
```

## 69.2 Selection

```text
include/exclude
target
checkpoint
deterministic order
containment
```

## 69.3 Scanner

```text
comments
strings
multiline blocks
Unicode
line numbers
```

## 69.4 Process

```text
stdout
stderr
exit
timeout
cancel
child process
encoding
path with spaces
```

## 69.5 Compiler

```text
command args
GF path
artifact paths
no-compile
CPU flag
diagnostic streams
```

## 69.6 Classifier

```text
ok
direct
downstream
ambiguous
noise
skipped
cycles
```

## 69.7 Scenarios

```text
markers
ignored command
timeout
normalization
gold match/mismatch
```

## 69.8 Reports

```text
empty result
FAIL
ERROR
Unicode
missing optional artifact
no process execution
```

## 69.9 Schemas

```text
round trip
unknown optional field
unknown enum
atomic write
legacy migration
deterministic order
```

## 69.10 GUI

```text
worker lifecycle
returned FAIL
exception
cancel
state
artifact opening
CLI equivalence
```

---

# 70. Useful focused commands

Compile all Python sources:

```powershell
python -m compileall app tests
```

Run all tests:

```powershell
python -m pytest
```

Run framework core tests:

```powershell
python -m pytest -k "audit_core or result_model or bootstrap" -vv
```

Run external-process tests:

```powershell
python -m pytest -k "process or compiler or timeout" -vv
```

Run diagnostic tests:

```powershell
python -m pytest -k "classifier or diagnostic" -vv
```

Run report/schema tests:

```powershell
python -m pytest -k "report or summary or manifest or schema" -vv
```

Run GUI tests:

```powershell
python -m pytest -k "gui or main_window or state" -vv
```

Use the repository's canonical test paths.

---

# 71. Static quality tools

When configured by the project, run:

```powershell
python -m ruff check .
python -m mypy app
```

Do not claim these checks ran when the tools are not installed.

A missing optional developer tool is not a framework runtime defect.

Document installation in `DEVELOPMENT_SETUP.md`.

---

# 72. Debugging with a clean environment

To detect hidden dependencies:

1. create a fresh virtual environment;
2. install only declared dependencies;
3. run unit tests;
4. run fake-process contract tests;
5. configure GF explicitly;
6. run real-GF integration tests;
7. launch CLI and GUI.

A test that passes only because of:

```text
global GF_LIB_PATH
user site packages
IDE working directory
undeclared executable on PATH
stale run files
```

is not isolated.

---

# 73. Debugging GF Audit compatibility

GF Audit compatibility is a boundary adapter, not a second architecture.

Compatibility readers and adapters may accept:

```text
all/file mode aliases
legacy flat application state
legacy project-owned GUI fields
FAIL-only file totals
combined compile/release assumptions
legacy report aggregates
legacy summary shapes and status aliases
```

Canonical writers and runtime models emit only Wordbench contracts.

### 73.1 Compatibility debugging rules

When a legacy asset or caller behaves incorrectly:

1. preserve the original input unchanged;
2. identify the registered legacy shape or alias;
3. convert it through one migration or compatibility owner;
4. validate the canonical result;
5. record warnings and semantic losses;
6. ensure the canonical writer never emits the legacy form;
7. add a fixture and round-trip or migration test;
8. keep process execution, scenarios, reports, and schemas on their canonical owners.

Compatibility code must not:

- duplicate the process runner;
- define a second validation pipeline;
- silently convert unknown values to success;
- mutate source assets during read-only loading;
- bypass one-project-per-workspace rules;
- introduce `gf-portfolio` runtime dependencies;
- require coding-progress status transitions in documentation.

### 73.2 Do not preserve legacy bugs for compatibility

Compatibility means reading old data or accepting registered old input aliases.

It does not require canonical writers to emit old values, preserve incorrect
semantics, or retain unsafe behavior.

---

# 74. Common debugging traps

### Trap 1 — Fixing the report

Symptom appears in `summary.md`.

Actual bug is in `RunResult`.

### Trap 2 — Updating gold

Mismatch comes from a normalizer regression.

### Trap 3 — Blaming the active language

GF command used the wrong working directory.

### Trap 4 — Treating timeout as direct

Timeout proves infrastructure/execution failure, not source causality.

### Trap 5 — Testing only stdout

GF emitted the useful diagnostic on stderr.

### Trap 6 — Reproducing manually with a different command

The manual test omits the failing GF path or output option.

### Trap 7 — Deleting corrupt state

Startup works again, but migration remains broken.

### Trap 8 — Adding another path builder

One operation works while compile/scenario drift grows.

### Trap 9 — Using broad exception swallowing

The visible crash disappears and evidence becomes untrustworthy.

### Trap 10 — Depending on the active project

Framework tests fail after changing language.

### Trap 11 — Sorting only in reports

Persisted JSON remains nondeterministic.

### Trap 12 — Mutating a finalized artifact

Manifest hashes fail immediately.

### Trap 13 — Treating worker completion as validation success

A structured `FAIL` is displayed as success.

### Trap 14 — Running Qt work from worker thread

Intermittent GUI crashes or freezes appear.

### Trap 15 — Using local time for identity

Runs collide or sort incorrectly across timezone changes.

---

# 75. Incident-severity guidance

### Severity 1 — Integrity or destructive defect

Examples:

- normal run modifies source or gold;
- run overwrites another run;
- manifest claims incorrect hashes;
- secrets written to artifacts;
- migration overwrites unreadable legacy data;
- cleanup deletes protected release evidence.

Action:

```text
stop affected workflow
preserve evidence
add containment fix
review all related boundaries
```

### Severity 2 — Incorrect validation decision

Examples:

- `FAIL` reported as `OK`;
- required skipped stage accepted;
- timeout reported as language failure;
- wrong project compared;
- missing PGF accepted.

### Severity 3 — Evidence or diagnostic defect

Examples:

- stderr missing;
- first error wrong;
- blocker missing;
- report path broken;
- aggregate stale.

### Severity 4 — Usability or performance defect

Examples:

- GUI layout issue;
- slow historical indexing;
- unclear warning;
- redundant output.

Severity does not replace issue priority.

---

# 76. Bug-report template

Use:

```markdown
# Framework Bug

## Summary

<one precise sentence>

## Expected behavior

<structured expected result>

## Actual behavior

<structured actual result>

## Reproduction

1. ...
2. ...
3. ...

## Environment

- GF Wordbench revision:
- Python:
- OS:
- GF:
- RGL:
- Invocation surface: CLI / GUI / API

## Resolved configuration

<redacted relevant fields>

## Evidence

- Run directory:
- summary.json:
- master.log:
- stdout:
- stderr:
- other artifact:

## Status fields

- validation_status:
- execution_state:
- error_kind:
- diagnostic_class:

## First incorrect boundary

<suspected provider and consumer>

## Minimal fixture

<path or attachment>

## Regression test

<regression test name>
```

---

# 77. Root-cause analysis template

```markdown
# Root Cause Analysis

## Incident

<identifier and date>

## User-visible impact

<what became incorrect or unavailable>

## Detection

<how it was found>

## Timeline

<ordered UTC events>

## First incorrect fact

<value or behavior>

## Owning component

<provider>

## Affected consumers

<list>

## Why existing tests missed it

<gap>

## Correction

<owner-level change>

## Compatibility and migration

<impact>

## New tests

<list>

## Documentation/lock changes

<list>

## Follow-up actions

<bounded actions>
```

The root cause is not “the report displayed the wrong value” when an earlier model produced it incorrectly.

---

# 78. Fix review checklist

```text
[ ] Original failing evidence preserved
[ ] Minimal reproduction exists
[ ] First incorrect boundary identified
[ ] Owner-level fix applied
[ ] No unrelated behavior changed
[ ] Regression test fails before fix
[ ] Regression test passes after fix
[ ] Focused tests pass
[ ] Complete tests pass
[ ] Python compileall passes
[ ] Real-GF test run when relevant
[ ] Windows path test run when relevant
[ ] Raw evidence preserved correctly
[ ] Status mapping reviewed
[ ] GUI/CLI equivalence reviewed
[ ] Schema version reviewed
[ ] Migration reviewed
[ ] Manifest reviewed
[ ] Locks reviewed
[ ] Documentation updated without coding-progress labels
[ ] `gf-portfolio` boundary preserved
[ ] ADR-0013 registry reviewed when an executable tool is affected
[ ] Temporary instrumentation removed
```

---

# 79. Release-debugging checklist

Before declaring a framework release ready:

```text
[ ] No known Severity 1 defect
[ ] Required tests pass
[ ] Contract tests pass
[ ] Schema round trips pass
[ ] Migration fixtures pass
[ ] Fake-process timeout/cancel tests pass
[ ] Real-GF integration passes on supported baseline
[ ] CLI exit codes verified
[ ] GUI FAIL/ERROR rendering verified
[ ] Paths with spaces verified
[ ] Required artifacts manifest correctly
[ ] Published hashes verify
[ ] Normal validation does not alter gold
[ ] No report launches GF
[ ] No active-language identifier in framework defaults
[ ] No Wordbench runtime dependency on `gf-portfolio`
[ ] Every optional executable is in the static diagnostic-tool registry
[ ] Canonical writers emit no legacy aliases
[ ] Documentation links resolve
```

---

# 80. Anti-patterns prohibited in fixes

Do not merge a fix that:

- catches `Exception` and returns `OK`;
- changes a public model without updating consumers;
- adds a status literal in one module;
- reconstructs an owned artifact path;
- edits raw evidence;
- changes normalization without gold review;
- changes a GF command in one caller;
- relies on shell command concatenation;
- removes timeout;
- parses only stdout;
- makes tests depend on developer-global GF configuration;
- stores project facts in GUI state;
- silently migrates in place during read-only load;
- suppresses manifest failure;
- rewrites a failed run directory;
- uses current working directory implicitly;
- leaves unconditional debug prints or breakpoints;
- weakens an assertion merely to make the suite pass;
- marks an unknown cause as direct;
- adds an executable command outside the static diagnostic-tool registry;
- allows project text to select an executable or interpreter;
- introduces a GF Wordbench runtime dependency on `gf-portfolio`;
- adds coding-progress labels to normative documentation.

---

# 81. Test structure

```text
tests/
├── unit/
│   ├── config/
│   ├── selection/
│   ├── scanner/
│   ├── diagnostics/
│   ├── classifier/
│   ├── results/
│   └── reports/
├── contracts/
│   ├── interfile/
│   ├── external_tools/
│   ├── diagnostic_tool_registry/
│   ├── schemas/
│   └── gui_cli/
├── integration/
│   ├── fake_process/
│   ├── real_gf/
│   ├── cli/
│   └── gui/
├── migrations/
├── fixtures/
│   ├── projects/
│   ├── gf_diagnostics/
│   ├── summaries/
│   ├── states/
│   └── processes/
└── smoke/
```

Tests are organized by responsibility and test level. Repository-specific subdirectories may vary, but discoverability, fixtures, markers, and CI commands remain stable.

---

# 82. Debugging documentation contradictions

When two documents conflict:

1. identify the accepted ADRs and specialized locks that apply;
2. apply `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`;
3. identify the document that owns the specific contract;
4. inspect code, tests, schemas, and artifacts for the actual violation;
5. update the owner contract and every affected consumer together;
6. add or update a contract test;
7. record any compatibility or migration effect;
8. update the documentation correction ledger during integration.

Do not resolve a contradiction locally in an overview, report, GUI label, or
single caller.

Examples:

```text
lock says ERROR, code emits FAIL
schema says run-relative, report emits absolute
GUI and CLI build different RunConfig values
raw-log reference says operational-only aggregate, writer embeds reports
ADR-0013 requires a static registry, adapter launches an arbitrary command
```

A contradiction remains a coordinated contract defect until every owner and
consumer agrees.

---

# 83. Debugging without real GF

Most framework defects can be isolated without GF.

Use fake process results for:

```text
command construction
timeout
stream capture
status mapping
artifact detection
diagnostic parsing
classification
reports
manifest
GUI rendering
```

Use real GF only for:

```text
actual command compatibility
native diagnostic formats
GF path behavior
PGF production
shell scenario behavior
parse/linearize/generation semantics
```

This keeps tests fast and deterministic.

---

# 84. Debugging with real GF

When real GF is required:

1. use a tiny fixture project;
2. resolve an explicit executable;
3. record version;
4. use an isolated output root;
5. avoid user-global GF path dependencies;
6. preserve raw streams;
7. mark the test as integration;
8. skip with a clear infrastructure reason when GF is unavailable;
9. do not convert missing GF into a passing test;
10. run on supported Windows baseline before release.

---

# 85. Ownership summary

```text
bootstrap/configuration bug
→ bootstrap/config owner

incorrect source set
→ selector owner

incorrect heuristic finding
→ scanner owner

incorrect command
→ GF request builder

launch/timeout/stream defect
→ process runner

incorrect GF interpretation
→ diagnostic parser

incorrect causal relationship
→ classifier

incorrect runtime assertion
→ scenario/marker owner

incorrect stable output
→ normalizer

incorrect expected comparison
→ gold comparator

incorrect release artifact
→ PGF builder/artifact verifier

incorrect prior-run relation
→ diff owner

incorrect counts/status
→ result model

incorrect report rendering
→ report writer

incorrect artifact integrity
→ manifest owner

incorrect GUI presentation
→ GUI controller/view

incorrect CLI code
→ CLI adapter

incorrect historical compatibility
→ migration/schema owner

incorrect optional-tool registration or policy
→ diagnostics registry owner

incorrect Portfolio interoperability artifact
→ reporting public-artifact owner
```

Escalate upward only when the lower owner is correct.

---

# 86. Debugging workflow

```text
observe
→ preserve
→ classify
→ reproduce
→ reduce
→ compare raw and structured evidence
→ locate first incorrect boundary
→ write failing test
→ fix owner
→ verify focused behavior
→ verify all consumers
→ verify contracts and schemas
→ compare artifacts
→ document
```

---

# 87. Core rule

A framework defect is corrected only when the system’s evidence, models, execution, reports, and interfaces agree again.

> Debug GF Wordbench from the originating boundary outward: preserve the raw event, prove the first incorrect transformation, repair the component that owns that transformation, and lock the correction with a regression test.

Do not make the visible symptom quieter.

Make the underlying contract correct.
