"""Unit tests for canonical GF Wordbench path primitives."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

import pytest

from gf_wordbench.kernel.errors import ContractViolationError, PathSecurityError
from gf_wordbench.kernel.paths import (
    ContainmentMode,
    PathClass,
    join_portable_path,
    lexically_contains,
    normalize_environment_path,
    normalize_portable_path,
    path_identity_key,
    portable_identity_key,
    relative_portable_path,
    require_lexical_containment,
    serialize_environment_path,
    serialize_portable_path,
    validate_portable_segment,
)


class _PathLike:
    def __init__(self, value: str) -> None:
        self.value = value

    def __fspath__(self) -> str:
        return self.value


def test_public_enums_have_canonical_values() -> None:
    assert [member.value for member in PathClass] == [
        "framework",
        "project",
        "run",
        "environment",
        "temporary",
        "external_evidence",
    ]
    assert [member.value for member in ContainmentMode] == [
        "inside_or_equal",
        "strictly_inside",
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("src/Main.gf", PurePosixPath("src/Main.gf")),
        ("./src/./Main.gf", PurePosixPath("src/Main.gf")),
        (r"src\Syntax\Main.gf", PurePosixPath("src/Syntax/Main.gf")),
        ("grammaire/Élève.gf", PurePosixPath("grammaire/Élève.gf")),
        (_PathLike("scenarios/smoke.gfs"), PurePosixPath("scenarios/smoke.gfs")),
        (Path("gold/parse.gold"), PurePosixPath("gold/parse.gold")),
        (".", PurePosixPath(".")),
    ],
)
def test_normalize_portable_path_returns_canonical_posix_path(
    value: object,
    expected: PurePosixPath,
) -> None:
    assert normalize_portable_path(value) == expected  # type: ignore[arg-type]


def test_portable_path_preserves_case_and_unicode() -> None:
    value = "Sources/Élève/GrammaireGF.gf"

    normalized = normalize_portable_path(value)

    assert normalized.as_posix() == value


def test_portable_root_can_be_forbidden() -> None:
    assert normalize_portable_path(".", allow_root=True) == PurePosixPath(".")

    with pytest.raises(ContractViolationError, match="child path"):
        normalize_portable_path(".", allow_root=False)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "a//b",
        "a/",
        "/absolute/path",
        r"\server\share\file.txt",
        "C:/project/file.txt",
        r"C:\project\file.txt",
        "C:relative.txt",
        "../outside.txt",
        "a/../outside.txt",
        "~/project/file.txt",
        "$HOME/project/file.txt",
        "${HOME}/project/file.txt",
        "%USERPROFILE%/project/file.txt",
        "bad\x00name.txt",
    ],
)
def test_invalid_portable_paths_are_rejected(value: str) -> None:
    with pytest.raises((ContractViolationError, PathSecurityError)):
        normalize_portable_path(value)


def test_canonical_portable_form_can_require_forward_slashes() -> None:
    with pytest.raises(ContractViolationError, match="must use '/' separators"):
        normalize_portable_path(
            r"src\Main.gf",
            accept_backslash=False,
        )


@pytest.mark.parametrize(
    "value",
    [
        b"src/Main.gf",
        object(),
    ],
)
def test_portable_path_requires_text_pathlike_input(value: object) -> None:
    with pytest.raises(ContractViolationError):
        normalize_portable_path(value)  # type: ignore[arg-type]


def test_serialize_portable_path_returns_canonical_text() -> None:
    assert serialize_portable_path(r"raw\scenario.stdout.txt") == ("raw/scenario.stdout.txt")
    assert isinstance(serialize_portable_path("summary.json"), str)


@pytest.mark.parametrize(
    "segment",
    [
        "",
        ".",
        "..",
        " leading",
        "trailing ",
        "trailing.",
        "a/b",
        r"a\b",
        "line\nbreak",
        "delete\x7fcharacter",
        "question?.txt",
        'quote".txt',
        "colon:name",
        "pipe|name",
        "star*.txt",
        "less<name",
        "greater>name",
        "CON",
        "con.txt",
        "NUL.json",
        "COM1",
        "com9.log",
        "LPT1",
        "lpt9.txt",
    ],
)
def test_validate_portable_segment_rejects_nonportable_names(segment: str) -> None:
    with pytest.raises(ContractViolationError):
        validate_portable_segment(segment)


@pytest.mark.parametrize(
    "segment",
    [
        "Main.gf",
        "COM10",
        "LPT10.txt",
        "configuration",
        "Élève-01.gf",
        "name with spaces.txt",
        ".hidden",
    ],
)
def test_validate_portable_segment_accepts_portable_names(segment: str) -> None:
    assert validate_portable_segment(segment) == segment


def test_validate_portable_segment_requires_text() -> None:
    with pytest.raises(ContractViolationError, match="must be text"):
        validate_portable_segment(1)  # type: ignore[arg-type]


def test_normalize_environment_path_normalizes_absolute_path(tmp_path: Path) -> None:
    candidate = tmp_path / "folder" / ".." / "artifact.txt"

    normalized = normalize_environment_path(candidate)

    assert normalized == tmp_path / "artifact.txt"
    assert normalized.is_absolute()


def test_relative_environment_path_requires_explicit_base(tmp_path: Path) -> None:
    with pytest.raises(ContractViolationError, match="explicit resolution base"):
        normalize_environment_path("relative/file.txt")

    assert (
        normalize_environment_path(
            "relative/./file.txt",
            base=tmp_path,
        )
        == tmp_path / "relative" / "file.txt"
    )


def test_environment_path_base_must_be_absolute() -> None:
    with pytest.raises(ContractViolationError, match="base must be absolute"):
        normalize_environment_path("child.txt", base="relative-root")


def test_environment_path_rejects_inline_variable_expansion(tmp_path: Path) -> None:
    for value in (
        "$HOME/file.txt",
        "${HOME}/file.txt",
        "%USERPROFILE%/file.txt",
    ):
        with pytest.raises(ContractViolationError, match="environment-variable"):
            normalize_environment_path(value, base=tmp_path)


def test_environment_path_home_expansion_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    with pytest.raises(ContractViolationError, match="not explicitly enabled"):
        normalize_environment_path("~/artifact.txt")

    assert (
        normalize_environment_path(
            "~/artifact.txt",
            expand_user=True,
        )
        == tmp_path / "artifact.txt"
    )


def test_environment_path_rejects_drive_relative_form() -> None:
    with pytest.raises(PathSecurityError, match="drive-relative"):
        normalize_environment_path("C:relative.txt", base=Path.cwd())


def test_environment_path_trims_outer_whitespace(tmp_path: Path) -> None:
    assert (
        normalize_environment_path(f"  {tmp_path / 'artifact.txt'}  ") == tmp_path / "artifact.txt"
    )


def test_serialize_environment_path_requires_absolute_path(tmp_path: Path) -> None:
    absolute = tmp_path / "résultat final.txt"

    assert serialize_environment_path(absolute) == absolute.as_posix()

    with pytest.raises(ContractViolationError, match="must be absolute"):
        serialize_environment_path("relative/file.txt")


def test_join_portable_path_joins_without_filesystem_access(tmp_path: Path) -> None:
    root = tmp_path / "run_20260725_120000"

    assert join_portable_path(root, r"raw\master.log") == (root / "raw" / "master.log")
    assert join_portable_path(root, ".") == root


def test_join_portable_path_rejects_relative_root() -> None:
    with pytest.raises(ContractViolationError, match="root must be absolute"):
        join_portable_path("relative-root", "summary.json")


def test_join_portable_path_can_forbid_root_equality(tmp_path: Path) -> None:
    with pytest.raises(ContractViolationError, match="child path"):
        join_portable_path(tmp_path, ".", allow_root=False)


def test_path_identity_key_normalizes_absolute_paths(tmp_path: Path) -> None:
    equivalent = tmp_path / "a" / ".." / "artifact.txt"

    assert path_identity_key(equivalent) == path_identity_key(tmp_path / "artifact.txt")
    assert path_identity_key(tmp_path / "artifact.txt") == os.path.normcase(
        os.path.normpath(str(tmp_path / "artifact.txt"))
    )


def test_path_identity_key_requires_absolute_path() -> None:
    with pytest.raises(ContractViolationError, match="must be absolute"):
        path_identity_key("relative/file.txt")


def test_portable_identity_key_has_explicit_case_policy() -> None:
    assert portable_identity_key("Sources/Main.gf") == "Sources/Main.gf"
    assert (
        portable_identity_key(
            "Sources/Main.gf",
            case_sensitive=False,
        )
        == "sources/main.gf"
    )
    assert (
        portable_identity_key(
            "Straße.gf",
            case_sensitive=False,
        )
        == "strasse.gf"
    )


def test_lexical_containment_accepts_descendants_and_optional_root_equality(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    child = root / "src" / "Main.gf"

    assert lexically_contains(root, child)
    assert lexically_contains(root, "src/Main.gf")
    assert lexically_contains(
        root,
        root,
        mode=ContainmentMode.INSIDE_OR_EQUAL,
    )
    assert not lexically_contains(
        root,
        root,
        mode=ContainmentMode.STRICTLY_INSIDE,
    )


def test_lexical_containment_rejects_escape_and_sibling_prefix(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"

    assert not lexically_contains(root, root.parent / "outside.txt")
    assert not lexically_contains(root, root.parent / "project-copy" / "file.txt")
    assert not lexically_contains(root, "../outside.txt")


def test_lexical_containment_requires_absolute_root() -> None:
    with pytest.raises(ContractViolationError, match="root must be absolute"):
        lexically_contains("relative-root", "child.txt")


def test_require_lexical_containment_returns_normalized_candidate(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"

    result = require_lexical_containment(
        root,
        "raw/../summary.json",
        role="run artifact",
    )

    assert result == root / "summary.json"


def test_require_lexical_containment_raises_security_error_on_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"

    with pytest.raises(PathSecurityError, match="violates lexical containment"):
        require_lexical_containment(
            root,
            "../outside.txt",
            role="run artifact",
        )


def test_relative_portable_path_serializes_contained_candidate(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"
    candidate = root / "raw" / "scénario.stdout.txt"

    assert relative_portable_path(
        root,
        candidate,
        role="run artifact",
    ) == PurePosixPath("raw/scénario.stdout.txt")
    assert relative_portable_path(
        root,
        root,
        role="run root",
    ) == PurePosixPath(".")


def test_relative_portable_path_strict_mode_rejects_root_equality(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"

    with pytest.raises(PathSecurityError, match="strictly_inside"):
        relative_portable_path(
            root,
            root,
            role="generated child",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )


def test_relative_portable_path_rejects_outside_candidate(tmp_path: Path) -> None:
    root = tmp_path / "run"

    with pytest.raises(PathSecurityError, match="violates lexical containment"):
        relative_portable_path(
            root,
            tmp_path / "outside.txt",
            role="run artifact",
        )
