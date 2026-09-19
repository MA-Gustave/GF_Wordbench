"""Release-fixture acceptance tests for GF Wordbench release readiness.

The fixture is language-neutral and intentionally uses repository-owned typed
contracts. Real GF process execution remains in the separately marked GF
integration suite; this module proves the complete release-fixture declaration,
canonical gate activation, terminal decision semantics, and required evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from gf_wordbench.kernel.ids import ProjectId, RunId
from gf_wordbench.kernel.statuses import ValidationStatus
from gf_wordbench.projects.models import (
    PROJECT_CONFIG_FILENAME,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
)
from gf_wordbench.projects.paths import (
    ProjectPaths,
    resolve_module_path,
    resolve_scenario_path,
)
from gf_wordbench.projects.schema import ProjectDocument, parse_project_document
from gf_wordbench.validation.release.models import (
    RELEASE_GATE_POLICY_VERSION,
    ReleaseDecision,
    ReleaseDecisionValue,
    ReleaseGateApplicability,
    ReleaseGateResult,
)

_RELEASE_PROJECT_ID: Final[ProjectId] = ProjectId("release-fixture")
_RELEASE_RUN_ID: Final[RunId] = RunId("20260725_120000")
_RELEASE_GATE_IDS: Final[tuple[str, ...]] = tuple(f"RG-{index:02d}" for index in range(15))
_CONDITIONAL_GATE_IDS: Final[frozenset[str]] = frozenset({"RG-05", "RG-08", "RG-10"})
_RELEASE_CONDITIONS: Final[dict[str, bool]] = {
    "checkpoints_declared": True,
    "required_gold_backed_scenarios_declared": True,
    "release_requires_pgf": True,
}


def _project_document() -> ProjectDocument:
    return ProjectDocument(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        project={
            "id": _RELEASE_PROJECT_ID,
            "name": "Language-neutral release fixture",
            "language_code": "zz",
            "root": ".",
        },
        sources={
            "directory": "src",
            "glob": "**/*.gf",
            "include_regex": "",
            "exclude_regex": "",
        },
        gf={
            "path_parts": ["src"],
            "minimum_version": "3.12",
        },
        modules={
            "entrypoints": ["Fixture.gf", "FixtureEng.gf"],
            "checkpoints": ["Fixture.gf"],
        },
        validation={
            "required_scenarios": [
                "load-fixture",
                "parse-linearize",
                "missing-function-policy",
            ],
            "optional_scenarios": [],
            "release_requires_pgf": True,
        },
    )


def _write_release_fixture(root: Path) -> None:
    project = root / "project"
    source = project / "src"
    scenarios = project / "validation" / "scenarios"
    gold = project / "validation" / "gold"

    source.mkdir(parents=True)
    scenarios.mkdir(parents=True)
    gold.mkdir(parents=True)

    (project / PROJECT_CONFIG_FILENAME).write_text(
        "# Parsed from the canonical in-memory fixture document.\n",
        encoding="utf-8",
    )
    (source / "Fixture.gf").write_text(
        "abstract Fixture = { cat Item ; fun Sample : Item ; }\n",
        encoding="utf-8",
    )
    (source / "FixtureEng.gf").write_text(
        'concrete FixtureEng of Fixture = { lincat Item = Str ; lin Sample = "sample" ; }\n',
        encoding="utf-8",
    )

    required = _project_document()["validation"]["required_scenarios"]
    for scenario_id in required:
        (scenarios / f"{scenario_id}.gfs").write_text(
            "-- GF Wordbench release fixture scenario\n",
            encoding="utf-8",
        )
        (gold / f"{scenario_id}.gold").write_text(
            "# normalized fixture output\n",
            encoding="utf-8",
        )


def _release_registry() -> ModuleType:
    try:
        return import_module("gf_wordbench.validation.release.registry")
    except Exception as exc:  # pragma: no cover - assertion carries root cause
        pytest.fail(
            f"the canonical release-gate registry must import cleanly: {type(exc).__name__}: {exc}",
            pytrace=True,
        )


def _successful_gate_results() -> tuple[ReleaseGateResult, ...]:
    return tuple(
        ReleaseGateResult(
            gate_id=gate_id,
            name=f"Release gate {gate_id}",
            applicability=(
                ReleaseGateApplicability.CONDITIONAL
                if gate_id in _CONDITIONAL_GATE_IDS
                else ReleaseGateApplicability.REQUIRED
            ),
            status=ValidationStatus.OK,
            summary=f"{gate_id} passed for the release fixture.",
            criteria_total=1,
            criteria_passed=1,
            blockers=(),
            warnings=(),
            evidence_paths=(Path("summary.json"),),
        )
        for gate_id in _RELEASE_GATE_IDS
    )


def test_release_fixture_declares_complete_project_evidence(
    tmp_path: Path,
) -> None:
    _write_release_fixture(tmp_path)
    project_root = (tmp_path / "project").resolve()
    project_file = project_root / PROJECT_CONFIG_FILENAME

    config = parse_project_document(
        _project_document(),
        source_file=project_file,
    )
    paths = ProjectPaths.from_root(project_root)

    assert config.project_id == _RELEASE_PROJECT_ID
    assert config.validation.release_requires_pgf is True
    assert config.modules.entrypoints == (
        Path("Fixture.gf"),
        Path("FixtureEng.gf"),
    )
    assert config.modules.checkpoints == (Path("Fixture.gf"),)

    for module in (*config.modules.checkpoints, *config.modules.entrypoints):
        assert resolve_module_path(config.source_root, module).is_file()

    for scenario_id in config.validation.required_scenarios:
        assert resolve_scenario_path(paths, scenario_id).is_file()
        assert (paths.gold_dir / f"{scenario_id}.gold").is_file()


def test_release_fixture_activates_every_conditional_release_gate() -> None:
    registry = _release_registry()

    active = registry.active_release_gates(
        _RELEASE_CONDITIONS,
        include_decision_gate=True,
    )

    assert registry.CANONICAL_RELEASE_GATE_IDS == _RELEASE_GATE_IDS
    assert tuple(gate.gate_id for gate in active) == _RELEASE_GATE_IDS
    assert active[-1].phase.value == "decision"
    assert all(gate.applicability.value != "not_applicable" for gate in active)


def test_release_fixture_produces_a_ready_terminal_decision() -> None:
    gate_results = _successful_gate_results()
    release_artifacts = (
        Path("summary.json"),
        Path("summary.md"),
        Path("manifest.json"),
        Path("artifacts/pgf/Fixture.pgf"),
    )

    decision = ReleaseDecision(
        decision=ReleaseDecisionValue.READY,
        gate_policy_version=RELEASE_GATE_POLICY_VERSION,
        project_id=_RELEASE_PROJECT_ID,
        run_id=_RELEASE_RUN_ID,
        gf_wordbench_version="1.0.0",
        gf_version="3.12",
        rgl_identity="fixture-rgl",
        gate_results=gate_results,
        required_gate_count=len(gate_results),
        passed_gate_count=len(gate_results),
        failed_gate_ids=(),
        error_gate_ids=(),
        skipped_required_gate_ids=(),
        warning_count=0,
        release_artifact_paths=release_artifacts,
        decided_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
    )

    assert decision.is_ready is True
    assert decision.decision is ReleaseDecisionValue.READY
    assert decision.statement == "GF Wordbench release gates passed."
    assert tuple(result.gate_id for result in decision.gate_results) == (_RELEASE_GATE_IDS)
    assert decision.release_artifact_paths == release_artifacts


def test_release_fixture_cannot_claim_ready_with_a_failed_gate() -> None:
    gate_results = list(_successful_gate_results())
    failed = gate_results[6]
    gate_results[6] = ReleaseGateResult(
        gate_id=failed.gate_id,
        name=failed.name,
        applicability=failed.applicability,
        status=ValidationStatus.FAIL,
        summary="Release entrypoint compilation failed.",
        criteria_total=1,
        criteria_passed=0,
        blockers=("FixtureEng.gf did not compile.",),
        warnings=(),
        evidence_paths=(Path("raw/compile/FixtureEng.log"),),
    )

    with pytest.raises(ValueError, match="decision"):
        ReleaseDecision(
            decision=ReleaseDecisionValue.READY,
            gate_policy_version=RELEASE_GATE_POLICY_VERSION,
            project_id=_RELEASE_PROJECT_ID,
            run_id=_RELEASE_RUN_ID,
            gf_wordbench_version="1.0.0",
            gf_version="3.12",
            rgl_identity="fixture-rgl",
            gate_results=tuple(gate_results),
            required_gate_count=len(gate_results),
            passed_gate_count=len(gate_results) - 1,
            failed_gate_ids=(failed.gate_id,),
            error_gate_ids=(),
            skipped_required_gate_ids=(),
            warning_count=0,
            release_artifact_paths=(Path("manifest.json"),),
            decided_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
        )
