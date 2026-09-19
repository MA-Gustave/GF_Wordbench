# GF Wordbench — CLI Reference

**Document ID:** `GF-WB-USAGE-CLI`  
**Status:** Normative command-line reference  
**Canonical path:** `docs/usage/CLI_REFERENCE.md`  
**Applies to:** GF Wordbench command-line interface  
**Canonical executable:** `gf-wordbench`  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**CLI contract version:** `1.2`  
**Last structural review:** 2026-08-05  

---


## ADR-0015 alignment — selected source and optional validation profile

The current startup model is path-resolved:

- the user selects a GF source file or an RGL language directory directly;
- Wordbench reads that source tree in place and does not copy it into this repository;
- `ResolvedLanguageContext` owns the selected path, resolved language identity, source root, RGL root, discovered entrypoints and effective GF-path facts;
- an explicit `ValidationProfile` is optional and may add only non-derivable policy such as additional selection filters, required or release entrypoints, checkpoints, scenarios, inputs, golds, PGF targets, required artifacts and release gates;
- a legacy `project/project.toml` may be read only when explicitly supplied as a validation profile; it is not a mandatory root file or startup authority;
- run state, logs and artifacts are written under the configured output root, normally `<output-root>/<language-key>/run_<run-id>` (with `_gf_wordbench` as the framework default), never into the selected source tree.

Unless a section is explicitly describing legacy migration input, references to an “active project” or a root `project/` directory are superseded by this model.

---
## 1. Purpose

This document defines the command-line interface of GF Wordbench.

It specifies:

- the canonical executable name;
- command and option syntax;
- validation modes;
- configuration precedence;
- path resolution;
- command behavior;
- console output;
- exit codes;
- automation behavior;
- compatibility aliases;
- security restrictions;
- error handling;
- testing requirements.

The CLI is a user-facing adapter.

It collects arguments, asks shared bootstrap code to resolve configuration, invokes the shared application layer, displays a concise result, and returns a stable process exit code.

The CLI does not own validation semantics.

### 1.1 Product boundary

One CLI invocation resolves one selected language context, zero or one explicit validation profile, and one run request.

The CLI does not provide:

- a project registry;
- a language-profile selector;
- a multi-workspace batch run;
- portfolio aggregation or portfolio readiness commands;
- any dependency on `gf-portfolio` runtime, storage or configuration.

`gf-portfolio` may invoke separate `gf-wordbench` processes and consume finalized public Wordbench artifacts. It does not alter Wordbench command semantics, resolved language identity or run results.

---

## 2. Core rule

> Every validation command must use the same shared configuration and orchestration flow as the GUI and supported automation.

The CLI must not independently implement:

- source selection;
- static scanning;
- GF compilation;
- scenario execution;
- PGF construction;
- direct/downstream classification;
- regression comparison;
- report generation;
- manifest generation;
- gold comparison.

The canonical validation flow is:

```text
parse CLI arguments
    -> resolve the selected language, optional profile and environment configuration
    -> validate the resolved request
    -> build RunConfig
    -> invoke the shared run application service
    -> print a concise structured summary
    -> return a documented exit code
```

---

## 3. Canonical executable

Installed command:

```text
gf-wordbench
```

Package metadata exposes this console script. The internal Python module path is not part of the public CLI contract.

The predecessor executable name:

```text
gf-audit
```

is accepted only as a compatibility alias. Canonical documentation, help, reports and examples use:

```text
gf-wordbench
```

---

## 4. Windows launchers

Canonical Windows launcher:

```text
launch_cli.bat
```

The launcher may:

- locate the project virtual environment;
- activate or use its Python interpreter;
- invoke `gf-wordbench`;
- forward every user argument;
- preserve the CLI exit code.

The launcher must not:

- build a separate configuration;
- change validation mode silently;
- rewrite paths;
- insert hidden GF options;
- reinterpret exit codes;
- become the only supported invocation path.

Example:

```bat
@echo off
setlocal
call "%~dp0.venv\Scripts\gf-wordbench.exe" %*
exit /b %ERRORLEVEL%
```

The launcher invokes the installed console script and preserves its exit code.

---

# 5. Command overview

Canonical command tree:

```text
gf-wordbench
├── validate
├── project
│   └── check
├── scenarios
│   └── check
├── gold
│   └── update
├── schemas
│   └── check
└── reports
    └── check
```

Global informational options:

```text
--help
--version
```

An additional top-level command requires a distinct stable responsibility not already covered by the existing commands.

---

# 6. General syntax

```text
gf-wordbench [GLOBAL-OPTION] <command> [COMMAND-OPTION]
```

Examples:

```text
gf-wordbench --version
gf-wordbench validate --mode quick --target lib/src/french/NounFre.gf
gf-wordbench validate --mode release --strict
gf-wordbench project check
gf-wordbench scenarios check --strict
gf-wordbench gold update linearize-basic
gf-wordbench schemas check <validation-profile-root>/project.toml
gf-wordbench reports check _gf_wordbench/run_20260722_181542
```

---

# 7. Help and version

## 7.1 Global help

```text
gf-wordbench --help
```

Expected behavior:

- print command overview;
- print global options;
- list subcommands;
- return exit code `0`;
- perform no project loading;
- launch no external process;
- create no run directory.

## 7.2 Command help

```text
gf-wordbench validate --help
gf-wordbench project check --help
gf-wordbench scenarios check --help
gf-wordbench gold update --help
gf-wordbench schemas check --help
gf-wordbench reports check --help
```

Expected behavior:

- print command-specific usage;
- return `0`;
- perform no write;
- launch no GF process.

## 7.3 Version

```text
gf-wordbench --version
```

Canonical output:

```text
GF Wordbench <version>
```

Example:

```text
GF Wordbench 1.0.0
```

The version must come from the package metadata source.

The CLI must not duplicate a hard-coded version.

---

# 8. Global behavior

## 8.1 Standard output

Use stdout for:

- help;
- version;
- normal progress when enabled;
- run summary;
- successful checker results;
- artifact paths.

## 8.2 Standard error

Use stderr for:

- invalid invocation details;
- configuration errors;
- framework/runtime errors;
- security-policy rejection;
- checker failures;
- warnings when not included in normal output.

## 8.3 Encoding

Console text should be emitted as Unicode.

Persisted artifacts remain UTF-8 regardless of terminal encoding.

## 8.4 Color

Color is optional.

Canonical text must remain understandable without color.

Color is disabled when output is not an interactive terminal.

Automation must not depend on color or terminal escape sequences.

## 8.5 Interactive prompts

Normal validation commands are non-interactive.

The only command allowed to request destructive confirmation is:

```text
gold update
```

Automation can use explicit confirmation flags documented below.

---

# 9. Common path resolution

The following options are common to commands that load the active project or execute GF:

```text
--project-root PATH
--gf-exe PATH
--rgl-root PATH
--out-root PATH
```

## 9.1 `--project-root`

Purpose:

```text
Compatibility option naming the framework/repository root; it does not identify the selected language.
```

Canonical default:

```text
current GF Wordbench repository root
```

When supplied explicitly, the optional validation profile may be:

```text
<validation-profile-root>/project.toml
```

Example:

```text
gf-wordbench validate --project-root C:\mycode\GF_Wordbench
```

## 9.2 `--gf-exe`

Purpose:

```text
Explicit path to gf or gf.exe.
```

Resolution precedence:

```text
1. explicit --gf-exe
2. documented GF_WORDBENCH_GF_EXE environment value
3. validated application environment configuration
4. executable discovery through PATH
```

Strict mode requires an explicitly resolved concrete executable path.

The resolved path must be recorded in run evidence.

## 9.3 `--rgl-root`

Purpose:

```text
Root of the RGL installation or source tree containing the selected language.
```

Resolution precedence:

```text
1. explicit --rgl-root
2. documented GF_WORDBENCH_RGL_ROOT environment value
3. validated application environment configuration
4. supported GF/toolchain discovery
```

The project configuration owns project-relative GF path parts.

The CLI does not own language-specific path lists.

## 9.4 `--out-root`

Purpose:

```text
Directory under which run_<run-id> directories are created.
```

Resolution precedence:

```text
1. explicit --out-root
2. documented GF_WORDBENCH_OUT_ROOT environment value
3. application environment configuration
4. framework-safe default
```

Canonical default:

```text
<project-root>/_gf_wordbench
```

## 9.5 Path normalization

CLI paths are:

- expanded according to platform policy;
- made absolute during configuration resolution;
- normalized before containment checks;
- recorded in resolved evidence.

The CLI must not manually add quote characters around a path value.

The shell handles user-entered quoting.

---

# 10. Environment variables

The CLI recognizes only documented environment variables.

Canonical environment variables:

```text
GF_WORDBENCH_GF_EXE
GF_WORDBENCH_RGL_ROOT
GF_WORDBENCH_OUT_ROOT
```

Optional conventional variable:

```text
NO_COLOR
```

Environment variables must not define active-language facts such as:

```text
source directory
entrypoints
checkpoints
required scenarios
release artifacts
language code
```

Those belong to:

```text
<validation-profile-root>/project.toml
```

Resolved environment-derived values must be recorded.

Secrets must not be stored in these variables or copied into reports.

---

# 11. Configuration precedence

For one CLI request, precedence from lowest to highest is:

```text
1. framework-safe defaults
2. <validation-profile-root>/project.toml
3. documented environment-specific values
4. explicit command-line options
```

Compatibility aliases are normalized before `RunConfig` is built.

Rules:

- active-language rules come from `project.toml`;
- environment values provide local tool paths, not project semantics;
- explicit CLI values override only documented overridable settings;
- required release constraints cannot be disabled silently;
- the CLI must print or persist the resolved canonical values, not aliases;
- application GUI state is not authoritative CLI configuration.

---

# 12. Validation-profile settings

The canonical CLI does not expose these predecessor project-owned options:

```text
--scan-dir
--scan-glob
--include-regex
--exclude-regex
--gf-path
```

These settings belong to:

```text
<validation-profile-root>/project.toml
```

Reasons:

- they define the active language project;
- repeating them on every invocation creates drift;
- GUI, CLI, and automation must share one project definition;
- release validation must not be changed by accidental local flags.

The compatibility adapter may accept these options only for predecessor invocations.

When accepted, they:

- print one compatibility warning;
- are recorded as explicit overrides;
- are rejected in strict release mode;
- never become canonical report fields.

---

# 13. `validate`

## 13.1 Purpose

Run GF Wordbench validation and create a complete run directory.

Canonical syntax:

```text
gf-wordbench validate [OPTIONS]
```

## 13.2 Required result

The command returns one structured `RunResult`.

It creates a run directory unless validation fails before run initialization.

## 13.3 Canonical options

```text
--mode quick|checkpoint|release|diagnostic
--target PATH
--checkpoint ID
--scenario ID
--strict
--no-version-probe
--no-compile
--compile-timeout SECONDS
--scenario-timeout SECONDS
--pgf-timeout SECONDS
--max-files COUNT
--cpu-stats
--keep-ok-details
--compare-previous
--no-compare-previous
--baseline PATH
--quiet
--verbose
--project-root PATH
--gf-exe PATH
--rgl-root PATH
--out-root PATH
```

Not every option is valid in every mode.

---

# 14. Validation modes

Canonical values:

```text
quick
checkpoint
release
diagnostic
```

Legacy aliases:

```text
file -> quick
all  -> diagnostic
```

Canonical output always uses the normalized value.

---

# 15. `validate --mode quick`

## 15.1 Purpose

Provide fast feedback for one explicit source target.

Syntax:

```text
gf-wordbench validate --mode quick --target PATH
```

Example:

```text
gf-wordbench validate ^
  --mode quick ^
  --target project\src\NounFre.gf
```

PowerShell:

```powershell
gf-wordbench validate `
  --mode quick `
  --target project/src/NounFre.gf
```

## 15.2 Requirements

`--target` is always required in quick mode.

Canonical policy:

```text
explicit --target required
```

The CLI must reject `--mode quick` before execution when no target is supplied.

## 15.3 Target identity

The target:

- must exist;
- must be a file;
- must remain inside the resolved source root;
- must satisfy project source policy;
- is persisted as a project-relative identity.

## 15.4 Stages

Quick mode normally runs:

```text
configuration
GF preflight
target selection
static scan
fingerprint
file compilation
classification
optional quick scenario
regression comparison when compatible
reports
manifest
```

Quick mode does not perform a release PGF build.

## 15.5 Invalid options

Normally invalid:

```text
--checkpoint
--max-files
```

A selected `--scenario` must be allowed by quick-mode project policy.

---

# 16. `validate --mode checkpoint`

## 16.1 Purpose

Validate one configured project checkpoint.

Syntax:

```text
gf-wordbench validate --mode checkpoint --checkpoint ID
```

Example:

```text
gf-wordbench validate --mode checkpoint --checkpoint morphology
```

## 16.2 Checkpoint selection

`--checkpoint` is required when the project declares more than one checkpoint and has no default.

The ID must exist in `project.toml`.

## 16.3 Stages

Checkpoint mode normally runs:

```text
configured checkpoint file selection
scan
fingerprint
compilation
classification
required checkpoint scenarios
gold comparison where declared
regression comparison
reports
manifest
```

## 16.4 Invalid options

Normally invalid:

```text
--target
--max-files
```

except where a documented checkpoint-debugging policy explicitly permits them.

---

# 17. `validate --mode release`

## 17.1 Purpose

Evaluate the active project’s release contract.

Syntax:

```text
gf-wordbench validate --mode release
```

Canonical:

```text
gf-wordbench validate --mode release --strict
```

## 17.2 Stages

Release mode runs all required stages:

```text
strict project validation
GF version compatibility
complete required source selection
static scans
source fingerprints
file compilation
direct/downstream classification
required release scenarios
required gold comparison
PGF construction
required artifact checks
release gates
regression comparison
reports
manifest validation
```

## 17.3 Prohibited bypasses

Release mode rejects:

```text
--no-compile
--max-files
```

It also rejects omission of required scenarios or required PGF gates.

## 17.4 Optional scenario selection

`--scenario` may add optional release diagnostics.

It cannot remove required scenarios.

## 17.5 Success

Exit `0` requires:

- overall status `OK`;
- every required release gate `OK`;
- required reports written;
- manifest valid.

---

# 18. `validate --mode diagnostic`

## 18.1 Purpose

Collect broad evidence for diagnosis.

Syntax:

```text
gf-wordbench validate --mode diagnostic
```

## 18.2 Stages

Diagnostic mode normally runs:

```text
broad source selection
static scan
fingerprinting
compilation
classification
required diagnostic scenarios
selected optional scenarios
optional PGF diagnostic build
regression comparison
full reports
manifest
```

## 18.3 `--max-files`

Diagnostic mode may use:

```text
--max-files COUNT
```

Rules:

- `0` means no limit;
- negative values are invalid;
- limiting files must be recorded;
- a limited diagnostic run is not release evidence;
- selection remains deterministic.

## 18.4 `--no-compile`

Diagnostic mode may use:

```text
--no-compile
```

This creates a scan/fingerprint diagnostic run.

Compilation results are:

```text
SKIPPED
```

They are not represented as successful.

## 18.5 Scenario selection

`--scenario ID` may be repeated:

```text
gf-wordbench validate --mode diagnostic ^
  --scenario parse-negation ^
  --scenario generation-smoke
```

Selected IDs must be registered.

---

# 19. `--target`

Syntax:

```text
--target PATH
```

Canonical use:

```text
quick mode
```

The canonical option name is:

```text
--target
```

Legacy alias:

```text
--target-file
```

Rules:

- accepted path must exist;
- directory values are invalid;
- path must be inside the resolved source root;
- path is normalized to project-relative identity;
- a target does not override the resolved language identity;
- release mode rejects target narrowing.

---

# 20. `--checkpoint`

Syntax:

```text
--checkpoint ID
```

Canonical use:

```text
checkpoint mode
```

Rules:

- ID must match a configured checkpoint;
- comparison baselines must use compatible checkpoint scope;
- declaration order remains project-owned;
- CLI input does not alter `project.toml`.

---

# 21. `--scenario`

Syntax:

```text
--scenario ID
```

Repeatable:

```text
--scenario load --scenario linearize-basic
```

Purpose:

- add registered optional scenarios;
- select diagnostic scenario subsets where policy permits.

Rules:

- ID must be registered;
- required scenarios cannot be removed;
- scenario order follows project configuration, not CLI argument order;
- unregistered `.gfs` paths are not executed directly;
- the CLI accepts IDs, not arbitrary shell-script paths.

This prevents accidental execution of unreviewed scripts.

---

# 22. `--strict`

Syntax:

```text
--strict
```

Strict mode applies stronger enforcement:

- explicit concrete GF executable resolution;
- supported GF version policy;
- no inherited hidden GF path;
- strict path containment;
- scenario system-command prohibition;
- required markers;
- required gold existence;
- output-size limits;
- symlink/junction escape rejection;
- manifest verification;
- stricter schema validation;
- no silent compatibility fallback.

Strict mode does not sandbox untrusted `.gfs` content.

---

# 23. Version probing

Canonical option:

```text
--no-version-probe
```

Default:

```text
version probe enabled
```

Legacy alias:

```text
--skip-version-probe
```

Rules:

- release strict mode may reject `--no-version-probe`;
- a skipped probe is recorded explicitly;
- the CLI must not represent skipped probing as a known supported GF version;
- version-probe timeout is separate from validation timeouts.

---

# 24. Compilation control

## 24.1 `--no-compile`

Purpose:

```text
scan and fingerprint without file compilation
```

Allowed:

```text
quick
checkpoint only when project policy permits
diagnostic
```

Prohibited:

```text
release
```

Result semantics:

```text
file status = SKIPPED for compilation
```

The overall command may still complete successfully as a diagnostic operation, but it must not claim grammar compilation success.

## 24.2 `--cpu-stats`

Purpose:

```text
request supported GF CPU/performance statistics
```

Legacy alias:

```text
--emit-cpu-stats
```

Rules:

- disabled by default;
- used only when supported by selected GF version;
- exact GF command is recorded;
- output remains diagnostic evidence;
- CPU statistics do not alter validation status by themselves.

---

# 25. Timeouts

Canonical options:

```text
--compile-timeout SECONDS
--scenario-timeout SECONDS
--pgf-timeout SECONDS
```

All values must be positive integers.

## 25.1 Compile timeout

Applies to each file compile request.

## 25.2 Scenario timeout

Applies to each `.gfs` scenario execution.

## 25.3 PGF timeout

Applies to the release PGF build.

## 25.4 Legacy timeout

Legacy:

```text
--timeout-sec
```

Migration behavior:

- maps to compile timeout;
- may supply scenario and PGF fallback values only during compatibility migration;
- prints one compatibility warning;
- canonical reports record resolved operation-specific timeouts.

## 25.5 Timeout behavior

A timeout:

- terminates the owned process tree when possible;
- preserves partial stdout and stderr;
- produces structured `ERROR`;
- returns exit code `3` when it prevents reliable required execution;
- is not hidden as a generic compile failure.

---

# 26. Previous-run comparison

## 26.1 Enable or disable

```text
--compare-previous
--no-compare-previous
```

Default is mode/project policy.

Canonical defaults:

```text
quick: enabled when compatible target baseline exists
checkpoint: enabled
release: enabled
diagnostic: enabled
```

## 26.2 Explicit baseline

```text
--baseline PATH
```

Accepted path:

```text
run directory
summary.json
```

Rules:

- explicit baseline implies comparison enabled;
- baseline is read-only;
- schema and comparability checks still apply;
- incompatible explicit baseline produces a configuration/comparison error;
- automatic discovery is bypassed;
- no current run is ever used as its own baseline.

## 26.3 Missing baseline

No compatible automatic baseline:

- does not fail validation;
- produces no regression entries;
- is reported clearly.

---

# 27. Detail retention

```text
--keep-ok-details
```

Purpose:

```text
retain optional per-file detail reports for successful files
```

Default:

```text
false
```

Rules:

- raw evidence required by contracts is not deleted merely because this option is false;
- this flag controls optional human detail artifacts;
- release manifests record produced files;
- it does not alter validation status.

---

# 28. Console verbosity

## 28.1 Default

Print:

- application name/version when useful;
- run ID;
- mode;
- overall status;
- important file/scenario counts;
- direct failure count;
- regression count;
- run directory;
- `summary.md`;
- `summary.json`;
- `AI_READY.md`;
- manifest path when available.

## 28.2 `--quiet`

Suppress normal progress and the human run summary.

Errors and warnings remain on stderr.

Exit codes and persisted artifacts remain authoritative.

Canonical successful quiet output:

```text
none
```

## 28.3 `--verbose`

Print stage transitions and resolved non-secret configuration.

Examples:

```text
project loaded
GF executable resolved
24 files selected
compiling 4/24
running scenario 2/6
writing reports
manifest verified
```

Verbose output is human diagnostic output.

Automation must not parse it.

## 28.4 Conflict

Using both:

```text
--quiet --verbose
```

is invalid.

---

# 29. Validation output

Canonical default console output:

```text
GF Wordbench 1.0.0
Run: 20260722_181542
Mode: release
Status: FAIL

Files: 39 OK, 3 FAIL, 0 ERROR, 0 SKIPPED
Failures: 1 direct, 2 downstream, 0 ambiguous
Scenarios: 5 OK, 1 FAIL, 0 ERROR, 0 SKIPPED
Regression: 2 regressed, 0 new, 1 improved, 0 removed

Run directory: C:\work\GF_Wordbench\_gf_wordbench\run_20260722_181542
Summary: C:\work\GF_Wordbench\_gf_wordbench\run_20260722_181542\summary.md
JSON: C:\work\GF_Wordbench\_gf_wordbench\run_20260722_181542\summary.json
AI packet: C:\work\GF_Wordbench\_gf_wordbench\run_20260722_181542\AI_READY.md
Manifest: C:\work\GF_Wordbench\_gf_wordbench\run_20260722_181542\manifest.json
```

Human-facing wording may change compatibly.

The structured meanings and exit code must remain stable.

---

# 30. `project check`

## 30.1 Purpose

Validate the selected-language and optional-profile contract without running full validation.

Syntax:

```text
gf-wordbench project check [OPTIONS]
```

## 30.2 Canonical options

```text
--strict
--probe-gf
--project-root PATH
--gf-exe PATH
--rgl-root PATH
--quiet
--verbose
```

## 30.3 Checks

```text
<validation-profile-root>/project.toml exists
UTF-8/TOML parsing succeeds
schema ID supported
schema version supported
project ID valid
language code valid
source root exists
source glob valid
entrypoints unique and ordered
checkpoints valid
scenario IDs unique
required scenario files exist
required gold policy is coherent
release entrypoints exist
expected artifact declarations are valid
project-relative paths remain contained
toolchain path parts are valid
```

## 30.4 `--probe-gf`

Additionally:

- resolves GF executable;
- runs `gf --version`;
- checks compatibility;
- validates RGL path.

It does not compile project files.

## 30.5 Writes

The command creates no normal run directory.

It may create only controlled temporary evidence when GF probing requires it, then remove it according to policy.

It must not rewrite `project.toml`.

## 30.6 Exit behavior

```text
0 = project contract valid
2 = invalid project/configuration
3 = GF probe/runtime failure
```

---

# 31. `scenarios check`

## 31.1 Purpose

Validate registered `.gfs` scenario contracts without executing them.

Syntax:

```text
gf-wordbench scenarios check [OPTIONS]
```

## 31.2 Canonical options

```text
--strict
--scenario ID
--project-root PATH
--quiet
--verbose
```

`--scenario` may be repeated.

Without `--scenario`, check every registered scenario.

## 31.3 Checks

```text
scenario IDs unique
registered scripts exist
scripts are UTF-8
paths remain inside project validation roots
required gold files exist
gold paths match policy
required markers are declared
outer scenario marker exists
explicit q termination exists where required
system commands are prohibited
unauthorized eh is prohibited
unauthorized rf is prohibited
unauthorized wf is prohibited
interactive commands are prohibited
generation commands are bounded
nested assets are declared
normalization version is declared
scenario ordering is deterministic
```

## 31.4 No execution

The command:

- does not launch GF;
- does not compare actual output;
- does not update gold;
- creates no normal run directory.

## 31.5 Exit behavior

```text
0 = selected scenario contracts valid
2 = invalid registration or scenario contract
3 = checker/runtime failure
```

---

# 32. `gold update`

## 32.1 Purpose

Explicitly regenerate reviewed expected output for selected scenarios.

Syntax:

```text
gf-wordbench gold update <SCENARIO-ID>... [OPTIONS]
```

Example:

```text
gf-wordbench gold update linearize-basic parse-basic
```

## 32.2 Canonical options

```text
--all
--yes
--strict
--show-diff
--project-root PATH
--gf-exe PATH
--rgl-root PATH
--out-root PATH
--scenario-timeout SECONDS
--quiet
--verbose
```

## 32.3 Selection

One or more scenario IDs are required unless:

```text
--all
```

is provided.

`--all` means all registered gold-backed scenarios.

It must not include scenarios whose policy forbids exact gold.

## 32.4 Confirmation

Interactive use asks for confirmation after generating and comparing candidate output.

Example:

```text
Update 2 gold files? [y/N]
```

Automation must provide:

```text
--yes
```

`--yes` confirms writing.

It does not bypass scenario validation, path safety, or strict mode.

## 32.5 Workflow

```text
validate selected registrations
run each scenario
preserve raw stdout/stderr
verify markers
normalize output
compare with current gold
show or save diff
request confirmation
write gold atomically
validate written gold
record update evidence
```

## 32.6 Failure protection

Gold is not updated when:

- GF launch fails;
- scenario times out;
- required markers fail;
- normalization fails;
- output is truncated;
- path containment fails;
- no meaningful output exists;
- user declines confirmation;
- atomic replacement fails.

## 32.7 Writes

The command may modify only selected:

```text
<validation-profile-root>/validation/gold/<scenario-id>.gold
```

It must not modify:

- `.gfs` scripts;
- GF sources;
- `project.toml`;
- unrelated gold files.

## 32.8 Exit behavior

```text
0 = selected gold updates completed or no changes required
1 = scenario executed but candidate output failed validation
2 = invalid invocation/configuration
3 = runtime/write/integrity error
```

User-declined confirmation returns:

```text
0
```

and performs no changes.

---

# 33. `schemas check`

## 33.1 Purpose

Validate one or more persisted GF Wordbench assets.

Syntax:

```text
gf-wordbench schemas check <PATH>... [OPTIONS]
```

Examples:

```text
gf-wordbench schemas check <validation-profile-root>/project.toml
gf-wordbench schemas check .gf_wordbench_state.json
gf-wordbench schemas check _gf_wordbench/run_20260722_181542/summary.json
gf-wordbench schemas check _gf_wordbench/run_20260722_181542
```

## 33.2 Canonical options

```text
--strict
--recursive
--project-root PATH
--quiet
--verbose
```

## 33.3 Auto-detection

Supported assets:

```text
project.toml
.gf_wordbench_state.json
summary.json
manifest.json
scenario .out
scenario .gold
run directory
```

## 33.4 Checks

```text
schema identity
schema version
required fields
canonical enum values
path form
deterministic identity constraints
count consistency
artifact references
legacy compatibility
migration availability
UTF-8
JSON/TOML syntax
gold/output canonical text rules
```

## 33.5 Legacy files

Supported legacy assets may produce:

```text
valid legacy, canonical migration available
```

They are not rewritten.

## 33.6 No implicit migration

`schemas check` is read-only.

Schema migration is a separate explicit project-lifecycle operation.

## 33.7 Exit behavior

```text
0 = every selected asset valid or supported legacy
2 = schema-invalid asset
3 = checker/runtime error
```

Strict mode may treat supported legacy form as exit `2`.

---

# 34. `reports check`

## 34.1 Purpose

Verify consistency and integrity of a completed or partial run directory.

Syntax:

```text
gf-wordbench reports check <RUN-DIR> [OPTIONS]
```

## 34.2 Canonical options

```text
--strict
--verify-hashes
--quiet
--verbose
```

Strict mode implies:

```text
--verify-hashes
```

when a manifest is present or required.

## 34.3 Checks

```text
run directory exists
summary.json parses
summary schema supported
summary.md exists when required
summary Markdown heading contract valid
required sections present
AI_READY.md exists when required
top_errors.txt format valid
manifest schema valid
manifest artifact paths contained
artifact sizes match
artifact SHA-256 hashes match
run ID agrees across artifacts
status and counts agree
file result counts agree
scenario result counts agree
regression entries valid
required raw evidence paths exist
required PGF artifact exists in release runs
```

## 34.4 Read-only behavior

The checker must not repair or rewrite a run.

## 34.5 Exit behavior

```text
0 = report/run integrity valid
2 = contract or schema invalid
3 = checker/runtime error
```

---

# 35. Commands intentionally omitted

The public CLI does not expose separate commands for:

```text
scan
compile
classify
diff
pgf
report
manifest
```

as public top-level operations.

Reasons:

- they are stages, not independent user workflows;
- exposing every internal stage encourages bypasses;
- validation modes already compose them safely;
- debugging can use documented diagnostic options;
- reports and manifests must remain tied to coherent runs.

Dedicated developer-only commands may exist under an explicitly unstable namespace, but they are not part of the public CLI contract.

---

# 36. Exit codes

Canonical process exit codes:

| Code | Name | Meaning |
|---:|---|---|
| `0` | `EXIT_OK` | Command completed successfully and all required criteria passed |
| `1` | `EXIT_VALIDATION_FAILED` | Command completed reliably, but at least one required validation criterion failed |
| `2` | `EXIT_USAGE_ERROR` | Invalid invocation, configuration, path, schema, or requested contract prevented a valid command result |
| `3` | `EXIT_RUNTIME_ERROR` | Framework, external-tool launch, timeout, I/O, integrity, persistence, or cancellation-handling failure |
| `4` | `EXIT_CANCELLED` | Controlled cancellation completed with process containment and best-effort evidence preservation |

## 36.1 Exit `0`

Examples:

- release validation passes;
- quick validation passes;
- project check passes;
- schema check passes;
- no compatible regression baseline exists but current validation passes;
- gold update is confirmed and succeeds;
- gold update finds no change.

## 36.2 Exit `1`

Examples:

- file compilation produces a required GF failure;
- required scenario assertion fails;
- required gold comparison mismatches;
- release PGF gate fails after GF executes reliably;
- explicit no-regression policy detects a qualifying regression;
- gold candidate scenario completes but fails required validation.

## 36.3 Exit `2`

Examples:

- unknown option;
- missing required target;
- incompatible mode/option combination;
- invalid project configuration detected before execution;
- unregistered scenario ID;
- unsafe path rejected before execution;
- unsupported persisted schema supplied as an input;
- prohibited scenario command detected before execution.

Exit `2` means that no valid command result was constructed.

## 36.4 Exit `3`

Examples:

- GF executable cannot launch;
- required process times out;
- output root cannot be written;
- report writer required by mode fails;
- manifest integrity cannot be established;
- controlled cancellation cannot safely contain child processes or preserve evidence;
- unexpected framework exception.

## 36.5 Exit `4`

Examples:

- the user requests cancellation;
- application shutdown requests cancellation;
- a controller policy requests cancellation;
- `Ctrl+C` is converted to controlled cancellation.

Exit `4` applies only when cancellation is the command-level outcome and containment plus best-effort evidence preservation complete successfully.

A timeout is not cancellation and returns `3`.

## 36.6 Help and version

```text
--help    -> 0
--version -> 0
```

## 36.7 Keyboard interruption

`Ctrl+C` should request controlled cancellation where possible.

Canonical result:

```text
controlled cancellation completed safely -> 4
cancellation handling failed critically   -> 3
```

The public GF Wordbench CLI does not use platform signal code `130` as its canonical application result.

---

# 37. Overall-status mapping

Validation command mapping:

```text
RunResult.overall_status = OK
    -> exit 0

RunResult.overall_status = FAIL
    -> exit 1

RunResult.overall_status = ERROR
    -> exit 3

controlled cancellation
    -> exit 4
```

Argument or configuration errors detected before a valid command result exists:

```text
exit 2
```

Canonical precedence after execution begins:

```text
runtime error
    > controlled cancellation
    > validation failure
    > success
```

Canonical overall status drives the exit code so that:

- runtime errors do not return success;
- controlled cancellation remains distinct from runtime failure;
- scenario failures affect the exit code;
- release-gate failures affect the exit code;
- skipped compilation is not mistaken for success;
- manifest failures are represented correctly.

---

# 38. Argument validation

The CLI validates obvious invocation rules before calling bootstrap.

Examples:

```text
timeout > 0
max-files >= 0
quick requires target
target is invalid outside quick
checkpoint ID valid for checkpoint mode
release rejects no-compile
release rejects max-files
quiet and verbose conflict
baseline implies comparison
scenario IDs have valid syntax
```

Bootstrap remains authoritative for:

- filesystem containment;
- project schema;
- tool resolution;
- RGL resolution;
- entrypoint and checkpoint existence;
- release requirements;
- scenario registration;
- output-root safety.

The CLI must not duplicate bootstrap rules inconsistently.

---

# 39. Error messages

## 39.1 Format

Errors begin with:

```text
ERROR:
```

Warnings begin with:

```text
WARNING:
```

Examples:

```text
ERROR: --target is required when --mode quick.
ERROR: release mode does not permit --no-compile.
ERROR: project configuration is invalid: duplicate scenario ID 'load'.
ERROR: GF executable could not be launched: C:\tools\gf.exe
WARNING: legacy mode 'all' was mapped to 'diagnostic'.
```

## 39.2 Content

A useful error identifies:

- invalid option or subject;
- expected condition;
- resolved path when relevant;
- next document or command when useful.

## 39.3 Tracebacks

Normal CLI use does not print a traceback by default.

Tracebacks are not a public console-output contract.

When retained for diagnosis, they are bounded and written through the framework logging and evidence policy.

---

# 40. Progress behavior

## 40.1 Non-interactive safety

Progress output must not require a TTY.

## 40.2 Redirected output

When stdout is redirected:

- avoid cursor-control sequences;
- emit line-based messages;
- disable color unless forced.

## 40.3 Stable automation

Progress text is not an API.

Automation uses:

- exit code;
- `summary.json`;
- `manifest.json`;
- documented artifact paths.

## 40.4 Run-path discovery

Automation sets a known `--out-root` and discovers the completed run through the documented run layout and persisted run identity.

It must not parse decorative console prose when a structured mechanism exists.

---

# 41. Automation examples

## 41.1 PowerShell release validation

```powershell
gf-wordbench validate `
  --mode release `
  --strict `
  --project-root C:\work\GF_Wordbench `
  --gf-exe C:\tools\gf\bin\gf.exe `
  --rgl-root C:\tools\gf-rgl `
  --out-root C:\work\GF_Wordbench\_gf_wordbench

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
```

## 41.2 Windows batch checkpoint

```bat
@echo off
gf-wordbench validate ^
  --mode checkpoint ^
  --checkpoint syntax ^
  --project-root C:\work\GF_Wordbench

exit /b %ERRORLEVEL%
```

## 41.3 POSIX shell diagnostic run

```sh
gf-wordbench validate \
  --mode diagnostic \
  --scenario parse-basic \
  --scenario generation-smoke \
  --out-root ./_gf_wordbench

status=$?
exit "$status"
```

## 41.4 Validate generated reports

```powershell
gf-wordbench reports check `
  C:\work\GF_Wordbench\_gf_wordbench\run_20260722_181542 `
  --strict
```

## 41.5 Explicit gold update

```powershell
gf-wordbench gold update linearize-basic `
  --show-diff `
  --yes
```

---

# 42. CI guidance

CI:

- use explicit project root;
- use an explicit or trusted resolved GF executable;
- use a known RGL root;
- use strict release mode for release gates;
- persist the complete run directory as an artifact;
- use exit codes;
- inspect `summary.json`;
- verify `manifest.json`;
- avoid parsing `summary.md`;
- avoid mutable global GF paths;
- avoid automatic gold update;
- avoid unbounded diagnostic generation.

Canonical release command:

```text
gf-wordbench validate --mode release --strict --quiet
```

`--quiet` is optional.

CI retains stderr and the complete run directory.

---

# 43. Security requirements

## 43.1 No shell command construction

The CLI passes plain values to bootstrap and orchestration.

It must not build one shell command string from user or project text.

## 43.2 Secrets

Do not pass secrets through CLI arguments.

Arguments may be visible in:

- process listings;
- shell history;
- logs;
- CI metadata.

GF Wordbench has no secret CLI options.

## 43.3 Scenario trust

`.gfs` scenarios are executable GF input.

The CLI must not offer an unrestricted:

```text
--script arbitrary.gfs
```

Canonical execution uses registered scenario IDs.

## 43.4 Gold safety

Gold updates require an explicit command and confirmation.

Normal `validate` never writes gold.

## 43.5 Path traversal

All project, scenario, report, and output paths undergo containment checks.

## 43.6 Privilege

Do not run GF Wordbench as Administrator/root unless required by the environment.

## 43.7 Untrusted projects

Strict mode reduces risk but is not a sandbox.

Use OS-level isolation for untrusted projects.

---

# 44. Compatibility with the inherited CLI

The inherited command currently uses:

```text
prog = gf-audit
modes = all | file
```

and exposes:

```text
--project-root
--rgl-root
--gf-exe
--out-root
--scan-dir
--scan-glob
--gf-path
--timeout-sec
--max-files
--mode
--target-file
--include-regex
--exclude-regex
--skip-version-probe
--no-compile
--emit-cpu-stats
--keep-ok-details
--diff-previous
```

It returns:

```text
0 = no file failures
1 = file failures
2 = invalid arguments
3 = runtime exception
```

The canonical CLI preserves predecessor meanings for codes `0` through `3` and adds code `4` for controlled cancellation.

---

# 45. Legacy alias table

| Legacy | Canonical | Policy |
|---|---|---|
| `gf-audit` | `gf-wordbench` | Compatibility input alias; canonical output uses `gf-wordbench` |
| `--mode file` | `--mode quick` | Read alias, emit canonical |
| `--mode all` | `--mode diagnostic` | Read alias, emit canonical |
| `--target-file` | `--target` | Compatibility input alias |
| `--skip-version-probe` | `--no-version-probe` | Compatibility input alias |
| `--emit-cpu-stats` | `--cpu-stats` | Compatibility input alias |
| `--timeout-sec` | `--compile-timeout` | Compatibility input alias |
| `--diff-previous` | `--compare-previous` | Compatibility input alias |
| `--scan-dir` | `project.toml` source config | Migration-only override |
| `--scan-glob` | `project.toml` source config | Migration-only override |
| `--include-regex` | `project.toml` selection config | Migration-only override |
| `--exclude-regex` | `project.toml` selection config | Migration-only override |
| `--gf-path` | project toolchain + resolved environment | Migration-only override |

Compatibility use prints one warning per invocation.

Canonical writers never persist legacy mode names or option labels as model values.

---

# 46. Compatibility alias rules

Compatibility aliases are accepted only at the CLI boundary.

The adapter:

```text
accepts the legacy spelling
emits one compatibility warning
normalizes immediately to the canonical command or option
builds only canonical RunConfig values
writes only canonical values to reports and schemas
```

Compatibility aliases do not appear in canonical help examples.

Removing a compatibility alias is a breaking CLI-contract change and requires:

```text
CHANGELOG.md
docs/release/MIGRATION_AND_DEPRECATION.md
a major CLI contract version
compatibility and help tests
```

---

# 47. CLI adapter structure

The CLI adapter has four responsibilities:

```text
argument parser
    defines commands, options, aliases and local syntax validation

configuration adapter
    converts CLI values into the shared bootstrap request

command dispatcher
    invokes the appropriate application use case

console presenter
    renders concise human output and maps structured results to exit codes
```

Conceptual dispatch:

```python
def main(argv=None) -> int:
    try:
        request = parse_cli_request(argv)
        result = dispatch_application_request(request)
        present_cli_result(result)
        return determine_exit_code(result)
    except CliConfigurationError as exc:
        print_error(exc)
        return EXIT_USAGE_ERROR
    except ControlledValidationFailure as exc:
        print_failure(exc)
        return EXIT_VALIDATION_FAILED
    except CancellationRequested as exc:
        print_error(exc)
        return EXIT_CANCELLED
    except Exception as exc:
        print_error(exc)
        return EXIT_RUNTIME_ERROR
```

Private module and function names are internal. The responsibility boundaries and exit behavior are normative.

---

# 48. Shared configuration contract

The CLI configuration adapter delegates to shared bootstrap and configuration code.

It normalizes CLI-specific values:

```text
Path
enum alias
repeatable scenario IDs
boolean flags
timeout values
```

It must not:

- rebuild project defaults;
- parse `project.toml` independently;
- construct a different GF path;
- select files;
- infer release gates;
- mutate application state.

Equivalent CLI and GUI requests produce equivalent `RunConfig`.

---

# 49. CLI summary contract

Conceptual presenter contract:

```python
present_run_summary(run_result: RunResult, *, quiet: bool = False) -> None
```

The summary reads structured fields.

It must not parse:

```text
summary.md
summary.json
master.log
```

to determine current status when `RunResult` is available.

It may print artifact paths from `RunPaths`.

---

# 50. Determining the exit code

Canonical mapping:

```python
def determine_exit_code(
    run_result: RunResult,
    *,
    cancelled: bool = False,
    runtime_error: bool = False,
    cancellation_error: bool = False,
) -> int:
    if runtime_error or cancellation_error or run_result.overall_status == "ERROR":
        return EXIT_RUNTIME_ERROR
    if cancelled:
        return EXIT_CANCELLED
    if run_result.overall_status == "FAIL":
        return EXIT_VALIDATION_FAILED
    return EXIT_OK
```

Before-run invocation and configuration exceptions map to:

```text
EXIT_USAGE_ERROR
```

The function must not depend only on:

```text
file fail_count
```

because a run includes scenarios, release gates, report requirements and integrity failures.

---

# 51. Invalid option combinations

The parser or CLI validation layer rejects:

```text
quick without target
target outside quick
checkpoint ID outside checkpoint mode
checkpoint mode without resolvable checkpoint
release with no-compile
release with max-files > 0
baseline with no-compare-previous
quiet with verbose
gold update with neither IDs nor --all
gold update with IDs and --all
schemas check with no paths
reports check with no run directory
negative max-files
zero or negative timeout
unknown scenario ID
```

A project policy may further restrict optional scenarios and checkpoint selection.

---

# 52. Cancellation

## 52.1 User interrupt

On `Ctrl+C`:

1. request controlled cancellation;
2. stop launching new stages;
3. terminate owned child processes;
4. preserve partial evidence;
5. write best-effort reports;
6. return exit `4` when containment and evidence preservation complete safely;
7. return exit `3` when cancellation handling itself fails critically.

## 52.2 Repeated interrupt

A second interrupt may force immediate termination.

The CLI warns that the run may remain unfinalized. An externally forced termination may prevent the application from returning a canonical code.

## 52.3 Partial run

A cancelled partial run must not be represented as finalized.

Automatic baseline discovery skips it unless the baseline policy explicitly supports partial runs.

## 52.4 Timeout distinction

A process timeout is a runtime error:

```text
timeout              -> 3
controlled cancellation -> 4
```

The CLI must not relabel a timeout as cancellation.

---

# 53. Filesystem behavior

## 53.1 Run creation

`validate` creates:

```text
<out-root>/run_<run-id>/
```

## 53.2 No source mutation

Normal validation does not modify:

```text
project.toml
.gf source
.gfs scenarios
.gold files
project documentation
```

## 53.3 Checker commands

`project check`, `scenarios check`, `schemas check`, and `reports check` are read-only.

## 53.4 Gold update

Only `gold update` may modify selected `.gold` files.

## 53.5 Existing run collision

A new unique run ID is generated.

Existing run directories are not overwritten silently.

---

# 54. Working-directory independence

Commands must behave consistently regardless of the caller’s current directory when explicit roots are equivalent.

Do not depend on:

- terminal working directory;
- IDE working directory;
- launcher location;
- batch-file current directory.

Relative CLI paths are resolved according to the documented CLI path policy.

Canonical path policy:

- `--project-root` resolves from current shell directory;
- project-relative assets then resolve from the project root;
- run-relative artifacts resolve from the run directory.

---

# 55. Output artifacts

A normal validation run exposes:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
details/
raw/
artifacts/
```

The CLI prints high-value paths.

It does not generate reports itself.

The run and reporting modules own them.

---

# 56. CLI tests

CLI test structure:

```text
tests/cli/
├── test_cli_help.py
├── test_cli_version.py
├── test_cli_parser.py
├── test_cli_validate.py
├── test_cli_modes.py
├── test_cli_configuration.py
├── test_cli_project_check.py
├── test_cli_scenarios_check.py
├── test_cli_gold_update.py
├── test_cli_schemas_check.py
├── test_cli_reports_check.py
├── test_cli_exit_codes.py
├── test_cli_output.py
├── test_cli_legacy_aliases.py
├── test_cli_cancellation.py
├── test_cli_security.py
└── test_cli_windows.py
```

## 56.1 Help tests

Verify:

- global help;
- every command help;
- no execution;
- exit `0`;
- canonical executable name.

## 56.2 Version tests

Verify:

- package version source;
- exact application name;
- exit `0`.

## 56.3 Parser tests

Verify:

- required command;
- mode values;
- repeatable scenarios;
- option conflicts;
- positive timeouts;
- nonnegative max-files;
- path types;
- quiet/verbose conflict.

## 56.4 Validation tests

Verify:

- CLI calls shared configuration builder;
- CLI invokes the shared run application service;
- CLI does not call compiler directly;
- CLI does not call scanner directly;
- CLI does not call report writers directly when orchestration owns reporting;
- result summary uses `RunResult`;
- artifact paths print.

## 56.5 Mode tests

Verify:

```text
quick target required
checkpoint ID behavior
release strict gates
release no-compile rejection
diagnostic max-files
legacy file -> quick
legacy all -> diagnostic
```

## 56.6 Exit-code tests

Verify:

```text
OK -> 0
FAIL -> 1
invalid args/config -> 2
ERROR -> 3
controlled cancellation -> 4
cancellation-handling failure -> 3
help -> 0
version -> 0
```

Include failures caused only by:

- scenario;
- PGF gate;
- manifest;
- report writer;
- timeout.

## 56.7 Checker tests

Verify each checker is read-only and maps invalid contracts to `2`.

## 56.8 Gold tests

Verify:

- explicit scenario IDs;
- `--all`;
- confirmation;
- `--yes`;
- no write after failed marker;
- no write after timeout;
- atomic write;
- only selected gold changes.

## 56.9 Security tests

Verify:

- unregistered script path cannot be executed;
- target traversal rejected;
- output-root escape rejected;
- no shell strings;
- secrets not printed;
- strict mode rejects prohibited scenario commands.

## 56.10 Windows tests

Verify:

- spaces;
- Unicode;
- drive letters;
- backslashes;
- `.bat` argument forwarding;
- original exit code preserved.

---

# 57. CLI golden-output tests

Human console output may use golden fixtures for:

```text
successful quick run
failing checkpoint run
release error
diagnostic partial run
project-check failure
scenario-check success
gold update confirmation
schema-check legacy warning
report-check hash mismatch
```

Rules:

- fixture data is deterministic;
- paths use controlled test roots;
- only user-facing wording is golden;
- exit codes are asserted separately;
- automation never depends on golden prose.

---

# 58. Contract checker for CLI help

The release contract test executes:

```text
gf-wordbench --help
gf-wordbench validate --help
gf-wordbench project check --help
gf-wordbench scenarios check --help
gf-wordbench gold update --help
gf-wordbench schemas check --help
gf-wordbench reports check --help
```

It verifies that:

- documented commands exist;
- required canonical options exist;
- removed legacy options are not presented as canonical;
- help returns `0`;
- package version is consistent;
- no command performs work during help rendering.

---

# 59. Anti-drift indicators

Probable CLI drift exists when:

- help says `gf-audit` instead of `gf-wordbench`;
- canonical mode is `all` or `file`;
- CLI and GUI build different GF paths;
- CLI selects files directly;
- CLI calls compiler directly;
- CLI calls report writers outside the orchestration contract;
- exit code depends only on file failures;
- scenario failures return `0`;
- release manifest failure returns `0`;
- project-owned source settings reappear as normal CLI defaults;
- normal validation updates gold;
- arbitrary `.gfs` paths can be executed;
- stdout prose becomes an automation API;
- a checker rewrites the asset it checks;
- `--strict` silently weakens required gates;
- a legacy alias is emitted into canonical persisted data;
- launcher changes mode or paths;
- invalid option combinations reach deep execution;
- quiet mode suppresses errors;
- traceback is printed by default;
- report artifacts are named differently from `RunPaths`;
- current working directory changes semantics unexpectedly.

Any indicator requires coordinated review.

---

# 60. Change control

A public CLI change must identify:

```text
CLI contract version:
Command:
Option:
Current syntax:
New syntax:
Default changed:
Mode impact:
Configuration impact:
RunResult impact:
Exit-code impact:
Automation impact:
Security impact:
Compatibility alias:
Compatibility period:
Tests:
Documentation:
```

Required checklist:

```text
[ ] CLI entrypoint updated
[ ] package console script updated
[ ] bootstrap reviewed
[ ] RunConfig reviewed
[ ] RunResult reviewed
[ ] GUI equivalence reviewed
[ ] exit-code reference updated
[ ] Windows launcher reviewed
[ ] help tests updated
[ ] parser tests updated
[ ] integration tests updated
[ ] CI examples updated
[ ] migration documentation updated
[ ] changelog updated
[ ] security impact reviewed
```

---

# 61. Compatibility rules

## 61.1 Compatible minor changes

May:

- improve help wording;
- add an optional non-conflicting flag;
- add a new checker option;
- add richer default console summaries;
- add a compatibility warning;
- support another path representation;
- improve error detail.

Must not:

- change canonical command meaning;
- change exit-code meaning;
- weaken release gates;
- change default project ownership;
- make reports machine-authoritative;
- remove an accepted option without a compatibility and migration policy.

## 61.2 Breaking changes

Include:

- renaming a command without alias;
- changing mode semantics;
- reusing an option for another meaning;
- changing exit-code meanings;
- making normal validation write source assets;
- changing project-root interpretation;
- changing whether a command executes GF;
- changing gold confirmation safety.

Breaking changes require a major CLI contract version.

---

# 62. CLI conformance checklist

```text
[ ] installed command is gf-wordbench
[ ] --version uses package metadata
[ ] subcommand help is complete
[ ] validate uses shared bootstrap
[ ] validate invokes the shared run application service
[ ] CLI does not own validation stages
[ ] project.toml owns language-specific selection
[ ] four canonical modes are accepted and normalized
[ ] quick target rules are enforced
[ ] checkpoint selection follows project configuration
[ ] release gates cannot be bypassed
[ ] diagnostic selection is deterministic
[ ] strict mode enforces its documented rules
[ ] operation-specific timeouts are validated
[ ] registered scenario IDs are supported
[ ] arbitrary script execution is absent
[ ] previous-run comparison options follow the comparison contract
[ ] explicit baseline is validated
[ ] concise console output follows the summary contract
[ ] quiet and verbose behavior is enforced
[ ] overall status drives exit code
[ ] five exit codes are stable
[ ] controlled cancellation returns `EXIT_CANCELLED` and cancellation-handling failure returns `EXIT_RUNTIME_ERROR`
[ ] project check is read-only and complete
[ ] scenarios check is read-only and complete
[ ] gold update is explicit and atomic
[ ] schemas check is read-only
[ ] reports check verifies manifests
[ ] compatibility aliases normalize to canonical values
[ ] Windows launcher forwards arguments and exit code
[ ] path handling supports spaces and Unicode
[ ] secrets are not printed
[ ] unit tests pass
[ ] CLI integration tests pass
[ ] Windows tests pass
[ ] help contract tests pass
```

---

# 63. Related documents

```text
README.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
docs/usage/INSTALLATION.md
docs/usage/QUICK_START.md
docs/usage/GUI_REFERENCE.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/validation/VALIDATION_MODES.md
docs/validation/RELEASE_GATES.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/SUMMARY_MARKDOWN_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/reference/EXIT_CODES.md
docs/reference/COMMAND_REFERENCE.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
SECURITY.md
```

---

# 64. Governing rule

The GF Wordbench CLI is a stable adapter over shared application behavior.

Therefore:

> Parse and validate user intent, resolve one canonical configuration, invoke the shared orchestration layer, print structured human guidance, return a stable exit code, and never duplicate the validation system inside the command-line interface.
