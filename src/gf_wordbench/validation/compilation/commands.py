"""Pure, version-aware GF command construction."""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from typing import Final, TypeAlias

PathArgument: TypeAlias = str | os.PathLike[str]

_VERSION_ARGUMENTS: Final[tuple[str, ...]] = ("--version",)
_MAX_ARGUMENTS: Final[int] = 4_096
_MAX_ARGUMENT_LENGTH: Final[int] = 32_768


@unique
class ValueOptionStyle(StrEnum):
    EQUALS = "equals"
    SEPARATE = "separate"


@dataclass(frozen=True, slots=True)
class GfCommandProfile:
    profile_id: str
    path_separator: str
    value_option_style: ValueOptionStyle = ValueOptionStyle.EQUALS
    batch_flag: str = "-batch"
    quiet_flag: str = "-s"
    make_flag: str = "-make"
    optimize_pgf_flag: str | None = "-optimize-pgf"
    path_option: str = "--path"
    gf_lib_path_option: str | None = "--gf-lib-path"
    gfo_dir_option: str | None = "--gfo-dir"
    output_dir_option: str | None = "--output-dir"
    cpu_stats_flag: str | None = "--cpu"

    def __post_init__(self) -> None:
        _validate_identifier(self.profile_id, field_name="profile_id")
        _validate_separator(self.path_separator)
        if not isinstance(self.value_option_style, ValueOptionStyle):
            raise TypeError("value_option_style must be a ValueOptionStyle")
        for field_name in (
            "batch_flag",
            "quiet_flag",
            "make_flag",
            "path_option",
        ):
            _validate_option_name(
                getattr(self, field_name),
                field_name=field_name,
                optional=False,
            )
        for field_name in (
            "optimize_pgf_flag",
            "gf_lib_path_option",
            "gfo_dir_option",
            "output_dir_option",
            "cpu_stats_flag",
        ):
            _validate_option_name(
                getattr(self, field_name),
                field_name=field_name,
                optional=True,
            )

    def value_option(self, option: str, value: str) -> tuple[str, ...]:
        _validate_option_name(option, field_name="option", optional=False)
        normalized_value = _validate_argument(
            value,
            field_name=f"value for {option}",
            allow_empty=False,
        )
        if self.value_option_style is ValueOptionStyle.EQUALS:
            return (f"{option}={normalized_value}",)
        return (option, normalized_value)


@dataclass(frozen=True, slots=True)
class GfCommand:
    operation: str
    executable: Path
    arguments: tuple[str, ...]
    working_directory: Path
    gf_search_paths: tuple[Path, ...] = ()
    profile_id: str | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.operation, field_name="operation")
        object.__setattr__(
            self,
            "executable",
            _coerce_path(self.executable, field_name="executable"),
        )
        object.__setattr__(
            self,
            "working_directory",
            _coerce_path(
                self.working_directory,
                field_name="working_directory",
            ),
        )
        object.__setattr__(
            self,
            "arguments",
            _normalize_arguments(self.arguments),
        )
        object.__setattr__(
            self,
            "gf_search_paths",
            _normalize_paths(
                self.gf_search_paths,
                field_name="gf_search_paths",
                allow_empty=True,
            ),
        )
        if self.profile_id is not None:
            _validate_identifier(
                self.profile_id,
                field_name="profile_id",
            )

    @property
    def argv(self) -> tuple[str, ...]:
        return (os.fspath(self.executable), *self.arguments)


def build_version_probe_arguments() -> tuple[str, ...]:
    return _VERSION_ARGUMENTS


def build_version_probe_command(
    *,
    executable: PathArgument,
    working_directory: PathArgument,
) -> GfCommand:
    return GfCommand(
        operation="probe_version",
        executable=_coerce_path(executable, field_name="executable"),
        arguments=build_version_probe_arguments(),
        working_directory=_coerce_path(
            working_directory,
            field_name="working_directory",
        ),
    )


def serialize_gf_search_path(
    gf_search_paths: Iterable[PathArgument],
    *,
    separator: str,
) -> str:
    _validate_separator(separator)
    paths = _normalize_paths(
        gf_search_paths,
        field_name="gf_search_paths",
        allow_empty=False,
    )
    serialized = separator.join(os.fspath(path) for path in paths)
    return _validate_argument(
        serialized,
        field_name="serialized GF search path",
        allow_empty=False,
    )


def build_module_compile_arguments(
    *,
    source_file: PathArgument,
    gf_search_paths: Iterable[PathArgument],
    profile: GfCommandProfile,
    rgl_root: PathArgument | None = None,
    gfo_dir: PathArgument | None = None,
    output_dir: PathArgument | None = None,
    quiet: bool = True,
    emit_cpu_stats: bool = False,
) -> tuple[str, ...]:
    _require_profile(profile)
    source_argument = _validate_gf_source_argument(source_file)
    search_paths = _normalize_paths(
        gf_search_paths,
        field_name="gf_search_paths",
        allow_empty=False,
    )

    arguments: list[str] = [profile.batch_flag]
    if _require_bool(quiet, field_name="quiet"):
        arguments.append(profile.quiet_flag)

    arguments.extend(
        profile.value_option(
            profile.path_option,
            serialize_gf_search_path(
                search_paths,
                separator=profile.path_separator,
            ),
        )
    )
    arguments.extend(
        _optional_path_option(
            option=profile.gf_lib_path_option,
            value=rgl_root,
            role="RGL root",
            profile=profile,
        )
    )
    arguments.extend(
        _optional_path_option(
            option=profile.gfo_dir_option,
            value=gfo_dir,
            role="GFO directory",
            profile=profile,
        )
    )
    arguments.extend(
        _optional_path_option(
            option=profile.output_dir_option,
            value=output_dir,
            role="output directory",
            profile=profile,
        )
    )

    if _require_bool(
        emit_cpu_stats,
        field_name="emit_cpu_stats",
    ):
        if profile.cpu_stats_flag is None:
            raise ValueError(
                f"GF command profile {profile.profile_id!r} "
                "does not support CPU statistics"
            )
        arguments.append(profile.cpu_stats_flag)

    arguments.append(source_argument)
    return _normalize_arguments(arguments)


def build_module_compile_command(
    *,
    executable: PathArgument,
    working_directory: PathArgument,
    source_file: PathArgument,
    gf_search_paths: Iterable[PathArgument],
    profile: GfCommandProfile,
    rgl_root: PathArgument | None = None,
    gfo_dir: PathArgument | None = None,
    output_dir: PathArgument | None = None,
    quiet: bool = True,
    emit_cpu_stats: bool = False,
) -> GfCommand:
    search_paths = _normalize_paths(
        gf_search_paths,
        field_name="gf_search_paths",
        allow_empty=False,
    )
    return GfCommand(
        operation="compile_module",
        executable=_coerce_path(executable, field_name="executable"),
        arguments=build_module_compile_arguments(
            source_file=source_file,
            gf_search_paths=search_paths,
            profile=profile,
            rgl_root=rgl_root,
            gfo_dir=gfo_dir,
            output_dir=output_dir,
            quiet=quiet,
            emit_cpu_stats=emit_cpu_stats,
        ),
        working_directory=_coerce_path(
            working_directory,
            field_name="working_directory",
        ),
        gf_search_paths=search_paths,
        profile_id=profile.profile_id,
    )


def build_pgf_arguments(
    *,
    entrypoints: Sequence[PathArgument],
    gf_search_paths: Iterable[PathArgument],
    profile: GfCommandProfile,
    rgl_root: PathArgument | None = None,
    output_dir: PathArgument | None = None,
    optimize: bool = True,
    emit_cpu_stats: bool = False,
) -> tuple[str, ...]:
    _require_profile(profile)
    normalized_entrypoints = _normalize_entrypoints(entrypoints)
    search_paths = _normalize_paths(
        gf_search_paths,
        field_name="gf_search_paths",
        allow_empty=False,
    )

    arguments: list[str] = [profile.make_flag]

    if _require_bool(optimize, field_name="optimize"):
        if profile.optimize_pgf_flag is None:
            raise ValueError(
                f"GF command profile {profile.profile_id!r} "
                "does not support optimized PGF construction"
            )
        arguments.append(profile.optimize_pgf_flag)

    arguments.extend(
        profile.value_option(
            profile.path_option,
            serialize_gf_search_path(
                search_paths,
                separator=profile.path_separator,
            ),
        )
    )
    arguments.extend(
        _optional_path_option(
            option=profile.gf_lib_path_option,
            value=rgl_root,
            role="RGL root",
            profile=profile,
        )
    )
    arguments.extend(
        _optional_path_option(
            option=profile.output_dir_option,
            value=output_dir,
            role="PGF output directory",
            profile=profile,
        )
    )

    if _require_bool(
        emit_cpu_stats,
        field_name="emit_cpu_stats",
    ):
        if profile.cpu_stats_flag is None:
            raise ValueError(
                f"GF command profile {profile.profile_id!r} "
                "does not support CPU statistics"
            )
        arguments.append(profile.cpu_stats_flag)

    arguments.extend(normalized_entrypoints)
    return _normalize_arguments(arguments)


def build_pgf_command(
    *,
    executable: PathArgument,
    working_directory: PathArgument,
    entrypoints: Sequence[PathArgument],
    gf_search_paths: Iterable[PathArgument],
    profile: GfCommandProfile,
    rgl_root: PathArgument | None = None,
    output_dir: PathArgument | None = None,
    optimize: bool = True,
    emit_cpu_stats: bool = False,
) -> GfCommand:
    normalized_entrypoints = _normalize_entrypoints(entrypoints)
    search_paths = _normalize_paths(
        gf_search_paths,
        field_name="gf_search_paths",
        allow_empty=False,
    )
    return GfCommand(
        operation="build_pgf",
        executable=_coerce_path(executable, field_name="executable"),
        arguments=build_pgf_arguments(
            entrypoints=normalized_entrypoints,
            gf_search_paths=search_paths,
            profile=profile,
            rgl_root=rgl_root,
            output_dir=output_dir,
            optimize=optimize,
            emit_cpu_stats=emit_cpu_stats,
        ),
        working_directory=_coerce_path(
            working_directory,
            field_name="working_directory",
        ),
        gf_search_paths=search_paths,
        profile_id=profile.profile_id,
    )


def _optional_path_option(
    *,
    option: str | None,
    value: PathArgument | None,
    role: str,
    profile: GfCommandProfile,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if option is None:
        raise ValueError(
            f"GF command profile {profile.profile_id!r} "
            f"does not support a {role} option"
        )
    path = _coerce_path(value, field_name=role)
    return profile.value_option(option, os.fspath(path))


def _normalize_entrypoints(
    entrypoints: Sequence[PathArgument],
) -> tuple[str, ...]:
    if isinstance(entrypoints, (str, bytes, os.PathLike)):
        raise TypeError("entrypoints must be a sequence of paths")
    normalized = tuple(
        _validate_gf_source_argument(
            entrypoint,
            field_name=f"entrypoints[{index}]",
        )
        for index, entrypoint in enumerate(entrypoints)
    )
    if not normalized:
        raise ValueError("entrypoints must contain at least one path")
    if len(normalized) != len(set(normalized)):
        raise ValueError("entrypoints must not contain duplicates")
    return normalized


def _validate_gf_source_argument(
    value: PathArgument,
    *,
    field_name: str = "source_file",
) -> str:
    path = _coerce_path(value, field_name=field_name)
    argument = _validate_argument(
        os.fspath(path),
        field_name=field_name,
        allow_empty=False,
    )
    portable = PurePosixPath(argument.replace("\\", "/"))
    if portable.suffix.casefold() != ".gf":
        raise ValueError(f"{field_name} must end in '.gf'")
    if portable.name in {"", ".", ".."}:
        raise ValueError(f"{field_name} must identify a GF source file")
    return argument


def _normalize_paths(
    values: Iterable[PathArgument],
    *,
    field_name: str,
    allow_empty: bool,
) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, os.PathLike)):
        raise TypeError(f"{field_name} must be an iterable of paths")
    normalized = tuple(
        _coerce_path(
            value,
            field_name=f"{field_name}[{index}]",
        )
        for index, value in enumerate(values)
    )
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _coerce_path(
    value: PathArgument,
    *,
    field_name: str,
) -> Path:
    if isinstance(value, bytes):
        raise TypeError(f"{field_name} must not be bytes")
    try:
        text = os.fspath(value)
    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be a string or path-like value"
        ) from exc
    if not isinstance(text, str):
        raise TypeError(f"{field_name} must resolve to text")
    _validate_argument(
        text,
        field_name=field_name,
        allow_empty=False,
    )
    return Path(text)


def _normalize_arguments(
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("arguments must be an iterable of strings")
    normalized = tuple(
        _validate_argument(
            value,
            field_name=f"arguments[{index}]",
            allow_empty=False,
        )
        for index, value in enumerate(values)
    )
    if len(normalized) > _MAX_ARGUMENTS:
        raise ValueError(
            f"arguments exceed the maximum of {_MAX_ARGUMENTS}"
        )
    return normalized


def _validate_argument(
    value: str,
    *,
    field_name: str,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > _MAX_ARGUMENT_LENGTH:
        raise ValueError(
            f"{field_name} exceeds {_MAX_ARGUMENT_LENGTH} characters"
        )
    if any(ord(character) < 32 for character in value):
        raise ValueError(
            f"{field_name} must not contain control characters"
        )
    return value


def _validate_option_name(
    value: str | None,
    *,
    field_name: str,
    optional: bool,
) -> None:
    if value is None:
        if optional:
            return
        raise TypeError(f"{field_name} must be a string")
    _validate_argument(
        value,
        field_name=field_name,
        allow_empty=False,
    )
    if not value.startswith("-"):
        raise ValueError(f"{field_name} must begin with '-'")
    if "=" in value or any(character.isspace() for character in value):
        raise ValueError(
            f"{field_name} must be an option name without a value"
        )


def _validate_identifier(
    value: str,
    *,
    field_name: str,
) -> None:
    _validate_argument(
        value,
        field_name=field_name,
        allow_empty=False,
    )
    if not all(
        character.isalnum() or character in {"_", "-", "."}
        for character in value
    ):
        raise ValueError(
            f"{field_name} contains unsupported characters"
        )


def _validate_separator(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("path_separator must be a string")
    if len(value) != 1:
        raise ValueError("path_separator must be exactly one character")
    if ord(value) < 32 or value in {"=", "\x00"}:
        raise ValueError("path_separator is invalid")


def _require_bool(value: bool, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a bool")
    return value


def _require_profile(
    profile: GfCommandProfile,
) -> GfCommandProfile:
    if not isinstance(profile, GfCommandProfile):
        raise TypeError("profile must be a GfCommandProfile")
    return profile


__all__ = (
    "GfCommand",
    "GfCommandProfile",
    "PathArgument",
    "ValueOptionStyle",
    "build_module_compile_arguments",
    "build_module_compile_command",
    "build_pgf_arguments",
    "build_pgf_command",
    "build_version_probe_arguments",
    "build_version_probe_command",
    "serialize_gf_search_path",
)
