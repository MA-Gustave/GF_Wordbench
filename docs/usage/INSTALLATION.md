# GF Wordbench — Installation

**Document ID:** `GF-WB-USAGE-INSTALLATION`  
**Status:** Normative installation guide  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\usage\INSTALLATION.md`  
**Applies to:** GF Wordbench framework installation, Python environment setup, GF core and RGL prerequisites, verification, upgrades, and removal  
**Owner:** GF Wordbench maintainers  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines the supported installation procedures for GF Wordbench.

It covers:

- Python installation;
- virtual-environment creation;
- GF Wordbench installation from source or a release wheel;
- development dependencies;
- Grammatical Framework core installation;
- Resource Grammar Library installation;
- Windows launcher behavior;
- installation verification;
- upgrades;
- uninstallation;
- common installation failures.

This document does not define:

- active-language project creation;
- `project.toml` contents;
- validation-mode behavior;
- CLI option details;
- GUI workflow;
- GF command semantics;
- release packaging procedures.

Those topics are covered by the referenced documents at the end.

The central rule is:

> Install Python, GF core, the RGL, and GF Wordbench as separate components, then verify each boundary independently.

---

## 2. Supported installation model

GF Wordbench is a Python application that invokes the external GF executable.

The installation has four distinct parts:

```text
Python runtime
    +
GF Wordbench Python package
    +
GF core executable
    +
RGL or other required GF libraries
```

These parts MUST remain separable.

Installing GF Wordbench does not install GF core automatically.

Installing GF core does not necessarily install the RGL.

Installing the RGL does not install the Python application.

---

## 3. Canonical component names

Final package and command names:

```text
Python distribution: gf-wordbench
CLI command:         gf-wordbench
GUI command:         gf-wordbench-gui
Python package:      app
```

Canonical source entrypoints:

```text
app.main_cli
app.main_gui
```

Legacy migration names may still appear temporarily:

```text
gf-audit
gf-audit-cli
gf-audit-gui
GF_AUDIT_PYTHON
GF_AUDIT_DEBUG_CONSOLE
```

New documentation and final release packaging MUST use the GF Wordbench names.

Recommended final launcher environment variables:

```text
GF_WORDBENCH_PYTHON
GF_WORDBENCH_DEBUG_CONSOLE
```

---

## 4. Installation profiles

Choose one installation profile.

## 4.1 Standard local installation

Use for ordinary local operation from a checked-out source tree.

```text
virtual environment
non-editable package installation
runtime dependencies only
```

Command:

```text
python -m pip install .
```

## 4.2 Development installation

Use when editing GF Wordbench code or documentation.

```text
virtual environment
editable package installation
development dependencies
```

Command:

```text
python -m pip install -e ".[dev]"
```

## 4.3 Release-wheel installation

Use when a project release provides a built wheel.

```text
python -m pip install <path-to-wheel>
```

Example shape:

```text
python -m pip install dist/gf_wordbench-<version>-py3-none-any.whl
```

Do not assume a public package index exists unless the release documentation explicitly states it.

## 4.4 `uv` installation

`uv` MAY be used as an optional environment and package manager.

It is not required by GF Wordbench.

Example development workflow:

```text
uv venv
uv pip install -e ".[dev]"
```

Launcher support for `uv` is convenience behavior only.

The canonical installation contract remains standard Python packaging through `pyproject.toml`.

---

# 5. Requirements

## 5.1 Python

Minimum version:

```text
Python 3.11
```

Recommended:

```text
latest supported 64-bit Python 3.11 or newer
```

The authoritative requirement is the `requires-python` field in:

```text
pyproject.toml
```

The final project metadata is expected to declare:

```toml
requires-python = ">=3.11"
```

Verify:

```text
python --version
```

Windows alternative:

```text
py -3 --version
```

A Python version below the declared minimum is unsupported.

---

## 5.2 Python package installer

Required:

```text
pip
```

Verify:

```text
python -m pip --version
```

Use:

```text
python -m pip
```

rather than an unqualified `pip` command when interpreter identity matters.

This ensures that packages are installed into the Python environment being used.

---

## 5.3 Grammatical Framework core

Required for compile, scenario, and release validation:

```text
gf
```

or on Windows:

```text
gf.exe
```

Verify:

```text
gf --version
```

or with an explicit Windows path:

```text
"C:\path\to\gf.exe" --version
```

The exact supported-version policy belongs to:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

At this document's review date, the current official binary release is GF 3.12.

Do not encode that observation as an eternal framework requirement.

---

## 5.4 Resource Grammar Library

Required when the active language project imports RGL modules.

Canonical component:

```text
gf-rgl
```

GF core and the RGL are distributed separately in current GF releases.

GF Wordbench requires a resolvable RGL root, not one particular installation method.

---

## 5.5 Git

Git is recommended when installing from a repository clone.

Verify:

```text
git --version
```

Git is not required when installing from:

- a source archive;
- a release wheel;
- a pre-existing checkout.

---

## 5.6 Operating system

Primary supported environment:

```text
Windows
```

The architecture is intended to remain portable to:

```text
Linux
macOS
```

Actual platform support depends on:

- Python support;
- PySide6 availability;
- GF binary availability;
- process and path integration tests.

The CLI is easier to support across platforms than the GUI.

The authoritative platform matrix belongs in release and compatibility documentation.

---

# 6. Python dependencies

The final Python package is expected to use:

```toml
dependencies = [
  "PySide6>=6.8,<7.0",
]
```

Development dependencies are expected to include:

```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.3,<9.0",
  "pytest-cov>=6.0,<7.0",
  "ruff>=0.11,<0.12",
  "mypy>=1.15,<2.0",
]
```

`pyproject.toml` is authoritative.

This document MUST be updated when dependency policy changes.

---

# 7. Recommended directory layout

Example Windows layout:

```text
C:\mycode\Grammatical_Framework\
├── GF_Wordbench\
│   └── GF_Wordbench\
├── gf-3.12-windows\
│   └── gf.exe
├── gf-rgl\
│   └── src\
└── gf-wordbench-runs\
```

The components do not need to be siblings.

The layout is useful because it keeps:

- framework source;
- GF executable;
- RGL source;
- generated runs;

separate and easy to configure.

The installation MUST NOT depend on this exact path.

Paths containing spaces MUST work.

---

# 8. Obtain GF Wordbench

## 8.1 Clone with Git

From the directory that will contain the checkout:

```text
git clone <GF-WORDBENCH-REPOSITORY-URL> GF_Wordbench
cd GF_Wordbench
```

If the repository contains an additional project-root directory:

```text
cd GF_Wordbench
```

Confirm that the current directory contains:

```text
pyproject.toml
app/
docs/
project/
templates/
```

The repository URL remains a release or project-management concern and MUST NOT be invented in this guide before publication.

## 8.2 Source archive

Extract the source archive.

Open a terminal in the directory containing:

```text
pyproject.toml
```

Do not install from a nested `app/` or `docs/` directory.

## 8.3 Release wheel

Obtain the wheel from the official GF Wordbench release channel.

Verify the release according to the project's security policy before installation.

---

# 9. Create a virtual environment

A repository-local virtual environment is recommended:

```text
.venv
```

Virtual environments are disposable and should be recreated rather than copied between locations.

---

## 9.1 Windows PowerShell

From the repository root:

```powershell
py -3.11 -m venv .venv
```

When a specific launcher is unavailable:

```powershell
python -m venv .venv
```

Activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify:

```powershell
python --version
python -m pip --version
```

---

## 9.2 Windows Command Prompt

Create:

```bat
py -3.11 -m venv .venv
```

Activate:

```bat
.venv\Scripts\activate.bat
```

Verify:

```bat
python --version
python -m pip --version
```

---

## 9.3 Linux and macOS

Create:

```bash
python3.11 -m venv .venv
```

When `python3.11` is not the installed command:

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

Verify:

```bash
python --version
python -m pip --version
```

---

## 9.4 Activation is optional

A virtual environment does not have to be activated.

Windows example:

```text
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

POSIX example:

```text
.venv/bin/python -m pip install -e ".[dev]"
```

Explicit interpreter paths are often preferable in launchers and automation.

---

## 9.5 PowerShell execution policy

PowerShell may block `Activate.ps1`.

A user-level policy may be set with:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Only change execution policy when permitted by local security policy.

Activation can also be avoided by invoking:

```powershell
.\.venv\Scripts\python.exe
```

directly.

---

# 10. Prepare packaging tools

Upgrade `pip` inside the virtual environment:

```text
python -m pip install --upgrade pip
```

The build backend declared in `pyproject.toml` is installed automatically when pip builds the project in an isolated environment.

The project currently uses or targets:

```toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"
```

A normal installation does not require a global Hatch installation.

---

# 11. Install GF Wordbench

## 11.1 Standard installation from source

```text
python -m pip install .
```

This installs:

- GF Wordbench;
- runtime dependencies;
- CLI entrypoint;
- GUI entrypoint.

It does not make source edits immediately visible.

Reinstall after source changes.

---

## 11.2 Development installation

```text
python -m pip install -e ".[dev]"
```

This installs:

- GF Wordbench in editable mode;
- PySide6;
- pytest;
- pytest-cov;
- Ruff;
- mypy;
- console entrypoints.

Python source edits become visible without reinstalling.

Changes to packaging metadata may still require reinstalling.

---

## 11.3 Runtime-only editable installation

For source development without developer tools:

```text
python -m pip install -e .
```

---

## 11.4 Wheel installation

```text
python -m pip install "<path-to-wheel>"
```

Windows example:

```powershell
python -m pip install ".\dist\gf_wordbench-0.1.0-py3-none-any.whl"
```

The actual version and filename come from the release.

---

## 11.5 Reinstall

Force reinstall from the current source:

```text
python -m pip install --force-reinstall .
```

Editable reinstall:

```text
python -m pip install -e ".[dev]"
```

after packaging metadata changes.

---

# 12. Verify the Python installation

## 12.1 Package import

```text
python -c "import app; print(app.__version__)"
```

Expected:

```text
a version string
```

## 12.2 PySide6 import

```text
python -c "import PySide6; print(PySide6.__version__)"
```

This verifies the GUI runtime dependency.

## 12.3 CLI entrypoint

```text
gf-wordbench --help
```

Version check:

```text
gf-wordbench --version
```

## 12.4 GUI entrypoint

```text
gf-wordbench-gui
```

The GUI should open without importing from a different checkout.

## 12.5 Module fallback

From a source checkout:

```text
python -m app.main_cli --help
python -m app.main_gui
```

Module execution is a supported diagnostic fallback.

Installed commands remain the preferred user interface.

---

# 13. Install GF core

Use a GF version supported by:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

The official GF download page provides binary packages for Windows, macOS, and Debian/Ubuntu.

GF may also be installed from Hackage or source.

Binary installation is recommended unless compiler development requires a source build.

---

## 13.1 Windows binary installation

1. Download the supported Windows GF binary package from the official GF release source.
2. Extract it to a stable directory.
3. Locate:

```text
gf.exe
```

4. Record the full path.

Example:

```text
C:\mycode\Grammatical_Framework\gf-3.12-windows\gf.exe
```

5. Verify:

```powershell
& "C:\mycode\Grammatical_Framework\gf-3.12-windows\gf.exe" --version
```

Adding the GF directory to `PATH` is optional for GF Wordbench when the executable is configured explicitly.

Explicit configuration is preferred because it prevents silent substitution of another GF installation.

---

## 13.2 Debian or Ubuntu binary installation

For the package matching the supported GF release and distribution:

```bash
sudo apt install ./gf-<version>-ubuntu-<release>.deb
```

Verify:

```bash
gf --version
```

Do not copy an example package filename blindly.

Use the filename provided by the official GF release.

---

## 13.3 macOS binary installation

Install the package matching the Mac architecture:

```text
Intel
Apple Silicon
```

When macOS blocks the package because it is not notarized, follow the official GF installation instructions and local security policy.

Verify:

```bash
gf --version
```

---

## 13.4 Hackage installation

For supported macOS, Linux, or WSL environments with a compatible Haskell toolchain:

```bash
cabal update
cabal install gf-<supported-version>
```

The executable is commonly installed into a user-local Cabal binary directory.

That directory may need to be added to `PATH`.

A source-toolchain installation is more complex than a binary installation and is not required for ordinary GF Wordbench use.

---

## 13.5 GF source installation

Clone:

```bash
git clone https://github.com/GrammaticalFramework/gf-core.git
cd gf-core
```

Install according to the official GF source instructions, commonly through:

```bash
cabal install
```

or:

```bash
stack install
```

Use a release tag or reviewed commit when reproducibility matters.

Do not use an arbitrary moving branch for release validation without recording the exact revision.

---

# 14. Install the RGL

GF core and the RGL are separate components.

The active project may depend on:

```text
abstract
common
prelude
api
language-specific RGL modules
```

GF Wordbench needs an RGL root that allows the configured GF path to resolve these modules.

---

## 14.1 RGL binary release

1. Download a compatible RGL binary release.
2. Extract it to a stable directory.
3. Record the directory that contains or anchors the RGL libraries.

The official GF instructions commonly use:

```text
GF_LIB_PATH
```

GF Wordbench SHOULD instead receive an explicit RGL root through its environment or application configuration.

It may set a child-process environment explicitly.

It MUST NOT depend silently on a developer's global `GF_LIB_PATH`.

---

## 14.2 RGL source checkout

Clone:

```bash
git clone https://github.com/GrammaticalFramework/gf-rgl.git
```

Typical checkout:

```text
C:\mycode\Grammatical_Framework\gf-rgl
```

Common RGL source root:

```text
C:\mycode\Grammatical_Framework\gf-rgl\src
```

Use the actual checkout structure.

Do not assume the root from directory name alone.

---

## 14.3 Compile the RGL from source

GF must already be installed and resolvable.

From the RGL checkout:

```bash
make
```

On Windows, follow the build instructions provided by the RGL release or repository.

GF Wordbench itself does not build the RGL automatically during ordinary installation.

---

## 14.4 RGL compatibility

GF core and RGL versions should be selected as a compatible pair.

For reproducible validation, record:

- GF version;
- RGL release or commit;
- effective GF search path.

A newer RGL checkout combined with an older GF executable may not be valid.

Compatibility is governed by project and GF compatibility documentation.

---

# 15. Verify GF and RGL together

## 15.1 GF version

```text
<gf-executable> --version
```

Windows example:

```powershell
& "C:\path\to\gf.exe" --version
```

## 15.2 Basic GF startup

```text
<gf-executable>
```

Exit the shell after confirming startup.

## 15.3 Path verification

Use a small project entrypoint or project check after configuring:

- GF executable;
- RGL root;
- project root.

Preferred GF Wordbench check:

```text
gf-wordbench project check
```

Then run a quick or checkpoint validation according to the project state.

## 15.4 Direct compile verification

A direct compile may be used for installation diagnosis:

```text
<gf> -batch -s <path-options> <known-valid-source.gf>
```

Do not use an ad hoc command as permanent project configuration.

GF Wordbench should construct and record the effective command.

---

# 16. Configure GF Wordbench environment

Machine-specific settings do not belong in `project.toml`.

Required environment facts commonly include:

```text
GF executable
RGL root
output root
```

They may be supplied through:

- CLI arguments;
- GUI selections;
- application state;
- documented environment configuration.

The exact precedence is defined by:

```text
docs/configuration/ENVIRONMENT_AND_PATHS.md
```

The resolved values MUST be visible in run metadata.

---

## 16.1 Example Windows paths

```text
GF executable:
C:\mycode\Grammatical_Framework\gf-3.12-windows\gf.exe

RGL root:
C:\mycode\Grammatical_Framework\gf-rgl\src

Output root:
C:\mycode\Grammatical_Framework\gf-wordbench-runs
```

Paths may contain spaces.

Do not add manual quote characters to values stored in configuration fields.

Quoting is applied by the shell only when typing a command.

---

## 16.2 Environment-variable policy

The final application may support documented variables such as:

```text
GF_WORDBENCH_PYTHON
GF_WORDBENCH_DEBUG_CONSOLE
```

GF-related environment variables may include:

```text
PATH
GF_LIB_PATH
```

Explicit GF Wordbench configuration takes precedence for correctness-critical paths.

Full environment dumps MUST NOT be written into reports.

---

# 17. Validate the active project

After installation, confirm:

```text
project/project.toml
```

exists and contains:

```text
schema_id = "gf-wordbench.project"
schema_version = "1.0"
```

Run:

```text
gf-wordbench project check
```

Strict validation:

```text
gf-wordbench project check --strict
```

A successful package installation does not prove that the active language project is configured correctly.

---

# 18. First CLI verification

Start with help:

```text
gf-wordbench --help
```

Then verify project configuration:

```text
gf-wordbench project check
```

Then run the smallest applicable validation.

Conceptual quick command:

```text
gf-wordbench run --mode quick --target-file <project-relative-file>
```

The exact final option names are defined in:

```text
docs/usage/CLI_REFERENCE.md
```

Do not preserve an example that disagrees with the final CLI parser.

---

# 19. First GUI verification

Run:

```text
gf-wordbench-gui
```

Confirm that the GUI can:

- load application defaults;
- locate the active project;
- display or accept GF executable path;
- display or accept RGL root;
- display or accept output root;
- validate configuration;
- close without an unhandled exception.

Do not begin with release mode.

Use project check or quick mode first.

---

# 20. Windows launchers

Expected convenience launchers:

```text
launch_cli.bat
launch_gui.bat
```

They are optional.

The Python package and installed entrypoints remain canonical.

---

## 20.1 Launcher responsibilities

A launcher MAY:

- resolve the repository root;
- prefer `.venv`;
- use an explicit Python override;
- optionally use `uv`;
- enforce UTF-8 mode;
- start the installed or module entrypoint;
- propagate meaningful exit codes;
- keep a console open after a visible failure.

A launcher MUST NOT:

- define validation semantics;
- change source selection silently;
- override the active project identity;
- construct a different GF path;
- hide the selected interpreter;
- be the only supported execution method.

---

## 20.2 Runtime resolution order

Recommended final Windows launcher order:

```text
1. GF_WORDBENCH_PYTHON
2. repository-local .venv
3. uv, when installed
4. Python launcher
5. python or pythonw on PATH
6. clear failure
```

The launcher should report which runtime could not be resolved.

---

## 20.3 Legacy launcher variables

During migration, the launchers may accept:

```text
GF_AUDIT_PYTHON
GF_AUDIT_DEBUG_CONSOLE
```

These are legacy aliases.

Final documentation and examples use:

```text
GF_WORDBENCH_PYTHON
GF_WORDBENCH_DEBUG_CONSOLE
```

---

## 20.4 Launcher use

CLI:

```bat
launch_cli.bat --help
```

GUI:

```bat
launch_gui.bat
```

A launcher should work from any current directory because it resolves its own repository root.

---

# 21. Development verification

From a development installation:

```text
python -m pytest
```

Expected:

```text
all required tests pass
```

Lint:

```text
python -m ruff check .
```

Type check:

```text
python -m mypy app
```

Coverage:

```text
python -m pytest --cov=app --cov-report=term-missing
```

The exact quality gates belong to:

```text
docs/development/TESTING_GF_WORDBENCH.md
```

Real-GF integration tests should be marked separately from unit tests that use fake process results.

---

# 22. Installation verification checklist

```text
[ ] supported Python installed
[ ] correct Python interpreter selected
[ ] virtual environment created
[ ] GF Wordbench package installed
[ ] app import succeeds
[ ] PySide6 import succeeds
[ ] CLI command resolves
[ ] GUI command resolves
[ ] GF executable exists
[ ] GF version probe succeeds
[ ] RGL root exists
[ ] active project.toml exists
[ ] project check succeeds
[ ] output root is writable
[ ] quick validation can start
[ ] test suite passes for development installs
```

Installation is not complete until every required item is verified.

---

# 23. Upgrade GF Wordbench

## 23.1 Editable source checkout

Update source:

```text
git pull
```

Refresh dependencies and entrypoints:

```text
python -m pip install -e ".[dev]"
```

Run:

```text
python -m pytest
gf-wordbench --version
gf-wordbench project check
```

Review migration documentation before opening or rewriting persisted state.

---

## 23.2 Standard source installation

Update source, then reinstall:

```text
python -m pip install --upgrade .
```

When dependency state is uncertain:

```text
python -m pip install --force-reinstall .
```

---

## 23.3 Wheel installation

```text
python -m pip install --upgrade <new-wheel>
```

Run project and schema checks afterward.

---

## 23.4 Schema migration

An application upgrade may introduce:

- state migration;
- project schema migration;
- summary-reader migration;
- gold normalization review.

Migration MUST be explicit.

Do not delete or overwrite old state before the canonical replacement validates successfully.

---

# 24. Upgrade GF core

Before replacing GF:

1. read the GF compatibility policy;
2. record the current GF version;
3. install the new GF version in a separate directory when possible;
4. configure GF Wordbench explicitly to use it;
5. run version probe;
6. run integration checks;
7. rebuild current-run artifacts;
8. do not reuse old `.gfo` or `.pgf` as proof;
9. review normalization and gold output;
10. remove the old version only after validation.

Different GF releases may use incompatible object or PGF formats.

Isolated installation directories reduce risk.

---

# 25. Upgrade the RGL

Before changing RGL revision:

1. record the current release or commit;
2. obtain the new RGL in a separate checkout or reviewed update;
3. rebuild if using source;
4. update explicit RGL root if needed;
5. run checkpoint validation;
6. run required scenarios;
7. review changed normalized output;
8. update gold only through the explicit gold workflow;
9. preserve prior release evidence.

An RGL update is a project dependency change, not a routine invisible package refresh.

---

# 26. Recreate the virtual environment

Recreate `.venv` when:

- the repository moves;
- the base Python installation moves;
- the Python minor version changes materially;
- installed scripts point to old paths;
- dependency state is corrupted;
- PySide6 import fails after upgrades;
- packaging metadata changes significantly.

Windows PowerShell:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

POSIX:

```bash
deactivate
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Virtual environments are not portable artifacts.

Do not commit `.venv` to version control.

---

# 27. Uninstall GF Wordbench

Inside the environment where it is installed:

```text
python -m pip uninstall gf-wordbench
```

Confirm removal when prompted.

For a repository-local virtual environment, removing `.venv` removes the isolated Python installation.

Uninstallation MUST NOT automatically delete:

- active project source;
- project documentation;
- scenarios;
- gold files;
- output runs;
- GF installation;
- RGL checkout.

Delete those only through explicit project or cleanup procedures.

---

# 28. Remove GF core

GF removal depends on installation method.

Examples:

- delete an extracted Windows binary directory;
- uninstall a platform package;
- remove a Cabal-installed executable according to Haskell tooling policy;
- remove a source checkout separately.

Before removal, confirm no active GF Wordbench configuration references the executable.

---

# 29. Remove the RGL

Remove the RGL directory only when:

- no active project depends on it;
- its revision is recorded where required;
- no release evidence relies on the directory remaining locally available;
- configuration is updated.

Generated run evidence should remain self-describing even if the local RGL checkout is later removed.

---

# 30. Offline installation

An offline installation requires obtaining all dependencies in advance.

Possible package set:

```text
GF Wordbench wheel
PySide6 wheels and dependencies
development wheels when required
GF binary package
RGL binary or source archive
```

On an online machine:

```text
python -m pip download --dest wheelhouse .
```

For development extras:

```text
python -m pip download --dest wheelhouse ".[dev]"
```

On the offline machine:

```text
python -m pip install --no-index --find-links wheelhouse .
```

Exact wheel compatibility depends on:

- Python version;
- operating system;
- CPU architecture.

Offline release procedures SHOULD include hashes or signatures when available.

---

# 31. Multiple Python installations

Windows may have several Python runtimes.

Inspect:

```text
py -0p
```

Create the environment with a specific interpreter:

```text
py -3.11 -m venv .venv
```

After activation:

```text
where python
python -c "import sys; print(sys.executable)"
```

The expected executable should be inside:

```text
<repository>\.venv\Scripts\python.exe
```

POSIX:

```text
which python
python -c "import sys; print(sys.executable)"
```

A successful `pip install` into another interpreter does not install GF Wordbench into the current one.

---

# 32. Common failures

## 32.1 Python version is too old

Symptom:

```text
Package requires a different Python
```

Check:

```text
python --version
```

Fix:

- install a supported Python;
- recreate `.venv`;
- reinstall GF Wordbench.

---

## 32.2 `pip` installs into the wrong Python

Check:

```text
python -m pip --version
python -c "import sys; print(sys.executable)"
```

Fix:

```text
python -m pip install -e ".[dev]"
```

using the intended interpreter.

---

## 32.3 `No module named PySide6`

Cause:

- runtime dependencies were not installed;
- wrong interpreter;
- broken environment.

Fix:

```text
python -m pip install .
```

or:

```text
python -m pip install -e ".[dev]"
```

Then verify:

```text
python -c "import PySide6; print(PySide6.__version__)"
```

---

## 32.4 CLI command is not found

Check package:

```text
python -m pip show gf-wordbench
```

Check script directory:

```text
python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
```

Try module fallback:

```text
python -m app.main_cli --help
```

Fix:

- activate the correct virtual environment;
- reinstall the package;
- confirm final entrypoint names in `pyproject.toml`.

---

## 32.5 GUI does not start

Run with a console:

```text
python -m app.main_gui
```

or set the debug-console launcher variable.

Check:

```text
python -c "import PySide6"
```

Inspect the displayed traceback.

Do not diagnose a GUI import failure as a GF grammar failure.

---

## 32.6 GF executable is not found

Check configured path.

Windows:

```powershell
Test-Path "C:\path\to\gf.exe"
& "C:\path\to\gf.exe" --version
```

POSIX:

```bash
command -v gf
gf --version
```

Fix the explicit GF executable configuration.

Do not rely on an unrelated GF executable found later on `PATH`.

---

## 32.7 RGL modules cannot be found

Check:

- configured RGL root;
- actual RGL directory structure;
- `gf.path_parts`;
- effective GF search path;
- GF/RGL version compatibility.

Do not copy missing RGL modules into the project source tree as a workaround.

---

## 32.8 `GF_LIB_PATH` changes behavior unexpectedly

Inspect:

```text
GF_LIB_PATH
```

Use explicit GF Wordbench RGL and path configuration.

A global environment variable should not silently override recorded run configuration.

---

## 32.9 Path contains spaces

Paths with spaces are supported.

Correct PowerShell invocation:

```powershell
& "C:\Program Files\GF\gf.exe" --version
```

Configuration values should store the raw path without embedded quote characters.

---

## 32.10 PowerShell activation is blocked

Use:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

without activation, or apply an approved user-level execution policy.

---

## 32.11 Repository moved after installation

Virtual-environment scripts contain absolute paths.

Delete and recreate `.venv`.

Do not attempt to repair every generated script manually.

---

## 32.12 Stale command still uses `gf-audit`

Cause:

- legacy editable install;
- old virtual environment;
- old script directory on `PATH`.

Check:

```text
where gf-audit-cli
where gf-wordbench
```

or POSIX:

```text
command -v gf-audit-cli
command -v gf-wordbench
```

Fix:

- uninstall legacy distribution;
- recreate the virtual environment;
- install final `gf-wordbench` metadata.

---

## 32.13 GF version mismatch in `.gfo` or `.pgf`

Cause:

- artifacts produced by another GF version.

Fix:

- do not reuse stale compiled artifacts;
- create a fresh run;
- rebuild `.gfo` and `.pgf` using the configured GF executable.

---

## 32.14 Tests cannot find real GF

Unit tests should not require a developer-global GF installation.

Real-GF tests must be explicitly configured and marked.

Provide the test GF executable and RGL path through documented test configuration.

---

# 33. Security requirements

Installation SHOULD follow these rules:

- obtain Python from an approved source;
- obtain GF from the official GF release source;
- obtain RGL from the official GF RGL source;
- verify release hashes or signatures when provided;
- use a virtual environment;
- do not run installation as administrator unless platform packaging requires it;
- do not store secrets in `project.toml`;
- do not trust arbitrary `.gfs` scenarios;
- review source before installing editable code from an untrusted repository;
- do not add unreviewed directories to system `PATH`;
- do not expose full environment variables in support logs.

A `.gfs` file is executable input to the GF shell and must be treated accordingly.

---

# 34. Reproducible installation record

A release or controlled development environment SHOULD record:

```text
GF Wordbench version
Python version
operating system
CPU architecture
PySide6 version
GF executable path
GF version
RGL release or commit
project schema version
dependency lock or resolved package list
```

Useful commands:

```text
python --version
python -m pip freeze
gf-wordbench --version
<gf-executable> --version
git -C <rgl-checkout> rev-parse HEAD
```

Do not copy secrets or complete environment dumps into the record.

---

# 35. CI installation

Recommended CI order:

```text
1. checkout repository
2. install supported Python
3. create or use isolated environment
4. install `.[dev]`
5. run unit tests without GF
6. install or expose GF for integration job
7. expose compatible RGL
8. run marked integration tests
9. validate project configuration
10. preserve test artifacts
```

Separate:

```text
unit job
real-GF integration job
release-validation job
```

This avoids making every test dependent on external GF installation.

---

# 36. Installation acceptance criteria

The installation procedure is valid when:

```text
[ ] Python requirement matches pyproject.toml
[ ] runtime dependencies install through standard packaging
[ ] development extras install through `.[dev]`
[ ] CLI entrypoint resolves
[ ] GUI entrypoint resolves
[ ] module fallback resolves
[ ] GF executable is external and explicit
[ ] GF version probe works
[ ] RGL root is explicit
[ ] project configuration validates
[ ] paths with spaces work
[ ] launchers are optional
[ ] launchers prefer the repository virtual environment
[ ] installation does not rewrite project source
[ ] installation does not create false run results
[ ] uninstallation preserves project and run data
[ ] upgrade path includes schema and compatibility review
[ ] official installation references are current
```

---

# 37. Anti-drift indicators

Installation drift exists when:

- `pyproject.toml` requires another Python version than this guide;
- package name differs between metadata and commands;
- CLI or GUI script names differ from this guide;
- launchers use another runtime-resolution order without documentation;
- a launcher defines hidden GF paths;
- GF core becomes an undeclared bundled dependency;
- RGL is assumed to be bundled with GF;
- the GUI imports a package not declared as a runtime dependency;
- tests require tools absent from `.[dev]`;
- installation instructions write machine paths into `project.toml`;
- global `GF_LIB_PATH` becomes mandatory without being recorded;
- a wheel-install command assumes a nonexistent public package;
- a virtual environment is described as movable;
- uninstallation deletes project or run data automatically;
- Windows-only launcher behavior is presented as framework semantics.

Any such change requires coordinated review of:

```text
pyproject.toml
launch_cli.bat
launch_gui.bat
app entrypoints
configuration loader
external-tool lock
environment documentation
development setup
CI documentation
this file
```

---

# 38. Official references

Primary GF installation documentation:

- [Grammatical Framework — Download and Installation](https://www.grammaticalframework.org/download/)
- [GF core repository](https://github.com/GrammaticalFramework/gf-core)
- [GF Resource Grammar Library repository](https://github.com/GrammaticalFramework/gf-rgl)

Primary Python environment documentation:

- [Python `venv` documentation](https://docs.python.org/3/library/venv.html)
- [Python packaging installation guide](https://docs.python.org/3/installing/index.html)

GF Wordbench compatibility and package metadata remain authoritative for the exact versions supported by a particular GF Wordbench release.

---

# 39. Cross-references

| Topic | Document |
|---|---|
| Quick start | `docs/usage/QUICK_START.md` |
| CLI commands | `docs/usage/CLI_REFERENCE.md` |
| GUI operation | `docs/usage/GUI_REFERENCE.md` |
| Project configuration | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Application state | `docs/configuration/APPLICATION_STATE_REFERENCE.md` |
| Environment and paths | `docs/configuration/ENVIRONMENT_AND_PATHS.md` |
| GF integration | `docs/gf/GF_TOOLCHAIN_INTEGRATION.md` |
| GF paths | `docs/gf/GF_PATH_RESOLUTION.md` |
| GF compatibility | `docs/gf/GF_VERSION_COMPATIBILITY.md` |
| Windows launchers | `docs/operations/WINDOWS_LAUNCHERS.md` |
| Development setup | `docs/development/DEVELOPMENT_SETUP.md` |
| Testing | `docs/development/TESTING_GF_WORDBENCH.md` |
| Migration | `docs/release/MIGRATION_AND_DEPRECATION.md` |
| Security | `SECURITY.md` |

---

# 40. Final rule

> A successful installation proves that the software components can be found and started; it does not prove that the active language project passes validation.

Verify Python, GF Wordbench, GF core, the RGL, and the active project separately before running release validation.
