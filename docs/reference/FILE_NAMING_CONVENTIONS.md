# GF Wordbench — File Naming Conventions

**Document ID:** `GF-WB-REF-FILE-NAMING`  
**Status:** Normative reference  
**Applies to:** Repository files, Python packages and modules, GF source files, active-project assets, templates, scenarios, gold files, run directories, reports, logs, artifacts, fixtures, migrations, and generated safe keys  
**Primary owners:** GF Wordbench maintainers and active-language project maintainers  
**Canonical repository name:** `GF_Wordbench`  
**Canonical package/distribution name:** `gf-wordbench`  
**Canonical CLI name:** `gf-wordbench`  
**Target architecture:** Final GF Wordbench architecture  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines how files and directories are named throughout GF Wordbench.

Its goals are to ensure that names are:

- predictable;
- portable;
- deterministic;
- readable;
- safe on Windows and other supported platforms;
- compatible with Python, GF, JSON, TOML, Markdown, shells, and version-control tools;
- stable enough for automation;
- unambiguous across framework, project, template, run, and legacy scopes;
- resistant to accidental collisions and contract drift.

The governing rule is:

> A name is part of the architecture when another file, component, command, schema, report, test, or user workflow depends on it.

Internal temporary names may vary when no consumer depends on them.

Canonical public names must change only through coordinated migration.

---

## 2. Related normative documents

This reference must remain consistent with:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/release/VERSIONING_POLICY.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/reference/SCHEMA_INDEX.md
docs/reference/STATUS_VALUES.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/project.toml
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Authority boundaries:

| Subject | Authoritative owner |
|---|---|
| File and directory naming rules | this document |
| Persisted canonical paths | `PERSISTED_SCHEMA_LOCK.md` |
| Artifact ownership | `ARTIFACT_MODEL.md` |
| Python provider/consumer paths | framework interfile lock |
| GF module relationships | project interfile lock |
| Schema identifiers | `SCHEMA_INDEX.md` |
| Renaming and compatibility | migration and versioning policies |

When this document and a lock disagree, the lock remains authoritative for its contract surface.

The documents must then be corrected together.

---

# 3. Scope

This document governs names for:

```text
repository directories
repository root files
Python packages
Python modules
Python classes and test files where tied to filenames
GF source files
GF module names
project directories
project documents
scenario scripts
scenario inputs
gold files
run directories
reports
logs
raw evidence
generated GF artifacts
manifest roles
schema fixtures
migration fixtures
temporary files
safe target keys
archive/export names
Windows launchers
```

This document does not prescribe:

```text
local variable names
private function names not reflected in filenames
GF local oper names
human prose headings outside locked report structure
version-control commit messages
branch names unless a release process depends on them
```

---

# 4. Normative terms

- **CANONICAL NAME**: name emitted or created by current GF Wordbench writers.
- **LEGACY NAME**: older accepted name read only for compatibility.
- **PUBLIC NAME**: name referenced by users, automation, schemas, reports, or another file.
- **PRIVATE NAME**: implementation detail with no external consumer.
- **PROJECT-RELATIVE PATH**: path relative to the active project root.
- **RUN-RELATIVE PATH**: path relative to one run directory.
- **SAFE KEY**: filename-safe deterministic identifier derived from a logical subject.
- **BASENAME**: filename without parent directories.
- **STEM**: basename without final extension.
- **EXTENSION**: suffix beginning with `.`.
- **MODULE NAME**: declared Python or GF module identity.
- **DISPLAY NAME**: human-readable title not necessarily safe as a filename.
- **IDENTIFIER**: stable machine-oriented name used across files or schemas.
- **COLLISION**: two logical subjects mapping to the same canonical name.
- **RESERVED NAME**: name prohibited by platform, framework, or contract.

---

# 5. General character policy

Canonical framework-controlled names use the portable ASCII subset:

```text
A-Z
a-z
0-9
-
_
.
```

Additional rules:

- names must not begin or end with whitespace;
- names must not contain control characters;
- names must not contain tabs or newlines;
- names must not contain `/` or `\` inside one path segment;
- names must not end with `.` on Windows-compatible paths;
- names must not end with a space;
- names must not contain shell metacharacters when the framework creates them;
- names must not contain reserved device basenames;
- names must not contain unresolved path traversal segments.

User-owned source files may contain Unicode when required by an existing project.

Framework-generated names must remain portable ASCII unless a contract explicitly requires preserving a source basename.

---

## 5.1 Portable ASCII preference

Use ASCII for:

```text
framework directories
Python modules
report filenames
schema fixture filenames
run directories
generated safe keys
temporary files
manifest-controlled generated artifacts
```

Unicode is permitted for:

```text
linguistic source content
user-provided input filenames when already authoritative
project display names
language names
historical imported files
```

When a Unicode source filename is used, the persisted project-relative path preserves it exactly after path normalization.

Do not transliterate an authoritative source path silently.

---

## 5.2 Spaces

Framework-controlled canonical filenames and directories must not contain spaces.

Use:

```text
hyphen
underscore
```

according to the naming family defined below.

Existing external source roots may contain spaces.

Process requests must support them safely through argument arrays.

A path containing spaces is not invalid merely because the framework would not generate it.

---

## 5.3 Case sensitivity

Canonical names are case-sensitive in contracts even on case-insensitive filesystems.

Rules:

- do not create two names differing only by case;
- comparisons for collision detection should be case-insensitive on Windows;
- canonical path serialization preserves declared case;
- GF module filename case must match the declared module name;
- Python module names are lowercase;
- normative documentation filenames use uppercase snake case where specified;
- report filenames preserve their locked case.

Example prohibited pair:

```text
GrammarEng.gf
grammareng.gf
```

inside one logical source root.

---

# 6. Path separator policy

Canonical persisted paths use:

```text
/
```

Examples:

```text
project/validation/scenarios/parse.gfs
raw/compile/GrammarEng.stderr.txt
lib/src/english/GrammarEng.gf
```

Runtime-native paths may use platform separators internally.

Rules:

- current writers emit `/` in JSON, TOML, manifests, and contract examples;
- legacy readers accept `\`;
- display code may render native paths for user convenience;
- path equality uses normalized semantic paths, not raw string equality;
- a path segment must not contain either separator.

---

# 7. Path base policy

Every persisted path field must have one defined base.

Canonical bases:

```text
repository root
project root
run root
output root
environment absolute
```

Examples:

| Path | Base |
|---|---|
| `project/project.toml` | repository root |
| `file_results[].file_path` | project root |
| `scenario_results[].script_path` | project root |
| `artifacts.summary_json` | run root |
| `metadata.gf_executable` | environment absolute |
| `metadata.rgl_root` | environment absolute |

Do not infer a path base from the filename.

The field contract owns the base.

---

# 8. Repository root naming

Canonical repository directory:

```text
GF_Wordbench
```

Example Windows location:

```text
C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench
```

The repository may be cloned to another local parent path.

The inner repository name should remain:

```text
GF_Wordbench
```

where practical, but code must not rely on the basename.

Package distribution and CLI names use hyphens instead:

```text
gf-wordbench
```

Python import package names use underscores:

```text
gf_wordbench
```

when or if a top-level import package uses the distribution name.

---

# 9. Root file names

Canonical root files:

```text
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
pyproject.toml
```

Optional root files may include:

```text
.gitignore
.gitattributes
.editorconfig
pre-commit-config.yaml
tox.ini
```

Rules:

- well-known ecosystem names keep their standard casing;
- root policy documents use uppercase conventional names;
- do not create lowercase duplicates such as `readme.md`;
- do not create both `LICENSE` and `LICENSE.md` unless distribution requirements explicitly demand both;
- one canonical packaging configuration should exist.

---

# 10. Top-level directory names

Canonical top-level directories:

```text
app
docs
project
templates
tests
scripts
runs
```

Only directories actually used by the implementation should be created.

Recommended meaning:

| Directory | Purpose |
|---|---|
| `app/` | Python application source |
| `docs/` | Framework documentation |
| `project/` | One active GF language project |
| `templates/` | Cloneable templates |
| `tests/` | Framework and fixture tests |
| `scripts/` | Repository maintenance helpers |
| `runs/` | Default local run output when repository-local |

Do not use ambiguous alternatives:

```text
srcs
documentation
test
output
outputs
results
temp
misc
common
utils2
new
old
backup
```

A directory called `legacy/` is permitted only when it clearly contains compatibility fixtures or archived migration code and is excluded from active discovery.

---

# 11. Python package directory names

Python package directories use:

```text
lowercase_snake_case
```

Examples:

```text
app/audit
app/reports
app/gui
app/utils
app/gold
```

Rules:

- only lowercase ASCII letters, digits, and underscores;
- must be valid Python identifiers;
- must not begin with a digit;
- avoid abbreviations unless standard within the project;
- avoid generic names such as `common` when a focused owner exists;
- package directory and import path must agree;
- include `__init__.py` when required by the packaging strategy.

Prohibited:

```text
Audit
audit-tools
audit tools
audit_v2
new_audit
misc
helpers
```

`helpers` may exist only if its responsibility is narrow and documented; focused domain names are preferred.

---

# 12. Python module filenames

Python modules use:

```text
lowercase_snake_case.py
```

Canonical examples:

```text
audit_core.py
file_selector.py
scanner.py
compiler.py
classifier.py
diagnostics.py
diff.py
fingerprint.py
result_model.py
report_json.py
report_markdown.py
report_ai.py
report_logs.py
report_details.py
process_utils.py
path_utils.py
io_utils.py
project_config.py
state.py
bootstrap.py
main_cli.py
```

Rules:

- filename describes one stable responsibility;
- avoid version suffixes such as `_v2.py`;
- avoid temporary adjectives such as `new_`, `old_`, `final_`, `latest_`;
- avoid implementation suffixes such as `_impl.py` unless paired with a stable interface for a justified reason;
- avoid plural names when the module owns one cohesive service, unless plural is natural;
- do not duplicate names across sibling packages when imports would be ambiguous without qualification;
- private experimental modules begin with `_` only when they are truly private and not imported outside the owning package.

---

## 12.1 Module rename policy

Renaming a public Python module requires:

```text
framework interfile contract review
all import updates
compatibility adapter decision
tests
documentation
migration/deprecation note
```

Do not keep two independent implementations under old and new filenames.

A temporary compatibility module may re-export canonical symbols.

It must be deprecated and have a removal target.

---

# 13. Python class-to-file relationship

Classes use `PascalCase`.

Files remain `snake_case.py`.

Examples:

```text
RunConfig              → models.py or run_config.py
RunPaths               → models.py or run_paths.py
ScenarioResult         → result_model.py
ProjectConfig          → project_config.py
GoldUpdateService      → update_service.py
```

Rules:

- do not create one file per tiny dataclass automatically;
- group tightly related models under the established owner;
- create a dedicated file when the class owns a stable public contract or substantial behavior;
- filename must not use `PascalCase.py`.

---

# 14. Python entrypoint filenames

Canonical CLI entrypoint:

```text
app/main_cli.py
```

Canonical GUI entrypoint may be:

```text
app/main_gui.py
```

or an explicitly documented GUI package entrypoint.

Packaging console script:

```toml
[project.scripts]
gf-wordbench = "app.main_cli:main"
```

The exact import target must match implementation.

Avoid multiple competing CLI roots such as:

```text
cli.py
main.py
command.py
run.py
```

unless one is clearly the parser and one is clearly the application entrypoint.

---

# 15. Test directory naming

Tests mirror application responsibility.

Canonical examples:

```text
tests/audit/
tests/reports/
tests/projects/
tests/scenarios/
tests/schemas/
tests/contracts/
tests/integration/
tests/release/
tests/fixtures/
```

Rules:

- directory names use lowercase snake case;
- tests for one component live under the corresponding domain;
- contract tests are grouped separately when they validate boundaries;
- real-GF tests are identifiable as integration tests;
- fixtures are not mixed with generated run output.

---

# 16. Test file naming

Test modules use:

```text
test_<subject>.py
```

Examples:

```text
test_compiler.py
test_scenario_runner.py
test_summary_schema.py
test_gold_update.py
test_contract_versions.py
```

Avoid:

```text
compiler_test.py
tests_compiler.py
test1.py
test_misc.py
```

A test file may include a specific concern:

```text
test_compiler_timeout.py
test_compiler_artifacts.py
test_summary_migration.py
```

Split only when the file has an independent concern and meaningful size.

---

# 17. Test function naming

Test functions use:

```text
test_<behavior>_<condition>_<expected_result>
```

Examples:

```python
def test_compile_timeout_returns_error():
    ...

def test_missing_required_gold_does_not_write_file():
    ...

def test_legacy_mode_all_migrates_to_diagnostic():
    ...
```

Names should describe behavior rather than implementation steps.

---

# 18. Fixture naming

Fixture directories use lowercase snake case.

Examples:

```text
tests/fixtures/gf_minimal/
tests/fixtures/legacy_summary_flat/
tests/fixtures/legacy_state_unversioned/
tests/fixtures/project_template_v1/
```

Fixture files should indicate purpose:

```text
valid_summary.json
missing_schema_id.json
unknown_enum.json
type_error.gf
syntax_error.gf
parse_success.gfs
```

Do not use unexplained names:

```text
sample1
testdata
foo
bar
x
```

Small conventional `foo` examples may appear inside isolated unit tests, but not as canonical fixture identities.

---

# 19. Documentation directory names

Documentation subdirectories use lowercase ASCII words:

```text
docs/architecture
docs/gf
docs/validation
docs/scenarios
docs/diagnostics
docs/reports
docs/configuration
docs/usage
docs/projects
docs/development
docs/operations
docs/release
docs/decisions
docs/reference
```

Rules:

- use singular or plural consistently with the canonical map;
- do not create near-duplicates such as `doc`, `documentation`, or `refs`;
- place a document under the directory owning its primary responsibility;
- cross-cutting root locks remain directly under `docs/`.

---

# 20. Framework documentation filenames

Normative and major reference documents use:

```text
UPPERCASE_SNAKE_CASE.md
```

Examples:

```text
ARCHITECTURE_OVERVIEW.md
COMPONENT_MAP.md
ERROR_HANDLING_MODEL.md
VALIDATION_PIPELINE.md
COMPILATION_VALIDATION.md
SUMMARY_JSON_REFERENCE.md
FILE_NAMING_CONVENTIONS.md
VERSIONING_POLICY.md
```

Rules:

- concise noun phrase;
- avoid articles;
- avoid dates in filenames;
- avoid version numbers in filenames;
- avoid `FINAL`, `NEW`, `OLD`, or `UPDATED`;
- use one canonical document per stable responsibility;
- do not duplicate a topic under slightly different filenames.

Prohibited examples:

```text
architecture-final.md
Architecture Overview.md
architecture_overview_v2.md
NEW_ERROR_MODEL.md
notes.md
misc.md
```

---

# 21. Navigation document filenames

Canonical navigation/start documents may use numeric prefixes:

```text
00_START_HERE.md
00_PROJECT_START_HERE.md
```

Rules:

- numeric prefixes are reserved for intentional reading order;
- use two digits;
- only navigation/index documents should use this convention;
- do not number every documentation file.

Decision records use their own numbering convention.

---

# 22. ADR filenames

Architecture Decision Records use:

```text
ADR-<four-digit-number>-<UPPERCASE-HYPHENATED-TITLE>.md
```

Canonical examples:

```text
ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
ADR-0002-GF-AS-EXECUTION-ENGINE.md
ADR-0003-SEPARATE-SCAN-AND-COMPILE.md
```

Rules:

- four-digit zero-padded sequence;
- IDs are never reused;
- title uses uppercase words separated by hyphens;
- filename remains stable after acceptance;
- superseded ADRs retain filenames and status;
- do not renumber ADRs.

---

# 23. Contract lock filenames

Canonical framework locks:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
```

Canonical project lock:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Canonical template lock:

```text
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Rules:

- filenames are identical where the role is the same in active project and template;
- directory context disambiguates scope;
- do not add language names to the active lock filename;
- do not create duplicate unofficial locks.

---

# 24. Active project directory names

Canonical active project root:

```text
project/
```

Canonical children:

```text
project/docs/
project/validation/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Optional project-controlled source root example:

```text
project/lib/src/<language-directory>/
```

Rules:

- one repository contains one active `project/`;
- do not name active projects `project1`, `current_project`, or language-specific top-level alternatives;
- clone/reset operations replace or recreate the content under `project/`;
- language identity comes from `project/project.toml`, not the directory name.

---

# 25. Project configuration filename

Canonical:

```text
project/project.toml
```

Template:

```text
templates/project/project.toml
```

Rules:

- lowercase filename;
- no language suffix;
- one authoritative configuration file;
- do not create `project.json`, `config.toml`, or `settings.toml` as competing project identities;
- environment-specific application state remains separate.

---

# 26. Active project documentation filenames

Canonical project docs:

```text
00_PROJECT_START_HERE.md
INTERFILE_CONTRACT_LOCK.md
LANGUAGE_OVERVIEW.md
LANGUAGE_ARCHITECTURE.md
MODULE_DEPENDENCY_MAP.md
CATEGORY_AND_LINCAT_CONTRACT.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
STATUS_LEDGER.md
DECISION_LOG.md
KNOWN_ISSUES.md
RELEASE_CRITERIA.md
RESEARCH_EVIDENCE.md
```

Rules:

- active project and template use the same required filenames;
- template content may contain placeholders;
- active project content must not retain unresolved required placeholders;
- do not add the language code to each filename;
- document role is identified by filename and directory.

---

# 27. Project README names

Canonical:

```text
project/README.md
project/validation/README.md
project/validation/scenarios/README.md
project/validation/inputs/README.md
project/validation/gold/README.md
```

Every directory requiring maintainer guidance may use `README.md`.

Do not create both:

```text
README.md
README_PROJECT.md
```

inside the same directory unless they have genuinely distinct responsibilities.

---

# 28. Language directory identifiers

A project-controlled language source directory should use a stable lowercase identifier:

```text
english
french
sqi
lang-sqi
```

Preferred pattern:

```text
lowercase-kebab-case
```

or existing upstream convention when sources remain inside an upstream repository.

Rules:

- language directory identity is project data;
- do not infer GF module suffix from directory spelling;
- avoid display names with spaces;
- avoid renaming solely for style during initial migration;
- record any rename as a project migration.

---

# 29. GF source filenames

GF source filenames must match the declared GF module name exactly:

```text
<ModuleName>.gf
```

Examples:

```text
GrammarEng.gf
SyntaxEng.gf
MorphoEng.gf
ParadigmsEng.gf
LexiconEng.gf
StructuralEng.gf
ExtendEng.gf
```

Rules:

- stem uses valid GF module identifier syntax;
- extension is lowercase `.gf`;
- case matches the module declaration;
- one source file owns one primary GF module;
- no spaces;
- no hyphens in the GF module stem;
- no `_v2`, `_new`, `_old`, `_copy`, or date suffixes in active modules;
- backup copies remain outside active source selection.

Prohibited active filenames:

```text
Grammar Eng.gf
grammarEng.gf
Grammar-Eng.gf
GrammarEng_v2.gf
GrammarEng copy.gf
GrammarEng_2026.gf
```

---

# 30. GF module naming families

GF module names use `PascalCase` and a project-consistent suffix.

Typical role prefixes:

```text
Grammar
Syntax
Morpho
Paradigms
Lexicon
Structural
Extend
Extra
Irreg
Dict
Lang
Noun
Verb
Adjective
Adverb
Sentence
Question
Relative
Conjunction
```

Examples:

```text
MorphoSqi
ParadigmsSqi
SyntaxSqi
GrammarSqi
LangSqi
```

The actual module family belongs to the active project architecture.

Framework code must not hardcode one language suffix.

Rules:

- suffix agrees with `project.toml`;
- provider and consumer docs use exact module names;
- module renames are coordinated contract migrations;
- interface/instance naming follows GF and project conventions consistently.

---

# 31. GF interface and instance filenames

Use exact GF module names:

```text
<InterfaceName>.gf
<InstanceName>.gf
```

Recommended project convention may include role indicators:

```text
MorphoFunctor.gf
MorphoSqi.gf
SyntaxFunctor.gf
SyntaxSqi.gf
```

The project must document which naming style it uses.

Do not infer an interface/instance relationship solely from filename text.

The module declaration and project dependency map are authoritative.

---

# 32. GF backup and retired files

Backup or retired source must not match active source selection.

Recommended archive patterns outside active source root:

```text
archive/GrammarEng.gf
legacy/GrammarEng.gf
retired/GrammarEng.gf
```

Temporary local backup patterns may be:

```text
GrammarEng.gf.bak
GrammarEng.gf.tmp
GrammarEng.gf.orig
```

Do not use:

```text
GrammarEng_old.gf
GrammarEng2.gf
GrammarEngFinal.gf
```

inside the active source root.

Active selection rules should exclude editor and merge artifacts:

```text
*.bak
*.tmp
*.orig
*~
*.rej
```

---

# 33. GF generated artifact filenames

GF-generated artifacts normally retain the module stem:

```text
<ModuleName>.gfo
<GrammarName>.pgf
```

Examples:

```text
GrammarEng.gfo
LangEng.pgf
```

Rules:

- extension is lowercase;
- generated files are not authoritative source;
- run-owned artifact directories provide freshness and ownership;
- source-adjacent generated artifacts must not be treated as current release evidence without verification;
- expected PGF name is documented in project configuration or release contract;
- framework must not rename a PGF arbitrarily after generation without preserving provenance.

---

# 34. Scenario filenames

Canonical scenario script:

```text
<scenario-id>.gfs
```

Scenario IDs use:

```text
lowercase-kebab-case
```

Examples:

```text
load.gfs
missing.gfs
linearize.gfs
parse.gfs
generation.gfs
morphology.gfs
parse-basic.gfs
linearize-noun-phrases.gfs
```

Rules:

- filename stem equals `scenario_id`;
- extension is lowercase `.gfs`;
- ID is unique within the active project;
- no spaces;
- no uppercase;
- no underscores in canonical scenario IDs;
- no version suffix in active filename;
- scenario renames are breaking project migrations;
- scenario order comes from configuration, not filename sorting unless documented.

Prohibited:

```text
Parse.gfs
parse_test.gfs
parse v2.gfs
parse-final.gfs
scenario1.gfs
```

`parse-final.gfs` is permitted only if `final` is semantically meaningful, not a development label.

---

# 35. Scenario marker identifiers

Scenario section and marker IDs use:

```text
lowercase-kebab-case
```

Examples:

```text
load-main
parse-basic
linearize-noun-phrases
missing-functions
```

Rules:

- unique within one scenario;
- stable across gold comparisons;
- no whitespace;
- no path separators;
- no display punctuation;
- no timestamp or random suffix;
- marker rename requires scenario and gold migration.

---

# 36. Scenario input filenames

Scenario input files use:

```text
<scenario-id>-<purpose>.<extension>
```

Examples:

```text
parse-basic.txt
linearize-trees.txt
morphology-lemmas.tsv
generation-seeds.txt
```

When one input belongs to one scenario, the scenario ID should prefix the filename.

Shared inputs may use a domain name:

```text
common-noun-phrases.txt
regression-cases.tsv
```

Rules:

- lowercase kebab case;
- extension reflects actual format;
- avoid generic `input.txt`;
- ordering semantics are documented;
- encoding is UTF-8 unless another format is explicitly required.

---

# 37. Gold filenames

Canonical:

```text
<scenario-id>.gold
```

Examples:

```text
parse.gold
linearize.gold
missing.gold
morphology.gold
```

Rules:

- stem equals scenario ID;
- extension is lowercase `.gold`;
- one authoritative gold per scenario variant;
- gold path is project-controlled;
- no timestamps;
- no reviewer name;
- no `_expected` suffix;
- no `.txt` double extension;
- old gold is preserved through version control or run-local migration evidence, not sibling backup files.

Prohibited:

```text
parse_expected.txt
parse.gold.old
parse-20260722.gold
Parse.gold
parse_v2.gold
```

---

# 38. Gold candidate and diff filenames

Run-local derived files may use:

```text
<scenario-id>.candidate.gold
<scenario-id>.previous.gold
<scenario-id>.gold.diff
```

Examples:

```text
parse.candidate.gold
parse.previous.gold
parse.gold.diff
```

These belong under the run directory, not the canonical project gold directory.

Temporary canonical replacement may use:

```text
.<scenario-id>.gold.tmp
```

inside the gold directory for atomic replacement.

The updater must ensure collision-safe temporary naming when concurrent operations are possible.

---

# 39. Normalized scenario output filenames

Canonical run-local normalized output:

```text
<scenario-id>.out
```

Examples:

```text
parse.out
linearize.out
```

Raw streams:

```text
<scenario-id>.stdout.txt
<scenario-id>.stderr.txt
```

Rules:

- raw and normalized outputs have distinct names;
- `.out` is normalized derived evidence;
- `.stdout.txt` and `.stderr.txt` preserve raw streams;
- do not use one combined `output.txt` as the only evidence;
- all names use the safe scenario ID.

---

# 40. Run directory naming

Canonical pattern:

```text
run_<run-id>
```

Recommended run ID:

```text
YYYYMMDD_HHMMSS
```

Collision suffix:

```text
YYYYMMDD_HHMMSS_02
```

Examples:

```text
run_20260722_143015
run_20260722_143015_02
```

Rules:

- timestamp is UTC;
- numeric fields are zero-padded;
- no timezone punctuation;
- no spaces;
- no local-language month names;
- suffix begins at `_02`;
- run ID is stable after creation;
- do not rename finalized run directories casually;
- run discovery validates contents, not only basename.

---

# 41. Run directory children

Canonical layout:

```text
run_<run-id>/
├── summary.json
├── summary.md
├── AI_READY.md
├── top_errors.txt
├── manifest.json
├── details/
├── raw/
│   ├── master.log
│   ├── ALL_SCAN_LOGS.TXT
│   ├── ALL_LOGS.TXT
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

Names are locked when persisted schemas or reports depend on them.

Do not create alternate spellings:

```text
Summary.json
ai_ready.md
top-errors.txt
artifact/
logs/
raw_logs/
```

unless introduced through a versioned migration.

---

# 42. Report filenames

Canonical report names:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
```

Rules:

- exact case is contractual;
- `summary.json` is machine-readable;
- `summary.md` is human-readable;
- `AI_READY.md` uses uppercase identity;
- `top_errors.txt` uses lowercase snake case;
- `manifest.json` is machine-readable;
- current writers emit only these names.

Legacy aliases may be read from historical summaries but not written.

---

# 43. Aggregate log filenames

Canonical:

```text
raw/master.log
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
```

Exact case remains stable because historical tools or humans may rely on it.

New aggregate logs should follow the existing family only when justified.

Prefer:

```text
UPPERCASE_SNAKE_CASE.TXT
```

for human aggregate bundles.

Per-subject logs use safe subject keys and lowercase stream suffixes.

---

# 44. Per-file compile log names

Canonical pattern:

```text
<safe-target-key>.stdout.txt
<safe-target-key>.stderr.txt
```

Examples:

```text
GrammarEng.stdout.txt
GrammarEng.stderr.txt
lib-src-english-GrammarEng--a1b2c3d4.stdout.txt
```

The simple module stem may be used only when collision-free within the run.

When paths may collide, use a deterministic safe key.

Do not use absolute paths in filenames.

---

# 45. Per-file scan log names

Canonical pattern:

```text
<safe-target-key>.scan.txt
```

Examples:

```text
GrammarEng.scan.txt
lib-src-english-GrammarEng--a1b2c3d4.scan.txt
```

Rules:

- same safe-key service as compile logs;
- no independent reconstruction by report writers;
- one source path maps to one stable key within a run.

---

# 46. Safe target keys

A safe target key converts a logical identity into a portable filename stem.

Recommended algorithm:

```text
1. take normalized project-relative identity
2. remove final known extension
3. replace path separators with -
4. replace unsupported characters with -
5. collapse repeated -
6. trim punctuation
7. preserve a readable bounded prefix
8. append --<short-stable-hash> when required for uniqueness
```

Example:

```text
lib/src/english/GrammarEng.gf
→ lib-src-english-GrammarEng--a1b2c3d4
```

Rules:

- deterministic;
- stable within schema/algorithm version;
- collision-resistant;
- no secret or absolute-root data;
- maximum length enforced;
- hash derived from canonical logical identity, not local absolute path;
- reports receive the generated key or owned path; they do not recompute it.

The safe-key algorithm becomes contractual when persisted paths depend on it.

---

# 47. Safe-key hash suffix

Recommended suffix:

```text
--<8-lowercase-hex>
```

Example:

```text
--a1b2c3d4
```

Rules:

- use a stable cryptographic digest such as SHA-256;
- truncate only the filename-disambiguation suffix, not source fingerprints;
- eight hex characters are acceptable for local run collision disambiguation when collision detection remains active;
- increase length or resolve deterministically on collision;
- never confuse safe-key hash with canonical source fingerprint.

---

# 48. Filename length policy

Recommended maximum generated basename:

```text
120 characters
```

Recommended maximum safe key before extensions:

```text
96 characters
```

Rules:

- preserve extensions;
- truncate readable prefix before hash suffix;
- never truncate in a way that removes collision protection;
- validate full path length on supported Windows environments;
- user-owned long source paths may be supported when the platform allows them;
- generated run paths should remain conservative.

---

# 49. Detail report filenames

Recommended pattern:

```text
<safe-target-key>.md
```

Examples:

```text
GrammarEng.md
parse.md
lib-src-english-GrammarEng--a1b2c3d4.md
```

If file and scenario identities can collide in one directory, prefix the subject kind:

```text
file--<safe-target-key>.md
scenario--<safe-scenario-id>.md
```

The chosen pattern must be owned by the detail-report writer and locked before external use.

Do not infer subject kind from extension alone.

---

# 50. Artifact directory names

Canonical run artifact directories:

```text
artifacts/gfo
artifacts/out
artifacts/pgf
```

Rules:

- lowercase;
- no leading dot;
- one directory per broad artifact family;
- no version suffix;
- no language suffix unless an additional subdirectory is justified;
- manifest identifies actual artifact roles.

Optional future artifact directories should use lowercase kebab or simple lowercase nouns:

```text
artifacts/graphs
artifacts/exports
```

Do not add directories without a producer and lifecycle.

---

# 51. Artifact filenames

Where GF controls the artifact name, preserve the GF-produced basename.

Where GF Wordbench creates the artifact, use:

```text
lowercase-kebab-case
```

or the safe-key family.

Examples:

```text
dependency-graph.dot
dependency-graph.svg
release-package.zip
project-inventory.json
```

Rules:

- extension matches content;
- no misleading extension;
- no timestamp unless multiple immutable versions are intentionally stored;
- version may appear in release package names when release policy defines it;
- manifest stores role and provenance.

---

# 52. Release package filenames

Recommended pattern:

```text
<project-id>-<project-version>.<archive-extension>
```

Examples:

```text
example-language-1.2.0.zip
example-language-1.2.0.tar.gz
```

Optional classifier:

```text
example-language-1.2.0-windows.zip
example-language-1.2.0-source.tar.gz
```

Rules:

- project ID uses lowercase kebab case;
- Semantic Version is exact;
- no spaces;
- no `latest`;
- no ambiguous `final`;
- checksum files append the algorithm:

```text
example-language-1.2.0.zip.sha256
```

Package naming must be defined by release policy before automation depends on it.

---

# 53. Schema fixture filenames

Recommended pattern:

```text
<schema-short-name>_<case>.<extension>
```

Examples:

```text
run_summary_valid.json
run_summary_missing_schema_id.json
project_valid.toml
manifest_path_escape.json
gold_wrong_scenario_id.gold
```

Version-specific fixtures:

```text
run_summary_v1_0_valid.json
run_summary_legacy_flat.json
project_v1_0_minimal.toml
```

Rules:

- lowercase snake case;
- version dots become underscores;
- case describes the expected condition;
- fixture name must not claim validity when intentionally malformed without indicating the fault.

---

# 54. Migration fixture names

Recommended:

```text
<domain>_<source-form>_to_<target-form>.<extension>
```

Examples:

```text
state_gf_audit_to_gf_wordbench.json
summary_flat_to_v1_0.json
project_template_v1_to_v2.toml
```

For source and expected output pairs:

```text
summary_flat.source.json
summary_flat.expected.json
summary_flat.warnings.json
```

Rules:

- suffix role is explicit;
- do not overwrite source fixture during tests;
- fixtures remain immutable.

---

# 55. Temporary file names

Atomic write temporary files use a sibling hidden pattern:

```text
.<basename>.tmp
```

Examples:

```text
.summary.json.tmp
.project.toml.tmp
.parse.gold.tmp
```

When concurrent writers are possible:

```text
.<basename>.<process-or-random-safe-token>.tmp
```

Rules:

- temporary file remains in destination directory when atomic replacement requires same filesystem;
- token contains portable ASCII;
- temporary files are excluded from discovery;
- no secret values in token;
- cleanup policy is explicit;
- temporary names are not persisted as canonical artifact paths.

---

# 56. Lock and sentinel filenames

If filesystem lock or incomplete-run markers are introduced, use hidden lowercase names:

```text
.gf-wordbench.lock
.incomplete
.finalizing
```

Such names require explicit ownership and lifecycle.

Do not introduce sentinel files ad hoc.

A sentinel becomes contractual when discovery or cleanup depends on it.

---

# 57. Backup filenames

Canonical source directories should not accumulate backups.

When explicit backup files are necessary:

```text
<basename>.backup
<basename>.pre-migration
```

Prefer storing backups in a migration-owned backup directory rather than beside canonical files.

Recommended:

```text
migration-backup/<migration-id>/<relative-path>
```

Rules:

- backup is not discoverable as active input;
- backup name records purpose, not vague `old`;
- backup hash is recorded when migration policy requires it;
- version control is preferred for project sources.

---

# 58. Archive directory names

Historical or retired material may use:

```text
archive/
legacy/
retired/
migration-backup/
```

Each directory needs a README or explicit exclusion rule.

Meaning:

| Name | Use |
|---|---|
| `archive/` | historical material retained for reference |
| `legacy/` | compatibility fixtures or old supported forms |
| `retired/` | no-longer-active contract/source examples |
| `migration-backup/` | explicit pre-migration copies |

Do not use these directories as active providers.

---

# 59. Windows launcher filenames

Recommended root or script names:

```text
run-gf-wordbench.cmd
run-gf-wordbench.ps1
install-gf-wordbench.ps1
```

Rules:

- lowercase kebab case;
- extension reflects shell;
- launcher is convenience only;
- no hardcoded personal paths;
- do not use `start.bat`, `run.bat`, or `test.bat` without specific context;
- one authoritative launcher per shell purpose.

If `.bat` is required for compatibility, use the same stem:

```text
run-gf-wordbench.bat
```

---

# 60. Repository maintenance script filenames

Use lowercase snake case for Python:

```text
scripts/check_contracts.py
scripts/build_release.py
scripts/verify_schemas.py
```

Use lowercase kebab case for shell scripts:

```text
scripts/check-contracts.ps1
scripts/check-contracts.sh
```

Rules:

- name describes one operation;
- no generic `util.py`;
- maintenance scripts must not duplicate application business logic;
- stable user-facing operations should migrate into the CLI.

---

# 61. Environment variable names

Environment variables use uppercase snake case with prefix:

```text
GF_WORDBENCH_
```

Examples:

```text
GF_WORDBENCH_GF_EXECUTABLE
GF_WORDBENCH_RGL_ROOT
GF_WORDBENCH_OUTPUT_ROOT
GF_WORDBENCH_LOG_LEVEL
```

GF-owned variables keep upstream names:

```text
GF_LIB_PATH
```

Rules:

- do not invent unprefixed framework variables;
- project identity should not depend on environment variables unless explicitly designed;
- environment aliases require deprecation and migration policy;
- variable names are public contracts once documented.

---

# 62. Schema identifiers

Schema IDs use lowercase dotted names:

```text
gf-wordbench.project
gf-wordbench.app-state
gf-wordbench.run-summary
gf-wordbench.artifact-manifest
gf-wordbench.scenario-output
gf-wordbench.gold
```

Rules:

- lowercase ASCII;
- prefix `gf-wordbench.`;
- hyphens allowed inside components where established;
- stable and never reused;
- version stored separately;
- not filenames;
- not Python import paths.

Do not use:

```text
GFWordbenchSummary
gf_wordbench_summary
summary-v1
```

as canonical schema IDs.

---

# 63. Contract identifiers

Framework contract IDs use the family defined by the framework lock.

Project contract IDs use:

```text
PIFC-<DOMAIN>-<NUMBER>
```

or the active canonical project-lock family when finalized.

External contract IDs use:

```text
EXT-<DOMAIN>-<NUMBER>
```

Migration IDs use:

```text
MIG-<DOMAIN>-<NUMBER>
```

Error codes use:

```text
GF-WB-<DOMAIN>-<NUMBER>
```

Rules:

- uppercase ASCII;
- hyphen separated;
- zero-padding policy consistent within one registry;
- IDs are never reused;
- filenames do not need to repeat every ID unless the document is one record per file.

---

# 64. Project identifiers

Canonical project ID uses:

```text
lowercase-kebab-case
```

Examples:

```text
example-language
albanian
rgl-sqi
```

Rules:

- stable;
- ASCII;
- begins with a letter;
- contains letters, digits, and single hyphens;
- no leading or trailing hyphen;
- no consecutive hyphens;
- not a display name;
- changing it is a breaking project migration.

---

# 65. Language codes

Language code format belongs to project policy.

Preferred forms:

```text
ISO 639 code when applicable
stable project-approved lowercase code
```

Examples:

```text
en
fr
sqi
```

Rules:

- lowercase in project metadata unless an external standard requires case;
- do not assume language code equals GF module suffix;
- do not embed code redundantly in every project filename;
- change requires project identity review.

---

# 66. Mode names in filenames

Canonical validation modes:

```text
quick
checkpoint
release
diagnostic
```

These names may appear in generated exports or test fixtures:

```text
quick_run.json
release_expected.json
```

Do not generate canonical files using legacy mode names:

```text
file
all
```

Legacy fixtures may retain them with clear `legacy` naming.

---

# 67. Status names in filenames

Statuses are not normally embedded in canonical artifact filenames.

Avoid:

```text
GrammarEng_FAIL.log
parse_OK.out
```

Status belongs in structured results and reports.

Status suffixes may be used in test fixture cases:

```text
summary_overall_error.json
scenario_skipped.json
```

This distinction prevents filenames from becoming stale when content changes.

---

# 68. Version numbers in filenames

Do not add version numbers to ordinary active source or documentation filenames.

Avoid:

```text
compiler_v2.py
ARCHITECTURE_V3.md
parse_v2.gfs
project_1_0.toml
```

Version numbers are appropriate for:

```text
release packages
schema fixtures
migration fixtures
published exports
compatibility snapshots
```

Examples:

```text
run_summary_v1_0_valid.json
example-language-1.2.0.zip
```

---

# 69. Dates in filenames

Do not add dates to active canonical filenames.

Dates may appear in:

```text
run IDs
dated exports
migration evidence
release archives when policy requires
historical snapshots
```

Use:

```text
YYYYMMDD
```

or:

```text
YYYY-MM-DD
```

according to the owning format.

Run directory IDs use compact UTC form.

Human archival documents may use ISO date.

Avoid locale-dependent forms:

```text
07-22-26
22juillet2026
July22
```

---

# 70. Extension case

Canonical extensions are lowercase:

```text
.py
.md
.toml
.json
.txt
.log
.gf
.gfs
.gfo
.pgf
.gold
.out
.tsv
.csv
.dot
.svg
.zip
```

Locked historical aggregate files may retain uppercase `.TXT` where already canonical.

Do not create new mixed-case extensions.

Double extensions are permitted when they express a real format:

```text
.stdout.txt
.stderr.txt
.candidate.gold
.tar.gz
.zip.sha256
```

---

# 71. MIME and extension consistency

File extension must match content.

Examples:

| Content | Extension |
|---|---|
| JSON object | `.json` |
| TOML configuration | `.toml` |
| Markdown | `.md` |
| Plain text | `.txt` |
| Raw log stream | `.txt` or `.log` according to owner |
| GF source | `.gf` |
| GF script | `.gfs` |
| Reviewed gold | `.gold` |
| Normalized scenario output | `.out` |
| Tabular tab-separated data | `.tsv` |

Do not store JSON in `.txt` merely to avoid schema responsibilities.

---

# 72. Hidden files

Hidden dotfiles are reserved for:

```text
tool configuration
disposable state
atomic temporary files
locks/sentinels
version-control metadata
```

Canonical state:

```text
.gf_wordbench_state.json
```

Legacy:

```text
.gf_audit_state.json
```

Rules:

- state filename is exact;
- project configuration is not hidden;
- project source assets are not hidden;
- hidden temporary files are excluded from discovery.

---

# 73. State filename

Canonical:

```text
.gf_wordbench_state.json
```

Legacy read-only source:

```text
.gf_audit_state.json
```

Rules:

- current writer emits only `.gf_wordbench_state.json`;
- one state file per application scope;
- state must not be confused with project configuration;
- do not add version numbers to filename;
- schema version lives inside the JSON.

---

# 74. Manifest roles versus filenames

Artifact roles are stable machine identifiers.

They do not need to equal filenames.

Examples:

```text
role: summary_json
path: summary.json

role: compile_stderr
path: raw/compile/GrammarEng.stderr.txt
```

Rules:

- roles use lowercase snake case;
- filenames follow their naming family;
- consumers use manifest role and path, not role-to-filename guessing;
- adding a role requires schema/registry review.

---

# 75. Collision policy

Before creating a framework-controlled file, the owner must detect:

```text
exact collision
case-insensitive collision
normalized-path collision
safe-key collision
reserved-name collision
file-versus-directory collision
```

Resolution order:

```text
1. preserve canonical logical identity
2. add deterministic hash suffix
3. increase hash length if collision persists
4. fail rather than overwrite unrelated content
```

Do not resolve collisions with nondeterministic counters unless the counter is part of a defined immutable run-ID policy.

---

# 76. Windows reserved names

Framework-generated path segments must reject Windows device names, case-insensitively:

```text
CON
PRN
AUX
NUL
COM1
COM2
COM3
COM4
COM5
COM6
COM7
COM8
COM9
LPT1
LPT2
LPT3
LPT4
LPT5
LPT6
LPT7
LPT8
LPT9
```

Also reject these names with extensions:

```text
CON.txt
NUL.log
```

A user-owned source using an unsupported reserved path cannot be represented safely on Windows and should produce a configuration error.

---

# 77. Prohibited path segments

Framework-generated paths must reject:

```text
.
..
empty segment
segment ending in space
segment ending in dot
control characters
NUL byte
path separator inside segment
reserved device name
```

Project-relative canonical paths must also reject:

```text
drive letter
UNC prefix
absolute root
unresolved traversal
```

Environment absolute paths may contain drive letters or UNC roots when supported.

---

# 78. Symlink naming and ownership

A symlink name follows the same naming family as the intended path.

Rules:

- symlinks are not used to bypass canonical ownership;
- project and run containment checks resolve symlinks according to security policy;
- generated artifacts must not overwrite through unsafe symlinks;
- migration backups must preserve or explicitly resolve symlink semantics;
- manifest records the actual supported artifact type.

Do not create symlink aliases as a substitute for migration without documenting them as compatibility adapters.

---

# 79. Case-only renames

Case-only renames are risky on Windows.

Required process:

```text
old name
→ temporary distinct name
→ canonical new name
```

Version control must record both steps correctly.

Applies to:

```text
GF modules
documentation files
scenario IDs
gold files
report filenames
```

A case-only rename of a public name is still a migration.

---

# 80. Naming and discovery

Discovery code must use explicit patterns.

Examples:

```text
Python tests: test_*.py
GF sources: configured glob, usually *.gf
Scenarios: registered *.gfs files
Golds: registry-owned <scenario-id>.gold
Runs: run_<run-id> plus valid summary/manifest checks
```

Do not discover active assets solely because a file extension exists.

Configuration and registries remain authoritative.

---

# 81. Naming and ordering

Filename order is not always semantic.

Canonical order sources:

| Asset | Order source |
|---|---|
| File results | normalized project-relative path |
| Scenarios | project configuration order |
| Checkpoints | project configuration order |
| Entrypoints | project configuration order |
| ADRs | numeric ID |
| Top errors | count then message |
| Diff entries | severity then identity |

Do not add numeric filename prefixes to force order when configuration owns order.

---

# 82. Naming and ownership

Every canonical generated filename has one writer.

Examples:

| Filename family | Owner |
|---|---|
| `summary.json` | JSON report writer |
| `summary.md` | Markdown report writer |
| `AI_READY.md` | AI report writer |
| `top_errors.txt` | top-error/report writer |
| `manifest.json` | manifest writer |
| `*.stdout.txt` | process/stage evidence owner |
| `*.stderr.txt` | process/stage evidence owner |
| `*.scan.txt` | scanner/log owner |
| `*.gold` | explicit gold updater/maintainer |
| `.gf_wordbench_state.json` | state manager |

A reader must not rewrite an asset merely because it knows its filename.

---

# 83. Naming and schemas

A filename change is a schema change when:

```text
the filename is persisted
another component constructs it
a manifest role depends on it
automation expects it
a report links it
run discovery depends on it
```

Examples:

```text
summary.json
manifest.json
AI_READY.md
project/project.toml
<scenario-id>.gold
```

Private temporary filename changes do not require schema versioning unless discovery or cleanup depends on them.

---

# 84. Naming and security

Never include in generated filenames:

```text
passwords
tokens
email addresses
full command lines
unredacted environment values
absolute user profile paths
raw user input without sanitization
```

A human display label may contain such text only when explicitly supplied and safe.

Generated safe keys use sanitized stable identities.

Raw unsafe identity remains in structured evidence when needed, not in filesystem names.

---

# 85. Naming and logs

Log filenames identify the subject and stream.

Log contents carry timestamps and statuses.

Do not encode:

```text
current status
error count
timestamp of every event
user message
```

into a mutable log filename.

One run owns immutable evidence names.

If multiple attempts exist, use an explicit attempt suffix:

```text
<safe-key>.attempt-01.stdout.txt
<safe-key>.attempt-02.stdout.txt
```

Attempts require a bounded retry contract.

---

# 86. Naming retries and attempts

Attempt suffix format:

```text
.attempt-<two-digit-number>
```

Example:

```text
parse.attempt-01.stdout.txt
parse.attempt-02.stdout.txt
```

Rules:

- first attempt may omit suffix only when no retry is possible;
- when retries are supported, consistent suffixing for every attempt is preferred;
- final result references all attempts;
- do not overwrite failed-attempt evidence.

---

# 87. Naming exports

Explicit exports use a descriptive stem:

```text
run-export-<run-id>.zip
project-export-<project-id>-<date>.zip
migration-report-<migration-id>.md
```

Rules:

- exports are not canonical source;
- include identity sufficient to distinguish contents;
- avoid `export.zip`;
- use stable UTC or ISO date where needed;
- manifest or export metadata describes internal versions.

---

# 88. Naming database-like snapshots

GF Wordbench does not currently require a database.

If snapshot files are introduced, use:

```text
<domain>-snapshot-<version-or-date>.<extension>
```

Only introduce them with a schema and lifecycle.

Do not accumulate ad hoc JSON snapshots under ambiguous names.

---

# 89. Naming project clones

Clone directories outside the repository may use:

```text
GF_Wordbench_<project-id>
```

or a user-selected local path.

Inside one framework repository, the active project remains:

```text
project/
```

Do not rename the active project directory to the language ID.

This preserves framework tooling and template assumptions.

---

# 90. Template directory naming

Canonical template root:

```text
templates/project/
```

The template mirrors active project structure.

Rules:

- `project` is lowercase;
- no template version in directory name;
- version belongs in metadata or release policy;
- old template fixtures may use versioned names under tests:

```text
tests/fixtures/project_template_v1/
```

Do not keep multiple active template roots such as:

```text
project-template
project_new
project_v2
```

---

# 91. Template placeholder naming

Placeholders use uppercase angle-bracket form in Markdown:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<PROJECT_ROOT>
<MODULE_SUFFIX>
<YYYY-MM-DD>
```

In TOML examples, placeholder strings may use:

```toml
id = "<project-id>"
```

Rules:

- active project must replace required placeholders;
- placeholders must be visually distinct;
- do not use realistic values that could be mistaken for completed configuration;
- placeholder names use uppercase snake case in normative templates.

---

# 92. Unknown or undecided names

Do not invent a permanent name for an unresolved responsibility.

Temporary planning references may use:

```text
<PROPOSED_COMPONENT>
<TBD>
```

only in planning documents.

They must not appear in:

```text
active project configuration
canonical schemas
generated artifacts
release manifests
public Python imports
```

Before implementation, the owner selects a canonical name.

---

# 93. Abbreviation policy

Use abbreviations only when established and unambiguous.

Accepted examples:

```text
GF
PGF
RGL
CLI
GUI
JSON
TOML
AI
ID
UTC
CPU
IO
API
```

Avoid project-local unexplained abbreviations in filenames.

Prefer:

```text
project_config.py
```

over:

```text
proj_cfg.py
```

Prefer:

```text
diagnostics.py
```

over:

```text
diag.py
```

unless brevity is already a stable public convention.

---

# 94. Singular versus plural

Use singular when the module owns one service or concept:

```text
compiler.py
scanner.py
classifier.py
fingerprint.py
state.py
bootstrap.py
```

Use plural when the module is a collection or registry:

```text
diagnostics.py
models.py
contracts.py
```

The existing canonical component map takes precedence over stylistic preference.

Do not rename solely to switch singular/plural without a responsibility change.

---

# 95. Prefix and suffix policy

Reserved useful suffixes:

```text
_config
_result
_request
_summary
_manifest
_reference
_policy
_model
_service
_runner
_writer
_reader
_migration
```

Use only when they clarify responsibility.

Avoid redundant names:

```text
config_configuration.py
result_model_result.py
report_writer_report.py
```

Reserved temporary anti-pattern suffixes:

```text
_new
_old
_final
_latest
_copy
_backup
_fixed
_v2
```

These must not appear in active canonical names.

---

# 96. Naming services

A service module may use:

```text
<domain>_service.py
```

only when it coordinates a coherent application operation.

Example:

```text
gold/update_service.py
projects/migration_service.py
```

Do not append `_service` to every module.

A pure domain operation can remain:

```text
compiler.py
scanner.py
diff.py
```

---

# 97. Naming readers and writers

Use explicit names when multiple formats exist:

```text
report_json.py
report_markdown.py
report_ai.py
manifest_writer.py
summary_reader.py
project_loader.py
```

Where one owner both reads and writes one format, a domain name may be enough:

```text
state.py
project_config.py
```

Avoid generic:

```text
reader.py
writer.py
parser.py
```

at broad package scope.

---

# 98. Naming migrations in code

Migration modules use:

```text
migrate_<source>_to_<target>.py
```

or one domain-owned migration registry.

Examples:

```text
migrate_gf_audit_state.py
migrate_summary_v0_to_v1.py
migrate_project_v1_to_v2.py
```

Rules:

- current target is clear;
- no `migration2.py`;
- completed migration modules may remain for support;
- if many migrations exist, group by domain and version;
- migration IDs remain documented independently of filenames.

---

# 99. Naming compatibility modules

Temporary compatibility modules may use:

```text
legacy_<domain>.py
compat_<domain>.py
```

Examples:

```text
legacy_summary.py
compat_modes.py
```

Rules:

- one canonical implementation remains elsewhere;
- compatibility module delegates;
- module is not imported by new core code except at compatibility boundary;
- removal target exists;
- filename does not become the new permanent owner.

---

# 100. Naming deprecated assets

Do not rename an active deprecated public asset merely to add `deprecated`.

Keep its stable name during the compatibility window.

Mark deprecation in:

```text
contract registry
documentation
warnings
changelog
```

After removal, historical fixtures may use a `legacy_` or versioned directory.

Renaming the deprecated asset early would itself be another breaking change.

---

# 101. Naming retired contracts

Retired contract records keep their original IDs and titles.

Do not move them into files named:

```text
old_contracts.md
unused.md
archive2.md
```

They may remain in the authoritative lock with status `Retired`.

A separate archive is allowed only when the lock preserves a clear index and history.

---

# 102. Naming legacy files

Legacy compatibility files must be clearly marked in fixture or migration directories.

Examples:

```text
legacy_state_unversioned.json
legacy_summary_flat.json
legacy_mode_all.json
```

Do not rename actual historical source files before migration detection unless a backup preserves the original identity.

The migrator should recognize source form from content and documented filename where applicable.

---

# 103. `gf-audit` legacy naming

Canonical migration mappings:

| Legacy name | Current name |
|---|---|
| `gf-audit` | `gf-wordbench` |
| `.gf_audit_state.json` | `.gf_wordbench_state.json` |
| `mode=file` | `mode=quick` |
| `mode=all` | `mode=diagnostic` |
| `ai_brief_path` | `artifacts.ai_ready` |
| old unversioned summary | `summary.json` with schema ID/version |

Rules:

- current filenames and writers use GF Wordbench identity;
- historical fixtures preserve old names;
- compatibility code may recognize old names;
- new docs must not present legacy names as canonical.

---

# 104. Naming migration outputs

Recommended migration report:

```text
migration-<migration-id>.md
```

Optional structured report after schema registration:

```text
migration-<migration-id>.json
```

Backup root:

```text
migration-backup/<migration-id>/
```

Candidate destination:

```text
<canonical-name>.candidate
```

or an owned output directory.

Names must distinguish:

```text
source
candidate
destination
backup
report
```

---

# 105. Naming hashes and checksum files

Checksum sidecar:

```text
<filename>.sha256
```

Content should follow the release checksum contract.

Do not use:

```text
<filename>.hash
checksum.txt
```

for a stable release unless one aggregate checksum manifest is explicitly defined.

Source fingerprints belong in structured data, not sidecar files by default.

---

# 106. Naming compressed artifacts

Canonical forms:

```text
.tar.gz
.zip
```

Avoid ambiguous multiple archives such as:

```text
.zip.zip
final.zip
latest.zip
```

Archive contents should have one stable top-level directory when distributed externally:

```text
<project-id>-<project-version>/
```

This release behavior requires explicit packaging policy.

---

# 107. Naming generated graphs

Recommended:

```text
dependency-graph.dot
dependency-graph.svg
component-map.dot
component-map.svg
```

When scoped:

```text
project-dependency-graph.svg
framework-component-map.svg
```

Graph source and rendered output use the same stem.

Graphviz remains optional unless an external-tool contract makes it required.

---

# 108. Naming screenshots and images

Documentation images use:

```text
lowercase-kebab-case.<extension>
```

Examples:

```text
gui-main-window.png
validation-flow.svg
project-layout.svg
```

Store under a documented images/assets directory:

```text
docs/assets/
```

or domain-specific equivalent.

Avoid:

```text
Screenshot 2026-07-22.png
image1.png
final-diagram.png
```

Alt text and document references provide meaning beyond filename.

---

# 109. Naming sample configuration files

Examples should use:

```text
project.example.toml
state.example.json
```

only when they are not the canonical active files.

Templates use the canonical filename inside the template directory:

```text
templates/project/project.toml
```

Do not put an example file beside the canonical active project where discovery may confuse them.

---

# 110. Naming local overrides

GF Wordbench should avoid project-local override files unless explicitly designed.

If introduced, use a clear non-canonical filename such as:

```text
project.local.toml
```

with:

- explicit precedence;
- versioned schema;
- `.gitignore` policy;
- no project identity override unless permitted;
- no silent discovery.

Do not introduce `config.local`, `.env`, or similar files informally.

---

# 111. Naming `.env` files

Environment files are not canonical GF Wordbench project configuration.

If development tooling uses them:

```text
.env
.env.example
```

Rules:

- never commit secrets;
- application behavior must document whether `.env` is loaded;
- project identity must not depend on undocumented `.env`;
- `.env.example` contains placeholders only.

No automatic `.env` support should be assumed without implementation and security review.

---

# 112. Naming branches and tags

Repository branch names are not strict file names, but recommended forms are:

```text
feature/<short-kebab-name>
fix/<short-kebab-name>
release/<major>.<minor>
```

Package tags:

```text
v<MAJOR>.<MINOR>.<PATCH>
```

Project tags may use:

```text
project-<project-id>-v<MAJOR>.<MINOR>.<PATCH>
```

only if release policy defines them.

Do not let branch names determine runtime project identity.

---

# 113. Naming issue and decision references

Issue references should remain in document content, not filenames, unless the file is specifically one record.

Decision log entries may use stable IDs inside:

```text
DECISION_LOG.md
```

Do not create many files named by ticket unless the project intentionally adopts one-file-per-decision records.

ADRs remain the framework-level exception with dedicated filenames.

---

# 114. Naming report sections versus files

A new report section does not imply a new report file.

Create a separate report file only when it has:

```text
distinct audience
distinct lifecycle
distinct artifact role
distinct writer or consumer
```

Avoid fragmentation:

```text
status.md
totals.md
errors.md
paths.md
```

when these belong inside `summary.md`.

---

# 115. Naming one-off diagnostics

One-off debug files belong under a run-local debug directory if explicitly enabled:

```text
raw/debug/
```

Recommended names:

```text
<safe-key>.<purpose>.txt
```

Examples:

```text
GrammarEng.command.txt
parse.normalization-debug.txt
```

Debug files are not canonical report contracts unless persisted consumers appear.

Do not write debug files into source directories.

---

# 116. Naming crash reports

Recommended:

```text
raw/crash-<utc-timestamp>.log
```

or:

```text
raw/framework-error.log
```

according to whether multiple crashes can occur in one run.

Crash report naming requires:

- redaction;
- bounded size;
- ownership;
- manifest policy if retained;
- no secrets in filename.

Do not use raw exception text as filename.

---

# 117. Naming cancellation evidence

Cancellation does not require renaming result files.

Use structured status/evidence.

Optional event log:

```text
raw/cancellation.log
```

only if a dedicated artifact is justified.

Do not suffix all partial files with `_cancelled`; their content and structured result already record interruption.

---

# 118. Naming failed and partial runs

Run directory name remains:

```text
run_<run-id>
```

regardless of outcome.

Do not rename to:

```text
failed_run_...
error_run_...
cancelled_run_...
```

Outcome belongs in `summary.json`, logs, and finalization markers.

Incomplete-run discovery uses validated contents or a defined sentinel, not basename prefixes.

---

# 119. Naming archived runs

When archived externally:

```text
run_<run-id>.zip
```

or:

```text
<project-id>-run-<run-id>.zip
```

Do not alter the internal run directory name.

Archive naming must not imply successful release unless the contents prove it.

---

# 120. Naming cleanup candidates

Cleanup operations should identify assets through manifests and validated run directories.

Do not decide deletion based only on names such as:

```text
old
tmp
backup
```

A matching name is not sufficient authorization to delete.

---

# 121. Name validation functions

The framework should centralize validation for:

```text
project IDs
scenario IDs
schema IDs
contract IDs
safe keys
project-relative paths
run-relative paths
generated basenames
```

Recommended ownership:

```text
app/utils/path_utils.py
app/models.py or focused identifier models
```

Do not duplicate regexes in CLI, GUI, project loader, and report writers.

---

# 122. Recommended identifier patterns

Conceptual patterns:

```text
project-id:
  ^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$

scenario-id:
  ^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$

schema-id:
  ^gf-wordbench\.[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$

error-code:
  ^GF-WB-[A-Z][A-Z0-9]*-[0-9]{3}$

migration-id:
  ^MIG-[A-Z][A-Z0-9]*-[0-9]{3}$

external-contract-id:
  ^EXT-[A-Z][A-Z0-9]*-[0-9]{3}$
```

The exact implemented regex belongs to the identifier owner and tests.

Changing an accepted public identifier pattern requires compatibility review.

---

# 123. Validation error messages

Naming validation errors should identify:

```text
invalid value
expected pattern
owning field
prohibited character or segment
example valid value
```

Example:

```text
Invalid scenario ID 'Parse_Test'.
Use lowercase kebab case, for example 'parse-test'.
```

Do not silently sanitize user-owned public identifiers.

For generated safe keys, sanitization is expected because the logical identity remains separately preserved.

---

# 124. Silent sanitization policy

Allowed silent sanitization:

```text
generated temporary token
generated safe target key
display-only archive suggestion
```

Prohibited silent sanitization:

```text
project ID
scenario ID
GF module name
schema ID
contract ID
gold ownership
entrypoint name
```

Public identifiers must be accepted exactly or rejected clearly.

---

# 125. Renaming workflow

Any public rename must document:

```text
old name
new name
reason
owner
providers
consumers
aliases
migration
deprecation
version impact
tests
```

Required updates may include:

```text
source file
imports
configuration
schemas
reports
manifest
CLI/GUI
scenarios
golds
documentation
fixtures
release notes
```

Renaming is not complete when only the filesystem entry changes.

---

# 126. Rename categories

## 126.1 Private rename

No external consumer.

Requires normal tests.

## 126.2 Compatible alias rename

Old public name remains temporarily as an alias.

Requires deprecation and adapter tests.

## 126.3 Persisted path rename

Requires schema migration.

## 126.4 Project GF rename

Requires project contract migration.

## 126.5 Scenario/gold rename

Requires project configuration, gold, reports, and comparison identity migration.

## 126.6 Report filename rename

Requires artifact schema, manifest, reader, GUI/CLI, and migration review.

---

# 127. Case-preserving but case-insensitive compatibility

Readers on Windows may accept legacy case variations only when documented.

Canonical writers emit exact case.

Example:

```text
legacy: ai_ready.md
canonical: AI_READY.md
```

Do not add broad case-insensitive fallback for every file.

It can hide duplicate or malicious files.

Prefer explicit alias mapping.

---

# 128. Naming and source-control ignores

Generated names should support clear ignore patterns:

```text
runs/
.gf_wordbench_state.json
*.gfo
*.pgf
*.tmp
```

Project-controlled gold, scenarios, inputs, and docs must not be ignored.

Source-adjacent `.gfo` and `.pgf` ignore rules must not prevent release artifact collection under run-owned directories.

Review `.gitignore` whenever generated naming changes.

---

# 129. Naming and packaging includes

Packaging configuration must include:

```text
Python source
required templates
required documentation if distributed
schema fixtures or resources required at runtime
```

It must exclude:

```text
runs
state files
temporary files
migration backups
developer-local artifacts
active project source unless distribution policy includes it
```

Names and paths in package data configuration are contracts.

---

# 130. Naming and import resources

Runtime resource files should live under a focused package resource directory.

Example:

```text
app/resources/
app/resources/schemas/
app/resources/templates/
```

Only create these when runtime packaging needs them.

Do not make Python code depend on repository-relative documentation paths unless explicitly designed.

---

# 131. Naming JSON/TOML keys versus files

File naming family and key naming family may differ.

Examples:

```text
file: project.toml
key: project_id or [project].id

file: summary.json
key: file_results
```

JSON and internal TOML keys generally use lowercase snake case.

Schema IDs use lowercase dotted names.

Do not mirror uppercase documentation filenames into JSON keys.

---

# 132. Naming report links

Reports should use human labels and owned paths.

Example:

```markdown
[Open stderr](raw/compile/GrammarEng.stderr.txt)
```

The link target comes from structured artifact paths.

Do not reconstruct names from module names in report code.

A naming change then remains centralized.

---

# 133. Naming within manifests

Manifest path values are run-relative canonical paths.

Artifact IDs or roles use lowercase snake case.

Example:

```json
{
  "role": "compile_stderr",
  "path": "raw/compile/GrammarEng.stderr.txt"
}
```

Rules:

- path is unique;
- role may repeat for multiple subjects;
- subject identity is stored separately when schema supports it;
- filename alone does not determine role.

---

# 134. Naming current and previous runs

Do not name a previous run:

```text
previous
last
latest
```

as its canonical directory.

Those are dynamic references.

A pointer or state record may refer to a stable run ID.

Symlink aliases such as `latest` require explicit platform and cleanup policy and should not be canonical persisted identities.

---

# 135. Naming user-selected output roots

The user may select any valid output-root directory.

Within it, GF Wordbench creates canonical run directories.

Do not require the output-root basename to be `runs`.

Code must not infer semantics from the parent directory name.

---

# 136. Naming custom project source roots

The configured source root may follow upstream naming conventions.

GF Wordbench must preserve it.

Framework-generated child directories still use canonical rules.

If the source root contains unsupported names for a target platform, validation should report the incompatibility instead of silently renaming source.

---

# 137. Naming copied projects

A clone/reset operation may create staging directories:

```text
.project-staging
.project-backup
```

only within an owned parent and with explicit lifecycle.

Final active directory remains:

```text
project
```

Staging must not be discoverable as active project.

Atomic directory replacement policy must be documented before use.

---

# 138. Naming import reports

Recommended:

```text
project-import-report.md
project-import-inventory.json
```

If multiple imports coexist:

```text
project-import-<migration-id>.md
```

Do not name:

```text
report.md
import.txt
results.json
```

outside a uniquely owned directory.

---

# 139. Naming release evidence

Release evidence may use:

```text
release-evidence.md
release-manifest.json
```

only after the release schema and owner are defined.

Until then, release evidence belongs in canonical run reports and project documentation.

Do not introduce competing summary files without a distinct role.

---

# 140. Naming status ledgers and decision logs

Canonical project files:

```text
STATUS_LEDGER.md
DECISION_LOG.md
KNOWN_ISSUES.md
```

Entries inside them use stable IDs when needed.

Do not create:

```text
STATUS_LEDGER_2.md
DECISIONS_NEW.md
ISSUES_FINAL.md
```

Split only when scale and ownership justify a versioned structural change.

---

# 141. Naming generated documentation indexes

Generated indexes may use:

```text
DOCUMENTATION_MAP.md
SCHEMA_INDEX.md
```

If generated, they must indicate generation ownership inside content.

Do not append `_GENERATED` to a public canonical filename unless users must distinguish it.

Generation status is metadata, not necessarily filename identity.

---

# 142. Naming command output files

A CLI option selecting a custom output file must validate:

- extension;
- parent path;
- overwrite policy;
- path containment when required.

Default output names remain canonical.

A user-selected custom export name is not automatically persisted as a standard artifact path.

---

# 143. Naming overwrite behavior

Writers must classify destination behavior:

```text
create-only
replace-owned
append-owned
user-confirmed overwrite
```

Filename alone must not imply permission to overwrite.

Canonical report writers replace their owned run files during finalization only according to run lifecycle.

Gold writers require explicit update authorization.

Project source writers require explicit project/migration operation.

---

# 144. Naming append-only files

Append-only logs use stable names:

```text
master.log
```

When concurrency or crash safety requires segmented logs:

```text
master.part-001.log
master.part-002.log
```

Segmentation requires an aggregation contract.

Do not create uncontrolled numbered files.

---

# 145. Naming rotations

GF Wordbench run evidence is immutable per run and should not need log rotation inside one run.

Application-global logs, if introduced, may use:

```text
gf-wordbench.log
gf-wordbench.log.1
```

only with an explicit logging policy.

Do not rotate canonical run reports.

---

# 146. Naming cache directories

No cache is required by the core architecture.

If introduced:

```text
.gf-wordbench-cache/
```

or an environment cache location.

Requirements:

- clear ownership;
- schema/version;
- invalidation;
- safe cleanup;
- never treated as release evidence;
- excluded from project source discovery.

Do not name an unversioned cache simply `cache/` inside active project source.

---

# 147. Naming virtual environments

Development environments may use:

```text
.venv/
```

This is not a GF Wordbench runtime contract.

It should be ignored by source discovery and version control.

Do not encode `.venv` location into project configuration.

---

# 148. Naming coverage and test outputs

Recommended conventional names:

```text
.coverage
htmlcov/
.pytest_cache/
```

These are tool-owned and excluded from project/run discovery.

Framework documentation should not redefine upstream tool conventions unnecessarily.

---

# 149. Naming static-analysis outputs

Use tool conventions or explicit report names:

```text
mypy-report.txt
ruff-report.txt
coverage.xml
junit.xml
```

Only when automation requires retained outputs.

These are build/CI artifacts, not GF Wordbench run artifacts unless integrated deliberately.

---

# 150. Naming CI workflow files

When using GitHub Actions:

```text
.github/workflows/test.yml
.github/workflows/release.yml
.github/workflows/gf-integration.yml
```

Use lowercase kebab case.

Names should describe workflow purpose.

Do not use `main.yml` for every workflow.

Other CI systems should follow their ecosystem conventions.

---

# 151. Naming project release tags

A language project may use:

```text
<project-id>-v<MAJOR>.<MINOR>.<PATCH>
```

Example:

```text
example-language-v1.2.0
```

Use only if framework and project releases share a repository and need disambiguation.

If the repository contains only the project release line, simple `v1.2.0` may be appropriate.

The release policy owns the final tag form.

---

# 152. Naming local scratch work

Local scratch files should live outside active directories or under an ignored scratch root:

```text
scratch/
```

The directory must be excluded from:

```text
source selection
scenario discovery
gold discovery
packaging
release evidence
```

Avoid placing scratch files beside canonical sources with similar extensions.

---

# 153. Naming examples in documentation

Examples should use plausible neutral identifiers:

```text
ExampleLanguage
example-language
GrammarEx
SyntaxEx
parse-basic
```

Do not use the active language as a universal framework default.

Do not use a real personal path when a generic path works.

Windows examples may use:

```text
C:/work/GF_Wordbench
```

or the user’s documented repository root when the document is project-specific.

---

# 154. Naming error examples

Use names that indicate the fault:

```text
missing-schema-id.json
path-escape.json
duplicate-scenario-id.toml
```

In test fixtures, underscores may be preferred for Python-oriented file sets:

```text
missing_schema_id.json
```

Choose one convention per fixture directory.

Do not mix without reason.

---

# 155. Naming generated IDs

Generated identifiers such as run IDs must be:

```text
deterministic where derived
collision-safe
portable
bounded
non-secret
```

Random UUIDs may be used only when a human-readable run ID is insufficient.

If used, canonical form is lowercase hexadecimal with hyphens.

Do not include UUIDs in every filename when one run directory already provides uniqueness.

---

# 156. Naming process IDs

Operating-system process IDs may appear in temporary filenames for collision avoidance:

```text
.summary.json.18420.tmp
```

They must not become canonical persisted identity.

PID reuse means it is not sufficient alone for long-lived uniqueness.

Combine with an owned random token when needed.

---

# 157. Naming timestamps

Generated timestamp format must be explicit.

Run ID:

```text
YYYYMMDD_HHMMSS
```

RFC 3339 inside data:

```text
YYYY-MM-DDTHH:MM:SSZ
```

Human release date:

```text
YYYY-MM-DD
```

Do not use one format interchangeably for every purpose.

---

# 158. Naming hashes in filenames

Use short hashes only for disambiguation.

Format:

```text
lowercase hexadecimal
```

Examples:

```text
a1b2c3d4
```

Full source fingerprints remain in structured metadata.

Do not include full SHA-256 in filenames unless immutable content-addressed storage is explicitly adopted.

---

# 159. Naming content-addressed artifacts

GF Wordbench does not currently require content-addressed storage.

If introduced, use a dedicated directory:

```text
artifacts/by-sha256/<full-hash>
```

with a manifest mapping logical identity to content identity.

Do not mix content-addressed names with human-owned canonical report names.

---

# 160. Naming policy for future plugins

A dynamic plugin system is not part of the current core architecture.

If introduced, plugin IDs should use:

```text
reverse-domain or lowercase dotted identifier
```

Example:

```text
org.example.gf-wordbench.graphviz
```

Plugin filenames and package names would require a separate plugin contract.

Do not reserve or create plugin directories preemptively.

---

# 161. Naming optional tools

External tool configuration keys use descriptive lowercase snake case:

```text
graphviz_executable
archive_executable
```

Do not place tool names in generic filenames unless the artifact is tool-specific.

Example:

```text
dependency-graph.dot
```

is preferable to:

```text
graphviz-output.dot
```

because the artifact purpose matters more than the implementation tool.

---

# 162. Naming deprecation aliases

Aliases are stored in code or migration registries, not by creating duplicate canonical files.

Example:

```text
ai_brief_path → artifacts.ai_ready
```

Do not create both:

```text
AI_BRIEF.md
AI_READY.md
```

as current outputs merely to support an alias.

---

# 163. Naming compatibility exports

When an old external consumer needs a transitional format, use an explicit export name:

```text
summary.legacy.json
```

or:

```text
legacy-summary-export.json
```

only through a dedicated compatibility command.

The canonical `summary.json` remains current.

The export must identify its legacy schema.

---

# 164. Naming project-specific reports

Project-specific persistent reports should live under project documentation only when they are maintained source artifacts.

Generated reports belong in run directories.

Examples:

```text
project/docs/RESEARCH_EVIDENCE.md
run_<id>/summary.md
```

Do not write generated audit reports into `project/docs/` automatically.

---

# 165. Naming research evidence files

Supporting source documents may use:

```text
project/docs/research/
```

if the project needs multiple files.

Filenames should use:

```text
lowercase-kebab-case.md
```

or source-preserving names for imported evidence.

The canonical summary remains:

```text
RESEARCH_EVIDENCE.md
```

Do not create this subdirectory unless scale justifies it.

---

# 166. Naming corpus and linguistic data files

Use descriptive lower-kebab names with real format extensions:

```text
basic-noun-phrases.tsv
verb-regression-cases.tsv
parse-smoke-input.txt
```

Rules:

- include language code only when multiple languages coexist in one data directory;
- active project normally contains one language, so redundant code is unnecessary;
- document encoding and columns;
- avoid `data1.csv`.

---

# 167. Naming generated linguistic outputs

Generated linguistic outputs belong under run artifacts or raw scenario evidence.

Examples:

```text
parse.out
morphology.out
generation.out
```

Do not write generated outputs beside input corpora with names that resemble source.

---

# 168. Naming manual expected outputs

Manual expected outputs should migrate to `.gold` when exact comparison is intended.

Legacy manual files may use:

```text
expected-parse.txt
```

only as historical migration sources.

Current active exact expectations use:

```text
parse.gold
```

Assertion-only expectations belong in scenario configuration or markers, not ambiguous text files.

---

# 169. Naming release criteria files

Canonical project release criteria:

```text
project/docs/RELEASE_CRITERIA.md
```

Framework release policy:

```text
docs/release/RELEASE_PROCESS.md
docs/release/VERSIONING_POLICY.md
docs/release/MIGRATION_AND_DEPRECATION.md
```

Do not create project-specific framework release files under `docs/release/`.

Scope is determined by directory.

---

# 170. Naming licenses and notices

Canonical root:

```text
LICENSE.md
```

or ecosystem-standard `LICENSE` if selected once.

Third-party notices:

```text
THIRD_PARTY_NOTICES.md
```

Project-specific linguistic data licenses may use:

```text
project/LICENSE.md
project/THIRD_PARTY_NOTICES.md
```

only when needed.

Do not rename upstream license files when legal requirements specify exact names.

---

# 171. Naming security-sensitive files

Security reports are not committed under predictable public filenames containing sensitive details.

Repository security policy:

```text
SECURITY.md
```

Generated secret scans or reports belong to protected CI artifacts.

Do not place credentials in:

```text
project.toml
state JSON
run filenames
logs
reports
```

---

# 172. Naming command scripts in scenarios

Native scenario scripts use `.gfs`.

Do not use:

```text
parse.cmd
parse.bat
parse.sh
```

for GF shell content.

External wrapper scripts may exist only when an external-tool contract requires them.

Their filenames must make the wrapper role explicit:

```text
run-parse-scenario.ps1
```

The canonical validation scenario remains `.gfs`.

---

# 173. Naming shell escape outputs

Shell escape is disabled by default.

If explicitly allowed, output files still follow run-owned naming and containment rules.

A command must not choose arbitrary output names from untrusted scenario text.

External artifacts are registered through the scenario result and manifest.

---

# 174. Naming unknown external artifacts

Unknown files produced by GF may be catalogued using their actual basenames when safe.

If a name is unsafe or collides, copy to:

```text
unknown-artifact--<safe-key>.<extension>
```

and preserve original name in metadata.

Do not silently discard unexpected artifacts required for diagnosis.

Do not treat them as required release artifacts without a contract.

---

# 175. Naming orphan files

Orphan detection reports the actual path.

Do not rename or delete an orphan automatically.

Examples:

```text
orphan gold
unregistered scenario
unreferenced input
unexpected .gfo
```

A maintenance command may propose a canonical destination.

User/project owner decides.

---

# 176. Naming check commands

Suggested commands:

```text
gf-wordbench names check
gf-wordbench names check --strict
gf-wordbench project names check
```

Potential checks:

```text
canonical report names
project doc names
scenario/gold pairing
GF module/file match
case-only collisions
Windows reserved names
unsafe path segments
legacy active names
template/project parity
safe-key collisions
```

These commands are future targets until implemented.

---

# 177. Naming check severity

Recommended classifications:

```text
error
warning
info
```

Errors:

```text
path traversal
reserved name
scenario/gold mismatch
GF module/file mismatch
canonical artifact collision
duplicate case-insensitive path
```

Warnings:

```text
noncanonical but supported Unicode source filename
legacy active alias
overlong user-owned path
backup-looking active source
```

Info:

```text
optional naming suggestion
```

Naming severity must not be confused with validation status.

---

# 178. Migration from noncanonical names

Migration process:

```text
inventory
→ classify public/private
→ identify consumers
→ choose canonical name
→ define alias or rename
→ update providers and consumers
→ update persisted paths
→ update scenarios/golds
→ update tests/docs
→ validate
→ retire old name
```

Do not bulk rename before dependency inventory.

---

# 179. Migration from `gf-audit` filenames

Required mappings include:

```text
.gf_audit_state.json
→ .gf_wordbench_state.json
```

Application names:

```text
gf-audit
→ gf-wordbench
```

Legacy run artifact aliases are read from historical summaries.

Current run filenames follow GF Wordbench canonical layout.

Old run directories remain historical and are not renamed automatically.

---

# 180. Migration of documentation names

When renaming a normative document:

- update documentation map;
- update all links;
- update lock references;
- update tests/checkers;
- decide whether a redirect stub is needed;
- preserve Git history;
- document migration.

Avoid document renames for cosmetic preferences.

A stable path is valuable to maintainers and automation.

---

# 181. Migration of scenario/gold names

Required coordinated unit:

```text
scenario ID
.gfs filename
project.toml registry
gold filename
gold header
input filenames where ID-prefixed
summary comparison identity
coverage matrix
contract lock
release evidence
```

Old IDs remain historical.

Do not reuse them for unrelated scenarios.

---

# 182. Migration of GF module names

Required coordinated unit:

```text
.gf filename
module declaration
imports
interfaces/instances
entrypoints
checkpoints
scenario commands
PGF targets
dependency map
contract lock
golds when output identity changes
```

A temporary forwarding module may preserve compatibility.

It must have one canonical provider and a deprecation plan.

---

# 183. Migration of report filenames

Changing:

```text
summary.md
AI_READY.md
manifest.json
```

requires:

```text
persisted schema review
artifact field updates
manifest roles
GUI/CLI links
automation readers
migration aliases
tests
versioning
```

Do not rename stable reports in a patch release for style.

---

# 184. Naming review checklist

```text
[ ] Name belongs to a defined family
[ ] Owner is identified
[ ] Public or private status is known
[ ] Case is canonical
[ ] Extension matches content
[ ] Path base is defined
[ ] Separator policy is correct
[ ] Windows reserved names are rejected
[ ] Case-insensitive collisions are checked
[ ] Length is bounded
[ ] No secret or personal path is embedded
[ ] No development suffix is used
[ ] No unnecessary version/date is used
[ ] Discovery behavior is reviewed
[ ] Persistence impact is reviewed
[ ] Manifest/report impact is reviewed
[ ] Migration is defined when renaming
[ ] Tests cover validation and collisions
```

---

# 185. Framework naming checklist

```text
[ ] Python package uses lowercase snake case
[ ] Python module uses lowercase snake case
[ ] Documentation uses canonical uppercase snake case
[ ] ADR uses four-digit ID and hyphenated title
[ ] Root file uses standard ecosystem name
[ ] Generated artifact uses owned canonical path
[ ] New environment variable uses GF_WORDBENCH_ prefix
[ ] New schema ID uses gf-wordbench. prefix
[ ] New contract/error/migration ID uses its registry family
```

---

# 186. Project naming checklist

```text
[ ] Project ID uses lowercase kebab case
[ ] Language code is stable
[ ] Module suffix agrees with project configuration
[ ] GF filename equals module name plus .gf
[ ] Scenario ID equals .gfs stem
[ ] Gold stem equals scenario ID
[ ] Project paths are relative
[ ] Required project docs use canonical filenames
[ ] Template and active project structures agree
[ ] No old language identity remains active
```

---

# 187. Run naming checklist

```text
[ ] Run directory uses run_<run-id>
[ ] Run ID is UTC and collision-safe
[ ] Required report names use exact case
[ ] Raw streams are separate
[ ] Per-subject names use owned safe keys
[ ] Artifact directories use canonical names
[ ] No absolute path appears in a basename
[ ] Manifest paths are run-relative
[ ] Temporary files are hidden and excluded
[ ] Failed outcome does not rename the run
```

---

# 188. Naming anti-patterns

Prohibited canonical names include:

```text
new_compiler.py
compiler2.py
compiler_final.py
old_summary.json
latest.pgf
parse_test_v2.gfs
parse_expected.txt
project_config_new.toml
README_FINAL.md
misc.py
utils2.py
output.txt
results.json
temp/
backup/
```

unless they exist only as clearly isolated legacy/test examples.

---

# 189. Balanced naming policy

GF Wordbench should not rename every imported project file to framework style.

Preserve authoritative external or upstream names when:

```text
GF module identity depends on them
version history matters
upstream synchronization matters
users already depend on them
```

Apply canonical framework naming to:

```text
new framework-owned files
new project-owned validation assets
generated artifacts
schemas
reports
tests
templates
```

Consistency must not destroy provenance.

---

# 190. Naming ownership registry

| Naming family | Owner |
|---|---|
| Python modules | component owner |
| Framework docs | documentation owner |
| Contract locks | contract owners |
| Project config/docs | project lifecycle and project owner |
| GF modules | active language project owner |
| Scenario IDs/files | scenario/project owner |
| Gold files | explicit gold updater/project reviewer |
| Run directory | run-path owner |
| Reports | report writers |
| Raw logs | stage/process evidence owner |
| Safe keys | path/artifact utility owner |
| Schema IDs | schema registry owner |
| Migration IDs | migration registry owner |
| Release package names | release owner |

A consumer must not independently invent a name owned elsewhere.

---

# 191. Required tests

Recommended files:

```text
tests/reference/test_file_naming.py
tests/utils/test_path_utils.py
tests/contracts/test_artifact_ownership.py
tests/projects/test_project_names.py
tests/scenarios/test_scenario_names.py
tests/migrations/test_name_migrations.py
```

Required cases:

```text
valid Python module name
invalid Python module case
valid project ID
invalid project ID
valid scenario ID
scenario/gold mismatch
GF module/file mismatch
Unicode source path
Windows reserved device
trailing dot
trailing space
path traversal
case-insensitive collision
safe-key determinism
safe-key collision resolution
safe-key length
run ID collision suffix
canonical report names
legacy state filename migration
legacy mode fixture naming
template/project document parity
atomic temporary names
source path with spaces
```

---

# 192. Naming contract tests

Contract tests should verify:

```text
report writer returns canonical path
manifest uses owned path
scenario runner uses registered ID
gold updater writes matching gold name
project loader validates canonical project paths
compiler/log writers use safe-key service
CLI and GUI do not reconstruct artifact filenames
current writers emit no legacy names
```

---

# 193. Definition of naming-compliant asset

An asset is naming-compliant when:

1. its name belongs to a documented family;
2. its owner is known;
3. its case and extension are canonical;
4. its path base is known;
5. it is portable for its supported platforms;
6. it does not collide case-insensitively;
7. it contains no unsafe segment;
8. it contains no hidden secret;
9. its consumers do not reconstruct it independently;
10. any public rename follows migration policy.

---

# 194. Final invariants

GF Wordbench naming must preserve:

1. `GF_Wordbench` for the repository identity.
2. `gf-wordbench` for package and CLI identity.
3. lowercase snake case for Python modules.
4. uppercase snake case for normative documentation files.
5. exact GF module name plus `.gf` for GF sources.
6. lowercase kebab case for project and scenario IDs.
7. scenario ID equals `.gfs` stem.
8. gold stem equals scenario ID.
9. `/` for canonical persisted path separators.
10. project-relative paths for project-owned assets.
11. run-relative paths for run-owned artifacts.
12. explicit absolute paths only for environment-owned locations.
13. exact locked report filenames.
14. UTC collision-safe run IDs.
15. deterministic safe keys.
16. no case-only duplicates.
17. no Windows reserved names.
18. no `new`, `old`, `final`, `latest`, `_v2`, or date suffixes in active canonical names.
19. no silent public identifier sanitization.
20. versioned migration for public renames.
21. current writers emit no legacy names.
22. one owner per generated naming family.
23. source provenance is preserved.
24. naming does not substitute for structured status or metadata.

---

# 195. Final rule

> Name files by their stable responsibility and identity, not by their temporary development state.

A canonical name must remain understandable after the current implementation, developer, machine, and release have changed.

GF Wordbench names should make ownership and purpose obvious without encoding transient status, personal environment details, or speculative architecture.
