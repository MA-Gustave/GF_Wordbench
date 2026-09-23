# GF Wordbench — Canonical Final File Architecture

**Document ID:** `GF-WB-CANONICAL-FILE-ARCHITECTURE`
**Status:** **Normative — final architecture**
**Version:** `1.1.1`
**Date:** `2026-08-03`
**Canonical repository path:** `docs/architecture/CANONICAL_FILE_ARCHITECTURE.md`
**Owner:** GF Wordbench maintainers
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`

---

## 1. Authority

This document is the sole authority for the fixed implementation and test file architecture of the final GF Wordbench product.

It supersedes `docs/REPOSITORY_STRUCTURE.md` and older component-path examples **only for source-code, support-file, and test-file placement**. Behavioral contracts, persisted formats, commands, and product rules remain governed by their dedicated normative documents.

This is not a provisional tree, migration sketch, or starting point. Every fixed path below belongs to the final product architecture.

---

## 2. Fixed file count

| Category | Files |
|---|---:|
| Runtime Python package | 229 |
| Repository support, launch, script, and CI files | 14 |
| Test modules and test helpers | 161 |
| **Total fixed coded files** | **404** |

Existing documentation, project-language content, templates, test fixture payloads, and generated run artifacts are not included in this count because their contents are documentation- or data-driven rather than fixed Python architecture.

### Runtime package distribution

| Source area | Files |
|---|---:|
| `Package root` | 5 |
| `config` | 6 |
| `kernel` | 7 |
| `state` | 5 |
| `projects` | 19 |
| `runs` | 22 |
| `validation` | 54 |
| `diagnostics` | 32 |
| `reporting` | 38 |
| `infrastructure` | 15 |
| `entrypoints` | 28 |
| **Runtime package total** | **231** |

### Test distribution

| Test area | Files |
|---|---:|
| `Test root` | 1 |
| `helpers` | 4 |
| `unit` | 93 |
| `components` | 8 |
| `contracts` | 14 |
| `schemas` | 7 |
| `integration` | 27 |
| `migrations` | 4 |
| `release` | 5 |
| **Test total** | **163** |

---

## 3. Canonical fixed tree

```text
GF_Wordbench/
├── .github/
│   └── workflows/
│       ├── quality.yml
│       ├── real_gf.yml
│       ├── release.yml
│       └── tests.yml
├── scripts/
│   ├── init_project.py
│   ├── migrate_project.py
│   ├── reset_project.py
│   ├── validate_contracts.py
│   ├── validate_schemas.py
│   └── verify_architecture.py
├── src/
│   └── gf_wordbench/
│       ├── config/
│       │   ├── __init__.py
│       │   ├── defaults.py
│       │   ├── environment.py
│       │   ├── models.py
│       │   ├── precedence.py
│       │   └── resolver.py
│       ├── diagnostics/
│       │   ├── classification/
│       │   │   ├── __init__.py
│       │   │   ├── blockers.py
│       │   │   ├── causality.py
│       │   │   ├── relationships.py
│       │   │   ├── service.py
│       │   │   └── top_errors.py
│       │   ├── parsing/
│       │   │   ├── __init__.py
│       │   │   ├── deduplication.py
│       │   │   ├── locations.py
│       │   │   ├── matcher.py
│       │   │   ├── multiline.py
│       │   │   ├── primary.py
│       │   │   ├── service.py
│       │   │   └── streams.py
│       │   ├── patterns/
│       │   │   ├── __init__.py
│       │   │   ├── common.py
│       │   │   ├── compilation.py
│       │   │   ├── pgf.py
│       │   │   ├── processes.py
│       │   │   └── scenarios.py
│       │   ├── tools/
│       │   │   ├── __init__.py
│       │   │   ├── evidence.py
│       │   │   ├── executor.py
│       │   │   ├── models.py
│       │   │   ├── registry.py
│       │   │   └── validator.py
│       │   ├── __init__.py
│       │   ├── findings.py
│       │   ├── models.py
│       │   ├── ports.py
│       │   ├── public.py
│       │   └── vocabulary.py
│       ├── entrypoints/
│       │   ├── cli/
│       │   │   ├── __init__.py
│       │   │   ├── audit_commands.py
│       │   │   ├── exit_codes.py
│       │   │   ├── language_commands.py
│       │   │   ├── main.py
│       │   │   ├── maintenance_commands.py
│       │   │   ├── output.py
│       │   │   ├── parser.py
│       │   │   └── project_commands.py
│       │   ├── gui/
│       │   │   ├── panels/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── artifacts.py
│       │   │   │   ├── diagnostics.py
│       │   │   │   ├── progress.py
│       │   │   │   ├── project.py
│       │   │   │   ├── results.py
│       │   │   │   └── validation.py
│       │   │   ├── __init__.py
│       │   │   ├── controller.py
│       │   │   ├── dialogs.py
│       │   │   ├── main.py
│       │   │   ├── runtime.py
│       │   │   ├── startup.py
│       │   │   ├── view_model.py
│       │   │   ├── widgets.py
│       │   │   ├── window.py
│       │   │   └── workers.py
│       │   ├── __init__.py
│       │   └── automation.py
│       ├── infrastructure/
│       │   ├── process/
│       │   │   ├── __init__.py
│       │   │   ├── launcher.py
│       │   │   ├── models.py
│       │   │   ├── requests.py
│       │   │   ├── runner.py
│       │   │   ├── streams.py
│       │   │   └── termination.py
│       │   ├── __init__.py
│       │   ├── atomic_io.py
│       │   ├── environment.py
│       │   ├── filesystem.py
│       │   ├── json_io.py
│       │   ├── logging.py
│       │   ├── time.py
│       │   └── toml_io.py
│       ├── kernel/
│       │   ├── __init__.py
│       │   ├── errors.py
│       │   ├── events.py
│       │   ├── ids.py
│       │   ├── paths.py
│       │   ├── serialization.py
│       │   └── statuses.py
│       ├── projects/
│       │   ├── __init__.py
│       │   ├── filesystem_adapter.py
│       │   ├── initializer.py
│       │   ├── languages/
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── ports.py
│       │   │   ├── probe.py
│       │   │   └── public.py
│       │   ├── loader.py
│       │   ├── migrator.py
│       │   ├── models.py
│       │   ├── paths.py
│       │   ├── policies.py
│       │   ├── ports.py
│       │   ├── public.py
│       │   ├── resetter.py
│       │   ├── schema.py
│       │   ├── toml_adapter.py
│       │   └── validator.py
│       ├── reporting/
│       │   ├── ai_packet/
│       │   │   ├── __init__.py
│       │   │   ├── evidence.py
│       │   │   ├── excerpts.py
│       │   │   └── renderer.py
│       │   ├── details/
│       │   │   ├── __init__.py
│       │   │   └── writer.py
│       │   ├── logs/
│       │   │   ├── __init__.py
│       │   │   ├── aggregates.py
│       │   │   ├── lifecycle.py
│       │   │   ├── process_streams.py
│       │   │   ├── redaction.py
│       │   │   ├── scan_logs.py
│       │   │   ├── subject_keys.py
│       │   │   └── truncation.py
│       │   ├── manifest/
│       │   │   ├── __init__.py
│       │   │   ├── builder.py
│       │   │   ├── declarations.py
│       │   │   ├── hashing.py
│       │   │   ├── media_types.py
│       │   │   ├── models.py
│       │   │   ├── requiredness.py
│       │   │   └── verifier.py
│       │   ├── schemas/
│       │   │   ├── __init__.py
│       │   │   ├── compatibility.py
│       │   │   ├── manifest_v1.py
│       │   │   ├── migrations.py
│       │   │   ├── registry.py
│       │   │   ├── summary_v1.py
│       │   │   └── validation.py
│       │   ├── summary/
│       │   │   ├── __init__.py
│       │   │   ├── json_writer.py
│       │   │   ├── markdown_writer.py
│       │   │   └── projection.py
│       │   ├── __init__.py
│       │   ├── artifacts.py
│       │   ├── ports.py
│       │   ├── public.py
│       │   └── publisher.py
│       ├── runs/
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── config.py
│       │   │   ├── paths.py
│       │   │   └── results.py
│       │   ├── __init__.py
│       │   ├── application.py
│       │   ├── budgets.py
│       │   ├── cancellation.py
│       │   ├── continuation.py
│       │   ├── finalizer.py
│       │   ├── history.py
│       │   ├── identity.py
│       │   ├── lifecycle.py
│       │   ├── orchestrator.py
│       │   ├── paths.py
│       │   ├── planner.py
│       │   ├── ports.py
│       │   ├── preflight.py
│       │   ├── progress.py
│       │   ├── public.py
│       │   ├── result_builder.py
│       │   └── stage_executor.py
│       ├── state/
│       │   ├── __init__.py
│       │   ├── migrations.py
│       │   ├── models.py
│       │   ├── repository.py
│       │   └── schema.py
│       ├── validation/
│       │   ├── compilation/
│       │   │   ├── __init__.py
│       │   │   ├── artifacts.py
│       │   │   ├── commands.py
│       │   │   ├── gf_adapter.py
│       │   │   ├── models.py
│       │   │   ├── module_compile.py
│       │   │   ├── pgf_build.py
│       │   │   ├── service.py
│       │   │   └── version_probe.py
│       │   ├── regression/
│       │   │   ├── __init__.py
│       │   │   ├── comparator.py
│       │   │   ├── compatibility.py
│       │   │   ├── loader.py
│       │   │   ├── matcher.py
│       │   │   └── models.py
│       │   ├── release/
│       │   │   ├── __init__.py
│       │   │   ├── decision.py
│       │   │   ├── evaluator.py
│       │   │   ├── models.py
│       │   │   └── registry.py
│       │   ├── scanning/
│       │   │   ├── rules/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── declarations.py
│       │   │   │   ├── structure.py
│       │   │   │   └── suspicious.py
│       │   │   ├── __init__.py
│       │   │   ├── masking.py
│       │   │   ├── models.py
│       │   │   ├── registry.py
│       │   │   └── service.py
│       │   ├── scenarios/
│       │   │   ├── __init__.py
│       │   │   ├── artifacts.py
│       │   │   ├── assertion_registry.py
│       │   │   ├── assertions.py
│       │   │   ├── discovery.py
│       │   │   ├── execution.py
│       │   │   ├── gold_compare.py
│       │   │   ├── gold_update.py
│       │   │   ├── markers.py
│       │   │   ├── models.py
│       │   │   ├── normalization.py
│       │   │   ├── parser.py
│       │   │   └── service.py
│       │   ├── selection/
│       │   │   ├── __init__.py
│       │   │   ├── filters.py
│       │   │   ├── models.py
│       │   │   ├── ordering.py
│       │   │   ├── service.py
│       │   │   └── targets.py
│       │   ├── __init__.py
│       │   ├── modes.py
│       │   ├── pipeline.py
│       │   ├── ports.py
│       │   ├── public.py
│       │   └── stage_contracts.py
│       ├── __init__.py
│       ├── __main__.py
│       ├── bootstrap.py
│       ├── py.typed
│       └── version.py
├── tests/
│   ├── components/
│   │   ├── test_app_state.py
│   │   ├── test_bootstrap.py
│   │   ├── test_cli_gui_parity.py
│   │   ├── test_diagnostics_service.py
│   │   ├── test_project_service.py
│   │   ├── test_reporting_service.py
│   │   ├── test_run_orchestrator.py
│   │   └── test_validation_pipeline.py
│   ├── contracts/
│   │   ├── test_artifact_ownership.py
│   │   ├── test_dependency_directions.py
│   │   ├── test_diagnostics_contracts.py
│   │   ├── test_environment_contract.py
│   │   ├── test_extension_registry.py
│   │   ├── test_filesystem_contract.py
│   │   ├── test_model_contracts.py
│   │   ├── test_process_contract.py
│   │   ├── test_product_boundary.py
│   │   ├── test_project_contracts.py
│   │   ├── test_reporting_contracts.py
│   │   ├── test_run_contracts.py
│   │   ├── test_validation_contracts.py
│   │   └── test_windows_contract.py
│   ├── helpers/
│   │   ├── assertions.py
│   │   ├── builders.py
│   │   ├── fake_processes.py
│   │   └── fixture_paths.py
│   ├── integration/
│   │   ├── cli/
│   │   │   ├── test_audit_command.py
│   │   │   ├── test_help_and_errors.py
│   │   │   └── test_maintenance_commands.py
│   │   ├── end_to_end/
│   │   │   ├── test_checkpoint_mode.py
│   │   │   ├── test_diagnostic_mode.py
│   │   │   ├── test_partial_run_finalization.py
│   │   │   ├── test_path_resolved_language_startup.py
│   │   │   ├── test_quick_mode.py
│   │   │   └── test_release_mode.py
│   │   ├── gf/
│   │   │   ├── test_artifact_observation.py
│   │   │   ├── test_compile_failure.py
│   │   │   ├── test_compile_success.py
│   │   │   ├── test_paths_with_spaces.py
│   │   │   ├── test_pgf_build.py
│   │   │   ├── test_scenario_execution.py
│   │   │   ├── test_unicode.py
│   │   │   └── test_version_probe.py
│   │   ├── gui/
│   │   │   ├── test_language_switching.py
│   │   │   ├── test_main_runtime_composition.py
│   │   │   ├── test_run_and_cancel.py
│   │   │   └── test_startup.py
│   │   └── process/
│   │       ├── test_arguments.py
│   │       ├── test_cancellation.py
│   │       ├── test_process_tree.py
│   │       ├── test_stdin.py
│   │       ├── test_stream_capture.py
│   │       └── test_timeout.py
│   ├── migrations/
│   │   ├── test_manifest_migrations.py
│   │   ├── test_project_migrations.py
│   │   ├── test_state_migrations.py
│   │   └── test_summary_migrations.py
│   ├── release/
│   │   ├── test_architecture_manifest.py
│   │   ├── test_documentation_alignment.py
│   │   ├── test_install_smoke.py
│   │   ├── test_package_build.py
│   │   └── test_release_fixture.py
│   ├── schemas/
│   │   ├── test_gold_schema.py
│   │   ├── test_manifest_schema.py
│   │   ├── test_migrations.py
│   │   ├── test_project_schema.py
│   │   ├── test_scenario_output_schema.py
│   │   ├── test_state_schema.py
│   │   └── test_summary_schema.py
│   ├── unit/
│   │   ├── config/
│   │   │   ├── test_defaults.py
│   │   │   ├── test_precedence.py
│   │   │   └── test_resolver.py
│   │   ├── diagnostics/
│   │   │   ├── test_blockers.py
│   │   │   ├── test_classification.py
│   │   │   ├── test_control_panel.py
│   │   │   ├── test_deduplication.py
│   │   │   ├── test_findings.py
│   │   │   ├── test_multiline_and_matching.py
│   │   │   ├── test_patterns.py
│   │   │   ├── test_relationships.py
│   │   │   ├── test_streams_and_locations.py
│   │   │   ├── test_tool_executor.py
│   │   │   ├── test_tool_registry.py
│   │   │   └── test_top_errors.py
│   │   ├── entrypoints/
│   │   │   ├── test_automation.py
│   │   │   ├── test_cli_commands.py
│   │   │   ├── test_cli_exit_codes.py
│   │   │   ├── test_cli_parser.py
│   │   │   ├── test_gui_controller.py
│   │   │   └── test_gui_view_model.py
│   │   ├── infrastructure/
│   │   │   ├── test_atomic_io.py
│   │   │   ├── test_filesystem.py
│   │   │   ├── test_json_toml_io.py
│   │   │   ├── test_process_launcher.py
│   │   │   ├── test_process_requests.py
│   │   │   ├── test_process_runner.py
│   │   │   ├── test_process_streams.py
│   │   │   └── test_process_termination.py
│   │   ├── kernel/
│   │   │   ├── test_ids.py
│   │   │   ├── test_paths.py
│   │   │   ├── test_serialization.py
│   │   │   └── test_statuses.py
│   │   ├── projects/
│   │   │   ├── test_language_probe.py
│   │   │   ├── test_lifecycle.py
│   │   │   ├── test_loader.py
│   │   │   ├── test_migrator.py
│   │   │   ├── test_models.py
│   │   │   ├── test_paths.py
│   │   │   └── test_validator.py
│   │   ├── reporting/
│   │   │   ├── test_ai_packet.py
│   │   │   ├── test_details_writer.py
│   │   │   ├── test_log_writers.py
│   │   │   ├── test_manifest_builder.py
│   │   │   ├── test_manifest_verifier.py
│   │   │   ├── test_publisher.py
│   │   │   ├── test_schema_compatibility.py
│   │   │   ├── test_schema_registry.py
│   │   │   ├── test_summary_projection.py
│   │   │   └── test_summary_writers.py
│   │   ├── runs/
│   │   │   ├── test_application_quick.py
│   │   │   ├── test_budgets.py
│   │   │   ├── test_cancellation.py
│   │   │   ├── test_continuation.py
│   │   │   ├── test_finalizer.py
│   │   │   ├── test_history.py
│   │   │   ├── test_identity_and_paths.py
│   │   │   ├── test_lifecycle.py
│   │   │   ├── test_orchestrator.py
│   │   │   ├── test_planner.py
│   │   │   ├── test_preflight.py
│   │   │   ├── test_result_builder.py
│   │   │   └── test_stage_executor.py
│   │   ├── state/
│   │   │   ├── test_migrations.py
│   │   │   ├── test_repository.py
│   │   │   └── test_schema.py
│   │   └── validation/
│   │       ├── compilation/
│   │       │   ├── test_artifacts.py
│   │       │   ├── test_commands.py
│   │       │   ├── test_module_compile.py
│   │       │   ├── test_pgf_build.py
│   │       │   ├── test_service.py
│   │       │   └── test_version_probe.py
│   │       ├── scanning/
│   │       │   ├── test_masking.py
│   │       │   ├── test_rules_declarations.py
│   │       │   ├── test_rules_structure.py
│   │       │   ├── test_rules_suspicious.py
│   │       │   └── test_service.py
│   │       ├── scenarios/
│   │       │   ├── test_artifacts.py
│   │       │   ├── test_assertions.py
│   │       │   ├── test_discovery_and_parser.py
│   │       │   ├── test_execution.py
│   │       │   ├── test_gold_compare.py
│   │       │   ├── test_gold_update.py
│   │       │   ├── test_markers.py
│   │       │   ├── test_normalization.py
│   │       │   └── test_service.py
│   │       ├── selection/
│   │       │   ├── test_filters.py
│   │       │   ├── test_ordering.py
│   │       │   ├── test_service.py
│   │       │   └── test_targets.py
│   │       ├── test_pipeline.py
│   │       ├── test_regression.py
│   │       └── test_release_gates.py
│   └── conftest.py
├── GF_Wordbench_output_mode_toggle.pyw
├── .gitignore
├── launch_cli.bat
├── launch_gui.bat
└── pyproject.toml
```

---

## 4. Variable-content zones

These directories are part of the final repository, but their contained filenames may vary without changing the fixed code architecture:

```text
docs/                         existing and future normative documentation
project/                      optional repository-local validation profile
templates/validation-profile/ reusable optional-profile template
tests/fixtures/projects/      temporary project fixtures
tests/fixtures/gf/            GF grammar and toolchain fixtures
tests/fixtures/diagnostics/   captured diagnostic evidence
tests/fixtures/schemas/       valid, invalid, and legacy persisted data
tests/fixtures/reports/       expected report fixtures
tests/fixtures/scenarios/     .gfs, input, output, and gold fixtures
tests/fixtures/legacy/        migration fixtures
tests/fixtures/executables/   controlled fake executables
runs/                         generated run directories
build/                        generated build output
dist/                         generated distributions
coverage/                     generated coverage output
```

Variable-content zones must not contain hidden framework policy or private Python plugins.

---

## 5. Split authority

| Concern | Authoritative split |
|---|---|
| Python package layout | `src/gf_wordbench/` replaces the legacy flat `app/` package. |
| Shared models | Only genuinely cross-module values belong in `kernel/`; project, run, validation, diagnostic, state, and reporting models stay with their owning module. |
| Run models | Configuration, paths, and results are separated under `runs/models/`; no giant `runs/models.py`. |
| Orchestration | Complete-run coordination belongs to `runs/`; bounded validation work belongs to `validation/`. |
| External processes | Generic launch, streams, timeout, cancellation, and termination belong to `infrastructure/process/`; GF command semantics remain in `validation/compilation/`. |
| Scenarios | Discovery, parsing, execution, markers, normalization, assertions, artifacts, gold comparison, and gold updating remain separate. Normal validation never calls `gold_update.py`. |
| Diagnostics | Raw parsing, pattern catalogs, causal classification, and approved diagnostic tools are separate packages. |
| Persisted schemas | Project schema belongs to `projects/schema.py`; application-state schema belongs to `state/schema.py`; summary and manifest schemas belong to `reporting/schemas/`. |
| Reporting | Summary, details, logs, AI packet, manifest, and publication are separate owners and never rerun validation. |
| Language startup | `projects/languages/models.py` owns the canonical language contracts; `projects/languages/ports.py` owns probe ports; and `projects.public` is the broad cross-module façade for language startup and optional validation-profile operations. CLI and GUI entrypoints translate user actions, while `bootstrap.py` supplies concrete adapters. The loader resolves exactly one explicit language before constructing the main runtime. |
| Runtime language model | Wordbench remains monolingual while running. Changing language shuts down the current runtime, returns to the loader, resolves a new path, and constructs a fresh monolingual runtime; simultaneous multilingual state is prohibited. |
| GUI | The introduction and language loader precede the main window. The window composes panels; controllers, view models, workers, dialogs, widgets, and panels do not absorb one another. |
| Tests | Tests are grouped by proof responsibility, not one-to-one with source files. Fixture payloads remain in variable-content zones. |

---

## 6. Legacy coarse-file mapping

| Legacy/coarse owner | Final owner |
|---|---|
| `app/config.py` | `config/` |
| `app/models.py` | `kernel/` plus module-owned models |
| `app/state.py` | `state/` |
| `app/audit/audit_core.py` | `runs/` plus `validation/pipeline.py` |
| `app/audit/file_selector.py` | `validation/selection/` |
| `app/audit/scanner.py` | `validation/scanning/` |
| `app/audit/compiler.py` | `validation/compilation/` |
| `app/audit/scenario_runner.py` | `validation/scenarios/` |
| `app/audit/diagnostics.py` | `diagnostics/parsing/` |
| `app/audit/classifier.py` | `diagnostics/classification/` |
| `app/audit/diff.py` | `validation/regression/` |
| `app/audit/result_model.py` | module-owned models plus `runs/result_builder.py` |
| `app/reports/*` | `reporting/` subpackages |
| `app/utils/process_utils.py` | `infrastructure/process/` |
| `app/utils/io_utils.py` | explicit infrastructure adapters |
| `app/gui/main_window.py` | `entrypoints/gui/` |

---

## 7. File-boundary rules

1. No generic `utils.py`, `common.py`, `shared.py`, or universal `models.py` may be introduced.
2. `public.py` files expose stable cross-module APIs only. `projects.public` is the broad project façade and re-exports language contracts directly from `projects/languages/models.py` and language operations from `projects/languages/public.py`.
3. `ports.py` files contain protocols and contracts, never concrete filesystem or process behavior.
4. Adapters may depend outward; domain and application logic may not import entrypoints.
5. A package must not be split into one-class-per-file fragments.
6. A new fixed source or test file requires an amendment to this document and a passing architecture-manifest test.
7. Removing or merging a listed file also requires an amendment; empty placeholder modules are prohibited.
8. `SelectedPathKind`, `LanguageCapability`, `LanguageProbeStatus`, `LanguageProbeSeverity`, `LanguageProbeRequest`, `LanguageProbeDiagnostic`, `LanguageModuleCandidate`, `LanguageCandidate`, `ResolvedLanguageContext`, and `LanguageProbeResult` are canonically owned by `projects/languages/models.py`; entrypoints and façades must re-export rather than redefine or rename them.
9. `__init__.py` files remain narrow and side-effect free.

---

## 8. Dependency direction

```text
entrypoints
    → bootstrap
    → projects/languages public language-loader API
    → runs application coordination
    → projects / validation / diagnostics / reporting public APIs
    → ports
    → adapters and infrastructure
    → filesystem, operating system, GF, and approved tools
```

Additional invariants:

```text
projects      -X→ runs, validation, diagnostics, reporting
validation    -X→ reporting or entrypoints
diagnostics   -X→ GF execution internals or reporting
reporting     -X→ validation execution
infrastructure-X→ product policy
framework     -X→ gf-portfolio internals
```

---

## 9. Change control

`scripts/verify_architecture.py` and `tests/release/test_architecture_manifest.py` must verify the fixed path set in this document.

A structural change is accepted only when all of the following change together:

```text
this document
the architecture verification script
the architecture-manifest test
affected import-boundary tests
affected owner documentation
```

Until such a coordinated amendment is accepted, the tree in Section 3 is final and authoritative.
