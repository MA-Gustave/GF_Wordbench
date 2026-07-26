"""Initialize one active GF Wordbench project from the canonical template."""

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

_PROJECT_DIRECTORY: Final[str] = "project"
_PROJECT_FILENAME: Final[str] = "project.toml"
_STAGE_DIRECTORY: Final[str] = ".gf-wordbench-project-init-stage"
_ROLLBACK_DIRECTORY: Final[str] = ".gf-wordbench-project-init-rollback"
_TEMPLATE_DIRECTORY: Final[PurePosixPath] = PurePosixPath("templates/project")
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
    workspace_root: Path
    config_file: Path
    source_tree: Path
    replacements: Mapping[str, str]
    strict_placeholders: bool
    allow_existing_empty_project: bool


@dataclass(frozen=True, slots=True)
class _FilesystemTemplateSource:
    """Materialize the canonical template plus one explicitly supplied source tree."""

    root: Path
    source_tree: Path
    source_destination: PurePosixPath
    filesystem: ProjectFilesystem

    def __post_init__(self) -> None:
        root = self.filesystem.resolve(self.root)
        source_tree = self.filesystem.resolve(self.source_tree)
        destination = _portable_relative_path(
            self.source_destination,
            field="source destination",
        )

        if not self.filesystem.is_directory(root):
            raise _ArgumentError(f"canonical project template is missing: {root}")
        if not self.filesystem.is_directory(source_tree):
            raise _ArgumentError(f"source tree is not a directory: {source_tree}")
        if _paths_overlap(root, source_tree):
            raise _ArgumentError("source tree must not overlap the canonical template")

        object.__setattr__(self, "root", root)
        object.__setattr__(self, "source_tree", source_tree)
        object.__setattr__(self, "source_destination", destination)

        self.inventory()

    def inventory(self) -> tuple[TreeEntry, ...]:
        template_entries = self.filesystem.inspect_tree(self.root)
        source_entries = self.filesystem.inspect_tree(self.source_tree)

        entries: dict[PurePosixPath, TreeEntry] = {}
        for entry in template_entries:
            _register_entry(entries, entry)

        for parent in _destination_directories(self.source_destination):
            _register_entry(
                entries,
                TreeEntry(relative_path=Path(parent.as_posix()), kind=TreeEntryKind.DIRECTORY),
                allow_matching_directory=True,
            )

        for entry in source_entries:
            prefixed = self.source_destination / PurePosixPath(entry.relative_path.as_posix())
            _register_entry(
                entries,
                TreeEntry(
                    relative_path=Path(prefixed.as_posix()),
                    kind=entry.kind,
                    size_bytes=entry.size_bytes,
                    link_target=entry.link_target,
                ),
            )

        return tuple(entries[path] for path in sorted(entries, key=PurePosixPath.as_posix))

    def materialize(
        self,
        destination: Path,
        *,
        replacements: Mapping[str, str],
    ) -> None:
        stage_root = self.filesystem.resolve(destination)
        self.filesystem.copy_tree(self.root, stage_root)

        try:
            source_destination = stage_root.joinpath(*self.source_destination.parts)
            source_destination.parent.mkdir(parents=True, exist_ok=True)
            self.filesystem.copy_tree(self.source_tree, source_destination)
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
    """Adapt a typed project configuration to the canonical TOML transport."""

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
            "Initialize project/ from templates/project/ using an explicit canonical "
            "project TOML document and an explicit GF source tree."
        ),
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=_REPOSITORY_ROOT,
        help="GF Wordbench repository root (default: repository containing this script).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="TOML file containing the final canonical project configuration.",
    )
    parser.add_argument(
        "--source-tree",
        type=Path,
        required=True,
        help=(
            "Existing GF source directory copied into the configured "
            "sources.directory inside project/."
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
        "--allow-existing-empty-project",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Permit replacement only when project/ exists and is empty (default: enabled).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        namespace = build_parser().parse_args(argv)
        arguments = _arguments_from_namespace(namespace)
        result = _initialize(arguments)
    except SystemExit as error:
        return int(error.code)
    except KeyboardInterrupt:
        print("Project initialization cancelled.", file=sys.stderr)
        return EXIT_CANCELLED
    except (_ArgumentError, ConfigurationError, FileNotFoundError, NotADirectoryError) as error:
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
    workspace_root = _absolute_normalized(namespace.workspace_root)
    config_file = _absolute_normalized(namespace.config, base=Path.cwd())
    source_tree = _absolute_normalized(namespace.source_tree, base=Path.cwd())

    strict_placeholders = namespace.strict_placeholders
    allow_existing_empty_project = namespace.allow_existing_empty_project
    if type(strict_placeholders) is not bool:
        raise _ArgumentError("--strict-placeholders must be boolean")
    if type(allow_existing_empty_project) is not bool:
        raise _ArgumentError("--allow-existing-empty-project must be boolean")

    replacements = _parse_replacements(namespace.replacement_values)
    return _Arguments(
        workspace_root=workspace_root,
        config_file=config_file,
        source_tree=source_tree,
        replacements=replacements,
        strict_placeholders=strict_placeholders,
        allow_existing_empty_project=allow_existing_empty_project,
    )


def _initialize(arguments: _Arguments) -> ProjectInitializationResult:
    _validate_repository(arguments.workspace_root)

    filesystem = ProjectFilesystemAdapter()
    workspace_root = filesystem.resolve(arguments.workspace_root)
    template_root = filesystem.resolve(
        workspace_root.joinpath(*_TEMPLATE_DIRECTORY.parts)
    )
    project_root = filesystem.resolve(workspace_root / _PROJECT_DIRECTORY)
    stage_root = filesystem.resolve(workspace_root / _STAGE_DIRECTORY)
    rollback_root = filesystem.resolve(workspace_root / _ROLLBACK_DIRECTORY)
    project_file = project_root / _PROJECT_FILENAME

    _validate_external_inputs(
        config_file=arguments.config_file,
        source_tree=arguments.source_tree,
        protected_roots=(template_root, project_root, stage_root, rollback_root),
    )
    config = _load_initialization_config(arguments.config_file, project_file=project_file)
    replacements = _automatic_replacements(config) | dict(arguments.replacements)

    template_source: ProjectTemplateSource = _FilesystemTemplateSource(
        root=template_root,
        source_tree=arguments.source_tree,
        source_destination=PurePosixPath(config.sources.directory.as_posix()),
        filesystem=filesystem,
    )
    config_writer: ProjectConfigWriter = _TomlProjectConfigWriter()

    request = ProjectInitializationRequest(
        workspace_root=workspace_root,
        config=config,
        template_values=replacements,
        require_resolved_placeholders=arguments.strict_placeholders,
        allow_existing_empty_project=arguments.allow_existing_empty_project,
    )
    return initialize_project(
        request,
        template_source=template_source,
        filesystem=filesystem,
        config_writer=config_writer,
    )


def _validate_external_inputs(
    *,
    config_file: Path,
    source_tree: Path,
    protected_roots: Sequence[Path],
) -> None:
    for protected_root in protected_roots:
        if _paths_overlap(source_tree, protected_root):
            raise _ArgumentError(
                f"source tree overlaps a protected initialization path: {protected_root}"
            )
        if _is_relative_to(config_file, protected_root):
            raise _ArgumentError(
                f"initialization config must remain outside protected path: {protected_root}"
            )


def _load_initialization_config(
    config_file: Path,
    *,
    project_file: Path,
) -> ProjectConfig:
    if not config_file.is_file():
        raise FileNotFoundError(f"initialization config not found: {config_file}")

    document = read_project_toml(config_file)
    validated = validate_project_schema(document, source=config_file)
    return parse_project_document(
        ProjectDocument(**validated),
        source_file=project_file,
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
            "release_requires_pgf": config.validation.release_requires_pgf,
        },
    )


def _automatic_replacements(config: ProjectConfig) -> dict[str, str]:
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


def _validate_repository(workspace_root: Path) -> None:
    required = (
        workspace_root / "pyproject.toml",
        workspace_root.joinpath(*_TEMPLATE_DIRECTORY.parts, _PROJECT_FILENAME),
        workspace_root.joinpath(*_SOURCE_DIRECTORY.parts),
    )
    missing = tuple(path for path in required if not path.exists())
    if missing:
        rendered = ", ".join(os.fspath(path) for path in missing)
        raise _ArgumentError(f"workspace is not a complete GF Wordbench repository: {rendered}")


def _register_entry(
    entries: dict[PurePosixPath, TreeEntry],
    entry: TreeEntry,
    *,
    allow_matching_directory: bool = False,
) -> None:
    path = _portable_relative_path(
        PurePosixPath(entry.relative_path.as_posix()),
        field="template inventory path",
    )
    existing = entries.get(path)
    if existing is None:
        entries[path] = entry
        return
    if (
        allow_matching_directory
        and existing.kind is TreeEntryKind.DIRECTORY
        and entry.kind is TreeEntryKind.DIRECTORY
    ):
        return
    raise _ArgumentError(f"source tree conflicts with project template path: {path}")


def _destination_directories(destination: PurePosixPath) -> tuple[PurePosixPath, ...]:
    directories: list[PurePosixPath] = []
    current = PurePosixPath()
    for part in destination.parts:
        current /= part
        directories.append(current)
    return tuple(directories)


def _portable_relative_path(value: PurePosixPath, *, field: str) -> PurePosixPath:
    rendered = value.as_posix()
    if (
        value.is_absolute()
        or rendered in {"", "."}
        or "\\" in rendered
        or "\x00" in rendered
        or any(part in {"", ".", ".."} for part in value.parts)
    ):
        raise _ArgumentError(f"{field} must be a safe portable relative path")
    return value


def _absolute_normalized(value: Path, *, base: Path | None = None) -> Path:
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
        second_resolved,
        first_resolved,
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
    print(f"Initialized project: {result.project_root}")
    print(f"Project file: {result.project_file}")
    print(f"Created files: {len(result.created_files)}")
    for relative_path in result.created_files:
        print(f"  {relative_path.as_posix()}")
    print("Project check: OK")

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
    print(_bounded(str(error) or type(error).__name__), file=sys.stderr)


def _bounded(value: str) -> str:
    if len(value) <= _MAX_ERROR_DETAIL:
        return value
    return value[: _MAX_ERROR_DETAIL - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
