"""Unit tests for explicit validation-target resolution."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path, PurePosixPath

import pytest

from gf_wordbench.config.models import ValidationTarget
from gf_wordbench.kernel.errors import (
    ContractViolationError,
    EvidenceIOError,
    PathSecurityError,
    ProjectConfigurationError,
)
from gf_wordbench.kernel.statuses import TargetKind
from gf_wordbench.validation.selection import targets as targets_module
from gf_wordbench.validation.selection.targets import (
    canonical_project_relative_target,
    canonical_source_relative_target,
    extract_module_name,
    format_target_identity,
    is_source_target_kind,
    resolve_configured_target,
    resolve_configured_targets,
    resolve_quick_target,
    resolve_release_targets,
    resolve_source_target,
)

_EXPECTED_PUBLIC_NAMES = (
    "canonical_project_relative_target",
    "canonical_source_relative_target",
    "extract_module_name",
    "format_target_identity",
    "is_source_target_kind",
    "resolve_configured_target",
    "resolve_configured_targets",
    "resolve_quick_target",
    "resolve_release_targets",
    "resolve_source_target",
)


def _project_tree(tmp_path: Path) -> tuple[Path, Path]:
    project_root = (tmp_path / "project").resolve()
    source_root = project_root / "grammar"
    source_root.mkdir(parents=True)
    return project_root, source_root


def _source_file(source_root: Path, relative_path: str) -> Path:
    path = source_root.joinpath(*PurePosixPath(relative_path).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"abstract {path.stem} = {{ cat Item ; }}\n",
        encoding="utf-8",
    )
    return path.resolve()


def test_targets_module_exposes_only_the_canonical_public_api() -> None:
    assert targets_module.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(targets_module, name) for name in targets_module.__all__)


@pytest.mark.parametrize(
    ("file_path", "expected"),
    [
        (Path("Main.gf"), "Main"),
        (Path("nested/Grammar.GF"), "Grammar"),
        (Path("grammaire/Été.gf"), "Été"),
    ],
)
def test_extract_module_name_preserves_the_source_filename(
    file_path: Path,
    expected: str,
) -> None:
    assert extract_module_name(file_path) == expected


@pytest.mark.parametrize(
    "file_path",
    [Path("Main"), Path("Main.txt"), Path("."), Path("..")],
)
def test_extract_module_name_rejects_non_source_paths(file_path: Path) -> None:
    with pytest.raises(ValueError):
        extract_module_name(file_path)


def test_extract_module_name_requires_a_path_and_rejects_nul() -> None:
    with pytest.raises(TypeError, match="file_path must be a Path"):
        extract_module_name("Main.gf")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="NUL"):
        extract_module_name(Path("Bad\x00.gf"))


def test_source_target_kinds_are_an_explicit_closed_set() -> None:
    assert {kind for kind in TargetKind if is_source_target_kind(kind)} == {
        TargetKind.FILE,
        TargetKind.MODULE,
        TargetKind.CHECKPOINT,
        TargetKind.ENTRYPOINT,
    }

    assert not is_source_target_kind(TargetKind.SCENARIO)
    assert not is_source_target_kind(TargetKind.PROJECT)
    assert not is_source_target_kind(TargetKind.REGRESSION)

    with pytest.raises(TypeError, match="TargetKind"):
        is_source_target_kind("file")  # type: ignore[arg-type]


def test_format_target_identity_is_typed_portable_and_stable() -> None:
    assert (
        format_target_identity(ValidationTarget(TargetKind.FILE, r"grammar\Main.gf"))
        == "file:grammar/Main.gf"
    )
    assert format_target_identity(ValidationTarget(TargetKind.MODULE, "Syntax")) == "module:Syntax"
    assert (
        format_target_identity(ValidationTarget(TargetKind.SCENARIO, "parse-smoke"))
        == "scenario:parse-smoke"
    )
    assert (
        format_target_identity(
            ValidationTarget(TargetKind.PROJECT, None),
            project_id="example-language",
        )
        == "project:example-language"
    )


def test_format_target_identity_requires_the_project_fallback_value() -> None:
    with pytest.raises(TypeError, match="project_id must be a string"):
        format_target_identity(ValidationTarget(TargetKind.PROJECT, None))

    with pytest.raises(ValueError, match="project_id must not be empty"):
        format_target_identity(
            ValidationTarget(TargetKind.PROJECT, None),
            project_id="",
        )

    with pytest.raises(TypeError, match="ValidationTarget"):
        format_target_identity(object())  # type: ignore[arg-type]


def test_canonical_relative_targets_use_resolved_posix_paths(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    file_path = _source_file(source_root, "syntax/GrammaireÉté.gf")

    assert canonical_project_relative_target(
        file_path,
        project_root=project_root,
    ) == PurePosixPath("grammar/syntax/GrammaireÉté.gf")
    assert canonical_source_relative_target(
        file_path,
        source_root=source_root,
    ) == PurePosixPath("syntax/GrammaireÉté.gf")


def test_canonical_relative_targets_reject_escape_and_root_identity(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    outside = _source_file((tmp_path / "outside").resolve(), "Main.gf")

    with pytest.raises(PathSecurityError, match="escapes the approved root"):
        canonical_source_relative_target(outside, source_root=source_root)

    with pytest.raises(PathSecurityError, match="inside, not equal to"):
        canonical_project_relative_target(
            project_root,
            project_root=project_root,
        )


def test_quick_target_accepts_project_and_source_relative_paths(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    main = _source_file(source_root, "Main.gf")
    nested = _source_file(source_root, "syntax/Nested.gf")

    assert (
        resolve_quick_target(
            Path("grammar/Main.gf"),
            project_root=project_root,
            source_root=source_root,
        )
        == main
    )
    assert (
        resolve_quick_target(
            Path("syntax/Nested.gf"),
            project_root=project_root,
            source_root=source_root,
        )
        == nested
    )


def test_quick_module_target_appends_the_gf_suffix(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)
    expected = _source_file(source_root, "syntax/Main.gf")

    actual = resolve_quick_target(
        ValidationTarget(TargetKind.MODULE, "syntax/Main"),
        project_root=project_root,
        source_root=source_root,
    )

    assert actual == expected


def test_quick_target_uses_unique_basename_fallback_only_after_direct_paths(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    nested = _source_file(source_root, "nested/Main.gf")

    assert (
        resolve_quick_target(
            "Main.gf",
            project_root=project_root,
            source_root=source_root,
        )
        == nested
    )

    direct = _source_file(source_root, "Main.gf")
    assert (
        resolve_quick_target(
            "Main.gf",
            project_root=project_root,
            source_root=source_root,
        )
        == direct
    )


def test_quick_target_rejects_ambiguous_basename_in_stable_order(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    _source_file(source_root, "zeta/Main.gf")
    _source_file(source_root, "Alpha/Main.gf")

    with pytest.raises(ProjectConfigurationError) as caught:
        resolve_quick_target(
            "Main.gf",
            project_root=project_root,
            source_root=source_root,
        )

    assert str(caught.value) == (
        "Quick target 'Main.gf' is ambiguous; matches: Alpha/Main.gf, zeta/Main.gf"
    )
    assert caught.value.stage == "selection"
    assert caught.value.operation == "resolve_quick_target"
    assert caught.value.subject == "Main.gf"


def test_quick_target_reports_missing_and_non_gf_targets(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)

    with pytest.raises(ProjectConfigurationError, match="was not found") as missing:
        resolve_quick_target(
            "Missing.gf",
            project_root=project_root,
            source_root=source_root,
        )
    assert missing.value.operation == "resolve_quick_target"

    readme = source_root / "README.md"
    readme.write_text("not GF\n", encoding="utf-8")
    with pytest.raises(ProjectConfigurationError, match=r"must end in '\.gf'"):
        resolve_quick_target(
            readme,
            project_root=project_root,
            source_root=source_root,
        )


def test_absolute_quick_target_must_remain_inside_the_source_root(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    inside = _source_file(source_root, "Main.gf")
    outside = project_root / "Outside.gf"
    outside.write_text("abstract Outside = {}\n", encoding="utf-8")

    assert (
        resolve_quick_target(
            inside,
            project_root=project_root,
            source_root=source_root,
        )
        == inside
    )

    with pytest.raises(PathSecurityError, match="escapes the approved root"):
        resolve_quick_target(
            outside,
            project_root=project_root,
            source_root=source_root,
        )


def test_quick_target_requires_file_or_module_kind(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)

    with pytest.raises(ContractViolationError, match="file.*module"):
        resolve_quick_target(
            ValidationTarget(TargetKind.CHECKPOINT, "Main.gf"),
            project_root=project_root,
            source_root=source_root,
        )


def test_configured_target_is_exactly_source_relative_without_fallback(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    expected = _source_file(source_root, "syntax/Main.gf")

    assert (
        resolve_configured_target(
            "syntax/Main.gf",
            project_root=project_root,
            source_root=source_root,
        )
        == expected
    )

    with pytest.raises(ProjectConfigurationError, match="does not exist"):
        resolve_configured_target(
            "Main.gf",
            project_root=project_root,
            source_root=source_root,
        )


@pytest.mark.parametrize(
    "target",
    [
        r"syntax\Main.gf",
        "../Main.gf",
        "/absolute/Main.gf",
        "C:/absolute/Main.gf",
        "syntax/Main.txt",
        ".",
    ],
)
def test_configured_target_rejects_nonportable_or_invalid_paths(
    tmp_path: Path,
    target: str,
) -> None:
    project_root, source_root = _project_tree(tmp_path)

    with pytest.raises(ProjectConfigurationError):
        resolve_configured_target(
            target,
            project_root=project_root,
            source_root=source_root,
        )


def test_configured_targets_preserve_order_and_first_filesystem_identity(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    first = _source_file(source_root, "Morphology.gf")
    second = _source_file(source_root, "Syntax.gf")

    def configured() -> Iterator[str]:
        yield "Morphology.gf"
        yield "Syntax.gf"
        yield "Morphology.gf"

    assert resolve_configured_targets(
        configured(),
        project_root=project_root,
        source_root=source_root,
    ) == (first, second)

    with pytest.raises(TypeError, match="iterable of paths"):
        resolve_configured_targets(
            "Morphology.gf",
            project_root=project_root,
            source_root=source_root,
        )


def test_release_targets_are_checkpoint_then_new_entrypoint_ordered_union(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    morphology = _source_file(source_root, "Morphology.gf")
    grammar = _source_file(source_root, "Grammar.gf")
    syntax = _source_file(source_root, "Syntax.gf")

    assert resolve_release_targets(
        ("Morphology.gf", "Grammar.gf"),
        ("Grammar.gf", "Syntax.gf"),
        project_root=project_root,
        source_root=source_root,
    ) == (morphology, grammar, syntax)


def test_resolve_source_target_dispatches_by_typed_kind(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)
    quick = _source_file(source_root, "quick/Main.gf")
    checkpoint = _source_file(source_root, "layers/Checkpoint.gf")

    assert (
        resolve_source_target(
            ValidationTarget(TargetKind.MODULE, "quick/Main"),
            project_root=project_root,
            source_root=source_root,
        )
        == quick
    )
    assert (
        resolve_source_target(
            ValidationTarget(TargetKind.CHECKPOINT, "layers/Checkpoint.gf"),
            project_root=project_root,
            source_root=source_root,
        )
        == checkpoint
    )

    with pytest.raises(ContractViolationError, match="does not resolve"):
        resolve_source_target(
            ValidationTarget(TargetKind.SCENARIO, "smoke"),
            project_root=project_root,
            source_root=source_root,
        )

    with pytest.raises(TypeError, match="ValidationTarget"):
        resolve_source_target(
            object(),  # type: ignore[arg-type]
            project_root=project_root,
            source_root=source_root,
        )


def test_resolved_target_must_be_readable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    target = _source_file(source_root, "Main.gf")
    monkeypatch.setattr(
        "gf_wordbench.validation.selection.targets.os.access",
        lambda *_args: False,
    )

    with pytest.raises(EvidenceIOError, match="not readable") as caught:
        resolve_quick_target(
            target,
            project_root=project_root,
            source_root=source_root,
        )

    assert caught.value.stage == "selection"
    assert caught.value.operation == "resolve_target"
    assert caught.value.subject == str(target)


def test_source_root_must_be_a_strict_child_of_project_root(
    tmp_path: Path,
) -> None:
    project_root = (tmp_path / "project").resolve()
    project_root.mkdir()
    target = _source_file(project_root, "Main.gf")

    with pytest.raises(PathSecurityError, match="inside, not equal to"):
        resolve_quick_target(
            target,
            project_root=project_root,
            source_root=project_root,
        )
