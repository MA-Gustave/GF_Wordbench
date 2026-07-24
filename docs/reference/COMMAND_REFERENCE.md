# GF Wordbench — Command Reference

**Document ID:** `GF-WB-COMMAND-REFERENCE`  
**Status:** Normative supporting reference  
**Document version:** `2.0.0`  
**Applies to:** command-boundary ownership, external GF requests, approved diagnostic-tool requests, process safety, evidence capture, and compatibility translation  
**Owner:** GF Wordbench maintainers  
**CLI authority:** `docs/usage/CLI_REFERENCE.md`  
**External-tool authority:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Last reviewed:** `2026-07-24`  
**Target path:** `docs/reference/COMMAND_REFERENCE.md`

---

## 1. Purpose

This document defines how GF Wordbench translates application intent into structured external-tool requests and how those requests are executed, recorded, and interpreted.

It does not define a second user-facing command surface.

The ownership boundary is:

```text
docs/usage/CLI_REFERENCE.md
    owns command names, groups, arguments, options, aliases, help text,
    defaults, examples, and user-visible command behavior

docs/reference/COMMAND_REFERENCE.md
    owns structured external requests, process invariants, evidence fields,
    tool-specific command construction, and compatibility translation rules
```

When the two documents overlap, `CLI_REFERENCE.md` governs user invocation. This document governs the requests Wordbench sends to GF and other approved executables.

The central rule is:

> Users and automation invoke GF Wordbench through its canonical CLI contract; GF Wordbench invokes external tools only through typed, allowlisted, evidence-producing command contracts.

---

## 2. Scope

This document governs:

- ownership of CLI parsing and dispatch boundaries;
- translation from application requests to external-tool requests;
- GF executable resolution;
- GF version probing;
- GF source compilation;
- PGF construction;
- native `.gfs` scenario execution;
- approved diagnostic-tool execution;
- path and working-directory construction;
- timeouts, cancellation, and process termination;
- stdout, stderr, exit-state, and artifact evidence;
- compatibility translation from accepted legacy inputs;
- deterministic command rendering;
- command-security requirements;
- tests for command construction and execution boundaries.

This document does not govern:

- exact CLI spelling;
- help text;
- option placement;
- command examples intended for users;
- numeric exit codes;
- complete status vocabularies;
- project configuration field names;
- report layout;
- Portfolio commands or schemas;
- arbitrary shell commands;
- GF language semantics.

---

## 3. Related normative documents

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/usage/CLI_REFERENCE.md
docs/reference/EXIT_CODES.md
docs/reference/STATUS_VALUES.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMMAND_CONSTRUCTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/diagnostics/TOOL_CATALOG.md
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
docs/reports/ARTIFACT_MANIFEST.md
```

Ownership remains singular:

| Subject | Owner |
|---|---|
| User command names and options | `docs/usage/CLI_REFERENCE.md` |
| External process contract | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| GF-specific command construction | this document and GF owner documents |
| Process lifecycle | `docs/architecture/PROCESS_EXECUTION_MODEL.md` |
| Paths and environment | `docs/configuration/ENVIRONMENT_AND_PATHS.md` |
| Persisted evidence | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Exit-code mapping | `docs/reference/EXIT_CODES.md` |
| Diagnostic tool allowlist | `docs/diagnostics/TOOL_CATALOG.md` |

---

## 4. Product boundary

Every Wordbench command resolves:

```text
one workspace
one active project
one run
one normative target or one bounded target set from that project
```

Wordbench commands must not:

- select several active projects in one run;
- discover a Portfolio workspace registry;
- aggregate several Wordbench workspaces;
- invoke external tools on behalf of Portfolio;
- read or write `gf-portfolio` private schemas, state, or storage;
- require Portfolio to resolve GF or complete a run.

The allowed product dependency remains:

```text
gf-portfolio
    → completed public versioned Wordbench artifacts

GF Wordbench
    -X→ gf-portfolio runtime, private APIs, database, or configuration
```

---

## 5. Architectural ownership

Command processing crosses the hexagonal architecture through explicit boundaries.

```text
CLI / GUI / automation entrypoint
    → application use case
    → domain request
    → external-tool port
    → GF or diagnostic-tool adapter
    → process port
    → local process adapter
    → approved executable
```

Result flow returns as data:

```text
process evidence
    → external-tool result
    → validation or diagnostic result
    → run result
    → reporting and entrypoint presentation
```

### 5.1 Entrypoints

Entrypoints own:

- argument collection;
- surface-level validation;
- conversion to application requests;
- rendering completed results;
- mapping results to the exit-code registry.

Entrypoints do not own:

- GF argument construction;
- process execution;
- path discovery;
- release rules;
- report generation;
- project mutation outside explicit project-writing use cases.

### 5.2 Application use cases

Application use cases own:

- intent validation;
- active-project resolution requests;
- mode and selector policy;
- orchestration of ports;
- write-safety classification;
- confirmation requirements;
- run creation and completion requests.

### 5.3 External-tool ports

Ports define typed requests and results without exposing:

- `subprocess` objects;
- shell command strings;
- platform-specific handles;
- GUI objects;
- private GF adapter classes;
- Portfolio types.

### 5.4 Adapters

Adapters own:

- executable-specific arguments;
- version-compatible flags;
- stdin construction;
- process request construction;
- raw response translation;
- expected artifact checks.

Adapters do not own project identity, run status, release decisions, or report wording.

---

## 6. Canonical structured request

Every external operation is represented by a structured request containing, as applicable:

```text
request ID
tool ID
operation ID
resolved executable
ordered argument vector
working directory
environment additions
environment removals
stdin bytes or stdin source reference
encoding
timeout
cancellation token or cancellation reference
output-size limits
approved read roots
approved write roots
expected artifacts
mutability class
network policy
evidence policy
```

### 6.1 Required invariants

- The executable and arguments are stored separately.
- Arguments preserve order.
- Empty arguments remain distinguishable from absent arguments.
- The working directory is explicit.
- Environment changes are explicit and local to the process.
- Standard input is explicit.
- Every external request has a finite timeout.
- Read and write roots are resolved before launch.
- The request identifies one active project and one run through application context.
- The request does not contain a shell-redirection expression.
- Secrets are omitted or explicitly redacted from persisted evidence.

### 6.2 Command rendering

A human-readable command may be rendered for logs or reports.

The rendered command:

- is derived from the structured request;
- is not reparsed for execution;
- uses platform-appropriate display quoting;
- clearly marks redacted arguments;
- does not become the authoritative request representation.

---

## 7. Canonical structured result

Every external operation returns a structured result containing, as applicable:

```text
request ID
tool ID
operation ID
launch state
exit code or absence of exit code
termination reason
started time
finished time
duration
stdout evidence reference
stderr evidence reference
stdout truncation state
stderr truncation state
timeout state
cancellation state
process-tree termination outcome
produced artifacts
missing expected artifacts
changed artifacts
adapter diagnostics
```

The result keeps these conditions distinct:

- executable not found;
- permission failure;
- invalid working directory;
- launch failure;
- timeout;
- cancellation;
- forced termination;
- non-zero exit;
- zero exit with missing required artifact;
- completed tool execution with validation failure;
- evidence-write failure;
- adapter contract failure.

A report must not collapse these conditions into one generic failure.

---

## 8. Command safety classes

Application commands are assigned a safety class by the CLI and application contracts.

| Class | Allowed effect |
|---|---|
| Read-only | Reads configuration, project facts, runs, or artifacts |
| Probe | Executes a bounded capability or version probe without modifying project assets |
| Run-writing | Creates one run and writes run-owned evidence |
| Project-writing | Modifies explicitly selected project-owned assets |
| Run-maintenance | Archives, restores, verifies, or removes selected run-owned evidence |
| Migration-writing | Reads one source representation and writes an explicit canonical destination |
| Destructive | Replaces or removes approved owned content after explicit authorization |

This document does not enumerate command names for these classes. `CLI_REFERENCE.md` maps commands to safety classes.

### 8.1 Read-only invariant

Read-only commands must not:

- modify `project.toml`;
- modify source;
- modify scenarios, inputs, or golds;
- create a validation run unless the command contract explicitly classifies the operation as run-writing;
- regenerate missing evidence;
- update application state except for non-semantic UI behavior explicitly allowed by the state contract.

### 8.2 Run-writing invariant

Run-writing commands may write only:

- the new run directory;
- approved temporary process artifacts;
- bounded application-state pointers that do not become project or run authority.

### 8.3 Project-writing invariant

Project-writing commands require:

- explicit user intent;
- path validation;
- a preview or dry run where destructive;
- atomic replacement where applicable;
- preservation or explicit discard policy;
- audit evidence for the write.

---

## 9. Configuration and resolution

Project facts and environment facts have different owners.

### 9.1 Project-owned facts

Examples:

```text
project ID
language identity
source selection
entrypoints
checkpoints
scenario registry
gold mappings
release entrypoint
expected PGF identity
```

Authority:

```text
project/project.toml
and project-owned contract documents where the schema delegates detail
```

CLI input may narrow a development operation where the CLI contract permits it. It must not create a second active-project definition.

### 9.2 Environment-owned facts

Examples:

```text
GF executable
RGL installation root
resolved GF path
output root
process timeout
local cache or state location
```

Resolution follows the environment and path references.

### 9.3 Recorded resolution

Run evidence records resolved values required to reproduce or explain execution, including:

- executable identity;
- executable-resolution source;
- GF version;
- working directory;
- ordered path inputs;
- effective GF path;
- relevant environment changes;
- timeout;
- approved output roots.

Raw CLI arguments alone are insufficient evidence.

---

## 10. Process execution rules

### 10.1 No implicit shell

Normal tool execution uses:

```text
executable + ordered argument vector
```

An intermediate shell is prohibited unless a separate accepted contract explicitly requires it.

Prohibited construction:

```text
"<gf> <flags> <file> > output.txt"
```

Required construction:

```text
executable: <resolved-gf>
arguments: [<flag-1>, <flag-2>, <source>]
stdout: captured by the process adapter
```

### 10.2 Finite execution

Every process has:

- a timeout;
- an output-size policy;
- a cancellation policy;
- a termination policy;
- process-tree cleanup behavior where supported.

### 10.3 Path safety

Before launch:

- executable path is validated;
- working directory is validated;
- project-relative paths are resolved;
- traversal is rejected;
- approved read and write roots are checked;
- symlink and junction policy is applied;
- Windows case-insensitive equivalence is considered;
- source and output roots remain distinct.

### 10.4 Evidence before interpretation

Raw stdout, stderr, exit state, timing, termination, and artifacts are captured before:

- diagnostic parsing;
- normalization;
- classification;
- comparison;
- reporting.

---

## 11. GF executable resolution

The GF executable is resolved through the documented environment policy.

Allowed resolution sources include:

1. explicit invocation or environment configuration accepted by the CLI contract;
2. approved local application configuration;
3. documented platform discovery;
4. explicit failure.

Project configuration must not contain a machine-specific executable path as portable language identity.

Resolution evidence includes:

```text
requested tool ID
resolved executable
resolution source
existence and executability checks
version-probe result
platform
```

Failure to resolve GF is a configuration or launch failure, not a GF language diagnostic.

---

## 12. GF version probe

### 12.1 Structured request

```text
tool ID: gf
operation ID: version
executable: <resolved-gf>
arguments: ["--version"]
working directory: <approved workspace or project directory>
stdin: absent
timeout: bounded version-probe timeout
mutability: read-only probe
```

### 12.2 Evidence

Preserve:

- stdout;
- stderr;
- exit code;
- launch state;
- timeout state;
- normalized version when recognized;
- raw first meaningful version text;
- compatibility interpretation.

Both output streams remain available even when one supplies the preferred display line.

### 12.3 Interpretation

Unknown or unparsable output remains unknown. It must not be silently treated as compatible.

---

## 13. GF source compilation

Compilation validates one selected source or configured module under one resolved active-project context.

### 13.1 Request inputs

```text
selected source identity
source path
resolved GF executable
resolved ordered GF path
working directory
compile timeout
GF compatibility profile
run-owned artifact root
optional performance-evidence request
```

### 13.2 Argument construction

The GF adapter constructs the version-compatible equivalent of:

```text
<gf>
-batch
<verbosity options>
<GF path options>
<artifact-output options>
<selected source>
```

The source argument remains the selected target and is not inferred from a directory name or previous run.

Exact GF flags are owned by `GF_COMMAND_CONSTRUCTION.md` and compatibility adapters.

### 13.3 Static scan separation

Compilation does not invoke static scanning.

Static scanning does not invoke compilation.

The `validation` application use case coordinates both and preserves separate results.

### 13.4 Success conditions

Compilation success requires all applicable conditions:

- process launched;
- timeout did not occur;
- cancellation did not occur;
- exit status satisfies the GF operation contract;
- no fatal GF diagnostic invalidates the operation;
- required current-run artifacts exist;
- artifacts are attributable to this request;
- required evidence was written.

A pre-existing `.gfo` file does not prove current compilation success.

### 13.5 Mutation boundary

Compilation must not modify:

- project source;
- project configuration;
- scenarios;
- inputs;
- golds;
- project documentation.

Generated GF artifacts are written or collected only under approved run-owned locations.

---

## 14. PGF construction

PGF construction is a distinct GF operation with an explicitly configured release entrypoint and expected artifact identity.

### 14.1 Request inputs

```text
resolved release entrypoint or ordered entrypoints
resolved GF path
GF compatibility profile
optimization policy
working directory
PGF timeout
run-owned output root
expected PGF identity
```

### 14.2 Argument construction

The GF adapter constructs the supported equivalent of:

```text
<gf>
-make
<PGF optimization options>
<GF path options>
<entrypoint-1>
[<entrypoint-N> ...]
```

The adapter must not guess the release entrypoint from whichever file compiled most recently.

### 14.3 Success conditions

PGF construction succeeds only when:

- process launched;
- execution completed within budget;
- exit status satisfies the operation contract;
- no fatal diagnostic invalidates the build;
- expected PGF exists;
- expected PGF is non-empty;
- freshness or attribution checks associate it with this request;
- the artifact is stored under the run-owned boundary;
- the manifest records it.

A diagnostic PGF built under different options is not substituted for a release artifact whose policy requires other options.

---

## 15. Native `.gfs` scenario execution

Scenarios are project-owned native `.gfs` files executed through GF.

### 15.1 Request inputs

```text
scenario ID
scenario path
declared input references
resolved GF executable
working directory
GF path context
scenario timeout
required markers and assertions
normalization profile
gold reference when comparison applies
run-owned evidence roots
```

### 15.2 Process construction

Shell redirection is not used.

The adapter:

1. reads the approved `.gfs` file;
2. validates its path and encoding;
3. supplies its bytes or text through process stdin;
4. invokes GF using an ordered argument vector;
5. captures stdout and stderr separately.

Structured representation:

```text
executable: <resolved-gf>
arguments: <version-compatible GF shell arguments>
stdin source: <registered scenario path>
working directory: <resolved project context>
```

### 15.3 Completion conditions

A zero exit code alone is insufficient.

Scenario completion requires, as applicable:

- process completion;
- expected begin and end markers;
- required section markers;
- required assertions;
- output normalization;
- gold comparison;
- expected artifact checks.

### 15.4 Trust boundary

A `.gfs` file is executable or semi-executable tool input.

Normal project policy prohibits:

- host-shell escapes;
- access outside approved roots;
- unbounded generation;
- arbitrary external commands;
- silent project or gold mutation.

---

## 16. GF shell operations used by scenarios

Scenario documentation owns exact script structure and marker conventions.

The GF adapter and compatibility profile may support operations for:

| Capability | GF shell operation family |
|---|---|
| Import or load grammar | import/load operation |
| Parse | `p` |
| Linearize | `l` |
| Generate | `gr` |
| Morphological analysis | `ma` |
| Grammar inspection | print/inspect operations |
| Missing linearizations | missing-function inspection |
| Concrete computation | concrete computation operation |
| Dependency inspection | dependency display operation |
| Quit | `q` |

Exact syntax is version-gated through `GF_SCRIPT_EXECUTION.md`.

This table describes operation families required by Wordbench scenarios. It is not a replacement for the official GF shell reference.

---

## 17. Diagnostic-tool requests

Executable diagnostic tools are available only through the controlled registry defined by ADR-0013 and `TOOL_CATALOG.md`.

Each registry entry defines:

```text
tool ID
purpose
executable resolution
allowed operations
allowed arguments
working-directory policy
input policy
timeout
output limits
mutability
network policy
evidence role
parser and normalization
```

### 17.1 Prohibitions

Wordbench must not:

- execute an arbitrary user-supplied command;
- accept an unrestricted command template from project configuration;
- use a shell to compose diagnostic pipelines;
- allow a diagnostic tool to mutate project files during normal validation;
- treat optional AI output as GF authority;
- expose Portfolio execution through the Wordbench tool registry.

### 17.2 Result ownership

Diagnostic tools produce evidence consumed by `diagnostics`.

They do not directly determine:

- GF compilation status;
- run status;
- release decision;
- gold acceptance;
- Portfolio readiness.

---

## 18. External command evidence

For every external request, preserve:

```text
request ID
tool ID
operation ID
resolved executable
ordered arguments
working directory
approved environment changes
stdin source identity or absence
started time
finished time
duration
launch state
exit code
timeout state
cancellation state
termination outcome
stdout evidence reference
stderr evidence reference
output truncation
produced artifacts
missing expected artifacts
adapter diagnostics
```

### 18.1 Redaction

Evidence may redact:

- passwords;
- tokens;
- private keys;
- credentials;
- secret environment values;
- secret arguments.

Redaction must preserve enough structure to explain the request.

### 18.2 Artifact attribution

An artifact is accepted as current only when evidence supports that it was produced or updated by the current request.

Attribution may use:

- pre-execution inventory;
- post-execution inventory;
- path;
- size;
- timestamp;
- content hash;
- producer identity;
- manifest entry.

### 18.3 Raw and normalized evidence

Raw output remains separate from:

- parsed diagnostics;
- normalized comparison material;
- human summaries;
- AI-ready excerpts.

A normalized value never replaces the raw evidence that produced it.

---

## 19. Compatibility translation

Legacy GF Audit inputs may be accepted only through explicit compatibility handling at the CLI or migration boundary.

### 19.1 Translation rules

Compatibility input is:

1. parsed by the compatibility-aware entrypoint;
2. translated to the canonical Wordbench application request;
3. validated through current project and environment contracts;
4. recorded using canonical names in run artifacts;
5. warned about through the documented deprecation channel.

### 19.2 Prohibited propagation

Legacy names and shapes must not propagate into:

- domain models;
- current schemas;
- reports;
- manifests;
- project configuration;
- external GF adapters;
- Portfolio artifacts.

### 19.3 Source-selection migration

Legacy scan directories, globs, roots, and flat mode selectors do not become active-project identity.

Project-owned selection comes from `project/project.toml`. A CLI selector may narrow one permitted development run without rewriting project policy.

Exact accepted aliases and their replacements belong exclusively to `CLI_REFERENCE.md`.

---

## 20. Status and exit separation

The command boundary preserves distinct concepts:

```text
process execution state
tool result
validation result
run terminal result
release decision
CLI exit code
```

The exact vocabularies and numeric mappings belong to their owner references.

Rules:

- report creation does not imply validation success;
- a GF validation failure is not a launch failure;
- timeout is not an ordinary GF source failure;
- cancellation is not success;
- a completed failing validation may still produce a complete run artifact set;
- the entrypoint maps the structured result to an exit code without modifying the result.

---

## 21. Determinism

Equivalent project, environment, request, GF version, and input must produce deterministic:

- command argument order;
- GF path order;
- scenario order;
- evidence naming;
- artifact inventory order;
- rendered command structure;
- result ordering.

Parallel execution must not alter persisted ordering.

Command rendering may differ in platform quoting while the underlying executable and argument vector remain equivalent.

---

## 22. Security rules

### 22.1 Injection prevention

- Use argument vectors.
- Do not interpolate project text into shell strings.
- Validate every path before launch.
- Treat `.gf`, `.gfs`, configuration, and inputs as untrusted tool input.
- Reject unapproved executable IDs.
- Enforce the diagnostic-tool allowlist.
- Bound stdout and stderr capture.
- Use finite timeouts.
- Terminate process trees where required and supported.

### 22.2 Filesystem containment

External requests may read and write only within approved roots.

Generated artifacts must not escape the run-owned output boundary.

### 22.3 Network policy

GF execution is local unless an explicit accepted contract says otherwise.

Diagnostic tools default to no network access unless their registry entry explicitly defines and secures it.

### 22.4 Secrets

Complete environment dumps must not be persisted.

Only the minimum relevant environment values are recorded, with redaction where required.

---

## 23. Error handling

Command construction and execution distinguish:

```text
invalid application request
unresolved executable
unsupported tool version
unsafe path
invalid argument contract
launch failure
timeout
cancellation
non-zero exit
output limit exceeded
missing artifact
evidence-write failure
adapter parsing failure
```

An adapter must not convert an unexpected exception into a successful empty result.

Partial evidence is retained when safe.

The run coordinator decides continuation and completion according to the run contract.

---

## 24. Tests

### 24.1 Command-construction tests

Tests cover:

- executable and arguments remain separate;
- deterministic argument order;
- paths containing spaces;
- Unicode paths and input;
- Windows and POSIX path behavior;
- GF path ordering;
- source target placement;
- version-compatible flags;
- absent optional arguments;
- explicit stdin handling;
- no shell redirection;
- secret redaction;
- stable rendered command.

### 24.2 Process-boundary tests

Tests cover:

- executable missing;
- permission failure;
- working directory missing;
- successful zero exit;
- non-zero exit;
- stdout-only and stderr-only output;
- timeout;
- cancellation;
- process-tree termination;
- output truncation;
- evidence-write failure;
- expected artifact present;
- expected artifact missing;
- stale artifact rejection.

### 24.3 GF operation tests

Tests cover:

- version probe;
- source compilation;
- PGF construction;
- scenario execution through stdin;
- marker failure;
- normalization and raw-evidence separation;
- compatibility-profile selection;
- path resolution;
- no source mutation;
- no gold mutation.

### 24.4 Architecture tests

Tests verify:

- entrypoints do not construct GF commands;
- application services use ports;
- domain models do not import adapters;
- GF adapter does not import reporting;
- reports do not launch tools;
- only approved process adapters use process libraries;
- arbitrary commands cannot be registered through project configuration;
- Wordbench does not import or call `gf-portfolio`.

### 24.5 Compatibility tests

Tests verify:

- accepted legacy inputs translate deterministically;
- canonical models and artifacts contain current names;
- unsupported legacy inputs fail explicitly;
- compatibility warnings do not corrupt machine-readable output;
- legacy inputs cannot bypass path, safety, or release rules.

---

## 25. Change control

A command-boundary change includes:

- changing a structured request or result;
- changing executable resolution;
- changing GF arguments;
- changing working-directory policy;
- changing stdin behavior;
- changing timeouts or output limits;
- changing artifact expectations;
- changing safety or mutability;
- adding a diagnostic tool;
- changing compatibility translation;
- changing persisted evidence.

The coordinated change updates:

1. the owning application use case;
2. the port contract;
3. the adapter;
4. process execution behavior;
5. evidence and persisted schemas;
6. diagnostics and reporting consumers;
7. CLI documentation when user behavior changes;
8. tests;
9. security review;
10. external-tool and interfile locks when their contracts change.

User-facing command changes are made in `CLI_REFERENCE.md`, not independently in this file.

---

## 26. Drift indicators

Command drift exists when:

- this document and `CLI_REFERENCE.md` define competing command names;
- an entrypoint constructs GF arguments;
- a report launches a tool;
- a scanner invokes compilation directly;
- a diagnostic classifier launches arbitrary commands;
- a project configuration field contains a shell command;
- a rendered command is reparsed for execution;
- a timeout is omitted;
- stdout or stderr is discarded before interpretation;
- stale artifacts satisfy current execution;
- environment-specific paths become project identity;
- compatibility names appear in current schemas;
- direct process-library use appears outside approved adapters;
- a tool writes outside approved roots;
- Wordbench invokes Portfolio internals;
- a command changes project files without explicit project-writing intent.

Detected drift is resolved by restoring the owner contract or adopting a coordinated architectural decision.

---

## 27. Review checklist

```text
[ ] CLI_REFERENCE.md remains the only user-command authority
[ ] one active project and one run are identified
[ ] application intent is converted to a typed request
[ ] executable and ordered arguments remain separate
[ ] working directory and environment are explicit
[ ] stdin behavior is explicit
[ ] timeout and cancellation are explicit
[ ] read and write roots are approved
[ ] no uncontrolled shell is used
[ ] raw stdout and stderr are preserved
[ ] execution, tool, validation, run, release, and exit meanings remain distinct
[ ] expected artifacts are attributable to the current request
[ ] compatibility input is canonicalized at the boundary
[ ] current schemas do not emit legacy names
[ ] diagnostic tools are allowlisted
[ ] project and gold mutation require explicit operations
[ ] Wordbench remains independent of gf-portfolio
[ ] tests and owner documents agree
```

---

## 28. Enforcement rule

GF Wordbench preserves one command boundary:

```text
canonical user intent
    → application request
    → typed external-tool request
    → approved adapter
    → controlled process execution
    → raw evidence
    → structured result
```

Therefore:

> No user-facing command contract may be duplicated outside `CLI_REFERENCE.md`, and no external executable may be invoked through an uncontrolled shell string, an unregistered tool definition, an unsafe path, or a request that cannot produce traceable evidence.
