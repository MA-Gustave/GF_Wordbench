# GF Wordbench — Development Setup

**Document ID:** `GF-WB-DEVELOPMENT-SETUP`  
**Status:** Final developer guide  
**Applies to:** Framework contributors, maintainers, reviewers, CI maintainers, and integration-test authors  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\development\DEVELOPMENT_SETUP.md`  
**Guide version:** `1.0.0`  
**Last reviewed:** `2026-07-21`

---

## 1. Purpose

This guide defines the supported local development setup for GF Wordbench.

It covers:

- repository preparation;
- Python environment creation;
- editable installation;
- development dependencies;
- GF and RGL configuration;
- unit, contract, integration and GUI tests;
- linting, formatting and type checking;
- local CLI and GUI execution;
- package verification;
- clean-room verification;
- common setup failures;
- contributor completion criteria.

This document is for developing the GF Wordbench framework.

For using GF Wordbench only, read:

```text
docs/usage/INSTALLATION.md
docs/usage/QUICK_START.md
```

---

## 2. Development principles

The development environment must preserve these rules:

```text
one active language project per repository copy
framework code remains language-neutral
GF remains the execution engine
tests do not depend on one developer's undocumented machine state
external processes use explicit paths and finite timeouts
raw evidence is preserved before interpretation
persisted schema changes are versioned and migrated
CLI and GUI use the same application contracts
```

A local setup is acceptable only when another contributor can reproduce it from the repository and documented prerequisites.

---

## 3. Supported baseline

The final baseline is:

```text
Python 3.11 or newer supported version
Hatchling build backend
PySide6 for the GUI
pytest for tests
pytest-cov for coverage
Ruff for linting and formatting checks
mypy for static type checking
Grammatical Framework for real integration tests
GF Resource Grammar Library for project integration tests
```

The authoritative version ranges remain in:

```text
pyproject.toml
```

Do not duplicate dependency version pins in source modules.

Documentation may describe minimum capabilities, but package metadata owns installable versions.

---

## 4. Repository root

Examples use:

```text
C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench
```

Open a terminal in the repository root.

PowerShell:

```powershell
Set-Location "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench"
```

POSIX shell:

```bash
cd /path/to/GF_Wordbench/GF_Wordbench
```

Verify the expected top-level structure:

```text
app/
docs/
project/
templates/
tests/
pyproject.toml
README.md
```

Additional development and launcher files may exist.

---

## 5. Logical source layout

The final framework is organized around these responsibilities:

```text
app/
├── __init__.py
├── bootstrap.py
├── config.py
├── models.py
├── state.py
├── main_cli.py
├── main_gui.py
├── audit/
├── gui/
├── reports/
├── utils/
└── schema or project-loading modules as finalized

tests/
├── unit or focused module tests
├── contract tests
├── integration tests
└── fixtures

project/
├── project.toml
├── docs/
└── validation/

templates/
└── project/
```

Important boundaries:

```text
CLI and GUI
    → bootstrap
        → audit orchestration
            → validation stages
                → process utilities
                    → GF
```

Reports consume structured results.

Reports must not invoke validation stages or GF.

---

## 6. Clone or copy the repository

Using Git:

```powershell
git clone <repository-url>
Set-Location GF_Wordbench\GF_Wordbench
```

When working from an existing local checkout:

```powershell
git status
git branch --show-current
```

Before changing framework code, confirm that generated run directories and local state are not staged.

Typical local-only files include:

```text
.venv/
.gf_wordbench_state.json
run_*/
coverage output
tool caches
temporary project fixtures
```

The exact ignore policy belongs to `.gitignore`.

---

## 7. Create a virtual environment

Use a repository-local virtual environment.

### 7.1 Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 7.2 Windows Command Prompt

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### 7.3 POSIX

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Confirm the active interpreter:

```powershell
python -c "import sys; print(sys.executable); print(sys.version)"
```

The executable should resolve inside `.venv`.

---

## 8. PowerShell execution-policy issue

When PowerShell blocks activation, inspect the policy:

```powershell
Get-ExecutionPolicy -List
```

A common per-user development setting is:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Apply security policy according to the local organization.

Changing PowerShell policy is not required when using:

```powershell
.\.venv\Scripts\python.exe
```

directly.

Example:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

---

## 9. Upgrade packaging tools

Inside the virtual environment:

```powershell
python -m pip install --upgrade pip
```

When the project requires an explicit recent packaging tool:

```powershell
python -m pip install --upgrade packaging
```

Do not globally upgrade unrelated packages to repair one project environment.

---

## 10. Install the framework in editable mode

Install runtime dependencies and an editable package:

```powershell
python -m pip install -e .
```

For framework development, install the development dependency group:

```powershell
python -m pip install -e ".[dev]"
```

Editable installation ensures that source changes under `app/` are used without reinstalling after every edit.

Reinstall when:

- `pyproject.toml` changes;
- console entrypoints change;
- dependency groups change;
- package layout changes;
- the editable installation becomes inconsistent.

Reinstall command:

```powershell
python -m pip install --upgrade --force-reinstall -e ".[dev]"
```

Use force reinstall only when ordinary editable installation is insufficient.

---

## 11. Optional `uv` workflow

`uv` may be used as a local environment and command runner when supported by the repository.

Example:

```powershell
uv venv
uv pip install -e ".[dev]"
```

Run a command:

```powershell
uv run python -m pytest
```

The canonical project behavior must not depend on `uv`.

A standard Python virtual environment remains supported.

Windows launchers may discover `uv` as a convenience, but launchers are not the source of application semantics.

---

## 12. Verify installed dependencies

Check the package:

```powershell
python -m pip show gf-wordbench
```

During the package-name migration, the installed predecessor name may still appear until `pyproject.toml` is updated.

Inspect the environment:

```powershell
python -m pip list
```

Verify core imports:

```powershell
python -c "import app; print(app.__file__)"
python -c "import PySide6; print(PySide6.__version__)"
python -c "import pytest; print(pytest.__version__)"
```

Verify development tools:

```powershell
python -m ruff --version
python -m mypy --version
python -m pytest --version
```

A missing development tool normally means the `dev` extra was not installed.

---

## 13. Verify the package entrypoint

Canonical final CLI:

```powershell
gf-wordbench --version
gf-wordbench --help
```

Source-module fallback during development:

```powershell
python -m app.main_cli --help
```

GUI entry:

```powershell
gf-wordbench gui
```

Source-module fallback:

```powershell
python -m app.main_gui
```

The installed console command is the preferred public interface.

The module entrypoint is useful for debugging package installation.

---

## 14. Install and verify Grammatical Framework

GF is required for real toolchain integration tests and project validation.

It is not required for most pure unit tests.

Verify the selected executable directly.

PowerShell:

```powershell
& "C:\tools\gf\gf.exe" --version
```

Command Prompt:

```bat
"C:\tools\gf\gf.exe" --version
```

POSIX:

```bash
/path/to/gf --version
```

Record:

```text
absolute executable path
reported version
installation source
supported-version status
```

Do not assume that the first `gf` on `PATH` is the intended version.

---

## 15. Install or locate the RGL

Real project tests normally require an RGL source root or equivalent GF library root.

Example:

```text
C:\work\gf-rgl\src
```

Confirm that the expected source directories exist.

PowerShell example:

```powershell
Test-Path "C:\work\gf-rgl\src"
Get-ChildItem "C:\work\gf-rgl\src" | Select-Object -First 10
```

The active project supplies ordered GF path parts.

The local environment supplies the machine-specific RGL root.

Do not hardcode the local absolute RGL root in portable `project/project.toml`.

---

## 16. Prepare the active project

A framework checkout contains one active project or a project template ready for initialization.

Verify:

```text
project/project.toml
project/docs/
project/validation/
```

Run the configuration checker:

```powershell
gf-wordbench config check `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

Configuration checking should occur before real integration tests.

Framework unit tests must not require the active language project unless the test is explicitly a project-integration test.

---

## 17. Development environment variables

Environment variables may be used for local convenience only when they are documented by:

```text
docs/configuration/ENVIRONMENT_AND_PATHS.md
```

Rules:

- explicit test or command arguments take precedence;
- tests must not depend on hidden user-level variables;
- environment fallback must be visible;
- secrets must not be dumped into reports;
- child-process overrides must be scoped to that process;
- framework tests must clean up temporary environment changes.

Do not add a new environment variable only in one module.

A new environment variable requires:

```text
single owner
documentation
precedence rule
validation
tests
security review
```

---

## 18. Run the fast baseline

Before editing code:

```powershell
python -m pytest
```

Then verify import and syntax compilation:

```powershell
python -m compileall -q app tests
```

Run lint:

```powershell
python -m ruff check .
```

Run formatting verification:

```powershell
python -m ruff format --check .
```

Run type checking:

```powershell
python -m mypy app tests
```

A clean starting baseline distinguishes pre-existing failures from changes introduced by the contributor.

When an optional tool is unavailable, install the development extra rather than silently omitting the check from release work.

---

## 19. Recommended local check sequence

Fast edit loop:

```powershell
python -m pytest tests/test_<affected_area>.py
python -m ruff check <changed-paths>
python -m compileall -q <changed-paths>
```

Pre-commit local sequence:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy app tests
python -m pytest
python -m compileall -q app tests
```

Expanded sequence with coverage:

```powershell
python -m pytest --cov=app --cov-report=term-missing
```

Real GF integration tests are run separately because they require an external installation.

---

## 20. Pytest configuration

The package configuration owns pytest defaults.

Expected baseline concepts:

```text
test directory: tests
test filename pattern: test_*.py
quiet default output may be enabled
```

Inspect active settings:

```powershell
python -m pytest --trace-config
```

List collected tests:

```powershell
python -m pytest --collect-only
```

Run one file:

```powershell
python -m pytest tests/test_scanner.py
```

Run one test:

```powershell
python -m pytest tests/test_scanner.py::test_name
```

Run tests matching a name:

```powershell
python -m pytest -k scanner
```

Stop after first failure:

```powershell
python -m pytest -x
```

Show local variables on failure:

```powershell
python -m pytest -l
```

Show captured output:

```powershell
python -m pytest -s
```

Use `-s` only when live output is required for debugging.

Tests should normally rely on captured output.

---

## 21. Test categories

GF Wordbench uses several conceptual test categories.

### 21.1 Unit tests

Test one bounded component without real GF.

Examples:

```text
models
path utilities
process-result conversion
file selection
scanner masking
diagnostic parsing
classification
diff generation
report formatting
schema validation
migration
```

### 21.2 Contract tests

Verify architectural and persisted boundaries.

Examples:

```text
forbidden imports
artifact ownership
CLI/GUI parity
report observation-only behavior
schema IDs and versions
mode rules
no gold mutation
framework language neutrality
```

### 21.3 Integration tests without real GF

Use:

- fake executable;
- temporary filesystem;
- controlled process result;
- fixture project;
- fake stdout and stderr;
- deterministic artifacts.

These test the process boundary without requiring a GF installation.

### 21.4 Real GF integration tests

Use a known GF executable and a small neutral fixture grammar.

Examples:

```text
version probe
successful compilation
failed compilation
PGF build
scenario load
parse
linearize
bounded generation
timeout containment where safe
```

### 21.5 Active-project validation tests

Validate the active language project.

These are not substitutes for language-neutral framework tests.

### 21.6 GUI tests

Test controllers, validators and state mapping without requiring manual interaction wherever possible.

---

## 22. Recommended pytest markers

The final test suite should use explicit markers for expensive or external tests.

Recommended markers:

```text
integration
requires_gf
gui
slow
project
```

Examples:

```powershell
python -m pytest -m "not requires_gf"
python -m pytest -m requires_gf
python -m pytest -m "integration and not slow"
```

Marker declarations belong in `pyproject.toml`.

Unregistered markers should be rejected or warned by strict pytest configuration.

---

## 23. Real GF test setup

Real GF tests must receive explicit environment configuration through the documented test fixture or command options.

They must record or display:

```text
GF executable
GF version
RGL root
fixture project
effective GF path
```

They must not depend on:

```text
a developer's global GF_LIB_PATH
the current terminal directory
the active project unless marked project
old generated .gfo files
an existing personal run directory
```

A missing real GF installation should cause a clear test skip only for tests explicitly marked as requiring GF.

It must not turn a required release integration job into a silent pass.

---

## 24. Neutral GF fixture grammar

Framework integration tests should use a small language-neutral fixture.

Suggested location:

```text
tests/fixtures/gf/
```

The fixture should be:

- minimal;
- deterministic;
- self-contained except for documented RGL use;
- fast to compile;
- capable of successful and failing cases;
- free from active-language identifiers;
- licensed for the repository;
- reviewed as test infrastructure.

Suggested fixture cases:

```text
valid abstract and concrete grammar
syntax error
type error
missing import
missing linearization
small parse and linearization
small PGF build
small .gfs scenario
```

Do not use a large active language as the only process-contract fixture.

---

## 25. Temporary directories

Tests that write files must use pytest temporary paths.

Example:

```python
def test_example(tmp_path):
    output_path = tmp_path / "result.json"
```

Tests must not write into:

```text
repository root
project source tree
committed gold directories
developer output root
user home
system temporary paths with fixed names
```

Temporary paths must remain unique per test.

Tests must not rely on execution order.

---

## 26. Filesystem test rules

Test at least:

```text
path containing spaces
Windows drive-style path handling where applicable
mixed slash input
project-relative normalization
parent traversal rejection
missing source directory
output-directory creation
filename collision
atomic replacement
read-only or unwritable destination
UTF-8 filename
```

Tests should use `pathlib.Path` internally.

Do not assert platform-specific separators in portable persisted output when the schema requires `/`.

---

## 27. Process test rules

The process layer must be tested independently.

Required cases:

```text
successful process
non-zero exit
stdout only
stderr only
stdout and stderr
timeout
launch failure
cancellation
path containing spaces
explicit working directory
environment override
output limit
UTF-8 output
invalid bytes under decoding policy
child termination where safely testable
```

Process tests must not infer success from stdout alone.

They must preserve both streams separately.

---

## 28. Scanner tests

Scanner tests should cover:

```text
empty file
normal GF source
comments
nested comment-like text where applicable
strings
escaped or doubled quotes
suspicious pattern in code
same pattern inside comment
same pattern inside string
line and column reporting
UTF-8 content
CRLF input
large file bound
deterministic finding order
```

Scanner tests prove heuristic behavior.

They do not replace GF compilation tests.

---

## 29. Classifier tests

Classifier tests should cover:

```text
successful result
direct failure
downstream failure
ambiguous failure
noise
skipped result
multiple independent blockers
dependency cycle or incomplete evidence
stable blocker ordering
preservation of raw error kind
```

The classifier must not execute GF or mutate raw evidence.

---

## 30. Report tests

Report tests should create structured in-memory results and verify generated artifacts.

Test:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
detail reports
manifest.json
```

Required rules:

- reports do not invoke GF;
- reports do not invoke scanner or compiler;
- JSON uses the canonical schema;
- Markdown is derived from the same result;
- paths are returned consistently;
- top errors are deterministic;
- secrets are absent;
- raw evidence references remain valid;
- report generation handles partial runs;
- report failures do not rewrite stage results.

---

## 31. Schema tests

Every persisted schema requires tests for:

```text
valid current document
missing required field
unknown optional field
unknown enum
unsupported major version
compatible minor version
UTF-8
CRLF legacy input where allowed
canonical LF output
deterministic arrays
atomic writes
legacy migration
failed migration preserving source
```

A schema test should not infer schema version from package version.

---

## 32. Scenario-runner tests

The final scenario runner requires tests for:

```text
fresh process per scenario
script passed through stdin
finite timeout
stdout and stderr capture
scenario begin marker
scenario end marker
section markers
missing marker
duplicate marker
marker order
fatal GF diagnostic
zero exit with incomplete script
assertion pass
assertion failure
gold match
gold mismatch
missing required gold
optional scenario
required scenario
normalization
output truncation
prohibited system command
script hash
deterministic scenario order
```

Use fake process results for most tests.

Use real GF only for a small integration subset.

---

## 33. CLI tests

CLI tests should verify:

```text
help
version
argument validation
mode selection
target parsing
configuration error exit
validation failure exit
runtime error exit
successful exit
report-path display
release weakening flags rejected
legacy mode alias migration
```

CLI tests should patch or inject orchestration at the public boundary.

They should not mock every internal helper.

---

## 34. GUI tests

Prefer testing:

```text
input validation
state loading
state saving
RunConfig construction
mode control behavior
prohibited release options disabled
progress event handling
result display mapping
report opening request
error dialog inputs
```

Avoid tests that require a human to click manually.

Where supported in CI, a Qt offscreen platform may be used.

Platform-specific GUI tests should be marked clearly.

GUI tests must not launch GF directly from widgets.

---

## 35. Ruff

Check the complete repository:

```powershell
python -m ruff check .
```

Check changed areas:

```powershell
python -m ruff check app tests
```

Apply safe automatic fixes:

```powershell
python -m ruff check . --fix
```

Review every automatic change.

Do not use unsafe fixes without understanding the effect.

Formatting check:

```powershell
python -m ruff format --check .
```

Format files:

```powershell
python -m ruff format .
```

The authoritative rule selection and line length remain in `pyproject.toml`.

---

## 36. mypy

Run type checking:

```powershell
python -m mypy app tests
```

Run on one module:

```powershell
python -m mypy app/audit/scanner.py
```

Expected project principles:

```text
typed public functions
no accidental implicit Optional
typed shared models
typed path values
typed result objects
bounded use of Any
```

Do not silence a type error globally when a narrow annotation or adapter can resolve it.

A `# type: ignore` requires:

- the narrowest error code supported;
- a reason when not obvious;
- no suppression of unrelated errors.

---

## 37. Compileall

Run:

```powershell
python -m compileall -q app tests
```

This catches syntax and import compilation problems.

It does not replace:

```text
pytest
Ruff
mypy
real package imports
```

A successful `compileall` does not prove runtime correctness.

---

## 38. Coverage

Generate terminal coverage:

```powershell
python -m pytest --cov=app --cov-report=term-missing
```

Generate HTML coverage:

```powershell
python -m pytest --cov=app --cov-report=html
```

Open:

```text
htmlcov/index.html
```

Coverage is a diagnostic measure.

A high percentage does not replace contract coverage.

Prioritize tests for:

- error branches;
- migrations;
- external-process outcomes;
- release gates;
- artifact ownership;
- scenario markers;
- configuration precedence.

---

## 39. Run the CLI from source

Use the installed entrypoint:

```powershell
gf-wordbench --help
```

Or the source-module entrypoint:

```powershell
python -m app.main_cli --help
```

Run configuration validation:

```powershell
gf-wordbench config check `
  --project-root "<ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

Run a focused development validation:

```powershell
gf-wordbench validate `
  --mode quick `
  --target "file:<PROJECT-RELATIVE-GF-FILE>" `
  --project-root "<ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

The exact public syntax is owned by `CLI_REFERENCE.md`.

---

## 40. Run the GUI from source

Preferred:

```powershell
gf-wordbench gui
```

Source fallback:

```powershell
python -m app.main_gui
```

Windows launcher:

```powershell
.\launch_gui.bat
```

For debugging GUI startup in a console, use the documented console mode of the launcher or run the Python module directly.

The GUI and CLI must resolve equivalent configuration through the same bootstrap path.

---

## 41. Windows launchers

Launchers may locate:

```text
repository virtual environment
explicit configured interpreter
uv
py or python
pythonw for GUI
```

They must:

- resolve repository root explicitly;
- pass arguments unchanged;
- preserve meaningful exit codes;
- avoid hidden validation defaults;
- remain convenience entrypoints.

When debugging launcher behavior, compare it with:

```powershell
python -X utf8 -m app.main_cli --help
python -X utf8 -m app.main_gui
```

A launcher-only success indicates a packaging or environment problem that should be fixed.

---

## 42. UTF-8 development policy

Canonical project text uses:

```text
UTF-8 without BOM
LF newlines
final newline
```

Readers may accept compatible legacy forms where documented.

Run Python with UTF-8 mode where launcher behavior requires it:

```powershell
python -X utf8 -m app.main_cli --help
```

Do not depend on the active console code page for GF source, scenarios, gold files, JSON, TOML or reports.

---

## 43. Logging during development

Use the framework logging utilities.

Do not add unrelated `print()` calls to production modules.

Development logging must:

- identify stage or component;
- avoid secrets;
- avoid full environment dumps;
- preserve raw external streams separately;
- use deterministic paths;
- avoid changing validation truth.

Temporary debug logging must be removed or converted to controlled diagnostic logging before merge.

---

## 44. Debugging external GF execution

When a real GF test fails, inspect:

```text
resolved GF executable
GF version
working directory
ordered arguments
effective GF path
environment overrides
timeout
stdout
stderr
generated artifacts
```

Reproduce the recorded command only after preserving the original run evidence.

Do not rewrite the recorded raw files.

A manually successful command does not invalidate the failed run if the manually used environment differs.

---

## 45. Debugging import problems

Show the imported package location:

```powershell
python -c "import app; print(app.__file__)"
```

Show Python search path:

```powershell
python -c "import sys; print('\n'.join(sys.path))"
```

Inspect editable installation:

```powershell
python -m pip show -f gf-wordbench
```

Common causes:

```text
wrong virtual environment
stale editable installation
repository root not active
duplicate package installed globally
renamed package entrypoint not reinstalled
local file shadowing a package
```

Do not modify `sys.path` inside production code to repair local setup.

---

## 46. Debugging PySide6

Verify import:

```powershell
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
```

Common issues:

```text
dev environment missing runtime dependencies
mixed Python architectures
unsupported Python version
GUI launched through wrong interpreter
headless CI without Qt platform configuration
```

Use the same interpreter for installation and launch:

```powershell
python -m pip install -e ".[dev]"
python -m app.main_gui
```

---

## 47. Clean rebuild of the environment

When the environment is irreparably inconsistent:

PowerShell:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Then rerun:

```powershell
python -m pytest
python -m ruff check .
python -m mypy app tests
python -m compileall -q app tests
```

Do not delete project sources, gold files or contract documents while cleaning the Python environment.

---

## 48. Clean generated development output

Generated outputs may include:

```text
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
__pycache__/
build/
dist/
*.egg-info/
run_*/
```

Remove only generated content.

PowerShell example:

```powershell
Remove-Item -Recurse -Force .pytest_cache, .mypy_cache, .ruff_cache, htmlcov -ErrorAction SilentlyContinue
Remove-Item -Force .coverage -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

Review paths before using broad deletion commands.

Run directories may contain valuable evidence.

Delete them only under the retention and cleanup policy.

---

## 49. Package build verification

Release maintainers should verify that the package builds from a clean checkout.

When the build frontend is installed:

```powershell
python -m build
```

Expected outputs:

```text
dist/*.whl
dist/*.tar.gz
```

Then test the wheel in a fresh environment:

```powershell
python -m venv .venv-wheel-test
.\.venv-wheel-test\Scripts\Activate.ps1
python -m pip install dist\<wheel-name>.whl
gf-wordbench --version
gf-wordbench --help
```

Remove the test environment after verification.

Package build requirements and commands are finalized by the release process documentation.

---

## 50. Clean-room verification

A change affecting installation, schemas, launchers or configuration must be tested in a clean environment.

Clean-room steps:

```text
fresh checkout or clean worktree
new virtual environment
editable or wheel installation
no inherited project state
explicit GF executable
explicit RGL root
temporary output root
unit and contract tests
required integration tests
one CLI smoke run
one GUI startup smoke test where applicable
```

A development machine with cached state is not sufficient proof.

---

## 51. Working on framework code

Before editing a module:

1. identify its architectural layer;
2. identify providers and consumers;
3. read its contract lock entries;
4. locate relevant tests;
5. run a focused baseline;
6. make the smallest coherent change;
7. update every affected consumer;
8. update schemas and migration when persisted data changes;
9. rerun focused and full checks.

A public cross-file change is not complete when only the provider compiles.

---

## 52. Working on the active project

Framework development and language-project development are separate concerns.

Active-project changes may affect:

```text
GF modules
project.toml
scenarios
inputs
gold
language documentation
release criteria
```

They should not introduce language-specific assumptions into:

```text
app/
framework tests
framework defaults
templates/
```

A project-specific workaround belongs in `project/` unless a reusable framework need is demonstrated.

---

## 53. Adding a Python module

Before adding a module:

```text
[ ] responsibility is not already owned
[ ] architectural layer is identified
[ ] dependencies follow DEPENDENCY_RULES.md
[ ] public API is minimal
[ ] private helpers remain private
[ ] no import side effects
[ ] errors are structured appropriately
[ ] unit tests exist
[ ] contract tests exist when crossing a boundary
[ ] component map is updated
```

Do not add a new package solely to create visual symmetry in the directory tree.

---

## 54. Adding a dependency

A new dependency requires:

```text
problem solved
why standard library or existing dependency is insufficient
runtime or development classification
version range
license review
platform support
security impact
failure behavior
adapter boundary
tests
documentation
```

Add dependencies only through `pyproject.toml`.

Do not install a package locally and import it without declaring it.

Optional dependencies must fail clearly when unavailable.

---

## 55. Changing shared models

Shared result and configuration models are cross-file contracts.

When changing a model:

```text
[ ] field owner identified
[ ] required versus optional defined
[ ] safe default defined
[ ] serialization updated
[ ] deserialization updated
[ ] schema updated
[ ] migration reviewed
[ ] report consumers updated
[ ] CLI and GUI consumers updated
[ ] tests updated
[ ] contract lock updated
```

Do not attach undocumented dynamic attributes to shared models.

---

## 56. Changing persisted schemas

A persisted schema change requires:

```text
explicit schema impact classification
compatible minor or breaking major decision
reader update
writer update
migration
round-trip tests
legacy fixture
atomic-write behavior
documentation update
PERSISTED_SCHEMA_LOCK.md update
```

Do not use package version as schema version.

Do not silently reinterpret an unknown enum.

---

## 57. Changing external commands

A GF command change affects an external-tool contract.

Update together:

```text
command builder
process request
working directory
configuration
result model
diagnostic parsing
artifact checks
unit tests
real integration tests
compatibility notes
EXTERNAL_TOOL_CONTRACT_LOCK.md
```

The logged structured command must match the executed command.

---

## 58. Changing reports

Reports are observers.

A report change must not:

- invoke GF;
- invoke scanning;
- mutate results;
- create missing evidence;
- change validation status;
- parse another human report as primary truth.

Test report changes from structured fixtures.

When `summary.json` changes, treat it as a schema change rather than a formatting change.

---

## 59. Changing GUI behavior

GUI changes must preserve:

```text
same project loader
same mode semantics
same RunConfig
same audit entrypoint
same release restrictions
same result interpretation
```

Widget state must not become project authority.

Prefer controller or service tests over direct widget-to-process behavior.

---

## 60. Changing CLI behavior

CLI changes must preserve:

```text
stable exit-code semantics
structured argument validation
bootstrap boundary
mode restrictions
report path visibility
automation compatibility
```

Avoid implementation logic inside the argument parser.

The CLI should convert input into a public application request.

---

## 61. Branch and commit hygiene

Recommended practice:

- one coherent contract change per branch or review unit;
- separate generated evidence from source changes;
- do not commit local state;
- do not commit accidental active-language paths in framework tests;
- do not combine unrelated formatting with schema migration;
- include tests with the change they prove;
- update documentation in the same change when behavior changes.

Before commit:

```powershell
git status
git diff --check
```

Inspect staged files:

```powershell
git diff --cached --stat
git diff --cached
```

---

## 62. Pre-commit checklist

```text
[ ] Correct virtual environment active
[ ] Editable development install current
[ ] Focused tests pass
[ ] Full pytest suite passes
[ ] Ruff formatting check passes
[ ] Ruff lint passes
[ ] mypy passes
[ ] compileall passes
[ ] Required GF integration tests pass
[ ] No generated run output staged
[ ] No local state staged
[ ] No secrets staged
[ ] No active-language identifier leaked into framework code
[ ] Contracts updated
[ ] Schemas and migrations updated where required
[ ] Documentation links remain valid
```

---

## 63. Pull-request evidence

A framework change should report:

```text
summary of behavior
affected contracts
tests run
GF version used for integration
platform tested
schema impact
migration impact
known limitations
```

Example test evidence:

```text
python -m pytest
python -m ruff format --check .
python -m ruff check .
python -m mypy app tests
python -m compileall -q app tests
real GF integration: <version and result>
```

Do not state that a tool passed when it was not installed or not run.

---

## 64. CI parity

Local commands should match CI as closely as practical.

CI should use:

```text
supported Python versions
clean dependency installation
no personal application state
temporary output roots
explicit GF setup for GF jobs
separate fast and real-GF jobs
archived failure evidence
```

A test that passes only because a developer has a global RGL path is invalid.

CI-specific wrappers must call the same public commands.

---

## 65. Recommended CI job split

### 65.1 Static and unit job

```text
install dev dependencies
Ruff format check
Ruff lint
mypy
compileall
unit tests
contract tests
```

No real GF required.

### 65.2 Real GF integration job

```text
install supported GF version
install or locate RGL
run requires_gf tests
run neutral fixture grammar
preserve raw evidence on failure
```

### 65.3 GUI job

```text
install PySide6
run GUI-independent tests
run approved offscreen smoke test
```

### 65.4 Active-project job

```text
config check
checkpoint or diagnostic validation
release validation for release branches
archive run artifacts
```

---

## 66. Troubleshooting: tests cannot import `app`

Confirm the repository and environment:

```powershell
Get-Location
python -c "import app; print(app.__file__)"
python -m pip show gf-wordbench
```

Reinstall editable package:

```powershell
python -m pip install -e ".[dev]"
```

Do not fix tests by inserting repository paths into every test module.

---

## 67. Troubleshooting: Ruff or mypy not found

Install the development group:

```powershell
python -m pip install -e ".[dev]"
```

Verify:

```powershell
python -m ruff --version
python -m mypy --version
```

Use `python -m` to ensure the tool belongs to the active interpreter.

---

## 68. Troubleshooting: PySide6 installation fails

Check:

```text
supported Python version
64-bit versus 32-bit interpreter
pip version
operating-system wheel support
corporate package mirror availability
```

Then retry in a fresh environment.

Do not replace PySide6 with another GUI toolkit in local code merely to bypass installation.

A GUI dependency change is an architectural decision.

---

## 69. Troubleshooting: real GF tests are skipped

Confirm that:

- the GF test marker is selected;
- the documented GF executable input is supplied;
- the executable launches;
- the RGL root exists;
- the fixture can resolve its GF path.

A local skip may be acceptable for ordinary unit work.

A release integration job must fail when its required GF environment is absent.

---

## 70. Troubleshooting: GF command differs from manual command

Compare the structured run evidence.

Check:

```text
executable
argument order
source argument
working directory
GF path
output directories
environment overrides
timeout
GF version
```

Do not compare only the human-rendered command.

Paths and arguments are passed structurally without an implicit shell.

---

## 71. Troubleshooting: tests modify project files

Tests must write into `tmp_path`.

Inspect for:

```text
hardcoded repository paths
direct writes to project/validation/gold
state service using repository root
run output defaulting into source tree
fixtures reused as mutable destinations
```

Restore modified source files from version control and correct the test owner.

---

## 72. Troubleshooting: platform-specific failure

Record:

```text
operating system
Python version
GF version
path form
working directory
locale
failing test
raw stdout and stderr
```

Separate:

- platform adapter defect;
- path normalization defect;
- GF version difference;
- test assumption;
- active-project difference.

Do not normalize away a meaningful platform difference without contract review.

---

## 73. Development completion criteria

A development environment is ready when:

```text
[ ] supported Python interpreter active
[ ] repository-local environment created
[ ] editable dev install succeeds
[ ] app imports from the checkout
[ ] CLI help runs
[ ] GUI import succeeds
[ ] pytest collects tests
[ ] unit and contract tests pass
[ ] Ruff is available
[ ] mypy is available
[ ] compileall passes
[ ] GF executable is known for integration work
[ ] RGL root is known for integration work
[ ] config check can resolve the active project
[ ] generated output is outside source roots
```

---

## 74. Minimal setup commands

PowerShell:

```powershell
Set-Location "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

python -m pytest
python -m ruff format --check .
python -m ruff check .
python -m mypy app tests
python -m compileall -q app tests

gf-wordbench --help
```

Real GF verification:

```powershell
& "C:\tools\gf\gf.exe" --version
```

Configuration verification:

```powershell
gf-wordbench config check `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

---

## 75. Related documentation

```text
docs/development/CODEBASE_GUIDE.md
docs/development/CODING_STANDARDS.md
docs/development/TESTING_GF_WORDBENCH.md
docs/development/EXTENDING_GF_WORDBENCH.md
docs/development/DEBUGGING_THE_FRAMEWORK.md
docs/architecture/DEPENDENCY_RULES.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/usage/QUICK_START.md
docs/operations/AUTOMATION_AND_CI.md
```

---

## 76. Final development rule

The supported development loop is:

```text
clean environment
→ editable dev install
→ focused baseline
→ coherent contract change
→ focused tests
→ static checks
→ full tests
→ required real GF integration
→ documentation and contract review
```

A change is ready only when its behavior, consumers, tests, schemas, evidence and documentation agree.

Local convenience must never become hidden project policy or an undocumented dependency.
