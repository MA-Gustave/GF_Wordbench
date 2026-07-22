# GF Wordbench — Migration and Deprecation

**Document ID:** `GF-WB-RELEASE-MIGRATION-DEPRECATION`  
**Status:** Normative release and compatibility policy  
**Applies to:** Package behavior, public Python contracts, CLI and GUI surfaces, persisted schemas, project templates, active-language projects, GF module contracts, scenarios, gold files, reports, artifacts, external-tool integrations, and legacy `gf-audit` data  
**Primary owners:** GF Wordbench maintainers and the owner of each migrated contract  
**Target architecture:** Final GF Wordbench architecture  
**Policy version:** `1.0.0`  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines how GF Wordbench changes a supported contract without losing data, silently changing meaning, or leaving providers and consumers on incompatible versions.

It governs:

- migration from `gf-audit` to GF Wordbench;
- migration between persisted-schema versions;
- migration of active language projects;
- migration between project-template versions;
- migration of Python APIs and component contracts;
- migration of CLI commands and options;
- migration of external GF invocation contracts;
- migration of validation modes;
- migration of scenarios and gold files;
- migration of report and artifact layouts;
- deprecation warnings;
- compatibility windows;
- removal and retirement;
- rollback and recovery;
- migration evidence and tests.

The governing rule is:

> A replacement is not complete merely because new code exists. It is complete when supported users, projects, readers, writers, scenarios, and automation have a safe and documented path from the old contract to the new contract.

---

## 2. Related normative documents

This policy must remain consistent with:

```text
CHANGELOG.md
CONTRIBUTING.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/release/VERSIONING_POLICY.md
docs/release/RELEASE_PROCESS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/reference/SCHEMA_INDEX.md
docs/reference/STATUS_VALUES.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/DECISION_LOG.md
project/docs/STATUS_LEDGER.md
project/docs/RELEASE_CRITERIA.md
templates/project/project.toml
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Authority boundaries:

| Subject | Authoritative owner |
|---|---|
| Version increment | `VERSIONING_POLICY.md` |
| Python component boundary | framework interfile lock |
| External executable boundary | external-tool lock |
| Persisted field and migration | persisted-schema lock |
| Active GF project boundary | project interfile lock |
| Gold update procedure | `UPDATING_GOLD_FILES.md` |
| Release execution | `RELEASE_PROCESS.md` |
| Migration and deprecation lifecycle | this document |

When this document conflicts with a lock, the lock remains authoritative for its contract surface.

The conflict must be corrected through one coordinated change.

---

# 3. Core principles

GF Wordbench migrations must preserve these principles:

1. **No implicit destructive migration.**
2. **Read old, write current.**
3. **The source remains recoverable.**
4. **Meaning is preserved or loss is reported.**
5. **Migration is version-aware.**
6. **Migration is idempotent.**
7. **Canonical writers emit no legacy aliases.**
8. **Every deprecated item has a replacement or a retirement reason.**
9. **Every removal has a support-window decision.**
10. **Every contract change updates providers and consumers together.**
11. **Project migrations include scenarios, golds, documentation, and release evidence.**
12. **Opening a file or project does not authorize rewriting it.**
13. **Warnings are visible but do not masquerade as validation failures.**
14. **Migration failures preserve the last valid source and destination.**
15. **Historical identifiers are never reused for unrelated meaning.**

---

# 4. Normative terms

- **CURRENT**: latest canonical supported form emitted by current writers.
- **LEGACY**: older supported or recognized form accepted only for compatibility.
- **SOURCE**: original asset supplied to a migration.
- **DESTINATION**: canonical asset produced by a migration.
- **MIGRATOR**: component that converts a source contract into a target contract.
- **ADAPTER**: temporary runtime compatibility layer between old and new contracts.
- **ALIAS**: old name accepted and mapped to a canonical name.
- **DEPRECATED**: supported temporarily but scheduled for removal.
- **RETIRED**: no longer active; identity remains reserved.
- **REMOVED**: implementation support no longer exists in the current release line.
- **LOSS**: meaning or evidence that cannot be preserved exactly.
- **WARNING**: recoverable migration concern not preventing a valid destination.
- **BLOCKER**: condition preventing safe migration.
- **IN-PLACE MIGRATION**: explicit replacement of an asset at its canonical path.
- **READ MIGRATION**: in-memory conversion performed while loading, without rewriting the source.
- **WRITE MIGRATION**: explicit creation of a canonical destination.
- **ROLLBACK**: restoration of the pre-migration valid state.
- **COMPATIBILITY WINDOW**: period during which old behavior remains readable or callable.
- **DUAL-READ**: reader accepts old and new forms.
- **DUAL-WRITE**: writer emits old and new forms.
- **CANONICAL-ONLY WRITE**: writer emits only the current form.

GF Wordbench normally permits dual-read but prohibits dual-write.

---

# 5. Migration categories

Every migration must be classified.

Canonical categories:

```text
read-only compatibility
explicit persisted migration
public API migration
CLI migration
GUI-state migration
project schema migration
project-template migration
active-language project migration
GF module contract migration
scenario migration
gold migration
normalization migration
report/artifact migration
external-tool contract migration
platform/environment migration
retirement cleanup
```

The category determines owners, warnings, support window, and required tests.

---

## 5.1 Read-only compatibility

A reader accepts a legacy form and converts it into a current in-memory model.

Example:

```text
legacy summary.json
→ current RunResult-compatible model
```

Rules:

- source is not modified;
- canonical destination is not written automatically;
- warnings and losses are retained;
- the reader does not emit legacy fields later;
- unsupported meaning is not guessed.

---

## 5.2 Explicit persisted migration

A user or release operation creates a canonical file from a legacy file.

Example:

```text
.gf_audit_state.json
→ .gf_wordbench_state.json
```

Rules:

- operation is explicit;
- source is preserved;
- destination is written atomically;
- post-write validation is mandatory;
- source removal is a separate decision.

---

## 5.3 Runtime API adapter

An adapter allows old callers to use a new provider temporarily.

Example:

```python
def legacy_compile_file(...):
    warnings.warn(...)
    return compile_file(new_request)
```

Rules:

- one-directional delegation;
- no duplicate implementation;
- warning identifies replacement;
- removal release is documented;
- tests prove old and new paths agree.

---

## 5.4 Project migration

A project migration changes one or more of:

```text
project schema
source location
language identity
module suffix
entrypoints
checkpoints
scenario registry
gold ownership
release targets
project documentation
```

It must update the complete project contract network.

---

## 5.5 Semantic migration

A semantic migration changes meaning rather than only syntax.

Examples:

```text
status meaning
path-base meaning
normalization meaning
lincat record shape
scenario assertion semantics
release-gate semantics
```

Semantic migrations require explicit major-version and coordinated consumer review.

They must never be treated as simple field renames.

---

# 6. Migration lifecycle

The standard lifecycle is:

```text
1. discover
2. classify
3. inventory
4. design target
5. define compatibility window
6. implement current provider/writer
7. implement reader or adapter
8. implement explicit migrator
9. add warnings
10. add fixtures and tests
11. publish deprecation
12. migrate supported assets
13. verify release evidence
14. remove legacy writer/caller
15. retire identifier
16. remove reader/adapter after support window
```

Not every migration requires every phase.

Persisted, public, or project-level migrations normally do.

---

# 7. Migration proposal

A migration proposal must answer:

```text
Migration ID:
Category:
Owner:
Source contract:
Source version:
Target contract:
Target version:
Reason:
Affected providers:
Affected consumers:
Canonical writer:
Legacy readers:
Migration command or operation:
Compatibility window:
Warnings:
Losses:
Security:
Rollback:
Tests:
Removal release:
Documentation:
```

Significant architectural migrations should have an ADR.

---

# 8. Migration identifiers

Recommended format:

```text
MIG-<DOMAIN>-<NUMBER>
```

Domains:

```text
APP
STATE
SCHEMA
SUMMARY
MANIFEST
PROJECT
TEMPLATE
API
CLI
GUI
MODE
GF
SCENARIO
GOLD
NORMALIZATION
REPORT
ARTIFACT
PLATFORM
```

Examples:

```text
MIG-STATE-001
MIG-SUMMARY-001
MIG-MODE-001
MIG-PROJECT-002
```

Rules:

- IDs are stable;
- IDs are never reused;
- completed migrations remain documented;
- retired migration code may be removed while the migration record remains.

---

# 9. Migration registry

GF Wordbench should maintain a migration registry in code or documentation.

Minimum fields:

| Field | Meaning |
|---|---|
| Migration ID | Stable identity |
| Source | Old schema, contract, command, or project form |
| Target | Canonical replacement |
| Introduced | First package/project release supporting migration |
| Deprecated | First release warning about old form |
| Removal | Earliest release allowed to remove support |
| Migrator | Owning component |
| Status | Planned, active, complete, retired |
| Loss policy | None, warning, or blocker |
| Tests | Fixture and contract evidence |

The registry may initially live in this document and schema locks.

A machine-readable registry requires its own schema before persistence.

---

# 10. Compatibility states

Supported states:

```text
experimental
active
deprecated
retired
removed
```

Project contracts may additionally use:

```text
blocked
```

Meaning:

| State | Meaning |
|---|---|
| `experimental` | No stable compatibility guarantee |
| `active` | Current supported contract |
| `deprecated` | Supported temporarily; replacement available |
| `blocked` | Intended project contract cannot currently be satisfied |
| `retired` | No longer active; identity reserved |
| `removed` | Implementation no longer accepts or exposes it |

`retired` is a documentation/registry state.

`removed` describes implementation availability.

A retired contract ID must not disappear from historical records.

---

# 11. Deprecation prerequisites

An item may be deprecated only when at least one condition applies:

```text
a better replacement exists
the contract is unsafe
the contract is incorrect
the feature is unmaintainable
the upstream tool no longer supports it
the behavior duplicates another owner
the format prevents future compatibility
the project contract has been redesigned deliberately
```

A normal deprecation should have:

- replacement;
- migration instructions;
- first deprecated version;
- earliest removal version;
- warning channel;
- tests;
- ownership.

A feature may be retired without replacement only when its purpose is no longer valid.

The reason must be explicit.

---

# 12. Deprecation support windows

After package `1.0.0`, the default minimum support window is:

```text
at least one package minor release
```

Prefer:

```text
two minor releases
```

for:

```text
persisted fields
widely used CLI options
project schemas
project-template requirements
public Python APIs
automation-consumed artifacts
```

A package major transition may remove deprecated behavior after the documented window.

Before package `1.0.0`:

- deprecations remain documented;
- migration remains required;
- removal may occur in the next `0.MINOR`;
- no silent removal is permitted.

Exceptions are allowed for:

```text
security
data corruption
unsafe execution
false success
legal or licensing requirement
upstream removal making support impossible
```

Exceptions must be documented in release notes.

---

# 13. Deprecation warnings

A warning must state:

```text
deprecated item
replacement
first deprecated version
earliest removal version when known
migration action
```

Example:

```text
mode 'file' is deprecated; use 'quick'.
Legacy reading remains supported through the migration window.
Canonical writers emit only 'quick'.
```

Warnings should be:

- emitted once per relevant invocation when practical;
- visible in CLI stderr;
- visible in GUI warning areas;
- included in migration results;
- testable;
- non-secret;
- non-fatal unless the old behavior is unsafe.

A deprecation warning does not change validation status.

---

# 14. Warning channels

| Surface | Warning channel |
|---|---|
| CLI option or command | stderr |
| GUI behavior | warning banner/dialog |
| Python API | typed warning, normally `DeprecationWarning` or project-defined warning |
| Project load | project diagnostics |
| Schema read | migration warnings |
| Summary migration | migration result |
| External tool | compatibility warning |
| Scenario/gold | validation or migration report |
| Release | changelog and release notes |

Warnings must not exist only in ephemeral debug logs when user action is required.

---

# 15. Canonical writer policy

Canonical writers emit only current forms.

They must not emit:

```text
legacy aliases
deprecated field names
old mode names
old absolute-path forms
old fingerprint forms
unversioned schemas
old report identities
```

Legacy values may be accepted by readers during the support window.

This is the central asymmetry:

```text
read old and current
write current only
```

Dual-write is prohibited by default because it creates ambiguous ownership and inconsistent consumers.

---

# 16. Dual-write exception

Dual-write may be permitted only when:

- an external consumer cannot migrate atomically;
- both outputs have distinct canonical paths;
- one output is explicitly transitional;
- reconciliation is deterministic;
- removal date exists;
- tests prove equivalent meaning;
- the schema and artifact locks document both outputs.

Dual-write must not place two names for the same field in one canonical object.

A transitional export is preferable to polluting the canonical writer.

---

# 17. Read migration versus write migration

## 17.1 Read migration

```text
legacy bytes
→ legacy parser
→ migration adapter
→ current in-memory model
```

No source modification occurs.

Use for:

```text
historical run viewing
previous-run comparison
legacy state import preview
project migration planning
```

## 17.2 Write migration

```text
legacy source
→ parse and validate
→ current model
→ canonical serialization
→ temporary destination
→ validation
→ atomic replacement or new file
```

Write migration requires explicit authorization.

## 17.3 Prohibited behavior

Opening a project or run must not:

- rewrite `project.toml`;
- replace a gold;
- update a summary;
- delete legacy state;
- rename scenarios;
- move source files.

The application may propose migration and show a plan.

---

# 18. Migration result model

Recommended result:

```python
@dataclass(frozen=True, slots=True)
class MigrationResult:
    migration_id: str
    source_schema: str
    source_version: str
    target_schema: str
    target_version: str
    source_path: str
    destination_path: str | None
    status: str
    warnings: tuple[str, ...]
    losses: tuple[str, ...]
    changed: bool
    written: bool
    backup_path: str | None
```

Recommended statuses:

```text
not_needed
planned
migrated
migrated_with_warnings
blocked
failed
cancelled
```

Persisting this model requires a registered schema.

Until then, it remains an internal result and may be rendered as reviewed Markdown.

---

# 19. Loss handling

A loss is any source meaning that cannot be represented exactly in the target.

Examples:

```text
absolute source path cannot be made project-relative
unknown legacy status
missing raw artifact
naive timestamp
malformed count
ambiguous alias
pre-scenario run has no scenario evidence
old lincat shape cannot map automatically
scenario command has no supported replacement
gold content cannot be associated with one scenario
```

Loss classes:

```text
none
non-semantic
semantic-recoverable
semantic-blocking
```

Rules:

- non-semantic loss may produce a warning;
- semantic-recoverable loss requires explicit user confirmation;
- semantic-blocking loss prevents successful migration;
- losses are never hidden;
- the destination must not claim stronger evidence than the source supports.

---

# 20. Migration blockers

Migration must stop when:

```text
source schema cannot be identified
source is corrupted beyond safe interpretation
required project identity is ambiguous
destination would overwrite unrelated data
path escapes approved roots
target version is unsupported
required enum meaning is unknown
gold owner cannot be identified
module rename has unresolved consumers
source and destination are the same unsafe path
migration cannot preserve required release evidence
security validation fails
```

A blocker must leave the source unchanged.

---

# 21. Atomic write and recovery

Write migration sequence:

```text
read source
→ validate source
→ build current model
→ validate current model
→ write sibling or owned temporary file
→ flush and close
→ read temporary file
→ validate destination
→ atomically publish destination
→ verify final bytes
→ record hashes
```

On failure:

- preserve source;
- preserve previous valid destination;
- retain or quarantine temporary evidence;
- report failure;
- do not claim migration success.

---

# 22. Backup policy

Version control is the preferred backup for project sources.

For non-versioned persisted assets, migration may create a backup.

Recommended backup rules:

```text
backup only before explicit in-place replacement
backup path is deterministic
backup is not treated as canonical
backup hash is recorded
backup cleanup is separate
```

Avoid accumulating uncontrolled `.bak` files in source directories.

A migration may instead write a new destination and leave the old source untouched.

This is preferred when practical.

---

# 23. Rollback policy

Every migration changing a canonical asset must define rollback.

Rollback should restore:

```text
previous canonical file
previous project configuration
previous source location
previous contract implementation
previous scenario/gold association
previous external-tool request
```

Rollback must not:

- erase migration evidence;
- reuse a failed destination as valid;
- downgrade a project silently;
- destroy data created by the newer version without warning.

Downgrade migrations are optional.

When unsupported, state that rollback requires restoring the pre-migration backup or version-control revision.

---

# 24. Idempotence

Running a migrator twice against the same source and target must:

- produce the same canonical meaning;
- avoid duplicate entries;
- avoid repeated renames;
- avoid multiplying warnings;
- avoid modifying an already current destination unnecessarily.

Expected outcomes:

```text
first run: migrated
second run: not_needed
```

Idempotence must be tested.

---

# 25. Determinism

Given identical:

```text
source bytes
source version
target version
migration options
environment-independent path context
```

the migrator must produce the same:

```text
target structure
field values
ordering
warnings
loss classifications
```

Environment-specific absolute paths may differ only where the target contract explicitly permits them.

---

# 26. Security requirements

Migration code handles potentially untrusted paths and data.

Required controls:

```text
root containment
symlink policy
path traversal rejection
size limits
UTF-8 policy
JSON/TOML parser safety
no arbitrary code execution
no shell interpolation
secret redaction
safe temporary files
atomic replacement
protected source preservation
```

A project or schema migration must never execute commands found in the source data merely because they are present.

Scenario execution is a separate explicit validation operation.

---

# 27. Migration commands

Recommended final command family:

```text
gf-wordbench migrate inspect <path>
gf-wordbench migrate apply <path>
gf-wordbench migrate verify <path>
```

Domain-specific forms may be clearer:

```text
gf-wordbench schemas migrate <path>
gf-wordbench project migrate
gf-wordbench state migrate
gf-wordbench runs migrate <run-dir>
```

Command design must be finalized in `CLI_REFERENCE.md`.

Required semantics:

- `inspect` is read-only;
- `apply` is explicit and writes canonical output;
- `verify` checks the destination;
- `--dry-run` performs no canonical write;
- `--output` selects a safe destination when supported;
- `--in-place` is explicit and guarded;
- no migration command deletes the source by default.

---

# 28. Migration plan

Before write migration, the tool should produce a plan containing:

```text
migration ID
source identity
detected version
target identity
target version
files read
files created
files replaced
files left unchanged
aliases converted
warnings
losses
blockers
rollback
```

A plan may be rendered to console or a run-local report.

Persisting plans requires a registered schema.

---

# 29. Migration verification

Verification checks:

```text
target schema identity
target schema version
required fields
canonical paths
canonical enums
ordering
hashes
cross-file references
required artifacts
no legacy aliases
no unresolved placeholders
no path escapes
no source modification
```

Project verification additionally checks:

```text
entrypoints
checkpoints
scenario registry
gold ownership
module suffix
project identity
template requirements
release gates
```

---

# 30. General deprecation lifecycle

Canonical lifecycle:

```text
release N:
  replacement introduced
  old item marked deprecated
  warning emitted
  migration documented

release N+1:
  old item still supported
  warning remains
  tests cover both paths
  canonical writer uses only replacement

eligible removal release:
  old caller/reader removed
  migration path retained when required
  identifier marked retired
  release notes list removal
```

For persisted historical data, readers may remain beyond runtime API removal.

Removal of a writer and removal of a reader are separate decisions.

---

# 31. Removal gates

A deprecated item may be removed only when:

```text
replacement is active
migration is documented
support window elapsed
usage within repository is removed
tests no longer depend on legacy path except migration fixtures
changelog lists removal
contract status is retired
identifier remains reserved
release version permits breaking change
```

Persisted-reader removal additionally requires:

```text
support policy permits it
migration tool exists or historical support is explicitly ended
fixtures verify clear rejection
```

---

# 32. Retirement cleanup

Retirement cleanup may remove:

```text
adapter code
legacy writer
deprecated CLI alias
unused project placeholder
old template example
obsolete report alias
old external command builder
```

Retirement cleanup must retain:

```text
contract ID
schema ID history
migration record
release note
legacy fixture when reader support remains
```

Do not delete evidence needed to interpret historical runs.

---

# 33. Public Python API migration

Recommended pattern:

```python
def old_api(*args, **kwargs):
    warn_deprecated(
        old="old_api",
        replacement="new_api",
        removal="2.0.0",
    )
    request = convert_legacy_arguments(*args, **kwargs)
    return new_api(request)
```

Rules:

- old API delegates to new owner;
- conversion is explicit;
- behavior differences are documented;
- exceptions are mapped deliberately;
- no duplicate implementation;
- adapter is tested;
- removal is versioned.

A required parameter or return-type change without an adapter is breaking.

---

# 34. Dataclass and result-model migration

When a public result model changes:

```text
identify producers
identify consumers
define new model
define old-to-new adapter
define persistence impact
define equality/round-trip expectations
update reports
update GUI/CLI
```

Adding optional in-memory data may be compatible.

Removing, renaming, or changing a required field is breaking.

Do not rely on unrestricted `**legacy_dict` construction to migrate models.

Map fields explicitly.

---

# 35. CLI migration

CLI deprecation must preserve:

```text
command intent
exit-code meaning
side-effect safety
machine-readable output behavior
```

Example:

```text
old:
  gf-wordbench audit --mode file

new:
  gf-wordbench quick --target <file>
```

Migration sequence:

1. introduce new command;
2. keep old alias temporarily;
3. emit warning;
4. translate old arguments into the new request;
5. preserve old exit behavior where safe;
6. document differences;
7. remove in permitted release.

A deprecated destructive command must not gain broader side effects during adaptation.

---

# 36. GUI migration

GUI migrations may change visual layout without strict compatibility requirements.

They must preserve:

```text
project loading
canonical mode selection
status semantics
artifact access
gold-update confirmation
state safety
```

GUI-state migration must:

- ignore unknown optional fields safely;
- reset impossible runtime state;
- preserve safe recent paths where possible;
- never migrate project identity into state;
- use current canonical state writer.

A malformed disposable state file should fall back safely.

---

# 37. Validation-mode migration

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Legacy mappings:

```text
file → quick
all → diagnostic
```

Rules:

- legacy values may be read during migration;
- canonical writers emit only current values;
- CLI aliases may warn during support window;
- mode translation must preserve or clearly document stage differences;
- no legacy mode may bypass release gates;
- state and summary migrations use the same mapping.

Removing aliases is a package compatibility decision, not a schema rewrite.

---

# 38. Persisted-schema migration

For every persisted schema:

```text
identify schema ID
identify source version
identify target version
define compatibility
define field mapping
define path mapping
define enum mapping
define defaults
define losses
define writer
define readers
add fixtures
add round-trip tests
```

Supported assets include:

```text
project/project.toml
.gf_wordbench_state.json
legacy .gf_audit_state.json
summary.json
manifest.json
scenario .out
gold files
stable report identities
persistent directory layout
```

A schema change is incomplete without readers, migration, and tests.

---

# 39. Enum migration

Enum migrations are high risk.

Rules:

- aliases map one old meaning to one current meaning;
- ambiguous values are blockers or losses;
- unknown values are never guessed;
- removing or redefining a value requires schema major review;
- strict readers reject unknown values;
- historical viewers may preserve unknown text with warning.

Example:

```text
legacy mode "all"
→ canonical mode "diagnostic"
```

Do not map an old value to a new value merely because names appear similar.

---

# 40. Path migration

Path migration must know the path base.

Possible bases:

```text
project root
run root
output root
environment absolute
```

Rules:

- canonical project-owned paths are relative with `/`;
- canonical run-artifact paths are run-relative with `/`;
- environment paths may remain absolute;
- Windows `\` is accepted in legacy input;
- unresolved `..` is rejected;
- drive letters are prohibited for project-relative paths;
- loss is reported when an absolute path cannot be safely relativized.

Not every string ending in a filename is a path.

Use field-specific mapping.

---

# 41. Timestamp migration

Canonical timestamps are RFC 3339 UTC strings.

Migration rules:

- timezone-aware values convert to UTC;
- `+00:00` may canonicalize to `Z`;
- naive timestamps produce warning or blocker according to importance;
- migration must not invent a timezone without explicit evidence;
- original raw value should be preserved in migration evidence when interpretation is uncertain.

---

# 42. Fingerprint migration

Legacy:

```text
sha1_short
```

Canonical:

```text
hash_algorithm = sha256
hash = full lowercase SHA-256
```

A legacy short hash cannot be expanded into SHA-256.

Migration options:

```text
recompute from available source bytes
record unavailable and warning
block when fingerprint is release-required
```

Never pad or relabel a SHA-1 value as SHA-256.

---

# 43. State migration

Legacy source:

```text
.gf_audit_state.json
```

Canonical destination:

```text
.gf_wordbench_state.json
```

Migration should:

- preserve safe environment paths;
- migrate legacy mode aliases;
- reset `is_running` or equivalent runtime state to false;
- remove project-owned language fields;
- validate timeout and numeric settings;
- discard unserializable runtime objects;
- write canonical schema identity and version;
- leave the legacy file until explicit cleanup.

State is disposable.

Loss of nonessential UI preferences may be a warning rather than a blocker.

---

# 44. Run-summary migration

Supported legacy forms include:

```text
flat unversioned summary
nested unversioned summary
legacy aliases and counts
pre-scenario summaries
```

Canonical target:

```text
gf-wordbench.run-summary/1.0
```

Mappings include:

```text
ai_brief_path → artifacts.ai_ready
ai_ready_path absolute → run-relative artifacts.ai_ready when possible
mode=file → quick
mode=all → diagnostic
ok → files_ok
fail → files_fail
top-error mapping → top-error array
legacy file path → project-relative file_path when possible
```

Migration must not invent scenario results for runs that predate scenarios.

Use:

```json
"scenario_results": []
```

and record historical limitation.

---

# 45. Manifest migration

Manifest migration must verify actual files.

Do not create a valid-looking manifest solely from old path fields.

Required checks:

```text
artifact exists
path stays inside run root
role is known
size is measured
SHA-256 is computed
requiredness is known
duplicates are rejected
manifest excludes itself
```

Missing required historical artifacts are losses.

A historical run may remain readable without becoming a fully verified current run.

---

# 46. Report migration

Human reports are not primary migration sources.

Rules:

- prefer `summary.json` and raw evidence;
- use Markdown only for historical display or last-resort recovery;
- never infer exact structured values from prose when ambiguity exists;
- preserve old reports as historical artifacts;
- current reports are regenerated only from a valid current model;
- regeneration must not rerun GF.

Stable report heading changes follow soft-schema version policy.

---

# 47. Project-schema migration

Opening a project may inspect and propose migration.

It must not rewrite:

```text
project/project.toml
project docs
scenarios
golds
source files
```

without explicit authorization.

Project migration plan must include:

```text
source schema
target schema
changed fields
new required files
template changes
entrypoint changes
scenario changes
gold changes
manual actions
release impact
rollback
```

A project schema major change normally requires explicit `project migrate`.

---

# 48. Project-template migration

A template upgrade does not automatically rewrite existing projects.

Existing projects are migrated by comparing:

```text
project schema
template version/provenance when known
required directory structure
required documents
required validation assets
```

Possible actions:

```text
add missing optional document
add required document with placeholder
migrate project.toml
add validation directory
update project contract template sections
```

Rules:

- never replace project-specific content with template content;
- merge cannot be automatic when semantic content exists;
- active project identity is preserved;
- newly required placeholders become migration tasks, not invented values.

---

# 49. Active-language project migration

A language project is a network of contracts.

Migration must coordinate:

```text
provider GF files
consumer GF files
interfaces and instances
entrypoints
checkpoints
project.toml
scenarios
inputs
golds
dependency map
status ledger
decision log
release criteria
release evidence
```

No project-level contract may be migrated through an isolated file edit.

---

# 50. GF module contract migration

Examples:

```text
lincat shape change
public oper rename
public parameter change
provider replacement
module suffix change
entrypoint rename
```

Required process:

1. identify contract ID;
2. update provider;
3. update direct consumers;
4. update interfaces/instances;
5. update downstream entrypoints;
6. update scenarios;
7. update golds deliberately;
8. update dependency map;
9. update status ledger;
10. update project lock;
11. run checkpoints and release validation.

Temporary adapters in GF may be used only when they preserve semantics and are documented.

Do not flatten structured lincats as a migration shortcut.

---

# 51. Module rename migration

A module rename changes:

```text
filename
module declaration
imports
entrypoints
checkpoints
scenario load commands
PGF targets
gold metadata when identity-dependent
documentation
```

Rules:

- one canonical new name;
- old module may remain as a temporary forwarding compatibility module;
- forwarding module is deprecated;
- duplicate ownership is prohibited;
- removal version is documented;
- clean compilation proves no hidden old import remains.

---

# 52. Project identity migration

Changing any of the following is breaking:

```text
project ID
language identifier
module suffix
authoritative source root
release entrypoint identity
```

Required migration:

```text
project.toml
GF filenames and module declarations when applicable
scenarios
gold headers and names
project docs
run comparison identity
release artifact naming
automation
contract lock
```

Old active identifiers must be removed from current project paths and validation assets after cutover.

Historical evidence may retain them.

---

# 53. Scenario migration

A scenario migration may change:

```text
scenario ID
script path
entrypoint
inputs
markers
commands
assertions
requiredness
gold association
normalization version
```

Rules:

- scenario ID rename is breaking;
- required marker changes are contract changes;
- unsupported old commands cannot be silently ignored;
- old and new scenario results may not be directly comparable when semantics differ;
- coverage matrix and release criteria must be updated;
- current writers/results use only current scenario IDs.

---

# 54. Gold migration

Gold migration must use the explicit gold workflow.

It must not:

- wrap unknown legacy text in a new header and declare success;
- auto-accept current output;
- modify gold during ordinary validation;
- discard old gold before review.

Required sequence:

```text
preserve old gold
→ identify scenario
→ run current scenario
→ preserve raw evidence
→ normalize
→ construct candidate
→ compare old and candidate
→ review semantic differences
→ accept explicitly
→ write atomically
```

Gold schema migration and gold content migration are separate.

---

# 55. Normalization migration

Normalization changes affect how raw evidence becomes comparable output.

Required actions:

```text
increment normalization version
update normalizer
update tests
run affected scenarios
generate every candidate
review every diff
update gold headers and content
record migration
rerun release validation
```

A normalization migration must not remove meaningful linguistic evidence.

If meaning can change, it is a normalization major migration.

---

# 56. Report and artifact path migration

Changing a stable artifact path requires:

```text
new artifact owner/path
reader compatibility
manifest update
summary artifact field update
cleanup behavior
migration or alias
report links
GUI/CLI access
tests
```

Preferred transition:

```text
read old path through legacy summary
write only new path
```

Avoid creating duplicate canonical files at both paths.

A transitional export may be offered explicitly.

---

# 57. External-tool contract migration

Changes to GF or another external tool include:

```text
executable resolution
ordered arguments
working directory
environment
stdin
stdout/stderr interpretation
timeout
termination
artifacts
supported versions
```

Migration must update:

```text
request builder
process runner
configuration
result model
diagnostics
artifact checks
unit tests
real-tool tests
golds when output changes
external-tool lock
compatibility notes
```

No external command may change in isolation.

---

# 58. GF version migration

When moving to a new GF version:

1. record old and new versions;
2. run version probe tests;
3. compile fixture grammar;
4. build PGF;
5. run scenarios;
6. review diagnostics;
7. review normalization;
8. review gold diffs;
9. test Windows behavior where supported;
10. update compatibility policy.

Possible outcomes:

```text
compatible
compatible_with_warnings
requires_normalization_migration
requires_project_changes
incompatible
```

A single successful compile is insufficient to declare version support.

---

# 59. Platform migration

Platform migration may include:

```text
Windows path handling
process-tree termination
line endings
encoding
launcher behavior
filesystem semantics
```

Rules:

- persisted canonical paths remain portable;
- raw evidence preserves actual environment where needed;
- platform-specific state remains outside project configuration;
- platform migration must not alter language project identity;
- tests include spaces, Unicode, CRLF, timeouts, and missing executable.

---

# 60. Migration of experimental behavior

Experimental behavior may change or disappear without a stable compatibility guarantee.

However:

- persisted experimental data still needs an identity;
- users must be warned before irreversible writes;
- experimental writers must not overwrite stable canonical assets;
- promotion to active requires migration decision;
- retirement must cleanly reject or migrate experimental data.

“Experimental” is not permission to corrupt data.

---

# 61. Migration of blocked project contracts

A blocked project contract represents intended behavior not currently satisfied.

Migration options:

```text
repair and activate
replace with a new active contract
retire as no longer required
split into smaller contracts
```

Rules:

- blocked is not stable;
- release criteria determine whether it gates release;
- migration must update status ledger;
- no consumer may assume blocked behavior is available.

---

# 62. Compatibility adapters

Adapters should be narrow.

Required properties:

```text
one old surface
one canonical replacement
deterministic mapping
warning
tests
removal target
no independent business logic
```

Adapters must not become permanent alternate architectures.

When multiple old forms exist, each may have a named adapter delegating to one canonical service.

---

# 63. Adapter removal

Before removing an adapter:

```text
repository callers use canonical API
CLI/GUI use canonical API
fixtures retain only intentional legacy cases
support window elapsed
migration docs exist
contract status retired
release notes list removal
```

Remove adapter tests only after adding clear rejection tests where necessary.

---

# 64. Legacy data retention

Legacy sources may be retained as:

```text
migration fixtures
historical runs
archived project snapshots
read-only state backups
gold migration evidence
```

They must be clearly separated from canonical active data.

Legacy fixtures must not be discovered as active projects, current runs, or current golds.

---

# 65. Legacy compatibility registry

Canonical legacy mappings:

| Legacy element | Canonical replacement | Policy |
|---|---|---|
| `.gf_audit_state.json` | `.gf_wordbench_state.json` | Import and migrate |
| Unversioned state | `gf-wordbench.app-state/1.0` | Read legacy, write current |
| Flat `summary.json` | `gf-wordbench.run-summary/1.0` | Read/migrate |
| Nested unversioned `summary.json` | `gf-wordbench.run-summary/1.0` | Read/migrate |
| `ai_brief_path` | `artifacts.ai_ready` | Read alias only |
| Absolute `ai_ready_path` | run-relative `artifacts.ai_ready` | Convert when possible |
| `mode=file` | `mode=quick` | Migration alias |
| `mode=all` | `mode=diagnostic` | Migration alias |
| `sha1_short` | SHA-256 fingerprint | Recompute or report unavailable |
| `ok` total | `files_ok` | Rename |
| `fail` total | `files_fail` | Rename |
| Top-error mapping | top-error array | Normalize |
| Language fields in state | `project.toml` | Remove from state |
| Legacy project placeholders | completed active-project values | Explicit project migration |
| Source-adjacent stale artifacts | run-owned current artifacts | Never accepted as current evidence |

Canonical writers must not emit any legacy element in this table.

---

# 66. `gf-audit` application migration

The application migration includes:

```text
name: gf-audit → GF Wordbench
package: gf-wordbench
CLI: gf-wordbench
state file migration
mode migration
summary migration
artifact-path migration
fingerprint migration
report alias migration
project identity extraction
```

Rules:

- historical `gf-audit` runs remain historical;
- they do not define the current active project;
- legacy readers may load them;
- current reports are not silently written into old run directories;
- old state is imported explicitly or safely at first use according to state policy;
- canonical writers use GF Wordbench identities only.

---

# 67. Cleanup of `gf-audit` compatibility

Removal phases:

```text
phase 1:
  read old, write current
  warn on active legacy aliases

phase 2:
  remove old CLI writers/callers
  retain legacy run/state readers

phase 3:
  retain only explicit migration tools and fixtures

phase 4:
  remove legacy readers when policy permits
  retain migration documentation and IDs
```

Historical run access may justify longer reader support than runtime CLI aliases.

---

# 68. Release requirements for migrations

A release containing a migration must include:

```text
migration ID
source and target versions
user action
automatic versus explicit behavior
warnings
loss policy
rollback
support window
tests
changelog entry
release matrix update
```

A migration release must not claim success when only the current writer was implemented.

---

# 69. Changelog requirements

Use categories:

```text
Deprecated
Removed
Migration
Compatibility
Changed
Security
```

Every deprecated item records:

```text
old item
replacement
first deprecated version
earliest removal
```

Every removed item records:

```text
last supported version
replacement
migration path
```

Every schema migration records:

```text
source schema
target schema
write behavior
reader support
```

---

# 70. Migration documentation requirements

User-facing migration instructions should provide:

```text
who needs migration
how to detect old form
backup step
dry-run command
apply command
verification command
expected file changes
known losses
rollback
post-migration validation
```

Do not require users to infer a migration from release notes alone.

---

# 71. Testing strategy

Migration tests must use real legacy fixtures.

Recommended directories:

```text
tests/migrations/
tests/fixtures/legacy/
tests/schemas/
tests/contracts/
tests/projects/
```

Required test classes:

```text
detection
mapping
warnings
losses
idempotence
atomic writes
rollback
security
reader support
canonical writer behavior
removal behavior
```

---

# 72. Persisted migration tests

Required cases:

```text
missing schema ID
wrong schema ID
supported old major
unsupported newer major
malformed version
unknown optional field
unknown enum
Windows path conversion
UTC conversion
naive timestamp
null optional path
top-error mapping
legacy mode
legacy fingerprint
missing raw artifact
atomic failure
source preservation
second-run idempotence
canonical-only writer
```

---

# 73. API and CLI migration tests

Required cases:

```text
old API delegates to new API
warning emitted once
old and new result meaning agree
invalid old argument rejected clearly
deprecated CLI alias maps correctly
exit code preserved
new command works independently
removal release rejects old form
```

---

# 74. Project migration tests

Required cases:

```text
old project schema
missing new required document
template upgrade
project identity preservation
module suffix rename plan
entrypoint rename
scenario ID rename
gold ownership change
unresolved placeholder
dirty project
unsafe path
rollback
release validation after migration
```

Use fixture projects, not the active project, for framework integration tests.

---

# 75. External-tool migration tests

Required cases:

```text
old and new GF versions
argument-order compatibility
working-directory behavior
stdout/stderr differences
timeout behavior
artifact verification
diagnostic parser differences
normalization differences
Windows paths
missing executable
```

Support claims must be evidence-based.

---

# 76. Migration acceptance criteria

A migration is accepted when:

```text
[ ] Source contract identified
[ ] Target contract identified
[ ] Versions identified
[ ] Owner identified
[ ] Providers updated
[ ] Consumers updated
[ ] Reader/adapter implemented
[ ] Canonical writer implemented
[ ] Explicit migrator implemented where required
[ ] Source remains recoverable
[ ] Warnings are visible
[ ] Losses are classified
[ ] Atomic write tested
[ ] Idempotence tested
[ ] Security reviewed
[ ] Rollback documented
[ ] Legacy writers removed
[ ] Tests use real legacy fixtures
[ ] Contract/schema locks updated
[ ] Changelog updated
[ ] Support window documented
[ ] Removal conditions documented
```

---

# 77. Deprecation acceptance criteria

A deprecation is valid when:

```text
[ ] Deprecated item is stable and identifiable
[ ] Replacement exists or retirement reason is documented
[ ] Warning text is defined
[ ] First deprecated version is known
[ ] Earliest removal version is known or policy-bound
[ ] Migration instructions exist
[ ] Old path remains tested
[ ] New path is tested
[ ] Canonical writers use replacement only
[ ] Contract status is Deprecated
[ ] Changelog includes deprecation
```

---

# 78. Removal acceptance criteria

A removal is valid when:

```text
[ ] Support window elapsed or exception approved
[ ] Replacement is Active
[ ] Repository consumers migrated
[ ] Canonical data contains no old form
[ ] Migration path remains available when required
[ ] Contract ID is Retired
[ ] Identifier is reserved
[ ] Rejection behavior is clear
[ ] Tests updated
[ ] Changelog lists removal
[ ] Package/project major policy is satisfied
```

---

# 79. Migration anti-patterns

Prohibited:

## 79.1 Silent rewrite on open

```text
load project
→ automatically rewrite project.toml
```

## 79.2 Dual canonical fields

```json
{
  "ai_brief_path": "...",
  "ai_ready": "..."
}
```

in one current canonical summary.

## 79.3 Guess unknown meaning

```text
unknown legacy status
→ assume FAIL
```

## 79.4 Relabel old hash

```text
sha1_short
→ claim sha256
```

## 79.5 Destructive in-place conversion

```text
overwrite source before destination validation
```

## 79.6 Permanent compatibility fork

Old and new implementations evolve independently.

## 79.7 Gold auto-migration

Current scenario output is accepted without review.

## 79.8 Template overwrite

Generic template replaces project-specific documentation.

## 79.9 Deprecated without replacement information

Users cannot act on the warning.

## 79.10 Removal without version review

A public or persisted contract disappears in a patch release.

---

# 80. Balanced migration policy

GF Wordbench should not keep every old implementation forever.

It should preserve enough compatibility to:

- open supported historical runs;
- migrate supported projects;
- recover state;
- explain old aliases;
- maintain current users through announced transitions.

It should not preserve:

- duplicate business logic;
- unsafe command behavior;
- legacy canonical writers;
- ambiguous data interpretation;
- undocumented compatibility paths;
- obsolete aliases indefinitely when migration is complete.

Long-term historical reading and active runtime compatibility are separate decisions.

---

# 81. Migration ownership

| Migration area | Owner |
|---|---|
| Package/API | framework maintainer |
| CLI | CLI owner and application service owner |
| GUI state | state owner |
| Framework contracts | contract owners |
| External GF/tool contract | tool integration owner |
| Persisted schema | schema owner |
| Project template | project lifecycle owner |
| Active project | language project owner |
| GF module contract | provider and project architecture owner |
| Scenario | scenario/project owner |
| Gold | explicit gold updater and project reviewer |
| Normalization | normalization owner |
| Reports/artifacts | report/artifact owner |
| Release | release maintainer |

A migration may have multiple owners, but one coordinator is required.

---

# 82. Migration change template

```text
Migration ID:
Title:
Owner:
Category:
Source:
Source version:
Target:
Target version:
Reason:
Deprecated in:
Removal no earlier than:
Reader support:
Canonical writer:
Explicit command:
Warnings:
Losses:
Blockers:
Security:
Rollback:
Tests:
Documentation:
Release evidence:
Status:
```

---

# 83. Deprecation entry template

```text
Item:
Type: API | CLI | schema | field | mode | artifact | scenario | project contract
Replacement:
Reason:
First deprecated version:
Earliest removal version:
Warning channel:
Migration:
Compatibility adapter:
Tests:
Owner:
Status:
```

---

# 84. Migration verification checklist

```text
[ ] Source bytes unchanged
[ ] Source hash recorded
[ ] Destination uses canonical identity
[ ] Destination uses canonical version
[ ] Destination validates
[ ] Required fields preserved
[ ] Unknown meanings reported
[ ] Paths use correct bases
[ ] Timestamps are explicit
[ ] Enums are canonical
[ ] Ordering is deterministic
[ ] No legacy aliases emitted
[ ] No secrets copied
[ ] Destination written atomically
[ ] Final hash verified
[ ] Second run is idempotent
[ ] Rollback path exists
[ ] Post-migration validation passes
```

---

# 85. Post-migration validation

After migration, run the relevant checks.

Framework/schema:

```text
gf-wordbench schemas check --strict
gf-wordbench contracts check --strict
gf-wordbench contracts check-external --strict
```

Project:

```text
gf-wordbench project contracts check
gf-wordbench checkpoint
gf-wordbench release
```

Use only commands implemented by the current release.

When a command is not implemented, run the equivalent test suite and document it.

A migration is not release-complete until relevant validation passes.

---

# 86. Drift indicators

Probable migration/deprecation drift exists when:

- a reader rewrites an asset it does not own;
- canonical output contains a legacy alias;
- old and new implementations have different business logic;
- warning has no replacement;
- removed item remains in docs as active;
- deprecated item has no tests;
- migration overwrites source;
- unknown enum is silently mapped;
- project opens and changes files automatically;
- old gold is replaced without diff review;
- contract ID disappears instead of becoming retired;
- support window differs across documents;
- package patch removes a public surface;
- legacy mode is emitted by current writer;
- migration cannot be run twice safely;
- destination validates only because required evidence was fabricated;
- release notes omit required user action.

Any drift requires migration review.

---

# 87. Policy exceptions

Exceptions are limited to:

```text
security
data corruption
unsafe process execution
false validation success
legal/licensing requirement
upstream incompatibility
```

An exception record must include:

```text
normal policy
exception
reason
affected versions
user action
recovery
tests
approval
```

An exception may shorten a support window.

It may not justify silent data loss.

---

# 88. Definition of migration complete

A migration is complete when:

1. the current provider and writer are active;
2. all maintained consumers use the current contract;
3. supported legacy sources are readable or explicitly rejected;
4. an explicit migrator exists where persisted rewrite is required;
5. source preservation and rollback are defined;
6. warnings and losses are visible;
7. canonical writers emit no old form;
8. tests cover source, target, failure, and idempotence;
9. locks and references are updated;
10. post-migration validation passes;
11. deprecation and removal states are recorded;
12. release notes explain user action.

Migration completion does not necessarily mean legacy readers can be removed.

---

# 89. Definition of deprecation complete

A deprecation phase is complete when:

1. the replacement is active;
2. the old surface warns;
3. users have instructions;
4. canonical writers use only the replacement;
5. old and new paths are tested;
6. the removal window is recorded;
7. repository-owned consumers have migrated;
8. changelog and contract status agree.

---

# 90. Definition of retirement complete

Retirement is complete when:

1. the deprecated implementation is removed;
2. required historical readers or migrators remain;
3. the contract ID is marked retired;
4. the identifier is reserved;
5. release notes list removal;
6. rejection behavior is clear;
7. no active project or template depends on it;
8. tests cover the final support boundary.

---

# 91. Final invariants

Migration and deprecation must preserve:

1. no implicit destructive migration;
2. source recoverability;
3. read-old/write-current behavior;
4. canonical-only writers;
5. explicit versions;
6. explicit migration ownership;
7. visible warnings;
8. reported losses;
9. blocking on unknown required meaning;
10. atomic publication;
11. idempotence;
12. deterministic output;
13. no secret leakage;
14. complete provider/consumer coordination;
15. project-wide migration for GF contract changes;
16. explicit scenario and gold review;
17. evidence-based external-tool compatibility;
18. documented support windows;
19. reserved historical identifiers;
20. post-migration validation.

---

# 92. Final rule

> Migrate meaning, not only bytes and names.

A safe migration preserves what can be preserved, reports what cannot, writes only the current canonical form, and leaves the source recoverable.

A responsible deprecation gives users a working replacement, enough time to migrate, and a clear removal boundary.

GF Wordbench must never achieve architectural cleanliness by silently discarding the evidence, projects, or assumptions that earlier versions created.
