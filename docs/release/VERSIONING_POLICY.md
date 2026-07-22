# GF Wordbench — Versioning Policy

**Document ID:** `GF-WB-RELEASE-VERSIONING-POLICY`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\release\VERSIONING_POLICY.md`  
**Applies to:** Framework releases, language-project releases, persisted schemas, normalization, contracts, documentation and compatibility declarations  
**Owner:** GF Wordbench maintainers  
**Framework package:** `gf-wordbench`  
**Framework version source:** `app/__init__.py`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines how GF Wordbench versions every independently evolving public contract.

GF Wordbench contains several kinds of versioned objects:

- the Python framework package;
- the active language project;
- persisted schemas;
- scenario-output normalization;
- framework and project contract locks;
- normative documentation;
- external-tool compatibility declarations;
- published artifacts.

These versions are related, but they are not interchangeable.

The central rule is:

> Every version number identifies one explicit compatibility domain, and no consumer may infer another domain’s compatibility from that number.

Examples:

- `gf-wordbench 1.4.2` does not imply schema `1.4`;
- schema `gf-wordbench.run-summary/1.1` does not imply package `1.1.0`;
- normalization `1.1` does not imply project release `1.1.0`;
- GF `3.x` does not imply compatibility with every GF Wordbench release;
- contract version `2.0.0` does not imply a package major release unless the changed contract is public to package users.

---

## 2. Scope

This document governs:

- framework package-version syntax;
- framework major, minor and patch meaning;
- pre-`1.0.0` policy;
- release and prerelease identifiers;
- version source of truth;
- Git-tag naming;
- package metadata;
- active-language-project release identifiers;
- persisted-schema versions;
- normalization versions;
- contract-lock versions;
- normative-document versions;
- external-tool compatibility versions;
- artifact version metadata;
- version-bump classification;
- coordinated multi-domain changes;
- changelog requirements;
- deprecation windows;
- release compatibility;
- version tests;
- anti-drift checks.

This document does not govern:

- the detailed release procedure;
- branch naming;
- repository hosting;
- package repository credentials;
- changelog prose format beyond required information;
- GF upstream release policy;
- Python upstream release policy;
- active-project linguistic release criteria;
- persisted field definitions;
- exact migration implementation;
- release signing infrastructure.

Those subjects belong to their dedicated documents.

---

## 3. Related normative documents

```text
CHANGELOG.md
pyproject.toml
app/__init__.py
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/projects/PROJECT_MODEL.md
docs/release/RELEASE_PROCESS.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/reference/SCHEMA_INDEX.md
docs/reference/COMMAND_REFERENCE.md
docs/gf/GF_VERSION_COMPATIBILITY.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/RELEASE_CRITERIA.md
```

`VERSIONING_POLICY.md` owns version meanings.

`RELEASE_PROCESS.md` owns the operational steps that create a release.

`MIGRATION_AND_DEPRECATION.md` owns migration execution and deprecation lifecycle.

`PERSISTED_SCHEMA_LOCK.md` owns each persisted format.

---

## 4. Normative terminology

- **VERSION DOMAIN**: one independently versioned compatibility surface.
- **FRAMEWORK VERSION**: version of the distributable `gf-wordbench` Python application.
- **PROJECT RELEASE VERSION**: release identifier of one active language grammar project.
- **SCHEMA VERSION**: version of one persisted data format identified by one immutable schema ID.
- **NORMALIZATION VERSION**: version of canonical scenario-output transformation and comparison semantics.
- **CONTRACT VERSION**: version of one normative interfile or external-tool contract lock.
- **DOCUMENT VERSION**: version of one normative document’s own content.
- **TOOL VERSION**: version reported by an external dependency such as GF or Python.
- **ARTIFACT VERSION**: release identity associated with a published artifact.
- **PRODUCER VERSION**: framework version that wrote a persisted artifact.
- **MAJOR CHANGE**: incompatible change within one version domain.
- **MINOR CHANGE**: backward-compatible capability addition within one version domain.
- **PATCH CHANGE**: backward-compatible correction within one version domain.
- **PRERELEASE**: identified build intended for testing before a final release.
- **DEVELOPMENT VERSION**: non-final build from an unreleased code state.
- **MIGRATION**: explicit conversion from an older contract or schema to a newer one.
- **DEPRECATION**: supported feature or contract scheduled for removal.
- **RELEASE TAG**: immutable source-control tag identifying a release commit.
- **COMPATIBILITY RANGE**: explicit set or interval of versions accepted by one consumer.
- **CURRENT VERSION**: version emitted by current canonical writers.
- **SUPPORTED VERSION**: version current readers can interpret safely.
- **LEGACY VERSION**: older version accepted only through documented compatibility or migration.

---

# Part I — Version-domain separation

## 5. Canonical version domains

GF Wordbench recognizes these primary version domains:

| Domain | Example | Format | Primary authority |
|---|---|---|---|
| Framework package | `1.4.2` | `MAJOR.MINOR.PATCH` | `app/__init__.py` |
| Project release | `2.1.0` | `MAJOR.MINOR.PATCH` | immutable project release tag and release record |
| Persisted schema | `1.1` | `MAJOR.MINOR` | schema lock and schema implementation |
| Normalization | `1.0` | `MAJOR.MINOR` | scenario normalization contract |
| Contract lock | `1.3.0` | `MAJOR.MINOR.PATCH` | lock-file metadata |
| Normative document | `1.0.2` | `MAJOR.MINOR.PATCH` | document metadata |
| External tool | upstream value | tool-defined | external tool |
| Artifact | project or framework release | owner-defined | release manifest and tag |

### 5.1 No implicit equality

Numbers that happen to be equal remain independent.

Example:

```text
framework version:       1.0.0
project schema version:  1.0
normalization version:   1.0
project release version: 1.0.0
```

This does not create one shared version.

### 5.2 No umbrella version

GF Wordbench MUST NOT add one “system version” that attempts to replace all domains.

The framework version is the product/application version.

Other domains retain explicit identities.

### 5.3 Coordinated changes

One change may affect several domains.

Each affected domain is classified and bumped independently.

Example:

```text
rename a required summary.json field
```

may require:

```text
framework package major bump
run-summary schema major bump
persisted-schema contract major bump
migration update
documentation update
```

The package version alone is insufficient.

---

## 6. Version registry

The repository SHOULD maintain a generated or checked registry equivalent to:

```text
Framework:
  package: 0.1.0

Schemas:
  gf-wordbench.project: 1.0
  gf-wordbench.app-state: 1.0
  gf-wordbench.run-summary: 1.0
  gf-wordbench.artifact-manifest: 1.0
  gf-wordbench.scenario-output: 1.0
  gf-wordbench.scenario-gold: 1.0

Normalization:
  canonical-v1: 1.0

Contracts:
  framework interfile: <version>
  external tool: <version>
  persisted schema: <version>
  active project interfile: <version>
```

The human reference belongs in:

```text
docs/reference/SCHEMA_INDEX.md
```

The check implementation must read authoritative sources rather than maintain a second manual registry.

---

## 7. Version-source rule

Each domain has one authoritative source.

A derived display may repeat the version.

It MUST NOT become independently editable.

Examples:

```text
app/__init__.py
    → pyproject dynamic package version
    → CLI --version
    → GUI About
    → producer.version

schema implementation constant
    → serialized schema_version
    → SCHEMA_INDEX reference

normalization constant
    → `.out` header
    → `.gold` header
    → ScenarioResult
```

---

# Part II — Framework package version

## 8. Framework version format

Final framework releases use:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
0.1.0
0.2.3
1.0.0
1.4.2
2.0.0
```

Each component is a non-negative integer.

Leading zeroes are prohibited except for the single value `0`.

Valid:

```text
1.2.3
0.9.0
```

Invalid:

```text
01.2.3
1.02.3
1.2
v1.2.3
1.2.3.4
```

The `v` prefix belongs to Git tags, not the package version value.

---

## 9. Framework version source of truth

Canonical source:

```text
app/__init__.py
```

Recommended declaration:

```python
__version__ = "0.1.0"
```

`pyproject.toml` reads this value dynamically.

Conceptual packaging configuration:

```toml
[project]
name = "gf-wordbench"
dynamic = ["version"]

[tool.hatch.version]
path = "app/__init__.py"
```

### 9.1 One source only

The framework version MUST NOT be manually duplicated as an authoritative value in:

```text
pyproject.toml
README.md
launchers
app/config.py
CLI parser
GUI source
report writers
schema modules
release scripts
```

Those consumers import or derive the version.

### 9.2 Import safety

Reading the version for packaging must not require:

```text
PySide6
GF
project configuration
application state
filesystem mutation
network access
```

`app/__init__.py` must remain safe to inspect.

---

## 10. Framework major version

Increment `MAJOR` after `1.0.0` when a supported user, automation or extension must change incompatibly.

Examples:

- remove or rename the installed CLI command;
- remove a documented CLI option without a completed deprecation;
- change a CLI option’s meaning incompatibly;
- remove a supported public Python API;
- change public result semantics incompatibly;
- remove support for a previously supported project-schema major;
- remove support for a documented run-summary schema major;
- require an incompatible project migration;
- change release-gate semantics so existing valid automation becomes invalid without opt-in;
- drop a supported platform or major runtime compatibility range;
- change launcher environment-variable names without compatibility handling;
- change required artifact ownership or directory meaning incompatibly;
- change the extension boundary so existing supported integrations break.

A major bump does not excuse missing migration guidance.

---

## 11. Framework minor version

Increment `MINOR` for backward-compatible user-visible capability.

Examples:

- add a CLI command;
- add an optional CLI flag;
- add a validation mode capability without changing existing mode meaning;
- add a report artifact;
- add an optional schema reader or migration;
- support a new compatible GF version;
- add an optional project configuration field;
- add a new built-in static scan rule with compatible persistence;
- add GUI functionality using existing contracts;
- add an optional scenario type;
- add an optional manifest role;
- add a new supported platform while preserving existing ones.

A minor release may include compatible fixes.

---

## 12. Framework patch version

Increment `PATCH` for backward-compatible correction.

Examples:

- fix path quoting;
- fix a false-positive scanner implementation while preserving documented rule semantics;
- fix report formatting;
- fix timeout cleanup;
- fix an incorrect diagnostic parser;
- fix a crash on malformed optional state;
- correct packaging metadata;
- improve performance without observable contract change;
- correct an implementation to match an already locked schema;
- correct documentation shipped with the package when a package release is otherwise required.

A patch release MUST NOT introduce an undocumented incompatible behavior change.

---

## 13. Internal changes and package bumps

Not every repository commit requires a package version bump.

No package bump is required solely for:

```text
unfinished work not released
test-only refactoring
comment-only change
draft documentation outside a release
CI implementation change with no distributed behavior
local development tooling
formatting
```

Before a release, all user-visible changes since the previous release are classified together and the highest required package bump is chosen.

---

## 14. Highest-impact rule

For one framework release:

```text
MAJOR > MINOR > PATCH
```

If changes include one minor feature and several fixes:

```text
increment MINOR
reset PATCH to 0
```

If any included change is major:

```text
increment MAJOR
reset MINOR and PATCH to 0
```

Examples:

```text
1.2.4 + patch changes → 1.2.5
1.2.4 + minor change  → 1.3.0
1.2.4 + major change  → 2.0.0
```

---

# Part III — Pre-1.0 framework policy

## 15. Meaning of major zero

Versions:

```text
0.MINOR.PATCH
```

indicate that the framework is not yet under the full post-`1.0.0` stability promise.

However, major zero is not permission for undocumented drift.

### 15.1 Pre-1.0 minor

Increment `MINOR` for:

- milestone capability;
- public contract expansion;
- intentionally incompatible public changes;
- significant architecture changes;
- persisted-schema support changes;
- release-gate redesign.

Any incompatible change must be called out prominently.

Example:

```text
0.3.5 → 0.4.0
```

### 15.2 Pre-1.0 patch

Increment `PATCH` only for compatible fixes and small compatible improvements.

Example:

```text
0.4.0 → 0.4.1
```

A patch release must not silently change:

```text
schema meaning
CLI option meaning
normalization behavior
contract ownership
artifact layout
```

### 15.3 Pre-1.0 deprecation

A pre-1.0 release may use a shorter deprecation window, but removal still requires:

- explicit notice;
- migration guidance;
- changelog entry;
- contract review;
- affected tests.

### 15.4 First stable release

`1.0.0` means the maintainers commit to the stable public surfaces declared in this policy.

Minimum conditions include:

```text
canonical package identity established
CLI and GUI entrypoints stable
four validation modes defined
project schema active
application-state schema active
run-summary schema active
manifest schema active
scenario output/gold schemas active
normalization version active
contract locks reconciled
migration from supported legacy data documented
release gates implemented
Windows launchers validated
public tests passing
known limitations documented
```

---

# Part IV — Prerelease and development versions

## 16. Final-release syntax

Final package releases use only:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
1.0.0
1.3.2
```

---

## 17. Prerelease syntax

Python package prereleases use canonical forms:

```text
MAJOR.MINOR.PATCHaN
MAJOR.MINOR.PATCHbN
MAJOR.MINOR.PATCHrcN
```

Examples:

```text
1.0.0a1
1.0.0b1
1.0.0rc1
1.2.0rc2
```

Meanings:

```text
a  = alpha
b  = beta
rc = release candidate
N  = positive sequence number
```

### 17.1 Ordering

Expected progression:

```text
1.0.0a1
1.0.0a2
1.0.0b1
1.0.0rc1
1.0.0rc2
1.0.0
```

### 17.2 Stability promise

Prereleases are not final compatibility commitments.

Known breaking corrections may occur before the final target release.

Every prerelease still has:

```text
immutable source tag
test evidence
changelog state
declared schema set
```

---

## 18. Development versions

Development builds may use:

```text
MAJOR.MINOR.PATCH.devN
```

Example:

```text
1.3.0.dev4
```

Development versions are not published as final releases.

### 18.1 Commit identity

The exact source commit belongs in build metadata or release evidence, not in the canonical final version.

Examples of evidence:

```text
Git commit SHA
dirty-working-tree flag
build timestamp
CI run ID
```

### 18.2 Local version identifiers

Local package identifiers using `+...` MAY be used for private builds when supported by the packaging workflow.

They MUST NOT become official release tags.

Example:

```text
1.3.0.dev4+g1a2b3c4
```

---

## 19. No date-based framework version

Dates do not replace the framework version.

Invalid official package versions:

```text
2026-07-22
20260722
release-2026-07
```

Dates may appear in:

```text
release notes
run IDs
artifact metadata
documentation review dates
```

---

# Part V — Git tags

## 20. Framework release tags

Canonical framework tag:

```text
v<framework-version>
```

Examples:

```text
v0.1.0
v1.0.0rc1
v1.0.0
v2.3.1
```

### 20.1 Tag/version agreement

For framework release tag:

```text
tag without `v` == app.__version__
```

A mismatch blocks release.

### 20.2 Tag immutability

Published release tags MUST NOT be moved or reused.

A broken release is corrected with a new version.

### 20.3 Annotated tags

Final releases SHOULD use annotated tags.

Signing policy belongs to `RELEASE_PROCESS.md`.

---

## 21. Project release tags

When the active language project is published independently, use:

```text
project-<project-id>-v<project-version>
```

Examples:

```text
project-sqi-v1.0.0
project-fra-v2.3.1
```

### 21.1 Project ID

`<project-id>` comes from:

```text
project/project.toml
```

It is not inferred from the repository directory name.

### 21.2 Same commit, multiple releases

A framework release and project release may point to the same commit.

Example:

```text
v1.2.0
project-sqi-v2.0.0
```

The two versions remain independent.

### 21.3 Unpublished projects

A project under development does not require a formal project release version for every commit.

Git commit identity and project status documents are sufficient until publication.

---

# Part VI — Framework display and producer metadata

## 22. CLI version display

Canonical command:

```text
gf-wordbench --version
```

It displays the framework package version.

It MUST NOT display a schema version as the primary application version.

Recommended output:

```text
gf-wordbench 1.2.3
```

Optional diagnostic version output may include:

```text
Python version
GF version
supported schema versions
active project ID
normalization version
commit identity
```

Those values must be labeled separately.

---

## 23. GUI version display

The GUI About view displays:

```text
GF Wordbench <framework-version>
```

It may also display separately labeled:

```text
active project ID
project release tag when known
GF version
schema versions
normalization version
```

No combined ambiguous version string is allowed.

---

## 24. Producer metadata

Canonical persisted JSON documents SHOULD include:

```json
{
  "producer": {
    "name": "gf-wordbench",
    "version": "1.2.3"
  }
}
```

### 24.1 Meaning

`producer.version` identifies the framework release that wrote the artifact.

### 24.2 Non-authority

A reader MUST NOT use `producer.version` as a substitute for:

```text
schema_version
normalization_version
project version
GF version
contract version
```

### 24.3 Patch release and schema stability

A package patch release may write the same schema version as the previous package release.

Example:

```text
producer.version: 1.2.3
schema_version:   1.0
```

followed by:

```text
producer.version: 1.2.4
schema_version:   1.0
```

This is normal.

---

# Part VII — Persisted schema versioning

## 25. Schema identity

Every persisted schema has:

```text
immutable schema_id
explicit schema_version
```

Example:

```text
schema_id:      gf-wordbench.run-summary
schema_version: 1.0
```

A schema ID is never reused for an unrelated format.

---

## 26. Schema version format

Canonical schema versions use:

```text
MAJOR.MINOR
```

Examples:

```text
1.0
1.1
2.0
```

Patch components are not used.

Invalid:

```text
1
1.0.0
v1.0
latest
```

---

## 27. Schema major version

Increment schema `MAJOR` for incompatible persisted-format changes.

Examples:

- remove a required field;
- rename a field;
- change a field type;
- change `null` meaning;
- change path ownership;
- change relative paths to absolute paths;
- change an enum incompatibly;
- change array ordering semantics;
- change a root object into another shape;
- split one field into several required fields;
- merge fields with information loss;
- change artifact identity;
- change canonical text header incompatibly;
- change required directory layout incompatibly.

Example:

```text
gf-wordbench.run-summary/1.2
→ gf-wordbench.run-summary/2.0
```

A migration is required when existing data must remain usable.

---

## 28. Schema minor version

Increment schema `MINOR` for compatible persisted-format additions.

Examples:

- add an optional field with a documented default;
- add an optional object;
- add an optional array;
- add an optional manifest role;
- add an optional scenario-result field;
- add an enum value only when older readers safely treat unknown values according to policy;
- clarify a field while preserving its exact existing meaning;
- add non-required metadata.

Example:

```text
gf-wordbench.run-summary/1.0
→ gf-wordbench.run-summary/1.1
```

### 28.1 Reader requirement

A supported-major reader SHOULD ignore unknown optional fields.

It MUST NOT reinterpret unknown enum values.

### 28.2 Writer requirement

Canonical writers emit one current schema version.

They do not emit a mixture of optional features without updating the version when the persisted contract changed.

---

## 29. No schema patch version

Implementation fixes that preserve serialized meaning do not change schema version.

They may require a framework package patch.

Example:

```text
fix JSON writer to emit the already required final newline
```

may produce:

```text
framework: 1.2.3 → 1.2.4
schema:    1.0 unchanged
```

---

## 30. Schema versions are per schema

Each schema evolves independently.

Current target registry includes:

```text
gf-wordbench.project
gf-wordbench.app-state
gf-wordbench.run-summary
gf-wordbench.artifact-manifest
gf-wordbench.scenario-output
gf-wordbench.scenario-gold
```

Changing one does not automatically bump the others.

Example:

```text
app-state 1.0 → 1.1
```

does not require:

```text
run-summary 1.0 → 1.1
```

unless that schema also changes.

---

## 31. Schema compatibility matrix

For every framework release, tests SHOULD define compatibility equivalent to:

| Schema | Read | Write |
|---|---|---|
| project `1.0` | Yes | Yes |
| app-state `1.0` | Yes | Yes |
| run-summary `1.0` | Yes | Yes |
| legacy state unversioned | Migration only | No |
| legacy summary unversioned | Migration only | No |

The exact matrix evolves with releases.

### 31.1 Read versus write

A release may read several versions but write only the current canonical version.

Example:

```text
read:  project 1.0, 1.1
write: project 1.1
```

### 31.2 Legacy formats

Legacy unversioned formats are not assigned fake schema versions.

They remain explicitly identified as legacy.

---

## 32. Schema migration requirement

An incompatible schema change requires:

```text
new schema version
reader or migrator
source preservation
target validation
atomic target write
compatibility tests
migration documentation
changelog entry
```

A compatible minor change may not require file rewriting until the owning writer naturally writes the file.

---

## 33. Project-schema version

`project/project.toml` contains:

```text
schema_id = "gf-wordbench.project"
schema_version = "1.0"
```

This is the project-configuration format version.

It is not the language grammar’s release version.

### 33.1 No project release field in v1.0

The canonical `gf-wordbench.project/1.0` schema does not define an authoritative project release-version field.

A project release version MUST NOT be inserted ad hoc without:

- schema review;
- a compatible schema minor bump when optional;
- writer/reader updates;
- migration/default policy;
- documentation update.

### 33.2 Release identity before such a field

Until a schema explicitly adds project release metadata, the immutable project release tag and release record are authoritative.

---

# Part VIII — Scenario normalization versioning

## 34. Normalization identity

Canonical profile:

```text
canonical-v1
```

Canonical version:

```text
1.0
```

The normalization version is written in:

```text
scenario `.out` header
scenario `.gold` header
structured scenario evidence where supported
```

---

## 35. Normalization format

Normalization versions use:

```text
MAJOR.MINOR
```

No patch component is used because every output-affecting change must be visible.

---

## 36. Normalization major version

Increment `MAJOR` for incompatible canonical-output semantics.

Examples:

- change output header structure;
- change canonical section-marker syntax;
- change source stream from stdout to merged streams;
- change Unicode-preservation policy;
- change exact comparison to unordered comparison;
- change path-token meanings;
- change semantic whitespace preservation;
- change marker identity model;
- change the role of unscoped output;
- change gold artifact identity incompatibly.

A major normalization change requires explicit gold migration.

---

## 37. Normalization minor version

Increment `MINOR` for a bounded compatible normalization addition that may alter canonical output.

Examples:

- recognize one documented additional GF wrapper prompt;
- add one approved path rendering form;
- remove one newly identified ANSI control form;
- add one exact framework-owned metadata replacement;
- add one compatible legacy marker adapter.

Even a minor normalization change requires:

```text
affected gold review
normalization tests
version update
migration or regeneration decision
changelog entry
```

---

## 38. No normalization patch version

An implementation correction that makes output conform to already documented `1.0` semantics does not create `1.0.1`.

It requires:

```text
framework patch or higher
regression test
gold review if actual canonical bytes change
```

If the documented semantics themselves change, bump normalization minor or major.

---

## 39. Exact gold compatibility

A `.gold` file and actual `.out` must have the same normalization version.

The comparator MUST NOT silently apply current normalization rules to an older gold.

Version mismatch is a contract error.

---

# Part IX — Contract-lock versioning

## 40. Contract version format

Framework and project contract locks use:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
1.0.0
1.2.0
2.0.0
```

Contract versions identify the normative promises in one lock document.

They do not identify the package release.

---

## 41. Contract major version

Increment contract `MAJOR` when a provider or consumer must change incompatibly.

Examples:

- transfer ownership between components;
- remove a required public contract;
- rename a public request or response field;
- change success semantics;
- change required side effects;
- change a public module entrypoint;
- change project entrypoints incompatibly;
- change scenario marker identity incompatibly;
- change expected artifact naming incompatibly;
- change a required lincat or constructor contract;
- change the external GF command contract incompatibly.

A major contract change usually affects package or project release classification, but the exact bump is decided in the affected domain.

---

## 42. Contract minor version

Increment contract `MINOR` for a compatible extension.

Examples:

- add an optional public helper;
- add an optional request field with a safe default;
- add an optional scenario;
- add an optional entrypoint;
- add an optional manifest role;
- add a new compatible external-tool capability;
- add a new contract entry without changing existing entries;
- activate a previously documented compatible optional contract.

---

## 43. Contract patch version

Increment contract `PATCH` for normative corrections that preserve behavior.

Examples:

- fix an incorrect provider path;
- clarify an invariant without changing it;
- correct a typo in a contract ID;
- align an example with already locked behavior;
- add a missing consumer to a relationship whose dependency already existed;
- correct status metadata without changing the contract.

Pure typography with no normative effect may update only the document version or review date.

---

## 44. Contract status and version

Changing a contract entry status may require a version bump.

Examples:

```text
experimental → active
```

usually requires a compatible contract minor bump.

```text
deprecated → retired
```

requires a major bump when supported behavior is removed.

```text
planned → active
```

requires a minor bump if capability is newly supported and compatible.

The overall lock version represents the highest contract impact since its previous release.

---

## 45. Lock versions are independent

These lock files evolve independently:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

### 45.1 Template and active project

The template project lock and populated active-project lock may have related structures but different content and lifecycle.

A template structural contract change may require:

```text
template lock version bump
active project migration/review
project lock version bump when its contracts change
```

They MUST NOT be forced to share one version value automatically.

---

# Part X — Normative-document versioning

## 46. Document version format

Normative documentation may declare:

```text
Document version: MAJOR.MINOR.PATCH
```

This version describes the document’s content.

It is not a package release.

---

## 47. Document major version

Increment document `MAJOR` when its normative model is replaced incompatibly.

Examples:

- replace the repository structure model;
- redefine a validation stage;
- change ownership boundaries;
- replace a lifecycle model;
- change a public policy’s governing assumptions.

When the document describes an independently versioned contract, the corresponding contract version must also be reviewed.

---

## 48. Document minor version

Increment document `MINOR` for substantial compatible expansion.

Examples:

- add a new supported workflow;
- add a new compatible section;
- document a new optional capability;
- expand testing requirements;
- add a compatible platform-specific policy.

---

## 49. Document patch version

Increment document `PATCH` for corrections and clarifications.

Examples:

- fix a path;
- fix a misleading example;
- clarify an existing rule;
- correct internal links;
- improve wording without changing behavior.

---

## 50. Review date

`Last reviewed` is not a version.

Updating only the review date does not require a document-version bump when no content changed.

A review that changes normative text requires appropriate classification.

---

## 51. Non-normative documents

A simple guide, README or generated reference does not require its own manual document version unless it has an independent compatibility role.

Generated references SHOULD derive version information from authoritative sources.

Avoid version metadata that creates no consumer value.

---

# Part XI — Active language project release version

## 52. Project release independence

The active language grammar may be released independently from the framework.

Examples:

```text
GF Wordbench framework: 1.4.2
active project release:  2.0.0
GF tool:                 upstream 3.x
```

None of these values replaces another.

---

## 53. Project release version format

When a language project publishes stable releases, use:

```text
MAJOR.MINOR.PATCH
```

The meaning is defined relative to the project’s supported public grammar surface.

The project must identify that surface in:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/RELEASE_CRITERIA.md
project/docs/LANGUAGE_ARCHITECTURE.md
```

---

## 54. Project major version

Increment project `MAJOR` for incompatible grammar or runtime API changes.

Possible examples:

- remove or rename public abstract functions;
- change constructor types incompatibly;
- change public categories incompatibly;
- change required lincat or record shape consumed externally;
- remove a published concrete syntax;
- rename public module entrypoints;
- change PGF API surface incompatibly;
- change externally consumed parse-tree representation incompatibly;
- break documented application integration;
- replace accepted output behavior in a way requiring consumer migration.

A linguistic correction is not automatically major.

The impact depends on the project’s declared public compatibility surface.

---

## 55. Project minor version

Increment project `MINOR` for compatible capability.

Possible examples:

- add public abstract functions;
- add lexical coverage;
- add an optional concrete syntax;
- expand morphology without breaking existing constructors;
- add parsing or linearization coverage;
- add a compatible grammar module;
- add optional runtime capabilities;
- add new scenario-backed supported behavior.

Large gold changes may still be minor when they are compatible improvements.

They require deliberate review.

---

## 56. Project patch version

Increment project `PATCH` for compatible correction.

Possible examples:

- correct an inflection;
- correct agreement;
- correct orthography;
- repair one linearization;
- improve one parse without breaking documented accepted behavior;
- fix a lexical entry;
- correct internal implementation with stable public signatures.

A patch may change linguistic output.

The project must review affected scenarios and gold files.

---

## 57. Project prereleases

Project prereleases may use:

```text
MAJOR.MINOR.PATCHaN
MAJOR.MINOR.PATCHbN
MAJOR.MINOR.PATCHrcN
```

Project release tags use the same version:

```text
project-<id>-v<version>
```

---

## 58. Project release source of truth

For a published project release, authority is:

```text
immutable project release tag
+ release record
+ source commit
+ validated artifacts
```

The release record must identify:

```text
project ID
project version
framework version
project schema version
GF version
RGL identity when relevant
normalization version
source commit
PGF artifact hash when applicable
release validation run
known accepted issues
```

### 58.1 Current project schema constraint

The current project schema does not silently gain a `version` field.

A future schema minor may add an optional project release field deliberately.

Until then, release tooling receives or derives the project release version through its explicit release operation and records it in release evidence.

---

## 59. Project development state

Project development uses:

```text
STATUS_LEDGER.md
DECISION_LOG.md
RELEASE_CRITERIA.md
Git commit identity
```

These are not substitute version numbers.

Terms such as:

```text
draft
experimental
blocked
release candidate
release ready
```

describe status, not version order.

---

# Part XII — External-tool versions

## 60. GF version

The GF version is reported by GF.

GF Wordbench records it exactly as external evidence.

It MUST NOT rewrite GF’s version into the framework version format.

### 60.1 Compatibility policy

GF Wordbench maintains:

```text
minimum supported GF version
tested GF versions
known incompatible GF versions
capability differences
```

The policy belongs to:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

### 60.2 Supporting a new GF version

Adding support is normally a framework minor change when it adds compatibility without breaking existing supported versions.

A compatibility-only fix may be a patch when the version was already declared supported.

### 60.3 Dropping GF support

After framework `1.0.0`, dropping a documented supported GF version is normally a framework major change.

An exception requires a clearly documented security or correctness emergency and migration guidance.

---

## 61. Python version

The supported Python range belongs to:

```text
pyproject.toml
installation documentation
compatibility tests
```

Adding support for a new Python version is normally minor or patch depending on whether capability was already expected.

Raising the minimum Python version after `1.0.0` is normally a framework major change when existing supported installations stop working.

---

## 62. RGL identity

The Resource Grammar Library may be identified by:

```text
release version
Git commit
distribution identifier
path fingerprint
```

The project or run evidence should record the strongest available identity.

An RGL version does not become the project release version.

---

## 63. Dependency versions

Runtime dependency ranges are explicit in `pyproject.toml`.

Changing dependencies is classified by user impact.

Examples:

- compatible bug-fix range correction: patch;
- new optional dependency for a new feature: minor;
- new required dependency that changes supported environments materially: minor or major;
- removal of support for installed environments: major after `1.0.0`.

---

# Part XIII — Artifact versioning

## 64. Framework distribution artifacts

Framework release artifacts use the framework version.

Examples:

```text
gf_wordbench-1.2.3-py3-none-any.whl
gf_wordbench-1.2.3.tar.gz
```

Exact normalized distribution filenames are produced by packaging tools.

The release process verifies embedded metadata.

---

## 65. PGF artifacts

A PGF artifact belongs to the active project release.

The canonical project contract controls its expected base filename.

Example:

```text
GrammarSqi.pgf
```

### 65.1 Stable filename

The PGF filename may remain stable across project releases.

Version identity may reside in:

```text
release tag
release directory
release manifest
artifact metadata
hash
```

A version suffix MUST NOT be inserted into the PGF filename unless the project artifact contract changes deliberately.

### 65.2 Artifact hash

SHA-256 identifies exact artifact bytes.

A hash is not a semantic version.

Two builds of the same project release should be traceable even if byte-identical reproducibility is not guaranteed.

---

## 66. Run artifacts

Run directories are identified by run ID, not framework version.

Example:

```text
run_20260722_153000
```

Run metadata records:

```text
producer.version
schema versions
GF version
project identity
normalization version
source fingerprints
```

A run ID is not a release version.

---

## 67. Manifest metadata

The manifest records artifact identity and hashes.

When a run is a release run, release metadata may be referenced through supported optional fields or an associated release record.

New manifest fields require schema-version review.

No release script may insert undocumented manifest fields.

---

## 68. Artifact replacement

A published artifact at one version is immutable.

If it is incorrect:

```text
publish a new version
```

Do not silently replace bytes under an existing public version or release tag.

---

# Part XIV — Change classification

## 69. Classification sequence

For every release candidate:

1. list changes since the previous release;
2. identify affected version domains;
3. identify providers and consumers;
4. classify each domain separately;
5. choose the highest bump in each domain;
6. identify migrations;
7. identify deprecations;
8. update authoritative version sources;
9. update tests;
10. update changelog and release evidence.

---

## 70. Framework classification questions

Ask:

```text
Does a supported user command stop working?
Does a supported configuration stop loading?
Does a supported schema stop reading?
Does public Python behavior change incompatibly?
Does required artifact meaning change?
Does a supported platform or tool version stop working?
Must automation change?
```

Any `yes` normally indicates a major framework impact after `1.0.0`.

---

## 71. Schema classification questions

Ask:

```text
Can an old reader safely interpret the new document?
Can a new reader interpret the old document?
Is any required field removed or renamed?
Does any field type or meaning change?
Does path ownership change?
Does ordering change?
Is migration required?
```

Use the answers to classify schema major or minor.

---

## 72. Normalization classification questions

Ask:

```text
Can canonical `.out` bytes change?
Can an existing `.gold` mismatch solely because of the rule change?
Does semantic preservation change?
Does marker parsing change?
Does token meaning change?
```

Any output-affecting change requires a normalization bump or a documented correction to existing semantics plus complete gold review.

---

## 73. Project classification questions

Ask:

```text
Do external consumers need to change?
Do public abstract signatures change?
Do entrypoint names change?
Do published constructor contracts change?
Does PGF API change?
Does expected linguistic behavior improve compatibly or break an accepted guarantee?
```

Project version classification follows the declared project contract.

---

## 74. Documentation-only classification

Ask:

```text
Did runtime behavior change?
Did persisted meaning change?
Did a contract promise change?
Did only explanation improve?
```

If only explanation improved:

```text
document patch or minor
no framework bump required until a release includes the docs
```

If documentation reveals that implementation and contract disagree, the mismatch must be resolved; it is not automatically “documentation only.”

---

# Part XV — Version-bump examples

## 75. Example matrix

| Change | Framework | Schema | Normalization | Contract | Project |
|---|---|---|---|---|---|
| Fix launcher quoting | Patch | None | None | Patch if contract text corrected | None |
| Add optional CLI command | Minor | None | None | Minor | None |
| Rename installed CLI command | Major | None | None | Major | None |
| Add optional summary field | Minor | run-summary minor | None | persisted lock minor | None |
| Rename required summary field | Major | run-summary major | None | persisted lock major | None |
| Correct writer to existing schema | Patch | None | None | Patch if needed | None |
| Add exact prompt normalization | Minor or patch by impact | scenario schema only if shape changes | Minor | external/normalization contract minor | Gold review |
| Change canonical marker syntax | Major | output/gold major | Normalization major | contract major | Project scenario migration |
| Add supported GF version | Minor | None | None | external contract minor | None |
| Drop supported GF version | Major | None | None | external contract major | Possible project impact |
| Add lexical entries | None | None | None | project contract minor if public | Project minor |
| Fix inflection | None | None | None | project contract patch if promise clarified | Project patch |
| Rename GF public function | None | None | Possibly gold changes | project contract major | Project major |
| Editorial typo | None | None | None | None | None |
| New normative guide section | None or package minor if shipped capability | None | None | None | None |

---

## 76. Multi-domain example: optional summary field

Change:

```text
add `normalization_version` to scenario result objects in summary.json
```

Required review:

```text
framework package: minor
run-summary schema: 1.0 → 1.1
persisted schema lock: minor
result model: update
writer: update
readers: update
migration/default: define
tests: update
documentation: update
```

The project schema does not change.

---

## 77. Multi-domain example: normalization correction

Change:

```text
path replacement failed on a documented Windows path form
```

When the existing normalization contract already required that form:

```text
framework package: patch
normalization version: unchanged
normalization document: patch
gold files: review affected output
tests: regression
```

When support for the path form is newly added to canonical semantics:

```text
framework package: minor
normalization: minor
normalization document: minor
gold files: review/migrate
tests: update
```

---

## 78. Multi-domain example: project entrypoint rename

Change:

```text
GrammarOld.gf → GrammarNew.gf
```

Possible impact:

```text
project release: major
project contract lock: major
project.toml: update
scenarios: update
PGF build: update
gold evidence: review
project docs: update
release artifacts: update
framework package: unchanged
```

The framework package does not bump solely because one active project changes.

---

# Part XVI — Deprecation

## 79. Deprecation requirement

A deprecation identifies:

```text
deprecated element
first deprecated release
replacement
migration steps
planned removal release or condition
affected consumers
tests during transition
```

A warning without replacement guidance is incomplete.

---

## 80. Post-1.0 deprecation window

For framework public surfaces after `1.0.0`, removal SHOULD occur no earlier than:

```text
the next major release
```

The deprecated element remains functional throughout the supported transition period unless security or correctness makes that unsafe.

---

## 81. Schema deprecation

Persisted fields are not removed through ordinary deprecation warnings.

Removal requires:

```text
schema major version
migration
reader compatibility policy
writer update
tests
```

A field may be marked deprecated in one schema major while remaining readable.

---

## 82. Contract deprecation

A deprecated contract entry remains listed with:

```text
status
replacement
consumers
removal condition
validation
```

Contract IDs are never reused.

---

## 83. Legacy `gf-audit`

Legacy names and formats follow explicit migration policy.

Examples:

```text
gf-audit package/command names
.gf_audit_state.json
unversioned summary formats
mode=file
mode=all
sha1_short
```

Canonical writers do not re-emit legacy aliases.

Removal of legacy readers follows the declared deprecation and migration policy.

---

# Part XVII — Changelog policy

## 84. Root changelog

Canonical path:

```text
CHANGELOG.md
```

It records framework package releases.

Each release entry includes applicable categories such as:

```text
Added
Changed
Fixed
Deprecated
Removed
Security
Schemas
Normalization
Compatibility
Migration
```

---

## 85. Unreleased section

The changelog SHOULD contain:

```text
Unreleased
```

Changes are accumulated there before release.

At release:

1. classify version impact;
2. assign version;
3. move relevant entries under the release heading;
4. include release date;
5. start a new Unreleased section.

---

## 86. Required breaking-change information

A breaking entry must identify:

```text
old behavior
new behavior
affected users or consumers
migration
removed version or schema
replacement
```

“Breaking changes” without migration detail is insufficient.

---

## 87. Schema changelog information

For each schema change:

```text
schema ID
old version
new version
compatible or breaking
writer impact
reader impact
migration command or procedure
```

---

## 88. Normalization changelog information

For normalization changes:

```text
old version
new version
changed rule
expected gold impact
migration/update workflow
```

---

## 89. Project release notes

Project releases use a release record associated with:

```text
project release tag
source commit
release validation evidence
```

Project linguistic changes need not be duplicated in the framework root changelog unless framework behavior changed.

---

# Part XVIII — Release coordination

## 90. Version freeze

Before a final framework release, maintainers freeze:

```text
framework version
schema versions
normalization version
contract versions
supported tool matrix
release artifact set
```

Any subsequent change is reclassified.

A release candidate cannot become final merely by renaming the version when code or contracts changed after validation.

---

## 91. Release-candidate rebuild

When code changes after `rcN`:

```text
create rcN+1
```

Do not move the existing prerelease tag.

Example:

```text
v1.0.0rc1
v1.0.0rc2
v1.0.0
```

---

## 92. Final release verification

A framework final release verifies:

```text
app.__version__ matches tag
pyproject reads the same version
CLI reports the same version
GUI reports the same version
producer metadata uses the same version
schema registry is internally consistent
normalization headers use the declared version
contract metadata is current
changelog contains the release
migration docs exist
release tests pass
artifacts contain correct package metadata
```

---

## 93. Project release verification

A project release verifies:

```text
project tag matches chosen project release version
project ID matches project.toml
source commit is fixed
framework version recorded
GF version recorded
RGL identity recorded
project schema version recorded
normalization version recorded
release criteria pass
required scenarios pass
gold comparisons pass
PGF artifact exists when required
artifact hash recorded
accepted issues recorded
```

---

## 94. Version changes after release

Published versions and tags are immutable.

Correction workflow:

```text
identify defect
classify impact
prepare new version
add changelog entry
rebuild
revalidate
publish new artifacts
```

Do not edit old release artifacts in place.

---

# Part XIX — Compatibility ranges

## 95. Explicit compatibility

Compatibility is declared, never inferred from numeric similarity.

Examples:

```text
framework 1.4 supports project schema 1.0 and 1.1
framework 2.0 reads run-summary 1.x and writes 2.0
project release 2.1 validated with GF <recorded-version>
```

---

## 96. Major-version compatibility is not automatic

A reader supporting schema `1.2` does not automatically support schema `2.0`.

A project built with framework `1.x` is not automatically compatible with every framework `1.y`.

Actual compatibility depends on documented contracts and tests.

---

## 97. Minimum and tested versions

For external tools distinguish:

```text
minimum supported
tested
known incompatible
unknown newer
```

Do not collapse these into one value.

---

## 98. Unknown future versions

Default policies:

- unknown schema major: reject or require migration;
- unknown schema minor within supported major: read conservatively according to schema policy;
- unknown newer GF version: warn or reject in strict mode according to compatibility policy;
- unknown project contract version: require review;
- unknown normalization version: do not compare gold.

---

# Part XX — Automation

## 99. Version check command

GF Wordbench SHOULD provide:

```text
gf-wordbench version
```

or equivalent diagnostic output.

It may report:

```text
framework package version
source commit when available
project ID
project release version when explicitly known
project schema version
state schema version
summary schema version
manifest schema version
normalization version
GF version
Python version
```

Every line is labeled by domain.

---

## 100. Release validation command

Release automation SHOULD verify version consistency before building artifacts.

Conceptual checks:

```text
version syntax
tag agreement
clean source tree
changelog entry
schema registry
normalization headers
contract metadata
package metadata
project release metadata
```

Exact commands belong to `RELEASE_PROCESS.md`.

---

## 101. Generated reference policy

These references SHOULD be generated or checked from authoritative code:

```text
CLI command reference
schema index
status values
diagnostic kinds
package version display
```

Manual duplicated version strings are drift risks.

---

## 102. No automatic bump by ordinary runtime

Normal GF Wordbench execution MUST NOT:

```text
edit app.__version__
change schema versions
change normalization version
change contract versions
create Git tags
edit changelog release headings
```

Version changes are explicit development/release operations.

---

# Part XXI — Tests

## 103. Package-version tests

Recommended file:

```text
tests/contracts/test_versioning.py
```

Required checks:

```text
app.__version__ exists
version syntax is valid
pyproject version is dynamic from app/__init__.py
package name is gf-wordbench
CLI version equals app.__version__
GUI version source equals app.__version__
producer.version equals app.__version__
no second authoritative framework version constant
```

---

## 104. Tag tests

Release automation verifies:

```text
framework tag has v prefix
tag value matches app.__version__
project tag contains project ID
project tag version syntax is valid
tag points to intended commit
tag is not reused
```

Tag immutability may also be enforced by repository hosting policy.

---

## 105. Schema-version tests

Required checks:

```text
every canonical persisted artifact has schema ID
every canonical persisted artifact has schema version
version syntax is MAJOR.MINOR
schema IDs are unique
current writers use declared current version
supported readers match compatibility matrix
unknown major is rejected
known legacy formats use migration paths
producer.version is not used as schema_version
schema index matches authoritative constants
```

---

## 106. Normalization-version tests

Required checks:

```text
`.out` header uses current normalization version
`.gold` header uses current normalization version
version mismatch cannot pass
normalizer result records the version
one authoritative normalization constant exists
gold updater preserves target version
no report writer rewrites normalization version
```

---

## 107. Contract-version tests

Recommended checks:

```text
every lock file declares a contract version
version syntax is MAJOR.MINOR.PATCH
contract IDs are unique within their registry
retired IDs are not reused
template and active project locks remain structurally compatible
breaking contract fixtures identify required migration
```

---

## 108. Document-version tests

For normative documents with metadata:

```text
document ID present
status present
document version syntax valid
last reviewed present
target path correct where included
```

Documentation checks should avoid requiring manual versions for non-normative generated references.

---

## 109. Project-release tests

When a project release is prepared:

```text
project tag syntax valid
project ID matches configuration
release version syntax valid
release record complete
source commit fixed
framework version recorded
GF version recorded
normalization version recorded
release evidence passes
artifact hashes present
```

---

## 110. Integration tests

Release integration should build a distribution and verify:

```text
wheel metadata version
source-distribution metadata version
installed CLI --version
installed GUI metadata
producer metadata in a sample run
schema versions in generated artifacts
normalization version in scenario output
```

---

# Part XXII — Anti-drift

## 111. Drift indicators

Probable version drift exists when:

- `pyproject.toml` and `app.__version__` disagree;
- CLI and GUI show different framework versions;
- a launcher contains a hard-coded framework version;
- `producer.version` is used as `schema_version`;
- two writers emit different current versions for the same schema;
- one schema changes without a version bump;
- every schema is bumped because one changed;
- a patch package release removes public behavior;
- a minor package release introduces an undocumented breaking migration;
- normalization output changes without a normalization review;
- a gold file passes under a different normalization version;
- contract content changes incompatibly without contract major bump;
- a contract ID is reused;
- a document version is treated as package version;
- GF version is rewritten into a framework version field;
- project release version is inferred from folder name;
- project release version is inserted into project schema without review;
- a run ID is treated as release version;
- an artifact hash is treated as semantic version;
- a release tag is moved;
- published artifact bytes are replaced under the same version;
- changelog lacks migration details;
- current writers emit legacy unversioned formats;
- unknown major schema versions are silently accepted;
- framework and project release changes are conflated;
- one Git tag is presented ambiguously as both framework and project version;
- generated references contain manually stale version strings.

Detected drift blocks release.

---

## 112. Version change checklist

For every proposed versioned change:

```text
[ ] affected version domains listed
[ ] providers identified
[ ] consumers identified
[ ] compatibility classified
[ ] framework bump selected
[ ] project bump selected when applicable
[ ] schema bumps selected independently
[ ] normalization bump selected
[ ] contract bumps selected
[ ] document versions selected
[ ] external-tool compatibility reviewed
[ ] deprecations reviewed
[ ] migrations defined
[ ] changelog updated
[ ] authoritative version sources updated
[ ] duplicate version strings removed
[ ] tests updated
[ ] release tags planned
[ ] artifact naming reviewed
[ ] release evidence requirements reviewed
```

---

## 113. Framework release checklist

```text
[ ] app.__version__ is final
[ ] package version syntax valid
[ ] pyproject reads dynamic version
[ ] CLI reports version
[ ] GUI reports version
[ ] changelog release section complete
[ ] breaking changes identified
[ ] migrations documented
[ ] deprecations documented
[ ] schema registry current
[ ] normalization version current
[ ] contract versions current
[ ] supported GF matrix current
[ ] supported Python range current
[ ] release tests pass
[ ] distribution metadata verified
[ ] framework tag prepared
[ ] tag matches version
```

---

## 114. Project release checklist

```text
[ ] project ID stable
[ ] project release version selected
[ ] project tag name valid
[ ] public project contract reviewed
[ ] project version impact classified
[ ] framework version recorded
[ ] project schema version recorded
[ ] normalization version recorded
[ ] GF version recorded
[ ] RGL identity recorded
[ ] required checkpoints pass
[ ] required scenarios pass
[ ] gold files reviewed
[ ] PGF built when required
[ ] artifact hash recorded
[ ] known issues reviewed
[ ] release criteria satisfied
[ ] release record complete
```

---

## 115. Schema release checklist

```text
[ ] schema ID unchanged
[ ] old version identified
[ ] new version selected
[ ] compatible versus breaking classified
[ ] writer updated
[ ] all readers reviewed
[ ] unknown-field behavior reviewed
[ ] path semantics reviewed
[ ] enum semantics reviewed
[ ] deterministic ordering reviewed
[ ] migration implemented when required
[ ] source preservation tested
[ ] target validation tested
[ ] schema index updated
[ ] persisted schema lock updated
[ ] changelog updated
```

---

## 116. Normalization release checklist

```text
[ ] old normalization version identified
[ ] new version selected
[ ] changed transformation listed
[ ] semantic preservation reviewed
[ ] raw evidence remains unchanged
[ ] marker handling reviewed
[ ] path tokens reviewed
[ ] Unicode behavior reviewed
[ ] gold compatibility reviewed
[ ] affected gold files listed
[ ] migration/update process tested
[ ] output and gold headers updated
[ ] comparison version check updated
[ ] changelog updated
```

---

# Part XXIII — Final version registry rules

## 117. Framework package

```text
format: MAJOR.MINOR.PATCH
source: app/__init__.py
tag:    v<version>
```

---

## 118. Project release

```text
format: MAJOR.MINOR.PATCH
source: immutable project release tag and release record
tag:    project-<project-id>-v<version>
```

---

## 119. Persisted schema

```text
format: MAJOR.MINOR
source: schema contract and implementation
identity: <schema-id>/<schema-version>
```

---

## 120. Normalization

```text
format: MAJOR.MINOR
source: canonical normalization implementation and contract
identity: <profile>/<normalization-version>
```

---

## 121. Contract lock

```text
format: MAJOR.MINOR.PATCH
source: lock-file metadata
```

---

## 122. Normative document

```text
format: MAJOR.MINOR.PATCH
source: document metadata
```

Only when independent document versioning provides value.

---

## 123. External tool

```text
format: upstream-defined
source: tool version probe or immutable distribution identity
```

GF Wordbench records but does not redefine it.

---

## 124. Final enforcement rule

Versions are compatibility promises, not decoration.

Therefore:

> No version may be bumped mechanically, copied across domains, inferred from an unrelated artifact or left unchanged when its own compatibility contract changes. Every release must identify exactly what is versioned, what remains compatible, what requires migration and which immutable source proves the released state.
