# GF Wordbench — Configuration Reference

**Document role:** Configuration precedence summary
**Status:** Normative
**Last reviewed:** 2026-08-05

## Resolution order

```text
framework-safe defaults
→ explicit selected language path
→ LanguageProbeService
→ immutable ResolvedLanguageContext
→ optional explicitly selected ValidationProfile
→ machine-local environment configuration
→ permitted explicit CLI or GUI run values
→ immutable ResolvedRunConfig
```

## Owners

| Value | Owner |
|---|---|
| active language and source facts | `ResolvedLanguageContext` |
| advanced validation and release policy | optional `ValidationProfile` |
| GF executable, output root, local overrides | environment resolution |
| run mode and focused target | explicit run request |
| generated artifact paths | `RunPaths` |
| remembered path and preferences | application state |

## Profile rule

`project/project.toml` may be loaded explicitly as a compatibility validation profile. It is not required at repository root and does not own the selected source path, language identity, RGL root, or effective GF path.

## Execution rule

Configuration is resolved once. Stages consume the immutable resolved request and do not reread GUI state, application state, profile files, or environment variables independently.
