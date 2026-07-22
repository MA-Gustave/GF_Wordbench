# GF Wordbench — Backward Compatibility

**Document ID:** `GF-WB-DEV-BACKWARD-COMPATIBILITY`  
**Status:** Normative development policy  
**Applies to:** GF Wordbench framework, persisted artifacts, public commands, project templates, active projects, and supported external-tool integrations  
**Canonical package:** `gf-wordbench`  
**Canonical CLI:** `gf-wordbench`  
**Initial stable compatibility line:** `1.x`  
**Owner:** GF Wordbench maintainers  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

This document defines what GF Wordbench promises to preserve across releases.

Backward compatibility is not one undifferentiated promise. GF Wordbench has several independently versioned surfaces:

- command-line syntax;
- process exit codes;
- Python entry points;
- shared result models;
- active-project configuration;
- application state;
- run summaries;
- manifests;
- scenario outputs and gold files;
- human-facing report structure;
- run-directory layout;
- project templates;
- external GF command contracts;
- GF project interfile contracts;
- Windows launchers;
- documented environment variables.

Each surface has a different consumer and a different safe migration path.

This policy prevents two opposite failures:

1. **silent breakage**, where existing projects or automation stop working without a migration path;
2. **permanent legacy accumulation**, where every historical implementation detail becomes frozen forever.

The governing principle is:

> Preserve documented contracts, migrate persisted meaning, deprecate deliberately, and keep private implementation details free to evolve.

---

## 2. Scope

This policy governs compatibility for:

```text
gf-wordbench command
public subcommands and options
process exit codes
documented environment variables
public Python entry points
shared serialized model fields
project/project.toml
.gf_wordbench_state.json
legacy .gf_audit_state.json
run_<id>/summary.json
run_<id>/manifest.json
scenario .out files
scenario .gold files
summary.md required headings
AI_READY.md required headings
top_errors.txt line format
run directory names and owned artifact paths
project template layout
GF executable invocation contracts
supported GF versions and capabilities
active-project contract migrations
```

It also governs compatibility shims used to import the earlier audit implementation.

---

## 3. Exclusions

The following are not backward-compatible public surfaces unless another contract explicitly says otherwise:

- private Python helpers;
- functions or classes whose names begin with `_`;
- local variable names;
- implementation-specific exception stack traces;
- internal log wording;
- console progress wording;
- GUI widget placement;
- GUI visual styling;
- Python object identity;
- dictionary key order in JSON;
- temporary files deleted before finalization;
- test-only fixtures not declared as compatibility fixtures;
- private module import paths;
- undocumented environment variables;
- source-code formatting;
- performance characteristics without an explicit performance contract;
- current implementation quirks contradicted by normative documentation.

An excluded detail becomes a compatibility surface when:

- it is documented as stable;
- another component depends on it;
- external automation consumes it;
- it is persisted and later read;
- a contract lock declares it;
- a migration registry lists it.

---

## 4. Normative terms

- **MUST**: mandatory for compatibility.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **CANONICAL**: form emitted by the current stable writer or interface.
- **LEGACY**: older supported input form not emitted by canonical writers.
- **COMPATIBLE CHANGE**: change that preserves documented meaning for supported consumers.
- **BREAKING CHANGE**: change requiring a major version, explicit migration, or both.
- **DEPRECATION**: supported feature scheduled for removal.
- **ALIAS**: accepted old name mapped to a canonical name without changing meaning.
- **MIGRATION**: explicit conversion from one documented representation to another.
- **SHIM**: temporary compatibility implementation that adapts an old interface.
- **SUPPORT WINDOW**: releases or schema versions that current readers still accept.
- **PUBLIC SURFACE**: documented contract used outside its owning implementation file.
- **LOSSLESS MIGRATION**: conversion preserving all required meaning.
- **LOSSY MIGRATION**: conversion where some meaning cannot be preserved and losses are reported.

---

## 5. Core compatibility rules

### 5.1 Canonical writers, tolerant readers

Current writers MUST emit only canonical forms.

Current readers SHOULD accept:

- the current canonical major version;
- supported minor versions of that major;
- the immediately previous canonical major when a tested migration exists;
- explicitly registered unversioned legacy forms during their support period.

Readers MUST NOT reinterpret unknown meaning silently.

### 5.2 One meaning per identifier

A command, field, enum value, contract ID, artifact name, or status string MUST NOT be reused for a different meaning.

Removed identifiers remain documented as retired when historical consumers may encounter them.

### 5.3 Explicit migration

A breaking persisted-format change requires:

- a new schema version;
- a reader or migrator;
- compatibility tests;
- loss reporting;
- release notes;
- an updated contract lock.

### 5.4 No legacy emission

Canonical writers MUST NOT emit legacy aliases merely because readers still accept them.

Examples:

```text
read mode=file
write mode=quick

read ai_brief_path
write artifacts.ai_ready

read sha1_short
write canonical SHA-256 fields
```

### 5.5 No silent fallback with changed semantics

A fallback is allowed only when it preserves documented meaning.

If an older GF version, schema, or command cannot provide equivalent semantics, GF Wordbench must:

- reject it;
- mark it unsupported;
- or continue with an explicit warning and reduced guarantee.

It must not call the result equivalent without evidence.

### 5.6 Compatibility is tested behavior

A compatibility promise without a test is incomplete.

Every supported alias, legacy reader, migration, or compatibility adapter must have a test fixture.

---

# 6. Versioning model

## 6.1 Framework version

GF Wordbench uses semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Example:

```text
1.4.2
```

### MAJOR

Increment for incompatible changes to one or more stable public surfaces when compatibility cannot be preserved through an ordinary alias or migration.

### MINOR

Increment for backward-compatible functionality, including:

- new optional fields;
- new optional commands;
- new optional report sections;
- expanded reader support;
- deprecated aliases;
- compatible GF capability support.

### PATCH

Increment for backward-compatible fixes, including:

- bug fixes;
- stricter validation of already invalid input;
- documentation corrections;
- security fixes preserving interfaces;
- deterministic-order fixes;
- diagnostic-parser fixes that do not redefine public status meaning.

## 6.2 Pre-1.0 behavior

Before the first stable `1.0.0` release, public surfaces may still change.

However, every persisted format and migration fixture must already be versioned.

Pre-release status does not permit silent data corruption.

## 6.3 Schema versions

Persisted schemas use:

```text
MAJOR.MINOR
```

Examples:

```text
gf-wordbench.project/1.0
gf-wordbench.run-summary/1.1
```

Patch-level implementation fixes do not require schema patch versions.

## 6.4 Contract versions

Contract locks may use:

```text
MAJOR.MINOR.PATCH
```

A contract version changes when the documented boundary changes, not for prose-only corrections.

## 6.5 CLI contract version

The CLI contract follows the framework major version unless a release explicitly documents a separate lifecycle.

---

# 7. Compatibility surfaces

| Surface | Canonical owner | Compatibility mechanism |
|---|---|---|
| CLI commands/options | `app/main_cli.py` | aliases, deprecation, major-version removal |
| Exit codes | CLI and exit-code reference | stable numeric meanings |
| Python entry points | owning modules | wrappers, adapters, major-version removal |
| Shared models | `app/models.py` | optional defaults, serializers, migrations |
| Project config | project schema/loader | schema versions and migrator |
| App state | state manager | legacy import, canonical rewrite |
| Run summary | JSON writer/reader | versioned schemas and migrations |
| Manifest | manifest writer/verifier | versioned schemas |
| Scenario output | scenario runner | normalization version |
| Gold files | project maintainers | explicit reviewed update |
| Human reports | report writers | soft-schema versions |
| Run layout | `RunPaths` owner | aliases/readers, major changes |
| External GF commands | command builders | version/capability adapters |
| Project template | initializer | template migration guidance |
| Project contracts | active project | project migration and validation |

---

# 8. Compatibility classes

Every public element should be classified as one of:

```text
stable
provisional
experimental
deprecated
retired
internal
```

## 8.1 Stable

A stable element follows this document’s compatibility rules.

## 8.2 Provisional

A provisional element is expected to become stable but may change before a declared release milestone.

Its limitations must be documented.

## 8.3 Experimental

An experimental element:

- is opt-in;
- may change in minor versions;
- must not be required for ordinary stable workflows;
- must be clearly labeled;
- must not silently create canonical persisted data without a schema.

## 8.4 Deprecated

A deprecated element remains supported temporarily.

It must have:

- a canonical replacement;
- a warning;
- a removal target;
- tests during the support period.

## 8.5 Retired

A retired element is no longer accepted by current interfaces.

Historical readers or migration tools may still recognize it.

## 8.6 Internal

An internal element has no compatibility promise.

---

# 9. Support windows

## 9.1 Framework releases

Recommended stable policy:

- current minor release line: fully supported;
- previous minor in the same major: security and critical compatibility fixes when practical;
- older minors: upgrade required;
- previous major: migration support only when explicitly documented.

## 9.2 Persisted schemas

Current readers SHOULD support:

```text
current major
immediately previous major when migration exists
registered unversioned GF Audit legacy forms
```

Current writers emit:

```text
latest supported canonical version only
```

## 9.3 CLI aliases

A deprecated stable CLI alias should remain for:

```text
at least one minor release
```

Recommended for widely used aliases:

```text
two minor releases or one major transition
```

## 9.4 Python APIs

A deprecated stable Python symbol should remain for at least one minor release unless:

- a critical security issue requires removal;
- keeping it would corrupt data;
- it was incorrectly documented as stable.

## 9.5 External GF versions

GF Wordbench maintains:

```text
minimum_supported_gf_version
tested_gf_versions
known_incompatible_gf_versions
```

Support is capability-based where possible.

## 9.6 Project templates

A project created by the previous stable minor should remain loadable by the current stable minor.

A project from an older schema may require explicit migration.

---

# 10. Deprecation lifecycle

Canonical lifecycle:

```text
stable
  -> deprecated
  -> retired
```

Optional earlier stages:

```text
experimental
  -> provisional
  -> stable
```

## 10.1 Introducing deprecation

A deprecation change must define:

```text
deprecated element
canonical replacement
first deprecated version
earliest removal version
warning behavior
migration instructions
tests
```

## 10.2 Warning requirements

Warnings must:

- identify the deprecated element;
- identify the replacement;
- avoid printing once per item in large loops;
- appear at most once per relevant invocation by default;
- remain visible unless normal warnings are explicitly suppressed.

Example:

```text
WARNING: --mode all is deprecated; use --mode diagnostic.
```

## 10.3 Canonical internal form

Aliases are normalized at the boundary.

Internal components receive only canonical values.

Example:

```text
CLI input: all
RunConfig.mode: diagnostic
summary.json: diagnostic
```

## 10.4 Removal

Before removal:

- update changelog;
- update migration documentation;
- remove canonical help listing;
- retain historical fixture coverage where migration still reads the old form;
- ensure errors identify the replacement when practical.

## 10.5 Security exception

A dangerous interface may be removed sooner.

The release must explain:

- security reason;
- affected versions;
- mitigation;
- replacement;
- migration impact.

---

# 11. Compatibility registry

The compatibility registry is maintained in documentation and tests.

Current initial registry:

| Legacy element | Canonical replacement | Compatibility policy |
|---|---|---|
| Package/project label `Grammatical_Framework_audit` | `GF Wordbench` | Historical reference only |
| CLI executable `gf-audit` | `gf-wordbench` | Temporary executable alias |
| `mode=file` | `mode=quick` | Read/CLI alias; never write |
| `mode=all` | `mode=diagnostic` | Read/CLI alias; never write |
| `--target-file` | `--target` | Deprecated CLI alias |
| `--skip-version-probe` | `--no-version-probe` | Deprecated CLI alias |
| `--emit-cpu-stats` | `--cpu-stats` | Deprecated CLI alias |
| `--timeout-sec` | `--compile-timeout` | Deprecated CLI alias |
| `--diff-previous` | `--compare-previous` | Deprecated CLI alias |
| `--scan-dir` | project source configuration | Migration-only override |
| `--scan-glob` | project source configuration | Migration-only override |
| `--include-regex` | project selection configuration | Migration-only override |
| `--exclude-regex` | project selection configuration | Migration-only override |
| `--gf-path` | project toolchain plus environment resolution | Migration-only override |
| `.gf_audit_state.json` | `.gf_wordbench_state.json` | Import and migrate |
| unversioned state | `gf-wordbench.app-state/1.0` | Read legacy; write canonical |
| flat `summary.json` | `gf-wordbench.run-summary/1.0` | Migrate |
| nested unversioned `summary.json` | `gf-wordbench.run-summary/1.0` | Migrate |
| `ai_brief_path` | `artifacts.ai_ready` | Read alias only |
| absolute `ai_ready_path` | run-relative `artifacts.ai_ready` | Convert when contained |
| `sha1_short` | SHA-256 fingerprint fields | Import only |
| total `ok` | `files_ok` | Rename during migration |
| total `fail` | `files_fail` | Rename during migration |
| top-error mapping | structured top-error array | Normalize |
| `DiffEntry.file_path` | `subject_kind + subject_id` | Migrate as file subject |
| diagnostic class `script_error` | `error_kind=SCRIPT` plus causal class | Migrate from evidence |
| diagnostic class `framework_error` | canonical technical error kind plus causal class | Migrate from evidence |
| `# GF Audit Summary` | `# GF Wordbench Audit Summary` | Human legacy only |
| language identity in GUI state | `project.toml` | Ignore/remove during migration |

Canonical writers must not emit any value in the legacy column.

---

# 12. Command-line compatibility

## 12.1 Stable command identity

Canonical command:

```text
gf-wordbench
```

Stable public subcommands:

```text
validate
project check
scenarios check
gold update
schemas check
reports check
```

Adding a new optional subcommand is normally backward-compatible.

Removing or reusing a stable subcommand is breaking.

## 12.2 Option compatibility

Compatible changes:

- add an optional flag with a safe default;
- add a repeatable optional selector;
- accept another path spelling;
- improve validation error wording;
- add a deprecated alias.

Breaking changes:

- remove a stable option without lifecycle;
- change an option’s meaning;
- change its value type;
- change default behavior materially;
- make a previously optional action destructive;
- permit an option in a mode where it weakens required guarantees;
- change path-base interpretation.

## 12.3 Boolean options

Boolean option pairs should use explicit positive/negative forms where state matters:

```text
--compare-previous
--no-compare-previous
```

Changing only the default may be breaking when behavior or generated artifacts change materially.

## 12.4 Positional arguments

Adding a required positional argument is breaking.

Adding an optional positional argument is discouraged because parsing may become ambiguous.

## 12.5 Help text

Help wording is not a machine API.

Command names, option names, accepted values, defaults, and exit meanings are contractual.

## 12.6 Automation

Automation must use:

- exit codes;
- `summary.json`;
- `manifest.json`;
- documented artifact paths.

Console prose is not stable machine output unless an explicit machine-output option is introduced.

---

# 13. Exit-code compatibility

Canonical codes:

```text
0 = command succeeded and required validation passed
1 = validation executed reliably but required validation failed
2 = usage, configuration, schema, or requested-contract error
3 = runtime, external-tool, I/O, timeout, cancellation, or integrity error
```

These numeric meanings are stable for the `1.x` line.

Compatible:

- classify a newly detected invalid argument as `2`;
- classify a new required validation failure as `1`;
- classify a newly detected runtime-integrity failure as `3`.

Breaking:

- reuse a code for a different category;
- return `0` for a condition previously defined as required failure;
- map runtime failure to validation failure without preserving distinction.

A future additional exit code requires:

- minor version at minimum;
- updated reference;
- unchanged meanings for existing codes;
- CI tests.

---

# 14. Python API compatibility

## 14.1 Stable entry points

The primary stable application entry point is:

```python
run_audit(
    run_config: RunConfig,
    run_paths: RunPaths | None = None,
) -> RunResult
```

Shared configuration builders and public report writers may also become stable when declared in the interfile lock.

## 14.2 Public versus internal

A Python symbol is stable only when:

- documented as public;
- exported through the owning module’s public surface;
- referenced by a contract lock;
- covered by compatibility tests.

Importability alone does not make a symbol public.

## 14.3 Compatible function changes

Normally compatible:

- add a keyword-only optional parameter with a safe default;
- broaden accepted path-like input without changing output;
- return a subtype preserving documented behavior;
- add a new public helper;
- improve validation of invalid input.

## 14.4 Breaking function changes

Breaking:

- rename a public function;
- remove a public parameter;
- make an optional parameter required;
- change positional parameter order;
- change return type or meaning;
- begin mutating inputs;
- change exception categories relied upon by callers;
- introduce hidden environment dependence.

## 14.5 Compatibility wrapper

A renamed function may retain a wrapper:

```python
def old_name(*args, **kwargs):
    warnings.warn(
        "old_name is deprecated; use new_name",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_name(*args, **kwargs)
```

The wrapper must preserve behavior during the deprecation period.

## 14.6 Dataclass construction

Adding a field is compatible only when:

- it has a safe default;
- it does not change existing field meaning;
- serializers handle it;
- readers tolerate absence in older data;
- mutable defaults use factories.

Reordering positional dataclass fields can break callers.

Stable models should favor keyword construction.

---

# 15. Shared result-model compatibility

## 15.1 Model surfaces

Key models include:

```text
RunConfig
RunPaths
ScanCounts
SourceFingerprint
CompileSummary
FileResult
ScenarioResult
DiffEntry
TopError
RunResult
```

## 15.2 Field stability

A stable field has:

- stable name;
- stable type;
- stable meaning;
- documented default when optional;
- centralized serialization.

## 15.3 Adding fields

A new optional field is compatible when:

- default preserves old behavior;
- canonical serializer includes it according to schema version;
- old summaries can be loaded without it;
- callers are not required to inspect it.

## 15.4 Removing or renaming fields

Requires:

- major model/schema change;
- migration;
- compatibility alias property or reader when practical;
- tests.

## 15.5 Enum values

Adding an enum value can break strict consumers.

Therefore:

- at least a minor version increment is required;
- strict readers reject unknown values;
- tolerant historical readers may preserve unknown values without reinterpretation;
- removing or redefining an enum value is breaking.

## 15.6 Redundant compatibility fields

Example:

```text
is_direct
```

may coexist with canonical:

```text
diagnostic_class
```

while older consumers depend on it.

During coexistence:

- both must remain coherent;
- the canonical field wins on conflicting legacy input;
- deprecation must be documented before removal.

---

# 16. `RunConfig` compatibility

## 16.1 Canonical modes

```text
quick
checkpoint
release
diagnostic
```

Legacy:

```text
file
all
```

is normalized at input.

## 16.2 Project-owned configuration

Language-specific settings move from generic framework defaults and old CLI options into:

```text
project/project.toml
```

This migration is compatible when:

- old input remains readable during the transition;
- canonical resolved `RunConfig` uses project values;
- required release constraints are not weakened;
- canonical outputs do not emit legacy settings.

## 16.3 New configuration fields

New optional fields need safe defaults.

New required fields require:

- project schema major version or documented migration;
- project-template update;
- active-project migration;
- clear error for unmigrated projects.

## 16.4 Hidden defaults

Changing a hidden default is potentially breaking.

Important resolved defaults must be documented or persisted.

---

# 17. `RunPaths` and directory-layout compatibility

## 17.1 Stable artifact names

Canonical:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
```

Changing these names is breaking unless:

- old readers discover aliases;
- a migration or compatibility symlink/copy policy exists;
- `RunPaths`, reports, manifest, GUI, CLI, and tests update together.

## 17.2 Stable directory roles

Canonical run roles:

```text
details/
raw/
raw/compile/
raw/scan/
raw/scenarios/
artifacts/
artifacts/gfo/
artifacts/out/
artifacts/pgf/
```

Adding an optional directory is compatible.

Changing ownership or path-base semantics is breaking.

## 17.3 Run directory naming

Canonical pattern:

```text
run_<run-id>
```

A collision suffix may be added without changing run identity semantics.

Readers must not derive all metadata from the directory name.

## 17.4 Legacy path aliases

`ai_brief_path` may remain a read-only compatibility alias for `ai_ready_path` in Python model loading.

Canonical paths and JSON use:

```text
AI_READY.md
artifacts.ai_ready
```

## 17.5 Absolute to relative paths

Canonical persisted run artifacts are run-relative where defined.

Legacy absolute paths may be converted only when containment is verified.

If conversion is impossible, migration records a loss or warning.

---

# 18. Project configuration compatibility

## 18.1 Canonical schema

```text
schema_id = gf-wordbench.project
schema_version = 1.0
```

## 18.2 Stable project identity

Fields defining identity are strongly compatible surfaces:

```text
project id
project name
language code
source root
module suffix when defined
entrypoints
checkpoints
required scenarios
release targets
```

Changing identity may require a project migration even when framework schema stays at the same major.

## 18.3 Compatible project changes

Usually compatible:

- add an optional scenario;
- add an optional documentation field;
- add an optional checkpoint;
- add an optional toolchain hint;
- add an optional release metadata field;
- expand source selection without changing existing identity meaning.

## 18.4 Breaking project changes

Examples:

- rename project ID;
- rename language code;
- change source-root base semantics;
- rename module suffix;
- remove required entrypoint;
- rename scenario IDs without mapping;
- change a required gold contract;
- change release artifact identity;
- make an optional field required.

## 18.5 Project migration

A project migration must coordinate:

```text
project.toml
GF source module names
imports
entrypoints
scenarios
gold files
project documentation
dependency map
status ledger
release evidence
```

Framework migration must not silently rewrite active project semantics during normal validation.

---

# 19. Application-state compatibility

## 19.1 Canonical state

```text
.gf_wordbench_state.json
gf-wordbench.app-state/1.0
```

## 19.2 Legacy state

```text
.gf_audit_state.json
```

may be imported during the migration period.

## 19.3 State purpose

State stores disposable UI convenience values.

It is not authoritative for:

- active language identity;
- project entrypoints;
- required scenarios;
- release rules;
- active execution objects.

## 19.4 Migration behavior

State migration should:

1. read legacy state without modifying it;
2. extract supported convenience values;
3. discard project identity fields moved to `project.toml`;
4. write canonical state atomically;
5. preserve a backup or source reference when appropriate;
6. report ignored fields.

## 19.5 Malformed state

Malformed state should be ignored or quarantined.

It must not prevent CLI validation or corrupt project configuration.

---

# 20. Run-summary compatibility

## 20.1 Canonical schema

```text
gf-wordbench.run-summary/1.x
```

## 20.2 Supported legacy forms

```text
unversioned flat GF Audit summary
unversioned nested GF Audit summary
```

## 20.3 Reader policy

The loader:

- detects canonical versus legacy form;
- validates required meaning;
- migrates into an in-memory canonical `RunResult`;
- records warnings and losses;
- does not rewrite the source automatically.

## 20.4 Writer policy

The current writer emits only the latest supported canonical schema.

## 20.5 Common migrations

```text
mode=file -> quick
mode=all -> diagnostic
ok -> files_ok
fail -> files_fail
ai_brief_path -> artifacts.ai_ready
top-error mapping -> top-error array
file-only DiffEntry -> generalized subject
absolute run paths -> run-relative paths
sha1_short -> imported legacy fingerprint evidence
```

## 20.6 Pre-scenario runs

Historical runs may lack:

```text
scenario_results
scenario totals
scenario artifacts
normalization version
```

Migration uses empty scenario collections and records that scenario data was unavailable.

It must not claim scenarios passed.

## 20.7 Missing required meaning

If a legacy status or identity cannot be recovered:

- preserve raw source;
- report a loss;
- mark affected data unknown or invalid;
- do not fabricate a canonical success.

---

# 21. Manifest compatibility

## 21.1 Canonical schema

```text
gf-wordbench.artifact-manifest/1.x
```

## 21.2 Addition of roles

Adding an optional manifest role is normally minor-compatible.

Strict consumers must still handle unknown roles according to schema policy.

## 21.3 Hash algorithm

Changing the canonical hash algorithm is a schema change.

During transition, entries may carry explicit:

```text
hash_algorithm
```

A verifier must not compare hashes using an assumed different algorithm.

## 21.4 Missing legacy manifest

Runs created before manifest support may remain readable.

They cannot be considered equivalent to strict manifest-verified release runs.

Reports should state:

```text
legacy run: manifest unavailable
```

## 21.5 Artifact identity

Changing artifact path or role meaning is breaking.

---

# 22. Scenario-output compatibility

## 22.1 Canonical output

Scenario normalized output has:

- explicit UTF-8;
- canonical LF;
- stable marker handling;
- normalization version;
- deterministic content where exact gold applies.

## 22.2 Normalization changes

A normalization change is compatible only when it cannot change existing comparison meaning.

If existing gold meaning may change, the change requires:

- normalization version increment;
- gold review;
- affected fixture update;
- migration/release note;
- compatibility tests.

## 22.3 Marker changes

Changing marker syntax is breaking for:

- scenario runner;
- `.gfs` scripts;
- normalized outputs;
- gold files;
- report interpretation.

A transition may support both old and new markers for one deprecation period.

Canonical scenarios emit only the new form.

## 22.4 Missing markers in historical output

Historical outputs without canonical markers may be readable only as raw legacy evidence.

They must not be upgraded to confirmed scenario success without equivalent completion proof.

---

# 23. Gold-file compatibility

## 23.1 Gold ownership

Gold files are reviewed project expectations.

They are not automatically rewritten by framework upgrades.

## 23.2 Compatible framework change

A framework change is gold-compatible when normalized semantically relevant output remains unchanged.

## 23.3 Gold-impacting change

A change that alters normalized output requires:

- explicit gold diff;
- human review;
- documented reason;
- version-control update;
- scenario validation;
- release review.

## 23.4 Project changes

Linguistic changes may legitimately update gold.

The commit or decision record should distinguish:

```text
expected linguistic change
normalization-only change
GF-version formatting change
bug fix
```

## 23.5 Legacy gold

A legacy gold file may be imported if:

- encoding is recoverable;
- normalization contract is known;
- marker/output semantics are equivalent.

Otherwise, regenerate through explicit reviewed `gold update`.

---

# 24. Human-report compatibility

Human reports use soft schemas.

## 24.1 `summary.md`

Canonical first heading:

```text
# GF Wordbench Audit Summary
```

Required sections:

```text
Run Summary
Outcome
File Results
Scenario Results
Regression Comparison
Artifacts
```

Compatible minor changes:

- add optional subsection;
- add optional table column;
- improve prose;
- add safe links.

Breaking:

- remove/rename required section;
- change its meaning;
- make Markdown machine-authoritative.

## 24.2 `AI_READY.md`

Canonical first heading:

```text
# AI Ready Packet
```

Required sections:

```text
Run Summary
Outcome
Diagnosis Snapshot
Failing Files
Failing Scenarios
Evidence
Artifacts
```

## 24.3 `top_errors.txt`

Canonical line:

```text
<count>\t<error-kind>\t<message>
```

Changing separators or field meaning is breaking.

## 24.4 Legacy report heading

```text
# GF Audit Summary
```

remains human-readable but is not emitted canonically.

No migrator should use Markdown as the primary source when `summary.json` exists.

---

# 25. Regression-comparison compatibility

## 25.1 Legacy model

```text
DiffEntry.file_path
```

## 25.2 Canonical model

```text
subject_kind
subject_id
previous_status
current_status
change_kind
message
```

## 25.3 Migration

Legacy entries become:

```text
subject_kind = file
subject_id = normalized file_path
```

## 25.4 Change kinds

Stable values:

```text
unchanged
improved
regressed
new
removed
```

Reusing one of these with a different meaning is breaking.

Adding another change kind requires schema and consumer review.

## 25.5 Historical comparison

A baseline with compatible subject identity and status meaning may be compared after migration.

An incompatible baseline is skipped or rejected explicitly.

---

# 26. Diagnostic compatibility

## 26.1 Canonical diagnostic classes

```text
ok
direct
downstream
ambiguous
noise
skipped
```

## 26.2 Canonical error kinds

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

## 26.3 Legacy classes

```text
script_error
framework_error
```

must not be emitted canonically.

Migration separates:

```text
technical nature -> error_kind
causal relationship -> diagnostic_class
```

## 26.4 Parser improvements

Improving diagnostic recognition is normally patch-compatible when:

- raw evidence remains unchanged;
- canonical status meanings remain unchanged;
- classification becomes more accurate under existing definitions.

Changing the definition of `direct` or `downstream` is a compatibility-sensitive behavioral change and requires documented review.

---

# 27. External GF compatibility

## 27.1 Version policy

GF Wordbench records and evaluates:

```text
minimum supported GF version
tested GF versions
known incompatible GF versions
```

## 27.2 Unknown newer version

Default non-strict behavior:

- warn;
- perform supported capability checks;
- continue when base contracts are satisfied;
- record exact version.

Strict/release policy may reject an unknown version.

## 27.3 Older unsupported version

Reject before language validation when required capabilities are absent.

## 27.4 Capability adapters

When GF command options vary, use:

- version-gated command building;
- capability probes;
- documented compatibility adapters.

Silent fallback to different behavior is prohibited.

## 27.5 Command changes

Changing any of these is compatibility-sensitive:

```text
executable resolution
argument order
working directory
GF search path
stdin behavior
timeout
stdout/stderr interpretation
expected artifact
```

The external-tool lock, tests, configuration, models, and docs update together.

## 27.6 Output changes

When a GF upgrade changes output:

1. preserve raw evidence;
2. compare semantic meaning;
3. update parser or normalization only for verified instability;
4. review gold;
5. update compatibility fixtures;
6. document supported-version impact.

---

# 28. Operating-system compatibility

## 28.1 Supported platforms

Each release documents tested operating systems.

A platform is supported only when:

- installation works;
- path handling works;
- process launching works;
- timeout termination works;
- reports and artifacts work;
- core tests pass.

## 28.2 Windows paths

Compatibility must cover:

- drive letters;
- spaces;
- Unicode;
- backslashes;
- CRLF input;
- `.exe`;
- `.bat` launcher;
- junctions and reparse points.

## 28.3 POSIX paths

Compatibility must cover:

- `/` paths;
- executable permissions;
- signals;
- symlinks;
- shell-independent process launch.

## 28.4 Persisted path form

Canonical project-relative and run-relative paths use `/`.

This provides cross-platform persisted identity.

## 28.5 Platform-specific feature

A platform-specific option may be added compatibly when:

- optional;
- clearly documented;
- absent on unsupported platforms;
- not required for canonical results.

---

# 29. Python-version compatibility

Each release documents:

```text
minimum supported Python
tested Python versions
unsupported Python versions
```

Dropping a supported Python minor requires at least:

- a minor GF Wordbench release;
- release-note notice;
- installation metadata update;
- CI update.

Dropping Python support may be treated as breaking for deployment even when application APIs are unchanged.

A major release is preferred when the impact is broad.

---

# 30. Dependency compatibility

## 30.1 Runtime dependencies

GF Wordbench should keep runtime dependencies minimal.

## 30.2 Compatible update

A dependency update is compatible when:

- documented behavior remains unchanged;
- supported Python/platform ranges remain valid;
- persisted output remains compatible;
- tests pass.

## 30.3 Breaking dependency update

Examples:

- drops supported Python;
- changes GUI platform support;
- changes TOML/JSON parsing semantics;
- changes subprocess behavior;
- changes persisted formatting;
- requires a new system library.

## 30.4 Locking

Development/release dependencies may be constrained for reproducibility.

Public library consumers should not be forced into unnecessarily exact transitive versions unless required.

---

# 31. Project-template compatibility

## 31.1 Template purpose

```text
templates/project/
```

defines the canonical starting structure for new active projects.

## 31.2 Framework versus existing project

Updating the template does not automatically update an existing active project.

Existing projects use:

- schema migration;
- project migration guidance;
- explicit copied files where needed.

## 31.3 Compatible template changes

Usually compatible:

- add optional documentation;
- add optional scenario example;
- add optional configuration field;
- improve comments.

## 31.4 Breaking template changes

Examples:

- move required directories;
- rename `project.toml`;
- change scenario/gold identity rules;
- change required entrypoint structure;
- require new project fields;
- change release artifact location.

A project migration checklist is required.

---

# 32. Active-project compatibility

The framework and active language project have separate compatibility responsibilities.

## 32.1 Framework responsibility

The framework preserves:

- configuration schema;
- execution contracts;
- result semantics;
- report schemas;
- migrations;
- project template expectations.

## 32.2 Project responsibility

The active project preserves or migrates:

- GF module names;
- imports;
- categories and lincats;
- public constructors and helpers;
- entrypoints;
- scenario IDs;
- gold expectations;
- release targets;
- project documentation contracts.

## 32.3 No hidden project migration

A framework upgrade must not silently rename GF modules or rewrite linguistic gold.

## 32.4 Project contract status

Project interfile contracts use statuses such as:

```text
active
experimental
deprecated
blocked
retired
```

A deprecated project symbol or module needs a consumer migration plan.

---

# 33. Migration architecture

## 33.1 Responsibilities

Recommended modules:

```text
app/schemas/versions.py
app/schemas/validators.py
app/schemas/migrations.py
```

or equivalent final owners.

## 33.2 Migration direction

Canonical migration direction:

```text
older -> current
```

Automatic downgrade is not required.

## 33.3 Stepwise migration

For multiple major versions:

```text
v1 -> v2 -> v3
```

is preferred over independent direct converters when stepwise logic is easier to test.

## 33.4 In-memory migration

Readers may migrate legacy data in memory for use.

They must not silently rewrite the source.

## 33.5 Explicit persisted migration

A separate explicit command may write the canonical destination.

The command must:

- preserve source;
- write atomically;
- validate destination;
- report warnings and losses;
- be idempotent.

---

# 34. Migration result

A migration should produce:

```json
{
  "source_schema": "gf-audit.run-summary-current",
  "source_version": "unversioned",
  "target_schema": "gf-wordbench.run-summary",
  "target_version": "1.0",
  "status": "migrated",
  "warnings": [],
  "losses": [],
  "source_path": "legacy/summary.json",
  "destination_path": "migrated/summary.json"
}
```

Canonical migration statuses:

```text
unchanged
migrated
migrated_with_warnings
failed
```

A migration must not return success when required meaning is lost.

---

# 35. Migration safety

A migrator must:

- read source without modifying it;
- validate source as far as possible;
- cap input size;
- use safe JSON/TOML/text parsing;
- avoid arbitrary object deserialization;
- preserve unknown data only under explicit policy;
- write a separate or atomic destination;
- verify output;
- avoid source-path traversal;
- never execute content during migration;
- avoid copying secrets into new artifacts.

---

# 36. Loss reporting

Potential losses include:

```text
absolute path could not be made project-relative
legacy status has no canonical equivalent
legacy timestamp lacks timezone
raw artifact is missing
sha1_short cannot become a real SHA-256
scenario data did not exist
ai_brief_path target is ambiguous
top-error count is malformed
duplicate file identity collapsed in legacy source
unknown module suffix
```

For every loss, record:

- field or subject;
- original value when safe;
- reason;
- canonical fallback;
- effect on reliability.

A fallback must not turn unknown validation into `OK`.

---

# 37. Idempotence

Running a migration twice on the same source must not:

- duplicate entries;
- change identity;
- keep incrementing versions;
- rewrite gold;
- create new warnings without reason;
- alter already canonical meaning.

Canonical input may produce:

```text
status = unchanged
```

---

# 38. Compatibility adapters

An adapter is appropriate when:

- the external GF command differs by supported version;
- an old CLI option maps exactly to a new one;
- a legacy field has one unambiguous canonical replacement;
- an older Python call can be wrapped safely.

An adapter is inappropriate when:

- semantics changed;
- required evidence is absent;
- security guarantees differ;
- data loss would be hidden;
- two old values map ambiguously to one new value.

In those cases, require explicit migration or reject the input.

---

# 39. Strict mode

Strict mode tightens compatibility handling.

It may reject:

- deprecated CLI aliases;
- unversioned persisted data;
- unknown schema fields where policy requires;
- unknown enum values;
- unknown newer GF versions;
- missing manifests;
- lossy migration;
- legacy absolute artifact paths;
- unsupported normalization versions.

Strict mode must not reinterpret legacy input differently.

It changes acceptance policy, not meaning.

---

# 40. Compatibility warnings

Warnings should use stable categories:

```text
DEPRECATED_CLI
LEGACY_SCHEMA
LOSSY_MIGRATION
UNKNOWN_NEWER_GF
UNTESTED_PLATFORM
LEGACY_PATH
NORMALIZATION_VERSION_CHANGED
MISSING_LEGACY_ARTIFACT
```

A structured warning should include:

```text
code
message
subject
replacement
removal_version when known
```

Human reports may render concise prose.

---

# 41. Compatibility errors

Errors include:

```text
unsupported schema major
removed CLI option
unknown required enum
incompatible explicit baseline
unsupported GF capability
unrecoverable project identity
unsafe legacy path
ambiguous migration
required field meaning lost
```

The error must identify:

- detected legacy/current form;
- expected form;
- supported migration command or documentation;
- whether the source was modified.

---

# 42. Compatibility and security

Backward compatibility must not preserve insecure behavior indefinitely.

Security overrides compatibility when an old interface permits:

- command injection;
- path traversal;
- unsafe deserialization;
- arbitrary system command execution;
- uncontrolled file deletion;
- secret disclosure;
- source/gold overwrite;
- unbounded external execution.

Response options:

1. disable immediately;
2. require explicit unsafe legacy mode temporarily;
3. provide a safe adapter;
4. migrate data without executing it;
5. release a security advisory.

The change must remain transparent.

---

# 43. Compatibility and correctness

A stricter rejection of input that was always invalid is normally compatible.

Examples:

- reject negative timeout;
- reject duplicate scenario ID;
- reject path escaping project root;
- reject downstream class without blockers;
- reject status `OK` with error kind `TIMEOUT`.

However, when users reasonably relied on permissive behavior, release notes and migration guidance are still required.

---

# 44. Compatibility and determinism

Fixing nondeterministic ordering is normally compatible when array order was already documented.

If consumers treated accidental order as meaningful, the canonical documented order still wins.

Order-sensitive persisted changes require schema review.

Canonical ordering includes:

```text
file_results -> normalized file path
scenario_results -> configured execution order
diff_entries -> severity then subject identity
top_errors -> descending count then message
manifest -> normalized artifact path
entrypoints/checkpoints -> declared order
```

---

# 45. Compatibility and reports

Reports may improve prose without a version change when:

- required headings remain;
- status meaning remains;
- machine data remains in `summary.json`;
- artifact links remain valid.

A prose change becomes compatibility-sensitive when:

- automation has been explicitly told to consume it;
- a required heading changes;
- line format is documented;
- another component parses it.

The preferred solution is to move machine needs into a structured schema rather than freeze prose.

---

# 46. Compatibility and GUI

GUI layout is not a stable API.

Stable GUI behavior includes:

- equivalent configuration to CLI;
- same validation semantics;
- same run artifacts;
- same project identity;
- same overall status;
- no hidden bypass of release rules.

State-file migrations protect preferences, not pixel layout.

---

# 47. Compatibility and launchers

Launchers are compatible when they continue to:

- invoke canonical CLI/application entry point;
- forward arguments;
- preserve working-directory independence;
- return the original process exit code;
- avoid hidden options.

Renaming a launcher may require a compatibility wrapper on platforms where users rely on shortcuts or scripts.

Launchers must not become independent implementations.

---

# 48. Compatibility test layers

Required categories:

```text
unit alias tests
legacy schema fixture tests
migration tests
current round-trip tests
cross-version reader tests
CLI help/exit tests
external GF adapter tests
project template migration tests
report soft-schema tests
Windows path compatibility tests
security regression tests
```

---

# 49. Legacy fixture policy

Legacy fixtures are allowed to contain old names and structures.

They must be clearly located:

```text
tests/fixtures/legacy/
```

Suggested structure:

```text
tests/fixtures/legacy/
├── state/
│   ├── gf_audit_state_valid.json
│   └── gf_audit_state_malformed.json
├── summaries/
│   ├── flat_valid.json
│   ├── nested_valid.json
│   ├── ai_brief_path.json
│   ├── mode_file.json
│   ├── mode_all.json
│   └── malformed.json
├── reports/
│   └── gf_audit_summary.md
└── projects/
    └── pre_project_toml/
```

Active framework tests must not otherwise hardcode historical language identifiers.

---

# 50. Round-trip tests

For every canonical persisted schema:

```text
construct canonical model
serialize
validate
load
compare semantic equality
serialize again
verify deterministic canonical output
```

Exact JSON key order is not semantically required.

Array order and path form are required where documented.

---

# 51. Migration tests

Each migration test should assert:

```text
source remains unchanged
target validates
canonical writer emits no legacy aliases
warnings are expected
losses are expected
migration is idempotent
paths are safe
result meaning is preserved
```

Lossy fixtures must verify that migration does not claim full success.

---

# 52. CLI compatibility tests

Required cases:

```text
gf-audit alias invokes canonical behavior
--mode file maps to quick
--mode all maps to diagnostic
--target-file maps to --target
--skip-version-probe maps to --no-version-probe
--emit-cpu-stats maps to --cpu-stats
--timeout-sec maps to compile timeout
--diff-previous maps to compare-previous
deprecated aliases warn once
canonical help prefers canonical names
canonical RunConfig contains no legacy mode
canonical summary contains no legacy mode
exit-code meanings remain stable
```

---

# 53. Model compatibility tests

Test:

- old constructor patterns still work during support window;
- new optional fields default safely;
- alias properties are read-only where appropriate;
- inconsistent redundant fields fail validation;
- serialization centralization;
- no dynamic undocumented attributes;
- unknown enum behavior;
- `ScenarioResult` absence in historical summaries;
- generalized `DiffEntry` migration.

---

# 54. External-tool compatibility tests

For each supported GF capability:

- known supported version;
- minimum supported version;
- below-minimum version;
- unknown newer version;
- missing option;
- changed stdout/stderr placement;
- paths with spaces;
- Windows executable;
- timeout;
- expected artifact missing;
- capability adapter selection.

Real-GF integration tests should be version-labeled.

---

# 55. Report compatibility tests

Verify:

```text
summary.md canonical heading
summary.md required sections
AI_READY.md canonical heading
AI_READY.md required sections
top_errors.txt tabs and ordering
legacy report not used as machine truth
optional new section does not break checker
required-heading change requires soft-schema major
```

---

# 56. Compatibility release gate

Before a stable release:

```text
[ ] canonical writers emit no legacy aliases
[ ] current schemas validate
[ ] previous supported schemas load
[ ] registered unversioned legacy summaries load
[ ] migration losses are explicit
[ ] deprecated CLI aliases behave as documented
[ ] canonical CLI help is current
[ ] exit codes remain stable
[ ] project template is current
[ ] previous stable project fixture loads
[ ] run-summary round trip passes
[ ] manifest verification passes
[ ] scenario normalization compatibility passes
[ ] gold impact reviewed
[ ] tested GF versions pass
[ ] Windows compatibility passes
[ ] changelog includes deprecations
[ ] removal targets are documented
[ ] contract locks are updated
```

A failed required compatibility test blocks release unless the release is an intentional major break with complete migration guidance.

---

# 57. Breaking-change procedure

A proposed breaking change must document:

```text
Affected surface:
Current contract:
New contract:
Why compatibility cannot be preserved:
Affected versions:
Affected projects:
Affected artifacts:
Security impact:
Data-loss risk:
Migration path:
Deprecation period:
Removal release:
Tests:
Rollback:
```

Required coordinated updates:

```text
implementation
all consumers
schema version
migrator
contract locks
CLI/GUI
project template
reports
tests
fixtures
release notes
migration guide
changelog
```

---

# 58. Major-release requirements

A major release must provide:

- compatibility summary;
- removed-feature list;
- schema migration table;
- CLI migration table;
- project migration checklist;
- supported GF/Python/platform matrix;
- known non-migratable cases;
- explicit backup guidance;
- release-validation evidence.

A major release must not simply reject all earlier data without documenting why migration is impossible.

---

# 59. Minor-release requirements

A minor release may add:

- optional model fields;
- optional report sections;
- optional commands;
- supported GF versions;
- deprecation warnings;
- compatible readers;
- new optional scenario capabilities.

It must not silently:

- change status meaning;
- change path bases;
- remove accepted stable input;
- alter required gold semantics;
- change exit-code meanings;
- bypass project configuration.

---

# 60. Patch-release requirements

A patch release may:

- fix parsing;
- correct migration bug;
- fix incorrect alias mapping;
- improve deterministic order;
- fix report escaping;
- fix path handling;
- fix timeout handling;
- close a security issue.

It should avoid introducing new public features.

A security patch may intentionally reject dangerous previously accepted input.

---

# 61. Rollback considerations

A migration should preserve enough source evidence to allow rollback.

Recommended:

- keep original file;
- write canonical destination separately or atomically with backup;
- record source schema;
- record target schema;
- record tool version;
- avoid deleting legacy runs;
- do not overwrite gold without explicit workflow.

Rollback does not guarantee that a newer project can run on an older framework when new required features were introduced.

---

# 62. Backup guidance

Before a major migration, back up:

```text
project/
project.toml
validation scenarios
gold files
contract locks
state file when preferences matter
selected release runs
manifested artifacts
```

Generated diagnostic runs may be recreated, but release evidence may need retention.

---

# 63. Removal of compatibility code

Compatibility code should be removed when:

- support window ended;
- replacement is stable;
- migration documentation exists;
- usage is no longer required by supported fixtures;
- security impact is acceptable;
- next major release permits removal.

Before removal:

- keep historical migration fixtures when useful;
- remove alias from help earlier than parser acceptance if lifecycle says so;
- update changelog;
- test clear rejection message.

Compatibility code must not remain indefinitely without an owner.

---

# 64. Avoiding compatibility complexity

Backward compatibility should not create a second permanent architecture.

Use these limits:

1. Normalize aliases immediately at boundaries.
2. Keep one canonical in-memory model.
3. Keep one canonical writer per artifact.
4. Keep legacy readers isolated.
5. Do not spread legacy conditions through core stages.
6. Do not preserve unsafe behavior.
7. Do not support undocumented historical quirks.
8. Do not add a migration framework more complex than the schemas require.
9. Remove shims on schedule.
10. Prefer explicit failure over ambiguous automatic conversion.

Recommended layering:

```text
legacy input
    -> detector
    -> legacy reader
    -> migration adapter
    -> canonical model
    -> ordinary current system
```

Not:

```text
legacy condition inside every compiler, classifier, report, GUI, and command
```

---

# 65. Compatibility ownership

| Domain | Owner |
|---|---|
| Framework version | package metadata/release owner |
| CLI compatibility | `app/main_cli.py` and CLI docs |
| Python API compatibility | owning module and interfile lock |
| Model compatibility | `app/models.py` and schema layer |
| Project config | project loader and project schema |
| State migration | state manager |
| Summary migration | summary loader/migrator |
| Manifest compatibility | manifest writer/verifier |
| Scenario normalization | scenario runner/normalizer |
| Gold compatibility | active-project maintainers |
| GF adapter | command builder/process integration |
| Report soft schemas | report writers |
| Project migration | active project owner |
| Deprecation schedule | release owner |

No reader may rewrite an artifact it does not own.

---

# 66. Documentation requirements

Every deprecated or migrated surface must appear in at least one appropriate document:

```text
CHANGELOG.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/usage/CLI_REFERENCE.md
docs/reference/SCHEMA_INDEX.md
docs/reference/STATUS_VALUES.md
relevant contract lock
```

Do not duplicate full rules everywhere.

This document owns general compatibility policy.

Specific references own exact syntax and fields.

---

# 67. Changelog requirements

Changelog sections should include:

```text
Added
Changed
Deprecated
Removed
Fixed
Security
Migration
```

A compatibility-sensitive entry identifies:

- old form;
- new form;
- first affected release;
- action required;
- removal release where applicable.

---

# 68. Compatibility matrix

A release should publish a concise matrix:

| Domain | Supported |
|---|---|
| GF Wordbench | current release line |
| Python | declared versions |
| GF | minimum/tested range |
| Project schema | current major plus supported previous |
| App-state schema | current plus registered legacy import |
| Run-summary schema | current plus supported previous/legacy |
| Manifest schema | current plus supported previous where applicable |
| OS | tested platforms |
| CLI aliases | active deprecation set |

The matrix records actual tested support.

It must not claim untested combinations as fully supported.

---

# 69. Known incompatible conditions

Examples that may require rejection:

```text
project schema newer than reader major
run summary with redefined status meaning
unknown required enum in strict mode
GF below minimum supported capability
gold normalization version with no adapter
project identity migration with ambiguous module suffix
manifest hash algorithm unknown to verifier
unsafe legacy absolute path escaping approved root
```

The error should remain specific.

---

# 70. Compatibility diagnostics

Suggested command:

```text
gf-wordbench schemas check <path>
```

It reports:

```text
canonical and valid
supported legacy
migration recommended
migration required
unsupported newer schema
invalid
```

A future aggregate command may be:

```text
gf-wordbench compatibility check
```

It is unnecessary until multiple compatibility checks cannot be expressed through existing commands.

Avoid adding it merely for symmetry.

---

# 71. Example: legacy CLI migration

Input:

```text
gf-audit --mode file --target-file project/src/NounFre.gf --timeout-sec 60
```

Canonical interpretation:

```text
gf-wordbench validate
--mode quick
--target project/src/NounFre.gf
--compile-timeout 60
```

Behavior:

- warn for legacy executable;
- warn for each unique deprecated option category;
- build canonical `RunConfig`;
- persist mode `quick`;
- persist operation-specific timeout;
- produce canonical report names.

---

# 72. Example: legacy summary migration

Legacy:

```json
{
  "mode": "all",
  "ok": 10,
  "fail": 2,
  "ai_brief_path": "C:\\runs\\run_1\\AI_READY.md",
  "top_errors": {
    "type mismatch": 2
  }
}
```

Canonical in-memory result:

```json
{
  "metadata": {
    "mode": "diagnostic"
  },
  "totals": {
    "files_ok": 10,
    "files_fail": 2
  },
  "artifacts": {
    "ai_ready": "AI_READY.md"
  },
  "top_errors": [
    {
      "error_kind": "OTHER",
      "message": "type mismatch",
      "count": 2
    }
  ]
}
```

Warnings:

```text
legacy unversioned summary
mode alias migrated
absolute artifact path converted
top-error kind unavailable; defaulted to OTHER
scenario data unavailable
```

---

# 73. Example: non-migratable fingerprint

Legacy:

```json
{
  "sha1_short": "a1b2c3d4"
}
```

Canonical SHA-256 cannot be reconstructed from a truncated SHA-1.

Correct migration:

```text
preserve sha1_short as legacy evidence
leave canonical SHA-256 absent or unknown
record loss
```

Incorrect migration:

```text
copy a1b2c3d4 into sha256
```

---

# 74. Example: diagnostic-class migration

Legacy:

```json
{
  "diagnostic_class": "script_error",
  "error_kind": "SCRIPT"
}
```

Canonical result depends on evidence:

```text
error_kind = SCRIPT
diagnostic_class = direct
```

when the current operation itself is the supported technical root.

Or:

```text
error_kind = SCRIPT
diagnostic_class = ambiguous
```

when causality cannot be recovered.

The migrator must not always choose `direct` without evidence.

---

# 75. Example: project identity change

Old:

```text
project id = sqi
module suffix = Sqi
```

New:

```text
project id = alb
module suffix = Alb
```

This is not a simple framework alias.

It requires project migration across:

```text
project.toml
GF filenames
module declarations
imports
entrypoints
scenarios
gold files
dependency map
documentation
release artifacts
```

The old ID may remain as migration metadata, not active identity.

---

# 76. Example: GF option compatibility

Suppose one tested GF version supports an option and an older supported version does not.

Allowed:

```text
capability probe
select documented equivalent command
record exact command and version
```

Not allowed:

```text
silently omit the option and claim identical validation
```

When no equivalent exists:

```text
reject that operation for the older GF version
```

---

# 77. Anti-drift indicators

Compatibility drift exists when:

- canonical writers emit legacy names;
- aliases survive past the boundary into core models;
- one reader migrates a field differently from another;
- CLI and GUI interpret old state differently;
- schema changes without version increment;
- a required field is added without migration;
- unknown enum becomes `OK`;
- Markdown becomes a migration source;
- a legacy absolute path is trusted without containment;
- `sha1_short` is mislabeled SHA-256;
- new GF behavior silently changes gold meaning;
- a deprecated option disappears without notice;
- exit-code meanings change;
- project template changes but migration docs do not;
- old-language identifiers appear in active framework defaults;
- compatibility branches spread into compiler/report stages;
- a migrator modifies its source;
- a migration loses data without reporting it;
- a strict reader silently accepts unknown meaning;
- a compatibility test fixture is removed before support ends.

Any indicator requires compatibility review.

---

# 78. Change-control template

Every compatibility-sensitive change should answer:

```text
Surface:
Current version:
Target version:
Current behavior:
New behavior:
Compatible or breaking:
Legacy input affected:
Canonical output affected:
Alias or adapter:
Migration:
Warnings:
Losses:
Removal target:
Security impact:
Tests:
Documentation:
```

---

# 79. Review checklist

```text
[ ] public surface identified
[ ] owner identified
[ ] current consumers identified
[ ] persisted impact reviewed
[ ] CLI impact reviewed
[ ] GUI impact reviewed
[ ] Python API impact reviewed
[ ] GF version impact reviewed
[ ] project-template impact reviewed
[ ] active-project impact reviewed
[ ] security impact reviewed
[ ] compatible default selected
[ ] schema version updated when needed
[ ] migrator implemented when needed
[ ] canonical writer emits only canonical form
[ ] legacy reader isolated
[ ] warnings implemented
[ ] removal target documented
[ ] tests added
[ ] fixtures added
[ ] changelog updated
[ ] contract locks updated
```

---

# 80. Implementation completion checklist

Backward compatibility is implemented adequately when:

```text
[ ] framework uses semantic versioning
[ ] persisted schemas have explicit IDs and versions
[ ] canonical writers emit no legacy aliases
[ ] current readers load the current schema major
[ ] supported previous major migration exists where promised
[ ] registered GF Audit legacy state loads
[ ] registered flat summary loads
[ ] registered nested summary loads
[ ] file/all modes normalize to quick/diagnostic
[ ] ai_brief_path migration is tested
[ ] absolute artifact-path conversion is contained
[ ] sha1_short is never mislabeled SHA-256
[ ] old top-error mapping normalizes
[ ] old DiffEntry file path normalizes
[ ] legacy diagnostic classes migrate safely
[ ] scenario absence in historical runs is explicit
[ ] CLI aliases warn and normalize
[ ] overall exit-code meanings are stable
[ ] project schema migration is explicit
[ ] state does not own active project identity
[ ] report soft schemas are tested
[ ] normalization versions are enforced
[ ] gold updates remain explicit
[ ] GF capability adapters are tested
[ ] strict mode rejects unsupported meaning
[ ] migrators are read-only on source
[ ] migrations are idempotent
[ ] warnings and losses are structured
[ ] previous stable project fixture loads
[ ] Windows paths and launchers remain compatible
[ ] security fixes can override unsafe compatibility
[ ] compatibility shims have removal targets
[ ] release gate passes
```

---

# 81. Related documents

```text
CHANGELOG.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/release/VERSIONING_POLICY.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/release/RELEASE_PROCESS.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/SUMMARY_MARKDOWN_REFERENCE.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/usage/CLI_REFERENCE.md
docs/reference/EXIT_CODES.md
docs/reference/SCHEMA_INDEX.md
docs/reference/STATUS_VALUES.md
project/docs/INTERFILE_CONTRACT_LOCK.md
SECURITY.md
```

---

# 82. Final rule

GF Wordbench keeps one current architecture and explicit adapters at its boundaries.

Therefore:

> Accept documented legacy inputs only through isolated, tested readers or aliases; convert them to one canonical model; emit only current versioned formats; report every ambiguity or loss; and remove compatibility code on a declared schedule instead of allowing legacy behavior to spread through the system.
