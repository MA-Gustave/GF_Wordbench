"""Build deterministic ScenarioSpec values from an optional validation profile."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
import re
from types import MappingProxyType
from typing import Final

from gf_wordbench.kernel.ids import validate_scenario_id, validate_section_id
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.projects.paths import ProjectPaths

from .models import ScenarioComparisonPolicy, ScenarioSpec

__all__ = ("build_profile_scenario_catalog",)

_INPUT_LOCK_RE: Final[re.Pattern[str]] = re.compile(
    r"^-- GF_WORDBENCH_INPUT_SHA256 (?P<sha>[0-9a-f]{64}) (?P<path>[^\r\n]+)$"
)
_BEGIN_RE: Final[re.Pattern[str]] = re.compile(
    r'^\s*ps\s+"GF_WORDBENCH_BEGIN\s+(?P<section>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)"\s*$'
)
_END_RE: Final[re.Pattern[str]] = re.compile(
    r'^\s*ps\s+"GF_WORDBENCH_END\s+(?P<section>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)"\s*$'
)
_OUTPUT_LIMIT_BYTES: Final[int] = 8 * 1024 * 1024


def build_profile_scenario_catalog(
    profile: ProjectConfig,
    *,
    timeout_sec: int = 60,
) -> Mapping[str, ScenarioSpec]:
    """Resolve every registered profile scenario and verify its declared input locks."""

    if not isinstance(profile, ProjectConfig):
        raise TypeError("profile must be ProjectConfig")
    if isinstance(timeout_sec, bool) or not isinstance(timeout_sec, int) or timeout_sec <= 0:
        raise ValueError("timeout_sec must be a positive integer")

    paths = ProjectPaths.from_root(profile.project_root)
    required = {str(value) for value in profile.validation.required_scenarios}
    ordered = tuple(str(value) for value in profile.validation.all_scenarios)
    catalog: dict[str, ScenarioSpec] = {}

    for raw_id in ordered:
        scenario_id = str(validate_scenario_id(raw_id))
        script_abs = paths.scenarios_dir / f"{scenario_id}.gfs"
        if not script_abs.is_file():
            raise FileNotFoundError(f"registered scenario script is missing: {script_abs}")
        script_text = script_abs.read_text(encoding="utf-8")
        if not script_text.endswith("\n"):
            raise ValueError(f"scenario script must end with a newline: {scenario_id}")

        input_paths = _verified_input_paths(script_text, project_root=paths.root)
        sections = _expected_sections(script_text, scenario_id=scenario_id)
        gold_abs = paths.gold_dir / f"{scenario_id}.gold"
        if gold_abs.is_file():
            gold_path = gold_abs.relative_to(paths.root)
            comparison = ScenarioComparisonPolicy.EXACT
        else:
            gold_path = None
            comparison = ScenarioComparisonPolicy.NONE

        catalog[scenario_id] = ScenarioSpec(
            scenario_id=scenario_id,
            script_path=script_abs.relative_to(paths.root),
            required=scenario_id in required,
            enabled_modes=(ValidationMode.DIAGNOSTIC, ValidationMode.CHECKPOINT, ValidationMode.RELEASE),
            working_directory=_working_directory_for_inputs(input_paths, project_root=paths.root),
            timeout_sec=float(timeout_sec),
            output_limit_bytes=_OUTPUT_LIMIT_BYTES,
            gold_path=gold_path,
            comparison_policy=comparison,
            normalization_version="1.0.0",
            expected_sections=sections,
            expected_artifacts=(),
            input_paths=input_paths,
            tags=("albanian", _family_tag(scenario_id)),
        )

    return MappingProxyType(catalog)



def _working_directory_for_inputs(
    input_paths: tuple[Path, ...],
    *,
    project_root: Path,
) -> Path:
    """Choose the narrowest stable cwd for project-locked scenario inputs.

    Generated GF scenarios commonly import their locked probe module by
    basename. When every declared input shares one directory, use that
    directory as cwd; otherwise fall back to the project root.
    """
    parents = {
        (project_root / relative).resolve(strict=True).parent
        for relative in input_paths
    }
    if len(parents) == 1:
        return next(iter(parents))
    return project_root.resolve(strict=True)

def _verified_input_paths(text: str, *, project_root: Path) -> tuple[Path, ...]:
    declared: list[Path] = []
    for line in text.splitlines():
        match = _INPUT_LOCK_RE.fullmatch(line.strip())
        if match is None:
            continue
        relative = Path(match.group("path"))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"scenario input lock must be project-relative: {relative}")
        absolute = (project_root / relative).resolve(strict=True)
        resolved_root = project_root.resolve(strict=True)
        if absolute == resolved_root or not absolute.is_relative_to(resolved_root):
            raise ValueError(f"scenario input escapes profile root: {relative}")
        if not absolute.is_file():
            raise FileNotFoundError(f"scenario input is not a file: {absolute}")
        actual = hashlib.sha256(absolute.read_bytes()).hexdigest()
        expected = match.group("sha")
        if actual != expected:
            raise ValueError(
                f"scenario input SHA mismatch for {relative.as_posix()}: expected {expected}, got {actual}"
            )
        declared.append(relative)
    if not declared:
        raise ValueError("scenario script declares no GF_WORDBENCH_INPUT_SHA256 inputs")
    if len({path.as_posix() for path in declared}) != len(declared):
        raise ValueError("scenario input lock contains duplicate paths")
    return tuple(declared)


def _expected_sections(text: str, *, scenario_id: str) -> tuple[str, ...]:
    begun: list[str] = []
    ended: list[str] = []
    for line in text.splitlines():
        begin = _BEGIN_RE.fullmatch(line)
        if begin is not None:
            begun.append(str(validate_section_id(begin.group("section"))))
        end = _END_RE.fullmatch(line)
        if end is not None:
            ended.append(str(validate_section_id(end.group("section"))))
    if not begun:
        raise ValueError(f"scenario {scenario_id} declares no GF_WORDBENCH_BEGIN sections")
    if tuple(begun) != tuple(ended):
        raise ValueError(f"scenario {scenario_id} begin/end section declarations do not match")
    if len(set(begun)) != len(begun):
        raise ValueError(f"scenario {scenario_id} repeats a section identifier")
    return tuple(begun)


def _family_tag(scenario_id: str) -> str:
    pieces = scenario_id.split("-")
    if len(pieces) >= 2:
        return pieces[1]
    return "campaign"
