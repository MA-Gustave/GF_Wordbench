# GF Wordbench — Creating a Validation Profile

**Document ID:** `GF-WB-PROFILES-CREATING`
**Status:** Normative profile-creation procedure
**Last reviewed:** 2026-08-05

## 1. Purpose

This procedure creates an optional validation profile for an existing GF language source tree. It does not create or copy the language implementation.

## 2. Preconditions

- the language already exists in an RGL or user-owned source location;
- Wordbench can resolve the language directory or a `.gf` file;
- advanced checkpoint, scenario, regression, or release policy is actually needed.

Basic browsing, scanning, and focused compilation do not require a profile.

## 3. Procedure

1. Select and resolve the existing language source path.
2. Choose a separate profile directory.
3. Copy `templates/validation-profile/` to that profile directory.
4. Replace placeholders with profile metadata and compatibility assertions.
5. Declare only additional source filters, required entrypoints, checkpoints, scenarios, golds, artifacts, and release gates.
6. Keep all profile-owned paths relative to the profile root.
7. Do not add local RGL, GF executable, output, state, or run paths.
8. Explicitly attach the profile to the resolved language and run profile validation.
9. Record a baseline run only after language and profile compatibility are proven.

## 4. Prohibited creation behavior

Profile initialization must not:

- create a repository-root `project/` unless that explicit destination was requested;
- copy the selected language directory;
- rewrite GF sources;
- discover and adopt a profile implicitly;
- infer required release targets from filenames;
- store machine-local absolute paths in the profile.

## 5. Completion criteria

A newly created profile is initialized when:

- its schema and version are valid;
- its profile ID is stable and portable;
- its language compatibility assertion matches the resolved context;
- required module and scenario IDs are deterministic;
- referenced profile assets exist and are contained;
- release policy is either complete or explicitly absent;
- no unresolved placeholders remain.
