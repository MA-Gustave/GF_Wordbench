# GF Wordbench Project — Validation Inputs

**Status:** Active project input contract  
**Scope:** `project/validation/inputs/`  
**Applies to:** Native `.gfs` scenarios, scenario registration, project validation, checkpoint evidence, release evidence, input linting, migrations, and project maintenance  
**Project identity:** Defined by `project/project.toml`  
**Validation authority:** `project/docs/VALIDATION_SPEC.md`  
**Project contract lock:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Scenario authoring guide:** `docs/scenarios/WRITING_GFS_SCENARIOS.md`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This directory contains version-controlled data consumed by project validation scenarios.

Typical validation inputs include:

```text
sentences to parse
words to analyze morphologically
abstract trees to linearize
accepted ambiguity cases
expected rejection cases
round-trip examples
regression reproductions
small reviewed corpora
operation names or query values
```

These files are project source assets.

They are not generated run output.

They are not gold files.

They are not GF shell scripts.

The governing relationship is:

```text
validation requirement
→ registered scenario
→ registered input file
→ native GF command
→ captured output
→ assertion or gold comparison
```

---

## 2. Core rule

> Every input file must have one declared purpose, one documented format, and at least one registered scenario consumer.

An input file is valid only when:

```text
it is stored under an approved project input root
and its path is registered
and its encoding is valid
and its format is documented
and its ordering semantics are known
and its blank-line semantics are known
and its comment policy is known
and its consumers are known
and its use is bounded
and required validation passes
```

An unregistered file in this directory is not automatically part of project validation.

---

## 3. What belongs here

Place a file in this directory when its primary purpose is to provide reviewed data to one or more validation scenarios.

Appropriate examples:

```text
parse-positive.txt
parse-negative.txt
morphology-words.txt
linearization-trees.txt
roundtrip-sentences.txt
ambiguity-cases.tsv
regression-cases.json
```

The names above are illustrative.

The active inventory is defined by project configuration and project validation documentation.

---

## 4. What does not belong here

Do not store:

```text
.gfs scenario scripts
.gold expected-output files
generated stdout or stderr
normalized scenario output
temporary debugging data
GF source modules
compiled .gfo files
release .pgf files
run summaries
application state
local machine configuration
secrets
large unreviewed corpora
operating-system scripts
```

Canonical neighboring roots:

```text
project/validation/scenarios/
project/validation/gold/
```

Generated evidence belongs under the configured run output root.

---

## 5. Authoritative inventory

The current input inventory must be derived from:

```text
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/INTERFILE_CONTRACT_LOCK.md
registered scenario metadata
```

This README defines the common input contract.

It intentionally does not duplicate volatile project-specific filenames.

A file may exist physically without being active.

A file becomes active only when it is registered and consumed by a current scenario or manual criterion.

---

## 6. Ownership

The active project owns every validation input.

Input owners are responsible for:

- linguistic correctness;
- file format;
- ordering;
- duplicate policy;
- comment policy;
- blank-line policy;
- consumer registration;
- scenario compatibility;
- release impact;
- version-control history.

GF Wordbench owns:

- path validation;
- bounded reading;
- encoding validation;
- registration checks;
- evidence capture;
- reporting;
- contract linting.

GF owns interpretation only after the data reaches a GF command.

---

## 7. Input data is not command text

Validation inputs must be treated as data.

They must not be concatenated into GF shell commands without a safe, documented transformation.

Unsafe conceptual behavior:

```text
read arbitrary line
→ append directly to GF command source
→ execute
```

Preferred behavior:

```text
registered input
→ validated reader
→ native GF data pipeline or safely quoted value
→ captured GF result
```

Input strings must not be interpreted as:

- operating-system commands;
- shell redirection;
- GF Wordbench CLI options;
- project configuration;
- scenario metadata;
- additional `.gfs` commands.

---

## 8. Canonical directory organization

Small projects may keep files directly under:

```text
project/validation/inputs/
```

Larger projects should group inputs by scenario or validation domain.

Recommended forms:

```text
project/validation/inputs/
├── parse-basic/
│   ├── positive.txt
│   ├── rejected.txt
│   └── ambiguous.tsv
├── morphology-basic/
│   ├── nouns.txt
│   └── verbs.txt
└── regressions/
    └── issue-cases.json
```

Alternative domain grouping:

```text
project/validation/inputs/
├── parsing/
├── linearization/
├── morphology/
├── roundtrip/
└── regressions/
```

Use one organization consistently.

Do not create both scenario-based and domain-based duplicates without a documented reason.

---

## 9. Naming rules

Recommended filename form:

```text
lowercase-kebab-case.extension
```

Examples:

```text
positive-sentences.txt
noun-forms.txt
expected-rejections.txt
ambiguity-cases.tsv
regression-cases.json
```

Recommended directory form:

```text
lowercase-kebab-case/
```

Avoid:

```text
Input Final 2.txt
test.txt
data-new.txt
misc.txt
temp.txt
sentences (copy).txt
```

A name should describe the data role.

It should not depend on a temporary development milestone.

---

## 10. Stable path identity

A registered input path is a project contract.

Renaming or moving it requires review of:

```text
scenario registry
.gfs consumers
project configuration
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
INTERFILE_CONTRACT_LOCK.md
project documentation
release evidence references
```

A path change must not leave an obsolete duplicate that remains accidentally consumed.

---

## 11. Project-relative paths

Persisted input paths must be project-relative.

Preferred:

```text
project/validation/inputs/parse-basic/positive.txt
```

Prohibited in portable project configuration:

```text
C:\Users\developer\Desktop\positive.txt
/home/developer/positive.txt
```

Canonical persisted separators use:

```text
/
```

The runtime may resolve native platform separators internally.

---

## 12. Path containment

Input paths must remain inside approved project input roots.

Reject:

```text
../secrets.txt
../../outside-project/data.txt
absolute user-profile paths
network paths not explicitly approved
symlink or junction escapes
```

A registered file must resolve to the intended project asset after normalization.

Unknown links are not followed automatically.

---

## 13. Encoding

Default encoding:

```text
UTF-8 without BOM
```

Canonical newline:

```text
LF
```

Every text file must end with a final newline unless its format explicitly prohibits one.

Readers may accept CRLF and normalize line endings for processing.

They must not silently discard undecodable bytes.

An encoding error is an input validation error.

---

## 14. Unicode policy

Unicode linguistic content may appear directly.

GF Wordbench must not apply an undocumented Unicode normalization transform.

Each input contract must state one of:

```text
preserve exact code points
require NFC
require another documented normalization
```

Recommended default:

```text
require NFC for ordinary linguistic text
```

Exceptions are appropriate when testing:

- decomposed characters;
- combining-mark behavior;
- normalization defects;
- orthographic distinctions represented by code-point sequence.

Such exceptions must be isolated and documented.

---

## 15. Byte-order mark

A UTF-8 BOM should not be present.

A BOM may:

- become part of the first input item;
- alter a parse string;
- change a tree;
- create an invisible regression.

The input linter should report a BOM.

Automatic removal may be offered only through an explicit formatting operation.

---

## 16. One file, one data contract

Each file should use one format and one interpretation.

Good:

```text
one sentence per line
one word per line
one GF tree per line
one TSV record per line
one JSON array under a versioned schema
```

Poor:

```text
sentences, commands, expected outputs and notes mixed together
```

When two datasets have different semantics, store them separately.

---

## 17. Default line-oriented format

The preferred simple format is:

```text
UTF-8 text
one logical item per line
stable file order
no implicit comments
no implicit trimming of semantic content
```

This format is appropriate for:

- sentences;
- words;
- abstract trees;
- identifiers;
- expected rejected inputs.

The consuming scenario or reader must define how each line is passed to GF.

---

## 18. Line numbering

Line numbers are evidence identifiers.

Validation failures should report:

```text
input path
1-based line number
item identity or safe excerpt
```

Inserting or removing earlier lines may change evidence line numbers.

When stable case identity is important, use an explicit ID format such as TSV or JSON.

---

## 19. Blank lines

Blank-line semantics must be explicit.

Allowed policies:

```text
blank lines prohibited
blank lines ignored
blank lines represent empty input
blank lines separate records
```

Default policy:

```text
blank lines prohibited
```

A blank parse string or morphology token must be tested in a dedicated format where emptiness is intentional and machine-distinguishable.

Do not rely on accidental empty lines at end of file.

---

## 20. Whitespace

Leading and trailing whitespace may be linguistically meaningful.

A reader must not trim it silently unless the input contract declares trimming.

The file contract should state:

```text
preserve
trim ASCII surrounding spaces
normalize documented separators
```

Default for ordinary sentence and word lists:

```text
reject accidental leading or trailing whitespace
```

Intentional whitespace tests should use a structured format that makes the expected characters explicit.

---

## 21. Tabs

Tabs are prohibited in simple one-item-per-line files unless the file format explicitly uses TSV.

A linter should report tabs in `.txt` inputs.

For TSV:

- tabs separate fields;
- field count is fixed;
- tabs inside values require a documented escaping or quoting rule;
- the first row policy is explicit.

---

## 22. Comments

There is no implicit comment syntax in ordinary input files.

A line beginning with:

```text
#
--
//
```

is data unless the file contract says otherwise.

Recommended default:

```text
comments prohibited in executable input files
```

Use nearby Markdown documentation or a structured field for notes.

When comments are allowed:

- the marker is documented;
- escaping is documented;
- the reader implements it;
- the scenario does not receive comment lines;
- tests cover the behavior.

---

## 23. Duplicate items

Duplicate semantics must be explicit.

Allowed policies:

```text
duplicates prohibited
duplicates preserved as repeated test cases
duplicates merged by stable case ID
```

Default:

```text
exact duplicate logical items prohibited
```

A deliberate repeated case should have distinct case IDs and a documented reason.

Do not silently deduplicate at runtime.

---

## 24. Ordering

Input order is stable and meaningful by default.

The runner or scenario must preserve registered order unless another deterministic order is documented.

Do not:

- rely on filesystem enumeration order;
- sort linguistically meaningful examples automatically;
- shuffle cases;
- use unordered sets for release input;
- merge files in nondeterministic order.

When order is declared nonsemantic, the comparison strategy must still be deterministic.

---

## 25. Case identity

Simple line files use:

```text
path + line number
```

as case identity.

Structured formats should use stable IDs.

Recommended case ID form:

```text
lowercase-kebab-case
```

Examples:

```text
basic-declarative-01
negative-polarity-02
irregular-noun-03
regression-issue-017
```

IDs must be unique within their declared scope.

Retired IDs should not be reused for unrelated cases.

---

# 26. Recommended input classes

The project may use the following classes.

## 26.1 Parse strings

One reviewed surface string per record.

Required metadata or scenario context:

```text
language
category
expected parse policy
ambiguity policy
positive or negative intent
```

## 26.2 Linearization trees

One valid GF abstract tree per record.

Required context:

```text
target language
expected output strategy
tree type or category
```

## 26.3 Round-trip strings

One reviewed input string per record.

Required context:

```text
parse language
category
linearization language
canonicalization policy
```

## 26.4 Morphology words

One word or token sequence per record.

Required context:

```text
analysis command
language
expected analysis policy
missing-word policy
```

## 26.5 Expected rejection cases

Inputs intended not to parse or not to satisfy a specified criterion.

Required context:

```text
rejection definition
maximum allowed result count
forbidden tree or pattern when relevant
```

## 26.6 Ambiguity cases

Inputs with an accepted bounded ambiguity contract.

Required context:

```text
minimum parse count
maximum parse count
required trees
forbidden trees
ordering policy
```

## 26.7 Regression cases

Inputs tied to a known issue, decision, or previously observed failure.

Required context:

```text
stable case ID
issue or decision ID
original failure
expected current behavior
```

---

# 27. Sentence-list format

Recommended extension:

```text
.txt
```

Contract:

```text
one sentence per line
no blank lines
no comments
stable order
UTF-8
NFC unless explicitly testing normalization
```

Example:

```text
This is a reviewed sentence.
This is another reviewed sentence.
```

The example is illustrative and not part of the active project inventory.

A sentence list must not include expected output on the same line unless a structured format is declared.

---

# 28. Word-list format

Recommended extension:

```text
.txt
```

Contract:

```text
one token or documented token sequence per line
no blank lines
no comments
stable order
duplicate policy explicit
```

Example:

```text
word-one
word-two
word-three
```

Hyphens in the example are data.

They do not imply a project orthography.

---

# 29. GF-tree-list format

Recommended extension:

```text
.trees.txt
```

Contract:

```text
one complete GF tree expression per line
no line continuation unless explicitly supported
no comments
stable order
tree category documented
```

Example:

```gf
UseCl (TTAnt TPres ASimul) PPos (PredVP (UsePron i_Pron) (UseV sleep_V))
```

The example is illustrative.

The active project must use constructors available through its configured grammar.

Tree syntax remains GF syntax.

GF Wordbench must not reinterpret it.

---

# 30. TSV case format

Use TSV when each case needs a stable ID and a small fixed set of fields.

Recommended extension:

```text
.tsv
```

Example schema:

```text
case_id	input	expectation
basic-01	reviewed input	accept
negative-01	reviewed invalid input	reject
```

Requirements:

- header presence is explicit;
- field order is fixed;
- required fields are documented;
- tabs delimit fields;
- line endings are canonical;
- quoting and escaping are documented;
- duplicate case IDs are prohibited.

Do not invent ad hoc columns without updating the file contract and consumers.

---

# 31. JSON case format

Use JSON only when nested or typed data is necessary.

Recommended extension:

```text
.json
```

A JSON input used for release should define:

```text
schema_id
schema_version
cases
```

Conceptual structure:

```json
{
  "schema_id": "project.validation-cases",
  "schema_version": "1.0",
  "cases": [
    {
      "id": "basic-01",
      "input": "reviewed input",
      "expectation": "accept"
    }
  ]
}
```

The schema ID above is an illustrative project-owned example.

A real project schema must have:

- an owner;
- version rules;
- validation;
- migration policy;
- tests.

Do not use JSON merely to wrap a simple line list.

---

# 32. CSV policy

CSV is discouraged for linguistic validation inputs because quoting, commas, newlines, and spreadsheet transformations can create ambiguity.

Use TSV or JSON instead.

CSV may be used only when:

- its dialect is fixed;
- encoding is UTF-8;
- newline handling is documented;
- quoting rules are tested;
- spreadsheet auto-conversion risks are controlled.

---

# 33. File size

Validation inputs must remain bounded.

The project should define limits for:

```text
maximum file size
maximum record count
maximum record length
maximum combined input size per scenario
```

Large corpora should not be inserted into release scenarios without a performance and retention policy.

A representative reviewed subset is normally preferable.

---

# 34. Record length

A very long record may cause:

- command parsing problems;
- excessive diagnostics;
- report bloat;
- output truncation;
- poor reviewability.

The linter should report records above the project threshold.

An exception must identify:

- why the long record is required;
- which scenario consumes it;
- timeout impact;
- output-size impact.

---

# 35. Bounded scenario use

An input file does not override scenario bounds.

The consuming scenario must still have:

```text
finite timeout
bounded output
bounded generation
deterministic order
output-size policy
```

A large input list must not be used to bypass command-level limits.

---

# 36. Registration

Every active input should be registered through the project scenario inventory or another documented project registry.

Registration should identify:

```text
input ID when used
project-relative path
format
encoding
consumer scenario IDs
purpose
required or optional status
ordering policy
blank-line policy
comment policy
duplicate policy
normalization policy
owner
```

The exact persisted representation belongs to the project schema.

---

# 37. Scenario-to-input relationship

A scenario may consume:

- no external input;
- one input file;
- several explicitly ordered input files.

The relationship must be visible in project metadata.

A scenario must not discover arbitrary files through a broad glob at runtime.

All release-relevant inputs must be registered and version-controlled.

---

# 38. Shared inputs

An input may be shared by several scenarios when the data has the same semantic meaning for each consumer.

Shared input requirements:

- one clear owner;
- all consumers registered;
- compatible format expectations;
- coordinated change review;
- no consumer-specific hidden interpretation.

When consumers require different semantics, create separate files.

---

# 39. Scenario-specific inputs

Scenario-specific data should normally live under:

```text
project/validation/inputs/<scenario-id>/
```

Benefits:

- clear ownership;
- easier cleanup review;
- easier migration;
- less accidental reuse;
- simpler scenario linting.

Do not rename a scenario-specific directory without updating the scenario registry.

---

# 40. Input-to-GF transfer

A scenario may transfer input to GF through documented native mechanisms such as a file-reading command and GF command pipeline.

The exact command must be tested for supported GF versions.

Requirements:

- input path is quoted where required;
- path is project-relative or safely resolved;
- command does not invoke an operating-system shell;
- input is treated as data;
- output is captured;
- case identity is retained or reconstructible;
- failure on one record is represented honestly.

---

# 41. Quoting and escaping

Input quoting rules belong to the transfer method.

A line containing:

```text
"
\
;
|
```

must not be assumed safe in every GF command context.

Before adding such input:

1. identify the native GF command receiving it;
2. define quoting or file-pipeline behavior;
3. test supported GF versions;
4. preserve raw evidence;
5. add regression coverage.

Do not create multiple independent escaping implementations.

---

# 42. Newline inside one logical item

A logical item spanning multiple lines is not supported by the default line-oriented format.

Use a structured format with explicit record boundaries.

Do not rely on:

- indentation;
- blank-line grouping;
- accidental continuation;
- editor word wrapping.

---

# 43. Expected output does not belong in ordinary input lists

A simple input file should normally contain only the stimulus.

Expected normalized output belongs in:

```text
project/validation/gold/
```

Expected semantic metadata may belong in TSV or JSON when the assertion engine consumes it explicitly.

Do not mix raw input and free-form human explanation in one executable file.

---

# 44. Positive and negative cases

Keep positive and negative data separate unless a structured field distinguishes them.

Preferred:

```text
parse-basic/positive.txt
parse-basic/rejected.txt
```

or:

```text
parse-basic/cases.tsv
```

with an explicit expectation field.

Avoid inferring negative cases from filename fragments inside scenario code.

Registration should define the case role.

---

# 45. Ambiguity

Ambiguity is a contract, not noise.

An ambiguity input must document:

```text
accepted minimum result count
accepted maximum result count
required tree set when applicable
forbidden tree set when applicable
ordering policy
normalization policy
```

A parser producing one parse where two are required is a failure.

A parser producing unbounded extra parses may also be a failure.

---

# 46. Expected rejection

A rejection case must define what rejection means.

Possible definitions:

```text
zero parses
no required tree
fatal diagnostic prohibited
bounded fallback output absent
specific assertion fails
```

Do not treat any stderr text as expected rejection unless the scenario contract explicitly defines it.

---

# 47. Regression inputs

A regression file or record must reference a stable project record.

Recommended references:

```text
known issue ID
status ledger ID
decision ID
external bug ID
previous run ID
```

Regression data should preserve the smallest case that reproduces the defect.

When the defect is fixed:

- keep the input when it provides continuing coverage;
- update the expected behavior;
- mark the linked issue resolved;
- preserve resolution evidence.

---

# 48. Sensitive data

Do not store secrets or private personal data in validation inputs.

Prohibited examples:

```text
tokens
passwords
private keys
unredacted private correspondence
personal identifiers without authorization
licensed corpora without redistribution permission
```

When linguistic evidence is sensitive:

- use an approved protected repository;
- minimize the data;
- document access;
- redact when semantics permit;
- exclude it from public run reports;
- follow organizational retention policy.

---

# 49. Licensing and provenance

Every nontrivial external dataset must have documented provenance.

Record:

```text
source
license
retrieval or creation date
allowed use
modifications
project owner
```

Do not commit text copied from an external corpus without permission.

Small authored test examples should still identify their project ownership when required.

Provenance may be stored in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

or a dataset-specific README.

---

# 50. Determinism

Given the same:

```text
input bytes
scenario
project sources
GF version
RGL revision
configuration
normalization profile
```

the validation result should be deterministic.

Inputs must not depend on:

- current date;
- network response;
- mutable remote file;
- directory enumeration order;
- random selection;
- environment-specific path text;
- another scenario’s output;
- application state.

---

# 51. Version control

Every input used by a required checkpoint or release scenario must be version-controlled.

Version-control review should show:

- exact record changes;
- ordering changes;
- additions;
- removals;
- encoding changes;
- newline changes;
- structured-schema changes.

Avoid binary formats that hide semantic diffs.

---

# 52. Input change classification

## 52.1 Compatible correction

Examples:

- fixing a typo in a case whose intended semantics were clear;
- correcting accidental trailing whitespace;
- correcting an invalid record that never represented intended coverage.

Required review:

- consumer scenarios;
- affected gold;
- coverage matrix;
- focused validation.

## 52.2 Compatible extension

Examples:

- adding a new positive case;
- adding a new morphology word;
- adding a new regression record;
- adding a new optional dataset.

Required review:

- performance bounds;
- scenario assertions;
- gold;
- checkpoint coverage;
- release impact.

## 52.3 Breaking validation change

Examples:

- changing record format;
- changing case ID;
- changing ordering semantics;
- changing a positive case to negative;
- changing Unicode normalization policy;
- moving or renaming the file;
- changing expected ambiguity.

Required review:

```text
all consumers
scenario registry
assertions
gold
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
INTERFILE_CONTRACT_LOCK.md
DECISION_LOG.md when significant
```

---

# 53. Removing an input

Before removing a file or record:

```text
[ ] All scenario consumers identified
[ ] Requirement coverage reviewed
[ ] Gold impact reviewed
[ ] Registry updated
[ ] Coverage matrix updated
[ ] Known issue or decision references updated
[ ] No release criterion loses its only proof
[ ] Focused validation passes
[ ] Checkpoint or release validation rerun
```

A removed file must be removed from every registered consumer.

---

# 54. Moving an input

A move is a contract change.

Required actions:

1. move the file;
2. update registered paths;
3. update `.gfs` references;
4. update documentation;
5. update project contract relationships;
6. verify path containment;
7. run input lint;
8. run every consumer scenario.

Do not leave a duplicate at the old path to hide an incomplete migration.

---

# 55. Editing workflow

Recommended workflow:

1. identify the consuming scenario;
2. identify the requirement covered;
3. inspect current format rules;
4. make the smallest coherent input change;
5. run the input linter;
6. run the focused scenario;
7. inspect raw output;
8. inspect normalized output;
9. inspect gold diff;
10. update gold only when the changed behavior is intentional;
11. rerun the proving mode;
12. update project records.

---

# 56. Input linting

Recommended command:

```text
gf-wordbench project inputs lint
```

The linter should detect:

```text
unregistered file
registered missing file
path outside approved root
invalid UTF-8
UTF-8 BOM
missing final newline
CRLF when strict canonical mode is enabled
unexpected blank line
unexpected comment
leading or trailing whitespace
tab in non-TSV file
duplicate record
duplicate case ID
invalid field count
invalid JSON
unsupported schema version
record over size limit
file over size limit
unregistered consumer
consumer scenario missing
unused input
nondeterministic multi-file order
```

Strict mode:

```text
gf-wordbench project inputs lint --strict
```

---

# 57. Formatting operation

A separate explicit formatting command may normalize safe presentation details.

Conceptual command:

```text
gf-wordbench project inputs format
```

It may:

- convert CRLF to LF;
- add final newline;
- remove UTF-8 BOM;
- apply declared JSON formatting;
- validate NFC when configured.

It must not:

- reorder records;
- deduplicate;
- trim semantic whitespace;
- rewrite linguistic text;
- change case IDs;
- change format;
- update gold;
- alter scenarios.

Dry-run or diff preview should be available.

---

# 58. Validation failures

Input validation failures should distinguish:

```text
CONFIG
IO
SCRIPT
OTHER
```

Examples:

### Missing registered file

```text
validation_status = ERROR
error_kind = CONFIG
```

### Invalid UTF-8

```text
validation_status = ERROR
error_kind = IO
```

### Valid input with failing linguistic assertion

```text
validation_status = FAIL
error_kind = SCRIPT or project-defined semantic class
```

### Gold mismatch caused by changed input

```text
validation_status = FAIL
primary_message = gold mismatch
```

Input-format failure must not be reported as a GF syntax error when GF never received valid data.

---

# 59. Raw evidence

A scenario result should make the consumed input traceable.

Recommended evidence:

```text
input path
input hash
input byte size
input record count
input format
input schema when applicable
consumer scenario
selected record range when narrowed
```

Reports should not reproduce an entire large or sensitive dataset.

They may include bounded excerpts or case IDs.

---

# 60. Input hashes

Required release inputs should have a stable content hash in run evidence or the release manifest.

Recommended algorithm:

```text
SHA-256
```

A hash helps prove that:

- the scenario used the reviewed version;
- the release archive contains the correct input;
- a restored project matches release evidence.

A hash does not replace version control or provenance.

---

# 61. Input selection

A scenario should consume its complete registered input by default.

A diagnostic run may select:

- one case ID;
- one line range;
- one registered subset.

A narrowed diagnostic result must record the selection.

It must not be presented as complete checkpoint or release evidence.

---

# 62. Multiple input files

When a scenario consumes several files, define explicit order.

Example conceptual order:

```text
positive
ambiguous
negative
```

The order belongs to registration.

Do not infer order from filenames unless that rule is explicitly part of the contract.

---

# 63. Generated inputs

Release inputs should normally be authored or reviewed source assets.

Generated input may be used only when:

- the generator is versioned;
- inputs to the generator are recorded;
- generation is deterministic;
- output is reviewed or validated;
- generated content is version-controlled or captured as release evidence;
- the scenario does not regenerate mutable input silently.

Random input generation belongs to diagnostic workflows unless determinism is guaranteed.

---

# 64. Derived subsets

A smaller input subset may be derived for quick validation.

The derivation must be explicit and deterministic.

Preferred:

```text
a registered quick input file
```

Avoid:

```text
take the first ten records implicitly
```

because file reordering would silently change quick coverage.

---

# 65. Release inputs

An input is release-significant when consumed by a required release scenario or manual release criterion.

Release-significant inputs must be:

```text
registered
version-controlled
reviewed
format-valid
path-contained
hashable
deterministic
licensed
nonsecret
archivable
```

A missing release input is a release failure.

---

# 66. Optional inputs

Optional inputs may support:

- exploratory diagnostics;
- experimental scenarios;
- extended coverage;
- research review.

They must still be:

- registered when executable;
- safe;
- format-valid;
- visible in results when selected.

Optional does not mean unowned.

---

# 67. Manual-review inputs

Some inputs may support a manual linguistic review rather than a `.gfs` scenario.

Such a file must be registered in the manual criterion record.

The record must identify:

```text
review purpose
reviewer role
review method
expected decision
evidence location
release impact
```

Manual input must not be mistaken for executable scenario coverage.

---

# 68. Documentation for a dataset

A complex dataset should have a sibling README.

Example:

```text
project/validation/inputs/ambiguity-cases/README.md
```

It should define:

```text
purpose
provenance
license
format
fields
ordering
normalization
comment policy
blank-line policy
duplicate policy
consumers
coverage
maintenance owner
```

Do not repeat the entire global contract.

Document only dataset-specific rules.

---

# 69. Project configuration relationship

Project configuration or the project scenario registry must resolve input paths.

It must not contain:

- absolute developer paths;
- stale removed paths;
- broad uncontrolled globs;
- run-output paths;
- paths derived from GUI state.

Normal validation reads input registration.

It must not rewrite the input source.

---

# 70. Scenario authoring relationship

When adding an input-driven scenario:

```text
[ ] Scenario has one primary purpose
[ ] Input format selected
[ ] Input path registered
[ ] Consumer relationship documented
[ ] Native GF transfer tested
[ ] Case identity preserved
[ ] Marker protocol complete
[ ] Timeout finite
[ ] Output bounded
[ ] Assertions defined
[ ] Gold strategy defined
[ ] Input hash recorded in evidence
```

---

# 71. Gold relationship

Input changes may change normalized output.

A changed output does not automatically justify a gold update.

Review:

1. was the input change intentional;
2. is the new GF behavior correct;
3. does the scenario still test the intended contract;
4. did the expected ambiguity change;
5. did ordering change;
6. did normalization change;
7. does project documentation require update.

Gold remains immutable during normal validation.

---

# 72. Coverage relationship

Every release-significant input should map to a requirement or coverage category.

The coverage matrix may reference:

```text
input path
case ID
scenario ID
requirement ID
checkpoint ID
```

An input that covers no documented requirement should be removed, documented, or marked exploratory.

---

# 73. Known-issue relationship

A regression input linked to an issue must remain consistent with `KNOWN_ISSUES.md`.

When the issue status changes:

- update expected behavior;
- preserve the case when it prevents recurrence;
- record the resolving run;
- avoid deleting the only reproducer.

---

# 74. Status-ledger relationship

Temporary or fallback datasets must have a status-ledger entry when they affect validation truth.

Examples:

- incomplete corpus subset;
- manually curated provisional examples;
- known missing negative cases;
- temporary accepted ambiguity list.

The entry must define an exit condition.

---

# 75. Security review

Input security checks include:

```text
path containment
symlink or junction containment
size bounds
record bounds
encoding
no secrets
no unauthorized personal data
no command concatenation
no shell interpretation
no network fetch
no automatic external file inclusion
```

A trusted project input can still cause resource exhaustion.

Bounds remain mandatory.

---

# 76. Untrusted projects

A `.gfs` scenario and its input files are executable-validation assets.

For an untrusted project:

- inspect scenario commands;
- inspect input transfer;
- reject operating-system escapes;
- use an external sandbox;
- restrict filesystem access;
- restrict network access;
- cap output and runtime.

GF Wordbench is not a complete hostile-code sandbox.

---

# 77. Cleanup and backup

Input files are authoritative project assets.

Normal cleanup must not delete them.

Backups should include:

```text
project/validation/inputs/
scenario registration
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
provenance documentation
```

Release archives should preserve every required input or a verifiable project snapshot containing it.

---

# 78. Restore

After restoring validation inputs:

```text
[ ] Paths match registration
[ ] UTF-8 validation passes
[ ] Hashes match backup when available
[ ] Scenario consumers exist
[ ] Required gold exists
[ ] Focused scenarios pass
[ ] Checkpoints pass
[ ] Release is rerun when required
```

Do not reconstruct an authoritative input solely from normalized output unless no trusted source exists and the reconstruction is explicitly reviewed.

---

# 79. Required tests

Input infrastructure tests should cover:

```text
valid UTF-8 line file
BOM detection
CRLF acceptance and strict rejection
missing final newline
blank-line policy
comment policy
leading whitespace
trailing whitespace
tab policy
duplicate records
duplicate IDs
stable ordering
invalid TSV field count
invalid JSON
unsupported JSON schema
path traversal
symlink escape
missing registered file
unregistered file
unused file
shared consumer registration
path containing spaces
Unicode NFC
intentional decomposed Unicode case
large record bound
large file bound
input hash
diagnostic subset selection
release input manifest
```

---

# 80. Project contract checks

Recommended command:

```text
gf-wordbench project contracts check
```

Input-specific checks should verify:

1. every registered input exists;
2. every active input has a consumer;
3. every consumer scenario exists;
4. every path is project-contained;
5. every release input is version-controlled;
6. every complex format is documented;
7. every JSON format has a supported schema;
8. every input follows its blank-line policy;
9. every input follows its comment policy;
10. every input follows its duplicate policy;
11. every input follows its ordering policy;
12. removed paths have no consumers;
13. old language identifiers are absent;
14. no input points to run output;
15. no input contains prohibited secret patterns under approved scanning policy.

---

# 81. Input review checklist

```text
[ ] Purpose is documented
[ ] Consumer scenarios are registered
[ ] Path is project-relative
[ ] Filename is descriptive
[ ] Format is documented
[ ] UTF-8 is valid
[ ] BOM is absent
[ ] Newlines are canonical
[ ] Final newline exists
[ ] Unicode policy is satisfied
[ ] Blank-line policy is satisfied
[ ] Comment policy is satisfied
[ ] Whitespace policy is satisfied
[ ] Duplicate policy is satisfied
[ ] Ordering is stable
[ ] Case IDs are unique when used
[ ] Size is bounded
[ ] Provenance is documented
[ ] License permits repository use
[ ] No secrets are present
[ ] Native GF transfer is tested
[ ] Assertions remain valid
[ ] Gold impact is reviewed
[ ] Coverage matrix is updated
[ ] Focused scenario passes
[ ] Required checkpoint or release passes
```

---

# 82. Adding a new input file

Procedure:

1. define the validation requirement;
2. identify the consuming scenario;
3. select the simplest appropriate format;
4. choose a stable descriptive path;
5. create UTF-8 LF content;
6. document format semantics;
7. register the input;
8. update the scenario;
9. add assertion or gold strategy;
10. run input lint;
11. run the focused scenario;
12. inspect raw and normalized output;
13. update coverage documentation;
14. run the proving mode.

---

# 83. Adding a new case

Procedure:

1. identify the requirement covered;
2. determine positive, negative, ambiguity, or regression role;
3. add the record in stable order;
4. assign a case ID when the format supports one;
5. check duplicate policy;
6. run the focused scenario;
7. review output;
8. review gold difference;
9. update project records when behavior changes.

---

# 84. Changing format

A file-format change is a breaking input contract unless every consumer supports both formats during migration.

Required steps:

1. define the new format;
2. define version or migration policy;
3. update every reader and scenario;
4. convert inputs deterministically;
5. preserve the old source until validation succeeds;
6. compare semantic case inventory;
7. update registration;
8. update documentation;
9. run all consumers;
10. rerun checkpoints and release as applicable.

---

# 85. Anti-patterns

Prohibited:

```text
unregistered data file silently discovered by glob
absolute local path in scenario
input line concatenated into shell command
mixed commands and data in one file
implicit comment syntax
implicit blank-line skipping
silent whitespace trimming
silent deduplication
nondeterministic sorting
random release subset
spreadsheet-edited CSV with unknown dialect
gold output stored as input data
generated run output copied into inputs without review
secret or private data committed
large corpus used without bounds
removed input left in scenario registration
```

---

# 86. Quick reference

Default simple input contract:

```text
location:
  project/validation/inputs/

encoding:
  UTF-8 without BOM

newlines:
  LF

records:
  one logical item per line

blank lines:
  prohibited

comments:
  prohibited

ordering:
  stable and preserved

duplicates:
  prohibited unless explicitly justified

paths:
  project-relative and registered

release use:
  version-controlled and hashed

mutation:
  never modified by normal validation
```

---

# 87. Related documents

```text
project/README.md
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/RESEARCH_EVIDENCE.md
project/validation/README.md
project/validation/scenarios/README.md
project/validation/gold/README.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
```

---

# 88. Final input contract

The final ownership chain is:

```text
project validation requirement
    owns the reason for the case

input file
    owns the reviewed stimulus data

scenario registry
    owns the path, format, consumer, and policy

native .gfs scenario
    owns how GF receives the data

GF
    owns grammatical interpretation

GF Wordbench
    owns safe execution, capture, assertions, and comparison

gold or assertion
    owns the accepted outcome

release validation
    decides whether required evidence passes
```

The governing invariant is:

> Validation inputs are immutable reviewed project data during normal execution; they are never hidden commands, never implicit configuration, and never accepted without a documented consumer and purpose.
