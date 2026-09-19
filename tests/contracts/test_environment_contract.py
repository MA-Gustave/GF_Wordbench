"""Contract tests for GF Wordbench environment ownership and isolation."""

from __future__ import annotations

import ast
from collections.abc import Mapping
import inspect
import os
from types import MappingProxyType, ModuleType
from typing import cast

import pytest

from gf_wordbench.config import environment as config_environment
from gf_wordbench.config.models import EnvironmentOverrides
from gf_wordbench.infrastructure import environment as process_environment

pytestmark = pytest.mark.contract

_CANONICAL_VARIABLES = (
    "GF_WORDBENCH_GF_EXE",
    "GF_WORDBENCH_RGL_ROOT",
    "GF_WORDBENCH_OUTPUT_ROOT",
    "GF_WORDBENCH_STATE_PATH",
)
_LEGACY_VARIABLES = ("GF_WORDBENCH_PROJECT_ROOT",)


def test_canonical_environment_namespace_is_exact_and_stable() -> None:
    assert config_environment.ENVIRONMENT_PREFIX == "GF_WORDBENCH_"
    assert config_environment.CANONICAL_ENVIRONMENT_VARIABLES == _CANONICAL_VARIABLES
    assert _CANONICAL_VARIABLES[0] == config_environment.GF_EXECUTABLE_ENV
    assert _CANONICAL_VARIABLES[1] == config_environment.RGL_ROOT_ENV
    assert _CANONICAL_VARIABLES[2] == config_environment.OUTPUT_ROOT_ENV
    assert _CANONICAL_VARIABLES[3] == config_environment.STATE_PATH_ENV
    assert config_environment.LEGACY_ENVIRONMENT_VARIABLES == _LEGACY_VARIABLES
    assert config_environment.PROJECT_ROOT_ENV == _LEGACY_VARIABLES[0]
    assert config_environment.LEGACY_PROJECT_ROOT_ENV == _LEGACY_VARIABLES[0]
    assert config_environment.KNOWN_ENVIRONMENT_VARIABLES == (
        *_CANONICAL_VARIABLES,
        *_LEGACY_VARIABLES,
    )
    assert len(set(config_environment.KNOWN_ENVIRONMENT_VARIABLES)) == 5


def test_config_environment_public_surface_has_one_owner() -> None:
    assert set(config_environment.__all__) == {
        "CANONICAL_ENVIRONMENT_VARIABLES",
        "ENVIRONMENT_PREFIX",
        "GF_EXECUTABLE_ENV",
        "KNOWN_ENVIRONMENT_VARIABLES",
        "LEGACY_ENVIRONMENT_VARIABLES",
        "LEGACY_PROJECT_ROOT_ENV",
        "OUTPUT_ROOT_ENV",
        "PROJECT_ROOT_ENV",
        "RGL_ROOT_ENV",
        "STATE_PATH_ENV",
        "find_unknown_environment_variables",
        "read_environment",
        "resolve_environment",
    }

    process_exports = set(process_environment.__all__)
    assert process_exports == {
        "CONTROLLED_INHERIT_V1",
        "EnvironmentMapping",
        "PreparedEnvironment",
        "REDACTED_VALUE",
        "build_child_environment",
    }
    assert not process_exports.intersection(config_environment.__all__)


def test_environment_modules_preserve_dependency_direction() -> None:
    config_imports = _imported_modules(config_environment)
    process_imports = _imported_modules(process_environment)

    assert "gf_wordbench.infrastructure.environment" not in config_imports
    assert not any(name.startswith("gf_wordbench.config") for name in process_imports)
    assert not any("gf_portfolio" in name for name in config_imports | process_imports)


def test_read_environment_returns_only_documented_raw_overrides() -> None:
    environ = {
        config_environment.PROJECT_ROOT_ENV: "/workspace/project",
        config_environment.GF_EXECUTABLE_ENV: "/tools/gf",
        config_environment.RGL_ROOT_ENV: "/tools/rgl/src",
        config_environment.OUTPUT_ROOT_ENV: "/workspace/runs",
        config_environment.STATE_PATH_ENV: "/workspace/state.json",
        "GF_WORDBENCH_UNDOCUMENTED": "/must/not/be/read",
        "GF_LIB_PATH": "/ambient/gf/path",
        "PATH": "/bin",
    }

    assert config_environment.read_environment(environ) == EnvironmentOverrides(
        project_root="/workspace/project",
        gf_executable="/tools/gf",
        rgl_root="/tools/rgl/src",
        output_root="/workspace/runs",
        state_path="/workspace/state.json",
    )


@pytest.mark.parametrize(
    "raw",
    (
        "%USERPROFILE%\\gf",
        "${HOME}/gf",
        "$GF_ROOT/src",
        "~/gf",
    ),
)
def test_raw_environment_reader_does_not_expand_path_expressions(raw: str) -> None:
    overrides = config_environment.read_environment({config_environment.RGL_ROOT_ENV: raw})

    assert overrides.rgl_root == raw


def test_empty_environment_values_are_unset_but_whitespace_is_preserved() -> None:
    overrides = config_environment.read_environment(
        {
            config_environment.PROJECT_ROOT_ENV: "",
            config_environment.GF_EXECUTABLE_ENV: " ",
            config_environment.RGL_ROOT_ENV: "",
            config_environment.OUTPUT_ROOT_ENV: "",
            config_environment.STATE_PATH_ENV: "",
        }
    )

    assert overrides.project_root is None
    assert overrides.gf_executable == " "
    assert overrides.rgl_root is None
    assert overrides.output_root is None
    assert overrides.state_path is None


def test_unknown_reserved_variables_are_reported_deterministically() -> None:
    environ = {
        "GF_WORDBENCH_ZETA": "1",
        "GF_WORDBENCH_ALPHA": "1",
        "GF_WORDBENCH_EMPTY": "",
        config_environment.PROJECT_ROOT_ENV: "/workspace/project",
        "GF_LIB_PATH": "/ambient",
    }

    assert config_environment.find_unknown_environment_variables(environ) == (
        "GF_WORDBENCH_ALPHA",
        "GF_WORDBENCH_ZETA",
    )


def test_environment_readers_reject_invalid_mapping_entries() -> None:
    with pytest.raises(TypeError, match="mapping"):
        config_environment.read_environment(cast("Mapping[str, str]", object()))

    malformed_name = cast("Mapping[str, str]", {1: "value"})
    with pytest.raises(TypeError, match="names must be strings"):
        config_environment.find_unknown_environment_variables(malformed_name)

    malformed_value = cast(
        "Mapping[str, str]",
        {config_environment.PROJECT_ROOT_ENV: 1},
    )
    with pytest.raises(TypeError, match="must contain a string"):
        config_environment.read_environment(malformed_value)

    with pytest.raises(ValueError, match="NUL"):
        config_environment.read_environment({config_environment.PROJECT_ROOT_ENV: "bad\x00path"})


def test_controlled_child_environment_preserves_os_context_and_removes_ambient_gf_path() -> None:
    parent = {
        "PATH": "/bin:/usr/bin",
        "TMPDIR": "/tmp",
        "LANG": "en_US.UTF-8",
        "HOME": "/home/tester",
        "UNRELATED": "retained",
        "GF_LIB_PATH": "/developer/global/rgl",
    }

    prepared = process_environment.build_child_environment(parent=parent)

    assert prepared.policy == process_environment.CONTROLLED_INHERIT_V1
    assert prepared.values == {
        "PATH": "/bin:/usr/bin",
        "TMPDIR": "/tmp",
        "LANG": "en_US.UTF-8",
        "HOME": "/home/tester",
        "UNRELATED": "retained",
    }
    assert prepared.recorded_overrides == {}
    assert isinstance(prepared.values, MappingProxyType)
    assert isinstance(prepared.recorded_overrides, MappingProxyType)


def test_child_environment_is_a_snapshot_and_never_mutates_inputs() -> None:
    parent = {"PATH": "before", "GF_LIB_PATH": "ambient"}
    overrides = {"PATH": "after", "GF_WORDBENCH_RUN_ID": "run-1"}
    parent_before = dict(parent)
    overrides_before = dict(overrides)
    process_before = dict(os.environ)

    prepared = process_environment.build_child_environment(
        parent=parent,
        overrides=overrides,
    )

    assert parent == parent_before
    assert overrides == overrides_before
    assert dict(os.environ) == process_before
    assert prepared.values["PATH"] == "after"
    assert prepared.values["GF_WORDBENCH_RUN_ID"] == "run-1"
    assert "GF_LIB_PATH" not in prepared.values

    parent["PATH"] = "mutated later"
    overrides["GF_WORDBENCH_RUN_ID"] = "mutated later"
    assert prepared.values["PATH"] == "after"
    assert prepared.values["GF_WORDBENCH_RUN_ID"] == "run-1"


def test_only_explicit_overrides_are_recorded() -> None:
    prepared = process_environment.build_child_environment(
        parent={
            "PATH": "/bin",
            "HOME": "/home/tester",
            "UNRELATED_SECRET": "must-not-be-recorded",
        },
        overrides={
            "LANG": "C.UTF-8",
            "GF_WORDBENCH_RUN_ID": "run-42",
        },
    )

    assert prepared.recorded_overrides == {
        "LANG": "C.UTF-8",
        "GF_WORDBENCH_RUN_ID": "run-42",
    }
    assert "PATH" not in prepared.recorded_overrides
    assert "HOME" not in prepared.recorded_overrides
    assert "UNRELATED_SECRET" not in prepared.recorded_overrides


def test_sensitive_override_values_are_redacted_only_in_evidence() -> None:
    prepared = process_environment.build_child_environment(
        parent={"PATH": "/bin"},
        overrides={"API_TOKEN": "secret", "LANG": "C.UTF-8"},
        sensitive_keys=frozenset({"API_TOKEN"}),
    )

    assert prepared.values["API_TOKEN"] == "secret"
    assert prepared.recorded_overrides == {
        "API_TOKEN": process_environment.REDACTED_VALUE,
        "LANG": "C.UTF-8",
    }
    assert "secret" not in prepared.recorded_overrides.values()


def test_explicit_override_may_replace_a_neutralized_ambient_value() -> None:
    prepared = process_environment.build_child_environment(
        parent={"GF_LIB_PATH": "/ambient"},
        overrides={"GF_LIB_PATH": "/explicit"},
    )

    assert prepared.values["GF_LIB_PATH"] == "/explicit"
    assert prepared.recorded_overrides == {"GF_LIB_PATH": "/explicit"}


def test_default_parent_environment_is_not_modified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GF_LIB_PATH", "/ambient")
    monkeypatch.setenv("GF_WORDBENCH_TEST_SENTINEL", "parent")
    before = dict(os.environ)

    prepared = process_environment.build_child_environment(
        overrides={"GF_WORDBENCH_TEST_SENTINEL": "child"}
    )

    assert dict(os.environ) == before
    assert os.environ["GF_LIB_PATH"] == "/ambient"
    assert os.environ["GF_WORDBENCH_TEST_SENTINEL"] == "parent"
    assert "GF_LIB_PATH" not in prepared.values
    assert prepared.values["GF_WORDBENCH_TEST_SENTINEL"] == "child"


def test_prepared_environment_mappings_are_immutable() -> None:
    prepared = process_environment.build_child_environment(
        parent={"PATH": "/bin"},
        overrides={"LANG": "C.UTF-8"},
    )

    with pytest.raises(TypeError):
        prepared.values["PATH"] = "/other"  # type: ignore[index]
    with pytest.raises(TypeError):
        prepared.recorded_overrides["LANG"] = "other"  # type: ignore[index]


def test_environment_builder_rejects_unsupported_policy() -> None:
    with pytest.raises(ValueError, match="unsupported environment policy"):
        process_environment.build_child_environment(policy="inherit-everything")


def test_environment_builder_rejects_invalid_environment_entries() -> None:
    invalid_cases: tuple[tuple[Mapping[str, str], type[Exception], str], ...] = (
        (cast("Mapping[str, str]", {1: "value"}), TypeError, "keys must be strings"),
        ({"": "value"}, ValueError, "must not be empty"),
        ({"BAD=KEY": "value"}, ValueError, "must not contain '='"),
        ({"BAD\x00KEY": "value"}, ValueError, "NUL"),
        (cast("Mapping[str, str]", {"KEY": 1}), TypeError, "must be a string"),
        ({"KEY": "bad\x00value"}, ValueError, "NUL"),
    )

    for environment, error_type, message in invalid_cases:
        with pytest.raises(error_type, match=message):
            process_environment.build_child_environment(parent=environment)


def test_environment_builder_requires_frozen_sensitive_key_set() -> None:
    with pytest.raises(TypeError, match="frozenset"):
        process_environment.build_child_environment(
            parent={},
            sensitive_keys=cast("frozenset[str]", {"TOKEN"}),
        )

    with pytest.raises(ValueError, match="must not contain '='"):
        process_environment.build_child_environment(
            parent={},
            sensitive_keys=frozenset({"BAD=KEY"}),
        )


def _imported_modules(module: ModuleType) -> set[str]:
    tree = ast.parse(inspect.getsource(module))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)

    return imports
