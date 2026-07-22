# ADR-0007 — Golden Output Testing

**ADR ID:** `ADR-0007`  
**Title:** Golden Output Testing  
**Status:** Accepted  
**Decision type:** Architecture and validation policy  
**Applies to:** Native GF scenarios, normalized outputs, project gold files, regression comparison and release validation  
**Owners:** GF Wordbench maintainers and active-language project maintainers  
**Decision date:** 2026-07-22  
**Last reviewed:** 2026-07-22  
**Supersedes:** None  
**Superseded by:** None

---

## 1. Decision

GF Wordbench will use reviewed golden-output files as the canonical exact-comparison mechanism for deterministic native GF scenario results.

The decision is:

```text
project scenario
    → native GF execution
    → raw stdout/stderr
    → validated markers
    → versioned normalization
    → canonical normalized output
    → reviewed project gold
    → exact comparison
    → structured scenario result
```

Golden files are project-owned expected outputs stored under:

```text
project/validation/gold/
```

Actual normalized outputs are run-owned artifacts stored under the current run directory.

Normal validation is read-only with respect to project gold files.

Gold updates require a separate explicit, reviewable operation.

---

## 2. Context

GF language validation frequently depends on outputs that are too rich to express safely as one boolean or one regular expression.

Examples include:

- abstract parse trees;
- sets or ordered lists of parses;
- linearized strings;
- morphology tables;
- missing-function inventories;
- bounded generation output;
- structured introspection;
- language-specific punctuation and Unicode;
- combinations of multiple GF commands in one scenario.

A scenario can often prove behavior only by preserving and comparing the actual GF output.

The system therefore needs a stable way to answer:

```text
Did GF produce exactly the accepted semantic output for this scenario?
```

The solution must also preserve the distinction between:

- raw evidence emitted by GF;
- normalization needed only for reproducibility;
- accepted project behavior;
- regression classification;
- framework/tool failures.

---

## 3. Problem statement

Without a formal golden-output policy, projects tend to drift toward one or more unsafe practices:

- comparing raw GF output directly even when prompts, paths or timing are unstable;
- deleting too much output through broad normalization;
- embedding expected strings in Python code;
- using ad hoc regular expressions for every scenario;
- accepting current output automatically;
- rewriting gold files during normal validation;
- losing the link between a scenario and its expected output;
- treating missing gold files as skipped tests;
- storing gold files inside generated run directories;
- mixing framework fixtures with language-project expectations;
- using old gold files with a new normalization profile without review;
- accepting output from a failed or timed-out GF process;
- relying on human-readable report prose instead of structured comparison results.

This ADR establishes one controlled model.

---

## 4. Decision drivers

The decision is driven by the following requirements.

### 4.1 Preserve native GF authority

GF must remain the execution engine.

The framework must not reimplement parsing, linearization, morphology, generation or grammar introspection.

### 4.2 Preserve raw evidence

A gold comparison must never replace raw stdout and stderr.

### 4.3 Support rich linguistic output

Expected behavior may be multiline, Unicode-rich and structurally complex.

### 4.4 Make regressions reviewable

A reviewer must be able to inspect a deterministic diff.

### 4.5 Keep expectations project-owned

Language-specific expected behavior belongs to the active project, not framework Python code.

### 4.6 Avoid silent acceptance

Current implementation output must not become accepted behavior automatically.

### 4.7 Support exact release gates

Required deterministic scenarios need a strict pass/fail comparison.

### 4.8 Support reproducibility across platforms

Known non-semantic instability must be normalized centrally and versioned.

### 4.9 Keep contracts explicit

Scenario identity, profile identity, normalization version and gold identity must remain linked.

### 4.10 Keep updates auditable

A gold change must be visible as a deliberate project change.

---

## 5. Scope of the decision

This ADR applies to exact-output validation for:

- parse scenarios;
- linearization scenarios;
- morphology scenarios;
- missing-function scenarios;
- deterministic introspection scenarios;
- deterministic bounded generation scenarios;
- release smoke scenarios;
- any future scenario whose accepted behavior is best represented by canonical text.

It also applies to:

- gold file location;
- gold file ownership;
- comparison semantics;
- update workflow;
- version relationships;
- failure behavior;
- testing and release gates.

---

## 6. Out of scope

This ADR does not require gold files for every validation.

Non-gold assertions may be preferable for:

- process launch;
- timeout handling;
- file existence;
- artifact integrity;
- source fingerprints;
- schema validity;
- marker completion;
- nondeterministic generation;
- performance thresholds;
- broad property checks;
- security policy;
- dynamic counts whose exact textual form is not stable.

This ADR also does not define:

- the exact `.gfs` command syntax;
- the full normalization algorithm;
- the complete persisted JSON schema;
- the final CLI command spelling;
- language-specific expected outputs.

Those are owned by their dedicated specifications.

---

## 7. Canonical terminology

### Gold file

A reviewed project asset representing accepted normalized output for one scenario.

### Actual output

The current run’s normalized scenario output.

### Raw output

Unmodified stdout and stderr captured from GF.

### Gold comparison

Deterministic comparison between actual normalized output and reviewed gold.

### Gold update

Explicit project mutation replacing or creating a gold after review.

### Gold-backed scenario

A scenario whose success criteria include exact comparison with a gold file.

### Non-gold scenario

A scenario validated through another explicit assertion strategy.

---

## 8. Canonical locations

### Project gold directory

```text
project/validation/gold/
```

### Default gold path

```text
project/validation/gold/<scenario-id>.gold
```

### Actual normalized output

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

### Mismatch diff

```text
run_<run-id>/raw/scenarios/<scenario-id>.gold.diff
```

The exact run layout remains governed by the artifact model and persisted schema.

---

## 9. Ownership

### Project maintainers own

- gold content;
- scenario-to-gold mapping;
- linguistic acceptance;
- approval of gold changes;
- project release consequences;
- project documentation.

### Scenario runner owns

- execution;
- raw capture;
- marker validation;
- actual-output production request;
- structured scenario result.

### Normalizer owns

- canonical normalized-output format;
- profile behavior;
- normalization version;
- stable tokens;
- deterministic rendering.

### Comparator owns

- actual-versus-gold comparison;
- mismatch result;
- deterministic diff;
- `gold_match`.

### Report writers own

- presentation of the structured result;
- links to actual, gold and diff evidence.

No report writer may modify a gold.

---

## 10. Required relationship

Every gold-backed scenario has this relationship:

```text
scenario ID
    → scenario file
    → configured entrypoint
    → normalization profile
    → normalization version
    → gold file
    → accepted project behavior
```

The relationship must be represented in:

- `project/project.toml`;
- project validation documentation;
- scenario result;
- gold header or schema;
- active project contract lock.

---

## 11. Gold identity

A gold file must identify at least:

```text
schema identity
schema version
scenario ID
profile ID
normalization version
```

Project version or approval metadata may be included as provenance when the schema permits.

A gold file must not be interpreted only by filename.

---

## 12. Gold schema

Gold files are persisted project assets.

They therefore require:

```text
schema_id
schema_version
```

The exact schema is governed by:

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Canonical writers must emit only the current schema.

Legacy gold readers may exist through documented migration support.

---

## 13. Normalized output as comparison source

The comparator compares:

```text
expected = project gold
actual   = normalized run output
```

It does not compare raw stdout directly.

Raw output remains the evidence source for diagnosis.

Normalized output is the stable comparison source.

---

## 14. Why raw output is not compared directly

Raw output may contain non-semantic instability such as:

- prompts;
- startup banners;
- absolute paths;
- run-directory paths;
- temporary paths;
- path separators;
- timestamps;
- durations;
- terminal control sequences;
- compatible GF-version banner differences.

Comparing raw output directly would create false regressions.

However, normalization is allowed only under the separate normalization contract.

---

## 15. Normalization boundary

Gold testing depends on central versioned normalization.

The comparator must not contain its own hidden semantic cleanup.

Allowed comparator preparation is limited to file-container rules explicitly defined by schema, such as:

- accepted UTF-8 BOM compatibility;
- CRLF to LF;
- final-newline policy.

All semantic comparison normalization belongs to the normalizer.

---

## 16. Raw-evidence invariant

A successful gold comparison requires preserved raw evidence.

The system must retain, as applicable:

```text
raw stdout
raw stderr
command
working directory
GF version
exit code
duration
timeout/cancellation state
scenario script identity
scenario hash
normalization profile/version
```

A gold match without raw evidence is not valid release proof when raw capture is required by the scenario contract.

---

## 17. Exact comparison semantics

Default comparison is exact byte-equivalent comparison after canonical container handling.

Comparison must preserve:

- line order;
- section order;
- Unicode;
- punctuation;
- constructor names;
- whitespace declared semantic;
- duplicates;
- empty sections;
- final newline policy.

No fuzzy matching is applied by default.

---

## 18. Ordered versus unordered output

Default: output is ordered.

A project may declare a specific section semantically unordered only when:

- the operation truly returns a set;
- upstream order is documented as unstable;
- duplicate semantics are defined;
- normalization performs deterministic ordering;
- profile version records the rule;
- gold review accepts the canonical order.

The comparator itself does not sort.

---

## 19. Duplicate semantics

Default: duplicates are preserved.

Deduplication is allowed only when:

- multiplicity is explicitly non-semantic;
- normalization profile documents it;
- duplicate count is not required evidence;
- profile version changes appropriately;
- golds are reviewed.

The comparator does not deduplicate independently.

---

## 20. Empty output

Empty output is not automatically success.

A gold-backed section may be intentionally empty only when:

- scenario contract permits it;
- canonical section markers exist;
- gold explicitly represents the empty section;
- raw evidence shows the operation completed;
- no fatal diagnostic exists.

Missing output and empty accepted output are distinct.

---

## 21. Required versus optional gold

A scenario may define gold as:

```text
required
optional
not applicable
```

### Required gold

Absence is a project validation failure or configuration error according to the scenario contract.

It must not auto-create.

### Optional gold

Comparison occurs when the gold exists, but the scenario has another explicit success criterion.

Optional use must be documented.

### Not applicable

The scenario uses a non-gold assertion strategy.

The reason must be explicit.

---

## 22. Missing required gold

A required gold file that does not exist results in non-success.

The system MUST NOT:

- skip silently;
- create it automatically;
- treat actual output as accepted;
- mark the scenario `OK`;
- downgrade it to a warning in release mode.

The result should identify:

```text
scenario ID
expected gold path
actual output path when available
requiredness
next explicit action
```

---

## 23. Gold mismatch

A mismatch means:

- GF execution completed sufficiently;
- normalization completed;
- expected and actual outputs are comparable;
- accepted project output differs from current output.

Canonical result:

```text
validation status = FAIL
gold_match = false
```

A mismatch is not normally:

```text
ERROR
```

unless comparison could not be performed reliably.

---

## 24. Comparator error

Comparison produces `ERROR` when:

- gold cannot be decoded;
- actual output is missing unexpectedly;
- schema identity/version is invalid;
- scenario IDs disagree;
- profile IDs are incompatible;
- normalization versions are incompatible;
- output was truncated;
- raw/normalized provenance is invalid;
- file I/O fails;
- comparator invariant fails.

An `ERROR` is distinct from a valid mismatch.

---

## 25. Gold match

A match requires:

```text
process completed under scenario policy
required markers completed
normalization status OK
gold schema valid
scenario identity matches
profile/version compatibility passes
actual bytes equal expected bytes
```

A matching file cannot override:

- timeout;
- cancellation;
- launch failure;
- fatal GF diagnostic;
- untrusted artifact state;
- missing required marker;
- capture failure.

---

## 26. Diff artifact

On mismatch, GF Wordbench should produce a deterministic unified diff.

The diff should identify:

```text
scenario ID
expected gold path
actual output path
profile ID
normalization version
expected label
actual label
newline-at-end differences
```

The diff is a run artifact.

It does not modify either input.

---

## 27. Diff stability

Diff generation must be deterministic.

It must not include unstable absolute paths unless converted to stable project/run-relative references.

Context-line count should be centrally configured or fixed by contract.

A report may excerpt the diff but must link to the complete diff artifact.

---

## 28. Gold update policy

Normal validation is read-only.

Gold updates require an explicit separate operation.

Conceptual command:

```text
gf-wordbench gold update <scenario-id>
```

The exact command surface belongs to the CLI reference.

---

## 29. Update preconditions

A gold update requires:

```text
scenario exists
scenario is registered
scenario executes
raw evidence is preserved
required markers complete
normalization succeeds
profile/version is known
actual output is complete
actual output is not truncated
security policy passes
destination is approved project gold path
```

A timed-out, cancelled or launch-failed run cannot update gold.

---

## 30. Update review

Before writing a gold, the operation must provide review evidence:

- old gold, if any;
- new actual output;
- deterministic diff;
- scenario identity;
- profile/version;
- raw evidence paths;
- GF version;
- application version;
- project version when available.

An explicit approval mechanism is required where the final implementation supports automation.

---

## 31. Atomic update

Gold updates must use atomic replacement:

```text
write sibling temporary file
flush
close
validate
replace destination
```

If replacement fails, the previous gold remains intact.

No partially written canonical gold may remain.

---

## 32. Update provenance

A project should record significant gold changes through:

- version control;
- commit message;
- decision log;
- changelog/release notes;
- project release record;
- normalization migration notes when relevant.

Not every lexical correction requires a new ADR.

The acceptance rationale must remain discoverable.

---

## 33. No automatic acceptance

The system MUST NOT provide a default operation equivalent to:

```text
accept all current outputs
```

without per-project explicit review policy.

Bulk updates may exist only when:

- every scenario output is reviewable;
- diffs are generated;
- explicit approval is required;
- failed/incomplete scenarios are excluded;
- the operation remains separate from normal validation.

---

## 34. Gold creation

The first gold for a scenario follows the same review standard as an update.

Absence of a previous file does not lower the acceptance requirement.

Recommended sequence:

```text
write scenario
run scenario
inspect raw stdout/stderr
inspect normalized output
verify normalization
validate against linguistic requirements
approve output
create gold explicitly
commit scenario and gold together
```

---

## 35. Scenario changes

A scenario change may require gold review when it changes:

- command sequence;
- input;
- entrypoint;
- section identity;
- section order;
- assertion semantics;
- output bound;
- GF operation;
- expected deterministic output.

A comment-only change normally does not require gold update.

---

## 36. Entrypoint changes

Changing a scenario entrypoint is contract-significant.

Existing gold must not be reused blindly.

Required review:

```text
new entrypoint identity
new raw output
new normalized output
semantic equivalence or intended difference
project contract update
gold update decision
```

---

## 37. Input changes

Changing project validation input may change expected behavior.

A gold update should be reviewed together with:

- input diff;
- expected linguistic effect;
- scenario diff;
- actual output diff;
- coverage-matrix impact.

A gold change without the input change can hide the cause.

---

## 38. Normalization profile changes

A profile change may alter many golds.

### Compatible profile minor

May avoid gold changes if the fixture corpus proves output stability.

### Profile major

Requires identification and deliberate review of all affected gold files.

The system should not rewrite all golds automatically and call the migration complete.

---

## 39. GF version changes

A new GF version may change output.

Before updating gold:

1. capture raw output under old and new GF;
2. determine whether change is:
   - banner/noise;
   - formatting;
   - diagnostic;
   - semantic;
3. update normalization only when the difference is non-semantic;
4. update gold only when accepted semantic behavior changed or canonical representation legitimately changed;
5. update GF compatibility documentation.

Do not hide semantic GF changes through broad normalization.

---

## 40. Project implementation changes

A project code change may produce:

### Intended correction

Gold should change after review.

### Intended new capability

Gold may change or new gold may be added.

### Unexpected regression

Gold must remain unchanged and the implementation should be fixed.

The presence of a diff does not determine which category applies.

Human/project review is required.

---

## 41. Release-gate behavior

For a required gold-backed scenario, release requires:

```text
scenario status = OK
gold_match = true
normalization compatible
raw evidence complete
no fatal diagnostic
no timeout/cancellation
```

A missing gold, mismatch or comparison error blocks release.

Optional scenario policy is project-defined.

---

## 42. Regression comparison

Gold comparison and previous-run comparison are separate.

### Gold comparison asks

```text
Does current behavior equal accepted behavior?
```

### Previous-run comparison asks

```text
How did current behavior change relative to the previous compatible run?
```

A run may be:

- unchanged from previous but still fail gold;
- changed from previous and now match gold;
- match gold but differ in non-gold metadata;
- fail before gold comparison.

The system must not merge these concepts.

---

## 43. Framework fixtures versus project golds

Framework fixtures validate framework behavior.

Examples:

- normalizer output;
- diagnostic parser output;
- report formatting;
- schema migrations.

Project golds validate active-language behavior.

They must live in separate ownership domains.

Framework tests must not depend on active project golds unless explicitly testing project integration.

---

## 44. Version-control policy

Gold files should be version-controlled.

A review should show:

- scenario diff;
- input diff;
- gold diff;
- relevant documentation diff.

Generated actual outputs and run diffs should not normally be committed outside test fixtures.

---

## 45. Merge-conflict policy

Gold files may conflict when multiple branches change the same scenario behavior.

Do not resolve by choosing one side blindly.

Resolve by:

1. understanding both intended changes;
2. rebuilding the combined implementation;
3. executing the scenario;
4. reviewing new raw and normalized output;
5. approving one combined gold;
6. running relevant release validation.

---

## 46. Encoding

Gold files use:

```text
UTF-8 without BOM
```

unless the persisted schema defines a compatibility reader.

Canonical newline:

```text
LF
```

A final newline is required.

Unicode content is preserved according to normalization policy.

---

## 47. Paths in gold

Gold files should use stable tokens or project-relative paths as produced by normalization.

Absolute developer-machine paths are prohibited in canonical gold output unless the scenario explicitly validates such a path contract, which is generally inappropriate.

---

## 48. Timestamps and durations

Execution timestamps and measured durations should not appear as literal accepted values unless the scenario validates them.

Approved normalization replaces or excludes them under versioned rules.

The comparator does not wildcard them.

---

## 49. Diagnostics in gold

A project may gold-test diagnostics when exact diagnostic behavior is intentionally part of the scenario.

Because diagnostic wording is GF-version-sensitive, such scenarios must define:

- supported GF versions;
- diagnostic parser/profile expectations;
- whether exact wording is required;
- migration policy.

Most failure classification should use structured diagnostics rather than broad diagnostic golds.

---

## 50. Negative scenarios

A negative scenario may use gold to verify expected rejection.

It must distinguish:

- expected GF rejection;
- infrastructure error;
- timeout;
- marker failure;
- unsupported command.

A timeout cannot satisfy a negative linguistic scenario merely because no accepted output appeared.

---

## 51. Generation scenarios

Exact gold is appropriate only when generation is deterministic under the declared contract.

Required conditions:

- finite bound;
- stable seed where relevant;
- stable order or versioned canonical set ordering;
- duplicate policy;
- compatible GF behavior.

Otherwise, use structured assertions instead of exact gold.

---

## 52. Morphology tables

Morphology outputs may be gold-tested when:

- table content is bounded;
- field/row meaning is stable;
- padding normalization is conservative;
- Unicode and empty forms remain visible;
- expected variants are defined.

Do not normalize away distinctions needed for linguistic review.

---

## 53. Parse trees

Parse-tree golds preserve:

- constructor names;
- nesting;
- argument order;
- parse ordering unless explicitly canonicalized;
- ambiguity;
- empty parse results;
- Unicode strings.

Do not reformat trees merely to reduce diffs unless a formal canonical GF-term renderer is adopted.

---

## 54. Linearization

Linearization golds preserve:

- surface strings;
- punctuation;
- Unicode;
- spacing with linguistic meaning;
- empty strings;
- variant order unless explicitly unordered.

Do not case-fold, strip accents or transliterate.

---

## 55. Missing functions

Missing-function golds preserve the accepted inventory.

Release policy may require an empty inventory.

If the project intentionally permits omissions, the gold and release criteria must document them.

A missing-function list must not be hidden as noise.

---

## 56. Gold file naming

Canonical default:

```text
<scenario-id>.gold
```

If multiple gold variants are supported in the future, the naming scheme must be versioned and explicit, for example by:

- GF compatibility profile;
- platform class;
- configured dialect;
- scenario variant.

Do not add ad hoc suffixes such as:

```text
-final
-new
-fixed
-copy2
```

---

## 57. Multiple gold variants

Multiple gold variants are discouraged.

They are allowed only when a real supported compatibility dimension exists.

The selection rule must be:

- deterministic;
- configured;
- documented;
- recorded in the scenario result;
- tested;
- release-reviewable.

A variant must not be selected merely because it matches current output.

---

## 58. Platform variants

Platform-specific golds should be avoided through safe normalization.

They may exist only when platform differences are semantically relevant and intentionally supported.

Path separators and line endings alone do not justify separate golds.

---

## 59. GF-version variants

GF-version-specific golds may be necessary when:

- the project supports multiple GF versions;
- output differences are semantic or contractually meaningful;
- normalization cannot safely unify them.

Selection must use recorded GF compatibility, not best-match fallback.

---

## 60. Gold provenance

A gold should be traceable to:

```text
scenario ID
scenario hash
profile ID/version
GF version
application version
project version
approval change
```

Not every field must be embedded directly in the file.

The combined repository and release evidence must provide the trace.

---

## 61. Gold validity

A gold becomes invalid when:

- scenario identity changes;
- schema version unsupported;
- profile major incompatible;
- entrypoint changes without review;
- accepted project behavior changes;
- project migration retires the scenario;
- file is malformed;
- file contains unresolved placeholders;
- file was generated from incomplete evidence.

Invalid golds must not be silently repaired during normal validation.

---

## 62. Deprecated scenarios

When a scenario is deprecated:

- its gold remains while the scenario remains supported;
- replacement is documented;
- coverage moves deliberately;
- removal occurs through project migration;
- the old scenario ID is not reused.

A retired scenario gold may move to historical fixtures only under explicit policy.

---

## 63. Gold deletion

Deleting a gold is contract-significant.

Allowed reasons:

- scenario retired;
- comparison strategy changed explicitly;
- scenario no longer deterministic and uses another assertion;
- project scope removed the behavior;
- migration replaced the identity.

Deletion requires updates to:

- project configuration;
- validation specification;
- coverage matrix;
- contract lock;
- release criteria;
- tests.

---

## 64. Comparison result model

A structured comparison result should contain:

```text
scenario_id
gold_required
gold_path
actual_path
gold_schema_id
gold_schema_version
profile_id
normalization_version
comparison_status
gold_match
diff_path
primary_message
warnings
```

The persisted shape is owned by the shared schema/model.

---

## 65. Comparison statuses

A comparator may internally use:

```text
matched
mismatched
not_applicable
error
```

The final validation result maps these to canonical validation status.

The internal vocabulary must not compete with the public status enum.

---

## 66. Failure mapping

Recommended mapping:

| Condition | Scenario status | Gold match |
|---|---:|---:|
| Exact match | `OK` | `true` |
| Valid mismatch | `FAIL` | `false` |
| Missing required gold | `FAIL` or project configuration `ERROR` per contract | `null` |
| Unsupported gold schema | `ERROR` | `null` |
| Profile/version mismatch | `ERROR` | `null` |
| Actual output missing after successful normalization expected | `ERROR` | `null` |
| Scenario skipped | `SKIPPED` | `null` |
| No gold applicable, alternative assertion passes | `OK` | `null` |
| Timeout/cancellation | `ERROR` | `null` |

The active schema/reference documents own final field semantics.

---

## 67. Primary messages

Recommended messages:

```text
Golden output matched.
Golden output differs from accepted output.
Required golden output is missing.
Golden output schema is unsupported.
Normalization profile is incompatible with the golden output.
Actual normalized output is unavailable.
Golden comparison was not applicable.
```

Messages are human-facing and must not become machine logic.

---

## 68. Security

Gold and actual output are untrusted text for rendering purposes.

The system must:

- avoid executing gold content;
- escape it in HTML-capable reports;
- bound diff generation;
- validate paths;
- prevent traversal;
- prevent gold update outside the approved directory;
- avoid secret values;
- reject symlink policies that escape the project root where strict policy requires.

---

## 69. Large golds

Gold files should remain reviewable.

A scenario producing extremely large output should be redesigned using:

- bounded representative sections;
- structural assertions;
- sampled deterministic cases;
- separate focused scenarios.

Large output limits belong to scenario and artifact policy.

Do not use enormous golds as a substitute for meaningful coverage design.

---

## 70. Performance

Comparison should be deterministic and bounded.

For large valid files:

- stream or memory-map only if needed;
- preserve exact semantics;
- generate bounded report excerpts;
- keep complete diff artifact only within configured limits;
- report when diff output is truncated.

A truncated diff may still accompany a valid mismatch if the complete expected/actual files remain available.

---

## 71. Automated checks

Recommended conceptual command:

```text
gf-wordbench gold check
```

Strict mode:

```text
gf-wordbench gold check --strict
```

The checker should verify:

1. every required gold-backed scenario has one gold;
2. no duplicate scenario-to-gold mapping exists;
3. file names match scenario IDs;
4. schema identity/version is supported;
5. profile identity/version is compatible;
6. UTF-8 and newline policy pass;
7. no unresolved placeholders exist;
8. no undeclared permanent gold exists in strict mode;
9. no gold path escapes the project root;
10. retired scenario IDs are not reused;
11. normal validation leaves gold unchanged;
12. project/template separation remains intact.

---

## 72. Required unit tests

Recommended framework tests:

```text
tests/gold/
├── test_gold_discovery.py
├── test_gold_schema.py
├── test_gold_comparison.py
├── test_gold_diff.py
├── test_gold_update.py
├── test_gold_version_compatibility.py
├── test_gold_security.py
└── test_gold_release_gates.py
```

---

## 73. Discovery tests

Required cases:

- canonical file exists;
- missing required file;
- optional file absent;
- filename mismatch;
- duplicate mapping;
- undeclared file;
- path traversal;
- symlink policy;
- deterministic order.

---

## 74. Schema tests

Required cases:

- current schema;
- supported legacy schema;
- unknown newer major;
- malformed header;
- wrong scenario ID;
- wrong profile ID;
- incompatible normalization version;
- missing required metadata.

---

## 75. Comparison tests

Required cases:

- exact match;
- one-line mismatch;
- multiline mismatch;
- Unicode difference;
- punctuation difference;
- trailing-space policy;
- final-newline difference;
- empty section;
- duplicate line;
- section-order difference;
- actual missing;
- expected missing.

---

## 76. Diff tests

Required cases:

- deterministic labels;
- stable context;
- Unicode;
- missing final newline;
- large diff truncation policy;
- no absolute unstable paths;
- actual/expected unchanged after diff generation.

---

## 77. Update tests

Required cases:

- create new gold explicitly;
- replace existing gold;
- diff shown before update;
- atomic write;
- write failure preserves old file;
- timeout output rejected;
- truncated output rejected;
- wrong scenario rejected;
- normal audit cannot update;
- bulk update requires explicit policy.

---

## 78. Release-gate tests

Required cases:

```text
required match → release gate may pass
required mismatch → fail
required missing → fail/error
optional mismatch → project policy
profile mismatch → error
timeout → error
no gold + documented non-gold assertion → allowed
```

---

## 79. Integration tests

A small real-GF fixture should prove:

- scenario execution;
- raw output capture;
- normalization;
- gold match;
- intentional mismatch;
- diff artifact;
- explicit update workflow;
- unchanged gold during normal audit.

---

## 80. Migration tests

When gold schema/profile changes:

- old fixture reads;
- migration result is deterministic;
- semantic content is preserved;
- incompatible changes are rejected;
- project review requirement remains explicit;
- migrated file writes atomically.

---

## 81. Review checklist

Before accepting a gold change:

```text
[ ] Scenario ID unchanged or migration reviewed
[ ] Entrypoint reviewed
[ ] Input reviewed
[ ] Raw stdout reviewed
[ ] Raw stderr reviewed
[ ] Normalized output reviewed
[ ] Normalization rules reviewed
[ ] GF version reviewed
[ ] Semantic change understood
[ ] Diff reviewed
[ ] Project documentation updated
[ ] Coverage matrix updated if needed
[ ] Release criteria updated if needed
[ ] Contract lock updated if needed
[ ] Project version reviewed
```

---

## 82. Alternatives considered

### 82.1 Compare raw stdout directly

**Rejected.**

Reasons:

- unstable prompts;
- absolute paths;
- timestamps;
- durations;
- platform line endings;
- compatible GF banner differences.

It would create false regressions.

---

### 82.2 Store expected outputs in Python tests only

**Rejected as the project-level standard.**

Reasons:

- language expectations would live in framework code;
- project maintainers could not review them independently;
- scenario IDs and outputs would be harder to map;
- active language would leak into framework tests.

Python fixtures remain appropriate for framework behavior.

---

### 82.3 Use only regular-expression assertions

**Rejected as the general mechanism.**

Reasons:

- insufficient for complex multiline output;
- easy to make too broad;
- can miss ordering, duplicates, punctuation and Unicode;
- tends to hide unintended extra output.

Regex assertions may supplement a scenario when narrowly justified.

---

### 82.4 Parse every GF output into a rich semantic AST

**Rejected for the baseline architecture.**

Reasons:

- GF output forms vary;
- high implementation complexity;
- risk of reimplementing GF behavior;
- parser/reserializer could alter meaning;
- unnecessary for exact reviewed text.

Dedicated structured parsers may be added for specific stable outputs through separate decisions.

---

### 82.5 Automatically accept current output

**Rejected.**

Reasons:

- bugs become accepted behavior;
- no independent expected value;
- no review boundary;
- regression testing loses value.

---

### 82.6 Update gold during normal validation

**Rejected.**

Reasons:

- validation would mutate its own expected results;
- CI could hide regressions;
- failed runs could overwrite expectations;
- audit reproducibility would be compromised.

---

### 82.7 Keep golds in run directories

**Rejected.**

Reasons:

- run artifacts are generated evidence;
- expected behavior is a maintained project asset;
- retention cleanup could delete expectations;
- ownership would be unclear.

---

### 82.8 One repository-wide gold for all projects

**Rejected.**

Reasons:

- one repository copy has one active project;
- language expectations are project-specific;
- template must remain generic;
- project release lifecycle is independent.

---

### 82.9 Snapshot every report

**Rejected as the validation source.**

Reasons:

- reports include presentation and metadata;
- report wording may change;
- exact language behavior should be isolated from report formatting;
- machine results already exist separately.

Report snapshots remain useful for report-writer tests.

---

### 82.10 Fuzzy comparison

**Rejected as the default.**

Reasons:

- tolerance rules can hide regressions;
- difficult to audit;
- unclear semantics for Unicode and trees;
- exact accepted behavior is preferred after controlled normalization.

Special fuzzy/property assertions require explicit separate contracts.

---

## 83. Consequences

### 83.1 Positive consequences

- Rich GF behavior is reviewable.
- Language expectations remain project-owned.
- Regressions produce readable diffs.
- Raw evidence is preserved.
- Cross-platform noise is handled centrally.
- Release gates can be strict.
- Scenario and gold identity are explicit.
- Expected outputs are version-controlled.
- Current output cannot silently become accepted.
- Framework fixtures remain separate from language expectations.

### 83.2 Costs

- Gold files require maintenance.
- Normalization must remain conservative and versioned.
- GF upgrades may require review.
- Merge conflicts may require rerunning scenarios.
- Large outputs must be redesigned.
- Project maintainers must distinguish intended changes from regressions.

### 83.3 Risks

- Over-normalization could hide semantic change.
- Blind gold updates could accept defects.
- Stale golds could block legitimate changes.
- Version mismatch could create confusing failures.
- Nondeterministic scenarios could create unstable golds.
- Review burden may increase.

These risks are mitigated by explicit update operations, profile versioning, raw evidence and project review.

---

## 84. Operational rules

The decision creates these mandatory operational rules:

```text
[1] Normal audits never write project golds.
[2] Actual output always belongs to the run.
[3] Raw evidence is retained.
[4] Normalization is centralized and versioned.
[5] Comparator applies no hidden semantic cleanup.
[6] Missing required gold is non-success.
[7] Mismatch is FAIL, comparison inability is ERROR.
[8] Timeout/cancellation cannot match gold.
[9] Gold updates are explicit and atomic.
[10] Gold/profile/scenario identities must agree.
```

---

## 85. Contract impacts

This decision affects:

- project configuration;
- scenario registry;
- scenario result model;
- normalized-output schema;
- gold schema;
- artifact model;
- report writers;
- release gates;
- project completion checklist;
- project template;
- migration tooling;
- tests.

Any change to one of these relationships requires coordinated review.

---

## 86. Persisted-schema impacts

At minimum, schemas must support:

- gold identity;
- normalized-output identity;
- scenario ID;
- profile ID;
- normalization version;
- gold path;
- actual path;
- match result;
- diff path;
- comparison error;
- requiredness.

The exact field shapes remain governed by the schema lock.

---

## 87. Project-template impacts

The template must contain:

```text
templates/project/validation/gold/README.md
```

and project documentation explaining:

- ownership;
- update policy;
- naming;
- review;
- schema/version relationship.

The template must not contain active-language gold content.

---

## 88. Documentation impacts

The following documents must remain aligned:

- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/OUTPUT_NORMALIZATION.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`
- `docs/gf/GF_OUTPUT_NORMALIZATION.md`
- `docs/validation/SCENARIO_VALIDATION.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/TEST_COVERAGE_MATRIX.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

This ADR records the architectural decision; detailed procedures belong to those documents.

---

## 89. Implementation guidance

Recommended conceptual components:

```text
scenario_runner
normalizer
gold_loader
gold_comparator
gold_diff_writer
gold_update_operation
result_builder
report writers
```

One component may own more than one closely related responsibility if the boundaries remain explicit.

---

## 90. Central constants

These values need one owner:

```text
gold extension
gold schema ID
normalized-output schema ID
profile IDs
canonical section markers
default gold directory
diff extension
```

Do not duplicate literal values in multiple components.

---

## 91. CLI/GUI behavior

CLI and GUI must invoke the same gold logic.

Equivalent inputs must produce equivalent:

- selected scenario;
- gold path;
- profile;
- comparison result;
- update behavior;
- errors.

GUI must not provide a silent “accept” shortcut that bypasses review policy.

---

## 92. CI behavior

CI normal validation:

- reads golds;
- writes actual outputs to run artifacts;
- produces diffs;
- fails required mismatches;
- does not update golds.

A dedicated reviewed CI workflow may propose gold updates, but it must not merge/accept them automatically without explicit project policy.

---

## 93. Migration strategy

When introducing golds into an existing project:

1. inventory scenarios;
2. classify deterministic scenarios;
3. define normalization profiles;
4. execute scenarios;
5. preserve raw evidence;
6. review normalized output;
7. create initial golds explicitly;
8. document non-gold scenarios;
9. update project validation specification;
10. update release gates.

Initial gold creation is a project migration, not merely test fixture generation.

---

## 94. Legacy gold formats

A legacy gold may be readable through an adapter.

The adapter must:

- detect legacy format;
- preserve semantic content;
- produce current in-memory representation;
- warn or migrate;
- avoid writing legacy format;
- reject ambiguous content.

Canonical writers emit only the current schema.

---

## 95. Decision compliance checks

A compliant implementation can answer:

```text
Which scenario owns this gold?
Which profile/version produced comparable output?
Where is the raw evidence?
Was the actual output complete?
Was the gold required?
Was the comparison exact?
Where is the diff?
Was the gold modified during normal validation?
Who approved the gold change?
```

If these answers cannot be established, the gold evidence is incomplete.

---

## 96. Drift indicators

Golden-testing drift exists when:

- normal validation modifies gold;
- actual output is written into the project gold directory;
- raw stdout/stderr are missing;
- comparator normalizes independently;
- a scenario matches a gold with a different ID;
- profile major changes without gold review;
- missing required gold passes;
- current output is auto-accepted;
- a timeout-produced output is compared as complete;
- a stale gold uses an old entrypoint unnoticed;
- framework tests depend on active project gold;
- gold variants are chosen by best match;
- a gold contains developer absolute paths;
- Unicode is silently rewritten;
- duplicates/order are changed without policy;
- a human report is used as the comparison source;
- a mismatch becomes `ERROR` without comparator failure;
- comparison errors become normal `FAIL`;
- a gold is deleted without coverage/release updates;
- a project template contains active-language gold content.

Every drift indicator requires correction or a new coordinated architectural decision.

---

## 97. Change workflow

A change affecting golden testing is complete only when applicable items are reviewed:

```text
[ ] Scenario identity reviewed
[ ] Entrypoint reviewed
[ ] Input reviewed
[ ] Raw output reviewed
[ ] Normalization profile reviewed
[ ] Normalization version reviewed
[ ] Gold schema reviewed
[ ] Gold requiredness reviewed
[ ] Comparator behavior reviewed
[ ] Diff behavior reviewed
[ ] Update workflow reviewed
[ ] Release-gate impact reviewed
[ ] Project-version impact reviewed
[ ] Contract locks updated
[ ] Schema lock updated
[ ] Tests updated
[ ] Documentation updated
```

---

## 98. Decision review triggers

Review this ADR when:

- fuzzy comparison is proposed as a general mechanism;
- semantic parsers replace text comparison;
- multiple active projects are introduced;
- project gold ownership changes;
- golds move outside the project;
- normal validation is proposed to update gold;
- a new nondeterministic assertion framework is introduced;
- normalization is removed or decentralized;
- scenario results no longer retain raw evidence;
- gold schema identity changes fundamentally.

Minor implementation refinements do not require a new ADR when they preserve this decision.

---

## 99. Related decisions

- `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`
- `ADR-0002-GF-AS-EXECUTION-ENGINE.md`
- `ADR-0003-SEPARATE-SCAN-AND-COMPILE.md`
- `ADR-0004-NATIVE-GFS-SCENARIOS.md`
- `ADR-0005-FILE-AND-SCENARIO-RESULTS.md`
- `ADR-0006-AI-READY-REPORT.md`

This ADR depends especially on:

```text
ADR-0002
ADR-0004
ADR-0005
```

---

## 100. Related normative documents

- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`
- `docs/scenarios/OUTPUT_NORMALIZATION.md`
- `docs/gf/GF_OUTPUT_NORMALIZATION.md`
- `docs/validation/SCENARIO_VALIDATION.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/release/VERSIONING_POLICY.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/TEST_COVERAGE_MATRIX.md`

---

## 101. Final decision statement

GF Wordbench adopts reviewed, versioned golden-output testing for deterministic native GF scenario behavior.

The accepted architecture is:

```text
raw GF evidence
    → versioned normalization
    → canonical actual output
    → reviewed project gold
    → exact comparison
    → deterministic diff
    → structured validation result
```

Normal validation remains read-only.

Expected behavior is never updated implicitly.

Therefore:

> A golden file is accepted project behavior, not a convenient copy of whatever the current implementation produced.

Any change to scenario identity, semantic input, entrypoint, normalization meaning or accepted output must be reviewed as one coordinated project contract change.
