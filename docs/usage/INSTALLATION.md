# GF Wordbench — Installation

**Document ID:** `GF-WB-USAGE-INSTALLATION`  
**Status:** Normative installation guide  
**Applies to:** GF Wordbench installation, Python environment setup, GF core and RGL prerequisites, verification, upgrades and removal  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Package authority:** `pyproject.toml`  
**Compatibility authority:** `docs/gf/GF_VERSION_COMPATIBILITY.md`  
**Environment authority:** `docs/configuration/ENVIRONMENT_AND_PATHS.md`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines the supported installation procedures for GF Wordbench.

It covers:

- Python installation;
- virtual-environment creation;
- installation from source or a release wheel;
- development dependencies;
- Grammatical Framework core installation;
- Resource Grammar Library installation;
- Windows launcher behavior;
- installation verification;
- upgrades;
- uninstallation;
- common installation failures.

This document does not define:

- active-project creation;
- `project.toml` fields;
- validation-mode semantics;
- complete CLI syntax;
- GUI workflow;
- GF command syntax;
- release packaging.

Those topics are owned by the referenced documents.

The governing rule is:

> Install Python, GF Wordbench, GF core and the RGL as separate components, then verify each boundary independently.

---

## 2. Product boundary

One GF Wordbench workspace contains one active GF language project.

Installing GF Wordbench does not create:

- a registry of several language projects;
- a multilingual workspace;
- a portfolio database;
- a dependency on `gf-portfolio`.

`gf-portfolio` is a separate product. It may consume public, finalized Wordbench artifacts, but Wordbench installation, startup and validation do not require Portfolio to be installed or available.

---

## 3. Supported installation model

GF Wordbench is a Python application that invokes an external GF executable.

The installation contains four separable parts:

```text
Python runtime
    +
GF Wordbench Python distribution
    +
GF core executable
    +
RGL or other required GF libraries
```

Installing GF Wordbench does not install GF core automatically.

Installing GF core does not guarantee that the RGL is installed.

Installing the RGL does not install the Python application.

Each component has its own version, installation path and verification procedure.

---

## 4. Canonical names

Canonical public names:

```text
Python distribution: gf-wordbench
CLI command:         gf-wordbench
GUI command:         gf-wordbench-gui
```

The Python import-package name and internal module entrypoints are defined by `pyproject.toml` and the repository structure. This guide does not duplicate them.

Legacy GF Audit commands or environment-variable names may be accepted only through documented compatibility behavior. New installation instructions use GF Wordbench names exclusively.

Windows launcher variables, when supported, are defined by:

```text
docs/operations/WINDOWS_LAUNCHERS.md
```

---

## 5. Installation profiles

Choose one profile.

### 5.1 Standard local installation

Use for ordinary local operation from a checked-out source tree.

```text
virtual environment
non-editable package installation
runtime dependencies
```

Command:

```text
python -m pip install .
```

### 5.2 Development installation

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

### 5.3 Release-wheel installation

Use a wheel published through the official GF Wordbench release process.

```text
python -m pip install "<path-to-wheel>"
```

Example filename shape:

```text
gf_wordbench-<version>-py3-none-any.whl
```

Do not assume that a public package index exists unless release documentation explicitly identifies one.

### 5.4 `uv`

`uv` may be used as an optional environment and package manager.

Example development workflow:

```text
uv venv
uv pip install -e ".[dev]"
```

Standard Python packaging through `pyproject.toml` remains authoritative.

---

## 6. Requirements

### 6.1 Python

The authoritative Python requirement is:

```text
pyproject.toml -> requires-python
```

Install a supported 64-bit Python version satisfying that constraint.

Verify:

```text
python --version
```

Windows launcher alternative:

```text
py --version
```

Examples in this guide may use Python 3.11. They do not override `requires-python`.

### 6.2 `pip`

Verify the installer associated with the selected interpreter:

```text
python -m pip --version
```

Use:

```text
python -m pip
```

rather than an unqualified `pip` command when interpreter identity matters.

### 6.3 GF core

GF core is required for compilation, native `.gfs` scenario execution and release validation.

Executable names:

```text
gf
gf.exe
```

Verify the selected executable:

```text
<gf-executable> --version
```

The exact supported version range is defined by:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

This guide does not freeze a current GF release number.

### 6.4 Resource Grammar Library

The RGL is required when the active project imports RGL modules.

GF Wordbench requires a resolvable RGL root and compatible GF search path. It does not require one particular RGL installation method.

### 6.5 Git

Git is useful for source checkouts and development.

Verify:

```text
git --version
```

Git is not required when installing from a wheel, source archive or existing checkout.

### 6.6 Operating system

The supported platform matrix is defined by release and compatibility documentation.

Installation depends on:

- Python availability;
- GUI dependency availability when the GUI is installed;
- GF binary availability;
- path and process integration support.

CLI and GUI support may differ by platform. This guide does not imply support beyond the published compatibility matrix.

---

## 7. Python dependencies

`pyproject.toml` is authoritative for:

```text
runtime dependencies
development extras
build backend
Python requirement
console entrypoints
package contents
```

Do not copy dependency versions from this guide into packaging metadata.

To inspect resolved package metadata after installation:

```text
python -m pip show gf-wordbench
```

To inspect all installed packages:

```text
python -m pip list
```

---

## 8. Directory layout

A clear local layout keeps source, tools, libraries and generated runs separate.

Example:

```text
workspace-parent/
├── GF_Wordbench/
├── gf-core-installation/
├── gf-rgl/
└── gf-wordbench-runs/
```

The components do not need to be siblings.

The installation must not depend on a particular absolute path, drive letter, username or parent-directory name.

Paths containing spaces and Unicode must work according to the platform contracts.

---

## 9. Obtain GF Wordbench

### 9.1 Git checkout

Clone from the official repository URL supplied by the release or project-maintenance documentation:

```text
git clone <GF-WORDBENCH-REPOSITORY-URL>
cd <GF-WORDBENCH-CHECKOUT>
```

The installation root is the directory containing:

```text
pyproject.toml
docs/
project/
templates/
```

The application package directory is determined by `pyproject.toml` and the repository layout.

Do not install from a nested documentation or package subdirectory.

### 9.2 Source archive

Extract the official source archive.

Open a terminal in the directory containing:

```text
pyproject.toml
```

Verify the archive according to the release security policy.

### 9.3 Release wheel

Obtain the wheel from the official GF Wordbench release channel.

Verify the release artifact before installation.

---

## 10. Create a virtual environment

A repository-local environment named `.venv` is recommended.

Virtual environments are disposable. Recreate them after moving a checkout or changing the base interpreter.

### 10.1 Windows PowerShell

```powershell
py -3.11 -m venv .venv
```

When another supported interpreter command is used:

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

### 10.2 Windows Command Prompt

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

Verify:

```bat
python --version
python -m pip --version
```

### 10.3 Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verify:

```bash
python --version
python -m pip --version
```

### 10.4 Activation is optional

Windows:

```text
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

POSIX:

```text
.venv/bin/python -m pip install -e ".[dev]"
```

Explicit interpreter paths are preferable in automation.

### 10.5 PowerShell execution policy

PowerShell may block `Activate.ps1`.

Follow local security policy. Activation can be avoided by invoking:

```powershell
.\.venv\Scripts\python.exe
```

directly.

Changing PowerShell execution policy is an operating-system administration decision, not a GF Wordbench requirement.

---

## 11. Prepare packaging tools

Inside the selected environment:

```text
python -m pip install --upgrade pip
```

The build backend declared in `pyproject.toml` is installed by the packaging frontend when isolated builds are used.

A global installation of the build backend is not required for normal installation.

---

## 12. Install GF Wordbench

### 12.1 Standard source installation

```text
python -m pip install .
```

This installs:

- the GF Wordbench distribution;
- runtime dependencies;
- declared CLI entrypoint;
- declared GUI entrypoint.

Source edits require reinstallation.

### 12.2 Development installation

```text
python -m pip install -e ".[dev]"
```

This installs the package in editable mode together with the declared development extra.

Source edits are visible without reinstalling. Packaging metadata changes may require reinstalling.

### 12.3 Runtime-only editable installation

```text
python -m pip install -e .
```

### 12.4 Wheel installation

```text
python -m pip install "<path-to-wheel>"
```

The actual wheel name and version come from the release.

### 12.5 Reinstallation

Standard reinstall:

```text
python -m pip install --force-reinstall .
```

Editable reinstall after packaging changes:

```text
python -m pip install -e ".[dev]"
```

---

## 13. Verify the Python installation

### 13.1 Distribution metadata

```text
python -c "from importlib.metadata import version; print(version('gf-wordbench'))"
```

Expected result:

```text
installed GF Wordbench version
```

This verification does not depend on a duplicated internal import-package name.

### 13.2 Package metadata

```text
python -m pip show gf-wordbench
```

Confirm:

- the intended interpreter environment;
- installation location;
- version;
- dependencies.

### 13.3 CLI entrypoint

```text
gf-wordbench --help
```

Use the version command defined by `docs/usage/CLI_REFERENCE.md`.

### 13.4 GUI entrypoint

```text
gf-wordbench-gui
```

The GUI should start from the installed distribution rather than importing an unrelated checkout.

### 13.5 Module diagnostics

Internal module execution is not a public installation contract unless explicitly documented in `CLI_REFERENCE.md`, `GUI_REFERENCE.md` or `pyproject.toml`.

Use installed console entrypoints for normal verification.

---

## 14. Install GF core

Install a GF version supported by:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

GF may be installed through:

- an official platform binary package;
- an approved operating-system package;
- Hackage with a compatible Haskell toolchain;
- a reviewed source build.

Binary installation is preferred for ordinary Wordbench use.

### 14.1 Windows binary installation

1. Obtain a supported GF binary package from the official GF release source.
2. Extract it to a stable machine-local directory.
3. Locate `gf.exe`.
4. record the full path;
5. verify it explicitly.

PowerShell example:

```powershell
& "C:\path\to\gf.exe" --version
```

Adding the directory to `PATH` is optional when Wordbench is configured with the explicit executable.

### 14.2 Debian or Ubuntu package

Install the package matching the supported GF release and operating-system version.

Example shape:

```bash
sudo apt install ./gf-<version>-<platform>.deb
```

Use the filename supplied by the official release.

Verify:

```bash
gf --version
```

### 14.3 macOS binary package

Install the package matching the machine architecture and supported GF version.

Follow official GF instructions and local security policy for package approval.

Verify:

```bash
gf --version
```

### 14.4 Hackage installation

With a compatible Haskell toolchain:

```bash
cabal update
cabal install gf-<supported-version>
```

Record the resulting executable path.

### 14.5 Source installation

Obtain `gf-core` from its official source repository and select a reviewed release tag or commit.

Build according to the official GF source instructions.

For reproducible validation, record:

- source revision;
- build toolchain;
- resulting executable path;
- GF version output.

Do not use an unrecorded moving branch for release validation.

---

## 15. Install the RGL

GF core and the RGL are separate components.

The active project may depend on:

```text
abstract
common
prelude
api
language-specific RGL modules
```

### 15.1 Binary RGL release

1. Obtain a compatible RGL package.
2. Extract it to a stable location.
3. identify the root required by the configured GF search path;
4. record the resolved path.

### 15.2 Source checkout

Obtain `gf-rgl` from its official source repository.

A common source root is:

```text
<rgl-checkout>/src
```

Use the actual checkout structure. Do not infer the root from the directory name alone.

### 15.3 Source build

When the selected RGL requires compilation, follow its release or repository build instructions.

GF Wordbench does not build the RGL automatically during ordinary application installation.

### 15.4 Compatibility

GF and RGL must be selected as a compatible pair.

Record:

- GF version;
- RGL release or commit;
- resolved RGL root;
- effective GF search path.

Compatibility is governed by project and GF compatibility documentation.

---

## 16. Verify GF and the RGL

### 16.1 GF version probe

```text
<gf-executable> --version
```

### 16.2 Basic startup

Start the selected executable and exit after confirming that it launches.

### 16.3 Wordbench verification

Configure:

- active project root;
- GF executable;
- RGL root;
- output root.

Then use the project and validation commands defined by:

```text
docs/usage/CLI_REFERENCE.md
```

### 16.4 Direct GF diagnosis

A direct GF invocation may be used to diagnose an installation boundary.

It is not a substitute for Wordbench command construction, evidence capture or project configuration.

Permanent validation commands are built through the Wordbench GF command contract.

---

## 17. Configure machine-local paths

Machine-local settings do not belong in `project.toml`.

Typical machine-local values:

```text
active project root
GF executable
RGL root
output root
application-state path
```

They may be supplied through:

- explicit CLI values;
- GUI values;
- documented environment variables;
- disposable application state;
- documented defaults or discovery.

The authoritative precedence and variable names are defined by:

```text
docs/configuration/ENVIRONMENT_AND_PATHS.md
```

Resolved values must be visible in run metadata and diagnostic configuration views.

Do not store quote characters inside path values.

---

## 18. Validate the active project

The active project contains:

```text
project/project.toml
```

or an explicitly selected project root containing `project.toml`, according to the environment-and-path contract.

The project file declares its schema identity and version.

Use the project-check operation defined by `docs/usage/CLI_REFERENCE.md`.

A successful package installation does not prove that the active GF project is valid.

---

## 19. First CLI verification

Verification order:

```text
1. display CLI help
2. display installed version
3. inspect resolved configuration
4. validate the active project
5. run the smallest applicable validation mode
```

Exact command spelling and options are defined by:

```text
docs/usage/CLI_REFERENCE.md
```

This installation guide must not preserve examples that disagree with the canonical CLI parser.

---

## 20. First GUI verification

Start:

```text
gf-wordbench-gui
```

Confirm that the GUI can:

- load application defaults;
- resolve the one active project;
- display GF executable configuration;
- display RGL-root configuration;
- display output-root configuration;
- validate configuration;
- close without an unhandled exception.

Begin with project inspection or the smallest applicable validation operation, not release validation.

---

## 21. Windows launchers

Repository convenience launchers may include:

```text
launch_cli.bat
launch_gui.bat
```

They are optional.

The Python distribution and installed console entrypoints remain canonical.

### 21.1 Responsibilities

A launcher may:

- resolve the repository root;
- prefer a repository-local virtual environment;
- use a documented explicit Python override;
- optionally use `uv`;
- enforce documented UTF-8 behavior;
- start the canonical CLI or GUI entrypoint;
- propagate meaningful exit codes;
- keep a console visible after a launch failure.

A launcher must not:

- define validation semantics;
- change source selection;
- override project identity;
- construct a different GF search path;
- hide the selected interpreter;
- become the only supported execution method;
- discover or launch `gf-portfolio`.

### 21.2 Runtime resolution

The runtime resolution order and supported launcher variables are defined by:

```text
docs/operations/WINDOWS_LAUNCHERS.md
```

### 21.3 Legacy aliases

Legacy GF Audit launcher variables may be accepted only through explicit compatibility behavior.

New examples use GF Wordbench variable names.

### 21.4 Invocation

```bat
launch_cli.bat --help
launch_gui.bat
```

Launchers resolve their repository root rather than depending on the caller's current directory.

---

## 22. Development verification

Use the quality commands defined by:

```text
docs/development/TESTING_GF_WORDBENCH.md
```

Typical operations include:

```text
python -m pytest
python -m ruff check .
python -m mypy <declared-package-root>
python -m pytest --cov=<declared-package-root> --cov-report=term-missing
```

The package root and exact quality gates are owned by `pyproject.toml` and the testing guide.

Real-GF integration tests are separated from unit tests that use fake process results.

---

## 23. Installation verification checklist

```text
[ ] supported Python installed
[ ] intended Python interpreter selected
[ ] virtual environment created
[ ] GF Wordbench distribution installed
[ ] distribution metadata query succeeds
[ ] CLI entrypoint resolves
[ ] GUI entrypoint resolves when GUI support is installed
[ ] GF executable exists
[ ] GF version probe succeeds
[ ] RGL root exists when required
[ ] active project configuration exists
[ ] project validation succeeds
[ ] output root is writable
[ ] smallest applicable validation can start
[ ] development test suite passes for development installations
```

Installation is complete when every applicable required item is verified.

---

## 24. Upgrade GF Wordbench

### 24.1 Editable source checkout

Update source through the repository's approved workflow.

Refresh dependencies and entrypoints:

```text
python -m pip install -e ".[dev]"
```

Then:

```text
python -m pytest
gf-wordbench --help
```

Run the documented version, project and schema checks.

### 24.2 Standard source installation

After updating source:

```text
python -m pip install --upgrade .
```

When dependency state is uncertain:

```text
python -m pip install --force-reinstall .
```

### 24.3 Wheel installation

```text
python -m pip install --upgrade "<new-wheel>"
```

Run configuration, project and schema checks afterward.

### 24.4 Migration

An application upgrade may require:

- application-state migration;
- project-schema migration;
- summary-reader migration;
- normalization or gold review.

Migration is explicit and follows:

```text
docs/release/MIGRATION_AND_DEPRECATION.md
```

Do not delete or overwrite old data before the replacement validates successfully.

---

## 25. Upgrade GF core

Before replacing GF:

1. review the compatibility policy;
2. record the current GF version;
3. install the new version in a separate location when possible;
4. configure Wordbench explicitly to use it;
5. run the version probe;
6. run integration checks;
7. create new run artifacts;
8. do not reuse old `.gfo` or `.pgf` as proof;
9. review normalized and gold output;
10. remove the previous installation only after validation.

GF releases may use incompatible object or PGF formats.

---

## 26. Upgrade the RGL

Before changing RGL revision:

1. record the current release or commit;
2. obtain the replacement in a separate checkout or reviewed update;
3. build it when required;
4. update the explicit RGL root;
5. run checkpoint validation;
6. run required scenarios;
7. review normalized output changes;
8. update gold only through the explicit gold workflow;
9. preserve prior run evidence.

An RGL update is a project dependency change.

---

## 27. Recreate the virtual environment

Recreate `.venv` when:

- the checkout moves;
- the base Python installation moves;
- the Python version changes;
- generated scripts point to stale paths;
- dependency state is corrupted;
- GUI dependencies fail after upgrades;
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
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Do not commit `.venv` to version control.

---

## 28. Uninstall GF Wordbench

Inside the environment where it is installed:

```text
python -m pip uninstall gf-wordbench
```

Removing a repository-local `.venv` also removes that isolated package installation.

Uninstallation must not automatically delete:

- active project source;
- project documentation;
- scenarios;
- gold files;
- run directories;
- GF installation;
- RGL checkout;
- Portfolio data owned by another product.

Delete those only through their explicit maintenance procedures.

---

## 29. Remove GF core or the RGL

Before removing GF core, confirm that no active Wordbench environment references its executable.

Before removing the RGL, confirm that:

- no active project depends on it;
- the revision is recorded where required;
- configuration is updated;
- required historical evidence remains available or self-describing.

Run evidence should remain interpretable after local tool installations are removed.

---

## 30. Offline installation

Prepare all required packages in advance:

```text
GF Wordbench wheel or source archive
runtime dependency wheels
development wheels when required
GF binary package
RGL binary or source archive
```

On an online machine, prepare a wheelhouse using the source or wheel release inputs.

Example:

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

Offline release procedures include hashes or signatures when supplied by the release channel.

---

## 31. Multiple Python installations

Windows:

```text
py -0p
py -3.11 -m venv .venv
where python
python -c "import sys; print(sys.executable)"
```

POSIX:

```text
which python
python -c "import sys; print(sys.executable)"
```

The selected interpreter should resolve inside the intended virtual environment.

Installing with another interpreter's `pip` does not install Wordbench into the current environment.

---

## 32. Common failures

### 32.1 Unsupported Python version

Check:

```text
python --version
```

Install a version satisfying `pyproject.toml`, recreate `.venv` and reinstall.

### 32.2 Package installed into the wrong interpreter

Check:

```text
python -m pip --version
python -c "import sys; print(sys.executable)"
```

Reinstall with the intended interpreter.

### 32.3 GUI dependency missing

Check the runtime dependencies declared by `pyproject.toml`.

Reinstall the distribution or development extra in the intended environment.

Do not diagnose a Python GUI import failure as a GF grammar failure.

### 32.4 CLI command not found

Check:

```text
python -m pip show gf-wordbench
python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
```

Activate the intended environment or call its interpreter explicitly, then reinstall.

### 32.5 GUI does not start

Start the installed GUI entrypoint from a visible terminal when supported by the platform.

Inspect the Python exception and dependency state.

### 32.6 GF executable not found

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

Fix explicit GF executable configuration. Do not silently substitute another installation.

### 32.7 RGL modules not found

Check:

- RGL root;
- actual directory structure;
- project GF path parts;
- resolved GF search path;
- GF/RGL compatibility.

Do not copy missing RGL modules into project source as an installation workaround.

### 32.8 Ambient GF path changes behavior

Inspect relevant GF environment variables.

Use explicit Wordbench path configuration. Ambient variables must not override the recorded execution contract silently.

### 32.9 Paths contain spaces

Pass executable paths as separate arguments.

PowerShell example:

```powershell
& "C:\Program Files\GF\gf.exe" --version
```

Stored path values do not include shell quote characters.

### 32.10 PowerShell activation blocked

Invoke the environment interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### 32.11 Checkout moved

Virtual-environment scripts contain absolute paths.

Recreate `.venv`.

### 32.12 Legacy GF Audit command remains

Cause:

- old editable installation;
- old environment;
- stale scripts on `PATH`.

Remove the legacy distribution or environment and reinstall `gf-wordbench`.

Legacy commands are compatibility inputs, not canonical installation names.

### 32.13 Stale `.gfo` or `.pgf`

Create a new run with the selected GF executable.

Do not use artifacts produced by another GF version as proof of current validation.

### 32.14 Tests cannot find GF

Unit tests do not require a developer-global GF installation.

Real-GF tests use explicit documented configuration and markers.

---

## 33. Security requirements

Installation follows these rules:

- obtain Python from an approved source;
- obtain GF and RGL from their official or approved release sources;
- verify hashes or signatures when supplied;
- use an isolated Python environment;
- avoid administrator privileges unless platform packaging requires them;
- do not store secrets in `project.toml`;
- treat `.gfs` scenarios as executable GF-shell input;
- review editable source before installation;
- do not add unreviewed directories to system `PATH`;
- do not include complete environment dumps in support records;
- do not install `gf-portfolio` as an undeclared Wordbench dependency.

---

## 34. Reproducible installation record

A controlled environment records:

```text
GF Wordbench version
Python version
operating system
CPU architecture
resolved Python dependencies
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
python -c "from importlib.metadata import version; print(version('gf-wordbench'))"
<gf-executable> --version
git -C <rgl-checkout> rev-parse HEAD
```

Do not record secrets or a complete environment dump.

---

## 35. CI installation

Canonical CI stages:

```text
1. checkout repository
2. install supported Python
3. create or select an isolated environment
4. install the declared development extra
5. run unit tests without GF
6. install or expose GF for integration jobs
7. expose a compatible RGL
8. run marked real-GF integration tests
9. validate the active project
10. preserve test artifacts
```

Separate:

```text
unit job
real-GF integration job
release-validation job
```

This keeps unit tests independent of external GF installation.

---

## 36. Installation acceptance criteria

```text
[ ] Python requirement matches pyproject.toml
[ ] runtime dependencies install through standard packaging
[ ] development extras install through the declared extra
[ ] CLI entrypoint resolves
[ ] GUI entrypoint resolves when supported
[ ] distribution metadata query succeeds
[ ] GF executable remains external and explicit
[ ] GF version probe succeeds
[ ] RGL root is explicit when required
[ ] active-project configuration validates
[ ] paths with spaces work
[ ] launchers remain optional
[ ] installation does not rewrite project source
[ ] installation does not create false run results
[ ] Wordbench installation does not depend on gf-portfolio
[ ] uninstallation preserves project and run data
[ ] upgrades include schema and compatibility review
```

---

## 37. Anti-drift indicators

Installation drift exists when:

- `pyproject.toml` and this guide disagree on Python support;
- distribution or console-command names differ;
- launcher behavior conflicts with `WINDOWS_LAUNCHERS.md`;
- a launcher introduces hidden GF paths;
- GF core becomes an undeclared bundled dependency;
- the RGL is assumed to be bundled with GF;
- a GUI dependency is absent from package metadata;
- development tests require tools absent from the declared development extra;
- machine-local paths are written into `project.toml`;
- ambient GF environment variables become mandatory without being recorded;
- a wheel command assumes an unpublished package source;
- a virtual environment is described as portable;
- uninstallation deletes project or run data;
- Windows launcher behavior is presented as framework semantics;
- internal Python package names are duplicated here and drift from `pyproject.toml`;
- Wordbench installation requires Portfolio code, configuration or storage.

Coordinated review includes:

```text
pyproject.toml
launch_cli.bat
launch_gui.bat
application composition root
configuration and path resolution
external-tool lock
development setup
testing and CI documentation
CLI and GUI references
this file
```

---

## 38. Official references

Primary GF sources:

- [Grammatical Framework — Download and Installation](https://www.grammaticalframework.org/download/)
- [GF core repository](https://github.com/GrammaticalFramework/gf-core)
- [GF Resource Grammar Library repository](https://github.com/GrammaticalFramework/gf-rgl)

Primary Python sources:

- [Python `venv` documentation](https://docs.python.org/3/library/venv.html)
- [Installing Python modules](https://docs.python.org/3/installing/index.html)

GF Wordbench package metadata and compatibility documents remain authoritative for versions supported by a particular release.

---

## 39. Cross-references

| Topic | Document |
|---|---|
| Product boundary | `docs/architecture/PRODUCT_BOUNDARIES.md` |
| Quick start | `docs/usage/QUICK_START.md` |
| CLI commands | `docs/usage/CLI_REFERENCE.md` |
| GUI operation | `docs/usage/GUI_REFERENCE.md` |
| Project configuration | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Application state | `docs/configuration/APPLICATION_STATE_REFERENCE.md` |
| Environment and paths | `docs/configuration/ENVIRONMENT_AND_PATHS.md` |
| GF integration | `docs/gf/GF_TOOLCHAIN_INTEGRATION.md` |
| GF command construction | `docs/gf/GF_COMMAND_CONSTRUCTION.md` |
| GF paths | `docs/gf/GF_PATH_RESOLUTION.md` |
| GF compatibility | `docs/gf/GF_VERSION_COMPATIBILITY.md` |
| Windows launchers | `docs/operations/WINDOWS_LAUNCHERS.md` |
| Development setup | `docs/development/DEVELOPMENT_SETUP.md` |
| Testing | `docs/development/TESTING_GF_WORDBENCH.md` |
| Migration | `docs/release/MIGRATION_AND_DEPRECATION.md` |
| Security | `SECURITY.md` |

---

## 40. Governing rule

> A successful installation proves that the software components can be found and started; it does not prove that the active GF language project passes validation.

Verify Python, GF Wordbench, GF core, the RGL and the active project independently before release validation.
