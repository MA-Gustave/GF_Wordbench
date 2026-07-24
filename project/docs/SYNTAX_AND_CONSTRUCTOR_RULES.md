# Albanian (`Sqi`) — Syntax and Constructor Rules

**Document role:** Project syntax contract  
**Decision status:** Project-owned  
**Implementation status:** General invariants are documented; the concrete constructor registry remains incomplete  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Authority

Actual abstract functions, concrete linearizations, arity and category types come from the current GF source. This registry defines rules for maintaining them without inventing project-specific facts.

## Constructor invariants

- Public names, arity, argument order and return category are stable contracts.
- A constructor preserves every required lincat field or documents an explicit reduction.
- No implementation silently replaces a missing construction with an empty string or unrelated constructor.
- Agreement controllers and conflict rules are explicit.
- Valency is not erased when saturating complements.
- Punctuation and spacing are composed through owned helpers rather than opaque concatenation.
- Coordination, questions, relatives and extensions preserve the state required by downstream consumers.

## Registry format

| Constructor | Owner module | Type | Status | Evidence | Notes |
|---|---|---|---|---|---|
| _populate from current abstract/concrete source_ | | | | | |

## Change classification

- **compatible internal change**: same public type and observed behavior;
- **compatible extension**: new constructor or derivable field with updated consumers;
- **breaking change**: rename, arity/order/type change, semantic field removal or altered output contract.

## Verification

Every stable constructor family requires compile evidence and representative parse, linearize or generation scenarios. The registry is incomplete until generated from the active source tree.
