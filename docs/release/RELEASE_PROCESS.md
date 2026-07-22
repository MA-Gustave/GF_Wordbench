# GF Wordbench — Release Process

**Document ID:** `GF-WB-RELEASE-PROCESS`  
**Status:** Normative release procedure  
**Applies to:** GF Wordbench framework releases, project-template releases, active-language project releases, prereleases, hotfixes, and security releases  
**Primary owners:** GF Wordbench maintainers and designated release manager  
**Process version:** `1.0`  
**Target product state:** Final architecture  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines the complete release process for GF Wordbench.

It specifies:

- which deliverables may be released;
- which roles participate;
- how a release is proposed and classified;
- how versions are selected;
- which contracts, schemas, migrations, tests, and artifacts must be reviewed;
- how release candidates are prepared;
- how packages and evidence are built;
- how releases are approved, tagged, published, and verified;
- how project-language releases differ from framework releases;
- how hotfixes and security releases are handled;
- how failed or defective releases are withdrawn without mutating published versions.

The process is designed to ensure that every release is reproducible, reviewable, migration-safe, and supported by durable evidence.

---

## 2. Core rule

> A release is complete only when its source, versions, contracts, schemas, tests, artifacts, migration notes, changelog, tag, and published outputs all describe the same product state.

Passing tests alone is insufficient.

Building a package alone is insufficient.

Creating a tag alone is insufficient.

A release exists only after publication and post-publication verification succeed.

---

## 3. Related authority

The following documents govern specific release boundaries:

```text
CHANGELOG.md
docs/release/VERSIONING_POLICY.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/development/TESTING_GF_WORDBENCH.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/ARTIFACT_MANIFEST.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
project/docs/RELEASE_CRITERIA.md
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/DECISION_LOG.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Priority when rules overlap:

1. versioning policy governs version meaning;
2. persisted-schema lock governs serialized compatibility;
3. contract locks govern provider-consumer and external-tool boundaries;
4. testing policy governs executable evidence;
5. this document governs release sequencing and approval;
6. project release criteria govern the active-language project.

---

## 4. Release deliverables

GF Wordbench recognizes three independently releasable deliverables.

```text
GF Wordbench framework
project template
active language project
```

A combined publication may release more than one deliverable, but each retains its own version, gates, and evidence.

---

## 5. Framework release

A framework release publishes the GF Wordbench software.

It may include:

- Python package;
- CLI;
- optional GUI;
- framework documentation;
- canonical schemas;
- project loader;
- process execution;
- validation stages;
- report writers;
- migration utilities;
- clean project template.

A framework release does not certify that the current active language project is linguistically release-ready.

---

## 6. Project-template release

A template release publishes the reusable structure under:

```text
templates/project/
```

It proves that a new project can be initialized from a clean language-neutral source.

A template release may be bundled with a framework release.

The template version remains independent.

---

## 7. Active-language project release

A project release publishes or certifies the current project under:

```text
project/
```

It may include:

- GF source modules;
- project configuration;
- project documentation;
- scenarios;
- inputs;
- gold files;
- final PGF;
- project release evidence.

A project release records the exact GF Wordbench and GF versions used.

It does not change the GF Wordbench framework version automatically.

---

## 8. Release types

Canonical release types:

```text
stable
release candidate
beta
alpha
hotfix
security
project-only
template-only
```

A release type influences gates and communication, but it does not override versioning policy.

---

## 9. Stable release

A stable release is intended for supported use.

It requires:

- final version;
- complete changelog;
- complete migration notes;
- all mandatory release gates;
- no unresolved release blocker;
- immutable publication;
- post-publication verification.

---

## 10. Release candidate

A release candidate is intended to become the stable release unless a blocker is found.

It should use:

- final intended schemas;
- final intended migration behavior;
- final intended report identities;
- final intended compatibility matrix;
- final intended package structure.

A release candidate must not be used to hide an unfinished required feature.

---

## 11. Alpha and beta

Alpha may contain incomplete functionality.

Beta should be feature-complete but may still require compatibility validation.

Alpha and beta releases must:

- identify their instability;
- avoid claiming stable compatibility;
- use versioned persisted formats;
- preserve migration evidence;
- avoid silently overwriting stable installations or data.

---

## 12. Hotfix

A hotfix addresses an urgent compatible defect in a published release.

Typical examples:

- process cleanup failure;
- false diagnostic classification;
- report-generation defect;
- supported-platform regression;
- package metadata error;
- migration correction preserving intended semantics.

A hotfix normally increments the patch version.

---

## 13. Security release

A security release addresses a vulnerability involving:

- process execution;
- shell injection;
- path traversal;
- symlink or junction escape;
- secret disclosure;
- unsafe scenario execution;
- unsafe gold update;
- artifact overwrite;
- untrusted file handling.

Compatibility may be broken when required for safety.

Security takes priority over preserving an unsafe interface.

---

# 14. Release roles

A small team may combine roles, but the responsibilities remain distinct.

Canonical roles:

```text
release manager
implementation owner
test owner
schema/contract reviewer
project maintainer
security reviewer
approver
```

---

## 15. Release manager

The release manager owns:

- release plan;
- version proposal;
- release checklist;
- branch or commit selection;
- gate coordination;
- artifact build;
- tag creation;
- publication;
- post-publication verification;
- release evidence archive.

The release manager must not override failed gates without a documented exception approved under this process.

---

## 16. Implementation owner

The implementation owner confirms:

- completed scope;
- relevant tests;
- unresolved limitations;
- affected contracts;
- affected schemas;
- migration impact;
- documentation updates.

---

## 17. Test owner

The test owner verifies:

- required suites ran;
- expected platforms were covered;
- required GF tests did not skip;
- coverage thresholds passed;
- flaky or quarantined tests are documented;
- failure evidence is retained.

---

## 18. Schema and contract reviewer

The reviewer confirms:

- version increments are correct;
- providers and consumers are aligned;
- migrations exist where required;
- canonical writers emit only current formats;
- old supported inputs remain readable;
- locks and fixtures agree.

---

## 19. Project maintainer

For an active-language release, the project maintainer confirms:

- linguistic scope;
- project version;
- scenarios;
- gold expectations;
- known issues;
- release criteria;
- PGF entrypoints;
- project documentation.

---

## 20. Security reviewer

The security reviewer is required when the release changes:

- process execution;
- environment inheritance;
- path containment;
- scenario trust policy;
- secret redaction;
- external-tool integration;
- migration of untrusted files;
- update or overwrite behavior.

---

## 21. Approver

The approver confirms that:

- no required gate is missing;
- exceptions are documented;
- evidence matches the proposed version;
- release notes are accurate;
- publication may proceed.

For a one-person project, the release manager may also approve, but the checklist must still record the self-review.

---

# 22. Release states

Canonical internal release states:

```text
proposed
planned
in preparation
candidate
approved
published
verified
withdrawn
superseded
aborted
```

These states are release-process metadata.

They are not validation statuses.

---

## 23. Proposed

Scope and target version are not yet final.

No publication claim exists.

---

## 24. Planned

The intended scope, compatibility impact, and target release type are documented.

---

## 25. In preparation

Implementation is frozen or stabilizing.

Required gates are being executed.

---

## 26. Candidate

A release-candidate artifact and tag exist for review.

The release is not stable.

---

## 27. Approved

All required evidence is complete and publication is authorized.

---

## 28. Published

Artifacts and release metadata are publicly or internally distributed at the designated destination.

---

## 29. Verified

Published artifacts were independently fetched or installed and verified.

This is the normal terminal state for a successful release.

---

## 30. Withdrawn

The release remains historically identifiable but should no longer be installed or used.

Published version content must not be changed.

---

## 31. Superseded

A newer release replaces the release operationally.

The old release remains immutable.

---

## 32. Aborted

Preparation ended before publication.

An aborted version may be reused only when no immutable tag or public artifact was published and policy explicitly permits it.

A published or tagged candidate identifier is not reused.

---

# 33. Release evidence directory

A release preparation should create a dedicated evidence directory outside the active source tree or under an approved release-output root.

Recommended shape:

```text
release_<version>/
├── release-plan.md
├── release-checklist.md
├── version-audit.txt
├── test-results/
├── coverage/
├── package/
├── checksums/
├── compatibility/
├── migrations/
├── documentation/
├── project-evidence/
└── publication-verification/
```

The evidence directory is not the application package.

It supports review and audit.

---

## 34. Evidence retention

Retain, when applicable:

```text
commit ID
source archive hash
version audit
test commands
test results
coverage report
GF version output
platform details
schema validation output
migration results
package artifacts
package hashes
release-mode run summary
release-mode manifest
PGF hash
publication verification
approval record
```

Secrets and complete environment dumps are prohibited.

---

# 35. Release initiation

A release begins with a release plan.

Minimum release plan:

```text
deliverable
release type
proposed version
scope
breaking changes
schema changes
contract changes
normalization changes
GF compatibility changes
platform changes
migration requirements
deprecations
known blockers
target publication channel
owners
```

---

## 36. Scope freeze

Before release-candidate preparation, freeze the intended scope.

After freeze, allowed changes are limited to:

- release blocker fixes;
- documentation corrections;
- packaging fixes;
- migration corrections;
- security fixes;
- test corrections that reveal or prove release behavior.

New unrelated features require a later release.

---

## 37. Release branch

A release branch may be used:

```text
release/<version>
```

It is optional.

When used:

- branch from a passing reviewed commit;
- accept only stabilization changes;
- merge or forward-port every correction;
- avoid maintaining divergent implementations;
- tag the exact approved commit.

The release branch does not define the version by itself.

---

## 38. Clean source requirement

Release preparation requires:

- expected branch or commit;
- no uncommitted production changes;
- no modified fixtures;
- no generated run artifacts tracked accidentally;
- no temporary migration files;
- no local secrets;
- no stale package artifacts in the build directory.

A dirty source tree may be used only for diagnostic builds, never for a stable release.

---

# 39. Release classification

Classify the release according to `VERSIONING_POLICY.md`.

Review:

```text
application compatibility
schema compatibility
contract compatibility
CLI compatibility
Python API compatibility
platform support
GF support
project-template compatibility
active-project compatibility
```

The highest required application-version impact wins.

---

## 40. Version reservation

Select the proposed version only after compatibility classification.

Verify:

- version is valid;
- tag does not already exist;
- package destination does not already contain different artifacts under that version;
- changelog has no conflicting published section;
- release candidate identifiers are monotonic.

---

## 41. Version source update

Update the canonical application version once.

Derived versions must read from it.

Verify:

```text
package metadata
CLI
GUI
report producer metadata
release tag
```

all agree.

---

## 42. Changelog preparation

Move included entries from:

```text
## [Unreleased]
```

into:

```text
## [MAJOR.MINOR.PATCH] - YYYY-MM-DD
```

Use the actual publication date only at final publication.

Before that point, a candidate may use an explicitly marked candidate date or retain release notes separately.

The changelog must include:

- user-visible additions;
- behavior changes;
- deprecations;
- removals;
- fixes;
- security changes;
- migrations.

---

## 43. Release notes

Release notes summarize the release for its audience.

They should include:

```text
release purpose
key changes
compatibility
installation or upgrade impact
migration actions
known issues
supported GF versions
supported Python versions
supported platforms
verification summary
```

Release notes do not replace the changelog or migration documentation.

---

# 44. Schema audit

For every canonical schema, record:

```text
current schema version
version emitted by this release
older supported versions
migration availability
breaking or compatible classification
fixtures
round-trip status
```

Schemas include:

```text
gf-wordbench.project
gf-wordbench.app-state
gf-wordbench.run-summary
gf-wordbench.artifact-manifest
gf-wordbench.scenario-output
gf-wordbench.scenario-gold
```

---

## 45. Schema release requirements

A release changing a schema requires:

- updated schema lock;
- canonical writer;
- canonical reader;
- migration when required;
- canonical minimal fixture;
- canonical complete fixture;
- invalid fixtures;
- legacy fixtures;
- round-trip tests;
- deterministic serialization tests;
- path-base tests;
- changelog entry.

---

## 46. Unknown-major behavior

Before release, verify that unknown newer major schema versions are rejected explicitly.

A release must not claim compatibility by silently accepting unknown meaning.

---

# 47. Contract audit

Review:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

For each changed contract:

- version increment matches impact;
- status is final;
- provider exists;
- consumers exist;
- public symbols exist;
- artifact ownership is correct;
- tests exist;
- migration exists when required;
- forbidden behavior remains absent.

---

## 48. Contract status requirement

Required release behavior must use:

```text
Active
```

Experimental behavior may ship when:

- explicitly labeled;
- nonessential to stable release;
- disabled by default or clearly isolated;
- no canonical persisted ambiguity is introduced.

A stable release must not rely on a merely planned contract.

---

## 49. External-tool audit

Verify:

- GF executable resolution;
- version probe;
- supported GF range;
- exact command construction;
- working directories;
- environment policy;
- finite timeouts;
- separate stdout and stderr;
- required artifacts;
- scenario stdin;
- no implicit shell;
- version-sensitive diagnostics;
- optional-tool contracts.

---

# 50. Normalization and gold audit

When normalization or scenario behavior changed:

1. preserve before/after raw evidence;
2. verify normalization version;
3. run normalization fixtures;
4. inspect every changed `.out`;
5. inspect every changed `.gold`;
6. confirm no meaningful linguistic output was removed;
7. confirm headers agree;
8. document regeneration or migration;
9. record project impact;
10. run required scenario release tests.

Widespread unexplained gold change is a release blocker.

---

# 51. Migration audit

Every migration included in the release must be tested against:

```text
valid legacy input
minimal legacy input
complete legacy input
ambiguous input
invalid input
already canonical input
target collision
write failure
repeat execution
```

Verify:

- source is preserved until success;
- losses are reported;
- warnings are actionable;
- target validates;
- canonical writer emits no legacy aliases.

---

# 52. Deprecation audit

For every deprecation, verify:

```text
deprecated item
replacement
first deprecated version
warning
migration path
earliest removal version
tests
documentation
```

For every removal, verify that its required deprecation window or emergency exception is documented.

---

# 53. Compatibility matrix

Before candidate approval, finalize the supported matrix.

Minimum dimensions:

```text
GF Wordbench version
Python versions
GF versions
project schema versions
summary schema versions
platforms
GUI availability
```

Use precise labels:

```text
supported
tested
experimental
deprecated
unsupported
incompatible
unknown
```

---

# 54. Documentation audit

Verify that:

- root README reflects current product identity;
- installation instructions match package contents;
- CLI reference matches implemented commands;
- GUI reference matches implemented behavior;
- project template paths exist;
- release notes match changelog;
- migration steps are complete;
- no canonical document presents deprecated names as current;
- no generated path is documented under the wrong base;
- all linked normative documents exist;
- documentation uses the selected version consistently.

---

# 55. Project-template audit

When the framework release includes the template, verify:

- template structure matches the documented project model;
- placeholders remain generic;
- no active-language name appears;
- no machine-local path appears;
- no state file appears;
- no run artifact appears;
- required documentation exists;
- project configuration validates after required placeholder replacement;
- template contract lock matches the framework project loader;
- template version is updated correctly.

---

# 56. Active-project isolation

A framework release test must not depend on the linguistic correctness of the active `project/`.

Use a dedicated framework fixture project for release integration.

The active project may be tested separately as a project release.

This prevents one incomplete language project from blocking a valid framework release and prevents one successful language project from masking framework defects.

---

# 57. Freeze checks

At release-candidate freeze, confirm:

```text
[ ] no unrelated feature remains open
[ ] no unresolved schema decision remains
[ ] no unresolved contract decision remains
[ ] compatibility matrix is final
[ ] migration scope is final
[ ] normalization version is final
[ ] required gold changes are reviewed
[ ] package structure is final
[ ] release notes are drafted
[ ] blockers are enumerated
```

---

# 58. Static release gates

Run:

```text
python -m ruff format --check .
python -m ruff check .
python -m mypy app
```

Also run:

- documentation consistency checks;
- dependency-direction tests;
- version-consistency tests;
- artifact-ownership tests;
- contract metadata validation.

No required warning is ignored without a documented exception.

---

# 59. Default test gate

Run the complete suite that does not require a real GF installation.

Recommended:

```text
python -m pytest -m "not gf"
```

This includes:

- unit;
- component;
- contracts;
- schemas;
- migrations;
- fake process;
- fake-GF integration;
- supported GUI-independent behavior;
- security tests not requiring GF.

---

# 60. Contract gate

Run:

```text
python -m pytest -m contract
```

Verify:

- public boundaries;
- result fields;
- status meanings;
- artifact ownership;
- no prohibited imports;
- CLI/GUI configuration equivalence;
- no report-time execution;
- no gold modification.

---

# 61. Schema and migration gate

Run:

```text
python -m pytest -m "schema or migration"
```

Verify every supported persisted family and migration path.

---

# 62. Security gate

Run security-marked tests.

Verify at minimum:

- no shell injection;
- argument boundaries;
- path traversal rejection;
- symlink/junction containment;
- secret redaction;
- output limit;
- scenario OS-escape policy;
- gold write separation;
- safe artifact destination;
- no environment dump.

---

# 63. Windows gate

Required Windows evidence includes:

- paths containing spaces;
- Unicode paths;
- native `gf.exe` or fake executable;
- CRLF inputs;
- timeout;
- cancellation;
- child-process termination;
- drive handling;
- junction containment;
- atomic writes;
- CLI launcher;
- GUI launcher when shipped.

---

# 64. POSIX gate

Required POSIX evidence includes:

- executable permission;
- Unicode paths;
- path separator behavior;
- process group termination;
- symlink containment;
- atomic writes;
- CLI package execution.

---

# 65. Real-GF gate

Run:

```text
python -m pytest -m gf
```

The release environment must provide explicit tested GF configuration.

The job fails if required GF tests skip unexpectedly.

Required real-GF evidence:

- version probe;
- successful compile;
- failed compile;
- explicit GF path;
- PGF build;
- `.gfs` load;
- parse;
- linearize;
- bounded generation;
- markers;
- Unicode;
- required artifact verification.

---

# 66. End-to-end gate

Run fake-GF and real-GF end-to-end workflows.

Fake-GF E2E proves framework control.

Real-GF E2E proves the external contract.

Required final real-GF flow:

```text
temporary canonical project
    → resolved configuration
    → GF version probe
    → source validation
    → PGF build
    → required scenario
    → normalization
    → gold comparison
    → reports
    → manifest verification
```

---

# 67. Coverage gate

Recommended release thresholds:

```text
overall line coverage: at least 85%
changed production lines: at least 90%
critical-module branch coverage target: at least 90%
```

Critical modules:

```text
process execution
path containment
schema migration
release gates
gold update
manifest
```

A threshold change requires an explicit policy update.

It must not be lowered solely to release the current change set.

---

# 68. Skip and xfail gate

Release requirements:

- no unexpected skip in required test categories;
- no strict xpass;
- every expected failure has a current issue and removal condition;
- quarantined tests are enumerated and approved;
- no retry-only success is accepted as stable evidence.

---

# 69. Repository cleanliness gate

After all tests:

- tracked fixtures remain unchanged;
- project golds remain unchanged unless the release intentionally updates them;
- no child process remains;
- no untracked secret appears;
- no generated package or run artifact is accidentally staged;
- source tree remains reproducible.

---

# 70. Package build

Build from the exact candidate commit in a clean environment.

Recommended outputs:

```text
wheel
source distribution when supported
source archive
```

Build tools and commands must be recorded.

The build directory must not contain stale artifacts from another version.

---

## 71. Clean build environment

The build environment should provide:

```text
supported Python
declared build dependencies
no editable installation
no uncommitted source changes
no inherited project state
no hidden GF path dependency
no network use except dependency retrieval when explicitly permitted
```

A reproducible internal build may use a prepopulated dependency cache.

---

## 72. Package-content audit

Inspect the built package.

Verify inclusion of:

- production Python modules;
- required metadata;
- license;
- required package resources;
- template assets when shipped.

Verify exclusion of:

- tests unless intentionally shipped;
- local state;
- active project source unless intentionally packaged;
- generated run artifacts;
- release evidence directory;
- secrets;
- caches;
- temporary files;
- developer-only snapshots.

---

## 73. Install smoke test

Install the built artifact into a clean environment.

Verify:

```text
import app
CLI --help
CLI --version
configuration inspection without GF
package metadata
optional GUI import or launch when shipped
```

The installed package must not depend on repository-relative imports.

---

## 74. Version verification

From the installed package, verify:

```text
installed distribution version
app.__version__
CLI version
GUI version
report producer version
```

all equal the candidate application version.

---

## 75. Source archive verification

A source archive should:

- correspond to the candidate commit;
- contain required build files;
- omit local state and generated artifacts;
- reproduce the package build;
- have a recorded SHA-256.

---

# 76. Release-candidate artifact set

Recommended framework candidate artifacts:

```text
wheel
source distribution or source archive
checksums file
release notes
CHANGELOG excerpt
migration guide
compatibility matrix
test summary
coverage summary
version audit
```

Internal releases may omit distribution formats not used by the installation method, but the omission must be deliberate.

---

## 77. Checksums

Use SHA-256 for release-artifact integrity.

Canonical checksum line:

```text
<sha256><two spaces><filename>
```

The checksum file itself may be signed when a signing process exists.

Do not claim signature verification unless signing and verification are actually implemented.

---

## 78. Signing

Artifact signing is recommended for public distribution but is not mandatory until a signing policy and trusted key management are implemented.

When signing is enabled, document:

- signing identity;
- key custody;
- signature format;
- verification command;
- rotation;
- revocation;
- CI access policy.

Unsigned artifacts must not be described as signed.

---

# 79. Candidate tag

Create an immutable candidate tag only after candidate artifacts pass internal verification.

Example:

```text
v1.2.0-rc.1
```

The tag must identify the exact source used to build the candidate.

Do not rebuild the same candidate tag with different content.

---

## 80. Candidate publication

Publish the candidate to a prerelease or staging channel.

Candidate communication must state:

- prerelease status;
- target stable version;
- tested compatibility;
- known issues;
- migration requirements;
- feedback channel;
- installation separation from stable release.

---

## 81. Candidate validation period

During candidate validation:

- run representative upgrade tests;
- run representative clean-install tests;
- validate package on required platforms;
- validate real-GF integration;
- inspect reports and manifests;
- review migration logs;
- collect blockers.

No unrelated feature is added.

---

## 82. Candidate blocker

A candidate blocker includes:

- data loss;
- unsafe execution;
- incorrect validation evidence;
- failing required platform;
- failing supported GF integration;
- invalid package;
- invalid schema or migration;
- missing required report or manifest;
- incorrect version;
- release-note contradiction;
- reproducible severe regression.

A blocker requires a new candidate after correction.

---

## 83. Candidate correction

For every candidate correction:

1. add or update a regression test;
2. update source;
3. update changelog or candidate notes;
4. rerun affected gates;
5. rerun all mandatory release gates;
6. increment candidate number;
7. build new artifacts;
8. create new immutable candidate tag.

---

# 84. Stable approval

Stable approval requires a completed release checklist.

Minimum approval evidence:

```text
version audit
all required gates
package install smoke
real-GF E2E
schema and migration audit
contract audit
security audit where applicable
compatibility matrix
release notes
checksums
candidate feedback resolution
```

---

## 85. Approval exceptions

A required gate may be waived only when:

- the gate is impossible for a documented external reason;
- equivalent evidence exists;
- risk is understood;
- approver accepts the risk;
- release notes identify the limitation;
- a follow-up issue exists.

The following normally cannot be waived for a stable release:

- version consistency;
- package installability;
- required schema validity;
- required migration safety;
- process security invariants;
- release manifest integrity;
- source preservation;
- no known data-loss defect.

---

# 86. Stable release preparation

Before stable tagging:

1. update final publication date;
2. finalize changelog section;
3. finalize release notes;
4. confirm version source;
5. confirm no code changed after final gate;
6. rebuild from the exact approved commit if candidate artifacts are not promoted directly;
7. verify hashes;
8. verify package contents;
9. record approval.

---

## 87. Stable tag

Canonical tag:

```text
v<MAJOR>.<MINOR>.<PATCH>
```

Example:

```text
v1.2.0
```

The tag is immutable.

It must correspond exactly to the published source.

---

## 88. Stable artifact build

Stable artifacts must be built from the stable tag or its exact commit.

Do not publish artifacts built from a different working tree.

Record:

```text
tag
commit
build environment
build command
artifact hash
```

---

# 89. Publication

Publication destinations depend on the project’s distribution model.

Possible destinations:

```text
package registry
source hosting release page
internal artifact repository
signed archive location
project release directory
```

The release plan must name the actual destinations.

The process must not claim publication to a destination that was not verified.

---

## 90. Publication order

Recommended order:

1. publish source tag;
2. publish package artifacts;
3. publish checksums or signatures;
4. publish release notes;
5. publish migration guide;
6. publish compatibility matrix;
7. mark release stable;
8. begin post-publication verification.

If package publication fails, do not claim the release complete.

---

## 91. Atomic publication

When the destination supports staging:

- upload artifacts privately or as draft;
- verify names and hashes;
- publish or promote atomically.

When atomic publication is unavailable:

- upload in documented order;
- withhold stable announcement until all required artifacts verify;
- withdraw partial artifacts if consistency cannot be restored.

---

# 92. Post-publication verification

Use a fresh environment separate from the build environment.

Verify:

```text
release tag resolves
published artifact downloads
SHA-256 matches
package installs
CLI version matches
CLI help works
configuration command works
real-GF smoke works when required
migration example works
release notes display
links resolve
```

---

## 93. Published-package smoke

At minimum:

```text
install published package
run --version
run --help
load canonical project config
create a temporary run
produce canonical reports with fake or real GF as appropriate
```

A public release is not verified merely because upload succeeded.

---

## 94. Publication mismatch

If a downloaded artifact hash differs:

- stop release announcement;
- mark the release incomplete or withdrawn;
- do not overwrite the artifact under the same version silently;
- investigate publication or build contamination;
- publish a corrected new version when required.

---

## 95. Post-release announcement

Announce only after verification.

Include:

- version;
- release type;
- key changes;
- supported environments;
- migration requirements;
- known issues;
- release notes location;
- security guidance when applicable.

Do not claim unsupported compatibility.

---

# 96. Post-release repository updates

After successful publication:

- reopen `Unreleased`;
- merge release changes to the main development branch;
- forward-port hotfixes;
- update development version when policy uses one;
- record release evidence;
- close release blockers;
- create follow-up issues;
- mark the release `verified`.

---

## 97. Release evidence archive

Archive:

```text
release plan
approved checklist
tag and commit
artifacts
hashes
test results
coverage
GF version evidence
compatibility matrix
migration evidence
publication verification
approvals
```

The archive should be read-only after finalization.

---

# 98. Framework release checklist

```text
[ ] release scope frozen
[ ] release type classified
[ ] application version selected
[ ] version source updated
[ ] package metadata agrees
[ ] CHANGELOG finalized
[ ] release notes finalized
[ ] compatibility matrix finalized
[ ] schema audit complete
[ ] contract audit complete
[ ] external-tool audit complete
[ ] normalization/gold audit complete
[ ] migration audit complete
[ ] deprecation audit complete
[ ] documentation audit complete
[ ] template audit complete when shipped
[ ] static gates pass
[ ] default suite passes
[ ] contract suite passes
[ ] schema suite passes
[ ] migration suite passes
[ ] security suite passes
[ ] Windows suite passes
[ ] POSIX suite passes
[ ] real-GF suite passes
[ ] fake-GF E2E passes
[ ] real-GF E2E passes
[ ] coverage gate passes
[ ] no unexpected required skips
[ ] no strict xpass
[ ] repository remains clean
[ ] package builds
[ ] package-content audit passes
[ ] clean install smoke passes
[ ] version audit passes
[ ] checksums generated
[ ] candidate validated when required
[ ] approval recorded
[ ] tag created
[ ] artifacts published
[ ] published hashes verified
[ ] post-publication smoke passes
[ ] release evidence archived
```

---

# 99. Template release process

A template-only release follows:

1. classify template-version change;
2. update template version;
3. validate template contract;
4. validate placeholder policy;
5. initialize a temporary project from the template;
6. fill required test placeholders;
7. load `project.toml`;
8. run fake-GF validation;
9. run real-GF fixture validation when relevant;
10. verify no active-language data;
11. verify no local paths or run artifacts;
12. package or publish template;
13. verify downloaded template;
14. record compatibility with GF Wordbench versions.

---

## 100. Template release checklist

```text
[ ] template version classified
[ ] required files exist
[ ] generic placeholders only
[ ] no active-language names
[ ] no machine-local absolute paths
[ ] no state file
[ ] no generated artifacts
[ ] project configuration validates after initialization
[ ] template contract lock matches framework loader
[ ] initialized project passes smoke validation
[ ] documentation links resolve
[ ] archive contents verified
[ ] compatibility range recorded
```

---

# 101. Active-language project release process

A project release is driven by:

```text
project/docs/RELEASE_CRITERIA.md
```

Framework release gates do not replace project linguistic gates.

Project release sequence:

1. freeze project scope;
2. classify project version;
3. update project version;
4. verify project configuration;
5. verify project contract lock;
6. review status ledger and known issues;
7. run release validation;
8. build required PGF;
9. run required scenarios;
10. compare required gold;
11. verify release gates;
12. generate reports;
13. verify manifest;
14. review linguistic changes;
15. create project release notes;
16. tag or archive project revision;
17. publish project artifacts;
18. verify published PGF and evidence.

---

## 102. Project release prerequisites

Required:

- one active project identity;
- canonical `project.toml`;
- no unresolved required placeholder;
- declared entrypoints;
- declared checkpoints;
- required scenarios;
- valid gold files;
- documented release criteria;
- no unresolved blocking known issue;
- supported GF Wordbench version;
- supported or approved GF version;
- clean source revision.

---

## 103. Project release mode

Run GF Wordbench in:

```text
release
```

The release run must not silently disable:

- required source validation;
- required entrypoints;
- PGF build;
- required scenarios;
- gold comparison;
- required artifacts;
- manifest integrity.

---

## 104. Project release evidence

Required project evidence normally includes:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master.log
required raw compiler evidence
required raw scenario evidence
normalized scenario outputs
gold diffs when failures occur
final PGF
project version
source revision
GF Wordbench version
GF version
```

A successful project release must not contain a required failure diff.

---

## 105. Project PGF verification

Verify:

- expected PGF exists;
- file is non-empty;
- path is owned;
- source entrypoints are correct;
- GF version is recorded;
- SHA-256 is recorded;
- manifest entry exists;
- prior release artifact was not overwritten silently;
- published PGF hash matches release evidence.

---

## 106. Project scenario verification

Every required release scenario must:

- exist;
- execute;
- complete required sections;
- pass assertions;
- use the declared normalization version;
- match required gold;
- produce required artifacts;
- have status `OK`.

`SKIPPED` is not success for a required release scenario.

---

## 107. Project known issues

A known issue may remain only when:

- explicitly nonblocking under project release criteria;
- documented;
- scoped;
- supported by evidence;
- not a security, data-loss, or invalid-release-evidence issue.

The release notes must identify relevant nonblocking limitations.

---

## 108. Project release tag

A project may use a project-specific tag.

Recommended:

```text
project/<project-id>/v<version>
```

or a repository-appropriate equivalent.

The tag must not be confused with the GF Wordbench framework tag.

---

## 109. Project artifact publication

Possible project deliverables:

```text
PGF
source archive
project documentation
scenario/gold archive
manifest
release summary
checksums
```

The release criteria determine which are required.

---

## 110. Project release checklist

```text
[ ] project scope frozen
[ ] project version classified
[ ] project version updated
[ ] project configuration validates
[ ] project contract lock current
[ ] status ledger current
[ ] known issues reviewed
[ ] release criteria current
[ ] source validation passes
[ ] entrypoint validation passes
[ ] PGF build passes
[ ] required scenarios pass
[ ] required gold matches
[ ] normalization versions agree
[ ] required artifacts exist
[ ] release manifest verifies
[ ] project release notes complete
[ ] GF Wordbench version recorded
[ ] GF version recorded
[ ] source revision recorded
[ ] PGF hash recorded
[ ] project tag/archive created
[ ] published artifacts verified
```

---

# 111. Combined framework and project release

A combined release must execute both checklists independently.

It must not infer:

```text
framework passed → project passed
project passed → framework passed
```

The release record should identify:

```text
framework version
template version
project version
GF version
```

---

# 112. Hotfix process

Hotfix sequence:

1. identify affected release;
2. reproduce defect;
3. assess security, data, schema, and compatibility impact;
4. create regression test;
5. implement minimal correction;
6. classify patch/minor/major;
7. update changelog;
8. run focused gates;
9. run all mandatory release gates;
10. build clean artifacts;
11. publish new immutable version;
12. verify upgrade from affected release;
13. communicate mitigation.

A hotfix must not skip required schema or migration review.

---

## 113. Hotfix branch

Optional:

```text
hotfix/<version>
```

The correction must be forward-ported to active development.

Avoid maintaining a permanent divergent hotfix implementation.

---

# 114. Security release process

Security release sequence:

1. limit disclosure to necessary participants;
2. preserve evidence securely;
3. identify affected versions;
4. implement safe fix;
5. add security regression tests;
6. assess compatibility impact;
7. prepare migration or mitigation;
8. execute required gates;
9. build and verify artifacts;
10. publish new version;
11. publish advisory when safe;
12. provide upgrade instructions;
13. revoke or withdraw unsafe artifacts where operationally possible.

---

## 115. Security release minimum gates

The following cannot be omitted:

- focused exploit regression;
- process/path/security contract tests;
- package integrity;
- migration safety when data changes;
- version consistency;
- clean install;
- post-publication verification.

Time pressure does not justify publishing unverified artifacts.

---

# 116. Failed release preparation

Abort preparation when:

- scope cannot stabilize;
- required gates fail;
- migration is unsafe;
- package cannot install;
- release evidence is inconsistent;
- required platform is unavailable without approved equivalent evidence;
- version classification is unresolved;
- security review blocks publication.

An aborted preparation is not a release.

---

## 117. Candidate withdrawal

Withdraw a candidate when a blocker is found.

Do not delete its historical identity when it was distributed.

Publish the next candidate under a new identifier.

---

## 118. Stable release defect

When a stable release is defective:

1. assess severity;
2. stop further promotion;
3. mark affected release;
4. preserve published artifacts;
5. publish mitigation;
6. prepare a corrected new version;
7. test upgrade and rollback guidance;
8. verify corrected publication.

Do not silently replace the original artifacts.

---

## 119. Release withdrawal

Withdrawal may be required for:

- security vulnerability;
- data loss;
- incorrect migration;
- invalid package;
- corrupted artifacts;
- false release evidence;
- licensing issue.

Withdrawal record should include:

```text
version
reason
date
affected artifacts
recommended replacement
mitigation
```

---

## 120. Rollback guidance

Rollback is operational, not a mutation of the release.

Before recommending downgrade:

- inspect schema versions;
- preserve user data;
- confirm older application can read current data;
- provide reverse migration only when tested;
- warn when downgrade is unsupported.

A new fix release is preferred over destructive rollback.

---

# 121. Reproducibility verification

A release should be reproducible from:

```text
tag
source archive
declared Python version
declared build dependencies
build command
package configuration
```

Minimum reproducibility check:

- build twice from clean environments where practical;
- compare package contents;
- explain permitted metadata differences;
- compare hashes when deterministic builds are supported.

A release must not claim byte-for-byte reproducibility without proof.

---

## 122. Source-to-artifact traceability

For each release artifact, record:

```text
release version
tag
commit
filename
size
SHA-256
build command
build environment
```

For project PGF:

```text
project version
entrypoints
GF version
GF Wordbench version
source revision
SHA-256
```

---

# 123. Manifest use in release

A GF Wordbench run manifest validates run artifacts.

A distribution checksum file validates published distribution artifacts.

They serve different scopes.

Do not substitute one for the other.

For a project release, the run manifest should include the final PGF and required reports.

---

## 124. Manifest verification

Before project release approval:

- load manifest;
- verify schema;
- verify every required entry exists;
- recompute SHA-256;
- verify size;
- reject path escape;
- reject unexpected mutation after manifest creation;
- confirm required role coverage.

---

# 125. Release report

The release manager should produce a concise final release report.

Recommended sections:

```text
Release identity
Scope
Versions
Compatibility
Schema changes
Contract changes
Migrations
Test evidence
Artifacts and hashes
Known issues
Approvals
Publication verification
```

This report is release evidence, not a replacement for `summary.json` or the changelog.

---

# 126. Approval record

Minimum approval record:

```text
release
approver
date
evidence reviewed
exceptions
decision
```

Decision:

```text
approved
rejected
approved with documented exception
```

---

# 127. Exception record

Every approved exception must state:

```text
gate
reason
risk
equivalent evidence
scope
expiry
follow-up
approver
```

Exceptions must not become undocumented permanent policy.

---

# 128. Release automation

Automation may:

- run gates;
- build packages;
- generate hashes;
- create draft releases;
- upload staged artifacts;
- verify package metadata;
- verify published downloads;
- assemble evidence.

Automation must not:

- choose a breaking version silently;
- approve migrations automatically without tests;
- update project gold automatically;
- mark a release stable before required verification;
- move an existing tag;
- overwrite published artifacts.

---

## 129. Release command

A future command may coordinate release checks:

```text
gf-wordbench release check
```

Possible strict mode:

```text
gf-wordbench release check --strict
```

The command may verify:

- versions;
- schema constants;
- contracts;
- required tests;
- artifact paths;
- changelog;
- compatibility;
- project release gates.

It does not replace human approval.

---

# 130. CI release workflow

Recommended CI release sequence:

```text
static
    ↓
unit/component
    ↓
contracts/schemas/migrations
    ↓
security
    ↓
Windows/POSIX
    ↓
real GF
    ↓
end-to-end
    ↓
package build
    ↓
artifact inspection
    ↓
staged publication
    ↓
post-publication verification
```

Each stage should expose bounded evidence.

---

# 131. CI trust boundary

Release credentials must be:

- limited to release jobs;
- inaccessible to pull-request code from untrusted sources;
- scoped to required destinations;
- rotated;
- excluded from logs;
- unavailable to normal validation scenarios.

GF project content must not be able to access publishing credentials through inherited environment values.

---

# 132. Release artifact retention

Retain stable release artifacts according to distribution policy.

At minimum retain:

- source tag;
- source archive;
- package artifacts;
- hashes;
- release notes;
- migration guide;
- compatibility matrix.

Do not depend solely on one ephemeral CI run.

---

# 133. Release metrics

Optional release metrics may include:

```text
test count
coverage
platforms tested
GF versions tested
migration fixtures
artifact count
release duration
```

Metrics do not determine version or replace gates.

---

# 134. Manual verification

Manual verification is limited to behavior not reasonably automated.

Examples:

- GUI visual smoke;
- installer prompt;
- operating-system warning;
- release-page presentation;
- signing prompt.

Record:

```text
environment
steps
expected
actual
reviewer
date
evidence
```

---

# 135. Release communication accuracy

Release communication must not claim:

- support not present in the compatibility matrix;
- a tested GF version without evidence;
- successful migration not exercised;
- signed artifacts when unsigned;
- reproducible builds without proof;
- project linguistic completeness beyond release criteria;
- zero known issues when nonblocking issues remain documented.

---

# 136. Release-process drift indicators

Release drift exists when:

- package version differs from CLI version;
- changelog version differs from tag;
- published artifact differs from approved hash;
- a release is tagged before gates complete;
- a schema changed without migration;
- a contract changed without consumer tests;
- gold changes without review;
- required real-GF tests skip;
- framework release depends on active-language success;
- project release omits PGF verification;
- manifest is generated before final reports;
- published artifact is overwritten under the same version;
- release notes omit a required migration;
- unknown GF version is labeled tested;
- source tree is dirty during stable build;
- package includes local state or run artifacts;
- a release exception lacks approval;
- a hotfix is not forward-ported;
- candidate and stable artifacts come from different unrecorded commits;
- post-publication verification is omitted;
- release announcement occurs before verification.

Any drift indicator blocks or invalidates release approval.

---

# 137. Framework release approval checklist

```text
Identity
[ ] deliverable identified
[ ] release type identified
[ ] version classified
[ ] version source consistent
[ ] tag available

Compatibility
[ ] Python range verified
[ ] GF range verified
[ ] platform matrix verified
[ ] project schema support verified
[ ] summary schema support verified
[ ] deprecations verified

Architecture
[ ] contract locks current
[ ] schema lock current
[ ] external-tool lock current
[ ] artifact ownership current
[ ] dependency direction passes

Validation
[ ] static checks pass
[ ] unit/component tests pass
[ ] contracts pass
[ ] schemas pass
[ ] migrations pass
[ ] security tests pass
[ ] platform tests pass
[ ] real-GF tests pass
[ ] E2E tests pass
[ ] coverage passes

Packaging
[ ] clean build
[ ] package content verified
[ ] install smoke passes
[ ] versions agree
[ ] hashes generated

Documentation
[ ] changelog finalized
[ ] release notes finalized
[ ] migration guide finalized
[ ] compatibility matrix finalized
[ ] known issues accurate

Publication
[ ] approval recorded
[ ] tag created
[ ] artifacts uploaded
[ ] hashes verified
[ ] installed from published artifact
[ ] post-publication smoke passes
[ ] release evidence archived
```

---

# 138. Project release approval checklist

```text
Identity
[ ] project ID verified
[ ] project version classified
[ ] source revision clean
[ ] framework version recorded
[ ] GF version recorded

Project contracts
[ ] project.toml validates
[ ] project contract lock current
[ ] category/lincat contract current
[ ] validation spec current
[ ] release criteria current
[ ] known issues reviewed

Validation
[ ] release mode executed
[ ] required source modules pass
[ ] required entrypoints pass
[ ] required PGF exists
[ ] required scenarios pass
[ ] required gold matches
[ ] no required scenario skipped
[ ] release gates pass

Artifacts
[ ] summary.json valid
[ ] summary.md present
[ ] AI_READY.md present
[ ] top_errors.txt present
[ ] master.log present
[ ] manifest valid
[ ] PGF hash verified
[ ] published artifacts match hashes

Publication
[ ] project release notes complete
[ ] tag/archive created
[ ] artifacts published
[ ] post-publication verification passes
[ ] evidence archived
```

---

# 139. Hotfix approval checklist

```text
[ ] affected version identified
[ ] defect reproduced
[ ] regression test added
[ ] compatibility impact classified
[ ] schema/migration impact reviewed
[ ] focused security review complete when applicable
[ ] full mandatory gates pass
[ ] upgrade from affected version tested
[ ] corrected version selected
[ ] changelog updated
[ ] new immutable artifacts built
[ ] publication verified
[ ] active development receives the fix
```

---

# 140. Security approval checklist

```text
[ ] vulnerability scope identified
[ ] affected versions identified
[ ] exploit regression exists
[ ] unsafe behavior removed
[ ] secrets absent from evidence
[ ] process/path/security contracts reviewed
[ ] migration or mitigation documented
[ ] package integrity verified
[ ] disclosure plan approved
[ ] new version published
[ ] advisory published when safe
[ ] unsafe release marked or withdrawn
```

---

# 141. Prohibited release behavior

The following are prohibited:

- releasing from an uncommitted working tree;
- publishing before required gates;
- silently skipping real-GF release tests;
- moving a published tag;
- rebuilding a published version with different content;
- publishing artifacts from a different commit than the tag;
- changing schema meaning without versioning;
- changing normalization without gold review;
- treating a missing PGF as success;
- treating a missing manifest as success;
- using active project success as framework proof;
- using framework success as project proof;
- automatic gold approval;
- hiding failed migrations;
- omitting breaking changes from release notes;
- claiming unsupported GF compatibility;
- publishing secrets or environment dumps;
- using shell commands built from untrusted project text in release automation;
- overwriting previous release artifacts silently;
- announcing stable release before post-publication verification;
- deleting historical evidence to conceal a defective release.

---

# 142. Final invariants

1. Framework, template, and project releases remain distinct.
2. Every release has one classified version in its own domain.
3. Published versions and tags are immutable.
4. Stable releases come from clean source.
5. Changelog, package, CLI, GUI, reports, and tag agree.
6. Schema changes are versioned and migrated.
7. Contract changes update providers and consumers.
8. Normalization changes trigger deliberate gold review.
9. Required test gates cannot skip silently.
10. Real-GF integration is required for a stable framework release.
11. Active-language release requires GF Wordbench release mode.
12. Required project scenarios cannot be skipped.
13. Required PGF must exist and be non-empty.
14. Required reports and manifest must exist.
15. Manifest hashes final artifacts.
16. Package artifacts are built from the approved commit.
17. Published downloads are verified independently.
18. Release evidence is retained.
19. Security may override compatibility when required for safety.
20. A defective release is replaced by a new version, not mutated.
21. Rollback guidance respects schema compatibility.
22. Release automation never provides final approval by itself.
23. Exceptions are explicit, bounded, and approved.
24. Framework fixtures remain language-neutral.
25. Project release evidence records framework and GF versions.
26. No release claims compatibility beyond recorded evidence.
27. Release notes do not replace migration documentation.
28. Release candidates are immutable and sequential.
29. Hotfixes are forward-ported.
30. Publication is complete only after post-publication verification.

---

# 143. Final rule

The GF Wordbench release process follows one controlled evidence chain:

```text
classified change
    → correct versions
    → synchronized contracts and schemas
    → tested migrations
    → complete release gates
    → clean reproducible artifacts
    → approval
    → immutable tag
    → publication
    → independent verification
    → retained evidence
```

A release must stop at the first missing link.

No artifact may be called a completed GF Wordbench release until every required link is present and verified.
