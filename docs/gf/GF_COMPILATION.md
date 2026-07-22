# GF Wordbench — GF Compilation

**Document ID:** `GF-WB-GF-COMPILATION`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\gf\GF_COMPILATION.md`  
**Applies to:** GF source-module compilation, `.gfo` artifact validation, compile evidence, and compile result construction  
**Owner:** GF Wordbench maintainers  
**Contract references:** `EXT-GF-003`, `IFC-AUDIT-005`, `IFC-AUDIT-006`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines how GF Wordbench compiles Grammatical Framework source modules and interprets the result.

It governs the validation path:

```text
GF source target
    → resolved GF command
    → external GF process
    → raw stdout and stderr
    → `.gfo` artifact evidence
    → CompileSummary
    → FileResult
```

It establishes:

- the difference between module compilation and PGF construction;
- the canonical batch-compiler command;
- input validation and path handling;
- working-directory and output-directory rules;
- timeout and process behavior;
- raw evidence requirements;
- diagnostic parsing boundaries;
- success, failure, error, and skipped semantics;
- `.gfo` freshness and stale-artifact protections;
- mode-specific compilation behavior;
- required tests and acceptance criteria.

This document does not define:

- static scanning rules;
- dependency-cascade classification;
- `.gfs` scenario execution;
- PGF release construction;
- report formatting;
- project-specific module architecture.

Those responsibilities are documented elsewhere.

---

## 2. Authority boundary

### 2.1 GF is authoritative for

GF is authoritative for:

- GF syntax;
- name resolution;
- type checking;
- module dependency resolution;
- source-to-object compilation;
- production of `.gfo` object files;
- GF diagnostic text;
- GF process exit behavior.

### 2.2 GF Wordbench is authoritative for

GF Wordbench is authoritative for:

- selecting the source target;
- resolving the GF executable;
- resolving the GF search path;
- constructing the ordered argument list;
- selecting the working directory;
- preparing run-owned output directories;
- applying a timeout;
- capturing stdout and stderr separately;
- recording process evidence;
- verifying required artifacts;
- mapping evidence into a structured compile result;
- preserving skipped compilation as distinct from success;
- passing results to the classifier and reporters.

### 2.3 Forbidden duplication

GF Wordbench MUST NOT implement a competing:

- GF parser;
- GF type checker;
- GF module resolver;
- GF optimizer;
- `.gfo` serializer;
- interpretation of GF source semantics.

Static scans may identify suspicious source patterns, but scan findings are not compilation truth.

---

## 3. Terminology

### Compilation target

The `.gf` source file explicitly selected for one compile operation.

### Dependency

A GF module required directly or transitively by the compilation target.

### Object artifact

A compiled GF object file:

```text
<ModuleName>.gfo
```

### Compile evidence

The command, working directory, GF version, process result, raw output streams, artifact checks, and source identity associated with one compilation attempt.

### Compile summary

The structured normalized result returned by the compiler component.

### Module compilation

Compilation of a `.gf` source module and its required dependencies into `.gfo` object files.

### PGF build

Linking one abstract grammar and one or more compatible concrete syntaxes into a `.pgf` runtime grammar.

Module compilation and PGF build are separate validation stages.

### Fatal diagnostic

A GF diagnostic recognized as proving that the requested compilation did not succeed, even when process behavior is unusual.

### Artifact freshness

Evidence that an object artifact corresponds to the current source state and current compile operation rather than an earlier run.

### Transitional command

A command retained temporarily for migration from the earlier GF Audit implementation but not accepted as the final canonical command.

---

## 4. Compilation versus PGF construction

GF recognizes distinct compilation products:

```text
*.gf
    → *.gfo
    → *.pgf
```

GF Wordbench MUST preserve this distinction.

### 4.1 Module compilation

Purpose:

```text
validate a source module and produce or validate `.gfo` evidence
```

Canonical command shape:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

### 4.2 PGF construction

Purpose:

```text
build the final runtime grammar from configured release entrypoints
```

Canonical command shape:

```text
<gf> -make -optimize-pgf <path-options> <entrypoint-1> [<entrypoint-N>...]
```

PGF construction is governed by:

```text
docs/gf/GF_PGF_BUILD.md
```

### 4.3 Required separation

GF Wordbench MUST NOT:

- treat `.gfo` compilation as proof that the final `.pgf` can be built;
- run `-make` merely to validate every individual source file;
- classify a PGF-linking failure as an ordinary per-file compile result;
- declare release readiness solely from successful file compilation;
- overwrite release artifacts during ordinary per-file validation.

---

## 5. Canonical module-compilation command

## 5.1 Normative form

```text
<gf-executable>
    -batch
    -s
    <resolved-path-options>
    <validated-artifact-options>
    <source-file>
```

Rendered as one line:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

The source-file argument MUST be last.

## 5.2 Argument representation

The executable and arguments MUST be represented separately:

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

The rendered command is for logs and reports only.

Normal process execution MUST use:

```text
shell = false
```

GF Wordbench MUST NOT construct one shell command string for normal compilation.

## 5.3 `-batch`

`-batch` invokes GF without opening the interactive shell and compiles `.gf` sources to `.gfo`.

It is REQUIRED for canonical per-file compilation.

## 5.4 `-s`

`-s` suppresses non-error compiler chatter.

Default policy:

| Mode | `-s` |
|---|---:|
| `quick` | required |
| `checkpoint` | required |
| `release` | required for module-compilation stages |
| `diagnostic` | optional |

Diagnostic mode may omit `-s` when verbose compiler progress is intentionally required.

The exact command MUST be recorded regardless of the verbosity choice.

## 5.5 Path options

GF Wordbench may provide a resolved GF search path using the option supported by the selected GF version.

Conceptual form:

```text
--path=<resolved-gf-path>
```

RGL or library-root options may also be supplied when supported and validated.

Conceptual form:

```text
--gf-lib-path=<rgl-root>
```

Detailed path construction belongs to:

```text
docs/gf/GF_PATH_RESOLUTION.md
```

The compiler MUST consume the resolved path as an ordered value. It MUST NOT independently rebuild project architecture.

## 5.6 Artifact options

GF Wordbench SHOULD route generated object artifacts into the current run:

```text
artifacts/gfo/
```

Optional GF flags may include:

```text
--gfo-dir=<run-gfo-dir>
--output-dir=<run-output-dir>
```

These options may be used only when:

1. the selected GF version supports them;
2. integration tests prove their behavior;
3. the resolved command is recorded;
4. the output directory is run-owned;
5. artifact verification uses the actual resolved location.

Unsupported flags MUST NOT be passed optimistically.

## 5.7 CPU statistics

An optional CPU-statistics flag may be supplied only through explicit configuration.

Conceptual form:

```text
--cpu
```

CPU statistics:

- MUST NOT be enabled silently;
- MUST NOT change validation status;
- MAY be preserved in raw output;
- SHOULD be normalized out of deterministic comparisons when unstable.

## 5.8 Final source argument

The selected source path MUST be the final argument.

This provides a stable command contract and makes command validation deterministic.

---

## 6. Transitional behavior from GF Audit

The earlier compiler currently builds arguments resembling:

```text
--batch
--make
--gf-lib-path=<rgl-root>
--path=<gf-path>
--gfo-dir=<gfo-dir>
--output-dir=<out-dir>
<source-file>
```

This behavior is transitional.

The final GF Wordbench implementation MUST separate:

```text
module compilation
```

from:

```text
PGF construction
```

Therefore:

- `--make` MUST be removed from canonical per-file compilation;
- PGF creation MUST move to the dedicated PGF build stage;
- compatibility behavior MAY remain behind an explicit migration flag;
- compatibility execution MUST record the exact resolved command;
- compatibility behavior MUST have a removal milestone;
- no new test or document may treat the transitional command as canonical.

Recommended migration sequence:

```text
1. retain current command behind compatibility mode;
2. implement canonical `-batch -s` command builder;
3. add real-GF integration tests;
4. verify object-output routing;
5. make canonical mode the default;
6. remove compatibility mode after the documented deprecation period.
```

---

## 7. Compilation inputs

Each compile request requires:

```text
source_file
run_config
run_paths
```

The resolved request must contain:

- explicit GF executable;
- active project root;
- selected source file;
- resolved GF path;
- RGL root where applicable;
- compile timeout;
- run-owned raw log paths;
- run-owned artifact paths;
- explicit compile mode;
- optional verbosity and CPU flags.

---

## 8. Source-target validation

Before launching GF, the compiler MUST validate the target.

Required checks:

```text
[ ] target is present
[ ] target is a regular file
[ ] target has the `.gf` suffix
[ ] target belongs to the active project or an explicitly permitted source root
[ ] target is included by resolved selection policy
[ ] target path contains no prohibited control characters
[ ] target can be represented safely as one process argument
```

The compiler MUST NOT:

- compile an excluded file accidentally;
- follow an unreviewed path outside the active project;
- silently replace a missing target with another same-named file;
- derive the target from report text;
- modify the target before or after compilation.

A target-validation failure is normally:

```text
validation_status = ERROR
error_kind = CONFIG or IO
execution_state = launch_failed or not_started
```

If `not_started` is not a persisted execution-state value, the process result remains absent and the file result records the configuration error explicitly.

---

## 9. Module identity

GF module identity and filename SHOULD agree.

Example:

```text
file:   GrammarX.gf
module: GrammarX
```

The selector or module-name extractor owns module identity extraction.

The compiler:

- MAY receive the expected module name;
- MUST NOT invent a different module name from diagnostic prose;
- MUST preserve the selected file path;
- SHOULD verify expected object-artifact naming when artifact checks are enabled.

A module-name mismatch is a project or compile validation failure, not a reason to rename artifacts silently.

---

## 10. GF executable resolution

The final run configuration MUST contain the GF executable actually used.

Resolution may begin from:

1. explicit CLI input;
2. explicit GUI input;
3. environment configuration;
4. optional `PATH` lookup;
5. failure.

Once the run configuration is finalized:

- GF Wordbench MUST NOT silently switch to another GF installation;
- the executable MUST be recorded in run metadata;
- paths containing spaces MUST be supported;
- on Windows, a configured directory MUST NOT be accepted as the executable;
- a missing or non-launchable executable produces a launch error.

A required compilation MUST normally be preceded by a GF version probe unless the probe was explicitly skipped.

---

## 11. GF version handling

The version probe and compile operation are separate process calls.

Version probe command:

```text
<gf-executable> --version
```

Version evidence:

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

Compilation MUST use the same resolved executable recorded by the version probe.

A version outside the tested range may:

- fail configuration when a known incompatibility exists;
- proceed with a warning when policy permits;
- require capability detection before optional flags are used.

The compile command MUST NOT be inferred solely from the application version.

---

## 12. GF path resolution

The compiler receives a resolved GF path.

It does not own the complete path-resolution policy.

The resolved path normally includes:

- active project source roots;
- required framework or project resource paths;
- configured RGL locations;
- required RGL subdirectories;
- documented compatibility paths.

Required invariants:

- order is deterministic;
- duplicates are removed without changing first occurrence;
- all required project source roots are represented;
- paths are normalized for the selected platform and GF version;
- the exact resolved value is recorded;
- CLI and GUI resolve equivalent configuration identically;
- path resolution does not depend on the process launch directory.

The compiler MUST NOT guess missing module directories after GF reports a resolution failure.

---

## 13. Working directory

Every compilation process MUST use an explicit working directory.

Canonical working directory:

```text
resolved project root
```

The working directory MUST NOT depend on:

- terminal location;
- IDE defaults;
- GUI launch directory;
- launcher shortcut location;
- Python package directory;
- previous process execution.

The working directory MUST be recorded as compile evidence.

---

## 14. Run-owned directories

Before process launch, GF Wordbench MUST prepare the required directories.

Canonical compile evidence directory:

```text
run_<run-id>/raw/compile/
```

Canonical object-artifact directory:

```text
run_<run-id>/artifacts/gfo/
```

Canonical auxiliary-output directory:

```text
run_<run-id>/artifacts/out/
```

Required preparation:

```text
compile_logs_dir.mkdir(parents=True, exist_ok=True)
gfo_dir.mkdir(parents=True, exist_ok=True)
out_dir.mkdir(parents=True, exist_ok=True)
```

Directory creation failure produces:

```text
validation_status = ERROR
error_kind = IO
```

The compiler MUST NOT fall back silently to a source directory after run-owned output preparation fails.

---

## 15. Evidence filenames

Each source target receives deterministic raw output paths.

Canonical pattern:

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
```

The safe file key SHOULD derive from the project-relative source path.

Example:

```text
lib/src/example/GrammarX.gf
```

may become:

```text
lib__src__example__GrammarX.gf.out.txt
lib__src__example__GrammarX.gf.err.txt
```

Exact escaping belongs to shared path utilities.

Required properties:

- deterministic;
- unique for distinct project-relative paths;
- path-safe on Windows;
- stable within one schema version;
- not derived only from basename when duplicate basenames are possible;
- independent of localized report text.

---

## 16. Process execution

Compilation MUST use the shared process runner.

Conceptual call:

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

The process runner owns:

- launch;
- timeout enforcement;
- process termination or containment;
- exit-code capture;
- duration measurement;
- stdout capture;
- stderr capture;
- launch-failure representation.

The process runner MUST NOT:

- parse GF diagnostics;
- assign `direct` or `downstream`;
- know project validation modes;
- generate reports;
- alter GF source files.

---

## 17. Standard streams

Stdout and stderr MUST be captured separately.

Required raw evidence:

```text
stdout_path
stderr_path
```

Rules:

- files are UTF-8-decoded according to documented process policy;
- undecodable bytes MUST be handled deterministically;
- both files SHOULD exist after a launched process, even when empty;
- non-zero exit MUST NOT discard either stream;
- timeout MUST preserve bytes captured before termination;
- parsing MUST occur only after raw evidence has been written;
- a parser error MUST NOT destroy or replace raw evidence.

A combined diagnostic view MAY be constructed in memory:

```text
stdout + newline + stderr
```

The combined view is derived evidence and MUST NOT replace the separate raw files.

Because separate streams do not preserve a universal cross-stream ordering, diagnostic parsers MUST NOT claim exact interleaving unless the process runner explicitly captured it.

---

## 18. Timeout behavior

Each compilation uses the configured per-file timeout.

Timeout rules:

- timeout value is a positive integer;
- the process runner enforces it;
- a timeout stops or contains the process according to platform policy;
- partial stdout and stderr are preserved;
- `timed_out` is true in legacy-compatible summaries;
- canonical execution state is `timed_out`;
- error kind is `TIMEOUT`;
- the result cannot be `OK`;
- the next file may continue according to orchestrator policy.

Recommended normalized result:

```text
validation_status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
first_error = TIMEOUT
```

A timeout is not a downstream classification. Dependency classification occurs later.

---

## 19. Cancellation behavior

Cancellation is distinct from timeout.

Recommended normalized result:

```text
validation_status = ERROR or SKIPPED according to explicit cancellation policy
execution_state = cancelled
error_kind = TOOL or OTHER
```

For a user-cancelled whole run, the run-level policy controls whether incomplete file checks are represented as `SKIPPED`.

`CANCELLED` MUST NOT be introduced as a validation-status enum.

---

## 20. Launch failures

A launch failure occurs when the operating system cannot start GF.

Examples:

- executable missing;
- permission denied;
- executable path is a directory;
- invalid working directory;
- invalid process arguments;
- platform launch error.

Recommended normalized result:

```text
validation_status = ERROR
execution_state = launch_failed
error_kind = TOOL, CONFIG, or IO
```

A launch failure MUST remain distinguishable from:

- GF returning a non-zero exit code;
- GF reporting a source compile failure;
- timeout;
- artifact verification failure.

---

## 21. Exit-code interpretation

Exit code is necessary evidence but is not the only success condition.

### 21.1 Zero exit

A zero exit permits success only when:

- process launched;
- process completed;
- no timeout or cancellation occurred;
- no recognized fatal diagnostic exists;
- required artifact checks pass.

### 21.2 Non-zero exit

A non-zero exit normally produces:

```text
validation_status = FAIL
```

when GF ran correctly and rejected the source.

It produces:

```text
validation_status = ERROR
```

when the non-zero result represents infrastructure, launch, unsupported-tool, or uninterpretability failure.

### 21.3 Zero exit with fatal diagnostic

If GF returns zero but a recognized fatal diagnostic proves failure:

- status MUST NOT be `OK`;
- raw evidence remains authoritative;
- the diagnostic parser records an error kind;
- artifact checks must not override the fatal diagnostic.

### 21.4 Exit code without diagnostic text

A non-zero exit with no usable diagnostic remains a failure.

Recommended summary:

```text
error_kind = OTHER
first_error = "Non-zero exit with no recognized diagnostic"
```

The exact exit code is preserved.

---

## 22. Compile success criteria

A compile result is successful only when every applicable condition is true:

```text
[ ] source target passed validation
[ ] GF executable resolved
[ ] required directories were prepared
[ ] process launched
[ ] process completed
[ ] process did not time out
[ ] process was not cancelled
[ ] exit code indicates success
[ ] no fatal diagnostic was recognized
[ ] target artifact check passed when required
[ ] evidence paths are valid
[ ] structured result is internally coherent
```

Canonical status:

```text
validation_status = OK
diagnostic_class = ok
error_kind = OK
```

The compiler returns compile evidence. The classifier owns final causal classification after all file results exist.

---

## 23. Compile failure criteria

A compile validation failure occurs when GF executes correctly but rejects the source or its dependency graph.

Examples:

- syntax error;
- type error;
- unresolved module;
- incompatible interface or instance;
- internal GF compilation diagnostic;
- non-zero exit attributable to grammar compilation.

Typical result:

```text
validation_status = FAIL
execution_state = completed
error_kind = SYNTAX, TYPE, INTERNAL, or OTHER
```

The compiler MUST NOT decide whether the failure is:

```text
direct
downstream
ambiguous
```

That decision belongs to the classifier.

---

## 24. Compile error criteria

A compile execution error occurs when GF Wordbench cannot perform or interpret the check reliably.

Examples:

- launch failure;
- timeout;
- output directory failure;
- unsupported command option;
- diagnostic parser failure;
- artifact contract failure where success cannot be trusted;
- unreadable raw output;
- invalid configuration.

Typical result:

```text
validation_status = ERROR
```

The appropriate error kind is selected from:

```text
INTERNAL
TIMEOUT
CONFIG
IO
TOOL
OTHER
```

---

## 25. Skipped compilation

Compilation may be skipped only by explicit resolved configuration or mode policy.

Legacy input:

```text
no_compile = true
```

Canonical result:

```text
validation_status = SKIPPED
diagnostic_class = skipped
execution_state = absent
```

A skipped compile MUST NOT be represented as a successful GF invocation.

Required evidence:

- the reason for skipping;
- target identity;
- source fingerprint where available;
- no fabricated process exit;
- no fabricated `.gfo` artifact.

Legacy `CompileSummary` compatibility may temporarily contain:

```text
exit_code = 0
timed_out = false
error_kind = OK
error_detail = "compile skipped"
```

However, the enclosing `FileResult.status` MUST remain `SKIPPED`, and future models SHOULD represent skip state explicitly rather than overloading process success fields.

---

## 26. Diagnostic parsing

Diagnostic parsing converts raw GF output into a compact structured summary.

It may identify:

```text
TYPE
SYNTAX
INTERNAL
TIMEOUT
OTHER
OK
```

Future integration may also use:

```text
CONFIG
IO
TOOL
SCRIPT
```

for non-GF execution failures.

### 26.1 Parser input

The parser receives:

- stdout text;
- stderr text;
- timeout state;
- exit code;
- optional duration;
- evidence paths.

### 26.2 Parser output

The parser returns or populates:

```text
error_kind
first_error
error_detail
```

### 26.3 Parser invariants

- parsing occurs after raw capture;
- parsing is deterministic;
- parsing does not rewrite raw files;
- recognized messages retain useful GF wording;
- parser patterns are tested against fixtures;
- unrecognized non-zero output becomes `OTHER`;
- parser failure never converts a failed process into `OK`;
- the parser does not assign downstream causality;
- report writers do not reparse raw GF output independently.

### 26.4 Current recognized patterns

The migrated implementation currently recognizes at least:

- timeout;
- internal `GeneratePMCFG` failures;
- type diagnostics containing expected and inferred forms;
- syntax diagnostics;
- first meaningful line on other non-zero exits;
- successful zero-exit fallback.

These patterns are a starting implementation, not a complete model of every GF diagnostic.

Pattern expansion MUST preserve backward-compatible meaning or be documented as a diagnostic-classification change.

---

## 27. `CompileSummary`

The minimum locked compile-summary fields are:

```text
exit_code
timed_out
duration_ms
error_kind
first_error
error_detail
stdout_path
stderr_path
```

Conceptual Python model:

```python
@dataclass(frozen=True, slots=True)
class CompileSummary:
    exit_code: int
    timed_out: bool
    duration_ms: int
    error_kind: str
    first_error: str
    error_detail: str
    stdout_path: Path | None
    stderr_path: Path | None
```

### 27.1 Field semantics

#### `exit_code`

The actual external process exit code when GF launched.

Synthetic compatibility codes MUST be documented and SHOULD be removed from final canonical schemas in favor of explicit execution state.

#### `timed_out`

Legacy-compatible convenience field.

It MUST be true when the process timed out.

Canonical process modeling SHOULD also expose:

```text
execution_state = timed_out
```

#### `duration_ms`

Non-negative measured process duration in milliseconds.

#### `error_kind`

Canonical error category.

#### `first_error`

The first useful normalized diagnostic selected by documented parser rules.

It is not guaranteed to be the ultimate root cause.

#### `error_detail`

Compact structured or normalized supplementary detail.

Raw multiline diagnostics belong in the raw logs.

#### `stdout_path`

Path to captured stdout.

Canonical persisted representation is run-relative.

#### `stderr_path`

Path to captured stderr.

Canonical persisted representation is run-relative.

### 27.2 Coherence invariants

- `duration_ms >= 0`;
- timeout implies `timed_out = true`;
- successful compile implies `exit_code == 0`;
- `error_kind = OK` only when no compile error was detected;
- `stdout_path` and `stderr_path` identify the actual captured files;
- skipped compilation is identified by the enclosing status;
- no field is populated from report prose.

---

## 28. File result construction

The audit orchestrator combines:

```text
source identity
scan counts
source fingerprint
compile summary
initial status
```

into `FileResult`.

Initial compile-derived status:

| Evidence | Initial status |
|---|---|
| explicitly skipped | `SKIPPED` |
| execution or framework error | `ERROR` |
| GF compile failure | `FAIL` |
| successful compile | `OK` |

Initial diagnostic class before global classification:

| Evidence | Initial class |
|---|---|
| skipped | `skipped` |
| success | `ok` |
| failure not yet classified | `ambiguous` |

After every file result exists, the classifier may change failure causality to:

```text
direct
downstream
ambiguous
```

The compiler MUST NOT perform this global classification.

---

## 29. `.gfo` artifact expectations

GF source compilation normally produces `.gfo` object files.

The expected target object name is normally derived from the GF module name:

```text
<ModuleName>.gfo
```

### 29.1 Artifact policies

GF Wordbench defines three artifact-check policies.

#### Required

The expected target artifact MUST:

- exist;
- be a regular file;
- be non-empty;
- belong to the current run or validated cache;
- correspond to the current source state.

Used by:

```text
checkpoint
release
```

#### Recommended

Artifact verification SHOULD run, but an explicitly documented unsupported routing limitation may produce a warning rather than invalidating the compile.

Used by:

```text
quick
diagnostic
```

during migration only.

#### Disabled

Artifact existence is not checked.

This policy is allowed only for an explicitly documented compatibility case and MUST NOT be used for release evidence.

### 29.2 Artifact existence is not sufficient

An existing `.gfo` does not prove current compilation success.

Success additionally requires:

- current process evidence;
- successful exit;
- no fatal diagnostic;
- source identity;
- current-run or validated-cache provenance.

### 29.3 Stale artifact protection

GF Wordbench MUST prevent a stale `.gfo` from masking a current source failure.

Preferred strategy:

```text
compile into an isolated run-owned `.gfo` directory
```

Before compilation:

- the expected target path in the current run MUST not already contain an unrelated artifact;
- a previous run directory MUST not be reused as the current output directory;
- source-tree `.gfo` files MUST not count as current-run evidence unless an explicit validated-cache policy exists.

After compilation:

- artifact modification or creation MUST be attributable to the current run;
- the expected target artifact is checked;
- the manifest records the artifact;
- release-significant evidence includes the source fingerprint and GF version.

---

## 30. Dependency artifacts

Compiling one target may compile or reuse dependencies.

Dependency `.gfo` files MAY appear in the run artifact directory.

Rules:

- dependency artifacts are allowed;
- artifact inventory order is deterministic;
- the target object remains separately identifiable;
- dependency artifacts do not each create a new `FileResult` unless those files were independently selected;
- a dependency compile failure remains part of the target compile evidence;
- the later classifier may link the target failure to another selected file.

GF Wordbench MUST NOT assume that every produced `.gfo` corresponds to a separately validated selected file.

---

## 31. Cache policy

The default final policy is:

```text
no shared cross-run compile cache
```

Each run uses isolated run-owned artifact directories.

This policy favors:

- reproducibility;
- stale-artifact protection;
- simpler evidence;
- easier cleanup;
- clearer manifests.

A future shared cache may be introduced only through an explicit architecture decision and contract update.

Any future cache key must account for at least:

- GF version;
- target module identity;
- target source fingerprint;
- dependency fingerprints or a safe dependency closure identity;
- resolved GF path;
- relevant compile options;
- platform-sensitive object-format compatibility.

Until that contract exists, previous-run `.gfo` files are evidence only, not compile inputs trusted by GF Wordbench.

---

## 32. Mode-specific behavior

## 32.1 Quick mode

Purpose:

```text
fast local feedback
```

Compilation scope:

- selected target file;
- dependencies resolved by GF;
- optional minimal entrypoint check when configured elsewhere.

Requirements:

- use canonical module compilation;
- preserve raw output;
- apply timeout;
- return one structured result;
- do not run PGF construction automatically.

## 32.2 Checkpoint mode

Purpose:

```text
prove one development layer
```

Compilation scope:

- configured checkpoint modules;
- deterministic checkpoint order.

Requirements:

- artifact verification is required;
- a checkpoint failure is preserved independently;
- later checkpoints may continue according to pipeline policy;
- dependency-cascade classification occurs after compilation.

## 32.3 Release mode

Purpose:

```text
prove release prerequisites
```

Module compilation scope:

- required checkpoint modules;
- configured entrypoints.

Requirements:

- isolated run-owned artifacts;
- required `.gfo` verification;
- no stale artifact acceptance;
- exact GF version and commands recorded;
- subsequent PGF build remains a separate stage.

## 32.4 Diagnostic mode

Purpose:

```text
maximize investigation evidence
```

Compilation scope:

- broad selected source set;
- optional verbose compiler output.

Requirements:

- raw output is never truncated before storage;
- report excerpts may be bounded;
- CPU statistics may be enabled explicitly;
- artifact and parser warnings remain visible;
- diagnostic mode must not change source or gold files.

---

## 33. Deterministic ordering

When multiple files are compiled:

- selector order is deterministic;
- checkpoint order follows project configuration;
- otherwise paths are ordered by normalized project-relative path;
- compile results retain execution order;
- artifact manifests sort by normalized run-relative path;
- top-error aggregation does not change compile order.

Parallel compilation is not part of the default v1 contract.

A future parallel mode requires explicit rules for:

- output isolation;
- process limits;
- deterministic result ordering;
- log ownership;
- cancellation;
- dependency contention;
- reproducible manifests.

---

## 34. Failure continuation policy

The orchestrator owns whether the run continues after a file failure.

Default diagnostic-oriented policy:

```text
continue with other selected files when safe
```

Stop immediately when:

- run configuration is invalid;
- GF executable cannot be launched for any file;
- output root is unusable;
- cancellation is requested;
- continuing would corrupt or overwrite evidence.

Continue when safe after:

- one GF source compile failure;
- one timeout, subject to process containment;
- one diagnostic parser fallback;
- one expected artifact failure isolated to the current target.

Every continuation decision must preserve the failed result.

---

## 35. Source immutability

Compilation MUST NOT modify:

- `.gf` source files;
- project documentation;
- project scenarios;
- project inputs;
- gold files;
- project configuration.

Generated `.gfo`, `.pgf`, logs, reports, and temporary files must be written only to owned locations.

If a selected GF option may modify source-adjacent files, it must be prohibited or isolated until explicitly reviewed.

---

## 36. Security rules

Required rules:

- use an argument list, not shell interpolation;
- use `shell = false`;
- validate executable and working directory separately;
- preserve paths containing spaces as one argument;
- reject embedded NUL characters;
- reject untrusted newline or control characters in logged command fields;
- do not execute source file text as shell content;
- do not expose secrets in command logs;
- do not allow a source-relative path to escape the project root after normalization;
- do not follow unreviewed symlinks outside allowed roots in strict mode;
- do not overwrite arbitrary paths supplied by project content.

Human-readable command rendering must quote safely for display but is never re-executed.

---

## 37. Windows requirements

GF Wordbench must support Windows paths.

Required behavior:

- executable path may contain spaces;
- project path may contain spaces;
- RGL path may contain spaces;
- output root may contain spaces;
- arguments are passed without shell parsing;
- path separator behavior is resolved by GF path policy;
- drive letters are not split as GF path elements accidentally;
- long paths produce a clear error when unsupported;
- process termination after timeout follows Windows containment policy;
- filenames use Windows-safe characters;
- reserved device names are not used as generated safe keys.

Example executable:

```text
C:\Program Files\GF\bin\gf.exe
```

It must be passed as the executable field, not manually quoted inside an argument string.

---

## 38. Unicode and encoding

GF source paths and output may contain Unicode.

Required policy:

- project source is expected to use UTF-8 according to project rules;
- process capture uses documented encoding handling;
- raw bytes are not silently discarded;
- replacement-decoding behavior, if used, is explicit;
- persisted logs are UTF-8;
- canonical text output uses LF;
- diagnostic normalization preserves linguistic Unicode;
- report escaping must not alter the raw log.

Encoding failures produce structured evidence and never erase the captured process output.

---

## 39. Logging requirements

The master log records at least:

```text
compile target
resolved executable
resolved argument list or command reference
working directory
start timestamp
finish timestamp
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

Per-file raw logs contain unmodified process streams.

A report may provide excerpts but MUST link or point to the full evidence paths.

---

## 40. Manifest requirements

Every retained compile artifact should be registered in:

```text
manifest.json
```

Recommended roles:

```text
compile_stdout
compile_stderr
gfo
other
```

Manifest entries include:

- run-relative path;
- role;
- media type;
- required flag;
- size;
- SHA-256;
- creating component.

A required target `.gfo` missing from the manifest invalidates release-significant artifact evidence.

---

## 41. Reporting boundaries

The compiler returns structured evidence.

It MUST NOT write:

- `summary.md`;
- `summary.json`;
- `AI_READY.md`;
- `top_errors.txt`;
- user-facing Markdown details.

Report writers consume `RunResult` and existing raw evidence.

They MUST NOT rerun compilation or independently reinterpret GF output with undocumented rules.

---

## 42. Regression comparison

Compilation comparison uses structured fields, not report prose.

Comparable fields may include:

- file identity;
- source fingerprint;
- validation status;
- diagnostic class;
- error kind;
- first error;
- timeout state;
- artifact existence;
- GF version;
- duration where used only as non-gating information.

A changed source fingerprint with unchanged status is not automatically a regression.

A current `FAIL` after previous `OK` is normally a regression.

A current `OK` after previous `FAIL` is normally an improvement.

Comparisons across incompatible schema or GF object-format versions must be marked incompatible rather than silently equated.

---

## 43. Compile contract API

Canonical public responsibility:

```python
def compile_file(
    file_path: Path,
    run_config: RunConfig,
    run_paths: RunPaths,
) -> CompileSummary:
    ...
```

Related public responsibilities:

```python
def build_gf_args(
    file_path: Path,
    run_config: RunConfig,
    run_paths: RunPaths,
) -> list[str]:
    ...
```

```python
def probe_gf_version(
    run_config: RunConfig,
    run_paths: RunPaths,
) -> str:
    ...
```

Final implementation may introduce stronger typed request and result models, but it must preserve:

- explicit source target;
- explicit resolved configuration;
- explicit run-owned paths;
- structured result;
- raw evidence;
- no report generation;
- no downstream classification.

---

## 44. Recommended final internal decomposition

A balanced final implementation may use:

```text
compiler.py
    build_compile_request(...)
    build_compile_args(...)
    compile_file(...)
    verify_compile_artifacts(...)

gf_utils.py
    parse_compile_summary(...)
    normalize_gf_diagnostic(...)

process_utils.py
    run_process_with_timeout(...)

path_utils.py
    relative_to_project_root(...)
    safe_name(...)

models.py
    CompileRequest
    ProcessResult
    CompileSummary
    ArtifactCheck
```

This decomposition is recommended, not mandatory.

The interfile contracts are mandatory.

Avoid unnecessary abstractions such as:

- one class per GF flag;
- a plugin system for one compiler;
- a custom GF parser;
- a generic workflow engine;
- an event bus for compile results;
- a cross-run cache before reproducibility rules exist.

---

## 45. Error-kind mapping

Recommended mapping:

| Condition | Error kind |
|---|---|
| success | `OK` |
| recognized GF type error | `TYPE` |
| recognized GF syntax error | `SYNTAX` |
| recognized GF internal failure | `INTERNAL` |
| timeout | `TIMEOUT` |
| invalid compile configuration | `CONFIG` |
| output or source I/O failure | `IO` |
| executable or unsupported-option failure | `TOOL` |
| scenario-only error | `SCRIPT` |
| unrecognized compile failure | `OTHER` |

`SCRIPT` is normally not produced by ordinary module compilation.

---

## 46. Failure-class mapping

External integration failure classes:

```text
launch_failure
timeout
gf_compile_failure
artifact_failure
diagnostic_parse_failure
contract_failure
```

These are descriptive failure classes, not validation-status enum values.

Recommended mapping:

| Failure class | Status | Execution state |
|---|---|---|
| `launch_failure` | `ERROR` | `launch_failed` |
| `timeout` | `ERROR` | `timed_out` |
| `gf_compile_failure` | `FAIL` | `completed` |
| `artifact_failure` | `FAIL` or `ERROR` by policy | `completed` |
| `diagnostic_parse_failure` | `ERROR` | `completed` |
| `contract_failure` | `ERROR` | context-dependent |

---

## 47. Required unit tests

Minimum unit-test set:

```text
test_build_args_uses_batch
test_build_args_uses_silent_by_default
test_build_args_omits_silent_in_verbose_diagnostic_mode
test_source_argument_is_last
test_arguments_are_ordered
test_explicit_gf_path_is_preserved
test_artifact_flags_require_capability
test_cpu_flag_disabled_by_default
test_cpu_flag_enabled_explicitly
test_compile_creates_output_directories
test_compile_uses_project_root_as_cwd
test_compile_uses_configured_executable
test_compile_uses_configured_timeout
test_compile_captures_stdout_and_stderr_separately
test_compile_returns_compile_summary
test_nonzero_exit_is_not_ok
test_zero_exit_with_fatal_diagnostic_is_not_ok
test_timeout_is_error
test_launch_failure_is_error
test_no_compile_is_skipped
test_parser_failure_preserves_raw_logs
test_target_outside_project_is_rejected
test_path_with_spaces_is_one_argument
test_unicode_path_is_supported
test_safe_file_key_is_deterministic
test_duplicate_basenames_get_distinct_logs
test_stale_gfo_does_not_count
test_required_gfo_missing_fails_artifact_check
test_current_gfo_is_manifested
```

---

## 48. Required diagnostic parser tests

Minimum fixtures:

```text
successful silent compile
successful verbose compile
syntax error on stdout
syntax error on stderr
type error with expected/inferred detail
internal GeneratePMCFG error
unresolved module
non-zero exit with generic message
non-zero exit with no message
zero exit with fatal text
timeout with partial output
Unicode diagnostic
Windows path in diagnostic
multiple diagnostics
progress lines before first error
```

Assertions:

- raw message remains available;
- first error selection is deterministic;
- error kind is correct;
- non-zero exit never becomes `OK`;
- fatal text is not ignored;
- dependency paths remain parseable by the classifier;
- parser does not rewrite evidence.

---

## 49. Required integration tests

Integration tests with a real supported GF installation SHOULD cover:

```text
minimal valid abstract module
minimal valid concrete module
resource module
interface and instance pair
module importing project dependency
module importing RGL dependency
syntax error
type error
missing import
target path containing spaces
project root containing spaces
RGL path containing spaces
isolated gfo output
target gfo existence
dependency gfo production
repeat compile in a fresh run
compile after source modification
compile with stale source-tree gfo present
version probe and compile use same executable
```

Release integration tests for `.pgf` belong to `GF_PGF_BUILD.md`.

---

## 50. Fake-process testing

Most unit tests SHOULD use a fake or injected process runner.

A fake process result must be able to model:

```text
successful completion
non-zero completion
timeout
cancellation
launch failure
stdout-only output
stderr-only output
both streams
empty streams
duration
artifact creation
artifact omission
```

Tests must not depend on a developer’s global GF installation unless explicitly marked as integration tests.

---

## 51. Acceptance criteria

The compilation subsystem is complete when:

```text
[ ] canonical per-file command uses batch compilation without PGF make mode
[ ] PGF construction is implemented separately
[ ] GF executable is explicit and recorded
[ ] GF path is deterministic and recorded
[ ] working directory is explicit
[ ] source argument is final
[ ] shell execution is disabled
[ ] stdout and stderr are captured separately
[ ] raw logs are written before diagnostic parsing
[ ] timeout is enforced
[ ] launch failure is distinct from GF failure
[ ] skipped compile is distinct from success
[ ] CompileSummary fields are coherent
[ ] compiler does not classify downstream failures
[ ] required `.gfo` artifacts are verified
[ ] stale artifacts cannot satisfy current-run checks
[ ] artifacts are registered in the manifest
[ ] path-with-spaces tests pass on Windows
[ ] diagnostic parser fixtures pass
[ ] real-GF integration tests pass for supported versions
[ ] documentation and lock files agree
```

---

## 52. Common failure examples

## 52.1 Syntax error

Evidence:

```text
process launched
exit code non-zero
syntax diagnostic present
```

Result:

```text
status = FAIL
execution_state = completed
error_kind = SYNTAX
```

## 52.2 Type error

Evidence:

```text
expected/inferred diagnostic present
```

Result:

```text
status = FAIL
execution_state = completed
error_kind = TYPE
```

## 52.3 Missing dependency

Evidence:

```text
GF cannot resolve imported module
```

Result before global classification:

```text
status = FAIL
diagnostic_class = ambiguous
error_kind = OTHER
```

The classifier may later assign:

```text
diagnostic_class = downstream
blocked_by = [...]
```

## 52.4 Timeout

Evidence:

```text
process exceeded configured timeout
```

Result:

```text
status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
```

## 52.5 Missing executable

Evidence:

```text
process did not launch
```

Result:

```text
status = ERROR
execution_state = launch_failed
error_kind = TOOL
```

## 52.6 Missing target `.gfo`

Evidence:

```text
GF returned success
required artifact not present
```

Result:

```text
status = FAIL or ERROR according to artifact policy
failure_class = artifact_failure
```

Release-significant validation MUST NOT pass.

## 52.7 Explicit compile skip

Evidence:

```text
resolved configuration disables compilation
```

Result:

```text
status = SKIPPED
diagnostic_class = skipped
```

No GF success is claimed.

---

## 53. Troubleshooting order

When compilation fails, inspect in this order:

1. resolved GF executable;
2. recorded GF version;
3. selected source path;
4. working directory;
5. resolved GF path;
6. exact ordered arguments;
7. stdout log;
8. stderr log;
9. exit code and execution state;
10. parsed error kind and first error;
11. expected `.gfo` path;
12. artifact manifest;
13. dependency classification;
14. previous-run comparison.

Do not begin by editing gold files or reports. They are not compilation inputs.

---

## 54. Anti-drift rules

Compilation drift exists when:

- `compiler.py` builds arguments differently from this document;
- CLI and GUI produce different GF paths for equivalent inputs;
- `-make` reappears in per-file compilation;
- source argument is no longer final;
- stdout and stderr are merged before raw capture;
- skipped compilation is reported as `OK`;
- report code reparses GF output independently;
- artifact directories differ from `RunPaths`;
- a stale `.gfo` counts as current evidence;
- `CompileSummary` fields change without updating schemas and consumers;
- compiler begins assigning `downstream`;
- timeout behavior differs between compiler and scenario runner without documented reason;
- a new GF flag is used without capability and integration testing.

Any such change requires coordinated updates to:

```text
compiler
process runner
models
configuration
artifact paths
diagnostic parser
tests
contract locks
this document
migration notes
```

---

## 55. Cross-references

| Topic | Document |
|---|---|
| External GF command contract | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Python compiler boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| Persisted compile fields | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Toolchain overview | `docs/gf/GF_TOOLCHAIN_INTEGRATION.md` |
| GF path construction | `docs/gf/GF_PATH_RESOLUTION.md` |
| PGF construction | `docs/gf/GF_PGF_BUILD.md` |
| Version policy | `docs/gf/GF_VERSION_COMPATIBILITY.md` |
| File selection | `docs/validation/FILE_SELECTION.md` |
| Compilation validation | `docs/validation/COMPILATION_VALIDATION.md` |
| Error parsing | `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md` |
| Process failures | `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md` |
| Artifact model | `docs/architecture/ARTIFACT_MODEL.md` |
| Status values | `docs/reference/STATUS_VALUES.md` |
| Active-project modules | `project/docs/INTERFILE_CONTRACT_LOCK.md` |

---

## 56. Official GF basis

This document follows the official GF distinction between:

```text
gf -batch -s <source.gf>
```

for batch source-to-object compilation, and:

```text
gf -make -optimize-pgf <concrete-entrypoints...>
```

for optimized PGF construction.

It also follows the GF compilation model:

```text
.gf source modules
    → .gfo object modules
    → .pgf runtime grammar
```

Primary references:

- [GF Shell Reference — The GF batch compiler](https://www.grammaticalframework.org/doc/gf-shell-reference.html)
- [GF Language Reference Manual](https://www.grammaticalframework.org/doc/gf-refman.html)
- [Grammatical Framework Tutorial](https://www.grammaticalframework.org/doc/tutorial/gf-tutorial.html)

The selected GF executable’s own:

```text
gf -help
```

output remains authoritative for version-specific optional flags.

---

## 57. Final rule

> A GF module compile is successful only when GF executed the canonical batch-compilation contract, its raw evidence was preserved, its result was interpreted coherently, and every required current-run artifact check passed.

A successful `.gfo` compilation is necessary evidence for many workflows.

It is not, by itself, proof of scenario correctness or release readiness.
