# GF Wordbench — Persisted Schema Lock

**Document ID:** `GF-WB-PERSISTED-SCHEMA-LOCK`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\PERSISTED_SCHEMA_LOCK.md`  
**Applies to:** GF Wordbench persisted configuration, state, run summaries, manifests, scenario outputs, golden expectations and stable report contracts  
**Owner:** GF Wordbench maintainers  
**Schema policy:** Explicit identifiers, explicit versions, deterministic serialization and tested migrations  
**Internal implementation:** Not governed unless it changes persisted data  
**Last structural review:** 2026-07-21

---

## 1. Purpose

This document prevents drift in every format that survives beyond one in-memory operation.

A persisted format creates a contract between:

- the writer that creates it;
- the reader that consumes it now;
- future versions of GF Wordbench;
- automation and external tools;
- previous and later audit runs;
- humans or AI systems that rely on stable sections;
- cloned language projects that must remain loadable.

A local code change is incomplete when it changes persisted data without updating its readers, migrations, tests and this lock.

The core rule is:

> A persisted schema may change only through an explicit, versioned and tested migration.

---

## 2. Scope

This lock governs the following persisted assets.

### 2.1 Machine-readable assets

- `project/project.toml`
- `.gf_wordbench_state.json`
- legacy `.gf_audit_state.json`
- `run_<run-id>/summary.json`
- `run_<run-id>/manifest.json`
- serialized file results
- serialized scenario results
- serialized diff entries
- serialized top-error records

### 2.2 Canonical text assets

- `project/validation/gold/*.gold`
- normalized scenario output files
- scenario transcripts when another component compares or parses them
- stable machine markers inside `.gfs` output

### 2.3 Stable human-facing assets

- `summary.md`
- `AI_READY.md`
- `top_errors.txt`

These Markdown and text reports are not primary machine schemas. Their required identities, ownership and minimum sections are nevertheless locked because users and AI workflows rely on them.

### 2.4 Persistent directory layout

- run directory naming;
- artifact locations;
- raw evidence locations;
- compile, scan and scenario subdirectories;
- report filenames.

---

## 3. Exclusions

This lock does not govern:

- temporary files deleted before a run completes;
- in-memory dataclasses unless they are serialized;
- console wording not consumed by another tool;
- private debug output;
- Python object identity;
- JSON key order;
- Markdown prose outside required stable sections;
- internal helper function names.

An excluded detail becomes governed when a reader begins depending on it.

---

## 4. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **WRITER**: component that owns and creates a persisted asset.
- **READER**: component that loads or interprets the asset.
- **MIGRATOR**: component that converts an older schema into a supported current schema.
- **CANONICAL**: the form emitted by current writers.
- **LEGACY**: an older form accepted only for compatibility.
- **SOFT SCHEMA**: a human-readable format with locked identity and minimum sections, but not a strict field-by-field machine schema.

---

## 5. Global schema rules

### 5.1 Schema identity

Every canonical machine-readable root document MUST contain:

```text
schema_id
schema_version
```

The value of `schema_id` identifies the format, not the application release.

Examples:

```text
gf-wordbench.project
gf-wordbench.app-state
gf-wordbench.run-summary
gf-wordbench.artifact-manifest
```

### 5.2 Schema version format

Schema versions MUST be strings using:

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

- `MAJOR` changes when compatibility is broken.
- `MINOR` changes when optional fields or compatible meanings are added.
- Patch-level application releases do not require schema changes.
- A schema version MUST NOT be inferred from the GF Wordbench package version.

### 5.3 Producer metadata

Canonical JSON documents SHOULD include:

```json
{
  "producer": {
    "name": "gf-wordbench",
    "version": "0.1.0"
  }
}
```

A reader MUST NOT use the producer version as a substitute for `schema_version`.

### 5.4 Character encoding

All canonical text formats MUST use:

```text
UTF-8 without BOM
```

Writers MUST emit valid Unicode.

Readers MAY accept a UTF-8 BOM for legacy compatibility but MUST remove it before parsing.

### 5.5 Newlines

Canonical text writers MUST use LF:

```text
\n
```

Readers MUST accept LF and CRLF.

Golden comparison MUST normalize CRLF to LF before comparison.

A final newline is REQUIRED for:

- `.gold`;
- normalized `.out`;
- Markdown reports;
- plain-text reports.

### 5.6 JSON restrictions

JSON writers MUST:

- write one JSON object at the root;
- use valid JSON, not JSON5;
- write booleans as `true` or `false`;
- write absence as `null`;
- never emit `NaN`, `Infinity` or `-Infinity`;
- serialize timestamps as strings;
- serialize paths as strings;
- serialize sets as deterministically ordered arrays;
- use `ensure_ascii = false` or equivalent Unicode-preserving behavior;
- use stable indentation for reviewable files.

### 5.7 TOML restrictions

`project.toml` MUST:

- use UTF-8;
- contain one active project;
- avoid duplicate keys;
- avoid environment-specific absolute paths unless explicitly permitted;
- use arrays for ordered collections;
- use stable section names;
- use quoted strings when ambiguity is possible.

### 5.8 Path representation

Path rules depend on the field category.

#### Project-owned paths

Paths inside the project MUST be serialized relative to the project root and use `/`.

Example:

```text
lib/src/french/GrammarFre.gf
```

They MUST NOT contain:

- drive letters;
- `..` segments after normalization;
- user-home aliases;
- environment variables;
- backslashes in canonical output.

#### Run-owned paths

Paths inside a run directory MUST be serialized relative to that run directory in portable manifests.

Example:

```text
raw/compile/GrammarFre.stdout.txt
```

#### Environment paths

Local tool and environment paths MAY be absolute:

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl/src
```

Canonical writers SHOULD normalize separators to `/`.

Legacy readers MUST accept `\`.

#### Source-result paths

`file_results[].file_path` MUST be project-relative in canonical v1 summaries.

Legacy absolute file paths MAY be accepted during migration.

### 5.9 Date and time representation

Canonical timestamps MUST use RFC 3339 / ISO 8601 with an explicit UTC designator:

```text
2026-07-21T16:32:10Z
```

Readers MAY accept:

```text
2026-07-21T16:32:10+00:00
```

Naive timestamps without a timezone SHOULD be rejected in strict mode.

Durations MUST use integer milliseconds:

```text
duration_ms
```

### 5.10 Integer rules

Counts and durations MUST be integers.

They MUST NOT be encoded as strings.

Negative values are prohibited for:

- counts;
- file sizes;
- durations;
- timeout values;
- result indexes.

### 5.11 Null and empty values

Use:

- `null` when a value is absent;
- `""` only when an empty string has a defined semantic meaning;
- `[]` for an empty ordered collection;
- `{}` for an empty mapping.

A missing field and a field set to `null` are not automatically equivalent.

Each schema section below defines defaults explicitly.

### 5.12 Deterministic ordering

Canonical arrays MUST use deterministic order.

Required ordering:

- `file_results`: normalized `file_path`;
- `scenario_results`: scenario execution order from configuration;
- `diff_entries`: severity rank, then path;
- `top_errors`: descending count, then case-insensitive message;
- manifest entries: normalized artifact path;
- entrypoints and checkpoints: declared configuration order;
- unordered path inventories: lexical path order.

JSON object key order is not semantically significant.

### 5.13 Unknown fields

For a supported major version:

- readers SHOULD ignore unknown optional fields;
- readers MUST validate required fields;
- readers MUST NOT silently reinterpret unknown enum values;
- writers MUST NOT copy unknown fields into a new document unless migration policy explicitly requires preservation.

### 5.14 Atomic writes

Writers for state, summary, manifest and project migration MUST use atomic replacement where supported:

1. write a sibling temporary file;
2. flush and close it;
3. validate it;
4. replace the destination atomically.

A failed write MUST NOT destroy the last valid file.

### 5.15 Secrets

Persisted files MUST NOT contain:

- passwords;
- access tokens;
- private keys;
- authentication cookies;
- environment dumps;
- secret command-line arguments.

Local absolute paths are not secrets, but portable exports MAY redact them.

---

## 6. Schema registry

| Schema ID | Canonical path or pattern | Current target version | Status |
|---|---|---:|---|
| `gf-wordbench.project` | `project/project.toml` | `1.0` | Planned normative |
| `gf-wordbench.app-state` | `.gf_wordbench_state.json` | `1.0` | Planned normative |
| `gf-wordbench.run-summary` | `run_<id>/summary.json` | `1.0` | Planned normative |
| `gf-wordbench.artifact-manifest` | `run_<id>/manifest.json` | `1.0` | Planned normative |
| `gf-wordbench.scenario-output` | `run_<id>/raw/scenarios/*.out` | `1.0` | Planned normative |
| `gf-wordbench.scenario-gold` | `project/validation/gold/*.gold` | `1.0` | Planned normative |
| `gf-audit.state-legacy` | `.gf_audit_state.json` | unversioned | Legacy readable |
| `gf-audit.run-summary-current` | `run_<id>/summary.json` | unversioned nested | Legacy readable |
| `gf-audit.run-summary-legacy` | `run_<id>/summary.json` | unversioned flat | Legacy readable |

No new unversioned schema may be introduced.

---

# 7. `project/project.toml`

## 7.1 Identity

```text
schema_id: gf-wordbench.project
schema_version: 1.0
```

## 7.2 Owner

The active language project owns this file.

GF Wordbench reads it but MUST NOT silently rewrite it during normal validation.

Migration and initialization commands MAY write it explicitly.

## 7.3 Purpose

This file defines one active language project per GF Wordbench copy.

It contains language-project facts and validation policy.

It MUST NOT become a store for transient GUI preferences.

## 7.4 Canonical structure

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "sqi"
name = "Albanian"
language_code = "sqi"
root = "."

[sources]
directory = "lib/src/albanian"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copie\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$|\\s)"

[gf]
path_parts = [
  "lib/src",
  "lib/src/albanian",
  "abstract",
  "common",
  "prelude",
]
minimum_version = ""

[modules]
entrypoints = [
  "GrammarSqi.gf",
  "SyntaxSqi.gf",
]
checkpoints = [
  "MorphoSqi.gf",
  "NounSqi.gf",
  "VerbSqi.gf",
  "ExtendSqi.gf",
  "StructuralSqi.gf",
]

[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
]
optional_scenarios = [
  "generation",
  "morphology",
]
release_requires_pgf = true
```

## 7.5 Required fields

### Root

| Field | Type | Rule |
|---|---|---|
| `schema_id` | string | MUST equal `gf-wordbench.project` |
| `schema_version` | string | MUST be supported |

### `[project]`

| Field | Type | Rule |
|---|---|---|
| `id` | string | Required; stable; path-safe; lowercase recommended |
| `name` | string | Required; human-readable |
| `language_code` | string | Required; stable project language identifier |
| `root` | string | Required; canonical value `.` unless a documented layout requires otherwise |

### `[sources]`

| Field | Type | Rule |
|---|---|---|
| `directory` | string | Required; project-relative |
| `glob` | string | Required |
| `include_regex` | string | Required; valid regular expression |
| `exclude_regex` | string | Required; valid regular expression or empty |

### `[gf]`

| Field | Type | Rule |
|---|---|---|
| `path_parts` | array of strings | Required; ordered; project-relative or documented RGL aliases |
| `minimum_version` | string | Optional; empty means no project-level minimum |

### `[modules]`

| Field | Type | Rule |
|---|---|---|
| `entrypoints` | array of strings | Required; at least one |
| `checkpoints` | array of strings | Optional; stable declared order |

### `[validation]`

| Field | Type | Rule |
|---|---|---|
| `required_scenarios` | array of strings | Required; may be empty during bootstrap |
| `optional_scenarios` | array of strings | Optional |
| `release_requires_pgf` | boolean | Required |

## 7.6 Invariants

- One file represents one active language.
- `project.id` MUST remain stable after published runs exist.
- Scenario identifiers MUST be unique across required and optional lists.
- Entrypoints MUST exist before release validation.
- `path_parts` order is semantically significant.
- Absolute `gf.exe`, RGL and output paths MUST NOT be stored here.
- Tool locations belong to environment configuration or application state.
- A normal audit MUST NOT reorder declared entrypoints, checkpoints or scenarios.
- Unknown major versions MUST be rejected.

## 7.7 Compatibility

Compatible additions:

- optional table;
- optional field with a defined default;
- optional scenario;
- additional checkpoint.

Breaking changes:

- renaming a required table;
- changing path-resolution rules;
- changing scenario-ID semantics;
- converting ordered arrays into unordered mappings;
- moving environment paths into this file;
- changing `project.id`.

---

# 8. Application state

## 8.1 Canonical identity

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

The legacy path MAY be imported once and migrated.

The canonical writer MUST write only `.gf_wordbench_state.json`.

## 8.4 Purpose

Application state stores disposable user-interface and local-environment preferences.

It is not the authoritative project definition.

Deleting it MUST NOT damage the project.

## 8.5 Canonical structure

```json
{
  "schema_id": "gf-wordbench.app-state",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "0.1.0"
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

## 8.6 Required fields

Required root fields:

```text
schema_id
schema_version
environment
selection
last_run
```

The `producer` field is recommended.

## 8.7 Environment fields

| Field | Type | Default |
|---|---|---|
| `project_root` | string or null | `null` |
| `rgl_root` | string or null | `null` |
| `gf_executable` | string or null | `null` |
| `output_root` | string or null | `null` |

## 8.8 Selection fields

| Field | Type | Default |
|---|---|---|
| `mode` | string | `diagnostic` |
| `target_file` | string | `""` |
| `timeout_sec` | integer | `60` |
| `max_files` | integer | `0` |
| `keep_ok_details` | boolean | `false` |
| `diff_previous` | boolean | `true` |
| `skip_version_probe` | boolean | `false` |
| `no_compile` | boolean | `false` |
| `emit_cpu_stats` | boolean | `false` |

## 8.9 Last-run fields

| Field | Type | Default |
|---|---|---|
| `run_dir` | string or null | `null` |
| `summary_path` | string or null | `null` |
| `status_message` | string | `""` |

## 8.10 State invariants

- Runtime objects MUST NOT be persisted.
- `current_run_config` MUST NOT be persisted.
- `current_run_result` MUST NOT be persisted.
- `is_running` MUST NOT be restored as `true`.
- On application start, running state is always false.
- Invalid state MUST fall back to safe defaults.
- A malformed state file SHOULD be quarantined or ignored, not crash the application.
- Language-specific scan directories and entrypoints MUST come from `project.toml`, not application state.
- State MUST be written atomically.

## 8.11 Legacy flat-state migration

Legacy keys MAY include:

```text
selected_mode
selected_target_file
selected_project_root
selected_rgl_root
selected_gf_exe
selected_out_root
selected_scan_dir
selected_scan_glob
selected_gf_path
selected_timeout_sec
selected_max_files
selected_include_regex
selected_exclude_regex
selected_keep_ok_details
selected_diff_previous
selected_skip_version_probe
selected_no_compile
selected_emit_cpu_stats
is_running
last_run_dir
last_summary_path
status_message
```

Migration rules:

- local paths move into `environment`;
- execution preferences move into `selection`;
- last-run pointers move into `last_run`;
- project-owned source settings are discarded after `project.toml` is authoritative;
- `is_running` is discarded;
- missing values use v1 defaults;
- the legacy file remains untouched until the v1 state is successfully written.

---

# 9. Run directory contract

## 9.1 Canonical directory name

```text
run_<run-id>
```

Recommended v1 run ID:

```text
YYYYMMDD_HHMMSS
```

The timestamp MUST represent UTC.

If a collision exists, append a deterministic numeric suffix:

```text
run_20260721_163210_02
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
| `top_errors.txt` | log/report writer |
| `manifest.json` | manifest writer |
| `details/` | detail report writer |
| `raw/compile/` | compiler |
| `raw/scan/` | scanner |
| `raw/scenarios/` | scenario runner |
| `artifacts/gfo/` | GF compilation stage |
| `artifacts/out/` | tool output stage |
| `artifacts/pgf/` | PGF build stage |

No observer may silently rewrite another owner’s artifact.

---

# 10. Run summary

## 10.1 Canonical identity

```text
schema_id: gf-wordbench.run-summary
schema_version: 1.0
```

## 10.2 Canonical path

```text
run_<run-id>/summary.json
```

## 10.3 Purpose

`summary.json` is the primary machine-readable record of a run.

It is the source for:

- previous-run comparison;
- automation;
- GUI result loading;
- report verification;
- AI handoff metadata;
- migration and historical analysis.

Markdown reports MUST NOT replace it as the source of truth.

## 10.4 Canonical root structure

```json
{
  "schema_id": "gf-wordbench.run-summary",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "0.1.0"
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

## 10.5 Required root fields

```text
schema_id
schema_version
metadata
totals
artifacts
file_results
scenario_results
diff_entries
top_errors
```

`producer` is recommended.

---

## 10.6 `metadata`

Canonical fields:

| Field | Type | Required |
|---|---|---|
| `run_id` | string | yes |
| `run_dir` | string | yes |
| `started_at` | RFC 3339 UTC string | yes |
| `finished_at` | RFC 3339 UTC string | yes |
| `duration_ms` | integer | yes |
| `gf_version` | string | yes |
| `mode` | enum | yes |
| `target_file` | string or null | yes |
| `project_id` | string | yes |
| `project_name` | string | yes |
| `project_root` | string | yes |
| `rgl_root` | string | yes |
| `gf_executable` | string | yes |
| `output_root` | string | yes |
| `source_directory` | string | yes |
| `source_glob` | string | yes |
| `gf_path` | array of strings | yes |
| `timeout_sec` | integer | yes |
| `max_files` | integer | yes |
| `skip_version_probe` | boolean | yes |
| `no_compile` | boolean | yes |
| `emit_cpu_stats` | boolean | yes |
| `keep_ok_details` | boolean | yes |
| `diff_previous` | boolean | yes |

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Migration aliases:

```text
file -> quick
all  -> diagnostic
```

`target_file` MUST be project-relative when present.

---

## 10.7 `totals`

Canonical fields:

| Field | Type |
|---|---|
| `files_seen` | integer |
| `files_included` | integer |
| `files_excluded` | integer |
| `files_ok` | integer |
| `files_fail` | integer |
| `files_error` | integer |
| `files_skipped` | integer |
| `direct_fail` | integer |
| `downstream_fail` | integer |
| `ambiguous_fail` | integer |
| `excluded_noise` | integer |
| `scenarios_seen` | integer |
| `scenarios_ok` | integer |
| `scenarios_fail` | integer |
| `scenarios_error` | integer |
| `scenarios_skipped` | integer |
| `required_scenario_fail` | integer |
| `overall_status` | enum |

Canonical overall status:

```text
OK
FAIL
ERROR
```

Invariants:

```text
files_included =
  files_ok + files_fail + files_error + files_skipped
```

```text
scenarios_seen =
  scenarios_ok + scenarios_fail + scenarios_error + scenarios_skipped
```

`overall_status` rules:

- `ERROR` when a required stage could not execute or be interpreted;
- `FAIL` when execution completed but a required criterion failed;
- `OK` when every required criterion passed.

---

## 10.8 `artifacts`

Canonical fields are paths relative to the run directory:

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

Rules:

- keys are stable semantic names;
- values are portable run-relative paths;
- absent optional artifacts use `null`;
- a required artifact listed here MUST exist when the run is finalized;
- readers MUST NOT reconstruct these paths from filenames when the field exists.

---

## 10.9 `file_results`

Each element uses this structure:

```json
{
  "file_path": "lib/src/albanian/GrammarSqi.gf",
  "module_name": "GrammarSqi",
  "status": "FAIL",
  "diagnostic_class": "direct",
  "is_direct": true,
  "blocked_by": [],
  "scan_counts": {
    "single_slash_eq": 0,
    "double_slash_dash": 0,
    "runtime_str_match": 0,
    "untyped_case_str_pat": 0,
    "untyped_table_str_pat": 0,
    "trailing_spaces": 0
  },
  "fingerprint": {
    "size_bytes": 1234,
    "hash_algorithm": "sha256",
    "hash": "0123456789abcdef",
    "last_modified_utc": "2026-07-21T16:32:10Z"
  },
  "compile_summary": {
    "exit_code": 1,
    "timed_out": false,
    "duration_ms": 240,
    "error_kind": "TYPE",
    "first_error": "type mismatch",
    "error_detail": "",
    "stdout_path": "raw/compile/GrammarSqi.stdout.txt",
    "stderr_path": "raw/compile/GrammarSqi.stderr.txt"
  },
  "scan_log_path": "raw/scan/GrammarSqi.scan.txt"
}
```

### Required fields

```text
file_path
module_name
status
diagnostic_class
is_direct
blocked_by
scan_counts
fingerprint
compile_summary
scan_log_path
```

### File status enum

```text
OK
FAIL
ERROR
SKIPPED
```

### Diagnostic class enum

```text
ok
direct
downstream
ambiguous
noise
skipped
framework_error
```

### Error kind enum

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

### File-result invariants

- `file_path` is project-relative.
- `module_name` matches the intended GF module identity.
- `status = OK` requires `compile_summary.exit_code = 0` unless compilation was intentionally omitted.
- `timed_out = true` requires `status` to be `FAIL` or `ERROR`.
- `diagnostic_class = downstream` requires a non-empty `blocked_by` whenever the blocker is known.
- `diagnostic_class = direct` SHOULD imply `is_direct = true`.
- scan findings do not independently force compile status.
- raw stdout and stderr paths are run-relative.
- counts are non-negative.

### Fingerprint rule

Canonical v1 uses:

```text
hash_algorithm = "sha256"
hash = full lowercase hexadecimal SHA-256
```

Legacy fields:

```text
sha1_short
last_modified_utc
size_bytes
```

Readers MAY import `sha1_short`, but new writers MUST use the canonical v1 form.

---

## 10.10 `scenario_results`

Each scenario result uses:

```json
{
  "scenario_id": "parse",
  "script_path": "project/validation/scenarios/parse.gfs",
  "required": true,
  "status": "OK",
  "command": [
    "C:/tools/gf/gf.exe"
  ],
  "working_directory": "C:/work/project",
  "exit_code": 0,
  "timed_out": false,
  "duration_ms": 540,
  "stdout_path": "raw/scenarios/parse.stdout.txt",
  "stderr_path": "raw/scenarios/parse.stderr.txt",
  "normalized_output_path": "raw/scenarios/parse.out",
  "gold_path": "project/validation/gold/parse.gold",
  "gold_match": true,
  "diagnostic_class": "ok",
  "error_kind": "OK",
  "primary_message": "",
  "sections": [
    {
      "id": "parse-basic",
      "completed": true
    }
  ],
  "artifacts": []
}
```

Required fields:

```text
scenario_id
script_path
required
status
command
working_directory
exit_code
timed_out
duration_ms
stdout_path
stderr_path
normalized_output_path
gold_path
gold_match
diagnostic_class
error_kind
primary_message
sections
artifacts
```

Invariants:

- `scenario_id` matches configuration.
- `script_path` is project-relative.
- `gold_path` is project-relative or `null`.
- `gold_match` is `null` when no gold comparison applies.
- a missing required marker causes `FAIL` or `ERROR`;
- normal execution MUST NOT update the gold file;
- command order is preserved;
- artifacts are run-relative unless they are project source assets.

---

## 10.11 `diff_entries`

Canonical structure:

```json
{
  "subject_kind": "file",
  "subject_id": "lib/src/albanian/GrammarSqi.gf",
  "previous_status": "FAIL",
  "current_status": "OK",
  "change_kind": "improved",
  "message": "Compilation now succeeds."
}
```

`subject_kind` enum:

```text
file
scenario
run
```

`change_kind` enum:

```text
unchanged
improved
regressed
new
removed
```

Invariants:

- identity is based on `subject_kind + subject_id`;
- path identity uses normalized project-relative paths;
- a missing previous summary produces an empty diff, not an error;
- deterministic severity order is:
  `regressed`, `new`, `improved`, `removed`, `unchanged`.

Legacy `file_path` MAY migrate to:

```text
subject_kind = "file"
subject_id = file_path
```

---

## 10.12 `top_errors`

Canonical format is an array:

```json
[
  {
    "error_kind": "TYPE",
    "message": "type mismatch",
    "count": 3
  }
]
```

Required fields:

```text
error_kind
message
count
```

Rules:

- empty messages are excluded;
- counts are positive integers;
- order is descending count, then message;
- a legacy object mapping message to count MAY be imported;
- writers MUST NOT emit the legacy mapping.

---

## 10.13 Current unversioned nested-summary migration

The current nested form contains:

```text
metadata
totals
artifacts
file_results
diff_entries
top_errors
```

Migration to v1 MUST:

- add `schema_id`;
- add `schema_version`;
- add `producer`;
- add an empty `scenario_results` array;
- rename total keys:
  - `ok` -> `files_ok`
  - `fail` -> `files_fail`
- add v1 total fields with safe defaults;
- map `mode=file` to `quick`;
- map `mode=all` to `diagnostic`;
- convert artifact paths to run-relative paths when possible;
- convert file paths to project-relative paths when possible;
- convert legacy fingerprint fields;
- normalize `top_errors` into the canonical array;
- preserve raw evidence paths;
- retain unknown legacy data only in a documented migration note, not as undocumented root fields.

---

## 10.14 Legacy flat-summary migration

Legacy summaries may contain:

```text
run_config
run_paths
started_at
finished_at
duration_ms
gf_version
flat count fields
file_results
diff_entries
top_errors
```

Migration MUST:

- build canonical `metadata` from `run_config` and root fields;
- build canonical `artifacts` from `run_paths`;
- build canonical `totals` from flat counts;
- map `ai_brief_path` to `ai_ready`;
- accept `ai_ready_path` when already present;
- reject impossible mandatory types in strict mode;
- use safe defaults only for genuinely optional values;
- never overwrite the legacy file during read-only loading.

---

# 11. Artifact manifest

## 11.1 Identity

```text
schema_id: gf-wordbench.artifact-manifest
schema_version: 1.0
```

## 11.2 Canonical path

```text
run_<run-id>/manifest.json
```

## 11.3 Purpose

The manifest proves which artifacts belong to a run and whether they remain intact.

## 11.4 Canonical structure

```json
{
  "schema_id": "gf-wordbench.artifact-manifest",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "0.1.0"
  },
  "run_id": "20260721_163210",
  "generated_at": "2026-07-21T16:32:11Z",
  "hash_algorithm": "sha256",
  "artifacts": [
    {
      "path": "summary.json",
      "role": "machine_summary",
      "media_type": "application/json",
      "required": true,
      "size_bytes": 12345,
      "sha256": "0123456789abcdef",
      "created_by": "report_json"
    }
  ]
}
```

## 11.5 Artifact fields

| Field | Type | Required |
|---|---|---|
| `path` | run-relative string | yes |
| `role` | string enum | yes |
| `media_type` | string | yes |
| `required` | boolean | yes |
| `size_bytes` | integer | yes |
| `sha256` | string | yes |
| `created_by` | string | yes |

Recommended roles:

```text
machine_summary
human_summary
ai_handoff
top_errors
master_log
aggregate_log
scan_log
compile_stdout
compile_stderr
scenario_stdout
scenario_stderr
scenario_output
detail
gfo
pgf
other
```

## 11.6 Manifest invariants

- manifest paths are unique;
- manifest paths remain inside the run directory;
- hashes are computed after final writes;
- the manifest MUST NOT hash itself;
- every required artifact listed in `summary.json` MUST appear;
- missing required artifacts cause manifest validation failure;
- size and hash MUST match the final file bytes;
- directories are not artifact entries;
- symlinks SHOULD be rejected in strict mode.

---

# 12. Normalized scenario output

## 12.1 Identity

```text
schema_id: gf-wordbench.scenario-output
schema_version: 1.0
```

This is a canonical text schema, not JSON.

## 12.2 Path

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

## 12.3 Format

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN parse-basic ---
<normalized GF output>
--- END parse-basic ---
```

## 12.4 Rules

- UTF-8 without BOM;
- LF newlines;
- final newline required;
- one stable header;
- sections use exact begin/end markers;
- section IDs are unique;
- unstable timestamps are removed;
- unstable absolute project/run paths are replaced by stable tokens;
- ANSI control sequences are removed;
- trailing spaces are removed;
- semantically meaningful whitespace inside GF output is preserved;
- GF diagnostic wording is not paraphrased;
- section order follows the scenario;
- missing end markers produce an invalid output.

## 12.5 Stable replacement tokens

Allowed normalization tokens:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

The normalizer MUST NOT replace arbitrary linguistic text.

---

# 13. Golden scenario files

## 13.1 Identity

```text
schema_id: gf-wordbench.scenario-gold
schema_version: 1.0
```

This is a canonical text schema.

## 13.2 Path

```text
project/validation/gold/<scenario-id>.gold
```

## 13.3 Canonical format

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN parse-basic ---
<expected normalized GF output>
--- END parse-basic ---
```

## 13.4 Invariants

- the scenario ID matches the filename and configured scenario;
- normalization version matches the runner;
- exact comparison occurs after newline normalization;
- normal validation is read-only;
- gold updates require an explicit command or flag;
- an update MUST show or save a diff;
- required gold files MUST be version-controlled;
- a missing required gold is a failure, not an automatic creation;
- changing normalization version requires reviewing every affected gold;
- an empty gold file is valid only when explicitly documented.

## 13.5 Gold update policy

Permitted operation:

```text
gf-wordbench gold update <scenario-id>
```

The update workflow MUST:

1. run the scenario;
2. normalize output;
3. show or store the diff;
4. require explicit confirmation or a dedicated non-interactive CI flag;
5. write atomically;
6. record the update in version control.

A standard audit command MUST NOT update gold files.

---

# 14. Soft schemas for human-facing reports

## 14.1 `summary.md`

Canonical path:

```text
run_<run-id>/summary.md
```

Required first heading:

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

A section MAY state `None` when empty.

Rules:

- facts derive from `summary.json` / `RunResult`;
- the report MUST NOT become a machine migration source;
- headings may gain optional subsections in minor releases;
- required headings may change only with a major soft-schema revision.

## 14.2 `AI_READY.md`

Canonical path:

```text
run_<run-id>/AI_READY.md
```

Required first heading:

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

Rules:

- no second compilation or scenario run;
- bounded raw excerpts;
- explicit distinction between direct and downstream failures;
- explicit artifact paths;
- no unsupported diagnosis;
- project-local secrets MUST NOT be included.

## 14.3 `top_errors.txt`

Canonical path:

```text
run_<run-id>/top_errors.txt
```

Canonical line format:

```text
<count>\t<error-kind>\t<message>
```

Example:

```text
3	TYPE	type mismatch
```

Rules:

- UTF-8;
- LF;
- final newline;
- descending count, then message;
- tabs separate fields;
- messages replace embedded tabs and newlines with spaces;
- empty file is allowed when no errors exist.

---

# 15. Schema compatibility policy

## 15.1 Compatible minor changes

Normally compatible:

- adding an optional field with a documented default;
- adding an optional report section;
- adding an optional manifest role;
- adding an optional project configuration table;
- adding an optional scenario-result field;
- adding an unknown field that older readers ignore.

## 15.2 Breaking major changes

Breaking:

- removing a required field;
- renaming a field;
- changing a field type;
- changing path-base semantics;
- changing timestamp semantics;
- changing status meaning;
- changing whether an array is ordered;
- changing ownership of an artifact;
- changing normalization so existing gold meaning changes;
- requiring a previously optional project field;
- reusing an enum value with a new meaning.

## 15.3 Enum changes

Adding an enum value can break strict readers.

Therefore:

- new enum values require at least a minor schema increment;
- readers MUST reject unknown enum values in strict mode;
- non-strict historical readers MAY preserve them as unknown without reinterpretation;
- removing or redefining an enum value requires a major increment.

## 15.4 Reader support window

GF Wordbench SHOULD support:

- the current canonical major version;
- the immediately previous canonical major version when a migration exists;
- documented unversioned GF Audit legacy summaries;
- the documented unversioned legacy state during the migration period.

A writer emits only the latest supported canonical version.

---

# 16. Migration rules

## 16.1 Migration principles

A migrator MUST:

- read without modifying the source;
- validate the source as far as possible;
- produce a canonical destination;
- record warnings;
- preserve raw source evidence;
- write atomically;
- be idempotent;
- never claim success when required meaning could not be recovered.

## 16.2 Migration result

A migration SHOULD return or persist:

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

## 16.3 Loss reporting

Potentially lossy conversions MUST be reported.

Examples:

- absolute file path could not be made project-relative;
- unknown legacy status;
- malformed top-error count;
- missing raw artifact;
- ambiguous `ai_brief_path`;
- naive timestamp;
- missing scenario data in pre-scenario runs.

## 16.4 No implicit project migration

Opening a project MAY propose migration.

It MUST NOT silently rewrite `project.toml`.

---

# 17. Validation and contract tests

Recommended test directory:

```text
tests/schemas/
```

Required tests:

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

## 17.1 Required test cases

### Identity and version

- missing `schema_id`;
- wrong `schema_id`;
- unsupported major version;
- supported minor version;
- malformed version.

### Serialization

- Unicode round trip;
- Windows path migration;
- POSIX canonical path;
- UTC timestamp round trip;
- empty collections;
- null optional paths;
- no `NaN` or infinity;
- deterministic array ordering.

### State

- missing state file;
- malformed JSON;
- unversioned legacy state;
- `is_running = true` resets to false;
- invalid timeout falls back safely;
- runtime objects are not persisted.

### Summary

- current nested legacy summary;
- flat legacy summary;
- `ai_brief_path` alias;
- canonical v1 round trip;
- file-result required fields;
- count invariants;
- top-error legacy mapping;
- unknown optional field;
- unknown enum;
- missing raw artifact.

### Manifest

- correct hashes;
- modified artifact;
- missing required artifact;
- duplicate path;
- path escaping run root;
- manifest excludes itself.

### Scenario and gold

- CRLF normalization;
- missing end marker;
- wrong scenario ID;
- wrong normalization version;
- exact match;
- mismatch diff;
- normal run does not modify gold;
- explicit update writes atomically.

## 17.2 Suggested command

```text
gf-wordbench schemas check
```

Strict mode:

```text
gf-wordbench schemas check --strict
```

Suggested checks:

- validate `project.toml`;
- validate state;
- validate every run summary;
- validate every manifest;
- verify artifact hashes;
- validate every gold header;
- detect unsupported schema versions;
- detect non-canonical path separators;
- detect absolute project-owned paths;
- verify deterministic ordering;
- verify required files exist.

---

# 18. Drift indicators

The following indicate persisted-schema drift:

- writer emits a field the reader does not recognize;
- reader requires an undocumented field;
- summary shape changes without version change;
- state contains project-owned language configuration;
- two files use different names for the same status;
- `top_errors` is sometimes a mapping and sometimes an array in canonical output;
- one writer uses absolute paths and another uses relative paths for the same field;
- a report reconstructs artifact paths instead of reading `artifacts`;
- gold files change during a standard run;
- a new run directory omits `manifest.json`;
- a timestamp lacks a timezone;
- a count is serialized as text;
- a schema ID is copied for a different format;
- a migration overwrites its source;
- an old alias becomes silently canonical;
- JSON fields are renamed without a major version increment.

Any drift MUST be resolved by:

1. restoring the locked schema; or
2. creating a versioned migration and updating this document.

---

# 19. Change workflow

A persisted-schema change is complete only when all boxes are satisfied:

```text
[ ] Schema ID identified
[ ] Current schema version identified
[ ] Change classified as compatible or breaking
[ ] Writer updated
[ ] Every reader updated
[ ] Migration updated or created
[ ] Defaults documented
[ ] Enum impact reviewed
[ ] Path semantics reviewed
[ ] Atomic-write behavior reviewed
[ ] Contract tests updated
[ ] Fixtures updated deliberately
[ ] Gold files reviewed if normalization changed
[ ] This lock updated
[ ] Changelog or migration guide updated
```

Change description template:

```text
Schema:
Current version:
Target version:
Change:
Reason:
Writers:
Readers:
Compatibility:
Migration:
Data-loss risk:
Tests:
```

---

# 20. Schema ownership registry

| Persisted asset | Writer | Readers |
|---|---|---|
| `project/project.toml` | initializer, migrator, maintainer | project loader, bootstrap |
| `.gf_wordbench_state.json` | state manager | GUI/bootstrap |
| `summary.json` | JSON report writer | diff loader, GUI, automation, migration tools |
| `manifest.json` | manifest writer | verifier, cleanup, export tooling |
| scenario `.out` | scenario runner | gold comparator, reports |
| scenario `.gold` | explicit gold updater, maintainer | gold comparator |
| `summary.md` | Markdown report writer | humans |
| `AI_READY.md` | AI report writer | humans and AI systems |
| `top_errors.txt` | report/log writer | humans and optional external tools |

A reader MUST NOT rewrite an asset it does not own.

---

# 21. Legacy compatibility registry

| Legacy element | Canonical replacement | Policy |
|---|---|---|
| `.gf_audit_state.json` | `.gf_wordbench_state.json` | Import and migrate |
| unversioned state | `gf-wordbench.app-state/1.0` | Read legacy, write canonical |
| flat `summary.json` | `gf-wordbench.run-summary/1.0` | Migrate |
| nested unversioned `summary.json` | `gf-wordbench.run-summary/1.0` | Migrate |
| `ai_brief_path` | `ai_ready` artifact key | Read alias only |
| `ai_ready_path` absolute | `artifacts.ai_ready` run-relative | Convert when possible |
| `mode=file` | `mode=quick` | Migration alias |
| `mode=all` | `mode=diagnostic` | Migration alias |
| `sha1_short` | SHA-256 fingerprint fields | Import only |
| `ok` total | `files_ok` | Rename |
| `fail` total | `files_fail` | Rename |
| top-error mapping | top-error array | Normalize |
| language fields in state | `project.toml` | Remove from state |

Legacy aliases MUST NOT be emitted by canonical writers.

---

# 22. Final enforcement rule

Persisted files are public contracts across time.

A writer does not own only the bytes it writes. It owns the guarantee that current and future readers can interpret those bytes according to a documented schema.

A reader does not own the writer’s implementation. It may rely only on the locked schema and documented migration rules.

Therefore:

> No persisted field, enum, path convention, artifact name, normalization rule or directory layout may change through an isolated file edit.

Every persisted-schema change must be versioned, migrated, tested and reviewed as one coordinated change.
