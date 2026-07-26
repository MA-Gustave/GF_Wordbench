from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from gf_wordbench.diagnostics.parsing.locations import (
    SourceLocation,
    extract_source_location,
    match_source_location_prefix,
    normalize_source_path,
    parse_source_location,
    split_location_prefix,
)
from gf_wordbench.diagnostics.parsing.streams import (
    DiagnosticStream,
    StreamDecodePolicy,
    StreamDocument,
    StreamSelection,
    build_combined_analysis_view,
    count_text_lines,
    decode_stream_bytes,
    find_line_index,
    line_excerpt,
    make_stream_bundle,
    select_stream_documents,
    select_stream_lines,
)

pytestmark = pytest.mark.unit


def test_stream_document_preserves_line_numbers_offsets_and_evidence_path(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / "compile.out.txt"
    document = StreamDocument(
        stream=DiagnosticStream.STDOUT,
        text="alpha\r\nbeta\rgamma\n",
        evidence_path=evidence_path,
    )

    assert document.line_count == 3
    assert count_text_lines(document.text) == 3
    assert document.lines() == (
        document.lines()[0],
        document.lines()[1],
        document.lines()[2],
    )

    first, second, third = document.lines()
    assert (
        first.stream,
        first.line_number,
        first.text,
        first.start_offset,
        first.end_offset,
        first.terminated,
        first.evidence_path,
    ) == (
        DiagnosticStream.STDOUT,
        1,
        "alpha",
        0,
        5,
        True,
        evidence_path,
    )
    assert (
        second.line_number,
        second.text,
        second.start_offset,
        second.end_offset,
        second.terminated,
    ) == (2, "beta", 7, 11, True)
    assert (
        third.line_number,
        third.text,
        third.start_offset,
        third.end_offset,
        third.terminated,
    ) == (3, "gamma", 12, 17, True)


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("", 0),
        ("one", 1),
        ("one\n", 1),
        ("one\n\n", 2),
        ("one\r\ntwo\rthree\n", 3),
    ),
)
def test_line_count_does_not_invent_a_trailing_empty_line(
    text: str,
    expected: int,
) -> None:
    assert count_text_lines(text) == expected


def test_stream_bundle_keeps_stdout_and_stderr_separate_and_freezes_metadata(
    tmp_path: Path,
) -> None:
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    metadata = {"operation": "compile", "target": "GrammarEx.gf"}

    bundle = make_stream_bundle(
        "compiler banner\n",
        "GrammarEx.gf:7:3: syntax error\n",
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        stdout_truncated=False,
        stderr_truncated=True,
        metadata=metadata,
    )
    metadata["target"] = "mutated.gf"

    assert bundle.stdout.stream is DiagnosticStream.STDOUT
    assert bundle.stderr.stream is DiagnosticStream.STDERR
    assert bundle.stdout.evidence_path == stdout_path
    assert bundle.stderr.evidence_path == stderr_path
    assert bundle.stdout.byte_length == len("compiler banner\n".encode("utf-8"))
    assert bundle.stderr.truncated
    assert bundle.truncated
    assert bundle.has_text
    assert not bundle.has_decode_issues
    assert isinstance(bundle.stdout.metadata, MappingProxyType)
    assert bundle.stdout.metadata["target"] == "GrammarEx.gf"
    assert bundle.stderr.metadata["target"] == "GrammarEx.gf"

    with pytest.raises(TypeError):
        bundle.stdout.metadata["new"] = "value"  # type: ignore[index]


def test_stream_selection_is_deterministic_and_never_merges_streams() -> None:
    bundle = make_stream_bundle(
        "out-1\nout-2\n",
        "err-1\n",
    )

    assert select_stream_documents(
        bundle,
        StreamSelection.STDOUT,
    ) == (bundle.stdout,)
    assert select_stream_documents(
        bundle,
        StreamSelection.STDERR,
    ) == (bundle.stderr,)
    assert select_stream_documents(
        bundle,
        StreamSelection.EITHER,
    ) == (bundle.stdout, bundle.stderr)
    assert select_stream_documents(
        bundle,
        StreamSelection.BOTH_STRUCTURE,
    ) == (bundle.stdout, bundle.stderr)

    lines = select_stream_lines(bundle, StreamSelection.EITHER)
    assert tuple(line.source_key for line in lines) == (
        ("stdout", 1),
        ("stdout", 2),
        ("stderr", 1),
    )


def test_line_lookup_and_excerpt_remain_bound_to_stream_identity() -> None:
    bundle = make_stream_bundle(
        "out-1\nout-2\nout-3\n",
        "err-1\nerr-2\n",
    )
    lines = select_stream_lines(bundle, StreamSelection.EITHER)

    anchor = find_line_index(
        lines,
        stream=DiagnosticStream.STDERR,
        line_number=1,
    )

    assert anchor == 3
    excerpt = line_excerpt(lines, anchor, before=1, after=1)
    assert tuple(line.source_key for line in excerpt) == (
        ("stdout", 3),
        ("stderr", 1),
        ("stderr", 2),
    )
    assert find_line_index(
        lines,
        stream=DiagnosticStream.STDERR,
        line_number=9,
    ) is None


def test_strict_utf8_decode_rejects_invalid_evidence() -> None:
    with pytest.raises(UnicodeDecodeError):
        decode_stream_bytes(
            DiagnosticStream.STDERR,
            b"valid\xffinvalid",
            policy=StreamDecodePolicy.STRICT_UTF8,
        )


def test_lossy_utf8_decode_records_exact_invalid_byte_spans(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / "compile.err.txt"

    document = decode_stream_bytes(
        "stderr",
        b"ok\xffbad\xe2\x82",
        evidence_path=evidence_path,
        policy="replace-invalid-utf8",
        truncated=True,
    )

    assert document.stream is DiagnosticStream.STDERR
    assert document.text == "ok\uFFFDbad\uFFFD"
    assert document.encoding == "utf-8"
    assert document.byte_length == 8
    assert document.truncated
    assert document.evidence_path == evidence_path
    assert tuple(
        (issue.stream, issue.start, issue.end)
        for issue in document.decode_issues
    ) == (
        (DiagnosticStream.STDERR, 2, 3),
        (DiagnosticStream.STDERR, 6, 8),
    )


def test_combined_analysis_view_is_mapped_but_not_chronological() -> None:
    bundle = make_stream_bundle("out\n", "error")
    separator = "\n<stderr>\n"

    view = build_combined_analysis_view(
        bundle,
        separator=separator,
    )

    assert view.text == f"out\n{separator}error"
    assert view.stream_order == (
        DiagnosticStream.STDOUT,
        DiagnosticStream.STDERR,
    )
    assert view.chronology_known is False

    stdout_segment = view.segment_for(DiagnosticStream.STDOUT)
    stderr_segment = view.segment_for("stderr")
    assert stdout_segment is not None
    assert stderr_segment is not None
    assert (
        stdout_segment.combined_start,
        stdout_segment.combined_end,
        stdout_segment.source_start,
        stdout_segment.source_end,
    ) == (0, 4, 0, 4)
    assert (
        stderr_segment.combined_start,
        stderr_segment.combined_end,
        stderr_segment.source_start,
        stderr_segment.source_end,
    ) == (4 + len(separator), len(view.text), 0, 5)

    assert view.source_at(1) == (DiagnosticStream.STDOUT, 1)
    assert view.source_at(4) is None
    assert view.source_at(stderr_segment.combined_start + 2) == (
        DiagnosticStream.STDERR,
        2,
    )
    assert view.source_at(len(view.text)) is None


def test_combined_view_can_exclude_empty_streams() -> None:
    bundle = make_stream_bundle("", "only stderr")

    view = build_combined_analysis_view(
        bundle,
        include_empty_streams=False,
    )

    assert view.text == "only stderr"
    assert len(view.segments) == 1
    assert view.segments[0].stream is DiagnosticStream.STDERR
    assert view.segments[0].combined_start == 0


@pytest.mark.parametrize(
    (
        "text",
        "raw_path",
        "normalized_path",
        "line",
        "column",
        "end_line",
        "end_column",
    ),
    (
        (
            "lib/src/example/GrammarEx.gf:42",
            "lib/src/example/GrammarEx.gf",
            "lib/src/example/GrammarEx.gf",
            42,
            None,
            None,
            None,
        ),
        (
            "/workspace/project/lib/src/GrammarEx.gf:42:7",
            "/workspace/project/lib/src/GrammarEx.gf",
            "lib/src/GrammarEx.gf",
            42,
            7,
            None,
            None,
        ),
        (
            r"C:\workspace\project\lib\src\GrammarEx.gf:42:7",
            r"C:\workspace\project\lib\src\GrammarEx.gf",
            "lib/src/GrammarEx.gf",
            42,
            7,
            None,
            None,
        ),
        (
            "lib/src/GrammarEx.gf:42:7-15",
            "lib/src/GrammarEx.gf",
            "lib/src/GrammarEx.gf",
            42,
            7,
            42,
            15,
        ),
        (
            "lib/src/GrammarEx.gf:42:7-44:3",
            "lib/src/GrammarEx.gf",
            "lib/src/GrammarEx.gf",
            42,
            7,
            44,
            3,
        ),
        (
            "lib/src/GrammarEx.gf:42-44",
            "lib/src/GrammarEx.gf",
            "lib/src/GrammarEx.gf",
            42,
            None,
            44,
            None,
        ),
    ),
)
def test_source_location_parser_preserves_paths_and_coordinates(
    text: str,
    raw_path: str,
    normalized_path: str,
    line: int,
    column: int | None,
    end_line: int | None,
    end_column: int | None,
) -> None:
    project_root: str | None
    if text.startswith("/"):
        project_root = "/workspace/project"
    elif text.startswith("C:"):
        project_root = r"C:\workspace\project"
    else:
        project_root = None

    location = parse_source_location(
        text,
        project_root=project_root,
    )

    assert location == SourceLocation(
        source_path_raw=raw_path,
        source_path_normalized=normalized_path,
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
    )


def test_windows_paths_with_spaces_and_unicode_are_supported() -> None:
    text = (
        r"C:\workspace with spaces\project\lib\src\GrammaireÉ.gf"
        ":12:4"
    )

    location = parse_source_location(
        text,
        project_root=r"C:\workspace with spaces\project",
    )

    assert location is not None
    assert location.source_path_raw == (
        r"C:\workspace with spaces\project\lib\src\GrammaireÉ.gf"
    )
    assert location.source_path_normalized == "lib/src/GrammaireÉ.gf"
    assert location.line == 12
    assert location.column == 4


def test_quoted_paths_with_spaces_are_supported() -> None:
    location = parse_source_location(
        r'"C:\workspace with spaces\GrammarEx.gf":9:2',
    )

    assert location is not None
    assert location.source_path_raw == (
        r"C:\workspace with spaces\GrammarEx.gf"
    )
    assert location.source_path_normalized == (
        "C:/workspace with spaces/GrammarEx.gf"
    )
    assert (location.line, location.column) == (9, 2)


def test_prefix_split_preserves_message_and_structured_location() -> None:
    text = "lib/src/GrammarEx.gf:17:6: unknown identifier"

    location, message = split_location_prefix(text)

    assert location is not None
    assert location.source_path_raw == "lib/src/GrammarEx.gf"
    assert location.source_path_normalized == "lib/src/GrammarEx.gf"
    assert (location.line, location.column) == (17, 6)
    assert message == "unknown identifier"


def test_embedded_location_extraction_reports_the_exact_source_span() -> None:
    text = (
        "GF error at "
        r"C:\workspace\project\lib\src\GrammarEx.gf:23:5"
        " while compiling"
    )

    matched = extract_source_location(
        text,
        project_root=r"C:\workspace\project",
        allow_embedded=True,
    )

    assert matched is not None
    assert matched.matched_text == (
        r"C:\workspace\project\lib\src\GrammarEx.gf:23:5"
    )
    assert text[matched.start : matched.end] == matched.matched_text
    assert matched.location.source_path_raw == (
        r"C:\workspace\project\lib\src\GrammarEx.gf"
    )
    assert matched.location.source_path_normalized == (
        "lib/src/GrammarEx.gf"
    )


def test_prefix_match_does_not_accept_command_echo_without_coordinates() -> None:
    assert match_source_location_prefix(
        "gf -make lib/src/GrammarEx.gf",
    ) is None
    assert parse_source_location("lib/src/GrammarEx.gf") is None


@pytest.mark.parametrize(
    ("raw_path", "project_root", "expected"),
    (
        (
            r"C:\workspace\project\lib\src\GrammarEx.gf",
            r"C:\workspace\project",
            "lib/src/GrammarEx.gf",
        ),
        (
            r"c:\WORKSPACE\PROJECT\lib\src\GrammarEx.gf",
            r"C:\workspace\project",
            "lib/src/GrammarEx.gf",
        ),
        (
            "/workspace/project/lib/src/GrammarEx.gf",
            "/workspace/project",
            "lib/src/GrammarEx.gf",
        ),
        (
            "/outside/GrammarEx.gf",
            "/workspace/project",
            "/outside/GrammarEx.gf",
        ),
        (
            r"C:\outside\GrammarEx.gf",
            r"D:\workspace\project",
            "C:/outside/GrammarEx.gf",
        ),
    ),
)
def test_path_normalization_is_lexical_and_only_relativizes_contained_paths(
    raw_path: str,
    project_root: str,
    expected: str,
) -> None:
    assert normalize_source_path(
        raw_path,
        project_root=project_root,
    ) == expected


@pytest.mark.parametrize(
    "text",
    (
        "GrammarEx.gf:0",
        "GrammarEx.gf:1:0",
        "GrammarEx.txt:1:1",
        "not a location",
    ),
)
def test_invalid_or_unsupported_location_text_is_not_invented(
    text: str,
) -> None:
    assert parse_source_location(text) is None


def test_location_input_rejects_nul_and_invalid_suffix_contracts() -> None:
    with pytest.raises(ValueError, match="NUL"):
        parse_source_location("GrammarEx.gf:1\x00")

    with pytest.raises(TypeError, match="iterable"):
        parse_source_location(
            "GrammarEx.gf:1",
            allowed_suffixes=".gf",
        )

    with pytest.raises(ValueError, match="at least one"):
        parse_source_location(
            "GrammarEx.gf:1",
            allowed_suffixes=(),
        )
