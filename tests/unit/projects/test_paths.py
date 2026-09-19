"""Unit tests for canonical active-project path derivation."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

from gf_wordbench.kernel.errors import ContractViolationError, PathSecurityError
from gf_wordbench.projects.paths import (
    PROJECT_CONFIG_FILENAME,
    PROJECT_DOCS_DIRECTORY,
    PROJECT_GOLD_DIRECTORY,
    PROJECT_INPUTS_DIRECTORY,
    PROJECT_README_FILENAME,
    PROJECT_ROOT_DECLARATION,
    PROJECT_SCENARIOS_DIRECTORY,
    PROJECT_VALIDATION_DIRECTORY,
    ProjectPaths,
    normalize_project_root_declaration,
    resolve_module_path,
    resolve_project_relative_path,
    resolve_scenario_path,
    resolve_source_relative_path,
    resolve_source_root,
)


def test_project_paths_from_root_derives_the_canonical_layout(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "active-project"

    paths = ProjectPaths.from_root(project_root)

    assert paths == ProjectPaths(
        root=project_root,
        config_file=project_root / PROJECT_CONFIG_FILENAME,
        readme_file=project_root / PROJECT_README_FILENAME,
        docs_dir=project_root / PROJECT_DOCS_DIRECTORY,
        validation_dir=project_root / PROJECT_VALIDATION_DIRECTORY,
        scenarios_dir=(project_root / PROJECT_VALIDATION_DIRECTORY / PROJECT_SCENARIOS_DIRECTORY),
        gold_dir=(project_root / PROJECT_VALIDATION_DIRECTORY / PROJECT_GOLD_DIRECTORY),
        inputs_dir=(project_root / PROJECT_VALIDATION_DIRECTORY / PROJECT_INPUTS_DIRECTORY),
    )


def test_project_paths_from_root_is_lexical_and_performs_no_io(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "missing" / "project"

    paths = ProjectPaths.from_root(project_root)

    assert paths.root == project_root
    assert not project_root.exists()
    assert paths.config_file == project_root / "project.toml"


def test_project_paths_from_root_rejects_relative_root() -> None:
    with pytest.raises(ContractViolationError, match="explicit resolution base"):
        ProjectPaths.from_root(Path("relative-project"))


def test_project_paths_from_root_normalizes_lexical_segments(
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "workspace" / ".." / "project"

    paths = ProjectPaths.from_root(raw_root)

    assert paths.root == tmp_path / "project"


def test_resolve_project_relative_path_joins_portable_segments(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"

    resolved = resolve_project_relative_path(
        project_root,
        "validation/scenarios/generation-smoke.gfs",
    )

    assert resolved == (project_root / "validation" / "scenarios" / "generation-smoke.gfs")


def test_resolve_project_relative_path_accepts_native_path_object(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    declaration = Path("validation") / "scenarios" / "load.gfs"

    assert resolve_project_relative_path(project_root, declaration) == (
        project_root / "validation" / "scenarios" / "load.gfs"
    )


def test_resolve_project_relative_path_accepts_windows_runtime_path(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    declaration = PureWindowsPath(r"validation\scenarios\generation-smoke.gfs")

    assert resolve_project_relative_path(project_root, declaration) == (
        project_root / "validation" / "scenarios" / "generation-smoke.gfs"
    )


def test_resolve_project_relative_path_preserves_unicode_and_case(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "Projet"

    resolved = resolve_project_relative_path(
        project_root,
        "docs/ÉtatDuProjet.md",
    )

    assert resolved == project_root / "docs" / "ÉtatDuProjet.md"


def test_resolve_project_relative_path_rejects_root_by_default(
    tmp_path: Path,
) -> None:
    with pytest.raises(ContractViolationError, match="child path"):
        resolve_project_relative_path(tmp_path, ".")


def test_resolve_project_relative_path_can_explicitly_return_root(
    tmp_path: Path,
) -> None:
    assert resolve_project_relative_path(tmp_path, ".", allow_root=True) == tmp_path


@pytest.mark.parametrize(
    "value",
    [
        "../outside.gf",
        "source/../../outside.gf",
        "/absolute/path.gf",
    ],
)
def test_resolve_project_relative_path_rejects_escape_attempts(
    tmp_path: Path,
    value: str,
) -> None:
    with pytest.raises(PathSecurityError):
        resolve_project_relative_path(tmp_path, value)


@pytest.mark.parametrize(
    "value",
    [
        r"source\Main.gf",
        "source//Main.gf",
        "source/${MODULE}.gf",
        "source/%MODULE%.gf",
        "source/NUL.gf",
    ],
)
def test_resolve_project_relative_path_rejects_noncanonical_raw_text(
    tmp_path: Path,
    value: str,
) -> None:
    with pytest.raises(ContractViolationError):
        resolve_project_relative_path(tmp_path, value)


def test_project_paths_resolve_project_path_delegates_to_canonical_rule(
    tmp_path: Path,
) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    assert paths.resolve_project_path("docs/reference.md") == (tmp_path / "docs" / "reference.md")


def test_project_paths_relative_path_returns_portable_identity(
    tmp_path: Path,
) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    candidate = tmp_path / "validation" / "gold" / "français.json"

    assert paths.relative_path(candidate) == PurePosixPath("validation/gold/français.json")


def test_project_paths_relative_path_can_forbid_root_identity(
    tmp_path: Path,
) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    assert paths.relative_path(tmp_path) == PROJECT_ROOT_DECLARATION
    with pytest.raises(PathSecurityError, match="lexical containment"):
        paths.relative_path(tmp_path, allow_root=False)


def test_project_paths_relative_path_rejects_external_candidate(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    paths = ProjectPaths.from_root(project_root)

    with pytest.raises(PathSecurityError, match="lexical containment"):
        paths.relative_path(tmp_path / "outside" / "Main.gf")


def test_normalize_project_root_declaration_accepts_only_dot_by_default() -> None:
    assert normalize_project_root_declaration(".") == PROJECT_ROOT_DECLARATION

    with pytest.raises(ContractViolationError, match="must be '\\.'"):
        normalize_project_root_declaration("nested/project")


def test_normalize_project_root_declaration_supports_reviewed_alternate_layout() -> None:
    assert normalize_project_root_declaration(
        "nested/project",
        allow_noncanonical=True,
    ) == PurePosixPath("nested/project")


def test_normalize_project_root_declaration_accepts_windows_runtime_path() -> None:
    declaration = PureWindowsPath(r"nested\project")

    assert normalize_project_root_declaration(
        declaration,
        allow_noncanonical=True,
    ) == PurePosixPath("nested/project")


def test_normalize_project_root_declaration_rejects_raw_backslashes() -> None:
    with pytest.raises(ContractViolationError, match="must use '/' separators"):
        normalize_project_root_declaration(
            r"nested\project",
            allow_noncanonical=True,
        )


def test_resolve_source_root_uses_project_root_as_its_only_base(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"

    assert resolve_source_root(project_root, "lib/src/french") == (
        project_root / "lib" / "src" / "french"
    )


def test_resolve_source_root_accepts_windows_runtime_path(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"

    assert (
        resolve_source_root(
            project_root,
            PureWindowsPath(r"lib\src\french"),
        )
        == project_root / "lib" / "src" / "french"
    )


def test_resolve_source_root_rejects_project_root_as_source_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(ContractViolationError, match="child path"):
        resolve_source_root(tmp_path, ".")


def test_resolve_source_relative_path_uses_source_root_as_base(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "project" / "src"

    assert (
        resolve_source_relative_path(
            source_root,
            "concrete/French.gf",
        )
        == source_root / "concrete" / "French.gf"
    )


def test_resolve_source_relative_path_accepts_windows_runtime_path(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "project" / "src"

    assert (
        resolve_source_relative_path(
            source_root,
            PureWindowsPath(r"concrete\French.gf"),
        )
        == source_root / "concrete" / "French.gf"
    )


def test_resolve_module_path_accepts_case_insensitive_gf_suffix(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"

    assert resolve_module_path(source_root, "Main.gf") == source_root / "Main.gf"
    assert resolve_module_path(source_root, "Legacy.GF") == (source_root / "Legacy.GF")


def test_resolve_module_path_accepts_windows_runtime_path(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"

    assert (
        resolve_module_path(
            source_root,
            PureWindowsPath(r"concrete\Main.gf"),
        )
        == source_root / "concrete" / "Main.gf"
    )


def test_resolve_module_path_rejects_raw_backslashes(
    tmp_path: Path,
) -> None:
    with pytest.raises(ContractViolationError, match="must use '/' separators"):
        resolve_module_path(tmp_path, r"concrete\Main.gf")


@pytest.mark.parametrize(
    "module_path",
    [
        "Main",
        "Main.gfo",
        "Main.pgf",
        "Main.gf.txt",
    ],
)
def test_resolve_module_path_requires_gf_source_suffix(
    tmp_path: Path,
    module_path: str,
) -> None:
    with pytest.raises(ContractViolationError, match="must end in '.gf'"):
        resolve_module_path(tmp_path, module_path)


def test_resolve_module_path_rejects_path_outside_source_root(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"

    with pytest.raises(PathSecurityError):
        resolve_module_path(source_root, "../Main.gf")


def test_resolve_scenario_path_derives_native_gfs_filename(
    tmp_path: Path,
) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    assert resolve_scenario_path(paths, "generation-smoke") == (
        tmp_path / "validation" / "scenarios" / "generation-smoke.gfs"
    )


def test_resolve_scenario_path_preserves_valid_unicode_identifier(
    tmp_path: Path,
) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    assert resolve_scenario_path(paths, "génération") == (
        tmp_path / "validation" / "scenarios" / "génération.gfs"
    )


@pytest.mark.parametrize(
    "scenario_id",
    [
        "",
        ".",
        "..",
        "nested/scenario",
        r"nested\scenario",
        "scenario.gfs",
        "SCENARIO.GFS",
        "NUL",
        "scenario ",
        "scenario\x00name",
    ],
)
def test_resolve_scenario_path_rejects_invalid_registry_identity(
    tmp_path: Path,
    scenario_id: str,
) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    with pytest.raises((ContractViolationError, PathSecurityError)):
        resolve_scenario_path(paths, scenario_id)
