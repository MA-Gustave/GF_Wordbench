# GF Wordbench — `summary.json` Reference

**Document ID:** `GF-WB-REPORT-SUMMARY-JSON`  
**Status:** Normative reference derived from the persisted schema lock  
**Schema ID:** `gf-wordbench.run-summary`  
**Schema version:** `1.0`  
**Canonical path:** `run_<run-id>/summary.json`  
**Writer:** `app/reports/report_json.py`  
**Primary source model:** `RunResult`  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Last reviewed:** 2026-07-24

---

## 1. Purpose

`summary.json` is the primary machine-readable record of one GF Wordbench run.

It supports:

- previous-run comparison within the same active project;
- automation and CI;
- GUI result loading;
- artifact verification;
- historical analysis;
- migration tooling;
- report verification;
- AI handoff metadata;
- debugging without rerunning GF.

`summary.md` and `AI_READY.md` are derived views. They must not replace `summary.json` as the structured source of truth.

---

## 2. Authority

The authoritative persisted schema is:

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Related documents:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/ARTIFACT_MANIFEST.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/reference/SCHEMA_INDEX.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
```

When this reference and `PERSISTED_SCHEMA_LOCK.md` disagree, the schema lock is authoritative. Both documents must then be corrected in one coordinated change.

---

## 3. Product and interoperability boundary

Each `summary.json` records one completed GF Wordbench run for exactly one active project and one normative language target.

The document must not contain:

- a registry of other Wordbench workspaces;
- several active project identities;
- cross-project aggregation state;
- portfolio readiness, comparison, or navigation state;
- private `gf-portfolio` identifiers, storage paths, or configuration.

`summary.json` is a public, versioned Wordbench artifact. The independent `gf-portfolio` product may consume a completed summary in read-only mode through the published schema contract.

Portfolio consumption must not:

- modify the Wordbench summary or its manifest;
- require Wordbench to import, call, configure, or persist Portfolio state;
- reinterpret private Wordbench application state as public schema;
- add consumer-specific fields to this schema without a Wordbench schema change.

---

## 4. Canonical identity


Every canonical file must contain:

```json
{
  "schema_id": "gf-wordbench.run-summary",
  "schema_version": "1.0"
}
```

Rules:

- `schema_id` identifies the format;
- `schema_version` identifies compatibility;
- the package version is not a substitute for the schema version;
- new summaries must not be unversioned;
- another format must not reuse this schema ID;
- readers validate the major schema version before interpreting fields.

---

## 5. Canonical location

```text
run_<run-id>/summary.json
```

Example:

```text
run_20260722_143015/summary.json
```

The JSON report writer owns this file. Readers must not rewrite it.

---

## 6. Encoding and serialization

Canonical writers use:

```text
UTF-8 without BOM
valid JSON
one object at the root
Unicode-preserving serialization
stable indentation
LF newlines
canonical newline
```

Canonical JSON must not contain:

```text
comments
JSON5 syntax
NaN
Infinity
-Infinity
Python object repr
unserialized Path objects
unserialized datetime objects
```

Conversions:

| Python value | JSON value |
|---|---|
| `Path` | string |
| aware `datetime` | RFC 3339 UTC string |
| tuple or set | deterministic array |
| enum | canonical string |
| absent value | `null` |
| boolean | `true` or `false` |

---

## 7. Canonical root structure

```json
{
  "schema_id": "gf-wordbench.run-summary",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "1.0.0"
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

Required root fields:

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

`producer` is optional in schema `1.0` and uses the canonical form below when present.

Required arrays use `[]` when empty. Required objects must not be replaced by `null`.

---

## 8. Root fields

| Field | Type | Required | Purpose |
|---|---|---:|---|
| `schema_id` | string | yes | Format identity |
| `schema_version` | string | yes | Compatibility version |
| `producer` | object | recommended | Producing application |
| `metadata` | object | yes | Run configuration and timing |
| `totals` | object | yes | Aggregated counts |
| `artifacts` | object | yes | Stable artifact locations |
| `file_results` | array | yes | Per-file results |
| `scenario_results` | array | yes | Per-scenario results |
| `diff_entries` | array | yes | Previous-run changes |
| `top_errors` | array | yes | Aggregated errors |

---

## 9. `producer`

Canonical optional form:

```json
{
  "name": "gf-wordbench",
  "version": "1.0.0"
}
```

Rules:

- `name` should be `gf-wordbench`;
- `version` is the package version;
- readers must not infer schema compatibility from it;
- package-version changes do not require schema-version changes;
- absence of `producer` does not invalidate schema `1.0`.

---

## 10. `metadata`

### 10.1 Fields

| Field | Type | Required |
|---|---|---:|
| `run_id` | string | yes |
| `run_dir` | string | yes |
| `started_at` | RFC 3339 UTC string | yes |
| `finished_at` | RFC 3339 UTC string | yes |
| `duration_ms` | integer | yes |
| `gf_version` | string | yes |
| `mode` | enum | yes |
| `target_file` | string or `null` | yes |
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

### 10.2 Example

```json
{
  "run_id": "20260722_143015",
  "run_dir": "C:/work/GF_Wordbench/runs/run_20260722_143015",
  "started_at": "2026-07-22T18:30:15Z",
  "finished_at": "2026-07-22T18:30:19Z",
  "duration_ms": 4217,
  "gf_version": "GF 3.12",
  "mode": "checkpoint",
  "target_file": null,
  "project_id": "example-language",
  "project_name": "Example Language",
  "project_root": "C:/work/GF_Wordbench/project",
  "rgl_root": "C:/tools/gf-rgl/src",
  "gf_executable": "C:/tools/gf/bin/gf.exe",
  "output_root": "C:/work/GF_Wordbench/runs",
  "source_directory": "lib/src/example",
  "source_glob": "*.gf",
  "gf_path": [
    "C:/work/GF_Wordbench/project/lib/src/example",
    "C:/tools/gf-rgl/src"
  ],
  "timeout_sec": 60,
  "max_files": 0,
  "skip_version_probe": false,
  "no_compile": false,
  "emit_cpu_stats": false,
  "keep_ok_details": false,
  "diff_previous": true
}
```

### 10.3 `run_id`

Canonical optional form:

```text
YYYYMMDD_HHMMSS
```

Collision suffix:

```text
YYYYMMDD_HHMMSS_02
```

The base timestamp represents UTC. The ID is stable within the run and agrees with the run directory.

### 10.4 `run_dir`

`run_dir` may be an absolute environment path because it identifies the actual local run directory. It is evidence for this run, not a portable project path or Portfolio workspace identity.

Canonical writers use `/` separators.

### 10.5 Timestamps

Canonical:

```text
2026-07-22T18:30:15Z
```

Readers accept:

```text
2026-07-22T18:30:15+00:00
```

Rules:

- timezone is explicit;
- UTC is canonical;
- naive timestamps fail strict validation;
- `finished_at` must not precede `started_at`.

### 10.6 `duration_ms`

Rules:

- integer;
- non-negative;
- not encoded as text;
- minor clock-resolution differences are acceptable.

### 10.7 `gf_version`

Contains the interpreted GF version used by the run.

The value must not be invented from the executable filename. Raw version evidence remains in run artifacts.

### 10.8 `mode`

Canonical values:

```text
quick
checkpoint
release
diagnostic
```

Legacy read aliases:

```text
file -> quick
all  -> diagnostic
```

Canonical writers must not emit `file` or `all`.

### 10.9 `target_file`

Rules:

- project-relative when present;
- `/` separators;
- `null` when absent;
- never use `""` for absence;
- no drive letter;
- no unresolved `..`.

### 10.10 Path categories

Project-owned paths include:

```text
target_file
source_directory
file_results[].file_path
scenario_results[].script_path
scenario_results[].gold_path
```

Environment evidence paths may be absolute and remain machine-local:

```text
run_dir
project_root
rgl_root
gf_executable
output_root
gf_path[]
scenario_results[].working_directory
```

Run-owned artifact paths are relative to the run directory.

### 10.11 `gf_path`

Rules:

- ordered array;
- reflects effective resolution order;
- no duplicate semantic entries;
- recorded exactly as used;
- shared by compilation and scenarios.

### 10.12 Numeric and boolean configuration

Counts, sizes, durations, and timeout values are integers.

Booleans remain booleans, not strings.

`max_files = 0` may mean unlimited only when configuration defines that meaning.

---

## 11. `totals`

### 11.1 Fields

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

All counts are required non-negative integers.

### 11.2 Example

```json
{
  "files_seen": 42,
  "files_included": 40,
  "files_excluded": 2,
  "files_ok": 37,
  "files_fail": 2,
  "files_error": 1,
  "files_skipped": 0,
  "direct_fail": 1,
  "downstream_fail": 1,
  "ambiguous_fail": 0,
  "excluded_noise": 2,
  "scenarios_seen": 4,
  "scenarios_ok": 3,
  "scenarios_fail": 1,
  "scenarios_error": 0,
  "scenarios_skipped": 0,
  "required_scenario_fail": 1,
  "overall_status": "FAIL"
}
```

### 11.3 Invariants

```text
files_included =
  files_ok + files_fail + files_error + files_skipped
```

```text
scenarios_seen =
  scenarios_ok + scenarios_fail + scenarios_error + scenarios_skipped
```

Canonical invariant:

```text
files_seen = files_included + files_excluded
```

Causal counts do not replace status counts.

### 11.4 Overall status

Canonical:

```text
OK
FAIL
ERROR
```

Meaning:

| Value | Meaning |
|---|---|
| `OK` | Every required criterion passed |
| `FAIL` | Execution completed, but a required criterion failed |
| `ERROR` | A required stage could not execute or be interpreted |

Precedence:

```text
ERROR > FAIL > OK
```

`SKIPPED` is not an overall status.

### 11.5 `required_scenario_fail`

This is a count.

Readers must still inspect individual scenario statuses, because a required scenario may be `ERROR` rather than `FAIL`.

---

## 12. `artifacts`

### 12.1 Canonical object

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

### 12.2 Rules

- values are run-relative;
- separators are `/`;
- paths must not escape the run directory;
- absent optional artifacts use `null`;
- required artifacts must exist when the run is closed;
- consumers must not reconstruct paths when fields exist;
- the manifest stores hashes and sizes.

### 12.3 Field roles

| Field | Kind |
|---|---|
| `summary_json` | machine summary |
| `summary_markdown` | human summary |
| `ai_ready` | AI handoff |
| `top_errors` | grouped error report |
| `manifest` | artifact inventory |
| `master_log` | orchestration log |
| `all_scan_logs` | aggregate scan logs |
| `all_logs` | aggregate logs |
| `details_dir` | detail-report directory |
| `raw_dir` | raw evidence root |
| `compile_logs_dir` | compile evidence root |
| `scan_logs_dir` | scan evidence root |
| `scenario_logs_dir` | scenario evidence root |
| `artifacts_dir` | tool artifact root |
| `gfo_dir` | `.gfo` directory |
| `out_dir` | generic output directory |
| `pgf_dir` | `.pgf` directory |

### 12.4 Manifest relationship

Every required file artifact listed here must appear in `manifest.json`.

Directories are not manifest artifact entries.

---

## 13. `file_results`

### 13.1 Canonical element

```json
{
  "file_path": "lib/src/example/GrammarEx.gf",
  "module_name": "GrammarEx",
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
    "hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "last_modified_utc": "2026-07-22T18:22:10Z"
  },
  "compile_summary": {
    "exit_code": 1,
    "timed_out": false,
    "duration_ms": 240,
    "error_kind": "TYPE",
    "first_error": "type mismatch",
    "error_detail": "",
    "stdout_path": "raw/compile/GrammarEx.stdout.txt",
    "stderr_path": "raw/compile/GrammarEx.stderr.txt"
  },
  "scan_log_path": "raw/scan/GrammarEx.scan.txt"
}
```

### 13.2 Required fields

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

### 13.3 Ordering

`file_results` is ordered by normalized `file_path`.

### 13.4 `file_path`

Rules:

- project-relative;
- `/` separators;
- stable comparison identity;
- no drive letter;
- no unresolved `..`.

### 13.5 File status

```text
OK
FAIL
ERROR
SKIPPED
```

| Status | Meaning |
|---|---|
| `OK` | Required validation passed |
| `FAIL` | Validation ran and criterion failed |
| `ERROR` | Validation could not run or be interpreted reliably |
| `SKIPPED` | Validation was intentionally omitted |

### 13.6 Diagnostic class

Schema `1.0` values:

```text
ok
direct
downstream
ambiguous
noise
skipped
framework_error
```

`framework_error` remains part of the locked `1.0` schema and cannot be removed without a schema-lock and migration update.

Precise technical semantics still belong primarily to `status` and `error_kind`.

### 13.7 `is_direct`

Compatibility boolean.

`diagnostic_class = direct` should imply `is_direct = true`.

Consumers should prefer `diagnostic_class` for complete classification.

### 13.8 `blocked_by`

Array of stable blocker identities.

Rules:

- `[]` when unknown or not applicable;
- deterministic order;
- project-relative paths for file blockers;
- no duplicates.

### 13.9 `scan_counts`

Required fields:

```text
single_slash_eq
double_slash_dash
runtime_str_match
untyped_case_str_pat
untyped_table_str_pat
trailing_spaces
```

Every value is a non-negative integer.

Adding a persisted scan counter requires schema review.

### 13.10 `fingerprint`

Fields:

```text
size_bytes
hash_algorithm
hash
last_modified_utc
```

Canonical:

```text
hash_algorithm = sha256
hash = full lowercase hexadecimal SHA-256
```

Legacy `sha1_short` may be imported but must not be emitted by canonical writers.

### 13.11 `compile_summary`

Fields:

```text
exit_code
timed_out
duration_ms
error_kind
first_error
error_detail
stdout_path
stderr_path
```

Error kinds:

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

Rules:

- timeout remains explicit;
- stdout and stderr stay separate;
- raw paths are run-relative;
- zero exit does not override missing required artifacts;
- a skipped compile must not be presented as a real successful invocation.

### 13.12 `scan_log_path`

Run-relative path to scan evidence.

Example:

```text
raw/scan/GrammarEx.scan.txt
```

---

## 14. `scenario_results`

### 14.1 Canonical element

```json
{
  "scenario_id": "parse",
  "script_path": "project/validation/scenarios/parse.gfs",
  "required": true,
  "status": "OK",
  "command": [
    "C:/tools/gf/bin/gf.exe"
  ],
  "working_directory": "C:/work/GF_Wordbench/project",
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

### 14.2 Required fields

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

### 14.3 Ordering

Scenario results follow configured execution order, not completion order.

### 14.4 Identity and paths

- `scenario_id` matches project configuration;
- `script_path` is project-relative;
- `gold_path` is project-relative or `null`;
- raw and normalized output paths are run-relative;
- `working_directory` may be absolute.

### 14.5 Status

```text
OK
FAIL
ERROR
SKIPPED
```

Typical mappings:

| Condition | Status |
|---|---|
| All required checks pass | `OK` |
| Valid gold comparison differs | `FAIL` |
| Timeout | `ERROR` |
| Missing required gold | `ERROR` |
| Scenario not selected | `SKIPPED` |

### 14.6 `command`

Ordered string array.

It preserves the executed request and must not be replaced by a shell command string.

### 14.7 `gold_match`

```text
true
false
null
```

- `true`: comparison applied and matched;
- `false`: comparison applied and differed;
- `null`: comparison did not apply.

Missing required gold must not appear as successful `null`.

### 14.8 `sections`

Minimum section object:

```json
{
  "id": "parse-basic",
  "completed": true
}
```

Rules:

- IDs are unique;
- order follows scenario order;
- missing required markers produce incomplete validation;
- process exit alone does not prove section completion.

### 14.9 `artifacts`

Array of scenario-produced artifact references.

Use `[]` when none.

Required retained artifacts must also appear in the manifest.

---

## 15. `diff_entries`

### 15.1 Canonical element

```json
{
  "subject_kind": "file",
  "subject_id": "lib/src/example/GrammarEx.gf",
  "previous_status": "FAIL",
  "current_status": "OK",
  "change_kind": "improved",
  "message": "Compilation now succeeds."
}
```

### 15.2 Fields

```text
subject_kind
subject_id
previous_status
current_status
change_kind
message
```

### 15.3 Enums

`subject_kind`:

```text
file
scenario
run
```

`change_kind`:

```text
unchanged
improved
regressed
new
removed
```

Ordering:

```text
regressed
new
improved
removed
unchanged
```

Identity:

```text
subject_kind + subject_id
```

A missing previous summary produces `diff_entries: []`.

### 15.4 Legacy migration

Legacy `file_path` maps to:

```text
subject_kind = file
subject_id = file_path
```

---

## 16. `top_errors`

Canonical array:

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

- messages are non-empty;
- counts are positive integers;
- order is descending count, then case-insensitive message;
- empty collection is `[]`;
- legacy message-to-count mappings may be imported;
- canonical writers must not emit the mapping form.

---

## 17. Complete example

```json
{
  "schema_id": "gf-wordbench.run-summary",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "1.0.0"
  },
  "metadata": {
    "run_id": "20260722_143015",
    "run_dir": "C:/work/GF_Wordbench/runs/run_20260722_143015",
    "started_at": "2026-07-22T18:30:15Z",
    "finished_at": "2026-07-22T18:30:19Z",
    "duration_ms": 4217,
    "gf_version": "GF 3.12",
    "mode": "checkpoint",
    "target_file": null,
    "project_id": "example-language",
    "project_name": "Example Language",
    "project_root": "C:/work/GF_Wordbench/project",
    "rgl_root": "C:/tools/gf-rgl/src",
    "gf_executable": "C:/tools/gf/bin/gf.exe",
    "output_root": "C:/work/GF_Wordbench/runs",
    "source_directory": "lib/src/example",
    "source_glob": "*.gf",
    "gf_path": [
      "C:/work/GF_Wordbench/project/lib/src/example",
      "C:/tools/gf-rgl/src"
    ],
    "timeout_sec": 60,
    "max_files": 0,
    "skip_version_probe": false,
    "no_compile": false,
    "emit_cpu_stats": false,
    "keep_ok_details": false,
    "diff_previous": true
  },
  "totals": {
    "files_seen": 1,
    "files_included": 1,
    "files_excluded": 0,
    "files_ok": 0,
    "files_fail": 1,
    "files_error": 0,
    "files_skipped": 0,
    "direct_fail": 1,
    "downstream_fail": 0,
    "ambiguous_fail": 0,
    "excluded_noise": 0,
    "scenarios_seen": 1,
    "scenarios_ok": 1,
    "scenarios_fail": 0,
    "scenarios_error": 0,
    "scenarios_skipped": 0,
    "required_scenario_fail": 0,
    "overall_status": "FAIL"
  },
  "artifacts": {
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
  },
  "file_results": [
    {
      "file_path": "lib/src/example/GrammarEx.gf",
      "module_name": "GrammarEx",
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
        "size_bytes": 2201,
        "hash_algorithm": "sha256",
        "hash": "1111111111111111111111111111111111111111111111111111111111111111",
        "last_modified_utc": "2026-07-22T18:22:10Z"
      },
      "compile_summary": {
        "exit_code": 1,
        "timed_out": false,
        "duration_ms": 240,
        "error_kind": "TYPE",
        "first_error": "type mismatch",
        "error_detail": "expected NP; inferred CN",
        "stdout_path": "raw/compile/GrammarEx.stdout.txt",
        "stderr_path": "raw/compile/GrammarEx.stderr.txt"
      },
      "scan_log_path": "raw/scan/GrammarEx.scan.txt"
    }
  ],
  "scenario_results": [
    {
      "scenario_id": "load",
      "script_path": "project/validation/scenarios/load.gfs",
      "required": true,
      "status": "OK",
      "command": [
        "C:/tools/gf/bin/gf.exe"
      ],
      "working_directory": "C:/work/GF_Wordbench/project",
      "exit_code": 0,
      "timed_out": false,
      "duration_ms": 420,
      "stdout_path": "raw/scenarios/load.stdout.txt",
      "stderr_path": "raw/scenarios/load.stderr.txt",
      "normalized_output_path": "raw/scenarios/load.out",
      "gold_path": null,
      "gold_match": null,
      "diagnostic_class": "ok",
      "error_kind": "OK",
      "primary_message": "",
      "sections": [
        {
          "id": "load-main",
          "completed": true
        }
      ],
      "artifacts": []
    }
  ],
  "diff_entries": [
    {
      "subject_kind": "file",
      "subject_id": "lib/src/example/GrammarEx.gf",
      "previous_status": "OK",
      "current_status": "FAIL",
      "change_kind": "regressed",
      "message": "Compilation now fails with a type mismatch."
    }
  ],
  "top_errors": [
    {
      "error_kind": "TYPE",
      "message": "type mismatch",
      "count": 1
    }
  ]
}
```

---

## 18. Writer requirements

`app/reports/report_json.py` must:

1. accept a completed `RunResult`;
2. avoid rerunning validation;
3. build the canonical root object explicitly;
4. emit schema identity and version;
5. serialize canonical path forms;
6. serialize UTC timestamps;
7. emit integers as integers;
8. preserve deterministic ordering;
9. exclude secrets;
10. write UTF-8;
11. write atomically;
12. validate before replacement;
13. return the owned `Path`;
14. preserve the last valid summary on failure.

Canonical writers must not emit legacy aliases.

### 18.1 Atomic write sequence

```text
build object
→ serialize to sibling temporary file
→ flush and close
→ parse temporary JSON
→ validate schema and invariants
→ atomically replace summary.json
→ verify destination
```

### 18.2 Deterministic ordering

```text
file_results:
  normalized file_path

scenario_results:
  project configuration order

diff_entries:
  severity rank, then identity

top_errors:
  descending count, then case-insensitive message
```

JSON object key order is not semantic, but writers should keep stable reviewable ordering.

### 18.3 Prohibitions

The writer must not:

- call GF;
- call scanners or compilers;
- run scenarios;
- recompute causal classification;
- modify gold files;
- parse Markdown to reconstruct missing data;
- drop failed results;
- copy unknown legacy fields;
- serialize exception objects;
- persist secrets.

---

## 19. Reader requirements

Readers must:

1. parse valid JSON;
2. require one root object;
3. validate `schema_id`;
4. parse `schema_version`;
5. reject unsupported major versions;
6. validate required fields and types;
7. validate enums;
8. validate path categories;
9. validate timestamps and integers;
10. validate totals in strict mode;
11. tolerate unknown optional fields within a supported major version;
12. never rewrite the source during read-only loading;
13. preserve migration warnings;
14. never substitute Markdown parsing.

### 19.1 Unknown fields

For supported major version `1`:

- ignore unknown optional fields;
- validate required known fields;
- do not reinterpret unknown enums;
- do not copy unknown fields into canonical output unless migration policy explicitly permits it.

### 19.2 Missing versus `null`

Examples:

- `target_file` is required but may be `null`;
- `gold_path` is required but may be `null`;
- `gold_match` is required but may be `null`;
- root arrays are required and use `[]`.

Missing and `null` are not automatically equivalent.

---

## 20. Validation levels

Validation levels:

```text
syntax
schema
invariants
artifacts
strict
```

### 20.1 Syntax

```text
valid UTF-8
valid JSON
one root object
```

### 20.2 Schema

```text
schema identity
supported version
required fields
types
enums
nullability
```

### 20.3 Invariants

```text
count equations
path categories
timestamps
ordering
unique identities
status relationships
non-negative values
```

### 20.4 Artifacts

```text
required paths exist
manifest includes required files
manifest hashes match
raw evidence paths resolve
project paths stay in project
run paths stay in run
```

### 20.5 Strict

```text
reject naive timestamps
reject non-canonical separators
reject unknown enums
reject duplicate identities
reject unsafe symlinks
verify deterministic ordering
verify full SHA-256
```

Schema validation commands:

```text
gf-wordbench schemas check
gf-wordbench schemas check --strict
```

---

## 21. Error handling

### 21.1 Writer failure

Failure to write or validate required `summary.json` makes run closure `ERROR`.

Captured raw evidence should remain available.

The run must not be reported as complete.

### 21.2 Reader failure

| Failure | Handling |
|---|---|
| File absent | Not a completed readable run |
| Invalid JSON | Read/schema error |
| Wrong schema ID | Reject |
| Unsupported major version | Reject |
| Missing required field | Reject |
| Unknown enum | Reject in strict mode |
| Invalid artifact path | Artifact validation failure |
| Count mismatch | Invariant failure |

### 21.3 Previous-run loading

A malformed previous summary must not relabel current run results.

It should produce an empty diff and warning unless strict historical comparison is required.

---

## 22. Migration from unversioned nested summaries

Legacy nested summaries may contain:

```text
metadata
totals
artifacts
file_results
diff_entries
top_errors
```

Migration to `1.0` must:

1. add `schema_id`;
2. add `schema_version`;
3. add `producer`;
4. add `scenario_results: []`;
5. rename `totals.ok` to `files_ok`;
6. rename `totals.fail` to `files_fail`;
7. add missing totals with safe defaults;
8. map `mode=file` to `quick`;
9. map `mode=all` to `diagnostic`;
10. convert artifact paths to run-relative paths;
11. convert file paths to project-relative paths;
12. convert legacy fingerprints;
13. normalize top errors to an array;
14. preserve raw evidence paths;
15. report losses or uncertainty;
16. avoid copying undocumented root fields.

---

## 23. Migration from legacy flat summaries

Legacy flat summaries may contain:

```text
run_config
run_paths
started_at
finished_at
duration_ms
gf_version
flat counts
file_results
diff_entries
top_errors
```

Migration must:

- build `metadata` from config and root fields;
- build `artifacts` from run paths;
- build `totals` from flat counts;
- map `ai_brief_path` to `artifacts.ai_ready`;
- accept `ai_ready_path` as a legacy alias;
- normalize paths and modes;
- normalize fingerprints;
- normalize top errors;
- reject impossible mandatory types in strict mode;
- use defaults only for optional values;
- never overwrite the legacy file during read-only loading.

---

## 24. Migration safety

Migrations are:

```text
explicit
version-aware
idempotent
tested
non-destructive
traceable
```

Migration flow:

```text
read source
→ identify legacy shape
→ build canonical in-memory model
→ validate
→ return model and warnings
→ write only through explicit migration command
```

Losses must be reported.

---

## 25. Compatibility policy

### 25.1 Major versions

Unknown major versions are incompatible.

A `1.x` reader must not guess `2.x`.

### 25.2 Minor versions

Readers may accept unknown optional fields within major version `1`.

They must still reject incompatible type changes, missing required fields, and unknown enum meanings.

### 25.3 Field removal or rename

Removing or renaming a field requires:

- a major version;
- migration;
- reader updates;
- tests;
- schema-lock update.

### 25.4 Optional extension

Adding an optional field requires:

- documented type;
- absence/default semantics;
- owner;
- writer;
- readers;
- tests;
- schema minor-version review.

---

## 26. Consumer guidance

### 26.1 GUI

Use:

```text
metadata
totals
file_results
scenario_results
diff_entries
artifacts
```

Do not parse `summary.md` for structured values.

### 26.2 Automation

Automation:

- validate schema version;
- use `overall_status`;
- distinguish fail and error counts;
- resolve paths through `artifacts`;
- use project-relative identities;
- ignore JSON object key order.

### 26.3 Diff loader

The diff loader:

- read supported summaries;
- migrate legacy summaries in memory;
- compare stable identities;
- preserve current-run meaning;
- return empty diff when no previous run exists.

### 26.4 AI workflows

AI workflows may consume `AI_READY.md` for concise context and `summary.json` for exact structured facts.

Missing evidence must not be inferred as success.

---

### 26.5 `gf-portfolio`

`gf-portfolio` consumes only supported public schema versions.

It must:

- treat the summary and manifest as immutable source artifacts;
- validate `schema_id` and `schema_version`;
- use `metadata.project_id` as the Wordbench project identity;
- preserve project-relative and run-relative path semantics;
- keep portfolio aggregation, indexing, readiness, and storage in its own schemas;
- reject or quarantine incompatible summaries without mutating them.

Wordbench does not emit Portfolio-specific fields and does not depend on Portfolio availability.


---

## 27. Path-resolution examples

### 27.1 Run artifact

```text
run_dir:
  C:/work/runs/run_20260722_143015

artifacts.summary_markdown:
  summary.md

resolved:
  C:/work/runs/run_20260722_143015/summary.md
```

### 27.2 Compile log

```text
file_results[0].compile_summary.stderr_path:
  raw/compile/GrammarEx.stderr.txt
```

Resolve against the run directory.

### 27.3 Project source

```text
file_results[0].file_path:
  lib/src/example/GrammarEx.gf
```

Resolve against the project root.

### 27.4 Gold file

```text
scenario_results[0].gold_path:
  project/validation/gold/parse.gold
```

Resolve according to the project path contract.

Not every path string has the same base.

---

## 28. Invariant checklist

```text
[ ] schema_id is correct
[ ] schema_version is supported
[ ] required root fields exist
[ ] metadata fields have correct types
[ ] timestamps include timezone
[ ] counts are non-negative integers
[ ] total equations hold
[ ] overall_status is valid
[ ] artifact paths are run-relative
[ ] file paths are project-relative
[ ] file_results are ordered
[ ] scenario_results follow configured order
[ ] diff_entries follow severity order
[ ] top_errors are ordered arrays
[ ] status enums are valid
[ ] diagnostic classes are valid
[ ] error kinds are valid
[ ] fingerprints use SHA-256
[ ] stdout and stderr remain separate
[ ] scenario IDs are unique
[ ] gold_match nullability is valid
[ ] required artifacts exist
[ ] manifest contains required artifacts
[ ] no secrets are present
```

---

## 29. Drift indicators

Probable drift exists when:

- a writer emits an undocumented field;
- a reader requires an undocumented field;
- root shape changes without version change;
- `top_errors` alternates between mapping and array;
- paths alternate between absolute and relative for the same field;
- canonical separators differ;
- reports reconstruct artifact paths;
- a new status appears in one component only;
- timestamps lose timezone;
- counts become strings;
- empty `scenario_results` is omitted;
- SHA-1 short hashes reappear;
- legacy modes are emitted;
- unknown legacy fields are copied;
- summary writing is non-atomic;
- listed required artifacts do not exist;
- a reader rewrites the loaded file.

Resolve drift by restoring `1.0` or introducing a versioned migration.

---

## 30. Schema-change workflow

Change description:

```text
Schema:
Current version:
Target version:
Change:
Reason:
Writer:
Readers:
Compatibility:
Migration:
Data-loss risk:
Path impact:
Enum impact:
Tests:
```

Checklist:

```text
[ ] Schema ID confirmed
[ ] Change classified
[ ] Writer contract updated
[ ] All reader contracts updated
[ ] Shared model contract updated
[ ] Defaults documented
[ ] Null semantics documented
[ ] Ordering documented
[ ] Path semantics reviewed
[ ] Enum impact reviewed
[ ] Migration contract updated
[ ] Legacy fixtures synchronized
[ ] Contract tests synchronized
[ ] Schema tests synchronized
[ ] GUI loading tested
[ ] Diff loading tested
[ ] Automation impact reviewed
[ ] Persisted schema lock synchronized
[ ] This reference synchronized
[ ] Changelog or migration guide updated
```

---

## 31. Required test coverage

```text
tests/schemas/test_summary_schema.py
tests/schemas/test_summary_round_trip.py
tests/schemas/test_summary_migration.py
tests/contracts/test_report_json_contract.py
tests/reports/test_summary_json.py
```

Required cases:

```text
canonical full summary
canonical empty arrays
Unicode paths and diagnostics
Windows path migration
project-relative paths
run-relative paths
UTC timestamps
naive timestamp rejection
negative counts
count mismatch
unknown enum
unknown optional field
unsupported major version
missing required field
null versus missing
deterministic ordering
SHA-256 fingerprint
legacy sha1_short migration
legacy nested migration
legacy flat migration
top-error mapping migration
mode alias migration
atomic write failure
secret rejection
manifest relationship
round-trip semantic equality
```

---

## 32. Writer design

Writer operation:

```python
def write_summary_json(run_result: RunResult) -> Path:
    document = build_summary_document(run_result)
    validate_summary_document(document)
    atomic_write_json(run_result.run_paths.summary_json_path, document)
    return run_result.run_paths.summary_json_path
```

Required separation:

```text
build canonical document
serialize canonical values
validate schema
write atomically
```

Do not use unrestricted recursive `asdict()` as the complete public schema strategy.

Internal dataclass refactors must not silently change persisted JSON.

---

## 33. Schema invariants

`summary.json` must preserve:

1. explicit schema identity;
2. explicit schema version;
3. one root object;
4. stable required root fields;
5. UTC timestamps;
6. integer counts and durations;
7. canonical statuses;
8. distinct file and scenario results;
9. deterministic arrays;
10. project-relative source identities;
11. run-relative artifact identities;
12. explicit environment paths;
13. separate stdout and stderr;
14. canonical SHA-256 fingerprints;
15. explicit null semantics;
16. atomic writing;
17. legacy read compatibility without legacy writes;
18. manifest consistency;
19. no secret persistence;
20. no report-time validation.

---

## 34. Governing rule

> `summary.json` records what the run proved—not what a report later inferred.

Every field must be reproducible from completed structured evidence, interpretable by supported readers, and protected by explicit schema-version rules.
