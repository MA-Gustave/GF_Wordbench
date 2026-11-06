# Ars Magna Defluens — GF WordBench integration

**2026-11-03** — Canonical orchestrator name: **Ars Magna Defluens**
(formerly **Ars Magna Lulli**, sometimes referred to as **Ars Magna**).

WordBench remains the authority for **GF-backed evidence for one language
project**. Defluens is the intended **cross-project orchestrator**: it may
schedule work and index immutable run artifacts, but it must not rerun a
linguistic verdict or silently change goldens. Observatory reads the resulting
state and preserves unknown/unverified claims.

The 15-capability *practical-generation profile* is a validation profile, not
a distinct ChatSystem application. A `light` or `quick` compile is **not** a
passing practical-generation scenario.

No CLI names, package names, JSON schema tokens, GF source paths, or existing
run artifact identifiers are changed by this naming update. In particular,
legacy machine tokens such as `lulli` must be handled through an explicit
versioned migration if and when an actual Defluens feed uses them.

This note documents **integration intent**, not a claim that the Defluens
GitOps runtime is already implemented.
