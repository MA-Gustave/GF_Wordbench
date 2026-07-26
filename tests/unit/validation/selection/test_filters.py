"""Unit tests for canonical GF source-selection filters."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

import pytest

from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.validation.selection import filters as filters_module
from gf_wordbench.validation.selection.filters import (
    CandidateFilterDecision,
    CompiledSourceFilters,
    EXCLUDED_BY_LIMIT,
    EXCLUDED_BY_REGEX,
    MISSING_FILE,
    NOT_A_FILE,
    NOT_GF_FILE,
    NOT_MATCHED_BY_INCLUDE_REGEX,
    OUTSIDE_PROJECT_ROOT,
    OUTSIDE_SOURCE_ROOT,
    UNREADABLE_FILE,
    apply_diagnostic_limit,
    candidate_exclusion_reason,
    compile_optional_regex,
    compile_source_filters,
    filter_candidate_files,
    is_included_file,
    matches_source_glob,
    normalize_source_glob,
)


def _project_tree(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project with spaces"
    source_root = project_root / "lib" / "src" / "example"
    source_root.mkdir(parents=True)
    return project_root, source_root


def _write(path: Path, text: str = "abstract Main = {}\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _no_filters() -> CompiledSourceFilters:
    return compile_source_filters(include_regex=None, exclude_regex=None)


def test_compile_optional_regex_treats_empty_values_as_no_rule() -> None:
    assert compile_optional_regex(None, field_name="include") is None
    assert compile_optional_regex("", field_name="include") is None
    assert compile_optional_regex("   ", field_name="include") is None

    compiled = compile_optional_regex(r"^[A-Z].*\.gf$", field_name="include")
    assert isinstance(compiled, re.Pattern)
    assert compiled.pattern == r"^[A-Z].*\.gf$"


def test_compile_optional_regex_rejects_invalid_or_unsafe_values() -> None:
    with pytest.raises(TypeError, match="must be a string or None"):
        compile_optional_regex(3, field_name="sources.include_regex")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must not contain NUL"):
        compile_optional_regex("A\x00B", field_name="sources.include_regex")

    with pytest.raises(ConfigurationError, match="not a valid regular expression") as caught:
        compile_optional_regex("[", field_name="sources.exclude_regex")

    assert caught.value.stage == "selection"
    assert caught.value.operation == "compile_regex"
    assert caught.value.subject == "sources.exclude_regex"
    assert caught.value.detail


def test_compiled_filters_apply_exclude_before_include() -> None:
    filters = compile_source_filters(
        include_regex=r"\.gf$",
        exclude_regex=r"\.disabled\.gf$",
    )

    assert filters.exclusion_reason(
        file_name="Grammar.disabled.gf",
        project_relative_path="lib/src/Grammar.disabled.gf",
    ) == EXCLUDED_BY_REGEX


def test_compiled_filters_search_filename_and_project_relative_path() -> None:
    filename_filter = compile_source_filters(
        include_regex=r"^Grammar[A-Z].*\.gf$",
        exclude_regex=None,
    )
    assert filename_filter.exclusion_reason(
        file_name="GrammarExample.gf",
        project_relative_path="lib/src/example/GrammarExample.gf",
    ) is None

    path_filter = compile_source_filters(
        include_regex=r"/syntax/",
        exclude_regex=None,
    )
    assert path_filter.exclusion_reason(
        file_name="SyntaxExample.gf",
        project_relative_path="lib/src/example/syntax/SyntaxExample.gf",
    ) is None
    assert path_filter.exclusion_reason(
        file_name="MorphoExample.gf",
        project_relative_path="lib/src/example/MorphoExample.gf",
    ) == NOT_MATCHED_BY_INCLUDE_REGEX


def test_regex_matching_is_case_sensitive_unless_pattern_requests_otherwise() -> None:
    sensitive = compile_source_filters(
        include_regex=r"^grammar\.gf$",
        exclude_regex=None,
    )
    insensitive = compile_source_filters(
        include_regex=r"(?i)^grammar\.gf$",
        exclude_regex=None,
    )

    arguments = {
        "file_name": "Grammar.gf",
        "project_relative_path": "lib/src/Grammar.gf",
    }
    assert sensitive.exclusion_reason(**arguments) == NOT_MATCHED_BY_INCLUDE_REGEX
    assert insensitive.exclusion_reason(**arguments) is None


def test_source_glob_validation_and_matching_are_portable() -> None:
    assert normalize_source_glob("*.gf") == "*.gf"
    assert matches_source_glob("lib/src/Main.gf") is True
    assert matches_source_glob(PurePosixPath("lib/src/nested/Main.gf")) is True
    assert matches_source_glob("lib/src/Main.gfo") is False
    assert matches_source_glob("lib/src/Main.gf", "lib/src/*.gf") is True

    with pytest.raises(ConfigurationError, match="must not be empty"):
        normalize_source_glob("  ")
    with pytest.raises(TypeError, match="must be a string"):
        normalize_source_glob(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must not contain NUL"):
        normalize_source_glob("*.gf\x00")
    with pytest.raises(ValueError, match="contained relative path"):
        matches_source_glob("../Main.gf")


def test_candidate_decision_enforces_canonical_shape(tmp_path: Path) -> None:
    resolved = (tmp_path / "Main.gf").resolve()
    selected = CandidateFilterDecision(
        candidate_path=resolved,
        resolved_path=resolved,
        project_relative_path="lib/src/Main.gf",
        excluded_reason=None,
    )
    excluded = CandidateFilterDecision(
        candidate_path=resolved,
        resolved_path=resolved,
        project_relative_path="lib/src/Main.gf",
        excluded_reason=EXCLUDED_BY_REGEX,
    )

    assert selected.selected is True
    assert excluded.selected is False

    with pytest.raises(ValueError, match="requires project_relative_path"):
        CandidateFilterDecision(
            candidate_path=resolved,
            resolved_path=resolved,
            project_relative_path=None,
            excluded_reason=None,
        )
    with pytest.raises(ValueError, match="POSIX separators"):
        CandidateFilterDecision(
            candidate_path=resolved,
            resolved_path=resolved,
            project_relative_path=r"lib\src\Main.gf",
            excluded_reason=EXCLUDED_BY_REGEX,
        )
    with pytest.raises(ValueError, match="contained and relative"):
        CandidateFilterDecision(
            candidate_path=resolved,
            resolved_path=resolved,
            project_relative_path="../Main.gf",
            excluded_reason=EXCLUDED_BY_REGEX,
        )
    with pytest.raises(ValueError, match="unsupported exclusion reason"):
        CandidateFilterDecision(
            candidate_path=resolved,
            resolved_path=resolved,
            project_relative_path="Main.gf",
            excluded_reason="other",  # type: ignore[arg-type]
        )


def test_candidate_hard_checks_use_canonical_order(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)
    missing = source_root / "Missing.gf"
    directory = source_root / "Directory.gf"
    directory.mkdir()
    non_gf = _write(source_root / "README.md")
    project_only = _write(project_root / "outside-source" / "Other.gf")
    external = _write(tmp_path / "external" / "External.gf")

    cases = (
        (missing, MISSING_FILE, None),
        (directory, NOT_A_FILE, None),
        (non_gf, NOT_GF_FILE, "lib/src/example/README.md"),
        (project_only, OUTSIDE_SOURCE_ROOT, "outside-source/Other.gf"),
        (external, OUTSIDE_PROJECT_ROOT, None),
    )

    for candidate, expected_reason, expected_relative in cases:
        decision = candidate_exclusion_reason(
            candidate,
            project_root=project_root,
            source_root=source_root,
            filters=_no_filters(),
        )
        assert decision.excluded_reason == expected_reason
        assert decision.project_relative_path == expected_relative
        assert decision.selected is False
        assert decision.resolved_path.is_absolute()


def test_candidate_selection_returns_absolute_path_and_posix_display_path(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    candidate = _write(source_root / "nested" / "GrammaireÉ.gf")

    decision = candidate_exclusion_reason(
        candidate,
        project_root=project_root,
        source_root=source_root,
        filters=_no_filters(),
    )

    assert decision.selected is True
    assert decision.resolved_path == candidate.resolve()
    assert decision.resolved_path.is_absolute()
    assert decision.project_relative_path == "lib/src/example/nested/GrammaireÉ.gf"
    assert "\\" not in decision.project_relative_path


def test_candidate_regex_filtering_uses_resolved_project_relative_path(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    accepted = _write(source_root / "syntax" / "SyntaxExample.gf")
    excluded = _write(source_root / "generated" / "GeneratedExample.gf")
    filters = compile_source_filters(
        include_regex=r"/syntax/|^GeneratedExample\.gf$",
        exclude_regex=r"/generated/",
    )

    assert candidate_exclusion_reason(
        accepted,
        project_root=project_root,
        source_root=source_root,
        filters=filters,
    ).selected
    assert candidate_exclusion_reason(
        excluded,
        project_root=project_root,
        source_root=source_root,
        filters=filters,
    ).excluded_reason == EXCLUDED_BY_REGEX


def test_candidate_unreadable_file_is_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    candidate = _write(source_root / "Main.gf")
    real_access = filters_module.os.access

    def fake_access(path: object, mode: int) -> bool:
        if Path(path) == candidate.resolve():
            return False
        return real_access(path, mode)

    monkeypatch.setattr(filters_module.os, "access", fake_access)

    decision = candidate_exclusion_reason(
        candidate,
        project_root=project_root,
        source_root=source_root,
        filters=_no_filters(),
    )
    assert decision.excluded_reason == UNREADABLE_FILE
    assert decision.project_relative_path == "lib/src/example/Main.gf"


def test_source_root_must_remain_inside_project_root(tmp_path: Path) -> None:
    project_root, _ = _project_tree(tmp_path)
    external_source_root = tmp_path / "external-source"
    external_source_root.mkdir()
    candidate = _write(external_source_root / "Main.gf")

    with pytest.raises(ConfigurationError, match="must remain inside project_root") as caught:
        candidate_exclusion_reason(
            candidate,
            project_root=project_root,
            source_root=external_source_root,
            filters=_no_filters(),
        )

    assert caught.value.stage == "selection"
    assert caught.value.operation == "validate_roots"
    assert caught.value.subject == str(external_source_root.resolve())


def test_filter_candidate_files_preserves_order_and_records_every_decision(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    first = _write(source_root / "B.gf")
    excluded = _write(source_root / "Backup.tmp.gf")
    second = _write(source_root / "A.gf")

    selected, decisions = filter_candidate_files(
        (first, excluded, second),
        project_root=project_root,
        source_root=source_root,
        include_regex=r"\.gf$",
        exclude_regex=r"\.tmp\.gf$",
    )

    assert selected == (first.resolve(), second.resolve())
    assert tuple(decision.candidate_path for decision in decisions) == (
        first,
        excluded,
        second,
    )
    assert tuple(decision.excluded_reason for decision in decisions) == (
        None,
        EXCLUDED_BY_REGEX,
        None,
    )


def test_filter_candidate_files_escalates_required_exclusion(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)
    excluded = _write(source_root / "Main.disabled.gf")

    with pytest.raises(ConfigurationError, match="required target is not selectable") as caught:
        filter_candidate_files(
            (excluded,),
            project_root=project_root,
            source_root=source_root,
            exclude_regex=r"\.disabled\.gf$",
            required=True,
        )

    assert caught.value.stage == "selection"
    assert caught.value.operation == "filter_required_target"
    assert caught.value.subject == str(excluded)


def test_filter_candidate_files_validates_collection_contract(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)

    with pytest.raises(TypeError, match="iterable of paths"):
        filter_candidate_files(
            source_root / "Main.gf",
            project_root=project_root,
            source_root=source_root,
        )
    with pytest.raises(TypeError, match="required must be a bool"):
        filter_candidate_files(
            (),
            project_root=project_root,
            source_root=source_root,
            required=1,  # type: ignore[arg-type]
        )


def test_is_included_file_is_a_boolean_convenience_boundary(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)
    selected = _write(source_root / "Main.gf")
    excluded = _write(source_root / "Main.bak.gf")

    assert is_included_file(
        selected,
        project_root=project_root,
        source_root=source_root,
        include_regex=r"^Main.*\.gf$",
        exclude_regex=r"\.bak\.gf$",
    ) is True
    assert is_included_file(
        excluded,
        project_root=project_root,
        source_root=source_root,
        include_regex=r"^Main.*\.gf$",
        exclude_regex=r"\.bak\.gf$",
    ) is False


def test_diagnostic_limit_zero_and_large_values_are_unlimited(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)
    paths = tuple(
        _write(source_root / name).resolve()
        for name in ("A.gf", "B.gf", "C.gf")
    )

    assert apply_diagnostic_limit(
        paths,
        max_files=0,
        project_root=project_root,
    ) == (paths, ())
    assert apply_diagnostic_limit(
        paths,
        max_files=3,
        project_root=project_root,
    ) == (paths, ())
    assert apply_diagnostic_limit(
        paths,
        max_files=10,
        project_root=project_root,
    ) == (paths, ())


def test_diagnostic_limit_preserves_order_and_accounts_for_overflow(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    paths = tuple(
        _write(source_root / name).resolve()
        for name in ("A.gf", "B.gf", "C.gf")
    )

    selected, overflow = apply_diagnostic_limit(
        paths,
        max_files=2,
        project_root=project_root,
    )

    assert selected == paths[:2]
    assert len(overflow) == 1
    assert overflow[0].candidate_path == paths[2]
    assert overflow[0].resolved_path == paths[2]
    assert overflow[0].project_relative_path == "lib/src/example/C.gf"
    assert overflow[0].excluded_reason == EXCLUDED_BY_LIMIT
    assert overflow[0].selected is False


def test_diagnostic_limit_rejects_invalid_limit_and_escaped_path(
    tmp_path: Path,
) -> None:
    project_root, source_root = _project_tree(tmp_path)
    inside = _write(source_root / "A.gf").resolve()
    outside = _write(tmp_path / "outside" / "B.gf").resolve()

    with pytest.raises(TypeError, match="must be an integer"):
        apply_diagnostic_limit(
            (inside,),
            max_files=True,  # type: ignore[arg-type]
            project_root=project_root,
        )
    with pytest.raises(ConfigurationError, match="must be non-negative") as negative:
        apply_diagnostic_limit(
            (inside,),
            max_files=-1,
            project_root=project_root,
        )
    assert negative.value.operation == "apply_limit"

    with pytest.raises(ConfigurationError, match="escaped project_root") as escaped:
        apply_diagnostic_limit(
            (inside, outside),
            max_files=1,
            project_root=project_root,
        )
    assert escaped.value.subject == str(outside)


def test_filtering_is_read_only_and_creates_no_output_directories(tmp_path: Path) -> None:
    project_root, source_root = _project_tree(tmp_path)
    candidate = _write(source_root / "Main.gf", "abstract Main = {}\n")
    original = candidate.read_bytes()
    output_root = project_root / "_gf_wordbench"

    selected, decisions = filter_candidate_files(
        (candidate,),
        project_root=project_root,
        source_root=source_root,
    )

    assert selected == (candidate.resolve(),)
    assert decisions[0].selected
    assert candidate.read_bytes() == original
    assert not output_root.exists()
