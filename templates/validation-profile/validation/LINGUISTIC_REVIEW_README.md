# Linguistic review evidence

GF Wordbench can export hash-bound scenario evidence for external linguistic review.

Recommended project workflow:

1. run the required scenarios;
2. export `LINGUISTIC_REVIEW_REQUEST.json`;
3. review the outputs using a named human or AI reviewer;
4. validate/import the structured response;
5. inspect `details/linguistic_review.md`;
6. promote only reviewed, accepted outputs through the explicit gold-update workflow;
7. rerun scenarios against goldens for regression evidence.

Do not store provider credentials in the validation profile. Wordbench's backend is provider-neutral and performs no external AI network calls.
