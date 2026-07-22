# GF Wordbench — Terminology Reference

**Document ID:** `GF-WB-REF-TERMINOLOGY`  
**Status:** Canonical reference  
**Applies to:** Framework code, persisted schemas, reports, project documentation, tests and release materials  
**Owner:** GF Wordbench maintainers  
**Related glossary:** `docs/GLOSSARY.md`  
**Related status reference:** `docs/reference/STATUS_VALUES.md`  
**Related diagnostic reference:** `docs/reference/DIAGNOSTIC_KINDS.md`  
**Related schema reference:** `docs/reference/SCHEMA_INDEX.md`

---

## 1. Purpose

This document is the compact canonical terminology reference for GF Wordbench.

Use it when naming:

- Python models and fields;
- CLI and GUI labels;
- persisted schema values;
- report headings;
- diagnostics;
- scenarios;
- artifacts;
- project documents;
- release records;
- tests.

The core rule is:

> One concept must have one canonical name, and one canonical name must not carry multiple unrelated meanings.

`docs/GLOSSARY.md` may provide longer explanations and examples. This file defines the preferred terms and their concise meanings.

---

## 2. Usage rules

- Use the exact canonical spelling shown here.
- Do not create local synonyms in code or schemas.
- Human-facing prose may use natural grammar, but machine values remain exact.
- A deprecated term may appear only in migration, compatibility or historical context.
- A term that changes schema or contract meaning requires coordinated review.
- Project-specific linguistic terminology belongs in `project/docs/`.

---

## 3. Product and repository terms

### GF Wordbench

The official product and repository name.

Canonical display form:

```text
GF Wordbench
```

### `gf-wordbench`

The canonical package, executable and CLI name.

### Framework

The reusable application code, tests, generic documentation and project template.

Framework scope includes:

```text
app/
tests/
docs/
templates/
```

### Active project

The one language project represented by the current repository copy.

Canonical location:

```text
project/
```

### Project template

The reusable generic project structure copied when creating a new active project.

Canonical location:

```text
templates/project/
```

### Repository copy

One clone or duplicate of GF Wordbench containing one active project.

### Active language

The language configured by the active project.

The framework itself is language-neutral.

### Project identity

The authoritative set of facts identifying the active project.

Primary owner:

```text
project/project.toml
```

### Project asset

A maintained, reviewed project-owned input.

Examples:

```text
project/project.toml
project/docs/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

### Source file

A GF source module, normally using the `.gf` extension.

### Generated artifact

A file created by GF Wordbench or an external tool during execution.

---

## 4. Configuration terms

### Application configuration

Framework-wide and local execution configuration used to construct a run.

### Project configuration

Project facts and validation policy persisted in:

```text
project/project.toml
```

### Application state

Disposable local convenience data such as recent paths or UI preferences.

Canonical file:

```text
.gf_wordbench_state.json
```

Application state is not project configuration.

### `AppConfig`

Typed framework/application defaults and environment-derived configuration.

### `RunConfig`

Complete immutable or effectively immutable configuration required to execute one non-interactive audit.

### Configuration builder

The shared provider that constructs validated `AppConfig` and `RunConfig` values for CLI and GUI consumers.

### Environment override

An explicit child-process environment value supplied by configuration.

### Local path

A machine-specific path such as the GF executable or RGL installation.

Local paths should not become portable project identity.

### Project-relative path

A path resolved against the active project root.

### Run-relative path

A path resolved against one run directory.

### Repository-relative path

A path resolved against the GF Wordbench repository root.

---

## 5. Execution and run terms

### Audit

One GF Wordbench validation execution.

### Run

A single persisted audit instance with one run ID and one run directory.

### Run ID

Filesystem-safe identifier for one run.

Recommended form:

```text
YYYYMMDD_HHMMSS
```

using UTC, with a deterministic collision suffix when necessary.

### Run directory

The directory containing all artifacts for one run.

Canonical pattern:

```text
run_<run-id>/
```

### `RunPaths`

The typed authoritative registry of paths owned by one run.

### Stage

One ordered validation step in the audit pipeline.

Examples:

```text
selection
scan
compile
scenario
diagnostic parsing
classification
reporting
manifest finalization
```

### Orchestration

Coordination of run lifecycle, stage order, dependencies and finalization.

### Execution mode

The configured validation scope.

Canonical values:

```text
quick
checkpoint
release
diagnostic
```

### `quick`

Fast targeted validation for early feedback.

### `checkpoint`

Validation of configured dependency-layer checkpoints and associated evidence.

### `release`

Strict validation of all required release gates and artifacts.

### `diagnostic`

Broad evidence collection intended to investigate failures without weakening status semantics.

### Legacy mode alias

Deprecated input mapped to a canonical mode.

Canonical aliases:

```text
file → quick
all  → diagnostic
```

### Current run

The run presently being executed or viewed.

### Previous compatible run

A prior run eligible for regression comparison under the compatibility policy.

---

## 6. Validation-status terms

### Validation status

The outcome of a validation object such as a file result or scenario result.

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

Validation completed and all applicable criteria passed.

### `FAIL`

Validation completed and produced interpretable evidence showing that a criterion failed.

Examples:

- GF type or syntax failure;
- gold mismatch;
- expected artifact not produced after otherwise normal execution;
- required linguistic expectation not met.

### `ERROR`

GF Wordbench could not complete or interpret validation reliably.

Examples:

- timeout;
- cancellation;
- launch failure;
- invalid configuration;
- I/O failure;
- schema failure;
- parser failure;
- untrusted artifact state.

### `SKIPPED`

Validation was intentionally not executed or could not run because of an explicit prerequisite policy.

### Success

Informal human term normally corresponding to `OK`.

Do not persist `SUCCESS` as a validation status.

### Non-success

Any outcome other than `OK`.

### Required result

A result whose non-success affects the containing gate according to policy.

### Optional result

A visible result that does not automatically block every gate.

---

## 7. Execution-state terms

### Execution state

The terminal state of one external process invocation.

Canonical values:

```text
completed
timed_out
cancelled
launch_failed
```

### `completed`

The process started and terminated before timeout or cancellation became the terminal cause.

It may still produce validation `OK`, `FAIL` or `ERROR`.

### `timed_out`

The process exceeded its finite deadline and termination was initiated.

### `cancelled`

The user or controller requested termination before timeout became the terminal cause.

### `launch_failed`

The operating system did not successfully start the requested process.

### Timeout

Expiration of the configured finite execution deadline.

Timeout maps to validation `ERROR` and error kind `TIMEOUT`.

### Cancellation

Explicit request to stop an active or pending operation.

Cancellation is an execution state, not a fifth validation status.

### Launch failure

Failure to start the requested executable.

### Normal termination

Process exit observed without timeout or cancellation as the terminal cause.

### Abnormal termination

Process termination caused by crash, signal, forced stop or other nonstandard condition.

### Soft termination

First cooperative or graceful attempt to stop an owned process tree.

### Forced termination

Hard termination attempted after the grace period.

### Termination grace period

Finite cleanup interval between soft and forced termination.

### Owned process tree

The process launched by GF Wordbench and its attributable descendants.

### Process-tree containment

Mechanism used to identify and terminate only the owned process tree.

### Process result

Typed record containing execution state, exit code, timing, capture paths and process-level warnings.

### Process request

Typed immutable description of an external invocation.

---

## 8. Error-kind terms

### Error kind

Stable category describing the primary failure type.

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

### `TYPE`

GF type-level or interface-level incompatibility.

### `SYNTAX`

GF lexical or source-syntax failure.

### `INTERNAL`

Internal GF Wordbench or GF invariant failure, used conservatively.

### `TIMEOUT`

Execution deadline exceeded.

### `SCRIPT`

Native GF shell script or command-contract failure.

### `CONFIG`

Invalid or incomplete configuration.

### `IO`

Filesystem, encoding, capture or persistence failure.

### `TOOL`

External-tool contract, compatibility, launch or required-tool-artifact failure not represented more precisely.

### `OTHER`

Interpretable failure that cannot be classified safely into a more specific canonical kind.

### `OK` error kind

No applicable error.

---

## 9. Diagnostic-class terms

### Diagnostic class

Causal relationship assigned by the classifier.

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### `ok`

No failure requiring causal classification.

### `direct`

Evidence identifies the current target or scenario as the primary failure owner.

### `downstream`

The current failure is caused by a previously identified dependency or prerequisite failure.

### `ambiguous`

Evidence is insufficient to assign direct or downstream ownership safely.

### `noise`

Recognized non-actionable diagnostic output that does not represent the validation failure.

### `skipped`

No causal classification applies because the item was skipped.

### Root cause

Informal term for the failure owner identified as direct through sufficient evidence.

Do not equate the first emitted diagnostic automatically with root cause.

### Cascade

Series of downstream failures caused by one or more earlier direct failures.

---

## 10. Diagnostic-parsing terms

### Diagnostic parser

Component that structures GF diagnostic text without assigning causal ownership.

### Diagnostic record

Structured representation of one recognized or retained diagnostic unit.

### Primary diagnostic

Deterministically selected diagnostic used for compact result fields.

### `first_error`

Compatibility field containing the compact message from the selected primary diagnostic.

It does not guarantee true cross-stream chronological first occurrence.

### `error_detail`

Bounded supporting context from the primary diagnostic.

### Diagnostic severity

Internal importance level:

```text
info
warning
error
fatal
unknown
```

### Pattern ID

Stable identifier for one diagnostic recognition rule.

Recommended form:

```text
GF-DIAG-<DOMAIN>-<NUMBER>
```

### Pattern registry

Versioned collection of supported diagnostic patterns and their scope.

### Parser version

Independent version identifying diagnostic interpretation behavior.

### Exact match confidence

Diagnostic form matches a narrowly defined fixture-backed pattern.

### Strong match confidence

Diagnostic form matches a documented guarded family.

### Fallback match confidence

Failure evidence is retained but only safely classified as a general category.

### Unknown diagnostic

Suspicious or failure-associated output that cannot be safely mapped to a known pattern.

Unknown diagnostic evidence is not noise.

### Continuation line

Line belonging to a preceding multiline diagnostic.

### Raw excerpt

Bounded text copied from raw evidence for a diagnostic record.

### Normalized diagnostic signature

Stable grouping identity used for aggregation and regression comparison.

---

## 11. File-selection and scanning terms

### File selection

Resolution of the ordered set of source files to validate.

### Target file

Explicit source file selected for targeted validation.

### Source root

Configured base directory containing relevant GF source files.

### Source glob

Pattern defining candidate source files.

### Include pattern

Rule adding eligible paths to selection.

### Exclude pattern

Rule removing eligible paths from selection.

### Static scan

Supplementary source-text analysis performed without native GF semantic authority.

### Scan rule

One versioned heuristic check applied to source text.

### Scan finding

One source-location observation produced by a scan rule.

### Scan count

Count of findings grouped by scan rule or category.

### Native validation

Validation performed by the GF executable.

Static scanning does not replace native validation.

---

## 12. Compilation terms

### Compilation

Native GF processing of a configured source target or checkpoint.

### File compilation

Compilation focused on one `.gf` source file.

### Checkpoint compilation

Compilation or load validation of a configured dependency-layer module.

### Final entrypoint validation

Validation of the configured top-level grammar or API module.

### PGF build

Native GF operation producing a `.pgf` artifact.

### `.gfo`

GF compiled-object artifact.

### `.pgf`

GF Portable Grammar Format artifact.

GF owns the binary format.

### Current artifact

Artifact proven to belong to the current invocation.

### Stale artifact

Pre-existing artifact not proven to belong to the current operation.

### Required artifact

Artifact whose absence or invalidity causes non-success.

### Optional artifact

Documented artifact that may be absent without invalidating the operation.

### Artifact trust

Assessment of whether an artifact may be used as valid current evidence.

Artifacts produced during timeout or cancellation are untrusted by default.

### Source fingerprint

Deterministic identity derived from relevant source inputs and configuration.

---

## 13. Project architecture terms

### Module

Named GF source unit.

### Module file

Filesystem file containing one GF module.

### Module name

GF-declared identifier of a module.

### Module suffix

Project-specific suffix identifying the active language in module names.

### Entrypoint

Top-level configured GF module used for loading, validation, API exposure or release construction.

### Checkpoint

Configured module representing a meaningful dependency-layer validation boundary.

### Provider

Module or component that owns and exposes a contract.

### Consumer

Module or component that depends on a provider contract.

### Direct dependency

Explicit import or call relationship.

### Transitive dependency

Dependency reached through one or more intermediate providers.

### Dependency map

Reviewed project representation of module relationships and checkpoint order.

### Category contract

Cross-module agreement concerning GF categories.

### Lincat contract

Cross-module agreement concerning concrete-syntax linearization categories and shared record fields.

### Constructor contract

Cross-module agreement concerning public GF constructors and their behavior.

### Fallback

Explicit temporary or compatible alternative behavior selected under a documented rule.

### Placeholder

Unresolved template or planned value such as `<ENTRYPOINT>`.

Unresolved placeholders are prohibited in final normative project files.

---

## 14. Scenario terms

### Scenario

One registered native GF shell script executed as one GF process invocation.

### Scenario ID

Stable project identifier for one scenario.

Recommended form:

```text
[a-z][a-z0-9-]*
```

### Scenario registry

Required and optional scenario lists in `project/project.toml`.

### Scenario file

Canonical script:

```text
project/validation/scenarios/<scenario-id>.gfs
```

### Required scenario

Scenario whose non-success affects required validation according to project policy.

### Optional scenario

Registered scenario not automatically required by every gate.

### Scenario section

Marked region of output with one stable validation purpose.

### Section ID

Stable identifier for a scenario section.

### Scenario marker

Exact line delimiting a raw scenario section.

Canonical form:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

### Marker completion

Successful recognition of matching begin and end markers.

### Scenario input

Inline or project-owned data consumed by a scenario.

### Input asset

Reviewed file under:

```text
project/validation/inputs/
```

### Scenario assertion

Criterion evaluated after native GF execution.

### Negative scenario

Scenario intentionally validating rejection or absence of behavior.

### Bounded scenario

Scenario constrained by finite timeout, output and operation limits.

### Deterministic scenario

Scenario expected to produce equivalent normalized output for equivalent supported inputs.

---

## 15. Normalization terms

### Normalization

Versioned transformation of captured output into deterministic comparison material.

### Raw output

Unmodified process stdout or stderr.

### Parse view

Derived in-memory representation prepared for diagnostic recognition.

### Normalized output

Deterministic derived text used for comparison.

Canonical scenario artifact:

```text
raw/scenarios/<scenario-id>.out
```

### Normalizer

Single owner of comparison normalization.

### Normalization profile

Named ordered set of normalization rules.

### Profile ID

Stable identifier of a normalization profile.

### Normalization version

Independent `MAJOR.MINOR` version identifying profile behavior.

### Stable token

Canonical placeholder replacing one approved unstable value.

Examples:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<TEMP_DIR>
<TIMESTAMP>
<DURATION_MS>
```

### Lossy rule

Normalization rule that removes or replaces source text.

### Idempotent normalization

Applying normalization again does not change the canonical result.

### Semantic output

Linguistic or grammatical output whose exact identity matters.

### Noise normalization

Removal or replacement of explicitly documented non-semantic instability.

### Unknown output

Output not safely classified by markers or approved rules.

Unknown output must not be silently deleted.

### Truncated output

Output cut by a configured safety limit.

Truncated output cannot satisfy an exact required comparison.

---

## 16. Golden-testing terms

### Gold file

Reviewed project-owned expected normalized output.

Canonical location:

```text
project/validation/gold/<scenario-id>.gold
```

### Gold-backed scenario

Scenario whose criteria include exact comparison against a gold file.

### Actual output

Current run’s normalized output.

### Expected output

Reviewed project gold.

### Gold comparison

Deterministic comparison of actual normalized output with expected gold.

### Gold match

Boolean or nullable comparison field indicating exact agreement.

### Gold mismatch

Valid comparison showing different accepted and actual outputs.

Canonical scenario result:

```text
status = FAIL
gold_match = false
```

### Gold diff

Derived deterministic diff artifact describing a mismatch.

### Gold update

Explicit project mutation creating or replacing a gold after review.

### Gold requiredness

Whether a gold is required, optional or not applicable for a scenario.

### Gold schema

Persisted schema defining gold file structure and identity.

### Blind gold update

Unreviewed acceptance of current output.

Blind gold updates are prohibited.

---

## 17. Artifact terms

### Artifact

Persisted file or directory with a defined role, owner, path base and lifecycle.

### Run artifact

Artifact owned by one run.

### Control artifact

Artifact describing run identity or inventory.

Examples:

```text
summary.json
manifest.json
master.log
```

### Raw evidence artifact

Unmodified captured evidence.

Examples:

```text
stdout
stderr
scan logs
```

### Derived artifact

Artifact computed from raw evidence or structured results.

Examples:

```text
normalized output
gold diff
summary.md
```

### Report artifact

Machine- or human-facing projection of structured results.

### Tool-generated artifact

Artifact whose bytes are produced by GF or another approved tool.

### Framework-generated artifact

Artifact whose bytes are produced by GF Wordbench.

### Artifact owner

Component responsible for location, format and write lifecycle.

### Artifact producer

Component or external tool producing the bytes.

### Artifact observer

Component allowed to read but not redefine or rewrite an artifact.

### Artifact cataloguer

Component recording metadata about an artifact without owning its contents.

### Artifact role

Stable semantic classification recorded in the manifest.

### Artifact finalization

Transition after all writers close, checks pass and final metadata/hashes are produced.

### Artifact integrity

Agreement between persisted file bytes and recorded metadata such as size and hash.

### Artifact manifest

Canonical finalized file inventory.

Canonical file:

```text
manifest.json
```

### Manifest entry

One artifact record containing path, role, size, hash and ownership metadata.

### SHA-256

Canonical cryptographic hash algorithm used for manifest integrity.

### Partial artifact

Incomplete or untrusted artifact retained after abnormal execution.

### Ephemeral file

Temporary implementation file not part of the finalized artifact set.

---

## 18. Report terms

### `summary.json`

Primary machine-readable run result.

### `summary.md`

Human-readable projection of the structured run result.

### `AI_READY.md`

Bounded evidence packet intended for AI-assisted analysis.

It is not a separate validation engine.

### `top_errors.txt`

Stable textual ranking of normalized error buckets.

### Detail report

Focused per-result human-readable artifact under `details/`.

### Aggregate log

Convenience file combining or indexing multiple logs.

### Raw log

Original captured evidence.

### Soft schema

Documented minimum identity and sections for a human-readable report.

### Report writer

Single owner of one report format.

### Report consumer

User or system reading a report without rerunning validation.

### Machine source of truth

Canonical structured persisted result.

For run outcomes:

```text
summary.json
```

### Projection

Derived representation of structured results for a specific audience.

---

## 19. Result-model terms

### Run result

Typed aggregate result of one audit.

### File result

Typed result for one selected source file or checkpoint target.

### Scenario result

Typed result for one scenario execution.

### Compile summary

Typed compilation/process/diagnostic summary used within a file or stage result.

### Diff entry

Structured description of a change between compatible runs.

### Result builder

Owner that combines process, diagnostic, artifact and comparison evidence into final typed results.

### Result ordering

Canonical deterministic sequence of results.

Examples:

```text
file results → normalized path order
scenario results → configuration order
```

### Result count invariant

Consistency rule requiring totals to agree with contained result arrays.

### Primary message

Concise human-readable message selected for one result.

---

## 20. Regression terms

### Regression comparison

Comparison of the current run with a previous compatible run.

### Baseline run

Selected prior run used as a comparison reference.

### Compatible run

Run whose schema, project identity and comparison-relevant configuration permit comparison.

### Change kind

Stable category describing how a result changed.

Exact values are defined in the schema/reference owner.

### New failure

Current non-success where the baseline did not contain the same failure.

### Resolved failure

Baseline failure no longer present.

### Unchanged failure

Equivalent failure present in both runs.

### Changed failure

Failure remains but its stable identity or classification changed.

### New item

Current file/scenario absent from the baseline.

### Removed item

Baseline file/scenario absent from the current run.

### Regression

New or worsened behavior relative to the accepted baseline or gold policy.

Gold comparison and previous-run comparison are separate concepts.

---

## 21. Schema and persistence terms

### Persisted schema

Versioned machine-readable data contract.

### Schema ID

Stable identifier of one persisted format.

### Schema version

Independent version describing the persisted structure and semantics.

### Canonical writer

Current writer emitting only the current canonical schema.

### Legacy reader

Compatibility reader accepting an older supported format.

### Migration

Deterministic conversion from an older supported schema to a newer one.

### Schema major version

Version increment required for incompatible persisted changes.

### Schema minor version

Version increment for compatible persisted additions.

### Forward compatibility

Ability of an older reader to handle a newer compatible format according to policy.

### Backward compatibility

Ability of current software to read or interoperate with older supported formats.

### Atomic write

Write-to-temporary, validate and replace operation preserving the last valid destination on failure.

### Null

Explicit serialized absence where allowed by schema.

### Missing field

Field not present in serialized data.

Missing and null may have different meanings.

### Unknown field

Field not recognized by the current reader.

Handling depends on schema compatibility policy.

### Unknown enum value

Serialized vocabulary value not recognized by the current reader.

It must not silently map to success.

---

## 22. Contract terms

### Contract

Explicit provider/consumer agreement concerning requests, responses, ownership, errors and invariants.

### Contract lock

Normative file freezing a set of contracts against silent drift.

### Interfile contract

Framework Python provider/consumer boundary.

### External-tool contract

Boundary between GF Wordbench and GF, the operating system or another approved tool.

### Persisted contract

Schema, path and lifecycle agreement for durable data.

### Project contract

Active-language relationship between modules, scenarios, inputs, golds and release artifacts.

### Contract ID

Stable identifier of one contract entry.

### Contract version

Independent version identifying observable contract behavior.

### Contract status

Lifecycle state of a contract entry.

Typical values:

```text
active
experimental
deprecated
blocked
retired
```

### Locked invariant

Rule that provider and consumers must preserve.

### Forbidden behavior

Explicitly prohibited implementation or integration behavior.

### Coordinated change

One change unit updating provider, consumers, tests, schemas, migrations and documentation together.

### Drift

Undocumented divergence between implementation, consumers, schemas or documentation.

### Anti-drift check

Automated or manual verification intended to detect contract divergence.

---

## 23. Versioning terms

### Application version

Semantic version of the GF Wordbench package.

Canonical form:

```text
MAJOR.MINOR.PATCH
```

### Project version

Independent semantic version of the active-language project.

### Template version

Version of the reusable project template.

### Parser version

Version of diagnostic parsing behavior.

### Profile version

Version of normalization behavior.

### GF version

Version reported by the GF executable.

### Prerelease

Version published before final stability.

Examples:

```text
alpha
beta
rc
```

### Release candidate

Prerelease intended to become final unless blocking defects are found.

### Build metadata

Non-precedence metadata appended to a semantic version.

### Major change

Incompatible change requiring consumer modification or migration.

### Minor change

Backward-compatible capability addition.

### Patch change

Backward-compatible correction.

### Deprecation

Supported behavior scheduled for removal.

### Removal

End of supported behavior after the declared transition.

### Compatibility window

Period during which legacy behavior or schemas remain supported.

---

## 24. Release terms

### Release gate

Required condition that must pass before a release is ready.

### Release run

Audit executed in `release` mode.

### Release readiness

State in which all configured project and framework release gates pass.

### Release artifact

Published artifact produced by a release run.

### Release PGF

Verified current `.pgf` produced from the configured release entrypoint.

### Release manifest

Verified manifest accompanying release evidence.

### Release blocker

Known condition preventing release readiness.

### Release criterion

Project-specific statement defining one required release condition.

### Release evidence

Persisted artifacts and structured results proving a release criterion.

### Release note

Human-facing summary of changes, compatibility, migrations and known issues.

### Changelog

Version-organized record of released changes.

---

## 25. Project-documentation terms

### Language overview

Project document describing language scope, identity and coverage.

### Language architecture

Project document describing module layers and entrypoints.

### Module dependency map

Project document describing imports and checkpoint relationships.

### Category and lincat contract

Project document defining shared category and linearization-category structures.

### Morphology specification

Project document defining paradigms and inflectional behavior.

### Syntax and constructor rules

Project document defining syntactic structure and constructor policy.

### Validation specification

Project authority defining what must be proven.

### Test coverage matrix

Mapping from requirements to providers, scenarios, inputs, golds and evidence.

### Status ledger

Tracked record of incomplete, temporary, blocked or fallback states.

### Decision log

Project-specific record of accepted choices.

### Known issue

Documented defect, limitation or risk.

### Release criteria

Project-specific final gate definition.

### Research evidence

Sources and observations supporting linguistic decisions.

---

## 26. Development terms

### Public API

Explicitly supported Python or CLI surface.

### Internal API

In-repository interface not promised as external package API but still governed by interfile contracts.

### Side effect

Filesystem, process, state, logging, environment or GUI mutation.

### Pure function

Function whose result depends only on explicit inputs and has no externally visible side effects.

### Adapter

Component translating one external or platform-specific interface into a stable internal contract.

### Boundary type

Typed request or result crossing module/layer boundaries.

### Compatibility adapter

Reader or translator supporting an older contract without changing the canonical writer.

### Feature flag

Typed centrally resolved switch controlling optional behavior.

### Strict mode

Policy mode rejecting compatibility ambiguity, unsafe fallback or unexpected content.

### Dry run

Operation resolving/displaying actions without fabricating validation success.

### Debug mode

Mode adding diagnostic evidence without weakening validation semantics.

### Test fixture

Controlled data or executable used to validate framework behavior.

### Real-GF test

Integration test invoking an actual supported GF executable.

### Golden fixture

Expected framework test output, distinct from active-project linguistic gold.

### Regression test

Test added to prevent recurrence of a defect.

### Property test

Test asserting general invariants over generated bounded inputs.

---

## 27. Security terms

### Trust boundary

Point where untrusted data enters a component.

Examples:

```text
CLI input
project paths
.gfs scripts
GF output
persisted files
external artifacts
```

### Untrusted text

Text that must be treated as data and escaped before rendering.

### Shell escape

Mechanism invoking operating-system commands from a script or shell.

Disabled by default for project scenarios.

### Path traversal

Attempt to escape an approved path root through relative segments or links.

### Symlink policy

Rules governing whether symbolic links are allowed, followed or rejected.

### Secret

Credential or sensitive token that must not be persisted in project/state/reports/logs.

### Redaction

Creation of a derived publication-safe copy with sensitive details removed.

Redacted content is not raw evidence.

### Resource bound

Finite runtime, output, memory or count limit protecting the system.

---

## 28. Compatibility terms

### Supported

Behavior or version covered by declared tests and release policy.

### Tested

Behavior demonstrated in the recorded test matrix.

Tested does not always imply fully supported.

### Experimental

Available behavior whose compatibility may change and is explicitly not stable.

### Supported with warnings

Usable under known limitations surfaced to the user.

### Unsupported

Known not to satisfy the declared contract.

### Unknown

Not yet classified through sufficient evidence.

### Capability probe

Safe operation determining whether a tool supports one required behavior.

### Compatibility matrix

Documented relationship between GF Wordbench, Python, platforms, GF versions and project/profile versions.

### Legacy

Older supported or historical behavior retained for compatibility.

### Canonical

Current authoritative representation emitted by writers and documented as the standard.

---

## 29. Terms to avoid

The following terms are ambiguous or non-canonical unless explicitly qualified.

| Avoid | Use instead |
|---|---|
| success status | `OK` |
| failed status | `FAIL` or `ERROR`, as applicable |
| cancelled status | execution state `cancelled` plus validation `ERROR` |
| grammar test | scenario, compile validation or release gate |
| output file | name the artifact role |
| log | raw log, aggregate log or master log |
| config | application configuration or project configuration |
| state | application state, execution state or validation status |
| error type | error kind |
| error class | diagnostic class |
| root cause | direct failure, when evidence supports it |
| expected output | gold, when referring to project acceptance |
| current output | actual normalized output |
| build | compilation, PGF build or package build |
| project | active project, repository or project template |
| language | active language, GF language module or concrete language |
| result | file result, scenario result, process result or run result |
| version | application, schema, contract, project, parser, profile or GF version |
| artifact | specify raw, derived, report, control or tool-generated when relevant |
| baseline | baseline run or project gold |
| normalization | diagnostic parsing, path normalization or scenario-output normalization |
| skipped error | `SKIPPED` status with explicit reason |
| warning failure | warning plus policy-defined outcome |

---

## 30. Deprecated canonical aliases

The following terms may appear only in compatibility contexts.

### `gf-audit`

Legacy product/package naming.

Canonical replacement:

```text
GF Wordbench
gf-wordbench
```

### File mode

Legacy mode concept.

Canonical replacement:

```text
quick
```

### All mode

Legacy mode concept.

Canonical replacement:

```text
diagnostic
```

### `CANCELLED` validation status

Deprecated/invalid validation vocabulary.

Canonical representation:

```text
execution_state = cancelled
validation_status = ERROR
```

### AI brief

Legacy or informal name for the AI-ready report.

Canonical artifact:

```text
AI_READY.md
```

### Audit state as project config

Invalid legacy assumption.

Canonical authority:

```text
project/project.toml
```

---

## 31. Canonical machine vocabularies

### Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

### Execution state

```text
completed
timed_out
cancelled
launch_failed
```

### Error kind

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

### Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### Validation mode

```text
quick
checkpoint
release
diagnostic
```

These vocabularies are closed unless a coordinated contract and schema change explicitly modifies them.

---

## 32. Naming review checklist

Before introducing a new term:

```text
[ ] Existing canonical term searched
[ ] Concept owner identified
[ ] Machine versus human use identified
[ ] Schema impact reviewed
[ ] Contract impact reviewed
[ ] CLI/GUI impact reviewed
[ ] Report impact reviewed
[ ] Project/template impact reviewed
[ ] Migration alias considered
[ ] Terminology reference updated
```

Do not add synonyms merely for local convenience.

---

## 33. Terminology drift indicators

Terminology drift exists when:

- code and schema use different names for the same concept;
- one term has multiple meanings;
- `FAIL` and `ERROR` are used interchangeably;
- cancellation becomes a validation status;
- parser and classifier terms are mixed;
- actual output is called raw output;
- gold is called a run artifact;
- application state is called project configuration;
- entrypoint and checkpoint are treated as synonyms;
- application version is used as schema version;
- report prose introduces a new status word;
- legacy names appear in new canonical APIs;
- one project-specific linguistic term enters framework machine vocabulary;
- documentation uses “root cause” without direct-classification evidence.

Every drift indicator requires correction or an explicit terminology decision.

---

## 34. Related documents

- `docs/GLOSSARY.md`
- `docs/reference/STATUS_VALUES.md`
- `docs/reference/DIAGNOSTIC_KINDS.md`
- `docs/reference/SCHEMA_INDEX.md`
- `docs/reference/COMMAND_REFERENCE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/diagnostics/ERROR_CLASSIFICATION.md`
- `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md`
- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/release/VERSIONING_POLICY.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 35. Final enforcement rule

Canonical terminology is part of the architecture.

Therefore:

> A new name must not be introduced when an existing canonical term already describes the concept, and an existing term must not be reused for a different concept.

Code, schemas, reports and documentation must remain aligned with this reference.
