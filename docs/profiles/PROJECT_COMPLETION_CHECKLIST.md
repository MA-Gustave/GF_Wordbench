# GF Wordbench — Project Completion Checklist

**Document ID:** `GF-WB-PROJECT-COMPLETION-CHECKLIST`  
**Status:** Normative  
**Applies to:** One active GF language project managed by GF Wordbench  
**Owner:** GF Wordbench maintainers and the active project owner  
**Checklist version:** `1.1.0`  
**Canonical path:** `docs/projects/PROJECT_COMPLETION_CHECKLIST.md`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Product-boundary authority:** `docs/architecture/PRODUCT_BOUNDARIES.md` and ADR-0001, ADR-0011, ADR-0012  
**Last structural review:** 2026-07-24

---

## 1. Purpose

This checklist defines the evidence required before an active GF language project may be described as:

- initialized;
- structurally complete;
- validation-complete;
- release-ready;
- released;
- safely transferable or clonable.

It is the project-level conformance gate that connects:

- project identity;
- GF source architecture;
- interfile contracts;
- configuration;
- checkpoints;
- entrypoints;
- scenarios;
- assertions;
- gold files;
- generated artifacts;
- diagnostics;
- documentation;
- known issues;
- release evidence.

The central rule is:

> A project is complete only when every required promise is satisfied, validated, documented, and supported by current evidence.

A successful compile of one entrypoint is necessary evidence in many projects, but it is not sufficient proof of project completion.

---

## 2. Scope

This checklist applies to:

```text
project/
project/project.toml
project GF source files
project/docs/
project/validation/
project release artifacts
the GF Wordbench release run
```

It applies when:

- creating a project from `templates/project/`;
- resetting a cloned GF Wordbench copy;
- migrating an existing GF language project;
- replacing one active language project with another;
- declaring a development milestone complete;
- preparing a release candidate;
- recording a release;
- handing the project to another maintainer.

---

## 3. Non-scope

This checklist does not:

- define GF syntax or semantics;
- replace the project validation specification;
- replace the project interfile contract lock;
- define framework code conformance;
- approve linguistic claims unsupported by evidence;
- authorize automatic gold acceptance;
- require every optional GF feature;
- require every RGL category when the project scope explicitly excludes it;
- turn undocumented omissions into acceptable non-applicability;
- replace legal, licensing, or publication review;
- aggregate several Wordbench workspaces;
- define `gf-portfolio` storage, registry, comparison, or orchestration rules.

Framework code conformance is governed separately by framework architecture, development, validation, and release documents.

---

## 4. Related normative documents

Framework-level owners:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_MODES.md
docs/validation/RELEASE_GATES.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/reports/AI_READY_REFERENCE.md
docs/release/RELEASE_PROCESS.md
```

Active-project owners:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/RESEARCH_EVIDENCE.md
```

When this checklist and a specialized normative document overlap, the specialized document owns the detailed rule.

This checklist owns the conformance proof that all required documents and evidence agree.

---

## 5. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **COMPLETE**: every in-scope project promise is satisfied or explicitly resolved.
- **RELEASE-READY**: complete and passing every mandatory release gate.
- **RELEASED**: release-ready evidence has been reviewed and the intended release has been published or recorded.
- **BLOCKER**: unresolved condition preventing completion or release.
- **EXCEPTION**: approved temporary deviation with owner, reason, risk, expiry, and evidence.
- **NOT APPLICABLE**: criterion outside the declared project scope and justified in writing.
- **EVIDENCE**: current file, test, run result, artifact, review record, or decision supporting a checklist item.
- **BASELINE RUN**: accepted validation run used as the first regression reference.
- **RELEASE RUN**: clean validation run used to support one release decision.
- **CURRENT EVIDENCE**: evidence produced from the source, configuration, tools, and expectations being released.
- **SIGN-OFF**: explicit approval by the designated project owner or reviewer.

---

# 6. Completion states

A project must use one of the following states.

## 6.1 `not_initialized`

The project template has not been fully instantiated.

Typical indicators:

- unresolved placeholders;
- missing project identity;
- old language names remain;
- no baseline configuration;
- no authoritative entrypoint.

## 6.2 `in_development`

The project is initialized but one or more required contracts remain incomplete.

This is the normal working state.

## 6.3 `checkpoint_complete`

One declared project checkpoint and its dependencies satisfy their checkpoint criteria.

This does not imply full project completion.

## 6.4 `structurally_complete`

All declared project components, entrypoints, contracts, and required documentation exist.

Validation may still fail.

## 6.5 `validation_complete`

All required validation capabilities exist and can execute.

Some release criteria may still fail.

## 6.6 `complete_not_release_ready`

The declared project scope is complete and documented, but one or more release blockers remain.

Examples:

- required source and project contracts complete, but required PGF not built;
- required scenario mismatch;
- unsupported GF version;
- unresolved release-blocking known issue.

## 6.7 `release_ready`

Every mandatory release gate passes using current evidence.

## 6.8 `released`

A release-ready state has been signed off and recorded with immutable or archived evidence.

## 6.9 State ownership

The current state must be recorded in:

```text
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
```

Release readiness must also be recorded in:

```text
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

A UI label or console message is not the authoritative project state.

---

# 7. Checklist result vocabulary

Each checklist item must use one status:

```text
PASS
FAIL
BLOCKED
NOT_APPLICABLE
NOT_REVIEWED
```

## 7.1 `PASS`

The item is satisfied and current evidence is recorded.

## 7.2 `FAIL`

The item was evaluated and is not satisfied.

## 7.3 `BLOCKED`

The item cannot currently be evaluated or completed because a named prerequisite is unresolved.

## 7.4 `NOT_APPLICABLE`

The item is outside the declared project scope.

It requires:

```text
reason
scope reference
approver
date
impact review
```

## 7.5 `NOT_REVIEWED`

The item has not yet been evaluated.

It cannot be treated as passing.

## 7.6 No blank completion

An unchecked or blank item means `NOT_REVIEWED`.

Silence never means approval.

---

# 8. Evidence requirements

Every `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE` decision must be traceable.

Recommended evidence record:

```text
item_id
status
evidence
reviewer
reviewed_at
notes
exception_id when applicable
```

Accepted evidence examples:

- project-relative file path;
- contract ID;
- scenario ID;
- gold file;
- test name;
- run ID;
- summary path;
- artifact role;
- manifest entry;
- decision-log entry;
- known-issue ID;
- status-ledger entry;
- manual review record.

Unacceptable evidence:

- “seems correct”;
- console output that was not saved;
- an old run from different source;
- an artifact whose producer cannot be identified;
- a missing warning;
- a successful process with a missing required artifact;
- a gold file updated only to remove a failure;
- AI-generated conclusions without project review.

---

# 9. Completion-gate summary

A project is `release_ready` only when all mandatory gate groups pass.

| Gate | Mandatory for structural completion | Mandatory for release |
|---|---:|---:|
| Project identity | Yes | Yes |
| Clone/reset hygiene | Yes | Yes |
| Project configuration | Yes | Yes |
| Source inventory | Yes | Yes |
| Architecture and ownership | Yes | Yes |
| Interfile contracts | Yes | Yes |
| Checkpoint compilation | As declared | Yes |
| Release entrypoint compilation | Yes | Yes |
| Required scenarios | Available | Yes |
| Required assertions | Available | Yes |
| Required gold files | Present | Match |
| Required PGF | Declared when applicable | Built and verified |
| Diagnostics and evidence | Available | Complete |
| Known issues and ledger | Current | No unapproved blocker |
| Documentation | Complete | Current |
| Tests | Present | Pass |
| Clean release run | No | Yes |
| Manifest and reports | No | Yes |
| Sign-off | No | Yes |

A project-specific `RELEASE_CRITERIA.md` may add stricter gates.

It must not weaken mandatory framework integrity, security, evidence, or schema gates.

---

# 10. Gate A — Project identity

## 10.1 Authoritative identity

```text
[ ] A-001 `project/project.toml` exists.
[ ] A-002 The project configuration schema is supported.
[ ] A-003 Project ID is explicit and stable.
[ ] A-004 Display name is explicit.
[ ] A-005 Language name is explicit.
[ ] A-006 Language code is explicit when the project uses one.
[ ] A-007 Module suffix or naming convention is explicit.
[ ] A-008 Source root is explicit.
[ ] A-009 Entrypoints are explicit.
[ ] A-010 Checkpoints are explicit.
[ ] A-011 Required scenarios are explicit.
[ ] A-012 Optional scenarios are explicit.
[ ] A-013 Release targets are explicit.
[ ] A-014 Expected PGF identity is explicit when applicable.
[ ] A-015 Exactly one active language project is represented in the workspace.
```

## 10.2 Identity agreement

```text
[ ] A-016 README identity matches `project.toml`.
[ ] A-017 Language documentation matches `project.toml`.
[ ] A-018 GF module naming matches the configured suffix or convention.
[ ] A-019 Scenario module names match current project identity.
[ ] A-020 Gold headers match current scenario IDs.
[ ] A-021 Expected artifact names match configuration.
[ ] A-022 Release documentation uses the same project version and identity.
```

## 10.3 Identity blockers

Release is blocked when:

- project identity is inferred from old output;
- GUI state is the only identity source;
- more than one active project identity is configured in the workspace;
- project and entrypoint names disagree;
- the expected PGF name is ambiguous.

---

# 11. Gate B — Clone and reset hygiene

This gate is mandatory when the project was created by cloning, resetting, or migrating another language project.

```text
[ ] B-001 Previous language names are absent from active project paths.
[ ] B-002 Previous language names are absent from active GF module names.
[ ] B-003 Previous language suffixes are absent from active GF imports.
[ ] B-004 Previous language names are absent from scenario scripts.
[ ] B-005 Previous language names are absent from validation inputs.
[ ] B-006 Previous language names are absent from gold files.
[ ] B-007 Previous language names are absent from active project documentation.
[ ] B-008 Previous release artifact names are absent.
[ ] B-009 Previous project IDs are absent from configuration.
[ ] B-010 Old run output is not used as active configuration.
[ ] B-011 Old generated `.gfo` and `.pgf` files cannot mask current builds.
[ ] B-012 Template placeholders have been replaced.
[ ] B-013 Non-applicable template examples have been removed or marked examples.
[ ] B-014 The project interfile lock is active-project content, not an unresolved template.
[ ] B-015 A project-wide stale-identifier scan passes.
```

Permitted historical references:

- migration notes;
- decision records;
- provenance;
- acknowledged source ancestry.

Historical references must be clearly identified as history rather than active identity.

---

# 12. Gate C — Required project structure

## 12.1 Root assets

```text
[ ] C-001 `project/README.md` exists.
[ ] C-002 `project/project.toml` exists.
[ ] C-003 Configured source root exists.
[ ] C-004 `project/docs/` exists.
[ ] C-005 `project/validation/` exists.
[ ] C-006 `project/validation/scenarios/` exists.
[ ] C-007 `project/validation/gold/` exists.
[ ] C-008 `project/validation/inputs/` exists.
```

## 12.2 Required project documents

```text
[ ] C-009 `project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md` exists.
[ ] C-010 `project/docs/INTERFILE_CONTRACT_LOCK.md` exists.
[ ] C-011 `project/docs/LANGUAGE_OVERVIEW.md` exists.
[ ] C-012 `project/docs/LANGUAGE_ARCHITECTURE.md` exists.
[ ] C-013 `project/docs/MODULE_DEPENDENCY_MAP.md` exists.
[ ] C-014 `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md` exists.
[ ] C-015 `project/docs/MORPHOLOGY_SPEC.md` exists.
[ ] C-016 `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` exists.
[ ] C-017 `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md` exists.
[ ] C-018 `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md` exists.
[ ] C-019 `project/docs/STATUS_LEDGER__PROJECT_DOCS.md` exists.
[ ] C-020 `project/docs/DECISION_LOG.md` exists.
[ ] C-021 `project/docs/KNOWN_ISSUES.md` exists.
[ ] C-022 `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` exists.
[ ] C-023 `project/docs/RESEARCH_EVIDENCE.md` exists.
```

## 12.3 Validation documentation

```text
[ ] C-024 `project/validation/README.md` exists.
[ ] C-025 `project/validation/scenarios/README.md` exists.
[ ] C-026 `project/validation/gold/README.md` exists.
[ ] C-027 `project/validation/inputs/README.md` exists.
```

## 12.4 Structure integrity

```text
[ ] C-028 Required paths match project configuration.
[ ] C-029 No required project file is stored only outside the project boundary.
[ ] C-030 Generated run artifacts are separated from project source assets.
[ ] C-031 Temporary files are excluded by documented policy.
[ ] C-032 Source cleanup cannot delete reviewed project assets.
[ ] C-033 Template and active-project required structures are compatible.
```

---

# 13. Gate D — Project configuration

## 13.1 Configuration validity

```text
[ ] D-001 TOML parses successfully.
[ ] D-002 `schema_id` is correct.
[ ] D-003 `schema_version` is supported.
[ ] D-004 Required tables exist.
[ ] D-005 Required fields have correct types.
[ ] D-006 Unknown fields follow compatibility policy.
[ ] D-007 Duplicate semantic definitions are absent.
[ ] D-008 Project-relative paths remain inside the project root.
[ ] D-009 Machine-local environment paths are not hard-coded as project truth.
[ ] D-010 Secrets are absent.
```

## 13.2 Source configuration

```text
[ ] D-011 Source root exists.
[ ] D-012 Source glob or source inventory is intentional.
[ ] D-013 Include rules are documented.
[ ] D-014 Exclude rules are documented.
[ ] D-015 Excluded required modules are prohibited.
[ ] D-016 Generated directories are excluded from source discovery.
[ ] D-017 Target module names match actual GF module declarations.
```

## 13.3 Validation configuration

```text
[ ] D-018 Checkpoint IDs are unique.
[ ] D-019 Checkpoint modules exist.
[ ] D-020 Entrypoint IDs are unique.
[ ] D-021 Entrypoint modules exist.
[ ] D-022 Scenario IDs are unique.
[ ] D-023 Scenario paths exist.
[ ] D-024 Requiredness is explicit.
[ ] D-025 Applicable modes are explicit.
[ ] D-026 Timeout policy is finite.
[ ] D-027 Gold paths exist where required.
[ ] D-028 Normalization versions are supported.
[ ] D-029 Artifact roles are known.
[ ] D-030 Release targets reference valid entrypoints.
```

## 13.4 Canonical modes

```text
[ ] D-031 Project policy uses `quick`, `checkpoint`, `release`, and `diagnostic`.
[ ] D-032 Legacy `file` and `all` values are not emitted as canonical project configuration.
[ ] D-033 Mode-specific requiredness is documented.
[ ] D-034 Release-required work cannot be disabled by disposable application state.
```

---

# 14. Gate E — Source inventory and module identity

## 14.1 Inventory

```text
[ ] E-001 Every intended GF source file is inventoried.
[ ] E-002 Every source file has an intended responsibility.
[ ] E-003 Every required configured module exists.
[ ] E-004 Every source filename matches its GF module name.
[ ] E-005 No duplicate active module declaration exists.
[ ] E-006 No stale generated source shadows an active module.
[ ] E-007 Source selection is deterministic.
[ ] E-008 Every exclusion has a reason.
[ ] E-009 No active source is accidentally excluded.
[ ] E-010 No run-output file is selected as source.
```

## 14.2 Module layers

```text
[ ] E-011 Abstract syntax modules are identified.
[ ] E-012 Concrete syntax modules are identified.
[ ] E-013 Resource modules are identified.
[ ] E-014 Interface and instance modules are identified where used.
[ ] E-015 Morphology modules are identified.
[ ] E-016 Paradigm modules are identified.
[ ] E-017 Syntax modules are identified.
[ ] E-018 Structural modules are identified.
[ ] E-019 Lexicon modules are identified.
[ ] E-020 Extension modules are identified.
[ ] E-021 Language entrypoints are identified.
[ ] E-022 API or grammar entrypoints are identified where used.
[ ] E-023 Test-only modules are identified and excluded from release entrypoints.
```

## 14.3 Temporary project elements

```text
[ ] E-024 Placeholder modules are registered in the project ledger.
[ ] E-025 Temporary `oper` definitions are registered.
[ ] E-026 Fallback linearizations are registered.
[ ] E-027 Disabled functions are registered.
[ ] E-028 Incomplete categories are registered.
[ ] E-029 Every temporary item has an owner.
[ ] E-030 Every temporary item has an exit condition.
[ ] E-031 Release-blocking temporary items are unresolved only with an approved exception.
```

---

# 15. Gate F — Language architecture

## 15.1 Architecture document

```text
[ ] F-001 Major module layers are documented.
[ ] F-002 Each layer has one clear responsibility.
[ ] F-003 Entry modules match the current source tree.
[ ] F-004 Current design is separated from historical design.
[ ] F-005 Expected dependency direction is documented.
[ ] F-006 Prohibited dependency direction is documented.
[ ] F-007 Extension boundaries are documented.
[ ] F-008 Generated artifacts and build boundaries are documented.
[ ] F-009 Project-specific deviations from conventional RGL layering are justified.
```

## 15.2 Dependency map

```text
[ ] F-010 Every direct project import is represented.
[ ] F-011 Entrypoint dependency chains are represented.
[ ] F-012 Checkpoint dependency chains are represented.
[ ] F-013 Removed modules are absent.
[ ] F-014 Newly added modules are present.
[ ] F-015 Cycles are intentional and supported, or absent.
[ ] F-016 Test-only dependencies are distinguished.
[ ] F-017 External RGL dependencies are identified at the appropriate level.
[ ] F-018 The map and project interfile lock agree.
[ ] F-019 The map and actual source imports agree.
```

## 15.3 Ownership

```text
[ ] F-020 Every public responsibility has one authoritative provider.
[ ] F-021 Duplicate helper ownership is absent or explicitly selected.
[ ] F-022 Morphology ownership is explicit.
[ ] F-023 Paradigm ownership is explicit.
[ ] F-024 Lincat ownership is explicit.
[ ] F-025 Structural-entry ownership is explicit.
[ ] F-026 Extension-family ownership is explicit.
[ ] F-027 Release-entrypoint ownership is explicit.
```

---

# 16. Gate G — Interfile contracts

## 16.1 Contract-lock completion

```text
[ ] G-001 No required placeholder remains in the active contract lock.
[ ] G-002 Project identity section is complete.
[ ] G-003 Contract statuses use approved values.
[ ] G-004 Every active provider has identified consumers.
[ ] G-005 Every active consumer depends only on documented promises.
[ ] G-006 Every contract has a stable ID.
[ ] G-007 Retired IDs are not reused.
[ ] G-008 Every contract identifies validation evidence.
[ ] G-009 Every contract identifies its documentation owner.
[ ] G-010 Every contract has a current review date or release.
```

## 16.2 Required relationship families

```text
[ ] G-011 Project configuration → source tree is locked.
[ ] G-012 Project identity → module naming is locked.
[ ] G-013 Abstract → concrete relationships are locked.
[ ] G-014 Category provider → consumer relationships are locked.
[ ] G-015 Morphology → paradigms relationships are locked.
[ ] G-016 Paradigms → lexicon relationships are locked.
[ ] G-017 Structural modules → entrypoints relationships are locked.
[ ] G-018 Extension providers → coordinator relationships are locked.
[ ] G-019 Interface → instance relationships are locked where applicable.
[ ] G-020 Entrypoint → PGF relationship is locked.
[ ] G-021 Scenario registry → scenario files is locked.
[ ] G-022 Scenario → entrypoint relationships are locked.
[ ] G-023 Scenario → input relationships are locked where applicable.
[ ] G-024 Scenario → marker protocol is locked.
[ ] G-025 Scenario → gold relationships are locked.
[ ] G-026 Source → `.gfo` relationship is locked.
[ ] G-027 Entrypoint → `.pgf` relationship is locked.
[ ] G-028 Validation → evidence relationship is locked.
[ ] G-029 Documentation → source and behavior relationships are locked.
[ ] G-030 Known issues → release decision relationship is locked.
```

## 16.3 Contract consistency

```text
[ ] G-031 Public GF types match documented contracts.
[ ] G-032 Lincat records match consumer assumptions.
[ ] G-033 Constructor arity matches all callers.
[ ] G-034 Public `oper` types match all consumers.
[ ] G-035 Ordering contracts match source behavior.
[ ] G-036 Side effects and artifacts match documentation.
[ ] G-037 Failure behavior matches validation expectations.
[ ] G-038 No isolated contract-changing edit remains uncoordinated.
```

---

# 17. Gate H — Categories and lincats

This gate applies to all categories declared in project scope.

## 17.1 Category inventory

```text
[ ] H-001 Every in-scope abstract category is inventoried.
[ ] H-002 Every category has an authoritative owner.
[ ] H-003 Every category has a documented lincat.
[ ] H-004 Every lincat field has documented meaning.
[ ] H-005 Every lincat field has documented producer.
[ ] H-006 Every lincat field has documented consumers.
[ ] H-007 Optional or unused fields are explicit.
[ ] H-008 Temporary fields are registered.
```

## 17.2 Agreement and grammatical features

```text
[ ] H-009 Person representation is documented where relevant.
[ ] H-010 Number representation is documented where relevant.
[ ] H-011 Gender representation is documented where relevant.
[ ] H-012 Case representation is documented where relevant.
[ ] H-013 Definiteness representation is documented where relevant.
[ ] H-014 Tense, aspect, mood, or polarity representation is documented where relevant.
[ ] H-015 Agreement propagation is documented.
[ ] H-016 Record-update assumptions are documented.
[ ] H-017 Empty or missing feature behavior is documented.
```

## 17.3 Compatibility

```text
[ ] H-018 Constructors produce every required field.
[ ] H-019 Consumers read only declared fields.
[ ] H-020 Field renames have no stale consumers.
[ ] H-021 Field-type changes have coordinated migrations.
[ ] H-022 Category and lincat documentation matches source.
[ ] H-023 Representative category scenarios exist.
```

A `NOT_APPLICABLE` category requires a scope reference, not an empty table.

---

# 18. Gate I — Morphology and paradigms

## 18.1 Morphology specification

```text
[ ] I-001 In-scope inflectional dimensions are documented.
[ ] I-002 Noun morphology is documented where in scope.
[ ] I-003 Adjective morphology is documented where in scope.
[ ] I-004 Verb morphology is documented where in scope.
[ ] I-005 Pronoun morphology is documented where in scope.
[ ] I-006 Determiner morphology is documented where in scope.
[ ] I-007 Closed-class morphology is documented where in scope.
[ ] I-008 Orthographic alternations are documented.
[ ] I-009 Irregularity strategy is documented.
[ ] I-010 Defective paradigms are documented.
```

## 18.2 Paradigm API

```text
[ ] I-011 Public paradigm constructors are inventoried.
[ ] I-012 Constructor types are documented.
[ ] I-013 Constructor naming is consistent.
[ ] I-014 Regular paradigms have representative tests.
[ ] I-015 Irregular paradigms have representative tests.
[ ] I-016 Unsupported forms fail or degrade according to policy.
[ ] I-017 Temporary paradigm shortcuts are registered.
[ ] I-018 Lexicon entries use approved paradigms.
[ ] I-019 Duplicate paradigm logic is absent or justified.
```

## 18.3 Morphology validation

```text
[ ] I-020 Required morphology checkpoint compiles.
[ ] I-021 Morphology scenarios load the intended module.
[ ] I-022 Representative forms are validated.
[ ] I-023 Empty or missing forms are detected.
[ ] I-024 Unicode and orthographic output is preserved.
[ ] I-025 Gold expectations are reviewed where used.
[ ] I-026 Known morphology gaps are recorded.
```

---

# 19. Gate J — Syntax and constructors

## 19.1 Constructor specification

```text
[ ] J-001 In-scope abstract functions are inventoried.
[ ] J-002 Constructor ownership is documented.
[ ] J-003 Constructor argument order is documented.
[ ] J-004 Linearization strategy is documented.
[ ] J-005 Agreement transfer is documented.
[ ] J-006 Complement behavior is documented.
[ ] J-007 Word-order alternatives are documented.
[ ] J-008 Optional elements are documented.
[ ] J-009 Coordination behavior is documented.
[ ] J-010 Negation and polarity behavior are documented where in scope.
```

## 19.2 Constructor coverage

```text
[ ] J-011 Every required abstract function has a concrete definition.
[ ] J-012 Missing linearizations are absent or explicitly release-accepted.
[ ] J-013 Placeholder strings are absent or registered.
[ ] J-014 Runtime failure placeholders are absent or registered.
[ ] J-015 Constructor return records satisfy lincat contracts.
[ ] J-016 Imported helpers are publicly owned and documented.
[ ] J-017 Unsupported structures fail according to explicit policy.
[ ] J-018 No test-only constructor leaks into the release entrypoint.
```

## 19.3 Syntax validation

```text
[ ] J-019 Required syntax checkpoints compile.
[ ] J-020 Representative linearization scenarios pass.
[ ] J-021 Representative parse scenarios pass where parsing is in scope.
[ ] J-022 Ambiguity behavior is reviewed.
[ ] J-023 Empty linearizations are detected.
[ ] J-024 Required constructor families have coverage.
[ ] J-025 Significant accepted divergences are documented.
```

---

# 20. Gate K — Lexicon and structural inventory

## 20.1 Lexicon policy

```text
[ ] K-001 Lexicon scope is declared.
[ ] K-002 Lexical-entry ownership is documented.
[ ] K-003 Approved paradigm usage is documented.
[ ] K-004 Orthography policy is applied.
[ ] K-005 Duplicate abstract identifiers are absent.
[ ] K-006 Temporary lexical entries are registered.
[ ] K-007 Required lexical categories are represented.
[ ] K-008 Lexicon-specific release criteria are explicit.
```

## 20.2 Structural and closed-class entries

```text
[ ] K-009 Structural-entry inventory is documented.
[ ] K-010 Prepositions preserve required complement behavior.
[ ] K-011 Pronouns preserve required agreement features.
[ ] K-012 Determiners preserve required agreement behavior.
[ ] K-013 Conjunctions preserve coordination behavior.
[ ] K-014 Particles and complementizers are documented.
[ ] K-015 Placeholder structural entries are explicit.
[ ] K-016 Consumers do not reconstruct authoritative structural entries independently.
```

## 20.3 Validation

```text
[ ] K-017 Lexicon module compiles.
[ ] K-018 Structural module compiles.
[ ] K-019 Entrypoints import the intended inventories.
[ ] K-020 Representative lexical scenarios pass.
[ ] K-021 Relevant gold outputs are reviewed.
```

---

# 21. Gate L — Dependency hygiene

```text
[ ] L-001 No lower-level module imports the release language entrypoint.
[ ] L-002 No resource module imports a higher syntax API without an approved contract.
[ ] L-003 No release entrypoint imports test-only modules.
[ ] L-004 Scenarios load documented entrypoints.
[ ] L-005 Scenarios do not load undocumented temporary substitutes.
[ ] L-006 Gold files do not drive source-generation logic.
[ ] L-007 Project configuration does not depend on generated run output.
[ ] L-008 Circular imports are absent or explicitly supported.
[ ] L-009 Duplicate helper definitions are absent or selected by policy.
[ ] L-010 Inheritance and override behavior is documented where used.
[ ] L-011 Local redefinitions of inherited families are justified.
[ ] L-012 Import paths are project- and toolchain-compatible.
[ ] L-013 No developer-only global path is required.
[ ] L-014 Clean-build dependency resolution succeeds.
```

---

# 22. Gate M — Static scanning

## 22.1 Scan execution

```text
[ ] M-001 Every selected release source is scanned under release policy.
[ ] M-002 Scanner version or rule set is recorded.
[ ] M-003 Structured findings are preserved.
[ ] M-004 Scan logs are attributable to source files.
[ ] M-005 Comments and strings are handled according to scanner contracts.
[ ] M-006 Scan failure is distinct from a scan finding.
[ ] M-007 No source file is modified by scanning.
```

## 22.2 Findings review

```text
[ ] M-008 Every blocking finding is resolved.
[ ] M-009 Every accepted finding is documented.
[ ] M-010 Finding severity is explicit.
[ ] M-011 False-positive exceptions have stable rationale.
[ ] M-012 New findings are compared with the baseline.
[ ] M-013 Scan findings are not misreported as GF compile errors.
[ ] M-014 Successful compilation does not erase scan findings.
```

---

# 23. Gate N — Checkpoint compilation

## 23.1 Checkpoint registry

```text
[ ] N-001 Every checkpoint has a stable ID.
[ ] N-002 Every checkpoint identifies one or more GF modules.
[ ] N-003 Checkpoint purpose is documented.
[ ] N-004 Checkpoint dependency order is documented.
[ ] N-005 Checkpoint release requiredness is explicit.
[ ] N-006 Checkpoint scenarios are identified where applicable.
```

## 23.2 Clean compilation

```text
[ ] N-007 Generated artifacts from older runs are isolated or removed.
[ ] N-008 GF executable and version are recorded.
[ ] N-009 GF path is recorded or reproducible.
[ ] N-010 Working directory is recorded.
[ ] N-011 Every required checkpoint process launches.
[ ] N-012 Every required checkpoint avoids timeout.
[ ] N-013 Every required checkpoint exits according to policy.
[ ] N-014 Every required `.gfo` exists when expected.
[ ] N-015 Compile stdout is preserved.
[ ] N-016 Compile stderr is preserved.
[ ] N-017 Diagnostic parsing succeeds or preserves unknown evidence.
[ ] N-018 Direct, downstream, and ambiguous failures are classified.
[ ] N-019 Required checkpoints pass in declared dependency order.
```

## 23.3 Checkpoint completion

A checkpoint is complete only when:

```text
[ ] N-020 Provider module compiles.
[ ] N-021 Direct consumers compile.
[ ] N-022 Relevant downstream entrypoint compiles.
[ ] N-023 Assigned scenarios pass.
[ ] N-024 Assigned gold comparisons pass.
[ ] N-025 Documentation and status ledger reflect the result.
```

---

# 24. Gate O — Release entrypoints

## 24.1 Entrypoint identity

```text
[ ] O-001 Release abstract or grammar entrypoint is explicit.
[ ] O-002 Release concrete language entrypoint is explicit.
[ ] O-003 API or syntax entrypoint is explicit where applicable.
[ ] O-004 Entrypoint module names match files.
[ ] O-005 Entrypoints import every required component.
[ ] O-006 Entrypoints import no test-only component.
[ ] O-007 Entrypoints use no undeclared local path.
```

## 24.2 Entrypoint validation

```text
[ ] O-008 All required checkpoints pass first.
[ ] O-009 Release entrypoints compile from a clean artifact state.
[ ] O-010 Release entrypoints produce expected `.gfo` artifacts.
[ ] O-011 Release entrypoints load in the GF shell.
[ ] O-012 Missing-function inspection satisfies project policy.
[ ] O-013 Required scenarios target the release entrypoint.
[ ] O-014 Entrypoint evidence belongs to the current source fingerprint.
```

A lower-level substitute is not proof that the release entrypoint works.

---

# 25. Gate P — Scenario registry

## 25.1 Registry validity

```text
[ ] P-001 Every required scenario ID is unique.
[ ] P-002 Every optional scenario ID is unique.
[ ] P-003 Every registered scenario maps to exactly one `.gfs` file.
[ ] P-004 Every required `.gfs` file exists.
[ ] P-005 Scenario filenames follow project policy.
[ ] P-006 Every scenario has a documented purpose.
[ ] P-007 Every scenario identifies requiredness.
[ ] P-008 Every scenario identifies applicable modes.
[ ] P-009 Every scenario identifies its entrypoint or target.
[ ] P-010 Every scenario has a finite timeout.
[ ] P-011 Every scenario identifies assertion strategy.
[ ] P-012 Every gold-backed scenario identifies a gold file.
[ ] P-013 Every scenario identifies normalization version.
[ ] P-014 Scenario execution order is deterministic.
```

## 25.2 Scenario source integrity

```text
[ ] P-015 Scenarios are native `.gfs` assets.
[ ] P-016 GF Wordbench does not reinterpret GF command syntax.
[ ] P-017 Scenarios use only supported GF commands.
[ ] P-018 Interactive prompts are prohibited or explicitly handled.
[ ] P-019 Scenarios terminate explicitly where required.
[ ] P-020 Shell escape is absent unless explicitly authorized.
[ ] P-021 Scenario hashes are recorded where required.
[ ] P-022 Normal validation cannot modify scenario files.
```

---

# 26. Gate Q — Markers and assertions

## 26.1 Marker protocol

```text
[ ] Q-001 Marker policy is explicit per scenario.
[ ] Q-002 Expected sections are declared.
[ ] Q-003 Section IDs are valid and unique.
[ ] Q-004 Raw marker syntax is canonical.
[ ] Q-005 Marker stream is stdout.
[ ] Q-006 Marker matching uses exact full lines.
[ ] Q-007 Scenario IDs in markers match the active scenario.
[ ] Q-008 Sections appear in deterministic order.
[ ] Q-009 Nested sections are absent.
[ ] Q-010 Duplicate sections are absent.
[ ] Q-011 Every required begin marker has a matching end marker.
[ ] Q-012 Unexpected or malformed reserved markers fail.
```

## 26.2 Assertions

```text
[ ] Q-013 Assertion IDs are unique.
[ ] Q-014 Assertion types are supported.
[ ] Q-015 Sources and scopes are valid.
[ ] Q-016 Expected values are explicit.
[ ] Q-017 Required assertions are explicit.
[ ] Q-018 Advisory assertions are justified.
[ ] Q-019 Unknown assertion types cannot pass.
[ ] Q-020 Process success is not the sole success criterion.
[ ] Q-021 Fatal diagnostics remain visible.
[ ] Q-022 Required section completion is asserted.
[ ] Q-023 Required artifacts are asserted.
[ ] Q-024 Required gold comparison is asserted.
[ ] Q-025 Assertion evidence is traceable.
[ ] Q-026 Required skipped assertions affect scenario status.
```

## 26.3 Release result

```text
[ ] Q-027 Every required scenario process launches.
[ ] Q-028 Every required scenario avoids timeout.
[ ] Q-029 Every required marker protocol is valid.
[ ] Q-030 Every required section completes.
[ ] Q-031 Every required assertion passes.
[ ] Q-032 Optional assertion failures remain visible.
```

---

# 27. Gate R — Validation inputs

```text
[ ] R-001 Every external input file is registered.
[ ] R-002 Input ownership is documented.
[ ] R-003 Input encoding is documented.
[ ] R-004 Input format is documented.
[ ] R-005 Input line or record meaning is documented.
[ ] R-006 Input order semantics are documented.
[ ] R-007 Scenario and input versions are compatible.
[ ] R-008 Required inputs exist.
[ ] R-009 Reviewed canonical inputs are version-controlled.
[ ] R-010 Generated temporary inputs do not replace canonical release inputs.
[ ] R-011 Sensitive input data is absent or governed.
[ ] R-012 Input changes trigger scenario and gold review.
```

---

# 28. Gate S — Output normalization

```text
[ ] S-001 Normalization profile is identified.
[ ] S-002 Normalization version is explicit.
[ ] S-003 Raw output is captured before normalization.
[ ] S-004 Rule order is deterministic.
[ ] S-005 Line-ending normalization is documented.
[ ] S-006 Approved path replacements are documented.
[ ] S-007 Timing or run-ID normalization is documented.
[ ] S-008 ANSI removal is documented.
[ ] S-009 Linguistic Unicode is preserved.
[ ] S-010 Abstract trees are preserved.
[ ] S-011 Linearized strings are preserved.
[ ] S-012 Parse ambiguity evidence is preserved.
[ ] S-013 Missing-function lists are preserved.
[ ] S-014 Morphology output is preserved.
[ ] S-015 Diagnostic meaning is preserved.
[ ] S-016 Marker identity is preserved as normalized section identity.
[ ] S-017 Incomplete sections cannot produce valid normalized output.
[ ] S-018 Normalization cannot turn failure into success.
[ ] S-019 Normalization fixtures pass.
[ ] S-020 Normalization changes trigger gold review.
```

---

# 29. Gate T — Gold files

## 29.1 Gold identity

```text
[ ] T-001 Every required gold-backed scenario has one registered gold file.
[ ] T-002 Gold filename follows scenario identity policy.
[ ] T-003 Gold header uses the supported schema identity.
[ ] T-004 Gold scenario ID matches configuration.
[ ] T-005 Gold normalization version matches the runner.
[ ] T-006 Gold section IDs match expected scenario sections.
[ ] T-007 Gold encoding and newline rules are correct.
[ ] T-008 Required gold files are version-controlled.
```

## 29.2 Gold quality

```text
[ ] T-009 Gold content represents reviewed accepted output.
[ ] T-010 Unstable timestamps are absent.
[ ] T-011 Unstable absolute paths are absent or normalized.
[ ] T-012 Semantically meaningful output is preserved.
[ ] T-013 Empty gold output is explicitly justified.
[ ] T-014 Random or unstable output is not used as exact gold without deterministic projection.
```

## 29.3 Gold release behavior

```text
[ ] T-015 Normal validation is read-only.
[ ] T-016 Missing required gold is a failure.
[ ] T-017 Every required gold comparison executes.
[ ] T-018 Every required gold comparison passes.
[ ] T-019 Mismatch diffs are preserved.
[ ] T-020 No gold was updated merely to make validation pass.
```

## 29.4 Gold update review

For every gold change:

```text
[ ] T-021 Source or specification change is intentional.
[ ] T-022 Old raw output was reviewed.
[ ] T-023 New raw output was reviewed.
[ ] T-024 Linguistic or architectural reason is documented.
[ ] T-025 Scenario still tests its intended contract.
[ ] T-026 Unstable noise did not leak into gold.
[ ] T-027 `VALIDATION_SPEC.md` was reviewed.
[ ] T-028 `DECISION_LOG.md` was updated when significant.
[ ] T-029 Contract lock was updated when the contract changed.
[ ] T-030 Gold was written atomically.
```

---

# 30. Gate U — PGF and generated artifacts

## 30.1 PGF applicability

```text
[ ] U-001 PGF requirement is explicit.
[ ] U-002 `NOT_APPLICABLE` PGF status is justified when no PGF is released.
```

## 30.2 PGF build

When required:

```text
[ ] U-003 PGF entrypoint is explicit.
[ ] U-004 Expected PGF filename is explicit.
[ ] U-005 Output location is explicit.
[ ] U-006 Build command follows the external-tool contract.
[ ] U-007 Build runs from current source state.
[ ] U-008 Stale PGF cannot count as success.
[ ] U-009 Process launches.
[ ] U-010 Process avoids timeout.
[ ] U-011 Exit policy passes.
[ ] U-012 Expected PGF exists.
[ ] U-013 Expected PGF is non-empty.
[ ] U-014 PGF corresponds to the configured entrypoint.
[ ] U-015 Required concrete language is present where verifiable.
[ ] U-016 Required runtime scenarios pass where applicable.
[ ] U-017 PGF is catalogued in the artifact manifest.
[ ] U-018 PGF is tied to the current run and source fingerprint.
```

## 30.3 Other generated artifacts

```text
[ ] U-019 Every required `.gfo` is catalogued or traceable.
[ ] U-020 Every generated release artifact has one owner.
[ ] U-021 Artifact role is stable.
[ ] U-022 Artifact media type is known.
[ ] U-023 Artifact size is recorded.
[ ] U-024 Artifact hash is recorded when policy requires it.
[ ] U-025 Artifact retention policy is documented.
[ ] U-026 Missing required artifacts fail release.
[ ] U-027 Source files are never overwritten by artifact generation.
```

---

# 31. Gate V — Diagnostics and causal classification

## 31.1 Diagnostic evidence

```text
[ ] V-001 GF stdout is preserved.
[ ] V-002 GF stderr is preserved.
[ ] V-003 Exit code is preserved.
[ ] V-004 Execution state is preserved.
[ ] V-005 Duration is preserved.
[ ] V-006 Command or reconstructible command is preserved.
[ ] V-007 Working directory is preserved.
[ ] V-008 GF version is preserved.
[ ] V-009 Required artifact checks are preserved.
[ ] V-010 Unrecognized diagnostics remain visible.
```

## 31.2 Classification

```text
[ ] V-011 Technical error kind is assigned separately from causal class.
[ ] V-012 Direct failures are evidence-based.
[ ] V-013 Downstream failures identify blockers where known.
[ ] V-014 Ambiguous failures remain ambiguous when evidence is insufficient.
[ ] V-015 Processing order alone is not used as proof of directness.
[ ] V-016 Noise and exclusions are explicit.
[ ] V-017 Skipped results are explicit.
[ ] V-018 Root-cause counts are not inflated by downstream failures.
```

## 31.3 Failure semantics

```text
[ ] V-019 Validation `FAIL` is distinct from execution `ERROR`.
[ ] V-020 Timeout is not reported as GF syntax failure.
[ ] V-021 Launch failure is not reported as project failure.
[ ] V-022 Gold mismatch is distinct from process failure.
[ ] V-023 Missing artifact after zero exit is a failure.
[ ] V-024 Cancellation is recorded as execution state.
```

---

# 32. Gate W — Regression comparison

## 32.1 Baseline

```text
[ ] W-001 A compatible baseline run exists or absence is explicitly accepted.
[ ] W-002 Baseline run ID is recorded.
[ ] W-003 Baseline summary schema is supported.
[ ] W-004 Baseline project identity matches.
[ ] W-005 Baseline comparison scope is compatible.
[ ] W-006 Baseline GF-version differences are understood.
```

## 32.2 Comparison

```text
[ ] W-007 Current and previous file identities are stable.
[ ] W-008 Current and previous scenario identities are stable.
[ ] W-009 Source fingerprints are compared.
[ ] W-010 `improved` entries are reviewed.
[ ] W-011 `regressed` entries are reviewed.
[ ] W-012 `new` entries are reviewed.
[ ] W-013 `removed` entries are reviewed.
[ ] W-014 Unchanged failures remain visible where relevant.
[ ] W-015 Current failure status is not hidden by improvement.
[ ] W-016 Missing previous evidence does not fabricate a comparison.
```

## 32.3 Regression release policy

```text
[ ] W-017 Every release-blocking regression is resolved or excepted.
[ ] W-018 Removed validation coverage is justified.
[ ] W-019 New warnings are documented.
[ ] W-020 Gold-output changes are deliberate.
```

---

# 33. Gate X — Test coverage

## 33.1 Coverage matrix

```text
[ ] X-001 Every required category maps to validation evidence.
[ ] X-002 Every required constructor family maps to evidence.
[ ] X-003 Every checkpoint maps to compile evidence.
[ ] X-004 Every entrypoint maps to compile and load evidence.
[ ] X-005 Every required scenario maps to assertions.
[ ] X-006 Every gold file maps to one scenario.
[ ] X-007 Every release criterion maps to executable or manual evidence.
[ ] X-008 Manual criteria identify owner and method.
[ ] X-009 Known untested areas are explicit.
```

## 33.2 Framework tests relevant to the project

```text
[ ] X-010 Configuration validation tests pass.
[ ] X-011 Project-contract tests pass.
[ ] X-012 Source-selection tests pass.
[ ] X-013 Scanner tests pass.
[ ] X-014 Compilation contract tests pass.
[ ] X-015 Diagnostic parsing tests pass.
[ ] X-016 Causal classification tests pass.
[ ] X-017 Scenario marker tests pass.
[ ] X-018 Assertion evaluation tests pass.
[ ] X-019 Normalization tests pass.
[ ] X-020 Gold-comparison tests pass.
[ ] X-021 PGF artifact tests pass where applicable.
[ ] X-022 Report tests pass.
[ ] X-023 Persisted-schema tests pass.
[ ] X-024 Migration tests pass.
```

## 33.3 Real-GF integration

```text
[ ] X-025 GF version probe succeeds.
[ ] X-026 Successful fixture compile succeeds.
[ ] X-027 Failing fixture compile is detected.
[ ] X-028 Scenario load is tested.
[ ] X-029 Parse is tested where in scope.
[ ] X-030 Linearization is tested.
[ ] X-031 Bounded generation is tested where in scope.
[ ] X-032 Timeout containment is tested where practical.
[ ] X-033 PGF build is tested where applicable.
```

---

# 34. Gate Y — Project documentation quality

## 34.1 Accuracy

```text
[ ] Y-001 Documentation describes the current project.
[ ] Y-002 Historical designs are labeled historical.
[ ] Y-003 Module names match source.
[ ] Y-004 Paths match repository structure.
[ ] Y-005 Entrypoints match configuration.
[ ] Y-006 Checkpoints match configuration.
[ ] Y-007 Scenario IDs match configuration.
[ ] Y-008 Gold names match scenario registrations.
[ ] Y-009 Artifact names match release configuration.
[ ] Y-010 Status values match the shared vocabulary.
```

## 34.2 Completeness

```text
[ ] Y-011 Language scope is documented.
[ ] Y-012 Non-goals are documented.
[ ] Y-013 Architecture is documented.
[ ] Y-014 Dependency direction is documented.
[ ] Y-015 Categories and lincats are documented.
[ ] Y-016 Morphology is documented.
[ ] Y-017 Syntax and constructors are documented.
[ ] Y-018 Validation strategy is documented.
[ ] Y-019 Test coverage is documented.
[ ] Y-020 Temporary status is documented.
[ ] Y-021 Known issues are documented.
[ ] Y-022 Release criteria are documented.
[ ] Y-023 Research claims have evidence or are labeled assumptions.
```

## 34.3 Navigation and anti-duplication

```text
[ ] Y-024 Project start document links to authoritative documents.
[ ] Y-025 Each normative rule has one owner.
[ ] Y-026 Other documents link instead of duplicating full rules.
[ ] Y-027 Contradictory acceptance criteria are absent.
[ ] Y-028 Deprecated instructions are removed or clearly marked.
[ ] Y-029 Template guidance is not presented as active project fact.
```

---

# 35. Gate Z — Status ledger and known issues

## 35.1 Status ledger

```text
[ ] Z-001 Every temporary project element is registered.
[ ] Z-002 Every fallback is registered.
[ ] Z-003 Every blocked area is registered.
[ ] Z-004 Every disabled required function is registered.
[ ] Z-005 Every accepted warning family is registered where policy requires.
[ ] Z-006 Every entry has a stable ID.
[ ] Z-007 Every entry has status.
[ ] Z-008 Every entry has owner.
[ ] Z-009 Every entry has impact.
[ ] Z-010 Every entry has next action or exit condition.
[ ] Z-011 Resolved entries retain resolution evidence.
[ ] Z-012 Source comments do not contradict the ledger.
```

## 35.2 Known issues

```text
[ ] Z-013 Every known issue has a stable ID.
[ ] Z-014 Every issue has severity.
[ ] Z-015 Every issue states whether it blocks release.
[ ] Z-016 Every issue has evidence.
[ ] Z-017 Every issue has scope.
[ ] Z-018 Every accepted issue has rationale.
[ ] Z-019 Every accepted release issue has approver.
[ ] Z-020 Undocumented warnings are not silently accepted.
[ ] Z-021 Closed issues identify the validating run or test.
```

## 35.3 Release blockers

```text
[ ] Z-022 No unresolved release-blocking ledger item remains.
[ ] Z-023 No unresolved release-blocking known issue remains.
[ ] Z-024 No expired exception remains.
[ ] Z-025 No required function remains disabled without explicit release policy.
```

---

# 36. Gate AA — Decision and research records

## 36.1 Decision log

```text
[ ] AA-001 Breaking module changes are recorded.
[ ] AA-002 Lincat changes are recorded.
[ ] AA-003 Entrypoint changes are recorded.
[ ] AA-004 Scenario-ID changes are recorded.
[ ] AA-005 Normalization changes are recorded.
[ ] AA-006 Significant gold changes are recorded.
[ ] AA-007 PGF-name changes are recorded.
[ ] AA-008 Dependency-direction exceptions are recorded.
[ ] AA-009 Accepted release exceptions are recorded.
[ ] AA-010 Superseded decisions remain traceable.
```

## 36.2 Research evidence

```text
[ ] AA-011 Linguistic claims identify sources where appropriate.
[ ] AA-012 Source quality is described where relevant.
[ ] AA-013 Conflicting sources are acknowledged.
[ ] AA-014 Project conventions are separated from external linguistic facts.
[ ] AA-015 Unverified assumptions are labeled.
[ ] AA-016 Research-driven design choices link to affected modules.
[ ] AA-017 Research gaps affecting release are identified.
[ ] AA-018 Copyright or data-use restrictions are recorded.
```

No research citation is required for purely internal code organization unless the project claims external linguistic authority.

---

# 37. Gate AB — Security and trust

```text
[ ] AB-001 Project paths are validated for containment.
[ ] AB-002 Scenario paths are validated.
[ ] AB-003 Input paths are validated.
[ ] AB-004 Artifact paths are validated.
[ ] AB-005 Path traversal is rejected.
[ ] AB-006 Project configuration contains no executable Python references.
[ ] AB-007 Arbitrary project Python plugins are absent.
[ ] AB-008 Shell command construction avoids untrusted interpolation.
[ ] AB-009 Scenario shell escape is absent or explicitly authorized.
[ ] AB-010 External processes have finite timeouts.
[ ] AB-011 stdout and stderr are captured separately.
[ ] AB-012 Complete environments are not logged.
[ ] AB-013 Secrets are not persisted.
[ ] AB-014 Reports redact sensitive environment values.
[ ] AB-015 AI-ready evidence is labeled as untrusted data.
[ ] AB-016 Normal validation performs no network upload.
[ ] AB-017 Gold updates require explicit operation.
[ ] AB-018 Persistent writes use safe or atomic behavior where required.
[ ] AB-019 Symlink policy is enforced in strict release mode.
[ ] AB-020 Untrusted projects are not executed without review.
```

---

# 38. Gate AC — Licensing and distribution

```text
[ ] AC-001 Project license status is explicit.
[ ] AC-002 Framework license notice is retained.
[ ] AC-003 Third-party GF/RGL licensing obligations are reviewed.
[ ] AC-004 Third-party source files retain required notices.
[ ] AC-005 Data and lexical sources permit intended use.
[ ] AC-006 Research quotations or extracts comply with applicable terms.
[ ] AC-007 Generated release bundle includes required notices.
[ ] AC-008 No file is distributed under an assumed license.
[ ] AC-009 Proprietary material is not published without authorization.
[ ] AC-010 Release destination matches the approved distribution scope.
```

This checklist is not legal advice.

Ambiguous rights block public distribution until reviewed.

---

# 39. Gate AD — Clean release validation

## 39.1 Release environment

```text
[ ] AD-001 Release source commit or snapshot is identified.
[ ] AD-002 Working tree state is recorded.
[ ] AD-003 Project version is fixed for the release.
[ ] AD-004 GF Wordbench version is recorded.
[ ] AD-005 GF version is recorded.
[ ] AD-006 Operating system and architecture are recorded when relevant.
[ ] AD-007 RGL identity or version is recorded.
[ ] AD-008 Required environment paths resolve.
[ ] AD-009 No developer-only global variable is required.
[ ] AD-010 Release output directory is clean and writable.
```

## 39.2 Clean build

```text
[ ] AD-011 Stale `.gfo` artifacts are isolated.
[ ] AD-012 Stale `.pgf` artifacts are isolated.
[ ] AD-013 Previous run output cannot satisfy current artifact checks.
[ ] AD-014 Project configuration preflight passes.
[ ] AD-015 Toolchain preflight passes.
[ ] AD-016 Required source selection is complete.
[ ] AD-017 Required scans execute.
[ ] AD-018 Required checkpoints compile.
[ ] AD-019 Required entrypoints compile.
[ ] AD-020 Required scenarios execute.
[ ] AD-021 Required assertions pass.
[ ] AD-022 Required gold comparisons pass.
[ ] AD-023 Required PGF builds.
[ ] AD-024 Required artifact verification passes.
[ ] AD-025 Regression policy passes.
[ ] AD-026 Known-issue policy passes.
```

## 39.3 Canonical release mode

```text
[ ] AD-027 Validation ran in canonical `release` mode.
[ ] AD-028 No legacy mode name is emitted.
[ ] AD-029 Required release work was not disabled.
[ ] AD-030 Required skipped work is absent.
[ ] AD-031 Overall run status is `OK`.
```

The exact release command is owned by `docs/usage/CLI_REFERENCE.md`.

This checklist does not invent an alternative command surface.

---

# 40. Gate AE — Release reports and manifest

## 40.1 Structured summary

```text
[ ] AE-001 `summary.json` exists.
[ ] AE-002 Schema ID is correct.
[ ] AE-003 Schema version is supported.
[ ] AE-004 Project identity is correct.
[ ] AE-005 Canonical mode is `release`.
[ ] AE-006 Overall status is `OK`.
[ ] AE-007 File results are complete.
[ ] AE-008 Scenario results are complete.
[ ] AE-009 Artifact results are complete.
[ ] AE-010 Top errors use canonical structure.
[ ] AE-011 Regression entries are present when expected.
```

## 40.2 Human summary

```text
[ ] AE-012 `summary.md` exists.
[ ] AE-013 Required headings exist.
[ ] AE-014 Claims derive from structured results.
[ ] AE-015 Direct, downstream, and ambiguous failures are distinguished.
[ ] AE-016 Scenario outcomes are included.
[ ] AE-017 Artifact paths are included.
```

## 40.3 AI-ready packet

```text
[ ] AE-018 `AI_READY.md` exists.
[ ] AE-019 First heading is `# AI Ready Packet`.
[ ] AE-020 All seven required sections exist.
[ ] AE-021 Empty failure sections are explicit.
[ ] AE-022 Evidence excerpts are bounded.
[ ] AE-023 Every excerpt is attributable.
[ ] AE-024 Evidence is labeled raw, normalized, or derived.
[ ] AE-025 No unsupported diagnosis appears.
[ ] AE-026 No secret appears.
[ ] AE-027 Artifact references are explicit.
```

## 40.4 Manifest

```text
[ ] AE-028 `manifest.json` exists.
[ ] AE-029 Manifest schema is supported.
[ ] AE-030 Every required finalized artifact is listed.
[ ] AE-031 Artifact roles are stable.
[ ] AE-032 Paths are canonical.
[ ] AE-033 Sizes match.
[ ] AE-034 Required hashes match.
[ ] AE-035 Raw evidence entries remain immutable.
[ ] AE-036 Manifest does not hash itself.
[ ] AE-037 Missing required artifact count is zero.
```

---

# 41. Gate AF — Reproducibility

```text
[ ] AF-001 Another supported environment can resolve the documented prerequisites.
[ ] AF-002 Project configuration contains no undocumented machine-local assumption.
[ ] AF-003 GF executable selection is reproducible.
[ ] AF-004 GF path construction is reproducible.
[ ] AF-005 Source selection is reproducible.
[ ] AF-006 Scenario ordering is reproducible.
[ ] AF-007 Normalization is deterministic.
[ ] AF-008 Gold comparison is deterministic.
[ ] AF-009 Artifact naming is deterministic.
[ ] AF-010 Report ordering is deterministic.
[ ] AF-011 Release run can be repeated from a clean state.
[ ] AF-012 Material differences between repeated runs are explained.
```

A byte-identical PGF is not universally required unless the project release policy explicitly requires it.

Validation decisions and evidence identity must nevertheless remain reproducible.

---

# 42. Gate AG — Performance and resource limits

```text
[ ] AG-001 Quick mode remains meaningfully bounded.
[ ] AG-002 Checkpoint mode avoids unrelated work.
[ ] AG-003 Release mode has finite process timeouts.
[ ] AG-004 Diagnostic mode has finite limits.
[ ] AG-005 Generation scenarios are bounded.
[ ] AG-006 Output-size limits are documented.
[ ] AG-007 Truncation is explicit.
[ ] AG-008 Truncation does not permit unsupported success.
[ ] AG-009 No orphan external process remains after cancellation or timeout.
[ ] AG-010 Run directory growth is understood.
[ ] AG-011 Retention policy is documented.
[ ] AG-012 Performance regressions affecting usability are reviewed.
```

---

# 43. Gate AH — Backup, retention, and recovery

```text
[ ] AH-001 Project source is version-controlled or equivalently backed up.
[ ] AH-002 Project configuration is backed up.
[ ] AH-003 Reviewed gold files are backed up.
[ ] AH-004 Project documentation is backed up.
[ ] AH-005 Release evidence is retained according to policy.
[ ] AH-006 Release PGF and required artifacts are retained.
[ ] AH-007 Manifest is retained with the release evidence.
[ ] AH-008 Recovery procedure is documented.
[ ] AH-009 State-file loss does not invalidate the project.
[ ] AH-010 Run-output cleanup does not delete project source assets.
[ ] AH-011 At least one release evidence bundle can be restored and inspected.
```

---

# 44. Gate AI — Handoff readiness

This gate applies before another maintainer takes ownership.

```text
[ ] AI-001 Project start document identifies authoritative entrypoints.
[ ] AI-002 Setup prerequisites are documented.
[ ] AI-003 Project configuration is understandable without private oral context.
[ ] AI-004 Module ownership is documented.
[ ] AI-005 Dependency map is current.
[ ] AI-006 Required checkpoints are documented.
[ ] AI-007 Scenario purposes are documented.
[ ] AI-008 Gold update policy is documented.
[ ] AI-009 Known blockers are explicit.
[ ] AI-010 Temporary project elements are explicit.
[ ] AI-011 Release procedure is documented.
[ ] AI-012 Last accepted release run ID is recorded.
[ ] AI-013 Last accepted artifact manifest is recorded.
[ ] AI-014 Contact or ownership information is recorded where appropriate.
[ ] AI-015 No secret knowledge is required to reproduce validation.
```

---

# 45. Manual linguistic review

Automation cannot prove every linguistic requirement.

The project must list manual review criteria in:

```text
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

For every manual criterion:

```text
[ ] ML-001 Criterion has a stable ID.
[ ] ML-002 Scope is explicit.
[ ] ML-003 Review method is explicit.
[ ] ML-004 Reviewer qualification or role is explicit where relevant.
[ ] ML-005 Sample or corpus is identified.
[ ] ML-006 Expected behavior is explicit.
[ ] ML-007 Actual observation is recorded.
[ ] ML-008 Decision is recorded.
[ ] ML-009 Limitations are recorded.
[ ] ML-010 Evidence location is recorded.
```

Examples of manual review domains:

- grammatical acceptability;
- idiomaticity;
- register;
- orthography;
- dialect choice;
- morphological completeness;
- ambiguity acceptability;
- lexical appropriateness;
- translation equivalence.

A manual criterion may be `NOT_APPLICABLE` only when outside declared project scope.

---

# 46. Exception policy

## 46.1 Exception record

Every exception must define:

```text
exception_id
affected checklist items
reason
risk
scope
owner
approver
created_at
expires_at or exit condition
mitigation
evidence
release impact
```

## 46.2 Prohibited exceptions

An exception must not permit:

- missing authoritative project identity;
- hidden secrets;
- unsafe path traversal;
- unbounded external execution;
- normal validation rewriting gold;
- a missing required artifact reported as success;
- unsupported diagnosis reported as fact;
- contradictory release status;
- unrecorded release-blocking issue;
- falsified evidence;
- a public distribution without confirmed rights.

## 46.3 Expiry

An expired exception is a blocker.

## 46.4 Scope

An exception applies only to its declared release or condition.

It must not become a silent permanent rule.

---

# 47. Completion decision algorithm

Use the following decision order.

```text
1. Are required project identity and structure complete?
   No → not_initialized or in_development.

2. Are all declared source, architecture, and interfile contracts complete?
   No → in_development.

3. Do all required validation mechanisms exist and execute?
   No → structurally_complete or in_development.

4. Are all required checkpoints, entrypoints, scenarios, assertions, golds,
   and artifacts represented?
   No → validation incomplete.

5. Are documentation, ledger, issues, and coverage current?
   No → complete status prohibited.

6. Does a clean release run pass every mandatory gate?
   No → complete_not_release_ready.

7. Are reports, manifest, rights, and sign-off complete?
   No → release_ready status prohibited.

8. Has the approved release been recorded and archived?
   No → release_ready.

9. Yes → released.
```

---

# 48. Minimal structural-completion checklist

The project may be called `structurally_complete` only when:

```text
[ ] Project identity is fixed.
[ ] Clone/reset hygiene passes.
[ ] Required directory structure exists.
[ ] Project configuration validates.
[ ] Required source modules exist.
[ ] Required entrypoints exist.
[ ] Required checkpoints exist.
[ ] Architecture document is current.
[ ] Dependency map is current.
[ ] Category and lincat contract is current.
[ ] Morphology specification is current.
[ ] Syntax and constructor specification is current.
[ ] Interfile contract lock has no unresolved placeholders.
[ ] Validation specification is current.
[ ] Required scenario files exist.
[ ] Required gold files exist.
[ ] Test coverage matrix is current.
[ ] Status ledger is current.
[ ] Known issues are current.
[ ] Release criteria are explicit.
```

Structural completion does not claim that validation passes.

---

# 49. Minimal validation-completion checklist

The project may be called `validation_complete` only when:

```text
[ ] Quick validation is supported.
[ ] Checkpoint validation is supported.
[ ] Release validation is supported.
[ ] Diagnostic validation is supported.
[ ] Project preflight is supported.
[ ] Deterministic file selection is supported.
[ ] Static scan evidence is supported.
[ ] Compile evidence is supported.
[ ] Diagnostic parsing is supported.
[ ] Causal classification is supported.
[ ] Native `.gfs` scenarios are supported.
[ ] Marker validation is supported.
[ ] Assertion validation is supported.
[ ] Versioned normalization is supported.
[ ] Gold comparison is supported.
[ ] PGF verification is supported when applicable.
[ ] Regression comparison is supported.
[ ] Structured summary is supported.
[ ] AI-ready evidence is supported.
[ ] Manifest generation is supported.
```

Validation completion does not claim that the project currently passes.

---

# 50. Minimal release-ready checklist

A project may be called `release_ready` only when:

```text
[ ] Structural completion passes.
[ ] Validation completion passes.
[ ] Clean project configuration preflight passes.
[ ] Supported GF toolchain is used.
[ ] All required source files are selected.
[ ] All blocking scan findings are resolved.
[ ] All required checkpoints compile.
[ ] All required entrypoints compile.
[ ] Missing-function policy passes.
[ ] All required scenarios pass.
[ ] All required marker protocols pass.
[ ] All required assertions pass.
[ ] All required gold comparisons match.
[ ] Required PGF builds and is verified.
[ ] Required artifacts exist.
[ ] No unresolved release-blocking ledger item remains.
[ ] No unresolved release-blocking known issue remains.
[ ] Regression policy passes.
[ ] Manual linguistic criteria pass.
[ ] Documentation is current.
[ ] License and distribution review passes.
[ ] `summary.json` is valid.
[ ] `summary.md` is valid.
[ ] `AI_READY.md` is valid.
[ ] `manifest.json` is valid.
[ ] Overall release run status is `OK`.
[ ] Release evidence is signed off.
```

---

# 51. Release sign-off record

Copy this record into the release evidence or project release document.

```markdown
# Project Completion Sign-off

- Project ID:
- Project display name:
- Language:
- Project version:
- GF Wordbench version:
- GF version:
- RGL identity/version:
- Source commit or snapshot:
- Checklist version:
- Release run ID:
- Release run path:
- Summary JSON:
- Manifest:
- PGF artifact:
- Overall status:
- Completion state:
- Open non-blocking issues:
- Approved exceptions:
- Reviewer:
- Project owner:
- Reviewed at:
- Decision:

## Decision statement

The reviewed project scope is complete and all mandatory release criteria
identified by `PROJECT_COMPLETION_CHECKLIST.md` and
`project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` have been evaluated against the cited
current evidence.

## Signatures or approvals

- Project owner:
- Validation reviewer:
- Linguistic reviewer, when required:
- Release approver:
```

A blank field is not approval.

---

# 52. Completion evidence bundle

The retained release evidence bundle should contain or reference:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
release run summary.json
release run summary.md
release run AI_READY.md
release run manifest.json
raw compile evidence
raw scenario evidence
normalized scenario outputs
gold diffs, when any
generated `.gfo` evidence
release `.pgf`, when applicable
manual review evidence
completion sign-off
```

The bundle may use references rather than duplicate project files.

Every reference must remain resolvable under the retention policy.

---

# 53. Automated conformance checks

`docs/usage/CLI_REFERENCE.md` owns the canonical command and options used to execute project-completion checks.

Automated checks verify, where possible:

- required file existence;
- placeholder absence;
- project configuration schema;
- path containment;
- module-name/file-name agreement;
- configured checkpoint existence;
- entrypoint existence;
- duplicate scenario IDs;
- scenario file existence;
- required gold existence;
- normalization-version compatibility;
- stale language identifiers;
- documentation existence;
- ledger and issue field completeness;
- release-run summary status;
- manifest completeness;
- required artifact existence.

Automated checks report manual criteria separately.

They must not mark manual criteria `PASS` automatically.

---

# 54. Change impact

This checklist must be reviewed when any of the following changes:

- project-scope definition;
- required project document set;
- project configuration schema;
- canonical validation modes;
- status vocabulary;
- scenario protocol;
- assertion vocabulary;
- normalization schema;
- gold schema;
- summary schema;
- artifact manifest schema;
- release gates;
- PGF release policy;
- licensing policy;
- required sign-off roles.

A compatible addition may increment the checklist minor version.

Removing or weakening a mandatory gate requires a major version and architecture/release review.

---

# 55. Anti-drift indicators

Probable completion drift exists when:

- the project is called complete but required placeholders remain;
- project identity differs across files;
- an old language suffix remains active;
- a required configured module is missing;
- a dependency map omits current imports;
- a consumer uses an undocumented field or helper;
- a required checkpoint is skipped;
- an entrypoint compiles only because stale `.gfo` files exist;
- a required scenario has no script;
- a required scenario has no assertion strategy;
- a required gold file is missing;
- a gold file changes without review;
- marker completion is not checked;
- zero exit is treated as full scenario success;
- a required PGF is missing after an apparently successful build;
- raw stdout or stderr is missing;
- timeout is mislabeled as syntax failure;
- downstream failures inflate root-cause counts;
- a release-blocking issue is absent from the ledger;
- documentation names removed modules;
- a release run uses legacy mode names;
- reports disagree with `summary.json`;
- the manifest omits a required artifact;
- release evidence comes from a different source fingerprint;
- an unchecked item is treated as passing;
- `NOT_APPLICABLE` has no rationale;
- an expired exception remains active;
- the project is released without sign-off.

Every detected indicator must be resolved before release.

---

# 56. Project-owner review checklist

Before signing:

```text
[ ] I reviewed project identity.
[ ] I reviewed project scope and non-goals.
[ ] I reviewed active entrypoints and checkpoints.
[ ] I reviewed the interfile contract lock.
[ ] I reviewed required scenarios and gold files.
[ ] I reviewed status-ledger entries.
[ ] I reviewed known issues.
[ ] I reviewed accepted exceptions.
[ ] I reviewed the clean release run.
[ ] I reviewed regression evidence.
[ ] I reviewed generated artifacts.
[ ] I reviewed the manifest.
[ ] I reviewed licensing and distribution scope.
[ ] I reviewed manual linguistic criteria.
[ ] I confirm no required item is silently skipped.
[ ] I confirm cited evidence belongs to the released source state.
```

---

# 57. Enforcement rule

Project completion is a claim about the whole project, not one successful file.

It requires agreement among:

- project identity;
- source files;
- module contracts;
- project configuration;
- validation policy;
- scenarios;
- assertions;
- gold expectations;
- generated artifacts;
- diagnostics;
- reports;
- known issues;
- documentation;
- release evidence.

Portfolio aggregation is outside this checklist. `gf-portfolio` may consume public, versioned release artifacts, but it cannot satisfy or replace a Wordbench project gate.

Therefore:

> GF Wordbench must not describe an active language project as complete or release-ready while any required contract is unsatisfied, any mandatory criterion is unproven, any blocking issue is unresolved, or any cited evidence belongs to a different project state.
