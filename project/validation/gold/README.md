# Albanian (`Sqi`) — Gold Files

**Document role:** Project gold governance  
**Decision status:** Project-owned  
**Implementation status:** Gold governance corrected; concrete gold completeness is not reverified  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

A `.gold` file is the reviewed normalized expectation for one deterministic scenario or variant.

```text
raw scenario output
→ marker extraction
→ versioned normalization
→ exact comparison
→ project/validation/gold/<scenario-id>.gold
```

## Rules

- Gold files are project inputs, not run artifacts.
- Raw output is never stored as the gold merely because it is current.
- Normal validation and release validation are read-only.
- Updates require an explicit operation, visible diff and reviewer approval.
- Each gold is traceable to a source run and normalization version.
- A missing, stale or incompatible required gold blocks release `OK`.
- Text golds use UTF-8 and a final newline.

## Non-claim

A passing gold proves stability for the reviewed scenario. It does not prove complete Albanian correctness or coverage.
