from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Final

_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
_DEFAULT_ROOT: Final[Path] = _SCRIPT_PATH.parent.parent
_SOURCE_ROOT: Final[Path] = _DEFAULT_ROOT / "src"
if _SOURCE_ROOT.is_dir() and str(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOURCE_ROOT))
from gf_wordbench.infrastructure.json_io import read_json  # noqa: E402
from gf_wordbench.infrastructure.toml_io import read_toml  # noqa: E402
from gf_wordbench.projects.schema import (  # noqa: E402
    ProjectSchemaCompatibility,
    validate_project_schema,
    validate_project_template_schema,
)
from gf_wordbench.reporting.schemas.manifest_v1 import parse_artifact_manifest  # noqa: E402
from gf_wordbench.reporting.schemas.registry import (  # noqa: E402
    APP_STATE_SCHEMA_ID,
    ARTIFACT_MANIFEST_SCHEMA_ID,
    CANONICAL_SCHEMA_DEFINITIONS,
    PROJECT_SCHEMA_ID,
    RUN_SUMMARY_SCHEMA_ID,
    SCHEMA_REGISTRY,
    SchemaContractClass,
    SchemaDefinition,
    SchemaFormat,
    current_schema,
    normalize_schema_path,
    schema_identity_from_mapping,
)
from gf_wordbench.reporting.schemas.summary_v1 import validate_summary_v1  # noqa: E402
from gf_wordbench.state.schema import parse_app_state  # noqa: E402
from gf_wordbench.validation.scenarios.gold_compare import (  # noqa: E402
    ScenarioTextKind,
    parse_scenario_text,
)

EXIT_OK: Final[int] = 0
EXIT_INVALID: Final[int] = 1
EXIT_USAGE: Final[int] = 2
EXIT_INTERNAL: Final[int] = 3
MAX_FILE_BYTES: Final[int] = 128 * 1024 * 1024
SCENARIO_OUTPUT_SCHEMA_ID: Final[str] = "gf-wordbench.scenario-output"
SCENARIO_GOLD_SCHEMA_ID: Final[str] = "gf-wordbench.scenario-gold"


_PROFILE_TOP_LEVEL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema_id",
        "schema_version",
        "profile",
        "compatibility",
        "selection",
        "modules",
        "validation",
        "release",
    }
)
_PROFILE_TABLE_FIELDS: Final[dict[str, frozenset[str]]] = {
    "profile": frozenset({"id", "name"}),
    "compatibility": frozenset({"expected_language_key"}),
    "selection": frozenset({"include", "exclude"}),
    "modules": frozenset(
        {"required_entrypoints", "release_entrypoints", "checkpoints"}
    ),
    "validation": frozenset({"required_scenarios", "optional_scenarios"}),
    "release": frozenset(
        {"requires_pgf", "pgf_targets", "required_artifacts", "required_gates"}
    ),
}
_PROFILE_STRING_LIST_FIELDS: Final[tuple[tuple[str, str], ...]] = (
    ("selection", "include"),
    ("selection", "exclude"),
    ("modules", "required_entrypoints"),
    ("modules", "release_entrypoints"),
    ("modules", "checkpoints"),
    ("validation", "required_scenarios"),
    ("validation", "optional_scenarios"),
    ("release", "pgf_targets"),
    ("release", "required_artifacts"),
    ("release", "required_gates"),
)
_PROFILE_FORBIDDEN_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "directory",
        "gf_executable",
        "gf_path",
        "language_directory",
        "language_path",
        "output_root",
        "path_parts",
        "rgl_root",
        "rgl_source_root",
        "run_dir",
        "source_root",
        "state_path",
    }
)


@dataclass(frozen=True, slots=True)
class Target:
    path: Path
    definition: SchemaDefinition | None = None
    template_project: bool = False
    enforce_path: bool = False


@dataclass(frozen=True, slots=True)
class Result:
    target: Target
    passed: bool
    schema_key: str
    message: str = ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Validate GF Wordbench persisted schemas without modifying files.")
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=(
            "Schema files or directories. With no paths, discover the active "
            "project, template, state, runs, normalized outputs, and golds."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=_DEFAULT_ROOT,
        help="Repository or workspace root used for discovery.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Require exact current fields, canonical ordering, UTF-8 without "
            "BOM, LF canonical text, and canonical placement."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed validation.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only failures and the final summary.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = absolute(args.root)
    registry_error = validate_registry()
    if registry_error is not None:
        print(f"FAIL registry: {registry_error}", file=sys.stderr)
        return EXIT_INTERNAL
    try:
        targets = (
            discover_targets(root) if not args.paths else explicit_targets(args.paths, root=root)
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"Schema-validator input error: {error_text(exc)}", file=sys.stderr)
        return EXIT_USAGE
    if not targets:
        print("No supported schema files were found.", file=sys.stderr)
        return EXIT_INVALID
    results: list[Result] = []
    for target in targets:
        result = validate_target(target, root=root, strict=args.strict)
        results.append(result)
        if not args.quiet or not result.passed:
            print_result(result, root=root)
        if args.fail_fast and not result.passed:
            break
    passed = sum(result.passed for result in results)
    failed = len(results) - passed
    print(f"Schema check: {passed} passed, {failed} failed, {len(results)} checked.")
    return EXIT_OK if failed == 0 else EXIT_INVALID


def validate_registry() -> str | None:
    try:
        definitions = tuple(SCHEMA_REGISTRY)
        canonical_definitions = tuple(CANONICAL_SCHEMA_DEFINITIONS)

        keys = tuple(definition.qualified_id for definition in definitions)
        if len(keys) != len(set(keys)):
            raise ValueError("registry contains duplicate schema keys")

        canonical_keys = tuple(definition.qualified_id for definition in canonical_definitions)
        if len(canonical_keys) != len(set(canonical_keys)):
            raise ValueError("canonical definitions contain duplicate schema keys")

        registry_by_key = {definition.qualified_id: definition for definition in definitions}
        canonical_by_key = {
            definition.qualified_id: definition for definition in canonical_definitions
        }

        registry_key_set = set(registry_by_key)
        canonical_key_set = set(canonical_by_key)
        if registry_key_set != canonical_key_set:
            missing = sorted(canonical_key_set - registry_key_set)
            unexpected = sorted(registry_key_set - canonical_key_set)
            details: list[str] = []
            if missing:
                details.append(f"missing={missing!r}")
            if unexpected:
                details.append(f"unexpected={unexpected!r}")
            raise ValueError(
                "registry schema keys differ from canonical definitions: " + ", ".join(details)
            )

        for key in sorted(canonical_by_key):
            if registry_by_key[key] != canonical_by_key[key]:
                raise ValueError(f"registry definition differs from canonical definition for {key}")

        for definition in definitions:
            if current_schema(definition.schema_id) != definition:
                raise ValueError(f"current schema mismatch for {definition.schema_id}")
            if (
                definition.contract_class is SchemaContractClass.CANONICAL_ROOT
                and definition.format not in {SchemaFormat.JSON, SchemaFormat.TOML}
            ):
                raise ValueError(f"{definition.qualified_id} has an invalid root format")
            if (
                definition.contract_class is SchemaContractClass.CANONICAL_TEXT
                and definition.newline != "lf"
            ):
                raise ValueError(f"{definition.qualified_id} must require LF newlines")
    except Exception as exc:
        return error_text(exc)
    return None


def discover_targets(root: Path) -> tuple[Target, ...]:
    targets: list[Target] = []

    active_project = root / "project" / "project.toml"
    if active_project.is_file():
        targets.append(
            Target(
                active_project,
                current_schema(PROJECT_SCHEMA_ID),
                enforce_path=True,
            )
        )

    template = root / "templates" / "validation-profile" / "project.toml"
    if template.is_file():
        targets.append(
            Target(
                template,
                current_schema(PROJECT_SCHEMA_ID),
                template_project=True,
                enforce_path=False,
            )
        )
    state = root / ".gf_wordbench_state.json"
    if state.is_file():
        targets.append(
            Target(
                state,
                current_schema(APP_STATE_SCHEMA_ID),
                enforce_path=True,
            )
        )
    for run_root in run_roots(root):
        for name, schema_id in (
            ("summary.json", RUN_SUMMARY_SCHEMA_ID),
            ("manifest.json", ARTIFACT_MANIFEST_SCHEMA_ID),
        ):
            candidate = run_root / name
            if candidate.is_file():
                targets.append(
                    Target(
                        candidate,
                        current_schema(schema_id),
                        enforce_path=True,
                    )
                )
        scenario_root = run_root / "raw" / "scenarios"
        if scenario_root.is_dir():
            targets.extend(
                Target(
                    candidate,
                    text_definition(candidate),
                    enforce_path=True,
                )
                for candidate in sorted(scenario_root.glob("*.out"))
                if candidate.is_file()
            )
    gold_root = root / "project" / "validation" / "gold"
    if gold_root.is_dir():
        targets.extend(
            Target(
                candidate,
                text_definition(candidate),
                enforce_path=True,
            )
            for candidate in sorted(gold_root.glob("*.gold"))
            if candidate.is_file()
        )
    return unique_targets(targets)


def explicit_targets(
    supplied_paths: Iterable[Path],
    *,
    root: Path,
) -> tuple[Target, ...]:
    targets: list[Target] = []
    for supplied in supplied_paths:
        candidate = absolute(supplied if supplied.is_absolute() else root / supplied)
        if not candidate.exists():
            raise FileNotFoundError(candidate)
        if candidate.is_file():
            targets.append(target_from_path(candidate))
        elif candidate.is_dir():
            targets.extend(targets_below(candidate))
        else:
            raise ValueError(f"unsupported filesystem object: {candidate}")
    return unique_targets(targets)


def validate_target(
    target: Target,
    *,
    root: Path,
    strict: bool,
) -> Result:
    definition = target.definition
    schema_key = definition.qualified_id if definition is not None else "auto-detect"
    if not target.path.is_file():
        return Result(
            target,
            False,
            schema_key,
            "required schema file is missing",
        )
    try:
        if target.path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"file exceeds the {MAX_FILE_BYTES}-byte limit")
        if strict:
            validate_encoding(target.path, definition)
        if target.template_project:
            document = read_toml(target.path)
            if _is_optional_profile_document(document):
                validate_optional_profile_schema(
                    document,
                    source=target.path,
                    strict=strict,
                    template=True,
                )
            else:
                validate_project_template_schema(
                    document,
                    source=target.path,
                )
            resolved = current_schema(PROJECT_SCHEMA_ID).qualified_id
        elif definition is None:
            resolved = validate_auto(target.path, strict=strict)
        else:
            resolved = validate_defined(
                target.path,
                definition,
                strict=strict,
            )
            if strict and target.enforce_path:
                require_canonical_placement(
                    target.path,
                    definition,
                    root=root,
                )
    except Exception as exc:
        return Result(
            target,
            False,
            schema_key,
            error_text(exc),
        )
    return Result(target, True, resolved)


def validate_defined(
    path: Path,
    definition: SchemaDefinition,
    *,
    strict: bool,
) -> str:
    if definition.format is SchemaFormat.TOML:
        toml_document = read_toml(path)
        if _is_optional_profile_document(toml_document):
            validate_optional_profile_schema(
                toml_document,
                source=path,
                strict=strict,
                template=False,
            )
        else:
            validate_project_schema(
                toml_document,
                source=path,
                compatibility=(
                    ProjectSchemaCompatibility.STRICT
                    if strict
                    else ProjectSchemaCompatibility.FORWARD_MINOR
                ),
            )
        return definition.qualified_id
    if definition.format is SchemaFormat.JSON:
        json_document = read_json(path, max_bytes=MAX_FILE_BYTES)
        identity = schema_identity_from_mapping(json_document)
        if identity.schema_id != definition.schema_id:
            raise ValueError(
                f"expected schema_id {definition.schema_id!r}, received {identity.schema_id!r}"
            )
        validate_json(
            path,
            json_document,
            schema_id=identity.schema_id,
            strict=strict,
        )
        return str(identity)
    kind = ScenarioTextKind.GOLD if path.suffix.casefold() == ".gold" else ScenarioTextKind.OUTPUT
    parse_scenario_text(path.read_text(encoding="utf-8"), kind=kind)
    return definition.qualified_id


def validate_auto(path: Path, *, strict: bool) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".toml":
        return validate_defined(
            path,
            current_schema(PROJECT_SCHEMA_ID),
            strict=strict,
        )
    if suffix in {".gold", ".out"}:
        return validate_defined(
            path,
            text_definition(path),
            strict=strict,
        )
    if suffix != ".json":
        raise ValueError(f"unsupported schema file type: {suffix or '<none>'}")
    document = read_json(path, max_bytes=MAX_FILE_BYTES)
    identity = schema_identity_from_mapping(document)
    validate_json(
        path,
        document,
        schema_id=identity.schema_id,
        strict=strict,
    )
    return str(identity)


def _is_optional_profile_document(document: object) -> bool:
    return isinstance(document, Mapping) and "profile" in document


def validate_optional_profile_schema(
    document: object,
    *,
    source: Path,
    strict: bool,
    template: bool,
) -> None:
    if not isinstance(document, Mapping):
        raise TypeError(f"{source}: validation profile must be a TOML table")

    _require_exact_schema_identity(document, source=source)
    _reject_forbidden_profile_fields(document, source=source)

    if strict:
        _reject_unknown_fields(
            document,
            allowed=_PROFILE_TOP_LEVEL_FIELDS,
            path="$",
            source=source,
        )

    tables: dict[str, Mapping[str, object]] = {}
    for table_name, allowed_fields in _PROFILE_TABLE_FIELDS.items():
        raw_table = document.get(table_name)
        if not isinstance(raw_table, Mapping):
            raise TypeError(f"{source}: $.{table_name} must be a TOML table")
        tables[table_name] = raw_table
        if strict:
            _reject_unknown_fields(
                raw_table,
                allowed=allowed_fields,
                path=f"$.{table_name}",
                source=source,
            )

    profile_id = _require_profile_string(
        tables["profile"], "id", path="$.profile.id", source=source
    )
    profile_name = _require_profile_string(
        tables["profile"], "name", path="$.profile.name", source=source
    )
    if template:
        if profile_id != "<PROFILE_ID>" or profile_name != "<PROFILE_NAME>":
            raise ValueError(
                f"{source}: template profile identity must use <PROFILE_ID> and <PROFILE_NAME>"
            )
    elif _is_placeholder(profile_id) or _is_placeholder(profile_name):
        raise ValueError(f"{source}: active validation profile contains unresolved placeholders")

    compatibility_key = tables["compatibility"].get("expected_language_key")
    if not isinstance(compatibility_key, str):
        raise TypeError(
            f"{source}: $.compatibility.expected_language_key must be a string"
        )
    _validate_profile_text(
        compatibility_key,
        path="$.compatibility.expected_language_key",
        source=source,
        allow_empty=True,
    )

    for table_name, field_name in _PROFILE_STRING_LIST_FIELDS:
        _require_unique_string_list(
            tables[table_name],
            field_name,
            path=f"$.{table_name}.{field_name}",
            source=source,
        )

    requires_pgf = tables["release"].get("requires_pgf")
    if type(requires_pgf) is not bool:
        raise TypeError(f"{source}: $.release.requires_pgf must be a Boolean")


def _require_exact_schema_identity(
    document: Mapping[str, object],
    *,
    source: Path,
) -> None:
    schema_id = document.get("schema_id")
    schema_version = document.get("schema_version")
    if schema_id != PROJECT_SCHEMA_ID:
        raise ValueError(
            f"{source}: $.schema_id: expected {PROJECT_SCHEMA_ID!r}, received {schema_id!r}"
        )
    expected_version = str(current_schema(PROJECT_SCHEMA_ID).version)
    if schema_version != expected_version:
        raise ValueError(
            f"{source}: $.schema_version: expected {expected_version!r}, "
            f"received {schema_version!r}"
        )


def _reject_forbidden_profile_fields(
    document: Mapping[str, object],
    *,
    source: Path,
) -> None:
    pending: list[tuple[str, Mapping[str, object]]] = [("$", document)]
    while pending:
        path, table = pending.pop()
        for raw_key, value in table.items():
            key = str(raw_key)
            field_path = f"{path}.{key}"
            if key in _PROFILE_FORBIDDEN_FIELDS:
                raise ValueError(
                    f"{source}: {field_path} is owned by ResolvedLanguageContext "
                    "or local environment configuration, not by a validation profile"
                )
            if isinstance(value, Mapping):
                pending.append((field_path, value))


def _reject_unknown_fields(
    table: Mapping[str, object],
    *,
    allowed: frozenset[str],
    path: str,
    source: Path,
) -> None:
    unknown = sorted(str(key) for key in table if str(key) not in allowed)
    if unknown:
        raise ValueError(f"{source}: {path} contains unknown fields: {', '.join(unknown)}")


def _require_profile_string(
    table: Mapping[str, object],
    field: str,
    *,
    path: str,
    source: Path,
) -> str:
    value = table.get(field)
    if not isinstance(value, str):
        raise TypeError(f"{source}: {path} must be a string")
    _validate_profile_text(value, path=path, source=source, allow_empty=False)
    return value


def _validate_profile_text(
    value: str,
    *,
    path: str,
    source: Path,
    allow_empty: bool,
) -> None:
    if "\x00" in value:
        raise ValueError(f"{source}: {path} must not contain NUL characters")
    if value != value.strip():
        raise ValueError(f"{source}: {path} must not contain surrounding whitespace")
    if not allow_empty and not value:
        raise ValueError(f"{source}: {path} must not be empty")


def _require_unique_string_list(
    table: Mapping[str, object],
    field: str,
    *,
    path: str,
    source: Path,
) -> tuple[str, ...]:
    value = table.get(field)
    if not isinstance(value, list):
        raise TypeError(f"{source}: {path} must be an array of strings")
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise TypeError(f"{source}: {path}[{index}] must be a string")
        _validate_profile_text(
            item,
            path=f"{path}[{index}]",
            source=source,
            allow_empty=False,
        )
        items.append(item)
    if len(items) != len(set(items)):
        raise ValueError(f"{source}: {path} must not contain duplicate values")
    return tuple(items)


def _is_placeholder(value: str) -> bool:
    return len(value) >= 3 and value.startswith("<") and value.endswith(">")

def validate_json(
    path: Path,
    document: object,
    *,
    schema_id: str,
    strict: bool,
) -> None:
    if schema_id == APP_STATE_SCHEMA_ID:
        parse_app_state(document, strict=strict, source=path)
        return
    if schema_id == RUN_SUMMARY_SCHEMA_ID:
        issues = validate_summary_v1(
            document,
            strict=strict,
            check_ordering=strict,
        )
        if issues:
            preview = "; ".join(
                f"{issue.path} [{issue.code}]: {issue.message}" for issue in issues[:12]
            )
            if len(issues) > 12:
                preview += f"; and {len(issues) - 12} more"
            raise ValueError(preview)
        return
    if schema_id == ARTIFACT_MANIFEST_SCHEMA_ID:
        parse_artifact_manifest(document, strict=strict)
        return
    if schema_id == PROJECT_SCHEMA_ID:
        raise ValueError("project schema is TOML, not JSON")
    raise ValueError(f"unsupported schema_id {schema_id!r}")


def targets_below(directory: Path) -> tuple[Target, ...]:
    return tuple(
        target_from_path(candidate)
        for candidate in sorted(directory.rglob("*"))
        if candidate.is_file() and supported_path(candidate)
    )


def target_from_path(path: Path) -> Target:
    name = path.name.casefold()
    if name == "project.toml":
        template = "templates" in {part.casefold() for part in path.parts}
        return Target(
            path,
            current_schema(PROJECT_SCHEMA_ID),
            template_project=template,
        )
    if name == ".gf_wordbench_state.json":
        return Target(path, current_schema(APP_STATE_SCHEMA_ID))
    if name == "summary.json":
        return Target(path, current_schema(RUN_SUMMARY_SCHEMA_ID))
    if name == "manifest.json":
        return Target(
            path,
            current_schema(ARTIFACT_MANIFEST_SCHEMA_ID),
        )
    if path.suffix.casefold() in {".gold", ".out"}:
        return Target(path, text_definition(path))
    return Target(path)


def text_definition(path: Path) -> SchemaDefinition:
    schema_id = (
        SCENARIO_GOLD_SCHEMA_ID if path.suffix.casefold() == ".gold" else SCENARIO_OUTPUT_SCHEMA_ID
    )
    return current_schema(schema_id)


def require_canonical_placement(
    path: Path,
    definition: SchemaDefinition,
    *,
    root: Path,
) -> None:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        return
    if definition.matches_path(relative):
        return
    if definition.schema_id in {
        RUN_SUMMARY_SCHEMA_ID,
        ARTIFACT_MANIFEST_SCHEMA_ID,
        SCENARIO_OUTPUT_SCHEMA_ID,
    }:
        parts = relative.split("/")
        for index, part in enumerate(parts):
            if part.startswith("run_"):
                candidate = "/".join(parts[index:])
                if definition.matches_path(candidate):
                    return
    raise ValueError(
        f"file is not stored at its canonical schema path: {normalize_schema_path(relative)!r}"
    )


def validate_encoding(
    path: Path,
    definition: SchemaDefinition | None,
) -> None:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("canonical files must be UTF-8 without BOM")
    data.decode("utf-8")
    if definition is not None and definition.contract_class is SchemaContractClass.CANONICAL_TEXT:
        if b"\r" in data:
            raise ValueError("canonical text must use LF newlines")
        if data and not data.endswith(b"\n"):
            raise ValueError("canonical text must end with a newline")


def run_roots(root: Path) -> tuple[Path, ...]:
    candidates = list(root.glob("run_*"))
    legacy_root = root / "runs"
    if legacy_root.is_dir():
        candidates.extend(legacy_root.glob("run_*"))
    return tuple(
        sorted(
            {candidate.resolve(strict=False) for candidate in candidates if candidate.is_dir()},
            key=lambda candidate: candidate.as_posix().casefold(),
        )
    )


def supported_path(path: Path) -> bool:
    return path.name.casefold() in {
        "project.toml",
        ".gf_wordbench_state.json",
        "summary.json",
        "manifest.json",
    } or path.suffix.casefold() in {".gold", ".out"}


def unique_targets(targets: Iterable[Target]) -> tuple[Target, ...]:
    selected: dict[str, Target] = {}
    for target in targets:
        key = str(target.path.resolve(strict=False)).casefold()
        selected.setdefault(key, target)
    return tuple(
        sorted(
            selected.values(),
            key=lambda target: target.path.as_posix().casefold(),
        )
    )


def print_result(result: Result, *, root: Path) -> None:
    try:
        display = result.target.path.relative_to(root).as_posix()
    except ValueError:
        display = str(result.target.path)
    stream = sys.stdout if result.passed else sys.stderr
    status = "OK" if result.passed else "FAIL"
    print(f"{status} {display} [{result.schema_key}]", file=stream)
    if result.message:
        print(f"  {result.message}", file=stream)


def absolute(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def error_text(exc: BaseException) -> str:
    message = str(exc).strip() or type(exc).__name__
    return f"{type(exc).__name__}: {message}"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Schema validation cancelled.", file=sys.stderr)
        raise SystemExit(130) from None
    except SystemExit:
        raise
    except Exception as exc:
        print(
            f"Internal schema-validator error: {error_text(exc)}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_INTERNAL) from exc
