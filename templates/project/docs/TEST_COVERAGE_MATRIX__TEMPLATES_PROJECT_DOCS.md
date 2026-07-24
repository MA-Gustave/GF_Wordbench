# Project Template — Test Coverage Matrix

**Document ID:** `GF-WB-TEMPLATE-PROJECT-TEST-COVERAGE`
**Status:** Normative project-template document
**Canonical path:** `templates/project/docs/TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md`
**Template scope:** One active GF language project
**Canonical active-project destination:** `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`
**Primary configuration source:** `project/project.toml`
**Primary contract source:** `project/docs/INTERFILE_CONTRACT_LOCK.md`
**Primary validation source:** `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md`
**Primary release source:** `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md`
**Template owner:** GF Wordbench project-template maintainers
**Project owner after initialization:** Active-language maintainers
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
**Document version:** `1.1.0`
**Last structural review:** 2026-07-24

---

## 1. Purpose

This document is the canonical template for mapping a language project's declared behavior to validation evidence.

It answers:

```text
What does the project claim to support?
Which provider owns that behavior?
Which consumers depend on it?
Which compile target proves structural consistency?
Which scenario proves runtime or linguistic behavior?
Which input and gold file define the expectation?
Which release criterion consumes the evidence?
Which declared requirements are outside scope or lack an approved proof contract?
```

The completed active-project matrix makes every significant release claim traceable to at least one repeatable proof contract.

A test count alone is not coverage.

Coverage exists only when the matrix links:

```text
project claim
→ contract
→ provider
→ consumer
→ validation operation
→ retained evidence
→ release interpretation
```

---

## 2. Template use

When creating a project:

1. copy this file to `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`;
2. replace every required placeholder;
3. remove non-applicable example rows;
4. add project-specific rows;
5. align the matrix with `project.toml`;
6. align scenario IDs with `.gfs` filenames;
7. align gold IDs with `.gold` filenames;
8. align module names with actual GF declarations;
9. align contract IDs with the project interfile lock;
10. align release requirements with `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`;
11. define the expected evidence location for every required proof;
12. record release-significant defects or unsupported scope in `KNOWN_ISSUES.md`.

The active file MUST NOT retain unresolved required placeholders when the project is declared complete or release-ready.

Template placeholders are expected in this file.

---

## 3. Related project files

The completed matrix must remain consistent with:

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
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Framework references include:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
docs/validation/VALIDATION_MODES.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/reference/STATUS_VALUES.md
docs/reference/FILE_NAMING_CONVENTIONS.md
```

When this matrix disagrees with the project interfile contract lock, the lock is authoritative.

The matrix must then be corrected.

This template describes one active Wordbench project. It does not define cross-workspace or multilingual portfolio coverage. `gf-portfolio` may consume finalized public Wordbench artifacts but does not alter project proof obligations.

---

# 4. Coverage principles

The project coverage model follows these principles:

1. **Every release claim has evidence.**
2. **Every project contract has evidence.**
3. **Every required scenario has a declared purpose.**
4. **Every required gold has a registered scenario.**
5. **Compilation and linguistic behavior are separate proofs.**
6. **A top-level compile does not prove lower-layer contracts.**
7. **A scenario process exit does not prove marker completion.**
8. **A gold match does not prove coverage outside the scenario inputs.**
9. **Optional evidence remains visible.**
10. **Missing evidence is not interpreted as success.**
11. **Manual evidence is allowed only when automation is not practical.**
12. **Known project issues affecting proof obligations remain explicit in `KNOWN_ISSUES.md`.**
13. **Coverage is evaluated against declared scope, not an imaginary complete grammar.**
14. **Release readiness requires all release-required rows to be satisfied.**
15. **Coverage changes update this matrix in the same project change.**

---

# 5. Normative terms

- **CLAIM**: behavior, feature, contract or supported scope stated by the project.
- **SUBJECT**: module, category, function family, scenario, artifact or release criterion being evaluated.
- **PROVIDER**: file or module supplying the behavior.
- **CONSUMER**: file, scenario, entrypoint or external user relying on the behavior.
- **CONTRACT ID**: stable identifier from the project interfile lock.
- **EVIDENCE**: retained compile, scenario, gold, artifact, inspection or review proof.
- **COVERAGE ROW**: one matrix entry connecting a claim to a proof contract.
- **REQUIRED ROW**: row whose pass condition gates release.
- **OPTIONAL ROW**: useful proof obligation that does not gate release.
- **CONDITIONAL ROW**: row required when its associated project feature applies.
- **OUT OF SCOPE**: subject excluded from the project's declared scope, with a reason.
- **AUTOMATED EVIDENCE**: proof generated by a repeatable command.
- **MANUAL EVIDENCE**: documented human review.
- **DIRECT PROOF**: evidence validating the provider or subject itself.
- **CONSUMER PROOF**: evidence validating a documented consumer.
- **ENTRYPOINT PROOF**: evidence validating the downstream project surface.
- **LINGUISTIC PROOF**: evidence validating output or analysis meaning.
- **ARTIFACT PROOF**: evidence validating required artifact existence, provenance and integrity.
- **NEGATIVE PROOF**: evidence that invalid or unsupported input fails as intended.
- **REGRESSION PROOF**: evidence preserving behavior that previously failed.

---

# 6. Proof-obligation semantics

This matrix does not store implementation progress, recent run results or row statuses.

Each row defines:

```text
requirement
claim
contract owner
provider
consumers
proof type
proof target
pass condition
evidence location pattern
release effect
```

A required row is satisfied only by a compatible validation run whose retained evidence meets the row's pass condition.

Missing or failing proof is evaluated by the run and release gate. Project defects, limitations and unsupported scope are documented in:

```text
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

The matrix changes only when the stable proof obligation changes.

---

# 7. Requirement levels

Canonical requirement levels:

```text
RELEASE
CHECKPOINT
DIAGNOSTIC
OPTIONAL
CONDITIONAL
```

| Level | Meaning |
|---|---|
| `RELEASE` | Missing or failing evidence blocks release |
| `CHECKPOINT` | Required for checkpoint and release validation |
| `DIAGNOSTIC` | Required only for diagnostic depth |
| `OPTIONAL` | Useful but non-gating |
| `CONDITIONAL` | Gating only when the associated feature is active |

The level must agree with `project.toml`, `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md`, and `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`.

---

# 8. Evidence types

Canonical evidence types:

```text
CONFIG
IDENTIFIER_SCAN
SOURCE_SCAN
DIRECT_COMPILE
CONSUMER_COMPILE
CHECKPOINT_COMPILE
ENTRYPOINT_COMPILE
GF_LOAD
_INSPECTION
LINEARIZE
PARSE
GENERATE
MORPHOLOGY
ASSERTION
GOLD
PGF_BUILD
PGF_LOAD
ARTIFACT
MANIFEST
SCHEMA_CHECK
DEPENDENCY_REVIEW
MANUAL_LINGUISTIC_REVIEW
MANUAL_ARCHITECTURE_REVIEW
MIGRATION_TEST
NEGATIVE_TEST
REGRESSION_TEST
```

A row may require more than one evidence type.

Example:

```text
lincat contract:
  DIRECT_COMPILE
  CONSUMER_COMPILE
  ENTRYPOINT_COMPILE
  LINEARIZE
```

---

# 9. Evidence-strength levels

Evidence strength:

```text
E2 — provider proof
E3 — consumer proof
E4 — entrypoint proof
E5 — behavioral proof
E6 — release artifact proof
```

| Level | Description |
|---|---|
| `E2` | Direct provider compiles or validates |
| `E3` | At least one documented consumer validates |
| `E4` | Downstream checkpoint or entrypoint validates |
| `E5` | Scenario, assertion or reviewed gold proves behavior |
| `E6` | Release artifact and release validation prove integration |

A document declaration is not validation evidence.

The required evidence level depends on the claim.

Examples:

- private morphology helper may require `E2` or `E3`;
- public lincat field normally requires `E4` and `E5`;
- release entrypoint normally requires `E6`;
- a linguistic construction claim normally requires `E5`;
- a PGF distribution claim requires `E6`.

---

# 10. Coverage dimensions

Coverage should be evaluated across these dimensions:

```text
existence
type correctness
dependency correctness
loadability
runtime behavior
linguistic correctness
negative behavior
artifact production
release integration
documentation agreement
migration compatibility
platform/toolchain compatibility
```

A row marked `` should identify which dimensions are proven.

---

# 11. Row identity

Each coverage row has a stable ID.

Canonical format:

```text
COV-<DOMAIN>-<NUMBER>
```

Domains:

```text
CONFIG
IDENTITY
MODULE
LINCAT
MORPH
SYNTAX
LEXICON
STRUCT
ENTRY
SCENARIO
GOLD
PGF
ARTIFACT
DOC
MIGRATION
PLATFORM
RELEASE
```

Examples:

```text
COV-CONFIG-001
COV-MORPH-004
COV-SYNTAX-012
COV-SCENARIO-003
```

Rules:

- IDs are unique;
- IDs are never reused;
- row IDs are changed only through an explicit contract migration.

---

# 12. Core row schema

Every coverage row defines:

| Field | Meaning |
|---|---|
| Coverage ID | Stable row identifier |
| Requirement | Release, checkpoint, diagnostic, optional or conditional |
| Claim | Behavior being validated |
| Contract ID | Related project contract |
| Provider | Owning file or module |
| Consumers | Direct or downstream consumers |
| Evidence type | Compile, scenario, gold, artifact or review |
| Evidence target | Module, scenario, input, gold, artifact or report |
| Expected result | Pass condition |
| Evidence location | Run artifact role, scenario file, gold or review record |
| Owner | Maintainer responsible for the proof contract |
| Release effect | Blocking, conditional or non-blocking |

Execution results and verification dates remain in run artifacts and release records, not in this matrix.

---

# 13. Project identity and configuration coverage

Replace the placeholder rows with actual project facts.

| Coverage ID | Requirement | Claim | Contract | Evidence | Expected result | Owner | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `COV-CONFIG-001` | `RELEASE` | Project configuration is valid | `<CONFIG_CONTRACT_ID>` | `SCHEMA_CHECK` | `project.toml` parses and validates | `<OWNER>` | `<NOTES>` |
| `COV-IDENTITY-001` | `RELEASE` | Project ID is authoritative | `<IDENTITY_CONTRACT_ID>` | `CONFIG`, `IDENTIFIER_SCAN` | One project ID | `<OWNER>` | `<NOTES>` |
| `COV-IDENTITY-002` | `RELEASE` | Module suffix agrees across assets | `<IDENTITY_CONTRACT_ID>` | `IDENTIFIER_SCAN` | Source, scenarios, golds and docs agree | `<OWNER>` | `<NOTES>` |
| `COV-CONFIG-002` | `RELEASE` | Source root selects intended sources | `<CONFIG_CONTRACT_ID>` | `CONFIG`, `SOURCE_SCAN` | Exact deterministic source inventory | `<OWNER>` | `<NOTES>` |
| `COV-CONFIG-003` | `RELEASE` | Entrypoints exist | `<ENTRY_CONTRACT_ID>` | `CONFIG`, `ENTRYPOINT_COMPILE` | Every configured entrypoint exists | `<OWNER>` | `<NOTES>` |
| `COV-CONFIG-004` | `CHECKPOINT` | Checkpoints exist and are ordered | `<RELEASE_CONTRACT_ID>` | `CONFIG`, `CHECKPOINT_COMPILE` | Every configured checkpoint exists | `<OWNER>` | `<NOTES>` |
| `COV-CONFIG-005` | `RELEASE` | Scenario registry is consistent | `<SCENARIO_CONTRACT_ID>` | `CONFIG`, `SCHEMA_CHECK` | IDs unique; files and requirements valid | `<OWNER>` | `<NOTES>` |
| `COV-CONFIG-006` | `RELEASE` | Expected release artifacts are declared | `<ARTIFACT_CONTRACT_ID>` | `CONFIG`, `ARTIFACT` | Artifact identities are unambiguous | `<OWNER>` | `<NOTES>` |

---

# 14. Source inventory coverage

| Coverage ID | Requirement | Subject | Provider/path | Evidence | Expected result | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<SOURCE_GROUP>` | `<SOURCE_PATH_OR_GLOB>` | `SOURCE_SCAN` | All intended files selected | `<NOTES>` |
| `<COV_ID>` | `<LEVEL>` | Module/file-name agreement | `<SOURCE_ROOT>` | `IDENTIFIER_SCAN` | Every `.gf` stem matches declared module | `<NOTES>` |
| `<COV_ID>` | `<LEVEL>` | No duplicate project modules | `<SOURCE_ROOT>` | `SOURCE_SCAN` | No conflicting module declarations | `<NOTES>` |
| `<COV_ID>` | `<LEVEL>` | No stale language identifiers | `<PROJECT_SCOPE>` | `IDENTIFIER_SCAN` | Only active identity used | `<NOTES>` |
| `<COV_ID>` | `<LEVEL>` | No unresolved merge or backup source | `<SOURCE_ROOT>` | `SOURCE_SCAN` | No selected temporary/backup file | `<NOTES>` |
| `<COV_ID>` | `<LEVEL>` | Source encoding | `<SOURCE_ROOT>` | `SOURCE_SCAN` | All selected files decode correctly | `<NOTES>` |

---

# 15. Module-layer coverage overview

List every architectural layer from `LANGUAGE_ARCHITECTURE.md`.

| Layer ID | Layer name | Providers | Main consumers | Checkpoint | Required evidence level | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<LAYER_ID>` | `<RESOURCE_LAYER>` | `<MODULES>` | `<CONSUMERS>` | `<CHECKPOINT_OR_NA>` | `<E_LEVEL>` | `<NOTES>` |
| `<LAYER_ID>` | `<MORPHOLOGY_LAYER>` | `<MODULES>` | `<CONSUMERS>` | `<CHECKPOINT_OR_NA>` | `<E_LEVEL>` | `<NOTES>` |
| `<LAYER_ID>` | `<CATEGORY_LAYER>` | `<MODULES>` | `<CONSUMERS>` | `<CHECKPOINT_OR_NA>` | `<E_LEVEL>` | `<NOTES>` |
| `<LAYER_ID>` | `<SYNTAX_LAYER>` | `<MODULES>` | `<CONSUMERS>` | `<CHECKPOINT_OR_NA>` | `<E_LEVEL>` | `<NOTES>` |
| `<LAYER_ID>` | `<STRUCTURAL_LAYER>` | `<MODULES>` | `<CONSUMERS>` | `<CHECKPOINT_OR_NA>` | `<E_LEVEL>` | `<NOTES>` |
| `<LAYER_ID>` | `<EXTENSION_LAYER>` | `<MODULES>` | `<CONSUMERS>` | `<CHECKPOINT_OR_NA>` | `<E_LEVEL>` | `<NOTES>` |
| `<LAYER_ID>` | `<ENTRYPOINT_LAYER>` | `<MODULES>` | `<SCENARIOS_OR_PGF>` | `<CHECKPOINT_OR_NA>` | `<E_LEVEL>` | `<NOTES>` |

Remove rows for layers the project does not use.

---

# 16. Per-module coverage matrix

Create one row for every active GF module.

| Coverage ID | Requirement | Module | Kind | Contract IDs | Direct compile | Consumer compile | Checkpoint/entrypoint | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<MODULE>.gf` | `<KIND>` | `<CONTRACT_IDS>` | `<EVIDENCE>` | `<EVIDENCE>` | `<EVIDENCE>` | `<SCENARIO_OR_NA>` |

Recommended module kinds:

```text
abstract
concrete
resource
interface
instance
morphology
paradigm
category provider
syntax
structural
extension
lexicon
grammar entrypoint
API entrypoint
test support
legacy
```

Minimum rules:

- every release-reachable module has one row;
- every checkpoint has a row;
- every entrypoint has a row;
- a direct compile alone is insufficient for a public provider;
- a module unreachable from release entrypoints must be justified;
- legacy modules are not counted as project coverage.

---

# 17. Abstract-to-concrete coverage

| Coverage ID | Requirement | Abstract provider | Concrete consumer | Missing-function evidence | Direct compile | Entrypoint proof | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<ABSTRACT_MODULE>` | `<CONCRETE_MODULE>` | `<SCENARIO_OR_COMMAND>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<NOTES>` |

Criteria:

- concrete module matches abstract function types;
- omitted functions are explicit;
- required missing-function policy passes;
- entrypoint includes the intended concrete;
- scenarios do not load an unrelated lower-level substitute.

---

# 18. Interface and instance coverage

| Coverage ID | Requirement | Interface | Instance | Direct consumer | Compile proof | Behavioral proof | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<INTERFACE_MODULE>` | `<INSTANCE_MODULE>` | `<CONSUMER>` | `<COMPILE_TARGET>` | `<SCENARIO_OR_NA>` | `<NOTES>` |

Criteria:

- all required interface fields are implemented;
- types agree;
- instance is used by intended consumers;
- no duplicate competing instance exists without policy;
- consumer proof exists.

---

# 19. Lincat coverage

Create rows for every public category structure documented in `CATEGORY_AND_LINCAT_CONTRACT.md`.

| Coverage ID | Requirement | Category | Provider | Shape/version | Direct consumers | Compile proof | Behavioral proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CATEGORY>` | `<MODULE>` | `<FIELDS_OR_REFERENCE>` | `<CONSUMERS>` | `<TARGETS>` | `<SCENARIOS>` |

Review dimensions:

```text
field existence
field type
field meaning
agreement dimensions
parameter values
constructor initialization
consumer pattern matching
word-order consequences
empty/missing representation
coercions
variants
```

A lincat row requires consumer and behavioral proof; defining-module compilation alone is insufficient.

---

# 20. Shared parameter and feature coverage

| Coverage ID | Requirement | Parameter/feature | Provider | Values | Consumers | Positive evidence | Negative/edge evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<FEATURE>` | `<MODULE>` | `<VALUES>` | `<CONSUMERS>` | `<SCENARIO>` | `<SCENARIO_OR_NA>` |

Possible features:

```text
number
gender
case
person
tense
aspect
mood
definiteness
animacy
polarity
degree
voice
agreement class
word-order state
language-specific inflection class
```

Only include features used by the project.

---

# 21. Morphology coverage overview

| Domain | Claimed scope | Provider modules | Paradigm modules | Scenario | Gold/assertion | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Nouns | `<SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Verbs | `<SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Adjectives | `<SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Adverbs | `<SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Pronouns | `<SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Determiners | `<SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Numerals | `<SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Other | `<DOMAIN_AND_SCOPE>` | `<MODULES>` | `<PARADIGMS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |

Remove non-applicable rows.

---

# 22. Morphology paradigm matrix

Create one row per public paradigm family or irregular-family contract.

| Coverage ID | Requirement | Paradigm/family | Provider | Input classes | Output dimensions | Representative inputs | Edge cases | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<PARADIGM>` | `<MODULE>` | `<INPUT_CLASSES>` | `<FEATURES>` | `<INPUT_FILE_OR_LIST>` | `<EDGE_CASES>` | `<SCENARIO>` |

Evidence should cover, where relevant:

```text
regular stems
irregular stems
orthographic alternations
defective paradigms
zero forms
multiple variants
stem boundary cases
short/long forms
agreement classes
loanword behavior
proper names
multiword lexical items
```

---

# 23. Morphology cell coverage

Use when a paradigm has a structured table that requires explicit cell coverage.

| Coverage ID | Paradigm | Feature combination | Expected behavior | Input | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<PARADIGM>` | `<FEATURE_VALUES>` | `<EXPECTED_FORM_OR_POLICY>` | `<LEMMA>` | `<SCENARIO_SECTION>` | `<NOTES>` |

Do not enumerate every cell when representative equivalence classes are documented and justified.

Do enumerate every cell when:

- the paradigm is small;
- each cell has unique logic;
- release correctness requires complete table coverage;
- known regressions cluster in specific cells.

---

# 24. Noun morphology matrix

| Coverage ID | Requirement | Noun class | Number | Case | Definiteness/state | Representative lexeme | Expected rule | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CLASS>` | `<NUMBER>` | `<CASE>` | `<STATE>` | `<LEXEME>` | `<RULE>` | `<SCENARIO_SECTION>` |

Use only dimensions supported by the project.

---

# 25. Verb morphology matrix

| Coverage ID | Requirement | Verb class | Person/number | Tense/aspect | Mood/voice | Representative lexeme | Expected rule | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CLASS>` | `<AGR>` | `<TAM>` | `<MOOD_VOICE>` | `<LEXEME>` | `<RULE>` | `<SCENARIO_SECTION>` |

Include irregular and defective families explicitly when claimed.

---

# 26. Adjective morphology matrix

| Coverage ID | Requirement | Adjective class | Agreement | Degree | Position/state | Representative lexeme | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CLASS>` | `<FEATURES>` | `<DEGREE>` | `<POSITION>` | `<LEXEME>` | `<SCENARIO_SECTION>` |

---

# 27. Pronoun and determiner coverage

| Coverage ID | Requirement | Family | Feature dimensions | Syntactic role | Provider | Scenario | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<PRONOUN_OR_DET_FAMILY>` | `<FEATURES>` | `<ROLE>` | `<MODULE>` | `<SCENARIO>` | `<NOTES>` |

Review:

```text
person
number
gender
case
politeness
deixis
definiteness
agreement
clitic/full form distinction
reflexivity
possessive behavior
```

---

# 28. Lexicon coverage

The matrix should distinguish grammar coverage from lexicon size.

| Coverage ID | Requirement | Lexical category | Required inventory or sampling policy | Provider | Paradigm policy | Duplicate-ID check | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CATEGORY>` | `<POLICY>` | `<LEXICON_MODULE>` | `<PARADIGM_POLICY>` | `<EVIDENCE>` | `<SCENARIO>` |

Possible policies:

```text
complete closed class
release-defined minimum inventory
representative open-class sample
regression-only entries
domain-specific vocabulary list
```

Do not claim complete lexicon coverage without a measurable definition.

---

# 29. Structural lexicon coverage

| Coverage ID | Requirement | Structural family | Provider | Required items | Consumer proof | Linguistic proof |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | Prepositions | `<MODULE>` | `<INVENTORY_OR_POLICY>` | `<TARGET>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Conjunctions | `<MODULE>` | `<INVENTORY_OR_POLICY>` | `<TARGET>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Pronouns | `<MODULE>` | `<INVENTORY_OR_POLICY>` | `<TARGET>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Determiners | `<MODULE>` | `<INVENTORY_OR_POLICY>` | `<TARGET>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Subjunctions | `<MODULE>` | `<INVENTORY_OR_POLICY>` | `<TARGET>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Other closed class | `<MODULE>` | `<INVENTORY_OR_POLICY>` | `<TARGET>` | `<SCENARIO>` |

Remove non-applicable rows.

---

# 30. Syntax construction overview

List every construction family claimed in `SYNTAX_AND_CONSTRUCTOR_RULES.md`.

| Construction family | Claimed scope | Provider modules | Entry category/function family | Scenario | Gold/assertion | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Basic clauses | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Noun phrases | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Verb phrases | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Questions | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Relatives | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Coordination | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Subordination | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Negation | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Imperatives | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Extensions | `<SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |
| Other | `<FAMILY_AND_SCOPE>` | `<MODULES>` | `<FUNCTIONS>` | `<SCENARIO>` | `<EVIDENCE>` | `<NOTES>` |

Remove rows outside project scope.

---

# 31. Per-constructor coverage

Create one row per public constructor or equivalence class of constructors when appropriate.

| Coverage ID | Requirement | Function/constructor | Provider | Input category pattern | Claimed behavior | Positive tree/input | Negative/edge input | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<FUNCTION>` | `<MODULE>` | `<TYPE>` | `<BEHAVIOR>` | `<INPUT>` | `<EDGE>` | `<SCENARIO_SECTION>` |

Grouping is allowed when:

- constructors share one source contract;
- representative equivalence is documented;
- ungrouped edge cases have separate rows.

Do not group unrelated functions merely to reduce matrix size.

---

# 32. Word-order coverage

| Coverage ID | Requirement | Context | Expected order | Variation policy | Provider | Example tree/input | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CONTEXT>` | `<ORDER_RULE>` | `<VARIANTS>` | `<MODULE>` | `<INPUT>` | `<SCENARIO_SECTION>` |

Possible contexts:

```text
declarative clause
polar question
wh-question
relative clause
negative clause
subordinate clause
noun phrase
adjective position
clitic sequence
auxiliary sequence
coordination
focus/topic construction
```

---

# 33. Agreement coverage

| Coverage ID | Requirement | Agreement relation | Controller | Target | Features | Positive evidence | Mismatch/edge evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<RELATION>` | `<CONTROLLER>` | `<TARGET>` | `<FEATURES>` | `<SCENARIO>` | `<NEGATIVE_OR_EDGE>` |

Examples:

```text
subject–verb
determiner–noun
adjective–noun
pronoun antecedent
relative agreement
predicative agreement
coordination resolution
```

---

# 34. Case and complement coverage

| Coverage ID | Requirement | Governor | Complement type | Required case/form | Provider | Positive input | Negative/edge input | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<GOVERNOR>` | `<COMPLEMENT>` | `<CASE_OR_FORM>` | `<MODULE>` | `<INPUT>` | `<EDGE>` | `<SCENARIO>` |

Use only when case/complement selection is part of the language contract.

---

# 35. Polarity and negation coverage

| Coverage ID | Requirement | Construction | Polarity feature | Placement rule | Interaction | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CONSTRUCTION>` | `<FEATURE>` | `<RULE>` | `<TENSE_QUESTION_ETC>` | `<SCENARIO>` | `<NOTES>` |

---

# 36. Question coverage

| Coverage ID | Requirement | Question type | Category | Word-order policy | Interrogative inventory | Parse proof | Linearization proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | Polar | `<CAT>` | `<RULE>` | `<NA>` | `<SCENARIO>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Wh-subject | `<CAT>` | `<RULE>` | `<ITEMS>` | `<SCENARIO>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Wh-object | `<CAT>` | `<RULE>` | `<ITEMS>` | `<SCENARIO>` | `<SCENARIO>` |
| `<COV_ID>` | `<LEVEL>` | Other | `<CAT>` | `<RULE>` | `<ITEMS>` | `<SCENARIO>` | `<SCENARIO>` |

Remove non-applicable rows.

---

# 37. Relative-clause coverage

| Coverage ID | Requirement | Relative type | Syntactic role | Agreement | Word order | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<TYPE>` | `<ROLE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` | `<NOTES>` |

---

# 38. Coordination coverage

| Coverage ID | Requirement | Coordinated category | Conjunction | Agreement resolution | Punctuation/order | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CATEGORY>` | `<ITEM>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |

---

# 39. Extension and override coverage

| Coverage ID | Requirement | Symbol/family | Action | Upstream provider | Local provider | Reason | Consumer proof | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<SYMBOL>` | `inherit/override/subtract` | `<UPSTREAM>` | `<LOCAL_OR_NA>` | `<REASON>` | `<TARGET>` | `<SCENARIO>` |

Criteria:

- every override is deliberate;
- every subtraction is deliberate;
- inherited functions remain inherited unless justified;
- local overrides have a documented owner, rationale and compatibility proof;
- upstream version compatibility is tested.

---

# 40. Entrypoint coverage

| Coverage ID | Requirement | Entrypoint | Project role | Direct compile | Clean compile | Load scenario | Missing inspection | PGF role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `RELEASE` | `<ENTRYPOINT>.gf` | `<ROLE>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<SCENARIO>` | `<EVIDENCE>` | `<PGF_OR_NA>` |

Every release entrypoint row should reach evidence level `E6` when it produces the release PGF.

---

# 41. Checkpoint coverage

| Coverage ID | Order | Checkpoint | Layer proven | Prerequisites | Compile evidence | Downstream evidence | Required modes |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<N>` | `<CHECKPOINT>.gf` | `<LAYER>` | `<PREREQUISITES>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<ENTRYPOINT_OR_SCENARIO>` | `checkpoint/release` |

Criteria:

- order matches `project.toml`;
- all required checkpoints are represented;
- downstream success does not erase a checkpoint failure;
- omitted checkpoint requires explicit project-policy decision.

---

# 42. Scenario registry coverage

| Coverage ID | Scenario ID | Script | Requirement | Modes | Entrypoint | Inputs | Gold/assertion | Purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `load` | `load.gfs` | `<REQUIRED>` | `<MODES>` | `<ENTRYPOINT>` | `<INPUTS_OR_NONE>` | `<ASSERTION_OR_GOLD>` | Load intended grammar |
| `<COV_ID>` | `missing` | `missing.gfs` | `<REQUIRED>` | `<MODES>` | `<ENTRYPOINT>` | `<INPUTS_OR_NONE>` | `<ASSERTION_OR_GOLD>` | Inspect missing functions |
| `<COV_ID>` | `linearize` | `linearize.gfs` | `<REQUIRED>` | `<MODES>` | `<ENTRYPOINT>` | `<INPUTS>` | `<GOLD_OR_ASSERTIONS>` | Validate representative trees |
| `<COV_ID>` | `parse` | `parse.gfs` | `<REQUIRED>` | `<MODES>` | `<ENTRYPOINT>` | `<INPUTS>` | `<GOLD_OR_ASSERTIONS>` | Validate representative strings |
| `<COV_ID>` | `generation` | `generation.gfs` | `<REQUIRED_OR_OPTIONAL>` | `<MODES>` | `<ENTRYPOINT>` | `<INPUTS_OR_NONE>` | `<ASSERTIONS_OR_GOLD>` | Bounded generation |
| `<COV_ID>` | `morphology` | `morphology.gfs` | `<REQUIRED_OR_OPTIONAL>` | `<MODES>` | `<ENTRYPOINT_OR_MODULE>` | `<INPUTS>` | `<GOLD_OR_ASSERTIONS>` | Validate paradigms |
| `<COV_ID>` | `<SCENARIO_ID>` | `<SCENARIO_ID>.gfs` | `<LEVEL>` | `<MODES>` | `<ENTRYPOINT>` | `<INPUTS>` | `<EVIDENCE>` | `<PURPOSE>` |

Remove or add rows to match `project.toml`.

---

# 43. Scenario section coverage

For each scenario, list required sections.

| Scenario ID | Section ID | Claim | Marker pair required | Assertion/gold section | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<SCENARIO_ID>` | `<SECTION_ID>` | `<CLAIM>` | `yes/no` | `<ASSERTION_OR_GOLD_SECTION>` | `<RUN_PATH>` | `<NOTES>` |

Rules:

- section IDs are unique within a scenario;
- every required begin marker has an end marker;
- missing section is not a pass;
- normalization preserves section identity.

---

# 44. Scenario input coverage

| Coverage ID | Scenario | Input file | Format | Encoding | Cases represented | Edge cases | Ordering semantics |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<SCENARIO_ID>` | `<INPUT_FILE>` | `<FORMAT>` | `<ENCODING>` | `<CASE_SET>` | `<EDGE_SET>` | `<ORDER_RULE>` |

Every release input should be version-controlled.

---

# 45. Gold coverage

| Coverage ID | Scenario | Gold file | Required | Gold schema | Normalization version | Sections |
| --- | --- | --- | ---: | --- | --- | --- |
| `<COV_ID>` | `<SCENARIO_ID>` | `<SCENARIO_ID>.gold` | `<YES_NO>` | `<VERSION>` | `<VERSION>` | `<SECTIONS>` |

Criteria:

- scenario and gold IDs agree;
- required gold exists;
- normalized output matches the reviewed expectation;
- last change is reviewed;
- linguistically meaningful output remains;
- ordinary validation did not rewrite the gold.

---

# 46. Assertion coverage

Use when exact gold is not the correct strategy.

| Coverage ID | Scenario | Assertion ID | Assertion type | Subject | Expected condition | Required |
| --- | --- | --- | --- | --- | --- | ---: |
| `<COV_ID>` | `<SCENARIO_ID>` | `<ASSERTION_ID>` | `<TYPE>` | `<SUBJECT>` | `<EXPECTED>` | `<YES_NO>` |

Possible bounded assertion types:

```text
section completed
output non-empty
output empty
contains exact line
does not contain line
expected tree present
parse count equals
parse count within range
artifact exists
artifact non-empty
missing-function set equals
no fatal diagnostic
```

Do not use arbitrary code expressions as project assertions.

---

# 47. Negative-test coverage

| Coverage ID | Requirement | Invalid/unsupported case | Expected failure | Evidence type | Scenario/test |
| --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CASE>` | `<FAILURE_BEHAVIOR>` | `NEGATIVE_TEST` | `<SCENARIO_OR_TEST>` |

Possible negative cases:

```text
invalid parse string
unsupported morphology class
missing required input
invalid marker sequence
wrong category
forbidden module dependency
unknown project identifier
missing required gold
unsupported GF command
```

Negative coverage should focus on contract boundaries, not arbitrary malformed data volume.

---

# 48. Regression coverage

Every fixed project regression SHOULD receive a stable coverage row.

| Coverage ID | Issue/decision ID | Regression description | Previous failure | Fix owner | Evidence | Required level |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<ISSUE_ID>` | `<DESCRIPTION>` | `<OLD_BEHAVIOR>` | `<MODULE>` | `<SCENARIO_SECTION_OR_TEST>` | `<LEVEL>` |

Rules:

- preserve enough input to reproduce the old failure;
- use a scenario or test at the correct layer;
- do not rely only on a closed issue description;
- removing the supported behavior requires removal or migration of the regression row with explanation.

---

# 49. Parse coverage matrix

| Coverage ID | Requirement | Input ID/text | Category | Expected parse policy | Expected tree(s) | Ambiguity policy | Scenario section |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<INPUT_ID>` | `<CATEGORY>` | `<AT_LEAST_ONE_EXACTLY_ONE_NONE_RANGE>` | `<TREES_OR_REFERENCE>` | `<POLICY>` | `<SECTION>` |

Review:

```text
positive cases
negative cases
ambiguity
orthographic variants
punctuation
category selection
unknown-word policy
```

---

# 50. Linearization coverage matrix

| Coverage ID | Requirement | Tree ID/tree | Target language | Expected output policy | Variant policy | Empty-output policy | Scenario section |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<TREE_ID>` | `<LANGUAGE>` | `<EXACT_OR_SET>` | `<POLICY>` | `<POLICY>` | `<SECTION>` |

Review:

```text
orthography
spacing
punctuation
agreement
word order
clitic behavior
variant ordering
empty versus missing output
```

---

# 51. Generation coverage matrix

| Coverage ID | Requirement | Category | Bound | Seed/policy | Expected condition | Scenario section | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CATEGORY>` | `<BOUND>` | `<SEED_OR_ORDER_POLICY>` | `<ASSERTION_OR_GOLD_POLICY>` | `<SECTION>` | `<NOTES>` |

Exact generation gold is permitted only when output is bounded and deterministic.

---

# 52. Missing-function coverage

| Coverage ID | Requirement | Concrete/entrypoint | Inspection command/scenario | Accepted missing set | Unexpected missing policy |
| --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `RELEASE` | `<MODULE>` | `<SCENARIO_OR_COMMAND>` | `<SET_OR_NONE>` | `FAIL` |

Do not treat empty output as success without the scenario contract confirming its meaning.

---

# 53. PGF coverage

| Coverage ID | Requirement | PGF target | Provider entrypoint | Build evidence | Existence | Non-empty | Hash/manifest | Load/smoke proof |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<RELEASE_OR_NA>` | `<EXPECTED_PGF>` | `<ENTRYPOINT>` | `<RUN_PATH>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<PASS_CONDITION_OR_EVIDENCE>` | `<SCENARIO_OR_TEST>` |

When PGF is not a release requirement, document why.

---

# 54. Artifact coverage

| Coverage ID | Requirement | Artifact role | Expected path/name | Producer | Consumer | Existence proof | Integrity proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `.gfo` | `<PATH_POLICY>` | GF compiler | downstream compile | `<EVIDENCE>` | `<FRESHNESS>` |
| `<COV_ID>` | `<LEVEL>` | `.pgf` | `<EXPECTED_NAME>` | PGF build | release/package/scenarios | `<EVIDENCE>` | `<HASH_MANIFEST>` |
| `<COV_ID>` | `<LEVEL>` | scenario output | `<PATH_POLICY>` | scenario runner | comparator | `<EVIDENCE>` | `<SCHEMA_OR_MARKERS>` |
| `<COV_ID>` | `<LEVEL>` | report | `<NAME>` | report writer | maintainer/automation | `<EVIDENCE>` | `<SCHEMA>` |

---

# 55. Report and manifest coverage

| Coverage ID | Requirement | Report/artifact | Required fields/sections | Schema/reference | Verification | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `RELEASE` | `summary.json` | `<FIELDS>` | `gf-wordbench.run-summary/<VERSION>` | strict schema check | `<NOTES>` |
| `<COV_ID>` | `RELEASE` | `manifest.json` | `<FIELDS>` | `gf-wordbench.artifact-manifest/<VERSION>` | hashes and paths | `<NOTES>` |
| `<COV_ID>` | `<LEVEL>` | `summary.md` | `<SECTIONS>` | `<SOFT_SCHEMA>` | document check | `<NOTES>` |
| `<COV_ID>` | `<LEVEL>` | `AI_READY.md` | `<SECTIONS>` | `<SOFT_SCHEMA>` | document check | `<NOTES>` |

---

# 56. Validation-mode coverage

Map each project validation subject to modes.

| Subject | Quick | Checkpoint | Release | Diagnostic | Reason |
|---|---:|---:|---:|---:|---|
| Targeted source compile | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |
| Source scan | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |
| All checkpoints | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |
| Release entrypoints | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |
| Required scenarios | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |
| Optional diagnostic scenarios | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |
| PGF build | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |
| Previous-run diff | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<YES_NO>` | `<REASON>` |

This table must agree with `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md`.

---

# 57. Release-criterion coverage

Map every active release criterion to evidence.

| Coverage ID | Release criterion | Requirement | Evidence source | Expected result |
| --- | --- | --- | --- | --- |
| `<COV_ID>` | Project identity | `RELEASE` | `project.toml`, identifier scan | consistent |
| `<COV_ID>` | Contract integrity | `RELEASE` | contract check | pass |
| `<COV_ID>` | Checkpoints | `RELEASE` | compile results | all `OK` |
| `<COV_ID>` | Entrypoints | `RELEASE` | compile results | all `OK` |
| `<COV_ID>` | Required scenarios | `RELEASE` | scenario results | all `OK` |
| `<COV_ID>` | Gold comparisons | `RELEASE` | scenario results | all required true |
| `<COV_ID>` | Required PGF | `<RELEASE_OR_NA>` | artifact/manifest | present, non-empty and attributable to the release run |
| `<COV_ID>` | Documentation | `RELEASE` | document review | agrees with source |
| `<COV_ID>` | Known issues | `RELEASE` | known-issue review | no blockers |
| `<COV_ID>` | Summary/manifest | `RELEASE` | schema checks | valid |

Extend to cover every gate in the active `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`.

---

# 58. Documentation coverage

| Coverage ID | Document | Required responsibility | Project subjects | Verification method |
| --- | --- | --- | --- | --- |
| `<COV_ID>` | `LANGUAGE_OVERVIEW.md` | Scope and identity | project configuration | document review |
| `<COV_ID>` | `LANGUAGE_ARCHITECTURE.md` | Module layers | source modules | dependency review |
| `<COV_ID>` | `MODULE_DEPENDENCY_MAP.md` | Actual dependencies | imports/extends/opens | source comparison |
| `<COV_ID>` | `CATEGORY_AND_LINCAT_CONTRACT.md` | Public category shapes | lincat providers/consumers | contract review |
| `<COV_ID>` | `MORPHOLOGY_SPEC.md` | Paradigms and features | morphology modules | scenario/review |
| `<COV_ID>` | `SYNTAX_AND_CONSTRUCTOR_RULES.md` | Constructor behavior | syntax modules | scenario/review |
| `<COV_ID>` | `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md` | Validation meanings | scenarios/gates | registry review |
| `<COV_ID>` | `KNOWN_ISSUES.md` | Defects, limitations and release blockers | affected project subjects | known-issue and source review |
| `<COV_ID>` | `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` | Release gates | project evidence | release review |

---

# 59. Toolchain and platform coverage

| Coverage ID | Requirement | Environment | GF version | RGL revision | Platform | Evidence set | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<ENVIRONMENT_ID>` | `<GF_VERSION>` | `<RGL_REVISION>` | `<PLATFORM>` | `<COMPILE_SCENARIO_PGF>` | `<NOTES>` |

Each environment row identifies its requirement level and the complete evidence set needed for the stated compatibility claim.

Do not claim compatibility from one successful source compile.

---

# 60. External compatibility coverage

Use when external modules or PGF consumers depend on the project.

| Coverage ID | Requirement | Consumer | Consumed surface | Compatibility contract | Test/evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<CONSUMER>` | `<MODULE_OR_PGF_API>` | `<CONTRACT_ID>` | `<EVIDENCE>` | `<NOTES>` |

---

# 61. Migration coverage

| Coverage ID | Requirement | Source form/version | Target form/version | Migrator or manual process | Fixture/evidence | Loss policy |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<SOURCE>` | `<TARGET>` | `<PROCESS>` | `<FIXTURE_OR_RUN>` | `<LOSS_POLICY>` |

Possible project migrations:

```text
module rename
module suffix rename
entrypoint rename
scenario ID rename
gold schema update
normalization update
project schema update
source-root migration
GF version transition
```

---

# 62. Manual review coverage

Manual review is permitted only when automation cannot fully prove the claim.

| Coverage ID | Requirement | Subject | Review criterion | Reviewer role | Evidence location | Frequency |
| --- | --- | --- | --- | --- | --- | --- |
| `<COV_ID>` | `<LEVEL>` | `<SUBJECT>` | `<CRITERION>` | `<ROLE>` | `<PATH_OR_RECORD>` | `<FREQUENCY>` |

Examples:

```text
linguistic acceptability
orthographic convention
research interpretation
license review
semantic gold change
```

Manual review cannot replace compile, artifact, hash, or schema proof.

---

# 63. Known proof gaps

A required proof gap is documented in:

```text
project/docs/KNOWN_ISSUES.md
```

The issue records:

```text
affected coverage ID
missing proof
reason
release impact
owner
required correction
exit condition
```

This matrix keeps the stable proof obligation. It does not duplicate the issue's changing lifecycle.

---

# 64. Non-blocking validation limitations

A non-blocking weakness, such as limited edge-case sampling or absent second-platform coverage, is documented in `KNOWN_ISSUES.md` when it affects users, maintenance or release interpretation.

It must not conceal a mandatory release proof.

---

# 65. Coverage exclusions

Excluded scope must be explicit.

| Exclusion ID | Subject | Reason outside scope | User impact | Documentation | Reconsideration trigger |
|---|---|---|---|---|---|
| `<EXCLUSION_ID>` | `<SUBJECT>` | `<REASON>` | `<IMPACT>` | `<DOC_REFERENCE>` | `<TRIGGER>` |

Examples:

```text
unsupported construction
out-of-scope dialect
unimplemented optional tense
external lexicon domain
platform not supported
```

An exclusion is not a failed test.

It is a declared scope boundary.

---

# 66. Coverage metrics

Metrics may summarize stable matrix structure but must not replace row review.

Useful structural metrics include:

```text
number of release-required rows
number of project contracts mapped to proof
number of checkpoints mapped
number of entrypoints mapped
number of required scenarios mapped
number of required artifacts mapped
number of manual proof obligations
```

Do not compute a single percentage that can hide a missing release-critical proof.

---

# 67. No weighted release score

GF Wordbench does not use a weighted coverage score to decide release readiness.

Every release-critical proof is evaluated directly through its gate.

---

# 68. Coverage-row completeness

A coverage row is complete when:

```text
claim defined
contract and owner defined
provider identified
consumer set reviewed
evidence type defined
evidence target defined
pass condition defined
evidence location pattern defined
release effect defined
```

Whether a run satisfies the row is recorded in run and release evidence.

---

# 69. Run-evidence compatibility

A run may satisfy a coverage row only when its evidence corresponds to the source, configuration, scenarios, inputs, gold, normalization, GF version, RGL revision and contract meaning being evaluated.

Compatibility and provenance are recorded in run artifacts and release records.

Preferred evidence locations include:

```text
run summary
run-local compile logs
run-local scenario logs
run-local normalized output
project-controlled gold
manifest
project decision or review record
version-control test result
```

Personal desktop files, chat messages and unversioned copied logs are not release evidence.

---

# 72. Matrix review triggers

Review this matrix when:

```text
project scope changes
module ownership changes
a contract changes
a lincat changes
scenario purpose or requiredness changes
gold policy changes
normalization policy changes
entrypoint or checkpoint obligations change
release criteria change
```

Routine source edits and ordinary run-result changes do not require matrix edits when the proof obligation is unchanged.

---

# 73. Coverage-contract change workflow

For each change to a proof obligation:

1. identify affected coverage rows;
2. identify affected contracts;
3. identify providers and consumers;
4. update scenarios, inputs or gold policy where required;
5. update the expected proof and pass condition;
6. run direct and downstream validation;
7. review release impact;
8. update this matrix in the same coordinated change.

A source change does not require a matrix edit when the stable proof contract remains unchanged.

---

# 74. Adding a new project feature

Before declaring a feature supported:

```text
[ ] Feature scope documented
[ ] Contract ID created or linked
[ ] Provider identified
[ ] Consumers identified
[ ] Direct compile evidence added
[ ] Consumer/entrypoint evidence added
[ ] Behavioral scenario added
[ ] Inputs added
[ ] Gold or assertions added
[ ] Negative/edge cases considered
[ ] Coverage row added
[ ] Release criterion reviewed
[ ] Known limitations documented
```

---

# 75. Changing a lincat or shared parameter

Required coverage actions:

```text
[ ] Provider row updated
[ ] Every direct consumer row reviewed
[ ] Constructor initialization evidence updated
[ ] Pattern-match consumers updated
[ ] Checkpoint evidence rerun
[ ] Entrypoint evidence rerun
[ ] Representative linearization rerun
[ ] Parse/generation evidence reviewed when affected
[ ] Gold changes reviewed
[ ] Contract lock updated
[ ] Decision log updated for breaking changes
```

---

# 76. Renaming a module or entrypoint

Coverage migration unit:

```text
module row
contract IDs
provider/consumer references
checkpoint registry
entrypoint registry
scenario entrypoint references
gold ownership where affected
PGF target
dependency map
release criteria
evidence paths
```

Old coverage IDs remain reserved.

---

# 77. Changing a scenario

Required actions:

```text
[ ] Scenario purpose reviewed
[ ] Scenario ID stability reviewed
[ ] Entrypoint mapping reviewed
[ ] Input rows updated
[ ] Marker rows updated
[ ] Assertion/gold rows updated
[ ] Normalization version reviewed
[ ] Coverage rows updated
[ ] Release requirement reviewed
[ ] Evidence location regenerated
```

---

# 78. Updating a gold

Required coverage actions:

```text
[ ] Source or specification reason identified
[ ] Scenario still proves intended claim
[ ] Raw old/new output reviewed
[ ] Normalized diff reviewed
[ ] Linguistic meaning reviewed
[ ] Gold row last-reviewed value updated
[ ] Affected construction/morphology rows reviewed
[ ] Decision log updated when significant
[ ] Release impact reviewed
```

---

# 79. GF/RGL upgrade review

When changing toolchain:

```text
[ ] Toolchain row updated
[ ] All checkpoints rerun
[ ] All entrypoints rerun
[ ] PGF rebuilt
[ ] All required scenarios rerun
[ ] Diagnostic parsing reviewed
[ ] Normalization reviewed
[ ] Gold diffs reviewed
[ ] Platform evidence updated
[ ] Compatibility claims updated
```

---

# 80. Release coverage rules

A normal release requires:

```text
every release-required row mapped to compatible retained evidence
every pass condition satisfied
every required checkpoint passing
every required entrypoint passing
every required scenario and gold comparison passing
every required artifact present and verified
every release criterion mapped to evidence
no unresolved release blocker in KNOWN_ISSUES.md
```

Optional and diagnostic obligations affect release only through `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`.

---

# 81. Coverage and waivers

A waiver does not provide missing evidence.

A release waiver records:

```text
waiver ID
affected coverage ID
reason
risk
approver
expiration
compensating evidence
```

The release policy decides whether the waiver is permitted. Core compilation, required scenarios, required gold, required artifacts and summary/manifest integrity are not waived for a normal release.

---

# 82. Coverage and known issues

`TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md` owns stable proof obligations.

`KNOWN_ISSUES.md` owns changing defects, limitations, missing proofs and release blockers.

The two documents agree on the affected contract and required proof, while issue actions and resolution history remain exclusively in `KNOWN_ISSUES.md`.

---

# 83. Coverage and decision log

Use `DECISION_LOG.md` when coverage changes because of:

```text
scope reduction
scope expansion
contract redesign
scenario ID change
normalization change
gold acceptance change
entrypoint change
PGF target change
manual-evidence policy
waiver of a significant criterion
```

Routine evidence refresh does not require a new decision entry.

---

# 84. Coverage and release criteria

Every mandatory project release gate should have at least one matrix row.

Every release-required matrix row should map to one or more release gates.

A mismatch indicates drift.

Examples:

```text
release requires PGF
→ PGF coverage row required

release requires parse scenario
→ parse registry, input, assertion/gold and linguistic rows required

release claims noun morphology
→ paradigm and representative cell rows required
```

---

# 85. Coverage and contract registry

Every project contract should appear in at least one row.

Recommended cross-reference table:

| Contract ID | Coverage rows | Evidence strength | Notes |
| --- | --- | --- | --- |
| `<CONTRACT_ID>` | `<COV_IDS>` | `<E_LEVEL>` | `<NOTES>` |

A contract with no coverage row is unproven.

---

# 86. Coverage and dependency map

Every provider/consumer relationship used by a coverage row should agree with `MODULE_DEPENDENCY_MAP.md`.

Review:

```text
provider exists
consumer imports/extends/opens provider
entrypoint reaches subject
scenario reaches intended entrypoint
no hidden higher-level dependency
```

---

# 87. Coverage and documentation claims

For every claim in:

```text
LANGUAGE_OVERVIEW.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
```

ask whether a coverage row exists.

Claims using words such as:

```text
supports
implements
complete
stable
release-ready
fully covers
correctly handles
```

require evidence.

Unsupported aspirational statements are removed or rewritten as explicit scope exclusions.

---

# 88. Initialization checklist

When instantiating this template:

```text
[ ] Replace project identity placeholders
[ ] List architectural layers
[ ] List every project module
[ ] Link every project contract
[ ] Register checkpoints
[ ] Register entrypoints
[ ] Register scenarios
[ ] Register inputs
[ ] Register golds
[ ] Define release criteria mapping
[ ] Add morphology domains
[ ] Add syntax construction families
[ ] Add lincat rows
[ ] Add regression rows
[ ] Add toolchain/platform rows
[ ] Link release-significant known issues
[ ] Remove non-applicable examples
[ ] Verify no required placeholder remains
```

---

# 89. Minimum active-project matrix

At minimum, the completed active matrix must include:

```text
project configuration rows
identity rows
one row per project module
one row per project contract
one row per checkpoint
one row per release entrypoint
one row per required scenario
one row per required scenario section
one row per scenario input
one row per required gold
one row per required release artifact
one row per release criterion
one reference for each release-blocking known issue that affects a proof obligation
```

Additional linguistic rows depend on project scope.

---

# 90. Template placeholder rules

This template deliberately uses placeholders such as:

```text
<PROJECT_ID>
<MODULE>
<CONTRACT_ID>
<SCENARIO_ID>
<OWNER>
<RELEASE_EFFECT>
<EVIDENCE_LOCATION>
```

Rules:

- placeholders indicate required project decisions;
- do not replace a placeholder by guessing;
- do not retain required placeholders in a release-ready project;
- remove non-applicable rows rather than filling them with misleading values;
- use `OUT_OF_SCOPE` only with a reason;
- template examples are not project coverage evidence.

---

# 91. Coverage review checklist

```text
[ ] Every release claim has a row
[ ] Every project contract has a row
[ ] Every project module has a row
[ ] Every checkpoint has a row
[ ] Every entrypoint has a row
[ ] Every required scenario has a row
[ ] Every required section has a row
[ ] Every required input has a row
[ ] Every required gold has a row
[ ] Every release artifact has a row
[ ] Evidence locations exist
[ ] Known-issue references are explicit where required
[ ] Non-blocking validation limitation is separated from blockers
[ ] Exclusions are documented
[ ] Manual proof obligations name a reviewer role and record type
[ ] Matrix agrees with project.toml
[ ] Matrix agrees with project lock
[ ] Matrix agrees with validation spec
[ ] Matrix agrees with release criteria
```

---

# 92. Coverage anti-patterns

Prohibited:

## 92.1 Test-count coverage

```text
100 tests pass
→ project fully covered
```

A count does not show which contracts or claims are proven.

## 92.2 Top-level-only coverage

```text
release entrypoint compiles
→ all lower modules are covered
```

Checkpoint and provider evidence remain necessary.

## 92.3 Gold-only coverage

```text
gold matches
→ all project behavior is correct
```

Gold covers only declared inputs and normalized output.

## 92.4 Compile-only linguistic coverage

```text
module compiles
→ linguistic behavior is correct
```

Behavioral scenarios are required.

## 92.5 Hidden exclusions

A missing feature is marked not applicable without changing project scope documents.

## 92.6 Stale evidence

Old run evidence is used after source, scenario, input, gold, or toolchain changes.

## 92.7 Placeholder completion

Template rows are left in the active matrix and counted as coverage.

## 92.8 One giant row

All morphology or syntax is represented by one vague row with no representative cases.

## 92.9 Unbounded case enumeration

Thousands of redundant rows are created without equivalence-class policy.

## 92.10 Manual substitution for repeatable proof

A repeatable compile or scenario proof is replaced by informal review.

---

# 93. Balanced coverage policy

The matrix should be detailed enough to prove claims without becoming an unmaintainable copy of every test input.

Use:

```text
one row per stable contract
one row per meaningful feature class
one row per important edge equivalence class
one row per regression
one row per required release gate
```

Do not use:

```text
one row per trivial internal helper
one row per identical lexical item
one row per generated test case
one row per output line
```

Detailed case inventories may live in version-controlled input files referenced by the matrix.

---

# 94. Coverage drift indicators

Probable drift exists when:

- a module exists with no row;
- a row names a missing module;
- a contract has no row;
- a scenario has no purpose row;
- a gold has no scenario row;
- required scenario IDs differ from `project.toml`;
- a row links to a stale entrypoint;
- a source claim has no linguistic proof;
- a release criterion has no evidence row;
- a row uses an obsolete contract;
- a gold changes without affected rows being reviewed;
- a GF version changes without toolchain rows being refreshed;
- a project document claims more support than the matrix;
- required placeholder text remains in a coverage row.

Every detected drift must be resolved before release approval.

---

# 95. Automated checks

The project checker verifies:

```text
coverage IDs unique
required columns present
contract IDs resolve
module paths resolve
scenario IDs resolve
gold paths resolve
input paths resolve
entrypoints resolve
checkpoints resolve
required release criteria mapped
no required placeholder remains
evidence-role references are valid where machine-checkable
```

Canonical command:

```text
gf-wordbench project check --strict
```

The Markdown matrix remains the human-facing normative document.

---

# 97. Coverage review summary

A project or release review summarizes:

```text
Project ID:
Project configuration hash:
Source revision:
GF Wordbench version:
GF version:
RGL revision:
Validation mode:
Run ID:

Release-required coverage IDs:
Checkpoint coverage IDs:
Entrypoint coverage IDs:
Required scenario coverage IDs:
Required gold coverage IDs:
Required artifact coverage IDs:
Known-issue references:
Release decision:
Reviewer:
Review date:
```

The summary references run evidence; it does not update proof obligations in this matrix.

---

# 99. Coverage row template

```markdown
## <COV-ID> — <Coverage claim>

**Requirement:** `RELEASE | CHECKPOINT | DIAGNOSTIC | OPTIONAL | CONDITIONAL`

**Contract**

`<PROJECT_CONTRACT_ID>`

**Provider**

`<PROJECT_RELATIVE_PATH_OR_MODULE>`

**Consumers**

- `<CONSUMER>`;
- `<CONSUMER>`.

**Claim**

`<EXACT_BEHAVIOR_BEING_VALIDATED>`

**Required evidence**

- `<EVIDENCE_TYPE>`;
- `<EVIDENCE_TYPE>`.

**Evidence targets**

- Compile: `<MODULE_OR_ENTRYPOINT>`;
- Scenario: `<SCENARIO_ID>`;
- Input: `<INPUT_FILE_OR_NONE>`;
- Gold/assertion: `<GOLD_OR_ASSERTION>`;
- Artifact: `<ARTIFACT_OR_NONE>`.

**Pass condition**

`<PASS_CONDITION>`

**Evidence location**

`<RUN_ARTIFACT_ROLE_OR_REVIEW_RECORD>`

**Owner**

`<OWNER>`

**Release effect**

`<BLOCKING_CONDITIONAL_OR_NON_BLOCKING>`
```

---

# 100. Construction-family template

```markdown
## <CONSTRUCTION_FAMILY>

**Declared scope**

`<SUPPORTED_BEHAVIOR>`

**Out of scope**

`<EXCLUSIONS>`

**Providers**

- `<MODULE>`;
- `<MODULE>`.

**Contract IDs**

- `<CONTRACT_ID>`.

**Coverage set**

| Case ID | Input/tree | Expected behavior | Scenario section | Negative/edge |
| --- | --- | --- | --- | --- |
| `<CASE_ID>` | `<INPUT>` | `<EXPECTED>` | `<SECTION>` | `<EDGE>` |

**Release interpretation**

`<RULE>`
```

---

# 101. Paradigm-family template

```markdown
## <PARADIGM_FAMILY>

**Provider**

`<MODULE>`

**Public constructors**

- `<CONSTRUCTOR>`;
- `<CONSTRUCTOR>`.

**Input classes**

- `<CLASS>`;
- `<CLASS>`.

**Output dimensions**

- `<FEATURE>`;
- `<FEATURE>`.

**Representative cases**

| Case ID | Lemma/input | Class | Expected table/rule | Scenario section |
| --- | --- | --- | --- | --- |
| `<CASE_ID>` | `<INPUT>` | `<CLASS>` | `<EXPECTED>` | `<SECTION>` |

**Edge cases**

- `<EDGE_CASE>`.

**Scope exclusions**

- `<EXCLUSION_OR_NONE>`.

**Release interpretation**

`<RULE>`
```

---

# 102. Scenario coverage template

```markdown
## Scenario `<SCENARIO_ID>`

**Requirement:** `<LEVEL>`

**Purpose**

`<PURPOSE>`

**Script**

`project/validation/scenarios/<SCENARIO_ID>.gfs`

**Entrypoint**

`<ENTRYPOINT>`

**Inputs**

- `project/validation/inputs/<INPUT_FILE>`.

**Required sections**

| Section ID | Claim | Marker required | Gold/assertion |
| --- | --- | ---: | --- |
| `<SECTION_ID>` | `<CLAIM>` | `<YES_NO>` | `<EVIDENCE>` |

**Gold**

`project/validation/gold/<SCENARIO_ID>.gold` or `not applicable`

**Normalization version**

`<VERSION>`

**Evidence location**

`<RUN_AND_PATH>`

**Release interpretation**

`<BLOCKING_OR_OPTIONAL_RULE>`
```

---

# 103. Release mapping template

```markdown
## Release criterion `<CRITERION_ID>`

**Criterion**

`<RELEASE_REQUIREMENT>`

**Coverage rows**

- `<COV_ID>`;
- `<COV_ID>`.

**Required evidence**

- `<EVIDENCE>`.

**Pass condition**

`<PASS_CONDITION>`

**Release effect**

`<RELEASE_EFFECT>`

**Waiver policy**

`<NOT_WAIVABLE_OR_POLICY>`
```

---

# 104. Project-matrix completion checklist

The active project matrix is complete when:

```text
[ ] Project identity rows are complete
[ ] Source inventory rows are complete
[ ] Every project module has a row
[ ] Every project contract has a row
[ ] Checkpoints are mapped
[ ] Entrypoints are mapped
[ ] Required scenarios are mapped
[ ] Required inputs are mapped
[ ] Required golds are mapped
[ ] Required artifacts are mapped
[ ] Every row defines a pass condition
[ ] Every row defines an evidence location pattern
[ ] Known release blockers are referenced through KNOWN_ISSUES.md
[ ] No required placeholder remains
```

The matrix does not claim that a run has passed. Run and release artifacts provide that evidence.

---

# 105. Release evidence checklist

```text
[ ] Every release-required row maps to retained evidence
[ ] Every mapped pass condition succeeds
[ ] Every project contract reaches its required evidence strength
[ ] Every checkpoint passes
[ ] Every entrypoint passes
[ ] Every required scenario passes
[ ] Every required section completes
[ ] Every required gold matches
[ ] Required PGF evidence passes
[ ] Required manifest and report checks pass
[ ] No unresolved release blocker remains
[ ] Release criteria mapping is complete
[ ] Reviewer and date are recorded in the release decision
```

---

# 106. Definition of coverage-complete

A project is coverage-complete for its declared scope when:

1. every public project contract has a coverage row;
2. every release-reachable module has structural proof;
3. every declared linguistic construction has behavioral proof;
4. every declared morphology family has representative proof;
5. every checkpoint and entrypoint has compatible compile proof in release evidence;
6. every required scenario and section has repeatable proof;
7. every required gold matches;
8. every required release artifact has integrity proof;
9. every release criterion maps to evidence;
10. every release-significant limitation is resolved or explicitly outside declared scope;
11. documentation claims do not exceed evidence;
12. release evidence is compatible with the candidate.

Coverage-complete does not mean the language is universally complete.

It means the project has sufficient evidence for the scope it explicitly claims.

---

# 107. Definition of template-complete

This template is ready for cloning when:

1. all required matrix domains are represented;
2. placeholders are visibly distinguishable;
3. no active language is embedded;
4. example rows are removable;
5. requirement and evidence vocabularies agree with GF Wordbench;
6. release, scenario, gold, artifact, and contract relationships are represented;
7. initialization instructions are explicit;
8. the template does not claim evidence of its own.

---

# 108. Coverage invariants

The completed project coverage matrix preserves:

1. one stable row ID per tracked claim;
2. one authoritative provider per public responsibility;
3. explicit consumers;
4. explicit contract linkage;
5. explicit evidence type;
6. explicit pass condition;
7. explicit evidence location pattern;
8. compile and linguistic proof separation;
9. direct and downstream proof separation;
10. scenario and gold identity agreement;
11. required and optional distinction;
12. no missing evidence interpreted as success;
13. no release claim beyond declared coverage;
14. release criteria mapped to evidence;
15. project configuration and matrix agreement;
16. project contract and matrix agreement;
17. documentation and matrix agreement;
18. deliberate gold updates;
19. PGF and artifact provenance in run evidence;
20. no unresolved required placeholders in the active project;
21. no aggregate score overriding a failed critical proof.

---

# 109. Governing rule

> Coverage is a traceable proof relationship, not a test count.

A language project may claim support only for behavior that this matrix can connect to an owner, a contract, a repeatable validation operation, retained evidence, and an explicit release interpretation.

Everything else is outside declared scope, a known issue, or an unsupported claim.
