# GF Wordbench — GF Toolchain Integration

**Document ID:** `GF-WB-GF-TOOLCHAIN`  
**Status:** Normative architecture and integration specification  
**Applies to:** GF Wordbench framework and one selected GF language context  
**Owner:** GF Wordbench maintainers  
**Canonical path:** `docs/gf/GF_TOOLCHAIN_INTEGRATION.md`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Document version:** `1.1.0`  
**Last reviewed:** 2026-08-05

---


## ADR-0015 alignment — selected source and optional validation profile

The current startup model is path-resolved:

- the user selects a GF source file or an RGL language directory directly;
- Wordbench reads that source tree in place and does not copy it into this repository;
- `ResolvedLanguageContext` owns the selected path, resolved language identity, source root, RGL root, discovered entrypoints and effective GF-path facts;
- an explicit `ValidationProfile` is optional and may add only non-derivable policy such as additional selection filters, required or release entrypoints, checkpoints, scenarios, inputs, golds, PGF targets, required artifacts and release gates;
- a legacy `project/project.toml` may be read only when explicitly supplied as a validation profile; it is not a mandatory root file or startup authority;
- run state, logs and artifacts are written under the configured output root, normally `<output-root>/<language-key>/run_<run-id>` (with `_gf_wordbench` as the framework default), never into the selected source tree.

Unless a section is explicitly describing legacy migration input, references to an “active project” or a root `project/` directory are superseded by this model.

---
## 1. Purpose

This document defines how GF Wordbench integrates the Grammatical Framework toolchain.

It explains:

- which responsibilities belong to GF;
- which responsibilities belong to GF Wordbench;
- how the GF executable is discovered and validated;
- how paths and process environments are resolved;
- how source modules are compiled;
- how PGF release artifacts are built;
- how native `.gfs` scenarios are executed;
- how parsing, linearization, generation, morphology, and introspection are validated;
- how stdout, stderr, exit codes, markers, and generated artifacts are interpreted;
- how evidence is preserved;
- how platform and GF-version differences are contained;
- how the integration is tested without duplicating GF internals.

This document is the architectural guide for the integration.

Cross-document product identity and authority order are locked in:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
```

The normative external-process boundary is locked in:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

Persisted fields and artifact schemas are locked in:

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Python-to-Python ownership and call boundaries are locked in:

```text
docs/INTERFILE_CONTRACT_LOCK.md
```

Language-specific GF module relationships are locked in:

```text
<validation-profile-root>/docs/INTERFILE_CONTRACT_LOCK.md
```

Executable diagnostic-tool registration is governed by:

```text
docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md
```

When this document and a lock or accepted ADR overlap, the lock or ADR governs the contract and this document explains the integration design.

---

## 2. Integration principle

GF Wordbench uses GF as the execution engine for GF semantics.

> GF Wordbench orchestrates, records, compares, and reports. GF compiles and executes GF grammars.

GF Wordbench must not create a competing implementation of:

- the GF source parser;
- the GF type checker;
- GF module resolution;
- GF compilation;
- the GF runtime;
- PGF serialization;
- parsing algorithms;
- linearization semantics;
- generation semantics;
- morphology semantics;
- GF shell command semantics.

GF Wordbench may perform static source scans, but their findings remain heuristics.

A scanner finding is not a GF compiler result.

A clean scanner result is not proof that a module compiles.

---

## 3. Authority boundaries

### 3.1 GF is authoritative for

GF is authoritative for:

- GF syntax;
- type checking;
- abstract and concrete module compatibility;
- resource, interface, and instance semantics;
- module imports;
- source-to-`.gfo` compilation;
- `.pgf` construction;
- grammar loading;
- parsing;
- linearization;
- random and exhaustive generation;
- morphology analysis;
- grammar introspection;
- missing-linearization detection;
- source and dependency introspection;
- native GF diagnostics.

### 3.2 GF Wordbench is authoritative for

GF Wordbench is authoritative for:

- executable selection;
- resolved GF version;
- command construction;
- argument ordering;
- working directory;
- GF search path construction;
- environment overrides;
- process timeout;
- process termination policy;
- stdout and stderr capture;
- raw evidence paths;
- expected artifact checks;
- scenario selection;
- scenario markers;
- output normalization;
- gold comparison;
- direct/downstream classification;
- regression comparison;
- run manifests;
- run status;
- human and machine reports.

### 3.3 Resolved context and validation-profile authority

The selected language context is authoritative for:

- project identity;
- language identity;
- source directory;
- entrypoint modules;
- checkpoint modules;
- project GF path additions;
- required scenarios;
- optional scenarios;
- scenario inputs;
- gold expectations;
- release artifacts;
- language-specific validation criteria.

The authoritative portable project configuration is:

```text
<validation-profile-root>/project.toml
```

### 3.4 Maintainer authority

Maintainers are authoritative for:

- accepting a new GF version;
- changing compatibility policy;
- approving gold updates;
- approving normalization changes;
- accepting known limitations;
- deciding whether a warning blocks release;
- approving additional external tools.

### 3.5 Workspace and Portfolio boundary

One GF Wordbench workspace contains exactly one selected GF language context.
Every GF operation belongs to one resolved project and one run.

GF Wordbench does not:

- discover or orchestrate several Wordbench workspaces;
- execute GF on behalf of a portfolio registry;
- aggregate multilingual readiness across projects;
- expose its private process runner as a required external API;
- require `gf-portfolio` code, storage, configuration, or services.

The independent `gf-portfolio` product may consume public, versioned, completed
Wordbench artifacts. That read-only consumer relationship does not change GF
execution ownership and creates no reverse dependency from Wordbench to Portfolio.

---

## 4. GF toolchain components used

GF Wordbench integrates the following GF capabilities.

| Capability | GF interface | GF Wordbench purpose |
|---|---|---|
| Version identification | executable version probe | compatibility and evidence |
| Module compilation | batch compiler | validate `.gf` source and produce `.gfo` |
| PGF construction | make mode | produce release `.pgf` |
| Shell execution | commands through stdin | execute `.gfs` scenarios |
| Grammar import | `import` / `i` | load source, object, or PGF grammar |
| Parse | `parse` / `p` | validate strings to abstract trees |
| Linearize | `linearize` / `l` | validate trees to strings |
| Random generation | `generate_random` / `gr` | bounded exploratory coverage |
| Exhaustive generation | `generate_trees` / `gt` | bounded deterministic coverage |
| Morphology | `morpho_analyse` / `ma` | validate lexical analysis |
| Abstract inspection | `abstract_info` / `ai` | inspect categories, functions, or expressions |
| Concrete operations | `show_operations` / `so` | inspect retained operations |
| Source inspection | `show_source` / `ss` | inspect compiled source surfaces |
| Dependencies | `show_dependencies` / `sd` | inspect module dependency information |
| Missing functions | `print_grammar -missing` / `pg -missing` | detect missing linearizations |
| Grammar information | `print_grammar` / `pg` | inspect categories, functions, languages, or words |
| Quit | `quit` / `q` | terminate scenarios explicitly |

Not every mode uses every capability.

---

## 5. Integration layers

The architecture separates six layers.

```text
configuration
→ GF request construction
→ process execution
→ raw evidence capture
→ GF-result interpretation
→ validation and reporting
```

### 5.1 Configuration layer

Resolves:

- executable;
- selected source root;
- RGL root;
- GF path;
- mode;
- timeouts;
- selected files;
- entrypoints;
- scenarios;
- output locations;
- compatibility policy.

### 5.2 Request-construction layer

Builds structured requests:

```text
executable
arguments[]
working_directory
environment_overrides{}
stdin_bytes or stdin_text
timeout
expected_artifacts[]
operation_kind
```

It does not start processes.

### 5.3 Process-execution layer

Owns:

- process launch;
- stream capture;
- timeout enforcement;
- cancellation;
- child-process termination;
- start/end timestamps;
- exit code;
- launch errors.

It does not understand GF dependency causality.

### 5.4 Raw-evidence layer

Writes:

- exact command representation;
- working directory;
- selected environment overrides;
- stdout;
- stderr;
- process metadata;
- tool-produced artifact inventory.

Raw evidence is written before semantic parsing or normalization.

### 5.5 Interpretation layer

Interprets GF-specific evidence:

- fatal diagnostic detection;
- error kind;
- missing marker;
- expected artifact absence;
- incomplete scenario;
- unsupported version;
- normalized output.

It preserves references to raw evidence.

### 5.6 Validation and reporting layer

Determines:

- validation status;
- diagnostic class;
- gold match;
- regression state;
- release gate outcome;
- reports.

Reports do not execute GF.

---

## 6. Integration ownership

The integration uses the following ownership.

| Responsibility | Owner |
|---|---|
| active-project configuration loading | projects module through an application port |
| run configuration and lifecycle | runs module and bootstrap composition |
| generic process execution | external-process port and platform process adapter |
| GF executable and version integration | GF anti-corruption adapter |
| GF path construction | GF path resolver inside the validation boundary |
| source-module compilation | validation module |
| PGF release construction | validation module |
| native `.gfs` execution | validation module |
| GF diagnostic parsing and classification | diagnostics module |
| output normalization and gold comparison | validation module |
| run orchestration | application use case coordinating projects, runs, validation, diagnostics, and reporting |
| result assembly and artifact publication | runs and reporting modules |
| human, machine, and AI-ready reports | reporting module |

Concrete filenames may change through a coordinated architectural update, but ownership and dependency direction remain stable.

---

## 7. Executable discovery

### 7.1 Accepted executable forms

GF may be configured as:

```text
gf
gf.exe
<absolute path to gf>
<absolute path to gf.exe>
```

### 7.2 Resolution order

Canonical resolution order:

1. explicit CLI value;
2. explicit GUI value;
3. application environment configuration;
4. persisted local application preference;
5. optional `PATH` lookup;
6. configuration failure.

The selected language context should not normally store a developer-specific absolute executable path.

### 7.3 Resolution invariants

The resolved executable must:

- be explicit in the resolved run configuration;
- exist or be resolvable before required validation;
- be recorded in `summary.json`;
- appear in structured process evidence;
- remain unchanged for the duration of one run;
- not be silently replaced after version probing;
- be passed separately from its arguments.

### 7.4 Validation

Before use, GF Wordbench should verify:

- the resolved path is not a directory;
- the process can be launched;
- the version probe completes or is explicitly skipped;
- a missing executable produces a configuration or launch error.

---

## 8. GF version probing

### 8.1 Purpose

Version probing provides:

- reproducibility;
- compatibility checking;
- report metadata;
- gold-regression context;
- platform diagnosis.

### 8.2 Request

Canonical request:

```text
<gf-executable> --version
```

A compatibility adapter may support another documented version option if required by a supported GF release.

### 8.3 Execution policy

Recommended defaults:

```text
timeout: 10 seconds
working directory: resolved selected source root
stdin: none
stdout: captured
stderr: captured
```

### 8.4 Interpretation

Version text is selected from:

1. the first non-empty stdout line;
2. otherwise the first non-empty stderr line;
3. otherwise `UNKNOWN`.

The exact raw output remains preserved.

A parsed version field should be separate from the display string.

Example:

```json
{
  "raw": "GF - Grammatical Framework 3.x",
  "normalized": "3.x",
  "recognized": true
}
```

### 8.5 Probe outcomes

Possible outcomes:

```text
recognized
unknown
skipped
timed_out
launch_failed
unsupported
```

These are probe outcomes, not language validation results.

### 8.6 Strict release behavior

Release mode should fail before language validation when:

- GF cannot launch;
- the version is below the minimum supported version;
- the version is explicitly known to be incompatible;
- strict compatibility policy rejects an unknown version.

An unknown newer version may proceed with a warning outside strict release mode.

---

## 9. Version compatibility policy

GF Wordbench must maintain:

```text
minimum_supported_gf_version
tested_gf_versions
known_incompatible_gf_versions
version_specific_capabilities
```

### 9.1 Compatibility categories

```text
supported
supported-with-warning
untested
unsupported
known-incompatible
```

### 9.2 Capability checks

When a command-line option differs between versions, use:

- a version-gated request builder;
- a capability probe;
- a documented compatibility adapter.

Silent semantic fallback is prohibited.

### 9.3 Gold implications

A GF version change may alter:

- diagnostic wording;
- output ordering;
- pretty printing;
- optimization behavior;
- generated trees;
- parser ambiguity ordering.

Therefore, changing the accepted GF version range requires:

1. integration tests;
2. scenario review;
3. normalization review;
4. deliberate gold review;
5. compatibility documentation.

Gold files must not be updated merely to hide an unexplained version difference.

---

## 10. Path model

GF uses paths in several distinct roles.

### 10.1 Selected source root

The selected source root is the base for:

- `project.toml`;
- project-relative source paths;
- scenario paths;
- input paths;
- gold paths;
- configured entrypoints.

### 10.2 RGL root

The RGL root identifies the installed or checked-out Resource Grammar Library source root required by the project.

It is environment-specific.

It should not be embedded into language source or gold output.

### 10.3 GF search path

The GF search path supplies directories used during module resolution.

The canonical path is resolved from:

1. framework-required directories;
2. selected language context source directories;
3. project-declared path additions;
4. required RGL directories;
5. explicit approved overrides.

### 10.4 Run output paths

GF-generated and captured outputs belong inside the owned run directory.

Examples:

```text
run_<id>/raw/compile/
run_<id>/raw/scenarios/
run_<id>/artifacts/gfo/
run_<id>/artifacts/out/
run_<id>/artifacts/pgf/
```

### 10.5 Path invariants

- ordering is deterministic;
- duplicate directories are removed without changing first-use precedence;
- required paths must exist before execution;
- equivalent compiler and scenario operations use equivalent search-path semantics;
- project-relative configuration uses `/`;
- native process arguments use host-compatible paths;
- paths containing spaces remain single arguments;
- no shell quoting is relied upon when `shell=False`;
- source paths must remain inside the selected language context unless explicitly approved;
- output paths must remain inside owned output roots.

---

## 11. GF path construction

### 11.1 Structured representation

Internally, GF path components should remain an ordered list:

```python
[
    project_source_root,
    project_additional_path,
    rgl_abstract,
    rgl_common,
    rgl_prelude,
]
```

The exact required RGL directories depend on the project and supported GF/RGL layout.

### 11.2 Rendering

The path builder renders the ordered components into the form accepted by the selected GF version.

The renderer must not be duplicated between:

- module compilation;
- PGF build;
- scenario execution;
- introspection.

### 11.3 Explicit override

An explicit GF path override may be supported for diagnosis.

When used:

- it must be recorded;
- strict mode should verify required project directories remain accessible;
- the report must identify that automatic construction was bypassed.

### 11.4 Failure behavior

Path resolution fails before GF execution when:

- a required directory does not exist;
- a path escapes a required security boundary;
- the active source directory is missing;
- the path cannot be rendered for the host platform;
- required RGL directories cannot be located.

---

## 12. Process invocation model

### 12.1 No implicit shell

Normal GF execution should use:

```python
subprocess.run(
    [executable, *arguments],
    shell=False,
)
```

Equivalent APIs are permitted.

GF Wordbench must not construct one shell command string from project data.

### 12.2 Structured request

Each request should contain:

```text
operation_id
operation_kind
executable
arguments
working_directory
environment_overrides
stdin_encoding
stdin_content_reference
timeout_sec
expected_artifacts
```

### 12.3 Structured result

Each result should contain:

```text
operation_id
started_at
finished_at
duration_ms
execution_state
exit_code
timed_out
cancelled
launch_error
stdout_path
stderr_path
artifact_paths
```

### 12.4 Working directory

Every invocation must define its working directory explicitly.

It must not depend on:

- the terminal launch directory;
- an IDE;
- the GUI process directory;
- a Windows shortcut;
- a batch launcher location.

### 12.5 Environment

GF Wordbench should pass a minimal inherited environment plus documented overrides.

Relevant values may include:

- locale;
- encoding;
- GF library path, when required;
- temporary directory;
- platform process settings.

Complete environment dumps must not be written to reports.

Secrets must not be persisted.

---

## 13. Evidence capture

### 13.1 Evidence-before-interpretation

GF Wordbench writes stdout and stderr before:

- parsing diagnostics;
- normalizing scenario output;
- comparing gold;
- generating human reports.

A parser failure must not destroy the underlying evidence.

### 13.2 Separate streams

Stdout and stderr remain separate raw artifacts.

Success must not be inferred from stdout alone.

Diagnostics may appear on either stream depending on GF version and platform.

### 13.3 Required process metadata

Preserve:

- structured command;
- rendered command for display;
- working directory;
- relevant environment overrides;
- start time;
- end time;
- duration;
- exit code;
- timeout state;
- cancellation state;
- launch error;
- stdout path;
- stderr path;
- produced artifact list.

### 13.4 Immutability

Raw evidence becomes immutable after capture.

Normalization and diagnostic summaries must be written as derived artifacts.

### 13.5 Truncation

Raw files should normally remain complete.

When an external size policy requires truncation:

- truncation must be explicit;
- original byte count must be recorded;
- truncation direction must be recorded;
- diagnostic excerpts must not be presented as complete raw output.

---

## 14. Exit-code policy

An exit code is evidence, not the complete validation decision.

### 14.1 Zero exit code

A zero exit code does not override:

- missing required scenario markers;
- absent required artifacts;
- recognized fatal diagnostics;
- incomplete script execution;
- failed gold comparison;
- invalid normalized output.

### 14.2 Non-zero exit code

A non-zero exit normally indicates operation failure.

GF Wordbench must still preserve and interpret both output streams.

### 14.3 Validation status

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

### 14.4 Execution state

Canonical execution states:

```text
completed
timed_out
cancelled
launch_failed
```

`cancelled` is an execution state, not a validation status.

### 14.5 Status mapping

Recommended mapping:

| Execution condition | Validation status |
|---|---|
| completed and criteria pass | `OK` |
| completed and criteria fail | `FAIL` |
| timed out | `ERROR` or operation-specific failure policy |
| launch failed | `ERROR` |
| cancelled by user | `SKIPPED` or `ERROR` according to run policy, with `execution_state=cancelled` |
| intentionally not requested | `SKIPPED` |

Release mode must not treat cancellation or skipped required work as success.

---

## 15. Timeout and cancellation

### 15.1 Finite timeouts

Every GF process must have a finite timeout.

Timeouts should be configurable by operation class:

```text
version_probe
module_compile
pgf_build
scenario
generation
introspection
```

### 15.2 Recommended relative sizing

The project may configure exact values, but generally:

```text
version probe < module compile < scenario < PGF build
```

Generation and exhaustive-tree scenarios require explicit bounds in addition to process timeouts.

### 15.3 Timeout handling

On timeout:

1. mark `timed_out=true`;
2. attempt graceful termination where meaningful;
3. terminate the owned process tree according to platform policy;
4. finish stream capture;
5. preserve partial output;
6. record termination behavior;
7. return a structured result.

A timeout must not be reported as a GF syntax error.

### 15.4 User cancellation

Cancellation must:

- be distinguishable from timeout;
- preserve available evidence;
- stop scheduling dependent operations;
- leave completed artifacts intact;
- never produce a successful release result.

---

## 16. Encoding policy

### 16.1 Canonical encoding

GF Wordbench uses UTF-8 for:

- `.gf`;
- `.gfs`;
- `.gold`;
- stdin;
- captured stdout/stderr text;
- normalized output;
- reports.

### 16.2 Newlines

Canonical persisted text uses LF.

Readers accept CRLF and normalize it before comparison.

### 16.3 Decode errors

Decode errors must use a documented strategy.

Bytes must not be silently discarded.

A recommended strategy is:

1. decode as UTF-8 strictly;
2. on failure, preserve raw bytes;
3. decode a diagnostic view with replacement characters;
4. record the decode error;
5. block exact gold comparison unless policy explicitly permits it.

### 16.4 Linguistic fidelity

Normalization must not erase meaningful:

- Unicode distinctions;
- diacritics;
- punctuation;
- token boundaries;
- case;
- non-breaking or binding semantics used by the grammar.

---

## 17. Source module compilation

### 17.1 Purpose

Module compilation validates a selected `.gf` source target and captures GF diagnostics.

### 17.2 Canonical conceptual request

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

The exact supported long- or short-option spelling is selected by the version adapter.

### 17.3 Silent and diagnostic behavior

`-s` is appropriate for routine validation because it suppresses non-error messages.

Diagnostic mode may omit silent behavior when verbose compiler output is required.

The resolved command must always be recorded.

### 17.4 Inputs

- one selected `.gf` source file;
- resolved GF executable;
- selected source root;
- resolved GF search path;
- RGL configuration;
- run-owned artifact directories;
- compile timeout;
- optional CPU statistics setting.

### 17.5 Outputs

Raw evidence:

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
```

Possible GF artifact:

```text
artifacts/gfo/**/*.gfo
```

### 17.6 Success criteria

Compilation succeeds only when all applicable criteria pass:

- process launched;
- no timeout;
- no cancellation;
- successful exit code;
- no recognized fatal diagnostic;
- required `.gfo` artifact checks pass when configured.

### 17.7 Compiler responsibilities

The compiler stage must:

- build or receive a structured request;
- create required output directories;
- invoke the generic process layer;
- preserve raw output;
- return a structured compile summary;
- identify tool-level error kind;
- reference generated artifacts.

### 17.8 Compiler non-responsibilities

The compiler must not:

- modify source files;
- classify dependency cascades;
- decide release readiness;
- generate user-facing reports;
- update gold files;
- infer project entrypoints;
- rerun itself from a report writer.

### 17.9 Compilation and PGF separation

GF Wordbench keeps these operations distinct:

```text
module compilation
```

and:

```text
PGF release construction
```

A compatibility adapter may translate an inherited combined command into the two canonical operations, but it must delegate to the same request builders, process boundary, evidence model, and artifact contracts. It must not define a second normative execution path.

---

## 18. PGF release build

### 18.1 Purpose

The PGF stage produces the portable runtime grammar required for release.

### 18.2 Canonical conceptual request

```text
<gf> -make -optimize-pgf <path-options> <entrypoint-1> [<entrypoint-N>...]
```

Optimization may be disabled only by an explicit diagnostic or compatibility policy.

### 18.3 Inputs

- one or more project-declared top-level concrete entrypoints;
- compatible abstract syntax family;
- deterministic entrypoint ordering;
- resolved GF search path;
- dedicated build timeout;
- declared output expectations.

### 18.4 Output

Expected artifact:

```text
artifacts/pgf/<grammar-name>.pgf
```

The filename must be declared or deterministically derived.

### 18.5 Success criteria

The PGF build succeeds only when:

- process launched;
- no timeout;
- no cancellation;
- successful exit code;
- no recognized fatal diagnostic;
- expected `.pgf` exists;
- the file is non-empty;
- the artifact is registered in `manifest.json`.

### 18.6 Release invariants

- individual `.gfo` success is not sufficient for release;
- PGF build is a distinct stage;
- the GF version and exact command are recorded;
- previous release artifacts are not silently overwritten;
- PGF output is generated or copied into an owned run location;
- required entrypoints cannot be inferred differently by CLI and GUI.

### 18.7 Optional export formats

GF can produce additional output formats through supported printer or batch options.

Additional exports must be:

- project-declared;
- version-gated;
- placed in owned artifact directories;
- separately registered in the manifest;
- non-blocking unless declared required.

They must not replace the canonical PGF release artifact without an architectural decision.

---

## 19. Native `.gfs` scenario execution

### 19.1 Purpose

Scenarios validate runtime grammar behavior using native GF shell commands.

### 19.2 Canonical execution model

GF accepts shell commands through standard input.

GF Wordbench sends scenario content to the GF process rather than reimplementing shell semantics.

Conceptually:

```text
<gf> < scenario.gfs
```

The process API should pass the script through stdin directly without requiring an operating-system shell redirection command.

### 19.3 Scenario location

```text
<validation-profile-root>/validation/scenarios/<scenario-id>.gfs
```

### 19.4 Input location

```text
<validation-profile-root>/validation/inputs/
```

### 19.5 Gold location

```text
<validation-profile-root>/validation/gold/<scenario-id>.gold
```

### 19.6 Runtime output

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
raw/scenarios/<scenario-id>.out
```

The `.out` file is normalized derived output.

### 19.7 Scenario request

A scenario request includes:

```text
scenario_id
script_path
required
working_directory
GF path
timeout
normalization_version
gold_path
required_markers
forbidden_markers
expected_artifacts
```

### 19.8 Script invariants

A project scenario must:

- use UTF-8;
- have one stable scenario identifier;
- load the intended grammar;
- use bounded commands;
- emit required start/end markers;
- terminate with `q` where appropriate;
- avoid local absolute paths;
- avoid operating-system shell escapes;
- avoid rewriting source, inputs, or gold;
- remain deterministic when used for exact gold comparison.

### 19.9 Unrecognized commands

GF may skip unrecognized script lines without terminating.

Therefore, GF Wordbench must not treat process completion or zero exit alone as proof that every intended command executed.

Required markers are mandatory for important scenario sections.

---

## 20. Scenario markers

### 20.1 Purpose

Markers prove that required script sections were reached.

Example:

```text
ps "GF_WORDBENCH_BEGIN parse-basic"
...
ps "GF_WORDBENCH_END parse-basic"
```

The exact marker syntax is defined in:

```text
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
```

### 20.2 Required behavior

The runner must verify:

- each required begin marker exists;
- each required end marker exists;
- end follows begin;
- section identifiers are unique;
- forbidden failure markers do not appear;
- the scenario completion marker is reached.

### 20.3 Missing marker

A missing required marker produces:

```text
validation_status = FAIL or ERROR
diagnostic_kind = contract_failure
```

The choice between `FAIL` and `ERROR` depends on whether the grammar failed a valid assertion or the framework could not interpret execution.

### 20.4 Marker safety

Marker text must be unlikely to occur in normal linguistic output.

Markers must remain stable across GF versions and language projects.

---

## 21. Grammar loading

### 21.1 GF command

Native shell command:

```text
import
```

Short form:

```text
i
```

### 21.2 Supported inputs

GF can load source, object, or PGF forms according to supported GF behavior.

GF Wordbench scenarios should normally load the form appropriate to the validation goal:

| Goal | Preferred input |
|---|---|
| source development diagnosis | `.gf` |
| compiled module behavior | `.gfo` |
| release runtime validation | `.pgf` |
| retained resource operations | source import with retain option |

### 21.3 Retained operations

Introspection commands such as operation or source inspection may require import with retained source operations.

Such scenarios must declare this requirement.

### 21.4 Load validation

A load scenario should verify:

- intended grammar is in scope;
- expected language modules are present;
- required marker after import is reached;
- fatal diagnostics are absent;
- expected artifact or grammar information is available.

---

## 22. Parsing validation

### 22.1 GF command

```text
parse
```

Short form:

```text
p
```

### 22.2 Purpose

Parsing validation checks that selected input strings map to expected abstract trees or expected parse properties.

### 22.3 Scenario dimensions

A parse assertion may validate:

- at least one parse;
- exactly one parse;
- expected abstract tree;
- expected category;
- expected ambiguity count;
- expected rejection;
- bounded robust parsing behavior.

### 22.4 Required explicitness

Scenarios should specify:

- input language;
- target category when not the grammar default;
- exact input string or input-file source;
- expected assertion type.

### 22.5 Ambiguity

Parse ordering may change across versions.

When all valid parses matter, normalize and compare a deterministic set.

When only acceptance matters, do not create a brittle exact-tree gold unnecessarily.

### 22.6 Negative tests

An expected rejection must be represented explicitly.

The absence of output alone is not sufficient unless the scenario protocol defines it.

---

## 23. Linearization validation

### 23.1 GF command

```text
linearize
```

Short form:

```text
l
```

### 23.2 Purpose

Linearization validates that an abstract tree produces expected language output.

### 23.3 Assertion types

A scenario may validate:

- exact string;
- one of several accepted variants;
- all variants;
- absence of an invalid form;
- round-trip behavior;
- stable tokenization;
- language-specific orthography.

### 23.4 Language selection

Scenarios should specify the language when multiple concrete syntaxes are loaded.

### 23.5 Variants

When GF produces legitimate variants:

- preserve all variants;
- normalize deterministic ordering only when semantics are order-independent;
- represent accepted sets explicitly;
- avoid selecting only the first variant without a documented reason.

### 23.6 Unicode

Linearization gold must preserve linguistically meaningful Unicode exactly.

---

## 24. Generation validation

### 24.1 Random generation

GF command:

```text
generate_random
```

Short form:

```text
gr
```

Use for:

- exploratory coverage;
- bounded smoke tests;
- detecting crashes;
- checking that generated trees linearize.

Random generation should not normally use exact gold output.

### 24.2 Exhaustive generation

GF command:

```text
generate_trees
```

Short form:

```text
gt
```

Use for:

- bounded deterministic category coverage;
- small depth-limited test spaces;
- systematic linearization checks.

### 24.3 Mandatory bounds

Every generation scenario must specify at least one effective bound:

```text
category
depth
number
timeout
```

A release scenario must not request unbounded generation.

### 24.4 Reproducibility

Exact gold comparison is appropriate only when output is deterministic under the supported GF version and configuration.

Random outputs should instead validate properties such as:

- command completed;
- requested number of trees did not exceed a limit;
- every tree linearized;
- no fatal diagnostic occurred;
- required markers completed.

---

## 25. Morphology validation

### 25.1 GF command

```text
morpho_analyse
```

Short form:

```text
ma
```

### 25.2 Purpose

Morphology scenarios may validate:

- known word analyses;
- expected lemma/category information;
- unknown-word behavior;
- missing-word lists;
- ambiguity;
- orthographic variants.

### 25.3 Input policy

Morphology inputs should be stored in reviewed project input files when the set is substantial.

### 25.4 Gold policy

Exact morphology gold is appropriate when:

- output format is stable for supported GF versions;
- ordering is deterministic or normalized safely;
- all linguistically meaningful distinctions are preserved.

---

## 26. Grammar introspection

GF Wordbench may use native shell introspection for diagnosis and release checks.

### 26.1 Abstract information

```text
abstract_info
ai
```

Use to inspect:

- categories;
- function types;
- expressions.

### 26.2 Operations

```text
show_operations
so
```

Use to inspect retained operations and signatures.

Requires an appropriate retained source import.

### 26.3 Source surface

```text
show_source
ss
```

Use to inspect compiled source information, signatures, or sizes.

### 26.4 Dependencies

```text
show_dependencies
sd
```

Use to inspect module dependencies available in the current environment.

### 26.5 Missing linearizations

```text
print_grammar -missing
pg -missing
```

Use to detect functions without linearization in the loaded grammar.

### 26.6 Grammar inventories

`print_grammar` may also expose:

- categories;
- functions;
- language modules;
- words;
- selected printer output.

### 26.7 Introspection rules

Introspection:

- is performed by GF;
- remains distinct from static source scanning;
- is captured as raw evidence;
- may be normalized only through versioned rules;
- must not be silently treated as compilation;
- must have bounded output or report truncation.

---

## 27. Dependency diagnostics

GF compilation failures often cascade.

GF Wordbench uses GF diagnostics and project dependency information to distinguish:

```text
direct
downstream
ambiguous
```

### 27.1 Compiler boundary

The compiler stage reports local process and diagnostic evidence.

It must not decide dependency causality.

### 27.2 Classifier boundary

The classifier may use:

- imported module names;
- dependency map;
- first error location;
- failed-provider set;
- source fingerprint;
- compile ordering;
- GF dependency introspection.

### 27.3 Language dependency map

The selected language context maintains:

```text
<validation-profile-root>/docs/MODULE_DEPENDENCY_MAP.md
```

When the dependency map and actual GF behavior differ, the map must be reviewed.

---

## 28. Output normalization

### 28.1 Purpose

Normalization removes unstable environment noise while preserving semantic evidence.

### 28.2 Allowed normalization

Versioned rules may normalize:

- CRLF to LF;
- ANSI control sequences;
- run-specific absolute paths to stable tokens;
- selected source root to `<PROJECT_ROOT>`;
- RGL root to `<RGL_ROOT>`;
- run directory to `<RUN_DIR>`;
- executable path to `<GF_EXECUTABLE>`;
- explicitly unstable timing lines;
- trailing spaces;
- approved non-semantic ordering.

### 28.3 Forbidden normalization

Normalization must not remove:

- GF error messages;
- relevant source filenames;
- relevant line or column locations;
- abstract trees;
- linearized strings;
- ambiguity information;
- missing-function lists;
- morphology results;
- meaningful punctuation;
- language-relevant Unicode;
- evidence that a required section did not run.

### 28.4 Versioning

Normalization rules have an explicit version.

A normalization change that alters existing comparisons requires:

1. normalization-rule update;
2. tests;
3. deliberate gold review;
4. compatibility note;
5. schema review when persisted output changes.

### 28.5 Raw-versus-normalized rule

Raw output is never overwritten by normalized output.

Derived output references the raw source artifacts.

---

## 29. Gold comparison

### 29.1 Comparison inputs

Gold comparison uses:

```text
normalized scenario output
reviewed gold file
normalization version
scenario identifier
```

### 29.2 Standard run behavior

A standard run:

- reads gold;
- never rewrites gold;
- writes a diff artifact on mismatch;
- preserves actual normalized output;
- records match status.

### 29.3 Explicit update behavior

Gold update requires a dedicated operation.

It must:

1. run the scenario;
2. normalize output;
3. show or save the diff;
4. require explicit approval or controlled CI policy;
5. write atomically;
6. preserve version-control reviewability.

### 29.4 Missing gold

For a required exact-comparison scenario, missing gold is a failure.

It is not automatically created.

---

## 30. Artifact model

### 30.1 Raw artifacts

Examples:

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
raw/compile/<key>.out.txt
raw/compile/<key>.err.txt
raw/scenarios/<id>.out.txt
raw/scenarios/<id>.err.txt
```

### 30.2 GF-generated artifacts

Examples:

```text
artifacts/gfo/**/*.gfo
artifacts/pgf/*.pgf
artifacts/out/*
```

### 30.3 Derived artifacts

Examples:

```text
raw/scenarios/<id>.out
details/<result>.md
gold diff
diagnostic summary
```

### 30.4 Manifest requirements

Every required generated artifact must be registered with:

```text
path
role
media type
required flag
size
hash
producer
```

### 30.5 Missing artifact

A required artifact missing after apparent process success produces an artifact failure.

It must not be silently accepted.

---

## 31. Validation modes and toolchain behavior

### 31.1 Quick mode

Typical GF work:

- optional version probe;
- compile selected file;
- optional short smoke scenario;
- no mandatory PGF build.

### 31.2 Checkpoint mode

Typical GF work:

- compile declared checkpoint modules;
- compile or load related entrypoints;
- run required subsystem scenarios;
- perform relevant introspection;
- compare gold.

### 31.3 Release mode

Required GF work:

- version compatibility check;
- compile all required entrypoints;
- run every required scenario;
- build required PGF;
- verify missing-linearization policy;
- execute bounded runtime validation;
- verify required artifacts.

A required GF stage cannot be silently skipped.

### 31.4 Diagnostic mode

Typical GF work:

- verbose compilation;
- broad module coverage;
- retained source import;
- dependency and operation introspection;
- full raw evidence;
- extended timeout where configured.

---

## 32. Security and trust boundaries

### 32.1 Scenario trust

A `.gfs` file is executable tool input.

Untrusted project scenarios must be treated as untrusted code.

### 32.2 Shell escapes

GF shell commands capable of invoking operating-system commands or pipes are prohibited in normal scenarios unless an explicit security policy enables them.

Examples include system-shell escape and system-pipe features.

### 32.3 Path containment

Before execution, validate:

- scenario path;
- input paths;
- source paths;
- output paths;
- gold paths;
- executable path.

Project-controlled paths must not escape their approved roots.

### 32.4 Command injection

Project strings must never be concatenated into an operating-system shell command.

Structured argument lists and direct stdin are required.

### 32.5 Environment leakage

Reports and manifests must not expose:

- tokens;
- credentials;
- private keys;
- complete environment dumps;
- secret command-line values.

### 32.6 Source mutation

Normal GF validation must not mutate:

- `.gf` source;
- `.gfs` scenarios;
- inputs;
- gold files;
- project documentation.

Tool-generated build files belong only in approved output locations.

---

## 33. Windows integration

Windows is a first-class supported environment.

### 33.1 Executable path

Support:

```text
C:\Program Files\GF\bin\gf.exe
```

A path containing spaces remains one executable value.

### 33.2 Argument handling

Use structured argument lists.

Do not add manual shell quotes to argument values passed through `shell=False`.

### 33.3 Newlines

Raw Windows output may use CRLF.

Persisted normalized text uses LF.

### 33.4 Process trees

Timeout and cancellation must terminate owned child processes according to Windows process policy.

### 33.5 Launchers

Batch files may provide convenience startup.

They must not:

- contain hidden GF semantics;
- construct a different GF path;
- bypass configuration validation;
- be the only supported execution route.

CLI, GUI, tests, and launchers must converge on the same configuration and orchestration APIs.

### 33.6 Long paths

GF Wordbench should:

- normalize paths;
- avoid unnecessary path depth;
- provide clear failure evidence for unsupported long paths;
- not silently shorten semantic filenames.

---

## 34. POSIX integration

On POSIX systems:

- executable permission failures are launch errors;
- process-tree termination should use process groups where appropriate;
- LF remains canonical;
- shell execution is still avoided;
- environment-specific library paths must be documented and recorded as relevant overrides;
- symlink resolution must respect containment policy.

Cross-platform behavior should produce equivalent structured results even when raw diagnostics differ.

---

## 35. Optional external tools

A new external tool is added only when GF, the Python standard library, and
existing GF Wordbench components cannot sufficiently provide the capability.

Every executable optional tool must have a static allowlist entry governed by
`ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md`.

Each entry defines:

```text
tool_id
purpose
executable resolution policy
version and license policy
platform support
allowed argument templates
working-directory policy
input policy
output and artifact contracts
timeout and output-size limits
mutability
network policy
evidence role
normalization and parser
failure semantics
fallback
tests
```

Registry rules:

- arbitrary user-supplied commands are prohibited;
- dynamically loaded executable plugins are prohibited;
- optional tools use the same controlled process boundary as GF;
- mutating tools require explicit user intent and cannot run during ordinary read-only validation;
- AI-assisted tools are optional, visible, bounded, and non-normative;
- AI output may annotate preserved evidence but cannot replace GF evidence or release criteria;
- tool absence cannot invalidate core GF evidence unless the selected language context explicitly declares the tool as a required release dependency;
- optional tools operate only for the active Wordbench project and are not Portfolio orchestration mechanisms.

Examples include:

- Graphviz for dependency visualization;
- archive utilities;
- independent schema validators;
- coverage tooling.

Optional tools must not become hidden release dependencies.

---

## 36. Prohibited integration behavior

The following are prohibited:

- reports launching GF;
- GUI widgets launching GF directly;
- CLI code constructing compiler commands independently;
- compilation and scenarios using different GF path builders;
- relying only on stdout;
- relying only on exit code;
- running without a timeout;
- hiding timeout as a compile failure;
- hiding launch failure as GF syntax failure;
- silently ignoring a missing PGF;
- normal runs modifying gold;
- normalized output replacing raw output;
- project scenarios using unapproved system shell escapes;
- tests relying on a developer’s undeclared global GF environment;
- random generation used as brittle exact gold;
- language-specific path rules embedded in the generic process layer;
- implementing GF parsing or typing inside GF Wordbench;
- inferring successful scenario completion without required markers;
- overwriting previous release artifacts without policy;
- changing command options without compatibility review;
- executing an optional command that is absent from the static registry;
- allowing project text to select an executable or interpreter;
- using the Wordbench process boundary to orchestrate `gf-portfolio` workspaces.

---

## 37. Testing strategy

The toolchain integration requires both isolated and real-GF tests.

### 37.1 Unit tests without GF

Use fake executables or mocked process results to validate:

- executable resolution;
- argument ordering;
- path rendering;
- paths containing spaces;
- working directory;
- environment overrides;
- timeout mapping;
- cancellation mapping;
- stream capture;
- decode errors;
- artifact checks;
- marker checks;
- normalization;
- gold comparison;
- manifest registration;
- version parsing;
- unsupported-version policy.

### 37.2 Fake executable behaviors

Test helpers should simulate:

```text
successful stdout
successful stderr
non-zero exit
timeout
large output
invalid UTF-8
partial output
missing artifact
artifact generated
ignored script command
missing completion marker
child process
```

### 37.3 Integration tests with real GF

A small fixture grammar should validate:

- executable version probe;
- successful module compilation;
- failed module compilation;
- source path with spaces;
- explicit GF path;
- automatic GF path;
- successful PGF build;
- `.gfs` execution;
- grammar import;
- parse;
- linearize;
- bounded generation;
- morphology;
- missing-function introspection;
- raw output preservation.

Real-GF tests should be separately marked so local development can distinguish missing infrastructure from code failures.

### 37.4 Contract tests

Recommended paths:

```text
tests/contracts/test_gf_executable_contract.py
tests/contracts/test_gf_version_contract.py
tests/contracts/test_gf_compile_contract.py
tests/contracts/test_gf_pgf_build_contract.py
tests/contracts/test_gf_scenario_contract.py
tests/contracts/test_process_contract.py
tests/contracts/test_timeout_contract.py
tests/contracts/test_normalization_contract.py
tests/contracts/test_windows_contract.py
```

### 37.5 Golden integration fixtures

Framework test gold files must use a tiny synthetic grammar.

They must not depend on the active language project.

---

## 38. Observability

Every GF operation must be traceable from the run summary to raw evidence.

Trace chain:

```text
summary result
→ operation ID
→ command request
→ process result
→ raw stdout/stderr
→ normalized evidence
→ artifact entries
→ validation decision
```

### 38.1 Human report

A human report may render:

- operation;
- GF version;
- source or scenario;
- status;
- duration;
- first error;
- evidence links.

### 38.2 Machine report

`summary.json` stores the structured fields defined by the persisted schema lock.

### 38.3 AI-ready report

`AI_READY.md` may include bounded evidence excerpts.

It must reference raw artifacts and must not rerun GF.

---

## 39. Diagnostics and classification

### 39.1 Error kind

The GF interpretation layer may emit:

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

### 39.2 Diagnostic class

The higher-level classifier may emit:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### 39.3 Separation rule

```text
error_kind
```

describes the nature of a problem.

```text
diagnostic_class
```

describes causal position in the project.

```text
execution_state
```

describes what happened to the process.

```text
validation_status
```

describes whether the validation criterion passed.

These fields must not be collapsed into one enum.

---

## 40. Determinism

Given the same:

- source files;
- GF version;
- RGL revision;
- project configuration;
- scenario inputs;
- normalization version;
- operating policy;

GF Wordbench should produce equivalent structured results.

Potentially unstable values include:

- durations;
- absolute paths;
- random generation;
- diagnostic ordering;
- filesystem ordering;
- platform newline style.

Only explicitly approved instability may be normalized.

Command ordering, file selection, entrypoint ordering, artifact inventories, and normalized deterministic scenarios must remain stable.

---

## 41. Release integration gate

The GF toolchain integration is release-ready only when:

```text
[ ] GF executable is resolved and recorded
[ ] GF version policy passes
[ ] Required source entrypoints compile
[ ] Required checkpoints compile
[ ] Required scenarios complete all markers
[ ] Required gold comparisons pass
[ ] Required introspection checks pass
[ ] Required PGF is built
[ ] PGF exists and is non-empty
[ ] Required artifacts are in the manifest
[ ] Raw stdout and stderr exist for required operations
[ ] No required operation timed out
[ ] No required operation was cancelled or skipped
[ ] No unsupported shell escape was used
[ ] Normalization version is recorded
[ ] Reports were generated without rerunning GF
```

---

## 42. Integration change workflow

A toolchain change is complete only when all applicable items are updated:

```text
[ ] External-tool contract reviewed
[ ] Request builder updated
[ ] Process layer reviewed
[ ] Path resolver reviewed
[ ] Result models updated
[ ] Persisted schema reviewed
[ ] Diagnostic parser updated
[ ] Normalization reviewed
[ ] Gold impact reviewed
[ ] Artifact expectations updated
[ ] Unit tests updated
[ ] Real-GF tests updated
[ ] Compatibility policy updated
[ ] Documentation updated
[ ] Compatibility and deprecation effects documented
```

Examples of contract-changing edits:

- adding a GF option;
- changing path order;
- changing working directory;
- changing script input method;
- changing timeout semantics;
- changing version parsing;
- changing required markers;
- changing expected PGF name;
- changing normalized output;
- changing artifact paths.

No such edit may be made in only one caller.

---

## 43. Integration matrix

| Operation | Input | Raw evidence | Required success evidence | Owner |
|---|---|---|---|---|
| version probe | executable | version stdout/stderr | recognized or accepted version | GF adapter |
| module compile | `.gf` | compile stdout/stderr | exit, diagnostics, optional `.gfo` | compiler |
| PGF build | entrypoints | build stdout/stderr | non-empty `.pgf` and manifest entry | PGF builder |
| scenario | `.gfs` | scenario stdout/stderr | required markers and assertions | scenario runner |
| parse | string | scenario evidence | declared parse assertion | scenario |
| linearize | tree | scenario evidence | declared linearization assertion | scenario |
| generation | category/tree | scenario evidence | bounded completion/property | scenario |
| morphology | input words | scenario evidence | declared analysis assertion | scenario |
| introspection | loaded grammar | scenario evidence | declared inventory assertion | diagnostics/scenario |
| gold compare | normalized output | diff | exact or policy-defined match | gold comparator |

---

## 44. Related documentation

Read with:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/gf/GF_OUTPUT_NORMALIZATION.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/RELEASE_GATES.md
<validation-profile-root>/project.toml
<validation-profile-root>/docs/INTERFILE_CONTRACT_LOCK.md
<validation-profile-root>/docs/VALIDATION_SPEC__PROJECT_DOCS.md
```

---

## 45. Official GF basis

This design relies on the documented GF model in which:

- the GF compiler translates `.gf` source to `.gfo` and `.pgf`;
- batch mode compiles source modules;
- make mode builds PGF grammars;
- optimized PGF is recommended for shipped grammars;
- GF shell commands provide import, parse, linearize, generation, morphology, and introspection;
- command scripts can be supplied through standard input;
- shell scripts may skip unrecognized command lines without necessarily terminating.

GF Wordbench adds orchestration and evidence requirements around those native capabilities.

---

## 46. Core rule

The GF toolchain boundary must remain explicit and reproducible.

> Every GF operation must be represented by a structured request, executed through one controlled process layer, preserved as raw evidence, interpreted without hiding GF output, and converted into a validation result only through documented criteria.

GF remains authoritative for grammar semantics.

GF Wordbench remains authoritative for proving what was requested, what executed, what evidence was produced, and why the resulting validation status was assigned.
