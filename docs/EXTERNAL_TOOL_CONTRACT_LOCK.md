# GF Wordbench — External Tool Contract Lock

**Document ID:** `GF-WB-EXT-TOOL-LOCK`  
**Status:** Normative  
**Applies to:** GF Wordbench framework and the active language project  
**Scope:** Contracts between GF Wordbench and external executables, runtimes, operating-system services, filesystems, shells and tool-produced artifacts  
**Primary target:** Grammatical Framework (`gf` / `gf.exe`)  
**Owner:** GF Wordbench maintainers  
**Contract version:** `1.0.0`  
**Schema version:** `1`  

---

## 1. Purpose

This document prevents drift between GF Wordbench and the external tools it invokes.

An external-tool integration is a contract. GF Wordbench sends a request through:

- an executable path;
- command-line arguments;
- a working directory;
- environment variables;
- standard input;
- source files;
- scenario files.

The tool responds through:

- an exit code;
- standard output;
- standard error;
- generated files;
- modified files;
- process duration;
- timeout or termination behavior.

A locally reasonable change can still break the integration when one side changes without the other. This document locks the observable boundary.

It does not reproduce GF internals. It specifies only what GF Wordbench is allowed to request, what evidence it must capture, and how it must interpret the response.

---

## 2. Core rule

> No external-tool command may be changed in isolation.

A change to an external-tool contract is complete only when all affected elements are updated together:

1. command builder;
2. process runner;
3. configuration model;
4. result model;
5. diagnostic parser;
6. artifact paths;
7. unit tests;
8. integration tests;
9. fixtures or gold files;
10. this contract lock;
11. compatibility or migration notes.

The external tool remains authoritative for its own semantics. GF Wordbench remains authoritative for orchestration, evidence capture, classification and reporting.

---

## 3. Normative language

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: required unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **LOCKED**: part of the external boundary.
- **RAW EVIDENCE**: unmodified stdout, stderr, exit status and produced artifacts.
- **NORMALIZED EVIDENCE**: stable representation derived from raw evidence.
- **TOOL FAILURE**: the external tool ran and reported failure.
- **LAUNCH FAILURE**: GF Wordbench could not start the external tool.
- **CONTRACT FAILURE**: execution completed, but the response violated an expected boundary.
- **VALIDATION FAILURE**: the tool ran correctly, but the language project failed the requested validation.

---

## 4. Scope

This lock governs:

- `gf` and `gf.exe`;
- GF version probing;
- GF batch compilation;
- PGF construction;
- GF shell execution;
- `.gfs` scenarios;
- parsing;
- linearization;
- generation;
- morphology and grammar introspection;
- process launching;
- standard input, output and error;
- timeouts and process termination;
- current working directories;
- environment variables;
- Windows executable and path handling;
- `.gfo`, `.pgf`, `.out`, `.err` and normalized scenario artifacts;
- optional external tools added later.

This lock does not govern:

- Python-to-Python contracts;
- internal GF implementation;
- the contents of a language module;
- persistent JSON or TOML schemas;
- module-to-module GF contracts;
- GUI layout;
- human report prose.

Those belong to other contract locks.

---

## 5. Authority boundaries

### 5.1 GF is authoritative for

- GF syntax and type checking;
- module loading;
- dependency resolution;
- `.gf` to `.gfo` compilation;
- `.pgf` construction;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF diagnostics.

### 5.2 GF Wordbench is authoritative for

- command construction;
- tool selection;
- executable discovery;
- working directory;
- environment preparation;
- timeouts;
- stdout and stderr capture;
- artifact collection;
- output normalization;
- scenario assertions;
- gold comparison;
- failure classification;
- run history;
- reports.

### 5.3 Forbidden duplication

GF Wordbench MUST NOT implement a competing version of:

- the GF parser;
- the GF type checker;
- the GF module resolver;
- the GF generation engine;
- the GF runtime;
- the PGF format;
- GF shell command semantics.

Static source scans MAY identify suspicious patterns, but they MUST remain distinct from GF execution truth.

---

## 6. Contract identifiers

Every external contract MUST use a stable identifier.

Format:

```text
EXT-<DOMAIN>-<NUMBER>
```

Domains used by this document:

```text
EXT-GF
EXT-PROC
EXT-FS
EXT-ENV
EXT-WIN
EXT-OPTIONAL
```

Contract identifiers MUST NOT be reused after retirement.

---

## 7. Required fields for every external contract

Each contract entry MUST define:

| Field | Requirement |
|---|---|
| Contract ID | Stable identifier |
| Status | `active`, `experimental`, `deprecated`, `retired` |
| Tool | Executable or operating-system service |
| Purpose | Why the contract exists |
| Request owner | GF Wordbench component constructing the request |
| Executable | How the program is selected |
| Arguments | Ordered argument contract |
| Working directory | Required process directory |
| Environment | Required or optional variables |
| Standard input | Input mode and encoding |
| Standard output | Capture and interpretation |
| Standard error | Capture and interpretation |
| Exit semantics | Meaning and limitations |
| Timeout | Required limit and behavior |
| Artifacts | Files expected or permitted |
| Normalization | Stable transformations allowed |
| Success criteria | Conditions for success |
| Failure classes | Tool, launch, timeout, contract or validation failure |
| Security rules | Quoting, shell, untrusted inputs |
| Tests | Required proof |
| Compatibility | Version and migration rules |

---

# 8. Global external-tool invariants

## 8.1 Explicit executable rule

The selected GF executable MUST be represented by an explicit path in the resolved run configuration.

Using `gf` from `PATH` MAY be supported as a convenience, but the resolved executable used for a run MUST be recorded.

Reports MUST show the executable actually invoked.

## 8.2 No implicit shell rule

External processes SHOULD be launched without an intermediate command shell.

Preferred model:

```python
subprocess.run(
    [executable, *args],
    shell=False,
)
```

GF Wordbench MUST NOT build one unquoted command string for normal GF execution.

Shell execution MAY be used only for a specifically documented external contract.

## 8.3 Ordered argument rule

Arguments MUST be represented as an ordered list.

The logged command MUST preserve:

- executable;
- argument order;
- argument values;
- working directory.

A human-readable rendered command MAY be produced for reports, but it MUST NOT replace the structured command.

## 8.4 Explicit working-directory rule

Every process invocation MUST define a working directory.

The working directory MUST NOT depend on:

- the terminal that launched GF Wordbench;
- the current GUI process directory;
- the location of a launcher shortcut;
- an IDE default.

## 8.5 Raw-evidence rule

Stdout and stderr MUST be captured separately before any normalization.

For every execution, GF Wordbench SHOULD preserve:

- command;
- working directory;
- environment overrides;
- start time;
- end time;
- duration;
- exit code;
- timeout state;
- launch error;
- stdout path;
- stderr path;
- artifact list.

## 8.6 No stdout-only rule

Success or failure MUST NOT be inferred from stdout alone.

GF versions and platforms may place diagnostics on stdout, stderr or both.

Diagnostic interpretation MUST consider both streams while preserving them separately.

## 8.7 Exit-code caution rule

An exit code is evidence, not the complete diagnosis.

A zero exit code MUST NOT override:

- missing required markers;
- absent required artifacts;
- fatal diagnostic text;
- an incomplete `.gfs` scenario;
- a failed gold comparison.

A non-zero exit code normally indicates failure, but raw diagnostics MUST still be retained.

## 8.8 Timeout rule

Every external process MUST have a finite timeout.

Timeouts MUST be configurable by operation class:

- version probe;
- file compilation;
- PGF build;
- scenario;
- generation;
- diagnostic introspection.

A timeout MUST be distinguishable from:

- tool-reported failure;
- launch failure;
- user cancellation;
- contract failure.

## 8.9 Termination rule

When a timeout occurs, GF Wordbench MUST attempt to terminate the process and its owned child processes according to the platform policy.

The result MUST record:

```text
timed_out = true
```

A timed-out execution MUST NOT be reported as a normal GF failure.

## 8.10 Encoding rule

GF Wordbench MUST use an explicit encoding policy for:

- stdin;
- stdout;
- stderr;
- `.gfs` files;
- `.gold` files;
- normalized output.

UTF-8 is the framework default.

Decoding errors MUST use a documented strategy and MUST NOT silently discard bytes.

## 8.11 Artifact ownership rule

GF Wordbench owns the run directory and captured evidence.

GF owns tool-generated grammar artifacts during execution.

GF Wordbench MAY copy or catalog generated artifacts, but it MUST NOT rewrite them while presenting them as raw GF output.

## 8.12 Source immutability rule

Normal validation MUST NOT modify:

- `.gf` source files;
- `.gfs` scenario files;
- `.gold` files;
- project documentation.

Updating a gold file MUST require an explicit command or mode.

## 8.13 Determinism rule

Commands, artifact lists and normalized outputs SHOULD be deterministic.

Unstable values MAY be normalized only when listed in the normalization policy.

## 8.14 Evidence-before-parsing rule

Raw output files MUST be written before diagnostic parsing or scenario comparison.

A parser failure MUST NOT destroy the underlying external-tool evidence.

---

# 9. External tool registry

| Contract | Tool/service | Purpose | Status |
|---|---|---|---|
| `EXT-GF-001` | GF executable | Discovery and validation | Active |
| `EXT-GF-002` | `gf --version` | Version probe | Active |
| `EXT-GF-003` | GF batch compiler | Module compilation | Active |
| `EXT-GF-004` | GF make mode | PGF build | Planned |
| `EXT-GF-005` | GF shell | `.gfs` scenario execution | Planned |
| `EXT-GF-006` | GF shell `import` | Grammar loading | Planned |
| `EXT-GF-007` | GF shell `parse` | Parsing validation | Planned |
| `EXT-GF-008` | GF shell `linearize` | Linearization validation | Planned |
| `EXT-GF-009` | GF shell generation | Bounded generation | Planned |
| `EXT-GF-010` | GF shell introspection | Grammar diagnostics | Planned |
| `EXT-PROC-001` | OS process service | Process launch and capture | Active |
| `EXT-PROC-002` | OS process service | Timeout and termination | Active |
| `EXT-FS-001` | Filesystem | Paths and artifact writes | Active |
| `EXT-ENV-001` | Process environment | GF path and locale | Active |
| `EXT-WIN-001` | Windows | Executable and launcher behavior | Active |
| `EXT-OPTIONAL-001` | Optional tools | Controlled future integration | Reserved |

---

# 10. GF executable contracts

## EXT-GF-001 — GF executable discovery and validation

**Status:** Active

**Tool**

```text
gf
gf.exe
```

**Request owner**

```text
configuration loader
bootstrap
CLI/GUI validators
```

**Request**

A configured executable path or a resolvable executable name.

**Locked invariants**

- The resolved executable MUST exist before a required GF validation begins.
- On Windows, a configured executable SHOULD resolve to a regular file.
- The resolved path MUST be recorded in the run configuration.
- The path MUST be passed to the process API as an executable field, not concatenated into an argument string.
- A missing executable MUST produce a configuration or launch failure.
- A selected file that exists but cannot execute MUST produce a launch failure.
- GF Wordbench MUST NOT silently substitute a different GF installation after configuration is resolved.

**Allowed resolution order**

1. explicit CLI value;
2. explicit GUI value;
3. project configuration;
4. environment-configured value;
5. optional `PATH` discovery;
6. failure.

The final implementation MAY use a different order only if documented consistently.

**Success criteria**

- executable resolution succeeds;
- version probing can start the executable, unless the probe was explicitly skipped.

**Required tests**

- valid executable path;
- missing executable;
- directory passed as executable;
- path containing spaces;
- non-executable file where the platform can detect it;
- `PATH` fallback, if supported.

---

## EXT-GF-002 — GF version probe

**Status:** Active

**Request**

```text
<gf-executable> --version
```

**Working directory**

Resolved project root.

**Timeout**

Default: `10 seconds`.

The version-probe timeout is separate from compilation and scenario timeouts.

**Capture**

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

or the corresponding paths defined by `RunPaths`.

**Interpretation**

Preferred version text:

1. first non-empty stdout line;
2. otherwise first non-empty stderr line;
3. otherwise `UNKNOWN`.

Timeout result:

```text
TIMEOUT
```

**Locked invariants**

- Version probing MUST NOT compile project files.
- Version probing MUST preserve both output streams.
- Failure to identify a version MUST NOT be represented as successful version detection.
- A skipped probe MUST be explicitly recorded.
- The exact returned version text MUST be preserved or referenced.
- Compatibility checks MUST use a normalized version field, not report prose.

**Failure classes**

```text
launch_failure
timeout
unknown_version
unsupported_version
```

**Compatibility policy**

GF Wordbench SHOULD support a declared minimum and tested-version range.

A version outside the tested range MAY run with a warning unless a known incompatibility requires rejection.

---

# 11. GF compilation contracts

## EXT-GF-003 — GF source module compilation

**Status:** Active

**Purpose**

Compile one GF source target and capture authoritative GF diagnostics.

**Request owner**

```text
app/audit/compiler.py
```

**Normative target command**

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

`-s` MAY be omitted in diagnostic mode when verbose output is required.

**Compatibility command**

During migration from the earlier audit tool, the implementation MAY temporarily combine supported compilation flags already used by that tool. The resolved command MUST always be recorded.

**Path options**

GF Wordbench MAY provide:

```text
--gf-lib-path=<rgl-root>
--path=<gf-search-path>
```

or the equivalent supported by the selected GF version.

**Artifact options**

GF Wordbench MAY provide:

```text
--gfo-dir=<run-gfo-dir>
--output-dir=<run-output-dir>
```

when supported and validated.

**Optional performance option**

```text
--cpu
```

MUST be enabled only by explicit configuration.

**Working directory**

Resolved GF project root.

**Standard input**

None.

**Timeout**

Configured per-file compilation timeout.

**Raw output**

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
```

**Expected artifacts**

Zero or more:

```text
.gfo
```

Other artifacts MAY be produced by GF depending on arguments and module role.

**Success criteria**

All applicable conditions:

- process launched;
- process did not time out;
- exit code indicates success;
- no fatal diagnostic was recognized;
- required artifact checks pass when enabled.

**Locked invariants**

- The source file path MUST be the final source argument.
- The exact GF path MUST be reproducible from recorded configuration.
- Output directories MUST exist before invocation when GF requires them.
- Stdout and stderr MUST be captured separately.
- Compilation MUST return a structured result.
- A skipped compile MUST be distinct from a successful invocation.
- The compiler MUST NOT classify dependency cascades.
- The compiler MUST NOT generate user-facing reports.
- The compiler MUST NOT mutate the source file.
- Parsing diagnostics MUST not replace raw logs.

**Failure classes**

```text
launch_failure
timeout
gf_compile_failure
artifact_failure
diagnostic_parse_failure
contract_failure
```

**Required tests**

- successful compile using a fake process result;
- non-zero exit;
- timeout;
- stdout-only diagnostic;
- stderr-only diagnostic;
- paths containing spaces;
- explicit GF path;
- automatic GF path;
- missing output directory creation;
- no-compile mode;
- CPU flag enabled and disabled.

---

## EXT-GF-004 — PGF release build

**Status:** Planned

**Purpose**

Build the final Portable Grammar Format artifact from one or more top-level concrete grammars.

**Normative command**

```text
<gf> -make -optimize-pgf <path-options> <entrypoint-1> [<entrypoint-N>...]
```

Optimization MAY be disabled in diagnostic mode.

**Inputs**

- one abstract family;
- one or more compatible top-level concrete modules;
- project entrypoints declared in project configuration.

**Working directory**

Resolved project root.

**Timeout**

Separate release-build timeout.

**Expected artifact**

```text
<grammar-name>.pgf
```

The expected path and filename MUST be declared or deterministically derived.

**Success criteria**

- process launched;
- no timeout;
- successful exit;
- no fatal diagnostic;
- expected `.pgf` exists;
- `.pgf` is non-empty;
- artifact is registered in the run manifest.

**Locked invariants**

- File compilation and PGF release build are distinct validation stages.
- A project MUST NOT be declared release-ready solely from individual `.gfo` success.
- Entrypoint ordering MUST be deterministic.
- The PGF artifact MUST be copied or generated inside an owned run/output location.
- Release mode MUST not overwrite a previous release artifact without an explicit policy.
- The build command and GF version MUST be recorded.

**Required tests**

- successful PGF build;
- missing PGF despite zero exit;
- incompatible entrypoints;
- timeout;
- artifact collision;
- optimized and non-optimized modes.

---

# 12. GF shell and scenario contracts

## EXT-GF-005 — Native `.gfs` scenario execution

**Status:** Planned

**Purpose**

Execute reproducible GF shell scenarios without implementing a custom GF interpreter.

**Preferred invocation**

One of the following supported mechanisms:

```text
<gf> < scenario.gfs
```

or:

```text
<gf>
stdin = contents of scenario.gfs
```

The implementation SHOULD use direct process stdin rather than a platform shell redirection operator.

**Request owner**

```text
app/audit/scenario_runner.py
```

**Inputs**

- scenario identifier;
- `.gfs` path;
- resolved project root;
- resolved GF executable;
- GF path configuration;
- timeout;
- optional gold path;
- normalization rules;
- required or optional flag.

**Working directory**

Scenario-declared directory or resolved project root.

**Standard input**

UTF-8 scenario content.

**Raw output**

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

**Normalized output**

```text
scenarios/<scenario-id>.normalized.txt
```

**Locked invariants**

- The `.gfs` file MUST remain an external project asset.
- GF Wordbench MUST not reinterpret GF command syntax.
- Raw output MUST be saved before normalization.
- Scenario execution MUST have a finite timeout.
- Required and optional scenarios MUST be distinct.
- Normal execution MUST NOT modify `.gfs` or `.gold`.
- A zero exit code is insufficient when required markers or artifacts are missing.
- The executed scenario hash SHOULD be recorded.
- Scenario identifiers MUST be unique.
- Scenario order MUST be deterministic.
- Interactive prompts MUST be prohibited or explicitly handled.

**Scenario termination**

A scenario SHOULD end with:

```text
q
```

when required by the selected GF execution mode.

**Required markers**

GF Wordbench scenarios SHOULD emit stable markers using `ps` or an equivalent GF command:

```text
GF_WORDBENCH_BEGIN <section-id>
GF_WORDBENCH_END <section-id>
```

The exact marker syntax MUST be documented by the scenario-format specification.

**Success criteria**

- process launched;
- no timeout;
- exit policy passed;
- required markers completed;
- fatal diagnostic checks passed;
- required artifacts exist;
- gold comparison passed when required.

---

## EXT-GF-006 — Grammar import and load validation

**Status:** Planned

**GF shell command**

```text
import <module-or-grammar>
```

Short form MAY be:

```text
i <module-or-grammar>
```

**Optional flag**

```text
-retain
```

MAY be used when later scenario commands require retained source operations.

**Purpose**

Prove that a target grammar or module can be loaded in the GF shell.

**Locked invariants**

- Import targets MUST come from project configuration or scenario input.
- Import success MUST be evaluated from captured evidence, not only exit code.
- `-retain` MUST be used only when required by later introspection.
- The scenario MUST identify the imported target.
- A higher-level grammar load is a separate proof from compiling one source file.

---

## EXT-GF-007 — Parse validation

**Status:** Planned

**GF shell command**

```text
parse
```

Short form:

```text
p
```

**Inputs**

- language;
- category where required;
- UTF-8 text;
- loaded grammar.

**Allowed options**

Project scenarios MAY use documented GF options such as:

```text
-lang=<language>
-cat=<category>
```

**Success criteria**

Defined per scenario, for example:

- at least one parse;
- exactly one parse;
- expected tree present;
- no parse allowed for a negative test;
- parse count within a limit.

**Locked invariants**

- Input strings MUST be treated as scenario data, not shell fragments.
- Expected ambiguity MUST be declared.
- Parse success MUST not be inferred merely from absence of fatal errors.
- Linguistic expectations belong to the active project validation specification.
- Raw GF tree output MUST be retained before normalization.

---

## EXT-GF-008 — Linearization validation

**Status:** Planned

**GF shell command**

```text
linearize
```

Short form:

```text
l
```

**Inputs**

- abstract tree;
- target language where required;
- loaded grammar.

**Allowed options**

Project scenarios MAY use documented options such as:

```text
-lang=<language>
-all
-treebank
```

**Success criteria**

Defined per scenario:

- expected surface form;
- one of an approved set of variants;
- no empty output;
- no runtime error;
- stable gold output.

**Locked invariants**

- Trees MUST be supplied as scenario data or from a previous GF command.
- Normalization MUST not erase meaningful orthography.
- Variant ordering MUST be handled explicitly.
- Empty strings MUST be distinguishable from missing output.
- Linearization failures are validation failures, not compiler failures.

---

## EXT-GF-009 — Bounded generation validation

**Status:** Planned

**GF shell commands**

```text
generate_random
generate_trees
```

Short forms:

```text
gr
gt
```

**Required bounds**

Every generation scenario MUST define one or more finite bounds:

```text
-number=<integer>
-depth=<integer>
-cat=<category>
```

**Locked invariants**

- Unbounded generation is prohibited in automated validation.
- Random generation MUST record enough configuration to reproduce the request.
- If GF does not expose a stable random seed for the selected version, random output MUST NOT be used as an exact gold unless normalized through a deterministic projection.
- Exhaustive generation MUST use conservative depth and count limits.
- Generated trees MAY be piped to linearization.
- Resource consumption MUST be constrained by timeout and output-size limits.

**Success criteria**

Possible scenario assertions:

- no runtime failure;
- no empty linearization;
- expected number of outputs;
- no forbidden token;
- all generated trees linearize;
- generation completes within limits.

---

## EXT-GF-010 — Grammar and morphology introspection

**Status:** Planned

**Supported GF shell commands MAY include**

```text
abstract_info / ai
print_grammar / pg
morpho_analyse / ma
show_dependencies / sd
dependency_graph / dg
show_operations / so
show_source / ss
compute_concrete / cc
```

**Purpose**

Development diagnostics, not mandatory release behavior unless explicitly configured.

**Locked invariants**

- Commands requiring retained source MUST be preceded by import with `-retain`.
- Introspection output MUST be treated as diagnostic evidence.
- Introspection failures MUST not be misclassified as language compilation failures.
- External artifacts such as dependency graphs MUST be registered when produced.
- Optional system tools used to render graph output require separate contracts.

---

# 13. Process-service contracts

## EXT-PROC-001 — Process launch and capture

**Status:** Active

**External service**

Operating-system process API through Python.

**Request owner**

```text
app/utils/process_utils.py
```

**Required request fields**

```text
executable
args
cwd
stdout_path
stderr_path
timeout_sec
```

Future additions MAY include:

```text
stdin_path
stdin_text
environment_overrides
creation_flags
output_size_limit
```

**Required response fields**

```text
exit_code
timed_out
duration_ms
launch_error
```

The existing response MAY omit `launch_error` until the model is extended, but launch failures MUST remain distinguishable.

**Locked invariants**

- `args` MUST be a list.
- `cwd` MUST be explicit.
- stdout and stderr MUST be written to their owned paths.
- Parent directories MUST exist before execution.
- Duration MUST use a monotonic clock.
- Non-zero exit MUST still return captured output.
- Launch failure MUST preserve a useful error message.
- The process layer MUST NOT parse GF diagnostics.
- The process layer MUST NOT assign `direct` or `downstream`.
- The process layer MUST not generate reports.

**Security**

- `shell=False` SHOULD be used.
- Untrusted text MUST NOT be inserted into an OS command string.
- Scenario content SHOULD be delivered through stdin or a controlled file.
- Environment inheritance MUST be documented.

---

## EXT-PROC-002 — Timeout and termination

**Status:** Active

**Locked invariants**

- Timeout values MUST be positive when execution is enabled.
- Timeout measurement begins immediately before process launch.
- On timeout, GF Wordbench MUST attempt controlled termination.
- Child-process handling MUST be platform-aware.
- Partial stdout and stderr MUST be retained.
- Timeout MUST produce a structured timeout result.
- Timeout MUST not be converted into a generic non-zero-exit result.
- A terminated process MUST not continue writing into a completed run directory.

**Windows policy**

The implementation SHOULD use a process-group or tree-termination method when child processes are possible.

Any Windows-specific creation flags MUST be isolated in the process layer.

---

# 14. Filesystem contract

## EXT-FS-001 — External-tool paths and artifacts

**Status:** Active

**Locked path classes**

```text
project root
RGL root
GF executable
GF search path
run root
raw output root
compile log directory
scenario log directory
GFO directory
PGF/output directory
artifact directory
```

**Locked invariants**

- Source and output roots MUST be distinct unless explicitly supported.
- Run-owned directories MAY be created automatically.
- Source directories MUST NOT be created automatically to hide configuration errors.
- Paths passed to Python APIs use native `Path` objects.
- Paths serialized for reports use a documented normalized representation.
- Relative project paths resolve against the project root.
- Relative scenario paths resolve according to the project contract.
- Path traversal outside allowed roots MUST be rejected for run-owned output.
- Artifact filenames MUST be sanitized without destroying result identity.
- Filename collisions MUST be resolved deterministically.
- Existing artifacts MUST follow an explicit overwrite policy.
- The run manifest SHOULD record size and hash for important artifacts.

**Windows path rules**

- Spaces in paths MUST be supported.
- Drive letters MUST be handled.
- Mixed slash forms MAY be accepted at input but MUST be normalized internally.
- Command arguments MUST not add manual quotation characters when passed as a list.
- Long-path limitations SHOULD be detected or documented.

---

# 15. Environment contract

## EXT-ENV-001 — GF path, locale and inherited environment

**Status:** Active

**Potential inputs**

```text
GF_LIB_PATH
PATH
locale variables
temporary-directory variables
```

**Precedence**

Explicit resolved configuration MUST take precedence over inherited environment for correctness-critical values.

Recommended order for GF library resolution:

1. explicit GF path in run configuration;
2. project-configured path parts;
3. RGL root and detected standard subdirectories;
4. environment fallback, if enabled;
5. configuration failure.

**Locked invariants**

- The effective GF search path MUST be recorded.
- Environment-dependent behavior MUST be visible in diagnostic output.
- GF Wordbench MUST not silently rely on the developer machine's current `GF_LIB_PATH`.
- Environment overrides MUST be scoped to the child process.
- Locale settings MUST not make diagnostic decoding nondeterministic.
- Secrets MUST not be copied into reports.
- Full environment dumps are prohibited by default.

---

# 16. Windows contract

## EXT-WIN-001 — Windows execution and launchers

**Status:** Active

**Scope**

```text
gf.exe
python.exe
pythonw.exe
.bat launchers
Windows paths
process termination
GUI startup
```

**Locked invariants**

- Launchers are convenience entrypoints, not the source of audit semantics.
- CLI and GUI MUST resolve to the same Python package behavior.
- Launchers MUST set or resolve the repository root explicitly.
- Launchers MUST propagate meaningful exit codes where a console is present.
- `pythonw.exe` MAY be used for GUI startup.
- GF execution MUST not depend on a visible console.
- Paths containing spaces MUST work.
- Launcher-specific environment changes MUST be documented.
- The Python application MUST remain runnable without the batch launchers.
- Windows-only code MUST remain isolated from platform-neutral orchestration.

---

# 17. Output normalization contract

Normalization produces stable comparison material. It MUST NOT alter raw evidence.

## 17.1 Allowed normalization

GF Wordbench MAY normalize:

- CRLF to LF;
- trailing spaces;
- known prompts;
- stable scenario markers;
- absolute run-directory prefixes;
- temporary-directory prefixes;
- timestamps explicitly marked unstable;
- measured durations;
- platform path separators;
- documented version banners when a scenario is version-independent.

## 17.2 Forbidden normalization

GF Wordbench MUST NOT remove:

- GF error messages;
- source filenames relevant to diagnosis;
- line and column locations unless the scenario explicitly ignores them;
- abstract trees;
- linearized strings;
- ambiguity counts;
- missing-function lists;
- morphology results;
- semantically meaningful punctuation;
- Unicode distinctions relevant to the language;
- evidence that a required section did not run.

## 17.3 Versioning

Normalization rules MUST have a version.

A normalization change that alters existing gold comparisons is a contract change and requires:

- rule update;
- test update;
- deliberate gold review;
- migration note.

---

# 18. Exit and failure semantics

GF Wordbench MUST distinguish:

| State | Meaning |
|---|---|
| `OK` | Tool ran and validation criteria passed |
| `FAIL` | Tool ran, but validation criteria failed |
| `ERROR` | GF Wordbench could not execute or interpret the contract |
| `SKIPPED` | Operation intentionally not executed |
| `CANCELLED` | User or controlling system cancelled execution |

Recommended diagnostic kinds:

```text
tool_failure
launch_failure
timeout
contract_failure
artifact_failure
normalization_failure
gold_mismatch
configuration_failure
unsupported_version
```

`direct`, `downstream` and `ambiguous` remain higher-level audit classifications and MUST NOT be assigned by the process layer.

---

# 19. Artifact contract

## 19.1 Raw artifacts

Examples:

```text
gf_version.out.txt
gf_version.err.txt
<module>.out.txt
<module>.err.txt
<scenario>.out.txt
<scenario>.err.txt
```

Raw artifacts MUST be immutable after capture.

## 19.2 Tool-generated artifacts

Examples:

```text
.gfo
.pgf
.dot
generated export formats
```

These MUST be catalogued with:

- producing contract;
- command;
- path;
- size;
- optional hash;
- required or optional status.

## 19.3 Derived artifacts

Examples:

```text
normalized scenario output
gold diff
diagnostic summary
```

Derived artifacts MUST reference their raw source evidence.

## 19.4 Missing artifact behavior

A required artifact missing after an apparently successful process MUST produce:

```text
artifact_failure
```

It MUST NOT be silently accepted.

---

# 20. Version compatibility policy

GF Wordbench MUST maintain:

```text
minimum_supported_gf_version
tested_gf_versions
known_incompatible_gf_versions
```

These MAY be stored in framework configuration or compatibility documentation.

## 20.1 Unknown newer version

An unknown newer GF version SHOULD produce a warning and MAY proceed unless strict mode is enabled.

## 20.2 Older unsupported version

An older version below the minimum SHOULD fail before language validation.

## 20.3 Command capability checks

Where GF options vary by version, GF Wordbench SHOULD use one of:

- version-gated command construction;
- capability probe;
- documented compatibility adapter.

Silent fallback to different semantics is prohibited.

---

# 21. Security and trust boundaries

## 21.1 Untrusted paths

Project paths, scenario paths and input files MUST be validated before use.

## 21.2 Shell escape commands

GF shell commands that invoke operating-system commands MUST be prohibited in normal project scenarios unless explicitly enabled by policy.

This includes GF shell features capable of calling system commands or piping to system utilities.

## 21.3 Scenario trust

A `.gfs` scenario is executable input.

Scenario files from untrusted projects MUST be treated as untrusted code.

## 21.4 Environment leakage

Reports MUST NOT include:

- secrets;
- tokens;
- private environment values;
- complete environment dumps.

## 21.5 Output limits

GF Wordbench SHOULD enforce output-size limits to prevent:

- runaway generation;
- disk exhaustion;
- excessive report size.

Raw evidence truncation, when necessary, MUST be explicit and recorded.

---

# 22. Optional external-tool policy

A new external tool MUST NOT be integrated only because it is convenient.

It must provide a capability not already supplied sufficiently by:

- GF;
- Python standard library;
- existing GF Wordbench components.

Before adding a tool, document:

```text
tool name
tool version
purpose
why GF cannot provide the capability
license
installation method
platform support
command contract
inputs
outputs
timeouts
artifacts
failure semantics
security impact
fallback behavior
tests
```

Examples of possible future tools:

```text
Graphviz
PGF runtime executables
coverage tools
format validators
archive tools
```

Each requires its own `EXT-OPTIONAL-*` contract before becoming required.

---

# 23. Prohibited dependency behavior

The following are prohibited:

- report generators launching GF;
- GUI widgets launching GF directly;
- multiple modules building their own GF path differently;
- tests depending on a developer's global `GF_LIB_PATH`;
- shell command strings built from untrusted project text;
- normal runs rewriting `.gold`;
- treating a missing `.pgf` as success;
- interpreting zero exit as complete scenario success;
- hiding timeout as generic compilation failure;
- discarding stderr after reading stdout;
- parsing only human summary reports to recover tool results;
- using launcher behavior as the only supported execution path;
- changing normalization without reviewing gold files;
- language-specific command rules embedded in the framework process layer.

---

# 24. Drift indicators

Probable external-contract drift exists when:

- the logged command differs from the executed command;
- an option is added in one caller but not documented;
- GUI and CLI resolve different GF executables;
- GF path construction differs between compilation and scenarios;
- stdout is parsed but stderr is ignored;
- a process can run without timeout;
- a required artifact is no longer checked;
- a new GF version changes output and normalization hides the change;
- a `.gfs` script succeeds without completing required markers;
- gold files change during normal execution;
- a report reruns GF;
- a tool-generated file is modified before raw capture;
- environment values alter behavior without appearing in evidence;
- Windows launchers apply hidden settings;
- process launch errors are reported as GF syntax errors;
- random generation is used as an exact deterministic gold;
- shell escape commands appear in project scenarios without authorization.

Any drift indicator MUST trigger contract review.

---

# 25. Required tests

Recommended test structure:

```text
tests/contracts/
├── test_gf_executable_contract.py
├── test_gf_version_contract.py
├── test_gf_compile_contract.py
├── test_gf_pgf_build_contract.py
├── test_gf_scenario_contract.py
├── test_process_contract.py
├── test_timeout_contract.py
├── test_filesystem_contract.py
├── test_environment_contract.py
├── test_windows_contract.py
└── test_normalization_contract.py
```

## 25.1 Unit tests without real GF

Use fake executables or mocked process results to test:

- argument ordering;
- path handling;
- timeout representation;
- stream capture;
- artifact checks;
- exit semantics;
- normalization;
- gold comparison.

## 25.2 Integration tests with real GF

A small fixture grammar SHOULD test:

- version probe;
- successful module compile;
- failed module compile;
- PGF build;
- `.gfs` load;
- parse;
- linearize;
- bounded generation;
- timeout containment if safely testable.

Tests requiring real GF SHOULD be marked separately.

## 25.3 Platform tests

At minimum:

- Windows path with spaces;
- native Windows executable;
- CRLF input;
- UTF-8 language data;
- process timeout;
- missing executable.

---

# 26. Automated contract checking

GF Wordbench SHOULD eventually provide:

```text
gf-wordbench contracts check-external
```

The checker SHOULD verify:

1. configured GF executable resolves;
2. version probe contract passes;
3. required command options are supported;
4. project and RGL roots exist;
5. GF path is reproducible;
6. run output directories are writable;
7. process timeouts are positive;
8. scenario files are UTF-8 readable;
9. scenario identifiers are unique;
10. required gold files exist;
11. gold files are not writable during a read-only validation mode, where enforceable;
12. shell escape commands are absent unless allowed;
13. expected artifacts are inside approved roots;
14. normalization version is declared;
15. supported-version policy is declared.

Strict mode:

```text
gf-wordbench contracts check-external --strict
```

MAY reject untested GF versions and optional environment fallbacks.

---

# 27. Contract-change workflow

Any external-contract change MUST answer:

```text
Contract ID:
Current command:
New command:
Reason:
GF versions affected:
Platforms affected:
Inputs changed:
Outputs changed:
Artifacts changed:
Timeout changed:
Normalization changed:
Compatibility:
Migration:
Tests:
```

Required checklist:

```text
[ ] Request builder updated
[ ] Process runner reviewed
[ ] Configuration updated
[ ] Result model updated
[ ] Raw evidence paths reviewed
[ ] Diagnostic parsing reviewed
[ ] Artifact checks reviewed
[ ] Unit tests updated
[ ] Real-GF integration test updated
[ ] Gold files deliberately reviewed
[ ] Compatibility policy updated
[ ] This lock updated
```

---

# 28. Contract entry template

```markdown
## EXT-<DOMAIN>-<NUMBER> — <name>

**Status:** Active | Experimental | Deprecated | Retired

**Tool**

`<executable or service>`

**Purpose**

<why it exists>

**Request owner**

`path/to/component.py`

**Executable**

`<resolution rule>`

**Arguments**

```text
<ordered arguments>
```

**Working directory**

`<path rule>`

**Environment**

- variable;
- precedence.

**Standard input**

- source;
- encoding.

**Standard output**

- path;
- interpretation.

**Standard error**

- path;
- interpretation.

**Timeout**

`<duration and configuration>`

**Artifacts**

- required;
- optional.

**Success criteria**

- criterion;
- criterion.

**Failure classes**

- class;
- class.

**Locked invariants**

- invariant;
- invariant.

**Security rules**

- rule;
- rule.

**Compatibility**

<version/platform policy>

**Tests**

- `tests/...`
```

---

# 29. Upstream references

The following upstream documents define GF behavior used by this lock:

- GF Shell Reference;
- GF Developers Guide;
- GF Quick Start;
- GF Language Reference Manual;
- GF version release notes when compatibility differs.

Upstream documentation explains GF behavior. This file defines the GF Wordbench integration contract.

When upstream behavior and this lock conflict:

1. preserve raw evidence;
2. identify the affected GF version;
3. mark the contract incompatible or update it deliberately;
4. add a regression test;
5. do not silently normalize the conflict away.

---

# 30. Final enforcement rule

An external command is part of the architecture.

GF Wordbench does not own GF's implementation, but it owns every request it sends and every conclusion it draws from the response.

Therefore:

> No executable, argument, environment, stdin format, output interpretation, timeout, artifact expectation or normalization rule may change without coordinated contract review and validation.
