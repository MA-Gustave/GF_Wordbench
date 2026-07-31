# ADR-0014 — Catalog-Driven Single-Language Startup

**ADR ID:** `ADR-0014`  
**Title:** Catalog-Driven Language Selection and Startup  
**Status:** Superseded  
**Decision date:** 2026-07-30  
**Last reviewed:** 2026-07-30  
**Decision owners:** GF Wordbench maintainers  
**Implementation status:** Not implemented; superseded before implementation  
**Verification status:** Historical record only; current verification is governed by ADR-0015  
**Applies to:** language catalog, RGL binding, language bundles, application state, GUI startup, bootstrap, path resolution, run construction, reporting, migrations and tests  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related locks:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Related decisions:** `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`, `ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md`, `ADR-0011-SEPARATE-PORTFOLIO.md`, `ADR-0012-INDEPENDENT-PRODUCTS.md`, `ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`  
**Supersedes:** the parts of `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md` that require one language per workspace, prohibit a startup language selector, or make `project/project.toml` the normal startup authority  
**Preserves:** exactly one resolved language context per running Wordbench session and exactly one language identity per ordinary run  
**Superseded by:** `ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`

---

## 0. Supersession notice

This ADR is retained as a historical record of the catalog-driven startup design.
It is no longer a normative implementation authority.

`ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md` replaces this design with an
explicit path-resolved startup model:

```text
one user-selected GF language directory or .gf file
→ bounded language probing
→ existing source-selection service
→ existing GF path resolver
→ existing preflight and GF execution boundaries
→ one immutable ResolvedLanguageContext
```

Under ADR-0015:

- `rgl-language-catalog.json` is not required for normal startup;
- a `language.toml` bundle is not required to browse, scan or compile a language;
- `project/project.toml` is an optional explicit validation profile rather than
  mandatory startup authority;
- scenarios, inputs, golds and release policy remain optional profile-owned
  configuration;
- application state may remember a selected path, but the path is revalidated on
  every load;
- discovery begins only from one explicit user-selected path and remains bounded;
- Wordbench reuses its existing source selection, path resolution, preflight, GF
  execution and diagnostic services instead of adding a parallel RGL scanner.

The following principles from this ADR remain valid because ADR-0015 preserves
them explicitly:

- every interactive GUI launch begins at an introduction surface;
- a session has no active language or exactly one immutable resolved language
  context;
- every ordinary run records exactly one language identity;
- language identity cannot change while a run is active;
- switching languages disposes the old runtime and composes a new one;
- GF remains the semantic authority;
- the effective GF path remains centrally resolved and shared by all GF-backed
  operations;
- normal startup and validation do not modify GF source files.

All sections below describe the superseded catalog-driven design. They are kept
unchanged except for metadata and this notice so that the decision history remains
auditable. They must not be used as current implementation requirements, test
requirements, schema requirements or acceptance criteria.

---

## 1. Decision summary

GF Wordbench supports several installed language bundles through one deterministic,
catalog-driven startup flow.

The product remains single-language at runtime:

> A Wordbench session has either no loaded language or exactly one completely
> resolved language context. Every ordinary run uses that one context without
> changing language identity while the run is active.

The canonical startup sequence is:

```text
create QApplication
→ load local application state
→ resolve the machine-local RGL root
→ load the canonical language catalog
→ show the introduction window
→ select an exact catalog language ID
→ resolve the catalog paths beneath the RGL root
→ load the catalog-referenced language bundle configuration
→ validate identity, containment and required files
→ construct one immutable resolved language context
→ compose the main Wordbench runtime
→ attempt to persist the successful language ID as a convenience value
→ show the main window
```

GF Wordbench does not discover languages from the filesystem during startup.
It does not scan `gf-rgl/src`, infer a language from directory names, inspect
module suffixes to create a catalog entry, or silently repair catalog data.

The version-controlled file:

```text
rgl-language-catalog.json
```

is the exclusive registry of selectable languages.

---

## 2. Supersession boundary

This ADR changes the workspace model established by
`ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`.

### 2.1 Rules replaced

The following earlier rules are replaced:

- one independently maintained language requires one Wordbench clone or worktree;
- the normal GUI cannot offer a language selector;
- application startup must load `project/project.toml` before the main window;
- language-specific documentation and validation assets must live under the
  Wordbench repository's `project/` directory;
- the active language is inseparable from the physical Wordbench workspace.

### 2.2 Rules preserved

The following rules remain mandatory:

- no ordinary run may contain more than one language identity;
- language identity cannot change while a run is active;
- source files, scenarios, golds and release evidence from different languages
  cannot be merged into one ordinary run;
- GUI state cannot invent or override language-owned configuration;
- `gf-portfolio` remains a separate product;
- Wordbench does not aggregate or compare several languages as a portfolio;
- completed run artifacts identify exactly one language and one resolved
  configuration state.

### 2.3 New product description

The canonical description is:

```text
GF Wordbench is multi-language capable,
single-active-language per session,
and single-language per run.
```

The phrases `multi-language capable` and `single-active-language` are not
contradictory. The first describes available configurations. The second describes
runtime state.

---

## 3. Normative terminology

### 3.1 Language catalog

The versioned JSON document at the Wordbench repository root that lists every
language the product may select and the exact RGL-relative paths required to
resolve it.

### 3.2 Catalog language ID

The exact, case-sensitive key used in `language_directories`.

For the existing RGL catalog, examples include:

```text
Eng
Fre
Ger
Sqi
```

The catalog language ID is the only persisted selection identifier. Wordbench
must not create a parallel ISO-code identifier, lowercase alias, directory-name
alias or translated-name alias unless a later versioned catalog contract defines
one explicitly.

### 3.3 Language bundle

A Wordbench-owned directory stored beneath the configured `gf-rgl` root and
referenced explicitly by one catalog entry. It contains the language-specific
Wordbench configuration, documentation, validation scenarios, inputs and golds.

### 3.4 Language bundle configuration

The versioned TOML document referenced by the catalog entry. Its canonical
filename is:

```text
language.toml
```

Its schema ID is:

```text
gf-wordbench.language-bundle
```

### 3.5 Introduction window

The initial GUI surface shown before the main Wordbench runtime exists. It owns
presentation and user intent only. It does not parse catalog JSON, resolve paths,
load TOML directly or construct runtime configuration.

### 3.6 Resolved language context

The complete immutable runtime model produced after a catalog language and its
bundle have passed all startup validation.

### 3.7 Last language

The optional catalog language ID remembered in local application state after a
successful load. It is a convenience pointer, not language configuration and not
an authority over the current catalog.

### 3.8 Language switch

A controlled transition that closes the current language runtime and returns to
the introduction window before resolving another language. It is not an in-place
mutation of an active runtime.

---

## 4. Canonical repository layout

### 4.1 GF Wordbench repository

The catalog remains a static, reviewed Wordbench artifact:

```text
GF_Wordbench/
├── rgl-language-catalog.json
├── src/
├── tests/
├── docs/
└── ...
```

The normal runtime never generates or rewrites this file.

### 4.2 RGL installation

Language sources and Wordbench-owned language bundles share the same RGL root but
remain in separate namespaces:

```text
gf-rgl/
├── src/
│   ├── abstract/
│   ├── common/
│   ├── api/
│   ├── prelude/
│   ├── english/
│   ├── french/
│   ├── albanian/
│   └── ...
└── wordbench/
    └── languages/
        ├── Eng/
        │   ├── language.toml
        │   ├── docs/
        │   └── validation/
        │       ├── scenarios/
        │       ├── inputs/
        │       └── gold/
        ├── Fre/
        │   ├── language.toml
        │   ├── docs/
        │   └── validation/
        └── Sqi/
            ├── language.toml
            ├── docs/
            └── validation/
```

The shown bundle names are a canonical organization convention, but runtime
resolution still uses the explicit path stored in the catalog. Wordbench must not
construct a bundle path merely by interpolating the language ID.

### 4.3 Namespace ownership

```text
gf-rgl/src/**
    RGL source ownership

gf-rgl/wordbench/languages/**
    Wordbench language-bundle ownership
```

Normal startup and validation are read-only for both namespaces.

An explicit authoring or gold-update operation may write only to approved paths
inside the selected Wordbench language bundle. It must not write to another
language bundle and must not modify `gf-rgl/src/**` as a side effect.

---

## 5. Authority matrix

| Fact | Authoritative owner | Runtime consumer | Forbidden substitute |
|---|---|---|---|
| Available language IDs | `rgl-language-catalog.json` | startup application service | filesystem enumeration |
| Display name | selected catalog entry | introduction and main GUI | translated or inferred directory name |
| RGL source directory | selected catalog entry | language resolver | `language.toml`, filename inference |
| Ordered GF search paths | selected catalog entry | bootstrap and GF adapter | directory scanning, global folder list |
| Language bundle config path | selected catalog entry | bundle loader | `<language-id>` interpolation |
| Module entrypoints | selected `language.toml` | validation planning | filename patterns |
| Module checkpoints | selected `language.toml` | validation planning | alphabetic discovery |
| Scenarios, inputs and golds | selected `language.toml` | scenario application services | recursive discovery |
| Local RGL root | environment or validated local state | startup resolver | catalog absolute path |
| Last language ID | application state | introduction application service | last run, directory name |
| Active runtime identity | `ResolvedLanguageContext` | all main-window services | mutable GUI fields |
| Run identity and evidence | completed run artifacts | reporting and readers | application state |

No provider may duplicate a value owned by another provider and then silently
choose one copy through precedence.

---

## 6. Catalog contract

### 6.1 Canonical identity

The startup-capable catalog uses:

```text
schema_id      = gf-wordbench.rgl-language-catalog
schema_version = 2.0
canonical path = rgl-language-catalog.json
```

Version `2.0` is required because runtime startup adds required per-language
fields that are absent from the existing inventory-oriented `1.0` shape.

### 6.2 Runtime purpose

The catalog is not a scanner report during normal operation. It is reviewed,
version-controlled configuration.

It provides:

- the complete selectable language set;
- exact case-sensitive language IDs;
- user-facing display names;
- exact RGL-relative source paths;
- exact RGL-relative bundle configuration paths;
- exact ordered search-path parts;
- optional reviewed metadata that does not affect path resolution.

### 6.3 Required top-level fields

```json
{
  "schema_id": "gf-wordbench.rgl-language-catalog",
  "schema_version": "2.0",
  "shared_paths": [],
  "technical_paths": [],
  "language_directories": {}
}
```

Additional producer or source metadata may be retained only when defined by the
schema. Runtime selection must not depend on historical scanner metadata such as
`discovery_source`.

### 6.4 Required language entry

Conceptual form:

```json
{
  "Fre": {
    "display_name": "French",
    "directory": "src/french",
    "primary_suffix": "Fre",
    "wordbench_config": "wordbench/languages/Fre/language.toml",
    "search_path_parts": [
      "src/french",
      "src/romance",
      "src/abstract",
      "src/common",
      "src/api",
      "src/prelude"
    ]
  }
}
```

Required fields:

```text
display_name
directory
primary_suffix
wordbench_config
search_path_parts
```

### 6.5 Path rules

Every catalog path:

- is relative to `rgl_root`;
- uses POSIX `/` separators;
- is normalized;
- contains no empty segment;
- contains no `.` or `..` segment;
- contains no drive letter, UNC prefix or URI scheme;
- is interpreted case-sensitively before platform-specific filesystem access;
- remains beneath the resolved `rgl_root` after symlink-aware containment checks.

### 6.6 Search-path order

`search_path_parts` is an ordered contract.

The resolver must preserve the JSON array order exactly. It must not:

- alphabetize paths;
- prepend every language directory;
- append every shared directory;
- deduplicate by case-insensitive comparison without an explicit policy;
- reconstruct dependencies from the global `shared_paths` array;
- inject the current working directory.

Duplicate normalized paths make the catalog entry invalid.

### 6.7 Selector order

The introduction window displays valid entries sorted by:

```text
(display_name.casefold(), language_id)
```

The sort is independent of operating-system locale. The selected and persisted
identifier remains the exact catalog key.

### 6.8 No runtime mutation

Startup must not:

- add a missing language entry;
- remove an invalid entry;
- rewrite path separators;
- fill `wordbench_config` from a convention;
- infer `search_path_parts`;
- update catalog schema versions;
- publish a repaired catalog.

An invalid catalog blocks language loading and produces a bounded diagnostic.

---

## 7. Language bundle contract

### 7.1 Canonical identity

```text
schema_id      = gf-wordbench.language-bundle
schema_version = 1.0
canonical name = language.toml
```

The file may reside at any RGL-relative path explicitly referenced by its catalog
entry. The recommended path is:

```text
wordbench/languages/<catalog-language-id>/language.toml
```

### 7.2 Responsibility split

The catalog owns location and ordered RGL path resolution.

`language.toml` owns Wordbench behavior for the selected language:

- exact identity confirmation;
- module entrypoints;
- module checkpoints;
- required and optional scenarios;
- input and gold references;
- release entrypoint and expected artifacts;
- language-specific validation policy references;
- documentation and bundle-relative asset roots.

`language.toml` must not redefine:

- `rgl_root`;
- its own absolute path;
- the language source directory;
- the ordered RGL search paths;
- another catalog language ID;
- machine-local GF or output paths.

### 7.3 Conceptual form

```toml
schema_id = "gf-wordbench.language-bundle"
schema_version = "1.0"

[language]
id = "Fre"
name = "French"
module_suffix = "Fre"

[assets]
docs_directory = "docs"
validation_directory = "validation"
scenario_directory = "validation/scenarios"
input_directory = "validation/inputs"
gold_directory = "validation/gold"

[modules]
entrypoints = [
  "GrammarFre.gf",
  "SyntaxFre.gf",
]
checkpoints = [
  "MorphoFre.gf",
  "NounFre.gf",
  "VerbFre.gf",
]

[validation]
required_scenarios = [
  "load",
  "linearize",
  "parse",
]
optional_scenarios = [
  "generation",
  "morphology",
]

[release]
required_entrypoints = ["GrammarFre.gf"]
expected_artifacts = ["GrammarFre.pgf"]
```

The exact schema is implemented later, but the ownership boundaries and identity
checks in this ADR are locked now.

### 7.4 Identity agreement

The following values must agree exactly:

```text
selected catalog key
language.toml language.id
catalog primary_suffix
language.toml module_suffix, when present
run metadata language_id
```

The display names may differ only through a future explicit localization
contract. Startup does not silently reconcile them.

### 7.5 Bundle-relative paths

Paths inside `language.toml` are relative to the directory containing
`language.toml`, unless the field contract explicitly says that a module filename
is relative to the catalog source directory.

Every field must have one documented base. No field may resolve relative to the
process current working directory.

---

## 8. Application-state contract

### 8.1 Purpose

Application state remembers machine-local convenience values. It does not store
the catalog, bundle configuration or resolved runtime context.

### 8.2 Schema update

The startup change requires a compatible app-state minor extension:

```text
schema_id      = gf-wordbench.app-state
schema_version = 1.1
```

Version `1.1` adds an optional state-owned startup group with a safe default.

Conceptual form:

```json
{
  "schema_id": "gf-wordbench.app-state",
  "schema_version": "1.1",
  "environment": {
    "rgl_root": "C:/local/gf-rgl",
    "gf_executable": null,
    "output_root": null,
    "project_root": null
  },
  "startup": {
    "last_language_id": "Fre"
  },
  "selection": {
    "mode": "diagnostic",
    "target_file": "",
    "timeout_sec": 60,
    "max_files": 0,
    "keep_ok_details": false,
    "diff_previous": true,
    "skip_version_probe": false,
    "no_compile": false,
    "emit_cpu_stats": false
  },
  "last_run": {
    "language_id": "Fre",
    "run_dir": null,
    "summary_path": null,
    "status_message": ""
  }
}
```

`project_root` is retained only for compatibility until a separate migration
removes or redefines it. It does not select the language in the new startup flow.

### 8.3 Last-language semantics

`startup.last_language_id`:

- is optional or nullable according to the final schema;
- contains one exact catalog key;
- is written only after a complete successful language resolution;
- is never written when resolution fails;
- is ignored when absent;
- is treated as unavailable when the current catalog lacks the key;
- does not cause automatic startup into the main window;
- cannot override an explicit user selection.

### 8.4 Language-scoped convenience values

A previous target or run pointer may be restored only when its recorded
`language_id` equals the newly resolved language ID.

On a language change:

- `selection.target_file` is cleared unless it is explicitly validated for the
  new language;
- `last_run` pointers from another language are not shown as the current
  language's previous run;
- the global validation mode may be retained;
- machine-local GF, RGL and output roots may be retained;
- no language-owned entrypoint, checkpoint, scenario or gold path is retained
  from the previous context.

### 8.5 Migration

The `1.0` to `1.1` migration is deterministic and non-destructive:

```text
last_language_id = null
last_run.language_id = null
all supported 1.0 values preserved
```

A migration must not infer the last language from `project_root`, a run path,
`project.toml`, module filenames or output contents.

---

## 9. Introduction-window contract

### 9.1 Mandatory startup surface

The introduction window is shown on every interactive GUI launch. A remembered
language does not bypass it automatically.

### 9.2 Required actions

Canonical action IDs and default labels:

| Action ID | Default label | Availability |
|---|---|---|
| `load_last_language` | Load last language | enabled only when the catalog is valid, the RGL root is valid and state has an ID |
| `choose_language` | Choose a language… | enabled only when the catalog and RGL root are valid |
| `select_rgl_root` | Select the gf-rgl folder… | always available |
| `quit` | Quit | always available |

The `load_last_language` control should include the resolved display label when
available, for example:

```text
Load last language — French (Fre)
```

### 9.3 Initial states

#### RGL root unavailable

```text
No language loaded.
RGL root is not configured or is unavailable.

[ Select the gf-rgl folder… ]
[ Quit ]
```

#### Catalog valid, no last language

```text
No language loaded.

[ Choose a language… ]
[ Select the gf-rgl folder… ]
[ Quit ]
```

#### Catalog valid, last language available

```text
No language loaded.

[ Load last language — French (Fre) ]
[ Choose a language… ]
[ Select the gf-rgl folder… ]
[ Quit ]
```

#### Last language absent from current catalog

```text
The last language "Fre" is not available in the current catalog.

[ Choose a language… ]
[ Select the gf-rgl folder… ]
[ Quit ]
```

The stale ID remains diagnostic evidence but is not used as a fallback path.

### 9.4 Presentation ownership

The introduction window may:

- display catalog-derived labels;
- collect a selected language ID;
- request an RGL-root directory;
- display bounded startup diagnostics;
- show busy state during resolution;
- allow retry or quit.

It must not:

- parse JSON or TOML;
- enumerate RGL directories;
- construct paths;
- call GF;
- create a run directory;
- write the catalog or bundle;
- mutate the main-window runtime;
- persist `last_language_id` before successful resolution.

---

## 10. Startup state machine

The GUI startup state is explicit:

```text
INITIALIZING
    ↓
INTRO_READY
    ↓ user action
RESOLVING_LANGUAGE
    ├── failure → INTRO_ERROR
    │                ↓ retry
    │             INTRO_READY
    └── success → LANGUAGE_READY
                      ↓
                 MAIN_WINDOW
```

Terminal states include:

```text
QUIT
FATAL_STARTUP_ERROR
```

Locked transition rules:

- `MAIN_WINDOW` is unreachable without `LANGUAGE_READY`;
- `LANGUAGE_READY` contains a complete `ResolvedLanguageContext`;
- a resolution failure returns to the introduction surface;
- no partially resolved context is cached as active;
- selecting another language while resolution is running is disabled;
- startup never creates a validation run automatically.

---

## 11. Deterministic language-resolution algorithm

Given an exact `language_id`, the application service performs these steps in
this order:

1. validate the ID as a non-empty, bounded, single-line string;
2. require a validated absolute `rgl_root`;
3. load and strictly validate `rgl-language-catalog.json`;
4. perform an exact case-sensitive key lookup in `language_directories`;
5. reject an unknown ID without aliases or fuzzy matching;
6. resolve `directory` beneath `rgl_root`;
7. resolve every `search_path_parts` value beneath `rgl_root` in array order;
8. resolve `wordbench_config` beneath `rgl_root`;
9. apply symlink-aware containment checks to every resolved path;
10. require the source directory and search-path directories to exist;
11. require `wordbench_config` to be a regular file;
12. load and strictly validate the referenced `language.toml`;
13. require exact identity agreement with the catalog key;
14. resolve bundle-relative documentation and validation paths;
15. resolve module entrypoints and checkpoints against the catalog source
    directory;
16. resolve scenarios, inputs and golds against the selected bundle;
17. require all schema-required assets to exist with the expected type;
18. construct one immutable `ResolvedLanguageContext`;
19. validate the completed context as a whole;
20. compose the main runtime from the completed context;
21. attempt to persist the successful language ID through the state repository;
22. show the main window.

Failure to persist convenience state produces a warning but does not invalidate a
complete resolved context or prevent the main window from opening.

No step may consume output from a later step. No step may write a compensating
configuration file on failure.

---

## 12. Resolved language context

### 12.1 Conceptual model

```python
@dataclass(frozen=True, slots=True)
class ResolvedLanguageContext:
    language_id: str
    display_name: str
    primary_suffix: str
    catalog_file: Path
    catalog_schema_version: str
    rgl_root: Path
    source_directory: Path
    bundle_configuration_file: Path
    bundle_root: Path
    documentation_directory: Path
    validation_directory: Path
    scenario_directory: Path
    input_directory: Path
    gold_directory: Path
    search_paths: tuple[Path, ...]
    entrypoints: tuple[Path, ...]
    checkpoints: tuple[Path, ...]
    required_scenarios: tuple[str, ...]
    optional_scenarios: tuple[str, ...]
```

The final implementation may split this model into cohesive nested immutable
models. It must preserve the complete-context invariant and public semantics.

### 12.2 Runtime-only status

The context:

- contains resolved absolute paths;
- exists only in memory during the session;
- is never serialized into application state as a replacement for source
  contracts;
- may be summarized in run evidence;
- is passed to consumers through bootstrap composition;
- is not reconstructed independently by validation stages.

### 12.3 Complete-context invariant

A context is valid only when all mandatory fields are resolved and validated.
There is no active state with a selected ID but unresolved paths.

Canonical invariant:

```text
active_context is None
or
active_context is complete, immutable and validated
```

---

## 13. Path alignment

### 13.1 Input bases

```text
catalog path fields       → rgl_root
bundle asset path fields  → bundle_root
module filenames          → source_directory
run artifact paths        → resolved language output root
```

### 13.2 Output scoping

A machine-local global output root may serve several languages, but run paths
must remain language-scoped.

Canonical derived layout:

```text
<output_root>/languages/<language_id>/run_<run-id>/
```

This derivation is a fixed Wordbench rule, not language discovery.

A run from `Fre` must never become the implicit previous run for `Sqi`.

### 13.3 GF path construction

The final GF search path is:

```text
project-local or generated temporary path additions, when explicitly approved
→ selected catalog search_path_parts in their recorded order
```

Wordbench must not append all language directories.

### 13.4 Working directory

The GF adapter receives an explicit working directory from the resolved run
plan. The current process directory is never a hidden search-path component.

---

## 14. Main-window contract

### 14.1 Creation

The main window is created only after successful language resolution.

Its title or primary project panel identifies the loaded language, for example:

```text
GF Wordbench — French (Fre)
```

### 14.2 Immutable session identity

The main window receives the resolved language context during composition. It
cannot replace individual paths or the language ID through mutable widgets.

### 14.3 Allowed controls

The main window may expose:

- validation mode;
- mode-specific targets drawn from the selected context;
- run preview;
- run start and cancellation;
- diagnostics and result navigation;
- `Change language…` when no run is active.

### 14.4 Forbidden controls

The main window must not expose independent editable fields for:

- language ID;
- source directory;
- bundle configuration path;
- individual catalog search paths;
- entrypoint paths outside the selected bundle contract.

Local environment settings may remain editable through an explicit settings
surface, but changing `rgl_root` invalidates the current language context and
requires returning to the introduction flow.

---

## 15. Language switching

### 15.1 User operation

The canonical main-window operation is:

```text
Change language…
```

### 15.2 Preconditions

A language switch is allowed only when:

- no run is active;
- no run finalization is active;
- no project-mutating operation is active;
- pending permitted state writes can complete safely.

### 15.3 Transition

```text
request language change
→ close dialogs and language-scoped views
→ release current runtime resources
→ discard the in-memory resolved context
→ clear incompatible language-scoped convenience values
→ show the introduction window
→ resolve a new language through the full algorithm
→ compose a new main runtime
```

The existing main runtime is not patched in place.

### 15.4 Active-run prohibition

During a run, `Change language…` is disabled.

A language switch request must not implicitly cancel a run. The user must first
use the explicit run-cancellation workflow and wait for bounded finalization.

---

## 16. Diagnostics and failure behavior

Stable startup diagnostic codes:

| Code | Meaning |
|---|---|
| `GF-WB-LANG-001` | canonical catalog missing or unreadable |
| `GF-WB-LANG-002` | catalog schema or content invalid |
| `GF-WB-LANG-003` | selected language ID absent from catalog |
| `GF-WB-LANG-004` | RGL root missing, relative or not a directory |
| `GF-WB-LANG-005` | catalog path escapes the RGL root |
| `GF-WB-LANG-006` | referenced language bundle config missing |
| `GF-WB-LANG-007` | catalog and bundle identities disagree |
| `GF-WB-LANG-008` | selected source directory missing |
| `GF-WB-LANG-009` | required search-path directory missing |
| `GF-WB-LANG-010` | required module or bundle asset missing |
| `GF-WB-LANG-011` | remembered last language unavailable |
| `GF-WB-LANG-012` | resolved language context incomplete |

### 16.1 Failure policy

Every startup language-resolution error is fail-closed:

- no main runtime is created;
- no active context is published;
- `last_language_id` is not updated when language resolution or runtime composition fails;
- a state-write failure after successful composition is reported as a non-fatal warning;
- no catalog or bundle file is rewritten;
- no validation run is created;
- the introduction window remains available when recovery is safe.

### 16.2 Bounded messages

User-facing messages include:

- language ID when known;
- failing relative path when safe;
- expected artifact type;
- corrective action;
- a technical diagnostic code.

They do not include complete catalog or bundle content.

---

## 17. Explicitly forbidden automatic behavior

The following behavior is prohibited in normal startup and runtime:

```text
scan gf-rgl/src for languages
read languages.csv to build a runtime language list
infer a language ID from a source directory
infer a source directory from a display name
infer wordbench_config from a language ID
infer entrypoints from Grammar*.gf or Lang*.gf
infer checkpoints from filename patterns
append all RGL language directories to GF paths
choose the only apparently valid directory
perform fuzzy or case-insensitive ID matching
load the newest language bundle by timestamp
restore language identity from a run directory
rewrite an invalid catalog
silently skip a missing required search path
fall back to project/project.toml during normal startup
```

A separate explicit maintenance validator may inspect catalog references and
report inconsistencies. It must not become a hidden runtime scanner.

---

## 18. Catalog maintenance and change control

### 18.1 Adding a language

A language becomes selectable only through one reviewed change that includes:

```text
[ ] one new exact catalog language ID
[ ] display name
[ ] source directory
[ ] primary suffix
[ ] wordbench_config path
[ ] ordered search_path_parts
[ ] valid language.toml
[ ] required bundle directories and assets
[ ] schema validation
[ ] path-containment validation
[ ] startup resolution test
[ ] introduction selector test
```

Creating a directory alone does not add a language.

### 18.2 Removing a language

Removing a catalog entry makes it unavailable immediately to startup.

A remembered ID then produces `GF-WB-LANG-011` and requires explicit selection of
another language. Wordbench must not select the next entry automatically.

### 18.3 Renaming a language ID

Changing a catalog key is an incompatible identity change. It requires:

- catalog major-version review;
- app-state migration or explicit stale-ID handling;
- bundle identity update;
- run-history compatibility review;
- documentation update;
- tests proving that the old ID is not silently reinterpreted.

### 18.4 Moving a path

Changing `directory`, `wordbench_config` or `search_path_parts` requires a
coordinated catalog and bundle review. Runtime does not search for the moved
resource.

### 18.5 Changing search-path order

Search-path reordering is behaviorally significant. It requires:

- explicit review rationale;
- compile and scenario regression tests;
- run evidence showing the resolved order;
- documentation update when module ownership or shadowing changes.

### 18.6 Manual authority

The catalog is maintained as reviewed source configuration. A scanner may be used
outside normal Wordbench operation as an authoring aid only when its output is
reviewed and explicitly adopted. Generated output never becomes authoritative
merely because it is newer.

---

## 19. Persisted evidence

Every completed run records enough information to identify its resolved language
without persisting machine-specific configuration as portable project truth.

Required run evidence includes:

```text
language_id
display_name
primary_suffix
catalog schema version
catalog content digest or selected-entry digest
language-bundle schema version
language-bundle content digest
source directory as an RGL-relative path
bundle config as an RGL-relative path
ordered search-path parts as RGL-relative paths
resolved local RGL root in environment evidence
```

Absolute paths may appear only in local run environment evidence according to the
existing reporting privacy contract. Portable identities remain relative.

A previous-run comparison is valid only when its language identity and relevant
contract versions satisfy the comparison policy.

---

## 20. Ownership and dependency direction

### 20.1 Functional ownership

| Responsibility | Owner |
|---|---|
| Catalog schema and model | language/catalog owner under the `projects` functional boundary |
| Catalog JSON persistence rules | schema registry and canonical serialization owners |
| Catalog loading | catalog adapter |
| Language-bundle schema and model | language-bundle owner under `projects` |
| TOML loading | language-bundle adapter |
| Language selection use case | projects application service |
| Path containment and filesystem access | approved filesystem port and adapter |
| Resolved language context | projects domain/application boundary |
| Introduction window | GUI entrypoint/presentation |
| Runtime composition | bootstrap |
| Last-language persistence | state repository |
| GF invocation | existing GF adapter boundary |
| Run evidence | runs and reporting owners |

### 20.2 Dependency direction

```text
introduction widgets
    → language-selection application service
    → catalog and bundle ports
    → filesystem / JSON / TOML adapters

successful resolved context
    → bootstrap
    → main-window runtime
    → validation and run services
```

Forbidden directions:

```text
GUI widgets -X→ JSON parser
GUI widgets -X→ TOML parser
GUI widgets -X→ filesystem scanning
validation stage -X→ application-state repository
reporting -X→ language selection
language bundle -X→ machine-local state
catalog loader -X→ GUI
```

---

## 21. Locked interfile contracts

### 21.1 `IFC-LANG-001` — Catalog loading

**Provider:** catalog loader adapter  
**Consumers:** language-selection service, catalog validator  
**Input:** canonical catalog file path  
**Output:** immutable validated catalog model  
**Failures:** missing file, invalid JSON, unsupported schema, invalid path shape,
duplicate normalized path, invalid language entry  
**Invariant:** the loader returns the document's meaning without filesystem-based
completion or repair.

### 21.2 `IFC-LANG-002` — Bundle loading

**Provider:** language-bundle TOML adapter  
**Consumers:** resolved-language service, bundle validator  
**Input:** exact catalog-referenced configuration path  
**Output:** immutable validated bundle model  
**Failures:** missing file, invalid TOML, unsupported schema, invalid field,
identity mismatch  
**Invariant:** the adapter does not discover modules or assets.

### 21.3 `IFC-LANG-003` — Language resolution

**Provider:** projects application service  
**Consumers:** GUI startup coordinator, CLI or automation entrypoint when later
supported  
**Input:** exact language ID, validated `rgl_root`, validated catalog and bundle
ports  
**Output:** complete immutable `ResolvedLanguageContext`  
**Failures:** stable `GF-WB-LANG-*` diagnostics  
**Invariant:** publication is atomic at the model boundary: no partial active
context escapes.

### 21.4 `IFC-LANG-004` — Introduction selection

**Provider:** GUI introduction controller  
**Consumer:** language-resolution use case  
**Input:** user intent carrying one exact language ID or one RGL-root selection  
**Output:** presentation state or successful handoff to bootstrap  
**Invariant:** presentation does not own configuration semantics.

### 21.5 `IFC-LANG-005` — Last-language state

**Provider:** state repository  
**Consumers:** introduction application service and shutdown/state sync  
**Input:** successful resolved language ID  
**Output:** validated app-state model and atomic persisted state  
**Invariant:** state cannot activate a language without current catalog
validation.

### 21.6 `IFC-LANG-006` — Runtime composition

**Provider:** bootstrap  
**Consumers:** GUI main entrypoint and run construction  
**Input:** complete resolved language context plus resolved environment  
**Output:** fully composed language-bound runtime  
**Invariant:** bootstrap does not re-resolve individual language paths through a
second algorithm.

---

## 22. Anti-drift invariants

The following are locked and require an ADR or coordinated contract update to
change:

1. `rgl-language-catalog.json` is the sole selectable-language registry.
2. Runtime performs no language discovery.
3. Catalog IDs are exact and case-sensitive.
4. Catalog paths are relative to `rgl_root` and use POSIX separators.
5. `wordbench_config` is explicit in each selectable entry.
6. `search_path_parts` order is explicit and preserved.
7. `language.toml` cannot override catalog source or search paths.
8. The selected catalog ID must equal the bundle language ID.
9. Startup always presents the introduction window.
10. Last-language state never bypasses current catalog validation.
11. The main runtime is created only from a complete immutable context.
12. There is at most one active context.
13. Language identity cannot change during a run.
14. Switching language recreates the runtime rather than patching paths.
15. Run outputs are language-scoped.
16. Previous-run pointers are language-tagged or ignored across languages.
17. GUI widgets do not parse persisted configuration.
18. Validation stages do not read application state.
19. Normal startup and validation do not write catalog or bundle configuration.
20. `gf-portfolio` is not part of startup, selection or path resolution.

---

## 23. Required tests

### 23.1 Catalog tests

```text
valid 2.0 catalog loads
wrong schema ID rejected
unsupported major rejected
missing required language field rejected
absolute path rejected
parent traversal rejected
backslash normalization is not silently persisted
duplicate normalized search path rejected
unknown language ID rejected case-sensitively
selector order deterministic
runtime ignores non-authoritative historical metadata
```

### 23.2 Bundle tests

```text
valid bundle loads
wrong schema ID rejected
catalog/bundle ID mismatch rejected
module suffix mismatch rejected when both values exist
absolute bundle asset path rejected
bundle path escape rejected
missing required entrypoint rejected
required and optional scenarios cannot overlap
```

### 23.3 Resolver tests

```text
all paths resolved under rgl_root
symlink escape rejected
search-path order preserved
no current-working-directory dependency
no filesystem language enumeration
no path inference from display name or ID
complete context immutable
partial failure publishes no context
successful resolution updates last_language_id
failed resolution does not update last_language_id
```

### 23.4 Introduction GUI tests

```text
intro always shown on launch
load-last hidden or disabled when absent
load-last label derived from current catalog
stale last ID produces bounded message
choose-language contains only catalog entries
main window not created before successful resolution
resolution error returns to intro
controls disabled while resolution active
quit works without loaded language
```

### 23.5 Language-switch tests

```text
switch disabled during run
switch releases old runtime
switch clears incompatible target selection
switch does not reuse previous-language run pointer
new runtime contains only new-language paths
failure to load new language leaves no active context
```

### 23.6 State tests

```text
1.0 state migrates to 1.1 with null language values
1.1 state round-trips canonically
last_language_id exact case preserved
unknown last ID remains recoverable diagnostic data
state deletion changes no catalog or bundle facts
last-run language mismatch blocks previous-run reuse
```

### 23.7 Architecture tests

```text
GUI does not import JSON or TOML language adapters
entrypoints do not import concrete filesystem mechanisms
validation does not import state repository
catalog and bundle models are immutable
bootstrap receives one complete resolved context
no runtime language scanner exists
no language-specific constants appear in generic framework logic
```

### 23.8 End-to-end tests

Use at least two synthetic catalog languages:

```text
TstA
TstB
```

Prove:

1. launch intro;
2. load `TstA`;
3. verify every resolved path belongs to `TstA` or its explicit shared paths;
4. close or return to intro;
5. load `TstB`;
6. verify no `TstA` source, scenario, gold, target or run pointer remains active;
7. restart;
8. load last language;
9. verify `TstB` resolves again from the current catalog, not cached paths.

---

## 24. Coordinated documentation updates

Implementation of this ADR is incomplete until the following documents are
reviewed and updated in one coordinated change:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/DATA_MODEL.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/gf/GF_PATH_RESOLUTION.md
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/CLONING_AND_RESETTING.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/reference/GLOSSARY.md
docs/reference/SCHEMA_INDEX.md
docs/usage/GUI_REFERENCE.md
docs/usage/CLI_REFERENCE.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
templates/project/**
project/**
```

The update must clearly mark legacy `project/` behavior as migrated, deprecated or
removed. Normal startup must not retain two authoritative language models.

---

## 25. Coordinated schema updates

Required schema work:

```text
rgl-language-catalog 1.0 → 2.0
    required wordbench_config
    required per-language search_path_parts
    runtime identity semantics

new gf-wordbench.language-bundle/1.0
    language identity
    bundle assets
    module targets
    validation and release policy

app-state 1.0 → 1.1
    optional startup.last_language_id
    optional last_run.language_id
    deterministic migration

run-summary and manifest review
    selected language identity
    catalog and bundle contract evidence
    language-scoped previous-run compatibility
```

Every schema must be registered with its canonical owner before a writer emits
it.

---

## 26. Implementation sequence

1. accept this ADR;
2. update the persisted-schema lock and schema registry plan;
3. define immutable catalog `2.0` models and validation;
4. update the static catalog manually to `2.0`;
5. define the language-bundle `1.0` model and TOML schema;
6. create one real language bundle as the proving fixture;
7. define filesystem ports required by catalog and bundle loaders;
8. implement strict read-only catalog loading;
9. implement strict read-only bundle loading;
10. implement `ResolvedLanguageContext` and its resolver;
11. update app-state models, migration and repository to `1.1`;
12. implement the introduction application service and view model;
13. implement the introduction window and controller;
14. change GUI entrypoint startup sequencing;
15. compose the main runtime from the resolved context;
16. scope run paths and previous-run selection by language ID;
17. implement controlled language switching;
18. update reports and manifests with language contract evidence;
19. add unit, contract, architecture and end-to-end tests;
20. update all coordinated documents;
21. remove or quarantine legacy normal-startup use of `project/project.toml`;
22. verify two-language switching with no path contamination.

---

## 27. Acceptance criteria

This ADR is implemented only when all of the following are true:

```text
[ ] GUI always starts at the introduction window
[ ] selector entries come only from the static catalog
[ ] no runtime language discovery exists
[ ] exact last-language reload works
[ ] stale last-language ID fails safely
[ ] catalog 2.0 is schema-validated
[ ] language-bundle 1.0 is schema-validated
[ ] app-state 1.1 migration is tested
[ ] one complete immutable context gates main-window creation
[ ] all resolved paths are contained under approved roots
[ ] search-path order matches the selected catalog entry exactly
[ ] switching language recreates the runtime
[ ] switching is impossible during a run
[ ] run output and previous-run reuse are language-scoped
[ ] no generic framework code contains a hard-coded language ID or directory
[ ] project/project.toml is not a second normal-startup authority
[ ] all affected locks and references are updated
[ ] two-language end-to-end replacement test passes
```

Verification requires automated tests. Documentation presence alone does not
establish implementation.

---

## 28. Rejected alternatives

### 28.1 Runtime scanner

Rejected because filesystem state would become an implicit registry and could
produce different language lists without a reviewed catalog change.

### 28.2 Infer bundle path from language ID

Rejected because a naming convention would become an undocumented second source
of truth and would fail silently after path reorganization.

### 28.3 Keep `project/project.toml` as an equal authority

Rejected because two active-language providers would require precedence rules and
could disagree about source paths, modules, scenarios and release identity.

### 28.4 Patch the existing runtime in place

Rejected because stale paths, targets, prior results, workers or adapters could
survive a language switch.

### 28.5 Automatically load the last language

Rejected because startup would hide the active selection and turn disposable
state into an implicit authority. The introduction window must expose the action.

### 28.6 Add all RGL directories to the GF search path

Rejected because it creates ambiguous module resolution and accidental
cross-language dependencies.

### 28.7 Use `gf-portfolio` as the selector

Rejected because language startup is a Wordbench runtime concern while portfolio
aggregation remains an independent product concern.

---

## 29. Governing rule

> The catalog declares what may be loaded. The selected language bundle declares
> how Wordbench works with that language. Local state remembers only convenience.
> Bootstrap publishes exactly one complete resolved context. Nothing is inferred,
> and no run may observe more than one language identity.
