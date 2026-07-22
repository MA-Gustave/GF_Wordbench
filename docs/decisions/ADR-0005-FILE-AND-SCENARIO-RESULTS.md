# ADR-0005 — Separate File and Scenario Result Models

**ADR ID:** `ADR-0005`  
**Status:** Accepted  
**Implementation status:** Partially implemented  
**Decision date:** `2026-07-22`  
**Last reviewed:** `2026-07-22`  
**Owners:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\decisions\ADR-0005-FILE-AND-SCENARIO-RESULTS.md`  
**Decision scope:** Runtime result models, result construction, classification, run aggregation, persisted run summaries, reports, diffs, tests, and migrations  
**Related contracts:** `IFC-AUDIT-008`, `IFC-AUDIT-009`, `IFC-SCENARIO-001`, `IFC-REPORT-001`, `IFC-MODEL-001`  
**Related schema:** `gf-wordbench.run-summary/1.0`  
**Supersedes:** No earlier accepted ADR  
**Superseded by:** None  

---

## 1. Decision summary

GF Wordbench will represent source-file validation and scenario validation with two distinct result types:

```text
FileResult
ScenarioResult
```

They will:

- use the same canonical validation-status vocabulary;
- use the same canonical diagnostic-class vocabulary;
- use the same canonical error-kind vocabulary;
- expose a small common diagnostic interface;
- preserve raw evidence paths;
- remain separate collections inside `RunResult`;
- remain separate arrays inside `summary.json`;
- use subject-aware diff and reporting logic.

They will not:

- inherit from a large public base dataclass;
- be merged into one generic result containing many irrelevant nullable fields;
- represent scenarios as synthetic files;
- represent files as synthetic scenarios;
- pass undocumented dictionaries between framework components;
- force file compilation evidence and scenario execution evidence into one identical shape.

The central decision is:

> Share semantics, not storage shape.

---

## 2. Context

GF Wordbench validates two fundamentally different kinds of subjects.

### 2.1 Source files

A selected `.gf` file may produce:

- source identity;
- module identity;
- static-scan findings;
- source fingerprint;
- GF compilation evidence;
- `.gfo` evidence;
- dependency-related diagnostics;
- direct, downstream, or ambiguous failure classification.

The inherited GF Audit implementation already represents these outcomes with:

```text
FileResult
```

and composes:

```text
ScanCounts
SourceFingerprint
CompileSummary
```

### 2.2 Scenarios

A registered `.gfs` scenario may produce:

- scenario identity;
- required or optional policy;
- process command;
- explicit working directory;
- exit evidence;
- timeout or launch evidence;
- raw stdout and stderr;
- normalized bounded output;
- marker-completion evidence;
- scenario assertions;
- gold-comparison evidence;
- generated artifacts;
- direct, downstream, or ambiguous failure classification.

The final GF Wordbench architecture requires:

```text
ScenarioResult
```

as a first-class result.

### 2.3 Run aggregation

A complete run may contain both:

```text
file_results
scenario_results
```

The machine-readable run-summary schema already reserves independent root arrays for both subject kinds.

The architecture therefore needs a stable answer to these questions:

1. Should files and scenarios share one result class?
2. Should one inherit from the other?
3. Should both inherit from a public base class?
4. Which fields are truly common?
5. Which fields must remain subject-specific?
6. How should `RunResult`, diffing, reporting, and migration handle both?
7. How should causal classification work across subject kinds?
8. How can the model avoid duplicated or contradictory status fields?

---

## 3. Problem statement

A result model must preserve enough structure for:

```text
orchestration
classification
aggregation
serialization
previous-run comparison
human reports
AI-ready reports
release gates
automation
migration
```

A model that is too narrow loses evidence.

A model that is too generic creates:

- irrelevant fields;
- pervasive `None`;
- weak type checking;
- unclear ownership;
- ambiguous invariants;
- fragile serialization;
- report-specific parsing;
- accidental coupling between unrelated validation stages.

The result architecture must support shared reasoning without pretending that file compilation and scenario execution are the same operation.

---

## 4. Decision drivers

The decision is driven by the following requirements.

### 4.1 Type clarity

A developer must be able to determine from the type which evidence is available.

### 4.2 Evidence preservation

Raw compile and scenario evidence must remain accessible after normalization and classification.

### 4.3 Stable schemas

Persisted file and scenario results must be versionable independently within one run-summary schema.

### 4.4 Shared status semantics

`OK`, `FAIL`, `ERROR`, and `SKIPPED` must mean the same thing for every validation subject.

### 4.5 Subject-specific criteria

A file can fail because compilation failed.

A scenario can fail despite exit code zero because:

- a required marker is absent;
- a scenario assertion failed;
- normalized output differs from gold;
- a required artifact is absent.

### 4.6 Causal classification

Both subject kinds may be:

```text
ok
direct
downstream
ambiguous
skipped
```

but their blocker evidence differs.

### 4.7 Deterministic reporting

File order and scenario order follow different contracts.

### 4.8 Compatibility

The inherited `FileResult` and legacy summaries must remain migratable.

### 4.9 Minimal abstraction

The architecture must avoid a hierarchy that exists only to remove a few repeated fields.

---

## 5. Considered options

---

### Option A — One generic `ValidationResult`

Conceptual shape:

```python
@dataclass
class ValidationResult:
    subject_kind: str
    subject_id: str
    file_path: Path | None = None
    module_name: str | None = None
    scenario_id: str | None = None
    script_path: Path | None = None
    scan_counts: ScanCounts | None = None
    fingerprint: SourceFingerprint | None = None
    compile_summary: CompileSummary | None = None
    gold_path: Path | None = None
    gold_match: bool | None = None
    sections: list[SectionResult] | None = None
    ...
```

#### Advantages

- one collection;
- one serializer entrypoint;
- one apparent report loop;
- one apparent diff type.

#### Disadvantages

- most fields are invalid for most subjects;
- invariants depend on `subject_kind`;
- illegal states are easy to construct;
- every consumer must branch repeatedly;
- static typing provides little protection;
- schema evolution becomes tightly coupled;
- file and scenario ownership becomes unclear;
- generic result fields invite stage-specific additions;
- reports may begin inferring meaning from field presence.

#### Decision

Rejected.

---

### Option B — Scenarios represented as synthetic files

Conceptual approach:

```text
project/validation/scenarios/parse.gfs
    → FileResult
```

#### Advantages

- reuses existing file-result reports;
- requires fewer immediate code changes.

#### Disadvantages

- `.gfs` is not a selected `.gf` source module;
- scenarios do not have `ScanCounts`;
- scenarios do not have source-module fingerprints by the same contract;
- scenarios do not produce `CompileSummary`;
- scenario pass criteria include markers and gold;
- scenario ordering follows configuration, not path order;
- scenario blockers may be grammar entrypoints;
- file totals would become misleading;
- reports would confuse source defects with validation-script outcomes.

#### Decision

Rejected.

---

### Option C — One public base dataclass with subclasses

Conceptual shape:

```python
@dataclass
class BaseResult:
    status: Status
    diagnostic_class: DiagnosticClass
    error_kind: ErrorKind
    primary_message: str
    blocked_by: list[str]

@dataclass
class FileResult(BaseResult):
    ...

@dataclass
class ScenarioResult(BaseResult):
    ...
```

#### Advantages

- centralizes common fields;
- allows polymorphic report helpers;
- enforces some shared vocabulary.

#### Disadvantages

- dataclass inheritance complicates field ordering and defaults;
- base-class growth would affect every result type;
- persisted layouts could be coupled accidentally;
- file error information currently belongs to `CompileSummary`;
- duplicated top-level and nested error fields could drift;
- subclass construction and migration become more fragile;
- consumers may rely on the base class instead of subject-specific contracts;
- a future non-process result may not fit the hierarchy.

#### Decision

Rejected as the public storage model.

A small structural protocol or helper interface is allowed internally.

---

### Option D — Separate concrete result types with shared vocabularies and helpers

Conceptual approach:

```text
FileResult
ScenarioResult
```

with:

```text
shared enums
shared diagnostic coherence rules
shared serialization primitives
shared report helper functions
subject-aware diff identity
```

#### Advantages

- illegal cross-subject field combinations are minimized;
- evidence ownership remains clear;
- each schema is readable;
- file compatibility remains manageable;
- scenario evolution does not distort file results;
- reports can share helper functions without sharing storage shape;
- future result kinds can be introduced deliberately;
- common semantics stay centralized.

#### Disadvantages

- some fields or helper logic are repeated;
- aggregation must handle two collections;
- serializers need two explicit sections;
- tests must cover both types;
- generic reports require subject-aware adapters.

#### Decision

Accepted.

---

## 6. Decision

GF Wordbench will implement Option D.

The canonical runtime result model will contain:

```text
FileResult
ScenarioResult
RunResult
DiffEntry
```

The design will use composition and small shared interfaces rather than a public result inheritance hierarchy.

---

## 7. Shared semantic contract

`FileResult` and `ScenarioResult` share these semantic dimensions:

```text
subject identity
validation status
diagnostic class
error kind
primary message
blocker relationships
raw evidence references
produced artifact references
```

They do not need to store each dimension identically.

### 7.1 Shared validation status

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

Meaning:

| Status | Meaning |
|---|---|
| `OK` | the criterion executed and passed |
| `FAIL` | the criterion executed correctly but was not satisfied |
| `ERROR` | the criterion could not execute or be interpreted reliably |
| `SKIPPED` | the criterion was intentionally not executed |

### 7.2 Shared diagnostic class

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

`noise` is expected mainly for retained exclusions and should be uncommon in normal file or scenario results.

### 7.3 Shared error kind

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

### 7.4 Shared diagnostic access

Framework code that must handle either subject may use a structural protocol.

Conceptual form:

```python
from typing import Protocol

class DiagnosticResult(Protocol):
    status: Status
    diagnostic_class: DiagnosticClass
    blocked_by: list[str]

    @property
    def error_kind(self) -> ErrorKind:
        ...

    @property
    def primary_message(self) -> str:
        ...
```

This protocol:

- is an internal typing convenience;
- does not define persisted layout;
- does not own result construction;
- must not grow into a generic result container;
- does not replace concrete subject types.

---

## 8. `FileResult`

`FileResult` represents the validation outcome for one selected GF source file.

### 8.1 Canonical responsibility

It combines:

```text
source identity
scan evidence
fingerprint evidence
compile evidence
causal classification
```

### 8.2 Canonical conceptual model

```python
@dataclass(slots=True)
class FileResult:
    file_path: Path
    module_name: str

    status: Status
    diagnostic_class: DiagnosticClass
    is_direct: bool
    blocked_by: list[str]

    scan_counts: ScanCounts
    fingerprint: SourceFingerprint
    compile_summary: CompileSummary
    scan_log_path: Path | None

    artifacts: list[ArtifactRecord] = field(default_factory=list)

    @property
    def error_kind(self) -> ErrorKind:
        return self.compile_summary.error_kind

    @property
    def primary_message(self) -> str:
        return self.compile_summary.first_error
```

`artifacts` may remain absent from the initial runtime model when the manifest is the authoritative artifact inventory.

It must not be added redundantly without a defined ownership need.

### 8.3 File identity

Canonical runtime identity:

```text
resolved Path
```

Canonical persisted identity:

```text
project-relative POSIX path
```

Example:

```text
lib/src/french/GrammarFre.gf
```

### 8.4 File-specific evidence

`FileResult` owns or references:

- `ScanCounts`;
- `SourceFingerprint`;
- `CompileSummary`;
- scan log path;
- compile stdout path;
- compile stderr path;
- optional current-run `.gfo` references.

### 8.5 File error access

The canonical file error kind remains owned by:

```text
compile_summary.error_kind
```

The canonical file primary message remains owned by:

```text
compile_summary.first_error
```

A report or classifier may access convenience properties.

It must not create duplicated writable top-level fields with the same meaning.

### 8.6 `is_direct`

`is_direct` is retained for legacy compatibility.

Invariant:

```python
is_direct == (diagnostic_class == "direct")
```

It is not an independent source of truth.

A future major schema may remove it after all readers migrate.

---

## 9. `ScenarioResult`

`ScenarioResult` represents the validation outcome for one registered `.gfs` scenario.

### 9.1 Canonical responsibility

It combines:

```text
scenario identity
scenario policy
process evidence
marker evidence
normalized output
assertion evidence
gold comparison
produced artifacts
causal classification
```

### 9.2 Canonical conceptual model

```python
@dataclass(slots=True)
class ScenarioResult:
    scenario_id: str
    script_path: Path
    required: bool

    status: Status
    diagnostic_class: DiagnosticClass
    error_kind: ErrorKind
    primary_message: str
    blocked_by: list[str]

    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    execution_state: ExecutionState
    timed_out: bool
    duration_ms: int

    stdout_path: Path | None
    stderr_path: Path | None
    normalized_output_path: Path | None

    gold_path: Path | None
    gold_match: bool | None

    sections: list[ScenarioSectionResult]
    artifacts: list[ArtifactRecord]
```

The exact internal command type may be `list[str]` or `tuple[str, ...]`.

Persisted JSON uses an ordered array.

### 9.3 Scenario identity

Canonical identity:

```text
scenario_id
```

Example:

```text
parse
```

The script path supports evidence and configuration validation.

It does not replace the stable scenario ID.

### 9.4 Scenario-specific evidence

Scenario-specific fields include:

- required or optional policy;
- script path;
- ordered command;
- working directory;
- process evidence;
- normalized output path;
- gold path;
- gold-match result;
- marker or section results;
- scenario-produced artifacts.

These fields do not belong in `FileResult`.

### 9.5 Scenario error fields

`ScenarioResult` stores:

```text
error_kind
primary_message
```

directly because scenario failure may arise after a successful process exit.

Examples:

- required marker missing;
- assertion failed;
- gold mismatch;
- required scenario artifact missing.

No nested `CompileSummary` is appropriate.

### 9.6 Scenario blockers

A scenario may be downstream of:

- a failed entrypoint file;
- a failed PGF build;
- a failed required prerequisite scenario when explicitly declared;
- another structured release prerequisite.

Therefore `ScenarioResult` includes:

```text
blocked_by
```

Canonical file blockers use project-relative source paths.

Other blocker kinds require stable typed subject identifiers.

### 9.7 `is_direct`

`ScenarioResult` does not require a persisted `is_direct` compatibility field.

Directness is derived from:

```text
diagnostic_class == direct
```

Generic code must not require `is_direct` on every result type.

---

## 10. Why the shapes differ

The difference is intentional.

### 10.1 File validation is composite

A file result combines several independent observations:

```text
scan
fingerprint
compile
artifact verification
classification
```

Compilation evidence is naturally nested in:

```text
CompileSummary
```

### 10.2 Scenario validation is one criterion with several gates

A scenario result represents one configured scenario whose acceptance may depend on:

```text
process completion
marker completion
assertions
normalization
gold comparison
artifact checks
```

The process is one part of the scenario result, not the complete criterion.

### 10.3 Forced symmetry would be misleading

Making both types use an identical storage shape would either:

- flatten useful file composition;
- introduce a meaningless `CompileSummary` for scenarios;
- introduce scan and fingerprint fields for scenarios;
- hide scenario-specific acceptance gates.

The architecture therefore favors equivalent semantics over identical fields.

---

## 11. Process evidence

Both compiler and scenario runner use the shared process runner.

The shared process layer returns structured process evidence.

Conceptual runtime model:

```python
@dataclass(frozen=True, slots=True)
class ProcessResult:
    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    execution_state: ExecutionState
    duration_ms: int
    stdout_path: Path | None
    stderr_path: Path | None
    launch_error: str
```

The process runner does not assign validation status or diagnostic class.

### 11.1 File mapping

Compiler maps `ProcessResult` into:

```text
CompileSummary
```

and artifact checks.

### 11.2 Scenario mapping

Scenario runner maps `ProcessResult` plus marker, assertion, normalization, gold, and artifact evidence into:

```text
ScenarioResult
```

### 11.3 Persistence compatibility

The run-summary schema may flatten process fields inside `ScenarioResult`.

Runtime composition and persisted shape do not need to be identical.

Serialization remains centralized.

---

## 12. `RunResult`

`RunResult` is the aggregate result for one run.

### 12.1 Canonical conceptual model

```python
@dataclass(slots=True)
class RunResult:
    run_config: RunConfig
    run_paths: RunPaths

    started_at: datetime
    finished_at: datetime
    duration_ms: int

    gf_version: str
    overall_status: Status

    file_results: list[FileResult]
    scenario_results: list[ScenarioResult]
    diff_entries: list[DiffEntry]
    top_errors: list[TopError]

    totals: RunTotals
```

The final implementation may keep individual count fields during migration.

The authoritative values must remain derivable from result collections.

### 12.2 Separate collections

Required:

```text
file_results
scenario_results
```

Forbidden:

```text
all_results with mixed untyped dictionaries
```

A typed union may be created temporarily for reporting:

```python
ResultSubject = FileResult | ScenarioResult
```

It must not replace the separate canonical collections.

### 12.3 Ordering

Canonical ordering:

```text
file_results:
    normalized project-relative file_path

scenario_results:
    declared scenario execution order from project configuration
```

One collection must not impose its ordering rule on the other.

### 12.4 Counts

File totals and scenario totals remain separate.

Recommended totals:

```text
files_seen
files_included
files_excluded
files_ok
files_fail
files_error
files_skipped

scenarios_total
scenarios_required
scenarios_optional
scenarios_ok
scenarios_fail
scenarios_error
scenarios_skipped

direct_count
downstream_count
ambiguous_count
```

Causal counts may be global or split by subject kind, but their semantics must be documented.

### 12.5 Overall status

Recommended required-result precedence:

```text
ERROR > FAIL > OK
```

Rules:

- any required result with `ERROR` makes the run `ERROR`;
- otherwise any required result with `FAIL` makes the run `FAIL`;
- otherwise required results pass;
- optional scenario failures remain visible;
- optional scenario gate behavior is defined by validation mode and project policy;
- skipped required criteria must not become implicit success.

---

## 13. Classification

### 13.1 Shared semantics

Both subject kinds use:

```text
ok
direct
downstream
ambiguous
skipped
```

### 13.2 Separate entrypoints

Recommended public functions:

```python
classify_file_results(
    file_results: list[FileResult],
) -> list[FileResult]
```

```python
classify_scenario_results(
    scenario_results: list[ScenarioResult],
    file_results: list[FileResult],
) -> list[ScenarioResult]
```

Shared internal helpers may operate on the diagnostic protocol.

### 13.3 File classification

File classification may use:

- current file or module references;
- failed peer files;
- compile diagnostics;
- normalized dependency references.

### 13.4 Scenario classification

Scenario classification may use:

- local marker or assertion failures;
- local gold mismatch;
- failed entrypoint file;
- failed PGF prerequisite;
- failed declared scenario prerequisite;
- process or framework evidence.

### 13.5 No synthetic blockers

A blocker must identify a real structured subject.

Reports must not infer blockers from prose after classification.

---

## 14. Diff model

The inherited file-only diff identity is insufficient.

`DiffEntry` becomes subject-aware.

Canonical conceptual model:

```python
@dataclass(slots=True)
class DiffEntry:
    subject_kind: Literal["file", "scenario", "run"]
    subject_id: str
    previous_status: str
    current_status: str
    change_kind: ChangeKind
    message: str
```

### 14.1 File identity

```text
subject_kind = file
subject_id = project-relative file path
```

### 14.2 Scenario identity

```text
subject_kind = scenario
subject_id = scenario ID
```

### 14.3 Compatibility

Legacy:

```text
file_path
```

migrates to:

```text
subject_kind = file
subject_id = file_path
```

### 14.4 Change semantics

Canonical change kinds:

```text
unchanged
improved
regressed
new
removed
```

Diff logic compares status first.

Subject-specific detail may compare:

- file error kind;
- file first error;
- scenario gold match;
- scenario marker completion;
- scenario primary message.

---

## 15. Persisted run-summary structure

Canonical root:

```json
{
  "schema_id": "gf-wordbench.run-summary",
  "schema_version": "1.0",
  "metadata": {},
  "totals": {},
  "artifacts": {},
  "file_results": [],
  "scenario_results": [],
  "diff_entries": [],
  "top_errors": []
}
```

### 15.1 Separate arrays are mandatory

The serializer must not combine them into:

```json
{
  "results": []
}
```

within schema major `1`.

### 15.2 Missing scenario array in legacy data

A legacy summary without scenario results migrates to:

```json
"scenario_results": []
```

This means:

```text
no scenario data existed
```

It does not mean:

```text
all scenarios passed
```

### 15.3 File paths

Canonical file result paths are project-relative.

### 15.4 Scenario paths

Canonical scenario script and gold paths are project-relative.

Scenario raw outputs and artifacts are run-relative.

### 15.5 `blocked_by` schema alignment

The final scenario model requires `blocked_by`.

Schema handling:

- if run-summary `1.0` has not been published, include `blocked_by` in `ScenarioResult` before publication;
- if `1.0` has already been published without it, introduce it as an optional field with default `[]` in `1.1`;
- readers of the supported major must default missing `blocked_by` to `[]`;
- `diagnostic_class = downstream` requires a non-empty `blocked_by` after migration and classification.

This is a required coordinated follow-up to the current draft schema.

### 15.6 Enum alignment

The persisted diagnostic-class set must be:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Draft-only values such as:

```text
framework_error
script_error
```

must not be emitted as diagnostic classes.

Their meaning belongs in:

```text
status
error_kind
```

---

## 16. Result construction ownership

Canonical owner:

```text
app/audit/result_model.py
```

Expected public functions:

```python
build_file_result(...)
build_scenario_result(...)
build_run_result(...)
update_run_counts(...)
bucket_top_errors(...)
```

### 16.1 Stage responsibilities

Stages produce stage evidence:

```text
scanner        → ScanCounts + scan log
compiler       → CompileSummary + artifacts
scenario runner → scenario evidence
```

### 16.2 Builder responsibilities

Builders:

- validate field coherence;
- construct concrete result objects;
- assign safe defaults;
- normalize paths through shared helpers;
- preserve evidence references;
- avoid rerunning stages.

### 16.3 Forbidden behavior

A report writer must not construct missing `FileResult` or `ScenarioResult` objects.

The classifier must not reconstruct stage evidence from report prose.

---

## 17. Serialization ownership

Canonical model serialization is centralized.

Allowed approaches:

- model-owned `to_dict` and `from_dict`;
- one designated schema adapter;
- one report JSON serializer using documented adapters.

Forbidden:

- each report inventing its own result shape;
- generic `asdict` as the sole public schema contract;
- dynamic attributes serialized accidentally;
- absolute project paths in canonical portable fields;
- sets serialized without deterministic order.

Runtime dataclass layout and JSON schema may differ.

The adapter owns the mapping explicitly.

---

## 18. Reporting

Reports must preserve subject identity.

### 18.1 Human summary

Recommended sections:

```text
File Results
Scenario Results
Direct Failures
Downstream Failures
Ambiguous Failures
Artifacts
```

### 18.2 AI-ready report

The AI packet should distinguish:

```text
failing files
failing scenarios
scenario blockers
gold mismatches
raw evidence
```

### 18.3 Detail reports

File detail artifacts use file-safe keys.

Scenario detail artifacts use scenario-safe keys.

Duplicate namespaces must not collide.

Example:

```text
details/files/...
details/scenarios/...
```

or another `RunPaths`-owned layout.

### 18.4 No report-side execution

Reports do not:

- compile a file;
- rerun a scenario;
- compare gold independently;
- reclassify a failure;
- create missing raw evidence.

---

## 19. Top errors

Top-error aggregation may include both files and scenarios.

A top-error record should retain enough context to avoid merging unrelated failures incorrectly.

Recommended conceptual model:

```python
@dataclass(frozen=True, slots=True)
class TopError:
    error_kind: ErrorKind
    message: str
    count: int
    subject_kinds: tuple[str, ...]
```

At minimum, aggregation key uses:

```text
error_kind
normalized message
```

A scenario gold mismatch must not be merged with a compiler type error merely because their messages are similar.

Ordering remains deterministic:

```text
descending count
then error kind
then case-insensitive message
```

---

## 20. Artifacts

### 20.1 File artifacts

May include:

```text
.gfo
compile stdout
compile stderr
scan log
```

### 20.2 Scenario artifacts

May include:

```text
scenario stdout
scenario stderr
normalized output
generated text output
scenario-specific files
```

### 20.3 Manifest authority

`manifest.json` remains the authoritative run artifact inventory.

Result-level artifact lists may reference relevant entries.

They must not define a competing manifest schema.

---

## 21. Required and optional scenarios

`ScenarioResult.required` is mandatory.

It is a policy field, not a status.

Examples:

```text
required = true, status = OK
required = true, status = FAIL
required = false, status = FAIL
required = false, status = SKIPPED
```

Rules:

- required status is resolved from project configuration;
- UI state cannot silently downgrade a required scenario;
- reports show optional failures;
- release-gate behavior consumes `required`;
- `required = false` does not imply `SKIPPED`;
- `SKIPPED` does not imply optional.

`FileResult` has no corresponding field because file inclusion and checkpoint/release requirements are represented by selection and mode policy.

---

## 22. Status coherence

### 22.1 File success

```text
status = OK
diagnostic_class = ok
compile_summary.error_kind = OK
```

### 22.2 Scenario success

```text
status = OK
diagnostic_class = ok
error_kind = OK
gold_match = true or null
all required sections completed
```

### 22.3 File timeout

```text
status = ERROR
diagnostic_class = ambiguous unless a blocker is known
compile_summary.error_kind = TIMEOUT
```

### 22.4 Scenario timeout

```text
status = ERROR
diagnostic_class = ambiguous unless a blocker is known
error_kind = TIMEOUT
timed_out = true
```

### 22.5 Scenario gold mismatch

```text
status = FAIL
diagnostic_class = direct
error_kind = OTHER
gold_match = false
```

A dedicated future gold-mismatch error kind requires a schema and contract update.

### 22.6 Downstream scenario

```text
status = FAIL or ERROR
diagnostic_class = downstream
blocked_by = [stable blocker identity]
```

---

## 23. Exceptions versus result failures

Expected validation outcomes are structured results.

Examples:

- GF rejects source syntax;
- scenario marker is missing;
- normalized output differs from gold;
- required `.gfo` is absent;
- scenario times out.

Exceptions are reserved for:

- invalid configuration before a result can be constructed;
- impossible filesystem operation;
- corrupted internal state;
- violated model invariant;
- programming error.

When enough subject identity exists, the orchestrator should contain an expected stage failure as a `FileResult` or `ScenarioResult`.

---

## 24. Migration from inherited GF Audit

The inherited implementation contains:

```text
FileResult
RunResult.file_results
file-only DiffEntry
file-only aggregate counts
no ScenarioResult
```

Migration steps:

```text
1. preserve current FileResult behavior
2. align status and diagnostic enums
3. add ScenarioResult
4. add build_scenario_result
5. add RunResult.scenario_results with default []
6. add scenario counts
7. generalize DiffEntry identity
8. add scenario JSON serialization
9. add scenario report sections
10. add scenario top-error aggregation
11. add compatibility readers
12. update locks and schemas
13. add contract tests
```

### 24.1 Legacy file results

Legacy file fields remain readable.

Canonical writers emit project-relative paths and current enums.

### 24.2 Legacy run results

A missing scenario list becomes an empty list.

Legacy file-only totals remain migratable.

### 24.3 No synthetic migration

Migration must not invent scenario results from old logs.

Absence remains absence.

---

## 25. Compatibility rules

### 25.1 Compatible changes

Normally compatible:

- add an optional field with safe default;
- add a derived property;
- add a new optional scenario artifact;
- add a new scenario section metadata field;
- improve internal construction while preserving serialized meaning;
- add shared helper functions.

### 25.2 Breaking changes

Breaking unless migration exists:

- remove or rename a required field;
- change a field type;
- change path-base semantics;
- change status meaning;
- change diagnostic-class meaning;
- change array ordering;
- merge the two root arrays;
- move file error ownership out of `CompileSummary`;
- replace scenario ID with script path identity;
- remove raw evidence references;
- make an optional scenario failure silently gate every mode;
- change artifact ownership.

---

## 26. Rejected future shortcuts

The following shortcuts are prohibited unless this ADR is superseded.

```text
ScenarioResult = dict[str, Any]
FileResult = dict[str, Any]
scenario results appended to file_results
one generic results array in run-summary v1
report parsing to recover missing fields
dynamic attributes added by classifiers
gold comparison stored only as prose
process exit used as sole scenario status
scan counts copied into scenarios
scenario markers copied into files
```

---

## 27. Implementation boundaries

### `app/models.py`

Owns:

```text
FileResult
ScenarioResult
shared enums
optional diagnostic protocol
```

### `app/audit/result_model.py`

Owns:

```text
result construction
aggregate counts
coherence validation
```

### `app/audit/compiler.py`

Owns:

```text
CompileSummary evidence
```

### `app/audit/scenario_runner.py`

Owns:

```text
ScenarioResult stage evidence
```

### `app/audit/classifier.py`

Owns:

```text
diagnostic_class
blocked_by
```

### `app/audit/diff.py`

Owns:

```text
subject-aware DiffEntry
```

### `app/reports/report_json.py`

Owns:

```text
canonical serialized arrays
```

### Other reports

Consume results without mutating or rerunning stages.

---

## 28. Testing strategy

### 28.1 File-result tests

```text
test_file_result_valid_success
test_file_result_valid_failure
test_file_result_timeout_error
test_file_result_scan_hits_do_not_force_compile_failure
test_file_result_is_direct_is_derived
test_file_result_paths_serialize_portably
test_file_result_round_trip
```

### 28.2 Scenario-result tests

```text
test_scenario_result_valid_success
test_scenario_result_nonzero_exit_failure
test_scenario_result_zero_exit_missing_marker_failure
test_scenario_result_gold_match
test_scenario_result_gold_mismatch
test_scenario_result_without_gold_uses_null
test_scenario_result_timeout_error
test_scenario_result_required_flag_preserved
test_scenario_result_blocked_by_failed_entrypoint
test_scenario_result_paths_serialize_portably
test_scenario_result_round_trip
```

### 28.3 Run-result tests

```text
test_run_result_contains_separate_collections
test_run_counts_files_and_scenarios_separately
test_required_scenario_fail_affects_overall_status
test_optional_scenario_fail_follows_gate_policy
test_file_failure_not_overwritten_by_scenario_result
test_scenario_order_follows_configuration
test_file_order_follows_normalized_path
```

### 28.4 Diff tests

```text
test_file_diff_identity
test_scenario_diff_identity
test_legacy_file_path_diff_migration
test_removed_scenario
test_new_scenario
test_scenario_regression
```

### 28.5 Schema tests

```text
test_run_summary_requires_file_results
test_run_summary_requires_scenario_results
test_missing_legacy_scenario_results_migrates_to_empty
test_scenario_blocked_by_default
test_unknown_required_field_rejected
test_enum_alignment
test_round_trip_preserves_evidence_paths
```

### 28.6 Contract tests

```text
test_reports_do_not_import_compiler
test_reports_do_not_import_scenario_runner
test_result_builders_do_not_execute_stages
test_normal_run_does_not_modify_gold
test_models_have_no_dynamic_fields
test_file_and_scenario_status_vocabularies_match
```

---

## 29. Acceptance criteria

This decision is fully implemented when:

```text
[ ] ScenarioResult exists as a typed shared model
[ ] FileResult remains a distinct typed model
[ ] no generic nullable result replaces them
[ ] shared enums are centralized
[ ] common diagnostic access is available
[ ] FileResult error ownership remains coherent
[ ] ScenarioResult records marker and gold evidence
[ ] ScenarioResult records blocked_by
[ ] RunResult stores separate result lists
[ ] file and scenario totals are distinct
[ ] overall status applies required-result policy
[ ] DiffEntry is subject-aware
[ ] summary.json contains both arrays
[ ] legacy summaries migrate safely
[ ] reports distinguish subject kinds
[ ] raw evidence paths survive round trips
[ ] scenario order is deterministic
[ ] file order is deterministic
[ ] report writers do not rerun stages
[ ] normal runs do not update gold
[ ] unit, schema, migration and contract tests pass
[ ] relevant lock documents are harmonized
```

---

## 30. Consequences

### 30.1 Positive consequences

- concrete types reflect actual validation subjects;
- evidence ownership is explicit;
- reports are less likely to confuse files and scenarios;
- scenario validation becomes first-class;
- schemas remain reviewable;
- file-only legacy migration remains practical;
- new result kinds can be added deliberately;
- status semantics stay centralized;
- illegal states are reduced;
- downstream scenario blockers can be represented explicitly.

### 30.2 Negative consequences

- result aggregation becomes more explicit;
- serializers require two result adapters;
- report code requires subject-aware helpers;
- classification has two public entrypoints;
- more tests are required;
- some shared fields appear in both conceptual models.

### 30.3 Neutral consequences

- `RunResult` grows;
- run-summary schema includes an empty scenario array before scenarios exist;
- compatibility code remains necessary during migration;
- file and scenario counts cannot be represented by one undifferentiated total without losing meaning.

---

## 31. Required coordinated updates

Acceptance of this ADR requires alignment of:

```text
app/models.py
app/audit/result_model.py
app/audit/audit_core.py
app/audit/scenario_runner.py
app/audit/classifier.py
app/audit/diff.py
app/reports/report_json.py
app/reports/report_md.py
app/reports/report_ai_ready.py
app/reports/report_logs.py
app/reports/report_details.py
tests/
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/reference/SCHEMA_INDEX.md
```

In particular, draft schema or lock values that still contain:

```text
framework_error
script_error
```

as diagnostic classes must be harmonized with the canonical model.

---

## 32. Decision review triggers

Review this ADR when:

- a third first-class validation subject is added;
- the run-summary result arrays are reconsidered;
- a public result inheritance hierarchy is proposed;
- `CompileSummary` ownership changes;
- scenario blockers require typed cross-subject references;
- `is_direct` is removed;
- process evidence is embedded differently;
- status or diagnostic enums change;
- result serialization moves to another owner;
- project releases require a new result subject.

A review does not imply reversal.

A replacement decision must supersede this ADR explicitly.

---

## 33. Cross-references

| Topic | Document |
|---|---|
| Shared terminology | `docs/GLOSSARY.md` |
| Framework contracts | `docs/INTERFILE_CONTRACT_LOCK.md` |
| Persisted schemas | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Code ownership | `docs/development/CODEBASE_GUIDE.md` |
| Error classification | `docs/diagnostics/ERROR_CLASSIFICATION.md` |
| GF compilation | `docs/gf/GF_COMPILATION.md` |
| Scenario validation | `docs/validation/SCENARIO_VALIDATION.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Summary JSON | `docs/reports/SUMMARY_JSON_REFERENCE.md` |
| Data model | `docs/architecture/DATA_MODEL.md` |
| Artifact model | `docs/architecture/ARTIFACT_MODEL.md` |
| Status values | `docs/reference/STATUS_VALUES.md` |
| Diagnostic kinds | `docs/reference/DIAGNOSTIC_KINDS.md` |
| Schema index | `docs/reference/SCHEMA_INDEX.md` |
| ADR index | `docs/decisions/ADR_INDEX.md` |

---

## 34. Final decision statement

> GF Wordbench will model file validation and scenario validation as separate concrete result types.

> They will share status and diagnostic semantics through centralized vocabularies and small helper interfaces, not through one generic nullable storage class.

> `RunResult` and `summary.json` will preserve both subject kinds explicitly.

This separation is required to keep evidence precise, schemas stable, classification honest, and future framework changes reviewable.
