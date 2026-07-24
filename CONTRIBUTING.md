# Contributing to GF Wordbench

Thank you for contributing to GF Wordbench.

GF Wordbench is a validation and development workbench for one active Grammatical Framework language project at a time. Contributions must preserve three properties:

1. **Correctness** — code, contracts, behavior, and evidence agree.
2. **Traceability** — every important result can be traced to source, command, output, artifact, or decision.
3. **Contract integrity** — files, tools, persisted formats, and language-project components do not drift apart.

This document defines the contribution workflow for framework code, documentation, tests, external-tool integration, persisted schemas, project templates, and the active language project.

---

## 1. Authoritative documents

Before changing GF Wordbench, identify which normative document owns the affected behavior.

The normative anti-drift documents are:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Their responsibilities are distinct:

| Lock | Governs |
|---|---|
| `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` | Cross-document product identity, ownership, terminology, and correction rules |
| `docs/INTERFILE_CONTRACT_LOCK.md` | Contracts between framework files and components |
| `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` | Contracts between GF Wordbench and external executables, runtimes, filesystems, and operating-system behavior |
| `docs/PERSISTED_SCHEMA_LOCK.md` | Versioned formats, persistent paths, manifests, state, summaries, normalized outputs, and gold files |
| `project/docs/INTERFILE_CONTRACT_LOCK.md` | Contracts inside the active language project |
| `templates/project/docs/INTERFILE_CONTRACT_LOCK.md` | Generic project-contract template used when initializing another language |

When documents disagree, follow the precedence defined by `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`. Do not choose one silently. Identify the conflict, apply the authoritative rule, update every affected owner document, and add validation that prevents recurrence.

During the coordinated documentation correction program, assignment and integration state are tracked in `docs/DOCUMENTATION_CORRECTION_LEDGER.md`. The ledger is operational tracking, not a product contract.

---

## 2. Contribution areas

Contributions may affect one or more of these areas:

- framework Python code;
- CLI or GUI behavior;
- GF process execution;
- static scanning;
- compilation and PGF construction;
- `.gfs` scenarios;
- normalized scenario output;
- gold expectations;
- diagnostics and classification;
- reports and manifests;
- persisted schemas and migrations;
- project initialization and reset;
- active-language GF source;
- project documentation;
- framework documentation;
- tests, fixtures, and CI;
- Windows launchers and automation.

Every change must declare its affected area or areas.

---

## 3. Repository boundaries

GF Wordbench separates reusable framework assets from the active language project.

### 3.1 Framework-owned content

Framework-owned content includes:

```text
app/
tests/
docs/
templates/
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
pyproject.toml
```

Framework code must not contain active-language identifiers, paths, suffixes, module names, or linguistic assumptions except in clearly named migration fixtures or compatibility tests.

Examples of project-specific content that must not appear in generic framework behavior:

```text
albanian
Sqi
GrammarSqi
NounSqi
lib/src/albanian
```

### 3.2 Active-project content

The active language project lives under:

```text
project/
```

It may contain language-specific:

- paths;
- module names;
- suffixes;
- morphology;
- syntax;
- lincat contracts;
- scenarios;
- inputs;
- gold files;
- decisions;
- known issues;
- release criteria.

### 3.3 Project template

The reusable empty project template lives under:

```text
templates/project/
```

It must remain language-neutral.

A contribution that changes the structure or required documentation of `project/` must normally update `templates/project/` in the same change.

### 3.4 Independent Portfolio boundary

Multi-workspace discovery, multilingual aggregation, cross-project comparison, and portfolio-wide readiness belong to the independent `gf-portfolio` product.

GF Wordbench must not depend on `gf-portfolio` code, runtime, storage, configuration, or availability. The permitted direction is read-only consumption of public, versioned GF Wordbench artifacts by `gf-portfolio`.

A contribution must not introduce Portfolio registries, multi-project selection, cross-workspace orchestration, or Portfolio-owned schemas into GF Wordbench.

### 3.5 Generated run output

Generated audit output must not be treated as source code.

Normal contributions must not commit:

```text
run_*/
_gf_wordbench/
_gf_audit/
*.gfo
*.pgf
temporary scenario output
temporary compile logs
application state containing local paths
```

Reviewed fixtures and intentional gold files are exceptions.

---

## 4. Before making a change

Before editing:

1. identify the owner of the behavior;
2. identify all direct consumers;
3. inspect downstream consumers when the contract crosses multiple layers;
4. identify relevant contract IDs;
5. classify the change;
6. identify required tests;
7. identify persisted-data or migration impact;
8. identify active-project and template impact;
9. identify authoritative documentation affected by a contract, command, schema, workflow, or user-visible behavior change;
10. determine whether an ADR or decision-log entry is required.

Do not begin a broad refactor by editing files independently. Define the coordinated change unit first.

---

## 5. Change classification

Every contribution must be classified as one of the following.

### 5.1 Documentation-only clarification

A documentation-only clarification:

- does not change runtime behavior;
- does not change a public contract;
- does not change a schema;
- does not change accepted validation evidence;
- resolves ambiguity without inventing new behavior.

Required work:

- update the authoritative document;
- check cross-references;
- verify that examples remain consistent with code and locks.

A documentation change that changes normative meaning is not documentation-only. It is a contract change.

### 5.2 Internal compatible change

An internal compatible change preserves every external promise.

Examples:

- refactoring a private helper;
- improving performance without changing output;
- reorganizing internal code;
- improving local error handling without changing public semantics;
- correcting comments;
- adding a local test.

Requirements:

- public signatures remain compatible;
- model fields remain compatible;
- artifact locations remain compatible;
- status semantics remain compatible;
- affected tests pass;
- contract locks remain true.

A lock update is optional only when the contract itself is unchanged.

### 5.3 Compatible contract extension

A compatible extension adds behavior that existing consumers can safely ignore.

Examples:

- an optional model field with a defined default;
- an optional report section;
- an optional scenario;
- an optional project configuration field;
- additional non-breaking diagnostic metadata;
- a new manifest role;
- a new optional GF helper.

Requirements:

- update the provider;
- review all consumers;
- define defaults;
- add tests;
- update relevant lock files;
- increment a schema minor version when persisted data changes;
- update templates when project structure changes;
- add changelog notes when user-visible.

### 5.4 Breaking contract change

A breaking change alters an existing promise.

Examples:

- renaming or removing a public symbol;
- changing a function signature;
- changing a model-field type;
- changing a lincat record shape;
- changing entrypoints;
- renaming a scenario ID;
- changing gold normalization;
- moving artifact ownership;
- changing path-base semantics;
- changing status meaning;
- renaming a persisted field;
- changing expected PGF names;
- changing required project configuration.

Requirements:

1. identify every affected contract ID;
2. document the reason;
3. identify providers and consumers;
4. define migration behavior;
5. update all affected files together;
6. update fixtures and gold files deliberately;
7. add backward-compatibility tests where supported;
8. update relevant lock files;
9. update the changelog and migration documentation;
10. increment the appropriate contract or schema major version;
11. run checkpoint and release validation where applicable.

### 5.5 Emergency repair

An emergency repair may temporarily shorten the normal process only when:

- data loss is possible;
- execution is unsafe;
- generated evidence is materially incorrect;
- a security issue exists.

The repair is not complete until missing tests, lock updates, migration notes, and documentation are added.

---

## 6. Contract-first workflow

A change crossing a file boundary must be treated as one coordinated change.

The minimum contract workflow is:

```text
identify contract
→ identify provider
→ identify all consumers
→ update shared model/schema
→ update code and adapters
→ update tests
→ update artifacts or fixtures
→ update lock
→ validate compatibility
```

A provider may be refactored internally without changing its consumers only when its documented request/response contract remains true.

A consumer may depend only on documented provider behavior. It must not depend on:

- private helpers;
- incidental log wording;
- dictionary insertion order;
- undocumented status values;
- reconstructed artifact paths;
- exception-message text;
- GUI-only state;
- report prose;
- undocumented private details.

---

## 7. Development environment

### 7.1 Supported Python

Use the Python version declared by `pyproject.toml`.

Do not lower the minimum Python version or broaden dependency ranges without compatibility review.

### 7.2 Virtual environment

Recommended Windows setup:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Recommended `cmd.exe` activation:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 7.3 GF environment

Tests that execute real GF require:

- a supported `gf` or `gf.exe`;
- a valid GF/RGL path;
- a writable output directory;
- a small fixture grammar or active project suitable for integration testing.

Unit tests must not require a globally installed GF executable unless marked as integration tests.

### 7.4 Local paths

Do not commit personal absolute paths.

Examples of prohibited committed paths:

```text
C:/Users/<name>/...
C:/mycode/...
/home/<name>/...
```

Absolute local paths may appear only in ignored application state or redacted test fixtures designed specifically to test path migration.

---

## 8. Branches and commits

Use a focused branch for each coherent change.

Recommended branch forms:

```text
feature/scenario-runner
fix/summary-schema-migration
docs/contributing
refactor/process-runner
project/update-morphology-contract
```

Commits should be reviewable and describe intent.

Recommended commit subjects:

```text
feat: add native GFS scenario execution
fix: preserve raw stderr after timeout
docs: define persisted schema migration workflow
test: cover Windows paths with spaces
refactor: centralize artifact path ownership
project: update morphology provider contracts
```

Avoid commits that mix unrelated framework, project, formatting, and generated-output changes.

Do not rewrite gold files, schemas, and code in a large unexplained commit. Separate preparation, behavior, and expected-output changes when practical.

---

## 9. Python coding standards

### 9.1 General rules

Python code must:

- target the configured Python version;
- use explicit type annotations for public functions;
- avoid hidden global mutable state;
- use `pathlib.Path` for filesystem paths;
- use dataclasses or explicit typed models for structured boundaries;
- use deterministic ordering for serialized collections;
- separate process execution from diagnostic interpretation;
- preserve raw evidence before normalization;
- use clear exceptions for framework errors;
- use structured results for expected validation failures;
- avoid duplicate constants and status literals.

### 9.2 Public and private symbols

Public symbols form contracts.

Private helpers should begin with `_`.

A consumer must not import a private symbol from another module unless the symbol is deliberately promoted and documented as public in the same contribution.

### 9.3 Path ownership

Components must receive paths through the designated configuration or path model.

Do not reconstruct owned artifact paths in consumers.

For example, a report reader should use:

```text
run_result.run_paths.summary_json_path
```

or its canonical equivalent, rather than recomputing:

```text
run_dir / "summary.json"
```

when the path is already owned elsewhere.

### 9.4 Process boundaries

`process_utils` owns generic process execution.

Process execution code must not classify GF errors.

Compiler and scenario components own interpretation specific to their requests, but raw stdout, stderr, exit status, command, working directory, timeout state, and duration must be retained.

### 9.5 Error handling

Expected validation failure should return a structured result.

Exceptions are appropriate for:

- invalid configuration;
- impossible filesystem operations;
- process launch failure;
- corrupted state;
- unsupported schema;
- contract violation;
- programming error.

Do not collapse all failures into one exception or one status.

### 9.6 No silent fallback

Fallback behavior must be explicit, testable, and documented.

Do not silently:

- use another executable;
- use another project root;
- change the GF path;
- skip a required scenario;
- create a missing gold file;
- accept an unsupported schema;
- ignore a malformed manifest;
- convert a required failure into a warning.

---

## 10. GF source and project standards

Changes under `project/` must follow the active project contract lock.

### 10.1 Module ownership

Every public GF symbol, helper, lincat field, paradigm, constructor family, or entrypoint must have one documented owner.

Do not duplicate a helper into multiple modules to bypass a dependency problem.

### 10.2 Provider and consumer validation

When a provider changes, validate:

1. the provider directly;
2. every direct consumer;
3. affected checkpoints;
4. affected entrypoints;
5. scenarios exercising the contract;
6. release PGF construction when release-facing.

A provider compile alone is insufficient evidence when consumers depend on its shape or semantics.

### 10.3 Structured categories

Do not flatten structured categories or records into strings merely to bypass a type contract.

Any intentional representation change requires:

- category/lincat contract update;
- consumer review;
- scenario review;
- gold review;
- decision-log entry;
- migration or release impact assessment.

### 10.4 Known issues and release blockers

Record an unresolved project issue only when it materially affects a language contract, validation result, release criterion, migration, or maintainer handoff. Use the project-owned issue or decision document appropriate to the subject.

Do not use project documentation to track routine development progress, transient implementation states, or short-lived work sequencing.

---

## 11. External-tool changes

A change to GF invocation or any external process is a contract change.

External-tool changes include:

- executable resolution;
- ordered command arguments;
- working directory;
- environment variables;
- standard input;
- stream encoding;
- timeout behavior;
- termination behavior;
- artifact expectations;
- output normalization;
- supported GF versions;
- platform-specific behavior.

Every external-tool change must document:

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

Required review:

```text
[ ] Request builder updated
[ ] Process runner reviewed
[ ] Configuration reviewed
[ ] Result model reviewed
[ ] Raw evidence paths reviewed
[ ] Diagnostic parsing reviewed
[ ] Artifact checks reviewed
[ ] Unit tests updated
[ ] Real-GF integration tests updated
[ ] Windows behavior reviewed
[ ] Gold files deliberately reviewed
[ ] External-tool lock updated
```

### 11.1 Security

Project scenarios must not contain shell escapes or arbitrary external-command execution unless the feature is explicitly authorized, documented, and tested.

GF Wordbench must not pass untrusted text through a shell command string when an argument-array API is available.

---

## 12. Persisted-schema changes

Persisted assets include:

- `project/project.toml`;
- application state;
- `summary.json`;
- `manifest.json`;
- file and scenario results;
- normalized `.out` files;
- `.gold` files;
- stable report filenames and directory layout.

A persisted-schema change must identify:

```text
Schema:
Current version:
Target version:
Change:
Reason:
Writers:
Readers:
Compatibility:
Migration:
Data-loss risk:
Tests:
```

Required checklist:

```text
[ ] Schema ID identified
[ ] Current schema version identified
[ ] Change classified as compatible or breaking
[ ] Writer updated
[ ] Every reader updated
[ ] Migration updated or created
[ ] Defaults documented
[ ] Enum impact reviewed
[ ] Path semantics reviewed
[ ] Atomic-write behavior reviewed
[ ] Contract tests updated
[ ] Fixtures updated deliberately
[ ] Gold files reviewed if normalization changed
[ ] Persisted-schema lock updated
[ ] Changelog or migration guide updated
```

### 12.1 Writer rules

Canonical writers must:

- emit the current schema version;
- write UTF-8;
- use deterministic ordering;
- use canonical path separators and bases;
- write atomically where required;
- never emit legacy aliases;
- preserve data types;
- reject impossible values;
- avoid secrets.

### 12.2 Reader rules

Readers must:

- validate schema identity;
- validate the supported major version;
- distinguish missing from null where defined;
- ignore unknown optional fields only when permitted;
- reject unknown enum values in strict mode;
- never silently reinterpret legacy values;
- preserve raw source during migration.

### 12.3 Migration rules

Migrations must:

- be idempotent;
- not overwrite the source during read-only loading;
- report warnings and losses;
- preserve recoverable evidence;
- write a canonical destination atomically;
- include tests for real legacy fixtures.

---

## 13. Scenario contributions

Scenario files belong under:

```text
project/validation/scenarios/
```

A scenario contribution must define:

- stable scenario ID;
- purpose;
- target entrypoint;
- required or optional status;
- inputs;
- expected markers;
- timeout;
- normalization policy;
- assertion or gold strategy;
- expected artifacts.

### 13.1 Scenario rules

Scenarios must:

- use UTF-8;
- use documented GF commands;
- include required begin/end markers;
- terminate predictably;
- avoid hidden environment dependencies;
- avoid machine-specific absolute paths;
- remain bounded;
- preserve reproducible evidence.

Random generation must not be used as an exact deterministic gold unless a stable seed and deterministic upstream behavior are guaranteed and documented.

### 13.2 Scenario review

A new required scenario must update:

- `project.toml`;
- project validation documentation;
- scenario registry;
- expected gold or explicit assertion strategy;
- release criteria when release-blocking;
- project interfile contract lock when it adds a new boundary.

---

## 14. Gold-file contributions

Gold files live under:

```text
project/validation/gold/
```

They are reviewed source artifacts, not disposable generated output.

A normal validation run must never modify them.

Gold changes require:

1. an intentional source, scenario, normalization, or accepted-behavior change;
2. a recorded diff;
3. review of linguistic and technical meaning;
4. matching scenario ID and normalization version;
5. explicit update operation;
6. project documentation review;
7. changelog or decision-log update when behavior changes.

Do not approve a gold update solely because it makes a failing test pass.

Review the output semantically.

A missing required gold file is a failure. It must not be created silently.

---

## 15. Diagnostic and status changes

The framework must keep distinct concepts distinct.

### 15.1 Validation status

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Meaning:

- `OK`: validation ran and met its criteria;
- `FAIL`: validation ran but did not meet its criteria;
- `ERROR`: GF Wordbench could not execute or interpret the validation correctly;
- `SKIPPED`: the stage was intentionally not executed.

### 15.2 Diagnostic class

Canonical causal classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### 15.3 Error kind

Error kind identifies technical or GF error nature and is separate from causal classification.

A contribution adding or changing a status, diagnostic class, or error kind must update:

- shared models;
- serializers;
- readers;
- reports;
- GUI and CLI displays;
- tests;
- status and diagnostic reference documents;
- interfile lock;
- persisted-schema lock when serialized.

Do not introduce a new status string in only one file.

---

## 16. Reports and artifacts

Reports consume results. They must not rerun validation.

A report contribution must:

- derive facts from structured results;
- preserve distinction between raw and normalized evidence;
- use owned artifact paths;
- avoid unsupported diagnosis;
- preserve deterministic ordering;
- handle missing optional artifacts safely;
- maintain required headings or schema fields;
- add report contract tests.

Changes to public report names, paths, schema, required sections, or machine-readable fields are persisted-schema changes.

### 16.1 AI-ready report

`AI_READY.md` must be produced from existing run evidence.

It must not trigger:

- a second compilation;
- a second scenario run;
- new language generation;
- silent log reconstruction.

---

## 17. Documentation standards

Documentation is part of the product contract.

### 17.1 Ownership

Each rule must have one authoritative owner.

Other documents should link to the owner rather than duplicate full normative rules.

Examples:

- schema details belong in `PERSISTED_SCHEMA_LOCK.md`;
- external invocation details belong in `EXTERNAL_TOOL_CONTRACT_LOCK.md`;
- framework file boundaries belong in `INTERFILE_CONTRACT_LOCK.md`;
- active-language boundaries belong in `project/docs/INTERFILE_CONTRACT_LOCK.md`.

### 17.2 Normative language

Use `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` only when the statement is intentionally normative.

Avoid contradictory requirements disguised as examples.

### 17.3 Examples

Examples must be labeled when they are not canonical.

Do not use active-language names in generic templates unless clearly marked as illustrative examples.

### 17.4 Cross-references

When a file is renamed or moved:

- update documentation links;
- update lock paths;
- update templates;
- update tests validating required documentation;
- update repository maps;
- update scripts that locate the file.

### 17.5 Documentation quality standard

A maintained document must:

- state its scope;
- identify its owner;
- distinguish normative rules from guidance;
- avoid unresolved placeholders unless it is explicitly a template;
- use stable terminology;
- agree with accepted ADRs, anti-drift locks, and public contracts;
- describe the product directly, without implementation-progress labels or routine development-status tracking.

### 17.6 Parallel documentation correction

During coordinated documentation repair:

- each branch edits one assigned target file;
- every branch receives the unchanged documentation alignment lock and relevant specialized locks;
- a branch does not reinterpret or edit the shared locks unless explicitly assigned a coordinated lock change;
- contradictions are reported rather than resolved silently;
- the complete corrected file is returned at its canonical repository path;
- `docs/DOCUMENTATION_CORRECTION_LEDGER.md` is updated only during integration.

---

## 18. Tests

Every behavioral change requires tests proportional to its risk.

### 18.1 Unit tests

Unit tests should isolate:

- pure parsing;
- command construction;
- path normalization;
- classification;
- schema validation;
- serialization;
- diff behavior;
- result aggregation;
- scenario-marker parsing;
- output normalization;
- gold comparison.

### 18.2 Contract tests

Contract tests belong under:

```text
tests/contracts/
```

They should verify:

- public signatures;
- required result fields;
- status semantics;
- artifact ownership;
- path ownership;
- deterministic ordering;
- serialization round trips;
- legacy loading;
- timeout representation;
- required-scenario behavior;
- gold read-only behavior;
- forbidden dependency directions.

### 18.3 Schema tests

Schema tests belong under:

```text
tests/schemas/
```

They should cover:

- schema identity;
- supported and unsupported versions;
- defaults;
- unknown fields;
- unknown enums;
- path portability;
- Unicode;
- timestamps;
- atomic writes;
- migrations;
- manifests;
- gold headers;
- normalized output;
- legacy fixtures.

### 18.4 Integration tests

Integration tests with real GF should use a small fixture grammar.

They should cover:

- version probe;
- successful compilation;
- failed compilation;
- PGF build;
- `.gfs` loading;
- parsing;
- linearization;
- bounded generation;
- missing executable;
- timeout handling where safe.

Mark tests requiring real GF separately so unit tests remain runnable without a GF installation.

### 18.5 Platform tests

At minimum, test:

- Windows paths with spaces;
- native Windows executable invocation;
- CRLF input;
- UTF-8 language data;
- missing executable;
- unwritable output;
- process timeout;
- canonical `/` serialization;
- legacy `\` path migration.

---

## 19. Validation commands

Use the commands defined by the repository configuration.

The baseline Python validation is expected to include:

```powershell
python -m pytest
python -m compileall -q app tests
python -m ruff check app tests
python -m mypy app
```

When a tool is unavailable, do not claim that its validation passed.

Report it as not executed.

Contract and schema validation includes:

```powershell
gf-wordbench contracts check --strict
gf-wordbench contracts check-external --strict
gf-wordbench schemas check --strict
gf-wordbench project contracts check
```

Project-facing changes should run the relevant GF Wordbench modes:

```text
quick
checkpoint
release
diagnostic
```

Run `release` for changes that affect:

- release entrypoints;
- required scenarios;
- gold output;
- PGF construction;
- schemas consumed by release tooling;
- external GF invocation;
- artifact ownership.

---

## 20. Pull request or change-set requirements

A contribution must explain what changed and why.

Recommended description:

```text
Summary:
Change classification:
Affected contracts:
Providers:
Consumers:
Behavior before:
Behavior after:
Compatibility:
Migration:
External-tool impact:
Persisted-schema impact:
Project/template impact:
Scenario/gold impact:
Security impact:
Tests:
Evidence:
Documentation:
```

### 20.1 General checklist

```text
[ ] Scope is coherent and focused
[ ] Change classification is stated
[ ] Contract IDs are identified
[ ] Providers and consumers are identified
[ ] Framework/project boundary is preserved
[ ] Shared models and schemas are updated
[ ] Artifact ownership is preserved
[ ] Error behavior is reviewed
[ ] Unit tests are updated
[ ] Contract tests are updated
[ ] Integration tests are updated where required
[ ] Documentation is updated
[ ] Relevant lock files are updated
[ ] Changelog or migration notes are updated when required
[ ] Generated files are not committed accidentally
[ ] No secrets or personal paths are included
```

### 20.2 External-tool checklist

```text
[ ] Command and argument order reviewed
[ ] Working directory reviewed
[ ] Environment reviewed
[ ] Encoding reviewed
[ ] Timeout reviewed
[ ] Raw stdout/stderr capture reviewed
[ ] Artifact checks reviewed
[ ] Supported GF versions reviewed
[ ] Real-GF test updated
[ ] Windows test updated
```

### 20.3 Persisted-schema checklist

```text
[ ] Schema ID and version reviewed
[ ] Writer updated
[ ] All readers updated
[ ] Migration provided
[ ] Defaults documented
[ ] Enum compatibility reviewed
[ ] Path semantics reviewed
[ ] Atomic write tested
[ ] Legacy fixture tested
[ ] Manifest impact reviewed
```

### 20.4 Active-project checklist

```text
[ ] Provider module validated
[ ] Direct consumers validated
[ ] Downstream entrypoints validated
[ ] Dependency map updated
[ ] Category/lincat contract updated
[ ] Scenarios reviewed
[ ] Inputs reviewed
[ ] Gold files reviewed
[ ] Known issues or release blockers updated when materially affected
[ ] Decision log updated when architectural
[ ] Checkpoint validation passed
[ ] Release validation passed when release-facing
```

---

## 21. Review expectations

Reviewers verify more than code style.

A reviewer should confirm:

- the change belongs in the claimed owner;
- every consumer was identified;
- no private behavior became a hidden contract;
- statuses and schemas remain consistent;
- reports do not rerun tools;
- raw evidence is preserved;
- gold changes are intentional;
- migrations are safe and tested;
- active-language content did not leak into the framework;
- template and active-project structure remain aligned;
- documentation describes accepted behavior and public contracts directly, without progress labels;
- validation evidence supports the conclusion.

For contract changes, reviewers should ask both:

```text
Does the provider still guarantee the documented response?
Does each consumer depend only on the documented guarantee?
```

---

## 22. Changelog and decisions

Update `CHANGELOG.md` for:

- user-visible features;
- bug fixes affecting results;
- schema changes;
- migration requirements;
- changed CLI or GUI behavior;
- supported GF-version changes;
- report format changes;
- changed release criteria.

Add or update an ADR when a change alters:

- architectural ownership;
- dependency direction;
- execution engine strategy;
- persisted schema strategy;
- scenario strategy;
- result model separation;
- major reporting policy;
- project lifecycle.

Use the active project decision log for language-specific architectural or linguistic decisions.

---

## 23. Security contributions

Report suspected vulnerabilities according to `SECURITY.md`.

Do not publish sensitive security details in a public issue before a safe remediation path exists.

Security-sensitive areas include:

- external process invocation;
- shell escapes;
- path traversal;
- symlink handling;
- unsafe archive extraction;
- untrusted project configuration;
- arbitrary file overwrite;
- gold update commands;
- secrets in logs;
- executable resolution;
- environment-variable leakage.

Security fixes may use the emergency process, but tests and contract documentation remain required before closure.

---

## 24. AI-assisted contributions

AI-assisted contributions are allowed, but the contributor remains responsible for correctness.

AI-generated changes must be reviewed for:

- invented files or APIs;
- nonexistent GF commands;
- fabricated schema fields;
- duplicated normative rules;
- active-language leakage;
- path assumptions;
- hidden behavior changes;
- untested gold rewrites;
- unsupported conclusions.

Do not submit an AI-generated change solely because it appears plausible.

Validate it against:

- the repository;
- the lock files;
- GF behavior;
- tests;
- real artifacts when applicable.

The contribution description should disclose substantial AI assistance when it materially shaped code, schemas, or normative documentation.

---

## 25. Definition of done

A contribution is complete when:

1. the behavior is correct;
2. the change is properly classified;
3. affected contracts are updated;
4. all providers and consumers agree;
5. persisted data remains compatible or is migrated;
6. external-tool behavior is validated;
7. required tests pass;
8. relevant GF validation passes;
9. authoritative documentation is updated when contracts, commands, schemas, workflows, or user-visible behavior change;
10. templates remain reusable;
11. raw evidence is preserved;
12. no unintended gold or artifact changes remain;
13. the changelog or decision record is updated when required;
14. review can trace every important claim to evidence.

Passing local unit tests alone is not sufficient for a contribution that changes a cross-file, external-tool, persisted-schema, or active-language contract.

---

## 26. Contract integrity rule

> Do not change one side of a contract and leave the other side to adapt implicitly.

Every accepted contribution must leave GF Wordbench in a state where:

- framework files agree with one another;
- external requests agree with external-response interpretation;
- writers agree with readers;
- active-project modules agree with consumers;
- scenarios agree with entrypoints;
- outputs agree with gold expectations;
- documentation agrees with accepted contracts and observable behavior;
- tests prove the agreement.
