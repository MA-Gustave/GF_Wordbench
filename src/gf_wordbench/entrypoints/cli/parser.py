"""Canonical command-line parser for GF Wordbench."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
import re
from types import MappingProxyType
from typing import Final, Never, TypeAlias, cast

from gf_wordbench.config.defaults import DEFAULT_VALIDATION_MODE
from gf_wordbench.kernel.ids import validate_scenario_id
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.version import __version__

_APP_NAME: Final[str] = "GF Wordbench"
_PROG: Final[str] = "gf-wordbench"
_CANONICAL_MODES: Final[tuple[str, ...]] = tuple(mode.value for mode in ValidationMode)
_LEGACY_MODE_ALIASES: Final[Mapping[str, ValidationMode]] = MappingProxyType(
    {
        "file": ValidationMode.QUICK,
        "all": ValidationMode.DIAGNOSTIC,
    }
)
_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_MAX_ARGUMENT_TEXT: Final[int] = 32_768
_MAX_REPEATABLE_VALUES: Final[int] = 10_000

ArgumentValue: TypeAlias = object


@unique
class CliCommand(StrEnum):
    LANGUAGE_PROBE = "language.probe"
    VALIDATE = "validate"
    PROJECT_CHECK = "project.check"
    SCENARIOS_CHECK = "scenarios.check"
    GOLD_UPDATE = "gold.update"
    SCHEMAS_CHECK = "schemas.check"
    REPORTS_CHECK = "reports.check"


class CliUsageError(ValueError):
    """Invalid command-line syntax or an invalid local option combination."""

    __slots__ = ("usage",)

    def __init__(self, message: str, *, usage: str | None = None) -> None:
        super().__init__(message)
        self.usage = usage


class CliArgumentParser(argparse.ArgumentParser):
    """Argument parser that reports usage errors to the CLI application layer."""

    def error(self, message: str) -> Never:
        raise CliUsageError(message, usage=self.format_usage().rstrip())


@dataclass(frozen=True, slots=True)
class CliRequest:
    """Normalized command-line request containing only canonical values."""

    command: CliCommand
    arguments: Mapping[str, ArgumentValue]
    compatibility_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.command, CliCommand):
            raise TypeError("command must be CliCommand")
        if not isinstance(self.arguments, Mapping):
            raise TypeError("arguments must be a mapping")

        frozen: dict[str, ArgumentValue] = {}
        for key, value in self.arguments.items():
            if not isinstance(key, str) or not key or key.startswith("_"):
                raise ValueError("argument names must be public non-empty strings")
            frozen[key] = _freeze_argument_value(value)

        warnings = tuple(self.compatibility_warnings)
        for warning in warnings:
            _require_text(warning, field="compatibility warning")

        object.__setattr__(self, "arguments", MappingProxyType(frozen))
        object.__setattr__(self, "compatibility_warnings", warnings)

    def get(self, name: str, default: ArgumentValue = None) -> ArgumentValue:
        return self.arguments.get(name, default)

    def require(self, name: str) -> ArgumentValue:
        try:
            return self.arguments[name]
        except KeyError as exc:
            raise KeyError(f"CLI request has no argument {name!r}") from exc

    def as_dict(self) -> dict[str, ArgumentValue]:
        return dict(self.arguments)

    @property
    def validation_profile_overrides(self) -> Mapping[str, ArgumentValue]:
        """Return immutable migration-only validation-profile overrides."""

        value = self.arguments.get("legacy_overrides", MappingProxyType({}))
        if not isinstance(value, Mapping):
            raise TypeError("legacy_overrides must be a mapping")
        return cast("Mapping[str, ArgumentValue]", value)

    @property
    def project_overrides(self) -> Mapping[str, ArgumentValue]:
        """Return migration-only legacy project overrides.

        The canonical path-resolved startup model does not use these values as
        language authority. The property remains available while legacy CLI
        inputs are migrated by the application layer.
        """

        return self.validation_profile_overrides


def build_parser(*, prog: str = _PROG) -> CliArgumentParser:
    """Build the canonical parser without reading configuration or the filesystem."""

    parser = CliArgumentParser(
        prog=prog,
        description=(
            "Open one Grammatical Framework language path, then validate, "
            "diagnose, compare, or assess its configured release policy."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{_APP_NAME} {__version__}",
    )

    commands = parser.add_subparsers(
        dest="_command_group",
        metavar="COMMAND",
        required=True,
    )

    _add_language_parser(commands)
    _add_validate_parser(commands)
    _add_project_parser(commands)
    _add_scenarios_parser(commands)
    _add_gold_parser(commands)
    _add_schemas_parser(commands)
    _add_reports_parser(commands)
    return parser


def parse_cli_namespace(
    argv: Sequence[str] | None = None,
    *,
    prog: str = _PROG,
) -> argparse.Namespace:
    """Parse and normalize command-line values while retaining an internal namespace."""

    parser = build_parser(prog=prog)
    try:
        namespace = parser.parse_args(argv)
    except argparse.ArgumentError as exc:
        raise CliUsageError(str(exc), usage=parser.format_usage().rstrip()) from exc
    return _normalize_namespace(namespace, parser)


def parse_cli_request(
    argv: Sequence[str] | None = None,
    *,
    prog: str = _PROG,
) -> CliRequest:
    """Parse one invocation into a canonical immutable CLI request."""

    namespace = parse_cli_namespace(argv, prog=prog)
    command = cast("CliCommand", namespace._command)
    warnings = tuple(namespace._compatibility_warnings)
    values = {key: value for key, value in vars(namespace).items() if not key.startswith("_")}
    return CliRequest(
        command=command,
        arguments=values,
        compatibility_warnings=warnings,
    )


def parse_args(
    argv: Sequence[str] | None = None,
    *,
    prog: str = _PROG,
) -> CliRequest:
    """Compatibility-neutral alias for the canonical request parser."""

    return parse_cli_request(argv, prog=prog)


def _add_language_parser(
    commands: argparse._SubParsersAction[CliArgumentParser],
) -> None:
    language = commands.add_parser(
        "language",
        help="path-resolved language startup operations",
        allow_abbrev=False,
    )
    actions = language.add_subparsers(
        dest="_language_action",
        metavar="ACTION",
        required=True,
    )
    probe = actions.add_parser(
        "probe",
        help="resolve one GF language directory or .gf file",
        description=(
            "Resolve one explicit GF language path through the shared "
            "path-resolved startup service without starting a validation run."
        ),
        allow_abbrev=False,
    )
    probe.set_defaults(_command=CliCommand.LANGUAGE_PROBE)
    probe.add_argument(
        "language_path",
        type=_path_value,
        metavar="LANGUAGE-PATH",
        help="GF language directory or .gf file",
    )
    probe.add_argument(
        "--profile",
        "--validation-profile",
        dest="validation_profile",
        type=_path_value,
        default=None,
        metavar="PATH",
        help="optional explicit validation profile",
    )
    probe.add_argument(
        "--probe-gf",
        "--verify-gf",
        "--verify-with-gf",
        dest="probe_gf",
        action="store_true",
        help="request capability verification through the normal GF boundary",
    )
    probe.add_argument("--strict", action="store_true")
    _add_verbosity_options(probe)
    _add_environment_paths(probe, include_output=False)


def _add_validate_parser(commands: argparse._SubParsersAction[CliArgumentParser]) -> None:
    parser = commands.add_parser(
        "validate",
        help="run validation and create one complete run directory",
        description="Run GF Wordbench validation through the shared application service.",
        allow_abbrev=False,
    )
    parser.set_defaults(_command=CliCommand.VALIDATE)
    _add_language_selection_options(parser, allow_last_language=True)
    parser.add_argument(
        "--profile",
        "--validation-profile",
        dest="validation_profile",
        type=_path_value,
        default=None,
        metavar="PATH",
        help="optional explicit validation profile",
    )
    parser.add_argument(
        "--mode",
        choices=(*_CANONICAL_MODES, *_LEGACY_MODE_ALIASES),
        default=None,
        help="validation policy mode",
    )
    parser.add_argument("--target", type=_path_value, default=None, metavar="PATH")
    parser.add_argument("--checkpoint", type=_canonical_id, default=None, metavar="ID")
    parser.add_argument(
        "--scenario",
        dest="scenario_ids",
        action="append",
        type=_scenario_id,
        default=None,
        metavar="ID",
        help="registered scenario ID; repeat to select multiple scenarios",
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-version-probe", action="store_true", default=None)
    parser.add_argument("--no-compile", action="store_true", default=None)
    parser.add_argument(
        "--compile-timeout",
        type=_positive_int,
        default=None,
        metavar="SECONDS",
    )
    parser.add_argument(
        "--scenario-timeout",
        type=_positive_int,
        default=None,
        metavar="SECONDS",
    )
    parser.add_argument(
        "--pgf-timeout",
        type=_positive_int,
        default=None,
        metavar="SECONDS",
    )
    parser.add_argument("--max-files", type=_nonnegative_int, default=None, metavar="COUNT")
    parser.add_argument("--cpu-stats", action="store_true", default=None)
    parser.add_argument("--keep-ok-details", action="store_true", default=None)

    comparison = parser.add_mutually_exclusive_group()
    comparison.add_argument(
        "--compare-previous",
        dest="compare_previous",
        action="store_const",
        const=True,
        default=None,
    )
    comparison.add_argument(
        "--no-compare-previous",
        dest="compare_previous",
        action="store_const",
        const=False,
    )
    parser.add_argument("--baseline", type=_path_value, default=None, metavar="PATH")

    _add_verbosity_options(parser)
    _add_environment_paths(parser, include_output=True)
    _add_legacy_project_root_option(parser)
    _add_validate_legacy_options(parser)


def _add_project_parser(commands: argparse._SubParsersAction[CliArgumentParser]) -> None:
    project = commands.add_parser(
        "project",
        help="explicit validation-profile contract operations",
        allow_abbrev=False,
    )
    actions = project.add_subparsers(dest="_project_action", metavar="ACTION", required=True)
    check = actions.add_parser(
        "check",
        help="validate one explicit validation profile without running validation",
        allow_abbrev=False,
    )
    check.set_defaults(_command=CliCommand.PROJECT_CHECK)
    check.add_argument("--strict", action="store_true")
    check.add_argument(
        "--probe-gf",
        "--verify-with-gf",
        dest="probe_gf",
        action="store_true",
    )
    _add_language_selection_options(check, allow_last_language=False)
    check.add_argument(
        "--profile",
        "--validation-profile",
        dest="validation_profile",
        type=_path_value,
        default=None,
        metavar="PATH",
        help="explicit validation profile to check",
    )
    _add_verbosity_options(check)
    _add_environment_paths(check, include_output=False)
    _add_legacy_project_root_option(check)


def _add_scenarios_parser(commands: argparse._SubParsersAction[CliArgumentParser]) -> None:
    scenarios = commands.add_parser(
        "scenarios",
        help="registered scenario contract operations",
        allow_abbrev=False,
    )
    actions = scenarios.add_subparsers(
        dest="_scenarios_action",
        metavar="ACTION",
        required=True,
    )
    check = actions.add_parser(
        "check",
        help="validate registered scenario contracts without executing GF",
        allow_abbrev=False,
    )
    check.set_defaults(_command=CliCommand.SCENARIOS_CHECK)
    check.add_argument("--strict", action="store_true")
    check.add_argument(
        "--scenario",
        dest="scenario_ids",
        action="append",
        type=_scenario_id,
        default=None,
        metavar="ID",
    )
    _add_language_selection_options(check, allow_last_language=True)
    check.add_argument(
        "--profile",
        dest="validation_profile",
        type=_path_value,
        default=None,
        metavar="PATH",
        help="explicit profile owning the scenario registry",
    )
    _add_verbosity_options(check)
    _add_legacy_project_root_option(check)


def _add_gold_parser(commands: argparse._SubParsersAction[CliArgumentParser]) -> None:
    gold = commands.add_parser(
        "gold",
        help="reviewed gold-output operations",
        allow_abbrev=False,
    )
    actions = gold.add_subparsers(dest="_gold_action", metavar="ACTION", required=True)
    update = actions.add_parser(
        "update",
        help="regenerate reviewed expected output for selected scenarios",
        allow_abbrev=False,
    )
    update.set_defaults(_command=CliCommand.GOLD_UPDATE)
    update.add_argument(
        "scenario_ids",
        nargs="*",
        type=_scenario_id,
        metavar="SCENARIO-ID",
    )
    update.add_argument("--all", dest="all_scenarios", action="count", default=0)
    update.add_argument("--yes", action="store_true")
    update.add_argument("--strict", action="store_true")
    update.add_argument("--show-diff", action="store_true")
    update.add_argument(
        "--scenario-timeout",
        type=_positive_int,
        default=None,
        metavar="SECONDS",
    )
    _add_language_selection_options(update, allow_last_language=True)
    update.add_argument(
        "--profile",
        dest="validation_profile",
        type=_path_value,
        default=None,
        metavar="PATH",
        help="explicit profile owning the selected gold contracts",
    )
    _add_verbosity_options(update)
    _add_environment_paths(update, include_output=True)
    _add_legacy_project_root_option(update)


def _add_schemas_parser(commands: argparse._SubParsersAction[CliArgumentParser]) -> None:
    schemas = commands.add_parser(
        "schemas",
        help="persisted-schema operations",
        allow_abbrev=False,
    )
    actions = schemas.add_subparsers(
        dest="_schemas_action",
        metavar="ACTION",
        required=True,
    )
    check = actions.add_parser(
        "check",
        help="validate persisted GF Wordbench assets",
        allow_abbrev=False,
    )
    check.set_defaults(_command=CliCommand.SCHEMAS_CHECK)
    check.add_argument("paths", nargs="+", type=_path_value, metavar="PATH")
    check.add_argument("--strict", action="store_true")
    check.add_argument("--recursive", action="store_true")
    _add_verbosity_options(check)
    check.add_argument("--project-root", type=_path_value, default=None, metavar="PATH")


def _add_reports_parser(commands: argparse._SubParsersAction[CliArgumentParser]) -> None:
    reports = commands.add_parser(
        "reports",
        help="completed-run report and integrity operations",
        allow_abbrev=False,
    )
    actions = reports.add_subparsers(
        dest="_reports_action",
        metavar="ACTION",
        required=True,
    )
    check = actions.add_parser(
        "check",
        help="verify consistency and integrity of one run directory",
        allow_abbrev=False,
    )
    check.set_defaults(_command=CliCommand.REPORTS_CHECK)
    check.add_argument("run_dir", type=_path_value, metavar="RUN-DIR")
    check.add_argument("--strict", action="store_true")
    check.add_argument("--verify-hashes", action="store_true")
    _add_verbosity_options(check)


def _add_language_selection_options(
    parser: argparse.ArgumentParser,
    *,
    allow_last_language: bool,
) -> None:
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--language-path",
        type=_path_value,
        default=None,
        metavar="PATH",
        help="GF language directory or .gf file",
    )
    if allow_last_language:
        selection.add_argument(
            "--last-language",
            dest="use_last_language",
            action="store_true",
            default=False,
            help="revalidate and use the last selected language path",
        )
    else:
        parser.set_defaults(use_last_language=False)


def _add_environment_paths(
    parser: argparse.ArgumentParser,
    *,
    include_output: bool,
) -> None:
    parser.add_argument(
        "--gf-exe",
        dest="gf_executable",
        type=_path_value,
        default=None,
        metavar="PATH",
    )
    parser.add_argument("--rgl-root", type=_path_value, default=None, metavar="PATH")
    if include_output:
        parser.add_argument(
            "--out-root",
            dest="output_root",
            type=_path_value,
            default=None,
            metavar="PATH",
        )


def _add_legacy_project_root_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-root",
        dest="_legacy_project_root",
        type=_path_value,
        default=None,
        metavar="PATH",
        help=argparse.SUPPRESS,
    )


def _add_verbosity_options(parser: argparse.ArgumentParser) -> None:
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("--quiet", action="store_true")
    verbosity.add_argument("--verbose", action="store_true")


def _add_validate_legacy_options(parser: argparse.ArgumentParser) -> None:
    hidden = argparse.SUPPRESS
    parser.add_argument("--target-file", dest="_legacy_target", type=_path_value, help=hidden)
    parser.add_argument("--timeout-sec", dest="_legacy_timeout", type=_positive_int, help=hidden)
    parser.add_argument(
        "--skip-version-probe",
        dest="_legacy_skip_version_probe",
        action="store_true",
        help=hidden,
    )
    parser.add_argument(
        "--emit-cpu-stats",
        dest="_legacy_cpu_stats",
        action="store_true",
        help=hidden,
    )
    parser.add_argument(
        "--diff-previous",
        dest="_legacy_compare_previous",
        action="store_true",
        help=hidden,
    )
    parser.add_argument("--scan-dir", dest="_legacy_scan_dir", type=_path_value, help=hidden)
    parser.add_argument("--scan-glob", dest="_legacy_scan_glob", type=_text_value, help=hidden)
    parser.add_argument(
        "--gf-path",
        dest="_legacy_gf_path",
        action="append",
        type=_path_value,
        help=hidden,
    )
    parser.add_argument(
        "--include-regex",
        dest="_legacy_include_regex",
        action="append",
        type=_regex_value,
        help=hidden,
    )
    parser.add_argument(
        "--exclude-regex",
        dest="_legacy_exclude_regex",
        action="append",
        type=_regex_value,
        help=hidden,
    )


def _normalize_namespace(
    namespace: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> argparse.Namespace:
    if not hasattr(namespace, "_command"):
        raise CliUsageError("a command is required", usage=parser.format_usage().rstrip())

    aliases: list[str] = []
    _normalize_repeatable_values(namespace)
    _normalize_language_inputs(namespace, aliases, parser)

    if namespace._command is CliCommand.LANGUAGE_PROBE:
        _normalize_language_probe(namespace, parser)
    elif namespace._command is CliCommand.VALIDATE:
        _normalize_validate(namespace, aliases, parser)
    elif namespace._command is CliCommand.PROJECT_CHECK:
        if getattr(namespace, "validation_profile", None) is None:
            _usage_error(parser, "project check requires --profile")
    elif namespace._command is CliCommand.SCENARIOS_CHECK:
        _validate_unique_ids(namespace.scenario_ids, option="--scenario")
        namespace.scenario_ids = tuple(namespace.scenario_ids)
        namespace.scenarios = namespace.scenario_ids
    elif namespace._command is CliCommand.GOLD_UPDATE:
        _normalize_gold_update(namespace, parser)
        namespace.scenario_ids = tuple(namespace.scenario_ids)
        namespace.scenarios = namespace.scenario_ids
    elif namespace._command is CliCommand.REPORTS_CHECK and namespace.strict:
        namespace.verify_hashes = True

    namespace.command = namespace._command
    namespace._compatibility_warnings = _compatibility_warnings(aliases)
    return namespace


def _normalize_language_inputs(
    namespace: argparse.Namespace,
    aliases: list[str],
    parser: argparse.ArgumentParser,
) -> None:
    legacy_root = getattr(namespace, "_legacy_project_root", None)
    if legacy_root is None:
        return

    existing = getattr(namespace, "language_path", None)
    if existing is not None and existing != legacy_root:
        _usage_error(parser, "--project-root conflicts with --language-path")
    namespace.language_path = legacy_root
    namespace.legacy_project_root = legacy_root
    aliases.append("--project-root -> --language-path (migration compatibility)")
    delattr(namespace, "_legacy_project_root")


def _normalize_language_probe(
    namespace: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    language_path = getattr(namespace, "language_path", None)
    if language_path is None:
        _usage_error(parser, "language probe requires LANGUAGE-PATH")
    probe_gf = bool(getattr(namespace, "probe_gf", False))
    namespace.probe_gf = probe_gf
    namespace.verify_with_gf = probe_gf


def _require_language_startup_input(
    namespace: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    if getattr(namespace, "language_path", None) is not None:
        return
    if bool(getattr(namespace, "use_last_language", False)):
        return
    if getattr(namespace, "legacy_project_root", None) is not None:
        return
    _usage_error(
        parser,
        "an explicit --language-path or --last-language selection is required",
    )


def _normalize_validate(
    namespace: argparse.Namespace,
    aliases: list[str],
    parser: argparse.ArgumentParser,
) -> None:
    raw_mode = namespace.mode
    if (
        getattr(namespace, "language_path", None) is None
        and not bool(getattr(namespace, "use_last_language", False))
        and getattr(namespace, "legacy_project_root", None) is None
        and raw_mode is None
        and getattr(namespace, "target", None) is None
        and not tuple(getattr(namespace, "scenario_ids", ()))
        and getattr(namespace, "validation_profile", None) is None
    ):
        _require_language_startup_input(namespace, parser)
    if raw_mode in _LEGACY_MODE_ALIASES:
        canonical_mode = _LEGACY_MODE_ALIASES[raw_mode]
        aliases.append(f"--mode {raw_mode} -> --mode {canonical_mode.value}")
        namespace.mode = canonical_mode
    elif raw_mode is not None:
        namespace.mode = ValidationMode(raw_mode)

    _apply_legacy_scalar(
        namespace,
        canonical="target",
        legacy="_legacy_target",
        legacy_label="--target-file",
        aliases=aliases,
    )
    _apply_legacy_scalar(
        namespace,
        canonical="compile_timeout",
        legacy="_legacy_timeout",
        legacy_label="--timeout-sec",
        aliases=aliases,
    )

    if namespace._legacy_skip_version_probe:
        namespace.no_version_probe = True
        aliases.append("--skip-version-probe -> --no-version-probe")
    if namespace._legacy_cpu_stats:
        namespace.cpu_stats = True
        aliases.append("--emit-cpu-stats -> --cpu-stats")
    if namespace._legacy_compare_previous:
        if namespace.compare_previous is False:
            _usage_error(
                parser,
                "--diff-previous conflicts with --no-compare-previous",
            )
        namespace.compare_previous = True
        aliases.append("--diff-previous -> --compare-previous")

    legacy_overrides = _collect_legacy_project_overrides(namespace, aliases)
    namespace.legacy_overrides = legacy_overrides

    effective_mode = namespace.mode or DEFAULT_VALIDATION_MODE
    if not isinstance(effective_mode, ValidationMode):
        effective_mode = ValidationMode(effective_mode)
    namespace.mode = effective_mode

    if effective_mode is ValidationMode.QUICK and namespace.target is None:
        language_path = getattr(namespace, "language_path", None)
        if not (isinstance(language_path, Path) and language_path.suffix.casefold() == ".gf"):
            _usage_error(
                parser,
                "--target is required in quick mode unless --language-path is a .gf file",
            )
    if namespace.target is not None and effective_mode is not ValidationMode.QUICK:
        _usage_error(parser, "--target is valid only when --mode quick")
    if namespace.checkpoint is not None and effective_mode is not ValidationMode.CHECKPOINT:
        _usage_error(parser, "--checkpoint is valid only when --mode checkpoint")
    if namespace.max_files not in (None, 0) and effective_mode is not ValidationMode.DIAGNOSTIC:
        _usage_error(parser, "--max-files greater than zero is valid only in diagnostic mode")
    if effective_mode is ValidationMode.RELEASE and namespace.no_compile:
        _usage_error(parser, "release mode does not permit --no-compile")
    if effective_mode is ValidationMode.RELEASE and namespace.max_files not in (None, 0):
        _usage_error(parser, "release mode does not permit a positive --max-files")
    if namespace.baseline is not None:
        if namespace.compare_previous is False:
            _usage_error(parser, "--baseline conflicts with --no-compare-previous")
        namespace.compare_previous = True
    if effective_mode is ValidationMode.RELEASE and namespace.strict and namespace.no_version_probe:
        _usage_error(parser, "strict release mode does not permit --no-version-probe")
    if effective_mode is ValidationMode.RELEASE and namespace.strict and legacy_overrides:
        _usage_error(parser, "strict release mode rejects migration-only legacy overrides")

    _validate_unique_ids(namespace.scenario_ids, option="--scenario")
    namespace.scenario_ids = tuple(namespace.scenario_ids)
    namespace.scenarios = namespace.scenario_ids
    namespace.checkpoints = () if namespace.checkpoint is None else (namespace.checkpoint,)
    namespace.skip_version_probe = namespace.no_version_probe
    namespace.emit_cpu_stats = namespace.cpu_stats
    namespace.diff_previous = namespace.compare_previous
    _remove_legacy_attributes(namespace)


def _normalize_gold_update(
    namespace: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    scenario_ids = tuple(namespace.scenario_ids)
    all_count = namespace.all_scenarios
    if type(all_count) is not int or all_count < 0:
        _usage_error(parser, "gold update received an invalid --all selection")
    if all_count > 1:
        _usage_error(parser, "gold update accepts --all only once")
    if all_count and scenario_ids:
        _usage_error(parser, "gold update accepts scenario IDs or --all, not both")
    if not all_count and not scenario_ids:
        _usage_error(parser, "gold update requires scenario IDs or --all")
    _validate_unique_ids(scenario_ids, option="SCENARIO-ID")
    namespace.all_scenarios = bool(all_count)
    namespace.scenario_ids = scenario_ids


def _normalize_repeatable_values(namespace: argparse.Namespace) -> None:
    for name in (
        "scenario_ids",
        "paths",
        "_legacy_gf_path",
        "_legacy_include_regex",
        "_legacy_exclude_regex",
    ):
        if not hasattr(namespace, name):
            continue
        value = getattr(namespace, name)
        if value is None:
            if name == "scenario_ids":
                setattr(namespace, name, ())
            continue
        if isinstance(value, list):
            if len(value) > _MAX_REPEATABLE_VALUES:
                raise CliUsageError(f"{name} exceeds the supported item limit")
            setattr(namespace, name, tuple(value))


def _collect_legacy_project_overrides(
    namespace: argparse.Namespace,
    aliases: list[str],
) -> Mapping[str, object]:
    values: dict[str, object] = {}
    mapping = (
        ("scan_dir", "_legacy_scan_dir", "--scan-dir"),
        ("scan_glob", "_legacy_scan_glob", "--scan-glob"),
        ("gf_path", "_legacy_gf_path", "--gf-path"),
        ("include_regex", "_legacy_include_regex", "--include-regex"),
        ("exclude_regex", "_legacy_exclude_regex", "--exclude-regex"),
    )
    for canonical, attribute, label in mapping:
        value = getattr(namespace, attribute)
        if value not in (None, ()):
            if canonical in {"include_regex", "exclude_regex"} and isinstance(value, tuple):
                value = value[0] if len(value) == 1 else value
            values[canonical] = value
            aliases.append(f"{label} -> migration-only project override")
    return MappingProxyType(values)


def _apply_legacy_scalar(
    namespace: argparse.Namespace,
    *,
    canonical: str,
    legacy: str,
    legacy_label: str,
    aliases: list[str],
) -> None:
    legacy_value = getattr(namespace, legacy)
    if legacy_value is None:
        return
    canonical_value = getattr(namespace, canonical)
    if canonical_value is not None and canonical_value != legacy_value:
        raise CliUsageError(f"{legacy_label} conflicts with its canonical replacement")
    setattr(namespace, canonical, legacy_value)
    aliases.append(f"{legacy_label} -> --{canonical.replace('_', '-')}")


def _remove_legacy_attributes(namespace: argparse.Namespace) -> None:
    for name in tuple(vars(namespace)):
        if name.startswith("_legacy_"):
            delattr(namespace, name)


def _compatibility_warnings(aliases: Sequence[str]) -> tuple[str, ...]:
    if not aliases:
        return ()
    rendered = ", ".join(dict.fromkeys(aliases))
    return (f"legacy CLI compatibility aliases were normalized: {rendered}",)


def _validate_unique_ids(values: Sequence[str], *, option: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise CliUsageError(f"{option} contains duplicate ID {value!r}")
        seen.add(value)


def _usage_error(parser: argparse.ArgumentParser, message: str) -> None:
    raise CliUsageError(message, usage=parser.format_usage().rstrip())


def _path_value(value: str) -> Path:
    checked = _require_argument_text(value, field="path")
    return Path(checked)


def _text_value(value: str) -> str:
    return _require_argument_text(value, field="value")


def _regex_value(value: str) -> str:
    checked = _require_argument_text(value, field="regular expression")
    try:
        re.compile(checked)
    except re.error as exc:
        raise argparse.ArgumentTypeError(f"invalid regular expression: {exc}") from exc
    return checked


def _scenario_id(value: str) -> str:
    checked = _require_argument_text(value, field="scenario ID")
    try:
        return str(validate_scenario_id(checked))
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _canonical_id(value: str) -> str:
    checked = _require_argument_text(value, field="identifier")
    if _ID_RE.fullmatch(checked) is None:
        raise argparse.ArgumentTypeError("identifier must be lowercase kebab case")
    return checked


def _positive_int(value: str) -> int:
    parsed = _plain_int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def _nonnegative_int(value: str) -> int:
    parsed = _plain_int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative integer")
    return parsed


def _plain_int(value: str) -> int:
    checked = _require_argument_text(value, field="integer")
    if not re.fullmatch(r"[+-]?[0-9]+", checked):
        raise argparse.ArgumentTypeError("value must be an integer")
    try:
        return int(checked, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc


def _require_argument_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise argparse.ArgumentTypeError(f"{field} must be a string")
    if not value:
        raise argparse.ArgumentTypeError(f"{field} must not be empty")
    if "\x00" in value:
        raise argparse.ArgumentTypeError(f"{field} must not contain NUL")
    if len(value) > _MAX_ARGUMENT_TEXT:
        raise argparse.ArgumentTypeError(f"{field} exceeds the supported length")
    return value


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip() or "\x00" in value:
        raise ValueError(f"{field} must be non-empty and contain no NUL")
    return value


def _freeze_argument_value(value: object) -> object:
    if isinstance(value, list):
        return tuple(_freeze_argument_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_argument_value(item) for item in value)
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_argument_value(item) for key, item in value.items()}
        )
    return value


__all__ = (
    "CliArgumentParser",
    "CliCommand",
    "CliRequest",
    "CliUsageError",
    "build_parser",
    "parse_args",
    "parse_cli_namespace",
    "parse_cli_request",
)
