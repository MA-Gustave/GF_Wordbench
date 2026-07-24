# Albanian (`Sqi`) — Morphology Specification

**Document role:** Project morphology contract  
**Decision status:** Project-owned  
**Implementation status:** Morphology checkpoint is configured; linguistic coverage is not reverified  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Scope

This specification governs project-owned morphological parameters, records, tables, paradigms and category integrations. Exact GF symbols must be confirmed in source before use.

## Documented ownership

- `MorphoSqi.gf` is a configured morphology checkpoint.
- Paradigm helpers, category modules, lexicon modules, structural modules and entrypoints consume morphology according to the dependency contract.
- Morphological state is represented structurally before surface realization.

## Required distinctions

The project documentation identifies noun number, definiteness, case and gender; adjective agreement and degree; verb agreement, tense/aspect/mood, voice and non-finite forms; and pronoun/clitic distinctions as areas that must be represented where supported by the source.

## Invariants

- Inflection tables are total over their declared parameter domain.
- Irregular forms are explicit and testable.
- Orthographic transformations are centralized and Unicode-safe.
- Stem derivation is conservative and does not guess unsupported forms.
- Category lincats preserve information needed by syntax.
- Lexicon entries use public paradigms rather than copying morphology.
- Fallback or incomplete forms remain labeled and cannot satisfy release coverage silently.

## Evidence

Morphology is verified through checkpoint compilation, table inspection where supported, morphology scenarios, representative lexical cases and gold comparisons for deterministic output.
