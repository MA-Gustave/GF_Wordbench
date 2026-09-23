# GF Wordbench — Linguistic Review Evidence

**Status:** Backend contract  
**Introduced:** 2026-09-22  
**Scope:** external human or AI review of scenario outputs; no GUI contract

## Purpose

Compilation and scenario execution prove technical facts. They do not by themselves prove that generated text is valid in the target language. The linguistic-review backend adds a provider-neutral, hash-bound evidence loop:

1. Wordbench exports `LINGUISTIC_REVIEW_REQUEST.json` from a completed run.
2. A reviewer (human, ChatGPT, or another explicitly identified reviewer) evaluates each normalized scenario output.
3. The reviewer returns `gf-wordbench-linguistic-review-response-v1` JSON.
4. Wordbench rejects responses whose request ID, source-lock SHA-256, scenario IDs, or output hashes do not match the run.
5. Wordbench produces `details/linguistic_review.json` and `details/linguistic_review.md`.
6. Only accepted, sufficiently confident reviews are candidates for the existing explicit gold-update workflow.

Wordbench does **not** call an AI provider directly. Network/provider integration belongs outside this backend contract.

## Verdict vocabulary

- `valid`: grammatical and natural for the declared language variety.
- `valid_variant`: grammatical but stylistically marked, context-dependent, or one of several accepted variants.
- `questionable`: evidence is insufficient or the reviewer is materially uncertain.
- `invalid`: morphologically, syntactically, lexically, or normatively unacceptable for the declared variety.

`questionable` and `invalid` are blocking. Low-confidence reviews are not gold-eligible under the default policy.

## Evidence binding

Every request is bound to:

- run ID;
- source-lock SHA-256;
- GF version;
- language key and declared variety;
- scenario script SHA-256;
- normalized scenario-output SHA-256.

The response must echo the request ID, source lock, scenario ID, and output hash. This prevents a review of one run from silently certifying another run.

## ChatGPT usage

For an Albanian campaign, set `language_variety` to an explicit target such as `Standard Albanian`. Give the exported request JSON to ChatGPT and require a response matching `gf-wordbench-linguistic-review-response-v1` exactly.

The report should be described as **AI-reviewed linguistic validation**, not as independent human linguistic certification. The reviewer identity and model are persisted in the evidence.

## Gold promotion

This backend does not silently update `.gold` files. A passing review only marks scenarios as `gold_eligible_scenarios`. Promotion remains an explicit operation through the existing `GoldUpdateRequest` contract, which already requires reviewer, rationale, decision reference, diff review, confirmation, and atomic write semantics.

## Compendium interpretation

A complete passing linguistic review can provide evidence for `T9 parse_and_generation_behavior`. `T10 regression_validation` is reported only when the same reviewed scenarios are already compared against matching goldens in the source run. This does not automatically promote unexecuted T1–T7 levels.

## Backend API

The stable validation facade exports:

- `build_linguistic_review_request`
- `write_linguistic_review_request`
- `load_linguistic_review_response`
- `evaluate_linguistic_review`
- `write_linguistic_review_evaluation`
- `LinguisticReviewPolicy`
- `LinguisticVerdict`
- `ReviewConfidence`

No GUI modules are modified by this feature.
