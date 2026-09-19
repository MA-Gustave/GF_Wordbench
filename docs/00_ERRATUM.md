# GF Wordbench — Erratum documentaire

**Document ID:** `GF-WB-DOC-ERRATUM-2026-07-23`  
**Status:** Actif — temporaire  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\ERRATUM.md`  
**Applies to:** snapshot documentaire généré le `2026-07-22` et fichiers déplacés le `2026-07-23`  
**Owner:** GF Wordbench maintainers  
**Created:** `2026-07-23`  
**Retirement condition:** toutes les corrections ci-dessous sont intégrées dans leurs fichiers propriétaires et validées par un nouvel audit documentaire.

---


## ADR-0015 alignment — interpretation of legacy project material

The current runtime starts from a user-selected GF source file or RGL language directory and constructs a `ResolvedLanguageContext`. A root `project/` directory and `project/project.toml` are not required.

This document may retain `project/`, `templates/validation-profile/`, “active project” or project-owned path examples only when describing a legacy source layout, a migration fixture or a deprecated contract. Their current replacements are:

- selected language sources remain in their original RGL or GF source tree;
- optional validation policy lives in an explicitly loaded validation profile;
- the reusable profile template lives under `templates/validation-profile/`;
- run outputs live under the configured output root and never own or copy the source language tree.

---
## 1. Purpose

This erratum centralizes known corrections and omissions discovered after assembly of the GF Wordbench documentation tree.

Until it is retired:

> When this erratum conflicts with an affected document, this erratum is authoritative for the correction described here.

This file does not replace the permanent owner documents. It records temporary corrections so the repository can remain understandable while the affected files are repaired.

---

## 2. Files intentionally excluded from this erratum

This erratum does not govern:

```text
README.md files that were intentionally ignored during the first bulk move
docs/release/VERSIONING_POLICY.md
```

The three validation README files subsequently moved into place are recorded in Section 3.

---

## 3. Files moved after the original snapshot

The following files were absent from the original assembled snapshot and were later moved into their canonical destinations:

```text
project/validation/scenarios/README.md
templates/validation-profile/validation/README.md
templates/validation-profile/validation/gold/README.md
```

They must be included in the next repository snapshot and checked for:

```text
UTF-8 without BOM
LF newlines
complete Markdown structure
valid internal links
no unresolved required placeholder in the active project file
placeholders only where intentional in template files
```

---

## 4. Missing file to create

The following canonical document is missing and must be created:

```text
docs/architecture/DATA_MODEL.md
```

It must define at least:

```text
AppConfig
ProjectConfig
RunConfig
RunPaths
ProcessResult
CompileSummary
FileResult
ScenarioResult
DiffEntry
RunResult
ArtifactRecord or ArtifactEntry
status values
execution states
diagnostic classes
error kinds
runtime-path versus persisted-path rules
serialization ownership
model-evolution rules
```

Until that file exists, references to `docs/architecture/DATA_MODEL.md` point to an unresolved document.

---

## 5. Incorrect documentation references

### 5.1 `docs/configuration/ENVIRONMENT_AND_PATHS.md`

Incorrect:

```text
docs/VALIDATION_SPEC.md
```

Correct:

```text
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
```

---

### 5.2 `docs/projects/CREATING_A_PROJECT.md`

References beginning with:

```text
docs/00_PROJECT_START_HERE.md
docs/LANGUAGE_OVERVIEW.md
docs/LANGUAGE_ARCHITECTURE.md
docs/MODULE_DEPENDENCY_MAP.md
docs/CATEGORY_AND_LINCAT_CONTRACT.md
docs/MORPHOLOGY_SPEC.md
docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
docs/VALIDATION_SPEC.md
docs/TEST_COVERAGE_MATRIX.md
docs/STATUS_LEDGER.md
docs/DECISION_LOG.md
docs/KNOWN_ISSUES.md
docs/RELEASE_CRITERIA.md
docs/RESEARCH_EVIDENCE.md
```

must instead point to:

```text
project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md
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

---

### 5.3 `docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md`

Incorrect:

```text
docs/decisions/ADR_INDEX.md
```

Correct:

```text
docs/decisions/README.md
```

---

### 5.4 `templates/validation-profile/docs/KNOWN_ISSUES.md`

Incorrect:

```text
docs/diagnostics/DIAGNOSTIC_CLASSIFICATION.md
```

Correct:

```text
docs/diagnostics/ERROR_CLASSIFICATION.md
```

---

### 5.5 `project/docs/MODULE_DEPENDENCY_MAP.md`

Incorrect:

```text
docs/gf/GF_MODULE_COMPILATION.md
docs/projects/PROJECT_DIRECTORY_LAYOUT.md
```

Correct:

```text
docs/gf/GF_COMPILATION.md
docs/REPOSITORY_STRUCTURE.md
```

---

### 5.6 `templates/validation-profile/docs/RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`

Incorrect:

```text
docs/gf/GF_MODULE_COMPILATION.md
docs/projects/PROJECT_DIRECTORY_LAYOUT.md
docs/projects/ADDING_A_NEW_LANGUAGE.md
```

Correct:

```text
docs/gf/GF_COMPILATION.md
docs/REPOSITORY_STRUCTURE.md
docs/projects/CREATING_A_PROJECT.md
```

---

### 5.7 `templates/validation-profile/README.md`

Incorrect:

```text
docs/projects/CREATING_A_LANGUAGE_PROJECT.md
docs/projects/CLONING_AN_EXISTING_PROJECT.md
docs/projects/VALIDATING_A_PROJECT.md
```

Correct:

```text
docs/projects/CREATING_A_PROJECT.md
docs/projects/CLONING_AND_RESETTING.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
```

---

### 5.8 `templates/validation-profile/validation/inputs/README.md`

Incorrect:

```text
docs/scenarios/AUTHORING_SCENARIOS.md
docs/scenarios/GOLD_FILE_FORMAT.md
```

Correct:

```text
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/GOLDEN_TESTS.md
```

---

### 5.9 `project/docs/RESEARCH_EVIDENCE.md`

Incorrect:

```text
project/docs/GLOSSARY.md
```

Correct:

```text
docs/GLOSSARY.md
```

---

## 6. Active-project documents not yet final

The following files are present but must not be interpreted as completed release evidence:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/DECISION_LOG.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
project/docs/KNOWN_ISSUES.md
```

### 6.1 `project/docs/INTERFILE_CONTRACT_LOCK.md`

The active-project lock still contains unresolved template placeholders and therefore does not yet identify the real Albanian providers and consumers.

It must eventually identify:

```text
project owner
language identity
module suffix
GF providers
GF consumers
entrypoints
checkpoints
scenario-to-entrypoint contracts
input-to-scenario contracts
scenario-to-gold contracts
GFO and PGF artifact contracts
validation evidence
last review date
```

### 6.2 `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md`

The project-specific constructor and syntax registry remains incomplete.

It must be completed from actual GF source for:

```text
categories
lincats
NP, VP and clause representation
word order
agreement
negation
questions
relative clauses
coordination
clitics
public constructors
provider and consumer modules
validation cases
```

### 6.3 `project/docs/MODULE_DEPENDENCY_MAP.md`

The current document must be replaced or completed using actual GF imports.

Required final evidence:

```text
complete module inventory
direct imports
transitive closure for each entrypoint
checkpoint order
RGL dependencies
cycle detection
orphan detection
scenario entrypoints
PGF entrypoints
```

### 6.4 `project/docs/LANGUAGE_OVERVIEW.md`

The project must record the final decisions for:

```text
primary Albanian variety
accepted variants
dialect policy
orthographic policy
Unicode normalization
canonical output
allowed gold variants
```

### 6.5 `project/docs/DECISION_LOG.md`

Open project decisions must be resolved before release, including:

```text
primary Albanian variety
orthographic policy
roles of GrammarSqi, LangSqi and AllSqi
final PGF name and contract
```

### 6.6 `project/docs/STATUS_LEDGER__PROJECT_DOCS.md`

The ledger requires a real project review and current counts for:

```text
release blockers
exceptions
temporary implementations
fallbacks
warnings
owners
evidence
exit conditions
```

### 6.7 `project/docs/KNOWN_ISSUES.md`

Historical or provisional issues must be:

```text
reproduced
resolved
retired as non-reproducible
or retained with current evidence and release impact
```

### 6.8 `project/project.toml`

The configuration must be revalidated against actual source and final decisions for:

```text
source root
entrypoints
checkpoints
GF path parts
minimum GF version
required scenarios
optional scenarios
release PGF policy
final PGF identity
```

---

## 7. Files requiring synchronization after source validation

The following files may be structurally complete but must be synchronized with the actual GF sources, scenarios, gold files, and final project decisions:

```text
project/README.md
project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/RESEARCH_EVIDENCE.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/validation/README.md
project/validation/gold/README.md
project/validation/inputs/README.md
project/validation/scenarios/README.md
```

These files must not present intended or template behavior as already implemented.

---

## 8. Executable project assets absent from the audited snapshot

The audited documentation snapshot did not establish the presence of the active GF sources.

At minimum, the modules declared by the active configuration must exist at the final configured source root:

```text
GrammarSqi.gf
SyntaxSqi.gf
MorphoSqi.gf
NounSqi.gf
VerbSqi.gf
ExtendSqi.gf
StructuralSqi.gf
```

All modules imported by those files must also be present or resolved through the configured GF/RGL path.

This erratum does not invent the complete module inventory. The final inventory must be derived from actual GF imports.

---

## 9. Scenario assets not yet established

The following scenario files are required by the current project configuration and must exist before release validation:

```text
project/validation/scenarios/load.gfs
project/validation/scenarios/missing.gfs
project/validation/scenarios/linearize.gfs
project/validation/scenarios/parse.gfs
project/validation/scenarios/generation.gfs
project/validation/scenarios/morphology.gfs
```

Current policy:

```text
load         required
missing      required
linearize    required
parse        required
generation   optional
morphology   optional
```

A zero process exit is not sufficient for scenario success. Required markers, assertions, normalized output, gold comparison, and artifact checks remain applicable.

---

## 10. Gold assets not yet established

Required by the current coverage policy:

```text
project/validation/gold/missing.gold
project/validation/gold/linearize.gold
project/validation/gold/parse.gold
```

Conditional, only when the corresponding scenarios use gold comparison:

```text
project/validation/gold/load.gold
project/validation/gold/generation.gold
project/validation/gold/morphology.gold
```

Normal validation must never create or rewrite canonical gold files automatically.

---

## 11. Scenario input assets

The exact input filenames must be derived from the implemented `.gfs` scenarios.

A likely, non-normative starting set is:

```text
project/validation/inputs/linearize_trees.trees
project/validation/inputs/parse_positive.phrases
project/validation/inputs/parse_negative.phrases
project/validation/inputs/morphology_nouns.tsv
project/validation/inputs/morphology_verbs.tsv
project/validation/inputs/generation_categories.txt
```

Do not create unused files solely to match this example.

Every canonical input must have:

```text
stable input ID
owner
format and format version
scenario consumers
ordering policy
duplicate policy
encoding
provenance
```

---

## 12. Release evidence not yet established

The repository must not be described as release-ready until an actual release run produces and verifies:

```text
run_<run-id>/summary.json
run_<run-id>/manifest.json
run_<run-id>/summary.md
run_<run-id>/AI_READY.md
run_<run-id>/top_errors.txt
run_<run-id>/raw/compile/
run_<run-id>/raw/scenarios/
run_<run-id>/artifacts/
run_<run-id>/artifacts/<final-pgf-name>.pgf
```

The release evidence must identify:

```text
GF Wordbench version
project identity
project configuration hash
source commit
GF version
RGL revision
normalization version
required FileResults
required ScenarioResults
PGF hash
manifest hash coverage
known issue and ledger review
```

---

## 13. Current delivery classification

Until the retirement conditions below are met, the repository must be classified as:

```text
documentation and project framework under finalization
```

It must not be classified as:

```text
final release
release-ready project
fully validated Albanian grammar
complete executable delivery
```

---

## 14. Retirement criteria

This erratum may be retired only when:

```text
[ ] docs/architecture/DATA_MODEL.md exists
[ ] every incorrect reference in Section 5 is corrected
[ ] the three moved README files are included in a new snapshot
[ ] the active project lock contains no unresolved required placeholder
[ ] the syntax and constructor registry matches actual GF source
[ ] the module dependency map is generated or verified from actual imports
[ ] language and orthographic decisions are recorded
[ ] project.toml matches actual source and scenarios
[ ] required GF source modules are present
[ ] required `.gfs` scenarios are present
[ ] required gold files are reviewed
[ ] required scenario inputs are registered
[ ] checkpoint validation passes
[ ] required scenarios pass
[ ] final PGF construction passes
[ ] summary.json and manifest.json validate
[ ] release evidence is retained
[ ] a new documentation-link audit passes
[ ] this erratum is marked retired or removed through a recorded decision
```

---

## 15. Final rule

> This erratum records known discrepancies; it does not convert missing implementation or missing evidence into completed work.

Every permanent correction must still be made in the file that owns the affected contract.
