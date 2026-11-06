# WordBench source-root authority — Git checkout (v1.2.1)

**Decision:** adopted for the local repository layout, 2026-11-05.

## Authority

The authoritative WordBench checkout is the directory that contains its
`.git`, `pyproject.toml`, and `src/gf_wordbench`:

`C:\mycode\Grammatical-Framework\GF_Wordbench\GF_Wordbench`

The enclosing `GF_Wordbench` directory is a container, not a second checkout
and not a Python package. No duplicate `src/gf_wordbench` subtree is created
inside the Git root. The root owns the Qt application, qualifier, CLI, pilots,
validation, tests, documentation, and release artifacts. WordBench delegates
all grammar execution to GF; Observatory only consumes evidence.

## Toolchain location

`gf-3.12-windows` and `gf-rgl` remain **siblings of the enclosing folder**,
under `Grammatical-Framework`. The shared `workspace_layout` resolver handles
the canonical nested Git checkout and a portable flat checkout. Toolchain
paths can still be selected explicitly. Do not infer toolchains from a
competing copy in the outer wrapper.

## Distribution and validation

The distribution ZIP is **rootless**: its members start at `README.md`,
`pyproject.toml`, `src/...`, etc. It must be extracted directly into the
Git root. It intentionally contains no `.git`, virtual environment, or run
artifacts and does not modify sibling projects.

Regressions test the nested layout, flat portability, path rejection, and
qualifier wiring. Actual Windows Qt/GF execution remains a local acceptance
gate; source-only tests are not linguistic certification.
