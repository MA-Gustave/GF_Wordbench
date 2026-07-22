# GF Wordbench — Command Reference

**Document ID:** `GF-WB-COMMAND-REFERENCE`  
**Status:** Final normative reference  
**Applies to:** GF Wordbench CLI commands, compatibility aliases, write-safety behavior, and external GF commands issued by GF Wordbench  
**Owner:** GF Wordbench maintainers  
**Primary executable:** `gf-wordbench`  
**Command contract version:** `1.0.0`  
**Normative counterparts:**
- `docs/usage/CLI_REFERENCE.md`
- `docs/reference/EXIT_CODES.md`
- `docs/reference/STATUS_VALUES.md`
- `docs/configuration/PROJECT_TOML_REFERENCE.md`
- `docs/configuration/ENVIRONMENT_AND_PATHS.md`
- `docs/gf/GF_TOOLCHAIN_INTEGRATION.md`
- `docs/gf/GF_PATH_RESOLUTION.md`
- `docs/gf/GF_COMPILATION.md`
- `docs/gf/GF_PGF_BUILD.md`
- `docs/gf/GF_SCRIPT_EXECUTION.md`
- `docs/operations/RUN_DIRECTORY_LIFECYCLE.md`
- `docs/reports/ARTIFACT_MANIFEST.md`
- `docs/release/VERSIONING_POLICY.md`

**Document version:** `1.0.0`

---

## 1. Purpose

This document is the consolidated command index for GF Wordbench.

It covers two command surfaces:

1. commands a user or automation system sends to `gf-wordbench`;
2. external GF requests that GF Wordbench constructs, executes, captures, and records.

The two surfaces must not be confused.

User-facing commands express intent:

```text
validate the active project
check the toolchain
compare gold output
verify a run
archive evidence
```

GF commands perform authoritative grammar operations:

```text
probe GF version
compile a module
run a .gfs scenario
build a PGF
parse
linearize
generate
inspect morphology or grammar structure
```

> Users invoke GF Wordbench. GF Wordbench invokes GF through locked external-tool contracts.

This reference defines command names and high-level option semantics. Detailed parser behavior, exact numeric exit codes, and command-specific examples remain additionally governed by their dedicated references.

---

## 2. Command status

The canonical command surface defined here is the final GF Wordbench `1.x` command contract.

Legacy GF Audit-compatible inputs may remain temporarily readable through explicit aliases.

Canonical help and reports MUST display final GF Wordbench names, not legacy names.

### 2.1 Canonical modes

```text
quick
checkpoint
diagnostic
release
```

### 2.2 Legacy mode aliases

```text
file → quick
all  → diagnostic
```

Aliases are compatibility inputs only.

Canonical output always records:

```text
quick
checkpoint
diagnostic
release
```

### 2.3 Command stability

Removing or incompatibly changing a command, option, exit meaning, or write-safety rule requires versioning under `VERSIONING_POLICY.md`.

---

## 3. Invocation grammar

General form:

```text
gf-wordbench [global-options] <command> [command-options] [arguments]
```

Examples:

```text
gf-wordbench --version
gf-wordbench project show
gf-wordbench validate --mode quick --target-file lib/src/example/NounX.gf
gf-wordbench gold check linearize
gf-wordbench runs verify 20260722_163210 --strict
```

### 3.1 Help

```text
gf-wordbench --help
gf-wordbench <command> --help
gf-wordbench <group> <command> --help
```

Help is read-only.

### 3.2 Version

```text
gf-wordbench --version
```

Canonical human output:

```text
GF Wordbench <MAJOR.MINOR.PATCH>
```

The runtime version comes from installed package metadata.

### 3.3 Option placement

Global options SHOULD appear before the command.

Command-specific options appear after the command.

A parser MAY accept an unambiguous global option later in the command line, but automation should use canonical placement.

---

## 4. Global option model

The final parser may expose some options only on commands that need them. Their semantic ownership remains global.

### 4.1 Project selection

```text
--project-root <path>
--project-config <path>
```

Canonical default configuration:

```text
project/project.toml
```

Rules:

- one active project only;
- `project.toml` remains the authority for project-owned facts;
- CLI options must not create a second language-project definition;
- project paths are resolved before execution.

### 4.2 GF environment

```text
--gf-exe <path>
--rgl-root <path>
--gf-path <path-list>
```

Rules:

- `--gf-exe` selects the executable actually invoked;
- `--rgl-root` supplies the machine-local RGL root;
- `--gf-path` is a complete explicit path override;
- equivalent values from local state may be used when no CLI override exists;
- the resolved values are recorded in run evidence.

### 4.3 Output environment

```text
--out-root <path>
```

The output root owns run directories.

It must remain separate from source, project validation inputs, and gold files.

### 4.4 Strictness

```text
--strict
```

Strict mode normally:

- rejects unknown or unsupported compatibility states;
- strengthens path and schema checks;
- rejects unsafe symlink behavior;
- treats selected warnings as errors where the owning policy requires it;
- never weakens release requirements.

### 4.5 Non-interactive execution

```text
--non-interactive
```

When exposed, this option prohibits prompts.

A command requiring confirmation must fail safely unless the exact write action has an explicit force/confirmation mechanism.

### 4.6 Output formatting

Potential canonical options:

```text
--quiet
--verbose
```

Human verbosity must not alter structured result semantics.

A machine-readable console format must have its own documented schema before becoming a stable automation interface.

Automation should prefer `summary.json`.

---

## 5. Configuration precedence

Project and environment values have different authorities.

### 5.1 Project-owned facts

Examples:

```text
project ID
language code
source directory
entrypoints
checkpoints
required scenarios
optional scenarios
PGF requirement
```

Authority:

```text
project/project.toml
```

A CLI selector may narrow a development run, but it does not rewrite the canonical project definition.

### 5.2 Environment values

Examples:

```text
GF executable
RGL root
output root
explicit GF path
timeout
```

Recommended precedence:

```text
explicit CLI
→ explicit GUI
→ local application state/environment configuration
→ documented discovery
→ error
```

### 5.3 Explicit path override

A non-empty:

```text
--gf-path
```

replaces the project-derived effective GF path for that run.

It does not append silently.

### 5.4 Recorded resolution

Resolved configuration—not only raw arguments—must appear in run evidence.

---

## 6. Command safety classes

Every command belongs to one safety class.

### 6.1 Read-only project command

Reads project or run assets but does not modify them.

Examples:

```text
project show
project check
gold check
gold diff
manifest verify
runs show
runs verify
```

### 6.2 Run-writing command

Creates a new run directory and writes only run-owned evidence.

Examples:

```text
validate
release check
scenario run
```

Normal run-writing commands do not modify project source or gold.

### 6.3 Project-writing command

Modifies active project assets.

Examples:

```text
project init
project reset
project migrate
gold update
```

These commands require explicit invocation and atomic writes where applicable.

### 6.4 Historical-run maintenance command

Writes, copies, archives, restores, or deletes run evidence.

Examples:

```text
manifest create
runs archive
runs restore
runs clean
```

### 6.5 Probe command

May launch GF but does not compile active project source unless explicitly stated.

Examples:

```text
gf version
gf capabilities
gf check
paths check
```

---

# Part I — Core validation commands

## 7. `validate`

Canonical command:

```text
gf-wordbench validate --mode <mode> [selectors] [execution-options]
```

Purpose:

- load the active project;
- resolve the environment;
- create one run directory;
- execute selected validation stages;
- write structured and human evidence;
- finalize and verify the artifact manifest where possible.

### 7.1 Modes

```text
--mode quick
--mode checkpoint
--mode diagnostic
--mode release
```

### 7.2 Default mode

The explicit mode is recommended for automation.

When the CLI defines a default, it must be documented in `CLI_REFERENCE.md` and must not change incompatibly within a stable major.

### 7.3 Typical examples

```text
gf-wordbench validate --mode quick --target-file lib/src/example/NounX.gf
```

```text
gf-wordbench validate --mode checkpoint --checkpoint NounX.gf
```

```text
gf-wordbench validate --mode diagnostic
```

```text
gf-wordbench validate --mode release
```

### 7.4 Write behavior

Creates:

```text
run_<run-id>/
```

It MUST NOT modify:

```text
project source
.gfs scenarios
.gold files
project.toml
project documentation
```

### 7.5 Result

Returns a command exit status and writes the canonical run result.

A validation failure can still produce a structurally finalized run.

---

## 8. `quick` validation

Canonical form:

```text
gf-wordbench validate --mode quick --target-file <source.gf>
```

Purpose:

- fast edit-loop feedback;
- selected file scan;
- selected file compile;
- optional configured smoke scenario;
- concise reports.

### 8.1 Required selector

Normally:

```text
--target-file <path>
```

The path must resolve to one selected project source file.

### 8.2 Compatibility alias

Legacy:

```text
--mode file
```

Canonicalized to:

```text
--mode quick
```

### 8.3 Limitations

Quick mode cannot by itself prove release readiness.

---

## 9. `checkpoint` validation

Canonical form:

```text
gf-wordbench validate --mode checkpoint --checkpoint <checkpoint>
```

Purpose:

- validate a configured module family or architecture layer;
- compile the checkpoint and required dependencies;
- execute associated scenarios;
- compare associated gold output;
- compare with a compatible previous run when requested.

### 9.1 Selector

```text
--checkpoint <configured-module-or-id>
```

The value must map to a checkpoint declared by the active project.

### 9.2 Multiple checkpoints

When supported:

```text
--checkpoint <id-1> --checkpoint <id-2>
```

Execution order follows project declaration, not argument reordering.

### 9.3 Release relationship

A passing checkpoint is necessary only when project release policy marks it required.

It does not replace final entrypoint and PGF validation.

---

## 10. `diagnostic` validation

Canonical form:

```text
gf-wordbench validate --mode diagnostic
```

Purpose:

- broad source inventory;
- static scan;
- per-file GF compilation;
- detailed direct/downstream/ambiguous classification;
- extended raw evidence;
- optional broad scenario execution;
- investigation of toolchain or contract problems.

### 10.1 Compatibility alias

Legacy:

```text
--mode all
```

Canonicalized to:

```text
--mode diagnostic
```

### 10.2 Verbosity

Diagnostic mode may omit GF silent mode where the external-tool contract permits it.

### 10.3 Release limitation

Diagnostic mode does not produce a `READY` release decision.

---

## 11. `release` validation

Canonical form:

```text
gf-wordbench validate --mode release
```

Equivalent convenience command:

```text
gf-wordbench release check
```

Both commands MUST call the same orchestration path and release-gate engine.

### 11.1 Required scope

Release mode evaluates:

- project identity and configuration;
- GF/RGL compatibility;
- project contracts;
- source inventory/static policy;
- required checkpoints;
- release entrypoints;
- required scenarios;
- required gold comparisons;
- completeness/missing-function policy;
- required PGF build;
- regressions and project blockers;
- schema and contract integrity;
- reports and manifest integrity;
- final release decision.

### 11.2 Prohibited options

Release mode MUST reject or neutralize options that weaken required scope, including:

```text
--no-compile
--skip-version-probe
single-file-only target
gold update
unbounded generation
```

### 11.3 Output decision

```text
READY
NOT_READY
ERROR
```

### 11.4 Write behavior

Writes only the release run directory and its current-run artifacts.

It does not publish or overwrite an external release artifact automatically.

---

## 12. Validation selectors

### 12.1 Target file

```text
--target-file <path>
```

Used primarily with `quick`.

The selected path must:

- exist;
- be a regular `.gf` source;
- remain under the permitted project source root;
- satisfy selection policy or receive an explicit diagnostic.

### 12.2 Checkpoint

```text
--checkpoint <id-or-module>
```

Used with `checkpoint`.

### 12.3 Scenario

```text
--scenario <scenario-id>
```

May narrow non-release scenario execution.

It must not omit required release scenarios in release mode.

### 12.4 Maximum files

```text
--max-files <integer>
```

`0` means no configured limit where compatibility behavior retains that rule.

Negative values are invalid.

Release mode SHOULD reject a limit that truncates required scope.

### 12.5 Include and exclude expressions

```text
--include-regex <regex>
--exclude-regex <regex>
```

These are development overrides.

Required project files must not be excluded silently.

Release mode uses canonical project selection and contract checks.

---

## 13. Validation stage options

### 13.1 Scan-only compatibility option

```text
--no-compile
```

Meaning:

- run static scanning;
- record compilation as `SKIPPED`;
- do not claim compile success.

This is a compatibility option.

A future positive stage-selection interface may replace it through deprecation.

Not allowed for release readiness.

### 13.2 Skip GF version probe

```text
--skip-version-probe
```

Meaning:

- version identity remains unknown;
- toolchain cannot be release-certified.

Not allowed in release mode.

### 13.3 Emit GF CPU statistics

```text
--emit-cpu-stats
```

Passes the supported GF performance option only when explicitly enabled and compatible.

Performance output is evidence, not compile success.

### 13.4 Keep successful detail reports

```text
--keep-ok-details
```

Controls optional detail artifacts.

It must not remove required raw evidence.

### 13.5 Previous-run comparison

```text
--diff-previous
```

Requests comparison against the previous compatible finalized run.

The candidate must still pass project/schema/integrity checks.

### 13.6 Compile timeout

```text
--timeout-sec <positive-integer>
```

Compatibility spelling for per-file compile timeout.

Operation-specific final options may use explicit names such as:

```text
--compile-timeout-sec
--scenario-timeout-sec
--pgf-timeout-sec
```

Exact parser names belong to `CLI_REFERENCE.md`.

### 13.7 GF path

```text
--gf-path <path-list>
```

Complete explicit override.

The selected path and separator are recorded.

---

## 14. Validation examples

### 14.1 Quick file

```text
gf-wordbench \
  --gf-exe C:/tools/gf/gf.exe \
  --rgl-root C:/work/gf-rgl/src \
  --out-root C:/work/gf-runs \
  validate \
  --mode quick \
  --target-file lib/src/example/NounX.gf
```

### 14.2 Checkpoint with diff

```text
gf-wordbench validate \
  --mode checkpoint \
  --checkpoint NounX.gf \
  --diff-previous
```

### 14.3 Full diagnostic without compilation

```text
gf-wordbench validate \
  --mode diagnostic \
  --no-compile
```

This is scan evidence only.

### 14.4 Release

```text
gf-wordbench validate --mode release
```

---

# Part II — Project commands

## 15. `project show`

```text
gf-wordbench project show
```

Safety:

```text
read-only
```

Displays:

- project ID;
- display name;
- language code;
- project config path;
- source root;
- entrypoints;
- checkpoints;
- required/optional scenario counts;
- PGF requirement;
- readiness summary.

It must not modify `project.toml`.

---

## 16. `project check`

```text
gf-wordbench project check
gf-wordbench project check --strict
```

Safety:

```text
read-only
```

Validates:

- project schema;
- identity;
- path syntax and containment;
- selection regexes;
- entrypoints/checkpoints;
- scenario registry;
- required files;
- project documentation;
- unresolved placeholders;
- stale language identity;
- interfile contract consistency.

`--strict` may enable deeper filesystem/document drift checks.

---

## 17. `project init`

```text
gf-wordbench project init
```

Safety:

```text
project-writing
```

Purpose:

- create one active project from the canonical template;
- render project identity;
- create required project documentation;
- create validation directories;
- initialize canonical `project.toml`.

### 17.1 Required behavior

- explicit identity input;
- no silent overwrite;
- atomic config writes;
- template placeholders resolved or reported;
- created files listed before completion.

### 17.2 Existing project

The command must fail safely when an active project already exists unless an explicit supported destination or replacement workflow is used.

---

## 18. `project reset`

```text
gf-wordbench project reset
```

Safety:

```text
destructive project-writing
```

Purpose:

- remove active-language identity/content;
- preserve framework code and language-neutral templates;
- prepare the copy for another project.

### 18.1 Required safeguards

- explicit confirmation;
- preview;
- backup/archive option;
- old-language identity scan;
- no framework deletion;
- no run-history deletion unless separately requested.

`--force`, when implemented, must not bypass path containment or framework protection.

---

## 19. `project migrate`

```text
gf-wordbench project migrate <source>
```

Safety:

```text
project-writing
```

Purpose:

- convert legacy GF Audit/project inputs into canonical GF Wordbench project assets.

Rules:

- read source without modifying it;
- create a canonical destination;
- report warnings and losses;
- write atomically;
- remain idempotent;
- never invent unrecoverable meaning.

Dry-run form:

```text
gf-wordbench project migrate <source> --dry-run
```

---

## 20. `project archive`

```text
gf-wordbench project archive
```

Safety:

```text
project/archive writing
```

Creates a project archive containing the project-controlled assets selected by policy.

It is distinct from:

```text
runs archive
```

A project archive may include release evidence by explicit selection.

---

# Part III — GF environment and path commands

## 21. `paths resolve`

```text
gf-wordbench paths resolve
gf-wordbench paths resolve --strict
gf-wordbench paths resolve --explain
```

Safety:

```text
read-only
```

Purpose:

- load project path requirements;
- resolve project-relative path parts;
- resolve RGL aliases;
- apply explicit override policy;
- deduplicate;
- display the effective ordered GF path.

`--explain` shows provenance for every path entry.

No GF compilation is performed.

---

## 22. `paths check`

```text
gf-wordbench paths check
```

Safety:

```text
read-only / optional filesystem probe
```

Checks:

- project root;
- source coverage;
- RGL root;
- required aliases;
- path containment;
- directories vs files;
- separator compatibility;
- duplicate resolution.

It may invoke a bounded GF capability check only when the command contract explicitly says so.

---

## 23. `gf version`

```text
gf-wordbench gf version
```

Safety:

```text
GF probe
```

Normative external request:

```text
<gf-executable> --version
```

Displays:

- executable;
- raw version line;
- normalized version;
- probe status;
- compatibility tier.

It does not compile project source.

---

## 24. `gf capabilities`

```text
gf-wordbench gf capabilities
```

Safety:

```text
GF probe
```

Purpose:

- detect or smoke-test the capabilities required by GF Wordbench;
- report evidence level.

Potential capability groups:

```text
version
batch compilation
GF path options
GFO output
scenario stdin
grammar import
parse
linearize
generate
morphology
introspection
PGF build
```

A capability query must not mutate project assets.

---

## 25. `gf check`

```text
gf-wordbench gf check
gf-wordbench gf check --strict
```

Safety:

```text
GF/RGL probe
```

Combines:

- executable validation;
- version probe;
- compatibility policy;
- GF path check;
- required capability suite;
- RGL identity/module check.

It may compile only a bundled language-neutral smoke fixture when documented.

It does not compile the active project unless an explicit option requests project validation.

---

## 26. `gf compatibility`

```text
gf-wordbench gf compatibility
```

Safety:

```text
read-only plus probes
```

Displays:

```text
normalized GF version
compatibility tier
platform support
RGL identity
required capability results
warnings
blockers
policy version
```

It does not replace `validate`.

---

# Part IV — Scenario commands

## 27. `scenario list`

```text
gf-wordbench scenario list
```

Safety:

```text
read-only
```

Displays registered scenarios in deterministic project order:

- ID;
- required/optional;
- script path;
- associated modes;
- entrypoint;
- gold status;
- normalization profile.

Fields not represented by project schema `1.0` are derived only from documented project validation contracts.

---

## 28. `scenario check`

```text
gf-wordbench scenario check
gf-wordbench scenario check <scenario-id>
```

Safety:

```text
read-only
```

Validates:

- registry uniqueness;
- script existence;
- path containment;
- encoding;
- marker structure;
- input references;
- gold mapping;
- normalization profile.

It does not execute GF unless an explicit run option is selected.

---

## 29. `scenario run`

```text
gf-wordbench scenario run <scenario-id>
```

Safety:

```text
run-writing
```

Purpose:

- create a run directory;
- execute one registered `.gfs` script through GF;
- capture stdout/stderr;
- validate markers/assertions;
- normalize output;
- compare gold when configured;
- write a structured `ScenarioResult`.

### 29.1 Multiple scenarios

When supported:

```text
gf-wordbench scenario run <id-1> <id-2>
```

Execution order remains deterministic.

### 29.2 Release limitation

Running selected scenarios manually does not replace release mode.

---

# Part V — Gold commands

## 30. `gold list`

```text
gf-wordbench gold list
```

Safety:

```text
read-only
```

Displays:

- scenario ID;
- gold path;
- schema version;
- normalization version;
- existence;
- validation status;
- optional variant identity.

---

## 31. `gold check`

```text
gf-wordbench gold check
gf-wordbench gold check <scenario-id>
```

Safety:

```text
read-only
```

Checks:

- scenario/gold registry;
- gold path containment;
- UTF-8;
- schema header;
- scenario ID;
- normalization version;
- section markers;
- final newline.

When configured to execute current scenarios, it creates a new run but still leaves gold read-only.

---

## 32. `gold diff`

```text
gf-wordbench gold diff <scenario-id>
```

Safety:

```text
read-only project / run-writing evidence
```

Purpose:

- produce or locate current normalized output;
- compare against gold;
- write/display a unified diff;
- never update gold.

A mismatch is a validation result, not a tool error.

---

## 33. `gold update`

```text
gf-wordbench gold update <scenario-id>
gf-wordbench gold update <scenario-id> --dry-run
```

Safety:

```text
project-writing
```

Purpose:

- explicitly create or replace one reviewed gold file.

Required behavior:

- scenario execution must be complete;
- current normalized output must validate;
- raw output and diff must be reviewable;
- write must be atomic;
- old/new SHA-256 values must be recorded;
- normal validation semantics remain separate.

### 33.1 Prohibited use

`gold update` cannot run as a side effect of:

```text
validate
release check
scenario run
gold check
```

### 33.2 Bulk updates

Bulk update, if supported, must require an explicit command and per-scenario review evidence.

---

# Part VI — Contract and schema commands

## 34. `contracts check`

```text
gf-wordbench contracts check
gf-wordbench contracts check --strict
```

Safety:

```text
read-only
```

Checks applicable domains:

```text
framework Python interfile contracts
external GF/tool contracts
active-project interfile contracts
```

It verifies declared providers, consumers, paths, ownership, enums, and required tests/fixtures where machine-checkable.

It must not edit lock files.

---

## 35. `schemas check`

```text
gf-wordbench schemas check
gf-wordbench schemas check <path>
```

Safety:

```text
read-only
```

Validates supported canonical persisted formats:

```text
project.toml
application state
summary.json
manifest.json
scenario .out
scenario .gold
```

Unknown/legacy formats are classified through migration policy.

---

## 36. `schemas migrate`

```text
gf-wordbench schemas migrate <source> --to <schema-id/version>
gf-wordbench schemas migrate <source> --to <schema-id/version> --dry-run
```

Safety:

```text
write-capable migration
```

Rules:

- source remains unchanged;
- destination is explicit;
- warnings and losses recorded;
- output canonical;
- atomic write;
- idempotence tested.

A generic migration command must not replace specialized `project migrate` where project semantics are required.

---

# Part VII — Manifest commands

## 37. `manifest show`

```text
gf-wordbench manifest show <run-dir-or-id>
```

Safety:

```text
read-only
```

Displays:

- schema;
- run ID;
- generation time;
- artifact count;
- required count;
- total bytes;
- role summary.

---

## 38. `manifest verify`

```text
gf-wordbench manifest verify <run-dir-or-id>
gf-wordbench manifest verify <run-dir-or-id> --strict
```

Safety:

```text
read-only
```

Validates:

- JSON/schema;
- run ID;
- paths;
- duplicate entries;
- file existence;
- sizes;
- SHA-256 hashes;
- self-exclusion;
- summary consistency;
- mode-specific required artifacts under strict/release policy.

Verification never recalculates and writes replacement hashes.

---

## 39. `manifest create`

```text
gf-wordbench manifest create <run-dir>
```

Safety:

```text
historical-run writing
```

This is an expert recovery/maintenance operation.

Normal runs create the manifest during finalization.

Manual creation must:

- use explicit artifact declarations;
- avoid guessing ownership or requiredness;
- refuse active runs;
- write atomically;
- distinguish a newly created trust statement from verification of an original historical manifest.

It must not make an incomplete validation retroactively release-ready.

---

# Part VIII — Run commands

## 40. `runs list`

```text
gf-wordbench runs list
```

Safety:

```text
read-only
```

Displays:

```text
run ID
project ID
mode
outcome
lifecycle classification
release decision
start time
size
manifest status
```

Discovery scans only the configured output root.

---

## 41. `runs show`

```text
gf-wordbench runs show <run-id>
```

Safety:

```text
read-only
```

Displays canonical summary and artifact references.

It must not regenerate missing reports.

---

## 42. `runs verify`

```text
gf-wordbench runs verify <run-id>
gf-wordbench runs verify <run-id> --strict
```

Safety:

```text
read-only
```

Combines:

- lifecycle classification;
- summary schema validation;
- manifest verification;
- run-ID consistency;
- artifact integrity;
- previous-run eligibility.

---

## 43. `runs archive`

```text
gf-wordbench runs archive <run-id>
```

Safety:

```text
archive-writing
```

Recommended strict process:

```text
verify source run
→ create archive
→ calculate archive SHA-256
→ extract to isolated temporary directory
→ verify extracted run
→ publish archive
```

Archival does not delete the original automatically.

---

## 44. `runs restore`

```text
gf-wordbench runs restore <archive>
```

Safety:

```text
historical-run writing
```

Rules:

- do not merge into an existing run;
- do not overwrite a colliding run ID;
- preserve directory/run identity;
- verify after extraction;
- restored run is historical evidence, not resumed execution.

---

## 45. `runs clean`

```text
gf-wordbench runs clean --dry-run
gf-wordbench runs clean <run-id>
```

Safety:

```text
destructive historical-run maintenance
```

### 45.1 Dry run

Required for bulk or policy-based cleanup.

Displays:

```text
selected
protected
ineligible
unknown
```

### 45.2 Protected runs

Must not delete:

- active runs;
- output root itself;
- project/source/gold/framework paths;
- protected baseline;
- protected release evidence;
- unsafe symlink/reparse targets.

### 45.3 Deletion scope

Candidates must be validated individually.

String-prefix or wildcard deletion alone is prohibited.

---

# Part IX — Release command group

## 46. `release check`

```text
gf-wordbench release check
```

Safety:

```text
run-writing
```

Exact semantic alias:

```text
gf-wordbench validate --mode release
```

No separate release-validation implementation is permitted.

---

## 47. `release show`

```text
gf-wordbench release show <run-id>
```

Safety:

```text
read-only
```

Displays:

- decision;
- gate-policy version;
- gate results;
- blockers;
- warnings;
- PGF path/hash;
- manifest status;
- release evidence paths.

It requires a release-mode run result.

---

## 48. `release verify`

```text
gf-wordbench release verify <run-id>
```

Safety:

```text
read-only
```

Performs strict run and manifest verification plus release-specific consistency checks.

It does not rerun the release.

---

# Part X — GUI and launcher commands

## 49. GUI launch

Recommended canonical command:

```text
gf-wordbench gui
```

The GUI:

- loads the same project/configuration services;
- calls the same audit/release entrypoints;
- uses the same results;
- does not invoke GF directly from widgets.

### 49.1 GUI availability

When GUI dependencies are not installed, the command fails with an actionable installation/configuration error.

### 49.2 Launchers

Windows launchers may call:

```text
gf-wordbench gui
```

or another canonical command.

They must not add hidden validation semantics.

---

## 50. Launcher rules

A launcher may:

- activate a local virtual environment;
- select a repository working directory;
- invoke the canonical CLI;
- display a useful error.

A launcher must not:

- contain language-specific GF path logic;
- silently select another GF executable;
- alter required release scope;
- become the only supported entrypoint;
- hide arguments from run evidence.

---

# Part XI — External GF commands

## 51. External-command rule

GF Wordbench launches external tools with:

```python
subprocess-style ordered argument lists
shell=False
```

for normal GF execution.

The logged request and executed request derive from the same structured command.

Every GF operation has:

- explicit executable;
- explicit ordered arguments;
- explicit working directory;
- finite timeout;
- separate stdout/stderr capture;
- recorded execution state;
- recorded artifacts.

---

## 52. GF version probe

Normative request:

```text
<gf-executable> --version
```

Working directory:

```text
resolved project root
```

Default timeout:

```text
10 seconds
```

It does not compile source.

Preferred version text:

1. first non-empty stdout line;
2. otherwise first non-empty stderr line;
3. otherwise unknown.

Both streams remain preserved.

---

## 53. GF source compilation

Normative target request:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

### 53.1 Optional diagnostic verbosity

`-s` may be omitted in diagnostic mode when the compatibility adapter permits it.

### 53.2 Path options

Potential arguments:

```text
--gf-lib-path=<rgl-root>
--path=<effective-gf-path>
```

or the version-compatible equivalent.

### 53.3 Artifact options

Potential arguments:

```text
--gfo-dir=<run-gfo-dir>
--output-dir=<run-output-dir>
```

when supported and validated.

### 53.4 Optional performance argument

```text
--cpu
```

only through explicit configuration.

### 53.5 Final source argument

The source file path must be the final source argument.

### 53.6 Success criteria

All applicable:

- launched;
- no timeout;
- successful exit;
- no fatal diagnostic;
- required artifact checks pass.

---

## 54. PGF release build

Normative target request:

```text
<gf> -make -optimize-pgf <path-options> <entrypoint-1> [<entrypoint-N>...]
```

### 54.1 Entrypoints

Come from active project configuration.

Order is deterministic.

### 54.2 Output

Expected:

```text
<grammar-name>.pgf
```

The expected name/path is declared or deterministically derived through the active project contract.

### 54.3 Success

- process launched;
- no timeout;
- successful exit;
- no fatal diagnostic;
- expected PGF exists;
- PGF non-empty;
- artifact in run-owned location;
- artifact listed in manifest.

### 54.4 Diagnostic build

Diagnostic mode may disable optimization when explicitly allowed.

A non-optimized diagnostic artifact is not a substitute for an optimized release artifact when release policy requires optimization.

---

## 55. GF scenario execution

Conceptual request:

```text
<gf-executable> < <scenario.gfs>
```

Implementation rule:

- do not construct a shell-redirection command;
- open/read the `.gfs` file;
- provide its bytes/text through process stdin;
- use an ordered executable argument list;
- capture stdout/stderr separately.

Recommended structured representation:

```text
executable: <gf>
arguments: <version-compatible shell arguments>
stdin_source: project/validation/scenarios/<id>.gfs
working_directory: resolved project root
```

### 55.1 Scenario completion

A zero exit code alone is insufficient.

Required markers and assertions must complete.

### 55.2 Script trust

`.gfs` is executable/semi-executable input.

Shell escape behavior is prohibited under normal project policy.

---

## 56. GF shell operations used by scenarios

Exact GF shell syntax is version-checked and owned by `GF_SCRIPT_EXECUTION.md`.

Typical operation contracts include:

| Capability | Typical GF shell operation |
|---|---|
| import/load grammar | `i` / import with retained environment |
| parse | `p` |
| linearize | `l` |
| generate | `gr` |
| morphological analysis | `ma` |
| print grammar | `pg` |
| print missing linearizations | `pm` |
| compute concrete | `cc` |
| show operations | `so` |
| show dependencies | `sd` |
| quit | `q` |

### 56.1 Compatibility

GF Wordbench must probe or version-gate operations whose syntax differs across supported GF versions.

### 56.2 Markers

Scenarios should print stable begin/end markers using the supported GF shell mechanism.

Marker syntax is owned by scenario documentation.

### 56.3 No direct user command guarantee

This table documents the operations GF Wordbench scenarios depend on.

It is not a complete replacement for the official GF shell reference.

---

## 57. External command evidence

For each external request, preserve:

```text
executable
arguments
working directory
environment overrides
stdin source or absence
start time
end time
duration
exit code
timeout state
launch error
stdout path
stderr path
produced artifacts
```

Reports may display a rendered command.

The structured request remains authoritative.

---

# Part XII — Legacy compatibility

## 58. Legacy flat GF Audit invocation

Earlier GF Audit used a flat command surface similar to:

```text
gf-audit \
  --project-root <path> \
  --rgl-root <path> \
  --gf-exe <path> \
  --out-root <path> \
  --mode all|file
```

and options such as:

```text
--scan-dir
--scan-glob
--gf-path
--timeout-sec
--max-files
--target-file
--include-regex
--exclude-regex
--skip-version-probe
--no-compile
--emit-cpu-stats
--keep-ok-details
--diff-previous
```

### 58.1 Migration behavior

GF Wordbench may accept a documented subset during migration.

It must canonicalize:

```text
all  → diagnostic
file → quick
```

### 58.2 Project-owned legacy options

Legacy source-selection values are not canonical project identity.

After `project.toml` becomes authoritative:

```text
scan directory
scan glob
entrypoints
language identity
```

must come from the active project unless a development selector explicitly and safely narrows a run.

### 58.3 Canonical writers

Reports/state/configuration must not emit legacy mode names or obsolete state keys.

---

## 59. Deprecated compatibility inputs

Potential compatibility inputs:

```text
--mode all
--mode file
--no-compile
--skip-version-probe
flat root-level validation options
```

A deprecated input must:

- remain documented during its support window;
- warn on stderr;
- preserve machine stdout;
- map deterministically;
- identify its canonical replacement;
- be removed only under the versioning/deprecation policy.

---

# Part XIII — Exit and status behavior

## 60. Exit categories

The exact numeric mapping is authoritative in:

```text
docs/reference/EXIT_CODES.md
```

Command behavior distinguishes at least:

```text
success
validation failure
invalid arguments/configuration
runtime/tool error
cancellation
```

### 60.1 Validation failure

Examples:

- GF rejects source;
- required scenario assertion fails;
- gold mismatch;
- release blocker remains.

### 60.2 Runtime/tool error

Examples:

- executable cannot launch;
- timeout;
- manifest cannot be written;
- schema cannot be interpreted;
- unsafe path.

### 60.3 No result hiding

A command must not return success only because reports were written.

---

## 61. Canonical statuses

Validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Execution states include:

```text
completed
timed_out
cancelled
launch_failed
```

Release decisions:

```text
READY
NOT_READY
ERROR
```

These concepts remain separate in command output and persisted results.

---

# Part XIV — Command behavior rules

## 62. No hidden project writes

Read-only and validation commands must not modify:

```text
project.toml
project source
project docs
scenarios
inputs
gold files
```

Only explicit project-writing commands may do so.

---

## 63. Atomic write rule

Write-capable commands use atomic replacement where applicable for:

```text
project.toml migrations
application state
summary.json
manifest.json
gold updates
```

A failed write must not destroy the last valid destination.

---

## 64. No implicit shell rule

GF and normal helper processes are launched without an intermediate shell.

Manual quoting and redirection strings are prohibited in normal process construction.

---

## 65. Timeout rule

Every external process has a finite timeout.

Timeouts are operation-specific.

A timeout is not reported as an ordinary GF source failure.

---

## 66. Path rule

All path-taking commands must validate:

- existence where required;
- file vs directory type;
- root containment;
- traversal;
- symlink/reparse policy;
- Windows drive-relative ambiguity;
- portability for project-owned values.

---

## 67. Evidence rule

A command that executes validation must preserve sufficient evidence even when the validation fails.

A report command must not rerun GF to fill missing data.

---

## 68. Deterministic ordering

Commands must preserve deterministic order for:

```text
entrypoints
checkpoints
scenarios
file results
manifest entries
run listings
diff entries
```

Parallel execution must not change persisted order.

---

## 69. Confirmation rule

Destructive or project-writing commands require explicit intent.

Examples:

```text
project reset
gold update
runs clean
project migration overwrite
```

A prompt is not allowed in non-interactive mode unless a documented confirmation input was supplied.

---

## 70. Secret handling

Commands and reports must not persist:

```text
passwords
tokens
private keys
cookies
complete environment dumps
secret command arguments
```

Local absolute paths may be recorded when required for evidence.

---

# Part XV — Quick index

## 71. Command index

| Command | Safety | Primary result |
|---|---|---|
| `--help` | Read-only | Help text |
| `--version` | Read-only | Product version |
| `validate --mode quick` | Run-writing | Focused file run |
| `validate --mode checkpoint` | Run-writing | Checkpoint run |
| `validate --mode diagnostic` | Run-writing | Broad diagnostic run |
| `validate --mode release` | Run-writing | Release decision |
| `project show` | Read-only | Project summary |
| `project check` | Read-only | Project diagnostics |
| `project init` | Project-writing | Initialized project |
| `project reset` | Destructive | Reset active project |
| `project migrate` | Project-writing | Canonical migrated project |
| `project archive` | Archive-writing | Project archive |
| `paths resolve` | Read-only | Effective GF path |
| `paths check` | Read-only/probe | Path diagnostics |
| `gf version` | GF probe | Version identity |
| `gf capabilities` | GF probe | Capability evidence |
| `gf check` | GF/RGL probe | Toolchain result |
| `gf compatibility` | Read-only/probe | Compatibility result |
| `scenario list` | Read-only | Scenario registry |
| `scenario check` | Read-only | Scenario diagnostics |
| `scenario run` | Run-writing | ScenarioResult/run |
| `gold list` | Read-only | Gold registry |
| `gold check` | Read-only | Gold validation |
| `gold diff` | Read-only/run-writing | Comparison diff |
| `gold update` | Project-writing | Updated gold |
| `contracts check` | Read-only | Contract results |
| `schemas check` | Read-only | Schema results |
| `schemas migrate` | Migration-writing | Canonical destination |
| `manifest show` | Read-only | Manifest summary |
| `manifest verify` | Read-only | Integrity result |
| `manifest create` | Run maintenance | New manifest |
| `runs list` | Read-only | Run inventory |
| `runs show` | Read-only | Run summary |
| `runs verify` | Read-only | Run integrity |
| `runs archive` | Archive-writing | Verified archive |
| `runs restore` | Run maintenance | Restored run |
| `runs clean` | Destructive | Deleted selected runs |
| `release check` | Run-writing | Release run |
| `release show` | Read-only | Gate summary |
| `release verify` | Read-only | Release integrity |
| `gui` | UI launch | Shared GUI workflow |

---

## 72. Common workflows

### 72.1 Edit loop

```text
gf-wordbench validate --mode quick --target-file <file.gf>
```

### 72.2 Module milestone

```text
gf-wordbench validate --mode checkpoint --checkpoint <module>
```

### 72.3 Broad debugging

```text
gf-wordbench validate --mode diagnostic --diff-previous
```

### 72.4 Toolchain diagnosis

```text
gf-wordbench paths check
gf-wordbench gf check --strict
```

### 72.5 Scenario review

```text
gf-wordbench scenario run <scenario-id>
gf-wordbench gold diff <scenario-id>
```

### 72.6 Intentional gold change

```text
gf-wordbench gold update <scenario-id> --dry-run
gf-wordbench gold update <scenario-id>
gf-wordbench gold check <scenario-id>
```

### 72.7 Release candidate

```text
gf-wordbench project check --strict
gf-wordbench contracts check --strict
gf-wordbench gf check --strict
gf-wordbench release check
```

### 72.8 Historical verification

```text
gf-wordbench runs verify <run-id> --strict
gf-wordbench release verify <run-id>
```

### 72.9 Archive and clean

```text
gf-wordbench runs archive <run-id>
gf-wordbench runs clean --dry-run
gf-wordbench runs clean <run-id>
```

---

## 73. Windows examples

Use argument-list semantics; user shell quoting applies only to the CLI invocation.

```text
gf-wordbench ^
  --gf-exe "C:\Program Files\GF\gf.exe" ^
  --rgl-root "C:\mycode\gf-rgl\src" ^
  --out-root "C:\mycode\gf-runs" ^
  validate --mode release
```

PowerShell:

```text
gf-wordbench `
  --gf-exe 'C:\Program Files\GF\gf.exe' `
  --rgl-root 'C:\mycode\gf-rgl\src' `
  --out-root 'C:\mycode\gf-runs' `
  validate --mode release
```

GF Wordbench does not pass literal wrapper quote characters to the process API.

---

## 74. CI examples

### 74.1 Diagnostic CI

```text
gf-wordbench \
  --non-interactive \
  --gf-exe "$GF_EXE" \
  --rgl-root "$RGL_ROOT" \
  --out-root "$CI_ARTIFACTS/gf-wordbench" \
  validate --mode diagnostic
```

### 74.2 Release CI

```text
gf-wordbench \
  --non-interactive \
  --strict \
  --gf-exe "$GF_EXE" \
  --rgl-root "$RGL_ROOT" \
  --out-root "$CI_ARTIFACTS/gf-wordbench" \
  release check
```

CI should publish the run directory whether the result is `READY`, `NOT_READY`, or `ERROR`, when evidence exists.

Only a `READY` run may publish the PGF as final.

---

# Part XVI — Implementation and change control

## 75. Parser ownership

Exactly one CLI parser hierarchy owns command names and option definitions.

Recommended package boundary:

```text
app/cli/
```

or the existing canonical CLI module until refactored.

GUI code must not define a second semantic command parser.

---

## 76. Dispatch ownership

Commands dispatch to service-layer operations.

Examples:

```text
validate       → audit/release orchestrator
project check  → project validator
gf check       → compatibility service
gold check     → gold loader/comparator
runs verify    → run/manifest verifier
```

Commands should not contain domain logic beyond argument validation and presentation.

---

## 77. Tests

Recommended test structure:

```text
tests/cli/test_help.py
tests/cli/test_version_command.py
tests/cli/test_validate_commands.py
tests/cli/test_project_commands.py
tests/cli/test_gf_commands.py
tests/cli/test_scenario_commands.py
tests/cli/test_gold_commands.py
tests/cli/test_manifest_commands.py
tests/cli/test_run_commands.py
tests/cli/test_release_commands.py
tests/contracts/test_command_contract.py
tests/migrations/test_legacy_cli_aliases.py
```

### 77.1 Required cases

- every documented command appears in help;
- unknown command fails;
- missing required argument fails;
- incompatible selector fails;
- write command requires explicit intent;
- non-interactive command never prompts;
- mode aliases canonicalize;
- canonical outputs never emit legacy mode names;
- CLI/GUI resolve equivalent configuration;
- release alias and validate release produce identical service request;
- read-only commands do not modify files;
- run-writing commands write only under run root;
- gold update is the only normal gold writer;
- cleanup path safety;
- structured exit categories;
- paths containing spaces;
- Unicode arguments;
- Windows/POSIX path behavior.

---

## 78. Change policy

A command-contract change includes:

- adding/removing/renaming command;
- changing command hierarchy;
- changing required argument;
- changing option meaning;
- changing default mode;
- changing write safety;
- changing canonical alias;
- changing exit category;
- changing external GF request;
- changing report/artifact path printed for automation.

A coordinated change MUST update:

1. CLI parser;
2. service request model;
3. GUI when applicable;
4. state/config handling;
5. command reference;
6. CLI reference;
7. exit-code reference;
8. contract locks;
9. schemas when persisted behavior changes;
10. unit/contract/integration/migration tests;
11. changelog;
12. migration/deprecation notes.

---

## 79. Prohibited command behavior

The following are prohibited:

- a report command launching GF;
- a GUI widget bypassing command/service contracts;
- a read-only command rewriting project or run evidence;
- validation updating gold;
- release accepting `--no-compile`;
- release skipping required version probe;
- cleanup following unsafe paths;
- manifest verification rewriting hashes;
- project initialization overwriting an active project silently;
- legacy aliases appearing in canonical persisted output;
- hidden launcher-only options;
- command help disagreeing with parser behavior;
- logged GF command differing from executed arguments;
- shell command strings assembled from project text;
- zero GF exit code overriding failed scenario markers;
- one command reconstructing artifact paths when structured paths exist.

---

## 80. Final enforcement rule

The command surface is an operational contract.

Each command must have one meaning, one safety class, one service owner, and one result model.

> GF Wordbench commands express project intent; GF commands provide authoritative grammar execution; neither layer may silently assume the responsibilities of the other.

Canonical commands create reproducible requests, preserve evidence, respect project ownership, and make every write or destructive action explicit.
