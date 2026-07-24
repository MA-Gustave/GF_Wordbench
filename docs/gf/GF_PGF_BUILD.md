# GF Wordbench — PGF Build

**Document role:** PGF build and verification contract  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Pending explicit project PGF identity and a current release run  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

A PGF build verifies that the configured release entrypoint can produce the required Portable Grammar Format artifact during the current run.

## Preconditions

- project configuration is valid;
- a release entrypoint and expected PGF identity are explicit;
- the GF version is supported;
- all required path components are resolved;
- prerequisite compilation evidence is current.

## Execution

PGF construction is requested through the GF boundary. The process adapter captures raw output, and the GF adapter verifies both command outcome and the produced file.

## Success criteria

A PGF build is `OK` only when:

- GF execution completes within budget;
- the expected artifact is produced during the current run;
- its resolved path is within the permitted artifact root;
- the file is non-empty and readable;
- its size and hash are recorded;
- the artifact is present in the run manifest;
- required inspection or smoke checks pass.

A stale pre-existing PGF never counts as current evidence.

## Project state

The supplied `project.toml` requires a PGF for release but does not identify a unique release entrypoint or expected PGF filename. Those values remain explicit project decisions and release blockers until configured and verified.
