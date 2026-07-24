# GF Wordbench — GF Compilation

**Document ID:** `GF-WB-GF-COMPILATION`  
**Status:** Normative  
**Applies to:** GF source-module compilation, `.gfo` artifact verification, compile evidence and structured compile results  
**Owner:** GF Wordbench maintainers  
**Document version:** `2.0.0`  
**Last reviewed:** `2026-07-24`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related locks:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Purpose

This document defines how GF Wordbench compiles Grammatical Framework source modules and interprets compilation evidence.

It governs this path:

```text
GF source target
    → validated compile request
    → resolved GF executable and search path
    → external GF process
    → raw stdout and stderr
    → `.gfo` artifact verification
    → structured compile result
    → file result and diagnostics
```

It defines:

- module compilation versus PGF construction;
- canonical command construction;
- target and path validation;
- working-directory and output-directory rules;
- timeout, cancellation and process behavior;
- raw evidence requirements;
- diagnostic parsing boundaries;
- success, failure, error and skipped semantics;
- stale-artifact protection;
- mode-specific compilation behavior;
- testing and anti-drift requirements.

It does not define:

- static scan rules;
- causal dependency classification;
- native `.gfs` scenario execution;
- PGF release construction;
- report formatting;
- project-specific module architecture.

---

## 2. Product boundary

GF Wordbench compiles modules for one resolved active project and one normative project target per run.

Compilation must not:

- enumerate or execute several active projects;
- use a Portfolio workspace registry;
- depend on `gf-portfolio`;
- import Portfolio code or private schemas;
- report cross-workspace compilation readiness.

`gf-portfolio` may consume public versioned Wordbench run artifacts. It does not participate in Wordbench compilation.

---

## 3. Authority boundary

### 3.1 GF authority

Grammatical Framework is authoritative for:

- GF syntax;
- name and module resolution;
- type checking;
- source-to-object compilation;
- `.gfo` production;
- GF diagnostic text;
- GF process exit behavior.

### 3.2 Wordbench authority

GF Wordbench is authoritative for:

- selecting the compilation target;
- resolving the GF executable;
- resolving the ordered GF search path;
- constructing the argument vector;
- choosing the working directory;
- preparing run-owned output paths;
- applying timeout and cancellation policy;
- capturing stdout and stderr separately;
- recording process evidence;
- verifying required artifacts;
- mapping evidence into structured results;
- passing results to diagnostics, comparison and reporting.

### 3.3 Prohibited duplication

GF Wordbench must not implement a competing:

- GF parser;
- GF type checker;
- GF module resolver;
- GF optimizer;
- `.gfo` serializer;
- interpretation of GF source semantics.

Static findings are Wordbench prechecks. They are not compilation truth.

---

## 4. Terminology

**Compilation target**  
The explicitly selected `.gf` source file for one compile operation.

**Dependency**  
A GF module required directly or transitively by the target.

**Object artifact**  
A GF object file:

```text
<ModuleName>.gfo
```

**Compile evidence**  
The executable, arguments, working directory, GF version, process result, raw streams, artifact checks and source identity for one attempt.

**Compile result**  
The structured result returned by the compilation component.

**Module compilation**  
Compilation of a `.gf` source module and required dependencies into `.gfo` files.

**PGF construction**  
Construction of a `.pgf` runtime grammar from configured release entrypoints.

**Fatal diagnostic**  
A GF diagnostic that establishes compilation failure even when process exit behavior is unusual.

**Artifact freshness**  
Evidence that an artifact belongs to the current compile operation and source state rather than an earlier run.

---

## 5. Compilation and PGF construction

GF compilation products are distinct:

```text
*.gf
    → *.gfo
    → *.pgf
```

### 5.1 Module compilation

Purpose:

```text
validate one source module and produce current `.gfo` evidence
```

Canonical command shape:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

### 5.2 PGF construction

Purpose:

```text
build the runtime grammar from configured release entrypoints
```

Canonical command shape:

```text
<gf> -make -optimize-pgf <path-options> <entrypoint-1> [<entrypoint-N>...]
```

PGF construction is governed by:

```text
docs/gf/GF_PGF_BUILD.md
```

### 5.3 Separation rule

GF Wordbench must not:

- treat `.gfo` compilation as proof that a `.pgf` can be built;
- use `-make` as the normal per-file compilation command;
- classify a PGF-linking failure as an ordinary per-file compile result;
- declare release readiness from file compilation alone;
- overwrite release artifacts during ordinary module validation.

---

## 6. Canonical module-compilation command

### 6.1 Form

```text
<gf-executable>
    -batch
    -s
    <resolved-path-options>
    <validated-artifact-options>
    <source-file>
```

Rendered:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

The source-file argument is last.

### 6.2 Argument representation

Executable and arguments are separate values:

```python
executable: Path
args: list[str]
```

Example:

```python
executable = Path("C:/Program Files/GF/bin/gf.exe")

args = [
    "-batch",
    "-s",
    "--path=<resolved-gf-path>",
    "--gfo-dir=<run-gfo-dir>",
    "lib/src/example/GrammarX.gf",
]
```

Normal compilation uses no command shell.

```text
shell = false
```

The rendered command is evidence for logs and reports. It is not re-executed as a shell string.

### 6.3 `-batch`

`-batch` performs non-interactive source compilation.

It is required for canonical per-file compilation.

### 6.4 `-s`

`-s` suppresses non-error compiler chatter.

| Mode | Policy |
|---|---|
| `quick` | required |
| `checkpoint` | required |
| `release` | required for module-compilation stages |
| `diagnostic` | may be omitted for intentionally verbose evidence |

The exact resolved argument vector is always recorded.

### 6.5 Search-path options

The compiler consumes the ordered path produced by the GF path resolver.

Conceptual option:

```text
--path=<resolved-gf-path>
```

Additional library-root options may be used only when the selected GF version supports them and the external-tool contract defines them.

The compiler does not reconstruct project architecture independently.

### 6.6 Artifact options

Object artifacts are written into the current run:

```text
artifacts/gfo/
```

Supported GF options may include:

```text
--gfo-dir=<run-gfo-dir>
--output-dir=<run-output-dir>
```

An option is used only when:

1. the selected GF version supports it;
2. the command contract defines it;
3. integration tests cover it;
4. the destination is run-owned;
5. artifact verification uses the resolved destination.

Unsupported flags are rejected rather than passed optimistically.

### 6.7 Optional process metrics

Optional CPU or timing flags require explicit run configuration.

They:

- do not change validation semantics;
- remain part of raw evidence;
- may be removed from deterministic comparison material through documented normalization.

---

## 7. Compile request

Each request identifies:

```text
source file
active project identity
project root
resolved GF executable
resolved GF version
ordered GF search path
working directory
timeout
run-owned stdout path
run-owned stderr path
run-owned artifact roots
verbosity policy
artifact-verification policy
```

The request is typed and structured. It is not a shell command string.

---

## 8. Target validation

Before GF is launched, the compiler verifies that the target:

```text
[ ] exists
[ ] is a regular file
[ ] has the `.gf` suffix
[ ] belongs to the active project or an explicitly approved source root
[ ] is included by the resolved file-selection policy
[ ] contains no prohibited control characters
[ ] can be passed safely as one process argument
```

The compiler must not:

- compile an excluded file accidentally;
- follow an unapproved path outside allowed roots;
- replace a missing file with another file sharing its basename;
- derive a target from report prose;
- modify the source before or after compilation.

A pre-launch target failure is a configuration or I/O error. No process success or artifact is fabricated.

---

## 9. Module identity

GF module identity and filename should agree.

Example:

```text
file:   GrammarX.gf
module: GrammarX
```

Module-name extraction has one owner.

The compiler:

- may receive an expected module name;
- preserves the selected path;
- does not infer a replacement name from diagnostic prose;
- verifies the expected `.gfo` name when artifact checks require it.

A mismatch is reported as project or compilation evidence. Artifacts are not renamed silently.

---

## 10. GF executable resolution

The resolved run configuration contains the exact executable used.

Resolution precedence is defined by environment and configuration documentation. It may include:

1. explicit CLI or GUI selection;
2. environment configuration;
3. validated application configuration;
4. documented `PATH` lookup;
5. explicit failure.

After resolution:

- the executable does not change silently;
- the resolved path is recorded;
- paths containing spaces are supported;
- a directory is not accepted as an executable;
- launchability errors remain distinct from GF source failures.

Compilation and version probing use the same resolved executable.

---

## 11. GF version evidence

Version probing is a separate process request:

```text
<gf-executable> --version
```

Canonical evidence paths:

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

The probed version governs optional command capabilities.

Unknown or incompatible output is reported explicitly. It is not silently treated as supported.

---

## 12. GF search path

The compiler receives an already resolved ordered search path.

The path may include:

- active project source roots;
- project resource roots;
- configured RGL roots;
- required RGL subdirectories;
- documented external aliases.

Invariants:

- order is deterministic;
- duplicate effective paths are removed without changing first occurrence;
- required project roots are present;
- values are normalized for the selected platform and GF version;
- the resolved value is recorded;
- CLI and GUI resolve equivalent inputs identically;
- resolution does not depend on process launch directory.

The compiler does not guess missing directories after GF reports a module-resolution failure.

---

## 13. Working directory

Each process uses an explicit working directory:

```text
resolved active-project root
```

The working directory does not depend on:

- terminal location;
- IDE defaults;
- GUI launch location;
- shortcut location;
- package installation directory;
- previous process execution.

It is recorded as compile evidence.

---

## 14. Run-owned directories

Canonical paths:

```text
run_<run-id>/raw/compile/
run_<run-id>/artifacts/gfo/
run_<run-id>/artifacts/out/
```

Required directories are prepared before launch.

Failure to prepare them is an I/O error.

The compiler must not fall back to source directories or another run directory.

---

## 15. Evidence filenames

Each target receives deterministic raw stream paths:

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
```

The safe key derives from the project-relative path, not only the basename.

Example:

```text
lib/src/example/GrammarX.gf
```

may map to:

```text
lib__src__example__GrammarX.gf.out.txt
lib__src__example__GrammarX.gf.err.txt
```

The encoding algorithm is:

- deterministic;
- unique for distinct project-relative paths;
- safe on supported platforms;
- stable for a schema version;
- independent of localized report text.

---

## 16. Process execution

Compilation uses the common external-process port and adapter.

Conceptual request:

```python
process_result = run_process_with_timeout(
    executable=gf_executable,
    args=compile_args,
    cwd=project_root,
    stdout_path=stdout_path,
    stderr_path=stderr_path,
    timeout_sec=compile_timeout_sec,
)
```

The process adapter owns:

- launch;
- timeout enforcement;
- cancellation and termination;
- exit-code capture;
- duration;
- stdout capture;
- stderr capture;
- launch-failure representation.

It does not:

- parse GF diagnostics;
- assign causal classes;
- know validation-mode policy;
- generate reports;
- alter project sources.

---

## 17. Standard streams

Stdout and stderr are captured separately.

Required evidence:

```text
stdout_path
stderr_path
```

Rules:

- both streams are retained after a launched process;
- non-zero exit does not discard either stream;
- timeout and cancellation preserve captured partial output;
- parsing occurs only after raw evidence has been written;
- parser failure does not replace or destroy raw evidence;
- decoding behavior is deterministic and documented.

A combined diagnostic view may be derived in memory, but it does not replace the separate raw files.

Unless the process adapter captures an ordered combined stream, no component claims exact cross-stream interleaving.

---

## 18. Timeout

Every compilation has a positive timeout or an explicit run-budget allocation.

On timeout:

```text
validation_status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
```

The process adapter attempts documented process-tree containment, preserves partial evidence and records cleanup failures separately.

Timeout is an execution condition, not a direct or downstream causal class.

---

## 19. Cancellation

Cancellation is distinct from timeout.

The result records:

```text
execution_state = cancelled
```

The run policy determines whether unstarted or interrupted validations are `ERROR` or `SKIPPED`.

Cancellation is not introduced as a separate validation-status value.

---

## 20. Launch failure

Launch failures include:

- executable not found;
- permission denied;
- executable path is a directory;
- invalid working directory;
- invalid process arguments;
- platform launch errors.

Typical result:

```text
validation_status = ERROR
execution_state = launch_failed
error_kind = TOOL, CONFIG or IO
```

Launch failure remains distinct from GF returning a non-zero exit code.

---

## 21. Exit interpretation

Exit code is necessary evidence, but not the only success condition.

### 21.1 Zero exit

A zero exit permits success only when:

- the process launched and completed;
- no timeout or cancellation occurred;
- no recognized fatal diagnostic exists;
- required artifact verification passes.

### 21.2 Non-zero exit

A non-zero exit produces `FAIL` when GF executed correctly and rejected the source or dependency graph.

It produces `ERROR` when the evidence indicates infrastructure, command-contract or interpretation failure.

### 21.3 Zero exit with fatal diagnostic

A recognized fatal diagnostic prevents `OK`, even if the exit code is zero.

### 21.4 Non-zero exit without usable diagnostic

The result remains a failure.

Example:

```text
error_kind = OTHER
first_error = "Non-zero exit with no recognized diagnostic"
```

The exact exit code remains preserved.

---

## 22. Result semantics

### 22.1 Successful compilation

Success requires:

```text
[ ] target validation passed
[ ] executable resolved
[ ] run-owned directories prepared
[ ] process launched
[ ] process completed
[ ] no timeout
[ ] no cancellation
[ ] successful exit
[ ] no fatal diagnostic
[ ] required artifact verification passed
[ ] evidence paths are valid
[ ] structured result is coherent
```

Result:

```text
validation_status = OK
diagnostic_class = ok
error_kind = OK
```

### 22.2 GF compilation failure

A GF source or dependency failure normally produces:

```text
validation_status = FAIL
execution_state = completed
error_kind = SYNTAX, TYPE, INTERNAL or OTHER
```

The compiler does not decide whether the failure is direct, downstream or ambiguous.

### 22.3 Execution or contract error

Examples:

- launch failure;
- timeout;
- output-directory failure;
- unsupported option;
- unreadable evidence;
- artifact-contract failure;
- invalid configuration.

Result:

```text
validation_status = ERROR
```

### 22.4 Skipped compilation

Compilation is skipped only through explicit mode or run policy.

Result:

```text
validation_status = SKIPPED
diagnostic_class = skipped
```

A skipped operation has no fabricated process exit and no fabricated `.gfo`.

---

## 23. Diagnostic parsing

Diagnostic parsing transforms captured GF evidence into a compact structured summary.

It may assign error kinds such as:

```text
OK
TYPE
SYNTAX
INTERNAL
TIMEOUT
CONFIG
IO
TOOL
OTHER
```

`SCRIPT` belongs to scenario execution, not ordinary module compilation.

Parser input includes:

```text
stdout
stderr
exit code
execution state
duration
evidence paths
```

Parser output includes:

```text
error kind
first error
supplementary detail
structured source location when available
```

Invariants:

- raw evidence remains unchanged;
- parsing is deterministic;
- specific rules precede fallbacks;
- unmatched failure evidence remains visible;
- parser failure cannot convert failure to success;
- diagnostic parsing does not assign causal ownership;
- reports do not maintain independent parser rules.

---

## 24. Structured compile result

The compile result contains at least:

```text
execution state
exit code when available
duration
error kind
first error
supplementary detail
stdout path
stderr path
command identity
working directory
GF version
artifact-check result
```

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class CompileResult:
    execution_state: str
    exit_code: int | None
    duration_ms: int
    error_kind: str
    first_error: str
    error_detail: str
    stdout_path: Path | None
    stderr_path: Path | None
    artifact_check: ArtifactCheck
```

Coherence rules:

- duration is non-negative;
- timeout maps to `timed_out`;
- launch failure has no fabricated exit code;
- successful compilation has exit code zero;
- `error_kind = OK` only on success;
- persisted evidence paths are run-relative;
- skip state is represented explicitly;
- no field is populated from report prose.

Exact serialization belongs to the persisted-schema reference.

---

## 25. File result construction

The validation orchestrator combines:

```text
source identity
source fingerprint
scan findings
compile result
initial validation status
```

into a file result.

Initial mapping:

| Evidence | Status | Initial class |
|---|---|---|
| explicit skip | `SKIPPED` | `skipped` |
| execution or contract error | `ERROR` | `ambiguous` |
| GF compile failure | `FAIL` | `ambiguous` |
| successful compile | `OK` | `ok` |

After all relevant results exist, the diagnostics module may assign:

```text
direct
downstream
ambiguous
```

The compiler does not perform global causal classification.

---

## 26. `.gfo` artifact verification

The expected object name normally derives from the GF module name:

```text
<ModuleName>.gfo
```

### 26.1 Required checks

For checkpoint and release evidence, the expected target object:

- exists;
- is a regular file;
- is non-empty;
- belongs to the current run or an explicitly defined validated cache;
- corresponds to the current source state;
- is registered in the artifact manifest.

### 26.2 Existence is not enough

A pre-existing `.gfo` does not prove current compilation success.

Success also requires:

- current process evidence;
- successful exit;
- no fatal diagnostic;
- source identity;
- current-run provenance.

### 26.3 Stale-artifact protection

Compilation uses an isolated run-owned `.gfo` directory.

Before launch:

- previous run directories are not reused;
- an unrelated artifact cannot satisfy the current request;
- source-tree `.gfo` files do not count as current-run evidence.

After launch:

- artifact production is attributable to the current run;
- the expected target artifact is checked;
- source fingerprint and GF version remain associated with release-significant evidence.

---

## 27. Dependency artifacts

Compiling one target may produce or reuse object files for dependencies.

Rules:

- dependency `.gfo` files are allowed in the run artifact directory;
- the target object remains separately identifiable;
- artifact inventory order is deterministic;
- a dependency object does not create a separate file result unless that source was independently selected;
- dependency failures remain part of the target compile evidence;
- causal links are assigned later by diagnostics.

---

## 28. Cache policy

The default compile contract uses isolated run-owned artifact directories.

Previous-run `.gfo` files are evidence, not trusted current compile inputs.

A shared cross-run cache requires a separate accepted contract defining:

- cache ownership;
- cache key;
- GF-version compatibility;
- source and dependency fingerprints;
- GF path identity;
- command options;
- platform compatibility;
- invalidation;
- corruption handling;
- manifest provenance.

---

## 29. Mode-specific behavior

### 29.1 Quick

Scope:

- one selected target;
- dependencies resolved by GF;
- optional configured smoke validation elsewhere in the pipeline.

Requirements:

- canonical module compilation;
- raw evidence;
- timeout;
- one structured result;
- no implicit PGF construction.

### 29.2 Checkpoint

Scope:

- configured checkpoint modules;
- deterministic project-declared order.

Requirements:

- required `.gfo` verification;
- independent result for each checkpoint;
- causal classification after compilation.

### 29.3 Release

Scope:

- required checkpoints;
- configured entrypoints.

Requirements:

- isolated artifacts;
- required object verification;
- no stale-artifact acceptance;
- recorded GF version and commands;
- separate PGF construction stage.

### 29.4 Diagnostic

Scope:

- broad selected source coverage;
- optional verbose compiler evidence.

Requirements:

- complete raw capture before report excerpt limits;
- visible parser and artifact warnings;
- no source or gold mutation.

---

## 30. Deterministic ordering

When compiling several files:

- project checkpoint order is preserved;
- configured entrypoint order is preserved;
- other targets use normalized project-relative ordering;
- results retain execution order;
- manifest entries use normalized run-relative ordering.

Parallel compilation requires a separate contract for:

- process limits;
- dependency contention;
- output isolation;
- cancellation;
- deterministic result ordering;
- log ownership;
- reproducible manifests.

---

## 31. Continuation policy

The run orchestrator decides whether processing continues.

Stop when:

- project or run configuration is invalid;
- GF cannot be launched for any target;
- the output root is unusable;
- cancellation is requested;
- continuing could corrupt evidence.

Continue when safe after:

- one GF source failure;
- one contained timeout;
- one parser fallback;
- one target-specific artifact failure.

Every failure remains represented in the run result.

---

## 32. Source immutability

Compilation does not modify:

- `.gf` sources;
- project configuration;
- project documentation;
- scenarios;
- inputs;
- gold files.

Generated objects, logs and temporary files are written only to owned run locations.

Options that may write beside source files are prohibited unless an explicit isolated contract defines their behavior.

---

## 33. Security

Required controls:

- executable and argument vector remain separate;
- normal compilation uses no shell;
- executable and working directory are validated independently;
- spaces and Unicode remain within individual arguments;
- NUL and prohibited control characters are rejected;
- source text is never interpreted as a host command;
- secrets are excluded from command evidence;
- normalized paths cannot escape approved roots;
- symlink resolution follows the security policy;
- project data cannot select arbitrary output paths.

Rendered commands are display evidence only.

---

## 34. Windows support

Wordbench supports:

- executable paths containing spaces;
- project and RGL paths containing spaces;
- run output roots containing spaces;
- native Windows process invocation;
- drive-letter-safe GF path handling;
- Windows-safe generated filenames;
- process-tree containment on timeout.

Example executable:

```text
C:\Program Files\GF\bin\gf.exe
```

It is passed as the executable value, not manually quoted inside a command string.

---

## 35. Unicode and encoding

Source paths and diagnostics may contain Unicode.

Rules:

- process bytes are preserved according to capture policy;
- decoding is deterministic;
- replacement decoding, when required, is explicit;
- persisted logs use UTF-8;
- canonical text artifacts use LF;
- normalization preserves linguistically meaningful Unicode;
- report escaping does not alter raw log files.

Encoding failures remain structured evidence.

---

## 36. Logging

The master log records at least:

```text
target
resolved executable
argument vector or command reference
working directory
start and finish timestamps
duration
execution state
exit code
error kind
first error
stdout path
stderr path
artifact-check result
```

Sensitive environment values are excluded.

Per-target stdout and stderr files contain captured process streams.

Reports may show excerpts but retain references to complete evidence.

---

## 37. Manifest

Retained compile evidence and artifacts are registered in:

```text
manifest.json
```

Typical roles:

```text
compile_stdout
compile_stderr
gfo
compile_auxiliary
```

Entries contain:

- run-relative path;
- role;
- media type;
- required policy;
- size;
- SHA-256;
- producer.

A required target `.gfo` absent from the manifest cannot satisfy release-significant evidence.

---

## 38. Reporting boundary

The compiler returns structured evidence.

It does not write:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
user-facing detail reports
```

Reports consume structured results and retained evidence.

They do not rerun compilation or maintain independent GF diagnostic semantics.

---

## 39. Regression comparison

Comparison consumes structured fields such as:

- file identity;
- source fingerprint;
- validation status;
- diagnostic class;
- error kind;
- first error;
- execution state;
- artifact existence;
- GF version.

Typical interpretation:

```text
previous OK + current FAIL  → regressed
previous FAIL + current OK  → improved
```

A source change with unchanged outcome is not automatically a regression.

Incompatible schema or GF environments are marked incompatible rather than silently equated.

---

## 40. Public responsibilities

Conceptual compilation use case:

```python
def compile_file(
    file_path: Path,
    run_config: RunConfig,
    run_paths: RunPaths,
) -> CompileResult:
    ...
```

Related responsibilities may include:

```python
def build_compile_request(...) -> CompileRequest:
    ...
```

```python
def build_compile_args(...) -> list[str]:
    ...
```

```python
def verify_compile_artifacts(...) -> ArtifactCheck:
    ...
```

```python
def probe_gf_version(...) -> GFVersionResult:
    ...
```

Observable contracts require:

- explicit target;
- explicit resolved configuration;
- explicit run-owned paths;
- structured result;
- raw evidence;
- no report generation;
- no causal classification.

Internal decomposition may vary while these contracts remain true.

---

## 41. Error-kind mapping

| Condition | Error kind |
|---|---|
| success | `OK` |
| recognized GF type error | `TYPE` |
| recognized GF syntax error | `SYNTAX` |
| recognized GF internal failure | `INTERNAL` |
| timeout | `TIMEOUT` |
| invalid compile configuration | `CONFIG` |
| source or output I/O failure | `IO` |
| executable or unsupported-option failure | `TOOL` |
| unrecognized compilation failure | `OTHER` |

---

## 42. Failure categories

| Failure category | Validation status | Execution state |
|---|---|---|
| launch failure | `ERROR` | `launch_failed` |
| timeout | `ERROR` | `timed_out` |
| cancellation | run policy | `cancelled` |
| GF compilation failure | `FAIL` | `completed` |
| artifact failure | `FAIL` or `ERROR` by contract | `completed` |
| diagnostic parsing failure | `ERROR` | `completed` |
| request contract failure | `ERROR` | context-dependent |

These categories do not replace validation status, error kind or diagnostic causal class.

---

## 43. Test obligations

Unit and contract tests cover at least:

```text
batch command construction
silent flag policy
source argument last
argument-vector ordering
resolved GF path preservation
version-gated optional flags
run-owned directory creation
explicit working directory
configured executable and timeout
separate stdout and stderr
zero and non-zero exit handling
fatal diagnostic with zero exit
timeout and cancellation
launch failure
explicit skip
parser failure with preserved raw evidence
target containment
paths with spaces
Unicode paths and diagnostics
deterministic evidence filenames
duplicate basenames
stale `.gfo` rejection
required artifact absence
manifest registration
prohibited report and process dependencies
```

Real-GF integration tests cover:

```text
valid abstract and concrete modules
resource modules
interface and instance modules
project and RGL imports
syntax and type errors
missing imports
paths with spaces
isolated `.gfo` output
dependency artifact production
fresh-run recompilation
source modification
stale source-tree artifacts
version probe and compile using the same executable
```

---

## 44. Conformance checklist

```text
[ ] per-file compilation uses `-batch`
[ ] PGF construction remains separate
[ ] executable is explicit and recorded
[ ] GF path is ordered and recorded
[ ] working directory is explicit
[ ] source argument is last
[ ] shell execution is disabled
[ ] stdout and stderr are captured separately
[ ] raw evidence precedes parsing
[ ] timeout and cancellation are explicit
[ ] launch failure differs from GF failure
[ ] skipped compilation differs from success
[ ] structured fields are coherent
[ ] compiler does not assign causal ownership
[ ] required `.gfo` artifacts are verified
[ ] stale artifacts cannot satisfy current checks
[ ] retained artifacts are manifested
[ ] path, Unicode and Windows tests pass
[ ] diagnostic fixtures pass
[ ] supported GF integration tests pass
[ ] locks and reference documents agree
[ ] Wordbench remains independent from `gf-portfolio`
```

---

## 45. Troubleshooting order

When compilation fails, inspect:

1. resolved GF executable;
2. GF version evidence;
3. selected source path;
4. working directory;
5. resolved GF search path;
6. ordered argument vector;
7. stdout;
8. stderr;
9. exit code and execution state;
10. parsed error kind and first error;
11. expected `.gfo` path;
12. artifact check and manifest;
13. causal classification;
14. previous compatible run.

Gold files and reports are not compilation inputs.

---

## 46. Anti-drift rules

Compilation drift exists when:

- compiler arguments differ from this contract;
- CLI and GUI resolve equivalent inputs differently;
- `-make` appears in normal per-file compilation;
- the source argument is no longer last;
- stdout and stderr are merged before capture;
- skipped compilation is reported as success;
- report code reparses GF output independently;
- artifact paths differ from their owner;
- stale `.gfo` files satisfy current-run checks;
- structured compile fields change without consumer and schema updates;
- the compiler assigns downstream causality;
- a GF flag is introduced without capability and integration tests;
- Wordbench compilation depends on `gf-portfolio`.

Such changes require coordinated updates to the compiler, external-process boundary, models, artifact ownership, diagnostics, tests, locks and this document.

---

## 47. Cross-references

| Topic | Document |
|---|---|
| Product boundary | `docs/architecture/PRODUCT_BOUNDARIES.md` |
| External GF contract | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Framework component contracts | `docs/INTERFILE_CONTRACT_LOCK.md` |
| Persisted compile fields | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Toolchain integration | `docs/gf/GF_TOOLCHAIN_INTEGRATION.md` |
| GF path resolution | `docs/gf/GF_PATH_RESOLUTION.md` |
| PGF construction | `docs/gf/GF_PGF_BUILD.md` |
| GF version policy | `docs/gf/GF_VERSION_COMPATIBILITY.md` |
| File selection | `docs/validation/FILE_SELECTION.md` |
| Compilation validation | `docs/validation/COMPILATION_VALIDATION.md` |
| GF diagnostics | `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md` |
| Timeouts and process failures | `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md` |
| Artifact model | `docs/architecture/ARTIFACT_MODEL.md` |
| Status values | `docs/reference/STATUS_VALUES.md` |
| Active-project contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |

---

## 48. Enforcement

> A GF module compilation succeeds only when GF executes the canonical batch-compilation request, raw process evidence is preserved, the result is interpreted coherently and every required current-run artifact check passes.

Successful `.gfo` compilation is necessary evidence for many workflows.

It is not proof of scenario correctness, PGF construction or release readiness.
