# GF Wordbench — PGF Build

**Document ID:** `GF-WB-GF-PGF-BUILD`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\gf\GF_PGF_BUILD.md`  
**Applies to:** PGF construction, verification, evidence capture and release gating  
**Owner:** GF Wordbench maintainers  
**Primary implementation owner:** `app/audit/compiler.py`  
**External contract:** `EXT-GF-004`  
**Project contracts:** `PIFC-ENTRY-003`, `PIFC-ARTIFACT-002`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines how GF Wordbench builds a Portable Grammar Format (`.pgf`) artifact from the active GF language project.

It specifies:

- when a PGF build is required;
- which project values are required;
- how the GF command is constructed;
- where GF writes temporary and final artifacts;
- how success and failure are determined;
- how stale artifacts are prevented;
- what evidence is retained;
- how the artifact enters the run manifest;
- which tests protect the build contract;
- which responsibilities remain with GF.

GF Wordbench does not implement a PGF compiler.

The core rule is:

> GF builds the PGF; GF Wordbench provides deterministic orchestration, isolation, verification, evidence and release policy.

---

## 2. Scope

This document governs:

- release-entrypoint resolution;
- ordered PGF input selection;
- GF search-path resolution as consumed by the PGF build;
- the `gf -make` invocation;
- optional PGF optimization;
- the PGF build timeout;
- the PGF output directory;
- expected artifact-name resolution;
- process and diagnostic evidence;
- artifact freshness checks;
- artifact hashing and manifest registration;
- PGF build results;
- release-gate integration;
- explicit publication or export after validation.

This document does not govern:

- GF source-language semantics;
- module implementation;
- `.gf` to `.gfo` checkpoint compilation in general;
- `.gfs` scenario syntax;
- parsing or linearization behavior;
- gold-output normalization;
- PGF runtime APIs;
- package publication outside GF Wordbench;
- project-specific entrypoint names.

Those subjects belong to their dedicated documents.

---

## 3. Authoritative sources and contracts

### 3.1 GF is authoritative for

GF owns:

- GF parsing and type checking;
- module dependency resolution;
- `.gf` to `.gfo` compilation;
- linking compatible top-level grammars;
- PGF construction;
- PGF optimization;
- PGF binary format;
- GF diagnostics;
- process exit behavior.

GF Wordbench MUST NOT infer that invalid GF source is valid because a heuristic scan passes.

### 3.2 GF Wordbench is authoritative for

GF Wordbench owns:

- project-entrypoint selection;
- command construction;
- working and output directories;
- process execution;
- timeout and cancellation;
- stdout and stderr capture;
- expected artifact path;
- stale-artifact prevention;
- success criteria;
- result classification;
- artifact hashing;
- run-manifest registration;
- release-gate decisions;
- publication policy.

### 3.3 Related normative documents

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/REPOSITORY_STRUCTURE.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/validation/RELEASE_GATES.md
docs/reports/ARTIFACT_MANIFEST.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/RELEASE_CRITERIA.md
project/docs/VALIDATION_SPEC.md
```

When this document and another normative document appear inconsistent, implementation MUST stop until the contract owners resolve the discrepancy.

---

## 4. GF compilation model

GF source modules use the `.gf` extension.

GF compiles source modules into `.gfo` object files and links compatible top-level grammar modules into a `.pgf` runtime grammar.

Conceptually:

```text
module-1.gf
module-2.gf
module-N.gf
       │
       ▼
module-1.gfo
module-2.gfo
module-N.gfo
       │
       ▼
grammar.pgf
```

A PGF represents:

```text
one abstract syntax
+ one or more compatible concrete syntaxes
```

A PGF build is therefore not equivalent to compiling one arbitrary file.

The selected top-level entrypoints MUST belong to the same abstract grammar family.

---

## 5. PGF build as a distinct validation stage

PGF construction is a dedicated stage.

It is separate from:

```text
static scanning
per-file compilation
checkpoint compilation
scenario execution
gold comparison
report generation
```

The distinction is required because:

- individual `.gfo` success does not prove final linking succeeds;
- compatible concrete syntaxes must agree on one abstract syntax;
- the expected `.pgf` may be missing even when some files compile;
- release optimization is PGF-specific;
- PGF artifact freshness must be proved independently;
- release scenarios must target the intended final grammar.

A project MUST NOT be declared release-ready solely because every selected `.gf` file compiled independently.

---

## 6. Validation-mode behavior

GF Wordbench defines four canonical modes:

```text
quick
checkpoint
diagnostic
release
```

### 6.1 Quick mode

Default behavior:

```text
PGF build: skipped
```

Quick mode MAY build a PGF only when the caller explicitly requests the PGF stage.

A quick run MUST NOT silently become a release build.

### 6.2 Checkpoint mode

Default behavior:

```text
PGF build: skipped
```

Checkpoint mode validates declared module layers.

A checkpoint MAY require a PGF only when the project explicitly defines that checkpoint as a PGF-producing gate.

### 6.3 Diagnostic mode

Default behavior:

```text
PGF build: optional
optimization: optional
```

Diagnostic mode may build an unoptimized PGF to reduce build cost or preserve diagnostic detail.

The result MUST clearly record whether optimization was enabled.

### 6.4 Release mode

Required behavior when the active project requires a PGF:

```text
PGF build: required
optimization: enabled by default
artifact verification: required
manifest registration: required
release scenarios: required according to project policy
```

If `release_requires_pgf` resolves to `true`, a skipped PGF build makes the release gate fail.

---

## 7. Required resolved project values

The PGF builder consumes an already validated project configuration.

It MUST NOT infer release identity from old runs, source-directory contents or GUI state.

The resolved configuration MUST provide:

```text
project identity
project root
source root
ordered GF search path
ordered release entrypoints
expected PGF filename
PGF-required policy
optimization policy
PGF build timeout
GF executable
GF version
run paths
```

The serialized field names belong to `PROJECT_TOML_REFERENCE.md` and `PERSISTED_SCHEMA_LOCK.md`.

This document locks the resolved meanings, not a competing TOML schema.

### 7.1 Release entrypoints

Release entrypoints MUST:

- be explicitly registered;
- be unique after path normalization;
- exist;
- use the `.gf` extension;
- resolve inside an approved source root;
- be ordered deterministically;
- belong to one compatible abstract family;
- be valid top-level grammar modules for the intended PGF.

### 7.2 Expected PGF filename

The expected PGF filename MUST be explicit in the resolved project contract.

It MUST:

- end with `.pgf`;
- contain a filename only;
- contain no directory separator;
- contain no `..`;
- be safe on supported filesystems;
- remain stable across equivalent builds;
- agree with the project interfile lock;
- agree with release scripts and consumers.

Example:

```text
GrammarTst.pgf
```

GF Wordbench MUST NOT search for “any new `.pgf` file” and accept the first match.

### 7.3 Build timeout

PGF construction has its own timeout.

It MUST NOT reuse a per-file timeout implicitly.

A project or framework default may define the timeout, but the resolved value MUST be:

```text
integer
greater than zero
finite
recorded in the run result
```

---

## 8. Canonical command

### 8.1 Release command shape

The canonical PGF build uses GF make mode:

```text
<gf> -make -optimize-pgf \
  --path=<resolved-gf-path> \
  --gfo-dir=<run-gfo-dir> \
  --output-dir=<run-pgf-dir> \
  <entrypoint-1.gf> [<entrypoint-N.gf>...]
```

On Windows, the process is created from an argument vector, not from a shell-concatenated command string.

Conceptual Python argument vector:

```python
[
    str(gf_executable),
    "-make",
    "-optimize-pgf",
    f"--path={gf_path}",
    f"--gfo-dir={gfo_dir}",
    f"--output-dir={pgf_dir}",
    str(entrypoint_1),
    str(entrypoint_n),
]
```

The exact compatible long-option spelling is centralized in the command builder and verified against supported GF versions.

### 8.2 Diagnostic command shape

When optimization is explicitly disabled:

```text
<gf> -make \
  --path=<resolved-gf-path> \
  --gfo-dir=<run-gfo-dir> \
  --output-dir=<run-pgf-dir> \
  <entrypoint-1.gf> [<entrypoint-N.gf>...]
```

### 8.3 Optional framework-owned flags

Additional flags MAY be emitted only when:

- supported by the detected GF version;
- owned by central configuration;
- documented in `EXTERNAL_TOOL_CONTRACT_LOCK.md`;
- covered by command-construction tests;
- recorded in the result.

Examples may include:

```text
silent output
CPU statistics
parallel compilation
explicit GF library path
```

A project file MUST NOT inject arbitrary raw command-line fragments.

### 8.4 Forbidden command construction

The following are prohibited:

```text
shell=True with interpolated project text
one unparsed command string
platform-specific manual quote insertion
entrypoint glob expansion by the shell
unvalidated environment-variable expansion
project-provided executable arguments
report modules constructing GF commands
GUI widgets invoking GF directly
```

---

## 9. Argument ordering

Command ordering is deterministic.

Canonical order:

1. GF executable;
2. make-mode flag;
3. optimization flag when enabled;
4. framework-owned stable options;
5. path options;
6. GFO output option;
7. PGF output option;
8. optional diagnostic flags;
9. ordered entrypoints.

Equivalent project inputs MUST produce the same logical argument sequence.

Ordering does not imply byte-identical PGF output across:

- different GF versions;
- different platforms;
- different runtime builds;
- different RGL versions.

GF Wordbench locks command determinism, not undocumented binary reproducibility.

---

## 10. Search-path handling

PGF construction uses the same authoritative GF path resolver as compilation and scenario loading.

There MUST be one implementation of GF path construction.

The resolved path MUST include only approved elements such as:

```text
active project source roots
required shared source roots
RGL roots
explicit project path parts
framework-approved compatibility roots
```

The path resolver MUST:

- normalize entries;
- preserve semantic order;
- remove exact duplicates without reordering;
- validate required directories;
- reject unsafe or unresolved entries;
- support spaces;
- produce a representation compatible with the active GF version;
- record the final resolved path.

The PGF builder MUST NOT append hidden language-specific paths.

Detailed policy belongs to `GF_PATH_RESOLUTION.md`.

---

## 11. Output isolation

### 11.1 Run-owned directories

Canonical PGF outputs belong to:

```text
run_<run-id>/artifacts/pgf/
```

GFO outputs used during the build belong to:

```text
run_<run-id>/artifacts/gfo/
```

Raw process evidence belongs to:

```text
run_<run-id>/raw/compile/
```

The persisted schema exposes these through stable artifact keys, including:

```text
gfo_dir
pgf_dir
```

### 11.2 Direct output

GF Wordbench SHOULD direct GF output to the run-owned directories through supported GF options.

It MUST NOT rely on the current source directory as the final artifact store.

### 11.3 Compatibility fallback

If a supported GF version cannot write PGF output directly to the run directory, any fallback strategy MUST be:

- explicitly defined in `GF_VERSION_COMPATIBILITY.md`;
- isolated;
- tested;
- atomic;
- freshness-safe;
- recorded in the result.

GF Wordbench MUST NOT silently search the project tree and copy a coincidentally matching PGF.

### 11.4 Source immutability

A normal PGF build MUST NOT modify:

```text
project/project.toml
project/docs/
project/validation/
GF source files
gold files
template files
previous run directories
```

GF-generated source-adjacent artifacts are prohibited when direct run-owned output is available.

---

## 12. Build preparation

Before launching GF, the builder MUST perform the following checks.

### 12.1 Configuration checks

```text
GF executable resolved
GF compatibility accepted
project configuration valid
release entrypoints non-empty
entrypoint paths valid
expected PGF filename valid
timeout valid
search path valid
run directories valid
optimization policy resolved
```

### 12.2 Directory checks

The builder MAY create run-owned output directories.

It MUST NOT create missing source directories to hide configuration errors.

Required run-owned directories:

```text
run root
raw compile log directory
GFO artifact directory
PGF artifact directory
```

### 12.3 Collision checks

The expected artifact path is:

```text
<run-pgf-dir>/<expected-pgf-filename>
```

Before execution:

- the path MUST resolve inside the run PGF directory;
- a directory at that path is an error;
- an existing file is an artifact collision;
- a previous run artifact MUST never be overwritten;
- the build MUST begin with no accepted artifact at the expected path.

Because every run has a unique directory, an existing expected artifact normally indicates retry state, corruption or an invalid run lifecycle.

### 12.4 Input fingerprint

A release PGF build SHOULD compute a build-input fingerprint from:

```text
project identity
canonical project configuration
ordered release entrypoints
hashes of selected project GF source files
resolved GF path identity
GF version
optimization mode
```

The fingerprint provides traceability.

It does not replace GF dependency resolution.

---

## 13. Process execution

The builder delegates process creation to `app/utils/process_utils.py`.

The process runner owns:

```text
argv execution
working directory
environment
stdin
stdout capture
stderr capture
timeout
cancellation
duration
exit code
launch failure
```

The PGF builder owns interpretation of that process result.

### 13.1 Working directory

The working directory MUST be explicitly resolved and recorded.

The canonical choice is the active project root unless the version-compatibility policy defines a tested isolated build directory.

The implementation MUST NOT inherit an arbitrary caller working directory.

### 13.2 Environment

The environment MUST be minimal and explicit where practical.

Relevant values MAY include:

```text
PATH
locale or encoding settings
GF-specific library environment
temporary directory
```

Tests MUST NOT depend on an undocumented developer-global `GF_LIB_PATH`.

### 13.3 Standard streams

Both stdout and stderr MUST be captured independently.

Neither stream may be discarded because the other contains diagnostics.

Canonical raw evidence:

```text
raw/compile/pgf-build.stdout.txt
raw/compile/pgf-build.stderr.txt
```

A merged human-readable log MAY also be produced, but it does not replace raw streams.

### 13.4 Timeout

On timeout:

- process termination is requested;
- descendant cleanup follows process-runner policy;
- partial output is not accepted;
- raw evidence is retained;
- execution state is `timed_out`;
- validation status is `ERROR` or `FAIL` according to the shared status policy;
- error kind is `TIMEOUT`.

### 13.5 Cancellation

User cancellation is distinct from timeout.

Cancellation MUST NOT be reported as successful validation.

The result records:

```text
execution_state = cancelled
```

The shared status model determines whether the validation status is `ERROR` or `SKIPPED`.

---

## 14. Artifact discovery

The builder knows the exact expected path before launch.

After GF exits, discovery is limited to:

```text
<run-pgf-dir>/<expected-pgf-filename>
```

The builder MUST NOT:

- accept another filename;
- select the newest PGF in a directory;
- search previous runs;
- accept a source-tree PGF;
- accept a zero-byte file;
- accept a pre-existing file;
- infer the artifact solely from stdout wording.

Unexpected PGF files in the output directory SHOULD be recorded as diagnostic evidence and SHOULD cause strict-mode failure.

---

## 15. Success criteria

A PGF build has validation status `OK` only when every condition below is true:

```text
process launch succeeded
execution was not cancelled
execution did not time out
GF exit code indicates success
no fatal diagnostic was classified
expected PGF path exists
expected path is a regular file
artifact was produced during the current build
artifact size is greater than zero
artifact can be opened for hashing
SHA-256 hash was computed
artifact metadata was recorded
artifact was registered in the run manifest
```

A zero exit code alone is insufficient.

Artifact existence alone is insufficient.

A valid old artifact is insufficient.

### 15.1 Optional load verification

A dedicated PGF-load scenario SHOULD verify that the produced PGF can be imported by the supported GF runtime.

That verification belongs to scenario validation.

The builder MUST NOT duplicate the complete scenario runner.

### 15.2 Release readiness

PGF build success is necessary but may not be sufficient for release.

Release readiness may additionally require:

```text
checkpoint gates
missing-linearization checks
parse scenarios
linearization scenarios
bounded generation
gold comparisons
known-issue review
manifest verification
```

---

## 16. Failure semantics

### 16.1 Configuration failure

Examples:

```text
no release entrypoint
missing entrypoint
invalid expected filename
invalid timeout
unresolved GF path
unsupported GF version
output path escapes run root
```

Result:

```text
error_kind = CONFIG
execution_state = not_started
validation_status = ERROR
```

No GF process is launched.

### 16.2 Launch failure

Examples:

```text
GF executable missing
permission denied
invalid executable format
operating-system process creation failure
```

Result:

```text
error_kind = TOOL or IO
execution_state = launch_failed
validation_status = ERROR
```

### 16.3 GF-reported build failure

Examples:

```text
syntax error
type error
missing module
incompatible abstract syntaxes
internal GF failure
```

Result:

```text
execution_state = completed
validation_status = FAIL or ERROR
```

The diagnostic parser assigns the most specific supported `error_kind`.

### 16.4 Contract failure after zero exit

Examples:

```text
expected PGF missing
expected PGF empty
artifact outside owned directory
artifact cannot be read
unexpected artifact name
manifest registration fails
```

Result:

```text
validation_status = ERROR
error_kind = IO, TOOL or INTERNAL
```

The exact classification follows shared error policy.

### 16.5 Partial artifact

A partial PGF produced by a failed, timed-out or cancelled build:

- MUST NOT be registered as a valid PGF;
- MUST NOT satisfy release gates;
- MAY be retained in the failed run directory as raw evidence;
- MUST be clearly marked invalid;
- MUST NOT be published.

---

## 17. Structured result

PGF build output MUST be represented as structured data before report generation.

A dedicated PGF build result SHOULD include at least:

```text
validation status
execution state
error kind
diagnostic class
ordered command arguments
display command
working directory
GF executable
GF version
ordered entrypoints
resolved search path
optimization enabled
timeout
started timestamp
finished timestamp
duration
exit code
stdout path
stderr path
expected artifact path
produced artifact path
artifact size
artifact SHA-256
build-input fingerprint
primary diagnostic
additional diagnostics
manifest registration state
```

This model belongs to shared runtime models.

Its serialized representation belongs to `PERSISTED_SCHEMA_LOCK.md`.

Report writers MUST consume this structured result and MUST NOT rerun GF.

---

## 18. Status vocabulary

PGF build behavior uses the shared orthogonal status dimensions.

### 18.1 Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

### 18.2 Execution state

```text
not_started
completed
timed_out
cancelled
launch_failed
```

### 18.3 Error kind

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

### 18.4 Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

For the PGF stage:

- a command or source error directly preventing PGF construction is normally `direct`;
- a PGF failure caused by an already identified lower checkpoint MAY be `downstream`;
- technical launch and I/O failures use the error kind and execution state rather than inventing a new diagnostic class.

---

## 19. Optimization policy

### 19.1 Release default

Release builds use:

```text
-optimize-pgf
```

unless the project documents an approved compatibility exception.

GF documentation recommends this optimization for grammars intended for shipping.

### 19.2 Diagnostic exception

Diagnostic builds MAY disable optimization when:

- reducing build cost is useful;
- optimization obscures investigation;
- the installed GF version has a documented issue;
- the user explicitly selects a diagnostic option.

The result MUST record the choice.

### 19.3 No semantic assumption

GF Wordbench MUST NOT assume that optimized and unoptimized PGFs are byte-identical.

Project scenarios SHOULD verify required runtime behavior under the release optimization policy.

---

## 20. Freshness and stale-artifact prevention

A PGF counts as current-run evidence only when:

- its expected path was known before launch;
- the run directory is current;
- the expected artifact did not pre-exist;
- the producing process completed successfully;
- the artifact exists after that process;
- the artifact is non-empty;
- its metadata and hash were captured;
- its build result references the current input fingerprint;
- the manifest records it.

The following are prohibited:

```text
reusing an old PGF because its name matches
copying the newest PGF found recursively
accepting a project-root PGF without current-run provenance
accepting an artifact after timeout
accepting an artifact from a different entrypoint set
accepting an artifact built under an unknown GF version
```

---

## 21. Manifest registration

A successful PGF is registered in:

```text
run_<run-id>/manifest.json
```

Recommended manifest role:

```text
pgf
```

Required manifest metadata:

```text
run-relative path
media type or binary type
required flag
size in bytes
SHA-256
producing component
producing contract
```

The artifact path is run-relative:

```text
artifacts/pgf/<expected-pgf-filename>
```

The manifest is written after final artifact writes.

The manifest MUST NOT hash itself.

If manifest registration fails, the run is not finalized successfully.

---

## 22. Reports

### 22.1 `summary.json`

The machine summary records the structured PGF build result or a stable reference to it.

It MUST record enough information to determine:

- whether the stage ran;
- whether it passed;
- which entrypoints were used;
- whether optimization was enabled;
- which artifact was produced;
- which GF version produced it;
- where raw evidence is stored.

### 22.2 `summary.md`

The human summary SHOULD include:

```text
PGF build status
expected artifact
actual artifact
optimization state
duration
artifact size
primary failure when applicable
```

### 22.3 `AI_READY.md`

The AI-ready report SHOULD include:

- the exact logical command;
- entrypoints;
- GF version;
- primary diagnostic;
- links to stdout and stderr;
- expected and actual artifact paths;
- relevant lower checkpoint failures.

It MUST NOT include unbounded raw binary content.

### 22.4 Reports do not execute

No report writer may:

- launch GF;
- rebuild the PGF;
- inspect source to reconstruct missing build facts;
- change artifact status;
- repair the manifest.

---

## 23. Publication and export

The run-owned PGF is validation evidence.

Publishing it to a stable release location is a separate operation.

### 23.1 Publication preconditions

Publication requires:

```text
release run overall status OK
PGF build status OK
required scenarios OK
manifest verification OK
release criteria satisfied
```

### 23.2 Atomic publication

Publication SHOULD:

1. copy to a temporary sibling path;
2. verify copied size and SHA-256;
3. atomically replace the destination when policy permits;
4. preserve or archive the previous release artifact;
5. record source run ID and hash.

### 23.3 Overwrite policy

A release artifact MUST NOT be overwritten silently.

Allowed policies:

```text
fail if exists
replace with explicit confirmation
versioned destination
archive then replace
```

Normal validation never publishes automatically.

---

## 24. Security and path safety

The PGF builder MUST treat project configuration as trusted repository configuration, but still validate paths.

Required protections:

- executable passed directly to process creation;
- arguments passed as an array;
- no shell interpolation;
- expected PGF name restricted to a filename;
- output contained inside the current run;
- entrypoints contained inside approved roots;
- symlink behavior explicitly checked;
- no traversal through `..`;
- no write into templates;
- no write into previous runs;
- no automatic execution of the produced PGF as operating-system code;
- no secrets written to command logs.

A PGF is a binary grammar artifact.

GF Wordbench SHOULD treat PGFs from untrusted sources as untrusted input to the GF runtime.

---

## 25. Cross-platform rules

GF Wordbench supports path handling through `pathlib.Path` or equivalent native path objects.

### 25.1 Windows

The implementation MUST support:

- drive-letter paths;
- spaces in executable and source paths;
- backslash-native paths;
- long argument values;
- `.exe` executable names;
- UTF-8 project filenames within supported GF behavior.

Manual quote insertion is prohibited.

### 25.2 POSIX

The implementation MUST support:

- absolute and relative executable resolution;
- spaces in paths;
- executable permission errors;
- signal-based termination;
- case-sensitive filenames.

### 25.3 Serialized paths

Runtime APIs use native paths.

Persisted reports use the normalized representation defined by `PERSISTED_SCHEMA_LOCK.md`.

---

## 26. Compatibility policy

GF command capabilities vary by GF version.

The PGF builder MUST use the verified feature matrix from:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

At minimum, compatibility verification covers:

```text
-make
-optimize-pgf
--path
--gfo-dir
--output-dir for PGF output
version probing
exit-code behavior
UTF-8 behavior
Windows path handling
```

GF 3.6 release notes document that `--output-dir` was extended to PGF files.

GF Wordbench MUST nevertheless verify actual installed behavior through integration tests for every supported GF release family.

Unsupported behavior causes a clear compatibility failure.

It MUST NOT trigger an undocumented fallback.

---

## 27. Determinism

GF Wordbench requires deterministic orchestration.

Deterministic inputs include:

```text
ordered entrypoints
ordered GF path
resolved options
optimization state
working directory
expected artifact name
output directory
timeout policy
```

GF Wordbench does not promise byte-identical PGF output across different tools or environments unless reproducibility has been verified for that exact compatibility profile.

A PGF hash is an artifact identity, not a universal semantic-version identifier.

---

## 28. Retry policy

A failed PGF build is not retried automatically by default.

Automatic retry can hide:

- nondeterministic source state;
- filesystem races;
- memory pressure;
- path mistakes;
- partial cleanup defects.

A retry requires either:

- a new run; or
- an explicit same-run retry policy that clears invalid output and preserves the first attempt’s evidence.

Attempts MUST have distinct logs.

Example:

```text
raw/compile/pgf-build.attempt-1.stdout.txt
raw/compile/pgf-build.attempt-1.stderr.txt
raw/compile/pgf-build.attempt-2.stdout.txt
raw/compile/pgf-build.attempt-2.stderr.txt
```

Only the accepted attempt may register the final artifact.

---

## 29. Concurrency

Different runs may build concurrently because each run owns separate artifact directories.

Within one run:

- only one PGF builder may own a specific expected artifact path;
- two stages MUST NOT build the same PGF concurrently;
- manifest finalization begins only after the PGF stage completes;
- publication begins only after release gates complete.

A lock file MAY protect same-run artifact ownership.

It MUST not become a persistent project lock or a source of project identity.

---

## 30. Cleanup

### 30.1 Successful run

Retain:

```text
final PGF
GFO artifacts according to retention policy
stdout
stderr
structured result
manifest metadata
```

### 30.2 Failed run

Retain:

```text
stdout
stderr
structured failure
partial artifact when safe and clearly invalid
diagnostic evidence
```

### 30.3 Source cleanup

The PGF builder MUST NOT delete source-tree files as cleanup.

Run cleanup is handled by run-retention policy.

---

## 31. Required unit tests

Recommended test file:

```text
tests/unit/audit/test_pgf_build.py
```

Required unit cases:

```text
single entrypoint
multiple ordered entrypoints
empty entrypoint list
duplicate entrypoints
missing entrypoint
entrypoint outside approved root
invalid expected filename
path traversal in expected filename
optimization enabled
optimization disabled
deduplicated GF path
path containing spaces
Windows executable path
timeout configuration
output-path collision
unexpected PGF filename
zero-byte artifact
missing artifact after zero exit
nonzero exit with artifact present
stdout-only diagnostic
stderr-only diagnostic
manifest metadata construction
```

Unit tests SHOULD use a fake process runner.

They MUST NOT require a real GF installation.

---

## 32. Required contract tests

Recommended test file:

```text
tests/contracts/test_gf_pgf_build_contract.py
```

Required contract checks:

- only the compiler/PGF builder constructs the command;
- command order is stable;
- process execution is delegated to `process_utils`;
- reports do not import the compiler;
- expected artifact path comes from resolved project configuration;
- PGF path is run-owned;
- stale artifacts cannot pass;
- optimization is required in release mode by default;
- artifact hash and size enter the result;
- successful artifact enters the manifest;
- failed artifact never enters the manifest as valid;
- normal validation does not publish;
- normal validation does not modify gold files.

---

## 33. Required integration tests

Recommended test file:

```text
tests/integration/test_real_gf_pgf_build.py
```

Integration tests requiring GF MUST be marked and skippable when no compatible GF executable is available.

Required real-GF cases:

```text
minimal valid grammar
two compatible concrete syntaxes
incompatible abstract syntaxes
syntax error
type error
missing imported module
optimized release build
unoptimized diagnostic build
direct output to run PGF directory
GFO output to run GFO directory
path containing spaces
load produced PGF
timeout with controlled slow fixture where practical
supported GF version matrix
```

For every supported GF version, integration evidence SHOULD record:

```text
GF version
platform
command
exit code
artifact name
artifact size
artifact hash
load-smoke result
```

---

## 34. Release-gate rules

When PGF is required, the release gate fails if any of the following is true:

```text
PGF stage skipped
configuration invalid
GF incompatible
process launch failed
timeout
cancellation
nonzero GF exit
fatal diagnostic
expected artifact missing
artifact empty
artifact stale
artifact outside run ownership
artifact hash unavailable
manifest registration failed
required PGF scenario failed
expected PGF name differs from project contract
```

A waiver MUST NOT convert a failed required PGF build into `OK`.

A project may defer release, but the recorded validation result remains failed or incomplete.

---

## 35. Drift indicators

The following indicate PGF-build drift:

- two modules construct different `gf -make` commands;
- release and diagnostic builds resolve different paths without policy;
- entrypoint ordering depends on filesystem enumeration;
- the expected PGF name is inferred from whatever file appears;
- output is written into source directories despite run-owned output support;
- a stale PGF satisfies a release gate;
- the result omits GF version;
- stdout or stderr is discarded;
- report generation triggers a rebuild;
- the GUI invokes GF directly;
- optimization changes without release-policy review;
- a project entrypoint changes without updating the project lock;
- the PGF filename changes without consumer migration;
- a manifest entry is reconstructed from naming conventions;
- required scenarios load a different grammar than the built PGF;
- a partial timed-out artifact is published;
- an unsupported GF flag is silently ignored;
- `project.toml`, the project lock and runtime configuration disagree.

Detected drift MUST be corrected through coordinated contract changes.

---

## 36. Change workflow

A PGF build contract change is complete only when all applicable items are checked:

```text
[ ] EXT-GF-004 reviewed
[ ] PIFC-ENTRY-003 reviewed
[ ] PIFC-ARTIFACT-002 reviewed
[ ] project configuration reviewed
[ ] expected PGF naming reviewed
[ ] command builder updated
[ ] process runner compatibility reviewed
[ ] GF path resolver reviewed
[ ] runtime result model updated
[ ] persisted schema reviewed
[ ] report writers updated
[ ] manifest writer updated
[ ] release gates updated
[ ] unit tests updated
[ ] contract tests updated
[ ] real-GF integration tests updated
[ ] version-compatibility matrix updated
[ ] migration impact documented
[ ] this document updated
```

Breaking changes include:

```text
renaming the expected PGF
changing release entrypoints
changing optimization policy
changing output ownership
changing command semantics
changing artifact freshness rules
changing result status semantics
changing manifest identity
```

---

## 37. Implementation checklist

A conforming implementation MUST satisfy:

```text
[ ] one central PGF command builder
[ ] one central GF path resolver
[ ] explicit ordered entrypoints
[ ] explicit expected PGF filename
[ ] dedicated PGF timeout
[ ] run-owned GFO output
[ ] run-owned PGF output
[ ] argv-based process execution
[ ] explicit working directory
[ ] independent stdout and stderr capture
[ ] timeout and cancellation distinction
[ ] stale-artifact prevention
[ ] exact expected-path verification
[ ] non-empty artifact verification
[ ] SHA-256 computation
[ ] structured PGF result
[ ] manifest registration
[ ] release-gate integration
[ ] no report-time execution
[ ] no normal-run publication
[ ] no gold modification
[ ] compatibility tests for supported GF versions
```

---

## 38. Official GF references

The following GF documentation supports the external behavior used by this contract:

- [GF Shell Reference](https://www.grammaticalframework.org/doc/gf-shell-reference.html)
- [GF Language Reference Manual](https://www.grammaticalframework.org/~hallgren/gf/doc/gf-refman.html)
- [GF Quickstart](https://www.grammaticalframework.org/doc/gf-quickstart.html)
- [GF 3.6 Release Notes](https://www.grammaticalframework.org/download/release-3.6.html)
- [GF Documentation Index](https://www.grammaticalframework.org/doc/)

GF Wordbench documentation MUST describe only the boundary it relies on.

It MUST not replace GF’s own language or compiler documentation.

---

## 39. Final enforcement rule

A PGF is accepted only as the verified output of the current run’s declared release inputs.

Therefore:

> No process exit code, old artifact, filename guess, report text or partial output may substitute for an explicit current-run PGF build result with traceable inputs, raw evidence, verified artifact metadata and manifest ownership.
