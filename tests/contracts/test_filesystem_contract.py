"""Contract tests for GF Wordbench filesystem and atomic-I/O primitives."""

from __future__ import annotations

import errno
import os
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.infrastructure.atomic_io import (
    atomic_binary_writer,
    atomic_text_writer,
    atomic_write_bytes,
    atomic_write_text,
)
from gf_wordbench.infrastructure.filesystem import (
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

_UTF8_PAYLOAD: Final[str] = "Grammatical Framework — café\n第二行\n"


def _symlink_or_skip(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")


def _temporary_files(directory: Path, destination_name: str) -> tuple[Path, ...]:
    return tuple(
        item
        for item in directory.iterdir()
        if item.name.startswith(f".{destination_name}.")
        and item.name.endswith(".tmp")
    )


@pytest.mark.parametrize(
    "operation",
    [
        lambda path: resolve_existing(path),
        lambda path: resolve_for_output(path),
        lambda path: require_regular_file(path),
        lambda path: require_directory(path),
        lambda path: read_bytes(path),
        lambda path: read_text(path),
        lambda path: write_bytes(path, b"x"),
        lambda path: write_text(path, "x"),
        lambda path: create_directory(path),
        lambda path: unlink_file(path),
        lambda path: remove_empty_directory(path),
        lambda path: iter_directory(path),
        lambda path: atomic_write_bytes(path, b"x"),
        lambda path: atomic_write_text(path, "x"),
    ],
)
def test_filesystem_boundaries_require_absolute_paths(operation) -> None:
    with pytest.raises(ValueError, match="must be absolute"):
        operation(Path("relative/path"))


def test_paths_reject_nul() -> None:
    with pytest.raises(ValueError, match="NUL"):
        resolve_for_output("/tmp/invalid\x00name")


def test_resolve_existing_returns_strict_absolute_path(tmp_path: Path) -> None:
    source = tmp_path / "nested" / "value.txt"
    source.parent.mkdir()
    source.write_text("value", encoding="utf-8")

    resolved = resolve_existing(source)

    assert resolved == source.resolve(strict=True)
    assert resolved.is_absolute()


def test_resolve_for_output_resolves_existing_ancestor(
    tmp_path: Path,
) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    _symlink_or_skip(alias, actual, directory=True)

    resolved = resolve_for_output(alias / "new" / "artifact.json")

    assert resolved == actual.resolve() / "new" / "artifact.json"
    assert resolved.is_absolute()


def test_containment_uses_resolved_paths(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    inside = root / "inside.txt"
    inside.write_text("inside", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")

    assert is_within(inside, root)
    assert not is_within(outside, root)

    with pytest.raises(PathContainmentError) as caught:
        require_within(
            outside,
            root,
            role="artifact",
            stage="contract test",
        )

    assert caught.value.candidate == outside.resolve()
    assert caught.value.root == root.resolve()
    assert caught.value.role == "artifact"
    assert caught.value.stage == "contract test"


def test_containment_can_reject_root_itself(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()

    assert is_within(root, root)
    assert not is_within(root, root, allow_equal=False)

    with pytest.raises(PathContainmentError):
        require_within(root, root, allow_equal=False)


def test_output_containment_rejects_parent_escape(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    escaped = root / ".." / "outside" / "artifact.txt"

    with pytest.raises(PathContainmentError):
        require_within(
            escaped,
            root,
            for_output=True,
            role="generated artifact",
        )


def test_symlink_escape_is_rejected_by_containment(tmp_path: Path) -> None:
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


def test_regular_file_and_directory_contracts(tmp_path: Path) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    file_path = tmp_path / "file.txt"
    file_path.write_text("content", encoding="utf-8")

    assert require_directory(directory) == directory.resolve()
    assert require_regular_file(file_path) == file_path.resolve()

    with pytest.raises(IsADirectoryError):
        require_regular_file(directory)
    with pytest.raises(NotADirectoryError):
        require_directory(file_path)


def test_read_bytes_enforces_maximum_size(tmp_path: Path) -> None:
    source = tmp_path / "payload.bin"
    source.write_bytes(b"12345")

    assert read_bytes(source, max_bytes=5) == b"12345"

    with pytest.raises(OSError) as caught:
        read_bytes(source, max_bytes=4)

    assert caught.value.errno == errno.EFBIG


@pytest.mark.parametrize("invalid_limit", [-1, True, 1.5, "4"])
def test_read_limit_validation(
    tmp_path: Path,
    invalid_limit: object,
) -> None:
    source = tmp_path / "payload.bin"
    source.write_bytes(b"x")

    expected = ValueError if invalid_limit == -1 else TypeError
    with pytest.raises(expected):
        read_bytes(source, max_bytes=invalid_limit)  # type: ignore[arg-type]


def test_text_io_is_strict_utf8_without_bom(tmp_path: Path) -> None:
    destination = tmp_path / "text.txt"

    written = write_text(destination, _UTF8_PAYLOAD)

    assert written == destination.resolve()
    assert destination.read_bytes() == _UTF8_PAYLOAD.encode("utf-8")
    assert not destination.read_bytes().startswith(b"\xef\xbb\xbf")
    assert read_text(destination) == _UTF8_PAYLOAD

    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"\xff")
    with pytest.raises(UnicodeDecodeError):
        read_text(invalid)


def test_write_collision_policy_is_explicit(tmp_path: Path) -> None:
    destination = tmp_path / "artifact.bin"

    write_bytes(destination, b"first")

    with pytest.raises(FileExistsError):
        write_bytes(destination, b"second")

    write_bytes(destination, b"second", overwrite=True)

    assert destination.read_bytes() == b"second"


def test_write_can_create_contained_parent_directories(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"
    root.mkdir()
    destination = root / "details" / "subject.txt"

    result = write_text(
        destination,
        "details",
        create_parents=True,
        root=root,
    )

    assert result == destination.resolve()
    assert destination.read_text(encoding="utf-8") == "details"


def test_write_rejects_destination_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "run"
    root.mkdir()
    destination = tmp_path / "outside.txt"

    with pytest.raises(PathContainmentError):
        write_text(destination, "outside", root=root)

    assert not destination.exists()


def test_write_rejects_symlink_destination(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    target = root / "target.txt"
    target.write_text("original", encoding="utf-8")
    link = root / "link.txt"
    _symlink_or_skip(link, target)

    with pytest.raises(OSError) as caught:
        write_text(link, "replacement", overwrite=True, root=root)

    assert caught.value.errno == errno.ELOOP
    assert target.read_text(encoding="utf-8") == "original"


def test_directory_creation_is_explicit_and_contained(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    nested = root / "a" / "b"

    created = create_directory(
        nested,
        parents=True,
        root=root,
    )

    assert created == nested.resolve()
    assert created.is_dir()

    with pytest.raises(FileExistsError):
        create_directory_exclusive(nested, root=root)

    with pytest.raises(PathContainmentError):
        create_directory(
            tmp_path / "outside",
            root=root,
        )


def test_copy_file_preserves_content_and_collision_policy(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "destination"
    source_root.mkdir()
    destination_root.mkdir()
    source = source_root / "input.bin"
    source.write_bytes(b"\x00\x01payload")
    destination = destination_root / "nested" / "output.bin"

    copied = copy_file(
        source,
        destination,
        create_parents=True,
        source_root=source_root,
        destination_root=destination_root,
    )

    assert copied == destination.resolve()
    assert destination.read_bytes() == source.read_bytes()

    with pytest.raises(FileExistsError):
        copy_file(
            source,
            destination,
            source_root=source_root,
            destination_root=destination_root,
        )


def test_copy_file_rejects_same_existing_file(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"value")

    with pytest.raises(OSError):
        copy_file(source, source, overwrite=True)


def test_iter_directory_is_stably_name_ordered(tmp_path: Path) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    for name in ("zeta", "alpha", "middle"):
        (directory / name).write_text(name, encoding="utf-8")

    entries = iter_directory(directory)

    assert [entry.name for entry in entries] == [
        "alpha",
        "middle",
        "zeta",
    ]


def test_unlink_file_never_removes_directory(tmp_path: Path) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    file_path = tmp_path / "file.txt"
    file_path.write_text("value", encoding="utf-8")

    unlink_file(file_path)
    assert not file_path.exists()

    unlink_file(file_path, missing_ok=True)

    with pytest.raises(IsADirectoryError):
        unlink_file(directory)

    assert directory.is_dir()


def test_remove_empty_directory_is_non_recursive(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    remove_empty_directory(empty)
    assert not empty.exists()

    non_empty = tmp_path / "non-empty"
    non_empty.mkdir()
    (non_empty / "value.txt").write_text("value", encoding="utf-8")

    with pytest.raises(OSError):
        remove_empty_directory(non_empty)

    assert non_empty.is_dir()


def test_atomic_write_replaces_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "summary.json"
    destination.write_bytes(b"old")

    result = atomic_write_bytes(
        destination,
        b'{"status":"ok"}\n',
        root=tmp_path,
        sync=False,
    )

    assert result == destination.absolute()
    assert destination.read_bytes() == b'{"status":"ok"}\n'
    assert _temporary_files(tmp_path, destination.name) == ()


def test_atomic_text_write_uses_utf8_and_lf(tmp_path: Path) -> None:
    destination = tmp_path / "summary.md"

    atomic_write_text(
        destination,
        "first\nsecond\n",
        root=tmp_path,
        sync=False,
    )

    assert destination.read_bytes() == b"first\nsecond\n"


def test_atomic_writer_does_not_publish_on_body_failure(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"stable")

    with pytest.raises(RuntimeError, match="abort publication"):
        with atomic_binary_writer(
            destination,
            root=tmp_path,
            sync=False,
        ) as stream:
            stream.write(b"partial")
            raise RuntimeError("abort publication")

    assert destination.read_bytes() == b"stable"
    assert _temporary_files(tmp_path, destination.name) == ()


def test_atomic_validator_runs_before_publication(tmp_path: Path) -> None:
    destination = tmp_path / "summary.json"
    destination.write_bytes(b"stable")
    observed: list[bytes] = []

    def reject(temporary: Path) -> None:
        observed.append(temporary.read_bytes())
        raise ValueError("schema rejected")

    with pytest.raises(ValueError, match="schema rejected"):
        atomic_write_bytes(
            destination,
            b"candidate",
            root=tmp_path,
            validator=reject,
            sync=False,
        )

    assert observed == [b"candidate"]
    assert destination.read_bytes() == b"stable"
    assert _temporary_files(tmp_path, destination.name) == ()


def test_atomic_writer_rejects_destination_symlink(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.txt"
    target.write_text("stable", encoding="utf-8")
    link = tmp_path / "link.txt"
    _symlink_or_skip(link, target)

    with pytest.raises(OSError) as caught:
        atomic_write_text(
            link,
            "replacement",
            root=tmp_path,
            sync=False,
        )

    assert caught.value.errno == errno.ELOOP
    assert target.read_text(encoding="utf-8") == "stable"


def test_atomic_writer_rejects_root_escape(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    destination = tmp_path / "outside.txt"

    with pytest.raises(PathContainmentError):
        atomic_write_text(
            destination,
            "outside",
            root=root,
            sync=False,
        )

    assert not destination.exists()


def test_atomic_writer_can_create_contained_parents(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    destination = root / "reports" / "summary.md"

    with atomic_text_writer(
        destination,
        create_parents=True,
        root=root,
        sync=False,
    ) as stream:
        stream.write("# Summary\n")

    assert destination.read_bytes() == b"# Summary\n"


def test_atomic_writer_rejects_stream_closed_by_caller(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "artifact.txt"

    with pytest.raises(ValueError, match="closed by the caller"):
        with atomic_text_writer(
            destination,
            root=tmp_path,
            sync=False,
        ) as stream:
            stream.write("incomplete")
            stream.close()

    assert not destination.exists()
    assert _temporary_files(tmp_path, destination.name) == ()
