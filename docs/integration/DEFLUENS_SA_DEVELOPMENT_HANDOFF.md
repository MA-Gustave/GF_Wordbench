# Defluens → SemantiK development evidence handoff (candidate only)

`Lancer_Handoff_SemantiK.bat` reads the latest completed full practical batch ZIP
from Downloads (or an explicit archive argument) and writes `semantik_handoff.json`.
It uses the recorded **15 capabilities × 14 pilot languages**, references all GF
candidate outcomes, and proposes their SA↔GF operation correspondences.

This is **not** a WordBench `gf-wordbench.artifact-manifest/1.0` READY release,
not an admitted SA candidate bundle, not a PGF, not gold approval and not
proof of semantic conformance. Source/script SHA-256 values are **reported**
from the archive, not independently re-hashed against the GF source tree.

The explicit gaps `condition-real`, `source-attribution` and
`conditional-instruction` cannot be silently represented by existing
SA↔GF v1 operation IDs. Several other capabilities need feature-level
conformance. The separate SA repository owns contract extensions; GF/RGL and
WordBench own grammatical implementations. Runtime Orchestrator owns promotion.

Next: create real immutable PGF/lexical/bridge candidate bundles, run the
existing `CandidateMatrixConformance` / candidate suite, then apply the normal
release gate. The handoff JSON never authorizes publication.
