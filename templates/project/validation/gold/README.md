# GF Wordbench Project Template — Golden Scenario Outputs

**Document ID:** `GF-WB-TEMPLATE-GOLD-README`  

**Document role:** Normative project template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Scope:** `project/validation/gold/` after project initialization  
**Applies to:** Reviewed expected scenario output, normalization contracts, scenario registration, gold comparison, explicit gold updates, checkpoint validation, release validation, migrations, backups, and project maintenance  
**Template owner:** GF Wordbench maintainers  
**Project owner:** `<PROJECT_OWNER>`  
**Project identity:** Defined by `project/project.toml`  
**Gold schema:** `gf-wordbench.scenario-gold/1.0`  
**Scenario-output schema:** `gf-wordbench.scenario-output/1.0`  
**Validation authority:** `project/docs/VALIDATION_SPEC.md`  
**Project contract lock:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Target template path:** `templates/project/validation/gold/README.md`  
**Last reviewed:** `<YYYY-MM-DD OR PROJECT RELEASE>`

---

## 1. Template use

This file is a template for the active project’s gold directory.

When initializing a project:

1. copy this directory to:

   ```text
   project/validation/gold/
   ```

2. replace required project-owner metadata;
3. register actual scenario-to-gold relationships;
4. remove example entries that do not apply;
5. create gold files only through reviewed explicit update or initialization;
6. validate every gold file against the canonical text schema;
7. verify no required project placeholder remains in the initialized active project;
8. commit required gold files to version control.

Placeholders are permitted in this template.

Unresolved required placeholders are prohibited in the initialized active project.

---

## 2. Purpose

This directory contains reviewed expected normalized output for registered native GF scenarios.

A gold file answers:

```text
For this scenario,
under this normalization contract,
what exact stable output has the project accepted?
```

The validation relationship is:

```text
registered .gfs scenario
→ real GF execution
→ raw stdout and stderr
→ marker validation
→ normalized scenario output
→ exact comparison with reviewed .gold
→ scenario result
→ checkpoint or release gate
```

Gold files are authoritative project validation assets.

They are not generated run logs.

They are not raw GF output.

They are not scenario input data.

They are not editable report prose.

---

## 3. Core rule

> A gold file is accepted project behavior, not merely the latest observed output.

A gold file is valid only when:

```text
its scenario is registered
and its scenario ID is correct
and its filename is correct
and its schema version is supported
and its normalization version matches the runner
and its sections match the scenario contract
and its contents were reviewed
and it is version-controlled when required
and normal validation does not modify it
```

A current scenario result must never become accepted behavior automatically.

---

## 4. What belongs here

Store files with the canonical extension:

```text
.gold
```

Canonical path:

```text
project/validation/gold/<scenario-id>.gold
```

Appropriate gold content includes stable normalized evidence such as:

```text
reviewed linearizations
reviewed abstract parse trees
reviewed bounded ambiguity
reviewed missing-linearization inventory
reviewed morphology output
reviewed operation introspection
reviewed bounded-generation sections
reviewed PGF smoke output
```

Only behavior declared by the scenario and validation specification belongs in gold.

---

## 5. What does not belong here

Do not store:

```text
raw stdout
raw stderr
GF prompts before normalization
unreviewed current output
scenario scripts
scenario input files
temporary diffs
debug notes
human explanations
application state
run summaries
compiled .gfo files
release .pgf files
external corpus data
local absolute paths
secrets
```

Canonical neighboring roots:

```text
project/validation/scenarios/
project/validation/inputs/
```

Generated evidence belongs in the run directory.

---

## 6. Ownership

Project maintainers own gold files.

Canonical writers are:

```text
explicit gold updater
authorized project maintainer
project initializer or migrator under explicit operation
```

Readers include:

```text
gold comparator
scenario result builder
checkpoint validation
release validation
reports
contract checks
archive and recovery tooling
```

A reader must not rewrite a gold file.

Normal scenario execution is read-only with respect to gold.

---

## 7. Canonical schema identity

Gold files use the canonical text schema:

```text
schema_id: gf-wordbench.scenario-gold
schema_version: 1.0
```

The schema identity is represented by the required first header line:

```text
# GF_WORDBENCH_GOLD 1.0
```

This is a text schema, not JSON.

Do not add an independent JSON sidecar merely to duplicate the same identity unless a later versioned contract explicitly requires one.

---

## 8. Canonical file format

Every canonical gold file uses:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: <scenario-id>
# normalization_version: 1.0
--- BEGIN <section-id> ---
<expected normalized GF output>
--- END <section-id> ---
```

Example:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: parse-basic
# normalization_version: 1.0
--- BEGIN parse-basic ---
<expected normalized GF output>
--- END parse-basic ---
```

The example output placeholder must be replaced in a real gold file.

---

## 9. Header contract

The canonical header contains exactly these required lines in this order:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: <scenario-id>
# normalization_version: <version>
```

Rules:

- the schema marker is the first line;
- the scenario ID is present exactly once;
- the normalization version is present exactly once;
- required header keys use lowercase names shown above;
- no blank line is required between the header and first section;
- unrecognized required-looking header keys are prohibited;
- future optional keys require a compatible schema decision;
- comments outside the defined header are not free-form metadata.

Project rationale and review notes belong in project documentation or version-control history.

---

## 10. Scenario ID contract

The `scenario_id` value must agree with:

```text
gold filename
project scenario registry
.gfs scenario markers
scenario result
validation specification
coverage matrix
```

Canonical relationship:

```text
scenario ID:
  parse-basic

script:
  project/validation/scenarios/parse-basic.gfs

gold:
  project/validation/gold/parse-basic.gold
```

A mismatch is a configuration or schema failure.

Do not infer a new scenario ID from a renamed gold file without updating all project contracts.

---

## 11. Normalization-version contract

The gold file records:

```text
# normalization_version: <version>
```

The version must match the normalization profile used to produce the current normalized scenario output.

A mismatch is not an ordinary text difference.

It is a normalization contract failure.

When normalization changes:

1. preserve raw evidence;
2. identify every affected scenario;
3. identify every affected gold file;
4. explain the semantic and nonsemantic effects;
5. increment the normalization contract as required;
6. regenerate candidate normalized output;
7. review every difference;
8. update gold explicitly;
9. rerun the proving validation modes.

Normalization must not be changed only to hide a project regression.

---

## 12. Section contract

Gold content is divided into exact sections:

```text
--- BEGIN <section-id> ---
...
--- END <section-id> ---
```

Rules:

- section IDs are unique within one gold file;
- begin and end IDs match;
- sections do not overlap;
- section order follows the scenario contract;
- every required scenario section appears;
- no undeclared section appears unless the scenario registry permits it;
- a missing end marker makes the gold invalid;
- duplicate sections make the gold invalid;
- section IDs are stable project contracts.

---

## 13. Section naming

Recommended section ID form:

```text
lowercase-kebab-case
```

Examples:

```text
load
missing-linearizations
linearize-basic
parse-positive
parse-negative
ambiguity-basic
morphology-nouns
generation-bounded
```

A section name should identify the behavior proven.

Avoid:

```text
test1
section-a
new-output
final
misc
```

Renaming a section is a breaking comparison change unless compatibility handling is provided.

---

## 14. One gold per scenario

Default policy:

```text
one authoritative .gold file per gold-backed scenario
```

A gold file may contain several ordered sections.

This preserves:

- one scenario-to-gold relationship;
- one scenario identity;
- one normalization version;
- one review unit;
- one comparison result.

Multiple gold variants are permitted only when the project registry explicitly defines the variant identity and selection rule.

Do not create competing files whose authoritative status is inferred from filename suffixes such as:

```text
parse.gold
parse-new.gold
parse-final.gold
parse-2.gold
```

---

## 15. Required file properties

Canonical gold files use:

```text
UTF-8 without BOM
LF newlines
final newline
```

Additional rules:

- trailing spaces are prohibited;
- tabs are preserved only when semantically meaningful and explicitly allowed;
- ANSI control sequences are prohibited;
- NUL bytes are prohibited;
- undecodable bytes are prohibited;
- file contents are deterministic.

The comparator may normalize CRLF input for compatibility, but canonical writers emit LF.

---

## 16. Unicode

Gold may contain direct Unicode linguistic output.

The gold file must preserve the exact normalized code-point sequence expected by the project.

Do not apply an undocumented Unicode transformation during comparison.

When project policy requires NFC or another form, the normalizer and documentation must state it.

Normalization tests must distinguish:

```text
orthographically equivalent display
from
byte- or code-point-distinct expected output
```

---

## 17. Meaningful whitespace

Semantically meaningful whitespace inside normalized GF output must be preserved.

Examples may include:

```text
token separation
line structure
tree indentation when declared stable
empty realization represented by an exact blank payload
punctuation spacing
```

The normalizer may remove trailing spaces under the canonical schema.

It must not collapse arbitrary internal whitespace.

A whitespace-only difference may be a real validation failure.

---

## 18. Empty output

An empty gold is valid only when explicitly documented.

Preferred representation for a section with no payload:

```text
--- BEGIN expected-empty ---
--- END expected-empty ---
```

The scenario assertion must also declare that an empty normalized section is expected.

Do not use a zero-byte `.gold` file.

A zero-byte file lacks:

- schema identity;
- scenario identity;
- normalization version;
- section contract.

---

## 19. Empty string versus missing output

The project must distinguish:

```text
valid empty linguistic realization
no result
missing section
failed GF command
normalization error
truncated output
```

A valid empty realization requires explicit scenario and gold design.

A missing result must not be converted into an empty accepted section.

---

## 20. Stable replacement tokens

Canonical normalization may use only documented stable tokens.

Initial allowed tokens include:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

These tokens replace unstable machine or run data.

They must not replace arbitrary linguistic text.

A new token requires:

- normalization contract update;
- tests;
- gold review;
- documentation;
- compatibility review.

---

## 21. Raw versus normalized evidence

Raw evidence is captured first.

Canonical relationship:

```text
raw scenario stdout
raw scenario stderr
→ normalization
→ canonical scenario-output text
→ gold comparison
```

Gold contains only expected normalized output.

It must not contain raw process metadata that the normalizer intentionally removes.

Raw output remains available in the run directory for diagnosis.

---

## 22. Exact comparison

Gold comparison occurs after canonical newline handling and schema validation.

The comparison is exact within the normalized content contract.

It must consider:

```text
header identity
scenario ID
normalization version
section inventory
section order
section text
meaningful whitespace
final newline policy
```

A comparator must not:

- silently ignore an unknown section;
- reorder sections;
- sort linguistic lines;
- deduplicate lines;
- trim semantic content;
- paraphrase GF diagnostics;
- choose the “closest” gold;
- update gold during comparison.

---

## 23. Difference evidence

A gold mismatch must produce reviewable difference evidence.

The diff should identify:

```text
scenario ID
gold path
normalized-output path
normalization version
section ID
added lines
removed lines
changed lines
context
```

The diff is a generated run artifact.

It does not belong in this source directory.

A mismatch remains a validation failure until:

- implementation is corrected;
- or the new behavior is deliberately accepted through explicit gold update.

---

## 24. Missing gold

A missing required gold file is a failure.

Required behavior:

```text
required scenario + configured gold + file missing
→ validation failure or configuration error
```

It must not result in:

```text
automatic gold creation
automatic pass
silent scenario downgrade
empty expected output
```

An optional scenario without configured gold may use assertions only.

That choice must be explicit in the scenario registry.

---

## 25. Unregistered gold

A `.gold` file that is not referenced by an active scenario is not active validation evidence.

The project contract checker should report:

```text
unregistered gold
orphan gold
obsolete scenario ID
duplicate authoritative gold
```

The maintainer must:

- register it;
- archive it outside the active source tree;
- or remove it after review.

Do not leave obsolete gold files to create ambiguous authority.

---

## 26. Scenario without gold

Not every scenario requires gold.

A scenario may be assertion-only when its contract is better represented by:

```text
required marker
forbidden diagnostic
required artifact
bounded result count
empty/nonempty section
regular-expression assertion
```

The registry must explicitly identify:

```text
gold = none
```

or its final equivalent.

A missing gold path and a configured-but-missing gold file are not equivalent.

---

## 27. Required and optional gold

A gold file may support:

```text
required scenario
optional scenario
diagnostic-only scenario
```

Release behavior is controlled by scenario and project policy.

Rules:

- required applicable gold mismatch blocks the mode;
- optional mismatch remains visible;
- release policy may promote optional evidence to blocking;
- gold requirement must not be inferred from directory presence.

---

## 28. Project registration

Every active gold relationship must be registered through project configuration or the final scenario registry.

Registration should resolve:

```text
scenario ID
gold path
required or optional state
applicable modes
checkpoint associations
normalization profile
required sections
comparison policy
owner
```

The exact persisted representation belongs to the project schema.

---

## 29. Gold registry template

Replace this table in the initialized project.

| Scenario ID | Gold path | Required | Modes | Normalization | Required sections | Owner |
|---|---|---:|---|---|---|---|
| `<SCENARIO-ID>` | `project/validation/gold/<SCENARIO-ID>.gold` | `<YES/NO>` | `<MODES>` | `<VERSION>` | `<SECTION IDS>` | `<OWNER>` |

Delete the placeholder row after adding real project entries.

---

## 30. Gold purpose record

Every gold-backed scenario must have a documented purpose.

Template:

```text
Scenario ID:
  <SCENARIO-ID>

Gold protects:
  <LINGUISTIC OR CONTRACTUAL BEHAVIOR>

Sections:
  <SECTION IDS>

Expected variation:
  <NONE OR DOCUMENTED POLICY>

Blocking modes:
  <MODES>

Related requirements:
  <VAL-* IDS>

Related contracts:
  <PIFC-* IDS>
```

A gold file without a documented acceptance criterion is invalid project coverage.

---

## 31. Appropriate gold use

Gold is appropriate when exact reviewed normalized output is meaningful and stable.

Typical uses:

- representative linearization;
- representative parse trees;
- accepted ambiguity inventory;
- missing-linearization list;
- morphology analysis;
- operation output;
- deterministic bounded generation;
- PGF smoke output.

Gold is less appropriate when:

- order is intentionally irrelevant and assertion sets are clearer;
- output is intentionally random;
- only existence of an artifact matters;
- exact wording is tool-version noise;
- the semantic contract is a count or predicate;
- output contains sensitive data.

Use the simplest stable proof.

---

## 32. Parsing gold

Parse gold should state the accepted parse contract through exact normalized output or complementary assertions.

Review:

```text
tree identity
tree count
ambiguity
tree order
category
language
negative cases
```

Do not accept a new tree solely because GF emitted it.

Determine whether it is:

- intended additional coverage;
- overgeneration;
- changed abstraction;
- toolchain variation;
- ordering noise;
- normalization defect.

---

## 33. Linearization gold

Linearization gold protects:

```text
surface form
word order
inflection
agreement
orthography
punctuation
accepted variants
```

Normalization must not erase meaningful orthographic or spacing behavior.

Empty strings must be distinguishable from missing output.

---

## 34. Missing-linearization gold

A missing-linearization scenario may compare the normalized output of:

```text
pg -missing
```

or the final approved equivalent.

Recommended release policy:

```text
required missing-linearization section is empty
```

When exceptions are allowed, each expected missing item must be documented in:

```text
STATUS_LEDGER.md
KNOWN_ISSUES.md
or an explicit project decision
```

A changed missing list requires project contract review.

---

## 35. Morphology gold

Morphology gold may protect:

```text
analysis
lemma
paradigm forms
inflection tables
missing-word results
ambiguity
```

Review toolchain wording separately from linguistic content.

A normalization rule must not paraphrase or reorder meaningful analyses unless the contract explicitly treats them as an unordered set.

---

## 36. Round-trip gold

Round-trip gold should document whether the project expects:

```text
identity
canonicalization
accepted variant
bounded ambiguity
```

Do not treat any changed relinearization as failure without the documented round-trip contract.

Do not accept any changed relinearization without review.

---

## 37. Generation gold

Exact generation gold is permitted only when output is deterministic.

Requirements:

```text
explicit category
explicit depth
explicit result limit
explicit language
deterministic order
finite timeout
stable normalization
```

Random generation must not use exact gold unless determinism is explicitly guaranteed.

For exploratory generation, prefer assertions and diagnostic evidence.

---

## 38. Diagnostic wording in gold

GF diagnostic wording may vary across supported versions.

Do not include unstable diagnostic prose in gold unless:

- exact wording is part of the intended contract;
- supported GF versions are constrained;
- compatibility policy documents it;
- normalization cannot safely isolate semantic data.

Prefer stable extracted sections for project behavior.

Raw diagnostics remain available separately.

---

## 39. GF-version changes

When GF version changes:

1. preserve the last accepted release evidence;
2. record old and new versions;
3. run compatibility scenarios;
4. inspect raw differences;
5. inspect normalized differences;
6. determine linguistic versus tool-only changes;
7. update normalization only for nonsemantic instability;
8. review every affected gold;
9. rerun checkpoints and release.

Do not bulk-accept all differences because the executable version changed.

---

## 40. RGL changes

RGL changes can alter:

```text
imports
public operations
linearization
parsing
generation
diagnostics
PGF behavior
```

A new RGL revision requires affected gold review.

Record the accepted RGL identity in release evidence.

---

## 41. Source changes

A source change may legitimately change gold.

Before updating:

```text
identify provider
identify consumers
identify changed project contract
identify affected scenario
inspect old and new raw evidence
verify intended linguistic behavior
update project documentation
```

Gold is a consumer of implementation behavior.

It must be updated as part of the coordinated change unit.

---

## 42. Scenario changes

Changing scenario commands, sections, inputs, languages, categories, or ordering may change gold independently of grammar behavior.

Required review:

```text
scenario purpose
marker structure
input inventory
normalization profile
required sections
gold path
coverage matrix
release modes
```

A scenario refactor that claims semantic equivalence must prove that normalized output remains equivalent or explain the intentional difference.

---

## 43. Input changes

A validation-input change may alter gold.

Review:

```text
added case
removed case
case order
case ID
positive/negative role
ambiguity expectation
Unicode and whitespace
```

Do not update gold before confirming the input still proves the intended requirement.

---

## 44. Normalization changes

A normalization change is cross-cutting.

It requires:

```text
normalizer change
scenario-output schema/profile review
gold schema/profile review
tests
affected gold inventory
diff review
version increment when required
documentation update
```

Changing normalization without reviewing gold files is prohibited.

---

## 45. Explicit gold update

Canonical command family:

```text
gf-wordbench gold update <scenario-id>
```

The exact CLI syntax belongs to the CLI reference.

The operation must be distinct from ordinary validation.

---

## 46. Update workflow

The updater must:

1. resolve the active project;
2. validate the registered scenario;
3. resolve the configured gold path;
4. verify the GF executable and normalization profile;
5. run the scenario in a fresh GF process;
6. preserve raw stdout and stderr;
7. validate required markers;
8. normalize output;
9. validate canonical scenario-output schema;
10. compare against existing gold when present;
11. show or save the diff;
12. require explicit authorization;
13. write a sibling temporary gold file;
14. validate the candidate gold;
15. flush and close it;
16. replace the destination atomically;
17. preserve failure evidence;
18. report the updated path;
19. require version-control review;
20. require rerun of the proving validation mode.

---

## 47. Interactive confirmation

Interactive update should display:

```text
project ID
scenario ID
script path
gold path
GF executable
GF version
normalization version
changed sections
added lines
removed lines
```

The user must explicitly confirm the update.

A generic prior preference must not silently approve future gold changes.

---

## 48. Noninteractive update

Automation may update gold only through a dedicated explicit noninteractive flag and controlled workflow.

Requirements:

```text
explicit scenario scope
dedicated authorization flag
preserved diff artifact
atomic write
machine-readable update report
version-control diff review
no automatic merge
```

Ordinary CI validation must remain read-only.

A CI job that updates gold must be clearly separated from a job that verifies gold.

---

## 49. Atomic writes

Gold updates use atomic replacement where supported.

Required sequence:

```text
write sibling temporary file
→ flush
→ close
→ validate
→ replace destination atomically
```

A failed update must not destroy the last valid gold.

Temporary candidates must not become active merely because they are newer.

---

## 50. Version-control review

Required gold files must be version-controlled.

Review should show:

```text
header changes
normalization-version changes
section changes
line additions
line removals
ordering changes
Unicode changes
whitespace changes
```

Binary or compressed gold is prohibited unless a separate versioned artifact contract explicitly permits it.

Text diffs are part of the review mechanism.

---

## 51. Commit discipline

A gold change should normally be committed with the source, scenario, input, or normalization change that caused it.

The commit or review description should state:

```text
why expected behavior changed
which scenarios changed
which sections changed
whether linguistic behavior changed
whether normalization changed
which proving mode passed
```

Do not create unexplained bulk “refresh gold” commits.

---

## 52. Gold-only change

A gold-only change is valid only when correcting an incorrect accepted expectation or canonical formatting defect.

It still requires:

- evidence that implementation behavior is correct;
- explanation of why gold was wrong;
- scenario review;
- normalization review;
- proving validation.

A gold-only change must not hide an unreviewed implementation regression.

---

## 53. Formatting-only change

Safe canonical formatting corrections may include:

```text
CRLF to LF
adding final newline
removing UTF-8 BOM
removing prohibited trailing spaces
```

Even formatting-only changes require schema validation.

They must not alter semantic payload.

A formatting command should show a diff.

---

## 54. Gold migration

A schema or format migration must:

1. read the old source without overwriting it;
2. identify source schema or legacy format;
3. parse the scenario identity;
4. map section boundaries;
5. preserve semantic payload;
6. assign target normalization version deliberately;
7. write a candidate destination;
8. validate the candidate;
9. compare semantic content;
10. promote atomically;
11. retain source until success;
12. run all affected scenarios.

A migration must not claim success when scenario identity or section meaning is ambiguous.

---

## 55. Scenario rename migration

Renaming a scenario requires coordinated change to:

```text
project configuration
.gfs filename
scenario markers
gold filename
gold scenario_id header
input paths when scenario-specific
validation specification
coverage matrix
interfile contract lock
known issue and decision references
```

Do not copy the old gold to the new name without reviewing the scenario contract.

---

## 56. Section rename migration

A section rename changes comparison identity.

Required actions:

- update `.gfs` marker IDs;
- update gold begin/end IDs;
- update assertions;
- update normalization tests;
- update documentation;
- rerun focused and proving modes.

Retaining both old and new sections temporarily requires explicit compatibility policy.

---

## 57. Splitting a scenario

When one scenario becomes several:

1. define new scenario purposes;
2. define new stable IDs;
3. split commands and inputs;
4. split normalized sections;
5. create one authoritative gold per new gold-backed scenario;
6. retire the old registry entry;
7. update coverage;
8. preserve history in version control;
9. run checkpoints and release.

Do not keep the old gold active as an undeclared aggregate baseline.

---

## 58. Combining scenarios

When several scenarios combine:

- define the combined purpose;
- define deterministic section order;
- define new scenario ID;
- merge only compatible normalization contracts;
- review every expected section;
- retire old gold registrations;
- rerun complete validation.

A combined gold must not erase which requirement each section proves.

---

## 59. Gold linter

Recommended command:

```text
gf-wordbench project gold lint
```

The linter should detect:

```text
missing schema header
wrong schema version
missing scenario_id
duplicate scenario_id header
filename and scenario ID mismatch
normalization-version mismatch
missing begin marker
missing end marker
mismatched section ID
duplicate section ID
unexpected section
wrong section order
UTF-8 BOM
invalid UTF-8
CRLF in strict mode
missing final newline
trailing whitespace
ANSI control sequence
zero-byte file
unregistered gold
registered missing gold
duplicate authoritative gold
obsolete scenario ID
unsupported stable token
unresolved template placeholder in active project
```

Strict mode:

```text
gf-wordbench project gold lint --strict
```

---

## 60. Schema check

Recommended command:

```text
gf-wordbench schemas check
```

Gold-specific schema checks should verify:

```text
gf-wordbench.scenario-gold identity
supported schema version
canonical header
canonical sections
canonical encoding
canonical newline policy
scenario registration
normalization compatibility
```

A schema check validates structure.

It does not approve linguistic content.

---

## 61. Comparison tests

Framework and project tests should cover:

```text
exact match
one added line
one removed line
changed line
section added
section removed
section reordered
wrong scenario ID
wrong normalization version
missing end marker
duplicate section
CRLF normalization
meaningful whitespace difference
empty expected section
zero-byte gold rejection
missing required gold
optional no-gold scenario
normal run remains read-only
explicit update writes atomically
failed update preserves old gold
```

---

## 62. Real GF integration

A small neutral GF fixture should prove:

```text
scenario execution
normalization
canonical scenario-output generation
gold exact match
gold mismatch
marker failure
update candidate generation
```

Project-specific integration should cover all required gold-backed scenarios.

---

## 63. Release contract

A required release gold passes only when:

```text
scenario is applicable
scenario execution completes
required markers complete
fatal diagnostic checks pass
normalization succeeds
normalization version matches
gold schema validates
gold exists
exact comparison matches
```

A required mismatch blocks release.

A missing required gold blocks release.

A gold parse or schema error blocks release.

---

## 64. Checkpoint contract

A checkpoint may require a subset of project gold files.

Checkpoint registration should identify:

```text
checkpoint ID
scenario IDs
gold paths
required sections
blocking policy
```

A gold-backed scenario may belong to several checkpoints when its purpose genuinely proves each boundary.

Avoid broad reuse that obscures coverage.

---

## 65. Diagnostic mode

Diagnostic mode may:

- run one gold-backed scenario;
- compare one section;
- produce expanded diff context;
- select a registered input subset;
- compare an alternative toolchain.

A narrowed diagnostic match is not complete checkpoint or release proof.

The result must record the narrowed scope.

---

## 66. Quick mode

Quick mode may run one small gold-backed smoke scenario.

A successful quick comparison proves only that selected scope.

It does not certify all project golds.

---

## 67. Optional variation

When several outputs are linguistically acceptable, do not encode accidental variation as unstable exact gold.

Choose one of these strategies:

```text
canonical output policy
explicit accepted variants in structured assertions
separate registered scenario variants
deterministic sorted semantic set when sorting is contractually valid
```

Do not make the comparator pick any file matching a wildcard.

---

## 68. Ordering variation

Output order may be:

```text
semantic and fixed
nonsemantic but deterministically canonicalized
tool-defined and supported-version stable
```

The project must state which applies.

Sorting is permitted only when:

- order is not semantic;
- the normalization contract documents sorting;
- duplicates remain meaningful or are handled explicitly;
- tests prove stability.

Do not sort parse trees or generations merely to make diffs smaller without reviewing semantic impact.

---

## 69. Ambiguity variation

Accepted ambiguity must be explicit.

Gold may protect:

```text
exact ordered tree list
exact canonicalized tree set
bounded list plus required/forbidden assertions
```

A new ambiguity is not automatically acceptable.

A lost ambiguity is not automatically an improvement.

Review project linguistic intent.

---

## 70. Tool noise

Examples of potentially removable nonsemantic noise:

```text
GF prompt
approved version banner
absolute project path
absolute RGL path
absolute run path
executable path
timing line
ANSI control sequence
```

Every removed class must be documented and tested.

Do not add a noise rule in response to a single unexplained mismatch without confirming the text is nonsemantic.

---

## 71. Linguistic content protection

Normalization and gold maintenance must preserve:

```text
surface strings
word order
inflection
agreement
orthography
punctuation when contractual
abstract trees
function names
category identity
ambiguity
missing-linearization names
morphological analyses
```

A rule that can erase these elements is prohibited unless a higher-level project contract explicitly defines a safe canonicalization.

---

## 72. Secrets and privacy

Gold files must not contain:

```text
passwords
tokens
private keys
private environment dumps
unredacted personal data
unauthorized corpus text
```

Absolute local paths should be replaced by approved stable tokens through normalization.

If a scenario handles sensitive data, the project needs a protected validation and reporting policy.

---

## 73. Licensing

Expected output may reproduce scenario inputs or external linguistic data.

The project must ensure that committed gold content may be stored and distributed under the repository policy.

Record provenance and licensing in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

or a dataset-specific document.

---

## 74. File size

Gold files must remain bounded and reviewable.

The project should define:

```text
maximum gold file size
maximum section size
maximum line length
maximum section count
```

Large deterministic outputs should be replaced by focused representative coverage or structured assertions when exact full output is not necessary.

A large gold exception must identify:

- purpose;
- owner;
- review method;
- retention impact;
- release impact.

---

## 75. Truncation

A truncated normalized output must never compare as complete gold evidence.

When raw evidence is truncated due to output limits:

```text
scenario result = failure or error according to contract
gold comparison = invalid
```

Do not truncate both current and expected output to obtain a match.

---

## 76. Hashes

Release evidence should record the SHA-256 of every required gold file or a source snapshot containing it.

A hash supports:

- release reproducibility;
- backup verification;
- restored-project validation;
- comparison identity.

A hash does not replace semantic review or version control.

---

## 77. Manifest and archive relationship

Gold files are project source assets, not ordinary run-owned artifacts.

A release archive should preserve:

- a project snapshot containing required gold;
- or explicit gold copies with project-relative paths and hashes.

The run manifest may reference source fingerprints or release snapshot artifacts according to the final archive contract.

A release must be reproducible against the same accepted gold state.

---

## 78. Backup

Project backups must include:

```text
project/validation/gold/
scenario registry
normalization documentation
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
INTERFILE_CONTRACT_LOCK.md
```

Gold is not disposable cache.

Normal cleanup must not delete it.

---

## 79. Restore

After restoring gold files:

```text
[ ] Paths match scenario registration
[ ] Schema lint passes
[ ] Scenario IDs match filenames
[ ] Normalization versions are supported
[ ] Hashes match backup when available
[ ] Required scenarios exist
[ ] Required inputs exist
[ ] Focused comparisons pass
[ ] Checkpoints pass
[ ] Release is rerun when required
```

Do not treat a restored historical gold as compatible with current normalization without verification.

---

## 80. Recovery from missing gold

Preferred recovery sources:

```text
version control
verified project backup
verified release archive project snapshot
```

Current normalized output may help reconstruct a candidate.

It must not become accepted gold without full review.

Recovery procedure:

1. restore trusted historical gold when available;
2. validate schema and normalization version;
3. compare against current output;
4. identify intended project changes;
5. perform explicit update only when appropriate;
6. rerun the proving mode.

---

## 81. Recovery from malformed gold

Procedure:

1. preserve the malformed file;
2. identify the last valid version;
3. lint the candidate;
4. validate scenario identity;
5. validate section inventory;
6. compare semantic payload;
7. write a corrected candidate atomically;
8. rerun the scenario;
9. rerun checkpoint or release.

Do not silently repair malformed gold during ordinary validation.

---

## 82. Recovery from failed update

A failed update must leave the previous valid gold intact.

Preserve:

```text
raw scenario output
normalized candidate
diff
temporary candidate
failure diagnostic
```

Retry only after correcting:

- filesystem permissions;
- schema failure;
- marker failure;
- normalization failure;
- project configuration;
- insufficient disk space.

---

## 83. Cleanup

Normal cleanup may remove generated:

```text
gold diffs
candidate normalized output
temporary run artifacts
```

It must not remove active `.gold` source files.

An explicit project reset may replace gold only after verified backup and confirmation.

---

## 84. Gold change checklist

```text
[ ] Scenario ID confirmed
[ ] Scenario purpose confirmed
[ ] Gold path confirmed
[ ] Source change identified
[ ] Scenario change reviewed
[ ] Input change reviewed
[ ] GF version recorded
[ ] RGL revision reviewed
[ ] Raw stdout reviewed
[ ] Raw stderr reviewed
[ ] Markers complete
[ ] Normalized output reviewed
[ ] Normalization version correct
[ ] Diff reviewed section by section
[ ] Linguistic correctness reviewed
[ ] Ambiguity reviewed
[ ] Ordering reviewed
[ ] Whitespace and Unicode reviewed
[ ] Project documentation updated
[ ] Coverage matrix updated
[ ] Status and known issues updated
[ ] Explicit update used
[ ] Atomic write succeeded
[ ] Gold lint passes
[ ] Focused scenario passes
[ ] Checkpoint passes
[ ] Release passes when applicable
[ ] Version-control diff committed
```

---

## 85. Adding a new gold-backed scenario

Procedure:

1. define a validation requirement;
2. create a single-purpose `.gfs` scenario;
3. add canonical scenario and section markers;
4. register the scenario;
5. register inputs;
6. define normalization profile;
7. define required sections;
8. run the scenario;
9. inspect raw evidence;
10. inspect normalized candidate;
11. create gold through explicit reviewed initialization;
12. lint the gold;
13. add coverage mapping;
14. run checkpoint or release.

---

## 86. Removing a gold file

Before removal:

```text
[ ] Scenario removal or no-gold conversion is intentional
[ ] Requirement coverage is preserved
[ ] Scenario registry updated
[ ] Validation specification updated
[ ] Coverage matrix updated
[ ] Interfile lock updated
[ ] Checkpoints reviewed
[ ] Release criteria reviewed
[ ] Historical references reviewed
[ ] No active consumer remains
```

Do not remove the only proof of a release requirement without replacing it.

---

## 87. Renaming a gold file

A filename is contractual.

Required actions:

- update scenario ID when identity changes;
- update registry path;
- update header;
- update scenario markers;
- update documentation;
- update tests;
- update archive references;
- rerun comparison.

A filename change without scenario identity change should be avoided unless the registry contract requires it.

---

## 88. Review roles

A project may define:

```text
scenario author
linguistic reviewer
normalization reviewer
release owner
```

One person may hold several roles in a small project.

Release-significant gold should receive review appropriate to project governance.

The reviewer must understand what the scenario proves.

---

## 89. Manual edit policy

Direct manual editing of gold payload is discouraged.

It may be permitted for:

- correcting a known invalid expectation;
- repairing canonical formatting;
- constructing a deliberately reviewed initial baseline.

Manual edits still require:

```text
schema lint
comparison
review
proving validation
version-control diff
```

Never manually edit gold merely to make a current failure pass.

---

## 90. Gold versus assertion decision guide

Use exact gold when:

```text
the full normalized output is meaningful
the output is deterministic
line-by-line review is useful
regression stability is required
```

Use assertions when:

```text
only presence or absence matters
only a count matters
order is intentionally irrelevant
the output includes unstable nonsemantic details
exact output would be overly large
```

Use both when:

```text
gold protects reviewed output
and assertions enforce critical semantic conditions
```

---

## 91. Gold quality criteria

A good gold file is:

```text
focused
deterministic
reviewable
schema-valid
small enough to understand
linguistically meaningful
free of machine-local noise
traceable to a scenario
traceable to requirements
stable under supported toolchains
explicitly updated
```

A large unexplained snapshot is weak validation evidence.

---

## 92. Gold drift indicators

Probable drift exists when:

- gold filename differs from scenario ID;
- header scenario ID differs from registry;
- normalization version differs from current runner;
- gold changes during normal validation;
- a required gold disappears;
- an orphan gold remains;
- section order differs from scenario;
- a new section appears without documentation;
- stable tokens replace linguistic text;
- an RGL change causes bulk gold changes without review;
- a source change affects output but gold is not reviewed;
- a gold commit has no causal source or specification change;
- active project gold contains template placeholders;
- current output matches only after undocumented trimming or sorting.

Every drift indicator requires contract review.

---

## 93. Anti-patterns

Prohibited:

```text
copy current output over gold automatically
create missing gold during release
update every gold after a toolchain change without review
store raw stdout as gold
remove marker sections from canonical format
ignore normalization-version mismatch
choose among several gold files by wildcard
treat zero-byte gold as ordinary expected output
sort parse trees only to suppress a diff
normalize away inflection or word order
edit gold from a report writer
commit absolute developer paths
store secrets
use random generation as exact gold
accept mismatch because exit code is zero
```

---

## 94. Required project checks

Recommended command:

```text
gf-wordbench project contracts check
```

Gold-specific checks should verify:

1. every registered required gold exists;
2. every gold belongs to one registered scenario;
3. filenames match scenario IDs;
4. schema headers are valid;
5. normalization versions are supported;
6. sections match scenario contracts;
7. required golds are version-controlled;
8. no duplicate authoritative gold exists;
9. no active gold contains unresolved placeholders;
10. no normal validation path writes gold;
11. no report writer owns gold updates;
12. gold changes have corresponding project review evidence where required.

---

## 95. Template gold example

A template project may include an illustrative file only when clearly marked as a template asset.

Example filename:

```text
example.gold.template
```

It must not be registered as an active scenario gold.

Example content:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: example
# normalization_version: 1.0
--- BEGIN example-section ---
<replace with reviewed expected normalized output>
--- END example-section ---
```

An initialized project should remove or rename the example according to its actual scenario inventory.

---

## 96. Initialized-project completion checklist

```text
[ ] Project owner filled
[ ] Real scenario registry added
[ ] Example placeholder rows removed
[ ] Required gold files created
[ ] Every gold header valid
[ ] Every filename matches scenario ID
[ ] Every normalization version current
[ ] Every section declared
[ ] Every gold reviewed
[ ] Every required gold version-controlled
[ ] Coverage matrix updated
[ ] Interfile contract updated
[ ] Focused scenarios pass
[ ] Checkpoints pass
[ ] Release passes
[ ] No unresolved required placeholder remains
```

---

## 97. Related documents

```text
project/README.md
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/DECISION_LOG.md
project/docs/RELEASE_CRITERIA.md
project/validation/README.md
project/validation/scenarios/README.md
project/validation/inputs/README.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/reference/SCHEMA_INDEX.md
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
```

---

## 98. Quick reference

Canonical gold:

```text
path:
  project/validation/gold/<scenario-id>.gold

encoding:
  UTF-8 without BOM

newlines:
  LF

schema:
  gf-wordbench.scenario-gold/1.0

header:
  # GF_WORDBENCH_GOLD 1.0
  # scenario_id: <scenario-id>
  # normalization_version: <version>

sections:
  --- BEGIN <section-id> ---
  <expected normalized GF output>
  --- END <section-id> ---

comparison:
  exact after canonical normalization

normal validation:
  read-only

update:
  explicit, reviewed, diffed, atomic

missing required gold:
  failure

release mismatch:
  failure
```

---

## 99. Final gold contract

The ownership chain is:

```text
project requirement
    defines the behavior to prove

native .gfs scenario
    executes the behavior through GF

raw evidence
    preserves what GF actually produced

normalization contract
    removes only documented nonsemantic instability

scenario-output artifact
    records the current normalized result

.gold file
    records reviewed accepted normalized behavior

gold comparator
    evaluates exact compatibility

checkpoint and release validation
    decide whether the project contract passes
```

The governing invariant is:

> Gold files are versioned, reviewed, read-only project contracts during normal execution; they may change only through an explicit, diffed, validated, and attributable acceptance decision.
