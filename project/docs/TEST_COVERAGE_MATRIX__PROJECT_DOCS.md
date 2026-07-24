# GF Wordbench Albanian Project — Test Coverage Matrix

**Document ID:** `GF-WB-SQI-TEST-COVERAGE-MATRIX`  
**Status:** Normative  
**Canonical path:** `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`  
**Project ID:** `sqi`  
**Language:** Albanian  
**Language code:** `sqi`  
**Module suffix:** `Sqi`  
**Project configuration:** `project/project.toml`  
**Owner:** Albanian project maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Document version:** `1.1.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines the required validation coverage for the active Albanian GF project.

It maps project contracts and release obligations to executable evidence:

```text
project configuration checks
source selection checks
static scans
GF module compilation
entrypoint loading
missing-linearization inspection
linearization scenarios
parse scenarios
bounded generation
morphology scenarios
gold comparison
PGF construction
artifact verification
documentation and contract checks
```

The matrix answers:

- what must be validated;
- which module, scenario, contract, or artifact is the subject;
- which validation mode must exercise it;
- which evidence proves coverage;
- whether the proof is required, optional, conditional, or manual;
- which failures block checkpoint or release status;
- what must be reviewed when a provider or consumer changes.

The central rule is:

> A documented requirement is not covered until a repeatable proof exists and its evidence is retained.

---

## 2. What this matrix is not

This file is not a live test-results dashboard.

It does not store:

- the latest `OK`, `FAIL`, `ERROR`, or `SKIPPED` values;
- the latest run ID;
- raw compiler output;
- scenario stdout or stderr;
- gold diffs;
- local GF or RGL paths;
- accepted warnings;
- unsupported implementation status.

Variable execution state belongs in:

```text
run_<run-id>/summary.json
run_<run-id>/manifest.json
run_<run-id>/summary.md
run_<run-id>/AI_READY.md
project/docs/KNOWN_ISSUES.md
```

This matrix defines the stable coverage obligation.

---

## 3. Sources of truth

Coverage requirements are derived from:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

When these documents disagree:

1. stop release validation;
2. identify the authoritative owner;
3. correct the disagreement deliberately;
4. update affected scenarios and gold;
5. rerun the required proof set;
6. update this matrix when the obligation changed.

This matrix belongs to the active Albanian Wordbench project only. It does not define cross-workspace or multilingual portfolio coverage. `gf-portfolio` may consume finalized public Wordbench artifacts but does not alter these project proof obligations.

---

# 4. Coverage vocabulary

## 4.1 Obligation

| Code | Meaning |
|---|---|
| `R` | Required for release |
| `C` | Required for checkpoint validation |
| `Q` | Required for the applicable quick target |
| `D` | Required in diagnostic mode |
| `O` | Optional evidence; failure remains visible |
| `X` | Conditional; required when the feature or contract applies |
| `M` | Manual review where automation cannot prove the criterion |
| `N/A` | Not applicable, with documented justification |

A row may have several codes.

Example:

```text
C/R
```

means required in checkpoint and release modes.

---

## 4.2 Proof type

| Proof type | Meaning |
|---|---|
| `CONFIG` | Configuration or registry validation |
| `EXISTS` | Required path or artifact existence |
| `SCAN` | Deterministic static source scan |
| `COMPILE` | GF `.gf → .gfo` compilation |
| `LOAD` | GF shell import/load |
| `MISSING` | Missing-linearization inspection |
| `LINEARIZE` | Representative abstract-tree linearization |
| `PARSE` | Representative and negative parsing checks |
| `GENERATE` | Bounded generation |
| `MORPHOLOGY` | Inflection or morphological analysis |
| `GOLD` | Normalized output comparison |
| `PGF` | `.pgf` construction and verification |
| `CONTRACT` | Automated interfile or schema contract check |
| `MANUAL` | Reviewed evidence with owner and record |

---

## 4.3 Evidence strength

| Level | Meaning |
|---|---|
| `E1` | Path or configuration assertion only |
| `E2` | Static source or registry validation |
| `E3` | Direct GF compilation or process proof |
| `E4` | Behavioral scenario with explicit assertions |
| `E5` | Behavioral scenario plus reviewed gold |
| `E6` | Clean release build plus artifact manifest and required scenarios |

A higher level does not erase lower-level requirements.

Example:

```text
PGF build success does not replace checkpoint compilation evidence.
```

---

## 4.4 Coverage proof rule

This matrix defines stable proof obligations, not implementation progress or recent execution state.

A proof obligation is satisfied only by the evidence defined in its row. Documentation, configuration or the existence of a scenario file does not by itself prove successful validation.

Execution results remain in run artifacts. Known project defects, limitations and release blockers remain in:

```text
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

---

# 5. Active project baseline

Canonical project identity:

| Field | Value |
|---|---|
| Project ID | `sqi` |
| Display name | `Albanian` |
| Language code | `sqi` |
| Module suffix | `Sqi` |
| Project root | `project/` |
| Source root | `project/lib/src/albanian/` |
| Source glob | `*.gf` |
| Release requires PGF | Yes |

Configured entrypoints:

```text
GrammarSqi.gf
SyntaxSqi.gf
```

Configured checkpoints, in required order:

```text
MorphoSqi.gf
NounSqi.gf
VerbSqi.gf
ExtendSqi.gf
StructuralSqi.gf
```

Required scenarios, in required order:

```text
load
missing
linearize
parse
```

Optional scenarios, in configured order:

```text
generation
morphology
```

---

# 6. Release coverage rule

Release coverage is complete only when all applicable rows marked `R` or `X` satisfy their proof contract.

Release MUST fail when:

- a required configuration check fails;
- a required module or scenario is missing;
- a required checkpoint does not compile;
- a required entrypoint does not compile or load;
- a required scenario is `FAIL`, `ERROR`, or unjustifiably `SKIPPED`;
- required normalized output differs from reviewed gold;
- the required PGF is absent, empty, stale, or unmanifested;
- a release-blocking known issue remains unresolved;
- a required manual review lacks an owner or evidence record.

Optional scenario failures remain visible but affect release only according to `RELEASE_CRITERIA__PROJECT_DOCS.md`.

---

# 7. Configuration and inventory coverage

| ID | Subject | Obligation | Proof | Level | Required assertion | Evidence |
|---|---|---:|---|---:|---|---|
| `TC-CONFIG-001` | `project/project.toml` | C/R/D | CONFIG | E2 | TOML parses as UTF-8 and matches `gf-wordbench.project/1.0` | project-check result |
| `TC-CONFIG-002` | Project identity | C/R/D | CONFIG | E2 | ID `sqi`, language code `sqi`, display name Albanian and root `.` are coherent | project-check result |
| `TC-CONFIG-003` | Source root | C/R/D | CONFIG | E2 | `lib/src/albanian` resolves inside the project and exists | project-check result |
| `TC-CONFIG-004` | Source filters | D/R | CONFIG | E2 | Include and exclude regexes compile and do not exclude required targets | selection result |
| `TC-CONFIG-005` | GF path parts | C/R/D | CONFIG | E2 | Declared order is preserved and all required effective paths resolve | run metadata |
| `TC-CONFIG-006` | Entrypoint registry | C/R | CONFIG | E2 | Both configured entrypoints are unique `.gf` files and exist | registry check |
| `TC-CONFIG-007` | Checkpoint registry | C/R | CONFIG | E2 | Five configured checkpoints exist, are unique and retain declared order | registry check |
| `TC-CONFIG-008` | Scenario registry | C/R/D | CONFIG | E2 | Required and optional IDs are unique and scripts resolve | registry check |
| `TC-CONFIG-009` | Gold registry | R | CONFIG | E2 | Every gold-backed required scenario has one canonical `.gold` file | registry check |
| `TC-CONFIG-010` | Project documentation set | R | EXISTS | E1 | Every mandatory project document exists | contract-check result |
| `TC-CONFIG-011` | Module suffix | C/R/D | CONTRACT | E2 | Active files, scenarios and documentation consistently use `Sqi` | identifier scan |
| `TC-CONFIG-012` | Old-language contamination | R/D | SCAN | E2 | No obsolete active-language identifier remains outside migration history | identifier scan |
| `TC-CONFIG-013` | Duplicate source identity | D/R | CONFIG | E2 | No selected source path or module identity is duplicated | selection result |
| `TC-CONFIG-014` | Machine-specific paths | R | CONTRACT | E2 | `project.toml` contains no GF executable, RGL root or output root | schema validation |
| `TC-CONFIG-015` | Required scenario policy | R | CONTRACT | E2 | UI or state cannot downgrade required scenarios | contract test |

---

# 8. Source-selection coverage

| ID | Selection behavior | Obligation | Proof | Required assertion |
|---|---|---:|---|---|
| `TC-SELECT-001` | Quick explicit target | Q | CONFIG | Exactly one valid in-root `.gf` target is selected |
| `TC-SELECT-002` | Quick missing target | Q | CONFIG | Missing target produces configuration error, not empty success |
| `TC-SELECT-003` | Quick ambiguous basename | Q | CONFIG | Ambiguity produces configuration error |
| `TC-SELECT-004` | Checkpoint order | C/R | CONFIG | Order matches `Morpho`, `Noun`, `Verb`, `Extend`, `Structural` |
| `TC-SELECT-005` | Release ordered union | R | CONFIG | Checkpoints precede new entrypoints; duplicates are removed |
| `TC-SELECT-006` | Diagnostic recursive selection | D | CONFIG | All accepted `.gf` candidates beneath source root are enumerated deterministically |
| `TC-SELECT-007` | Exclude precedence | D/R | CONFIG | Exclusion wins when include and exclude both match |
| `TC-SELECT-008` | Required target exclusion | C/R | CONFIG | Excluded checkpoint or entrypoint causes configuration failure |
| `TC-SELECT-009` | Outside-root target | Q/C/R/D | CONFIG | Resolved paths outside source root are rejected |
| `TC-SELECT-010` | Diagnostic `max_files` | D | CONFIG | Limit applies after filtering and sorted overflow is recorded |
| `TC-SELECT-011` | Release completeness | R | CONFIG | `max_files` cannot truncate release targets |
| `TC-SELECT-012` | Path with spaces | Q/C/R/D | CONFIG | Parent-directory spaces are supported even though active filenames are filtered by project policy |

---

# 9. Generic per-source proof

Every source selected in diagnostic mode must receive the following baseline proof.

| ID | Criterion | Obligation | Proof | Level | Release effect |
|---|---|---:|---|---:|---|
| `TC-SOURCE-001` | Source is readable UTF-8 under project policy | D/R | SCAN | E2 | Error when unreadable |
| `TC-SOURCE-002` | Filename and expected module identity are coherent | D/R | CONTRACT/COMPILE | E3 | Failure when incoherent |
| `TC-SOURCE-003` | Static scan completes | D/R | SCAN | E2 | Scan error blocks reliable validation |
| `TC-SOURCE-004` | Source fingerprint is recorded | D/R | CONTRACT | E2 | Required for stale-artifact evidence |
| `TC-SOURCE-005` | GF process evidence is retained | Q/C/R/D | COMPILE | E3 | Required for compile claim |
| `TC-SOURCE-006` | stdout and stderr are separate | Q/C/R/D | CONTRACT | E3 | Missing evidence invalidates result |
| `TC-SOURCE-007` | Current-run `.gfo` is verified when required | C/R | COMPILE | E3 | Missing/stale artifact blocks gate |
| `TC-SOURCE-008` | Failure is classified | Q/C/R/D | CONTRACT | E3 | Must be `direct`, `downstream`, or `ambiguous` |
| `TC-SOURCE-009` | No source modification occurs | Q/C/R/D | CONTRACT | E2 | Modification is framework error |
| `TC-SOURCE-010` | Artifact is registered | R | CONTRACT | E6 | Unmanifested required artifact blocks release |

---

# 10. Checkpoint module coverage

Checkpoint order is a dependency-oriented release contract.

Every checkpoint must compile from clean run-owned artifact directories before entrypoint validation.

## 10.1 `MorphoSqi.gf`

| ID | Coverage target | Obligation | Proof | Level | Required assertion |
|---|---|---:|---|---:|---|
| `TC-MORPHO-001` | Direct module compilation | C/R | COMPILE | E3 | Exit succeeds, no fatal diagnostic, current `.gfo` exists |
| `TC-MORPHO-002` | Static source integrity | C/R/D | SCAN | E2 | Scanner completes and findings remain separate from compile status |
| `TC-MORPHO-003` | Morphology provider contract | C/R | CONTRACT | E2 | Public parameters, tables and helper ownership agree with project specs |
| `TC-MORPHO-004` | Nominal inflection evidence | X/R | MORPHOLOGY/GOLD | E5 | Representative noun/adjective forms follow approved paradigms |
| `TC-MORPHO-005` | Verbal inflection evidence | X/R | MORPHOLOGY/GOLD | E5 | Representative verb forms include regular and documented irregular behavior |
| `TC-MORPHO-006` | Deterministic normalization | R | GOLD | E5 | Orthographically meaningful output is preserved |

Coverage notes:

- the optional `morphology` scenario is the preferred behavioral proof;
- if it remains optional, required morphology assertions must be covered by another required scenario or documented release proof;
- direct compile evidence alone does not prove linguistic inflection quality.

---

## 10.2 `NounSqi.gf`

| ID | Coverage target | Obligation | Proof | Level | Required assertion |
|---|---|---:|---|---:|---|
| `TC-NOUN-001` | Direct module compilation | C/R | COMPILE | E3 | Current `.gfo` exists and compile evidence is retained |
| `TC-NOUN-002` | Lincat-field use | C/R | CONTRACT | E2 | Only fields declared by category providers are consumed |
| `TC-NOUN-003` | Agreement behavior | R | LINEARIZE/GOLD | E5 | Number, gender, case and definiteness behave as specified |
| `TC-NOUN-004` | Determiner/noun composition | R | LINEARIZE/GOLD | E5 | Representative determiner and common-noun constructions are non-empty and correct |
| `TC-NOUN-005` | Pronoun or NP behavior | X/R | LINEARIZE/PARSE | E4/E5 | Required NP functions round-trip or satisfy explicit one-way expectations |
| `TC-NOUN-006` | Negative coverage | R | PARSE | E4 | At least one invalid or unsupported nominal form is rejected where specified |

---

## 10.3 `VerbSqi.gf`

| ID | Coverage target | Obligation | Proof | Level | Required assertion |
|---|---|---:|---|---:|---|
| `TC-VERB-001` | Direct module compilation | C/R | COMPILE | E3 | Current `.gfo` exists and compile evidence is retained |
| `TC-VERB-002` | Verb morphology contract | C/R | CONTRACT | E2 | Verb constructors consume documented morphology providers |
| `TC-VERB-003` | Tense/person/number coverage | R | LINEARIZE/GOLD | E5 | Representative finite forms cover configured agreement dimensions |
| `TC-VERB-004` | Complement behavior | R | LINEARIZE/PARSE | E4/E5 | Transitive/intransitive and other required complement patterns behave as specified |
| `TC-VERB-005` | Negation or polarity | X/R | LINEARIZE/GOLD | E5 | Required polarity constructions preserve intended placement and agreement |
| `TC-VERB-006` | Irregular behavior coverage | R | MORPHOLOGY/CONTRACT | E4 | Documented irregular forms are exercised by explicit assertions |

---

## 10.4 `ExtendSqi.gf`

| ID | Coverage target | Obligation | Proof | Level | Required assertion |
|---|---|---:|---|---:|---|
| `TC-EXTEND-001` | Direct module compilation | C/R | COMPILE | E3 | Current `.gfo` exists and compile evidence is retained |
| `TC-EXTEND-002` | Inheritance policy | C/R | CONTRACT | E2 | Inherited, overridden and subtracted symbols match the documented registry |
| `TC-EXTEND-003` | Override compatibility | R | COMPILE/LINEARIZE | E4 | Local overrides preserve abstract signatures and required output |
| `TC-EXTEND-004` | No duplicate upstream behavior | R/M | CONTRACT/MANUAL | E2 | Override rationale is recorded where behavior already exists upstream |
| `TC-EXTEND-005` | Downstream entrypoint coverage | R | COMPILE/LOAD | E4 | Both configured entrypoints remain compatible |
| `TC-EXTEND-006` | Override ownership | R | CONTRACT | E2 | Every local override has one documented owner, rationale and consumer contract |

---

## 10.5 `StructuralSqi.gf`

| ID | Coverage target | Obligation | Proof | Level | Required assertion |
|---|---|---:|---|---:|---|
| `TC-STRUCT-001` | Direct module compilation | C/R | COMPILE | E3 | Current `.gfo` exists and compile evidence is retained |
| `TC-STRUCT-002` | Structural category correctness | C/R | CONTRACT | E2 | Entries expose intended GF categories |
| `TC-STRUCT-003` | Prepositions | R | LINEARIZE/PARSE/GOLD | E5 | Required complement or case behavior is preserved |
| `TC-STRUCT-004` | Pronouns | R | LINEARIZE/PARSE/GOLD | E5 | Person, number, gender and agreement dimensions are represented |
| `TC-STRUCT-005` | Determiners | R | LINEARIZE/GOLD | E5 | Definiteness and agreement follow project policy |
| `TC-STRUCT-006` | Conjunctions | R | LINEARIZE/GOLD | E5 | Coordination structure is preserved |
| `TC-STRUCT-007` | Structural entry completeness | R | SCAN/CONTRACT | E2 | Required structural entries contain no placeholder or fallback implementation |
| `TC-STRUCT-008` | No consumer reconstruction | R/M | CONTRACT/MANUAL | E2 | Consumers do not duplicate structural entries independently |

---

# 11. Entrypoint coverage

## 11.1 `GrammarSqi.gf`

| ID | Coverage target | Obligation | Proof | Level | Required assertion |
|---|---|---:|---|---:|---|
| `TC-GRAMMAR-001` | Direct compilation | C/R | COMPILE | E3 | Compile completes and current `.gfo` exists |
| `TC-GRAMMAR-002` | Dependency closure | C/R | COMPILE | E3 | Every required concrete component resolves |
| `TC-GRAMMAR-003` | Shell load | C/R | LOAD | E4 | Grammar imports without fatal diagnostic |
| `TC-GRAMMAR-004` | Missing linearizations | R | MISSING/GOLD | E5 | Missing-function output satisfies project release threshold |
| `TC-GRAMMAR-005` | Representative linearization | C/R | LINEARIZE/GOLD | E5 | Required trees produce reviewed non-empty Albanian output |
| `TC-GRAMMAR-006` | Representative parse | R | PARSE/GOLD | E5 | Required positive and negative cases satisfy declared ambiguity policy |
| `TC-GRAMMAR-007` | PGF participation | R | PGF | E6 | Entrypoint participates in the configured PGF build |
| `TC-GRAMMAR-008` | Artifact registration | R | CONTRACT | E6 | `.gfo`, logs and PGF-related evidence are manifested |

---

## 11.2 `SyntaxSqi.gf`

| ID | Coverage target | Obligation | Proof | Level | Required assertion |
|---|---|---:|---|---:|---|
| `TC-SYNTAX-001` | Direct compilation | C/R | COMPILE | E3 | Compile completes and current `.gfo` exists |
| `TC-SYNTAX-002` | Public API availability | C/R | LOAD/CONTRACT | E4 | Required syntax/API operations remain available |
| `TC-SYNTAX-003` | Constructor behavior | R | LINEARIZE/GOLD | E5 | Representative public constructor combinations produce expected output |
| `TC-SYNTAX-004` | Parse API behavior | R | PARSE/GOLD | E5 | Required parse cases work through the configured API entrypoint |
| `TC-SYNTAX-005` | PGF participation | R | PGF | E6 | Entrypoint is included when required by the PGF build policy |
| `TC-SYNTAX-006` | Application smoke coverage | X/R | LOAD/LINEARIZE/PARSE | E4 | Application-facing use cases pass when this is the application entrypoint |

---

# 12. Scenario coverage matrix

## 12.1 Required scenarios

| Scenario ID | Script | Policy | Modes | Primary proof | Gold | Required assertions | Release effect |
|---|---|---:|---|---|---|---|---|
| `load` | `validation/scenarios/load.gfs` | R | checkpoint/release | LOAD | Optional | Configured entrypoint loads; markers complete; no fatal diagnostic | Any failure blocks release |
| `missing` | `validation/scenarios/missing.gfs` | R | release | MISSING | `validation/gold/missing.gold` | Missing-linearization inventory is complete and within approved threshold | Mismatch or missing gold blocks release |
| `linearize` | `validation/scenarios/linearize.gfs` | R | checkpoint/release | LINEARIZE | `validation/gold/linearize.gold` | Representative trees produce reviewed Albanian forms; no empty required output | Failure or mismatch blocks release |
| `parse` | `validation/scenarios/parse.gfs` | R | release | PARSE | `validation/gold/parse.gold` | Positive, ambiguity and negative expectations are explicit and satisfied | Failure or mismatch blocks release |

Required scenario invariants:

```text
[ ] script exists
[ ] scenario ID matches project.toml
[ ] loaded entrypoint is configured
[ ] GF command set is supported
[ ] execution timeout is finite
[ ] required begin/end markers complete
[ ] raw stdout and stderr are retained
[ ] normalized output is retained
[ ] gold comparison occurs after normalization
[ ] ordinary execution does not modify gold
[ ] ScenarioResult is written
[ ] required evidence is manifested
```

---

## 12.2 Optional scenarios

| Scenario ID | Script | Policy | Modes | Primary proof | Gold | Required assertions | Release treatment |
|---|---|---:|---|---|---|---|---|
| `generation` | `validation/scenarios/generation.gfs` | O | diagnostic/release | GENERATE | Optional | Generation is bounded by count/depth/category; all required outputs are usable | Failure remains visible; gate follows release criteria |
| `morphology` | `validation/scenarios/morphology.gfs` | O | diagnostic/release | MORPHOLOGY | Recommended | Representative nominal and verbal forms satisfy morphology specification | Failure remains visible; may become blocking when required morphology has no other proof |

Optional does not mean unvalidated.

Every optional scenario still requires:

- valid registration;
- deterministic execution order;
- finite timeout;
- complete markers;
- explicit assertions;
- retained evidence;
- no silent gold update.

---

# 13. Scenario assertion coverage

| ID | Assertion family | Applies to | Obligation | Minimum evidence |
|---|---|---|---:|---|
| `TC-SCENARIO-001` | Process launch | all scenarios | R/O | execution state and command |
| `TC-SCENARIO-002` | Timeout | all scenarios | R/O | finite timeout and preserved partial output |
| `TC-SCENARIO-003` | Marker completion | all scenarios | R/O | expected section list and completion status |
| `TC-SCENARIO-004` | Fatal diagnostics | all scenarios | R/O | normalized diagnostic result |
| `TC-SCENARIO-005` | Empty output | linearize/generation/morphology | R/O | explicit non-empty assertion |
| `TC-SCENARIO-006` | Parse count | parse | R | expected range or exact count |
| `TC-SCENARIO-007` | Expected tree | parse | R | tree-present assertion where applicable |
| `TC-SCENARIO-008` | Negative parse | parse | R | no-parse assertion for declared negative cases |
| `TC-SCENARIO-009` | Missing inventory | missing | R | normalized inventory and threshold |
| `TC-SCENARIO-010` | Gold match | gold-backed scenarios | R/O | normalized byte or canonical semantic comparison |
| `TC-SCENARIO-011` | Required artifact | artifact-producing scenario | X | existence, non-empty check and manifest entry |
| `TC-SCENARIO-012` | Explicit termination | all applicable scripts | R/O | script ends with supported termination command |
| `TC-SCENARIO-013` | Script immutability | all scenarios | R/O | pre/post fingerprint or read-only contract |
| `TC-SCENARIO-014` | Gold immutability | all normal runs | R | pre/post fingerprint or contract test |

---

# 14. Linguistic capability coverage

This section maps broad linguistic obligations to the configured project proof set.

It does not define the detailed linguistic expectation; the project specifications own that detail.

| Capability | Primary providers | Compile proof | Behavioral proof | Gold expectation | Release obligation |
|---|---|---|---|---|---:|
| Core morphology | `MorphoSqi.gf` | checkpoint compile | `morphology`, `linearize` | representative forms | R |
| Nominal syntax | `NounSqi.gf` | checkpoint compile | `linearize`, `parse` | noun phrase forms and parses | R |
| Verbal syntax | `VerbSqi.gf` | checkpoint compile | `linearize`, `parse`, optional `morphology` | clauses and inflection | R |
| Structural lexicon | `StructuralSqi.gf` | checkpoint compile | `linearize`, `parse` | function-word behavior | R |
| Extension layer | `ExtendSqi.gf` | checkpoint compile | `load`, `linearize`, targeted family cases | changed output only when intentional | R |
| Concrete grammar | `GrammarSqi.gf` | entrypoint compile | all required scenarios | required gold set | R |
| Syntax/API surface | `SyntaxSqi.gf` | entrypoint compile | load/linearize/parse smoke paths | API-relevant output | R/X |
| Missing implementations | release grammar | entrypoint compile | `missing` | `missing.gold` | R |
| Bounded generation | release grammar | entrypoint compile | `generation` | optional/deterministic projection | O |
| Runtime grammar | configured entrypoints | all required compiles | required scenarios | release evidence | R |

---

# 15. Positive, negative and boundary coverage

Every linguistic family represented in required scenarios SHOULD include:

```text
at least one positive case
at least one boundary or irregular case
at least one negative or rejection case where meaningful
```

## 15.1 Positive cases

Examples:

- valid noun phrase linearizes;
- valid clause linearizes;
- expected phrase parses;
- regular inflection table contains required form;
- configured grammar loads.

## 15.2 Boundary cases

Examples:

- irregular morphology;
- agreement change;
- definiteness contrast;
- singular/plural contrast;
- ambiguous parse with declared allowed count;
- optional constructor path;
- empty lexical or structural edge explicitly prohibited.

## 15.3 Negative cases

Examples:

- invalid phrase produces no parse;
- missing implementation remains visible;
- absent marker fails scenario;
- excluded backup source is not selected;
- stale `.gfo` does not satisfy current run;
- missing gold is not accepted;
- unsupported GF command is not success.

---

# 16. Contract coverage matrix

| Contract ID | Relationship | Proof obligation | Primary evidence | Release |
|---|---|---|---|---:|
| `PIFC-CONFIG-001` | `project.toml` → source tree | paths, targets and scenarios resolve | project contract check | R |
| `PIFC-CONFIG-002` | project identity → `Sqi` suffix | suffix consistency | identifier scan | R |
| `PIFC-MODULE-001` | abstract → concrete syntax | signature and missing coverage | compile + missing scenario | R |
| `PIFC-MODULE-002` | category provider → syntax consumers | lincat field compatibility | checkpoint and entrypoint compile | R |
| `PIFC-MODULE-003` | morphology → paradigms/consumers | form construction and helper ownership | compile + morphology/linearize | R |
| `PIFC-MODULE-004` | paradigms → lexicon | constructor compatibility | diagnostic compile + project review | X |
| `PIFC-MODULE-005` | structural → entrypoints | category and composition integrity | compile + linearize/parse | R |
| `PIFC-MODULE-006` | extension providers → coordinator | inheritance/override compatibility | Extend compile + family scenarios | X |
| `PIFC-MODULE-007` | interface → instance | exact implementation contract | direct compile | X |
| `PIFC-LINCAT-001` | categories → lincat consumers | field and meaning stability | compile + contract review | R |
| `PIFC-LINCAT-002` | parameters → pattern consumers | exhaustive/valid parameter use | compile + generation/linearization | R |
| `PIFC-HELPER-001` | helper providers → consumers | one owner and compatible type | helper registry + compile | R |
| `PIFC-ENTRY-001` | grammar entrypoint → scenarios/release | load and compile | `load` + compile | R |
| `PIFC-ENTRY-002` | API entrypoint → application use | smoke behavior | Syntax compile + scenarios | X |
| `PIFC-ENTRY-003` | release entrypoints → PGF | clean PGF build | PGF artifact and manifest | R |
| `PIFC-SCENARIO-001` | registry → `.gfs` files | unique and complete registration | scenario registry check | R |
| `PIFC-SCENARIO-002` | scenario → entrypoint | configured target is loaded | scenario raw evidence | R |
| `PIFC-SCENARIO-003` | scenario → inputs | every input exists and is versioned | input registry check | X |
| `PIFC-SCENARIO-004` | scenario → markers | all required sections complete | ScenarioResult sections | R |
| `PIFC-GOLD-001` | scenario output → gold | normalized comparison | gold diff/result | R where configured |
| `PIFC-GOLD-002` | implementation change → gold update | explicit reviewed update | decision/review record | R |
| `PIFC-ARTIFACT-001` | `.gf` → `.gfo` | current-run object proof | compile artifact | R |
| `PIFC-ARTIFACT-002` | entrypoints → `.pgf` | runtime artifact proof | PGF build | R |
| `PIFC-ARTIFACT-003` | validation → evidence | complete artifact inventory | manifest | R |
| `PIFC-DOC-001` | architecture → module ownership | documentation matches source | documentation review/check | R |
| `PIFC-DOC-002` | category contract → lincats | documented fields match consumers | contract review + compile | R |
| `PIFC-DOC-003` | validation spec → scenarios | each criterion has evidence | this matrix + registry check | R |
| `PIFC-DOC-004` | known issues → source and validation | no hidden blocker or unsupported fallback | known-issue and contract review | R |
| `PIFC-DOC-005` | decision log → breaking changes | significant changes recorded | release review | R |
| `PIFC-RELEASE-001` | checkpoints → entrypoints | all checkpoints pass first | release pipeline | R |
| `PIFC-RELEASE-002` | required scenarios → release | all required scenarios pass | release pipeline | R |
| `PIFC-RELEASE-003` | known issues → decision | blockers resolved or exception approved | release review | R |

---

# 17. Artifact coverage

| ID | Artifact | Obligation | Producer | Required checks |
|---|---|---:|---|---|
| `TC-ART-001` | Compile stdout | C/R/D | compiler | exists, attributable to target, manifested when retained |
| `TC-ART-002` | Compile stderr | C/R/D | compiler | exists, attributable to target, manifested when retained |
| `TC-ART-003` | Scan log | D/R | scanner | exists for scanned file or explicit structured replacement |
| `TC-ART-004` | Target `.gfo` | C/R | GF compiler | exists, non-empty, current-run provenance, hash |
| `TC-ART-005` | Scenario stdout | R/O | scenario runner | raw output retained before normalization |
| `TC-ART-006` | Scenario stderr | R/O | scenario runner | raw output retained before normalization |
| `TC-ART-007` | Normalized scenario output | R/O | scenario runner | normalization version recorded |
| `TC-ART-008` | Gold diff or result | R where gold-backed | comparator | match status and evidence retained |
| `TC-ART-009` | Release `.pgf` | R | PGF builder | exists, non-empty, expected languages/functions, hash |
| `TC-ART-010` | `summary.json` | R | JSON reporter | valid schema and complete result arrays |
| `TC-ART-011` | `summary.md` | R | Markdown reporter | derives facts from `RunResult` |
| `TC-ART-012` | `AI_READY.md` | R on failure | AI reporter | bounded, evidence-linked, no rerun |
| `TC-ART-013` | `manifest.json` | R | manifest writer | complete deterministic inventory with hashes |
| `TC-ART-014` | `top_errors.txt` | R on failure | aggregate reporter | deterministic normalized aggregation |

---

# 18. PGF release coverage

Because:

```toml
release_requires_pgf = true
```

the following are mandatory.

| ID | Criterion | Obligation | Proof |
|---|---|---:|---|
| `TC-PGF-001` | All configured checkpoints pass | R | release pipeline |
| `TC-PGF-002` | Both configured entrypoints compile | R | compile results |
| `TC-PGF-003` | PGF command uses documented entrypoints | R | recorded command |
| `TC-PGF-004` | Build runs from explicit working directory | R | process result |
| `TC-PGF-005` | Build completes without timeout | R | execution state |
| `TC-PGF-006` | Exit policy passes | R | process result |
| `TC-PGF-007` | No fatal build diagnostic | R | normalized diagnostics |
| `TC-PGF-008` | Expected `.pgf` exists | R | artifact check |
| `TC-PGF-009` | PGF is non-empty | R | artifact check |
| `TC-PGF-010` | PGF belongs to current run | R | run provenance |
| `TC-PGF-011` | Required concrete language is present | R | PGF inspection/load |
| `TC-PGF-012` | Required functions are available | R | smoke scenario/introspection |
| `TC-PGF-013` | PGF is registered with SHA-256 | R | manifest |
| `TC-PGF-014` | Source and gold remain unchanged | R | immutability check |

---

# 19. Validation-mode coverage

## 19.1 Quick mode

Minimum proof:

```text
explicit target resolution
static scan
source fingerprint
target compile unless explicitly disabled
raw evidence
structured FileResult
```

Quick mode is not a release proof.

---

## 19.2 Checkpoint mode

Minimum proof:

```text
project configuration validation
five checkpoint modules in declared order
current-run `.gfo` checks
failure classification
load scenario
linearize scenario
required evidence and reports
```

Checkpoint mode may stop release work early but does not replace release mode.

---

## 19.3 Release mode

Minimum proof:

```text
strict project and contract validation
all checkpoints
both entrypoints
required scenarios
required gold comparisons
PGF build
artifact manifest
known-issue review
release summary
```

No diagnostic file limit is allowed.

---

## 19.4 Diagnostic mode

Minimum proof:

```text
recursive selected source set
static scan of every selected source
compile attempt for every selected source unless explicitly disabled
classification of all failures
optional scenarios according to configuration
complete evidence
```

Diagnostic mode maximizes evidence but does not automatically waive release rules.

---

# 20. Framework contract tests supporting project coverage

Project proof depends on framework behavior.

The framework test suite must cover at least:

```text
project.toml parsing
source-root containment
entrypoint/checkpoint ordering
scenario registry validation
required/optional distinction
file selection
compile command construction
timeout behavior
stdout/stderr separation
current-run `.gfo` verification
diagnostic parsing
direct/downstream classification
ScenarioResult construction
marker validation
gold comparison
gold immutability
PGF artifact verification
manifest writing
summary schema
legacy migration
CLI/GUI configuration equivalence
```

These tests prove the framework can execute project validation correctly.

They do not prove Albanian linguistic correctness.

---

# 21. Manual review coverage

Automation cannot prove every linguistic or architectural property.

Required manual reviews:

| ID | Review | Frequency | Owner | Required record |
|---|---|---|---|---|
| `TC-MANUAL-001` | Linguistic correctness of changed gold | every gold update | Albanian maintainer | review/decision record |
| `TC-MANUAL-002` | Public lincat compatibility | lincat change | module owners | contract update |
| `TC-MANUAL-003` | Override necessity in `ExtendSqi.gf` | override change | extension owner | contract or decision record |
| `TC-MANUAL-004` | Structural lexical category correctness | structural change | structural owner | review record |
| `TC-MANUAL-005` | Release-significant known issues | every release | release owner | release decision |
| `TC-MANUAL-006` | Dependency map accuracy | architecture change | project maintainer | document review |
| `TC-MANUAL-007` | Scenario representativeness | scenario change/release | validation owner | validation-spec review |
| `TC-MANUAL-008` | GF/RGL upgrade output | toolchain upgrade | project + release owners | compatibility review |

A manual review without named evidence is not completed coverage.

---

# 22. Coverage gaps

A gap exists when any of the following is true:

```text
required criterion has no proof producer
required module is absent from configuration
required scenario is absent
scenario has no assertions
gold-backed scenario has no gold
gold exists without a registered scenario
required linguistic behavior appears only in an optional scenario
configured entrypoint is not loaded by required scenarios
checkpoint has no direct compile proof
PGF build has no artifact check
contract has no validation row
manual criterion has no owner
known blocker or unsupported fallback is absent from `KNOWN_ISSUES.md`
latest release evidence used a different project identity or module suffix
```

Every gap is recorded in:

```text
project/docs/KNOWN_ISSUES.md
```

with its affected contract, required correction and release impact.

A gap is not closed by adding a row to this matrix. It is closed only when the required proof passes and retained evidence confirms the correction.

---

# 23. Coverage completeness checks

The project contract checker verifies this matrix against configuration and files.

Canonical checks:

```text
every configured checkpoint appears in this matrix
every configured entrypoint appears in this matrix
every required scenario appears in this matrix
every optional scenario appears in this matrix
every gold file maps to one scenario
every required gold-backed scenario has one gold file
every active project contract has at least one proof row
every release artifact has a verification row
no obsolete module suffix appears
no duplicate test-coverage ID exists
all referenced documents exist
```

Canonical command:

```text
gf-wordbench project check --strict
```

---

# 24. Evidence update protocol

After every checkpoint or release run:

1. retain the complete run directory;
2. inspect `summary.json`;
3. verify required `FileResult` and `ScenarioResult` entries;
4. inspect direct and ambiguous failures before downstream failures;
5. verify required artifact manifest entries;
6. review gold differences explicitly;
7. update `KNOWN_ISSUES.md` when a defect, limitation or release blocker changes;
8. update this matrix only when the required proof set changes;
9. record release evidence in the release decision.

Do not paste transient execution results into this matrix.

---

# 25. Change-impact rules

## 25.1 Provider change

When a provider changes:

```text
[ ] direct compile proof rerun
[ ] direct consumers identified
[ ] downstream checkpoints rerun
[ ] both entrypoints reviewed
[ ] relevant scenarios rerun
[ ] relevant gold reviewed
[ ] contract rows reviewed
[ ] dependency map reviewed
[ ] release impact classified
```

## 25.2 New module

A new project module requires:

```text
configuration decision
dependency-map entry
ownership documentation
direct compile proof
consumer compile proof
entrypoint impact review
scenario coverage decision
matrix row
```

## 25.3 New scenario

A new scenario requires:

```text
unique scenario ID
project.toml registration
script
mode and required/optional policy
marker contract
assertions
timeout
input registry
gold decision
ScenarioResult coverage
matrix row
validation-spec update
```

## 25.4 Gold change

A gold change requires:

```text
intentional source/specification reason
normalized-output diff
linguistic review
normalization-version review
release-impact review
decision or review record
```

## 25.5 Entry point change

An entrypoint rename, addition or removal requires:

```text
project.toml update
project contract update
scenario update
PGF build update
artifact naming review
dependency-map update
matrix update
project-version impact review
```

---

# 26. Required release evidence bundle

The release evidence bundle must contain or reference:

```text
strict project-check result
contract-check result
GF version
RGL revision or release
source commit
project configuration hash
checkpoint FileResults
entrypoint FileResults
required ScenarioResults
normalized scenario outputs
required gold results
PGF build result
PGF hash
manifest
summary.json
summary.md
AI_READY.md when failures or accepted exceptions exist
known-issues review
release decision
```

A release claim without this evidence bundle is incomplete.

---

# 27. Exit criteria by layer

## 27.1 Configuration layer

Complete when:

```text
all required paths, targets, scenarios and documents resolve
```

## 27.2 Checkpoint layer

Complete when:

```text
all five configured checkpoint modules pass direct compile and artifact checks
```

## 27.3 Entrypoint layer

Complete when:

```text
GrammarSqi.gf and SyntaxSqi.gf pass compile and load checks
```

## 27.4 Scenario layer

Complete when:

```text
load, missing, linearize and parse pass all assertions and required gold comparisons
```

## 27.5 Artifact layer

Complete when:

```text
required `.gfo` and `.pgf` artifacts are current, non-empty and manifested
```

## 27.6 Release layer

Complete when:

```text
every required row in this matrix is covered
no unapproved release blocker remains
the release evidence bundle is complete
```

---

# 28. Acceptance criteria for this matrix

This matrix is valid when:

```text
[ ] project identity matches project.toml
[ ] configured source root matches project.toml
[ ] every checkpoint is listed once
[ ] every entrypoint is listed once
[ ] every scenario is listed once
[ ] required and optional policy matches project.toml
[ ] release PGF policy matches project.toml
[ ] contract IDs match the project lock
[ ] proof types use the canonical vocabulary
[ ] every required proof has an evidence location
[ ] transient statuses are not stored here
[ ] manual criteria name an owner and record
[ ] no placeholder remains
[ ] no obsolete active-language name remains
[ ] documentation cross-references resolve
```

---

# 29. Anti-drift indicators

Coverage drift exists when:

- `project.toml` adds a checkpoint not listed here;
- a configured entrypoint disappears from the matrix;
- a required scenario is marked optional here;
- a scenario script changes purpose without matrix review;
- a gold file has no matrix row;
- a linguistic contract relies only on compilation;
- a required behavior is tested only by an optional scenario;
- PGF is required by configuration but omitted from release coverage;
- a source provider changes without consumer coverage;
- framework unit tests are cited as proof of Albanian linguistic correctness;
- historical fixture results are presented as current project results;
- `KNOWN_ISSUES.md` and this matrix disagree about a missing proof;
- a release uses evidence from another project ID, language code or module suffix;
- a manual review is claimed without a retained record.

Any drift blocks release until corrected or explicitly accepted through the release decision.

---

# 30. Cross-references

| Topic | Document |
|---|---|
| Documentation alignment | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Single active project | `docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md` |
| Active project configuration | `project/project.toml` |
| Project contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Language architecture | `project/docs/LANGUAGE_ARCHITECTURE.md` |
| Module dependencies | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Category and lincat rules | `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md` |
| Morphology expectations | `project/docs/MORPHOLOGY_SPEC.md` |
| Syntax expectations | `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Validation semantics | `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md` |
| Known issues | `project/docs/KNOWN_ISSUES.md` |
| Release gates | `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` |
| Project decisions | `project/docs/DECISION_LOG.md` |
| Framework file selection | `docs/validation/FILE_SELECTION.md` |
| GF compilation | `docs/gf/GF_COMPILATION.md` |
| Error classification | `docs/diagnostics/ERROR_CLASSIFICATION.md` |
| Scenario result decision | `docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md` |
| Project schema | `docs/configuration/PROJECT_TOML_REFERENCE.md` |

---

# 31. Governing rule

> Coverage is a relationship between a requirement and retained evidence.

A module name in configuration is not proof.

A scenario file is not proof until it executes and its assertions pass.

A zero process exit is not proof when markers, gold, or artifacts are missing.

A release is covered only when every required project contract has a repeatable proof and the complete evidence is retained.
