"""Initialize an optional external GF Wordbench validation profile."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import sys
from typing import Final, Never

_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SOURCE_ROOT: Final[Path] = _REPOSITORY_ROOT / "src"
if os.fspath(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_SOURCE_ROOT))

from gf_wordbench.entrypoints.cli.exit_codes import (  # noqa: E402
    EXIT_CANCELLED,
    EXIT_OK,
    EXIT_RUNTIME_ERROR,
    EXIT_USAGE_ERROR,
)
from gf_wordbench.kernel.errors import (  # noqa: E402
    ConfigurationError,
    GFWordbenchError,
)
from gf_wordbench.projects.filesystem_adapter import (  # noqa: E402
    ProjectFilesystemAdapter,
)
from gf_wordbench.projects.initializer import (  # noqa: E402
    ProjectInitializationRequest,
    ProjectInitializationResult,
)
from gf_wordbench.projects.models import ProjectConfig  # noqa: E402
from gf_wordbench.projects.ports import (  # noqa: E402
    ProjectConfigWriter,
    ProjectFilesystem,
    ProjectTemplateSource,
    TreeEntry,
    TreeEntryKind,
)
from gf_wordbench.projects.public import initialize_project  # noqa: E402
from gf_wordbench.projects.schema import (  # noqa: E402
    ProjectDocument,
    parse_project_document,
    validate_project_schema,
)
from gf_wordbench.projects.toml_adapter import (  # noqa: E402
    read_project_toml,
    write_project_toml,
)

_PROFILE_FILENAME: Final[str] = "project.toml"
_TEMPLATE_DIRECTORY: Final[PurePosixPath] = PurePosixPath("templates/validation-profile")
_SOURCE_DIRECTORY: Final[PurePosixPath] = PurePosixPath("src/gf_wordbench")

_TEXT_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".gf", ".gfs", ".json", ".md", ".toml", ".txt", ".yaml", ".yml"}
)
_MAX_ERROR_DETAIL: Final[int] = 4_000


class _ArgumentError(ValueError):
    """Raised when command-line values cannot form an initialization request."""


class _Parser(argparse.ArgumentParser):
    """Argument parser that reports invalid input through ``main``."""

    def error(self, message: str) -> Never:
        raise _ArgumentError(message)


@dataclass(frozen=True, slots=True)
class _Arguments:
    repository_root: Path
    destination_root: Path
    config_file: Path
    replacements: Mapping[str, str]
    strict_placeholders: bool
    allow_existing_empty_profile: bool


@dataclass(frozen=True, slots=True)
class _FilesystemTemplateSource:
    """Materialize the canonical validation-profile template."""

    root: Path
    filesystem: ProjectFilesystem

    def __post_init__(self) -> None:
        root = self.filesystem.resolve(self.root)
        if not self.filesystem.is_directory(root):
            raise _ArgumentError(f"canonical validation-profile template is missing: {root}")
        object.__setattr__(self, "root", root)
        self.inventory()

    def inventory(self) -> tuple[TreeEntry, ...]:
        entries = self.filesystem.inspect_tree(self.root)
        if not entries:
            raise _ArgumentError(f"canonical validation-profile template is empty: {self.root}")
        return entries

    def materialize(
        self,
        destination: Path,
        *,
        replacements: Mapping[str, str],
    ) -> None:
        stage_root = self.filesystem.resolve(destination)
        self.filesystem.copy_tree(self.root, stage_root)

        try:
            self._replace_template_tokens(stage_root, replacements)
        except BaseException:
            if self.filesystem.exists(stage_root):
                self.filesystem.remove_tree(stage_root)
            raise

    def _replace_template_tokens(
        self,
        stage_root: Path,
        replacements: Mapping[str, str],
    ) -> None:
        if not replacements:
            return

        for entry in self.filesystem.inspect_tree(self.root):
            if entry.kind is not TreeEntryKind.FILE:
                continue

            relative_path = PurePosixPath(entry.relative_path.as_posix())
            if relative_path.suffix.lower() not in _TEXT_SUFFIXES:
                continue

            target = stage_root.joinpath(*relative_path.parts)
            original = self.filesystem.read_text(target, encoding="utf-8")
            rendered = original
            for token, replacement in replacements.items():
                rendered = rendered.replace(token, replacement)

            if rendered != original:
                self.filesystem.write_text_atomic(
                    target,
                    rendered,
                    encoding="utf-8",
                    overwrite=True,
                )


@dataclass(frozen=True, slots=True)
class _TomlProjectConfigWriter:
    """Adapt a typed validation-profile configuration to TOML."""

    def write(
        self,
        project_file: Path,
        config: ProjectConfig,
        *,
        overwrite: bool = False,
    ) -> None:
        path = Path(project_file)
        if path.exists() and not overwrite:
            raise FileExistsError(os.fspath(path))
        write_project_toml(path, _project_document(config))


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="init_project.py",
        description=(
            "Initialize an optional external validation profile from templates/validation-profile/."
        ),
    )
    parser.add_argument(
        "--repository-root",
        "--workspace-root",
        dest="repository_root",
        type=Path,
        default=_REPOSITORY_ROOT,
        help=(
            "GF Wordbench repository root containing the canonical template "
            "(default: repository containing this script)."
        ),
    )
    parser.add_argument(
        "--destination",
        "--profile-root",
        dest="destination_root",
        type=Path,
        required=True,
        help=(
            "External directory that will receive the validation profile. "
            "It must not be inside the GF Wordbench repository."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help=(
            "TOML file containing the final validation-profile configuration. "
            "The source file must remain outside the destination directory."
        ),
    )
    parser.add_argument(
        "--set",
        dest="replacement_values",
        action="append",
        default=[],
        metavar="TOKEN=VALUE",
        help=(
            "Replace one template token. TOKEN may be PROJECT_OWNER or "
            "<PROJECT_OWNER>; repeat as needed."
        ),
    )
    parser.add_argument(
        "--strict-placeholders",
        action="store_true",
        help="Reject publication when any <UPPER_SNAKE_CASE> token remains.",
    )
    parser.add_argument(
        "--allow-existing-empty-profile",
        "--allow-existing-empty-project",
        dest="allow_existing_empty_profile",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Permit publication only when an existing destination directory is "
            "empty (default: enabled)."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        namespace = build_parser().parse_args(argv)
        arguments = _arguments_from_namespace(namespace)
        result = _initialize(arguments)
    except SystemExit as error:
        if isinstance(error.code, int):
            return error.code
        return EXIT_OK if error.code is None else EXIT_USAGE_ERROR
    except KeyboardInterrupt:
        print("Validation-profile initialization cancelled.", file=sys.stderr)
        return EXIT_CANCELLED
    except (
        _ArgumentError,
        ConfigurationError,
        FileNotFoundError,
        NotADirectoryError,
    ) as error:
        _print_error(error)
        return EXIT_USAGE_ERROR
    except (TypeError, ValueError) as error:
        _print_error(error)
        return EXIT_USAGE_ERROR
    except (OSError, GFWordbenchError) as error:
        _print_error(error)
        return EXIT_RUNTIME_ERROR
    except Exception as error:
        _print_error(error)
        return EXIT_RUNTIME_ERROR

    _print_result(result)
    return EXIT_OK


def _arguments_from_namespace(namespace: argparse.Namespace) -> _Arguments:
    repository_root = _absolute_normalized(namespace.repository_root)
    destination_root = _absolute_normalized(
        namespace.destination_root,
        base=Path.cwd(),
    )
    config_file = _absolute_normalized(namespace.config, base=Path.cwd())

    strict_placeholders = namespace.strict_placeholders
    allow_existing_empty_profile = namespace.allow_existing_empty_profile

    if type(strict_placeholders) is not bool:
        raise _ArgumentError("--strict-placeholders must be boolean")
    if type(allow_existing_empty_profile) is not bool:
        raise _ArgumentError("--allow-existing-empty-profile must be boolean")

    replacements = _parse_replacements(namespace.replacement_values)
    return _Arguments(
        repository_root=repository_root,
        destination_root=destination_root,
        config_file=config_file,
        replacements=replacements,
        strict_placeholders=strict_placeholders,
        allow_existing_empty_profile=allow_existing_empty_profile,
    )


def _initialize(arguments: _Arguments) -> ProjectInitializationResult:
    _validate_repository(arguments.repository_root)

    filesystem = ProjectFilesystemAdapter()
    repository_root = filesystem.resolve(arguments.repository_root)
    template_root = filesystem.resolve(repository_root.joinpath(*_TEMPLATE_DIRECTORY.parts))
    destination_root = filesystem.resolve(arguments.destination_root)
    profile_file = destination_root / _PROFILE_FILENAME

    _validate_external_inputs(
        repository_root=repository_root,
        template_root=template_root,
        destination_root=destination_root,
        config_file=arguments.config_file,
    )

    config = _load_initialization_config(
        arguments.config_file,
        profile_file=profile_file,
    )
    replacements = _automatic_replacements(config) | dict(arguments.replacements)

    template_source: ProjectTemplateSource = _FilesystemTemplateSource(
        root=template_root,
        filesystem=filesystem,
    )
    config_writer: ProjectConfigWriter = _TomlProjectConfigWriter()

    request = _build_initialization_request(
        repository_root=repository_root,
        destination_root=destination_root,
        config=config,
        replacements=replacements,
        strict_placeholders=arguments.strict_placeholders,
        allow_existing_empty_profile=(arguments.allow_existing_empty_profile),
    )

    return initialize_project(
        request,
        template_source=template_source,
        filesystem=filesystem,
        config_writer=config_writer,
    )


def _build_initialization_request(
    *,
    repository_root: Path,
    destination_root: Path,
    config: ProjectConfig,
    replacements: Mapping[str, str],
    strict_placeholders: bool,
    allow_existing_empty_profile: bool,
) -> ProjectInitializationRequest:
    """Build the canonical project-initialization request."""

    return ProjectInitializationRequest(
        workspace_root=repository_root,
        project_root=destination_root,
        config=config,
        template_values=replacements,
        require_resolved_placeholders=strict_placeholders,
        allow_existing_empty_project=allow_existing_empty_profile,
    )


def _validate_external_inputs(
    *,
    repository_root: Path,
    template_root: Path,
    destination_root: Path,
    config_file: Path,
) -> None:
    if _paths_overlap(destination_root, repository_root):
        raise _ArgumentError(
            "validation-profile destination must be external to the "
            f"GF Wordbench repository: {destination_root}"
        )

    if _paths_overlap(destination_root, template_root):
        raise _ArgumentError(
            "validation-profile destination must not overlap the canonical "
            f"template: {template_root}"
        )

    if _is_relative_to(config_file, destination_root):
        raise _ArgumentError(
            "initialization config must remain outside the destination "
            f"directory: {destination_root}"
        )

    if _is_relative_to(config_file, template_root):
        raise _ArgumentError(
            "initialization config must not modify or originate from the "
            f"canonical template: {template_root}"
        )

    destination_parent = destination_root.parent
    if not destination_parent.is_dir():
        raise NotADirectoryError(
            f"validation-profile destination parent does not exist: {destination_parent}"
        )


def _load_initialization_config(
    config_file: Path,
    *,
    profile_file: Path,
) -> ProjectConfig:
    if not config_file.is_file():
        raise FileNotFoundError(f"initialization config not found: {config_file}")

    document = read_project_toml(config_file)
    validated = validate_project_schema(document, source=config_file)
    return parse_project_document(
        ProjectDocument(**validated),
        source_file=profile_file,
    )


def _project_document(config: ProjectConfig) -> ProjectDocument:
    return ProjectDocument(
        schema_id=str(config.schema_id),
        schema_version=config.schema_version,
        project={
            "id": str(config.identity.id),
            "name": config.identity.name,
            "language_code": config.identity.language_code,
            "root": config.identity.root.as_posix(),
        },
        sources={
            "directory": config.sources.directory.as_posix(),
            "glob": config.sources.glob,
            "include_regex": config.sources.include_regex,
            "exclude_regex": config.sources.exclude_regex,
        },
        gf={
            "path_parts": list(config.gf.path_parts),
            "minimum_version": config.gf.minimum_version,
        },
        modules={
            "entrypoints": [path.as_posix() for path in config.modules.entrypoints],
            "checkpoints": [path.as_posix() for path in config.modules.checkpoints],
        },
        validation={
            "required_scenarios": [str(value) for value in config.validation.required_scenarios],
            "optional_scenarios": [str(value) for value in config.validation.optional_scenarios],
            "release_requires_pgf": (config.validation.release_requires_pgf),
        },
    )


def _automatic_replacements(
    config: ProjectConfig,
) -> dict[str, str]:
    entrypoints = tuple(path.as_posix() for path in config.modules.entrypoints)
    checkpoints = tuple(path.as_posix() for path in config.modules.checkpoints)
    required_scenarios = tuple(str(value) for value in config.validation.required_scenarios)
    optional_scenarios = tuple(str(value) for value in config.validation.optional_scenarios)

    primary_entrypoint = entrypoints[0]
    primary_entrypoint_path = PurePosixPath(primary_entrypoint)
    source_directory = config.sources.directory.as_posix()

    replacements = {
        "<PROJECT_ID>": str(config.identity.id),
        "<PROJECT_NAME>": config.identity.name,
        "<PROJECT_DISPLAY_NAME>": config.identity.name,
        "<LANGUAGE_NAME>": config.identity.name,
        "<LANGUAGE_CODE>": config.identity.language_code,
        "<PROJECT_ROOT>": ".",
        "<SOURCE_DIRECTORY>": source_directory,
        "<SOURCE_DIR>": source_directory,
        "<SOURCE_ROOT>": source_directory,
        "<SOURCE_GLOB>": config.sources.glob,
        "<INCLUDE_REGEX>": config.sources.include_regex,
        "<EXCLUDE_REGEX>": config.sources.exclude_regex,
        "<PRIMARY_ENTRYPOINT>": primary_entrypoint_path.stem,
        "<ENTRYPOINT>": primary_entrypoint,
        "<ENTRYPOINTS>": _render_values(entrypoints),
        "<CHECKPOINTS>": _render_values(checkpoints),
        "<REQUIRED_SCENARIOS>": _render_values(required_scenarios),
        "<OPTIONAL_SCENARIOS>": _render_values(optional_scenarios),
        "<PROJECT_SCHEMA_VERSION>": config.schema_version,
    }

    if config.gf.path_parts:
        replacements["<SOURCE_PATH_PART>"] = config.gf.path_parts[0]
    if config.gf.minimum_version:
        replacements["<GF_MINIMUM_VERSION>"] = config.gf.minimum_version

    return replacements


def _parse_replacements(values: object) -> Mapping[str, str]:
    if not isinstance(values, list):
        raise _ArgumentError("--set values must be a list")

    replacements: dict[str, str] = {}
    for raw in values:
        if not isinstance(raw, str) or "=" not in raw:
            raise _ArgumentError("--set must use TOKEN=VALUE")

        token, replacement = raw.split("=", 1)
        token = token.strip()
        replacement = replacement.strip()

        if not token:
            raise _ArgumentError("--set token must not be empty")
        if not token.startswith("<"):
            token = f"<{token}>"
        if not replacement:
            raise _ArgumentError(f"replacement for {token} must not be empty")

        replacements[token] = replacement

    return dict(sorted(replacements.items()))


def _validate_repository(repository_root: Path) -> None:
    required = (
        repository_root / "pyproject.toml",
        repository_root.joinpath(
            *_TEMPLATE_DIRECTORY.parts,
            _PROFILE_FILENAME,
        ),
        repository_root.joinpath(*_SOURCE_DIRECTORY.parts),
    )
    missing = tuple(path for path in required if not path.exists())
    if missing:
        rendered = ", ".join(os.fspath(path) for path in missing)
        raise _ArgumentError(f"workspace is not a complete GF Wordbench repository: {rendered}")


def _absolute_normalized(
    value: Path,
    *,
    base: Path | None = None,
) -> Path:
    if not isinstance(value, Path):
        raise _ArgumentError("path arguments must be pathlib.Path values")

    path = value.expanduser()
    if not path.is_absolute():
        path = (base or Path.cwd()) / path
    return path.resolve(strict=False)


def _paths_overlap(first: Path, second: Path) -> bool:
    first_resolved = first.resolve(strict=False)
    second_resolved = second.resolve(strict=False)
    return _is_relative_to(first_resolved, second_resolved) or _is_relative_to(
        second_resolved, first_resolved
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _render_values(values: Sequence[str]) -> str:
    return ", ".join(values) if values else "none"


def _print_result(result: ProjectInitializationResult) -> None:
    profile_root = getattr(
        result,
        "profile_root",
        getattr(result, "project_root", None),
    )
    profile_file = getattr(
        result,
        "profile_file",
        getattr(result, "project_file", None),
    )

    print(f"Initialized validation profile: {profile_root}")
    print(f"Validation-profile file: {profile_file}")
    print(f"Created files: {len(result.created_files)}")
    for relative_path in result.created_files:
        print(f"  {relative_path.as_posix()}")
    print("Validation-profile check: OK")

    if result.unresolved_placeholders:
        print(
            f"Unresolved placeholders: {len(result.unresolved_placeholders)}",
            file=sys.stderr,
        )
        for placeholder in result.unresolved_placeholders:
            print(f"  {placeholder}", file=sys.stderr)
    else:
        print("Unresolved placeholders: 0")


def _print_error(error: BaseException) -> None:
    if isinstance(error, GFWordbenchError):
        prefix = f"{error.code}: " if error.code else ""
        print(f"{prefix}{error.message}", file=sys.stderr)
        if error.detail:
            print(_bounded(error.detail), file=sys.stderr)
        if error.subject:
            print(f"Subject: {error.subject}", file=sys.stderr)
        return

    print(
        _bounded(str(error) or type(error).__name__),
        file=sys.stderr,
    )


def _bounded(value: str) -> str:
    if len(value) <= _MAX_ERROR_DETAIL:
        return value
    return value[: _MAX_ERROR_DETAIL - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
