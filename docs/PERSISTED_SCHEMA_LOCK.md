# GF Wordbench — Persisted Schema Lock

**Document ID:** `GF-WB-PERSISTED-SCHEMA-LOCK`  
**Status:** Normative  
**Contract version:** `2.1.0`  
**Applies to:** Wordbench configuration, application state, run directories, summaries, manifests, scenario evidence, gold expectations and public artifact contracts  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Schema inventory authority:** exact field inventories belong to their schema reference documents and must remain synchronized with the corresponding writers and readers

---

## 1. Purpose

This file prevents drift in data that survives beyond one in-memory operation. A persisted change is incomplete until writers, readers, versions, migrations, tests and owner documentation agree.

The core rule is:

> A persisted schema changes only through an explicit, versioned and tested contract change.

## 2. Product boundary

Wordbench persistence is mono-project and run-scoped.

- `project/project.toml` represents exactly one active GF language project in one Wordbench workspace.
- Each run, summary, manifest and release artifact identifies exactly one resolved active project and one normative language target.
- Wordbench schemas do not contain a Portfolio workspace registry, selectable project list, language-profile selector, cross-workspace aggregation state or portfolio-readiness state.
- `gf-portfolio` owns independent schema identifiers, versions, migrations, storage and retention.
- Portfolio may read public, finalized Wordbench artifacts without mutating them.
- Wordbench must not require Portfolio state, a Portfolio database or a Portfolio service.

## 3. Normative schema rules

Every machine-readable persisted schema must define:

```text
schema identifier
schema version
owner writer
supported readers
required identity fields
optional fields and defaults
unknown-field policy
path representation
serialization encoding
migration policy
retention or lifecycle when applicable
verification method and owning tests
```

Locked rules:

- schema version is independent from application version;
- unknown major versions are rejected unless a documented compatibility adapter exists;
- compatible additions define defaults and reader behavior;
- breaking changes use a new major version and migration path;
- writers serialize deterministically;
- readers do not silently reinterpret malformed data;
- examples illustrate contracts but do not replace schema definitions, writers, readers or tests.

## 4. Encoding and serialization

Canonical persisted text uses UTF-8. Machine-readable JSON must not emit `NaN`, `Infinity` or other non-JSON values. Sets or maps with unstable iteration order are serialized deterministically.

Canonical portable paths use `/` and are relative to the owning root whenever possible.

Persisted timestamps use an explicit timezone and machine-readable format. Human display formats do not replace canonical timestamps.

Stable text comparison normalizes documented line-ending differences while retaining raw evidence where applicable.

## 5. Path ownership

### 5.1 Project-owned paths

Paths to sources, scenarios, inputs, golds and project documentation are relative to `project/` unless an owner contract explicitly defines an external alias.

They must not embed:

- developer-specific drive letters;
- user-home aliases;
- unresolved environment variables;
- normalized `..` escapes;
- Portfolio roots.

### 5.2 Run-owned paths

Manifest references to files inside a run directory are relative to that run directory. A run artifact cannot point outside approved run and project evidence roots without an explicit external-reference contract.

### 5.3 Environment-owned paths

GF executable, RGL installation and output-root locations are environment or application configuration. They are not portable active-language facts.

## 6. Schema and artifact registry

| Schema or artifact | Canonical owner | Minimum locked identity | External visibility |
|---|---|---|---|
| `project/project.toml` | active project / projects module | schema version, project ID, language identity, source and validation policy | project-local |
| application state | state adapter | schema version, non-authoritative UI/application preferences | private Wordbench state |
| run directory | runs module | run ID, project ID, lifecycle status | Wordbench-owned |
| `summary.json` | reporting module | schema version, run ID, project identity, terminal status, result summaries | public versioned artifact |
| `manifest.json` | reporting/finalization | schema version, run ID, artifact entries, hashes or freshness metadata when defined | public versioned artifact |
| `summary.md` | reporting module | run and project identity, status, major findings | public human-readable artifact |
| `AI_READY.md` | reporting module | explicit evidence references and non-normative interpretation boundary | public human-readable artifact |
| raw process evidence | external-tool adapter / run | request identity, stdout, stderr, exit/termination state | Wordbench evidence; may be referenced publicly |
| normalized scenario output | validation module | scenario ID, normalization profile/version, source evidence reference | run evidence |
| `.gold` files | active project | scenario ID, reviewed expected normalized output | project-local contract |

Canonical filenames are defined by their owner reference documents and must remain synchronized with the writers, readers, manifests and tests that use them.

## 7. `project/project.toml` contract

The active project owns this file. Wordbench reads it and does not silently rewrite it during normal validation.

Minimum locked semantics:

```text
one project identity
one language identity
one project root
source selection
GF path policy
entrypoints and checkpoints
required and optional scenarios
release policy
schema version
```

Invariants:

- one file represents exactly one active language project and one normative language target;
- project ID remains stable after published runs exist, unless a versioned migration says otherwise;
- ordered fields remain ordered;
- scenario IDs are unique;
- entrypoints and required project files must exist before the corresponding release gate can pass;
- executable and machine-specific output paths are not stored as language-project facts;
- Portfolio fields are prohibited.

The detailed field inventory belongs to `docs/configuration/PROJECT_TOML_REFERENCE.md` and must remain synchronized with the parser, validation rules, examples and tests.

## 8. Application state contract

Application state may store non-authoritative preferences such as window state, last opened view or permitted environment selections.

It must not become authority for:

- active language identity;
- a second active project;
- project source paths that contradict `project.toml`;
- release status;
- validation success;
- Portfolio workspace membership.

State corruption must not silently change project identity. Recovery or reset behavior is explicit.

## 9. Run directory contract

One run owns one run directory.

Minimum lifecycle states distinguish:

```text
created
running
finalizing
succeeded
failed
cancelled
timed_out
incomplete or recovery-required
```

Exact canonical status values are owned by `docs/reference/STATUS_VALUES.md`; this lock requires that terminal and non-terminal states cannot be confused.

Locked rules:

- run identity is unique within its artifact root;
- active project identity is recorded at run creation;
- artifacts from another run do not satisfy the current run;
- partial artifacts remain identifiable as partial;
- finalization records completion before an artifact is advertised as finalized;
- cleanup cannot remove project-owned sources, scenarios, inputs or golds;
- recovery preserves evidence needed to explain interruption.

## 10. Summary contract

Machine-readable summaries are derived from finalized typed results. They do not independently rerun validation or infer project identity.

Minimum semantics:

```text
schema ID and version
run identity
active project identity
start/end or duration information
terminal run status
stage results
file and scenario result summaries
diagnostic summaries
artifact references
incompleteness or truncation indicators
```

A summary cannot represent a timed-out, cancelled or incomplete run as a complete success.

## 11. Manifest contract

The manifest inventories artifacts owned by the run.

Each entry identifies, as applicable:

```text
logical role
relative path
media or artifact type
size
hash or freshness evidence
producer
availability or completeness
schema identity for structured artifacts
```

Locked rules:

- manifest paths are portable and run-relative;
- missing required artifacts are explicit;
- stale files are not silently included as current outputs;
- public/private classification is explicit when introduced;
- Portfolio may consume published entries but cannot rewrite the Wordbench manifest.

## 12. Scenario, normalized output and gold contract

Relationships are keyed by stable scenario ID.

```text
scenario registration -> .gfs file -> declared inputs -> raw transcript
-> marker extraction -> named normalization -> normalized output -> reviewed gold
```

Locked rules:

- raw transcript is retained before normalization;
- normalization version or profile is identifiable when it affects comparison;
- gold files contain reviewed expected normalized output, not raw mutable logs;
- normal validation never updates golds;
- a gold update is explicit, reviewable and attributable;
- line-ending normalization does not permit semantic rewriting.

## 13. Public artifact boundary

A Wordbench artifact is public only when its owner contract says so and its schema/version is present or otherwise unambiguous.

For `gf-portfolio` consumption:

- only finalized public artifacts are supported;
- private application state and private module APIs are not supported interfaces;
- the consumer handles its own indexing and migration state;
- read failure or incompatibility does not mutate the source run;
- public schema evolution follows semantic compatibility rules and migration notes.

## 14. Migration and compatibility

A schema change is classified as:

- **compatible repair**: clarifies or fixes invalid output without changing valid consumer meaning;
- **compatible extension**: adds optional data with defined defaults;
- **breaking change**: removes, renames, retypes or reinterprets required data;
- **historical read support**: reader accepts a documented legacy schema without writing it anew.

Breaking changes require:

1. new major schema version;
2. reader and writer coordination;
3. migration or explicit non-migratable decision;
4. fixtures for old and new formats;
5. release and deprecation notes;
6. public consumer impact review;
7. lock and ledger update.

No new unversioned machine schema may be introduced.

## 15. Validation requirements

Schema verification should include:

- round-trip tests where appropriate;
- required-field and malformed-data tests;
- unknown-version tests;
- deterministic serialization tests;
- path portability and traversal tests;
- migration fixtures;
- incomplete-run fixtures;
- stale-artifact rejection;
- public artifact compatibility fixtures;
- proof that Wordbench works without Portfolio state.

Documented schema tests must correspond to executable tests or fixtures maintained with the owning schema.

## 16. Change control checklist

```text
[ ] owner writer and all readers identified
[ ] schema ID and version reviewed
[ ] one active project and target remain explicit
[ ] project, environment and run paths remain distinct
[ ] malformed and unknown versions fail explicitly
[ ] migration or compatibility behavior is documented
[ ] raw and normalized evidence remain distinct
[ ] stale artifacts cannot satisfy current runs
[ ] public artifact impact is reviewed
[ ] no Portfolio registry or private state entered Wordbench
[ ] schema definitions, writers, readers, references and tests agree
[ ] schema references, tests, release notes and ledger are updated
```
