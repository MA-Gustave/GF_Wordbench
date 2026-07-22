# Active Project — Release Criteria

**Document ID:** `GF-WB-PROJECT-RELEASE-CRITERIA`  
**Status:** Normative active-project release gate  
**Applies to:** The single active GF language project configured by `project/project.toml`  
**Project identity source:** `project/project.toml`  
**Contract source:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Validation source:** `project/docs/VALIDATION_SPEC.md`  
**Known-state sources:** `project/docs/STATUS_LEDGER.md` and `project/docs/KNOWN_ISSUES.md`  
**Decision source:** `project/docs/DECISION_LOG.md`  
**Primary owners:** Active-project maintainers  
**Review authority:** Project release approver  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines the exact conditions under which the active GF language project may be declared release-ready.

It converts project configuration, module contracts, validation results, scenario expectations, gold files, generated artifacts, documentation, known issues, and release evidence into one explicit release decision.

A release is approved only when the project can demonstrate that:

- the intended source state is known;
- the configured project identity is internally consistent;
- all required module contracts remain valid;
- required checkpoints compile;
- required release entrypoints compile;
- required scenarios execute and pass;
- required gold comparisons match reviewed expectations;
- the required PGF is built and verified;
- required evidence and reports are complete;
- no undocumented fallback or release blocker remains;
- the result is reproducible under the declared GF toolchain;
- the final run completed with `overall_status = OK`.

This document is project-specific in scope but resolves concrete module, entrypoint, scenario, and artifact names from the active project configuration and project contract registry.

It must not duplicate those names as independent sources of truth.

---

## 2. Governing release rule

> The active project may be released only when every required gate is satisfied by current, complete, reproducible evidence from the exact source revision being released.

A release must not be approved from:

- memory;
- an old run directory;
- an uncommitted or unknown source state;
- direct compilation of only one top-level module;
- stale `.gfo` files;
- a pre-existing `.pgf`;
- scenario output that lacks required markers;
- gold files changed only to remove failures;
- a partial or errored run;
- screenshots without structured evidence;
- undocumented manual exceptions;
- optional-stage success masking a required-stage failure.

---

## 3. Normative terms

The following terms are normative:

- **MUST**: mandatory for release.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **RELEASE CANDIDATE**: exact source revision and configuration proposed for release.
- **GATE**: condition that must pass before release approval.
- **BLOCKER**: condition that prevents release.
- **WAIVER**: explicit time-bounded approval for a permitted exception.
- **CHECKPOINT**: configured module proving that a project layer remains coherent.
- **ENTRYPOINT**: configured top-level GF module used for release validation or PGF construction.
- **REQUIRED SCENARIO**: scenario whose non-success prevents release.
- **OPTIONAL SCENARIO**: visible scenario whose result is not release-gating unless project policy says otherwise.
- **GOLD**: reviewed normalized expected output for a scenario.
- **CURRENT ARTIFACT**: artifact proven to have been produced from the release candidate during the release run.
- **RELEASE RUN**: finalized GF Wordbench run used as release evidence.
- **RELEASE EVIDENCE**: machine-readable and human-readable records proving gate outcomes.
- **ACCEPTED ISSUE**: known issue explicitly reviewed and marked non-blocking.
- **RELEASE EXCEPTION**: approved departure from a normally required criterion where this document permits an exception.
- **CUTOVER**: point at which the approved release becomes the active published project version.
- **ROLLBACK**: restoration of the last approved release state.

---

## 4. Related project documents

Release approval depends on the following active-project files:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RESEARCH_EVIDENCE.md
project/docs/RELEASE_CRITERIA.md
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Framework-level references include:

```text
docs/validation/VALIDATION_MODES.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/RELEASE_GATES.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/release/VERSIONING_POLICY.md
docs/release/MIGRATION_AND_DEPRECATION.md
```

When this document and `project/docs/INTERFILE_CONTRACT_LOCK.md` disagree about a project contract, the project lock is authoritative.

The disagreement must be corrected before release.

---

## 5. Sources of truth

Release evaluation uses the following ownership model.

| Release fact | Authoritative source |
|---|---|
| Project identity | `project/project.toml` |
| Source root and selection | `project/project.toml` |
| GF path parts | `project/project.toml` |
| Checkpoint order | `project/project.toml` |
| Release entrypoints | `project/project.toml` |
| Required and optional scenarios | `project/project.toml` |
| Expected PGF and artifacts | `project/project.toml` and project contract lock |
| GF module contracts | project interfile contract lock |
| Dependency direction | `LANGUAGE_ARCHITECTURE.md` |
| Actual dependency registry | `MODULE_DEPENDENCY_MAP.md` |
| Lincat structures | `CATEGORY_AND_LINCAT_CONTRACT.md` |
| Morphology promises | `MORPHOLOGY_SPEC.md` |
| Constructor behavior | `SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Validation meanings | `VALIDATION_SPEC.md` |
| Coverage | `TEST_COVERAGE_MATRIX.md` |
| Temporary and blocked work | `STATUS_LEDGER.md` |
| Known defects | `KNOWN_ISSUES.md` |
| Significant accepted changes | `DECISION_LOG.md` |
| Final run evidence | finalized release run |
| Final machine status | `summary.json` |
| Artifact integrity | `manifest.json` |

No GUI state, old run, local shell alias, or developer-specific path is an authoritative project fact.

---

# 6. Release decision outcomes

The release decision has four outcomes:

```text
APPROVED
REJECTED
DEFERRED
CANCELLED
```

## 6.1 `APPROVED`

Use only when:

- every mandatory gate passes;
- every required result is `OK`;
- required final artifacts exist and verify;
- every accepted issue is explicitly non-blocking;
- every approved waiver is valid;
- the release run is finalized;
- the approver records approval.

## 6.2 `REJECTED`

Use when:

- a mandatory gate fails;
- a required criterion is `FAIL`;
- a required operation is `ERROR`;
- a release-blocking issue remains;
- evidence is invalid or incomplete;
- source identity cannot be established;
- required artifacts are missing or stale.

## 6.3 `DEFERRED`

Use when:

- release evaluation has not completed;
- approval evidence is incomplete but not known to be invalid;
- a required external review is pending;
- a fix is planned before a new candidate is produced.

A deferred candidate is not releasable.

## 6.4 `CANCELLED`

Use when the candidate is withdrawn intentionally.

Cancellation must not be presented as project validation failure.

---

# 7. Release gate summary

The mandatory gate families are:

```text
GATE 01 — candidate identity
GATE 02 — repository and source integrity
GATE 03 — project configuration
GATE 04 — toolchain compatibility
GATE 05 — project contracts
GATE 06 — module dependency integrity
GATE 07 — source-quality and scan policy
GATE 08 — checkpoint compilation
GATE 09 — release-entrypoint compilation
GATE 10 — PGF construction
GATE 11 — required scenario execution
GATE 12 — marker and assertion completion
GATE 13 — gold integrity and comparison
GATE 14 — linguistic and coverage review
GATE 15 — known issues and status ledger
GATE 16 — documentation consistency
GATE 17 — artifact and manifest integrity
GATE 18 — report and schema finalization
GATE 19 — determinism and repeatability
GATE 20 — security and data hygiene
GATE 21 — release version and change record
GATE 22 — approval and rollback readiness
```

The project may add stricter gates.

It must not silently weaken these gates.

---

# 8. Gate status vocabulary

Each gate uses:

```text
PASS
FAIL
ERROR
NOT_APPLICABLE
WAIVED
PENDING
```

Meaning:

| Gate status | Meaning |
|---|---|
| `PASS` | Required criterion is satisfied |
| `FAIL` | Criterion was evaluated and not satisfied |
| `ERROR` | Criterion could not be evaluated reliably |
| `NOT_APPLICABLE` | Gate is genuinely outside this project’s declared release policy |
| `WAIVED` | Permitted exception approved under this document |
| `PENDING` | Evaluation not complete |

Rules:

- `PENDING` prevents approval;
- `FAIL` prevents approval;
- `ERROR` prevents approval;
- `NOT_APPLICABLE` requires a documented reason;
- `WAIVED` is permitted only for explicitly waivable criteria;
- core evidence, required compilation, required scenarios, and artifact integrity are not normally waivable.

---

# 9. Gate 01 — Release candidate identity

The release candidate MUST have one unambiguous identity.

Required evidence:

```text
project ID
project display name
language code
module suffix
source repository identity
source revision
branch or release line
working-tree state
project configuration hash
candidate version or release label
release run ID
```

Criteria:

- `project/project.toml` loads successfully;
- project ID is stable and canonical;
- project identity agrees with active module suffixes;
- source revision is recorded;
- dirty state is either absent or fully enumerated;
- untracked active source is prohibited unless deliberately included and recorded;
- release run references the same source state;
- old-language identifiers do not influence active paths, scenarios, golds, or docs;
- one active language project is represented.

Blockers:

```text
unknown source revision
unrecorded active source modifications
multiple active project identities
module suffix mismatch
release run from a different source state
```

---

# 10. Gate 02 — Repository and source integrity

The source tree MUST be complete, readable, and protected from generated-artifact confusion.

Criteria:

- every selected `.gf` file exists;
- every selected file is inside the configured source root;
- source selection is deterministic;
- excluded active-looking files have documented reasons;
- no duplicate normalized paths exist;
- no case-insensitive path collisions exist;
- filename and declared GF module name agree;
- no unresolved merge markers remain;
- no editor backup is selected as active source;
- generated `.gfo` and `.pgf` files are not authoritative source;
- source fingerprints use the canonical algorithm;
- required source fingerprints are valid;
- source files remain unchanged during validation;
- active source does not depend on undocumented local files.

Recommended source-integrity checks:

```text
project names check
source inventory comparison
module-name/file-name check
old-identifier scan
hash/fingerprint check
```

A required fingerprint failure is a release `ERROR`.

---

# 11. Gate 03 — Project configuration

`project/project.toml` MUST satisfy the current project schema and project contracts.

Required configuration includes or resolves:

```text
project identity
source root
source glob
include/exclude policy
ordered GF path parts
ordered checkpoints
ordered entrypoints
required scenarios
optional scenarios
scenario paths
scenario inputs
scenario gold associations
release-required entrypoints
expected release artifacts
PGF requirement
```

Criteria:

- schema ID and version are supported;
- no unresolved required placeholder remains;
- every relative path resolves from the project root;
- no project-owned path escapes the project;
- every checkpoint exists;
- every entrypoint exists;
- scenario IDs are unique;
- required scenario scripts exist;
- optional scenarios are marked explicitly;
- expected PGF identity is unambiguous;
- order-sensitive arrays are deterministic;
- no developer-local absolute executable or RGL path is stored as project identity;
- release policy is not inferred from GUI state.

Blockers:

```text
invalid TOML
unsupported project schema
missing required field
duplicate scenario ID
missing entrypoint
missing checkpoint
unsafe path
ambiguous expected artifact
```

---

# 12. Gate 04 — GF toolchain compatibility

The release run MUST use a supported and recorded GF toolchain.

Required evidence:

```text
resolved GF executable
GF version probe output
parsed GF version
compatibility classification
effective GF path
RGL root or revision
working directory
platform
```

Criteria:

- the executable resolves explicitly;
- version probing succeeds unless release policy defines an approved equivalent;
- GF version is supported for release;
- the effective GF path is recorded;
- required path parts exist;
- compilation and scenarios use the same path-resolution policy;
- no hidden developer-global path changes semantics;
- required command options are supported by the selected GF version;
- Windows path behavior is valid when Windows is a supported release platform;
- untested newer GF versions are not treated as supported release toolchains without explicit approval and evidence.

A launch failure, unsupported version, or unresolvable path is a release `ERROR`.

---

# 13. Gate 05 — Project contract integrity

Every active project contract required for release MUST be valid.

Criteria:

- every active provider exists;
- every active consumer exists;
- every required relationship has a stable contract ID;
- provider and consumer descriptions agree;
- public symbols and types agree;
- required lincat fields agree;
- constructor arity and ordering agree;
- helper ownership is unambiguous;
- entrypoint ownership is unambiguous;
- scenario and gold ownership are registered;
- expected PGF ownership is registered;
- every active contract has validation evidence;
- no required contract remains merely experimental;
- no release-required contract is blocked;
- deprecated contracts have valid replacement/migration status;
- retired contracts are not used by active files.

Required check:

```text
project contract validation
```

A contract mismatch is a release blocker even when isolated compilation happens to succeed.

---

# 14. Gate 06 — Module dependency integrity

The actual GF dependency graph MUST agree with the documented project architecture.

Criteria:

- dependency direction follows `LANGUAGE_ARCHITECTURE.md`;
- no circular imports exist;
- lower-level modules do not import final entrypoints;
- one provider owns each public helper role unless a documented exception exists;
- interfaces and instances match;
- provider changes have all consumers reviewed;
- the dependency map names all configured entrypoints and checkpoints;
- no active module is unintentionally unreachable;
- no release entrypoint depends on test-only or retired modules;
- inherited behavior and local overrides follow documented policy;
- source moves and renames are reflected in documentation and validation.

Default expected direction:

```text
resources and morphology
→ category implementations
→ paradigms and lexicon
→ syntax, structural and extension layers
→ grammar or API entrypoints
→ PGF
```

Any documented exception requires a decision-log entry.

---

# 15. Gate 07 — Source-quality and scan policy

Static scan policy MUST be evaluated according to `VALIDATION_SPEC.md`.

Criteria:

- required scanner stage completes;
- source decoding succeeds;
- required scan logs exist;
- prohibited source patterns are absent or explicitly accepted;
- trailing-space or formatting policy is satisfied where gating;
- undocumented string-based fallbacks are absent;
- suspicious operators or patterns are reviewed;
- scan findings do not contradict status-ledger claims;
- no scanner `ERROR` remains;
- accepted non-blocking findings remain visible.

A scan finding is not automatically a GF language failure.

The project validation specification determines which findings are release-blocking.

A required scanner execution error prevents release.

---

# 16. Gate 08 — Checkpoint compilation

Every configured required checkpoint MUST compile before final entrypoint validation.

Criteria:

- checkpoint order follows project configuration and dependency order;
- every required checkpoint is attempted;
- no required checkpoint is `SKIPPED`;
- every required checkpoint status is `OK`;
- no checkpoint times out;
- no checkpoint launch fails;
- no checkpoint has a syntax or type failure;
- no required current artifact is missing;
- compile stdout and stderr are retained separately;
- compile command and working directory are recorded;
- direct/downstream causality is classified after evidence exists;
- downstream failures are not misreported as independent root causes;
- artifacts are current-run or request-isolated.

Release-blocking outcomes:

```text
FAIL
ERROR
SKIPPED
```

A required checkpoint may be skipped only through a formally approved release exception.

Such an exception is permitted only when:

- the checkpoint is temporarily impossible for an external reason;
- equivalent or stronger evidence exists;
- the project contract permits the substitution;
- the exception is time-bounded;
- the approver records it;
- the release is not represented as satisfying the omitted checkpoint itself.

For normal releases, checkpoint waivers SHOULD NOT be used.

---

# 17. Gate 09 — Release-entrypoint compilation

Every configured release entrypoint MUST compile successfully from the release candidate.

Criteria:

- entrypoint source exists;
- module/file identity matches;
- entrypoint is registered;
- every required checkpoint has already passed;
- compile request is reproducible;
- process launches;
- no timeout occurs;
- exit semantics indicate success;
- no fatal diagnostic remains;
- required `.gfo` exists when promised;
- produced artifacts are current;
- entrypoint does not depend on stale source-adjacent artifacts;
- output evidence is retained;
- status is `OK`.

Direct compilation of an entrypoint does not override a failed lower checkpoint.

An entrypoint that compiles only when a required lower checkpoint is omitted does not satisfy release criteria.

---

# 18. Gate 10 — PGF construction

When `project.toml` declares that release requires a PGF, the final PGF MUST be built and verified.

Required evidence:

```text
PGF target identity
entrypoints used
GF command
GF version
effective GF path
working directory
timeout
stdout
stderr
exit code
artifact path
artifact size
artifact hash
manifest role
```

Criteria:

- required entrypoints passed;
- PGF build process launches;
- no timeout occurs;
- process completes successfully;
- no fatal diagnostic remains;
- expected PGF exists;
- expected PGF is a regular file;
- PGF is non-empty;
- PGF is current for this release run;
- PGF path is inside the owned artifact root;
- filename agrees with project configuration;
- required concrete language is represented according to project policy;
- PGF is registered in `manifest.json`;
- PGF hash is recorded after final bytes are stable;
- required PGF smoke scenarios pass when configured.

A pre-existing PGF is not release evidence.

A successful process without the expected PGF is `ERROR`.

When the project explicitly does not require a PGF, this gate may be `NOT_APPLICABLE` only if the reason is documented in project configuration and release policy.

---

# 19. Gate 11 — Required scenario execution

Every required scenario registered in the active project MUST execute.

Criteria:

- scenario ID is unique;
- script exists;
- script path is project-relative and safe;
- scenario loads its documented entrypoint;
- required inputs exist;
- input encoding and ordering are documented;
- command is supported by the selected GF version;
- process launches;
- no timeout occurs;
- execution is not cancelled;
- stdout and stderr are retained separately;
- normalized output is produced when required;
- scenario status is `OK`;
- no required scenario is missing or skipped.

A required scenario that fails to load its entrypoint is a release failure.

An unsupported GF command that is ignored does not count as scenario success.

Optional scenarios may fail or warn only when:

- they are explicitly optional;
- their result remains visible;
- they are not required by another release criterion;
- their failure does not reveal a broader release blocker.

---

# 20. Gate 12 — Marker and assertion completion

Scenario process success alone is insufficient.

Criteria:

- every required begin marker exists;
- every required begin marker has a matching end marker;
- section IDs are unique;
- marker identity is preserved through normalization;
- every required section is marked complete;
- declarative assertions are evaluated;
- no required assertion fails;
- assertion semantics match the current scenario contract;
- no scenario is accepted from an incomplete output fragment.

Missing or malformed required markers are release errors.

A zero process exit code does not override missing markers.

---

# 21. Gate 13 — Gold integrity and comparison

Every required gold-backed scenario MUST have one valid reviewed gold file and an exact current comparison.

Criteria:

- gold file exists;
- gold filename matches scenario ID;
- gold header scenario ID matches;
- gold schema version is supported;
- normalization version matches the scenario result;
- required sections exist;
- section markers are balanced;
- gold is UTF-8 and follows newline policy;
- gold comparison executes;
- `gold_match = true`;
- normal validation has not modified gold;
- no unreviewed candidate gold remains;
- gold changes in the candidate are associated with an intentional source, scenario, specification, GF compatibility, or normalization change;
- significant gold changes have decision-log review;
- meaningful linguistic output has not been normalized away.

Release-blocking conditions:

```text
missing required gold
malformed gold
normalization error
normalization-version mismatch
gold mismatch
unreviewed gold update
nondeterministic gold output
```

Gold files MUST NOT be updated merely to make release validation pass.

---

# 22. Gate 14 — Linguistic and coverage review

Automated success MUST be accompanied by coverage appropriate to the declared release scope.

The project coverage matrix MUST map release claims to evidence.

Review areas include, where applicable:

```text
module loading
missing linearizations
noun morphology
verb morphology
adjective morphology
pronouns
determiners
structural lexicon
basic clause construction
questions
relatives
coordination
extensions
linearization
parsing
bounded generation
morphology tables
final PGF behavior
```

Criteria:

- declared supported constructions have validation evidence;
- unsupported areas are documented;
- representative examples are reviewed;
- known ambiguity is documented;
- missing-linearization results satisfy project policy;
- no release claim exceeds coverage evidence;
- gold changes affecting linguistic output receive linguistic review;
- research-sensitive behavior references evidence when required;
- test inputs remain representative and bounded.

A compile-only project is not automatically linguistically release-ready.

---

# 23. Gate 15 — Known issues and status ledger

Every known temporary, fallback, warning, blocked, disabled, deprecated, or incomplete state MUST be registered and reviewed.

Criteria:

- `STATUS_LEDGER.md` is current;
- `KNOWN_ISSUES.md` is current;
- source comments do not contradict ledger entries;
- every temporary implementation has an owner;
- every temporary implementation has a next action or exit condition;
- every issue states whether it blocks release;
- resolved entries retain resolution records;
- no undocumented warning is silently accepted;
- no release-blocking entry remains open;
- no required function is disabled;
- no required provider contract is blocked;
- accepted non-blocking issues have explicit rationale;
- accepted issues do not invalidate release claims.

A release-blocking ledger entry prevents approval.

A known issue may be accepted only when:

- impact is understood;
- it does not violate a mandatory contract;
- validation still proves the release scope;
- the approver accepts it explicitly;
- it appears in release notes when user-visible.

---

# 24. Gate 16 — Documentation consistency

Project documentation MUST agree with the release candidate.

Required documents MUST exist and be current.

Criteria:

- `LANGUAGE_OVERVIEW.md` matches project identity and supported scope;
- `LANGUAGE_ARCHITECTURE.md` matches module layers;
- `MODULE_DEPENDENCY_MAP.md` matches actual dependencies;
- `CATEGORY_AND_LINCAT_CONTRACT.md` matches public lincat shapes;
- `MORPHOLOGY_SPEC.md` matches implemented paradigms and features;
- `SYNTAX_AND_CONSTRUCTOR_RULES.md` matches constructor behavior;
- `VALIDATION_SPEC.md` matches configured modes and scenarios;
- `TEST_COVERAGE_MATRIX.md` matches actual coverage;
- `STATUS_LEDGER.md` matches incomplete code;
- `DECISION_LOG.md` includes significant breaking decisions;
- `KNOWN_ISSUES.md` matches accepted defects;
- `RELEASE_CRITERIA.md` matches current gates;
- `RESEARCH_EVIDENCE.md` is current where project claims depend on it;
- project contract lock reflects current providers and consumers;
- no old-language identifier remains active;
- no required template placeholder remains unresolved;
- documentation paths point to existing files.

Documentation drift is a release blocker when it affects public, architectural, validation, or release meaning.

Minor prose errors may be corrected before final tagging without rerunning GF unless they alter a contract or criterion.

---

# 25. Gate 17 — Artifact and manifest integrity

The release run MUST contain all required artifacts and a valid manifest.

Required canonical files normally include:

```text
summary.json
summary.md
manifest.json
master log
compile evidence
scenario evidence
required normalized outputs
required generated GF artifacts
required PGF
```

Project or framework policy may additionally require:

```text
AI_READY.md
top_errors.txt
aggregate logs
detail reports
release package
checksums
```

Criteria:

- each required artifact exists;
- each required file is inside the run root;
- every required artifact has one owner;
- manifest path is canonical;
- manifest entries are deterministically ordered;
- file size is correct;
- SHA-256 matches final bytes;
- artifact role is valid;
- requiredness is correct;
- duplicate paths are absent;
- unsafe symlink targets are absent;
- manifest excludes itself when required by manifest contract;
- no artifact changes after final hashing;
- generated artifacts are associated with the release candidate.

A required artifact missing from the manifest is a release error.

A manifest hash mismatch is a release error.

---

# 26. Gate 18 — Report and schema finalization

The release run MUST be finalized successfully.

Criteria:

- `summary.json` parses;
- summary schema ID and version are supported;
- required root fields exist;
- metadata identifies the release run;
- count invariants hold;
- file results are complete;
- scenario results are complete;
- overall status is `OK`;
- required artifact paths resolve;
- `summary.md` exists when required;
- required AI or human reports exist;
- final report writers completed;
- no report writer reran validation;
- no critical finalization warning remains;
- final run is discoverable as complete;
- incomplete-run sentinel is absent or finalization state is complete;
- manifest and summary agree.

A run that passed validation but failed required summary or manifest finalization is `ERROR` and cannot support release.

---

# 27. Gate 19 — Determinism and repeatability

Release evidence SHOULD be reproducible from the same source, configuration, GF version, and inputs.

For high-confidence releases, run release validation at least twice in clean or isolated artifact directories.

Criteria:

- compile plan order is identical;
- checkpoint order is identical;
- scenario order is identical;
- statuses are identical;
- gold results are identical;
- expected artifact names are identical;
- PGF creation succeeds consistently;
- normalized scenario output is stable;
- no timestamp, temporary path, or machine-specific noise affects gold;
- any binary artifact differences are understood and do not invalidate functional reproducibility;
- no hidden global environment variable changes results;
- previous-run diff does not reveal unexplained regression.

A nondeterministic required gold scenario blocks release.

A nondeterministic PGF byte hash may be accepted only if:

- upstream GF is known to produce nondeterministic binary bytes;
- functional PGF validation passes;
- the cause is documented;
- artifact provenance remains complete;
- project release policy explicitly permits it.

---

# 28. Gate 20 — Security and data hygiene

The release candidate and evidence MUST satisfy security and privacy requirements.

Criteria:

- no secrets exist in source-controlled project configuration;
- no tokens or credentials exist in reports or logs;
- command arguments are safely structured;
- shell escape is disabled unless explicitly approved;
- project paths remain contained;
- run artifact paths remain contained;
- no unsafe symlink overwrite is possible;
- no source file was overwritten by validation;
- gold files changed only through the explicit update path;
- migration operations preserved source;
- output-size limits were enforced;
- untrusted input did not select arbitrary destinations;
- release package does not include local state, temporary files, backups, or personal paths;
- third-party data licensing is satisfied;
- known security issues are reviewed.

A credential leak, unsafe path, source overwrite, or unapproved arbitrary command execution is an unconditional release blocker.

---

# 29. Gate 21 — Release version and change record

The project release identity MUST be documented according to the project’s versioning policy.

Required evidence:

```text
release version or release label
source revision
project contract version when applicable
GF Wordbench package version
GF version
project schema version
gold schema version
normalization version
release run ID
release date
```

Criteria:

- version increment matches project change severity;
- breaking project changes have migration notes;
- scenario ID, entrypoint, lincat, or PGF-name changes are classified correctly;
- changelog or release notes list user-visible changes;
- gold changes are explained;
- known issues are listed;
- deprecated and removed project behavior is listed;
- source tag or release record agrees with the candidate;
- no published version is reused for different bytes or source.

When the project schema does not yet define a persisted project version field, the version MUST be recorded in the release record or version-control tag rather than added silently to `project.toml`.

---

# 30. Gate 22 — Approval and rollback readiness

Final release approval MUST be explicit.

Required approval record:

```text
candidate identity
release version
release run ID
decision
approver
approval date
waivers
accepted issues
artifact location
rollback reference
```

Rollback readiness requires:

- previous approved release revision is known;
- previous release artifacts are recoverable;
- rollback owner is known;
- release package replacement procedure is known;
- schema/project migration rollback limits are documented;
- new release does not destroy previous gold or source history;
- emergency withdrawal procedure exists.

A release without rollback reference is not approved.

---

# 31. Mandatory non-waivable gates

The following are non-waivable for a normal release:

```text
unambiguous project identity
known source revision
valid project configuration
supported GF execution
required checkpoint completion
required entrypoint completion
required scenario completion
required marker completion
required gold integrity
required PGF when configured
required artifact existence
manifest integrity
summary finalization
overall_status = OK
absence of security blockers
explicit approval
```

A release omitting any of these is not a normal release.

An emergency distribution that cannot satisfy them must be labeled and governed separately.

It must not be presented as a validated normal release.

---

# 32. Waivable criteria

A limited waiver MAY apply to:

```text
optional scenario failure
non-gating scan warning
minor documentation formatting issue
non-critical optional report failure
accepted non-blocking known issue
temporarily unavailable optional external tool
repeat-run requirement when an emergency deadline exists
```

Waiver requirements:

- stable waiver ID;
- exact criterion;
- reason;
- evidence;
- risk;
- scope;
- owner;
- approver;
- expiration;
- follow-up action;
- release-note visibility when user-impacting.

A waiver cannot change a `FAIL` or `ERROR` into `OK` in `summary.json`.

It changes only the release decision under explicitly permitted criteria.

---

# 33. Waiver record

Recommended format:

```text
Waiver ID:
Release candidate:
Criterion:
Original result:
Reason:
Risk:
Compensating evidence:
Scope:
Approved by:
Approved on:
Expires:
Follow-up:
Release-note requirement:
```

Waiver IDs use a stable project registry family.

Example family:

```text
REL-WAIVER-001
```

The exact registry belongs to project policy.

Waiver IDs must not be reused.

---

# 34. Release exceptions and project contract changes

A release exception MUST NOT be used to bypass a changed project contract.

If a criterion fails because the intended contract changed:

1. identify the contract ID;
2. update provider and consumers;
3. update project configuration;
4. update scenarios and inputs;
5. update gold deliberately;
6. update documentation;
7. record the decision;
8. rerun checkpoint and release validation.

A waiver is not a substitute for migration.

---

# 35. Optional scenarios

Optional scenarios remain visible.

Release may proceed after an optional scenario `FAIL` or `ERROR` only when:

- the scenario is explicitly optional;
- no required contract depends on it;
- its result does not reveal a required entrypoint or project-wide failure;
- the reason is reviewed;
- the release decision records it;
- release notes include it when user-visible.

An optional scenario that detects a general safety, data corruption, or final-PGF problem becomes release-blocking regardless of its configured optionality.

---

# 36. Required scenario policy

A required scenario MUST be:

```text
registered
present
readable
supported by the GF version
linked to the documented entrypoint
provided with required inputs
provided with required gold or assertions
executed
complete
OK
```

A required scenario cannot be marked optional solely for one failing release candidate without a project contract change and decision record.

---

# 37. Missing-linearization policy

The required missing-linearization scenario or equivalent MUST satisfy the project’s declared policy.

Possible project policies include:

```text
no missing linearizations
only explicitly accepted missing functions
category-scoped accepted omissions
no new missing functions relative to baseline
```

The exact policy belongs to `VALIDATION_SPEC.md`.

Release criteria:

- command or scenario completes;
- output is bounded;
- output is normalized;
- accepted omissions are documented;
- unexpected missing functions cause `FAIL`;
- missing-function gold is reviewed;
- no unsupported command is accepted as success.

An empty output is not automatically correct unless the scenario contract defines it as correct.

---

# 38. Linearization policy

Required linearization scenarios MUST cover representative project contracts.

Criteria:

- test trees are reviewed;
- output is non-empty where required;
- orthography is correct;
- spacing and punctuation are correct;
- agreement is correct;
- word order matches the documented syntax;
- variants are represented according to policy;
- empty versus missing output is distinguished;
- gold matches;
- changed output is reviewed linguistically.

A project release claiming support for a construction SHOULD include at least one representative linearization scenario for that construction or an explicitly stronger equivalent.

---

# 39. Parse policy

Required parse scenarios MUST define:

```text
language
category
input
accepted trees or assertion
ambiguity policy
failure expectation where applicable
```

Criteria:

- required positive cases parse;
- required negative cases do not parse when specified;
- accepted ambiguity is documented;
- unexpected parse expansion is reviewed;
- tree identity and ordering are handled according to scenario policy;
- gold or assertions pass;
- parse result is produced by the release entrypoint or approved PGF target.

---

# 40. Generation policy

Generation is release-gating only when project policy marks it required.

Exact generation gold requires:

```text
bounded output
stable ordering or non-semantic sorting
stable seed when applicable
documented category
documented depth/size bound
```

Unbounded or nondeterministic generation MUST NOT use exact gold.

Use assertions when exact text is not stable.

Any generation run that exceeds limits is `ERROR`, not an accepted partial pass.

---

# 41. Morphology policy

Required morphology validation SHOULD cover the paradigms and feature distinctions claimed by the release.

Review may include:

```text
noun forms
verb forms
adjective forms
agreement features
case
number
gender
tense
person
irregular paradigms
orthographic alternations
missing cells
variants
```

Criteria:

- required forms are present;
- impossible or unsupported forms are represented according to policy;
- morphology providers compile;
- paradigm consumers compile;
- representative lexicon consumers compile;
- scenario assertions or gold pass;
- known gaps appear in the status ledger.

---

# 42. Entrypoint-to-scenario consistency

Every required scenario MUST load or use its documented release entrypoint.

Criteria:

- scenario registry names the entrypoint;
- script command agrees;
- entrypoint exists;
- module suffix agrees with project identity;
- lower-level substitute is not used unless scenario purpose explicitly requires it;
- entrypoint changes trigger scenario review;
- entrypoint compile and scenario execution refer to the same source state.

A scenario that passes against a different entrypoint does not prove the release entrypoint.

---

# 43. Scenario-to-gold consistency

Every gold-backed scenario MUST satisfy:

```text
scenario ID = script stem
scenario ID = gold stem
gold header scenario_id = scenario ID
normalization version = executed normalizer version
required sections = gold sections
```

Any mismatch is `ERROR`.

An orphan gold is not release evidence.

An unregistered scenario is not release evidence unless explicitly added to the candidate’s validation contract before approval.

---

# 44. Input integrity

Scenario input files MUST be version-controlled when they define release behavior.

Criteria:

- input path is registered;
- encoding is documented;
- input format is documented;
- ordering semantics are documented;
- file hash or source revision association is available;
- generated temporary inputs do not replace canonical reviewed inputs;
- private or licensed data is handled correctly;
- input changes receive scenario and gold review.

A required input missing at release time is `ERROR`.

---

# 45. Clean build requirement

Release validation MUST use clean or request-isolated generated artifact directories.

It MUST NOT rely on:

```text
previous run .gfo
source-adjacent stale .gfo
previous release .pgf
developer-global build cache without validation
untracked generated files
```

Criteria:

- artifact directories are empty or isolated before build;
- expected artifacts are produced by the release run;
- freshness is verified;
- source fingerprints are recorded;
- artifact provenance is linked to the run;
- cleanup does not delete source.

A validated cache MAY be used only if project and framework release policy explicitly allow it.

The default release policy SHOULD use a clean build.

---

# 46. Previous-run diff policy

Previous-run comparison is supporting evidence.

It MUST NOT replace current validation.

Review:

```text
new failures
regressions
improvements
removed subjects
new subjects
status changes
scenario changes
artifact changes
```

Criteria:

- current result remains authoritative;
- missing previous run is not a current failure;
- malformed previous run produces a warning;
- unexplained regression blocks release;
- intentionally removed subjects are documented;
- new subjects are covered by contracts and validation.

A clean `diff_entries` array is not by itself proof of release readiness.

---

# 47. Top-error policy

For an approved release:

- `top_errors` SHOULD be empty for required failures;
- warnings may remain outside error aggregation;
- no required `FAIL` or `ERROR` may be hidden by aggregation;
- grouped messages must not contain secrets;
- every non-empty top-error entry must be explained before approval.

When `overall_status = OK`, any retained top-error entry requires schema/aggregation review because it may indicate inconsistent status semantics.

---

# 48. Count invariants

The release summary MUST satisfy:

```text
files_included =
  files_ok
  + files_fail
  + files_error
  + files_skipped
```

```text
scenarios_seen =
  scenarios_ok
  + scenarios_fail
  + scenarios_error
  + scenarios_skipped
```

For a normal approved release:

```text
files_fail = 0
files_error = 0
required scenario fail count = 0
scenarios_error = 0 for required scenarios
scenarios_skipped = 0 for required scenarios
overall_status = OK
```

Optional scenario results are interpreted through individual `required` fields.

Count mismatch is a summary invariant error.

---

# 49. Required `summary.json` release facts

The final summary MUST allow a reader to establish:

```text
schema identity and version
producer
run ID
timestamps
duration
GF version
mode = release
project identity
source and path configuration
file totals
scenario totals
overall status
artifact paths
file results
scenario results
diff entries
top errors
```

Release evidence from another mode is insufficient unless the release validation specification explicitly proves equivalent or stronger stages and the run is identified as release-equivalent.

The preferred and canonical mode is:

```text
release
```

---

# 50. Required manifest facts

The manifest MUST identify every required retained file with:

```text
path
role
media type
required flag
size
SHA-256
producer
```

or the current locked manifest equivalent.

Release package consumers MUST resolve artifact paths through the manifest or summary-owned paths.

They must not reconstruct filenames from module names.

---

# 51. Documentation review depth

Release documentation review has three levels.

## 51.1 Existence

Required file exists.

## 51.2 Structural validity

Required sections, IDs, tables, and references exist.

## 51.3 Semantic agreement

Document agrees with source, configuration, scenarios, results, and release claims.

A file passing existence checks but containing stale module names does not satisfy the documentation gate.

---

# 52. Contract review depth

Contract review includes:

```text
provider existence
consumer existence
symbol/type agreement
ordering agreement
failure behavior
artifact ownership
validation evidence
documentation link
status
last review
```

A contract with no current validation evidence cannot support release unless manual inspection is the only possible method and is explicitly recorded.

---

# 53. Decision-log requirements

`DECISION_LOG.md` MUST include significant release-affecting decisions such as:

```text
module ownership changes
lincat shape changes
entrypoint changes
scenario ID changes
gold normalization changes
expected PGF name changes
accepted major linguistic behavior changes
release waivers
accepted high-impact known issues
GF version policy changes
```

Routine compatible bug fixes may be recorded only in changelog/release notes unless project policy requires a decision entry.

---

# 54. Status-ledger release categories

Each open ledger entry SHOULD include one release category:

```text
blocking
non-blocking
informational
```

Examples of normally blocking entries:

```text
required provider blocked
required function disabled
temporary fallback replacing a required final implementation
required scenario unavailable
unknown lincat contract
release entrypoint incomplete
PGF build unavailable
```

Examples that may be non-blocking after review:

```text
optional construction incomplete
performance limitation
non-gating diagnostic warning
future coverage expansion
```

No entry may be considered non-blocking solely because it has existed for a long time.

---

# 55. Known-issue acceptance

A known issue may be accepted when:

- the affected scope is outside the declared release scope; or
- behavior remains contract-compliant; or
- a documented limitation is intentional and validated; or
- the issue affects only an optional capability.

Acceptance record includes:

```text
issue ID
affected modules
affected scenarios
user impact
release impact
workaround
owner
planned action
approval
```

Issues involving data corruption, false success, security, or source overwrite cannot be accepted as non-blocking.

---

# 56. Release candidate freeze

Before the final release run, the candidate SHOULD enter a freeze.

During freeze:

```text
source changes require a new candidate
project.toml changes require a new candidate
scenario changes require a new candidate
input changes require a new candidate
gold changes require a new candidate
normalization changes require a new candidate
GF version changes require a new candidate
release document contract changes require review
```

Pure release-note wording may be corrected without a new GF run when it does not alter claims or criteria.

Any uncertainty requires rerunning release validation.

---

# 57. Changes after release validation

The following changes invalidate the release run:

```text
.gf source byte changes
project.toml changes
scenario script changes
scenario input changes
gold changes
normalizer changes
checkpoint or entrypoint changes
GF executable/version changes
RGL revision changes
required report or artifact writer changes affecting evidence
```

Documentation-only changes invalidate the run when they change:

```text
supported scope
contract meaning
validation criterion
known-issue classification
release gate
```

When invalidated, create a new release run.

Do not edit a finalized summary to match later changes.

---

# 58. Release run selection

The release run used for approval MUST be:

- finalized;
- complete;
- associated with the candidate;
- performed after the last validating change;
- discoverable by run ID;
- protected from accidental mutation;
- retained according to project policy.

When multiple successful release runs exist, the approval record identifies exactly one.

A later verification run may be referenced additionally.

---

# 59. Recommended release execution order

```text
1. verify clean candidate identity
2. validate project schema
3. validate project contracts
4. validate naming and paths
5. resolve GF executable/version/path
6. create clean run directories
7. scan selected sources
8. fingerprint selected sources
9. compile checkpoints in order
10. compile release entrypoints
11. build required PGF
12. execute required scenarios
13. execute optional release scenarios
14. normalize outputs
15. compare required golds
16. classify direct/downstream failures
17. compare previous run
18. write summary and reports
19. write manifest after final bytes stabilize
20. validate summary and manifest
21. review ledgers, docs and coverage
22. record release decision
```

The exact pipeline is owned by the framework release mode and project validation specification.

---

# 60. Recommended commands

Target commands include:

```text
gf-wordbench schemas check --strict
gf-wordbench project contracts check
gf-wordbench names check --strict
gf-wordbench release
```

Additional verification may include:

```text
gf-wordbench schemas check <run>/summary.json
gf-wordbench schemas check <run>/manifest.json
```

Only commands implemented by the current package may be used.

When a named future command is unavailable, use the documented equivalent test or validation operation and record it.

---

# 61. Release evidence directory

The canonical release evidence remains the finalized run directory.

Do not copy selected result files into an undocumented second evidence format.

A release package or archive MAY include:

```text
release artifact
manifest
summary
license
release notes
checksums
```

only according to a documented packaging contract.

The run directory remains the detailed evidence source.

---

# 62. Release package criteria

When a distributable package is produced:

- package identity matches project release identity;
- archive filename follows release naming policy;
- package contains only intended files;
- no state, temporary files, run backups, or personal paths are included;
- required PGF is included when it is the release artifact;
- source inclusion follows project policy;
- licenses and notices are included;
- package checksum is produced;
- package contents are inventoried;
- package extraction is safe;
- a smoke test is performed against the packaged artifact when required.

The package is a derived artifact.

It must not replace source and run evidence.

---

# 63. Release notes

Release notes SHOULD include:

```text
project version or release label
release date
source revision
GF Wordbench version
GF version
major changes
fixed defects
new coverage
known limitations
deprecated behavior
removed behavior
migration actions
gold changes
PGF identity
release run ID
checksums or artifact links
```

Release notes must not claim unsupported features.

---

# 64. Version classification

Project release changes use:

```text
MAJOR
MINOR
PATCH
```

A project major is required for breaking project/public GF contract changes.

A project minor is used for compatible capability additions.

A project patch is used for compatible corrections.

The project version and project contract-lock version may differ but SHOULD be cross-referenced.

A gold body change does not automatically determine version severity.

The underlying linguistic or contract change determines severity.

---

# 65. Emergency release policy

An emergency release may use an accelerated process only for:

```text
security correction
data-corruption correction
source-overwrite prevention
false-release-success correction
critical toolchain incompatibility
```

Emergency criteria that remain mandatory:

```text
known candidate identity
focused validation of the fix
affected contract validation
required artifact integrity
summary/manifest finalization
security review
explicit approval
rollback
```

Any omitted normal gate is listed explicitly.

The release is labeled as emergency and receives a full follow-up release validation as soon as practical.

An emergency process MUST NOT silently call an incomplete run a normal validated release.

---

# 66. Release rejection reasons

The following always reject a normal release:

```text
overall_status != OK
required checkpoint FAIL, ERROR or SKIPPED
required entrypoint FAIL, ERROR or SKIPPED
required scenario FAIL, ERROR or SKIPPED
required gold mismatch
missing required gold
missing required marker
unsupported GF version
missing required PGF
stale required artifact
manifest hash mismatch
summary finalization error
invalid project configuration
release-blocking status entry
undocumented known failure
unresolved contract drift
source identity mismatch
security blocker
unapproved post-run source change
```

---

# 67. Release deferral reasons

Common deferral reasons:

```text
linguistic review pending
release approver unavailable
repeatability run pending
license review pending
migration notes incomplete
optional but high-impact failure under investigation
documentation review incomplete
release package smoke test pending
```

Deferral should identify the next action and owner.

---

# 68. Release approval record

Recommended project release record:

```text
Project ID:
Release version or label:
Source revision:
Project configuration hash:
Project contract version:
GF Wordbench version:
GF version:
RGL revision:
Release run ID:
Release summary path:
Manifest path:
PGF path:
Required scenarios:
Waivers:
Accepted issues:
Decision:
Approver:
Approval date:
Rollback revision:
Notes:
```

This record may be stored in:

```text
release notes
version-control tag annotation
project decision log
a future versioned release manifest
```

Do not introduce a machine-readable release record without registering its schema.

---

# 69. Manual review evidence

Manual review is permitted only where automation cannot fully establish correctness.

Examples:

```text
linguistic acceptability
orthographic convention
research evidence interpretation
license review
visual report readability
```

Manual review record includes:

```text
reviewed subject
reviewer
date
criteria
decision
evidence path
limitations
```

Manual review cannot replace executable evidence for:

```text
compilation
scenario execution
artifact existence
hash verification
schema validity
```

---

# 70. Release review roles

Recommended roles:

```text
release owner
language reviewer
contract reviewer
toolchain reviewer
artifact/release approver
```

One person may hold multiple roles in a small project.

The approval record SHOULD indicate which reviews occurred.

No role may approve evidence they know to be stale or unrelated to the candidate.

---

# 71. Separation of author and approver

For significant releases, the project SHOULD use an approver other than the primary author of the largest breaking change.

When that is impractical:

- self-approval is recorded;
- automated evidence is complete;
- manual review checklist is explicit;
- risk is acknowledged.

Security-sensitive or high-impact migrations SHOULD receive independent review.

---

# 72. Repeatability run

Recommended repeatability procedure:

1. preserve the first successful release run;
2. clear or isolate generated artifacts;
3. rerun release validation with the same candidate and toolchain;
4. compare statuses, normalized outputs, expected artifacts, and manifest roles;
5. explain any allowed binary differences;
6. record the second run ID.

The first or second run may be the approval run.

Both must refer to the same candidate.

---

# 73. Release artifact retention

Retain at least:

```text
approved source revision
project configuration
release run summary
manifest
required raw evidence
required PGF
release package and checksum when distributed
release notes
approval record
```

Retention duration belongs to project operations policy.

Do not retain secrets merely for reproducibility.

---

# 74. Rollback criteria

Rollback SHOULD be initiated when a published release reveals:

```text
security vulnerability
data corruption
false validation success
critical linguistic regression
unloadable PGF
missing required functions
invalid package contents
wrong source revision
wrong project identity
```

Rollback procedure:

1. identify affected release;
2. stop distribution when possible;
3. restore prior approved revision/artifact;
4. record incident;
5. preserve failed release evidence;
6. create corrected candidate;
7. rerun required gates.

Do not delete the failed release evidence needed for investigation.

---

# 75. Post-release verification

After publication, verify:

```text
published artifact hash
download/extraction
PGF loading
release notes links
version/tag identity
project metadata
rollback availability
```

A post-release smoke failure triggers release incident review.

---

# 76. Release incident record

Recommended fields:

```text
Incident ID:
Affected release:
Detected at:
Detected by:
Impact:
Root cause:
Affected contracts:
Affected artifacts:
Immediate action:
Rollback:
Corrective action:
Regression tests:
Follow-up release:
```

Incident IDs require a stable project registry if used persistently.

---

# 77. Template parity

The active project release is not blocked merely because the generic template contains different project-specific values.

It IS blocked when framework-required structure has drifted incompatibly.

Review:

- required project documents exist;
- required project configuration structure is supported;
- required validation directories exist;
- active project contains no template-only unresolved placeholders;
- template migration requirements have been applied where required.

Template content must not overwrite active project content.

---

# 78. Migration readiness

When a release changes project schema or public contracts:

- migration instructions exist;
- supported source versions are identified;
- source remains recoverable;
- migration is explicit;
- losses are documented;
- rollback is documented;
- current writers emit only current forms;
- legacy readers or adapters follow support policy;
- migration tests pass.

A release requiring migration without a migration path is rejected.

---

# 79. Deprecation readiness

A release introducing deprecation must record:

```text
deprecated item
replacement
first deprecated project/framework version
earliest removal
warning behavior
migration action
```

A release removing deprecated behavior must satisfy the support window and versioning policy.

---

# 80. Old-identifier scan

Before approval, scan active project assets for:

```text
previous project ID
previous language code
previous module suffix
previous entrypoints
previous scenario IDs
previous PGF name
legacy tool name
legacy project paths
```

Allowed occurrences:

```text
migration history
decision records
legacy fixtures
explicit historical references
```

Prohibited occurrences:

```text
active project.toml values
active module imports
active scenario commands
active gold headers
current release scripts
current validation paths
```

Any active stale identifier is a release blocker.

---

# 81. Placeholder scan

Before release, required active project files MUST contain no unresolved placeholder tokens.

Scan for patterns such as:

```text
the literal TBD marker
the literal TODO marker
the project-identity placeholder
the language-name placeholder
the module-suffix placeholder
the entrypoint placeholder
the scenario placeholder
an unresolved date placeholder
```

Exceptions:

- documentation discussing placeholder syntax;
- historical examples clearly marked non-active;
- code tests intentionally validating placeholders.

Every match in an active normative section must be reviewed.

---

# 82. Source TODO review

Not every source `TODO` blocks release.

The project must classify active TODOs.

Blocking examples:

```text
required function unimplemented
temporary unsafe fallback
unknown lincat field
disabled release path
placeholder output
```

Potentially non-blocking examples:

```text
performance improvement
future optional coverage
documentation enhancement
```

Every release-relevant TODO must appear in `STATUS_LEDGER.md` or `KNOWN_ISSUES.md`.

---

# 83. Uncommitted-change policy

Preferred normal release state:

```text
clean version-control working tree
```

When the environment is not under version control or a clean tree is impossible:

- inventory all source and project files;
- record hashes;
- archive the exact candidate;
- record why the tree is not clean;
- prohibit further changes before approval.

Uncommitted generated run artifacts outside source do not invalidate the candidate when properly ignored and owned.

Uncommitted source, scenario, gold, or project configuration changes require explicit candidate recording.

---

# 84. Line-ending and encoding policy

Release validation MUST use canonical or supported encodings.

Criteria:

- GF sources decode according to project policy;
- project TOML is UTF-8;
- scenario scripts are UTF-8;
- gold files are UTF-8;
- canonical writers emit LF where specified;
- CRLF compatibility does not change semantic comparison;
- Unicode distinctions significant to the language are preserved;
- no BOM appears where prohibited.

Encoding failure in a required asset is `ERROR`.

---

# 85. File-naming compliance

Active assets MUST follow `FILE_NAMING_CONVENTIONS.md`.

Release review includes:

```text
GF module/file match
scenario ID/script stem match
gold/scenario stem match
canonical project document names
canonical report names
safe run paths
no Windows reserved names
no case-only collision
no active _v2, new, old, final or latest suffixes
```

A noncanonical imported source filename may be accepted only when preserving upstream identity is intentional and the project contract documents it.

---

# 86. Performance criteria

Performance is release-gating only when project policy defines thresholds.

Possible criteria:

```text
maximum compile duration
maximum scenario duration
maximum PGF size
maximum scenario output size
maximum memory use
```

Thresholds must be:

- documented;
- measured consistently;
- platform-aware;
- treated as warnings or gates explicitly.

A timeout always remains an execution error, regardless of performance policy.

---

# 87. Compatibility criteria

Release compatibility review includes:

```text
supported GF version
supported RGL revision
supported platform
supported Python/GF Wordbench version for validation
project schema compatibility
scenario/gold normalization compatibility
public GF contract compatibility
PGF consumer compatibility
```

Do not claim compatibility that has not been tested or documented.

---

# 88. Downstream-consumer review

When the project exposes modules or PGF behavior to external consumers, release review SHOULD include:

```text
consumer compile
consumer load
API entrypoint use
PGF smoke test
migration note
```

Internal project success may be insufficient when external consumers depend on a public contract.

Consumer identities and guarantees belong in the project contract lock.

---

# 89. Release gate matrix

The release owner SHOULD maintain a completed matrix for each candidate.

| Gate | Required evidence | Result |
|---|---|---|
| Candidate identity | source revision and hashes | |
| Source integrity | inventory and fingerprints | |
| Project configuration | schema/config check | |
| Toolchain | GF version and path evidence | |
| Contracts | project contract check | |
| Dependencies | dependency review | |
| Scan policy | scan results | |
| Checkpoints | compile results | |
| Entrypoints | compile results | |
| PGF | build and artifact verification | |
| Scenarios | required scenario results | |
| Markers/assertions | section results | |
| Gold | exact comparisons | |
| Coverage | coverage matrix review | |
| Known issues | ledger review | |
| Documentation | consistency review | |
| Artifacts | manifest verification | |
| Reports | summary/finalization check | |
| Determinism | repeatability evidence | |
| Security | security checklist | |
| Version | release/change record | |
| Approval | approval and rollback | |

Blank results mean `PENDING`, not pass.

---

# 90. Compact normal-release checklist

```text
[ ] Candidate source revision recorded
[ ] Working tree clean or fully inventoried
[ ] project.toml validates
[ ] Project identity consistent
[ ] GF executable and version supported
[ ] Effective GF path recorded
[ ] Project contract check passes
[ ] Dependency map agrees with source
[ ] Required scan policy passes
[ ] All required checkpoints are OK
[ ] All release entrypoints are OK
[ ] Required PGF builds and verifies
[ ] All required scenarios are OK
[ ] Required markers and assertions complete
[ ] Every required gold matches
[ ] Coverage supports release claims
[ ] No release-blocking status entry
[ ] Known issues reviewed
[ ] Documentation matches candidate
[ ] Required artifacts exist
[ ] Manifest validates
[ ] summary.json validates
[ ] overall_status is OK
[ ] No security blocker
[ ] Version and release notes complete
[ ] Approval recorded
[ ] Rollback reference recorded
```

---

# 91. Extended evidence checklist

```text
[ ] Run ID recorded
[ ] Run started and finished timestamps valid
[ ] GF Wordbench producer version recorded
[ ] GF version raw evidence retained
[ ] Source fingerprints retained
[ ] Compile commands retained
[ ] Compile stdout retained
[ ] Compile stderr retained
[ ] Scenario commands retained
[ ] Scenario stdout retained
[ ] Scenario stderr retained
[ ] Normalized outputs retained
[ ] Gold paths retained
[ ] Gold match values true where required
[ ] PGF size recorded
[ ] PGF hash recorded
[ ] Manifest hashes verified
[ ] Previous-run diff reviewed
[ ] Top errors reviewed
[ ] Waivers attached
[ ] Manual reviews attached
```

---

# 92. Release reviewer questions

Reviewers SHOULD ask:

```text
Is this the exact source being released?
Does project.toml identify one active language?
Are all entrypoints and checkpoints real and current?
Did every required lower checkpoint pass?
Did every release entrypoint compile from clean artifacts?
Was the PGF built by this run?
Did every required scenario load the intended entrypoint?
Did every required section complete?
Did every required gold match?
Were gold changes intentional and reviewed?
Does coverage support the release claims?
Are temporary implementations visible?
Are known issues truly non-blocking?
Do docs match source?
Does the manifest verify every required artifact?
Did summary finalization complete?
Can another maintainer reproduce the result?
Is rollback possible?
```

---

# 93. Release decision template

```text
Release candidate:
Project ID:
Release version or label:
Source revision:
GF Wordbench version:
GF version:
Release run ID:

Gate result:
- Candidate identity:
- Source integrity:
- Project configuration:
- Toolchain:
- Contracts:
- Dependencies:
- Scan:
- Checkpoints:
- Entrypoints:
- PGF:
- Required scenarios:
- Markers/assertions:
- Gold:
- Coverage:
- Known issues:
- Documentation:
- Artifacts:
- Reports:
- Repeatability:
- Security:
- Versioning:
- Rollback:

Waivers:
Accepted issues:
Decision:
Approver:
Date:
Notes:
```

Every blank item remains pending.

---

# 94. Release-blocker template

```text
Blocker ID:
Candidate:
Gate:
Subject:
Observed result:
Expected result:
Evidence:
Owner:
Required action:
Retest scope:
Status:
Resolution:
Resolved in run:
```

Blocker IDs must be stable within the project’s tracking system.

---

# 95. Accepted-issue template

```text
Issue ID:
Candidate:
Affected scope:
Observed behavior:
Expected limitation:
Why non-blocking:
Validation evidence:
User impact:
Workaround:
Owner:
Approval:
Follow-up:
```

---

# 96. Repeatability record template

```text
Candidate:
First release run:
Second release run:
Source revision:
Project configuration hash:
GF executable:
GF version:
RGL revision:
Status comparison:
Gold comparison:
Artifact-name comparison:
PGF comparison:
Allowed differences:
Decision:
Reviewer:
```

---

# 97. Release evidence preservation

After approval:

- make the run directory read-only where practical;
- preserve summary and manifest;
- preserve required raw evidence;
- preserve PGF and package artifacts;
- preserve release notes;
- preserve source tag/revision;
- preserve approval record;
- preserve waivers and accepted issues.

Do not mutate approved evidence in place.

Corrections require a new release candidate or a clearly versioned metadata addendum.

---

# 98. Release criteria changes

Changing this document may itself change project release semantics.

Classification:

## 98.1 Clarification

No criterion meaning changes.

Action:

- update wording;
- review consistency;
- no project release-version change necessarily required.

## 98.2 Compatible tightening

Adds evidence or a compatible gate without invalidating previously valid project contracts unexpectedly.

Action:

- update validation spec;
- update project lock if contract changes;
- update tests;
- document effective release.

## 98.3 Breaking release-policy change

Changes required scenarios, required artifacts, release entrypoints, PGF requirements, status semantics, or accepted output meaning.

Action:

- identify affected project contract IDs;
- update project configuration;
- update scenarios/golds;
- add migration;
- update project contract version;
- record decision;
- rerun release validation.

Release criteria MUST NOT change silently between candidate run and approval.

---

# 99. Drift indicators

Probable release-policy drift exists when:

- a required scenario is absent from configuration;
- configuration and validation spec disagree;
- an entrypoint compiles but a lower checkpoint is omitted;
- a scenario loads a different module;
- a gold exists without a registered scenario;
- a required scenario has no gold or assertion policy;
- gold changes without source/specification reason;
- expected PGF name differs across files;
- a status-ledger blocker is ignored;
- docs name modules that no longer exist;
- active files reference an old language suffix;
- source-adjacent stale `.gfo` supports a build;
- `summary.json` reports `OK` despite required `ERROR`;
- manifest omits the PGF;
- optional results are hidden;
- a release is approved from a checkpoint run rather than release evidence;
- source changes after the release run;
- a waiver changes machine result fields;
- approval lacks rollback.

Every drift indicator must be resolved before approval.

---

# 100. Automated release checks

GF Wordbench SHOULD eventually automate:

```text
project configuration validation
required document existence
placeholder scan
old-identifier scan
module/file-name consistency
entrypoint/checkpoint registry
scenario registry
scenario-to-entrypoint mapping
scenario-to-gold mapping
gold schema validation
status-ledger blocker detection
checkpoint compilation
entrypoint compilation
PGF verification
required scenario execution
summary invariant validation
manifest hash validation
release version check
```

Automation does not remove the need for linguistic and approval review.

---

# 101. Test requirements for this release policy

Framework/project test suites SHOULD cover:

```text
required checkpoint failure blocks release
required checkpoint skip blocks release
entrypoint success cannot override checkpoint failure
required scenario failure blocks release
optional scenario remains visible
missing required scenario blocks release
missing required gold blocks release
gold mismatch blocks release
missing marker blocks release
PGF absence blocks release
stale artifact blocks release
manifest mismatch blocks release
summary finalization error blocks release
overall_status ERROR blocks release
ledger blocker blocks release
waiver cannot alter result status
post-run source change invalidates candidate
old identifier blocks release
unresolved placeholder blocks release
```

---

# 102. Release-policy ownership

| Area | Owner |
|---|---|
| Project identity | project maintainer |
| GF module contracts | provider and project architecture owner |
| Validation specification | validation owner |
| Scenario content | scenario owner |
| Gold acceptance | linguistic/project reviewer |
| GF toolchain | toolchain owner |
| PGF artifact | release artifact owner |
| Status ledger | subsystem owners and release owner |
| Documentation | document owners |
| Release decision | release approver |
| Rollback | release owner |
| Framework execution semantics | GF Wordbench maintainers |

No single automated status replaces owner review of linguistic and contract claims.

---

# 103. Definition of release-ready

The active project is release-ready when:

1. the candidate identity is complete and immutable;
2. project configuration validates;
3. all release-required project contracts are active and satisfied;
4. dependency direction is valid;
5. source scan policy passes;
6. every required checkpoint is `OK`;
7. every release entrypoint is `OK`;
8. the required PGF is current, non-empty, and verified;
9. every required scenario is `OK`;
10. every required marker and assertion completes;
11. every required gold comparison is true;
12. coverage supports the declared release scope;
13. no release-blocking issue or ledger entry remains;
14. project documentation agrees with source and configuration;
15. required artifacts and hashes verify;
16. `summary.json` and `manifest.json` validate;
17. `overall_status = OK`;
18. repeatability is established to the required confidence;
19. no security blocker remains;
20. release version, notes, approval, and rollback are recorded.

---

# 104. Definition of release-approved

A release-ready candidate becomes release-approved only when:

1. the release gate matrix is complete;
2. every non-waived mandatory gate passes;
3. every waiver is valid and permitted;
4. accepted issues are explicit;
5. the approver records `APPROVED`;
6. the approved run and artifacts are identified;
7. rollback reference is verified;
8. no invalidating change occurs afterward.

---

# 105. Definition of release-published

A release-approved candidate becomes release-published when:

1. the approved source revision is tagged or otherwise identified;
2. intended artifacts are distributed;
3. published hashes match approved hashes;
4. release notes are available;
5. post-release smoke verification passes;
6. rollback remains available.

Publication does not retroactively repair missing approval evidence.

---

# 106. Final invariants

The project release process MUST preserve:

1. one active project identity;
2. one exact release candidate;
3. authoritative project configuration;
4. current project contracts;
5. checkpoint-before-entrypoint validation;
6. all required scenarios passing;
7. required marker completion;
8. reviewed gold equality;
9. current PGF provenance;
10. clean or isolated release artifacts;
11. separate raw stdout and stderr;
12. explicit timeouts and execution states;
13. valid source fingerprints;
14. no stale generated evidence;
15. complete summary and manifest;
16. `overall_status = OK`;
17. visible optional failures;
18. visible known issues and temporary states;
19. documentation-source agreement;
20. explicit waivers only where permitted;
21. explicit approval;
22. rollback readiness;
23. immutable approved evidence;
24. no release claim beyond proven coverage.

---

# 107. Final rule

> Release the evidence-backed project, not the hoped-for project.

A GF project is release-ready only when its configured checkpoints, entrypoints, scenarios, golds, PGF, contracts, documentation, and artifacts all describe and validate the same source state.

Any unexplained mismatch means the release decision is not yet complete.
