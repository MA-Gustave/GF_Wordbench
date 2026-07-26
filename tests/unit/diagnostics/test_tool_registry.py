from __future__ import annotations

from dataclasses import replace

import pytest

from gf_wordbench.diagnostics.tools.models import (
    DiagnosticToolSpec,
    ToolAvailabilityPolicy,
    ToolConfirmationPolicy,
    ToolEnvironmentPolicy,
    ToolEvidenceRole,
    ToolExecutableResolution,
    ToolExecutableResolutionKind,
    ToolInputContract,
    ToolMutability,
    ToolNetworkPolicy,
    ToolOutputLimits,
    ToolPathPolicy,
    ToolPlatform,
    ToolVersionPolicy,
    ToolWorkingDirectoryPolicy,
)
from gf_wordbench.diagnostics.tools.registry import (
    CATALOG_VERSION,
    DEFAULT_TOOL_REGISTRY,
    CatalogVersionMismatchError,
    DiagnosticToolRegistry,
    DuplicateDiagnosticToolError,
    UnknownDiagnosticToolError,
    build_tool_registry,
    get_registered_tool,
    is_registered_tool,
    normalize_tool_id,
    registered_tool_ids,
    require_registered_tool,
)


def _tool_spec(
    tool_id: str,
    *,
    availability: ToolAvailabilityPolicy = ToolAvailabilityPolicy.OPTIONAL,
    mutability: ToolMutability = ToolMutability.READ_ONLY,
    confirmation: ToolConfirmationPolicy = ToolConfirmationPolicy.NONE,
    normative: bool = False,
    ai_assisted: bool = False,
    platforms: tuple[ToolPlatform, ...] = (
        ToolPlatform.WINDOWS,
        ToolPlatform.LINUX,
    ),
) -> DiagnosticToolSpec:
    return DiagnosticToolSpec(
        tool_id=tool_id,
        catalog_version=CATALOG_VERSION,
        tool_version_policy=ToolVersionPolicy(
            minimum_version="1.0",
            tested_versions=("1.0", "1.1"),
            version_probe=("--version",),
        ),
        description=f"Diagnostic tool {tool_id}",
        purpose="Produce bounded diagnostic evidence.",
        executable_resolution=ToolExecutableResolution(
            kind=ToolExecutableResolutionKind.APPROVED_PATH_LOOKUP,
            executable_name=tool_id,
            approved_path_names=(tool_id, f"{tool_id}.exe"),
        ),
        input_contract=ToolInputContract(
            subject_kinds=("source_file",),
            file_types=(".gf",),
        ),
        allowed_flags=(),
        working_directory_policy=ToolWorkingDirectoryPolicy.RUN_DIRECTORY,
        environment_policy=ToolEnvironmentPolicy(
            policy_id="diagnostic-default",
            inherited_variables=("PATH",),
        ),
        mutability=mutability,
        confirmation_policy=confirmation,
        allowed_paths=ToolPathPolicy(
            readable_path_classes=("active_project", "run_directory"),
            writable_path_classes=("run_directory",),
        ),
        network_policy=ToolNetworkPolicy.DENIED,
        timeout_sec=30.0,
        output_limits=ToolOutputLimits(
            stdout_bytes=64 * 1024,
            stderr_bytes=64 * 1024,
            generated_files_bytes=256 * 1024,
            total_retained_bytes=512 * 1024,
        ),
        evidence_roles=(
            ToolEvidenceRole.TOOL_STDOUT,
            ToolEvidenceRole.TOOL_STDERR,
            *((ToolEvidenceRole.AI_ANNOTATION,) if ai_assisted else ()),
        ),
        normalization_profile="diagnostic-text-v1",
        parser_id="diagnostic-parser-v1",
        ai_assisted=ai_assisted,
        normative=normative,
        availability_policy=availability,
        platforms=platforms,
    )


@pytest.mark.parametrize(
    "tool_id",
    (
        "gf-lint",
        "graph-check-2",
        "x",
    ),
)
def test_normalize_tool_id_accepts_only_canonical_identity(
    tool_id: str,
) -> None:
    assert normalize_tool_id(tool_id) == tool_id


@pytest.mark.parametrize(
    "tool_id",
    (
        "",
        " ",
        "GF-Lint",
        "gf_lint",
        "gf lint",
        "-gf-lint",
        "gf-lint-",
        "gf--lint",
        "évidence",
    ),
)
def test_normalize_tool_id_rejects_noncanonical_identity(
    tool_id: str,
) -> None:
    with pytest.raises(ValueError):
        normalize_tool_id(tool_id)


def test_registry_sorts_entries_and_exposes_immutable_lookup() -> None:
    alpha = _tool_spec("alpha-check")
    zeta = _tool_spec("zeta-check")

    registry = build_tool_registry((zeta, alpha))

    assert registry.catalog_version == CATALOG_VERSION
    assert registry.specs == (alpha, zeta)
    assert registry.tool_ids == ("alpha-check", "zeta-check")
    assert tuple(registry) == registry.specs
    assert len(registry) == 2
    assert bool(registry)
    assert "alpha-check" in registry
    assert "ALPHA-CHECK" not in registry
    assert registry.get("alpha-check") is alpha
    assert registry.require("zeta-check") is zeta

    with pytest.raises(TypeError):
        registry.mapping["other"] = alpha  # type: ignore[index]


def test_registry_rejects_duplicate_ids_and_catalog_mismatch() -> None:
    first = _tool_spec("syntax-check")
    duplicate = replace(first, description="Duplicate entry")

    with pytest.raises(DuplicateDiagnosticToolError):
        DiagnosticToolRegistry((first, duplicate))

    mismatched = replace(first, catalog_version="2.0")
    with pytest.raises(CatalogVersionMismatchError):
        DiagnosticToolRegistry((mismatched,))


def test_registry_filters_specs_and_builds_complete_snapshot() -> None:
    required = _tool_spec(
        "required-check",
        availability=ToolAvailabilityPolicy.REQUIRED,
        normative=True,
        platforms=(ToolPlatform.WINDOWS,),
    )
    optional = _tool_spec(
        "optional-check",
        availability=ToolAvailabilityPolicy.OPTIONAL,
        platforms=(ToolPlatform.LINUX,),
    )
    diagnostic_only = _tool_spec(
        "ai-review",
        availability=ToolAvailabilityPolicy.DIAGNOSTIC_ONLY,
        ai_assisted=True,
        platforms=(ToolPlatform.WINDOWS, ToolPlatform.LINUX),
    )
    registry = DiagnosticToolRegistry(
        (diagnostic_only, optional, required)
    )

    assert registry.by_availability("required") == (required,)
    assert registry.by_availability(
        ToolAvailabilityPolicy.OPTIONAL
    ) == (optional,)
    assert registry.by_availability("diagnostic_only") == (
        diagnostic_only,
    )
    assert registry.by_mutability(ToolMutability.READ_ONLY) == (
        diagnostic_only,
        optional,
        required,
    )
    assert registry.normative() == (required,)
    assert registry.ai_assisted() == (diagnostic_only,)
    assert registry.read_only() == registry.specs
    assert registry.for_platform("windows") == (
        diagnostic_only,
        required,
    )
    assert registry.for_platform(ToolPlatform.LINUX) == (
        diagnostic_only,
        optional,
    )

    snapshot = registry.snapshot()
    assert snapshot.catalog_version == CATALOG_VERSION
    assert snapshot.tool_ids == (
        "ai-review",
        "optional-check",
        "required-check",
    )
    assert snapshot.required_tool_ids == ("required-check",)
    assert snapshot.optional_tool_ids == ("optional-check",)
    assert snapshot.diagnostic_only_tool_ids == ("ai-review",)
    assert snapshot.normative_tool_ids == ("required-check",)
    assert snapshot.ai_assisted_tool_ids == ("ai-review",)


def test_selection_is_deterministic_and_rejects_unknown_tools() -> None:
    alpha = _tool_spec("alpha-check")
    beta = _tool_spec("beta-check")
    registry = DiagnosticToolRegistry((beta, alpha))

    assert registry.select(("beta-check", "alpha-check")) == (
        alpha,
        beta,
    )

    with pytest.raises(UnknownDiagnosticToolError):
        registry.require("missing-check")
    with pytest.raises(UnknownDiagnosticToolError):
        registry.select(("alpha-check", "missing-check"))
    with pytest.raises(ValueError):
        registry.select(("alpha-check", "alpha-check"))


def test_public_helpers_use_the_selected_registry_without_global_mutation() -> None:
    spec = _tool_spec("source-check")
    registry = DiagnosticToolRegistry((spec,))

    assert is_registered_tool("source-check", registry=registry)
    assert not is_registered_tool("missing-check", registry=registry)
    assert get_registered_tool("source-check", registry=registry) is spec
    assert get_registered_tool("missing-check", registry=registry) is None
    assert require_registered_tool("source-check", registry=registry) is spec
    assert registered_tool_ids(registry=registry) == ("source-check",)

    with pytest.raises(UnknownDiagnosticToolError):
        require_registered_tool("missing-check", registry=registry)

    assert len(DEFAULT_TOOL_REGISTRY) == 0
    assert registered_tool_ids() == ()


def test_registry_preserves_reviewed_mutation_and_confirmation_policy() -> None:
    mutating = _tool_spec(
        "project-rewriter",
        mutability=ToolMutability.PROJECT_MUTATING,
        confirmation=ToolConfirmationPolicy.EXPLICIT_USER_CONFIRMATION,
        availability=ToolAvailabilityPolicy.DIAGNOSTIC_ONLY,
    )
    registry = DiagnosticToolRegistry((mutating,))

    selected = registry.require("project-rewriter")
    assert selected.is_mutating
    assert not selected.is_executable_in_normal_validation
    assert selected.confirmation_policy is (
        ToolConfirmationPolicy.EXPLICIT_USER_CONFIRMATION
    )
    assert registry.read_only() == ()
