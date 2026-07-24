# GF Wordbench — GF Version Compatibility

**Document role:** GF compatibility policy  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Pending a tested GF/RGL compatibility matrix  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Policy

GF compatibility is declared, tested and evidence-based. An empty minimum version does not mean that every GF version is supported.

## Compatibility record

For each supported combination record:

```text
GF version
RGL revision or compatibility range
operating system
Python version
supported operations
known deviations
test evidence
last verified date
```

## Probe behavior

The GF adapter probes the executable before normative execution unless a verified result for the same executable is intentionally reused. Probe output is preserved as evidence.

## Capability handling

Version-specific command syntax, output parsing and feature capability belong in the GF adapter. Domain and application services operate on stable Wordbench requests and results.

## Unknown versions

An untested or unparseable version is reported explicitly. `quick` or `diagnostic` may continue only under a documented non-release policy. `release` is fail-closed unless the combination is supported and verified.

## Current project gap

`project/project.toml` leaves `gf.minimum_version` empty. The project decision log must establish the supported GF range before release readiness can be claimed.
