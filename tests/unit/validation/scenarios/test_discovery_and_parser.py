"""Unit tests for scenario discovery and native ``.gfs`` preflight parsing."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from gf_wordbench.config.models import ResolvedEnvironment, RunConfig
from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.kernel.ids import (
    ScenarioId,
    validate_project_id,
    validate_scenario_id,
)
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.models import (
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.validation.scenarios.discovery import discover_scenarios
from gf_wordbench.validation.scenarios.models import (
    ScenarioComparisonPolicy,
    ScenarioSpec,
)
from gf_wordbench.validation.scenarios.parser import (
    ScenarioMarkerPhase,
    ScenarioParserPolicy,
    ScenarioScriptIssueCode,
    ScenarioScriptLineKind,
    ParsedScenarioScript,
    ScenarioScriptParseError,
    parse_scenario_bytes,
    parse_scenario_file,
    parse_scenario_text,
    validate_scenario_text,
)


def _project(
    tmp_path: Path,
    *,
    required: tuple[str, ...] = (),
    optional: tuple[str, ...] = (),
) -> ProjectConfig:
    project_root = (tmp_path / "project").resolve()
    source_root = project_root / "src"
    scenarios_root = project_root / "validation" / "scenarios"

    source_root.mkdir(parents=True)
    scenarios_root.mkdir(parents=True)
    (project_root / "project.toml").write_text(
        "# scenario discovery fixture\n",
        encoding="utf-8",
    )

    return ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id=validate_project_id("scenario-test-project"),
            name="Scenario test project",
            language_code="en",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("src"),
            glob="**/*.gf",
            include_regex=r".*\.gf$",
            exclude_regex=r"\A\Z",
        ),
        gf=GFProjectConfig(
            path_parts=(),
            minimum_version="",
        ),
        modules=ModuleTargets(
            entrypoints=(),
            checkpoints=(),
        ),
        validation=ValidationPolicy(
            required_scenarios=tuple(validate_scenario_id(value) for value in required),
            optional_scenarios=tuple(validate_scenario_id(value) for value in optional),
            release_requires_pgf=False,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=source_root,
    )


def _run_config(
    tmp_path: Path,
    *,
    required: tuple[str, ...] = (),
    optional: tuple[str, ...] = (),
    selected: tuple[str, ...] = (),
    mode: ValidationMode = ValidationMode.DIAGNOSTIC,
) -> RunConfig:
    project = _project(
        tmp_path,
        required=required,
        optional=optional,
    )
    environment_root = (tmp_path / "environment").resolve()
    rgl_root = environment_root / "rgl"
    output_root = environment_root / "runs"
    gf_executable = environment_root / "bin" / "gf"

    rgl_root.mkdir(parents=True)
    output_root.mkdir(parents=True)
    gf_executable.parent.mkdir(parents=True)
    gf_executable.write_text("test executable placeholder\n", encoding="utf-8")

    return RunConfig(
        project=project,
        environment=ResolvedEnvironment(
            project_root=project.project_root,
            rgl_root=rgl_root,
            gf_executable=gf_executable,
            output_root=output_root,
            gf_path=(project.source_root, rgl_root),
        ),
        mode=mode,
        target=None,
        timeout_sec=30,
        max_files=0,
        keep_ok_details=False,
        diff_previous=False,
        skip_version_probe=False,
        no_compile=False,
        emit_cpu_stats=False,
        selected_checkpoints=(),
        selected_entrypoints=(),
        selected_scenarios=selected,
        release_requires_pgf=False,
        evidence_level="bounded",
    )


def _scenario_spec(
    run_config: RunConfig,
    scenario_id: str,
    *,
    required: bool,
    enabled_modes: tuple[ValidationMode, ...] = (ValidationMode.DIAGNOSTIC,),
    script_path: Path | None = None,
) -> ScenarioSpec:
    relative_script = script_path or Path(
        "validation",
        "scenarios",
        f"{scenario_id}.gfs",
    )
    project = run_config.project
    assert project is not None
    absolute_script = project.project_root / relative_script
    absolute_script.parent.mkdir(parents=True, exist_ok=True)
    absolute_script.write_text("q\n", encoding="utf-8")

    return ScenarioSpec(
        scenario_id=validate_scenario_id(scenario_id),
        script_path=relative_script,
        required=required,
        enabled_modes=enabled_modes,
        working_directory=project.project_root,
        timeout_sec=30.0,
        output_limit_bytes=1024 * 1024,
        gold_path=None,
        comparison_policy=ScenarioComparisonPolicy.NONE,
        normalization_version="1.0",
        expected_sections=(),
        expected_artifacts=(),
        input_paths=(),
    )


def _issue_codes(parsed: ParsedScenarioScript) -> tuple[ScenarioScriptIssueCode, ...]:
    issues = parsed.issues
    return tuple(issue.code for issue in issues)


def test_parser_preserves_evidence_line_kinds_and_ordered_markers() -> None:
    source_path = Path("validation/scenarios/smoke.gfs")
    text = (
        "-- reviewed smoke scenario\n"
        'ps "@@GF-WORDBENCH BEGIN smoke linearize@@"\n'
        "l Greeting\n"
        'ps "@@GF-WORDBENCH END smoke linearize@@"\n'
        "q\n"
    )

    parsed = parse_scenario_text(
        text,
        scenario_id="smoke",
        source_path=source_path,
    )

    assert parsed.valid
    assert parsed.issues == ()
    assert parsed.source_path == source_path
    assert parsed.sha256 == sha256(text.encode("utf-8")).hexdigest()
    assert parsed.size_bytes == len(text.encode("utf-8"))
    assert parsed.line_count == 5
    assert parsed.termination_line == 5
    assert tuple(line.kind for line in parsed.lines) == (
        ScenarioScriptLineKind.COMMENT,
        ScenarioScriptLineKind.COMMAND,
        ScenarioScriptLineKind.COMMAND,
        ScenarioScriptLineKind.COMMAND,
        ScenarioScriptLineKind.TERMINATION,
    )
    assert tuple(marker.phase for marker in parsed.markers) == (
        ScenarioMarkerPhase.BEGIN,
        ScenarioMarkerPhase.END,
    )
    assert tuple(str(value) for value in parsed.section_ids) == ("linearize",)
    assert tuple(str(value) for value in parsed.completed_sections) == ("linearize",)


def test_parser_reports_portability_security_and_post_termination_commands() -> None:
    parsed = parse_scenario_text(
        '! echo unsafe\ni /tmp/Grammar.gf\nps "$GF_LIB_PATH"\nq\nl TooLate\n',
        scenario_id="security-check",
    )

    assert not parsed.valid
    assert _issue_codes(parsed) == (
        ScenarioScriptIssueCode.PROHIBITED_SHELL_ESCAPE,
        ScenarioScriptIssueCode.MACHINE_LOCAL_ABSOLUTE_PATH,
        ScenarioScriptIssueCode.ENVIRONMENT_REFERENCE,
        ScenarioScriptIssueCode.COMMAND_AFTER_TERMINATION,
    )
    assert tuple((issue.line, issue.column) for issue in parsed.issues) == (
        (1, 1),
        (2, 3),
        (3, 5),
        (5, 1),
    )


def test_parser_rejects_wrong_nested_and_mismatched_markers() -> None:
    parsed = parse_scenario_text(
        'ps "@@GF-WORDBENCH BEGIN other first@@"\n'
        'ps "@@GF-WORDBENCH BEGIN marker-check second@@"\n'
        'ps "@@GF-WORDBENCH END marker-check second@@"\n'
        "q\n",
        scenario_id="marker-check",
    )

    codes = _issue_codes(parsed)
    assert ScenarioScriptIssueCode.WRONG_SCENARIO_MARKER in codes
    assert ScenarioScriptIssueCode.NESTED_BEGIN_MARKER in codes
    assert ScenarioScriptIssueCode.MISMATCHED_END_MARKER in codes
    assert ScenarioScriptIssueCode.OPEN_SECTION_AT_EOF in codes
    assert parsed.completed_sections == ()


def test_generation_requires_a_bound_when_timeout_is_not_the_bound() -> None:
    policy = ScenarioParserPolicy(timeout_is_generation_bound=False)

    unbounded = parse_scenario_text(
        "gr\nq\n",
        scenario_id="generation",
        policy=policy,
    )
    bounded = parse_scenario_text(
        "gr -number=3\nq\n",
        scenario_id="generation",
        policy=policy,
    )

    assert _issue_codes(unbounded) == (ScenarioScriptIssueCode.UNBOUNDED_GENERATION,)
    assert bounded.valid


def test_parser_records_invalid_utf8_without_decoding_partial_source() -> None:
    data = b"i Grammar.gf\n\xffq\n"

    parsed = parse_scenario_bytes(
        data,
        scenario_id="invalid-utf8",
        source_path=Path("invalid-utf8.gfs"),
    )

    assert parsed.sha256 == sha256(data).hexdigest()
    assert parsed.size_bytes == len(data)
    assert parsed.line_count == 0
    assert parsed.lines == ()
    assert parsed.markers == ()
    assert _issue_codes(parsed) == (ScenarioScriptIssueCode.INVALID_UTF8,)


def test_validate_raises_structured_error_for_invalid_script() -> None:
    with pytest.raises(ScenarioScriptParseError) as captured:
        validate_scenario_text(
            "i Grammar.gf\n",
            scenario_id="missing-termination",
            source_path=Path("missing-termination.gfs"),
        )

    error = captured.value
    assert error.code == "GF-WB-SCENARIO-006"
    assert error.stage == "scenario"
    assert error.operation == "parse_scenario_script"
    assert error.subject == "missing-termination.gfs"
    assert "missing_termination" in error.detail
    assert error.evidence_paths == ("missing-termination.gfs",)


def test_parse_file_requires_gfs_extension_before_reading(tmp_path: Path) -> None:
    path = tmp_path / "scenario.txt"
    path.write_text("q\n", encoding="utf-8")

    with pytest.raises(ScenarioScriptParseError) as captured:
        parse_scenario_file(path, scenario_id="wrong-extension")

    assert captured.value.code == "GF-WB-SCENARIO-007"
    assert captured.value.operation == "parse_scenario_file"


def test_discovery_selects_required_then_explicit_optional_in_registry_order(
    tmp_path: Path,
) -> None:
    run_config = _run_config(
        tmp_path,
        required=("required-one", "required-two"),
        optional=("optional-one", "optional-two"),
        selected=("optional-two", "optional-one"),
    )
    catalog = {
        scenario_id: _scenario_spec(
            run_config,
            scenario_id,
            required=scenario_id.startswith("required"),
        )
        for scenario_id in (
            "optional-two",
            "required-two",
            "optional-one",
            "required-one",
        )
    }

    selected = discover_scenarios(run_config, catalog)

    assert tuple(str(spec.scenario_id) for spec in selected) == (
        "required-one",
        "required-two",
        "optional-one",
        "optional-two",
    )


def test_discovery_rejects_unregistered_explicit_scenario(tmp_path: Path) -> None:
    run_config = _run_config(
        tmp_path,
        required=("required",),
        optional=("optional",),
        selected=("unknown",),
    )
    catalog = {
        "required": _scenario_spec(run_config, "required", required=True),
        "optional": _scenario_spec(run_config, "optional", required=False),
    }

    with pytest.raises(ConfigurationError) as captured:
        discover_scenarios(run_config, catalog)

    assert captured.value.code == "GF-WB-CONFIG-325"
    assert captured.value.stage == "scenario_discovery"
    assert captured.value.subject == "selected_scenarios"
    assert captured.value.detail == "unknown"


def test_discovery_requires_the_canonical_registry_script_path(tmp_path: Path) -> None:
    run_config = _run_config(
        tmp_path,
        required=("canonical",),
    )
    spec = _scenario_spec(
        run_config,
        "canonical",
        required=True,
        script_path=Path("validation", "scenarios", "renamed.gfs"),
    )

    with pytest.raises(ConfigurationError) as captured:
        discover_scenarios(run_config, {"canonical": spec})

    assert captured.value.code == "GF-WB-CONFIG-318"
    assert "validation/scenarios/canonical.gfs" in captured.value.detail
    assert "validation/scenarios/renamed.gfs" in captured.value.detail
