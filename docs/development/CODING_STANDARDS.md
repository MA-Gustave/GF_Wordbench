# GF Wordbench — Coding Standards

**Document ID:** `GF-WB-DEV-CODING-STANDARDS`  
**Status:** Normative development specification  
**Applies to:** Framework source, tests, migrations, scripts and maintained developer tooling  
**Primary language:** Python  
**Owner:** GF Wordbench maintainers  
**Tool configuration authority:** `pyproject.toml`  
**Architectural authority:** `docs/architecture/`  
**Interfile authority:** `docs/INTERFILE_CONTRACT_LOCK.md`  
**External-tool authority:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Persisted-format authority:** `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Purpose

This document defines the coding standards for GF Wordbench.

The standards keep the codebase:

- readable;
- typed;
- deterministic;
- testable;
- cross-platform;
- secure around external processes;
- explicit at component boundaries;
- compatible with persisted formats;
- faithful to raw evidence;
- resistant to architectural drift.

GF Wordbench is a validation system, not a collection of unrelated scripts.

A locally correct change is incomplete when it:

- breaks a provider/consumer contract;
- changes a persisted format without migration;
- changes a GF command without integration review;
- weakens raw-evidence preservation;
- introduces different CLI and GUI semantics;
- makes ordering dependent on the filesystem;
- hides a failure behind a fallback.

The core rule is:

> Code may be concise, but ownership, contracts, paths, errors, ordering and persisted behavior must remain explicit.

---

## 2. Scope

This specification governs:

- Python source under `app/`;
- tests under `tests/`;
- CLI and GUI entrypoints;
- audit orchestration;
- GF process integration;
- scanners and compilers;
- scenario execution;
- normalization;
- diagnostic parsing;
- failure classification;
- result construction;
- report writers;
- state and configuration handling;
- filesystem utilities;
- process utilities;
- schema migrations;
- committed developer scripts;
- public and interfile APIs;
- comments and docstrings defining behavior.

It does not govern:

- style inside active-project `.gf` modules;
- linguistic naming conventions;
- generated run artifacts;
- third-party source;
- temporary uncommitted experiments;
- general documentation prose outside code examples.

Project-specific GF conventions belong under `project/docs/`.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless an explicit exception is documented.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **PUBLIC API**: symbol or behavior consumed outside its defining module.
- **INTERFILE CONTRACT**: dependency between provider and consumer files.
- **OWNER**: component responsible for one behavior, path, schema or artifact.
- **BOUNDARY TYPE**: typed request or result crossing a component boundary.
- **RAW EVIDENCE**: unmodified captured source or process evidence.
- **PERSISTED FORMAT**: data surviving beyond one in-memory operation.
- **COMPATIBLE CHANGE**: change preserving supported consumers.
- **BREAKING CHANGE**: change requiring coordinated migration.
- **SIDE EFFECT**: filesystem, process, environment, state, logging or GUI mutation.
- **SENTINEL**: explicit special value distinguishing states such as missing and null.

---

## 4. Authority hierarchy

When documents overlap, use this precedence:

1. contract-lock files;
2. architectural decision records;
3. persisted-schema definitions;
4. subsystem architecture documents;
5. this coding standard;
6. local comments.

A local comment MUST NOT override a normative contract.

`pyproject.toml` is authoritative for:

- supported Python versions;
- package metadata;
- dependencies;
- optional dependency groups;
- build configuration;
- formatter configuration;
- linter configuration;
- type-checker configuration;
- test-runner configuration;
- executable entrypoints.

This document defines required engineering behavior without inventing tool versions not declared by the repository.

---

## 5. Core engineering principles

Code MUST favor:

```text
explicit data
explicit ownership
explicit paths
explicit side effects
explicit failures
explicit versions
explicit ordering
```

over:

```text
hidden global state
implicit current directories
stringly typed contracts
ad hoc dictionaries
silent fallback
duplicate path construction
duplicate parsing
unversioned persistence
```

Correctness and auditability take priority over cleverness.

---

## 6. Balanced simplicity

Simplicity means the smallest design that preserves all real contracts.

It does not mean:

- combining unrelated responsibilities;
- returning untyped dictionaries;
- swallowing exceptions;
- rebuilding paths in every caller;
- using one status for unrelated failure types;
- bypassing migrations;
- omitting tests;
- duplicating code instead of naming an owner.

A new abstraction is justified when it provides:

- one authoritative owner;
- one typed boundary;
- removal of repeated contract logic;
- isolation of side effects;
- deterministic behavior;
- testability;
- platform adaptation;
- compatibility handling.

Do not add an abstraction merely to reduce line count.

---

## 7. Module responsibilities

Each module MUST have one primary stable responsibility.

Good responsibility questions:

```text
How is run configuration constructed?
How are source files selected?
How is GF invoked?
How are diagnostics parsed?
How are failures classified?
How is summary.json written?
```

A module SHOULD NOT mix:

- process execution and reporting;
- GUI widgets and validation semantics;
- scanning and compilation;
- configuration loading and audit execution;
- artifact verification and diagnostic parsing;
- state persistence and project identity.

Refactor when one file becomes the owner of unrelated lifecycle phases.

---

## 8. Canonical dependency direction

Conceptual direction:

```text
CLI / GUI
    → bootstrap and configuration
    → audit orchestration
    → audit stages
    → process/filesystem adapters
    → shared models
    → reports consume completed results
```

Prohibited examples:

```text
reports → compiler
reports → scanner
reports → scenario runner
models → GUI
compiler → report writer
scanner → compiler
classifier → process launcher
state → project identity owner
```

A dependency cycle requires architectural review.

---

## 9. Public surfaces

Every public module SHOULD expose a small deliberate API.

Use:

- explicit imports;
- typed public functions/classes;
- clear docstrings;
- `__all__` only for intentional package re-exports;
- leading underscores for private helpers.

A package `__init__.py` MUST NOT become an unreviewed catch-all export layer.

A public symbol consumed by another file becomes an interfile contract.

---

## 10. Import standards

Imports MUST be:

- explicit;
- free of wildcard imports;
- deterministic;
- at module scope unless delayed import is justified;
- compatible with optional-dependency boundaries.

Prohibited:

```python
from module import *
```

Conceptual grouping:

```python
from __future__ import annotations

import json
from pathlib import Path

from third_party import dependency

from app.models import RunConfig
```

The configured formatter owns exact whitespace.

---

## 11. Import-time side effects

Importing a module MUST NOT:

- launch GF;
- create run directories;
- read the active project unexpectedly;
- write files;
- mutate environment variables;
- open GUI windows;
- scan a source tree;
- change application state.

Permitted import-time content includes:

- constants;
- enums;
- immutable pattern definitions;
- functions;
- classes.

---

## 12. Naming conventions

Use conventional Python naming:

```text
module_name.py
ClassName
function_name
variable_name
CONSTANT_NAME
_private_helper
```

Names MUST express domain meaning.

Preferred:

```python
build_run_config
parse_gf_diagnostics
normalized_output_path
required_scenarios
```

Avoid:

```python
do_stuff
data2
thing
temp_final
helper_manager
```

---

## 13. Boolean names

Boolean names should express a proposition:

```python
timed_out
gold_match
is_required
has_fatal_diagnostic
should_compile
```

Avoid double negatives:

```python
not_disabled
dont_skip
no_no_compile
```

Legacy negative CLI flags may be accepted at the boundary, but resolved internal models should use clear semantics.

---

## 14. Collection names

Plural names represent collections:

```python
file_results
scenario_ids
diagnostics
artifact_paths
```

Singular names represent one object.

Do not call a list of results `result`.

---

## 15. Unit suffixes

Numeric names MUST include units where ambiguity is possible:

```python
timeout_seconds
duration_ms
size_bytes
maximum_lines
```

Avoid ambiguous names such as `duration` or `size` in public boundaries.

---

## 16. Path names

Use names that identify the path role:

```python
project_root
source_root
run_dir
summary_json_path
scenario_path
gold_path
```

`*_dir` represents a directory.

`*_path` represents a file or generic path.

---

## 17. Formatting and source files

All committed Python code MUST pass the configured formatter.

Source files MUST use:

```text
UTF-8
final newline
no trailing whitespace
spaces for indentation
```

Tests may intentionally contain alternate encodings/newlines only when validating those behaviors.

Do not create module-specific formatting exceptions for personal style.

---

## 18. Line complexity

The configured formatter/linter owns the exact line-length limit.

Regardless of the number:

- avoid deeply nested expressions;
- split arguments logically;
- introduce meaningful intermediate values;
- do not hide business rules inside one expression;
- preserve exact user-visible strings when required.

---

## 19. Type annotations

All new or materially changed public functions, methods and classes MUST be typed.

Complete typing is mandatory at boundaries such as:

- configuration builders;
- process requests/results;
- scanner results;
- compiler results;
- scenario results;
- diagnostic parser requests/results;
- report writers;
- persistence readers/writers;
- migrations.

Private helpers SHOULD be typed when nontrivial.

---

## 20. Type-checking policy

Code MUST pass the configured type checker.

A local issue MUST NOT be solved by weakening project-wide strictness.

Suppressions require:

- the narrowest location;
- the specific error code when supported;
- a reason when not self-evident;
- an upstream compatibility reference when applicable.

Avoid unrestricted:

```python
# type: ignore
```

---

## 21. Avoid `Any`

`Any` disables contract checking.

Use it only at true untyped boundaries such as:

- raw legacy data before validation;
- third-party APIs without usable types;
- narrow compatibility adapters.

Convert it immediately to validated domain types.

Preferred:

```python
raw: object = load_json(path)
summary = parse_run_summary(raw)
```

Do not propagate `Any` through core models.

---

## 22. `object` versus `Any`

Use `object` when a function accepts an unknown value and validates it.

Use `Any` only when type checking must intentionally be bypassed.

Coercion helpers should normally accept `object`.

---

## 23. Closed vocabularies

Use enums or literal types for stable closed vocabularies:

```text
validation status
execution state
diagnostic class
error kind
change kind
validation mode
```

Canonical values must agree with schema/reference documents.

Do not define competing string sets in multiple modules.

---

## 24. Enum persistence

When enums are persisted:

- values are explicit stable strings;
- Python member names are not assumed to be schema values;
- unknown values are rejected or migrated;
- renaming a member must not silently change persisted output;
- enum order is not business logic unless documented.

---

## 25. Domain models

Use typed dataclasses or equivalent models for stable structured data.

Examples:

```text
AppConfig
RunConfig
RunPaths
ProcessRequest
ProcessResult
FileResult
ScenarioResult
DiagnosticRecord
DiffEntry
ArtifactRecord
```

Models should distinguish:

- required fields;
- optional fields;
- derived fields;
- persisted fields;
- internal-only fields.

---

## 26. Model invariants

Enforce invariants in one owner:

- constructor;
- factory;
- validator;
- schema parser.

Examples:

```text
timeout_seconds > 0
run paths remain under run_dir
scenario ID is valid
status is canonical
execution-state booleans agree
```

Do not rely on every consumer remembering the invariant.

---

## 27. Mutability

Configuration, requests and finalized results SHOULD be immutable or treated as immutable.

Mutable staged assembly is allowed only when:

- one owner performs it;
- the mutation phase is bounded;
- consumers do not observe partial state;
- finalization is explicit.

Avoid passing one mutable dictionary through the whole pipeline.

---

## 28. Optional values

Use `None` only when “no value” is part of the domain.

Distinguish where the schema requires:

```text
missing
null
empty
skipped
unknown
```

Do not silently convert every invalid value to `None`.

---

## 29. Sentinels

Use a private sentinel when `None` is meaningful:

```python
_MISSING = object()
```

Do not serialize the sentinel directly.

---

## 30. Dictionaries

Use dictionaries for genuinely dynamic mappings.

A stable `dict[str, object]` crossing files is a contract and SHOULD become:

- a typed model;
- validated input;
- documented keys;
- tested serialization.

Do not use dictionaries to avoid defining domain models.

---

## 31. Return values

Avoid large positional tuples:

```python
return status, path, error, detail, duration
```

Prefer a named result model.

Tuples remain appropriate for small local fixed structures whose positions are obvious.

---

## 32. Function responsibility

A function should perform one coherent operation.

Refactor when a function combines:

```text
configuration resolution
process launch
diagnostic parsing
classification
report writing
```

Length alone is not the criterion.

Inputs, outputs, side effects and failure modes must remain understandable.

---

## 33. Function signatures

Prefer:

- keyword-only arguments for similar types;
- request models for large calls;
- explicit defaults;
- no mutable defaults;
- no hidden dependency on current directory/global state.

Example:

```python
def run_process(
    request: ProcessRequest,
    *,
    cancellation: CancellationToken | None = None,
) -> ProcessResult:
    ...
```

---

## 34. Mutable defaults

Prohibited:

```python
def collect(items: list[str] = []) -> list[str]:
    ...
```

Use `None` and create a fresh collection.

---

## 35. Keyword-only parameters

Use keyword-only parameters when:

- adjacent values share a type;
- booleans are unclear;
- units differ;
- compatibility may add options;
- the function is a public boundary.

Avoid:

```python
run(path, 30, True, False, 10)
```

---

## 36. Pure logic and side effects

Separate pure logic from side-effect adapters.

Examples:

```text
build command        → pure
launch command       → side effect
parse diagnostics    → pure over captured text
classify results     → pure over structured evidence
write summary        → side effect
```

Do not write files inside classification logic.

---

## 37. Dependency injection

Inject external dependencies when testing benefits:

- clock;
- process adapter;
- filesystem reader;
- environment source;
- cancellation token;
- run-ID generator;
- capability probe.

Keep injection direct and simple.

Do not add a general service container without demonstrated need.

---

## 38. Global state

Mutable global state is prohibited in core validation logic.

Permitted globals:

- immutable constants;
- enum classes;
- immutable pattern registries;
- stateless logger configuration.

The active project MUST NOT be an implicit global selected by the GUI.

---

## 39. Configuration ownership

Defaults have one owner.

CLI and GUI MUST use the same configuration builder.

Prohibited:

- CLI reconstructing `RunConfig`;
- GUI mutating completed configuration;
- stage modules reading raw CLI arguments;
- reports reading GUI widgets;
- modules inventing alternate timeout defaults.

Resolved configuration must support non-interactive execution.

---

## 40. Project configuration versus state

`project/project.toml` owns project facts.

Application state owns local convenience values.

State MUST NOT define:

- language identity;
- module suffix;
- required scenarios;
- release targets;
- validation policy.

Invalid state falls back safely.

---

## 41. Path handling

Use `pathlib.Path` or the canonical typed path abstraction.

Convert external strings to paths at boundaries.

Do not pass path strings through core code without reason.

---

## 42. Relative-path bases

Every relative path has one explicit base:

```text
project-relative
run-relative
repository-relative
working-directory-relative
```

Never resolve against an accidental current directory.

---

## 43. Path ownership

Owned paths are built by their owner:

- `RunPaths` owns run artifact paths;
- project configuration owns project asset paths;
- state manager owns the state path;
- each report writer receives its output path.

Consumers MUST NOT repeat canonical filenames.

Avoid:

```python
summary_path = run_dir / "summary.json"
```

outside the path owner.

Use:

```python
summary_path = run_paths.summary_json_path
```

---

## 44. Path containment

Before writing or deleting:

- resolve the approved root;
- validate containment;
- apply symlink policy;
- reject traversal;
- fail on ambiguity.

A string-prefix check is not sufficient:

```python
str(path).startswith(str(root))
```

---

## 45. Cross-platform paths

Tests MUST include:

- Windows drive paths;
- POSIX paths;
- paths with spaces;
- Unicode segments;
- mixed separators in external text;
- relative paths;
- missing paths where allowed.

Filesystem code MUST NOT hardcode path separators.

---

## 46. Safe artifact keys

When a filename represents a path/ID, use the canonical safe-key owner.

Safe keys must be:

- deterministic;
- collision-aware;
- traversal-safe;
- platform-safe;
- tested.

The safe key does not replace the canonical source identity.

---

## 47. File reads

Text readers must:

- use explicit encoding;
- distinguish missing/unreadable/empty;
- bound large reads where relevant;
- preserve decoding failures;
- raise or return documented errors.

Do not catch all exceptions and return empty text.

---

## 48. File writes

Writers must:

- write only owned paths;
- use explicit encoding/newline policy;
- create parents through designated utilities;
- distinguish append and replacement;
- close before hashing;
- report failure.

---

## 49. Atomic writes

State, canonical JSON, manifests, migrations and gold updates MUST use atomic replacement where specified:

```text
write sibling temporary
flush
close
validate
replace
```

A failed write MUST NOT destroy the last valid file.

---

## 50. Deletion

Deletion functions must be narrow.

Before deletion:

- validate root containment;
- confirm object type;
- apply symlink policy;
- avoid unsafe following;
- report failure.

Never call recursive deletion on an unvalidated user path.

---

## 51. External process ownership

Only the process owner launches external tools.

Normal GF invocation MUST use:

- explicit executable;
- ordered argument list;
- `shell=False`;
- explicit working directory;
- finite timeout;
- separate stdout/stderr capture;
- explicit encoding;
- owned process-tree cleanup.

Reports, GUI widgets and classifiers MUST NOT launch GF directly.

---

## 52. Command construction

Commands are structured data.

Preferred:

```python
args = [str(executable), "-path", gf_path, target]
```

Do not concatenate untrusted project text into shell commands.

Rendered commands are derived human output, not execution authority.

---

## 53. Process result type

Process execution returns a typed result.

It must distinguish:

```text
completed
timed_out
cancelled
launch_failed
```

Do not return only:

```python
tuple[int, str, str]
```

when timeout, launch and capture facts matter.

---

## 54. Raw process evidence

Capture stdout and stderr separately before parsing/normalization.

Code MUST NOT:

- discard stderr;
- merge streams before raw capture;
- rewrite raw files;
- parse only reports;
- remove unknown diagnostics;
- replace raw evidence with normalized output.

Derived artifacts reference raw evidence.

---

## 55. Output limits

Honor bounded output policy.

When truncated:

- record truncation;
- continue safe draining;
- avoid absence claims;
- prevent release success from incomplete evidence;
- preserve the retained raw prefix.

---

## 56. Timeouts

Every external process has a finite timeout.

Timeouts come from central configuration.

Use monotonic time for deadlines.

Continuous output does not extend a deadline silently.

Timeout maps to:

```text
validation status = ERROR
error kind = TIMEOUT
```

---

## 57. Cancellation

CLI interrupt, GUI cancel and audit cancel use one shared contract.

Cancellation is an execution state, not a validation status.

Do not introduce `CANCELLED` into the canonical status enum.

---

## 58. Process cleanup

Terminate only the owned process tree.

Prohibited:

- global kill by executable name;
- indefinite cleanup waits;
- trusting artifacts from timeout/cancellation;
- hashing open capture files.

Termination failure remains visible.

---

## 59. Error-handling philosophy

Errors must be:

- classified at the correct layer;
- explicit;
- preserved with context;
- recovered only when safe;
- never converted silently to success.

Independent work may continue under policy, but original failure remains unchanged.

---

## 60. Exceptions versus results

Use structured results for expected validation outcomes.

Examples:

```text
GF type failure → FAIL result
gold mismatch → FAIL result
timeout → ERROR result
missing configuration → configuration exception or ERROR
disk write failure → IO ERROR at boundary
```

Do not raise merely because the grammar under validation is invalid.

---

## 61. Exception hierarchy

A small dedicated hierarchy MAY exist:

```text
ConfigurationError
ProcessLaunchError
ArtifactError
SchemaError
MigrationError
ReportError
```

Create a class only when handling differs meaningfully.

---

## 62. Catching exceptions

Catch only when the layer can:

- add context;
- convert to a structured result;
- clean up owned resources;
- retry under explicit policy;
- translate a third-party exception.

Avoid:

```python
except Exception:
    return None
```

Top-level containment may catch broadly but must preserve evidence and report an internal error.

---

## 63. Exception chaining

Preserve causes:

```python
raise ConfigurationError(message) from exc
```

Use `from None` only when the original cause has no diagnostic value.

---

## 64. Error messages

Messages should identify:

```text
operation
affected identity/path
what failed
expected condition
actionable context when known
```

Avoid vague text such as “Something went wrong.”

Never expose secrets.

---

## 65. Canonical validation status

Use exactly:

```text
OK
FAIL
ERROR
SKIPPED
```

Do not introduce competing statuses such as:

```text
SUCCESS
FAILED
CANCELLED
UNKNOWN
```

Execution state and diagnostic class are separate.

---

## 66. Canonical error kind

Use the shared owner for:

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

Do not compare ad hoc lowercase strings.

---

## 67. Canonical diagnostic class

Only the classifier assigns:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

The parser does not assign causal ownership from text.

The process layer does not assign it from exit code.

---

## 68. Diagnostic patterns

Patterns must be:

- versioned;
- fixture-backed;
- operation-scoped;
- false-positive-tested;
- deterministic;
- bounded.

Unknown evidence is retained.

No report writer may maintain a competing regex set.

---

## 69. Classification functions

Classifiers consume structured evidence.

They MUST NOT:

- launch tools;
- read GUI state;
- write reports;
- modify raw logs;
- parse human summaries;
- invent dependencies.

Return `ambiguous` when evidence is insufficient.

---

## 70. Static scanner

Scanning is heuristic, not native GF authority.

Scanner code must:

- use stable rule IDs;
- preserve locations;
- handle comments/strings safely;
- remain bounded;
- avoid rewriting sources;
- avoid mapping findings automatically to GF type/syntax errors.

---

## 71. Scenario execution

The scenario runner owns:

- process request;
- raw capture;
- marker validation;
- normalization call;
- gold comparison call;
- scenario result.

It MUST NOT:

- infer requiredness from directory enumeration;
- rewrite gold during normal audit;
- ignore missing markers;
- allow unauthorized shell escapes.

---

## 72. Central normalization

All comparison normalization belongs to the normalizer.

Do not normalize independently in:

- runner;
- comparator;
- reports;
- GUI.

Normalization must be versioned, deterministic and idempotent.

Raw evidence remains unchanged.

---

## 73. Gold handling

Normal validation is read-only for gold files.

Gold updates are explicit and must:

- produce a diff;
- validate identities/versions;
- write atomically;
- preserve old gold on failure;
- never occur as a hidden normal-audit option.

---

## 74. Artifact ownership

Every persisted artifact has one owner.

Examples:

- compiler owns compile evidence;
- scenario runner owns scenario evidence;
- JSON writer owns `summary.json`;
- manifest writer owns `manifest.json`;
- state manager owns state.

The manifest catalogs artifacts; it does not own their bytes.

---

## 75. Artifact finalization

Before finalization:

- all writers close;
- required artifacts are checked;
- paths use schema-required bases;
- hashes use final bytes;
- manifest is written after catalogued files;
- manifest excludes itself.

Do not hash open files.

---

## 76. Report writers

Reports consume completed structured results.

They MUST NOT:

- rerun GF;
- rescan source;
- reconstruct missing evidence;
- parse `summary.md` to build JSON;
- change statuses/classes;
- normalize raw output independently.

Each format has one writer.

---

## 77. JSON writers

Canonical JSON writers must:

- emit schema ID/version;
- serialize stable enum values;
- use deterministic array ordering;
- use UTF-8;
- reject NaN/infinity;
- distinguish missing/null per schema;
- validate output;
- write atomically where required.

JSON object key order is not semantic.

---

## 78. JSON readers

Readers must:

- validate required fields;
- handle documented optional unknown fields;
- reject unknown enum values unless migrated;
- distinguish malformed/unsupported/legacy;
- avoid truthiness coercion;
- produce current typed models.

Legacy readers remain isolated from canonical writers.

---

## 79. TOML ownership

`project/project.toml` is project-owned.

Normal validation MUST NOT rewrite it.

Initialization/migration may write it explicitly.

Readers depend on semantic fields, not incidental formatting or key order.

---

## 80. Migrations

Breaking persisted changes require:

- source detection;
- target version;
- deterministic conversion;
- validation;
- non-destructive/atomic write;
- tests;
- migration note;
- compatibility review.

Do not silently discard meaningful unknown data.

---

## 81. Backward compatibility

Compatibility code should be:

- narrow;
- documented;
- tested;
- visibly legacy;
- separate from canonical writers;
- assigned deprecation policy.

Canonical writers emit only current forms.

---

## 82. Deterministic ordering

Every visible collection has a defined order.

Examples:

```text
file results → normalized path
scenario results → configuration order
entrypoints → declared order
checkpoints → declared order
manifest entries → normalized artifact path
top errors → count then message
```

Never rely on filesystem enumeration.

Do not alphabetically sort semantically ordered configuration.

---

## 83. Time

Use timezone-aware UTC for persisted timestamps unless schema says otherwise.

Use monotonic clocks for durations/deadlines.

Do not calculate elapsed time from wall-clock timestamps.

Inject clocks in deterministic tests.

---

## 84. Run IDs

Run-ID construction has one owner.

IDs must be:

- filesystem-safe;
- timezone-defined;
- collision-aware;
- deterministic with injected time/collision state.

CLI, GUI and tests must not build IDs independently.

---

## 85. Hashing

Use the contract-defined algorithm.

Manifest hashing uses SHA-256.

Hash final bytes, stream large files and emit lowercase hexadecimal where specified.

Never use Python `hash()` for persisted identity.

---

## 86. Logging

Logs record events; they do not replace results.

Include useful context:

```text
run ID
operation
target
stage
status
duration
artifact path
```

Structured outputs remain authoritative.

---

## 87. Log levels

Use levels consistently:

- debug: internal decision detail;
- info: normal progress;
- warning: recoverable risk;
- error: operation failed;
- critical: integrity/cleanup failure.

Do not log successful expected flow as an error.

---

## 88. Sensitive data

Logs/reports/state/manifests MUST NOT contain:

- passwords;
- tokens;
- private keys;
- authentication cookies;
- complete environment dumps;
- secret arguments.

Paths may be redacted in exports, but a redacted copy is derived evidence, not raw evidence.

---

## 89. Comments

Comments explain:

- why;
- invariants;
- compatibility;
- security boundaries;
- rejected alternatives;
- upstream constraints.

Do not narrate obvious code.

Useful:

```python
# Preserve configuration order; scenario order is a persisted contract.
```

---

## 90. Stale comments

Misleading comments are defects.

Update/remove comments with behavior changes.

Do not retain commented-out code as history.

---

## 91. TODOs

A TODO must identify an action and owner/reference:

```python
# TODO(issue-123): Remove flat-summary reader after the deprecation window.
```

Avoid:

```python
# TODO fix later
```

Release blockers must also be tracked outside comments.

---

## 92. Docstrings

Public modules/classes/nontrivial functions SHOULD have docstrings describing:

- responsibility;
- non-obvious parameter semantics;
- return contract;
- public exceptions;
- side effects;
- path base;
- units;
- compatibility caveats.

Do not duplicate obvious annotations.

Example:

```python
"""Build the canonical JSON summary from completed structured results."""
```

---

## 93. Canonical naming

New code/documentation uses:

```text
GF Wordbench
gf-wordbench
```

Legacy `gf-audit` names remain only in:

- migration readers;
- legacy files;
- compatibility tests;
- historical documentation;
- explicit aliases.

Do not create new canonical APIs with legacy names.

---

## 94. CLI responsibilities

CLI code owns:

- arguments;
- user-value conversion;
- shared configuration builder call;
- orchestration call;
- console rendering;
- process exit code.

It MUST NOT:

- reconstruct audit logic;
- call compiler/scanner/reports directly;
- diverge from GUI semantics;
- own schema logic.

---

## 95. CLI options

Use consistent kebab-case and canonical vocabulary.

Actual names are authoritative in the CLI reference.

Legacy aliases are translated at the boundary and marked deprecated.

---

## 96. CLI exit codes

Exit codes follow the reference document.

Required validation failure MUST NOT return success.

Do not invent undocumented codes.

---

## 97. GUI responsibilities

GUI code:

- converts widget values to plain Python;
- uses shared configuration/orchestration;
- remains optional for headless core;
- displays structured results;
- sends shared cancellation.

It MUST NOT:

- launch GF directly;
- make state authoritative;
- create alternate timeout semantics;
- require GUI packages to import core validation.

---

## 98. GUI concurrency

Long work must not block the event loop.

Concurrency must:

- preserve one orchestration path;
- use typed events/results;
- support cancellation;
- avoid unsafe widget access;
- propagate exceptions;
- avoid concurrent artifact ownership.

---

## 99. Concurrency rules

Concurrency requires:

- unique artifact ownership;
- deterministic result order;
- safe cancellation;
- bounded process count;
- attributable logs;
- correct dependency order;
- race tests.

Do not parallelize dependency-sensitive checkpoints merely for speed.

---

## 100. Testing requirement

Every behavior change requires tests at appropriate levels:

```text
unit
property
contract
integration
real-GF
migration
end-to-end
```

Persisted or external-boundary changes normally require more than unit tests.

---

## 101. Test names

Names should state condition and expected behavior:

```python
def test_timeout_marks_error_and_preserves_partial_stdout() -> None:
    ...
```

Avoid opaque numbering.

---

## 102. Test structure

Use clear given/when/then flow.

Keep each test focused.

Helpers reduce repeated setup but must not hide the key assertion.

---

## 103. Assertions

Assert contracts, not incidental implementation details.

Preferred:

```python
assert result.execution_state is ExecutionState.TIMED_OUT
assert result.stdout_path == expected_path
```

Use full snapshots only when complete structure is the contract.

---

## 104. Test isolation

Tests MUST NOT depend on:

- developer GF path;
- home state;
- current directory;
- test order;
- old run directories;
- network;
- uncontrolled wall time;
- GUI state.

Use explicit temporary directories and fixtures.

---

## 105. Temporary test paths

Use the test framework’s temporary-directory fixture.

Do not write to project/source/repository/home paths except dedicated integration fixtures.

---

## 106. Fake process fixtures

Process tests should simulate:

- success;
- non-zero exit;
- stdout/stderr;
- timeout;
- cancellation;
- child process;
- truncation;
- partial artifact;
- invalid bytes.

Fixtures remain bounded and test-only.

---

## 107. Real-GF tests

Real-GF tests should:

- use a small fixture grammar;
- be marked separately;
- handle missing GF explicitly;
- record GF version;
- preserve failure evidence;
- avoid active-language dependency unless intended;
- remain reproducible.

Unit tests must not all require GF.

---

## 108. Gold/snapshot review

Framework fixtures and active-project golds are distinct.

Snapshot/gold updates require deliberate review.

Do not accept all changed snapshots automatically.

---

## 109. Property tests

Useful for:

- path normalization;
- safe keys;
- parser robustness;
- schema round trips;
- ordering;
- idempotence;
- Unicode;
- process-result invariants.

Failing randomized cases must be reproducible.

---

## 110. Regression tests

Every defect fix should add a test failing before the fix.

Test the underlying contract rather than only the accidental implementation.

---

## 111. Migration tests

Every migration needs:

- source fixture;
- expected current model;
- canonical rewritten output when applicable;
- invalid cases;
- data preservation;
- idempotence or documented one-way behavior.

---

## 112. Test doubles

Prefer fakes/adapters over deep mocking.

Mock side-effect boundaries:

- process;
- clock;
- filesystem failure;
- environment;
- GUI adapter.

Do not mock chains of private helpers.

---

## 113. Coverage standard

Coverage percentage is not sufficient.

High-risk branches require explicit tests:

- timeout;
- cancellation;
- process termination;
- schema migration;
- artifact deletion;
- gold update;
- release gates.

---

## 114. Test performance

Fast tests should remain routine.

Mark/group slow tests:

```text
real GF
platform-specific
stress
end-to-end
```

Do not delete integration coverage merely to improve speed.

---

## 115. Linting

All committed code must pass the configured linter.

New global suppressions require review.

Per-line suppressions must be narrow and justified.

Do not disable high-risk categories globally to accommodate one legacy module.

---

## 116. Dead code

Remove dead code unless compatibility requires it.

Deprecated public behavior needs:

- replacement;
- warning policy;
- tests;
- removal plan.

Do not preserve unused helpers “just in case.”

---

## 117. Complexity

When complexity rises, first ask whether responsibilities are mixed.

Refactor by domain phase:

```text
resolve_request
capture_process
parse_diagnostics
verify_artifacts
build_result
```

Avoid meaningless helpers such as `part1`, `part2`.

---

## 118. Performance

Optimize only while preserving:

- raw capture;
- hashing;
- validation stages;
- dependency order;
- diagnostics;
- artifact freshness.

Measure changes intended to improve performance.

---

## 119. Caching

Caching needs an explicit validity key including applicable values:

```text
source fingerprint
configuration identity
GF version
command
path context
normalization version
```

Do not cache compile success by filename alone.

Release must reject stale cache artifacts unless equivalence is proven.

---

## 120. Memory

Stream large outputs where practical.

Use bounded excerpts.

Do not load unbounded logs into memory without documented limits.

---

## 121. Security boundaries

Treat as untrusted:

```text
project paths
scenario files
scenario inputs
GF output
persisted files
CLI arguments
environment values
external artifacts
```

Validate before use.

---

## 122. Shell safety

Normal execution MUST NOT use an implicit shell.

Prohibited:

```python
subprocess.run(f"{exe} {user_text}", shell=True)
```

A shell-based integration requires its own documented threat model and contract.

---

## 123. Secret handling

Secrets must not enter project config, state, logs, reports, manifests or fixtures.

Future credentialed integrations need a dedicated secret-provider boundary.

---

## 124. Untrusted rendering

GF/project text may contain Markdown/HTML control characters.

Report writers must escape safely.

Never treat GF output as trusted HTML.

---

## 125. Regex standards

Regexes for diagnostics/scanning/normalization must be:

- bounded;
- specific;
- fixture-backed;
- false-positive-tested;
- performance-tested where risky.

Broad expressions such as `.*error.*` cannot be authoritative classifications.

---

## 126. Unicode

Preserve Unicode unless a specific contract defines transformation.

Do not:

- strip accents;
- transliterate;
- case-fold linguistic output globally;
- silently normalize Unicode;
- assume ASCII paths.

---

## 127. Locale

Core behavior must not depend on process locale.

Use explicit encodings and deterministic comparisons.

Localized presentation belongs at UI boundaries.

---

## 128. Platform-specific code

Isolate platform behavior behind adapters/narrow branches:

- process-tree termination;
- executable resolution;
- file locking;
- signals.

Do not scatter platform checks through unrelated modules.

Public result semantics remain stable.

---

## 129. Windows requirements

Consider:

- paths with spaces;
- drive letters;
- Unicode;
- CRLF;
- file locks;
- `gf.exe`;
- no implicit shell;
- child termination.

POSIX-only behavior is incomplete unless explicitly scoped.

---

## 130. POSIX requirements

Consider:

- LF;
- executable permissions;
- process groups;
- signals;
- Unicode;
- symlinks;
- case-sensitive filesystems.

Do not assume Windows path syntax universally.

---

## 131. Symlinks

Symlink behavior must be explicit for containment, deletion, manifests and project paths.

Strict mode should reject unsafe symlinks where required.

Do not follow untrusted symlinks during recursive deletion.

---

## 132. Public API changes

Before changing a public symbol:

```text
[ ] Find direct consumers
[ ] Find downstream consumers
[ ] Review interfile lock
[ ] Review typing
[ ] Review tests
[ ] Review persisted effects
[ ] Review compatibility
[ ] Update documentation
```

A rename is not cosmetic when imported elsewhere.

---

## 133. Function compatibility

Potentially compatible:

- optional keyword-only parameter with safe default;
- wider safe accepted input;
- more specific compatible return subtype.

Breaking:

- positional meaning change;
- return-shape change;
- relied-upon exception change;
- path-base change;
- side-effect change;
- ordering change;
- status-semantic change.

---

## 134. Shared model changes

Changing a model requires review of:

- constructors;
- consumers;
- serializers;
- readers;
- migrations;
- CLI/GUI;
- reports;
- tests;
- locks.

A Python-only rename is internal only when no serializer/consumer depends on it.

---

## 135. Persisted changes

Any persisted change must identify:

```text
schema ID
current version
target version
writer
readers
migration
defaults
ordering
unknown-field behavior
tests
compatibility window
```

No new unversioned persisted format may be introduced.

---

## 136. External command changes

Any GF command change reviews:

- command builder;
- process runner;
- configuration;
- results;
- diagnostics;
- artifacts;
- tests;
- fixtures/golds;
- GF compatibility;
- external-tool lock.

No command changes in isolation.

---

## 137. Documentation synchronization

Update documentation in the same change when modifying:

- user behavior;
- CLI/GUI surface;
- architecture;
- ownership;
- external contract;
- schema;
- statuses;
- modes;
- artifact layout;
- project template;
- release gates.

---

## 138. ADR requirement

Create/update an ADR for durable architectural decisions such as:

- process model;
- project model;
- required report;
- execution engine;
- scenario strategy;
- persistence architecture.

Routine implementation details do not require ADRs.

---

## 139. Review standard

Reviewers examine:

```text
correctness
ownership
dependency direction
typing
errors
paths
raw evidence
schemas
platform behavior
security
tests
documentation
```

Style-only review is insufficient for contract changes.

---

## 140. Change size

Prefer reviewable changes, but keep cross-file contracts complete.

Do not split a breaking unit into inconsistent commits such as:

```text
provider now, consumer later
schema now, migration later
command now, tests later
```

---

## 141. Generated files

Generated code/files must identify:

- generator;
- source;
- edit policy;
- regeneration command;
- review policy.

Fix the generator rather than hand-editing output.

---

## 142. Developer scripts

Committed scripts must:

- have one purpose;
- follow shared path/config rules;
- fail clearly;
- avoid hidden environment dependence;
- validate destructive paths;
- have tests when high impact.

One-off scripts must not become supported workflow accidentally.

---

## 143. Dependency policy

Add a dependency only when:

- standard library/current dependencies are insufficient;
- purpose is clear;
- maintenance/license/security are acceptable;
- platform support fits;
- it is declared in `pyproject.toml`;
- integration is tested.

Do not add a large framework for one trivial helper.

---

## 144. Optional dependencies

Core validation imports must not require optional GUI packages.

Optional dependency failures should appear only at the relevant boundary with clear setup instructions.

---

## 145. Package resources

Access packaged templates/resources using supported package-resource APIs.

Do not rely on repository current directory after installation.

Packaging tests should verify required templates and runtime files.

---

## 146. Version ownership

Application version has one owner.

Do not duplicate version strings in CLI, GUI, reports and package modules.

Schema/parser/normalization versions remain independent.

---

## 147. Feature flags

Feature flags must be:

- explicit;
- typed;
- centrally resolved;
- documented;
- tested in both states;
- assigned a stabilization/removal plan if temporary.

No undocumented environment flags.

---

## 148. Assertions

Use `assert` only for internal impossible conditions.

Do not use it for:

- user input;
- schemas;
- paths;
- artifacts;
- process results;
- security.

Use explicit errors.

---

## 149. Randomness

Avoid randomness in core validation.

When required:

- seed policy is explicit;
- seed is recorded;
- output is bounded;
- exact gold is justified or avoided;
- tests use fixed seeds.

---

## 150. Floating point

Prefer integer milliseconds/bytes/counts for exact persisted data.

Reject NaN/infinity in canonical JSON.

Document rounding/tolerance where floats are necessary.

---

## 151. Sorting

Use explicit stable sort keys.

Avoid locale-dependent sorting.

Do not sort when declared order is semantic.

---

## 152. Resource management

Use context managers for:

- files;
- temporary directories;
- locks;
- process resources;
- transaction-like operations.

Close all handles deterministically.

---

## 153. Background workers

No unmanaged background threads/processes.

Every worker needs:

- owner;
- cancellation;
- shutdown;
- error propagation;
- lifecycle test.

Daemon threads must not hide cleanup problems.

---

## 154. Recovery

Recovery distinguishes:

```text
raw evidence
derived artifacts
control files
temporary files
finalized run
partial run
```

It may rebuild derived artifacts only when source evidence is sufficient.

It must not fabricate raw evidence or claim original finalization.

---

## 155. Cleanup

Cleanup MUST NOT:

- remove active-run directories;
- delete sources;
- delete golds;
- follow unsafe symlinks;
- delete protected release/baseline runs;
- ignore errors.

Use ownership and retention policy.

---

## 156. State handling

State is disposable.

Readers:

- validate;
- use documented coercion;
- fall back safely;
- isolate legacy aliases.

Writers:

- write atomically;
- avoid secrets/results/project identity.

---

## 157. Coercion

Avoid permissive coercion such as:

```text
any non-empty string → true
invalid integer → zero
unknown enum → success
```

Rules must be explicit and tested.

Schema readers should prefer validation errors over silent semantic changes.

---

## 158. Equality and identity

Use `is` for `None`, sentinels and enum members where appropriate.

Use `==` for values.

Do not depend on object identity for reconstructed/persisted models.

---

## 159. Public constants

Public constants have:

- one owner;
- stable meaning;
- clear type;
- tests when contract-relevant.

Do not duplicate filenames, schema IDs or marker prefixes.

---

## 160. Marker/schema constants

Scenario markers and schema identities have one owner.

Runners, normalizers, readers and writers consume the same definition.

Changing them is a contract/schema change.

---

## 161. Codes versus messages

Branch on typed codes, not message text.

Preferred:

```python
if result.error_kind is ErrorKind.TIMEOUT:
    ...
```

Prohibited:

```python
if "timed out" in result.message:
    ...
```

Human wording may change unless explicitly locked.

---

## 162. Feature detection

For GF differences use:

- version gating;
- capability probe;
- documented adapter.

Do not try random command variants until one succeeds.

Silent semantic fallback is prohibited.

---

## 163. Fallbacks

Fallbacks require:

- equivalent semantics;
- documented selection;
- visibility;
- tests;
- strict-mode policy.

A fallback must not turn unsupported behavior into misleading success.

---

## 164. Strict mode

Strict mode may reject:

- untested GF versions;
- unknown schemas/enums;
- unsafe symlinks;
- unexpected artifacts;
- unresolved placeholders;
- unknown scenario output;
- legacy fallbacks.

It tightens acceptance; it does not redefine success semantics.

---

## 165. Dry run and debug

A dry run may resolve/display configuration, commands and selections.

It MUST NOT fabricate validation results or artifacts.

Debug mode may add evidence but MUST NOT:

- weaken validation;
- change commands;
- update gold;
- expose secrets;
- suppress errors.

---

## 166. Documentation code examples

Examples must be:

- syntactically plausible;
- labeled conceptual when not implemented;
- aligned with canonical vocabulary;
- free of active-language assumptions in framework docs;
- free of obsolete command names.

Do not present a proposed command as implemented.

---

## 167. Changelog

Add changelog entries for:

- user-visible features;
- breaking changes;
- schema/migration changes;
- deprecations;
- CLI/GUI changes;
- compatibility changes;
- release-gate changes;
- security fixes.

Pure internal refactors may not need user-facing entries.

---

## 168. Release quality gate

Before release, run the configured equivalents of:

```text
format check
lint
type check
unit tests
contract tests
migration tests
real-GF tests where required
documentation/link checks
schema checks
artifact checks
```

Actual commands belong to `pyproject.toml`, CI and testing documentation.

---

## 169. Minimum conceptual checks

Typical checks may include:

```text
python -m compileall app tests
python -m pytest
gf-wordbench contracts check --strict
gf-wordbench schemas check --strict
```

Only claim commands that actually exist in the repository.

---

## 170. Code-review checklist

```text
[ ] Responsibility remains clear
[ ] Dependency direction is valid
[ ] Public boundaries are typed
[ ] No hidden global state was added
[ ] Path bases are explicit
[ ] Side effects are isolated
[ ] Errors are classified at the correct layer
[ ] Raw evidence is preserved
[ ] Status/error/class values are canonical
[ ] Ordering is deterministic
[ ] Processes remain bounded
[ ] Persisted changes are versioned
[ ] Compatibility is addressed
[ ] Security boundaries are validated
[ ] Windows and POSIX are considered
[ ] Tests prove the changed contract
[ ] Documentation is synchronized
```

---

## 171. Prohibited patterns

Unless an explicit contract justifies them, these are prohibited:

```text
wildcard imports
mutable default arguments
untyped public dictionaries
implicit current-directory resolution
implicit shell execution
global process killing by name
stdout-only diagnostic handling
silent broad exception swallowing
reports launching GF
GUI widgets launching GF directly
normal validation updating gold
unversioned persisted formats
filesystem-order-dependent results
active-language defaults in framework code
duplicated canonical status strings
duplicated artifact path construction
truthiness coercion of schema fields
raw evidence rewriting
silent timeout retry
accepting stale .gfo or .pgf artifacts
```

---

## 172. Drift indicators

Drift exists when:

- a module owns unrelated responsibilities;
- CLI/GUI build different configurations;
- a report imports a process stage;
- a consumer reconstructs an owned path;
- untyped dictionaries become public result models;
- canonical values are duplicated;
- timeout becomes generic `FAIL`;
- parser assigns causal class;
- state defines the active language;
- schema changes without migration;
- unknown enum falls back to success;
- filesystem order changes reports;
- tests depend on developer environment;
- new command uses `shell=True`;
- normal validation changes gold;
- raw streams are merged/overwritten;
- legacy alias becomes canonical output;
- active-language names enter framework defaults;
- broad suppressions hide new issues;
- documentation claims unimplemented behavior.

Every indicator requires restoration or coordinated contract change.

---

## 173. Standards-change workflow

```text
[ ] Rule identified
[ ] Reason documented
[ ] Existing code impact assessed
[ ] Tool configuration reviewed
[ ] Architecture reviewed
[ ] Contract locks reviewed
[ ] Schemas reviewed
[ ] Tests updated
[ ] CI updated
[ ] Migration added if needed
[ ] Documentation updated
[ ] Changelog reviewed
```

Do not change coding policy only through a local linter configuration edit.

---

## 174. Exception process

A deliberate exception records:

```text
rule
affected code
reason
risk
scope
owner
test coverage
review/removal condition
```

Exceptions should be narrow.

A permanent exception should update this standard or architecture.

---

## 175. Related documents

### Architecture

- `docs/architecture/ARCHITECTURE_OVERVIEW.md`
- `docs/architecture/COMPONENT_MAP.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/architecture/PROCESS_EXECUTION_MODEL.md`
- `docs/architecture/ERROR_HANDLING_MODEL.md`
- `docs/architecture/DEPENDENCY_RULES.md`
- `docs/architecture/EXTENSION_BOUNDARIES.md`

### Contracts and schemas

- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

### Development

- `docs/development/DEVELOPMENT_SETUP.md`
- `docs/development/CODEBASE_GUIDE.md`
- `docs/development/TESTING_GF_WORDBENCH.md`
- `docs/development/EXTENDING_GF_WORDBENCH.md`
- `docs/development/BACKWARD_COMPATIBILITY.md`
- `docs/development/DEBUGGING_THE_FRAMEWORK.md`

### Diagnostics, validation and reports

- `docs/diagnostics/ERROR_CLASSIFICATION.md`
- `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md`
- `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md`
- `docs/validation/VALIDATION_PIPELINE.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/reports/REPORTING_OVERVIEW.md`
- `docs/reports/ARTIFACT_MANIFEST.md`

### Repository policy

- `CONTRIBUTING.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `pyproject.toml`

---

## 176. Final enforcement rule

GF Wordbench code is acceptable only when behavior remains understandable across component boundaries and durable across runs and versions.

Therefore:

> No implementation convenience may silently override ownership, typed contracts, raw-evidence preservation, deterministic ordering, external-tool safety or persisted-schema compatibility.

Every change must make the system easier to verify, or document precisely why necessary complexity remains.
