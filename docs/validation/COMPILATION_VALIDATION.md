# GF Wordbench — Compilation Validation

**Document ID:** `GF-WB-VALIDATION-COMPILATION`  
**Status:** Normative validation specification  
**Applies to:** GF module compilation, checkpoint validation, entrypoint validation, PGF release construction, compile evidence, and compile-related result aggregation  
**Primary owner:** `app/audit/compiler.py`  
**Orchestration owner:** `app/audit/audit_core.py`  
**External authority:** Grammatical Framework (`gf` / `gf.exe`)  
**Target architecture:** Final GF Wordbench architecture  
**Last structural review:** 2026-07-22

---

## 1. Purpose

Compilation validation proves that the active GF language project can be processed by the selected Grammatical Framework toolchain under a reproducible configuration.

It must answer:

- which source or entrypoint was compiled;
- why that subject was selected;
- which GF executable was used;
- which GF search path was effective;
- which ordered command was executed;
- which working directory was used;
- whether the process launched;
- whether it timed out;
- which diagnostics GF emitted;
- which artifacts were expected;
- which artifacts were produced;
- whether those artifacts belong to the current source state;
- whether the subject passed, failed, errored, or was skipped;
- whether a failure is direct, downstream, or ambiguous;
- whether compilation evidence is sufficient for checkpoint or release claims.

Compilation validation is not a replacement for:

- static scanning;
- native `.gfs` scenarios;
- gold comparison;
- linguistic review;
- project contract review;
- final PGF behavior validation.

A project can compile successfully and still fail required scenarios.

A set of individual modules can compile successfully and still fail final PGF construction.

---

## 2. Related normative documents

This specification must remain consistent with:

```text
docs/architecture/COMPONENT_MAP.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/validation/VALIDATION_MODES.md
docs/validation/FILE_SELECTION.md
docs/validation/RELEASE_GATES.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/VALIDATION_SPEC.md
project/docs/RELEASE_CRITERIA.md
```

Authority boundaries:

| Subject | Authoritative owner |
|---|---|
| Compile-stage architecture | this document |
| Exact external command contract | `EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| GF path resolution | `GF_PATH_RESOLUTION.md` |
| Persisted result fields | `PERSISTED_SCHEMA_LOCK.md` |
| Status and exception semantics | `ERROR_HANDLING_MODEL.md` |
| Active project entrypoints/checkpoints | `project/project.toml` |
| Module-to-module GF contracts | project interfile lock |
| Final mode stage plan | `VALIDATION_MODES.md` and `audit_core.py` |
| GF semantics and diagnostics | GF itself |

This document may summarize rules owned elsewhere, but must not redefine them incompatibly.

---

## 3. Core rule

> Compilation is successful only when the requested GF operation completed, its evidence was interpreted, and every required artifact and contract check passed.

A zero process exit code is necessary where GF defines it as success, but it is not sufficient.

Compilation success may additionally require:

- no timeout;
- no launch failure;
- no recognized fatal diagnostic;
- valid source identity;
- valid effective GF path;
- expected `.gfo` artifact;
- expected `.pgf` artifact;
- non-empty artifact;
- current-run artifact freshness;
- artifact registration;
- valid result construction.

---

## 4. Scope

This document governs:

- GF executable preflight for compilation;
- GF version compatibility for compilation;
- effective GF search-path construction;
- source-file compile requests;
- checkpoint compile requests;
- final entrypoint compile requests;
- PGF release builds;
- command and working-directory evidence;
- stdout and stderr capture;
- compile timeouts;
- compile artifact directories;
- `.gfo` verification;
- `.pgf` verification;
- compile-result construction;
- diagnostic interpretation;
- compile-stage status;
- integration with direct/downstream classification;
- continuation and fail-fast behavior;
- compile-related reporting and tests;
- migration from the current `gf-audit` behavior.

This document does not govern:

- static scan rule definitions;
- `.gfs` scenario syntax;
- gold normalization;
- parse or linearization acceptance;
- GUI widget layout;
- human wording outside required report semantics;
- GF's internal dependency resolver;
- GF's type checker implementation.

---

## 5. Normative terms

- **COMPILE SUBJECT**: source, checkpoint, entrypoint, or PGF target requested from GF.
- **SOURCE COMPILE**: validation of one selected `.gf` file.
- **CHECKPOINT**: configured module proving that a project layer is coherent.
- **ENTRYPOINT**: top-level configured module used for integration or release validation.
- **PGF BUILD**: construction of the final Portable Grammar Format artifact.
- **RAW EVIDENCE**: command, working directory, streams, exit facts, timing, and produced files before interpretation.
- **EXPECTED ARTIFACT**: file required by the current compile request.
- **FRESH ARTIFACT**: artifact proven to belong to the current request and source state.
- **CLEAN BUILD**: build executed without relying on previous run artifacts.
- **COMPILE PLAN**: deterministic ordered list of compile requests for one mode.
- **GATING COMPILE**: compile whose non-success affects overall mode outcome.
- **OPTIONAL COMPILE**: compile reported but not mode-gating.
- **DIRECT FAILURE**: failure attributed to the current subject as a root cause.
- **DOWNSTREAM FAILURE**: failure caused by a known failed dependency.
- **AMBIGUOUS FAILURE**: failure whose causality cannot be resolved reliably.

---

# 6. Component ownership

## 6.1 Compiler component

**Owner**

```text
app/audit/compiler.py
```

Responsibilities:

- construct compile and PGF requests;
- call the generic process runner;
- preserve raw compile evidence;
- request shared diagnostic interpretation;
- verify compile artifacts;
- return structured compile results;
- remain independent of reports and GUI;
- avoid direct/downstream classification.

Recommended final public operations:

```python
probe_gf_version(...)
build_compile_request(...)
compile_file(...)
compile_checkpoint(...)
compile_entrypoint(...)
build_release_pgf(...)
verify_compile_artifacts(...)
```

The exact public symbols are locked in `INTERFILE_CONTRACT_LOCK.md`.

## 6.2 Audit orchestrator

**Owner**

```text
app/audit/audit_core.py
```

Responsibilities:

- choose which compile requests belong to the active mode;
- preserve configured order;
- decide continuation and fail-fast behavior;
- combine compile results with scan and scenario results;
- request causal classification;
- compute overall outcome.

The orchestrator must not construct raw GF arguments directly.

## 6.3 Process runner

**Owner**

```text
app/utils/process_utils.py
```

Responsibilities:

- launch the ordered executable request;
- enforce timeout;
- capture stdout and stderr separately;
- record duration and execution facts;
- terminate timed-out owned processes;
- return generic process evidence.

It must not interpret GF diagnostics.

## 6.4 Diagnostic normalizer

**Owner**

```text
app/audit/diagnostics.py
```

Responsibilities:

- inspect both streams;
- identify GF error kinds;
- preserve raw evidence references;
- produce a stable primary message and detail;
- distinguish recognized GF failure from diagnostic parser error.

## 6.5 Classifier

**Owner**

```text
app/audit/classifier.py
```

Responsibilities:

- classify file-result causality after compile evidence exists;
- resolve blockers;
- distinguish direct, downstream, and ambiguous failures.

It must not execute GF or rebuild compile requests.

---

# 7. Compile-subject model

The final compiler supports four compile-subject kinds.

```text
source
checkpoint
entrypoint
pgf
```

Recommended model:

```python
@dataclass(frozen=True, slots=True)
class CompileTarget:
    target_id: str
    kind: str
    source_path: Path
    module_name: str
    required: bool
    expected_artifacts: tuple[Path, ...]
    declared_order: int
```

Required semantic fields:

| Field | Meaning |
|---|---|
| `target_id` | Stable identity in the run |
| `kind` | `source`, `checkpoint`, `entrypoint`, or `pgf` |
| `source_path` | Project-relative source or entrypoint path |
| `module_name` | GF module identity |
| `required` | Whether failure gates the active mode |
| `expected_artifacts` | Artifacts required from this request |
| `declared_order` | Deterministic configuration order |

A PGF target may reference multiple entrypoints while retaining one stable release target ID.

---

# 8. Compilation levels

## 8.1 Source compilation

Purpose:

- validate a selected file directly;
- obtain local GF diagnostics;
- support targeted development;
- build file-level evidence.

Source compilation does not alone prove that all consumers remain compatible.

## 8.2 Checkpoint compilation

Purpose:

- validate a configured architectural layer;
- prove provider/consumer integration at a meaningful boundary;
- catch downstream breakage earlier than final release.

Examples of checkpoint roles:

```text
morphology layer
noun layer
verb layer
syntax layer
structural layer
extension layer
language grammar layer
```

The actual checkpoint modules are active-project data.

Framework code must not hardcode their names.

## 8.3 Entrypoint compilation

Purpose:

- validate the top-level concrete or language/API module;
- prove that required project modules integrate;
- prove that release scenarios can load the intended grammar;
- produce expected top-level `.gfo` evidence.

Entrypoints come from `project/project.toml`.

## 8.4 PGF release build

Purpose:

- construct the final release artifact;
- validate compatibility of configured top-level modules;
- establish a deployable grammar artifact for release scenarios.

PGF construction is a separate stage from individual source and entrypoint compilation.

---

# 9. Mode participation

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Recommended compile participation:

| Compile level | Quick | Checkpoint | Release | Diagnostic |
|---|---:|---:|---:|---:|
| Target source | Required when selected | Optional | Optional | Included |
| Changed source set | Optional | Optional | Optional | Included when configured |
| Checkpoints | No by default | Required | Required | Included |
| Entrypoints | Optional | Required when configured | Required | Included |
| PGF build | No | Optional | Required when configured | Optional |
| Clean artifact isolation | Recommended | Recommended | Required | Configurable |
| Full raw evidence | Required | Required | Required | Required |

The precise plan is owned by `VALIDATION_MODES.md`.

Mode rules must not be duplicated separately in CLI and GUI.

---

# 10. Compile-plan construction

The orchestrator constructs one deterministic plan.

Recommended order:

```text
1. version preflight
2. target source, when applicable
3. additional selected sources, in normalized path order
4. checkpoints, in project.toml order
5. entrypoints, in project.toml order
6. PGF targets, in project.toml or release-policy order
```

Rules:

- duplicate target identities are prohibited;
- the same module may be compiled once per distinct compile purpose when evidence requirements differ;
- redundant equivalent requests should be deduplicated;
- deduplication must not remove a required artifact check;
- target order must be recorded;
- project order is semantically meaningful for checkpoints and entrypoints;
- filesystem enumeration order must not affect the plan;
- optional targets remain visible.

Recommended plan record:

```python
@dataclass(frozen=True, slots=True)
class CompilePlan:
    mode: str
    targets: tuple[CompileTarget, ...]
    clean_build: bool
    fail_fast: bool
    gf_version_required: bool
```

---

# 11. Preflight validation

Compilation must not begin until preflight validates the request.

## 11.1 Required preflight checks

```text
project configuration loaded
source root exists
selected source exists
selected source is inside approved project roots
source path is a .gf file
GF executable resolves
working directory exists
RGL root exists when required
effective GF path is valid
timeout is positive
compile output directories are writable
expected artifact paths stay inside approved run roots
GF version is compatible when required
command options are supported by selected GF version
```

## 11.2 Preflight outcome

Invalid global preflight:

```text
status: ERROR
error_kind: CONFIG or TOOL
```

No process is launched.

Invalid per-subject preflight:

- create subject `ERROR` when a stable target exists;
- continue independent subjects when safe;
- skip dependent subjects explicitly.

## 11.3 No implicit repair

Preflight must not silently:

- choose another project;
- choose another source;
- change an entrypoint;
- use a different GF executable;
- remove an unsupported option and continue with different semantics;
- create a missing project source;
- use stale generated artifacts.

Safe output-directory creation is permitted when the directory belongs to the run and the contract requires it.

---

# 12. GF executable and version

## 12.1 Executable resolution

The final `RunConfig` contains the resolved executable actually used.

A convenience value such as `gf` from `PATH` may be accepted before resolution.

The recorded run evidence must contain an explicit resolved executable.

## 12.2 Version probe

Recommended conceptual request:

```text
<gf> --version
```

or the supported equivalent for the selected GF version.

The exact command belongs to the external-tool lock.

## 12.3 Version outcomes

| Outcome | Compile policy |
|---|---|
| Tested supported version | Continue |
| Supported untested newer version | Warn; continue only when non-strict policy permits |
| Below minimum version | Stop compilation with `ERROR` |
| Known incompatible version | Stop compilation with `ERROR` |
| Probe skipped explicitly | Record `SKIPPED`; continue only where allowed |
| Probe launch failure | Compilation cannot safely begin |
| Probe output unparseable | Error when version-gated options are needed |

## 12.4 Version evidence

Record:

```text
resolved executable
raw version stdout
raw version stderr
version command
parsed version
compatibility classification
warning or error
```

---

# 13. Effective GF search path

Compilation and scenarios must use the same path-resolution service.

Recommended precedence:

```text
1. explicit path in resolved RunConfig
2. active project path parts
3. configured RGL root and supported standard subdirectories
4. explicitly enabled environment fallback
5. configuration error
```

Rules:

- path-part order is deterministic;
- relative project paths resolve against the documented project root;
- duplicate path parts are removed without changing first-occurrence order;
- nonexistent required parts are errors;
- optional parts may be warnings only when documented;
- environment fallback must be visible;
- developer-global `GF_LIB_PATH` must not affect a run silently;
- the effective path is recorded exactly;
- compilation and scenarios must not construct different paths.

Canonical serialized project-owned paths use `/`.

Process-native path rendering may use the platform form required by GF.

---

# 14. Command construction

## 14.1 Structured request

Recommended request model:

```python
@dataclass(frozen=True, slots=True)
class CompileRequest:
    target: CompileTarget
    executable: Path
    args: tuple[str, ...]
    working_directory: Path
    environment: Mapping[str, str]
    timeout_sec: int
    stdout_path: Path
    stderr_path: Path
    expected_artifacts: tuple[Path, ...]
```

The request must be complete before process launch.

## 14.2 No shell string

Preferred invocation:

```python
[executable, *args]
```

with:

```text
shell = false
```

Normal compilation must not depend on shell quoting or redirection.

## 14.3 Argument ordering

Argument order is part of the external contract.

The source path must occupy the documented final source position for source compilation when required by the external contract.

The logged structured command must equal the executed structured command.

## 14.4 Working directory

The working directory is explicit.

Recommended default:

```text
resolved GF project root
```

It must not depend on:

- terminal launch directory;
- GUI process directory;
- IDE;
- launcher shortcut;
- current Python working directory.

## 14.5 Environment

Environment overrides must be minimal and child-process-scoped.

Record approved overrides, with secrets redacted.

Full environment dumps are prohibited.

---

# 15. Source compile request

Conceptual command:

```text
<gf> <compile-options> <path-options> <artifact-options> <source.gf>
```

The exact supported command is version-gated and owned by the external-tool contract.

Possible options include supported equivalents of:

```text
--gf-lib-path=<rgl-root>
--path=<effective-gf-path>
--gfo-dir=<run-gfo-dir>
--output-dir=<run-output-dir>
--cpu
```

Rules:

- optional CPU statistics require explicit configuration;
- unsupported options must not be passed;
- compatibility adapters must be documented;
- final source argument ordering must be deterministic;
- source path must be the intended target;
- source must not be modified;
- generated output belongs to run-owned artifact directories when supported;
- if GF cannot isolate output directly, copied/catalogued artifacts must retain provenance.

---

# 16. Checkpoint compile request

Checkpoint compilation uses the same compiler and process boundary as source compilation.

Additional rules:

- checkpoint target comes from `project.toml`;
- checkpoint order follows configuration;
- checkpoint source must exist;
- checkpoint identity must match the intended GF module;
- expected dependent modules are documented in the project dependency map;
- successful checkpoint compile validates integration only up to that boundary;
- a checkpoint failure does not automatically identify its root cause;
- classifier assigns direct/downstream status after the relevant file results exist.

A checkpoint must not be simulated by compiling an arbitrary nearby source.

---

# 17. Entrypoint compile request

Entrypoint compilation validates the configured top-level grammar.

Rules:

- entrypoint comes from `project.toml`;
- entrypoint source exists;
- module identity matches configuration;
- no active-language entrypoint name is hardcoded in framework code;
- required entrypoint order is deterministic;
- output is isolated from source where practical;
- expected `.gfo` is verified when the command contract promises it;
- required scenarios must reference the same intended grammar;
- entrypoint compile success does not replace scenario validation.

---

# 18. PGF release request

Conceptual command:

```text
<gf> -make -optimize-pgf <path-options> <entrypoint-1> [<entrypoint-N>...]
```

The exact option set is capability-gated.

Rules:

- optimization may be disabled only by documented mode policy;
- release entrypoints come from project configuration;
- entrypoint ordering is deterministic;
- PGF timeout is separate from per-file timeout;
- expected PGF name and path are declared or deterministically derived;
- PGF is created or copied into an owned release artifact location;
- PGF must be non-empty;
- PGF must belong to the current release request;
- PGF must be registered in the manifest;
- previous release artifacts must not be overwritten silently;
- build command and GF version are preserved;
- PGF success is release-gating when `release_requires_pgf = true`.

The detailed packaging and runtime checks belong to `GF_PGF_BUILD.md`.

---

# 19. Timeout policy

Every compile request has a finite positive timeout.

Operation classes:

```text
version probe
source compilation
checkpoint compilation
entrypoint compilation
PGF build
```

Recommended configuration separates at least:

```text
version_timeout_sec
compile_timeout_sec
pgf_timeout_sec
```

Rules:

- timeout values are validated before launch;
- timeout begins at process launch;
- timeout includes external process execution, not preflight;
- process and owned children are terminated according to platform policy;
- partial streams are retained;
- timeout is explicit;
- a timeout is `ERROR`, not normal GF `FAIL`;
- timeout must not be inferred solely from a legacy exit code;
- retry is prohibited unless an explicit bounded policy exists.

---

# 20. Raw compile evidence

For every attempted compile, preserve:

```text
compile target ID
target kind
project-relative source path
module name
required flag
resolved GF executable
parsed GF version
structured ordered command
rendered human command
working directory
effective GF search path
environment overrides, redacted
start timestamp
finish timestamp
duration
launch result
exit code
timeout state
cancellation state when available
stdout path
stderr path
expected artifacts
produced artifacts
artifact verification
source fingerprint
```

Stdout and stderr remain separate.

Combined diagnostic text may be derived, but it must not replace raw files.

---

# 21. Compile artifact layout

Canonical run locations:

```text
run_<run-id>/
├── raw/
│   └── compile/
│       ├── <safe-target-key>.stdout.txt
│       └── <safe-target-key>.stderr.txt
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

The exact filenames must be generated by the artifact/path owner.

Consumers must not independently reconstruct them.

Safe target keys must be:

- deterministic;
- path-safe;
- collision-resistant within one run;
- independent of local absolute-root prefixes;
- traceable back to target identity.

---

# 22. Artifact verification

## 22.1 Verification dimensions

For each expected artifact, verify:

```text
path
containment
existence
regular-file type
non-empty requirement
creation or modification during current request
source/request association
optional hash
manifest registration
```

## 22.2 Freshness

Artifact existence alone is insufficient.

Recommended freshness proof uses one or more:

```text
clean isolated artifact directory
pre-request absence
post-request creation timestamp
request-specific directory
source fingerprint association
artifact hash recorded after request
manifest provenance
```

Release mode must use a clean or request-isolated artifact location.

## 22.3 Missing artifact

If an artifact is required and absent after apparent success:

```text
status: ERROR
error_kind: TOOL
internal reason: artifact_failure
```

## 22.4 Unexpected artifact

Unexpected artifacts are catalogued when safe.

They are warnings unless they:

- escape approved roots;
- overwrite protected files;
- conflict with expected artifact identity;
- indicate unsupported command behavior.

## 22.5 Source-directory artifacts

GF may produce artifacts beside source when tool capabilities or compatibility require it.

When this occurs:

- source must not be modified;
- generated files are identified;
- generated files are copied or catalogued;
- cleanup policy is explicit;
- release validation must prove freshness;
- stale artifacts must not influence conclusions.

---

# 23. Clean-build policy

## 23.1 Quick mode

A clean artifact directory is recommended.

Reuse may be allowed for speed only when:

- reused artifacts are never accepted as fresh evidence;
- the requested target is still executed;
- output provenance remains clear.

## 23.2 Checkpoint mode

Checkpoint validation should use isolated run artifacts.

## 23.3 Release mode

Release compilation must use clean or request-isolated artifact directories.

It must not rely on:

```text
source-adjacent stale .gfo
previous run artifacts
developer-global build directories
untracked PGF files
```

## 23.4 Diagnostic mode

Diagnostic mode may preserve broader intermediate artifacts, but freshness and provenance rules remain unchanged.

---

# 24. Caching and incremental execution

Caching is optional.

It must not weaken validation semantics.

A cached compile result may be used only when all cache-key inputs match, including:

```text
source fingerprint
relevant dependency fingerprints
GF executable identity
GF version
effective GF path
ordered command
working-directory semantics
environment overrides affecting GF
expected artifact policy
compiler contract version
```

Rules:

- cache hit is explicit;
- cached evidence remains traceable;
- release mode should default to no cache or validated clean rebuild;
- unknown dependency changes invalidate cache;
- a stale `.gfo` is not a cache;
- cache failure must not become language failure;
- cache correctness requires dedicated tests.

GF Wordbench may omit compilation caching entirely.

Correctness is more important than build-speed complexity.

---

# 25. Parallelism

Compilation should be serial by default until safe concurrency is proven.

Parallel compilation may be enabled only when:

- GF invocations are independent;
- artifact paths do not collide;
- logs are target-specific;
- result ordering remains deterministic;
- process limits are bounded;
- cancellation is safe;
- Windows behavior is tested;
- GF version behavior is compatible.

Release entrypoint and PGF construction should remain serial unless a documented need proves otherwise.

Parallel completion order must not change persisted result order.

---

# 26. Diagnostic interpretation

The compiler passes both raw streams and execution facts to the shared diagnostic normalizer.

Recognized broad kinds:

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

Compiler-specific interpretation:

| Evidence | Status | Error kind |
|---|---|---|
| Valid compile, required checks pass | `OK` | `OK` |
| GF type/unification failure | `FAIL` | `TYPE` |
| GF syntax failure | `FAIL` | `SYNTAX` |
| Unknown GF-reported language failure | `FAIL` | `OTHER` |
| GF internal runtime/compiler failure | `ERROR` | `INTERNAL` |
| Timeout | `ERROR` | `TIMEOUT` |
| Launch failure | `ERROR` | `TOOL` |
| Required artifact missing | `ERROR` | `TOOL` |
| Diagnostic parser crashes | `ERROR` | `SCRIPT` |
| Invalid compile configuration | `ERROR` | `CONFIG` |
| Evidence I/O failure | `ERROR` | `IO` |
| Intentional no-compile | `SKIPPED` | `OK` |

Diagnostic rules:

- both streams are considered;
- first error is stable and bounded;
- error detail may preserve expected/inferred information;
- GF source locations are preserved when diagnostic;
- raw messages are not rewritten as different GF semantics;
- user-facing reports may normalize environmental path prefixes only where allowed.

---

# 27. Compile result model

Canonical persisted file results currently embed a compile summary.

Recommended final in-memory compile model:

```python
@dataclass(frozen=True, slots=True)
class CompileSummary:
    target_id: str
    target_kind: str
    status: str
    command: tuple[str, ...]
    working_directory: str
    exit_code: int | None
    launched: bool
    timed_out: bool
    cancelled: bool
    duration_ms: int
    error_kind: str
    first_error: str
    error_detail: str
    stdout_path: str | None
    stderr_path: str | None
    expected_artifacts: tuple[str, ...]
    produced_artifacts: tuple[str, ...]
    artifact_checks_passed: bool
```

This is a target design.

Persisting new fields requires a schema-compatible extension or versioned migration.

The minimum current canonical persisted fields remain governed by `PERSISTED_SCHEMA_LOCK.md`.

---

# 28. File-result integration

A file result combines:

```text
source identity
static scan evidence
source fingerprint
compile summary
validation status
diagnostic class
blocked_by
scan log path
```

Rules:

- compile summary does not own direct/downstream classification;
- scan findings do not automatically overwrite compile status;
- fingerprint failure is not represented as a valid empty fingerprint;
- target file path is project-relative;
- raw output paths are run-relative in canonical summaries;
- file-result ordering is normalized project path order.

---

# 29. Status criteria

## 29.1 `OK`

A compile subject is `OK` only when all applicable conditions pass:

```text
valid request
process launched
no timeout
not cancelled
exit semantics indicate success
no fatal diagnostic
required evidence captured
required artifact checks pass
result interpreted successfully
```

## 29.2 `FAIL`

A compile subject is `FAIL` when:

- GF executed sufficiently;
- language/project compile criterion was evaluated;
- criterion failed;
- evidence remains interpretable.

Typical kinds:

```text
TYPE
SYNTAX
OTHER
```

## 29.3 `ERROR`

A compile subject is `ERROR` when:

- launch fails;
- timeout occurs;
- GF internal failure prevents reliable validation;
- required evidence is unavailable;
- required artifact is missing;
- diagnostic interpretation fails;
- request contract is invalid;
- source fingerprint is required but unavailable;
- result construction violates invariants.

## 29.4 `SKIPPED`

A compile subject is `SKIPPED` when:

- no-compile was explicitly selected;
- mode excludes the target;
- prerequisite failure makes execution meaningless;
- fail-fast or cancellation prevents launch;
- target is explicitly non-applicable.

A reason is required.

---

# 30. Direct and downstream classification

Compilation produces evidence.

Classification happens after enough related results exist.

Rules:

- compiler returns no final dependency-cascade classification;
- classifier inspects project-relative GF references and known failed subjects;
- direct failure indicates likely root subject;
- downstream failure includes `blocked_by`;
- blocker chains should collapse to root failures where reliable;
- cycles are detected;
- uncertain causality remains `ambiguous`;
- `ERROR` from framework execution must not be presented as a project dependency failure.

A non-zero exit alone does not establish direct causality.

---

# 31. Continuation policy

Default behavior collects independent compile evidence.

## 31.1 Continue after

Normally continue after:

- ordinary source `FAIL`;
- one checkpoint `FAIL`, when later independent targets remain meaningful;
- one optional target `ERROR`;
- warning-only version uncertainty permitted by mode.

## 31.2 Skip dependent targets after

Skip dependent work when:

- required project configuration is invalid;
- GF cannot launch globally;
- effective GF path is invalid globally;
- source root is unavailable;
- target prerequisite is known unavailable;
- artifact directory is unsafe or unwritable;
- cancellation is requested.

## 31.3 Release behavior

Release mode should gather all safe, meaningful gating evidence.

A failed checkpoint may still permit compiling an entrypoint for diagnostic value, but:

- the entrypoint result must not erase the checkpoint failure;
- release remains non-successful;
- dependent scenario execution may be skipped if loading cannot succeed meaningfully.

---

# 32. Fail-fast behavior

Fail-fast is optional.

When enabled:

- first gating `FAIL` or `ERROR` stops new compile launches;
- currently running process is handled by normal cancellation policy;
- remaining targets become `SKIPPED`;
- skip reason is `fail_fast`;
- completed results remain unchanged;
- overall outcome reflects the triggering result;
- reports show incomplete plan execution.

Fail-fast should not be the default for release evidence.

---

# 33. Cancellation

On cancellation:

1. stop launching new compile targets;
2. terminate owned active process safely;
3. preserve partial stdout and stderr;
4. mark active compile `ERROR` or the future versioned cancellation representation;
5. mark remaining targets `SKIPPED`;
6. record cancellation cause;
7. finalize partial run evidence when safe.

Cancellation must not be reported as a GF type failure.

---

# 34. No-compile mode

No-compile is an intentional policy.

Rules:

- scanner may still run;
- compile requests are not launched;
- compile result is `SKIPPED`;
- no fake successful exit is claimed;
- no `.gfo` or `.pgf` freshness claim is made;
- release mode cannot be release-ready when required compilation is skipped;
- reports state why compilation was omitted.

Legacy implementations that encode skipped compile as exit code zero must migrate to explicit status semantics.

---

# 35. Static scan interaction

Static scanning and compilation remain separate evidence channels.

Rules:

- scanner does not execute GF;
- compiler does not duplicate scanner rules;
- scan findings may coexist with compile `OK`;
- release policy may make selected scan findings gating;
- compile success does not erase scan findings;
- scan failure does not automatically prevent compile when execution remains safe;
- final file result preserves both.

GF execution is authoritative for actual GF compile success.

---

# 36. Scenario interaction

Compilation and scenarios validate different contracts.

Required sequence for a release-oriented run:

```text
checkpoints
→ entrypoints
→ PGF build when required
→ scenarios that load intended grammar/PGF
```

Rules:

- compile success does not satisfy scenario criteria;
- scenario success does not replace missing compile evidence;
- scenarios use the same resolved GF executable and path policy;
- scenario reports consume compile artifact locations through owned models;
- reports must not rerun compile to fill scenario evidence;
- a failed required compile may cause dependent scenarios to be `SKIPPED`.

---

# 37. Project contract interaction

When a provider GF module changes:

```text
provider source compile
→ direct consumers
→ affected checkpoints
→ affected entrypoints
→ required scenarios
→ PGF release build where applicable
```

Compilation validation supports this chain but does not infer every project dependency automatically unless dependency data is available.

The active project must document:

- entrypoints;
- checkpoints;
- required consumers;
- expected artifacts;
- release targets.

These belong to project configuration and the project interfile lock.

---

# 38. Reporting requirements

Reports consume completed compile results.

They must display or reference:

```text
target
target kind
status
error kind
diagnostic class
primary message
blocked_by
duration
timeout
resolved executable
GF version
stdout path
stderr path
expected artifacts
artifact-check result
```

Human summaries may omit low-level fields for `OK` results when links remain available.

Machine summaries must follow the persisted schema.

AI-ready reports must distinguish:

- language compile failures;
- downstream compile failures;
- timeout;
- launch failure;
- GF internal failure;
- missing artifact;
- skipped compile.

No report may launch GF.

---

# 39. Manifest requirements

Every retained compile artifact must be catalogued.

Recommended manifest roles:

```text
compile_stdout
compile_stderr
gfo
pgf
other
```

Manifest metadata includes:

```text
path
role
media type
required flag
size
SHA-256
created_by
```

Rules:

- raw streams appear when retained;
- required `.gfo`/`.pgf` appear;
- missing required artifact prevents valid manifest finalization;
- manifest hashes final bytes;
- generated grammar artifacts are not rewritten after hashing;
- manifest does not hash itself.

---

# 40. Security rules

Compilation validates untrusted project paths and source assets.

Rules:

- no shell command string for normal compile;
- arguments remain separate;
- source paths are validated;
- artifact paths remain inside approved roots;
- symlink escape is rejected in strict mode;
- executable resolution is explicit;
- environment override is minimal;
- secrets are not logged;
- command rendering redacts secret-marked arguments;
- compiler never modifies source;
- cleanup never deletes outside run-owned roots;
- source filenames cannot select arbitrary output paths;
- path collisions are errors.

A security violation stops the unsafe operation.

---

# 41. Determinism

Given identical:

```text
source state
project configuration
GF executable/version
effective GF path
command contract
environment policy
mode
```

GF Wordbench must produce the same:

```text
compile plan
target order
structured requests
artifact paths
result ordering
status interpretation
manifest ordering
```

Raw GF diagnostic wording may differ across supported GF versions.

Version-specific differences must be preserved and handled through compatibility rules, not silently erased.

---

# 42. Platform behavior

## 42.1 Windows

Required support:

```text
gf.exe
paths containing spaces
Unicode paths where supported
CRLF source/input handling
process termination
headless GUI-triggered execution
batch launchers as convenience only
```

Compiler execution must not require a visible console.

## 42.2 Other platforms

Platform-neutral orchestration should use:

```text
pathlib
argument arrays
explicit working directory
explicit encoding
portable serialized paths
```

Platform-specific process-tree termination remains isolated in infrastructure.

---

# 43. Performance boundaries

Compilation validation should avoid unnecessary work without sacrificing correctness.

Allowed optimizations:

- deterministic request deduplication;
- bounded parallelism after proven safe;
- optional source fingerprint precomputation;
- optional validated cache;
- concise `OK` detail output;
- reuse of already loaded project configuration;
- reuse of resolved effective GF path within one run.

Prohibited optimizations:

- accepting stale artifact as current;
- skipping required entrypoint compile because a child compiled;
- skipping PGF build because `.gfo` files exist;
- omitting raw evidence;
- suppressing artifact verification;
- sharing output paths across concurrent targets;
- inferring success from previous run.

---

# 44. Legacy migration from `gf-audit`

The current implementation supplies a useful baseline but final compilation validation requires coordinated changes.

## 44.1 Legacy modes

```text
file → quick
all  → diagnostic
```

Canonical writers emit only final mode names.

## 44.2 Legacy compile status

Legacy behavior may derive status directly from:

```text
exit_code == 0
```

Final behavior evaluates full success criteria.

## 44.3 Legacy timeout code

Legacy timeout may use a sentinel exit code.

Final behavior uses explicit timeout facts as authoritative.

## 44.4 Legacy script errors

Broad exceptions may currently become `FAIL` with `SCRIPT`.

Final behavior distinguishes:

```text
language FAIL
framework ERROR
configuration ERROR
I/O ERROR
tool ERROR
```

## 44.5 Legacy artifacts

Legacy output directories and source-adjacent `.gfo` may be readable for historical runs.

Final release validation uses run-owned or request-isolated artifacts.

## 44.6 Legacy fingerprint

Legacy abbreviated SHA-1 may be imported.

Canonical new evidence uses full SHA-256 according to the persisted schema.

## 44.7 Legacy APIs

Legacy symbols such as:

```python
build_gf_args(...)
compile_file(...)
probe_gf_version(...)
```

may remain compatibility wrappers temporarily.

They must delegate to one final request and execution path.

---

# 45. Unit tests

Recommended tests:

```text
tests/validation/test_compile_plan.py
tests/validation/test_compile_request.py
tests/validation/test_compile_status.py
tests/validation/test_compile_artifacts.py
tests/validation/test_checkpoint_compilation.py
tests/validation/test_entrypoint_compilation.py
tests/validation/test_pgf_build.py
```

Required unit cases:

```text
valid source request
invalid source path
source outside project
deterministic arguments
source argument order
working directory
explicit GF path
automatic GF path
missing executable
unsupported option
positive timeout validation
non-zero exit
stdout-only diagnostic
stderr-only diagnostic
fatal diagnostic with zero exit
timeout
cancellation
missing .gfo
missing .pgf
empty .pgf
stale artifact
no-compile
CPU option enabled/disabled
path with spaces
Unicode diagnostic
report does not rerun compile
```

---

# 46. Contract tests

Recommended contract files:

```text
tests/contracts/test_gf_compile_contract.py
tests/contracts/test_gf_pgf_build_contract.py
tests/contracts/test_process_contract.py
tests/contracts/test_artifact_ownership.py
tests/contracts/test_model_contracts.py
tests/contracts/test_project_config_contracts.py
```

They must verify:

- compiler calls process runner through the documented boundary;
- process runner returns structured evidence;
- compiler does not import reports;
- compiler does not classify dependency cascades;
- reports do not import compiler;
- CLI and GUI use `audit_core`;
- effective GF path is shared;
- artifact paths come from owners;
- persisted fields agree with schema;
- required artifacts are checked;
- skip is distinct from success.

---

# 47. Integration tests with real GF

A small language-neutral fixture grammar should test:

```text
version probe
successful source compile
syntax failure
type failure
checkpoint compile
entrypoint compile
PGF build
missing artifact detection
paths containing spaces
UTF-8 grammar content
```

Tests requiring real GF are separately marked.

Integration evidence should record tested GF versions.

A real-GF test must not depend on:

```text
developer-global GF_LIB_PATH
active project language
pre-existing .gfo
source-adjacent stale artifacts
personal absolute paths
```

---

# 48. Release-gate criteria

Compilation portion of release readiness requires:

```text
[ ] supported GF version established
[ ] effective GF path recorded
[ ] required checkpoints compiled
[ ] required entrypoints compiled
[ ] required compile artifacts verified
[ ] PGF built when required
[ ] PGF non-empty
[ ] PGF registered in manifest
[ ] no required compile ERROR
[ ] no required compile FAIL
[ ] no required compile SKIPPED
[ ] raw evidence retained
[ ] source fingerprints valid
[ ] clean/request-isolated artifacts used
[ ] required dependent scenarios completed separately
```

Compilation alone does not complete the release gate.

---

# 49. Drift indicators

Probable compilation-contract drift exists when:

- CLI and GUI build different compile requests;
- compiler and scenario runner construct different GF paths;
- command logged differs from command executed;
- source argument position changes silently;
- a new option appears without GF-version policy;
- timeout is absent or non-positive;
- stderr is ignored;
- zero exit is accepted despite missing artifact;
- `.gfo` or `.pgf` ownership changes;
- report writer launches GF;
- compiler classifies direct/downstream failure;
- project-specific module names appear in framework defaults;
- entrypoint order differs from `project.toml`;
- stale artifacts satisfy current validation;
- no-compile appears as `OK`;
- summary schema changes without version update;
- release succeeds without required PGF;
- artifact path is reconstructed by a consumer;
- fingerprint failure is replaced with a valid-looking empty value.

Any indicator requires contract review.

---

# 50. Change workflow

Any compile-contract change must answer:

```text
Compile contract:
Current behavior:
New behavior:
Reason:
GF versions affected:
Platforms affected:
Target kinds affected:
Command changed:
Path resolution changed:
Timeout changed:
Artifacts changed:
Result model changed:
Status semantics changed:
Persistence changed:
Migration:
Tests:
```

Required checklist:

```text
[ ] Compiler request builder updated
[ ] Process runner reviewed
[ ] Project configuration reviewed
[ ] Bootstrap reviewed
[ ] RunConfig reviewed
[ ] Result model reviewed
[ ] Diagnostic parsing reviewed
[ ] Artifact verification reviewed
[ ] Manifest reviewed
[ ] File-result aggregation reviewed
[ ] Classifier reviewed
[ ] CLI/GUI behavior reviewed
[ ] Unit tests updated
[ ] Contract tests updated
[ ] Real-GF tests updated
[ ] Windows behavior tested
[ ] External-tool lock updated
[ ] Interfile lock updated
[ ] Persisted schema updated when needed
[ ] Migration notes added
[ ] Changelog updated when user-visible
```

---

# 51. Review checklist

Reviewers should ask:

```text
Is the correct target being compiled?
Does the target come from authoritative configuration?
Is the command structured and deterministic?
Is the exact executable recorded?
Is the working directory explicit?
Is the GF path reproducible?
Are both streams preserved?
Is timeout finite and explicit?
Is zero exit treated only as evidence?
Are required artifacts verified?
Are artifacts fresh?
Can stale output affect the result?
Is language FAIL distinct from framework ERROR?
Is no-compile SKIPPED?
Does classifier own causality?
Do reports avoid execution?
Are entrypoint and PGF rules release-safe?
Does the implementation remain language-neutral?
Do tests prove the external boundary?
```

---

# 52. Final invariants

Compilation validation must always preserve:

1. one compile request owner;
2. one generic process owner;
3. one shared GF diagnostic interpreter;
4. deterministic target order;
5. explicit executable;
6. explicit working directory;
7. reproducible GF path;
8. finite timeout;
9. separate stdout and stderr;
10. source immutability;
11. current-run artifact provenance;
12. required artifact verification;
13. `FAIL` for evaluated language failure;
14. `ERROR` for execution or interpretation failure;
15. `SKIPPED` for intentional omission;
16. direct/downstream classification outside compiler;
17. no report-time execution;
18. language-neutral framework configuration;
19. clean release artifact policy;
20. distinct source, checkpoint, entrypoint, and PGF evidence;
21. schema-compatible persistence;
22. traceable migration from legacy behavior.

---

# 53. Final rule

> GF Wordbench may claim that a compile target passed only when it can reproduce the request, preserve the response, verify the required artifacts, and show that the evidence belongs to the current source state.

Neither a green console line, a zero exit code, an existing `.gfo`, nor a previous `.pgf` is sufficient proof.
