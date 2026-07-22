# GF Wordbench — Golden Tests

**Document ID:** `GF-WB-GOLDEN-TESTS`  
**Status:** Final normative specification  
**Applies to:** GF scenario regression testing, normalized outputs, reviewed expectations, checkpoint validation, and release validation  
**Owner:** GF Wordbench maintainers and the active project maintainers  
**Golden-test policy version:** `1.0.0`  
**Normative counterparts:**
- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md`
- `docs/scenarios/OUTPUT_NORMALIZATION.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`
- `docs/validation/SCENARIO_VALIDATION.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

**Document version:** `1.0.0`

---

## 1. Purpose

Golden tests detect unintended changes in stable GF behavior.

A golden test compares:

```text
current normalized scenario output
```

with:

```text
reviewed expected output
```

stored in a `.gold` file.

Golden tests are useful when the expected result is naturally textual or structured as stable text, including:

- abstract trees;
- linearizations;
- parse results;
- ambiguity information;
- morphology tables;
- missing-linearization inventories;
- selected grammar introspection;
- deterministic command transcripts;
- stable scenario markers and assertions.

Golden tests do not replace GF compilation, explicit assertions, or linguistic review.

> A gold file is approved evidence of expected behavior, not a mechanism for hiding a changed result.

---

## 2. Core model

A golden test has six distinct artifacts or stages.

```text
scenario definition
→ raw GF execution evidence
→ extracted scenario sections
→ normalized current output
→ reviewed gold output
→ comparison result
```

These stages MUST remain separate.

### 2.1 Scenario definition

A `.gfs` file defines what GF must execute.

Canonical location:

```text
project/validation/scenarios/<scenario-id>.gfs
```

### 2.2 Raw GF evidence

The scenario runner preserves the exact process output.

Canonical examples:

```text
run_<run-id>/raw/scenarios/<scenario-id>.stdout.txt
run_<run-id>/raw/scenarios/<scenario-id>.stderr.txt
```

Raw evidence is immutable after capture.

### 2.3 Extracted scenario sections

Required marker-delimited output is identified and validated.

Marker validation proves that expected scenario portions actually ran.

### 2.4 Normalized current output

The normalizer removes only documented unstable noise.

Canonical path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

### 2.5 Gold output

The project stores the reviewed expected output.

Canonical path:

```text
project/validation/gold/<scenario-id>.gold
```

### 2.6 Comparison result

The comparator records:

```text
match
mismatch
not_compared
comparison_error
```

The comparison result is part of `ScenarioResult`.

---

## 3. Authority boundaries

### 3.1 GF authority

GF is authoritative for:

- parsing;
- linearization;
- generation;
- morphology;
- grammar loading;
- grammar introspection;
- GF diagnostics;
- the raw textual results of GF commands.

### 3.2 Scenario authority

The `.gfs` scenario is authoritative for:

- commands to execute;
- target grammar or entrypoint;
- selected test cases;
- marker placement;
- scenario-specific assertions;
- intended output sections.

### 3.3 Normalizer authority

The normalizer is authoritative only for documented stability transformations.

It is not allowed to reinterpret linguistic output.

### 3.4 Gold authority

The `.gold` file is the project's reviewed expectation for one scenario variant and one normalization version.

### 3.5 Comparator authority

The comparator determines equality between canonical current output and canonical expected output.

### 3.6 Maintainer authority

Maintainers decide whether an intentional behavior change should update a gold file.

GF Wordbench MUST NOT make that decision automatically.

---

## 4. When to use golden tests

Golden tests SHOULD be used when:

- output is deterministic after approved normalization;
- the complete expected result is easier to review as a file;
- changes to output are release-significant;
- an explicit scalar assertion would lose important detail;
- multiple related outputs form one coherent snapshot;
- historical regression detection is valuable.

Typical use cases:

```text
representative tree linearizations
representative phrase parses
missing-function inventories
morphology tables
bounded introspection output
stable dependency or operation listings
```

---

## 5. When not to use golden tests

Golden tests SHOULD NOT be the primary test mechanism when:

- output is intentionally random;
- output order is not stable and not semantically ordered;
- the expected output is extremely large;
- only one boolean or numeric condition matters;
- platform-specific differences cannot be normalized safely;
- the test depends on timestamps, durations, or temporary paths;
- accepting the entire output would make review meaningless;
- output contains secrets or private data;
- the scenario's purpose is better expressed as an explicit assertion.

Examples better handled by assertions:

```text
parse count must be greater than zero
missing-function count must equal zero
PGF file must exist
scenario must finish before timeout
specific constructor must appear
```

A scenario MAY combine explicit assertions with a gold comparison.

---

## 6. Golden-test categories

GF Wordbench recognizes the following categories.

### 6.1 Exact linguistic snapshot

Captures linguistically meaningful output exactly.

Examples:

- linearized strings;
- parse trees;
- morphology forms.

Normalization must be minimal.

### 6.2 Structural snapshot

Captures stable grammar structure.

Examples:

- missing-function list;
- selected public operations;
- module or dependency inventory.

### 6.3 Diagnostic snapshot

Captures a deliberately stable diagnostic case.

Use sparingly because diagnostic wording may change between GF versions.

### 6.4 Cross-operation snapshot

Captures related operations in one scenario.

Example:

```text
input phrase
parsed tree
linearized output
round-trip result
```

### 6.5 Platform-profiled snapshot

Used only when unavoidable platform differences are meaningful and documented.

Example paths:

```text
project/validation/gold/<scenario-id>.windows.gold
project/validation/gold/<scenario-id>.posix.gold
```

Platform-profiled golds require explicit project configuration.

### 6.6 Version-profiled snapshot

Used only when supported GF versions legitimately produce different accepted output.

Example:

```text
project/validation/gold/<scenario-id>.gf-3.11.gold
project/validation/gold/<scenario-id>.gf-3.12.gold
```

Version-profiled golds are a last resort.

A normalizer or compatibility adapter should be preferred when the difference is irrelevant noise.

A single gold should be preferred when the semantic expectation is identical.

---

## 7. Scenario-to-gold registry

Every gold file MUST belong to exactly one registered scenario variant.

The active project owns the registry through:

```text
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Recommended future canonical configuration:

```toml
[[validation.scenarios]]
id = "linearize"
script = "validation/scenarios/linearize.gfs"
required = true
modes = ["checkpoint", "release"]
gold = "validation/gold/linearize.gold"
normalization_profile = "gf-text-v1"
```

Until this structured table is adopted through a schema revision, the equivalent mapping must be explicit in project documentation and existing scenario lists.

### 7.1 Registry invariants

- scenario IDs are unique;
- gold paths are project-relative;
- one scenario variant maps to at most one authoritative gold;
- one gold maps to exactly one scenario variant;
- required gold-backed scenarios must have an existing gold;
- unregistered gold files do not count as validation evidence;
- scenario and gold filenames SHOULD share the scenario ID;
- a scenario rename requires coordinated gold migration.

---

## 8. Canonical gold location and naming

### 8.1 Root directory

```text
project/validation/gold/
```

### 8.2 Standard name

```text
<scenario-id>.gold
```

Examples:

```text
load.gold
linearize.gold
parse.gold
missing.gold
morphology-nouns.gold
```

### 8.3 Variant name

When variants are explicitly required:

```text
<scenario-id>.<variant-id>.gold
```

Examples:

```text
parse.strict.gold
linearize.gf-3.12.gold
morphology.windows.gold
```

### 8.4 Identifier rules

Scenario and variant IDs SHOULD use:

```text
lowercase ASCII
digits
hyphens
```

Recommended pattern:

```text
^[a-z][a-z0-9-]*$
```

### 8.5 Prohibited names

Avoid:

```text
new.gold
final.gold
final2.gold
working.gold
expected-new.gold
copy.gold
```

Gold filenames must identify behavior, not editing history.

---

## 9. Canonical gold format

The persisted-schema lock defines the canonical text schema.

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: linearize
# normalization_version: 1.0
--- BEGIN basic-sentences ---
<expected normalized output>
--- END basic-sentences ---
```

### 9.1 Encoding

```text
UTF-8 without BOM
```

### 9.2 Newlines

Canonical writers use:

```text
LF
```

Readers accept LF and CRLF, but comparison occurs after CRLF-to-LF normalization.

### 9.3 Final newline

A final newline is required.

### 9.4 Header order

Canonical order:

```text
schema header
scenario_id
normalization_version
optional metadata
section content
```

### 9.5 Header identity

Required first line:

```text
# GF_WORDBENCH_GOLD 1.0
```

### 9.6 Required metadata

```text
scenario_id
normalization_version
```

### 9.7 Optional metadata

Permitted examples:

```text
# variant_id: strict
# gf_compatibility: 3.12.x
# platform_profile: none
# reviewed_revision: <revision>
```

Optional metadata must not become an undocumented comparison dependency.

### 9.8 Comments inside content

Lines beginning with `#` inside output sections are data unless a documented parser rule treats them as metadata.

To avoid ambiguity, metadata belongs before the first `BEGIN` marker.

---

## 10. Canonical normalized-output format

Current normalized output uses:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: linearize
# normalization_version: 1.0
--- BEGIN basic-sentences ---
<normalized current output>
--- END basic-sentences ---
```

The gold and current output headers differ by identity:

```text
GF_WORDBENCH_GOLD
GF_WORDBENCH_OUTPUT
```

The comparator compares their semantic canonical bodies and required metadata according to the comparison contract.

It MUST NOT fail solely because the schema identity word differs as designed.

---

## 11. Section model

Golden content is divided into stable marker-delimited sections.

Canonical markers:

```text
--- BEGIN <section-id> ---
--- END <section-id> ---
```

### 11.1 Section identifiers

Recommended pattern:

```text
^[a-z][a-z0-9-]*$
```

### 11.2 Section invariants

- every begin marker has exactly one matching end marker;
- section IDs are unique within a scenario output;
- sections do not overlap;
- section order is stable and meaningful;
- missing required sections cause scenario failure or error;
- an empty section is valid only when the scenario contract permits it;
- marker text is not localized;
- normalization preserves marker identity.

### 11.3 Section selection

The scenario contract defines which sections are:

```text
required
optional
diagnostic_only
excluded_from_gold
```

Excluded diagnostic material remains available in raw evidence.

### 11.4 Partial comparison

Partial comparison is allowed only through declared sections.

The comparator MUST NOT arbitrarily select lines from an undeclared full transcript.

---

## 12. Raw output and normalization

Raw evidence and comparison material have different purposes.

### 12.1 Raw evidence

Raw evidence preserves:

- GF prompts;
- banners;
- stdout;
- stderr;
- diagnostics;
- paths;
- timing-related output;
- unexpected text;
- incomplete markers.

### 12.2 Normalized output

Normalized output preserves stable semantic material while removing only approved instability.

### 12.3 Required rule

> Normalization must make irrelevant differences stable without making meaningful differences invisible.

---

## 13. Allowed normalization

The normalizer MAY perform documented transformations such as:

- CRLF to LF;
- removal of trailing spaces;
- removal of known GF prompts;
- normalization of stable marker spacing;
- replacement of absolute run-directory prefixes;
- replacement of temporary-directory prefixes;
- replacement of declared unstable timestamps;
- replacement of measured durations;
- normalization of platform path separators;
- removal of documented version banners for version-independent scenarios;
- deterministic ordering of a set-like section when the scenario contract explicitly declares order irrelevant.

### 13.1 Stable replacement tokens

Allowed examples:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

### 13.2 Ordered-data warning

Sorting is prohibited by default.

A section may be sorted only when:

- it represents a semantic set;
- the scenario contract declares order irrelevant;
- the sorting key is documented;
- tests prove duplicates and distinctions are preserved.

---

## 14. Forbidden normalization

The normalizer MUST NOT remove or change:

- GF error messages relevant to the scenario;
- source filenames relevant to diagnosis;
- line and column locations unless the scenario explicitly excludes them;
- abstract trees;
- linearized strings;
- ambiguity counts;
- parse alternatives;
- missing-function lists;
- morphology results;
- semantically meaningful punctuation;
- meaningful whitespace;
- Unicode distinctions relevant to the language;
- case distinctions relevant to the language;
- section markers;
- evidence that a required section did not execute;
- duplicate outputs when duplicates are meaningful;
- lexical ordering when order is part of the expected behavior.

### 14.1 Prohibited broad filters

Examples of unsafe normalizers:

```text
remove every line containing "warning"
remove every line containing a path
sort every output line
strip all punctuation
convert all Unicode to ASCII
remove duplicate lines
ignore all whitespace
```

---

## 15. Normalization profiles

Every gold-backed scenario uses one named normalization profile.

Recommended identifiers:

```text
gf-text-v1
gf-diagnostic-v1
gf-missing-v1
gf-morphology-v1
gf-parse-v1
```

### 15.1 Profile contents

A profile defines:

```text
profile ID
normalization version
allowed transformations
section policy
replacement tokens
ordering policy
whitespace policy
header policy
tests
```

### 15.2 Single owner

Recommended implementation owner:

```text
app/scenarios/normalization.py
```

or:

```text
app/audit/normalization.py
```

Exactly one module should own profile resolution.

### 15.3 Versioning

A normalization profile has a version independent of:

- GF Wordbench package version;
- project version;
- GF core version;
- gold schema version.

### 15.4 Breaking normalization change

A change is breaking when it changes canonical output for existing evidence.

Required coordinated updates:

1. normalizer;
2. profile version;
3. unit tests;
4. scenario-output schema if affected;
5. gold review;
6. migration note;
7. project validation specification;
8. affected gold files;
9. this document.

---

## 16. Comparison contract

### 16.1 Preconditions

Comparison starts only when:

- scenario execution reached a comparable state;
- required markers are complete;
- normalized current output exists;
- gold file exists;
- both schemas are valid;
- scenario IDs match;
- normalization versions match or a documented migration applies.

### 16.2 Canonical comparison

Comparison is exact after canonical parsing and permitted newline normalization.

Conceptually:

```python
current.canonical_body == gold.canonical_body
```

### 16.3 Whitespace

Whitespace is significant after normalization.

The comparator MUST NOT apply a second undocumented whitespace cleanup.

### 16.4 Section order

Section order is significant unless the normalization profile explicitly canonicalizes a set-like section.

### 16.5 Metadata comparison

Required metadata must be compatible.

At minimum:

```text
scenario_id equal
normalization_version equal
variant identity equal when present
```

### 16.6 Match result

```text
gold_match = true
status contribution = OK
```

### 16.7 Mismatch result

```text
gold_match = false
status contribution = FAIL
diagnostic kind = gold_mismatch
```

### 16.8 Comparison error

Examples:

- invalid gold schema;
- invalid normalized-output schema;
- unreadable file;
- normalization version mismatch;
- scenario ID mismatch;
- duplicate section ID;
- missing required marker.

Result:

```text
status contribution = ERROR
gold_match = null
diagnostic kind = comparison_error or schema_error
```

---

## 17. Status semantics

A gold comparison uses the canonical validation status model.

### 17.1 `OK`

- scenario succeeded;
- comparison was applicable;
- gold and current output matched.

### 17.2 `FAIL`

- comparison ran correctly;
- output differed from reviewed expectation.

### 17.3 `ERROR`

- comparison could not be performed reliably;
- required files or metadata were invalid;
- normalization failed;
- required scenario sections were incomplete.

### 17.4 `SKIPPED`

Allowed only when:

- the scenario is optional and not selected;
- the scenario has no gold by design;
- the gate is not applicable.

A required gold-backed scenario MUST NOT be skipped in release mode.

---

## 18. Scenario result fields

Recommended `ScenarioResult` fields:

```python
scenario_id: str
script_path: Path
required: bool
status: str
stdout_path: Path
stderr_path: Path
normalized_output_path: Path | None
gold_path: Path | None
gold_match: bool | None
normalization_profile: str | None
normalization_version: str | None
comparison_status: str
diff_path: Path | None
primary_message: str
```

### 18.1 Separation

The scenario status and comparison status should remain distinguishable.

Example:

```text
scenario execution = OK
gold comparison = FAIL
overall scenario result = FAIL
```

### 18.2 Missing gold

For a required gold-backed scenario:

```text
scenario execution = OK
gold comparison = ERROR
overall scenario result = ERROR
```

A missing gold is not an automatic mismatch and not an automatic creation.

---

## 19. Diff artifacts

A mismatch SHOULD produce a reviewable diff.

Recommended path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.gold.diff
```

### 19.1 Diff requirements

The diff SHOULD:

- identify gold and current paths;
- use stable relative labels;
- preserve Unicode;
- show enough context;
- use line-based unified format;
- avoid terminal color codes in persisted output;
- remain derived evidence;
- reference raw and normalized source artifacts.

### 19.2 Diff is not the result source

The structured comparison result remains authoritative.

The diff is review support.

### 19.3 Large diffs

For large mismatches, reports may include a bounded excerpt while preserving the complete diff artifact.

---

## 20. Determinism requirements

A gold-backed scenario must be deterministic enough for meaningful review.

### 20.1 Deterministic inputs

Release comparison uses:

- reviewed scenario script;
- reviewed input files;
- fixed scenario command order;
- explicit GF path;
- recorded GF/RGL toolchain;
- bounded operations;
- stable normalization profile.

### 20.2 Random generation

Random generation MUST NOT be compared to an exact gold unless:

- GF exposes and the scenario fixes a stable seed;
- ordering and count are proven stable for supported versions;
- the project documents the contract.

Otherwise, use assertions such as:

```text
generation completes
count within bounds
all results linearize
required constructor appears
```

### 20.3 Unordered GF output

If GF output order is not guaranteed, the scenario should:

- avoid exact gold comparison;
- compare an explicit semantic set through a declared canonicalization;
- use assertions.

### 20.4 Time and performance output

Durations are excluded or replaced with stable tokens.

Performance thresholds belong to assertions or release gates, not exact gold text.

---

## 21. Designing useful gold scenarios

A high-quality gold scenario is:

- focused;
- deterministic;
- representative;
- reviewable;
- bounded;
- stable across irrelevant environment changes;
- sensitive to meaningful behavior changes.

### 21.1 Scope rule

Prefer several coherent scenarios over one enormous transcript.

Example:

```text
linearize-basic.gfs
linearize-agreement.gfs
linearize-negation.gfs
```

instead of:

```text
everything.gfs
```

### 21.2 Case identity

Every test case SHOULD have a stable case or section ID.

Example:

```text
--- BEGIN noun-agreement ---
...
--- END noun-agreement ---
```

### 21.3 Representative coverage

Gold scenarios should cover behavior selected in:

```text
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
```

### 21.4 Avoid implementation snapshots

Do not gold internal debug tables unless their stability is itself a contract.

Prefer public grammar behavior.

---

## 22. Initial gold creation

A gold file is created only after the scenario and its expected behavior have been reviewed.

### 22.1 Preconditions

- scenario purpose documented;
- scenario script reviewed;
- required markers validated;
- raw output reviewed;
- normalization profile reviewed;
- normalized output reviewed;
- behavior accepted;
- no unexpected diagnostics hidden;
- toolchain identity recorded.

### 22.2 Creation workflow

```text
1. run scenario without gold acceptance
2. preserve raw output
3. normalize output
4. inspect raw and normalized forms
5. verify expected linguistic behavior
6. create gold through explicit command
7. write atomically
8. run comparison again
9. commit scenario, gold, and documentation together
```

### 22.3 No bootstrap pass

When a required gold does not exist, normal validation fails or errors.

It MUST NOT create the gold and pass in the same operation.

---

## 23. Updating gold files

Gold updates are governed by a separate deliberate workflow.

Normal commands:

```text
quick
checkpoint
diagnostic
release
```

MUST NOT modify `.gold` files.

### 23.1 Valid reasons

A gold update may be valid when:

- an intentional linguistic correction changes output;
- an approved architecture change changes public behavior;
- a scenario is intentionally expanded;
- an accepted GF/RGL migration changes stable output;
- a normalization contract changes deliberately.

### 23.2 Invalid reasons

A gold update is invalid when done because:

- a test failed unexpectedly;
- review is inconvenient;
- output is not understood;
- a compiler warning should be hidden;
- an unstable scenario was designed poorly;
- a path or timestamp was not normalized correctly;
- a required section failed to run;
- the new output merely comes from an unintended dependency change.

### 23.3 Required review

Before update:

- inspect old gold;
- inspect raw new output;
- inspect normalized new output;
- inspect full diff;
- identify the source change;
- confirm scenario purpose still holds;
- confirm no semantic output was normalized away;
- document significant behavior changes.

### 23.4 Coordinated files

An update may require changes to:

```text
source modules
scenario script
scenario input
gold file
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
DECISION_LOG.md
INTERFILE_CONTRACT_LOCK.md
STATUS_LEDGER.md
normalization profile
migration notes
```

### 23.5 Atomic write

The updater MUST:

1. write a temporary sibling file;
2. validate the new gold;
3. flush and close;
4. replace atomically;
5. preserve the previous file if validation fails.

### 23.6 Explicit command

Recommended interface:

```text
gf-wordbench gold update <scenario-id>
```

Preview only:

```text
gf-wordbench gold update <scenario-id> --dry-run
```

The final CLI syntax becomes normative in the CLI reference.

---

## 24. Gold-update result

Recommended structured result:

```python
@dataclass(frozen=True, slots=True)
class GoldUpdateResult:
    scenario_id: str
    gold_path: Path
    previous_hash: str | None
    new_hash: str
    normalized_output_path: Path
    diff_path: Path | None
    status: str
    reviewed: bool
    message: str
```

### 24.1 Statuses

```text
created
updated
unchanged
rejected
error
```

### 24.2 Audit trail

The update SHOULD record:

```text
scenario ID
old hash
new hash
normalization version
toolchain identity
source revision
reason
reviewer when available
timestamp
```

This audit trail may live in version control and the project decision log rather than inside the gold file.

---

## 25. Release behavior

Golden tests are part of release gate `RG-08`.

For every required gold-backed scenario:

- scenario must run;
- markers must complete;
- normalization must succeed;
- gold must exist;
- schemas must validate;
- versions must match;
- comparison must match;
- gold must remain unmodified during the run.

Any required mismatch causes:

```text
release decision = NOT_READY
```

Any required comparison error causes:

```text
release decision = ERROR
```

A required skipped comparison also blocks release.

---

## 26. Checkpoint and quick behavior

### 26.1 Quick mode

Quick mode MAY run a small gold-backed smoke scenario.

A failed selected gold test fails quick validation.

### 26.2 Checkpoint mode

Checkpoint mode runs gold scenarios associated with the selected checkpoint.

Required checkpoint gold mismatches fail the checkpoint.

### 26.3 Diagnostic mode

Diagnostic mode may run all relevant gold comparisons and preserve expanded diffs.

Diagnostic mode still MUST NOT update gold automatically.

---

## 27. Toolchain-version changes

A new GF or RGL version may change output.

The change must be classified.

### 27.1 Irrelevant presentation difference

Examples:

- banner wording;
- prompt format;
- absolute path;
- timing output.

Action:

- update the normalizer if safely generalizable;
- increment normalization version when canonical output changes;
- review all affected golds.

### 27.2 Meaningful behavior difference

Examples:

- different parse tree;
- changed linearization;
- changed ambiguity;
- changed missing-function result;
- changed morphology form.

Action:

- investigate;
- decide whether project behavior is correct;
- update source or accept the change deliberately;
- review gold and project documentation.

### 27.3 Version-profiled gold decision

Use version-specific gold only when:

- both outputs are intentionally supported;
- normalization cannot safely unify them;
- the project explicitly supports both GF lines;
- maintenance cost is justified.

---

## 28. Platform differences

Platform differences should normally be removed by safe normalization.

Examples:

```text
path separators
temporary path prefixes
line endings
```

Platform-specific linguistic outputs are suspicious and require investigation.

A platform-profiled gold is allowed only after documenting:

- the exact difference;
- why it is legitimate;
- supported platforms;
- profile selection;
- release implications.

---

## 29. Security and trust

Gold files and scenarios are project-controlled inputs.

### 29.1 Scenario trust

A `.gfs` file may invoke GF shell behavior.

Untrusted scenarios must be reviewed before execution.

### 29.2 Shell escape prohibition

Normal project scenarios MUST NOT execute operating-system commands unless explicitly authorized by security policy.

### 29.3 Sensitive output

Gold files MUST NOT contain:

- passwords;
- tokens;
- private keys;
- personal data not required by the project;
- complete environment dumps;
- confidential filesystem content.

### 29.4 Path safety

Gold and scenario paths must remain beneath their permitted project directories.

### 29.5 Malicious gold size

Readers SHOULD enforce reasonable size limits.

A size-limit failure is explicit and must not silently truncate comparison input.

---

## 30. Storage and version control

Required project gold files SHOULD be committed to version control.

### 30.1 Commit coherence

A commit that changes a gold SHOULD include the source, scenario, input, or policy change that explains it.

### 30.2 Binary prohibition

Canonical `.gold` files are UTF-8 text.

Binary golden artifacts require another explicitly versioned artifact contract.

### 30.3 Generated current outputs

Current `.out` files belong to run directories and SHOULD NOT be committed as project golds automatically.

### 30.4 Backup copies

Files such as:

```text
parse.gold.bak
parse - Copy.gold
parse.old.gold
```

must not be treated as registered golds.

Historical versions belong in version control.

---

## 31. Orphan and drift detection

The project checker SHOULD detect:

- gold with no registered scenario;
- required scenario with no gold or assertion strategy;
- duplicate gold ownership;
- scenario ID mismatch;
- filename mismatch;
- normalization version mismatch;
- stale old-language suffix;
- gold changed without related source/scenario/policy change;
- unregistered variant;
- missing required section;
- gold file outside the gold root;
- unresolved template placeholder;
- invalid encoding;
- missing final newline.

### 31.1 Drift resolution

Resolve drift by either:

1. restoring the locked mapping; or
2. changing the scenario-to-gold contract deliberately.

---

## 32. Reporting

### 32.1 `summary.json`

Each gold-backed scenario should report:

```text
gold_path
gold_match
normalization_profile
normalization_version
comparison_status
diff_path
gold_hash
normalized_output_hash
```

Adding canonical persisted fields requires updating the persisted-schema lock.

### 32.2 `summary.md`

Should show:

```text
scenario ID
required/optional
comparison status
gold path
first mismatch summary
diff path
```

### 32.3 `AI_READY.md`

Should include:

- scenario purpose;
- current and expected artifact paths;
- concise diff excerpt;
- raw evidence paths;
- explicit statement that gold was not updated.

### 32.4 Raw logs

Raw logs remain accessible even when comparison succeeds.

---

## 33. Manifest integration

For a release run, the artifact manifest SHOULD include:

```text
normalized scenario output
gold diff when mismatch
scenario stdout
scenario stderr
```

Project gold files are source-controlled project assets, not normally copied into the run manifest as generated artifacts.

The release summary SHOULD record their hashes.

### 33.1 Required hashes

Recommended:

```text
SHA-256 of gold file
SHA-256 of normalized current output
```

### 33.2 Integrity check

The comparator SHOULD verify the gold file did not change between read and release finalization.

---

## 34. Implementation architecture

Recommended modules:

```text
app/scenarios/gold_loader.py
app/scenarios/gold_compare.py
app/scenarios/gold_update.py
app/scenarios/normalization.py
app/scenarios/models.py
```

### 34.1 Responsibilities

| Module | Responsibility |
|---|---|
| `gold_loader.py` | load and validate gold schema |
| `gold_compare.py` | canonical comparison and diff |
| `gold_update.py` | explicit reviewed update workflow |
| `normalization.py` | named normalization profiles |
| `models.py` | typed results |

### 34.2 Forbidden responsibility overlap

- scenario runner MUST NOT approve gold changes;
- report writer MUST NOT compare raw files independently;
- GUI MUST NOT implement a separate comparator;
- release engine MUST consume comparison results rather than reread prose;
- normalizer MUST NOT write gold files;
- comparator MUST NOT launch GF.

---

## 35. Recommended models

```python
@dataclass(frozen=True, slots=True)
class GoldDocument:
    schema_version: str
    scenario_id: str
    normalization_version: str
    variant_id: str | None
    sections: tuple["GoldSection", ...]
    path: Path
    sha256: str
```

```python
@dataclass(frozen=True, slots=True)
class GoldSection:
    section_id: str
    content: str
```

```python
@dataclass(frozen=True, slots=True)
class GoldComparisonResult:
    scenario_id: str
    status: str
    gold_match: bool | None
    gold_path: Path
    normalized_output_path: Path
    gold_sha256: str
    output_sha256: str
    diff_path: Path | None
    message: str
```

### 35.1 Immutability

Loaded documents and comparison results SHOULD be immutable.

### 35.2 Structured errors

Schema and comparison errors use stable diagnostic codes.

---

## 36. Diagnostic codes

Recommended codes:

```text
GOLD_FILE_MISSING
GOLD_FILE_UNREADABLE
GOLD_SCHEMA_INVALID
GOLD_SCHEMA_UNSUPPORTED
GOLD_SCENARIO_ID_MISMATCH
GOLD_VARIANT_MISMATCH
GOLD_NORMALIZATION_VERSION_MISMATCH
GOLD_DUPLICATE_SECTION
GOLD_SECTION_MISSING
GOLD_OUTPUT_SCHEMA_INVALID
GOLD_NORMALIZATION_FAILED
GOLD_MISMATCH
GOLD_DIFF_WRITE_FAILED
GOLD_CHANGED_DURING_RUN
GOLD_UPDATE_NOT_AUTHORIZED
GOLD_UPDATE_REJECTED
GOLD_PATH_OUTSIDE_ROOT
GOLD_ENCODING_INVALID
```

### 36.1 Diagnostic stability

Codes are stable contracts.

Human messages may improve without changing code meaning.

---

## 37. CLI behavior

Recommended commands:

```text
gf-wordbench gold check
gf-wordbench gold check <scenario-id>
gf-wordbench gold diff <scenario-id>
gf-wordbench gold update <scenario-id>
gf-wordbench gold update <scenario-id> --dry-run
gf-wordbench gold list
```

### 37.1 `gold check`

- validates registry;
- validates gold schemas;
- optionally runs scenarios;
- never writes gold.

### 37.2 `gold diff`

- runs or reads current normalized output;
- creates a diff;
- never updates gold.

### 37.3 `gold update`

- explicit write-capable command;
- validates scenario success;
- requires project-write permission;
- writes atomically;
- records old and new hashes.

Exact CLI syntax becomes normative in `CLI_REFERENCE.md`.

---

## 38. GUI behavior

The GUI SHOULD provide:

- gold status per scenario;
- path to current normalized output;
- path to gold;
- diff viewer;
- explicit update action separate from validation;
- strong confirmation before update;
- old/new hash display;
- reason field when project policy requires it.

The GUI MUST NOT:

- update gold on ordinary run completion;
- hide raw evidence;
- label mismatch as tool error;
- label missing gold as match;
- perform its own normalization logic.

---

## 39. CI behavior

CI validation:

```text
read-only gold policy
```

### 39.1 Required CI checks

- no gold file modified;
- required golds exist;
- schemas validate;
- comparisons pass;
- diffs published on failure;
- gold hashes recorded;
- release blocked on mismatch.

### 39.2 CI gold updates

Automatic CI gold updates are prohibited by default.

A dedicated controlled workflow MAY produce proposed gold artifacts for review, but MUST NOT merge or approve them automatically.

### 39.3 Working-tree check

CI SHOULD verify:

```text
git diff --exit-code -- project/validation/gold
```

or an equivalent repository check after validation.

---

## 40. Testing strategy

Recommended files:

```text
tests/scenarios/test_gold_loader.py
tests/scenarios/test_gold_compare.py
tests/scenarios/test_gold_update.py
tests/scenarios/test_normalization_profiles.py
tests/contracts/test_gold_contract.py
tests/integration/test_golden_scenarios.py
tests/schemas/test_gold_schema.py
```

### 40.1 Schema tests

- valid canonical gold;
- missing header;
- wrong schema identity;
- unsupported schema version;
- missing scenario ID;
- missing normalization version;
- duplicate section;
- unmatched marker;
- invalid UTF-8;
- missing final newline;
- CRLF accepted and canonicalized.

### 40.2 Comparison tests

- exact match;
- one-line mismatch;
- added section;
- removed section;
- reordered section;
- whitespace after normalization;
- significant whitespace mismatch;
- Unicode distinction;
- scenario ID mismatch;
- normalization version mismatch;
- gold missing;
- current output missing.

### 40.3 Normalization tests

- path replacement;
- CRLF conversion;
- trailing-space removal;
- prompt removal;
- timestamp token;
- duration token;
- forbidden linguistic alteration;
- duplicate preservation;
- meaningful punctuation preservation;
- marker preservation;
- deterministic output.

### 40.4 Update tests

- create new gold explicitly;
- update existing gold;
- unchanged update;
- dry run;
- atomic replacement;
- validation failure preserves old file;
- unauthorized update rejected;
- old/new hash recorded;
- normal scenario run does not write gold.

### 40.5 Integration tests

With a minimal GF fixture:

- run `.gfs`;
- capture raw streams;
- validate markers;
- normalize;
- compare;
- produce diff;
- update through explicit workflow;
- rerun and match;
- verify release mismatch behavior.

---

## 41. Example: linearization gold

Scenario intent:

```text
validate representative declarative sentence linearizations
```

Gold:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: linearize
# normalization_version: 1.0
--- BEGIN basic-declaratives ---
PredVP (UsePron i_Pron) (UseV sleep_V)
I sleep.
--- END basic-declaratives ---
```

A changed linearized string is meaningful and MUST appear in the diff.

---

## 42. Example: missing-function gold

Gold:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: missing
# normalization_version: 1.0
--- BEGIN missing-functions ---
--- END missing-functions ---
```

The empty section encodes an explicit zero-missing expectation.

The scenario contract must document that empty means:

```text
no missing functions
```

An absent section is not equivalent to an empty section.

---

## 43. Example: morphology gold

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: morphology-nouns
# normalization_version: 1.0
--- BEGIN noun-example-1 ---
Sg Nom: ...
Sg Acc: ...
Pl Nom: ...
Pl Acc: ...
--- END noun-example-1 ---
```

Paradigm ordering is significant when the project defines it.

The normalizer must not sort forms alphabetically unless the contract says order is irrelevant.

---

## 44. Example: mismatch result

```json
{
  "scenario_id": "linearize",
  "status": "FAIL",
  "gold_match": false,
  "comparison_status": "mismatch",
  "gold_path": "project/validation/gold/linearize.gold",
  "normalized_output_path": "raw/scenarios/linearize.out",
  "diff_path": "raw/scenarios/linearize.gold.diff",
  "primary_message": "Normalized output differs from reviewed gold."
}
```

---

## 45. Example: comparison error

```json
{
  "scenario_id": "parse",
  "status": "ERROR",
  "gold_match": null,
  "comparison_status": "schema_error",
  "gold_path": "project/validation/gold/parse.gold",
  "normalized_output_path": "raw/scenarios/parse.out",
  "diff_path": null,
  "primary_message": "Gold normalization version does not match current output."
}
```

---

## 46. Review checklist

Before approving a gold creation or update:

```text
[ ] Scenario purpose is documented
[ ] Scenario entrypoint is correct
[ ] Scenario markers are complete
[ ] Raw stdout reviewed
[ ] Raw stderr reviewed
[ ] No fatal diagnostic hidden
[ ] Normalization profile is correct
[ ] Normalized output reviewed
[ ] Full diff reviewed
[ ] Linguistic changes understood
[ ] Structural changes understood
[ ] Toolchain change considered
[ ] Project specification updated if needed
[ ] Contract lock updated if needed
[ ] Decision log updated if significant
[ ] Gold schema validates
[ ] Gold written atomically
[ ] Follow-up comparison passes
```

---

## 47. Anti-patterns

The following are prohibited or strongly discouraged:

- accepting output by copying it blindly into gold;
- updating every gold after a broad change without individual review;
- using one huge gold for unrelated features;
- normalizing away errors;
- storing raw terminal prompts as semantic output;
- comparing random generation exactly;
- hiding platform differences with broad line deletion;
- treating missing gold as first-run success;
- updating gold inside release mode;
- using gold to test only file existence;
- committing backup gold copies;
- allowing multiple gold owners for one scenario variant;
- comparing stdout while ignoring required stderr diagnostics;
- using a report excerpt as the current comparison source;
- modifying a gold without updating its scenario ID after rename;
- changing normalization without versioning.

---

## 48. Migration from a non-gold project

A project introducing golden tests should proceed incrementally.

### 48.1 Phase 1 — Scenario stabilization

- define scenario purpose;
- add markers;
- bound output;
- preserve raw evidence;
- use explicit assertions first.

### 48.2 Phase 2 — Normalization

- identify actual unstable noise;
- define minimal profile;
- test semantic preservation.

### 48.3 Phase 3 — Baseline creation

- review current output;
- create initial gold explicitly;
- document expected behavior.

### 48.4 Phase 4 — Gate activation

- mark scenario gold-backed;
- enable in checkpoint or release;
- add schema and integration tests.

### 48.5 No mass baseline assumption

Existing output is not automatically correct merely because it is current.

---

## 49. Change policy

A change is contract-significant when it affects:

- gold schema;
- scenario-to-gold mapping;
- scenario ID;
- variant selection;
- normalization profile;
- normalization version;
- section markers;
- comparison semantics;
- whitespace policy;
- update authorization;
- release-gate behavior;
- persisted comparison fields.

A coordinated change MUST update:

1. implementation;
2. typed models;
3. persisted schema when affected;
4. scenario documentation;
5. project validation specification;
6. active project interfile lock;
7. tests;
8. affected golds through explicit review;
9. migration notes;
10. this document.

---

## 50. Final enforcement rule

A gold file is not correct because it matches the latest output.

A gold file is correct because its expected behavior was reviewed and accepted.

> Normal validation may read gold files, validate them, compare against them, and report differences. It may never rewrite them.

Every gold change must be explicit, atomic, reviewable, and connected to an intentional project or normalization change.
