"""Scenario registry discovery and deterministic mode selection."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from gf_wordbench.config.models import RunConfig
from gf_wordbench.kernel.errors import (
    ConfigurationError,
    EvidenceIOError,
    PathSecurityError,
)
from gf_wordbench.kernel.ids import (
    ScenarioId,
    validate_scenario_id,
)
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.paths import (
    ProjectPaths,
    resolve_scenario_path,
)

from .models import ScenarioSpec

__all__ = (
    "ScenarioDiscoveryFilesystem",
    "ScenarioDiscoveryService",
    "discover_scenarios",
)

_SCENARIO_SUFFIX: Final[str] = ".gfs"
_MAX_REGISTERED_SCENARIOS: Final[int] = 4096


@runtime_checkable
class ScenarioDiscoveryFilesystem(Protocol):
    def resolve(
        self,
        path: Path,
        *,
        strict: bool,
    ) -> Path:
        ...

    def exists(self, path: Path) -> bool:
        ...

    def is_file(self, path: Path) -> bool:
        ...

    def is_directory(self, path: Path) -> bool:
        ...

    def is_readable(self, path: Path) -> bool:
        ...


class _LocalScenarioDiscoveryFilesystem:
    __slots__ = ()

    def resolve(
        self,
        path: Path,
        *,
        strict: bool,
    ) -> Path:
        return path.resolve(strict=strict)

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def is_directory(self, path: Path) -> bool:
        return path.is_dir()

    def is_readable(self, path: Path) -> bool:
        return os.access(path, os.R_OK)


_LOCAL_FILESYSTEM: Final[ScenarioDiscoveryFilesystem] = (
    _LocalScenarioDiscoveryFilesystem()
)


@dataclass(frozen=True, slots=True)
class ScenarioDiscoveryService:
    filesystem: ScenarioDiscoveryFilesystem = _LOCAL_FILESYSTEM

    def __post_init__(self) -> None:
        if not isinstance(
            self.filesystem,
            ScenarioDiscoveryFilesystem,
        ):
            raise TypeError(
                "filesystem must satisfy "
                "ScenarioDiscoveryFilesystem"
            )

    def discover(
        self,
        run_config: RunConfig,
        catalog: Mapping[str, ScenarioSpec],
        *,
        explicit_scenario_ids: Sequence[str] | None = None,
    ) -> tuple[ScenarioSpec, ...]:
        _require_run_config(run_config)
        normalized_catalog = _normalize_catalog(catalog)
        explicit_ids = _normalize_explicit_ids(
            run_config.selected_scenarios
            if explicit_scenario_ids is None
            else explicit_scenario_ids
        )

        required_ids = tuple(
            validate_scenario_id(
                value,
                field=(
                    "project.validation."
                    f"required_scenarios[{index}]"
                ),
            )
            for index, value in enumerate(
                run_config.project.validation.required_scenarios
            )
        )
        optional_ids = tuple(
            validate_scenario_id(
                value,
                field=(
                    "project.validation."
                    f"optional_scenarios[{index}]"
                ),
            )
            for index, value in enumerate(
                run_config.project.validation.optional_scenarios
            )
        )

        _validate_registry_size(
            required_ids,
            optional_ids,
        )
        _validate_explicit_membership(
            explicit_ids,
            required_ids=required_ids,
            optional_ids=optional_ids,
        )

        project_paths = ProjectPaths.from_root(
            run_config.project.project_root
        )
        resolved_project_root = self._require_directory(
            project_paths.root,
            field="project.project_root",
        )
        resolved_scenarios_root = self._require_directory(
            project_paths.scenarios_dir,
            field="project.validation.scenarios",
        )

        if not _contains(
            resolved_project_root,
            resolved_scenarios_root,
            allow_equal=False,
        ):
            raise PathSecurityError(
                "The canonical scenario directory escapes "
                "the active project root.",
                code="GF-WB-PATH-310",
                detail=(
                    f"project_root={resolved_project_root!s}\n"
                    f"scenarios_root={resolved_scenarios_root!s}"
                ),
                stage="scenario_discovery",
                operation="resolve_registry_roots",
                subject=str(resolved_scenarios_root),
            )

        validated_required: dict[str, ScenarioSpec] = {}
        for scenario_id in required_ids:
            spec = normalized_catalog.get(str(scenario_id))
            if spec is None:
                raise _configuration_error(
                    "A required registered scenario has no "
                    "resolved ScenarioSpec.",
                    code="GF-WB-CONFIG-310",
                    subject=str(scenario_id),
                    detail=(
                        f"scenario_id={scenario_id}\n"
                        "registry=required"
                    ),
                )
            self._validate_spec(
                spec,
                scenario_id=scenario_id,
                required=True,
                project_paths=project_paths,
                resolved_project_root=resolved_project_root,
                resolved_scenarios_root=resolved_scenarios_root,
            )
            validated_required[str(scenario_id)] = spec

        selected: list[ScenarioSpec] = []
        selected_ids: set[str] = set()

        for scenario_id in required_ids:
            spec = validated_required[str(scenario_id)]

            if (
                run_config.mode is ValidationMode.RELEASE
                and not spec.is_enabled_for(
                    ValidationMode.RELEASE
                )
            ):
                raise _configuration_error(
                    "A required release scenario is disabled "
                    "for release mode.",
                    code="GF-WB-CONFIG-311",
                    subject=str(scenario_id),
                    detail=(
                        f"scenario_id={scenario_id}\n"
                        "mode=release"
                    ),
                )

            if spec.is_enabled_for(run_config.mode):
                selected.append(spec)
                selected_ids.add(str(scenario_id))

        explicit_set = {
            str(scenario_id)
            for scenario_id in explicit_ids
        }

        for scenario_id in explicit_ids:
            key = str(scenario_id)
            spec = normalized_catalog.get(key)
            if spec is None:
                registry_kind = (
                    "required"
                    if scenario_id in required_ids
                    else "optional"
                )
                raise _configuration_error(
                    "An explicitly selected registered scenario "
                    "has no resolved ScenarioSpec.",
                    code="GF-WB-CONFIG-312",
                    subject=key,
                    detail=(
                        f"scenario_id={key}\n"
                        f"registry={registry_kind}"
                    ),
                )

            required = scenario_id in required_ids
            self._validate_spec(
                spec,
                scenario_id=scenario_id,
                required=required,
                project_paths=project_paths,
                resolved_project_root=resolved_project_root,
                resolved_scenarios_root=resolved_scenarios_root,
            )

            if not spec.is_enabled_for(run_config.mode):
                raise _configuration_error(
                    "The explicitly selected scenario is disabled "
                    "for the current validation mode.",
                    code="GF-WB-CONFIG-313",
                    subject=key,
                    detail=(
                        f"scenario_id={key}\n"
                        f"mode={run_config.mode.value}"
                    ),
                )

        for scenario_id in optional_ids:
            key = str(scenario_id)
            if key not in explicit_set:
                continue

            spec = normalized_catalog[key]
            if key in selected_ids:
                continue
            selected.append(spec)
            selected_ids.add(key)

        if run_config.mode is ValidationMode.RELEASE:
            missing_required = tuple(
                str(scenario_id)
                for scenario_id in required_ids
                if str(scenario_id) not in selected_ids
            )
            if missing_required:
                raise _configuration_error(
                    "Release scenario selection omitted required "
                    "project scenarios.",
                    code="GF-WB-CONFIG-314",
                    subject="selected_scenarios",
                    detail="\n".join(missing_required),
                )

        if (
            not selected
            and explicit_ids
        ):
            raise _configuration_error(
                "The explicit scenario selection produced no "
                "runnable scenarios.",
                code="GF-WB-CONFIG-315",
                subject="selected_scenarios",
                detail=(
                    f"mode={run_config.mode.value}\n"
                    f"requested={','.join(map(str, explicit_ids))}"
                ),
            )

        _require_unique_selected_ids(selected)
        return tuple(selected)

    def _validate_spec(
        self,
        spec: ScenarioSpec,
        *,
        scenario_id: ScenarioId,
        required: bool,
        project_paths: ProjectPaths,
        resolved_project_root: Path,
        resolved_scenarios_root: Path,
    ) -> None:
        if not isinstance(spec, ScenarioSpec):
            raise TypeError(
                "catalog values must be ScenarioSpec instances"
            )
        if spec.scenario_id != scenario_id:
            raise _configuration_error(
                "ScenarioSpec identity does not match the "
                "project registry.",
                code="GF-WB-CONFIG-316",
                subject=str(scenario_id),
                detail=(
                    f"registry_id={scenario_id}\n"
                    f"spec_id={spec.scenario_id}"
                ),
            )
        if spec.required is not required:
            raise _configuration_error(
                "ScenarioSpec required state does not match the "
                "project registry.",
                code="GF-WB-CONFIG-317",
                subject=str(scenario_id),
                detail=(
                    f"registry_required={required}\n"
                    f"spec_required={spec.required}"
                ),
            )

        expected_absolute = resolve_scenario_path(
            project_paths,
            str(scenario_id),
        )
        expected_relative = expected_absolute.relative_to(
            project_paths.root
        )

        if spec.script_path != expected_relative:
            raise _configuration_error(
                "ScenarioSpec script_path does not use the "
                "canonical scenario registry path.",
                code="GF-WB-CONFIG-318",
                subject=str(scenario_id),
                detail=(
                    f"expected={expected_relative.as_posix()}\n"
                    f"actual={spec.script_path.as_posix()}"
                ),
            )

        lexical_script_path = project_paths.resolve_project_path(
            spec.script_path,
            role=f"scenario {scenario_id} script",
        )
        resolved_script_path = self._require_file(
            lexical_script_path,
            field=f"scenario[{scenario_id}].script_path",
        )

        if resolved_script_path.suffix.casefold() != _SCENARIO_SUFFIX:
            raise _configuration_error(
                "A registered scenario script must end in .gfs.",
                code="GF-WB-CONFIG-319",
                subject=str(scenario_id),
                detail=f"path={resolved_script_path!s}",
            )

        if not _contains(
            resolved_project_root,
            resolved_script_path,
            allow_equal=False,
        ):
            raise PathSecurityError(
                "A registered scenario script escapes the "
                "active project root.",
                code="GF-WB-PATH-311",
                detail=(
                    f"scenario_id={scenario_id}\n"
                    f"path={resolved_script_path!s}"
                ),
                stage="scenario_discovery",
                operation="validate_script_path",
                subject=str(resolved_script_path),
            )

        if not _contains(
            resolved_scenarios_root,
            resolved_script_path,
            allow_equal=False,
        ):
            raise PathSecurityError(
                "A registered scenario script escapes the "
                "canonical scenario directory.",
                code="GF-WB-PATH-312",
                detail=(
                    f"scenario_id={scenario_id}\n"
                    f"path={resolved_script_path!s}"
                ),
                stage="scenario_discovery",
                operation="validate_script_path",
                subject=str(resolved_script_path),
            )

        if not self._is_readable(resolved_script_path):
            raise EvidenceIOError(
                "A registered scenario script is not readable.",
                code="GF-WB-IO-310",
                detail=(
                    f"scenario_id={scenario_id}\n"
                    f"path={resolved_script_path!s}"
                ),
                stage="scenario_discovery",
                operation="validate_script_readability",
                subject=str(resolved_script_path),
                retryable=True,
            )

    def _require_directory(
        self,
        path: Path,
        *,
        field: str,
    ) -> Path:
        normalized = self._resolve(
            path,
            strict=False,
            operation="resolve_directory",
        )
        if not self._exists(normalized):
            raise _configuration_error(
                "A required scenario discovery directory "
                "does not exist.",
                code="GF-WB-CONFIG-320",
                subject=field,
                detail=f"path={normalized!s}",
            )
        if not self._is_directory(normalized):
            raise _configuration_error(
                "A required scenario discovery path is not "
                "a directory.",
                code="GF-WB-CONFIG-321",
                subject=field,
                detail=f"path={normalized!s}",
            )
        if not self._is_readable(normalized):
            raise EvidenceIOError(
                "A required scenario discovery directory is "
                "not readable.",
                code="GF-WB-IO-311",
                detail=f"path={normalized!s}",
                stage="scenario_discovery",
                operation="validate_directory",
                subject=field,
                retryable=True,
            )
        return self._resolve(
            normalized,
            strict=True,
            operation="resolve_existing_directory",
        )

    def _require_file(
        self,
        path: Path,
        *,
        field: str,
    ) -> Path:
        normalized = self._resolve(
            path,
            strict=False,
            operation="resolve_scenario_script",
        )
        if not self._exists(normalized):
            raise _configuration_error(
                "A referenced scenario script does not exist.",
                code="GF-WB-CONFIG-322",
                subject=field,
                detail=f"path={normalized!s}",
            )
        if not self._is_file(normalized):
            raise _configuration_error(
                "A referenced scenario script is not a "
                "regular file.",
                code="GF-WB-CONFIG-323",
                subject=field,
                detail=f"path={normalized!s}",
            )
        return self._resolve(
            normalized,
            strict=True,
            operation="resolve_existing_scenario_script",
        )

    def _resolve(
        self,
        path: Path,
        *,
        strict: bool,
        operation: str,
    ) -> Path:
        if not isinstance(path, Path):
            raise TypeError(
                "scenario discovery paths must be pathlib.Path"
            )
        if "\x00" in str(path):
            raise ValueError(
                "scenario discovery paths must not contain NUL"
            )

        try:
            return self.filesystem.resolve(
                path,
                strict=strict,
            )
        except FileNotFoundError:
            if strict:
                raise
            return path.absolute()
        except OSError as exc:
            raise EvidenceIOError(
                "A scenario discovery path could not be "
                "resolved.",
                code="GF-WB-IO-312",
                detail=f"path={path!s}\nerror={exc}",
                stage="scenario_discovery",
                operation=operation,
                subject=str(path),
                retryable=True,
            ) from exc

    def _exists(self, path: Path) -> bool:
        try:
            return self.filesystem.exists(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A scenario discovery path could not be "
                "inspected.",
                code="GF-WB-IO-313",
                detail=f"path={path!s}\nerror={exc}",
                stage="scenario_discovery",
                operation="exists",
                subject=str(path),
                retryable=True,
            ) from exc

    def _is_file(self, path: Path) -> bool:
        try:
            return self.filesystem.is_file(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A scenario path could not be inspected.",
                code="GF-WB-IO-314",
                detail=f"path={path!s}\nerror={exc}",
                stage="scenario_discovery",
                operation="is_file",
                subject=str(path),
                retryable=True,
            ) from exc

    def _is_directory(self, path: Path) -> bool:
        try:
            return self.filesystem.is_directory(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A scenario directory could not be inspected.",
                code="GF-WB-IO-315",
                detail=f"path={path!s}\nerror={exc}",
                stage="scenario_discovery",
                operation="is_directory",
                subject=str(path),
                retryable=True,
            ) from exc

    def _is_readable(self, path: Path) -> bool:
        try:
            return self.filesystem.is_readable(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A scenario path readability check failed.",
                code="GF-WB-IO-316",
                detail=f"path={path!s}\nerror={exc}",
                stage="scenario_discovery",
                operation="is_readable",
                subject=str(path),
                retryable=True,
            ) from exc


def discover_scenarios(
    run_config: RunConfig,
    catalog: Mapping[str, ScenarioSpec],
    *,
    explicit_scenario_ids: Sequence[str] | None = None,
    filesystem: ScenarioDiscoveryFilesystem | None = None,
) -> tuple[ScenarioSpec, ...]:
    service = ScenarioDiscoveryService(
        filesystem=filesystem or _LOCAL_FILESYSTEM
    )
    return service.discover(
        run_config,
        catalog,
        explicit_scenario_ids=explicit_scenario_ids,
    )


def _normalize_catalog(
    catalog: Mapping[str, ScenarioSpec],
) -> dict[str, ScenarioSpec]:
    if not isinstance(catalog, Mapping):
        raise TypeError(
            "catalog must be a mapping of scenario IDs "
            "to ScenarioSpec values"
        )
    if len(catalog) > _MAX_REGISTERED_SCENARIOS:
        raise ValueError(
            "catalog exceeds the supported scenario limit"
        )

    normalized: dict[str, ScenarioSpec] = {}
    for raw_key, spec in catalog.items():
        scenario_id = validate_scenario_id(
            raw_key,
            field="catalog key",
        )
        key = str(scenario_id)

        if not isinstance(spec, ScenarioSpec):
            raise TypeError(
                f"catalog[{key!r}] must be a ScenarioSpec"
            )
        if spec.scenario_id != scenario_id:
            raise ValueError(
                f"catalog key {key!r} does not match "
                f"ScenarioSpec ID {spec.scenario_id!r}"
            )
        if key in normalized:
            raise ValueError(
                f"catalog contains duplicate scenario ID {key!r}"
            )

        normalized[key] = spec

    return normalized


def _normalize_explicit_ids(
    values: Sequence[str],
) -> tuple[ScenarioId, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            "explicit_scenario_ids must be a sequence "
            "of scenario IDs"
        )
    if len(values) > _MAX_REGISTERED_SCENARIOS:
        raise ValueError(
            "explicit_scenario_ids exceeds the supported limit"
        )

    normalized: list[ScenarioId] = []
    seen: set[str] = set()

    for index, value in enumerate(values):
        scenario_id = validate_scenario_id(
            value,
            field=f"explicit_scenario_ids[{index}]",
        )
        key = str(scenario_id)
        if key in seen:
            raise _configuration_error(
                "Explicit scenario filters contain a duplicate ID.",
                code="GF-WB-CONFIG-324",
                subject=key,
            )
        seen.add(key)
        normalized.append(scenario_id)

    return tuple(normalized)


def _validate_explicit_membership(
    explicit_ids: tuple[ScenarioId, ...],
    *,
    required_ids: tuple[ScenarioId, ...],
    optional_ids: tuple[ScenarioId, ...],
) -> None:
    registered = {
        str(scenario_id)
        for scenario_id in (
            *required_ids,
            *optional_ids,
        )
    }
    unknown = tuple(
        str(scenario_id)
        for scenario_id in explicit_ids
        if str(scenario_id) not in registered
    )
    if unknown:
        raise _configuration_error(
            "Explicit scenario filters reference "
            "unregistered scenario IDs.",
            code="GF-WB-CONFIG-325",
            subject="selected_scenarios",
            detail="\n".join(unknown),
        )


def _validate_registry_size(
    required_ids: tuple[ScenarioId, ...],
    optional_ids: tuple[ScenarioId, ...],
) -> None:
    if (
        len(required_ids) + len(optional_ids)
        > _MAX_REGISTERED_SCENARIOS
    ):
        raise ValueError(
            "project scenario registry exceeds the supported limit"
        )

    required_keys = {
        str(scenario_id)
        for scenario_id in required_ids
    }
    overlap = tuple(
        str(scenario_id)
        for scenario_id in optional_ids
        if str(scenario_id) in required_keys
    )
    if overlap:
        raise _configuration_error(
            "Scenario IDs cannot be both required and optional.",
            code="GF-WB-CONFIG-326",
            subject="project.validation",
            detail="\n".join(overlap),
        )


def _require_unique_selected_ids(
    specs: Sequence[ScenarioSpec],
) -> None:
    seen: set[str] = set()
    for spec in specs:
        key = str(spec.scenario_id)
        if key in seen:
            raise AssertionError(
                "scenario discovery produced duplicate IDs"
            )
        seen.add(key)


def _require_run_config(
    value: object,
) -> RunConfig:
    if not isinstance(value, RunConfig):
        raise TypeError(
            "run_config must be a RunConfig"
        )
    if not isinstance(value.mode, ValidationMode):
        raise TypeError(
            "run_config.mode must be a ValidationMode"
        )
    return value


def _contains(
    root: Path,
    candidate: Path,
    *,
    allow_equal: bool,
) -> bool:
    try:
        common = Path(
            os.path.commonpath(
                (str(root), str(candidate))
            )
        )
    except ValueError:
        return False

    if _path_key(common) != _path_key(root):
        return False
    if (
        not allow_equal
        and _path_key(candidate) == _path_key(root)
    ):
        return False
    return True


def _path_key(path: Path) -> str:
    return os.path.normcase(
        os.path.normpath(str(path))
    )


def _configuration_error(
    message: str,
    *,
    code: str,
    subject: str | None = None,
    detail: str = "",
) -> ConfigurationError:
    return ConfigurationError(
        message,
        code=code,
        detail=detail,
        stage="scenario_discovery",
        operation="discover_scenarios",
        subject=subject,
    )
