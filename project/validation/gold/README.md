# Project Validation Gold Files

This directory contains the active project's reviewed golden expectations for deterministic GF scenarios.

A `.gold` file is the approved normalized output for one registered scenario variant. GF Wordbench compares the current normalized scenario output with the corresponding gold to detect unintended behavioral changes.

```text
project/validation/scenarios/<scenario-id>.gfs
        ↓ GF execution
run_<run-id>/raw/scenarios/<scenario-id>.stdout.txt
run_<run-id>/raw/scenarios/<scenario-id>.stderr.txt
        ↓ marker validation and normalization
run_<run-id>/raw/scenarios/<scenario-id>.out
        ↓ exact canonical comparison
project/validation/gold/<scenario-id>.gold
```

Gold files are project-maintained inputs.

They are not generated run artifacts, compiler caches, or disposable snapshots.

---

## 1. Directory contract

Canonical directory:

```text
project/validation/gold/
```

This directory may contain:

```text
README.md
<scenario-id>.gold
<scenario-id>.<variant-id>.gold
```

It must not contain:

```text
raw GF stdout
raw GF stderr
current normalized .out files
temporary editor files
backup copies
generated .gfo files
generated .pgf files
run reports
unreviewed proposed output
```

Historical gold content belongs in version control, not in backup files beside the active gold.

Examples of prohibited backup names:

```text
parse.gold.bak
parse.old.gold
parse - Copy.gold
linearize.final2.gold
```

---

## 2. Ownership

Gold files are owned by the active project maintainers.

GF Wordbench may:

- read them;
- validate their schema;
- compare normalized output against them;
- calculate hashes;
- create review diffs;
- report mismatches.

Normal validation must not rewrite them.

The only normal write-capable workflow is an explicit reviewed gold update.

```text
gf-wordbench gold update <scenario-id>
```

Exact command availability and options are defined by the CLI reference.

---

## 3. Gold meaning

A gold file means:

> For this registered scenario, scenario variant, and normalization version, this exact canonical output is currently accepted by the project.

A gold file does not mean:

- every line produced by GF is stable;
- the raw GF transcript is irrelevant;
- the current implementation is automatically correct;
- a new output should be accepted because it is current;
- a compiler upgrade is harmless;
- all linguistic behavior is covered;
- the scenario passed merely because GF exited with code zero.

Gold acceptance requires reviewed behavior and successful scenario completion.

---

## 4. Required registration

Every gold file must belong to exactly one registered scenario variant.

The authoritative mapping is defined through:

```text
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Required invariants:

- scenario IDs are unique;
- required and optional scenario IDs do not overlap;
- every registered gold path remains beneath this directory;
- one scenario variant maps to at most one authoritative gold;
- one gold maps to exactly one scenario variant;
- every required gold-backed scenario has an existing gold;
- unregistered gold files do not count as validation evidence;
- scenario and gold IDs agree;
- scenario and gold normalization versions agree.

A gold file with no registered scenario is orphaned and must be removed, registered, or archived outside the active project.

---

## 5. Naming

Standard filename:

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
agreement-basic.gold
```

Variant filename:

```text
<scenario-id>.<variant-id>.gold
```

Examples:

```text
parse.strict.gold
linearize.gf-3.12.gold
morphology.windows.gold
```

Recommended identifier pattern:

```text
^[a-z][a-z0-9-]*$
```

Names should describe validated behavior, not editing history.

---

## 6. Canonical format

Each gold uses the canonical text schema:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: linearize
# normalization_version: 1.0
--- BEGIN basic-sentences ---
<reviewed normalized output>
--- END basic-sentences ---
```

Required properties:

```text
encoding: UTF-8 without BOM
canonical newline: LF
final newline: required
schema header: first line
scenario_id: required
normalization_version: required
section markers: balanced and unique
```

Readers may accept CRLF and canonicalize it to LF before comparison.

Canonical writers use LF.

---

## 7. Header

Required first line:

```text
# GF_WORDBENCH_GOLD 1.0
```

Required metadata:

```text
# scenario_id: <scenario-id>
# normalization_version: <version>
```

Optional metadata may include:

```text
# variant_id: <variant-id>
# gf_compatibility: <version-policy>
# platform_profile: <profile-or-none>
# reviewed_revision: <source-revision>
```

Optional metadata must be documented before it influences comparison behavior.

Metadata belongs before the first output section.

---

## 8. Sections

Canonical section markers:

```text
--- BEGIN <section-id> ---
--- END <section-id> ---
```

Section identifier recommendation:

```text
^[a-z][a-z0-9-]*$
```

Section rules:

- every `BEGIN` has one matching `END`;
- section IDs are unique within the file;
- sections do not overlap;
- section order is deterministic;
- required sections must be present;
- an absent section is not equivalent to an empty section;
- an empty section is valid only when the scenario contract gives it meaning;
- marker spelling and capitalization are stable;
- marker lines remain visible after normalization.

Example zero-missing expectation:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: missing
# normalization_version: 1.0
--- BEGIN missing-functions ---
--- END missing-functions ---
```

Here the empty section must be documented as:

```text
no missing functions
```

---

## 9. Raw, normalized, and gold output

These three outputs have different purposes.

### Raw output

Raw scenario evidence preserves exactly what the GF process produced.

Examples:

```text
run_<run-id>/raw/scenarios/<scenario-id>.stdout.txt
run_<run-id>/raw/scenarios/<scenario-id>.stderr.txt
```

Raw files may contain:

- GF banners;
- prompts;
- diagnostics;
- absolute paths;
- timing output;
- incomplete sections;
- unexpected text.

Raw evidence is never rewritten by the gold comparator.

### Normalized output

Normalized output removes only documented unstable noise.

Canonical example:

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

### Gold output

Gold contains the reviewed expected canonical output.

Canonical example:

```text
project/validation/gold/<scenario-id>.gold
```

The comparator must use the exact normalized `.out` produced by the scenario result.

It must not compare a report excerpt or reconstructed output.

---

## 10. Normalization

Normalization must stabilize irrelevant differences without hiding meaningful behavior.

Allowed examples may include:

- CRLF to LF;
- trailing-space removal;
- known GF prompt removal;
- absolute run-directory replacement;
- temporary-directory replacement;
- documented timestamp replacement;
- documented duration replacement;
- path-separator normalization;
- removal of a version banner when the scenario is version-independent.

Stable replacement-token examples:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

Normalization is profile-based and versioned.

Every gold-backed scenario must identify:

```text
normalization profile
normalization version
```

---

## 11. Forbidden normalization

Normalization must not erase or alter:

- abstract trees;
- linearized strings;
- parse alternatives;
- ambiguity counts;
- missing-function lists;
- morphology results;
- meaningful punctuation;
- meaningful whitespace;
- language-significant Unicode;
- relevant case distinctions;
- relevant source locations;
- required marker evidence;
- meaningful duplicates;
- meaningful ordering;
- fatal diagnostics relevant to the scenario.

Unsafe broad rules include:

```text
remove every warning line
remove every line containing a path
sort every output line
remove duplicate lines
ignore all whitespace
convert all Unicode to ASCII
strip all punctuation
```

A normalization change that modifies canonical output requires versioning and review of every affected gold.

---

## 12. Exact comparison

Comparison is exact after:

1. schema validation;
2. required metadata validation;
3. canonical newline handling;
4. documented normalization.

Conceptually:

```text
current canonical body == reviewed gold canonical body
```

Whitespace is significant after normalization.

Section order is significant unless a normalization profile explicitly defines a section as an unordered semantic set.

The comparator must not apply undocumented cleanup after normalization.

---

## 13. Comparison outcomes

### Match

```text
comparison_status = match
gold_match = true
validation contribution = OK
```

### Mismatch

```text
comparison_status = mismatch
gold_match = false
validation contribution = FAIL
diagnostic = GOLD_MISMATCH
```

### Comparison error

Examples:

- gold missing;
- invalid schema;
- wrong scenario ID;
- wrong normalization version;
- duplicate section;
- missing marker;
- unreadable file;
- normalization failure.

Result:

```text
comparison_status = schema_error or comparison_error
gold_match = null
validation contribution = ERROR
```

### Skipped

Allowed only when comparison is not applicable or the optional scenario was not selected.

A required gold-backed scenario must not be skipped in release mode.

---

## 14. Mismatch diffs

A mismatch should produce a unified diff.

Canonical run path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.gold.diff
```

A useful diff must:

- identify expected and current paths;
- preserve Unicode;
- use stable relative labels;
- include context;
- avoid terminal color codes in the persisted file;
- link back to raw and normalized evidence.

The diff is review support.

The structured comparison result remains authoritative.

---

## 15. Initial gold creation

A missing required gold is not a first-run success.

It is a configuration/comparison error until a reviewed gold is created explicitly.

Creation workflow:

```text
1. write and review the .gfs scenario
2. run the scenario without accepting output
3. inspect raw stdout
4. inspect raw stderr
5. validate required markers and assertions
6. inspect normalized output
7. verify linguistic and structural behavior
8. create the gold through the explicit update command
9. validate the written gold schema
10. rerun comparison
11. commit scenario, gold, and documentation together
```

A command must not create a missing gold and report the same validation run as passed.

---

## 16. Updating a gold

A gold update is valid only when the new behavior is understood and accepted.

Valid reasons include:

- intentional linguistic correction;
- approved architecture change;
- intentionally expanded scenario;
- accepted GF/RGL migration;
- deliberate normalization-contract change.

Invalid reasons include:

- the test failed and the cause is unknown;
- copying current output is faster than investigation;
- a diagnostic should be hidden;
- unstable output was not normalized correctly;
- a required section did not execute;
- a dependency changed unintentionally;
- the implementation is incomplete.

---

## 17. Review before update

Before updating a gold, inspect:

```text
old gold
new raw stdout
new raw stderr
new normalized output
full diff
source changes
scenario changes
GF version
RGL identity
normalization version
```

Confirm:

- the scenario purpose still holds;
- required markers completed;
- no fatal diagnostic was hidden;
- new output is linguistically intended;
- structural changes are understood;
- normalization preserved semantic evidence;
- affected contracts and docs are updated;
- the change is covered by the decision log when significant.

---

## 18. Atomic update

The gold updater must:

1. write a temporary sibling file;
2. validate the temporary gold;
3. flush and close it;
4. atomically replace the target;
5. preserve the previous file if validation fails;
6. record old and new SHA-256 values;
7. rerun comparison.

Normal scenario execution and release validation remain read-only for this directory.

---

## 19. Update command

Recommended workflow:

```text
gf-wordbench gold update <scenario-id> --dry-run
gf-wordbench gold update <scenario-id>
gf-wordbench gold check <scenario-id>
```

`--dry-run` must not modify the gold.

A bulk update, when supported, must remain explicit and preserve per-scenario review evidence.

---

## 20. Release behavior

Required gold-backed scenarios participate in the golden regression release gate.

For each required comparison:

- scenario exists;
- scenario executes;
- required markers complete;
- assertions pass;
- normalization succeeds;
- gold exists;
- schemas validate;
- scenario IDs match;
- normalization versions match;
- current normalized output exactly matches gold;
- gold remains unchanged during the run.

Mismatch:

```text
release decision = NOT_READY
```

Comparison error:

```text
release decision = ERROR
```

Required skip:

```text
release decision != READY
```

---

## 21. Checkpoint and quick behavior

### Quick

Quick mode may execute a small selected gold-backed smoke scenario.

A selected mismatch fails the quick validation scope.

Quick mode does not prove full release readiness.

### Checkpoint

Checkpoint mode runs gold scenarios associated with the selected checkpoint.

A required checkpoint gold mismatch fails that checkpoint.

### Diagnostic

Diagnostic mode may run broader comparisons and preserve expanded diffs.

Diagnostic mode must not update gold automatically.

---

## 22. Toolchain changes

A GF or RGL change may alter scenario output.

Classify the difference before updating gold.

### Irrelevant presentation change

Examples:

- prompt format;
- banner wording;
- temporary path;
- duration.

Preferred action:

- update safe normalization;
- change normalization version when canonical output changes;
- review affected golds.

### Meaningful behavior change

Examples:

- different parse tree;
- changed linearization;
- changed ambiguity;
- changed morphology;
- changed missing-function result.

Required action:

- investigate source and toolchain;
- determine intended project behavior;
- update source or deliberately accept the behavior;
- update project documentation and decision records;
- review gold explicitly.

---

## 23. Version- and platform-specific golds

Use a single gold whenever semantic expectations are identical.

Version-specific or platform-specific golds are a last resort.

Examples:

```text
linearize.gf-3.11.gold
linearize.gf-3.12.gold
morphology.windows.gold
morphology.posix.gold
```

Such variants require:

- explicit project registration;
- documented selection;
- verified legitimate differences;
- maintenance justification;
- release-policy coverage.

Platform-specific linguistic differences are suspicious and should be investigated.

Path separators and line endings belong in normalization, not linguistic variants.

---

## 24. Determinism

A gold-backed scenario must be deterministic enough for review.

Release comparison uses:

- fixed scenario script;
- fixed inputs;
- deterministic command order;
- explicit GF path;
- recorded GF/RGL toolchain;
- bounded operations;
- stable normalization profile.

Random generation must not use exact gold comparison unless a stable seed and ordering contract are proven.

Otherwise use explicit assertions such as:

```text
generation completed
result count within bounds
required constructor appeared
all results linearized
```

---

## 25. Scenario design

A useful gold scenario is:

- focused;
- deterministic;
- bounded;
- representative;
- readable;
- sensitive to meaningful changes;
- insensitive to irrelevant environment noise.

Prefer several coherent scenarios:

```text
linearize-basic.gfs
linearize-agreement.gfs
linearize-negation.gfs
```

over one unreviewable transcript:

```text
everything.gfs
```

Each output section should have a stable case identity.

---

## 26. Appropriate gold content

Good candidates:

- representative abstract trees;
- representative linearizations;
- expected parse alternatives;
- ambiguity information;
- morphology paradigms;
- missing-function inventory;
- bounded stable introspection;
- round-trip evidence with explicit interpretation.

Use assertions instead when only one scalar condition matters:

```text
parse count > 0
missing count == 0
PGF exists
scenario completed before timeout
specific constructor appears
```

A scenario may combine assertions and a gold.

---

## 27. Security and trust

Gold files must not contain:

- passwords;
- tokens;
- private keys;
- confidential filesystem content;
- unrelated personal information;
- complete environment dumps.

Gold paths must remain under:

```text
project/validation/gold/
```

Readers must enforce reasonable size limits without silently truncating comparison input.

Gold files are project input.

They must never contain commands intended for execution.

---

## 28. Version control

Required project golds should be committed to version control.

A gold-changing commit should include the source, scenario, input, normalization, or policy change that explains it.

Review the complete diff.

Do not commit:

```text
current .out files as gold automatically
temporary updater files
backup copies
raw logs
terminal transcripts
unregistered proposals
```

---

## 29. Orphan and drift checks

Project checks should detect:

- gold with no registered scenario;
- required scenario with no gold or assertion strategy;
- duplicate gold ownership;
- wrong scenario ID;
- wrong normalization version;
- invalid encoding;
- missing final newline;
- unmatched marker;
- duplicate section;
- stale language/module suffix;
- unregistered variant;
- gold outside the gold root;
- gold changed without validation-spec review;
- backup/copy file in the directory.

Resolve drift by:

1. restoring the existing mapping; or
2. changing the scenario-to-gold contract deliberately.

---

## 30. Reporting

Each gold-backed `ScenarioResult` should identify:

```text
scenario_id
gold_path
gold_match
comparison_status
normalization_profile
normalization_version
normalized_output_path
diff_path
gold_sha256
normalized_output_sha256
primary_message
```

Reports should state clearly:

- whether the scenario executed;
- whether comparison applied;
- whether output matched;
- where the raw evidence is;
- where the diff is;
- that the gold was not modified.

---

## 31. Manifest relationship

Project golds are source-controlled project inputs.

They are not normally copied into the run artifact manifest.

The run result should record:

```text
project-relative gold path
gold SHA-256
```

The manifest should include generated run artifacts such as:

```text
scenario stdout
scenario stderr
normalized .out
gold diff on mismatch
```

The comparator should verify that the gold did not change during release finalization.

---

## 32. Common diagnostics

Recommended stable codes:

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

A mismatch is `FAIL`.

An unreadable or invalid gold is `ERROR`.

---

## 33. Examples

### Linearization

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: linearize
# normalization_version: 1.0
--- BEGIN basic-declaratives ---
PredVP (UsePron i_Pron) (UseV sleep_V)
I sleep.
--- END basic-declaratives ---
```

The actual project must use trees and strings appropriate to its active language and grammar.

### Missing functions

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: missing
# normalization_version: 1.0
--- BEGIN missing-functions ---
--- END missing-functions ---
```

This empty section is valid only when documented as a zero-missing expectation.

### Morphology

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

The ellipses above are explanatory README examples, not acceptable active gold content.

---

## 34. Review checklist

Before creating or updating a gold:

```text
[ ] Scenario is registered
[ ] Scenario purpose is documented
[ ] Scenario entrypoint is correct
[ ] Scenario inputs are reviewed
[ ] Required markers complete
[ ] Assertions pass
[ ] Raw stdout reviewed
[ ] Raw stderr reviewed
[ ] No fatal diagnostic hidden
[ ] Normalization profile is correct
[ ] Normalization version is correct
[ ] Normalized output reviewed
[ ] Full diff reviewed
[ ] Linguistic changes understood
[ ] Structural changes understood
[ ] GF/RGL changes considered
[ ] Project contracts updated
[ ] Validation specification updated
[ ] Decision log updated when significant
[ ] Gold schema validates
[ ] Update is atomic
[ ] Follow-up comparison matches
```

---

## 35. Directory checklist

```text
[ ] Only registered .gold files and README.md are present
[ ] Filenames use scenario IDs
[ ] No backup/copy/temp files exist
[ ] Every required scenario has expected coverage
[ ] Every gold uses UTF-8 without BOM
[ ] Every gold has a final newline
[ ] Every schema header is supported
[ ] Every scenario_id matches registration
[ ] Every normalization version matches
[ ] Every section is balanced and unique
[ ] No secret or environment dump is present
[ ] Normal validation cannot write this directory
```

---

## 36. Related project files

Scenario registry and release requirements:

```text
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/RELEASE_CRITERIA.md
```

Contract and change ownership:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/DECISION_LOG.md
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
```

Scenario assets:

```text
project/validation/scenarios/
project/validation/inputs/
```

Framework specifications:

```text
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/RELEASE_GATES.md
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 37. Final rule

A gold is not accepted because it is the newest output.

A gold is accepted because the scenario completed, the normalized behavior was reviewed, and the project deliberately approved it.

> Normal validation may read, validate, hash, and compare gold files. It must never rewrite them.

Every gold change must be explicit, atomic, reviewable, version-controlled, and connected to an intentional source, scenario, toolchain, or normalization change.
