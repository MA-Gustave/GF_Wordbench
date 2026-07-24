# Albanian (`Sqi`) — Category and Lincat Contract

**Document role:** Project category/lincat contract  
**Decision status:** Project-owned  
**Implementation status:** Detailed category contracts exist in the supplied document set but are not revalidated against source here  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

This contract protects the structured representations shared across Albanian GF modules. GF source remains authoritative for exact definitions.

## Documented parameter families

The existing project records identify parameter families such as case, gender, number/definiteness combinations, tense and agreement. Exact constructors and fields must be verified against the current source before being marked stable.

## Core invariants

- One module owns each public category lincat.
- Consumers use the owning definition rather than duplicating a compatible-looking record.
- Required agreement, case, definiteness, clitic and complement state is not silently flattened to strings.
- Adding a derivable internal field may be compatible; removing, renaming or changing the meaning of a public field is breaking.
- Pattern matches are updated exhaustively when public parameter constructors change.
- Fallback values remain explicit and cannot be presented as complete linguistic behavior.

## Change process

A public lincat change requires:

1. provider update;
2. all consumer updates;
3. constructor and pattern review;
4. compile checks for affected checkpoints and entrypoints;
5. relevant scenarios and gold review;
6. dependency-map and contract update;
7. decision record when compatibility changes.

## Status vocabulary

Use `stable`, `conditional`, `warning`, `fallback-only` or `blocked` for contract areas. These labels describe evidence, not general linguistic quality.
