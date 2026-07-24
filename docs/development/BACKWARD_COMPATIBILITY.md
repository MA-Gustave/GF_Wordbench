# GF Wordbench — Backward Compatibility

**Document ID:** `GF-WB-DEV-BACKWARD-COMPATIBILITY`  
**Status:** Normative development policy  
**Applies to:** GF Wordbench framework, public commands, persisted artifacts, project templates, active projects and supported external-tool integrations  
**Canonical package:** `gf-wordbench`  
**Canonical CLI:** `gf-wordbench`  
**Compatibility line:** `1.x`  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related locks:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Purpose

This document defines what GF Wordbench preserves across releases and how incompatible historical inputs are handled.

Compatibility applies independently to:

- command-line syntax;
- process exit codes;
- declared Python entrypoints;
- shared result models;
- project configuration;
- application state;
- run summaries and manifests;
- scenario outputs and gold files;
- human-report soft schemas;
- run-directory layout;
- project templates;
- external GF command contracts;
- active-project interfile contracts;
- Windows launchers;
- documented environment variables.

The governing rule is:

> Preserve documented contracts, migrate persisted meaning explicitly, emit only canonical forms and keep legacy handling isolated from the current architecture.

This policy prevents:

- silent breakage of projects, automation and persisted evidence;
- permanent propagation of legacy behavior through core components.

---

## 2. Product boundary

GF Wordbench compatibility concerns one active project per workspace and one normative project target per run.

It does not create compatibility contracts for:

- multi-workspace registries;
- multilingual portfolio databases;
- cross-project readiness models;
- `gf-portfolio` private schemas, storage or services.

Allowed dependency direction:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
```

GF Wordbench must remain installable, executable and testable without `gf-portfolio`.

External consumers depend only on documented public artifacts and interfaces.

---

## 3. Compatibility surfaces

This policy governs:

```text
gf-wordbench command
public subcommands and options
process exit codes
documented environment variables
declared Python entrypoints
shared serialized model fields
project/project.toml
.gf_wordbench_state.json
supported legacy .gf_audit_state.json input
run_<run-id>/summary.json
run_<run-id>/manifest.json
scenario normalized output
scenario gold files
summary.md required headings
AI_READY.md required headings
top_errors.txt line format
run-directory names and owned artifact paths
project template layout
GF executable invocation contracts
supported GF versions and capabilities
active-project contract migrations
```

A detail is not a public compatibility surface unless it is documented, persisted, externally consumed or declared by a contract lock.

Examples of non-public details:

- private Python helpers;
- private module paths;
- local variable names;
- exception traceback wording;
- console progress prose;
- GUI placement and styling;
- temporary files removed before run finalization;
- undocumented environment variables;
- test fixtures not declared as compatibility fixtures;
- implementation quirks contradicted by normative documentation.

---

## 4. Normative terms

- **CANONICAL**: form emitted by the current writer or public interface.
- **LEGACY**: supported historical input not emitted canonically.
- **COMPATIBLE CHANGE**: preserves documented meaning for supported consumers.
- **BREAKING CHANGE**: requires a major version, explicit migration or both.
- **DEPRECATION**: temporary continued support for a replaced public element.
- **ALIAS**: historical name mapped exactly to a canonical name.
- **MIGRATION**: explicit conversion between documented representations.
- **SHIM**: isolated adapter for an older public interface.
- **SUPPORT WINDOW**: versions or forms accepted by current readers.
- **LOSSLESS MIGRATION**: preserves all required meaning.
- **LOSSY MIGRATION**: cannot preserve all meaning and reports every loss.
- **PUBLIC SURFACE**: documented contract used outside its owner.

---

## 5. Core rules

### 5.1 Canonical writers and tolerant readers

Current writers emit only canonical forms.

Current readers may accept:

- the current schema major;
- supported minor versions of that major;
- the immediately preceding major when a tested migration exists;
- explicitly registered unversioned predecessor forms.

Readers must reject or preserve unknown meaning without reinterpretation.

### 5.2 One meaning per identifier

A command, field, enum value, artifact role, contract ID or status token must not be reused for another meaning.

Historical identifiers remain documented where readers may still encounter them.

### 5.3 Explicit persisted migration

A breaking persisted-format change requires:

- a schema version change;
- a reader or migrator;
- compatibility fixtures;
- loss reporting;
- release notes;
- relevant lock updates.

### 5.4 No legacy emission

Canonical writers never emit accepted legacy aliases.

Examples:

```text
read mode=file
write mode=quick

read ai_brief_path
write artifacts.ai_ready

read legacy SHA-1 evidence
write no fabricated SHA-256 value
```

### 5.5 No semantic fallback

Fallback is allowed only when documented meaning is preserved.

When equivalent behavior is unavailable, Wordbench:

- rejects the input;
- reports it as unsupported;
- or proceeds with an explicit reduced-guarantee warning.

It does not silently claim equivalence.

### 5.6 Compatibility is tested

Every supported alias, legacy reader, migration and external-tool adapter has a fixture or contract test.

---

## 6. Versioning

### 6.1 Framework version

GF Wordbench uses semantic versioning:

```text
MAJOR.MINOR.PATCH
```

**MAJOR** changes incompatible stable public contracts when ordinary migration or aliasing cannot preserve them.

**MINOR** adds compatible functionality such as:

- optional fields;
- optional commands;
- optional report sections;
- additional reader support;
- deprecation warnings;
- compatible GF capabilities.

**PATCH** fixes behavior without redefining public meaning, including:

- parsing and path fixes;
- deterministic-order fixes;
- report escaping;
- security corrections;
- diagnostic recognition improvements under existing status semantics.

### 6.2 Persisted schema versions

Persisted schemas use:

```text
MAJOR.MINOR
```

Examples:

```text
gf-wordbench.project/1.0
gf-wordbench.run-summary/1.1
```

Implementation-only fixes do not change a schema version.

### 6.3 Contract versions

Contract-lock versions change only when the documented boundary changes.

Prose correction without semantic change does not require a contract-version increment.

---

## 7. Compatibility ownership

| Surface | Owner | Mechanism |
|---|---|---|
| CLI commands and options | CLI entrypoint | aliases, warnings, major-version removal |
| Exit codes | CLI/application result owner | stable numeric meanings |
| Python entrypoints | declaring module and interfile lock | wrappers and adapters |
| Shared models | domain/application model owner | defaults, serializers and migrations |
| Project config | project loader and schema owner | schema versions |
| Application state | state adapter | legacy import and canonical rewrite |
| Run summary | summary reader/writer | schema migration |
| Manifest | manifest reader/writer | schema migration and verification |
| Scenario output | scenario normalizer | normalization versions |
| Gold files | active-project maintainers | reviewed updates |
| Human reports | report writers | soft-schema compatibility |
| Run paths | run-path owner | explicit migration and aliases |
| External GF commands | GF adapter | version/capability adapters |
| Project template | project initializer | migration guidance |
| Project contracts | active-project owner | explicit project migration |
| Deprecation schedule | release owner | changelog and removal release |

No reader rewrites an artifact it does not own.

---

## 8. Support policy

Current readers support:

```text
current schema major
supported minor versions
immediately previous major when a tested migration exists
registered predecessor GF Audit forms
```

Current writers emit:

```text
latest supported canonical form only
```

A deprecated CLI or Python alias remains available for at least one documented release transition unless immediate removal is required for security or data integrity.

Project templates from the preceding supported release line remain loadable or have an explicit migration.

GF support is capability-based and documented through:

```text
minimum supported version
tested versions
known incompatible versions
```

The support matrix records tested combinations only.

---

## 9. Deprecation

A deprecation defines:

```text
deprecated element
canonical replacement
first affected release
earliest removal release
warning behavior
migration instructions
tests
```

Warnings identify the old element and its replacement.

Example:

```text
WARNING: --mode all is deprecated; use --mode diagnostic.
```

Aliases normalize at the public boundary:

```text
CLI input: all
RunConfig.mode: diagnostic
summary.json: diagnostic
```

Before removal:

- update the changelog and migration guide;
- remove the alias from canonical examples and help when scheduled;
- preserve historical fixtures where readers still migrate it;
- return a clear replacement message.

Unsafe behavior may be removed immediately with a security explanation and migration guidance.

---

## 10. Compatibility registry

| Legacy element | Canonical replacement | Policy |
|---|---|---|
| Product label `Grammatical_Framework_audit` | `GF Wordbench` | Historical text only |
| CLI executable `gf-audit` | `gf-wordbench` | Optional boundary alias |
| `mode=file` | `mode=quick` | Read/CLI alias; never write |
| `mode=all` | `mode=diagnostic` | Read/CLI alias; never write |
| `--target-file` | `--target` | CLI alias |
| `--skip-version-probe` | `--no-version-probe` | CLI alias |
| `--emit-cpu-stats` | `--cpu-stats` | CLI alias |
| `--timeout-sec` | `--compile-timeout` | CLI alias |
| `--diff-previous` | `--compare-previous` | CLI alias |
| `--scan-dir` | project source configuration | Explicit migration override only |
| `--scan-glob` | project source configuration | Explicit migration override only |
| `--include-regex` | project selection configuration | Explicit migration override only |
| `--exclude-regex` | project selection configuration | Explicit migration override only |
| `--gf-path` | project and environment path resolution | Explicit migration override only |
| `.gf_audit_state.json` | `.gf_wordbench_state.json` | Import and migrate |
| unversioned state | `gf-wordbench.app-state/1.0` | Read legacy; write canonical |
| unversioned flat summary | `gf-wordbench.run-summary/1.0` | Migrate |
| unversioned nested summary | `gf-wordbench.run-summary/1.0` | Migrate |
| `ai_brief_path` | `artifacts.ai_ready` | Read alias only |
| absolute `ai_ready_path` | run-relative `artifacts.ai_ready` | Convert after containment verification |
| `sha1_short` | explicit legacy fingerprint evidence | Never relabel as SHA-256 |
| total `ok` | `files_ok` | Migrate |
| total `fail` | `files_fail` | Migrate |
| top-error mapping | structured top-error array | Normalize |
| `DiffEntry.file_path` | generalized subject identity | Migrate as file subject |
| diagnostic class `script_error` | `error_kind=SCRIPT` plus causal class | Evidence-based migration |
| diagnostic class `framework_error` | technical error kind plus causal class | Evidence-based migration |
| `# GF Audit Summary` | `# GF Wordbench Audit Summary` | Historical human report only |
| language identity in GUI state | `project.toml` | Ignore during state migration |

Canonical writers emit none of the legacy forms.

---

## 11. CLI compatibility

Canonical command:

```text
gf-wordbench
```

Canonical command and option names are governed by `docs/usage/CLI_REFERENCE.md`.

Compatible changes include:

- adding an optional command or flag;
- accepting another safe path spelling;
- improving invalid-input diagnostics;
- adding a documented alias;
- adding an explicit positive/negative Boolean pair.

Breaking changes include:

- removing a stable command without migration;
- reusing a command or option for another meaning;
- changing a value type;
- adding a required positional argument;
- changing path-base interpretation;
- changing a default that materially changes validation or artifacts;
- allowing an option to bypass required release guarantees.

Automation uses:

- exit codes;
- `summary.json`;
- `manifest.json`;
- documented artifact paths.

Human terminal prose is not a machine API.

---

## 12. Exit-code compatibility

Canonical codes:

```text
0 = command succeeded and all required criteria passed
1 = command completed but required criteria failed
2 = invocation or pre-execution configuration was invalid
3 = runtime, external-tool, I/O or integrity error
4 = controlled cancellation
```

These meanings are stable within the compatibility line.

Wordbench never forwards a child GF code directly.

Compatible changes may classify a newly detected condition under an existing definition.

Breaking changes include:

- reusing a number for another meaning;
- returning `0` for a required failure;
- collapsing runtime errors into validation failure;
- relabeling timeout as cancellation.

A new allocated code requires explicit contract and CI review while preserving meanings `0` through `4`.

---

## 13. Python API compatibility

A symbol is public only when:

- documented as public;
- exported through an owner-controlled surface;
- declared by an interfile contract;
- covered by compatibility tests.

Importability alone does not create a public promise.

Compatible function changes include:

- adding a keyword-only optional parameter with a safe default;
- broadening equivalent path-like input;
- adding a public helper;
- improving validation of already invalid input.

Breaking changes include:

- renaming or removing a public function;
- changing positional order;
- making an optional parameter required;
- changing return type or meaning;
- mutating previously immutable input;
- changing documented exception categories;
- adding hidden environment dependence.

A compatibility wrapper may delegate to the canonical function and emit a deprecation warning.

Stable models favor keyword construction.

---

## 14. Shared model compatibility

Key models include:

```text
RunConfig
RunPaths
ScanCounts
SourceFingerprint
ProcessResult
CompileResult
FileResult
ScenarioResult
DiffEntry
TopError
RunResult
```

A stable field has:

- one name;
- one type;
- one meaning;
- a documented optional default;
- centralized serialization.

Adding an optional field is compatible when old data can omit it safely.

Removing, renaming or changing a field's type requires schema and migration review.

Adding an enum value requires at least a compatible schema update and consumer review because strict readers may reject unknown values.

Redundant compatibility fields may coexist temporarily only when coherence is validated and one canonical field remains authoritative.

---

## 15. `RunConfig`

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Legacy inputs:

```text
file
all
```

normalize at the boundary.

Language-specific configuration belongs to:

```text
project/project.toml
```

A new optional run field needs a safe default.

A new required project field requires:

- project schema migration;
- template update;
- active-project migration guidance;
- clear errors for unmigrated projects.

Changing a hidden default is compatibility-sensitive when it changes behavior, evidence or artifact production.

---

## 16. Run paths and layout

Stable artifact names:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
```

Stable directory roles:

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

Canonical run-directory pattern:

```text
run_<run-id>
```

Readers must not derive complete run metadata from the directory name.

Changing a stable path, ownership role or path base is breaking unless a documented migration preserves consumers.

Persisted project-relative and run-relative paths use `/`.

Legacy absolute paths are converted only after containment verification.

---

## 17. Project configuration

Canonical schema:

```text
gf-wordbench.project/1.0
```

Project identity includes:

```text
project ID
display name
language code
source root
entrypoints
checkpoints
required scenarios
release targets
```

Compatible project changes may add optional scenarios, metadata or checkpoints without redefining existing meaning.

Project migration is required for changes such as:

- project ID or language-code replacement;
- source-root base changes;
- module suffix or module-name changes;
- required entrypoint removal;
- scenario-ID renaming;
- required gold-contract changes;
- release artifact identity changes;
- new mandatory configuration fields.

A project migration coordinates:

```text
project.toml
GF module filenames and declarations
imports
entrypoints
scenarios
gold files
dependency maps
project documentation
release evidence
```

Normal validation never silently rewrites project semantics.

---

## 18. Application state

Canonical state:

```text
.gf_wordbench_state.json
gf-wordbench.app-state/1.0
```

Legacy state:

```text
.gf_audit_state.json
```

may be imported by the state adapter.

State stores disposable machine-local preferences.

It is not authoritative for:

- active project identity;
- entrypoints;
- scenarios;
- release policy;
- active execution objects.

Migration:

1. reads legacy state without modifying it;
2. extracts supported preferences;
3. discards duplicated project facts;
4. writes canonical state atomically;
5. reports ignored fields.

Malformed state is ignored or quarantined and never blocks CLI validation.

---

## 19. Run-summary compatibility

Canonical schema:

```text
gf-wordbench.run-summary/1.x
```

Supported predecessor forms may include:

```text
unversioned flat GF Audit summary
unversioned nested GF Audit summary
```

The reader:

- detects the form;
- validates available meaning;
- migrates to a canonical in-memory model;
- records warnings and losses;
- does not rewrite the source automatically.

Typical mappings:

```text
mode=file -> quick
mode=all -> diagnostic
ok -> files_ok
fail -> files_fail
ai_brief_path -> artifacts.ai_ready
top-error mapping -> structured array
file-only diff entry -> generalized file subject
absolute run paths -> verified run-relative paths
sha1_short -> explicit legacy evidence
```

Historical runs without scenarios use empty scenario collections plus an explicit “unavailable” compatibility note.

They do not claim that scenarios passed.

Missing or unrecoverable required meaning remains unknown or invalid, never fabricated as success.

---

## 20. Manifest compatibility

Canonical schema:

```text
gf-wordbench.artifact-manifest/1.x
```

Adding an optional role is compatible under schema policy.

Changing a role's meaning, path identity or hash semantics is compatibility-sensitive.

Hash entries identify their algorithm explicitly.

Runs created before manifest support may remain readable but are not equivalent to manifest-verified release evidence.

Reports state:

```text
legacy run: manifest unavailable
```

---

## 21. Scenario output and normalization

Normalized scenario output has:

- UTF-8 encoding;
- LF newlines;
- stable marker handling;
- a normalization identity or version;
- deterministic content when exact gold comparison applies.

A normalization change is compatible only when comparison meaning cannot change.

A meaning-changing normalization update requires:

- normalization version change;
- explicit gold review;
- fixture updates;
- compatibility tests;
- release notes.

Marker changes affect scripts, runner logic, normalized output, gold files and reports.

A transition may read both forms, while canonical scenarios emit only the current form.

Historical output without equivalent completion proof remains raw evidence, not confirmed scenario success.

---

## 22. Gold compatibility

Gold files are reviewed active-project expectations.

Framework upgrades do not rewrite them automatically.

A gold-impacting change requires:

- explicit expected-versus-actual diff;
- human review;
- documented reason;
- version-control update;
- scenario validation;
- release review.

Reasons distinguish:

```text
linguistic change
normalization change
GF-version presentation change
bug fix
```

Legacy gold is imported only when encoding, normalization and marker semantics are known to be equivalent.

Otherwise, use an explicit reviewed gold-update workflow.

---

## 23. Human-report compatibility

Human reports use documented soft schemas.

### `summary.md`

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

### `AI_READY.md`

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
Ready Prompt For AI
```

### `top_errors.txt`

Canonical line format:

```text
<count>\t<error-kind>\t<message>
```

Compatible report changes may add optional sections or improve prose.

Removing or renaming a required heading, changing its meaning or making Markdown machine-authoritative is breaking.

Readers use `summary.json` when structured data exists.

---

## 24. Regression comparison

Canonical diff identity includes:

```text
subject_kind
subject_id
previous_status
current_status
change_kind
message
```

Legacy `DiffEntry.file_path` maps to:

```text
subject_kind = file
subject_id = normalized file path
```

Canonical change kinds:

```text
unchanged
improved
regressed
new
removed
```

Their meanings must not be reused.

Incompatible baselines are rejected or skipped explicitly.

---

## 25. Diagnostic compatibility

Canonical causal classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Canonical technical error kinds are governed by `docs/reference/DIAGNOSTIC_KINDS.md`.

Legacy values such as:

```text
script_error
framework_error
```

are not emitted canonically.

Migration separates:

```text
technical nature -> error_kind
causal relationship -> diagnostic_class
```

Diagnostic parser improvements are compatible when raw evidence and public meanings remain unchanged.

Redefining `direct`, `downstream` or status semantics requires coordinated compatibility review.

---

## 26. External GF compatibility

Wordbench records:

```text
minimum supported GF version
tested GF versions
known incompatible GF versions
```

For an unknown newer version, policy may:

- warn;
- probe required capabilities;
- continue when the command contract is satisfied;
- record the exact version.

Strict or release policy may reject it.

An older version lacking required capabilities is rejected before validation.

Command adapters use:

- version-gated argument construction;
- capability probes;
- explicit equivalent commands.

Silent omission of a required option is prohibited.

Compatibility-sensitive external-tool fields include:

```text
executable resolution
argument order
working directory
GF search path
stdin behavior
timeouts and budgets
stdout/stderr interpretation
expected artifacts
```

GF upgrades that change output require preserved raw evidence, verified semantic comparison, parser or normalization review, gold review and version-labeled integration fixtures.

---

## 27. Operating systems, Python and dependencies

Each release documents tested:

```text
operating systems
Python versions
GF versions
```

Supported platforms must pass installation, path, process, timeout and artifact tests.

Canonical persisted relative paths use `/`.

Windows coverage includes drive letters, spaces, Unicode, `.exe`, `.bat`, CRLF input and reparse-point safety.

POSIX coverage includes executable permissions, signals, symlinks and shell-independent launch.

Dropping a supported Python or operating-system version requires release-note and compatibility review.

Dependency updates are compatible only when documented behavior, platform ranges and persisted output remain compatible.

---

## 28. Project template

```text
templates/project/
```

defines the generic starting structure.

Updating the template does not silently modify existing projects.

Compatible template changes include optional documentation, scenario examples and optional configuration fields.

Breaking template changes include:

- moving required directories;
- renaming `project.toml`;
- changing scenario or gold identity;
- requiring new project fields;
- changing release artifact locations.

Such changes require a project migration checklist.

The template remains language-neutral and contains placeholders rather than active Albanian facts.

---

## 29. Active-project responsibility

The framework preserves:

- project schema;
- execution contracts;
- result semantics;
- report schemas;
- migrations;
- template expectations.

The active project preserves or explicitly migrates:

- GF module names;
- imports;
- categories and lincats;
- public constructors and helpers;
- entrypoints;
- scenario IDs;
- gold expectations;
- release targets;
- project documentation contracts.

A framework upgrade never silently renames GF modules or rewrites linguistic gold.

---

## 30. Migration architecture

Migration direction:

```text
older -> current
```

Automatic downgrade is not required.

For several major versions, stepwise migration is preferred:

```text
v1 -> v2 -> v3
```

Readers may migrate in memory without rewriting the source.

An explicit persisted migration command:

- preserves the source;
- writes atomically;
- validates the destination;
- reports warnings and losses;
- is idempotent.

Conceptual migration result:

```json
{
  "source_schema": "gf-audit.run-summary",
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

Migration statuses:

```text
unchanged
migrated
migrated_with_warnings
failed
```

Required meaning loss prevents unqualified migration success.

---

## 31. Migration safety

A migrator must:

- read source without modifying it;
- validate available source meaning;
- cap input size;
- use safe JSON, TOML or text parsing;
- avoid arbitrary object deserialization;
- preserve unknown fields only under explicit policy;
- write to a separate or atomically replaced destination;
- verify the result;
- reject path traversal;
- never execute migrated content;
- avoid propagating secrets.

Potential losses include:

```text
absolute path cannot be made relative
legacy status has no equivalent
timestamp lacks timezone
raw artifact missing
truncated SHA-1 cannot become SHA-256
scenario data never existed
artifact path is ambiguous
top-error count malformed
duplicate identity collapsed
module suffix unknown
```

Each loss records:

- field or subject;
- original value when safe;
- reason;
- canonical fallback;
- reliability impact.

Unknown validation never becomes `OK`.

---

## 32. Idempotence and adapters

Repeated migration must not:

- duplicate entries;
- change identity;
- repeatedly increment versions;
- rewrite gold;
- change already canonical meaning.

Canonical input produces:

```text
status = unchanged
```

An adapter is appropriate when an old value maps exactly to one canonical value.

An adapter is inappropriate when:

- semantics changed;
- required evidence is absent;
- security guarantees differ;
- data loss would be hidden;
- mapping is ambiguous.

Ambiguous input requires explicit migration or rejection.

---

## 33. Strict compatibility mode

Strict mode may reject:

- deprecated CLI aliases;
- unversioned persisted data;
- unknown fields or enums where required;
- unknown newer GF versions;
- missing manifests;
- lossy migrations;
- legacy absolute artifact paths;
- unsupported normalization versions.

Strict mode changes acceptance policy, not meaning.

It must not reinterpret legacy values differently from ordinary mode.

---

## 34. Compatibility diagnostics

Structured warnings may use stable categories such as:

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

A warning includes:

```text
code
message
subject
replacement
removal release when applicable
```

Compatibility errors identify:

- detected form;
- expected form;
- supported migration action;
- whether the source changed.

Examples:

```text
unsupported schema major
removed CLI option
unknown required enum
incompatible comparison baseline
unsupported GF capability
unrecoverable project identity
unsafe legacy path
ambiguous migration
required meaning lost
```

---

## 35. Security and correctness

Backward compatibility does not preserve behavior that permits:

- command injection;
- path traversal;
- unsafe deserialization;
- arbitrary host-command execution;
- uncontrolled deletion;
- secret disclosure;
- source or gold overwrite;
- unbounded external execution.

A dangerous legacy interface may be disabled immediately, placed behind an explicit temporary unsafe mode or replaced by a safe adapter.

Stricter rejection of input that was always invalid is normally compatible.

Examples:

- negative timeout;
- duplicate scenario ID;
- path escape;
- downstream classification without evidence;
- `OK` with timeout error.

Release notes remain appropriate where permissive historical behavior was relied upon.

---

## 36. Determinism and reports

Fixing nondeterministic ordering is compatible when the canonical order was already documented.

Canonical examples:

```text
file results -> normalized project-relative path
scenario results -> configured order
diff entries -> severity then subject
top errors -> descending count then message
manifest -> normalized artifact path
entrypoints/checkpoints -> declared order
```

Human report prose may improve without version change when required headings, statuses and artifact paths remain stable.

Machine needs belong in structured schemas rather than frozen prose.

---

## 37. GUI and launcher compatibility

GUI layout is not a machine API.

Stable GUI behavior includes:

- equivalent resolved configuration to CLI;
- identical validation semantics;
- identical run artifacts;
- identical project identity and status;
- no hidden bypass of release rules.

State migration preserves preferences, not pixel layout.

Launchers remain compatible when they:

- invoke the canonical entrypoint;
- forward arguments;
- remain independent of the current working directory;
- propagate the application exit code;
- add no hidden options.

Launchers never become separate implementations.

---

## 38. Compatibility tests

Required categories:

```text
boundary alias tests
legacy schema fixture tests
migration tests
canonical round-trip tests
cross-version reader tests
CLI and exit-code tests
external GF adapter tests
project-template migration tests
report soft-schema tests
Windows path and launcher tests
security regression tests
```

Legacy fixtures live under a clearly historical path such as:

```text
tests/fixtures/legacy/
```

Active framework tests otherwise avoid historical active-language identifiers.

Round-trip tests perform:

```text
construct canonical model
serialize
validate
load
compare semantic equality
serialize again
verify deterministic output
```

Migration tests verify:

```text
source unchanged
target valid
no legacy aliases emitted
warnings and losses expected
idempotence
safe paths
meaning preserved
```

---

## 39. Release compatibility gate

Before a stable release:

```text
[ ] canonical writers emit no legacy aliases
[ ] current schemas validate
[ ] supported previous schemas load
[ ] registered predecessor summaries load
[ ] migration losses are explicit
[ ] supported CLI aliases normalize correctly
[ ] canonical CLI help is current
[ ] exit-code meanings remain stable
[ ] project template matches the project schema
[ ] previous supported project fixture loads or migrates
[ ] summary round trip passes
[ ] manifest verification passes
[ ] scenario normalization compatibility passes
[ ] gold impact is reviewed
[ ] supported GF versions pass
[ ] Windows paths and launchers pass
[ ] security compatibility review passes
[ ] changelog and migration documentation are current
[ ] contract locks agree
[ ] Wordbench remains independent from gf-portfolio
```

A required compatibility failure blocks release unless the release intentionally changes the major contract and supplies complete migration guidance.

---

## 40. Breaking-change procedure

A breaking proposal documents:

```text
affected surface
current contract
new contract
reason compatibility cannot be preserved
affected versions and projects
affected artifacts
security impact
data-loss risk
migration path
deprecation period when applicable
removal release
tests
rollback
```

Coordinated updates include:

```text
implementation
consumers
schema version
migrator
contract locks
CLI and GUI
project template
reports
tests and fixtures
release notes
migration guide
changelog
```

A major release publishes:

- compatibility summary;
- removed interfaces;
- schema and CLI migration tables;
- project migration checklist;
- supported GF/Python/platform matrix;
- non-migratable cases;
- backup guidance;
- release-validation evidence.

---

## 41. Rollback and backups

Migrations preserve source evidence where possible.

Before a major migration, back up:

```text
project/
project/project.toml
validation scenarios
gold files
contract locks
application state when useful
selected release runs
manifested release artifacts
```

A migration records source schema, target schema and tool version.

Rollback does not guarantee that a project using new required features can run on an older framework.

---

## 42. Removing compatibility code

Compatibility code may be removed when:

- its support window ended;
- the replacement is established;
- migration documentation exists;
- supported fixtures no longer require runtime acceptance;
- security constraints permit removal;
- the scheduled release permits it.

Before removal:

- retain useful historical migration fixtures;
- update help, changelog and migration documentation;
- test clear rejection with replacement guidance.

Legacy handling remains isolated:

```text
legacy input
    → detector
    → legacy reader
    → migration adapter
    → canonical model
    → ordinary current system
```

Legacy conditions must not spread through compilers, diagnostics, reports, GUI and current writers.

---

## 43. Documentation

General compatibility policy belongs here.

Exact syntax and fields belong to their owner references.

Compatibility-sensitive changes update the appropriate subset of:

```text
CHANGELOG.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/usage/CLI_REFERENCE.md
docs/reference/EXIT_CODES.md
docs/reference/SCHEMA_INDEX.md
docs/reference/STATUS_VALUES.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/reports/
docs/scenarios/
relevant contract locks
active-project migration documents
```

Internal changes that preserve public contracts do not require broad compatibility documentation updates.

---

## 44. Compatibility matrix

Each release publishes tested support:

| Domain | Supported values |
|---|---|
| GF Wordbench | declared release line |
| Python | tested versions |
| GF | minimum and tested versions |
| Project schema | current and explicitly migratable versions |
| Application-state schema | current and registered legacy import |
| Run-summary schema | current and supported prior/legacy forms |
| Manifest schema | current and supported prior forms |
| Operating systems | tested platforms |
| CLI aliases | documented active alias set |

Untested combinations are not claimed as fully supported.

---

## 45. Examples

### Legacy CLI

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

The boundary emits warnings, constructs canonical `RunConfig` and writes only canonical report values.

### Legacy summary

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

Canonical in-memory form:

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

Warnings identify the unversioned schema, mode alias, path conversion, unavailable error kind and absent scenario data.

### Non-migratable fingerprint

Legacy:

```json
{
  "sha1_short": "a1b2c3d4"
}
```

Correct handling:

```text
preserve as legacy SHA-1 evidence
leave canonical SHA-256 absent
record a loss
```

It is never copied into a SHA-256 field.

### Project identity change

Changing:

```text
project id = sqi
module suffix = Sqi
```

to another active identity requires coordinated project migration across configuration, GF files, module declarations, imports, entrypoints, scenarios, golds, documentation and release artifacts.

It is not a framework alias.

### GF option difference

When a supported GF version lacks an option, Wordbench uses a documented equivalent only when capability evidence proves equivalent behavior.

Otherwise the operation is rejected for that version.

---

## 46. Drift indicators

Compatibility drift exists when:

- canonical writers emit legacy names;
- aliases enter core models;
- readers migrate the same field differently;
- CLI and GUI interpret legacy state differently;
- a schema changes without versioning;
- a required field appears without migration;
- unknown meaning becomes `OK`;
- Markdown becomes a migration source;
- legacy absolute paths bypass containment;
- truncated SHA-1 is labeled SHA-256;
- a GF upgrade silently changes gold meaning;
- an alias disappears without documented replacement;
- exit-code meanings change;
- a template changes without project migration guidance;
- historical language identifiers enter framework defaults;
- migration branches spread into current execution stages;
- a migrator modifies its source;
- loss is hidden;
- strict mode accepts unknown meaning silently;
- supported fixtures are removed too early;
- Wordbench compatibility code depends on `gf-portfolio`.

Any drift indicator requires coordinated correction.

---

## 47. Review checklist

```text
[ ] public surface identified
[ ] owner identified
[ ] consumers identified
[ ] persisted impact reviewed
[ ] CLI and GUI impact reviewed
[ ] Python API impact reviewed
[ ] GF version impact reviewed
[ ] project-template impact reviewed
[ ] active-project impact reviewed
[ ] security impact reviewed
[ ] schema version changed when required
[ ] migration or adapter defined
[ ] canonical writer emits only canonical form
[ ] legacy reader remains isolated
[ ] warnings and losses are explicit
[ ] tests and fixtures added
[ ] changelog and migration guide updated
[ ] contract locks updated
[ ] removal release documented when applicable
[ ] Wordbench/Portfolio boundary preserved
```

---

## 48. Conformance checklist

```text
[ ] framework versions follow semantic versioning
[ ] persisted schemas have explicit IDs and versions
[ ] canonical writers emit no legacy aliases
[ ] current readers load the supported schema set
[ ] registered predecessor state imports safely
[ ] registered flat and nested summaries migrate
[ ] file/all normalize to quick/diagnostic
[ ] ai_brief_path migration is tested
[ ] absolute artifact conversion verifies containment
[ ] legacy fingerprints are not mislabeled
[ ] top-error mappings normalize deterministically
[ ] legacy diff entries gain explicit subject identity
[ ] legacy diagnostic classes migrate from evidence
[ ] missing scenario history remains explicit
[ ] CLI aliases warn and normalize
[ ] exit-code meanings 0–4 remain stable
[ ] project migration is explicit
[ ] application state does not own project identity
[ ] report soft schemas are tested
[ ] normalization versions are enforced
[ ] gold changes remain explicit
[ ] GF capability adapters are tested
[ ] strict mode rejects unsupported meaning
[ ] migrators preserve source and are idempotent
[ ] warnings and losses are structured
[ ] supported project fixtures load or migrate
[ ] Windows paths and launchers remain compatible
[ ] security may reject unsafe historical behavior
[ ] release compatibility gate passes
```

---

## 49. Related documents

```text
CHANGELOG.md
SECURITY.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
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
docs/reports/AI_READY_REFERENCE.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/usage/CLI_REFERENCE.md
docs/reference/EXIT_CODES.md
docs/reference/SCHEMA_INDEX.md
docs/reference/STATUS_VALUES.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 50. Enforcement

GF Wordbench keeps one canonical architecture and isolates compatibility at its boundaries.

Therefore:

> Accept documented historical inputs only through tested readers, aliases or migrations; convert them into one canonical model; emit only current versioned forms; report every ambiguity or loss; preserve security and correctness; and prevent legacy behavior from spreading through the current system.
