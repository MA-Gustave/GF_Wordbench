from __future__ import annotations

from pathlib import Path

import pytest

from gf_wordbench.config import resolver as resolver_module
from gf_wordbench.config.models import (
    AppConfig,
    ConfigurationIssue,
    ConfigurationProvenance,
    ConfigurationResolutionRequest,
    EnvironmentResolution,
    IssueSeverity,
    OutputDefaults,
    ResolvedEnvironment,
    SchemaSupport,
    SelectionDefaults,
    ValidationTarget,
)
from gf_wordbench.config.precedence import (
    ConfigurationSource,
    PrecedenceResolution,
    PrecedenceValues,
)
from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import (
    TargetKind,
    ValidationMode,
)
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


def _defaults() -> AppConfig:
    return AppConfig(
        producer=ProducerInfo(
            name="gf-wordbench",
            version="1.0.0",
        ),
        selection_defaults=SelectionDefaults(
            mode=ValidationMode.CHECKPOINT,
            timeout_sec=60,
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
    source_root = project_root / "src"

    return ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id="example-language",
            name="Example Language",
            language_code="ex",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("src"),
            glob="**/*.gf",
            include_regex="",
            exclude_regex="",
        ),
        gf=GFProjectConfig(
            path_parts=("src",),
            minimum_version="",
        ),
        modules=ModuleTargets(
            entrypoints=(Path("Main.gf"),),
            checkpoints=(
                Path("Syntax.gf"),
                Path("Morphology.gf"),
            ),
        ),
        validation=ValidationPolicy(
            required_scenarios=("smoke",),
            optional_scenarios=("regression",),
            release_requires_pgf=True,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=source_root,
    )


def _environment(tmp_path: Path) -> ResolvedEnvironment:
    project_root = (tmp_path / "project").resolve()
    rgl_root = (tmp_path / "rgl").resolve()
    output_root = (tmp_path / "runs").resolve()
    executable = (tmp_path / "bin" / "gf").resolve()

    return ResolvedEnvironment(
        project_root=project_root,
        rgl_root=rgl_root,
        gf_executable=executable,
        output_root=output_root,
        gf_path=(
            project_root / "src",
            rgl_root,
        ),
    )


def _precedence_values(
    tmp_path: Path,
    *,
    mode: ValidationMode = ValidationMode.DIAGNOSTIC,
) -> PrecedenceValues:
    return PrecedenceValues(
        project_root=(tmp_path / "project").resolve(),
        gf_executable=(tmp_path / "bin" / "gf").resolve(),
        rgl_root=(tmp_path / "rgl").resolve(),
        output_root=(tmp_path / "runs").resolve(),
        state_path=(tmp_path / ".gf_wordbench_state.json").resolve(),
        mode=mode,
        target=ValidationTarget(
            kind=TargetKind.PROJECT,
            value=None,
        ),
        timeout_sec=45,
        max_files=25,
        keep_ok_details=True,
        diff_previous=False,
        skip_version_probe=True,
        no_compile=False,
        emit_cpu_stats=True,
        evidence_level="expanded",
        selected_checkpoints=(),
        selected_entrypoints=(),
        selected_scenarios=(),
        release_requires_pgf=False,
    )


def _provenance(
    field_path: str,
    source: ConfigurationSource,
    value: object,
) -> ConfigurationProvenance:
    return ConfigurationProvenance(
        field_path=field_path,
        source=source,
        provided_value=value,
        resolved_value=value,
    )


def _issue(
    *,
    severity: IssueSeverity,
    field_path: str,
    source: ConfigurationSource,
    message: str,
) -> ConfigurationIssue:
    return ConfigurationIssue(
        severity=severity,
        source=source,
        field_path=field_path,
        provided_value=None,
        message=message,
        remediation="Correct the source value.",
    )


def test_resolve_configuration_requires_typed_request() -> None:
    with pytest.raises(
        TypeError,
        match="ConfigurationResolutionRequest",
    ):
        resolver_module.resolve_configuration(object())  # type: ignore[arg-type]


def test_resolver_composes_precedence_environment_and_project_owners(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    request = ConfigurationResolutionRequest(
        defaults=_defaults(),
        project=project,
    )
    warning = _issue(
        severity=IssueSeverity.WARNING,
        field_path="compatibility.legacy_mode",
        source=ConfigurationSource.LEGACY_MIGRATION,
        message="Legacy mode alias was migrated.",
    )

    monkeypatch.setattr(
        resolver_module,
        "resolve_precedence",
        lambda supplied: PrecedenceResolution(
            values=_precedence_values(tmp_path),
            issues=(warning,),
            provenance=(
                _provenance(
                    "mode",
                    ConfigurationSource.CLI,
                    ValidationMode.DIAGNOSTIC,
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        resolver_module,
        "resolve_environment",
        lambda supplied: EnvironmentResolution(
            value=_environment(tmp_path),
            provenance=(
                _provenance(
                    "environment.gf_executable",
                    ConfigurationSource.PATH_DISCOVERY,
                    (tmp_path / "bin" / "gf").resolve(),
                ),
            ),
        ),
    )

    resolution = resolver_module.resolve_configuration(request)

    assert resolution.succeeded is True
    configuration = resolution.require()
    assert configuration.project is project
    assert configuration.environment == _environment(tmp_path)
    assert configuration.mode is ValidationMode.DIAGNOSTIC
    assert configuration.timeout_sec == 45
    assert configuration.max_files == 25
    assert configuration.keep_ok_details is True
    assert configuration.diff_previous is False
    assert configuration.skip_version_probe is True
    assert configuration.emit_cpu_stats is True
    assert configuration.evidence_level == "expanded"
    assert configuration.selected_checkpoints == (
        project.source_root / "Syntax.gf",
        project.source_root / "Morphology.gf",
    )
    assert configuration.selected_entrypoints == (
        project.source_root / "Main.gf",
    )
    assert configuration.selected_scenarios == (
        "smoke",
        "regression",
    )
    assert configuration.release_requires_pgf is True
    assert configuration.compatibility_warnings == (
        "Legacy mode alias was migrated.",
    )

    provenance = {
        record.field_path: record.source
        for record in resolution.provenance
    }
    assert provenance["mode"] is ConfigurationSource.CLI
    assert (
        provenance["environment.gf_executable"]
        is ConfigurationSource.PATH_DISCOVERY
    )
    for field_path in (
        "project",
        "release_requires_pgf",
        "selected_checkpoints",
        "selected_entrypoints",
        "selected_scenarios",
    ):
        assert provenance[field_path] is ConfigurationSource.PROJECT_TOML


def test_resolver_does_not_construct_run_config_when_an_owner_reports_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = ConfigurationResolutionRequest(
        defaults=_defaults(),
        project=_project(tmp_path),
    )
    error = _issue(
        severity=IssueSeverity.ERROR,
        field_path="environment.gf_executable",
        source=ConfigurationSource.PATH_DISCOVERY,
        message="GF executable was not found.",
    )
    warning = _issue(
        severity=IssueSeverity.WARNING,
        field_path="mode",
        source=ConfigurationSource.LEGACY_MIGRATION,
        message="Legacy mode alias was migrated.",
    )

    monkeypatch.setattr(
        resolver_module,
        "resolve_precedence",
        lambda supplied: PrecedenceResolution(
            values=_precedence_values(tmp_path),
            issues=(warning,),
            provenance=(
                _provenance(
                    "mode",
                    ConfigurationSource.CLI,
                    ValidationMode.DIAGNOSTIC,
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        resolver_module,
        "resolve_environment",
        lambda supplied: EnvironmentResolution(
            value=None,
            issues=(error,),
            provenance=(
                _provenance(
                    "environment.gf_executable",
                    ConfigurationSource.PATH_DISCOVERY,
                    None,
                ),
            ),
        ),
    )

    resolution = resolver_module.resolve_configuration(request)

    assert resolution.succeeded is False
    assert resolution.configuration is None
    assert resolution.issues == (error, warning)
    assert tuple(
        record.field_path for record in resolution.provenance
    ) == (
        "environment.gf_executable",
        "mode",
    )


def test_resolver_reports_conflicting_provenance_as_composition_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = ConfigurationResolutionRequest(
        defaults=_defaults(),
        project=_project(tmp_path),
    )

    monkeypatch.setattr(
        resolver_module,
        "resolve_precedence",
        lambda supplied: PrecedenceResolution(
            values=_precedence_values(tmp_path),
            provenance=(
                _provenance(
                    "output_root",
                    ConfigurationSource.CLI,
                    (tmp_path / "runs").resolve(),
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        resolver_module,
        "resolve_environment",
        lambda supplied: EnvironmentResolution(
            value=_environment(tmp_path),
            provenance=(
                _provenance(
                    "output_root",
                    ConfigurationSource.ENVIRONMENT_VARIABLE,
                    (tmp_path / "other-runs").resolve(),
                ),
            ),
        ),
    )

    resolution = resolver_module.resolve_configuration(request)

    assert resolution.configuration is None
    assert resolution.provenance == ()
    assert len(resolution.issues) == 1
    issue = resolution.issues[0]
    assert issue.severity is IssueSeverity.ERROR
    assert issue.source is ConfigurationSource.RUNTIME_DERIVED
    assert issue.field_path == "configuration"
    assert "conflicting provenance" in issue.message


def test_resolver_converts_invalid_run_config_into_structured_issue(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = ConfigurationResolutionRequest(
        defaults=_defaults(),
        project=_project(tmp_path),
    )
    values = _precedence_values(
        tmp_path,
        mode=ValidationMode.QUICK,
    )
    values = PrecedenceValues(
        **{
            field: getattr(values, field)
            for field in values.__dataclass_fields__
            if field != "target"
        },
        target=None,
    )

    monkeypatch.setattr(
        resolver_module,
        "resolve_precedence",
        lambda supplied: PrecedenceResolution(values=values),
    )
    monkeypatch.setattr(
        resolver_module,
        "resolve_environment",
        lambda supplied: EnvironmentResolution(
            value=_environment(tmp_path),
        ),
    )

    resolution = resolver_module.resolve_configuration(request)

    assert resolution.configuration is None
    assert len(resolution.issues) == 1
    issue = resolution.issues[0]
    assert issue.severity is IssueSeverity.ERROR
    assert issue.field_path == "configuration"
    assert "quick mode requires a resolved target" in issue.message


def test_require_configuration_raises_canonical_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = ConfigurationResolutionRequest(
        defaults=_defaults(),
        project=_project(tmp_path),
    )
    issue = _issue(
        severity=IssueSeverity.ERROR,
        field_path="mode",
        source=ConfigurationSource.CLI,
        message="Mode is invalid.",
    )

    monkeypatch.setattr(
        resolver_module,
        "resolve_precedence",
        lambda supplied: PrecedenceResolution(
            values=None,
            issues=(issue,),
        ),
    )
    monkeypatch.setattr(
        resolver_module,
        "resolve_environment",
        lambda supplied: EnvironmentResolution(
            value=_environment(tmp_path),
        ),
    )

    with pytest.raises(
        ConfigurationError,
        match="mode.*Mode is invalid",
    ):
        resolver_module.require_configuration(request)
