# GF Wordbench Project Template — Validation Inputs

**Document ID:** `GF-WB-TEMPLATE-VALIDATION-INPUTS-README`  
**Status:** Normative template guide  
**Template path:** `templates/project/validation/inputs/README.md`  
**Active-project destination:** `project/validation/inputs/README.md`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**Document version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This directory contains reviewed, version-controlled input data consumed by GF Wordbench project validation scenarios.

Typical inputs include:

```text
phrases to parse
abstract trees to linearize
lemmas and feature bundles for morphology checks
negative examples
bounded generation seeds
expected ambiguity ranges
lexical fixture identifiers
scenario-specific parameter tables
small structured registries
```

The files in this directory are project source assets.

They are not generated run artifacts.

The central rule is:

> Every canonical validation input must have a documented format, stable ownership, explicit consumers, bounded size, deterministic meaning, and retained review history.

---

## 2. Scope

This guide governs files stored under:

```text
project/validation/inputs/
```

It defines:

- when a scenario should use an external input file;
- permitted formats;
- encoding and newline policy;
- naming and path rules;
- record and line semantics;
- comments and blank lines;
- stable identifiers;
- ordering;
- duplicates;
- positive and negative cases;
- Unicode handling;
- scenario-to-input registration;
- validation and integrity checks;
- security boundaries;
- update and migration rules;
- template initialization.

It does not define:

- GF scenario command syntax;
- output marker syntax;
- gold-file format;
- output normalization;
- run-result schemas;
- local machine paths;
- generated scenario output.

Those are defined by the referenced documents at the end.

---

## 3. Template versus active project

The template directory is generic.

The initialized active directory is project-specific.

| Directory | Role | Allowed content |
|---|---|---|
| `templates/project/validation/inputs/` | Generic project source | This README, optional empty-directory marker, generic examples clearly marked as examples |
| `project/validation/inputs/` | Active project inputs | Reviewed language-specific input files and initialized README |

The template MUST NOT contain:

- active-language phrases;
- another project's trees;
- another project's lexical items;
- copied negative examples;
- local filesystem paths;
- run outputs;
- credentials;
- gold output disguised as input;
- generated temporary data.

---

## 4. When to use an external input file

Use an input file when scenario data is:

- long enough to obscure the `.gfs` script;
- shared by more than one scenario;
- maintained by a different owner;
- naturally tabular or record-based;
- expected to evolve independently of scenario commands;
- reviewed as a linguistic fixture;
- easier to diff one record per line;
- needed by project contract validation.

Keep a small literal inside a scenario when:

- it is one short smoke case;
- it defines the scenario's control flow;
- externalization would reduce clarity;
- it is not reused;
- it does not need a separate ownership contract.

Do not split every literal into a separate file mechanically.

---

## 5. Canonical directory rules

Canonical active path:

```text
project/validation/inputs/
```

Rules:

- all input paths are project-relative;
- canonical separators are `/`;
- files must remain inside the project root;
- `..` traversal is prohibited;
- absolute paths are prohibited;
- symlink escape is prohibited;
- filenames preserve case;
- scenario references must use the exact canonical path;
- generated runs must not write into this directory.

The scenario runner must treat these files as read-only.

---

## 6. Encoding and newlines

Canonical encoding:

```text
UTF-8 without BOM
```

Canonical newline:

```text
LF
```

Readers may accept CRLF for compatibility.

Canonical writers and reviewed updates emit LF.

Rules:

- decoding errors are configuration or input errors;
- silent replacement of invalid bytes is prohibited;
- Unicode distinctions meaningful to the language must be preserved;
- normalization must not alter the canonical source file silently;
- the selected Unicode-normalization policy must be documented when relevant.

Recommended project policy:

```text
NFC
```

A project may choose another form when the language or source contract requires it.

---

## 7. Recommended formats

Prefer simple formats that are easy to review.

| Extension | Use | Status |
|---|---|---|
| `.txt` | One logical record per line | Preferred |
| `.tsv` | Small deterministic tables | Preferred |
| `.json` | Structured nested records requiring explicit schema | Allowed |
| `.toml` | Human-edited structured scenario configuration | Allowed |
| `.trees` | One GF abstract tree per record | Allowed project convention |
| `.phrases` | One phrase record per line | Allowed project convention |
| `.csv` | Only when quoting and delimiter rules are defined | Conditional |
| `.yaml` / `.yml` | Not canonical unless an approved parser dependency exists | Discouraged |
| binary formats | Only through an explicit contract | Prohibited by default |

Use Python standard-library-readable formats when possible.

Do not add a parser dependency only for convenience.

---

## 8. Plain-text record format

The default format is UTF-8 text with one logical record per line.

### 8.1 Blank lines

By default:

```text
blank lines are ignored
```

A format that assigns meaning to blank lines must document that meaning explicitly.

### 8.2 Comments

Preferred full-line comment marker:

```text
#
```

Example:

```text
# Representative positive parse cases.
```

Rules:

- comments occupy a whole logical line;
- inline comments are prohibited by default;
- a literal leading `#` requires an escape or a format that supports quoting;
- comments are not scenario data;
- comment wording may change without changing input semantics.

### 8.3 Whitespace

Default policy:

- remove the line terminator;
- preserve meaningful internal whitespace;
- reject or normalize trailing whitespace according to the file contract;
- do not collapse repeated spaces when linguistically meaningful;
- do not trim a phrase silently if leading or trailing whitespace is part of the tested input.

Every file registry entry must state its whitespace policy.

---

## 9. Tab-separated format

Use UTF-8 TSV for records with several stable fields.

Example generic header:

```text
case_id	input	expected_kind	notes
```

Rules:

- the delimiter is one U+0009 tab;
- the first row is a header unless explicitly documented otherwise;
- column names are stable identifiers;
- every required column must be present exactly once;
- extra columns require a compatible format revision;
- field order is stable for canonical writing;
- rows must have the declared number of fields;
- tabs inside fields require a different format;
- line meaning must be documented.

Do not align TSV using spaces.

---

## 10. JSON format

Use JSON only when nested structure is genuinely necessary.

Canonical root should be:

```text
object
```

or:

```text
array of typed records
```

Every JSON input requires:

```text
schema_id
schema_version
```

Conceptual example:

```json
{
  "schema_id": "gf-wordbench.project-input",
  "schema_version": "1.0",
  "input_id": "<INPUT_ID>",
  "records": []
}
```

A project-specific JSON schema ID must be documented before use.

Unknown required fields must produce a clear error.

Do not use unrestricted dictionaries with undocumented keys.

---

## 11. TOML format

TOML may be used for small human-maintained configuration-like fixtures.

Appropriate examples:

```text
bounded generation limits
scenario-specific category lists
named test groups
feature-selection tables
```

TOML inputs must:

- identify their format version;
- use project-relative paths;
- avoid machine-specific values;
- reject unknown required fields;
- preserve deterministic array order;
- avoid secrets.

`project.toml` remains the owner of project identity and scenario policy.

Input TOML must not redefine those facts.

---

## 12. File naming

Recommended filename pattern:

```text
<scenario-id>_<purpose>.<extension>
```

Examples as patterns:

```text
parse_positive.phrases
parse_negative.phrases
linearize_trees.trees
morphology_nouns.tsv
morphology_verbs.tsv
generation_categories.txt
```

Rules:

- use lowercase ASCII for filenames unless the project documents another policy;
- use `_` or `-` consistently;
- include the scenario ID when ownership is scenario-specific;
- avoid spaces;
- avoid locale-dependent names;
- avoid version numbers in filenames when the format contains a version;
- avoid `final`, `new`, `old`, `copy`, or dates as semantic identity;
- do not reuse a retired filename for different content.

Shared inputs may use a capability prefix instead of one scenario ID.

---

## 13. Input identity

Every canonical input file must have a stable logical identity.

Recommended ID:

```text
input:<project-id>:<input-name>
```

Example shape:

```text
input:<PROJECT_ID>:parse-positive
```

The ID may be stored:

- in a registry document;
- in a structured file;
- in scenario metadata;
- in a project contract.

Do not derive semantic identity only from absolute path.

A rename requires scenario and contract review.

---

## 14. Input registry

Complete this table in the active project.

| Input ID | File | Format | Owner | Consumers | Stability | Required |
|---|---|---|---|---|---|---:|
| `<INPUT_ID>` | `<RELATIVE_PATH>` | `<FORMAT>` | `<OWNER>` | `<SCENARIO_IDS>` | `<stable|experimental|deprecated>` | Yes/No |

Each entry must identify:

- one owner;
- every direct scenario consumer;
- format and version;
- required or optional status;
- ordering policy;
- duplicate policy;
- update review requirements.

An unregistered input file is not release evidence unless explicitly invoked and recorded.

---

## 15. Scenario-to-input contract

For each scenario using external inputs, register:

| Scenario ID | Input file | Purpose | Record selector | Failure behavior |
|---|---|---|---|---|
| `<SCENARIO_ID>` | `<RELATIVE_PATH>` | `<PURPOSE>` | `<ALL_OR_FILTER>` | `<FAILURE>` |

Locked invariants:

- the scenario references the documented file;
- the file exists before execution;
- encoding is validated;
- record meaning is documented;
- scenario and input versions are compatible;
- required input failure is not converted to `SKIPPED`;
- temporary generated input does not replace reviewed canonical input in release mode;
- removing or reordering records triggers gold-impact review.

---

## 16. Ownership

The project maintainers own canonical input files.

A specific input may have a more focused owner:

```text
morphology maintainer
syntax maintainer
lexicon maintainer
scenario maintainer
release maintainer
```

Ownership includes:

- defining record meaning;
- reviewing edits;
- maintaining consumers;
- preserving stable IDs;
- updating validation documentation;
- assessing gold impact;
- maintaining migration behavior.

The scenario runner is a consumer.

It does not own project input content.

---

## 17. Ordering

Input order must be deliberate.

Choose one policy per file:

```text
semantic order
dependency order
difficulty order
stable case-ID order
alphabetical order
order is not meaningful
```

When order is not meaningful, canonical writers should still sort deterministically.

When order is meaningful:

- the reason must be documented;
- consumers must preserve it;
- reordering is a semantic change;
- gold impact must be reviewed.

Never rely on filesystem enumeration order.

---

## 18. Stable case identifiers

Every non-trivial test record should have a stable case ID.

Recommended patterns:

```text
PARSE-POS-001
PARSE-NEG-001
LIN-001
MORPH-N-001
MORPH-V-001
GEN-001
```

Rules:

- IDs are unique within the project or documented namespace;
- IDs are not reused after retirement;
- renumbering for visual neatness is prohibited;
- IDs appear in output when practical;
- gold output should preserve IDs;
- issue and decision records may reference IDs.

A changed phrase with unchanged intended contract may retain its ID.

A different test purpose requires a new ID.

---

## 19. Positive cases

A positive case asserts that an operation should succeed.

Examples:

```text
a phrase should parse
a tree should linearize
a lemma should produce a form
a category should generate at least one bounded result
```

Every positive record should define:

- case ID;
- input;
- intended operation;
- expected success criterion;
- expected output or assertion strategy;
- allowed ambiguity or variants;
- owner.

Do not assume “non-empty output” is sufficient when a stronger criterion is required.

---

## 20. Negative cases

A negative case asserts that a specific outcome should not occur.

Examples:

```text
a phrase should not parse
an invalid constructor input should be rejected
a prohibited form should not appear
an unsupported category should remain unavailable
```

Every negative record must state:

- why it is invalid or prohibited;
- expected failure type;
- whether zero results or a diagnostic is expected;
- whether the case is linguistically invalid or merely unsupported;
- whether future support would intentionally retire the case.

Do not mix negative and positive records without a field that distinguishes them.

---

## 21. Boundary cases

Boundary cases should cover:

```text
empty input where applicable
single-character input
long but bounded input
Unicode combining characters
punctuation
multiword expressions
maximum configured generation depth
ambiguous phrases
irregular morphology
defective paradigms
rare feature bundles
```

Boundary inputs must remain bounded.

Stress testing that produces unbounded output belongs in a separate controlled test contract.

---

## 22. Parse input format

Recommended TSV:

```text
case_id	phrase	expectation	min_parses	max_parses	expected_tree_id	notes
```

Possible `expectation` values:

```text
parse
no_parse
error
```

Rules:

- `min_parses` and `max_parses` are non-negative integers or documented empty values;
- `max_parses` must be finite for automated release checks;
- `expected_tree_id` references a documented tree or may be empty;
- phrase text is preserved exactly according to whitespace policy;
- ambiguity expectations are explicit;
- a negative phrase is not represented by an undocumented comment.

---

## 23. Linearization input format

Recommended TSV:

```text
case_id	tree	expected_variant_policy	notes
```

or one tree per line with a stable ID separator.

Rules:

- tree syntax must be valid for the configured grammar;
- case IDs must survive into normalized output;
- expected variants must be documented;
- tree ordering is stable;
- tree input must not contain shell commands;
- an invalid tree used as a negative case must be explicitly marked.

Expected strings normally belong in gold output, not duplicated in the input file.

---

## 24. Morphology input format

Recommended TSV:

```text
case_id	lemma	constructor	features	expectation	notes
```

Rules:

- `features` uses one documented serialization;
- feature names match project morphology contracts;
- constructor names are stable public identifiers;
- irregular and fallback cases are marked;
- unsupported and defective cases are distinguishable;
- expected forms normally belong in gold output unless a structured assertion file is deliberately used.

Example generic feature serialization:

```text
Number=Singular;Case=Nominative
```

The active project must replace feature names and values with its real contract.

---

## 25. Generation input format

Recommended TSV:

```text
case_id	category	max_depth	max_results	seed_or_projection	notes
```

Rules:

- every limit is finite;
- default limits are explicit;
- random behavior is prohibited for exact gold unless a stable seed and deterministic tool behavior are proven;
- output may use a deterministic projection;
- generated result count limits must protect disk and report size.

Unbounded generation is prohibited in normal validation.

---

## 26. Lexical fixture format

Recommended TSV:

```text
entry_id	category	lemma	constructor	arguments	status	notes
```

Use lexical fixtures only when they are not the authoritative project lexicon.

Rules:

- test fixtures must not silently become production lexical data;
- constructor arguments use documented encoding;
- temporary entries are marked;
- fixture IDs are stable;
- culturally or linguistically sensitive content is reviewed;
- personal data is prohibited.

---

## 27. Metadata header

Plain-text files may begin with a comment header.

Recommended fields:

```text
# input_id: <INPUT_ID>
# format: <FORMAT_ID>
# format_version: 1.0
# owner: <OWNER>
# consumers: <SCENARIO_IDS>
# ordering: <ORDER_POLICY>
# unicode_normalization: NFC
```

Header keys are optional unless the project validation specification makes them required.

When present:

- keys are lowercase ASCII;
- values are single-line;
- duplicate keys are invalid;
- unknown required keys are invalid;
- comment headers end before the first data record.

---

## 28. Format versioning

Every structured or shared input format should have:

```text
MAJOR.MINOR
```

Minor increment:

- optional compatible column;
- optional metadata field;
- additional record kind with safe default behavior.

Major increment:

- renamed field;
- changed delimiter;
- changed field meaning;
- changed case-ID semantics;
- changed ordering meaning;
- formerly optional field becomes required;
- whitespace policy changes;
- Unicode-normalization policy changes existing records.

The input format version is independent of:

```text
GF Wordbench version
project version
scenario version
gold format version
normalization version
```

---

## 29. Compatibility

A scenario must declare which input format versions it supports.

Canonical behavior:

- current supported major is accepted;
- newer unknown major is rejected;
- newer minor may be accepted only when optional-field rules are defined;
- older supported major may be migrated through an explicit adapter;
- unversioned legacy input is rejected or migrated through a documented rule.

A scenario must not guess column meaning from the number of delimiters.

---

## 30. Duplicates

Choose a duplicate policy per input file.

Possible policies:

```text
reject duplicate case IDs
reject duplicate complete records
allow duplicate input with different expectations
allow duplicates only through explicit variant IDs
```

Canonical default:

```text
duplicate case IDs are errors
```

Duplicate phrases may be valid only when they test different entrypoints, feature settings, or expectations.

The distinction must be explicit.

---

## 31. Empty files

An empty canonical input file is valid only when:

- the file is optional;
- the scenario contract permits no records;
- the empty state has explicit meaning;
- release policy does not require coverage from it.

A required input file with zero usable records must normally produce:

```text
FAIL
```

when the file is valid but the coverage criterion is unmet, or:

```text
ERROR
```

when the file cannot be interpreted.

It must not become an automatic pass.

---

## 32. Missing files

A missing required input file is a configuration error.

Canonical result:

```text
validation_status = ERROR
error_kind = CONFIG or IO
```

according to the owner of the failure.

A missing optional file may produce `SKIPPED` only when:

- optionality is explicit;
- the scenario can run meaningfully without it;
- the skip reason is retained;
- release policy permits the skip.

---

## 33. Input validation lifecycle

Canonical lifecycle:

```text
resolve project-relative path
    → verify containment
    → verify existence and file type
    → read raw bytes
    → decode declared encoding
    → verify newline and Unicode policy
    → parse format
    → validate schema/header
    → validate record fields
    → validate stable IDs
    → validate limits
    → expose immutable records to scenario
```

Validation must occur before the input is used to construct GF commands or scenario data.

---

## 34. Raw preservation

Canonical source input files remain unchanged during validation.

A run may record:

```text
input path
input size
input SHA-256
format ID and version
record count
selected record IDs
```

A run should not duplicate every canonical input unless release evidence policy requires a snapshot.

When copied into run evidence, the manifest must identify the copy as:

```text
input snapshot
```

and preserve the source hash.

---

## 35. Generated temporary inputs

A scenario may generate temporary data only when the scenario contract permits it.

Generated temporary inputs:

- belong under the run directory;
- are not written into `project/validation/inputs/`;
- have deterministic generation when used for comparison;
- are recorded in the manifest;
- cannot replace reviewed canonical release input silently;
- are deleted or retained according to run policy;
- are treated as generated artifacts, not source.

Release validation must prefer canonical reviewed inputs for release-gating cases.

---

## 36. Scenario command safety

Input records are data, not shell fragments.

Prohibited:

```text
building shell command strings from input text
executing operating-system commands from input fields
allowing input records to select arbitrary executables
allowing path traversal
allowing unrestricted GF shell escape commands
```

When an input contains a GF abstract tree or phrase, it must be passed through the documented GF scenario mechanism.

The framework must not reinterpret it as operating-system command text.

---

## 37. Secrets and personal data

Validation inputs MUST NOT contain:

- passwords;
- tokens;
- private keys;
- credentials;
- private environment values;
- personal addresses;
- non-public personal correspondence;
- production customer data;
- confidential corpora without an approved data contract.

Use synthetic or properly licensed examples.

When a linguistic corpus has license restrictions, record:

- license;
- source;
- permitted redistribution;
- attribution;
- transformation policy;
- repository inclusion decision.

---

## 38. Licensing and provenance

Every externally sourced input collection must have provenance.

Complete:

| Input ID | Source | License | Transformation | Reviewer |
|---|---|---|---|---|
| `<INPUT_ID>` | `<SOURCE>` | `<LICENSE>` | `<TRANSFORMATION>` | `<REVIEWER>` |

Inputs created by project maintainers should still identify the responsible owner.

Do not copy examples from external resources without confirming reuse rights.

---

## 39. Determinism

Given the same:

```text
input file bytes
scenario script
project configuration
GF version
RGL revision
normalization version
```

the selected input records and their interpretation should be deterministic.

Determinism requires:

- explicit encoding;
- explicit delimiter;
- explicit comment rules;
- stable ordering;
- finite limits;
- no current-time filters;
- no locale-dependent sort;
- no uncontrolled randomness;
- no filesystem enumeration dependency;
- no hidden environment substitution.

---

## 40. Relationship to gold

Inputs define what is exercised.

Gold defines accepted normalized output.

They are separate source artifacts.

Rules:

- input files do not contain generated gold unless the format deliberately combines request and expected assertion;
- changing input order may change gold order;
- adding a case normally requires gold review;
- removing a case normally requires gold review;
- changing case IDs requires gold review;
- normal validation changes neither input nor gold;
- a failing gold comparison must not be fixed by deleting the input case without review.

---

## 41. Input changes

Every input change must be classified.

### 41.1 Comment-only change

Compatible when:

- record bytes and parsing are unchanged;
- no metadata meaning changes.

### 41.2 Compatible addition

Examples:

- new positive case;
- new negative case;
- optional metadata;
- new stable case ID.

Required review:

```text
scenario capacity
gold output
coverage matrix
validation specification
```

### 41.3 Behavior change

Examples:

- change phrase text;
- change tree;
- change feature bundle;
- change ambiguity limit;
- reorder meaningful records;
- retire a case.

Required review:

```text
contract intent
gold impact
project version impact
decision or issue record when significant
```

### 41.4 Breaking format change

Examples:

- rename column;
- change delimiter;
- change ID meaning;
- change comment behavior;
- change Unicode normalization;
- make an optional field required.

Requires:

```text
format major increment
consumer update
migration rule
fixtures
contract tests
documentation
release note
```

---

## 42. Deleting an input

Before deletion:

1. identify every consumer;
2. identify gold affected by its records;
3. determine whether coverage is removed or moved;
4. update scenarios;
5. update the input registry;
6. update `VALIDATION_SPEC.md`;
7. update `TEST_COVERAGE_MATRIX.md`;
8. update project contracts;
9. record retirement where the ID is externally referenced;
10. rerun required validation.

Do not leave broken scenario references.

---

## 43. Renaming an input

A rename is a contract change because scenarios reference paths.

Required updates:

```text
scenario files
input registry
interfile contract lock
validation specification
coverage matrix
documentation links
fixtures
tests
gold review
```

Preserve the logical input ID when only the path changes.

Use a new ID when the purpose changes.

---

## 44. Scenario result requirements

A scenario using input files should retain enough evidence to identify:

```text
scenario ID
input IDs
input paths
input hashes
input format versions
record count
selected case IDs
skipped or filtered case IDs when relevant
primary input error
```

These fields may live in scenario metadata or an associated artifact.

They must not be reconstructed by parsing human reports.

---

## 45. Error classification

Typical mappings:

| Condition | Status | Error kind | Diagnostic class |
|---|---|---|---|
| Valid required input, assertion fails | `FAIL` | `OTHER` | `direct` |
| Missing required input | `ERROR` | `CONFIG` or `IO` | `direct` to scenario configuration or `ambiguous` by ownership |
| Invalid encoding | `ERROR` | `IO` | `direct` when current input owns defect |
| Unsupported format version | `ERROR` | `CONFIG` | `direct` |
| Failed prerequisite entrypoint | `FAIL`/`ERROR` | inherited | `downstream` |
| Optional input deliberately absent | `SKIPPED` or scenario continues | `OK`/policy-specific | `skipped` or scenario's final class |
| Parser implementation crashes | `ERROR` | `INTERNAL` | `ambiguous` |

The input loader does not assign causal relationships beyond its owned evidence.

---

## 46. Recommended project checker

Preferred command:

```text
gf-wordbench project inputs check
```

Strict form:

```text
gf-wordbench project inputs check --strict
```

Recommended checks:

```text
registry completeness
path containment
file existence
regular-file type
UTF-8 decoding
BOM policy
newline policy
format version
header validity
required columns
duplicate IDs
record counts
finite limits
scenario consumers
unregistered files
unused files
gold-impact mapping
license metadata when required
active-language identifier consistency
```

Until the command exists, equivalent checks must be covered by tests or release review.

---

## 47. Required tests

Recommended contract tests:

```text
tests/contracts/test_project_input_contracts.py
tests/contracts/test_scenario_input_contracts.py
```

Minimum cases:

```text
valid UTF-8 text input
CRLF compatibility
BOM rejection or migration
invalid UTF-8
missing required file
optional missing file
outside-root path
symlink escape
unknown format version
missing required column
duplicate case ID
blank-line handling
comment handling
literal leading comment marker
trailing whitespace
Unicode normalization
TSV field-count mismatch
empty required file
finite generation limits
stable ordering
scenario-to-input registry match
unregistered input detection
normal run preserves input bytes
input hash recorded
```

---

## 48. Initialization procedure

When creating an active project:

1. copy this README to `project/validation/inputs/README.md`;
2. replace project placeholders;
3. choose the input formats;
4. document encoding and whitespace policy;
5. create the input registry;
6. add canonical input files;
7. assign stable input and case IDs;
8. register scenario consumers;
9. document format versions;
10. define duplicate and ordering rules;
11. define license and provenance where required;
12. update project contracts;
13. update validation specification;
14. update coverage matrix;
15. add tests;
16. run strict input validation;
17. execute every consuming scenario;
18. review resulting gold changes;
19. retain baseline evidence.

---

## 49. Initialization checklist

```text
[ ] Project owner replaced
[ ] Language placeholders replaced
[ ] Encoding policy selected
[ ] Unicode normalization selected
[ ] Filename convention selected
[ ] Approved formats selected
[ ] Input registry completed
[ ] Every input has one owner
[ ] Every input has consumers
[ ] Every input has a format version
[ ] Every input has ordering policy
[ ] Every input has duplicate policy
[ ] Required inputs identified
[ ] Optional inputs identified
[ ] Stable case IDs assigned
[ ] Positive cases documented
[ ] Negative cases documented
[ ] Boundary cases documented
[ ] Finite generation limits defined
[ ] License and provenance recorded
[ ] Scenario references updated
[ ] Project contract lock updated
[ ] Validation specification updated
[ ] Coverage matrix updated
[ ] Gold impact reviewed
[ ] Contract tests added
[ ] Strict input check passes
[ ] Consuming scenarios pass or documented gaps are ledgered
[ ] No unresolved required placeholder remains
[ ] No active input contains secrets or private data
[ ] Baseline evidence retained
```

---

## 50. Template validation

The framework template tests should verify:

```text
this README exists
only approved placeholders appear
no active-language phrase appears
no active language code appears
no local absolute path appears
no canonical project input data appears
fenced blocks are balanced
cross-references use canonical paths
the initialized copy rejects unresolved placeholders
```

The generic input directory does not need executable language data.

It must remain safe and complete as a template.

---

## 51. Common mistakes

### 51.1 Putting expected output in every input file

This duplicates gold and creates two expectation owners.

Use gold output unless record-level assertions require a structured expected field.

### 51.2 Treating file order as accidental

If output follows input order, reordering can invalidate gold.

Declare order explicitly.

### 51.3 Using a phrase as its own identifier

Phrase text may change.

Use a stable case ID.

### 51.4 Hiding unsupported cases by deletion

Removing a failing case reduces coverage.

Record the decision and review release impact.

### 51.5 Using generated files as canonical inputs

Run-generated files are artifacts.

They cannot replace reviewed source inputs silently.

### 51.6 Storing absolute paths

Absolute paths destroy project portability.

Use project-relative paths.

### 51.7 Using random generation without a bound

Unbounded or uncontrolled random generation is unsuitable for deterministic validation.

### 51.8 Silent Unicode normalization

Normalization may change linguistic content.

Document and test the policy.

### 51.9 Accepting invalid UTF-8 with replacement characters

This hides source corruption.

Fail explicitly.

### 51.10 Letting scenario scripts parse the same format differently

One input format must have one documented parser contract.

---

## 52. Anti-drift indicators

Input drift exists when:

- a scenario references an unregistered file;
- an input file has no owner;
- line meaning is undocumented;
- a required file is generated temporarily instead of versioned;
- encoding changes silently;
- case IDs are reused;
- meaningful order changes without gold review;
- a format changes without version update;
- a consumer guesses missing fields;
- duplicate IDs are silently accepted;
- comments are interpreted as data by one consumer;
- one scenario trims phrases while another preserves them;
- Unicode distinctions disappear;
- input data contains machine paths;
- canonical inputs contain secrets or private data;
- generated runs modify source inputs;
- an input change is used to make a failing scenario pass without reviewing the criterion;
- another language's fixture data remains after project cloning;
- an unused input is presented as release coverage.

Any drift indicator requires contract review.

---

## 53. Cross-references

| Topic | Document |
|---|---|
| Project template | `templates/project/README.md` |
| Project schema | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Project contracts | `templates/project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Scenario authoring | `docs/scenarios/AUTHORING_SCENARIOS.md` |
| Gold format | `docs/scenarios/GOLD_FILE_FORMAT.md` |
| Gold updates | `docs/scenarios/UPDATING_GOLD_FILES.md` |
| Output normalization | `docs/scenarios/OUTPUT_NORMALIZATION.md` |
| Scenario validation | `docs/validation/SCENARIO_VALIDATION.md` |
| Project validation spec | `templates/project/docs/VALIDATION_SPEC.md` |
| Coverage matrix | `templates/project/docs/TEST_COVERAGE_MATRIX.md` |
| Status ledger | `templates/project/docs/STATUS_LEDGER.md` |
| Known issues | `templates/project/docs/KNOWN_ISSUES.md` |
| Active input directory | `project/validation/inputs/` |

---

## 54. Final rule

> Validation inputs are reviewed source contracts, not disposable test strings.

Each input must be identifiable, readable, bounded, deterministic, licensed when necessary, and connected to an explicit scenario purpose.

Normal validation may read inputs and record their hashes.

It must never rewrite the canonical source files.
