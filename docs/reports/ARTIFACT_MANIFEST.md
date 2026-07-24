# GF Wordbench — Artifact Manifest

**Document ID:** `GF-WB-ARTIFACT-MANIFEST`  
**Status:** Normative artifact-integrity specification  
**Applies to:** every finalized GF Wordbench run for one active project and one normative language target, with stricter completeness requirements in `release` mode  
**Owner:** GF Wordbench maintainers  
**Manifest schema:** `gf-wordbench.artifact-manifest/1.0`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Schema authority:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Artifact authority:** `docs/architecture/ARTIFACT_MODEL.md`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-24`

**Normative counterparts:**

- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/reports/REPORTING_OVERVIEW.md`
- `docs/reports/SUMMARY_JSON_REFERENCE.md`
- `docs/reports/RAW_LOGS_REFERENCE.md`
- `docs/operations/RUN_DIRECTORY_LIFECYCLE.md`

---

## 1. Purpose

`manifest.json` is the authoritative inventory of finalized files owned by one GF Wordbench run.

It answers:

1. Which files belong to this run?
2. What role does each file serve?
3. Which files are required?
4. What bytes were finalized?
5. What size and SHA-256 digest identify those bytes?
6. Which component created each file?
7. Can the run still be trusted after files have been copied, archived, or inspected?

The manifest does not decide whether the grammar is linguistically correct. It proves artifact identity and integrity.

> A run artifact is not verified merely because a file with the expected name exists.

For a required artifact to be verified:

- the path must be safe and run-relative;
- the file must exist;
- the file must be a permitted regular file;
- its final byte size must match;
- its SHA-256 digest must match;
- its role and ownership must be declared;
- its presence must be consistent with the finalized run result.

---

## 2. Scope

This document governs:

- the canonical `manifest.json` path;
- manifest schema identity and version;
- manifest production;
- artifact discovery;
- artifact declaration;
- run-relative path rules;
- artifact roles;
- media types;
- required and optional artifact semantics;
- creator identity;
- size calculation;
- SHA-256 calculation;
- duplicate detection;
- symlink policy;
- manifest verification;
- finalization ordering;
- release-gate integration;
- archive and export verification;
- migration and compatibility;
- CLI, GUI, and CI behavior;
- testing requirements.

This document does not govern:

- source-control manifests;
- Python package manifests;
- RGL installation manifests;
- project source inventories;
- external release-package formats;
- the internal format of `.gfo` or `.pgf`;
- linguistic acceptance criteria;
- gold-file approval;
- report prose beyond artifact references.

---

## Product and public-artifact boundary

One manifest belongs to exactly one finalized Wordbench run. That run belongs to exactly one active GF language project and one normative language target.

Schema `1.0` obtains project identity through the required `summary.json` artifact:

```text
manifest.json
    -> machine_summary entry
    -> summary.json
    -> run and project identity
```

The manifest and its listed public artifacts form a read-only interoperability boundary.

The independent `gf-portfolio` product may:

- read a finalized manifest;
- verify listed bytes;
- locate `summary.json`;
- ingest public versioned Wordbench artifacts;
- maintain its own indexing and aggregation state.

`gf-portfolio` must not:

- rewrite `manifest.json`;
- modify a listed run artifact;
- infer private Wordbench state;
- require Wordbench to acknowledge ingestion;
- participate in Wordbench manifest generation or verification.

GF Wordbench manifest creation and verification must succeed without `gf-portfolio` installed or reachable.

---

## 3. Canonical identity

### 3.1 Schema identity

```text
schema_id: gf-wordbench.artifact-manifest
schema_version: 1.0
```

### 3.2 Canonical path

```text
run_<run-id>/manifest.json
```

The path is relative to the configured output root.

### 3.3 Encoding

```text
UTF-8 without BOM
```

### 3.4 Newline

Canonical writers use:

```text
LF
```

### 3.5 JSON format

The manifest is:

- one JSON object at the root;
- strict JSON, not JSON5;
- Unicode-preserving;
- deterministically indented;
- terminated with a final newline;
- free of `NaN`, `Infinity`, and `-Infinity`.

---

## 4. Ownership

### 4.1 Reporting module

The `reporting` module is the sole owner of:

```text
manifest construction
canonical JSON serialization
atomic manifest writing
manifest loading
manifest verification
```

Conceptual operations:

```python
build_manifest(
    run_result: RunResult,
    run_paths: RunPaths,
    artifact_declarations: Sequence[ArtifactDeclaration],
) -> ArtifactManifest
```

```python
write_manifest(
    manifest: ArtifactManifest,
    run_paths: RunPaths,
) -> ManifestWriteResult
```

```python
verify_manifest(
    manifest_path: Path,
    run_root: Path,
    policy: ManifestVerificationPolicy,
) -> ManifestVerificationResult
```

Exact private type and function names may vary. Ownership, inputs and outputs remain singular.

### 4.2 Runs module

The `runs` module owns:

- the run identity;
- the run directory;
- finalization ordering;
- the transition to a finalized lifecycle state;
- the prohibition on post-manifest writes;
- propagation of manifest failure into run status and release gates.

The runs module does not serialize or independently verify the manifest.

### 4.3 Artifact producers

Validation, diagnostics and reporting producers register structured artifact declarations.

Examples:

| Artifact | Logical owner |
|---|---|
| `summary.json` | reporting machine-summary writer |
| `summary.md` | reporting human-summary writer |
| `AI_READY.md` | reporting AI-handoff writer |
| `top_errors.txt` | reporting log writer |
| run master log | runs evidence writer |
| compile stdout/stderr | external-tool evidence adapter for validation |
| scenario stdout/stderr | external-tool evidence adapter for validation |
| normalized scenario output | validation scenario normalizer |
| `.gfo` | GF execution, catalogued by validation |
| `.pgf` | GF execution, catalogued by the PGF validation stage |
| `manifest.json` | reporting manifest writer |

Producers do not write manifest fragments and do not hash files owned by other producers.

### 4.4 Readers

Permitted readers include:

- reporting manifest verifier;
- runs release-gate consumer;
- CLI and GUI entrypoints;
- CI automation;
- archive and export tooling;
- cleanup tooling;
- support and diagnostic tooling;
- human reviewers;
- optional `gf-portfolio` ingestion adapters.

Readers must not rewrite `manifest.json` or listed artifacts.

A migration operation may create a new canonical manifest from a supported legacy run while preserving provenance and without claiming unverifiable historical integrity.

### 4.5 Ownership invariant

The manifest inventories files owned by other components. It does not take ownership of their contents.

The manifest writer reads only finalized bytes. It must not alter, normalize, redact or regenerate an artifact before hashing it.

---

## 5. Core principles

### 5.1 Final-byte principle

Hashes and sizes describe final bytes after all permitted writers have completed.

### 5.2 Run-root principle

Every manifest path is relative to one run root.

### 5.3 No-self-hash principle

`manifest.json` MUST NOT include itself as an artifact entry.

### 5.4 No-directory-entry principle

Directories are not artifact entries.

Only files are catalogued.

### 5.5 Single-path principle

Each normalized artifact path appears at most once.

### 5.6 Explicit-requiredness principle

Every entry states whether it is required.

### 5.7 No-reconstruction principle

A consumer must use recorded artifact paths when available. It must not reconstruct them from naming conventions.

### 5.8 Immutable-evidence principle

Raw evidence is hashed as captured. A normalizer or report writer must not modify it before manifesting.

### 5.9 Deterministic-order principle

Artifact entries are sorted by normalized run-relative path.

### 5.10 Fail-closed principle

A required artifact that cannot be verified invalidates the manifest.

### 5.11 Single-run principle

Every entry belongs to the same run root and the same run identity.

### 5.12 Single-project principle

The required machine summary identifies the one active project and normative language target represented by the run.

### 5.13 Consumer-read-only principle

External consumers, including `gf-portfolio`, may verify and copy public artifacts but must not mutate the manifested run.

### 5.14 Portfolio-independence principle

Manifest generation, verification and release gates do not depend on Portfolio availability, state or acknowledgment.

---

## 6. Canonical structure

Schema `1.0` uses this structure:

```json
{
  "schema_id": "gf-wordbench.artifact-manifest",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "1.0.0"
  },
  "run_id": "20260722_163210",
  "generated_at": "2026-07-22T16:32:11Z",
  "hash_algorithm": "sha256",
  "artifacts": [
    {
      "path": "summary.json",
      "role": "machine_summary",
      "media_type": "application/json",
      "required": true,
      "size_bytes": 12345,
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "created_by": "reporting_json"
    }
  ]
}
```

No additional root field is required by schema `1.0`.

Readers for the supported major version SHOULD ignore unknown optional fields, but strict readers MUST reject unknown required semantics that cannot be interpreted safely.

---

## 7. Root fields

### 7.1 `schema_id`

**Type:** string  
**Required:** yes  
**Value:**

```text
gf-wordbench.artifact-manifest
```

Any other value is a schema error.

### 7.2 `schema_version`

**Type:** string  
**Required:** yes  
**Current value:**

```text
1.0
```

Version format:

```text
MAJOR.MINOR
```

An unsupported major version MUST be rejected.

### 7.3 `producer`

**Type:** object  
**Required:** yes

Canonical fields:

```json
{
  "name": "gf-wordbench",
  "version": "1.0.0"
}
```

The producer version identifies the application writer. It does not replace `schema_version`.

### 7.4 `run_id`

**Type:** string  
**Required:** yes

It MUST equal the authoritative run identifier recorded in `summary.json` and represented by the run directory.

### 7.5 `generated_at`

**Type:** RFC 3339 UTC string  
**Required:** yes

Example:

```text
2026-07-22T16:32:11Z
```

It records manifest generation time, not run start time.

### 7.6 `hash_algorithm`

**Type:** string  
**Required:** yes  
**Canonical value:**

```text
sha256
```

Schema `1.0` does not permit per-entry hash algorithms.

### 7.7 `artifacts`

**Type:** array of artifact objects  
**Required:** yes

An empty array is valid only for a non-finalized diagnostic failure with no persisted artifact other than the manifest. In normal finalized runs, the array is non-empty.

---

## 8. Artifact fields

Every artifact entry contains exactly the following required semantic fields in schema `1.0`.

### 8.1 `path`

**Type:** string  
**Required:** yes

Rules:

- relative to the run directory;
- uses `/` as separator;
- not empty;
- not absolute;
- no drive letter;
- no URI scheme;
- no `.` terminal identity;
- no traversal outside the run root;
- normalized;
- unique after normalization;
- points to a file, not a directory;
- MUST NOT equal `manifest.json`.

Examples:

```text
summary.json
raw/master.log
raw/compile/lib_src_noun.out.txt
artifacts/gfo/NounX.gfo
artifacts/pgf/GrammarX.pgf
```

### 8.2 `role`

**Type:** string enum  
**Required:** yes

The role describes semantic purpose, not extension.

Canonical schema `1.0` roles:

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

Adding a role requires a compatible schema review and at least a minor schema increment when strict readers are expected.

### 8.3 `media_type`

**Type:** string  
**Required:** yes

Use a stable media type.

Canonical examples:

```text
application/json
text/markdown; charset=utf-8
text/plain; charset=utf-8
application/octet-stream
```

Binary GF artifacts use:

```text
application/octet-stream
```

unless GF Wordbench later standardizes a tested vendor media type through a schema update.

### 8.4 `required`

**Type:** boolean  
**Required:** yes

Meaning:

- `true`: absence or integrity failure invalidates the finalized artifact set;
- `false`: the artifact is informative or conditional.

Requiredness is resolved before manifest writing.

It is not inferred from role alone.

### 8.5 `size_bytes`

**Type:** integer  
**Required:** yes

Rules:

- zero or greater;
- actual final filesystem byte count;
- not character count;
- not compressed archive size;
- not an estimate.

An empty required file is allowed only when the owning artifact contract permits emptiness.

### 8.6 `sha256`

**Type:** lowercase hexadecimal string  
**Required:** yes

Canonical pattern:

```text
^[0-9a-f]{64}$
```

The digest covers exact file bytes.

It is computed after the writer closes the file.

### 8.7 `created_by`

**Type:** string  
**Required:** yes

Identifies the owning producer component or stable producer ID.

Recommended values:

```text
reporting_json
reporting_markdown
reporting_ai_ready
reporting_logs
runs
validation_scanner
validation_compiler
validation_scenario
validation_normalizer
validation_pgf
gf
```

`created_by` is a logical producer identity, not necessarily a Python filename.

Changing internal code without changing logical ownership does not require changing the producer ID.

---

## 9. Role registry

### 9.1 `machine_summary`

Canonical artifact:

```text
summary.json
```

Expected media type:

```text
application/json
```

Normally required for every finalized run.

### 9.2 `human_summary`

Canonical artifact:

```text
summary.md
```

Expected media type:

```text
text/markdown; charset=utf-8
```

Normally required.

### 9.3 `ai_handoff`

Canonical artifact:

```text
AI_READY.md
```

Expected media type:

```text
text/markdown; charset=utf-8
```

Normally required under the current product definition.

### 9.4 `top_errors`

Canonical artifact:

```text
top_errors.txt
```

Expected media type:

```text
text/plain; charset=utf-8
```

The file may be empty when there are no errors.

### 9.5 `master_log`

Canonical example:

```text
raw/master.log
```

Contains run-level orchestration evidence.

### 9.6 `aggregate_log`

Canonical examples:

```text
raw/ALL_LOGS.TXT
raw/ALL_SCAN_LOGS.TXT
```

Aggregate logs are derived indexes or concatenations. Raw per-operation files remain authoritative for exact process evidence.

### 9.7 `scan_log`

Per-file or aggregate scan evidence.

### 9.8 `compile_stdout`

Raw stdout captured from one GF compilation operation.

### 9.9 `compile_stderr`

Raw stderr captured from one GF compilation operation.

### 9.10 `scenario_stdout`

Raw stdout captured from one scenario execution.

### 9.11 `scenario_stderr`

Raw stderr captured from one scenario execution.

### 9.12 `scenario_output`

Canonical normalized scenario output used for assertions or gold comparison.

### 9.13 `detail`

Human- or AI-readable detail artifact associated with a file, scenario, gate, or diagnostic result.

### 9.14 `gfo`

GF-generated compiled module artifact.

A `.gfo` entry is valid evidence only when tied to the current run's source and command context.

### 9.15 `pgf`

GF-generated Portable Grammar Format artifact.

A required release PGF must be non-empty and current-run-owned.

### 9.16 `other`

Used only when no schema `1.0` role applies.

`other` SHOULD be accompanied by clear path, media type, and producer identity.

Frequent use of `other` indicates the role registry should be reviewed.

---

## 10. Requiredness policy

### 10.1 Required by framework

Artifacts normally required for a finalized run:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
raw/master.log
```

The exact current policy belongs to run configuration and report contracts.

### 10.2 Required by executed stages

Examples:

- compile stdout/stderr for a compile stage;
- scenario stdout/stderr for a scenario stage;
- normalized scenario output for a comparable scenario;
- `.gfo` when the compile contract requires it;
- `.pgf` when release policy requires PGF;
- gold diff on mismatch when policy requires persisted full diff.

### 10.3 Required by mode

#### Quick

May have a smaller artifact set.

#### Checkpoint

Requires evidence for selected checkpoints and scenarios.

#### Diagnostic

May produce more optional evidence, but required executed-stage evidence remains mandatory.

#### Release

Requires the full artifact set declared by release gates and project policy.

### 10.4 Conditional requiredness

An artifact is conditionally required when an activation condition is true.

Example:

```text
release_requires_pgf = true
→ expected PGF entry required = true
```

### 10.5 Skipped stage

A skipped stage produces no tool artifact unless a skip-record artifact is explicitly defined.

The manifest must not claim a nonexistent skipped-stage output.

### 10.6 Failed stage

Failed stages may still produce required raw stdout/stderr evidence.

The result artifact may be required even when the project outcome is `FAIL`.

### 10.7 Error stage

When a process cannot launch, stdout/stderr files may be absent if no stream existed.

The run result must describe the error. The manifest must reflect only files actually created.

---

## 11. Path normalization

### 11.1 Internal source path

The writer begins with an absolute candidate file beneath the run root.

### 11.2 Canonical manifest path

The canonical path is computed as:

```text
candidate relative to resolved run root
```

then serialized with `/`.

### 11.3 Rejection cases

Reject:

```text
C:\run\summary.json
/run/summary.json
../summary.json
raw/../../outside.txt
file:///run/summary.json
\\server\share\file
```

as manifest values.

A network-backed run root may be supported, but entries remain relative to that run root.

### 11.4 Dot segments

Normalize harmless `.` segments.

Reject unresolved `..` traversal.

### 11.5 Case handling

Do not lowercase serialized paths.

On case-insensitive platforms, duplicate detection uses a case-normalized comparison key while preserving the first canonical display path.

### 11.6 Unicode normalization

The framework SHOULD preserve filesystem names.

If Unicode normalization is applied for comparison keys on a supported platform, it must be documented and tested.

### 11.7 Reserved manifest path

The following normalized value is prohibited as an entry:

```text
manifest.json
```

---

## 12. File-type policy

### 12.1 Regular files

Regular files are accepted.

### 12.2 Directories

Directories are excluded.

Their contents are listed individually when required.

### 12.3 Symlinks

Default strict policy:

```text
reject
```

Non-strict policy MAY allow a symlink only when:

- its resolved target remains under the run root;
- the target is a regular file;
- the manifest records the bytes read through the resolved target;
- archive/export behavior preserves meaning;
- policy use is visible.

Release mode SHOULD reject symlink artifact entries.

### 12.4 Hard links

Hard links may appear as regular files.

The manifest treats each path as a separate artifact path, even when inode identity is shared.

### 12.5 Special files

Reject:

- sockets;
- named pipes;
- devices;
- reparse points with unsafe semantics;
- files that cannot be read deterministically.

---

## 13. Hashing

### 13.1 Algorithm

Schema `1.0` requires:

```text
SHA-256
```

### 13.2 Input

Hash the exact final file bytes.

Do not:

- decode text;
- normalize line endings;
- strip a BOM;
- decompress;
- parse and reserialize;
- omit metadata;
- ignore trailing newlines.

### 13.3 Streaming

Large files SHOULD be hashed in chunks.

Hashing uses bounded streaming chunks; chunk size is an internal performance choice.

### 13.4 Race protection

The writer SHOULD detect files modified during hashing.

Required race-safe procedure:

1. read metadata before hashing;
2. stream bytes and calculate digest;
3. read metadata after hashing;
4. reject or retry if size or modification identity changed;
5. optionally verify digest by reopening under strict release policy.

### 13.5 Open-file writers

All owning writers MUST close their files before manifest hashing begins.

### 13.6 Hash casing

Writers emit lowercase hexadecimal.

Readers MAY accept uppercase for legacy input but canonicalize to lowercase after validation.

### 13.7 Hash mismatch

A mismatch is a manifest integrity failure.

It must not be reported as a GF syntax or linguistic failure.

---

## 14. Size calculation

### 14.1 Unit

```text
bytes
```

### 14.2 Zero-byte files

Permitted examples:

- `top_errors.txt` with no errors;
- intentionally empty optional diagnostic output.

Prohibited when the artifact contract requires content:

- required `.pgf`;
- required `summary.json`;
- required scenario normalized output unless explicitly valid;
- required raw evidence expected to contain captured text when execution produced text.

### 14.3 Size mismatch

A size mismatch invalidates the entry even if a separately computed hash somehow matches.

---

## 15. Media-type policy

### 15.1 Determination

Media type is declared by artifact role and owning contract.

It is not inferred only from file extension.

### 15.2 Canonical mapping

| Artifact kind | Media type |
|---|---|
| JSON | `application/json` |
| Markdown UTF-8 | `text/markdown; charset=utf-8` |
| Plain text UTF-8 | `text/plain; charset=utf-8` |
| `.gfo` | `application/octet-stream` |
| `.pgf` | `application/octet-stream` |
| unknown binary | `application/octet-stream` |

### 15.3 Content sniffing

Manifest generation SHOULD NOT depend on heuristic content sniffing.

### 15.4 Media mismatch

A declared media type incompatible with the owning role is a contract warning or error according to strictness.

Example:

```text
role = machine_summary
media_type = image/png
```

is an error.

---

## 16. Artifact declaration

### 16.1 Declared artifacts

Owning components register expected artifacts as structured declarations.

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ArtifactDeclaration:
    path: Path
    role: str
    media_type: str
    required: bool
    created_by: str
```

The manifest writer enriches declarations with:

```text
size_bytes
sha256
```

### 16.2 No blind recursive inventory

The writer MUST NOT recursively include every file under the run directory without policy.

Blind inclusion can:

- include temporary files;
- include partial writes;
- include editor backups;
- include secrets;
- include the manifest itself;
- classify files incorrectly.

### 16.3 Controlled discovery

Controlled discovery MAY be used for known directories and patterns.

Examples:

```text
artifacts/gfo/**/*.gfo
raw/compile/*.out.txt
raw/compile/*.err.txt
```

Each discovered file still requires role and producer resolution.

### 16.4 Undeclared files

An undeclared run file may be:

- ignored when known temporary/non-product data;
- warned about;
- rejected in strict release mode;
- added through a declared discovery rule.

Release policy SHOULD reject unexplained finalized files in owned artifact directories.

---

## 17. Manifest construction algorithm

The following algorithm is normative.

```text
INPUT:
  finalized RunResult
  resolved RunPaths
  artifact declarations
  run root
  strictness policy

1. Confirm run root exists.
2. Confirm manifest target is inside run root.
3. Resolve expected artifact declarations.
4. Add controlled discovered artifacts.
5. Normalize each candidate to a run-relative path.
6. Reject unsafe, duplicate, directory, and self entries.
7. Resolve requiredness.
8. Confirm every required artifact exists.
9. Confirm every present artifact is a permitted file type.
10. Confirm owning writers are complete.
11. Calculate final byte size.
12. Calculate SHA-256.
13. Detect mutation during hashing.
14. Build entries.
15. Sort entries by normalized path.
16. Validate root metadata and run ID.
17. Serialize canonical JSON to a sibling temporary file.
18. Validate serialized temporary manifest.
19. Atomically replace manifest.json.
20. Re-read and validate manifest.json.
21. Verify every listed file against size and digest.
22. Return structured manifest result.
```

---

## 18. Deterministic serialization

### 18.1 Artifact order

Sort by:

```text
normalized path, lexical ascending
```

### 18.2 Object key order

JSON key order is not semantically significant.

Canonical writers SHOULD use stable presentation order for review.

Canonical presentation order:

```text
schema_id
schema_version
producer
run_id
generated_at
hash_algorithm
artifacts
```

Canonical entry presentation order:

```text
path
role
media_type
required
size_bytes
sha256
created_by
```

### 18.3 Timestamps

`generated_at` is expected to differ between runs.

No content hash for the manifest itself is included.

### 18.4 Repeated generation

Regenerating the manifest over unchanged artifacts may change `generated_at`.

It should not change artifact entries.

A released run SHOULD treat manifest regeneration as an explicit maintenance action, not normal reading.

---

## 19. Self-exclusion

### 19.1 Rule

The manifest MUST NOT include:

```text
manifest.json
```

### 19.2 Reason

Including its own digest creates a recursive content dependency with no stable ordinary solution.

### 19.3 Manifest integrity

The manifest's own integrity may be protected externally through:

- archive digest;
- release-package digest;
- source-control object identity;
- detached signature;
- external checksum file.

Those mechanisms are outside schema `1.0`.

### 19.4 Summary reference

`summary.json` may reference:

```text
manifest.json
```

as the canonical manifest path.

That reference does not require the manifest to hash itself.

---

## 20. Summary and manifest consistency

### 20.1 Summary artifact map

When `summary.json` lists an artifact path, the manifest MUST contain the corresponding file entry when that artifact exists and is required by the finalized run.

### 20.2 Required summary artifact

`summary.json` itself normally appears in the manifest as:

```text
role = machine_summary
required = true
```

### 20.3 No circular read requirement

The manifest writer consumes the finalized structured run result and artifact declarations.

It MUST NOT parse human-readable reports to discover artifact paths.

### 20.4 Consistency checks

Verify:

- `run_id` matches;
- `summary.json` identifies exactly one active project and one normative language target;
- all required summary artifact paths appear;
- all manifest paths resolve beneath the same run root;
- the summary-declared manifest path equals `manifest.json`;
- mode-specific required artifacts are present;
- PGF requirement agrees with project and release result;
- scenario output entries agree with scenario results.

### 20.5 Optional summary artifact

A summary field set to `null` means no artifact is declared at that semantic key.

It must not be reconstructed automatically.

---

## 21. Finalization and circular-dependency resolution

`summary.json` contains the run outcome, while `manifest.json` hashes `summary.json`. Release integrity also depends on successful manifest generation.

GF Wordbench resolves this without self-hashing or endless rewriting.

### 21.1 Successful finalization sequence

```text
1. Complete all GF, scan, scenario, gold, diff, and PGF stages.
2. Finalize all gate results that do not depend on physical manifest writing.
3. Resolve the prospective artifact set.
4. Validate that the prospective manifest can be built.
5. Finalize RG-13 and RG-14 in memory for the success path.
6. Write final summary.json and all non-manifest reports.
7. Close every writer.
8. Hash final non-manifest artifacts.
9. Build and atomically write manifest.json.
10. Re-read and verify manifest.json.
11. Do not modify any listed artifact after successful verification.
```

### 21.2 Why this is stable

- the manifest does not hash itself;
- `summary.json` is final before hashing;
- the successful manifest result is determined from validated inputs and atomic writing;
- listed files are frozen after verification.

### 21.3 Manifest-write failure path

If manifest writing or verification fails:

1. final release state becomes `ERROR`;
2. invalid or partial manifest is removed or quarantined;
3. `summary.json` and human reports MAY be rewritten to record the manifest failure;
4. no valid `manifest.json` is claimed;
5. the run remains diagnostically useful but is not release-ready.

A failed manifest cannot hash the rewritten failure summary because no valid manifest exists.

### 21.4 Post-manifest modification

Any modification to a listed artifact after successful manifest verification invalidates the manifest.

Normal finalization MUST prohibit such writes.

---

## 22. Manifest verification

### 22.1 Verification modes

Canonical verification modes:

```text
standard
strict
release
```

### 22.2 Standard verification

Checks:

- JSON parse;
- schema identity/version;
- required root fields;
- path safety;
- duplicate paths;
- file existence;
- size;
- SHA-256;
- no self entry.

### 22.3 Strict verification

Adds:

- unknown role rejection;
- symlink rejection;
- media-type/role validation;
- unexplained finalized-file detection where configured;
- creator registry validation;
- exact canonical path formatting;
- final newline/encoding checks for known text roles.

### 22.4 Release verification

Includes strict verification plus:

- release-mode required artifact set;
- required PGF;
- required scenario outputs;
- summary consistency;
- gate evidence consistency;
- no post-finalization modifications;
- approved toolchain and project identity references.

### 22.5 Verification result

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ManifestVerificationResult:
    status: str
    manifest_path: Path
    schema_version: str | None
    artifacts_checked: int
    required_artifacts_checked: int
    missing_paths: tuple[str, ...]
    mismatched_paths: tuple[str, ...]
    unsafe_paths: tuple[str, ...]
    warnings: tuple[str, ...]
    message: str
```

---

## 23. Verification statuses

Use canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

### 23.1 `OK`

The manifest and every required entry validate.

### 23.2 `FAIL`

Use when the manifest is structurally valid but a declared artifact no longer matches or a required artifact is absent.

Examples:

- hash mismatch;
- size mismatch;
- missing required file.

### 23.3 `ERROR`

Use when verification cannot be performed reliably.

Examples:

- unreadable manifest;
- invalid JSON;
- unsupported schema;
- unsafe path;
- programming/IO failure;
- ambiguous run root.

### 23.4 `SKIPPED`

Permitted only for a non-finalized operation that explicitly does not require a manifest.

A release run MUST NOT skip manifest verification.

---

## 24. Failure codes

Canonical diagnostic codes:

```text
MANIFEST_MISSING
MANIFEST_UNREADABLE
MANIFEST_JSON_INVALID
MANIFEST_SCHEMA_ID_INVALID
MANIFEST_SCHEMA_VERSION_UNSUPPORTED
MANIFEST_RUN_ID_MISMATCH
MANIFEST_HASH_ALGORITHM_INVALID
MANIFEST_ARTIFACT_ENTRY_INVALID
MANIFEST_ARTIFACT_PATH_EMPTY
MANIFEST_ARTIFACT_PATH_ABSOLUTE
MANIFEST_ARTIFACT_PATH_TRAVERSAL
MANIFEST_ARTIFACT_PATH_DUPLICATE
MANIFEST_ARTIFACT_PATH_SELF
MANIFEST_ARTIFACT_MISSING
MANIFEST_ARTIFACT_NOT_FILE
MANIFEST_ARTIFACT_SYMLINK
MANIFEST_ARTIFACT_SIZE_MISMATCH
MANIFEST_ARTIFACT_HASH_MISMATCH
MANIFEST_ARTIFACT_MUTATED_DURING_HASH
MANIFEST_ROLE_UNKNOWN
MANIFEST_MEDIA_TYPE_INVALID
MANIFEST_CREATED_BY_UNKNOWN
MANIFEST_REQUIRED_ARTIFACT_UNDECLARED
MANIFEST_SUMMARY_INCONSISTENT
MANIFEST_ATOMIC_WRITE_FAILED
MANIFEST_POSTWRITE_VERIFY_FAILED
```

Codes are stable. Human wording may improve.

---

## 25. Release-gate integration

The manifest is part of:

```text
RG-13 — Evidence, reports, and manifest integrity
```

Release requirements include:

- manifest schema valid;
- manifest path canonical;
- every required artifact listed;
- every required artifact exists;
- every entry size matches;
- every entry SHA-256 matches;
- no unsafe path;
- no duplicate path;
- no self entry;
- required PGF present when configured;
- summary and manifest consistent;
- manifest re-read verification succeeds.

### 25.1 Decision mapping

Required manifest mismatch:

```text
RG-13 status = ERROR or FAIL according to failure type
release decision != READY
```

Integrity corruption discovered after finalization normally produces `ERROR` for the verification operation.

### 25.2 Missing manifest

A release without a valid manifest is not ready.

---

## 26. Non-release runs

### 26.1 Quick

A quick run SHOULD produce a manifest when the run reaches normal finalization.

### 26.2 Checkpoint

A checkpoint run SHOULD manifest all selected compile and scenario evidence.

### 26.3 Diagnostic

A diagnostic run SHOULD manifest large raw evidence and explicitly record any truncation artifacts.

### 26.4 Aborted/cancelled run

A cancelled run MAY lack a canonical manifest if finalization could not safely complete.

If a partial manifest is written, it MUST NOT be presented as a finalized canonical manifest unless its schema and semantics explicitly support partial state. Schema `1.0` does not define a separate partial-manifest state.

### 26.5 Catastrophic startup failure

No manifest is required when no run directory could be created.

---

## 27. Raw evidence

### 27.1 Separate streams

Compilation and scenario stdout/stderr remain separate files and separate entries.

### 27.2 Raw immutability

Hash raw files before any process that could rewrite them.

Normalizers read raw files and create separate derived artifacts.

### 27.3 Truncation

When output limits require truncation:

- truncation must be explicit;
- the raw artifact must indicate truncation;
- the manifest hashes the actual stored bytes;
- reports must not imply complete output;
- release policy determines whether truncation is acceptable.

### 27.4 Aggregate logs

Aggregate logs do not replace per-operation evidence.

They are separate entries with `aggregate_log`.

---

## 28. GF-generated artifacts

### 28.1 `.gfo`

Manifest entry requirements:

```text
role = gfo
media_type = application/octet-stream
created_by = gf or validation_compiler
```

A `.gfo` must be associated with the current run.

### 28.2 `.pgf`

Manifest entry requirements:

```text
role = pgf
media_type = application/octet-stream
required = true when project release policy requires PGF
created_by = gf or validation_pgf
```

A required PGF must:

- exist;
- be non-empty;
- match expected name;
- be in the current run artifact root;
- be produced from configured release entrypoints;
- be hashed after build completion.

### 28.3 Other GF outputs

Use an existing role when appropriate.

Use `other` only until a schema-reviewed role exists.

### 28.4 No source-directory artifacts

Release artifacts SHOULD be isolated from source directories.

Files generated outside the run root must be copied into an owned run artifact directory before cataloguing, without rewriting their bytes.

---

## 29. Scenario and gold artifacts

### 29.1 Scenario streams

Use:

```text
scenario_stdout
scenario_stderr
```

### 29.2 Normalized output

Use:

```text
scenario_output
```

### 29.3 Gold files

Project `.gold` files are project inputs, not run-generated artifacts.

They normally do not appear as run manifest entries.

Their paths and SHA-256 values SHOULD be recorded in scenario results or release evidence.

### 29.4 Gold diffs

Schema `1.0` has no dedicated `gold_diff` role.

Until a role is added through schema review, a persisted diff uses:

```text
role = detail
```

or:

```text
role = other
```

with clear `created_by`.

### 29.5 Comparison integrity

The normalized current output in the manifest must be the exact file used by the gold comparator.

---

## 30. Portfolio consumption

A finalized manifest is a public Wordbench artifact suitable for optional read-only consumption by `gf-portfolio`.

The Portfolio adapter:

1. validates the manifest schema and paths;
2. verifies required hashes according to its ingestion policy;
3. locates the required `machine_summary`;
4. reads project and language identity from `summary.json`;
5. stores Portfolio-owned indexing and aggregation state separately;
6. records the source manifest schema and digest;
7. leaves the Wordbench run unchanged.

Portfolio ingestion failure does not change the Wordbench run status or manifest.

A Portfolio-specific cache, database, index or readiness model must not be added to the Wordbench manifest schema.

---

## 31. Security

### 30.1 Path containment

Manifest paths must remain under the run root after resolution.

### 30.2 No secret discovery

The writer must not recursively inventory arbitrary files.

### 30.3 Secret scanning

Release policy MAY scan text artifacts before manifest finalization.

Detected secrets block release and should be redacted at the owning writer, not by the manifest writer.

### 30.4 Executable files

The manifest may inventory executable helper artifacts only under explicit policy.

### 30.5 Untrusted manifest

A manifest loaded from another source is untrusted input.

Readers must validate paths before filesystem access.

### 30.6 Hashes are not signatures

SHA-256 detects content change relative to the manifest.

It does not prove who created or approved the manifest.

### 30.7 Detached signatures

Detached signatures require a separate security and schema contract.

---

## 32. Atomic writing

### 32.1 Procedure

The writer MUST:

1. serialize to a sibling temporary file;
2. flush and close;
3. validate temporary JSON and schema;
4. atomically replace `manifest.json`;
5. re-read and validate final file.

### 32.2 Existing manifest

Normal initial finalization creates the manifest once.

Regeneration explicitly replaces it atomically.

### 32.3 Failure

A failed write MUST NOT leave a partial file at the canonical path.

### 32.4 Temporary filename

Temporary files must not be catalogued.

They should be cleaned after success or recoverable failure.

---

## 33. Archive and export behavior

### 33.1 Run archive

An archive of a run SHOULD preserve:

- relative paths;
- file bytes;
- `manifest.json`;
- permissions when relevant;
- UTF-8 filenames.

### 33.2 Verification after extraction

After extraction, the canonical CLI manifest-verification operation produces the same artifact-integrity result.

Exact syntax is defined by `docs/usage/CLI_REFERENCE.md`.

### 33.3 Archive digest

An archive may have its own external SHA-256.

That digest is separate from `manifest.json`.

### 33.4 Portable export

A portable export MAY redact local absolute paths inside reports only when:

- a new export artifact is produced;
- original run artifacts remain preserved;
- the export has its own manifest;
- redaction is explicit.

Modifying a manifested run artifact in place is prohibited.

---

## 34. Cleanup and retention

### 34.1 Manifest-aware cleanup

Cleanup tooling SHOULD use the manifest to distinguish owned artifacts from unrelated files.

### 34.2 Required artifact deletion

Deleting a required manifested artifact invalidates the run's integrity.

### 34.3 Optional artifact deletion

Deleting an optional manifested artifact also makes the original manifest fail verification.

Optional means not required for run success, not disposable without integrity impact.

### 34.4 Derived reduced package

To remove optional files while preserving integrity, create a new package and new manifest.

### 34.5 Retention policy

Retention policy belongs to operations documentation.

The manifest records integrity, not retention duration.

---

## 35. Migration

### 35.1 Legacy GF Audit runs

Earlier GF Audit runs may lack `manifest.json`.

They remain readable historical runs but are:

```text
manifest_status = absent_legacy
```

They are not retroactively verified.

### 35.2 Migration-generated manifest

A migration tool MAY generate a manifest for a legacy run when:

- run root is identifiable;
- artifact paths are safe;
- ownership and role can be recovered;
- migration provenance is recorded through a compatible schema extension or a separate migration record;
- no claim is made that historical bytes are original when provenance is uncertain.

### 35.3 Canonical writer

New GF Wordbench runs emit only the latest supported canonical manifest schema.

### 35.4 Schema change

Breaking examples:

- changing path base;
- removing required entry fields;
- changing hash meaning;
- allowing directories as entries;
- changing self-exclusion;
- redefining role meaning.

Compatible examples:

- adding an optional root field with a safe default;
- adding an optional artifact field;
- adding a new role through minor-version policy.

---

## 36. CLI behavior

The CLI exposes manifest operations equivalent to:

```text
show manifest metadata
verify artifact integrity
verify under strict or release policy
create a manifest through an explicit maintenance operation
```

Exact command names, arguments and exit codes are owned by `docs/usage/CLI_REFERENCE.md`.

### 36.1 Show behavior

The show operation displays:

- schema version;
- run ID;
- generation time;
- entry count;
- required count;
- roles;
- total bytes.

### 36.2 Verify behavior

The verify operation validates the manifest and listed file integrity. It returns structured verification status and the documented CLI exit code.

### 36.3 Create behavior

Creation is normally part of run finalization.

A manual maintenance operation must not guess missing ownership, role or requiredness. It either resolves declarations from supported structured evidence or fails explicitly.

### 36.4 Display example

```text
Manifest: OK
Schema: gf-wordbench.artifact-manifest/1.0
Run: 20260722_163210
Artifacts checked: 42
Required artifacts: 18
Total bytes: 1849201
```

---

## 37. GUI behavior

The GUI SHOULD display:

- manifest status;
- schema version;
- artifact count;
- required artifact count;
- verification action;
- grouped artifact roles;
- path, size, hash, and producer;
- first integrity failure;
- links to open artifacts.

The GUI MUST NOT:

- rewrite the manifest during viewing;
- silently ignore mismatches;
- infer success from file existence;
- hide unsafe paths;
- recalculate a different artifact set from the manifest writer.

---

## 38. CI behavior

A release CI job SHOULD:

1. run release validation;
2. require a valid manifest;
3. verify the manifest in a separate read-only step;
4. publish the full run directory or approved release package;
5. publish the PGF only when release decision is `READY`;
6. retain verification output.

### 38.1 Post-publication verification

CI MAY download the published artifact package and re-run verification.

### 38.2 Working-directory mutation

No step may modify manifested files between manifest creation and publication.

### 38.3 Failure

Any required artifact mismatch fails the CI release job.

---

## 39. Canonical conceptual models

```python
@dataclass(frozen=True, slots=True)
class ArtifactManifestEntry:
    path: str
    role: str
    media_type: str
    required: bool
    size_bytes: int
    sha256: str
    created_by: str
```

```python
@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    schema_id: str
    schema_version: str
    producer_name: str
    producer_version: str
    run_id: str
    generated_at: str
    hash_algorithm: str
    artifacts: tuple[ArtifactManifestEntry, ...]
```

```python
@dataclass(frozen=True, slots=True)
class ManifestWriteResult:
    status: str
    manifest_path: Path | None
    entry_count: int
    required_entry_count: int
    total_size_bytes: int
    warnings: tuple[str, ...]
    message: str
```

### 39.1 Paths in models

Manifest entry paths are canonical strings because they are persisted run-relative identifiers.

Filesystem operations use resolved `Path` objects separately.

### 39.2 Central serialization

One serializer owns JSON shape and ordering.

---

## 40. API boundaries

### 40.1 Producers to manifest writer

Producers provide structured declarations.

They do not write manifest fragments.

### 40.2 Manifest writer to verifier

The writer returns:

- canonical manifest path;
- structured write result;
- optional in-memory manifest model.

### 40.3 Verifier to release engine

The verifier returns `ManifestVerificationResult`.

The release engine does not parse verification prose.

### 40.4 Reports

Reports may display manifest data.

They do not create or verify artifacts independently.

### 40.5 Cleanup/export

Cleanup and export read the manifest but do not change its meaning.

---

## 41. Prohibited behavior

The following are prohibited:

- hashing `manifest.json` inside itself;
- listing directories as artifact entries;
- using absolute artifact paths;
- permitting path traversal;
- converting artifact paths through lossy normalization;
- hashing text after decoding instead of hashing bytes;
- hashing files before writers close them;
- silently ignoring missing required artifacts;
- treating symlinks as ordinary release artifacts without policy;
- recursively including every run file blindly;
- using extension alone to determine semantic role;
- using a hash other than SHA-256 in schema `1.0`;
- modifying a listed artifact after manifest verification;
- regenerating reports after hashing without rebuilding the manifest;
- creating the manifest from human report prose;
- assigning one path multiple roles through duplicate entries;
- including project source or gold files as run-generated artifacts without an explicit copy/export contract;
- considering an optional artifact removable while preserving original manifest validity;
- claiming release readiness without manifest verification;
- allowing `gf-portfolio` or another consumer to rewrite the run;
- storing Portfolio registry, cache or readiness state in the Wordbench manifest.

---

## 42. Drift indicators

Manifest drift is likely when:

- a new artifact is written but never declared;
- two modules define the same artifact path;
- `summary.json` lists a path absent from the manifest;
- a manifest reader reconstructs filenames;
- role strings appear in multiple uncoordinated registries;
- a report changes after manifest creation;
- PGF exists but is not listed;
- a missing artifact is treated as warning despite `required = true`;
- a directory appears as an entry;
- hash logic differs between writer and verifier;
- Windows and POSIX normalize paths differently;
- symlinks pass in one mode and fail silently in another;
- `manifest.json` appears in its own artifacts array;
- schema changes without version change;
- cleanup deletes an entry without creating a new manifest;
- archive export changes bytes but reuses the old manifest;
- manifest generation depends on Portfolio state or availability.

Every indicator requires contract review.

---

## 43. Required tests

Required coverage is organized around:

```text
tests/reports/test_manifest_writer.py
tests/reports/test_manifest_verifier.py
tests/schemas/test_manifest_schema.py
tests/contracts/test_artifact_manifest_contract.py
tests/integration/test_run_manifest.py
tests/integration/test_release_manifest.py
tests/migrations/test_legacy_manifest.py
```

### 43.1 Schema tests

- valid canonical manifest;
- missing `schema_id`;
- wrong `schema_id`;
- missing `schema_version`;
- unsupported major version;
- missing producer;
- missing run ID;
- wrong hash algorithm;
- missing artifacts array;
- malformed artifact object;
- unknown required role in strict mode;
- Unicode round trip;
- deterministic ordering.

### 43.2 Path tests

- root-level file;
- nested file;
- Windows separator input canonicalized;
- absolute Windows path rejected;
- POSIX absolute path rejected;
- `..` traversal rejected;
- URI rejected;
- duplicate path rejected;
- case-only duplicate on Windows;
- directory rejected;
- self entry rejected;
- symlink strict rejection;
- path with spaces;
- Unicode filename.

### 43.3 Hash tests

- correct SHA-256;
- one-byte modification;
- newline modification;
- size mismatch;
- uppercase legacy hash accepted by migration only;
- mutation during hash;
- large streaming file;
- empty permitted file;
- empty required PGF rejected by release policy.

### 43.4 Requiredness tests

- missing required artifact;
- missing optional declaration;
- optional present artifact;
- conditional PGF required;
- failed compile still requires raw logs;
- skipped scenario has no fabricated output.

### 43.5 Consistency tests

- summary run ID mismatch;
- summary project identity missing or inconsistent;
- summary required path absent;
- scenario result output absent;
- PGF requirement mismatch;
- unknown extra file strict behavior;
- creator/role mismatch;
- media-type mismatch.

### 43.6 Atomic-write tests

- successful replacement;
- invalid temporary JSON;
- destination write failure;
- previous valid manifest preserved;
- postwrite re-read failure;
- temporary cleanup.

### 43.7 Finalization tests

- successful release finalization;
- manifest write failure transitions run to error;
- no listed file changes after verification;
- summary finalized before hashing;
- manifest not self-listed;
- re-verification after archive extraction.

---

## 44. Example complete manifest

```json
{
  "schema_id": "gf-wordbench.artifact-manifest",
  "schema_version": "1.0",
  "producer": {
    "name": "gf-wordbench",
    "version": "1.0.0"
  },
  "run_id": "20260722_163210",
  "generated_at": "2026-07-22T16:32:11Z",
  "hash_algorithm": "sha256",
  "artifacts": [
    {
      "path": "AI_READY.md",
      "role": "ai_handoff",
      "media_type": "text/markdown; charset=utf-8",
      "required": true,
      "size_bytes": 8210,
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "created_by": "reporting_ai_ready"
    },
    {
      "path": "artifacts/pgf/GrammarX.pgf",
      "role": "pgf",
      "media_type": "application/octet-stream",
      "required": true,
      "size_bytes": 481920,
      "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "created_by": "validation_pgf"
    },
    {
      "path": "raw/master.log",
      "role": "master_log",
      "media_type": "text/plain; charset=utf-8",
      "required": true,
      "size_bytes": 12391,
      "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "created_by": "runs"
    },
    {
      "path": "summary.json",
      "role": "machine_summary",
      "media_type": "application/json",
      "required": true,
      "size_bytes": 28943,
      "sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "created_by": "reporting_json"
    },
    {
      "path": "summary.md",
      "role": "human_summary",
      "media_type": "text/markdown; charset=utf-8",
      "required": true,
      "size_bytes": 7392,
      "sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "created_by": "reporting_markdown"
    },
    {
      "path": "top_errors.txt",
      "role": "top_errors",
      "media_type": "text/plain; charset=utf-8",
      "required": true,
      "size_bytes": 0,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "created_by": "reporting_logs"
    }
  ]
}
```

The example hashes other than the known empty-file SHA-256 are placeholders and are not valid evidence for real files.

---

## 45. Example verification failure

```json
{
  "status": "FAIL",
  "manifest_path": "manifest.json",
  "schema_version": "1.0",
  "artifacts_checked": 17,
  "required_artifacts_checked": 12,
  "missing_paths": [],
  "mismatched_paths": [
    "artifacts/pgf/GrammarX.pgf"
  ],
  "unsafe_paths": [],
  "warnings": [],
  "message": "One required artifact does not match its recorded SHA-256."
}
```

---

## 46. Review checklist

Before declaring manifest integrity `OK`:

```text
[ ] Schema identity is correct
[ ] Schema version is supported
[ ] Producer metadata is present
[ ] Run ID matches summary and directory
[ ] Hash algorithm is SHA-256
[ ] Entries are deterministically ordered
[ ] Paths are run-relative
[ ] Paths use forward slashes
[ ] No path traversal exists
[ ] No duplicate path exists
[ ] manifest.json is not listed
[ ] No directory is listed
[ ] Symlink policy passes
[ ] Every required artifact exists
[ ] Every size matches
[ ] Every SHA-256 matches
[ ] Roles are valid
[ ] Media types are valid
[ ] Producers are valid
[ ] Summary artifact paths are represented
[ ] Required scenario evidence is represented
[ ] Required PGF is represented
[ ] Final manifest was written atomically
[ ] Final manifest was re-read and verified
[ ] No listed artifact changed afterward
```

---

## 47. Change policy

A manifest change is contract-significant when it changes:

- schema identity;
- schema version;
- path base;
- required root fields;
- required entry fields;
- role meanings;
- hash algorithm;
- byte-hashing semantics;
- requiredness semantics;
- self-exclusion;
- symlink policy;
- deterministic ordering;
- summary consistency;
- finalization order;
- release-gate behavior.

A coordinated change MUST update:

1. persisted-schema lock;
2. manifest models;
3. writer;
4. verifier;
5. artifact declarations;
6. run finalizer;
7. release gates;
8. summary schema/reference when affected;
9. CLI and GUI;
10. archive/cleanup tooling;
11. unit, contract, schema, migration, and integration tests;
12. this document;
13. release and migration notes.

---

## 47. Governing rule

The manifest is the run's integrity ledger.

It is created only after owned artifacts are finalized, and its entries describe exact bytes.

> A required artifact that is absent, unsafe, modified, misidentified, or unverifiable invalidates the artifact set.

`manifest.json` never hashes itself. Its trust may be extended by an external archive digest or signature, but its internal responsibility remains precise: enumerate and verify every declared run artifact without rewriting any of them.
