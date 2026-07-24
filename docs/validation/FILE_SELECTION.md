# GF Wordbench — File Selection

**Document ID:** `GF-WB-VALIDATION-FILE-SELECTION`  
**Status:** Normative  
**Canonical path:** `docs/validation/FILE_SELECTION.md`  
**Applies to:** GF source discovery, explicit target resolution, include and exclude filtering, mode-specific target construction, deterministic ordering, and exclusion reporting  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Contract references:** `IFC-WB-001`, `IFC-WB-002`, `IFC-WB-004`  
**Document version:** `1.1.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines how GF Wordbench decides which Grammatical Framework source files belong to one validation run.

File selection is the boundary between resolved configuration and executable validation stages.

It answers:

- where source discovery begins;
- which files are candidates;
- how explicit targets are resolved;
- how `quick`, `checkpoint`, `release`, and `diagnostic` modes differ;
- how glob, include, and exclude rules interact;
- how file limits are applied;
- how duplicate and ambiguous paths are handled;
- how selected and excluded files are ordered;
- which paths are returned to run orchestration;
- which failures are configuration errors rather than ordinary exclusions.

The central rule is:

> A file may be scanned or compiled only when the file selector selected it through the resolved project and run configuration.

---

## 2. Scope

This document governs:

- active-project source-root resolution;
- recursive source enumeration;
- source glob application;
- include-regex application;
- exclude-regex application;
- explicit target-file resolution;
- checkpoint target resolution;
- release-entrypoint target resolution;
- candidate deduplication;
- deterministic ordering;
- `max_files`;
- exclusion reasons;
- module-name expectation derived from filenames;
- selector errors;
- selector tests;
- compatibility with legacy `file` and `all` modes.

This document does not govern:

- source parsing;
- static scan rules;
- GF compilation;
- GF dependency resolution;
- downstream failure classification;
- scenario selection;
- report formatting;
- run-directory creation;
- artifact retention.

### 2.1 Product boundary

File selection operates on exactly one resolved Wordbench workspace, one active project and one validation run.

It MUST NOT:

- discover projects through a Portfolio registry;
- combine source roots from several Wordbench workspaces;
- select files for several active language projects in one run;
- depend on `gf-portfolio` state, storage or configuration.

`gf-portfolio` may invoke independent Wordbench runs and consume their finalized public artifacts. It does not participate in source-file selection.

---

## 3. Authority boundary

### 3.1 Project configuration owns

`project/project.toml` owns:

- the active source directory;
- the source glob;
- the include regex;
- the exclude regex;
- checkpoint target order;
- entrypoint target order.

Canonical configuration fields:

```text
sources.directory
sources.glob
sources.include_regex
sources.exclude_regex
modules.checkpoints
modules.entrypoints
```

### 3.2 Run configuration owns

The resolved `RunConfig` owns:

- canonical validation mode;
- explicit quick-mode target;
- optional diagnostic file limit;
- any documented explicit runtime override.

### 3.3 File-selection component owns

The validation module's file-selection component owns:

- candidate enumeration;
- explicit path resolution;
- file-safety checks;
- include and exclude filtering;
- mode-specific target-set construction;
- deduplication;
- deterministic ordering;
- exclusion-reason construction;
- expected module-name extraction from a filename.

### 3.4 Run orchestration owns

The application run orchestration owns:

- invoking file selection once;
- recording selection counts;
- sending only selected files to later stages;
- preserving selection errors;
- deciding whether a configuration error aborts the run.

Run orchestration MUST NOT duplicate selection rules.

### 3.5 GF owns

GF owns dependency resolution after a selected target is compiled.

A dependency compiled by GF is not automatically a separately selected file.

---

## 4. Core invariants

The file-selection subsystem MUST satisfy all of the following:

```text
[ ] one active project is used
[ ] one resolved source root is used
[ ] every selected target is a regular `.gf` file
[ ] every selected target is inside the allowed source root
[ ] exclude rules take precedence over include rules
[ ] required explicit targets are never silently omitted
[ ] selected files are unique
[ ] selected ordering is deterministic
[ ] excluded files are never compiled
[ ] selection has no source-file side effects
[ ] selection does not invoke GF
[ ] selection does not create run output directories
[ ] selection does not generate reports
```

---

## 5. Canonical terminology

### Candidate file

A filesystem path discovered or explicitly requested for evaluation by the selector.

A candidate is not selected until it passes all applicable rules.

### Selected file

A candidate accepted for the current run.

Selected files may proceed to scanning, fingerprinting, and compilation.

### Excluded file

A discovered candidate intentionally rejected by a documented selection rule.

### Explicit target

A path named directly by quick-mode configuration, checkpoint configuration, or entrypoint configuration.

### Enumerated target

A path found recursively beneath the configured source root using the configured glob.

### Source root

The resolved directory identified by:

```text
sources.directory
```

### Required target

A checkpoint or entrypoint that the selected validation mode requires.

A required target that cannot be selected is a configuration or project error.

### Selection limit

The optional `max_files` cap used only for diagnostic enumeration.

### Exclusion reason

A stable machine-readable identifier explaining why a discovered candidate was not selected.

---

## 6. Canonical configuration

Example:

```toml
[sources]
directory = "lib/src/example"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"

[modules]
checkpoints = [
  "MorphoX.gf",
  "NounX.gf",
  "VerbX.gf",
]
entrypoints = [
  "GrammarX.gf",
  "SyntaxX.gf",
]
```

Runtime selection example:

```json
{
  "mode": "diagnostic",
  "target_file": "",
  "max_files": 0
}
```

---

## 7. Configuration precedence

The selector receives already-resolved configuration.

Canonical precedence:

1. explicit CLI or GUI runtime value;
2. documented project value;
3. application default;
4. configuration error when a required value remains unresolved.

The selector MUST NOT reapply precedence independently.

Legacy fields may map as follows during migration:

| Legacy field | Canonical source |
|---|---|
| `scan_dir` | `sources.directory` |
| `scan_glob` | `sources.glob` |
| `include_regex` | `sources.include_regex` |
| `exclude_regex` | `sources.exclude_regex` |
| `mode = file` | `mode = quick` |
| `mode = all` | `mode = diagnostic` |

Canonical selectors receive only canonical modes.

---

## 8. Source-root resolution

The source root is resolved from:

```text
project_root / sources.directory
```

Algorithm:

```text
1. resolve project root
2. require project root to exist and be a directory
3. require sources.directory to be project-relative
4. join project root and sources.directory
5. resolve the resulting path
6. require the result to remain inside project root
7. require the result to exist
8. require the result to be a directory
```

Canonical pseudocode:

```python
project_root = Path(config.project_root).resolve(strict=True)
source_root = (project_root / config.sources_directory).resolve(strict=True)

require_is_relative_to(source_root, project_root)
require_directory(source_root)
```

### 8.1 Empty source directory

An empty `sources.directory` MAY mean the project root only when the project schema explicitly permits it.

Canonical project templates SHOULD use an explicit non-empty source directory.

### 8.2 Absolute source directory

Canonical `project.toml` MUST NOT store an absolute `sources.directory`.

An absolute legacy value may be migrated only through an explicit compatibility layer.

### 8.3 Escaping path

Values containing traversal such as:

```text
../other-project
```

MUST be rejected when resolution escapes the active project root.

### 8.4 Symlinks

In strict mode, a source-root symlink resolving outside the project root MUST be rejected.

A project that intentionally uses an external source root requires an explicit configured alias and containment contract. It MUST NOT be enabled through an accidental symlink.

---

## 9. Mode normalization

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Legacy aliases:

```text
file → quick
all  → diagnostic
```

Alias conversion belongs to configuration loading or migration.

`file_selector.py` SHOULD reject unknown and unresolved legacy modes rather than guessing.

---

# 10. Quick-mode selection

## 10.1 Purpose

Quick mode provides fast validation of one explicitly requested source file.

## 10.2 Required input

```text
mode = quick
target_file = non-empty path
```

## 10.3 Cardinality

Quick mode MUST select exactly one file.

Possible outcomes:

| Condition | Outcome |
|---|---|
| exactly one valid target | select it |
| target missing | configuration error |
| target resolves outside source root | configuration error |
| target is excluded | configuration error |
| target is ambiguous | configuration error |
| target is not `.gf` | configuration error |
| more than one match | configuration error |

Quick mode MUST NOT silently fall back to diagnostic enumeration.

## 10.4 Dependencies

GF may compile dependencies required by the quick target.

Those dependency files are not separately selected unless another mode or target list selected them explicitly.

## 10.5 `max_files`

`max_files` does not reduce quick mode below one target.

Configuration rule:

```text
max_files = 0 or 1
```

A larger value has no effect and SHOULD produce a configuration warning.

---

# 11. Checkpoint-mode selection

## 11.1 Purpose

Checkpoint mode validates the ordered development checkpoints declared by the active project.

## 11.2 Source list

Canonical source:

```text
modules.checkpoints
```

## 11.3 Ordering

Checkpoint order is the declared configuration order.

The selector MUST NOT alphabetically reorder checkpoints.

## 11.4 Required-target behavior

Every configured checkpoint is required for checkpoint mode unless the project schema later introduces an explicit optional-checkpoint field.

For each checkpoint:

```text
resolve
validate
apply include/exclude policy
deduplicate while preserving first occurrence
```

A missing, invalid, excluded, ambiguous, or outside-root checkpoint is a configuration or project error.

It MUST NOT be converted into an ordinary silent exclusion.

## 11.5 Empty checkpoint list

An empty checkpoint list is allowed only during project bootstrap.

Running checkpoint mode with an empty list produces a clear configuration error unless an explicit bootstrap policy allows an empty pass.

An empty checkpoint list MUST NOT yield a misleading successful checkpoint run.

## 11.6 `max_files`

`max_files` MUST NOT truncate checkpoint targets.

Configuration rule:

```text
max_files must be 0 in checkpoint mode
```

A non-zero value is rejected because it could weaken the checkpoint contract.

---

# 12. Release-mode selection

## 12.1 Purpose

Release mode selects every source target required to prove release prerequisites before PGF construction and release scenarios.

## 12.2 Source lists

Canonical sources:

```text
modules.checkpoints
modules.entrypoints
```

## 12.3 Ordered union

Release selection is the ordered union:

```text
checkpoints
then entrypoints not already selected
```

Example:

```toml
checkpoints = [
  "MorphoX.gf",
  "GrammarX.gf",
]

entrypoints = [
  "GrammarX.gf",
  "SyntaxX.gf",
]
```

Selected order:

```text
MorphoX.gf
GrammarX.gf
SyntaxX.gf
```

## 12.4 Required targets

Every release target is required.

A target that cannot be resolved or selected is a release-configuration failure.

Release mode MUST NOT:

- silently omit an excluded entrypoint;
- replace a missing entrypoint with a same-named file elsewhere;
- truncate the target list;
- use diagnostic enumeration as a substitute;
- infer release targets from old `.gfo` or `.pgf` artifacts.

## 12.5 `max_files`

`max_files` MUST be `0` in release mode.

A non-zero value is a configuration error.

Release completeness cannot be weakened by a runtime file cap.

---

# 13. Diagnostic-mode selection

## 13.1 Purpose

Diagnostic mode enumerates the active language source tree broadly and deterministically.

## 13.2 Enumeration

Candidates are discovered recursively under the source root using:

```text
Path.rglob(sources.glob)
```

Conceptual algorithm:

```python
candidates = [
    path.resolve()
    for path in source_root.rglob(source_glob)
    if path.is_file()
]
```

## 13.3 Filter order

The final order of operations is:

```text
1. enumerate all glob candidates
2. normalize paths
3. deduplicate candidates
4. apply hard file-safety checks
5. apply exclude regex
6. apply include regex
7. sort accepted candidates deterministically
8. apply max_files to accepted candidates
9. mark overflow candidates as excluded_by_limit
```

Applying `max_files` before filtering is prohibited because excluded files could consume the selection budget.

## 13.4 Empty result

A diagnostic selection with no selected files is not automatically successful.

The orchestrator reports one of:

- valid empty project during explicit bootstrap;
- no files matched glob;
- every candidate was excluded;
- invalid filter configuration.

The mode policy decides whether an intentionally empty bootstrap project may pass.

## 13.5 `max_files`

Canonical semantics:

```text
0 = unlimited
positive integer = maximum accepted diagnostic files
negative integer = invalid configuration
```

The limit applies after include and exclude rules.

Candidates beyond the limit receive:

```text
excluded_by_limit
```

This preserves complete selection accounting.

---

# 14. Explicit target resolution

Explicit target resolution applies to:

- quick target;
- checkpoint item;
- entrypoint item.

The accepted resolution strategy differs slightly by target source.

## 14.1 Quick target resolution order

For a quick-mode user target:

```text
1. absolute path, when supplied
2. project-root-relative path
3. source-root-relative path
4. unique basename fallback, only when no direct path exists
```

Every resolved result must still remain inside the source root.

## 14.2 Configured checkpoint and entrypoint resolution

Configured module targets resolve as source-root-relative paths.

Example:

```text
GrammarX.gf
```

resolves to:

```text
<source-root>/GrammarX.gf
```

Example:

```text
syntax/SyntaxX.gf
```

resolves to:

```text
<source-root>/syntax/SyntaxX.gf
```

Configured targets MUST NOT use basename search fallback.

Project configuration must identify one stable path.

## 14.3 Absolute quick target

An absolute quick target is permitted as a user convenience only when the resolved file is inside the active source root.

The persisted canonical target path is project-relative.

## 14.4 Basename fallback

Basename fallback is permitted only for quick-mode interactive convenience.

Example:

```text
GrammarX.gf
```

If no direct path exists, the selector may search:

```text
source_root.rglob("GrammarX.gf")
```

Outcomes:

- one match: select candidate for later validation;
- zero matches: not found error;
- several matches: ambiguous target error.

Basename fallback MUST NOT choose the first match.

## 14.5 Case behavior

On case-insensitive filesystems, resolution follows filesystem identity.

On case-sensitive filesystems, incorrect case may produce a not-found error.

GF Wordbench MUST preserve the actual resolved filename casing in runtime evidence.

---

# 15. Candidate hard checks

Every candidate must pass these checks before regex filtering.

Canonical order:

```text
1. exists
2. is a regular file
3. has `.gf` suffix
4. resolves inside project root
5. resolves inside source root
6. is readable according to platform policy
```

Canonical exclusion reasons:

```text
missing_file
not_a_file
not_gf_file
outside_project_root
outside_source_root
unreadable_file
```

Explicit required targets failing a hard check raise an error.

Enumerated candidates failing a hard check are excluded and recorded when the filesystem operation permits reliable identification.

---

# 16. Glob semantics

## 16.1 Canonical field

```text
sources.glob
```

## 16.2 Default

```text
*.gf
```

## 16.3 Recursion

The selector applies the glob recursively beneath the source root.

With `rglob`, `*.gf` includes `.gf` files in nested directories.

## 16.4 Empty glob

An empty canonical glob is invalid.

A legacy empty value may migrate to:

```text
*.gf
```

New project files MUST store the explicit value.

## 16.5 Glob versus regex

The glob determines which paths become enumerated candidates.

Regex rules then decide whether those candidates are selected.

A path not matched by the glob does not become an excluded entry because it was never a candidate.

## 16.6 Hidden directories

Hidden directories are traversed only when the glob and platform traversal expose them.

Projects SHOULD use `exclude_regex` or a future explicit directory-exclusion policy when hidden source subtrees must be ignored.

The selector MUST not hardcode language-specific hidden-directory assumptions.

---

# 17. Regex semantics

## 17.1 Inputs

Regex rules are evaluated against both:

```text
file name
project-relative POSIX path
```

Example candidate:

```text
C:\work\project\lib\src\example\syntax\GrammarX.gf
```

Evaluation strings:

```text
GrammarX.gf
lib/src/example/syntax/GrammarX.gf
```

## 17.2 Exclude precedence

Exclude is evaluated before include.

Canonical logic:

```python
if exclude_matches(name_or_path):
    exclude("excluded_by_regex")
elif include_exists and not include_matches(name_or_path):
    exclude("not_matched_by_include_regex")
else:
    include()
```

A candidate matching both rules is excluded.

## 17.3 Empty regex

An empty or whitespace-only regex means no rule.

```text
include_regex empty → all glob candidates may proceed
exclude_regex empty → no regex exclusion
```

## 17.4 Regex compilation

Regexes are compiled once per selection operation.

An invalid regex produces a configuration error before file processing begins.

The selector MUST NOT ignore a malformed regex.

## 17.5 Case sensitivity

Canonical regex matching is case-sensitive unless the pattern itself requests another behavior.

Example case-insensitive pattern:

```text
(?i)\.gf$
```

The framework MUST NOT silently inject case-insensitive behavior.

## 17.6 Search semantics

Canonical matching uses regex search against filename or relative path.

Patterns requiring full-string matching should use anchors:

```text
^
$
```

## 17.7 Language neutrality

Framework defaults MUST NOT contain names tied to one active language.

Copy, backup, temporary, and disabled-file conventions may be represented by generic template defaults, but the active project owns its final policy.

---

# 18. Template default filters

Generic project template:

```toml
[sources]
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"
```

These are defaults, not GF language rules.

Projects may need Unicode module filenames or different naming conventions.

When Unicode module names are supported, the include regex must be changed deliberately and tested.

Whitespace in any path MUST NOT be globally prohibited merely because Windows paths may contain spaces.

A project may exclude source filenames containing spaces through explicit policy, but framework paths and directory names must support spaces.

---

# 19. Deduplication

The same file may enter selection through:

- duplicate configuration entries;
- checkpoint and entrypoint overlap;
- equivalent relative path spellings;
- filesystem aliases;
- quick resolution alternatives.

Deduplication uses resolved filesystem identity.

Identity key:

```python
os.path.normcase(str(path.resolve()))
```

On case-sensitive platforms, exact resolved path identity is preserved.

## 19.1 Ordering during deduplication

For explicit ordered lists:

```text
preserve first occurrence
```

For diagnostic enumeration:

```text
deduplicate before deterministic sorting
```

## 19.2 Duplicate configuration

Duplicate checkpoint or entrypoint entries SHOULD produce a configuration warning.

They do not create duplicate validation work.

## 19.3 Symlink aliases

Strict mode SHOULD reject aliases that resolve outside the source root.

Two aliases resolving to the same allowed file produce one selected file.

---

# 20. Deterministic ordering

Selection order must be reproducible for the same project, configuration, platform semantics, and filesystem contents.

## 20.1 Quick mode

One target only.

## 20.2 Checkpoint mode

Declared checkpoint order.

## 20.3 Release mode

Ordered union:

```text
declared checkpoints
then new declared entrypoints
```

## 20.4 Diagnostic mode

Sort by normalized project-relative POSIX path using:

```python
(relative_path.casefold(), relative_path)
```

The exact path is the tie-breaker.

## 20.5 Excluded files

Excluded entries SHOULD be ordered by:

```text
discovery or explicit-target order for explicit lists
normalized path order for diagnostic enumeration
```

Reports must not apply a conflicting undocumented order.

---

# 21. `max_files`

## 21.1 Canonical meaning

```text
0 = no limit
N > 0 = select at most N accepted diagnostic candidates
N < 0 = invalid
```

## 21.2 Allowed modes

| Mode | Allowed |
|---|---:|
| `quick` | tolerated but does not change one-target cardinality |
| `checkpoint` | prohibited when non-zero |
| `release` | prohibited when non-zero |
| `diagnostic` | supported |

## 21.3 Limit timing

The limit is applied after:

- enumeration;
- hard checks;
- exclude regex;
- include regex;
- deterministic ordering.

## 21.4 Overflow accounting

Accepted candidates beyond the limit are excluded with:

```text
excluded_by_limit
```

They count as seen and excluded.

## 21.5 Reproducibility

Because sorting occurs before limiting, the same source tree and configuration select the same first `N` files.

---

# 22. Exclusion reasons

Canonical v1 exclusion reasons:

```text
missing_file
not_a_file
not_gf_file
outside_project_root
outside_source_root
unreadable_file
excluded_by_regex
not_matched_by_include_regex
excluded_by_limit
duplicate_candidate
```

## 22.1 Stable semantics

| Reason | Meaning |
|---|---|
| `missing_file` | candidate no longer exists |
| `not_a_file` | candidate exists but is not a regular file |
| `not_gf_file` | suffix is not `.gf` |
| `outside_project_root` | resolved candidate escapes the active project |
| `outside_source_root` | resolved candidate is not under the configured source root |
| `unreadable_file` | platform access policy cannot read the candidate |
| `excluded_by_regex` | exclude regex matched filename or relative path |
| `not_matched_by_include_regex` | include regex existed and matched neither |
| `excluded_by_limit` | accepted diagnostic candidate exceeded `max_files` |
| `duplicate_candidate` | candidate resolves to a previously processed identity |

## 22.2 Empty reason

Selected files have no exclusion reason.

An excluded entry MUST have a non-empty canonical reason.

## 22.3 Human explanations

Reports may map stable reasons to human text.

Example:

```text
excluded_by_regex → Excluded by project regex.
```

Machine consumers use the stable identifier, not localized prose.

## 22.4 Explicit-target escalation

For a required explicit target, an exclusion condition becomes an error.

Example:

```text
checkpoint GrammarX.gf → excluded_by_regex
```

Outcome:

```text
configuration error:
required checkpoint is excluded by project selection policy
```

The selector MUST NOT return a successful partial checkpoint list.

---

# 23. Selection result contract

The public file-selection API is:

```python
def select_files(
    run_config: RunConfig,
) -> tuple[list[Path], list[ExcludedFileEntry]]:
    ...
```

Where:

```python
@dataclass(frozen=True, slots=True)
class ExcludedFileEntry:
    file_path: Path
    excluded_reason: str
```

## 23.1 Selected paths

Runtime selected paths are:

- absolute;
- resolved;
- unique;
- ordered deterministically;
- valid at selection time.

## 23.2 Excluded paths

Excluded entries contain:

- resolved absolute path when available;
- canonical exclusion reason.

## 23.3 Persisted representation

Persisted project-owned paths are project-relative and use `/`.

The JSON report writer, not the selector, owns serialization.

# 24. Selection counts

Canonical totals:

```text
files_seen
files_included
files_excluded
```

In diagnostic mode:

```text
files_seen = files_included + files_excluded
```

Candidates not matched by the discovery glob are not seen.

In explicit modes, configured targets count as seen once they enter resolution.

## 24.1 Required-target configuration errors

When selection aborts before producing a complete result, the run may record:

- attempted target count;
- selector error;
- partial evidence.

It MUST NOT fabricate coherent final selection totals when selection did not complete.

## 24.2 Noise count

`excluded_noise` may equal or summarize documented exclusion categories according to result-model policy.

The selector supplies reasons; the result builder owns aggregate reporting fields.

---

# 25. Module-name expectation

Public helper:

```python
def extract_module_name(file_path: Path) -> str:
    return file_path.stem
```

Example:

```text
GrammarX.gf → GrammarX
```

This helper returns the expected module name derived from the filename.

It does not parse or prove the module declaration inside the GF source.

A mismatch between filename and declared GF module identity must be detected by:

- GF compilation;
- a dedicated source-identity check;
- or another documented validation stage.

Module-name extraction MUST remain independent of report formatting.

---

# 26. Error model

Selection failures are divided into:

## 26.1 Configuration errors

Examples:

- unknown mode;
- malformed include regex;
- malformed exclude regex;
- missing project root;
- missing source root;
- source root outside project;
- negative `max_files`;
- non-zero release limit;
- missing checkpoint configuration;
- missing entrypoint configuration.

Canonical result:

```text
validation_status = ERROR
error_kind = CONFIG
```

## 26.2 Filesystem errors

Examples:

- permission denied;
- unreadable directory;
- race during enumeration;
- broken symlink;
- inaccessible target.

Canonical result:

```text
validation_status = ERROR
error_kind = IO
```

## 26.3 Explicit target errors

Examples:

- quick target missing;
- quick target ambiguous;
- checkpoint outside root;
- required target excluded;
- entrypoint not a `.gf` file.

Canonical result:

```text
validation_status = ERROR
error_kind = CONFIG or IO
```

## 26.4 Ordinary exclusions

Examples:

- backup file matched by diagnostic glob;
- candidate rejected by include regex;
- candidate beyond diagnostic limit.

Ordinary exclusions do not by themselves make diagnostic selection fail.

---

# 27. Race conditions

The filesystem may change after selection.

Possible race:

```text
selected file exists
    → file deleted before scan or compile
```

Policy:

- selector validates at selection time;
- later stages validate their own required preconditions;
- a later missing file becomes a stage error;
- selector results are not silently rewritten;
- raw run evidence records the failure.

The selector MUST NOT hold open every selected file merely to prevent changes.

Source fingerprints provide later source identity.

---

# 28. Source immutability

The selector is read-only.

It MUST NOT:

- modify source contents;
- rename files;
- delete backups;
- move excluded files;
- create `.gfo`;
- create run directories;
- update `project.toml`;
- change application state;
- update project records;
- normalize source files;
- follow a remediation action automatically.

Selection reports facts and decisions only.

---

# 29. Security requirements

Required protections:

- resolved candidates remain inside allowed roots;
- traversal escapes are rejected;
- NUL characters are rejected;
- configured regexes are compiled before enumeration;
- untrusted paths are not executed;
- symlink behavior is explicit;
- quick basename fallback never selects among several matches;
- project configuration cannot select arbitrary external files silently;
- selected paths are passed as path objects, not shell fragments;
- exclusion prose is escaped by report writers.

## 29.1 Regex denial of service

Project regexes are trusted project configuration, but pathological patterns can still be expensive.

The framework SHOULD:

- compile patterns once;
- avoid applying regexes to unbounded file contents;
- apply them only to short filenames and relative paths;
- document that project maintainers own regex quality.

Regex timeout is outside this contract and requires a coordinated contract change if introduced.

---

# 30. Windows behavior

GF Wordbench must support:

- drive letters;
- paths containing spaces;
- Unicode paths;
- case-insensitive filesystem identity;
- backslashes in runtime paths;
- POSIX separators in persisted relative paths.

Example quick target:

```text
C:\mycode\GF Project\lib\src\example\GrammarX.gf
```

It must remain one path value.

The selector MUST NOT reject a file merely because a parent directory contains spaces.

Generated path keys and reports normalize separately.

---

# 31. Unicode behavior

Unicode may occur in:

- project paths;
- directory names;
- source filenames;
- project-relative paths.

The selector:

- uses Python path APIs;
- preserves actual path text;
- serializes through the report layer;
- does not encode paths manually as ASCII.

The default include regex may intentionally exclude Unicode module names.

Projects supporting Unicode module names must define a compatible include rule and test it.

---

# 32. Hidden and generated source artifacts

The source root may contain:

- `.gfo`;
- `.pgf`;
- `.out`;
- `.log`;
- editor backups;
- temporary `.gf` copies.

The `.gf` suffix hard check prevents non-source artifacts from selection.

Backup or copied `.gf` files require an explicit exclude policy.

Generated run directories SHOULD remain outside the active source root.

The selector MUST NOT hardcode a particular editor’s backup naming beyond generic template defaults.

---

# 33. Interaction with scanning

Only selected files are sent to the static scanner.

The scanner does not decide whether a file belongs to the run.

An excluded candidate:

- is not scanned;
- has no scan result;
- may appear in exclusion reporting.

A scan finding MUST NOT retroactively remove a selected file.

---

# 34. Interaction with compilation

Only selected files are sent to the compiler.

The compiler:

- receives one selected path at a time;
- does not reapply include and exclude regexes;
- may cause GF to compile dependencies;
- preserves compile evidence.

A dependency outside the selected set may appear in GF diagnostics or `.gfo` artifacts, but it does not become selected retroactively.

---

# 35. Interaction with classification

The selector does not classify failures as:

```text
direct
downstream
ambiguous
```

It provides the deterministic selected set.

The classifier may use:

- selected file identities;
- module names;
- compile diagnostics;
- dependency references.

Excluded files are normally outside compile-cascade classification.

---

# 36. Interaction with reports

Reports consume selector-derived counts and exclusion records.

Reports MUST NOT:

- re-enumerate the source tree;
- rerun regexes;
- invent exclusion reasons;
- select additional files;
- reconstruct a different ordering.

Human reports may summarize exclusions.

Machine reports use stable paths and reason identifiers where persisted.

---

# 37. Interaction with project configuration

A project configuration change can alter selection.

Breaking or review-significant examples:

- changing `sources.directory`;
- changing recursive glob scope;
- changing include semantics;
- changing exclude semantics;
- reordering checkpoints;
- adding or removing entrypoints;
- renaming a source module;
- moving a configured target into a subdirectory.

Such changes require review of:

```text
project.toml
module dependency map
validation specification
project interfile contract lock
gold-backed scenarios where entrypoints change
selection tests
release criteria
```

---

# 38. Legacy behavior and migration

The predecessor GF Audit selector:

- recognizes `file` and non-`file` behavior;
- returns absolute selected paths;
- records `ExcludedFileEntry`;
- evaluates regexes against filename and project-relative path;
- gives exclude precedence;
- sorts paths case-insensitively;
- supports unique basename fallback;
- applies `max_files` during enumeration before regex filtering;
- may represent outside-project paths as absolute matching strings.

The GF Wordbench contract defines these canonical behaviors:

| Legacy GF Audit behavior | Canonical Wordbench behavior |
|---|---|
| `file` | normalized to `quick` before selection |
| `all` or other branch | explicit `diagnostic` only |
| non-file modes treated alike | distinct checkpoint, release, diagnostic logic |
| `max_files` before filters | limit after accepted diagnostic sorting |
| outside-project relative fallback | outside allowed roots rejected |
| configured targets may rely on broad search | source-root-relative exact paths |
| no release limit prohibition | release cannot be truncated |
| duplicate candidates silently ignored | deterministic dedupe; optional recorded reason |
| source-root policy partly implicit | explicit project-root and source-root containment |

Migration tests MUST cover both alias loading and canonical selector behavior.

---

# 39. Reference selection flow

```python
def select_files(run_config: RunConfig) -> tuple[list[Path], list[ExcludedFileEntry]]:
    config = validate_selection_config(run_config)
    project_root = resolve_project_root(config)
    source_root = resolve_source_root(project_root, config.sources_directory)

    match config.mode:
        case "quick":
            targets = resolve_quick_targets(config, project_root, source_root)
            return select_required_targets(targets, config, project_root, source_root)

        case "checkpoint":
            targets = resolve_configured_targets(
                config.checkpoints,
                source_root,
            )
            return select_required_targets(targets, config, project_root, source_root)

        case "release":
            target_specs = ordered_unique([
                *config.checkpoints,
                *config.entrypoints,
            ])
            targets = resolve_configured_targets(target_specs, source_root)
            return select_required_targets(targets, config, project_root, source_root)

        case "diagnostic":
            candidates = enumerate_candidates(source_root, config.source_glob)
            selected, excluded = filter_candidates(
                candidates,
                config,
                project_root,
                source_root,
            )
            return apply_diagnostic_limit(selected, excluded, config.max_files)

        case _:
            raise SelectionConfigError(...)
```

This is a behavioral reference, not a mandatory function decomposition.

---

# 40. Internal helper boundary

The file-selection component uses cohesive helpers such as:

```python
select_files(...)
filter_candidate_files(...)
is_included_file(...)
extract_module_name(...)
resolve_project_root(...)
resolve_source_root(...)
resolve_quick_target(...)
resolve_configured_targets(...)
enumerate_candidate_files(...)
compile_optional_regex(...)
apply_diagnostic_limit(...)
ordered_unique_paths(...)
```

Avoid unnecessary architecture such as:

- a plugin system for file selectors;
- a rule class for each exclusion;
- a workflow engine;
- a database-backed file inventory;
- persistent indexing before scale requires it;
- a custom glob language;
- a custom regex engine.

The standard path, glob, and regex libraries are sufficient.

---

# 41. Required unit tests

Minimum selection tests:

```text
test_quick_selects_exact_target
test_quick_requires_target
test_quick_rejects_missing_target
test_quick_rejects_ambiguous_basename
test_quick_accepts_unique_basename
test_quick_rejects_target_outside_project
test_quick_rejects_target_outside_source_root
test_quick_rejects_excluded_target
test_checkpoint_preserves_declared_order
test_checkpoint_rejects_missing_target
test_checkpoint_rejects_excluded_target
test_checkpoint_rejects_nonzero_max_files
test_release_selects_ordered_union
test_release_deduplicates_checkpoint_entrypoint_overlap
test_release_requires_entrypoints
test_release_rejects_nonzero_max_files
test_diagnostic_enumerates_recursively
test_diagnostic_applies_glob
test_diagnostic_exclude_precedes_include
test_diagnostic_regex_checks_filename
test_diagnostic_regex_checks_relative_path
test_diagnostic_empty_include_means_no_include_filter
test_diagnostic_empty_exclude_means_no_exclude_filter
test_diagnostic_rejects_invalid_regex
test_diagnostic_sorts_deterministically
test_diagnostic_deduplicates_candidates
test_diagnostic_applies_limit_after_filters
test_diagnostic_marks_overflow_excluded_by_limit
test_zero_max_files_means_unlimited
test_negative_max_files_is_invalid
test_missing_source_root_is_error
test_source_root_file_is_error
test_source_root_escape_is_error
test_non_gf_candidate_is_excluded
test_selected_paths_are_absolute
test_persisted_display_path_is_project_relative
test_extract_module_name_returns_stem
test_selection_does_not_create_output_directories
test_selection_does_not_modify_source
```

---

# 42. Required Windows tests

```text
test_windows_project_path_with_spaces
test_windows_target_path_with_spaces
test_windows_drive_letter_not_split
test_windows_case_variant_deduplicates
test_windows_safe_relative_display_path
test_windows_unicode_path
test_windows_reserved_name_not_generated_by_selector
```

Tests may use platform-aware skips when behavior cannot be represented faithfully on another operating system.

---

# 43. Required integration tests

Integration tests create temporary project trees covering:

```text
flat source directory
nested source directory
duplicate basenames in different subdirectories
backup `.gf` files
disabled `.gf` files
non-GF artifacts
missing configured checkpoint
checkpoint and entrypoint overlap
source-root symlink
project path with spaces
Unicode directory
large candidate set with max_files
filesystem mutation after enumeration
```

Integration tests do not need a real GF executable because selection does not invoke GF.

---

# 44. Property tests

Useful property assertions:

```text
selected and excluded identities do not overlap
selected identities are unique
selected diagnostic paths are sorted
selected files all end with `.gf`
selected files all remain under source root
max_files never truncates checkpoint or release
same tree and configuration produce same selection
exclude match always defeats include match
```

Property-testing libraries are optional.

Deterministic ordinary tests are required.

---

# 45. Conformance checks

The file-selection contract is satisfied when:

```text
[ ] canonical modes are accepted and normalized
[ ] legacy aliases are resolved before selection
[ ] project and source roots are validated
[ ] quick mode selects exactly one target
[ ] checkpoint mode preserves declared order
[ ] release mode selects the complete ordered union
[ ] diagnostic mode enumerates recursively
[ ] glob semantics are documented and tested
[ ] exclude precedence is enforced
[ ] invalid regexes fail clearly
[ ] selected paths are unique and deterministic
[ ] explicit required targets cannot be silently excluded
[ ] max_files is diagnostic-only
[ ] max_files is applied after filtering
[ ] overflow candidates are accounted for
[ ] outside-root candidates are rejected
[ ] selector has no side effects
[ ] selector never invokes GF
[ ] run orchestration does not duplicate filters
[ ] reports do not re-enumerate files
[ ] Windows paths with spaces pass
[ ] source and project lock documents agree
```

---

# 46. Troubleshooting order

When the wrong files are selected, inspect:

1. canonical validation mode;
2. project root;
3. `sources.directory`;
4. resolved source root;
5. configured target list;
6. `sources.glob`;
7. exclude regex;
8. include regex;
9. normalized project-relative path;
10. deterministic ordering;
11. `max_files`;
12. exclusion reason;
13. legacy alias migration;
14. CLI or GUI override precedence.

Do not troubleshoot selection by changing compiler flags.

The compiler receives only the selector’s result.

---

# 47. Common examples

## 47.1 Diagnostic selection

Configuration:

```toml
[sources]
directory = "lib/src/example"
glob = "*.gf"
include_regex = "^[A-Z].*\\.gf$"
exclude_regex = "\\.(bak|tmp)\\.gf$"
```

Files:

```text
GrammarX.gf
NounX.gf
notes.gf
Old.bak.gf
nested/SyntaxX.gf
README.md
```

Selected:

```text
GrammarX.gf
NounX.gf
nested/SyntaxX.gf
```

Excluded:

```text
notes.gf        → not_matched_by_include_regex
Old.bak.gf      → excluded_by_regex
```

`README.md` was not a candidate because the glob did not match it.

## 47.2 Exclude precedence

Candidate:

```text
GrammarX.disabled.gf
```

Include regex matches `.gf`.

Exclude regex matches `.disabled.gf`.

Outcome:

```text
excluded_by_regex
```

## 47.3 Quick basename ambiguity

Files:

```text
core/GrammarX.gf
experimental/GrammarX.gf
```

Target:

```text
GrammarX.gf
```

Outcome:

```text
configuration error: ambiguous target
```

No file is selected.

## 47.4 Diagnostic limit

Accepted sorted candidates:

```text
A.gf
B.gf
C.gf
```

Configuration:

```text
max_files = 2
```

Selected:

```text
A.gf
B.gf
```

Excluded:

```text
C.gf → excluded_by_limit
```

## 47.5 Release ordered union

Checkpoints:

```text
MorphoX.gf
GrammarX.gf
```

Entrypoints:

```text
GrammarX.gf
SyntaxX.gf
```

Selected:

```text
MorphoX.gf
GrammarX.gf
SyntaxX.gf
```

---

# 48. Anti-drift indicators

Selection drift exists when:

- CLI and GUI select different files for equivalent configuration;
- run orchestration applies its own regex;
- a report re-enumerates source files;
- checkpoint order changes alphabetically;
- release targets are truncated by `max_files`;
- a required target is silently omitted;
- include takes precedence over exclude;
- path matching uses absolute machine paths in one component and project-relative paths in another;
- `max_files` is applied before filtering;
- basename ambiguity chooses one file silently;
- a file outside the source root is selected;
- legacy `file` and `all` remain canonical modes;
- exclusion reason text changes without updating consumers;
- selector creates output directories;
- selector starts GF;
- module-name extraction begins parsing report text.

Any such change requires coordinated review of:

```text
file selector
project loader
bootstrap
RunConfig
run orchestration
result model
reports
tests
INTERFILE_CONTRACT_LOCK.md
PERSISTED_SCHEMA_LOCK.md
this document
```

---

# 49. Cross-references

| Topic | Document |
|---|---|
| Documentation alignment | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Single active project | `docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md` |
| Independent Portfolio boundary | `docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md`, `docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md` |
| Framework file boundary | `docs/INTERFILE_CONTRACT_LOCK.md` |
| Project configuration schema | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Project TOML fields | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Validation modes | `docs/validation/VALIDATION_MODES.md` |
| Static scanning | `docs/validation/STATIC_SCANNING.md` |
| Compilation | `docs/gf/GF_COMPILATION.md` |
| Pipeline order | `docs/validation/VALIDATION_PIPELINE.md` |
| Status values | `docs/reference/STATUS_VALUES.md` |
| Active project targets | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Dependency map | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Validation specification | `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md` |

---

# 50. Governing rule

> Selection is complete only when every chosen file is valid, inside the active source root, accepted by project policy, unique, and ordered according to the current validation mode.

No later stage may add, remove, reorder, or substitute source targets silently.
