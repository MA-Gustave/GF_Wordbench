# GF Wordbench — Writing GFS Scenarios

**Document role:** Scenario authoring guide  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Authoring sequence

1. Define one behavior family and its acceptance claim.
2. Choose a stable scenario ID.
3. Add minimal reviewed inputs.
4. Write a portable `.gfs` script.
5. Emit stable section markers.
6. Keep output deterministic and bounded.
7. Run through Wordbench, not an ad-hoc shell transcript.
8. Inspect raw and normalized evidence.
9. Add or update a gold only through the explicit review workflow.

## Good scenario properties

- small enough to diagnose;
- independent of prior runs;
- explicit about the module or PGF loaded;
- representative but not unnecessarily broad;
- deterministic under the declared GF/RGL combination;
- traceable to a project requirement or known issue.

## Prohibited patterns

- absolute local paths;
- dependence on terminal prompts or color;
- unbounded generation;
- silent fallback to another module;
- automatic gold creation;
- combining unrelated assertions only to reduce file count.

## Review checklist

Confirm registration, input ownership, markers, timeout, raw evidence, normalization version, assertion meaning and release impact.
