"""Unit tests for deterministic, shell-free GF command construction."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from gf_wordbench.validation.compilation.commands import (
    GfCommand,
    GfCommandProfile,
    ValueOptionStyle,
    build_module_compile_arguments,
    build_module_compile_command,
    build_pgf_arguments,
    build_pgf_command,
    build_version_probe_arguments,
    build_version_probe_command,
    serialize_gf_search_path,
)


def _profile(
    *,
    style: ValueOptionStyle = ValueOptionStyle.EQUALS,
    **overrides: object,
) -> GfCommandProfile:
    values: dict[str, object] = {
        "profile_id": "gf-tested-v1",
        "path_separator": os.pathsep,
        "value_option_style": style,
    }
    values.update(overrides)
    return GfCommandProfile(**values)  # type: ignore[arg-type]


def test_version_probe_has_exact_argument_contract(tmp_path: Path) -> None:
    executable = tmp_path / "tools" / "gf executable"
    working_directory = tmp_path / "tool context"

    command = build_version_probe_command(
        executable=executable,
        working_directory=working_directory,
    )

    assert build_version_probe_arguments() == ("--version",)
    assert command == GfCommand(
        operation="probe_version",
        executable=executable,
        arguments=("--version",),
        working_directory=working_directory,
    )
    assert command.argv == (os.fspath(executable), "--version")
    assert command.profile_id is None
    assert command.gf_search_paths == ()


def test_equal_style_module_arguments_follow_canonical_order() -> None:
    profile = _profile()
    source = Path("project source") / "DemoEng.gf"
    project_source = Path("project source")
    shared_source = Path("shared grammar")
    rgl_root = Path("RGL root")
    gfo_dir = Path("run output") / "gfo"
    output_dir = Path("run output") / "generated"

    arguments = build_module_compile_arguments(
        source_file=source,
        gf_search_paths=(project_source, shared_source),
        profile=profile,
        rgl_root=rgl_root,
        gfo_dir=gfo_dir,
        output_dir=output_dir,
        quiet=True,
        emit_cpu_stats=True,
    )

    assert arguments == (
        "-batch",
        "-s",
        f"--path={project_source}{os.pathsep}{shared_source}",
        f"--gf-lib-path={rgl_root}",
        f"--gfo-dir={gfo_dir}",
        f"--output-dir={output_dir}",
        "--cpu",
        os.fspath(source),
    )
    assert arguments[-1] == os.fspath(source)
    assert all(not argument.startswith(('"', "'")) for argument in arguments)


def test_separate_style_keeps_each_option_value_as_one_argument() -> None:
    profile = _profile(style=ValueOptionStyle.SEPARATE)
    source = Path("source with spaces") / "Demo.gf"
    search_path = Path("source with spaces")
    output_dir = Path("output with spaces")

    arguments = build_module_compile_arguments(
        source_file=source,
        gf_search_paths=(search_path,),
        profile=profile,
        output_dir=output_dir,
        quiet=False,
    )

    assert arguments == (
        "-batch",
        "--path",
        os.fspath(search_path),
        "--output-dir",
        os.fspath(output_dir),
        os.fspath(source),
    )
    assert '"' not in "".join(arguments)


def test_module_command_preserves_structured_execution_values(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "Program Files" / "GF" / "gf.exe"
    working_directory = tmp_path / "project with spaces"
    source = working_directory / "DemoEng.gf"
    search_paths = (
        working_directory,
        tmp_path / "RGL source",
        working_directory,
    )

    command = build_module_compile_command(
        executable=executable,
        working_directory=working_directory,
        source_file=source,
        gf_search_paths=search_paths,
        profile=_profile(),
        quiet=True,
    )

    assert command.operation == "compile_module"
    assert command.executable == executable
    assert command.working_directory == working_directory
    assert command.gf_search_paths == search_paths
    assert command.profile_id == "gf-tested-v1"
    assert command.argv == (os.fspath(executable), *command.arguments)
    assert command.arguments[-1] == os.fspath(source)
    assert command.arguments.count(os.fspath(source)) == 1
    assert all(
        not (
            len(argument) >= 2
            and argument[0] == argument[-1]
            and argument[0] in {'"', "'"}
        )
        for argument in command.argv
    )


def test_search_path_serialization_preserves_order_and_duplicates() -> None:
    paths = (Path("zeta"), Path("alpha"), Path("zeta"))

    assert serialize_gf_search_path(paths, separator=";") == "zeta;alpha;zeta"
    assert serialize_gf_search_path(paths, separator=":") == "zeta:alpha:zeta"


def test_pgf_arguments_preserve_entrypoint_order() -> None:
    profile = _profile()
    entrypoints = (
        Path("src") / "DemoEng.gf",
        Path("src") / "DemoSpa.gf",
    )
    source_root = Path("src")
    output_dir = Path("run") / "pgf"

    arguments = build_pgf_arguments(
        entrypoints=entrypoints,
        gf_search_paths=(source_root,),
        profile=profile,
        output_dir=output_dir,
        optimize=True,
        emit_cpu_stats=True,
    )

    assert arguments == (
        "-make",
        "-optimize-pgf",
        f"--path={source_root}",
        f"--output-dir={output_dir}",
        "--cpu",
        os.fspath(entrypoints[0]),
        os.fspath(entrypoints[1]),
    )
    assert arguments[-2:] == tuple(map(os.fspath, entrypoints))


def test_pgf_command_records_profile_and_search_paths(tmp_path: Path) -> None:
    executable = tmp_path / "gf"
    working_directory = tmp_path / "project"
    source_root = working_directory / "src"
    entrypoints = (source_root / "DemoEng.gf",)

    command = build_pgf_command(
        executable=executable,
        working_directory=working_directory,
        entrypoints=entrypoints,
        gf_search_paths=(source_root,),
        profile=_profile(),
        optimize=False,
    )

    assert command.operation == "build_pgf"
    assert command.executable == executable
    assert command.working_directory == working_directory
    assert command.gf_search_paths == (source_root,)
    assert command.profile_id == "gf-tested-v1"
    assert "-optimize-pgf" not in command.arguments
    assert command.arguments[-1] == os.fspath(entrypoints[0])


@pytest.mark.parametrize(
    "source_file",
    (
        "Demo.pgf",
        "Demo",
        "",
        "Demo.gf\n--version",
    ),
)
def test_module_source_must_be_a_safe_gf_path(source_file: str) -> None:
    with pytest.raises(ValueError):
        build_module_compile_arguments(
            source_file=source_file,
            gf_search_paths=("src",),
            profile=_profile(),
        )


@pytest.mark.parametrize(
    "entrypoints",
    (
        (),
        ("Demo.gf", "Demo.gf"),
        ("Demo.txt",),
    ),
)
def test_pgf_entrypoints_must_be_nonempty_unique_gf_paths(
    entrypoints: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError):
        build_pgf_arguments(
            entrypoints=entrypoints,
            gf_search_paths=("src",),
            profile=_profile(),
        )


@pytest.mark.parametrize("entrypoints", ("Demo.gf", Path("Demo.gf"), b"Demo.gf"))
def test_pgf_entrypoints_reject_scalar_path_values(entrypoints: object) -> None:
    with pytest.raises(TypeError, match="sequence of paths"):
        build_pgf_arguments(
            entrypoints=entrypoints,  # type: ignore[arg-type]
            gf_search_paths=("src",),
            profile=_profile(),
        )


@pytest.mark.parametrize("search_paths", ((), "src", Path("src"), b"src"))
def test_search_paths_require_a_nonempty_path_iterable(search_paths: object) -> None:
    expected_error = ValueError if search_paths == () else TypeError
    with pytest.raises(expected_error):
        build_module_compile_arguments(
            source_file="Demo.gf",
            gf_search_paths=search_paths,  # type: ignore[arg-type]
            profile=_profile(),
        )


@pytest.mark.parametrize("separator", ("", "::", "=", "\n"))
def test_search_path_separator_is_one_safe_character(separator: str) -> None:
    with pytest.raises(ValueError):
        serialize_gf_search_path(("src",), separator=separator)


def test_search_path_separator_must_be_text() -> None:
    with pytest.raises(TypeError, match="string"):
        serialize_gf_search_path(("src",), separator=1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("profile_id", "invalid profile", ValueError),
        ("path_separator", "", ValueError),
        ("path_separator", "::", ValueError),
        ("batch_flag", "batch", ValueError),
        ("path_option", "--path=value", ValueError),
        ("quiet_flag", "-s quiet", ValueError),
        ("value_option_style", "equals", TypeError),
    ),
)
def test_profile_rejects_invalid_contract_fields(
    field: str,
    value: object,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        _profile(**{field: value})


def test_optional_compile_option_fails_when_profile_does_not_support_it() -> None:
    profile = _profile(gfo_dir_option=None)

    with pytest.raises(ValueError, match="does not support a GFO directory option"):
        build_module_compile_arguments(
            source_file="Demo.gf",
            gf_search_paths=("src",),
            profile=profile,
            gfo_dir="run/gfo",
        )


def test_optional_pgf_features_fail_when_profile_does_not_support_them() -> None:
    no_optimization = _profile(optimize_pgf_flag=None)
    no_cpu_stats = _profile(cpu_stats_flag=None)

    with pytest.raises(ValueError, match="does not support optimized PGF"):
        build_pgf_arguments(
            entrypoints=("Demo.gf",),
            gf_search_paths=("src",),
            profile=no_optimization,
            optimize=True,
        )

    with pytest.raises(ValueError, match="does not support CPU statistics"):
        build_pgf_arguments(
            entrypoints=("Demo.gf",),
            gf_search_paths=("src",),
            profile=no_cpu_stats,
            emit_cpu_stats=True,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("quiet", 1),
        ("emit_cpu_stats", "yes"),
    ),
)
def test_compile_boolean_flags_require_actual_bool(field: str, value: object) -> None:
    arguments: dict[str, object] = {
        "source_file": "Demo.gf",
        "gf_search_paths": ("src",),
        "profile": _profile(),
        field: value,
    }

    with pytest.raises(TypeError, match=f"{field} must be a bool"):
        build_module_compile_arguments(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("optimize", 1),
        ("emit_cpu_stats", "yes"),
    ),
)
def test_pgf_boolean_flags_require_actual_bool(field: str, value: object) -> None:
    arguments: dict[str, object] = {
        "entrypoints": ("Demo.gf",),
        "gf_search_paths": ("src",),
        "profile": _profile(),
        field: value,
    }

    with pytest.raises(TypeError, match=f"{field} must be a bool"):
        build_pgf_arguments(**arguments)  # type: ignore[arg-type]


def test_command_rejects_shell_control_characters_and_scalar_arguments() -> None:
    with pytest.raises(ValueError, match="control characters"):
        GfCommand(
            operation="compile_module",
            executable="gf",
            arguments=("Demo.gf\n--version",),
            working_directory=".",
        )

    with pytest.raises(TypeError, match="iterable of strings"):
        GfCommand(
            operation="compile_module",
            executable="gf",
            arguments="Demo.gf",  # type: ignore[arg-type]
            working_directory=".",
        )


def test_command_is_immutable() -> None:
    command = build_version_probe_command(
        executable="gf",
        working_directory=".",
    )

    with pytest.raises(AttributeError):
        command.operation = "changed"  # type: ignore[misc]
