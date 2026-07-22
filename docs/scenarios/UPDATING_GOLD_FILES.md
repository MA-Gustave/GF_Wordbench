# GF Wordbench — Updating Gold Files

**Document ID:** `GF-WB-SCENARIOS-GOLD-UPDATE`  
**Status:** Normative operational specification  
**Applies to:** Reviewed `.gold` files associated with GF Wordbench `.gfs` scenarios  
**Primary owner:** Gold update service using `app/audit/scenario_runner.py`  
**Project owner:** Maintainers of the active language project  
**Canonical gold root:** `project/validation/gold/`  
**Target architecture:** Final GF Wordbench architecture  
**Last structural review:** 2026-07-22

---

## 1. Purpose

Gold files are reviewed expected outputs for deterministic scenario validation.

They are source artifacts, not disposable test output.

This document defines the only safe process for:

- creating a gold file for a new scenario;
- updating a gold after an intentional behavior change;
- reviewing normalization changes;
- updating one or several scenarios;
- performing an approved non-interactive update;
- preserving evidence, rollback, and version-control history;
- preventing accidental baseline acceptance.

The governing rule is:

> A gold file may change only after its candidate output has been produced by the configured scenario, normalized by the declared normalization version, reviewed as a diff, and accepted through an explicit update operation.

A normal audit must never update a gold file.

---

## 2. Related normative documents

This document must remain consistent with:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/RELEASE_GATES.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/DECISION_LOG.md
project/docs/STATUS_LEDGER.md
project/docs/RELEASE_CRITERIA.md
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Authority boundaries:

| Subject | Owner |
|---|---|
| Gold text schema and canonical path | `PERSISTED_SCHEMA_LOCK.md` |
| GF scenario execution boundary | `EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Scenario syntax and markers | `SCENARIO_FORMAT.md` |
| Normalization rules | `OUTPUT_NORMALIZATION.md` |
| Gold comparison semantics | `GOLDEN_TESTS.md` |
| Gold update workflow | this document |
| Scenario and gold registry | active project contract lock |
| Linguistic correctness | active project maintainers |
| Release gating | project release criteria |

---

## 3. Canonical gold format

Canonical path:

```text
project/validation/gold/<scenario-id>.gold
```

Canonical format:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: <scenario-id>
# normalization_version: <version>
--- BEGIN <section-id> ---
<expected normalized GF output>
--- END <section-id> ---
```

Example:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: linearize
# normalization_version: 1.0
--- BEGIN linearize-basic ---
la maison
--- END linearize-basic ---
```

Encoding:

```text
UTF-8 without BOM
LF newlines
final newline required
```

Readers may accept CRLF for compatibility.

Canonical writers emit LF.

---

## 4. Gold invariants

Every gold file must satisfy:

1. Its filename matches the configured scenario ID.
2. Its header scenario ID matches the filename.
3. The scenario exists in `project.toml`.
4. The scenario script exists.
5. The normalization version is declared and supported.
6. Required sections are present.
7. Section markers are balanced.
8. Section IDs are unique.
9. Content is normalized output, not raw process output.
10. Linguistically meaningful content remains intact.
11. Platform noise is removed only by documented normalization.
12. Required gold files are version-controlled.
13. Ordinary validation opens them read-only.
14. A missing required gold is an error.
15. An empty gold is valid only when explicitly documented.
16. One scenario variant has one authoritative gold.
17. The gold corresponds to reviewed behavior.
18. No secrets or full environment dumps are included.
19. No developer-local path is included unless intentionally tested.
20. Gold writes occur only through the explicit update path.

---

## 5. What a passing gold comparison proves

A passing comparison proves that:

- the configured scenario ran;
- required markers completed;
- raw output was captured;
- normalization succeeded;
- the normalized output matched the reviewed gold;
- the declared normalization version was used.

It does not prove that:

- every module compiles;
- every linguistic behavior is correct;
- every variant is covered;
- the final PGF is release-ready;
- the scenario itself is complete;
- the baseline was reviewed correctly.

Gold validation is one layer of the release evidence.

---

## 6. Legitimate reasons to update

A gold update is justified by an intentional change such as:

```text
language source behavior changed
scenario input changed
scenario command changed
scenario section contract changed
accepted linguistic output changed
accepted variant order changed
GF version changed and the difference is understood
normalization rule changed
normalization version changed
an incorrect gold was repaired
a new scenario was added
an optional gold became required
```

The update must be associated with a concrete source, scenario, specification, compatibility, or normalization change.

---

## 7. Illegitimate reasons to update

Do not update gold merely because:

- a test failed;
- accepting the output is easier than diagnosing it;
- the source change was accidental;
- the wrong project ran;
- the wrong entrypoint loaded;
- the wrong GF executable ran;
- the scenario timed out;
- required markers are missing;
- normalization failed;
- stale `.gfo` or `.pgf` artifacts were used;
- output is nondeterministic;
- environment paths leaked into output;
- an unsupported command was ignored;
- an internal GF error occurred;
- the reviewer cannot explain the difference.

A gold update is not an error-recovery shortcut.

---

## 8. Canonical update command

```text
gf-wordbench gold update <scenario-id>
```

Examples:

```text
gf-wordbench gold update linearize
gf-wordbench gold update parse
gf-wordbench gold update missing
```

This command is separate from all ordinary validation commands.

The following must never imply gold updating:

```text
gf-wordbench quick
gf-wordbench checkpoint
gf-wordbench release
gf-wordbench diagnostic
gf-wordbench validate
```

---

## 9. Update scopes

### 9.1 One scenario

Preferred default:

```text
gf-wordbench gold update <scenario-id>
```

### 9.2 Explicit scenario set

```text
gf-wordbench gold update <scenario-id-1> <scenario-id-2>
```

Each scenario receives an independent candidate, diff, decision, and write result.

### 9.3 All registered gold scenarios

```text
gf-wordbench gold update --all
```

`--all` includes only registered scenarios with an explicit gold contract.

It must not include:

- orphan gold files;
- disabled scenarios;
- scenarios without gold;
- scenarios outside the active project;
- assertion-only scenarios.

Bulk update remains a collection of individually reviewable updates.

---

## 10. Dry-run preview

```text
gf-wordbench gold update <scenario-id> --dry-run
```

Dry run must:

1. resolve the project;
2. validate the scenario contract;
3. execute the scenario;
4. capture raw evidence;
5. normalize output;
6. construct the candidate;
7. validate the candidate;
8. compute and save the diff;
9. write no canonical project gold.

A dry run must not create a missing gold in `project/validation/gold/`.

---

## 11. Interactive acceptance

Interactive mode is the default.

The confirmation view must show:

```text
project ID
scenario ID
scenario script
current gold path
candidate path
GF executable
GF version
normalization version
old hash
new hash
diff path
changed sections
```

Available decisions should include:

```text
accept
reject
show full diff
show raw evidence
abort remaining updates
```

The default decision is rejection.

Pressing Enter without an explicit positive decision must not accept.

---

## 12. Explicit scripted acceptance

The final CLI may support:

```text
--accept
```

Rules:

- it must be explicitly supplied;
- it applies only to `gold update`;
- it is never inherited from configuration or GUI state;
- it must not be implied by a generic `--yes`;
- it must not be enabled by default;
- every written file is listed in the command result.

Projects may prohibit this flag outside controlled maintenance workflows.

---

## 13. Non-interactive CI acceptance

A dedicated CI operation may be supported:

```text
gf-wordbench gold update <scenario-id> --ci-approved
```

It is allowed only when:

```text
CI is explicitly detected
the scenario selection is explicit
the project is valid
the GF version is supported
the normalization version is declared
scenario execution succeeds
required markers complete
candidate validation succeeds
a complete diff is saved
the workflow has an external human approval gate
```

`--ci-approved` is not permission to accept arbitrary new output.

A routine test workflow must not rewrite and commit gold files automatically.

Acceptable CI controls include:

```text
manually triggered maintenance workflow
protected environment approval
reviewed pull request
explicit baseline-update job
```

---

## 14. Required workflow

The updater must perform this sequence:

```text
resolve active project
→ resolve scenario contract
→ validate current gold
→ resolve GF executable and version
→ resolve effective GF path
→ execute scenario
→ preserve raw evidence
→ verify markers and required artifacts
→ normalize output
→ construct canonical candidate
→ validate candidate
→ compare with current gold
→ classify changes
→ show or save complete diff
→ obtain explicit acceptance
→ write sibling temporary file
→ validate temporary file
→ atomically replace destination
→ re-read and verify final bytes
→ record update evidence
```

No required step may be skipped.

---

## 15. Resolve the active project

The updater loads:

```text
project/project.toml
```

It establishes:

```text
project ID
language identity
project root
scenario registry
required/optional status
entrypoints
GF path parts
validation policy
```

It must not infer project identity from:

```text
old run directories
gold filenames
GUI state
current terminal directory alone
scenario filenames alone
```

A project identity mismatch stops the update.

---

## 16. Resolve the scenario contract

The selected scenario must resolve to one registry entry.

Required checks:

```text
scenario ID is unique
script exists
script is inside the project
script is UTF-8 readable
required/optional status is known
entrypoint is declared
input files are declared
gold path is declared
normalization version is known
expected markers are known
timeout is positive
```

An orphan gold must not be updated by guessing its scenario.

---

## 17. Validate the current gold

When the gold exists, validate:

```text
schema header
schema version
scenario ID
normalization version
balanced markers
required sections
UTF-8 readability
path containment
final newline
```

If the current gold is malformed:

- report the error;
- preserve it;
- do not silently replace it;
- require an explicit repair or migration;
- keep a version-control recovery path.

---

## 18. Execute the scenario

The updater must use the same scenario runner as ordinary validation.

It must not implement a second GF execution path.

Required execution evidence:

```text
resolved GF executable
GF version
ordered command
working directory
effective GF path
timeout
start and finish time
duration
exit code
timeout state
stdout path
stderr path
scenario hash
input hashes when applicable
```

Raw output is captured before normalization.

---

## 19. Candidate-generation prerequisites

Candidate generation may continue only when:

```text
the process launched
no timeout occurred
execution was not cancelled
the exit policy passed
no fatal framework/tool error remains
required markers completed
required artifacts exist
raw stdout and stderr are available
```

The update stops on:

```text
launch failure
timeout
cancellation
missing or malformed marker
unsupported scenario command
missing evidence
normalization failure
security violation
missing required artifact
```

A scenario `FAIL` caused only by a gold mismatch may continue to review.

---

## 20. Raw evidence

Canonical run evidence:

```text
run_<run-id>/raw/scenarios/<scenario-id>.stdout.txt
run_<run-id>/raw/scenarios/<scenario-id>.stderr.txt
```

Raw evidence is immutable after capture.

Candidate and diff artifacts must reference the raw evidence from which they were derived.

Raw output must not be copied directly into a gold without normalization and review.

---

## 21. Normalization

The updater calls the same versioned normalizer used by validation.

Allowed documented normalization may include:

```text
CRLF to LF
trailing spaces
known prompts
absolute run-directory prefixes
temporary paths
unstable timestamps
measured durations
platform path separators
irrelevant version banners
```

Normalization must not remove:

```text
GF error messages
required source locations
abstract trees
linearized strings
parse counts
ambiguity information
missing-function lists
morphology results
meaningful punctuation
meaningful whitespace
Unicode distinctions
evidence that a required section did not run
```

An updater-only normalizer is prohibited.

---

## 22. Candidate construction

Recommended candidate path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.candidate.gold
```

The candidate contains:

```text
canonical gold header
scenario ID
normalization version
normalized completed sections
final newline
```

The candidate must not be written directly to the project gold path before acceptance.

Candidate generation must be deterministic.

---

## 23. Candidate validation

The candidate must pass:

```text
UTF-8 validation
canonical header validation
scenario ID validation
normalization version validation
marker validation
required-section validation
duplicate-section detection
newline policy
output-size limit
secret detection
unstable-noise checks where enforceable
```

An invalid candidate cannot be accepted.

---

## 24. Comparison result

The updater distinguishes:

```text
unchanged
created
modified
added sections
removed sections
normalization-version change
schema-version change
```

If the candidate is identical to the current gold:

```text
no update required
```

The canonical file should not be rewritten.

---

## 25. Diff requirements

Every changed candidate produces a complete UTF-8 unified diff.

Recommended path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.gold.diff
```

The diff should identify:

```text
current gold
candidate
scenario ID
normalization version
added lines
removed lines
changed sections
```

The console may show a summary, but the complete diff must be saved.

No gold update may be accepted without an inspectable diff.

---

## 26. Semantic review

The reviewer must answer:

```text
Did the intended source or specification change?
Did the correct project run?
Did the correct entrypoint load?
Did the correct scenario run?
Did all required sections complete?
Is the output linguistically correct?
Did ambiguity change intentionally?
Did variant order change intentionally?
Did missing-linearization output change intentionally?
Did orthography or Unicode change intentionally?
Did normalization remove meaningful content?
Did unstable noise leak into the candidate?
Did a GF version change cause the difference?
Does the scenario still test its intended contract?
Do project documents require updates?
Does release behavior change?
```

A diff that cannot be explained must be rejected.

---

## 27. Review by scenario type

### Load

Review:

```text
entrypoint identity
marker completion
unexpected diagnostics
stable grammar identity
```

### Missing linearizations

Review:

```text
added missing functions
removed missing functions
category impact
ordering stability
whether omissions are intentional
```

### Linearization

Review:

```text
surface forms
orthography
spacing
punctuation
capitalization
agreement
word order
variant order
empty versus missing output
```

### Parse

Review:

```text
accepted trees
rejected inputs
parse counts
ambiguity
category
language
tree order when contractual
```

### Generation

Exact gold is allowed only for bounded deterministic generation.

Otherwise use assertions.

### Morphology

Review:

```text
forms
features
paradigm coverage
orthography
variants
missing cells
ordering
```

---

## 28. Normalization-version changes

A normalization-version change is a contract change.

Required actions:

```text
update normalizer
increment normalization version
update normalization documentation
update tests
run every affected scenario
generate a diff for every affected gold
review semantic preservation
record migration notes
update affected gold headers
rerun release validation
```

The updater must not change only the header.

---

## 29. GF-version changes

When GF changes output:

1. record old and new GF versions;
2. confirm support policy;
3. inspect compatibility notes when available;
4. classify each difference as environmental or semantic;
5. normalize only truly unstable non-semantic differences;
6. review semantic differences as project changes;
7. add regression tests;
8. update compatibility documentation.

Do not normalize away a real behavior change to preserve an old gold.

---

## 30. New gold creation

A missing gold may be created only when:

```text
the scenario is registered
the gold contract is declared
scenario execution succeeds
required markers complete
normalization succeeds
candidate validation succeeds
linguistic review occurs
explicit acceptance occurs
```

The command remains:

```text
gf-wordbench gold update <scenario-id>
```

The tool must display:

```text
current gold: missing
candidate: <path>
action: create
```

Ordinary validation must report a missing required gold as `ERROR`.

---

## 31. Removing a gold

A gold may be removed when:

```text
the scenario is retired
the scenario becomes assertion-only
the scenario is merged
exact output is no longer the intended contract
```

Removal requires coordinated updates to:

```text
project.toml
scenario documentation
project interfile lock
validation specification
test coverage matrix
release criteria
tests
migration or changelog notes
```

The updater must not delete a gold because a candidate is empty.

---

## 32. Renaming a scenario or gold

Renaming is a breaking project contract change.

Required updates:

```text
scenario filename
gold filename
project.toml
gold header
scenario markers where ID-dependent
input references
project contract lock
validation documents
tests
migration notes
```

No rename may be inferred automatically from similar content.

---

## 33. Atomic replacement

Accepted updates use atomic replacement.

Required sequence:

```text
write sibling temporary file
flush and close
validate temporary file
replace destination atomically
re-read destination
validate final bytes
record final hash
```

Example temporary name:

```text
project/validation/gold/.<scenario-id>.gold.tmp
```

Rules:

- the temporary file remains inside the gold directory;
- the name is collision-safe;
- failure preserves the previous valid gold;
- temporary files are not discovered as gold;
- unsafe symlink targets are rejected;
- destination containment is verified.

---

## 34. Read-only ordinary validation

Ordinary validation:

```text
reads gold
normalizes current scenario output
compares output with gold
writes diff evidence in the run directory
returns OK, FAIL, ERROR, or SKIPPED
does not modify project gold
```

Outcome mapping:

| Condition | Status |
|---|---|
| Exact match | `OK` |
| Valid output differs | `FAIL` |
| Required gold missing | `ERROR` |
| Gold malformed | `ERROR` |
| Normalization failure | `ERROR` |
| Scenario intentionally not run | `SKIPPED` |

A mismatch must not automatically enter update mode.

---

## 35. Version-control policy

Required gold files are version-controlled.

An accepted update should be committed with:

```text
the related source/scenario change
the gold diff
relevant documentation
tests
```

Recommended commit subject:

```text
project: update <scenario-id> gold after <reason>
```

Change description:

```text
Scenario:
Reason:
Related source/specification change:
GF version:
Normalization version:
Old hash:
New hash:
Sections changed:
Linguistic review:
Release impact:
Validation run:
```

Do not commit an unexplained gold-only change.

---

## 36. Dirty-worktree policy

Recommended behavior:

- warn about unrelated modifications;
- refuse unsafe bulk updates unless explicitly overridden;
- never reset or discard user changes;
- record whether the workspace was dirty;
- prefer clean workspaces for release baseline updates.

A dirty workspace may be allowed for targeted development, but provenance must remain clear.

---

## 37. Backup and rollback

Version control is the primary rollback mechanism.

Run-local evidence may include:

```text
<scenario-id>.previous.gold
<scenario-id>.candidate.gold
<scenario-id>.gold.diff
```

These belong in the run directory.

Do not accumulate `.bak` files in the project gold directory.

After a failed atomic update, the previous valid gold must remain intact.

---

## 38. Batch updates

For multiple scenarios:

1. resolve the explicit selection;
2. validate all contracts;
3. execute each scenario independently;
4. build one candidate per scenario;
5. save one diff per scenario;
6. obtain one decision per scenario unless approved batch acceptance is explicit;
7. atomically write accepted files;
8. leave rejected files unchanged;
9. summarize every outcome.

Summary categories:

```text
unchanged
accepted
rejected
errored
skipped
```

One failure must not silently accept another scenario.

Per-file atomicity is sufficient; a complex cross-file transaction is not required.

---

## 39. Partial batch failure

If one scenario fails:

- mark it `ERROR`;
- preserve its evidence;
- do not write its gold;
- continue independent scenarios when safe;
- return a non-success command result;
- distinguish rejection from error.

Recommended exit policy:

```text
0 all requested updates unchanged or accepted
1 at least one update rejected or dry-run difference found
2 invalid arguments or configuration
3 execution, normalization, write, or verification error
130 cancelled
```

The definitive registry belongs to `EXIT_CODES.md`.

---

## 40. Recommended result model

```python
@dataclass(frozen=True, slots=True)
class GoldUpdateResult:
    scenario_id: str
    action: str
    status: str
    current_gold_path: str | None
    candidate_path: str
    diff_path: str | None
    old_hash: str | None
    new_hash: str
    normalization_version: str
    accepted: bool
    written: bool
    message: str
```

Recommended actions:

```text
unchanged
create
update
reject
skip
error
```

Persisting this model requires a deliberate schema change.

---

## 41. Update evidence

Record:

```text
run ID
timestamp
project ID
scenario ID
scenario path
scenario hash
input hashes
GF executable
GF version
effective GF path
normalization version
stdout path
stderr path
normalized output path
candidate path
diff path
old gold hash
new candidate hash
decision mode
write result
final gold hash
```

Decision modes:

```text
interactive
explicit_accept
ci_approved
dry_run
```

Do not record credentials or full environment dumps.

---

## 42. GUI workflow

A GUI **Update Gold** action must:

- be separate from validation;
- show project and scenario identity;
- show raw evidence locations;
- show a complete diff;
- default to reject;
- require explicit confirmation;
- display GF and normalization versions;
- display final write status;
- never accept by closing a dialog;
- never persist an “always accept” preference.

A generic auto-fix action must not rewrite gold files.

---

## 43. Release policy

Before release, each required gold scenario must have:

```text
registered scenario
existing valid gold
current normalization version
successful scenario execution
completed required markers
exact gold match
no pending candidate
committed reviewed gold changes
```

A release command must never imply gold update.

If a required gold differs:

1. release fails;
2. maintainer runs `gold update`;
3. maintainer reviews and commits;
4. release validation runs again.

---

## 44. Security requirements

Gold updating writes source-controlled files.

Required protections:

```text
validate project root
validate gold-root containment
reject path traversal
reject unsafe symlinks
reject scenario-controlled destination paths
avoid shell-based file replacement
reject unsafe shell escapes
redact secrets
enforce output limits
write only selected gold paths
never overwrite .gf or .gfs source
```

A security violation stops the operation.

---

## 45. Output-size policy

Gold output must remain reviewable.

If the normalized candidate exceeds the configured maximum:

```text
status: ERROR
reason: candidate exceeds output limit
```

The updater must not truncate a candidate and accept the truncated content.

Large scenarios should be split or replaced with targeted assertions.

---

## 46. Nondeterminism policy

Exact gold requires deterministic normalized output.

Potential nondeterminism:

```text
random generation
unordered variants
timestamps
temporary IDs
filesystem ordering
locale-dependent output
concurrent output
GF-version-specific ordering
```

Corrective actions:

- stabilize the source;
- sort only when order is explicitly non-semantic;
- use a documented seed when supported;
- switch to assertions when exact output is inappropriate;
- never repeatedly update gold to chase unstable output.

---

## 47. Whitespace and Unicode review

Reviewers must inspect:

```text
leading and trailing whitespace
multiple spaces
non-breaking spaces
combining marks
Unicode normalization forms
directional marks
apostrophe variants
hyphen variants
quotation marks
line endings
final newline
```

The updater should provide escaped or code-point detail for suspicious differences.

Language-significant Unicode must not be normalized away.

---

## 48. Orphan detection

The project checker should detect:

```text
gold without registered scenario
required gold missing
scenario referencing wrong gold
duplicate scenario ID
duplicate gold ownership
header/filename mismatch
unsupported normalization version
unreferenced legacy gold
```

Orphans are reported, not deleted automatically.

---

## 49. Drift indicators

Probable drift exists when:

- gold changes during normal validation;
- a gold changes without an explained project change;
- scenario ID differs from the gold header;
- validator and updater normalize differently;
- raw output is unavailable;
- a candidate exists despite missing markers;
- a missing gold is auto-created;
- bulk update includes unregistered files;
- GUI and CLI use different update logic;
- local paths leak into gold;
- output changes every run;
- meaningful linguistic output disappears during normalization;
- acceptance occurs without a diff;
- routine CI commits gold;
- stale compile artifacts produce the candidate;
- release passes with unreviewed gold changes.

Every drift indicator requires contract review.

---

## 50. Tests

Recommended unit tests:

```text
tests/scenarios/test_gold_candidate.py
tests/scenarios/test_gold_diff.py
tests/scenarios/test_gold_update.py
tests/scenarios/test_gold_atomic_write.py
tests/scenarios/test_gold_security.py
tests/scenarios/test_gold_cli.py
```

Required cases:

```text
unchanged gold
modified gold
new gold
missing required gold
malformed gold
scenario ID mismatch
normalization mismatch
balanced and missing markers
normalization failure
timeout
launch failure
dry run
default rejection
explicit acceptance
atomic failure preserving old gold
final hash verification
path traversal
symlink escape
UTF-8
CRLF to LF
final newline
empty gold policy
large candidate rejection
batch partial failure
ordinary validation never writes gold
```

Contract tests:

```text
tests/contracts/test_gold_read_only_contract.py
tests/contracts/test_gold_update_contract.py
tests/contracts/test_normalization_contract.py
tests/contracts/test_artifact_ownership.py
```

They must prove one execution path, one normalizer, diff-before-write, explicit acceptance, and atomic replacement.

---

## 51. Integration tests with real GF

Use a temporary language-neutral fixture project to test:

```text
stable scenario output
candidate construction
exact comparison
intentional source change
reviewable diff
accepted update
subsequent passing validation
diagnostic preventing update
timeout preventing update
paths with spaces
UTF-8 output
```

Real-GF tests must never modify the active project gold directory.

---

## 52. Update checklist

```text
[ ] Correct active project confirmed
[ ] Correct scenario confirmed
[ ] Correct script confirmed
[ ] Correct entrypoint confirmed
[ ] Correct inputs confirmed
[ ] Supported GF executable/version confirmed
[ ] Effective GF path recorded
[ ] Scenario completed without timeout
[ ] Required markers completed
[ ] Raw stdout and stderr preserved
[ ] Normalization version confirmed
[ ] Candidate validated
[ ] Complete diff reviewed
[ ] Linguistic output reviewed
[ ] Variant and ambiguity changes reviewed
[ ] Unstable noise absent
[ ] Source/specification reason documented
[ ] Related documentation reviewed
[ ] Release impact reviewed
[ ] Atomic write succeeded
[ ] Final hash verified
[ ] Version-control change reviewed
[ ] Release validation rerun when required
```

---

## 53. Change record template

```text
Scenario:
Gold path:
Action: create | update | remove | rename
Reason:
Related source change:
Related scenario change:
GF executable:
GF version:
Normalization version:
Old hash:
New hash:
Sections changed:
Linguistic review:
Nondeterminism review:
Documentation updated:
Release impact:
Validation run ID:
Reviewer:
```

---

## 54. Implementation ownership

Recommended final ownership:

```text
app/audit/scenario_runner.py
    executes scenarios
    verifies markers
    preserves raw evidence
    normalizes output
    compares gold

app/gold/update_service.py
    constructs candidates
    validates candidates
    computes diffs
    coordinates acceptance
    writes atomically
    records update evidence

app/main_cli.py
    parses gold commands
    calls the update service

app/gui/
    presents update review
    calls the update service

app/utils/io_utils.py
    provides atomic write primitives
```

The exact service path may change only through a component-map and interfile-contract update.

The service must not duplicate scenario execution or normalization.

---

## 55. Dependency rules

Prohibited:

```text
ordinary validation → gold writer
report writer → gold writer
normalizer → project file replacement
scenario script → gold destination selection
gold file → source generation logic
GUI widget → direct replacement
CLI parser → direct replacement
```

Expected:

```text
CLI/GUI
    → gold update service
    → scenario runner
    → normalizer
    → diff builder
    → atomic I/O

ordinary validation
    → scenario runner
    → gold reader/comparator
```

---

## 56. Legacy migration

Legacy projects may contain:

```text
unversioned gold
raw-output gold
CRLF gold
headerless gold
gold with old names
manual expected-output text
```

Migration must:

1. preserve the original;
2. identify the owning scenario;
3. run the current scenario;
4. normalize with the current version;
5. construct a canonical candidate;
6. show the migration diff;
7. require explicit acceptance;
8. write atomically;
9. record losses or uncertainty.

Legacy content must not simply receive a new header and be declared valid.

---

## 57. Failure behavior

| Failure | Result |
|---|---|
| Invalid project | `ERROR`, no write |
| Unknown scenario | `ERROR`, no write |
| Missing script | `ERROR`, no write |
| Unsupported GF version | `ERROR`, no write |
| Launch failure | `ERROR`, no write |
| Timeout | `ERROR`, no write |
| Missing marker | `ERROR`, no write |
| Normalization failure | `ERROR`, no write |
| Invalid candidate | `ERROR`, no write |
| Dry-run mismatch | Difference reported, no write |
| Reviewer rejects | Rejected, no write |
| Atomic replacement fails | `ERROR`, old gold preserved |
| Final hash mismatch | `ERROR`, recovery required |
| Candidate unchanged | Unchanged, no rewrite |
| Candidate accepted | Created or updated |

---

## 58. Final invariants

Gold updating must preserve:

1. an explicit update command;
2. authoritative project identity;
3. registered scenario identity;
4. one scenario execution path;
5. one versioned normalizer;
6. raw evidence before normalization;
7. valid required markers;
8. canonical candidate schema;
9. a complete saved diff;
10. explicit acceptance;
11. default rejection;
12. atomic replacement;
13. final-byte verification;
14. preservation of the old valid file on failure;
15. read-only ordinary validation;
16. no automatic missing-gold creation;
17. no removal of semantic output;
18. no secret persistence;
19. version-control review;
20. release revalidation.

---

## 59. Final rule

> Update the gold only when the changed output is the intended behavior—not merely the observed behavior.

A gold file is an approved contract.

It must never become a mechanism for making unexplained failures disappear.
