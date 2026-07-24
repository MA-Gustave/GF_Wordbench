# GF Wordbench — Cleanup, Backup and Recovery

**Document role:** Operational safety procedure  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Asset classes

### Authoritative

Project configuration, GF sources, project documents, scenarios, reviewed inputs and gold files. Cleanup must never delete these assets.

### Reproducible

Caches, `.gfo`, `.pgf` and generated reports that can be recreated from authoritative inputs. Deletion is allowed only when no retained evidence depends on them.

### Evidence

Resolved requests, raw logs, normalized outputs, summaries, diffs and manifests. Retention follows project and release policy.

## Cleanup

A cleanup operation must show its target root, classify every deletion, stay inside approved paths, avoid following unsafe symlinks and support a dry run. It must never infer authority from filenames alone.

## Backup

A project backup includes authoritative assets plus the configuration needed to resolve local dependencies. A release backup also includes the final run, manifest, hashes, tool versions and release artifacts.

## Recovery

Recovery uses a new directory, validates hashes, restores authoritative assets first, re-resolves local GF/RGL paths, runs configuration checks and creates a new validation run. Old generated artifacts are not silently trusted as current.

## Failure safety

Partial cleanup, backup or restore operations produce explicit logs and non-success status. No failed recovery may overwrite the only verified copy.
