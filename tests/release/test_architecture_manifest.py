"""Release lock for the canonical GF Wordbench fixed-file architecture.

This test intentionally embeds the complete fixed path manifest. A structural
change therefore requires a coordinated edit to the normative architecture
document, ``scripts/verify_architecture.py``, and this release test.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import re
from types import ModuleType
from typing import Final


EXPECTED_TOTAL: Final = 393
EXPECTED_MANIFEST_SHA256: Final = "2261e217a68600a1cbbf56bad888b134a0d482385eb9e8ba615b2de524f3d348"

EXPECTED_CATEGORY_COUNTS: Final = {
    "runtime": 222,
    "support": 14,
    "tests": 157,
}

EXPECTED_RUNTIME_COUNTS: Final = {
    "package_root": 5,
    "config": 6,
    "kernel": 7,
    "state": 5,
    "projects": 14,
    "runs": 21,
    "validation": 54,
    "diagnostics": 32,
    "reporting": 38,
    "infrastructure": 15,
    "entrypoints": 25,
}

EXPECTED_TEST_COUNTS: Final = {
    "test_root": 1,
    "helpers": 4,
    "unit": 90,
    "components": 8,
    "contracts": 14,
    "schemas": 7,
    "integration": 24,
    "migrations": 4,
    "release": 5,
}

_DOCUMENT_CANDIDATES: Final = (
    Path("docs/architecture/CANONICAL_FILE_ARCHITECTURE.md"),
    Path("docs/GF_WORDBENCH_CANONICAL_FILE_ARCHITECTURE.md"),
)

_MANIFEST_TEXT: Final = """\
.github/workflows/quality.yml
.github/workflows/real_gf.yml
.github/workflows/release.yml
.github/workflows/tests.yml
.gitignore
launch_cli.bat
launch_gui.bat
pyproject.toml
scripts/init_project.py
scripts/migrate_project.py
scripts/reset_project.py
scripts/validate_contracts.py
scripts/validate_schemas.py
scripts/verify_architecture.py
src/gf_wordbench/__init__.py
src/gf_wordbench/__main__.py
src/gf_wordbench/bootstrap.py
src/gf_wordbench/config/__init__.py
src/gf_wordbench/config/defaults.py
src/gf_wordbench/config/environment.py
src/gf_wordbench/config/models.py
src/gf_wordbench/config/precedence.py
src/gf_wordbench/config/resolver.py
src/gf_wordbench/diagnostics/__init__.py
src/gf_wordbench/diagnostics/classification/__init__.py
src/gf_wordbench/diagnostics/classification/blockers.py
src/gf_wordbench/diagnostics/classification/causality.py
src/gf_wordbench/diagnostics/classification/relationships.py
src/gf_wordbench/diagnostics/classification/service.py
src/gf_wordbench/diagnostics/classification/top_errors.py
src/gf_wordbench/diagnostics/findings.py
src/gf_wordbench/diagnostics/models.py
src/gf_wordbench/diagnostics/parsing/__init__.py
src/gf_wordbench/diagnostics/parsing/deduplication.py
src/gf_wordbench/diagnostics/parsing/locations.py
src/gf_wordbench/diagnostics/parsing/matcher.py
src/gf_wordbench/diagnostics/parsing/multiline.py
src/gf_wordbench/diagnostics/parsing/primary.py
src/gf_wordbench/diagnostics/parsing/service.py
src/gf_wordbench/diagnostics/parsing/streams.py
src/gf_wordbench/diagnostics/patterns/__init__.py
src/gf_wordbench/diagnostics/patterns/common.py
src/gf_wordbench/diagnostics/patterns/compilation.py
src/gf_wordbench/diagnostics/patterns/pgf.py
src/gf_wordbench/diagnostics/patterns/processes.py
src/gf_wordbench/diagnostics/patterns/scenarios.py
src/gf_wordbench/diagnostics/ports.py
src/gf_wordbench/diagnostics/public.py
src/gf_wordbench/diagnostics/tools/__init__.py
src/gf_wordbench/diagnostics/tools/evidence.py
src/gf_wordbench/diagnostics/tools/executor.py
src/gf_wordbench/diagnostics/tools/models.py
src/gf_wordbench/diagnostics/tools/registry.py
src/gf_wordbench/diagnostics/tools/validator.py
src/gf_wordbench/diagnostics/vocabulary.py
src/gf_wordbench/entrypoints/__init__.py
src/gf_wordbench/entrypoints/automation.py
src/gf_wordbench/entrypoints/cli/__init__.py
src/gf_wordbench/entrypoints/cli/audit_commands.py
src/gf_wordbench/entrypoints/cli/exit_codes.py
src/gf_wordbench/entrypoints/cli/main.py
src/gf_wordbench/entrypoints/cli/maintenance_commands.py
src/gf_wordbench/entrypoints/cli/output.py
src/gf_wordbench/entrypoints/cli/parser.py
src/gf_wordbench/entrypoints/cli/project_commands.py
src/gf_wordbench/entrypoints/gui/__init__.py
src/gf_wordbench/entrypoints/gui/controller.py
src/gf_wordbench/entrypoints/gui/dialogs.py
src/gf_wordbench/entrypoints/gui/main.py
src/gf_wordbench/entrypoints/gui/panels/__init__.py
src/gf_wordbench/entrypoints/gui/panels/artifacts.py
src/gf_wordbench/entrypoints/gui/panels/diagnostics.py
src/gf_wordbench/entrypoints/gui/panels/progress.py
src/gf_wordbench/entrypoints/gui/panels/project.py
src/gf_wordbench/entrypoints/gui/panels/results.py
src/gf_wordbench/entrypoints/gui/panels/validation.py
src/gf_wordbench/entrypoints/gui/view_model.py
src/gf_wordbench/entrypoints/gui/widgets.py
src/gf_wordbench/entrypoints/gui/window.py
src/gf_wordbench/entrypoints/gui/workers.py
src/gf_wordbench/infrastructure/__init__.py
src/gf_wordbench/infrastructure/atomic_io.py
src/gf_wordbench/infrastructure/environment.py
src/gf_wordbench/infrastructure/filesystem.py
src/gf_wordbench/infrastructure/json_io.py
src/gf_wordbench/infrastructure/logging.py
src/gf_wordbench/infrastructure/process/__init__.py
src/gf_wordbench/infrastructure/process/launcher.py
src/gf_wordbench/infrastructure/process/models.py
src/gf_wordbench/infrastructure/process/requests.py
src/gf_wordbench/infrastructure/process/runner.py
src/gf_wordbench/infrastructure/process/streams.py
src/gf_wordbench/infrastructure/process/termination.py
src/gf_wordbench/infrastructure/time.py
src/gf_wordbench/infrastructure/toml_io.py
src/gf_wordbench/kernel/__init__.py
src/gf_wordbench/kernel/errors.py
src/gf_wordbench/kernel/events.py
src/gf_wordbench/kernel/ids.py
src/gf_wordbench/kernel/paths.py
src/gf_wordbench/kernel/serialization.py
src/gf_wordbench/kernel/statuses.py
src/gf_wordbench/projects/__init__.py
src/gf_wordbench/projects/filesystem_adapter.py
src/gf_wordbench/projects/initializer.py
src/gf_wordbench/projects/loader.py
src/gf_wordbench/projects/migrator.py
src/gf_wordbench/projects/models.py
src/gf_wordbench/projects/paths.py
src/gf_wordbench/projects/policies.py
src/gf_wordbench/projects/ports.py
src/gf_wordbench/projects/public.py
src/gf_wordbench/projects/resetter.py
src/gf_wordbench/projects/schema.py
src/gf_wordbench/projects/toml_adapter.py
src/gf_wordbench/projects/validator.py
src/gf_wordbench/py.typed
src/gf_wordbench/reporting/__init__.py
src/gf_wordbench/reporting/ai_packet/__init__.py
src/gf_wordbench/reporting/ai_packet/evidence.py
src/gf_wordbench/reporting/ai_packet/excerpts.py
src/gf_wordbench/reporting/ai_packet/renderer.py
src/gf_wordbench/reporting/artifacts.py
src/gf_wordbench/reporting/details/__init__.py
src/gf_wordbench/reporting/details/writer.py
src/gf_wordbench/reporting/logs/__init__.py
src/gf_wordbench/reporting/logs/aggregates.py
src/gf_wordbench/reporting/logs/lifecycle.py
src/gf_wordbench/reporting/logs/process_streams.py
src/gf_wordbench/reporting/logs/redaction.py
src/gf_wordbench/reporting/logs/scan_logs.py
src/gf_wordbench/reporting/logs/subject_keys.py
src/gf_wordbench/reporting/logs/truncation.py
src/gf_wordbench/reporting/manifest/__init__.py
src/gf_wordbench/reporting/manifest/builder.py
src/gf_wordbench/reporting/manifest/declarations.py
src/gf_wordbench/reporting/manifest/hashing.py
src/gf_wordbench/reporting/manifest/media_types.py
src/gf_wordbench/reporting/manifest/models.py
src/gf_wordbench/reporting/manifest/requiredness.py
src/gf_wordbench/reporting/manifest/verifier.py
src/gf_wordbench/reporting/ports.py
src/gf_wordbench/reporting/public.py
src/gf_wordbench/reporting/publisher.py
src/gf_wordbench/reporting/schemas/__init__.py
src/gf_wordbench/reporting/schemas/compatibility.py
src/gf_wordbench/reporting/schemas/manifest_v1.py
src/gf_wordbench/reporting/schemas/migrations.py
src/gf_wordbench/reporting/schemas/registry.py
src/gf_wordbench/reporting/schemas/summary_v1.py
src/gf_wordbench/reporting/schemas/validation.py
src/gf_wordbench/reporting/summary/__init__.py
src/gf_wordbench/reporting/summary/json_writer.py
src/gf_wordbench/reporting/summary/markdown_writer.py
src/gf_wordbench/reporting/summary/projection.py
src/gf_wordbench/runs/__init__.py
src/gf_wordbench/runs/budgets.py
src/gf_wordbench/runs/cancellation.py
src/gf_wordbench/runs/continuation.py
src/gf_wordbench/runs/finalizer.py
src/gf_wordbench/runs/history.py
src/gf_wordbench/runs/identity.py
src/gf_wordbench/runs/lifecycle.py
src/gf_wordbench/runs/models/__init__.py
src/gf_wordbench/runs/models/config.py
src/gf_wordbench/runs/models/paths.py
src/gf_wordbench/runs/models/results.py
src/gf_wordbench/runs/orchestrator.py
src/gf_wordbench/runs/paths.py
src/gf_wordbench/runs/planner.py
src/gf_wordbench/runs/ports.py
src/gf_wordbench/runs/preflight.py
src/gf_wordbench/runs/progress.py
src/gf_wordbench/runs/public.py
src/gf_wordbench/runs/result_builder.py
src/gf_wordbench/runs/stage_executor.py
src/gf_wordbench/state/__init__.py
src/gf_wordbench/state/migrations.py
src/gf_wordbench/state/models.py
src/gf_wordbench/state/repository.py
src/gf_wordbench/state/schema.py
src/gf_wordbench/validation/__init__.py
src/gf_wordbench/validation/compilation/__init__.py
src/gf_wordbench/validation/compilation/artifacts.py
src/gf_wordbench/validation/compilation/commands.py
src/gf_wordbench/validation/compilation/gf_adapter.py
src/gf_wordbench/validation/compilation/models.py
src/gf_wordbench/validation/compilation/module_compile.py
src/gf_wordbench/validation/compilation/pgf_build.py
src/gf_wordbench/validation/compilation/service.py
src/gf_wordbench/validation/compilation/version_probe.py
src/gf_wordbench/validation/modes.py
src/gf_wordbench/validation/pipeline.py
src/gf_wordbench/validation/ports.py
src/gf_wordbench/validation/public.py
src/gf_wordbench/validation/regression/__init__.py
src/gf_wordbench/validation/regression/comparator.py
src/gf_wordbench/validation/regression/compatibility.py
src/gf_wordbench/validation/regression/loader.py
src/gf_wordbench/validation/regression/matcher.py
src/gf_wordbench/validation/regression/models.py
src/gf_wordbench/validation/release/__init__.py
src/gf_wordbench/validation/release/decision.py
src/gf_wordbench/validation/release/evaluator.py
src/gf_wordbench/validation/release/models.py
src/gf_wordbench/validation/release/registry.py
src/gf_wordbench/validation/scanning/__init__.py
src/gf_wordbench/validation/scanning/masking.py
src/gf_wordbench/validation/scanning/models.py
src/gf_wordbench/validation/scanning/registry.py
src/gf_wordbench/validation/scanning/rules/__init__.py
src/gf_wordbench/validation/scanning/rules/declarations.py
src/gf_wordbench/validation/scanning/rules/structure.py
src/gf_wordbench/validation/scanning/rules/suspicious.py
src/gf_wordbench/validation/scanning/service.py
src/gf_wordbench/validation/scenarios/__init__.py
src/gf_wordbench/validation/scenarios/artifacts.py
src/gf_wordbench/validation/scenarios/assertion_registry.py
src/gf_wordbench/validation/scenarios/assertions.py
src/gf_wordbench/validation/scenarios/discovery.py
src/gf_wordbench/validation/scenarios/execution.py
src/gf_wordbench/validation/scenarios/gold_compare.py
src/gf_wordbench/validation/scenarios/gold_update.py
src/gf_wordbench/validation/scenarios/markers.py
src/gf_wordbench/validation/scenarios/models.py
src/gf_wordbench/validation/scenarios/normalization.py
src/gf_wordbench/validation/scenarios/parser.py
src/gf_wordbench/validation/scenarios/service.py
src/gf_wordbench/validation/selection/__init__.py
src/gf_wordbench/validation/selection/filters.py
src/gf_wordbench/validation/selection/models.py
src/gf_wordbench/validation/selection/ordering.py
src/gf_wordbench/validation/selection/service.py
src/gf_wordbench/validation/selection/targets.py
src/gf_wordbench/validation/stage_contracts.py
src/gf_wordbench/version.py
tests/components/test_app_state.py
tests/components/test_bootstrap.py
tests/components/test_cli_gui_parity.py
tests/components/test_diagnostics_service.py
tests/components/test_project_service.py
tests/components/test_reporting_service.py
tests/components/test_run_orchestrator.py
tests/components/test_validation_pipeline.py
tests/conftest.py
tests/contracts/test_artifact_ownership.py
tests/contracts/test_dependency_directions.py
tests/contracts/test_diagnostics_contracts.py
tests/contracts/test_environment_contract.py
tests/contracts/test_extension_registry.py
tests/contracts/test_filesystem_contract.py
tests/contracts/test_model_contracts.py
tests/contracts/test_process_contract.py
tests/contracts/test_product_boundary.py
tests/contracts/test_project_contracts.py
tests/contracts/test_reporting_contracts.py
tests/contracts/test_run_contracts.py
tests/contracts/test_validation_contracts.py
tests/contracts/test_windows_contract.py
tests/helpers/assertions.py
tests/helpers/builders.py
tests/helpers/fake_processes.py
tests/helpers/fixture_paths.py
tests/integration/cli/test_audit_command.py
tests/integration/cli/test_help_and_errors.py
tests/integration/cli/test_maintenance_commands.py
tests/integration/end_to_end/test_checkpoint_mode.py
tests/integration/end_to_end/test_diagnostic_mode.py
tests/integration/end_to_end/test_partial_run_finalization.py
tests/integration/end_to_end/test_quick_mode.py
tests/integration/end_to_end/test_release_mode.py
tests/integration/gf/test_artifact_observation.py
tests/integration/gf/test_compile_failure.py
tests/integration/gf/test_compile_success.py
tests/integration/gf/test_paths_with_spaces.py
tests/integration/gf/test_pgf_build.py
tests/integration/gf/test_scenario_execution.py
tests/integration/gf/test_unicode.py
tests/integration/gf/test_version_probe.py
tests/integration/gui/test_run_and_cancel.py
tests/integration/gui/test_startup.py
tests/integration/process/test_arguments.py
tests/integration/process/test_cancellation.py
tests/integration/process/test_process_tree.py
tests/integration/process/test_stdin.py
tests/integration/process/test_stream_capture.py
tests/integration/process/test_timeout.py
tests/migrations/test_manifest_migrations.py
tests/migrations/test_project_migrations.py
tests/migrations/test_state_migrations.py
tests/migrations/test_summary_migrations.py
tests/release/test_architecture_manifest.py
tests/release/test_documentation_alignment.py
tests/release/test_install_smoke.py
tests/release/test_package_build.py
tests/release/test_release_fixture.py
tests/schemas/test_gold_schema.py
tests/schemas/test_manifest_schema.py
tests/schemas/test_migrations.py
tests/schemas/test_project_schema.py
tests/schemas/test_scenario_output_schema.py
tests/schemas/test_state_schema.py
tests/schemas/test_summary_schema.py
tests/unit/config/test_defaults.py
tests/unit/config/test_precedence.py
tests/unit/config/test_resolver.py
tests/unit/diagnostics/test_blockers.py
tests/unit/diagnostics/test_classification.py
tests/unit/diagnostics/test_deduplication.py
tests/unit/diagnostics/test_findings.py
tests/unit/diagnostics/test_multiline_and_matching.py
tests/unit/diagnostics/test_patterns.py
tests/unit/diagnostics/test_relationships.py
tests/unit/diagnostics/test_streams_and_locations.py
tests/unit/diagnostics/test_tool_executor.py
tests/unit/diagnostics/test_tool_registry.py
tests/unit/diagnostics/test_top_errors.py
tests/unit/entrypoints/test_automation.py
tests/unit/entrypoints/test_cli_commands.py
tests/unit/entrypoints/test_cli_exit_codes.py
tests/unit/entrypoints/test_cli_parser.py
tests/unit/entrypoints/test_gui_controller.py
tests/unit/entrypoints/test_gui_view_model.py
tests/unit/infrastructure/test_atomic_io.py
tests/unit/infrastructure/test_filesystem.py
tests/unit/infrastructure/test_json_toml_io.py
tests/unit/infrastructure/test_process_launcher.py
tests/unit/infrastructure/test_process_requests.py
tests/unit/infrastructure/test_process_runner.py
tests/unit/infrastructure/test_process_streams.py
tests/unit/infrastructure/test_process_termination.py
tests/unit/kernel/test_ids.py
tests/unit/kernel/test_paths.py
tests/unit/kernel/test_serialization.py
tests/unit/kernel/test_statuses.py
tests/unit/projects/test_lifecycle.py
tests/unit/projects/test_loader.py
tests/unit/projects/test_migrator.py
tests/unit/projects/test_models.py
tests/unit/projects/test_paths.py
tests/unit/projects/test_validator.py
tests/unit/reporting/test_ai_packet.py
tests/unit/reporting/test_details_writer.py
tests/unit/reporting/test_log_writers.py
tests/unit/reporting/test_manifest_builder.py
tests/unit/reporting/test_manifest_verifier.py
tests/unit/reporting/test_publisher.py
tests/unit/reporting/test_schema_compatibility.py
tests/unit/reporting/test_schema_registry.py
tests/unit/reporting/test_summary_projection.py
tests/unit/reporting/test_summary_writers.py
tests/unit/runs/test_budgets.py
tests/unit/runs/test_cancellation.py
tests/unit/runs/test_continuation.py
tests/unit/runs/test_finalizer.py
tests/unit/runs/test_history.py
tests/unit/runs/test_identity_and_paths.py
tests/unit/runs/test_lifecycle.py
tests/unit/runs/test_orchestrator.py
tests/unit/runs/test_planner.py
tests/unit/runs/test_preflight.py
tests/unit/runs/test_result_builder.py
tests/unit/runs/test_stage_executor.py
tests/unit/state/test_migrations.py
tests/unit/state/test_repository.py
tests/unit/state/test_schema.py
tests/unit/validation/compilation/test_artifacts.py
tests/unit/validation/compilation/test_commands.py
tests/unit/validation/compilation/test_module_compile.py
tests/unit/validation/compilation/test_pgf_build.py
tests/unit/validation/compilation/test_service.py
tests/unit/validation/compilation/test_version_probe.py
tests/unit/validation/scanning/test_masking.py
tests/unit/validation/scanning/test_rules_declarations.py
tests/unit/validation/scanning/test_rules_structure.py
tests/unit/validation/scanning/test_rules_suspicious.py
tests/unit/validation/scanning/test_service.py
tests/unit/validation/scenarios/test_artifacts.py
tests/unit/validation/scenarios/test_assertions.py
tests/unit/validation/scenarios/test_discovery_and_parser.py
tests/unit/validation/scenarios/test_execution.py
tests/unit/validation/scenarios/test_gold_compare.py
tests/unit/validation/scenarios/test_gold_update.py
tests/unit/validation/scenarios/test_markers.py
tests/unit/validation/scenarios/test_normalization.py
tests/unit/validation/scenarios/test_service.py
tests/unit/validation/selection/test_filters.py
tests/unit/validation/selection/test_ordering.py
tests/unit/validation/selection/test_service.py
tests/unit/validation/selection/test_targets.py
tests/unit/validation/test_pipeline.py
tests/unit/validation/test_regression.py
tests/unit/validation/test_release_gates.py
"""

EXPECTED_FIXED_PATHS: Final = frozenset(_MANIFEST_TEXT.splitlines())

_IGNORED_DIRECTORY_NAMES: Final = frozenset(
    {
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "build",
        "coverage",
        "dist",
        "htmlcov",
    }
)


def _repository_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    if not (root / "pyproject.toml").is_file():
        raise AssertionError(
            f"Could not locate repository root from {__file__!r}"
        )
    return root


def _manifest_digest(paths: frozenset[str] | set[str]) -> str:
    payload = "\n".join(sorted(paths)) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _category(path: str) -> str:
    if path.startswith("src/gf_wordbench/"):
        return "runtime"
    if path.startswith("tests/"):
        return "tests"
    return "support"


def _runtime_area(path: str) -> str:
    relative = path.removeprefix("src/gf_wordbench/")
    if "/" not in relative:
        return "package_root"
    return relative.split("/", 1)[0]


def _test_area(path: str) -> str:
    relative = path.removeprefix("tests/")
    if "/" not in relative:
        return "test_root"
    return relative.split("/", 1)[0]


def _normative_document(root: Path) -> Path:
    for relative in _DOCUMENT_CANDIDATES:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    expected = ", ".join(path.as_posix() for path in _DOCUMENT_CANDIDATES)
    raise AssertionError(
        "Canonical architecture document is missing; expected one of: "
        f"{expected}"
    )


def _parse_document_manifest(text: str) -> frozenset[str]:
    section = re.search(
        r"^## 3\. Canonical fixed tree\s*$"
        r".*?^```text\s*$"
        r"(?P<tree>.*?)"
        r"^```\s*$",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if section is None:
        raise AssertionError(
            "Canonical architecture document has no Section 3 text tree"
        )

    lines = section.group("tree").splitlines()
    if not lines or lines[0].strip() != "GF_Wordbench/":
        raise AssertionError(
            "Canonical architecture tree must start with GF_Wordbench/"
        )

    files: list[str] = []
    stack: list[str] = []
    item_pattern = re.compile(
        r"^(?P<prefix>(?:│   |    )*)(?:├── |└── )(?P<name>.+)$"
    )

    for line_number, line in enumerate(lines[1:], start=2):
        item = item_pattern.fullmatch(line)
        if item is None:
            if line.strip():
                raise AssertionError(
                    "Malformed canonical tree line "
                    f"{line_number}: {line!r}"
                )
            continue

        prefix = item.group("prefix")
        if len(prefix) % 4:
            raise AssertionError(
                "Malformed canonical tree indentation on line "
                f"{line_number}"
            )

        depth = len(prefix) // 4
        if depth > len(stack):
            raise AssertionError(
                "Canonical tree skips a directory level on line "
                f"{line_number}"
            )

        name = item.group("name").strip()
        if not name or name in {".", ".."}:
            raise AssertionError(
                f"Invalid canonical tree entry on line {line_number}"
            )

        stack = stack[:depth]
        if name.endswith("/"):
            stack.append(name[:-1])
            continue

        files.append("/".join((*stack, name)))

    if len(files) != len(set(files)):
        duplicates = sorted(
            path
            for path, count in Counter(files).items()
            if count > 1
        )
        raise AssertionError(
            "Canonical document contains duplicate paths: "
            + ", ".join(duplicates)
        )

    return frozenset(files)


def _is_ignored(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part in _IGNORED_DIRECTORY_NAMES for part in relative.parts)


def _collect_repository_fixed_paths(root: Path) -> frozenset[str]:
    collected: set[str] = set()

    fixed_roots = (
        root / ".github" / "workflows",
        root / "scripts",
        root / "src" / "gf_wordbench",
        root / "tests",
    )

    for fixed_root in fixed_roots:
        if not fixed_root.exists():
            continue
        for candidate in fixed_root.rglob("*"):
            if not candidate.is_file() or _is_ignored(candidate, root):
                continue

            relative = candidate.relative_to(root)
            if relative.parts[:2] == ("tests", "fixtures"):
                continue

            if relative.parts[0] == "scripts" and candidate.suffix != ".py":
                continue

            if relative.parts[0] == "tests" and candidate.suffix != ".py":
                continue

            collected.add(relative.as_posix())

    root_code_names = {
        ".gitignore",
        "launch_cli.bat",
        "launch_gui.bat",
        "pyproject.toml",
    }
    root_code_suffixes = {
        ".bat",
        ".py",
        ".pyi",
        ".pyw",
        ".toml",
        ".yaml",
        ".yml",
    }
    for candidate in root.iterdir():
        if not candidate.is_file():
            continue
        if (
            candidate.name in root_code_names
            or candidate.suffix.lower() in root_code_suffixes
        ):
            collected.add(candidate.name)

    return frozenset(collected)


def _format_difference(
    *,
    missing: set[str],
    unexpected: set[str],
) -> str:
    lines: list[str] = []
    if missing:
        lines.append("Missing canonical paths:")
        lines.extend(f"  - {path}" for path in sorted(missing))
    if unexpected:
        if lines:
            lines.append("")
        lines.append("Unexpected fixed-zone paths:")
        lines.extend(f"  + {path}" for path in sorted(unexpected))
    return "\n".join(lines) or "No manifest differences."


def _load_verifier(root: Path) -> ModuleType:
    script = root / "scripts" / "verify_architecture.py"
    if not script.is_file():
        raise AssertionError(f"Architecture verifier is missing: {script}")

    specification = importlib.util.spec_from_file_location(
        "_gf_wordbench_verify_architecture",
        script,
    )
    if specification is None or specification.loader is None:
        raise AssertionError(
            f"Could not load architecture verifier: {script}"
        )

    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _render_verifier_failure(result: object) -> str:
    findings = getattr(result, "findings", ())
    rendered: list[str] = []
    for finding in findings:
        render = getattr(finding, "render", None)
        rendered.append(
            str(render()) if callable(render) else str(finding)
        )
    return "\n".join(rendered) or repr(result)


def test_embedded_release_manifest_is_self_consistent() -> None:
    assert len(EXPECTED_FIXED_PATHS) == EXPECTED_TOTAL
    assert _manifest_digest(EXPECTED_FIXED_PATHS) == (
        EXPECTED_MANIFEST_SHA256
    )

    assert Counter(
        _category(path) for path in EXPECTED_FIXED_PATHS
    ) == Counter(EXPECTED_CATEGORY_COUNTS)

    assert Counter(
        _runtime_area(path)
        for path in EXPECTED_FIXED_PATHS
        if _category(path) == "runtime"
    ) == Counter(EXPECTED_RUNTIME_COUNTS)

    assert Counter(
        _test_area(path)
        for path in EXPECTED_FIXED_PATHS
        if _category(path) == "tests"
    ) == Counter(EXPECTED_TEST_COUNTS)


def test_normative_document_matches_release_manifest() -> None:
    root = _repository_root()
    document = _normative_document(root)
    documented = _parse_document_manifest(
        document.read_text(encoding="utf-8")
    )

    missing = set(EXPECTED_FIXED_PATHS - documented)
    unexpected = set(documented - EXPECTED_FIXED_PATHS)
    assert documented == EXPECTED_FIXED_PATHS, _format_difference(
        missing=missing,
        unexpected=unexpected,
    )


def test_repository_fixed_zones_match_release_manifest() -> None:
    root = _repository_root()
    observed = _collect_repository_fixed_paths(root)

    missing = set(EXPECTED_FIXED_PATHS - observed)
    unexpected = set(observed - EXPECTED_FIXED_PATHS)
    assert observed == EXPECTED_FIXED_PATHS, _format_difference(
        missing=missing,
        unexpected=unexpected,
    )


def test_architecture_verifier_accepts_release_tree() -> None:
    root = _repository_root()
    verifier = _load_verifier(root)

    verify = getattr(verifier, "verify", None)
    assert callable(verify), (
        "scripts/verify_architecture.py must expose verify(root)"
    )

    result = verify(root)
    assert getattr(result, "passed", False), _render_verifier_failure(
        result
    )
