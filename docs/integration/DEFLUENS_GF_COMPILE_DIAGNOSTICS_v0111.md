# WordBench ↔ Defluens — v0.11.1 diagnostics for actual GF failure

`build_semantik_profile3_candidate.py` remains WordBench's compilation/packaging authority. Its `ProcessRequest` writes `gf-stdout.log` and `gf-stderr.log` in an isolated `semantik-pgf-build-*` work directory. A completed process with nonzero `exit_code` has no `launch_error_message` by design; reporting only that launch field misleadingly produced `"error": ""` for Windows GF 3.12 exit code 1.

This hotfix retains the captured evidence and adds bounded stdout/stderr excerpts, explicit failure classification and paths inside `build-report.json`. The independent, read-only `inspect_semantik_gf_failure.py` also reads old reports that lack this metadata.

Admission gates remain unchanged: successful process state, zero exit code, complete evidence and nonempty expected `.pgf`. Existing candidate contents survive any failed attempt, including `--force`. This patch does **not** change GF source, semantic operations, lexical selection, RuntimeSets, publication or activation. Real GF grammatical conformance is not claimed until Windows GF logs and successful compilation/linearization are inspected.

The affected Windows command is `Qualifier_Candidats_FR_EN_v011.bat --compile-and-real` and its nested `Compiler_Candidats_FR_EN_GF312.bat`. On failure, the most recent matching French/English logs are printed automatically. For previous runs, use the companion Defluens `Diagnostiquer_Echec_GF_v0111.bat` without recompiling.
