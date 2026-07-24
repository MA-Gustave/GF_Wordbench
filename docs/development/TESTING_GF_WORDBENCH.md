# GF Wordbench — Testing GF Wordbench

**Document ID:** `GF-WB-DEV-TESTING`  
**Status:** Normative development and release-testing specification  
**Applies to:** GF Wordbench framework, project template, test fixtures, migrations, and supported platform integrations  
**Primary owners:** GF Wordbench maintainers  
**Test framework:** `pytest`  
**Supporting tools:** `pytest-cov`, `ruff`, `mypy`  
**Specification version:** `1.1`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Product-boundary authority:** ADR-0001, ADR-0011 and ADR-0012  
**Contract authorities:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`  
**Last reviewed:** 2026-07-24  

---

## 1. Purpose

This document defines the testing strategy for GF Wordbench.

It specifies:

- the test layers;
- which tests require a real GF installation;
- which tests must remain environment-independent;
- test directory structure;
- test markers;
- fixture design;
- fake executable design;
- contract and schema tests;
- report and artifact tests;
- scenario and gold tests;
- platform tests;
- end-to-end tests;
- coverage policy;
- static analysis;
- local and CI commands;
- release gates;
- failure triage;
- compatibility with the inherited GF Audit evidence and formats.

The goal is not merely to accumulate tests.

The goal is to prove that the architecture, contracts, schemas, GF integration, and generated evidence remain coherent as one system.

---

## 2. Core rule

> Every externally visible behavior must be proven at the lowest reliable layer and again at each architectural boundary where drift could occur.

A unit test alone is insufficient when behavior crosses:

- Python module boundaries;
- process boundaries;
- persisted schemas;
- project assets;
- GF versions;
- operating systems;
- report and artifact ownership;
- migration boundaries.

A full end-to-end test alone is also insufficient because it cannot isolate every failure precisely.

GF Wordbench therefore uses a layered suite.

---

## 3. Related authority

The following documents define behaviors tested by this specification:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/DEPENDENCY_RULES.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/SCENARIO_VALIDATION.md
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
docs/reports/REPORTING_OVERVIEW.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/release/RELEASE_PROCESS.md
```

The active language project has separate language-validation evidence under:

```text
project/validation/
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
```

Framework tests must not hardcode one active language.

---

## 4. Scope

This document governs tests for:

- configuration;
- project loading;
- application state;
- path resolution;
- file selection;
- source scanning;
- process execution;
- GF executable discovery;
- GF version probing;
- compilation;
- PGF construction;
- scenario execution;
- marker parsing;
- output normalization;
- gold comparison;
- diagnostic parsing;
- causal classification;
- fingerprints;
- previous-run comparison;
- result aggregation;
- release gates;
- reports;
- manifests;
- migrations;
- CLI;
- GUI boundaries;
- Windows launchers;
- security invariants;
- dependency direction;
- project-template integrity.

---

## 5. Exclusions

This document does not define:

- the complete linguistic test suite for one language;
- the linguistic correctness of project-specific examples;
- upstream GF’s own internal test suite;
- performance benchmarking of GF itself;
- remote services;
- load testing for a hosted platform;
- browser testing;
- a requirement for mutation-testing tools in version `1.0`;
- a requirement for property-testing libraries in version `1.0`.

Property-based or mutation testing may be added where it provides stable value.

It is not required merely to increase tool count.

## 5.1 Independent-product boundary

GF Wordbench tests run without `gf-portfolio` installed, configured or available.

The suite verifies:

- no Wordbench package imports `gf-portfolio`;
- no Wordbench schema contains a Portfolio workspace registry or private Portfolio state;
- no validation, diagnostic, reporting or release test requires a Portfolio service;
- Wordbench produces finalized public artifacts without a Portfolio runtime;
- external consumers may read public versioned artifacts without mutating them;
- Portfolio-specific adapters and aggregation tests remain outside the Wordbench core suite.

---

# 6. Testing principles

## 6.1 Determinism

Tests must produce the same result from the same controlled inputs.

Timestamps, temporary roots, process IDs, and durations must be normalized or asserted by type/range rather than exact value.

## 6.2 Isolation

Tests must not depend silently on:

```text
developer PATH
developer GF_LIB_PATH
current working directory
GUI state
existing run history
user home contents
network access
unrelated environment variables
```

## 6.3 Evidence preservation

A failing integration test should retain enough evidence to explain:

- executed command;
- working directory;
- stdout;
- stderr;
- exit code;
- timeout or cancellation;
- expected artifact state.

## 6.4 Boundary focus

Contract tests verify boundaries, not private code details.

## 6.5 Minimal mocking

Mock at an architectural boundary.

Do not mock every helper inside the component under test.

## 6.6 Realistic fixtures

Fixtures resemble canonical project, run, schema, and GF evidence formats.

## 6.7 No false success

A test must not pass because:

- GF was unavailable and the test silently skipped;
- a required artifact assertion was omitted;
- output comparison ignored stderr;
- a gold file was rewritten automatically;
- an exception was swallowed;
- an empty collection satisfied a vacuous assertion unintentionally.

## 6.8 Fast default suite

The default local suite must not require a real GF installation.

## 6.9 Explicit expensive tests

Tests requiring GF, GUI, platform containment, or large fixtures are explicitly marked.

## 6.10 One behavior per failure reason

A test may assert several closely related invariants, but its failure must identify one coherent contract.

---

# 7. Test layers

The suite has eight layers.

```text
1. unit
2. component
3. contract
4. schema and migration
5. process integration
6. real-GF integration
7. end-to-end
8. release verification
```

These layers overlap by design but have different proof responsibilities.

---

## 8. Unit tests

Unit tests cover pure or tightly bounded behavior.

Examples:

- enum validation;
- path serialization;
- safe artifact keys;
- diagnostic regexes;
- marker state machines;
- count aggregation;
- report section ordering;
- source-scanner lexical behavior;
- migration field mapping;
- release-gate predicates.

Unit tests:

- use `tmp_path` for filesystem needs;
- use explicit dataclass/model builders;
- avoid launching GF;
- avoid GUI creation unless testing a GUI-specific unit;
- complete quickly.

---

## 9. Component tests

Component tests exercise one architectural owner with its immediate collaborators replaced at stable boundaries.

Examples:

```text
validation compilation service with fake ProcessResult
scenario validation service with fake external-tool port
runs coordinator with fake validation stages
reporting service with real RunResult fixture
projects loader with temporary project configuration
bootstrap with controlled ports and environment
```

Component tests prove:

- request construction;
- result construction;
- error propagation;
- ownership;
- no prohibited side effect.

---

## 10. Contract tests

Contract tests verify documented provider-consumer agreements.

Examples:

- CLI and GUI call the same application use cases;
- reporting consumes structured run results;
- validation returns the documented compile and scenario models;
- the external-tool adapter preserves stdout and stderr;
- artifact paths come from the runs-owned path registry;
- normal validation does not modify gold;
- the projects module accepts the canonical project schema;
- readers accept documented legacy forms through migration;
- reporting does not import validation execution adapters;
- no component reconstructs artifacts owned by another module;
- Wordbench starts, tests and produces artifacts without `gf-portfolio`.

Contract tests are required because local unit tests may all pass while cross-file behavior drifts.

---

## 11. Schema and migration tests

Schema tests verify machine-readable persisted contracts.

They cover:

```text
project.toml
.gf_wordbench_state.json
summary.json
manifest.json
scenario .out
scenario .gold
```

They prove:

- schema identity;
- schema version;
- required fields;
- field types;
- enums;
- path bases;
- ordering;
- encoding;
- migrations;
- canonical re-emission;
- rejection of unsupported major versions.

---

## 12. Process integration tests

Process integration tests launch controlled local fake executables.

They do not require GF.

They prove:

- argument boundaries;
- shell-free execution;
- working directory;
- environment;
- stdin;
- stdout/stderr capture;
- timeout;
- cancellation;
- child-process termination;
- output limits;
- launch failure;
- encoding behavior;
- expected artifact observation.

These tests exercise the real process runner.

---

## 13. Real-GF integration tests

Real-GF tests invoke an actual supported GF executable against a small fixture grammar.

They prove the external contract.

They cover:

- version probe;
- successful compile;
- failed compile;
- path options;
- PGF build;
- `.gfs` execution;
- parse;
- linearize;
- bounded generation;
- markers;
- UTF-8 data;
- expected artifacts.

They are explicitly marked and may be skipped only when the invocation does not require GF.

A release verification environment must not skip them.

---

## 14. End-to-end tests

An end-to-end test starts at a supported user boundary and ends with a validated run directory.

Typical path:

```text
CLI arguments
    → bootstrap
    → project loading
    → audit orchestration
    → stages
    → reports
    → manifest verification
```

End-to-end tests use:

- a fake GF executable for the standard cross-platform suite;
- a real GF executable for a smaller release integration suite.

---

## 15. Release verification

Release verification is the complete required gate.

It includes:

```text
format/lint
type checking
default test suite
contract suite
schema suite
platform-required suite
real-GF suite
end-to-end release fixture
documentation and lock consistency checks
package build and installation smoke test
```

A release is not accepted based only on percentage coverage.

---

# 16. Canonical test directory structure

```text
tests/
├── conftest.py
├── unit/
│   ├── projects/
│   ├── runs/
│   ├── validation/
│   ├── diagnostics/
│   ├── reporting/
│   ├── schemas/
│   ├── paths/
│   └── process/
├── components/
│   ├── test_bootstrap.py
│   ├── test_project_loader.py
│   ├── test_run_coordinator.py
│   ├── test_compilation_service.py
│   ├── test_scenario_service.py
│   ├── test_diagnostics_service.py
│   └── test_reporting_service.py
├── contracts/
│   ├── test_project_contracts.py
│   ├── test_run_contracts.py
│   ├── test_validation_contracts.py
│   ├── test_diagnostics_contracts.py
│   ├── test_reporting_contracts.py
│   ├── test_model_contracts.py
│   ├── test_artifact_ownership.py
│   ├── test_dependency_directions.py
│   ├── test_environment_contract.py
│   ├── test_filesystem_contract.py
│   ├── test_product_boundary.py
│   └── test_windows_contract.py
├── schemas/
│   ├── test_project_schema.py
│   ├── test_state_schema.py
│   ├── test_summary_schema.py
│   ├── test_manifest_schema.py
│   ├── test_scenario_output_schema.py
│   ├── test_gold_schema.py
│   └── test_migrations.py
├── integration/
│   ├── process/
│   ├── gf/
│   ├── cli/
│   ├── gui/
│   └── end_to_end/
├── fixtures/
│   ├── projects/
│   ├── gf/
│   ├── diagnostics/
│   ├── schemas/
│   ├── reports/
│   ├── scenarios/
│   ├── legacy/
│   └── executables/
└── helpers/
    ├── builders.py
    ├── fake_processes.py
    ├── assertions.py
    └── fixture_paths.py
```

This organization is canonical.

A file may move without changing its test intent, but each test remains assigned to one stable proof responsibility.

---

## 17. Avoiding unnecessary fragmentation

A new test file is justified when it owns a stable test domain.

Do not create one file per function.

Required balance:

- one test module per cohesive contract owner;
- separate contract tests from component and unit tests;
- separate real-GF tests from fake-process tests;
- separate schema versions or formats when fixtures become substantial.

Small related tests may remain together.

---

# 18. Pytest configuration

The project uses `pytest`.

Canonical configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = [
  "-ra",
  "--strict-markers",
  "--strict-config",
]
markers = [
  "gf: requires a real GF executable",
  "gui: requires GUI dependencies or display support",
  "windows: Windows-specific behavior",
  "posix: POSIX-specific behavior",
  "slow: intentionally slower than the normal suite",
  "e2e: full application workflow",
  "contract: architectural contract validation",
  "schema: persisted-schema validation",
  "migration: legacy migration validation",
  "security: security or containment behavior",
]
```

`pyproject.toml` may add coverage defaults through documented commands rather than forcing coverage on every quick local run.

---

## 19. Strict markers

`--strict-markers` is required.

A misspelled marker must fail collection.

This prevents a test from being excluded accidentally from release gates.

---

## 20. Strict configuration

`--strict-config` is required.

Invalid pytest configuration must fail.

Warnings caused by deprecated test configuration are resolved deliberately.

---

## 21. Warning policy

Unexpected warnings should fail the suite or be escalated in CI.

A warning filter must:

- identify the exact source;
- document why the warning is accepted;
- have a removal condition.

Broad suppression such as:

```text
ignore all warnings
```

is prohibited.

---

# 22. Test markers

## 22.1 `gf`

Use for a test that launches a real GF executable.

Do not use for tests that only parse captured GF output.

## 22.2 `gui`

Use when a test imports or creates actual GUI components.

Pure GUI-controller or configuration tests that do not need the GUI runtime may remain unmarked.

## 22.3 `windows`

Use for behavior meaningful only on Windows.

## 22.4 `posix`

Use for behavior meaningful only on POSIX.

## 22.5 `slow`

Use when a test is materially slower than the default suite.

A test must not be marked slow merely because it is inconvenient.

## 22.6 `e2e`

Use for complete user-to-artifact workflows.

## 22.7 `contract`

Use for architectural boundary assertions.

## 22.8 `schema`

Use for persisted-schema validation.

## 22.9 `migration`

Use for compatibility conversion.

## 22.10 `security`

Use for path escape, shell injection, secret redaction, containment, or unsafe scenario behavior.

---

# 23. Canonical commands

## 23.1 Fast local suite

```text
python -m pytest -m "not gf and not gui and not slow"
```

## 23.2 Complete suite without real GF

```text
python -m pytest -m "not gf"
```

## 23.3 Contract suite

```text
python -m pytest -m contract
```

## 23.4 Schema and migration suite

```text
python -m pytest -m "schema or migration"
```

## 23.5 Real-GF suite

```text
python -m pytest -m gf
```

## 23.6 End-to-end suite

```text
python -m pytest -m e2e
```

## 23.7 Full available suite

```text
python -m pytest
```

A release environment must configure GF and required GUI/platform capabilities explicitly before running the full release gate.

---

# 24. Development dependencies

Required development dependencies include:

```text
pytest
pytest-cov
ruff
mypy
```

The project pins compatible version ranges in `pyproject.toml` according to dependency policy.

A new mandatory test dependency requires:

- clear capability;
- maintenance review;
- license review;
- CI support;
- documentation;
- justification over the standard library or current tools.

---

# 25. Python version matrix

The project’s declared minimum Python version is authoritative.

The baseline currently targets Python `3.11`.

The CI matrix includes:

```text
minimum supported Python
latest supported Python
```

Additional versions may be tested when support is promised.

A release must not be made from only an unsupported development interpreter.

---

# 26. Platform matrix

Minimum platform coverage:

```text
Windows
one supported POSIX environment
```

Windows is first-class because the framework explicitly supports:

- `gf.exe`;
- Windows paths;
- batch launchers;
- GUI startup;
- process termination;
- CRLF input;
- paths containing spaces.

Platform-neutral tests run on every platform.

Platform-specific tests are marked and gated appropriately.

---

# 27. GF version matrix

Real-GF CI or release verification should cover:

```text
minimum supported GF version
primary tested GF version
latest tested GF version when different
```

Known incompatible versions should be tested through configuration or compatibility fixtures even when they are not installed in every CI job.

A GF version outside the tested range must not be silently treated as fully certified.

---

# 28. Environment-independent default suite

The default suite must pass when:

```text
GF is not installed
PySide6 display is unavailable
GF_LIB_PATH is unset
no project state file exists
no previous runs exist
network access is disabled
```

Tests must provide their own:

- temporary project;
- output root;
- state path;
- fake executable;
- source fixtures;
- schema fixtures.

---

# 29. Test environment cleanup

Use pytest fixtures such as:

```text
tmp_path
monkeypatch
capsys
caplog
```

Every test that changes environment or current directory must restore it automatically.

Direct mutation of global process state without fixture cleanup is prohibited.

---

# 30. Current working directory

Tests must not rely on the test runner being launched from the repository root unless the behavior under test explicitly concerns invocation paths.

Use explicit fixture paths.

A test that changes current working directory should use:

```python
monkeypatch.chdir(...)
```

and assert the intended base behavior.

---

# 31. Environment variables

Tests must clear or control relevant values:

```text
GF_WORDBENCH_PROJECT_ROOT
GF_WORDBENCH_GF_EXE
GF_WORDBENCH_RGL_ROOT
GF_WORDBENCH_OUTPUT_ROOT
GF_WORDBENCH_STATE_PATH
GF_LIB_PATH
```

Do not inherit a developer’s path behavior accidentally.

---

# 32. Time control

Tests involving timestamps or run IDs should use:

- injected clock;
- deterministic clock fixture;
- range assertions;
- explicit run ID override in test-only APIs.

Avoid sleeping to advance wall time.

Timeout tests may use controlled child processes, but must remain bounded.

---

# 33. Randomness

Core tests should avoid randomness.

When random data is useful:

- set and report a seed;
- bound generated size;
- retain a minimized failing case where possible;
- never use randomness for exact gold output without a stable seed and ordering contract.

---

# 34. Test data encoding

Canonical fixture text uses:

```text
UTF-8 without BOM
LF
terminating newline where required
```

Compatibility fixtures should explicitly include:

- CRLF;
- UTF-8 BOM;
- invalid UTF-8 bytes;
- Windows separators;
- legacy absolute paths.

A fixture’s noncanonical property must be intentional and documented.

---

# 35. Fixture immutability

Source fixtures under `tests/fixtures/` are read-only test inputs.

A test that validates writing should copy the fixture into `tmp_path`.

Tests must not modify repository fixtures in place.

After a test run, version-control status should remain clean.

---

# 36. Fixture metadata

Complex captured fixtures should include metadata.

Example:

```json
{
  "fixture_id": "gf-type-expected-inferred-01",
  "gf_version": "3.x",
  "platform": "windows",
  "operation_kind": "compile",
  "exit_code": 1,
  "expected_pattern_ids": ["DP-GFTYPE-001"]
}
```

Do not claim an exact GF version when the fixture source did not record it.

Use:

```text
unknown
```

rather than inventing metadata.

---

# 37. Model builders

Tests should use shared fixture builders for large models.

Canonical helpers:

```python
make_app_config(...)
make_project_config(...)
make_run_config(...)
make_run_paths(...)
make_process_result(...)
make_compile_summary(...)
make_file_result(...)
make_scenario_result(...)
make_run_result(...)
```

Builders should:

- provide canonical safe defaults;
- expose meaningful overrides;
- return real production models;
- use typed shared models at cross-component boundaries;
- remain test-only.

---

# 38. Avoiding fragile fixtures

Tests should not manually construct every field of a large result repeatedly.

That creates test drift when compatible fields are added.

Use builders, but ensure explicit tests still verify required fields and defaults.

A contract test should not hide the public model behind a builder completely.

---

# 39. `SimpleNamespace` migration

The inherited GF Audit tests use `SimpleNamespace` for some CLI and report fixtures.

This is acceptable for the historical baseline.

Cross-component tests use actual typed models because:

- field mistakes should fail early;
- serialization meaning matters;
- status semantics are contractual;
- dynamic attributes are prohibited.

`SimpleNamespace` may remain for narrow protocol stubs that intentionally model only a small boundary.

---

# 40. Mocking policy

Mock:

- process execution when testing compiler logic;
- GF stage services when testing orchestration;
- filesystem errors through controlled fixture adapters;
- GUI dialogs at the dialog boundary;
- time through injected clocks.

Do not mock:

- the function under test;
- serialization when testing serialization;
- path containment when testing path containment;
- report builders when testing report output;
- process runner when the test’s purpose is process behavior.

---

# 41. Monkeypatch boundary

Monkeypatch stable public seams.

Good:

```text
scenario runner’s process executor dependency
runs coordinator’s validation-stage dependencies
CLI’s application service
clock provider
```

Avoid patching deeply nested private helpers whose names are not part of a contract.

---

# 42. Fake executables

The process suite requires controlled fake executables.

A single helper executable or Python script may implement modes:

```text
exit-zero
exit-nonzero
stdout
stderr
both-streams
sleep
spawn-child
ignore-terminate
read-stdin
write-artifact
emit-invalid-utf8
flood-output
print-args
print-env
```

The test invokes it through the same structured process request used for GF.

---

# 43. Fake executable requirements

A fake executable must:

- be deterministic;
- have bounded defaults;
- not require network access;
- avoid writing outside its requested fixture root;
- support Unicode;
- expose child-process behavior where platform permits;
- return documented exit codes;
- clean up through the process runner.

Platform wrapper scripts may differ, but behavior remains equivalent.

---

# 44. Fake GF adapter

A higher-level fake GF executable may recognize a small set of invocation patterns:

```text
--version
compile-success
compile-fail
pgf-success
scenario-success
scenario-marker-fail
```

It does not reproduce GF semantics.

It only provides controlled external-process evidence for framework integration tests.

Tests of actual GF semantics remain in the real-GF suite.

---

# 45. Captured GF evidence

Diagnostic tests use captured stdout and stderr fixtures.

They should test:

- stream identity;
- pattern precedence;
- Unicode;
- unknown fallback;
- version-sensitive behavior;
- false positives.

Captured output must remain unmodified.

Derived expected diagnostic records belong in separate fixture metadata or assertions.

---

# 46. Small real-GF fixture grammar

The real-GF suite uses a tiny language-neutral or synthetic fixture grammar.

It should contain:

```text
one abstract module
one successful concrete module
one intentionally failing module
one top-level entrypoint
one PGF build target
one parse example
one linearization example
one bounded generation example
one .gfs scenario
one gold file
```

The fixture exists to prove integration, not to test a full natural language.

---

# 47. Real-GF fixture constraints

The fixture must:

- be small;
- compile quickly;
- avoid depending on the active project;
- use documented RGL requirements;
- have stable expected behavior;
- identify the GF versions tested;
- avoid unbounded generation;
- remain independent of user state;
- use explicit paths.

---

# 48. Real-GF test setup

Real-GF tests obtain configuration from explicit test inputs.

Canonical test-harness variables:

```text
GF_WORDBENCH_TEST_GF_EXE
GF_WORDBENCH_TEST_RGL_ROOT
```

These are test-harness variables, not normal runtime configuration variables.

They must be documented in the development setup.

When absent:

- local `-m gf` may skip with a clear reason;
- release verification must fail before test execution or require them explicitly.

---

# 49. Skip policy

A skip is acceptable when a capability was not requested.

Examples:

- Windows-specific test on POSIX;
- GUI test without optional GUI environment in the default suite;
- real-GF test in the default no-GF suite.

A skip is not acceptable when:

- the release job promises that capability;
- GF was configured but cannot launch;
- a fixture is missing;
- a dependency import fails unexpectedly;
- setup is invalid.

Release jobs assert zero unexpected skips in required markers.

---

# 50. Xfail policy

`xfail` is exceptional.

An expected failure must include:

- issue or known-issue identifier;
- narrow condition;
- reason;
- strict mode where appropriate;
- removal criterion.

Preferred form:

```python
@pytest.mark.xfail(
    condition,
    reason="KNOWN-ISSUE-...",
    strict=True,
)
```

Broad non-strict xfails are prohibited.

---

# 51. Quarantine policy

Flaky tests must not be silently removed from release gates.

A temporary quarantine requires:

```text
owner
issue
observed failure
affected platforms
expiry or review date
replacement evidence
```

The underlying product behavior must remain tested elsewhere when possible.

Repeated reruns are not a substitute for fixing nondeterminism.

---

# 52. Unit test domains

The unit suite includes cohesive coverage for:

```text
config parsing
state parsing
path normalization
path containment
safe names
file selection
source scanner
command construction
diagnostic patterns
marker parser
normalization
gold comparator
classification
fingerprints
diff logic
result aggregation
release gates
report builders
manifest builder
migration helpers
```

---

# 53. Configuration tests

Required cases:

- canonical project configuration;
- missing required field;
- unknown major schema;
- optional field default;
- duplicate scenario ID;
- missing entrypoint;
- ordered checkpoints;
- absolute project path rejected;
- environment path excluded from project config;
- project identity remains stable;
- strict unknown field behavior.

---

# 54. Application-state tests

Required cases:

- missing state file;
- canonical state;
- corrupt JSON;
- unsupported schema;
- invalid path field;
- atomic save;
- legacy flat-state migration;
- state deletion does not damage project;
- no project entrypoints in state;
- no secrets;
- `is_running` legacy field discarded.

---

# 55. Path tests

Required cases include:

- project-relative path;
- run-relative path;
- environment absolute path;
- path with spaces;
- Unicode;
- Windows separators;
- POSIX separators;
- drive-relative Windows path rejection;
- `..` escape;
- symlink escape;
- junction escape;
- output/source overlap;
- duplicate GF path;
- RGL aliases;
- deterministic run collision suffix;
- no inline environment interpolation.

---

# 56. File-selection tests

Required cases:

- configured glob;
- include regex;
- exclude regex;
- deterministic order;
- maximum file limit;
- target-file quick selection;
- checkpoint selection;
- missing target;
- path outside source root;
- duplicate path identity;
- Unicode filename;
- source directory empty.

---

# 57. Scanner tests

The inherited baseline already tests:

- suspicious token patterns;
- runtime string matching;
- untyped string patterns;
- trailing spaces;
- comments and strings;
- empty files;
- summary-log creation.

The scanner suite also tests:

- doubled GF quotes;
- nested comments if supported by scanner policy;
- CRLF;
- Unicode;
- malformed source;
- size limits;
- deterministic finding order;
- no conversion of scan findings into GF diagnostics;
- scan evidence path ownership.

---

# 58. Process tests

Required cases:

```text
valid request
invalid request
argument with spaces
empty argument
Unicode argument
explicit cwd
environment override
secret redaction
stdin none
stdin text
stdin file
stdout only
stderr only
both streams
zero exit
non-zero exit
launch failure
timeout
pre-launch cancellation
running cancellation
output limit
child termination
graceful termination
forced termination
invalid UTF-8
expected artifact exists
expected artifact absent
capture collision
path escape
```

---

# 59. Compiler tests

Component tests use fake process results.

Required cases:

- canonical command order;
- source file is the terminal source argument;
- GF path option;
- output directory option;
- CPU option enabled and disabled;
- successful compile;
- non-zero exit;
- timeout;
- launch failure;
- stdout diagnostic;
- stderr diagnostic;
- internal error;
- type error;
- syntax error;
- missing required `.gfo`;
- compile skipped;
- source not mutated;
- no causal classification in compiler;
- no report generation in compiler.

---

# 60. PGF builder tests

Required cases:

- deterministic entrypoint order;
- successful build;
- missing PGF with zero exit;
- empty PGF;
- non-zero exit;
- fatal diagnostic;
- timeout;
- launch failure;
- artifact collision;
- optimized mode;
- nonoptimized diagnostic mode;
- output below owned root;
- manifest registration;
- source and previous PGF not overwritten.

---

# 61. Diagnostic parser tests

Required active patterns:

```text
DP-PROC-001 timeout
DP-PROC-002 launch failure
DP-PROC-003 cancellation
DP-PROC-004 output limit
DP-GFINT-001 GeneratePMCFG
DP-GFTYPE-001 expected/inferred
DP-GFSYN-001 syntax/parse/unexpected token
DP-FALLBACK-001 useful nonzero line
DP-FALLBACK-002 nonzero no message
DP-ART-001 missing artifact
DP-NORM-001 normalization failure
DP-GOLD-001 gold mismatch
```

Every broad text pattern requires negative fixtures.

---

# 62. Classifier tests

Required cases:

- successful result → `ok`;
- self-referenced source failure → direct candidate;
- known failing provider reference → downstream candidate;
- no reliable relationship → ambiguous;
- scan-only noise;
- skipped;
- multiple blockers;
- deterministic blocker order;
- internal/process error policy;
- classifier does not change raw diagnostic kind;
- classifier does not launch tools.

---

# 63. Scenario registry tests

Required cases:

- required scenarios;
- optional scenarios;
- duplicate ID;
- missing script;
- deterministic order;
- mode filtering;
- checkpoint association;
- invalid path;
- invalid timeout;
- missing required gold;
- unsupported normalization version;
- expected section duplication;
- input path outside project.

---

# 64. Marker tests

Required cases:

```text
BEGIN then END
missing BEGIN
missing END
END before BEGIN
duplicate BEGIN
duplicate END
unexpected section
multiple ordered sections
Unicode surrounding output
marker phrase inside unrelated text
marker-free approved scenario
```

Marker parsing has one authoritative owner.

---

# 65. Scenario runner tests

Required cases:

- direct `.gfs` stdin;
- explicit working directory;
- scenario hash;
- successful markers;
- marker failure despite zero exit;
- non-zero exit;
- timeout;
- cancellation;
- output limit;
- fatal diagnostic;
- assertion failure;
- normalization success;
- normalization failure;
- gold match;
- gold mismatch;
- missing gold;
- prerequisite blocked;
- required versus optional aggregation;
- raw stdout/stderr ownership;
- normal run does not modify `.gfs` or `.gold`.

---

# 66. Normalization tests

Required cases:

- CRLF to LF;
- ANSI removal;
- declared run-root replacement;
- temporary-path replacement;
- prompt removal;
- stable marker handling;
- timing normalization;
- preserved abstract tree;
- preserved linearized Unicode;
- preserved ambiguity count;
- preserved missing-function list;
- preserved punctuation;
- incomplete-section evidence retained;
- unsupported version;
- idempotence where required.

A normalizer change affecting gold must update its version and fixtures deliberately.

---

# 67. Gold tests

Required cases:

- exact match;
- mismatch;
- missing gold;
- empty intentional gold;
- wrong scenario ID;
- wrong schema version;
- wrong normalization version;
- CRLF compatibility;
- terminating newline;
- Unicode;
- diff creation;
- no modification during validation;
- explicit updater changes only approved destination;
- updater atomicity;
- updater preserves prior file on failure.

---

# 68. Result-model tests

Required cases:

- safe defaults;
- immutable or controlled fields;
- enum validation;
- no shared mutable defaults;
- derived totals;
- status aggregation;
- process-state consistency;
- path class consistency;
- serialization subset;
- legacy adapter;
- new optional field default;
- unknown enum rejection at persisted boundary.

---

# 69. Diff tests

The inherited baseline already tests:

- latest older run selection;
- non-run directory exclusion;
- improved/regressed/new/removed;
- OK-to-fail regression;
- summary loading;
- legacy AI path alias;
- missing prior summary;
- `DiffEntry` results.

The suite includes:

- project identity filtering;
- schema-version validation;
- scenario diff entries;
- release-gate regression;
- malformed prior run;
- current-run exclusion;
- timestamp tie-breaking;
- run-relative artifact migration;
- deterministic order.

---

# 70. Report tests

Required reports:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
master.log
ALL_SCAN_LOGS.TXT
ALL_LOGS.TXT
details/
manifest.json
```

Tests must verify:

- correct owner writes each path;
- no report launches GF;
- no report changes `RunResult`;
- both stdout and stderr are referenced;
- deterministic order;
- UTF-8;
- LF;
- terminating newline for text;
- bounded excerpts;
- secret redaction;
- partial-run rendering;
- report-write failure isolation.

---

# 71. JSON report tests

Required cases:

- canonical schema identity;
- canonical schema version;
- producer metadata;
- UTC timestamps;
- integer durations;
- file results;
- scenario results;
- release gates;
- top errors;
- diff entries;
- project-relative paths;
- run-relative artifacts;
- environment paths;
- Unicode;
- deterministic arrays;
- no NaN;
- round-trip through canonical reader;
- atomic replacement.

---

# 72. Markdown report tests

Required cases:

- successful run;
- direct failure;
- downstream failure;
- ambiguous failure;
- framework error;
- failing required scenario;
- gold mismatch;
- release gate failure;
- scan finding with compile success;
- previous-run regression;
- missing optional sections;
- relative artifact links;
- terminating newline.

Golden report fixtures may be used when the stable layout is intentionally locked.

---

# 73. AI report tests

Required cases:

- required heading;
- bounded packet;
- direct failure first;
- downstream separated;
- ambiguous uncertainty preserved;
- failing scenario;
- raw evidence paths;
- truncated excerpt marker;
- no unsupported diagnosis;
- no secret argument;
- no full environment;
- no second execution;
- deterministic investigation order.

---

# 74. Top-error tests

Required cases:

- empty;
- one item;
- duplicates;
- same message with different kinds;
- descending count;
- message tie-break;
- tab removal;
- newline removal;
- Unicode;
- terminating newline.

---

# 75. Manifest tests

Required cases:

- all required artifacts;
- missing required artifact;
- optional artifact absent;
- size;
- SHA-256;
- deterministic path order;
- path containment;
- modified artifact detection;
- finalization timing;
- self-entry policy;
- atomic write;
- cleanup/export consumer compatibility.

---

# 76. CLI tests

Required cases:

- help;
- version;
- valid quick run;
- valid diagnostic run;
- release run;
- invalid project root;
- invalid GF executable;
- required target missing;
- validation `OK` exit code;
- validation `FAIL` exit code;
- framework `ERROR` exit code;
- cancellation exit behavior;
- resolved configuration display;
- no GUI dependency;
- no direct compiler import;
- no report-generation duplication.

CLI tests should patch the application service for unit/component behavior and use fake GF for integration behavior.

---

# 77. GUI tests

The GUI suite should focus on:

- state loading;
- field conversion;
- validation feedback;
- same `RunConfig` as CLI;
- run invocation through application boundary;
- progress-event handling;
- cancellation request;
- result rendering;
- artifact links;
- state save;
- GUI remains optional for CLI installation/runtime paths.

Avoid brittle pixel-level tests unless a stable visual requirement exists.

---

# 78. Launcher tests

Windows launcher tests should verify:

- repository root resolution;
- CLI launcher exit-code propagation;
- GUI launcher starts the intended entrypoint;
- paths containing spaces;
- no hidden audit semantics;
- Python application works without launchers;
- launcher environment changes are documented.

Where automated launcher execution is unreliable, static contract tests may inspect the scripts, supplemented by a Windows smoke test.

---

# 79. Dependency-direction tests

Contract tests inspect imports or architecture metadata to enforce:

```text
domain → no GUI, CLI, filesystem, process, JSON/TOML library or GF executable
application → domain and ports
adapters → ports and external systems
entrypoints → application
bootstrap → application, ports and adapters
reporting → no validation execution adapters
diagnostics → no process launch outside the external-tool port
projects → no GUI state authority
functional module → no private internals of another functional module
GF Wordbench → no gf-portfolio runtime, storage, configuration or private schemas
```

Expected high-level directions remain intact.

A dependency test parses Python imports and package metadata rather than relying on naive substring matches.

---

# 80. Artifact-ownership tests

Verify:

- each canonical artifact path has one owner;
- `RunPaths` supplies canonical paths;
- no duplicate filename constants exist outside the owner where detectable;
- observers do not rewrite raw files;
- reports do not write compile or scenario streams;
- normal validation does not write gold;
- manifest writer does not alter artifacts;
- detail writer copies only validated sources.

---

# 81. Anti-drift tests

Required automated checks:

```text
documented provider exists
documented consumer exists
public contract symbol or port exists
required model field exists
status values match their owner reference
schema IDs and versions match the persisted-schema lock
artifact filenames match the runs-owned path registry
reporting returns owned paths
reporting imports no execution adapters
entrypoints do not bypass application use cases
framework source contains no active-language defaults
normal validation does not modify gold
project template remains language-neutral
one workspace resolves one active project
one run resolves one active project and target
Wordbench imports no gf-portfolio package
Wordbench schemas contain no Portfolio registry or private state
Wordbench tests and release gates pass with gf-portfolio absent
```

These checks supplement review of ADRs and contract locks; they do not replace it.

---

# 82. Schema fixture classes

For every persisted schema, maintain:

```text
canonical minimal
canonical complete
compatible minor extension
invalid missing required
invalid field type
invalid enum
unsupported major
legacy supported
legacy ambiguous
```

Each fixture identifies the expected reader behavior.

---

# 83. Migration tests

A migration test proves:

1. legacy source remains unchanged;
2. reader identifies legacy shape;
3. fields map correctly;
4. ambiguous values produce warnings;
5. canonical target validates;
6. canonical writer emits only current names;
7. repeated migration is safe or explicitly rejected;
8. failed migration does not destroy valid data.

---

# 84. Project migration tests

Required cases:

- legacy state paths to environment state;
- old modes `file` and `all`;
- old AI report aliases;
- absolute source paths to project-relative;
- absolute artifact paths to run-relative;
- SHA-1 legacy fingerprints;
- top-error mapping to array;
- language fields removed from state;
- unknown project identity handled explicitly.

---

# 85. Security tests

Required domains:

```text
shell injection
argument boundaries
path traversal
symlink/junction escape
secret redaction
environment leakage
scenario OS escape
output exhaustion
unsafe artifact overwrite
unsafe gold update
diagnostic-mentioned path access
malicious report text
invalid Unicode
```

Security tests assert safe failure and evidence preservation.

---

# 86. Shell-injection tests

Use arguments containing:

```text
&
|
>
<
;
$()
backticks
quotes
spaces
```

Verify:

- they remain one argument or are rejected by the owning validator;
- no second process starts;
- no unintended file is created;
- rendered display command is not re-executed.

---

# 87. Path-security tests

Verify rejection of:

```text
../escape
absolute project path
drive-relative Windows path
UNC project path
symlink out of project
junction out of run
source file as report destination
gold file as raw capture destination
```

---

# 88. Secret-redaction tests

Provide fake sensitive:

```text
argument
environment value
path segment where export redaction applies
```

Verify:

- child receives the real value when required;
- logs show `<redacted>`;
- summaries omit the value;
- environment dumps are absent;
- failures do not reveal the secret through exception text.

---

# 89. Output-exhaustion tests

Use a controlled flood-output process.

Verify:

- output limit is enforced;
- process tree is terminated;
- partial evidence remains;
- truncation/cancellation is explicit;
- scenario or process status is `ERROR`;
- gold comparison is not performed;
- test itself remains bounded.

---

# 90. End-to-end fake-GF tests

A fake-GF E2E fixture covers:

### Success

```text
project loads
files selected
scan executes
compile succeeds
scenario succeeds
reports written
manifest validates
exit code is success
```

### Validation failure

```text
compile or scenario FAIL
raw evidence preserved
summary reports FAIL
CLI returns validation-failure code
```

### Framework error

```text
launch or report contract ERROR
partial evidence preserved
summary reports ERROR
CLI returns runtime-error code
```

---

# 91. End-to-end real-GF tests

Required release E2E flow:

```text
temporary canonical project
    → resolved real GF
    → version probe
    → source compile
    → PGF build
    → required scenario
    → normalization
    → gold comparison
    → reports
    → manifest verification
```

The fixture remains small enough for every release candidate.

---

# 92. Release-mode tests

Required cases:

- all gates pass;
- source compile fails;
- required scenario fails;
- required scenario skipped;
- required gold missing;
- gold mismatch;
- PGF missing despite zero exit;
- manifest missing required report;
- report failure;
- unsupported GF version strict mode;
- unresolved known blocking issue;
- optional scenario failure according to policy.

A release gate must not be inferred only from file totals.

---

# 93. Performance tests

Performance tests are limited and targeted.

Useful checks:

- no unbounded output memory;
- deterministic bounded scenario time;
- report generation on a large synthetic result;
- file selection on a large synthetic tree;
- diagnostic parser on bounded large logs.

Performance thresholds must account for CI variance.

Avoid fragile microbenchmarks in the mandatory suite.

---

# 94. Coverage policy

Coverage is a diagnostic and release gate, not a quality substitute.

Coverage policy:

```text
overall line coverage minimum: 85%
changed production lines minimum: 90%
critical modules branch coverage minimum: 90%
```

Critical modules include:

```text
process execution
path containment
schema migration
release gates
gold update
artifact manifest
```

A threshold change is explicit, reviewed and recorded.

A threshold is never lowered silently to pass a release.

---

## 95. Coverage exclusions

Legitimate exclusions may include:

- defensive platform branch impossible on the current runner;
- `TYPE_CHECKING`;
- explicit unreachable assertion;
- GUI entrypoint wrapper;
- version metadata constant.

Every `pragma: no cover` has a documented reason.

Do not exclude complex error paths merely because they are difficult to test.

---

## 96. Branch coverage

Line coverage alone is insufficient for:

- status aggregation;
- migration branches;
- timeout/cancellation;
- release gates;
- path containment;
- schema-version handling;
- report failure isolation.

Branch coverage is enabled in release coverage runs.

Canonical command:

```text
python -m pytest \
  --cov=app \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml
```

---

# 97. Static analysis

Testing is supplemented by:

```text
ruff check
ruff format --check
mypy
```

Canonical commands:

```text
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests
```

Whether tests are included in strict mypy checking may be phased in.

Production code must remain fully typed according to project policy.

---

# 98. Formatting

The formatter is not a semantic test.

However, formatting checks prevent unrelated style drift and simplify review.

Generated fixture data and gold output must not be reformatted by Python formatters.

---

# 99. Type-checking focus

Type checking especially protects:

```text
shared models
optional paths
schema readers
status enums
process results
report inputs
migration return types
```

Avoid pervasive `Any` at architectural boundaries.

Tests may use typed builders to expose model drift.

---

# 100. Package-build tests

A release candidate tests:

```text
build wheel
build source distribution when supported
install into clean environment
import app
run CLI --help
run CLI --version
run no-GF configuration command
```

The installed package must not depend on repository-relative import accidents.

---

# 101. Documentation tests

Documentation checks verify:

- referenced canonical files exist;
- lock IDs are unique;
- schema IDs match runtime constants;
- documented commands parse where feasible;
- project and template documentation trees align;
- no active-language data appears in generic templates;
- no outdated canonical mode names are presented as current;
- no obsolete GF Audit artifact names are emitted as canonical.

Code-block execution is required only for selected stable examples.

---

# 102. Template tests

`templates/project/` must be tested as a real initialization source.

Verify:

- expected files exist;
- placeholders are present only where allowed;
- no active-language name remains;
- no local absolute path remains;
- initialized project config validates after required values are supplied;
- template and active project structure match the documented contract;
- no generated run artifact is included;
- gold files are absent or intentionally generic.

---

# 103. Snapshot and golden tests

Golden testing is appropriate for:

- normalized scenario output;
- canonical human reports;
- stable text manifests where applicable;
- selected CLI output;
- diagnostic rendering.

Golden testing is not appropriate for:

- raw timestamps;
- durations;
- absolute temporary paths;
- process IDs;
- unordered data;
- binary GF artifacts.

Normalize only documented instability.

---

# 104. Updating test golds

Test golden files are updated deliberately.

Required workflow:

1. run the focused test;
2. inspect the diff;
3. verify whether behavior or formatting intentionally changed;
4. update the contract/schema version if required;
5. update all affected tests;
6. record material change in changelog;
7. rerun full relevant suite.

A command that updates test golds must not also approve project language golds implicitly.

---

# 105. Failure messages

Assertions explain the contract.

Prefer:

```python
assert result.execution_state == "timed_out"
```

with useful model repr or a focused custom assertion.

Avoid assertions that only say:

```text
False is not true
```

Shared custom assertions may include:

```text
assert_valid_summary
assert_manifest_complete
assert_path_contained
assert_gold_unchanged
assert_no_process_leaks
```

---

# 106. Multiple assertions

A test may assert a coherent result contract:

```text
timeout state
exit code absent
partial logs exist
termination attempted
```

This is preferable to four duplicated setups.

Do not combine unrelated features in one test merely to reduce test count.

---

# 107. Parameterization

Use parameterization for:

- status combinations;
- path forms;
- diagnostic patterns;
- schema versions;
- supported operation kinds;
- platform-safe arguments;
- report ordering.

Parameter IDs are readable.

Do not hide complex distinct scenarios in one unreadable parameter matrix.

---

# 108. Test naming

Canonical form:

```text
test_<unit>_<condition>_<expected>
```

Examples:

```text
test_run_process_timeout_preserves_partial_streams
test_project_loader_absolute_source_path_raises
test_release_gate_missing_required_pgf_fails
test_summary_writer_paths_are_run_relative
```

Names communicate the contract without reading the body.

---

# 109. Test documentation

A docstring is useful when:

- the contract is nonobvious;
- the fixture reproduces an upstream GF behavior;
- a regression needs historical context;
- platform behavior is subtle.

Do not add docstrings that merely repeat the test name.

---

# 110. Regression tests

Every reproducible fixed defect receives a regression test.

The test should:

- fail before the fix;
- pass after the fix;
- target the smallest reliable boundary;
- identify the defect or changelog context where useful.

Examples from the inherited baseline include:

- doubled GF quotes in scanner strings;
- outdated CLI report ownership;
- complete top-error output;
- report assertion syntax;
- centralized version metadata.

---

# 111. Bug-fix workflow

For a reproducible bug:

```text
1. preserve evidence
2. write failing test
3. identify owning layer
4. implement fix
5. run focused suite
6. run contract/schema suite when affected
7. run default suite
8. run real-GF suite when external behavior changed
9. update documentation and changelog
```

An emergency safety fix may precede the test only when delay risks data loss or unsafe execution.

The test must be added before the repair is considered closed.

---

# 112. Contract-change workflow

A contract-changing change set must include:

```text
[ ] contract ID identified
[ ] provider tests updated
[ ] consumer tests updated
[ ] model/schema tests updated
[ ] artifact ownership tested
[ ] error behavior tested
[ ] compatibility tested
[ ] migration tested
[ ] real-GF integration reviewed
[ ] documentation updated
[ ] changelog updated
```

---

# 113. Schema-change workflow

A persisted-schema change requires:

```text
[ ] schema version classified
[ ] canonical writer updated
[ ] canonical reader updated
[ ] old reader expectations reviewed
[ ] migration added
[ ] canonical minimal fixture updated
[ ] canonical complete fixture updated
[ ] invalid fixtures updated
[ ] round-trip test updated
[ ] deterministic serialization tested
[ ] path semantics tested
[ ] lock updated
```

---

# 114. External-GF change workflow

A GF command or interpretation change requires:

```text
[ ] affected external contract identified
[ ] supported GF versions identified
[ ] command fixture updated
[ ] process test updated
[ ] fake-GF integration updated
[ ] real-GF integration updated
[ ] stdout and stderr fixtures reviewed
[ ] diagnostic parser reviewed
[ ] artifact checks reviewed
[ ] normalization/gold reviewed
[ ] compatibility behavior documented
```

---

# 115. Local development sequence

Focused development loop:

```text
1. run test file for changed owner
2. run related contract tests
3. run related schema tests
4. run fast local suite
5. run ruff
6. run mypy
7. run real-GF tests when affected
```

Do not run only the newly added test and consider the change complete.

---

# 116. Pre-commit verification

Minimum pre-commit or pre-push command set:

```text
python -m ruff format --check .
python -m ruff check .
python -m mypy app
python -m pytest -m "not gf and not gui and not slow"
```

A developer changing schemas, process behavior, or GF integration should also run the focused required suites.

---

# 117. CI stages

CI stages:

```text
1. static
2. unit-component
3. contracts-schemas
4. platform
5. real-gf
6. end-to-end
7. package
8. release-verification
```

Independent stages improve failure diagnosis.

---

## 118. Static CI stage

Runs:

```text
ruff format --check
ruff check
mypy
documentation consistency
dependency-direction checks
independent-product boundary checks
```

No GF is required.

---

## 119. Unit-component CI stage

Runs:

```text
unit
component
default fake-process integration
```

Produces coverage.

No GF is required.

---

## 120. Contracts-schemas CI stage

Runs:

```text
contract tests
schema tests
migration tests
artifact ownership
anti-drift checks
Wordbench-without-Portfolio checks
```

This stage is mandatory for every change.

---

## 121. Platform CI stage

At minimum:

- Windows platform suite;
- POSIX platform suite.

Tests:

- paths with spaces;
- Unicode;
- CRLF;
- process timeout;
- child termination;
- native executable handling;
- atomic writes;
- symlink/junction containment as supported.

---

## 122. Real-GF CI stage

Runs on environments with an explicit tested GF installation.

It must publish failure artifacts:

```text
stdout
stderr
resolved command
GF version
fixture project
run summary
manifest when generated
```

The job fails if required GF tests are unexpectedly skipped.

---

## 123. End-to-end CI stage

Runs:

- fake-GF E2E on required platforms;
- real-GF E2E on the release integration environment.

Verifies generated run directory and manifest.

---

## 124. Package CI stage

Builds and installs the package in a clean environment.

Verifies console entrypoints and optional GUI packaging where supported.

---

# 125. CI artifact retention

On failure, retain only useful bounded evidence.

Canonical:

```text
pytest report
coverage XML
failed test logs
fake-process streams
real-GF streams
generated summary.json
generated summary.md
manifest.json
gold diffs
```

Do not upload:

- secrets;
- complete environment dumps;
- unrelated user files;
- huge runaway logs without explicit truncation.

---

# 126. Parallel test execution

Parallel test execution is optional.

Do not add it until:

- tests are isolated;
- run directory names are collision-safe;
- environment mutation is controlled;
- process tests own distinct paths;
- order independence is proven.

A parallelization plugin is not required in version `1.0`.

Correctness and determinism come first.

---

# 127. Test order independence

The suite must pass in any collection order.

Tests must not depend on:

- previous test state;
- global run history;
- fixture modification;
- shared output directory;
- cached active project;
- GUI singleton left alive;
- child process left running.

Order-dependent failures are defects.

---

# 128. Resource cleanup assertions

Process and GUI tests should verify cleanup where relevant.

Examples:

- child process no longer exists;
- capture handles closed;
- temporary file removed;
- state file replaced atomically;
- no source or gold modification;
- GUI worker stopped;
- run directory finalized.

Cleanup failure must not be hidden by a passing primary assertion.

---

# 129. Flakiness prevention

Avoid:

- fixed arbitrary sleeps;
- unbounded polling;
- exact duration assertions;
- network dependencies;
- shared ports;
- global temp filenames;
- relying on process scheduling order;
- testing raw interleaving of stdout and stderr when it is not guaranteed.

Use deadlines and condition polling with bounded intervals.

---

# 130. Test timeout policy

The test suite itself should have bounded execution through CI job timeouts.

Individual tests that launch processes must use shorter controlled timeouts.

A test should fail rather than hang if the process runner’s timeout logic regresses.

The project may add a pytest timeout plugin later if justified.

It is not mandatory in version `1.0`.

---

# 131. Failure triage

When a test fails, classify first:

```text
test defect
product defect
fixture drift
schema drift
contract drift
GF-version incompatibility
platform-specific defect
environment misconfiguration
flakiness
```

Do not update expected output until the category is known.

---

# 132. Real-GF failure triage

Capture:

```text
GF version
platform
command array
working directory
GF path list
stdout
stderr
exit code
artifact observations
fixture revision
```

Compare with the external-tool contract.

Do not normalize away an upstream behavior change merely to restore a green suite.

---

# 133. Golden-diff triage

For a gold mismatch:

1. confirm normalization version;
2. inspect raw output;
3. inspect normalized output;
4. inspect expected gold;
5. determine linguistic, framework, environment, or GF-version cause;
6. update code or gold deliberately;
7. rerun focused and broader scenario suites.

---

# 134. Coverage regression triage

A coverage drop may mean:

- new code lacks tests;
- generated/unreachable code was added;
- test discovery changed;
- branch behavior changed;
- files entered coverage unexpectedly.

Do not immediately lower the threshold.

---

# 135. Legacy GF Audit evidence preserved

The GF Audit suite provides five historical test modules:

```text
tests/test_classifier.py
tests/test_diff.py
tests/test_reports.py
tests/test_scanner.py
tests/test_smoke.py
```

Its development configuration includes:

```text
pytest
pytest-cov
ruff
mypy
```

The following evidence remains part of Wordbench compatibility coverage:

- failure classification;
- previous-run comparison;
- AI-ready reporting;
- static scanning;
- CLI smoke and exit behavior;
- improved, regressed, new and removed comparison states;
- legacy AI report path loading;
- scanner exclusion of comments and strings;
- scanner empty-file handling;
- report generation and top-error rendering.

These tests are migrated or wrapped without discarding their regression value.

---

# 136. Legacy compatibility obligations

Compatibility tests preserve:

```text
legacy mode aliases
legacy state loading
legacy run-summary shapes
legacy AI report aliases
legacy source fingerprints
legacy top-error structures
legacy scanner rules
legacy CLI exit semantics where retained by contract
```

Canonical writers emit only Wordbench formats and names.

---

# 137. Wordbench coverage domains

The Wordbench suite covers:

```text
project.toml
application-state schema
runs-owned path registry
external-tool port and process adapter
launch failure
cancellation
process-tree termination
output limits
real GF
PGF build
native .gfs scenarios
markers
normalization
gold comparison
manifest
release gates
schema versions
migration matrix
CLI and GUI application-boundary equivalence
dependency directions
security containment
independent-product boundary
```

---

# 138. Legacy fixture migration

Cross-component fixtures use typed production models.

`SimpleNamespace` remains only for narrow protocol stubs where dynamic shape is the intended boundary.

Legacy tests retain recognizable names, fixtures and historical evidence when moved into the canonical directory structure.

---

# 139. Test migration rule

Moving a test file is not improved coverage by itself.

During migration:

- preserve test intent;
- keep regression history recognizable;
- avoid rewriting every assertion simultaneously with source changes;
- add missing contract tests separately;
- remove a legacy test only after equivalent or stronger proof exists;
- preserve legacy inputs unchanged until canonical migration succeeds.

---

# 140. Required release gates

A GF Wordbench framework release requires:

```text
[ ] formatting passes
[ ] lint passes
[ ] type checking passes
[ ] default unit/component suite passes
[ ] contract suite passes
[ ] schema suite passes
[ ] migration suite passes
[ ] security-critical suite passes
[ ] Windows required suite passes
[ ] POSIX required suite passes
[ ] real-GF integration passes
[ ] fake-GF E2E passes
[ ] real-GF release E2E passes
[ ] package build/install smoke passes
[ ] required coverage threshold passes
[ ] no unexpected required skips
[ ] no strict xpass
[ ] documentation consistency passes
[ ] repository fixtures remain unchanged
[ ] Wordbench passes without `gf-portfolio` installed or configured
```

---

# 141. Project versus framework release tests

Framework release tests prove GF Wordbench itself.

Active-language release tests prove the current project.

They are related but distinct.

A framework release must not depend on the active project’s linguistic correctness.

A project release records:

```text
GF Wordbench version
GF version
project revision
required scenario results
PGF artifact
manifest
```

---

# 142. Manual testing

Manual testing is allowed only for behavior that cannot reasonably be automated.

Examples may include:

- selected GUI usability review;
- installer presentation;
- operating-system signing prompt;
- visual path picker behavior.

Manual evidence must record:

```text
test ID
environment
steps
expected result
actual result
reviewer
date
evidence
```

Manual testing must not replace automatable contract checks.

---

# 143. Test documentation ownership

This file owns the framework-wide testing strategy.

Detailed test lists may also appear in domain documents.

Duplication rules:

- domain document defines domain-specific required cases;
- this document defines suite organization and release integration;
- test code is the executable proof;
- contract locks define which proof is mandatory.

When lists conflict, the stricter applicable normative requirement must be reconciled rather than ignored.

---

# 144. Adding a new test category

A new category requires:

```text
purpose
owner
marker if needed
default-suite inclusion
CI stage
fixtures
failure evidence
release requirement
documentation
```

Do not create a marker or CI job for a single isolated test unless the capability boundary is stable.

---

# 145. Adding a new external tool

Before testing a new external tool, its contract must define:

```text
executable
version
arguments
working directory
environment
stdin
stdout
stderr
timeout
artifacts
success
failure
security
compatibility
```

Tests then cover the same boundary structure used for GF.

---

# 146. Prohibited testing behavior

The following are prohibited:

- tests passing only because GF exists on the developer’s `PATH`;
- tests depending on global `GF_LIB_PATH`;
- normal tests modifying project golds;
- tests modifying repository fixtures in place;
- swallowing unexpected exceptions;
- broad warning suppression;
- broad non-strict xfail;
- network dependence in the core suite;
- unbounded generation;
- unbounded process output;
- shell command strings built from test project input;
- asserting only stdout when stderr is contractually relevant;
- treating zero exit as complete success;
- deleting failure evidence before assertion;
- reports being tested by rerunning audit stages;
- schema tests using report prose as machine truth;
- exact assertions on unstable absolute temp paths;
- fixed sleeps as synchronization;
- silently skipped required release tests;
- lowering coverage solely to pass a release;
- updating gold without diff review;
- mocking the behavior the test claims to prove.

---

# 147. Drift indicators

Testing drift exists when:

- a public contract changes but only unit tests change;
- a schema changes without migration fixtures;
- a new result field has no builder or serializer test;
- CLI and GUI tests use different configuration logic;
- process tests omit stderr;
- a real-GF command changes without a real-GF test update;
- normalization changes without gold review;
- a report imports and executes a stage in tests;
- artifact names are duplicated in test setup;
- tests create noncanonical paths that production never accepts;
- current GF Audit mode names remain canonical in new tests;
- active-language names appear in framework fixtures;
- test results depend on execution order;
- required tests are marked optional;
- widespread gold changes are approved without cause analysis;
- a flaky test is rerun until passing;
- coverage rises while critical branches remain untested;
- a release job skips its promised platform or GF capability.

Any drift indicator requires review before release.

---

# 148. Test review checklist

```text
[ ] Test targets a documented behavior
[ ] Correct layer is used
[ ] Fixture is deterministic
[ ] Environment is controlled
[ ] No repository fixture is modified
[ ] Both stdout and stderr are considered when relevant
[ ] Timeout is bounded
[ ] Failure evidence is retained
[ ] Assertion explains the contract
[ ] Negative case exists for broad matching
[ ] Platform assumption is marked
[ ] Real-GF requirement is marked
[ ] Skip behavior is intentional
[ ] No hidden global state remains
[ ] Related contract/schema tests are updated
[ ] Product boundary remains independent from `gf-portfolio`
[ ] Gold changes were reviewed
```

---

# 149. Suite health checklist

```text
[ ] Fast suite remains fast
[ ] Default suite requires no GF
[ ] Real-GF suite is separately runnable
[ ] Required release suite has no unexpected skips
[ ] Test order is independent
[ ] Process tests leave no child processes
[ ] Temporary paths are isolated
[ ] Fixture inventory is documented
[ ] Contract tests cover ownership
[ ] Schema tests cover every persisted root
[ ] Migration tests cover every supported legacy format
[ ] Windows behavior is genuinely exercised
[ ] POSIX behavior is genuinely exercised
[ ] Coverage reports are generated
[ ] Flaky tests have no silent quarantine
[ ] Wordbench suite passes with `gf-portfolio` absent
```

---

# 150. Invariants

1. The default suite does not require GF.
2. Real-GF tests are explicit and required for release.
3. Unit tests do not replace contract tests.
4. Contract tests do not replace end-to-end tests.
5. End-to-end tests do not replace focused unit tests.
6. Persisted schemas have canonical, invalid, and legacy fixtures.
7. Every migration preserves its source until success.
8. Every external process test is bounded.
9. Stdout and stderr are tested separately.
10. Timeout, cancellation, and launch failure are distinct.
11. Missing required artifacts are tested even with zero exit.
12. Normal validation never modifies gold.
13. Normalization changes require versioned test updates.
14. Reports are tested as passive consumers.
15. Artifact ownership is tested.
16. Dependency direction is tested.
17. CLI and GUI share configuration semantics.
18. Windows paths with spaces and Unicode are tested.
19. Ambient developer environment cannot determine success.
20. Test fixtures are immutable.
21. Required release tests cannot skip silently.
22. Xfail is narrow, strict, and temporary.
23. Coverage gates protect critical code but do not replace assertions.
24. A reproducible bug receives a regression test.
25. A contract change updates provider, consumers, schemas, fixtures, and integration evidence.
26. Framework tests remain language-neutral.
27. Active-language linguistic tests remain project-owned.
28. Package installation is tested in a clean environment.
29. Failed integration tests preserve diagnostic evidence.
30. Testing complexity exists only to prove a real architectural, compatibility, platform, or safety boundary.
31. Wordbench tests, validation and release verification require no `gf-portfolio` runtime, storage, configuration or service.

---

# 151. Governing rule

GF Wordbench testing follows one proof chain:

```text
pure behavior
    → component behavior
    → interfile contract
    → persisted schema
    → external process contract
    → real GF behavior
    → complete run artifacts
    → release decision
```

A release is valid only when every required link in that chain is proven by executable, repeatable evidence.
