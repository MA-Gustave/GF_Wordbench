# GF Wordbench — Schema Index

**Document ID:** `GF-WB-REFERENCE-SCHEMA-INDEX`  
**Status:** Normative schema registry and navigation reference  
**Applies to:** GF Wordbench persisted configuration, application state, run artifacts, scenario outputs, gold expectations, human reports, migrations, and external readers  
**Owner:** GF Wordbench maintainers  
**Canonical path:** `docs/reference/SCHEMA_INDEX.md`  
**Document version:** `1.1.0`  
**Registry source:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Product-boundary authority:** ADR-0001, ADR-0011 and ADR-0012  
**Last reviewed:** 2026-08-05

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

This document is the central index of every persisted GF Wordbench format.

It answers:

- which schemas exist;
- which paths they govern;
- which version is canonical;
- which component owns each writer;
- which components may read each format;
- whether a format is canonical, soft, embedded, deprecated, or legacy-readable;
- which migration path applies;
- which formats canonical writers emit;
- which formats remain read-only compatibility inputs;
- which documents define full field-level behavior.

This document is an index.

The normative field definitions, compatibility rules, migration rules, and serialization requirements are owned by:

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Detailed format references may add examples and explanations, but must not contradict the schema lock.

---

## 2. Core registry rule

> Every persisted format must have one identity, one version policy, one writer owner, and a documented reader/migration policy.

No new canonical persisted format may be introduced without:

```text
schema identity
schema version
canonical path or pattern
writer owner
reader list
encoding
compatibility policy
migration policy
tests
registry entry
```

No new unversioned machine-readable schema is permitted.

GF Wordbench schemas describe exactly one selected language context and one run at a time. They must not contain a Portfolio workspace registry, cross-workspace aggregation state, portfolio readiness, or `gf-portfolio` private configuration.

`gf-portfolio` may consume finalized public Wordbench artifacts through versioned read-only contracts. Wordbench does not require Portfolio storage, runtime, services, schemas, or availability.

---

## 3. Schema categories

GF Wordbench distinguishes five schema categories.

### 3.1 Machine-readable root schemas

Top-level JSON or TOML documents containing:

```text
schema_id
schema_version
```

### 3.2 Canonical text schemas

Versioned text files with stable headers and markers.

### 3.3 Embedded record schemas

Structured records serialized inside a root document.

Examples:

```text
file result
scenario result
diff entry
top-error record
manifest artifact entry
```

These do not necessarily have independent `schema_id` values.

They inherit the version of their root schema unless separately versioned later.

### 3.4 Soft schemas

Human-facing Markdown or plain-text artifacts with:

- a canonical path;
- a required first heading or title;
- required sections;
- stable ownership;
- documented compatibility rules.

They are not primary machine migration sources.

### 3.5 Legacy readable formats

Older formats accepted only for migration or historical loading.

Canonical writers must never emit them.

---

# 4. Canonical schema registry

| Schema ID | Version | Format | Canonical path or pattern | Contract class |
|---|---:|---|---|---|
| `gf-wordbench.project` | `1.0` | TOML | `<validation-profile-root>/project.toml` | Canonical root schema |
| `gf-wordbench.app-state` | `1.0` | JSON | `.gf_wordbench_state.json` | Canonical root schema |
| `gf-wordbench.run-summary` | `1.0` | JSON | `run_<run-id>/summary.json` | Canonical root schema |
| `gf-wordbench.artifact-manifest` | `1.0` | JSON | `run_<run-id>/manifest.json` | Canonical root schema |
| `gf-wordbench.scenario-output` | `1.0` | canonical text | `run_<run-id>/raw/scenarios/<scenario-id>.out` | Canonical text schema |
| `gf-wordbench.scenario-gold` | `1.0` | canonical text | `<validation-profile-root>/validation/gold/<scenario-id>.gold` | Canonical text schema |

Every canonical schema requires:

```text
[ ] one writer owner
[ ] documented readers
[ ] field and path validation
[ ] deterministic serialization
[ ] migration behavior where required
[ ] contract tests
[ ] registry and lock agreement
```

---

# 5. Legacy compatibility registry

| Legacy identity | Source path or pattern | Canonical replacement | Reader policy | Writer policy |
|---|---|---|---|---|
| `gf-audit.state-legacy` | `.gf_audit_state.json` | `gf-wordbench.app-state/1.0` | Import and migrate | Never write |
| unversioned GF Audit state | `.gf_audit_state.json` or historical equivalent | `gf-wordbench.app-state/1.0` | Read legacy fields with warnings | Never write |
| `gf-audit.run-summary-current` | historical nested `run_<id>/summary.json` | `gf-wordbench.run-summary/1.0` | Read and migrate | Never write |
| `gf-audit.run-summary-legacy` | historical flat `run_<id>/summary.json` | `gf-wordbench.run-summary/1.0` | Read and migrate | Never write |
| `mode=file` | state or historical summary | `mode=quick` | Read alias | Emit `quick` |
| `mode=all` | state or historical summary | `mode=diagnostic` | Read alias | Emit `diagnostic` |
| `ai_brief_path` | historical summary | `artifacts.ai_ready` | Read alias | Never write |
| absolute `ai_ready_path` | historical summary | run-relative `artifacts.ai_ready` | Convert where possible | Emit run-relative path |
| short SHA-1 fingerprint | historical file result | SHA-256 fingerprint fields | Import only | Emit SHA-256 |
| total `ok` | historical summary | `files_ok` | Rename during migration | Emit `files_ok` |
| total `fail` | historical summary | `files_fail` | Rename during migration | Emit canonical totals |
| top-error mapping | historical summary | ordered top-error array | Normalize during migration | Emit array |
| language fields in GUI state | legacy state | `<validation-profile-root>/project.toml` | Discard after project config is authoritative | Never write to state |

Legacy aliases must not become canonical again.

---

# 6. Global schema rules

## 6.1 Identity

Every canonical machine-readable root document must contain:

```text
schema_id
schema_version
```

`schema_id` identifies the format.

It does not identify:

- the application release;
- the project release;
- the GF version;
- the document version.

---

## 6.2 Version format

Schema versions use:

```text
MAJOR.MINOR
```

Examples:

```text
1.0
1.1
2.0
```

Rules:

- increment `MAJOR` for incompatible changes;
- increment `MINOR` for backward-compatible optional additions;
- do not infer schema version from the GF Wordbench package version;
- do not add undocumented patch components.

---

## 6.3 Producer metadata

Canonical JSON documents contain:

```json
{
  "producer": {
    "name": "gf-wordbench",
    "version": "<framework-version>"
  }
}
```

The producer version records which application wrote the file.

It does not replace `schema_version`.

---

## 6.4 Encoding

All canonical text formats use:

```text
UTF-8 without BOM
```

Readers may accept a UTF-8 BOM for legacy compatibility.

Canonical writers must not emit it.

---

## 6.5 Newlines

Canonical text writers use:

```text
LF
```

Readers accept:

```text
LF
CRLF
```

A terminating newline is required for:

```text
.gold files
normalized .out files
Markdown reports
plain-text reports
```

---

## 6.6 JSON restrictions

Canonical JSON writers must:

- write one object at the root;
- use valid JSON;
- preserve Unicode;
- emit booleans as JSON booleans;
- emit absence as `null`;
- never emit `NaN`;
- never emit positive or negative infinity;
- serialize timestamps as strings;
- serialize paths as strings;
- serialize sets as deterministically ordered arrays;
- use stable indentation.

---

## 6.7 Paths

Path roles determine representation.

### Project-owned portable paths

Use project-relative paths with `/`.

### Run-owned paths

Use paths relative to the run directory with `/`.

### Machine-local state paths

May be absolute.

Canonical writers normalize separators to `/`.

### Raw external output

May retain native paths emitted by GF.

---

## 6.8 Timestamps

Canonical timestamps must:

- include a timezone;
- use UTC where required;
- use RFC 3339-compatible text;
- avoid naive local timestamps in canonical output.

Canonical form:

```text
2026-07-22T14:32:10Z
```

---

## 6.9 Deterministic ordering

Required canonical order:

| Collection | Order |
|---|---|
| `file_results` | normalized `file_path` |
| `scenario_results` | project scenario execution order |
| `diff_entries` | severity rank, then stable path/identity |
| `top_errors` | descending count, then case-insensitive message |
| manifest entries | normalized artifact path |
| entrypoints | declared configuration order |
| checkpoints | declared configuration order |
| unordered path inventories | lexical path order |

JSON object key order is not semantically significant.

---

## 6.10 Unknown fields

For a supported major version:

- readers should ignore unknown optional fields;
- readers must validate required fields;
- readers must not reinterpret unknown enum values;
- writers must not copy unknown fields into a new document unless migration policy requires preservation.

---

## 6.11 Missing versus `null`

A missing field and a field set to `null` are not automatically equivalent.

Each schema defines:

- required fields;
- optional fields;
- default behavior;
- allowed `null` values.

---

## 6.12 Atomic writes

Canonical writers for:

```text
project migration
application state
run summary
artifact manifest
gold update
```

must use atomic replacement where supported:

1. write a sibling temporary file;
2. flush and close;
3. validate;
4. replace the destination.

A failed write must not destroy the last valid file.

---

## 6.13 Secrets

Persisted files must not contain:

```text
passwords
access tokens
private keys
authentication cookies
complete environment dumps
secret command-line values
```

Local absolute paths are not automatically secrets.

Portable exports may redact them under explicit policy.

---

# 7. `gf-wordbench.project/1.0`

## 7.1 Identity

```text
schema_id: gf-wordbench.project
schema_version: 1.0
```

## 7.2 Canonical path

```text
<validation-profile-root>/project.toml
```

## 7.3 Format

```text
TOML
UTF-8 without BOM
LF
```

## 7.4 Purpose

Defines the single active language project in one GF Wordbench workspace.

It contains portable project facts and validation policy.

It must not contain transient GUI state.

## 7.5 Owner

```text
active language project
project maintainers
project initializer
explicit project migrator
```

## 7.6 Readers

```text
project loader
bootstrap
validation plan builder
CLI
GUI
contract checker
release gate evaluator
```

Readers do not own the file.

Normal validation must not rewrite it.

## 7.7 Expected domains

```text
project identity
language identity
source roots
source selection rules
GF path additions
entrypoints
checkpoints
required scenarios
optional scenarios
release targets
release criteria references
```

## 7.8 Canonical skeleton

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "<project-id>"
name = "<project-name>"
language_code = "<language-code>"
root = "."

[source]
directory = "<source-directory>"
glob = "**/*.gf"

[gf]
path_additions = []

[entrypoints]
release = []

[checkpoints]
items = []

[validation]
required_scenarios = []
optional_scenarios = []

[release]
required_artifacts = []
```

The complete structure is defined by:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

## 7.9 Compatibility

Breaking examples:

- rename `project.id`;
- change scenario-ID meaning;
- convert ordered arrays to unordered mappings;
- move machine-local environment paths into this file;
- change project-root semantics;
- remove required project domains.

Compatible additions must be optional and have safe defaults.

## 7.10 Migration

Opening a project may propose migration.

It must not silently rewrite `project.toml`.

Migration must be explicit, reviewable, atomic, and backed up according to policy.

---

# 8. `gf-wordbench.app-state/1.0`

## 8.1 Identity

```text
schema_id: gf-wordbench.app-state
schema_version: 1.0
```

## 8.2 Canonical path

```text
.gf_wordbench_state.json
```

## 8.3 Legacy path

```text
.gf_audit_state.json
```

## 8.4 Purpose

Stores disposable local application preferences.

Deleting it must not damage the selected language context.

It is not the project definition.

## 8.5 Writer

```text
application state manager
```

## 8.6 Readers

```text
GUI
bootstrap
local settings workflow
state migration tool
```

## 8.7 Canonical root domains

```text
producer
environment
selection
last_run
```

## 8.8 Canonical skeleton

```json
{
  "schema_id": "gf-wordbench.app-state",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "<framework-version>"
  },
  "environment": {
    "project_root": "C:/work/GF_Wordbench",
    "rgl_root": "C:/work/gf-rgl/src",
    "gf_executable": "C:/tools/gf/gf.exe",
    "output_root": "C:/work/gf-wordbench-runs"
  },
  "selection": {
    "mode": "diagnostic",
    "target_file": "",
    "timeout_sec": 60,
    "max_files": 0,
    "keep_ok_details": false,
    "diff_previous": true,
    "skip_version_probe": false,
    "no_compile": false,
    "emit_cpu_stats": false
  },
  "last_run": {
    "run_dir": null,
    "summary_path": null,
    "status_message": ""
  }
}
```

## 8.9 Allowed contents

Machine-local fields:

```text
project root
RGL root
GF executable
output root
last local selection
last completed run pointers
```

## 8.10 Forbidden contents

Do not persist:

```text
is_running = true
current RunConfig
current RunResult
worker objects
thread objects
cancellation tokens
project entrypoints
project checkpoints
required scenarios
language-specific source rules
secrets
```

Runtime state resets on startup.

## 8.11 Migration

Legacy fields may be mapped as follows:

```text
selected_* local paths → environment
selected_* run preferences → selection
last_* pointers → last_run
mode=file → quick
mode=all → diagnostic
profile-owned source fields → discarded
is_running → discarded
```

The legacy file remains untouched until canonical state is written successfully.

---

# 9. Run directory contract

The run directory is a persisted layout contract.

It is not a root schema ID by itself.

## 9.1 Directory name

```text
run_<run-id>
```

Canonical v1 run ID:

```text
YYYYMMDD_HHMMSS
```

The timestamp represents UTC.

Collision example:

```text
run_20260722_143210
run_20260722_143210_02
```

## 9.2 Canonical layout

```text
run_<run-id>/
├── summary.json
├── summary.md
├── AI_READY.md
├── top_errors.txt
├── manifest.json
├── details/
├── raw/
│   ├── master.log
│   ├── ALL_SCAN_LOGS.TXT
│   ├── ALL_LOGS.TXT
│   ├── gf_version.out.txt
│   ├── gf_version.err.txt
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

## 9.3 Ownership

| Path | Owner |
|---|---|
| `summary.json` | JSON report writer |
| `summary.md` | Markdown report writer |
| `AI_READY.md` | AI report writer |
| `top_errors.txt` | report/log writer |
| `manifest.json` | manifest writer |
| `details/` | detail report writer |
| `raw/master.log` | runs module |
| `raw/compile/` | validation module and process adapter |
| `raw/scan/` | validation module |
| `raw/scenarios/` | validation module and process adapter |
| `artifacts/gfo/` | validation module |
| `artifacts/out/` | owning module through the artifact service |
| `artifacts/pgf/` | validation module |

No observer may rewrite another component’s artifact.

## 9.4 Run-relative artifact paths

Canonical summary paths use stable semantic keys such as:

```json
{
  "summary_json": "summary.json",
  "summary_markdown": "summary.md",
  "ai_ready": "AI_READY.md",
  "top_errors": "top_errors.txt",
  "manifest": "manifest.json",
  "master_log": "raw/master.log",
  "all_scan_logs": "raw/ALL_SCAN_LOGS.TXT",
  "all_logs": "raw/ALL_LOGS.TXT",
  "details_dir": "details",
  "raw_dir": "raw",
  "compile_logs_dir": "raw/compile",
  "scan_logs_dir": "raw/scan",
  "scenario_logs_dir": "raw/scenarios",
  "artifacts_dir": "artifacts",
  "gfo_dir": "artifacts/gfo",
  "out_dir": "artifacts/out",
  "pgf_dir": "artifacts/pgf"
}
```

Consumers must read owned path fields instead of reconstructing filenames.

---

# 10. `gf-wordbench.run-summary/1.0`

## 10.1 Identity

```text
schema_id: gf-wordbench.run-summary
schema_version: 1.0
```

## 10.2 Canonical path

```text
run_<run-id>/summary.json
```

## 10.3 Purpose

Primary machine-readable record of one validation run.

It is the source for:

```text
previous-run comparison
automation
GUI result loading
report verification
AI handoff metadata
historical analysis
migration
```

Human Markdown reports must not replace it.

## 10.4 Writer

```text
JSON report writer
```

## 10.5 Readers

```text
diff loader
GUI result loader
CLI summary presenter
automation
migration tools
schema validator
report verifier
export tooling
external consumers of finalized public artifacts, including `gf-portfolio`
```

## 10.6 Canonical root structure

```json
{
  "schema_id": "gf-wordbench.run-summary",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "<framework-version>"
  },
  "metadata": {},
  "totals": {},
  "artifacts": {},
  "file_results": [],
  "scenario_results": [],
  "diff_entries": [],
  "top_errors": []
}
```

## 10.7 Required root domains

```text
schema_id
schema_version
producer
metadata
totals
artifacts
file_results
scenario_results
diff_entries
top_errors
```

## 10.8 Metadata domain

Expected concepts include:

```text
run ID
project ID
mode
overall status
started_at
finished_at
duration
GF executable
GF version
source/project root references
normalization version
framework version
optional source revision
```

## 10.9 Totals domain

Canonical totals distinguish:

```text
files_included
files_ok
files_fail
files_error
files_skipped
scenarios_seen
scenarios_ok
scenarios_fail
scenarios_error
scenarios_skipped
direct_failures
downstream_failures
ambiguous_failures
regressions
improvements
```

Exact required fields remain owned by the schema lock.

## 10.10 Artifact domain

Paths are relative to the run directory.

The summary references artifacts.

It does not replace `manifest.json` integrity metadata.

## 10.11 Embedded record types

The root schema contains the embedded records indexed in sections 11–14.

## 10.12 Compatibility

Readers may accept supported legacy summaries through migration.

Canonical writers emit only v1 shape and canonical enum values.

A required-field rename or incompatible type change requires a new schema major version.

---

# 11. Embedded file-result record

## 11.1 Root owner

```text
gf-wordbench.run-summary/1.0
```

## 11.2 Purpose

Represents one selected source-file validation result.

## 11.3 Stable identity

```text
project-relative file_path
```

## 11.4 Expected domains

```text
file_path
module identity when available
validation_status
execution_state
error_kind
diagnostic_class
is_direct
blocked_by
scan counts
fingerprint
compile summary
first_error
error_detail
evidence paths
```

## 11.5 Canonical statuses

Validation:

```text
OK
FAIL
ERROR
SKIPPED
```

Execution:

```text
completed
timed_out
cancelled
launch_failed
```

Diagnostic class:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Error kind:

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

## 11.6 Ordering

File-result arrays are sorted by normalized `file_path`.

## 11.7 Ownership

Producer:

```text
result-model assembly
```

Evidence owners remain:

```text
scanner
compiler
process runner
classifier
```

The result assembler must not fabricate missing evidence.

---

# 12. Embedded scenario-result record

## 12.1 Root owner

```text
gf-wordbench.run-summary/1.0
```

## 12.2 Stable identity

```text
scenario_id
```

## 12.3 Expected domains

```text
scenario_id
required
validation_status
execution_state
error_kind
diagnostic_class
blocked_by
stdout_path
stderr_path
normalized_output_path
gold_path
gold_match
diff_path
marker results
duration
expected artifact results
```

## 12.4 Ordering

Scenario results follow configured execution order.

They are not sorted alphabetically unless configuration order is alphabetical.

## 12.5 Missing optional data

A scenario without gold comparison uses an explicit absent/null value according to the root schema.

It must not report a false match.

---

# 13. Embedded diff-entry record

## 13.1 Root owner

```text
gf-wordbench.run-summary/1.0
```

## 13.2 Purpose

Represents the relationship between one current subject and a compatible previous run.

## 13.3 Canonical change kinds

```text
unchanged
improved
regressed
new
removed
```

## 13.4 Stable identity

Examples:

```text
file:<project-relative-path>
scenario:<scenario-id>
artifact:<artifact-role-or-path>
```

## 13.5 Ordering

```text
severity rank
then stable path or identity
```

## 13.6 Compatibility

A previous run must be compatible by project identity and supported schema/migration policy.

Diff loading failure must not corrupt current results.

---

# 14. Embedded top-error record

## 14.1 Root owner

```text
gf-wordbench.run-summary/1.0
```

## 14.2 Purpose

Provides deterministic grouped diagnostic triage.

## 14.3 Expected fields

```text
error_kind
message
count
optional subject references
```

## 14.4 Ordering

```text
descending count
then case-insensitive message
then stable error kind
```

## 14.5 Legacy migration

Historical mappings are normalized into an ordered array.

Canonical writers do not emit a mapping.

Top errors are summaries.

They do not replace item-level evidence.

---

# 15. `gf-wordbench.artifact-manifest/1.0`

## 15.1 Identity

```text
schema_id: gf-wordbench.artifact-manifest
schema_version: 1.0
```

## 15.2 Canonical path

```text
run_<run-id>/manifest.json
```

## 15.3 Purpose

Defines the finalized artifact set for a run and proves integrity.

## 15.4 Writer

```text
designated manifest writer
```

## 15.5 Readers

```text
manifest verifier
GUI
cleanup tooling
archive tooling
export tooling
release validator
historical integrity checker
```

## 15.6 Canonical skeleton

```json
{
  "schema_id": "gf-wordbench.artifact-manifest",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "<framework-version>"
  },
  "run_id": "20260722_143210",
  "generated_at": "2026-07-22T14:32:11Z",
  "hash_algorithm": "sha256",
  "artifacts": [
    {
      "path": "summary.json",
      "role": "machine_summary",
      "media_type": "application/json",
      "required": true,
      "size_bytes": 12345,
      "sha256": "<64-lowercase-hex>",
      "created_by": "report_json"
    }
  ]
}
```

## 15.7 Artifact-entry schema

Each entry includes:

```text
path
role
media_type
required
size_bytes
sha256
created_by
```

Additional optional metadata requires a schema-minor review.

## 15.8 Rules

- paths are run-relative;
- paths are unique;
- directories are not artifact entries;
- required artifacts must exist;
- hashes use SHA-256;
- empty files are valid artifacts when expected;
- the manifest does not hash itself;
- strict mode rejects escaping symlinks;
- entries are sorted by normalized path;
- hashes are computed from finalized bytes.

## 15.9 Failure meaning

A modified or missing required artifact makes the run integrity-invalid.

The verifier must not silently repair or ignore the mismatch.

---

# 16. `gf-wordbench.scenario-output/1.0`

## 16.1 Identity

```text
schema_id: gf-wordbench.scenario-output
schema_version: 1.0
```

This identity is represented by the stable text header rather than JSON root fields.

## 16.2 Canonical path

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

## 16.3 Format

```text
canonical text
UTF-8 without BOM
LF
terminating newline
```

## 16.4 Canonical skeleton

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN parse-basic ---
<normalized GF output>
--- END parse-basic ---
```

## 16.5 Writer

```text
scenario normalizer / scenario runner
```

## 16.6 Readers

```text
marker verifier
gold comparator
scenario report writer
AI-ready report writer
schema validator
```

## 16.7 Rules

- one stable header;
- scenario ID matches the configured scenario;
- normalization version is explicit;
- section IDs are unique;
- begin/end markers are exact;
- section order follows execution;
- CRLF is normalized to LF;
- unstable approved paths may be replaced;
- ANSI control sequences may be removed;
- trailing spaces may be removed;
- meaningful GF output and Unicode must remain;
- missing end marker invalidates the output.

## 16.8 Allowed replacement tokens

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

A normalizer must not replace arbitrary linguistic text.

## 16.9 Source relationship

The normalized output is derived from:

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

It must not overwrite either raw stream.

---

# 17. `gf-wordbench.scenario-gold/1.0`

## 17.1 Identity

```text
schema_id: gf-wordbench.scenario-gold
schema_version: 1.0
```

This identity is represented by the stable text header.

## 17.2 Canonical path

```text
<validation-profile-root>/validation/gold/<scenario-id>.gold
```

## 17.3 Format

```text
canonical text
UTF-8 without BOM
LF
terminating newline
```

## 17.4 Canonical skeleton

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN parse-basic ---
<expected normalized GF output>
--- END parse-basic ---
```

## 17.5 Writer

```text
explicit gold-update workflow
project maintainer
```

## 17.6 Readers

```text
gold comparator
schema validator
release gate evaluator
project review tooling
```

## 17.7 Invariants

- scenario ID matches filename and project registry;
- normalization version matches actual output;
- exact comparison follows newline normalization;
- normal validation is read-only;
- missing required gold is a failure;
- gold update is explicit;
- update writes atomically;
- update shows or stores a diff;
- required gold is version-controlled;
- empty gold is valid only when documented;
- normalization-version changes require reviewing affected gold files.

## 17.8 Explicit update operation

`docs/usage/CLI_REFERENCE.md` owns the exact command surface for gold updates.

The operation requires a scenario ID, shows or stores the diff, writes atomically and records the profile-owned decision evidence.

A standard validation command must not update gold.

---

# 18. Soft schema: `summary.md`

## 18.1 Path

```text
run_<run-id>/summary.md
```

## 18.2 Owner

```text
Markdown report writer
```

## 18.3 Readers

```text
humans
GUI text/open action
documentation and support workflows
```

Automation must use `summary.json`.

## 18.4 Required first heading

```text
# GF Wordbench Audit Summary
```

## 18.5 Required sections

```text
Run Summary
Outcome
File Results
Scenario Results
Regression Comparison
Artifacts
```

An empty section may state:

```text
None
```

## 18.6 Compatibility

- facts derive from `RunResult` / `summary.json`;
- required headings may change only through a major soft-schema revision;
- optional subsections may be added compatibly;
- it must not become a migration source;
- it must not rerun validation.

---

# 19. Soft schema: `AI_READY.md`

## 19.1 Path

```text
run_<run-id>/AI_READY.md
```

## 19.2 Owner

```text
AI report writer
```

## 19.3 Readers

```text
humans
AI systems
support workflows
```

## 19.4 Required first heading

```text
# AI Ready Packet
```

## 19.5 Required sections

```text
Run Summary
Outcome
Diagnosis Snapshot
Failing Files
Failing Scenarios
Evidence
Artifacts
```

## 19.6 Rules

- facts derive from `RunResult`;
- evidence excerpts are bounded;
- raw artifact paths are identified;
- direct/downstream/ambiguous distinctions are preserved;
- no GF execution occurs during report writing;
- the report must not claim certainty absent from structured results.

---

# 20. Soft schema: `top_errors.txt`

## 20.1 Path

```text
run_<run-id>/top_errors.txt
```

## 20.2 Owner

```text
report/log writer
```

## 20.3 Readers

```text
humans
optional external diagnostic tooling
```

## 20.4 Purpose

Provides a compact deterministic rendering of grouped top errors.

## 20.5 Rules

- derived from structured top-error records;
- does not replace item results;
- does not replace raw logs;
- stable ordering follows count and message rules;
- canonical UTF-8, LF, and terminating newline apply.

The exact textual rendering is a soft schema unless a machine parser is formally introduced.

---

# 21. Soft schema: `raw/master.log`

## 21.1 Path

```text
run_<run-id>/raw/master.log
```

## 21.2 Owner

```text
audit orchestration / lifecycle logger
```

## 21.3 Purpose

Chronological lifecycle evidence.

## 21.4 Canonical line format

```text
<RFC3339-UTC> <LEVEL> <EVENT> [key=value ...]
```

## 21.5 Status

Semi-structured soft schema.

Automation should not use it instead of `summary.json`.

## 21.6 Related reference

```text
docs/reports/RAW_LOGS_REFERENCE.md
```

---

# 22. Soft schema: aggregate logs

## 22.1 Scan aggregate

```text
run_<run-id>/raw/ALL_SCAN_LOGS.TXT
```

Owner:

```text
aggregate log writer
```

Purpose:

```text
deterministic concatenation of individual scan logs
```

## 22.2 Operation aggregate

```text
run_<run-id>/raw/ALL_LOGS.TXT
```

Owner:

```text
aggregate log writer
```

Purpose:

```text
deterministic convenience view of operational evidence
```

## 22.3 Authority

Individual logs remain authoritative.

Aggregate logs are reproducible views.

They must not be the only copy of required evidence.

They must not become machine migration sources.

---

# 23. Non-schema persisted artifacts

The following are persisted artifacts but are not themselves root data schemas.

| Artifact | Path | Owner | Contract type |
|---|---|---|---|
| Compile stdout | `raw/compile/<key>.out.txt` | validation module / process adapter | raw evidence |
| Compile stderr | `raw/compile/<key>.err.txt` | validation module / process adapter | raw evidence |
| Scenario stdout | `raw/scenarios/<id>.out.txt` | validation module / process adapter | raw evidence |
| Scenario stderr | `raw/scenarios/<id>.err.txt` | validation module / process adapter | raw evidence |
| GF version stdout | `raw/gf_version.out.txt` | GF adapter / process adapter | raw evidence |
| GF version stderr | `raw/gf_version.err.txt` | GF adapter / process adapter | raw evidence |
| Scan log | `raw/scan/<key>.scan.txt` | validation module | semi-structured evidence |
| Detail report | `details/*` | detail report writer | soft report |
| `.gfo` | `artifacts/gfo/**` | validation module | external binary artifact |
| `.pgf` | `artifacts/pgf/*.pgf` | validation module | external binary artifact |
| Other tool output | `artifacts/out/**` | owning module through the artifact service | external/derived artifact |
| Gold diff | designated run path | gold comparator | derived evidence |

These artifacts are indexed in `manifest.json`.

Any component that parses one of these as a stable machine format must first define a schema or formal contract.

---

# 24. Schema ownership registry

| Persisted asset | Writer | Readers |
|---|---|---|
| `<validation-profile-root>/project.toml` | initializer, migrator, project maintainer | project loader, bootstrap |
| `.gf_wordbench_state.json` | state manager | GUI, bootstrap |
| `summary.json` | JSON report writer | diff, GUI, automation, migration |
| `manifest.json` | manifest writer | verifier, cleanup, export |
| scenario `.out` | scenario normalizer/runner | gold comparator, reports |
| scenario `.gold` | explicit gold updater, maintainer | gold comparator |
| `summary.md` | Markdown report writer | humans |
| `AI_READY.md` | AI report writer | humans, AI systems |
| `top_errors.txt` | report/log writer | humans, optional external tools |
| `master.log` | runs module | humans, aggregate writer |
| individual compile logs | validation module / process adapter | diagnostics, reports |
| individual scan logs | validation module | reports, aggregate writer |
| individual scenario logs | validation module / process adapter | diagnostics, normalizer |
| aggregate logs | aggregate writer | humans, support workflows |

A reader must not rewrite an asset it does not own.

---

# 25. Reader and writer compatibility

## 25.1 Canonical writer rule

Current writers emit only the current canonical version of each root schema.

They must not emit:

```text
unversioned roots
legacy aliases
legacy flat summaries
legacy nested summaries
legacy state paths
old mode names
short SHA-1 canonical fingerprints
```

## 25.2 Reader rule

Readers may accept:

- current canonical formats;
- documented same-major compatible minor versions;
- documented legacy formats through migration.

Readers must reject unsupported major versions clearly.

## 25.3 Reader is not a writer

A normal read operation must not silently rewrite:

```text
project.toml
application state source
historical summary
gold
manifest
```

An explicit migration may create a new canonical file.

---

# 26. Schema compatibility matrix

| Schema | Canonical writer policy | Canonical reader policy | Legacy reader | Migration policy |
|---|---|---|---|---|
| Project `1.0` | Emit `gf-wordbench.project/1.0` only | Validate `1.x`; reject unsupported major versions | project-specific older formats when documented | Explicit |
| App state `1.0` | Emit `gf-wordbench.app-state/1.0` only | Validate `1.x`; tolerate disposable-state recovery | `.gf_audit_state.json`, unversioned flat state | Required when imported |
| Run summary `1.0` | Emit `gf-wordbench.run-summary/1.0` only | Validate `1.x`; reject unreliable required fields | nested and flat GF Audit summaries | Required when imported |
| Manifest `1.0` | Emit `gf-wordbench.artifact-manifest/1.0` only | Verify paths, required files and hashes | none canonical | Not applicable |
| Scenario output `1.0` | Emit versioned normalized output only | Validate header, scenario identity and markers | explicitly supported unversioned transcripts | Regenerate or explicitly import |
| Scenario gold `1.0` | Write only through explicit reviewed update | Validate header, scenario identity and normalization version | explicitly imported legacy expected outputs | Explicit review |

Release support is established by schema validation, migration fixtures and contract tests.

---

# 27. Migration contract

## 27.1 Required behavior

Migration must:

1. identify source format;
2. preserve source bytes;
3. parse conservatively;
4. map known fields;
5. report warnings;
6. report losses;
7. build canonical data in memory;
8. validate target schema;
9. write atomically only when explicitly requested;
10. preserve a backup or unchanged source according to policy.

## 27.2 Migration result

Canonical migration record:

```json
{
  "source_schema": "gf-audit.run-summary-current",
  "source_version": "unversioned",
  "target_schema": "gf-wordbench.run-summary",
  "target_version": "1.0",
  "warnings": [],
  "losses": []
}
```

## 27.3 Loss examples

```text
absolute path cannot be made project-relative
unknown legacy status
malformed top-error count
missing raw artifact
ambiguous AI report path
naive timestamp
missing scenario data
unsupported enum
```

A migration must never claim success when required meaning could not be recovered.

---

# 28. Schema support classes

The registry uses these support classes:

```text
Canonical
Deprecated
Legacy readable
Retired
```

## 28.1 Canonical

The schema is the format emitted by canonical writers and accepted by canonical readers.

Only one canonical version line is emitted for each persisted asset class.

## 28.2 Deprecated

The schema remains readable, and may remain writable only when an explicit compatibility policy requires it.

Every deprecated schema identifies:

```text
replacement
migration path
reader policy
writer policy
removal condition
```

## 28.3 Legacy readable

The format is accepted only as a migration or historical input.

Canonical writers never emit it.

## 28.4 Retired

The format is not accepted by current readers or writers.

Historical preservation may remain outside runtime support.

---

# 29. Schema-version change rules

## 29.1 Major change

Increment schema major when:

- a required field is renamed;
- a field type changes incompatibly;
- a field is removed;
- an enum changes incompatibly;
- path semantics change incompatibly;
- nullability changes incompatibly;
- record identity changes;
- ordering becomes semantically different;
- canonical structure changes incompatibly.

Required work:

```text
new schema version
new reader
migration
tests
lock update
index update
release notes
consumer review
```

## 29.2 Minor change

Increment schema minor when:

- an optional field is added;
- optional metadata is added;
- a compatible optional artifact role is added;
- readers can safely ignore the new field.

If older same-major readers would misinterpret the data, the change is major.

## 29.3 No schema change

No schema bump is required for:

- report prose corrections outside locked sections;
- internal code refactoring;
- JSON key-order changes;
- private in-memory fields not serialized;
- bug fixes that restore the documented representation without changing it.

The framework release version may still change.

---

# 30. Validation commands

`docs/usage/CLI_REFERENCE.md` owns the canonical command names and options for schema validation.

The schema-validation operation performs these checks:

```text
validate project.toml
validate application state
validate run summaries
validate manifests
verify artifact hashes
validate scenario output headers
validate gold headers
detect unsupported versions
detect non-canonical separators
detect absolute profile-owned paths
verify deterministic arrays
verify required files
detect legacy aliases in canonical output
```

The same rules apply to automated validation, tests and explicit manual review.

---

# 31. Required tests

Canonical test directory:

```text
tests/schemas/
```

Required test files:

```text
test_project_schema.py
test_app_state_schema.py
test_summary_schema.py
test_manifest_schema.py
test_scenario_output_schema.py
test_gold_schema.py
test_schema_migrations.py
test_schema_determinism.py
```

## 31.1 Identity/version tests

```text
missing schema_id
wrong schema_id
missing schema_version
unsupported major
supported minor
malformed version
```

## 31.2 Serialization tests

```text
Unicode round trip
Windows path migration
POSIX canonical path
UTC timestamp round trip
empty collections
null optional paths
no NaN/infinity
deterministic arrays
atomic write
```

## 31.3 App-state tests

```text
missing state file
malformed JSON
legacy unversioned state
is_running resets
invalid timeout fallback
runtime objects not persisted
profile-owned fields discarded
```

## 31.4 Summary tests

```text
canonical v1 round trip
legacy nested summary
legacy flat summary
AI path aliases
file-result required fields
count invariants
top-error migration
unknown optional field
unknown enum
missing raw artifact
```

## 31.5 Manifest tests

```text
correct hashes
modified artifact
missing required artifact
duplicate path
escaping path
manifest excludes itself
zero-byte artifact
deterministic ordering
```

## 31.6 Scenario/gold tests

```text
CRLF normalization
missing end marker
wrong scenario ID
wrong normalization version
exact match
mismatch diff
normal run does not modify gold
explicit update writes atomically
```

---

# 32. Schema drift indicators

Persisted-schema drift exists when:

- a writer emits a field its reader does not recognize;
- a reader requires an undocumented field;
- a root shape changes without a version change;
- application state contains profile-owned language configuration;
- two files use different names for one status;
- `top_errors` changes between mapping and array in canonical output;
- one writer uses absolute paths while another uses relative paths for the same role;
- a report reconstructs artifact paths;
- gold changes during normal validation;
- a completed run omits required `manifest.json`;
- a timestamp lacks timezone;
- a count is serialized as text;
- one schema ID is reused for another format;
- a migration overwrites its source;
- a legacy alias becomes canonical;
- a required JSON field is renamed without a major version;
- normalized scenario output lacks a version header;
- a new machine-readable text format is parsed without registry entry;
- a Wordbench schema contains a multi-workspace or Portfolio registry;
- Wordbench requires `gf-portfolio` state or schemas to read its own artifacts.

Drift must be resolved by:

1. restoring the locked schema; or
2. creating a versioned migration and updating this index and the schema lock.

---

# 33. Change workflow

A schema change is complete only when:

```text
[ ] affected schema identified
[ ] compatibility impact classified
[ ] version selected
[ ] writer updated
[ ] all readers updated
[ ] embedded records reviewed
[ ] path rules reviewed
[ ] enums reviewed
[ ] ordering reviewed
[ ] migration written
[ ] loss reporting written
[ ] fixtures added
[ ] unit tests updated
[ ] integration tests updated
[ ] PERSISTED_SCHEMA_LOCK.md updated
[ ] DOCUMENTATION_ALIGNMENT_LOCK.md reviewed
[ ] product-boundary ADRs reviewed
[ ] SCHEMA_INDEX.md updated
[ ] detailed reference updated
[ ] changelog updated
[ ] release compatibility reviewed
```

No persisted-schema change may be applied in one writer only.

---

# 34. Detailed reference map

| Schema or contract | Detailed reference |
|---|---|
| Global persisted rules | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Project TOML | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Application state | `docs/configuration/APPLICATION_STATE_REFERENCE.md` |
| Run summary | `docs/reports/SUMMARY_JSON_REFERENCE.md` |
| Artifact manifest | `docs/reports/ARTIFACT_MANIFEST.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Scenario markers | `docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md` |
| Normalized output | `docs/scenarios/OUTPUT_NORMALIZATION.md` |
| Gold behavior | `docs/scenarios/GOLDEN_TESTS.md` |
| Gold updates | `docs/scenarios/UPDATING_GOLD_FILES.md` |
| Human summary | `docs/reports/SUMMARY_MARKDOWN_REFERENCE.md` |
| AI packet | `docs/reports/AI_READY_REFERENCE.md` |
| Raw logs | `docs/reports/RAW_LOGS_REFERENCE.md` |
| Versioning | `docs/release/VERSIONING_POLICY.md` |
| Migration/deprecation | `docs/release/MIGRATION_AND_DEPRECATION.md` |
| Status enums | `docs/reference/STATUS_VALUES.md` |
| Diagnostic kinds | `docs/reference/DIAGNOSTIC_KINDS.md` |

---

# 35. Quick lookup by file

| File or pattern | Schema/contract |
|---|---|
| `<validation-profile-root>/project.toml` | `gf-wordbench.project/1.0` |
| `.gf_wordbench_state.json` | `gf-wordbench.app-state/1.0` |
| `.gf_audit_state.json` | legacy state |
| `run_<id>/summary.json` | `gf-wordbench.run-summary/1.0` or legacy summary |
| `run_<id>/manifest.json` | `gf-wordbench.artifact-manifest/1.0` |
| `run_<id>/raw/scenarios/*.out` | `gf-wordbench.scenario-output/1.0` |
| `<validation-profile-root>/validation/gold/*.gold` | `gf-wordbench.scenario-gold/1.0` |
| `run_<id>/summary.md` | summary soft schema |
| `run_<id>/AI_READY.md` | AI-ready soft schema |
| `run_<id>/top_errors.txt` | top-errors soft schema |
| `run_<id>/raw/master.log` | lifecycle-log soft schema |
| `run_<id>/raw/ALL_SCAN_LOGS.TXT` | scan aggregate soft schema |
| `run_<id>/raw/ALL_LOGS.TXT` | operation aggregate soft schema |
| `run_<id>/raw/compile/*.out.txt` | raw compile stdout |
| `run_<id>/raw/compile/*.err.txt` | raw compile stderr |
| `run_<id>/raw/scenarios/*.out.txt` | raw scenario stdout |
| `run_<id>/raw/scenarios/*.err.txt` | raw scenario stderr |
| `run_<id>/artifacts/gfo/**` | GF-generated object artifacts |
| `run_<id>/artifacts/pgf/*.pgf` | GF-generated PGF artifacts |

---

# 36. Quick lookup by owner

| Owner | Assets |
|---|---|
| Project maintainers | `project.toml`, reviewed gold |
| Project initializer/migrator | canonical project creation/migration |
| State manager | `.gf_wordbench_state.json` |
| JSON report writer | `summary.json` |
| Manifest writer | `manifest.json` |
| Scenario runner/normalizer | normalized `.out` |
| Gold updater | `.gold` update |
| Markdown report writer | `summary.md` |
| AI report writer | `AI_READY.md` |
| Report/log writer | `top_errors.txt`, aggregate logs |
| Runs module | `master.log` |
| Validation module / process adapter | compile stdout/stderr |
| Validation module | scan logs |
| Validation module | `.gfo` |
| Validation module | `.pgf` |

---

# 37. Quick lookup by reader

| Reader | Schemas/assets consumed |
|---|---|
| Bootstrap | project, app state |
| Project loader | project |
| GUI | app state, run summary, manifest |
| CLI | project, app state/overrides, run summary |
| Diff loader | run summary |
| Automation | run summary, manifest |
| Gold comparator | scenario output, scenario gold |
| Report writers | `RunResult`, evidence references |
| Manifest verifier | manifest and listed artifacts |
| Migration tools | legacy state, legacy summaries, canonical schemas |
| Cleanup/export | manifest, run summary |
| AI workflows | AI packet, summary, selected raw evidence |

---

# 38. Canonical source-of-truth rules

| Question | Source |
|---|---|
| What project is active? | `<validation-profile-root>/project.toml` |
| What local GUI/environment preferences exist? | `.gf_wordbench_state.json` |
| What happened in a run? | `summary.json` |
| Which files belong to the run? | `manifest.json` |
| What exact scenario output was compared? | normalized scenario `.out` |
| What output was expected? | scenario `.gold` |
| What did GF write to stdout/stderr? | individual raw logs |
| What should a human read first? | `summary.md` |
| What should an AI system receive? | `AI_READY.md` plus structured/raw evidence |
| What format versions are supported? | this index and `PERSISTED_SCHEMA_LOCK.md` |
| What may Portfolio consume? | finalized public artifacts defined by Wordbench contracts |

---

# 39. Enforcement rule

Persisted schemas are public contracts across time.

> No persisted field, enum, path convention, artifact name, marker, normalization rule, report identity, or directory layout may change through an isolated code edit.

Every change must be:

```text
identified
versioned
owned
migrated
tested
registered
documented
reviewed
```

This index identifies every canonical schema and every legacy format supported for reading.
