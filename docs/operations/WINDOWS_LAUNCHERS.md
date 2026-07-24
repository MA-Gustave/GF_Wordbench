# GF Wordbench — Windows Launchers

**Document role:** Windows launcher contract  
**Decision status:** Accepted  
**Implementation status:** Applicable only to launchers that exist in the repository  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Scope

Windows launchers are convenience entrypoints. They do not own configuration, validation logic or exit-code semantics.

## Required behavior

A maintained `.bat` or PowerShell launcher must:

- resolve its own repository directory safely;
- quote every path;
- invoke the documented Python module or installed CLI;
- forward user arguments without reinterpreting them;
- preserve the child exit code;
- avoid changing persistent state except through the application;
- print actionable errors when Python or the environment is unavailable.

## Prohibited behavior

- embedding machine-local GF or RGL paths;
- invoking GF directly;
- duplicating CLI parsing or validation policy;
- swallowing non-zero exit codes;
- relying on the caller's current directory;
- using temporary shell files containing untrusted arguments.

## Verification

Launcher tests should cover repository paths with spaces, missing environment, argument forwarding, GUI/CLI selection and exit-code propagation.
