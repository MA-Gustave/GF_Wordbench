# GF Wordbench validation profile template

## Purpose

A validation profile is an **optional policy package** attached explicitly to one
resolved language selection.

GF Wordbench reads the selected language directly from its existing RGL source
tree. It does not copy the language into this profile and it does not make the
profile the owner of the language path, language identity, RGL root, GF
executable, output root, or source inventory.

The profile adds information that cannot be inferred safely from source files:

- additional include and exclude rules;
- required and release entrypoints;
- ordered checkpoints;
- scenario scripts, inputs, and expected gold outputs;
- expected release artifacts;
- release gates and documented exceptions.

A normal scan or compile can run without a profile.

## Canonical ownership

| Value | Owner |
|---|---|
| Selected path and language directory | `ResolvedLanguageContext` |
| Language key and observed source inventory | `ResolvedLanguageContext` |
| RGL source root and effective GF search path | language/toolchain resolution |
| Executable, timeouts, output root, and run options | environment and run request |
| Run logs, reports, temporary files, and artifacts | Wordbench run directory |
| Required scenarios, golds, checkpoints, and release policy | validation profile |

The profile may declare an expected language key as a compatibility guard. That
value does not become the active language identity.

## Directory layout

```text
<profile-root>/
├── project.toml
├── README.md
├── docs/
└── validation/
    ├── README.md
    ├── scenarios/
    ├── inputs/
    └── gold/
```

The filename `project.toml` is retained for compatibility with existing readers.
Its role is an optional validation profile, not a mandatory active-project
configuration.

## Attachment model

A profile is loaded only when the user, CLI, automation request, or application
state selects it explicitly.

```text
existing RGL language directory
        │
        ├── read directly by Wordbench
        │
        ▼
ResolvedLanguageContext
        │
        ├── optional compatibility check
        ▼
ValidationProfile
        │
        ▼
validation run
        │
        ▼
<output-root>/<language-key>/run_<run-id>/
```

The profile directory can live in the Wordbench repository, beside a language,
or in another controlled location. Profile-relative paths must remain inside the
profile root. They must never redirect source discovery away from the resolved
language context.

## Initialization

1. Copy `templates/validation-profile/` to a profile location.
2. Replace required placeholders in `project.toml`.
3. Add only policy that is genuinely project-specific.
4. Add scenario scripts, inputs, and golds as needed.
5. Attach the profile explicitly to a resolved language.
6. Run profile validation before using it for release decisions.

Do not copy `.gf` language sources into the profile.

## Compatibility

The previous `gf-wordbench.project` model treated `project.toml` as the owner of
project identity, source location, and GF path parts. That ownership model is
superseded.

Readers may support a migration period, but new documentation and templates
must follow these rules:

- source facts come from `ResolvedLanguageContext`;
- machine and run facts come from environment/run configuration;
- the validation profile owns policy only;
- missing profiles do not block ordinary startup;
- conflicting profile facts are rejected rather than overriding resolved facts.

## Template files

| File | Purpose |
|---|---|
| `project.toml` | machine-readable profile policy |
| `docs/INTERFILE_CONTRACT_LOCK.md` | ownership and consistency rules |
| `docs/VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md` | profile validation semantics |
| `docs/TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md` | coverage mapping |
| `docs/RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` | release requirements |
| `validation/scenarios/` | scenario scripts |
| `validation/inputs/` | reusable scenario inputs |
| `validation/gold/` | expected outputs |

## Completion checklist

- [ ] no language sources copied into the profile
- [ ] no absolute machine-specific path
- [ ] no GF executable path
- [ ] no output-root or run-directory setting
- [ ] expected language key is absent or matches the selected language
- [ ] every required entrypoint exists in the resolved source inventory
- [ ] every checkpoint exists in the resolved source inventory
- [ ] every required scenario has a script
- [ ] every required gold reference exists
- [ ] release gates are explicit
- [ ] known exceptions have owners and rationale
