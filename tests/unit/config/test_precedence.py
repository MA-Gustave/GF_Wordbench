from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from gf_wordbench.config.models import (
    AppConfig,
    ConfigurationResolutionRequest,
    EnvironmentOverrides,
    OutputDefaults,
    SchemaSupport,
    SelectionDefaults,
    ValidationTarget,
)
from gf_wordbench.config.precedence import (
    PRECEDENCE_POLICIES,
    ConfigurationDomain,
    ConfigurationSource,
    PrecedencePolicy,
    policy_for,
    resolve_precedence,
)
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import (
    GFProjectConfig,
    ModuleTargets,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)

pytestmark = pytest.mark.unit

_DEFAULT_TIMEOUT: Final[int] = 60


def _defaults() -> AppConfig:
    return AppConfig(
        producer=ProducerInfo(
            name="gf-wordbench",
            version="1.0.0",
        ),
        selection_defaults=SelectionDefaults(
            mode=ValidationMode.CHECKPOINT,
            timeout_sec=_DEFAULT_TIMEOUT,
            max_files=0,
            keep_ok_details=False,
            diff_previous=True,
            skip_version_probe=False,
            no_compile=False,
            emit_cpu_stats=False,
        ),
        output_defaults=OutputDefaults(
            evidence_level="standard",
            generate_manifest=True,
            generate_ai_ready=True,
            aggregate_logs=True,
        ),
        schema_support=SchemaSupport(
            project_major=1,
            app_state_major=1,
            run_summary_major=1,
            artifact_manifest_major=1,
        ),
        state_filename=".gf_wordbench_state.json",
    )


def _project(tmp_path: Path) -> ProjectConfig:
    project_root = (tmp_path / "project").resolve()
    source_directory = Path("lib/src/example")
    return ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id="example",
            name="Example Language",
            language_code="ex",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=source_directory,
            glob="*.gf",
            include_regex=r".*\.gf$",
            exclude_regex=r"(?:^|/)attic(?:/|$)",
        ),
        gf=GFProjectConfig(
            path_parts=("lib/src/example", "lib/src/common"),
            minimum_version="3.11",
        ),
        modules=ModuleTargets(
            entrypoints=(Path("GrammarEx.gf"),),
            checkpoints=(Path("MorphologyEx.gf"),),
        ),
        validation=ValidationPolicy(
            required_scenarios=("smoke",),
            optional_scenarios=("regression",),
            release_requires_pgf=True,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=project_root / source_directory,
    )


def _request(
    tmp_path: Path,
    *,
    environment: EnvironmentOverrides | None = None,
    candidates: dict[
        ConfigurationSource,
        dict[str, object],
    ]
    | None = None,
) -> ConfigurationResolutionRequest:
    return ConfigurationResolutionRequest(
        defaults=_defaults(),
        project=_project(tmp_path),
        environment=environment or EnvironmentOverrides(),
        candidates_by_source=candidates or {},
    )


def _provenance(
    result: object,
) -> dict[str, ConfigurationSource]:
    records = getattr(result, "provenance")
    return {
        record.field_path: record.source
        for record in records
    }


def test_policy_registry_is_read_only_and_complete() -> None:
    assert isinstance(PRECEDENCE_POLICIES, MappingProxyType)
    assert set(PRECEDENCE_POLICIES) == set(ConfigurationDomain)

    with pytest.raises(TypeError):
        PRECEDENCE_POLICIES[ConfigurationDomain.MODE] = policy_for(  # type: ignore[index]
            ConfigurationDomain.MODE
        )


def test_canonical_policy_tiers_are_exact() -> None:
    explicit = (
        ConfigurationSource.CLI,
        ConfigurationSource.GUI,
        ConfigurationSource.AUTOMATION,
    )
    startup = (
        ConfigurationSource.STARTUP_OPTION,
        *explicit,
    )

    expected = {
        ConfigurationDomain.PROJECT_ROOT: (
            startup,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
        ConfigurationDomain.GF_EXECUTABLE: (
            explicit,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.PATH_DISCOVERY,),
        ),
        ConfigurationDomain.RGL_ROOT: (
            explicit,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.PATH_DISCOVERY,),
        ),
        ConfigurationDomain.OUTPUT_ROOT: (
            explicit,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
        ConfigurationDomain.STATE_PATH: (
            startup,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
        ConfigurationDomain.PROJECT_FIELD: (
            (ConfigurationSource.PROJECT_TOML,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
        ConfigurationDomain.MODE: (
            explicit,
            (ConfigurationSource.PROJECT_TOML,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
        ConfigurationDomain.TARGET: (
            explicit,
            (ConfigurationSource.PROJECT_TOML,),
            (ConfigurationSource.RUNTIME_DERIVED,),
        ),
        ConfigurationDomain.TIMEOUT: (
            explicit,
            (ConfigurationSource.PROJECT_TOML,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
        ConfigurationDomain.RUN_OPTION: (
            explicit,
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
    }

    for domain, tiers in expected.items():
        policy = policy_for(domain)
        assert policy.domain is domain
        assert policy.tiers == tiers


def test_policy_rank_equivalence_and_authorization() -> None:
    policy = policy_for(ConfigurationDomain.MODE)

    assert policy.rank(ConfigurationSource.CLI) == 0
    assert policy.rank(ConfigurationSource.PROJECT_TOML) == 1
    assert policy.outranks(
        ConfigurationSource.CLI,
        ConfigurationSource.PROJECT_TOML,
    )
    assert policy.equivalent(
        ConfigurationSource.CLI,
        ConfigurationSource.GUI,
    )
    assert not policy.allows(ConfigurationSource.APPLICATION_STATE)

    with pytest.raises(ValueError, match="not authorized"):
        policy.rank(ConfigurationSource.APPLICATION_STATE)


def test_policy_rejects_empty_tiers_and_duplicate_sources() -> None:
    with pytest.raises(ValueError, match="non-empty tiers"):
        PrecedencePolicy(
            domain=ConfigurationDomain.MODE,
            tiers=(),
        )

    with pytest.raises(ValueError, match="only once"):
        PrecedencePolicy(
            domain=ConfigurationDomain.MODE,
            tiers=(
                (ConfigurationSource.CLI,),
                (ConfigurationSource.CLI,),
            ),
        )


def test_explicit_values_outrank_project_environment_state_and_defaults(
    tmp_path: Path,
) -> None:
    cli_target = ValidationTarget(
        kind=TargetKind.ENTRYPOINT,
        value="GrammarEx.gf",
    )
    result = resolve_precedence(
        _request(
            tmp_path,
            environment=EnvironmentOverrides(
                project_root="environment-project",
                output_root="environment-output",
            ),
            candidates={
                ConfigurationSource.APPLICATION_STATE: {
                    "project_root": "state-project",
                    "output_root": "state-output",
                    "max_files": 5,
                },
                ConfigurationSource.PROJECT_TOML: {
                    "mode": ValidationMode.RELEASE,
                    "timeout_sec": 90,
                    "target": ValidationTarget(
                        kind=TargetKind.PROJECT,
                        value=None,
                    ),
                },
                ConfigurationSource.CLI: {
                    "project_root": "cli-project",
                    "output_root": "cli-output",
                    "mode": ValidationMode.DIAGNOSTIC,
                    "timeout_sec": 15,
                    "target": cli_target,
                    "max_files": 12,
                },
            },
        )
    )

    assert result.issues == ()
    assert result.values is not None
    assert result.values.project_root == "cli-project"
    assert result.values.output_root == "cli-output"
    assert result.values.mode is ValidationMode.DIAGNOSTIC
    assert result.values.timeout_sec == 15
    assert result.values.target == cli_target
    assert result.values.max_files == 12

    provenance = _provenance(result)
    assert provenance["project_root"] is ConfigurationSource.CLI
    assert provenance["output_root"] is ConfigurationSource.CLI
    assert provenance["mode"] is ConfigurationSource.CLI
    assert provenance["timeout_sec"] is ConfigurationSource.CLI
    assert provenance["target"] is ConfigurationSource.CLI
    assert provenance["max_files"] is ConfigurationSource.CLI


def test_application_state_outranks_framework_defaults_for_run_options(
    tmp_path: Path,
) -> None:
    result = resolve_precedence(
        _request(
            tmp_path,
            candidates={
                ConfigurationSource.APPLICATION_STATE: {
                    "max_files": 7,
                    "keep_ok_details": True,
                    "diff_previous": False,
                    "evidence_level": "complete",
                }
            },
        )
    )

    assert result.issues == ()
    assert result.values is not None
    assert result.values.max_files == 7
    assert result.values.keep_ok_details is True
    assert result.values.diff_previous is False
    assert result.values.evidence_level == "complete"

    provenance = _provenance(result)
    assert provenance["max_files"] is ConfigurationSource.APPLICATION_STATE
    assert (
        provenance["keep_ok_details"]
        is ConfigurationSource.APPLICATION_STATE
    )
    assert (
        provenance["diff_previous"]
        is ConfigurationSource.APPLICATION_STATE
    )
    assert (
        provenance["evidence_level"]
        is ConfigurationSource.APPLICATION_STATE
    )


def test_equal_tier_equal_values_are_accepted_deterministically(
    tmp_path: Path,
) -> None:
    result = resolve_precedence(
        _request(
            tmp_path,
            candidates={
                ConfigurationSource.CLI: {
                    "timeout_sec": 25,
                },
                ConfigurationSource.GUI: {
                    "timeout_sec": 25,
                },
            },
        )
    )

    assert result.issues == ()
    assert result.values is not None
    assert result.values.timeout_sec == 25
    assert (
        _provenance(result)["timeout_sec"]
        is ConfigurationSource.CLI
    )


def test_equal_tier_conflicts_fail_closed(tmp_path: Path) -> None:
    result = resolve_precedence(
        _request(
            tmp_path,
            candidates={
                ConfigurationSource.CLI: {
                    "mode": ValidationMode.QUICK,
                },
                ConfigurationSource.GUI: {
                    "mode": ValidationMode.RELEASE,
                },
            },
        )
    )

    assert result.values is None
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.source is ConfigurationSource.RUNTIME_DERIVED
    assert issue.field_path == "mode"
    assert "Equivalent sources supplied conflicting values" in issue.message


def test_invalid_authoritative_value_does_not_fall_back_to_default(
    tmp_path: Path,
) -> None:
    result = resolve_precedence(
        _request(
            tmp_path,
            candidates={
                ConfigurationSource.CLI: {
                    "timeout_sec": 0,
                }
            },
        )
    )

    assert result.values is None
    assert any(
        issue.field_path == "timeout_sec"
        and issue.source is ConfigurationSource.CLI
        and "greater than or equal to 1" in issue.message
        for issue in result.issues
    )


def test_unauthorized_source_is_reported_even_when_a_default_exists(
    tmp_path: Path,
) -> None:
    result = resolve_precedence(
        _request(
            tmp_path,
            candidates={
                ConfigurationSource.PATH_DISCOVERY: {
                    "timeout_sec": 30,
                }
            },
        )
    )

    assert result.values is None
    assert any(
        issue.field_path == "timeout_sec"
        and issue.source is ConfigurationSource.PATH_DISCOVERY
        and "not authorized" in issue.message
        for issue in result.issues
    )


def test_unknown_precedence_field_is_a_structured_error(
    tmp_path: Path,
) -> None:
    result = resolve_precedence(
        _request(
            tmp_path,
            candidates={
                ConfigurationSource.CLI: {
                    "not_a_configuration_field": "value",
                }
            },
        )
    )

    assert result.values is None
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.source is ConfigurationSource.CLI
    assert issue.field_path == "not_a_configuration_field"
    assert "Unknown precedence-controlled field" in issue.message


def test_environment_values_outrank_state_but_not_explicit_values(
    tmp_path: Path,
) -> None:
    environment_result = resolve_precedence(
        _request(
            tmp_path,
            environment=EnvironmentOverrides(
                gf_executable="environment-gf",
                rgl_root="environment-rgl",
                output_root="environment-output",
            ),
            candidates={
                ConfigurationSource.APPLICATION_STATE: {
                    "gf_executable": "state-gf",
                    "rgl_root": "state-rgl",
                    "output_root": "state-output",
                }
            },
        )
    )

    assert environment_result.issues == ()
    assert environment_result.values is not None
    assert environment_result.values.gf_executable == "environment-gf"
    assert environment_result.values.rgl_root == "environment-rgl"
    assert environment_result.values.output_root == "environment-output"

    explicit_result = resolve_precedence(
        _request(
            tmp_path,
            environment=EnvironmentOverrides(
                gf_executable="environment-gf",
            ),
            candidates={
                ConfigurationSource.AUTOMATION: {
                    "gf_executable": "automation-gf",
                }
            },
        )
    )

    assert explicit_result.issues == ()
    assert explicit_result.values is not None
    assert explicit_result.values.gf_executable == "automation-gf"


def test_project_owned_selection_is_copied_without_surface_override(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    result = resolve_precedence(
        ConfigurationResolutionRequest(
            defaults=_defaults(),
            project=project,
        )
    )

    assert result.issues == ()
    assert result.values is not None
    assert result.values.selected_entrypoints == project.modules.entrypoints
    assert result.values.selected_checkpoints == project.modules.checkpoints
    assert result.values.selected_scenarios == project.validation.all_scenarios
    assert (
        result.values.release_requires_pgf
        is project.validation.release_requires_pgf
    )

    provenance = _provenance(result)
    for field_path in (
        "selected_entrypoints",
        "selected_checkpoints",
        "selected_scenarios",
        "release_requires_pgf",
    ):
        assert (
            provenance[field_path]
            is ConfigurationSource.PROJECT_TOML
        )


def test_candidate_mappings_are_frozen_on_request_creation(
    tmp_path: Path,
) -> None:
    raw = {
        ConfigurationSource.CLI: {
            "timeout_sec": 10,
        }
    }
    request = _request(tmp_path, candidates=raw)

    raw[ConfigurationSource.CLI]["timeout_sec"] = 99

    assert request.candidates_by_source[ConfigurationSource.CLI][
        "timeout_sec"
    ] == 10

    with pytest.raises(TypeError):
        request.candidates_by_source[ConfigurationSource.CLI][  # type: ignore[index]
            "timeout_sec"
        ] = 20


def test_resolver_rejects_non_request_inputs() -> None:
    with pytest.raises(
        TypeError,
        match="ConfigurationResolutionRequest",
    ):
        resolve_precedence(object())  # type: ignore[arg-type]
