# GF Wordbench — Glossary

**Document ID:** `GF-WB-GLOSSARY`  
**Status:** Normative terminology reference  
**Target path:** `docs/GLOSSARY.md`  
**Applies to:** GF Wordbench framework, active language project, validation assets, reports, schemas, and contract locks  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Terminology version:** `1.1.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This glossary defines the canonical vocabulary used by GF Wordbench.

Its goals are to:

- assign one stable meaning to each important term;
- prevent the same concept from receiving multiple names;
- separate GF concepts from GF Wordbench concepts;
- distinguish execution state, validation result, diagnostic cause, and error kind;
- identify legacy terms that remain readable but are no longer canonical;
- provide a shared language for code, tests, configuration, reports, documentation, and contract locks.

When another document gives a more detailed procedure, this glossary remains authoritative for the meaning of the term itself.

---

## 2. Terminology rules

### 2.1 Canonical terms

A **canonical term** is the preferred term for code, schemas, configuration, documentation, reports, and user interfaces.

New code and documentation MUST use canonical terms.

### 2.2 Legacy terms

A **legacy term** is accepted only for compatibility with earlier GF Audit files, states, modes, or reports.

Legacy terms MUST NOT be emitted by new canonical writers unless a migration or compatibility output explicitly requires them.

### 2.3 Ambiguous terms

An ambiguous term SHOULD be qualified.

Examples:

- use **validation status**, not only *status*;
- use **execution state**, not only *state*;
- use **project root**, **source root**, **run root**, or **output root**, not only *root*;
- use **GF module**, **Python module**, or **project document**, not only *module* or *file*;
- use **raw evidence** or **normalized evidence**, not only *output*.

### 2.4 Normative capitalization

The following values are serialized exactly as shown:

```text
OK
FAIL
ERROR
SKIPPED
```

The following values are serialized in lowercase:

```text
ok
direct
downstream
ambiguous
noise
skipped
completed
timed_out
cancelled
launch_failed
quick
checkpoint
release
diagnostic
```

### 2.5 Singular and plural

Schema field names use the form defined by the schema, even when ordinary prose would use another form.

Examples:

```text
file_results
scenario_results
diff_entries
top_errors
```

---

# 3. Normative language

## MAY

Permitted but not required.

## MUST

Mandatory. A violation is a contract or specification failure.

## MUST NOT

Prohibited. A violation is a contract or specification failure.

## SHOULD

Expected unless a documented and reviewable reason justifies an exception.

## SHOULD NOT

Normally prohibited unless a documented and reviewable exception exists.

---

# 4. GF Wordbench core concepts

## Active language project

The single GF language project currently configured and validated by one GF Wordbench copy.

An active language project includes:

- `project/project.toml`;
- GF source modules;
- project documentation;
- validation scenarios;
- validation inputs;
- gold files;
- release entrypoints and expected artifacts.

GF Wordbench does not manage several active language projects in parallel within the same project directory.

## Audit

A structured execution that gathers evidence about the current language project.

An audit may include:

- file selection;
- static scanning;
- GF version probing;
- compilation;
- PGF construction;
- scenario execution;
- gold comparison;
- diagnostic classification;
- regression comparison;
- report generation.

An audit does not automatically imply release readiness.

## Audit core

The orchestration component that coordinates validation stages and builds the final run result.

The audit core does not own GF semantics. It owns execution order, stage coordination, evidence aggregation, and report initiation.

## Canonical writer

The current component authorized to emit the latest supported form of a persisted schema or artifact.

A canonical writer emits current names, current paths, current enums, and current schema versions.

## Check

A general validation operation that produces a structured result.

A check may be file-based, scenario-based, process-based, schema-based, or release-based.

## Clone

A copy of GF Wordbench prepared to host a new active language project.

Cloning preserves the framework and templates but replaces or resets active-project content and run history.

## Contract

An externally observable promise between a provider and one or more consumers.

A contract may define:

- accepted inputs;
- guaranteed outputs;
- public symbols;
- schemas;
- side effects;
- artifact ownership;
- error behavior;
- path semantics;
- compatibility expectations.

## Contract lock

A normative document that records contracts that must not drift silently.

GF Wordbench uses these lock categories:

- framework interfile contracts;
- external-tool contracts;
- persisted-schema contracts;
- active-project interfile contracts.

## Consumer

A file, component, process, scenario, or tool that imports, calls, reads, loads, interprets, compares, or otherwise depends on a provider.

## Drift

An unintended disagreement between two or more parts of the system.

Examples:

- a provider changes a field but a consumer still expects the old field;
- a scenario loads a different entrypoint from the one documented;
- a writer emits a new JSON shape without a schema version change;
- CLI and GUI build different configurations for equivalent inputs;
- a gold file no longer represents the documented behavior;
- a report reconstructs artifact paths differently from `RunPaths`.

## Evidence

Recorded information used to justify a validation result or diagnosis.

Evidence may include:

- source fingerprints;
- command lines;
- process exit codes;
- stdout;
- stderr;
- scan logs;
- generated artifacts;
- normalized scenario output;
- gold diffs;
- manifests;
- structured result fields.

## Framework

The reusable Python application, tests, documentation, templates, and runtime conventions that make up GF Wordbench.

The framework excludes the language-specific content of the active project.

## GF Wordbench

A clonable validation and development framework for one active Grammatical Framework language project.

GF Wordbench orchestrates GF tools, preserves evidence, classifies failures, compares runs, and produces reports. It does not reimplement the GF compiler, parser, type checker, runtime, or module resolver.

## Internal detail

An implementation detail that no other component consumes or assumes.

An internal detail becomes contractual when another component starts depending on it.

## Lock

A normative restriction preventing silent incompatible change.

A lock governs a boundary or persisted promise, not every line of internal implementation.

## Observer

A component permitted to read an artifact without modifying it.

## Owner

The component responsible for creating, replacing, migrating, or mutating a specific artifact or schema.

An artifact has one owner, although it may have many observers.

## Provider

A file, component, process, scenario, or artifact that supplies a symbol, structure, result, behavior, or persisted format to consumers.

## Project

See **active language project**.

## Project template

The generic, language-neutral structure copied when initializing a new active language project.

Template placeholders are valid in `templates/project/` but MUST be replaced in the active `project/` directory.

## Reset

The controlled removal of active-language data, generated run data, local state, or project-specific configuration while preserving the reusable GF Wordbench framework.

## Run

One recorded execution of GF Wordbench.

A run has:

- a unique run ID;
- a run directory;
- configuration;
- timestamps;
- file results;
- scenario results;
- artifacts;
- reports;
- optional comparison with a previous run.

## Stage

A distinct part of the validation pipeline with a clear input, output, owner, and failure behavior.

Examples:

- file selection;
- static scanning;
- compilation;
- classification;
- scenario execution;
- gold comparison;
- reporting.

## Validation

The process of determining whether a defined criterion is satisfied and preserving the evidence supporting that conclusion.

Validation is broader than compilation.

## Validation criterion

A precise condition that can pass, fail, be skipped, or encounter an execution error.

Examples:

- a GF file compiles;
- a required entrypoint loads;
- a PGF is created;
- a scenario emits all required markers;
- normalized output matches a reviewed gold file.

## Validation pipeline

The ordered set of stages executed for a selected validation mode.

## Wordbench project

A synonym for **active language project** when the context is unambiguous.

---

# 5. Roots, paths, and directories

## Artifact directory

The run-owned directory containing produced GF or validation artifacts.

Canonical examples:

```text
artifacts/gfo/
artifacts/out/
artifacts/pgf/
```

## Environment path

A path that identifies a local installation or machine-specific location.

Examples:

- GF executable;
- RGL installation;
- user-selected output root.

Environment paths may be absolute.

## GF path

The ordered search path passed to GF for resolving imported modules and compiled resources.

The order of GF path elements is semantically significant.

## Output root

The environment-level directory under which GF Wordbench creates run directories.

The output root is not the same as the project root or run root.

## Path normalization

The conversion of paths into a stable representation for comparison, persistence, or reporting.

Canonical persisted project-owned and run-owned paths use `/`.

## Project-owned path

A path to a file or directory belonging to the active project.

Canonical persisted project-owned paths are relative to the project root.

## Project root

The authoritative base directory of the active language project, as resolved from project configuration.

## RGL root

The local root of the Grammatical Framework Resource Grammar Library used by the active project.

## Run directory

The directory containing all persisted outputs for one run.

Canonical pattern:

```text
run_<run-id>/
```

## Run root

The base directory of one specific run. Paths in `manifest.json` and canonical artifact references are relative to this directory.

## Source root

The directory containing the active language GF source files.

The source root is configured by `project/project.toml`.

## Working directory

The directory in which an external process is launched.

The working directory is an explicit part of an external-tool contract.

---

# 6. GF source and module concepts

## Abstract module

A GF module defining categories and abstract functions without language-specific linearization.

Typical responsibilities:

- `cat`;
- `fun`;
- abstract grammar structure.

## Abstract syntax

The language-independent GF categories, functions, and tree structures defined by abstract modules.

## API entrypoint

A top-level GF module exposing the intended public grammar API to applications, tests, or downstream users.

An API entrypoint may differ from the main grammar entrypoint and must be validated independently when present.

## Category

A type of abstract syntax tree in GF, declared with `cat`.

Examples include sentence, noun phrase, verb phrase, and language-specific categories.

## Concrete module

A GF module implementing an abstract grammar for a specific language.

Typical responsibilities:

- `lincat`;
- `lin`;
- language-specific linearization.

## Concrete syntax

The language-specific realization of abstract syntax trees into linearization structures and strings.

## Constructor

A function or operation used to build a GF value or structure.

The term may refer to:

- an abstract `fun`;
- a concrete `lin`;
- a resource-grammar constructor;
- a project helper with constructor-like behavior.

The providing module and accepted argument structures must be explicit when the constructor crosses a file boundary.

## Dependency

A relationship in which one module, file, scenario, or artifact requires another.

A dependency may be:

- a GF import;
- an interface-instance relationship;
- a scenario-entrypoint relationship;
- a gold-scenario relationship;
- a Python import or call;
- a persisted writer-reader relationship.

## Extension module

A GF module that adds or overrides language behavior beyond the core grammar layers.

Extension behavior must respect documented inheritance and override contracts.

## Function

In abstract GF syntax, a symbol declared with `fun`.

In broader GF Wordbench documentation, *function* may also refer to a Python function. The term SHOULD be qualified when ambiguity is possible.

## GF module

A source or compiled Grammatical Framework module.

Source form:

```text
*.gf
```

Compiled form:

```text
*.gfo
```

## GF module name

The name declared by a GF module.

It must agree with configured entrypoints, scenarios, imports, and expected artifacts.

## Helper

A reusable GF operation, constructor, transformation, or support definition used by one or more consumers.

A helper becomes contractual when another module depends on its signature, representation, or behavior.

## Incomplete concrete module

A GF concrete module intentionally permitting missing linearizations.

Its incompleteness must be explicit. It must not be mistaken for a complete release concrete.

## Inheritance

The reuse of behavior through GF module composition, extension, interface implementation, or another documented module relationship.

Project documentation must distinguish inherited behavior from locally overridden behavior.

## Instance module

A GF module implementing an interface module for a specific language or resource configuration.

## Interface module

A GF module defining a reusable public resource contract to be implemented by one or more instance modules.

## `lin`

A GF concrete-syntax declaration implementing how an abstract function is linearized.

## `lincat`

A GF concrete-syntax declaration defining the linearization type of an abstract category.

A `lincat` is a cross-file contract when constructors, helpers, scenarios, or downstream modules assume its fields or structure.

## Linearization structure

The GF value associated with a category by its `lincat`.

It may contain strings, parameters, tables, records, agreement information, or other language-specific fields.

## Module suffix

The language-specific suffix used in GF module names.

Example:

```text
Sqi
```

A suffix migration is a breaking project-wide change because imports, scenarios, documentation, and artifacts may depend on it.

## `oper`

A reusable GF operation declared in a resource or concrete module.

A public `oper` is contractual when another module imports or assumes it.

## Paradigm

A reusable morphological constructor or pattern that produces inflected lexical behavior.

Paradigms usually belong to morphology or resource modules.

## `param`

A GF parameter type used to represent finite grammatical alternatives such as gender, number, case, tense, or agreement features.

## Pattern

A GF expression used to match a value in a `case`, `table`, or another pattern context.

## Record

A GF structure containing named fields.

A record layout becomes contractual when consumers access or construct its fields.

## Resource module

A GF module providing reusable language-specific operations, parameters, paradigms, tables, or helper structures.

## Structural module

A GF module providing structural words or grammar resources such as determiners, conjunctions, pronouns, prepositions, auxiliaries, or similar closed-class elements.

## Table

A GF structure mapping parameter values or patterns to results.

## Top-level grammar module

A GF module used as a primary compilation, loading, scenario, or release target.

## Type contract

A documented requirement about the category, `lincat`, field structure, argument types, or result types exchanged across a module boundary.

---

# 7. GF toolchain and runtime concepts

## GF

Grammatical Framework, including its compiler, shell, runtime, module system, and PGF tooling.

GF is authoritative for:

- GF syntax;
- GF type checking;
- module resolution;
- `.gf` to `.gfo` compilation;
- PGF construction;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF diagnostics.

## GF executable

The configured external program used to invoke GF.

Typical names:

```text
gf
gf.exe
```

## GF shell

The interactive or scripted GF command environment used for loading grammars and running commands such as parsing, linearization, generation, and introspection.

## GF version probe

A process invocation used to identify the installed GF version before validation.

## GFO

A compiled GF module artifact, conventionally stored as:

```text
*.gfo
```

A `.gfo` proves module compilation but does not by itself prove complete grammar or release readiness.

## Grammar introspection

GF commands that expose grammar structure, functions, types, dependencies, source information, morphology, or missing implementations.

## Linearization

The GF operation that transforms an abstract syntax tree into language-specific output.

## Morphological analysis

The GF operation that examines possible morphological interpretations of a word form.

## Parse

The GF operation that transforms input text into one or more abstract syntax trees.

## PGF

Portable Grammar Format, the compiled grammar artifact used by GF runtimes and applications.

A successful process exit is not sufficient proof of PGF construction; the expected current artifact must also exist.

## PGF build

The release-oriented process that constructs the configured PGF from documented entrypoints.

## RGL

Resource Grammar Library, the reusable GF grammar library on which language implementations may depend.

## Generation

The GF operation that produces abstract trees, linearizations, or test data according to grammar constraints.

## Toolchain

The external executables, paths, environment, commands, and artifact expectations required to compile and validate a GF project.

---

# 8. Validation modes

## Checkpoint mode

Canonical serialized value:

```text
checkpoint
```

A validation mode used after completing a coherent development layer or subsystem.

Typical scope:

- checkpoint modules;
- required smoke scenarios;
- selected gold comparisons;
- regression comparison.

## Diagnostic mode

Canonical serialized value:

```text
diagnostic
```

The most evidence-rich mode for investigation.

Typical scope:

- broad file audit;
- detailed logs;
- classification;
- optional introspection;
- full diagnostic reporting.

Legacy alias:

```text
all
```

## Quick mode

Canonical serialized value:

```text
quick
```

A fast development-loop mode focused on a target file or small change area.

Typical scope:

- target selection;
- static scan;
- local compilation;
- minimal smoke scenario where configured.

Legacy alias:

```text
file
```

## Release mode

Canonical serialized value:

```text
release
```

The strict final gate for an active language project.

Typical scope:

- required checkpoints;
- entrypoint validation;
- PGF construction;
- required scenarios;
- required gold comparisons;
- manifest verification;
- release criteria.

## Validation mode

A named pipeline profile controlling which stages and criteria execute.

Canonical values:

```text
quick
checkpoint
release
diagnostic
```

---

# 9. File selection and static scanning

## Excluded file

A source candidate intentionally omitted by include, exclude, glob, mode, path, or noise rules.

## File selection

The deterministic process that identifies which GF source files a run will examine.

File selection does not compile or modify source files.

## Include rule

A glob, regular expression, path rule, or configured condition that permits a file to enter the candidate set.

## Exclude rule

A glob, regular expression, path rule, or configured condition that removes a file from the candidate set.

## Noise

A result or candidate intentionally excluded from meaningful failure analysis because it is not part of the requested validation target.

## Scan finding

A heuristic observation produced by static scanning.

A scan finding is not equivalent to a GF compilation error.

## Static scan

A non-executing inspection of GF source text for known suspicious patterns, formatting issues, or project-specific risks.

Static scanning does not replace GF syntax or type checking.

## Target file

The project-owned GF source file selected for a focused quick validation.

---

# 10. Scenario and gold concepts

## Assertion

A precise condition evaluated against scenario execution or output.

Examples:

- expected marker exists;
- forbidden text is absent;
- normalized output equals gold;
- required section completed;
- artifact exists.

## Gold

Reviewed expected normalized output associated with a scenario.

A gold file is a source-controlled acceptance artifact, not generated disposable output.

Canonical extension:

```text
.gold
```

## Gold comparison

The deterministic comparison between normalized scenario output and its reviewed gold file.

## Gold update

An explicit, reviewed operation that replaces a gold file after intentional behavior change.

A gold update MUST NOT occur during ordinary validation.

## Input fixture

Reviewed input data consumed by a scenario.

Input fixtures belong under:

```text
project/validation/inputs/
```

## Marker

Stable text delimiting a scenario output section.

Canonical conceptual form:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

Exact syntax is governed by the scenario-format documentation and lock files.

## Normalization profile

A documented set of transformations applied to raw scenario output before assertion or gold comparison.

## Normalized output

Stable output derived from raw evidence by removing only documented unstable noise.

Normalization must preserve linguistically and diagnostically meaningful content.

Canonical extension:

```text
.out
```

## Required scenario

A scenario that must pass for the validation mode or release gate that includes it.

## Optional scenario

A scenario that may provide additional evidence but is not required for every relevant gate.

## Scenario

A `.gfs` script registered in project configuration and executed by GF Wordbench through GF.

A scenario may test:

- grammar loading;
- missing linearizations;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection.

## Scenario ID

The stable unique identifier assigned to a scenario.

The scenario ID links:

- project configuration;
- `.gfs` script;
- normalized output;
- gold file;
- scenario result;
- reports.

## Scenario result

The structured result of executing one scenario.

It records execution evidence, assertion outcomes, gold comparison, diagnostics, and artifact paths.

## Section

A marker-delimited portion of scenario output with a unique section ID.

## Transcript

The captured stdout and stderr produced by scenario execution.

A transcript is raw evidence unless explicitly normalized.

---

# 11. Execution and process concepts

## Cancellation

An intentional request to stop an operation before normal completion.

Canonical execution state:

```text
cancelled
```

Cancellation is an execution state, not a validation status.

## Command

The executable and ordered argument list sent to an external process.

## Command builder

The component that constructs a valid external-tool invocation from configuration and requested operation.

## Completed

Canonical execution state indicating that the process finished without timeout, cancellation, or launch failure.

```text
completed
```

A completed process may still produce `FAIL` or `ERROR`.

## Contract failure

A failure in which an external tool executed but its observable response violated the expected integration contract.

Examples:

- required marker missing;
- expected artifact not produced;
- output encoding contract violated;
- tool output could not be interpreted according to the supported contract.

## Environment

The external variables and local machine context supplied to a process.

## Execution state

The state of process execution, independent of whether validation passed.

Canonical values:

```text
completed
timed_out
cancelled
launch_failed
```

## Exit code

The integer process status returned by an external executable.

An exit code is evidence. It does not alone determine diagnostic class.

## Launch failure

A failure in which GF Wordbench could not start the requested process.

Canonical execution state:

```text
launch_failed
```

## Process result

The structured result of launching an external process.

It includes at least:

- command;
- working directory;
- exit code;
- execution state;
- duration;
- stdout;
- stderr.

## Standard error

The byte or text stream written by a process to `stderr`.

## Standard input

The data supplied to a process through `stdin`.

GF Wordbench may use standard input to execute `.gfs` scenarios.

## Standard output

The byte or text stream written by a process to `stdout`.

## Timeout

The configured maximum duration allowed for a process or stage.

## Timed out

Canonical execution state indicating that the process exceeded its timeout.

```text
timed_out
```

## Tool failure

A failure in which an external tool launched correctly and reported failure through its exit code, output, or artifacts.

## Validation failure

A result in which execution worked as intended, but a required project criterion was not satisfied.

---

# 12. Result and status concepts

## Error kind

The category describing the nature of an error.

Canonical values:

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

`error_kind` is distinct from diagnostic class, execution state, and validation status.

## Overall status

The aggregate validation status of a complete run.

Canonical values:

```text
OK
FAIL
ERROR
```

A run does not normally use `SKIPPED` as its overall status.

## Validation status

The outcome of one validation result.

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

The requested validation executed and satisfied its criterion.

### `FAIL`

The validation executed correctly but did not satisfy its criterion.

### `ERROR`

GF Wordbench could not correctly execute, interpret, or complete the validation.

### `SKIPPED`

The validation was intentionally not executed.

## File result

The structured result associated with one selected GF source file.

It may include:

- file identity;
- scan counts;
- source fingerprint;
- compile summary;
- diagnostic classification;
- blocking relationships;
- evidence paths.

## Run result

The complete structured in-memory result of one GF Wordbench run.

It is the primary source from which reports and persisted summaries are built.

## Scenario result

See **scenario result** in the scenario section.

## Skipped

A validation result not executed by intentional policy or configuration.

`SKIPPED` must not be used for a launch failure, timeout, or undocumented omission.

---

# 13. Diagnostic concepts

## Ambiguous

Canonical diagnostic class:

```text
ambiguous
```

The available evidence is insufficient to identify the failure confidently as direct or downstream.

## Blocker

A file, module, scenario, tool, or earlier failure that prevents another validation from succeeding or being meaningfully interpreted.

## `blocked_by`

A structured list identifying known blockers for a downstream result.

## Diagnostic class

The category describing the causal relationship of a result to a failure.

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Diagnostic class does not describe the technical error type.

## Direct

Canonical diagnostic class:

```text
direct
```

The evidence points to the current subject as a likely local or root failure.

## Downstream

Canonical diagnostic class:

```text
downstream
```

The current subject failed because a known or strongly indicated dependency failed earlier.

## First error

The earliest relevant normalized diagnostic message selected from a process or stage.

The first error is evidence, not necessarily a complete root-cause diagnosis.

## Framework error

Descriptive prose for an internal GF Wordbench execution or interpretation problem.

`framework_error` is not a canonical diagnostic-class value. Such problems use:

```text
validation_status = ERROR
```

and an appropriate `error_kind`.

## Noise diagnostic

Canonical diagnostic class:

```text
noise
```

A result excluded from meaningful failure analysis by documented policy.

## Normalized diagnostic

A stable structured interpretation derived from raw tool output.

## Root failure

An informal description of the earliest or most causal failure in a chain.

Canonical structured representation normally uses:

```text
diagnostic_class = direct
```

The term *root failure* should not imply mathematical certainty unless evidence supports it.

## Script error

An error related to scenario syntax, unsupported commands, missing markers, malformed script behavior, or scenario-runner interpretation.

Canonical representation uses:

```text
error_kind = SCRIPT
```

`script_error` is not a canonical diagnostic-class value.

---

# 14. Regression and comparison concepts

## Change kind

The classification assigned when comparing a current subject with the corresponding subject in a previous run.

Canonical values:

```text
unchanged
improved
regressed
new
removed
```

## Diff entry

A structured record describing how one file, scenario, or run changed relative to a previous run.

## Improved

A change kind indicating that the current result is better than the previous result according to documented status rules.

## New

A change kind indicating that the current subject did not exist in the comparable previous run.

## Previous run

The most recent compatible earlier run selected for comparison.

## Regressed

A change kind indicating that the current result is worse than the previous result according to documented status rules.

## Regression

An unintended deterioration in validation outcome, output, artifact, compatibility, or documented behavior.

## Regression comparison

The structured comparison between the current run and a compatible previous run.

## Removed

A change kind indicating that a subject existed in the previous run but not in the current run.

## Unchanged

A change kind indicating no relevant difference under the documented comparison rules.

---

# 15. Artifact and evidence concepts

## AI-ready report

The bounded Markdown handoff report designed for human or AI diagnosis without rerunning GF.

Canonical filename:

```text
AI_READY.md
```

## Artifact

A file or persistent output created, copied, or collected by a run.

Examples:

- reports;
- logs;
- `.gfo`;
- `.pgf`;
- normalized scenario output;
- manifests;
- detail files.

## Artifact manifest

The machine-readable inventory of run artifacts, including identity, role, size, and hash.

Canonical filename:

```text
manifest.json
```

## Artifact role

The stable semantic classification assigned to a manifest entry.

Examples:

```text
machine_summary
human_summary
ai_handoff
compile_stdout
compile_stderr
scenario_output
gfo
pgf
```

## Compile log

Captured compile stdout or stderr associated with one file or build action.

## Detail artifact

A per-result file that exposes focused evidence without replacing the raw source log.

## Fingerprint

A stable representation of source identity used to associate results with exact source content or metadata.

Canonical content hashing uses SHA-256.

## Hash

A deterministic digest used to detect content identity or modification.

## Human summary

The main human-readable run report.

Canonical filename:

```text
summary.md
```

## Machine summary

The primary machine-readable run report.

Canonical filename:

```text
summary.json
```

## Manifest

See **artifact manifest**.

## Raw evidence

Unmodified evidence captured from a source or external process.

Examples:

- stdout;
- stderr;
- exit code;
- generated file bytes;
- original scan log;
- process command.

## Report

A persisted presentation derived from structured run results and existing evidence.

A report must not rerun compilation or scenarios to reconstruct missing data.

## Scan log

A per-file text artifact containing static-scan evidence and summary counts.

## Top errors

A deterministic frequency-ranked collection of normalized errors.

Canonical machine representation is an array of records.

Canonical text filename:

```text
top_errors.txt
```

---

# 16. Persistence and schema concepts

## Application state

Disposable persisted local preferences used by the GUI or bootstrap process.

Canonical filename:

```text
.gf_wordbench_state.json
```

Application state is not the authoritative active-project definition.

## Atomic write

A write strategy that prevents partial replacement of the last valid file.

Typical sequence:

1. write a temporary sibling;
2. flush and validate;
3. replace the destination atomically.

## Canonical

The current form emitted by supported writers.

## Compatibility

The ability of a reader, writer, project, or schema version to interoperate without changing the documented meaning of required data.

## Compatible change

A change that preserves existing required meaning and can be consumed safely by supported readers.

Examples:

- adding an optional field with a documented default;
- adding an optional report section;
- adding an optional scenario.

## Breaking change

A change that removes, renames, retypes, reinterprets, or relocates a required contract.

Breaking schema changes require a major schema-version increment and migration policy.

## Legacy

An older accepted form retained only for compatibility or migration.

## Migration

The explicit conversion of an older supported format or project structure into a newer canonical form.

## Migrator

The component that performs a migration.

A migrator reads its source without silently overwriting it before a valid destination exists.

## Persisted asset

Any configuration, state, report, manifest, output, gold, or artifact that survives beyond one in-memory operation.

## Reader

The component that loads or interprets a persisted asset.

## Schema

The documented structure, field meanings, types, enums, defaults, path rules, and compatibility policy of a persisted format.

## Schema ID

A stable identifier naming one persisted format.

Examples:

```text
gf-wordbench.project
gf-wordbench.app-state
gf-wordbench.run-summary
gf-wordbench.artifact-manifest
```

## Schema version

The version of one persisted schema, independent of the GF Wordbench package version.

Canonical form:

```text
MAJOR.MINOR
```

## Soft schema

A human-readable format with a locked identity and minimum required sections but without a strict field-by-field machine schema.

Examples may include:

- `summary.md`;
- `AI_READY.md`.

## Strict mode

A validation mode for schemas or contracts that rejects unknown, non-canonical, or weakly recoverable structures that a compatibility reader might otherwise tolerate.

## Writer

The component that owns and creates a persisted asset.

---

# 17. Configuration concepts

## Application configuration

Framework-level defaults and environment-derived settings used to build a run configuration.

Application configuration does not define the identity of the active language project.

## Application state

See **application state** in the persistence section.

## Configuration precedence

The documented order in which defaults, project configuration, environment values, CLI arguments, and GUI selections are resolved.

## Environment configuration

Machine-specific settings such as:

- GF executable;
- RGL root;
- output root;
- process environment.

## Project configuration

The authoritative language-project definition stored in:

```text
project/project.toml
```

## Run configuration

The fully resolved immutable or stable configuration used for one audit run.

It contains every value needed to execute the run non-interactively.

## `project.toml`

The canonical persisted configuration for one active language project.

It defines project identity, source location, GF path parts, entrypoints, checkpoints, scenarios, and release policy.

---

# 18. Documentation and governance concepts

## ADR

Architecture Decision Record.

An ADR documents one significant framework-level design decision, its context, decision, consequences, and status.

## Decision log

A chronological project or framework record of decisions that do not require a separate ADR or that track language-specific choices.

## Dependency map

A project document recording module providers, consumers, imports, entrypoints, checkpoints, and important dependency chains.

## Known issue

A documented unresolved limitation with defined scope and impact.

## Normative document

A document that defines requirements, contracts, schemas, or canonical terminology.

## Reference document

A document designed for lookup rather than procedural reading.

## Release criteria

The project-specific conditions that must be satisfied before the active language project is considered releasable.

## Release evidence

Persisted evidence proving that release criteria were evaluated against the intended current source state.

## Validation specification

The project document defining required checkpoints, scenarios, inputs, golds, assertions, release gates, and acceptance criteria.

---

# 19. Project and release concepts

## Checkpoint

A module, subsystem, or defined validation boundary whose success demonstrates that one development layer is coherent.

## Decision record

A documented statement of what was decided, why it was decided, and what alternatives or consequences matter.

## Entrypoint

A top-level GF module used for compilation, loading, scenario execution, packaging, API exposure, or release validation.

## Release gate

A mandatory validation criterion or collection of criteria that must pass before release.

## Release target

The configured entrypoint and artifact expected from a release build.

---

# 20. Canonical value reference

## Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

## Overall run status

```text
OK
FAIL
ERROR
```

## Execution state

```text
completed
timed_out
cancelled
launch_failed
```

## Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

## Error kind

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

## Validation mode

```text
quick
checkpoint
release
diagnostic
```

## Diff change kind

```text
unchanged
improved
regressed
new
removed
```

---

# 21. Legacy and non-canonical aliases

| Legacy or discouraged term | Canonical replacement | Policy |
|---|---|---|
| `gf-audit` | `GF Wordbench` / `gf-wordbench` | Historical compatibility only |
| `.gf_audit_state.json` | `.gf_wordbench_state.json` | Import and migrate |
| `file` mode | `quick` | Read as migration alias |
| `all` mode | `diagnostic` | Read as migration alias |
| `ai_brief_path` | `artifacts.ai_ready` | Read alias only |
| `ai_ready_path` as absolute persisted path | `artifacts.ai_ready` as run-relative path | Migrate |
| `script_error` diagnostic class | `error_kind = SCRIPT` | Do not emit |
| `framework_error` diagnostic class | `validation_status = ERROR` plus appropriate `error_kind` | Do not emit |
| `CANCELLED` validation status | `execution_state = cancelled` | Do not emit as validation status |
| flat `ok` total | `files_ok` | Migrate |
| flat `fail` total | `files_fail` | Migrate |
| top-error mapping | ordered top-error record array | Migrate |
| `sha1_short` | SHA-256 fingerprint fields | Read legacy only |
| *root* without qualifier | project root, source root, run root, RGL root, or output root | Qualify |
| *status* without qualifier | validation status, overall status, execution state, ADR status, or document status | Qualify |
| *output* without qualifier | stdout, stderr, raw evidence, normalized output, report, or artifact | Qualify |

---

# 22. Terms intentionally kept distinct

The following pairs MUST NOT be treated as synonyms.

## Artifact vs evidence

An artifact is a persisted file. Evidence is information supporting a conclusion. An artifact may contain evidence, but not every artifact is evidence and not every piece of evidence is a separate artifact.

## Canonical vs current

*Canonical* means the format writers are authorized to emit. *Current* may refer only to what happens to exist in a working copy.

## Compilation success vs release success

Compilation success proves that a compilation operation succeeded. Release success requires every configured release gate.

## Diagnostic class vs error kind

Diagnostic class describes causal relationship. Error kind describes technical nature.

## Entry point vs checkpoint

An entrypoint is a top-level module used for loading, packaging, or release. A checkpoint proves a development layer and may be lower-level.

## Execution state vs validation status

Execution state describes what happened to the process. Validation status describes whether the criterion passed.

## Framework configuration vs project configuration

Framework configuration defines reusable application behavior and environment defaults. Project configuration defines the active language project.

## GF truth vs scan finding

GF execution is authoritative for GF syntax, typing, module resolution, and runtime behavior. A scan finding is heuristic evidence only.

## Gold vs generated output

A gold file is reviewed expected output. Generated output is the current result being tested.

## Internal detail vs contract

An internal detail is not consumed elsewhere. A contract is externally depended upon and cannot change silently.

## Legacy vs deprecated

Legacy describes an older readable format or term. Deprecated describes a still-supported contract scheduled for removal.

## Project root vs repository root

The project root anchors the active language project. The repository root anchors the full GF Wordbench checkout. They may coincide but are not semantically identical.

## Raw evidence vs normalized evidence

Raw evidence is unmodified. Normalized evidence applies documented stability transformations.

## Scenario failure vs compilation failure

A scenario may fail after compilation succeeds. These are distinct result types and must remain separately reportable.

## Validation failure vs framework error

A validation failure means the project did not satisfy the criterion. A framework error means GF Wordbench could not execute or interpret the criterion correctly.

---

# 23. Cross-reference ownership

Detailed rules belong to these documents:

| Topic | Authoritative document |
|---|---|
| Python file boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| External executables and GF invocation | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted fields, schemas, paths, and migrations | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Active-project GF module boundaries | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Architecture | `docs/architecture/ARCHITECTURE_OVERVIEW.md` |
| Validation stages and modes | `docs/validation/VALIDATION_PIPELINE.md`, `VALIDATION_MODES.md` |
| Scenario syntax and markers | `docs/scenarios/SCENARIO_FORMAT.md` |
| Gold comparison | `docs/scenarios/GOLDEN_TESTS.md` |
| Diagnostics | `docs/diagnostics/DIAGNOSTIC_OVERVIEW.md` |
| Configuration | `docs/configuration/CONFIGURATION_OVERVIEW.md` |
| Reports | `docs/reports/REPORTING_OVERVIEW.md` |
| Project acceptance | `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md`, `RELEASE_CRITERIA.md` |

When two documents appear to define the same term differently, this glossary controls the term’s general meaning, while the more specialized normative document controls its detailed operational rules.

---

# 24. Glossary change policy

A glossary change is required when:

- a new public concept is introduced;
- an enum value is added, removed, or renamed;
- a legacy alias is accepted or retired;
- two documents use different names for the same concept;
- one term becomes ambiguous across framework and project layers;
- a contract lock introduces a new normative term.

A glossary change MUST include:

```text
[ ] canonical term selected
[ ] definition written
[ ] conflicting aliases identified
[ ] affected schemas reviewed
[ ] affected lock files reviewed
[ ] code and tests reviewed
[ ] migration impact reviewed
[ ] cross-references updated
```

A term MUST NOT be redefined silently.

---

# 25. Final terminology rule

> One concept must have one canonical name, and one canonical name must have one stable meaning.

When precision matters, use the qualified term even if the shorter form appears obvious.
