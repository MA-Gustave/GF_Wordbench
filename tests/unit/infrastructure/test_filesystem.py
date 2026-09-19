"""Unit tests for generic GF Wordbench filesystem primitives."""

from __future__ import annotations

from collections.abc import Callable
import errno
import os
from pathlib import Path
import shutil
from typing import Any, Final, cast

import pytest

from gf_wordbench.infrastructure.filesystem import (
    UTF8,
    PathContainmentError,
    copy_file,
    create_directory,
    create_directory_exclusive,
    is_within,
    iter_directory,
    read_bytes,
    read_text,
    remove_empty_directory,
    require_directory,
    require_regular_file,
    require_within,
    resolve_existing,
    resolve_for_output,
    unlink_file,
    write_bytes,
    write_text,
)

_UTF8_TEXT: Final = "Grammatical Framework — café\r\n第二行\n"


def _symlink_or_skip(
    link: Path,
    target: Path,
    *,
    directory: bool = False,
) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")


def _hardlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.hardlink_to(target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"hard links are unavailable: {exc}")


def _assert_containment_error(
    error: PathContainmentError,
    *,
    candidate: Path,
    root: Path,
    role: str,
    stage: str,
) -> None:
    assert isinstance(error, PermissionError)
    assert error.errno == errno.EPERM
    assert Path(error.filename) == candidate
    assert error.candidate == candidate
    assert error.root == root
    assert error.role == role
    assert error.stage == stage
    assert role in str(error)
    assert stage in str(error)
    assert str(candidate) in str(error)
    assert str(root) in str(error)


@pytest.mark.parametrize(
    "operation",
    [
        resolve_existing,
        resolve_for_output,
        require_regular_file,
        require_directory,
        read_bytes,
        read_text,
        iter_directory,
    ],
)
def test_existing_path_operations_require_absolute_paths(
    operation: Callable[[Path], object],
) -> None:
    with pytest.raises(ValueError, match="must be absolute"):
        operation(Path("relative/path"))


@pytest.mark.parametrize(
    "operation",
    [
        lambda path: write_bytes(path, b"value"),
        lambda path: write_text(path, "value"),
        lambda path: create_directory(path),
        lambda path: create_directory_exclusive(path),
        lambda path: unlink_file(path),
        lambda path: remove_empty_directory(path),
    ],
)
def test_mutating_operations_require_absolute_paths(
    operation: Callable[[Path], object],
) -> None:
    with pytest.raises(ValueError, match="must be absolute"):
        operation(Path("relative/path"))


def test_copy_requires_absolute_source_and_destination(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"value")

    with pytest.raises(ValueError, match="must be absolute"):
        copy_file(Path("source.bin"), tmp_path / "destination.bin")

    with pytest.raises(ValueError, match="must be absolute"):
        copy_file(source, Path("destination.bin"))


def test_paths_reject_bytes_and_nul(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="text, not bytes"):
        resolve_existing(cast("Any", os.fsencode(tmp_path)))

    with pytest.raises(ValueError, match="NUL"):
        resolve_for_output(str(tmp_path / "invalid\x00name"))


def test_resolve_existing_is_strict_and_resolves_links(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("value", encoding=UTF8)
    link = tmp_path / "link.txt"
    _symlink_or_skip(link, target)

    assert resolve_existing(str(target)) == target.resolve(strict=True)
    assert resolve_existing(link) == target.resolve(strict=True)

    with pytest.raises(FileNotFoundError):
        resolve_existing(tmp_path / "missing.txt")


def test_resolve_existing_maps_symlink_loop_to_eloop(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _symlink_or_skip(first, second)
    _symlink_or_skip(second, first)

    with pytest.raises(OSError) as caught:
        resolve_existing(first)

    assert caught.value.errno == errno.ELOOP
    assert caught.value.filename == os.fspath(first.absolute())


def test_resolve_for_output_preserves_missing_component_order(
    tmp_path: Path,
) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    candidate = existing / "one" / "two" / "artifact.json"

    assert resolve_for_output(candidate) == candidate.absolute()
    assert not candidate.exists()


def test_resolve_for_output_resolves_existing_linked_ancestor(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    _symlink_or_skip(alias, target, directory=True)

    resolved = resolve_for_output(alias / "nested" / "output.txt")

    assert resolved == target.resolve() / "nested" / "output.txt"


def test_existing_and_prospective_containment_are_distinct(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    missing = root / "future" / "artifact.txt"

    with pytest.raises(FileNotFoundError):
        is_within(missing, root)

    assert is_within(missing, root, for_output=True)
    assert require_within(missing, root, for_output=True) == missing.absolute()


def test_containment_supports_inside_equal_and_strict_inside(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    child = root / "child.txt"
    child.write_text("value", encoding=UTF8)
    outside = tmp_path / "outside.txt"
    outside.write_text("value", encoding=UTF8)

    assert is_within(child, root)
    assert is_within(root, root)
    assert not is_within(root, root, allow_equal=False)
    assert not is_within(outside, root)

    assert require_within(child, root) == child.resolve()
    with pytest.raises(PathContainmentError):
        require_within(root, root, allow_equal=False)


@pytest.mark.security
def test_containment_error_preserves_required_context(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding=UTF8)

    with pytest.raises(PathContainmentError) as caught:
        require_within(
            outside,
            root,
            role="generated artifact",
            stage="pre-publication containment",
        )

    _assert_containment_error(
        caught.value,
        candidate=outside.resolve(),
        root=root.resolve(),
        role="generated artifact",
        stage="pre-publication containment",
    )


@pytest.mark.security
def test_output_containment_rejects_lexical_parent_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    escaped = root / "nested" / ".." / ".." / "outside.txt"

    with pytest.raises(PathContainmentError) as caught:
        require_within(
            escaped,
            root,
            role="run output",
            stage="pre-write containment",
            for_output=True,
        )

    assert caught.value.candidate == (tmp_path / "outside.txt").absolute()


@pytest.mark.security
def test_output_containment_rejects_symlinked_parent_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    alias = root / "external"
    _symlink_or_skip(alias, outside, directory=True)
    candidate = alias / "artifact.txt"

    assert not is_within(candidate, root, for_output=True)
    with pytest.raises(PathContainmentError):
        require_within(candidate, root, for_output=True)


def test_file_and_directory_requirements_validate_type_and_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    directory = root / "directory"
    directory.mkdir()
    file_path = root / "file.txt"
    file_path.write_text("value", encoding=UTF8)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding=UTF8)

    assert require_regular_file(file_path, root=root) == file_path.resolve()
    assert require_directory(directory, root=root) == directory.resolve()

    with pytest.raises(IsADirectoryError) as file_error:
        require_regular_file(directory, role="configuration file")
    assert file_error.value.errno == errno.EISDIR
    assert "configuration file" in str(file_error.value)

    with pytest.raises(NotADirectoryError) as directory_error:
        require_directory(file_path, role="source root")
    assert directory_error.value.errno == errno.ENOTDIR
    assert "source root" in str(directory_error.value)

    with pytest.raises(PathContainmentError):
        require_regular_file(outside, root=root)


def test_read_bytes_supports_exact_and_zero_limits(tmp_path: Path) -> None:
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"12345")

    assert read_bytes(payload) == b"12345"
    assert read_bytes(payload, max_bytes=5) == b"12345"
    assert read_bytes(empty, max_bytes=0) == b""

    with pytest.raises(OSError) as caught:
        read_bytes(payload, max_bytes=4, role="captured stream")

    assert caught.value.errno == errno.EFBIG
    assert caught.value.filename == os.fspath(payload.resolve())
    assert "captured stream" in str(caught.value)
    assert "4-byte" in str(caught.value)


@pytest.mark.parametrize(
    ("value", "error_type"),
    [
        (-1, ValueError),
        (True, TypeError),
        (False, TypeError),
        (1.0, TypeError),
        ("1", TypeError),
    ],
)
def test_read_limit_validation(
    tmp_path: Path,
    value: object,
    error_type: type[Exception],
) -> None:
    source = tmp_path / "payload.bin"
    source.write_bytes(b"x")

    with pytest.raises(error_type):
        read_bytes(source, max_bytes=cast("Any", value))


def test_read_text_uses_strict_utf8_without_newline_conversion(
    tmp_path: Path,
) -> None:
    source = tmp_path / "text.txt"
    source.write_bytes(_UTF8_TEXT.encode(UTF8))

    assert read_text(source) == _UTF8_TEXT

    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"\xff")
    with pytest.raises(UnicodeDecodeError):
        read_text(invalid)


@pytest.mark.parametrize(
    "payload",
    [
        b"bytes",
        bytearray(b"bytearray"),
        memoryview(b"memoryview"),
    ],
)
def test_write_bytes_accepts_bytes_like_payloads(
    tmp_path: Path,
    payload: bytes | bytearray | memoryview,
) -> None:
    destination = tmp_path / f"{type(payload).__name__}.bin"

    result = write_bytes(destination, payload)

    assert result == destination.resolve()
    assert destination.read_bytes() == bytes(payload)


def test_write_text_uses_utf8_and_preserves_newlines(tmp_path: Path) -> None:
    destination = tmp_path / "text.txt"

    result = write_text(destination, _UTF8_TEXT)

    assert result == destination.resolve()
    assert destination.read_bytes() == _UTF8_TEXT.encode(UTF8)
    assert not destination.read_bytes().startswith(b"\xef\xbb\xbf")

    with pytest.raises(TypeError, match="text must be str"):
        write_text(tmp_path / "invalid.txt", cast("Any", b"bytes"))


def test_write_collision_and_parent_creation_are_explicit(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"
    root.mkdir()
    destination = root / "details" / "artifact.bin"

    with pytest.raises(FileNotFoundError):
        write_bytes(destination, b"first", root=root)

    assert (
        write_bytes(
            destination,
            b"first",
            create_parents=True,
            root=root,
        )
        == destination.resolve()
    )

    with pytest.raises(FileExistsError) as caught:
        write_bytes(destination, b"second", root=root)
    assert caught.value.errno == errno.EEXIST

    write_bytes(destination, b"second", overwrite=True, root=root)
    assert destination.read_bytes() == b"second"


def test_write_rejects_directory_destination(tmp_path: Path) -> None:
    destination = tmp_path / "directory"
    destination.mkdir()

    with pytest.raises(IsADirectoryError) as caught:
        write_bytes(destination, b"value", overwrite=True)

    assert caught.value.errno == errno.EISDIR
    assert destination.is_dir()


@pytest.mark.security
def test_write_rejects_destination_symlink(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    target = root / "target.txt"
    target.write_text("stable", encoding=UTF8)
    link = root / "link.txt"
    _symlink_or_skip(link, target)

    with pytest.raises(OSError) as caught:
        write_text(link, "replacement", overwrite=True, root=root)

    assert caught.value.errno == errno.ELOOP
    assert target.read_text(encoding=UTF8) == "stable"
    assert link.is_symlink()


@pytest.mark.security
def test_write_rejects_symlinked_parent_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    alias = root / "external"
    _symlink_or_skip(alias, outside, directory=True)

    destination = alias / "artifact.txt"
    with pytest.raises(PathContainmentError):
        write_text(destination, "outside", root=root)

    assert not (outside / "artifact.txt").exists()


def test_directory_creation_honors_parents_exist_ok_and_exclusive(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    nested = root / "one" / "two"

    with pytest.raises(FileNotFoundError):
        create_directory(nested, root=root)

    created = create_directory(nested, parents=True, root=root)
    assert created == nested.resolve()

    assert create_directory(nested, exist_ok=True, root=root) == nested.resolve()

    with pytest.raises(FileExistsError):
        create_directory_exclusive(nested, root=root)

    exclusive = root / "exclusive"
    assert create_directory_exclusive(exclusive, root=root) == exclusive.resolve()


@pytest.mark.security
def test_directory_creation_rejects_escape_before_mutation(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"

    with pytest.raises(PathContainmentError):
        create_directory(outside, root=root)

    assert not outside.exists()


def test_copy_file_copies_content_and_supports_overwrite(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "destination"
    source_root.mkdir()
    destination_root.mkdir()
    source = source_root / "input.bin"
    source.write_bytes(b"source payload")
    destination = destination_root / "nested" / "output.bin"

    copied = copy_file(
        source,
        destination,
        create_parents=True,
        source_root=source_root,
        destination_root=destination_root,
    )

    assert copied == destination.resolve()
    assert destination.read_bytes() == b"source payload"

    with pytest.raises(FileExistsError):
        copy_file(
            source,
            destination,
            source_root=source_root,
            destination_root=destination_root,
        )

    source.write_bytes(b"replacement")
    copy_file(
        source,
        destination,
        overwrite=True,
        source_root=source_root,
        destination_root=destination_root,
    )
    assert destination.read_bytes() == b"replacement"


def test_copy_file_can_preserve_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    destination = tmp_path / "destination.bin"
    source.write_bytes(b"payload")
    timestamp_ns = 1_700_000_000_123_456_789
    os.utime(source, ns=(timestamp_ns, timestamp_ns))

    copy_file(source, destination, preserve_metadata=True)

    assert destination.stat().st_mtime_ns == source.stat().st_mtime_ns


def test_copy_file_rejects_same_file_and_hardlink_alias(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"payload")

    with pytest.raises(shutil.SameFileError):
        copy_file(source, source, overwrite=True)

    alias = tmp_path / "alias.bin"
    _hardlink_or_skip(alias, source)
    with pytest.raises(shutil.SameFileError):
        copy_file(source, alias, overwrite=True)


def test_copy_file_enforces_source_and_destination_roots(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source-root"
    destination_root = tmp_path / "destination-root"
    source_root.mkdir()
    destination_root.mkdir()
    outside_source = tmp_path / "outside-source.bin"
    outside_source.write_bytes(b"source")
    inside_source = source_root / "inside.bin"
    inside_source.write_bytes(b"inside")
    outside_destination = tmp_path / "outside-destination.bin"

    with pytest.raises(PathContainmentError):
        copy_file(
            outside_source,
            destination_root / "output.bin",
            source_root=source_root,
            destination_root=destination_root,
        )

    with pytest.raises(PathContainmentError):
        copy_file(
            inside_source,
            outside_destination,
            source_root=source_root,
            destination_root=destination_root,
        )

    assert not outside_destination.exists()


@pytest.mark.security
def test_copy_source_symlink_cannot_escape_source_root(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source-root"
    destination_root = tmp_path / "destination-root"
    source_root.mkdir()
    destination_root.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    link = source_root / "linked.bin"
    _symlink_or_skip(link, outside)

    with pytest.raises(PathContainmentError):
        copy_file(
            link,
            destination_root / "copy.bin",
            source_root=source_root,
            destination_root=destination_root,
        )

    assert not (destination_root / "copy.bin").exists()


def test_unlink_file_handles_missing_files_and_rejects_directories(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError) as caught:
        unlink_file(missing, role="evidence file")
    assert caught.value.errno == errno.ENOENT
    assert "evidence file" in str(caught.value)

    unlink_file(missing, missing_ok=True)

    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(IsADirectoryError) as directory_error:
        unlink_file(directory)
    assert directory_error.value.errno == errno.EISDIR
    assert directory.is_dir()


def test_unlink_file_removes_file_and_contained_symlink_only(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    file_path = root / "file.txt"
    file_path.write_text("value", encoding=UTF8)

    unlink_file(file_path, root=root)
    assert not file_path.exists()

    target = root / "target.txt"
    target.write_text("stable", encoding=UTF8)
    link = root / "link.txt"
    _symlink_or_skip(link, target)

    unlink_file(link, root=root)

    assert not os.path.lexists(link)
    assert target.read_text(encoding=UTF8) == "stable"


@pytest.mark.security
def test_unlink_file_rejects_outside_target_and_escaping_symlink(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding=UTF8)

    with pytest.raises(PathContainmentError):
        unlink_file(outside, root=root)
    assert outside.exists()

    link = root / "outside-link.txt"
    _symlink_or_skip(link, outside)
    with pytest.raises(PathContainmentError):
        unlink_file(link, root=root)
    assert link.is_symlink()
    assert outside.exists()


def test_broken_symlink_removal_is_explicitly_rejected(
    tmp_path: Path,
) -> None:
    missing_target = tmp_path / "missing-target.txt"
    link = tmp_path / "broken-link.txt"
    _symlink_or_skip(link, missing_target)

    with pytest.raises(FileNotFoundError):
        unlink_file(link)

    assert os.path.lexists(link)


def test_remove_empty_directory_is_non_recursive(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    remove_empty_directory(empty)
    assert not empty.exists()

    non_empty = tmp_path / "non-empty"
    non_empty.mkdir()
    (non_empty / "value.txt").write_text("value", encoding=UTF8)

    with pytest.raises(OSError):
        remove_empty_directory(non_empty)
    assert non_empty.is_dir()


@pytest.mark.security
def test_remove_empty_directory_rejects_links_and_root_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    target = root / "target"
    target.mkdir()
    link = root / "link"
    _symlink_or_skip(link, target, directory=True)

    with pytest.raises(OSError) as link_error:
        remove_empty_directory(link, root=root)
    assert link_error.value.errno == errno.ELOOP
    assert target.is_dir()

    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(PathContainmentError):
        remove_empty_directory(outside, root=root)
    assert outside.is_dir()


def test_junction_like_paths_are_rejected_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    original = getattr(Path, "is_junction", None)

    def is_junction(path: Path) -> bool:
        if path == candidate:
            return True
        if original is None:
            return False
        return bool(original(path))

    monkeypatch.setattr(Path, "is_junction", is_junction, raising=False)

    with pytest.raises(OSError) as caught:
        remove_empty_directory(candidate)

    assert caught.value.errno == errno.ELOOP
    assert candidate.is_dir()


def test_iter_directory_returns_stable_snapshot(tmp_path: Path) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    for name in ("zeta", "Alpha", "middle"):
        (directory / name).write_text(name, encoding=UTF8)

    entries = iter_directory(directory)

    assert isinstance(entries, tuple)
    assert [entry.name for entry in entries] == ["Alpha", "middle", "zeta"]

    (directory / "later").write_text("later", encoding=UTF8)
    assert [entry.name for entry in entries] == ["Alpha", "middle", "zeta"]


def test_iter_directory_validates_type_and_containment(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    inside = root / "inside"
    inside.mkdir()
    file_path = root / "file.txt"
    file_path.write_text("value", encoding=UTF8)
    outside = tmp_path / "outside"
    outside.mkdir()

    assert iter_directory(inside, root=root) == ()

    with pytest.raises(NotADirectoryError):
        iter_directory(file_path, root=root)

    with pytest.raises(PathContainmentError):
        iter_directory(outside, root=root)
