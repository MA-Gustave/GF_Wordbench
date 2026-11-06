# GF WordBench — Practical Generation Profile (prototype)

This is an **application suitability profile**, not a new value of the normative
`ValidationMode` enum (`quick`, `checkpoint`, `release`, `diagnostic`). The
`gf-wordbench-practical` CLI subcommands reuse the existing `checkpoint` mode, explicit
validation profiles, scenario runner, and golden output comparisons.

## Profile semantics

`profiles/practical_generation_v1.json` lists 20 semantic capabilities (15
required and 5 optional) across `encyclopedic` and `procedural`. The `required`
flag applies only within the capability's listed domains. A capability maps to
one or more **scenario IDs**, not to fixed GF tenses. Different languages can
implement the same scenario meaning with different forms or paraphrases.

Before running a language, its ordinary WordBench `project.toml` validation
profile must register the matching scenario IDs, and supply locked `.gfs` scripts
and approved `.gold` outputs. The sample practical profile is a **test plan**,
not the GF scenarios themselves. The repository snapshot does not contain a
complete RGL checkout, a GF executable, or such per-language gold data.

## CLI usage

```shell
# Run only required practical scenarios via WordBench's regular validation engine:
python -m gf_wordbench.practical.cli run \
  --language-path /path/to/gf-rgl/src/english \
  --validation-profile /path/to/Eng-validation-profile/project.toml \
  --practical-profile profiles/practical_generation_v1.json \
  --output-root /path/to/wordbench-results

# Alternatively, evaluate an existing completed WordBench run:
python -m gf_wordbench.practical.cli check \
  --summary /path/to/run_YYYYMMDD_HHMMSS/summary.json \
  --practical-profile profiles/practical_generation_v1.json
```

`practical_coverage.json` is an **independent derived sidecar**, not an element
of the canonical run manifest. It does not replace or modify the original
WordBench summary, manifest, release status, or RGL scope. The default sidecar
is written alongside the summary so Observatory can recheck the source hash.

Statuses: `ready` = every required scenario for the domain passed a gold
comparison in a successful compiled run; `needs_work` = at least one required
scenario failed; `unverified` = missing/unevaluated/review-unproven evidence.
An unverified capability must **not** be reported as missing implementation.
Optional capabilities are reported but do not block practical readiness.

The conventional scenario IDs in the JSON profile are stable semantic test
identifiers. They do not prescribe morphology, grammar construction methods,
or a globally identical tense inventory. Translation correctness, factual
accuracy, stylistic naturalness and robustness beyond the chosen gold corpus
still require appropriate human review.

Only CLI support is included in this prototype. It does not change WordBench's
existing GUI, canonical persistence schema, or general release gates.
