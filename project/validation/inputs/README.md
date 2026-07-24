# Albanian (`Sqi`) — Validation Inputs

**Document role:** Project input contract  
**Decision status:** Project-owned  
**Implementation status:** Input directory contract corrected; concrete input inventory is not reverified  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

This directory contains reviewed, version-controlled data consumed by project scenarios.

## Rules

- Use UTF-8 and a final newline for text formats unless the format forbids it.
- Keep inputs minimal, deterministic and project-relative.
- Record the consuming scenario and purpose.
- Do not store executables, generated `.gfo`/`.pgf`, run logs, secrets or machine-local paths.
- Preserve Albanian Unicode exactly; do not normalize orthography silently.
- Changes to expected behavior trigger scenario and gold review.

## Naming

Use lowercase filesystem-safe names. Variants should be explicit rather than encoded as “final”, “new” or copy suffixes.

## Validation

Input checks cover path safety, encoding, size, final newline, duplicate content and registration consistency.
