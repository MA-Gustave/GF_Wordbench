# GF Wordbench — Release Process

**Document ID:** `GF-WB-RELEASE-PROCESS`  
**Status:** Normative release procedure  
**Applies to:** GF Wordbench framework releases, project-template releases, active-project releases, prereleases, hotfixes and security releases  
**Owner:** GF Wordbench maintainers and designated release manager  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Versioning authority:** `CHANGELOG.md` and the published package metadata  
**Schema authority:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Contract authorities:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Process version:** `1.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines the release process for GF Wordbench.

It specifies:

- independently releasable deliverables;
- release roles and workflow states;
- version and compatibility review;
- contract, schema and migration review;
- required tests and platform evidence;
- package and project-artifact construction;
- candidate, approval, tagging and publication procedures;
- post-publication verification;
- hotfix, security, withdrawal and rollback procedures;
- evidence retention.

The governing rule is:

> A release is complete only when its source, versions, contracts, schemas, tests, artifacts, migration notes, changelog, tag and published outputs describe the same approved product state.

Passing tests alone is insufficient.

Building an artifact alone is insufficient.

Creating a tag alone is insufficient.

Publication is complete only after the published outputs are independently verified.

---

## 2. Product boundary

GF Wordbench and `gf-portfolio` are independent products.

This process covers:

```text
GF Wordbench framework
GF Wordbench project template
one active GF language project
```

It does not cover a `gf-portfolio` product release.

A Portfolio release may consume public, versioned Wordbench artifacts. Wordbench release tooling must not depend on Portfolio code, runtime, storage, schemas, configuration or publication state.

One Wordbench project release concerns exactly one project identity and one normative language target.

---

## 3. Related authority

```text
CHANGELOG.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/development/TESTING_GF_WORDBENCH.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/ARTIFACT_MANIFEST.md
docs/validation/RELEASE_GATES.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Priority when rules overlap:

1. accepted ADRs and the documentation-alignment lock govern product and architecture decisions;
2. package metadata and release version policy govern version identity;
3. the persisted-schema lock governs serialized compatibility;
4. contract locks govern provider, consumer and external-tool boundaries;
5. testing policy governs executable evidence;
6. this document governs release sequencing and approval;
7. project release criteria govern the active project.

---

## 4. Releasable deliverables

GF Wordbench recognizes three independently releasable deliverables:

```text
framework
project template
active project
```

A combined publication may include more than one deliverable. Each deliverable retains its own:

- version;
- source identity;
- compatibility statement;
- gates;
- artifacts;
- approval;
- publication evidence.

A successful release of one deliverable does not prove that another deliverable is releasable.

---

## 5. Framework release

A framework release publishes the GF Wordbench software.

It may include:

- Python distribution;
- CLI;
- GUI when included by package metadata;
- framework documentation;
- schemas;
- project loader;
- process execution adapters;
- validation modules;
- diagnostics;
- report writers;
- migration utilities;
- project template.

A framework release does not certify the linguistic completeness of the active project.

Framework integration tests use language-neutral fixture projects rather than depending on the active `project/`.

---

## 6. Project-template release

A template release publishes the reusable structure under:

```text
templates/project/
```

It proves that a new project can be initialized from a language-neutral source.

Template requirements:

- generic placeholders only;
- no active-language identity;
- no machine-local path;
- no application state;
- no run artifact;
- valid project documentation structure;
- compatibility with the framework project loader;
- successful initialization and smoke validation.

The template may be bundled with a framework release, but its version and evidence remain identifiable.

---

## 7. Active-project release

An active-project release publishes or certifies the project under:

```text
project/
```

It may include:

- GF source modules;
- project configuration;
- project documentation;
- native `.gfs` scenarios;
- inputs;
- reviewed gold files;
- PGF;
- release reports;
- artifact manifest;
- checksums.

The project release records:

```text
project ID
project version
source revision
GF Wordbench version
GF version
RGL release or revision
normalization version
PGF SHA-256
```

A project release does not change the GF Wordbench framework version automatically.

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

Release type affects gates, communication and publication channel. It does not override compatibility or versioning rules.

### 8.1 Stable

A stable release is intended for supported use.

It requires:

- approved version;
- complete changelog and release notes;
- required migrations;
- all mandatory gates;
- no unresolved blocker;
- immutable publication;
- post-publication verification.

### 8.2 Release candidate

A release candidate is a complete candidate for a stable release.

It uses the intended:

- schemas;
- migration behavior;
- report identities;
- compatibility matrix;
- package structure.

A release candidate must not conceal a missing required capability.

### 8.3 Alpha and beta

Alpha may expose incomplete or experimental behavior.

Beta has the planned release scope but may require broader compatibility verification.

Both must:

- identify instability;
- avoid stable-support claims;
- use versioned persisted formats;
- preserve migration evidence;
- avoid overwriting stable data silently.

### 8.4 Hotfix

A hotfix corrects an urgent defect in a published release.

Typical examples:

- process cleanup failure;
- incorrect diagnostic interpretation;
- report defect;
- platform regression;
- package metadata defect;
- migration correction preserving intended semantics.

### 8.5 Security

A security release addresses vulnerabilities involving:

- process execution;
- command injection;
- path traversal;
- symlink or junction escape;
- secret disclosure;
- scenario execution;
- artifact overwrite;
- untrusted file handling.

Safety may require a compatibility break. The release must document the impact and migration or mitigation.

---

## 9. Roles

A small team may combine roles, but responsibilities remain explicit.

```text
release manager
change owner
test owner
schema and contract reviewer
project maintainer
security reviewer
approver
```

### 9.1 Release manager

Owns:

- release plan;
- proposed version;
- checklist;
- commit selection;
- gate coordination;
- artifact build;
- tag creation;
- publication;
- post-publication verification;
- evidence archive.

The release manager cannot convert a failed gate into success without an approved exception.

### 9.2 Change owner

Confirms:

- included scope;
- relevant tests;
- known limitations;
- affected contracts;
- affected schemas;
- migration impact;
- documentation updates.

### 9.3 Test owner

Confirms:

- required suites ran;
- required platforms were covered;
- real-GF tests did not skip unexpectedly;
- coverage policy passed;
- quarantined tests are documented;
- failure evidence is retained.

### 9.4 Schema and contract reviewer

Confirms:

- version increments match semantic impact;
- providers and consumers agree;
- migrations exist where required;
- canonical writers emit current formats;
- supported older inputs remain readable;
- locks, models and fixtures agree.

### 9.5 Project maintainer

For an active-project release, confirms:

- project scope;
- project version;
- scenarios;
- gold expectations;
- release criteria;
- PGF entrypoints;
- known nonblocking limitations;
- project documentation.

### 9.6 Security reviewer

Required when a release changes:

- process execution;
- environment inheritance;
- path containment;
- scenario trust;
- secret redaction;
- external-tool integration;
- migration of untrusted files;
- overwrite or update behavior.

### 9.7 Approver

Confirms:

- no required gate is missing;
- exceptions are explicit;
- evidence matches the proposed version;
- release notes are accurate;
- publication may proceed.

A one-person project may use self-approval, but the evidence must still record the review.

---

## 10. Workflow states

Release workflow states are process metadata, not implementation-status tracking.

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

- `proposed`: scope and version are under review.
- `planned`: intended scope and compatibility impact are recorded.
- `in preparation`: scope is frozen and gates are running.
- `candidate`: immutable candidate artifacts exist.
- `approved`: required evidence authorizes publication.
- `published`: artifacts are available at the designated destination.
- `verified`: published artifacts were fetched or installed and checked.
- `withdrawn`: the release remains identifiable but should not be used.
- `superseded`: a newer release replaces it operationally.
- `aborted`: preparation ended before publication.

A published or tagged identifier is never reused for different bytes.

---

## 11. Release evidence

Release preparation creates a dedicated evidence directory outside the active project source and package source.

Canonical shape:

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

Retain, as applicable:

```text
tag
commit ID
source archive hash
version audit
test commands and results
coverage report
GF version output
platform details
schema validation output
migration evidence
package artifacts
package hashes
release-mode summary and manifest
PGF hash
approval record
publication verification
```

Secrets and complete environment dumps are prohibited.

---

## 12. Release initiation

A release begins with a plan containing:

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
publication destinations
owners
```

Before candidate preparation, freeze the intended scope.

After freeze, allowed changes are limited to:

- release-blocker corrections;
- documentation corrections;
- packaging corrections;
- migration corrections;
- security corrections;
- test corrections that expose or prove release behavior.

Unrelated features move to another release.

---

## 13. Source and branch rules

A release branch may use:

```text
release/<version>
```

A hotfix branch may use:

```text
hotfix/<version>
```

Branches are optional.

When used:

- start from a reviewed passing commit;
- accept only release-relevant changes;
- forward-port every correction;
- avoid permanent divergent implementations;
- tag the exact approved commit.

Stable preparation requires:

- expected branch or commit;
- no uncommitted production change;
- no modified fixture outside release scope;
- no tracked generated run artifact;
- no temporary migration file;
- no local secret;
- no stale build artifact.

A dirty tree is permitted only for diagnostic builds, never for stable publication.

---

## 14. Version and changelog

Classify compatibility before reserving a version.

Review:

```text
application behavior
persisted schemas
public contracts
CLI
GUI
Python API when public
platform support
GF support
project-template compatibility
active-project compatibility
```

The largest required version impact governs the framework version.

Before reserving a version, verify:

- identifier is valid;
- tag is unused;
- publication destination has no conflicting artifact;
- changelog has no conflicting published section;
- candidate sequence is monotonic.

Update the canonical application version once. Derived version displays read from that source.

Verify agreement among:

```text
package metadata
CLI
GUI
report producer metadata
release tag
```

Move release entries from `Unreleased` into the versioned changelog section at publication.

Release notes include:

- purpose;
- principal changes;
- compatibility;
- installation and upgrade impact;
- migrations;
- known issues;
- supported GF and Python ranges;
- supported platforms;
- verification summary.

Release notes do not replace the changelog or migration guide.

---

## 15. Schema audit

For every persisted schema, record:

```text
schema ID
current version
version emitted by the release
supported older versions
migration availability
compatibility classification
fixtures
round-trip status
```

Applicable families include:

```text
gf-wordbench.project
gf-wordbench.app-state
gf-wordbench.run-summary
gf-wordbench.artifact-manifest
scenario-output and gold formats defined by the schema lock
```

A schema change requires:

- updated schema lock;
- canonical writer and reader;
- migration when required;
- minimal and complete fixtures;
- invalid fixtures;
- legacy fixtures;
- round-trip tests;
- deterministic serialization tests;
- path-base tests;
- changelog entry.

Unknown newer major versions must be rejected explicitly.

---

## 16. Contract audit

Review:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

For every changed contract:

- semantic version impact is correct;
- the contract is active and normative;
- provider exists;
- consumers exist;
- public symbols or message shapes agree;
- artifact ownership is singular;
- tests exist;
- migration exists when required;
- prohibited dependencies remain absent.

Stable release behavior must not depend on an inactive, experimental or undocumented contract.

---

## 17. External-tool audit

Verify:

- GF executable resolution;
- exact version probe;
- supported GF range;
- typed command construction;
- ordered argument arrays;
- explicit working directories;
- controlled environment policy;
- finite timeouts;
- separate stdout and stderr;
- native `.gfs` standard input;
- required-artifact declarations;
- no implicit shell;
- version-sensitive diagnostics;
- optional diagnostic-tool contracts.

---

## 18. Normalization and gold audit

When scenario behavior or normalization changes:

1. preserve before-and-after raw evidence;
2. verify normalization version;
3. run normalization fixtures;
4. inspect changed normalized outputs;
5. inspect changed gold files;
6. confirm no meaningful linguistic output was removed;
7. confirm headers and metadata agree;
8. document regeneration or migration;
9. record project impact;
10. run required scenario release tests.

Widespread unexplained gold changes block release.

Gold updates remain explicit project-maintenance operations. Release automation must not approve them automatically.

---

## 19. Migration and deprecation audit

Each migration is tested against:

```text
valid legacy input
minimal legacy input
complete legacy input
ambiguous input
invalid input
already canonical input
target collision
write failure
repeated execution
```

Verify:

- source remains intact until success;
- losses are reported;
- warnings are actionable;
- target validates;
- canonical writer emits no legacy aliases.

Each deprecation records:

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

A removal must satisfy the documented deprecation window or an approved emergency exception.

---

## 20. Compatibility matrix

Before candidate approval, publish the supported matrix.

Minimum dimensions:

```text
GF Wordbench version
Python versions
GF versions
project schema versions
run-summary schema versions
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

Do not label a version or platform `tested` without evidence.

---

## 21. Documentation audit

Verify that:

- README reflects current product identity;
- installation instructions match package metadata;
- CLI reference matches the command parser;
- GUI reference matches shipped behavior;
- project-template paths exist;
- release notes match the changelog;
- migration procedures are complete;
- deprecated names are not presented as current;
- generated paths use the correct base;
- normative links resolve;
- release version is consistent;
- Wordbench documentation does not describe Portfolio as an internal module;
- no implementation-status labels are used as product documentation.

---

## 22. Framework and template isolation

A framework release test must not depend on the linguistic correctness of the active project.

Use a dedicated language-neutral fixture project.

A template audit verifies:

- documented structure;
- generic placeholders;
- no active-language identity;
- no machine-local path;
- no state or run artifact;
- required documentation;
- project-loader compatibility;
- successful initialized-project smoke test.

---

## 23. Release gates

Exact commands and package roots are defined by `pyproject.toml` and `docs/development/TESTING_GF_WORDBENCH.md`.

Required gate families:

```text
format and lint
type checking
documentation consistency
dependency direction
version consistency
artifact ownership
contract validation
unit and component tests
schema and migration tests
security tests
platform tests
real-GF tests
fake-GF end-to-end
real-GF end-to-end
coverage
repository cleanliness
```

Required tests must not skip unexpectedly.

Expected failures require a current issue and removal condition.

A retry-only pass is not stable evidence.

### 23.1 Security evidence

At minimum:

- argument-boundary tests;
- no shell injection;
- path traversal rejection;
- symlink and junction containment;
- secret redaction;
- bounded output;
- scenario OS-escape policy;
- gold-write separation;
- safe artifact destinations;
- no environment dump.

### 23.2 Windows evidence

At minimum:

- paths with spaces;
- Unicode paths;
- `gf.exe` or a controlled fake executable;
- CRLF input;
- timeout and cancellation;
- child-process termination;
- drive handling;
- junction containment;
- atomic writes;
- CLI launcher;
- GUI launcher when shipped.

### 23.3 POSIX evidence

At minimum:

- executable permission;
- Unicode paths;
- search-path separator behavior;
- process-group termination;
- symlink containment;
- atomic writes;
- installed CLI execution.

### 23.4 Real-GF evidence

At minimum:

- version probe;
- successful compilation;
- failing compilation;
- explicit GF search path;
- PGF build;
- native `.gfs` execution;
- parsing;
- linearization;
- bounded generation;
- marker checks;
- Unicode;
- required-artifact verification.

---

## 24. End-to-end release flow

Required real-GF flow:

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

Fake-GF end-to-end proves framework control and failure semantics.

Real-GF end-to-end proves the external GF contract.

---

## 25. Coverage and cleanliness

Coverage thresholds are owned by the testing policy.

A threshold must not be reduced merely to release the current changes.

After all gates:

- tracked fixtures remain unchanged unless intentionally updated;
- project gold remains unchanged unless explicitly reviewed;
- no owned child process remains;
- no untracked secret exists;
- no generated run or package artifact is staged accidentally;
- the source tree remains reproducible.

---

## 26. Package build and inspection

Build from the exact candidate commit in a clean environment.

Framework distribution artifacts may include:

```text
wheel
source distribution
source archive
checksums
release notes
migration guide
compatibility matrix
test and coverage summaries
```

The release plan identifies which formats are required.

Clean build environment:

- supported Python;
- declared build dependencies;
- no editable installation;
- no uncommitted changes;
- no inherited application state;
- no hidden GF path dependency;
- controlled dependency retrieval.

Inspect package contents.

Required inclusions:

- production package content;
- metadata;
- license;
- required resources;
- template assets when shipped.

Required exclusions:

- local state;
- active project source unless intentionally packaged;
- generated run artifacts;
- evidence directory;
- secrets;
- caches;
- temporary files;
- developer snapshots.

---

## 27. Installation smoke and version audit

Install the built artifact into a clean environment.

Verify:

```text
distribution metadata
CLI help
CLI version
configuration inspection without GF
GUI import or launch when shipped
package resources
```

Do not rely on repository-relative imports.

Verify version agreement among:

```text
installed distribution
public CLI
public GUI
report producer metadata
release tag
```

Internal Python package paths are not duplicated in this process document; they come from package metadata and architecture documentation.

---

## 28. Checksums and signing

Use SHA-256 for distribution-artifact integrity.

Canonical checksum line:

```text
<sha256><two spaces><filename>
```

Artifact signing may be used only under a documented key-management and verification policy.

When signing is enabled, record:

- signing identity;
- key custody;
- signature format;
- verification procedure;
- rotation;
- revocation;
- CI access policy.

Unsigned artifacts must not be described as signed.

---

## 29. Candidate process

Create an immutable candidate tag only after candidate artifacts pass internal verification.

Example:

```text
v1.2.0-rc.1
```

Do not rebuild the same candidate identifier with different bytes.

Candidate publication identifies:

- prerelease status;
- intended stable version;
- tested compatibility;
- known issues;
- migrations;
- feedback channel;
- installation separation from stable releases.

During candidate validation:

- test clean installation and upgrade;
- test required platforms;
- run real-GF integration;
- inspect reports and manifests;
- review migration logs;
- collect blockers;
- add no unrelated features.

A blocker requires:

1. correction;
2. regression test;
3. updated candidate notes;
4. affected and mandatory gates;
5. incremented candidate identifier;
6. new artifacts and immutable tag.

---

## 30. Stable approval

Approval evidence includes:

```text
version audit
required gates
clean install smoke
real-GF end-to-end
schema and migration audit
contract audit
security audit when applicable
compatibility matrix
release notes
checksums
candidate blocker resolution
```

A required gate may be waived only when:

- an external reason makes it impossible;
- equivalent evidence exists;
- risk is documented;
- approver accepts the risk;
- release notes disclose the limitation;
- a follow-up exists.

Normally non-waivable:

- version consistency;
- package installability;
- required schema validity;
- required migration safety;
- process-security invariants;
- manifest integrity;
- source preservation;
- absence of known data-loss defects.

Before stable tagging:

1. update publication date;
2. approve changelog and release notes;
3. confirm version source;
4. confirm no code changed after gates;
5. build from the approved commit;
6. verify package contents and hashes;
7. record approval.

---

## 31. Tagging and publication

Stable tag:

```text
v<MAJOR>.<MINOR>.<PATCH>
```

Tags and published artifacts are immutable.

Stable artifacts are built from the stable tag or its exact commit.

Record:

```text
tag
commit
build environment
build command
filename
size
SHA-256
```

Publication destinations may include:

- package registry;
- source-hosting release page;
- internal artifact repository;
- signed archive location;
- project release location.

The release plan names the actual destinations.

Publication sequence:

1. publish source tag;
2. upload package artifacts;
3. upload checksums or signatures;
4. publish release notes;
5. publish migration guide;
6. publish compatibility matrix;
7. promote the release;
8. begin independent verification.

When staging is supported, verify privately before promotion.

When publication is partially complete, do not announce a stable release.

---

## 32. Post-publication verification

Use a clean environment separate from the build environment.

Verify:

```text
tag resolves
published artifacts download
SHA-256 matches
package installs
version matches
CLI help works
configuration inspection works
real-GF smoke works when required
migration example works
release notes and links resolve
```

A release is not verified merely because upload succeeded.

If a downloaded hash differs:

- stop announcement;
- mark publication incomplete or withdraw it;
- do not overwrite the version silently;
- investigate build or publication contamination;
- publish a corrected new version when required.

Announce only after verification.

---

## 33. Framework release checklist

```text
[ ] scope frozen
[ ] release type and version classified
[ ] canonical version source updated
[ ] package metadata agrees
[ ] changelog and release notes approved
[ ] compatibility matrix approved
[ ] schema audit complete
[ ] contract audit complete
[ ] external-tool audit complete
[ ] normalization and gold audit complete
[ ] migration and deprecation audit complete
[ ] documentation audit complete
[ ] template audit complete when shipped
[ ] static and dependency gates pass
[ ] unit and component suites pass
[ ] contract suites pass
[ ] schema and migration suites pass
[ ] security suites pass
[ ] required platform suites pass
[ ] real-GF suite passes
[ ] fake-GF and real-GF end-to-end pass
[ ] coverage policy passes
[ ] no unexpected skip or strict xpass
[ ] repository is clean
[ ] package builds from approved commit
[ ] package-content audit passes
[ ] clean installation smoke passes
[ ] version audit passes
[ ] checksums generated
[ ] candidate validated when required
[ ] approval recorded
[ ] immutable tag created
[ ] artifacts published
[ ] published hashes verified
[ ] post-publication smoke passes
[ ] release evidence archived
```

---

## 34. Template release process

1. classify template-version impact;
2. update template version;
3. validate the template contract;
4. validate placeholder policy;
5. initialize a temporary project;
6. fill test placeholders;
7. load `project.toml`;
8. run fake-GF smoke validation;
9. run real-GF fixture validation when applicable;
10. verify language neutrality;
11. verify absence of local paths and run artifacts;
12. package or publish the template;
13. verify the downloaded template;
14. record framework compatibility.

Checklist:

```text
[ ] template version classified
[ ] required files exist
[ ] generic placeholders only
[ ] no active-language identity
[ ] no machine-local path
[ ] no state file
[ ] no generated artifact
[ ] initialized project configuration validates
[ ] template contract matches framework loader
[ ] initialized project passes smoke validation
[ ] documentation links resolve
[ ] archive contents verify
[ ] compatibility range recorded
```

---

## 35. Active-project release process

The active project release is driven by:

```text
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

Sequence:

1. freeze project scope;
2. classify project version;
3. update project version;
4. validate project configuration;
5. validate the project contract lock;
6. review the project status ledger;
7. run release-mode validation;
8. validate required source and entrypoints;
9. build the PGF;
10. run required scenarios;
11. compare required gold;
12. evaluate release gates;
13. publish reports;
14. verify the artifact manifest;
15. review linguistic changes;
16. prepare project release notes;
17. tag or archive the project revision;
18. publish project artifacts;
19. verify published PGF and evidence.

Required prerequisites:

- one active project identity;
- one normative language target;
- canonical `project.toml`;
- no unresolved required placeholder;
- declared entrypoints and checkpoints;
- required scenarios;
- valid required gold files;
- documented release criteria;
- no unresolved blocker;
- supported Wordbench and GF versions;
- clean source revision.

Required project evidence normally includes:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master log
required compiler streams
required scenario streams
normalized scenario outputs
gold diffs on failure
PGF
project version
source revision
GF Wordbench version
GF version
```

A successful release contains no required failure or skipped required criterion.

---

## 36. Project artifact verification

PGF verification:

- expected path exists;
- file is non-empty;
- path is run-owned;
- configured entrypoints were used;
- GF version is recorded;
- SHA-256 is recorded;
- manifest entry exists;
- previous release artifact was not overwritten;
- published hash matches release evidence.

Required scenario verification:

- scenario exists;
- process executed;
- required marker sections completed;
- assertions passed;
- normalization version matches;
- required gold matches;
- required artifacts exist;
- result is `OK`.

`SKIPPED` is not success for a required scenario.

A nonblocking project issue may remain only when it is:

- explicitly permitted by release criteria;
- documented;
- scoped;
- supported by evidence;
- neither a security issue nor an invalid-evidence issue.

---

## 37. Combined release

A combined framework, template and project publication executes each applicable checklist independently.

Do not infer:

```text
framework passed -> project passed
project passed -> framework passed
```

Record:

```text
framework version
template version
project version
GF version
RGL revision
```

---

## 38. Hotfix and security releases

### 38.1 Hotfix

1. identify affected release;
2. reproduce defect;
3. assess security, schema, data and compatibility impact;
4. add regression test;
5. implement the minimal correction;
6. classify version impact;
7. update changelog;
8. run focused and mandatory gates;
9. build clean artifacts;
10. publish a new immutable version;
11. verify upgrade from the affected version;
12. communicate mitigation;
13. forward-port the correction.

A hotfix does not skip schema or migration review.

### 38.2 Security release

1. limit disclosure;
2. preserve evidence securely;
3. identify affected versions;
4. implement the safe correction;
5. add exploit regression tests;
6. assess compatibility impact;
7. prepare migration or mitigation;
8. execute mandatory gates;
9. build and verify artifacts;
10. publish a new version;
11. publish advisory when safe;
12. provide upgrade instructions;
13. mark or withdraw unsafe releases where operationally possible.

Non-waivable security-release evidence:

- exploit regression;
- process, path and security contract tests;
- package integrity;
- migration safety when data changes;
- version consistency;
- clean installation;
- post-publication verification.

---

## 39. Failed and defective releases

Abort preparation when:

- scope cannot stabilize;
- required gates fail;
- migration is unsafe;
- package cannot install;
- evidence is inconsistent;
- version classification is unresolved;
- security review blocks publication.

Withdraw a candidate under its existing historical identifier and publish a corrected candidate with a new identifier.

For a defective stable release:

1. assess severity;
2. stop promotion;
3. mark the affected release;
4. preserve published artifacts;
5. publish mitigation;
6. prepare a corrected new version;
7. test upgrade and rollback guidance;
8. verify corrected publication.

Never silently replace published bytes.

Withdrawal record:

```text
version
reason
date
affected artifacts
recommended replacement
mitigation
```

Rollback is operational, not a mutation of the release. Downgrade guidance must respect persisted-schema compatibility and preserve user data.

---

## 40. Reproducibility and traceability

A release is reproducible from:

```text
tag
source archive
supported Python version
declared build dependencies
build command
package configuration
```

When practical:

- build twice in clean environments;
- compare package contents;
- explain permitted metadata differences;
- compare hashes when deterministic builds are supported.

Do not claim byte-for-byte reproducibility without evidence.

For each distribution artifact, record:

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

For a project PGF, record:

```text
project version
entrypoints
GF version
GF Wordbench version
source revision
SHA-256
```

The run manifest verifies run artifacts.

The distribution checksum file verifies published distribution artifacts.

They are different integrity scopes.

---

## 41. Release report and approvals

The release manager produces a concise release report containing:

```text
release identity
scope
versions
compatibility
schema changes
contract changes
migrations
test evidence
artifacts and hashes
known issues
approvals
publication verification
```

Approval record:

```text
release
approver
date
evidence reviewed
exceptions
decision
```

Allowed decisions:

```text
approved
rejected
approved with documented exception
```

Each exception records:

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

Exceptions must not become undocumented policy.

---

## 42. Automation and CI

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

- select a breaking version silently;
- approve migrations without tests;
- update project gold automatically;
- mark a release stable before verification;
- move a tag;
- overwrite published artifacts;
- require `gf-portfolio` for Wordbench release completion.

Exact CLI release commands, if exposed, are defined by `docs/usage/CLI_REFERENCE.md`. This document does not invent command syntax.

Canonical CI stages:

```text
static checks
    -> unit and component
    -> contracts, schemas and migrations
    -> security
    -> required platforms
    -> real GF
    -> end-to-end
    -> package build
    -> artifact inspection
    -> staged publication
    -> post-publication verification
```

Release credentials are isolated from untrusted pull-request code and from GF project content.

---

## 43. Communication accuracy

Release communication must not claim:

- support absent from the compatibility matrix;
- tested GF versions without evidence;
- successful migrations not exercised;
- signed artifacts when unsigned;
- reproducible builds without proof;
- project linguistic completeness beyond release criteria;
- no known issues when documented nonblocking issues remain;
- Portfolio integration as a Wordbench runtime requirement.

---

## 44. Drift indicators

Release drift exists when:

- package version differs from CLI or tag;
- changelog version differs from tag;
- published bytes differ from approved hashes;
- tag is created before required gates;
- schema changes without migration;
- contract changes without consumer tests;
- gold changes without review;
- required real-GF tests skip;
- framework release depends on active-project success;
- project release omits PGF verification;
- manifest is generated before owned artifacts are closed;
- published artifacts are overwritten under the same version;
- release notes omit a required migration;
- unknown GF version is labeled tested;
- source tree is dirty during stable build;
- package contains local state or run artifacts;
- an exception lacks approval;
- hotfix is not forward-ported;
- candidate and stable artifacts come from unrecorded different commits;
- announcement occurs before verification;
- Wordbench release depends on `gf-portfolio` availability.

Any drift indicator blocks or invalidates approval.

---

## 45. Prohibited behavior

The following are prohibited:

- releasing from an uncommitted stable-build tree;
- publishing before required gates;
- silently skipping required real-GF tests;
- moving a published tag;
- rebuilding a published version with different content;
- publishing artifacts from a different commit than the tag;
- changing schema meaning without versioning;
- changing normalization without gold review;
- treating a missing PGF or manifest as success;
- using active-project success as framework proof;
- using framework success as project proof;
- automatic gold approval;
- hiding failed migrations;
- omitting breaking changes from release notes;
- claiming unsupported GF compatibility;
- publishing secrets or environment dumps;
- building shell commands from untrusted project text;
- overwriting previous release artifacts;
- announcing stable release before post-publication verification;
- deleting historical evidence to conceal a defect;
- publishing several active projects as one Wordbench project release;
- treating `gf-portfolio` as an internal Wordbench release module.

---

## 46. Governing invariants

1. Framework, template and project releases remain distinct.
2. One project release represents one project identity and one normative language target.
3. Each deliverable has one classified version in its own domain.
4. Published versions, tags and candidate identifiers are immutable.
5. Stable releases come from clean source.
6. Changelog, package metadata, public version displays, reports and tag agree.
7. Schema changes are versioned and migrated.
8. Contract changes update providers and consumers.
9. Normalization changes trigger deliberate gold review.
10. Required gates cannot skip silently.
11. Real-GF integration is required for stable framework release evidence.
12. Active-project release uses release-mode validation.
13. Required project scenarios cannot be skipped.
14. Required PGF is present and non-empty.
15. Required reports and manifest exist.
16. The manifest hashes closed, finalized artifact bytes.
17. Distribution artifacts are built from the approved commit.
18. Published downloads are independently verified.
19. Release evidence is retained.
20. Safety may override compatibility.
21. A defective release is replaced by a new version, not mutated.
22. Rollback guidance respects schema compatibility.
23. Automation never provides approval by itself.
24. Exceptions are explicit, bounded and approved.
25. Framework fixtures remain language-neutral.
26. Project release evidence records framework and GF versions.
27. Compatibility claims do not exceed evidence.
28. Release notes do not replace migration documentation.
29. Candidate identifiers are immutable and sequential.
30. Hotfixes are forward-ported.
31. Wordbench releases do not depend on `gf-portfolio`.
32. Publication is complete only after post-publication verification.

---

## 47. Governing rule

The release process follows one controlled evidence chain:

```text
classified change
    -> correct versions
    -> synchronized contracts and schemas
    -> tested migrations
    -> complete gates
    -> clean reproducible artifacts
    -> approval
    -> immutable tag
    -> publication
    -> independent verification
    -> retained evidence
```

A release stops at the first missing link.

No artifact is a completed GF Wordbench release until every required link is present and verified.
