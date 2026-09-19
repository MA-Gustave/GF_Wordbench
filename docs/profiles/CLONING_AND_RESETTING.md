# GF Wordbench — Cloning and Resetting Validation Profiles

**Document ID:** `GF-WB-PROFILES-CLONING-RESETTING`
**Status:** Normative profile-lifecycle procedure
**Last reviewed:** 2026-08-05

## 1. Scope

Cloning and resetting apply to optional validation-profile files, generated runs, and disposable application state. They do not define language switching and do not own GF source lifecycle.

## 2. Profile clone

A profile clone copies profile-owned configuration, docs, scenarios, inputs, and golds to another explicit profile directory. It must preserve or intentionally change profile identity according to the schema contract.

A profile clone must not copy the selected GF source tree or capture local absolute paths.

## 3. Profile reset

Reset replaces profile-owned files from `templates/validation-profile/` after explicit authorization. It may archive the previous profile. It must not alter the selected source tree.

## 4. Generated-run cleanup

Run cleanup removes only owned generated directories under approved output roots. It never removes sources, profiles, golds, framework tests, or external archives.

## 5. Application-state reset

State reset removes only disposable state. It does not change sources, profile policy, or retained run evidence.

## 6. Language switching

Language switching is a runtime operation:

```text
end current runtime
→ select new language path
→ resolve new context
→ compose new runtime
```

It does not require cloning, resetting, or replacing the Wordbench repository or profile.

## 7. Transactional safety

Any profile write operation must support preflight, dry-run planning, staging, verification, bounded replacement, and rollback where applicable.
