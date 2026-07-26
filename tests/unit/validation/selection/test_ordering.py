"""Unit tests for deterministic validation-target ordering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest

from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.validation.selection import ordering
from gf_wordbench.validation.selection.ordering import (
    DiagnosticLimitResult,
    apply_diagnostic_limit,
    deduplicate_preserving_order,
    diagnostic_sort_key,
    order_checkpoints,
    order_diagnostic,
    order_excluded_diagnostic,
    order_excluded_explicit,
    order_for_mode,
    order_quick,
    order_release,
    ordered_union,
    project_relative_posix_path,
    resolved_identity_key,
)

_EXPECTED_PUBLIC_NAMES = (
    "DiagnosticLimitResult",
    "apply_diagnostic_limit",
    "deduplicate_preserving_order",
    "diagnostic_sort_key",
    "order_checkpoints",
    "order_diagnostic",
    "order_excluded_diagnostic",
    "order_excluded_explicit",
    "order_for_mode",
    "order_quick",
    "order_release",
    "ordered_union",
    "project_relative_posix_path",
    "resolved_identity_key",
)


@dataclass(frozen=True, slots=True)
class _Candidate:
    candidate_id: str
    path: Path


def _candidate(candidate_id: str, path: Path) -> _Candidate:
    return _Candidate(candidate_id=candidate_id, path=path)


def _path(candidate: _Candidate) -> Path:
    return candidate.path


def test_module_exposes_only_the_canonical_ordering_api() -> None:
    assert ordering.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(ordering, name) for name in ordering.__all__)


def test_resolved_identity_key_normalizes_equivalent_absolute_paths(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "src" / "Main.gf"
    equivalent = tmp_path / "src" / "nested" / ".." / "Main.gf"

    assert resolved_identity_key(canonical) == resolved_identity_key(equivalent)


def test_resolved_identity_key_does_not_require_the_path_to_exist(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "src" / "Missing.gf"

    key = resolved_identity_key(missing)

    assert isinstance(key, str)
    assert key
    assert Path(key).is_absolute()


@pytest.mark.parametrize("value", ["Main.gf", b"Main.gf", None])
def test_resolved_identity_key_requires_a_path(value: object) -> None:
    with pytest.raises(TypeError, match="path must be a pathlib.Path"):
        resolved_identity_key(value)  # type: ignore[arg-type]


def test_resolved_identity_key_requires_an_absolute_path() -> None:
    with pytest.raises(ValueError, match="path must be absolute"):
        resolved_identity_key(Path("src/Main.gf"))


def test_resolved_identity_key_rejects_nul_characters(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not contain NUL"):
        resolved_identity_key(tmp_path / "bad\x00name.gf")


def test_project_relative_posix_path_returns_portable_project_path(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "project" / "src"
    source_path = source_root / "grammar" / "Été.gf"

    relative = project_relative_posix_path(
        source_path,
        source_root=source_root,
    )

    assert relative == PurePosixPath("grammar/Été.gf")
    assert relative.as_posix() == "grammar/Été.gf"


def test_project_relative_posix_path_accepts_the_source_root_itself(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"

    assert project_relative_posix_path(
        source_root,
        source_root=source_root,
    ) == PurePosixPath(".")


def test_project_relative_posix_path_rejects_path_outside_source_root(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "project" / "src"
    outside = tmp_path / "other" / "Main.gf"

    with pytest.raises(ValueError, match="path is outside source_root"):
        project_relative_posix_path(outside, source_root=source_root)


@pytest.mark.parametrize(
    ("path", "source_root", "message"),
    [
        (Path("Main.gf"), Path("/source"), "path must be absolute"),
        (Path("/source/Main.gf"), Path("source"), "source_root must be absolute"),
    ],
)
def test_project_relative_posix_path_requires_absolute_inputs(
    path: Path,
    source_root: Path,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        project_relative_posix_path(path, source_root=source_root)


def test_diagnostic_sort_key_uses_casefold_then_exact_path(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"

    assert diagnostic_sort_key(
        source_root / "Grammar" / "Main.gf",
        source_root=source_root,
    ) == ("grammar/main.gf", "Grammar/Main.gf")


def test_deduplicate_preserving_order_keeps_first_resolved_identity(
    tmp_path: Path,
) -> None:
    first = _candidate("first", tmp_path / "src" / "Main.gf")
    alias = _candidate(
        "alias",
        tmp_path / "src" / "nested" / ".." / "Main.gf",
    )
    second = _candidate("second", tmp_path / "src" / "Other.gf")

    result = deduplicate_preserving_order(
        (first, alias, second, first),
        path_getter=_path,
    )

    assert result == (first, second)
    assert result[0] is first


def test_deduplicate_preserving_order_accepts_one_shot_iterables(
    tmp_path: Path,
) -> None:
    candidates = (
        _candidate(str(index), tmp_path / f"{index}.gf")
        for index in range(3)
    )

    result = deduplicate_preserving_order(candidates, path_getter=_path)

    assert tuple(item.candidate_id for item in result) == ("0", "1", "2")


def test_deduplicate_preserving_order_rejects_string_iterables() -> None:
    with pytest.raises(TypeError, match="items must be an iterable of items"):
        deduplicate_preserving_order("Main.gf", path_getter=lambda value: value)  # type: ignore[arg-type,return-value]


def test_deduplicate_preserving_order_requires_callable_path_getter(
    tmp_path: Path,
) -> None:
    candidate = _candidate("main", tmp_path / "Main.gf")

    with pytest.raises(TypeError, match="path_getter must be callable"):
        deduplicate_preserving_order(
            (candidate,),
            path_getter=None,  # type: ignore[arg-type]
        )


def test_deduplicate_preserving_order_requires_path_results(
    tmp_path: Path,
) -> None:
    candidate = _candidate("main", tmp_path / "Main.gf")

    with pytest.raises(
        TypeError,
        match="path_getter must return pathlib.Path values",
    ):
        deduplicate_preserving_order(
            (candidate,),
            path_getter=lambda item: str(item.path),  # type: ignore[return-value]
        )


def test_ordered_union_preserves_first_list_then_new_second_items(
    tmp_path: Path,
) -> None:
    checkpoint_a = _candidate("checkpoint-a", tmp_path / "A.gf")
    checkpoint_b = _candidate("checkpoint-b", tmp_path / "B.gf")
    duplicate_b = _candidate("entrypoint-b", tmp_path / "." / "B.gf")
    entrypoint_c = _candidate("entrypoint-c", tmp_path / "C.gf")

    result = ordered_union(
        (checkpoint_a, checkpoint_b),
        (duplicate_b, entrypoint_c),
        path_getter=_path,
    )

    assert result == (checkpoint_a, checkpoint_b, entrypoint_c)


def test_order_quick_requires_exactly_one_deduplicated_target(
    tmp_path: Path,
) -> None:
    first = _candidate("first", tmp_path / "Main.gf")
    duplicate = _candidate("duplicate", tmp_path / "." / "Main.gf")

    assert order_quick((first, duplicate), path_getter=_path) == (first,)

    with pytest.raises(
        ValueError,
        match="quick mode requires exactly one selected target",
    ):
        order_quick((), path_getter=_path)

    with pytest.raises(
        ValueError,
        match="quick mode requires exactly one selected target",
    ):
        order_quick(
            (first, _candidate("other", tmp_path / "Other.gf")),
            path_getter=_path,
        )


def test_order_checkpoints_preserves_declared_order_and_deduplicates(
    tmp_path: Path,
) -> None:
    second = _candidate("second", tmp_path / "Second.gf")
    first = _candidate("first", tmp_path / "First.gf")
    duplicate_second = _candidate("duplicate", tmp_path / "." / "Second.gf")

    assert order_checkpoints(
        (second, first, duplicate_second),
        path_getter=_path,
    ) == (second, first)


def test_order_release_is_ordered_checkpoint_entrypoint_union(
    tmp_path: Path,
) -> None:
    checkpoint_a = _candidate("checkpoint-a", tmp_path / "A.gf")
    checkpoint_b = _candidate("checkpoint-b", tmp_path / "B.gf")
    overlapping_entrypoint = _candidate("entrypoint-b", tmp_path / "B.gf")
    entrypoint_c = _candidate("entrypoint-c", tmp_path / "C.gf")

    assert order_release(
        (checkpoint_a, checkpoint_b),
        (overlapping_entrypoint, entrypoint_c),
        path_getter=_path,
    ) == (checkpoint_a, checkpoint_b, entrypoint_c)


def test_order_diagnostic_deduplicates_before_relative_path_sorting(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    zeta = _candidate("zeta", source_root / "zeta.gf")
    alpha = _candidate("alpha", source_root / "Alpha.gf")
    beta = _candidate("beta", source_root / "nested" / "beta.gf")
    duplicate_alpha = _candidate(
        "duplicate-alpha",
        source_root / "nested" / ".." / "Alpha.gf",
    )

    result = order_diagnostic(
        (zeta, duplicate_alpha, beta, alpha),
        source_root=source_root,
        path_getter=_path,
    )

    assert result == (duplicate_alpha, beta, zeta)


def test_order_diagnostic_uses_exact_path_as_casefold_tie_breaker(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    lowercase = _candidate("lower", source_root / "a.gf")
    uppercase = _candidate("upper", source_root / "A.gf")

    if resolved_identity_key(lowercase.path) == resolved_identity_key(uppercase.path):
        pytest.skip("case-insensitive filesystem identity collapses case variants")

    assert order_diagnostic(
        (lowercase, uppercase),
        source_root=source_root,
        path_getter=_path,
    ) == (uppercase, lowercase)


def test_order_diagnostic_rejects_candidates_outside_source_root(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    outside = _candidate("outside", tmp_path / "other" / "Main.gf")

    with pytest.raises(ValueError, match="path is outside source_root"):
        order_diagnostic(
            (outside,),
            source_root=source_root,
            path_getter=_path,
        )


def test_diagnostic_limit_result_normalizes_sequences_to_tuples(
    tmp_path: Path,
) -> None:
    selected = _candidate("selected", tmp_path / "Selected.gf")
    overflow = _candidate("overflow", tmp_path / "Overflow.gf")

    result = DiagnosticLimitResult(
        selected=[selected],  # type: ignore[arg-type]
        overflow=[overflow],  # type: ignore[arg-type]
    )

    assert result.selected == (selected,)
    assert result.overflow == (overflow,)


def test_diagnostic_limit_result_rejects_same_object_in_both_groups(
    tmp_path: Path,
) -> None:
    candidate = _candidate("same", tmp_path / "Same.gf")

    with pytest.raises(
        ValueError,
        match="selected and overflow must not contain the same object",
    ):
        DiagnosticLimitResult(
            selected=(candidate,),
            overflow=(candidate,),
        )


def test_apply_diagnostic_limit_zero_means_unlimited(tmp_path: Path) -> None:
    candidates = tuple(
        _candidate(str(index), tmp_path / f"{index}.gf")
        for index in range(3)
    )

    result = apply_diagnostic_limit(candidates, max_files=0)

    assert result.selected == candidates
    assert result.overflow == ()


def test_apply_diagnostic_limit_splits_after_the_selected_prefix(
    tmp_path: Path,
) -> None:
    candidates = tuple(
        _candidate(str(index), tmp_path / f"{index}.gf")
        for index in range(4)
    )

    result = apply_diagnostic_limit(candidates, max_files=2)

    assert result.selected == candidates[:2]
    assert result.overflow == candidates[2:]


def test_apply_diagnostic_limit_larger_than_input_has_no_overflow(
    tmp_path: Path,
) -> None:
    candidate = _candidate("main", tmp_path / "Main.gf")

    assert apply_diagnostic_limit(
        (candidate,),
        max_files=10,
    ) == DiagnosticLimitResult(selected=(candidate,), overflow=())


@pytest.mark.parametrize("max_files", [-1, -100])
def test_apply_diagnostic_limit_rejects_negative_limits(
    max_files: int,
) -> None:
    with pytest.raises(ValueError, match="max_files must be non-negative"):
        apply_diagnostic_limit((), max_files=max_files)


@pytest.mark.parametrize("max_files", [True, 1.5, "2", None])
def test_apply_diagnostic_limit_requires_an_integer(max_files: object) -> None:
    with pytest.raises(TypeError, match="max_files must be an integer"):
        apply_diagnostic_limit((), max_files=max_files)  # type: ignore[arg-type]


def test_order_for_mode_quick_tolerates_positive_max_files(
    tmp_path: Path,
) -> None:
    candidate = _candidate("quick", tmp_path / "Quick.gf")

    result = order_for_mode(
        mode=ValidationMode.QUICK,
        quick=(candidate,),
        max_files=25,
        path_getter=_path,
    )

    assert result == DiagnosticLimitResult(
        selected=(candidate,),
        overflow=(),
    )


def test_order_for_mode_checkpoint_preserves_order_and_rejects_limit(
    tmp_path: Path,
) -> None:
    second = _candidate("second", tmp_path / "Second.gf")
    first = _candidate("first", tmp_path / "First.gf")

    result = order_for_mode(
        mode=ValidationMode.CHECKPOINT,
        checkpoints=(second, first),
        path_getter=_path,
    )

    assert result.selected == (second, first)
    assert result.overflow == ()

    with pytest.raises(ValueError, match="max_files must be 0 in checkpoint mode"):
        order_for_mode(
            mode=ValidationMode.CHECKPOINT,
            checkpoints=(second, first),
            max_files=1,
            path_getter=_path,
        )


def test_order_for_mode_release_builds_union_and_rejects_limit(
    tmp_path: Path,
) -> None:
    checkpoint = _candidate("checkpoint", tmp_path / "Checkpoint.gf")
    duplicate = _candidate("duplicate", tmp_path / "." / "Checkpoint.gf")
    entrypoint = _candidate("entrypoint", tmp_path / "Entrypoint.gf")

    result = order_for_mode(
        mode=ValidationMode.RELEASE,
        checkpoints=(checkpoint,),
        entrypoints=(duplicate, entrypoint),
        path_getter=_path,
    )

    assert result.selected == (checkpoint, entrypoint)
    assert result.overflow == ()

    with pytest.raises(ValueError, match="max_files must be 0 in release mode"):
        order_for_mode(
            mode=ValidationMode.RELEASE,
            checkpoints=(checkpoint,),
            entrypoints=(entrypoint,),
            max_files=1,
            path_getter=_path,
        )


def test_order_for_mode_diagnostic_sorts_before_applying_limit(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    zeta = _candidate("zeta", source_root / "zeta.gf")
    alpha = _candidate("alpha", source_root / "alpha.gf")
    beta = _candidate("beta", source_root / "beta.gf")

    result = order_for_mode(
        mode=ValidationMode.DIAGNOSTIC,
        diagnostic=(zeta, beta, alpha),
        source_root=source_root,
        max_files=2,
        path_getter=_path,
    )

    assert result.selected == (alpha, beta)
    assert result.overflow == (zeta,)


def test_order_for_mode_diagnostic_requires_source_root(tmp_path: Path) -> None:
    candidate = _candidate("main", tmp_path / "Main.gf")

    with pytest.raises(
        ValueError,
        match="source_root is required in diagnostic mode",
    ):
        order_for_mode(
            mode=ValidationMode.DIAGNOSTIC,
            diagnostic=(candidate,),
            path_getter=_path,
        )


def test_order_for_mode_requires_validation_mode() -> None:
    with pytest.raises(TypeError, match="mode must be a ValidationMode"):
        order_for_mode(
            mode="diagnostic",  # type: ignore[arg-type]
            path_getter=_path,
        )


def test_order_excluded_explicit_preserves_discovery_order(
    tmp_path: Path,
) -> None:
    second = _candidate("second", tmp_path / "Second.gf")
    first = _candidate("first", tmp_path / "First.gf")
    duplicate = _candidate("duplicate", tmp_path / "." / "Second.gf")

    assert order_excluded_explicit(
        (second, first, duplicate),
        path_getter=_path,
    ) == (second, first)


def test_order_excluded_diagnostic_uses_normalized_path_order(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    zeta = _candidate("zeta", source_root / "zeta.gf")
    alpha = _candidate("alpha", source_root / "alpha.gf")

    assert order_excluded_diagnostic(
        (zeta, alpha),
        source_root=source_root,
        path_getter=_path,
    ) == (alpha, zeta)
