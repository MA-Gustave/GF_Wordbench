# GF Wordbench — Windows Launchers

**Document ID:** `GF-WB-OPERATIONS-WINDOWS-LAUNCHERS`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\operations\WINDOWS_LAUNCHERS.md`  
**Applies to:** Repository-local Windows batch launchers for the CLI and GUI  
**Owner:** GF Wordbench maintainers  
**Canonical launchers:** `launch_cli.bat`, `launch_gui.bat`  
**Python entrypoints:** `app.main_cli:main`, `app.main_gui:main`  
**Package name:** `gf-wordbench`  
**CLI command:** `gf-wordbench`  
**GUI command:** `gf-wordbench-gui`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines the final contract for the Windows batch launchers shipped at the root of the GF Wordbench repository.

The launchers provide convenient Windows entry points for:

```text
command-line use
graphical use
repository-local development
double-click startup
diagnostic startup
```

They are intentionally thin.

Their job is limited to:

1. locating their own repository copy;
2. verifying the minimum repository markers required for startup;
3. selecting an approved Python runtime;
4. establishing a predictable UTF-8 process environment;
5. starting the canonical Python module;
6. forwarding caller arguments;
7. returning a meaningful launcher or application result.

The central rule is:

> A Windows launcher starts GF Wordbench; it does not configure, implement, repair, install or reinterpret GF Wordbench.

---

## 2. Scope

This document governs:

- `launch_cli.bat`;
- `launch_gui.bat`;
- repository-root discovery;
- Python-runtime resolution;
- environment-variable overrides;
- UTF-8 startup settings;
- current-working-directory handling;
- argument forwarding;
- CLI help behavior;
- GUI windowed and debug-console behavior;
- launcher-specific error handling;
- exit-code propagation;
- quoting and path safety;
- Windows path handling;
- migration from `gf-audit` launcher names and variables;
- launcher tests;
- launcher anti-drift rules.

This document does not govern:

- CLI argument definitions;
- GUI behavior after startup;
- Python dependency installation;
- virtual-environment creation;
- GF executable discovery;
- RGL discovery;
- active-project configuration;
- application-state schema;
- audit execution;
- scenario execution;
- report generation;
- Windows installer packaging;
- Start Menu shortcuts;
- desktop shortcuts;
- PowerShell launchers;
- shell integration.

---

## 3. Related normative documents

```text
docs/REPOSITORY_STRUCTURE.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/usage/INSTALLATION.md
docs/usage/CLI_REFERENCE.md
docs/usage/GUI_REFERENCE.md
docs/reference/EXIT_CODES.md
docs/development/DEVELOPMENT_SETUP.md
docs/operations/AUTOMATION_AND_CI.md
pyproject.toml
app/main_cli.py
app/main_gui.py
```

`CLI_REFERENCE.md` owns CLI arguments.

`GUI_REFERENCE.md` owns GUI behavior.

`EXIT_CODES.md` owns the global exit-code registry.

This document owns only the Windows launcher boundary.

---

## 4. Normative terminology

- **LAUNCHER**: repository-root `.bat` script that starts one canonical Python entrypoint.
- **REPOSITORY ROOT**: directory containing the launcher and required GF Wordbench root markers.
- **CLI LAUNCHER**: `launch_cli.bat`.
- **GUI LAUNCHER**: `launch_gui.bat`.
- **PYTHON OVERRIDE**: explicit `GF_WORDBENCH_PYTHON` interpreter path.
- **LOCAL VIRTUAL ENVIRONMENT**: `.venv\Scripts\python.exe` under the repository root.
- **WINDOWED RUNTIME**: `pythonw.exe` or `pyw` used to start the GUI without a Python console.
- **CONSOLE RUNTIME**: `python.exe`, `py` or `python` used for visible diagnostics.
- **DEBUG CONSOLE MODE**: GUI launch mode selected with `GF_WORDBENCH_DEBUG_CONSOLE=1`.
- **DISPATCH SUCCESS**: the launcher successfully requested process startup.
- **APPLICATION EXIT CODE**: result returned by the Python entrypoint when the launcher waits for it.
- **LAUNCHER FAILURE**: failure before the canonical Python entrypoint begins.
- **THIN WRAPPER**: launcher containing environment and process-startup logic only.
- **LEGACY VARIABLE**: `GF_AUDIT_*` environment variable from the predecessor system.

---

## 5. Canonical files

Repository root:

```text
GF_Wordbench/
├── launch_cli.bat
├── launch_gui.bat
├── pyproject.toml
└── app/
    ├── __init__.py
    ├── main_cli.py
    └── main_gui.py
```

No additional batch launcher is required for the final core system.

In particular, the framework does not require:

```text
launch_debug.bat
launch_release.bat
launch_scan.bat
launch_project.bat
launch_admin.bat
install_and_launch.bat
```

Those responsibilities belong to CLI arguments, application services or installation documentation.

---

## 6. Canonical entrypoints

### 6.1 CLI module

```text
python -m app.main_cli
```

Installed console command:

```text
gf-wordbench
```

Packaging entry:

```toml
[project.scripts]
gf-wordbench = "app.main_cli:main"
```

### 6.2 GUI module

```text
python -m app.main_gui
```

Installed GUI command:

```text
gf-wordbench-gui
```

Packaging entry:

```toml
[project.gui-scripts]
gf-wordbench-gui = "app.main_gui:main"
```

### 6.3 Repository-local rule

The root launchers use the module entrypoints:

```text
app.main_cli
app.main_gui
```

They do not require the console scripts to have been installed.

This guarantees that a launcher in a repository copy starts that repository copy.

---

## 7. Launcher responsibilities

Both launchers own:

```text
repository-root resolution
minimum repository-marker checks
Python-runtime resolution
UTF-8 startup environment
working-directory setup
canonical module invocation
argument forwarding
launcher error messages
result handling
```

The CLI launcher additionally owns:

```text
no-argument help dispatch
full application exit-code propagation
```

The GUI launcher additionally owns:

```text
windowed runtime preference
debug-console selection
windowed dispatch behavior
```

---

## 8. Prohibited launcher responsibilities

A launcher MUST NOT:

```text
parse project.toml
read or write application state
select a language
select a GF source tree
construct GF paths
locate gf.exe
locate the RGL
run GF directly
compile `.gf` files
build `.gfo` files
build `.pgf` files
run `.gfs` scenarios
normalize output
update gold files
create run directories
write reports
classify failures
perform repository reset
perform project migration
install Python
install dependencies
create a virtual environment
run pip install
run uv sync
download tools
modify PATH permanently
modify the registry
request elevation
run Git commands
commit files
clean untracked files
repair configuration
```

If a launcher begins to own one of these responsibilities, the architecture has drifted.

---

# Part I — Shared launcher contract

## 9. Repository-root resolution

Each launcher resolves its repository root from its own physical location.

Canonical batch principle:

```bat
for %%I in ("%~dp0.") do set "REPO_ROOT=%%~fI"
```

The final implementation may use an equivalent safe form.

### 9.1 Current directory is not authoritative

The launcher MUST NOT assume that the caller’s current directory is the repository root.

Valid launch contexts include:

```text
double-click from Explorer
Command Prompt in another directory
PowerShell in another directory
another batch script
a desktop shortcut
a test harness
```

### 9.2 No upward search

The launcher does not recursively search parent directories.

Its own directory is expected to be the repository root.

This avoids accidentally starting another checkout.

### 9.3 Normalized root

The root must be resolved to an absolute Windows path.

It must support:

```text
spaces
parentheses
Unicode
drive letters
UNC paths where the selected tools support them
```

---

## 10. Repository-marker checks

Before runtime resolution, both launchers verify at least:

```text
<REPO_ROOT>\pyproject.toml
<REPO_ROOT>\app\__init__.py
```

The CLI launcher also verifies:

```text
<REPO_ROOT>\app\main_cli.py
```

The GUI launcher also verifies:

```text
<REPO_ROOT>\app\main_gui.py
```

### 10.1 Purpose

These checks detect:

- a moved launcher copied without the repository;
- an incomplete checkout;
- an incorrect shortcut target;
- an accidental working-directory assumption;
- a damaged package structure.

### 10.2 Limits

Marker checks do not prove that:

```text
dependencies are installed
the active project is valid
GF is installed
the RGL is available
the application will pass startup validation
```

Those checks belong to Python.

---

## 11. Batch environment discipline

Canonical batch header:

```bat
@echo off
setlocal EnableExtensions DisableDelayedExpansion
```

### 11.1 `setlocal`

All launcher environment changes are process-local.

The launcher MUST NOT leave environment changes in the parent shell.

### 11.2 Delayed expansion

Delayed expansion remains disabled by default.

This avoids altering argument or path text containing:

```text
!
```

### 11.3 Command extensions

Command extensions are enabled because the launchers use standard batch control constructs and subroutines.

---

## 12. UTF-8 startup environment

Both launchers set, within `setlocal`:

```text
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

### 12.1 Purpose

These values make Python startup and standard-stream encoding predictable for:

```text
Unicode source paths
Unicode project names
GF output
diagnostics
reports
console output
```

### 12.2 Scope

The variables apply only to the launcher process and its child.

They are not written permanently.

### 12.3 Code page

The launcher SHOULD NOT run:

```bat
chcp 65001
```

by default.

Changing the caller’s console code page is broader than required and may affect the surrounding shell.

Python controls its own UTF-8 behavior through the documented environment and `-X utf8`.

### 12.4 Batch text

The `.bat` files themselves SHOULD use ASCII-only comments and messages.

This avoids dependence on the active `cmd.exe` code page.

---

## 13. Python bytecode policy

The launchers do not need to set:

```text
PYTHONDONTWRITEBYTECODE
```

Python bytecode caching is a runtime optimization and belongs to normal Python behavior.

Generated `__pycache__/` directories are excluded by repository policy.

A development environment may set this variable independently.

---

## 14. `PYTHONPATH` policy

The launchers MUST NOT construct a project-specific `PYTHONPATH`.

They instead:

1. change to the repository root;
2. invoke the package with `-m`.

Canonical principle:

```text
working directory = repository root
entrypoint = python -m app.main_cli
```

or:

```text
working directory = repository root
entrypoint = python -m app.main_gui
```

### 14.1 No global modification

The launcher MUST NOT permanently add the repository to `PYTHONPATH`.

### 14.2 Existing `PYTHONPATH`

The launcher does not depend on an inherited `PYTHONPATH`.

Tests should verify that the repository-local `app` package is selected.

---

## 15. Working directory

Before starting Python:

```text
pushd "<REPO_ROOT>"
```

After a synchronous launch:

```text
popd
```

### 15.1 Purpose

A stable working directory supports:

- module resolution;
- repository-relative defaults;
- predictable diagnostics;
- consistent GUI and CLI startup;
- path tests.

### 15.2 `pushd` failure

Failure to enter the root is a launcher failure.

Python is not started.

### 15.3 UNC behavior

`pushd` may provide a temporary drive mapping for a UNC path.

The launcher must pair successful `pushd` with `popd`.

No drive mapping may be left behind intentionally.

---

## 16. Environment-variable vocabulary

Canonical launcher variables:

```text
GF_WORDBENCH_PYTHON
GF_WORDBENCH_DEBUG_CONSOLE
```

No other environment variable is required by the final launcher contract.

### 16.1 Naming

All GF Wordbench-specific environment variables use:

```text
GF_WORDBENCH_
```

### 16.2 No project values

Launcher variables MUST NOT carry:

```text
language identity
project entrypoints
scan rules
GF paths
release criteria
scenario IDs
gold policy
```

---

## 17. `GF_WORDBENCH_PYTHON`

### 17.1 Purpose

Provides an explicit console-capable Python interpreter.

Example:

```bat
set "GF_WORDBENCH_PYTHON=C:\Python312\python.exe"
```

### 17.2 Value contract

The value is:

```text
one executable filesystem path
```

It MUST NOT contain:

```text
surrounding quote characters
command arguments
environment assignments
shell operators
redirection
a command alias
```

Correct:

```text
C:\Tools\Python\python.exe
```

Incorrect:

```text
"C:\Tools\Python\python.exe"
python -X utf8
C:\Tools\Python\python.exe & echo unsafe
```

### 17.3 Validation

When the variable is defined:

- its path must exist;
- it must not be a directory;
- it takes precedence over automatic runtime resolution;
- a missing path is an explicit launcher failure;
- the launcher does not silently fall back to another runtime.

### 17.4 Console interpreter

The canonical override points to `python.exe`, not `pythonw.exe`.

The GUI launcher may derive a sibling `pythonw.exe` for normal windowed startup.

Debug-console mode always uses the console interpreter.

---

## 18. `GF_WORDBENCH_DEBUG_CONSOLE`

### 18.1 Purpose

Forces the GUI launcher to use a console-capable runtime.

Example:

```bat
set "GF_WORDBENCH_DEBUG_CONSOLE=1"
launch_gui.bat
```

### 18.2 Enabled value

Canonical enabled value:

```text
1
```

Other values mean disabled.

### 18.3 Behavior

When enabled:

- GUI starts through a console runtime;
- startup tracebacks remain visible;
- stdout and stderr remain attached;
- the launcher waits for completion;
- application exit code is propagated.

### 18.4 Scope

This variable affects only the GUI launcher.

It does not enable application debug features automatically.

Application logging levels remain application configuration.

---

# Part II — Python runtime resolution

## 19. Shared console-runtime order

The canonical console-runtime resolution order is:

```text
1. GF_WORDBENCH_PYTHON
2. <REPO_ROOT>\.venv\Scripts\python.exe
3. Windows Python launcher: py -3
4. python.exe on PATH
```

The first available valid choice wins.

### 19.1 Why the order is stable

- explicit override supports controlled environments;
- repository-local `.venv` provides project isolation;
- `py -3` is a standard Windows fallback;
- `python` on `PATH` is the broadest fallback.

### 19.2 No `uv` launcher dependency

The final batch launchers do not require or auto-select `uv`.

`uv` may be used during installation or development, but it is not required at launcher runtime.

This keeps the launcher boundary small and avoids hidden environment synchronization.

### 19.3 No Conda-specific logic

A currently activated Conda environment may be reached through `python` on `PATH`.

The launchers do not implement a separate Conda resolver.

### 19.4 No registry search

The launchers do not search the Windows registry for Python installations.

The Windows Python launcher already owns registered-interpreter selection.

---

## 20. Runtime candidate validation

### 20.1 Explicit and virtual-environment paths

Path candidates must exist as files.

### 20.2 `py`

The launcher checks availability using a command lookup equivalent to:

```bat
where py
```

The invocation uses:

```text
py -3
```

The Python application verifies the supported Python version.

### 20.3 `python`

The launcher checks availability using:

```bat
where python
```

It should resolve the first command found according to normal Windows search rules.

### 20.4 Minimum version

GF Wordbench requires the Python version declared by `pyproject.toml`.

The final application startup path owns the authoritative version check.

The launcher MAY provide an early friendly check, but such a check must not duplicate a separate version policy.

---

## 21. Runtime not found

When no runtime is available, the launcher prints an ASCII-only error identifying the accepted choices:

```text
ERROR: No supported Python runtime was found.

Expected one of:
  - GF_WORDBENCH_PYTHON
  - .venv\Scripts\python.exe
  - py on PATH
  - python on PATH
```

It exits with the launcher/bootstrap failure code defined by `EXIT_CODES.md`.

It does not:

```text
download Python
open a browser
create `.venv`
run an installer
fall back to an unrelated executable
```

---

## 22. Dependency availability

Finding Python does not prove GF Wordbench dependencies are installed.

Import or startup errors remain Python application errors.

The launcher SHOULD present a concise installation pointer when startup fails due to missing dependencies, but it MUST NOT run installation commands automatically.

Installation instructions belong to:

```text
docs/usage/INSTALLATION.md
docs/development/DEVELOPMENT_SETUP.md
```

---

# Part III — CLI launcher

## 23. CLI launcher path

```text
<REPO_ROOT>\launch_cli.bat
```

The file is version-controlled.

---

## 24. CLI invocation contract

Canonical logical invocation:

```text
<console-python> -X utf8 -m app.main_cli <forwarded-arguments>
```

For `py`:

```text
py -3 -X utf8 -m app.main_cli <forwarded-arguments>
```

### 24.1 Current directory

```text
<REPO_ROOT>
```

### 24.2 Argument forwarding

All provided batch arguments are forwarded in original order.

Conceptual batch form:

```bat
%*
```

### 24.3 No argument rewriting

The launcher MUST NOT:

```text
translate old CLI options
insert project paths
insert GF paths
insert a validation mode
remove unknown options
reorder options
expand response files
parse JSON
parse TOML
```

The Python CLI parser owns arguments.

---

## 25. CLI no-argument behavior

When no arguments are supplied, the launcher invokes:

```text
python -m app.main_cli --help
```

It does not begin an audit.

### 25.1 Result

The help command’s exit code is returned.

### 25.2 No pause

The final CLI launcher does not pause by default.

Reasons:

- automation must not block;
- terminal users already control their shell;
- help text remains accessible with `--help`;
- double-click is not the primary CLI interface.

A separate pause environment variable is not required.

---

## 26. CLI synchronous behavior

The CLI launcher waits for the Python CLI process.

After completion it:

1. captures the Python exit code immediately;
2. restores the previous directory;
3. returns the same exit code.

Conceptual sequence:

```bat
<invoke CLI>
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
```

### 26.1 Exit-code integrity

No `echo`, `popd` or cleanup command may overwrite the captured result before it is stored.

### 26.2 No launcher reinterpretation

The launcher does not translate:

```text
validation failure
argument failure
runtime failure
```

into new codes.

It preserves the application code.

---

## 27. CLI use from PowerShell

Example:

```powershell
.\launch_cli.bat --help
```

Arguments follow Windows shell quoting before reaching the batch file.

The launcher does not implement PowerShell parsing.

For complex data containing shell metacharacters, use documented quoting or a project input file.

---

## 28. CLI use from another batch script

The caller should use:

```bat
call launch_cli.bat <arguments>
```

The launcher itself returns with:

```bat
exit /b
```

It MUST NOT call:

```bat
exit
```

without `/b`, because that could terminate the caller’s command shell.

---

# Part IV — GUI launcher

## 29. GUI launcher path

```text
<REPO_ROOT>\launch_gui.bat
```

The file is version-controlled.

---

## 30. GUI modes

The GUI launcher supports exactly two startup modes:

```text
windowed
debug console
```

No application feature mode is selected by the launcher.

---

## 31. Windowed mode

Default behavior:

```text
GF_WORDBENCH_DEBUG_CONSOLE is not 1
```

The launcher prefers a windowed Python runtime.

### 31.1 Windowed runtime resolution

After resolving the console runtime:

1. if an executable path was selected, look for sibling `pythonw.exe`;
2. if `py -3` was selected, use `pyw -3` when available;
3. if `python` on `PATH` was selected, use `pythonw` when available;
4. otherwise use the console runtime as a safe fallback.

### 31.2 Canonical logical invocation

```text
<windowed-python> -X utf8 -m app.main_gui <forwarded-arguments>
```

### 31.3 Fallback visibility

When no windowed runtime exists, the launcher may print:

```text
INFO: No windowed Python runtime was found; starting GUI with console Python.
```

This is not an error.

### 31.4 Startup errors

The GUI application must install its own fatal-startup error handling and logging.

The launcher does not parse Python tracebacks.

---

## 32. Debug-console mode

Enabled by:

```text
GF_WORDBENCH_DEBUG_CONSOLE=1
```

Canonical logical invocation:

```text
<console-python> -X utf8 -m app.main_gui <forwarded-arguments>
```

The launcher:

- waits for completion;
- leaves stdout and stderr visible;
- captures the application exit code;
- restores the prior working directory;
- returns the application code.

---

## 33. Windowed process ownership

The implementation must choose and document one of these compatible behaviors:

```text
A. wait for the windowed process and return its exit code
B. dispatch the windowed process and return dispatch status
```

Final preferred behavior:

```text
windowed mode: dispatch and close the batch console
debug mode: wait and return the full application exit code
```

### 33.1 Dispatch result

A successful dispatch means only that Windows accepted the process-start request.

It does not prove the GUI initialized successfully.

### 33.2 Application startup evidence

GUI startup errors must be available through:

```text
fatal error dialog when possible
application log
debug-console mode
```

### 33.3 No silent failure claim

Documentation and UI support must not call windowed dispatch success “application success.”

---

## 34. GUI arguments

Arguments are forwarded to `app.main_gui`.

The GUI parser owns their meanings.

The launcher does not:

```text
inject a project root
inject a state path
inject debug logging
select the last run
open a report automatically
```

A future documented GUI argument remains compatible because the launcher forwards arguments without parsing them.

---

## 35. GUI no-argument behavior

No arguments means:

```text
start the GUI normally
```

Unlike the CLI launcher, the GUI launcher does not display help by default.

---

## 36. GUI single-instance policy

The launcher does not enforce a single GUI instance.

If GF Wordbench later requires single-instance behavior, the application owns it because it must understand:

```text
repository identity
project identity
state ownership
lifecycle operations
```

A batch lock file is not an adequate application-instance model.

---

# Part V — Quoting and path safety

## 37. Variable assignment

Canonical form:

```bat
set "NAME=value"
```

This prevents accidental trailing spaces and reduces quoting errors.

The final launcher SHOULD use this form for every internal variable.

---

## 38. Path use

Filesystem paths are quoted at use sites:

```bat
if exist "%PATH_VALUE%"
pushd "%REPO_ROOT%"
"%PYTHON_EXE%" -X utf8 -m app.main_cli
```

The quotes are not stored inside the variable value.

---

## 39. `start` command title rule

When the GUI launcher uses `start`, it MUST provide an explicit empty title before a quoted executable:

```bat
start "" <options> "<executable>" <arguments>
```

Without the empty title, the first quoted string may be interpreted as the window title.

---

## 40. Argument forwarding limits

Batch forwarding uses Windows command-line semantics.

The launcher cannot safely reinterpret arbitrary shell syntax.

Callers must quote values containing:

```text
spaces
ampersands
pipes
redirection characters
parentheses
carets
percent signs
exclamation marks
```

where required by the invoking shell.

### 40.1 Long data

Large text, scenario material and linguistic input should be passed through project files, scenario files or input artifacts rather than very long command lines.

---

## 41. Delayed expansion and exclamation marks

Because delayed expansion is disabled, literal `!` characters are less likely to be modified by the launcher.

The caller’s shell may still process text before the batch script receives it.

Launcher tests must include:

```text
path containing !
argument containing !
```

where supported.

---

## 42. Percent signs

A percent sign has special meaning in batch files.

Arguments entered interactively and arguments embedded in another batch script follow different escaping rules.

GF Wordbench documentation should not recommend passing complex GF source text directly through `.bat` arguments.

---

## 43. No shell-command construction

The launcher may branch between fixed approved invocations.

It MUST NOT assemble and execute one unquoted command string from user-provided text.

Approved:

```text
fixed executable
fixed Python flags
fixed module
forwarded argument vector as received by batch
```

Prohibited:

```text
set COMMAND=<user text>
call %COMMAND%
cmd /c "%UNTRUSTED%"
```

---

# Part VI — Error handling

## 44. Launcher error classes

Launcher failures are limited to:

```text
repository marker missing
entrypoint missing
explicit Python override invalid
no Python runtime found
working-directory change failed
process dispatch failed
internal batch control failure
```

Project, GF and validation errors belong to the application.

---

## 45. Error-message requirements

Launcher errors must:

- begin with `ERROR:`;
- be ASCII-only;
- identify the failed responsibility;
- print the relevant path when safe;
- avoid stack traces;
- avoid environment dumps;
- avoid secrets;
- provide one direct next action when useful.

Example:

```text
ERROR: GF Wordbench CLI entrypoint was not found:
  C:\work\GF_Wordbench\app\main_cli.py

Restore the repository files or run the launcher from a complete checkout.
```

---

## 46. Launcher-specific exit code

Launcher failures use the bootstrap/runtime code assigned by:

```text
docs/reference/EXIT_CODES.md
```

Recommended final assignment:

```text
3 = launcher or application runtime failure
```

The launcher document does not create additional exit codes.

### 46.1 CLI application codes

When Python starts, the CLI application’s code is returned unchanged.

### 46.2 GUI debug codes

Debug-console mode returns the GUI application code unchanged.

### 46.3 GUI windowed code

Windowed mode returns dispatch status according to its process-ownership policy.

---

## 47. No default pause

Canonical launchers do not call:

```bat
pause
```

by default.

### 47.1 Reasons

- CI and automation must not hang;
- nested batch callers must regain control;
- error codes must be observable;
- terminal users control their own window;
- GUI debug mode already keeps a console available.

### 47.2 Explorer troubleshooting

For troubleshooting a double-click startup, use:

```text
Command Prompt
PowerShell
GF_WORDBENCH_DEBUG_CONSOLE=1
```

A separate pause mode is unnecessary.

---

## 48. Cleanup on failure

A synchronous launcher must restore its previous working directory after a successful `pushd`.

`setlocal` automatically restores environment values at exit.

The launcher does not create temporary files.

---

# Part VII — Environment and security

## 49. Environment preservation

The launcher inherits the user environment needed for ordinary process startup, including:

```text
PATH
SystemRoot
TEMP
TMP
user profile
display and desktop context
```

It changes only its documented local variables.

---

## 50. Environment values it must not set

The launcher MUST NOT synthesize:

```text
GF_LIB_PATH
GF executable path
RGL root
project root
source root
entrypoints
output root
release mode
scenario selection
gold-update flags
```

The application resolves these through explicit configuration and user input.

---

## 51. Secrets

Launcher variables and messages must not contain:

```text
passwords
access tokens
private keys
credential files
complete environment dumps
```

The launcher never prints all environment variables.

---

## 52. Elevation

The launchers MUST NOT request administrative privileges.

GF Wordbench should run under the current user account.

A permission error is reported rather than bypassed through elevation.

---

## 53. Downloads and installation

The launchers MUST NOT access the network.

They do not:

```text
download Python
download GF
download RGL
install PySide6
install packages
update the application
```

This keeps startup predictable and auditable.

---

## 54. Executable trust

`GF_WORDBENCH_PYTHON` is an explicit local trust decision.

The launcher verifies path existence but cannot prove interpreter integrity.

Installation and environment documentation must instruct users to select a trusted Python runtime.

---

## 55. Antivirus and file locks

When Windows or security software blocks an executable, the launcher reports process-start failure.

It MUST NOT:

```text
disable antivirus
change execution policy
copy the executable elsewhere automatically
retry indefinitely
```

---

# Part VIII — Portability and repository copies

## 56. No absolute repository path

The launchers contain no hard-coded repository path.

They derive the root from:

```text
%~dp0
```

This supports:

```text
repository moves
separate clones
Git worktrees
different drive letters
different user directories
```

---

## 57. One launcher pair per repository copy

Every repository copy contains its own:

```text
launch_cli.bat
launch_gui.bat
```

The launchers always target their own copy.

A desktop shortcut must point to the intended copy’s launcher.

---

## 58. Project identity

Launchers do not infer active language identity from:

```text
repository folder name
shortcut name
batch filename
working directory
last run
application state
```

The application loads project identity from:

```text
project/project.toml
```

---

## 59. External source trees

The launchers do not touch external GF source trees.

They do not need to know where those sources are located.

---

# Part IX — Legacy migration

## 60. Legacy filenames

The predecessor already used:

```text
launch_cli.bat
launch_gui.bat
```

The filenames may remain.

Their internal product identity must change from:

```text
gf-audit
```

to:

```text
GF Wordbench
```

---

## 61. Legacy environment variables

Retired:

```text
GF_AUDIT_PYTHON
GF_AUDIT_DEBUG_CONSOLE
```

Canonical replacements:

```text
GF_WORDBENCH_PYTHON
GF_WORDBENCH_DEBUG_CONSOLE
```

### 61.1 Final writer behavior

Canonical launchers MUST NOT emit, document as primary or set `GF_AUDIT_*`.

### 61.2 Optional transition adapter

A temporary compatibility release MAY read a legacy variable only when:

- migration policy explicitly requires it;
- canonical variable is absent;
- a deprecation warning is shown;
- the legacy value is validated under the canonical rules;
- removal release is documented.

The final target launchers do not require this adapter.

---

## 62. Legacy commands

Retired:

```text
gf-audit-cli
gf-audit-gui
python -m app.main_cli under gf-audit branding
```

Canonical installed commands:

```text
gf-wordbench
gf-wordbench-gui
```

Repository modules remain:

```text
python -m app.main_cli
python -m app.main_gui
```

---

## 63. Legacy runtime resolution

The predecessor launchers included broader runtime logic such as optional automatic `uv` selection and pauses on error.

The final contract simplifies this to:

```text
explicit Python
local `.venv`
`py -3`
`python`
```

and:

```text
no default pause
no automatic environment synchronization
```

This preserves useful portability without turning the launcher into an environment manager.

---

## 64. Legacy CLI options

The launcher does not translate:

```text
--mode all
--mode file
old product option names
old project arguments
```

CLI migration belongs to the Python CLI parser or explicit migration documentation.

Canonical modes remain:

```text
quick
checkpoint
diagnostic
release
```

---

# Part X — Reference algorithms

## 65. Shared launcher algorithm

```text
START
  resolve repository root from launcher path
  validate repository markers
  validate selected Python entrypoint
  resolve console Python runtime
  set UTF-8 child environment
  enter repository root
  invoke launcher-specific path
  capture relevant result
  restore previous directory
  return result
END
```

No business operation occurs before Python starts.

---

## 66. CLI algorithm

```text
resolve shared startup
if no arguments:
    invoke app.main_cli with --help
else:
    invoke app.main_cli with all arguments
wait
capture application exit code
restore working directory
return application exit code
```

---

## 67. GUI algorithm

```text
resolve shared startup
if GF_WORDBENCH_DEBUG_CONSOLE == 1:
    select console runtime
    invoke app.main_gui
    wait
    return application exit code
else:
    derive preferred windowed runtime
    dispatch app.main_gui
    return dispatch result
```

---

## 68. Runtime resolver algorithm

```text
if GF_WORDBENCH_PYTHON is defined:
    if path exists:
        select explicit executable
    else:
        fail
else if .venv\Scripts\python.exe exists:
    select local virtual-environment executable
else if py exists on PATH:
    select py -3
else if python exists on PATH:
    select python
else:
    fail
```

The resolver returns structured internal batch variables rather than one concatenated command string.

---

# Part XI — Canonical implementation requirements

## 69. `launch_cli.bat` checklist

```text
[ ] starts with @echo off
[ ] uses setlocal
[ ] enables extensions
[ ] disables delayed expansion
[ ] resolves root from %~dp0
[ ] verifies pyproject.toml
[ ] verifies app\__init__.py
[ ] verifies app\main_cli.py
[ ] recognizes GF_WORDBENCH_PYTHON
[ ] prefers .venv\Scripts\python.exe
[ ] falls back to py -3
[ ] falls back to python
[ ] sets Python UTF-8 environment
[ ] enters repository root
[ ] invokes -m app.main_cli
[ ] shows help when no arguments
[ ] forwards all provided arguments
[ ] waits for Python
[ ] captures ERRORLEVEL immediately
[ ] restores directory
[ ] returns the application code
[ ] contains no pause
[ ] contains no GF command
[ ] contains no installation command
[ ] contains no project-specific path
```

---

## 70. `launch_gui.bat` checklist

```text
[ ] starts with @echo off
[ ] uses setlocal
[ ] enables extensions
[ ] disables delayed expansion
[ ] resolves root from %~dp0
[ ] verifies pyproject.toml
[ ] verifies app\__init__.py
[ ] verifies app\main_gui.py
[ ] recognizes GF_WORDBENCH_PYTHON
[ ] recognizes GF_WORDBENCH_DEBUG_CONSOLE=1
[ ] resolves the shared console runtime
[ ] derives pythonw/pyw when available
[ ] sets Python UTF-8 environment
[ ] enters repository root
[ ] invokes -m app.main_gui
[ ] forwards all provided arguments
[ ] distinguishes windowed dispatch from debug completion
[ ] restores directory for synchronous paths
[ ] returns meaningful status
[ ] contains no pause
[ ] contains no GF command
[ ] contains no installation command
[ ] contains no project-specific path
```

---

## 71. Batch source style

The final batch files SHOULD use:

```text
uppercase internal variable names
quoted set assignments
two-space indentation inside parentheses
ASCII comments
short labels
one responsibility per subroutine
explicit exit /b
```

Recommended internal names:

```text
REPO_ROOT
APP_ENTRY
VENV_PYTHON
PYTHON_KIND
PYTHON_EXE
WINDOWED_EXE
DEBUG_CONSOLE
RC
```

Avoid legacy names containing:

```text
AUDIT
ALBANIAN
Sqi
language-specific identifiers
```

---

## 72. Subroutines

A launcher MAY use small private batch subroutines such as:

```text
:resolve_console_python
:run_console_python
:fail
```

Subroutines must remain launcher-level.

They MUST NOT implement application services.

---

## 73. Duplication between the two launchers

Small duplication is acceptable for two independent root files.

A third shared batch library is not required.

Reasons:

- two launchers are short;
- `call`-based shared batch libraries complicate path and exit behavior;
- deployment should remain obvious;
- the shared contract and tests prevent drift.

When runtime resolution changes, both launchers and their tests are updated together.

---

# Part XII — Testing

## 74. Static contract tests

Recommended file:

```text
tests/contracts/test_windows_launchers.py
```

Tests read the launcher text and verify:

```text
both launcher files exist
both use @echo off
both use setlocal
both derive the root from %~dp0
both reference GF_WORDBENCH_PYTHON
GUI references GF_WORDBENCH_DEBUG_CONSOLE
CLI references app.main_cli
GUI references app.main_gui
both reference pyproject.toml
both reference app\__init__.py
both set PYTHONUTF8
both set PYTHONIOENCODING
both use -X utf8
both use -m
neither contains GF_AUDIT_
neither contains gf-audit
neither contains a language-specific path
neither invokes gf.exe
neither invokes pip install
neither invokes uv sync
neither invokes git reset
neither invokes git clean
neither invokes pause
neither requests elevation
```

Text checks are necessary but not sufficient.

---

## 75. CLI integration tests on Windows

Use temporary repository fixtures and fake Python executables or controlled wrapper executables.

Required cases:

```text
launch from repository root
launch from another current directory
repository path with spaces
repository path with parentheses
explicit Python override
invalid explicit override
local virtual environment selected
py fallback selected
python fallback selected
no runtime found
missing pyproject.toml
missing app\__init__.py
missing app\main_cli.py
no arguments produces help invocation
arguments preserve order
application code 0 propagated
application code 1 propagated
application code 2 propagated
application runtime code propagated
working directory restored
environment variables remain local
```

---

## 76. GUI integration tests on Windows

Required cases:

```text
normal windowed launch
debug-console launch
explicit Python override
sibling pythonw selected
pyw selected
console fallback selected
missing app\main_gui.py
windowed dispatch failure
debug application exit code propagated
arguments forwarded
repository path with spaces
Unicode repository path
working directory is repository root
```

Windowed-process tests must distinguish:

```text
dispatch success
application initialization success
```

---

## 77. Argument tests

Include:

```text
simple option
quoted path with spaces
empty quoted value where supported
ampersand escaped by caller
parentheses in path
exclamation mark
percent sign from another batch caller
Unicode argument
multiple repeated options
`--` separator
```

The launcher is not required to make invalid shell syntax valid.

---

## 78. Security tests

Verify that:

```text
GF_WORDBENCH_PYTHON with a missing path fails
GF_WORDBENCH_PYTHON is not executed as a command string
quotes stored inside override are rejected or fail safely
shell operators in override are not interpreted
repository path cannot redirect output
launcher does not create files outside expected process effects
launcher does not modify permanent environment
launcher does not invoke network tools
```

---

## 79. Packaging tests

Verify `pyproject.toml` provides:

```text
gf-wordbench
gf-wordbench-gui
```

and that both call the same Python entrypoints as the batch launchers.

The installed command and repository launcher must not diverge in application behavior.

---

## 80. Manual acceptance tests

On a supported Windows system:

1. create `.venv`;
2. install GF Wordbench dependencies;
3. double-click `launch_gui.bat`;
4. launch GUI from Command Prompt;
5. enable debug console and launch;
6. call `launch_cli.bat --help`;
7. call CLI from another directory;
8. run CLI with a path containing spaces;
9. move the repository and repeat;
10. confirm no hard-coded path remains.

---

# Part XIII — Diagnostics and support

## 81. Troubleshooting order

When startup fails:

```text
1. run launcher from Command Prompt
2. verify repository markers
3. verify GF_WORDBENCH_PYTHON when set
4. verify .venv\Scripts\python.exe
5. run selected Python with --version
6. run selected Python -m app.main_cli --help
7. run GUI with GF_WORDBENCH_DEBUG_CONSOLE=1
8. review application log
9. review installation documentation
```

The launcher does not attempt automated repair.

---

## 82. Common launcher failures

### 82.1 Entrypoint missing

Cause:

```text
incomplete repository
launcher copied alone
incorrect checkout
```

Response:

```text
restore repository files
```

### 82.2 Explicit Python missing

Cause:

```text
stale GF_WORDBENCH_PYTHON
moved interpreter
deleted virtual environment
```

Response:

```text
correct or clear the variable
```

### 82.3 No runtime found

Cause:

```text
no local .venv
no py launcher
no python on PATH
```

Response:

```text
complete installation
```

### 82.4 Import failure

Cause:

```text
dependencies missing
wrong interpreter
unsupported Python
damaged installation
```

Response:

```text
use the documented environment
```

### 82.5 GUI closes immediately

Response:

```text
enable GF_WORDBENCH_DEBUG_CONSOLE=1
launch from a terminal
review application log
```

---

## 83. Diagnostic output limits

Launcher diagnostics are short.

They do not print:

```text
complete PATH
complete environment
pip package list
project configuration
application state
source code
GF logs
```

Detailed diagnostics belong to Python or installation tooling.

---

# Part XIV — Compatibility and change control

## 84. Compatible launcher changes

Normally compatible:

```text
clearer ASCII error message
additional repository marker check
equivalent safer quoting
equivalent runtime lookup fix
new tests
internal label rename
support for a new compatible Python command form
```

The observable runtime order and entrypoint must remain compatible.

---

## 85. Breaking launcher changes

Breaking changes include:

```text
renaming a launcher file
renaming GF_WORDBENCH_PYTHON
renaming GF_WORDBENCH_DEBUG_CONSOLE
changing runtime precedence
changing the Python module entrypoint
stopping argument forwarding
changing no-argument CLI behavior
changing windowed/debug GUI semantics
changing exit-code behavior
requiring a new external launcher tool
adding automatic installation
changing repository-root discovery
```

A breaking change requires:

- documentation update;
- contract-lock review;
- installation update;
- CLI/GUI reference update;
- tests;
- migration note;
- release note.

---

## 86. Python entrypoint changes

Changing:

```text
app.main_cli
app.main_gui
```

requires coordinated updates to:

```text
launch_cli.bat
launch_gui.bat
pyproject.toml
tests
REPOSITORY_STRUCTURE.md
COMPONENT_MAP.md
CLI_REFERENCE.md
GUI_REFERENCE.md
this document
```

No launcher may independently target a renamed module before packaging and tests are updated.

---

## 87. Runtime-policy changes

Adding a runtime manager such as `uv` to automatic launcher resolution requires proof that:

- it is an accepted optional or required dependency;
- command behavior is versioned;
- offline startup behavior is defined;
- no implicit environment mutation occurs;
- tests cover its precedence;
- installation docs agree.

Convenience alone is insufficient.

---

## 88. Launcher ownership registry

| Responsibility | Owner |
|---|---|
| root discovery | launcher |
| Python selection | launcher |
| Python version acceptance | application/bootstrap |
| dependency installation | installation workflow |
| CLI parsing | `app/main_cli.py` |
| GUI parsing/startup | `app/main_gui.py` |
| project configuration | project loader/bootstrap |
| application state | `app/state.py` |
| GF execution | process and audit layers |
| reports | report writers |
| exit-code registry | `docs/reference/EXIT_CODES.md` |

This table prevents responsibility migration into `.bat` files.

---

# Part XV — Drift prevention

## 89. Drift indicators

Probable launcher drift exists when:

- one launcher still uses `gf-audit`;
- one launcher still uses `GF_AUDIT_*`;
- GUI and CLI resolve Python differently without documented reason;
- a launcher hard-codes a repository path;
- a launcher hard-codes a language project path;
- a launcher sets GF or RGL paths;
- a launcher reads application state;
- a launcher parses TOML;
- a launcher runs GF;
- a launcher builds a PGF;
- a launcher creates a run directory;
- a launcher installs dependencies;
- a launcher selects `uv` implicitly without policy;
- a launcher pauses and blocks automation;
- CLI exit code is lost after `popd`;
- GUI dispatch is reported as completed application success;
- arguments are reordered;
- no-argument CLI starts an audit;
- GUI no-argument mode shows CLI help;
- one launcher adds `PYTHONPATH` while the other does not;
- one launcher modifies the console code page;
- a copied launcher starts another repository;
- a launcher calls `exit` without `/b`;
- windowed and debug GUI modes target different Python modules;
- installed commands target different functions than launchers;
- batch messages contain code-page-dependent characters;
- a launcher uses a shell-built command from project text.

Detected drift must be corrected through coordinated launcher and documentation changes.

---

## 90. Change checklist

```text
[ ] launcher responsibility remains thin
[ ] CLI and GUI entrypoints reviewed
[ ] pyproject scripts reviewed
[ ] repository-root logic reviewed
[ ] marker checks reviewed
[ ] Python-resolution order reviewed
[ ] environment-variable names reviewed
[ ] UTF-8 behavior reviewed
[ ] working-directory behavior reviewed
[ ] argument forwarding reviewed
[ ] CLI no-argument behavior reviewed
[ ] GUI windowed behavior reviewed
[ ] GUI debug-console behavior reviewed
[ ] exit-code behavior reviewed
[ ] path quoting reviewed
[ ] shell injection reviewed
[ ] automation behavior reviewed
[ ] legacy variable migration reviewed
[ ] static tests updated
[ ] Windows integration tests updated
[ ] installation docs updated
[ ] CLI reference updated
[ ] GUI reference updated
[ ] exit-code reference updated
[ ] this document updated
```

---

## 91. Final acceptance checklist

```text
[ ] launch_cli.bat starts the repository-local CLI
[ ] launch_gui.bat starts the repository-local GUI
[ ] both work from another current directory
[ ] both support paths with spaces
[ ] both use canonical GF Wordbench naming
[ ] both reject invalid explicit Python
[ ] both prefer the local virtual environment
[ ] both use deterministic runtime fallback
[ ] both establish Python UTF-8 mode
[ ] neither modifies permanent environment
[ ] neither creates configuration
[ ] neither performs installation
[ ] neither invokes GF
[ ] neither contains language-specific values
[ ] CLI displays help without arguments
[ ] CLI propagates application exit codes
[ ] GUI supports debug-console mode
[ ] windowed dispatch is not confused with application success
[ ] no default pause exists
[ ] installed commands and module entrypoints agree
[ ] contract tests pass
[ ] Windows integration tests pass
```

---

## 92. Final enforcement rule

Windows launchers are convenience entry points, not alternate implementations.

Therefore:

> Any launcher change is valid only when it preserves repository-local startup, deterministic Python resolution, safe argument forwarding, UTF-8 behavior and clear result handling without acquiring configuration, installation, GF execution or application logic.
