# GF Wordbench — GF Command Construction

**Document ID:** `GF-WB-GF-COMMAND-CONSTRUCTION`  
**Status:** Normative GF request-construction specification  
**Applies to:** GF version probing, source compilation, PGF construction, native `.gfs` scenario execution and supported GF inspection operations  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**External-tool authority:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Path authority:** `docs/configuration/ENVIRONMENT_AND_PATHS.md`, `docs/gf/GF_PATH_RESOLUTION.md`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines how GF Wordbench converts a validated application request into a structured request for the Grammatical Framework executable.

GF commands are constructed by named operations. Command syntax must not be assembled independently in validation stages, entrypoints, reports or project code.

The command-construction boundary owns:

- operation-specific argument construction;
- GF-version syntax selection;
- ordered GF search-path representation;
- working-directory selection;
- standard-input construction for native `.gfs` scenarios;
- expected-artifact declarations;
- timeout selection;
- redacted display rendering;
- request validation before process launch.

It does not own:

- process creation or termination;
- stdout or stderr capture;
- diagnostic classification;
- result aggregation;
- report generation;
- project identity;
- release-policy decisions.

---

## 2. Product and run boundary

One GF Wordbench run resolves exactly one active GF language project and one normative language target.

Every GF request belongs to that resolved run and project. A request must not:

- combine modules from several active projects;
- discover projects through a Portfolio registry;
- execute validation for several Wordbench workspaces;
- depend on `gf-portfolio` configuration, storage, schemas or runtime.

`gf-portfolio` may consume finalized public Wordbench artifacts. It does not participate in GF command construction.

---

## 3. Core rule

> GF Wordbench constructs GF requests as typed operation data, never as dispersed string concatenation.

The process adapter receives:

```text
executable
arguments[]
working_directory
environment
stdin
timeout
```

It does not receive an opaque shell command as the authoritative execution form.

A human-readable command may be rendered for logs and reports, but that rendering is not executed.

---

## 4. Ownership

### 4.1 Application layer

The application layer selects a named GF operation and supplies validated semantic inputs.

Examples:

```text
probe_version
compile_module
build_pgf
run_scenario
inspect_grammar
```

The application layer must not encode version-specific GF flags directly.

### 4.2 GF command builder

The GF command builder owns:

- mapping an operation to GF arguments;
- applying the selected GF-version contract;
- validating operation-specific inputs;
- producing a structured `GfRequest`;
- declaring expected artifacts;
- producing a redacted display form.

### 4.3 External-tool adapter

The external-tool adapter owns:

- launching the resolved executable;
- passing the argument array;
- setting the working directory;
- passing standard input;
- applying the environment mapping;
- enforcing timeout and cancellation;
- capturing raw process evidence.

It must not rebuild or reinterpret the GF command.

### 4.4 Validation modules

Validation modules consume structured process results and verify operation-specific outcomes.

They own:

- compile-result interpretation;
- scenario marker validation;
- output normalization;
- gold comparison;
- expected-artifact verification;
- structured validation results.

They must not reconstruct GF arguments after execution.

---

## 5. Request model

A GF request contains:

```text
request_id
operation_kind
project_id
run_id
gf_version
executable
arguments[]
working_directory
gf_search_paths[]
environment_policy
environment_overrides
stdin_payload
expected_artifacts[]
timeout
redaction_policy
```

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class GfRequest:
    request_id: str
    operation_kind: GfOperationKind
    project_id: str
    run_id: str

    gf_version: str
    executable: Path
    arguments: tuple[str, ...]
    working_directory: Path
    gf_search_paths: tuple[Path, ...]

    environment_policy: str
    environment_overrides: Mapping[str, str]
    stdin_payload: bytes | None

    expected_artifacts: tuple[ExpectedArtifact, ...]
    timeout_seconds: float
    redaction_policy: str
```

Exact runtime type names may vary. The semantic fields and ownership rules remain stable.

---

## 6. Operation kinds

Canonical operation kinds are:

```text
probe_version
compile_module
build_pgf
run_scenario
inspect_grammar
```

A new operation kind requires:

1. one documented purpose;
2. one input contract;
3. one GF-version mapping;
4. one timeout policy;
5. one expected-evidence contract;
6. one test matrix;
7. coordinated updates to the external-tool and interfile locks.

Operation kinds must not be inferred from arbitrary argument arrays.

---

## 7. Common request invariants

Every GF request must satisfy:

```text
one resolved executable
one operation kind
one active project
one run identity
one explicit working directory
one ordered argument array
one finite timeout
one environment policy
zero or one stdin payload
zero or more declared expected artifacts
```

The builder must reject a request when:

- the executable is unresolved;
- the operation kind is unsupported;
- an argument contains a NUL character;
- the working directory is missing or invalid;
- a required module or script path is invalid;
- a path escapes its approved root;
- the timeout is non-positive;
- the GF version has no supported syntax contract;
- an expected artifact has no owner or approved destination.

---

## 8. Argument construction

### 8.1 Argument arrays

Arguments are represented as an ordered sequence:

```python
tuple[str, ...]
```

Required rules:

- one logical argument equals one sequence element;
- executable path is stored separately;
- no manual quoting is added for execution;
- no shell redirection is embedded;
- no platform command prefix is embedded;
- argument ordering is deterministic;
- empty arguments are permitted only when the GF operation explicitly requires them.

Correct:

```python
GfRequest(
    executable=Path("C:/Program Files/GF/bin/gf.exe"),
    arguments=("--version",),
    ...
)
```

Incorrect:

```text
"C:\Program Files\GF\bin\gf.exe" --version
```

as one executable command string.

### 8.2 No shell dependency

Normal GF execution must not require:

```text
cmd.exe
powershell
/bin/sh
bash
shell=True
```

A shell-capable operation requires a separate accepted security contract and is outside normal GF command construction.

### 8.3 User-controlled text

Project-controlled text must not become a host-shell fragment.

This includes:

- module names;
- source paths;
- scenario paths;
- input strings;
- marker identifiers;
- output filenames;
- project IDs.

Each value is validated according to its semantic role before it becomes an argument or standard-input payload.

---

## 9. GF version contract

GF command syntax is selected through an explicit version contract.

Conceptual registry:

```text
GF version range
    -> supported operations
    -> argument syntax
    -> path-option syntax
    -> artifact behavior
    -> diagnostic expectations
```

Rules:

- version probing uses the exact executable selected for the run;
- syntax selection occurs once the version is known;
- unsupported versions fail explicitly;
- unknown versions are handled according to the compatibility policy;
- version differences are localized in the GF adapter or command builder;
- validation stages must not branch independently on GF version;
- the selected version contract is recorded in request evidence.

A compatibility alias may map several tested GF versions to one command contract when their relevant syntax is equivalent.

---

## 10. Executable

The request uses the exact resolved GF executable path.

Rules:

- executable resolution occurs before request construction;
- the executable is not discovered again by the process adapter;
- a bare token such as `gf` is not authoritative after resolution;
- the path is passed separately from arguments;
- the resolved executable is recorded in evidence;
- disappearance or replacement after resolution is reported as a launch or integrity failure.

The executable is machine-local configuration. It must not be stored as a portable project fact.

---

## 11. Working directory

Every request declares one explicit working directory.

The working directory is selected according to the operation contract.

Typical ownership:

| Operation | Working-directory rule |
|---|---|
| `probe_version` | Approved environment or tool directory |
| `compile_module` | Active project or resolved source context |
| `build_pgf` | Active project root or declared build root |
| `run_scenario` | Active project root or declared scenario context |
| `inspect_grammar` | Context required by the inspected artifact |

Rules:

- the directory exists before launch;
- it is inside an approved root;
- it is not inferred from the caller's current directory;
- it is recorded in evidence;
- CLI and GUI resolve the same directory for equivalent requests;
- operation code must not change the process-wide current directory.

---

## 12. GF search paths

The request stores GF search paths as an ordered structured sequence:

```python
tuple[Path, ...]
```

The command builder receives this resolved sequence from the path-resolution boundary.

Rules:

- order is preserved;
- duplicates are removed only by the documented path-resolution policy;
- project-relative declarations are resolved before construction;
- RGL aliases are resolved before construction;
- path elements are validated before launch;
- the command-line joined representation is derived at this boundary only;
- the structured sequence remains the authoritative representation.

The builder must not:

- search the filesystem for missing path elements;
- read ambient `GF_LIB_PATH` as hidden project configuration;
- sort paths lexically when project order is meaningful;
- combine paths from several active projects.

---

## 13. Environment

GF process environment is derived from the documented environment policy.

The request records:

```text
environment_policy
explicit override keys
non-sensitive override values
redaction markers
```

The request must not record or report the complete inherited environment.

Rules:

- the builder does not mutate `os.environ`;
- environment changes are scoped to one child process;
- ambient GF path variables are neutralized or handled explicitly;
- secret values are redacted;
- project metadata does not override machine-local environment policy;
- equivalent CLI and GUI requests use equivalent environment construction.

---

## 14. Standard input

### 14.1 No standard input

Operations such as version probing or direct module compilation normally use:

```text
stdin_payload = null
```

### 14.2 Native `.gfs` scenario input

`run_scenario` supplies reviewed native GF shell content through standard input.

Rules:

- the `.gfs` file is project-owned;
- the file is read as documented UTF-8 text;
- the content is converted to one explicit byte payload;
- no intermediate operating-system shell is used;
- the script hash is recorded;
- the original script is not modified;
- marker and assertion metadata remain outside invalid GF pseudo-syntax;
- prohibited scenario commands are rejected according to the scenario security contract.

The process adapter passes the payload unchanged.

---

## 15. Named operation contracts

### 15.1 `probe_version`

Inputs:

```text
resolved executable
working directory
environment policy
probe timeout
```

Output expectation:

```text
process evidence containing version text or an explicit probe failure
```

Invariants:

- uses the exact run executable;
- does not depend on project source;
- produces no project artifact;
- non-zero exit, timeout and unparseable output remain distinct;
- raw stdout and stderr are preserved.

### 15.2 `compile_module`

Inputs:

```text
module or source entry
ordered GF search paths
active project context
compile timeout
artifact destination policy
```

Expected evidence:

```text
stdout
stderr
exit state
compile diagnostics
expected .gfo evidence when required
```

Invariants:

- static scanning is not part of command construction;
- module identity is validated before launch;
- command syntax is version-selected;
- generated artifacts remain inside approved build or run roots;
- a zero exit code does not override a missing required artifact.

### 15.3 `build_pgf`

Inputs:

```text
release entrypoint or entrypoints
ordered GF search paths
active project context
PGF options
build timeout
expected PGF declaration
```

Expected artifact declaration includes:

```text
logical role
expected filename
approved destination
required flag
minimum validity checks
```

Invariants:

- PGF construction is distinct from per-file compilation;
- entrypoint order is deterministic;
- the expected PGF name is project-owned;
- the artifact destination is run-owned;
- stale PGF files cannot satisfy the current request;
- missing, empty or misplaced PGF output is a contract failure.

### 15.4 `run_scenario`

Inputs:

```text
scenario ID
scenario script
ordered GF search paths
working directory
input assets
scenario timeout
declared artifact expectations
```

Expected evidence:

```text
raw stdout
raw stderr
exit state
marker evidence
normalized output reference
gold-comparison inputs
generated artifacts
```

Invariants:

- one request executes one registered scenario;
- execution uses a fresh GF process;
- raw evidence is preserved before normalization;
- a zero exit code does not override missing required markers;
- normal validation never updates gold files.

### 15.5 `inspect_grammar`

This operation covers bounded, documented GF inspection commands used by diagnostics or project validation.

It must define:

- the inspected subject;
- permitted GF commands;
- bounded output;
- timeout;
- expected evidence;
- whether the operation is normative or diagnostic.

Arbitrary interactive GF command execution is outside this operation.

---

## 16. Expected artifacts

An expected artifact declaration contains:

```text
artifact_role
relative_destination
required
expected_type
freshness_policy
minimum_size
content or identity checks
```

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ExpectedArtifact:
    role: str
    relative_destination: PurePosixPath
    required: bool
    expected_type: str
    freshness_policy: str
    minimum_size: int | None
```

Rules:

- destination is resolved before launch;
- destination remains inside an approved run or build root;
- each artifact role has one writer;
- expected artifacts are inventoried before execution when freshness matters;
- verification occurs after execution;
- stale artifacts do not satisfy the request;
- required missing artifacts produce a contract failure distinct from process launch or GF diagnostic failure;
- the process adapter reports produced files but does not decide validation success.

---

## 17. Timeout

Every request has a finite timeout.

The timeout is selected from the operation policy and run budget.

Rules:

- timeout is expressed in seconds or another documented monotonic duration unit;
- the value is positive;
- operation timeout does not exceed the remaining run budget;
- finalization reserve is not consumed by new tool execution;
- timeout is recorded in request evidence;
- timeout produces a distinct process termination state;
- partial stdout, stderr and produced artifacts are retained.

---

## 18. Redacted display command

GF Wordbench may render a human-readable command for logs and reports.

The display form:

- identifies the executable;
- preserves argument order;
- quotes values for readability only;
- redacts secrets and sensitive environment values;
- may replace approved absolute prefixes with tokens;
- clearly identifies omitted or bounded standard input;
- must not be executed.

Example:

```text
"C:/Program Files/GF/bin/gf.exe" <version-specific arguments>
cwd=<PROJECT_ROOT>
stdin=<scenario:parse.gfs sha256:...>
```

The display renderer must not reconstruct arguments from prose.

---

## 19. Request evidence

Before launch, Wordbench records as applicable:

```text
request ID
operation kind
project ID
run ID
GF executable
GF version contract
ordered arguments
working directory
structured GF search paths
environment policy
redacted overrides
stdin presence and content hash
timeout
expected artifacts
redacted display command
```

Evidence paths follow the persisted-schema and run-artifact contracts.

Sensitive values are redacted without altering the actual execution request.

---

## 20. Process-result boundary

The process adapter returns structured evidence equivalent to:

```text
launch state
exit code
stdout path
stderr path
duration
timeout state
cancellation state
termination detail
produced or changed paths
output truncation state
```

Command construction does not assign:

- validation status;
- diagnostic class;
- directness;
- blocker relationships;
- gold result;
- release readiness.

Those decisions occur after raw evidence is available.

---

## 21. Artifact verification

Artifact verification runs after process completion.

Verification distinguishes:

```text
process launch failure
process timeout or cancellation
GF-reported failure
successful process with missing artifact
successful process with invalid artifact
successful process with valid artifact
```

A required artifact is valid only when:

- it belongs to the current request;
- it exists at the approved destination;
- it has the expected type;
- it satisfies minimum size or content checks;
- it is not stale;
- it remains inside the approved artifact root.

An artifact failure does not rewrite raw GF stdout or stderr.

---

## 22. Error model

Command-construction failures are configuration, contract or security errors.

Examples:

- unsupported operation kind;
- unsupported GF version;
- invalid module identity;
- invalid working directory;
- unresolved GF search path;
- path escape;
- invalid timeout;
- NUL in an argument;
- expected artifact outside the run root;
- conflicting artifact ownership.

No process is launched when request construction fails.

Launch and process failures are represented by the external-tool result and remain distinct from construction failures.

---

## 23. Security rules

Required protections:

- argument arrays instead of shell strings;
- no uncontrolled shell execution;
- explicit executable path;
- explicit working directory;
- validated project and artifact paths;
- finite timeouts;
- bounded standard input and output;
- environment redaction;
- no complete environment dump;
- no project-controlled executable selection;
- no arbitrary diagnostic command;
- no writes outside approved roots;
- no `gf-portfolio` path or runtime dependency.

A change that expands executable, network, filesystem or mutation capability requires security review.

---

## 24. Determinism

Equivalent validated semantic inputs produce equivalent:

- operation kind;
- argument order;
- GF search-path order;
- working-directory choice;
- environment policy;
- standard-input bytes;
- expected-artifact declarations;
- timeout class;
- redacted display structure.

Machine-local absolute paths and run IDs may differ, but their semantic roles remain identical.

---

## 25. Tests

Required command-construction coverage includes:

### 25.1 Common construction

- one logical argument per sequence element;
- paths containing spaces;
- Unicode paths and module names where permitted;
- NUL rejection;
- no shell dependency;
- deterministic argument order;
- redacted display rendering;
- invalid timeout;
- invalid working directory;
- path containment failure.

### 25.2 Version probing

- supported version output;
- non-zero exit;
- timeout;
- empty output;
- unparseable output;
- executable with spaces;
- raw evidence retention.

### 25.3 Compilation

- valid module;
- missing module;
- ordered GF paths;
- version-specific syntax;
- compile timeout;
- stale `.gfo` rejection;
- required `.gfo` missing after zero exit;
- output containment.

### 25.4 PGF construction

- deterministic entrypoint order;
- expected PGF declaration;
- valid PGF;
- missing PGF;
- empty PGF;
- stale PGF;
- unexpected filename;
- artifact outside owned root.

### 25.5 Scenarios

- native `.gfs` standard input;
- exact payload bytes;
- script hash;
- fresh process request;
- marker metadata outside command syntax;
- prohibited scenario command;
- missing script;
- timeout;
- generated-artifact declaration.

### 25.6 Security and platform behavior

- Windows executable path with spaces;
- POSIX executable permission;
- no manual executable quoting;
- environment redaction;
- ambient GF path neutralization;
- no shell metacharacter interpretation;
- equivalent CLI and GUI request construction.

---

## 26. Change control

A command-contract change identifies:

```text
operation kind
affected GF versions
old syntax
new syntax
working-directory impact
GF path impact
environment impact
stdin impact
artifact impact
timeout impact
security impact
compatibility impact
tests
```

Coordinated documents include, as applicable:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/validation/SCENARIO_VALIDATION.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/PERSISTED_SCHEMA_LOCK.md
```

A local validation stage must not introduce a new GF syntax variation independently.

---

## 27. Related documents

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/validation/SCENARIO_VALIDATION.md
docs/scenarios/SCENARIO_FORMAT.md
SECURITY.md
```

---

## 28. Governing rule

> Construct one validated, typed GF request for one named operation; execute it without a shell; preserve raw evidence; and verify declared artifacts after execution.

No entrypoint, validation stage, report writer or project document may construct a competing GF command contract.
